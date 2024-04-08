# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, credentials

cred = credentials.Certificate("serviceAccountKey.json")

initialize_app(cred)


@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello world!")


@https_fn.on_request()
def createTopic(req: https_fn.Request) -> https_fn.Response:
    """Take the JSON payload passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    try:
        data = req
    except ValueError:
        return https_fn.Response("Invalid JSON", status=400)
    if not data:
        return https_fn.Response("No topic information provided", status=400)
    print("topic not empty")
    firestore_client: google.cloud.firestore.Client = firestore.client()
    print("working")
    
    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("deliberations").add(
        {"topic": data["text"]}
    )
    # Send back a message that we've successfully written the message
    # return https_fn.Response(f"Message with ID {doc_ref.id} added.")
    # return make_response(
    #     jsonify({"message": f"Topic with ID {doc_ref.id} added."}), 200
    # )