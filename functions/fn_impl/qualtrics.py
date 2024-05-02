import os
import requests


# QUALTRICS
# # Setting user Parameters
# apiToken = "m62BiuqMZnT2373IRVojOx5a90EVHcuNzavS58jX" # Replace with Account API Token
# dataCenter = "ca1"

# baseUrl = "https://{0}.qualtrics.com/API/v3/survey-definitions".format(
#     dataCenter)
# headers = {
#     "x-api-token": apiToken,
#     "content-type": "application/json",
#     "Accept": "application/json"
# }

# data = {"SurveyName": "My New Survey","Language": "EN","ProjectCategory": "CORE"}

# response = requests.post(baseUrl, json=data, headers=headers)
# print(response.text)





import os
import requests

apiToken = "m62BiuqMZnT2373IRVojOx5a90EVHcuNzavS58jX"
dataCenter = "ca1"
library_id = "UR_8jDTL4gXw0OVIN0"

# Create Survey
baseUrl = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions"
headers = {
    "x-api-token": apiToken,
    "content-type": "application/json",
    "Accept": "application/json"
}
data = {"SurveyName": "Bananas Survey", "Language": "EN", "ProjectCategory": "CORE"}

response = requests.post(baseUrl, json=data, headers=headers)
if response.status_code == 200:
    survey_id = response.json()['result']['SurveyID']
    print("Survey created successfully with ID:", survey_id)
else:
    print("Failed to create survey:", response.text)
    exit()  # Exit if survey creation fails to prevent further errors

# Upload Image
image_path = 'banana.jpeg'  # Make sure the path is correct
files = {'file': ('banana.jpeg', open(image_path, 'rb'), 'image/jpeg')}
upload_url = f"https://{dataCenter}.qualtrics.com/API/v3/libraries/{library_id}/graphics"
response = requests.post(upload_url, files=files, headers=headers)

if response.status_code == 200:
    graphic_id = response.json()['result']['id']
    print("Image uploaded successfully with ID:", graphic_id)
else:
    print("Failed to upload image:", response.text)
    exit()  # Exit if image upload fails

# Add Question with Image
question_data = {
    "QuestionText": "What do you think about this image?",
    "DataExportTag": "Q1",
    "QuestionType": "MC",
    "Selector": "SAVR",
    "Configuration": {
        "QuestionDescriptionOption": "UseText"
    },
    "Choices": {
        "1": {
            "Display": f"<img src='graphic://{graphic_id}' alt='description' style='width: 100%; max-width: 500px;'>"
        }
    }
}

questions_url = f"https://{dataCenter}.qualtrics.com/API/v3/survey-definitions/{survey_id}/questions"
response = requests.post(questions_url, json=question_data, headers=headers)

if response.status_code == 200:
    print("Question added successfully.")
else:
    print("Failed to add question:", response.text)