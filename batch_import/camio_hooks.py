#!/usr/bin/env python

import re
import pprint
import time
import traceback
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
CAMIO_SERVER_URL = "https://www.camio.com"
CAMIO_REGISTER_ENDPOINT = "/api/cameras/discovered"
CAMIO_JOBS_ENDPOINT = "/api/jobs"
CAMIO_DEVICES_ENDPOINT = "/api/devices"
CAMIO_STATE_ENDPOINT = "/api/devices/state/"
CAMIO_PARAMS = {}
BATCH_IMPORT_DEFAULT_PORT = 8080

# TODO - change to CAMIO_TEST_PROD when on production
CAMIO_OAUTH_TOKEN_ENVVAR = "CAMIO_OAUTH_TOKEN"
CAMIO_BOX_DEVICE_ID_ENVVAR = "CAMIO_BOX_DEVICE_ID"

# if posting to box fails, wait this long before trying again
POST_FAILURE_RETRY_SECONDS = 25

# handle to logger
Log = None

# plan definitions for actual_values entry
CAMIO_PLANS = { 'pro': 'PRO', 'plus': 'PLUS', 'basic': 'BASIC' }

def fail(msg, *args):
    Log.error(msg, *args)
    sys.exit(1)

def network_request(reqtype, url, data=None, json=None):
    access_token = get_access_token()
    headers = {"Authorization": "token %s" % access_token}
    func = getattr(requests, reqtype)
    ret = None
    Log.debug("making %s request to URL (%s)")
    try:
        ret = func(url, headers=headers, data=data, json=json)
    except Exception, e:
        Log.error("%s request to url (%s) failed")
        Log.error(traceback.format_exc())
    return ret

def set_hook_data(data_dict):
    """
    let the importer pass in arbitrary key-value pairs for use by the hooks program
    (we tend to use this to accept plan data or user-account information)
    data_dict: a python list/dictionary of values passed in from the video importer script, passed in by the
                user under the --hook_data_json argument. 
    """
    global CAMIO_PARAMS
    global CAMIO_SERVER_URL
    global Log
    CAMIO_PARAMS.update(data_dict)
    if CAMIO_PARAMS.get('logger') and not Log:
        Log = CAMIO_PARAMS['logger']
    elif not Log:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        Log = logging.getLogger()
    if CAMIO_PARAMS.get('test'):
        Log.info("using test.camio.com instead of www.camio.com")
        CAMIO_SERVER_URL = "https://test.camio.com"
    Log.debug("setting camio_hooks data as:\n%r", CAMIO_PARAMS)

def get_account_info():
    """
    this function takes an auth token and gathers both the device ID of their
    Camio Box and then uses that device ID to query for the current local IP
    address. This way the user doesn't have to supply those items to use manually
    """
    access_token = get_access_token()
    device_id = get_device_id()
    ip_address = CAMIO_PARAMS.get('ip_address')
    if not device_id:
        url = CAMIO_SERVER_URL + CAMIO_DEVICES_ENDPOINT
        ret = network_request('get', url)
        if not ret:
            fail("unable to obtain account info (device_id and Box IP address")
        devices = ret.json()
        if not devices or len(devices) < 1:
            fail('no Camio Box devices found on your account, have you registered your Box yet?')
        device_id = devices[0]['device_id']
        CAMIO_PARAMS['device_id'] = device_id
    if not ip_address:
        url = CAMIO_SERVER_URL + CAMIO_STATE_ENDPOINT + "?device_id=%s" % device_id
        ret = network_request('get', url)
        device = ret.json()
        network_config = device.get('state').get('network_configuration_actual')
        if not network_config:
            fail("unable to obtain IP address of Camio box")
        ip_address = network_config.get('ip_address')
        if not network_config:
            fail("unable to obtain IP address of Camio box")
        CAMIO_PARAMS['ip_address'] = ip_address
    return ip_address, device_id


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

def get_access_token():
    if not CAMIO_PARAMS.get('access_token'):
        token = os.environ.get(CAMIO_OAUTH_TOKEN_ENVVAR)
        if not token:
            fail("unable to find Camio OAuth token in either hook-params json or CAMIO_OAUTH_TOKEN envvar. \
                 Please set or submit this token")
        CAMIO_PARAMS['access_token'] = token
    return CAMIO_PARAMS['access_token']

def dateshift(timestamp, seconds, format = "%Y-%m-%dT%H:%M:%S.%f"):
    date = datetime.datetime.strptime(timestamp[:23], format)
    date = date + datetime.timedelta(seconds=seconds)
    return date.strftime(format)

def get_device_id(fail=True):
    if not CAMIO_PARAMS.get('device_id'):
        device = os.environ.get(CAMIO_BOX_DEVICE_ID_ENVVAR)
        if not device:
            fail("unable to find Camio Box Device ID in either hook-params json or CAMIO_BOX_DEVICE_ID_ENVVAR envvar.\
                  Please set or submit this value")
        CAMIO_PARAMS['device_id'] = device 
    return CAMIO_PARAMS['device_id']

def get_camera_param(camera_name, key):
    """
    CAMIO_PARAMS = {
       "key": "value",
       "cameras": {
         "camera_1": {
           "key1": "value1" <-- given camera_name = camera_1 and key = key1, return this value "value1"
         },
         "camera_2": {
           "key2": "value2"
         }
        }
    }
    """
    return CAMIO_PARAMS.get('cameras', {}).get(camera_name, {}).get(key) or CAMIO_PARAMS.get(key)

def get_camera_plan(camera_name):
    """
    plan will either be under the cameras.$camera_name.plan item or at the top-level 'plan'
    """
    plan = get_camera_param(camera_name, 'plan')
    if not plan:
        Log.warn("no camera-plan value submitted in hook-data, assuming PLUS as plan")
        return CAMIO_PLANS['plus']
    elif not CAMIO_PLANS.get(plan.lower()):
        fail("submitted invalid 'plan' value: %s, valid values are: %r",
                plan, [CAMIO_PLANS[key] for key in CAMIO_PLANS])
    return CAMIO_PLANS.get(plan.lower())

def get_camera_image_resolutions(camera_name):
    Log.debug("checking image resolution values")
    actual_values = dict()
    for item in ['img_%s_size%s' % (x,y) for x in ['x', 'y'] for y in ['', '_cover', '_extraction']]:
        value = get_camera_param(camera_name, item)
        Log.debug("value for (%s): %r", item, value)
        if not value: continue
        actual_values[item] = dict(options=[{'name': item, 'value': value}])
    return actual_values

def get_camera_config(local_camera_id):
    access_token = get_access_token()
    headers = {"Authorization": "token %s" % access_token}
    url = CAMIO_SERVER_URL + CAMIO_REGISTER_ENDPOINT
    #response = requests.get(url, headers=headers)
    response = network_request('get', url)
    response = response.json()
    Log.debug("cameras under account:\n%r", [response[camera].get('name') for camera in response])
    return response[local_camera_id]

def generate_actual_values(camera_name):
    camera_plan = get_camera_plan(camera_name)
    image_values = get_camera_image_resolutions(camera_name)
    plan = dict(
        is_multiselect = False,
        options = [ {'name': 'Plan', 'value': camera_plan }]
    )
    actual_values = dict(plan=plan)
    actual_values.update(image_values)
    Log.debug("final actual values:\n%r", actual_values)
    return actual_values

def register_camera(camera_name, port=None):
    """
    arguments:
        camera_name   - the name of the camera (as parsed from the filename) 
        port          - the port to access the webserver of the segmenter
    returns: this function returns a dctionary describing the new camera, including the camera ID
             note - it is required that there is at least one property in this dictionary called
             'camera_id', that is the unique ID of the camera as determined by the service this
             function is registering the camera with.
                 
    description: this function is called when a new camera is found by the import script, 
                 if a camera needs to be registered with a service before content from that
                 camera can be segmented then the logic for registering the camera should 
                 exist in this function.
                 For Camio, this function POSTs to /api/cameras/discovered with the new camera
                 entry. It is required that the "acquisition_method": "batch" set in the camera 
                 config for it to be known as a batch-import source as opposed to a real-time 
                 input source.
    """
    device_id, host = get_account_info()
    access_token = get_access_token()
    user_agent = "video-importer script"
    local_camera_id = hashlib.sha1(camera_name).hexdigest()
    actual_values = generate_actual_values(camera_name)
    payload = dict(
            device_id_discovering=device_id,
            acquisition_method='batch',
            device_user_agent=user_agent,
            local_camera_id=local_camera_id,
            name=camera_name,
            actual_values = actual_values,
            default_values = actual_values,
            mac_address=camera_name, # TODO - find out if this is still required.
            is_authenticated=True,
            should_config=True # toggles the camera 'ON'
    )
    Log.info("registering camera: name=%s, local_camera_id=%s", camera_name, local_camera_id)
    payload = {local_camera_id: payload}
    headers = {"Authorization": "token %s" % access_token}
    url = CAMIO_SERVER_URL + CAMIO_REGISTER_ENDPOINT
    #response = requests.post(url, headers=headers, json=payload)
    response = network_request('post', url, json=payload)
    try:
        config = get_camera_config(local_camera_id)
    except:
        Log.info("key error for new camera, waiting 15 seconds to retry")
        time.sleep(15)
        config = get_camera_config(local_camera_id)
    return config

def post_video_content(camera_name, camera_id, filepath, timestamp, host=None, port=None, location=None):
    """
    arguments:
        host        - the url of the segmenter
        port        - the port to access the webserver on the segmenter
        camera_name - the parsed name of the camera
        camera_id   - the ID of the camera as returned from the service
        filepath    - full path to the video file that needs segmentation
        timestamp   - the starting timestamp of the video file
        location(opt) - a json-string describing the location of the camera 
                        Example {"location:" {"lat": 7.367598, "lng":134.706975}, "accuracy":5.0}
    returns: true/false based on success
    
    description: this function is called when we find a video for a specific camera, we call
                 this function where the logic should exist to post the file content to a video
                 segmenter.
    """
    device_id, host = get_account_info()
    if not port:
        port = BATCH_IMPORT_DEFAULT_PORT
    with open(filepath) as fh:
        filehash = hash_file_in_chunks(fh)
    urlbase = "http://%s:%s" % (host, port)
    urlbase = urlbase + "/box/content"
    local_camera_id = hashlib.sha1(camera_name).hexdigest()
    urlparams = "access_token=%s&local_camera_id=%s&camera_id=%s&hash=%s&timestamp=%s" % (
        device_id, local_camera_id, camera_id, filehash, timestamp)
    url = urlbase + "?" + urlparams
    if not os.path.exists(filepath):
        Log.error("unable to locate video-file: %s, continuing", filepath)
        return False
    Log.debug("posting video content: file=%s, camera=%s, timestamp=%s", filepath, camera_name, timestamp)
    repsonse = None
    try:
        with open(filepath, 'rb') as fh:
            #response = requests.post(url, data=fh)
            response = network_request('post', url, data=fh)
    except Exception, e:
        Log.error("error while posting video content to Box")
        Log.error(traceback.format_exc())
        Log.error("backing off for %d seconds before retry", POST_FAILURE_RETRY_SECONDS)
        for i in range(0, POST_FAILURE_RETRY_SECONDS, 5):
            Log.info("waited: %d seconds...", i)
        Log.info("back-off wait over, retrying POST video content")
        with open(filepath, 'rb') as fh:
            #response = requests.post(url, data=fh)
            response = network_request('post', url, data=fh)

    return response and response.status_code in (200, 204)

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
        cameras = CAMIO_PARAMS.get('registered_cameras', {})
        payload = {
            'device_id':device_id, 
            'item_count':item_count,
            'earliest_date': earliest_date,
            'latest_date': latest_date,
            'item_average_size_bytes':item_average_size_bytes,
            'cameras': cameras
        }
        headers = {'Authorization': 'token %s' % camio_account_token}
        Log.debug("registering job with parameters:\n%r\nheaders:\n%r", payload, headers)
        url = CAMIO_SERVER_URL + CAMIO_JOBS_ENDPOINT
        #res = requests.put(url, json=payload, headers=headers)         
        res = network_request('put', url, json=payload)

        try:
            shards = res.json()
            Log.debug("server returned shards:\n%r", shards)
        except:
            fail("server response error:\n%r", res)
        job_id = shards['job_id']
        n = 0
        upload_urls = []
        for shard_id in sorted(shards['shard_map']):
            shard = shards['shard_map'][shard_id]
            n += shard['item_count']
            upload_urls.append((n, shard_id, shard['upload_url']))

        # for debug only 
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
        return job_id

def register_jobs(self, db, jobs):
    success = True
    for job_id, shard_id in jobs:
        rows = filter(lambda params: \
            (params['job_id'], params['shard_id']) == (job_id, shard_id), db.values()
        )
        hash_map = {}
        for params in rows:
            hash_map[params['key']] = {
                'original_filename': params['filename'], 'size_MB': params['size']/1e6
            }
        payload = {
            'job_id': job_id,
            'shard_id': shard_id,
            'item_count':len(rows),
            'hash_map': hash_map
            }
        Log.debug("registering job:\n ID=%s\n shard ID=%s\n num items=%d\n file-map=%r", 
                job_id, shard_id, len(rows), hash_map)
        url = rows[0]['upload_url']
        #ret = requests.put(url, json=payload)
        ret = network_request('put', url, json=payload)
        if not ret.status_code in (200, 204):
            Log.error("error registering job: %s", job_id)
            Log.error("server returned: %d", ret.status_code)
            success = False
        return success

