import datetime
from typing import List, Union, Optional

import pytz
import requests
import json as Serializable

from pydantic.error_wrappers import ValidationError
from requests import Response

from abc_fitness_schemas import ABCFitnessIntegrationDriverConfig, ABCFitnessEventsPayload, ABCFitnessMembersPayload
from base import BaseIntegrationDriver, TestBaseIntegrationDriver
from schemas import PACSEvent
from utils import Utils


class ABCFitnessIntegrationDriver(BaseIntegrationDriver):
    """
    The ABC Fitness integration driver. Handles specific methods for converting ABC Fitness events and devices into Camio
    PACS events and devices. Also handles creating the payloads for and making authenticated requests to the ABC Fitness
    API.
    """

    DESC_MAP = {
        'Normal Entry': 'Entry Unlocked',
        'Entry Allowed': 'Entry Unlocked'
    }

    def __init__(self, config_class=ABCFitnessIntegrationDriverConfig, **kwargs):
        super(ABCFitnessIntegrationDriver, self).__init__(config_class=config_class, **kwargs)
        self.last_fetch_time = None

    @staticmethod
    def format_date_for_abc(date: datetime.datetime):
        """
        Returns the date string in the format expected by the ABC Fitness API. Ex: 2024-07-01 23:50:00.000000
        """
        return date.strftime('%Y-%m-%d %H:%M:%S.%f')

    def create_auth_payload(self) -> str:
        """
        Requests to the ABC Fitness API are authenticated using the app_id, app_key, and club_id which are included
        in the url and as headers. No auth payload is required.
        """
        pass

    def start_authenticated_session(self, method=requests.post, headers=None, **kwargs):
        """
        Requests to the ABC Fitness API are authenticated using the app_id, app_key, and club_id which are included
        in the url and as headers. No request to start an authenticated session is required.
        """
        pass

    def parse_authentication_response(self, response: Response) -> bool:
        """
        Requests to the ABC Fitness API are authenticated using the app_id, app_key, and club_id which are included
        in the url and as headers. No request to start an authenticated session is required so there is no need to parse
        a response from the authentication url.
        """

        return True

    def authenticated_request(self, url: str, method=requests.get, data: str = None, member_id: str = None, **kwargs) \
            -> Union[requests.Response, None]:
        """
        Makes an authenticated request to the ABC Fitness API by including the app_key and app_id in the request Headers.

        Args:
            url (str): Url to send the request to, will be formatted with club_id
            method (): Request method (requests.POST, requests.GET, etc.)
            data (str): (optional) String representation of the content to send.
            member_id (str): (optional) Include if the member_id is part of the url itself and not a parameter
            kwargs (): passed in to request e.g. method(**kwargs). For example, can include params

        Returns:
            response from calling the ABC Fitness API
        """

        formatted_url = url.format(club_id=self.credentials.club_id, member_id=member_id)

        headers = {
            "app_key": self.credentials.app_key,
            "app_id": self.credentials.app_id,
            "accept": "application/json;charset=UTF-8"  # Important else returns as XML
        }
        self.logger.info(f"Making request to ABCFitness API with url: {formatted_url} and payload: {data}")
        response = method(formatted_url, headers=headers, json=data, **kwargs)
        self.logger.info(f"ABCFitness API response: {response.status_code} ({response.reason})")
        return response

    def convert_to_pacs_devices(self, response: requests.Response = None,
                                devices_str: str = None) -> Union[List[dict], None]:
        """
        Not implemented for ABC Fitness.
        """

        return None

    def get_iso_date_from_timestamp(self, timestamp: str):
        """
        Expected timestamp format: YYYY-MM-DD HH:MM:SS.ff
        Example: "2016-10-31 10:00:00.00"

        Args:
            timestamp (str): String representation of the time of the event

        Returns:
            ISO UTC date string as parsed from the timestamp. Format: %Y-%m-%dT%H:%M:%SZ. Raises value error if fails
            to parse the timestamp.
        """
        if not timestamp:
            return None

        try:
            self.logger.debug(f"Parsing timestamp {timestamp} with timezone {self.events_timezone}")

            # Parse the input date string
            input_date = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')

            localized_date = self.events_timezone.localize(input_date)

            # Convert to UTC
            utc_date = localized_date.astimezone(pytz.UTC)

            # Format the UTC date in ISO8601 format
            date_string = utc_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            return date_string
        except ValueError as e:
            self.logger.error(f"Error parsing date: {e}")
            raise e

    def get_members(self, member_ids: List[str], page: int = 1) -> Optional[ABCFitnessMembersPayload]:
        """
        Retrieves the member info for each of the passed memeber_ids. This includes member name and email address.
        """
        if not member_ids:
            self.logger.warning("Member ids is None")
            return None

        size = self.requests_config.members.page_size
        self.logger.info(f"Fetching member info of {len(member_ids)} members, page {page}, with size {size}")
        params = {
            "memberIds": ",".join(member_ids),
            "page": page,
            "size": size
        }
        response = self.authenticated_request(url=self.urls.members, params=params)
        if self.response_ok(response):
            response_dict = Serializable.loads(response.text)
            payload_obj = ABCFitnessMembersPayload(**response_dict)
            return payload_obj

    def convert_to_pacs_events(self, response: requests.Response = None,
                               events_str: str = None) -> Union[List[PACSEvent], None]:
        """
        Converts the response from ABC Fitness checkins (/clubs/checkins/details) to Camio PACSEvents.

        Args:
            response (Response): response from calling events_url
            events_str (str): text to convert to PACSEvents

        Returns:
            List of converted PACSEvents as dicts, or None if no events found
        """
        if response is None and events_str is None:
            raise ValueError(f"Response or events is required to convert to PACS events")

        if response is not None:
            events_str = response.text

        self.logger.debug(f"Received events payload of length {len(events_str)}")

        response_dict = Serializable.loads(events_str)
        payload = ABCFitnessEventsPayload(**response_dict)
        pacs_events = []

        for checkin in payload.checkins:
            station_name = checkin.stationName
            if station_name is None:
                self.logger.warning(f"No station name found for check-in with ID: {checkin.checkInId}. Skipping.")
                continue

            try:
                event_type = self.DESC_MAP.get(checkin.checkInStatus,
                                               None)  # Get supported PACS event_type from the ABC check in status
                labels = []
                # Only add fields to the labels if they are not None, otherwise a schema validation error occurs
                # These values become searchable in the Camio app
                for field in [checkin.checkInStatus, checkin.checkInMessage]:
                    if field is not None:
                        labels.append(field)

                pacs_event = PACSEvent(device_id=station_name,
                                       timestamp=self.get_iso_date_from_timestamp(checkin.checkInTimestamp),
                                       event_type=event_type,
                                       actor_id=checkin.member.memberId if checkin.member else None,
                                       labels=labels)

                self.logger.debug(f"Parsed ABCFitness event as PACSEvent: {pacs_event}")
                pacs_events.append(pacs_event)

            except ValidationError as e:
                self.logger.error(f"Error converting ABCFitness event to PACSEvent: {e}")
                continue  # continue for best effort reading events

        self.logger.info(f"{len(pacs_events)} PACS events created from {len(payload.checkins) if payload.checkins else 0} checkins")
        return pacs_events

    def end_authenticated_session(self) -> bool:
        """
        Since the ABC Fitness API does not require starting an authenticated session, this method just returns True.
        """

        return True

    def get_devices(self, method=requests.get, **kwargs) -> Union[List[dict], None]:
        """
        Not implemented for ABC Fitness.
        """

        return None

    def get_events(self, method=requests.get, **kwargs) -> Union[List[dict], Response, None]:
        """
        Makes an authenticated request to events_url then converts the response to a list of Camio PACS events.
        Overrides the default get_events method in order to use pagination. Continues calling the checkins endpoint
        until the ABC Fitness API returns that there is no next page.

        Args:
            method (): method to use to make the call to events_url, default is GET
            **kwargs (): passed into the call to authenticated_request

        Returns:
            List of PACSEvents (dict representation) or None if could not get events
        """

        if self.events_url is None:
            self.logger.error("Cannot fetch events, events_url is None")
            return None

        page = 1
        pacs_events = []
        now = datetime.datetime.utcnow()
        if not self.last_fetch_time:
            # If never fetched events before, set last fetch time to now - the event polling interval
            # e.g. if polling every 12 hours, fetch the last 12 hours of checkins on start
            self.last_fetch_time = now - datetime.timedelta(seconds=self.events_polling_interval)
            self.logger.info(f"First time fetching checkins. Retrieving checks from {self.last_fetch_time} to now ({now})")

        start_time_formatted = self.format_date_for_abc(self.last_fetch_time)
        end_time_formatted = self.format_date_for_abc(now)

        while True:
            params = {
                "size": self.requests_config.events.page_size,
                "page": page,
                "checkInTimestampRange": f"{start_time_formatted},{end_time_formatted}"
            }
            self.logger.info(f"Requesting checkins with parameters: {params}")
            events_response = self.authenticated_request(self.events_url, method=method,
                                                         data=self.create_get_events_payload(),
                                                         stream=self.stream_events,
                                                         params=params,
                                                         **kwargs)
            # Event streaming not supported for ABC Fitness

            if self.response_ok(events_response):
                pacs_events.extend(self.convert_to_pacs_events(response=events_response))

                response_dict = Serializable.loads(events_response.text)
                payload = ABCFitnessEventsPayload(**response_dict)

                # Continue requesting checkins until all checkins from the range have been retrieved
                if payload.status.nextPage:
                    page = payload.status.nextPage
                    continue

                # No more checkins to retrieve, break the loop
                else:
                    break

            else:
                self.logger.warning("Response from checkins endpoint not OK, breaking to avoid infinite loop")
                break

        # If get_member_info is true, get the member information for all members in the fetched checkin events
        if self.requests_config.events.get_member_info and len(pacs_events) > 0:
            self.logger.info(f"Retrieving member info for {len(pacs_events)} events")
            member_to_event_map = {}
            for pacs_event in pacs_events:
                if pacs_event.actor_id:
                    if pacs_event.actor_id in member_to_event_map:
                        member_to_event_map[pacs_event.actor_id].append(pacs_event)
                    else:
                        member_to_event_map[pacs_event.actor_id] = [pacs_event]

            self.logger.info(f"Found {len(member_to_event_map)} unique members")

            member_page = 1
            members = []
            while True:
                member_response_payload = self.get_members(list(member_to_event_map.keys()), page=member_page)

                if member_response_payload:
                    members.extend(member_response_payload.members)

                    # Continue requesting members until all requested members have been retrieved
                    if member_response_payload.status.nextPage:
                        member_page = member_response_payload.status.nextPage
                        continue

                    # No more members to retrieve, break the loop
                    else:
                        break

                else:
                    self.logger.warning("Response from members endpoint not OK, breaking to avoid infinite loop")
                    break

            # Once all member info has been fetched, use to populate the pac events
            for member in members:
                member_id = member.memberId
                member_pacs_events = member_to_event_map.get(member_id, [])
                self.logger.debug(f"Adding member {member_id} info to {len(member_pacs_events)} events")
                for pacs_event in member_pacs_events:
                    pacs_event.actor_name = member.get_actor_name()
                    pacs_event.actor_email = member.get_actor_email()

        self.logger.debug(f"PACSEvents are now: {pacs_events}")
        self.last_fetch_time = now
        return [pacs_event.dict() for pacs_event in pacs_events]


def main():
    """
    Gets the config filepath from the command line args. Reads the config and passes the values into the driver then
    starts running the driver. Note: This will run infinitely unless an error occurs such as a bad config value.
    """
    args = Utils.parse_args()
    config_filepath = args.get("config")
    if config_filepath is not None:
        kwargs = Utils.read_config_file(config_filepath, use_absolute=True)
    else:
        kwargs = {}  # If not using a config file, add dict config here

    driver = ABCFitnessIntegrationDriver(**kwargs)
    driver.run()  # loop creation happens in run


if __name__ == "__main__":
    main()


class TestABCFitnessDriver(TestBaseIntegrationDriver):
    """
    Tests for the ABC Fitness driver. Overrides the necessary methods from TestBaseIntegrationDriver to be specific to ABC Fitness.
    Note that some of the tests may take a while (depending on polling intervals set in the test config). I recommend
    keeping all polling_intervals under 30 seconds for test.
    Requires either a config file in configs/test/abc_fitness_config.yaml or a config filepath passed in when running the
    tests via the command line.

    The config file should contain all of the usual values of the ABC Fitness driver as well as:

    test_values:
      create_events_url: "https://api.abcfinancial.com/rest/{club_id}/members/checkins/{member_id}"  # This endpoint must be enabled in the account's ABC Fitness API
      station_id: "INSERT TEST STATION ID"  # For tests to pass this MUST be a real station id mapped to a camera in the user's Camio PACS integration settings
      member_id: "INSERT TEST MEMBER ID"  # For tests to pass this MUST be a real member id. NOTE: The member used for testing may receive tailgating notification emails
    """
    _defaults = {
        "test_config_filepath": "./test/abc_fitness_config.yaml",
    }

    async def asyncSetUp(self) -> None:
        await super(TestABCFitnessDriver, self).asyncSetUp()
        self.member_id = self.test_values.get("member_id", None)

    def setup_driver(self, **kwargs):
        """Override for specific driver class tests"""
        return ABCFitnessIntegrationDriver(**kwargs)

    def create_test_event_payload(self):
        """
        Returns the payload to be sent with the request to create a checkin.
        """

        payload = {
            "clubNumber": self.driver.credentials.club_id,
            "memberId": self.member_id,
            "checkins": [
                {
                    "access": {
                        "locationTimestamp": self.driver.format_date_for_abc(datetime.datetime.utcnow()),
                        "allowed": "true",
                        "stationId": self.test_values.get("station_id")
                    }
                }
            ]
        }
        return payload

    async def create_test_events(self, num_test_events: int = 1, task_names: List[str] = None, **kwargs):
        """
        This will fail if self.member_id is None.
        """
        return await super(TestABCFitnessDriver, self).create_test_events(num_test_events=num_test_events,
                                                                          task_names=task_names,
                                                                          member_id=self.member_id)

    def test_get_devices(self):
        """
        ABC Fitness driver does not fetch devices.
        """
        self.assertIsNone(self.driver.last_devices_fetch)
        devices = self.driver.get_devices()
        self.logger.info(f"Got devices: {devices}")
        self.assertIsNone(devices)
        self.assertIsNone(self.driver.last_devices_fetch)

    def test_get_and_forward_devices(self):
        """
        ABC Fitness driver does not fetch devices.
        """
        self.assertIsNone(self.driver.last_devices_fetch)
        response = self.driver.get_and_forward_devices()
        self.assertIsNone(response)
        self.assertIsNone(self.driver.last_devices_fetch)

    async def test_minimal_driver_config(self):
        """
        Test the driver schema taking the minimum required field.
        """

        # Currently, only the credential fields should be required
        config = {
            "credentials": {
                "app_key": "1",
                "app_id": "2",
                "club_id": "3",
                "camio_api_token": "4"
            }
        }

        # Raises an error if any required fields are missing
        driver_config = ABCFitnessIntegrationDriverConfig(**config)
        print(f"Driver config: \n{driver_config}")
        self.assertIsNotNone(driver_config)

        # Assert default urls are populated
        self.assertIsNotNone(driver_config.urls)
        # self.assertIsNotNone(driver_config.urls.devices)
        self.assertIsNotNone(driver_config.urls.events)
        self.assertIsNotNone(driver_config.urls.pacs_server)

        # Assert default polling intervals are populated
        self.assertIsNotNone(driver_config.requests)
        # self.assertIsNotNone(driver_config.requests.devices)
        # self.assertIsNotNone(driver_config.requests.devices.polling_interval)
        self.assertIsNotNone(driver_config.requests.events)
        self.assertIsNotNone(driver_config.requests.events.polling_interval)

    async def test_get_events(self):
        # Set last fetch time as now so that we only fetch the test events from now -> time of get_events
        self.driver.last_fetch_time = datetime.datetime.utcnow()
        await super(TestABCFitnessDriver, self).test_get_events()

    def test_date_conversion(self):
        # With timezone offset
        timestamp = "2016-10-31 10:00:00.000000"
        self.driver.events_timezone = self.driver.parse_timezone(timezone_offset="-0500")
        iso_date = self.driver.get_iso_date_from_timestamp(timestamp)
        self.assertEqual("2016-10-31T15:00:00Z", iso_date)

        # Error in timezone_offset falls back to UTC
        self.driver.events_timezone = self.driver.parse_timezone(timezone_offset="hello")
        iso_date = self.driver.get_iso_date_from_timestamp(timestamp)
        self.assertEqual("2016-10-31T10:00:00Z", iso_date)

        # With timezone name
        self.driver.events_timezone = self.driver.parse_timezone(timezone_offset=None, timezone_name="US/Pacific")
        self.driver.timezone = self.driver.parse_timezone()
        iso_date = self.driver.get_iso_date_from_timestamp(timestamp)
        self.assertEqual("2016-10-31T17:00:00Z", iso_date)

        # Error in timezone name falls back to UTC and logs timezones
        self.driver.events_timezone = self.driver.parse_timezone(timezone_offset=None, timezone_name="US")
        self.driver.timezone = self.driver.parse_timezone()
        iso_date = self.driver.get_iso_date_from_timestamp(timestamp)
        self.assertEqual("2016-10-31T10:00:00Z", iso_date)

        # Without timezone, parses as UTC
        self.driver.events_timezone = self.driver.parse_timezone(timezone_offset=None, timezone_name=None)
        iso_date = self.driver.get_iso_date_from_timestamp(timestamp)
        self.assertEqual("2016-10-31T10:00:00Z", iso_date)

        # Incorrect timestamp format raises errors
        timestamp = "2016-10-31 10:00:00"
        self.assertRaises(ValueError, self.driver.get_iso_date_from_timestamp, timestamp=timestamp)

    def test_get_events_payload(self):
        payload = self.driver.create_get_events_payload()
        self.assertIsNone(payload)