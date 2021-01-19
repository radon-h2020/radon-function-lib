import os
import json
from base64 import b64decode
import requests

# "Have I Been Pwned" requires and api token in order to make calls to the api
API_KEY_ENV = os.getenv("HIBP_KEY")


def handler(event,context):
  # retrieve body and email to verify risk factor
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event
    
    error,email,api_key = parse_parameters(params)

    if error:
        return {
                'body': json.dumps({'message':"Either email or api-key is not provided"}),
                'headers': {'Content-Type': 'application/json'},
                'statusCode': 401
            }

    response = make_request(email,api_key)

    if response:
        return {
                'body': json.dumps({'message':f"this email has been breached in the following data leaks {json.loads(response)}"}),
                'headers': {'Content-Type': 'application/json'},
                'statusCode': 200
            }
    else:
        return {
                'body': json.dumps({'message': 'this email has not been included in any known data leaks'}),
                'headers': {'Content-Type': 'application/json'},
                'statusCode': 200
            }


#######################
#   Helper functions  #
#######################

def parse_parameters(params):
    try:
        email = params['email']
        if 'api_key' in params:
            api_key = params['api_key']
        else:
            api_key = API_KEY_ENV
    except KeyError as e:
        return e,"",""
    return None,email,api_key

def make_request(email,api_key):
    URL = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    response = requests.get(URL, headers={'hibp-api-key': api_key})

    return response.text