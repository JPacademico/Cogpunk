"""Source for the Cak-ti (D4), 2026-11-17. Run from the repo root:

    python -P art/desert/make_cakti_art.py [--preview FILE]

User, 2026-11-17: "a new weapon called cak-ti, ranged, a very fast cactus weapon that shoots thin cacti spikes ... crafted using
cactus and rusted cogs" (with a reference picture: a pixel-art gun grown from a cactus, white flowers on it, a wooden stock).
Drawn at 1x with rig.py's parts, exported 2x; pointing right like every gun (D4 rule 8).

The gun (26 x 13): a ribbed cactus column for the barrel and receiver, its arm curling up into the front sight, its tip the
muzzle; white blooms with ember hearts on its back; an oak stock and grip; a rusted cog bolted where the wood meets the cactus.
Lit from the top-left; the ribs, spines and blooms are stamped after the finish. The cactus green is a new palette ramp
(Cactus 0-4, 2026-11-17: the palette's greens were jade and verdigris only).

The spike (CaktiSpike.png): a thin cactus needle, a green base and a pale tip, rendered at 16 headings in 9 x 9 cells (never
rotated at runtime), so a needle stuck in an enemy keeps the heading it struck at.

Outputs: Content/Desert/Weapons/Cakti.png (52 x 26), Content/Desert/Weapons/CaktiSpike.png (18 x 16 cells of 18 x 18).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Canvas, flat, finish)  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

CA, OK, IV, EM, CU, BR, ST = (RAMP[k] for k in ("cactus", "oak", "ivory", "ember", "copper", "brass", "steel"))
OUT = "Content/Desert/Weapons/"
HEADINGS, SPIKE_CELL = 16, 9


def lit(lo, mid, hi, cx, cy):
    """Screen-space top-left light round a centre: hi on the lit side, lo on the shadow side."""
    def shade(i):
        d = (i.x + 0.5 - cx) * 0.6 + (i.y + 0.5 - cy)
        return hi if d < -1.4 else mid if d < 1.0 else lo
    return shade


def gun():
    cv = Canvas()
    # the oak stock and the grip
    cv.part(Xf(), Poly([(0.4, 5.0), (8.0, 4.6), (8.4, 8.4), (1.2, 9.6)]), "oak", lit(2, 3, 4, 4.0, 6.5), rust=0.0)
    cv.part(Xf(), Poly([(8.0, 7.6), (11.6, 7.6), (11.0, 12.6), (8.2, 12.6)]), "oak", lit(2, 3, 4, 9.6, 9.6), rust=0.0)
    # the cactus: the barrel column, its arm curling up into the sight, the muzzle
    cv.part(Xf(), Capsule((8.6, 6.0), (22.4, 6.0), 3.1), "cactus", lit(1, 2, 3, 15.0, 5.4), rust=0.0)
    cv.part(Xf(), Capsule((18.6, 4.0), (19.4, 0.9), 1.6), "cactus", lit(1, 2, 3, 19.0, 2.0), rust=0.0)
    finish(cv)
    # the ribs (a dark seam every third column, one shade up beside it) and the spines
    for x in (11, 14, 17, 20):
        for y in range(4, 9):
            if cv.px.get((x, y)) in CA[1:]:
                cv.put(x, y, CA[1])
                if cv.px.get((x - 1, y)) in CA[1:]:
                    cv.put(x - 1, y, CA[3] if y < 6 else CA[2])
    for (x, y) in ((10, 2), (13, 2), (16, 2), (22, 2), (12, 9), (15, 9), (21, 9), (24, 3)):
        cv.put(x, y, IV[4])
    cv.put(24, 6, CA[0])                                  # the muzzle's dark mouth
    cv.put(24, 5, CA[0])
    # the blooms: white petals round an ember heart
    for (cx, cy) in ((11, 3), (19, 0)):
        for (dx, dy, col) in ((0, -1, IV[5]), (-1, 0, IV[5]), (1, 0, IV[4]), (0, 1, IV[4]), (0, 0, EM[3])):
            cv.put(cx + dx, cy + dy, col)
    # the rusted cog bolted at the joint
    for (dx, dy, col) in ((0, -1, CU[3]), (-1, 0, CU[3]), (1, 0, CU[2]), (0, 1, CU[2]), (0, 0, BR[1]), (-1, -1, CU[1]), (1, 1, CU[1])):
        cv.put(8 + dx, 6 + dy, col)
    return cv


def spike(k):
    """The needle at heading k (k * 22.5 degrees, 0 = right, clockwise on screen): base to tip, green to pale."""
    cv = Canvas()
    a = math.radians(k * 22.5)
    c = SPIKE_CELL / 2.0
    cols = (CA[2], CA[3], IV[3], IV[3], IV[4], IV[5])
    pts = []
    for t in range(6):
        x, y = c - 0.5 + math.cos(a) * (t - 2.5), c - 0.5 + math.sin(a) * (t - 2.5)
        q = (int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))
        if q not in pts:
            pts.append(q)
            cv.put(q[0], q[1], cols[t])
    for (x, y) in pts[:-1]:                                # a shadow pixel under the shaft so it reads on pale ground
        if (x, y + 1) not in pts and (x, y + 1) not in cv.px:
            cv.put(x, y + 1, CA[0])
    return cv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    g = gun()
    img = to_image(g.px, 0, 0, 26, 13)
    export(img, OUT + "Cakti.png")
    sheet = Image.new("RGBA", (SPIKE_CELL, (SPIKE_CELL + 1) * HEADINGS - 1), (0, 0, 0, 0))
    for k in range(HEADINGS):
        sheet.alpha_composite(to_image(spike(k).px, 0, 0, SPIKE_CELL, SPIKE_CELL), (0, k * (SPIKE_CELL + 1)))
    export(sheet, OUT + "CaktiSpike.png")
    if args.preview:
        sc = 10
        out = Image.new("RGBA", (img.width * sc * 2 + 30, img.height * sc + 20), (30, 30, 36, 255))
        out.alpha_composite(img.resize((img.width * sc, img.height * sc), Image.NEAREST), (10, 10))
        light = Image.new("RGBA", (img.width * sc, img.height * sc), (196, 214, 232, 255))
        light.alpha_composite(img.resize((img.width * sc, img.height * sc), Image.NEAREST))
        out.alpha_composite(light, (img.width * sc + 20, 10))
        out.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
