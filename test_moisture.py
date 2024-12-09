import time
from grove.grove_moisture_sensor import GroveMoistureSensor

# connect to alalog pin 0(slot A0)
PIN = 0

sensor = GroveMoistureSensor(PIN)

print('Detecting moisture...')
while True:
    m = sensor.moisture
    if 0 <= m and m < 300:
        result = 'Dry'
    elif 300 <= m and m < 600:
        result = 'Moist'
    else:
        result = 'Wet'
    print('Moisture value: {0}, {1}'.format(m, result))
    time.sleep(1)