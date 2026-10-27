"""Source for Trash-Tr0m, the Junkyard boss (D4, art direction of 2026-10-26). Run from the repo root:

    python -P art/bosses/trashtr0m/make_trashtr0m_art.py [--preview DIR]

Design: the torn-off upper half of a Devastator-style construction titan, seen in a three-quarter side view (facing
left, turned towards the viewer). No legs: it leans forward on its two arms and crawls, hand over hand, dragging its
ragged waist (spine, cables, pistons) along the ground. Its huge hunched head hangs low in front of the shoulders, with
a hydraulic jaw that drops open on two grinder drums, a hazard-brass visor and three ember eyes; a verdigris shoulder
yoke, exhaust stacks and a cement-mixer drum ride on its back. Every part is a different salvaged machine.

Multiplane rig (three layers, drawn far to near; Core/Visuals/DepthLayers):
    TrashTr0m_ArmFar.png    far arm: dump-bed pauldron, crane boom, winch elbow, three-prong claw (baked one ramp step
                            darker: it is further away)
    TrashTr0m.png           body: torso, waist, stacks, drum, yoke, head, jaw (+ TrashTr0m_Glow.png: eyes, furnace,
                            throat, the live wire)
    TrashTr0m_ArmNear.png   near arm: tyre pauldron, excavator boom, gear elbow, bucket fist
Each layer is a packed atlas (pack_layer, 2026-10-26): every frame cropped to its own pixels and shelf-packed into
pages of at most 2048x2048 (TrashTr0m.png, TrashTr0m_Page1.png, ...), which is what makes room for the in-between
frames (wind-ups, strikes, settles, death tweens). Arm poses are rendered with two-bone IK for the shoulder of the body
frame they go with, so nothing is ever rotated or scaled at runtime (D4: no mixels). The frame tables (page, rectangle,
rig origin), hand contact points, the mouth point and the hit strips are written to
Content/Bosses/TrashTr0m/TrashTr0mRigData.cs for the C# code.

Crawl: a 12-frame cycle in four phases of three frames (near arm reaches / near arm drags / far arm reaches / far arm
drags). The body only moves while a planted hand drags: CRAWL_STEP px at each of the six drag transitions, exactly the
distance the planted hands move back relative to the body, so they stay nailed to the ground.

Height: 147 px at 1x = 294 px in game = 7x the player's 42 px hitbox. Lit from the top-left, every part outlined in
ramp 0 of its own material, Cogpunk palette only, 48-colour boss cap.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import (RAMP, WHITE, Xf, Poly, Ellipse, Ring, Capsule, Union, box, Canvas, flat, face, dome,  # noqa: E402
                 cyl, rivet, bolt, seam, line, weld, stripes, grime, ik)

ROOT = os.getcwd()
OUT = "Content/Bosses/TrashTr0m/"
I, B, C, V, E, S, LE = (RAMP[k] for k in ("iron", "brass", "copper", "verd", "ember", "steam", "leather"))


def P(xf, p):
    """Rig point -> integer pixel."""
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def fs(n, lo=1, hi=4, gain=1.3, bias=0.0, bevel=True):
    """Shader for a flat face with rig-space normal n (turned again by the part transform for posed frames)."""
    return face(n, lo=lo, hi=hi, gain=gain, bias=bias, bevel=bevel, ramp_len=hi + 1)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ================================================================================================
# Body - hand-placed massing in rig space (neutral pose). Normals are (x, y, z), z towards the viewer.
# ================================================================================================
WAIST_PIVOT = (52.0, -14.0)                            # body poses rotate about the torn waist
HUMP = (6.0, -114.0, 62.0, 33.0, -12.0)                # shoulder yoke dome: centre, radii, rotation (deg)
CHEST_FRONT = [(-50, -112), (-8, -122), (12, -86), (0, -46), (-20, -40), (-42, -62)]
CHEST_SIDE = [(-8, -122), (58, -116), (84, -78), (90, -40), (62, -24), (22, -26), (0, -46), (12, -86)]
BELLY = [(-20, -40), (0, -46), (22, -26), (16, -14), (-2, -22)]
N_FRONT = (-0.8, 0.15, 0.58)
N_SIDE = (0.32, -0.08, 0.94)
N_BELLY = (-0.45, 0.75, 0.5)
STACKS = [((44, -130), (54, -162), 4.0), ((60, -124), (68, -152), 3.2)]
DRUM = ((26, -150), (80, -132), 15.0, 11.0)
TEAR = [(16, -14), (22, -26), (62, -24), (90, -40), (98, -20), (92, -7), (80, -3), (62, -7), (46, -4), (30, -8)]
NECK = (-40.0, -98.0)
HEAD_ORIGIN = (-64.0, -40.0)                           # bottom centre of the helmet box (neutral)


class BodyPose:
    def __init__(self, lean=0.0, drop=0.0, head=(0.0, 0.0), head_tilt=0.0, jaw=0.0, grind=0, eyes=1.0,
                 drum=0, breathe=0, wreck=0):
        self.lean, self.drop, self.head, self.head_tilt = lean, drop, head, head_tilt
        self.jaw, self.grind, self.eyes, self.drum, self.breathe, self.wreck = jaw, grind, eyes, drum, breathe, wreck


def body_xf(pose):
    """Whole-body pose: rotate about the waist (positive = clockwise = leaning further forward... for a left-facing
    body the top swings left when the angle is negative) and drop."""
    return Xf.pose(pose.lean, WAIST_PIVOT, (0.0, pose.drop))


def exhaust_stacks(cv, xf, pose):
    for base, top, r in STACKS:
        top = (top[0], top[1] + pose.breathe)
        inner = cv.part(xf, Capsule(base, top, r), "iron", cyl(base, top, r, lo=1, hi=4, gain=1.5), shadow=(1, 1))
        ux, uy = top[0] - base[0], top[1] - base[1]
        ln = math.hypot(ux, uy)
        ux, uy = ux / ln, uy / ln
        rim_a, rim_b = (top[0] - ux * 1.5, top[1] - uy * 1.5), (top[0] + ux * 2.5, top[1] + uy * 2.5)
        cv.part(xf, Capsule(rim_a, rim_b, r + 1.4), "brass", cyl(rim_a, rim_b, r + 1.4, lo=2, hi=5, gain=1.6))
        mx, my = P(xf, (top[0] + ux * 2.5, top[1] + uy * 2.5))
        for dx in (-1, 0, 1):
            cv.put(mx + dx, my, I[0])
        for t in (0.3, 0.55, 0.8):
            p = lerp(base, top, t)
            line(cv, xf, (p[0] - r + 1, p[1]), (p[0] + r - 1, p[1]), lambda n: B[3] if n < 2 else B[1], inner)


def mixer_drum(cv, xf, pose, rng):
    """A cement-mixer drum riding across the back, its spiral fins drifting with pose.drum."""
    a, b, r0, r1 = DRUM
    inner = cv.part(xf, Capsule(a, b, r0, r1), "verd", cyl(a, b, (r0 + r1) / 2, lo=1, hi=3, gain=1.35, bias=0.05), shadow=(2, 2))
    ax, ay = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(ax, ay)
    ux, uy = ax / ln, ay / ln
    nx, ny = -uy, ux
    for k in range(6):
        t = ((k * 8 + pose.drum * 2) % 48) / 48.0
        c = lerp(a, b, t)
        rr = r0 + (r1 - r0) * t
        p0 = (c[0] + nx * rr * 0.95 - ux * 3, c[1] + ny * rr * 0.95 - uy * 3)
        p1 = (c[0] - nx * rr * 0.95 + ux * 3, c[1] - ny * rr * 0.95 + uy * 3)
        line(cv, xf, p0, p1, lambda n: V[0], inner)
        line(cv, xf, (p0[0] + 1, p0[1]), (p1[0] + 1, p1[1]), lambda n: V[3] if n % 3 else V[2], inner)
    for t in (0.06, 0.94):
        c = lerp(a, b, t)
        rr = r0 + (r1 - r0) * t
        hin = cv.part(xf, Capsule((c[0] + nx * rr, c[1] + ny * rr), (c[0] - nx * rr, c[1] - ny * rr), 1.6), "brass", flat(3))
        for s_ in (-0.6, 0.0, 0.6):
            rivet(cv, xf, (c[0] + nx * rr * s_, c[1] + ny * rr * s_), "brass", hin)
    grime(cv, inner, rng, 0.05, [V[0], C[1], LE[0]])
    cv.part(xf, Ellipse(b[0] + ux * 2, b[1] + uy * 2, 5.5, 8.0), "iron", flat(1, bevel=False))
    cv.part(xf, Ellipse(b[0] + ux * 2.5, b[1] + uy * 2.5, 3.0, 5.0), "leather", flat(1, bevel=False), outline=False)


def waist(cv, xf, pose, rng, glow=True):
    """The torn waist: a ragged rim of bright metal, the spine, pistons and cables dragging on the ground."""
    rin = cv.part(xf, Poly(TEAR), "iron", flat(1, bevel=False))
    jag = (0, 2, 1, 3, 1, 2, 0, 3)
    for k, (a, b) in enumerate(zip(TEAR[3:9], TEAR[4:10])):
        for n in range(6):
            p = lerp(a, b, n / 6)
            q = P(xf, (p[0], p[1] - 1 - jag[(k * 6 + n) % 8]))
            if q in rin:
                cv.put(q[0], q[1], I[4] if n % 2 == 0 else I[3])
    for k in range(5):                                    # exposed spine
        c = (58 + k * 7, -8 + k * 0.8)
        cv.part(xf, Ellipse(c[0], c[1], 3.4 - k * 0.3, 2.4), "iron", dome(c[0], c[1], 3.4, lo=1, hi=4))
    for (p0, p1, r, ramp) in (((26, -12), (22, -2), 2.8, "iron"), ((44, -8), (36, -1.5), 2.2, "brass")):
        cv.part(xf, Capsule(p0, p1, r), ramp, cyl(p0, p1, r, lo=1, hi=4 if ramp == "iron" else 5, gain=1.5))
        cv.part(xf, Capsule(p1, (p1[0] - 2, p1[1] + 0.5), r * 0.55), "steam", flat(2, bevel=False))
    cables = (((50, -6), [(-12, 4), (-26, 5), (-38, 5)], "copper"),
              ((64, -5), [(10, 3), (22, 4), (32, 5)], "ember"),
              ((72, -4), [(14, 2), (26, 4), (42, 5)], "verd"),
              ((56, -6), [(-2, 4), (-10, 5), (-16, 5)], "brass"))
    for (start, offs, ramp) in cables:
        pts = [start] + [(start[0] + dx, min(-1.0, start[1] + dy)) for dx, dy in offs]
        r = RAMP[ramp]
        for a, b in zip(pts, pts[1:]):
            line(cv, xf, a, b, lambda k: r[1])
            line(cv, xf, (a[0], a[1] - 1), (b[0], b[1] - 1), lambda k: r[2] if k % 4 else r[3])
    if glow:                                              # the live wire sparks at its cut end
        ex, ey = P(xf, (96.0, -1.5))
        cv.put_glow(ex, ey, E[3])
        cv.put_glow(ex + 1, ey - 1, E[2])


def body_mass(cv, xf, pose, rng):
    """Chest (front, facing down-left), the near side wall down to the waist, and the belly."""
    side = cv.part(xf, Poly(CHEST_SIDE), "iron", fs(N_SIDE, bias=-0.1), shadow=(2, 2))
    belly = cv.part(xf, Poly(BELLY), "iron", fs(N_BELLY, hi=3, gain=1.2, bias=-0.2))
    front = cv.part(xf, Poly(CHEST_FRONT), "iron", fs(N_FRONT, bias=0.15), shadow=(1, 1))
    for (p0, p1) in (((12, -88), (82, -80)), ((6, -60), (88, -54)), ((40, -118), (44, -27))):
        seam(cv, xf, p0, p1, "iron", side)
    plate = Poly([(46, -76), (84, -70), (88, -42), (48, -40)])
    pin = cv.part(xf, plate, "brass", fs(N_SIDE, lo=2, gain=1.2, bias=-0.1), shadow=(1, 1))
    strip = cv.raster(xf, Poly([(46, -50), (88, -50), (88, -40), (46, -40)])) & pin
    stripes(cv, strip, 3, B[4], I[0], slope=1)
    for k in range(5):
        rivet(cv, xf, (50 + k * 7.5, -73 + k * 0.6), "brass", pin)
    grime(cv, pin - strip, rng, 0.04, [B[1], C[1]])
    rad = Poly([(14, -112), (38, -114), (40, -92), (16, -90)])
    rin = cv.part(xf, rad, "iron", flat(1, bevel=False))
    for p in rin:
        if p[1] % 2 == 0:
            cv.put(p[0], p[1], I[3] if p[0] % 5 else I[2])
    rust = Poly([(12, -54), (36, -54), (36, -32), (16, -30)])
    ruin = cv.part(xf, rust, "copper", fs(N_SIDE, hi=3, gain=1.1, bias=-0.15))
    for q in ((15, -51), (32, -51), (17, -34), (32, -34)):
        rivet(cv, xf, q, "copper", ruin)
    grime(cv, ruin, rng, 0.08, [C[1], C[3]])
    verd = Poly([(52, -110), (66, -108), (72, -88), (54, -88)])
    vin = cv.part(xf, verd, "verd", fs(N_SIDE, hi=3, gain=1.1, bias=-0.1))
    weld(cv, xf, (8, -58), (40, -56), side)
    weld(cv, xf, (50, -86), (80, -82), side)
    for k in range(10):
        rivet(cv, xf, (8 + k * 8, -118 + k * 0.8), "iron", side)
    for k in range(6):
        rivet(cv, xf, (86, -68 + k * 5), "iron", side)
    grime(cv, side - pin - rin - ruin - vin, rng, 0.005, [I[1], C[1]])
    # a recessed machinery gap along the chest-side seam: dark, with a gear turning in it
    gap = Poly([(36, -86), (46, -88), (48, -58), (38, -56)])
    gin = cv.part(xf, gap, "iron", flat(0, bevel=False))
    gc = (42.0, -72.0)
    teeth = Union(*[Capsule(gc, (gc[0] + math.cos(math.radians(a + pose.drum * 15)) * 6.0, gc[1] + math.sin(math.radians(a + pose.drum * 15)) * 6.0), 1.2)
                    for a in range(0, 360, 45)])
    cv.part(xf, Ellipse(gc[0], gc[1], 4.4, 4.4) | teeth, "brass", dome(gc[0] - 1, gc[1] - 1, 6, lo=1, hi=4), clip=gin | cv.raster(xf, gap))
    # the big hydraulic ram that holds the torso up, from the hip to under the shoulder, and a cable bundle beside it
    hydraulic(cv, xf, (74.0, -30.0), (20.0, -96.0), 4.6, frac=0.55)
    for k, (ramp, off) in enumerate((("copper", 0.0), ("leather", 3.0), ("verd", 6.0))):
        pts = [(88 - off * 0.3, -66 + off), (66, -52 + off), (40, -44 + off * 0.8), (14, -48 + off * 0.6)]
        r = RAMP[ramp]
        for a, b in zip(pts, pts[1:]):
            line(cv, xf, a, b, lambda n: r[1])
            line(cv, xf, (a[0], a[1] - 1), (b[0], b[1] - 1), lambda n: r[2] if n % 5 else r[-1])
        for q in pts[1:3]:
            cv.part(xf, Capsule((q[0] - 1.5, q[1] - 1), (q[0] + 1.5, q[1] - 1), 1.6), "brass", flat(3))
    # chest front: the furnace grate (embers glow between the bars), rivets and a pressure gauge
    fur = Poly([(-32, -98), (-6, -104), (4, -72), (-22, -64)])
    finner = cv.part(xf, fur, "iron", flat(1, bevel=False))
    for p in finner:
        if p[0] % 3 == 0:
            cv.put(p[0], p[1], I[3] if p[1] % 4 else I[2])
        elif (p[0] + p[1]) % 7 == 0:
            cv.put(p[0], p[1], E[1])
        else:
            cv.put_glow(p[0], p[1], E[3] if (p[0] * 3 + p[1]) % 5 else E[2])
    for k in range(5):
        rivet(cv, xf, (-42 + k * 7, -108 - k * 1.2), "iron", front)
    gx, gy = -10.0, -56.0
    cv.part(xf, Ellipse(gx, gy, 5.5, 5.5), "brass", dome(gx, gy, 5.5, lo=2, hi=5), shadow=(1, 1))
    for p in cv.raster(xf, Ellipse(gx, gy, 3.5, 3.5)):
        cv.put(p[0], p[1], S[2] if (p[0] + p[1]) % 6 else S[1])
    line(cv, xf, (gx, gy), (gx + 2.5, gy - 2), lambda n: E[1])
    for p in belly:
        if p[1] % 2 == 0:
            cv.put(p[0], p[1], I[1] if p[0] % 4 else I[2])
    return side, front


def yoke(cv, xf, pose, rng):
    """The shoulder yoke: a great rounded armour shell over the shoulders - the hunch of the silhouette."""
    cx, cy, rx, ry, ang = HUMP
    cy += pose.breathe
    yx = xf.then(Xf.pose(ang, (cx, cy)))
    cut = box(cx - rx - 2, cy + ry * 0.55, cx + rx + 2, cy + ry + 2)
    shell = Ellipse(cx, cy, rx, ry) - cut
    yin = cv.part(yx, shell, "verd", dome(cx - rx * 0.35, cy - ry * 0.55, rx * 1.15, lo=1, hi=3, gain=1.35, bias=0.2), shadow=(3, 3))
    rim_band = cv.raster(yx, box(cx - rx, cy + ry * 0.3, cx + rx, cy + ry * 0.55)) & yin
    stripes(cv, rim_band, 3, B[4], I[0], slope=-1)
    for k, off in enumerate((-0.55, -0.15, 0.2)):        # overlapping armour lames: dark lip, lit edge below
        edge = []
        for n in range(-24, 25):
            ex = cx + rx * n / 25.0
            u = (ex - cx) / rx
            ey = cy + ry * off - ry * 0.55 * (1 - u * u) + ry * 0.55
            edge.append((ex, ey))
        for a, b in zip(edge, edge[1:]):
            line(cv, yx, a, b, lambda n: V[0], yin)
            line(cv, yx, (a[0], a[1] + 1), (b[0], b[1] + 1), lambda n: V[3], yin)
        for n in range(-4, 5):
            ex = cx + rx * n * 0.2
            u = (ex - cx) / rx
            ey = cy + ry * off - ry * 0.55 * (1 - u * u) + ry * 0.55 + 3
            rivet(cv, yx, (ex, ey), "verd", yin)
    grime(cv, yin - rim_band, rng, 0.004, [V[0]])
    for (x, y) in ((cx - rx * 0.5, cy - ry * 0.62), (cx - rx * 0.46, cy - ry * 0.7), (cx - rx * 0.42, cy - ry * 0.76)):
        q = P(yx, (x, y))
        if q in yin:
            cv.put(q[0], q[1], WHITE)
    return yin


# --- the head ---------------------------------------------------------------------------------------------------
class Head:
    """The helmet: a box-like housing (front = face plate facing down-left, near side, rounded top) placed by hxf."""

    def __init__(self, pose):
        ox, oy = HEAD_ORIGIN
        self.hxf = Xf.pose(pose.head_tilt, (ox, oy - 26), (pose.head[0], pose.head[1]))
        # face plate (front), near side and top, in head space
        self.front = [(-106, -90), (-64, -98), (-56, -30), (-100, -22)]
        self.near = [(-64, -98), (-30, -92), (-26, -34), (-56, -30)]
        self.top = [(-104, -92), (-70, -108), (-32, -102), (-30, -92), (-64, -98)]
        self.n_front, self.n_near, self.n_top = (-0.85, 0.1, 0.52), (0.4, 0.0, 0.92), (-0.2, -0.85, 0.48)
        self.hinge = (-46, -46)                           # jaw hinge (near side, low)

    def f(self, u, v):
        """A point on the face plate: u from its left edge to its right, v from top to bottom."""
        q = self.front
        a, b = lerp(q[0], q[1], u), lerp(q[3], q[2], u)
        return lerp(a, b, v)

    def n(self, u, v):
        q = self.near
        a, b = lerp(q[0], q[1], u), lerp(q[3], q[2], u)
        return lerp(a, b, v)

    def fquad(self, u0, v0, u1, v1):
        return Poly([self.f(u0, v0), self.f(u1, v0), self.f(u1, v1), self.f(u0, v1)])

    def nquad(self, u0, v0, u1, v1):
        return Poly([self.n(u0, v0), self.n(u1, v0), self.n(u1, v1), self.n(u0, v1)])


def neck(cv, xf, pose):
    a, b = (NECK[0] + 16, NECK[1] - 4), (-40 + pose.head[0], -76 + pose.head[1])
    cv.part(xf, Capsule(a, b, 12.0, 10.0), "iron", cyl(a, b, 11.0, lo=1, hi=3, gain=1.3, bands=3), shadow=(1, 2))


def head(cv, bxf, pose, rng):
    """Helmet: a verdigris cranium with a riveted crest, a heavy hazard-brass brow angled down over a dark eye slot
    with three ember eyes, an iron face plate with vents, and steel fangs over the jaw."""
    h = Head(pose)
    xf = bxf.then(h.hxf)
    top = cv.part(xf, Poly(h.top), "verd", fs(h.n_top, hi=3, gain=1.3, bias=0.15), shadow=(2, 3))
    near = cv.part(xf, Poly(h.near), "verd", fs(h.n_near, hi=3, gain=1.3, bias=-0.1), shadow=(2, 3))
    front = cv.part(xf, Poly(h.front), "iron", fs(h.n_front, hi=3, gain=1.2, bias=-0.1), shadow=(1, 2))
    crown = Ellipse(-66, -100, 36, 10)
    cv.part(xf.then(Xf.pose(-8, (-66, -100))), crown, "verd", dome(-74, -104, 34, lo=1, hi=3, gain=1.3, bias=0.2), shadow=(1, 2))
    crest = Poly([(-94, -104), (-40, -112), (-38, -119), (-76, -117)])
    crin = cv.part(xf, crest, "brass", flat(3, hi=4), shadow=(1, 2))
    for k in range(5):
        rivet(cv, xf, (-86 + k * 10, -110.5 - k * 1.1), "brass", crin)
    for k in range(4):                                    # near side: cheek vents and rivet rows
        seam(cv, xf, h.n(0.18, 0.34 + k * 0.09), h.n(0.62, 0.34 + k * 0.09), "verd", near, dark=0, light=3)
    for k in range(5):
        rivet(cv, xf, h.n(0.1 + k * 0.2, 0.07), "verd", near)
        rivet(cv, xf, h.n(0.9, 0.15 + k * 0.16), "verd", near)
    grime(cv, near, rng, 0.02, [V[0], C[1]])
    # eye slot: a dark recess under the brow; three narrow eyes with hot cores
    slot = cv.raster(xf, Poly([h.f(-0.02, 0.15), h.f(1.0, 0.1), h.f(1.0, 0.27), h.f(-0.02, 0.3)])) & front
    for p in slot:
        cv.put(p[0], p[1], I[0])
    for k, u in enumerate((0.08, 0.38, 0.68)):
        d = k * 0.012
        eye = cv.raster(xf, Poly([h.f(u, 0.2 - d), h.f(u + 0.22, 0.17 - d), h.f(u + 0.22, 0.225 - d), h.f(u, 0.255 - d)])) & slot
        xs = [q[0] for q in eye] or [0]
        x0, x1 = min(xs), max(xs)
        for q in eye:
            if pose.eyes >= 1:
                cv.put_glow(q[0], q[1], E[3] if x0 + 1 <= q[0] <= x1 - 1 else E[2])
            elif pose.eyes > 0:
                cv.put_glow(q[0], q[1], E[1])
            else:
                cv.put(q[0], q[1], I[1])
    # brow: a thick brass bar angled down towards the front, hazard-striped on its lower lip
    brow = Poly([h.f(-0.08, -0.02), h.f(1.06, -0.04), h.f(1.06, 0.1), h.f(-0.08, 0.17)])
    bin_ = cv.part(xf, brow, "brass", fs(h.n_front, lo=2, hi=5, gain=1.1, bias=0.25), shadow=(0, 3))
    lip = cv.raster(xf, Poly([h.f(-0.08, 0.11), h.f(1.06, 0.06), h.f(1.06, 0.1), h.f(-0.08, 0.17)])) & bin_
    stripes(cv, lip, 2, B[4], I[0], slope=-1)
    for k in range(6):
        rivet(cv, xf, h.f(0.03 + k * 0.18, 0.04 - k * 0.006), "brass", bin_)
    q = P(xf, h.f(0.06, 0.02))
    cv.put(q[0], q[1], WHITE)
    # face plate between the eyes and the mouth: vents and bolts
    plate = cv.part(xf, h.fquad(0.0, 0.31, 1.0, 0.44), "iron", fs(h.n_front, gain=1.2, bias=0.1), shadow=(0, 1))
    for k in range(5):
        bolt(cv, xf, h.f(0.08 + k * 0.2, 0.345), "brass", plate)
    for k in range(3):
        seam(cv, xf, h.f(0.2 + k * 0.25, 0.38), h.f(0.32 + k * 0.25, 0.38), "iron", plate, dark=0, light=3)
    for k in range(7):                                    # upper fangs hanging from the lip
        p = h.f(0.05 + k * 0.148, 0.44)
        cv.part(xf, Poly([(p[0] - 2.2, p[1] - 1.0), (p[0] + 2.2, p[1] - 1.0), (p[0] + 0.4, p[1] + 4.0)]), "steam", flat(1, bevel=False))
    for q2 in ((-80, -90), (-79, -91)):
        p = P(xf, q2)
        if p in top:
            cv.put(p[0], p[1], WHITE)
    return h, xf


def jaw_and_mouth(cv, xf, h, pose, rng):
    """The hydraulic jaw: a heavy bucket hinged low on the cheek. It drops open (pose.jaw 0..1) on a throat with two
    grinder drums turning in opposite directions around a glowing vortex. Returns the mouth point (rig space)."""
    open_deg = -40.0 * pose.jaw                           # negative = counter-clockwise: the jaw's front swings down
    jxf = xf.then(Xf.pose(open_deg, h.hinge))
    up_l, up_r = h.f(0.0, 0.44), h.f(1.0, 0.44)
    lo_l, lo_r = h.f(0.0, 1.0), h.f(1.0, 1.0)
    mouth_local = lerp(lerp(up_l, up_r, 0.35), lerp(lo_l, lo_r, 0.35), 0.3 + 0.25 * pose.jaw)
    if pose.jaw > 0.05:
        jl, jr = jxf.fwd(lerp(up_l, lo_l, 0.15)), jxf.fwd(lerp(up_r, lo_r, 0.15))
        cav = Poly([xf.fwd(up_l), xf.fwd((up_r[0] + 4, up_r[1])), xf.fwd(h.n(0.1, 0.95)), (jr[0], jr[1]), (jl[0], jl[1])])
        cin = cv.part(Xf(), cav, "iron", flat(0, bevel=False), outline=False)
        mx, my = xf.fwd(mouth_local)
        for p in cin:
            d = math.hypot(p[0] + 0.5 - mx, (p[1] + 0.5 - my) * 1.2)
            ang = math.atan2(p[1] + 0.5 - my, p[0] + 0.5 - mx)
            if d < 2.5 * pose.jaw + 1:
                cv.put_glow(p[0], p[1], E[3])
            elif d < 5.0 * pose.jaw + 1.5:
                cv.put_glow(p[0], p[1], E[2])
            elif d < 8.5 * pose.jaw + 2:
                cv.put_glow(p[0], p[1], E[1])
            elif int(ang * 2.0 / math.pi * 3 + d * 0.35 + pose.grind * 0.75) % 3 == 0:
                cv.put(p[0], p[1], I[1])                  # the vortex arms, turning with the grinder
        for (dxf, pa, pb, sgn) in ((xf, up_l, up_r, 1), (jxf, lerp(up_l, lo_l, 0.14), lerp(up_r, lo_r, 0.14), -1)):
            pa2 = (pa[0] + 2, pa[1] + 3.0 * sgn)
            pb2 = (pb[0] + 1, pb[1] + 3.0 * sgn)
            cv.part(dxf, Capsule(pa2, pb2, 3.4), "iron", cyl(pa2, pb2, 3.4, lo=1, hi=4, gain=1.5))
            ln = math.hypot(pb2[0] - pa2[0], pb2[1] - pa2[1])
            for k in range(int(ln // 4) + 2):
                t = (k * 4 + (pose.grind * 2 * sgn) % 4) / ln
                if 0.03 <= t <= 0.97:
                    q = lerp(pa2, pb2, t)
                    a1 = P(dxf, (q[0], q[1] + 3.8 * sgn))
                    a2 = P(dxf, (q[0], q[1] + 5.2 * sgn))
                    cv.put(a1[0], a1[1], S[2])
                    cv.put(a2[0], a2[1], I[3])
                    cv.put(a2[0] + 1, a2[1], I[1])
    # the jaw: side wall (brass, hazard stripes) behind, front face (dark iron, brass lip and big teeth) in front
    side = Poly([up_r, (up_r[0] + 10, up_r[1] - 2), (lo_r[0] + 12, lo_r[1] - 6), (lo_r[0] + 2, lo_r[1] + 2)])
    sin_ = cv.part(jxf, side, "brass", fs(h.n_near, lo=1, hi=4, gain=1.2, bias=-0.15), shadow=(1, 2))
    band = Poly([lerp(up_r, lo_r, 0.55), (up_r[0] + 10, up_r[1] + 13), (lo_r[0] + 12, lo_r[1] - 12), lerp(up_r, lo_r, 0.75)])
    stripes(cv, cv.raster(jxf, band) & sin_, 3, B[4], I[0])
    for k in range(3):
        rivet(cv, jxf, (up_r[0] + 5, up_r[1] + 6 + k * 9), "brass", sin_)
    jaw = Poly([(up_l[0] - 2, up_l[1] + 1), (up_r[0] + 1, up_r[1] + 1), (lo_r[0] + 2, lo_r[1] + 2), (lo_l[0] - 4, lo_l[1] + 4)])
    jin = cv.part(jxf, jaw, "iron", fs(h.n_front, hi=4, gain=1.25, bias=-0.05), shadow=(1, 2))
    lipb = cv.raster(jxf, Poly([(up_l[0] - 2, up_l[1] + 1), (up_r[0] + 1, up_r[1] + 1), lerp(up_r, lo_r, 0.14), lerp(up_l, lo_l, 0.14)])) & jin
    for p in lipb:
        cv.put(p[0], p[1], B[4] if (p[0], p[1] - 1) not in lipb else B[3])
    chin = cv.raster(jxf, Poly([lerp(up_l, lo_l, 0.72), lerp(up_r, lo_r, 0.72), lerp(up_r, lo_r, 0.82), lerp(up_l, lo_l, 0.82)])) & jin
    stripes(cv, chin, 3, B[4], I[0])
    for k in range(6):
        p = lerp(up_l, up_r, 0.1 + k * 0.155)
        cv.part(jxf, Poly([(p[0] - 2.4, p[1] + 2.0), (p[0] + 2.4, p[1] + 2.0), (p[0] + 0.3, p[1] - 4.0)]), "steam", flat(1, bevel=False))
    for k in range(4):
        bolt(cv, jxf, lerp(lerp(up_l, lo_l, 0.45), lerp(up_r, lo_r, 0.45), 0.12 + k * 0.25), "brass", jin)
    for k in range(3):
        seam(cv, jxf, lerp(lerp(up_l, lo_l, 0.25), lerp(up_r, lo_r, 0.25), 0.2 + k * 0.3),
             lerp(lerp(up_l, lo_l, 0.65), lerp(up_r, lo_r, 0.65), 0.2 + k * 0.3), "iron", jin, dark=0, light=3)
    grime(cv, jin - chin - lipb, rng, 0.02, [I[1], C[1]])
    # the jaw ram on the cheek: cylinder on the helmet, chrome rod down to the jaw
    r0 = h.n(0.45, 0.45)
    r1 = xf.inv(jxf.fwd((up_r[0] + 7, up_r[1] + 20)))
    cv.part(xf, Capsule(r0, lerp(r0, r1, 0.6), 2.6), "iron", cyl(r0, r1, 2.6, lo=2, hi=4, gain=1.6))
    cv.part(xf, Capsule(lerp(r0, r1, 0.55), r1, 1.3), "steam", flat(2, bevel=False))
    cv.part(xf, Ellipse(h.hinge[0], h.hinge[1], 3.4, 3.4), "brass", dome(h.hinge[0], h.hinge[1], 3.4, lo=2, hi=5))
    return xf.fwd(mouth_local)


def draw_body(pose, rng_seed=7):
    rng = random.Random(rng_seed)
    cv = Canvas()
    bxf = body_xf(pose)
    exhaust_stacks(cv, bxf, pose)
    mixer_drum(cv, bxf, pose, rng)
    waist(cv, bxf, pose, rng)
    body_mass(cv, bxf, pose, rng)
    yoke(cv, bxf, pose, rng)
    neck(cv, bxf, pose)
    h, hxf = head(cv, bxf, pose, rng)
    mouth = jaw_and_mouth(cv, hxf, h, pose, rng)
    return cv, {"mouth": mouth}


# ================================================================================================
# Arms - two-bone IK, rendered per pose (no runtime rotation)
# ================================================================================================
SHOULDER_NEAR = (4.0, -94.0)
SHOULDER_FAR = (-34.0, -112.0)
NEAR_L1, NEAR_L2 = 50.0, 58.0
FAR_L1, FAR_L2 = 66.0, 70.0
AS = 1.5                                               # arm scale: the arms were drawn at 1.0 and read too thin
NEAR_GRIP = (4.0, -24.0)                               # wrist relative to the fist's contact point (planted)
FAR_GRIP = (5.0, -22.0)
CRAWL_STEP = 3                                         # 1x px the body moves per drag transition (6 px in game)
NEAR_FRONT, FAR_FRONT = -34.0, -126.0                  # contact x where each hand plants


def seg_xf(p0, p1):
    """Local frame of a limb segment: x along it from p0, y across it."""
    return Xf.pose(math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])), (0.0, 0.0), p0)


def hydraulic(cv, xf, a, b, r, depth=0, frac=0.58):
    """A hydraulic ram from a to b (local): iron cylinder, chrome rod, brass collar."""
    m = lerp(a, b, frac)
    cv.part(xf, Capsule(a, m, r), "iron", cyl(a, m, r, lo=1, hi=4, gain=1.6), depth=depth)
    cv.part(xf, Capsule(m, b, r * 0.5), "steam", cyl(m, b, r * 0.5, lo=0, hi=3, gain=1.4), depth=depth)
    c0, c1 = lerp(a, b, frac - 0.05), lerp(a, b, frac + 0.01)
    cv.part(xf, Capsule(c0, c1, r + 0.8), "brass", flat(3), depth=depth)


def near_arm(cv, shoulder, wrist, hand_angle=0.0, bend=1, rng=None, stub=False):
    """Excavator arm: tyre pauldron, brass boom with a ram, gear elbow, hazard forearm, iron knuckle fist."""
    rng = rng or random.Random(11)
    elbow, wrist = ik(shoulder, wrist, NEAR_L1, NEAR_L2, bend)
    # forearm (drawn first: the elbow gear and upper arm overlap its top end)
    fx = seg_xf(elbow, wrist)
    lf = math.hypot(wrist[0] - elbow[0], wrist[1] - elbow[1])
    fore = cv.part(fx, Capsule((0, 0), (lf, 0), 12.5, 15.0), "brass", cyl((0, 0), (lf, 0), 14.0, lo=1, hi=4, gain=1.3, bias=0.05), shadow=(3, 3))
    for u in (0.3, 0.62):
        seam(cv, fx, (lf * u, -14), (lf * u, 14), "brass", fore, dark=1, light=4)
    band = cv.raster(fx, box(lf * 0.66, -16, lf * 0.84, 16)) & fore
    stripes(cv, band, 3, B[4], I[0])
    plate = cv.part(fx, box(lf * 0.06, -6, lf * 0.6, 10), "iron", cyl((0, 2), (lf, 2), 9, lo=1, hi=4, gain=1.2), shadow=(1, 1))
    for k in range(5):
        rivet(cv, fx, (lf * (0.1 + k * 0.11), -8.5), "brass", fore)
    for k in range(4):
        bolt(cv, fx, (lf * (0.12 + k * 0.13), 6), "brass", plate)
    grime(cv, fore - band, rng, 0.02, [B[1], C[1]])
    hydraulic(cv, fx, (lf * 0.08, 14.0), (lf * 0.85, 15.5), 3.6)
    # fist: knuckles forward-down, flat on the ground when planted
    hx = Xf.pose(hand_angle, (0.0, 0.0), wrist).then(Xf(AS, 0, 0, AS, 0, 0))
    back = Poly([(-6, -9), (10, -8), (13, 4), (9, 16), (-14, 16), (-17, 8), (-13, -4)])
    bk = cv.part(hx, back, "iron", face((0.2, -0.5, 0.84), lo=1, hi=4, gain=1.25, bias=0.1, ramp_len=5), shadow=(2, 2))
    for k in range(4):                                    # four curled knuckles along the front
        kx, ky = -14.5 + k * 0.6, -1.0 + k * 4.2
        cv.part(hx, Ellipse(kx, ky, 4.4, 3.0), "iron", dome(kx - 1, ky - 1, 4.4, lo=1, hi=4, gain=1.3), shadow=(1, 1))
    guard = cv.part(hx, Poly([(-6, -10), (10, -9), (12, 2), (-8, 3)]), "brass", face((0.1, -0.7, 0.7), lo=2, hi=5, gain=1.2, bias=0.15, ramp_len=6), shadow=(1, 2))
    stripes(cv, cv.raster(hx, box(-8, -2, 12, 2)) & guard, 2, B[4], I[0])
    for (x, y) in ((-2, -6), (6, -6)):
        bolt(cv, hx, (x, y), "brass", guard)
    for (x, y) in ((-9, 13), (-1, 13), (6, 13)):
        rivet(cv, hx, (x, y), "iron", bk)
    # elbow: a toothed gear with a brass hub
    teeth = Union(*[Capsule(elbow, (elbow[0] + math.cos(math.radians(a)) * 14.5, elbow[1] + math.sin(math.radians(a)) * 14.5), 2.6)
                    for a in range(0, 360, 36)])
    cv.part(Xf(), Ellipse(elbow[0], elbow[1], 12.0, 12.0) | teeth, "iron", dome(elbow[0] - 3, elbow[1] - 3, 14.5, lo=1, hi=4, gain=1.1), shadow=(2, 2))
    for k in range(6):
        a = math.radians(k * 60 + 30)
        rivet(cv, Xf(), (elbow[0] + math.cos(a) * 8.5, elbow[1] + math.sin(a) * 8.5), "iron")
    cv.part(Xf(), Ellipse(elbow[0], elbow[1], 5.4, 5.4), "brass", dome(elbow[0] - 1, elbow[1] - 1, 5.4, lo=2, hi=5))
    # upper arm: brass boom with a ram on its outer face
    ux = seg_xf(shoulder, elbow)
    lu = math.hypot(elbow[0] - shoulder[0], elbow[1] - shoulder[1])
    up = cv.part(ux, Capsule((0, 0), (lu, 0), 12.0, 11.0), "brass", cyl((0, 0), (lu, 0), 12.0, lo=1, hi=4, gain=1.3, bias=0.05), shadow=(3, 3))
    seam(cv, ux, (lu * 0.15, -3), (lu * 0.85, -3), "brass", up, dark=1, light=4)
    seam(cv, ux, (lu * 0.15, 5), (lu * 0.85, 5), "brass", up, dark=1, light=4)
    for k in range(6):
        rivet(cv, ux, (lu * (0.16 + k * 0.13), -8.0), "brass", up)
    stripes(cv, cv.raster(ux, box(lu * 0.7, -13, lu * 0.84, 13)) & up, 3, B[4], I[0])
    grime(cv, up, rng, 0.02, [B[1], C[1]])
    hydraulic(cv, ux, (lu * 0.05, -14.5), (lu * 0.95, -13.0), 3.4)
    # pauldron: a tractor tyre bolted over the shoulder, brass hub with lug nuts
    cx, cy = shoulder[0] + 2, shoulder[1] - 4
    tyre = Ring(cx, cy, 10.0, 25.0)
    tin = cv.part(Xf(), tyre, "iron", dome(cx - 5, cy - 6, 27, lo=1, hi=3, gain=1.1, bias=-0.2), shadow=(3, 3))
    for k in range(22):
        a = math.radians(k * (360 / 22) + 6)
        for r in (21.5, 23.0):
            q = (int(math.floor(cx + math.cos(a) * r)), int(math.floor(cy + math.sin(a) * r)))
            if q in tin:
                cv.put(q[0], q[1], I[0])
    for k in range(-165, -75, 5):
        a = math.radians(k)
        q = (int(math.floor(cx + math.cos(a) * 17.5)), int(math.floor(cy + math.sin(a) * 17.5)))
        if q in tin:
            cv.put(q[0], q[1], I[3])
    hub = cv.part(Xf(), Ellipse(cx, cy, 10.5, 10.5), "brass", dome(cx - 2, cy - 2, 11, lo=1, hi=5, gain=1.2))
    for k in range(6):
        a = math.radians(k * 60 - 90)
        bolt(cv, Xf(), (cx + math.cos(a) * 6.4 - 0.5, cy + math.sin(a) * 6.4 - 0.5), "iron", hub)
    cv.put(int(cx), int(cy), B[0])
    cv.put(int(cx) - 1, int(cy) - 1, B[0])
    for q in ((int(cx - 16), int(cy - 15)), (int(cx - 15), int(cy - 16))):
        if q in tin:
            cv.put(q[0], q[1], I[4])
    return elbow, wrist


def far_arm(cv, shoulder, wrist, hand_angle=0.0, bend=1, rng=None):
    """Crane arm (baked one ramp step darker: the far plane): dump-bed pauldron, lattice boom, winch elbow, claw."""
    rng = rng or random.Random(13)
    d = 1
    elbow, wrist = ik(shoulder, wrist, FAR_L1, FAR_L2, bend)
    fx = seg_xf(elbow, wrist)
    lf = math.hypot(wrist[0] - elbow[0], wrist[1] - elbow[1])
    fore = cv.part(fx, Capsule((0, 0), (lf, 0), 10.5, 12.0), "copper", cyl((0, 0), (lf, 0), 11.0, lo=1, hi=4, gain=1.3, bias=0.1), shadow=(2, 2), depth=d)
    for u in (0.25, 0.5, 0.75):
        seam(cv, fx, (lf * u, -11), (lf * u, 11), "copper", fore, dark=1, light=3)
    for k in range(5):
        rivet(cv, fx, (lf * (0.12 + k * 0.17), -6.5), "copper", fore)
    grime(cv, fore, rng, 0.03, [C[1], LE[0]])
    hydraulic(cv, fx, (lf * 0.12, -12.0), (lf * 0.8, -12.5), 3.2, depth=d)
    # claw: a palm block and three prongs digging into the ground
    hx = Xf.pose(hand_angle, (0.0, 0.0), wrist).then(Xf(AS, 0, 0, AS, 0, 0))
    for (x0, lean) in ((-13, -3), (-5, -1.5), (3, 0)):
        prong = Poly([(x0 - 3, 4), (x0 + 3, 4), (x0 + 2 + lean, 12), (x0 + lean, 17), (x0 - 2 + lean, 17), (x0 - 3 + lean, 11)])
        cv.part(hx, prong, "iron", flat(3), shadow=(1, 1), depth=d)
    palm = cv.part(hx, Poly([(-16, -4), (8, -5), (9, 6), (-17, 6)]), "iron", face((0.0, -0.6, 0.8), lo=1, hi=4, gain=1.2, bias=0.1, ramp_len=5), shadow=(1, 1), depth=d)
    for x in (-12, -4, 4):
        rivet(cv, hx, (x, -1), "iron", palm)
    # winch elbow
    cv.part(Xf(), Ellipse(elbow[0], elbow[1], 11.0, 11.0), "iron", dome(elbow[0] - 3, elbow[1] - 3, 12, lo=1, hi=4), shadow=(1, 1), depth=d)
    for p in cv.raster(Xf(), Ellipse(elbow[0], elbow[1], 8.0, 8.0)):
        if (p[0] + p[1]) % 3 == 0:
            cv.put(p[0], p[1], LE[1])
    cv.part(Xf(), Ellipse(elbow[0], elbow[1], 3.4, 3.4), "brass", flat(3), depth=d)
    # upper arm: a lattice crane boom (two rails and cross bracing)
    ux = seg_xf(shoulder, elbow)
    lu = math.hypot(elbow[0] - shoulder[0], elbow[1] - shoulder[1])
    for y in (-8.0, 8.0):
        cv.part(ux, Capsule((0, y), (lu, y * 0.8), 3.6), "copper", cyl((0, y), (lu, y), 3.6, lo=1, hi=4, gain=1.4), depth=d)
    for k in range(7):
        x0 = lu * (0.05 + k * 0.13)
        for off in (0, 1):
            line(cv, ux, (x0 + off, -5), (x0 + lu * 0.065 + off, 5), lambda n: C[1])
            line(cv, ux, (x0 + lu * 0.065 + off, 5), (x0 + lu * 0.13 + off, -5), lambda n: C[1])
    # dump-bed pauldron
    pts = [(shoulder[0] - 24, shoulder[1] - 9), (shoulder[0] + 21, shoulder[1] - 18), (shoulder[0] + 27, shoulder[1] + 6),
           (shoulder[0] - 18, shoulder[1] + 15)]
    pin = cv.part(Xf(), Poly(pts), "copper", face((-0.3, -0.6, 0.75), lo=1, hi=4, gain=1.2, ramp_len=5), shadow=(2, 2), depth=d)
    stripes(cv, cv.raster(Xf(), Poly([pts[3], pts[2], lerp(pts[2], pts[1], 0.3), lerp(pts[3], pts[0], 0.3)])) & pin, 3, B[3], I[0])
    return elbow, wrist


# --- crawl cycle (contact points, rig space) -------------------------------------------------------------------------
def crawl_contacts(front):
    """Contact point of one hand over the 12-frame cycle, starting with its own reach phase (frame 0 = lift)."""
    d = CRAWL_STEP
    planted = {3: 0, 4: 1, 5: 2, 6: 3, 7: 3, 8: 3, 9: 3, 10: 4, 11: 5}
    out = []
    for f in range(12):
        if f in planted:
            out.append((front + planted[f] * d, 0.0, True))
        elif f == 0:
            out.append((front + 6 * d, -6.0, False))
        elif f == 1:
            out.append((front + 3 * d, -20.0, False))
        else:
            out.append((front - 2.0, -9.0, False))
    return out


NEAR_CYCLE = crawl_contacts(NEAR_FRONT)
_far = crawl_contacts(FAR_FRONT)
FAR_CYCLE = [_far[(f + 6) % 12] for f in range(12)]   # the far hand runs half a cycle behind
DRAG_TRANSITIONS = (3, 4, 5, 9, 10, 11)                # frame k -> k+1 moves the body CRAWL_STEP px forward


# ================================================================================================
# Frame tables
# ================================================================================================
# Body frames: (name, BodyPose)
BODY_FRAMES = [
    ("Idle0", BodyPose(breathe=0, drum=0, grind=0)),
    ("Idle1", BodyPose(breathe=0, drum=1, grind=1)),
    ("Idle2", BodyPose(breathe=1, drum=2, grind=2)),
    ("Idle3", BodyPose(breathe=1, drum=3, grind=3)),
    ("JawOpen1", BodyPose(jaw=0.35, drum=0)),
    ("JawOpen2", BodyPose(jaw=0.7, drum=1)),
    ("Suck0", BodyPose(jaw=1.0, grind=0, drum=2)),
    ("Suck1", BodyPose(jaw=1.0, grind=1, drum=3)),
    ("Suck2", BodyPose(jaw=1.0, grind=2, drum=0)),
    ("Suck3", BodyPose(jaw=1.0, grind=3, drum=1)),
    ("Gulp0", BodyPose(jaw=0.0, head=(1.0, 2.0), head_tilt=-3.0)),
    ("Gulp1", BodyPose(jaw=0.12, head=(-1.0, -1.0), head_tilt=2.0, breathe=1)),
    ("SpitWind", BodyPose(jaw=0.25, head=(5.0, -4.0), head_tilt=9.0, breathe=1)),
    ("Spit", BodyPose(jaw=1.0, head=(-4.0, 2.0), head_tilt=-6.0, grind=2)),
    ("SlamWind", BodyPose(lean=7.0, jaw=0.25, head=(2.0, -2.0), head_tilt=5.0)),
    ("SlamHit", BodyPose(lean=-5.0, drop=2.0, jaw=0.4, head=(-2.0, 2.0), head_tilt=-4.0)),
    ("DeathJolt", BodyPose(lean=6.0, jaw=0.8, head=(3.0, -5.0), head_tilt=12.0, eyes=1.0)),
    ("DeathSag", BodyPose(lean=-4.0, drop=5.0, jaw=0.5, head=(-1.0, 3.0), head_tilt=-5.0, eyes=0.5)),
    ("DeathSlump", BodyPose(lean=-5.0, drop=9.0, jaw=0.6, head=(-2.0, 0.0), head_tilt=-6.0, eyes=0.5)),
    ("DeathDown", BodyPose(lean=-6.0, drop=13.0, jaw=0.85, head=(-3.0, -2.0), head_tilt=-6.0, eyes=0.0)),
    # in-betweens (2026-10-26): each sits halfway between two key poses so no transition snaps
    ("SlamWind0", BodyPose(lean=3.5, jaw=0.12, head=(1.0, -1.0), head_tilt=2.5)),                  # idle -> wind-up
    ("SlamStrike", BodyPose(lean=1.0, drop=1.0, jaw=0.35, head=(0.0, 0.0), head_tilt=0.0)),       # wind-up -> impact
    ("SlamSettle", BodyPose(lean=-2.5, drop=1.0, jaw=0.2, head=(-1.0, 1.0), head_tilt=-2.0)),     # impact -> idle
    ("SpitWind0", BodyPose(jaw=0.12, head=(2.5, -2.0), head_tilt=4.5)),                          # idle -> spit wind
    ("SpitFollow", BodyPose(jaw=0.55, head=(-2.0, 1.0), head_tilt=-3.0, grind=1)),                # spit -> idle
    ("DeathJoltSag", BodyPose(lean=1.0, drop=2.5, jaw=0.65, head=(1.0, -1.0), head_tilt=3.5, eyes=0.5)),
    ("DeathSagSlump", BodyPose(lean=-4.5, drop=7.0, jaw=0.55, head=(-1.5, 1.5), head_tilt=-5.5, eyes=0.5)),
    ("DeathSlumpDown", BodyPose(lean=-5.5, drop=11.0, jaw=0.72, head=(-2.5, -1.0), head_tilt=-6.0, eyes=0.5)),
]
BODY_INDEX = {name: k for k, (name, _) in enumerate(BODY_FRAMES)}

# Arm frames: (name, body frame whose shoulders they hang from, near (contact or wrist, planted, bend), far (...))
# A planted pose gives the fist's contact point on the ground; an air pose gives it too (lifted); "wrist" poses give
# the wrist directly (the raised slam arm).
ARM_FRAMES = []
for f in range(12):
    n, fa = NEAR_CYCLE[f], FAR_CYCLE[f]
    ARM_FRAMES.append(("Crawl%d" % f, "Idle0", ("contact", n[0], n[1], 1), ("contact", fa[0], fa[1], 1)))
REST = 5                                                # both hands planted (the end of a drag): every attack starts here
_rn, _rf = NEAR_CYCLE[REST], FAR_CYCLE[REST]
ARM_FRAMES += [
    ("SlamRaise", "SlamWind", ("wrist", -30.0, -146.0, -1), ("contact", _rf[0], 0.0, 1)),
    ("SlamHigh", "SlamWind", ("wrist", -4.0, -184.0, -1), ("contact", _rf[0], 0.0, 1)),
    ("SlamHit", "SlamHit", ("contact", -78.0, 0.0, 1), ("contact", _rf[0], 0.0, 1)),
    ("SlamLift", "Idle0", ("contact", -54.0, -16.0, 1), ("contact", _rf[0], 0.0, 1)),
    # the second slam of the enraged phase: the far arm, while the near arm stays planted
    ("FarSlamRaise", "SlamWind", ("contact", _rn[0], 0.0, 1), ("wrist", -72.0, -148.0, -1)),
    ("FarSlamHigh", "SlamWind", ("contact", _rn[0], 0.0, 1), ("wrist", -52.0, -170.0, -1)),
    ("FarSlamHit", "SlamHit", ("contact", _rn[0], 0.0, 1), ("contact", -138.0, 0.0, 1)),
    ("FarSlamLift", "Idle0", ("contact", _rn[0], 0.0, 1), ("contact", -132.0, -16.0, 1)),
    ("DeathJolt", "DeathJolt", ("contact", _rn[0], 0.0, 1), ("contact", _rf[0], 0.0, 1)),
    ("DeathSag", "DeathSag", ("contact", _rn[0] - 4, 0.0, 1), ("contact", _rf[0] - 4, 0.0, 1)),
    ("DeathSlump", "DeathSlump", ("contact", _rn[0] - 12, 0.0, 1), ("contact", _rf[0] - 8, 0.0, 1)),
    ("DeathDown", "DeathDown", ("contact", _rn[0] - 18, 0.0, 1), ("contact", _rf[0] - 10, 0.0, 1)),
    # in-betweens (2026-10-26): the fist leaves the ground, rises, cocks back, swings through, and lowers again
    ("SlamRaise0", "SlamWind0", ("contact", -32.0, -14.0, 1), ("contact", _rf[0], 0.0, 1)),
    ("SlamRaise1", "SlamWind", ("wrist", -44.0, -110.0, -1), ("contact", _rf[0], 0.0, 1)),
    ("SlamCock", "SlamWind", ("wrist", 4.0, -190.0, -1), ("contact", _rf[0], 0.0, 1)),
    ("SlamStrike", "SlamStrike", ("wrist", -66.0, -100.0, -1), ("contact", _rf[0], 0.0, 1)),
    ("SlamLower", "Idle0", ("contact", -40.0, -8.0, 1), ("contact", _rf[0], 0.0, 1)),
    ("FarSlamPrep", "SlamWind0", ("contact", -40.0, -6.0, 1), ("contact", _rf[0] - 12, -14.0, 1)),
    ("FarSlamStrike", "SlamStrike", ("contact", _rn[0], 0.0, 1), ("wrist", -110.0, -100.0, -1)),
    ("FarSlamLower", "Idle0", ("contact", _rn[0], 0.0, 1), ("contact", -122.0, -6.0, 1)),
    ("DeathJoltSag", "DeathJoltSag", ("contact", _rn[0] - 2, 0.0, 1), ("contact", _rf[0] - 2, 0.0, 1)),
    ("DeathSagSlump", "DeathSagSlump", ("contact", _rn[0] - 8, 0.0, 1), ("contact", _rf[0] - 6, 0.0, 1)),
    ("DeathSlumpDown", "DeathSlumpDown", ("contact", _rn[0] - 15, 0.0, 1), ("contact", _rf[0] - 9, 0.0, 1)),
]
ARM_INDEX = {name: k for k, (name, *_rest) in enumerate(ARM_FRAMES)}


def shoulders(body_name):
    pose = dict(BODY_FRAMES)[body_name]
    bx = body_xf(pose)
    return bx.fwd(SHOULDER_NEAR), bx.fwd(SHOULDER_FAR)


def draw_arm(which, spec, shoulder, rng_seed):
    kind, x, y, bend = spec
    grip = NEAR_GRIP if which == "near" else FAR_GRIP
    planted = kind == "contact" and y >= 0.0
    if kind == "contact":
        wrist = (x + grip[0], y + grip[1])
        contact = (x, y)
    else:
        wrist = (x, y)
        contact = (x - grip[0], y - grip[1])
    if planted:
        angle = 0.0
    else:
        ang = math.degrees(math.atan2(wrist[1] - shoulder[1], wrist[0] - shoulder[0]))
        angle = max(-35.0, min(35.0, (ang - 110.0) * 0.35)) if kind == "contact" else (ang + 90.0) * 0.5
    cv = Canvas()
    fn = near_arm if which == "near" else far_arm
    fn(cv, shoulder, wrist, hand_angle=angle, bend=bend, rng=random.Random(rng_seed))
    return cv, contact


def render_all():
    bodies, meta = [], []
    for name, pose in BODY_FRAMES:
        cv, m = draw_body(pose)
        bodies.append(cv)
        meta.append(m)
    near, far, contacts = [], [], []
    for name, body, nspec, fspec in ARM_FRAMES:
        sn, sf = shoulders(body)
        cn, pn = draw_arm("near", nspec, sn, 11)
        cf, pf = draw_arm("far", fspec, sf, 13)
        near.append(cn)
        far.append(cf)
        contacts.append((pn, pf))
    return bodies, meta, near, far, contacts


# ================================================================================================
# Sheets
# ================================================================================================
GROUND_CLIP = 1                                          # rows below the ground line are never drawn in game


PAGE = 1024                                              # 1x page size limit: 2048x2048 at 2x
FRAME_FIELDS = 7                                         # page, x, y, w, h, origin x, origin y


def crop_frame(cv, glow=False):
    """The frame's own pixels above the ground clip: (image, x0, y0) with (x0, y0) the crop's top-left in rig space,
    or (None, 0, 0) for a frame with nothing to draw (a glow frame with the eyes out)."""
    src = {p: c for p, c in (cv.glow if glow else cv.px).items() if p[1] < GROUND_CLIP}
    if not src:
        return None, 0, 0
    xs = [x for (x, _) in src]
    ys = [y for (_, y) in src]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0 + 1, max(ys) - y0 + 1
    return to_image(src, x0, y0, w, h), x0, y0


def pack_layer(canvases, glow=False):
    """Packs a layer's frames, each cropped to its own pixels, into as few PAGE x PAGE pages as a shelf packer manages
    (tallest first, 1 px between frames: 2 px at 2x, like the old grid's padding). Trimming the empty space every grid
    cell carried (the union of all poses) is what leaves room for the in-between frames. Returns (pages, table): table
    is FRAME_FIELDS values per frame, in game px (2x): page, x, y, w, h, and the rig origin inside the crop."""
    crops = [crop_frame(cv, glow) for cv in canvases]
    order = sorted(range(len(crops)), key=lambda k: -(crops[k][0].height if crops[k][0] else 0))
    pages, placed = [], {}
    x = y = shelf = 0
    page = -1
    for k in order:
        im = crops[k][0]
        if im is None:
            placed[k] = None
            continue
        if im.width + 1 > PAGE or im.height + 1 > PAGE:
            raise SystemExit("frame %d (%dx%d) is larger than a page" % (k, im.width, im.height))
        if page >= 0 and x + im.width + 1 > PAGE:
            x, y, shelf = 0, y + shelf, 0
        if page < 0 or y + im.height + 1 > PAGE:
            pages.append([])
            page += 1
            x = y = shelf = 0
        pages[page].append((im, x, y))
        placed[k] = (page, x, y)
        x += im.width + 1
        shelf = max(shelf, im.height + 1)
    images = []
    for items in pages:
        w = max(px + im.width + 1 for im, px, _ in items)
        h = max(py + im.height + 1 for im, _, py in items)
        page_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for im, px, py in items:
            page_img.alpha_composite(im, (px, py))
        images.append(page_img)
    table = []
    for k, (im, x0, y0) in enumerate(crops):
        if placed[k] is None:
            table += [0, 0, 0, 0, 0, 0, 0]
            continue
        pg, px, py = placed[k]
        table += [pg, px * 2, py * 2, im.width * 2, im.height * 2, -x0 * 2, -y0 * 2]
    return images, table


def page_name(base, page):
    return base + ("" if page == 0 else "_Page%d" % page) + ".png"


def export(img, rel):
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    big = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    big.save(out)
    print("wrote %s (%dx%d)" % (rel, big.width, big.height))


def cs_array(name, values, fmt="{}", per_line=12, typ="int"):
    lines = []
    for k in range(0, len(values), per_line):
        lines.append("\t\t\t" + ", ".join(fmt.format(v) for v in values[k:k + per_line]) + ",")
    return "\t\tpublic static readonly %s[] %s = {\n%s\n\t\t};\n" % (typ, name, "\n".join(lines))


def hit_strips(cv, n):
    """n vertical strips over a frame's opaque pixels (above the ground line), each the box of the pixels in it: a
    staircase that follows the silhouette, for the boss's contact damage. 2x rig px (x0, y0, x1, y1) per strip; an
    empty strip is (0, 0, 0, 0)."""
    pts = [p for p in cv.px if p[1] < GROUND_CLIP]
    if not pts:
        return [(0, 0, 0, 0)] * n
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
        keep = [(x, y) for (x, y) in col if rows[y] >= 3]   # ignore one- and two-pixel wisps (cables, a stack rim)
        if not keep:
            out.append((0, 0, 0, 0))
            continue
        out.append((min(q[0] for q in keep) * 2, min(q[1] for q in keep) * 2,
                    (max(q[0] for q in keep) + 1) * 2, (max(q[1] for q in keep) + 1) * 2))
    return out


BODY_STRIPS, ARM_STRIPS = 6, 3


def write_rig_data(path, layers, meta, contacts, bodies, nears, fars):
    """C# tables for the drawing, the AI points and the hitboxes. All values in game pixels (2x art). layers maps
    "Body", "Glow", "Near", "Far" to (page count, frame table)."""
    L = []
    L.append("// <auto-generated> by art/bosses/trashtr0m/make_trashtr0m_art.py - do not edit by hand. </auto-generated>")
    L.append("namespace Cogpunk.Content.Bosses.TrashTr0m")
    L.append("{")
    L.append("\t/// <summary>Trash-Tr0m's multiplane rig, generated with its sprites: the packed frame tables of every layer, frame")
    L.append("\t/// indices, hand contact points, the mouth point and the hit strips. Game pixels (2x art), left-facing; mirror X when")
    L.append("\t/// facing right. Each layer is a set of pages (TrashTr0m.png, TrashTr0m_Page1.png...); a frame is FrameFields")
    L.append("\t/// values: page, x, y, width, height, and the rig origin (the ground point under the body pivot) inside that rectangle.</summary>")
    L.append("\tpublic static class TrashTr0mRigData")
    L.append("\t{")
    L.append("\t\tpublic const int FrameFields = %d;" % FRAME_FIELDS)
    L.append("\t\tpublic const int BodyPages = %d, GlowPages = %d, NearPages = %d, FarPages = %d;"
             % tuple(layers[k][0] for k in ("Body", "Glow", "Near", "Far")))
    L.append("\t\tpublic const int CrawlStep = %d;                   // game px the body moves per drag transition" % (CRAWL_STEP * 2))
    L.append("\t\tpublic const int CrawlFrames = 12;")
    L.append("\t\tpublic const int RestFrame = %d;" % REST)
    xs = [q[0] for cv in bodies for q in cv.px if q[1] < GROUND_CLIP]
    ys = [q[1] for cv in bodies for q in cv.px if q[1] < GROUND_CLIP]
    L.append("\t\t/// <summary>The union of every body frame (the bestiary sizes its box from it) and the tallest body above the")
    L.append("\t\t/// ground line (how far it must sink to be fully buried).</summary>")
    L.append("\t\tpublic const int BodyBoundsWidth = %d, BodyBoundsHeight = %d, BodyMaxHeight = %d;"
             % ((max(xs) - min(xs) + 1) * 2, (max(ys) - min(ys) + 1) * 2, -min(ys) * 2))
    L.append("")
    L.append("\t\t// Body frames")
    for name, k in BODY_INDEX.items():
        L.append("\t\tpublic const int Body%s = %d;" % (name, k))
    L.append("\t\tpublic const int BodyFrameCount = %d;" % len(BODY_FRAMES))
    L.append("")
    L.append("\t\t// Arm frames (the same index in both arm layers)")
    for name, k in ARM_INDEX.items():
        L.append("\t\tpublic const int Arm%s = %d;" % (name, k))
    L.append("\t\tpublic const int ArmFrameCount = %d;" % len(ARM_FRAMES))
    L.append("")
    for key in ("Body", "Glow", "Near", "Far"):
        L.append("\t\t/// <summary>%s layer: page, x, y, w, h, origin x, origin y per frame.</summary>" % key)
        L.append(cs_array(key + "Frames", layers[key][1], typ="short", per_line=14).rstrip("\n"))
    L.append("\t\t/// <summary>Crawl frame k -> k+1 moves the body CrawlStep px forward (a planted hand drags).</summary>")
    drags = [1 if k in DRAG_TRANSITIONS else 0 for k in range(12)]
    L.append(cs_array("CrawlDrag", drags, typ="byte").rstrip("\n"))
    L.append("\t\t/// <summary>Near and far hand contact points per arm frame, relative to the rig origin (x, y pairs).</summary>")
    nc, fc = [], []
    for (pn, pf) in contacts:
        nc += [int(round(pn[0] * 2)), int(round(pn[1] * 2))]
        fc += [int(round(pf[0] * 2)), int(round(pf[1] * 2))]
    L.append(cs_array("NearContact", nc, typ="short").rstrip("\n"))
    L.append(cs_array("FarContact", fc, typ="short").rstrip("\n"))
    mouth = []
    for m in meta:
        mouth += [int(round(m["mouth"][0] * 2)), int(round(m["mouth"][1] * 2))]
    L.append("\t\t/// <summary>Mouth (throat) point per body frame, relative to the rig origin (x, y pairs).</summary>")
    L.append(cs_array("Mouth", mouth, typ="short").rstrip("\n"))
    L.append("\t\tpublic const int BodyStrips = %d, ArmStrips = %d;" % (BODY_STRIPS, ARM_STRIPS))
    for (name, cvs, n) in (("BodyHit", bodies, BODY_STRIPS), ("NearHit", nears, ARM_STRIPS), ("FarHit", fars, ARM_STRIPS)):
        vals = []
        for cv in cvs:
            for r in hit_strips(cv, n):
                vals += list(r)
        L.append("\t\t/// <summary>Contact boxes per frame (%d strips of x0, y0, x1, y1 that follow the silhouette), relative to the rig origin.</summary>" % n)
        L.append(cs_array(name, vals, typ="short", per_line=16).rstrip("\n"))
    xs = [q[0] for q in bodies[0].px if q[1] < GROUND_CLIP]
    ys = [q[1] for q in bodies[0].px if q[1] < GROUND_CLIP]
    L.append("\t\t/// <summary>The idle body's bounding box (the NPC hitbox for player hits), relative to the rig origin.</summary>")
    L.append("\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d;" % (min(xs) * 2, (max(xs) + 1) * 2, min(ys) * 2))
    L.append("\t}")
    L.append("}")
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


# ================================================================================================
# Small sprites: projectiles, the Lost Key, gores, map icon
# ================================================================================================
def small_image(cv, w, h, ox=0, oy=0):
    return to_image(cv.px, -ox, -oy, w, h)


def shockwave_frames():
    """The slam's ground wave (hostile: ember and steam). 4 frames, 44x30 px, the wave rolls left (it is mirrored in
    code for a wave travelling right); the ground line is the bottom row."""
    frames = []
    for f in range(4):
        rng = random.Random(40 + f)
        cv = Canvas()
        # dust mound (opaque steam shades), rolling: its crest leans further forward each frame
        lean = f * 1.5
        mound = Poly([(2, 30), (6 - lean, 18), (14 - lean, 9), (22 - lean * 0.5, 6), (32, 11), (40, 20), (43, 30)])
        cv.part(Xf(), mound, "leather", dome(14 - lean, 8, 26, lo=1, hi=2, gain=1.2, bias=0.1))
        for k in range(5):                               # dust puffs along the crest
            cx, cy = 8 + k * 7 - lean * (1 - k / 5), 12 + abs(k - 1.5) * 2.5 + (f + k) % 2
            r = 4.5 - abs(k - 2) * 0.5
            cv.part(Xf(), Ellipse(cx, cy, r, r * 0.85), "steam", dome(cx - 1.5, cy - 1.5, r, lo=0, hi=2, gain=1.2))
        for k in range(4):                               # scrap half-buried in the mound
            x, y = 6 + k * 9 - lean * 0.5, 22 + (k % 2) * 3
            cv.part(Xf.pose((k * 50 + f * 20) % 360, (x, y)), Poly([(x - 2.5, y - 1.5), (x + 2.5, y - 2), (x + 2, y + 1.5), (x - 2, y + 2)]),
                    ("iron", "copper", "brass", "iron")[k], flat(2, bevel=False))
        # flung chunks: scrap and dirt arcing up off the front
        for k in range(6):
            t = (k / 6 + f * 0.11) % 1.0
            x = 4 + t * 26 - lean
            y = 26 - math.sin(t * math.pi) * (20 + (k % 3) * 3)
            ang = (k * 47 + f * 33) % 360
            pts = [(x + math.cos(math.radians(ang + a)) * r, y + math.sin(math.radians(ang + a)) * r)
                   for a, r in ((0, 2.4), (110, 1.8), (200, 2.2), (290, 1.6))]
            ramp = ("iron", "copper", "iron", "iron", "brass", "copper")[k]
            cv.part(Xf(), Poly(pts), ramp, flat(2 if ramp != "brass" else 3, bevel=False))
        # ember sparks on the crest and a crack in the ground at its foot
        for k in range(4):
            x, y = int(10 + k * 7 - lean + (f * 3 + k * 5) % 4), int(6 + (k * 3 + f) % 5)
            cv.put(x, y, E[3])
            cv.put(x + 1, y + 1, E[2])
        for x in range(2, 42):
            if (x + f) % 7 < 5:
                cv.put(x, 29, I[0])
                if (x + f) % 7 == 2:
                    cv.put(x, 28, E[1])
        frames.append(small_image(cv, 44, 30))
    return frames


def scrap_clump(cv, cx, cy, r, ang, rng, hot=False):
    """A compacted lump of mangled scrap at (cx, cy), turned by ang degrees (pre-rendered rotation)."""
    xf = Xf.pose(ang, (cx, cy))
    base = Ellipse(cx, cy, r, r * 0.92)
    cv.part(xf, base, "iron", dome(cx - r * 0.35, cy - r * 0.4, r * 1.15, lo=1, hi=4, gain=1.3))
    bits = [("copper", 0.0, 0.55, 0.42), ("brass", 120.0, 0.6, 0.36), ("iron", 220.0, 0.5, 0.4), ("copper", 300.0, 0.62, 0.3),
            ("verd", 60.0, 0.35, 0.28), ("brass", 180.0, 0.28, 0.26)]
    for ramp, a, dist, size in bits:
        bx = cx + math.cos(math.radians(a)) * r * dist
        by = cy + math.sin(math.radians(a)) * r * dist
        s = r * size
        pts = [(bx + math.cos(math.radians(a + t)) * s * q, by + math.sin(math.radians(a + t)) * s * q)
               for t, q in ((0, 1.0), (80, 0.7), (150, 1.1), (230, 0.8), (300, 1.0))]
        hi = len(RAMP[ramp]) - 1
        cv.part(xf, Poly(pts), ramp, face((math.cos(math.radians(a)) * 0.5, math.sin(math.radians(a)) * 0.5, 0.7),
                                          lo=1, hi=hi, gain=1.3, ramp_len=hi + 1))
    if hot:
        for (dx, dy) in ((0, 0), (1, 0), (0, 1)):
            q = P(xf, (cx + dx - 0.5, cy + dy - 0.5))
            cv.put_glow(q[0], q[1], E[3] if (dx, dy) == (0, 0) else E[2])
    for k in range(3):
        rivet(cv, xf, (cx + math.cos(k * 2.1) * r * 0.5, cy + math.sin(k * 2.1) * r * 0.5), "iron")


def chewed_frames():
    """Regurgitated scrap: what it chewed, spat back. 3 frames, 16x16 px, tumbling."""
    out = []
    for f in range(3):
        cv = Canvas()
        scrap_clump(cv, 8, 8, 5.5, f * 40, random.Random(5), hot=True)
        for (x, y) in ((2, 9), (3, 11), (13, 5)):        # grease drips
            cv.put(x + f % 2, y, LE[0])
        out.append(small_image(cv, 16, 16))
    return out


def scrapball_frames():
    """The big spat scrap ball. 4 frames, 30x30 px, a quarter turn apart."""
    out = []
    for f in range(4):
        cv = Canvas()
        scrap_clump(cv, 15, 15, 13.0, f * 22.5, random.Random(9))
        xf = Xf.pose(f * 22.5, (15, 15))
        cv.part(xf, Ring(15, 21, 3.0, 5.5), "iron", dome(13, 19, 6, lo=1, hi=3))      # a tyre fragment pressed in
        cv.part(xf, Capsule((6, 9), (12, 5), 1.6), "steam", flat(2, bevel=False))      # a bent piston rod
        out.append(small_image(cv, 30, 30))
    return out


def lost_key():
    """The Lost Key: an old iron key with a cog-shaped brass bow and verdigris crust (16x16 at 1x, item: <= 16 colours)."""
    cv = Canvas()
    xf = Xf.pose(-45.0, (8, 8))                         # drawn horizontal, turned so the bit points to the top right
    shaft = box(6.0, 6.5, 17.5, 9.5)
    cv.part(xf, shaft, "iron", cyl((6, 8), (17, 8), 1.5, lo=1, hi=4, gain=1.4))
    cv.part(xf, Poly([(13, 9), (17.5, 9), (17.5, 13.5), (15.5, 13.5), (15.5, 11.5), (13, 11.5)]), "iron", flat(3))
    teeth = Union(*[Capsule((3.5, 8), (3.5 + math.cos(math.radians(a)) * 5.0, 8 + math.sin(math.radians(a)) * 5.0), 1.1) for a in range(0, 360, 45)])
    bow = (Ellipse(3.5, 8, 4.0, 4.0) | teeth) - Ellipse(3.5, 8, 1.5, 1.5)
    cv.part(xf, bow, "brass", dome(2.5, 7, 5.2, lo=1, hi=5, gain=1.3))
    for q0 in ((7.5, 9.0), (11.0, 7.0)):
        q = P(xf, q0)
        cv.put(q[0], q[1], V[2])
    return small_image(cv, 16, 16)


def gore_images():
    """Pieces that fly off in the death animation: tyre, jaw, helmet crest, elbow gear, piston, hazard plate."""
    out = {}
    rng = random.Random(3)
    cv = Canvas()
    tin = cv.part(Xf(), Ring(12, 12, 4.5, 11.0), "iron", dome(9, 9, 12, lo=1, hi=3, gain=1.1, bias=-0.2))
    for k in range(14):
        a = math.radians(k * (360 / 14))
        q = (int(12 + math.cos(a) * 9.8), int(12 + math.sin(a) * 9.8))
        if q in tin:
            cv.put(q[0], q[1], I[0])
    cv.part(Xf(), Ellipse(12, 12, 4.5, 4.5), "brass", dome(11, 11, 5, lo=1, hi=5))
    out["Tyre"] = small_image(cv, 24, 24)
    cv = Canvas()
    jin = cv.part(Xf(), Poly([(1, 3), (24, 1), (25, 13), (3, 15)]), "iron", flat(2))
    for k in range(5):
        cv.part(Xf(), Poly([(3 + k * 4.5, 3), (6.5 + k * 4.5, 2.6), (5 + k * 4.5, -1.5)]), "steam", flat(1, bevel=False))
    stripes(cv, cv.raster(Xf(), box(2, 10, 25, 13)) & jin, 3, B[4], I[0])
    out["Jaw"] = small_image(cv, 26, 16, 0, -2)
    cv = Canvas()
    cin = cv.part(Xf(), Poly([(1, 10), (12, 2), (22, 4), (20, 12), (2, 14)]), "verd", dome(8, 5, 14, lo=1, hi=3))
    cv.part(Xf(), Poly([(4, 4), (18, 1), (19, 4), (6, 7)]), "brass", flat(3))
    for k in range(3):
        rivet(cv, Xf(), (6 + k * 5, 9), "verd", cin)
    out["Crest"] = small_image(cv, 24, 16)
    cv = Canvas()
    teeth = Union(*[Capsule((9, 9), (9 + math.cos(math.radians(a)) * 8.5, 9 + math.sin(math.radians(a)) * 8.5), 1.6) for a in range(0, 360, 36)])
    cv.part(Xf(), Ellipse(9, 9, 7, 7) | teeth, "iron", dome(7, 7, 8.5, lo=1, hi=4))
    cv.part(Xf(), Ellipse(9, 9, 3, 3), "brass", dome(8, 8, 3, lo=2, hi=5))
    out["Gear"] = small_image(cv, 18, 18)
    cv = Canvas()
    hydraulic(cv, Xf(), (2, 4), (24, 4), 2.6)
    out["Piston"] = small_image(cv, 28, 8)
    cv = Canvas()
    pin = cv.part(Xf(), Poly([(1, 2), (20, 1), (21, 14), (2, 15)]), "brass", flat(3))
    stripes(cv, cv.raster(Xf(), box(1, 10, 21, 15)) & pin, 3, B[4], I[0])
    for k in range(4):
        rivet(cv, Xf(), (4 + k * 4.5, 4), "brass", pin)
    out["Plate"] = small_image(cv, 22, 16)
    return out


def boss_icon():
    """16x16 map / boss-bar icon: the brow, three eyes and the jaw, front-on so it reads at map size."""
    cv = Canvas()
    cv.part(Xf(), Poly([(1, 4), (14, 3), (15, 15), (1, 15)]), "verd", flat(2))
    brow = cv.part(Xf(), Poly([(0, 2), (15, 1), (15, 5), (0, 6)]), "brass", flat(4))
    stripes(cv, cv.raster(Xf(), box(0, 4, 16, 6)) & brow, 2, B[4], I[0])
    for x in range(2, 14):
        cv.put(x, 7, I[0])
    for x in (3, 7, 11):
        cv.put(x, 7, E[3])
        cv.put(x + 1, 7, E[2])
    jaw = cv.part(Xf(), Poly([(2, 9), (14, 9), (13, 15), (3, 15)]), "iron", flat(2))
    for x in range(3, 13, 2):
        cv.put(x, 10, S[2])
    cv.put_glow(8, 12, E[3])
    cv.put_glow(7, 12, E[2])
    return small_image(cv, 16, 16)


# ================================================================================================
# Export helpers
# ================================================================================================
def to_image(px, x0, y0, w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = img.load()
    for (x, y), col in px.items():
        xx, yy = x - x0, y - y0
        if 0 <= xx < w and 0 <= yy < h:
            p[xx, yy] = col + (255,)
    return img


def preview(canvases, path, bg=(30, 30, 36), scale=2):
    xs = [x for cv in canvases for (x, _) in cv.px]
    ys = [y for cv in canvases for (_, y) in cv.px]
    x0, y0, x1, y1 = min(xs) - 4, min(ys) - 4, max(xs) + 5, max(ys) + 5
    img = Image.new("RGBA", (x1 - x0, y1 - y0), bg + (255,))
    for cv in canvases:
        img.alpha_composite(to_image(cv.px, x0, y0, x1 - x0, y1 - y0))
    for x in range(x1 - x0):                              # ground line at rig y = 0
        if 0 <= -y0 < img.height and (x, -y0) not in ():
            if img.getpixel((x, -y0))[:3] == bg:
                img.putpixel((x, -y0), (90, 60, 40, 255))
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(path)
    print("preview", path, img.size)


def composite(body, near, far, path, frames, scale=2, bg=(30, 30, 36)):
    """Preview: far arm, body, near arm composited for each (body index, arm index)."""
    imgs = []
    for (bi, ai) in frames:
        cvs = [far[ai], body[bi], near[ai]]
        xs = [x for cv in cvs for (x, _) in cv.px]
        ys = [y for cv in cvs for (_, y) in cv.px]
        imgs.append((cvs, min(xs), min(ys), max(xs), max(ys)))
    x0 = min(t[1] for t in imgs) - 4
    y0 = min(t[2] for t in imgs) - 4
    x1 = max(t[3] for t in imgs) + 5
    y1 = max(t[4] for t in imgs) + 5
    w, h = x1 - x0, y1 - y0
    out = Image.new("RGBA", (w * len(imgs), h), bg + (255,))
    for k, (cvs, *_r) in enumerate(imgs):
        for cv in cvs:
            out.alpha_composite(to_image(cv.px, x0, y0, w, h), (k * w, 0))
        for x in range(w):
            if out.getpixel((k * w + x, -y0))[:3] == bg:
                out.putpixel((k * w + x, -y0), (90, 60, 40, 255))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    out.save(path)
    print("preview", path, out.size)


def vertical(frames, pad=1):
    """Equal frames stacked vertically with `pad` px (1x) under each (D4: 2 px at 2x)."""
    w, h = frames[0].size
    out = Image.new("RGBA", (w, (h + pad) * len(frames)), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        out.alpha_composite(im, (0, k * (h + pad)))
    return out


LAYER_FILES = {"Body": "TrashTr0m", "Glow": "TrashTr0m_Glow", "Near": "TrashTr0m_ArmNear", "Far": "TrashTr0m_ArmFar"}


def export_all():
    bodies, meta, near, far, contacts = render_all()
    layers = {}
    for key, cvs, glow in (("Body", bodies, False), ("Glow", bodies, True), ("Near", near, False), ("Far", far, False)):
        pages, table = pack_layer(cvs, glow)
        for k, im in enumerate(pages):
            export(im, OUT + page_name(LAYER_FILES[key], k))
        for k in range(len(pages), 8):                     # pages left over from a bigger layout
            stale = os.path.join(ROOT, OUT + page_name(LAYER_FILES[key], k))
            if os.path.exists(stale):
                os.remove(stale)
        layers[key] = (len(pages), table)
    write_rig_data(OUT + "TrashTr0mRigData.cs", layers, meta, contacts, bodies, near, far)
    export(boss_icon(), OUT + "TrashTr0m_Head_Boss.png")
    export(vertical(shockwave_frames()), OUT + "Projectiles/TrashTr0mShockwave.png")
    export(vertical(chewed_frames()), OUT + "Projectiles/TrashTr0mChewedScrap.png")
    export(vertical(scrapball_frames()), OUT + "Projectiles/TrashTr0mScrapBall.png")
    export(lost_key(), OUT + "Items/LostKey.png")
    for name, im in gore_images().items():
        export(im, OUT + "Gores/TrashTr0m_Gore" + name + ".png")
    return bodies, meta, near, far, contacts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    bodies, meta, near, far, contacts = export_all()
    if a.preview:
        composite(bodies, near, far, os.path.join(a.preview, "rig_crawl.png"), [(0, k) for k in range(0, 12, 2)])
        composite(bodies, near, far, os.path.join(a.preview, "rig_attacks.png"),
                  [(BODY_INDEX["Suck1"], ARM_INDEX["Crawl6"]), (BODY_INDEX["SlamWind"], ARM_INDEX["SlamHigh"]),
                   (BODY_INDEX["SlamHit"], ARM_INDEX["SlamHit"]), (BODY_INDEX["DeathDown"], ARM_INDEX["DeathDown"])])
        composite(bodies, near, far, os.path.join(a.preview, "rig_farslam.png"),
                  [(BODY_INDEX["SlamWind"], ARM_INDEX["FarSlamRaise"]), (BODY_INDEX["SlamWind"], ARM_INDEX["FarSlamHigh"]),
                   (BODY_INDEX["SlamHit"], ARM_INDEX["FarSlamHit"]), (BODY_INDEX["Idle0"], ARM_INDEX["FarSlamLift"])])
