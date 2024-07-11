#!/bin/bash

# remove old log files (success_test_*.log and fail_test_.log) in tests/test_files
rm -f tests/test_files/success_test_*.log
rm -f tests/test_files/fail_test_*.log

python -m unittest discover -s tests
