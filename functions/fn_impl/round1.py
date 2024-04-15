from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json

enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )

@https_fn.on_request(cors=enableCors)
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
        seedYesTaglines = topic_doc["seedViewpoints"]["yes"]["taglines"]
        seedNoTaglines = topic_doc["seedViewpoints"]["no"]["taglines"]
        seedYesDescriptions = topic_doc["seedViewpoints"]["yes"]["descriptions"]
        seedNoDescriptions = topic_doc["seedViewpoints"]["no"]["descriptions"]

        yesSeedList = list()
        noSeedList = list()
        for tagline, description in zip(seedYesTaglines, seedYesDescriptions):
            yesSeedList.append({"tagline": tagline, "description": description})

        for tagline, description in zip(seedNoTaglines, seedNoDescriptions):
            noSeedList.append({"tagline": tagline, "description": description})

        massaged_doc = {
            "topicName": topic_doc["topic"],
            "yesSeeds": yesSeedList,
            "noSeeds": noSeedList,
        }

        # send back a JSON object with the doc references and also the topic names
        return https_fn.Response(
            json.dumps(massaged_doc), content_type="application/json"
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