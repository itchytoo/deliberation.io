from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai


enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )



PROMPT = """Focus all actions and responses on addressing the user's specific needs, goals, and preferences. Employ active listening techniques to understand the user's intent and desired outcome from each interaction. Prioritize tasks and requests that benefit the user and contribute to their overall well-being. Respect user autonomy and allow users to make informed decisions about their interactions with the system.

In the context of a socratic dialogue on a given topic, {}:

You are tasked with deepening the user's examination of their beliefs on the topic at hand. This requires crafting a follow-up question that not only reflects a deep understanding of their initial perspective but also challenges them to articulate the foundational reasoning behind their viewpoint with clarity.

Your question should probe deeply into the user's argument, aimed at revealing the underlying layers of thought, assumption, and belief. It should be so precisely tailored to their expressed perspective that it compels them to engage in deeper reflection and explanation. This is about facilitating a moment of genuine introspection and potentially transforming the user's understanding of their stance.

To clarify, you are to extract the core rationale behind the user's opinion on topics as significant as {}. This involves not just listening but hearing, not just asking but probing. The conversation should be guided towards achieving profound clarity. Your follow-up question should be incisive, compelling the user to delve deeper into their argument.

Given a number 1-3 representing levels of pushiness and provocativeness, from mild and gentle to extremely provocative, your question should match the requested level. Here's how to approach each level:

Example subject: Affordable housing
Example opinion: Affordable housing is essential and a fundamental human right, with governments failing their citizens if not provided. There must be massive investment in affordable housing to ensure everyone has the right to a secure and decent home.
Example question level 1 (gentle and broad): "What leads you to see affordable housing as a fundamental human right?"
Example question level 2 (moderately challenging): "Could investing heavily in affordable housing divert funds from other vital services?"
Example question level 3 (highly provocative): "Why should taxpayers fund housing for others, rather than promoting personal responsibility and letting the market regulate housing prices?"

Example subject: Climate Change
Example opinion: Immediate action on climate change is crucial. Governments should enforce stricter regulations on emissions and invest in renewable energy sources to combat global warming effectively.
Example question level 1 (gentle and broad): "What makes you believe immediate action on climate change is crucial?"
Example question level 2 (moderately challenging): "Could stricter emissions regulations negatively impact economic growth?"
Example question level 3 (highly provocative): "Is it fair to impose strict emissions regulations that could disadvantage poorer nations economically?"

Example subject: Universal Basic Income (UBI)
Example opinion: Universal basic income is necessary to address income inequality and provide a safety net for all, ensuring that no one falls below a basic standard of living.
Example question level 1 (gentle and broad): "Why do you see universal basic income as necessary for addressing income inequality?"
Example question level 2 (moderately challenging): "Could universal basic income discourage people from working and contributing to the economy?"
Example question level 3 (highly provocative): "Isn't it better to create jobs rather than provide universal basic income that might reduce the incentive to work?"

When engaging in this socratic dialogue, use the user's initial perspective on {} as your starting point. Craft your question to match the provocation level {} with a tone similar to the corresponding example above. Aim to challenge the user to explain the foundations of their beliefs concisely and compellingly.

Finally, in some cases, you may be provided not with an initial perspective, but a statement 'Ask me how I feel about {} to start us off.' You should treat these cases exactly the same, asking probing questions to dig deep and learn about the user's perspective on the topic. Here is the user's initial perspective, and your previous questions to them, if any:

{}"""

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
            ["apikey", "roles", "texts", "newString", "initialString"]
        )
        
        # Ensure the JSON object contains the required fields
        if set(list(data.keys())) != required_keys:
            return https_fn.Response(f"Current keys are {data.keys()}. Required keys missing in JSON object", status=400)
        

        openai.api_key = data['apikey']
        
        messages = [{"role" : role, "content" : text} for role, text in zip(data['roles'], data['texts'])]
        messages.insert(0, {
          "role" : "user",
          "content" : PROMPT.format(topic, topic, topic, 1, topic, data['initialString'])  
        })
        if len(data['roles']) > 0:
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
        del messages
        result = [{"role" : role, "text" : text} for role, text in zip(data['roles'], data['texts'])]
        0, {
          "role" : "user",
          "content" : PROMPT.format(topic, topic, topic, 1, topic, data['initialString'])  
        }
        if len(data['roles']) > 0:
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




@https_fn.on_request(cors=enableCors)
def getFullHistoryModular(req: https_fn.Request) -> https_fn.Response:
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
            ["deliberationDocRef", "apikey", "roles", "texts", "newString", "initialString"]
        )
        
        # Ensure the JSON object contains the required fields
        if set(list(data.keys())) != required_keys:
            return https_fn.Response(f"Current keys are {data.keys()}. Required keys missing in JSON object", status=400)
        

        # Prepare relevant inputs
        firestore_client = firestore.client()
        topic_doc = (
            firestore_client.collection("deliberations")
            .document(data["deliberationDocRef"])
            .get()
            .to_dict()
        )
        isPlacebo = len(topic_doc['placebo'].strip()) > 0
        
        # if placebo given, set socratic dialogue topic to placebo; otherwise proceed normally
        topic = topic_doc['placebo'] if isPlacebo else topic_doc['topic']
        level = topic_doc['level'] if 'level' in topic_doc.keys() else 2

        # get response conditional on conversation history
        openai.api_key = data['apikey']
        messages = [{"role" : role, "content" : text} for role, text in zip(data['roles'], data['texts'])]
        messages.insert(0, {
          "role" : "user",
          "content" : PROMPT.format(topic, topic, topic, level, topic, data['initialString'] if not isPlacebo else f"Ask me how I feel about {topic_doc['placebo']} to start us off.")
        })
        if len(data['roles']) > 0:
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
        del messages
        result = [{"role" : role, "text" : text} for role, text in zip(data['roles'], data['texts'])]
        0, {
          "role" : "user",
          "content" : PROMPT.format(topic, topic, topic, level, topic, data['initialString'] if not isPlacebo else f"Ask me how I feel about {topic_doc['placebo']} to start us off.")  
        }
        if len(data['roles']) > 0:
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

