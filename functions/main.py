"""
This file contains the main functions that are deployed to the Firebase Cloud Functions.
Authors: Chinmaya, Guinness
"""

# import the functions from the implementation files
from fn_impl.home import *
from fn_impl.createTopic import *
from fn_impl.round1 import *
from fn_impl.round2 import *
from fn_impl.admin import *
from fn_impl.socratic import *

# initialize the app
initialize_app()


exp1234567 = {
    "Waiting Room" : "Round 1",
    "Round 1" : "Waiting Room",
    "Waiting Room" : "Socratic Dialogue",
    "Socratic Dialogue" : "Waiting Room",
    "Waiting Room" : "Round 2"
}

exp89 = {
    "Waiting Room" : "Round 1",
    "Round 1" : "Waiting Room",
    "Waiting Room" : "Round 2"
}