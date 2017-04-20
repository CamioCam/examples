Camio Box Batch-Import with the Video Importer
===============

## Using the [Video Importer](https://github.com/tnc-ca-geo/video-importer) For Batch Import

The open-source [video import script](https://github.com/tnc-ca-geo/video-importer) can be used to batch-import videos from a directory
to a Camio Box. This is accomplished by passing in the [camio_hooks.py](batch_import/camio_hooks.py) module into the importer script as
the `--hooks_module` argument. This causes the importer to use the callback camera-registration and content-post functions that are necessary
for interaction with the Camio servers.

####  Setting up the Environment

To use the `camio_hooks` module, you first must define some environment variables for yourself. These variables are

 - `CAMIO_OAUTH_TOKEN` - set this to the oauth token that is generated from your [Camio settings](https://www.camio.com/settings/integrations) page.
 - `CAMIO_BOX_DEVICE_ID` - set this to the device ID of the Camio Box that you are sending the video to for segmentation and analysis. This can be gotten from the URL 
   on your [/boxes](https://www.camio.com/boxes) page, after the query-parameter `device_id`. We are adding a more convenient method for obtaining this value through
   the UI on the Camio website but that change is not currently live.

You can set environment variables by putting them in a file like `/home/$user/.bashrc` as `export CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYX"`, then sourcing the file
by running `source ~/.bashrc`. If you don't want to set them permentantly like this, you can also prepend the definitions to the command to run the script, so something like

```bash
CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYZ" CAMIO_BOX_DEVICE_ID="sdfsdfsdfsdfsdfsdfsdf" python importer.py $args
```

Once these environment variables are set you need to collect a few more pieces of information prior to being able to use the import script.
 
 - Get your Camio Box running and registered under your account.
 - Find the IP address of your Camio Box. You can do this with a network scanning tool like Fing.
 - The regex that defines the different attributes that can be parsed from the filenames that your are uploading.

#### File-parsing Regex

When uploading videos to a Camio Box for batch-import mode, Camio needs to know a few attributes of the videos. These are

1. The camera name that the video came from
2. The timestamp of the video file (the actual timestamp from when the video was recorded)

The importer script will go over the directory of video files and parse out the attributes given above. For each new camera it finds (based on the camera name) 
it will register the camera with your Camio account through the Camio API. 

*Example*

Let's say you had videos in a directory of the format

`CAMERA_FRONT-rand-1475973147.mp4`
`CAMERA_FRONT-rand-1475973267.mp4`
`CAMERA_FRONT-rand-1475973350.mp4`

Then you would supply something like the following regex to the importer script:

`.*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4`

This regex would put `CAMERA_FRONT` into the `camera` variable (which the importer uses internally to hold the camera name) and would put the `14759753350` value into the
`epoch` variable, which represents the Unix timestamp for the video. 

