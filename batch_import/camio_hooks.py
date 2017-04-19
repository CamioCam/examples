#!/usr/bin/env python

import re
import pprint
import os
import sys
import json
import logging
import hashlib
import requests

"""
Camio-specific hook examples for use with the video import script
"""

CAMIO_REGISTER_URL="https://www.camio.com/api/cameras/discovered"
CAMIO_REGISTER_URL_TEST="https://test.camio.com/api/cameras/discovered"
CAMIO_JOBS_URL = "https://test.camio.com/api/jobs"
CAMIO_PARAMS = {}

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
    urlbase = "http://%s:%s" % (host, port)
    url = urlbase + "/box/settings"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def register_camera(camera_name, device_id=None, host=None, port=None):
    """
    arguments:
        camera_name   - the name of the camera (as parsed from the filename) 
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
    """
    access_token = get_access_token()
    user_id = get_user_id()
    #device_id, user_agent = get_device_data(host, port)
    user_agent = "Linux"
    CAMIO_PARAMS.update(device_id=device_id, user_id=user_id, user_agent=user_agent)
    local_camera_id = hashlib.sha1(camera_name).hexdigest()
    payload = dict(
            device_id_discovering=device_id,
            acquisition_method='batch',
            device_user_agent=user_agent,
            user_id=user_id,
            local_camera_id=local_camera_id,
            name=camera_name,
            mac_address=camera_name, # TODO - find out if this is still required.
            is_authenticated=True,
            should_config=True # toggles the camera 'ON'
    )
    payload = {local_camera_id: payload}
    headers = {"Authorization": "token %s" % access_token}
    response = requests.post(CAMIO_REGISTER_URL_TEST, headers=headers, json=payload)
    response = response.json()
    camera_id = response[local_camera_id].get('camera_id')
    return camera_id # @TODO - parse out the camera ID from the response and return that

def post_video_content(host, port, camera_name, camera_id, filepath, timestamp, latlng=None):
    """
    arguments:
        host        - the url of the segmenter
        port        - the port to access the webserver on the segmenter
        camera_name - the parsed name of the camera
        camera_id   - the ID of the camera as returned from the service
        latlng (opt) - the lat/long of the camera (as parsed from the filename)
        filepath    - full path to the video file that needs segmentation
        timestamp   - the starting timestamp of the video file
    returns: true/false based on success
    
    description: this function is called when we find a video for a specific camera, we call
                 this function where the logic should exist to post the file content to a video
                 segmenter.
    """
    filehash = None
    device_id = CAMIO_PARAMS.get('device_id')
    if not device_id: return False
    with open(filepath) as fh:
        filehash = hash_file_in_chunks(fh)
    urlbase = "http://%s:%s" % (host, port)
    urlbase = urlbase + "/box/content"
    local_camera_id = hashlib.sha1(camera_name).hexdigest()
    urlparams = "access_token=%s&local_camera_id=%s&camera_id=%s&hash=%s&timestamp=%s" % (
        device_id, local_camera_id, camera_id, filehash, timestamp)
    url = urlbase + "?" + urlparams
    if not os.path.exists(filepath):
        sys.stderr.write("unable to locate video-file: %s. exiting" % filepath)
        return False
    with open(filepath, 'rb') as fh:
        response = requests.post(url, data=fh)
    return response.status_code in (200, 204)

def assign_job_ids(self, db, unscheduled):
    item_count = len(unscheduled)
    # if we have files to upload follow process in https://github.com/CamioCam/Camiolog-Web/issues/4555
    if item_count:        
        device_id = CAMIO_PARAMS.get('device_id')
        camio_account_token = get_access_token()
        item_average_size_bytes = sum(params['size'] for params in unscheduled)/item_count
        payload = {'device_id':device_id, 'item_count':item_count, 
                   'item_average_size_bytes':item_average_size_bytes}
        headers = {'Authorization': 'token %s' % camio_account_token}
        res = requests.put(CAMIO_JOBS_URL, json=payload, headers=headers)         
        try:
            shards = res.json()
        except:
            print res.content
            print 'server response error: %r' % res
            sys.exit(1)
        job_id = shards['job_id']
        n = 0
        upload_urls = []
        for shard_id in sorted(shards['shard_map']):
            shard = shards['shard_map'][shard_id]
            n += shard['item_count']
            upload_urls.append((n, shard_id, shard['upload_url']))

        # for each new file to upload store the job_id and the upload_url from the proper shard
        upload_urls_k = 0
        for k, params in enumerate(unscheduled):        
            key = params['key']
            params['job_id'] = job_id
            while k>=upload_urls[upload_urls_k][0]: upload_urls_k += 1
            params['shard_id'] = upload_urls[upload_urls_k][1]
            params['upload_url'] = upload_urls[upload_urls_k][2]
            db[key] = params
            db.sync()

def register_jobs(self, db, jobs):
    for job_id, shard_id in jobs:
        rows = filter(lambda params: (params['job_id'], params['shard_id']) == (job_id, shard_id), db.values())
        hash_map = {}
        for params in rows:
            hash_map[params['key']] = {'original_filename': params['filename'], 'size_MB': params['size']/1e6}
            payload = {
                'job_id': job_id,
                'shard_id': shard_id,
                'item_count':len(rows),
                'hash_map': hash_map
                }
        url = rows[0]['upload_url']
        requests.put(url, json=payload)
