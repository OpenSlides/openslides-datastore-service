#!/bin/bash

# executes all lines of ci.sh and gathers the error codes.
# Fails if at least one command failed

printf "\n\n\n\n\n\n\n ------------- COMMANDS -------------- \n"

result=0
while read p; do
    eval "$p"
    error=$?
    if (( error > result )); then
        result=$error
    fi
done < ci.sh
exit $result

printf "\n\n\n\n\n\n\n"
