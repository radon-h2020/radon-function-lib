import wfuzz
import json

def handler(event, context):
    if "body" in event and event["body"]:
        params = json.loads(event["body"])
    else:
        params = event
    try:
        fuzz_url = f"{params['wfuzz_url']}/FUZZ"
        print(fuzz_url)
    except KeyError:
        return {
            "body": json.dumps({"message": "wfuzz_url is not provided"}),
            "headers": {"Content-Type": "application/json"},
            "statusCode": 401,
        }
    try:
        results = {}
        for r in wfuzz.fuzz(url=fuzz_url, hc=[200], payloads=[("file",dict(fn="tests/payload.txt"))]):
            if r.code == 200 or r.code == 301:
                results[r.description] = [r.url,r.code]

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
