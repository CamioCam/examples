# Camio Hooks

## Introduction

Camio provides an image processing pipeline. Videos are uploaded to the Camio cloud from
any network camera/DVR/NVR/VMS via [Camio Box](https://camio.com/box). 
The Camio pipeline provides a labeling 
service but also allows you to register hooks to call your own labeling services.
A hook is a way to register a custom web service that can act on video events; for example,
a hook may call your service to compute labels derived from analysis of the images extracted from a video event.

As videos are uploaded to Camio, they are segmented into events,
which are classified as no-motion, boring, or interesting. 
Interesting events are classified by the Camio service and labeled.
The salient images are extracted from the video event. 
If you have registered a hook, and the event matches your hook's `parsed_query` filter, 
then the images belonging to the event are POSTed to your hook's `callback_url` in the form of a JSON payload. 
Your hook URL should record the JSON payload, decoded it, extract the images, label them, and then POST the labels back to 
the `callback_url` provided by the JSON payload of Camio's call to your service. 
The new labels computed by your service are then added to the video event.

Your hook labels an entire video event (not just a single image or video) based on the images and/or video in that event. 
A single event may contain mutiple images and multiple videos. The same video can span multiple consecutive events. 
Currently, Camio sends to your service only the preprocessed images. 
Also, Camio calls your hook service only on those events that Camio has already pre-filtered for you as interesting.

## Installing the example hook code

The provided code includes an installation script for Debian/Ubuntu 

   [hook-install.sh](hook-install.sh)

and an example of a hook:

   [hook-example.py](hook-example.py)

You can run the installation with the command:

```shell
   ./hook-install.sh
```

and it will install the required dependencies and start two processes:

1. a web server that received the hook calls and enqueues requests
2. a background process that handles the requests and posts back labels to Camio

The queue is implemented as a mongodb database collection.

## The example hook

This [hook-example.py](hook-example.py) depends on bottle (0.13), gunicorn, requests, PIL, and pymongo.

The hook-example.py code is build on bottle.py 0.13 and intended to work any WSGI web 
server. We recommend gunicorn (a prefork WSGI server) and the install script assumes it.
Once you have all the dependencies installed you can start the web server with:

```shell
    nohup gunicorn -w 2 app:hook-example -b 0.0.0.0:8000 > /tmp/gunicorn.log &
```

Here `8000` is the port to be used and `0.0.0.0` refers to the IP address of your hook server.
`-w 2` requests two web server workers and `/tmp/gunicorn.log` is the location of the logfile.

The server will expose three endpoints:

1. `GET http://{{your_domain}}:8000/tasks/` which you can call to check that the service is running
2. `POST http://{{your_domain}}:8000/tasks/{{api_key}}` which is the `callback_url` you [register](http://api.camio.com/#create-hook) with Camio to receive the POST of images to label
3. `GET http://{{your_domain}}:8000/tasks/{{api_key}}` which you can call to obtain a list of pending tasks

The `api_key` is your own API key and you can make it up to be whatever you want. It has to match the [`API_KEY`](hook-example.py#L21) 
global variable in the example code. The purpose of the `API_KEY` is to allow Camio to access to your hook while preventing unauthorized access.

Along with the web server you must start the background process:

```shell
    nohup python hook-example.py > /tmp/taskqueue.log &
```

The background process retrieves pending tasks collected by the hook and posts computed labels back to Camio. The labels will be added to the originating video event.

The [hook-example.py](hook-example.py) depends on the following function:

```python
    def compute_labels(images):
        labels = []
        for image in images:
            ...
        labels = ['cat','dog','mouse']
        return labels
```

This does nothing more than return the same three labels (cat, dog, mouse) for each 
event, but you can edit it to user your favorite ML or NN tool such as Caffe or Tensorflow,
to perform Object Detection and compute labels from the images.

## Registering the hook

Once you create a labeling server, you register it as a [Camio Hook](http://api.camio.com/#create-hook)
with the `POST` to camio.com.

This is a two step process:

1. Open [https://camio.com/settings/integrations#api](https://camio.com/settings/integrations#api) and 
  press the "Generate Token" button to obtain a "Developer OAuth Token".
2. Using curl or other tool, register your hook as described in [Create Hook](http://api.camio.com/#create-hook) with a command like:

```shell
    curl \
    -H "Content-Type: application/json" \
    -H "Authorization: token {{oauth_token}}" \
    -d '{"callback_url": "https://{{your_domain}}:8000/tasks/{{api_key}}", "type": "query_match", "parsed_query": "camera == '{{camera_name}}'"}
    -X POST https://www.camio.com/api/users/me/hooks
```

`https://{{your_domain}}:8000/tasks/{{api_key}}` is the location of your hook including the `api_key` you have selected (NOT the same as your develper `oauth_token`) and `parsed_query` is a string that will be used to filter which events to send to the service. In this example, only those events from the camera named 'camera_name' will trigger
the hook.

Please see [parsed_query conditions](https://api.camio.com/#parsed_query-conditions) for a full description of the Python conditional operators and variable names supported.

