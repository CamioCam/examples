Batch Import
===============

This README documents the usage of both the `import_video.py` script that will traverse and upload a directory of videos and the `camio_hooks.py` module
that allows the `import_video.py` script to interface with the Camio service. 

For a concrete, step-by-step example of how to use these programs, see the [EXAMPLE.md](batch_import/EXAMPLE.md) file. 

## Using the [Video Importer](https://github.com/tnc-ca-geo/video-importer) with Camio Box

The open source [video importer](https://github.com/tnc-ca-geo/video-importer) allows you to specify a set of hooks that describe how the importer
should interact with the segmentation and labeling service of your choosing. To use the video-importer with the Camio service, you must supply the
[`camio_hooks.py`](camio_hooks.py) module as the value for the the [`--hooks_module` argument](https://github.com/tnc-ca-geo/video-importer#hook-module)
 of the video importer. You must also have a batch-import-enabled Camio Box VM running on your local network.

The video importer calls the [`register_camera`](https://github.com/tnc-ca-geo/video-importer#camera-registration-function) 
and [`post_video_content`](https://github.com/tnc-ca-geo/video-importer#post-video-content-function) functions that take care 
of processing the video with the Camio services. These functions are designed to seemelessly integrate with a Camio Box on your local network, which will handle the 
segmentation and first-level analysis of the vidoe content before sending off the results to Camio servers for further processing and labeling.

#### Obtain and Set-up Your Batch-Import Enabled Camio Box

Follow all of the instructions listed in [this help article for setting up Camio Box VM in VirtualBox](https://help.camio.com/hc/en-us/articles/115000667046-How-to-Setup-Camio-Box-i
but (IMPORTANT) use [this version of Camio Box VM for VirtualBox](https://storage.googleapis.com/camio_firmware_images/camio-box-os-virtualbox-2017-05-16.zip) instead of the version
The reason for the switch is that [this new version](https://storage.googleapis.com/camio_firmware_images/camio-box-os-virtualbox-2017-05-16.zip) of the Camio Box VM includes suppor
in that help-article does not. The rest of the steps are the same.

#### Boot-Up Your Camio Box

Your Camio Box needs to be powered on, registered under your account, and on the same local network as the computer running the batch-importer script.
Your Camio Box can be registered through [the /box/register page](https://www.camio.com/box/register).

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

After batch-importing videos with the [`import_video.py`](batch_import/video-importer/import_video.py) script, you were returned a job ID. 
You can use this value along with the [`batch_download.py](batch_import/batch_download.py) script to download a bookmark of all labels for all events that
were processed through the batch-import job.


To see how to use the script, you can enter the following into a shell from the `examples/batch_import/` directory.

```bash
python batch_download.py --help
```

Which will output the following:

```sh
$ python batch_download.py --help
usage: batch_download.py [-h] [-a ACCESS_TOKEN] [-c] [-x] [-t] [-v] [-q]
                         [job_id] [output_file]

This script will take a Camio job-ID, find the time-boundaries and cameras 
involved in that job, and iterate over that time range while downloading all 
of the labels that Camio has annotated the events with.

This script is designed to be used after a batch-import job has been completed 
and you wish to retreive a compilation of all of the labels assigned to all of 
the events that were parsed from the grouping of batch import video you submitted 
for the given job.

If no job_id is submitted this script will query all of the jobs listed for your
account and display them to you before exiting.

positional arguments:
  job_id                the ID of the job that you wish to download the labels
                        for
  output_file           full path to the output file where the resulting
                        labels will be stored in json format (default =
                        {job_id}_results.json)

optional arguments:
  -h, --help            show this help message and exit
  -a ACCESS_TOKEN, --access_token ACCESS_TOKEN
                        your Camio OAuth token (if not given we check the
                        CAMIO_OAUTH_TOKEN envvar)
  -c, --csv             set to export in CSV format
  -x, --xml             set to export in XML format
  -t, --testing         use Camio testing servers instead of production (for
                        dev use only!)
  -v, --verbose         set logging level to debug
  -q, --quiet           set logging level to errors only

Example:

    Here is an example of how to run the script to recover a dictionary of lables for
    the last job that you submitted

    python batch_download.py -v SjksdkjoowlkjlSDFifajoijerWE231dsdf /home/me/outputfile.json

```

So this script takes in a job-id, queries the [Camio API](https://api.camio.com/#jobs) to get the job definition, then uses 
the job definition and the [Camio search API](https://api.camio.com/#search) to go through all events that belong to that job. While
going through all of these events it assembles the labels into a json object and writes this object to the output file (which can be specified 
by you or simply defaults to `{job_id}_results.json`). This json object has the following structure

```json
{
    "earliest_date": "1970-01-01T12:00:00.0000-0000",
    "latest_date": "1970-01-01T12:30:00.0000-0000",
    "job_id": "sdfslkjfjowejoijsldkjflksjdf",
    "labels": {
         "1970-01-01T12:00:01.0345-0000": {
              "cameras": {
                  "camera_name_1": {
                      "name": "camera_name_1",
                      "camera_id": "wer9ikjsodfj09j34rojiosj"
                   }
                },
                "labels": [
                    "dog",
                    "car",
                    "human"
                ]
            }
         },
         "1970-01-01T12:00:03.02089-0000": {
              "cameras": {
                  "camera_name_1": {
                      "name": "camera_name_1",
                      "camera_id": "wer9ikjsodfj09j34rojiosj"
                   }
                },
                "labels": [
                    "human",
                    "suv",
                    "tree"
                ]
            }
        }
    }
}
```

