Batch Import Camera Setup / API Docs
===============================

This file contains documentation on the design and usage of the batch-import functionality of Camio Box.

Batch-import is a feature that allows you to send videos to Camio for analysis through a Camio Box. This makes it possible
to index and label existing videos in the same way that a Camio Box allows one to segment, label, and videos from real-time 
input sources like cameras that stream over RTSP.

## Overview

At a high-level, the following steps are needed to analyze existing video through Camio.

1. Register an account with Camio
2. Purchase a Camio Box or download a VM image of one, setup the Box on your local network.
3. Register a camera source in 'batch' acquisition mode with our service through the Camio API
4. Send the video content to the web server running on your Camio Box either manually or using our importer script.
5. Let the Box segment, process, and analyze the video. Once it is done the clips will be available through the Camio webapp.


## Box API Documenation


###### POST `/box/content`


Query args:

- `accesstoken`: `device_id` of the Box being used, serves as shared secret
- `local_camera_id`: the ID of the camera as given by the user
- `camera_id`: the camera ID of the batch input source (TODO: why do we need both of these?)
- `hash`: SHA sum of the content being posted, used to map segments back to the original source
- `timestamp`: starting timestamp (ISO8601 YYYY-mm-ddTHH:MM:SS.FFFF format) of the video

Body:

- H.264 encoded video content in an mp4 container.

This endpoint is how you get video data onto Box for segmentation and analysis. You upload video files to the webserver running on Box through the
`/box/content` endpoint, associating the video file with a regitered camera in the process. The video is segmented, analyzed, and eventually sent to the Camio
servers where it is indexed and available for search through the Camio website.


###### GET `/box/settings`

returns 

```json

{
  "device_id": "ZADfg23_98kuS-3FyLv2oxbPrsOPqmerT534aDf56wlUUde8X2B_7B2hBv3-t56bk-sRoBVgaonxCMpi4CAmLkvmT0fz",
  "user-agent": "Linux (x86/64) Camio Box VirtualBox 2017-04-22:ab234badsfb293nas9db9f7231arereds",
}
```

This endpoint serves as a simple way to get some necessary information about the Camio Box you are using for segmentation.
To POST content to Box you'll need to supply the device\_id as a form of a shared secret and you'll need to supply the same value
when registering a camera as a batch-input source.

## Using the [Video Import Script](https://github.com/tnc-ca-geo/video-importer) For Batch Import

The open-source [video import script](https://github.com/tnc-ca-geo/video-importer) can be used to batch-import videos from a directory
to a Camio Box. This is accomplished by passing in the [camio_hooks.py](batch_import/camio_hooks.py) module into the importer script as
the `--hooks_module` argument. This causes the importer to use the callback camera-registration and content-post functions that are necessary
for interaction with the Camio servers.

#### Environment Variables

To use the `camio_hooks` module, you first must define some environment variables for yourself. These variables are

 - `CAMIO_OAUTH_TOKEN` - set this to the oauth token that is generated from your [Camio settings](https://www.camio.com/settings/integrations) page.
 - `CAMIO_BOX_DEVICE_ID` - set this to the device ID of the Camio Box that you are sending the video to for segmentation and analysis. This can be gotten from the URL 
   on your [/boxes](https://www.camio.com/boxes) page, after the query-parameter `device_id`. We are adding a more convenient method for obtaining this value through
   the UI on our website but that change is not currently live.

Once these environment variables are set you need to collect a few more pieces of information prior to being able to use the import script.
 
 - Get your Camio Box running and registered under your account.
 - Find the IP address of your Camio Box. You can do this with a network scanning tool like Fing.
 - The regex that defines the different attributes that can be parsed from the filenames that your are uploading.

#### File-parsing Regex

When uploading videos to a Camio Box for batch-import mode, we need to know a few attributes of the videos. These are

1. The camera name that the video came from
2. The timestamp of the video file (the actual timestamp from when the video was recorded)

The importer script will go over the directory of video files and parse out the attributes given above. For each new camera it finds (based on the camera name) 
it will register the camera with your Camio account through the Camio API. 

## Registering a Camera

Registering a camera is done as follows

POST `/api/cameras/discovered`

Headers: `"Authorization: token {{auth_token}}"`

Body: JSON blob with the following structure

```json
{
    "{{localcameraid}}": {
    "device_id": "{{device_id}}",
    "acquisition_method": "batch",
    "user_id": "{{user_id}}",
    "local_camera_id": "{{local_camera_id}}",
    "name": "{{camera_name}}",
    "mac_address": "{{local_camera_id}}",
    "should_config": false,
  }
}  
```

The `"acquisition_method": "batch"` line is important, it is how we tell the server that this is a batch-input
source instead of a real-time video feed. `{{device_id}}` is the ID of the Box that will be used to accept videos
for this batch-input source. 


Inside of [`register_batch_source.sh`](batch-import/register_batch_source.sh) is a function `register_batch_source` that can be used to register 
a batch-input-source with the Camio servers. Once this is done you need to go to your 
`https://www.camio.com/boxes` page and attach the camera to the Box that you want to process 
the video in batch mode.


## POST to `/box/content` example

In the [`post_content.sh`](batch-import/post-content.sh) script there is a function `post_batch_import` that handles the sending
of a video file to the Box for segmentation and analysis.

This will only work if you already have a camera registered under your account with the `"acquisition_mode": "batch"` option 
set in the config for that camera (see [*Registering a Camera*](#registering-a-camera) section). That camera must then be attached to the
Box that you are sending this video data to.

```bash
# source the script
. post_content.sh 
# set up the parameters
cameraid="CAMERA_EAST_ONE" # camera ID given to Camio upon registration
camiocameraid="CAMEAST1_AAAABBBBCCCC.0" # camera ID returned by Camio during registration 
device_id="ZXCVZXCVZXCV-QWERTQWERT" # ID of the Camio Box (gotten by GET /box/settings)
host="192.168.1.18"
port="8080"
timestamp="2017-04-02T18:48:32.0000"

# post the content
# assuming the video we want to segment is at /home/$user/movie.mp4
post_batch_import $host $port ~/movie.mp4 $cameraid $camiocameraid $device_id $timestamp
```
