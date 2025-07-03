#!/bin/sh

if [ "$APP_CONTEXT" = "dev"   ]; then exec python -m flask run -h 0.0.0.0 -p "$PORT"; fi
if [ "$APP_CONTEXT" = "tests" ]; then sleep inf; fi
if [ "$APP_CONTEXT" = "debug" ]; then exec python -m debugpy --listen 0.0.0.0:5678 -m flask run -h 0.0.0.0 -p "$PORT" --no-reload; fi
if [ "$APP_CONTEXT" = "prod"  ]; then exec gunicorn -w "$NUM_WORKERS" -b 0.0.0.0:"$PORT" datastore."$MODULE".app:application -t "$WORKER_TIMEOUT"; fi