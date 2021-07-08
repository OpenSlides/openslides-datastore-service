#!/bin/bash

dirs=$(ls -d */ | grep -v "ci/")

./execute-cleanup.sh "$dirs"
