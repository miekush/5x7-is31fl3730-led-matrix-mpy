# Test 9: shutdown() and wake()
#
# Expected: a pattern shows, the display goes dark for 2 seconds (low-power
# shutdown), then the same pattern returns at the same brightness.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=30)

d.text("S")
time.sleep(1.5)

d.shutdown()        #LEDs off, chip draws ~2 uA, picture is kept
print("shut down")
time.sleep(2)

d.wake()            #picture comes back; brightness is restored too
print("awake, brightness", d.brightness(), "%")
time.sleep(1.5)
d.clear()
print("done")
