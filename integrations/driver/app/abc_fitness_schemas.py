from typing import List

from pydantic import BaseModel, Field, Extra

from schemas import BaseIntegrationDriverConfig, BaseRequestConfigMap, BaseEventsRequestConfig, BaseUrls, \
    BaseDevicesRequestConfig


# ----------------- ABC FITNESS API RESPONSE SCHEMAS -----------------

class ABCFitnessMemberPersonal(BaseModel):
    """
    This contains demographic information for a member
    {
        "firstName": "TESTER",
        "lastName": "SMITH",
        "middleInitial": "M",
        "email": "test@example.com",
        "isActive": "true",
        "memberStatus": "Active",
        "joinStatus": "Member",
        ...
    }
    NOTE: A lot of additional fields that aren't currently included in this schema.
    """

    firstName: str = Field(None, description="The first name of the member")
    lastName: str = Field(None, description="The last name of the member")
    middleInitial: str = Field(None, description="The middle initial of the member")
    email: str = Field(None, description="The e-mail for the member")
    isActive: bool = Field(False, description="Boolean indicating whether the member is active or inactive, ['true', "
                                              "'false']")
    memberStatus: str = Field(None, description="The current status of the member, ['active', 'inactive', 'all', "
                                                "'prospect'] ")
    joinStatus: str = Field(None, description="Indicates the join status of the member, ['Member', 'Prospect'] ")


class ABCFitnessMember(BaseModel):
    """
    {
        "memberId": "cc4329b2595b485799d354537d7c33cb",
        "personal": {
            "firstName": "Tester",
            "lastName": "Smith",
            "state": "AR",
            "countryCode": "US",
            "email": "test@example.com",
            "workPhoneExt": "0000",
            "emergencyExt": "0000",
            "barcode": "0900359298",
            "gender": "Unknown",
            "isActive": "true",
            "memberStatus": "Need Phone Number",
            "joinStatus": "Member",
            "isConvertedProspect": "false",
            "hasPhoto": "false",
            "memberStatusReason": "Need phone number",
            "firstCheckInTimestamp": "2024-07-08 06:36:40.044000",
            "lastCheckInTimestamp": "2024-07-08 07:36:23.788000",
            "totalCheckInCount": "2",
            "createTimestamp": "2024-07-08 06:35:41.088000",
            "lastModifiedTimestamp": "2024-07-08 07:36:23.829511",
            "dataSharingPreferences": {
                "memberDataFlags": {
                    "optOutCcpa": "false",
                    "optOutGdpr": "false",
                    "optOutOther": "false",
                    "deleteCcpa": "false",
                    "deleteGdpr": "false",
                    "deleteOther": "false"
                },
                "marketingPreferences": {
                    "email": "true",
                    "sms": "true",
                    "directMail": "true",
                    "pushNotification": "true"
                }
            },
            "homeClub": "9003"
        },
        "agreement": {
            ...
        }
    },
    """
    memberId: str = Field(description="The ABC Fitness GUID of the member")
    personal: ABCFitnessMemberPersonal = Field(None, description="This contains demographic information for a member, "
                                                                 "including name and email address")

    def get_actor_name(self):
        if self.personal is not None:
            return f"{self.personal.firstName} {self.personal.lastName}"
        else:
            return None

    def get_actor_email(self):
        return self.personal.email if self.personal is not None else None


class ABCFitnessEvent(BaseModel, extra=Extra.allow):
    """
     In ABC Fitness terminology, a checkIn. Ex:
    {
        "checkInId": "3869F76D88DE4A23B42C4A018044A7C2",
        "checkInTimestamp": "2024-07-01 23:51:34.574000",
        "checkInMessage": "ALREADY CHECKED IN",
        "stationName": "Door Access",
        "checkInStatus": "Normal Entry",
        "member": {
            "memberId": "cc4329b2595b485799d354537d7c33cb",
            "homeClub": "9003"
        }
    }
    """
    checkInId: str = Field(None, description="The GUID for this specific checkin")
    checkInTimestamp: str = Field(description="The date and time at which this checkin occurred in YYYY-MM-DD "
                                              "hh:mm:ss.nnnnnn format ")
    checkInMessage: str = Field(None, description="The text of the note that appeared when the member checked in, "
                                                  "ex: ALREADY CHECKED IN")
    stationName: str = Field(None, description="The name for the station at which the member checked in")
    checkInStatus: str = Field(None,
                               description="One of ['Normal Entry', 'Entry Allowed', 'Entry Denied', 'Entry Not Set']")
    member: ABCFitnessMember = Field(None, description="This contains information about the member who checked in")


class ABCFitnessDevice(BaseModel):
    """
    In ABC Fitness terminology, a station. Ex:
    {
        "stationId": "F84273CC22A44655AE78FC04F6A8CA30",
        "name": "Bark Station",
        "status": "active",
        "abcCode": "ACCESS_CONTROL_0"
    }
    """

    stationId: str = Field(None,
                           description="The ABCFitness GUID for the station, ex: F84273CC22A44655AE78FC04F6A8CA30")
    name: str = Field(None, description="Name of the ABCFitness device")
    status: str = Field(None, description="The status of the station, ['active', 'inactive']")
    abcCode: str = Field(None, description="The ABC Code for the station")


class ABCFitnessEventsRequestStatus(BaseModel):
    """
    This contains the status of the request with pagination details
    {
        "message": "success",
        "count": "10",
        "nextPage": "2"
    }
    """
    nextPage: int = Field(None, description="The page number of the next page that contains results. If this value is "
                                            "not returned, it means there are no more records")
    count: int = Field(None, description="An integer representing the result set size of the requested resource")
    message: str = Field(None, description="The general status message returned by the API. In the case of a "
                                           "validation or processing error, this will be descriptive text defining "
                                           "the issue. In the case of a successful request, the value will be "
                                           "'success'")


class ABCFitnessEventsRequest(BaseModel):
    """
    This contains the echo of the request details
    {
        "clubNumber": "9003",
        "page": "1",
        "size": "5000",
        "checkInTimestampRange": "2024-07-01 23:50:00.000000,2024-07-15 23:50:00.000000"
    }
    """
    clubNumber: int = Field(None, description="The club number provided in the request i.e. club_id")
    page: int = Field(1, description="The page number provided in the request parameters defaulted to 1 if none is "
                                     "provided")
    size: int = Field(None, description="The result set size provided in the request parameters. If no value is "
                                        "provided, the default will vary depending on the API")
    checkInTimestampRange: str = Field(None, description="The checkin timestamp range provided in the request")


class ABCFitnessEventsPayload(BaseModel):
    """
    Documentation: https://abcfinancial.3scale.net/docs/clubs#Clubs_getCheckinDetailsUsingGET_content

    Response from calling https://api.abcfinancial.com/rest/{club_id}/clubs/checkins/details/. Ex:
    {
        "status": {
            "message": "success",
            "count": "10",
            "nextPage": "2"
        },
        "request": {
            "clubNumber": "9003",
            "page": "1",
            "size": "5000",
            "checkInTimestampRange": "2024-07-01 23:50:00.000000,2024-07-15 23:50:00.000000"
        },
        "checkins": [
            {
                "checkInId": "3869F76D88DE4A23B42C4A018044A7C2",
                "checkInTimestamp": "2024-07-02 09:39:37.304000",
                "checkInMessage": "Club Payment Overdue 136 DAYS",
                "stationName": "ABC Support",
                "checkInStatus": "Entry Allowed",
                "member": {
                    "memberId": "cc4329b2595b485799d354537d7c33cb",
                    "homeClub": "9003"
                }
            },
            ...
        ]
    }
    """

    status: ABCFitnessEventsRequestStatus = Field(None, description="This contains the status of the request with "
                                                                    "pagination details")
    request: ABCFitnessEventsRequest = Field(None, description="This contains the echo of the request details")
    checkins: List[ABCFitnessEvent] = Field([], description="This contains a list of checkin details of a specified "
                                                            "club")


class ABCFitnessMembersPayload(BaseModel):
    """
    Documentation: https://abcfinancial.3scale.net/docs/members#!/Members/getMembersUsingGET

    Response from calling https://api.abcfinancial.com/rest/{club_id}/members. Ex:
    {
        "status": {
            "message": "success",
            "count": "10",
            "nextPage": "2"
        },
        "request": {
            "clubNumber": "9003",
            "page": "1",
            "size": "5000",
            "checkInTimestampRange": "2024-07-01 23:50:00.000000,2024-07-15 23:50:00.000000"
        },
        "checkins": [
            {
                "checkInId": "3869F76D88DE4A23B42C4A018044A7C2",
                "checkInTimestamp": "2024-07-02 09:39:37.304000",
                "checkInMessage": "Club Payment Overdue 136 DAYS",
                "stationName": "ABC Support",
                "checkInStatus": "Entry Allowed",
                "member": {
                    "memberId": "cc4329b2595b485799d354537d7c33cb",
                    "homeClub": "9003"
                }
            },
            ...
        ]
    }
    """

    status: ABCFitnessEventsRequestStatus = Field(None, description="This contains the status of the request with "
                                                                    "pagination details")
    request: ABCFitnessEventsRequest = Field(None, description="This contains the echo of the request details")
    members: List[ABCFitnessMember] = Field([], description="This contains a list of members with demographic, "
                                                            "agreement and alerts information that match the "
                                                            "parameter values that were specified")


# ----------------- DRIVER SCHEMAS -----------------

class ABCFitnessUrls(BaseUrls, extra=Extra.allow):
    """
    Contains the full urls for each request type. Some urls are optional.
    """

    devices: str = Field("https://api.abcfinancial.com/rest/{club_id}/clubs/stations",
                         description="Url to call to get the user's ABC Fitness stations")
    events: str = Field("https://api.abcfinancial.com/rest/{club_id}/clubs/checkins/details",
                        description="Url to call to get the user's ABC Fitness checkin events")
    pacs_server: str = Field("https://incoming.integrations.camio.com/pacs",
                             description="Url to forward the devices and events to once they have been converted to "
                                         "PACS format")
    members: str = Field("https://api.abcfinancial.com/rest/{club_id}/members",
                         description="Url to call to get the member information")


class ABCFitnessEventsRequestConfig(BaseEventsRequestConfig):
    """
    Config for calling the events (checkins) url. Include the number of checkins to request in one page.
    """

    streaming: bool = Field(False, description="ABC Fitness API does not support streaming", const=True)
    polling_interval: int = Field(43200,
                                  description="In seconds, how frequently to request checkin information via the ABC "
                                              "Fitness API. Defaults to every 12 hours")
    timezone_offset: str = Field(None, description="Timezone offset for timestamps in the events, +/- is required. "
                                                   "Note that daylight savings may not be accounted for. Ex: -0500")
    timezone_name: str = Field("UTC", description="Timezone name for timestamps in the events. Supported timezones all "
                                                  "pytz.all_timezones")
    get_member_info: bool = Field(True, description="If true, fetch the member info for all checkin events")
    page_size: int = Field(100, description="The number of checkins to request in one call to the ABCFitness API")


class ABCFitnessDevicesRequestConfig(BaseDevicesRequestConfig):
    """
    Config for calling the events (checkins) url. Include the number of checkins to request in one page.
    """

    polling_interval: int = Field(43200, description="In seconds, how frequently to request station information "
                                                     "via the ABC Fitness API. Defaults to every 12 hours")


class ABCFitnessMembersRequestConfig(BaseModel):
    """
    Config for calling the events members url. Include the number of members to request in one page.
    """

    page_size: int = Field(100, description="The number of members to request in one call to the ABCFitness API")


class ABCFitnessRequestConfigMap(BaseRequestConfigMap):
    """
    Configs specific to the URL being called.
    """

    devices: ABCFitnessDevicesRequestConfig = Field(ABCFitnessDevicesRequestConfig(),
                                                    description="Config for requests to the integration's devices URL")
    events: ABCFitnessEventsRequestConfig = Field(ABCFitnessEventsRequestConfig(),
                                                  description="Config for requests to the integration's events URL")
    members: ABCFitnessMembersRequestConfig = Field(ABCFitnessMembersRequestConfig(),
                                                    description="Config for requests to the integration's members URL")


class ABCFitnessIntegrationDriverConfig(BaseIntegrationDriverConfig, extra=Extra.allow):
    """
    Class for the ABC Fitness integration configs. Configs are yaml files that get read at the time of driver setup and
    then passed into the ABCFitnessIntegrationDriverConfig class for validation. All the default value config values
    should go into one of these Pydantic models instead of in the code directly.
    """

    urls: ABCFitnessUrls = Field(ABCFitnessUrls(), description="The urls to be called by the integration driver")
    requests: ABCFitnessRequestConfigMap = Field(ABCFitnessRequestConfigMap(),
                                                 description="Configurations for calls to various urls, such as "
                                                             "polling intervals and backoff attempts")