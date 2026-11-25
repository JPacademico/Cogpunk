"""The alpha's research art (2026-11-25). Run from the repo root:

    python -P art/research/make_altar_art.py [--preview FILE]

* Altar/DemonTable.png (the item) and Altar/DemonTableTile.png: the Demon Table (user: "be able to craft a demon table
  (demon/crimson altar crafting station but without spreading corruption or scarying npcs)"). My design: a portable altar
  built as a table, both evils at once: a slab of ebonstone (amethyst, lit from the top-left, a lit lip and a shadowed
  underside), a crimson cloth runner hanging over its front with a gilt-stitched hem, two curled horns for legs (bone, the
  altars' horns), and on top a horned skull, a bowl of embers (the glow) and a black candle; a sigil on the apron glows ember.
  24 x 17 art px like the Ancient Research Table, cut into a 3 x 2 tile sheet (18 px stride at 2x, the bottom row 18 tall).
* UI/WhoIsHe.png (user: "the icon for it should be the npc miniature with a red circle and arrow arround it (like the "who
  is he?" meme)"): the Last Ghedalari's own map head (Content/Town/Friendobo_Head.png, his miniature, pixel for pixel) inside a
  hand-drawn red marker circle with a red arrow pointing at him from the lower right, 20 x 20 art px (the node's field).

Colours: the Cogpunk palette only (rig.RAMP); the head keeps its own.
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
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
from pixkit import Pix  # noqa: E402

OUT = "Content/Research/"
AM, K, BN, EM, G, ST = (RAMP[k] for k in ("amethyst", "crimson", "bone", "ember", "gilt", "steel"))


def pixmap(rows, legend):
    px = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                px[(x, y)] = legend[ch]
    return px


# The Demon Table, 24 x 17 (x right, y down), built from parts and outlined in each part's own darkest shade (pixkit):
# the slab of ebonstone (rows 7-9: its top lit from the left, its front in shadow), the crimson runner hanging from it with
# folds and a gilt hem round an ember sigil (rows 10-13), two curled ivory horns for legs (rows 9-16), and on top a horned
# skull with an ember eye, a bowl of embers and a black candle.
PL, IV = RAMP["plum"], RAMP["ivory"]
SLAB = (PL[0], PL[1], PL[2], AM[1], AM[2], AM[3])                       # ebonstone: plum's darks under amethyst's lights


def table():
    p = Pix(24, 17)
    # the slab: top face lit from the left, the front a band darker, its lower edge darker still
    for x in range(24):
        p.put(x, 6, SLAB, 3)                                              # the top edge (the outline takes it)
        p.put(x, 7, SLAB, 5 if x < 7 else 4)                              # the top face, lit from the left
        p.put(x, 8, SLAB, 3 if x < 4 else 2)
        p.put(x, 9, SLAB, 1)
    for x in (5, 11, 17):                                                 # the slab's seams (blocks of ebonstone)
        p.put(x, 8, SLAB, 1)
    # the runner: crimson, lit on its left, three folds, a gilt hem
    for y in range(10, 14):
        for x in range(4, 20):
            p.put(x, y, K, 3 if x > 5 else 4)
    for x in (8, 15):
        for y in range(10, 13):
            p.put(x, y, K, 2)
    for x in range(4, 20):
        p.put(x, 13, G, 5 if x % 2 else 7)
    for (x, y) in ((4, 13), (19, 13)):
        p.clear(x, y)                                                     # the hem's corners rounded
    # the horn legs: ivory, thick under the slab, curling out to the floor, lit on their left
    horn_l = ((1, 10, 4), (2, 10, 4), (3, 10, 3), (1, 11, 4), (2, 11, 3), (3, 11, 2), (1, 12, 3), (2, 12, 2), (0, 13, 3),
              (1, 13, 2), (0, 14, 3), (1, 14, 2), (0, 15, 2), (1, 15, 2), (2, 15, 1), (0, 16, 2), (1, 16, 1), (2, 16, 1), (3, 16, 1))
    for (x, y, i) in horn_l:
        p.put(x, y, IV, i + 1)
        p.put(23 - x, y, IV, max(1, i))                                   # the right one in the slab's shade
    # on top: the horned skull (x 1-6), the ember bowl (x 9-14), the black candle (x 19-21)
    skull = ((2, 2, 4), (3, 2, 4), (4, 2, 4), (5, 2, 3), (1, 3, 4), (2, 3, 4), (3, 3, 3), (4, 3, 3), (5, 3, 3), (6, 3, 2),
             (1, 4, 3), (2, 4, 3), (3, 4, 3), (4, 4, 3), (5, 4, 2), (6, 4, 2), (2, 5, 2), (3, 5, 3), (4, 5, 2), (5, 5, 2))
    for (x, y, i) in skull:
        p.put(x, y, IV, i)
    for (x, y, i) in ((1, 1, 4), (1, 0, 5), (6, 1, 3), (6, 0, 4)):       # its little horns
        p.put(x, y, IV, i)
    bowl = ((9, 4, 3), (10, 4, 3), (11, 4, 2), (12, 4, 2), (13, 4, 2), (14, 4, 1), (10, 5, 2), (11, 5, 2), (12, 5, 2), (13, 5, 1))
    for (x, y, i) in bowl:
        p.put(x, y, ST, i + 1)
    for x in range(10, 14):
        p.put(x, 3, EM, 1 if x in (10, 13) else 2)                        # the coals heaped in it
    p.put(11, 2, EM, 2)
    p.put(12, 2, EM, 2)
    for y in range(2, 6):
        p.put(20, y, ST, 1 if y < 5 else 0)                               # the candle: black wax
        p.put(21, y, ST, 0)
    p.put(19, 5, ST, 1)
    p.put(22, 5, ST, 0)
    p.outline()
    # stamps (after the outline): the skull's sockets and ember eye, the flames, the sigil, the embers' light
    p.put(2, 3, PL, 0, lock=True)                                         # the skull's socket
    p.put(4, 3, EM, 2, lock=True)                                         # and its ember eye
    p.put(3, 5, PL, 0, lock=True)                                         # the nose
    for (x, y, i) in ((11, 1, 3), (12, 1, 2), (11, 0, 2), (12, 2, 3), (11, 2, 3)):
        p.put(x, y, EM, i, lock=True)                                     # the bowl's flame
    for (x, y, i) in ((20, 1, 2), (20, 0, 3), (21, 1, 1)):
        p.put(x, y, EM, i, lock=True)                                     # the candle's flame
    for (x, y, i) in ((11, 10, 2), (12, 10, 2), (10, 11, 2), (13, 11, 2), (11, 11, 3), (12, 11, 3), (11, 12, 2), (12, 12, 2)):
        p.put(x, y, EM, i, lock=True)                                     # the sigil: an ember diamond on the runner
    return p


def image(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def tile_sheet(img):
    """The 24 x 17 table cut into 8 px tiles with 1 px gaps (3 x 2, the bottom row 9 tall): 18 px stride at 2x."""
    out = Image.new("RGBA", (3 * 9, 9 + 10), (0, 0, 0, 0))
    for r, (y0, h) in enumerate(((0, 8), (8, 9))):
        for c in range(3):
            out.alpha_composite(img.crop((c * 8, y0, c * 8 + 8, y0 + h)), (c * 9, r * 9))
    return out


# --- "Who is he?" ---------------------------------------------------------------------------------------------------------
ICON = 20
RED, RED_DARK, RED_EDGE = K[4], K[3], K[1]


def who_is_he():
    head = Image.open(os.path.join("Content", "Town", "Friendobo_Head.png")).convert("RGBA")
    head = head.resize((head.width // 2, head.height // 2), Image.NEAREST)     # back to its 1x pixels (13 x 11)
    px = {}
    hx, hy = 2, 3
    for y in range(head.height):
        for x in range(head.width):
            c = head.getpixel((x, y))
            if c[3] > 0:
                px[(hx + x, hy + y)] = c[:3]
    # the marker circle: one red stroke round him, a pixel wide (pixel-perfect: no L corners), a little wobble and its end
    # overshooting its start, as a hand draws it; then a dark edge on its outer side only, so it reads on the dark field
    cx, cy, rx, ry = 8.6, 8.4, 7.6, 7.2
    ring = []
    steps = 600
    for k in range(steps + 1):
        t = k / steps * (2 * math.pi + 0.5) - 2.3
        wob = 0.3 * math.sin(3 * t + 0.6)
        q = (int(math.floor(cx + (rx + wob) * math.cos(t))), int(math.floor(cy + (ry + wob) * math.sin(t))))
        if not ring or ring[-1] != q:
            ring.append(q)
    keep = []
    for i, b in enumerate(ring):                                      # pixel-perfect: drop the corner of every L, judged
        if keep and i + 1 < len(ring):                               # against the pixel kept before it
            a, c = keep[-1], ring[i + 1]
            if abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1                     and abs(c[0] - b[0]) + abs(c[1] - b[1]) == 1:
                continue
        if not keep or keep[-1] != b:
            keep.append(b)
    red = set(keep)
    arrow_px = set()
    # the arrow: a two-pixel shaft from the lower right corner to just outside the ring, its head two strokes back
    for k in range(5):
        arrow_px.add((19 - k, 19 - k))
        arrow_px.add((18 - k, 19 - k))
    tip = (14, 14)
    for (x, y) in ((tip[0], tip[1]), (tip[0] + 1, tip[1]), (tip[0] + 2, tip[1]), (tip[0], tip[1] + 1), (tip[0], tip[1] + 2)):
        arrow_px.add((x, y))
    arrow_px = {q for q in arrow_px if 0 <= q[0] < ICON and 0 <= q[1] < ICON}
    red |= arrow_px
    red = {q for q in red if 0 <= q[0] < ICON and 0 <= q[1] < ICON}
    for q in red:
        px[q] = RED
    for (x, y) in red:                                               # lit from the top-left: the ring's lower-right half darker
        if (x, y) in arrow_px or (x + 0.5 - cx) + (y + 0.5 - cy) > 1.5:
            px[(x, y)] = RED_DARK if (x, y) not in arrow_px or (x + 1, y + 1) not in red else RED
    for (x, y) in arrow_px:                                          # the arrow: a dark edge round it, so it reads on any field
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            q = (x + dx, y + dy)
            if q not in red and q not in px and 0 <= q[0] < ICON and 0 <= q[1] < ICON:
                px[q] = RED_EDGE
    return image(px, ICON, ICON)


def export_all():
    t = table().image()
    export(t, OUT + "Altar/DemonTable.png")
    export(tile_sheet(t), OUT + "Altar/DemonTableTile.png")
    export(who_is_he(), OUT + "UI/WhoIsHe.png")


def preview(path):
    t = table().image()
    icon = who_is_he()
    frame_path = os.path.join("Content", "Research", "UI", "ResearchNode.png")
    tiles = [t, icon]
    sc = 8
    out = Image.new("RGBA", (sum(i.width * sc + 16 for i in tiles) + 16 + 60 * 2, max(i.height for i in tiles) * sc * 2 + 48), (20, 20, 24, 255))
    for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
        x = 8
        for im in tiles:
            band = Image.new("RGBA", (im.width * sc + 8, im.height * sc + 8), bg + (255,))
            band.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (4, 4))
            out.alpha_composite(band, (x, 8 + row * (max(i.height for i in tiles) * sc + 16)))
            x += im.width * sc + 16
    if os.path.exists(frame_path):                                   # the icon on the node frame, at game scale x2
        fr = Image.open(frame_path).convert("RGBA").crop((0, 0, 56, 56))
        big = icon.resize((40, 40), Image.NEAREST)
        fr.alpha_composite(big, (8, 8))
        out.alpha_composite(fr.resize((112, 112), Image.NEAREST), (out.width - 124, 8))
    out.save(path)
    print("wrote", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
