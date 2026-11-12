"""Source for the Macuahuitl (D4), 2026-11-11 (user, with a reference image of an obsidian-edged wooden war club: "add a new
melee weapon crafted using 20 wood + 8 obsidian + 3 condensed tar; it should cause 23 damage and deal double damage on the
first hit against an enemy (4x if it crits), same range as the metal wrench but attacks faster and 12% base crit chance").
Run from the repo root:

    python -P art/junkyard/make_macuahuitl_art.py [--preview FILE]

A flat wooden war club along the sprite's diagonal, pointing top-right like every swung sword (D4 rule 8), the Metal
Wrench's size (34x34 art, 68x68 in game: a swing's reach is its sprite's frame):
- a ring pommel at the hand's end (a hole through it) with a red tassel hanging from it;
- a grip wrapped in red cord, a turn every other step, dark bands where the wrap starts and ends;
- the paddle: warm carved wood (Oak), lit on its upper-left face, cut into panels by dark grooves, each panel carved with
  a gilt glyph (an eye, a wave, a sun, a step);
- obsidian chips set in both edges, two steps long with a step between (dark Denim and near-black, a cold sheen on the
  lit facet), the edge the Condensed Tar glues them into;
- a squared tip, its last chips set into it.
Lit from the top-left, ramp outlines (a lighter one on the lit edge), at most 16 colours (D4 rule 5).

Coordinates: across the club t = x + y (the axis is t = AXIS; less is the lit upper-left side), along it s = x - y (the
pommel's end -31, the tip +31). Every part is a band of s and of the distance from the axis, so its edges cross the club
square.

Output: Content/Junkyard/Weapons/Macuahuitl.png (68x68).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
import make_scrap_art  # noqa: E402
from make_scrap_art import Canvas, export  # noqa: E402
from rig import RAMP  # noqa: E402

for _k, _c in zip("123456", RAMP["oak"]):              # oak: 1 (outline) .. 6 (lit)
    make_scrap_art.PAL[_k] = _c
for _k, _c in zip("KLMNOP", RAMP["crimson"]):          # crimson: K .. P
    make_scrap_art.PAL[_k] = _c
for _k, _c in zip("fghop", RAMP["denim"][:5]):         # denim (obsidian): f (near black) .. p (the sheen)
    make_scrap_art.PAL[_k] = _c
make_scrap_art.PAL["H"] = RAMP["gilt"][7]              # the glyphs' gilt
make_scrap_art.PAL["I"] = RAMP["gilt"][5]

OUT = "Content/Junkyard/Weapons/Macuahuitl.png"
SIZE = 34
AXIS = 33                                              # the diagonal from the bottom-left corner to the top-right
POMMEL = (-28, -24)                                    # s range of the ring
GRIP = (-23, -12)
SHOULDER = (-11, -10)
PADDLE = (-9, 29)
TIP = 30


def club():
    c = Canvas(SIZE, SIZE)
    for y in range(SIZE):
        for x in range(SIZE):
            t, s = x + y, x - y
            a = t - AXIS                               # across: < 0 the lit upper-left side
            ch = None
            if GRIP[0] <= s <= GRIP[1] and abs(a) <= 2:
                if s in (GRIP[0], GRIP[1]):
                    ch = "1" if a >= 0 else "2"        # the wrap's dark bands
                elif a == -2:
                    ch = "O" if s % 2 else "N"         # the lit edge of the cord
                elif a == 2:
                    ch = "K"                           # the outline under
                else:
                    turn = (s + a) % 4 in (0, 1)       # the cord's turns, slanting
                    ch = ("N" if a < 0 else "M") if turn else ("M" if a < 0 else "L")
            elif SHOULDER[0] <= s <= SHOULDER[1] and abs(a) <= 4:
                ch = "5" if a <= -3 else ("1" if a >= 3 else ("4" if a < 0 else "3"))
            elif PADDLE[0] <= s <= TIP and abs(a) <= 7:
                ch = paddle(s, a)
            if ch:
                c.set(x, y, ch)
    # the ring pommel: a disc round the axis at the hand's end, a hole through it
    pc = ((POMMEL[0] + POMMEL[1]) / 2.0)
    px, py = (AXIS + pc) / 2.0, (AXIS - pc) / 2.0
    for y in range(SIZE):
        for x in range(SIZE):
            d = math.hypot(x + 0.5 - (px + 0.5), y + 0.5 - (py + 0.5))
            if d <= 2.6:
                lit = (x + 0.5 - (px + 0.5)) + (y + 0.5 - (py + 0.5)) < -0.6
                c.set(x, y, "1" if d > 1.9 and not lit else ("5" if lit else "3"))
                if d <= 0.8:
                    c.set(x, y, ".")                   # the hole
    # the tassel: red strands from the ring, swung out behind the swing (down and right)
    tx, ty = int(round(px)) + 2, int(round(py)) + 1
    for k, (dx, dy) in enumerate(((0, 0), (1, 1), (2, 1), (3, 2), (1, 2), (2, 3), (4, 2))):
        if 0 <= ty + dy < SIZE and 0 <= tx + dx < SIZE and c.get(tx + dx, ty + dy) == ".":
            c.set(tx + dx, ty + dy, "N" if k % 2 == 0 else "M")
    return c


def paddle(s, a):
    """The paddle at (s, a): wood within |a| <= 4, obsidian chips at |a| 5..6 (two steps of every three, the middle of
    each pointing out to 7: teeth), the tar seam (f) between chips."""
    edge = abs(a)
    step = (s - PADDLE[0]) % 3
    chip = step != 2 and s < TIP
    if edge >= 5:
        if not chip:
            return "f" if edge == 5 else None              # the tar seam between chips
        if edge == 7:
            return "f" if step == 0 else None              # each chip's point
        lit = a < 0
        if edge == 5:
            return "p" if lit else "g"                     # the chip's inner facet: the sheen on the lit side
        return "h" if lit else "f"
    if s >= TIP - 1:                                       # the squared tip
        return "2" if a >= 0 else "4"
    k = (s - PADDLE[0]) // 7                               # panels between grooves every 7 steps
    local = (s - PADDLE[0]) % 7
    if local == 0:
        return "1" if a >= -3 else "2"                     # a groove across the paddle
    if edge == 4:
        return "5" if a < 0 else "2"                       # the paddle's rim: lit upper-left, shaded below
    if 2 <= local <= 5 and edge <= 2:                      # the panel's carved field, a little darker
        mark = abs(local - 3.5) + abs(a) <= 1.6 if k % 2 == 0 else (abs(a) <= 1 and local in (3, 4))
        if mark:
            return "H" if a <= 0 else "I"                  # the gilt glyph: a diamond, or a bar
        return "3"
    return "4" if a < 0 else "3"


def preview(path):
    c = club()
    im = Image.new("RGBA", (SIZE, SIZE), (60, 60, 70, 255))
    for y in range(SIZE):
        for x in range(SIZE):
            ch = c.get(x, y)
            if ch != ".":
                im.putpixel((x, y), make_scrap_art.PAL[ch] + (255,))
    im.resize((SIZE * 10, SIZE * 10), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export(club(), OUT)
