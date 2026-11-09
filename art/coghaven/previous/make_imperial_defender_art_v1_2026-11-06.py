"""Source for the Imperial Defender, a Coghaven enemy (D4), 2026-11-06. Run from the repo root:

    python -P art/coghaven/make_imperial_defender_art.py [--preview FILE [--frames A,B]]

Design (user, 2026-11-06: "an imperial guard robot with a dadao sword that causes heavy contact damage and sometimes stops
to parry attacks and projectiles for 2 seconds, once every 8 seconds"): a stocky bronze robot in the armour of an
imperial palace guard, in vanilla's chunky proportions (D4 rule 18), the Sheriff's size. A gilt helmet bowl with ribs, a
brim and flared cheek guards, a spike with a red horsehair tassel flowing back, a crimson neck guard; a steel face mask
with a dark visor band, two ember eyes (hostile, D3) and a mouth grille. A torso that faces the screen (the user's
2026-11-06 rule): lamellar gilt plates in a brick bond over a crimson coat, a round chest mirror (huxinjing) with a jade
boss on the torso's axis, a crimson sash with a jade plaque, lamellar tassets with crimson hems; big gilt pauldrons;
crimson trousers, gilt knee caps, steel greaves and boots. The dadao: a broad, heavy saber widening to a clipped point,
a bright edge, a dark spine and a fuller, a gilt disc guard, a crimson-wrapped grip, a ring pommel with a tassel.
Three-quarter view facing left (D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg, the far arm and pauldron, flat and a step darker),
middle (the near leg drawn first so the tassets cover its thigh, then the body and the head), near (the near arm, the
dadao and the near pauldron); the glow sheet holds the eyes and the gleam running along the edge while he stands guard.
Stable pixels (D4 rule 17): the body is built in its own space and placed by whole-pixel bobs, the lamellar pattern is
counted in that space; limbs are lit with their light's turn snapped; far limbs are one tone; the sword is posed whole.

Frames: Walk x8 (the dadao carried low), Idle x2, GuardIn x3 (the blade swept up from the low carry), Guard x2 (held
upright before him, edge forward, the gleam running along it), GuardOut x2.

Outputs:
    Content/Coghaven/NPCs/ImperialDefender.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/ImperialDefenderRigData.cs     cells, origin, frame runs, the walk step
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
from westbots import (RAMP, Xf, Poly, Ellipse, box, Canvas, flat, dome, face, P, finish, leg, arm, texture,  # noqa: E402
                      glint, ST, G, K, E)
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
JD = RAMP["ghost"]                                   # jade: the Coghaven accent
THIGH, SHIN = 4.8, 4.6
UPPER, FORE = 4.3, 4.1
HIP_Y = -11.6
HEAD = (-0.4, -27.2)
SHOULDER_NEAR, SHOULDER_FAR = (-5.6, -21.8), (4.8, -22.0)
ARM = dict(r_upper=2.3, r_fore=2.0, sleeve="crimson", forearm="steel", glove="steel", cuff="gilt")
GUARD_HAND, GUARD_ANGLE = (-8.6, -18.4), 62.0        # the upright guard: the near fist out front, the blade up and forward
CARRY_ANGLE = -32.0                                  # the walk's low carry, the blade down and forward


class Pose:
    def __init__(self, bob=0, near_foot=(-2.0, 0.0), far_foot=(2.4, 0.0), hand=(-6.8, -15.0), far_hand=(4.6, -14.6),
                 guard=0.0, gleam=None):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot
        self.hand, self.far_hand = hand, far_hand
        self.guard = guard                           # 0 = the low carry .. 1 = the upright guard
        self.gleam = gleam                           # None, or 0..1: where the gleam runs along the edge


# Hand-placed details (a 7-px disc rasterised from an ellipse is all outline at 1x, as the Sheriff's star): digits are
# gilt shades, s..v jade shades (2..5). The chest mirror has no black ring: its rim is the darker gilt round a bright
# disc, so the lamellar round it still reads; the jade boss is lit from the top-left.
MIRROR = ["..343..",
          ".48973.",
          "39vut63",
          "48uts53",
          "37tss42",
          ".36542.",
          "..232.."]
MIRROR_AT = (-3.9, -22.2)                            # its top-left corner in the body's own space (the disc on the axis)
PLAQUE = ["2vut2",
          "2uts1"]
STAMP_JADE = {"s": 2, "t": 3, "u": 4, "v": 5}


def stamp(cv, rows, x0, y0):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            cv.put(x0 + dx, y0 + dy, JD[STAMP_JADE[ch]] if ch in STAMP_JADE else G[int(ch)])


def lamellar(cv, inner, oy, top, phase=0):
    """Rows of small plates in a brick bond over a gilt part (counted in the body's own space, so they ride its bob
    without crawling): each 2-px row is a lit plate face over its shadowed lower lip; the plates split every 4 px, the
    splits offset by half a plate on alternate rows."""
    for (x, y) in inner:
        col = cv.px.get((x, y))
        if col not in G:
            continue
        k = G.index(col)
        row, sub = divmod(y - oy - top, 2)
        if sub == 1:
            cv.put(x, y, G[max(2, k - 2)])
        elif (x + phase + (row % 2) * 2) % 4 == 0:
            cv.put(x, y, G[max(2, k - 1)])


def head(mid, glow, bx, at, oy):
    hx, hy = HEAD
    # the neck guard: crimson lamellar hanging behind the head (first, so the face covers its front)
    ng = mid.part(bx, Poly([(hx + 0.6, hy - 0.8), (hx + 4.6, hy - 1.0), (hx + 6.2, hy + 5.0), (hx + 1.8, hy + 5.8)]), "crimson",
                  face((0.2, -0.6, 0.75), lo=2, hi=4, ramp_len=6, fixed=True), rust=0.0)
    for (x, y) in ng:
        if (y - oy) % 2 == 0:
            mid.put(x, y, K[2])
    mid.part(bx, box(hx - 2.0, hy + 3.8, hx + 2.0, hy + 6.2), "steel", flat(3), rust=0.0)             # the neck
    fm = mid.part(bx, Ellipse(hx - 0.2, hy + 1.4, 3.9, 3.9), "steel",
                  dome(hx - 1.8, hy - 0.4, 4.8, lo=3, hi=7, gain=1.3, bias=0.25, fixed=True), shadow=(1, 1), rust=0.0)
    ey = at(0.0, hy + 0.9)[1]
    for x in range(at(hx - 3.8, 0.0)[0], at(hx + 3.2, 0.0)[0] + 1):
        if (x, ey) in fm:
            mid.put(x, ey, ST[1])                                    # the visor band
    for (ex, cols) in ((hx - 2.6, (E[3], E[2])), (hx + 0.6, (E[2],))):
        q = (at(ex, 0.0)[0], ey)
        for dx, col in enumerate(cols):
            mid.put_glow(q[0] + dx, q[1], col)
            glow.put_glow(q[0] + dx, q[1], col)
    nx = at(hx - 1.2, 0.0)[0]
    for y in (ey + 1, ey + 2):
        if (nx, y) in fm:
            mid.put(nx, y, ST[7])                                    # the mask's nose ridge, catching the light
            mid.put(nx + 1, y, ST[3])
    gy = ey + 3
    for x in range(at(hx - 2.8, 0.0)[0], at(hx + 1.2, 0.0)[0] + 1):
        if (x, gy) in fm:
            mid.put(x, gy, ST[2] if x % 2 else ST[5])                # the mouth grille
            if (x, gy + 1) in fm:
                mid.put(x, gy + 1, ST[2] if x % 2 else ST[4])
    # the cheek guards: gilt plates flaring down both sides of the mask
    for pts, n in (([(hx - 5.0, hy - 0.8), (hx - 3.2, hy - 0.8), (hx - 2.9, hy + 3.8), (hx - 3.8, hy + 5.4), (hx - 5.2, hy + 3.2)],
                    (-0.6, -0.4, 0.7)),
                   ([(hx + 2.9, hy - 0.8), (hx + 4.6, hy - 0.8), (hx + 4.4, hy + 3.4), (hx + 3.3, hy + 4.8)], (0.4, -0.5, 0.75))):
        mid.part(bx, Poly(pts), "gilt", face(n, lo=3, hi=7, ramp_len=10, gain=1.25, fixed=True), rust=0.0)
    # the bowl: a ribbed gilt half-dome on a brim
    arc = [(hx + 4.7 * math.cos(math.pi + t * math.pi / 12), hy - 1.4 + 4.6 * math.sin(math.pi + t * math.pi / 12)) for t in range(13)]
    bowl = mid.part(bx, Poly(arc), "gilt", dome(hx - 1.8, hy - 4.4, 5.6, lo=3, hi=8, gain=1.35, bias=0.2, fixed=True), rust=0.0)
    for rib in (-2.4, 0.2, 2.8):
        for (x, y) in bowl:
            ly = y - oy + 0.5
            span = 4.6 * math.sqrt(max(0.0, 1.0 - ((ly - (hy - 1.4)) / 4.6) ** 2))
            if span > 1.2 and int(math.floor(hx + rib * span / 4.7)) == x and ly > hy - 5.2:
                k = G.index(mid.px[(x, y)]) if mid.px[(x, y)] in G else 5
                mid.put(x, y, G[max(2, k - 2)])
    brim = mid.part(bx, box(hx - 5.6, hy - 1.8, hx + 5.2, hy - 0.4), "gilt", face((-0.3, -0.8, 0.6), lo=4, hi=8, ramp_len=10, fixed=True),
                    rust=0.0)
    jq = at(hx - 2.0, hy - 1.3)
    if jq in brim:                                                   # a jade bead on the brim's front
        mid.put(jq[0], jq[1], JD[4])
        mid.put(jq[0] + 1, jq[1], JD[2])
    gq = at(hx - 2.6, hy - 4.0)
    if gq in bowl:
        glint(mid, gq[0], gq[1], "gilt", cross=True)
    # the spike and its ball, and the red horsehair tassel flowing back over the bowl
    mid.part(bx, box(hx - 0.5, hy - 9.0, hx + 0.6, hy - 5.8), "gilt", flat(7), rust=0.0)
    mid.part(bx, Ellipse(hx, hy - 6.6, 1.4, 1.2), "gilt", dome(hx - 0.6, hy - 7.2, 1.8, lo=4, hi=9, fixed=True), rust=0.0)
    tassel = Poly([(hx - 1.8, hy - 5.6), (hx - 0.6, hy - 6.4), (hx + 2.4, hy - 6.8), (hx + 5.0, hy - 5.0), (hx + 6.6, hy - 1.8),
                   (hx + 6.0, hy - 0.2), (hx + 4.6, hy - 2.2), (hx + 3.0, hy - 3.8), (hx + 0.8, hy - 4.6), (hx - 1.2, hy - 4.4)])
    tin = mid.part(bx, tassel, "crimson", face((-0.4, -0.7, 0.6), lo=2, hi=5, ramp_len=6, gain=1.3, fixed=True), shadow=(1, 1), rust=0.0)
    for (x, y) in tin:
        if (x - (y - oy)) % 3 == 0:
            mid.put(x, y, K[2])                                      # its strands, combed back


def body(mid, glow, p):
    """The middle plane in the body's own space, placed by one whole-pixel translation (D4 rule 17)."""
    oy = p.bob
    bx = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))

    def at(x, y):
        return P(bx, (x, y))
    # --- the coat under the armour: crimson, from the shoulders to the knees ---------------------------------------------
    coat = Poly([(-6.4, -23.0), (5.6, -23.0), (6.4, -12.8), (5.8, -6.0), (-6.4, -6.0), (-7.0, -12.8)])
    mid.part(bx, coat, "crimson", texture(face((-0.5, -0.4, 0.75), lo=2, hi=4, ramp_len=6, gain=1.3, bias=0.2, fixed=True), "weave",
                                           seed=31), shadow=(1, 1), rust=0.0)
    # --- the lamellar cuirass (down under the sash) and the chest mirror (huxinjing) on the torso's axis -----------------
    cuirass = Poly([(-6.2, -23.0), (5.4, -23.0), (5.8, -12.6), (-6.6, -12.6)])
    inner = mid.part(bx, cuirass, "gilt", face((-0.5, -0.5, 0.72), lo=4, hi=8, ramp_len=10, gain=1.25, bias=0.25, fixed=True), rust=0.0)
    lamellar(mid, inner, oy, -23)
    x0, y0 = at(MIRROR_AT[0], MIRROR_AT[1])
    stamp(mid, MIRROR, x0, y0)
    # --- the lamellar tassets with crimson hems, then the sash over their tops with a jade plaque ------------------------
    for k, (fx0, fx1) in enumerate(((-7.0, -0.6), (-0.6, 6.2))):
        flap = Poly([(fx0, -13.4), (fx1, -13.4), (fx1 + 0.4, -6.6), (fx0 - 0.6, -6.2)])
        fin = mid.part(bx, flap, "gilt", face((-0.4, -0.5, 0.75), lo=4, hi=7, ramp_len=10, gain=1.2, fixed=True), rust=0.0)
        lamellar(mid, fin, oy, -12, phase=k)
        bottom = max(y for (_, y) in fin) if fin else 0
        for (x, y) in fin:
            if y == bottom:
                mid.put(x, y, K[4] if x % 3 else K[3])               # the crimson hem
    mid.part(bx, box(-6.8, -15.6, 6.2, -12.2), "crimson", face((-0.4, -0.6, 0.75), lo=2, hi=5, ramp_len=6, fixed=True), rust=0.0)
    px, py = at(-2.0, -15.0)
    stamp(mid, PLAQUE, px, py)
    head(mid, glow, bx, at, oy)
    return ((SHOULDER_NEAR[0], SHOULDER_NEAR[1] + oy), (SHOULDER_FAR[0], SHOULDER_FAR[1] + oy), (-1.4, HIP_Y + oy),
            (1.6, HIP_Y - 0.2 + oy))


def dadao(cv, grip, angle, gleam=None, glow=None):
    """The dadao in its own space (the blade towards -x from the guard, the edge towards +y, the grip towards +x), posed
    whole by `angle` degrees about the hand at `grip` (a generator rotation: never at runtime, D4 rule 14)."""
    xf = Xf.pose(angle, (0.0, 0.0), grip)
    blade = Poly([(-1.2, -1.1), (-12.4, -1.5), (-15.6, -1.1), (-17.2, 0.6), (-16.4, 2.6), (-13.6, 3.9), (-8.0, 3.2), (-1.2, 1.5)])
    bin_ = cv.part(xf, blade, "steel", face((-0.4, -0.6, 0.72), lo=4, hi=7, ramp_len=9, gain=1.25, bias=0.15, snap=45.0), rust=0.0)
    edge = []
    for t in range(2, 17):                                           # the bright edge, one pixel inside the curved belly
        x = -t - 0.5
        y = 1.0 + 2.6 * min(1.0, t / 13.6) - (max(0.0, t - 14.0) * 0.9)
        q = P(xf, (x, y))
        if q in bin_:
            edge.append(q)
            cv.put(q[0], q[1], ST[8])
        s = P(xf, (x, -0.7 - 0.04 * t))
        if s in bin_:
            cv.put(s[0], s[1], ST[3])                                # the spine
        if 3 <= t <= 11:
            f = P(xf, (x, 0.5))
            if f in bin_ and f not in edge:
                cv.put(f[0], f[1], ST[4])                            # the fuller
    if gleam is not None and glow is not None and edge:
        k = min(len(edge) - 1, int(gleam * len(edge)))
        for j in (k - 1, k, k + 1):
            if 0 <= j < len(edge):
                c = RAMP["steam"][3] if j == k else RAMP["ember"][3]
                glow.put_glow(edge[j][0], edge[j][1], c)
                cv.put_glow(edge[j][0], edge[j][1], c)
    cv.part(xf, Ellipse(-0.5, 0.2, 1.3, 2.9), "gilt", face((-0.5, -0.5, 0.7), lo=4, hi=8, ramp_len=10, snap=45.0), rust=0.0)  # guard
    cv.part(xf, box(0.4, -0.9, 5.8, 0.9), "crimson", flat(3, bevel=False), rust=0.0)                                         # grip
    for x in (1, 3, 5):
        q = P(xf, (x + 0.5, 0.0))
        cv.put(q[0], q[1], K[1])                                     # its wrapping
    ring = cv.part(xf, Ellipse(7.0, 0.0, 1.6, 1.6), "gilt", flat(6), rust=0.0)
    rq = P(xf, (7.0, 0.0))
    if rq in ring:
        cv.put(rq[0], rq[1], G[1])                                   # the ring's hole
    tq = P(xf, (7.6, 1.8))
    for dy in range(3):
        cv.put(tq[0], tq[1] + dy, K[4 if dy == 0 else 3])            # the tassel hanging from the ring
    return P(xf, (-16.0, 0.0))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    hip_near = (-1.4, HIP_Y + p.bob)
    leg(mid, hip_near, p.near_foot[0], p.near_foot[1], 0, THIGH, SHIN, r_thigh=2.4, r_shin=2.2, trousers="crimson", boot_ramp="steel",
        spur=False, knee_ramp="gilt")
    sh_near, sh_far, _, hip_far = body(mid, glow, p)
    leg(far, hip_far, p.far_foot[0], p.far_foot[1], 1, THIGH, SHIN, r_thigh=2.4, r_shin=2.2, trousers="crimson", boot_ramp="steel",
        spur=False, knee_ramp="gilt")
    g = p.guard
    hand = lerp((p.hand[0], p.hand[1] + p.bob), (GUARD_HAND[0], GUARD_HAND[1] + p.bob), g)
    far_hand = lerp((p.far_hand[0], p.far_hand[1] + p.bob), (3.0, -16.0 + p.bob), g)      # in guard: a fist at his far hip
    fist, _ = arm(near, sh_near, hand, 0, UPPER, FORE, **ARM)
    dadao(near, (fist[0] - 0.2, fist[1]), CARRY_ANGLE + (GUARD_ANGLE - CARRY_ANGLE) * g, gleam=p.gleam, glow=glow)
    arm(far, sh_far, far_hand, 1, UPPER, FORE, **ARM)
    fx, fy = sh_far
    far.part(Xf(), Ellipse(fx - 0.2, fy - 0.4, 2.8, 2.4), "gilt", flat(4), rust=0.0)   # the far pauldron (one tone)
    sx, sy = sh_near
    pin = near.part(Xf(), Ellipse(sx + 0.2, sy - 0.4, 3.3, 2.7), "gilt", dome(sx - 1.0, sy - 1.6, 3.8, lo=4, hi=9, gain=1.35, fixed=True),
                    rust=0.0)
    for (x, y) in pin:
        if y == int(math.floor(sy + 0.4)):
            near.put(x, y, G[3])                                     # its lamellar row
        elif y == int(math.floor(sy + 1.6)):
            near.put(x, y, K[3])                                     # the crimson edging
    for cv in (far, mid, near):
        finish(cv)
    return far, mid, near, glow


WALK = 8
STRIDE = 5.6


def cycle_foot(phase, n, stride, lift):
    t = (phase % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    nf, ff = cycle_foot(k, WALK, STRIDE, 1.8), cycle_foot(k + WALK // 2, WALK, STRIDE, 1.8)
    swing = 1 if k in (1, 2, 3) else (-1 if k in (5, 6, 7) else 0)
    return Pose(bob=1 if k % 4 in (1, 2) else 0, near_foot=(nf[0] - 2.0, nf[1]), far_foot=(ff[0] + 2.4, ff[1]),
                hand=(-6.8 - swing * 0.5, -15.0), far_hand=(4.6 + swing, -14.6))


STANCE = dict(near_foot=(-3.6, 0.0), far_foot=(3.4, 0.0))
FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Idle0", Pose()), ("Idle1", Pose(bob=1))]
          + [("GuardIn%d" % k, Pose(guard=g, **STANCE)) for k, g in enumerate((0.3, 0.65, 0.9))]
          + [("Guard%d" % k, Pose(guard=1.0, gleam=gl, **STANCE)) for k, gl in enumerate((0.3, 0.75))]
          + [("GuardOut%d" % k, Pose(guard=g, **STANCE)) for k, g in enumerate((0.6, 0.25))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Idle0"])
    top, bottom = int(math.floor(HEAD[1] - 9.0)), int(math.floor(HEAD[1] + 5.8))
    helmet = {q: c for q, c in mid.px.items() if top <= q[1] <= bottom and q[0] >= int(math.floor(HEAD[0] - 5.6))}
    sword = Canvas()
    dadao(sword, (0.0, 0.0), -20.0)
    finish(sword)
    mirror = Canvas()
    mirror.part(Xf(), Ellipse(0.0, 0.0, 3.4, 3.2), "gilt", dome(-1.2, -1.2, 3.8, lo=3, hi=9, gain=1.45, fixed=True), rust=0.0)
    mirror.part(Xf(), Ellipse(0.0, 0.0, 1.7, 1.6), "ghost", dome(-0.7, -0.7, 2.0, lo=2, hi=5, fixed=True), rust=0.0)
    finish(mirror)
    return {"ImperialDefender_GoreHelmet": crop(helmet), "ImperialDefender_GoreSword": crop(sword.px),
            "ImperialDefender_GoreMirror": crop(mirror.px)}


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
         "\t\t/// <summary>The guard's blade: its middle, game px from the origin (left-facing), where a parried hit sparks.</summary>",
         "\t\tpublic const int GuardBladeX = %d, GuardBladeY = %d;" % guard_blade(),
         "\t}",
         "}"]
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def guard_blade():
    """The middle of the blade in the upright guard, game px from the origin."""
    a = math.radians(GUARD_ANGLE)
    gx, gy = GUARD_HAND[0] - 0.2, GUARD_HAND[1]
    return round((gx - 8.0 * math.cos(a)) * 2), round((gy - 8.0 * math.sin(a)) * 2)


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
    cw, ch = 56, 50
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
