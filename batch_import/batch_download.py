#!/usr/bin/env python

DESCRIPTION = \
"""
this script will cycle over a given time-period and download all videos from a given camera that come from
within that time period using the Camio search API (https://api.camio.com/#search)

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


import os
import sys
import argparse
import logging
import json
import urllib
import requests
import textwrap

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def fail(msg, *args):
    logging.error(msg, *args)
    sys.exit(1)

class BatchDownloader(object):

    def __init__(self):
        self.CAMIO_SERVER_URL = "https://www.camio.com"
        self.CAMIO_JOBS_EDNPOINT = "api/jobs"
        self.CAMIO_SEARCH_ENDPOINT = "api/search"
        self.CAMIO_OAUTH_TOKEN_ENVVAR = "CAMIO_OAUTH_TOKEN"
        self.access_token = None
	self.job_id = None
        self.job = None

        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent(DESCRIPTION), epilog=EXAMPLES
        )
        # positional args
        self.parser.add_argument('job_id', type=str, help='the ID of the job that you wish to download the labels for')
        # optional arguments
        self.parser.add_argument('-a', '--access_token', type=str, help='your Camio OAuth token (if not given we check the CAMIO_OAUTH_TOKEN envvar)')
        self.parser.add_argument('-c', '--csv', action='store_true', help='set to export in CSV format')
        self.parser.add_argument('-x', '--xml', action='store_true', help='set to export in XML format')
        self.parser.add_argument('-t', '--testing', action='store_true', help="use Camio testing servers instead of production (for dev use only!)")
        self.parser.add_argument('-v', '--verbose', action='store_true', default=False, help='set logging level to debug')
        self.parser.add_argument('-q', '--quiet', action='store_true', default=False, help='set logging level to errors only')

    def parse_argv_or_exit(self):
        self.args = self.parser.parse_args()
	self.job_id = self.args.job_id
        if self.args.access_token:
            self.access_token = self.args.access_token
        if self.args.testing:
            self.CAMIO_SERVER_URL = "https://test.camio.com"
        if self.args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif self.args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        return self.args

    def get_access_token(self):
        if not self.access_token:
            token = os.environ.get(self.CAMIO_OAUTH_TOKEN_ENVVAR)
            if not token:
                fail("unable to find Camio OAuth token in either hook-params json or CAMIO_OAUTH_TOKEN envvar. \
                     Please set or submit this token")
            self.access_token = token
        return self.access_token

    def get_job_url(self):
        return "%s/%s/%s" % (self.CAMIO_SERVER_URL, self.CAMIO_JOBS_EDNPOINT, self.job_id)

    def gather_job_data(self):
        headers = {"Authorization": "token %s" % self.get_access_token() }
        logging.debug("making GET request to endpoint %s, headers: %r", self.get_job_url(), headers)
        ret = requests.get(self.get_job_url(), headers=headers)
        if not ret.status_code in (200, 204):
            fail("unable to obtain job resource with id: %s from %s endpoint. return code: %r", self.job_id, self.get_job_url(), ret.status_code)
        logging.debug("got job-information returned from server:\n%r", ret.text)
        self.job = ret.json()
        self.earliest_date, self.latest_date = self.job['request']['earliest_date'], self.job['request']['latest_date']
        self.cameras = [camera['name'] for camera in self.job['request']['cameras']]
        logging.info("Job Definition | earliest date: %r, latest date: %r", self.earliest_date, self.latest_date)
        logging.info("\tcameras included in inquiry: %r", self.cameras)
        return self.job

    def make_search_request(self, text):
        pass

    def get_results_for_epoch(self, start_time, end_time, camera_name):
        """ 
        use the Camio search API to return all of the search results for the given camera between the two unix-style timestamps
        these search results can then be parsed and the meta-data about the labels added to each event can be extracted and assembled
        into a dictionary of some sorts to be returned to the user
        """
        pass

    def run(self):
        self.parse_argv_or_exit()
        self.gather_job_data()
        # grab the job from the job API
        # forward that job info to some function that loops over the start-to-end-time
        # have the function call get_result_for_epoch with small time windows that assembles the 
        # labels into a dictionary for you
        return  True

def main():
    return BatchDownloader().run()

if __name__ == '__main__':
    main()

