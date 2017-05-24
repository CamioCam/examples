#!/usr/bin/env python

DESCRIPTION = \
"""
This script will take a Camio job_id, find the time-boundaries and cameras involved in that job, and iterate over that 
time range while downloading all of the labels that Camio has annotated the events with.

This script is designed to be used after a batch-import job has been completed and you wish to retreive a
compilation of all of the labels assigned to all of the events that were parsed from the grouping of batch import
video you submitted for the given job.
"""

EXAMPLES = \
"""
Example:

    Here is an example of how to run the script to recover a dictionary of lables for the last job that you 
    submitted. This will obtain the bookmark of labels for the job with job_id "SjksdkjoowlkjlSDFiwjoijerSDRdsdf" and
    will write this output to the file /tmp/job_labels.json

    python download_labels.py --output_file /tmp/job_labels.json SjksdkjoowlkjlSDFiwjoijerSDRdsdf 

    If you just want to list all jobs that belong to your account, you can do the followng

    python download_labels.py --output_file /tmp/job_list.json

    which will print a list of jobs under your accout to stdout

"""


import os
import sys
import argparse
import logging
import traceback
import json
import urllib
import requests
import dateutil.parser
import textwrap
from datetime import datetime,timedelta

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
        self.white_labels = []

        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent(DESCRIPTION), epilog=EXAMPLES
        )
        # positional args
        self.parser.add_argument('job_id', nargs='?', type=str, help='the ID of the job that you wish to download the labels for')
        # optional arguments
        self.parser.add_argument('-o', '--output_file', type=str, default=None,
                                help="full path to the output file where the resulting labels will \
                                be stored in json format (default = {job_id}_results.json)")
        self.parser.add_argument('-a', '--access_token', type=str, help='your Camio OAuth token (if not given we check the CAMIO_OAUTH_TOKEN envvar)')
        self.parser.add_argument('-w', '--label_white_list', type=str, help='a json list of labels that are whitelisted to be included in the response')
        self.parser.add_argument('-f', '--label_white_list_file', type=str, help='a file containing a json list of labels that are whitelisted')
        self.parser.add_argument('-c', '--csv', action='store_true', help='(not implemented yet) set to export in CSV format')
        self.parser.add_argument('-x', '--xml', action='store_true', help='(not implemented yet) set to export in XML format')
        self.parser.add_argument('-t', '--testing', action='store_true', help="use Camio testing servers instead of production (for dev use only!)")
        self.parser.add_argument('-v', '--verbose', action='store_true', default=False, help='set logging level to debug')
        self.parser.add_argument('-q', '--quiet', action='store_true', default=False, help='set logging level to errors only')

    def parse_argv_or_exit(self):
        self.args = self.parser.parse_args()
        if not self.args.job_id:
            logging.info("no job_id specified, getting list of jobs")
        self.job_id = self.args.job_id
        if not self.args.output_file and self.job_id:
            self.results_file = "%s_results.json" % self.job_id
        elif not self.args.output_file:
            self.results_file = "job_list.json"
        else:
            self.results_file = self.args.output_file
        if self.args.access_token:
            self.access_token = self.args.access_token
        if self.args.testing:
            self.CAMIO_SERVER_URL = "https://test.camio.com"
        if self.args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif self.args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        if self.args.label_white_list:
            try:
                self.white_labels += json.loads(self.args.white_label_list)
            except:
                logging.error("unable to deserialize label white-list")
                logging.error(traceback.format_exc())
        if self.args.label_white_list_file:
            try:
                with open(self.args.label_white_list_file) as fh:
                    self.white_labels += json.load(fh)
            except:
                logging.error("unable to deserialize label white-list from file: %s", self.args.label_white_list_file)
                logging.error(traceback.format_exc())
                
        return self.args

    def get_access_token(self):
        if not self.access_token:
            token = os.environ.get(self.CAMIO_OAUTH_TOKEN_ENVVAR)
            if not token:
                fail("unable to find Camio OAuth token in either hook-params json or CAMIO_OAUTH_TOKEN envvar. \
                     Please set or submit this token")
            self.access_token = token
        return self.access_token

    def gather_all_job_data(self):
        """ GET /api/jobs to list all job data to user """
        headers = {"Authorization": "token %s" % self.get_access_token() }
        logging.debug("making GET request to endpoint %s, headers: %r", self.get_job_url(), headers)
        ret = requests.get(self.get_job_url(), headers=headers)
        if not ret.status_code in (200, 204):
            fail("unable to obtain job resource with id: %s from %s endpoint. return code: %r", self.job_id, self.get_job_url(), ret.status_code)
        parsed = ret.json()
        jobs = { job['job_id']: {
                    "start_time": job['request'].get('earliest_date'), 
                    "end_time": job['request'].get('latest_date'),
                    "item_count": job['request'].get('item_count'),
                    "status": job['status'],
                    "shard_count": len(job['shard_map']),
                    #"progress": len(job['shard_map']) / len([shard for shard in job['shard_map'] if shard['status'] == 'complete']),
                } for job in parsed
        }


        logging.info("total of %d jobs associated with your account", len(parsed))
        logging.debug(json.dumps(jobs, indent=2, sort_keys=True))
        logging.info("writing list of jobs to file: %s", self.results_file)
        with open(self.results_file, 'w') as fh:
            fh.write(json.dumps(jobs, indent=2, sort_keys=True))
        sys.exit(0)

    def get_job_url(self):
        if self.job_id:
            return "%s/%s/%s" % (self.CAMIO_SERVER_URL, self.CAMIO_JOBS_EDNPOINT, self.job_id)
        else:
            return "%s/%s" % (self.CAMIO_SERVER_URL, self.CAMIO_JOBS_EDNPOINT)

    def get_search_url(self, text, date=None):
        endpoint = self.CAMIO_SERVER_URL + "/" + self.CAMIO_SEARCH_ENDPOINT
        if date:
            return "%s?text=%s&num_results=100&date=%s" % (endpoint, text, date.isoformat())
        else:
            return "%s?text=%s&num_results=100" %(endpoint, text)

    def gather_job_data(self):
        headers = {"Authorization": "token %s" % self.get_access_token() }
        logging.debug("making GET request to endpoint %s, headers: %r", self.get_job_url(), headers)
        ret = requests.get(self.get_job_url(), headers=headers)
        if not ret.status_code in (200, 204):
            fail("unable to obtain job resource with id: %s from %s endpoint. return code: %r", self.job_id, self.get_job_url(), ret.status_code)
        logging.debug("got job-information returned from server:\n%r", ret.text)
        self.job = ret.json()
        self.earliest_date, self.latest_date = self.job['request']['earliest_date'], self.job['request']['latest_date']
        self.earliest_datetime = dateutil.parser.parse(self.earliest_date)
        self.latest_datetime = dateutil.parser.parse(self.latest_date)
        logging.debug("earliest datetime: %r, latest datetime: %r", self.earliest_datetime, self.latest_datetime)
        self.cameras = [camera['name'] for camera in self.job['request']['cameras']]
        logging.info("Job Definition:")
        logging.info("\tearliest date: %r, latest date: %r", self.earliest_date, self.latest_date)
        logging.info("\tcameras included in inquiry: %r", self.cameras)
        return self.job

    def make_search_request(self, text, date=None):
        headers = {"Authorization": "token %s" % self.get_access_token() }
        url = self.get_search_url(text, date)
        ret = requests.get(url, headers=headers)
        if not ret.status_code in (200, 204):
            logging.error("unable to obtain search results with query (%s)", text)
        logging.debug("got search results for query (%s)", text)
        #logging.debug("results:\n%r", ret.text)
        return ret.json()

    def get_results_from_epoch(self, start_time, end_time, camera_names):
        end_time = dateutil.parser.parse(end_time.isoformat() + "+00:00")
        more_results = True
        labels = dict()
        while more_results:
            text = " ".join(camera_names)
            text = "all " + text
            ret = self.make_search_request(text, start_time)
            results = ret.get('result')
            if not results: return None
            logging.debug("gathering labels from %d buckets", len(results.get('buckets', [])))
            for index, bucket in enumerate(results.get('buckets')):
                logging.debug("bucket #%d - for date (%s) found labels: %r", index, bucket['earliest_date'], bucket.get('labels'))
                for frameidx, image in enumerate(bucket.get('images')):
                    logging.debug("\timage #%d - for date (%s) found labels: %r", frameidx, image['date_created'], image.get('labels'))
                    if labels.get(image['date_created']):
                        logging.debug("WARN - duplicate timestamps found, possible bug in iteration")
                    if not image.get('labels') or len(image['labels']) == 0:
                        continue
                    new_labels = image['labels']
                    if self.white_labels:
                        new_labels = [label for label in new_labels if label in self.white_labels]
                    labels[image['date_created']] = {
                        'labels': new_labels,
                        'camera': {
                            'name': image['source']
                        },
                    }
            # see if there are more results and if so shift the start time of the query to reflect the new range
            more_results = results.get('more_results', False)
            if more_results and results.get('latest_date_considered'): 
                start_time = dateutil.parser.parse(results.get('latest_date_considered'))
                if start_time > end_time: more_results = False
        return labels

    def gather_labels_batch(self):
        start, end = self.earliest_datetime, self.latest_datetime
        labels = dict(job_id=self.job_id, earliest_date=self.earliest_date, latest_date=self.latest_date, labels={})
        logging.info("gathering over time slot: %r to %r", start.isoformat(), end.isoformat())
        subset_labels = self.get_results_from_epoch(start, end, self.cameras)
        labels['labels'].update(subset_labels)
        logging.debug("\nall found labels:\n%r", json.dumps(labels))
        logging.info("finished gathering labels")
        return labels

    def dump_labels_to_file(self):
        logging.info("writing label info to file: %s", self.results_file)
        with open(self.results_file, 'w') as fh:
            fh.write(json.dumps(self.labels))
        logging.info("labels are now available in: %s", self.results_file)

    def run(self):
        try:
            self.parse_argv_or_exit()
            if not self.job_id:
                self.gather_all_job_data()
            self.job = self.gather_job_data()
            self.labels = self.gather_labels_batch()
            self.dump_labels_to_file()
        except Exception, e:
            logging.error("exception during main program flow")
            logging.error(traceback.format_exc())
            sys.exit(1)
        return  True

def main():
    return BatchDownloader().run()

if __name__ == '__main__':
    main()

