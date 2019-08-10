"""
Support for the SmartStart platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.smartstart/
"""
import logging

from custom_components.smartstart import DOMAIN as SS_DOMAIN
from homeassistant.util import slugify
from .const import (
    ICON
)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['smartstart']

def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the SmartStart tracker."""
    vehicles = []
    for vehicle in hass.data[SS_DOMAIN]['vehicles']:
        locateAction = next((a for a in vehicle['AvailActions'] if a['Name'] == 'locate'), None)
        if locateAction:
            vehicles.append(vehicle)
    if vehicles:
        SmartStartDeviceTracker(hass, see, vehicles)
    return True

class SmartStartDeviceTracker(object):
    """Representation of a SmartStart device tracker."""

    def __init__(self, hass, see, vehicles):
        """Initialise the SmartStart device tracker."""
        self._controller = hass.data[SS_DOMAIN]['controller']
        self._see = see
        self._vehicles = vehicles
        for vehicle in vehicles:
            device_id = vehicle['DeviceId']
            gps_location = vehicle['GeoPosition'].split('/')
            address = vehicle['Address']
            speed = vehicle['LastKnownSpeed']
            heading = vehicle['LastKnownHeading']
            self._update_device(device_id, gps_location, address, speed, heading)

    def _update_device(self, device_id, gps_location, address, speed, heading):
        vehicle = next((v for v in self._vehicles if v['DeviceId'] == device_id), None)
        entity_id = slugify('{} {}'.format(SS_DOMAIN, device_id).lower())
        name = vehicle['Name']
        attr = {
            'address': address,
            'speed': speed,
            'heading': heading,
            'vin': vehicle["Field1"],
            'year': vehicle["Field4"],
            'manufacturer': vehicle["Field5"],
            'model': vehicle["Field6"],
            'airid': vehicle["AirId"],
            'esn': vehicle["ESN"]
        }
        self._see(
            dev_id=entity_id, host_name=name, icon=ICON,
            attributes=attr, gps=gps_location)
