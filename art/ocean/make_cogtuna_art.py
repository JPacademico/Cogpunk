"""Source for the Cogtuna (the Cogshark until the user renamed it, 2026-11-05), a Cogpunk enemy of the ocean, and its Shark Eye (D4), 2026-11-04. Run from the repo root:

    python -P art/ocean/make_cogtuna_art.py [--preview FILE]

Design (user, 2026-11-04: "a new enemy for the default ocean called Cogshark, like a steampunk shark, high armor and
damage, only in the water; it drops the Shark Eye"): a riveted iron shark with a brass belly. A deep-headed gunmetal
hull lit from the top-left in hard bands, a bright rolled ridge along its back, a brass collar behind three curved gill
vents, plate seams with rivets and a lit lip, a brass dorsal fin with a lit leading edge, a porthole eye with an ember
lens (hostile), a jaw of steam-white saw teeth with a furnace glowing in its throat when it gapes, iron pectoral and
pelvic fins with brass spars, an exhaust stack on its back (bubbles in game) and a tail of two riveted lobes turning on
a brass cog hub. Three-quarter side view facing left (D4 rule 13).

Three planes (DepthLayers.DrawWalker grid sheets): far (the far pectoral fin, a ramp step darker), middle (the hull,
dorsal fin, tail, jaw), near (the near pectoral fin); the glow sheet holds the eye's lens and the throat's furnace.
Stable pixels (D4 rule 17): every part is lit in its own space (painted on); the swim loop moves the hull by whole
pixels and turns only the tail and the fins (deliberate sweeps); the tilted frames turn the whole fish (Rise / Dive),
so nothing is rotated at runtime.

The rig's origin is the hull's centre; every frame is shifted so the lowest pixel of any frame sits on the grid sheets'
bottom row, and `CenterY` (game px) tells the C# how far above that row the hull's centre is (the NPC is drawn from its
centre: a fish has no feet).

Frames: Swim x6 (the tail sweeping, the fins sculling), Rise x2 / Dive x2 (nose up / down 18 degrees), Lunge x3 (the
telegraph's gape, the gaping dash, the bite), Beached x2 (out of water: arched, flopping).

Outputs:
    Content/Ocean/NPCs/Cogtuna.png, Cogtuna_Far.png, Cogtuna_Near.png, Cogtuna_Glow.png   grid sheets
    Content/Ocean/NPCs/CogtunaRigData.cs         cells, origin, centre, frames, the mouth and the exhaust (bubbles)
    Content/Ocean/Items/SharkEye.png              28x28 the accessory: a porthole eye with a fin
    Content/Ocean/Gores/Cogtuna_GoreHead.png, _GoreFin.png, _GoreTail.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, box, Canvas, flat, dome, face  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer, shifted  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Ocean/"
I, B, C, E, S = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam"))

# The hull's profile (1x, facing left, y down, origin at the hull's centre): (x, top, bottom). A deep head and a
# powerful shoulder tapering to the tail's peduncle.
PROFILE = [(-28.0, -1.0, 1.6), (-26.0, -3.2, 3.4), (-23.0, -5.2, 4.8), (-19.0, -6.6, 5.8), (-14.0, -7.6, 6.6), (-8.0, -8.2, 7.0),
           (-2.0, -8.0, 6.8), (4.0, -7.2, 6.0), (9.0, -5.8, 4.8), (13.0, -4.4, 3.6), (17.0, -3.0, 2.6), (20.0, -2.2, 1.8),
           (22.0, -1.9, 1.4)]
BELLY = 0.62                              # the brass belly starts this far down the hull's height
MOUTH_HINGE = (-15.0, 3.4)                # the lower jaw turns about this point
VENT_TOP = (10.5, -10.6)                  # the exhaust's mouth (bubbles)
MOUTH_POINT = (-25.0, 2.6)                # the bite's front (bubbles and splash)
TAIL_HUB = (21.0, -0.2)


def despeckle(cv):
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def profile_at(x):
    """(top, bottom) of the hull at a local x (linear between the profile's stations)."""
    if x <= PROFILE[0][0]:
        return PROFILE[0][1], PROFILE[0][2]
    for (x0, t0, b0), (x1, t1, b1) in zip(PROFILE, PROFILE[1:]):
        if x <= x1:
            u = (x - x0) / (x1 - x0)
            return t0 + (t1 - t0) * u, b0 + (b1 - b0) * u
    return PROFILE[-1][1], PROFILE[-1][2]


def body_shape():
    top = [(x, t) for (x, t, _) in PROFILE]
    bottom = [(x, b) for (x, _, b) in reversed(PROFILE)]
    return Poly(top + bottom)


def belly_shape():
    """The brass belly: from BELLY of the hull's height down, from under the jaw to the peduncle."""
    stations = [(x, t + (b - t) * BELLY) for (x, t, b) in PROFILE if -23.0 <= x <= 20.0]
    return Poly(stations + [(x, b + 1.0) for (x, _, b) in reversed(PROFILE) if -23.0 <= x <= 20.0])


def body_shade():
    """The hull's iron in hard bands across its height (a horizontal cylinder lit from the top-left, measured in the
    hull's own space: painted on, stable whatever the pose, D4 rule 17): the lit back, the upper flank, the flank in
    shadow; the tail end a step darker than the head."""
    def shade(i):
        t, b = profile_at(i.lx)
        u = (i.ly - t) / max(0.5, b - t)
        if u < 0.17:
            k = 4 if i.lx < 2.0 else 3
        elif u < 0.4:
            k = 3
        else:
            k = 2
        if i.lx > 14.0:
            k = max(1, k - 1)
        return k
    return shade


class Pose:
    def __init__(self, tilt=0.0, tail=0.0, jaw=0.0, bob=0, lean=0, fin=0, arch=0.0, gape=False):
        self.tilt = tilt                 # degrees, + = nose down (clockwise on screen)
        self.tail = tail                 # degrees the tail turns about its hub (+ = tail tip down)
        self.jaw = jaw                   # degrees the lower jaw drops
        self.bob, self.lean = bob, lean  # whole px: down, back (+x)
        self.fin = fin                   # 0 / 1: the pectoral fins scull down
        self.arch = arch                 # degrees the head and the tail lift (beached: arched)
        self.gape = gape                 # the throat's furnace shows (the jaw open)


def rivets_along(cv, xf, a, b, n, inner, ramp="iron"):
    r = RAMP[ramp]
    for k in range(n):
        u = (k + 0.5) / n
        q = P(xf, (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
        if q in inner and (q[0] + 1, q[1] + 1) in inner:
            cv.put(q[0], q[1], r[-1])
            cv.put(q[0] + 1, q[1] + 1, r[1])


def hull(mid, glow, xf, p):
    """The hull, belly plates, collar, seams, gills, eye, nose cap, dorsal fin and exhaust; returns its mask."""
    shape = body_shape()
    mask = mid.raster(xf, shape)
    inner = mid.part(xf, shape, "iron", body_shade(), rust=0.0)
    belly = belly_shape()
    bmask = mid.raster(xf, belly) & inner
    binner = mid.part(xf, belly, "brass", face((-0.2, 0.3, 0.9), lo=2, hi=3, gain=1.3, bias=0.1, fixed=True), clip=inner,
                      outline=False, rust=0.0)
    edge = mask - inner
    for q in edge:                                                 # the belly's own ramp-0 outline where it meets the water
        if any((q[0] + ox, q[1] + oy) in bmask for ox, oy in ((0, -1), (1, 0), (-1, 0))) and (q[0], q[1] - 1) not in edge:
            mid.put(q[0], q[1], B[0])
    for x in range(-22, 19):                                       # the seam: a dark brass groove, its lit lip under it
        t, b = profile_at(x + 0.5)
        q = P(xf, (x + 0.5, t + (b - t) * BELLY + 0.3))
        if q in bmask:
            mid.put(q[0], q[1], B[1])
            if (q[0], q[1] + 1) in bmask and x % 5 != 2:
                mid.put(q[0], q[1] + 1, B[4])
    rivets_along(mid, xf, (-18.0, 5.0), (14.0, 3.6), 6, binner, "brass")
    iron = inner - bmask
    # the plates' rolled top edge: a bright ridge along the back, broken at the plate joints
    for x in range(-24, 19):
        t, _ = profile_at(x + 0.5)
        q = P(xf, (x + 0.5, t + 1.2))
        if q in iron and x not in (-7, -6, -5, 5, 6, 14, 15):
            mid.put(q[0], q[1], I[4] if x < 6 else I[3])
    # the brass collar behind the gills, riveted
    t0, b0 = profile_at(-6.0)
    collar = Poly([(-7.0, t0 - 0.5), (-5.0, t0 - 0.5), (-5.0, b0 + 1.0), (-7.0, b0 + 1.0)])
    cmask = mid.raster(xf, collar) & mask
    for q in cmask:                                                # a band of brass: lit on top, its own outline on the edge
        lx, ly = xf.inv((q[0] + 0.5, q[1] + 0.5))
        t, b = profile_at(lx)
        u = (ly - t) / max(0.5, b - t)
        if q in edge:
            mid.put(q[0], q[1], B[0])
        else:
            mid.put(q[0], q[1], B[4] if u < 0.3 else (B[3] if u < 0.65 else B[2]))
    for q in cmask:                                                # the band's back edge: a dark groove on the iron
        r = (q[0] + 1, q[1])
        if r in inner and r not in cmask:
            mid.put(r[0], r[1], I[1])
    for y in (t0 + 2.2, (t0 + b0) / 2.0 + 0.4, b0 - 2.0):
        q = P(xf, (-6.4, y))
        if q in cmask and q not in edge:
            mid.put(q[0], q[1], B[5])
            mid.put(q[0], q[1] + 1, B[1])
    # plate seams further back: a dark groove, a lit lip behind it, rivets in front
    for x in (6.0, 15.0):
        t, b = profile_at(x)
        bl = t + (b - t) * BELLY
        for k in range(int((bl - t - 1.0) * 2)):
            ly = t + 1.0 + k * 0.5
            q = P(xf, (x + 0.4 * math.sin(k * 0.3), ly))
            if q in iron:
                mid.put(q[0], q[1], I[1])
                if (q[0] + 1, q[1]) in iron:
                    mid.put(q[0] + 1, q[1], I[4] if ly < t + (b - t) * 0.3 else I[3])
        rivets_along(mid, xf, (x - 2.2, t + 2.2), (x - 2.2, bl - 1.0), 2, iron)
    # gill vents: three curved slits behind the head, a lit lip behind each
    for gx in (-13.2, -11.0, -8.8):
        for j in range(6):
            ly = -2.6 + j * 1.05
            q = P(xf, (gx - 0.5 * math.sin(j / 5.0 * math.pi), ly))
            if q in iron:
                mid.put(q[0], q[1], I[0])
                if (q[0] + 1, q[1]) in iron:
                    mid.put(q[0] + 1, q[1], I[4] if ly < 0 else I[3])
    # the porthole eye: a brass ring and an ember lens (glow)
    e = P(xf, (-20.4, -2.8))
    for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (2, -1), (-1, 0), (2, 0), (-1, 1), (2, 1), (-1, 2), (0, 2), (1, 2), (2, 2)):
        q = (e[0] + dx, e[1] + dy)
        if q in mask:
            mid.put(q[0], q[1], B[5] if (dy < 0 and dx < 1) else (B[4] if dy < 1 and dx < 0 else B[2]))
    for (dx, dy, col) in ((0, 0, E[3]), (1, 0, E[2]), (0, 1, E[2]), (1, 1, E[1])):
        mid.put_glow(e[0] + dx, e[1] + dy, col)
        glow.put_glow(e[0] + dx, e[1] + dy, col)
    # the snout's nose cap: a darker riveted plate
    cap = Poly([(-28.6, -1.2), (-25.4, -3.6), (-24.0, -3.4), (-24.0, 1.4), (-27.8, 1.6)])
    capi = mid.part(xf, cap, "iron", face((-0.7, -0.5, 0.5), lo=2, hi=3, fixed=True), clip=mask, rust=0.0)
    rivets_along(mid, xf, (-25.4, -1.8), (-25.4, 0.0), 1, capi)
    # the dorsal fin: brass, swept back, rivets along its root, a lit leading edge, its shadow on the back
    dorsal = Poly([(-7.0, -7.6), (-3.6, -11.0), (-0.8, -14.6), (1.4, -16.4), (2.6, -16.0), (2.4, -13.6), (3.8, -10.2), (6.6, -7.0)])
    dinner = mid.part(xf, dorsal, "brass", face((-0.55, -0.45, 0.7), lo=2, hi=4, gain=1.3, fixed=True), rust=0.0)
    rivets_along(mid, xf, (-4.0, -8.8), (4.4, -8.6), 3, dinner, "brass")
    for k in range(6):
        q = P(xf, (-5.6 + k * 1.2, -9.4 - k * 1.25))
        if q in dinner:
            mid.put(q[0], q[1], B[5])
    for k in range(6):
        q = P(xf, (-4.0 + k * 2.0, -6.8))
        if q in iron:
            mid.darken(q[0], q[1])
    # the exhaust behind the fin: a brass stack, an iron cap
    mid.part(xf, box(9.0, -10.0, 12.0, -4.6), "brass", face((-0.6, -0.2, 0.75), lo=2, hi=4, fixed=True), rust=0.0)
    mid.part(xf, box(8.4, -11.0, 12.6, -9.6), "iron", face((-0.5, -0.6, 0.6), lo=2, hi=4, fixed=True), rust=0.0)
    # the pelvic fin under the belly: small, iron, a brass spar
    pelvic = Poly([(6.0, 5.4), (9.6, 4.6), (12.6, 7.8), (11.4, 8.4), (7.6, 7.0)])
    pinner = mid.part(xf, pelvic, "iron", face((-0.4, 0.2, 0.9), lo=2, hi=3, fixed=True), rust=0.0)
    for k in range(4):
        q = P(xf, (7.0 + k * 1.4, 5.6 + k * 0.7))
        if q in pinner:
            mid.put(q[0], q[1], B[3])
    return mask


def jaw(mid, glow, xf, p, mask):
    """The lower jaw (turned down by p.jaw about the hinge), the teeth on both jaws, the mouth's dark line when shut and
    the throat's furnace when it gapes."""
    hx, hy = MOUTH_HINGE
    jx = xf.then(Xf.pose(-p.jaw, (hx, hy), (0.0, 0.0)))            # the jaw drops (anticlockwise, facing left)
    if p.jaw > 1.0:
        cavity = Poly([(-27.4, 1.0), (-22.0, 2.4), (-15.6, 3.0), (-14.6, 4.2), (-22.0, 7.4), (-27.6, 6.4)])
        for q in mid.raster(xf, cavity):
            mid.put(q[0], q[1], I[0])
        if p.gape:
            f = P(xf, (-18.8, 4.2))
            for (dx, dy, col) in ((0, 0, E[3]), (1, 0, E[2]), (-1, 0, E[2]), (0, 1, E[1]), (1, 1, E[1]), (-1, 1, E[1]), (2, 1, E[0]), (-2, 1, E[0])):
                mid.put_glow(f[0] + dx, f[1] + dy, col)
                glow.put_glow(f[0] + dx, f[1] + dy, col)
    lower = Poly([(-26.8, 2.2), (-21.0, 3.2), (-15.6, 3.0), (-14.4, 4.2), (-17.0, 6.2), (-22.0, 6.0), (-25.8, 4.4)])
    linner = mid.part(jx, lower, "iron", face((-0.3, 0.6, 0.75), lo=1, hi=3, fixed=True), rust=0.0)
    mid.part(jx, Poly([(-25.4, 4.2), (-20.0, 5.4), (-17.0, 5.8), (-21.0, 6.0), (-25.0, 5.0)]), "brass", flat(2), outline=False, rust=0.0)
    if p.jaw <= 1.0:
        for k in range(12):                                         # the shut mouth's line, back to the hinge
            q = P(xf, (-26.6 + k * 0.95, 2.0 + k * 0.12))
            if q in mask:
                mid.put(q[0], q[1], I[0])
    for k in range(5):                                              # saw teeth, upper (down) and lower (up)
        x = -25.8 + k * 2.1
        q = P(xf, (x, 2.0 + 0.15 * k))
        mid.put(q[0], q[1] + 1, S[2])
        if k % 2 == 0 or p.jaw > 1.0:
            mid.put(q[0], q[1] + 2, S[1])
        if p.jaw > 1.0:
            lq = P(jx, (x + 1.0, 2.6 + 0.15 * k))
            mid.put(lq[0], lq[1], S[2])
            mid.put(lq[0], lq[1] - 1, S[1])
    return linner


def tail(mid, xf, p):
    hx, hy = TAIL_HUB
    tx = xf.then(Xf.pose(p.tail - p.arch, (hx, hy), (0.0, 0.0)))
    fin = Poly([(19.6, -2.6), (23.6, -4.8), (27.4, -9.0), (31.4, -14.2), (33.0, -14.0), (31.8, -10.0), (29.4, -4.2), (28.2, -0.6),
                (29.6, 4.0), (31.4, 8.0), (30.2, 8.8), (26.0, 5.0), (23.0, 2.6), (19.6, 1.8)])
    finner = mid.part(tx, fin, "iron", face((-0.5, -0.5, 0.7), lo=2, hi=3, gain=1.25, bias=-0.2, snap=45), rust=0.0)
    for q in list(finner):                                         # the lobes' lit leading edges (top and front of each)
        if (q[0], q[1] - 1) not in finner or (q[0] - 1, q[1]) not in finner:
            lx, ly = tx.inv((q[0] + 0.5, q[1] + 0.5))
            mid.put(q[0], q[1], I[4] if ly < 0.0 else I[3])
    for (a, b) in (((24.0, -3.8), (31.4, -12.8)), ((24.0, 1.8), (29.8, 7.0))):   # the lobes' brass spars
        for k in range(8):
            u = k / 7.0
            q = P(tx, (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            if q in finner:
                mid.put(q[0], q[1], B[3] if k % 3 else B[4])
    rivets_along(mid, tx, (24.6, -2.0), (24.6, 1.0), 1, finner)
    cx, cy = xf.fwd((hx, hy))                                        # the hub: a brass cog
    mid.part(Xf(), Ellipse(cx, cy, 2.3, 2.3), "brass", dome(cx - 0.8, cy - 0.8, 2.6, lo=2, hi=5, fixed=True), rust=0.0)
    c = (int(math.floor(cx)), int(math.floor(cy)))
    for (dx, dy) in ((0, -3), (3, 0), (0, 3), (-3, 0)):
        mid.put(c[0] + dx, c[1] + dy, B[2] if dy > 0 or dx > 0 else B[4])
    mid.put(c[0], c[1], B[1])
    return finner


def pectoral(cv, xf, p, depth, dx=0.0, dy=0.0):
    """A pectoral fin swept down and back from under the gills: iron, a brass leading edge, sculling 1 px."""
    fx = xf.then(Xf.pose(-8.0 * p.fin, (-9.0 + dx, 4.6 + dy), (0.0, float(p.fin))))
    pts = [(-10.6 + dx, 4.2 + dy), (-5.0 + dx, 5.0 + dy), (0.4 + dx, 10.6 + dy), (0.0 + dx, 11.8 + dy), (-3.0 + dx, 11.2 + dy), (-8.4 + dx, 7.6 + dy)]
    finner = cv.part(fx, Poly(pts), "iron", flat(3, hi=3), depth=depth, rust=0.0)
    for q in list(finner):                                         # the fin's shadowed trailing half
        lx, ly = fx.inv((q[0] + 0.5, q[1] + 0.5))
        if (lx - dx) > -6.0 + (ly - dy - 5.0) * 0.9:
            cv.put(q[0], q[1], I[max(1, 2 - depth)])
    for k in range(6):
        u = k / 5.0
        q = P(fx, (-9.6 + dx + 9.4 * u, 4.8 + dy + 6.0 * u))
        if q in finner:
            cv.put(q[0], q[1], B[4 - depth] if k % 2 == 0 else B[3 - depth])
    rivets_along(cv, fx, (-6.6 + dx, 5.8 + dy), (-6.6 + dx, 6.6 + dy), 1, finner)
    return finner


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    xf = Xf.pose(p.tilt + p.arch * 0.35, (0.0, 0.0), (float(p.lean), float(p.bob)))
    pectoral(far, xf, p, 1, dx=3.0, dy=-1.4)
    tail(mid, xf, p)
    mask = hull(mid, glow, xf, p)
    jaw(mid, glow, xf, p, mask)
    pectoral(near, xf, p, 0)
    for cv in (far, mid, near):
        despeckle(cv)
    return far, mid, near, glow


SWIM = 6
FRAMES = ([("Swim%d" % k, Pose(tail=round(14.0 * math.sin(2 * math.pi * k / SWIM) / 2.0) * 2.0, bob=1 if k in (1, 2) else 0,
                               fin=1 if k in (2, 3) else 0)) for k in range(SWIM)]
          + [("Rise0", Pose(tilt=-18.0, tail=8.0)), ("Rise1", Pose(tilt=-18.0, tail=-8.0)),
             ("Dive0", Pose(tilt=18.0, tail=8.0)), ("Dive1", Pose(tilt=18.0, tail=-8.0)),
             ("Lunge0", Pose(jaw=24.0, lean=2, tail=-10.0, gape=True)),
             ("Lunge1", Pose(jaw=36.0, lean=-1, tail=12.0, gape=True)),
             ("Lunge2", Pose(jaw=0.0, lean=-2, tail=-6.0)),
             ("Beached0", Pose(arch=14.0, tail=-14.0)), ("Beached1", Pose(arch=-10.0, tail=16.0, bob=1))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The Shark Eye (an accessory) and the gores
# ================================================================================================
def ring(cv, cx, cy, r_out, r_in, ramp, lo, hi):
    """A lit ring (a lens mount, a porthole), per pixel: its own ramp-0 outline outside, lit on the top-left."""
    r = RAMP[ramp]
    pts = set()
    for y in range(int(cy - r_out - 1), int(cy + r_out + 2)):
        for x in range(int(cx - r_out - 1), int(cx + r_out + 2)):
            if r_in <= math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r_out:
                pts.add((x, y))
    for (x, y) in pts:
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        outer = any((x + ox, y + oy) not in pts and math.hypot(x + ox + 0.5 - cx, y + oy + 0.5 - cy) > r_out
                    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if outer:
            cv.put(x, y, r[0])
            continue
        lightness = ((x + 0.5 - cx) * -0.6 + (y + 0.5 - cy) * -0.75) / max(0.5, d)
        cv.put(x, y, r[hi] if lightness > 0.35 else (r[hi - 1] if lightness > -0.35 else r[lo]))
    return pts


def shark_eye_icon():
    """14x14: a riveted iron porthole holding the shark's dark lens, an ember iris ring and a wet glint, its dorsal fin on
    top."""
    cv = Canvas()
    fin = cv.part(Xf(), Poly([(4.2, 3.8), (7.6, 0.2), (8.8, 0.0), (8.4, 2.0), (10.0, 4.0)]), "iron",
                  face((-0.6, -0.4, 0.7), lo=2, hi=4, fixed=True), rust=0.0)
    for (x, y) in ((7, 1), (6, 2)):
        if (x, y) in fin:
            cv.put(x, y, I[4])
    cx, cy = 7.0, 8.4
    ring(cv, cx, cy, 5.6, 3.4, "iron", 2, 4)
    for (x, y) in ((6, 3), (11, 8), (6, 13), (1, 8)):           # rivets at the four points
        cv.put(x, y, I[4])
    for y in range(int(cy - 4), int(cy + 4)):
        for x in range(int(cx - 4), int(cx + 4)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < 3.4:
                lit_side = (x + 0.5 - cx) + (y + 0.5 - cy) < -0.4
                if d > 2.7:
                    col = B[2]                                  # the brass bezel
                elif d > 1.7:
                    col = E[3] if lit_side else E[2]            # the ember iris ring
                else:
                    col = I[0]                                  # the dark pupil
                cv.put(x, y, col)
    cv.put(6, 7, WHITE)                                         # a wet glint
    return to_image(cv.px, 0, 0, 14, 14)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Swim0"])
    return {"Cogtuna_GoreHead": crop({q: c for q, c in mid.px.items() if q[0] <= -12}),
            "Cogtuna_GoreFin": crop(near.px),
            "Cogtuna_GoreTail": crop({q: c for q, c in mid.px.items() if q[0] >= 18})}


def write_rig(path, cell, ymax):
    w, h, ox, oy = cell

    def pt(p):
        return round(p[0] * 2), round((p[1] - ymax) * 2)
    mx, my = pt(MOUTH_POINT)
    vx, vy = pt(VENT_TOP)
    L = ["// <auto-generated> by art/ocean/make_cogtuna_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Ocean.NPCs",
         "{",
         "\t/// <summary>The Cogtuna's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells with",
         "\t/// 2 px under each. The origin is on the cells' bottom row; the hull's centre is <see cref=\"CenterY\"/> px above it",
         "\t/// (the NPC is drawn from its centre). Mouth and Vent (the exhaust) are from the origin, facing left, level frames.</summary>",
         "\tpublic static class CogtunaRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, CenterY = %d;"
         % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), round(ymax * 2)),
         "\t\tpublic const int Swim = 0, SwimFrames = %d, Rise = %d, RiseFrames = 2, Dive = %d, DiveFrames = 2, Lunge = %d, LungeFrames = 3, Beached = %d, BeachedFrames = 2;"
         % (SWIM, INDEX["Rise0"], INDEX["Dive0"], INDEX["Lunge0"], INDEX["Beached0"]),
         "\t\tpublic const int MouthX = %d, MouthY = %d, VentX = %d, VentY = %d;" % (mx, my, vx, vy),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def built():
    frames = [frame(p) for _, p in FRAMES]
    ymax = max(y for fr in frames for cv in fr for (_, y) in list(cv.px) + list(cv.glow))
    return [tuple(shifted(cv, -ymax) for cv in fr) for fr in frames], ymax


def export_all():
    frames, ymax = built()
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Cogtuna%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Cogtuna_Glow.png")
    write_rig(OUT + "NPCs/CogtunaRigData.cs", cell, ymax)
    export(shark_eye_icon(), OUT + "Items/SharkEye.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    frames, ymax = built()
    cw, ch = 72, 44
    cols = 5
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2 + 18), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, fr in enumerate(frames):
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in fr[:3]:
                t.alpha_composite(to_image(cv.px, -cw // 2, -ch + 4, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
    extras = Image.new("RGBA", (cw * cols, 18), (36, 40, 48, 255))
    extras.alpha_composite(shark_eye_icon(), (4, 2))
    sheet.paste(extras, (0, ch * rows * 2))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
