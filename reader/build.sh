#!/bin/bash

docker build --tag "${img:-openslides/openslides-datastore-reader:latest}" \
    --build-arg MODULE=reader --build-arg PORT=9010 \
    --pull "${OPTIONS[@]}" ..
