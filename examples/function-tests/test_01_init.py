# Test 1: find the board on the I2C bus, initialise it and check every LED
#
# Expected: the console lists the address(es) found, then each LED lights
# one at a time in reading order, starting top-left (jumper labels at top).

from machine import I2C, Pin
import is31fl3730
from is31fl3730 import IS31FL3730

#init i2c1 at pins 2(SDA) and 3(SCL)
i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)

#list every IS31FL3730 that answers (0x60-0x63)
found = is31fl3730.scan(i2c)
print("boards found:", [hex(a) for a in found])
if not found:
    raise SystemExit("no boards found - check wiring, pull-ups (JP5) and address jumper")

#init the first board found (or pass one of ADDR_GND/SCL/SDA/VDD)
d = IS31FL3730(i2c, found[0], brightness=50)
print("initialised", d)

#light each LED in turn
d.test_pattern(delay_ms=80)
print("done - all 35 LEDs should have lit, top-left first")
