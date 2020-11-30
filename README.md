# Radon Function Library

This repository contains a number of serverless functions relating to log, state, cloud & security.

# Deploying Functions

The project comes with a `serverless framework` project to deploy the functions.

Deploying the functions will require `npm` and `python/pip` to be installed.

First clone this repository, then use `npm` to install `serverless` and it's dependencies:
```sh
npm install
```

Then use the `serverless` cli tool to deploy the stack:
```sh
serverless deploy
```

For convenience serverless provides the alias `sls` for the `serverless` command.

You can use the `info` command to get an overview of existing resources:
```sh
sls info
```

# Adding New Functions

New functions added to the project should be placed in a directory in the `functions` directory.
Each directory in `functions` should contain all of the code, and dependency specification, i.e. `requirements.txt` or `package.json`, for that function.

The function should be added to the `serverless.yml` in order to easily deploy the function and verify that it works.

Add a new key to `functions` yaml dictionary:
```yaml
functions:
  ...
  <function_name>:
    handler: <function_name>.handler
    module: functions/<function_name>
  ...
```

Then use `serverless deploy` to deploy the new function.

Note that the deployment uses an AWS API gateway, which has a specific way of providing JSON arguments, and requirements for how responses should be structured.
You might want to look at how the existing functions handle this, in order to now experience API Gateway related problems.

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

Currently `python` and `node` runtimes are supported. In order to test a function artifact, it's corresponding dependecy configuration file must be included in the root of the artifact .zip file.
Valid filename are:
- `requirements.txt` - for the `python` runtime.
- `package.json` - for the `node` runtime.

### Testing snyk_test function

There are a number of function artifacts located in `functions/snyk_test/test_artifacts`, that can be used to test function.
Each test case is expressed in a .json file in `functions/snyk_test/tests` and can be tested by running `sls invoke -f snyk_test -p functions/snyk_test/tests/<test file>`.
The script `test.sh` automates this.

### Adding support for more runtimes

Support for more runtimes can be added by using the appropriate methods of the [pysnyk](https://github.com/snyk-labs/pysnyk#testing-for-vulnerabilities) pip package to test the runtime's dependency file.
The method `test_depdencies_for_vulnerabilities` in the file `functions/snyk_test/snyk_test.py`, contains a functional implementation that can be extended with support for new runtimes.

## secrets_scanner

This function scans cloudstash.io function artifacts for tokens/keys/credentails/passwords/etc.
The scanning is provided by `DumpsterDiver` (https://github.com/securing/DumpsterDiver).

The function accepts the following arguments:
- `artifact_id` cloudstash.io id of artifact to test.
- `artifact_url` URL to download .zip from cloudstash.io containing artifact to test.
    - you must specify one of `artifact_id` or `artifact_url` !

The function will return a list of found items (strings) that have a high entropy, or a string indicating that nothing suspicious was found.

### Testing secrets_scanner function

There are a number of function artifacts located in `functions/secrets_scanner/test_artifacts`, that can be used to test function.
Each test case is expressed in a .json file in `functions/secrets_scanner/tests` and can be tested by running `sls invoke -f snyk_test -p functions/secrets_scanner/tests/<test file>`.
The script `test.sh` automates this.
