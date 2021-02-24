#!/bin/bash

# exit script if anything fails
set -e

zip_file="snyk_test.zip"

echo "--> Creating .zip archive of function code ..."
zip -r "$zip_file" * -x \*.log -x test_artifacts/\* -x tests/\* -x __pycache__/\* -x upload_to_functionhub.sh

echo "--> checking that fuhub bin is available ..."
which fuhub

echo "--> Uploading function to cloudstash.io ..."
fuhub --token=$cloudstash_token upload "$zip_file"

echo "--> Removing .zip file"
rm "$zip_file"
