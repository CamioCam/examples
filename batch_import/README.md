Batch Import
===============

This README documents the usage of both the `import_video.py` script that will traverse and upload a directory of videos and the `camio_hooks.py` module
that allows the `import_video.py` script to interface with the Camio service. 

For a concrete, step-by-step example of how to use these programs, see the [EXAMPLE.md](/batch_import/EXAMPLE.md) file. 

## Using the [Video Importer](https://github.com/tnc-ca-geo/video-importer) with Camio Box

The open source [video importer](https://github.com/tnc-ca-geo/video-importer) allows you to specify a set of hooks that describe how the importer
should interact with the segmentation and labeling service of your choosing. To use the video-importer with the Camio service, you must supply the
[`camio_hooks.py`](camio_hooks.py) module as the value for the the [`--hooks_module`](https://github.com/tnc-ca-geo/video-importer#hooks_module)
argument of the video importer. You must also have a [batch-import-enabled Camio Box VM](#obtain-and-set-up-your-batch-import-enabled-camio-box) 
running on your local network.

The video importer calls the [`register_camera`](https://github.com/tnc-ca-geo/video-importer#register_camera) 
and [`post_video_content`](https://github.com/tnc-ca-geo/video-importer#post_video_content) functions that take care 
of processing the video with Camio services. These functions integrate seamlessly with a Camio Box running on your local network and will handle the 
segmentation and first-level analysis of the video content before submitting the results to Camio servers for further processing and labeling.

#### Obtain and Set-up Your Batch-Import Enabled Camio Box

Follow all of the instructions listed in [this help article for setting up Camio Box VM in VirtualBox](https://help.camio.com/hc/en-us/articles/115002492123)

#### Installing the Dependencies

The scripts in this repository are meant to be run by a Python 2.7 interpreter. Python2.7 comes installed by default
on OSX and most Linux distributions, to check that it is installed on your machine, you can do the following:

```sh
$ which python
/usr/bin/python
$ python -V
Python 2.7.13
```

On Windows you will need to install it by downloading it from [the offical website](https://www.python.org/downloads/windows/).

You will then need to install `PIP`, the official python package manager. To do this you would download
the [`get-pip.py`](https://bootstrap.pypa.io/get-pip.py) script and run it using the following command

```sh
$ python get-pip.py
```

The [`camio_hooks.py`](camio_hooks.py) and [`download_labels.py`](download_labels.py) scripts require that certain python modules
be installed on the system. All of these modules are listed in the [`requirements.txt`](requirements.txt) text file. You can install these using the `PIP` package manager by running the following from the `examples/batch_import` directory

```sh
$ pip install -r requirements.txt
Collecting requests (from -r requirements.txt (line 1))
  Downloading requests-2.14.2-py2.py3-none-any.whl (560kB)
    100% |████████████████████████████████| 563kB 539kB/s
Installing collected packages: requests
Successfully installed requests-2.14.2
```

#### Setting up the Environment

To use the [`camio_hooks.py`](camio_hooks.py) module properly, you must define some information specific to your Camio account. This information is defined through
the usage of environment variables. The required variable is:

| Variable | Description |
| -------- | ------------|
| `CAMIO_OAUTH_TOKEN` | set this to the Developer OAuth token that is generated from your [Camio settings](https://camio.com/settings/integrations#api) page. |

Environment variables are handled slightly differently on Windows systems than they are on OSX and Linux systems.

##### OSX / Linux

You can set environment variables by putting them in a file like `/home/$user/.bashrc` as:

```bash
# on OSX/Linux
$ export CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYZ" 
```

Then source the file by running:

```bash
$ source ~/.bashrc
```

If you don't want to set it permanently like this, you can also prepend the variable definition to the command that runs the video importer script; for example, 
where `$args` is a placeholder for the actual arguments you'd supply to the script, you would enter:

```bash
$ CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYZ" python import_video.py $args
```

##### Windows

```bat
C:\Users\user\examples\batch_import> set CAMIO_OAUTH_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ

C:\Users\user\examples\batch_import> set CAMIO_OAUTH_TOKEN
CAMIO_OAUTH_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

Once these environment variables are set, there are three more steps before you can start the import:
 
1. Get your [Camio Box](https://camio.com/box) (also available as [free VM](https://camio.com/box/vm)) running and registered under your account.
2. Obtain the IP address of your Camio Box. This will soon be displayed on the [/boxes](https://camio.com/boxes) page, but until then, please
use a network scanning tool like [Fing](https://help.camio.com/hc/en-us/articles/206214636) to find its IP address.
3. Create a regular expression for the importer's [`--regex`](https://github.com/tnc-ca-geo/video-importer#metadata-extraction-with---regex) argument that defines the capture groups for `camera_name` and `timestamp` extracted from the video filenames being imported.

#### Setting Camera-specific Data (plans, image resolution, etc)

There are two main ways to get data into the `camio_hooks.py` module from the import_video.py script.

1. Through the `--hook_data_json` argument. Supply this argument and then follow it up with a string representing a json object that contains the data needed to be passed in.
2. Through the `--hook_data_json_file` argument. Supply this argument and then the path to a file containing a string represeting a json object with the data needed to be passed to the hooks.

The structure of the JSON passed in should look something like this:

```json
{
    "plan": "plus",
    "cameras": {
        "camera_name_1": {
            "plan": "pro",
            "img_y_size_extraction": 1080,
            "img_x_size_cover": 1920,
            "img_y_size_cover": 1080,
            "img_x_size": 1280,
            "img_y_size": 720
        },
        "camera_name_2": {
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

Notice that you are able to specify values on both a per-camera and global basis.
The values inside the `cameras.{{camera_name}}` objects will apply only to those specific cameras.
The values at the top level will apply to all cameras that do not have their own values specified.

The values you can specify include:

1. `plan` - can be any of `basic`, `plus`, and `pro`. See https://www.camio.com/price for information on plans
2. `img_y_size_extraction` - the height of the frames extracted from the videos (before resizing!)
3. `img_x_size_cover` - the x size (in pixels) of the cover images.
4. `img_y_size_cover` - the y size (in pixels) of the cover images.
5. `img_x_size` - the x size (in pixels) of the non-cover images.
6. `img_y_size` - the y size (in pixels) of the non-cover images.

Note that if `img_y_size` or `img_y_size_cover` are larger than `img_y_size_extraction`, 
Camio will replace the value of `img_y_size_extraction` with the larger of the two other values.
This is because it doesn't make sense to extract at a lower resolution only to scale up.


#### Running `import_video.py` 

Now [run the video importer](https://github.com/tnc-ca-geo/video-importer#running-the-importer) with a command line that looks something like this:

```bash
$ python import_video.py \
  --regex ".*/(?P<camera>\w+?)\-(?P<epoch>\d+)\.mp4" \
  --hook_data_json_file ~/examples/batch_import/samples/sample_hook_data.json \
  ~/input_videos \
  ~/examples/batch_import/camio_hooks.py \
```

In the example above, the Camio Box receives the videos and:

1. analyzes the motion in each video to segment the video files into smaller events
2. creates metadata for each event that isolated real motion, color-blocking, direction of movement, etc...
3. submits selected events for advanced labeling via camio.com, which includes all registered labeling hooks

Upon completion of the import, all the resulting labeled events can be downloaded using the Camio [Search API](https://api.camio.com/#search).
The downloaded JSON includes the `camera_id`, `camera_name`, `earliest_date`, `latest_date` and `labels` for each event.

### Checking Job Status

Here is the full documentation for the [Jobs API](https://api.camio.com/#jobs). 
To get information about a specific job given a `job_id`, you would do the following.

GET https://www.camio.com/api/jobs/{{job_id}}`

Where `{{job_id}}` is the value returned returned from a `PUT` request to the `https://www.camio.com/api/jobs` endpoint. This `GET` request returns the following payload

```json
{
    "job_id": "agpIDYggsM",
    "request": {
        "device_id": "d123pdq",
        "item_count": 4099, 
        "item_average_size_bytes": 512, 
        "cameras":[
            {"name": "starboard"}
        ],
        "earliest_date":"2017-04-30T05:17:22.551-0700", 
        "latest_date": "2017-05-17T16:35:36.362-0700"
    },    
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

After batch-importing videos with the [`import_video.py`](batch_import/video-importer/import_video.py) script, you were returned a `job_id`. 
You can use this value along with the [`download_labels.py`](batch_import/download_labels.py) script to download a bookmark of all labels for all events that
were processed through the batch-import job.

To see how to use the script, you can enter the following into a shell from the `examples/batch_import/` directory.

```bash
python download_labels.py --help
```

Which will output the following:

```sh
$ python download_labels.py --help
usage: download_labels.py [-h] [-o OUTPUT_FILE] [-a ACCESS_TOKEN]
                          [-w LABEL_WHITE_LIST] [-f LABEL_WHITE_LIST_FILE]
                          [-c] [-x] [-t] [-v] [-q]
                          [job_id]

This script accepts a Camio job_id, finds the time-boundaries and cameras associated with that job,
and iterates over that time range while downloading all of the labels that Camio has assigned to those events.

If no `job_id` is submitted, this script will query all of the jobs you've created with your account, assemble them into
a json structure, and write that json structure to the file given by the `--output_file` argument.

positional arguments:
  job_id                the ID of the job that you wish to download the labels
                        for

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        full path to the output file where the resulting
                        labels will be stored in json format (default =
                        {{job_id}}_results.json)
  -a ACCESS_TOKEN, --access_token ACCESS_TOKEN
                        your Camio OAuth token (if not given we check the
                        CAMIO_OAUTH_TOKEN envvar)
  -w LABEL_WHITE_LIST, --label_white_list LABEL_WHITE_LIST
                        a json list of labels that are whitelisted to be
                        included in the response
  -f LABEL_WHITE_LIST_FILE, --label_white_list_file LABEL_WHITE_LIST_FILE
                        a file containing a json list of labels that are
                        whitelisted
  -c, --csv             (not implemented yet) set to export in CSV format
  -x, --xml             (not implemented yet) set to export in XML format
  -t, --testing         use Camio testing servers instead of production (for
                        dev use only!)
  -v, --verbose         set logging level to debug
  -q, --quiet           set logging level to errors only

Example:

    Here is an example of how to run the script to recover a dictionary of lables for the job with job_id=SjksdkjoowlkjlSDFiwjoijerSDRdsdf.
    This will obtain the bookmark of labels for the job and will write this output to the file /tmp/job_labels.json

    python download_labels.py --output_file /tmp/job_labels.json SjksdkjoowlkjlSDFiwjoijerSDRdsdf

    If you just want to list all jobs that belong to your account, you can do the followng

    python download_labels.py --output_file /tmp/job_list.json

    which will write the list of jobs that belong to the user to the file '/tmp/job_list.json'

```

This script accepts a `job_id`, queries the [Camio API](https://api.camio.com/#jobs) to get the job definition, then uses 
the job definition and the [Camio search API](https://api.camio.com/#search) to go through all events that belong to that job. While
going through all of these events, it assembles the labels into a json object and writes this object to the output file (which can be specified 
by you or simply defaults to `{{job_id}}_results.json`). This json object has the following structure

```json
{
  "job_id": "ag1zfmNhbWlvbG9nZ2VychALEgNKb2IYgIDI15PVuwgM",
  "latest_date": "2016-10-09T06:22:36.993000",
  "earliest_date": "2016-10-09T05:02:37.000"
  "labels": {
    "2016-10-09T05:10:31.456-0000": {
      "camera": {
        "name": "C2_Hi"
      },
      "labels": [
        "_color_white",
        "47390561bf685356557fc083c410914dc4b6fde6",
        "bluefin tuna",
        "human",
        "_color_green",
        "yellowfin tuna",
        "_ml_mail",
        "marlin",
        "_ml_human",
        "octopus",
        "_color_gray",
      ]
    },
    "2016-10-09T05:11:47.061-0000": {
      "camera": {
        "name": "C2_Hi"
      },
      "labels": [
        "_color_white",
        "47390561bf685356557fc083c410914dc4b6fde6",
        "human",
        "bluefin tuna",
        "bird",
        "_color_green",
        "yellowfin tuna",
        "_ml_mail",
        "_ml_human",
        "octopus",
        "_color_gray",
        "_ml_approaching"
      ]
    },
    "2016-10-09T05:09:13.788-0000": {
      "camera": {
        "name": "C2_Hi"
      },
      "labels": [
        "_ml_departing",
        "47390561bf685356557fc083c410914dc4b6fde6",
        "human",
        "_color_cyan",
        "_color_green",
        "yellowfin tuna",
        "_ml_mail",
        "_ml_human",
        "bird",
        "_ml_approaching"
      ]
    }
  },
}
```

