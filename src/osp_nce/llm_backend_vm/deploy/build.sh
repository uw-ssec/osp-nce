#!/bin/bash

# Check if the .env file exists; if not, prompt for the HF token and create it
if [ ! -f ".env" ]; then
  echo ".env file not found."
  echo -n "Please enter your Hugging Face token: "
  read -r HF_TOKEN
  echo "HF_TOKEN=${HF_TOKEN}" > .env
  echo ".env file created with the provided token."
fi

# Build the Docker images
docker compose build

# Run the Docker containers
docker compose up
