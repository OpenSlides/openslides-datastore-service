#!/bin/bash

set -e

dirs=$(ls -d */)
pytest_target=${1:-test}

if [[ $pytest_target == "test" ]]; then
    pytest --cov --cov-report term-missing
else
    pytest $pytest_target
fi
