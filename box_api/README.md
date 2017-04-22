Batch Import with the Camio Box API
===================================

This file contains documentation on the design and usage of the Camio Box API for importing video files in batch (vs. real-time).

The `/box/content` API enables you to submit video files to Camio for analysis and labeling.
This makes it possible to index and label existing video files in the same way that a Camio Box 
segments and labels video from real-time RTSP video sources.

## Overview

At a high-level, these are the steps required to analyze existing video with Camio.

1. Sign up for a [Camio account](https://camio.com/account).
2. Purchase a [Camio Box](https://camio.com/box) or download a free [Camio Box VM](https://camio.com/box/vm) and run it on your local network.
3. Register a camera with `batch` specified as `acquisition_method` using the Camio API to [Create a Camera](https://api.camio.com/#create-a-camera).
4. Submit video content via your Camio Box's `POST /box/content` API.
5. [Search](https://api.camio.com/#search), or [browse](https://camio.com/app/#search) the labeled video after Camio has segmented, analyzed and labeled the video. 


## Box API Documenation

### Uploading Content

Please see the Camio Box [`/box/content`](https://api.camio.com/#upload-content) API for documentation
on submitting video files for batch processing.


### Settings

Please see the Camio Box [`/box/settings`](https://api.camio.com/#get-settings-camio-box) API for documentation
on fetching the `device_id` and `User-Agent` of your locally running Camio Box.


## Registering a Camera

Please see the [`/api/cameras/discovered`](https://api.camio.com/#create-a-camera) API for documentation
on creating a camera that is registered to your account.

An example request for registering a camera for batch import via Camio Box is:

```
POST /api/cameras/discovered
```

with HTTP Header:

```
Authorization: token {{oauth_token}}
```

and JSON body: 

```json
{
    "{{localcameraid}}": {
    "device_id": "{{device_id}}",
    "acquisition_method": "batch",
    "user_id": "{{user_id}}",
    "local_camera_id": "{{local_camera_id}}",
    "name": "{{camera_name}}",
    "mac_address": "{{mac_address}}",
    "should_config": true
  }
}  
```

// TODO(carter) change localcameraid -> local_camera_id; remove `user_id`, `mac_address` from input. Rename `should_config`.

The `"acquisition_method": "batch"` line is important. That's how you tell the Camio servers that this is a batch input
source rather than a real-time RTSP video stream. The `device_id` is the ID of the Camio Box that's receiving video from this
camera source.

The function `register_batch_source` in [`register_batch_source.sh`](register_batch_source.sh) shows how to 
register a camera for batch import. 


## Submitting Video Files

The function `post_batch_import` in the [`post_content.sh`](post-content.sh) script shows how to POST a video file
to the Camio Box for segmentation and analysis.

This will only work if you already have a camera registered under your account with the `"acquisition_mode": "batch"` option 
set in the config for that camera (see [Registering a Camera](#registering-a-camera)). 

TODO(carter) make all variables snake case (e.g. cameraid -> camera_id)

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
# assuming the video the user wants to segment is at /home/$user/movie.mp4
post_batch_import $host $port ~/movie.mp4 $cameraid $camiocameraid $device_id $timestamp
```
