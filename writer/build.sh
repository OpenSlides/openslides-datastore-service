#!/bin/bash

docker build --tag "${img:-openslides/openslides-datastore-writer:latest}" \
    --build-arg MODULE=writer --build-arg PORT=9011 \
    --pull "${OPTIONS[@]}" ..
