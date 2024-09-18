#!/bin/bash

export MESSAGE_BUS_HOST=${MESSAGE_BUS_HOST:-redis}
export MESSAGE_BUS_PORT=${MESSAGE_BUS_PORT:-6379}

if [[ $MESSAGE_BUS_HOST && $MESSAGE_BUS_PORT ]]; then
    while ! nc -z "$MESSAGE_BUS_HOST" "$MESSAGE_BUS_PORT"; do
        echo "waiting for $MESSAGE_BUS_HOST:$MESSAGE_BUS_PORT"
        sleep 1
    done

    echo "$MESSAGE_BUS_HOST:$MESSAGE_BUS_PORT is available"
fi
