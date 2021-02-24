# this python program was written using python 3.8.6
import json
import uuid
import os
import glob
import zipfile
from typing import Callable
import snyk
import requests

# This lambda function takes a cloudstash.io function artifact and
# returns a list of vulnerabilities in the codes/dependencies as reported by snyk

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
# a personal snyk api key is necassary in order to scan the artifact
SNYK_API_KEY = os.getenv("SNYK_API_KEY")


def handler(event, context):

    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse parameters and load envrironment variables
    param_error, snyk_api_key, artifact_url, artifact_id, output_format = parse_parameters(params=parameters)
    if param_error:
        return param_error

    # create the snyk org object to test files with
    # also verifies that the api key is valid
    org_error, snyk_org = get_snyk_org(snyk_api_key=snyk_api_key)
    if org_error:
        return org_error

    # download the artifact zip file into a directory /tmp/<inovocation uuid>/artifact.zip
    artifact_download_error = get_artifact(url=artifact_url)
    if artifact_download_error:
        return artifact_download_error

    # what runtime does the function use?
    runtime_interpolation_error, runtime = get_function_runtime(artifact_id=artifact_id)
    if runtime_interpolation_error:
        return runtime_interpolation_error

    # vulnerabilities will be a list of snyk.api_response.issues.vulnerabilities
    # if any vulnerabilities are found, otherwise will be an empty list
    test_error, vulnerabilities = test_dependencies_for_vulnerabilities(
        runtime=runtime, artifact_location=ARTIFACT_EXTRACT_LOCATION, snyk_org=snyk_org
    )
    if test_error:
        return test_error

    # only attempt to format if there are any vulnerabilitues
    body = None
    if vulnerabilities:
        format_error, formatted_vulnerabilities = format_vulnerabilities(
            output_format=output_format, vulnerabilities=vulnerabilities
        )
        if format_error:
            return format_error
        if formatted_vulnerabilities:
            body = formatted_vulnerabilities
    else:
        body = "No vulnerabilities found."

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def format_vulnerabilities(output_format: str, vulnerabilities: list) -> (str, list):
    error = None
    formatted_vulnerabilities = []

    if output_format == "human":
        for vuln in vulnerabilities:
            # parse a selection of fields and label for humans to read
            human_readable_vuln = {
                "Title": vuln.title,
                "Snyk ID": vuln.id,
                "Snyk URL": vuln.url,
                "Package": f"{vuln.package}:{vuln.version}",
                "Severity": vuln.severity,
                "CVSS Score": vuln.cvssScore,
                "CVE": vuln.identifiers,
                "Description": vuln.description,
            }
            formatted_vulnerabilities.append(human_readable_vuln)
    elif output_format == "full":
        for vuln in vulnerabilities:
            # parse all fields of the snyk object to a JSON parseable dict
            formatted_vulnerabilities.append(vuln.__dict__)
    else:
        error = f"{ERROR_PREFIX} Could not format vulnerabilities using the specified output format: {output_format}"

    return error, formatted_vulnerabilities


def test_dependency_file(
    snyk_test_func: Callable[[str], list],
    dependency_file_name: str,
    artifact_location: str,
) -> (str, list):
    error = None
    vulns = []

    # use glob to recursively find the path to the dependency file if it is not in the root
    dependency_file = (
        None
        if not glob.glob(pathname=f"{artifact_location}/**/{dependency_file_name}", recursive=True)
        else glob.glob(pathname=f"{artifact_location}/**/{dependency_file_name}", recursive=True)[0]
    )

    if dependency_file:
        with open(dependency_file, "r") as df:
            try:
                # use the snyk test function supplied
                api_response = snyk_test_func(df)
                if api_response.issues.vulnerabilities:
                    vulns = api_response.issues.vulnerabilities
            except Exception:
                error = f"{ERROR_PREFIX} There was an error getting the vulnerabilities for the artifact."
    else:
        error = f"{ERROR_PREFIX} No {dependency_file_name} file could be found, please include it in the root of the function archive."

    return error, vulns


def test_dependencies_for_vulnerabilities(runtime: str, artifact_location: str, snyk_org: snyk.client) -> (str, list):
    # use the appropriate snyk test function based on the runtime
    # TODO figure out some way of differentiating between runtimes with multiple
    # dependency file types, like for java - gradle vs maven
    if runtime == "node":
        return test_dependency_file(
            snyk_test_func=snyk_org.test_packagejson,
            dependency_file_name="package.json",
            artifact_location=artifact_location,
        )
    return (f"{ERROR_PREFIX} runtime is not supported.", None)


def get_function_runtime(artifact_id: str) -> (str, str):
    # query the cloudstash artifact for it's runtime
    error = None
    runtime = None

    cloudstash_url = f"https://cloudstash.io/artifact/{artifact_id}"
    response = requests.get(cloudstash_url)
    if response.status_code == 200:
        groupid = response.json()["groupId"]
    else:
        error = f"{ERROR_PREFIX} could not get cloudstash artifact metadata, make sure that the artifact id is correct."

    if "node" in groupid:
        runtime = "node"

    return error, runtime


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


def get_snyk_org(snyk_api_key: str) -> (str, str):
    error = None
    org = None
    # create the snyk client
    try:
        client = snyk.SnykClient(snyk_api_key)
        # create the orgianzation to use for testing
        org = client.organizations.first()
    # if the api key is invalid, return an error
    except snyk.errors.SnykHTTPError:
        error = f"{ERROR_PREFIX} Provided Snyk API key is not valid."
    return error, org


def parse_parameters(params: dict) -> (str, str, str):

    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None

    # load snyk api token from environment if it is not provided
    snyk_api_key = params["body"]["snyk_api_key"] if "snyk_api_key" in params else SNYK_API_KEY
    # if api key is not set, return error
    if snyk_api_key is None:
        error = f"{ERROR_PREFIX} Could not find a Snyk API key, please set the 'SNYK_API_KEY' environment variable, or pass the API key as an argument: 'snyk_api_key':<api_key>."

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

    return error, snyk_api_key, artifact_url, artifact_id, output_format


# test the code locally
# will only be run if called from cli
if __name__ == "__main__":
    from pprint import pprint

    test_event = {}
    # test cases
    test_json_file = "tests/test_artifact_url_vulnerable.json"
    #  test_json_file = "tests/test_artifact_id_vulnerable.json"
    #  test_json_file = "tests/test_artifact_id_no_vulnerabilities.json"
    #  test_json_file = "tests/node_test_artifact_vulns.json"
    #  test_json_file = "tests/node_test_artifact_no_vulns.json"
    with open(test_json_file) as test_json:
        test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    #  pprint(json.loads(test_res["body"]))
    print(test_res)
