from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json

enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )

@https_fn.on_request(cors=enableCors)
def getStageInfo(req: https_fn.Request) -> https_fn.Response:
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
                "deliberationDocRef"
            ]
        )
        
        
        # Ensure the JSON object contains a 'topic' field
        if set(list(data.keys())) != required_keys:
            return https_fn.Response("Required keys missing in JSON object", status=400)
        

        # Initialize Firestore client
        firestore_client = firestore.client()


        # add the doc reference to the topic_drefs collection
        deliberationInfo = firestore_client.collection("deliberations").document(data["deliberationDocRef"]).get().to_dict()
        desiredStages = [stage for stage, choice in zip(STAGES, deliberationInfo["delibFlow"]) if choice != "None"]
        result = [
            {
                "stageName" : "test", 
                "isCurrent" : True if deliberationInfo["currStage"] == key else False
            }
            for key in deliberationInfo
        ]
        
        # Send back a message that we've successfully written the document
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
    
    

@https_fn.on_request(cors=enableCors)
def pollUserLocations(req: https_fn.Request) -> https_fn.Response:
    # Send back a message that we've successfully written the document
    try: 
        return https_fn.Response(
            json.dumps("all good!"), content_type="application/json"
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