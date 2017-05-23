Batch Import Concrete Example
========================

### Overview

See the [overview of video importing](/README.md#overview-of-video-importing) for a high level overview of the end-to-end video processing pipeline.

### What's Needed

1. A registered Camio account
2. A [batch-import-enabled Camio Box Virtual Machine](https://help.camio.com/hc/en-us/articles/115002492123)
3. An OAuth token for your Camio account (gotten from [the integrations page](https://www.camio.com/settings/integrations/#api))
4. [The testing directory of videos](https://storage.googleapis.com/camio_test_general/batch_import_video_files.zip)
5. A regular-expression describing how to parse your input filenames ([described here](#constructing-the-file-parsing-regex))
6. Python Version 2.7 (installed by default on OSX and Linux, can be obtained from the [python website](https://www.python.org/downloads/windows/) for Windows)
7. PIP (the Python Package Manager) is needed to download the required dependencies

Once you have all of the items listed above, you can start to batch-import videos to Camio.

### Instructions

#### Obtain and Set-up Your Batch-Import Enabled Camio Box

Follow all of the instructions listed in [this help article for setting up Camio Box VM in VirtualBox](https://help.camio.com/hc/en-us/articles/115002492123).

#### Boot-Up Your Camio Box

Your Camio Box needs to be powered on, registered under your account, and on the same local network as the computer running the batch-importer script.
Your Camio Box can be registered through [the /box/register page](https://www.camio.com/box/register).

#### Clone the Importer and Use the Camio Hooks

Start by cloning the [Camio examples](https://www.github.com/CamioCam/examples) repository, go into the 
[examples/batch_import/video-importer](examples/batch_import/video-importer) directory. Then run the `setup.py` script
to install the package onto your system.

```sh
$ git clone --recursive https://www.github.com/CamioCam/examples
Cloning into 'examples'...
remote: Counting objects: 764, done.
remote: Compressing objects: 100% (18/18), done.
remote: Total 764 (delta 8), reused 0 (delta 0), pack-reused 746
Receiving objects: 100% (764/764), 161.65 KiB | 0 bytes/s, done.
Resolving deltas: 100% (486/486), done.
Checking connectivity... done.
Submodule 'batch_import/video-importer' (https://www.github.com/tnc-ca-geo/video-importer) registered for path 'batch_import/video-importer'
Cloning into '/private/tmp/examples/batch_import/video-importer'...
Submodule path 'batch_import/video-importer': checked out '0b677c1d8c7f7cfca14896de8e1948080e942e17'
$ cd examples/batch_import/video-importer
$ pwd
/home/user/examples/batch_import/video-importer
$ ls -l
total 80
-rw-r--r--  1 john  staff   1062 May  1 15:32 LICENSE
-rw-r--r--  1 john  staff  10373 May 18 12:37 README.md
-rw-r--r--  1 john  staff   2555 May 18 12:37 hooks_template.py
-rw-r--r--  1 john  staff  15104 May 18 12:55 import_video.py
-rw-r--r--  1 john  staff    682 May 18 12:55 setup.py
$ python setup.py install
running install
running install_lib
running build_py
creating 'dist/import_video-0.1-py2.7.egg' and adding 'build/bdist.macosx-10.12-x86_64/egg' to it
Installing import_video script to /usr/local/bin
Installed /usr/local/lib/python2.7/site-packages/import_video-0.1-py2.7.egg
Processing dependencies for import-video==0.1
Searching for psutil==4.3.1
Best match: psutil 4.3.1
Adding psutil 4.3.1 to easy-install.pth file
# ... more output
Using /usr/local/lib/python2.7/site-packages
Finished processing dependencies for import-video==0.1
```

#### Set the Necessary Environment Variables

For the video-import script to work properly with Camio and the [camio_hooks.py](examples/batch_import/camio_hooks.py) module, a few environment 
variables must be defined. These are

| Variable | Description |
| -------- | ------------|
| `CAMIO_OAUTH_TOKEN` | set this to the Developer OAuth token that is generated from your [Camio settings](https://camio.com/settings/integrations#api) page. |

###### On OSX and Linux

You can set this by just entering the following in your shell

```sh
$ export CAMIO_OAUTH_TOKEN="qdSxve9OtdpPlcsyqzhzN95cYAE7A_P" # insert your oauth token here
$ echo $CAMIO_OAUTH_TOKEN
qdSxve9OtdpPlcsyqzhzN95cYAE7A_P
```

##### On Windows

```sh
set CAMIO_OAUTH_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ"

C:\Users\users\examples\batch_import> set CAMIO_OAUTH_TOKEN
CAMIO_OAUTH_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ
```


##### Get the Testing Videos

Camio supplies a [small directory of video files](https://storage.googleapis.com/camio_firmware_images/batch_import_video_files.zip) 
that you can use with the `import_video.py` program for testing purposes.  

You can either download them through your browser by click [this link](https://storage.googleapis.com/camio_firmware_images/batch_import_video_files.zip),
or you can do it with `curl` via a terminal by following the steps below.

```sh
$ cd ~
$ brew install curl
==> Downloading https://homebrew.bintray.com/bottles/curl-7.54.0.sierra.bottle.tar.gz
######################################################################## 100.0%
==> Pouring curl-7.54.0.sierra.bottle.tar.gz
==> Using the sandbox
==> Caveats
==> Summary
🍺  /usr/local/Cellar/curl/7.54.0: 392 files, 2.8MB
$ curl https://storage.googleapis.com/camio_test_general/batch_import_video_files.zip -o batch_import_video_files.zip
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  303M  100  303M    0     0  2233k      0  0:02:19  0:02:19 --:--:-- 1647k
$ unzip batch_import_video_files.zip
Archive:  batch_import_video_files.zip
   creating: input_videos/
  inflating: input_videos/office_street-camera-1495068758.mp4
  inflating: input_videos/office_street-camera-1495069946.mp4
```

You will now have a directory `input_videos` that contians the two files:

```
office_street-1495068758.mp4
office_street-1495069946.mp4
```

##### Constructing the File-Parsing Regex

You will be running the video-import script over a directory of video files. For this example we will assume you are using the example video files
[supplied by Camio](https://storage.googleapis.com/camio_test_general/batch_import_video_files.zip). Downloading and unzipping these files was described
in the [last section](#get-the-testing-videos)

As described in the previous section, you now have a directory `input_videos` that contians the two files:

```
office_street-1495068758.mp4
office_street-1495069946.mp4
```

Then you would use the following string as the regular expression passed to the video-import script.

`.*/(?P<camera>\w+?)\-(?P<epoch>\d+)\.mp4`

This captures the `office_street` part as the camera name (used for registering the camera with Camio), and parses the `1495068758` part as the Unix-timestamp
of the video.


#### Submitting Camera-Plan and Image-Resolution Data

There are two main ways to get data into the `camio_hooks.py` module from the video-import script.

1. `--hook_data_json` argument. Supply this argument and then follow it up with a string representing a json object that contains the data needed to be passed in.
2. `--hook_data_json_file` argument. Supply this argument and then the path to a file containing a string represeting a json object with the data needed to be passed to

The values you can specify (meaningfully) as of now are:

1. `plan` - can be any of `basic`, `plus`, and `pro`. See https://www.camio.com/price for information on plans
2. `img_y_size_extraction` - the height of the frames extracted from the videos (before resizing!)
3. `img_{x,y}_size_cover` - the x,y size (in pixels) of the cover-image after resizing.
4. `img_{x,y}_size` - the x,y size (in pixels) of the non-cover images after resizing.

Note that if `img_y_size` or `img_y_size_cover` are larger than `img_y_size_extraction` we will replace the value of `img_y_size_extraction` with the larger of the two other values.
This is because it doesn't make sense to extract at a lower resolution only to scale up.

In the [samples](/batch_import/samples/sample_hook_data.json) directory there is a sample json file that defines the plan as 'Pro' and the extraction and resizing parameters
to be high-definition.

```json
{
    "plan": "pro",
    "img_y_size_extraction": 1080,
    "img_x_size_cover": 1920,
    "img_y_size_cover": 1080
}
```

This file we will pass to the video-import script in a later step.


####  Running the video-importer Script

You are now ready to batch-import videos to Camio through your Camio Box. 

To start, go to the `video-importer` directory.

```sh
$ cd ~/examples/batch_import/video-importer
```

Run the importer with all of the values we've assembled in the previous steps.

```bash
$ python import_video.py \
  --regex ".*/(?P<camera>\w+?)\-(?P<epoch>\d+)\.mp4" \
  --hook_data_json_file ~/examples/batch_import/samples/sample_hook_data.json \
  ~/input_videos \
  ~/examples/batch_import/camio_hooks.py \
  "192.168.1.57"  

INFO:root:submitted hooks module: '/Users/user/examples/batch_import/camio_hooks.py'
INFO:root:camera_name: office_street
INFO:root:epoch: 1475973350
INFO:root:/Users/user/batch_videos/office_street-1475973350.mp4 (scheduled for upload)
INFO:root:1/1 uploading /Users/user/batch_videos/office_street-1475973350.mp4
INFO:root:completed
INFO:root:finishing up...
INFO:root:Job ID: agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw
```

*NOTE* - The `job_id` is returned in the last output line of the script ran above. Note down this value, you will need to give it to the [`download_labels.py`](batch_import/download_labels.py)
script in order to recover the dictionary of labels for all events discovered in the batch-import run you just finished.

If you get any errors about missing the [`device_id`](#set-the-necessary-environment-variables) of the Camio Box or an unauthenticated error, try to set the environment variables again. To check that the environment variables
are currently set, you can always `echo $CAMIO_BOX_DEVICE_ID` or `echo $CAMIO_OAUTH_TOKEN` and check that the values printed out match what you expect.


#### Seeing the Imported Video

Once the script has completed sending videos to Box for segmentation and first-order analysis, the video clips will begin to 
be available to search through on [your Camio feed](https://www.camio.com/app/#search).
You can search for the name of the camera (that was parsed from the filenames) to see the videos that have been uploaded from that camera. 

Camio is currently writing some tools to help you recover all of the labels that were generated for the batch-imported videos, but this tool is not available yet. Camio is also designing tools and an API
that will allow you to check on the status of your video processing.

#### Gathering the Labels

After batch-importing videos with the [`import_video.py`](batch_import/video-importer/import_video.py) script, you were returned a job ID. 
You can use this value along with the [`download_labels.py](batch_import/download_labels.py) script to download a bookmark of all labels for all events that
were processed through the batch-import job.


To see how to use the script, you can enter the following into a shell from the `examples/batch_import/` directory.

```bash
python download_labels.py --help
```

Which will output the following:

```sh
$ python download_labels.py --help
usage: download_labels.py [-h] [-a ACCESS_TOKEN] [-c] [-x] [-t] [-v] [-q]
                         [job_id] [output_file]
```

To gather your labels into the file `/home/user/mylabels.json`, you would run the following (assuming the `job_id` is `agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw` as returned from the example above).

```sh
$ python download_labels.py agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw /home/user/mylabels.json
INFO:root:Job Definition:
INFO:root:  earliest date: u'2017-05-17T13:07:36.000', latest date: u'2017-05-17T13:17:36.120000'
INFO:root:  cameras included in inquiry: [u'office_street']
INFO:root:gathering over time slot: '2017-05-17T13:07:36' to '2017-05-17T13:17:36'
INFO:root:gathering over time slot: '2017-05-17T13:17:36' to '2017-05-17T13:27:36'
INFO:root:finished gathering labels
INFO:root:writing label info to file: /home/user/mylabels.json
INFO:root:labels are now available in: /home/user/mylabels.json
```

Now if you go and look at the output file (`/home/user/mylabels.json`), it will look something like this.

```json
{
  "job_id": "agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw",
  "latest_date": "2016-10-08T17:42:26.771000",
  "earliest_date": "2016-10-08T17:02:27.000",
  "labels": {
    "2016-10-08T17:30:56.715-0000": {
      "camera": {
        "name": "C2_Hi20161009"
      },
      "labels": [
        "b60d4781f4a42649c9734d77af71d5aa4f047ff9",
        "_color_orange",
        "_color_gray",
        "_color_red"
      ]
    },
    "2016-10-08T17:22:07.674-0000": {
      "camera": {
        "name": "C2_Hi20161009"
      },
      "labels": [
        "_color_black",
        "window",
        "tire",
        "_color_gray",
        "00973fb80d5205ccaf76182ee2cc0bc44f057bf5"
      ]
    },
    "2016-10-08T17:41:49.294-0000": {
      "camera": {
        "name": "C2_Hi20161009"
      },
      "labels": [
        "806f3186880404b7d37a75802e59fae18c677671",
        "_ml_mail",
        "_color_black",
        "_ml_human",
        "_color_blue",
        "_color_gray",
        "_ml_approaching"
      ]
    },
    "2016-10-08T17:20:48.254-0000": {
      "camera": {
        "name": "C2_Hi20161009"
      },
      "labels": [
        "_color_black",
        "00973fb80d5205ccaf76182ee2cc0bc44f057bf5"
      ]
    },
    "2016-10-08T17:39:36.374-0000": {
      "camera": {
        "name": "C2_Hi20161009"
      },
      "labels": []
    },
    "2016-10-08T17:37:59.741-0000": {
      "camera": {
        "name": "C2_Hi20161009"
      },
      "labels": []
    },
}
```
