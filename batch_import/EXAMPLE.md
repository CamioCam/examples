Batch Import Concrete Example
========================

### What's Needed

1. A registered Camio account
2. A Camio Box (either [physical](https://www.camio.com/box) or a [VM](https://www.camio.com/box/vm))
3. An OAuth token for your Camio account (gotten from [here](https://www.camio.com/settings/integrations))
4. The Camio Box IP-address (explained in the [section](#get-the-camio-box-ip-address))
5. A directory of videos that you wish to process through Camio
6. A regular-expression describing how to parse your input videos ([described here](#constructing-the-file-parsing-regex))

Once you have all of the items listed above, you can start to batch-import videos to Camio

### Instructions

#### Boot-Up Your Camio Box

Your Camio Box needs to be powered on, registered under your account, and on the same local-network as the computer running the batch-importer script.
Your Camio Box can be registered through [here](https://www.camio.com/box/register).

#### Obtain the video-import Script and the Camio-specific Hooks Code

Start by cloning the [Camio examples](https://www.github.com/CamioCam/examples) repository, go into the 
[examples/batch_import/video-importer](examples/batch_import/video-importer) directory.

```sh
$ git clone https://www.github.com/CamioCam/examples
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

You can set these by just entering

```sh
export CAMIO_OAUTH_TOKEN="{{your_camio_oauth_token}}" # insert your oauth token here
export CAMIO_BOX_DEVICE_ID="{{device_id of your Camio Box}}"
```

#### Get the Camio Box IP Address

You need to know the local-IP address of your Camio Box. You can do this in many ways but the two easiest are listed below.

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
192.168.1.18    00:1e:06:33:d8:01    WIBRAIN
192.168.1.19    00:1e:06:33:a8:1a    WIBRAIN
192.168.1.20    b8:27:eb:a0:25:bc    Raspberry Pi Foundation
192.168.1.24    b8:27:eb:e0:97:6d    Raspberry Pi Foundation
192.168.1.26    98:ee:cb:48:c5:e1    (Unknown)
192.168.1.30    00:1e:06:33:d7:1a    WIBRAIN
# ....
```

Look for the entry with the MAC address of your Camio Box (for VMs this will start with `BE:FE:11`), and note down the IP address.

##### Using The Fing Application

Download the [Fing application](https://www.fing.io/) to your phone. Open the app and click the 'refresh' button on the top bar. Ths will kick off a scan
of the network, displaying all of the devices that it located. Look through the list for the MAC address of your Camio Box and note down the IP-address listed.


##### Constructing the File-Parsing Regex

For the sake of the example, let's say that your directory of video files for batch-import is located at `~/batch_videos/`, and the files have the
format of 

```
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

Run the importer

```bash
python importer.py \
  --regex ".*/(?P<camera>\w+?)\-.*\-(?P<epoch>\d+)\.mp4" \
  --folder "~/batch_videos" \
  --host 192.168.1.57 \
  --hook_module camio_hooks
```
