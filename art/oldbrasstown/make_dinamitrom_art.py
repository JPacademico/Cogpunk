"""Source for the Dinamitrom, an enemy of Old Brass Town, and its blast (D4), 2026-11-04. Run from the repo root:

    python -P art/oldbrasstown/make_dinamitrom_art.py [--preview FILE]

Design (user, 2026-11-04: "a dynamite barrel robot that jumps at the player and explodes; low health and high damage"):
a stout wooden powder barrel on two coiled iron spring legs with big flat feet. Leather-brown staves with a lit edge and
dark grooves between them, two riveted iron hoops, a bundle of red dynamite sticks with paper bands poking out of the
top and a fuse curling up from them with a spark on its end (glow), and a face: two round iron goggles with ember lenses
(hostile) over a jagged grin of steam-white teeth. Three-quarter side view facing left (D4 rule 13), lit from the
top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg, a ramp step darker), middle (the barrel, the
dynamite, the fuse), near (the near leg); the glow sheet holds the lenses and the fuse's spark. Stable pixels (D4 rule
17): the barrel moves by whole pixels (squash = the springs, never the staves), parts lit in their own space.

Frames: Idle x2, Hop x4 (crouch, spring up, tucked in the air, land), Windup x2 (the telegraph: crouched deep, the fuse
flaring, shaking 0/1 px), Leap (springs out, tipped forward). The hop stretches the springs and never tips the barrel
(tipping it re-rasterised its staves: check_flicker 2.8%), and the rigid barrel moves at most 3 whole pixels between
frames (a 5 px jump read as flicker in the checker's window).

Outputs:
    Content/OldBrassTown/NPCs/Dinamitrom.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/OldBrassTown/NPCs/DinamitromRigData.cs   cells, origin, frames, the fuse's spark (from the origin, facing left)
    Content/OldBrassTown/Projectiles/DinamitromBlast.png   7 frames, 128x128: fireball, splinters of stave and hoop, smoke
    Content/OldBrassTown/Gores/Dinamitrom_GoreStave.png, _GoreHoop.png, _GoreStick.png
"""
import argparse
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from westbots import (RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, face, cyl, P, despeckle, finish, texture,  # noqa: E402
                      glint, I, B, C, E, S, LE, ST, G, H, K, OK, IV)
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"
BARREL_W, BARREL_H = 14.0, 14.0
FUSE_TIP = (2.6, -26.4)                    # the spark, relative to the barrel's rest pose (the origin is under the feet)


class Pose:
    def __init__(self, lift=6.0, bob=0, tilt=0.0, shake=0, spark=1, near_foot=(-2.0, 0.0), far_foot=(2.0, 0.0), air=False):
        self.lift = lift                   # px from the ground to the barrel's bottom (the springs' length)
        self.bob = bob                     # whole px the barrel drops (a squash read through the springs)
        self.tilt = tilt                   # degrees the whole barrel tips (the leap; + = forward/left side down)
        self.shake = shake                 # whole px sideways (0 / 1, never -1 / +1)
        self.spark = spark                 # 0 dim, 1 lit, 2 flaring (the telegraph)
        self.near_foot, self.far_foot = near_foot, far_foot
        self.air = air                     # the feet tucked up (in the air)


def spring_leg(cv, top, foot, depth):
    """A coiled iron spring from under the barrel to a big flat foot: zig-zag coils, alternately lit and shaded."""
    (tx, ty), (fx, fy) = top, foot
    n = 4
    pts = []
    for k in range(n * 2 + 1):
        u = k / (n * 2)
        x = tx + (fx - tx) * u + (1.2 if k % 2 else -1.2)
        y = ty + (fy - 1.2 - ty) * u
        pts.append((x, y))
    for k, (a, b) in enumerate(zip(pts, pts[1:])):                   # front loops lit, back loops dark: a coil, no outline
        k_lit = (7 if k % 2 == 0 else 2) if depth == 0 else (4 if k % 2 == 0 else 1)
        cv.part(Xf(), Capsule(a, b, 1.1), "steel", flat(k_lit, bevel=False), rust=0.0, outline=False)   # a chrome coil
    cv.part(Xf(), Poly([(fx - 2.8, fy - 2.6), (fx + 2.0, fy - 2.6), (fx + 2.6, fy + 0.4), (fx - 3.4, fy + 0.4)]), "steel",
            flat(3, bevel=False) if depth else face((-0.5, -0.5, 0.7), lo=2, hi=6, ramp_len=9, fixed=True), rust=0.0)   # the flat foot


def barrel(mid, glow, xf, p):
    """The barrel (staves, hoops, face) in its own space: x -5.5..5.5, y -12..0 (its bottom on its local origin)."""
    w, h = BARREL_W / 2.0, BARREL_H
    shape = Poly([(-w + 0.6, -h), (w - 0.6, -h), (w, -h + 2.2), (w + 0.4, -h / 2), (w, -2.2), (w - 0.6, 0.0), (-w + 0.6, 0.0), (-w, -2.2),
                  (-w - 0.4, -h / 2), (-w, -h + 2.2)])
    inner = mid.part(xf, shape, "oak", texture(face((-0.6, -0.3, 0.75), lo=2, hi=5, ramp_len=6, gain=1.3, bias=0.25, fixed=True, dither=0.16),
                                               "grain", seed=7), shadow=(1, 1), rust=0.0)
    # the staves: dark grooves with a lit lip, bowing with the barrel
    for sx in (-4.2, -1.2, 1.8, 4.8):
        for k in range(int(h * 2)):
            ly = -h + 0.6 + k * 0.5
            bow = 0.6 * math.sin(math.pi * (ly + h) / h) * (1 if sx > 0 else -1)
            q = P(xf, (sx + bow, ly))
            if q in inner:
                mid.put(q[0], q[1], OK[1])
                if (q[0] + 1, q[1]) in inner and sx < 2:
                    mid.put(q[0] + 1, q[1], OK[5] if ly < -h * 0.55 else OK[4])
    # two riveted iron hoops
    for hy in (-h + 2.6, -2.8):
        band = mid.raster(xf, box(-w - 1.0, hy - 0.8, w + 1.0, hy + 0.8)) & (inner | mid.raster(xf, shape))
        for q in band:
            lx, ly = xf.inv((q[0] + 0.5, q[1] + 0.5))
            mid.put(q[0], q[1], ST[7] if ly < hy - 0.4 else (ST[5] if ly < hy + 0.4 else ST[3]))
        for rx in (-3.6, 0.4, 3.8):
            q = P(xf, (rx, hy - 0.4))
            if q in band:
                mid.put(q[0], q[1], ST[8])
                if (q[0] + 1, q[1] + 1) in band:
                    mid.put(q[0] + 1, q[1] + 1, ST[2])
    # the face: two round goggles with ember lenses, a jagged grin
    for ex in (-4.4, -0.6):
        e = P(xf, (ex, -h + 5.8))
        for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (2, -1), (-1, 0), (2, 0), (-1, 1), (2, 1), (-1, 2), (0, 2), (1, 2), (2, 2)):
            mid.put(e[0] + dx, e[1] + dy, G[8] if dy < 0 or dx < 0 else G[4])  # the goggle's brass ring
        for (dx, dy, col) in ((0, 0, E[3]), (1, 0, E[2]), (0, 1, E[2]), (1, 1, E[1])):
            mid.put_glow(e[0] + dx, e[1] + dy, col)
            glow.put_glow(e[0] + dx, e[1] + dy, col)
    mouth_y = -h + 9.6
    for k in range(8):
        q = P(xf, (-5.6 + k * 1.0, mouth_y + (0.6 if k in (0, 7) else 0.0)))
        if q in inner:
            mid.put(q[0], q[1], OK[0])
            below = (q[0], q[1] + 1)
            if below in inner:
                mid.put(below[0], below[1], IV[4] if k % 2 == 1 else OK[0])    # a jagged grin: an ivory tooth, then a gap
            above = (q[0], q[1] - 1)
            if above in inner and k % 2 == 0 and 0 < k < 7:
                mid.put(above[0], above[1], IV[3])
    return inner


def dynamite(mid, glow, xf, p):
    """Four red sticks bundled out of the barrel's top, paper bands, a fuse curling up from the middle, its spark."""
    h = BARREL_H
    # one outlined bundle (thin sticks drown in their own outlines), each stick modelled inside it, dark seams between
    sticks = []
    for k, (sx, top, lean) in enumerate(((-4.2, -h - 4.4, -0.8), (-1.4, -h - 6.2, -0.2), (1.4, -h - 5.6, 0.3), (4.2, -h - 4.0, 0.9))):
        sticks.append((Poly([(sx - 1.5, -h + 0.6), (sx + 1.5, -h + 0.6), (sx + 1.5 + lean, top), (sx - 1.5 + lean, top)]), sx, top, lean))
    bundle = mid.part(xf, Union(*[st[0] for st in sticks]), "crimson",
                      face((-0.6, -0.2, 0.75), lo=2, hi=5, ramp_len=6, gain=1.3, bias=0.15, fixed=True), rust=0.0)
    for k, (shape, sx, top, lean) in enumerate(sticks):
        inner = mid.part(xf, shape, "crimson", cyl((sx - 1.5, -h), (sx - 1.5 + lean, top), 1.6, lo=2, hi=5, gain=1.4, fixed=True),
                         outline=False, clip=bundle, rust=0.0)
        if k > 0:
            for j in range(int(h * 0.0 - top - h) + 6):
                q = P(xf, (sx - 1.5 + lean * (j / 6.0), -h + 0.2 - j))
                if q in bundle:
                    mid.put(q[0], q[1], K[1])                           # the seam to the stick before it
        for by in (top + 2.0, top + 2.6):
            for bx in (sx - 0.6 + lean * 0.7, sx + 0.4 + lean * 0.7):
                q = P(xf, (bx, by))
                if q in inner:
                    mid.put(q[0], q[1], IV[4] if bx < sx + lean * 0.7 else IV[2])   # the paper band
        q = P(xf, (sx - 0.4 + lean, top + 0.6))
        if q in inner:
            mid.put(q[0], q[1], IV[3])                                  # its cut end
    pts = [(-1.4, -h - 6.0), (-0.6, -h - 7.8), (0.8, -h - 9.0), (1.8, -h - 10.6), (1.8, -h - 11.8)]
    for a, b in zip(pts, pts[1:]):
        for q in mid.raster(xf, Capsule(a, b, 0.5)):
            mid.put(q[0], q[1], H[2])
    tip = P(xf, pts[-1])
    sparks = (((0, 0, E[3]),), ((0, 0, WHITE), (0, -1, E[3]), (1, 0, E[2])),
              ((0, 0, WHITE), (0, -1, E[3]), (1, 0, E[3]), (-1, 0, E[2]), (0, -2, E[2]), (1, -1, E[2]), (-1, -1, E[1])))[p.spark]
    for (dx, dy, col) in sparks:
        mid.put_glow(tip[0] + dx, tip[1] + dy, col)
        glow.put_glow(tip[0] + dx, tip[1] + dy, col)
    return xf.fwd(pts[-1])


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    base = -(p.lift - p.bob)
    xf = Xf.pose(-p.tilt, (0.0, 0.0), (float(p.shake), base))
    nf, ff = p.near_foot, p.far_foot
    fy = base + (-1.0 if p.air else 0.0)
    nfoot = (nf[0], (fy + 4.0) if p.air else -nf[1])
    ffoot = (ff[0], (fy + 4.0) if p.air else -ff[1])
    spring_leg(far, xf.fwd((3.0, -0.6)), (ffoot[0] + p.shake, ffoot[1]), 1)
    barrel(mid, glow, xf, p)
    spark = dynamite(mid, glow, xf, p)
    spring_leg(near, xf.fwd((-2.6, -0.6)), (nfoot[0] + p.shake, nfoot[1]), 0)
    for cv in (far, mid, near):
        finish(cv)
    return far, mid, near, glow, spark


FRAMES = [("Idle0", Pose(lift=6.0)), ("Idle1", Pose(lift=6.0, bob=1)),
          ("Hop0", Pose(lift=4.0, near_foot=(-2.4, 0.0), far_foot=(2.4, 0.0))),                 # crouch
          ("Hop1", Pose(lift=7.0)),                                                             # springing up
          ("Hop2", Pose(lift=6.0, air=True)),                                                   # tucked, in the air
          ("Hop3", Pose(lift=5.0, bob=1, near_foot=(-2.6, 0.0), far_foot=(2.6, 0.0))),          # landing
          ("Windup0", Pose(lift=2.0, spark=2, near_foot=(-2.8, 0.0), far_foot=(2.8, 0.0))),
          ("Windup1", Pose(lift=2.0, spark=2, shake=1, near_foot=(-2.8, 0.0), far_foot=(2.8, 0.0))),
          ("Leap", Pose(lift=9.0, tilt=18.0, spark=2, near_foot=(1.0, 0.0), far_foot=(3.0, 0.0)))]
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The blast and the gores
# ================================================================================================
BLAST_FRAMES = 7
BLAST_SIZE = 64                            # 1x, centred: 128x128 in game (the blast radius is 64 px: 4 tiles)


def blast_frame(k):
    rng = random.Random(70 + k)
    cv = Canvas()
    c = BLAST_SIZE / 2.0
    r = (12.0, 21.0, 27.0, 29.5, 30.0, 29.0, 27.0)[k]
    if k <= 3:
        for (x, y) in cv.raster(Xf(), Ellipse(c, c, r, r)):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) / r
            n = rng.random() * 0.12
            col = S[3] if d + n < 0.32 - 0.08 * k else (E[3] if d + n < 0.62 else (E[2] if d + n < 0.86 else E[1]))
            cv.put(x, y, col)
    if k >= 2:
        puffs = 11
        for j in range(puffs):
            a = 2.0 * math.pi * j / puffs + 0.2
            dist = r * (0.55 + 0.1 * (k - 2))
            pr = max(2.0, 8.0 - 1.1 * (k - 2) + rng.random())
            px, py = c + math.cos(a) * dist, c + math.sin(a) * dist - (k - 2) * 1.8
            for (x, y) in cv.raster(Xf(), Ellipse(px, py, pr, pr)):
                d = math.hypot(x + 0.5 - px + 1, y + 0.5 - py + 1) / pr
                cv.put(x, y, S[1] if d < 0.5 else (S[0] if d < 0.85 else I[2]))
    if 1 <= k <= 4:                                                    # splinters of stave and shards of hoop flying out
        for j in range(12):
            a = rng.random() * 2 * math.pi
            d = r * (0.7 + 0.25 * rng.random()) + k * 1.5
            x, y = c + math.cos(a) * d, c + math.sin(a) * d
            ramp = LE if j % 3 else I
            for t in range(3):
                q = (int(math.floor(x + math.cos(a) * t)), int(math.floor(y + math.sin(a) * t)))
                cv.put(q[0], q[1], ramp[2] if t == 0 else ramp[1])
    if k <= 3:
        for _ in range(12 - 3 * k):
            a = rng.random() * 2 * math.pi
            d = rng.random() * r * 0.8
            x, y = int(c + math.cos(a) * d), int(c + math.sin(a) * d)
            cv.put(x, y, E[3])
            cv.put(x + 1, y, E[2])
    return cv


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Idle0"])
    return {"Dinamitrom_GoreStave": crop({q: c for q, c in mid.px.items() if q[0] <= -2 and -16 <= q[1] <= -7}),
            "Dinamitrom_GoreHoop": crop({q: c for q, c in mid.px.items() if c in (I[3], I[1], I[4]) and q[1] < -12}),
            "Dinamitrom_GoreStick": crop({q: c for q, c in mid.px.items() if q[1] < -18 and q[0] <= 0})}


def write_rig(path, cell, spark):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/oldbrasstown/make_dinamitrom_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.OldBrassTown.NPCs",
         "{",
         "\t/// <summary>The Dinamitrom's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells",
         "\t/// with 2 px under each; the origin is the ground point under its feet. The fuse's spark is from the origin, facing left,",
         "\t/// at rest. The blast sheet holds <see cref=\"BlastFrames\"/> frames of <see cref=\"BlastSize\"/> px.</summary>",
         "\tpublic static class DinamitromRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Idle = %d, IdleFrames = 2, Hop = %d, HopFrames = 4, Windup = %d, WindupFrames = 2, Leap = %d;"
         % (INDEX["Idle0"], INDEX["Hop0"], INDEX["Windup0"], INDEX["Leap"]),
         "\t\tpublic const int SparkX = %d, SparkY = %d;" % (round(spark[0] * 2), round(spark[1] * 2)),
         "\t\tpublic const int BlastFrames = %d, BlastSize = %d;" % (BLAST_FRAMES, BLAST_SIZE * 2),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Dinamitrom%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Dinamitrom_Glow.png")
    write_rig(OUT + "NPCs/DinamitromRigData.cs", cell, frames[INDEX["Idle0"]][4])
    export(vertical([to_image(blast_frame(k).px, 0, 0, BLAST_SIZE, BLAST_SIZE) for k in range(BLAST_FRAMES)]), OUT + "Projectiles/DinamitromBlast.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 30, 34
    sheet = Image.new("RGBA", (cw * len(FRAMES), ch * 2 + BLAST_SIZE), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * len(FRAMES), ch), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
                t.alpha_composite(to_image(cv.px, -cw // 2, -ch + 3, cw, ch))
            tile.alpha_composite(t, (k * cw, 0))
        sheet.paste(tile, (0, half * ch))
    blast = Image.new("RGBA", (cw * len(FRAMES), BLAST_SIZE), (36, 40, 48, 255))
    for k in range(4):
        blast.alpha_composite(to_image(blast_frame(k * 2).px, 0, 0, BLAST_SIZE, BLAST_SIZE), (k * BLAST_SIZE // 1, 0))
    sheet.paste(blast, (0, ch * 2))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
