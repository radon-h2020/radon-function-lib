import json

# aws creds
aws_access_key_id = ("AKIAJIS5NP79GW2AYZHA",)
aws_secret_access_key = "lxRV/uiC4kmZQryIZxSSlQ6xNlZMjo4kn+LnjNiF"


def lambda_handler(event, context):
    # TODO implement
    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}
