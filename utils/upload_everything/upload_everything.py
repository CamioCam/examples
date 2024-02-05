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


Excecute with:
python upload_everything.py --cameras_filename your_cameras_filename.csv --time_range_filename your_time_range_filename.csv --token your_access_token

See help with:
python upload_everything.py --help

cameras_filename is a csv with a header row and three required columns like this,
where the rows without is_requested value TRUE are skipped:

user_email,camera,is_requested
sanmateo@camiolog.com,Front Entrance,TRUE
sanmateo@camiolog.com,Back Exit,TRUE


time_range_filename is a csv with a header row and two required columns like this,
where each time range should span less than 800 Events (for reference, the max number
of Events/hour/camera is typically 180):

start_time,end_time
7pm PT January 31,7:30pm PT January 31st
7:30pm PT January 31,8:00pm PT January 31st

You can obtain your_access_token from:
https://camio.com/settings/integrations/#api

The stdout is a CSV with four columns like this example, where the search_url can be used to view the results the requested
uploads are completed:

python upload_everything.py --cameras_filename cameras.csv --time_range_filename time-ranges.csv --token YOURTOKEN | tee output.csv

api_request_url,status,upload_commands_count,uploading_devices,search_url
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+East+7pm+PT+January+31st+to+8pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+East+7pm+PT+January+31st+to+8pm+PT+January+31st+all
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+East+8pm+PT+January+31st+to+9pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+East+8pm+PT+January+31st+to+9pm+PT+January+31st+all
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+West+7pm+PT+January+31st+to+8pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+West+7pm+PT+January+31st+to+8pm+PT+January+31st+all
https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+West+8pm+PT+January+31st+to+9pm+PT+January+31st+all+tag%3Abox,200,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+West+8pm+PT+January+31st+to+9pm+PT+January+31st+all


Only the tag:box upload request query text is shown when using the --dry_run argument like this:

python upload_everything.py --cameras_filename cameras.csv --time_range_filename time-ranges.csv --token YOURTOKEN --dry_run
api_request_url,status,upload_commands_count,uploading_devices,search_url
sanmateo@camiolog.com Front East 7pm PT January 31st to 8pm PT January 31st all tag:box,N/A,0,N/A
sanmateo@camiolog.com Front East 8pm PT January 31st to 9pm PT January 31st all tag:box,N/A,0,N/A
sanmateo@camiolog.com Front West 7pm PT January 31st to 8pm PT January 31st all tag:box,N/A,0,N/A
sanmateo@camiolog.com Front West 8pm PT January 31st to 9pm PT January 31st all tag:box,N/A,0,N/A

"""

import requests
import csv
import sys
import argparse
import time

def make_api_request(concatenated_string, token, hostname):
    base_url = f"https://{hostname}/api/search"
    headers = {'Authorization': f'token {token}'}
    params = {'text': concatenated_string}
    response = requests.get(base_url, params=params, headers=headers)
    return response

def process_files(cameras_filename, time_range_filename, token, wait_seconds, hostname, dry_run=False):
    time_ranges = []
    with open(time_range_filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            start_time = row.get('start_time', '')
            end_time = row.get('end_time', '')
            if start_time and end_time:
                time_ranges.append((start_time, end_time))
    row_count = 0
    row_count_skipped = 0
    print(f"api_request_url,status,upload_commands_count,uploading_devices,search_url")    # header row
    with open(cameras_filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            user = row.get('user_email', '')
            camera_name = row.get('camera', '')
            is_requested = row.get('is_requested', '')
            if user and camera_name and is_requested == 'TRUE':
                row_count += 1
                for time_range in time_ranges:
                    start_time = time_range[0]
                    end_time = time_range[1]
                    concatenated_string = f"{user} {camera_name} {start_time} to {end_time} all tag:box"
                    if not dry_run:
                        response = make_api_request(concatenated_string, token, hostname)
                        search_url = response.url.replace("/api/search?text=", "/app/#search;q=").replace("+tag%3Abox", "")
                        upload_commands_count = 0
                        uploading_devices = ''
                        if response.status_code // 100 == 2:  # in the 2xx range
                            response_data = response.json()
                            if 'operations' in response_data and 'upload_commands' in response_data['operations'] and isinstance(response_data['operations']['upload_commands'], list):
                                upload_commands = response_data['operations']['upload_commands']
                                upload_commands_count = len(upload_commands)
                                uploading_devices = ' '.join(upload_command["device_id_internal"] for upload_command in upload_commands)
                            time.sleep(wait_seconds)
                        print(f"{response.url},{response.status_code},{upload_commands_count},{uploading_devices},{search_url}")
                    else:
                        print(f"{concatenated_string},N/A,0,N/A")
                    sys.stdout.flush()  # just so we see stdout even if redirected to file with tee or >.
            else:
                row_count_skipped += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Request upload of all video events regardless of motion from a list of cameras and a list of time ranges.')
    parser.add_argument('--cameras_filename', required=True, help='Path to the cameras filename with CSV user_email,camera,is_requested.')
    parser.add_argument('--time_range_filename', required=True, help='Path to the time range filename with CSV start_time,end_time.')
    parser.add_argument('--token', required=True, help='Access token for API (obtain from https://camio.com/settings/integrations/#api).')
    parser.add_argument('--wait_seconds', required=False, default=60, help='Wait time between each request in seconds (default 60).')
    parser.add_argument('--hostname', required=False, default='camio.com', help='The hostname of the API endpoint (default is camio.com).')
    parser.add_argument('--dry_run', action='store_true', help='Perform a dry run (skip actual API requests).')

    args = parser.parse_args()

    process_files(args.cameras_filename, args.time_range_filename, args.token, int(args.wait_seconds), args.hostname, args.dry_run)

