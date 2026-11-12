"""D5 proofs for the second request of 2026-11-06, built from the real sprite sheets and the constants parsed out of the C#
files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_06b_sim.py --out docs/media

Writes nothing any more: its last scene, the Imperial Defender's (2026-11-09_coghaven-imperial-defender.gif), went with the
enemy on 2026-11-11 (user: "remove the imperial defender enemy, we will not use it anymore"; the scene is kept in
tools/sim/previous/update_2026_11_06b_sim_2026-11-09.py). (The Jade Golem's and the Cursed Lantern's scenes were removed
2026-11-10b: their proofs are update_2026_11_10b_sim.py's.) Its helpers (Planes, coghaven_backdrop, numbers, note, Sparks,
seg_box_dist) are still imported by the later sims.

Leaves out: lighting, the planes' parallax, vanilla's player physics (scripted paths), defense on the player, netcode (the
sim is the server). Numbers are Expert's.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, player_sprite, TPF  # noqa: E402

COG = "Content/Coghaven/"
KG = consts(COG + "NPCs/JadeGolem.cs", COG + "NPCs/JadeGolemRigData.cs", COG + "Projectiles/JadeRay.cs")
LAN = "Content/Bosses/CursedConductor/Weapons/"
KL = consts(LAN + "CursedLantern.cs", LAN + "SoulFire.cs")
EMBER, STEAM, JADE, AETHER, HURT = (255, 199, 90), (238, 241, 243), (118, 220, 162), (198, 189, 255), (236, 113, 40)


def int_array(path, name):
    m = re.search(name + r"\s*=\s*\{([^}]*)\}", open(path, encoding="utf-8").read())
    return [int(v) for v in m.group(1).split(",")]


MUZZLE_X = int_array(COG + "NPCs/JadeGolemRigData.cs", "MuzzleX")
MUZZLE_Y = int_array(COG + "NPCs/JadeGolemRigData.cs", "MuzzleY")


class Planes:
    """A grid enemy's far, middle, near and glow cells (in k["Columns"] columns), drawn at the origin and mirrored when it
    faces right, like DepthLayers.DrawWalker (parallax left out)."""

    def __init__(self, base, k):
        self.k = k
        self.sheets = [load(base + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]

    def draw(self, img, frame, anchor, face_right, glow=1.0):
        cw, ch, ox, oy = self.k["CellWidth"], self.k["CellHeight"], self.k["OriginX"], self.k["OriginY"]
        cols = int(self.k.get("Columns", 1))
        x0, y0 = frame % cols * (cw + 2), frame // cols * (ch + 2)
        for i, sheet in enumerate(self.sheets):
            cell = sheet.crop((x0, y0, x0 + cw, y0 + ch))
            if i == 3 and glow < 1.0:
                cell.putalpha(cell.getchannel("A").point(lambda a: int(a * glow)))
            if face_right:
                cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(cell, (int(round(anchor[0] - (cw - ox))), int(round(anchor[1] - oy))))
            else:
                img.alpha_composite(cell, (int(round(anchor[0] - ox)), int(round(anchor[1] - oy))))


def coghaven_backdrop(w, h, ground, ledges=()):
    """The island's sky over Palace Flagstone (the real tile's top and middle frames), with optional stone ledges."""
    img = backdrop(w, h, ground, sky=((170, 206, 236), (120, 160, 208)), dirt=(152, 132, 104))
    tiles = load(COG + "Tiles/PalaceFlagstoneTile.png")
    top, mid = tiles.crop((18, 0, 34, 16)), tiles.crop((18, 18, 34, 34))
    for (x0, x1, y) in [(0, w, ground)] + list(ledges):
        for x in range(x0, x1, 16):
            img.alpha_composite(top, (x, y))
            for yy in range(y + 16, h, 16):
                img.alpha_composite(mid, (x, yy))
    return img


def numbers(gif, img, pops, tick):
    for (t0, x, y, s, col) in pops:
        if 0 <= tick - t0 < 45:
            gif.text(img, (int(x), int(y - (tick - t0) // 2)), s, fill=col, font=gif.big)


def note(gif, img, notes, tick):
    live = [s for (t0, s) in notes if t0 <= tick]
    if live:
        gif.text(img, (10, 8), live[-1], fill=STEAM)


class Sparks:
    def __init__(self):
        self.items = []

    def burst(self, x, y, direction, n=6, col=EMBER):
        for _ in range(n):
            self.items.append([x, y, direction * random.uniform(1.5, 4.0), random.uniform(-3.0, 0.5), 16, col])

    def step_draw(self, d):
        for s in self.items:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.25
            s[4] -= 1
            d.rectangle([s[0] - 1, s[1] - 1, s[0] + 1, s[1] + 1], fill=s[5] + (255,))
        self.items = [s for s in self.items if s[4] > 0]


# ================================================================================================
# Shared: a segment's distance to a box (the Jade Golem's scene moved to update_2026_11_10b_sim.py)
# ================================================================================================
def seg_box_dist(a, b, box):
    """Distance from the segment a-b to the box (0 if they touch); sampled every 2 px (a proof, not the game's test)."""
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2))
    best = 1e9
    for i in range(n + 1):
        x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
        dx = max(box[0] - x, 0, x - box[2])
        dy = max(box[1] - y, 0, y - box[3])
        best = min(best, math.hypot(dx, dy))
    return best


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    random.seed(11)
    jobs = []                                    # the Defender's scene went with the enemy (2026-11-11)
    for name, job in jobs:
        if args.only in (None, name):
            job()


if __name__ == "__main__":
    main()
