# Test 3: bitmap(), columns(), fill(), invert() and clear()
#
# Expected: a smiley, the same smiley drawn from numbers, a checkerboard
# from raw columns, all on, inverted checkerboard, then blank.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

#7 rows of strings: '#' (or 'X', '1', 'o') = on, '.' (or ' ', '0') = off
smiley = [
    ".....",
    ".#.#.",
    ".#.#.",
    ".....",
    "#...#",
    ".###.",
    ".....",
]
d.bitmap(smiley)
time.sleep(1.5)

#the same picture as 5-bit numbers (leftmost LED = highest bit)
d.bitmap([0b00000, 0b01010, 0b01010, 0b00000, 0b10001, 0b01110, 0b00000])
time.sleep(1.5)

#raw column bytes, left to right (bit 0 = top row)
d.columns([0b1010101, 0b0101010, 0b1010101, 0b0101010, 0b1010101])
time.sleep(1.5)

d.fill(1)       #all on
time.sleep(1)
d.columns([0b1010101, 0b0101010, 0b1010101, 0b0101010, 0b1010101])
d.invert()      #swap on/off
time.sleep(1.5)
d.clear()       #all off
print("done")
