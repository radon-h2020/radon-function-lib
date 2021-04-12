import json
import os
from zipfile import ZipFile as zip_file

from pylint import epylint as lint
import requests

LOCAL_PATH = "/tmp"

def handler(event, context):
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event
    try:
        git_repo = params["git_repo"]
        git_branch = params["git_branch"] if "git_branch" in params else "master"
        main_file = params["python_main"]
    except KeyError:
        return {
            "body": json.dumps({"message": "git_repo is not provided"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 401,
        }
    result = ""
    try:
        result = requests.get(f"{git_repo}/archive/{git_branch}.zip")
        open(f"{LOCAL_PATH}/{git_branch}.zip",'wb').write(result.content)

        with zip_file(f"{LOCAL_PATH}/{git_branch}.zip", "r") as zip_obj:
            zip_obj.extractall(f"{LOCAL_PATH}")

        for root, dirs, files in os.walk(LOCAL_PATH):
            for file in files:
                if main_file in file:
                    (stdout, stderr) = lint.py_run(f"{root}/{file} -f json",return_std = True)
                    result = stdout if stdout else stderr

        return {
            "body": {"message": json.loads(result.getvalue())},
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }
    except Exception as e:
        message = e.message if hasattr(e,'message') else e
        return {
            "body": {"message": message},
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }

if __name__ == "__main__":
    test_event = {}
    # test cases
    #  test_json_file = "tests/test.json"
    test_json_file = "tests/test.json"
    with open(test_json_file) as test_json:
        test_event = json.load(test_json)
    test_context = {}
    test_res = handler(test_event, test_context)
    print(test_res)
