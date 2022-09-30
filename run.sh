#!/bin/bash

docker build -f Dockerfile -t docker-test-technique .
docker run -p 8050:8050 -v "$(pwd)"/app:/app --rm docker-test-technique
