# Test 11: MatrixGroup - several boards used as one wide display
#
# Set the boards' address jumpers to different addresses (leftmost 0x60,
# then 0x61, ...). Boards on a second I2C bus or a SoftI2C bus also work:
# see the commented lines below.
#
# Expected: one character per board, right-aligned text, a dot moving
# across every board, a wide bitmap, then text scrolling across all boards.

from machine import I2C, SoftI2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730, MatrixGroup

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)

#Option 1: find every board on the bus automatically (ordered by address)
group = MatrixGroup.discover(i2c, brightness=40)

#Option 2: list the boards yourself, leftmost first. They can be on
#different buses, e.g. a second bus made with SoftI2C:
# soft = SoftI2C(sda=Pin(24), scl=Pin(25), freq=400_000)
# group = MatrixGroup([
#     IS31FL3730(i2c, 0x60),
#     IS31FL3730(i2c, 0x61),
#     IS31FL3730(soft, 0x60),     #same address is fine on another bus
# ])

n = len(group)
print("group of", n, "board(s):", group.displays)

#one character per board; extra characters are dropped
group.text("ABCDEFGH")
time.sleep(2)

#shorter text can be aligned left, center or right
group.text("1", align="right")
time.sleep(1.5)

#pixel x runs 0 .. 5*n-1 across all boards
group.clear()
for x in range(group.width):
    group.pixel(x, 3, 1)
    time.sleep_ms(100)
    group.pixel(x, 3, 0)

#a bitmap as wide as the whole group (5*n columns per row)
w = group.width
group.bitmap(["#" * w, "." * w, "#." * (w // 2) + "#" * (w % 2),
              "." * w, ".#" * (w // 2) + "." * (w % 2), "." * w, "#" * w])
time.sleep(2)

#brightness for every board at once
group.brightness(10)
time.sleep(1)
group.brightness(40)

#scroll across every board (the hidden gap between boards is gap=1)
group.scroll("Scrolling across %d board(s)" % n, delay_ms=60, loops=1)
print("done")
