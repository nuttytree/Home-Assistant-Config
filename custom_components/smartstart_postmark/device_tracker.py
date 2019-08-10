import json
import logging
from datetime import timedelta

import requests

from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.util import slugify
from custom_components.smartstart import DOMAIN as SS_DOMAIN
from custom_components.smartstart.device_tracker import (ICON,
                                                         SmartStartDeviceTracker)

_LOGGER = logging.getLogger(__name__)
_TRACKER = None

DEPENDENCIES = ['smartstart']
DEPENDENCIES = ['webhook']

def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the SmartStart tracker."""
    global _TRACKER
    vehicles = []
    for vehicle in hass.data[SS_DOMAIN]['vehicles']:
        locateAction = next((a for a in vehicle['AvailActions'] if a['Name'] == 'locate'), None)
        if locateAction:
            vehicles.append(vehicle)
    if vehicles:
        _TRACKER = SmartStartPostMarkTracker(hass, see, vehicles)
    return True

class SmartStartPostMarkTracker(SmartStartDeviceTracker):
    """Representation of a SmartStart/PostMark device tracker."""

    def __init__(self, hass, see, vehicles):
        """Initialise the SmartStart device tracker."""
        super().__init__(hass, see, vehicles)
        hass.components.webhook.async_register('device_tracker', 'SmartStart/PostMark Device Tracker', 'smartstart_postmark', handle_webhook)
    
    def get_vehicle_from_name(self, name):
        return next((v for v in self._vehicles if v['Name'].lower() == name), None)

async def handle_webhook(hass, webhook_id, request):
    data = await request.json()
    name = data['Subject'].lower().replace('smart alert received for ', '')
    vehicle = _TRACKER.get_vehicle_from_name(name)
    if vehicle == None:
        return "Vehicle not found"
    entity_id = slugify('{} {}'.format(SS_DOMAIN, vehicle['DeviceId']).lower())
    attr = {
        'address': None,
        'speed': None,
        'heading': None,
        'vin': vehicle["Field1"],
        'year': vehicle["Field4"],
        'manufacturer': vehicle["Field5"],
        'model': vehicle["Field6"],
        'airid': vehicle["AirId"],
        'esn': vehicle["ESN"]
    }
    location = ""
    if "Entered SmartFence" in data['HtmlBody']:
        location = STATE_HOME
    elif "Exited SmartFence" in data['HtmlBody']:
        location = STATE_NOT_HOME
    else:
        return "Couldn't determine location"
    _TRACKER._see(
        dev_id=entity_id, host_name=name, icon=ICON,
        attributes=attr, location_name=location)
    return "Set location"
