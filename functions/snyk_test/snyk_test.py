# this python program was written using python 3.8.6
import json
import uuid
import os
import snyk
import requests
import zipfile
import dependency_tester

# This lambda function takes a cloudstash.io function artifact and
# returns a list of vulnerabilities in the codes/dependencies as reported by snyk

# either get the hostname from env variable, or use the default
CLOUDSTASH_HOSTNAME = os.getenv("CLOUDSTASH_HOSTNAME", "https://cloudstash.io")
# the endpoint from where to download artifacts
CLOUDSTASH_DOWNLOAD_ENDPOINT = os.getenv("CLOUDSTASH_DOWNLOAD_ENDPOINT", "artifact_download")
# the unique identifier for this invocation, used to create a unique directory to store temporary files
#  INVOCATION_UUID = uuid.uuid4()
# TODO change back after debug
INVOCATION_UUID = "ed0de8dc-0309-402d-ad2e-c9b82b4c11a6"
# prefix for error messages:
ERROR_PREFIX = "ERROR:"
# the temporary directory the artifact will be downloaded to
ARTIFACT_DOWNLOAD_LOCATION = f"/tmp/artifact_{INVOCATION_UUID}"
# the directory where artifact files will be extracted to
ARTIFACT_EXTRACT_LOCATION = f"{ARTIFACT_DOWNLOAD_LOCATION}/extracted"
# the absolute path of the downloaded artifact zip file
ARTIFACT_ZIP_FILE = f"{ARTIFACT_DOWNLOAD_LOCATION}/artifact.zip"
# the default output format to use if none is specified
DEFUALT_FORMAT = "human"


def handler(event, context):

    # parse parameters and load envrironment variables
    param_error, snyk_api_key, artifact_url = parse_parameters(params=event)

    if param_error:
        return param_error

    # create the snyk org object to test files with
    # also verifies that the api key is valid
    org_error, snyk_org = get_snyk_org(snyk_api_key=snyk_api_key)

    if org_error:
        return org_error

    # download the artifact zip file into a directory /tmp/<inovocation uuid>/artifact.zip
    # TODO reenable
    #  artifact_download_error = get_artifact(url=artifact_url)

    #  if artifact_download_error:
    #  return artifact_download_error

    # what runtime does the function use?
    runtime_interpolation_error, runtime = interpolate_function_runtime()

    if runtime_interpolation_error:
        return runtime_interpolation_error

    test_error, vulnerabilities = test_dependencies_for_vulnerabilities(
        runtime=runtime, artifact_location=ARTIFACT_EXTRACT_LOCATION, snyk_org=snyk_org
    )

    if test_error:
        return test_error

    # TODO should be parsed from paramter
    output_format = "human"

    format_error, formatted_vulnerabilities = format_vulnerabilities(
        output_format=output_format, vulnerabilities=vulnerabilities
    )

    if format_error:
        return format_error

    # TODO finish
    # the body containing response data
    body = {}
    body = vulnerabilities
    #  body["vulnerabilities"] = vulnerabilities
    # build the response
    jsonified_body = json.dumps(body)
    response = {"statusCode": 200, "body": jsonified_body}
    #  response = {"statusCode": 200, "body": body}

    return response


def format_vulnerabilities(output_format: str, vulnerabilities: list) -> (str, list):
    error = None
    formatted_vulnerabilities = []

    if output_format == "human":
        for vuln in vulnerabilities:
            human_readable_vuln = {
                vuln.title: {
                    "Title": vuln.title,
                    "Snyk ID": vuln.id,
                    "Snyk URL": vuln.url,
                    "Package": vuln.package,
                    "Package Version": vuln.version,
                    "Severity": vuln.severity,
                    "CVSS Score": vuln.cvssScore,
                    "Description": vuln.description,
                }
            }
            formatted_vulnerabilities.append(human_readable_vuln)
    elif output_format == "full":
        for vuln in vulnerabilities:
            # parse all fields of the snyk object to a JSON parseable dict
            formatted_vulnerabilities.append(vuln.__dict__)
    else:
        error = f"{ERROR_PREFIX} Could not format vulnerabilities using the specified output format: {output_format}"

    return error, formatted_vulnerabilities


def test_dependencies_for_vulnerabilities(
    runtime: str, artifact_location: str, snyk_org: snyk.client.Organization
) -> (str, list):
    error = None
    # polymorhic tester, does different tests depending on the runtime and project type
    error, tester = create_dependency_tester(runtime=runtime, snyk_org=snyk_org)
    if error:
        return error, None
    return tester.test(artifact_location=artifact_location)


def create_dependency_tester(
    runtime: str, snyk_org: snyk.client.Organization
) -> (str, dependency_tester.AbstractDependencyTester):
    error = None
    tester = None
    if runtime == "python":
        tester = dependency_tester.PythonDenpendencyTester(snyk_org=snyk_org)
    elif runtime == "nodejs":
        tester = dependency_tester.NodeJSDenpendencyTester(snyk_org=snyk_org)
    # TODO implement other available testers
    # as are specified on the pysnyk github page:
    # https://github.com/snyk-labs/pysnyk
    else:
        error = f"{ERROR_PREFIX} The runtime: {runtime} is not supported."
    return error, tester


def interpolate_function_runtime() -> (str, str):
    # TODO this function should interpolate what runtime the function uses
    # either by inspecting the files in the extracted zip file
    # or by queriying cloudstash for metadata about the artifact,
    # which seems to include the runtime under 'groupId'
    error = None
    runtime = "python"
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
    snyk_api_key = params["snyk_api_key"] if "snyk_api_key" in params else os.getenv("SNYK_API_KEY")
    # if api key is not set, return error
    if snyk_api_key is None:
        error = f"{ERROR_PREFIX} Could not find a Snyk API key, please set the 'SNYK_API_KEY' environment variable, or pass the API key as an argument: 'snyk_api_key':<api_key>."

    if "artifact_url" in params:
        artifact_url = params["artifact_url"]
    elif "artifact_id" in params:
        artifact_url = f"{CLOUDSTASH_HOSTNAME}/{CLOUDSTASH_DOWNLOAD_ENDPOINT}/{params['artifact_id']}"
    else:
        artifact_url = None
        error = f"{ERROR_PREFIX} No URL was provided for a CloudStash artifact, you must provide either a url as 'artifact_url':'<url>' or the CloudStash artifact ID as 'artifact_id':'<id>'"

    return error, snyk_api_key, artifact_url


if __name__ == "__main__":
    test_event = {}
    # test cases
    #  test_json_file = "test_artifact_url_with_api_key.json"
    #  test_json_file = "test_artifact_url.json"
    test_json_file = "test_artifact_id.json"
    with open(test_json_file) as test_json:
        test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    #  print(json.dumps(test_res))
    print(test_res)
    #  from pprint import pprint

    #  pprint(test_res)
