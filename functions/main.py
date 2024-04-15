"""
This file contains the main functions that are deployed to the Firebase Cloud Functions.
Authors: Chinmaya, Guinness
"""

# import the functions from the implementation files
from fn_impl.home import *
from fn_impl.createTopic import *
from fn_impl.round1 import *

# initialize the app
initialize_app()


