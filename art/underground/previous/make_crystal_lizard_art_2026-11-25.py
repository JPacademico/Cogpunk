"""Source for the Crystal Lizard and the Tearstone (D4), 2026-11-25 (user: "add a new enemy that can spawn on the underground
called "cristal lizard" its a small rare underground enemy that runs from the player when takes damage or comes close and if
not killed in 5 seconds it dugs away and despawns. It should have good armor and drop from 1-5 gold coins and 1-3 of a random
gem and a small chance to drop a accessory called "tearstone" that gives 10 defense when the player is at full hp").
Run from the repo root:

    python -P art/underground/make_crystal_lizard_art.py [--preview FILE]

Design (my calls): a low, long cave lizard of slate (the palette's iron ramp) with a pale underside, a flat wedge head with a
bright little eye, and a back armoured in faceted crystal shards (denim's blues to steam's white: every shard two flat facets,
the one facing the top-left light pale, the other in shadow, a white glint on the tallest). Sculpted (art/templates/sculpt.py),
three-quarter side view facing left. Two planes: far (the far legs) and middle; the glow sheet holds the crystals' lit facets.

Frames:
    Idle 0-1    the tail's tip flicks a pixel
    Alert 2     head up, looking round (the moment it notices you)
    Run 3-8     a scuttle: legs in diagonal pairs, the body a pixel up on the push, the tail swaying
    Dig 9-12    nose down, scrabbling (the C# sinks it into the ground over these: DepthLayers' buried clip)

Also the Tearstone (Items/Tearstone.png, 16 x 16 art): a silver ring set with a tear-shaped stone of the same crystal.

Outputs (Content/Underground/): NPCs/CrystalLizard.png, _Far.png, _Glow.png, NPCs/CrystalLizardRigData.cs, Items/Tearstone.png.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from sculpt import Frame, Ell, Tube, Poly, Part, render  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402
from pixkit import Pix  # noqa: E402

OUT = "Content/Underground/"
IRON, IV, DN, STM, ST = RAMP["iron"], RAMP["ivory"], RAMP["denim"], RAMP["steam"], RAMP["steel"]
# the crystals: deep teal to cyan to white (the glowing mushrooms' cyans, already in the palette), darkest first
CRYSTAL = ((10, 47, 71), (8, 100, 114), (11, 135, 137), (12, 176, 161), (67, 221, 248), STM[1], STM[2])
SKIN = DN                                                                # a blue-grey hide (denim): one body under the crystals
S = 1.4                                                                  # the model's scale (it was too small to read)
W, H, OX, OY = 50, 24, 22, 22


class Pose:
    def __init__(self, phase=None, bob=0, head=0.0, tail=0.0, dig=0.0):
        self.phase, self.bob, self.head, self.tail, self.dig = phase, bob, head, tail, dig


def leg_feet(phase):
    """Four feet (near front, near hind, far front, far hind) as (dx, lift) for a scuttle phase 0..1, diagonal pairs; None:
    standing."""
    if phase is None:
        return [(0.0, 0.0)] * 4
    out = []
    for k, off in enumerate((0.0, 0.5, 0.5, 0.0)):
        t = (phase + off) % 1.0
        if t < 0.5:
            out.append((2.2 - 4.4 * (t / 0.5), 0.0))
        else:
            u = (t - 0.5) / 0.5
            out.append((-2.2 + 4.4 * u, 1.2 * math.sin(math.pi * u)))
    return out


def sc(pts):
    return [(x * S, y * S) for (x, y) in pts]


def parts(p):
    b = -p.bob / S                                                       # the bob stays a whole pixel after scaling
    pitch = 0.32 * p.dig                                                 # digging: the whole body tips nose down
    body = Frame(0.0, (-3.6 + b + 1.2 * p.dig) * S, pitch, S, S)
    headf = Frame(-7.6 * S, (-3.8 + b - 1.4 * p.head + 3.0 * p.dig) * S, -0.25 * p.head + 0.55 * p.dig, S, S)
    tailf = Frame(5.6 * S, (-3.0 + b + 0.6 * p.dig) * S, 0.10 * p.tail + 0.2 * p.dig, S, S)
    feet = leg_feet(p.phase)
    out = []
    # far legs (far plane)
    for k, (hx, rest) in enumerate(((-3.6, -5.8), (3.6, 2.4))):
        fx, lift = feet[2 + k]
        if p.dig > 0.3:
            fx += -1.0 + (k * 2 - 1) * 0.8 * math.sin(p.dig * 9.0)        # scrabbling
        out.append(Part("leg_far%d" % k, Tube(sc([(hx - 1.4, -3.0 + b), (rest + fx + 1.0, -1.6 - lift), (rest + fx, -0.4 - lift)]),
                                              [1.0 * S, 0.8 * S, 0.7 * S]), SKIN, 0, None, lo=1, hi=3, plane="far"))
    # the tail (a long taper, swaying)
    sway = p.tail
    out.append(Part("tail", Tube([(0.0, 0.0), (5.0, 0.6 + 0.4 * sway), (10.0, 1.4 + 1.0 * sway), (14.0, 1.8 + 1.6 * sway)],
                                 [2.2, 1.6, 1.0, 0.5]), SKIN, 1, tailf, lo=1, hi=5,
                    bumps=((3.0, -0.8, 0.8), (7.0, 0.0, 0.7))))
    out.append(Part("body", Ell(0.0, 0.0, 6.8, 3.2), SKIN, 2, body, lo=1, hi=5,
                    bumps=((-3.0, -1.6, 1.0), (1.0, -2.0, 1.0), (4.0, -1.2, 0.9))))
    out.append(Part("belly", Ell(-0.6, 1.7, 5.8, 1.4, 0.4), IV, 3, body, lo=1, hi=4))
    out.append(Part("head", Poly([(-4.4, 0.4), (-3.0, -1.8), (0.8, -2.4), (2.6, -1.0), (2.4, 1.6), (-1.2, 1.8), (-4.0, 1.2)], tilt=(0.0, -0.25)),
                    SKIN, 4, headf, lo=1, hi=5, dither=0.0))
    out.append(Part("jaw", Poly([(-4.2, 0.8), (-0.6, 1.4), (2.0, 1.6), (-1.0, 2.2), (-3.6, 1.6)], tilt=(0.0, 0.4)), IV, 5, headf,
                    lo=1, hi=4, dither=0.0))
    # near legs
    for k, (hx, rest) in enumerate(((-4.6, -7.0), (2.8, 1.6))):
        fx, lift = feet[k]
        if p.dig > 0.3:
            fx += -1.0 + (k * 2 - 1) * 0.8 * math.sin(p.dig * 9.0 + 1.5)
        out.append(Part("leg%d" % k, Tube(sc([(hx, -2.6 + b), (rest + fx + 1.2, -1.4 - lift), (rest + fx, -0.2 - lift)]),
                                          [1.1 * S, 0.9 * S, 0.8 * S]), SKIN, 6, None, lo=1, hi=5))
    # the crystals: faceted shards along the back, each two flat facets (lit and shadowed), tallest in the middle
    shards = ((-4.6, -2.0, 2.0, 3.4, -0.25), (-1.4, -2.8, 2.4, 4.8, -0.08), (2.0, -2.6, 2.2, 4.2, 0.12), (4.8, -1.6, 1.7, 3.0, 0.3))
    for i, (sx, sy, half, height, lean) in enumerate(shards):
        tip = (sx + lean * height, sy - height)
        left = Poly([(sx - half, sy + 0.6), tip, (sx + 0.2, sy + 0.8)], tilt=(-0.7, -0.5))
        right = Poly([(sx + 0.2, sy + 0.8), tip, (sx + half, sy + 0.4)], tilt=(0.8, 0.1))
        out.append(Part("shardL%d" % i, left, CRYSTAL, 7 + 2 * i, body, lo=4, hi=6, dither=0.0, glow_from=5))
        out.append(Part("shardR%d" % i, right, CRYSTAL, 8 + 2 * i, body, lo=1, hi=3, dither=0.0))
    return out, headf, body, shards


def frame(p):
    ps, headf, body, shards = parts(p)
    far, _, _ = render([q for q in ps if q.plane == "far"], W, H, OX, OY)
    far = {q: SKIN[max(0, SKIN.index(c) - 1)] if c in SKIN else c for q, c in far.items()}
    mid, glow, owner = render([q for q in ps if q.plane != "far"], W, H, OX, OY)
    # the eye (after the outline): a bright bead with a dark rim under it
    ex, ey = headf.to_world(-1.0, -0.8)
    e = (int(math.floor(ex + OX)), int(math.floor(ey + OY)))
    if e in mid:
        mid[e] = STM[2]
        glow[e] = STM[2]
        under = (e[0], e[1] + 1)
        if under in mid:
            mid[under] = SKIN[0]
    # the tallest shard's glint
    sx, sy, half, height, lean = shards[1]
    gx, gy = body.to_world(sx + lean * height - 0.3, sy - height + 1.4)
    g = (int(math.floor(gx + OX)), int(math.floor(gy + OY)))
    if g in mid and owner.get(g, "").startswith("shard"):
        mid[g] = STM[3]
        glow[g] = STM[3]
    if p.dig > 0.0:                                                    # dirt kicked up by the claws as it digs in
        oak = RAMP["oak"]
        k = int(round(p.dig * 4))
        for i, (dx, dy) in enumerate(((-13, -2), (-15, -4), (-12, -5), (-16, -1), (-14, -6), (-11, -3))):
            if (i + k) % 3 != 0:
                q = (OX + dx - (k % 2), OY + dy - (k // 2))
                if q not in mid:
                    mid[q] = oak[1 + (i + k) % 3]
    return far, mid, glow


RUN = 6
FRAMES = (
    [("Idle0", Pose()), ("Idle1", Pose(tail=0.6)), ("Alert", Pose(head=1.0, tail=-0.4))]
    + [("Run%d" % k, Pose(phase=k / RUN, bob=1 if k % 3 == 1 else 0, tail=0.8 * math.sin(k / RUN * math.tau))) for k in range(RUN)]
    + [("Dig%d" % k, Pose(dig=(k + 1) / 4.0, tail=0.6 * math.sin(k * 1.7))) for k in range(4)]
)
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def to_image(px, w=W, h=H):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def grid(images):
    out = Image.new("RGBA", (W, (H + 1) * len(images)), (0, 0, 0, 0))
    for k, im in enumerate(images):
        out.alpha_composite(im, (0, k * (H + 1)))
    return out


def write_rig(path, frames):
    _, mid, _ = frames[0]
    xs = sorted(x for (x, y) in mid)
    ys = sorted(y for (x, y) in mid)
    left, right, top = (xs[1] - OX) * 2, (min(xs[-1], OX + 11) - OX + 1) * 2, (ys[len(ys) // 20] - OY) * 2   # the tail left out
    L = ["// <auto-generated> by art/underground/make_crystal_lizard_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Underground.NPCs",
         "{",
         "\t/// <summary>The Crystal Lizard's grid sheets (game px, facing left): far and middle planes and the glow, equal cells with",
         "\t/// 2 px under each; the origin is the ground point under its body. Body*: its hitbox from the origin (head and body,",
         "\t/// the tail left out). RunStep: game px a foot slides back per run frame.</summary>",
         "\tpublic static class CrystalLizardRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (W * 2, H * 2, OX * 2, OY * 2, len(FRAMES)),
         "\t\tpublic const int Idle = 0, IdleFrames = 2, Alert = %d, Run = %d, RunFrames = %d, Dig = %d, DigFrames = 4;"
         % (INDEX["Alert"], INDEX["Run0"], RUN, INDEX["Dig0"]),
         "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d;" % (left, right, top),
         "\t\tpublic const int RunStep = %d;" % round(4.4 * S * 2 / (RUN / 2)),
         "\t}",
         "}"]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def tearstone():
    """16 x 16: a silver ring (steel, lit from the top-left) set with a tear-shaped crystal (the lizards' own), a glint."""
    p = Pix(16, 16)
    cx, cy, r_out, r_in = 8.0, 10.2, 5.8, 2.7
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.15)
            if r_in < d <= r_out and y >= 5:
                lit = -((x + 0.5 - cx) + (y + 0.5 - cy)) / (r_out * 1.4)
                p.put(x, y, ST, 6 + round(lit * 2))
    # the tear: a drop pointing up, set on the ring's top
    drop = ((7, 1), (8, 1), (7, 2), (8, 2), (6, 3), (7, 3), (8, 3), (9, 3), (6, 4), (7, 4), (8, 4), (9, 4), (5, 5), (6, 5), (7, 5),
            (8, 5), (9, 5), (10, 5), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6), (6, 7), (7, 7), (8, 7), (9, 7))
    for (x, y) in drop:
        lit = -((x - 7.5) * 0.7 + (y - 4.5) * 0.7) / 3.5
        i = 3 + round(lit * 2.2)
        p.put(x, y, CRYSTAL, max(1, min(6, i)))
    for (x, y) in ((5, 7), (10, 7)):
        p.put(x, y, ST, 4)                                             # the claws of the setting
    p.outline()
    p.put(7, 3, STM, 3, lock=True)                                     # the glint
    p.put(6, 5, CRYSTAL, 6, lock=True)
    return p.image()


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    export(grid([to_image(f[0]) for f in frames]), OUT + "NPCs/CrystalLizard_Far.png")
    export(grid([to_image(f[1]) for f in frames]), OUT + "NPCs/CrystalLizard.png")
    export(grid([to_image(f[2]) for f in frames]), OUT + "NPCs/CrystalLizard_Glow.png")
    write_rig(OUT + "NPCs/CrystalLizardRigData.cs", frames)
    export(tearstone(), OUT + "Items/Tearstone.png")
    return frames


def preview(path, frames, sc=6):
    cols = 7
    rows = (len(frames) + cols - 1) // cols
    out = Image.new("RGBA", (cols * (W * sc + 6) + 6 + 16 * sc + 12, rows * 2 * (H * sc + 6) + 6), (20, 20, 24, 255))
    for half, bg in enumerate(((30, 34, 60), (170, 190, 210))):
        for k, (far, mid, glow) in enumerate(frames):
            im = Image.new("RGBA", (W, H), bg + (255,))
            im.alpha_composite(to_image(far))
            im.alpha_composite(to_image(mid))
            x = 6 + (k % cols) * (W * sc + 6)
            y = 6 + (half * rows + k // cols) * (H * sc + 6)
            out.alpha_composite(im.resize((W * sc, H * sc), Image.NEAREST), (x, y))
    t = Image.new("RGBA", (16, 16), (30, 34, 60, 255))
    t.alpha_composite(tearstone())
    out.alpha_composite(t.resize((16 * sc, 16 * sc), Image.NEAREST), (out.width - 16 * sc - 6, 6))
    out.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args()
    fr = [frame(p) for _, p in FRAMES] if a.no_export else export_all()
    if a.preview:
        preview(a.preview, fr)
