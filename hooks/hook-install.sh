#!/usr/bin/env bash

sudo apt-get install mongodb
sudo apt-get install python-dev
sudo apt-get install python-pil
pip install bottle gunicorn pymongo requests
nohup gunicorn -w 2 -b 0.0.0.0:80 hook-example:app > /tmp/gunicorn.log &
nohup python hook-example.py > /tmp/taskqueue.log &
