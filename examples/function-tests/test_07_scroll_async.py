# Test 7: scroll_async() - scrolling text alongside other asyncio tasks
#
# Expected: text scrolls on the display while the Feather's on-board LED
# blinks (pin 13) and the console counts seconds. Ctrl-C to stop.

from machine import I2C, Pin
import asyncio
import is31fl3730
from is31fl3730 import IS31FL3730

i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=50)

async def blink():
    led = Pin(13, Pin.OUT)      #red LED on the Adafruit Feather RP2040
    while True:
        led.toggle()
        await asyncio.sleep_ms(250)

async def seconds():
    n = 0
    while True:
        await asyncio.sleep(1)
        n += 1
        print("seconds:", n)

async def main():
    asyncio.create_task(blink())
    asyncio.create_task(seconds())
    await d.scroll_async("asyncio works! ", delay_ms=80)   #loops=0: forever

try:
    asyncio.run(main())
except KeyboardInterrupt:
    d.clear()
