Batch Import
===============

These examples show how to import video files in bulk using Camio.

## Using the [Video Importer](https://github.com/tnc-ca-geo/video-importer) with Camio Box

The open source [video importer](https://github.com/tnc-ca-geo/video-importer) allows you to specify a set of hooks that describe how the importer
should interact with the segmentation and labeling service of your choosing. To use the video-importer with the Camio service, you must supply the
[`camio_hooks.py`](camio_hooks.py) module as the value for the the [`--hooks_module` argument](https://github.com/tnc-ca-geo/video-importer#hook-module)
 of the video importer.

The video importer calls the [`register_camera`](https://github.com/tnc-ca-geo/video-importer#camera-registration-function) 
and [`post_video_content`](https://github.com/tnc-ca-geo/video-importer#post-video-content-function) functions that take care 
of processing the video with the Camio services. These functions are designed to seemelessly integrate with a Camio Box on your local network, which will handle the 
segmentation and first-level analysis of the vidoe content before sending off the results to Camio servers for further processing and labeling.


#### Setting up the Environment

To use the [`camio_hooks.py`](camio_hooks.py) module, Camio needs to know some account information. You can either define this in json format through the 
`--hook_data_json` argument, or you can define some environment variables for yourself. These variables are:

| Variable | Description |
| -------- | ------------|
| `CAMIO_OAUTH_TOKEN` | set this to the Developer OAuth token that is generated from your [Camio settings](https://camio.com/settings/integrations#api) page. |
| `CAMIO_BOX_DEVICE_ID` | set this to the `device_id` of the [Camio Box](https://camio.com/box) that's processing your imported video files. You can get your  `device_id` from your [/boxes](https://camio.com/boxes) page. Until there's a more convenient way to copy and paste your `device_id`, please copy it from the URL hash parameter `device_id` that's shown in your browser's address bar on that page. | 

You can set environment variables by putting them in a file like `/home/$user/.bashrc` as:

```bash
export CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYX" 
```

Then source the file by running:

```bash
source ~/.bashrc
```

If you don't want to set them permanently like this, you can also prepend the variable definitions to the command that runs the video importer script; for example, 
where `$args` is a placeholder for the actual arguments you'd supply to the script, you would enter:

```bash
CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYZ" CAMIO_BOX_DEVICE_ID="sdfsdfsdfsdfsdfsdfsdf" python import_video.py $args
```

Once these environment variables are set, there are three more steps before you can start the import:
 
1. Get your [Camio Box](https://camio.com/box) (also available as [free VM](https://camio.com/box/vm)) running and registered under your account.
2. Obtain the IP address of your Camio Box. This will soon be displayed on the [/boxes](https://camio.com/boxes) page, but until then, please
use a network scanning tool like [Fing](https://help.camio.com/hc/en-us/articles/206214636) to find its IP address.
3. Create a regular expression for the importer's [`--regex` argument](https://github.com/tnc-ca-geo/video-importer#metadata-extraction-with---regex) that defines the capture groups for `camera_name` and `timestamp` extracted from the video filenames being imported.

#### Setting Camera-specific Data (plans, image resolution, etc)

There are two main ways to get data into the `camio_hooks.py` module from the video-import script.

1. Through the `--hook_data_json` argument. Supply this argument and then follow it up with a string representing a json object that contains the data needed to be passed in.
2. Through the `--hook_data_json_file` argument. Supply this argument and then the path to a file containing a string represeting a json object with the data needed to be passed to the hooks.

The structure of the JSON passed in should look something like what follows:

```json
{
    "plan": "plus",
    "cameras": {
        "camera_name_2": {
            "plan": "pro",
            "img_y_size_extraction": 1080,
            "img_x_size_cover": 1920,
            "img_y_size_cover": 1080,
            "img_x_size": 1280,
            "img_y_size": 720
        },
        "camera_name_1": {
            "plan": "pro",
            "img_y_size_extraction": 1080,
            "img_x_size_cover": 1920,
            "img_y_size_cover": 1080,
            "img_x_size": 1280,
            "img_y_size": 720
        },
    },
    "img_y_size_extraction": 1080,
    "img_x_size_cover": 1920,
    "img_y_size_cover": 1080
}
```

Notice that you are able to specify on a per-camera basis by putting the values inside of the `cameras.{{camera_name}}` objects. These values will only apply to the camera with
`camera_name` as the name. If you place the values at the top-level, then we will use those values for any cameras who do not have custom values specified.

The values you can specify (meaningfully) as of now are:

1. `plan` - can be any of `basic`, `plus`, and `pro`. See https://www.camio.com/price for information on plans
2. `img_y_size_extraction` - the height of the frames extracted from the videos (before resizing!)
3. `img_{x,y}_size_cover` - the x,y size (in pixels) of the cover-image after resizing.
4. `img_{x,y}_size` - the x,y size (in pixels) of the non-cover images after resizing.

Note that if `img_y_size` or `img_y_size_cover` are larger than `img_y_size_extraction` we will replace the value of `img_y_size_extraction` with the larger of the two other values.
This is because it doesn't make sense to extract at a lower resolution only to scale up.


#### Running the Import

Now [run the video importer](https://github.com/tnc-ca-geo/video-importer#running-the-importer) with a command line that looks something like this:

```bash
$ python import_video.py \
  --regex ".*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4" \
  --host 192.168.1.57 \
  --port 8080 \
  --hook_data_json_file /tmp/camio_hook_data.json \
  "~/my-folder" \ # folder containing input videos
  "camio_hooks" \ # hooks module with callback functions
  "192.168.1.57"  # ip-address / hosntame of the segment server
```

In the example above, the Camio Box that's running on port `8080` of the ip address `192.168.1.57`:

1. analyzes the motion in each video to segment the video files into smaller events
2. creates metadata for each event that isolated real motion, color-blocking, direction of movement, etc...
3. submits selected events for advanced labeling via camio.com, which includes all registered labeling hooks

Upon completion of the import, all the resulting labeled events can be downloaded using the Camio Search API.
The downloaded JSON includes the `camera_id`, `camera_name`, `earliest_date`, `latest_date` and `labels` for each event.

### Checking Job Status

Here is the full documentation for the [Jobs API](api.camio.com/#jobs). To get information about a specific job given a job ID, you would do the following.

`GET https://www.camio.com/api/jobs/{{job_id}}`

Where `{{job_id}}` is the value returned returned from a `PUT` request to the `https://www.camio.com/api/jobs` endpoint. This `GET` request returns the following payload

```json
{
    "job_id": "agpIDYggsM",
    "shard_map": {
        "0": {
            "item_count": 2048,
            "job_id": "agpIDYggsM",
            "shard_id": "0",
            "status": "missing"
        },
        "1": {
            "item_count": 2048,
            "job_id": "agpIDYggsM",
            "shard_id": "1",
            "status": "missing"
        },
        "2": {
            "item_count": 3,
            "job_id": "agpIDYggsM",
            "shard_id": "2",
            "status": "missing"
        }
    },
    "status": "shards_missing"
}
```



### Getting Job Results

Once a job has been finished you are able to export a payload (in either json, csv, or xml format) that described the labels assocaited with the submitted videos.

@TODO - describe how you goes about asking for the labels to be exported

