"""The Jade Token and its spirit fox, v3 2026-11-23. Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--preview FILE]

History: 2026-11-18 the user's design (reference/jade_fox_user_2026-11-18.webp) traced at 60% with a few hand pixels;
2026-11-19 the user kept that trace ("leave the fox as it was") with a tail sway while it moves (previous/
make_jade_fox_art_2026-11-19b.py). 2026-11-23 (user: "provide a redesign of our most bellow average sprites like Jadey, Fox
spirit, fungimancer ... keeping the theme but reworking with found data analisis"; docs/design/sprite-quality-study.md): the
trace measured 13 colours, a body at L* 75 and jumps of 32 L* between neighbours, so the fox is modelled again from the user's
design (its parts, colours and ornaments), with the cogpunk-pixel-art skill's method (art/templates/sculpt.py): every part a
shape with a surface normal sampled 4 x 4 per art pixel, pixelated per part, shaded in bands of its ramp with dither only at
band edges, a selective outline, a rim light, a cast shadow on what is behind.

The fox (faces right, the pet flips by direction; its feet on the cell's bottom row): pale mint fur (the sage ramp, cool green
shadows to cream light) with fur strands, a chest ruff, big ears lined with jade, a slender snout with a dark nose, a big jade
eye with a glint under a gilt mask, a jade gem on the brow, a gilt collar with a jade pendant, slim legs with gilt bands on
the near pair, a big fluffy brush of a tail ending in a jade spirit flame (the user's design) that glows. Frames (JadeFoxPet's
constants, unchanged): Idle 0-3, Trot 4-9 (the tail sways up and down, user 2026-11-19), Float 10-13, Settle 14-15, Sleep
16-17, Wake 18-20. Outputs: JadeFoxPet.png + _Glow.png (21 frames of 40 x 29 at 1x, 1 px apart), JadeFoxBuff.png (the head),
JadeToken.png (the coin, unchanged: from the 2026-11-19 generator).
"""
import argparse
import importlib.util
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "jadey"))
from sculpt import Frame, Ell, Tube, Poly, Part, render  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Coghaven/Pets/"
SA, EM, G, SM = RAMP["sage"], RAMP["emerald"], RAMP["gilt"], RAMP["steam"]
CELL_W, CELL_H, FRAMES_N = 40, 29, 21
OX, OY = 26, 28                    # the rig origin (the ground under the body's middle) in the cell; OriginX 52 at 2x


class Pose:
    def __init__(self, body=0.0, head=0.0, legs=None, tuck=0.0, lie=False, eye=True, tail=0.0, flame=0, stretch=0.0):
        self.body, self.head = body, head            # px the body / the head sit lower (< 0 higher)
        self.legs = legs or {}                        # leg -> swing (radians, + forward)
        self.tuck, self.lie, self.eye = tuck, lie, eye
        self.tail = tail                              # radians the tail rises (< 0 dips): the sway
        self.flame = flame                            # the flame's flicker phase (0-3)
        self.stretch = stretch                        # 0..1: the wake's stretch (forelegs out, rump up)


def leg(parts, name, hip, length, swing, z, dim, tuck, band=False):
    hx, hy = hip
    if tuck:
        foot = (hx - 1.2 * tuck, hy + length * (1.0 - 0.55 * tuck))
    else:
        foot = (hx + math.sin(swing) * length, hy + math.cos(swing) * length)
    knee = ((hx + foot[0]) / 2.0 + (0.6 if "Fore" in name else -0.6), (hy + foot[1]) / 2.0)
    parts.append(Part(name, Tube([hip, knee, foot], [1.7, 1.35, 1.2]), SA, z, lo=1, hi=5 - dim, bump_step=False))
    parts.append(Part(name + "Paw", Ell(0.0, 0.0, 1.6, 1.05), SA, z + 0.05, frame=Frame(foot[0] + 0.5, foot[1] - 0.4), lo=2, hi=5 - dim))
    return foot


def model(p):
    parts = []
    b = p.body
    # the tail: a fluffy brush from the rump, sweeping back and up, its flame tip glowing jade (behind everything)
    root = (-12.0, -10.0 + b)
    t = p.tail

    def tp(dx, dy):
        c, s_ = math.cos(-t), math.sin(-t)
        return (root[0] + dx * c - dy * s_, root[1] + dx * s_ + dy * c)
    brush = [tp(0, 0), tp(-4.5, -1.0), tp(-8.0, -3.5), tp(-9.5, -7.0), tp(-9.0, -10.5)]
    parts.append(Part("Tail", Tube(brush, [3.0, 4.6, 5.0, 4.2, 2.8]), SA, 1, lo=1, hi=4, gain=1.0,
                      lines=((tp(-2.5, 0.5), tp(-6.5, -2.0), tp(-9.0, -6.0)), (tp(-4.0, 2.4), tp(-8.5, 0.0)),
                             (tp(-6.0, -6.5), tp(-7.0, -9.5)))))
    fl = p.flame
    flame = [tp(-9.0, -10.0), tp(-8.6 + (fl % 2) * 0.6, -13.4), tp(-9.6 + (fl // 2) * 0.8, -16.0 - (fl == 1))]
    parts.append(Part("Flame", Tube(flame, [2.6, 1.7, 0.6]), EM, 1.1, lo=3, hi=6, glow_from=4, bump_step=False))
    # the far legs (behind the body), dimmer
    if not p.lie:
        leg(parts, "HindFar", (-10.0, -7.5 + b), 7.0, p.legs.get("HF", 0.0), 2, 1, p.tuck)
        leg(parts, "ForeFar", (1.0, -7.5 + b), 7.0, p.legs.get("FF", 0.0), 2, 1, p.tuck)
    # the body (short) and the chest ruff (big, pale)
    parts.append(Part("Body", Ell(0.0, 0.0, 8.2, 5.0), SA, 3, frame=Frame(-5.5, -9.5 + b, -0.06), lo=1, hi=4, gain=1.0,
                      lines=(((-5.0, 3.4), (-1.5, 4.2), (2.5, 4.0)),)))
    parts.append(Part("Ruff", Ell(0.0, 0.0, 4.6, 5.6), SA, 4, frame=Frame(1.5, -10.5 + b), lo=2, hi=5,
                      lines=(((-1.5, 1.2), (0.0, 3.8)), ((1.5, 0.4), (2.6, 2.8)))))
    # the near legs
    if not p.lie:
        leg(parts, "HindNear", (-8.5, -7.0 + b), 7.0, p.legs.get("HN", 0.0), 5, 0, p.tuck)
        leg(parts, "ForeNear", (2.5, -7.0 + b), 7.0, p.legs.get("FN", 0.0), 5, 0, p.tuck)
    else:
        for k, x in enumerate((4.5 + p.stretch * 2.0, 6.0 + p.stretch * 2.5)):         # the forepaws out in front
            parts.append(Part("PawOut%d" % k, Ell(0.0, 0.0, 2.2, 1.2), SA, 5 + k * 0.1, frame=Frame(x, -1.2), lo=2, hi=5))
    # the head (big, a fennec's), snout, cheek tuft, ears lined with jade, the far ear behind
    hb = b + p.head
    parts.append(Part("EarFar", Poly([(1.2, -19.5 + hb), (3.2, -28.5 + hb), (6.2, -20.5 + hb)]), SA, 5.5, lo=1, hi=3, dither=0.0))
    parts.append(Part("EarFarIn", Poly([(2.6, -20.5 + hb), (3.4, -26.0 + hb), (5.0, -20.8 + hb)]), EM, 5.6, lo=1, hi=2,
                      outline=False, dither=0.0))
    parts.append(Part("Head", Ell(0.0, 0.0, 5.8, 5.0), SA, 6, frame=Frame(5.5, -16.5 + hb), lo=1, hi=5))
    parts.append(Part("Snout", Ell(0.0, 0.0, 3.4, 2.1), SA, 6.2, frame=Frame(10.6, -15.0 + hb, 0.08), lo=2, hi=5))
    parts.append(Part("Cheek", Poly([(2.0, -14.5 + hb), (6.5, -11.6 + hb), (1.0, -10.8 + hb)]), SA, 6.1, lo=3, hi=5, dither=0.0))
    parts.append(Part("EarNear", Poly([(6.0, -20.0 + hb), (10.4, -30.0 + hb), (11.8, -18.8 + hb)]), SA, 6.4, lo=2, hi=5, dither=0.0))
    parts.append(Part("EarIn", Poly([(7.6, -20.4 + hb), (10.2, -27.4 + hb), (10.8, -20.2 + hb)]), EM, 6.5, lo=2, hi=4,
                      outline=False, dither=0.0))
    return parts


def stamp(px, glow, p):
    """The face and the gilt, by hand at the target size."""
    hb = p.body + p.head

    def put(x, y, c, g=False):
        q = (int(math.floor(x)) + OX, int(math.floor(y)) + OY)
        if q in px:
            px[q] = c
            if g:
                glow[q] = c
    ex, ey = 7.0, -17.6 + hb
    if p.eye:
        for (dx, dy, c, g) in ((0, 0, EM[5], True), (1, 0, EM[4], True), (0, 1, EM[3], True), (1, 1, EM[2], False),
                               (2, 0, EM[3], False), (2, 1, EM[1], False), (0, 2, SA[1], False), (1, 2, SA[1], False),
                               (-1, 0, SA[0], False), (-1, 1, SA[0], False), (3, 1, SA[0], False), (3, 0, SA[1], False),
                               (-1, -1, G[6], False), (0, -1, G[7], False), (1, -1, G[8], False), (2, -1, G[7], False),
                               (3, -1, G[6], False), (4, -1, G[5], False)):
            put(ex + dx, ey + dy, c, g)
        put(ex, ey, SM[3], True)                                 # the glint
    else:
        for dx in (-1, 0, 1, 2):
            put(ex + dx, ey + 0.6, SA[0])                        # shut
        for dx in (0, 1, 2):
            put(ex + dx, ey - 0.6, G[7])
    put(13.6, -15.4 + hb, SA[0])                                 # the nose
    put(13.6, -14.4 + hb, SA[1])
    put(4.4, -21.0 + hb, G[6])                                   # the brow gem in its gilt setting
    put(5.4, -21.0 + hb, EM[5], True)
    put(6.4, -21.0 + hb, G[7])
    put(5.4, -20.0 + hb, G[5])
    if not p.lie:                                                # the collar and its pendant
        for (x, y) in ((2.6, -14.0), (3.2, -13.2), (3.8, -12.4), (4.4, -11.6)):
            put(x, y + p.body, G[7] if x < 3.5 else G[5])
        put(4.6, -10.4 + p.body, EM[5], True)
        put(4.6, -9.4 + p.body, EM[3], True)
        for leg_name, x in (("HN", -8.5), ("FN", 2.5)):          # the gilt bands on the near legs
            sw = p.legs.get(leg_name, 0.0)
            put(x + math.sin(sw) * 4.0, -3.0 + p.body * 0.4, G[7])


def frame(p):
    parts = model(p)
    px, glow, owner = render(parts, CELL_W, CELL_H, OX, OY)
    stamp(px, glow, p)
    return px, glow


TAU = 2 * math.pi
TROT_TAIL = (0.08, 0.16, 0.08, 0.0, -0.08, 0.0)                    # the user's sway (2026-11-19), in radians now


def trot(k):
    ph = k / 6.0 * TAU
    s1, s2 = math.sin(ph) * 0.45, math.sin(ph + math.pi) * 0.45
    return Pose(body=-1.0 if k % 3 == 1 else 0.0, legs={"FN": s1, "HF": s1, "FF": s2, "HN": s2}, tail=TROT_TAIL[k], flame=k % 4)


POSES = ([Pose(body=b, tail=t, flame=k) for k, (b, t) in enumerate(((0, 0.0), (0, 0.03), (1, 0.05), (1, 0.02)))]
         + [trot(k) for k in range(6)]
         + [Pose(body=b, tuck=1.0, tail=t, flame=k) for k, (b, t) in enumerate(((0, 0.05), (-1, 0.12), (-1, 0.18), (0, 0.12)))]
         + [Pose(body=1, tuck=0.4, tail=-0.05, flame=1), Pose(body=4, lie=True, tail=-0.12, flame=2)]
         + [Pose(body=5, lie=True, eye=False, tail=-0.15, flame=0), Pose(body=5, head=1, lie=True, eye=False, tail=-0.15, flame=2)]
         + [Pose(body=5, lie=True, tail=-0.1, flame=1), Pose(body=2, stretch=1.0, lie=True, tail=0.1, flame=3), Pose(flame=0)])
assert len(POSES) == FRAMES_N


def sheet(frames, glow=False):
    im = Image.new("RGBA", (CELL_W, (CELL_H + 1) * FRAMES_N), (0, 0, 0, 0))   # 1 px under every frame (the game reads Height / 21)
    for k, (px, gl) in enumerate(frames):
        for (x, y), c in (gl if glow else px).items():
            if 0 <= x < CELL_W and 0 <= y < CELL_H:
                im.putpixel((x, y + k * (CELL_H + 1)), tuple(c) + (255,))
    return im


def buff_icon(px0):
    """The buff: the fox's head (frame 0) in 16 x 16."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    hx, hy = 6 + OX, -18 + OY
    for (x, y), c in px0.items():
        u, v = x - hx + 7, y - hy + 9
        if 0 <= u < 16 and 0 <= v < 16 and y <= -12 + OY:
            im.putpixel((u, v), tuple(c) + (255,))
    return im


def old_token():
    spec = importlib.util.spec_from_file_location("fox_prev", os.path.join(HERE, "previous", "make_jade_fox_art_2026-11-19b.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.boxed(mod.token(), 14, 14)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()
    frames = [frame(p) for p in POSES]
    if not args.no_export:
        export(sheet(frames), OUT + "JadeFoxPet.png")
        export(sheet(frames, glow=True), OUT + "JadeFoxPet_Glow.png")
        export(buff_icon(frames[0][0]), OUT + "JadeFoxBuff.png")
        export(old_token(), OUT + "JadeToken.png")
    if args.preview:
        sc = 6
        cols = 7
        rows = (FRAMES_N + cols - 1) // cols
        out = Image.new("RGBA", (cols * (CELL_W * sc + 6) + 6, rows * (CELL_H * sc + 6) + 6), (24, 24, 30, 255))
        for k, (px, gl) in enumerate(frames):
            im = Image.new("RGBA", (CELL_W, CELL_H), (40, 40, 48, 255))
            for (x, y), c in px.items():
                im.putpixel((x, y), tuple(c) + (255,))
            out.alpha_composite(im.resize((CELL_W * sc, CELL_H * sc), Image.NEAREST), (6 + (k % cols) * (CELL_W * sc + 6), 6 + (k // cols) * (CELL_H * sc + 6)))
        out.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
