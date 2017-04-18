#!/usr/bin/env python

import requests
import re
import json
import hashlib

"""
Camio-specific hook examples for use with the video import script
"""

CAMIO_REGISTER_URL="https://www.camio.com/api/cameras/discovered"
CAMIO_REGISTER_URL_TEST="https://test.camio.com/api/cameras/discovered"

def get_access_token():
    return None # @TODO - grab access token from env vars

def get_user_id():
    return None # @TODO - grab userID from env vars

def hash_file_in_chunks(fh, chunksize=65536):
    """ get the SHA1 of $filename but by reading it in $chunksize at a time to not keep the
    entire file in memory (these can be large files) """
    sha1 = hashlib.sha1()
    while True:
        data = fh.read(chunksize)
        if not data:
            break
        sha1.update(data)
    return sha1.hexdigest()

def get_device_data(host, port):
    """ 
    calls the /box/settings endpoint to get (Device_id, user-agent) pair that is needed
    to register a camera properly
    """
    urlbase = "%s:%s" % (host, port)
    url = urlbase + "/box/content"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def register_camera(camera_name, host=None, port=None, latlong=None):
    """
    arguments:
        camera_name   - the name of the camera (as parsed from the filename) 
        latlong (opt) - the lat/long of the camera (as parsed from the filename)
        host          - the URI/IP address of the segmenter being used
        port          - the port to access the webserver of the segmenter
    returns: this function returns the Camio-specific camera ID.
                 
    description: this function is called when a new camera is found by the import script, 
                 if a camera needs to be registered with a service before content from that
                 camera can be segmented then the logic for registering the camera should 
                 exist in this function.
                 For Camio, this function POSTs to /api/cameras/discovered with the new camera
                 entry. It is required that the "acquisition_method": "batch" set in the camera 
                 config for it to be known as a batch-import source as opposed to a real-time 
                 input source.

    NOTE - the json payload is given as follows
    {
	"$localcameraid": {
	"device_id_discovering": "$deviceid",
	"acquisition_method": "batch",
	"discovery_history": {},
	"device_user_agent": "CamioBox (Linux; virtualbox)",
	"user_id": "$userid",
	"local_camera_id": "$localcameraid",
	"name": "$cameraname",
	"mac_address": "$localcameraid",
	"is_authenticated": false,
	"should_config": false,
      }
    }
    """
    access_token = get_access_token()
    user_id = get_user_id()
    device_id, user_agent = get_device_data(host, port)
    payload = dict(
            device_id_discovering=device_id,
            acquisition_method='batch',
            device_user_agent=user_agent,
            user_id=user_id,
            local_camera_id=camera_name,
            name=camera_name,
            mac_address=camera_name, # TODO - find out if this is still required.
            is_authenticated=True,
            should_config=True # toggles the camera 'ON'
    )
    payload = dict(camera_name=payload)
    headers = {"Authorization", "token %s" % access_token}
    response = requests.post(CAMIO_REGISTER_URL, headers=headers, json=payload)
    print response
    return response # @TODO - parse out the camera ID from the response and return that

def post_video_content(host, port, camera_name, camera_id, filepath, timestamp):
    """
    arguments:
        host        - the url of the segmenter
        port        - the port to access the webserver on the segmenter
        camera_name - the parsed name of the camera
        camera_id   - the ID of the camera as returned from the service
        filepath    - full path to the video file that needs segmentation
        timestamp   - the starting timestamp of the video file
    returns: true/false based on success
    
    description: this function is called when we find a video for a specific camera, we call
                 this function where the logic should exist to post the file content to a video
                 segmenter.
    """
    filehash = None
    with open(filepath) as fh:
        filehash = hash_file_in_chunks(fh)
    urlbase = "%s:%s" % (host, port)
    url = urlbase + "access_token=%s&local_camera_id=%s&camera_id=%s&hash=%s&timestamp=%s" % (access_token, camera_name, camera_id, filehash, timestamp)
    if not os.path.exists(filepath):
        sys.stderr.print("unable to locate video-file: %s. exiting" % filepath)
        return False
    response = requests.post(url, files={'file': open(filepath, 'rb')})
    return response.status_code in (200, 204)




