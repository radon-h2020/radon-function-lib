#  MIT License

#  Copyright (c) 2018 Epsagon

#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:

#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.

#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

# list_lambas by Epsagon, modified by zanderhavgaard
# https://github.com/epsagon/list-lambdas

#  Enumerates Lambda functions from every region with interesting metadata

from __future__ import print_function
from datetime import datetime
import argparse
import codecs
import boto3
from boto3.session import Session
from botocore.exceptions import ClientError

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
BYTE_TO_MB = 1024.0 * 1024.0

ALL_TABLE_HEADERS = [
    "Region",
    "Function",
    "Memory (MB)",
    "Code Size (MB)",
    "Timeout (seconds)",
    "Runtime",
    "Description",
    "Last Modified",
    "Last Invocation",
]

SORT_KEYS = ["region", "last-modified", "last-invocation", "runtime"]


def list_available_lambda_regions():
    """
    Enumerates list of all Lambda regions
    :return: list of regions
    """
    session = Session()
    regions = session.get_available_regions("lambda")
    # for some reason stockholm is not returned by the above call
    if "eu-north-1" not in regions:
        regions.append("eu-north-1")
    return regions


def init_boto_client(client_name, region, args):
    """
    Initiates boto's client object
    :param client_name: client name
    :param region: region name
    :param args: arguments
    :return: Client
    """
    #  if args.token_key_id and args.token_secret:
    #  boto_client = boto3.client(
    #  client_name,
    #  aws_access_key_id=args.token_key_id,
    #  aws_secret_access_key=args.token_secret,
    #  region_name=region,
    #  )
    #  elif args.profile:
    #  session = boto3.session.Session(profile_name=args.profile)
    #  boto_client = session.client(client_name, region_name=region)
    #  else:
    #  boto_client = boto3.client(client_name, region_name=region)

    # TODO fix
    boto_client = boto3.client(
        client_name,
        aws_access_key_id=args.token_key_id,
        aws_secret_access_key=args.token_secret,
        region_name=region,
    )

    return boto_client


def get_days_ago(datetime_obj):
    """
    Converts a datetime object to "time ago" string
    :param datetime_obj: Datetime
    :return: "time ago" string
    """
    days_ago = (datetime.now() - datetime_obj).days
    datetime_str = "Today"
    if days_ago == 1:
        datetime_str = "Yesterday"
    elif days_ago > 1:
        datetime_str = "{0} days ago".format(days_ago)

    return datetime_str


def get_last_invocation(region, args, function_name):
    """
    Return last invocation timestamp (epoch) or -1 if not found.
    -1 can be returned if no log group exists for Lambda,
    or if there are no streams in the log.
    :param region: function region
    :param args: arguments
    :param function_name: function name
    :return: last invocation or -1
    """
    logs_client = init_boto_client("logs", region, args)
    last_invocation = -1

    try:
        logs = logs_client.describe_log_streams(
            logGroupName="/aws/lambda/{0}".format(function_name), orderBy="LastEventTime", descending=True
        )
    except ClientError as _:
        return last_invocation

    log_streams_timestamp = [log.get("lastEventTimestamp", 0) for log in logs["logStreams"]]

    if log_streams_timestamp:
        last_invocation = max(log_streams_timestamp)

    return last_invocation


def format_lambda_data(lambdas_data, args):
    formatted_data = []
    for lambda_data in lambdas_data:
        function_data = lambda_data["function-data"]
        last_invocation = "N/A (no invocations?)"
        if lambda_data["last-invocation"] != -1:
            last_invocation = get_days_ago(datetime.fromtimestamp(lambda_data["last-invocation"] / 1000))
        formatted_data.append(
            {
                "region": lambda_data["region"],
                "function_name": str(function_data["FunctionName"]),
                "function_memory": str(function_data["MemorySize"]),
                "function_size": "%.2f" % (function_data["CodeSize"] / BYTE_TO_MB),
                "function_timeout": str(function_data["Timeout"]),
                "runtime": str(function_data["Runtime"]),
                "function_description": function_data["Description"],
                "last_invocation": get_days_ago(lambda_data["last-modified"]),
                "num_invocations": last_invocation,
            }
        )

    return formatted_data


def print_lambda_list(args):
    """
    Main function
    :return: None
    """
    regions = list_available_lambda_regions()

    lambdas_data = []
    for region in regions:
        lambda_client = init_boto_client("lambda", region, args)
        next_marker = None
        response = lambda_client.list_functions()
        while next_marker != "":
            next_marker = ""
            functions = response["Functions"]
            if not functions:
                continue

            for function_data in functions:
                # Extract last modified time
                last_modified = datetime.strptime(function_data["LastModified"].split(".")[0], DATETIME_FORMAT)

                # Extract last invocation time from logs
                last_invocation = get_last_invocation(region, args, function_data["FunctionName"])

                if last_invocation != -1:
                    inactive_days = (datetime.now() - datetime.fromtimestamp(last_invocation / 1000)).days
                    if args.inactive_days_filter > inactive_days:
                        continue

                lambdas_data.append(
                    {
                        "region": region,
                        "function-data": function_data,
                        "last-modified": last_modified,
                        "last-invocation": last_invocation,
                        "runtime": function_data["Runtime"],
                    }
                )

            # Verify if there is next marker
            if "NextMarker" in response:
                next_marker = response["NextMarker"]
                response = lambda_client.list_functions(Marker=next_marker)

    # Sort data by the given key (default: by region)
    lambdas_data.sort(key=lambda x: x[args.sort_by])

    #  min_table_data, all_table_data = create_tables(lambdas_data, args)
    formatted_lambda_data = format_lambda_data(lambdas_data, args)

    return formatted_lambda_data
