"""ARCHIVED 2026-10-30: the generator as it stood on 2026-10-29 (third round), kept so the look can be restored. Running it
overwrites the current assets (it writes the same Content/ paths). Run from the repo root.
"""
"""Source for Tar Tyrant, the Junkyard tar pool's boss (T3 since the 2026-10-29 rework), and its Scrapworm summon (D4,
art direction of 2026-10-26). Run from the repo root:

    python -P art/bosses/tartyrant/make_tartyrant_art.py [--preview FILE --frames Name0,Name1 --cols N]

Design (user, 2026-10-29: "a mass of tar with dinosaur bones sticking out of it"): a heaving mound of glossy tar that
never leaves its own puddle, built around the fossil it swallowed. A Tyrannosaurus skull rides the front of the mass as
its head (fenestrae full of tar, an ember burning in the orbit, a hinged jaw strung with tar), neural spines break
through the top of the mound like a ridge, a ribcage shows through its near flank, far ribs arch out of its back and a
great femur juts out of it. The near arm is a tar limb with the bones of the forearm showing and a three-taloned bone
claw; the far arm is a smaller one behind it. Three-quarter view facing left, lit from the top-left, the tar's gloss in
cold Iron 2/3 strokes, the bone in a tar-stained ramp (rig.RAMP["bone"]).

History: this look was drawn first (2026-10-29); the same day a redraw from the user's reference painting (blue-black
pitch, a horned skull, a web over its back) replaced it, and the user then asked for this one back with the redraw's
animation ("update the animation so the previous look as alive as the current one"): what follows is this look on the
redraw's animation system, and the femur throw is gone (user: bones fly out of its back on their own instead).

Stable pixels (user, 2026-10-29; tools/check_flicker.py measures it): the mass is two parts, a lower body that stays put
and an upper body (hump, throat, skull, spines, ribs, femur) moved by whole pixels in the loops; each is lit in its own
space (space_dome), so a breath carries its shading with it instead of dragging the light across it; highlights are drawn
in the part's space; limbs are lit in 45-degree steps (rig.py snap); shakes are 0/1 px; a last pass removes lone pixels
and lightens the lit side of the outline (selective outline).

Multiplane rig (DepthLayers): every pose renders three canvases, far (the far arm, one ramp step darker), middle (puddle,
tar mass, ribs, spines, femur, skull and jaw; + glow: the orbit's ember and the hot throat) and near (the claw arm).
Tar is soft and bone is not: the mass squashes and melts through its transforms while every bone is placed rigidly at a
point of it. Nothing is rotated or scaled at runtime except the shrink (SKILL.md D4 rule 14's exception); the frames are
packed atlases (pack_layer) and Content/Bosses/TarTyrant/TarTyrantRigData.cs holds the frame tables, hit strips and the
AI points (mouth, eye, hand, core, top, vent) per frame.

Frames (100): idle x8, ooze x8, burp x10, spit x8, melt x8, rise x10, summon x10, roar x6, death x32 (recoil and a last
roar, its bones working loose, the slump, the settling, the last bubble). About 120 px at 1x (240 px in game). Boss cap
48 colours.

Also: the attack sprites (tar bubble, spit glob, tar puddle, bone spike with its warning patch, the enrage claw with its
warning patch, the "!" sign, the bones it flings out of its back and the vent they burst out of), the Tyrant armor's
set-bonus claw (the enrage claw cut down to a player's size), gores (skull, jaw, claw, rib, femur, vertebra), the map
head, the treasure bag, the Serene Tear (Gota Serena) accessory, and the Scrapworm (critter sheet + bait item). The
Tyrant armor pieces themselves: art/bosses/tartyrant/make_tyrant_armor.py.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "trashtr0m"))
from rig import (RAMP, Xf, Shape, Poly, Ellipse, Capsule, Union, Canvas, flat, dome, cyl, line, ik, seg_pixels,  # noqa: E402
                 level, lit)
from make_trashtr0m_art import (seg_xf, pack_layer, page_name, export, to_image, cs_array, vertical,  # noqa: E402
                                GROUND_CLIP)

ROOT = os.getcwd()
OUT = "Content/Bosses/TarTyrant/"
ARMOR_OUT = OUT + "Armor/"
I, B, C, E, S, LE, T, BN, AE = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "leather", "tar", "bone", "aether"))
LIGHT_DIR = (-0.6, -0.8)                                     # towards the light, rig space (top-left)
LIMB_SNAP = 45.0                                             # limbs and spin frames: light follows turns in 45-degree steps


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def smooth(t):
    return t * t * (3.0 - 2.0 * t)


def ease_in(t):
    return t * t


def rnd(v):
    return (int(round(v[0])), int(round(v[1])))


class Posed(Shape):
    """A shape placed by its own transform, so parts in different transforms can be one union (rig space)."""

    def __init__(self, xf, shape):
        self.xf, self.shape = xf, shape

    def inside(self, x, y):
        lx, ly = self.xf.inv((x, y))
        return self.shape.inside(lx, ly)

    def bbox(self):
        x0, y0, x1, y1 = self.shape.bbox()
        pts = [self.xf.fwd(p) for p in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def space_dome(xf, cx, cy, r, lo=1, hi=2, gain=1.35, bias=0.0):
    """A dome lit in the space `xf` maps from (for a part drawn with the identity whose shape is posed by `xf`): the
    shading rides the part, so a squash, a bob or a lean never drags its bands across it (stable pixels)."""
    def shade(i):
        lx, ly = xf.inv((i.x + 0.5, i.y + 0.5))
        dx, dy = (lx - cx) / r, (ly - cy) / r
        d2 = min(1.0, dx * dx + dy * dy)
        return max(lo, min(hi, level(lit(dx, dy, math.sqrt(1.0 - d2)), lo, hi, gain, bias)))
    return shade


def gloss_line(cv, a, b, inner, bright_every=4):
    """A cold wet highlight stroke (rig space), only on `inner` pixels: Iron 2 with Iron 3 glints."""
    for n, (x, y) in enumerate(seg_pixels(a, b)):
        if (x, y) in inner:
            cv.put(x, y, T[4] if n % bright_every == 1 else T[3])


def arc_points(c, rx, ry, a0, a1, k, n=8):
    """Points on an ellipse arc (degrees, screen angles: 180 left, 270 up) at k x the radii."""
    out = []
    for j in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * j / n)
        out.append((c[0] + math.cos(a) * rx * k, c[1] + math.sin(a) * ry * k))
    return out


def drip(cv, x, y, length, depth=0):
    """A tar strand hanging from (x, y): a 1 px strand ending in a 2 px drop with a glint, outlined dark."""
    x, y = int(math.floor(x)), int(math.floor(y))
    body = T[max(1, 2 - depth)]
    for k in range(length):
        cv.put(x, y + k, body)
        cv.put(x + 1, y + k, T[0])
    for (dx, dy) in ((0, length), (1, length), (0, length + 1), (1, length + 1)):
        cv.put(x + dx, y + dy, T[1])
    cv.put(x, y + length, T[3] if not depth else T[2])
    cv.put(x - 1, y + length + 1, T[0])
    cv.put(x + 2, y + length + 1, T[0])
    cv.put(x, y + length + 2, T[0])
    cv.put(x + 1, y + length + 2, T[0])


def lit_side(xf):
    """The local normal (0, -1) or (0, 1) of a segment frame that faces the light."""
    up = xf.rvec((0.0, -1.0))
    return -1.0 if up[0] * LIGHT_DIR[0] + up[1] * LIGHT_DIR[1] >= 0.0 else 1.0


def near_edge(inner, d):
    """The pixels of a region within d px of its outside (a band along the silhouette)."""
    band = set()
    frontier = {q for q in inner if any((q[0] + dx, q[1] + dy) not in inner for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    band |= frontier
    for _ in range(d - 1):
        nxt = set()
        for (x, y) in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in inner and q not in band:
                    nxt.add(q)
        band |= nxt
        frontier = nxt
    return band


def crescent(cv, xf, c, rx, ry, inner, k=0.9, off=(1.9, 2.3), threshold=0.5):
    """A wet highlight on a bulge: the band between an ellipse and the same ellipse pushed down-right by `off` px,
    kept where it faces the light: Iron 2, Iron 3 at its brightest (only on `inner` pixels). The facing is measured in
    the bulge's own space, so the highlight rides the part (stable pixels)."""
    scale = math.sqrt(abs(xf.a * xf.d - xf.b * xf.c)) or 1.0
    outer = Canvas.raster(None, xf, Ellipse(c[0], c[1], rx * k, ry * k))
    cut = Canvas.raster(None, xf, Ellipse(c[0] + off[0] / scale, c[1] + off[1] / scale, rx * k, ry * k))
    for (x, y) in (outer - cut) & inner:
        lx, ly = xf.inv((x + 0.5, y + 0.5))
        dx, dy = lx - c[0], ly - c[1]
        d = math.hypot(dx, dy) or 1.0
        dot = (dx * LIGHT_DIR[0] + dy * LIGHT_DIR[1]) / d
        if dot > threshold:
            cv.put(x, y, T[4] if dot > 0.94 else T[3])


def despeckle(cv):
    """No lone pixels (D4): a pixel whose four neighbours are all opaque and all a different colour takes the commonest
    of them (glow pixels are left alone)."""
    px = cv.px
    changes = {}
    for (x, y), col in px.items():
        if (x, y) in cv.glow:
            continue
        nb = [px.get((x + 1, y)), px.get((x - 1, y)), px.get((x, y + 1)), px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    px.update(changes)


def selout(cv):
    """Selective outline (D4 rule 3 allows it): the outline on the lit side (open to the top or the left) one step
    lighter, so the silhouette reads soft on top and hard underneath."""
    lighter = {T[0]: T[1], BN[0]: BN[1]}
    out = {}
    for (x, y), col in cv.px.items():
        if col not in lighter or (x, y) in cv.glow:
            continue
        if ((x - 1, y) not in cv.px or (x, y - 1) not in cv.px) and (x + 1, y) in cv.px and (x, y + 1) in cv.px:
            out[(x, y)] = lighter[col]
    cv.px.update(out)


def merge_creases(cv, region):
    """Where the lower and the upper body meet inside the mass their outlines leave dark seams; an outline pixel with
    tar on all four sides is not an edge of anything, so it takes the deep shade (no seams inside one material)."""
    tar = set(T[1:])
    for _ in range(2):
        out = {}
        for q in region:
            if cv.px.get(q) != T[0]:
                continue
            nb = [cv.px.get((q[0] + 1, q[1])), cv.px.get((q[0] - 1, q[1])), cv.px.get((q[0], q[1] + 1)), cv.px.get((q[0], q[1] - 1))]
            if all(n in tar or n == T[0] for n in nb) and sum(1 for n in nb if n in tar) >= 2:
                out[q] = T[1]
        cv.px.update(out)


# ================================================================================================
# Pose
# ================================================================================================
WAIST = (0.0, -24.0)                                          # big moves lean the mass about this point
NECK = (-22.0, -74.0)                                         # the skull's jaw hinge sits here on the upper body
SHOULDER_NEAR = (-26.0, -46.0)                                # the arms hang off the lower body (they stay put while it breathes)
SHOULDER_FAR = (16.0, -56.0)
REST_NEAR = (-50.0, -4.0)                                     # the claw planted in the puddle in front
REST_FAR = (46.0, -5.0)
NEAR_L1, NEAR_L2 = 28.0, 26.0
FAR_L1, FAR_L2 = 20.0, 19.0
FEMUR_LEN = 44.0
FEMUR_GRIP = 6.0                                              # the grip sits this far down the shaft from the ball
FEMUR_BASE = (30.0, -80.0)                                    # where the femur goes into the back (upper space)
FEMUR_BACK_DIR = 134.0                                        # its condyles point into the mass (screen degrees)
JAW_OPEN_DEG = 30.0
SKULL_SCALE = 1.12
VENT = (13.0, -95.0)                                          # the top of the hump between two spines: the bones fly out here

DEFAULTS = dict(up=(0.0, 0.0), squash=0.0, lean=0.0, shake=0, head=(0.0, 0.0), tilt=0.0, jaw=0.06, near=REST_NEAR, grip=0.2,
                far=REST_FAR, far_grip=0.3, stretch=1.0, melt=0.0, sag=0.0, spread=0.0, bones=1.0, tar=1.0, inflate=0.0, eyes=1.0,
                mouth_glow=0.0, drip=0, ripple=0.0, bubble=0.0, plunge=0.0, fall=0.0)
DISCRETE = ("drip", "shake")


class Pose:
    def __init__(self, **kw):
        for k, v in DEFAULTS.items():
            setattr(self, k, v)
        for k, v in kw.items():
            if k not in DEFAULTS:
                raise KeyError(k)
            setattr(self, k, v)

    def but(self, **kw):
        q = Pose(**{k: getattr(self, k) for k in DEFAULTS})
        for k, v in kw.items():
            if k not in DEFAULTS:
                raise KeyError(k)
            setattr(q, k, v)
        return q


def tween(a, b, t):
    """The pose a fraction t of the way from a to b (numbers and points lerp; discrete fields switch at the end)."""
    q = Pose()
    for k in DEFAULTS:
        va, vb = getattr(a, k), getattr(b, k)
        if k in DISCRETE:
            setattr(q, k, va if t < 1.0 else vb)
        elif isinstance(va, tuple):
            setattr(q, k, lerp2(va, vb, t))
        else:
            setattr(q, k, lerp(va, vb, t))
    return q


def base_xf(p):
    """The lower body (mass space -> rig): squash and melt about the ground under it, a lean about the waist (big moves
    only; the loops never lean)."""
    sy = (1.0 - p.squash) * (1.0 - 0.72 * p.melt) * (0.1 + 0.9 * p.tar)
    sx = (1.0 + 0.5 * p.squash) * (1.0 + 0.32 * p.melt + 0.12 * p.spread) * (0.6 + 0.4 * min(1.0, p.tar))
    return Xf.pose(p.lean, WAIST, (0.0, 0.0)).then(Xf(sx, 0.0, 0.0, sy, 0.0, 0.0))


def upper_xf(p):
    """The upper body: the lower body's transform plus a whole-pixel offset (the breathing and the ooze)."""
    ux, uy = rnd(p.up)
    return Xf.pose(0.0, (0.0, 0.0), (ux + p.shake, uy)).then(base_xf(p))


def bone_drop(p):
    """How far the bones sit below their places (rising out of / sinking into the puddle; sagging as it dies)."""
    return int(round((1.0 - p.bones) * 140.0 + p.sag * 14.0))


def place(p, xf, pt, angle, sag_turn=0.0):
    """A rigid bone placed at point `pt` of the space `xf`, turned by `angle` (+ the lean, + a droop as it sags)."""
    x, y = xf.fwd(pt)
    return Xf.pose(angle + p.lean + sag_turn * p.sag, (0.0, 0.0), (round(x), round(y) + bone_drop(p)))


# ================================================================================================
# The mass
# ================================================================================================
def base_blobs(p):
    """The lower body as ellipses in mass space: (centre, rx, ry): the base flowing into the puddle, the belly, the haunch."""
    inf = p.inflate
    return (((0.0, -15.0), 54.0, 17.0),
            ((-6.0, -37.0 - 2.0 * inf), 46.0 + 4.0 * inf, 27.0 + 3.0 * inf),
            ((36.0, -30.0), 26.0, 24.0))


def upper_blobs(p):
    """The upper body: the hump and the front shoulder (the throat under the skull)."""
    inf = p.inflate
    return (((6.0, -63.0 - 2.0 * inf), 40.0 + 3.0 * inf, 34.0 + 4.0 * inf),
            ((-27.0, -60.0 - 1.0 * inf), 22.0 + 4.0 * inf, 22.0 + 3.0 * inf))


def puddle(cv, p):
    """The pool it never leaves: a wide flat ellipse with rings of gloss drifting outwards with `ripple`, and a few
    bubbles on it that swell and pop in turn."""
    cx = 4.0 + 8.0 * p.spread
    rx = 64.0 + 26.0 * p.spread + 10.0 * p.melt
    ry = 5.0 + 1.5 * p.spread
    pin = cv.part(Xf(), Ellipse(cx, -1.0, rx, ry), "tar", dome(cx - 20.0, -6.0, rx, lo=1, hi=2, gain=1.0, bias=-0.25, fixed=True), rust=0.0)
    cv.puddle = cv.raster(Xf(), Ellipse(cx, -1.0, rx, ry))      # kept out of the hit strips: the pool itself is harmless
    for k in range(3):
        r = 14.0 + ((k * 16.0 + p.ripple * 16.0) % 48.0)
        for side in (-1, 1):
            x0 = cx + side * r
            x1 = cx + side * (r + 6.0)
            y = -3.0 + (k % 2)
            line(cv, Xf(), (min(x0, x1), y), (max(x0, x1), y), lambda n: T[3] if n % 3 else T[2], pin)
    for k, (bx, r) in enumerate(((-52.0, 2.2), (-42.0, 1.5), (52.0, 2.0), (62.0, 1.5))):
        ph = (p.drip + k * 3) % 8
        if ph >= 6:
            continue                                            # popped: a gap of two frames before the next one swells
        rr = r * (0.6 + 0.1 * ph)
        bub = cv.part(Xf(), Ellipse(bx, -2.0 - rr * 0.6, rr + 0.6, rr), "tar", dome(bx - 1.0, -3.0 - rr, rr + 1.0, lo=1, hi=2, fixed=True), rust=0.0)
        q = P(Xf(), (bx - rr * 0.5, -2.0 - rr * 1.1))
        if q in bub:
            cv.put(q[0], q[1], T[3])
    return pin


def mass(cv, p, bx, ux, pin):
    """The tar mound: the lower body and the upper body, two parts that flow into each other without a seam (one
    surface), each lit in its own space. Returns the tar's pixels."""
    lows = base_blobs(p)
    base = Union(*[Posed(bx, Ellipse(c[0], c[1], rx, ry)) for c, rx, ry in lows])
    base_in = cv.part(Xf(), base, "tar", space_dome(bx, -22.0, -90.0, 92.0, lo=1, hi=2, gain=1.35, bias=-0.15), rust=0.0, merge=pin)
    ups = upper_blobs(p)
    upper = Union(*[Posed(ux, Ellipse(c[0], c[1], rx, ry)) for c, rx, ry in ups])
    up_in = cv.part(Xf(), upper, "tar", space_dome(ux, -22.0, -90.0, 92.0, lo=1, hi=2, gain=1.35, bias=-0.15), rust=0.0, merge=pin | base_in)
    base_in -= up_in
    tar = base_in | up_in
    merge_creases(cv, {q for q in cv.px if q in tar or any((q[0] + dx, q[1] + dy) in tar for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))})
    # wet gloss: a crescent on the lit (top-left) side of every bulge, only near the silhouette (no rings inside it)
    rim = near_edge(tar, 4)
    for c, rx, ry in lows[1:]:
        crescent(cv, bx, c, rx, ry, rim & base_in)
    for c, rx, ry in ups:
        crescent(cv, ux, c, rx, ry, rim & up_in)
    for (xf, region, c, rx, ry) in ((bx, base_in, (-40.0, -30.0), 9.0, 8.0), (ux, up_in, (26.0, -50.0), 9.0, 8.0), (bx, base_in, (48.0, -22.0), 7.0, 7.0)):
        crescent(cv, xf, c, rx, ry, region, 1.0, (1.4, 1.6), 0.7)
    # creases where the mass folds over itself
    for (xf, region, a, b) in ((bx, base_in, (-36, -26), (-22, -22)), (bx, base_in, (10, -30), (24, -34)), (ux, up_in, (30, -48), (44, -44)),
                               (bx, base_in, (-14, -14), (2, -12))):
        line(cv, Xf(), xf.fwd(a), xf.fwd(b), lambda n: T[0], region)
        line(cv, Xf(), xf.fwd((a[0], a[1] + 1)), xf.fwd((b[0], b[1] + 1)), lambda n: T[2] if n % 2 else None, region)
    # bubbles rising through it and popping at the surface
    for k, (xf, region, (qx, qy)) in enumerate(((bx, base_in, (-30.0, -40.0)), (ux, up_in, (20.0, -50.0)), (bx, base_in, (42.0, -22.0)),
                                                 (bx, base_in, (-6.0, -24.0)), (ux, up_in, (-18.0, -64.0)))):
        phase = (p.drip + k * 3) % 8
        if phase >= 6:
            continue
        r = 1 if phase < 3 else 2
        q = P(xf, (qx, qy - phase))
        ring = [(r, 0), (-r, 0), (0, r), (0, -r)] + ([(1, 1), (-1, -1), (1, -1), (-1, 1)] if r == 2 else [])
        for (dx, dy) in ring:
            if (q[0] + dx, q[1] + dy) in region:
                cv.put(q[0] + dx, q[1] + dy, T[3] if dy < 0 or dx < 0 else T[0])
    return tar


def collar(cv, xf, centre, rx, ry, under):
    """A lip of tar where a bone goes into the mass (merged into it, no seam)."""
    return cv.part(xf, Ellipse(centre[0], centre[1], rx, ry), "tar", dome(centre[0] - 2, centre[1] - 2, max(rx, ry) + 2, lo=1, hi=2, gain=1.3),
                   rust=0.0, merge=under)


# ================================================================================================
# Bones (placed rigidly: they only turn in the melt, the rise and the death)
# ================================================================================================
def long_bone(cv, xf, a, b, r0, r1, depth=0, hi=4, shadow=(1, 1), snap=None):
    """A shaft of bone from a to b (local), lit across its axis (`snap`: the light follows big turns only)."""
    return cv.part(xf, Capsule(a, b, r0, r1), "bone", cyl(a, b, max(r0, r1), lo=1, hi=hi, gain=1.6, bias=-0.05, snap=snap), depth=depth,
                   shadow=shadow if not depth else None, rust=0.0)


def knob(cv, xf, c, rx, ry, depth=0, hi=4, snap=None):
    return cv.part(xf, Ellipse(c[0], c[1], rx, ry), "bone",
                   dome(c[0] - rx * 0.4, c[1] - ry * 0.5, max(rx, ry) * 1.3, lo=1, hi=hi, gain=1.4, bias=0.0, snap=snap),
                   depth=depth, shadow=None if depth else (1, 1), rust=0.0)


def rib(cv, xf, length, bow, r0, depth=0):
    """A rib in its own space: from the root (0, 0) down (+y), bowing forward (-x) and back in."""
    pts = []
    for j in range(7):
        t = j / 6.0
        pts.append((-bow * math.sin(math.pi * t * 0.9) + 2.0 * t, length * t))
    parts = []
    for j in range(6):
        ra = r0 * (1.0 - 0.45 * j / 6.0)
        rb = r0 * (1.0 - 0.45 * (j + 1) / 6.0)
        parts.append(Capsule(pts[j], pts[j + 1], ra, rb))
    inner = cv.part(xf, Union(*parts), "bone", cyl((0, 0), (0, length), r0 + 1.0, lo=1, hi=4 - depth, gain=1.6, bias=-0.1), depth=depth,
                    shadow=None if depth else (1, 1), rust=0.0)
    return pts, inner


def spine(cv, xf, length, depth=0):
    """A neural spine in its own space: base (0, 0), the blade up (-y), a knob of vertebra at the foot."""
    blade = Poly([(-2.6, 0.0), (2.6, 0.0), (1.8, -length * 0.55), (0.6, -length), (-0.8, -length + 1.0), (-2.0, -length * 0.5)])
    inner = cv.part(xf, blade, "bone", cyl((0, 0), (0, -length), 3.0, lo=1, hi=4 - depth, gain=1.6, bias=-0.05), depth=depth,
                    shadow=None if depth else (1, 1), rust=0.0)
    line(cv, xf, (-0.2, -1.0), (0.2, -length * 0.7), lambda n: BN[2] if n % 3 else None, inner)      # the blade's ridge
    return inner


def femur_shapes():
    """The femur in its own space: the grip at (0, 0), the ball end up (-y), the condyles down (+y)."""
    top = -FEMUR_GRIP
    bot = FEMUR_LEN - FEMUR_GRIP
    shaft = Capsule((0.0, top + 3.0), (0.0, bot - 4.0), 3.2, 3.6)
    ball = Union(Ellipse(-3.2, top - 1.0, 3.8, 3.6), Capsule((-2.4, top), (0.4, top + 3.0), 2.4))
    trochanter = Ellipse(2.6, top + 1.5, 2.8, 3.4)
    condyles = Union(Ellipse(-2.8, bot - 1.0, 4.4, 3.8), Ellipse(3.0, bot - 1.4, 4.0, 3.6))
    return shaft, ball, trochanter, condyles


def femur(cv, xf, depth=0):
    shaft, ball, trochanter, condyles = femur_shapes()
    top = -FEMUR_GRIP
    bot = FEMUR_LEN - FEMUR_GRIP
    inner = long_bone(cv, xf, (0.0, top + 3.0), (0.0, bot - 4.0), 3.2, 3.6, depth)
    inner |= cv.part(xf, trochanter, "bone", dome(1.5, top, 4.0, lo=1, hi=4, gain=1.4, bias=0.0), depth=depth, rust=0.0)
    inner |= cv.part(xf, ball, "bone", dome(-4.5, top - 2.5, 5.0, lo=1, hi=4, gain=1.4, bias=0.05), depth=depth, rust=0.0)
    inner |= cv.part(xf, condyles, "bone", dome(-3.0, bot - 3.0, 6.0, lo=1, hi=4, gain=1.4, bias=0.0), depth=depth,
                     shadow=None if depth else (1, 1), rust=0.0)
    line(cv, xf, (0.0, bot - 3.0), (0.0, bot + 1.0), lambda n: BN[1], inner)                         # the notch between the condyles
    line(cv, xf, (-1.4, top + 6.0), (-1.0, bot - 8.0), lambda n: BN[4] if n % 5 == 2 else None, inner)  # glints down the shaft
    return inner


# --- the skull (lit in its own space: it tilts in the big moves) ----------------------------------------------------------
SKULL = [(9, -8), (11, -18), (6, -26), (-3, -30), (-9, -31), (-14, -28), (-26, -25), (-38, -21), (-46, -17), (-49, -13),
         (-48, -9), (-40, -7), (-28, -6), (-14, -5), (-2, -5)]
ORBIT = Union(Ellipse(-10.5, -21.5, 3.4, 3.6), Ellipse(-11.0, -17.5, 2.0, 2.6))
ANTORBITAL = Poly([(-17, -22), (-29, -19), (-27, -13), (-17, -14)])
TEMPORAL = Poly([(-3, -23), (4, -22), (4, -14), (-2, -15)])
NOSTRIL = Ellipse(-43.0, -16.0, 2.4, 1.5)
MAXILLARY = Ellipse(-33.5, -13.5, 1.5, 1.3)
JAW = [(6, -7), (4, -1), (-8, 2), (-22, 1), (-36, -2), (-44, -5), (-45, -8), (-30, -7), (-14, -6), (-2, -6)]
JAW_HOLE = Ellipse(-6.0, -2.5, 3.0, 1.4)
HINGE = (0.0, -5.0)
UPPER_TEETH = (-45, -41, -37, -33, -29, -25, -21, -17, -13)
LOWER_TEETH = (-41, -37, -33, -29, -25, -21, -17)


def head_xf(p, ux):
    x, y = ux.fwd(NECK)
    hx, hy = rnd(p.head)
    return Xf.pose(p.lean * 0.6 + p.tilt - 16.0 * p.sag, (0.0, 0.0),
                   (round(x) + hx, round(y) + hy + bone_drop(p) + int(round(6.0 * p.sag)))).then(Xf(SKULL_SCALE, 0.0, 0.0, SKULL_SCALE, 0.0, 0.0))


def jaw_xf(p, hxf):
    return hxf.then(Xf.pose(-p.jaw * JAW_OPEN_DEG, HINGE))


def tooth(cv, xf, x, y0, length, down):
    """A conical tooth (local), pointing down (upper jaw) or up (lower jaw)."""
    s = 1.0 if down else -1.0
    tip = (x - 0.6, y0 + s * length)
    shape = Poly([(x - 1.4, y0), (x + 1.4, y0), tip])
    inner = cv.part(xf, shape, "bone", flat(3, bevel=False), rust=0.0)
    q = P(xf, (x - 0.4, y0 + s * 1.0))
    if q in inner:
        cv.put(q[0], q[1], BN[4])
    return inner


def head(cv, glow, p, ux, under):
    """The skull on the front of the mass: mouth, lower jaw, skull, teeth, the tar over the back of it, the eye."""
    hxf = head_xf(p, ux)
    jxf = jaw_xf(p, hxf)
    if p.jaw > 0.08:                                       # the inside of the open maw: tar, hot at the back
        upper = [hxf.fwd((x, -6.0)) for x in (2.0, -10.0, -22.0, -34.0, -44.0)]
        lower = [jxf.fwd((x, -7.0)) for x in (-44.0, -34.0, -22.0, -10.0, 2.0)]
        maw = cv.part(Xf(), Poly(upper + lower), "tar", flat(1, bevel=False), rust=0.0)
        heat = p.mouth_glow
        for (x, y) in maw:
            lx, ly = hxf.inv((x + 0.5, y + 0.5))
            if heat > 0.0 and lx > -30.0 + 22.0 * (1.0 - heat):
                col = E[2] if lx > -12.0 + 10.0 * (1.0 - heat) else E[1]
                cv.put_glow(x, y, col)
                glow.put_glow(x, y, col)
        xs = sorted({x for (x, _) in maw})
        for k, x in enumerate(xs[3::7]):                    # tar strands strung across the maw
            for q in [q for q in maw if q[0] == x]:
                if q not in glow.glow:
                    cv.put(q[0], q[1], T[2] if (q[1] + k) % 3 else T[3])
    jaw = cv.part(jxf, Poly(JAW), "bone", dome(-24.0, -8.0, 30.0, lo=1, hi=4, gain=1.25, bias=0.05, bevel=True, fixed=True), shadow=(1, 1), rust=0.0)
    for x in LOWER_TEETH:
        tooth(cv, jxf, x, -6.5, 2.6, down=False)
    for q in cv.raster(jxf, JAW_HOLE) & jaw:
        cv.put(q[0], q[1], T[1])
    line(cv, jxf, (-42.0, -3.0), (-8.0, 0.0), lambda n: BN[2] if n % 2 else None, jaw)          # the jaw's lower ridge
    skull = cv.part(hxf, Poly(SKULL), "bone", dome(-22.0, -30.0, 34.0, lo=1, hi=4, gain=1.3, bias=0.1, bevel=True, fixed=True), shadow=(1, 2), rust=0.0)
    for x in UPPER_TEETH:
        tooth(cv, hxf, x, -6.0, 3.4 if x > -40 else 2.8, down=True)
    # the 3/4 top: the far side's brow and nasal ridge catch the light over the near side
    line(cv, hxf, (-46.0, -17.5), (-27.0, -25.0), lambda n: BN[4] if n % 4 else BN[3], skull)
    line(cv, hxf, (-24.0, -26.0), (-6.0, -30.0), lambda n: BN[4] if n % 3 else BN[3], skull)
    # the openings: dark tar inside the skull
    for hole in (ANTORBITAL, TEMPORAL, NOSTRIL, MAXILLARY, ORBIT):
        px = cv.raster(hxf, hole) & skull
        edge = {q for q in px if any((q[0] + dx, q[1] + dy) not in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        for q in px:
            cv.put(q[0], q[1], T[0] if q in edge else T[1])
        for q in px:                                         # the rim below each opening catches a little light
            below = (q[0], q[1] + 1)
            if below in skull and below not in px:
                cv.put(below[0], below[1], BN[2])
    # tar oozing over the back of the skull into the mass (no seam with the mass)
    mane = Union(Ellipse(9.0, -16.0, 7.0, 12.0), Ellipse(3.0, -27.0, 6.0, 4.0), Poly([(2, -30), (14, -26), (14, -4), (6, -2)]))
    lip = cv.part(hxf, mane, "tar", dome(4.0, -26.0, 14.0, lo=1, hi=2, gain=1.3, fixed=True), shadow=(1, 1), rust=0.0, merge=under)
    gloss_line(cv, hxf.fwd((2.0, -28.0)), hxf.fwd((10.0, -24.0)), lip)
    drip(cv, *P(hxf, (4.0, -21.0)), 2 + p.drip % 3)
    drip(cv, *P(jxf, (-24.0, 1.0)), 1 + (p.drip + 1) % 3)
    drip(cv, *P(jxf, (-10.0, 2.0)), 2 + (p.drip + 2) % 3)
    # the eye: an ember deep in the orbit
    eye_c = (-10.5, -20.5)
    if p.eyes > 0.05:
        level_ = p.eyes
        for (x, y) in cv.raster(hxf, Ellipse(eye_c[0], eye_c[1], 1.2 + 0.9 * min(1.0, level_ - 0.6) if level_ > 0.6 else 1.0, 1.4)):
            if (x, y) in skull:
                col = E[3] if level_ >= 0.9 else (E[2] if level_ > 0.4 else E[1])
                cv.put_glow(x, y, col)
                glow.put_glow(x, y, col)
        if level_ > 1.3:                                    # blazing: the ember fills the orbit
            for (x, y) in cv.raster(hxf, ORBIT) & skull:
                if (x, y) not in glow.glow:
                    cv.put_glow(x, y, E[1])
                    glow.put_glow(x, y, E[1])
    return hxf, jxf, skull | jaw


# --- the claw (lit in 45-degree steps: the arm moves in the loops) ---------------------------------------------------------
def claw(cv, hx, grip, scale=1.0, depth=0, spread=1.0):
    """A three-taloned bone claw in the hand's space: +x along the forearm from the wrist."""
    s = scale
    palm = cv.part(hx, Union(Capsule((0.0, -1.0 * s), (7.0 * s, -2.0 * s), 3.2 * s), Capsule((0.0, 1.0 * s), (7.0 * s, 2.4 * s), 3.0 * s)), "bone",
                   cyl((0, 0), (7 * s, 0), 3.4 * s, lo=1, hi=4 - depth, gain=1.3, bias=0.2, snap=LIMB_SNAP), depth=depth,
                   shadow=None if depth else (1, 1), rust=0.0)
    tips = []
    for d in (-1, 0, 1):
        base = (7.0 * s, d * 2.8 * s)
        a = math.radians(d * 26.0 * spread)
        curl = math.radians(10.0 + grip * 62.0)
        p1 = (base[0] + math.cos(a + curl * 0.5) * 6.0 * s, base[1] + math.sin(a + curl * 0.5) * 6.0 * s)
        p2 = (p1[0] + math.cos(a + curl * 1.1) * 5.0 * s, p1[1] + math.sin(a + curl * 1.1) * 5.0 * s)
        p3 = (p2[0] + math.cos(a + curl * 1.8) * 7.5 * s, p2[1] + math.sin(a + curl * 1.8) * 7.5 * s)
        long_bone(cv, hx, base, p1, 1.9 * s, 1.7 * s, depth, snap=LIMB_SNAP)
        long_bone(cv, hx, p1, p2, 1.7 * s, 1.6 * s, depth, snap=LIMB_SNAP)
        talon = cv.part(hx, Capsule(p2, p3, 1.9 * s, 0.45 * s), "bone", cyl(p2, p3, 1.9 * s, lo=1, hi=3 - depth, gain=1.4, bias=0.0, snap=LIMB_SNAP),
                        depth=depth, shadow=None if depth else (1, 1), rust=0.0)
        q = P(hx, lerp2(p2, p3, 0.35))
        if q in talon and not depth:
            cv.put(q[0], q[1], BN[4])
        knob(cv, hx, p1, 1.6 * s, 1.6 * s, depth, snap=LIMB_SNAP)
        tips.append(hx.fwd(p3))
    return palm, tips


# ================================================================================================
# Arms
# ================================================================================================
def tar_limb(cv, a, b, r0, r1, depth=0):
    xf = seg_xf(a, b)
    ln = max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]))
    inner = cv.part(xf, Capsule((0, 0), (ln, 0), r0, r1), "tar", cyl((0, 0), (ln, 0), max(r0, r1), lo=1, hi=2, gain=1.4, bias=-0.3, snap=LIMB_SNAP),
                    depth=depth, shadow=None if depth else (1, 1), rust=0.0)
    side = lit_side(xf)
    if not depth:
        gloss_line(cv, xf.fwd((ln * 0.12, side * (r0 - 2.0))), xf.fwd((ln * 0.78, side * (r1 - 2.0))), inner)
    return xf, ln, inner


def shoulder_of(p, bx, point):
    sx, sy = bx.fwd(point)
    return (round(sx), round(sy) + int(round(bone_drop(p) * 0.6)))


def near_arm(cv, p, bx):
    """The claw arm (near plane): a thick tar arm, the forearm's bones showing, a bone claw. Returns the palm point."""
    shoulder = shoulder_of(p, bx, SHOULDER_NEAR)
    elbow, wrist = ik(shoulder, rnd(p.near), NEAR_L1 * p.stretch, NEAR_L2 * p.stretch, 1)
    sh = cv.part(Xf(), Ellipse(shoulder[0], shoulder[1], 12.5, 11.0), "tar", dome(shoulder[0] - 5, shoulder[1] - 6, 13, lo=1, hi=2, gain=1.3), rust=0.0)
    crescent(cv, Xf(), shoulder, 12.5, 11.0, sh)
    ux_, lu, up = tar_limb(cv, shoulder, elbow, 11.0, 9.0)
    fx, lf, fore = tar_limb(cv, elbow, wrist, 9.0, 7.0)
    side = lit_side(fx)                                    # the bones of the forearm show through a tear in the tar
    long_bone(cv, fx, (lf * 0.34, side * 1.6), (lf * 0.74, side * 1.2), 1.8, 1.6, hi=3, snap=LIMB_SNAP)
    a = fx.fwd((lf * 0.5, -6.0))                            # a strand of tar across the bone
    b = fx.fwd((lf * 0.5 + 1.5, 6.0))
    line(cv, Xf(), a, b, lambda n: T[1] if n % 2 else T[2], fore)
    knob(cv, Xf(), (elbow[0] + (elbow[0] - wrist[0]) * 0.08, elbow[1] + (elbow[1] - wrist[1]) * 0.08), 3.0, 2.8, snap=LIMB_SNAP)   # the elbow's point
    ang = math.degrees(math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]))
    hx = Xf.pose(ang, (0.0, 0.0), wrist)
    claw(cv, hx, p.grip, 1.3)
    drip(cv, *P(ux_, (lu * 0.6, 7.0)), 1 + (p.drip + 1) % 3)
    drip(cv, *P(hx, (2.0, 3.0)), 1 + p.drip % 3)
    return hx.fwd((7.8, 0.0))


def far_arm(cv, p, bx):
    """The far arm (far plane, one ramp step darker): a smaller tar arm and claw behind the mass."""
    d = 1
    shoulder = shoulder_of(p, bx, SHOULDER_FAR)
    elbow, wrist = ik(shoulder, rnd(p.far), FAR_L1, FAR_L2, 1)
    tar_limb(cv, shoulder, elbow, 7.5, 6.5, d)
    tar_limb(cv, elbow, wrist, 6.5, 5.0, d)
    ang = math.degrees(math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]))
    claw(cv, Xf.pose(ang, (0.0, 0.0), wrist), p.far_grip, 0.8, d, 0.8)


# ================================================================================================
# One frame
# ================================================================================================
RIBS = (((-13.0, -82.0), 10.0, 38.0, 10.0), ((-1.0, -86.0), 5.0, 40.0, 11.0), ((11.0, -84.0), 0.0, 38.0, 10.5), ((23.0, -78.0), -6.0, 32.0, 9.0))
BACK_RIBS = (((14.0, -84.0), 196.0, 30.0, 6.0), ((30.0, -74.0), 208.0, 30.0, 6.0), ((44.0, -58.0), 222.0, 24.0, 5.0))
SHARDS = (((50.0, -34.0), 70.0, 9.0), ((40.0, -14.0), 96.0, 7.0), ((-44.0, -18.0), -64.0, 7.0))
SPINES = (((-16.0, -88.0), -20.0, 13.0), ((-5.0, -93.0), -14.0, 16.0), ((7.0, -95.0), -6.0, 18.0), ((19.0, -92.0), 4.0, 16.0),
          ((33.0, -83.0), 14.0, 13.0), ((44.0, -71.0), 24.0, 11.0), ((52.0, -57.0), 34.0, 8.0))


FEMUR_SOCKET = FEMUR_LEN - FEMUR_GRIP - 10.0                 # this far down the shaft it goes into the back (10 px buried)
FEMUR_LIE_ANGLE = 100.0                                       # where it ends as it dies: lying on the pool behind the mass,
FEMUR_LIE_SOCKET = (50.0, -7.0)                               # ball end back (rig space, so the slump can't bury it)


def femur_back_xf(p, ux):
    """The femur in its back, condyles in, ball end out. As it dies (p.fall) it first slides out of its socket and tips
    back (fall 0..0.25), then topples over its back onto the pool behind it (0.25..1). Returns (femur xf, socket xf)."""
    root = place(p, ux, FEMUR_BASE, 0.0)
    f = p.fall
    a0 = FEMUR_BACK_DIR - 90.0 + p.lean - 10.0 * p.sag
    loose = min(1.0, f * 4.0)
    ang = a0 + 22.0 * loose
    d = math.radians(ang)
    tx = root.tx + math.sin(d) * 7.0 * loose                  # out along the shaft, towards the ball end
    ty = root.ty - math.cos(d) * 7.0 * loose
    if f > 0.25:
        u = smooth((f - 0.25) / 0.75)
        ang = lerp(ang, FEMUR_LIE_ANGLE, u)
        tx = lerp(tx, FEMUR_LIE_SOCKET[0], u)
        ty = lerp(ty, FEMUR_LIE_SOCKET[1], u) - 8.0 * math.sin(math.pi * u)   # over the hump, then down
    return Xf.pose(ang, (0.0, 0.0), (round(tx), round(ty))).then(Xf.pose(0.0, (0.0, 0.0), (0.0, -FEMUR_SOCKET))), root


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    bx, ux = base_xf(p), upper_xf(p)
    far_arm(far, p, bx)
    pin = puddle(mid, p)
    for (pt, ang, ln, bow) in BACK_RIBS:                    # the far side's ribs arch up out of the back (the mass hides their roots)
        rib(mid, place(p, ux, pt, ang, 14.0), ln, -bow, 2.8)
    tar = mass(mid, p, bx, ux, pin)
    under = tar | pin
    for (root, ang, ln) in SHARDS:                         # broken bones sticking out of the haunch and the base
        xf = place(p, bx, root, ang, 18.0)
        spine(mid, xf, ln)
        under |= collar(mid, xf, (0.0, 1.0), 3.6, 2.4, under)
    for k, (root, ang, ln, bow) in enumerate(RIBS):        # the ribcage on the near flank
        xf = place(p, ux, root, ang, 22.0 + 6.0 * k)
        pts, inner = rib(mid, xf, ln, bow, 3.0)
        under |= collar(mid, xf, (0.0, 1.0), 4.0, 3.0, under)
        end = pts[-1]
        under |= collar(mid, xf, (end[0], end[1] - 1.0), 4.5, 3.0, under)
        drip(mid, *P(xf, (pts[4][0] + 1.5, pts[4][1])), 1 + (p.drip + k) % 3)
    fxf, root = femur_back_xf(p, ux)                         # the femur in its back
    socket = (root.tx, root.ty)
    if p.fall < 0.3:
        femur(mid, fxf)
        under |= collar(mid, Xf(), fxf.fwd((0.0, FEMUR_SOCKET)), 6.0, 4.5, under)
    else:
        mid.part(Xf(), Ellipse(socket[0], socket[1], 4.0, 3.0), "tar", flat(1, bevel=False), rust=0.0, merge=under)   # the hole it left
        femur(mid, fxf)
    for (root_, ang, ln) in SPINES:                        # the ridge of neural spines
        xf = place(p, ux, root_, ang, 20.0)
        spine(mid, xf, ln)
        under |= collar(mid, xf, (0.0, 1.0), 4.0, 2.6, under)
    hxf, jxf, skull = head(mid, glow, p, ux, under)
    if p.bubble > 0.0:                                     # a last bubble swelling on the slumped mass (death)
        r = 2.0 + 5.0 * p.bubble
        top = ux.fwd((10.0, -92.0))
        c = (top[0], top[1] - r * 0.6)
        bub = mid.part(Xf(), Ellipse(c[0], c[1], r, r * 0.85), "tar", dome(c[0] - r * 0.4, c[1] - r * 0.5, r * 1.3, lo=1, hi=2, fixed=True), rust=0.0)
        gloss_line(mid, (c[0] - r * 0.6, c[1] - r * 0.3), (c[0] - r * 0.1, c[1] - r * 0.75), bub, 2)
    hand = near_arm(near, p, bx)
    if p.plunge > 0.0:                                     # tar thrown up where the claw went into the puddle
        for k in range(5):
            x = hand[0] - 12.0 + k * 6.0
            h = (3.0 + (k * 7) % 5) * p.plunge
            line(mid, Xf(), (x, -1.0), (x + (k - 2) * 0.6, -1.0 - h), lambda n: T[2] if n % 2 else T[3])
    for cv in (far, mid, near):
        despeckle(cv)
    selout(mid)
    pts = {
        "mouth": hxf.fwd((-40.0, -6.0)) if p.jaw < 0.3 else lerp2(hxf.fwd((-40.0, -6.0)), jxf.fwd((-40.0, -7.0)), 0.5),
        "eye": hxf.fwd((-10.5, -20.5)),
        "hand": hand,
        "core": bx.fwd((0.0, -48.0)),
        "top": ux.fwd((6.0, -96.0)),
        "vent": ux.fwd(VENT),
        "puddle": mid.puddle,
    }
    return far, mid, near, glow, pts


# ================================================================================================
# Frame list (index = TarTyrantRigData constants). Every sequence is tweened from key poses.
# ================================================================================================
IDLE = Pose()
FRAMES = []
SEQS = {}


def add(name, poses):
    SEQS[name] = (len(FRAMES), len(poses))
    for k, q in enumerate(poses):
        FRAMES.append(("%s%d" % (name, k), q))


# idle: the upper body breathes one whole pixel up and down, the skull a beat later; drips run, bubbles rise in it and
# pop on the pool (8, a loop)
UP_IDLE = (0, 0, -1, -1, -1, -1, 0, 0)
HEAD_IDLE = (0, 0, 0, -1, -1, -1, -1, 0)
add("Idle", [IDLE.but(up=(0.0, UP_IDLE[k]), head=(0.0, HEAD_IDLE[k]), drip=k, ripple=k / 8.0) for k in range(8)])

# ooze: the upper body lurches forward and back by whole pixels, the claw reaches out, plants and drags it along, the far
# claw paddles behind (8, a loop)
UP_MOVE = ((0, 0), (-1, 0), (-2, -1), (-2, -1), (-1, 0), (0, 0), (1, -1), (1, -1))
HAND_MOVE = ((0, 0), (-4, -5), (-8, -8), (-10, -3), (-8, 1), (-4, 1), (-1, 1), (1, 0))
FAR_MOVE = ((4, 0), (3, 0), (0, 0), (-3, -3), (-4, -4), (-3, -3), (0, 0), (3, 0))
GRIP_MOVE = (0.2, 0.4, 0.5, 0.4, 0.2, 0.2, 0.2, 0.2)
add("Move", [IDLE.but(up=UP_MOVE[k], head=(UP_MOVE[(k - 1) % 8][0], 0), near=(REST_NEAR[0] + HAND_MOVE[k][0], REST_NEAR[1] + HAND_MOVE[k][1]),
                      far=(REST_FAR[0] + FAR_MOVE[k][0], REST_FAR[1] + FAR_MOVE[k][1]), grip=GRIP_MOVE[k], drip=k, ripple=k / 4.0, spread=0.05)
             for k in range(8)])

# burp: it swells and rears its head back, then heaves the bubbles out of its throat (10)
b1 = IDLE.but(inflate=0.5, tilt=6.0, up=(1.0, -1.0), head=(1.0, -1.0), jaw=0.0, drip=1)
b2 = IDLE.but(inflate=1.0, tilt=12.0, up=(2.0, -2.0), head=(2.0, -2.0), jaw=0.0, eyes=1.4, drip=2)
b3 = IDLE.but(inflate=0.25, tilt=-6.0, up=(-3.0, 1.0), head=(-4.0, 2.0), jaw=1.0, mouth_glow=1.0, eyes=1.6, drip=3)
b4 = IDLE.but(inflate=0.0, tilt=-2.0, up=(-1.0, 0.0), head=(-2.0, 1.0), jaw=0.6, mouth_glow=0.5, drip=4)
add("Burp", [IDLE.but(drip=0), tween(IDLE, b1, 0.5), b1, tween(b1, b2, 0.55), b2, b3, tween(b3, b4, 0.5), b4,
             tween(b4, IDLE, 0.5).but(drip=5), IDLE.but(drip=6)])

# spit: the head rears back and snaps forward, the jaws flying open (8)
s1 = IDLE.but(tilt=14.0, up=(2.0, -1.0), head=(4.0, -3.0), jaw=0.15, inflate=0.25, eyes=1.3, drip=1)
s2 = IDLE.but(tilt=-9.0, up=(-3.0, 1.0), head=(-6.0, 3.0), jaw=0.85, mouth_glow=0.8, eyes=1.5, drip=2)
s3 = IDLE.but(tilt=-5.0, up=(-2.0, 0.0), head=(-4.0, 2.0), jaw=0.5, mouth_glow=0.3, drip=3)
add("Spit", [tween(IDLE, s1, 0.35), tween(IDLE, s1, 0.7), s1, s2, tween(s2, s3, 0.5), s3, tween(s3, IDLE, 0.5).but(drip=4), IDLE.but(drip=5)])

# melt: the tar gives way and it slumps into its puddle, bones sinking, the eye going dim (8)
MELTED = IDLE.but(melt=1.0, sag=1.0, spread=0.6, bones=0.72, eyes=0.25, jaw=0.5, tilt=-14.0, near=(-60.0, 4.0), grip=0.0, far=(52.0, 2.0))
add("Melt", [tween(IDLE, MELTED, ease_in(k / 8.0)).but(drip=k) for k in range(1, 9)])

# rise: the puddle heaves, the skull and the ridge burst out, the tar climbs them and the arm tears free (10)
r0 = IDLE.but(tar=0.05, bones=0.0, spread=0.45, eyes=0.0, near=(-48.0, 30.0), far=(46.0, 20.0), jaw=0.2)
r1 = IDLE.but(tar=0.16, bones=0.28, spread=0.35, eyes=0.4, near=(-48.0, 22.0), far=(46.0, 12.0), jaw=0.3, tilt=8.0)
r2 = IDLE.but(tar=0.32, bones=0.55, spread=0.25, eyes=0.9, near=(-48.0, 10.0), jaw=0.5, tilt=12.0)
r3 = IDLE.but(tar=0.52, bones=0.78, spread=0.15, eyes=1.2, near=(-50.0, -2.0), jaw=0.7, tilt=15.0, grip=0.0)
r4 = IDLE.but(tar=0.74, bones=0.96, spread=0.05, eyes=1.5, jaw=0.85, tilt=16.0, grip=0.1, mouth_glow=0.5)
r5 = IDLE.but(tar=0.98, bones=1.04, squash=-0.06, eyes=1.6, jaw=0.95, tilt=14.0, mouth_glow=0.8)
r6 = IDLE.but(tar=1.04, bones=1.0, squash=-0.04, eyes=1.4, jaw=0.7, tilt=10.0, mouth_glow=0.4)
r7 = IDLE.but(squash=0.06, jaw=0.4, tilt=4.0, eyes=1.2)
r8 = IDLE.but(squash=0.02, jaw=0.2, tilt=2.0)
add("Rise", [r0, r1, r2, r3, r4, r5, r6, r7, r8, IDLE.but(drip=1)])

# summon: the claw goes up, clenches, eyes blazing, and plunges into the tar: the bones answer (10)
u_top = IDLE.but(near=(-64.0, -118.0), grip=0.0, up=(1.0, -1.0), tilt=10.0, eyes=2.0, jaw=0.5, stretch=1.35)
u_cl1 = u_top.but(near=(-64.0, -121.0), grip=1.0, shake=1, jaw=0.7, mouth_glow=0.5)
u_cl2 = u_top.but(near=(-65.0, -119.0), grip=1.0, shake=0, jaw=0.7, mouth_glow=0.5)
u_down = IDLE.but(near=(-52.0, -52.0), grip=1.0, up=(-2.0, 0.0), tilt=-6.0, jaw=0.4, stretch=1.1)
u_in = IDLE.but(near=(-62.0, 8.0), grip=1.0, up=(-3.0, 2.0), tilt=-8.0, jaw=0.8, mouth_glow=0.6, eyes=1.8, plunge=1.0)
u_hold = u_in.but(up=(-2.0, 1.0), jaw=0.6, plunge=0.6, mouth_glow=0.3)
add("Summon", [IDLE.but(near=(-56.0, -36.0), up=(1.0, 0.0), eyes=1.2, grip=0.1, stretch=1.1),
               IDLE.but(near=(-62.0, -76.0), up=(1.0, -1.0), tilt=4.0, eyes=1.4, grip=0.0, stretch=1.25),
               IDLE.but(near=(-64.0, -106.0), up=(1.0, -1.0), tilt=8.0, eyes=1.7, jaw=0.3, grip=0.0, stretch=1.32), u_top, u_cl1, u_cl2, u_down, u_in,
               u_hold, IDLE.but(near=(-54.0, -8.0), up=(-1.0, 0.0), jaw=0.2, grip=0.4)])

# roar: it draws breath and bellows, shaking a pixel (6; the middle three loop while it holds)
o1 = IDLE.but(tilt=10.0, jaw=0.5, inflate=0.4, up=(2.0, -2.0), head=(1.0, -1.0), eyes=1.5)
o2 = IDLE.but(tilt=16.0, jaw=1.0, up=(2.0, -2.0), head=(2.0, -2.0), shake=1, eyes=2.0, mouth_glow=1.0, inflate=0.2)
add("Roar", [IDLE.but(tilt=6.0, jaw=0.25, inflate=0.3, up=(1.0, -1.0)), o1, o2, o2.but(tilt=17.0, shake=0), o2.but(jaw=0.95, shake=1, mouth_glow=0.9),
             IDLE.but(tilt=6.0, jaw=0.4, up=(1.0, -1.0), eyes=1.4)])

# death: recoil and a last roar; its bones work loose (the femur slides out of its back, the ridge leans); the tar lets go
# of them and runs back into the puddle; it settles, the skull rolls, the ember goes out, a last bubble (32)
d_roar = IDLE.but(tilt=16.0, jaw=0.9, up=(4.0, -3.0), head=(2.0, -2.0), eyes=1.8, mouth_glow=0.7)
death = [IDLE.but(tilt=12.0, jaw=0.6, up=(3.0, -2.0), eyes=1.6), d_roar, d_roar.but(shake=1, tilt=18.0, jaw=1.0), d_roar.but(shake=0, jaw=0.9, eyes=1.5)]
loose = d_roar.but(tilt=6.0, jaw=0.6, eyes=1.3, mouth_glow=0.3, up=(2.0, -2.0))
for k in range(4):                                                          # its bones work loose
    t = (k + 1) / 4.0
    death.append(loose.but(fall=0.25 * t, sag=0.2 * t, tilt=6.0 - 8.0 * t, up=(2.0 - k * 0.5, -2.0 + k * 0.5), eyes=1.3 - 0.1 * k,
                           mouth_glow=0.3 - 0.07 * k, drip=k))
SLUMP = IDLE.but(melt=1.0, sag=1.0, spread=0.92, bones=1.0, tilt=-4.0, jaw=0.8, eyes=0.1, near=(-62.0, 4.0), far=(54.0, 2.0), grip=0.0, far_grip=0.0,
                 fall=1.0)
start = death[-1].but(drip=0)
for k in range(16):                                                         # the slump, slowing as it spreads
    t = (k + 1) / 16.0
    e = 1.0 - (1.0 - t) ** 1.7
    death.append(tween(start, SLUMP, e).but(drip=k % 8, eyes=max(0.1, 1.0 - 0.9 * t), mouth_glow=max(0.0, 0.1 - 0.1 * t)))
for k in range(4):                                                          # it settles; the skull rolls a little
    death.append(SLUMP.but(tilt=-4.0 - 2.0 * (k + 1), eyes=0.1 - 0.02 * k, drip=k, ripple=0.25 * k))
death += [SLUMP.but(tilt=-12.0, bubble=0.45, eyes=0.03, drip=4), SLUMP.but(tilt=-12.0, bubble=1.0, eyes=0.02, drip=5),
          SLUMP.but(tilt=-12.0, bubble=0.0, eyes=0.0, drip=6, ripple=0.5), SLUMP.but(tilt=-12.0, eyes=0.0, bones=0.9, drip=7, ripple=1.0)]
add("Death", death)

INDEX = {name: k for k, (name, _) in enumerate(FRAMES)}
STRIPS = 6


def merged(cvs):
    out = Canvas()
    for cv in cvs:
        out.px.update(cv.px)
    return out


def solid(fr):
    """The frame's pixels that can touch a player: all three planes, without the puddle under it."""
    out = merged(fr[:3])
    for q in fr[4]["puddle"]:
        out.px.pop(q, None)
    return out


def hit_strips(cv, n, gap=6):
    """n vertical strips over the frame's opaque pixels above the ground clip, each split in two where its rows leave a
    gap of `gap` px or more (the air under the snout, between a raised claw and the mass): 2n boxes of the rows with
    >= 3 px, game px (x0, y0, x1, y1); an unused box is (0, 0, 0, 0)."""
    pts = [q for q in cv.px if q[1] < GROUND_CLIP]
    if not pts:
        return [(0, 0, 0, 0)] * (2 * n)
    x0 = min(q[0] for q in pts)
    x1 = max(q[0] for q in pts) + 1
    out = []
    for k in range(n):
        a = x0 + (x1 - x0) * k // n
        b = x0 + (x1 - x0) * (k + 1) // n
        col = [q for q in pts if a <= q[0] < b]
        rows = {}
        for (x, y) in col:
            rows[y] = rows.get(y, 0) + 1
        keep = [(x, y) for (x, y) in col if rows[y] >= 3]
        if not keep:
            out += [(0, 0, 0, 0), (0, 0, 0, 0)]
            continue
        ys = sorted({y for (_, y) in keep})
        split = None
        best = gap - 1
        for u, v in zip(ys, ys[1:]):
            if v - u - 1 > best:
                best, split = v - u - 1, v
        runs = [keep] if split is None else [[q for q in keep if q[1] < split], [q for q in keep if q[1] >= split]]
        for run in runs:
            out.append((min(q[0] for q in run) * 2, min(q[1] for q in run) * 2, (max(q[0] for q in run) + 1) * 2, (max(q[1] for q in run) + 1) * 2))
        if len(runs) == 1:
            out.append((0, 0, 0, 0))
    return out


# ================================================================================================
# Attack sprites
# ================================================================================================
BUBBLE_CELL = 30
BUBBLE_RADII = (6.0, 7.0, 8.0, 9.0, 10.5, 12.0, 13.5)


def bubble_frame(k, w):
    """A condensed tar bubble (30x30 cell): size step k (it grows over its life), wobble w. A glossy skin: a dark core,
    a lighter rim where the film is seen edge-on, a wet crescent and a hard glint top-left, the far side's light low
    right; strands of tar run round it as it stretches thin."""
    cv = Canvas()
    r = BUBBLE_RADII[k]
    c = (15.0, 15.0)
    wob = (0.05 + 0.012 * k) * (1 if w else -1)
    rx, ry = r * (1.0 + wob), r * (1.0 - wob)
    pin = cv.part(Xf(), Ellipse(c[0], c[1], rx, ry), "tar", flat(1, bevel=False), rust=0.0)
    for q in near_edge(pin, 2 if r < 9 else 3):
        cv.put(q[0], q[1], T[2])
    crescent(cv, Xf(), c, rx, ry, pin, 0.86, (1.6, 1.9), 0.35)
    g = P(Xf(), (c[0] - r * 0.42, c[1] - r * 0.48))
    for (dx, dy) in ((0, 0), (1, 0), (0, 1)):
        if (g[0] + dx, g[1] + dy) in pin:
            cv.put(g[0] + dx, g[1] + dy, S[2] if (dx, dy) == (0, 0) else T[4])
    low = arc_points(c, rx, ry, 28.0, 62.0, 0.72, 3)               # the light coming through the far side, low right
    for a, b in zip(low, low[1:]):
        line(cv, Xf(), a, b, lambda n: T[3], pin)
    if k >= 4:                                                      # stretched thin: strands of tar run round it
        for a0 in (130.0, 310.0):
            arc = arc_points(c, rx, ry, a0, a0 + 36.0, 0.48 + 0.05 * (k - 4), 4)
            for a, b in zip(arc, arc[1:]):
                line(cv, Xf(), a, b, lambda n: T[0] if n % 2 else None, pin)
    despeckle(cv)
    return to_image(cv.px, 0, 0, BUBBLE_CELL, BUBBLE_CELL)


def glob_frame(k):
    """A spat glob of tar (14x14): a wobbling blob with a cold glint and a trailing strand."""
    cv = Canvas()
    sq = (0.0, 0.8, -0.6)[k]
    cv.part(Xf(), Ellipse(7.0, 7.0, 4.6 + sq, 4.6 - sq), "tar", dome(5.5, 5.5, 5.0, lo=1, hi=2, gain=1.3, fixed=True), rust=0.0)
    cv.put(5, 5, T[3])
    cv.put(6, 4, T[4])
    for (x, y) in ((11, 8 + k % 2), (12, 9)):
        cv.put(x, y, T[1])
    return to_image(cv.px, 0, 0, 14, 14)


PUDDLE_W, PUDDLE_H = 30, 8


def puddle_frame(k):
    """A splash of tar on the ground, 3 tiles wide (30x8, bottom row on the ground): flat, glossy, bubbling."""
    cv = Canvas()
    pin = cv.part(Xf(), Ellipse(15.0, 5.5, 14.5, 2.8), "tar", dome(10.0, 3.5, 14.0, lo=1, hi=2, gain=1.1, fixed=True), rust=0.0)
    line(cv, Xf(), (5, 4), (12, 4), lambda n: T[3], pin)
    for j, bx in enumerate((8, 21)):
        ph = (k + j * 2) % 4
        if ph < 2:
            r = 1.0 + ph * 0.8
            cv.part(Xf(), Ellipse(bx, 4.6 - r * 0.6, r, r), "tar", flat(2), rust=0.0)
            cv.put(bx - 1, int(4.0 - r), T[4])
        elif ph == 2:
            cv.put(bx - 2, 3, T[2])
            cv.put(bx + 2, 3, T[2])
    return to_image(cv.px, 0, 0, PUDDLE_W, PUDDLE_H)


SPIKE_W, SPIKE_H = 16, 44
SPIKE_SEQ = ("Warn", 3), ("Rise", 4), ("Hold", 2), ("Sink", 3)


def spike_frames():
    """A bone spike out of the ground (16x44 cells, the bottom row is the ground): Warn x3 (the tar patch the players
    see first, bubbling), Rise x4 (it bursts up, overshoots, settles), Hold x2 (tar running off it), Sink x3."""
    out = []

    def patch(cv, width):
        pin = cv.part(Xf(), Ellipse(8.0, 42.2, width, 2.6), "tar", dome(5.0, 41.0, width, lo=1, hi=2, fixed=True), rust=0.0)
        line(cv, Xf(), (8.0 - width * 0.7, 41.0), (8.0 - width * 0.1, 41.0), lambda n: T[3] if n % 3 else T[4], pin)
        return pin

    def bone(cv, f, drips):
        h = 40.0 * f
        base = 43.0
        blade = Poly([(4.4, base + 4.0), (11.6, base + 4.0), (10.6, base - h * 0.45), (8.8, base - h * 0.8), (7.6, base - h),
                      (6.6, base - h * 0.86), (5.0, base - h * 0.5)])
        clip = {(x, y) for x in range(SPIKE_W) for y in range(SPIKE_H - 1)}
        inner = cv.part(Xf(), blade, "bone", cyl((8.0, base), (8.0, base - h), 3.6, lo=1, hi=4, gain=1.5, bias=0.25, fixed=True), rust=0.0, clip=clip)
        for (x0, y0, x1, y1) in ((10.6, base - h * 0.3, 8.6, base - h * 0.36), (5.0, base - h * 0.62, 6.8, base - h * 0.66)):
            line(cv, Xf(), (x0, y0), (x1, y1), lambda n: BN[1], inner)                          # notches: it is a broken rib
        line(cv, Xf(), (6.4, base - 3.0), (7.4, base - h * 0.8), lambda n: BN[4] if n % 4 == 1 else None, inner)
        if drips:
            for (x, y, ln) in drips:
                if f > 0.4:
                    drip(cv, x, base - h * y, ln)
        cv.part(Xf(), Ellipse(8.0, 42.5, 6.5, 2.4), "tar", dome(5.0, 41.0, 6.0, lo=1, hi=2, fixed=True), rust=0.0)

    for k in range(3):
        cv = Canvas()
        patch(cv, 6.0 + k * 0.7)
        for j in range(3):                                          # it boils: bubbles rise and pop
            bx = 3 + j * 4 + (k + j) % 2
            if (k + j) % 3 != 2:
                cv.put(bx, 40, T[4] if (k + j) % 3 == 0 else T[3])
                cv.put(bx + 1, 40, T[0])
                cv.put(bx, 39, T[0])
        if k == 2:                                                  # the tip of the bone breaks the surface
            for (x, y, c) in ((7, 39, BN[4]), (8, 39, BN[3]), (7, 38, BN[0]), (8, 38, BN[0])):
                cv.put(x, y, c)
        out.append(cv)
    for f in (0.32, 0.78, 1.12, 1.0):
        cv = Canvas()
        bone(cv, f, None)
        out.append(cv)
    for j in range(2):
        cv = Canvas()
        bone(cv, 1.0, [(9.6, 0.55 - 0.1 * j, 2 + j), (6.2, 0.3 + 0.05 * j, 1 + j)])
        out.append(cv)
    for f in (0.62, 0.3, 0.06):
        cv = Canvas()
        bone(cv, f, None)
        out.append(cv)
    return [to_image(cv.px, 0, 0, SPIKE_W, SPIKE_H) for cv in out]


CLAW_W, CLAW_H = 72, 96
CLAW_SEQ = ("Warn", 4), ("Rise", 4), ("Grab", 3), ("Sink", 4)
CLAW_ROWS = 8                                                # two columns: one column of 15 frames would be 2910 px tall (D0: 2048 max)
# The Tyrant armor's set bonus (2026-10-29): the same claw at 0.62 of the size, a short boil instead of the long warning
TYRANT_CLAW_SCALE = 0.62
TYRANT_CLAW_W, TYRANT_CLAW_H = 46, 62
TYRANT_CLAW_SEQ = ("Warn", 2), ("Rise", 4), ("Grab", 3), ("Sink", 4)


def columns(frames, rows, pad=1):
    """Equal frames in columns of `rows` (frame k at column k // rows, row k % rows), `pad` px (1x) after each."""
    w, h = frames[0].size
    cols = (len(frames) + rows - 1) // rows
    out = Image.new("RGBA", ((w + pad) * cols, (h + pad) * min(rows, len(frames))), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        out.alpha_composite(im, ((k // rows) * (w + pad), (k % rows) * (h + pad)))
    return out


def claw_frames(s=1.0, cw=CLAW_W, ch=CLAW_H, seq=CLAW_SEQ):
    """The enrage attack's claw (72x96 cells at s = 1, the bottom row on the ground; 8 tiles wide in game): Warn (a patch
    of tar spreading and boiling where it will come up), Rise x4 (a tar arm bursts up, the bone claw open), Grab x3 (the
    talons snap shut), Sink x4 (it pulls back under). `s` scales the whole drawing (the Tyrant armor's claw)."""
    out = []
    G = ch - 1.0
    cx = cw / 2.0
    warn = dict(seq)["Warn"]

    def patch(cv, width, boil):
        pin = cv.part(Xf(), Ellipse(cx, G - 0.5, width, max(2.0, 2.6 * s)), "tar", dome(cx - 10.0 * s, G - 2.0, width, lo=1, hi=2, fixed=True), rust=0.0)
        line(cv, Xf(), (cx - width * 0.7, G - 2.0), (cx - width * 0.2, G - 2.0), lambda n: T[3], pin)
        for j in range(5):
            if (j + boil) % 3 == 0:
                x = int(cx - width * 0.8 + j * width * 0.4)
                cv.put(x, int(G - 3), T[3])
                cv.put(x + 1, int(G - 3), T[0])
                cv.put(x, int(G - 4), T[0])
        return pin

    def arm(cv, f, grip):
        h = 82.0 * s * f
        wrist = (cx, G - h + 24.0 * s)
        mid_y = (G + wrist[1]) * 0.5
        lumps = [Capsule((cx, G + 2.0), (cx - 1.0 * s, mid_y), 12.0 * s, 9.0 * s), Capsule((cx - 1.0 * s, mid_y), (cx, wrist[1] + 4.0 * s), 9.0 * s, 7.5 * s),
                 Ellipse(cx, G - 1.0, 17.0 * s, 5.0 * s)]
        for (dx, fy, rx, ry) in ((-7.0, 0.22, 7.0, 8.0), (7.0, 0.5, 6.5, 8.0), (-5.0, 0.78, 5.5, 6.5)):
            y = G - (G - wrist[1]) * fy
            if y < G - 4.0 * s:
                lumps.append(Ellipse(cx - 0.5 * s + dx * s, y, rx * s, ry * s))     # it bulges as it boils up
        col = cv.part(Xf(), Union(*lumps), "tar", dome(cx - 8.0 * s, wrist[1] + 8.0 * s, 40.0 * s, lo=1, hi=2, gain=1.3, bias=-0.2), rust=0.0)
        for (dx, fy, rx, ry) in ((-7.0, 0.22, 7.0, 8.0), (-5.0, 0.78, 5.5, 6.5)):
            y = G - (G - wrist[1]) * fy
            if y < G - 4.0 * s:
                crescent(cv, Xf(), (cx - 0.5 * s + dx * s, y), rx * s, ry * s, near_edge(col, 3), 0.95, (1.4, 1.6), 0.4)
        hx = Xf.pose(-90.0, (0.0, 0.0), wrist)
        k2 = 2.0 * s
        cv.part(hx, Ellipse(5.0 * k2, 0.0, 6.0 * k2, 4.2 * k2), "tar", dome(3.0 * k2, -2.0 * k2, 6.0 * k2, lo=1, hi=2), rust=0.0)
        for d in (-1.5, -0.5, 0.5, 1.5):
            root = (0.0, d * 1.1 * k2)
            base = (7.0 * k2, d * 3.0 * k2)
            a = math.radians(d * 24.0 * (1.0 - 0.7 * grip))
            curl = math.radians(6.0 + grip * 70.0) * (1 if d > 0 else -1)
            p1 = (base[0] + math.cos(a + curl * 0.5) * 6.0 * k2, base[1] + math.sin(a + curl * 0.5) * 6.0 * k2)
            p2 = (p1[0] + math.cos(a + curl * 1.1) * 5.0 * k2, p1[1] + math.sin(a + curl * 1.1) * 5.0 * k2)
            p3 = (p2[0] + math.cos(a + curl * 1.8) * 8.0 * k2, p2[1] + math.sin(a + curl * 1.8) * 8.0 * k2)
            long_bone(cv, hx, root, base, 1.5 * k2, 1.7 * k2)                    # the metacarpals fan out of the tar
            knob(cv, hx, base, 1.9 * k2, 1.8 * k2)
            long_bone(cv, hx, base, p1, 1.8 * k2, 1.6 * k2)
            long_bone(cv, hx, p1, p2, 1.6 * k2, 1.5 * k2)
            talon = cv.part(hx, Capsule(p2, p3, 1.9 * k2, 0.4 * k2), "bone", cyl(p2, p3, 1.9 * k2, lo=1, hi=3, gain=1.4), shadow=(1, 1), rust=0.0)
            q = P(hx, lerp2(p2, p3, 0.35))
            if q in talon:
                cv.put(q[0], q[1], BN[4])
            knob(cv, hx, p1, 1.6 * k2, 1.6 * k2)
        cuff = cv.part(Xf(), Ellipse(cx, wrist[1] + 3.0 * s, 9.5 * s, 5.0 * s), "tar", dome(cx - 4.0 * s, wrist[1], 9.0 * s, lo=1, hi=2), rust=0.0)
        crescent(cv, Xf(), (cx, wrist[1] + 3.0 * s), 9.5 * s, 5.0 * s, cuff, 0.9, (1.2, 1.4), 0.4)
        for k in range(3):
            drip(cv, cx - 9.0 * s + k * 9.0 * s, wrist[1] + 6.0 * s + (k % 2) * 5.0 * s, max(1, int(round((2 + k % 2) * s))))
        cv.part(Xf(), Ellipse(cx, G - 0.5, 20.0 * s, max(2.0, 3.0 * s)), "tar", dome(cx - 8.0 * s, G - 2.0, 18.0 * s, lo=1, hi=2, fixed=True), rust=0.0)

    clip = {(x, y) for x in range(cw) for y in range(ch - 1)}
    for k in range(warn):
        cv = Canvas()
        patch(cv, s * (18.0 + 16.5 * k / max(1, warn - 1)), k)
        out.append(cv)
    for f, g in ((0.25, 0.0), (0.62, 0.0), (1.04, 0.0), (1.0, 0.1)):
        cv = Canvas()
        patch(cv, 32.0 * s, 0)
        arm(cv, f, g)
        out.append(cv)
    for g in (0.45, 0.85, 1.0):
        cv = Canvas()
        patch(cv, 32.0 * s, 1)
        arm(cv, 0.98, g)
        out.append(cv)
    for f in (0.7, 0.42, 0.18, 0.0):
        cv = Canvas()
        patch(cv, (32.0 - (0.7 - f) * 20.0) * s, 2)
        if f > 0.0:
            arm(cv, f, 1.0)
        out.append(cv)
    for cv in out:
        despeckle(cv)
    return [to_image({q: c for q, c in cv.px.items() if q in clip}, 0, 0, cw, ch) for cv in out]


WARN_W, WARN_H = 10, 16


def warn_frames():
    """The "!" over a claw's target (10x16, 4 frames): an ember sign that pulses (hostile colours, D3)."""
    out = []
    for k in range(4):
        cv = Canvas()
        hot = k in (1, 2)
        bar = cv.part(Xf(), Poly([(2.6, 0.6), (7.4, 0.6), (6.4, 10.0), (3.6, 10.0)]), "ember", flat(3 if hot else 2, bevel=True, hi=3), rust=0.0)
        cv.part(Xf(), Ellipse(5.0, 13.2, 2.2, 2.2), "ember", flat(3 if hot else 2, bevel=True, hi=3), rust=0.0)
        for (x, y) in ((4, 2), (4, 3)):
            if (x, y) in bar:
                cv.put(x, y, S[3] if hot else E[3])
        out.append(to_image(cv.px, 0, 0, WARN_W, WARN_H))
    return out


# --- the bones it flings out of its back (user, 2026-10-29: "bones should automatically fly out of his upper back") ------
BONE_CELL = 16
BONE_TURNS = 8
BONE_KINDS = 2


def back_bone(cv, xf, kind):
    """A loose bone in its own space, centred on (0, 0): a broken rib (a shaft with a joint knob and a snapped end) or a
    vertebra (the round centrum, its spine and two processes), a lick of tar still on it. Lit in 45-degree steps."""
    if kind == 0:
        shaft = long_bone(cv, xf, (-4.0, 0.4), (4.0, -0.4), 2.2, 1.9, snap=LIMB_SNAP)
        knob(cv, xf, (-5.0, 0.6), 2.9, 2.7, snap=LIMB_SNAP)
        cv.part(xf, Poly([(3.0, -2.4), (6.6, -1.8), (5.2, -0.4), (6.8, 0.8), (3.4, 1.8)]), "bone",
                cyl((3.0, 0.0), (6.8, 0.0), 2.2, lo=1, hi=4, gain=1.4, snap=LIMB_SNAP), rust=0.0)
        line(cv, xf, (-2.0, -0.9), (2.4, -1.2), lambda n: BN[4] if n % 3 != 2 else None, shaft)    # the sheen on its top
        for (x, y) in ((0.6, 1.0), (1.4, 1.2)):                             # a lick of tar under the shaft
            q = P(xf, (x, y))
            if q in shaft:
                cv.put(q[0], q[1], T[1])
    else:
        cv.part(xf, Poly([(-1.6, -1.2), (1.6, -1.2), (1.0, -6.4), (-0.4, -7.0), (-1.4, -4.4)]), "bone",
                cyl((0.0, -1.2), (0.0, -6.8), 2.0, lo=1, hi=4, gain=1.5, snap=LIMB_SNAP), rust=0.0)
        long_bone(cv, xf, (-5.6, 0.4), (5.6, 0.4), 1.5, 1.5, snap=LIMB_SNAP)
        body = knob(cv, xf, (0.0, 1.4), 3.6, 3.1, snap=LIMB_SNAP)
        for q in cv.raster(xf, Ellipse(0.3, 1.8, 1.1, 1.0)) & body:
            cv.put(q[0], q[1], T[1])                                        # the spinal canal, full of tar


def back_bone_frames():
    """Each kind in eight turns of 45 degrees (16x16 cells), the light kept on its top-left in every one (D4: never
    rotated at runtime)."""
    out = []
    for kind in range(BONE_KINDS):
        for k in range(BONE_TURNS):
            cv = Canvas()
            back_bone(cv, Xf.pose(k * 45.0, (0.0, 0.0), (8.0, 8.0)), kind)
            despeckle(cv)
            out.append(to_image(cv.px, 0, 0, BONE_CELL, BONE_CELL))
    return out


# --- the vent the bones burst out of: drawn over the boss at its "vent" point (an overlay: the volley keeps its own time) --
VENT_W, VENT_H = 30, 30
VENT_OX, VENT_OY = 15, 24                                    # the vent point (the mound's surface) in the cell
VENT_SEQ = ("Swell", 4), ("Burst", 3)


def vent_frames():
    """Swell x4 (the telegraph: the tar on its back heaves up into a boiling dome and the ends of bones break its skin)
    and Burst x3 (the dome bursts: a crown of tar thrown up, then falling back as the skin closes). The dome's foot is
    not outlined, so it reads as the mound itself rising."""
    out = []
    cx, base = float(VENT_OX), float(VENT_OY)
    under = {(x, y) for x in range(VENT_W) for y in range(VENT_OY + 1, VENT_H)}     # the mound below: no outline against it
    for k in range(4):
        cv = Canvas()
        r = 3.6 + 1.2 * k
        h = 2.5 + 1.6 * k
        shape = Union(Ellipse(cx, base - h * 0.45, r, h), Ellipse(cx, base + 1.5, r + 2.5, 2.5))
        pin = cv.part(Xf(), shape, "tar", dome(cx - r * 0.45, base - h, r + 3.0, lo=1, hi=2, gain=1.35, bias=-0.15, fixed=True), rust=0.0,
                      merge=under, clip={(x, y) for x in range(VENT_W) for y in range(VENT_OY + 2)})
        crescent(cv, Xf(), (cx, base - h * 0.45), r, h, pin, 0.92, (1.2, 1.4), 0.45)
        for j in range(1 + k // 2):                                   # it boils
            bx = cx - r * 0.5 + j * r * 0.9 + (k % 2)
            by = base - h * 0.4 - (k + j) % 2
            for (dx, dy, col) in ((0, 0, T[3]), (1, 0, T[0]), (0, 1, T[0])):
                if (int(bx) + dx, int(by) + dy) in pin:
                    cv.put(int(bx) + dx, int(by) + dy, col)
        if k >= 2:                                                    # the ends of bones break the skin
            for j, a in enumerate((-38.0, 4.0, 40.0)[:k]):
                d = math.radians(a - 90.0)
                tip = (cx + math.cos(d) * (r * 0.62), base - h * 0.45 + math.sin(d) * (h * 0.8))
                end = Xf.pose(a, (0.0, 0.0), tip)
                poke = 1.0 + 1.2 * (k - 2)
                long_bone(cv, end, (0.0, 1.0), (0.0, -poke), 1.6, 1.6, shadow=None)
                knob(cv, end, (0.0, -poke - 0.8), 2.3, 2.1)
        out.append(cv)
    for k in range(3):
        cv = Canvas()
        r = 6.0 + 1.0 * k
        h = (5.0, 3.0, 1.8)[k]
        shape = Union(Ellipse(cx, base - h * 0.45, r, h), Ellipse(cx, base + 1.5, r + 2.5, 2.5))
        pin = cv.part(Xf(), shape, "tar", dome(cx - r * 0.45, base - h, r + 3.0, lo=1, hi=2, gain=1.35, bias=-0.15, fixed=True), rust=0.0,
                      merge=under, clip={(x, y) for x in range(VENT_W) for y in range(VENT_OY + 2)})
        for q in cv.raster(Xf(), Ellipse(cx, base - h * 0.5, r * 0.45, max(1.0, h * 0.35))) & pin:
            cv.put(q[0], q[1], T[1] if k < 2 else T[2])               # the hole the bones tore, closing
        for j in range(6):                                            # the crown of tar thrown up
            a = math.radians(-90.0 + (j - 2.5) * 26.0)
            reach = (6.0, 11.0, 14.0)[k] * (0.8 + 0.25 * (j % 2))
            foot = (cx + math.cos(a) * r * 0.6, base - h * 0.6)
            tip = (foot[0] + math.cos(a) * reach * 0.6, foot[1] + math.sin(a) * reach)
            if k == 0:
                strand = cv.part(Xf(), Capsule(foot, tip, 1.8, 1.2), "tar", flat(2, bevel=False), rust=0.0)
                q = P(Xf(), lerp2(foot, tip, 0.7))
                if q in strand:
                    cv.put(q[0], q[1], T[3])
            else:                                                     # the strands snap into drops, then the drops fall
                drop = (tip[0], tip[1] + (0.0, 4.0)[k - 1] + 1.5 * (j % 3))
                blob = cv.part(Xf(), Ellipse(drop[0], drop[1], 1.9, 2.1), "tar", flat(2, bevel=False), rust=0.0)
                q = P(Xf(), (drop[0] - 0.5, drop[1] - 0.7))
                if q in blob:
                    cv.put(q[0], q[1], T[3])
        out.append(cv)
    for cv in out:
        despeckle(cv)
    return [to_image(cv.px, 0, 0, VENT_W, VENT_H) for cv in out]


# ================================================================================================
# Gores, icons, items
# ================================================================================================
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gore_images():
    out = {}
    cv = Canvas()
    hxf = Xf.pose(0.0, (0.0, 0.0), (60.0, 40.0))
    skull = cv.part(hxf, Poly(SKULL), "bone", dome(-22.0, -30.0, 34.0, lo=1, hi=4, gain=1.3, bias=0.1, bevel=True), rust=0.0)
    for x in UPPER_TEETH:
        tooth(cv, hxf, x, -6.0, 3.0, down=True)
    for hole in (ANTORBITAL, TEMPORAL, NOSTRIL, MAXILLARY, ORBIT):
        for q in cv.raster(hxf, hole) & skull:
            cv.put(q[0], q[1], T[1])
    out["TarTyrant_GoreSkull"] = crop(cv.px)
    cv = Canvas()
    jxf = Xf.pose(0.0, (0.0, 0.0), (60.0, 40.0))
    jaw = cv.part(jxf, Poly(JAW), "bone", dome(-24.0, -8.0, 30.0, lo=1, hi=4, gain=1.25, bias=0.05, bevel=True), rust=0.0)
    for x in LOWER_TEETH:
        tooth(cv, jxf, x, -6.5, 2.6, down=False)
    for q in cv.raster(jxf, JAW_HOLE) & jaw:
        cv.put(q[0], q[1], T[1])
    out["TarTyrant_GoreJaw"] = crop(cv.px)
    cv = Canvas()
    rib(cv, Xf.pose(0.0, (0.0, 0.0), (20.0, 4.0)), 30.0, 7.0, 2.6)
    out["TarTyrant_GoreRib"] = crop(cv.px)
    cv = Canvas()
    femur(cv, Xf.pose(-90.0, (0.0, 0.0), (10.0, 20.0)))
    out["TarTyrant_GoreFemur"] = crop(cv.px)
    cv = Canvas()
    spine(cv, Xf.pose(0.0, (0.0, 0.0), (10.0, 24.0)), 14.0)
    knob(cv, Xf(), (10.0, 25.0), 4.0, 3.0)
    out["TarTyrant_GoreVertebra"] = crop(cv.px)
    cv = Canvas()
    claw(cv, Xf.pose(-60.0, (0.0, 0.0), (10.0, 30.0)), 0.5)
    out["TarTyrant_GoreClaw"] = crop(cv.px)
    return out


HEAD_ICON = (
    "................",
    "................",
    "........ooooo...",
    "......oohhhmmo..",
    "....oohhmmmmmmo.",
    "..oohmmmmmmmrrmo",
    ".ohmkmmkkkmmreko",
    "ohmmmmmkkmmmmmto",
    "ommmmmmmmmmmmtto",
    ".owdwdwdwdwdmtto",
    "..odddddddddtto.",
    "...ommmmmmmmdo..",
    "....oddddddddo..",
    ".....oooooooo...",
    "................",
    "................",
)
HEAD_COLOURS = {"o": BN[0], "h": BN[4], "m": BN[3], "d": BN[2], "w": BN[3], "k": T[0], "e": E[3], "r": E[2], "t": T[2]}


def head_icon():
    """Map head (16x16 -> 32x32): the skull in profile, its ember eye, a tooth row and tar over the back of it."""
    cv = Canvas()
    for y, row in enumerate(HEAD_ICON):
        for x, ch in enumerate(row):
            if ch in HEAD_COLOURS:
                cv.put(x, y, HEAD_COLOURS[ch])
    return to_image(cv.px, 0, 0, 16, 16)


def treasure_bag():
    """Treasure bag (18x18 -> 36x36): a round sack soaked in tar up to its middle, its neck tied with a little bone."""
    cv = Canvas()
    X = Xf()
    sack = cv.part(X, Union(Ellipse(9.0, 11.6, 7.4, 5.6), Poly([(5.6, 6.0), (12.4, 6.0), (14.0, 9.0), (4.0, 9.0)])), "leather",
                   dome(6.0, 8.0, 10.0, lo=1, hi=2, gain=1.3, bias=0.15), shadow=(1, 1), rust=0.0)
    tar = cv.part(X, Ellipse(9.0, 14.6, 7.6, 3.6), "tar", dome(6.0, 13.0, 8.0, lo=1, hi=2), rust=0.0, clip=sack | cv.raster(X, Ellipse(9.0, 14.6, 7.6, 3.6)))
    gloss_line(cv, (3.4, 13.2), (7.6, 12.0), tar, 3)
    cv.part(X, Poly([(6.4, 1.6), (11.6, 1.6), (12.4, 6.0), (5.6, 6.0)]), "leather", flat(2), rust=0.0)
    long_bone(cv, X, (4.4, 6.0), (13.6, 5.4), 1.0, 1.0, shadow=None)
    knob(cv, X, (4.0, 6.0), 1.6, 1.5)
    knob(cv, X, (14.0, 5.4), 1.6, 1.5)
    drip(cv, 7, 17, 0)
    return to_image(cv.px, 0, 0, 18, 18)


def serene_tear():
    """The Serene Tear / Gota Serena (12x16 -> 24x32): a teardrop of aether glass hanging from a brass cap, a curl of
    steam asleep inside it."""
    cv = Canvas()
    X = Xf()
    drop = Union(Ellipse(6.0, 10.6, 4.6, 4.6), Poly([(1.6, 9.6), (10.4, 9.6), (6.6, 3.4), (5.4, 3.4)]))
    glass = cv.part(X, drop, "aether", dome(4.2, 8.6, 6.0, lo=1, hi=3, gain=1.3, bias=0.1), shadow=None, rust=0.0)
    for (x, y) in ((5, 9), (6, 10), (7, 11), (6, 12), (5, 12), (4, 11)):            # the sleeping curl of steam
        if (x, y) in glass:
            cv.put(x, y, S[1] if (x + y) % 2 else S[2])
    for (x, y) in ((3, 9), (3, 10), (4, 8)):
        if (x, y) in glass:
            cv.put(x, y, S[3])
    cv.part(X, Poly([(4.4, 2.0), (7.6, 2.0), (7.4, 4.2), (4.6, 4.2)]), "brass", flat(3, bevel=True), rust=0.0)
    cv.part(X, Ellipse(6.0, 1.0, 1.6, 1.2) - Ellipse(6.0, 1.0, 0.6, 0.4), "brass", flat(4, bevel=False), rust=0.0)
    return to_image(cv.px, 0, 0, 12, 16)


# --- Scrapworm (unchanged from 2026-10-28) -------------------------------------------------------------------------------
def worm_frame(k):
    """The Scrapworm (16x8 per frame, facing left, 2 frames like vanilla's worm): a segmented worm of rusted scrap rings
    on a tar-black body, a little brass drill-bit head, a wire tail; frame 1 inches forward (the segments bunch up)."""
    cv = Canvas()
    bunch = k == 1
    segs = 5
    for j in range(segs):
        x = 4.0 + j * (2.2 if bunch else 2.6)
        y = 5.0 - (1.0 if bunch and j in (2, 3) else 0.0)
        ramp_name = "copper" if j % 2 == 0 else "iron"
        cv.part(Xf(), Ellipse(x, y, 1.9, 1.8), ramp_name, dome(x - 0.6, y - 0.6, 2.0, lo=1, hi=3), rust=0.0)
    hx = 2.4
    cv.part(Xf(), Poly([(hx + 1.5, 3.4), (hx - 2.2, 5.0), (hx + 1.5, 6.6)]), "brass", flat(3), rust=0.0)
    cv.put(int(hx + 1), 4, E[3])
    tail = int(4.0 + segs * (2.2 if bunch else 2.6))
    cv.put(tail, 5, I[2])
    cv.put(tail + 1, 4 if bunch else 5, I[3])
    return to_image(cv.px, 0, 0, 16, 8)


def worm_item():
    """The bait item (16x16 -> 32x32): the worm coiled into a loop, drill head up."""
    cv = Canvas()
    for j in range(8):
        a = math.radians(200 + j * 40)
        x, y = 8.0 + math.cos(a) * 4.2, 9.0 + math.sin(a) * 4.2
        ramp_name = "copper" if j % 2 == 0 else "iron"
        cv.part(Xf(), Ellipse(x, y, 1.9, 1.9), ramp_name, dome(x - 0.6, y - 0.6, 2.1, lo=1, hi=3), rust=0.0)
    cv.part(Xf(), Poly([(3.0, 4.0), (5.5, 1.0), (6.5, 5.0)]), "brass", flat(3), rust=0.0)
    cv.put(5, 4, E[3])
    return to_image(cv.px, 0, 0, 16, 16)


# ================================================================================================
# Export
# ================================================================================================
LAYER_FILES = {"Body": "TarTyrant", "Glow": "TarTyrant_Glow", "Near": "TarTyrant_Near", "Far": "TarTyrant_Far"}
STALE = ("Projectiles/TarTyrantSaw.png", "Projectiles/TarTyrantWave.png", "Projectiles/TarTyrantGeyser.png", "Projectiles/TarTyrantBoneSlam.png",
         "Projectiles/TarTyrantBoneBoomerang.png", "Gores/TarTyrant_GoreCrown.png", "Gores/TarTyrant_GoreGrate.png", "Gores/TarTyrant_GoreGauntlet.png",
         "Gores/TarTyrant_GoreValve.png", "Gores/TarTyrant_GoreHorn.png")


def render_all():
    return [frame(p) for _, p in FRAMES]


def runs(prefix, seq):
    run, parts = 0, []
    for name, n in seq:
        parts.append("%s%s0 = %d, %s%sFrames = %d" % (prefix, name, run, prefix, name, n))
        run += n
    return run, ", ".join(parts)


def write_rig_data(path, layers, frames):
    L = ["// <auto-generated> by art/bosses/tartyrant/make_tartyrant_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Bosses.TarTyrant",
         "{",
         "\t/// <summary>Tar Tyrant's sprite layout, generated with the sprites (game px, 2x art, left-facing; mirror X when",
         "\t/// facing right). Packed atlases like Trash-Tr0m's: FrameFields values per frame (page, x, y, w, h, origin x, origin y),",
         "\t/// origin = the ground point under the mass. Points are relative to that origin. Each sequence is Name0 .. Name0 +",
         "\t/// NameFrames - 1.</summary>",
         "\tpublic static class TarTyrantRigData",
         "\t{",
         "\t\tpublic const int FrameFields = 7;",
         "\t\tpublic const int BodyPages = %d, GlowPages = %d, NearPages = %d, FarPages = %d;" % tuple(layers[k][0] for k in ("Body", "Glow", "Near", "Far")),
         "\t\tpublic const int FrameCount = %d;" % len(FRAMES)]
    for name, (first, count) in SEQS.items():
        L.append("\t\tpublic const int %s0 = %d, %sFrames = %d;" % (name, first, name, count))
    for key in ("Body", "Glow", "Near", "Far"):
        L.append("\t\t/// <summary>%s layer: page, x, y, w, h, origin x, origin y per frame.</summary>" % key)
        L.append(cs_array(key + "Frames", layers[key][1], typ="short", per_line=14).rstrip("\n"))
    L.append("\t\t/// <summary>Contact boxes per frame: %d columns, each split in two around a gap.</summary>" % STRIPS)
    L.append("\t\tpublic const int Strips = %d;" % (STRIPS * 2))
    vals = []
    for fr in frames:
        for r in hit_strips(solid(fr), STRIPS):
            vals += list(r)
    L.append("\t\t/// <summary>Contact boxes per frame (Strips boxes of x0, y0, x1, y1 over all three planes, the puddle left out).</summary>")
    L.append(cs_array("Hit", vals, typ="short", per_line=16).rstrip("\n"))
    for key, doc in (("mouth", "the mouth (between the jaws)"), ("eye", "the orbit's ember"), ("hand", "the near claw's palm"),
                     ("core", "the middle of the mass"), ("top", "the top of the mound"),
                     ("vent", "the top of the hump between two spines, where the bones fly out (TarTyrant_Vent's origin)")):
        vals = []
        for fr in frames:
            vals += [int(round(fr[4][key][0] * 2)), int(round(fr[4][key][1] * 2))]
        L.append("\t\t/// <summary>%s%s per frame (x, y pairs).</summary>" % (doc[0].upper(), doc[1:]))
        L.append(cs_array(key.capitalize(), vals, typ="short").rstrip("\n"))
    idle = solid(frames[INDEX["Idle0"]])
    xs = [q[0] for q in idle.px if q[1] < GROUND_CLIP]
    ys = [q[1] for q in idle.px if q[1] < GROUND_CLIP]
    L.append("\t\t/// <summary>The idle frame's box (all planes), the NPC rectangle at full size.</summary>")
    L.append("\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d;" % (min(xs) * 2, (max(xs) + 1) * 2, min(ys) * 2))
    allx = [q[0] for fr in frames for cv in fr[:3] for q in cv.px if q[1] < GROUND_CLIP]
    ally = [q[1] for fr in frames for cv in fr[:3] for q in cv.px if q[1] < GROUND_CLIP]
    L.append("\t\t/// <summary>The union of every frame (the bestiary box) and the tallest frame above the ground line.</summary>")
    L.append("\t\tpublic const int BoundsWidth = %d, BoundsHeight = %d, MaxHeight = %d;" % ((max(allx) - min(allx) + 1) * 2,
                                                                                             (max(ally) - min(ally) + 1) * 2, -min(ally) * 2))
    L.append("\t\t// Attack sprites (game px): cells and frame runs of their sheets (2 px between cells).")
    L.append("\t\tpublic const int BubbleCell = %d, BubbleSizes = %d;" % (BUBBLE_CELL * 2, len(BUBBLE_RADII)))
    L.append(cs_array("BubbleRadius", [int(round(r * 2)) for r in BUBBLE_RADII], typ="short").rstrip("\n"))
    L.append("\t\tpublic const int GlobSize = 28, PuddleWidth = %d, PuddleHeight = %d;" % (PUDDLE_W * 2, PUDDLE_H * 2))
    n, parts = runs("Spike", SPIKE_SEQ)
    L.append("\t\tpublic const int SpikeWidth = %d, SpikeHeight = %d, SpikeFrameCount = %d;" % (SPIKE_W * 2, SPIKE_H * 2, n))
    L.append("\t\tpublic const int %s;" % parts)
    n, parts = runs("Claw", CLAW_SEQ)
    L.append("\t\tpublic const int ClawWidth = %d, ClawHeight = %d, ClawFrameCount = %d, ClawRows = %d;" % (CLAW_W * 2, CLAW_H * 2, n, CLAW_ROWS))
    L.append("\t\tpublic const int %s;" % parts)
    L.append("\t\tpublic const int WarnWidth = %d, WarnHeight = %d, WarnFrameCount = 4;" % (WARN_W * 2, WARN_H * 2))
    L.append("\t\t/// <summary>The bones it flings out of its back: BoneKinds kinds of BoneTurns turns each (kind k's turn t is frame k x BoneTurns + t).</summary>")
    L.append("\t\tpublic const int BoneCell = %d, BoneTurns = %d, BoneKinds = %d, BoneFrameCount = %d;" % (BONE_CELL * 2, BONE_TURNS, BONE_KINDS, BONE_TURNS * BONE_KINDS))
    n, parts = runs("Vent", VENT_SEQ)
    L.append("\t\t/// <summary>The vent overlay (TarTyrant_Vent.png): its origin sits on the Vent point.</summary>")
    L.append("\t\tpublic const int VentWidth = %d, VentHeight = %d, VentOriginX = %d, VentOriginY = %d, VentFrameCount = %d;" % (
        VENT_W * 2, VENT_H * 2, VENT_OX * 2, VENT_OY * 2, n))
    L.append("\t\tpublic const int %s;" % parts)
    n, parts = runs("TyrantClaw", TYRANT_CLAW_SEQ)
    L.append("\t\t/// <summary>The Tyrant armor's set-bonus claw (Armor/TyrantClaw.png, one column, the bottom row on the ground).</summary>")
    L.append("\t\tpublic const int TyrantClawWidth = %d, TyrantClawHeight = %d, TyrantClawFrameCount = %d;" % (TYRANT_CLAW_W * 2, TYRANT_CLAW_H * 2, n))
    L.append("\t\tpublic const int %s;" % parts)
    L.append("\t\tpublic const int WormWidth = 32, WormHeight = 16;")
    L.append("\t}")
    L.append("}")
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = render_all()
    layers = {}
    for key, idx, glow in (("Body", 1, False), ("Glow", 3, True), ("Near", 2, False), ("Far", 0, False)):
        pages, table = pack_layer([fr[idx] for fr in frames], glow)
        for k, im in enumerate(pages):
            export(im, OUT + page_name(LAYER_FILES[key], k))
        for k in range(len(pages), 8):
            stale = os.path.join(ROOT, OUT + page_name(LAYER_FILES[key], k))
            if os.path.exists(stale):
                os.remove(stale)
        layers[key] = (len(pages), table)
    export(vertical([bubble_frame(k, w) for k in range(len(BUBBLE_RADII)) for w in (0, 1)]), OUT + "NPCs/TarTyrantBubble.png")
    export(vertical([glob_frame(k) for k in range(3)]), OUT + "Projectiles/TarTyrantGlob.png")
    export(vertical([puddle_frame(k) for k in range(4)]), OUT + "Projectiles/TarTyrantPuddle.png")
    export(vertical(spike_frames()), OUT + "Projectiles/TarTyrantBoneSpike.png")
    export(columns(claw_frames(), CLAW_ROWS), OUT + "Projectiles/TarTyrantClaw.png")
    export(vertical(warn_frames()), OUT + "Projectiles/TarTyrantClaw_Warning.png")
    export(vertical(back_bone_frames()), OUT + "Projectiles/TarTyrantBackBone.png")
    export(vertical(vent_frames()), OUT + "TarTyrant_Vent.png")
    export(vertical(claw_frames(TYRANT_CLAW_SCALE, TYRANT_CLAW_W, TYRANT_CLAW_H, TYRANT_CLAW_SEQ)), ARMOR_OUT + "TyrantClaw.png")
    for name, im in gore_images().items():
        export(im, OUT + "Gores/" + name + ".png")
    export(head_icon(), OUT + "TarTyrant_Head_Boss.png")
    export(treasure_bag(), OUT + "Items/TarTyrantBag.png")
    export(serene_tear(), OUT + "Items/SereneTear.png")
    export(vertical([worm_frame(k) for k in range(2)]), OUT + "Summon/ScrapwormCritter.png")
    export(worm_item(), OUT + "Summon/Scrapworm.png")
    for rel in STALE:
        stale = os.path.join(ROOT, OUT + rel)
        if os.path.exists(stale):
            os.remove(stale)
            print("removed", OUT + rel)
    write_rig_data(OUT + "TarTyrantRigData.cs", layers, frames)
    return frames


def preview(path, names=None, cols=8, bg=(36, 40, 48)):
    names = names or [n for n, _ in FRAMES]
    cw, ch = 250, 200
    out = Image.new("RGBA", (cw * min(cols, len(names)), ch * ((len(names) + cols - 1) // cols)), bg + (255,))
    for k, n in enumerate(names):
        far, mid, near, glow, _ = frame(dict(FRAMES)[n])
        tile = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cv in (far, mid, near):
            tile.alpha_composite(to_image({q: c for q, c in cv.px.items() if q[1] < GROUND_CLIP}, -cw // 2 - 10, -ch + 8, cw, ch))
        out.alpha_composite(tile, ((k % cols) * cw, (k // cols) * ch))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(path)
    print("preview", path, out.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames")
    ap.add_argument("--cols", type=int, default=8)
    a = ap.parse_args()
    if a.preview:
        preview(a.preview, a.frames.split(",") if a.frames else None, a.cols)
    else:
        export_all()
