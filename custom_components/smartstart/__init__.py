"""
Support for SmartStart remote starters.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/smartstart/
"""

import json
import logging
import time
from multiprocessing import RLock
from urllib.error import HTTPError

import requests

import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify
from .const import (
    DOMAIN, SS_COMPONENTS, NOTIFICATION_ID, NOTIFICATION_TITLE
)

# REQUIREMENTS = ['teslajsonpy==0.05']

__version__ = '0.05'

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

def hide_email(email):
    """Obfuscate email."""
    part = email.split('@')
    return "{}{}{}@{}".format(part[0][0],
                              "*"*(len(part[0])-2),
                              part[0][-1],
                              part[1])

def hide_serial(item):
    """Obfuscate serial."""
    if item is None:
        return ""
    if isinstance(item, dict):
        response = item.copy()
        serial = item['serialNumber']
        response['serialNumber'] = hide_serial(serial)
    elif isinstance(item, str):
        response = "{}{}{}".format(item[0],
                                   "*"*(len(item)-4),
                                   item[-3:])
    return response

async def async_setup(hass, base_config):
    """Set up of SmartStart component."""
    # from teslajsonpy import Controller as teslaAPI, TeslaException

    config = base_config.get(DOMAIN)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    if hass.data.get(DOMAIN) is None:
        try:
            hass.data[DOMAIN] = {}
            hass.data[DOMAIN]['controller'] = Controller(username, password)
            _LOGGER.debug("Connected to the SmartStart API.")
        except SmartStartException as ex:
            if ex.code == 401:
                hass.components.persistent_notification.create(
                    "Error:<br />Please check username and password."
                    "You will need to restart Home Assistant after fixing.",
                    title=NOTIFICATION_TITLE,
                    notification_id=NOTIFICATION_ID)
            else:
                hass.components.persistent_notification.create(
                    "Error:<br />"
                    "Can't communicate with the SmartStart API.<br />"
                    "Error code: {} Reason: {}"
                    "You will need to restart Home Assistant after fixing."
                    "".format(ex.code, ex.message),
                    title=NOTIFICATION_TITLE,
                    notification_id=NOTIFICATION_ID)
            _LOGGER.error("Unable to communicate with the SmartStart API: %s",
                          ex.message)
            return False
    
    hass.data[DOMAIN]['vehicles'] = hass.data[DOMAIN]['controller'].vehicles

    if not hass.data[DOMAIN]['vehicles']:
        return False

    device_registry = await dr.async_get_registry(hass)
    for vehicle in hass.data[DOMAIN]['vehicles']:
        device_registry.async_get_or_create(
            config_entry_id=None,
            identifiers={
                (DOMAIN, vehicle['DeviceId']),
                ('vin', vehicle['Field1']),
                ('airid', vehicle['AirId']),
                ('esn', vehicle['ESN'])
            },
            manufacturer=vehicle['Field5'],
            name=vehicle['Name'],
            model=vehicle['Field6']
        )

    for component in SS_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, base_config)

    return True


class SmartStartDevice(Entity):
    """Representation of a SmartStart entity."""

    def __init__(self, vehicle, controller):
        """Initialise the SmartStart entity."""
        self._vehicle = vehicle
        self._controller = controller
        self._name = vehicle['Name']
        self._smartstart_id = vehicle['DeviceId']
        self._unique_id = slugify('{} {}'.format(DOMAIN, self._smartstart_id).lower())

    @property
    def unique_id(self):
        """Return the SmartStart device Id."""
        return self._unique_id
    
    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return info about the SmartStart device."""
        return {
            'identifiers': {
                (DOMAIN, self._smartstart_id),
                ('vin', self._vehicle['Field1']),
                ('airid', self._vehicle['AirId']),
                ('esn', self._vehicle['ESN'])
            },
            'name': self.name,
            'manufacturer': self._vehicle['Field5'],
            'model': self._vehicle['Field6'],
            'sw_version': None,
            'via_hub': None
        }

    @property
    def assumed_state(self):
        """Return the assumed state flag."""
        return True
    
    @property
    def should_poll(self):
        """Return the should poll flag."""
        return False



URL_BASE = 'https://colt.calamp-ts.com/'
AUTH_URL = URL_BASE + 'auth/login/{username}/{password}'
VEHICLES_URL = URL_BASE + 'device/advancedsearch?sessid={session_id}'
COMMAND_URL = URL_BASE + 'device/sendcommand/{device_id}/{command}?sessid={session_id}'
SESSION_TIMEOUT = 600

class Controller:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._session_id = None
        self._session_expires = None
        self._vehicles = []
        self._lock = RLock()
        self._get_session_id()
        self._vehicles = self._get_vehicles()
    
    def _get_session_id(self):
        current_time = time.time()
        with self._lock:
            if (self._session_id == None) or (self._session_expires < current_time):
                try:
                    response = requests.get(AUTH_URL.format(username=self._username, password=self._password))
                except HTTPError as e:
                    self._session_id = None
                    raise SmartStartException(e.code)
                data = json.loads(response.content)
                self._session_id = data["Return"]["Results"]["SessionID"]
                self._session_expires = current_time + SESSION_TIMEOUT

    def _get_vehicles(self):
        try:
            response = requests.get(VEHICLES_URL.format(session_id=self._session_id))
        except HTTPError as e:
            self._vehicles = []
            raise SmartStartException(e.code)
        data = json.loads(response.content)
        return data["Return"]["Results"]["Devices"]
    
    def send_command(self, device_id, command):
        """Send a command to a vehicle."""
        self._get_session_id()
        try:
            response = requests.get(COMMAND_URL.format(device_id=device_id, command=command, session_id=self._session_id))
        except HTTPError as e:
            raise SmartStartException(e.code)
        try:
            data = json.loads(response.content)
        except Exception as e:
            if b'Unable to verify action on device' in response.content:
                raise SmartStartException(1)
            else:
                raise SmartStartException(0)
        return data['Return']

    @property
    def vehicles(self):
        """Return the list of vehicles."""
        return self._vehicles

class SmartStartException(Exception):
    def __init__(self, code, *args, **kwargs):
        self.message = ""
        super().__init__(*args, **kwargs)
        self.code = code
        if self.code == 1:
            self.message = 'COMMUNICATION_FAILED'
        if self.code == 401:
            self.message = 'UNAUTHORIZED'
        if self.code == 408:
            self.message = 'TIME_OUT'
        else:
            self.message = 'UNKNOWN_ERROR'
