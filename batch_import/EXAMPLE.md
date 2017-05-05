Batch Import Concrete Example
========================

### What's Needed

1. A registered Camio account
2. A Camio Box (either [physical](https://www.camio.com/box) or a [VM](https://www.camio.com/box/vm))
3. An OAuth token for your Camio account (gotten from [here](https://www.camio.com/settings/integrations))
4. A directory of videos that you wish to process through Camio

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
export CAMIO_OAUTH_TOKEN="{{your_camio_oauth_token}} # insert your oauth token here
export CAMIO_BOX_DEVICE_ID="{{device_id of your Camio Box}}
```
