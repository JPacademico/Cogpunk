"""Source for the Mechromancer, a Blood Moon mini-boss (D4), its Soul Fire Cog, its floating eyes and its graves. Run from the
repo root:

    python -P art/bloodmoon/make_mechromancer_art.py [--preview FILE] [--frames Float0,Cast3,...]

v2, 2026-11-16 (user: "rework its design based on the image example ... ensure terraria/metal slug quality pixel art", a
painting of a hooded, ram-horned sorcerer in a dark, gilt-patterned robe, a bony mask in the hood's shadow, clawed hands
raised in green fire and green eyeballs floating round him). The v1 generator (a brass skull with a soul flame for a head,
a ribcage, a staff) is art/bloodmoon/previous/make_mechromancer_art_v1_2026-11-12.py.

The robot necromancer, redrawn in Cogpunk's materials (my calls on the details): a deep hood of oak-brown cloth trimmed in
gilt, a brass skull for a face in its shadow with soul-fire eyes, ram horns of old ivory ringed with brass bands curling
out of the hood; a high collar, brass pauldrons with ivory spikes, a long robe (oak, a crimson lining showing at the sleeves'
mouths) with a gilt-bordered tabard down its front where three soul runes burn, a gilt belt with a cog buckle, a hem torn
into tatters (it floats: no legs); wide bell sleeves over brass gauntlets with three claws each, soul fire in the claws. Its
floating eyes are separate sprites (brass-bezelled glass eyes with ghost-green irises) that the game draws orbiting it,
looking at its target (Mechromancer_Eye, nine pupil frames).

Three-quarter view facing left (D4 rule 13), the torso facing the screen (2026-11-06: collar, tabard, belt and buckle on its
axis), lit from the top-left. Three planes (DepthLayers.DrawWalker grid sheets): far (the far arm and the far horn, one ramp
step darker), middle (the robe, the hood, the skull, the near horn), near (the near arm); the glow sheet holds the eyes, the
runes and the soul fire. Stable pixels (D4 rule 17): the body is lit in its own space and never moves; only the tatters,
the sleeves' bells and the arms move, the tatters by whole pixels; the float's bob is in code.

Frames (smooth in-betweens, user 2026-11-16: "ensure ... smooth frame animation"): Float x6 (the tatters sway, the bells
swing, the claws flex), Cast x6 (the near arm rises in two steps, held flaring for the telegraph in two flickers, thrust at
the target: the volley, follow-through), Summon x6 (both arms rise in two steps, held high in two flickers: the telegraph,
swept down: the dead rise, settle).

Outputs (1x art exported 2x nearest-neighbour):
    Content/BloodMoon/NPCs/Mechromancer.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/BloodMoon/NPCs/Mechromancer_Eye.png, _EyeGlow.png                  the floating eyes, 9 pupil frames
    Content/BloodMoon/NPCs/MechromancerRigData.cs        cells, origin, frames, the hand's fire (where cogs leave), the head
    Content/BloodMoon/Projectiles/SoulFireCog.png, _Glow.png
    Content/BloodMoon/Projectiles/MechromancerGrave.png, _Glow.png   the summon's mark on the ground, 4 flickers
    Content/BloodMoon/Gores/Mechromancer_GoreSkull.png, _GoreHorn.png, _GoreClaw.png
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
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, face, P, finish, limb, texture)  # noqa: E402
from rig import ik  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/BloodMoon/"
GH, G, OK, IV, ST, K = (RAMP[k] for k in ("ghost", "gilt", "oak", "ivory", "steel", "crimson"))

CX = 0.0                                   # the torso's axis
WAIST_Y = -17.0
COLLAR_Y = -30.0
SH_NEAR, SH_FAR = (CX - 8.0, -27.6), (CX + 8.0, -27.6)
UPPER, FORE = 6.2, 6.4
HOOD_C = (CX - 0.6, -37.6)                 # the hood's face opening, centre


class Pose:
    def __init__(self, tails=0, bells=0, near=(-18.2, -33.6), far=(17.6, -34.0), claw=1, fire=1, far_fire=1, roar=0, eyes=1):
        self.tails = tails                 # -1 / 0 / 1: the hem's tatters swing (whole pixels)
        self.bells = bells                 # -1 / 0 / 1: the sleeves' drapes swing
        self.near = near                   # the near hand (rig space)
        self.far = far                     # the far hand
        self.claw = claw                   # 0 curled .. 2 spread
        self.fire = fire                   # 0..3: the near claw's soul fire (3: the volley leaves)
        self.far_fire = far_fire           # 0..3: the far claw's
        self.roar = roar                   # 0..2: the summon: soul fire in both claws, the hood's eyes blaze
        self.eyes = eyes                   # 0..2: the skull's eyes


# --- the robe ---------------------------------------------------------------------------------------------------------------
def robe(mid, glow, p):
    """Oak cloth from the shoulders flaring to a hem torn into tatters, dark in the folds; its front open from the belt
    down over a crimson under-robe with three small soul runes, the opening edged with gilt filigree bands; a filigree
    border along the hem; a gilt belt with a cog buckle on the axis."""
    t = p.tails
    hem = [(-13.0, -2.6), (-11.8 + t * 0.6, 0.2), (-10.0, -2.2), (-8.0 + t, 0.6), (-5.8, -1.8), (-3.4 + t, 0.8), (-1.0, -1.6),
           (1.4 + t, 0.8), (3.6, -1.8), (6.0 + t, 0.6), (8.2, -2.0), (10.4 + t * 0.6, 0.2), (12.4, -2.6)]
    shape = Poly([(CX - 8.6, COLLAR_Y + 1.0), (CX + 8.6, COLLAR_Y + 1.0), (CX + 7.8, -22.0), (CX + 7.0, WAIST_Y), (CX + 10.2, -9.0),
                  (CX + 12.6, -3.0)] + hem[::-1] + [(CX - 13.0, -3.0), (CX - 10.6, -9.0), (CX - 7.2, WAIST_Y), (CX - 8.0, -22.0)])
    shade = texture(face((-0.45, -0.3, 0.84), lo=1, hi=3, ramp_len=6, gain=1.6, bias=-0.02, fixed=True, dither=0.18), "weave", seed=23)
    inner = mid.part(Xf(), shape, "oak", shade, shadow=(1, 1), rust=0.0)
    # folds: long creases down the skirt, a shade down with a lit edge on their left (subtle, in the cloth's own ramp)
    for (x0, x1) in ((-6.2, -9.6), (-4.6, -6.4), (5.0, 7.4), (6.4, 9.8)):
        for y in range(int(WAIST_Y) + 3, -4):
            f = (y - WAIST_Y) / -WAIST_Y
            x = int(math.floor(x0 + (x1 - x0) * f))
            if (x, y) in inner and (x, y + 1) in inner and mid.px.get((x, y)) not in (OK[0],):
                mid.put(x, y, OK[1])
                if (x - 1, y) in inner:
                    mid.put(x - 1, y, OK[3] if x < CX else OK[2])
    # the open front: the crimson under-robe between two gilt filigree bands, widening to the hem
    for y in range(int(WAIST_Y) + 1, 0):
        f = (y - WAIST_Y) / -WAIST_Y
        half = 1.6 + 2.2 * f
        for x in range(int(math.floor(CX - half - 1.6)), int(math.ceil(CX + half + 1.6)) + 1):
            q = (x, y)
            if q not in inner:
                continue
            d = x + 0.5 - CX
            if abs(d) < half:
                mid.put(x, y, K[1] if (x + 2 * y) % 5 else K[2])
            elif abs(d) < half + 1.6:
                left = d < 0
                mid.put(x, y, (G[7] if (y % 3) else G[5]) if left else (G[5] if (y % 3) else G[3]))
    runes = (((0, -13), (-1, -12), (1, -12), (0, -11)),
             ((-1, -9), (1, -9), (0, -8), (0, -7)),
             ((0, -5), (-1, -4), (1, -4)))
    for k, rune in enumerate(runes):
        for (x, y) in rune:
            col = GH[4] if (x == 0) else GH[3]
            mid.put_glow(x, y, col)
            glow.put_glow(x, y, col)
    # the hem's filigree border: a gilt band two rows deep over the tatters' roots, a key pattern on its top row
    for x in range(-13, 13):
        for y, k in ((-5, 6), (-4, 3)):
            q = (x, y)
            if q in inner and abs(x + 0.5 - CX) >= 4.0:
                kk = k + (1 if x < -3 else 0) - (1 if x > 5 else 0)
                if y == -5 and x % 3 == 0:
                    kk -= 3
                mid.put(x, y, G[max(1, min(8, kk))])
    # the belt: a gilt band, its buckle a little cog with a soul-fire eye
    for x in range(-8, 8):
        for (y, k) in ((int(WAIST_Y) - 1, 7), (int(WAIST_Y), 4)):
            if (x, y) in inner or (x, y) in mid.px:
                mid.put(x, y, G[k + (1 if x < -2 else 0)])
    for (dx, dy, col) in ((-1, -1, G[8]), (0, -1, G[7]), (1, -1, G[6]), (-2, 0, G[7]), (2, 0, G[4]), (-1, 1, G[5]), (0, 1, G[4]),
                          (1, 1, G[3]), (-2, -1, G[1]), (2, 1, G[1]), (-1, 0, G[2]), (1, 0, G[2])):
        mid.put(int(CX) + dx, int(WAIST_Y) + dy, col)
    mid.put_glow(int(CX), int(WAIST_Y), GH[5])
    glow.put_glow(int(CX), int(WAIST_Y), GH[5])
    return inner


def chest(mid, p):
    """The robe's breast between the shoulders: oak with a gilt V collar on the axis; brass pauldrons with ivory spikes."""
    breast = Poly([(CX - 8.8, COLLAR_Y), (CX + 8.8, COLLAR_Y), (CX + 7.8, WAIST_Y - 1.0), (CX - 7.8, WAIST_Y - 1.0)])
    inner = mid.part(Xf(), breast, "oak", texture(face((-0.4, -0.5, 0.78), lo=1, hi=3, ramp_len=6, gain=1.5, fixed=True, dither=0.14),
                                                   "weave", seed=29), rust=0.0)
    for k in range(9):                                         # the V collar: two gilt bands meeting on the axis
        y = int(COLLAR_Y) + 1 + k
        for side in (-1, 1):
            x = int(math.floor(CX + side * (5.5 - k * 0.6)))
            for w in range(2):
                q = (x + (w if side > 0 else -w), y)
                if q in inner:
                    mid.put(q[0], q[1], G[7 - w * 2] if side < 0 else G[5 - w * 2])
    for y in range(int(COLLAR_Y) + 1, int(COLLAR_Y) + 9):      # the dark under-tunic in the V
        for x in range(-2, 2):
            w = 4.6 - (y - COLLAR_Y) * 0.55
            if abs(x + 0.5 - CX) < w - 0.8 and (x, y) in inner:
                mid.put(x, y, K[1] if (x + y) % 4 else K[2])
    for (cx, side) in ((CX - 9.0, -1), (CX + 9.0, 1)):         # the pauldrons
        lit_hi = 8 if side < 0 else 6
        pd = mid.part(Xf(), Ellipse(cx, COLLAR_Y + 1.6, 4.0, 3.2), "gilt",
                      dome(cx - 1.6, COLLAR_Y + 0.2, 4.6, lo=2, hi=lit_hi, gain=1.4, fixed=True), shadow=(1, 1), rust=0.0)
        for k in range(3):                                     # its riveted rim
            q = P(Xf(), (cx - 2.4 + k * 2.4, COLLAR_Y + 3.6))
            if q in pd:
                mid.put(q[0], q[1], G[1])
        spike = Poly([(cx - 1.4 + side * 0.4, COLLAR_Y - 0.6), (cx + 1.2 + side * 0.4, COLLAR_Y - 0.6), (cx + side * 2.6, COLLAR_Y - 6.4)])
        mid.part(Xf(), spike, "ivory", face((-0.6, -0.5, 0.6), lo=2, hi=5, ramp_len=6, fixed=True), rust=0.0)
    return inner


# --- the hood, the skull, the horns ---------------------------------------------------------------------------------------
def hood(mid, p):
    """A deep pointed hood (its tip draping back), gilt trim round the face opening, the opening's shadow (the skull goes
    in it). Returns the opening's pixels."""
    hx, hy = HOOD_C
    outer = Poly([(hx - 7.4, hy + 7.4), (hx - 7.8, hy - 1.0), (hx - 5.4, hy - 7.0), (hx - 1.0, hy - 10.0), (hx + 4.0, hy - 10.6),
                  (hx + 7.6, hy - 9.0), (hx + 6.6, hy - 6.8), (hx + 7.8, hy - 1.6), (hx + 8.0, hy + 7.4)])
    inner = mid.part(Xf(), outer, "oak", texture(dome(hx - 3.0, hy - 6.0, 11.0, lo=1, hi=4, gain=1.4, fixed=True, dither=0.16),
                                                  "weave", seed=37), shadow=(1, 1), rust=0.0)
    opening = Ellipse(hx - 0.4, hy + 0.6, 5.0, 6.4)
    hole = set()
    for q in list(inner):
        if opening.inside(q[0] + 0.5, q[1] + 0.5):
            hole.add(q)
    for q in hole:
        mid.put(q[0], q[1], ST[0] if q[1] < hy - 2 else ST[1])
    for q in list(inner):                                      # the gilt trim round the opening
        if q in hole:
            continue
        if any((q[0] + dx, q[1] + dy) in hole for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            mid.put(q[0], q[1], G[7] if q[0] < hx - 1 or q[1] < hy - 4 else G[4])
    for k in range(5):                                         # a fold down the hood's crown
        q = (int(hx + 1.6 + k * 0.5), int(hy - 9.0 + k))
        if q in inner and q not in hole:
            mid.put(q[0], q[1], OK[1])
            if (q[0] - 1, q[1]) in inner and (q[0] - 1, q[1]) not in hole:
                mid.put(q[0] - 1, q[1], OK[4])
    return hole


# The skull in the hood, placed by hand (8 px wide): three-quarters to the left, the brow, the sockets (the near one bigger)
# with soul-fire eyes, the nose's hole, cheekbones, two rows of brass teeth.
SKULL = ("..2343..",
         ".356764.",
         "35776653",
         "3600603.",
         "35565443",
         ".356543.",
         ".2a8a7a.",
         "..1b1b1.",
         "...2a2..")
SKULL_AT = (-5, -42)


def skull(mid, glow, p):
    x0, y0 = int(HOOD_C[0]) + SKULL_AT[0] + 1, SKULL_AT[1] + 2
    for dy, row in enumerate(SKULL):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + dx, y0 + dy
            if ch == "0":
                mid.put(x, y, ST[0])
            elif ch == "a":
                mid.put(x, y, G[8])
            elif ch == "b":
                mid.put(x, y, G[6])
            else:
                mid.put(x, y, G[int(ch)])
    eyes = ((x0 + 1, y0 + 3), (x0 + 2, y0 + 3), (x0 + 5, y0 + 3))
    for k, (x, y) in enumerate(eyes):
        col = (GH[3], GH[4], GH[5])[min(2, p.eyes + (1 if k == 0 else 0))]
        mid.put_glow(x, y, col)
        glow.put_glow(x, y, col)
    if p.roar or p.eyes >= 2:                                   # the eyes blaze: a lick of soul fire off the near socket
        for (x, y, col) in ((x0, y0 + 2, GH[3]), (x0 - 1, y0 + 2, GH[2]), (x0 + 1, y0 + 2, GH[4])):
            mid.put_glow(x, y, col)
            glow.put_glow(x, y, col)


def horn(cv, root, side, depth):
    """A ram horn of old ivory curling out of the hood: up and out from `root`, round and down past the cheek, thinning to
    its tip; one silhouette (a union of tube segments, outlined once), lit from the top-left in its own space, ringed by
    dark ridges each with a lit lip, a brass band near the root. side -1 curls to the left (the near horn), +1 right."""
    pts, radii = [], []
    for k in range(13):
        a = math.radians(-120 + k * 24.0)                      # from up-and-in, round outwards, down, and in again
        r = 4.6 - k * 0.15
        cx, cy = root[0] + side * 3.4, root[1] + 0.4
        pts.append((cx + side * math.cos(a + math.pi) * -r, cy + math.sin(a) * r))
        radii.append(2.7 - k * 0.12)
    shape = Union(*[Capsule(pts[k], pts[k + 1], radii[k], radii[k + 1]) for k in range(len(pts) - 1)])
    if depth > 0:
        painted = cv.part(Xf(), shape, "ivory", flat(2, bevel=False), rust=0.0)
    else:
        painted = cv.part(Xf(), shape, "ivory", face((-0.5, -0.6, 0.62), lo=2, hi=4, ramp_len=6, gain=1.0, bevel=True, fixed=True), rust=0.0)
    for k in range(2, len(pts) - 1, 2):                        # the ridges across the tube
        a = pts[k]
        b = pts[k + 1] if k + 1 < len(pts) else pts[k]
        d = (b[0] - a[0], b[1] - a[1])
        ln = math.hypot(*d) or 1.0
        n = (-d[1] / ln, d[0] / ln)
        for s in (-1.0, 0.0, 1.0):
            q = P(Xf(), (a[0] + n[0] * s * radii[k] * 0.8, a[1] + n[1] * s * radii[k] * 0.8))
            if q in painted:
                cv.put(q[0], q[1], IV[1] if depth == 0 else IV[0])
    if depth == 0:
        q = P(Xf(), pts[1])                                    # the brass band near the root
        for (dx, dy, col) in ((0, 0, G[7]), (1, 0, G[5]), (0, 1, G[4]), (-1, 0, G[6]), (0, -1, G[8])):
            if (q[0] + dx, q[1] + dy) in painted:
                cv.put(q[0] + dx, q[1] + dy, col)
    return painted


# --- the arms ---------------------------------------------------------------------------------------------------------------
def claws(cv, glow, hand, u, spread, depth, fire):
    """Three brass claws past the gauntlet's knuckles, along the forearm's direction, fanned by `spread` (0..2), each two
    pixels thick at its root and pointed; soul fire licking round them (fire 1..3). Returns the fire's centre."""
    base = math.atan2(u[1], u[0])
    fan = (0.22, 0.4, 0.62)[max(0, min(2, spread))]
    tip_r = 4.2
    for k in (-1, 0, 1):
        a = base + k * fan
        tip = (hand[0] + math.cos(a) * tip_r, hand[1] + math.sin(a) * tip_r)
        root = (hand[0] + math.cos(a) * 1.4, hand[1] + math.sin(a) * 1.4)
        if depth > 0:
            cv.part(Xf(), Capsule(root, tip, 0.9, 0.3), "gilt", flat(3, bevel=False), rust=0.0)
        else:
            cv.part(Xf(), Capsule(root, tip, 0.95, 0.3), "gilt", face((-0.6, -0.6, 0.5), lo=3, hi=8, ramp_len=10, fixed=True), rust=0.0)
    c = (hand[0] + math.cos(base) * (3.4 + fire * 0.5), hand[1] + math.sin(base) * (3.4 + fire * 0.5))
    if fire:
        rad = (1.2, 2.0, 2.8, 3.5)[min(3, fire)]
        for y in range(int(c[1] - rad - 1), int(c[1] + rad + 2)):
            for x in range(int(c[0] - rad - 1), int(c[0] + rad + 2)):
                d = math.hypot(x + 0.5 - c[0], y + 0.5 - c[1])
                if d <= rad and (x, y) not in cv.px:
                    col = GH[5] if d < rad * 0.35 else GH[4] if d < rad * 0.7 else GH[3]
                    cv.put_glow(x, y, col)
                    glow.put_glow(x, y, col)
    return c


def arm(cv, glow, shoulder, hand, depth, bells, spread, fire, bend, side):
    """A bell sleeve of oak cloth over the whole arm, thick at the shoulder and flaring at the wrist, its mouth lined in
    crimson under a gilt cuff band, its lower edge sagging a pixel or two with `bells` (gravity); the brass gauntlet's
    fist out of the mouth and three claws. side -1: the near arm, +1 the far one. Returns the soul fire's centre."""
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, bend)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    mouth = (wrist[0] - u[0] * 0.8, wrist[1] - u[1] * 0.8 + abs(bells) * 0.4)
    sleeve = Union(Capsule(shoulder, elbow, 3.1, 2.9), Capsule(elbow, mouth, 2.9, 3.9))
    if depth > 0:
        inner = cv.part(Xf(), sleeve, "oak", flat(1, bevel=False), rust=0.0)
    else:
        inner = cv.part(Xf(), sleeve, "oak", texture(face((-0.45, -0.3, 0.84), lo=1, hi=4, ramp_len=6, gain=1.6, bias=0.05, fixed=True,
                                                          dither=0.16), "weave", seed=41), shadow=(1, 1), rust=0.0)
    full = set(inner) | {q for q in cv.raster(Xf(), sleeve)}
    for q in full:                                             # the mouth: crimson lining, a gilt cuff band behind it
        t = ((q[0] + 0.5 - elbow[0]) * u[0] + (q[1] + 0.5 - elbow[1]) * u[1]) / max(1e-6, math.hypot(mouth[0] - elbow[0], mouth[1] - elbow[1]))
        if q not in inner:
            continue
        if t > 0.86:
            cv.put(q[0], q[1], K[2] if depth == 0 else K[1])
        elif t > 0.7:
            cv.put(q[0], q[1], (G[7] if (q[0] + q[1]) % 2 else G[6]) if depth == 0 else G[3])
    if depth == 0:                                             # a long fold down the sleeve
        for k in range(1, 5):
            f = 0.15 + k * 0.12
            q = P(Xf(), (elbow[0] + (mouth[0] - elbow[0]) * f - u[1] * side * 1.2, elbow[1] + (mouth[1] - elbow[1]) * f + u[0] * side * 1.2))
            if q in inner:
                cv.put(q[0], q[1], OK[1])
    hand_c = (wrist[0] + u[0] * 1.2, wrist[1] + u[1] * 1.2)
    if depth > 0:
        cv.part(Xf(), Ellipse(hand_c[0], hand_c[1], 2.0, 1.9), "gilt", flat(3, bevel=False), rust=0.0)
    else:
        fist = cv.part(Xf(), Ellipse(hand_c[0], hand_c[1], 2.2, 2.0), "gilt", dome(hand_c[0] - 0.8, hand_c[1] - 0.8, 2.8, lo=3, hi=8, fixed=True),
                       rust=0.0)
        r = P(Xf(), (hand_c[0] + u[0] * 0.6, hand_c[1] + u[1] * 0.6))   # a knuckle rivet
        if r in fist:
            cv.put(r[0], r[1], G[1])
    return claws(cv, glow, hand_c, u, spread, depth, fire)


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    roar_fire = (0, 1, 2)[p.roar]
    arm(far, glow, SH_FAR, p.far, 1, p.bells, p.claw, max(p.far_fire, roar_fire), bend=-1, side=1)
    horn(far, (HOOD_C[0] + 6.6, HOOD_C[1] - 4.6), 1, 1)
    robe(mid, glow, p)
    chest(mid, p)
    hood(mid, p)
    skull(mid, glow, p)
    horn(mid, (HOOD_C[0] - 6.2, HOOD_C[1] - 4.8), -1, 0)
    fire = arm(near, glow, SH_NEAR, p.near, 0, p.bells, p.claw, max(p.fire, roar_fire), bend=1, side=-1)
    for cv in (far, mid, near):
        finish(cv)
    return far, mid, near, glow, fire


FLOAT_TAILS = (0, 1, 1, 0, -1, -1)
FLOAT_BELLS = (0, 0, 1, 1, 0, -1)
FLOAT_FIRE = (1, 1, 2, 1, 1, 0)                                 # the palms' soul fire breathes
FRAMES = ([("Float%d" % k, Pose(tails=FLOAT_TAILS[k], bells=FLOAT_BELLS[k], claw=(1, 1, 2, 2, 1, 1)[k], fire=FLOAT_FIRE[k],
                                far_fire=FLOAT_FIRE[(k + 3) % 6], eyes=(1, 1, 1, 2, 1, 1)[k])) for k in range(6)]
          + [("Cast0", Pose(tails=1, bells=0, near=(-17.2, -38.0), claw=1, fire=1)),
             ("Cast1", Pose(tails=1, bells=-1, near=(-15.8, -42.4), claw=2, fire=2, eyes=2)),
             ("Cast2", Pose(tails=0, bells=-1, near=(-15.2, -43.4), claw=2, fire=3, eyes=2)),
             ("Cast3", Pose(tails=-1, bells=-1, near=(-15.4, -43.2), claw=2, fire=2, eyes=2)),
             ("Cast4", Pose(tails=-1, bells=1, near=(-21.0, -31.4), claw=2, fire=3, eyes=2)),
             ("Cast5", Pose(tails=0, bells=1, near=(-19.6, -32.6), claw=1, fire=1))]
          + [("Summon0", Pose(tails=0, bells=0, near=(-16.6, -39.4), far=(16.0, -40.0), claw=1, roar=1)),
             ("Summon1", Pose(tails=1, bells=-1, near=(-14.6, -44.2), far=(14.0, -44.8), claw=2, roar=2, eyes=2)),
             ("Summon2", Pose(tails=1, bells=-1, near=(-14.2, -45.0), far=(13.6, -45.6), claw=2, roar=2, eyes=2)),
             ("Summon3", Pose(tails=0, bells=-1, near=(-14.4, -44.6), far=(13.8, -45.2), claw=2, roar=2, eyes=2)),
             ("Summon4", Pose(tails=-1, bells=1, near=(-19.8, -24.6), far=(19.2, -25.0), claw=2, roar=1)),
             ("Summon5", Pose(tails=0, bells=0, near=(-19.0, -30.2), far=(18.4, -30.6), claw=1))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- the floating eyes ------------------------------------------------------------------------------------------------------
EYE = 7
EYE_DIRS = [(0, 0), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def floating_eye(k):
    """A brass-bezelled glass eye, 7 px: the bezel (gilt, lit top-left), the white (ivory), a ghost-green iris round a black
    pupil that looks one pixel towards EYE_DIRS[k], a glint up-left. The iris also goes on the glow canvas."""
    cv, glow = Canvas(), Canvas()
    c = EYE / 2.0
    for y in range(EYE):
        for x in range(EYE):
            r = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if r > 3.5:
                continue
            if r > 2.6:
                light = -((x + 0.5 - c) * 0.6 + (y + 0.5 - c) * 0.8) / max(0.8, r)
                cv.put(x, y, G[0] if r > 3.2 and light < 0.2 else G[max(3, min(8, 5 + int(round(light * 3))))])
            else:
                cv.put(x, y, IV[4] if (x + y) < 6 else IV[3])
    dx, dy = EYE_DIRS[k]
    ix, iy = 3 + dx, 3 + dy
    for (ox, oy) in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        q = (ix + ox, iy + oy)
        if q in cv.px and math.hypot(q[0] + 0.5 - c, q[1] + 0.5 - c) <= 2.6:
            col = GH[4] if oy < 0 or ox < 0 else GH[3]
            cv.put_glow(q[0], q[1], col)
            glow.put_glow(q[0], q[1], col)
    cv.put(ix, iy, ST[0])
    cv.glow.pop((ix, iy), None)
    g = (2, 2) if (dx, dy) != (-1, -1) else (3, 2)
    if g != (ix, iy):
        cv.put(g[0], g[1], IV[5])
        cv.glow.pop(g, None)
        glow.glow.pop(g, None)
    return cv, glow


# --- the Soul Fire Cog ------------------------------------------------------------------------------------------------------
def soul_cog(rot, size=14):
    """A brass 8-tooth cog (radius 3.7 + 1.3 teeth) with a soul-fire hub, wreathed in a ring of soul fire (glow)."""
    cv, glow = Canvas(), Canvas()
    c = (size / 2.0, size / 2.0)
    for y in range(size):
        for x in range(size):
            du, dv = x + 0.5 - c[0], y + 0.5 - c[1]
            r = math.hypot(du, dv)
            th = math.degrees(math.atan2(dv, du)) - rot
            tooth = math.cos(math.radians(th * 8)) > 0.2
            outer = 3.7 + (1.3 if tooth else 0.0)
            if r <= outer:
                if r < 1.4:
                    cv.put_glow(x, y, GH[5] if r < 0.8 else GH[4])
                    glow.put_glow(x, y, GH[5] if r < 0.8 else GH[4])
                    continue
                light = -(du * 0.62 + dv * 0.78) / max(0.8, r)
                col = G[1] if r > outer - 0.8 or (1.4 <= r < 2.0) else G[max(3, min(8, 5 + int(round(light * 2.6))))]
                cv.put(x, y, col)
            elif r <= outer + 1.3 and r < size / 2.0:
                k = 3 if (int(th // 22.5) % 2 == 0) else 2
                glow.put_glow(x, y, GH[k])
    return cv, glow


COG_FRAMES = 4                                                 # 45-degree symmetry / 4 = 11.25 degrees a frame


# --- the grave mark (the summon's telegraph, where a zombie will climb out) -----------------------------------------------
GRAVE_W, GRAVE_H, GRAVE_FRAMES = 22, 10, 4


def grave(k):
    """A ring of soul fire burnt flat into the ground round a cracked, dark patch with a cog's sign in it; flames lick up
    from the ring, a different few each frame (bottom row = the ground line)."""
    cv, glow = Canvas(), Canvas()
    cx, cy, rx, ry = GRAVE_W / 2.0, GRAVE_H - 2.5, 9.6, 2.4
    for y in range(GRAVE_H):
        for x in range(GRAVE_W):
            r = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if r > 1.0:
                continue
            if r > 0.72:
                c = GH[4] if y + 0.5 < cy else GH[3]
                cv.put_glow(x, y, c)
                glow.put_glow(x, y, c)
            else:
                cv.put(x, y, OK[0] if r < 0.45 else OK[1])
    for (x, y) in ((10, 7), (11, 7), (9, 7), (12, 7), (10, 6), (11, 8), (8, 8), (13, 6)):
        if (x, y) in cv.px and (x, y) not in cv.glow:
            cv.put_glow(x, y, GH[2])
            glow.put_glow(x, y, GH[2])
    tongues = ((2, 3, 5, 1), (4, 2, 7, 2), (6, 4, 4, 3), (5, 3, 6, 2))[k]
    for i, xx in enumerate((3 + (k % 2), 7 + k, 13 - k, 17 + (k % 2))):
        h = tongues[i]
        for dy in range(h):
            y = int(cy - ry) - 1 - dy
            c = GH[4] if dy == 0 else GH[3] if dy < h - 1 else GH[2]
            if 0 <= y < GRAVE_H:
                cv.put_glow(xx, y, c)
                glow.put_glow(xx, y, c)
    return cv, glow


# --- outputs -------------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Float0"])
    hx, hy = HOOD_C
    return {"Mechromancer_GoreSkull": crop({q: c for q, c in mid.px.items() if abs(q[0] - hx) <= 5 and hy - 6 <= q[1] <= hy + 6
                                             and q not in mid.glow}),
            "Mechromancer_GoreHorn": crop({q: c for q, c in mid.px.items() if q[0] <= hx - 6 and hy - 11 <= q[1] <= hy - 1
                                           and c in RAMP["ivory"] + RAMP["gilt"]}),
            "Mechromancer_GoreClaw": crop({q: c for q, c in near.px.items() if q[1] <= -29})}


def write_rig(path, cell, fires):
    w, h, ox, oy = cell
    fx = ", ".join("%d" % round(f[0] * 2) for f in fires)
    fy = ", ".join("%d" % round(f[1] * 2) for f in fires)
    L = ["// <auto-generated> by art/bloodmoon/make_mechromancer_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.BloodMoon.NPCs",
         "{",
         "\t/// <summary>The Mechromancer's grid sheets (game px, facing left): far, middle, near and glow, equal cells with 2 px",
         "\t/// under each; the origin is the bottom of the robe's hem. FireX/FireY: the near claw's soul fire in each frame (from the",
         "\t/// origin, facing left), where its Soul Fire Cogs leave. Head: the hood's face (the floating eyes orbit round it).",
         "\t/// Eye: the floating eyes' cells (9 pupil frames, the pupil towards each heading's eighth: 0 still, 1 right, then",
         "\t/// clockwise on screen).</summary>",
         "\tpublic static class MechromancerRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Float = %d, FloatFrames = 6, Cast = %d, CastFrames = 6, Summon = %d, SummonFrames = 6;" % (
             INDEX["Float0"], INDEX["Cast0"], INDEX["Summon0"]),
         "\t\tpublic const int HeadX = %d, HeadY = %d, EyeCell = %d, EyeFrames = %d;" % (round(HOOD_C[0] * 2), round(HOOD_C[1] * 2), EYE * 2, len(EYE_DIRS)),
         "\t\tpublic static readonly int[] FireX = { %s };" % fx,
         "\t\tpublic static readonly int[] FireY = { %s };" % fy,
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def vertical(canvases, size, glow=False):
    im = Image.new("RGBA", (size, (size + 1) * len(canvases) - 1), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        for (x, y), col in src.items():
            if 0 <= x < size and 0 <= y < size:
                im.putpixel((x, y + k * (size + 1)), col + (255,))
    return im


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Mechromancer%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Mechromancer_Glow.png")
    write_rig(OUT + "NPCs/MechromancerRigData.cs", cell, [fr[4] for fr in frames])
    eyes = [floating_eye(k) for k in range(len(EYE_DIRS))]
    export(vertical([e[0] for e in eyes], EYE), OUT + "NPCs/Mechromancer_Eye.png")
    export(vertical([e[1] for e in eyes], EYE, glow=True), OUT + "NPCs/Mechromancer_EyeGlow.png")
    cogs = [soul_cog(k * 45.0 / COG_FRAMES) for k in range(COG_FRAMES)]
    size = 14
    for name, idx in (("SoulFireCog", 0), ("SoulFireCog_Glow", 1)):
        im = Image.new("RGBA", (size, size * COG_FRAMES), (0, 0, 0, 0))
        for k, pair in enumerate(cogs):
            src = pair[idx].glow if idx == 1 else pair[idx].px
            for (x, y), col in src.items():
                im.putpixel((x, y + k * size), col + (255,))
        export(im, OUT + "Projectiles/%s.png" % name)
    graves = [grave(k) for k in range(GRAVE_FRAMES)]
    for name, idx in (("MechromancerGrave", 0), ("MechromancerGrave_Glow", 1)):
        im = Image.new("RGBA", (GRAVE_W, GRAVE_H * GRAVE_FRAMES), (0, 0, 0, 0))
        for k, pair in enumerate(graves):
            src = pair[idx].glow if idx == 1 else pair[idx].px
            for (x, y), col in src.items():
                im.putpixel((x, y + k * GRAVE_H), col + (255,))
        export(im, OUT + "Projectiles/%s.png" % name)
    for old in ("Mechromancer_GoreRibs", "Mechromancer_GoreStaff"):
        path = os.path.join(ROOT, OUT + "Gores/%s.png" % old)
        if os.path.exists(path):
            os.remove(path)
            print("removed", OUT + "Gores/%s.png" % old)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=5, names=None, bg=(48, 18, 24)):
    names = names or [n for n, _ in FRAMES]
    cw, ch = 50, 62
    cols = min(6, len(names))
    rws = (len(names) + cols - 1) // cols
    lookup = dict(FRAMES)
    sheet = Image.new("RGBA", (cw * cols, ch * rws), bg + (255,))
    for k, n in enumerate(names):
        far, mid, near, glow, _ = frame(lookup[n])
        t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cvs in (far, mid, near):
            t.alpha_composite(to_image(cvs.px, -cw // 2, -ch + 4, cw, ch))
        sheet.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
    eyes = [floating_eye(k)[0] for k in range(len(EYE_DIRS))]
    strip = Image.new("RGBA", (len(eyes) * (EYE + 2), EYE + 2), bg + (255,))
    for k, e in enumerate(eyes):
        strip.alpha_composite(to_image(e.px, 0, 0, EYE, EYE), (k * (EYE + 2) + 1, 1))
    out = Image.new("RGBA", (max(sheet.width, strip.width), sheet.height + strip.height), bg + (255,))
    out.alpha_composite(sheet, (0, 0))
    out.alpha_composite(strip, (0, sheet.height))
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview, names=a.frames.split(",") if a.frames else None)
    else:
        export_all()
