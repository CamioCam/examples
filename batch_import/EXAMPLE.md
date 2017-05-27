Batch Import Concrete Example
========================

### Overview

See the [overview of video importing](/README.md#overview-of-video-importing) for a high level overview of the end-to-end video processing pipeline.

### What's Needed

1. A registered Camio account
2. A [batch-import-enabled Camio Box Virtual Machine](https://help.camio.com/hc/en-us/articles/115000667046)
3. An OAuth token for your Camio account (gotten from [the integrations page](https://www.camio.com/settings/integrations/#api))
4. [The testing directory of videos provided by Camio](https://storage.googleapis.com/camio_test_general/video_importer_test_files.zip)
5. A regular-expression describing how to parse your input filenames ([described here](#constructing-the-file-parsing-regex))
6. Python Version 2.7 (installed by default on OSX and Linux, can be obtained from the [python website](https://www.python.org/downloads/windows/) for Windows)
7. PIP (the Python Package Manager) is needed to install the required dependencies

Once you have all of the items listed above, you can start to batch-import videos to Camio.

### Instructions

#### Obtain and Set-up Your Batch-Import Enabled Camio Box

Follow all of the instructions listed in [this help article for setting up Camio Box VM in VirtualBox](https://help.camio.com/hc/en-us/articles/115002492123).

#### Boot-Up Your Camio Box

Your Camio Box needs to be powered on, registered under your account, and on the same local network as the computer running the batch-importer script.
Your Camio Box can be registered through [the /box/register page](https://www.camio.com/box/register).

#### Clone the Importer and Use the Camio Hooks

Start by cloning the [Camio examples](https://www.github.com/CamioCam/examples) repository, go into the 
[examples/batch_import/video-importer](/examples/batch_import/video-importer) directory. Then run the `setup.py` script
to install the package onto your system.

```sh
# clone the repo to get the code
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

# install the dependencies for camio_hooks.py
$ cd examples/batch_import
$ pip install -r requirements.txt # sudo required for OSX/Linux
Collecting requests (from -r requirements.txt (line 1))
  Downloading requests-2.14.2-py2.py3-none-any.whl (560kB)
    100% |████████████████████████████████| 563kB 538kB/s
Collecting python-dateutil (from -r requirements.txt (line 2))
  Downloading python_dateutil-2.6.0-py2.py3-none-any.whl (194kB)
    100% |████████████████████████████████| 194kB 1.4MB/s
Requirement already satisfied: six>=1.5 in /usr/lib/python2.7/dist-packages (from python-dateutil->-r requirements.txt (line 2))
Installing collected packages: requests, python-dateutil
Successfully installed python-dateutil-2.6.0 requests-2.14.2

# install the video importer onto the system
$ cd examples/batch_import/video-importer
$ pwd
/home/user/examples/batch_import/video-importer
$ ls -l
total 80
-rw-r--r--  1 user  staff   1062 May  1 15:32 LICENSE
-rw-r--r--  1 user  staff  10373 May 18 12:37 README.md
-rw-r--r--  1 user  staff   2555 May 18 12:37 hooks_template.py
-rw-r--r--  1 user  staff  15104 May 18 12:55 import_video.py
-rw-r--r--  1 user  staff    682 May 18 12:55 setup.py
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
set CAMIO_OAUTH_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ

C:\Users\users\examples\batch_import> set CAMIO_OAUTH_TOKEN
CAMIO_OAUTH_TOKEN=ABCDEFGHIJKLMNOPQRSTUVWXYZ
```


##### Get the Testing Videos

Camio supplies a [small directory of video files](https://storage.googleapis.com/camio_test_general/video_importer_test_files.zip) 
that you can use with the `import_video.py` program for testing purposes.  

You can either download them through your browser by clicking [this link](https://storage.googleapis.com/camio_test_general/video_importer_test_files.zip),
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
$ curl https://storage.googleapis.com/camio_test_general/video_importer_test_files.zip -o video_importer_test_files.zip
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
 13  236M   13 30.8M    0     0  3576k      0  0:01:07  0:00:08  0:00:59 3747k
$ unzip video_importer_test_files.zip
Archive:  video_importer_test_files.zip
   creating: video_importer_test_files/
  inflating: video_importer_test_files/C2_Hi20161009-120237-1476014557.mp4
  inflating: video_importer_test_files/C2_Hi20161009-131237-1476018757.mp4
```

You will now have a directory `video_importer_test_files` that contians the two files:

```
C2_Hi20161009-120237-1476014557.mp4 
C2_Hi20161009-131237-1476018757.mp4
```

##### Constructing the File-Parsing Regex

You will be running the video-import script over a directory of video files. For this example we will assume you are using the example video files
[supplied by Camio](https://storage.googleapis.com/camio_test_general/video_importer_test_files.zip). Downloading and unzipping these files was described
in the [last section](#get-the-testing-videos).

As described in the previous section, you now have a directory `video_importer_test_files` that contians the two files:

```
C2_Hi20161009-120237-1476014557.mp4 
C2_Hi20161009-131237-1476018757.mp4
```

Then you would use the following string as the regular expression passed to the video-import script.

* On Linux and OSX *

`".*/(?P<camera>.*_\D+)\d+\-.*\-(?P<epoch>\d+)\.mp4"`

* On Windows *

`".*[\\](?P<camera>.*_\D+)\d+\-.*\-(?P<epoch>\d+)\.mp4"`

This captures the `C2_Hi` part as the camera name (used for registering the camera with Camio), and parses the `1476014557` part as the Unix-timestamp
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

Note that if `img_y_size` or `img_y_size_cover` are larger than `img_y_size_extraction` we will replace the value 
of `img_y_size_extraction` with the larger of the two other values. This is because it doesn't make sense to 
extract at a lower resolution only to scale up.

In the [samples](/batch_import/samples) directory there is a [sample_hook_data.json](/batch_import/samples/sample_hook_data.json) 
file that defines the plan as 'Pro' and the extraction and resizing parameters
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

#### Using the Example Hook Service

Camio has set up a demo hook service that you can use as a proof-of-concept for other labeling services. This hook service simply returns a random list
of labels from the set [cat, dog, mouse, pasta, tortilla, monkey, cheeto, hippo, leviathan]. 

The example hook server is sitting at http://104.198.98.243 on port 8080, and the path to the hook endpoint is `/tasks/batch-import-test`. You must also submit a query
for the hook to be applied over, in this case the easiest query to give is  `"1==1"`, which means the hook will run on all events uploaded.

Note that this script also depends on the `CAMIO_OAUTH_TOKEN` environment variable being set in order to authenticate it as your account.

To register this hook to your account run the following in your shell

```bash
$ cd ~/examples/hooks # go to your examples directory, then to the hooks directory
$ bash hook-register.sh "http://104.198.98.243:8080/tasks/batch-import-test" "1==1"
Note: Unnecessary use of -X or --request, POST is already inferred.
*   Trying 216.239.38.21...
* Connected to camio.com (216.239.38.21) port 443 (#0)
* TLS 1.2 connection using TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
* Server certificate: *.camio.com
* Server certificate: DigiCert SHA2 Secure Server CA
* Server certificate: DigiCert Global Root CA
> POST /api/users/me/hooks HTTP/1.1
> Host: camio.com
> User-Agent: curl/7.49.1
> Accept: */*
> Content-Type: application/json
> Authorization: token zTiruJf-zL6dPQSb-mzHrgzGuiY40d7G
> Content-Length: 117
>
* upload completely sent off: 117 out of 117 bytes
< HTTP/1.1 200 OK
< Expires: Thu, 01 Jan 1970 00:00:00 GMT
< Set-Cookie: JSESSIONID=ozJ7lu-l3KOxlcgOCKsvzA;Path=/
< Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH
< Content-Type: application/json; charset=UTF-8
< X-Cloud-Trace-Context: 5fe0397617bfac498481b45a111fcfbb
< Date: Sat, 27 May 2017 00:47:36 GMT
< Server: Google Frontend
< Content-Length: 176
< Cache-Control: private
<
* Connection #0 to host camio.com left intact
{"id":"ag1zfmNhbWlvbG9nZ2VychELEgRIb29rGICAyLf_1ZcLDA","type":"query_match","parsed_query":"1\u003d\u003d1","callback_url":"http://104.198.98.243:8080/tasks/batch-import-test"}
```

The output returned from this call will include the hook ID and some other information about the hook. If you see the output listed above it means the hook registered succesfully,
and you should see random subsets of the labels listed above showing up in your bookmark of labels that is downloaded after a job is complete.


####  Running the video-importer Script

You are now ready to batch-import videos to Camio through your Camio Box. 

To start, go to the `video-importer` directory.

```sh
$ cd ~/examples/batch_import/video-importer
```

Run the importer with all of the values we've assembled in the previous steps.

```bash
$ python import_video.py  \
 --hook_data_json_file ../samples/sample_hook_data.json \
 --regex ".*/(?P<camera>.*_\D+)\d+\-.*\-(?P<epoch>\d+)\.mp4" \
 ~/video_importer_test_files/ ../camio_hooks.py
   INFO - import_video.py:       init_args:108:   submitted hooks module: '../camio_hooks.py'
   INFO - import_video.py:      get_params:139:   camera_name: C2_Hi
   INFO - import_video.py:      get_params:143:   epoch: 1476014557
   INFO - import_video.py:   upload_folder:229:   /Users/john/video_importer_test_files/C2_Hi20161009-120237-1476014557.mp4 (scheduled for upload)
   INFO - import_video.py:      get_params:139:   camera_name: C2_Hi
   INFO - import_video.py:      get_params:143:   epoch: 1476018757
   INFO - import_video.py:   upload_folder:229:   /Users/john/video_importer_test_files/C2_Hi20161009-131237-1476018757.mp4 (scheduled for upload)

Multiple Camio Box devices belong to your account. Please select the one you wish to use
1. homevmware2.0
2. BoxVM-Office-Windows-20170413.0
3. CamioBox_VBOX_Office.20170518.0

3
   INFO -  camio_hooks.py:get_account_info:116:   You have selected Camio Box: CamioBox_VBOX_Office.20170518.0
   INFO -  camio_hooks.py: register_camera:272:   registering camera: name=C2_Hi, local_camera_id=5f72bf2d11034854c0ff34ff54b8b0b74b138e50
   INFO - import_video.py:   upload_folder:278:   1/2 uploading /Users/john/video_importer_test_files/C2_Hi20161009-120237-1476014557.mp4
   INFO - import_video.py:   upload_folder:285:   completed
   INFO - import_video.py:   upload_folder:278:   2/2 uploading /Users/john/video_importer_test_files/C2_Hi20161009-131237-1476018757.mp4
   INFO - import_video.py:   upload_folder:285:   completed
   INFO - import_video.py:            main:358:   finishing up...
   INFO - import_video.py:            main:360:   Job ID: ag1zfmNhbWlvbG9nZ2VychALEgNKb2IYgIDIt9LVyQoM
```

*NOTE* - The `job_id` is returned in the last output line of the script ran above. Note down this value, you need to give it to the [`download_labels.py`](batch_import/download_labels.py)
script in order to recover the dictionary of labels for all events discovered in the batch-import run you just finished.

#### Seeing the Imported Video

Once the script has completed sending videos to Box for segmentation and first-order analysis, the video clips will begin to 
be available to search through on [your Camio feed](https://www.camio.com/app/#search).
You can search for the name of the camera (that was parsed from the filenames) to see the videos that have been uploaded from that camera. 

#### Gathering the Labels

After batch-importing videos with the [`import_video.py`](batch_import/video-importer/import_video.py) script, you were returned a `job_id`.
You can use this value along with the [`download_labels.py](batch_import/download_labels.py) script to download a bookmark of all labels for all events that
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
```

To gather your labels into the file `/home/user/mylabels.json`, you would run the following (assuming the `job_id` is `agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw` as returned from the example above).

```sh
$ python download_labels.py agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw /home/user/mylabels.json
INFO:root:Job Definition:
INFO:root:  earliest date: u'2016-10-09T05:02:37.000', latest date: u'2016-10-09T06:22:36.993000'
INFO:root:  cameras included in inquiry: C2_Hi
INFO:root:gathering over time slot: '2016-10-09T05:02:37' to '2016-10-09T06:22:36.993000'
INFO:root:results gathered, new starting time: '2016-10-09T06:22:35.930000+00:00'
INFO:root:results gathered, new starting time: '2016-10-09T06:22:35.930000+00:00'
INFO:root:finished gathering labels
INFO:root:writing label info to file: samples/sample_hook_data.json
INFO:root:labels are now available in: samples/sample_hook_data.json
```

Now if you go and look at the output file (`/home/user/mylabels.json`), it will look something like this.

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
