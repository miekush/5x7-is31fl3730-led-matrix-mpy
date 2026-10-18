# Test 5: scroll() - blocking scrolling text
#
# Expected: "Hello world!" scrolls twice, then a faster scroll in the
# small font, then a slow scroll that repeats forever (Ctrl-C to stop).

from machine import I2C, Pin
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

#loops = how many times to scroll it; delay_ms = time per one-column step
d.scroll("Hello world!", delay_ms=80, loops=2)

d.scroll("Small font 0123", delay_ms=50, font="small", loops=1)

#spacing = blank columns between repeats (default: one display width)
print("scrolling forever - press Ctrl-C to stop")
try:
    d.scroll("Repeat ", delay_ms=120, loops=0, spacing=2)
except KeyboardInterrupt:
    d.clear()
