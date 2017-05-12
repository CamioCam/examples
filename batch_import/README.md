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

#### Setting the Camera Plan

Camio has varying levels of service; starting off with BASIC, moving up to PLUS, and finally the PRO plan. You can tell Camio which plan you would like to use for
your batch-input source by specifying the 'plan' variable inside of the json passed to the `--hook_data_json` argument to the video-importer. This argument
must be a valid json dictionary, and anything defined in it will be passed to the `camio_hooks.py` module. As an example, you would do the following to set the plan to
'basic' for your camera.

```bash
python import_video.py "...some arguments.." --hook_data_json '{"plan": "basic"}'
```

Valid values for the plan variable are 'basic', 'plus', and 'pro'.


#### Running the Import

Now [run the video importer](https://github.com/tnc-ca-geo/video-importer#running-the-importer) with a command line that looks something like this:

```bash
importer.py \
  --regex ".*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4" \
  --folder "/my-folder" \
  --host 192.168.1.57 \
  --port 8080 \
  --hook_module camio_hooks
  --hook_data_json '{"plan": "basic"}'
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

