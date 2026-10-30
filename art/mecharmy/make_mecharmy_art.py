"""Source for the Mech Army invasion's sprites (D4, art direction of 2026-10-26), 2026-10-27. Run from the repo root:

    python -P art/mecharmy/make_mecharmy_art.py [--preview DIR]

Every enemy is a detailed entity (D4 rules 13-16): a three-quarter view facing left, rendered from rig.py parts (shapes
placed by transforms and rasterised per pixel, limbs posed with two-bone IK), never rotated or scaled at runtime, split
into up to three planes drawn with Core/Visuals/DepthLayers (the far plane baked one ramp step darker), Metal Slug-level
detail (ramp-0 outlines, rivets, seams with lit lips, hazard stripes, pistons, cast shadows). Hostile lights are ember.

    Jaeger (miniboss)     a jaeger-style war machine, 6.6x the player (146 px at 1x = 292 px; the player is 42 px tall):
                          armoured head sunk between two hazard-striped pauldrons, a furnace reactor in the chest, piston
                          arms ending in riveted fists, smokestacks on its back. Far plane: far arm + far leg; middle:
                          hips, torso, head, stacks (+ _Glow: reactor and visor); near plane: near leg + near arm.
                          28 frames: a 24-frame walk (each foot planted for 12 frames, sliding back WALK_STEP px a frame:
                          the root motion is exactly that, so the planted foot never slips) and a 4-frame idle. Packed
                          atlases (pack_layer, as Trash-Tr0m) and Content/MechArmy/MechArmyRigData.cs (frame tables,
                          footfalls, hit strips, reactor point).
    Rogue Mice-bot        the Mice-bot summon's clockwork mouse gone feral: copper armadillo shell, iron back plate,
                          brass ear, ember eye, iron snout with steel teeth, wind-up key, wire tail. Far: far wheels and
                          ear; near: near wheels. 8 frames (idle x2, run x4, leap, bite).
    Boombot               a walking bomb: riveted iron sphere, hazard-striped brass belt, ember eye lens, a fuse cap
                          with a warning lamp (+ _Glow: eye and lamp, blinked in code), two piston legs with claw feet.
                          Far: far leg; near: near leg. 9 frames (run x6, idle x2, leap).
    Annoy-o-tron          a squat brass alarm box on two treads with a speaker horn, under a red emergency beacon whose
                          reflector spins (a separate 8-frame _Beacon sheet + _Beacon_Glow drawn on its head, so it spins
                          whatever the body does). Far: far tread; near: near tread. 7 body frames (drive x4, idle x2,
                          hop).
Also: the Boombot's blast (6 frames), gores, and the invasion's progress-bar icon.
Small enemies use grid sheets (equal cells, 2 px padding, DepthLayers.DrawCell); cell sizes and origins are written to
the rig data too, so code and art can't drift apart.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import (RAMP, Xf, Poly, Ellipse, Ring, Capsule, Union, box, Canvas, flat, face, dome, cyl,  # noqa: E402
                 rivet, bolt, seam, line, stripes, ik)
from make_trashtr0m_art import (fs, lerp, seg_xf, hydraulic, pack_layer, page_name, export, to_image, cs_array,  # noqa: E402
                                vertical, GROUND_CLIP)
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
import make_scrap_weapons as scrap_weapons  # noqa: E402  (the Mice-bot minion's mouse, reused by the Rogue Mice-bot)
from make_scrap_art import PAL as SCRAP_PAL  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/MechArmy/"
I, B, C, V, E, S, LE = (RAMP[k] for k in ("iron", "brass", "copper", "verd", "ember", "steam", "leather"))
N_FRONT = (-0.8, 0.15, 0.58)                           # faces turned to the left (forward)
N_SIDE = (0.32, -0.08, 0.94)                           # faces turned to the viewer
N_TOP = (-0.1, -0.95, 0.3)


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def emblem(cv, cx, cy, col, dark, inner=None):
    """The Mech Army's unit mark: a 7x5 chevron over a bar, symmetric so it still reads when the sprite is mirrored
    (a number decal would turn into a mirror image when the NPC faces right)."""
    rows = ("...#...", "..#.#..", ".#...#.", ".......", "#######")
    for ry, bits in enumerate(rows):
        for rx, b in enumerate(bits):
            q = (cx - 3 + rx, cy - 2 + ry)
            if b == "#" and (inner is None or q in inner):
                cv.put(q[0], q[1], col)
                below = (q[0], q[1] + 1)
                if (inner is None or below in inner) and (ry + 1 >= len(rows) or rows[ry + 1][rx] != "#"):
                    cv.put(below[0], below[1], dark)


# ================================================================================================
# Jaeger (was "Yager" until 2026-10-28)
# ================================================================================================
WALK_FRAMES = 24
IDLE_FRAMES = 4
WALK_STEP = 3                                          # 1x px a planted foot slides back per frame (= root motion)
STRIDE = WALK_STEP * WALK_FRAMES // 2                  # 36 px a step
HALF = STRIDE / 2.0
PELVIS_Y = -66.0
HIP_NEAR, HIP_FAR = (5.0, -64.0), (-6.0, -67.0)
THIGH, SHIN = 31.0, 31.0
ANKLE_Y = -8.0
FOOT_NEAR_X, FOOT_FAR_X = 3.0, -4.0                    # the two feet's tracks (three-quarter view)
SHOULDER_NEAR, SHOULDER_FAR = (15.0, -110.0), (-15.0, -114.0)
UPPER, FORE = 25.0, 29.0
ARM_SWING = 10.0
LIFT = 11.0


class YPose:
    def __init__(self, bob=0.0, near_foot=(0.0, 0.0), far_foot=(0.0, 0.0), near_hand=(0.0, 0.0), far_hand=(0.0, 0.0),
                 vent=0, fist=0):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot    # (x, lift) of each ankle
        self.near_hand, self.far_hand = near_hand, far_hand    # hand offsets from the hanging rest point
        self.vent = vent
        self.fist = fist


def foot_cycle(f):
    """(x, lift) of the near ankle at walk frame f: planted for frames 0..12 sliding back WALK_STEP a frame (heel strike
    at -HALF on frame 0, toe-off at +HALF on frame 12), then swung forward through an arc."""
    f %= WALK_FRAMES
    half = WALK_FRAMES // 2
    if f <= half:
        return -HALF + WALK_STEP * f, 0.0
    t = (f - half) / half
    return HALF - STRIDE * t, LIFT * math.sin(math.pi * t)


def walk_pose(f):
    nx, nl = foot_cycle(f)
    fx, fl = foot_cycle(f + WALK_FRAMES // 2)
    phase = 2.0 * math.pi * f / WALK_FRAMES
    bob = -1.6 * abs(math.sin(phase))                  # lowest at heel strike (frames 0 and 12), up at mid-stance
    swing = ARM_SWING * math.cos(phase)
    return YPose(bob=bob, near_foot=(FOOT_NEAR_X + nx, nl), far_foot=(FOOT_FAR_X + fx, fl),
                 near_hand=(swing, -abs(swing) * 0.25), far_hand=(-swing, -abs(swing) * 0.25), vent=f % 8)


def idle_pose(k):
    breathe = (0.0, -1.0, -1.0, 0.0)[k]
    return YPose(bob=breathe, near_foot=(FOOT_NEAR_X - 7.0, 0.0), far_foot=(FOOT_FAR_X + 8.0, 0.0),
                 near_hand=(1.0, breathe * 0.5), far_hand=(-1.5, breathe * 0.5), vent=k * 2)


def armour_leg(cv, hip, ankle_x, lift, depth):
    """Thigh, knee, greave, piston and boot. Knee forward (bend -1)."""
    ankle = (ankle_x, ANKLE_Y - lift)
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)
    # boot first: the greave overlaps its top
    ax, ay = ankle
    heel, toe = ax + 10.0, ax - 15.0
    sole_y = ay + 8.0
    boot = cv.part(Xf(), Poly([(heel, ay - 4), (ax - 5, ay - 5), (toe + 2, sole_y - 6), (toe, sole_y - 1), (heel + 1, sole_y - 1)]),
                   "iron", fs(N_SIDE, bias=-0.2), depth=depth, shadow=(1, 1), rust=0.0)
    cv.part(Xf(), Poly([(toe + 3, sole_y - 6), (ax - 4, ay - 3), (ax - 1, ay + 1), (toe + 1, sole_y - 2)]), "brass",
            fs(N_FRONT, lo=2, hi=5, bias=0.25), depth=depth, rust=0.0)
    sole = cv.raster(Xf(), box(toe, sole_y - 2, heel + 1, sole_y)) & boot
    for (x, y) in sole:
        cv.put(x, y, I[max(1, 1 - depth)] if (x + y) % 3 else I[0])
    for k in range(3):
        rivet(cv, Xf(), (heel - 3 - k * 4, sole_y - 4), "iron", boot)
    # greave (shin): a wide armour shell, flaring at the ankle
    sx = seg_xf(knee, ankle)
    ls = math.hypot(ankle[0] - knee[0], ankle[1] - knee[1])
    shin = cv.part(sx, Poly([(-2, -7.0), (ls + 1, -10.0), (ls + 1, 8.5), (-2, 6.5)]), "verd",
                   cyl((0, 0), (ls, 0), 9.0, lo=1, hi=3, gain=1.5, bias=-0.25), depth=depth, shadow=(2, 2), rust=0.0)
    seam(cv, sx, (ls * 0.35, -8), (ls * 0.35, 7), "verd", shin)
    seam(cv, sx, (ls * 0.72, -9), (ls * 0.72, 8), "verd", shin)
    plate = cv.part(sx, Poly([(ls * 0.08, -7.0), (ls * 0.62, -8.5), (ls * 0.62, -2.5), (ls * 0.08, -2.0)]), "brass",
                    cyl((0, -5), (ls, -5), 4.0, lo=1, hi=4, gain=1.3, bias=0.0), depth=depth, rust=0.0)
    stripes(cv, cv.raster(sx, box(ls * 0.40, -9, ls * 0.6, -2)) & plate, 2, B[max(1, 4 - depth)], I[0], slope=1)
    for k in range(4):
        rivet(cv, sx, (ls * (0.12 + k * 0.2), 5.0), "iron", shin)
    hydraulic(cv, sx, (ls * 0.1, 8.5), (ls * 0.92, 9.0), 2.6, depth=depth)
    # knee: a brass cap with a bolt
    cv.part(Xf(), Ellipse(knee[0] - 1.0, knee[1], 6.5, 6.0), "brass", dome(knee[0] - 2.5, knee[1] - 2.0, 7.5, lo=1, hi=5), depth=depth, shadow=(1, 1), rust=0.0)
    bolt(cv, Xf(), (knee[0] - 2.0, knee[1] - 1.0), "iron")
    # thigh: iron cylinder with a ram, under a hip plate
    tx = seg_xf(hip, knee)
    lt = math.hypot(knee[0] - hip[0], knee[1] - hip[1])
    thigh = cv.part(tx, Capsule((0, 0), (lt, 0), 8.5, 7.0), "iron", cyl((0, 0), (lt, 0), 8.5, lo=1, hi=4, gain=1.5, bias=-0.35),
                    depth=depth, shadow=(2, 2), rust=0.0)
    seam(cv, tx, (lt * 0.25, -6), (lt * 0.25, 6), "iron", thigh)
    for k in range(3):
        rivet(cv, tx, (lt * (0.35 + k * 0.18), -4.0), "iron", thigh)
    hydraulic(cv, tx, (lt * 0.15, -7.5), (lt * 0.9, -6.0), 2.2, depth=depth)
    return knee, ankle


def armour_arm(cv, shoulder, hand_off, depth, number=None):
    """Pauldron, upper arm, elbow, gauntlet forearm and fist. Elbow back (bend +1)."""
    rest = (shoulder[0] + 3.0, shoulder[1] + 52.0)
    hand = (rest[0] + hand_off[0], rest[1] + hand_off[1])
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)
    # upper arm
    ux = seg_xf(shoulder, elbow)
    lu = math.hypot(elbow[0] - shoulder[0], elbow[1] - shoulder[1])
    up = cv.part(ux, Capsule((0, 0), (lu, 0), 7.0, 6.0), "iron", cyl((0, 0), (lu, 0), 7.0, lo=1, hi=4, gain=1.5, bias=-0.35),
                 depth=depth, shadow=(2, 2), rust=0.0)
    seam(cv, ux, (lu * 0.55, -5), (lu * 0.55, 5), "iron", up)
    hydraulic(cv, ux, (lu * 0.2, 6.0), (lu * 0.95, 5.0), 2.0, depth=depth)
    # forearm gauntlet: a big brass-trimmed iron shell
    fx = seg_xf(elbow, wrist)
    lf = math.hypot(wrist[0] - elbow[0], wrist[1] - elbow[1])
    fore = cv.part(fx, Poly([(-1, -6.5), (lf * 0.55, -9.5), (lf + 1, -9.0), (lf + 1, 9.0), (lf * 0.55, 9.5), (-1, 6.5)]), "verd",
                   cyl((0, 0), (lf, 0), 9.5, lo=1, hi=3, gain=1.4, bias=-0.25), depth=depth, shadow=(2, 3), rust=0.0)
    cuff = cv.part(fx, box(lf * 0.72, -9.5, lf + 1, 9.5), "brass", cyl((0, 0), (lf, 0), 9.5, lo=1, hi=4, gain=1.3, bias=0.0), depth=depth, rust=0.0)
    stripes(cv, cv.raster(fx, box(lf * 0.78, -9, lf * 0.95, 9)) & cuff, 2, B[max(1, 4 - depth)], I[0])
    seam(cv, fx, (lf * 0.3, -8), (lf * 0.3, 8), "verd", fore)
    for k in range(4):
        rivet(cv, fx, (lf * (0.1 + k * 0.15), -6.5), "iron", fore)
    hydraulic(cv, fx, (lf * 0.05, 8.5), (lf * 0.7, 9.5), 2.4, depth=depth)
    # elbow joint
    cv.part(Xf(), Ellipse(elbow[0], elbow[1], 5.5, 5.5), "brass", dome(elbow[0] - 1.5, elbow[1] - 1.5, 6.0, lo=1, hi=5), depth=depth, shadow=(1, 1), rust=0.0)
    cv.put(int(elbow[0]), int(elbow[1]), I[1])
    # fist: knuckles forward-down
    hx, hy = wrist
    fist = cv.part(Xf(), Poly([(hx - 9, hy - 2), (hx + 6, hy - 3), (hx + 8, hy + 9), (hx + 3, hy + 15), (hx - 8, hy + 15), (hx - 11, hy + 8)]),
                   "iron", fs(N_SIDE, bias=-0.15), depth=depth, shadow=(2, 2), rust=0.0)
    for k in range(4):
        kx, ky = hx - 10.0 + k * 0.3, hy + 1.0 + k * 3.4
        cv.part(Xf(), Ellipse(kx, ky, 3.2, 2.2), "iron", dome(kx - 1, ky - 1, 3.2, lo=1, hi=4, gain=1.3), depth=depth, rust=0.0)
    cv.part(Xf(), Poly([(hx - 6, hy - 2), (hx + 5, hy - 3), (hx + 6, hy + 2), (hx - 6, hy + 3)]), "brass", fs(N_TOP, lo=2, hi=4, bias=0.1), depth=depth, rust=0.0)
    for (x, y) in ((hx - 2, hy + 9), (hx + 3, hy + 9)):
        rivet(cv, Xf(), (x, y), "iron", fist)
    # pauldron: a curved armour shell over the shoulder, hazard band on its rim, the unit mark
    sx, sy = shoulder
    pad = Poly([(sx - 17, sy - 6), (sx - 11, sy - 16), (sx + 3, sy - 20), (sx + 15, sy - 16), (sx + 19, sy - 4),
                (sx + 17, sy + 10), (sx - 15, sy + 10)])
    pin = cv.part(Xf(), pad, "verd", dome(sx - 6, sy - 12, 22, lo=1, hi=3, gain=1.3, bias=-0.2), depth=depth, shadow=(2, 3), rust=0.0)
    rim = cv.raster(Xf(), box(sx - 18, sy + 5, sx + 20, sy + 10)) & pin
    stripes(cv, rim, 3, B[max(1, 4 - depth)], I[0], slope=-1)
    seam(cv, Xf(), (sx - 12, sy - 4), (sx + 15, sy - 2), "verd", pin)
    for k in range(6):
        rivet(cv, Xf(), (sx - 11 + k * 5, sy - 8 - (2 if 1 <= k <= 4 else 0)), "iron", pin)
    if number:
        emblem(cv, int(sx + 1), int(sy - 3), B[max(1, 4 - depth)], V[0], pin)
    return elbow, wrist


def jaeger_body(cv, pose):
    """Hips, abdomen, torso, collar, head, smokestacks, reactor; returns the reactor centre."""
    oy = pose.bob
    xf = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))
    # smokestacks behind the torso
    for (x0, x1, top, r) in ((18.0, 20.0, -146.0, 3.2), (24.0, 26.0, -140.0, 2.8)):
        st = cv.part(xf, Capsule((x0, -110.0), (x1, top), r), "iron", cyl((x0, -110.0), (x1, top), r, lo=1, hi=3, gain=1.5, bands=6), shadow=(1, 1), rust=0.0)
        cv.part(xf, Capsule((x0 + (x1 - x0) * 0.6, top + 8.0), (x0 + (x1 - x0) * 0.62, top + 6.5), r + 0.8), "brass", flat(2), rust=0.0)
        cv.part(xf, Capsule((x1 - 0.2, top + 1.0), (x1 + 0.2, top - 0.5), r + 1.0), "iron", flat(3), rust=0.0)
        tip = P(xf, (x1, top - 1.0))
        cv.put(tip[0], tip[1], I[0])
        cv.put(tip[0] - 1, tip[1], I[0])
    # pelvis skirt and hip block
    cv.part(xf, Poly([(-18, -76), (14, -76), (16, -62), (8, -54), (-10, -54), (-19, -62)]), "iron", fs(N_SIDE, bias=-0.3), shadow=(2, 2), rust=0.0)
    skirt = cv.part(xf, Poly([(-20, -70), (-6, -71), (-5, -56), (-17, -58)]), "brass", fs(N_FRONT, lo=2, hi=4, bias=0.0), rust=0.0)
    side_skirt = cv.part(xf, Poly([(-6, -71), (16, -70), (15, -58), (-5, -56)]), "brass", fs(N_SIDE, lo=1, hi=3, bias=-0.1), rust=0.0)
    stripes(cv, cv.raster(xf, box(-20, -61, 16, -55)) & (skirt | side_skirt), 3, B[4], I[0], slope=1)
    for k in range(4):
        rivet(cv, xf, (-3 + k * 5, -67), "brass", side_skirt)
    # abdomen: stacked iron rings (a flexible spine)
    for k in range(3):
        y = -84.0 + k * 4.0
        cv.part(xf, Poly([(-14 + k, y - 3), (12 - k, y - 3), (11 - k, y + 2), (-13 + k, y + 2)]), "iron", fs(N_SIDE, lo=1, hi=3, bias=-0.1), shadow=(0, 1), rust=0.0)
    # torso: top, front (forward) and side (towards the viewer) faces
    top = cv.part(xf, Poly([(-31, -119), (-16, -130), (18, -128), (28, -120), (-9, -124)]), "verd", fs(N_TOP, lo=2, hi=3, bias=0.1), rust=0.0)
    front = cv.part(xf, Poly([(-31, -119), (-9, -124), (-6, -84), (-19, -78)]), "verd", fs(N_FRONT, hi=3, bias=0.05), shadow=(1, 1), rust=0.0)
    side = cv.part(xf, Poly([(-9, -124), (28, -120), (29, -100), (16, -82), (-6, -84)]), "verd", fs(N_SIDE, hi=3, bias=-0.3), shadow=(2, 2), rust=0.0)
    # side armour plates, seams, welds, rivet rows
    seam(cv, xf, (-6, -104), (28, -102), "verd", side)
    seam(cv, xf, (8, -121), (11, -83), "verd", side)
    plate = cv.part(xf, Poly([(13, -117), (25, -115), (26, -101), (14, -102)]), "brass", fs(N_SIDE, lo=2, hi=4, bias=0.0), shadow=(1, 1), rust=0.0)
    emblem(cv, 19, int(-111 + oy), B[1], B[0], plate)
    for k in range(7):
        rivet(cv, xf, (-4 + k * 4.8, -121.5 + k * 0.5), "iron", side)
    for k in range(4):
        rivet(cv, xf, (27.5, -115 + k * 5), "iron", side)
    vent = cv.part(xf, Poly([(-3, -98), (7, -97), (7, -88), (-3, -89)]), "iron", flat(1, bevel=False), rust=0.0)
    for p in vent:
        if (p[1] - int(oy)) % 2 == 0:
            cv.put(p[0], p[1], I[3] if (p[0] + pose.vent) % 4 else I[2])
    # chest reactor: a furnace port on the front face, brass rim, grille, glowing core
    rc = (-18.0, -104.0)
    cv.part(xf, Ellipse(rc[0], rc[1], 7.0, 9.0), "brass", dome(rc[0] - 2, rc[1] - 3, 9, lo=1, hi=4, gain=1.2), shadow=(1, 1), rust=0.0)
    core = cv.raster(xf, Ellipse(rc[0], rc[1], 4.6, 6.5))
    for (x, y) in core:
        ly = y - int(oy)
        if ly % 3 == 0:
            cv.put(x, y, I[1])
        else:
            cv.put_glow(x, y, E[3] if (x - int(rc[0])) ** 2 + (ly - int(rc[1])) ** 2 < 10 else E[2])
    for k in range(5):
        a = math.radians(k * 72 - 90)
        rivet(cv, xf, (rc[0] + math.cos(a) * 5.8, rc[1] + math.sin(a) * 7.8), "brass")
    for k in range(4):
        rivet(cv, xf, (-28 + k * 5.0, -116.5 - k * 1.2), "iron", front)
    seam(cv, xf, (-24, -92), (-7, -94), "verd", front)
    # cables from the back of the torso into the hips
    for k, ramp in enumerate(("verd", "leather")):
        r = RAMP[ramp]
        pts = [(20 - k * 3, -86), (14 - k * 3, -78), (8 - k * 2, -72)]
        for a, b in zip(pts, pts[1:]):
            line(cv, xf, a, b, lambda n: r[1])
            line(cv, xf, (a[0] - 1, a[1]), (b[0] - 1, b[1]), lambda n: r[2])
    # collar: armour plates around the neck
    cv.part(xf, Poly([(-20, -124), (-14, -133), (8, -133), (14, -125), (-6, -121)]), "iron", fs(N_TOP, lo=1, hi=3, bias=0.0), shadow=(1, 1), rust=0.0)
    # head: a squat helmet, visor slit, brass crest
    hf = cv.part(xf, Poly([(-18, -138), (-9, -141), (-8, -127), (-16, -125)]), "verd", fs(N_FRONT, hi=3, bias=0.05), shadow=(1, 1), rust=0.0)
    hs = cv.part(xf, Poly([(-9, -141), (4, -140), (5, -128), (-8, -127)]), "verd", fs(N_SIDE, hi=3, bias=-0.3), rust=0.0)
    cv.part(xf, Poly([(-18, -138), (-12, -144), (1, -143), (4, -140), (-9, -141)]), "verd", fs(N_TOP, lo=2, hi=3, bias=0.1), rust=0.0)
    for x in range(-17, -9):
        q = P(xf, (x + 0.5, -133.5 + (x + 17) * 0.12))
        if q in hf:
            cv.put_glow(q[0], q[1], E[3] if x < -12 else E[2])
            cv.put(q[0], q[1] + 1, I[0])
    cv.part(xf, Poly([(-11, -147), (-4, -148), (2, -144), (-9, -143)]), "brass", fs(N_SIDE, lo=2, hi=4, bias=0.0), rust=0.0)
    rivet(cv, xf, (-3, -136), "iron", hs)
    rivet(cv, xf, (1, -132), "iron", hs)
    return (rc[0], rc[1] + oy)


def jaeger_frame(pose):
    """(far, middle, near) canvases of one pose."""
    far, mid, near = Canvas(), Canvas(), Canvas()
    oy = pose.bob
    hip_f = (HIP_FAR[0], HIP_FAR[1] + oy)
    hip_n = (HIP_NEAR[0], HIP_NEAR[1] + oy)
    sh_f = (SHOULDER_FAR[0], SHOULDER_FAR[1] + oy)
    sh_n = (SHOULDER_NEAR[0], SHOULDER_NEAR[1] + oy)
    # far plane: far leg then far arm (the arm hangs in front of the far leg)
    armour_leg(far, hip_f, pose.far_foot[0], pose.far_foot[1], depth=1)
    armour_arm(far, sh_f, pose.far_hand, depth=1)
    reactor = jaeger_body(mid, pose)
    armour_leg(near, hip_n, pose.near_foot[0], pose.near_foot[1], depth=0)
    armour_arm(near, sh_n, pose.near_hand, depth=0, number=True)
    return far, mid, near, reactor


def jaeger_frames():
    poses = [walk_pose(f) for f in range(WALK_FRAMES)] + [idle_pose(k) for k in range(IDLE_FRAMES)]
    return [jaeger_frame(p) for p in poses]


JAEGER_STRIPS = 5


def merged(cvs):
    out = Canvas()
    for cv in cvs:
        out.px.update(cv.px)
    return out


def hit_strips(cv, n):
    """n vertical strips over the frame's opaque pixels above the ground clip, each the box of the rows with >= 3 px."""
    pts = [p for p in cv.px if p[1] < GROUND_CLIP]
    x0 = min(p[0] for p in pts)
    x1 = max(p[0] for p in pts) + 1
    out = []
    for k in range(n):
        a = x0 + (x1 - x0) * k // n
        b = x0 + (x1 - x0) * (k + 1) // n
        col = [p for p in pts if a <= p[0] < b]
        rows = {}
        for (x, y) in col:
            rows[y] = rows.get(y, 0) + 1
        keep = [(x, y) for (x, y) in col if rows[y] >= 3]
        if not keep:
            out.append((0, 0, 0, 0))
            continue
        out.append((min(q[0] for q in keep) * 2, min(q[1] for q in keep) * 2,
                    (max(q[0] for q in keep) + 1) * 2, (max(q[1] for q in keep) + 1) * 2))
    return out


def plant_frames():
    """Walk frames where a heel strikes the ground (a footfall: sound, dust, a small shake)."""
    return [1 if f in (0, WALK_FRAMES // 2) else 0 for f in range(WALK_FRAMES)]


# ================================================================================================
# Small enemies: (far, middle, near[, glow]) canvases per frame, origin on the ground under the body centre
# ================================================================================================
def wheel(cv, cx, cy, r, turn, depth=0):
    """An iron wheel with a brass hub; the spoke notch moves a quarter turn per step of `turn`."""
    w = cv.part(Xf(), Ellipse(cx, cy, r, r), "iron", dome(cx - 0.8, cy - 0.8, r * 1.2, lo=1, hi=4, gain=1.3), depth=depth, rust=0.0)
    hub = (int(math.floor(cx)), int(math.floor(cy)))
    cv.put(hub[0], hub[1], B[max(1, 3 - depth)])
    dx, dy = ((1, 0), (0, 1), (-1, 0), (0, -1))[turn % 4]
    q = (hub[0] + dx, hub[1] + dy)
    if q in w:
        cv.put(q[0], q[1], I[1])
    return w


def mouse_frame(k):
    """Rogue Mice-bot frame k: 0-1 idle, 2-5 run, 6 leap, 7 bite. Returns far, mid (eye in its glow), near.
    Redrawn 2026-10-28 (user: "too big and different from the ones summoned from the staff"): it is now the Mice-bot
    minion itself, the same 16x11 clockwork mouse drawn by art/scrap/make_scrap_weapons.py `mouse()` with the same
    frames, mirrored to face left (D4 rule 8), its friendly verdigris eye swapped for a hostile ember one (D3 colour
    code). A mouse this small has no depth to split, so it is all on the middle plane (no _Far/_Near sheets)."""
    letters = scrap_weapons.mouse(**MOUSE_SPECS[k])
    mid = Canvas()
    for y in range(letters.h):
        for x in range(letters.w):
            ch = letters.g[y][x]
            if ch == ".":
                continue
            rx, ry = (letters.w - 1 - x) - letters.w // 2, y - (letters.h - 1)   # mirrored; the wheels' bottom row on y 0
            if ch == "u":
                mid.put_glow(rx, ry, E[2])                   # the eye: ember, hostile
            else:
                mid.put(rx, ry, SCRAP_PAL[ch])
    return Canvas(), mid, Canvas()


MOUSE_SPECS = [                                          # = make_scrap_weapons.make_mouse_frames(), frame for frame
    dict(key=0),
    dict(key=1, sniff=True, tail=2),
    dict(key=0, wheel=0, tail=0),
    dict(key=1, wheel=1, tail=1, bob=-1),
    dict(key=0, wheel=2, tail=0),
    dict(key=1, wheel=3, tail=1, bob=-1),
    dict(key=1, pounce=True, tail=2),
    dict(key=0, pounce=True, mouth=True, tail=1),
]


MOUSE_FRAMES = 8


BOMB_R = 6.5                                           # the bomb's radius (1x): 13 px across, 26 in game
BOMB_LEGS = 4.0                                        # hip to sole: short, quick legs
BOMB_CY = -(BOMB_LEGS + BOMB_R)                        # standing: the bomb's centre above the ground
ROLL_FRAMES = 8                                        # a full turn in 8 frames of 45 degrees
BOOM_RUN_FRAMES = 6
BOOM_IDLE, BOOM_LEAP, BOOM_TRIP, BOOM_FALL, BOOM_ROLL = 6, 8, 9, 10, 11


def bomb(mid, glow, cx, cy, angle, spark, flare=False):
    """The bomb: a black, rusted iron sphere (the dark end of the iron ramp, copper rust patches that turn with it), a
    riveted seam round its middle, a fuse cap on top with a short frayed fuse ending in a spark (glow). `angle` turns
    the whole bomb (0 = upright; negative = counter-clockwise, which is forward for the left-facing art). The light
    stays top-left whatever the angle (the shaders turn the normals back), so only the details roll."""
    xf = Xf.pose(angle, (0.0, 0.0), (cx, cy))
    body = mid.part(xf, Ellipse(0.0, 0.0, BOMB_R, BOMB_R), "iron", dome(-2.4, -2.6, BOMB_R * 1.35, lo=1, hi=2, gain=1.4, bias=-0.35),
                    shadow=(1, 1), rust=0.55, seed=0xB0B)
    for t in range(-6, 7):                                # the seam: a dark groove with a lit lip
        q = P(xf, (t, 0.5))
        if q in body:
            mid.put(q[0], q[1], I[0])
            lip = (q[0], q[1] + 1)
            if lip in body:
                mid.put(lip[0], lip[1], I[2])
    for t in (-4.0, 0.0, 4.0):
        rivet(mid, xf, (t, -1.2), "iron", body)
    gx, gy = int(math.floor(cx - 3.0)), int(math.floor(cy - 3.5))   # the glint: a reflection, so it doesn't roll
    for (x, y, c) in ((gx, gy, I[3]), (gx + 1, gy, I[3]), (gx, gy + 1, I[3]), (gx - 1, gy + 1, I[2]), (gx + 1, gy - 1, I[4])):
        if (x, y) in body:
            mid.put(x, y, c)
    mid.part(xf, box(-1.8, -BOMB_R - 2.2, 1.8, -BOMB_R + 1.2), "iron", flat(2), rust=0.0)        # fuse cap
    mid.part(xf, box(-2.4, -BOMB_R - 2.8, 2.4, -BOMB_R - 1.6), "brass", flat(3), rust=0.0)       # its brass rim
    for n, pt in enumerate(((0.3, -BOMB_R - 3.0), (1.2, -BOMB_R - 4.4), (2.6, -BOMB_R - 5.2))):  # the frayed fuse
        q = P(xf, pt)
        mid.put(q[0], q[1], LE[2] if n % 2 == 0 else LE[1])
    tip = P(xf, (3.6, -BOMB_R - 5.6))
    core = E[3] if spark % 2 == 0 else S[3]
    arms = ((1, 0), (0, -1)) if spark % 2 == 0 else ((-1, 0), (0, 1), (1, -1))
    if flare:
        arms = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, -1))
    for (x, y, c) in [(tip[0], tip[1], core)] + [(tip[0] + dx, tip[1] + dy, E[2]) for dx, dy in arms]:
        mid.put_glow(x, y, c)
        glow.put_glow(x, y, c)
    return xf, body


def bomb_leg(cv, hip, foot, depth):
    """A short piston leg: iron thigh, brass shin, an iron clog of a foot (2 px tall, toes forward)."""
    knee, ankle = ik(hip, foot, 2.6, 2.6, -1)
    cv.part(Xf(), Capsule(hip, knee, 1.5, 1.3), "iron", cyl(hip, knee, 1.5, lo=1, hi=3), depth=depth, rust=0.0)
    cv.part(Xf(), Capsule(knee, ankle, 1.4, 1.2), "brass", cyl(knee, ankle, 1.4, lo=1, hi=4), depth=depth, rust=0.0)
    ax, ay = ankle
    cv.part(Xf(), Poly([(ax + 1.6, ay - 0.6), (ax - 1.2, ay - 1.0), (ax - 3.0, ay + 0.6), (ax - 2.6, ay + 1.6), (ax + 1.8, ay + 1.6)]),
            "iron", flat(2), depth=depth, rust=0.0)


def boombot_frame(k):
    """Boombot frame k (redrawn 2026-10-28, user: "a black rusted bomb with a fuse and short quick legs"): 0-5 run,
    6-7 idle, 8 leap, 9 trip (stumbling, pitched forward), 10 fall (face down, legs flung up), 11-18 roll (a full turn
    forward in 45-degree steps, legs tucked in). Returns far, mid, near, glow."""
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    if k >= BOOM_ROLL:
        r = k - BOOM_ROLL
        bomb(mid, glow, 0.0, -BOMB_R, -45.0 * r, r)
        return far, mid, near, glow
    if k == BOOM_TRIP:                                    # a foot caught: the near leg kicked back, the far one stabbing forward
        cx, cy = -1.0, BOMB_CY + 0.5
        bomb_leg(far, (cx - 2.0, cy + 4.5), (cx - 5.5, -0.5), 1)
        bomb(mid, glow, cx, cy, -30.0, 1)
        bomb_leg(near, (cx + 2.5, cy + 5.0), (cx + 6.5, -3.0), 0)
        return far, mid, near, glow
    if k == BOOM_FALL:                                    # going down face first, both legs flung up behind
        cx, cy = -2.5, -BOMB_R - 0.5
        bomb_leg(far, (cx + 3.0, cy + 3.5), (cx + 6.5, cy - 0.5), 1)
        bomb(mid, glow, cx, cy, -75.0, 0)
        bomb_leg(near, (cx + 4.5, cy + 2.5), (cx + 7.5, cy - 2.5), 0)
        return far, mid, near, glow
    if k < BOOM_IDLE:                                     # run: quick little steps
        ph = 2.0 * math.pi * k / BOOM_RUN_FRAMES
        bob = -0.8 * abs(math.sin(ph))
        nf = (2.6 * math.cos(ph), max(0.0, 1.8 * math.sin(ph)))
        ff = (2.6 * math.cos(ph + math.pi), max(0.0, 1.8 * math.sin(ph + math.pi)))
    elif k == BOOM_LEAP:
        bob, nf, ff = -2.0, (1.5, 2.5), (-1.8, 3.0)
    else:
        bob = 0.0 if k == BOOM_IDLE else -0.5
        nf, ff = (1.5, 0.0), (-1.5, 0.0)
    cy = BOMB_CY + bob
    bomb_leg(far, (-1.8, cy + BOMB_R - 1.2), (ff[0] - 0.8, -0.5 - ff[1]), 1)
    bomb(mid, glow, 0.0, cy, 0.0, k)
    bomb_leg(near, (1.8, cy + BOMB_R - 1.0), (nf[0] + 0.6, -0.5 - nf[1]), 0)
    return far, mid, near, glow


BOOMBOT_FRAMES = BOOM_ROLL + ROLL_FRAMES


def annoy_frame(k, friendly=False):
    """Annoy-o-tron body frame k: 0-3 drive, 4-5 idle, 6 hop. Returns far, mid, near, bob (1x px the beacon moves).
    A small brass alarm box on two treads: a round speaker on its side, a grille mouth in front, a whip antenna; its head
    is the beacon (_Beacon sheet), seated on the collar drawn here. `friendly` (the Alarm Head minion, 2026-10-28): a
    verdigris antenna tip instead of an ember one (D3 colour code: hostile ember, friendly verdigris/aether)."""
    far, mid, near = Canvas(), Canvas(), Canvas()
    drive = k <= 3
    hop = k == 6
    bob = -1 if (drive and k % 2 == 1) else (-2 if hop else 0)
    shift = k % 4 if drive else 0

    def tread(cv, x0, x1, y0, y1, depth):
        t = cv.part(Xf(), Union(box(x0 + 2, y0, x1 - 2, y1), Ellipse(x0 + 2.5, (y0 + y1) / 2, 2.5, (y1 - y0) / 2),
                                Ellipse(x1 - 2.5, (y0 + y1) / 2, 2.5, (y1 - y0) / 2)), "iron", flat(2), depth=depth, rust=0.0)
        for (x, y) in t:
            on_rim = (x, y - 1) not in t or (x, y + 1) not in t
            if on_rim and (x + shift) % 2 == 0:
                cv.put(x, y, I[max(1, 3 - depth)])
        for wx in (x0 + 2.5, (x0 + x1) / 2, x1 - 2.5):
            q = (int(math.floor(wx)), int(math.floor((y0 + y1) / 2)))
            if q in t:
                cv.put(q[0], q[1], B[max(1, 3 - depth)])
                cv.put(q[0] + 1, q[1], I[1])
        return t

    lift = 2 if hop else 0
    tread(far, -9.0, 5.0, -7.0 - lift, -2.0 - lift, 1)
    oy = bob
    xf = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))
    # chassis: front, side and top faces (brass), a hazard band along the bottom
    front = mid.part(xf, Poly([(-9, -12), (-5, -13), (-5, -5), (-9, -5)]), "brass", fs(N_FRONT, lo=1, hi=4, bias=0.1), shadow=(1, 1), rust=0.0)
    side = mid.part(xf, Poly([(-5, -13), (7, -13), (7, -5), (-5, -5)]), "brass", fs(N_SIDE, lo=1, hi=4, bias=-0.15), shadow=(1, 1), rust=0.0)
    mid.part(xf, Poly([(-9, -12), (-6, -15), (8, -15), (7, -13), (-5, -13)]), "brass", fs(N_TOP, lo=2, hi=4, bias=0.2), rust=0.0)
    stripes(mid, mid.raster(xf, box(-9, -7.0, 7, -5.0)) & (side | front), 2, B[4], I[0], slope=-1)
    # grille mouth on the front face
    for y in (-11, -9):
        for x in (-8, -7):
            q = P(xf, (x + 0.5, y + 0.5))
            if q in front:
                mid.put(q[0], q[1], I[0])
    # round speaker on the side: brass rim, iron cone, rings; it throbs on the idle frames
    sr = 3.2 + (0.4 if k == 5 else 0.0)
    mid.part(xf, Ellipse(1.5, -9.5, sr, sr), "brass", dome(0.5, -10.5, sr + 0.6, lo=1, hi=4), shadow=(1, 1), rust=0.0)
    cone = mid.raster(xf, Ellipse(1.5, -9.5, sr - 1.2, sr - 1.2))
    for (x, y) in cone:
        d = math.hypot(x + 0.5 - 1.5, y - int(oy) + 0.5 + 9.5)
        mid.put(x, y, I[0] if d < 0.9 else (I[2] if int(d * 2) % 2 == 0 else I[1]))
    for x in (6.0,):
        rivet(mid, xf, (x, -12.0), "iron", side)
    rivet(mid, xf, (-4.0, -12.0), "iron", side)
    # whip antenna with an ember tip
    line(mid, xf, (5.5, -15.0), (7.5, -21.0), lambda n: I[2] if n % 2 else I[3])
    tip = P(xf, (7.7, -21.6))
    mid.put_glow(tip[0], tip[1], V[3] if friendly else E[3])
    # the beacon's collar (the head, a separate sheet, sits on it)
    mid.part(xf, Ellipse(-0.5, -15.6, 5.6, 1.6), "iron", flat(2), rust=0.0)
    tread(near, -8.0, 7.0, -6.0 - lift, -0.0 - lift, 0)
    return far, mid, near, bob


ANNOY_FRAMES = 7
BEACON_FRAMES = 8


def beacon_frame(k, friendly=False):
    """The head: an emergency beacon on its collar (rest position: bob 0). A red glass dome on a brass base; the
    reflector inside turns a full circle in BEACON_FRAMES frames, and flares when it faces the viewer. `friendly`: a
    verdigris dome and light (the Alarm Head minion)."""
    G = V if friendly else E
    cv, glow = Canvas(), Canvas()
    cx, base = -0.5, -16.0
    cv.part(Xf(), box(cx - 5.0, base - 2.0, cx + 5.0, base + 0.5), "brass", fs(N_SIDE, lo=1, hi=4, bias=0.1), rust=0.0)
    for x in (-4, -1, 2):
        rivet(cv, Xf(), (cx + x, base - 1.2), "brass")
    dome_px = cv.part(Xf(), Ellipse(cx, base - 6.0, 4.8, 5.0) - box(cx - 7, base - 2.0, cx + 7, base + 3), "verd" if friendly else "ember",
                      dome(cx - 1.5, base - 8.0, 5.0, lo=1, hi=2, gain=1.15), rust=0.0)
    a = 2.0 * math.pi * k / BEACON_FRAMES
    across = math.sin(a)                                 # -1 left .. +1 right
    facing = math.cos(a)                                 # +1 towards the viewer
    rx = cx + across * 3.0
    width = 2.2 if facing > 0.3 else (1.4 if facing > -0.3 else 0.8)
    for (x, y) in dome_px:
        if abs(x + 0.5 - rx) <= width:
            glow.put_glow(x, y, G[3] if facing > -0.3 and abs(x + 0.5 - rx) < width - 0.7 else G[2])
    cv.put(int(math.floor(cx - 2.6)), int(math.floor(base - 8.5)), S[2])   # a glint on the glass
    cv.put(int(math.floor(cx - 2.6)), int(math.floor(base - 7.5)), S[1])
    cap = (int(math.floor(cx)), int(math.floor(base - 11.4)))
    cv.put(cap[0], cap[1], B[2])
    cv.put(cap[0] - 1, cap[1], B[1])
    if facing > 0.85:                                    # the flare: a cross of light
        fx, fy = int(math.floor(rx)), int(math.floor(base - 6.0))
        for d in range(6, 9):
            col = G[3] if d < 8 else G[2]
            for (dx, dy) in ((0, -d), (-d, 0), (d, 0)):
                glow.put_glow(fx + dx, fy + dy, col)
    return cv, glow


# ================================================================================================
# Blast, gores, icon
# ================================================================================================
BLAST_FRAMES = 6
BLAST_SIZE = 48                                         # 1x, centred: 96x96 in game (the blast radius is 48 px)


def blast_frame(k):
    rng = random.Random(40 + k)
    cv = Canvas()
    c = BLAST_SIZE / 2.0
    radii = (9.0, 16.0, 20.0, 22.0, 22.0, 21.0)
    r = radii[k]
    if k <= 2:
        core = cv.raster(Xf(), Ellipse(c, c, r, r))
        for (x, y) in core:
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) / r
            n = rng.random() * 0.12
            col = S[3] if d + n < 0.35 - 0.1 * k else (E[3] if d + n < 0.65 else (E[2] if d + n < 0.88 else E[1]))
            cv.put(x, y, col)
    # smoke puffs from frame 2 on, drifting outwards and up
    if k >= 2:
        puffs = 9
        for j in range(puffs):
            a = 2.0 * math.pi * j / puffs + 0.3
            dist = r * (0.55 + 0.12 * (k - 2))
            pr = max(2.0, 6.5 - 1.1 * (k - 2) + rng.random())
            px, py = c + math.cos(a) * dist, c + math.sin(a) * dist - (k - 2) * 1.5
            ring = cv.raster(Xf(), Ellipse(px, py, pr, pr))
            for (x, y) in ring:
                d = math.hypot(x + 0.5 - px + 1, y + 0.5 - py + 1) / pr
                cv.put(x, y, S[1] if d < 0.5 else (S[0] if d < 0.85 else I[2]))
        if k <= 3:
            for _ in range(10 - 3 * (k - 2)):
                a = rng.random() * 2 * math.pi
                d = rng.random() * r * 0.8
                x, y = int(c + math.cos(a) * d), int(c + math.sin(a) * d)
                cv.put(x, y, E[3])
                cv.put(x + 1, y, E[2])
    return cv


def fit_cell(canvas_sets):
    """The smallest cell (1x width, height, origin x, origin y) that holds every pixel above the ground clip of every
    canvas, with the origin on the ground point: the same cell for all of an enemy's sheets."""
    xs = [x for cvs in canvas_sets for cv in cvs for (x, y) in list(cv.px) + list(cv.glow) if y < GROUND_CLIP]
    ys = [y for cvs in canvas_sets for cv in cvs for (x, y) in list(cv.px) + list(cv.glow) if y < GROUND_CLIP]
    x0, x1, y0 = min(xs), max(xs), min(ys)
    ox = max(-x0, x1 + 1)                                # symmetric about the origin, so a flipped frame stays in place
    return (2 * ox, GROUND_CLIP - y0, ox, -y0)


def grid_layer(canvases, cell, glow=False):
    """Equal cells stacked vertically, 1 px (2 px in game) under each; every pixel must fit in its cell."""
    w, h, ox, oy = cell
    out = Image.new("RGBA", (w, (h + 1) * len(canvases)), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        for (x, y), col in src.items():
            if y >= GROUND_CLIP:
                continue
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[cx, cy + k * (h + 1)] = col + (255,)
    return out


def shifted(cv, dy):
    out = Canvas()
    for (x, y), c in cv.px.items():
        out.px[(x, y + dy)] = c
    for (x, y), c in cv.glow.items():
        out.glow[(x, y + dy)] = c
    return out


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gore_images():
    out = {}
    fr = jaeger_frame(idle_pose(0))
    mid, near = fr[1], fr[2]
    out["Jaeger_GoreHead"] = crop({p: c for p, c in mid.px.items() if p[1] <= -125 and p[0] <= 6})
    out["Jaeger_GorePauldron"] = crop({p: c for p, c in near.px.items() if p[1] <= -96})
    out["Jaeger_GoreFist"] = crop({p: c for p, c in near.px.items() if -62 <= p[1] <= -44 and p[0] >= 4})
    out["Jaeger_GoreBoot"] = crop({p: c for p, c in near.px.items() if p[1] >= -10})
    out["Jaeger_GorePlate"] = crop({p: c for p, c in mid.px.items() if -122 <= p[1] <= -100 and p[0] >= 10})
    bm = boombot_frame(BOOM_IDLE)[1]
    top = round(BOMB_CY - BOMB_R)                         # the fuse cap's lowest row
    out["Boombot_GoreShell"] = crop({p: c for p, c in bm.px.items() if p[0] <= 0 and top + 1 < p[1] <= round(BOMB_CY) + 2})
    out["Boombot_GoreLamp"] = crop({p: c for p, c in bm.px.items() if p[1] <= top + 1})   # the fuse cap and fuse
    mf = mouse_frame(0)[1]
    out["RogueMiceBot_GoreWheel"] = crop({p: c for p, c in mf.px.items() if p[1] >= -1 and p[0] >= 0})
    out["RogueMiceBot_GoreShell"] = crop({p: c for p, c in mf.px.items() if p[1] <= -2 and p[0] >= -5})
    ab = annoy_frame(4)
    out["AnnoyOTron_GoreSpeaker"] = crop({p: c for p, c in ab[1].px.items() if -2 <= p[0] <= 5 and -13 <= p[1] <= -6})
    out["AnnoyOTron_GoreBeacon"] = crop(beacon_frame(2)[0].px)
    return out


def alarm_head_icon(k=0):
    """The Alarm Head (summon item, 16x16 -> 32x32): the friendly beacon head on its brass base, lifted off the box,
    with its collar ring and a stub of the whip antenna; beacon frame `k` (0: the reflector faces the viewer)."""
    cv, glow = beacon_frame(k, friendly=True)
    out = Canvas()
    for (x, y), c in cv.px.items():
        out.put(x, y + 8, c)
    out.part(Xf(), Ellipse(-0.5, -6.6, 5.6, 1.6), "iron", flat(2), rust=0.0)       # the collar it sat on
    line(out, Xf(), (5.0, -7.0), (6.5, -11.0), lambda n: I[2] if n % 2 else I[3])   # the antenna stub
    out.put(6, -12, V[3])
    xs = [x for (x, _) in out.px]
    ys = [y for (_, y) in out.px]
    w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    return to_image(out.px, min(xs) - (16 - w) // 2, min(ys) - (16 - h) // 2, 16, 16)


def alarmobo_buff_icon():
    """Buff icon (16x16 -> 32x32): the same head with its reflector turned aside (the beacon spinning)."""
    return alarm_head_icon(2)


def icon():
    """The invasion's progress-bar icon (16x16 -> 32x32): the Jaeger's helmet in a brass cog."""
    cv = Canvas()
    c = (7.5, 7.5)
    teeth = Union(*[Capsule(c, (c[0] + math.cos(math.radians(a)) * 7.4, c[1] + math.sin(math.radians(a)) * 7.4), 1.4) for a in range(0, 360, 45)])
    cv.part(Xf(), Ellipse(c[0], c[1], 6.0, 6.0) | teeth, "brass", dome(5.5, 5.0, 8.0, lo=1, hi=5), rust=0.0)
    cv.part(Xf(), Ellipse(c[0], c[1], 4.6, 4.6), "iron", flat(1, bevel=False), rust=0.0)
    cv.part(Xf(), Poly([(3.5, 4.0), (8.0, 3.0), (8.5, 11.5), (4.0, 11.5)]), "verd", fs(N_FRONT, hi=3, bias=0.1), rust=0.0)
    cv.part(Xf(), Poly([(8.0, 3.0), (12.0, 4.0), (12.0, 11.0), (8.5, 11.5)]), "verd", fs(N_SIDE, hi=3, bias=-0.2), rust=0.0)
    for x in range(4, 9):
        cv.put(x, 7, E[3] if x < 7 else E[2])
    cv.put(9, 5, I[4])
    return to_image(cv.px, 0, 0, 16, 16)


# ================================================================================================
# Rig data and export
# ================================================================================================
LAYER_FILES = {"Body": "NPCs/Jaeger", "Glow": "NPCs/Jaeger_Glow", "Near": "NPCs/Jaeger_Near", "Far": "NPCs/Jaeger_Far"}


def write_rig_data(path, layers, frames, cells):
    L = []
    L.append("// <auto-generated> by art/mecharmy/make_mecharmy_art.py - do not edit by hand. </auto-generated>")
    L.append("namespace Cogpunk.Content.MechArmy")
    L.append("{")
    L.append("\t/// <summary>The Mech Army's sprite layout, generated with the sprites (game pixels, 2x art, left-facing; mirror X")
    L.append("\t/// when facing right). Small enemies: three grid sheets (far, middle, near: Name_Far.png, Name.png, Name_Near.png) of")
    L.append("\t/// equal cells with CellPadding px under each, origin = the ground point under the body centre. The Jaeger: packed")
    L.append("\t/// atlases like Trash-Tr0m's (FrameFields values per frame: page, x, y, w, h, origin x, origin y).</summary>")
    L.append("\tpublic static class MechArmyRigData")
    L.append("\t{")
    L.append("\t\tpublic const int CellPadding = 2;")
    for name, n in (("Mice", MOUSE_FRAMES), ("Boombot", BOOMBOT_FRAMES), ("Annoy", ANNOY_FRAMES)):
        w, h, ox, oy = cells[name]
        L.append("\t\tpublic const int %sCellWidth = %d, %sCellHeight = %d, %sOriginX = %d, %sOriginY = %d, %sFrames = %d;"
                 % (name, w * 2, name, h * 2, name, ox * 2, name, oy * 2, name, n))
    L.append("\t\tpublic const int MiceIdle = 0, MiceRun = 2, MiceRunFrames = 4, MiceLeap = 6, MiceBite = 7;")
    L.append("\t\tpublic const int BoombotRun = 0, BoombotRunFrames = %d, BoombotIdle = %d, BoombotLeap = %d, BoombotTrip = %d, "
             "BoombotFall = %d, BoombotRoll = %d, BoombotRollFrames = %d;" % (BOOM_RUN_FRAMES, BOOM_IDLE, BOOM_LEAP, BOOM_TRIP, BOOM_FALL,
                                                                           BOOM_ROLL, ROLL_FRAMES))
    L.append("\t\t/// <summary>The bomb's radius, game px: a rolling Boombot turns one roll frame per (2 pi r / roll frames) px.</summary>")
    L.append("\t\tpublic const int BoombotRadius = %d;" % round(BOMB_R * 2))
    L.append("\t\tpublic const int AnnoyDrive = 0, AnnoyDriveFrames = 4, AnnoyIdle = 4, AnnoyHop = 6;")
    L.append("\t\tpublic const int BeaconFrames = %d;" % BEACON_FRAMES)
    bobs = [annoy_frame(k)[3] * 2 for k in range(ANNOY_FRAMES)]
    L.append("\t\t/// <summary>How far the Annoy-o-tron's beacon sheet moves with each body frame (its bob), game px.</summary>")
    L.append(cs_array("AnnoyBeaconY", bobs, typ="short").rstrip("\n"))
    L.append("\t\tpublic const int BlastFrames = %d, BlastSize = %d;" % (BLAST_FRAMES, BLAST_SIZE * 2))
    L.append("")
    L.append("\t\t// Jaeger")
    L.append("\t\tpublic const int FrameFields = 7;")
    L.append("\t\tpublic const int JaegerBodyPages = %d, JaegerGlowPages = %d, JaegerNearPages = %d, JaegerFarPages = %d;"
             % tuple(layers[k][0] for k in ("Body", "Glow", "Near", "Far")))
    L.append("\t\tpublic const int JaegerWalk = 0, JaegerWalkFrames = %d, JaegerIdle = %d, JaegerIdleFrames = %d;" % (WALK_FRAMES, WALK_FRAMES, IDLE_FRAMES))
    L.append("\t\t/// <summary>Game px a planted foot slides back per walk frame: the body moves exactly this far forward on every")
    L.append("\t\t/// walk frame change (root motion), so the planted foot never slips.</summary>")
    L.append("\t\tpublic const int JaegerStep = %d;" % (WALK_STEP * 2))
    L.append("\t\t/// <summary>1 on the walk frames where a heel strikes the ground (footfall effects).</summary>")
    L.append(cs_array("JaegerFootfall", plant_frames(), typ="byte").rstrip("\n"))
    for key in ("Body", "Glow", "Near", "Far"):
        L.append("\t\t/// <summary>Jaeger %s layer: page, x, y, w, h, origin x, origin y per frame.</summary>" % key)
        L.append(cs_array("Jaeger" + key + "Frames", layers[key][1], typ="short", per_line=14).rstrip("\n"))
    L.append("\t\tpublic const int JaegerStrips = %d;" % JAEGER_STRIPS)
    vals = []
    for fr in frames:
        for r in hit_strips(merged(fr[:3]), JAEGER_STRIPS):
            vals += list(r)
    L.append("\t\t/// <summary>Contact boxes per frame (JaegerStrips strips of x0, y0, x1, y1 following the silhouette of all three")
    L.append("\t\t/// planes), relative to the rig origin.</summary>")
    L.append(cs_array("JaegerHit", vals, typ="short", per_line=16).rstrip("\n"))
    reactor = []
    for fr in frames:
        reactor += [int(round(fr[3][0] * 2)), int(round(fr[3][1] * 2))]
    L.append("\t\t/// <summary>The chest reactor's centre per frame (x, y pairs), relative to the rig origin: its light.</summary>")
    L.append(cs_array("JaegerReactor", reactor, typ="short").rstrip("\n"))
    idle = merged(frames[WALK_FRAMES][:3])
    xs = [q[0] for q in idle.px if q[1] < GROUND_CLIP]
    ys = [q[1] for q in idle.px if q[1] < GROUND_CLIP]
    L.append("\t\t/// <summary>The idle frame's bounding box (all planes; the NPC hitbox), relative to the rig origin.</summary>")
    L.append("\t\tpublic const int JaegerLeft = %d, JaegerRight = %d, JaegerTop = %d;" % (min(xs) * 2, (max(xs) + 1) * 2, min(ys) * 2))
    allx = [q[0] for fr in frames for cv in fr[:3] for q in cv.px if q[1] < GROUND_CLIP]
    ally = [q[1] for fr in frames for cv in fr[:3] for q in cv.px if q[1] < GROUND_CLIP]
    L.append("\t\tpublic const int JaegerBoundsWidth = %d, JaegerBoundsHeight = %d;" % ((max(allx) - min(allx) + 1) * 2, (max(ally) - min(ally) + 1) * 2))
    L.append("\t}")
    L.append("}")
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = jaeger_frames()
    layers = {}
    for key, idx, glow in (("Body", 1, False), ("Glow", 1, True), ("Near", 2, False), ("Far", 0, False)):
        pages, table = pack_layer([fr[idx] for fr in frames], glow)
        for k, im in enumerate(pages):
            export(im, OUT + page_name(LAYER_FILES[key], k))
        for k in range(len(pages), 8):
            stale = os.path.join(ROOT, OUT + page_name(LAYER_FILES[key], k))
            if os.path.exists(stale):
                os.remove(stale)
        layers[key] = (len(pages), table)
    cells = {}
    mice = [mouse_frame(k) for k in range(MOUSE_FRAMES)]
    cells["Mice"] = cell = fit_cell([m[:3] for m in mice])
    export(grid_layer([m[1] for m in mice], cell), OUT + "NPCs/RogueMiceBot.png")          # one plane (see mouse_frame)
    export(grid_layer([m[1] for m in mice], cell, glow=True), OUT + "NPCs/RogueMiceBot_Glow.png")
    for stale in ("NPCs/RogueMiceBot_Far.png", "NPCs/RogueMiceBot_Near.png"):
        if os.path.exists(os.path.join(ROOT, OUT + stale)):
            os.remove(os.path.join(ROOT, OUT + stale))
    boom = [boombot_frame(k) for k in range(BOOMBOT_FRAMES)]
    cells["Boombot"] = cell = fit_cell([b for b in boom])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([b[idx] for b in boom], cell), OUT + "NPCs/Boombot%s.png" % suffix)
    export(grid_layer([b[3] for b in boom], cell, glow=True), OUT + "NPCs/Boombot_Glow.png")
    annoy = [annoy_frame(k) for k in range(ANNOY_FRAMES)]
    beacons = [beacon_frame(k) for k in range(BEACON_FRAMES)]
    lowest = min(a[3] for a in annoy)                     # the beacon rides the bob: leave room for its highest position
    raised = [[shifted(b[0], lowest), shifted(b[1], lowest)] for b in beacons]
    cells["Annoy"] = cell = fit_cell([a[:3] for a in annoy] + raised)
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([a[idx] for a in annoy], cell), OUT + "NPCs/AnnoyOTron%s.png" % suffix)
    export(grid_layer([a[1] for a in annoy], cell, glow=True), OUT + "NPCs/AnnoyOTron_Glow.png")
    export(grid_layer([b[0] for b in beacons], cell), OUT + "NPCs/AnnoyOTron_Beacon.png")
    export(grid_layer([b[1] for b in beacons], cell, glow=True), OUT + "NPCs/AnnoyOTron_BeaconGlow.png")
    # the Alarm Head's minion: the same cells (MechArmyRigData.Annoy*), verdigris lights
    friendly = [annoy_frame(k, friendly=True) for k in range(ANNOY_FRAMES)]
    fbeacons = [beacon_frame(k, friendly=True) for k in range(BEACON_FRAMES)]
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([a[idx] for a in friendly], cell), OUT + "Minions/AlarmoboMinion%s.png" % suffix)
    export(grid_layer([a[1] for a in friendly], cell, glow=True), OUT + "Minions/AlarmoboMinion_Glow.png")
    export(grid_layer([b[0] for b in fbeacons], cell), OUT + "Minions/AlarmoboMinion_Beacon.png")
    export(grid_layer([b[1] for b in fbeacons], cell, glow=True), OUT + "Minions/AlarmoboMinion_BeaconGlow.png")
    export(alarm_head_icon(), OUT + "Minions/AlarmHead.png")
    export(alarmobo_buff_icon(), OUT + "Minions/AlarmoboBuff.png")
    blast = [blast_frame(k) for k in range(BLAST_FRAMES)]
    export(vertical([to_image(b.px, 0, 0, BLAST_SIZE, BLAST_SIZE) for b in blast]), OUT + "Projectiles/BoombotBlast.png")
    for name, im in gore_images().items():
        export(im, OUT + "Gores/" + name + ".png")
    export(icon(), OUT + "MechArmyIcon.png")
    write_rig_data(OUT + "MechArmyRigData.cs", layers, frames, cells)
    return frames, mice, boom, annoy, beacons, blast


def sheet_preview(path, scale=3, bg=(40, 44, 52)):
    """Every small enemy frame composited (far, middle + glow, beacon, near), one row per enemy."""
    rows = []
    for frames_fn, n in ((mouse_frame, MOUSE_FRAMES), (boombot_frame, BOOMBOT_FRAMES), (annoy_frame, ANNOY_FRAMES)):
        cvs = []
        for k in range(n):
            fr = frames_fn(k)
            layers = [fr[0], fr[1]]
            if frames_fn is annoy_frame:
                bc, bglow = beacon_frame(k % BEACON_FRAMES)
                moved = Canvas()
                for (x, y), c in list(bc.px.items()) + list(bglow.px.items()):
                    moved.put(x, y + fr[3], c)
                layers.append(moved)
            if len(fr) > 3 and isinstance(fr[3], Canvas):
                layers.append(fr[3])
            layers.append(fr[2])
            cvs.append(layers)
        rows.append(cvs)
    cw, ch = 40, 30
    out = Image.new("RGBA", (cw * max(len(r) for r in rows), ch * len(rows)), bg + (255,))
    for r, cvs in enumerate(rows):
        for k, layers in enumerate(cvs):
            for cv in layers:
                out.alpha_composite(to_image(cv.px, -cw // 2, -ch + 2, cw, ch), (k * cw, r * ch))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    out.save(path)
    print("preview", path, out.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        sheet_preview(os.path.join(a.preview, "mecharmy_small.png"))
    else:
        export_all()
