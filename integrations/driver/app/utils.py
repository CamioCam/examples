import argparse
import datetime
import logging
import pathlib
import traceback
import unittest
import time
from typing import Union

import requests
import yaml

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(20)


class Utils:

    @staticmethod
    def parse_args() -> dict:
        """
        Parses the command line arguments for an integration driver and returns them as a dict.
        """
        parser = argparse.ArgumentParser(description='Creates an integration driver which listens for devices and '
                                                     'events and forwards them to the Camio PACS server', )
        parser.add_argument("--config", type=str, help="Config file to be used to configure the driver", default=None)
        return vars(parser.parse_args())

    @staticmethod
    def read_config_file(config_filepath: str, use_absolute: bool = False):
        """
        Takes the path to a config file, reads it, and if the file has the yaml extension loads it as a dictionary.

        Args:
            config_filepath (str): path to the config file
            use_absolute (bool): if true, uses config_filepath as it is, else joins the config_filepath with where the
            configs are expected to be

        Returns:
            config loaded as a dictionary, else an error raised if file not found or invalid file type
        """
        if use_absolute:
            config_path = pathlib.Path(config_filepath)
        else:
            base_dir = pathlib.Path(__file__).parent.parent.joinpath('configs')
            config_path = pathlib.Path.joinpath(base_dir, config_filepath)

        if not config_path.exists():
            logger.error(f"Config file not found at {config_path}")
            raise ValueError(f"Config file not found at {config_path}")

        if str(config_filepath).endswith('.yaml'):
            with open(config_path, 'r') as inp:
                return yaml.safe_load(inp)
        else:
            raise TypeError("Config type not identified. Use [yaml]")

    @staticmethod
    def request_with_backoff(url: str,
                             request_kwargs: dict,
                             method=requests.post,
                             backoff_multiplier=2.0,
                             backoff_starter=2.0,
                             backoff_limit=3) -> Union[requests.Response, None]:
        """
        Perform a request with backoff attempts

        Args:
            url (str): url to make the request to
            request_kwargs (dict): kwargs to include when calling method
            method (): request method, default is POST
            backoff_multiplier (): multiplier for increasing the sleep between retries
            backoff_starter (): initial seconds until retry, gets multiplied by backoff_multiplier after each attempt
            backoff_limit (): maximum number of attempts to call the url

        Returns:
            Response from calling the url or None if failure
        """

        backoff = backoff_starter
        # logger.debug(f"Request headers: {request_kwargs.get('headers')}")
        for _ in range(backoff_limit):
            try:
                r = method(url, **request_kwargs)

                if r.ok:
                    logger.debug(f"Completed request with backoff to {url}")
                    return r

                elif r.status_code >= 500:
                    # if there was some sort of server error, maybe it was transient.
                    # raise a ConnectionError to instantiate retry logic
                    logger.error(f"Error on making call to {url}")
                    raise requests.ConnectionError(f"Received code {r.status_code} from server")
                else:
                    # if it's a 400 or some other error then we must be running bad code or have sent a
                    # bad payload, as we don't know how to correct the payload, we have to give up
                    logger.error(
                        f"Received an unrecoverable error from call to {url}")
                    logger.error(f"Error Details: {r.status_code}, {r}")
                    return None

            except requests.ConnectionError as e:
                logger.error("Failed to POST callback with requests error: %s", e)
                logger.error("Sleeping for %.2f seconds before retrying", backoff)
                time.sleep(backoff)
                backoff *= backoff_multiplier

            except Exception as e:
                logger.error("Unexpected and unrecoverable exception received when making callback request")
                logger.error(traceback.format_exc())
                return None

    @staticmethod
    def time_interval_has_passed(last_time: datetime.datetime, seconds: int, tz=None):
        """
        Args:
            last_time (datetime.datetime): compared to datetime.(utc)now to see if seconds have passed
            seconds (int): the desired number of seconds since last_time
            tz (): optional timezone to be passed into datetime.now

        Returns:
            True if x seconds have passed since last_time, else False. Also returns True if last_time is None.
        """
        if last_time is None:
            return True

        if tz is not None:
            now = datetime.datetime.now(tz=tz)
        else:
            now = datetime.datetime.utcnow()

        duration = now - last_time
        return duration.total_seconds() >= seconds


class TestUtils(unittest.TestCase):

    def test_request_with_backoff(self):
        response = Utils.request_with_backoff(url="https://test.camio.com/does/not/exist", request_kwargs={},
                                              method=requests.get)
        self.assertIsNone(response)

        response = Utils.request_with_backoff(url="https://test.camio.com/home", request_kwargs={},
                                              method=requests.get)
        self.assertIsNotNone(response)

    def test_read_config_file(self):
        self.assertRaises(ValueError, Utils.read_config_file, config_filepath="does_not_exist.yaml")

    def test_time_interval_has_passed(self):
        last_time = None
        num_seconds = 10
        self.assertTrue(Utils.time_interval_has_passed(last_time, num_seconds))

        last_time = datetime.datetime.utcnow()
        self.assertFalse(Utils.time_interval_has_passed(last_time, num_seconds))
        time.sleep(num_seconds)
        self.assertTrue(Utils.time_interval_has_passed(last_time, num_seconds))
