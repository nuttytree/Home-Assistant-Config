"""
Support for SmartStart remote starters.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/smartstart/
"""

DOMAIN = 'smartstart'

SS_COMPONENTS = [
    'lock', 'switch', 'device_tracker'
]

NOTIFICATION_ID = 'smartstart_integration_notification'
NOTIFICATION_TITLE = 'SmartStart integration setup'

ICON = 'mdi:car-connected'