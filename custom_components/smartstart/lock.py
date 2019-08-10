"""
Support for SmartStart door locks.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/lock.smartstart/
"""
import logging

from homeassistant.components.lock import ENTITY_ID_FORMAT, LockDevice
from custom_components.smartstart import DOMAIN as SS_DOMAIN
from custom_components.smartstart import SmartStartDevice

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['smartstart']


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the SmartStart lock platform."""
    devices = [SmartStartLock(vehicle, hass.data[SS_DOMAIN]['controller'])
               for vehicle in hass.data[SS_DOMAIN]['vehicles']]
    add_entities(devices, True)


class SmartStartLock(SmartStartDevice, LockDevice):
    """Representation of a SmartStart door lock."""

    def __init__(self, vehicle, controller):
        """Initialise the SmartStart lock."""
        super().__init__(vehicle, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.unique_id)

    def lock(self, **kwargs):
        """Send the lock command."""
        _LOGGER.debug("Locking doors for: %s", self._name)
        self._controller.send_command(self._smartstart_id, 'arm')

    def unlock(self, **kwargs):
        """Send the unlock command."""
        self._controller.send_command(self._smartstart_id, 'disarm')
