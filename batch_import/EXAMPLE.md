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
[examples/batch_import/video-importer](examples/batch_import/video-importer) directory.

```sh
$ git clone https://www.github.com/CamioCam/examples
Cloning into 'examples'...
remote: Counting objects: 394, done.
remote: Compressing objects: 100% (127/127), done.
remote: Total 394 (delta 68), reused 0 (delta 0), pack-reused 267
Receiving objects: 100% (394/394), 87.31 KiB | 138.00 KiB/s, done.
Resolving deltas: 100% (218/218), done.
Checking connectivity... done.
$ cd examples/batch_import/video-importer
$ pwd
/home/user/examples/batch_import/video-importer
$ ls -l
total 48
-rw-r--r--  1 user  staff  1062 May  1 15:32 LICENSE
-rw-r--r--  1 user  staff  7145 May  1 18:57 README.md
-rw-r--r--  1 user  staff  9408 May  1 18:57 importer.py

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

Run the importer with all of the values we've assembled in the previous steps.

```bash
$ python importer.py -v \
  --folder ~/batch_videos/ \
  --host 192.168.1.51 \
  --hook_module ~/examples/batch_import/camio_hooks.py 
  --regex ".*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4"
  --hook_data_json '{"plan": "plus"}'

INFO:root:submitted hooks module: '/Users/user/examples/batch_import/camio_hooks.py'
DEBUG:root:setting camio_hooks data as:
{'logger': <module 'logging' from '/usr/local/lib/python/2.7.13/lib/python2.7/logging/__init__.pyc'>, u'plan': u'plus'}
INFO:root:camera_name: C2_Hi20161009
INFO:root:epoch: 1476018757
INFO:root:/Users/user/batch_videos/CAMERA_FRONT-rand-1475973147.mp4 (scheduled for upload)
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): test.camio.com
DEBUG:requests.packages.urllib3.connectionpool:https://test.camio.com:443 "POST /api/cameras/discovered HTTP/1.1" 200 33548
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): test.camio.com
DEBUG:requests.packages.urllib3.connectionpool:https://test.camio.com:443 "GET /api/cameras/discovered HTTP/1.1" 200 37221
DEBUG:root:Camera ID: u'ABD07226DFG218614620:CAMERA_FRONT:81219708c6fe2a5eb9cb35896b8ed78610ce9c6f'
DEBUG:root:assigning job id: [{'job_id': None, 'timestamp': '2016-10-09T06:12:37.000', 'uploaded_on': None, 'filename': '/Users/user/batch_videos/C2_Hi20161009-131237-1476018757.mp4', 'shard_id': None, 'camera': 'C2_Hi20161009', 'given_name': 'C2_Hi20161009.2016-10-09T06:12:37.000.3385bfc912590c2521d829524a7d2136fae517f3.mp4', 'key': '3385bfc912590c2521d829524a7d2136fae517f3', 'discovered_on': '2017-05-11T18:00:14.229431', 'lat': None, 'lng': None, 'confirmed_on': None, 'size': 125297958}]
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): test.camio.com
DEBUG:requests.packages.urllib3.connectionpool:https://test.camio.com:443 "PUT /api/jobs HTTP/1.1" 200 575
DEBUG:root:upload item: 1
DEBUG:root:len(unscheduled)=1
INFO:root:1/1 uploading /Users/user/batch_videos/C2_Hi20161009-131237-1476018757.mp4
INFO:root:input-file /Users/user/batch_videos/C2_Hi20161009-131237-1476018757.mp4 has been renamed C2_Hi20161009.2016-10-09T06:12:37.000.3385bfc912590c2521d829524a7d2136fae517f3.mp4
DEBUG:root:Params: {'job_id': u'lkSSSNhbWlvL443RyEAsSA0pvYhiAgKCIoeaACgw', 'timestamp': '2016-10-09T06:12:37.000', 'uploaded_on': None, 'filename': '/Users/user/batch_videos/C2_Hi20161009-131237-1476018757.mp4', 'shard_id': u'0', 'camera': 'C2_Hi20161009', 'given_name': 'C2_Hi20161009.2016-10-09T06:12:37.000.3385bfc912590c2521d829524a7d2136fae517f3.mp4', 'key': '3385bfc912590c2521d829524a7d2136fae517f3', 'discovered_on': '2017-05-11T18:00:14.229431', 'lat': None, 'lng': None, 'upload_url': u'https://storage.googleapis.com/camio_test_mr_output/bij-agxzfmNhbWlvLXRlc3RyEAsSA0pvYhiAgKCIoeaACgw-0?GoogleAccessId=397790679937@developer.gserviceaccount.com&Expires=1494552017&Signature=J0WIg9QDbDsKwUPyrsCbqAs2aFf34V%2BacINp9p0wvt1dZSTb%2BadEsZ1QsqkDTNC6n5%2FHUExuVcXTNkq1GT%2BPEPY9RyzMwEkUYr2CT7Ctkmai7SqQ0GiRdZx5DUTVht77huEGYh6Ypt3YJouzoPLZIRoWTmR3kW4CQ1h%2BpzOAsxU%3D', 'confirmed_on': None, 'size': 125297958}
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 192.168.1.13
DEBUG:requests.packages.urllib3.connectionpool:http://192.168.1.13:8080 "POST /box/content?access_token=SDFW33WlFgtSyEyXnRh8wiEYJZEdsT26mdiH7Kj2B_73-sRoBVgaonxCMpi4CAmLkvOSD8223&local_camera_id=81219708c6fe2a5eb9cb35896b8ed78610ce9c6f&camera_id=109010722686218614620:C220161009:81219708c6fe2a5eb9cb35896b8ed78610ce9c6f&hash=646c65289f24f26577912ea1deac8f6b26a847be&timestamp=2016-10-09T06:12:37.000 HTTP/1.1" 204 0
INFO:root:completed
DEBUG:root:registering jobs: set([(u'lkSSSNhbWlvL443RyEAsSA0pvYhiAgKCIoeaACgw', u'0')])
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): storage.googleapis.com
DEBUG:requests.packages.urllib3.connectionpool:https://storage.googleapis.com:443 "PUT /camio_test_mr_output/bij-SDFzfmNhbW234FSDwsssvYhiAgKCIoeaACgw-0?GoogleAccessId=984550679937@developer.gserviceaccount.com&Expires=1494552017&Signature=J0WIg9QDbDsKwUPyrsCbqAs2aFf34V%2BacINp9p0wvt1dZSTb%2BadEsZ1QsqkDTNC6n5%2FHUExuVcXTNkq1GT%2BPEPY9RyzMwEkUYr2CT7Ctkmai7SqQ0GiRdZx5DUTVht77huEGYh6Ypt3YJouzoPLZIRoWTmR3kW4CQ1h%2BpzOAsxU%3D HTTP/1.1" 200 0
```

If you get any errors about missing the [`device_id`](#set-the-necessary-environment-variables) of the Camio Box or an unauthenticated error, try to set the environment variables again. To check that the environment variables
are currently set, you can always `echo $CAMIO_BOX_DEVICE_ID` or `echo $CAMIO_OAUTH_TOKEN` and check that the values printed out match what you expect.


#### Seeing the Imported Video

Once the script has completed sending videos to Box for segmentation and first-order analysis, the video clips will begin to 
be available to search through on [your Camio feed](https://www.camio.com/app/#search).
You can search for the name of the camera (that was parsed from the filenames) to see the videos that have been uploaded from that camera. 

Camio is currently writing some tools to help you recover all of the labels that were generated for the batch-imported videos, but this tool is not available yet. Camio is also designing tools and an API
that will allow you to check on the status of your video processing.
