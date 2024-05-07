
from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import io
import requests
from datetime import datetime, timedelta

enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app", r"https://deliberationiobeta2\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )


@https_fn.on_request(cors=enableCors)
def createQualtricsSurvey(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]

        # Check if the user is the admin
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        adminId = doc.get("adminID")
        if adminId != user_id:
            return https_fn.Response("User is not the admin", status=401)








         # add the new deliberation to the collection
        user_vote_docs = firestore_client.collection("deliberations").document(data["deliberationDocRef"]).collection("votesCollection").stream()
        isSteelman = firestore_client.collection("deliberations").document(deliberationDocRef).get().to_dict()['isSteelman']
        comment_type = 'steelman' if isSteelman else 'comments'
        # Get the comments from the user_comment_docs
        upvotes, downvotes = defaultdict(int), defaultdict(int)
        for vote_doc in user_vote_docs:
            vote_doc_dict = vote_doc.to_dict()[comment_type]
            for key in vote_doc_dict:
                maxIndex = max(list(vote_doc_dict[key].keys()))
                if vote_doc_dict[key][maxIndex] == 1:
                    upvotes[key] += 1
                elif vote_doc_dict[key][maxIndex] == -1:
                    downvotes[key] += 1
    
        # Find the union of keys from both dictionaries
        all_keys = set(upvotes.keys()).union(downvotes.keys())

        # Access each key in both dictionaries to ensure they exist
        for key in all_keys:
            upvotes[key]
            downvotes[key]
        
        comment_upvotes, comment_downvotes = defaultdict(int), defaultdict(int)
        user_comment_docs = firestore_client.collection("deliberations").document(data["deliberationDocRef"]).collection("commentCollection").stream()
        for comment_doc in user_comment_docs:
            comment_doc_list = comment_doc.to_dict()[comment_type]
            latest_comment = comment_doc_list[-1]
            if len(latest_comment.strip()) == 0:
                continue
            if comment_doc.id in upvotes.keys():
                comment_upvotes[latest_comment] = upvotes[comment_doc.id]
                comment_downvotes[latest_comment] = downvotes[comment_doc.id]
        
        result = {
            "upvotes" : upvotes,
            "downvotes" : downvotes,
            "commentUpvotes" : comment_upvotes,
            "commentDownvotes" : comment_downvotes
        }
        
        
        
        
        
        
        
        
        # set qualtrics api info
        apiToken = firestore_client.collection("keys").document('APIKEYS').get().to_dict()['qualtrics_api_token']
        dataCenter = "yul1"
        library_id = firestore_client.collection("keys").document('APIKEYS').get().to_dict()['qualtrics_library_key']
        owner_id = firestore_client.collection("keys").document('APIKEYS').get().to_dict()['qualtrics_user_id']
        # Create a plot
        data = pd.DataFrame({
            'Upvotes': comment_upvotes,
            'Downvotes': comment_downvotes
        })
        fig, ax = plt.subplots()
        data.plot(kind='bar', ax=ax, color={'Upvotes': '#799FCB', 'Downvotes': '#F9665E'})
        ax.set_title('Comment Upvotes and Downvotes')
        ax.set_xlabel('Comments')
        ax.set_ylabel('Number of Votes')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10)
        
        # Save the plot to a BytesIO object
        img_buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buf, format='jpeg')
        img_buf.seek(0)  # Important: move the read cursor to the start of the buffer
        files = {'file': (f'{deliberationDocRef}.jpeg', img_buf, 'image/jpeg')}
        image_headers = {
            'Accept' : 'application/json',
            'boundary' : '',
            'X-API-TOKEN': apiToken
        }
        upload_url = f"https://{dataCenter}.qualtrics.com/API/v3/libraries/{library_id}/graphics"
        response = requests.post(upload_url, files=files, headers=image_headers)

        if response.status_code == 200:
            graphic_id = response.json()['result']['id']
            print("Image uploaded successfully with ID:", graphic_id)
        else:
            raise Exception(response.text)
        
        
        
        
        # Create Survey
        deliberation_doc_dict = firestore_client.collection("deliberations").document(deliberationDocRef).get().to_dict()
        baseUrl = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions"
        headers = {
            "x-api-token": apiToken,
            "content-type": "application/json",
            "Accept": "application/json"
        }
        data = {"SurveyName": f"{deliberation_doc_dict['topicName']}", "Language": "EN", "ProjectCategory": "CORE"}
        response = requests.post(baseUrl, json=data, headers=headers)
        if response.status_code == 200:
            survey_id = response.json()['result']['SurveyID']
        else:
            raise Exception(response.text)
        
        # Add a question with the uploaded image
        question_data = {
            "QuestionType": "MC",
            "QuestionText": f"This is a test question for deliberation with ID {deliberationDocRef}",
            "Selector": "SAVR",
            "SubSelector": "TX",
            "ChoiceOrder": ["1", "2", "3"],
            "Choices": { "1": { "Display": "choice 1" }, "2": { "Display": "choice 2" }, "3": {"Display": f"<img src='https://stanforduniversity.qualtrics.com/ControlPanel/Graphic.php?IM={graphic_id}' alt='description' style='width: 100%; max-width: 500px;'>"}},
            "Validation": { "Settings": { "ForceResponse": "ON", "Type": "None" } },
            "Configuration": {
                "QuestionDescriptionOption": "UseText"
            }
        }
        questions_url = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions/{survey_id}/questions"
        response = requests.post(questions_url, json=question_data, headers=headers)

        if response.status_code == 200:
            print("Question added successfully.")
            print(response.text, '\n')
        else:
            raise Exception(response.text)
            
            
        publishing_url = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions/{survey_id}/versions"
        publishing_headers = {
            "Accept" : "application/json",
            "Content-Type" : "application/json",
            "X-API-TOKEN" : apiToken
        }
        survey_publishing_data = {
            "Description" : "Testing description",
            "Published" : True
        }
        response = requests.post(publishing_url, json=survey_publishing_data, headers=publishing_headers)
        if response.status_code == 200:
            print("Survey published successfully.")
            print(response.text, '\n')
        else:
            raise Exception(response.text)

        # Set up headers for the activation/update request
        activation_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-TOKEN": apiToken
        }


        # Current date and time in UTC
        current_date = datetime.now()

        # Setting start date to current date and end date to 3 years in the future
        survey_activation_data = {
            "name": f"{deliberation_doc_dict['topicName']}",
            "isActive": True,
            "expiration": {
                "startDate": current_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDate": (current_date + timedelta(days=3*365)).strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "ownerId": owner_id
        }


        # URL to update the survey
        activation_url = f"https://{dataCenter}.qualtrics.com/API/v3/surveys/{survey_id}"

        # Make a PUT request to update the survey
        response = requests.put(activation_url, json=survey_activation_data, headers=activation_headers)
        if response.status_code == 200:
            print("Survey updated and activated successfully.")
            print(response.text)
        else:
            print("Failed to update and activate survey:", response.text)

        # Print the survey link
        survey_link = f"https://stanforduniversity.qualtrics.com/jfe/form/{survey_id}"
        return https_fn.Response(
            json.dumps({'link' : survey_link}), content_type="application/json"
        )
        
        
        
        # Create survey
    # Catch any errors that occur during the process
    except auth.InvalidIdTokenError:
        return https_fn.Response("Invalid JWT token", status=401)

    except auth.ExpiredIdTokenError:
        return https_fn.Response("Expired JWT token", status=401)

    except auth.RevokedIdTokenError:
        return https_fn.Response("Revoked JWT token", status=401)

    except auth.CertificateFetchError:
        return https_fn.Response(
            "Error fetching the public key certificates", status=401
        )

    except auth.UserDisabledError:
        return https_fn.Response("User is disabled", status=401)

    except ValueError:
        return https_fn.Response("No JWT token provided", status=401)
