Batch Import Concrete Example
========================

### What's Needed

1. A registered Camio account
2. A Camio Box (either [physical](https://www.camio.com/box) or a [VM](https://www.camio.com/box/vm))
3. An OAuth token for your Camio account (gotten from [the integrations page](https://www.camio.com/settings/integrations))
4. The Camio Box IP-address (explained in the [section](#get-the-camio-box-ip-address))
5. A directory of videos that you wish to process through Camio
6. A regular-expression describing how to parse your input videos ([described here](#constructing-the-file-parsing-regex))
7. Python Version 2.7 (installed by default on OSX and Linux, can be obtained from the [python website](https://www.python.org/downloads/windows/) for Windows)

Once you have all of the items listed above, you can start to batch-import videos to Camio

### Instructions

#### Boot-Up Your Camio Box

Your Camio Box needs to be powered on, registered under your account, and on the same local-network as the computer running the batch-importer script.
Your Camio Box can be registered through [the /box/register page](https://www.camio.com/box/register).

#### Obtain the video-import Script and the Camio-specific Hooks Code

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

For the video-import script to work properly with Camio and the [Camio Hooks](examples/batch_import/camio_hooks.py) module, a few environment 
variables must be defined. These are

| Variable | Description |
| -------- | ------------|
| `CAMIO_OAUTH_TOKEN` | set this to the Developer OAuth token that is generated from your [Camio settings](https://camio.com/settings/integrations#api) page. |
| `CAMIO_BOX_DEVICE_ID` | set this to the `device_id` of the [Camio Box](https://camio.com/box) that's processing your imported video files. You can get your  `device_id` from your [/boxes](https://camio.com/boxes) page. Until there's a more con

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

You need to know the local-IP address of your Camio Box. You can do this in many ways but the two easiest are 
by using either the [`arp-scan` shell program](#using-arp-scan) or the [Fing phone](#using-the-fing-application) application. 
##### Using `arp-scan`

Get the `arp-scan` tool:

```sh
# on OSX
brew install arp-scan

# on Linux (Ubuntu)
sudo apt-get install arp-scan
```

Scan the network

You need to figure out what your network interface is, on OSX it is often `en0`, on Linux it's often `eth0` or `enp0s3`. You can check this
with the `route` tool:

**On OSX**
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

**On Linux**
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

Download the [Fing application](https://www.fing.io/) to your phone. Open the app and click the 'refresh' button on the top bar. Ths will kick off a scan
of the network, displaying all of the devices that it has located. Look through the list for the MAC address of your Camio Box and note down the IP-address listed.


##### Constructing the File-Parsing Regex

For the sake of the example, let's say that your directory of video files for batch-import is located at `~/batch_videos/`, and the files have the
format of 

```
$ ls ~/batch_videos
CAMERA_FRONT-rand-1475973147.mp4
CAMERA_FRONT-rand-1475973267.mp4
CAMERA_FRONT-rand-1475973350.mp4
```

Then you would use the following string as the regular-expression passed to the video-import script.

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

Run the importer with all of the values we've assembled in the previous steps

```bash
$ python importer.py \
  --regex ".*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4" \
  --folder "~/batch_videos" \
  --host 192.168.1.57 \
  --hook_module "~/examples/batch_import/camio_hooks.py"

hooks module: '/Users/user/examples/batch_import/camio_hooks.py'
cwd: '/Users/user/examples/batch_import/video-importer'
camera_name: CAMERA_FRONT
epoch: 1475971347
INFO:root:/Users/user/natconv_test/CAMERA_FRONT-rand-1475971347.mp4 (scheduled for upload)
camera_name: CAMERA_FRONT
epoch: 1475971947
INFO:root:/Users/user/natconv_test/CAMERA_FRONT-rand-1475971947.mp4 (scheduled for upload)
camera_name: CAMERA_FRONT
epoch: 1475972547
INFO:root:/Users/user/natconv_test/CAMERA_FRONT-rand-1475972547.mp4 (scheduled for upload)
camera_name: CAMERA_FRONT
epoch: 1475973147
INFO:root:/Users/user/natconv_test/CAMERA_FRONT-003227-1475973147.mp4 (scheduled for upload)
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): test.camio.com
DEBUG:requests.packages.urllib3.connectionpool:https://test.camio.com:443 "POST /api/cameras/discovered HTTP/1.1" 200 3244
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): test.camio.com
DEBUG:requests.packages.urllib3.connectionpool:https://test.camio.com:443 "GET /api/cameras/discovered HTTP/1.1" 200 3402
Camera ID: u'109010722686218614620:C220161009:81219708c6fe2a5eb9cb35896b8ed78610ce9c6f'
INFO:root:1/4 uploading /Users/user/natconv_test/CAMERA_FRONT-rand-1475971347.mp4
Params: {'job_id': None, 'timestamp': '2016-10-08T17:02:27.000', 'uploaded_on': None, 'filename': '/Users/user/natconv_test/CAMERA_FRONT-rand-1475971347.mp4', 'shard_id': None, 'camera': 'CAMERA_FRONT', 'given_name': 'CAMERA_FRONT.2016-10-08T17:02:27.000.4b0bef93c8b4f6a26f5081630b8ad9fb87bb80e0.mp4', 'key': '4b0bef93c8b4f6a26f5081630b8ad9fb87bb80e0', 'discovered_on': '2017-05-05T12:59:12.476759', 'lat': None, 'lng': None, 'confirmed_on': None, 'size': 372157776}
DEBUG:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 192.168.1.13
INFO:root:completed
INFO:root:2/4 uploading /Users/john/natconv_test/CAMERA_FRONT-rand-1475971947.mp4
#  ....
INFO:root:completed
```

If you get any errors about missing the Device ID of the Camio Box or an unauthenticated error, try to set the environment variables again. To check that the environment variables
are currently set, you can always `echo $CAMIO_BOX_DEVICE_ID` or `echo $CAMIO_OAUTH_TOKEN` and check that the values printed out match what you expect.
