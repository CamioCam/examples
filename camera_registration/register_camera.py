#!/usr/bin/env python

DESCRIPTION = \
"""
this script allows one to register a camera source with the Camio service through 
the /api/devices/registered endpoint. Camera registration is normally done automatically 
by a Camio Box that scans the local network and automatically detects and registers the cameras
that it finds, this script allows one to register a camera that a Camio Box doesn't know how to recognize.

This script is meant to be used by 3rd parties who wish to use their cameras/nvrs/dvrs with the Camio service,
they can use this script to register their device with the correct RTSP connection information. Once registered, 
the camera/dvr/nvr will show up as an entry on your https://www.camio.com/boxes page, where you can choose to connect
it to a Camio Box and have the video stream processed.

*NOTE* - Camio only supports H264 encoded video streams, mjpeg, etc. will not work.

Camio uses mustache-style placeholders in the RTSP URLs for the following values:
    username
    password
    ip_address
    port
    stream
    channel

You can place these as {{placeholder}} anywhere inside of the RTSP URL, and we will fill in the appropriate values before attempting to
connect to the given device.
"""

EXAMPLES = \
"""
Examples:

To register a camera with:
name:        my_new_camera
make:        Hikvision
model:       DCS-2302-I
username:    admin
password:    admin
port:        8080
ip address:  192.168.1.18
RTSP URL:    rtsp://{{username}}:{{password}}@{{ip_address}}:{{port}}/live/{{stream}}.h264
camera-ID:   AABBCCDDEEDD.0
MAC address: AABBCCDDEEDD

you would do the following:

python register_camera.py -v -u admin -p admin -s 1 -i 192.168.1.18 -p 8080 \\
        --make Hikvision --model DCS-2302-I \\
        rtsp://{{username}}:{{password}}@{{ip_address}}:{{port}} \\
        /live/{{stream}}.h264 AABBCCDDEEDD AABBCCDDEEDD.0 my_new_camera ASDASDASDASDASDA
"""

import argparse
import sys
import os
import json
import textwrap
import requests

CAMIO_SERVER_URL = "https://www.camio.com"
CAMIO_TEST_SERVER_URL = "https://test.camio.com"

REGISTER_CAMERA_ENDPOINT = "/api/cameras/discovered"
DEBUG_OUTPUT = False

def print_debug(string):
    if DEBUG_OUTPUT:
        sys.stderr.write(string + '\n')

def parse_cmd_line_or_exit():
    global DEBUG_OUTPUT
    global CAMIO_SERVER_URL
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = textwrap.dedent(DESCRIPTION), epilog=EXAMPLES
    )
    parser.add_argument('-u', '--username', type=str, help='the username used to access the RTSP stream')
    parser.add_argument('-p', '--password', type=str, help='the password used to access the RTSP stream')
    parser.add_argument('-s', '--stream', type=str, help='the selected stream to use in the RTSP URL')
    parser.add_argument('-c', '--channel', type=str, help='the selected stream to use in the RTSP URL')
    parser.add_argument('-P', '--port', type=int, help='the port that the RTSP stream is accessed through', default=554)
    parser.add_argument('-i', '--ip_address', type=str, help='The IP address of the camera (local or external)')
    parser.add_argument('--maker', type=str, help='the make (manufacturer name) of the camera')
    parser.add_argument('--model', type=str, help='the model of the camera')
    parser.add_argument('--test', action='store_true', help='use the Camio testing servers instead of production')
    parser.add_argument('-v', '--verbose', action='store_true', help='print extra information to stdout for debugging purposes')
    parser.add_argument('rtsp_server', type=str, 
        help='the RTSP URL that identifies the video server, with placeholder (e.g. rtsp://{{username}}:{{password}}@{{ip_address}})'
    )
    parser.add_argument('rtsp_path', type=str, 
        help='the path that is appended to the rtsp_server value to construct the final RTSP URL, with placeholders (e.g. /live/{{stream}}.h264)'
    )
    parser.add_argument('mac_address', type=str, help='the MAC address of the device being connected to')
    parser.add_argument('local_camera_id', type=str, help='some string representing an ID for your camera. Must be unique per account')
    parser.add_argument('camera_name', type=str, help='some user-friendly name for your camera')
    parser.add_argument('auth_token', type=str, help='your Camio auth token (see https://www.camio.com/settings/integrations)')
    args = parser.parse_args()
    if args.verbose: DEBUG_OUTPUT = True
    if args.test: CAMIO_SERVER_URL = CAMIO_TEST_SERVER_URL
    return args
    
def generate_payload(args):
    actual_values=dict()
    arg_dict = args.__dict__
    for item in [x for x in ['username', 'password', 'port'] if arg_dict.get(x)]:
        actual_values[item] = dict(options=[{'value': arg_dict.get(item)}])
    for item in [x for x in ['stream', 'channel'] if arg_dict.get(x)]:
        actual_values[item] = dict( 
            options = [ {'name': "%s %s" % (item, arg_dict.get(item)), 'value': arg_dict.get(item)}]
        )
    payload = dict(
        local_camera_id=args.local_camera_id,
        name=args.camera_name,
        mac_address=args.mac_address,
        maker=arg_dict.get('maker', ''), 
        model=arg_dict.get('model', ''), 
        ip_address=arg_dict.get('ip_address', ''), # ip address might not always be specified separately 
        rtsp_server=args.rtsp_server,
        rtsp_path=args.rtsp_path,
        actual_values=actual_values,
        default_values=actual_values
    )
    payload = dict(
        local_camera_id=payload
    )
    print_debug("JSON payload to Camio Servers:\n %s" % json.dumps(payload))
    return payload

def generate_headers(args):
    headers = {"Authorization": "token %s" % args.auth_token}
    print_debug("Generated Headers:\n %s" % headers)
    return headers

def post_payload(payload, headers):
    url = CAMIO_SERVER_URL + REGISTER_CAMERA_ENDPOINT
    ret = requests.post(url, headers=headers, json=payload)
    print_debug("return from POST to /api/cameras/discovered:\n %s" % vars(ret))
    return ret.status_code in (200, 204)

def main():
    args = parse_cmd_line_or_exit()
    print_debug("Parsed command line arguments:\n %s" % args.__dict__)
    post_values = generate_payload(args)
    headers = generate_headers(args)
    if not post_payload(post_values, headers):
        sys.stderr.write("error registering camera (name: %s, ID: %s) with Camio servers" % (args.camera_name, args.local_camera_id))
        sys.exit(1)
    sys.stdout.write("successfully registered camera (name: %s, ID: %s) with Camio servers" % (args.camera_name, args.local_camera_id))
    sys.exit(0)


if __name__ == '__main__':
    main()
