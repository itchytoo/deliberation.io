from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai


enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )


STEELMAN_SYS_PROMPT = "You are helpful."
STEELMAN_PROMPT = "How are you? {}"
@https_fn.on_request(cors=enableCors)
def steelmanJob(req: https_fn.Request) -> https_fn.Response:
    """Take the JSON object passed to this HTTP endpoint and insert it into
    a new document in the messages collection. Expects a POST request."""
    # authenticate the user
    token = req.headers.get("Authorization").split("Bearer ")[1]
    decoded_token = auth.verify_id_token(token)
    user_id = decoded_token["user_id"]
    try:
        # Parse JSON directly from request body
        data = req.get_json()
        required_keys = set(
            ["deliberationDocRef", "apikey"]
        )
        
        # Ensure the JSON object contains the required fields
        if set(list(data.keys())) != required_keys:
            return https_fn.Response(f"Current keys are {data.keys()}. Required keys missing in JSON object", status=400)

        # Initialize Firestore client
        firestore_client = firestore.client()
        topic_doc = (
            firestore_client.collection("deliberations")
            .document(data["deliberationDocRef"])
            .get()
            .to_dict()
        )
        isSteelman = topic_doc['isSteelman'].strip() == 'Yes'
        if not isSteelman:
            return https_fn.Response("No steelman job necessary!")

        # add the new deliberation to the collection
        user_comment_docs = firestore_client.collection("deliberations").document(data["deliberationDocRef"]).collection("commentCollection").stream()
        # Get the comments from the user_comment_docs
        comments_list = []
        for user_comment_doc in user_comment_docs:
            user_comment_dict = user_comment_doc.to_dict()
            commentText = user_comment_dict["comments"][-1]
            userID = user_comment_doc.id
            commentID = {"userID": userID, "commentIndex": len(user_comment_dict["comments"])-1}
            commentCard = {"commentID": commentID, "commentText": commentText}
            comments_list.append(commentCard)
        comments_list_formatted = '\n\n'.join([comment['commentText'].strip() for comment in comments_list])
        
        
         # get response conditional on conversation history
        openai.api_key = data['apikey']
        # messages = [
        #     {"role" : "system", "content" : STEELMAN_SYS_PROMPT},
        #     {"role" : "user", "content" : STEELMAN_PROMPT.format(comments_list_formatted)}
        # ]
        messages = [
            {"role" : "system", "content" : STEELMAN_SYS_PROMPT},
            {"role" : "user", "content" : STEELMAN_PROMPT.format(':)')}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        result = response['choices'][0]['message']['content']
        comments = [f"Steelman Comment {i}" for i in range(6)]
        
        

        # Initialize Firestore client
        firestore_client = firestore.Client()

        # Reference to the 'deliberations' collection
        collection_ref = firestore_client.collection("deliberations")

        # Specific document reference within 'deliberations' collection based on data["deliberationDocRef"]
        doc_ref = collection_ref.document(data["deliberationDocRef"])

        # Reference to the 'steelmanCommentCollection' subcollection
        steelman_comment_collection = doc_ref.collection('steelmanCommentCollection')

        # Loop through comments and add each as a new document in 'steelmanCommentCollection'
        for i, comment in enumerate(comments):
            # Add new comment document to 'steelmanCommentCollection'
            new_doc_ref = steelman_comment_collection.document()
            new_doc_ref.set({
                'comments': [comment],
            })

            # Using the document ID from new_doc_ref, create a new user document in the 'users' collection
            user_doc_ref = firestore_client.collection("users").document(new_doc_ref.id).set({
                "createdDeliberations": [],
                "participatedDeliberations": [],
                "email": f"{new_doc_ref.id}@stanford.edu",
                "uid": new_doc_ref.id,
            })

    
        # Return the list of comments
        return https_fn.Response("Steelman job completed.")
        

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
