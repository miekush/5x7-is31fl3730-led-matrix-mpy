# IS31FL3730 5x7 LED Matrix — MicroPython driver

A single-file driver (`is31fl3730.py`) for the 5x7 LED matrix breakout. Copy it to the board's filesystem, for example with `mpremote cp is31fl3730.py :`. Tested on MicroPython 1.30.

## Board facts the driver relies on

| Item | Value |
|---|---|
| LED wiring | Matrix 1: anodes on R1–R7 (ROW1–7), cathodes on C1–C5 (COL1–5) |
| Chip mode | 8×8 mode, matrix 1 only (config reg `0x00 = 0x00`) |
| Orientation | Jumper labels at the top: x=0 is COL1 (left), y=0 is ROW7 (top). `rotation=180` flips it. |

| Jumper | AD pin | Address | Constant |
|---|---|---|---|
| JP4 (silk "0x60") | GND | 0x60 | `ADDR_GND` |
| JP2 (silk "61") | SCL | 0x61 | `ADDR_SCL` |
| JP1 (silk "62") | SDA | 0x62 | `ADDR_SDA` |
| JP3 (silk "63") | VDD | 0x63 | `ADDR_VDD` |

Close only one jumper. Each bus holds up to 4 boards, and you can add more buses with `I2C` or `SoftI2C`. JP5 connects the on-board 4.7 kΩ pull-ups. With several boards on one bus, consider opening JP5 on all but one so the pull-ups do not stack up in parallel.

## API

### One board: `IS31FL3730(i2c, address=0x60, *, brightness=50, current=None, rotation=0, auto_show=True)`

| Method | What it does |
|---|---|
| `pixel(x, y, v=None)` | Sets an LED (x 0–4, y 0–6). With no `v`, it reads the LED instead. |
| `bitmap(rows)` | Takes 7 rows, each a string like `"#..#."` or a 5-bit int (MSB = left). |
| `columns(cols)` | Takes 5 raw column bytes (bit 0 = top). |
| `fill(v)` / `clear()` / `invert()` | Turns all LEDs on, all off, or toggles them. |
| `char(c, font)` / `text(s, font)` | Shows one character. `font` is `"large"` (5×7) or `"small"` (3×5). |
| `scroll(text, delay_ms=80, font="large", loops=0)` | Blocking scroll. `loops=0` scrolls forever. |
| `scroller(...)` / `scroll_async(...)` | Non-blocking and asyncio versions of `scroll`. |
| `brightness(pct)` | Sets brightness 0–100 % through the PWM register `0x19`. With no argument, returns the current value. |
| `current(mA)` | Sets peak row current 5–75 mA (reg `0x0D`). The chip default is 40 mA. |
| `shutdown()` / `wake()` | Enters and leaves low-power shutdown. `wake()` restores the brightness. |
| `test_pattern()` | Lights each LED in reading order, starting top-left. |
| `show()` | Pushes the buffer to the LEDs. Call it yourself when `auto_show=False`. |

### Several boards: `MatrixGroup(displays, gap=1)`

Pass the boards left to right. They can sit on different I2C buses. `MatrixGroup.discover(i2c0, i2c1, ...)` scans the buses and builds the group for you.

* `text(s, font, align)` shows one character per board. Only the first *N* characters appear, where *N* is the number of boards. `align` is `"left"`, `"center"` or `"right"`.
* `scroll`, `scroller` and `scroll_async` move text across every board. `gap=1` adds one hidden column between boards, which matches the physical spacing of boards butted edge to edge.
* `pixel`, `bitmap` (rows 5·N wide), `fill`, `clear`, `brightness`, `current`, `shutdown` and `wake` work across the whole group.

### `Scroller`

`s = group.scroller("text")`, then call `s.update()` in your main loop. It returns `False` when the scroll finishes. `s.set_text()` changes the text mid-scroll, and `s.stop()` ends it.

## Examples

```
micropython/
├── is31fl3730.py          the driver: copy this to the board first
├── basic_test.py          "Hello world!" scrolling on one board
└── examples/
    ├── function-tests/    one script per driver feature
    ├── animations/        DVD bounce, digital rain, Snake, Pong, heart
    └── video-player/      PC-side video converter and on-board player
```

All examples assume the Feather RP2040 STEMMA QT port (I2C1, SDA = GP2, SCL = GP3) and a board at 0x60. Edit the `I2C(...)` line near the top of each script if yours differs.

### Function tests (`examples/function-tests/`)

Each script tests one part of the driver and prints what you should see. Copy `is31fl3730.py` to the board, then run a test from your editor (Thonny, or "Run current file" in MicroPico) or with `mpremote run test_01_init.py`.

| Script | Tests |
|---|---|
| `test_01_init.py` | `scan()`, creating a display, `test_pattern()`. Run this one first: it checks wiring, address and that every LED works. |
| `test_02_pixel.py` | `pixel()` set, clear and read back, plus batching changes with `auto_show = False` and `show()`. |
| `test_03_bitmap.py` | `bitmap()` from strings and from numbers, `columns()`, `fill()`, `invert()`, `clear()`. |
| `test_04_text.py` | `text()` and `char()` in the large and small fonts, cycling through every character. |
| `test_05_scroll.py` | `scroll()` with `loops`, `delay_ms`, the small font and `spacing`. |
| `test_06_scroll_nonblocking.py` | `scroller()` with `update()` and `set_text()` while your own loop keeps running. |
| `test_07_scroll_async.py` | `scroll_async()` alongside other asyncio tasks (blinks the Feather's red LED on pin 13). |
| `test_08_brightness.py` | `brightness()` fading and `current()` from 5 to 40 mA. |
| `test_09_shutdown.py` | `shutdown()` and `wake()`, including the brightness being restored. |
| `test_10_rotation.py` | `rotation = 180` for a board mounted upside down. |
| `test_11_multi_display.py` | `MatrixGroup`: `discover()`, one character per board, `align`, group-wide `pixel()` and `bitmap()`, brightness and scrolling across boards. Needs two or more boards with different addresses. |

### Animations (`examples/animations/`)

To set up the board:
1. Copy `is31fl3730.py`, `examples/animations/matrix_setup.py` and the animation you want to the board.
2. Run the animation with `import dvd_bounce`, `import heart`, and so on. Ctrl-C stops it and blanks the display.
3. Edit the I2C pins and brightness in `matrix_setup.py`. It defaults to the Feather RP2040 STEMMA QT port (I2C1, GP2/GP3) and finds every board on that bus. Give the leftmost board address 0x60, the next 0x61, and so on.

All the animations scale to however many boards you have.

| Script | What it does |
|---|---|
| `dvd_bounce.py` | A block bounces off the edges, and the display flashes when it hits a corner exactly. |
| `matrix_rain.py` | Streaks fall down every column at random speeds. |
| `snake.py` | Snake plays itself, using shortest path to the food while avoiding traps. Set `BUTTON_LEFT_PIN`/`BUTTON_RIGHT_PIN` to play with two buttons wired to GND. |
| `pong.py` | Two computer paddles play first to 5, with the score scrolled after each point. Set `BUTTON_UP_PIN`/`BUTTON_DOWN_PIN` to control the left paddle. |
| `heart.py` | A heartbeat ("lub-dub") that swells and brightens on each beat. With several boards, the hearts ripple. |

The settings at the top of each script include speed, sizes and how often the computer players make mistakes.

### Video playback (`examples/video-player/`)

1. On your PC, convert a video with `video_to_matrix.py` (needs `pip install opencv-python numpy`):
   `python video_to_matrix.py "video.mp4" bad_apple.bin --boards 1 --preview preview.mp4`
   * `--boards N` makes a file for N boards side by side.
   * `--fps 15` halves the file size.
   * `--fit stretch` keeps the whole frame instead of cropping the sides.
   * `--invert` swaps which pixels light up.
   * `--preview` writes a simulated-LED video so you can check the result before copying anything.
2. Copy `is31fl3730.py`, `bad_apple.py` and the `.bin` file to the board.
3. Run `import bad_apple`. It plays at the file's frame rate, skips frames if it falls behind, and loops by default.

Each frame is 5 bytes per board, so a 3.5-minute video at 30 fps is about 32 KB per board.
