#!/bin/bash

# executes all lines of travis.sh and gathers the error codes.
# Fails if at least one command failed

printf "\n\n\n\n\n\n\n ------------- COMMANDS -------------- \n"

result=0
while read p; do
    eval "$p"
    error=$?
    if (( error > result )); then
        result=$error
    fi
done < travis.sh
exit $result

printf "\n\n\n\n\n\n\n"
