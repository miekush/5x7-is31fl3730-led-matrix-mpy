
#basic "Hello world!" test of the 5x7 LED Matrix

from machine import I2C, SoftI2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730, MatrixGroup

#init i2c1 at pins 2(SDA) and 3(SCL)
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)

#init display with i2c address 0x60 (AD tied to GND)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

#looping text with "Hello world!"
d.scroll("Hello world!", delay_ms=100, loops=0)
