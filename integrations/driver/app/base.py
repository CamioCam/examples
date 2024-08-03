import asyncio
import datetime
import json
import logging
import random
import traceback
import unittest
from urllib.parse import urljoin, urlparse
from asyncio import Task
from time import sleep
from typing import Union, List

import pytz
import requests
from requests import Response

from schemas import PACSDevice, BaseIntegrationDriverConfig
from utils import Utils

logging.basicConfig()


class BaseIntegrationDriver:
    """
    Base class for integration drivers. Integration drivers periodically poll an integration API for devices and events.
    They then forwards the device and event information the the Camio PACS (Physical Access Control) API. This makes
    the access control events viewable and searchable in the Camio app.
    This class is not intended to be used directly, but instead should be extended for each specific integration.
    See the README in this directory for more details.
    """

    PACS_DEVICES_ENDPOINT = "devices"
    PACS_EVENTS_ENDPOINT = "webhooks"

    def __init__(self, config_class=BaseIntegrationDriverConfig, **kwargs):
        """
        Initial the integration driver. Validates the kwargs using the provided config schema. Starts an authenticated
        session with the integration's API.

        Args:
            config_class (BaseIntegrationDriverConfig or extension): the class to use to validate kwargs
            **kwargs (): the config as a dictionary to be passed into config_class for validation
        """

        self.config = config_class(**kwargs)

        # Set up logger
        self.logger = logging.getLogger()
        self.logger.setLevel(self.config.log_level)

        # Credentials
        self.credentials = self.config.credentials  # user_name, password or other
        self.camio_api_token = self.credentials.camio_api_token
        self.credentials_filepath = self.config.credentials_filepath
        self.auth_token = None  # response from authenticating TODO: Add auth token refresh rate?

        # URLS
        self.urls = self.config.urls
        self.auth_url = self.urls.auth
        self.devices_url = self.urls.devices
        self.events_url = self.urls.events
        self.logs_url = self.urls.logs
        self.stats_url = self.urls.stats
        self.pacs_server_url = self.urls.pacs_server
        self.skip_ssl_verification = self.urls.skip_ssl_verification

        # Requests config
        self.requests_config = self.config.requests

        # Devices request config
        self.devices_config = self.requests_config.devices
        self.devices_polling_interval = self.devices_config.polling_interval
        self.last_devices_fetch = None

        # Event request config
        self.events_config = self.requests_config.events
        self.stream_events = self.events_config.streaming
        self.events_polling_interval = self.events_config.polling_interval
        self.events_count_reset_interval = self.events_config.count_reset_interval
        self.last_events_count_reset = datetime.datetime.utcnow()  # setting last reset as time of initialization, since starts at 0
        self.events_forwarded_count = 0
        self.events_timezone = self.parse_timezone(self.events_config.timezone_offset, self.events_config.timezone_name)

        # PACS request config
        self.pacs_config = self.requests_config.pacs
        self.pacs_backoff_multiplier = self.pacs_config.backoff_multiplier
        self.pacs_backoff_starter = self.pacs_config.backoff_start
        self.pacs_backoff_limit = self.pacs_config.backoff_limit

        self.logger.debug(f"Set up integration driver using config: {self.config}")

    def parse_timezone(self, timezone_offset: str = None, timezone_name: str = None):
        """
        Parse timezone_offset/timezone_name using pytz, returns the timezone object. If both timezone_offset and
        timezone_name are provided, only offset is used. If an error occurs in parsing, falls back to UTC.
        """
        if timezone_offset is not None:
            # Extract the hours and minutes from the timezone offset
            try:
                if len(timezone_offset) < 3:
                    self.logger.error(f"Timezone offset {timezone_offset} needs to be at least length 3")
                    timezone = pytz.UTC

                else:
                    offset_sign = timezone_offset[0]  # Get the sign (+ or -)
                    offset_hours = int(timezone_offset[1:3])
                    offset_minutes = int(timezone_offset[3:])

                    # Calculate the total offset in minutes, considering the sign
                    total_offset_minutes = offset_hours * 60 + offset_minutes
                    if offset_sign == '-':
                        total_offset_minutes = -total_offset_minutes

                    # Create a timezone object with the calculated offset
                    timezone = pytz.FixedOffset(total_offset_minutes)
            except ValueError as e:
                self.logger.error(f"Error parsing timezone offset: {e}. Falling back to UTC.")
                timezone = pytz.UTC
            except Exception as e:
                self.logger.error(f"Unexpected error parsing timezone offset: {e}. Falling back to UTC.")
                timezone = pytz.UTC

        elif timezone_name is not None:
            # Use the provided timezone name
            try:
                timezone = pytz.timezone(timezone_name)
            except pytz.exceptions.UnknownTimeZoneError as e:
                self.logger.error(f"Error parsing time zone name {timezone_name}: {e}. Falling back to UTC.")
                all_timezones = '\n'.join(pytz.all_timezones)
                self.logger.error(f"The supported timezones are:\n{all_timezones}")
                timezone = pytz.UTC
            except Exception as e:
                self.logger.error(f"Unexpected error parsing time zone name {timezone_name}: {e}. Falling back to UTC.")
                all_timezones = '\n'.join(pytz.all_timezones)
                self.logger.error(f"The supported timezones are:\n{all_timezones}")
                timezone = pytz.UTC

        else:
            timezone = pytz.UTC

        self.logger.debug(f"Timezone parsed as: {timezone}")
        return timezone

    def create_auth_payload(self):
        """
        Payload to send in the request to the auth_url. If no payload needed, no need to override this method.
        """
        return None

    def start_authenticated_session(self, method=requests.post, headers: dict = None, **kwargs):
        """
        Authenticates this session with the integration API using the provided credentials. Response is parsed
        in order to get an auth_token which can be used in subsequent requests as auth. Essentially a "login" function.
        Override if auth will be handled differently. For example, if each call will include a username and password
        instead of exchanging for a token - override this method to pass and then write authenticated_request().

        Args:
            method (): method to use to make the request, default is POST
            headers (dict): headers to include in the request to auth_url, optional

        Returns:
            True if success starting authenticated session, else False
        """
        if headers is None:
            headers = {}

        self.logger.debug("Attempting to start authenticated session")

        if self.auth_url is None:
            self.logger.error("Cannot authenticate, auth_url is None")
            raise ValueError("Config must contain an auth url in order to authenticate requests")

        if all in [self.credentials_filepath is None, self.credentials is None]:
            self.logger.error("Cannot authenticate without credentials file or credentials dict.")
            raise ValueError("Config does not contain credentials or credentials_filepath")

        auth_payload = self.create_auth_payload()

        verify = not self.skip_ssl_verification
        response = method(self.auth_url, headers=headers, data=auth_payload, verify=verify, **kwargs)
        if not self.response_ok(response):
            self.logger.error(f"Error getting auth token, will be unable to make authenticated requests")
            return False

        return self.parse_authentication_response(response)

    def parse_authentication_response(self, response: Response) -> bool:
        """
        Parses the response from calling auth_url in order to get the auth_token.
        Each integration driver should override this function.
        If no parsing required, return True.

        Args:
            response (Response): the response from calling start_authenticated_session which call the auth_url

        Returns:
            True if success parsing response, else False
        """
        raise NotImplementedError

    def end_authenticated_session(self) -> bool:
        """
        Makes request to auth_url to invalidate current auth_token. Essentially a "logout" function.
        If request succeeds, auth_token will be set to None and will need to re-authenticate to continue making
        requests.

        Returns:
            True if success ending the session, else False
        """
        raise NotImplementedError

    def authenticated_request(self, url: str, method=requests.get, **kwargs) -> Union[requests.Response, None]:
        """
        Uses self.credentials to create an authenticated request to url. Should be overridden by each integration driver
        for their specific way of making authenticated requests.

        Args:
            url (str): url to make the request to
            method (): method to use to make the request, default is GET

        Returns:
            the requests.Response from calling url or None if unable to authenticate
        """
        raise NotImplementedError

    def response_ok(self, response: requests.Response) -> bool:
        """
        Only needs overriding if additional checks are needed to verify successful API call other than checking response.ok.
        For example, override if response status code is in response body (response.text) instead of response.status_code.

        Args:
            response (requests.Response): the response from calling authenticated_request

        Returns:
            True if response indicates a successful API call, False otherwise
        """
        if response is None:
            return False

        self.logger.debug(f"Call to {response.url} returned {response.status_code}: {response.reason}")
        return response.ok

    def create_get_devices_payload(self) -> str:
        """
        Payload to send in the request to the devices_url. If no payload needed, no need to override this method.

        Returns:
            The payload to be passed in as data to the request to the devices_url
        """
        return None

    def get_devices(self, method=requests.post, **kwargs) -> Union[List[dict], None]:
        """
        Makes an authenticated request to self.devices_url then converts the response to a list of Camio PACS devices.

        Args:
            method (): method to use to make the call to devices_url, default is POST
            **kwargs (): passed into the call to authenticated_request

        Returns:
            List of PACSDevices (dict representation) or None if could not get devices
        """
        if self.devices_url is None:
            self.logger.error("Cannot fetch devices, devices_url is None")
            return None

        self.logger.info("Fetching devices")
        devices_response = self.authenticated_request(self.devices_url, method=method,
                                                      data=self.create_get_devices_payload(), **kwargs)

        if self.response_ok(devices_response):
            pacs_devices = self.convert_to_pacs_devices(response=devices_response)
            # Update last_devices_fetch if success getting the pacs devices
            # If !response.okay, will then immediately re-try getting devices on next loop iteration
            self.last_devices_fetch = datetime.datetime.utcnow()
            return pacs_devices
        else:
            return None

    def get_and_forward_devices(self, **kwargs) -> Union[requests.Response, None]:
        """
        Get the PACS devices by calling the devices_url and then forward them to the Camio PACS API.

        Args:
            **kwargs (): passed into the request to get_devices

        Returns:
            response from forwarding to the Camio pacs api, or None if no devices were found
        """
        pacs_devices = self.get_devices(**kwargs)

        if isinstance(pacs_devices, List) and len(pacs_devices) > 0:
            self.logger.info(
                f"Forwarding {len(pacs_devices)} device{'s' if len(pacs_devices) > 1 else ''} to the PACS server")
            payload = {"readers": pacs_devices}
            return self.send_to_pacs_server(endpoint=self.PACS_DEVICES_ENDPOINT, data=json.dumps(payload))

        else:
            self.logger.warning("No devices to forward")

    async def get_and_forward_devices_loop(self):
        """
        Infinite loop of getting devices and forwarding to the Camio PACS API. Sleeps after each get in order to yield
        back to the asyncio event loop (to continue getting events).
        """
        while True:
            try:
                self.get_and_forward_devices()
            except Exception as e:  # Don't let errors fetching devices block getting events
                self.logger.error(e)

            await asyncio.sleep(0)

    def convert_to_pacs_devices(self, response: requests.Response = None,
                                devices_str: str = None) -> Union[List[dict], None]:
        """
        Converts the response from calling the integration's devices_url into a list of Camio PACS devices, to be
        forwarded to the Camio PACS API. Needs to be overridden by each specific integration driver.

        Args:
            response (Response): response from calling the devices_url, either this or devices_str is required
            devices_str (str): string representation of the integration devices to be converted to PACSDevices

        Returns:
            List of Camio PACSDevices (dict representation so can be json dumped), or None if no devices found
        """
        raise NotImplementedError

    def is_time_to_get_devices(self) -> bool:
        """
        Returns:
            True if it has been devices_polling_interval seconds since last_devices_fetch
        """
        return Utils.time_interval_has_passed(self.last_devices_fetch, self.devices_polling_interval)

    def is_time_to_reset_event_count(self) -> bool:
        """
        Returns:
            True if it has been events_count_reset_interval seconds since last_events_count_reset
        """
        return Utils.time_interval_has_passed(self.last_events_count_reset, self.events_count_reset_interval)

    def reset_event_count(self):
        """
        Logs and then resets the events_forwarded_count to 0. Sets last_events_count_reset to now
        """
        self.logger.info(f"Resetting event count from {self.events_forwarded_count} to 0 after "
                         f"{self.events_count_reset_interval} seconds")
        self.events_forwarded_count = 0
        self.last_events_count_reset = datetime.datetime.utcnow()

    def create_get_events_payload(self):
        """
        Payload to send in the request to the events_url. If no payload needed, no need to override this method.

        Returns:
            The payload to be passed in as data to the request to the devices_url
        """
        return None

    def get_events(self, method=requests.post, **kwargs) -> Union[List[dict], Response, None]:
        """
        Makes an authenticated request to events_url then converts the response to a list of Camio PACS events.

        Args:
            method (): method to use to make the call to events_url, default is POST
            **kwargs (): passed into the call to authenticated_request

        Returns:
            List of PACSEvents (dict representation) or None if could not get events
            Alternatively returns the response object if event streaming
        """
        if self.events_url is None:
            self.logger.error("Cannot fetch events, events_url is None")
            return None

        events_response = self.authenticated_request(self.events_url, method=method,
                                                     data=self.create_get_events_payload(),
                                                     stream=self.stream_events,
                                                     **kwargs)
        if self.stream_events:
            return events_response

        if self.response_ok(events_response):
            return self.convert_to_pacs_events(response=events_response)
        else:
            return None

    def __forward_converted_events(self, pacs_events: List[dict]) -> bool:
        """
        Checks the pacs_events and then sends them to the Camio PACS API

        Args:
            pacs_events (List[dict]): a list of dict representations of PACSEvents

        Returns:
            True if successfully sent all events, else False
        """
        previous_count = self.events_forwarded_count
        success = True
        if isinstance(pacs_events, List) and len(pacs_events) > 0:
            self.logger.info(
                f"Forwarding {len(pacs_events)} event{'s' if len(pacs_events) > 1 else ''} to the PACS server")

            # Send all events in a batch
            payload = {
                "events": pacs_events
            }
            pacs_response = self.send_to_pacs_server(endpoint=self.PACS_EVENTS_ENDPOINT,
                                                     data=json.dumps(payload))
            if pacs_response is not None and pacs_response.ok:
                self.events_forwarded_count += len(pacs_events)
            else:
                success = False

            events_sent = self.events_forwarded_count - previous_count
            self.logger.info(f"Successfully forwarded {events_sent} event{'s' if events_sent > 1 else ''}")
            return success

        else:
            return False

    async def get_and_forward_events(self, **kwargs) -> Union[Response, bool, None]:
        """
        Calls the events_url to get the integration events, converts them to Camio PACSEvents, and sends them to the
        Camio PACS API.

        Args:
            **kwargs (): included in call to get_events

        Returns:
            response from forwarding to pacs server, or None if no events were found
            alternatively, if event streaming, iterates over the streamed response (infinitely so long as response
            lines come in), and returns None
        """
        pacs_events = self.get_events(**kwargs)

        if self.stream_events:
            response = pacs_events
            if response is not None and response.ok:
                self.logger.info("Starting to iterate over event streaming response")
                for event in response.iter_lines():  # Iterate over lines streaming in to the response

                    if self.is_time_to_get_devices():
                        self.logger.debug("Yielding to get devices")
                        await asyncio.sleep(0)

                    if self.is_time_to_reset_event_count():
                        self.reset_event_count()

                    # Filter out keep-alive new lines
                    if event:
                        try:
                            pacs_events = self.convert_to_pacs_events(events_str=event)
                            self.__forward_converted_events(pacs_events)

                        except Exception as e:
                            self.logger.error(f"Error reading streaming response: {e}")
                            # Continue for best effort

        if isinstance(pacs_events, List) and len(pacs_events) > 0:
            return self.__forward_converted_events(pacs_events)

        else:
            self.logger.info("No events to forward")

    async def get_and_forward_events_loop(self, **kwargs):
        """
        Infinite loop of getting events and forwarding to the Camio PACS API. Sleeps when it is time to get devices in
        order to yield the asyncio event loop. Also checks if it is time to reset the event count after each get.

        Args:
            **kwargs (): passed in to get_and_forward_events
        """
        while True:
            try:
                await self.get_and_forward_events(**kwargs)  # Note: If event streaming, this step can run infinitely

                if not self.stream_events:
                    if self.is_time_to_get_devices():
                        self.logger.debug("Yielding to get devices.")
                        await asyncio.sleep(0)

                    if self.is_time_to_reset_event_count():
                        self.reset_event_count()

                sleep(self.events_polling_interval)

            except Exception as e:  # Continue for best effort, if event streaming fails this also ensures a re-try
                self.logger.error(f"Error getting and forwarding events: {e}")
                self.logger.error(traceback.format_exc())

    def convert_to_pacs_events(self, response: requests.Response = None,
                               events_str: str = None) -> Union[List[dict], None]:
        """
        Converts the response from calling the events endpoint into a list of Camio PACS events, to be
        forwarded to the Camio PACS API. Needs to be overridden by each specific integration driver.

        Args:
            response (Response): response from calling the events_url, either this or events_str is required
            events_str (str): string representation of the integration events to be converted to PACSEvents

        Returns:
            List of Camio PACSEvents (dict representation so can be json dumped), or None if no events found
        """
        raise NotImplementedError

    def get_logs(self):
        """TODO: Implement"""
        raise NotImplementedError

    def get_stats(self):
        """TODO: Implement"""
        raise NotImplementedError

    def get_version(self):
        """ Gets the version of the access control system TODO: Implement """
        raise NotImplementedError

    def send_to_pacs_server(self, endpoint: str = None, method=requests.post, data=None,
                            **kwargs) -> Union[Response, None]:
        """
        Sends a request to the Camio PACS API to add the events or devices to the Camio system.

        Args:
            endpoint (str): specific PACS endpoint to call, prepended to pacs_server_url, e.g. /devices or /webhooks
            method (): method to use to make the request, default is POST
            data (): included in the request as the data field
            **kwargs (): included as request_kwargs in the call to request_with_backoff

        Returns:
            response from making a request to the PACS server or None if request can't be made
        """
        if self.pacs_server_url is None:
            self.logger.error("Cannot send to pacs server, url is None")
            return None

        url = self.pacs_server_url

        if endpoint is not None:
            if url[-1] != "/":  # This is necessary because otherwise urljoin will override the last section of the path
                url = f"{url}/"

            url = urljoin(url, endpoint)

        request_kwargs = {"data": data, **kwargs}

        if self.camio_api_token is not None:
            # join passed in headers with the Auth header, preferring the passed in headers
            request_kwargs["headers"] = {"Authorization": f"Bearer {self.camio_api_token}",
                                         **request_kwargs.get("headers", {})}

        response = Utils.request_with_backoff(url=url, method=method, request_kwargs=request_kwargs,
                                              backoff_limit=self.pacs_backoff_limit,
                                              backoff_starter=self.pacs_backoff_starter,
                                              backoff_multiplier=self.pacs_backoff_multiplier)
        if response is not None:
            self.logger.debug(f"Request to pacs server returned {response.status_code}: {response.reason}")

        return response

    def run(self):
        """
        Starts the devices and events tasks, both of which should run infinitely.
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.get_and_forward_devices_loop(), name="devices_loop")
        loop.create_task(self.get_and_forward_events_loop(), name="events_loop")

        if not loop.is_running():  # Covers already running test loop
            try:
                self.logger.info("Beginning driver loop")
                loop.run_forever()  # Calling run forever keeps the script (and the asyncio event loop) running,
                # otherwise the script would just end
            finally:
                self.logger.warning("Asyncio event loop has ended, closing")
                loop.close()


class TestBaseIntegrationDriver(unittest.IsolatedAsyncioTestCase):
    """
    Tests for the integration drivers.

    The base tests on their own won't pass. To test a specific integration driver, extend this class and override the
    test_config_filepath in _defaults as well as the setup_driver() function.

    The tests will automatically determine from the config whether to test event streaming or batch fetches.
    """

    _defaults = {
        "test_config_filepath": "",
    }

    async def asyncSetUp(self) -> None:
        """
        Sets up the integration driver using the config passed in or the default config filepath.
        """
        self.loop = asyncio.get_event_loop()
        self.logger = logging.getLogger()
        self.logger.info("---------- SET UP -------------")

        # Read the config values
        args = Utils.parse_args()
        config_filepath = args.get("config") if args.get("config") is not None else self._defaults.get(
            "test_config_filepath")
        if config_filepath is not None:
            self.kwargs = Utils.read_config_file(config_filepath)
        else:
            self.fail("Need a config file to run tests")

        # Create driver using the config values as arguments
        self.driver = self.setup_driver(**self.kwargs)

        # Any additional test values from the config
        self.test_values = self.kwargs.get("test_values", {})
        self.create_events_url = self.test_values.get("create_events_url", self.driver.events_url) if self.test_values else None

        self.logger.info("---------- END SET UP -------------")
        self.logger.info("---------- TESTS -------------")

    def setup_driver(self, **kwargs):
        """ Override for specific driver class tests """
        return BaseIntegrationDriver(**kwargs)

    async def asyncTearDown(self):
        self.logger.info("---------- END TESTS -------------")
        self.logger.info("---------- TEAR DOWN -------------")
        session_ended = self.driver.end_authenticated_session()
        self.assertTrue(session_ended)
        self.logger.info("---------- END TEAR DOWN -------------")

    def create_test_event_payload(self) -> str:
        """
        Override to include a body in the request to create test events.

        Returns:
            String to be included as the request data
        """
        return None

    async def create_test_events(self, num_test_events: int = 1, task_names: List[str] = None, **kwargs):
        """
        Makes a request to the integration API to make test events. To set this up make sure you override
        create_test_event_payload and test_values.create_events_url in your driver's config if not the same url as your
        driver's events_url.

        Args:
            task_names (List[str]): optional, names of asyncio tasks to cancel after sending test events
            num_test_events (int): number of test events to send, default is 1

        Returns:

        """
        payload = self.create_test_event_payload()
        self.log_current_tasks()

        if self.driver.stream_events:
            self.logger.info("Ready to send test events once event streaming has started")
            self.logger.info("Yielding event loop to start streaming")
            await asyncio.sleep(0)

        self.logger.info("Sending test events")
        for i in range(1, num_test_events + 1):
            self.logger.info(f"Sending test event {i} of {num_test_events}")
            response = self.driver.authenticated_request(self.create_events_url, method=requests.post, data=payload, **kwargs)
            ok = self.driver.response_ok(response)
            self.assertTrue(ok)

        self.driver.last_devices_fetch = datetime.datetime.utcnow()  # update last devices fetch so that stream_events won't prematurely yield

        self.logger.info("Yielding event loop to get new events")
        await asyncio.sleep(0)

        self.log_current_tasks()
        if task_names is not None:
            self.cancel_tasks(task_names=task_names)

    async def test_send_events(self):
        await self.create_test_events(10)

    def log_current_tasks(self):
        """
        Logs all of the current asyncio tasks and whether they are currently running or waiting.
        """
        all_tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()
        self.logger.info("---------- TASKS ----------")
        for task in all_tasks:
            current = task.get_name() == current_task.get_name()
            self.logger.debug(
                f"\t {task.get_name()}: {'cancelled' if task.cancelled() else ('running' if current else 'waiting')}")
        self.logger.info("---------------------------")

    def get_task_by_name(self, name: str) -> Union[Task, None]:
        """
        Args:
            name (str): Name of the task to return

        Returns:
            Asyncio Task if found, else None
        """

        all_tasks = asyncio.all_tasks()

        for task in all_tasks:
            if task.get_name() == name:
                return task

        return None

    def cancel_tasks(self, task_names: List[str]):
        """
        Gets the asyncio tasks with names in task_names and cancels them. Will only attempt to cancel if an uncancelled
        task by that name if found.

        Args:
            task_names (List[str]): names of asyncio tasks to be cancelled
        """
        for name in task_names:
            self.logger.info(f"Attempting to cancel task {name}")
            task = self.get_task_by_name(name)

            if task is not None and not task.cancelled():
                task.cancel()
            else:
                self.fail("Cannot cancel if task doesn't exist or is already cancelled.")

    def test_auth(self):
        """
        Tests that an authenticated session has been started. Override if not using auth_token for auth.
        """
        auth_response = self.driver.start_authenticated_session()
        # If the driver urls contain an auth url, assume an auth_response and auth_token are required
        if self.driver.urls.auth:
            self.assertTrue(auth_response)
            self.assertIsNotNone(self.driver.auth_token)

        # Else assume the auth_response should be None
        else:
            self.assertIsNone(auth_response)

    def test_get_devices(self):
        """
        Tests retrieving integration devices.
        """
        self.assertIsNone(self.driver.last_devices_fetch)
        devices = self.driver.get_devices()
        self.logger.info(f"Got devices: {devices}")
        self.assertIsNotNone(devices)
        self.assertGreater(len(devices), 0)
        self.assertIsNotNone(self.driver.last_devices_fetch)

    def test_get_and_forward_devices(self):
        """
        Tests retrieving integration devices and forwarding them to the Camio PACS server.
        """
        self.assertIsNone(self.driver.last_devices_fetch)
        response = self.driver.get_and_forward_devices()
        self.assertIsNotNone(response)
        self.assertTrue(response.ok)
        self.assertIsNotNone(self.driver.last_devices_fetch)

    def test_reset_events_count(self):
        """
        Tests the functions for resetting the events forwarded count on the set interval.
        Does not test an actual reset happening during run().
        """
        test_reset_interval = 10  # seconds

        # Check intial setup is good
        original_last_reset = self.driver.last_events_count_reset
        self.assertIsNotNone(original_last_reset)
        self.assertFalse(self.driver.is_time_to_reset_event_count())

        # Check methods function correctly after reset interval has passed
        self.driver.events_count_reset_interval = test_reset_interval  # override driver's reset interval for just this test
        self.driver.events_forwarded_count = 100  # override count to mock having sent a bunch of events
        sleep(test_reset_interval)
        self.assertTrue(self.driver.is_time_to_reset_event_count())
        self.driver.reset_event_count()
        self.assertEqual(self.driver.events_forwarded_count, 0)
        self.assertIsNotNone(self.driver.last_events_count_reset)
        self.assertNotEqual(original_last_reset, self.driver.last_events_count_reset)

    async def test_get_events(self):
        """
        Test getting and forwarding the integration events. If event streaming is enabled this test can take a while,
        since it will start event streaming, send events, and wait for the events to come into the streaming response.
        Relies on the yields in the BaseIntegrationDriver to function properly.

        You can lower the polling_interval for devices/events to potentially speed up this test.
        """
        devices_response = self.driver.get_and_forward_devices()  # Populate portal map before testing events
        self.assertIsNotNone(devices_response)

        num_test_events = random.randint(5, 10)

        if self.create_events_url:
            if self.driver.stream_events:
                create_test_events = asyncio.create_task(
                    self.create_test_events(num_test_events=num_test_events, task_names=["events_loop"]),
                    name="create_test_events")  # Streaming, so first schedule event creation
                stream_events_task = asyncio.create_task(self.driver.get_and_forward_events(), name="events_loop")

                try:
                    await asyncio.gather(create_test_events, stream_events_task)
                except asyncio.exceptions.CancelledError:
                    pass

            else:
                await self.create_test_events(num_test_events=num_test_events)
                await self.driver.get_and_forward_events()

            self.assertEqual(num_test_events, self.driver.events_forwarded_count)

        else:
            self.fail("Cannot test getting events without a url to create events")

    async def test_run(self):
        """
        Tests the continuous event and devices fetching that occurs in run(). If event streaming is enabled this test
        can take a while, since it will start event streaming, send events, and wait for the events to come into the
        streaming response. Relies on the yields in the BaseIntegrationDriver to function properly.

        You can lower the polling_interval for devices/events to potentially speed up this test.
        """
        num_test_events = random.randint(5, 10)

        self.driver.run()  # Creates and starts processing the events and devices tasks
        create_test_events = self.loop.create_task(
            self.create_test_events(num_test_events=num_test_events, task_names=["devices_loop", "events_loop"]),
            name="create_test_events")  # Schedules task to create test event(s)

        try:
            await asyncio.gather(create_test_events)
        except asyncio.exceptions.CancelledError:
            pass

        self.assertEqual(num_test_events, self.driver.events_forwarded_count)
        self.assertIsNotNone(self.driver.last_devices_fetch)
