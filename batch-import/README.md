Batch Import Camera Setup / API Docs
===============================

This file contains documentation on the design and usage of the batch-import functionality of Camio Box.

### Box API Documenation


POST `/box/content`

Query args:

- `accesstoken`: `device_id` of the Box being used, serves as some sort of shared secret
- `local_camera_id`: the ID of the camera as given by the user
- `camera_id`: the camera ID of the batch input source (TODO: why do we need both of these?)
- `hash`: SHA sum of the content being posted, used to map segments back to the original source
- `timestamp`: starting timestamp (ISO8601 YYYY-mm-ddTHH:MM:SS.FFFF format) of the video

Body:

- H.264 encoded video content in an mp4 container.

This endpoint is how you get video data onto Box for segmentation and analysis. You upload video files to the webserver running on Box through the
`/box/content` endpoint, associating the video file with a regitered camera in the process. The video is segmented, analyzed, and eventually sent to the Camio
servers where it is indexed and available for search through the Camio website.


GET `/box/settings`

returns 

```json

{
  "device_id": "SDFSDFSDFSD",
  "user-agent": "Linux (x86/64) Camio Box VirtualBox 2017-04-22:ab234badsfb293nas9db9f7231arereds",
}
```

This endpoint serves as a simple way to get some necessary information about the Camio Box you are using for segmentation.
To POST content to Box you'll need to supply the device_id as a form of a shared secret and you'll need to supply the same value
when registering a camera as a batch-input source.


### Registering a Camera

Registering a camera is done as follows

POST `/api/cameras/discovered`

Headers: `"Authorization: token $CAMIOTOKEN"`

Body: JSON blob with the following structure

```json
{
    "$localcameraid": {
    "device_id_discovering": "$device_id",
    "acquisition_method": "batch",
    "device_user_agent": "",
    "user_id": "$userid",
    "local_camera_id": "$localcameraid",
    "name": "$cameraname",
    "mac_address": "$localcameraid",
    "maker": "",
    "rtsp_path": "",
    "rtsp_server": "",
    "should_config": false,
  }
}  
```

The `"acquisition_method": "batch"` line is important, it is how we tell the server that this is a batch-input
source instead of a real-time video feed. `$device_id` is the ID of the Box that will be used to accept videos
for this batch-input source. 


Inside of [`register_batch_source.sh`](batch-import/register_batch_source.sh) is a function `register_batch_source` that can be used to register 
a batch-input-source with the Camio servers. Once this is done you need to go to your 
`https://www.camio.com/boxes` page and attach the camera to the Box that you want to process 
the video in batch mode.


### POST to `/box/content` example

In the [`post_content.sh`](batch-import/post-content.sh) script there is a function `post_batch_import` that handles the sending
of a video file to the Box for segmentation and analysis.

This will only work if you already have a camera registered under your account with the `"acquisition_mode": "batch"` option 
set in the config for that camera (see *Registering a Camera* section). That camera must then be attached to the
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
