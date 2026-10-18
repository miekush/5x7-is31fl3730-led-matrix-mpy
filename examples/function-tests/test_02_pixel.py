# Test 2: pixel() - set, clear and read single LEDs
#
# Expected: the four corners light, then the centre, then a dot walks
# down the middle column. Readback results print to the console.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

#x = 0..4 (left to right), y = 0..6 (top to bottom)
for x, y in ((0, 0), (4, 0), (0, 6), (4, 6)):
    d.pixel(x, y, 1)
    time.sleep(0.4)

d.pixel(2, 3, 1)
print("pixel(2, 3) reads", d.pixel(2, 3), "(expect 1)")
print("pixel(1, 1) reads", d.pixel(1, 1), "(expect 0)")
time.sleep(1)

#walk a dot down the middle column
d.clear()
for y in range(7):
    d.pixel(2, y, 1)
    time.sleep(0.2)
    d.pixel(2, y, 0)

#batch several changes and update the LEDs once with show()
d.auto_show = False
for i in range(5):
    d.pixel(i, i, 1)
d.show()
d.auto_show = True
print("done - a diagonal line should be showing")
