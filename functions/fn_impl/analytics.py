
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
        
        
        # get response conditional on conversation history
        apiToken = firestore_client.collection("keys").document('APIKEYS').get().to_dict()['qualtrics_api_token']
        dataCenter = "yul1"
        library_id = firestore_client.collection("keys").document('APIKEYS').get().to_dict()['qualtrics_library_key']
        # Convert dictionaries to a DataFrame
        data = pd.DataFrame({
            'Upvotes': comment_upvotes,
            'Downvotes': comment_downvotes
        })

        # Create a plot
        fig, ax = plt.subplots()

        # Plotting the data
        data.plot(kind='bar', ax=ax, color={'Upvotes': 'green', 'Downvotes': 'red'})

        # Adding titles and labels
        ax.set_title('Comment Upvotes and Downvotes')
        ax.set_xlabel('Comments')
        ax.set_ylabel('Number of Votes')
        
        # Save the plot to a BytesIO object instead of a file
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='jpeg')
        img_buf.seek(0)  # Important: move the read cursor to the start of the buffer
        
        # files = {'file': ('banana.jpeg', open(image_path, 'rb'), 'image/jpeg')}
        files = {'file': (f'{deliberationDocRef}.jpeg', img_buf, 'image/jpeg')}
        image_headers = {
            'Accept' : 'application/json',
            'boundary' : '',
            'X-API-TOKEN': apiToken
        }
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