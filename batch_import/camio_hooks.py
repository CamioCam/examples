#!/usr/bin/env python

import re
import pprint
import os
import sys
import json
import logging
import logging
import hashlib
import datetime
import requests

"""
Camio-specific hook examples for use with the video import script
"""

# TODO - change the URLs to test.camio.com instead of test.camio.com after deployed to prod
CAMIO_REGISTER_URL="https://test.camio.com/api/cameras/discovered"
CAMIO_JOBS_URL = "https://test.camio.com/api/jobs"
CAMIO_PARAMS = {}

# TODO - change to CAMIO_TEST_PROD when on production
CAMIO_OAUTH_TOKEN_ENVVAR = "CAMIO_OAUTH_TOKEN"
CAMIO_BOX_DEVICE_ID_ENVVAR = "CAMIO_BOX_DEVICE_ID"

# handle to logger
Log = None

# plan definitions for actual_values entry
CAMIO_PLANS = { 'pro': 'PRO', 'plus': 'PLUS', 'basic': 'BASIC' }

def fail(msg):
    Log.error(msg)
    sys.exit(1)

def set_hook_data(data_dict):
    global CAMIO_PARAMS
    global Log
    CAMIO_PARAMS.update(data_dict)
    if CAMIO_PARAMS.get('logger'):
        Log = CAMIO_PARAMS['logger']
    else:
        Log = logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    Log.debug("setting camio_hooks data as:\n%r", data_dict)

def get_access_token():
    if not CAMIO_PARAMS.get('access_token'):
        token = os.environ.get(CAMIO_OAUTH_TOKEN_ENVVAR)
        if not token:
            fail("unable to find Camio OAuth token in either hook-params json or CAMIO_OAUTH_TOKEN envvar. \
                 Please set or submit this token")
        CAMIO_PARAMS['access_token'] = token
    return CAMIO_PARAMS['access_token']

def dateshift(timestamp, seconds):
    date = datetime.datetime.strptime(timestamp[:23], "%Y-%m-%dT%H:%M:%S.%f")
    date = date + datetime.timedelta(seconds=seconds)
    return date.isoformat()

def get_device_id():
    if not CAMIO_PARAMS.get('device_id'):
        device = os.environ.get(CAMIO_BOX_DEVICE_ID_ENVVAR)
        if not device:
            fail("unable to find Camio Box Device ID in either hook-params json or CAMIO_BOX_DEVICE_ID_ENVVAR envvar.\
                  Please set or submit this value")
        CAMIO_PARAMS['device_id'] = device 
    return CAMIO_PARAMS['device_id']

def get_camera_plan():
    if not CAMIO_PARAMS.get('plan'):
        Log.warn("no camera-plan value submitted in hook-data, assuming PLUS as plan")
        return CAMIO_PLANS['plus']
    elif not CAMIO_PLANS.get(CAMIO_PARAMS['plan'].lower()):
        Log.error("submitted invalid 'plan' value: %s, valid values are: %r",
                CAMIO_PARAMS['plan'], [CAMIO_PLANS[key] for key in CAMIO_PLANS])
        return CAMIO_PLANS['plus'] 
    return CAMIO_PLANS.get(CAMIO_PARAMS['plan'].lower())

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

def get_camera_id(local_camera_id):
    access_token = get_access_token()
    headers = {"Authorization": "token %s" % access_token}
    response = requests.get(CAMIO_REGISTER_URL, headers=headers)
    response = response.json()
    return response[local_camera_id].get('camera_id')

def register_camera(camera_name, host=None, port=None):
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
    device_id, access_token, camera_plan = get_device_id(), get_access_token(), get_camera_plan()
    user_agent = "video-importer script"
    local_camera_id = hashlib.sha1(camera_name).hexdigest()
    plan = dict(
        is_multiselect = False,
        options = [ {'name': 'Plan', 'value': camera_plan }]
    )
    payload = dict(
            device_id_discovering=device_id,
            acquisition_method='batch',
            device_user_agent=user_agent,
            local_camera_id=local_camera_id,
            name=camera_name,
            actual_values = dict(plan=plan),
            mac_address=camera_name, # TODO - find out if this is still required.
            is_authenticated=True,
            should_config=True # toggles the camera 'ON'
    )
    payload = {local_camera_id: payload}
    headers = {"Authorization": "token %s" % access_token}
    response = requests.post(CAMIO_REGISTER_URL, headers=headers, json=payload)
    return get_camera_id(local_camera_id)

def post_video_content(host, port, camera_name, camera_id, filepath, timestamp, location=None):
    """
    arguments:
        host        - the url of the segmenter
        port        - the port to access the webserver on the segmenter
        camera_name - the parsed name of the camera
        camera_id   - the ID of the camera as returned from the service
        location(opt) - a json-string describing the location of the camera 
                        Example {"location:" {"lat": 7.367598, "lng":134.706975}, "accuracy":5.0}
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
        earliest_date = min(params['timestamp'] for params in unscheduled)
        latest_date = max(dateshift(params['timestamp'], params['duration']) 
                          for params in unscheduled)
        device_id = CAMIO_PARAMS.get('device_id')
        camio_account_token = get_access_token()
        item_average_size_bytes = sum(len(json.dumps(
                    {'key':params['key'], 
                     'original_filename': params['filename'], 
                     'size_MB': params['size']/1e6})) for params in unscheduled)/item_count
        payload = {
            'device_id':device_id, 
            'item_count':item_count,
            'earliest_date': earliest_date,
            'latest_date': latest_date,
            'item_average_size_bytes':item_average_size_bytes
        }
        headers = {'Authorization': 'token %s' % camio_account_token}
        res = requests.put(CAMIO_JOBS_URL, json=payload, headers=headers)         

        try:
            shards = res.json()
        except:
            Log.error('server response error: %r', res)
            sys.exit(1)
        job_id = shards['job_id']
        n = 0
        upload_urls = []
        for shard_id in sorted(shards['shard_map']):
            shard = shards['shard_map'][shard_id]
            n += shard['item_count']
            upload_urls.append((n, shard_id, shard['upload_url']))

        # for debug onlin
        for item in upload_urls:
            Log.debug("upload item: %r", item[0])
        Log.debug('len(unscheduled)=%s', len(unscheduled))

        # for each new file to upload store the job_id and the upload_url from the proper shard
        upload_urls_k = 0
        total_urls = 0
        for k, params in enumerate(unscheduled):        
            key = params['key']
            params['job_id'] = job_id
            while k >= upload_urls[upload_urls_k][0]: 
                Log.debug("upload_urls_k: %r", upload_urls_k)
                upload_urls_k += 1
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

