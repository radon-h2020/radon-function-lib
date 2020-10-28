#!/bin/bash

# exit script if anything fails
set -e

function msg {
    echo -e "\n==> $1\n"
}

# test functions
for fx in $(ls functions) ; do
    msg "Tesging $fx ..."
    for test_case in $(ls functions/$fx/tests) ; do
        msg "Testing: $fx: $test_case"
        sls invoke -f "$fx" -p "functions/$fx/tests/$test_case"
    done
done
