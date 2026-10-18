"""
matrix_setup.py - shared hardware setup for the example animations.

Edit this one file to match your wiring; every example imports it.
Defaults are for the Adafruit Feather RP2040 STEMMA QT port
(I2C1: SDA = GP2, SCL = GP3).
"""

from machine import I2C, Pin
from is31fl3730 import MatrixGroup

BRIGHTNESS = 40  # percent


def get_group():
    i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
    # Finds every board on the bus (0x60-0x63), ordered by address,
    # so set the leftmost board to 0x60, the next to 0x61, and so on.
    # For boards on several buses: MatrixGroup.discover(i2c0, i2c1, ...)
    group = MatrixGroup.discover(i2c, brightness=BRIGHTNESS)
    group.auto_show = False  # the examples draw a whole frame, then show()
    group.clear()
    group.show()
    return group


def run(main):
    """Run an example and blank the display on Ctrl-C."""
    group = get_group()
    try:
        main(group)
    except KeyboardInterrupt:
        pass
    finally:
        group.clear()
        group.show()
