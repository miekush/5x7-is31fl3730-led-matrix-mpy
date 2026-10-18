"""
is31fl3730.py - MicroPython driver for the IS31FL3730 5x7 LED matrix breakout.

Copy this single file to your board (e.g. with Thonny or `mpremote cp`).

Quick start
-----------
    from machine import I2C, Pin
    import is31fl3730

    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
    d = is31fl3730.IS31FL3730(i2c, is31fl3730.ADDR_GND)   # 0x60 jumper

    d.pixel(0, 0, 1)          # top-left LED on
    d.text("A")               # one character
    d.brightness(25)          # 25 %
    d.scroll("Hello world!")  # scrolls forever (Ctrl-C to stop)

Several boards (on one or more I2C buses) are combined with MatrixGroup:

    group = is31fl3730.MatrixGroup([d1, d2, d3])
    group.text("HEY")
    group.scroll("Scrolling across three boards  ")

Coordinates
-----------
x = 0..4 (left -> right), y = 0..6 (top -> bottom), with the board held so the
"0x60 | 61 | 62 | 63" jumper labels are at the top and readable. Pass
rotation=180 if your board is mounted the other way up.

Hardware notes (from the board schematic and IS31FL3730 datasheet)
-------------------------------------------------------------------
* LEDs are wired as Matrix 1: anodes on R1..R7 (ROW1..ROW7), cathodes on
  C1..C5 (COL1..COL5). The chip runs in 8x8 mode, matrix 1 only.
* I2C address = 0b11000 + AD pin state, chosen by closing ONE jumper:
      JP4 -> AD = GND -> 0x60      JP2 -> AD = SCL -> 0x61
      JP1 -> AD = SDA -> 0x62      JP3 -> AD = VDD -> 0x63
  so at most 4 boards share one I2C bus. Use more I2C buses (hardware or
  SoftI2C) for more boards.
"""

try:
    from micropython import const
except ImportError:  # running under CPython (desktop testing)
    def const(x):
        return x

import time

try:
    _sleep_ms = time.sleep_ms
    _ticks_ms = time.ticks_ms
    _ticks_diff = time.ticks_diff
    _ticks_add = time.ticks_add
except AttributeError:  # CPython fallbacks, for desktop testing only
    def _sleep_ms(ms):
        time.sleep(ms / 1000)

    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_diff(a, b):
        return a - b

    def _ticks_add(a, b):
        return a + b

try:
    import asyncio
except ImportError:
    try:
        import uasyncio as asyncio
    except ImportError:
        asyncio = None

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# I2C addresses (state of the AD pin, set with the solder jumpers)
# ---------------------------------------------------------------------------
ADDR_GND = const(0x60)  # JP4, silkscreen "0x60"
ADDR_SCL = const(0x61)  # JP2, silkscreen "61"
ADDR_SDA = const(0x62)  # JP1, silkscreen "62"
ADDR_VDD = const(0x63)  # JP3, silkscreen "63"
ADDRESSES = (0x60, 0x61, 0x62, 0x63)

# ---------------------------------------------------------------------------
# Registers (IS31FL3730 datasheet, Table 2)
# ---------------------------------------------------------------------------
_REG_CONFIG = const(0x00)   # SSD | DM | A_EN | ADM
_REG_MATRIX1 = const(0x01)  # 0x01..0x0B -> columns C1..C11, bit n = R(n+1)
_REG_UPDATE = const(0x0C)   # write 0x00 to latch the data registers
_REG_EFFECT = const(0x0D)   # AGS (audio gain) | CS (row current)
_REG_PWM = const(0x19)      # 0..128 global brightness
_REG_RESET = const(0xFF)    # write 0x00 to reset all registers

_CFG_SSD = const(0x80)          # software shutdown bit
_CFG_NORMAL = const(0x00)       # DM=00 matrix 1 only, A_EN=0, ADM=00 (8x8)

WIDTH = const(5)
HEIGHT = const(7)

# Row-current settings (mA) -> CS code (datasheet Table 6)
_CURRENT_CODES = {40: 0, 45: 1, 50: 2, 55: 3, 60: 4, 65: 5, 70: 6, 75: 7,
                  5: 8, 10: 9, 15: 10, 20: 11, 25: 12, 30: 13, 35: 14}

# Lookup table that mirrors the 7 row bits (bit0 <-> bit6).
_REV7 = bytearray(128)
for _i in range(128):
    _r = 0
    for _b in range(7):
        if _i & (1 << _b):
            _r |= 1 << (6 - _b)
    _REV7[_i] = _r
del _i, _r, _b


# ---------------------------------------------------------------------------
# Fonts. Glyphs are stored column by column, bit 0 = top pixel.
# ---------------------------------------------------------------------------
_FONT_5X7_DATA = (
    b"\x00\x00\x00\x00\x00\x00\x00\x5f\x00\x00\x00\x07\x00\x07\x00\x14\x7f\x14\x7f\x14"
    b"\x24\x2a\x7f\x2a\x12\x23\x13\x08\x64\x62\x36\x49\x55\x22\x50\x00\x05\x03\x00\x00"
    b"\x00\x1c\x22\x41\x00\x00\x41\x22\x1c\x00\x08\x2a\x1c\x2a\x08\x08\x08\x3e\x08\x08"
    b"\x00\x50\x30\x00\x00\x08\x08\x08\x08\x08\x00\x60\x60\x00\x00\x20\x10\x08\x04\x02"
    b"\x3e\x51\x49\x45\x3e\x00\x42\x7f\x40\x00\x42\x61\x51\x49\x46\x21\x41\x45\x4b\x31"
    b"\x18\x14\x12\x7f\x10\x27\x45\x45\x45\x39\x3c\x4a\x49\x49\x30\x01\x71\x09\x05\x03"
    b"\x36\x49\x49\x49\x36\x06\x49\x49\x29\x1e\x00\x36\x36\x00\x00\x00\x56\x36\x00\x00"
    b"\x08\x14\x22\x41\x00\x14\x14\x14\x14\x14\x00\x41\x22\x14\x08\x02\x01\x51\x09\x06"
    b"\x32\x49\x79\x41\x3e\x7e\x11\x11\x11\x7e\x7f\x49\x49\x49\x36\x3e\x41\x41\x41\x22"
    b"\x7f\x41\x41\x22\x1c\x7f\x49\x49\x49\x41\x7f\x09\x09\x09\x01\x3e\x41\x49\x49\x7a"
    b"\x7f\x08\x08\x08\x7f\x00\x41\x7f\x41\x00\x20\x40\x41\x3f\x01\x7f\x08\x14\x22\x41"
    b"\x7f\x40\x40\x40\x40\x7f\x02\x0c\x02\x7f\x7f\x04\x08\x10\x7f\x3e\x41\x41\x41\x3e"
    b"\x7f\x09\x09\x09\x06\x3e\x41\x51\x21\x5e\x7f\x09\x19\x29\x46\x46\x49\x49\x49\x31"
    b"\x01\x01\x7f\x01\x01\x3f\x40\x40\x40\x3f\x1f\x20\x40\x20\x1f\x3f\x40\x38\x40\x3f"
    b"\x63\x14\x08\x14\x63\x07\x08\x70\x08\x07\x61\x51\x49\x45\x43\x00\x7f\x41\x41\x00"
    b"\x02\x04\x08\x10\x20\x00\x41\x41\x7f\x00\x04\x02\x01\x02\x04\x40\x40\x40\x40\x40"
    b"\x00\x01\x02\x04\x00\x20\x54\x54\x54\x78\x7f\x48\x44\x44\x38\x38\x44\x44\x44\x20"
    b"\x38\x44\x44\x48\x7f\x38\x54\x54\x54\x18\x08\x7e\x09\x01\x02\x0c\x52\x52\x52\x3e"
    b"\x7f\x08\x04\x04\x78\x00\x44\x7d\x40\x00\x20\x40\x44\x3d\x00\x7f\x10\x28\x44\x00"
    b"\x00\x41\x7f\x40\x00\x7c\x04\x18\x04\x78\x7c\x08\x04\x04\x78\x38\x44\x44\x44\x38"
    b"\x7c\x14\x14\x14\x08\x08\x14\x14\x18\x7c\x7c\x08\x04\x04\x08\x48\x54\x54\x54\x20"
    b"\x04\x3f\x44\x40\x20\x3c\x40\x40\x20\x7c\x1c\x20\x40\x20\x1c\x3c\x40\x30\x40\x3c"
    b"\x44\x28\x10\x28\x44\x0c\x50\x50\x50\x3c\x44\x64\x54\x4c\x44\x00\x08\x36\x41\x00"
    b"\x00\x00\x7f\x00\x00\x00\x41\x36\x08\x00\x08\x04\x08\x10\x08"
)

_FONT_3X5_CHARS = ' !"#%\'()*+,-./0123456789:<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
_FONT_3X5_DATA = (
    b"\x00\x00\x00\x00\x17\x00\x03\x00\x03\x1f\x0a\x1f\x19\x04\x13\x00\x03\x00\x00\x0e\x11"
    b"\x11\x0e\x00\x0a\x04\x0a\x04\x0e\x04\x10\x08\x00\x04\x04\x04\x00\x10\x00\x18\x04\x03"
    b"\x1f\x11\x1f\x12\x1f\x10\x1d\x15\x17\x15\x15\x1f\x07\x04\x1f\x17\x15\x1d\x1f\x15\x1d"
    b"\x01\x19\x07\x1f\x15\x1f\x17\x15\x1f\x00\x0a\x00\x04\x0a\x11\x0a\x0a\x0a\x11\x0a\x04"
    b"\x01\x15\x02\x1e\x05\x1e\x1f\x15\x0a\x0e\x11\x11\x1f\x11\x0e\x1f\x15\x11\x1f\x05\x01"
    b"\x0e\x11\x1d\x1f\x04\x1f\x11\x1f\x11\x08\x10\x0f\x1f\x04\x1b\x1f\x10\x10\x1f\x06\x1f"
    b"\x1f\x01\x1e\x0e\x11\x0e\x1f\x05\x02\x0e\x19\x16\x1f\x05\x1a\x12\x15\x09\x01\x1f\x01"
    b"\x1f\x10\x1f\x0f\x10\x0f\x1f\x0c\x1f\x1b\x04\x1b\x03\x1c\x03\x19\x15\x13\x10\x10\x10"
)


class Font:
    """A fixed-width bitmap font (column-major, bit 0 = top row)."""

    def __init__(self, name, width, height, data, chars=None):
        self.name = name
        self.width = width
        self.height = height
        self._data = data
        self._chars = chars  # None = contiguous ASCII starting at ' '
        self._count = len(data) // width
        self._fallback = self._index("?")

    def _index(self, ch):
        if self._chars is None:
            i = ord(ch) - 32
            return i if 0 <= i < self._count else -1
        i = self._chars.find(ch)
        if i < 0 and "a" <= ch <= "z":
            i = self._chars.find(ch.upper())
        return i

    def glyph(self, ch):
        """Return the column bytes for one character ('?' if unsupported)."""
        i = self._index(ch)
        if i < 0:
            i = self._fallback
        w = self.width
        return self._data[i * w:(i + 1) * w]


FONT_5X7 = Font("5x7", 5, 7, _FONT_5X7_DATA)
FONT_3X5 = Font("3x5", 3, 5, _FONT_3X5_DATA, _FONT_3X5_CHARS)

FONTS = {
    "large": FONT_5X7, "5x7": FONT_5X7, "normal": FONT_5X7,
    "small": FONT_3X5, "3x5": FONT_3X5,
}


def _get_font(font):
    if isinstance(font, Font):
        return font
    try:
        return FONTS[str(font).lower()]
    except KeyError:
        raise ValueError("unknown font %r (use 'large' or 'small')" % (font,))


def _glyph_columns(ch, font):
    """5 display columns (bit 0 = top) with `ch` centred on one board."""
    f = _get_font(font)
    cols = bytearray(WIDTH)
    xo = (WIDTH - f.width) // 2
    yo = (HEIGHT - f.height) // 2
    for i, c in enumerate(f.glyph(ch)):
        cols[xo + i] = (c << yo) & 0x7F
    return cols


def _text_columns(text, font):
    """A strip of columns for `text`, one blank column after each glyph."""
    f = _get_font(font)
    yo = (HEIGHT - f.height) // 2
    cols = bytearray()
    for ch in text:
        for c in f.glyph(ch):
            cols.append((c << yo) & 0x7F)
        cols.append(0)
    return cols


def _is_on(v):
    if isinstance(v, str):
        return v not in " .0_-"
    return bool(v)


def scan(i2c):
    """Return the IS31FL3730 addresses (0x60-0x63) that answer on `i2c`."""
    return [a for a in i2c.scan() if a in ADDRESSES]


# ---------------------------------------------------------------------------
# Single board
# ---------------------------------------------------------------------------
class IS31FL3730:
    """One 5x7 LED matrix board.

    i2c        machine.I2C or machine.SoftI2C instance the board is on
    address    0x60..0x63 (ADDR_GND / ADDR_SCL / ADDR_SDA / ADDR_VDD)
    brightness initial brightness in percent (0-100)
    current    peak row current in mA (5-75, steps of 5). None leaves the
               chip default (40 mA). Check your LEDs' ratings.
    rotation   0 (jumper labels at the top) or 180
    auto_show  if True, drawing calls update the LEDs immediately. Set
               False and call show() yourself to batch many changes.
    """

    width = WIDTH
    height = HEIGHT

    def __init__(self, i2c, address=ADDR_GND, *, brightness=50, current=None,
                 rotation=0, auto_show=True):
        if address not in ADDRESSES:
            raise ValueError("address must be 0x60, 0x61, 0x62 or 0x63")
        self.i2c = i2c
        self.address = address
        self.auto_show = auto_show
        self._buf = bytearray(WIDTH)   # framebuffer: column x, bit y
        self._out = bytearray(WIDTH)   # register image for C1..C5
        self._one = bytearray(1)
        self._brightness = 0
        self._current = 40
        self._rotation = 0
        self._group = None
        self.rotation = rotation
        self.init(brightness, current)

    def __repr__(self):
        return "<IS31FL3730 0x%02x>" % self.address

    # -- low level ---------------------------------------------------------
    def _write_reg(self, reg, value):
        self._one[0] = value
        self.i2c.writeto_mem(self.address, reg, self._one)

    def init(self, brightness=None, current=None):
        """Reset the chip and configure it for the 5x7 matrix."""
        try:
            self._write_reg(_REG_RESET, 0x00)
        except OSError:
            raise OSError("IS31FL3730 not found at 0x%02x - check wiring, "
                          "pull-ups and address jumper" % self.address)
        self._write_reg(_REG_CONFIG, _CFG_NORMAL)
        if current is not None:
            self.current(current)
        self.brightness(self._brightness if brightness is None else brightness)
        self._buf[:] = b"\x00" * WIDTH
        self.show()

    def show(self):
        """Push the framebuffer to the LEDs."""
        buf, out = self._buf, self._out
        if self._rotation == 0:
            # x=0 is COL1 (left), y=0 is ROW7 (top) - verified on hardware
            for x in range(WIDTH):
                out[x] = _REV7[buf[x] & 0x7F]
        else:
            # upside down: x=0 is COL5, y=0 is ROW1
            for x in range(WIDTH):
                out[WIDTH - 1 - x] = buf[x] & 0x7F
        self.i2c.writeto_mem(self.address, _REG_MATRIX1, out)
        self._write_reg(_REG_UPDATE, 0x00)

    def _changed(self):
        if self.auto_show:
            self.show()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        if value not in (0, 180):
            raise ValueError("rotation must be 0 or 180")
        self._rotation = value

    # -- settings ----------------------------------------------------------
    def brightness(self, percent=None):
        """Set (0-100) or return the brightness in percent (PWM register)."""
        if percent is None:
            return self._brightness
        percent = max(0, min(100, percent))
        self._brightness = percent
        self._write_reg(_REG_PWM, int(percent * 128 / 100 + 0.5))
        self._write_reg(_REG_UPDATE, 0x00)

    def current(self, ma=None):
        """Set or return the peak row current in mA (5-75, steps of 5)."""
        if ma is None:
            return self._current
        if ma not in _CURRENT_CODES:
            raise ValueError("current must be 5, 10, ... 75 mA")
        self._current = ma
        self._write_reg(_REG_EFFECT, _CURRENT_CODES[ma])

    def shutdown(self):
        """Blank the display and enter low-power shutdown (data is kept)."""
        self._write_reg(_REG_CONFIG, _CFG_NORMAL | _CFG_SSD)

    def wake(self):
        """Leave shutdown. The chip resets its PWM register on shutdown,
        so the brightness is written again here."""
        self._write_reg(_REG_CONFIG, _CFG_NORMAL)
        self.brightness(self._brightness)

    # -- drawing -----------------------------------------------------------
    def pixel(self, x, y, value=None):
        """Get (value=None) or set the LED at column x (0-4), row y (0-6)."""
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            if value is None:
                return 0
            raise IndexError("pixel (%d, %d) is off the 5x7 matrix" % (x, y))
        if value is None:
            return (self._buf[x] >> y) & 1
        if value:
            self._buf[x] |= 1 << y
        else:
            self._buf[x] &= ~(1 << y)
        self._changed()

    def fill(self, value=1):
        """Turn every LED on (1) or off (0)."""
        v = 0x7F if value else 0
        for x in range(WIDTH):
            self._buf[x] = v
        self._changed()

    def clear(self):
        """Turn every LED off."""
        self.fill(0)

    def invert(self):
        """Toggle every LED."""
        for x in range(WIDTH):
            self._buf[x] ^= 0x7F
        self._changed()

    def bitmap(self, rows):
        """Set the whole display from 7 rows, top row first.

        Each row is either a string of 5 characters ('#', 'X', '1', 'o'... are
        on; ' ', '.', '0', '_', '-' are off) or a 5-bit int where bit 4 is
        the leftmost LED, e.g. 0b10001. A list of 5 ints/bools per row works
        too.

            d.bitmap([
                ".#.#.",
                "#####",
                "#####",
                ".###.",
                "..#..",
                ".....",
                ".....",
            ])
        """
        if len(rows) != HEIGHT:
            raise ValueError("bitmap needs 7 rows")
        for x in range(WIDTH):
            self._buf[x] = 0
        for y, row in enumerate(rows):
            for x in range(WIDTH):
                if isinstance(row, int):
                    on = row & (1 << (WIDTH - 1 - x))
                else:
                    on = _is_on(row[x]) if x < len(row) else False
                if on:
                    self._buf[x] |= 1 << y
        self._changed()

    def columns(self, cols):
        """Set the display from 5 column bytes (bit 0 = top row)."""
        for x in range(WIDTH):
            self._buf[x] = cols[x] & 0x7F
        self._changed()

    def char(self, ch, font="large"):
        """Show a single character, centred. font: 'large' (5x7) or
        'small' (3x5), or a Font object."""
        self.columns(_glyph_columns(ch, font))

    def test_pattern(self, delay_ms=60):
        """Light each LED in reading order (top-left first) to check
        orientation and that every LED works."""
        auto = self.auto_show
        self.auto_show = True
        try:
            self.clear()
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    self.pixel(x, y, 1)
                    _sleep_ms(delay_ms)
            _sleep_ms(300)
            self.clear()
        finally:
            self.auto_show = auto

    # -- text helpers (same as a MatrixGroup of one board) -------------------
    @property
    def group(self):
        if self._group is None:
            self._group = MatrixGroup([self])
        return self._group

    def text(self, text, font="large", align="left"):
        """Show the first character of `text` (see MatrixGroup.text)."""
        self.group.text(text, font, align)

    def scroll(self, text, delay_ms=80, font="large", loops=0, spacing=None):
        """Scroll `text` across this board (blocking; loops=0 = forever)."""
        self.group.scroll(text, delay_ms, font, loops, spacing)

    def scroller(self, text, delay_ms=80, font="large", loops=0, spacing=None):
        """Non-blocking scroller - see the Scroller class."""
        return self.group.scroller(text, delay_ms, font, loops, spacing)

    async def scroll_async(self, text, delay_ms=80, font="large", loops=0,
                           spacing=None):
        await self.group.scroll_async(text, delay_ms, font, loops, spacing)


# ---------------------------------------------------------------------------
# Several boards side by side
# ---------------------------------------------------------------------------
class MatrixGroup:
    """Several boards arranged left to right as one wide display.

    displays  list of IS31FL3730 objects, leftmost first. They can be on
              different I2C buses (hardware I2C, SoftI2C, or a mix).
    gap       number of "invisible" columns between neighbouring boards used
              when scrolling, so text moves smoothly across the physical gap
              between the LED matrices. 1 matches the board spacing when the
              boards are butted edge to edge; use 0 to ignore the gap.
    """

    def __init__(self, displays, gap=1):
        displays = list(displays)
        if not displays:
            raise ValueError("MatrixGroup needs at least one display")
        seen = set()
        for d in displays:
            key = (id(d.i2c), d.address)
            if key in seen:
                raise ValueError("two displays share address 0x%02x on the "
                                 "same I2C bus" % d.address)
            seen.add(key)
        self.displays = displays
        self.gap = gap
        self.width = WIDTH * len(displays)
        self.height = HEIGHT
        self.auto_show = True

    @classmethod
    def discover(cls, *i2c_buses, gap=1, **kwargs):
        """Scan the given buses and build a group from every board found,
        ordered by bus (in the order given) then by address. Extra keyword
        arguments (brightness, current, rotation) go to each IS31FL3730."""
        displays = []
        for bus in i2c_buses:
            for addr in sorted(scan(bus)):
                displays.append(IS31FL3730(bus, addr, **kwargs))
        if not displays:
            raise OSError("no IS31FL3730 boards found")
        return cls(displays, gap=gap)

    def __len__(self):
        return len(self.displays)

    def __getitem__(self, i):
        return self.displays[i]

    def __iter__(self):
        return iter(self.displays)

    # -- output ------------------------------------------------------------
    def show(self):
        for d in self.displays:
            d.show()

    def _changed(self, displays=None):
        if self.auto_show:
            for d in (self.displays if displays is None else displays):
                d.show()

    def brightness(self, percent=None):
        """Set (0-100) or return the brightness of every board."""
        if percent is None:
            return self.displays[0].brightness()
        for d in self.displays:
            d.brightness(percent)

    def current(self, ma=None):
        if ma is None:
            return self.displays[0].current()
        for d in self.displays:
            d.current(ma)

    def shutdown(self):
        for d in self.displays:
            d.shutdown()

    def wake(self):
        for d in self.displays:
            d.wake()

    # -- drawing -----------------------------------------------------------
    def pixel(self, x, y, value=None):
        """Get or set a pixel; x runs 0 .. 5*len(group)-1 across all boards."""
        if not (0 <= x < self.width and 0 <= y < HEIGHT):
            if value is None:
                return 0
            raise IndexError("pixel (%d, %d) is outside the group" % (x, y))
        d = self.displays[x // WIDTH]
        lx = x % WIDTH
        if value is None:
            return (d._buf[lx] >> y) & 1
        if value:
            d._buf[lx] |= 1 << y
        else:
            d._buf[lx] &= ~(1 << y)
        self._changed((d,))

    def fill(self, value=1):
        v = 0x7F if value else 0
        for d in self.displays:
            for x in range(WIDTH):
                d._buf[x] = v
        self._changed()

    def clear(self):
        self.fill(0)

    def bitmap(self, rows):
        """Like IS31FL3730.bitmap but each of the 7 rows spans every board
        (strings of 5*len(group) characters, or ints with the MSB = left)."""
        if len(rows) != HEIGHT:
            raise ValueError("bitmap needs 7 rows")
        w = self.width
        for d in self.displays:
            for x in range(WIDTH):
                d._buf[x] = 0
        for y, row in enumerate(rows):
            for x in range(w):
                if isinstance(row, int):
                    on = row & (1 << (w - 1 - x))
                else:
                    on = _is_on(row[x]) if x < len(row) else False
                if on:
                    self.displays[x // WIDTH]._buf[x % WIDTH] |= 1 << y
        self._changed()

    def text(self, text, font="large", align="left"):
        """Show one character per board. Only the first len(group)
        characters are shown; boards left over are blanked.

        font   'large' (5x7) or 'small' (3x5), or a Font object
        align  'left', 'center' or 'right' when the text is shorter than
               the number of boards
        """
        text = str(text)[:len(self.displays)]
        pad = len(self.displays) - len(text)
        if align == "right":
            text = " " * pad + text
        elif align in ("center", "centre"):
            text = " " * (pad // 2) + text
        for i, d in enumerate(self.displays):
            ch = text[i] if i < len(text) else " "
            d._buf[:] = _glyph_columns(ch, font)
        self._changed()

    # -- scrolling ---------------------------------------------------------
    def scroller(self, text, delay_ms=80, font="large", loops=0, spacing=None):
        """Return a Scroller for non-blocking use - call .update() often."""
        return Scroller(self, text, delay_ms, font, loops, spacing)

    def scroll(self, text, delay_ms=80, font="large", loops=0, spacing=None):
        """Scroll `text` right-to-left across all boards.

        delay_ms  time per one-column step (smaller = faster)
        loops     how many times to scroll the text; 0 = forever. This call
                  blocks until finished (Ctrl-C to stop a forever scroll);
                  use scroller() or scroll_async() to keep doing other work.
        spacing   blank columns between repeats (default: the group width)
        """
        Scroller(self, text, delay_ms, font, loops, spacing).run()

    async def scroll_async(self, text, delay_ms=80, font="large", loops=0,
                           spacing=None):
        """asyncio version of scroll()."""
        await Scroller(self, text, delay_ms, font, loops, spacing).run_async()


class Scroller:
    """Scrolls text across a MatrixGroup one column per step.

    Blocking:      s.run()
    Non-blocking:  call s.update() from your main loop; it only advances
                   when delay_ms has passed and returns False when done.
    asyncio:       await s.run_async()
    """

    def __init__(self, group, text, delay_ms=80, font="large", loops=0,
                 spacing=None):
        if isinstance(group, IS31FL3730):
            group = group.group
        self.group = group
        self.delay_ms = delay_ms
        self.loops = loops
        self.font = font
        self._spacing = spacing
        self._stride = WIDTH + group.gap
        self._view = len(group.displays) * self._stride - group.gap
        self.set_text(text)
        self._next = _ticks_ms()

    def set_text(self, text, restart=False):
        """Change the text (takes effect immediately)."""
        spacing = self._view if self._spacing is None else self._spacing
        self._strip = bytearray(spacing) + _text_columns(str(text), self.font)
        if restart or not hasattr(self, "_pos"):
            self._pos = 0
            self.count = 0
            self.done = False
        else:
            self._pos %= len(self._strip)

    def step(self):
        """Draw the current frame and advance one column."""
        if self.done:
            return
        strip = self._strip
        n = len(strip)
        pos = self._pos
        for i, d in enumerate(self.group.displays):
            base = pos + i * self._stride
            buf = d._buf
            for x in range(WIDTH):
                buf[x] = strip[(base + x) % n]
            d.show()
        pos += 1
        if pos >= n:
            pos = 0
            self.count += 1
            if self.loops and self.count >= self.loops:
                self.done = True
                self.group.clear()
        self._pos = pos

    def update(self):
        """Advance if it is time to. Returns False once all loops are done."""
        if self.done:
            return False
        now = _ticks_ms()
        if _ticks_diff(now, self._next) >= 0:
            self.step()
            self._next = _ticks_add(self._next, self.delay_ms)
            if _ticks_diff(now, self._next) > 0:  # fell behind; resync
                self._next = _ticks_add(now, self.delay_ms)
        return not self.done

    def stop(self):
        self.done = True

    def run(self):
        while not self.done:
            self.step()
            _sleep_ms(self.delay_ms)

    async def run_async(self):
        if asyncio is None:
            raise RuntimeError("asyncio is not available on this port")
        while not self.done:
            self.step()
            if hasattr(asyncio, "sleep_ms"):   # MicroPython
                await asyncio.sleep_ms(self.delay_ms)
            else:
                await asyncio.sleep(self.delay_ms / 1000)
