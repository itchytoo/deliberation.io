from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai

enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )


@https_fn.on_request(cors=enableCors)
def getFullHistory(req: https_fn.Request) -> https_fn.Response:
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
            ["apikey", "roles", "texts", "newString"]
        )
        
        # Ensure the JSON object contains the required fields
        if set(list(data.keys())) != required_keys:
            return https_fn.Response(f"Current keys are {data.keys()}. Required keys missing in JSON object", status=400)
        

        openai.api_key = data['apikey']
        
        messages = [{"role" : role, "content" : text} for role, text in zip(data['roles'], data['texts'])]
        messages.append(
            {
                "role" : "user",
                "content" : data['newString']
            }
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        result = [{"role" : role, "text" : text} for role, text in zip(data['roles'], data['texts'])]
        result.append({
            "role" : "user",
            "text" : data["newString"]
        })
        result.append({
            "role" : "assistant",
            "text" : response['choices'][0]['message']['content']
        })
        
    
        # Return the list of comments
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
