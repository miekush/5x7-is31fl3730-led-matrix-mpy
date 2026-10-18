# Test 8: brightness() and current()
#
# Expected: all LEDs fade up and down, then step through a few row-current
# settings (each a little brighter), then return to the chip default.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)
d.fill(1)

#brightness is a percentage (0-100) set with the PWM register
for level in list(range(0, 101, 5)) + list(range(100, -1, -5)):
    d.brightness(level)
    time.sleep_ms(60)
print("brightness now", d.brightness(), "%")

#current() sets the peak row current in mA (5-75 in steps of 5).
#The chip default is 40 mA - check your LEDs' rating before going higher.
d.brightness(100)
for ma in (5, 10, 20, 30, 40):
    d.current(ma)
    print("row current", d.current(), "mA")
    time.sleep(1)

d.brightness(50)
d.clear()
print("done")
