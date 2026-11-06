"""Source for Old Brass Town's locked strongbox and the Sheriff's Key (D4), 2026-11-04. Run from the repo root:

    python -P art/oldbrasstown/make_strongbox_art.py [--preview FILE]

Design (user, 2026-11-04: "a key that opens the chest inside the house in the town"): the bank vault's Brass Strongbox,
a riveted brass chest with iron bands, a domed lid and a lock plate; style 1 (locked) wears a heavy iron padlock with a
sheriff's star stamped on it and an iron bar across the lid. Three lid frames each (shut, ajar, open: vanilla animates a
chest from the sheet's rows), lit from the top-left. The Sheriff's Key: a brass key with a sheriff's star for a bow.

Layout (vanilla chests, ExampleMod 1.4.4 ExampleChest: 2 styles side by side, 3 lid frames stacked; each 2x2-tile frame
is 36x38 at 2x with 2 px between tiles, the bottom tiles 18 tall so the chest sinks 2 px into the floor). The highlight
(smart cursor) is each frame's outer ring in white.

Outputs:
    Content/OldBrassTown/Tiles/BrassStrongboxTile.png            72x114
    Content/OldBrassTown/Tiles/BrassStrongboxTile_Highlight.png  72x114
    Content/OldBrassTown/Items/BrassStrongbox.png                the item (the chest shut, unlocked)
    Content/OldBrassTown/Items/SheriffsKey.png                   28x28
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, box, Canvas, flat, dome, face  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

I, B, C, E, S = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam"))
W1, H1 = 16, 17                      # one chest at 1x (2x2 tiles, the bottom row 1 px taller)


def star(cv, cx, cy, col_hi, col_lo, col_mid):
    for (dx, dy, col) in ((0, -1, col_hi), (-1, 0, col_hi), (0, 0, col_mid), (1, 0, col_lo), (-1, 1, col_lo), (1, 1, col_lo)):
        cv.put(cx + dx, cy + dy, col)


def chest(locked, lid):
    """One chest at 1x, rows 0-16 (the last one sinks into the floor, as vanilla's 18 px bottom tiles do): lid 0 shut, 1
    ajar, 2 open (raised 1 and 2 px over the dark inside)."""
    cv = Canvas()
    raise_by = (0, 1, 2)[lid]
    # the body: a brass box, iron bands down its sides, rivets, a lit top edge
    body = cv.part(Xf(), box(1.0, 6.6, 15.0, 16.6), "brass", face((-0.5, -0.4, 0.75), lo=2, hi=4, gain=1.2, fixed=True), rust=0.0)
    for bx in (3, 12):
        for y in range(8, 16):
            if (bx, y) in body:
                cv.put(bx, y, I[3] if y < 10 else I[2])
                cv.put(bx + 1, y, I[2] if y < 10 else I[1])
        for y in (9, 14):
            cv.put(bx, y, I[4])
    for x in range(2, 14):                                   # the foot band
        if (x, 15) in body:
            cv.put(x, 15, B[2])
    # the lock plate (unlocked: a keyhole; locked: the padlock below)
    plate = cv.part(Xf(), box(6.0, 8.0, 10.0, 12.6), "iron", face((-0.4, -0.5, 0.75), lo=2, hi=4, fixed=True), rust=0.0)
    cv.put(8, 10, I[0])
    cv.put(8, 11, I[0])
    if lid == 2:                                             # open: the dark inside and a glint of gold
        inside = cv.raster(Xf(), box(1.6, 4.4, 14.4, 7.6))
        for q in inside:
            if q not in body:
                cv.put(q[0], q[1], I[1] if q[1] > 3 else I[0])
        for (x, y, col) in ((5, 6, B[5]), (6, 6, B[4]), (9, 6, B[4]), (10, 5, B[5])):
            cv.put(x, y, col)
    # the domed lid
    ly = 6.6 - raise_by
    lidp = cv.part(Xf(), Poly([(0.6, ly + 0.4), (1.6, ly - 2.6), (4.0, ly - 4.2), (12.0, ly - 4.2), (14.4, ly - 2.6), (15.4, ly + 0.4)]), "brass",
                   face((-0.4, -0.7, 0.6), lo=2, hi=5, gain=1.25, fixed=True), rust=0.0)
    for bx in (3, 12):                                       # the lid's iron bands and their rivets
        for y in range(int(ly - 3), int(ly + 1)):
            if (bx, y) in lidp:
                cv.put(bx, y, I[3])
                cv.put(bx + 1, y, I[2])
    for x in range(4, 12):                                   # the lid's lit ridge
        q = (x, int(ly - 3))
        if q in lidp:
            cv.put(q[0], q[1], B[5])
    if lid > 0:                                              # the gap under a raised lid
        for x in range(2, 14):
            for y in range(int(ly + 1), 7):
                if (x, y) not in body and (x, y) not in lidp:
                    cv.put(x, y, I[0])
    if locked:
        # an iron bar across the lid and the box, and a heavy padlock with a sheriff's star stamped on it
        for x in range(1, 15):
            q = (x, 8)
            if q in body or q in plate:
                cv.put(q[0], q[1], I[3] if x % 4 else I[4])
        for x in range(6, 10):
            cv.put(x, 9, I[1])
        shackle = [(6, 10), (6, 11), (7, 9), (8, 9), (9, 10), (9, 11)]
        for q in shackle:
            cv.put(q[0], q[1], I[4] if q[1] < 10 else I[3])
        lock = cv.part(Xf(), box(5.0, 11.6, 11.0, 16.0), "iron", face((-0.5, -0.5, 0.7), lo=1, hi=3, fixed=True), rust=0.0)
        star(cv, 8, 13, B[5], B[2], B[4])
        del lock
    return cv


def outline_ring(img):
    """The highlight: the frame's outer ring (opaque pixels with an empty 4-neighbour) in white."""
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px, po = img.load(), out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ox, y + oy
                if not (0 <= nx < w and 0 <= ny < h) or px[nx, ny][3] == 0:
                    po[x, y] = WHITE + (255,)
                    break
    return out


def tile_frame(img):
    """A 16x17 chest at 1x cut into vanilla's 2x2 tile frame at 1x: tiles 8x8 / 8x9 with a 1 px gap (2 px at 2x)."""
    out = Image.new("RGBA", (18, 19), (0, 0, 0, 0))
    out.alpha_composite(img.crop((0, 0, 8, 8)), (0, 0))
    out.alpha_composite(img.crop((8, 0, 16, 8)), (9, 0))
    out.alpha_composite(img.crop((0, 8, 8, 17)), (0, 9))
    out.alpha_composite(img.crop((8, 8, 16, 17)), (9, 9))
    return out


def sheet():
    tiles = Image.new("RGBA", (36, 57), (0, 0, 0, 0))
    glow = Image.new("RGBA", (36, 57), (0, 0, 0, 0))
    for style, locked in ((0, False), (1, True)):
        for lid in range(3):
            img = to_image(chest(locked, lid).px, 0, 0, W1, H1)
            tiles.alpha_composite(tile_frame(img), (style * 18, lid * 19))
            glow.alpha_composite(tile_frame(outline_ring(img)), (style * 18, lid * 19))
    return tiles, glow


def key_icon():
    """14x14: a brass key, a sheriff's star for its bow, the bit at the bottom right."""
    cv = Canvas()
    cv.part(Xf(), Capsule((5.6, 5.4), (11.0, 11.0), 1.0), "brass", flat(3), rust=0.0)
    for (x, y) in ((10, 11), (11, 10), (12, 11), (11, 12)):
        cv.put(x, y, B[2])                                    # the bit's teeth
    cv.put(9, 11, B[3])
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = 4.6 if k % 2 == 0 else 2.2
        pts.append((4.4 + math.cos(a) * r, 4.6 + math.sin(a) * r))
    bow = cv.part(Xf(), Poly(pts), "brass", face((-0.5, -0.6, 0.6), lo=3, hi=5, fixed=True), rust=0.0)
    cv.put(4, 4, B[1])                                        # the hole through the star
    cv.put(3, 3, WHITE)
    del bow
    for k in range(5):                                        # the shank's lit edge
        cv.put(6 + k, 5 + k, B[4])
    return to_image(cv.px, 0, 0, 14, 14)


def export_all():
    tiles, glow = sheet()
    export(tiles, "Content/OldBrassTown/Tiles/BrassStrongboxTile.png")
    export(glow, "Content/OldBrassTown/Tiles/BrassStrongboxTile_Highlight.png")
    export(to_image(chest(False, 0).px, 0, 0, W1, H1), "Content/OldBrassTown/Items/BrassStrongbox.png")
    export(key_icon(), "Content/OldBrassTown/Items/SheriffsKey.png")


def preview(path):
    tiles, glow = sheet()
    out = Image.new("RGBA", (36 * 2 + 40, 57 * 2), (36, 40, 48, 255))
    light = Image.new("RGBA", (36, 57), (150, 180, 210, 255))
    light.alpha_composite(tiles)
    out.alpha_composite(tiles, (0, 0))
    out.paste(light, (38, 0))
    out.alpha_composite(glow, (0, 57))
    out.alpha_composite(key_icon(), (80, 4))
    out.resize((out.width * 6, out.height * 6), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
