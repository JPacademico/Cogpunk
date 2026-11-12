"""Source for the Diamond Cutter (D4), 2026-11-11 (user: "add a new mechanist weapon called diamond cutter, it should be
crafted using a diamond and some platinum/gold bars. it should fire a precise instantaneous thin laser that can pierce up
to 3 enemies with 12% crit chance but 19 damage and 30 use time (8 steam per attack), it should not consume ammo and
should ignore 20% of enemy defense"). Run from the repo root:

    python -P art/mechanist/make_diamond_cutter_art.py [--preview FILE]

Design (my calls): a jeweller's steam cutter, a gun that points right (D4 rule 8).
* A brass receiver lit from the top-left, a panel seam and two rivets, a steel valve wheel on its flank and a round
  pressure gauge on top (a pale dial, the needle up at full pressure), a rounded brass end cap.
* A slim steel focusing tube with a gleam along its top, two brass bands round it and a brass steam line under it.
* At the muzzle a brass collar holding a cut diamond, its point forward: the lit facets white, the far ones in cool
  blues (the denim ramp from its 3rd shade), so the gem reads as glass, not metal.
* A leather grip raked back, a brass ring round it, a steel trigger in a steel guard.
* Its beam (DiamondCutterBeam, drawn added onto the scene): a 1 px white core between two pale blue edges, 3 frames
  (full, thinning, broken into sparkles). The spark (DiamondCutterSpark) at the muzzle and where the beam stops: a
  four-point star, 4 frames (flash, cross, small, dot).
At most 16 colours (D4 rule 5).

Outputs:
    Content/Mechanist/Weapons/DiamondCutter.png        56x28
    Content/Mechanist/Weapons/DiamondCutterBeam.png    16x6 a frame, 3 frames, stride 8
    Content/Mechanist/Weapons/DiamondCutterSpark.png   14x14 a frame, 4 frames, stride 16
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, sheet, preview  # noqa: E402
from rig import RAMP  # noqa: E402

BR, _ST, _HD = RAMP["brass"], RAMP["steel"], RAMP["hide"]
DN, SM = RAMP["denim"], RAMP["steam"]
# Compact ramps, index 0 the outline, so the whole gun fits the 16-colour cap (D4 rule 5): steel's gleam is the gem's
# white, the leather's outline is brass's darkest.
ST = (_ST[0], _ST[3], _ST[6], SM[2])
HD = (BR[0], _HD[2], _HD[4])
GEM = (DN[2], DN[4], DN[5], SM[2], SM[3])                 # the diamond: cool blues up to white
OUT = "Content/Mechanist/Weapons/"
W, H = 28, 14
TIP = (27, 6)                                             # the diamond's point (1x), where the beam leaves


def gun():
    p = Pix(W, H)
    # the grip, raked back, behind the receiver
    for y, (x0, x1) in zip(range(9, 14), ((4, 7), (4, 7), (3, 6), (3, 6), (3, 5))):
        for x in range(x0, x1 + 1):
            p.put(x, y, HD, 2 if x == x0 else 1)
    for x in range(3, 7):                                 # a brass ring round it
        p.put(x, 11, BR, 4 if x == 3 else 3)
    # the trigger guard and trigger
    for (x, y) in ((8, 10), (8, 11), (11, 10), (11, 11), (9, 12), (10, 12)):
        p.put(x, y, ST, 1)
    p.put(9, 10, ST, 2)
    # the receiver
    shades = {3: 4, 4: 4, 5: 3, 6: 3, 7: 2, 8: 2, 9: 1}
    for y in range(3, 10):
        for x in range(2, 13):
            p.put(x, y, BR, shades[y] + (1 if x == 2 else 0))
    for y in range(4, 9):                                 # a panel seam, its front edge catching the light
        p.put(9, y, BR, 1)
        p.put(10, y, BR, 4)
    for (x, y, i) in ((5, 6, 3), (6, 6, 2), (5, 7, 2), (6, 7, 1)):   # the valve wheel
        p.put(x, y, ST, i)
    for y in range(4, 9):                                 # the end cap
        p.put(1, y, BR, 4 if y < 6 else 3)
    for y in range(5, 8):
        p.put(0, y, BR, 3)
    # the gauge on top
    for (x, y) in ((6, 0), (7, 0), (8, 0), (5, 1), (9, 1), (5, 2), (9, 2)):
        p.put(x, y, BR, 3)
    for (x, y) in ((6, 1), (7, 1), (8, 1), (6, 2), (7, 2), (8, 2)):
        p.put(x, y, ST, 3)
    p.put(7, 2, ST, 0)                                    # the needle, up and right: full pressure
    p.put(8, 1, ST, 0)
    # the focusing tube
    tube = {4: 2, 5: 3, 6: 2, 7: 1, 8: 1}
    for y in range(4, 9):
        for x in range(13, 22):
            p.put(x, y, ST, tube[y])
    for x in range(13, 21):                               # the steam line under it
        p.put(x, 9, BR, 2)
    # the bands, the collar
    for x0 in (15, 19):
        for y in range(3, 10):
            p.put(x0, y, BR, 4)
            p.put(x0 + 1, y, BR, 2)
    for y in range(2, 11):
        p.put(21, y, BR, 4)
        p.put(22, y, BR, 2)
    # the diamond, point forward: lit facets white, the far ones blue
    span = {2: (24, 24), 3: (23, 25), 4: (23, 26), 5: (23, 27), 6: (23, 27), 7: (23, 27), 8: (23, 26), 9: (23, 25), 10: (24, 24)}
    for y, (x0, x1) in span.items():
        for x in range(x0, x1 + 1):
            if y < 6:
                i = 3 if x <= 24 else 2
            else:
                i = 2 if x <= 24 else 1
            p.put(x, y, GEM, i)
    p.put(23, 2, BR, 4)                                   # the collar's lips over the gem
    p.put(23, 10, BR, 2)
    p.outline()
    # stamps after the outline
    p.put(11, 5, BR, 5)                                   # rivets
    p.put(11, 7, BR, 5)
    p.put(3, 5, BR, 5)
    p.put(24, 4, GEM, 4)                                  # the gem's sparkle
    p.put(14, 5, ST, 3)
    return p


def beam():
    """3 frames, 8x3 at 1x: a white core between pale blue edges; thinning; broken into sparkles."""
    frames = []
    for k in range(3):
        p = Pix(8, 3)
        for x in range(8):
            if k == 0:
                p.put(x, 0, GEM, 2)
                p.put(x, 1, GEM, 4)
                p.put(x, 2, GEM, 2)
            elif k == 1:
                p.put(x, 1, GEM, 3)
                if x % 4 == 1:
                    p.put(x, 0, GEM, 1)
                    p.put(x, 2, GEM, 1)
            elif x % 3 == 0:
                p.put(x, 1, GEM, 3 if x % 2 == 0 else 2)
        frames.append(p.image())
    return frames


def spark():
    """4 frames, 7x7 at 1x: a four-point star flashing out to a dot."""
    rows = (
        ("...a...", "...b...", "..aba..", "abbcbba", "..aba..", "...b...", "...a..."),
        ("...a...", "...a...", "...b...", ".abcba.", "...b...", "...a...", "...a..."),
        (".......", ".......", "...a...", "..aca..", "...a...", ".......", "......."),
        (".......", ".......", ".......", "...b...", ".......", ".......", "......."),
    )
    key = {"a": (GEM, 2), "b": (GEM, 3), "c": (GEM, 4)}
    frames = []
    for r in rows:
        p = Pix(7, 7)
        p.rows(0, 0, r, key)
        frames.append(p.image())
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    g = gun()
    print("gun colours:", len(g.colours()))
    export(g.image(), OUT + "DiamondCutter.png")
    export(sheet(beam()), OUT + "DiamondCutterBeam.png")
    export(sheet(spark()), OUT + "DiamondCutterSpark.png")
    if a.preview:
        preview([g.image()] + beam() + spark(), a.preview, scale=6)


if __name__ == "__main__":
    main()
