# Test 10: rotation - for boards mounted upside down
#
# Expected: an "R" the right way up, then an upside-down "R" (it reads
# correctly if you turn the board 180 degrees), then back to normal.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)

#rotation can also be passed when creating the display: rotation=180
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

d.text("R")
time.sleep(1.5)

d.rotation = 180
d.text("R")
time.sleep(1.5)

d.rotation = 0
d.text("R")
time.sleep(1.5)
d.clear()
print("done")
