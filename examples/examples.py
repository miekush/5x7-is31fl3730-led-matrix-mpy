"""
Examples for is31fl3730.py. Pin numbers are for a Raspberry Pi Pico -
change them for your board. Uncomment the demo you want at the bottom.
"""
from machine import I2C, SoftI2C, Pin
import time
import is31fl3730
from is31fl3730 import IS31FL3730, MatrixGroup


def single_board():
    i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
    print("found:", [hex(a) for a in is31fl3730.scan(i2c)])

    d = IS31FL3730(i2c, is31fl3730.ADDR_GND, brightness=40)  # 0x60 jumper
    d.test_pattern()               # check orientation: starts top-left

    d.pixel(2, 3, 1)               # centre LED
    time.sleep(1)

    d.bitmap([                     # a heart
        ".#.#.",
        "#####",
        "#####",
        "#####",
        ".###.",
        "..#..",
        ".....",
    ])
    for level in (100, 50, 10, 50, 100):
        d.brightness(level)
        time.sleep(0.4)

    d.text("7")                    # large 5x7 font
    time.sleep(1)
    d.text("7", font="small")      # small 3x5 font
    time.sleep(1)

    d.scroll("Hello!", delay_ms=70, loops=2)


def several_boards():
    # Up to 4 boards per bus (0x60-0x63). Two hardware buses plus a
    # SoftI2C bus here; any mix works.
    i2c0 = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    i2c1 = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
    soft = SoftI2C(sda=Pin(14), scl=Pin(15), freq=400_000)

    group = MatrixGroup([
        IS31FL3730(i2c0, 0x60),     # leftmost board
        IS31FL3730(i2c0, 0x61),
        IS31FL3730(i2c1, 0x60),     # same address is fine on another bus
        IS31FL3730(soft, 0x60),     # rightmost board
    ])
    # Or let the library find them: group = MatrixGroup.discover(i2c0, i2c1, soft)

    group.brightness(30)
    group.text("ABCDEFG")           # shows "ABCD" (one char per board)
    time.sleep(2)
    group.text("42", align="right")
    time.sleep(2)
    group.scroll("Scrolling across every board...   ", delay_ms=60)  # forever


def non_blocking():
    i2c = I2C(0, sda=Pin(2), scl=Pin(3), freq=400_000)
    group = MatrixGroup.discover(i2c)
    s = group.scroller("Temp: --.- C", delay_ms=70)
    last = time.ticks_ms()
    while True:
        s.update()                  # returns immediately
        if time.ticks_diff(time.ticks_ms(), last) > 5000:
            last = time.ticks_ms()
            s.set_text("Temp: %.1f C" % 21.5)   # change text on the fly
        # ... do other work here ...


def with_asyncio():
    import asyncio
    i2c = I2C(0, sda=Pin(2), scl=Pin(3), freq=400_000)
    group = MatrixGroup.discover(i2c)

    async def blink():
        led = Pin("LED", Pin.OUT)
        while True:
            led.toggle()
            await asyncio.sleep_ms(250)

    async def main():
        asyncio.create_task(blink())
        await group.scroll_async("asyncio!", delay_ms=60)  # forever

    asyncio.run(main())


single_board()
# several_boards()
# non_blocking()
# with_asyncio()
