from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai


enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app", r"https://deliberationiobeta2\.flutterflow\.app"],
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



MAX_K = 7
STEELMAN_SYS_PROMPT = "You are helpful."
STEELMAN_PROMPT = """As a moderator in a discussion, your role is to extract the most fundamental perspectives from users' diverse opinions on the topic: {}.

You must present at least 3 and no more than {} fundamental opinions—this is a strict upper limit, and the goal is to stay as close to 3 as possible. Your task is to refine each perspective into its strongest form, amalgamating similar yet slightly differing opinions into single, robust viewpoints. Ensure that each selected opinion is steelmanned, providing a tight list of perspectives, each crafted in no more than 5 sentences and no less than 3, with clear and forceful justification. That is to say, each opinion should be a few sentences, giving both the distilled opinion and a brief justification for that opinion.

This task demands precision: neither exceed the minimal number needed to encapsulate the discussion's essence nor fall short by missing key perspectives. Avoid hitting the upper limit of {}. The selected perspectives must reflect your meticulous analysis and should be structured as follows:

Each fundamental opinion must be separated by '###' to clearly delineate each perspective. Do not use any numbered lists or additional markers. Present the opinions as:

Opinion 1
###
Opinion 2
###
Opinion 3
###
...
###
Opinion n (where 3 <= n <= {})

If your output format differs AT ALL from the format I have specified above (with '###' delimiters), I will lose billions of dollars and get a deathly illness, and you will be unemployed. Additionally, do not preface each opinion with 'Opinion i:' or 'Opinion' or anything else - each opinion should simply be the perspective and justification itself in complete sentences. Here are the initial perspectives:

{}"""


@https_fn.on_request(cors=enableCors)
def getNextPage(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]
        currentPage = data["currentPage"]

        # Get the next page from the database
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        nextPage = doc.get("pageMap")[currentPage]

        # return the next page
        return https_fn.Response(nextPage)

    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def isGateOpen(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]
        gateName = data["gateName"]

        # Get the gate status from the database
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        gateOpen = doc.get(gateName + "GateOpen")

        # return the gate status as an object with field "gateOpen"
        return https_fn.Response(json.dumps({"gateOpen": gateOpen}))

    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def imHere(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]
        currentPage = data["currentPage"]

        # Increment the count of users on the current page
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        pageCounts = doc.get("pageCounts")
        pageCounts[currentPage] += 1
        firestore_client.collection("deliberations").document(deliberationDocRef).update(
            {"pageCounts": pageCounts}
        )

        # return nothing
        return https_fn.Response("success")

    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def openGate(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]
        gateName = data["gateName"]

        # Check if the user is the admin
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        adminId = doc.get("adminID")
        if adminId != user_id:
            return https_fn.Response("User is not the admin", status=401)
        
        # if the gate is socraticGate or commentVotingGate, AND the job has not been run yet, then run the job, then open the gate
        if (gateName == "socratic" or gateName == "commentVoting") and not doc.get("jobRun"):
            
            try:
                topic_doc = (
                    firestore_client.collection("deliberations")
                    .document(data["deliberationDocRef"])
                    .get()
                    .to_dict()
                )
                isSteelman = topic_doc['isSteelman']
                if isSteelman:
                    # add the new deliberation to the collection
                    user_comment_docs = firestore_client.collection("deliberations").document(data["deliberationDocRef"]).collection("commentCollection").stream()
                    # Get the comments from the user_comment_docs
                    comments_list = []
                    for user_comment_doc in user_comment_docs:
                        user_comment_dict = user_comment_doc.to_dict()
                        commentText = user_comment_dict["comments"][-1]
                        userID = user_comment_doc.id
                        commentID = {"userID": userID, "commentIndex": len(user_comment_dict["comments"])-1}
                        commentCard = {"commentID": commentID, "commentText": commentText}
                        comments_list.append(commentCard)
                    comments_list_formatted = '\n\n'.join([comment['commentText'].strip() for comment in comments_list])
                    
                    
                    # get response conditional on conversation history
                    openai.api_key = firestore_client.collection("keys").document('APIKEYS').get().to_dict()['openai_apikey']
                    messages = [
                        {"role" : "system", "content" : STEELMAN_SYS_PROMPT},
                        {"role" : "user", "content" : STEELMAN_PROMPT.format(topic_doc['topicName'], MAX_K, MAX_K, MAX_K, comments_list_formatted)}
                    ]
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=messages
                    )
                    
                    result = response['choices'][0]['message']['content']
                    #comments = [f"Steelman Comment {i}" for i in range(6)]
                    comments = result.split('###')
                    

                    # Initialize Firestore client
                    firestore_client = firestore.Client()

                    # Reference to the 'deliberations' collection
                    collection_ref = firestore_client.collection("deliberations")

                    # Specific document reference within 'deliberations' collection based on data["deliberationDocRef"]
                    doc_ref = collection_ref.document(data["deliberationDocRef"])

                    # Reference to the 'steelmanCommentCollection' subcollection
                    steelman_comment_collection = doc_ref.collection('steelmanCommentCollection')

                    # Loop through comments and add each as a new document in 'steelmanCommentCollection'
                    for i, comment in enumerate(comments):
                        # Add new comment document to 'steelmanCommentCollection'
                        new_doc_ref = steelman_comment_collection.document()
                        new_doc_ref.set({
                            'comments': [comment],
                        })

                        # Using the document ID from new_doc_ref, create a new user document in the 'users' collection
                        user_doc_ref = firestore_client.collection("users").document(new_doc_ref.id).set({
                            "createdDeliberations": [],
                            "participatedDeliberations": [],
                            "email": f"{new_doc_ref.id}@stanford.edu",
                            "uid": new_doc_ref.id,
                        })
            except Exception as e:
                return https_fn.Response(str(e), status=400)
                
            # update the database to show that the job has been run
            firestore_client.collection("deliberations").document(deliberationDocRef).update(
                {"jobRun": True}
            )
            
        # Open the gate
        firestore_client.collection("deliberations").document(deliberationDocRef).update(
            {gateName + "GateOpen": True}
        )

        # Get the next gate
        nextGate = doc.get("gateMap")[gateName]

        # return the next gate as an object with field "nextGate"
        return https_fn.Response(json.dumps({"nextGate": nextGate}))
    
    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def getPageCounts(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]

        # Check if the user is the admin
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        adminId = doc.get("adminID")
        if adminId != user_id:
            return https_fn.Response("User is not the admin", status=401)
        
        # get the page counts
        pageCounts = doc.get("pageCounts")
        # get the pages in the correct order
        orderedPages = ["Initial Waiting Room", "Initial Comments", "Socratic Dialogue", "Comment Voting", "Final Waiting Room"]

        # get the counts in the correct order
        orderedCounts = []
        orderedPagesReduced = []
        for page in orderedPages:
            if page in pageCounts:
                orderedCounts.append(pageCounts[page])
                orderedPagesReduced.append(page)

        # repack everything into the correct format
        pageCounts = [{"page": orderedPagesReduced[i], "count": orderedCounts[i]} for i in range(len(orderedCounts))]

        # return the page counts
        return https_fn.Response(json.dumps(pageCounts))
    
    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def getPageTime(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]
        currentPage = data["currentPage"]

        # Update the time
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        pageTimes = doc.get("timeMap")
        time = pageTimes[currentPage]

        # return JSON object with time
        return https_fn.Response(json.dumps({"time": time}))
    
    except Exception as e:
        return https_fn.Response(str(e), status=400)