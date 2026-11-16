"""Source for the Mechromancer, a Blood Moon mini-boss (D4), and its Soul Fire Cog. Run from the repo root:

    python -P art/bloodmoon/make_mechromancer_art.py [--preview FILE]

Design (user, 2026-11-12: "a new blood moon mini boss enemy called the Mechromancer. it should be a robot with a brass skull
soul flame head that summon cogsqueletons and shoots soul fire cogs"; the rest my calls): a gaunt robot necromancer that
floats over the blood-red night. A brass skull for a head (a heavy brow, deep sockets with ghost-green eyes, a nasal
cavity, cheekbones, a jaw of brass teeth), its cranium split open and a soul flame streaming out of it; a steel ribcage
of a chest with a soul-fire core burning behind the ribs (the lantern-heart that feeds its spells); brass pauldrons; a
tattered crimson robe from the waist down where legs would be (it has none: it floats), a brass-buckled sash; crimson
sleeves over steel forearms and brass claws; and a staff of black iron crowned with a brass cog ring that holds a ball of
soul fire (the cogs it shoots are lit there). Hostile colour code (D3): ember/steam are for hostile effects, but the
soul fire is ghost green like the Cursed Conductor's soul fire, the mod's established undead flame (my call).

Three-quarter view facing left (D4 rule 13), lit from the top-left, torso turned to the screen (2026-11-06). Three
planes (DepthLayers.DrawWalker grid sheets): far (the far arm, a step darker), middle (the robe, the ribcage, the head and
its flame), near (the near arm and the staff); the glow sheet holds the eyes, the flame, the core and the staff's fire.
Stable pixels (D4 rule 17): the body is drawn in its own space; the bob of the float is in code; the robe's tatters and
the flames move by whole pixels between frames.

Frames: Float x4 (the tatters sway, the flame licks), Cast x4 (the staff drawn back, raised with its fire flaring: the
telegraph; thrust at the target: the volley; recovery), Summon x4 (both arms rise, raised high with the flame roaring:
the telegraph; the staff driven down: the Cogsqueletons rise; held).

The Soul Fire Cog: a brass 8-tooth cog wreathed in soul fire, 4 spin frames of 11.25 degrees (a seamless loop: the cog
has 45-degree symmetry), the fire on its glow sheet.

Outputs:
    Content/BloodMoon/NPCs/Mechromancer.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/BloodMoon/NPCs/MechromancerRigData.cs        cells, origin, frames, the staff's fire (where cogs leave)
    Content/BloodMoon/Projectiles/SoulFireCog.png, _Glow.png
    Content/BloodMoon/Projectiles/CogsqueletonGrave.png, _Glow.png   the summon's mark on the ground, 4 flickers
    Content/BloodMoon/Gores/Mechromancer_GoreSkull.png, _GoreStaff.png, _GoreRibs.png
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
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, face, P, finish, limb, texture,  # noqa: E402
                      glint, ST, G, K, IV)
from rig import ik  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/BloodMoon/"
GH = RAMP["ghost"]                                            # the soul fire: 0 darkest .. 5 white-green

WAIST_Y = -14.5
SHOULDER_NEAR, SHOULDER_FAR = (-6.2, -24.4), (5.8, -24.8)
HEAD = (-1.6, -31.4)
UPPER, FORE = 5.0, 5.4
STAFF_UP, STAFF_DOWN = 17.0, 15.0                             # the staff's length above and below the hand
COG_R = 3.9


class Pose:
    def __init__(self, tails=0, flame=0, near_hand=(-11.0, -16.4), staff=0.0, far_hand=(7.6, -16.8), fire=1, roar=0,
                 claws_open=False):
        self.tails = tails            # -1 / 0 / 1: the robe's tatters swing
        self.flame = flame            # 0..3: the soul flame's shape
        self.near_hand = near_hand
        self.staff = staff            # degrees the staff leans: + its top back (right), - forward (left)
        self.far_hand = far_hand
        self.fire = fire              # 0..2: the staff's soul fire (2 = flaring, the telegraph)
        self.roar = roar              # 0..2: the head's flame grows (the summon)
        self.claws_open = claws_open


# --- the robe, the ribcage, the head ------------------------------------------------------------------------------------------
def robe(mid, p):
    """Crimson cloth from the waist down, flaring, its hem torn into tatters that swing by whole pixels."""
    t = p.tails
    hem = [(-9.0 + t, -3.0), (-7.6 + t, 0.0), (-5.6, -2.6), (-3.4 + t, 0.6), (-1.0, -2.2), (1.4 + t, 0.4), (3.8, -2.4),
           (6.0 + t, 0.0), (7.8 + t, -3.2)]
    shape = Poly([(-4.6, WAIST_Y), (4.4, WAIST_Y), (6.2, -10.0)] + hem[::-1][:1] + hem[::-1][1:] + [(-7.0, -10.0)])
    shade = texture(face((-0.45, -0.35, 0.82), lo=1, hi=4, ramp_len=6, gain=1.3, bias=0.15, fixed=True, dither=0.12), "weave", seed=31)
    inner = mid.part(Xf(), shape, "crimson", shade, shadow=(1, 1), rust=0.0)
    # folds: long darker creases, lit on their left
    for (x0, x1, k) in ((-3.0, -4.6, 1), (0.8, 1.2, 1), (3.6, 4.8, 2)):
        for y in range(int(WAIST_Y) + 2, 0):
            f = (y - WAIST_Y) / -WAIST_Y
            x = int(math.floor(x0 + (x1 - x0) * f))
            if (x, y) in inner and (x, y + 1) in inner:
                mid.put(x, y, K[k])
                if (x - 1, y) in inner:
                    mid.put(x - 1, y, K[4] if x < 0 else K[3])
    # a tarnished gilt trim along the hem's top
    for x in range(-8, 8):
        y = -5 if x < -1 else -4
        q = (x, y)
        if q in inner:
            mid.put(x, y, G[6] if x < -3 else G[4] if x < 3 else G[3])
    # the sash at the waist and its brass buckle (a little cog)
    sash = mid.part(Xf(), box(-5.0, WAIST_Y - 1.6, 4.8, WAIST_Y + 1.2), "crimson",
                    face((-0.4, -0.6, 0.75), lo=1, hi=3, ramp_len=6, fixed=True), rust=0.0)
    cx, cy = P(Xf(), (-1.4, WAIST_Y - 0.4))
    for (dx, dy, k) in ((0, -1, 8), (-1, 0, 7), (0, 0, 5), (1, 0, 4), (0, 1, 3), (-1, -1, 6), (1, 1, 2), (1, -1, 5), (-1, 1, 4)):
        mid.put(cx + dx, cy + dy, G[k])
    mid.put(cx, cy, ST[1])
    return inner, sash


def ribcage(mid, glow, p):
    """The chest: a barrel of steel ribs either side of a sternum, dark inside, a soul-fire core burning behind them;
    big brass pauldrons on the shoulders."""
    cage = Poly([(-6.4, -25.4), (5.8, -25.6), (6.4, -21.0), (4.8, WAIST_Y - 0.6), (-5.4, WAIST_Y - 0.6), (-7.0, -21.0)])
    inner = mid.part(Xf(), cage, "steel", flat(1, bevel=False), shadow=(1, 1), rust=0.0)
    core = (-0.4, -20.6)
    for q in list(inner):
        d = math.hypot(q[0] + 0.5 - core[0], (q[1] + 0.5 - core[1]) * 1.1)
        if d < 4.2:
            k = 5 if d < 1.4 else 4 if d < 2.6 else 3 if d < 3.5 else 2
            mid.put_glow(q[0], q[1], GH[k])
            glow.put_glow(q[0], q[1], GH[k])
    # four ribs a side, curving down from the sternum and round the flank; lit on top, a shadow under
    for (k, y0) in enumerate((-24.4, -22.0, -19.6, -17.2)):
        for side in (-1, 1):
            for step in range(0, 8):
                x = (-1 - step) if side < 0 else step
                u = abs(x + 0.5)
                y = int(math.floor(y0 + 0.11 * u * u - 0.25 * k))
                q = (x, y)
                if q not in inner:
                    continue
                lit_ = 7 if side < 0 else 5
                mid.put(x, y, ST[lit_ - (1 if u > 4.5 else 0)])
                mid.glow.pop(q, None)
                glow.glow.pop(q, None)
                below = (x, y + 1)
                if below in inner and below not in mid.glow:
                    mid.put(below[0], below[1], ST[3] if side < 0 else ST[2])
    for y in range(-25, int(WAIST_Y)):                          # the sternum
        for (x, k) in ((-1, 7), (0, 4)):
            if (x, y) in inner:
                mid.put(x, y, ST[k])
                mid.glow.pop((x, y), None)
                glow.glow.pop((x, y), None)
    # the pauldrons: big brass domes, riveted, a dark rim under
    for (cx, cy, r, lo, hi) in ((SHOULDER_FAR[0] + 0.6, SHOULDER_FAR[1] - 0.2, 3.4, 2, 6), (SHOULDER_NEAR[0], SHOULDER_NEAR[1] - 0.2, 3.8, 3, 8)):
        pd = mid.part(Xf(), Ellipse(cx, cy, r, r * 0.8), "gilt", dome(cx - 1.4, cy - 1.2, r + 0.8, lo=lo, hi=hi, gain=1.4, fixed=True),
                      shadow=(1, 1), rust=0.0)
        for (dx, dy) in ((-1.4, 0.2), (1.2, 0.4)):
            q = P(Xf(), (cx + dx, cy + dy))
            if q in pd:
                mid.put(q[0], q[1], ST[8] if hi > 6 else ST[6])
    return inner


# The skull, placed by hand (a 13-px skull needs every feature placed): three-quarters to the left. Its silhouette row by
# row (local x from..to; the cranium bulges back to the right, the face and jaw sit forward and narrow to the chin),
# shaded as a dome lit from the top-left, outlined; then the features at exact pixels: the brow, two big rounded sockets
# (the far one narrower: three-quarters) with soul-fire eyes, the nose bridge, the nasal hole, the cheekbones, two rows
# of brass teeth with the seam between, the chin; a seam on the temple; the crown split under the flame.
SKULL_ROWS = ((4, 8), (2, 10), (1, 11), (0, 12), (0, 12), (0, 12), (0, 12), (0, 11), (0, 11), (0, 10), (0, 9), (1, 8),
              (1, 8), (2, 7), (3, 6))
SKULL_AT = (-8, -39)                                           # local (0, 0) in rig space
NEAR_SOCKET = ((2, 5), (3, 5), (1, 6), (2, 6), (3, 6), (4, 6), (1, 7), (2, 7), (3, 7), (4, 7), (2, 8), (3, 8))
FAR_SOCKET = ((6, 5), (7, 5), (6, 6), (7, 6), (8, 6), (6, 7), (7, 7), (8, 7), (7, 8))
EYES = (((2, 6), 5), ((3, 6), 4), ((2, 7), 3), ((7, 6), 4), ((7, 7), 3))
NASAL = ((4, 9), (5, 9), (5, 10))


def skull(mid, glow, p):
    x0, y0 = SKULL_AT
    pts = set()
    for ly, (a, b) in enumerate(SKULL_ROWS):
        for lx in range(a, b + 1):
            pts.add((lx, ly))
    for (lx, ly) in pts:
        dx, dy = (lx + 0.5 - 3.6) / 9.0, (ly + 0.5 - 2.4) / 9.5
        d2 = min(1.0, dx * dx + dy * dy)
        nz = (1.0 - d2) ** 0.5
        light = (-dx * 0.55 - dy * 0.6 + nz * 0.6)
        k = max(3, min(8, int(round(3.0 + 5.6 * max(0.0, light) ** 1.2))))
        if ly >= 9:
            k = max(3, k - 1)                                    # the face under the brow: a step down
        mid.put(x0 + lx, y0 + ly, G[k])
    for (lx, ly) in pts:                                         # the outline (the lit side's softened by selout later)
        if any((lx + ox, ly + oy) not in pts for (ox, oy) in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            mid.put(x0 + lx, y0 + ly, G[0])

    def put(lx, ly, col, glowing=False):
        if glowing:
            mid.put_glow(x0 + lx, y0 + ly, col)
            glow.put_glow(x0 + lx, y0 + ly, col)
        else:
            mid.put(x0 + lx, y0 + ly, col)
    for lx in range(1, 10):                                      # the brow ridge, lit
        put(lx, 4, G[8] if lx < 5 else G[7] if lx < 8 else G[6])
    for (lx, ly) in NEAR_SOCKET + FAR_SOCKET:
        put(lx, ly, G[0])
    for (q, k) in EYES:
        put(q[0], q[1], GH[k], glowing=True)
    for ly in (5, 6, 7):                                         # the nose bridge between the sockets
        put(5, ly, G[7] if ly < 7 else G[6])
    for (lx, ly) in NASAL:
        put(lx, ly, G[0])
    put(3, 9, G[6])                                              # the nasal hole's lit rim
    put(1, 8, G[7])
    put(1, 9, G[8])                                              # the near cheekbone
    put(2, 9, G[7])
    put(7, 9, G[5])                                              # the far cheekbone
    put(8, 8, G[4])
    for lx in range(1, 9):                                       # the upper teeth, the seam, the lower teeth
        put(lx, 11, G[8] if lx % 2 else G[5])
        put(lx, 12, G[1])
    for lx in range(2, 8):
        put(lx, 13, G[7] if lx % 2 == 0 else G[4])
    put(1, 10, G[2])                                             # the upper jaw's line over the teeth
    for lx in range(2, 9):
        put(lx, 10, G[3] if lx > 5 else G[4])
    for (lx, ly) in ((9, 3), (10, 4), (10, 5), (11, 6)):         # a seam on the temple
        put(lx, ly, G[2])
    put(9, 9, G[2])                                              # the jaw's hinge
    put(10, 8, G[3])
    for (lx, ly) in ((4, 1), (5, 0), (6, 1), (7, 0), (8, 1)):    # the split in the crown, under the flame's root
        put(lx, ly, G[1])
    return pts, pts


# The soul flame, placed by hand: a bulb of fire rising from the split crown, white-green where it leaves the skull,
# tongues licking up (digits are ghost shades, 2 the darkest edge .. 5 white-green). Four flickers: the tongues sway a
# pixel either way and the tallest takes turns; the summon's roar stretches the bulb.
FLAME = ("....2.....",
         "...23..2..",
         "...34..3..",
         "..2344.43.",
         ".234454432",
         ".345555443",
         "2345555543",
         ".345555432",
         "..3455543.",
         "...34543..",
         "....454...")
FLAME_AT = (-7, -49)                                            # the bottom row's middle (local x 5) sits on the crown


def flame_rows(k, roar):
    rows = [list(r) for r in FLAME]
    sway = (0, 1, 0, -1)[k % 4]
    if sway:
        for r in range(0, 4):                                    # the tongues lean
            row = rows[r]
            rows[r] = (["."] * sway + row[:-sway]) if sway > 0 else (row[-sway:] + ["."] * -sway)
    if k % 4 == 2:
        rows.insert(0, list("....2....."))                       # the tallest tongue flares
        rows[1][7] = "."
    else:
        rows.insert(0, list(".........."))
    for _ in range(roar * 2):
        rows.insert(6, list(rows[6]))
    return ["".join(r) for r in rows]


def flame(mid, glow, p, base=None):
    rows = flame_rows(p.flame, p.roar)
    x0 = FLAME_AT[0]
    y0 = FLAME_AT[1] - (len(rows) - len(FLAME))
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != ".":
                mid.put_glow(x0 + dx, y0 + dy, GH[int(ch)])
                glow.put_glow(x0 + dx, y0 + dy, GH[int(ch)])


def staff(cv, glow, hand, angle, fire):
    """The black-iron staff gripped at `hand`, leaning `angle` degrees, crowned with a brass cog ring holding soul fire.
    Returns the fire's centre (where the cogs leave)."""
    a = math.radians(angle)
    up = (math.sin(a), -math.cos(a))
    top = (hand[0] + up[0] * STAFF_UP, hand[1] + up[1] * STAFF_UP)
    bottom = (hand[0] - up[0] * STAFF_DOWN, hand[1] - up[1] * STAFF_DOWN)
    limb(cv, bottom, top, 1.25, "steel", 0, lo=1, hi=4)
    for f in (2.0, 2.6):                                         # a brass ferrule under the hand
        q = P(Xf(), (hand[0] - up[0] * f * 1.4, hand[1] - up[1] * f * 1.4))
        cv.put(q[0], q[1], G[6])
    # the cog ring: 8 teeth, brass, lit from the top-left; the soul fire in its middle
    c = (top[0] + up[0] * COG_R, top[1] + up[1] * COG_R)
    for y in range(int(c[1] - COG_R - 2), int(c[1] + COG_R + 3)):
        for x in range(int(c[0] - COG_R - 2), int(c[0] + COG_R + 3)):
            du, dv = x + 0.5 - c[0], y + 0.5 - c[1]
            r = math.hypot(du, dv)
            th = math.degrees(math.atan2(dv, du)) - angle
            tooth = math.cos(math.radians(th * 8)) > 0.25
            outer = COG_R + (1.1 if tooth else 0.0)
            if r > outer:
                continue
            if r < COG_R - 1.2:
                k = 5 if r < 0.9 else 4 if r < 1.6 else 3
                k = min(5, k + (1 if fire >= 2 and r < 1.8 else 0))
                cv.put_glow(x, y, GH[k])
                glow.put_glow(x, y, GH[k])
                continue
            light = -(du * 0.62 + dv * 0.78) / max(0.8, r)
            col = G[1] if r > outer - 0.7 else G[max(3, min(8, 5 + int(round(light * 2.5))))]
            cv.put(x, y, col)
    if fire >= 2:                                                # the telegraph: the fire licks out of the ring
        for (dx, dy, k) in ((0, -5, 3), (1, -5, 2), (-1, -4, 3), (0, -4, 4), (2, -4, 2)):
            q = (int(math.floor(c[0] + dx)), int(math.floor(c[1] + dy)))
            cv.put_glow(q[0], q[1], GH[k])
            glow.put_glow(q[0], q[1], GH[k])
    return c


def claw(cv, fist, u, depth, open_):
    """Three brass claws past the fist, along the forearm (fanned open for a spell)."""
    base = math.atan2(u[1], u[0])
    spread = (0.55 if open_ else 0.22)
    for k in (-1, 0, 1):
        a = base + k * spread
        for s in (1.6, 2.6):
            q = P(Xf(), (fist[0] + math.cos(a) * s, fist[1] + math.sin(a) * s))
            cv.put(q[0], q[1], G[3] if depth else (G[6] if k < 1 and s < 2.0 else G[4]))


def arm_bones(cv, shoulder, hand, depth, bend=1, open_=False):
    """A crimson sleeve, a steel forearm, a gilt cuff, a brass fist with claws."""
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, bend)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    limb(cv, elbow, wrist, 1.6, "steel", depth)
    limb(cv, shoulder, elbow, 2.4, "crimson", depth)
    # the bell of the sleeve: crimson flaring past the elbow over the forearm's start
    nrm = (-u[1], u[0])
    mouth = (elbow[0] + u[0] * 2.4, elbow[1] + u[1] * 2.4)
    bell = Poly([(elbow[0] + nrm[0] * 2.2, elbow[1] + nrm[1] * 2.2), (mouth[0] + nrm[0] * 3.2, mouth[1] + nrm[1] * 3.2),
                 (mouth[0] - nrm[0] * 3.2, mouth[1] - nrm[1] * 3.2), (elbow[0] - nrm[0] * 2.2, elbow[1] - nrm[1] * 2.2)])
    if depth > 0:
        cv.part(Xf(), bell, "crimson", flat(1, bevel=False), rust=0.0)
    else:
        cv.part(Xf(), bell, "crimson", texture(face((-0.45, -0.35, 0.82), lo=1, hi=4, ramp_len=6, gain=1.3, fixed=True), "weave", seed=37),
                rust=0.0)
    if depth == 0:
        q = P(Xf(), (wrist[0] - u[0] * 0.5, wrist[1] - u[1] * 0.5))
        cv.put(q[0], q[1], G[7])
        cv.put(q[0], q[1] + 1, G[4])
    fist = (wrist[0] + u[0] * 0.8, wrist[1] + u[1] * 0.8)
    if depth > 0:
        cv.part(Xf(), Ellipse(fist[0], fist[1], 1.6, 1.5), "gilt", flat(3, bevel=False), rust=0.0)
    else:
        cv.part(Xf(), Ellipse(fist[0], fist[1], 1.7, 1.6), "gilt", dome(fist[0] - 0.7, fist[1] - 0.7, 2.3, lo=3, hi=7, fixed=True), rust=0.0)
    claw(cv, fist, u, depth, open_)
    return fist


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    arm_bones(far, SHOULDER_FAR, p.far_hand, 1, bend=-1, open_=p.claws_open)
    robe(mid, p)
    ribcage(mid, glow, p)
    skull(mid, glow, p)
    flame(mid, glow, p)
    fist = arm_bones(near, SHOULDER_NEAR, p.near_hand, 0, bend=1)
    fire = staff(near, glow, (fist[0] - 0.2, fist[1]), p.staff, p.fire)
    near.part(Xf(), Ellipse(fist[0], fist[1], 1.8, 1.6), "gilt", dome(fist[0] - 0.8, fist[1] - 0.8, 2.4, lo=3, hi=7, fixed=True), rust=0.0)
    for cv in (far, mid, near):
        finish(cv)
    return far, mid, near, glow, fire


FRAMES = ([("Float%d" % k, Pose(tails=(0, 1, 0, -1)[k], flame=k)) for k in range(4)]
          + [("Cast0", Pose(tails=1, flame=1, near_hand=(-11.4, -24.6), staff=-6.0, far_hand=(6.4, -21.0), fire=1)),
             ("Cast1", Pose(tails=1, flame=2, near_hand=(-11.0, -28.0), staff=-16.0, far_hand=(6.0, -23.4), fire=2, claws_open=True)),
             ("Cast2", Pose(tails=-1, flame=3, near_hand=(-10.0, -22.0), staff=-58.0, far_hand=(5.6, -22.0), fire=2, claws_open=True)),
             ("Cast3", Pose(tails=0, flame=0, near_hand=(-11.0, -19.0), staff=-30.0, far_hand=(6.4, -20.2), fire=1))]
          + [("Summon0", Pose(tails=0, flame=1, near_hand=(-10.8, -24.2), staff=2.0, far_hand=(7.4, -25.6), fire=1, roar=1, claws_open=True)),
             ("Summon1", Pose(tails=1, flame=2, near_hand=(-10.6, -28.6), staff=4.0, far_hand=(7.0, -31.6), fire=2, roar=2, claws_open=True)),
             ("Summon2", Pose(tails=-1, flame=3, near_hand=(-9.0, -16.0), staff=-6.0, far_hand=(6.0, -18.4), fire=2, roar=1)),
             ("Summon3", Pose(tails=0, flame=0, near_hand=(-8.8, -17.0), staff=-4.0, far_hand=(6.4, -19.0), fire=1, roar=0))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- the Soul Fire Cog ----------------------------------------------------------------------------------------------------------
def soul_cog(rot, size=14):
    """A brass 8-tooth cog (radius 3.6 + 1.2 teeth) with a soul-fire hub, wreathed in a ring of soul fire (glow)."""
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
                if r > outer - 0.8 or (1.4 <= r < 2.0):
                    col = G[1]
                else:
                    col = G[max(3, min(8, 5 + int(round(light * 2.6))))]
                cv.put(x, y, col)
            elif r <= outer + 1.3 and r < size / 2.0:
                k = 3 if (int(th // 22.5) % 2 == 0) else 2                 # the fire's ring, two flickering bands
                glow.put_glow(x, y, GH[k])
    return cv, glow


COG_FRAMES = 4                                                 # 45-degree symmetry / 4 = 11.25 degrees a frame


# --- the grave mark (the summon's telegraph, where a Cogsqueleton will climb out) -----------------------------------------
GRAVE_W, GRAVE_H, GRAVE_FRAMES = 22, 10, 4


def grave(k):
    """A ring of soul fire burnt flat into the ground round a cracked, dark patch with a cog's sign in it; flames lick up
    from the ring, a different few each frame. Returns (texture canvas, glow canvas) in a GRAVE_W x GRAVE_H box whose
    bottom row is the ground line."""
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
                cv.put(x, y, RAMP["oak"][0] if r < 0.45 else RAMP["oak"][1])
    for (x, y) in ((10, 7), (11, 7), (9, 7), (12, 7), (10, 6), (11, 8), (8, 8), (13, 6)):   # the cog's sign: spokes and a hub
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
    hx, hy = HEAD
    return {"Mechromancer_GoreSkull": crop({q: c for q, c in mid.px.items() if q[1] <= hy + 6 and q[1] >= hy - 5 and abs(q[0] - hx) <= 6
                                             and q not in mid.glow}),
            "Mechromancer_GoreStaff": crop({q: c for q, c in near.px.items() if q[0] <= -7}),
            "Mechromancer_GoreRibs": crop({q: c for q, c in mid.px.items() if -28 <= q[1] <= -17 and abs(q[0]) <= 6 and q not in mid.glow})}


def write_rig(path, cell, fires):
    w, h, ox, oy = cell
    fx = ", ".join("%d" % round(f[0] * 2) for f in fires)
    fy = ", ".join("%d" % round(f[1] * 2) for f in fires)
    L = ["// <auto-generated> by art/bloodmoon/make_mechromancer_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.BloodMoon.NPCs",
         "{",
         "\t/// <summary>The Mechromancer's grid sheets (game px, facing left): far, middle, near and glow, equal cells with 2 px",
         "\t/// under each; the origin is the bottom of the robe's hem. FireX/FireY: the staff's fire in each frame (from the",
         "\t/// origin, facing left), where its Soul Fire Cogs leave.</summary>",
         "\tpublic static class MechromancerRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Float = 0, FloatFrames = 4, Cast = %d, CastFrames = 4, Summon = %d, SummonFrames = 4;" % (INDEX["Cast0"], INDEX["Summon0"]),
         "\t\tpublic static readonly int[] FireX = { %s };" % fx,
         "\t\tpublic static readonly int[] FireY = { %s };" % fy,
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Mechromancer%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Mechromancer_Glow.png")
    write_rig(OUT + "NPCs/MechromancerRigData.cs", cell, [fr[4] for fr in frames])
    cogs = [soul_cog(k * 45.0 / COG_FRAMES) for k in range(COG_FRAMES)]
    size = 14
    for name, idx in (("SoulFireCog", 0), ("SoulFireCog_Glow", 1)):
        im = Image.new("RGBA", (size, size * COG_FRAMES), (0, 0, 0, 0))
        for k, pair in enumerate(cogs):
            src = pair[idx].glow if idx == 1 else pair[idx].px
            for (x, y), col in src.items():
                if idx == 0 and (x, y) in pair[0].glow:
                    pass
                im.putpixel((x, y + k * size), col + (255,))
        export(im, OUT + "Projectiles/%s.png" % name)
    graves = [grave(k) for k in range(GRAVE_FRAMES)]
    for name, idx in (("CogsqueletonGrave", 0), ("CogsqueletonGrave_Glow", 1)):
        im = Image.new("RGBA", (GRAVE_W, GRAVE_H * GRAVE_FRAMES), (0, 0, 0, 0))
        for k, pair in enumerate(graves):
            src = pair[idx].glow if idx == 1 else pair[idx].px
            for (x, y), col in src.items():
                im.putpixel((x, y + k * GRAVE_H), col + (255,))
        export(im, OUT + "Projectiles/%s.png" % name)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=6, names=None):
    names = names or [n for n, _ in FRAMES]
    cw, ch = 40, 58
    cols = min(4, len(names))
    rws = (len(names) + cols - 1) // cols
    lookup = dict(FRAMES)
    sheet = Image.new("RGBA", (cw * cols, ch * rws), (48, 18, 24, 255))
    for k, n in enumerate(names):
        far, mid, near, glow, _ = frame(lookup[n])
        t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cvs in (far, mid, near):
            t.alpha_composite(to_image(cvs.px, -cw // 2 - 2, -ch + 4, cw, ch))
        sheet.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)
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
