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