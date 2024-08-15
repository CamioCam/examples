# Check if the correct number of arguments are provided
if ($args.Length -ne 4) {
    Write-Host "Usage: $0 app_key app_id club_id camio_api_token"
    exit 1
}

# Assign command-line arguments to variables
$app_key = $args[0]
$app_id = $args[1]
$club_id = $args[2]
$camio_api_token = $args[3]

# Define the config.yaml file path
$config_file = "configs\production\abc_fitness_config.yaml"

# Create a backup of the original config.yaml file
Copy-Item -Path $config_file -Destination "$config_file.bak" -Force

# Use -replace operator to update the values in the YAML file
(Get-Content $config_file) -replace 'app_key:\s*".*"', "app_key: `"$app_key`"" `
                          -replace 'app_id:\s*".*"', "app_id: `"$app_id`"" `
                          -replace 'club_id:\s*".*"', "club_id: `"$club_id`"" `
                          -replace 'camio_api_token:\s*".*"', "camio_api_token: `"$camio_api_token`"" |
Out-File $config_file -Encoding utf8

Write-Host "abc_fitness_config.yaml has been updated."

# Run the docker compose
docker-compose -f abc-fitness-docker-compose.yaml up -d
