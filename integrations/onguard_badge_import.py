"""
Copyright 2024 Camiolog, Inc.

This code is licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This script imports OnGuard badge information into the Camio system in order to enable tailgating notifications, as well
as search and alert on specific user badge-ins.

Execute with:
python integrations/onguard_badge_import.py CAMIO_BEARER_TOKEN PATH_TO_BADGE_FILE

You can obtain a Camio bearer token from the Camio OnGuard Integration settings page: https://camio.com/settings/integrations/onguard.

The badge file must be a CSV with the following columns: badge_id, email. The file must contain all of the desired badges.
Any previously imported badges will be overwritten each time this script is run.

Instructions on performing the badge import via the settings page UI can be found here: https://help.camio.com/hc/en-us/articles/360055730712-Camio-User-Guide-for-OnGuard-Tailgating-detection-and-real-time-video-search#h_01GHHRMKDMGSFKH8SFY5W1B94F.
"""

import sys
import requests
import logging
import os


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    # Ensure the script receives the token and file path as command-line arguments
    if len(sys.argv) != 3:
        logger.error("Usage: python onguard_badge_import.py <Camio_Bearer_Token> <Badge_File_Path>")
        sys.exit(1)

    # Extract the token and file path from the command-line arguments
    token = sys.argv[1]
    file_path = sys.argv[2]

    # Verify that the file is a CSV
    if not file_path.lower().endswith('.csv'):
        logger.error("The file must be a CSV.")
        sys.exit(1)

    # Ensure the file exists
    if not os.path.isfile(file_path):
        logger.error("The specified file does not exist.")
        sys.exit(1)

    # Define headers for API requests
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        # Step 1: Get the user's email from the /api/user endpoint
        user_url = "https://camio.com/api/user"
        user_response = requests.get(user_url, headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            user_email = user_data['email']
            logger.debug(f"Retrieved user email: {user_email}")
        else:
            logger.error(
                f"Failed to fetch user information with status code {user_response.status_code}: {user_response.text}")
            sys.exit(1)

        # Step 2: Make the initial POST request to get upload and callback URLs
        badges_url = f"https://camio.com/api/integrations/onguard/badges/import?user={user_email}"
        badges_response = requests.post(badges_url, headers={"Content-Type": "application/octet-stream", **headers})

        if badges_response.status_code == 200:
            badges_data = badges_response.json()
            upload_url = badges_data['upload']['url']
            upload_method = badges_data['upload']['method']
            callback_url = badges_data['callback']['url']
            callback_method = badges_data['callback']['method']

            logger.debug(f"Upload URL: {upload_url}")
            logger.debug(f"Callback URL: {callback_url}")

            # Step 3: Upload the file using the specified method and URL
            with open(file_path, 'rb') as file:
                upload_headers = {"Content-Type": badges_data['upload']['content_type']}
                upload_response = requests.request(upload_method, upload_url, headers=upload_headers, data=file)

            if upload_response.status_code == 200:
                logger.info(f"File {file_path} uploaded successfully.")

                # Step 4: Trigger the callback
                callback_headers = {"Authorization": f"Bearer {token}"}
                callback_response = requests.request(callback_method, callback_url, headers=callback_headers)

                if callback_response.status_code == 200:
                    logger.info(f"Successfully requested badge import, an email will be sent to {user_email} upon "
                                f"completion.")
                else:
                    logger.error(
                        f"Callback failed with status code {callback_response.status_code}: {callback_response.text}")
            else:
                logger.error(
                    f"File upload failed with status code {upload_response.status_code}: {upload_response.text}")
        else:
            logger.error(
                f"Initial request failed with status code {badges_response.status_code}: {badges_response.text}")

    except requests.exceptions.RequestException as e:
        logger.exception("An error occurred:")


if __name__ == "__main__":
    main()
