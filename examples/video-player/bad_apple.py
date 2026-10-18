"""
bad_apple.py - play a frame file made by video_to_matrix.py on the 5x7 LED
matrix boards.

1. On your PC:  python video_to_matrix.py "<video>.mp4" bad_apple.bin --boards 1
2. Copy is31fl3730.py, bad_apple.py and bad_apple.bin to the board
   (e.g. mpremote cp is31fl3730.py bad_apple.py bad_apple.bin :)
3. Run it:  import bad_apple   (or mpremote run bad_apple.py)

Edit the I2C pins / addresses below to match your setup. Pins are for the
Adafruit Feather RP2040 STEMMA QT port (SDA=GP2, SCL=GP3 on I2C1).
"""

import struct
import time
from machine import I2C, Pin
from is31fl3730 import IS31FL3730, MatrixGroup

FRAME_FILE = "bad_apple.bin"
BRIGHTNESS = 40     # percent
LOOP = True         # restart when the video ends


def play(group, path=FRAME_FILE, loop=LOOP):
    with open(path, "rb") as f:
        magic, version, boards, fps, _, count = struct.unpack(
            "<4sBBBBI", f.read(12))
        if magic != b"LEDV":
            raise ValueError("%s is not a video_to_matrix.py frame file" % path)
        if boards > len(group):
            raise ValueError("file is for %d boards but the group has %d"
                             % (boards, len(group)))
        displays = group.displays[:boards]
        frame = bytearray(5 * boards)
        mv = memoryview(frame)
        period_us = 1_000_000 // fps
        print("playing %d frames at %d fps on %d board(s)" % (count, fps, boards))

        while True:
            f.seek(12)
            start = time.ticks_us()
            n = 0
            while n < count:
                # Where should we be? Skip frames if I2C/flash fell behind.
                due = time.ticks_diff(time.ticks_us(), start) // period_us
                if due > n:
                    f.seek(12 + due * len(frame))
                    n = due
                    if n >= count:
                        break
                if f.readinto(frame) != len(frame):
                    break
                for i, d in enumerate(displays):
                    d._buf[:] = mv[i * 5:i * 5 + 5]
                    d.show()
                n += 1
                wait = period_us * n - time.ticks_diff(time.ticks_us(), start)
                if wait > 0:
                    time.sleep_us(wait)
            if not loop:
                break
    group.clear()


def main():
    i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
    # One board:
    group = MatrixGroup([IS31FL3730(i2c, 0x60, brightness=BRIGHTNESS)])
    # Several boards, leftmost first (must match --boards used when converting):
    # group = MatrixGroup.discover(i2c, brightness=BRIGHTNESS)
    try:
        play(group)
    except KeyboardInterrupt:
        group.clear()


main()
