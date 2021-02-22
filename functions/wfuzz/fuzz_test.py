import wfuzz
import json

def handler(event, context):
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event
    try:
        fuzz_url = f"{params['fuzz_url']}/FUZZ"
    except KeyError:
        return {
            "body": json.dumps({"message": "fuzz_url is not provided"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 401,
        }

    try:
        results = []
        for r in wfuzz.fuzz(url=fuzz_url, hc=[200], payloads=[("file",dict(fn="wordlist/general/common.txt"))]):
            results.append(r)

        return {
            "body": {"message": results},
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
    test_context = {}
    with open("tests/test.json") as test_json:
        test_event = json.load(test_json)
    test_res = handler(test_event, test_context)
    print(test_res)
