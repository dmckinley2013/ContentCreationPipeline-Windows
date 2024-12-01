#!/bin/bash

# Pull the required Docker images
docker pull rabbitmq:latest
docker pull python:3.10-slim

# Start the Docker Compose services
sudo docker-compose -f "docker-compose.yml" up -d --build

# Get the container ID of the setup-python service
container_id=$(docker-compose -f "docker-compose.yml" ps -q setup-python)

# Check if the container ID is retrieved, otherwise exit with an error
if [[ -z "$container_id" ]]; then
  echo "Error: Could not get the container ID of the setup-python service."
  exit 1
fi

# Monitor the setup-python container
while : ; do
  echo "Waiting for setup-python container to complete..."
  status=$(docker inspect --format '{{.State.Status}}' "$container_id")
  
  if [[ "$status" != "running" ]]; then
    echo "setup-python container has completed. Removing..."
    docker rm -f "$container_id"
    break
  fi
  
  sleep 5
done

# Check for GPU and run the appropriate profile
if command -v nvidia-smi &> /dev/null && nvidia-smi -L; then
  echo "GPU detected. Running GPU profile..."
  docker-compose --profile gpu up
else
  echo "No GPU detected. Running non-GPU profile..."
  docker-compose --profile non-gpu up
fi
