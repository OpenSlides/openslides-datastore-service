#!/bin/bash

if [ -n "$MESSAGE_BUS_HOST" ]; then
    export MESSAGE_BUS_PORT=${MESSAGE_BUS_PORT:-6379}
    wait-for-it --timeout=15 "$MESSAGE_BUS_HOST:$MESSAGE_BUS_PORT"
fi
