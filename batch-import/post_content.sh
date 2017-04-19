#!/usr/bin/env bash

# POST a single video to a Box for segmentation and analysis
# This requires that
# 1. You have a Camio Box running and you can access it over the network
# 2. You've registered a batch-import source with Camio
# 3. That batch-import source is 'toggled-on' for the Box described in #1

function post_batch_import {
    host=$1          # IP-address of Box
    port=$2          # port of web-server on Box (normally 8080)
    filepath=$3      # path to video file to send to Box
    localcameraid=$4 # arbitrary user-chosen ID for the camera
    cameraid=$5      # full ID of the camera, returned by Camio upon registration
    accesstoken=$6   # device_id of the Box the POST is being sent to 
    timestamp=$7     # YYYY-MM-DDTHH:MM:SS.FF formatted timestamp of the start of the video
    if [ ! -e $filepath ]; then
        echo "file ($filepath) doesn't exist!"
        exit 1
    fi
    hash=$(shasum -b "$filepath" | awk '{ print $1 }')
    baseurl="$host:$port/box/content"
    queryargs="access_token=$accesstoken&local_camera_id=$localcameraid&camera_id=$cameraid&hash=$hash&timestamp=$timestamp"
    urlstring="$baseurl?$queryargs"
    echo "posting to url: $urlstring"
    curl --data-binary "@$filepath" "$urlstring"
    echo $?
}

post_batch_import "$@"
