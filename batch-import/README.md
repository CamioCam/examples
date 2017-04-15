Batch Import Camera Setup / API Docs
===============================

This file contains documentation on the design and usage of the batch-import functionality of Camio Box.

### Box API Documenation

POST `/box/content`

Query args:

- `accesstoken`: `device_id` of the Box being used, serves as some sort of shared secret
- `local_camera_id`: the local camera ID for the batch input source
- `camera_id`: the camera ID of the batch input source (TODO: why do we need both of these?)
- `hash`: SHA sum of the content being posted, used to map segments back to the original source
- `timestamp`: starting timestamp of the video, the timestamps of the segments are calculated from there.

Body:

- H.264 encoded video content in an mp4 container.


### Registering a Camera

Registering a camera is done as follows

POST `/api/cameras/discovered'
Headers: `"Authorization: token $CAMIOTOKEN"`
Body: JSON blob with the following structure

```json
{
    "$localcameraid": {
    "device_id_discovering": "$deviceid",
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
    "default_values": {
    },
    "actual_values": {
    },
  }
}  
```

The `"acquisition_method": "batch"` line is important, it is how we tell the server that this is a batch-input
source instead of a real-time video feed. `$deviceid` is the ID of the Box that will be used to accept videos
for this batch-input source. 


Inside of `register_batch_source.sh` is a function `register_batch_source` that can be used to register 
a batch-input-source with the Camio servers. Once this is done you need to go to your 
`https://www.camio.com/boxes` page and attach the camera to the Box that you want to process 
the video in batch mode.


### POST to `/box/content` example

Below is a function that I use to test out the batch import API on a running Box. This function serves to take a 
video file you have locally and post it to the `/content` endpoint on a running Box that has batch-import enabled.

This will only work if you already have a camera registered under your account with the `"acquisition_mode": "batch"` option 
set in the config for that camera (see *Registering a Camera* section).

This will post that video to the camera with the given `camera_id` and `local_camera_id`, the `camera_id` is generally
`$user_id:$localcameraid:$localcameraid`

```bash
# source the script
. post_content.sh 
# setup the parameters
cameraid="AAAABBBBCCCC.0"
deviceid="ZXCVZXCVZXCV-QWERTQWERT"
host="192.168.1.18"
port="8080"
timestamp="2017-04-02T18:48:32.0000"

# post the content
# assuming the video we want to segment is at /home/$user/movie.mp4
post_batch_import $host $port ~/movie.mp4 $cameraid $cameraid $deviceid $timestamp
```
