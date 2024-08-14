import logging
from typing import Literal, Dict, Optional

from pydantic import BaseModel, Field, conlist, Extra


class PACSDevice(BaseModel):
    """
    Schema for a Camio PACS Device, used when calling the Camio PACS API to store devices.
    """

    device_id: str
    device_name: str = None


class PACSEvent(BaseModel):
    """
    Schema for a Camio PACS Event, used when calling the Camio PACS API to annotate Camio events with access control
    event data.
    """

    device_id: str = Field(description="PACS device id (such as a door's reader ID), used to determine which cameras "
                                       "may have matching Camio events")
    timestamp: str = Field(
        description="String representation of the datetime that the PACS event occurred, used to determine matching Camio events. ISO8601 format.")
    event_type: str = Field(None, description="PACS event type (such as entry_unlocked) to be converted into a label")
    actor_name: str = Field(None,
                            description="Name of the person in the PACS event, to be converted into a label if included")
    actor_id: str = Field(None,
                          description="ID of the person in the PACS event, to be converted into a label if included")
    actor_email: str = Field(None,
                             description="Email address of the person in the PACS event. Enable tailgating notifications.")
    labels: conlist(str, min_items=0) = Field(None,
                                              description="Any labels to be added to matching Camio events, in addition"
                                                          " to constructed labels")


class BaseCredentials(BaseModel, extra=Extra.allow):
    """
    Contains the credentials used to authenticate requests with the integration's API.
    """
    camio_api_token: str = Field(None,
                                 description="If included, is added as a bearer token to the request to the Camio PACS server")


class BaseUrls(BaseModel, extra=Extra.allow):
    """
    Contains the full urls for each request type. Some urls are optional.
    """
    auth: str = Field(None, description="Url to call to start an authenticated session with the integration API")
    devices: str = Field(description="Url to call to get the user's integration devices e.g. card readers, stations, doors, etc.")
    events: str = Field(description="Url to call to get the user's integration events e.g. badge ins, check ins, etc.")
    pacs_server: str = Field(
        description="Url to forward the devices and events to once they have been converted to PACS format")
    logs: str = Field(None, description="Optional because unimplemented for now")
    stats: str = Field(None, description="Optional because unimplemented for now")
    skip_ssl_verification: bool = Field(False, description="If true, use verify=False when requesting integration API")


class BaseRequestConfig(BaseModel, extra=Extra.allow):
    pass


class BaseDevicesRequestConfig(BaseRequestConfig):
    """
    Config for calling the integrations devices url.
    """
    polling_interval: int = Field(60 * 60 * 2, description="How frequently to perform the request, in seconds. Default"
                                                           "for devices is every 2 hours.")


class BasePACSRequestConfig(BaseRequestConfig):
    """
    Config for call the Camio PACS API.
    """
    backoff_multiplier: float = Field(2.0, description="Multiplier for increasing the sleep between retries calling the"
                                                       "PACS API")
    backoff_start: float = Field(2.0,
                                 description="Initial seconds until retry, gets multiplied by backoff_multiplier after each attempt")
    backoff_limit: int = Field(3, description="Maximum number of attempts to call the PACS API")


class BaseEventsRequestConfig(BaseRequestConfig):
    """
    Config for calling the integration's events url.
    """
    streaming: bool = Field(False, description="Whether the response from the events URL should be streamed or not")
    polling_interval: int = Field(10,
                                  description="How frequently to perform the request, in seconds. Default for events"
                                              " is every 10 seconds.")
    count_reset_interval: int = Field(60 * 60 * 24, description="In seconds, the interval on which to reset the events "
                                                                "forwarded count to 0. Default is every 24 hours.")
    fields: dict = Field({}, description="Optional. For filtering what fields to include in the responses from the "
                                         "integration events url")
    timezone_offset: str = Field(None, description="Timezone offset for timestamps in the events, +/- is required. "
                                                   "Note that daylight savings may not be accounted for. Ex: -0500")
    timezone_name: str = Field(None, description="Timezone name for timestamps in the events. Supported timezones all "
                                                 "pytz.all_timezones")


class BaseRequestConfigMap(BaseModel):
    """
    Configs specific to the URL being called.
    """
    devices: BaseDevicesRequestConfig = Field(BaseDevicesRequestConfig(), description="Config for requests to the integration's devices URL")
    events: BaseEventsRequestConfig = Field(BaseEventsRequestConfig(), description="Config for requests to the integration's events URL")
    pacs: BasePACSRequestConfig = Field(BasePACSRequestConfig(), description="Config for requests to the Camio PACS server")


class BaseIntegrationDriverConfig(BaseModel, extra=Extra.allow):
    """
    Base class for integration configs. Configs are yaml files that get read at the time of driver setup and then passed
    into the BaseIntegrationDriverConfig (or extended class) for validation. All the default value config values should
    go into one of these pydantic models instead of in the code directly.
    """
    log_level: Literal[logging.DEBUG,
                       logging.INFO,
                       logging.WARNING,
                       logging.ERROR,
                       logging.CRITICAL] = Field(10, description="Python logging level. 10 is debug, 20 info, etc.")
    credentials: BaseCredentials = Field(None,
                                         description="Credentials used to authenticate with the integration's API")
    credentials_filepath: str = Field(None,
                                      description="Optional, filepath to get credential payload to send to the auth url")
    urls: BaseUrls = Field(description="The urls to be called by the integration driver")
    requests: BaseRequestConfigMap = Field(description="Configurations for calls to various urls, such as "
                                                       "polling intervals and backoff attempts")
    test_values: Optional[dict] = Field({},
                                        description="Optional test values to be used in unittests if the config is a "
                                                    "test config")
