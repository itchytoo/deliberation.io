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
    try:
        # Verify the JWT token
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = req.get_json()
        required_keys = set(
            [
                "adminId",
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

    except auth.InvalidIdTokenError:
        return https_fn.Response("Invalid JWT token", status=401)

    except auth.ExpiredIdTokenError:
        return https_fn.Response("Expired JWT token", status=401)

    except auth.RevokedIdTokenError:
        return https_fn.Response("Revoked JWT token", status=401)

    except auth.CertificateFetchError:
        return https_fn.Response("Error fetching the public key certificates", status=401)

    except auth.UserDisabledError:
        return https_fn.Response("User is disabled", status=401)

    except ValueError:
        return https_fn.Response("No JWT token provided", status=401)
