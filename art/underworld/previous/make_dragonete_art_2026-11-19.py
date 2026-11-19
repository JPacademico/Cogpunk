"""Source for the Dragonete Miudo (D4), 2026-11-11 (user: "add a new enemy to the hell biome called Dragonete miudo it
should be a baby dragon that spits fire bolts at a distance and if it misses it comes flying trying to bite the
player"). Run from the repo root:

    python -P art/underworld/make_dragonete_art.py [--preview FILE]

Design (my calls): a chubby baby dragon of the Underworld, three-quarter side view facing left (D4 rule 13), chibi
(D4 rule 18: the head nearly as big as the body). Crimson scales lit from the top-left with a scale lattice in their own
space, a warm gilt belly in plates, a short snout with two nostrils and a little fang, big gilt eyes with a slit pupil,
two ivory horn nubs and a row of ivory spines down the back, stubby legs with ivory claws, a curling tail ending in a
spade, and bat wings of ember membrane on crimson finger bones.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far wing, the far legs, the far horn, a step darker), middle
(tail, body, belly, head, jaw, the near horn), near (the near wing and legs); the glow sheet holds the eyes, the throat's
fire while it inhales and the burst in its mouth. Stable pixels (D4 rule 17): every part lit in its own space, placed by
whole pixels; the bob of the flight is done in code (the whole sprite, every plane together).

Frames:
- Fly x6: one wing beat (up, half, level, down, half, up again), the tail swinging a pixel against it.
- Inhale x3: the telegraph: the head rears back, the chest swells, the throat glows brighter each frame.
- Spit x3: the head lunges, the jaw drops on a burst of fire, the recoil.
- Swoop x2: tipped nose-down, wings swept back, jaws open, a wing twitch.
- Bite x3: jaws wide, snapped shut, the recoil.

Outputs:
    Content/Underworld/NPCs/DragoneteMiudo.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Underworld/NPCs/DragoneteMiudoRigData.cs   cells, origin, frames, the mouth (from the origin, facing left)
    Content/Underworld/Projectiles/DragoneteFireBolt.png   16x16 a frame, 4 frames, stride 18
    Content/Underworld/Gores/DragoneteMiudo_GoreHead.png, _GoreWing.png, _GoreTail.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, Canvas, flat, dome, P, limb, finish, texture)  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402
import pixkit  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Underworld/"
K, G, IV, EM, SM = RAMP["crimson"], RAMP["gilt"], RAMP["ivory"], RAMP["ember"], RAMP["steam"]
FAR = (2, -1)                                  # the far side's wing, legs and horn: back and up a pixel (whole px)

# --- the rig (art px, facing left, y down, the origin under its middle where its feet would touch the ground) ---------
BODY = (3.0, -11.0, 7.4, 6.0)                  # the round body: centre, radii
BELLY = (1.4, -9.0, 5.2, 4.4)
NECK = (-3.0, -13.0)                           # the head's pivot
HEAD = (-7.8, -17.0, 7.0, 6.2)                 # big chibi head
SNOUT = (-13.8, -15.0, 3.4, 2.6)
JAW_PIVOT = (-9.0, -12.6)
SHOULDER = (2.0, -15.0)                        # the wing's root
TAIL = [(9.0, -9.0, 2.8), (13.0, -6.6, 2.1), (16.6, -6.8, 1.6), (19.2, -9.4, 1.2)]
SPADE = (20.4, -11.0)
HIPS = {"fore": (-2.4, -7.2), "hind": (5.0, -6.6)}
FEET = {"fore": (-1.6, -4.6), "hind": (7.6, -3.6)}   # tucked for flight: fore under the chest, hind trailing
EYE = (-9.8, -18.2)
MOUTH = (-17.6, -13.2)                         # where the bolt leaves, before the head's pose


class Pose:
    def __init__(self, wing=0.0, spread=1.0, head=0.0, jaw=0.0, tilt=0.0, puff=0.0, tail=0, throat=0, fire=0, legs=0):
        self.wing = wing                # degrees the wings beat (- up, + down)
        self.spread = spread            # how far they are opened (1 open, less swept back)
        self.head = head                # degrees the head turns (+ down/forward, - reared back)
        self.jaw = jaw                  # degrees the jaw drops
        self.tilt = tilt                # degrees the whole body tips (+ nose down)
        self.puff = puff                # px the chest swells (inhale)
        self.tail = tail                # whole px the tail tip swings (0 / 1 / -1)
        self.throat = throat            # 0..3: the throat's fire (glow)
        self.fire = fire                # 0..2: the burst in the mouth (glow)
        self.legs = legs                # whole px the legs tuck up


# --- shading -------------------------------------------------------------------------------------------------------------
def scaled(base, seed):
    """Dragon scales in the part's own space: a staggered lattice of small arcs, one shade down (stable, D4 rule 17)."""
    def fn(i):
        k = base(i)
        x, y = int(math.floor(i.lx)), int(math.floor(i.ly))
        row = y // 2
        if y % 2 == 0 and (x + (row % 2) * 2) % 4 == 0:
            k -= 1
        return max(1, k)
    return texture(fn, "speckle", seed=seed, density=0.04, lo=1, hi=5)


def body(mid, T, p):
    cx, cy, rx, ry = BODY
    inner = mid.part(T, Ellipse(cx, cy, rx + p.puff * 0.3, ry + p.puff), "crimson",
                     scaled(dome(cx - 3.0, cy - 3.6, 8.4, lo=1, hi=5, gain=1.35, bias=0.05, fixed=True, dither=0.22), 61), rust=0.0)
    bx, by, brx, bry = BELLY
    belly = mid.part(T, Ellipse(bx, by + p.puff * 0.4, brx, bry + p.puff * 0.6), "gilt", plates(bx, by, bry), rust=0.0, outline=False,
                     clip=inner)
    return inner, belly


def plates(bx, by, ry):
    """The belly's plates: gilt bands across it, dark seams between, lit at the top."""
    def fn(i):
        k = 6 if i.ly < by - 1.0 else 5
        if int(math.floor(i.ly - by + 20)) % 3 == 0:
            k = 3
        if i.ly > by + ry * 0.55:
            k -= 1
        return max(2, k)
    return fn


def tail(mid, T, p):
    pts = [(x, y + (p.tail if k == len(TAIL) - 1 else 0), r) for k, (x, y, r) in enumerate(TAIL)]
    caps = [Capsule((a[0], a[1]), (b[0], b[1]), a[2], b[2]) for a, b in zip(pts, pts[1:])]
    sx, sy = SPADE
    sy += p.tail
    caps.append(Poly([(sx - 1.6, sy + 1.2), (sx + 0.2, sy - 2.2), (sx + 2.6, sy + 0.2), (sx + 0.6, sy + 1.8)]))
    return mid.part(T, Union(*caps), "crimson", scaled(dome(12.0, -10.0, 9.0, lo=1, hi=4, gain=1.2, fixed=True, dither=0.2), 63),
                    rust=0.0)


def wing(cv, T, p, depth):
    """A bat wing at the shoulder: an arm bone to the wrist, three fingers fanning back from it, the membrane scalloped
    between their tips (ember, lit along the top), the bones dark crimson; it beats about its root."""
    off = FAR if depth else (0, 0)
    root = (SHOULDER[0] + off[0], SHOULDER[1] + off[1])
    W = T.then(Xf.pose(p.wing, root, (0.0, 0.0))).then(Xf(p.spread, 0.0, 0.0, 1.0, root[0] * (1 - p.spread), 0.0))
    rx, ry = root
    wrist = (rx + 5.0, ry - 7.6)
    tips = ((rx + 11.6, ry - 13.4), (rx + 16.4, ry - 7.0), (rx + 14.6, ry + 0.2))
    pts = [(rx - 1.2, ry + 0.8), (rx - 0.2, ry - 1.6), (wrist[0] - 0.6, wrist[1] - 0.8), tips[0], (rx + 11.0, ry - 9.0), tips[1],
           (rx + 12.6, ry - 4.0), tips[2], (rx + 9.0, ry - 0.8), (rx + 4.6, ry + 1.4)]
    bones = (((rx, ry), wrist, 0.8),) + tuple((wrist, t, 0.55) for t in tips)

    def near_bone(x, y):
        for a, b, w in bones:
            ax, ay = a
            bx, by = b
            dx, dy = bx - ax, by - ay
            ln2 = dx * dx + dy * dy or 1e-6
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / ln2))
            if math.hypot(x - (ax + dx * t), y - (ay + dy * t)) < w:
                return True
        return False

    def shade(i):
        if depth:
            return 1
        return 2 if i.ly < ry - 7.0 or near_bone(i.lx, i.ly + 1.0) else 1
    inner = cv.part(W, Poly(pts), "ember", shade, rust=0.0)
    for q in list(inner):                                # the bones in crimson over the membrane
        lx, ly = W.inv((q[0] + 0.5, q[1] + 0.5))
        if near_bone(lx, ly):
            cv.put(q[0], q[1], K[1] if depth else K[2])
    if depth == 0:                                       # a claw at the wrist
        c = P(W, (wrist[0] - 0.4, wrist[1] - 1.4))
        cv.put(c[0], c[1], IV[3])
    return inner


def leg(cv, T, key, p, depth):
    off = FAR if depth else (0, 0)
    hx, hy = HIPS[key]
    fx, fy = FEET[key]
    a = T.fwd((hx + off[0], hy + off[1]))
    b = T.fwd((fx + off[0], fy + off[1] - p.legs))
    limb(cv, a, b, 1.7 if key == "hind" else 1.45, "crimson", depth, lo=2, hi=4)
    if depth == 0:
        for k in (-1, 0, 1):                             # three ivory claws
            q = P(Xf(), (b[0] - 1.2 + k * 1.1, b[1] + 1.4))
            cv.put(q[0], q[1], IV[3] if k < 1 else IV[2])


def head(mid, far, T, p):
    Hx = T.then(Xf.pose(p.head, NECK, (0.0, 0.0)))
    # the far horn first, behind
    horn(far, Hx, (-4.4 + FAR[0], -20.6 + FAR[1]), 1)
    cx, cy, rx, ry = HEAD
    hinner = mid.part(Hx, Union(Ellipse(cx, cy, rx, ry), Ellipse(*SNOUT)), "crimson",
                      scaled(dome(cx - 2.6, cy - 2.8, 7.4, lo=1, hi=5, gain=1.4, bias=0.02, fixed=True, dither=0.22), 67), rust=0.0)
    J = Hx.then(Xf.pose(-p.jaw, JAW_PIVOT, (0.0, 0.0)))
    jaw = mid.part(J, Union(Capsule((-9.0, -12.2), (-15.6, -12.4), 1.9, 1.5)), "crimson",
                   dome(-12.0, -13.4, 5.0, lo=1, hi=3, gain=1.2, fixed=True), rust=0.0)
    horn(mid, Hx, (-4.4, -20.6), 0)
    return Hx, J, hinner, jaw


def horn(cv, Hx, base, depth):
    bx, by = base
    shape = Union(Capsule((bx, by + 1.0), (bx + 2.4, by - 2.6), 1.5, 0.7))
    cv.part(Hx, shape, "ivory", flat(2 if depth else 3, bevel=False), rust=0.0)


def spines(mid, T, inner):
    """Ivory spines down the back, over the body's top edge."""
    for (x, y) in ((-1.0, -17.0), (2.4, -17.4), (5.8, -16.4), (8.8, -14.4), (11.6, -11.2)):
        q = P(T, (x, y))
        mid.put(q[0], q[1], IV[3])
        mid.put(q[0], q[1] + 1, IV[2])


# --- a frame ---------------------------------------------------------------------------------------------------------------
def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    T = Xf.pose(p.tilt, (0.0, -11.0), (0.0, 0.0))
    # far: the far wing, the far legs
    wing(far, T, p, 1)
    for key in ("fore", "hind"):
        leg(far, T, key, p, 1)
    # middle: tail, body, head, jaw
    tail(mid, T, p)
    binner, belly = body(mid, T, p)
    spines(mid, T, binner)
    Hx, J, hinner, jaw = head(mid, far, T, p)
    # near: the legs, the wing
    for key in ("hind", "fore"):
        leg(near, T, key, p, 0)
    wing(near, T, p, 0)
    for cv in (far, mid, near):
        finish(cv)
    stamps(mid, glow, T, Hx, J, p, binner)
    return far, mid, near, glow, J.fwd(MOUTH)


def stamps(mid, glow, T, Hx, J, p, binner):
    """Under 3 px, after finish(): the eye, the nostril, the fang, the throat's fire, the burst in the mouth."""
    e = P(Hx, EYE)
    for (dx, dy, col) in ((0, 0, G[8]), (1, 0, G[7]), (0, 1, G[6]), (1, 1, G[6]), (0, -1, G[7]), (1, -1, K[1]), (-1, 0, K[1]),
                          (-1, 1, K[1])):
        mid.put(e[0] + dx, e[1] + dy, col)
    mid.put(e[0] + 1, e[1], K[0])                          # the slit pupil
    mid.put(e[0] + 1, e[1] + 1, K[0])
    mid.put(e[0], e[1] - 1, SM[3])                         # the glint
    for (dx, dy, col) in ((0, -1, G[8]), (0, 0, G[8]), (0, 1, G[6])):
        glow.put_glow(e[0] + dx, e[1] + dy, col)
    n = P(Hx, (-15.8, -16.0))                             # the nostril
    mid.put(n[0], n[1], K[0])
    f = P(J, (-13.4, -11.2))                              # a little fang over the jaw
    mid.put(f[0], f[1], IV[4])
    if p.throat:                                          # the throat's fire, brighter each inhale frame
        for k, (x, y) in enumerate(((-4.0, -11.6), (-3.0, -10.6), (-5.0, -10.6), (-4.0, -9.6), (-2.0, -11.6), (-6.0, -11.6))):
            if k >= p.throat * 2:
                break
            q = P(T, (x, y))
            col = (EM[3] if k < 2 else EM[2]) if p.throat >= 2 else EM[2]
            mid.put_glow(q[0], q[1], col)
            glow.put_glow(q[0], q[1], col)
    if p.fire:                                            # the burst at the mouth
        m = J.fwd(MOUTH)
        pts = ((0, 0, G[9]), (-1, 0, G[8]), (0, -1, EM[3]), (0, 1, EM[3]), (-2, 0, EM[3]), (-1, -1, EM[2]), (-1, 1, EM[2]))
        if p.fire >= 2:
            pts += ((-3, 0, EM[2]), (-2, -1, EM[2]), (-2, 1, EM[2]), (1, -1, EM[2]))
        for (dx, dy, col) in pts:
            x, y = int(math.floor(m[0])) + dx, int(math.floor(m[1])) + dy
            mid.put_glow(x, y, col)
            glow.put_glow(x, y, col)


# --- poses -------------------------------------------------------------------------------------------------------------------
BEAT = (-58.0, -30.0, 0.0, 26.0, 8.0, -30.0)
TAIL_SWING = (0, 0, 1, 1, 0, 0)
FRAMES = ([("Fly%d" % k, Pose(wing=w, tail=TAIL_SWING[k])) for k, w in enumerate(BEAT)]
          + [("Inhale0", Pose(wing=-20.0, head=-8.0, puff=0.5, throat=1)),
             ("Inhale1", Pose(wing=-24.0, head=-14.0, puff=1.0, throat=2)),
             ("Inhale2", Pose(wing=-26.0, head=-18.0, puff=1.0, throat=3))]
          + [("Spit0", Pose(wing=-10.0, head=10.0, jaw=26.0, fire=2)),
             ("Spit1", Pose(wing=0.0, head=6.0, jaw=18.0, fire=1)),
             ("Spit2", Pose(wing=-14.0, head=-2.0, jaw=6.0))]
          + [("Swoop0", Pose(wing=34.0, spread=0.72, tilt=-22.0, head=6.0, jaw=24.0, legs=1)),
             ("Swoop1", Pose(wing=26.0, spread=0.7, tilt=-22.0, head=6.0, jaw=26.0, legs=1))]
          + [("Bite0", Pose(wing=10.0, tilt=-12.0, head=8.0, jaw=34.0)),
             ("Bite1", Pose(wing=0.0, tilt=-8.0, head=12.0, jaw=0.0)),
             ("Bite2", Pose(wing=-20.0, tilt=-2.0, head=0.0, jaw=4.0))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- the fire bolt ------------------------------------------------------------------------------------------------------------
BOLT_ROWS = (
    ("........", "...ab...", "..abcb..", ".abccdba", ".abccdba", "..abcb..", "...ab...", "........"),
    ("........", "..ab....", ".abcb...", "abccdba.", "abccdcba", ".abcb...", "..ab....", "........"),
    ("........", "....ab..", "..abcba.", ".abcdcba", "abccdba.", "..abcb..", "...a....", "........"),
    ("........", "...ab...", ".aabcb..", "abccdba.", ".abccdba", "..abcb..", "....a...", "........"),
)


def bolt():
    """4 frames, 8x8 at 1x, pointing right (the way it flies): a white-gold heart, ember round it, flickering."""
    key = {"a": (EM, 1), "b": (EM, 2), "c": (EM, 3), "d": (G, 9)}
    frames = []
    for rows in BOLT_ROWS:
        px = pixkit.Pix(8, 8)
        px.rows(0, 0, rows, key)
        frames.append(px.image())
    return frames


# --- outputs -----------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Fly2"])
    return {"DragoneteMiudo_GoreHead": crop({q: c for q, c in mid.px.items() if q[0] <= -3 and q[1] <= -9}),
            "DragoneteMiudo_GoreWing": crop({q: c for q, c in near.px.items() if q[1] <= -9}),   # the wing, not the legs
            "DragoneteMiudo_GoreTail": crop({q: c for q, c in mid.px.items() if q[0] >= 9})}


def write_rig(path, cell, mouth):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/underworld/make_dragonete_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Underworld.NPCs",
         "{",
         "\t/// <summary>The Dragonete Miudo's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal",
         "\t/// cells with 2 px under each; the origin is the point under its middle. The mouth (in the first spit frame) is from",
         "\t/// the origin, facing left.</summary>",
         "\tpublic static class DragoneteMiudoRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Fly = 0, FlyFrames = %d, Inhale = %d, InhaleFrames = 3, Spit = %d, SpitFrames = 3;"
         % (len(BEAT), INDEX["Inhale0"], INDEX["Spit0"]),
         "\t\tpublic const int Swoop = %d, SwoopFrames = 2, Bite = %d, BiteFrames = 3;" % (INDEX["Swoop0"], INDEX["Bite0"]),
         "\t\tpublic const int MouthX = %d, MouthY = %d;" % (round(mouth[0] * 2), round(mouth[1] * 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/DragoneteMiudo%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/DragoneteMiudo_Glow.png")
    write_rig(OUT + "NPCs/DragoneteMiudoRigData.cs", cell, frames[INDEX["Spit0"]][4])
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")
    pixkit.export(pixkit.sheet(bolt()), OUT + "Projectiles/DragoneteFireBolt.png")


def preview(path, scale=4):
    cw, ch = 56, 44
    cols = 6
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (40, 22, 20, 255)), (1, (150, 170, 190, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
                t.alpha_composite(to_image(cv.px, -cw // 2, -ch + 6, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
