import os
import schemathesis
from hypothesis import settings, Verbosity


### ENV
#Path to OpenAPI config, either json or yaml
API_PATH = os.getenv("API_URL")
BASE_URL = os.getenv("BASE_URL")

def handler(event,context):
    import pytest
    return pytest.main(['-o', 'cache_dir=/tmp/.testcache'])

# will only be run if called from cli
if __name__ == "__main__":
    test_event = {'openapi_uri':'tests/openapi_example.yaml', 'base_url':'https://cloudstash.io'}
    test_context = {'env':{}}
    test_res = handler(test_event, test_context)
    print(test_res)

schema = schemathesis.from_uri(API_PATH)
@schema.parametrize()
@settings(deadline=2000,print_blob=True, max_examples=10, verbosity=Verbosity.verbose)
def test_api(case):
    response = case.call_and_validate()
    return response