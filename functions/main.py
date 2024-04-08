# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, credentials, firestore
from flask import jsonify


initialize_app()


@https_fn.on_request()
def createTopic(req: https_fn.Request) -> https_fn.Response:
    """Take the JSON object passed to this HTTP endpoint and insert it into
    a new document in the messages collection. Expects a POST request."""

    # Parse JSON directly from request body
    data = req.get_json()
    required_keys = set(
        [
            "topic",
            "description",
            "startTime",
            "endTime",
            "aiModerationFeatures",
            "seedViewpoints",
            "creatorUserId",
            "rounds",
        ]
    )
    # Ensure the JSON object contains a 'topic' field
    if set(list(data.keys())) != required_keys:
        return https_fn.Response("Required keys missing in JSON object", status=400)
    # data["aiModerationFeatures"] = req.args.getlist("aiModerationFeatures")

    firestore_client: google.cloud.firestore.Client = firestore.client()

    # Push the new document into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("deliberations").add(data)

    # Send back a message that we've successfully written the document
    return https_fn.Response(f"Topic with ID {doc_ref.id} added.")
