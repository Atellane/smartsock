from DPS import DPS
from time import sleep

# connect to pin I2C
dps310 = DPS()

def is_close(a: float, b: float, margin: float) -> bool:
    """
    hyp: margin >= 0
    Check wether two floats are close or not
    """
    return (a-b < margin, "up") if a-b > 0 else (a-b > -margin, "down")

def get_pressure() -> float:
    """
    hyp:
    Returns the pressure value mesured by the barometer
    """
    pressure = 0.0
    old_pressure = 0.0
    while True:
        scaled_p = dps310.calcScaledPressure()
        scaled_t = dps310.calcScaledTemperature()
        old_pressure = pressure
        sleep(1)
        pressure = dps310.calcCompPressure(scaled_p, scaled_t)
        print("a")
        if is_close(old_pressure, pressure, 0.01):
            break
    return pressure

def are_socks_possibly_in_the_box(initial_value: float) -> bool:
    """
    hyp:
    Returns True if there are probably socks in the box, otherwise returns False 
    """
    scaled_p = dps310.calcScaledPressure()
    scaled_t = dps310.calcScaledTemperature()
    pressure = dps310.calcCompPressure(scaled_p, scaled_t)
    print(f"current pressure : {pressure}")
    return not is_close(initial_value, pressure, 0.4)

def are_socks_in_the_box(initial_pressure) -> bool:
    """
    hyp:
    Calculate the mean of 20 are_socks_possibly_in_the_box to guess wether socks are in the box or not.
    depending on that condition, it returns True or False
    """
    results = []
    for _ in range(20):
        print(f"initial pressure : {initial_pressure},", end=" ")
        results.append(are_socks_possibly_in_the_box(initial_pressure))
        sleep(0.1)
    print(sum(results)/len(results))

if __name__ == "__main__":
    try:
        i_p = get_pressure()
        while True:
            are_socks_in_the_box(i_p)
            sleep(0.1)

    except KeyboardInterrupt:
        pass