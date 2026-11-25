"""The Cogpunk accessory slot (D4), 2026-11-25 (user: "add a cogpunk stylized aditional accessory slot ... it should be locked
for now"). Run from the repo root:

    python -P art/equipment/make_slot_art.py [--preview FILE]

Vanilla's slot back is 52 x 52 (26 x 26 art): ours is a riveted brass frame (lit from the top-left, an inner bevel) round a
dark steel field with a cog's outline sunk in it; the vanity slot's frame is copper and the dye slot's steel (vanilla tells
the three apart by colour too). The icons (16 x 16 art): a padlock (a steel body, a brass shackle, a keyhole) while locked,
and a cog while unlocked and empty.

Outputs (Content/Equipment/): CogpunkSlot_Back.png, _BackVanity.png, _BackDye.png, _Lock.png, _Cog.png.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

G, CU, ST = RAMP["gilt"], RAMP["copper"], RAMP["steel"]
OUT = "Content/Equipment/"


def back(frame):
    """26 x 26: an outline, a 3 px frame lit from the top-left with a bevel, rivets in the corners, the dark field with a sunk
    cog. `frame` is the frame's ramp (darkest first)."""
    n = len(frame)
    px = {}
    for y in range(26):
        for x in range(26):
            edge = min(x, y, 25 - x, 25 - y)
            if edge == 0:
                px[(x, y)] = frame[0]
            elif edge <= 3:
                lit = (x < y and x + y < 25) or (y <= x and x + y < 25)       # the top and left halves of the frame
                top_left = x + y < 25
                if edge == 1:
                    px[(x, y)] = frame[min(n - 1, n - 2)] if top_left else frame[2]
                elif edge == 3:
                    px[(x, y)] = frame[1] if top_left else frame[min(n - 1, 3)]    # the bevel turns at the inner edge
                else:
                    px[(x, y)] = frame[min(n - 1, n - 3)] if lit else frame[min(n - 1, 3)]
            else:
                px[(x, y)] = ST[1] if (x + y) % 7 else ST[2]                  # the field, a faint diagonal grain
    for (cx, cy) in ((2, 2), (23, 2), (2, 23), (23, 23)):                     # rivets
        px[(cx, cy)] = ST[7]
        px[(cx + 1, cy + 1) if cx < 13 else (cx - 1, cy + 1)] = ST[3]
    for y in range(4, 22):                                                    # a cog's outline sunk in the field
        for x in range(4, 22):
            dx, dy = x + 0.5 - 13.0, y + 0.5 - 13.0
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            r = 6.2 + (1.2 if math.cos(a * 8) > 0.3 else 0.0)
            if abs(d - r) < 0.55 or abs(d - 2.4) < 0.5:
                px[(x, y)] = ST[2] if dx + dy < 0 else ST[0]
    return px


def lock():
    """16 x 16: a padlock: a brass shackle over a steel body lit from the top-left, a keyhole, an outline in each part's
    darkest shade."""
    px = {}
    for y in range(1, 8):                                                     # the shackle: a brass arch
        for x in range(3, 13):
            d = math.hypot((x + 0.5 - 8.0) / 4.6, (y + 0.5 - 7.0) / 5.6)
            if 0.62 < d <= 1.0:
                px[(x, y)] = G[7] if x < 8 else G[5]
    for y in range(7, 15):                                                    # the body
        for x in range(3, 13):
            lit = (x - 3) + (y - 7)
            px[(x, y)] = ST[7] if lit < 4 else ST[6] if lit < 9 else ST[5] if lit < 13 else ST[4]
    for (x, y) in ((7, 9), (8, 9), (7, 10), (8, 10), (7, 11), (7, 12)):       # the keyhole
        px[(x, y)] = ST[1]
    out = dict(px)
    for (x, y), c in px.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px:
                out[q] = G[1] if c in G else ST[1]
    return out


def cog():
    """16 x 16: a brass cog with eight teeth and a hole, lit from the top-left."""
    px = {}
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - 8.0, y + 0.5 - 8.0
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            r = 5.0 + (1.6 if math.cos(a * 8) > 0.3 else 0.0)
            if 1.8 < d <= r:
                lit = -(dx + dy) / 8.0
                px[(x, y)] = G[7] if lit > 0.3 else G[6] if lit > -0.1 else G[5] if lit > -0.45 else G[4]
    out = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px:
                out[q] = G[1]
    return out


def img(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    ims = {"CogpunkSlot_Back": img(back(G), 26, 26), "CogpunkSlot_BackVanity": img(back(CU), 26, 26),
           "CogpunkSlot_BackDye": img(back(ST), 26, 26), "CogpunkSlot_Lock": img(lock(), 16, 16), "CogpunkSlot_Cog": img(cog(), 16, 16)}
    for name, im in ims.items():
        export(im, OUT + name + ".png")
    if a.preview:
        sc = 4
        out = Image.new("RGBA", (3 * (52 * sc // 2 + 8) + 2 * (32 * sc // 2 + 8) + 8, 52 * sc // 2 + 16), (24, 26, 40, 255))
        x = 8
        for name in ("CogpunkSlot_Back", "CogpunkSlot_BackVanity", "CogpunkSlot_BackDye"):
            bk = ims[name].resize((26 * sc, 26 * sc), Image.NEAREST)
            if name == "CogpunkSlot_Back":
                bk.alpha_composite(ims["CogpunkSlot_Lock"].resize((16 * sc, 16 * sc), Image.NEAREST), (5 * sc, 5 * sc))
            out.alpha_composite(bk, (x, 8))
            x += 26 * sc + 8
        out.alpha_composite(ims["CogpunkSlot_Cog"].resize((16 * sc, 16 * sc), Image.NEAREST), (x, 8))
        out.save(a.preview)
        print("preview", a.preview)


if __name__ == "__main__":
    main()
