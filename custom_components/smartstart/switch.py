"""
Support for SmartStart remote start "switch".

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.smartstart/
"""
import logging

from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchDevice
from custom_components.smartstart import DOMAIN as SS_DOMAIN
from custom_components.smartstart import SmartStartDevice

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['smartstart']

ICON = 'mdi:engine'

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the SmartStart switch platform."""
    devices = [SmartStartSwitch(vehicle, hass.data[SS_DOMAIN]['controller'])
               for vehicle in hass.data[SS_DOMAIN]['vehicles']]
    add_entities(devices, True)


class SmartStartSwitch(SmartStartDevice, SwitchDevice):
    """Representation of a SmartStart remote start "switch"."""

    def __init__(self, vehicle, controller):
        """Initialise the SmartStart start "switch"."""
        super().__init__(vehicle, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.unique_id)

    def turn_on(self, **kwargs):
        """Send the on (start) command."""
        self._controller.send_command(self._smartstart_id, 'remote')

    @property
    def is_on(self):
        """Get whether the switch is in on state."""
        return None
    
    @property
    def icon(self):
        """Return the icon to display."""
        return ICON
