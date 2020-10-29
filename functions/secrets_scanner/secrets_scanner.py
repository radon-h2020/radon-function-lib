# this python program was written using python 3.8.6
import json
import uuid
import os
import glob
import zipfile
from typing import Callable
import requests

# This lambda function takes a cloudstash.io function artifact and
# and scans all of the files for secrets/credentials/token/keys

# either get the hostname from env variable, or use the default
CLOUDSTASH_HOSTNAME = os.getenv("CLOUDSTASH_HOSTNAME", "https://cloudstash.io")
# the endpoint from where to download artifacts
CLOUDSTASH_DOWNLOAD_ENDPOINT = os.getenv("CLOUDSTASH_DOWNLOAD_ENDPOINT", "artifact_download")
# the unique identifier for this invocation, used to create a unique directory to store temporary files
INVOCATION_UUID = uuid.uuid4()
# prefix for error messages:
ERROR_PREFIX = "ERROR:"
# the temporary directory the artifact will be downloaded to
ARTIFACT_DOWNLOAD_LOCATION = f"/tmp/artifact_{INVOCATION_UUID}"
# the directory where artifact files will be extracted to
ARTIFACT_EXTRACT_LOCATION = f"{ARTIFACT_DOWNLOAD_LOCATION}/extracted"
# the absolute path of the downloaded artifact zip file
ARTIFACT_ZIP_FILE = f"{ARTIFACT_DOWNLOAD_LOCATION}/artifact.zip"
# the default output format to use if none is specified
DEFAULT_OUTPUT_FORMAT = "full"


def handler(event, context):

    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse parameters and load envrironment variables
    param_error, artifact_url, artifact_id, output_format = parse_parameters(params=parameters)
    if param_error:
        return param_error

    # download the artifact zip file into a directory /tmp/<inovocation uuid>/artifact.zip
    artifact_download_error = get_artifact(url=artifact_url)
    if artifact_download_error:
        return artifact_download_error

    scan_errors, scan_result = scan_for_secrets()

    # only attempt to format if there are any vulnerabilitues
    body = None
    if scan_result:
        #  format_error, formatted_vulnerabilities = format_vulnerabilities(
        #  output_format=output_format, vulnerabilities=vulnerabilities
        #  )
        #  if format_error:
        #  return format_error
        #  if formatted_vulnerabilities:
        #  body = formatted_vulnerabilities
        body = {}
    else:
        body = "No vulnerabilities found."

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def scan_for_secrets():
    pass


def get_artifact(url: str) -> str:
    error = None
    # create the directories, creating any parent directories needed
    os.makedirs(ARTIFACT_EXTRACT_LOCATION, exist_ok=True)
    # download the zipfile
    request = requests.get(url=url, stream=True)
    downloaded_successfully = False
    if request.ok:
        # write the downloaded file as a stream to the zipfile
        with open(ARTIFACT_ZIP_FILE, "wb") as writeable_zip_file:
            for chunk in request.iter_content(chunk_size=128):
                writeable_zip_file.write(chunk)
            downloaded_successfully = True
    else:
        error = f"{ERROR_PREFIX} could not download the specified artifact, please verify that the url/id is correct."

    if downloaded_successfully and zipfile.is_zipfile(ARTIFACT_ZIP_FILE):
        try:
            with zipfile.ZipFile(ARTIFACT_ZIP_FILE, "r") as zf:
                # TODO maybe refactor this to use ZipFile.extract() instead
                # as there is a warning in the documentation about absolute file paths
                # https://docs.python.org/3.8/library/zipfile.html#zipfile.ZipFile.extractall
                zf.extractall(ARTIFACT_EXTRACT_LOCATION)
        except RuntimeError:
            error = f"{ERROR_PREFIX} There was an error extracting the artifact zip file."

    return error


def parse_parameters(params: dict) -> (str, str, str):

    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None

    if "artifact_url" in params:
        url = params["artifact_url"]
        artifact_url = url
        # if url ends on / remove it, to make parsing the id easier
        if url[len(url) - 1] == "/":
            url = url[:-1]
        _, artifact_id = os.path.split(url)
    elif "artifact_id" in params:
        artifact_url = f"{CLOUDSTASH_HOSTNAME}/{CLOUDSTASH_DOWNLOAD_ENDPOINT}/{params['artifact_id']}"
        artifact_id = params["artifact_id"]
    else:
        artifact_url = None
        artifact_id = None
        error = f"{ERROR_PREFIX} No URL was provided for a CloudStash artifact, you must provide either a url as 'artifact_url':'<url>' or the CloudStash artifact ID as 'artifact_id':'<id>'"

    # parse the ourput format to return data in
    if "output_format" in params:
        of = params["output_format"]
        if of == "human" or of == "full":
            output_format = params["output_format"]
        else:
            error = f"{ERROR_PREFIX} Invalid output format, must one of 'human', 'full'."
    else:
        output_format = DEFAULT_OUTPUT_FORMAT

    return error, artifact_url, artifact_id, output_format


# test the code locally
# will only be run if called from cli
if __name__ == "__main__":
    from pprint import pprint

    test_event = {}
    # test cases
    test_json_file = ""
    with open(test_json_file) as test_json:
        test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    #  pprint(json.loads(test_res["body"]))
    print(test_res)
