"""
snake.py - Snake. Plays itself by default; wire two buttons (to GND) and
set the pins below to play it yourself.

Run with:  import snake   (needs is31fl3730.py and matrix_setup.py)

The food blinks so you can tell it apart from the snake. When the snake
crashes it flashes, scrolls the score, and starts again.
"""

import random
import time
from machine import Pin
from matrix_setup import run

FRAME_MS = 220
START_LENGTH = 2

# Optional buttons (wired from the pin to GND). None = the snake plays itself.
BUTTON_LEFT_PIN = None    # e.g. 6  -> turn left (counter-clockwise)
BUTTON_RIGHT_PIN = None   # e.g. 7  -> turn right (clockwise)

DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))   # right, down, left, up (clockwise)


class Game:
    def __init__(self, W, H):
        self.W, self.H = W, H
        y = H // 2
        self.body = [y * W + x for x in range(START_LENGTH)]  # tail ... head
        self.dir = 0
        self.score = 0
        self.place_food()

    def place_food(self):
        free = [c for c in range(self.W * self.H) if c not in self.body]
        self.food = free[random.randint(0, len(free) - 1)] if free else None

    def step_cell(self, cell, d):
        """Cell reached by moving from `cell` in direction d, or None at a wall."""
        x, y = cell % self.W + DIRS[d][0], cell // self.W + DIRS[d][1]
        if 0 <= x < self.W and 0 <= y < self.H:
            return y * self.W + x
        return None

    # -- self-play: shortest path to the food, unless that leads to a trap --
    def flood(self, start, blocked):
        seen = {start}
        todo = [start]
        while todo:
            c = todo.pop()
            for d in range(4):
                n = self.step_cell(c, d)
                if n is not None and n not in seen and n not in blocked:
                    seen.add(n)
                    todo.append(n)
        return len(seen)

    def first_step_to(self, target, blocked):
        head = self.body[-1]
        prev = {head: None}
        queue = [head]
        i = 0
        while i < len(queue):
            c = queue[i]
            i += 1
            if c == target:
                while prev[c] != head:
                    c = prev[c]
                return c
            for d in range(4):
                n = self.step_cell(c, d)
                if n is not None and n not in prev and n not in blocked:
                    prev[n] = c
                    queue.append(n)
        return None

    def ai_direction(self):
        head = self.body[-1]
        blocked = set(self.body[1:])       # the tail moves out of the way
        options = []
        for d in range(4):
            n = self.step_cell(head, d)
            if n is not None and n not in blocked:
                after = blocked | {n}
                options.append((self.flood(n, after), d, n))
        if not options:
            return self.dir                # trapped: crash gracefully
        best = self.first_step_to(self.food, blocked) if self.food is not None else None
        for area, d, n in options:
            if n == best and area >= len(self.body):
                return d
        options.sort()
        return options[-1][1]              # most room to move

    def advance(self):
        """Move one cell. Returns False when the snake crashes."""
        new = self.step_cell(self.body[-1], self.dir)
        if new is None or new in self.body[1:]:
            return False
        self.body.append(new)
        if new == self.food:
            self.score += 1
            self.place_food()
        else:
            self.body.pop(0)
        return True


def draw(group, game, blink):
    group.fill(0)
    W = game.W
    for c in game.body:
        group.pixel(c % W, c // W, 1)
    if game.food is not None and blink:
        group.pixel(game.food % W, game.food // W, 1)
    group.show()


def main(group):
    buttons = None
    if BUTTON_LEFT_PIN is not None and BUTTON_RIGHT_PIN is not None:
        buttons = (Pin(BUTTON_LEFT_PIN, Pin.IN, Pin.PULL_UP),
                   Pin(BUTTON_RIGHT_PIN, Pin.IN, Pin.PULL_UP))

    while True:
        game = Game(group.width, group.height)
        blink = True
        idle = 0
        while True:
            if buttons:
                # Poll the buttons for one frame; one turn per frame.
                end = time.ticks_add(time.ticks_ms(), FRAME_MS)
                turned = False
                while time.ticks_diff(end, time.ticks_ms()) > 0:
                    if not turned and buttons[0].value() == 0:
                        game.dir = (game.dir - 1) % 4
                        turned = True
                    elif not turned and buttons[1].value() == 0:
                        game.dir = (game.dir + 1) % 4
                        turned = True
                    time.sleep_ms(5)
            else:
                game.dir = game.ai_direction()
                time.sleep_ms(FRAME_MS)

            score = game.score
            if not game.advance() or game.food is None:
                break
            idle = 0 if game.score != score else idle + 1
            if idle > game.W * game.H * 4:   # self-play stuck going in circles
                break
            blink = not blink
            draw(group, game, blink)

        # Game over: flash the snake, then show the score
        for i in range(6):
            if i % 2 == 0:
                draw(group, game, False)
            else:
                group.fill(0)
                group.show()
            time.sleep_ms(150)
        if game.food is None:
            group.scroll("WIN! %d" % game.score, delay_ms=60, loops=1)
        else:
            group.scroll("Score %d" % game.score, delay_ms=60, loops=1)


run(main)
