import json
import os
import snyk
import requests


def handler(event, context):

    body = {}

    snyk_api_token = os.getenv("SNYK_TOKEN", "could_not_find_token")

    client = snyk.SnykClient(snyk_api_token)
    snyk_orgs = client.organizations.all()
    test_org = client.organizations.first()

    if "command" in event:
        command = event["command"]
        if command == "test_from_url":
            response = requests.get(event["url"])
            result = test_org.test_pipfile(response.text)
            body["result"] = {}
            for res in result.issues.vulnerabilities:
                body["result"][res.title] = res.__dict__

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
