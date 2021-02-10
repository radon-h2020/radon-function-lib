import os
import subprocess
import json
from zipfile import ZipFile
from black import format_file_in_place, FileMode, WriteBack
from pathlib import Path

LOCAL_PATH = "/tmp/repo"


def handler(event, context):
    # retrieve body and email to verify risk factor
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event

    try:
        git_repo = params["git_repo"]



    except KeyError:
        return {
            "body": json.dumps({"message": "git_repo is not provided"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 401,
        }

    try:
        download_command = f"wget {git_repo}/archive/master.zip -P {LOCAL_PATH}"
        os.system(download_command)

        with ZipFile("/tmp/repo/master.zip", "r") as zipObj:
            zipObj.extractall("")

        lint_command = f"black {LOCAL_PATH} --diff"
        result = subprocess.check_output(lint_command, shell=True)
        return {
            "body": result,
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }
    except:
        return {
            "body": json.dumps({"message": "something went wrong"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 200,
        }
