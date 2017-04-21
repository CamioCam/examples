Importing Video Files in Bulk
===============

## Using the [Video Importer](https://github.com/tnc-ca-geo/video-importer) with Camio Box

The open source [video importer](https://github.com/tnc-ca-geo/video-importer) includes a hook to specify 
Camio Box as the services that segments and labels the video files imported from a directory.

Specify the [`camio_hooks.py`](camio_hooks.py) module as the value for 
the [`--hooks_module` argument of the video importer](https://github.com/tnc-ca-geo/video-importer#hook-module).
The video importer calls the [`register_camera`](https://github.com/tnc-ca-geo/video-importer#camera-registration-function) 
and [`post_video_content`](https://github.com/tnc-ca-geo/video-importer#post-video-content-function) functions that take care 
of processing the video with the Camio services.


####  Setting up the Environment

To use the [`camio_hooks.py`](camio_hooks.py) module, you first must define some environment variables for yourself. These variables are:

| Variable | Description |
| -------- | ------------|
| `CAMIO_OAUTH_TOKEN` | set this to the Developer OAuth token that is generated from your [Camio settings](https://camio.com/settings/integrations#api) page. |
| `CAMIO_BOX_DEVICE_ID` | set this to the `device_id` of the [Camio Box](https://camio.com/box) that's processing your imported video files. You can get
your `device_id` from your [/boxes](https://camio.com/boxes) page. Until there's a more convenient way to copy and paste your `device_id`, please copy it
from the URL hash parameter `device_id` that's shown in your browser's address bar on that page. |


You can set environment variables by putting them in a file like `/home/$user/.bashrc` as `export CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYX"`, then sourcing the file by running `source ~/.bashrc`. 
If you don't want to set them permanently like this, you can also prepend the variable definitions to the command that runs the video importer script; for example, where `$args` is a placeholder for the actual arguments you'd supply to the script, you would enter:

```bash
CAMIO_OAUTH_TOKEN="ABCDEFGHIJKLMNOPQRSTUVWXYZ" CAMIO_BOX_DEVICE_ID="sdfsdfsdfsdfsdfsdfsdf" python importer.py $args
```

Once these environment variables are set, there are three more steps before you can start the import:
 
1. Get your [Camio Box](https://camio.com/box) (also available as [free VM](https://camio.com/box/vm)) running and registered under your account.
2. Obtain the IP address of your Camio Box. This will soon be displayed on the [/boxes](https://camio.com/boxes) page, but until then, please
use a network scanning tool like [Fing](https://help.camio.com/hc/en-us/articles/206214636) to find its IP address.
3. Create a [regular expression for the importer's `--regex` argument](https://github.com/tnc-ca-geo/video-importer#metadata-extraction-with---regex) that defines the capture groups for `camera_name` and `timestamp` extracted from the video filenames being imported.


