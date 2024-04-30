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


Execute with:
python upload_everything.py --cameras_filename your_cameras_filename.csv --time_range_filename your_time_range_filename.csv --token your_access_token --device_ids camio_box_device_id_1 camio_box_device_id_1

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

The stdout is a CSV with five columns like this example, where the search_url can be used to view the results the requested
uploads are completed:

python upload_everything.py --cameras_filename cameras.csv --time_range_filename time-ranges.csv --token YOURTOKEN --device_ids camio_box_device_id_1 camio_box_device_id_1 --max_wait_time 600 | tee output.csv

timestamp,api_request_url,status,upload_commands_count,uploading_devices,search_url
2024-02-05T14:56:39.197221,https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+East+7pm+PT+January+31st+to+8pm+PT+January+31st+all+tag%3Abox,200,2,0,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+East+7pm+PT+January+31st+to+8pm+PT+January+31st+all
2024-02-05T14:56:40.197221,https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+East+8pm+PT+January+31st+to+9pm+PT+January+31st+all+tag%3Abox,200,2,1,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+East+8pm+PT+January+31st+to+9pm+PT+January+31st+all
2024-02-05T14:56:41.197221,https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+West+7pm+PT+January+31st+to+8pm+PT+January+31st+all+tag%3Abox,200,2,2,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+West+7pm+PT+January+31st+to+8pm+PT+January+31st+all
2024-02-05T14:56:42.197221,https://camio.com/api/search?text=sanmateo%40camiolog.com+Front+West+8pm+PT+January+31st+to+9pm+PT+January+31st+all+tag%3Abox,200,2,3,gd:00vx12273wf6fvd:000C29EF1F22 gd:00vx12273wf6fvd:B0416F040AF6,https://camio.com/app/#search;q=sanmateo%40camiolog.com+Front+West+8pm+PT+January+31st+to+9pm+PT+January+31st+all

Only the tag:box upload request query text is shown when using the --dry_run argument like this:

python upload_everything.py --cameras_filename cameras.csv --time_range_filename time-ranges.csv --token YOURTOKEN --dry_run
timestamp,api_request_url,status,upload_commands_count,uploading_devices,search_url
2024-02-05T14:59:09.749413,sanmateo@camiolog.com Front East 7pm PT January 31st to 8pm PT January 31st all tag:box,N/A,0,N/A
2024-02-05T14:59:09.749448,sanmateo@camiolog.com Front East 8pm PT January 31st to 9pm PT January 31st all tag:box,N/A,0,N/A
2024-02-05T14:59:09.749481,sanmateo@camiolog.com Front West 7pm PT January 31st to 8pm PT January 31st all tag:box,N/A,0,N/A
2024-02-05T14:59:09.749490,sanmateo@camiolog.com Front West 8pm PT January 31st to 9pm PT January 31st all tag:box,N/A,0,N/A
"""
import requests
import csv
import sys
import argparse
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


def make_api_request(concatenated_string, token, hostname):
    base_url = f"https://{hostname}/api/search"
    headers = {'Authorization': f'token {token}'}
    params = {'text': concatenated_string}
    response = requests.get(base_url, params=params, headers=headers)
    return response


def get_upload_queue_lengths(user, token, hostname, device_ids_to_check, dry_run=False) -> list:
    """
    Requests /api/devices and extracts the upload_queue_length for specified device_ids_to_check. If dry_run or no
    device_ids_to_check, returns an empty list. If the specified device ids are not found in the devices payload, returns
    an empty list.

    Ex: [0, 100, 20]
    """
    if dry_run or not device_ids_to_check:
        return []

    devices_url = f"https://{hostname}/api/devices"
    headers = {'Authorization': f'token {token}'}
    params = {'user': user}
    device_response = requests.get(devices_url, params=params, headers=headers)
    queue_lengths = []

    if device_response.status_code == 200:
        devices_data = device_response.json()
        for device in devices_data:
            if device['device_id'] and device['device_id'].strip() in device_ids_to_check and device['state'] and \
                    device['state']['queue_stats']:
                queue_lengths.append(device['state']['queue_stats']['upload_queue_length'])
    else:
        sys.stderr.write(f"Error retrieving device info: {device_response.status_code} ({device_response.reason})\n")

    return queue_lengths


def process_user(user, cameras, time_ranges, token, wait_seconds, max_wait_time, hostname, device_ids_to_check,
                 upload_queue_threshold, dry_run=False):
    # Proceeding with the search API request
    for camera_name in cameras:
        for time_range in time_ranges:
            iteration_start_time = datetime.now()

            while True:
                start_time, end_time = time_range
                concatenated_string = f"{user} {camera_name} {start_time} to {end_time} all tag:box"
                call_time = datetime.now()

                # Get the queue lengths for the specified boxes, will be [] if none specified
                queue_lengths = get_upload_queue_lengths(user=user, token=token, hostname=hostname,
                                                         device_ids_to_check=device_ids_to_check, dry_run=dry_run)
                queue_lengths_string = ' '.join(str(length) for length in queue_lengths)
                queue_is_full = not all(value < upload_queue_threshold for value in queue_lengths)

                # Don't request tag:box upload for dry runs or if the queue is filling up
                if not dry_run and not queue_is_full:
                    response = make_api_request(concatenated_string, token, hostname)
                    search_url = response.url.replace("/api/search?text=", "/app/#search;q=").replace("+tag%3Abox", "")
                    upload_commands_count = 0
                    uploading_devices = ''
                    is_working = False
                    if response.status_code // 100 == 2:  # in the 2xx range
                        response_data = response.json()
                        if 'operations' in response_data and 'upload_commands' in response_data[
                            'operations'] and isinstance(response_data['operations']['upload_commands'], list):
                            upload_commands = response_data['operations']['upload_commands']
                            upload_commands_count = len(upload_commands)
                            uploading_devices = ' '.join(
                                upload_command["device_id_internal"] for upload_command in upload_commands)
                            is_working = True
                    else:
                        sys.stderr.write(f"Error making upload request: {response.status_code} ({response.reason})\n")

                    print(
                        f"{call_time.isoformat()},{response.url},{response.status_code},{upload_commands_count},{queue_lengths_string},{uploading_devices},{search_url}")
                    sys.stdout.flush()
                    if is_working:
                        time.sleep(wait_seconds)
                    break

                elif not dry_run and queue_is_full:
                    # One or more of the queues is full
                    current_time = datetime.now()
                    elapsed_time = current_time - iteration_start_time
                    elapsed_total_seconds = elapsed_time.total_seconds()

                    # Break iteration if reached max wait time
                    if elapsed_total_seconds > max_wait_time:
                        sys.stderr.write(f"Waited for max {max_wait_time}s for user {user}, camera {camera_name}\n")
                        print(
                            f"{call_time.isoformat()},{concatenated_string},N/A,N/A,{queue_lengths_string},N/A,N/A")
                        sys.stdout.flush()
                        break

                    # Sleep to give queues time to drain
                    else:
                        sys.stderr.write(f"Queue is full, sleeping for {wait_seconds}s. Queue lengths: {queue_lengths}\n")
                        time.sleep(wait_seconds)

                else:
                    print(f"{call_time.isoformat()},{concatenated_string},N/A,0,{queue_lengths_string},N/A")
                    sys.stdout.flush()
                    break


def process_files(cameras_filename, time_range_filename, token, wait_seconds, max_wait_time, hostname,
                  device_ids_to_check, upload_queue_threshold, dry_run=False):
    time_ranges = []
    with open(time_range_filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            start_time = row.get('start_time', '')
            end_time = row.get('end_time', '')
            if start_time and end_time:
                time_ranges.append((start_time, end_time))

    users_cameras = {}
    with open(cameras_filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            user = row.get('user_email', '')
            camera_name = row.get('camera', '')
            is_requested = row.get('is_requested', '')
            if user and camera_name and is_requested == 'TRUE':
                if user not in users_cameras:
                    users_cameras[user] = []
                users_cameras[user].append(camera_name)

    row_count = 0
    print(
        f"timestamp,api_request_url,status,upload_commands_count,upload_queue_lengths,uploading_devices,search_url")  # header row

    with ThreadPoolExecutor() as executor:  # Python version 3.8: Default value of max_workers is changed to min(32, os.cpu_count() + 4)
        for user, cameras in users_cameras.items():
            row_count += len(cameras)
            executor.submit(process_user, user, cameras, time_ranges, token, wait_seconds, max_wait_time, hostname,
                            device_ids_to_check, upload_queue_threshold, dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Request upload of all video events regardless of motion from a list of cameras and a list of time ranges.')
    parser.add_argument('--cameras_filename', required=True,
                        help='Path to the cameras filename with CSV user_email,camera,is_requested.')
    parser.add_argument('--time_range_filename', required=True,
                        help='Path to the time range filename with CSV start_time,end_time.')
    parser.add_argument('--token', required=True,
                        help='Access token for API (obtain from https://camio.com/settings/integrations/#api).')
    parser.add_argument('--wait_seconds', required=False, default=500,
                        help='Wait time between each request in seconds (default 500 for 1 hour of 89-stream 1775R).')
    parser.add_argument('--hostname', required=False, default='camio.com',
                        help='The hostname of the API endpoint (default is camio.com).')
    parser.add_argument('--device_ids', nargs='+', required=False, default=[],
                        help='List of device IDs to check the upload queue length of.')
    parser.add_argument('--upload_queue_threshold', required=False, default=500,
                        help='Only perform the upload requests when the upload queue is below this threshold of pending tasks.')
    parser.add_argument('--max_wait_time', required=False, default=3600,
                        help='How long to continue waiting if the upload queue is full, before breaking iteration, in seconds.')  # Default of 1 hour
    parser.add_argument('--dry_run', action='store_true', help='Perform a dry run (skip actual API requests).')

    args = parser.parse_args()

    process_files(args.cameras_filename, args.time_range_filename, args.token, int(args.wait_seconds),
                  int(args.max_wait_time), args.hostname, args.device_ids, int(args.upload_queue_threshold), args.dry_run)
