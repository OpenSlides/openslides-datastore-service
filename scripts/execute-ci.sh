#!/bin/bash

printf "\n\n\n ------------- COMMANDS -------------- \n"

result=0
readarray -d '' ci_files < <(printf '%s\0' ci/*.sh | sort -zV)
for i in "${ci_files[@]}"; do
    [ -f "$i" ] || break
    echo "-> $i"
    bash -c "$i $1"
    error=$?
    if (( error > 0 )); then
        echo "Got a non-zero status code!"
    fi
    if (( error > result )); then
        result=$error
    fi
done

exit $result
