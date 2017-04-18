#!/usr/bin/env python

"""
Camio-specific hook examples for use with the video import script
"""

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
    """
    pass

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
    pass
