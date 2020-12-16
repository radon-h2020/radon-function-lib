# this python program was written using python 3.6.5

"""
This lambda function will provide a report of AWS resources that should be cleaned up (deleted)
based on ......
TODO

aws_cleanup by Praqma/Eficode https://github.com/Praqma/aws-cleanup (private repo)
modified by @zanderhavgaard

This function developed by @zanderhavgaard
"""

import os
import argparse
import json
from instance_cleaner import cleanup

ERROR_PREFIX = "ERROR:"


def handler(event, context):

    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse parameters and load envrironment variables
    param_error, key, secret_key, dry_run = parse_parameters(params=parameters)
    if param_error:
        return param_error

    # TODO remove
    #  print(key, secret_key)

    clean_error, report = clean_aws_resources(aws_key=key, aws_secret=secret_key, dry_run=dry_run)
    if clean_error:
        return clean_error

    body = report

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def clean_aws_resources(
    aws_key: str,
    aws_secret: str,
    dry_run: bool,
):
    error = None

    # TODO uncomment
    #  try:
    report = cleanup(aws_key=aws_key, aws_secret=aws_secret, dry_run=dry_run)
    #  except Exception:
    #  error = f"{ERROR_PREFIX} there was an error cleaning the resources, verify that the AWS credentials are valid and have the appropirate permissions."

    return error, report


def parse_parameters(params: dict) -> (str, str, str, bool):

    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None

    # aws key and secret key to allow to find lambdas
    key = None
    secret_key = None
    # default to dry run
    dry_run = True

    if "dry_run" in params:
        # python is a bit particular with parsing strings to booleans..
        dry_run = params["dry_run"].lower() == "true"
    else:
        error = f"{ERROR_PREFIX} 'dry_run' must be one of 'true' or 'false'."

    if "aws_key" in params:
        key = params["aws_key"]
    elif "AWS_KEY" in os.environ:
        key = os.getenv("AWS_KEY", None)
    else:
        return (
            "Could not parse an aws_key, you must either set one as an environment variable or provide one with as the 'aws_key' argument.",
            None,
            None,
        )

    if "aws_secret" in params:
        secret_key = params["aws_secret"]
    elif "AWS_SECRET" in os.environ:
        secret_key = os.getenv("AWS_SECRET", None)
    else:
        return (
            "Could not parse an aws_secret, you must either set one as an environment variable or provide one with as the 'aws_secret' argument.",
            None,
            None,
        )

    return error, key, secret_key, dry_run


# test the code locally
# will only be run if called from cli
if __name__ == "__main__":
    from pprint import pprint

    test_event = {}
    # test cases
    test_json_file = "tests/test1.json"
    with open(test_json_file) as test_json:
        test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    #  print(test_res)
    pprint(object=json.loads(test_res["body"]), width=120)
    #  print(test_res)
    #  pprint(test_res)
