Registering a Camera Source With Camio
==========================

## Overview

To connect a camera to Camio, you need to register the video source through the Camio API. Normally this is done automatically by a Camio Box
that scans your local network, identifies all of the cameras, and automatically registers them. If you have a camera that is not recognized by
Camio Box, you can manually register it using the [register_camera](register_camera.py) script.
## Usage

Details on the script can be found by supplying the `--help` argument to the python script, output given below:

```sh
$ python register_camera.py --help
usage: register_camera.py [-h] [-u USERNAME] [-p PASSWORD] [-s STREAM]
                          [-c CHANNEL] [-P PORT] [-i IP_ADDRESS]
                          [--maker MAKER] [--model MODEL] [--test] [-v]
                          rtsp_server rtsp_path mac_address local_camera_id
                          camera_name auth_token device_id

This script allows you to connect your cameras/nvrs/dvrs with the Camio service,
you can use this script to register your device with the correct RTSP connection information. Once registered,
the camera/dvr/nvr will show up as an entry on your https://www.camio.com/boxes page, where you can choose to connect
it to a Camio Box and have the video stream processed.

To connect a camera to your Camio account, you must specify the Camio Box `device_id` that you will be connecting the camera
to the Camio servers through. You do this by providing the device ID of the Camio Box to this script. Currently, the easiest way
to get the device ID is by going to your https://www.camio.com/boxes page and getting the device ID out of the URL.
(the URL will look like: https://www.camio.com/boxes#device_id=AABBCCDDEFFAABBDDEEFFCC, grab the AABBCCDDEFFAABBDDEEFFCC part)

*NOTE* - Camio only supports H.264 encoded video streams, mjpeg, etc. will not work.

Camio uses mustache-style placeholders in the RTSP URLs for the following values:
    username
    password
    ip_address
    port
    stream
    channel

You can place these as {{placeholder}} anywhere inside of the RTSP URL, and Camio will fill in the appropriate values before attempting to
connect to the given device.

positional arguments:
  rtsp_server           the RTSP URL that identifies the video server, with
                        placeholder (e.g.
                        rtsp://{{username}}:{{password}}@{{ip_address}})
  rtsp_path             the path that is appended to the rtsp_server value to
                        construct the final RTSP URL, with placeholders (e.g.
                        /live/{{stream}}.h264)
  mac_address           the MAC address of the device being connected to
  local_camera_id       some string representing an ID for your camera. Must
                        be unique per account
  camera_name           some user-friendly name for your camera
  auth_token            your Camio auth token (see
                        https://www.camio.com/settings/integrations)
  device_id             the device ID of the Camio Box you wish to connect
                        this camera to

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        the username used to access the RTSP stream
  -p PASSWORD, --password PASSWORD
                        the password used to access the RTSP stream
  -s STREAM, --stream STREAM
                        the selected stream to use in the RTSP URL
  -c CHANNEL, --channel CHANNEL
                        the selected stream to use in the RTSP URL
  -P PORT, --port PORT  the port that the RTSP stream is accessed through
  -i IP_ADDRESS, --ip_address IP_ADDRESS
                        The IP address of the camera (local or external)
  --maker MAKER         the make (manufacturer name) of the camera
  --model MODEL         the model of the camera
  --test                use the Camio testing servers instead of production
  -v, --verbose         print extra information to stdout for debugging
                        purposes
```

## Examples

Below is an example of how to run the script to register a camera with the Camio service. The camera connection parameters are listed, 
and then below that is how you would arrange those parameters when running the script.

To register a camera with:

| key   | value  |
| ----- | ---------------- |
| name    |  Front Entrance |
| make |        Hikvision  |
| model |       DCS-2302-I |
| username |    admin |
| password |    admin |
| port |        8080 |
| ip address |  192.168.1.18 |
| RTSP URL |    rtsp://{{username}}:{{password}}@{{ip_address}}:{{port}}/live/{{stream}}.h264 |
| camera-ID |   AABBCCDDEEDD.0 | 
| MAC address | AABBCCDDEEDD |

you would execute the following command:

```
python register_camera.py -v -u admin -p admin -s 1 -i 192.168.1.18 -p 8080 \
        --make Hikvision --model DCS-2302-I \
        rtsp://{{username}}:{{password}}@{{ip_address}}:{{port}} \
        /live/{{stream}}.h264 AABBCCDDEEDD AABBCCDDEEDD.0 "Front Entrance" \
        $CAMIO_ACCOUNT_AUTH_TOKEN $CAMIOBOX_DEVICE_ID
```
