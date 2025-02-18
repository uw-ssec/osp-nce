#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$0")

# Run credentials.sh to set environment variables
source "$SCRIPT_DIR/credentials.sh"

# Get and navigate to project root
cd "$SCRIPT_DIR/.."
PROJECT_ROOT="$(pwd)"

# Build and run the services using Docker Compose
docker-compose build
docker-compose up