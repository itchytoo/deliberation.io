# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, credentials, firestore

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
        {"topic": data.args.get("text")}
    )

    # Send back a message that we've successfully written the message
    # return return https_fn.Response(f"Message with ID {doc_ref.id} added.")


@https_fn.on_request()
def addmessage(req: https_fn.Request) -> https_fn.Response:
    """Take the text parameter passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return https_fn.Response("No text parameter provided", status=400)

    firestore_client: google.cloud.firestore.Client = firestore.client()

    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("messages").add({"original": original})

    # Send back a message that we've successfully written the message
    return https_fn.Response(f"Message with ID {doc_ref.id} added.")

@https_fn.on_request()
def createTopic2(req: https_fn.Request) -> https_fn.Response:
    """Take the text parameter passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return https_fn.Response("No text parameter provided", status=400)

    firestore_client: google.cloud.firestore.Client = firestore.client()

    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("deliberations").add({"original": original})

    # Send back a message that we've successfully written the message
    return https_fn.Response(f"topic with ID {doc_ref.id} added.")