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

def register_camera(camera_name, latlong=None):
    """
    arguments:
        camera_name   - the name of the camera (as parsed from the filename) 
        latlong (opt) - the lat/long of the camera (as parsed from the filename)
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
    payload = dict(
            device_id_discovering=None,
            acquisition_method='batch',
            device_user_agent=None,
            user_id=None,
            local_camera_id=camera_name,
            name=camera_name,
            mac_address=camera_name, # TODO - find out if this is still required.
            is_authenticated=True,
            should_config=True # toggles the camera 'ON'
    )
    payload = dict(camera_name=payload)
    access_token = get_access_token()
    headers = {"Authorization", "token %s" % access_token}
    response = requests.post(CAMIO_REGISTER_URL, headers=headers, data=json.dumps(payload))
    print response
    return response # @TODO - parse out the camera ID from the response and return that

def post_video_content(camera_name, camera_id, filepath):
    """
    arguments:
        camera_name - the parsed name of the camera
        camera_id   - the ID of the camera as returned from the service
        filepath    - full path to the video file that needs segmentationl
    returns: nothing
    
    description: this function is called when we find a video for a specific camera, we call
                 this function where the logic should exist to post the file content to a video
                 segmenter.
    """
    filehash = None
    with open(filepath) as fh:
        filehash = hash_file_in_chunks(fh)


