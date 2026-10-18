# Test 4: text() and char() with both fonts
#
# Expected: "A" in the large 5x7 font, "A" in the small 3x5 font, then
# every printable character in turn in each font.

from machine import I2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

d.text("A")                     #large font is the default
time.sleep(1)
d.text("A", font="small")       #3x5 font, centred
time.sleep(1)

#on one board text() shows only the first character
d.text("Zebra")
time.sleep(1)

#every character in the large font (ASCII 32-126)
for code in range(32, 127):
    d.char(chr(code))
    time.sleep_ms(150)

#the small font has digits, A-Z (lowercase is shown as uppercase) and
#common punctuation; anything else shows as "?"
for ch in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!?.,:-+=/%#()<>_":
    d.char(ch, font="small")
    time.sleep_ms(200)

d.clear()
print("done")
