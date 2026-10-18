# Test 6: scroller() - scroll text while your own code keeps running
#
# Expected: a counter scrolls across the display and changes every 2
# seconds; the console prints how often the main loop runs. Stops after
# 20 seconds.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

s = d.scroller("Count: 0", delay_ms=70)
count = 0
loops = 0
start = time.ticks_ms()
last = start

while time.ticks_diff(time.ticks_ms(), start) < 20_000:
    s.update()          #returns at once; only steps when delay_ms has passed
    loops += 1

    #your own code runs here, e.g. read a sensor
    if time.ticks_diff(time.ticks_ms(), last) >= 2000:
        last = time.ticks_ms()
        count += 1
        s.set_text("Count: %d" % count)     #change the text mid-scroll
        print("main loop ran", loops, "times in the last 2 s")
        loops = 0

s.stop()
d.clear()
print("done")
