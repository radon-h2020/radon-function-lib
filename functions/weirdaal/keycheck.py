import json
import boto3
import botocore
import sys

region = 'us-east-1'
regions = ['us-east-1']

def check_root_account(session):
    '''
    Do various checks to see if the account has root or elevated IAM privs
    '''
    try:
        client = session.client('iam', region_name=region)
        
        data = {}
        acct_summary = client.get_account_summary()
        if acct_summary:
            data[f"User {session.get_credentials().access_key}"] = "Root Key!!! This is either a root key or has IAM access"

        client_list = client.list_users()
        for user in client_list['Users']:
            try:
                profile = client.get_login_profile(UserName=user['UserName'])
                if profile:
                    mfa = client.list_mfa_devices(UserName=user['UserName'])
                    data[user['UserName']] = {"console access": True, "account last used" : user['PasswordLastUsed'].strftime("%m/%d/%Y, %H:%M:%S"), "MFA": mfa['MFADevices']}
                else:
                    data[user['UserName']] = "likely doesnt have console access"
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    data[user['UserName']] = "likely doesnt have console access"
                else:
                    return e
        return data
    except botocore.exceptions.ClientError as e:
        return e.response['Error']['Message']        


def handler(event, context):
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event
    try:
        AWS_SECRET_KEY_ID= params['aws_secret_key_id']
        AWS_SECRET_ACCESS_KEY = params['aws_secret_access_key']

        session = boto3.Session(AWS_SECRET_KEY_ID, AWS_SECRET_ACCESS_KEY)
        data = check_root_account(session)
        return {
            "body": data,
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }
    except KeyError:
        return {
            "body": json.dumps({"message": "keys not passed correctly"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 401,
        }

if __name__ == "__main__":
    test_event = {}
    test_context = {}
    with open("tests/test.json") as test_json:
        test_event = json.load(test_json)
    test_res = handler(test_event, test_context)
    print(test_res)
