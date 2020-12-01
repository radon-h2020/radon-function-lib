# this python program was written using python 3.8.6
import json
import sys

# add the observatory package to module import path
sys.path.append("http-observatory")
# import the http scan command
from httpobs.scanner.local import scan as observatory_scan

"""
This lambda function takes a URL and uses Observatory to provide
an overview of the HTTP securitory of the site.
The function uses Observatory, developed by Mozilla - github.com/mozilla/http-observatory
This function was developed by @zanderhavgaard
"""

# prefix for error messages:
ERROR_PREFIX = "ERROR:"
# default output format to use
DEFAULT_OUTPUT_FORMAT = "full"
ALLOWED_OUTPUT_FORMATS = ["full", "human"]


def handler(event, context):
    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse parameters and load envrironment variables
    param_error, url, output_format = parse_parameters(params=parameters)
    if param_error:
        return param_error

    # use observatory to scan the provided url
    scan_error, scan_result = scan_url(url=url)
    if scan_error:
        return scan_error

    # format the recieved result
    format_error, formatted_result = format_scan_result(url=url, result=scan_result, output_format=output_format)

    # set the response body
    body = formatted_result

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def format_scan_result(url: str, result: dict, output_format: str) -> (str, dict):
    error = None
    if output_format == "full":
        # for the full output, do not modify anything
        result["URL"] = url
        return error, result
    elif output_format == "human":
        sc = result["scan"]
        human_result = {
            "URL": url,
            "Grade": sc["grade"],
            "Score": sc["score"],
            "Tests Passed": f"{sc['tests_passed']}/{sc['tests_quantity']}",
        }
        return error, human_result


def scan_url(url: str) -> (str, str):
    # scan a provided url using observatory
    error = None
    try:
        result = observatory_scan(url)
    except Exception:
        error = f"{ERROR_PREFIX} there was an error scanning the URL, please check that the URL is valid."

    return error, result


def parse_parameters(params: dict) -> (str, str, str):
    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None

    if "url" in params:
        url = params["url"]
    else:
        url = None
        error = f"{ERROR_PREFIX} you must include a url to scan, use the key 'url' to specify."

    if "output_format" in params:
        output_format = params["output_format"]
        if output_format not in ALLOWED_OUTPUT_FORMATS:
            error = f"{ERROR_PREFIX} the 'output_format' specified is not valid, must be one of 'full' or 'human'"
    else:
        output_format = DEFAULT_OUTPUT_FORMAT

    return error, url, output_format


# psycopg2==2.8.6

# test the code locally
# will only be run if called from cli
if __name__ == "__main__":
    from pprint import pprint

    #  test_json_file = "tests/test_url1.json"
    test_json_file = "tests/test_url2.json"
    #  test_json_file = "tests/test_url3.json"
    test_event = {}
    # test cases
    with open(test_json_file) as test_json:
        test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    pprint(json.loads(test_res["body"]))
