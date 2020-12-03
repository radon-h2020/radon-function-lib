# this python program was written using python 3.8.6
from pprint import pprint
import json
import sys
import check_tls_certs

#  from check_tls_certs import main as check_tls_cert

"""
This lambda function takes a domain name or a list of domain names
and returns an overview of the status of the SSL/TLS certificates served.
The function uses check_tls_cert by @fschulze - https://github.com/fschulze/check-tls-certs
This function was developed by @zanderhavgaard
"""

# prefix for error messages:
ERROR_PREFIX = "ERROR:"


def handler(event, context):
    if "body" in event:
        # the API gateway will wrap the request body, so we must parse it
        parameters = json.loads(event["body"])
    else:
        parameters = event

    # parse function parameters
    parse_error, domains = parse_parameters(params=parameters)
    if parse_error:
        return parse_error

    # use check_tls_certs to check the domains
    check_error, result = check_domains(domains=domains)
    if check_error:
        return check_error

    # format the check_tls_certs output to be JSON compatible
    format_error, formatted_result = format_result(result=result)
    if format_error:
        return format_error

    # set the response body
    body = formatted_result

    # build the response
    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def check_domains(domains: list) -> (str, list):
    error = None
    result = None

    # check_tls_certs metadata
    _file = None
    expiry_warn = 0
    verbosity = 2

    #  try:
    #  use check_tls_certs to check the certificates of the provided domain names
    #  result = check_tls_cert(file=_file, domain=domains, expiry_warn=expiry_warn, verbose=verbosity)
    result = check_tls_certs.main(file=_file, domain=domains, expiry_warn=expiry_warn, verbose=verbosity)
    #  except Exception:
    #  error = f"{ERROR_PREFIX} there was error checking the specified domain(s), please verify that the domain names are valid."

    return error, result


def format_result(result: list) -> (str, list):
    error = None
    formatted_result = []

    try:
        for domain, messages, expiration in result:
            # format each domains result tuple into a dictionary
            res = {"Domain": domain[0], "messages": [], "Certificate Expiry Date": str(expiration)}
            for message in messages:
                # format each message tuple into a string
                message_str = f"{message[0]}: {message[1]}"
                res["messages"].append(message_str)
            formatted_result.append(res)
    except Exception:
        error = f"{ERROR_PREFIX}: There was an error formatting the result."

    return error, formatted_result


def parse_parameters(params: dict) -> (str, str, str):
    # return an error string if any of the parameters are not parsed correctly, or missing
    error = None
    domains = []

    if "domain" in params:
        domains.append(params["domain"])

    if "domains" in params:
        for domain in params["domains"]:
            domains.append(domain)

    # if no domains are provided, return an error
    if not domains:
        error = f"{ERROR_PREFIX} you must at least one domain name with the 'domain' argument, or a list of domains using the 'domains' argument."

    return error, domains


# test the code locally
# will only be run if called from cli
if __name__ == "__main__":
    from pprint import pprint

    #  test_json_file = "tests/test_domain1.json"
    #  test_json_file = "tests/test_domain_expired.json"
    test_json_file = "tests/test_domains.json"

    with open(test_json_file) as test_json:
        test_event = json.load(test_json)

    test_context = {}

    test_res = handler(test_event, test_context)

    pprint(json.loads(test_res["body"]))
