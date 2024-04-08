# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, credentials, firestore, auth
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

        # TODO: add topic : doc_ref kv pair in another collection
        firestore_client.collection("topic_drefs").document(data["topic"]).set(
            {"docref": doc_ref.id}
        )
        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        if "participatedDeliberations" not in user_doc.keys():
            user_doc["participatedDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)
        if "createdDeliberations" not in user_doc.keys():
            user_doc["createdDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)
        firestore_client.collection("users").document(user_id).update(
            {
                "participatedDeliberations": user_doc["participatedDeliberations"]
                + [doc_ref.id]
            }
        )
        firestore_client.collection("users").document(user_id).update(
            {"createdDeliberations": user_doc["createdDeliberations"] + [doc_ref.id]}
        )

        # Send back a message that we've successfully written the document
        return https_fn.Response(f"Topic {data['topic']} with ID {doc_ref.id} added.")

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


@https_fn.on_request()
def joinTopic(req: https_fn.Request) -> https_fn.Response:
    try:
        # Verify the JWT token
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = req.get_json()
        required_keys = set(["topic"])
        # Ensure the JSON object contains a 'topic' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)

        firestore_client: google.cloud.firestore.Client = firestore.client()
        # Push the new document into Cloud Firestore using the Firebase Admin SDK.
        topic_doc_ref = firestore_client.collection("topic_drefs").document(
            data["topic"]
        )

        topic_doc = topic_doc_ref.get()
        if topic_doc.exists:
            print(f"Document data: {topic_doc.to_dict()}")
        else:
            return https_fn.Response("Requested topic does not exist.", status=400)
        topic_id = topic_doc.to_dict()["docref"]

        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        if "participatedDeliberations" not in user_doc.keys():
            user_doc["participatedDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)
        firestore_client.collection("users").document(user_id).update(
            {
                "participatedDeliberations": user_doc["participatedDeliberations"]
                + [topic_id]
            }
        )

        # Send back a message that we've successfully written the document
        return https_fn.Response(f"You have been added to the requested deliberation.")

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
