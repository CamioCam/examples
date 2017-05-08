#!/usr/bin/env python

DESCRIPTION = \
"""
this script will cycle over a given time-period and download all videos from a given camera that come from
within that time period using the Camio search API (https://api.camio.com/#search (https://api.camio.com/#search)

This script is designed to be used after a batch-import job has been completed and you wish to retreive a
compilation of all of the labels assigned to all of the events that were parsed from the grouping of batch import
video you submitted for the given job.
"""

EXAMPLES = \
"""
Example:

    Here is an example of how to run the script to recover a dictionary of lables for the last job that you 
    submitted
"""

API_NOTES = \
"""
here are some notes on example API calls taken from watching dev-tools in the webapp

https://camio.com/api/search/?text=sharx-east+john%40camiolog.com&sort=desc&num_results=100&date=2017-05-05T19%3A10%3A10.514-0700

"""

import os
import sys
import argparse
import json
import requests

def parse_argv_or_exit():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = textwrap.dedent(DESCRIPTION), epilog=EXAMPLES
    )

    # positional args
	parser.add_argument('start_time_unix', type=int, 'the Unix-timestamp of the time to start downloading meta-data from')
	parser.add_argument('end_time_unix', type=int, 'the Unix-timestamp to gather meta-data until')
	parser.add_argument('camera_name', type=int, 'the name of the camera that you wish to download meta-data for')
	

def main():
    args = parse_argv_or_exit()

if __name__ == '__main__':
    main()

