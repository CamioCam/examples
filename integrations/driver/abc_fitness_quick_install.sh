#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 4 ]; then
  echo "Usage: $0 app_key app_id club_id camio_api_token"
  exit 1
fi

# Assign command-line arguments to variables
app_key=$1
app_id=$2
club_id=$3
camio_api_token=$4

# Define the config.yaml file path
config_file="configs/production/abc_fitness_config.yaml"

# Create a backup of the original config.yaml file
cp "$config_file" "${config_file}.bak"

# Use sed to replace the values after the keys with actual values, properly escaping quotes
sed -i '' -e "s/\(app_key:\s*\).*/\1 \"$app_key\"/" \
          -e "s/\(app_id:\s*\).*/\1 \"$app_id\"/" \
          -e "s/\(club_id:\s*\).*/\1 \"$club_id\"/" \
          -e "s/\(camio_api_token:\s*\).*/\1 \"$camio_api_token\"/" "$config_file"

echo "abc_fitness_config.yaml has been updated."

# Build the image
docker build -t camio-integration-driver-abc-fitness:latest --no-cache -f abc-fitnessDockerfile .

# Run the docker compose
docker compose -f abc-fitness-docker-compose.yaml up -d