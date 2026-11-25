"""The enemy banners (D4), 2026-11-25 (user: "dont forget to create banners for each enemy we have (excluding bosses and mini
bosses)"). Run from the repo root:

    python -P art/banners/make_banner_art.py [--preview FILE]

A Cogpunk banner, vanilla's size (1 x 3 tiles: 8 x 24 art px, 16 x 48 in game): a brass rod with a cog at each end, crimson
cloth in a brass trim, a notched end with a brass rivet, and in the middle the enemy itself: its own first frame (every plane
of it) shrunk to fit a 6 x 10 box by the commonest colour of each block (never an average: the palette stays), outlined in the
cloth's darkest red so it reads on the cloth.

Outputs (Content/Banners/): EnemyBannerTile.png (one column of three 8 px tiles per enemy, 9 px apart: 18 px at 2x, in
EnemyBanners.Enemies' order) and Items/<Enemy>Banner.png (the whole banner).
"""
import argparse
import os
import re
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

K, G, ST = RAMP["crimson"], RAMP["gilt"], RAMP["steel"]
OUT = "Content/Banners/"
BW, BH = 8, 24
ICON = (1, 4, 6, 10)                       # x, y, w, h of the icon's box on the cloth

ENEMIES = [
    ("Toadstool", "Content/Bosses/Fungimancer/NPCs"), ("Cogscorpion", "Content/Coghaven/NPCs"),
    ("FlyingBuddhaHead", "Content/Coghaven/NPCs"), ("JadeGolem", "Content/Coghaven/NPCs"), ("Coghawk", "Content/Desert/NPCs"),
    ("BeatBoxer", "Content/Dungeon/NPCs"), ("RhinoBeetle", "Content/Jungle/NPCs"), ("Trapper", "Content/Jungle/NPCs"),
    ("LivingTar", "Content/Junkyard/NPCs"), ("RustCollector", "Content/Junkyard/NPCs"), ("AnnoyOTron", "Content/MechArmy/NPCs"),
    ("Boombot", "Content/MechArmy/NPCs"), ("RogueMiceBot", "Content/MechArmy/NPCs"), ("Cogtuna", "Content/Ocean/NPCs"),
    ("BrassBandit", "Content/OldBrassTown/NPCs"), ("Dinamitrom", "Content/OldBrassTown/NPCs"), ("MechanicalBull", "Content/OldBrassTown/NPCs"),
    ("Splasher", "Content/Rain/NPCs"), ("DeliveryDrone", "Content/Scrap/NPCs"), ("CrystalLizard", "Content/Underground/NPCs"),
    ("Driller", "Content/Underground/NPCs"), ("PuxaFrango", "Content/Underground/NPCs"), ("DragoneteMiudo", "Content/Underworld/NPCs"),
]


SHARED_RIG = {"AnnoyOTron": "Annoy", "Boombot": "Boombot", "RogueMiceBot": "Mice"}     # MechArmyRigData's prefixes


def frame_box(name, folder):
    """The first frame's rectangle (game px) in the enemy's middle sheet: from its RigData (CellWidth x CellHeight; the Mech
    Army's share one, its names prefixed) when it has one, else its frame count (vanilla's layout: the height split evenly)."""
    if name in SHARED_RIG:
        src = open(os.path.join(os.path.dirname(folder), "MechArmyRigData.cs"), encoding="utf-8").read()
        pre = SHARED_RIG[name]
        w = int(re.search(pre + r"CellWidth = (\d+)", src).group(1))
        h = int(re.search(pre + r"CellHeight = (\d+)", src).group(1))
        return (0, 0, w, h)
    rig = os.path.join(folder, name + "RigData.cs")
    if os.path.exists(rig):
        src = open(rig, encoding="utf-8").read()
        w = int(re.search(r"CellWidth = (\d+)", src).group(1))
        h = int(re.search(r"CellHeight = (\d+)", src).group(1))
        return (0, 0, w, h)
    cs = open(os.path.join(folder, name + ".cs"), encoding="utf-8").read()
    m = re.search(r"Main\.npcFrameCount\[Type\]\s*=\s*([A-Za-z0-9_.]+)", cs)
    n = 1
    if m:
        v = m.group(1)
        if v.isdigit():
            n = int(v)
        else:
            c = re.search(r"\b" + re.escape(v.split(".")[-1]) + r"\s*=\s*(\d+)", cs)
            n = int(c.group(1)) if c else 1
    tex = Image.open(os.path.join(folder, name + ".png"))
    return (0, 0, tex.width, tex.height // max(1, n))


def first_frame(name, folder):
    """The enemy's first frame at 1x (all its planes: far, middle, near), cropped to its pixels."""
    box = frame_box(name, folder)
    out = None
    for suffix in ("_Far", "", "_Near"):
        p = os.path.join(folder, name + suffix + ".png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA").crop(box)
        out = im if out is None else Image.alpha_composite(out, im)
    out = out.resize((out.width // 2, out.height // 2), Image.NEAREST)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def shrink(im, w, h):
    """Fits `im` into w x h keeping its shape: each new pixel the commonest opaque colour of its block (empty when most of the
    block is empty)."""
    s = min(w / im.width, h / im.height, 1.0)
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    px = im.load()
    out = {}
    for y in range(nh):
        for x in range(nw):
            x0, x1 = int(x / s), max(int(x / s) + 1, int((x + 1) / s))
            y0, y1 = int(y / s), max(int(y / s) + 1, int((y + 1) / s))
            cols = [px[i, j][:3] for j in range(y0, min(y1, im.height)) for i in range(x0, min(x1, im.width)) if px[i, j][3] > 0]
            total = (min(y1, im.height) - y0) * (min(x1, im.width) - x0)
            if cols and len(cols) * 2 >= total:
                out[(x, y)] = Counter(cols).most_common(1)[0][0]
    return out, nw, nh


def banner(name, folder):
    px = {}
    for x in range(BW):                                   # the rod, its cog caps
        px[(x, 0)] = G[7] if 1 <= x <= 6 else ST[5]
        px[(x, 1)] = G[4] if 1 <= x <= 6 else ST[3]
    for y in range(2, 21):                                # the cloth in its trim
        for x in range(BW):
            if x in (0, 7):
                px[(x, y)] = G[5] if x == 0 else G[3]
            else:
                px[(x, y)] = K[3] if x < 4 else K[2]
    for x in range(BW):
        px[(x, 2)] = G[6]                                 # the hem under the rod
        px[(x, 20)] = G[5] if x < 4 else G[4]             # the brass band at the end
    for (x, y) in ((1, 21), (2, 21), (3, 21), (4, 21), (5, 21), (6, 21), (1, 22), (2, 22), (5, 22), (6, 22), (1, 23), (6, 23)):
        px[(x, y)] = K[2] if x < 4 else K[1]              # the notched end: two points
    px[(3, 22)] = G[7]                                    # a rivet between them
    px[(4, 22)] = G[5]
    icon, iw, ih = shrink(first_frame(name, folder), ICON[2], ICON[3])
    ox = ICON[0] + (ICON[2] - iw) // 2
    oy = ICON[1] + (ICON[3] - ih) // 2
    for (x, y), c in icon.items():
        px[(ox + x, oy + y)] = c
    for (x, y) in list(icon):                             # a dark red edge round it, on the cloth only
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (ox + x + dx, oy + y + dy)
            if (q[0] - ox, q[1] - oy) not in icon and 1 <= q[0] <= 6 and 3 <= q[1] <= 19:
                px[q] = K[0]
    im = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    for (x, y), c in px.items():
        im.putpixel((x, y), tuple(c) + (255,))
    return im


def tile_sheet(banners):
    out = Image.new("RGBA", (9 * len(banners), 27), (0, 0, 0, 0))
    for k, b in enumerate(banners):
        for r in range(3):
            out.alpha_composite(b.crop((0, r * 8, 8, r * 8 + 8)), (k * 9, r * 9))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    banners = [banner(n, f) for n, f in ENEMIES]
    export(tile_sheet(banners), OUT + "EnemyBannerTile.png")
    for (n, _), b in zip(ENEMIES, banners):
        export(b, OUT + "Items/%sBanner.png" % n)
    if a.preview:
        sc = 5
        out = Image.new("RGBA", (len(banners) * (BW * sc + 6) + 6, BH * sc + 12), (30, 34, 60, 255))
        for k, b in enumerate(banners):
            out.alpha_composite(b.resize((BW * sc, BH * sc), Image.NEAREST), (6 + k * (BW * sc + 6), 6))
        out.save(a.preview)
        print("preview", a.preview)


if __name__ == "__main__":
    main()
