#!/bin/bash

set -xe

black --target-version py310 $(ls -d */)
isort --diff $(ls -d */)
flake8 $(ls -d */)
mypy $(ls -d */ | grep -v "ci/")