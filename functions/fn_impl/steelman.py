from firebase_functions import https_fn, firestore_fn, options
from firebase_admin import initialize_app, credentials, firestore, auth
from flask import jsonify
import json
import openai


enableCors = options.CorsOptions(
        cors_origins=[r"firebase\.com$", r"https://flutter\.com", r"https://flutter\.com", r"https://deliberationio-yizum0\.flutterflow\.app"],
        cors_methods=["get", "post"],
    )


