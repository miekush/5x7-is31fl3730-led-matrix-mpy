"""
video_to_matrix.py - convert a video into a frame file for the 5x7 LED
matrix boards (run this on your PC, not on the microcontroller).

    pip install opencv-python numpy
    python video_to_matrix.py "bad-apple.mp4" bad_apple.bin --boards 1 --fps 30

Options
  --boards N      number of 5x7 boards side by side (default 1)
  --gap G         hidden columns between boards, same as MatrixGroup(gap=)
                  (default 1, matches boards butted edge to edge)
  --fps F         output frame rate; source frames are dropped to match
                  (default 30)
  --fit MODE      'crop' keeps the aspect ratio and crops the sides (default),
                  'stretch' squeezes the whole frame onto the LEDs
  --threshold T   0-255 brightness cut-off for "LED on" (default 128)
  --invert        light the LEDs for dark pixels instead of bright ones
  --preview F     also write an upscaled preview video of the result

Output format (all little-endian):
  header  4s  magic b"LEDV"
          B   version (1)
          B   number of boards
          B   frame rate
          B   reserved (0)
          I   frame count
  frames  5 * boards bytes per frame: for each board, left to right, its 5
          columns left to right; bit 0 = top row. This is exactly the
          IS31FL3730 driver's framebuffer layout.
"""

import argparse
import struct

import cv2
import numpy as np

W, H = 5, 7


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("output")
    ap.add_argument("--boards", type=int, default=1)
    ap.add_argument("--gap", type=int, default=1)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--fit", choices=("crop", "stretch"), default="crop")
    ap.add_argument("--threshold", type=int, default=128)
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--preview")
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    if not cap.isOpened():
        raise SystemExit("could not open %s" % a.video)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # The virtual canvas includes the hidden gap columns between boards so
    # the picture keeps its proportions across the physical gaps.
    canvas_w = a.boards * W + (a.boards - 1) * a.gap
    visible = [b * (W + a.gap) + x for b in range(a.boards) for x in range(W)]

    # Crop box for --fit crop (LED pitch is the same in x and y)
    target = canvas_w / H
    if a.fit == "crop":
        if src_w / src_h > target:
            cw, ch = int(round(src_h * target)), src_h
        else:
            cw, ch = src_w, int(round(src_w / target))
        x0, y0 = (src_w - cw) // 2, (src_h - ch) // 2
    else:
        x0, y0, cw, ch = 0, 0, src_w, src_h

    out_fps = min(a.fps, src_fps)
    step = src_fps / out_fps
    frames = []
    previews = []
    next_pick = 0.0
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i + 0.5 >= next_pick:
            next_pick += step
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)[y0:y0 + ch, x0:x0 + cw]
            small = cv2.resize(gray, (canvas_w, H), interpolation=cv2.INTER_AREA)
            on = small >= a.threshold
            if a.invert:
                on = ~on
            on = on[:, visible]                       # drop the gap columns
            cols = bytearray()
            for x in range(on.shape[1]):
                b = 0
                for y in range(H):
                    if on[y, x]:
                        b |= 1 << y
                cols.append(b)
            frames.append(bytes(cols))
            if a.preview:
                previews.append(on)
        i += 1

    with open(a.output, "wb") as f:
        f.write(struct.pack("<4sBBBBI", b"LEDV", 1, a.boards,
                            int(round(out_fps)), 0, len(frames)))
        for fr in frames:
            f.write(fr)

    size = 12 + len(frames) * W * a.boards
    print("%d frames at %g fps (%.1f s) for %d board(s) -> %s (%.1f KB)"
          % (len(frames), out_fps, len(frames) / out_fps, a.boards,
             a.output, size / 1024))

    if a.preview:
        write_preview(a.preview, previews, out_fps, a.boards, a.gap)
        print("preview ->", a.preview)


def write_preview(path, previews, fps, boards, gap, cell=24):
    """Draw each frame as round LEDs so you can check the result."""
    w = (boards * W + (boards - 1) * gap) * cell
    h = H * cell
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for on in previews:
        img = np.full((h, w, 3), 25, np.uint8)
        for bx in range(boards):
            for x in range(W):
                for y in range(H):
                    px = (bx * (W + gap) + x) * cell + cell // 2
                    py = y * cell + cell // 2
                    col = (40, 60, 255) if on[y, bx * W + x] else (20, 20, 70)
                    cv2.circle(img, (px, py), cell // 2 - 3, col, -1)
        vw.write(img)
    vw.release()


if __name__ == "__main__":
    main()
