service_data = { 'title': 'TV Time is Over!', 'message': '', 'data': { 'color': 'red', 'transparency': '50%', 'fontsize': 'max', 'duration': 5 } }
for i in range(30, 0, -5):
    service_data['message'] = 'TV will shutdown in %s seconds.' % i
    hass.services.call('notify', 'basement_tv', service_data, False)
    time.sleep(1)
service_data['message'] = 'Shutting down...'
service_data['data']['duration'] = 30
hass.services.call('notify', 'basement_tv', service_data, False)
time.sleep(25);
hass.services.call('remote', 'turn_off', { 'entity_id': 'remote.basement_harmony_hub' }, False)
