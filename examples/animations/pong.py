"""
pong.py - Pong between two computer paddles on the left and right edges.
Wire two buttons (to GND) and set the pins below to control the left paddle.

Run with:  import pong   (needs is31fl3730.py and matrix_setup.py)

Looks best on two or more boards (more room for the ball), but plays on one.
"""

import random
import time
from machine import Pin
from matrix_setup import run

FRAME_MS = 140
PADDLE = 2            # paddle height in LEDs
WIN_SCORE = 5
AI_MISTAKES = 20      # percent chance per frame a computer paddle hesitates

# Optional buttons for the left paddle (pin to GND). None = computer plays.
BUTTON_UP_PIN = None    # e.g. 6
BUTTON_DOWN_PIN = None  # e.g. 7


def main(group):
    W, H = group.width, group.height
    buttons = None
    if BUTTON_UP_PIN is not None and BUTTON_DOWN_PIN is not None:
        buttons = (Pin(BUTTON_UP_PIN, Pin.IN, Pin.PULL_UP),
                   Pin(BUTTON_DOWN_PIN, Pin.IN, Pin.PULL_UP))

    def draw(paddles, ball):
        group.fill(0)
        for x, top in ((0, paddles[0]), (W - 1, paddles[1])):
            for i in range(PADDLE):
                group.pixel(x, top + i, 1)
        if ball:
            group.pixel(ball[0], ball[1], 1)
        group.show()

    def ai_move(top, ball_y, coming):
        if not coming or random.randint(0, 99) < AI_MISTAKES:
            return top
        centre = top + PADDLE // 2
        if ball_y < centre and top > 0:
            return top - 1
        if ball_y > centre - (1 - PADDLE % 2) and top < H - PADDLE:
            return top + 1
        return top

    while True:
        score = [0, 0]
        serve = 1 if random.getrandbits(1) else -1
        while max(score) < WIN_SCORE:
            paddles = [(H - PADDLE) // 2, (H - PADDLE) // 2]
            bx, by = W // 2, random.randint(1, H - 2)
            dx, dy = serve, (1 if random.getrandbits(1) else -1)
            draw(paddles, (bx, by))
            time.sleep_ms(500)

            while True:
                # Paddles
                if buttons:
                    if buttons[0].value() == 0 and paddles[0] > 0:
                        paddles[0] -= 1
                    elif buttons[1].value() == 0 and paddles[0] < H - PADDLE:
                        paddles[0] += 1
                else:
                    paddles[0] = ai_move(paddles[0], by, dx < 0)
                paddles[1] = ai_move(paddles[1], by, dx > 0)

                # Ball: bounce off the top and bottom
                if not 0 <= by + dy < H:
                    dy = -dy
                nx, ny = bx + dx, by + dy

                # Reached a paddle column?
                if nx in (0, W - 1):
                    side = 0 if nx == 0 else 1
                    top = paddles[side]
                    if top <= ny < top + PADDLE or top <= by < top + PADDLE:
                        dx = -dx
                        # Where it hits changes the angle
                        hit = ny - top
                        dy = -1 if hit <= 0 else (1 if hit >= PADDLE - 1 else dy)
                        if random.randint(0, 3) == 0:
                            dy = 0 if dy else (1 if random.getrandbits(1) else -1)
                        nx = bx + dx
                        ny = by + dy
                        if not 0 <= ny < H:
                            dy = -dy
                            ny = by + dy
                    else:
                        # Missed: show the ball in the gutter, then score
                        draw(paddles, (nx, max(0, min(H - 1, ny))))
                        time.sleep_ms(400)
                        winner = 1 - side
                        score[winner] += 1
                        serve = -1 if winner == 0 else 1
                        break

                bx, by = nx, ny
                draw(paddles, (bx, by))
                time.sleep_ms(FRAME_MS)

            group.scroll("%d-%d" % (score[0], score[1]), delay_ms=50, loops=1)

        group.scroll("%s WINS" % ("LEFT" if score[0] > score[1] else "RIGHT"),
                     delay_ms=60, loops=1)


run(main)
