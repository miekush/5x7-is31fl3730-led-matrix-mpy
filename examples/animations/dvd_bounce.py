"""
dvd_bounce.py - the old DVD-player screensaver: a block bounces around the
display, and the whole display flashes when it hits a corner exactly.

Run with:  import dvd_bounce   (needs is31fl3730.py and matrix_setup.py)
"""

import random
import time
from matrix_setup import run

BLOCK_W = 2          # block size in LEDs
BLOCK_H = 2
FRAME_MS = 140       # smaller = faster
CORNER_FLASHES = 4


def main(group):
    W, H = group.width, group.height
    max_x, max_y = W - BLOCK_W, H - BLOCK_H
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)
    dx = 1 if random.getrandbits(1) else -1
    dy = 1 if random.getrandbits(1) else -1
    corners = 0

    while True:
        group.fill(0)
        for bx in range(BLOCK_W):
            for by in range(BLOCK_H):
                group.pixel(x + bx, y + by, 1)
        group.show()
        time.sleep_ms(FRAME_MS)

        # Bounce off the edges
        hit_x = hit_y = False
        if not 0 <= x + dx <= max_x:
            dx = -dx
            hit_x = True
        if not 0 <= y + dy <= max_y:
            dy = -dy
            hit_y = True

        if hit_x and hit_y:          # the corner hit!
            corners += 1
            print("corner hits:", corners)
            for _ in range(CORNER_FLASHES):
                for d in group:      # invert every board
                    for c in range(5):
                        d._buf[c] ^= 0x7F
                group.show()
                time.sleep_ms(120)

        x += dx
        y += dy


run(main)
