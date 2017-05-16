Batch Import Concrete Example
========================

### What's Needed

1. A registered Camio account
2. A Camio Box (either [physical](https://www.camio.com/box) or a [VM](https://www.camio.com/box/vm))
3. An OAuth token for your Camio account (gotten from [the integrations page](https://www.camio.com/settings/integrations/#api))
4. The Camio Box IP address (explained in the [get IP address section](#get-the-camio-box-ip-address))
5. A directory of videos that you wish to process through Camio
6. A regular-expression describing how to parse your input filenames ([described here](#constructing-the-file-parsing-regex))
7. Python Version 2.7 (installed by default on OSX and Linux, can be obtained from the [python website](https://www.python.org/downloads/windows/) for Windows)

Once you have all of the items listed above, you can start to batch-import videos to Camio.

### Instructions

#### Boot-Up Your Camio Box

Your Camio Box needs to be powered on, registered under your account, and on the same local network as the computer running the batch-importer script.
Your Camio Box can be registered through [the /box/register page](https://www.camio.com/box/register).

#### Clone the Importer and Use the Camio Hooks

Start by cloning the [Camio examples](https://www.github.com/CamioCam/examples) repository, go into the 
[examples/batch_import/video-importer](examples/batch_import/video-importer) directory. Then run the `setup.py` script
to install the package onto your system.

```sh
$ git clone https://www.github.com/CamioCam/examples
Cloning into 'examples'...
remote: Counting objects: 394, done.
remote: Compressing objects: 100% (127/127), done.
remote: Total 394 (delta 68), reused 0 (delta 0), pack-reused 267
Receiving objects: 100% (394/394), 87.31 KiB | 138.00 KiB/s, done.
Resolving deltas: 100% (218/218), done.
Checking connectivity... done.
$ git submodule update --init
Submodule 'batch_import/video-importer' (https://www.github.com/tnc-ca-geo/video-importer) registered for path 'batch_import/video-importer'
Cloning into '/private/tmp/examples/batch_import/video-importer'...
Submodule path 'batch_import/video-importer': checked out '79ef21f84697643824f6d31fb05699bc695d9135'
$ cd examples/batch_import/video-importer
$ pwd
/home/user/examples/batch_import/video-importer
$ ls -l
total 48
-rw-r--r--  1 user  staff  1062 May  1 15:32 LICENSE
-rw-r--r--  1 user  staff  7145 May  1 18:57 README.md
-rw-r--r--  1 user  staff  9408 May  1 18:57 import_video.py
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
| `CAMIO_BOX_DEVICE_ID` | set this to the `device_id` of the [Camio Box](https://camio.com/box) that's processing your imported video files. You can get your  `device_id` from your [/boxes](https://camio.com/boxes) page by looking for the `#device_id=XXX` URL hash parameter. Camio is adding an easier means to obtain the device ID but as of right now this is the easiest way to get it. |

You can set these by just entering the following in your shell

```sh
$ export CAMIO_OAUTH_TOKEN="qdSxve9OtdpPlcsyqzhzN95cYAE7A_P" # insert your oauth token here
$ export CAMIO_BOX_DEVICE_ID="Fgh5tmkbqAD6ba6CY7p2_dXRPIJsVFHASo4HrtY0-TELJPxb2B_7B2hBv3-zq98uh-sRoBVgaonxCMpi4CAmLkvmT0fz"
$ echo $CAMIO_OAUTH_TOKEN
qdSxve9OtdpPlcsyqzhzN95cYAE7A_P
$ echo $CAMIO_BOX_DEVICE_ID
Fgh5tmkbqAD6ba6CY7p2_dXRPIJsVFHASo4HrtY0-TELJPxb2B_7B2hBv3-zq98uh-sRoBVgaonxCMpi4CAmLkvmT0fz
```

#### Get the Camio Box IP Address

You need to know the local IP address of your Camio Box. You can do this in many ways but the two easiest are 
by using either the [`arp-scan` shell program](#using-arp-scan) or the [Fing phone](#using-the-fing-application) application. 
##### Using `arp-scan`

Get the `arp-scan` tool:

```sh
# arp-scan on OSX
brew install arp-scan

# arp-scan on Linux (Ubuntu)
sudo apt-get install arp-scan
```

Scan the network

You need to figure out what your network interface is, on OSX it is often `en0`, on Linux it's often `eth0` or `enp0s3`. You can check this
with the `route` tool:

**route On OSX**
```sh
$ route get example.com   
route to: 93.184.216.34
destination: default
       mask: default
    gateway: 192.168.1.1
  interface: en0 ## <--- this is the interface name ##
      flags: <UP,GATEWAY,DONE,STATIC,PRCLONING>
 recvpipe  sendpipe  ssthresh  rtt,msec    rttvar  hopcount      mtu     expire
       0         0         0         0         0         0      1500         0
```

**route On Linux**
```sh
$ route
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface 
default         192.168.1.1     0.0.0.0         UG    0      0        0 enp0s3 ## <-- this is the interface name
192.168.1.0     *               255.255.255.0   U     0      0        0 enp0s3
``` 

Then run the `arp-scan` tool (replace `eth0` with your interface name)
```sh
$ sudo arp-scan --interface=eth0 --localnet 
Interface: en0, datalink type: EN10MB (Ethernet)
Starting arp-scan 1.9 with 256 hosts (http://www.nta-monitor.com/tools/arp-scan/)
192.168.1.1    20:e5:2a:02:f6:fc    NETGEAR INC.,
192.168.1.10    28:10:7b:07:0c:51    D-Link International
192.168.1.20    b8:27:eb:a0:25:bc    Raspberry Pi Foundation
192.168.1.30    00:1e:06:33:d7:1a    WIBRAIN
192.168.1.51    be:fe:11:27:02:88    (Unknown)
# ....
```

Look for the entry with the MAC address of your Camio Box (for VMs this will start with `BE:FE:11`), and note down the IP address.

##### Using The Fing Application

Download the [Fing application](https://www.fing.io/) to your phone. Open the app and click the 'refresh' button on the top bar. This will kick off a scan
of the network, displaying all of the devices that it has located. Look through the list for the MAC address of your Camio Box and note down the IP address listed.


##### Constructing the File-Parsing Regex

For the sake of the example, let's say that your directory of video files for batch-import is located at `~/batch_videos/`, and the filesnames have the
format of 

```
$ ls ~/batch_videos
CAMERA_FRONT-rand-1475973147.mp4
CAMERA_FRONT-rand-1475973267.mp4
CAMERA_FRONT-rand-1475973350.mp4
```

Then you would use the following string as the regular expression passed to the video-import script.

`.*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4`

This captures the `CAMERA_FRONT` part as the camera name (used for registering the camera with Camio), and parses the `1475973147` part as the Unix-timestamp
of the video.

####  Running the video-importer Script

You are now ready to batch-import videos to Camio through your Camio Box. 

To start, go to the `video-importer` directory.

```sh
$ cd ~
$ cd examples/batch_import/video-importer
```

To see how the arguments are named/formatted/ordered as input to the scirpt you can always just give the `--help` flag to the script

```bash
$ python import_video.py --help
usage: import_video.py [-h] [-v] [-q] [-c] [-p PORT] [-r REGEX] [-s STORAGE]
                       [-d HOOK_DATA_JSON]
                       folder hook_module host

positional arguments:
  folder                full path to folder of input videos to process
  hook_module           full path to hook module for custom functions (a
                        python file)
  host                  the IP-address / hostname of the segmenter

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         set logging level to debug
  -q, --quiet           set logging level to errors only
  -c, --csv             dump csv log file
  -p PORT, --port PORT  the segmenter port number
  -r REGEX, --regex REGEX
                        regex to find camera name
                        (Default=".*/(?P<camera>.+?)/(?P<epoch>\d+(.\d+)?).*")
  -s STORAGE, --storage STORAGE
                        location of the local storage db
  -d HOOK_DATA_JSON, --hook_data_json HOOK_DATA_JSON
                        a json object containing extra information to be
                        passed to the hook-module
```

Run the importer with all of the values we've assembled in the previous steps.

```bash
$ python import_video.py \
  --regex ".*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4" \
  --host 192.168.1.57 \
  --port 8080 \
  --hook_data_json '{"plan": "basic"}' \
  "~/my-folder" \ # folder containing input videos
  "camio_hooks" \ # hooks module with callback functions
  "192.168.1.57"  # ip-address / hosntame of the segment server

INFO:root:submitted hooks module: '/Users/user/examples/batch_import/camio_hooks.py'
INFO:root:camera_name: CAMERA_FRONT
INFO:root:epoch: 1475973350
INFO:root:/Users/user/batch_videos/CAMERA_FRONT-rand-1475973350.mp4 (scheduled for upload)
INFO:root:1/1 uploading /Users/user/batch_videos/CAMERA_FRONT-rand-1475973350.mp4
INFO:root:completed
INFO:root:finishing up...
INFO:root:Job ID: agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKDIhYD4CQw
```

If you get any errors about missing the [`device_id`](#set-the-necessary-environment-variables) of the Camio Box or an unauthenticated error, try to set the environment variables again. To check that the environment variables
are currently set, you can always `echo $CAMIO_BOX_DEVICE_ID` or `echo $CAMIO_OAUTH_TOKEN` and check that the values printed out match what you expect.


#### Seeing the Imported Video

Once the script has completed sending videos to Box for segmentation and first-order analysis, the video clips will begin to 
be available to search through on [your Camio feed](https://www.camio.com/app/#search).
You can search for the name of the camera (that was parsed from the filenames) to see the videos that have been uploaded from that camera. 

Camio is currently writing some tools to help you recover all of the labels that were generated for the batch-imported videos, but this tool is not available yet. Camio is also designing tools and an API
that will allow you to check on the status of your video processing.
