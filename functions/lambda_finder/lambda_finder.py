# this python program was written using python 3.8.6
import json
import boto3

# use list_lambas to find lambdas
import list_lambdas


# this lambda function ...


def handler(event, context):

    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse parameters and load envrironment variables
    param_error = parse_parameters(params=parameters)
    if param_error:
        return param_error

    lambda_finder_error, found_lambdas = find_lambdas()

    # only attempt to format if there are any vulnerabilitues
    body = None
    if found_lambdas:
        body = found_lambdas
    else:
        body = "No vulnerabilities found."

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def find_lambdas():
    error = None

    import argparse

    parser = argparse.ArgumentParser(
        description=("Enumerates Lambda functions from every region with " "interesting metadata.")
    )

    parser.add_argument(
        "--all",
        dest="should_print_all",
        default=False,
        action="store_true",
        help=("Print all the information to the screen " "(default: print summarized information)."),
    )
    parser.add_argument("--csv", type=str, help="CSV filename to output full table data.", metavar="output_filename")
    parser.add_argument(
        "--token-key-id",
        type=str,
        help=("AWS access key id. Must provide AWS secret access key as well " "(default: from local configuration)."),
        metavar="token-key-id",
    )
    parser.add_argument(
        "--token-secret",
        type=str,
        help=("AWS secret access key. Must provide AWS access key id " "as well (default: from local configuration."),
        metavar="token-secret",
    )
    parser.add_argument(
        "--inactive-days-filter",
        type=int,
        help="Filter only Lambda functions with minimum days of inactivity.",
        default=0,
        metavar="minimum-inactive-days",
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        help=(
            "Column name to sort by. Options: region, " "last-modified, last-invocation, " "runtime (default: region)."
        ),
        default="region",
        metavar="sort_by",
    )
    parser.add_argument(
        "--profile",
        type=str,
        help=("AWS profile. Optional " '(default: "default" from local configuration).'),
        metavar="profile",
    )

    SORT_KEYS = ["region", "last-modified", "last-invocation", "runtime"]
    arguments = parser.parse_args()
    if arguments.sort_by not in SORT_KEYS:
        print("ERROR: Illegal column name: {0}.".format(arguments.sort_by))
        exit(1)

    function_data = list_lambdas.print_lambda_list(arguments)

    return error, function_data


def parse_parameters(params: dict) -> (str, str, str):

    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None

    # TODO

    #  if "artifact_url" in params:
    #  url = params["artifact_url"]
    #  artifact_url = url
    #  # if url ends on / remove it, to make parsing the id easier
    #  if url[len(url) - 1] == "/":
    #  url = url[:-1]
    #  _, artifact_id = os.path.split(url)
    #  elif "artifact_id" in params:
    #  artifact_url = f"{CLOUDSTASH_HOSTNAME}/{CLOUDSTASH_DOWNLOAD_ENDPOINT}/{params['artifact_id']}"
    #  artifact_id = params["artifact_id"]
    #  else:
    #  artifact_url = None
    #  artifact_id = None
    #  error = f"{ERROR_PREFIX} No URL was provided for a CloudStash artifact, you must provide either a url as 'artifact_url':'<url>' or the CloudStash artifact ID as 'artifact_id':'<id>'"

    #  return error, artifact_url, artifact_id

    return error


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
    pprint(json.loads(test_res["body"]))
    #  print(test_res)
    #  pprint(test_res)
