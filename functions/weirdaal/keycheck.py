import json
import boto3
import botocore
import pprint
import sys

pp = pprint.PrettyPrinter(indent=5, width=80)

region = 'us-east-1'
regions = ['us-east-1']

def check_root_account(session):
    '''
    Do various checks to see if the account has root or elevated IAM privs
    '''
    client = boto3.client('iam', region_name=region)

    try:
        data = {}
        acct_summary = client.get_account_summary()
        if acct_summary:
            data[f"client {session.get_credentials().access_key}"] = "Root Key!!! This is either a root key or has IAM access"

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
                    print("Unexpected error: {}" .format(e))
        
        return data

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidClientTokenId':
            sys.exit("The AWS KEY IS INVALID. Exiting")
        if e.response['Error']['Code'] == 'AccessDenied':
            print('{} : Is NOT a root key' .format(AWS_ACCESS_KEY_ID))
        elif e.response['Error']['Code'] == 'SubscriptionRequiredException':
            print('{} : Has permissions but isnt signed up for service - usually means you have a root account' .format(AWS_ACCESS_KEY_ID))
        else:
            print("Unexpected error: {}" .format(e))


def handler(event, context):
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event
    try:
        AWS_SECRET_KEY_ID= params['aws_secret_key_id']
        AWS_SECRET_ACCESS_KEY = params['aws_secret_access_key']
    except KeyError:
        return {
            "body": json.dumps({"message": "keys not passed correctly"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 401,
        }
    try:


        session = boto3.Session(AWS_SECRET_KEY_ID, AWS_SECRET_ACCESS_KEY)

        return {
            "body": {"message": check_root_account(session)},
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }
    except Exception as e:
        message = e.message if hasattr(e,'message') else e
        return {
            "body": {"message": message},
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }

if __name__ == "__main__":
    test_event = {}
    test_context = {}
    with open("tests/test.json") as test_json:
        test_event = json.load(test_json)
    test_res = handler(test_event, test_context)
    print(test_res)
