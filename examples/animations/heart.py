"""
heart.py - a heart that beats: "lub-dub", pause, repeat. It swells and
brightens on each beat and shrinks and dims while resting.

Run with:  import heart   (needs is31fl3730.py and matrix_setup.py)
With several boards each shows a heart, beating slightly out of step.
"""

import time
from matrix_setup import run

BPM = 70
MAX_BRIGHTNESS = 100   # percent at the peak of a beat
MIN_BRIGHTNESS = 6     # percent while resting
STEP_MS = 20

BIG = [
    ".....",
    ".#.#.",
    "#####",
    "#####",
    ".###.",
    "..#..",
    ".....",
]
SMALL = [
    ".....",
    ".....",
    ".#.#.",
    ".###.",
    "..#..",
    ".....",
    ".....",
]


def beat_level(t):
    """0..1 brightness for time t (0..1 through one heartbeat)."""
    def pulse(t, centre, width):
        d = abs(t - centre) / width
        return max(0.0, 1.0 - d) ** 2
    return max(pulse(t, 0.10, 0.10), 0.7 * pulse(t, 0.30, 0.10))  # lub, dub


def main(group):
    period = 60000 // BPM
    shape = [None] * len(group)
    start = time.ticks_ms()
    while True:
        now = time.ticks_diff(time.ticks_ms(), start)
        for i, d in enumerate(group):
            # Offset each board a little so a row of hearts ripples
            t = ((now - i * 90) % period) / period
            level = beat_level(t)
            want = BIG if level > 0.35 else SMALL
            if shape[i] is not want:
                shape[i] = want
                d.auto_show = False
                d.bitmap(want)
                d.show()
            # Square the level so the fade looks even to the eye
            d.brightness(MIN_BRIGHTNESS + (MAX_BRIGHTNESS - MIN_BRIGHTNESS) * level * level)
        time.sleep_ms(STEP_MS)


run(main)
