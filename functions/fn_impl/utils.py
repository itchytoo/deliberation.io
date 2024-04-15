NUM_OPTIONS = 5
OPTIONS = {
    "round1" : ["Include seed comments", "No seed comments"],
    "intervention" : ["Socratic dialogue", "Comment feedback", "Socratic dialogue and comment feedback", "None"],
    "round2" : ["Raw comments, randomized", "Steelman arguments, randomized", "Raw comments, ordered", "Steelman arguments, ordered"],
    "round3" : ["Revote", "None"]
}
OPTIONAL_KEYS = set(["intervention", "round3"])