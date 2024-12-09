from time import sleep
from water_sensor import water_sensor
from barometer import get_pressure, are_socks_in_the_box

class socks():
    def __init__(self: object, name: str, owner: str, color: str, water_sensor_class: water_sensor) -> object:
        """
        hyp:
        Represents the socks and its state.
        """
        self.name = name
        self.owner = owner
        self.color = color
        self.i_pressure = 0.0
        self.water_sensor = water_sensor_class
    
    def put_socks_in_the_box(self) -> None:
        """
        hyp:
        Measures initial pressure when the user put its socks in the box to have a reference value.
        """
        self.i_pressure = get_pressure()
    
    def remove_socks_from_the_box(self) -> None:
        """
        hyp:
        Reinitialise the initial pressure value.
        """
        self.i_pressure = 0.0
    
    def are_socks_in_the_box(self) -> bool:
        """
        hyp:
        Calculate the mean of 20 are_socks_possibly_in_the_box to guess wether socks are in the box or not based on the pressure.
        Depending on that condition, it returns True or False.
        """
        return are_socks_in_the_box(self.i_pressure) if self.i_pressure != 0.0 else False
    
    def is_humid(self) -> bool or None:
        """
        hyp:
        Returns True if the sensor detects humidity, otherwise return False. Returns None if the socks are not in the box.
        """
        return self.water_sensor.is_humid() if self.i_pressure != 0.0 else None

if __name__ == "__main__":
    print('Detecting ...')
    w_sensor = water_sensor(0)
    sock_ex = socks("example", "me", w_sensor, "")
    while True:
        print(sock_ex.i_pressure)
        sock_ex.put_socks_in_the_box()
        sleep(5)
        print(sock_ex.i_pressure)
        print(sock_ex.are_socks_in_the_box())
        print(sock_ex.is_humid())
        sock_ex.remove_socks_from_the_box()
        print(sock_ex.i_pressure)
        print(sock_ex.are_socks_in_the_box())
        print(sock_ex.is_humid())