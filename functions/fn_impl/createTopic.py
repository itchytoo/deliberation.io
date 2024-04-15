from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json

enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )


NUM_OPTIONS = 5
OPTIONS = {
    "round1" : ["Include seed comments", "No seed comments"],
    "intervention" : ["Socratic dialogue", "Comment feedback", "Socratic dialogue and comment feedback", "None"],
    "round2" : ["Raw comments, randomized", "Steelman arguments, randomized", "Raw comments, ordered", "Steelman arguments, ordered"],
    "round3" : ["Revote", "None"]
}
OPTIONAL_KEYS = set(["intervention", "round3"])

@https_fn.on_request(cors=enableCors)
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
                "topic",
                "seedViewpoints",
                "deliberationSettings"
            ]
        )
        
        
        # Ensure the JSON object contains a 'topic' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)
        if type(data["deliberationSettings"]) is not dict:
            return https_fn.Response("Deliberation settings incorrectly formatted.", status=400)
        
        finalFlow, finalTimes = list(), list()
        for i, key in enumerate(list(OPTIONS.keys())):
            # idx = OPTIONS[key].index(data["deliberationSettings"][key]["option"])
            # if key in OPTIONAL_KEYS and idx == len(OPTIONS[key]) - 1:
            #     idx = -1
            finalFlow.append(data["deliberationSettings"][key]["option"])
            finalTimes.append(data["deliberationSettings"][key]["time"] * 1000)  # convert from seconds to milliseconds for Flutterflow widgets

        # add the adminID field to the data
        data["adminID"] = user_id
        
        del data["deliberationSettings"]
        data["delibFlow"] = finalFlow
        data["stageTimes"] = finalTimes
        data["currStage"] = -1


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


@https_fn.on_request(cors=enableCors)
def editTopic(req: https_fn.Request) -> https_fn.Response:
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
                "topic",
                "seedViewpoints",
                "deliberationSettings"
            ]
        )
        
        
        # Ensure the JSON object contains a 'topic' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)
        if type(data["deliberationSettings"]) is not dict:
            return https_fn.Response("Deliberation settings incorrectly formatted.", status=400)
        
        finalFlow, finalTimes = list(), list()
        for i, key in enumerate(list(OPTIONS.keys())):
            finalFlow.append(data["deliberationSettings"][key]["option"])
            finalTimes.append(data["deliberationSettings"][key]["time"] * 1000)  # convert from seconds to milliseconds for Flutterflow widgets

        # add the adminID field to the data
        data["adminID"] = user_id
        
        
        del data["deliberationSettings"]
        data["delibFlow"] = finalFlow
        data["stageTimes"] = finalTimes
        data["currStage"] = -1


        # Initialize Firestore client
        firestore_client = firestore.client()

        # add the doc reference to the topic_drefs collection
        firestore_client.collection("topic_drefs").document(data["topic"]).update(
            data
        )

        # Send back a message that we've successfully written the document
        return https_fn.Response(f"Topic {data['topic']} successfully updated.")

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
