"""Source for the Jade Refractor (D4), 2026-11-24 (user: "unlocks the "jade refractor" mechanist weapon crafted using the
diamond cutter weapon + jade + glass. A direct upgrade for the diamond cutter that should shoot a continuous thin jade
colored laser"). Run from the repo root:

    python -P art/mechanist/make_jade_refractor_art.py [--preview FILE]

Design (my calls): the Diamond Cutter (art/mechanist/make_diamond_cutter_art.py) rebuilt as its upgrade, a gun that points
right (D4 rule 8):
* The cutter's brass receiver, longer and gilded, a jade inlay along its flank and a pressure gauge on top (the needle in the
  red: a continuous beam).
* A steel focusing tube banded in gilt, and round it a coil of jade-green copper (the refraction coil).
* At the muzzle a glass housing (pale, clear: the steam ramp's light end over aether's) holding a cut jade lens, its point
  forward: the lit facets mint, the far ones deep green.
* The grip and trigger of the cutter.
Its beam (JadeRefractorBeam, drawn added onto the scene): a 1 px pale core between jade edges, 4 frames that run a shimmer
along it. The spark at the lens and where the beam stops: a jade four-point star, 4 frames.
At most 16 colours (D4 rule 5).

Outputs:
    Content/Research/Weapons/JadeRefractor.png        64x32
    Content/Research/Weapons/JadeRefractorBeam.png    16x6 a frame, 4 frames, stride 8
    Content/Research/Weapons/JadeRefractorSpark.png   14x14 a frame, 4 frames, stride 16
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, sheet, preview  # noqa: E402
from rig import RAMP  # noqa: E402

GI, ST, HD, EM, SM = RAMP["gilt"], RAMP["steel"], RAMP["hide"], RAMP["emerald"], RAMP["steam"]
GOLD = (GI[1], GI[3], GI[5], GI[7], GI[8])
STEEL = (ST[1], ST[3], ST[6], SM[2])
GRIP = (GI[1], HD[2], HD[4])
JADE = (EM[1], EM[2], EM[3], EM[5], EM[6])
GLASS = (EM[1], SM[1], SM[2])                              # the housing: clear, outlined in the jade's darkest
OUT = "Content/Research/Weapons/"
W, H = 32, 16
TIP = (31, 7)                                              # the lens's point (1x), where the beam leaves
GRIP_AT = (7, 10)                                          # where the hand holds it (1x): JadeRefractor.GripOrigin x 2


def gun():
    p = Pix(W, H)
    # the grip, raked back under the receiver, a gilt ring round it
    for y, (x0, x1) in zip(range(10, 16), ((5, 8), (5, 8), (4, 7), (4, 7), (4, 6), (4, 6))):
        for x in range(x0, x1 + 1):
            p.put(x, y, GRIP, 2 if x == x0 else 1)
    for x in range(4, 8):
        p.put(x, 12, GOLD, 3 if x == 4 else 2)
    for (x, y) in ((9, 11), (9, 12), (12, 11), (12, 12), (10, 13), (11, 13)):   # the trigger guard and trigger
        p.put(x, y, STEEL, 1)
    p.put(10, 11, STEEL, 2)
    # the receiver: gilt, lit from the top, a jade inlay along it, the end cap
    shades = {4: 4, 5: 4, 6: 3, 7: 3, 8: 2, 9: 2, 10: 1}
    for y in range(4, 11):
        for x in range(2, 15):
            p.put(x, y, GOLD, shades[y] + (1 if x == 2 and shades[y] < 4 else 0))
    for x in range(4, 13):                                 # the inlay
        p.put(x, 7, JADE, 3 if x < 8 else 2)
        p.put(x, 8, JADE, 1)
    for y in range(5, 10):                                 # the end cap
        p.put(1, y, GOLD, 4 if y < 7 else 3)
    for y in range(6, 9):
        p.put(0, y, GOLD, 3)
    # the gauge on top, its needle in the red
    for (x, y) in ((7, 0), (8, 0), (9, 0), (6, 1), (10, 1), (6, 2), (10, 2), (6, 3), (10, 3)):
        p.put(x, y, GOLD, 3)
    for (x, y) in ((7, 1), (8, 1), (9, 1), (7, 2), (8, 2), (9, 2), (7, 3), (8, 3), (9, 3)):
        p.put(x, y, STEEL, 3)
    p.put(8, 2, STEEL, 0)
    p.put(9, 2, STEEL, 0)
    # the focusing tube and the jade coil round it
    tube = {5: 2, 6: 3, 7: 2, 8: 1, 9: 1}
    for y in range(5, 10):
        for x in range(15, 25):
            p.put(x, y, STEEL, tube[y])
    for x in range(16, 24, 2):                             # the coil: turns of jade wire over the tube
        for y in range(4, 11):
            p.put(x, y, JADE, 3 if y < 7 else 2 if y < 9 else 1)
    for y in range(3, 12):                                 # the gilt collar holding the housing
        p.put(25, y, GOLD, 4)
        p.put(26, y, GOLD, 2)
    # the glass housing and the jade lens in it, point forward
    for y in range(4, 11):
        for x in range(27, 31):
            p.put(x, y, GLASS, 2 if y < 6 else 1)
    span = {5: (28, 29), 6: (27, 30), 7: (27, 31), 8: (27, 30), 9: (28, 29)}
    for y, (x0, x1) in span.items():
        for x in range(x0, x1 + 1):
            p.put(x, y, JADE, (4 if x <= 28 else 3) if y < 7 else (2 if x <= 28 else 1))
    p.outline(skip=(tuple(tuple(c) for c in GLASS),))
    # the glass's own rim (its outline is the jade's darkest), stamps after the outline
    for x in range(27, 31):
        p.put(x, 3, GLASS, 0)
        p.put(x, 11, GLASS, 0)
    p.put(31, 4, GLASS, 0)
    p.put(31, 10, GLASS, 0)
    p.put(13, 5, GOLD, 4)                                  # rivets
    p.put(13, 9, GOLD, 4)
    p.put(3, 6, GOLD, 4)
    p.put(28, 6, JADE, 4)                                  # the lens's sparkle
    p.put(28, 5, GLASS, 2)
    return p


def beam():
    """4 frames, 8x3 at 1x: a pale core between jade edges, with a bright knot that runs along the line frame by frame."""
    frames = []
    for k in range(4):
        p = Pix(8, 3)
        for x in range(8):
            knot = (x - 2 * k) % 8 < 2
            p.put(x, 0, JADE, 3 if knot else 2)
            p.put(x, 1, JADE, 4 if knot else 3)
            p.put(x, 2, JADE, 3 if knot else 2)
        frames.append(p.image())
    return frames


def spark():
    """4 frames, 7x7 at 1x: a jade four-point star that turns as it pulses (held while the beam burns)."""
    rows = (
        ("...a...", "...b...", "..aba..", "abbcbba", "..aba..", "...b...", "...a..."),
        (".......", ".a...a.", "..bab..", "..aca..", "..bab..", ".a...a.", "......."),
        ("...a...", "...a...", "...b...", ".abcba.", "...b...", "...a...", "...a..."),
        (".......", "..a.a..", "...b...", "..bcb..", "...b...", "..a.a..", "......."),
    )
    key = {"a": (JADE, 2), "b": (JADE, 3), "c": (JADE, 4)}
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
    if a.preview:
        preview([g.image()] + beam() + spark(), a.preview, scale=8)
        return
    export(g.image(), OUT + "JadeRefractor.png")
    export(sheet(beam()), OUT + "JadeRefractorBeam.png")
    export(sheet(spark()), OUT + "JadeRefractorSpark.png")


if __name__ == "__main__":
    main()
