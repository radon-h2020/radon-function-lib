# this python program was written using python 3.8.6
# by @zanderhavgaard

import json
import argparse
import os
# use list_lambas to find lambdas
import list_lambdas

# this lambda function scans all AWS regions for deployed lambda functions and returns a JSON list
# with information about deployed lambdas
# uses 'list-lambdas' by @epsagon: https://github.com/epsagon/list-lambdas


def handler(event, context):

    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse parameters and load envrironment variables
    param_error, key, secret_key = parse_parameters(params=parameters)
    if param_error:
        return param_error

    # TODO remove
    print(key, secret_key)

    # find lambdas
    lambda_finder_error, found_lambdas = find_lambdas(aws_key=key, aws_secret_key=secret_key)
    if lambda_finder_error:
        return lambda_finder_error

    # return a message if no lambdas were found
    body = None
    if found_lambdas:
        body = found_lambdas
    else:
        body = "No lambdas found."

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def find_lambdas(aws_key: str, aws_secret_key: str) -> (str, dict):
    error = None
    function_data = None

    arguments = argparse.Namespace(
        csv=None,
        inactive_days_filter=0,
        profile=None,
        should_print_all=False,
        sort_by="region",
        token_key_id=aws_key,
        token_secret=aws_secret_key,
    )

    # TODO uncomment
    #  try:
    #  function_data = list_lambdas.print_lambda_list(arguments)
    #  except Exception:
    #  error = f"ERROR: There was an error when getting the list of lambdas."

    function_data = list_lambdas.print_lambda_list(arguments)

    return error, function_data


def parse_parameters(params: dict) -> (str, str, str):

    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None

    # aws key and secret key to allow to find lambdas
    key = None
    secret_key = None

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

    return error, key, secret_key

# test the code locally
# will only be run if called from cli
if __name__ == "__main__":
    from pprint import pprint

    test_event = {}
    # test cases
    #  test_json_file = ""
    #  with open(test_json_file) as test_json:
    #  test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    print(test_res)

    #  pprint(json.loads(test_res["body"]))
    #  print(test_res)
    #  pprint(test_res)
