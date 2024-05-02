from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai
from utils import *

enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app", r"https://deliberationiobeta2\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )


"""
Description of what we need to implement:

- API that takes in deliberationDocRef and currentPage, then returns next page
    - This will be used by the front end to navigate between pages
    - Inside our database, there will be a map from page to next page, so we can easily look up the next page
    - This design will allow for modular changes to the order of pages

- API that returns whether or not the "gate" is open for the deliberation
    - This will be polled by the front end while the user is in the initial waiting room.
    - It checks a boolean in the database to see if the gate is open
    - There is a seperate API that the admin can call to open the gate

- Exactly the same as above but for the final gate before the results page

- API that takes in the current page and deliberationDocRef, and returns nothing
    - This will be called by the front end on page load
    - This lets the backend know that the user is on the page
    - There will be an integer in the database that keeps track of how many users are on each page
    - This will ultimately let the admin know how many users are on each page, so they know when to open the initial gate and the final gate

- API that takes in the deliberationDocRef, checks whether or not the user is the admin, and if so, opens the gate

- Same as above but for the final gate
    
- API that takes in the deliberationDocRef, checks if the user is the admin, and if so, returns the count of users on each page
    - This will be polled by the front end when the admin is on the dashboard page
    - This is so the admin can see how many users are on each page, and decide when to open the gates

"""





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
def isInitialGateOpen(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]

        # Get the gate status from the database
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        gateOpen = doc.get("initialGateOpen")

        # return the gate status
        return https_fn.Response(str(gateOpen))

    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def isFinalGateOpen(request):
    try:
        # authenticate the user
        token = request.headers.get("Authorization").split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token["user_id"]

        # Parse JSON directly from request body
        data = request.get_json()
        deliberationDocRef = data["deliberationDocRef"]

        # Get the gate status from the database
        firestore_client = firestore.client()
        doc = firestore_client.collection("deliberations").document(deliberationDocRef).get()
        gateOpen = doc.get("finalGateOpen")

        # return the gate status
        return https_fn.Response(str(gateOpen))

    except Exception as e:
        return https_fn.Response(str(e), status=400)

# lets unify the isInitialGateOpen and isFinalGateOpen into one function that takes in a gateName parameter and returns whether or not that gate is open

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
def openInitialGate(request):
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
        
        # Open the gate
        firestore_client.collection("deliberations").document(deliberationDocRef).update(
            {"initialGateOpen": True}
        )

        # return nothing
        return https_fn.Response("success")
    
    except Exception as e:
        return https_fn.Response(str(e), status=400)

@https_fn.on_request(cors=enableCors)
def openFinalGate(request):
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
        
        # Open the gate
        firestore_client.collection("deliberations").document(deliberationDocRef).update(
            {"finalGateOpen": True}
        )

        # return nothing
        return https_fn.Response("success")
    
    except Exception as e:
        return https_fn.Response(str(e), status=400)

# I want to combine openInitialGate and openFinalGate into one function in order to make it more general. The new implementation will have 4 gates actually, not just 
# initial and final. It will take in a gateName parameter and open the gate with that name. Then it will return what the next gate is. If the gateName is the last gate,
# it will return "none". This will be useful for the front end to know what the next gate is.

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
                isSteelman = topic_doc['isSteelman'].strip() == 'Yes'
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
                        {"role" : "user", "content" : STEELMAN_PROMPT.format(topic_doc['topic'], MAX_K, MAX_K, MAX_K, comments_list_formatted)}
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
                {"socraticJobRun": True}
            )
            
        # Open the gate
        firestore_client.collection("deliberations").document(deliberationDocRef).update(
            {gateName + "GateOpen": True}
        )

        # Get the next gate
        nextGate = doc.get("nextGate")[gateName]

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
        for page in orderedPages:
            if page in pageCounts:
                orderedCounts.append(pageCounts[page])

        # repack everything into the correct format
        pageCounts = [{"page": orderedPages[i], "count": orderedCounts[i]} for i in range(len(orderedPages))]

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