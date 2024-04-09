"""
This file contains the main functions that are deployed to the Firebase Cloud Functions.
Authors: Chinmaya, Guinness
"""

from firebase_functions import https_fn, firestore_fn
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json

initialize_app()


@https_fn.on_request()
def createTopic(req: https_fn.Request) -> https_fn.Response:
    """Take the JSON object passed to this HTTP endpoint and insert it into
    a new document in the messages collection. Expects a POST request."""
    try:
        # authenticate the user
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = req.get_json()
        required_keys = set(
            [
                "topicName",
                "yesSeeds",
                "noSeeds",
            ]
        )
        # Ensure the JSON object contains a 'topic' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)

        # Initialize Firestore client
        firestore_client = firestore.client()

        # add the new deliberation to the collection
        _, doc_ref = firestore_client.collection("deliberations").add(data)

        # add the doc reference to the topic_drefs collection
        firestore_client.collection("topic_drefs").document(data["topic"]).set(
            {"docref": doc_ref.id}
        )

        # retrieve the user doc and update the createdDeliberations fields
        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        # if the user has not created any deliberations yet, create the field
        if "createdDeliberations" not in user_doc.keys():
            user_doc["createdDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)

        # update the createdDeliberations field
        firestore_client.collection("users").document(user_id).update(
            {"createdDeliberations": user_doc["createdDeliberations"] + [doc_ref.id]}
        )

        # Send back a message that we've successfully written the document
        return https_fn.Response(f"Topic {data['topic']} with ID {doc_ref.id} added.")

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


@https_fn.on_request()
def joinTopic(req: https_fn.Request) -> https_fn.Response:
    try:
        # authenticate the user
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = req.get_json()
        required_keys = set(["topicID"])
        # Ensure the JSON object contains a 'topic' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)

        # Initialize Firestore client
        firestore_client = firestore.client()

        # retrieve the topic doc reference
        topic_lookup_ref = (
            firestore_client.collection("topic_drefs").document(data["topicID"]).get()
        )

        # if the topic does not exist, return an error
        if not topic_lookup_ref.exists:
            return https_fn.Response("Requested topic does not exist.", status=400)

        # get the doc reference of the topic
        topic_doc_ref = topic_lookup_ref.to_dict()["docref"]

        # retrieve the user doc and update the participatedDeliberations fields
        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        # if the user has not participated in any deliberations yet, create the field
        if "participatedDeliberations" not in user_doc.keys():
            user_doc["participatedDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)

        # update the participatedDeliberations field
        firestore_client.collection("users").document(user_id).update(
            {
                "participatedDeliberations": user_doc["participatedDeliberations"]
                + [topic_doc_ref]
            }
        )

        # Send back a message that we've successfully written the document
        return https_fn.Response(f"You have been added to the requested deliberation.")

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


@https_fn.on_request()
def getCreatedTopics(req: https_fn.Request) -> https_fn.Response:
    try:
        # authenticate the user
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Initialize Firestore client
        firestore_client = firestore.client()

        # retrieve the user doc
        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        # if the user has not created any deliberations yet, create the field
        if "createdDeliberations" not in user_doc.keys():
            user_doc["createdDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)

        createdDeliberations = user_doc["createdDeliberations"]

        # retrieve the topic names of the created deliberations
        topic_list = []
        for topic_id in createdDeliberations:
            topic_doc = (
                firestore_client.collection("deliberations")
                .document(topic_id)
                .get()
                .to_dict()
            )
            topic_list.append(
                {"deliberationID": topic_id, "topicName": topic_doc["topic"]}
            )

        # send back a JSON object with the doc references and also the topic names
        return https_fn.Response(
            json.dumps(topic_list), content_type="application/json"
        )

    # catch any errors that occur during the process
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
def getParticipatedTopics(req: https_fn.Request) -> https_fn.Response:
    try:
        # authenticate the user
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Initialize Firestore client
        firestore_client = firestore.client()

        # retrieve the user doc
        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        # if the user has not created any deliberations yet, create the field
        if "participatedDeliberations" not in user_doc.keys():
            user_doc["participatedDeliberations"] = []
            firestore_client.collection("users").document(user_id).set(user_doc)

        participatedDeliberations = user_doc["participatedDeliberations"]

        # retrieve the topic names of the created deliberations
        topic_list = []
        for topic_id in participatedDeliberations:
            topic_doc = (
                firestore_client.collection("deliberations")
                .document(topic_id)
                .get()
                .to_dict()
            )
            topic_list.append(
                {"deliberationID": topic_id, "topicName": topic_doc["topic"]}
            )

        # send back a JSON object with the doc references and also the topic names
        return https_fn.Response(
            json.dumps(topic_list), content_type="application/json"
        )

    # catch any errors that occur during the process
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
def getRound1Information(req: https_fn.Request) -> https_fn.Response:
    try:
        # authenticate the user
        token = req.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Initialize Firestore client
        firestore_client = firestore.client()

        # retrieve the user doc
        user_doc = (
            firestore_client.collection("users").document(user_id).get().to_dict()
        )

        data = req.get_json()
        required_keys = set(["deliberationDocRef"])
        # Ensure the JSON object contains a 'deliberationDocRef' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)

        # if the user has not created any deliberations yet or is not part of the requested deliberation, give response
        if (
            "participatedDeliberations" not in user_doc.keys()
            or len(user_doc["participatedDeliberations"]) == 0
            or data["deliberationDocRef"] not in user_doc["participatedDeliberations"]
        ):
            return https_fn.Response(
                "Seems like you don't have access to this deliberation. Sorry!",
                status=401,
            )

        # retrieve the topic information for the desired deliberation
        topic_doc = (
            firestore_client.collection("deliberations")
            .document(data["deliberationDocRef"])
            .get()
            .to_dict()
        )

        # send back a JSON object with the doc references and also the topic names
        return https_fn.Response(json.dumps(topic_doc), content_type="application/json")

    # catch any errors that occur during the process
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
