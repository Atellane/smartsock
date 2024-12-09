from grove.grove_water_sensor import GroveWaterSensor

class water_sensor():
    def __init__(self: object, PIN: int) -> object:
        """
        hyp: PIN is 0, 2, 4 or 6
        Wrapper for the grove.grove_water_sensor.GroveWaterSensor class to avoid
        making an instaciation of it each time we call is_humid
        """
        self.sensor = GroveWaterSensor(PIN)
        
    def is_humid(self: object) -> bool:
        """
        hyp:
        Returns True if the sensor detects humidity, otherwise return False. 
        """
        return self.sensor.value < 600

if __name__=="__main__":
    print('Detecting ...')
    sensor = water_sensor(0)
    while True:
        print(sensor.is_humid())