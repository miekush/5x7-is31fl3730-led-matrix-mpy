"""
matrix_rain.py - "digital rain": streaks of LEDs falling at different
speeds down every column.

Run with:  import matrix_rain   (needs is31fl3730.py and matrix_setup.py)
"""

import random
import time
from matrix_setup import run

FRAME_MS = 60
SPAWN_CHANCE = 12    # percent chance per frame that an empty column starts a drop
MIN_TRAIL, MAX_TRAIL = 2, 5
SPEEDS = (1, 2, 3)   # frames per row: 1 = fastest
SPARKLE = 3          # percent chance per frame of a stray "glyph" flicker


class Drop:
    def __init__(self):
        self.y = -1
        self.trail = random.randint(MIN_TRAIL, MAX_TRAIL)
        self.speed = SPEEDS[random.randint(0, len(SPEEDS) - 1)]
        self.tick = 0


def main(group):
    W, H = group.width, group.height
    drops = [None] * W

    while True:
        group.fill(0)
        for x in range(W):
            d = drops[x]
            if d is None:
                if random.randint(0, 99) < SPAWN_CHANCE:
                    drops[x] = d = Drop()
                else:
                    continue
            # Advance this drop at its own speed
            d.tick += 1
            if d.tick >= d.speed:
                d.tick = 0
                d.y += 1
            # Draw the head and trail
            for i in range(d.trail):
                y = d.y - i
                if 0 <= y < H:
                    group.pixel(x, y, 1)
            if d.y - d.trail >= H:     # trail has left the bottom
                drops[x] = None

        if random.randint(0, 99) < SPARKLE:
            group.pixel(random.randint(0, W - 1), random.randint(0, H - 1), 1)

        group.show()
        time.sleep_ms(FRAME_MS)


run(main)
