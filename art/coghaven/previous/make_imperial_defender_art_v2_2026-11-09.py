"""Source for the Imperial Defender, a Coghaven enemy (D4). Run from the repo root:

    python -P art/coghaven/make_imperial_defender_art.py [--preview FILE [--frames A,B]]

Version 2 (2026-11-09, the user: "no Terraria quality nor Metal Slug pixel density ... the sword is ugly and the position
is horrible (pointed downwards)"); version 1 is kept in art/coghaven/previous/. Built like the sprites the user approved
(the Beat-Boxer, the Coghawk): a few big parts, each one material with clean highlight bands, strong contrast between
materials, and the small features hand-placed after the finishing pass so nothing eats them.

Design (user, 2026-11-06: "an imperial guard robot with a dadao sword that causes heavy contact damage and sometimes stops
to parry attacks and projectiles for 2 seconds"): a stocky palace-guard automaton, about 2.5 heads tall (the study's
proportions). A polished steel helmet bowl with gilt ribs, brim and spike under a red horsehair tassel; under it a fierce
gilt mask (a general's war mask) with ember eyes (hostile, D3), heavy brows and a moustache. The torso faces the screen
(user, 2026-11-06): a red coat under the Tang "bright-light" armour (two round gilt chest discs on a gilt strap), a steel
belly plate, a red sash with a gilt beast-face buckle, a red skirt with a gilt hem; gilt shoulder domes; red sleeves,
gilt vambraces, steel gauntlets; red trousers, steel greaves, black boots with gilt toe caps. The dadao: a broad, heavy
saber widening to a clipped point (a bright edge bevel, a steel flat with a fuller, a dark spine), a gilt disc guard, a
red-wrapped grip, a ring pommel with a red tassel; drawn by `dadao` at pixel-clean angles only (45, 63.4 and 90 degrees:
the stairs of a 1:1 and 1:2 line), never rotated at runtime (D4 rule 14).

Poses: he marches in a ready stance, the blade up and forward at 45 degrees from his near hand at his waist (never
pointing down); to parry he raises it through 63 degrees into an upright guard in front of his body, edge forward (a wall
between him and what comes at him), and a gleam runs up the edge while he holds it.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and arm, one tone a step darker), middle (the near leg,
the body, the head), near (the dadao, the near arm and its shoulder dome); the glow sheet holds the eyes and the gleam.
Stable pixels (D4 rule 17): the body is built in its own space and placed by whole-pixel bobs; limbs are lit with their
light's turn snapped; the dadao is rasterised from the same few angles and only translated.

Frames: Walk x8, Idle x2, GuardIn x3, Guard x2, GuardOut x2.

Outputs:
    Content/Coghaven/NPCs/ImperialDefender.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/ImperialDefenderRigData.cs     cells, origin, frame runs, the walk step, the guard's blade
    Content/Coghaven/Gores/ImperialDefender_GoreHelmet.png, _GoreSword.png, _GoreMirror.png
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
from westbots import (RAMP, Xf, Poly, Ellipse, box, Canvas, flat, dome, face, P, finish, limb, ik, texture, ST, G, K, E)  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
JD = RAMP["ghost"]
WHITE = RAMP["steam"][3]

# --- proportions (1x art px, y up is negative, the origin on the ground under the hips) ----------------------------------
HIP_NEAR, HIP_FAR = (-2.4, -13.0), (2.4, -13.2)
THIGH, SHIN = 5.6, 5.4
SHOULDER_NEAR, SHOULDER_FAR = (-6.6, -26.0), (6.4, -26.2)
UPPER, FORE = 5.0, 4.8
HEAD = (-0.6, -34.4)                                  # the mask's centre
BLADE = 20.0                                          # the dadao's blade length
CARRY = (-8.6, -16.4)                                 # the near hand in the ready stance (at the waist, in front)
GUARD = (-10.4, -21.4)                                # the near hand in the upright guard (chest height, in front)


class Pose:
    def __init__(self, bob=0, near_foot=(-2.6, 0.0), far_foot=(3.0, 0.0), hand=CARRY, angle=45, far_hand=(8.0, -15.4),
                 gleam=None):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot
        self.hand, self.angle, self.far_hand = hand, angle, far_hand
        self.gleam = gleam                            # None, or 0..1 up the edge


# ------------------------------------------------------------------------------------------------------------------------
# The dadao
# ------------------------------------------------------------------------------------------------------------------------
def blade_profile(s):
    """(spine, edge) offsets across the blade at s px from the guard (positive towards the edge): a straight thick back,
    the edge widening to the clipped point (the dadao's weight sits near the tip)."""
    spine = -1.3
    edge = 1.0 + 2.6 * (s / BLADE) ** 1.4
    if s > BLADE - 4.0:                               # the clipped point: the back drops to meet the edge
        k = (s - (BLADE - 4.0)) / 4.0
        spine = -1.3 + 3.2 * k * k
        edge = min(edge, 3.6 - 1.4 * k)
    return spine, edge


def dadao(cv, glow, grip, angle, gleam=None):
    """The dadao with its grip in the hand at `grip`, pointing `angle` degrees above forward (left), its edge forward;
    each pixel is classed by its place across the blade (edge bevel, flat, fuller, spine), so the stairs of the 1:1, 1:2
    and upright lines stay clean. Returns the pixel set of the blade."""
    a = math.radians(angle)
    u = (-math.cos(a), -math.sin(a))                 # along the blade, towards the tip
    v = (-math.sin(a), math.cos(a))                  # across it, towards the edge (forward)
    g = (grip[0] + u[0] * 3.4, grip[1] + u[1] * 3.4)     # the guard's face, past the fist
    inside, cls = set(), {}
    x0, x1 = int(math.floor(min(g[0], g[0] + u[0] * BLADE) - 6)), int(math.ceil(max(g[0], g[0] + u[0] * BLADE) + 6))
    y0, y1 = int(math.floor(min(g[1], g[1] + u[1] * BLADE) - 6)), int(math.ceil(max(g[1], g[1] + u[1] * BLADE) + 6))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px, py = x + 0.5 - g[0], y + 0.5 - g[1]
            s, t = px * u[0] + py * u[1], px * v[0] + py * v[1]
            if not (0.0 <= s <= BLADE):
                continue
            spine, edge = blade_profile(s)
            if spine <= t <= edge:
                inside.add((x, y))
                if t >= edge - 1.0:
                    cls[(x, y)] = ST[8]                # the edge bevel, catching the light
                elif t <= spine + 0.9:
                    cls[(x, y)] = ST[4]                # the thick back
                elif 2.5 <= s <= BLADE - 6.0 and abs(t - (spine + 1.7)) < 0.5:
                    cls[(x, y)] = ST[4]                # the fuller
                else:
                    cls[(x, y)] = ST[6]                # the flat
    for (x, y) in inside:                             # the outline: dark steel, one pixel round the blade
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in inside:
                cv.put(q[0], q[1], ST[1])
    for q, c in cls.items():
        cv.put(q[0], q[1], c)
    tip = (int(math.floor(g[0] + u[0] * (BLADE - 1.0))), int(math.floor(g[1] + u[1] * (BLADE - 1.0))))
    if tip in inside:
        cv.put(tip[0], tip[1], ST[8])
    if gleam is not None and glow is not None:       # a gleam running up the edge (the guard's held frames)
        s0 = 3.0 + gleam * (BLADE - 7.0)
        for (x, y) in inside:
            px, py = x + 0.5 - g[0], y + 0.5 - g[1]
            s, t = px * u[0] + py * u[1], px * v[0] + py * v[1]
            spine, edge = blade_profile(s)
            if t >= edge - 1.0 and abs(s - s0) < 1.6:
                col = WHITE if abs(s - s0) < 0.6 else RAMP["ember"][3]
                cv.put_glow(x, y, col)
                glow.put_glow(x, y, col)
    # the disc guard, the wrapped grip, the ring pommel and its tassel
    gx, gy = g[0] - u[0] * 0.6, g[1] - u[1] * 0.6
    cv.part(Xf(), Ellipse(gx, gy, 2.0, 2.0), "gilt", dome(gx - 0.8, gy - 0.8, 2.4, lo=4, hi=8, fixed=True), rust=0.0)
    for k in range(1, 6):
        q = P(Xf(), (g[0] - u[0] * (0.8 + k), g[1] - u[1] * (0.8 + k)))
        cv.put(q[0], q[1], K[3] if k % 2 else K[1])
        n = (q[0] + int(round(v[0])), q[1] + int(round(v[1])))
        if n not in inside:
            cv.put(n[0], n[1], K[1] if k % 2 else K[0])
    pc = (g[0] - u[0] * 7.4, g[1] - u[1] * 7.4)
    ring = cv.part(Xf(), Ellipse(pc[0], pc[1], 1.5, 1.5), "gilt", flat(6), rust=0.0)
    hole = P(Xf(), pc)
    if hole in ring:
        cv.put(hole[0], hole[1], G[1])
    for dy in range(1, 4):
        cv.put(hole[0], hole[1] + 1 + dy, K[4] if dy == 1 else K[3])
        if dy > 1:
            cv.put(hole[0] - 1, hole[1] + 1 + dy, K[2])
    return inside


# ------------------------------------------------------------------------------------------------------------------------
# Body parts
# ------------------------------------------------------------------------------------------------------------------------
def boot(cv, ankle, depth):
    """A black boot with an upturned toe and a gilt toe cap (the toe forward, left)."""
    ax, ay = ankle
    shade = flat(1, bevel=False) if depth else face((-0.4, -0.6, 0.7), lo=1, hi=3, ramp_len=9, fixed=True)
    cv.part(Xf(), Poly([(ax - 1.8, ay - 0.6), (ax + 1.8, ay - 0.6), (ax + 2.4, ay + 3.0), (ax - 3.6, ay + 3.0), (ax - 4.6, ay + 1.4)]),
            "steel", shade, rust=0.0)
    if depth == 0:
        t = P(Xf(), (ax - 4.0, ay + 1.6))
        cv.put(t[0], t[1], G[7])
        cv.put(t[0] + 1, t[1], G[5])


def leg(cv, hip, foot, depth):
    ankle = (foot[0], -3.0 - foot[1])
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)
    limb(cv, hip, knee, 3.0, "crimson", depth, lo=2, hi=4)
    limb(cv, knee, ankle, 2.5, "steel", depth, lo=3, hi=7)
    boot(cv, ankle, depth)
    if depth == 0:                                    # a gilt knee plate
        cv.part(Xf(), Ellipse(knee[0] - 0.4, knee[1], 1.7, 1.5), "gilt", dome(knee[0] - 1.0, knee[1] - 0.8, 2.0, lo=4, hi=8, fixed=True),
                rust=0.0)
    return knee


def arm(cv, shoulder, hand, depth):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)
    limb(cv, shoulder, elbow, 2.4, "crimson", depth, lo=1, hi=4)
    limb(cv, elbow, wrist, 2.2, "gilt", depth, lo=3, hi=7)
    shade = flat(2, bevel=False) if depth else dome(hand[0] - 0.8, hand[1] - 0.8, 2.4, lo=3, hi=7, fixed=True)
    cv.part(Xf(), Ellipse(hand[0], hand[1], 2.0, 1.9), "steel", shade, rust=0.0)


def shoulder_dome(cv, at, depth):
    """A steel shoulder dome with a gilt trim and a jade stud, built in its own space and placed by whole pixels so its
    brushed texture rides with it (D4 rule 17)."""
    ox, oy = int(round(at[0])), int(round(at[1]))
    xf = Xf.pose(0.0, (0.0, 0.0), (ox, oy))
    shade = flat(4, bevel=False) if depth else texture(dome(-1.4, -1.6, 4.0, lo=3, hi=8, gain=1.3, fixed=True), "brushed", seed=3)
    inner = cv.part(xf, Ellipse(0.0, 0.0, 3.8, 3.1), "steel", shade, rust=0.0)
    if depth == 0:
        for (x, y) in inner:
            if y == oy + 2:
                cv.put(x, y, G[6] if x % 2 else G[4])    # its gilt trim
        c = P(xf, (-0.4, -0.2))
        cv.put(c[0], c[1], JD[4])                     # a jade stud
        cv.put(c[0] + 1, c[1], JD[2])


def body(mid, p):
    """The middle plane's body in its own space, placed by one whole-pixel translation (D4 rule 17)."""
    oy = p.bob
    bx = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))
    # the skirt: red cloth to the knees, a gilt hem, a split in front
    skirt = mid.part(bx, Poly([(-6.0, -16.0), (5.8, -16.0), (7.8, -8.2), (0.8, -7.6), (-0.4, -9.6), (-1.6, -7.6), (-8.4, -8.2)]),
                     "crimson", face((-0.5, -0.4, 0.75), lo=2, hi=5, ramp_len=6, gain=1.25, fixed=True), rust=0.0)
    hem = max(y for (_, y) in skirt)
    fold = [P(bx, (fx, 0.0))[0] for fx in (-4.6, 3.6)]
    for (x, y) in skirt:
        if y >= hem - 1:
            mid.put(x, y, G[7] if y == hem - 1 else G[4])
        elif x in fold and y > -14 + oy:
            mid.put(x, y, K[2])                       # folds
            if (x + 1, y) in skirt:
                mid.put(x + 1, y, K[4])
    # the coat (red), the torso facing the screen
    coat = mid.part(bx, Poly([(-6.6, -27.6), (6.4, -27.6), (7.0, -17.0), (-7.2, -17.0)]), "crimson",
                    face((-0.5, -0.4, 0.75), lo=2, hi=5, ramp_len=6, gain=1.25, fixed=True), shadow=(1, 1), rust=0.0)
    sy = P(bx, (0.0, -18.6))[1]
    for (x, y) in coat:
        if y == sy and x % 3 == 0:
            mid.put(x, y, G[7])                       # a studded band under the chest
            if (x, y + 1) in coat:
                mid.put(x, y + 1, K[1])
    mid.part(bx, box(-5.6, -28.0, 5.4, -26.2), "gilt", face((-0.3, -0.8, 0.6), lo=4, hi=8, ramp_len=10, fixed=True), rust=0.0)   # collar
    mid.part(bx, box(-7.0, -17.8, 6.8, -15.0), "crimson", face((-0.4, -0.6, 0.75), lo=1, hi=2, ramp_len=6, fixed=True), rust=0.0)  # sash
    # the bright-light armour: two round gilt discs on the chest
    for cx in (-3.1, 2.9):
        mid.part(bx, Ellipse(cx, -22.6, 3.0, 2.9), "gilt", dome(cx - 1.0, -23.6, 3.4, lo=4, hi=8, gain=1.3, bias=0.1, fixed=True), rust=0.0)
    head(mid, bx, oy)
    return ((SHOULDER_NEAR[0], SHOULDER_NEAR[1] + oy), (SHOULDER_FAR[0], SHOULDER_FAR[1] + oy), (HIP_NEAR[0], HIP_NEAR[1] + oy),
            (HIP_FAR[0], HIP_FAR[1] + oy))


def head(mid, bx, oy):
    hx, hy = HEAD
    # the neck guard: red flaps flaring behind and below the mask
    mid.part(bx, Poly([(hx - 3.8, hy + 2.6), (hx + 5.0, hy + 0.6), (hx + 6.8, hy + 6.2), (hx - 2.2, hy + 6.6)]), "crimson",
             face((0.2, -0.6, 0.75), lo=1, hi=3, ramp_len=6, fixed=True), rust=0.0)
    # the gilt war mask
    mid.part(bx, Ellipse(hx - 0.2, hy + 1.0, 5.2, 5.0), "gilt", dome(hx - 2.0, hy - 0.8, 6.0, lo=5, hi=8, gain=1.3, bias=0.25, fixed=True),
             shadow=(1, 1), rust=0.0)
    # the helmet: a polished steel bowl on a gilt brim, gilt ribs, a gilt spike
    arc = [(hx + 5.6 * math.cos(math.pi + t * math.pi / 12), hy - 2.6 + 5.0 * math.sin(math.pi + t * math.pi / 12)) for t in range(13)]
    bowl = mid.part(bx, Poly(arc), "steel", texture(dome(hx - 2.0, hy - 6.0, 6.4, lo=3, hi=8, gain=1.35, bias=0.2, fixed=True), "brushed",
                                                     seed=9), rust=0.0)
    for (x, y) in bowl:
        lx = x + 0.5 - hx
        if abs(lx + 0.2) < 0.5 or abs(lx - 3.0) < 0.5 or abs(lx + 3.4) < 0.5:
            mid.put(x, y, G[6] if lx < 0 else G[5])   # the gilt ribs
    mid.part(bx, box(hx - 6.4, hy - 3.2, hx + 6.2, hy - 1.4), "gilt", face((-0.3, -0.8, 0.6), lo=4, hi=8, ramp_len=10, fixed=True),
             rust=0.0)
    mid.part(bx, box(hx - 0.6, hy - 10.4, hx + 0.8, hy - 7.2), "gilt", flat(7), rust=0.0)
    # the red horsehair tassel round the spike, flowing back
    mid.part(bx, Poly([(hx - 2.4, hy - 7.2), (hx - 0.4, hy - 9.0), (hx + 2.8, hy - 8.8), (hx + 6.4, hy - 6.0), (hx + 7.8, hy - 2.6),
                       (hx + 6.0, hy - 3.4), (hx + 3.2, hy - 6.0), (hx - 0.6, hy - 6.4)]), "crimson",
             face((-0.4, -0.7, 0.6), lo=2, hi=5, ramp_len=6, gain=1.3, fixed=True), rust=0.0)


# The mask's features and the small marks, hand-placed after the finishing pass (the despeckle would eat them):
# (dx, dy, colour key) from the mask's centre; e/E ember glow, g/G gilt shades, j jade, w white glow.
FACE = [(-3, -1, "g0"), (-2, -1, "g0"), (-1, 0, "g1"), (0, 0, "g1"), (1, -1, "g0"), (2, -1, "g0"),      # brows, frowning
        (-3, 0, "E3"), (-2, 1, "E2"), (1, 0, "E3"), (1, 1, "E2"),                                          # the eyes
        (-1, 1, "g8"), (-1, 2, "g7"), (0, 2, "g4"),                                                        # the nose
        (-4, 3, "g1"), (-3, 3, "g0"), (-2, 4, "g0"), (-1, 4, "g0"), (0, 4, "g0"), (1, 3, "g0"), (2, 3, "g1"),  # moustache
        (-2, 5, "g2"), (-1, 5, "g9"), (0, 5, "g2"),                                                        # the mouth, a glint of teeth
        (-1, -3, "j4"), (0, -3, "j2")]                                                                     # the brim's jade bead
BUCKLE = [(-2, 0, "g7"), (-1, 0, "g8"), (0, 0, "g7"), (1, 0, "g6"), (-2, 1, "g6"), (-1, 1, "j4"), (0, 1, "g5"), (1, 1, "j3"),
          (-2, 2, "g5"), (-1, 2, "g3"), (0, 2, "g3"), (1, 2, "g4")]


def stamp_marks(cv, glow, marks, cx, cy):
    for dx, dy, key in marks:
        x, y = cx + dx, cy + dy
        if key[0] == "E":
            c = RAMP["ember"][int(key[1:])]
            cv.put_glow(x, y, c)
            glow.put_glow(x, y, c)
        elif key[0] == "w":
            cv.put_glow(x, y, WHITE)
            glow.put_glow(x, y, WHITE)
        else:
            cv.put(x, y, {"g": G, "j": JD, "s": ST, "k": K}[key[0]][int(key[1:])])


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    leg(mid, (HIP_NEAR[0], HIP_NEAR[1] + p.bob), p.near_foot, 0)
    sh_near, sh_far, _, hip_far = body(mid, p)
    leg(far, hip_far, p.far_foot, 1)
    arm(far, sh_far, (p.far_hand[0], p.far_hand[1] + p.bob), 1)
    hand = (p.hand[0], p.hand[1] + p.bob)
    dadao(near, glow, hand, p.angle, p.gleam)
    arm(near, sh_near, hand, 0)
    shoulder_dome(mid, (sh_far[0] + 0.6, sh_far[1] - 0.6), 0)
    shoulder_dome(near, (sh_near[0] - 0.6, sh_near[1] - 0.6), 0)
    for cv in (far, mid, near):
        finish(cv)
    fx, fy = P(Xf(), (HEAD[0], HEAD[1] + p.bob))
    stamp_marks(mid, glow, FACE, fx, fy)
    bx_, by_ = P(Xf(), (0.0, -16.6 + p.bob))
    stamp_marks(mid, glow, BUCKLE, bx_, by_)
    return far, mid, near, glow


# ------------------------------------------------------------------------------------------------------------------------
# Animation
# ------------------------------------------------------------------------------------------------------------------------
WALK = 8
STRIDE = 8.0                     # 2 art px a frame = WalkStep 4 game px exactly (7.0 gave 3.5: a 0.5 px slip a frame)
LIFT = 3.0


def foot_cycle(f):
    """(x, lift) of a foot at walk frame f: planted for half the cycle, sliding BACK (+x: he faces -x, so the body walks
    forward over it), heel strike at -STRIDE/2 in front, toe-off at +STRIDE/2 behind; then swung forward through an arc.
    The Jaeger's cycle (art/mecharmy). Fixed 2026-11-09 (user: "the defender walk animation is backwards"): the planted
    foot slid forward (-x) and the swinging foot went back, a moonwalk, and the sword arm swung with its own leg."""
    f %= WALK
    half = WALK // 2
    if f <= half:
        return -STRIDE / 2 + STRIDE * f / half, 0.0
    t = (f - half) / half
    return STRIDE / 2 - STRIDE * t, round(LIFT * math.sin(math.pi * t))


def walk_pose(f):
    nx, nl = foot_cycle(f)
    fx, fl = foot_cycle(f + WALK // 2)
    bob = 0 if f % (WALK // 2) == 0 else -1           # lowest at each heel strike, up through mid-stance
    swing = math.cos(2.0 * math.pi * f / WALK)
    return Pose(bob=bob, near_foot=(nx - 2.6, nl), far_foot=(fx + 3.0, fl), hand=(CARRY[0] + round(swing), CARRY[1]),   # whole px: the blade only translates
                far_hand=(8.0 - swing * 1.8, -15.4 - abs(swing) * 0.4))


STANCE = dict(near_foot=(-4.2, 0.0), far_foot=(4.4, 0.0))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Idle0", Pose(**STANCE)), ("Idle1", Pose(bob=-1, **STANCE))]
          + [("GuardIn0", Pose(hand=lerp(CARRY, GUARD, 0.35), angle=45, far_hand=(7.6, -16.0), **STANCE)),
             ("GuardIn1", Pose(hand=lerp(CARRY, GUARD, 0.75), angle=63, far_hand=(7.2, -16.6), **STANCE)),
             ("GuardIn2", Pose(hand=GUARD, angle=90, far_hand=(7.0, -17.0), **STANCE))]
          + [("Guard%d" % k, Pose(hand=GUARD, angle=90, far_hand=(7.0, -17.0), gleam=gl, **STANCE)) for k, gl in enumerate((0.2, 0.75))]
          + [("GuardOut0", Pose(hand=lerp(CARRY, GUARD, 0.7), angle=63, far_hand=(7.2, -16.6), **STANCE)),
             ("GuardOut1", Pose(hand=lerp(CARRY, GUARD, 0.3), angle=45, far_hand=(7.6, -16.0), **STANCE))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Idle0"])
    hx, hy = HEAD
    helmet = {q: c for q, c in mid.px.items() if hy - 10.0 <= q[1] <= hy + 5.0 and hx - 6.0 <= q[0] <= hx + 7.0}
    sword = Canvas()
    dadao(sword, Canvas(), (0.0, 0.0), 45)
    mirror = Canvas()
    mirror.part(Xf(), Ellipse(0.0, 0.0, 2.9, 2.8), "gilt", dome(-1.0, -1.0, 3.2, lo=3, hi=9, gain=1.4, bias=0.15, fixed=True), rust=0.0)
    finish(mirror)
    return {"ImperialDefender_GoreHelmet": crop(helmet), "ImperialDefender_GoreSword": crop(sword.px),
            "ImperialDefender_GoreMirror": crop(mirror.px)}


def guard_blade():
    """The middle of the upright blade in the guard, game px from the origin."""
    gx, gy = GUARD[0], GUARD[1] - 3.4 - BLADE / 2
    return round(gx * 2), round(gy * 2)


def write_rig(path, cell):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/coghaven/make_imperial_defender_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.NPCs",
         "{",
         "\t/// <summary>The Imperial Defender's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal",
         "\t/// cells with 2 px under each; the origin is the ground point under his hips. Each sequence is Name .. Name +",
         "\t/// NameFrames - 1.</summary>",
         "\tpublic static class ImperialDefenderRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Idle = %d, IdleFrames = 2, GuardIn = %d, GuardInFrames = 3, Guard = %d, GuardFrames = 2, GuardOut = %d, GuardOutFrames = 2;"
         % (WALK, INDEX["Idle0"], INDEX["GuardIn0"], INDEX["Guard0"], INDEX["GuardOut0"]),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d;" % round(STRIDE * 2 / (WALK / 2)),
         "\t\t/// <summary>The upright guard's blade: its middle, game px from the origin (left-facing), where a parried hit sparks.</summary>",
         "\t\tpublic const int GuardBladeX = %d, GuardBladeY = %d;" % guard_blade(),
         "\t}",
         "}"]
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/ImperialDefender%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/ImperialDefender_Glow.png")
    write_rig(OUT + "NPCs/ImperialDefenderRigData.cs", cell)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, names=None, scale=4):
    cw, ch = 56, 54
    chosen = [(n, p) for (n, p) in FRAMES if names is None or n in names]
    cols = min(6, len(chosen))
    rows = (len(chosen) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(chosen):
            far, mid, near, glow = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near, glow):
                t.alpha_composite(to_image(cv.px, -cw // 2 - 6, -ch + 3, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames", help="comma-separated frame names for a close-up preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview, a.frames.split(",") if a.frames else None, 8 if a.frames else 4)
    else:
        export_all()
