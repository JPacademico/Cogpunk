"""D5 proofs for the second request of 2026-11-06, built from the real sprite sheets and the constants parsed out of the C#
files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_06b_sim.py --out docs/media [--only defender]

Writes:
    2026-11-09_coghaven-imperial-defender.gif   the Imperial Defender marches at a gunner; once every 8 s he plants his
                                                feet and raises the dadao for 2 s: shots from the front are knocked away
                                                ("Parried!", sparks off the blade), until the gunner jumps over him and
                                                shoots his back (full damage); then he lowers the blade and turns.
    (The Jade Golem's and the Cursed Lantern's scenes were removed 2026-11-10b: the Golem's hands and aiming and the
    Lantern's soul limit changed; their proofs are update_2026_11_10b_sim.py's.)

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
KD = consts(COG + "NPCs/ImperialDefender.cs", COG + "NPCs/ImperialDefenderRigData.cs")
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
# The Imperial Defender
# ================================================================================================
def scene_defender(out, font):
    W, H, G = 640, 230, 200
    bg = coghaven_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    knight = Planes(COG + "NPCs/ImperialDefender", KD)
    guard_in, guard_out = KD["GuardInFrames"] * KD["FrameTicks"], KD["GuardOutFrames"] * KD["FrameTicks"]
    march_ticks = KD["ParryEvery"] - guard_in - KD["ParryTicks"] - guard_out
    kx, face = 470.0, -1
    state, timer, marched, counter = "march", 0, march_ticks - 60, 0.0
    px, py, p_face = 180.0, float(G), 1
    shots, pops, sparks = [], [], Sparks()
    notes = [(0, "Imperial Defender: marches, heavy contact (%d)" % KD["ContactDamage"]),
             (60, "every 8 s: the guard, held %d ticks (2 s)" % KD["ParryTicks"]),
             (95, "hits from the front: parried (1 damage, shots destroyed)"),
             (150, "his feet stay planted: hits from behind land in full")]
    jump0, jump_len = 120, 46
    for tick in range(330):
        # --- the gunner (scripted): shoots, then jumps over him and shoots his back ---------------------------------
        if jump0 <= tick < jump0 + jump_len:
            u = (tick - jump0) / jump_len
            px = 240.0 + (540.0 - 240.0) * u
            py = G - 4 * 92 * u * (1 - u)
            p_face = 1
        elif tick >= jump0 + jump_len:
            px, py, p_face = 540.0, float(G), -1
        elif tick >= 95:
            px = min(240.0, px + 3.0)
        fire_every = 16
        if tick % fire_every == 0 and py >= G - 1 and not (jump0 <= tick < jump0 + jump_len):
            shots.append([px + 16 * p_face, G - 34, 9.0 * p_face])
        # --- the Defender --------------------------------------------------------------------------------------------
        timer += 1
        if state == "march":
            marched += 1
            want = 1 if px > kx else -1
            vx = want * KD["MarchSpeed"]
            if abs(px - kx) > 40:
                kx += vx
                counter = (counter + abs(vx)) % (KD["WalkStep"] * KD["WalkFrames"])
            face = want
            frame = KD["Walk"] + int(counter / KD["WalkStep"]) % int(KD["WalkFrames"])
            if marched >= march_ticks:
                state, timer, marched = "in", 0, 0
        elif state == "in":
            frame = KD["GuardIn"] + min(KD["GuardInFrames"] - 1, timer // KD["FrameTicks"])
            if timer >= guard_in:
                state, timer = "guard", 0
        elif state == "guard":
            frame = KD["Guard"] + (timer // 10) % KD["GuardFrames"]
            if timer >= KD["ParryTicks"]:
                state, timer = "out", 0
        else:
            frame = KD["GuardOut"] + min(KD["GuardOutFrames"] - 1, timer // KD["FrameTicks"])
            if timer >= guard_out:
                state, timer = "march", 0
        box = (kx - KD["Width"] / 2 if "Width" in KD else kx - 14, G - 58, kx + 14, G)
        for s in shots:
            s[0] += s[2]
            if box[0] <= s[0] <= box[2] and box[1] <= s[1] <= box[3] and s[2] != 0:
                from_front = (s[0] - s[2] - kx) * face >= 0
                if state == "guard" and from_front:
                    blade = (kx + KD["GuardBladeX"] * -face, G + KD["GuardBladeY"])
                    sparks.burst(blade[0], blade[1], face)
                    pops.append((tick, kx - 34, G - 92, "Parried!", EMBER))
                else:
                    pops.append((tick, kx - 10, G - 86, "20", HURT))     # 30 - defense 20 / 2
                s[2] = 0
        shots = [s for s in shots if s[2] != 0 and 0 <= s[0] <= W]
        # --- draw ------------------------------------------------------------------------------------------------------
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        knight.draw(img, frame, (kx, G), face == 1)
        img.alpha_composite(player_sprite(flip=p_face < 0), (int(px - 20), int(py - 56)))
        for s in shots:
            d.line([s[0] - 4, s[1], s[0] + 4, s[1]], fill=(255, 231, 160, 255), width=2)
        sparks.step_draw(d)
        gif.text(img, (10, H - 22), "state: %s" % {"march": "march", "in": "guard up", "guard": "GUARD (parry)", "out": "guard down"}[state],
                 fill=EMBER if state == "guard" else STEAM)
        note(gif, img, notes, tick)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


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
    jobs = [("defender", lambda: scene_defender(os.path.join(args.out, "2026-11-09_coghaven-imperial-defender.gif"), args.font))]
    for name, job in jobs:
        if args.only in (None, name):
            job()


if __name__ == "__main__":
    main()
