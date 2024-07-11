#!/bin/bash

test_dirs=("regression_test")
fail=0

for dir in "${test_dirs[@]}"; do
    echo "Running tests in ${dir}"
    cd "${dir}" || exit
    ./run_tests.sh
    result=$?
    if [ $result -ne 0 ]; then
        echo "Tests failed in ${dir}"
        fail=1
    fi
    cd ..
done

if [ $fail -ne 0 ]; then
    echo "Some tests failed."
    exit 1
else
    echo "All tests passed."
fi

