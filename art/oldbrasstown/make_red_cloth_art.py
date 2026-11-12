"""Source for the Red Cloth (D4), 2026-11-10b (user: "a new accessory that can be dropped by the mechanical bull enemy at a
10% chance called red cloth; it should make so the next contact damage the player takes is dodged every 12 seconds").
Run from the repo root:

    python -P art/oldbrasstown/make_red_cloth_art.py [--preview FILE]

A matador's muleta, Westworld style: a crimson cloth hung from a brass rod (a cog-toothed knob at the grip end, a cap at
the other), swept out to the right as if mid-pass, deep folds running down it, its hem flaring. Lit from the top-left:
the cloth's folds catch the light on their left faces; ramp outlines (crimson 0 under and right, a lighter crimson on the
lit top), the rod gilt. Items: at most 16 colours (D4 rule 5).

Outputs:
    Content/OldBrassTown/Accessories/RedCloth.png          the item, 16x16 at 1x (32x32)
    Content/OldBrassTown/Accessories/RedClothCooldown.png  the recharge's buff icon, 16x16 at 1x (32x32): the cloth folded
                                                           over its rod, an hourglass in front
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
import make_scrap_art  # noqa: E402
from make_scrap_art import Canvas, export  # noqa: E402
from rig import RAMP  # noqa: E402

for _k, _c in zip("KLMNOP", RAMP["crimson"]):          # crimson: K (outline) .. P (lightest)
    make_scrap_art.PAL[_k] = _c

OUT = "Content/OldBrassTown/Accessories/"
SHADE = "KLMNOP"


def cloth_shape(w, h, top, left, right, hem):
    """The cloth's pixels: columns left..right, from the rod's row under `top(x)` down to `hem(x)`."""
    cells = set()
    for x in range(left, right + 1):
        for y in range(top(x), hem(x) + 1):
            if 0 <= x < w and 0 <= y < h:
                cells.add((x, y))
    return cells


def paint_cloth(c, cells, fold_period, phase):
    """Folds: a light face on each fold's left, its shadow on the right; brighter high and left (the light), darker low and
    right; a crimson-0 outline under and right, the lit outline (L) on the top-left."""
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for (x, y) in cells:
        out = [(x + dx, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if out[0] or out[2]:
            c.set(x, y, "K")                       # the outline on the shaded sides
            continue
        if out[1] or out[3]:
            c.set(x, y, "L" if (out[3] and y > y0 + 1) or (out[1] and y > (y0 + y1) // 2) else "M")
            continue
        fold = math.sin((x + phase + 0.35 * (y - y0)) / fold_period * 2 * math.pi)   # the folds lean with the sweep
        light = 0.62 - 0.32 * (x - x0) / max(1, x1 - x0) - 0.36 * (y - y0) / max(1, y1 - y0) + 0.34 * fold
        k = 1 + int(round(max(0.0, min(1.0, light)) * 4))          # L .. P
        c.set(x, y, SHADE[k])


def rod(c, x0, y0, x1, y1):
    """A gilt rod from (x0, y0) to (x1, y1) (a gentle slope), lit on top, its outline under; a cog-toothed knob at the
    grip end (x0) and a small cap at x1."""
    n = max(abs(x1 - x0), 1)
    for i in range(n + 1):
        x = x0 + i
        y = int(round(y0 + (y1 - y0) * i / n))
        c.set(x, y, "F")
        c.set(x, y + 1, "B")
    for (dx, dy, ch) in ((-1, -1, "E"), (0, -1, "F"), (-1, 0, "G"), (-2, 0, "D"), (-1, 1, "C"), (-2, -1, "B"), (-2, 1, "B"),
                         (0, 1, "B"), (-1, 2, "B"), (-1, -2, "B")):
        c.set(x0 + dx, y0 + dy, ch)                   # the knob: a little brass cog
    c.set(x1 + 1, y1, "D")
    c.set(x1 + 1, y1 + 1, "B")


def inside(poly, x, y):
    """Point-in-polygon (even-odd) for the pixel centre (x + 0.5, y + 0.5)."""
    px, py = x + 0.5, y + 0.5
    hit = False
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
        if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay):
            hit = not hit
    return hit


def item():
    """The cloth swept out to the right mid-pass: straight down from the grip end, its hem curving out and down to a point
    past the rod's tip."""
    c = Canvas(16, 16)
    rx0, ry0, rx1, ry1 = 2, 2, 12, 4
    rod_y = lambda x: int(round(ry0 + (ry1 - ry0) * (x - rx0) / (rx1 - rx0)))
    poly = [(3.0, 4.0), (12.6, 5.6), (13.6, 8.5), (15.6, 14.8), (12.0, 14.2), (8.0, 13.4), (5.0, 12.2), (3.0, 10.6)]
    cells = {(x, y) for y in range(16) for x in range(16) if inside(poly, x, y) and y > rod_y(x)}
    paint_cloth(c, cells, 3.4, 0.9)
    rod(c, rx0, ry0, rx1, ry1)
    for x in range(4, 12, 3):                         # the cloth's top sewn round the rod: brass rings
        c.set(x, rod_y(x) + 1, "D")
    return c


def cooldown_icon():
    c = Canvas(16, 16)
    rod(c, 2, 3, 12, 3)
    cells = cloth_shape(16, 16, top=lambda x: 5, left=3, right=11, hem=lambda x: 12 - abs(x - 7) // 2)
    paint_cloth(c, cells, 3.0, 0.2)
    for (x, y, ch) in ((10, 8, "B"), (11, 8, "D"), (12, 8, "D"), (13, 8, "D"), (14, 8, "B"),     # the hourglass in front
                       (11, 9, "B"), (12, 9, "t"), (13, 9, "B"),
                       (12, 10, "E"),
                       (11, 11, "B"), (12, 11, "F"), (13, 11, "B"),
                       (10, 12, "B"), (11, 12, "F"), (12, 12, "F"), (13, 12, "E"), (14, 12, "B"),
                       (10, 13, "B"), (11, 13, "D"), (12, 13, "D"), (13, 13, "D"), (14, 13, "B")):
        c.set(x, y, ch)
    return c


def preview(path):
    from PIL import Image
    tiles = []
    for cv in (item(), cooldown_icon()):
        im = Image.new("RGBA", (cv.w, cv.h), (60, 60, 70, 255))
        for y in range(cv.h):
            for x in range(cv.w):
                ch = cv.get(x, y)
                if ch != ".":
                    im.putpixel((x, y), make_scrap_art.PAL[ch] + (255,))
        tiles.append(im.resize((cv.w * 12, cv.h * 12), Image.NEAREST))
    sheet = Image.new("RGBA", (sum(t.width for t in tiles) + 12, tiles[0].height), (30, 30, 36, 255))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 12
    sheet.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export(item(), OUT + "RedCloth.png")
        export(cooldown_icon(), OUT + "RedClothCooldown.png")
