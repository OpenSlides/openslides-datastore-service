#!/bin/bash

set -e

mypy $(ls -d */ | grep -v "ci/")
