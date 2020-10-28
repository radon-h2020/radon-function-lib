# Radon Function Library

TODO write

# Functions

## snyk_test

This functions uses the snyk api to test the dependencies of function artifacts stored on cloudstash.io for vulnerabilities.
The function accepts the following arguments:
- `artifact_id` cloudstash.io id of artifact to test.
- `artifact_url` URL to download .zip from cloudstash.io containing artifact to test.
    - you must specify one of `artifact_id` or `artifact_url` !

- `snyk_api_key` (optional) - in order to use snyk, you must have a API key from a service account, and either pass it as an argument using the `snyk_api_key` key, or save it as an environment variable in the lambda function called `SNYK_API_KEY`.
- `output_format` (optional) - the formatting of the returned JSON, must be one of `full`, `human`. Defaults to `full`.

The function will return a list of vulnerabilities if any are found, or string indicating that no vulnerabilities were found.

Currently `python` and `node` runtimes are supported. In order to test a function artifact, it's corresponding dependecy configuration file must be included in the root of the artifact .zip file. valid filename are:
- `requirements.txt` - for the `python` runtime.
- `package.json` - for the `node` runtime.

### Testing snyk_test function

There are a number of function artifacts located in `functions/snyk_test/test_artifacts`, that can be used to test function.
Each test case is expressed in a .json file in `functions/snyk_test/tests` and can be tested by running `sls invoke -f snyk_test -p functions/snyk_test/tests/<test file>`.
The script `test.sh` automates this.
