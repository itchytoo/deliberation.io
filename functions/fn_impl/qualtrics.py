import os
import requests
import json  # Import the json module
from datetime import datetime, timedelta


# Qualtrics API setup
apiToken = "m62BiuqMZnT2373IRVojOx5a90EVHcuNzavS58jX"
dataCenter = "yul1"
library_id = "UR_8jDTL4gXw0OVIN0"

# Create Survey
baseUrl = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions"
headers = {
    "x-api-token": apiToken,
    "content-type": "application/json",
    "Accept": "application/json"
}
data = {"SurveyName": "Bananas Survey", "Language": "EN", "ProjectCategory": "CORE"}
print("JSON being sent for survey creation:", json.dumps(data))  # Print the JSON data
response = requests.post(baseUrl, json=data, headers=headers)

if response.status_code == 200:
    survey_id = response.json()['result']['SurveyID']
    print("Survey created successfully with ID:", survey_id)
    print(response.text, '\n')
else:
    print("Failed to create survey:", response.text)

# Upload Image
image_path = 'banana.jpeg'
image_headers = {
    'Accept' : 'application/json',
 'boundary' : '',
 'X-API-TOKEN': apiToken
 }

print("Uploading image from path:", image_path)  # Print the image path
files = {'file': ('banana.jpeg', open(image_path, 'rb'), 'image/jpeg')}
upload_url = f"https://{dataCenter}.qualtrics.com/API/v3/libraries/{library_id}/graphics"
response = requests.post(upload_url, files=files, headers=image_headers)
print(upload_url)
print(files)
print(image_headers)

if response.status_code == 200:
    graphic_id = response.json()['result']['id']
    print("Image uploaded successfully with ID:", graphic_id)
else:
    print("Failed to upload image:", response.text)
    exit()

# Add a question with the uploaded image
question_data = {
    "QuestionType": "MC",
    "QuestionText": "Something",
    "Selector": "SAVR",
    "SubSelector": "TX",
    "ChoiceOrder": ["1", "2", "3"],
    "Choices": { "1": { "Display": "choice 1" }, "2": { "Display": "choice 2" }, "3": {"Display": f"<img src='https://stanforduniversity.qualtrics.com/ControlPanel/Graphic.php?IM={graphic_id}' alt='description' style='width: 100%; max-width: 500px;'>"}},
    "Validation": { "Settings": { "ForceResponse": "ON", "Type": "None" } },
    "Configuration": {
        "QuestionDescriptionOption": "UseText"
    }
}
print("JSON being sent for adding a question:", json.dumps(question_data))  # Print the JSON data
questions_url = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions/{survey_id}/questions"
response = requests.post(questions_url, json=question_data, headers=headers)

if response.status_code == 200:
    print("Question added successfully.")
    print(response.text, '\n')
else:
    print("Failed to add question:", response.text)
    
    
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
    print("Failed to publish survey:", response.text)

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
    "name": "Banana Survey",
    "isActive": True,
    "expiration": {
        "startDate": current_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDate": (current_date + timedelta(days=3*365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    },
    "ownerId": "UR_8jDTL4gXw0OVIN0"
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
print(f"Survey link: {survey_link}")


from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai
import pandas
from collections import defaultdict

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
        isSteelman = firestore_client.collection("deliberations").document(deliberationDocRef).get().todict()['isSteelman']
        comment_type = 'steelman' if isSteelman else 'comments'
        # Get the comments from the user_comment_docs
        upvotes, downvotes = defaultdict(int), defaultdict(int)
        for vote_doc in user_vote_docs:
            vote_doc_dict = vote_doc.to_dict()[comment_type]
            for key in vote_doc_dict:
                maxIndex = max(list(vote_doc_dict[key].keys()))
                if vote_doc_dict[key][maxIndex] == 1:
                    upvotes[key] += 1
                elif vote_doc_dict[key][maxIndex] == 0:
                    downvotes[key] += 1
        
        # Find the union of keys from both dictionaries
        all_keys = set(upvotes.keys()).union(downvotes.keys())

        # Access each key in both dictionaries to ensure they exist
        for key in all_keys:
            upvotes[key]
            downvotes[key]
        result = {
            "upvotes" : upvotes,
            "downvotes" : downvotes
        }
            
        return https_fn.Response(
            json.dumps(result), content_type="application/json"
        )
        
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