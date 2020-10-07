import json
import os
import snyk


def handler(event, context):
    foo = os.getenv("foo", "default")
    body = {
        "test": foo,
        "message": "Hi, I am another lambda function",
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
