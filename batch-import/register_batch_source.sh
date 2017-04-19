#!/usr/bin/env bash

# Use this script to register a camera source with your Camio account. 
# You need to know the following information to use this script
# 1 - Device ID of the Camio-Box you plan on using this batch-input source with
# 2 - Some name for the new camera source
# 3 - some ID for the new camera

# NOTE - this script assumed that you have some environment variables set, these varibles are
# CAMIOTOKENPROD - access token (oauth) for you Camio account on the production servers
# CAMIOIDPROD - ID of your camio account on production servers
# then the same thing but for our testing server (test.camio.com)

function register_batch_camera {
    # args
    # 1 - either 'test' or 'prod' for testing/production servers
    # 2 - device_id
    # 3 - local_camera_id
    # 4 - cameraname

    if [ $1 == "test" ]; then
        : "${CAMIOTOKENTEST? Need to set CAMIOTOKENTEST environment variable to use this script in 'test' mode}"
        : "${CAMIOIDTEST? Need to set CAMIOIDTEST environment variable to use this script in 'test' mode}"
        url="https://test.camio.com/api/cameras/discovered"
        token=$CAMIOTOKENTEST
        userid=$CAMIOIDTEST
        echo "using testing servers"
    else
        : "${CAMIOTOKENPROD? Need to set CAMIOTOKENPROD environment variable to use this script in 'prod' mode}"
        : "${CAMIOIDPROD? Need to set CAMIOIDPROD environment variable to use this script in 'prod' mode}"
        url="https://www.camio.com/api/cameras/discovered"
        token=$CAMIOTOKENPROD
        userid=$CAMIOIDPROD
        echo "using production"
    fi
    deviceid=$2
    localcameraid=$3
    cameraname=$4

    cat <<EOF > /tmp/tmp_batch_import.json
{
    "$localcameraid": {
        "device_id": "$deviceid",
        "acquisition_method": "batch",
        "user_id": "$userid",
        "local_camera_id": "$localcameraid",
        "name": "$cameraname",
        "should_config": true
      }
  }
EOF

    cat /tmp/tmp_batch_import.json | curl -H "Authorization: token $token" --data-binary "@-" $url
    success=$?
    # rm /tmp/tmp_batch_import.json
    if [ $? -ne 0 ]; then
        echo "camera: (name: $cameraname, ID: $localcameraid) registration failed";
        return 1;
    else
        echo "camera: (name: $cameraname, ID: $localcameraid) registration succeeded";
        return 0;
    fi 
    
}       

register_batch_camera "$@"
