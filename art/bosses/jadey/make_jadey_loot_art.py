"""Source for Jadey's loot and summon (D4), 2026-11-17 (the glaive 2026-11-18). Run from the repo root:

    python -P art/bosses/jadey/make_jadey_loot_art.py [--preview FILE]

User, 2026-11-17: the Jade-shaper Pendant, the Jade Incense (her summon, sold by the Friendo-bot), her three weapons (the
Jade-shaper Whip, the Jade Cursed Glaives "like the image example", the Firework Cannon) and the buffs they need. Drawn at 1x
in the Cogpunk palette with art/bosses/trashtr0m/rig.py's parts and shaders (Canvas, Xf, Poly, Ellipse, Capsule), exported 2x.

The Jade Cursed Glaive (2026-11-18: the user's own art, reference/jade_cursed_glaive_user_2026-11-18.webp, read on its pixel
grid and shrunk to Terraria's size by user_art.py, its emblem redrawn pixel by pixel; the earlier drawn glaives are in
previous/):
  * The slash (JadeGlaiveSlash.png + _Trail.png, 2 kinds x FRAMES cells): the glaive's gem orbits a point just in front of
    the shoulder on a circle in a plane tilted towards the viewer (a diagonal and the depth axis, tilt K), so the swing
    projects to a thin ellipse along its diagonal: kind 0 "\\" from up-and-behind to down-and-ahead, kind 1 "/" from
    down-and-behind to up-and-ahead; two in a row cross in an X. Each frame is the glaive rendered in 3D (an affine map of
    its plane, sampled back from the art), a step bigger near the viewer, a step smaller and darker behind (the far plane,
    D4 rule 14), with ONE slash (user, 2026-11-18: "one bigger slash effect"): a crescent along the reach behind the blade
    (fel ramp, opaque pixels, drawn added in game). Never turned at runtime (D4 rule 14). JadeGlaiveRigData.cs gets the
    cells, the shoulder, the hub and the reach point at SAMPLES points of each swing (the hits and the arm) and which frames
    pass in front of the body.
  * The throw (JadeGlaiveThrown.png): the glaive spinning in a plane tipped back SPIN_TILT degrees, SPIN_FRAMES turns, in
    columns of SPIN_ROWS.
  * The icon (JadeCursedGlaives.png): the glaive as the user drew it.

Outputs (Content/Bosses/Jadey/...): Items/JadeShaperPendant.png, Items/JadeIncense.png, Buffs/JadeStatue.png,
Buffs/JadeShaperRest.png, Weapons/JadeShaperWhip.png, Weapons/JadeShaperWhipProjectile.png, Weapons/JadeShaperWhipDebuff.png,
Weapons/JadeCursedGlaives.png, Weapons/JadeGlaiveSlash.png, Weapons/JadeGlaiveSlash_Trail.png, Weapons/JadeGlaiveThrown.png,
Weapons/JadeGlaiveRigData.cs, Weapons/FireworkCannon.png, Weapons/FireworkRocket.png, Weapons/FireworkRocket_Burst.png.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, HERE)
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, Canvas, flat, dome, face, finish)  # noqa: E402
from rig import COLOR_INDEX, soften_orphans  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
import user_art  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Bosses/Jadey/"
GH, G, K, ST, IV, AE, EM, SM, OK, HI, BR = (RAMP[k] for k in ("ghost", "gilt", "crimson", "steel", "ivory", "aether", "ember", "steam",
                                                              "oak", "hide", "brass"))
LIGHT = (-0.45, -0.62, 0.64)                      # top-left, towards the viewer (rig.lit's light, normalised below)


def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def mul(v, k):
    return tuple(c * k for c in v)


L3 = norm(LIGHT)


def img_of(cv, w, h, ox=0, oy=0, glow=False):
    return to_image(cv.glow if glow else cv.px, -ox, -oy, w, h)


# ================================================================================================
# The glaive (2026-11-18, third pass; user: "you are not getting the glaive design so i did (its on the image of the prompt).
# just resize to match terraria but keep the detail and style. Also fix the slash of this weapon as its making 2 separate
# slashes effects now causing visual disconfort, it should have one bigger slash effect (does not need to match blade size,
# so do make the glaive huge to fit)"). The glaive is the user's own art (reference/jade_cursed_glaive_user_2026-11-18.webp),
# read on its own pixel grid, put in the palette (the new Fel and Plum ramps keep its vivid greens and dark membranes) and
# shrunk GLAIVE_SCALE times by area (user_art.py): 74 x 27 px at 1x, 148 px across in game (huge, as asked). Its emblem (a
# gilt shield, a dark steel star on crossed silver blades, the lime gem) blurred when shrunk, so it is redrawn pixel by pixel
# at that size. The 2026-11-17 passes (two linked crescents; one drawn glaive) are in previous/.
# Local axes as before: u along the glaive (the gem at 0), v up, the way its tips curl. A pose renders the bitmap through the
# pose's affine map (each pixel sampled back from a 4x EPX-smoothed copy of the art, RotSprite's way, so turned edges stay
# clean), never turned at runtime (D4 rule 14).
# ================================================================================================
GLAIVE_REF = "art/bosses/jadey/reference/jade_cursed_glaive_user_2026-11-18.webp"
GLAIVE_SCALE = 2.5
GEM_NATIVE = (94.5, 39.0)                          # the gem's centre on the reference's own grid
FEL, PLUM = RAMP["fel"], RAMP["plum"]
SUPER = 4                                          # the EPX copy's scale (two Scale2x passes)
SHIELD = [(-7.2, -6.0), (-4.2, -7.2), (0.0, -8.4), (4.2, -7.2), (7.2, -6.0), (8.2, -2.0), (7.4, 3.0), (4.6, 7.0), (0.5, 9.6),
          (-0.5, 9.6), (-4.6, 7.0), (-7.4, 3.0), (-8.2, -2.0)]
STAR_ROWS = (".....#.....", ".....#.....", "....###....", "....###....", "###########", ".#########.", "..#######..",
             "...#####...", "...##.##...", "..##...##..", ".##.....##.")


def _inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _edge(region, q):
    x, y = q
    return any((x + dx, y + dy) not in region for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def emblem(pix, hx, hy):
    """The guard's emblem at sprite size (the user's design): a gilt shield (its rim lit top-left, a dark inner border down
    the sides), crossed silver blades behind a dark steel star (their tips at the shield's top corners, a third blade down
    between the star's legs), the star's gilt rim, the lime gem in its heart. px from the gem; lit from the top-left."""
    region = {}
    for y in range(-10, 11):
        for x in range(-10, 11):
            if _inside(SHIELD, x + 0.5, y + 0.5):
                region[(x, y)] = True
    for (x, y) in region:
        pix[(hx + x, hy + y)] = ST[2] if (x + y) < -5 else ST[1]
    for (x, y) in list(region):
        if _edge(region, (x, y)):
            pix[(hx + x, hy + y)] = G[7] if (x < 0 and y < 2) or y < -5 else G[5] if x <= 0 or y < 0 else G[3]
        elif any(_edge(region, (x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) and abs(x) >= 5 and -3 <= y <= 4:
            pix[(hx + x, hy + y)] = G[2]
    star = set()
    for r, row in enumerate(STAR_ROWS):
        for c, ch in enumerate(row):
            if ch == "#":
                star.add((c - 5, r - 5))
    for (x, y, col) in ((-6, -6, ST[7]), (-5, -6, ST[6]), (-5, -5, ST[7]), (-4, -5, ST[6]), (-4, -4, ST[7]), (-3, -4, ST[5]),
                        (-3, -3, ST[6]), (5, -6, ST[6]), (4, -6, ST[7]), (4, -5, ST[6]), (3, -5, ST[7]), (3, -4, ST[6]), (2, -4, ST[5]),
                        (2, -3, ST[5]), (-1, 4, ST[7]), (0, 4, ST[5]), (-1, 5, ST[7]), (0, 5, ST[5]), (-1, 6, ST[6]), (0, 6, ST[4]),
                        (-1, 7, ST[5]), (0, 7, ST[4])):
        if (x, y) in region and not _edge(region, (x, y)) and (x, y) not in star:
            pix[(hx + x, hy + y)] = col
    for (x, y) in star:
        pix[(hx + x, hy + y)] = ST[3] if x < 0 and y <= 0 else ST[2] if x < 0 or y < 0 else ST[1]
    for (x, y) in star:
        if _edge(star, (x, y)):
            pix[(hx + x, hy + y)] = G[7] if (x < 0 and y < 1) or y < -2 else G[4]
    for (dx, dy, c) in ((-1, -1, FEL[7]), (0, -1, FEL[6]), (-1, 0, FEL[6]), (0, 0, FEL[5])):
        pix[(hx + dx, hy + dy)] = c


def glaive_bitmap():
    """{(i, j): colour}: the glaive at 1x, (0, 0) the gem's pixel, j down (local u = i + 0.5, v = -(j + 0.5))."""
    rows = user_art.native(GLAIVE_REF, user_art.GRIDS["glaive"])
    pix = user_art.to_palette(rows, FEL + PLUM + G + ST, (26, 27, 36))
    x0, y0 = min(x for x, _ in pix), min(y for _, y in pix)
    keep = {FEL[0]: 1.35, FEL[6]: 1.5, FEL[7]: 1.3, PLUM[0]: 1.2, G[0]: 1.3, G[1]: 1.2, ST[0]: 1.35, G[7]: 1.25, G[8]: 1.25}
    sm = user_art.tidy(user_art.shrink(pix, GLAIVE_SCALE, keep=keep))
    hx = int(round((GEM_NATIVE[0] - x0) / GLAIVE_SCALE))
    hy = int(round((GEM_NATIVE[1] - y0) / GLAIVE_SCALE))
    emblem(sm, hx, hy)
    return {(x - hx, y - hy): c for (x, y), c in sm.items()}


def epx(pix):
    """Scale2x (EPX) of a sparse image (absent = clear): corners take a neighbour's colour where two agree."""
    xs, ys = [x for x, _ in pix], [y for _, y in pix]
    out = {}
    for y in range(min(ys) - 1, max(ys) + 2):
        for x in range(min(xs) - 1, max(xs) + 2):
            p = pix.get((x, y))
            a, b, c, d = pix.get((x, y - 1)), pix.get((x + 1, y)), pix.get((x - 1, y)), pix.get((x, y + 1))
            q = (a if (c == a and c != d and a != b) else p, b if (a == b and a != c and b != d) else p,
                 c if (d == c and d != b and c != a) else p, d if (b == d and b != a and d != c) else p)
            for k, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
                if q[k] is not None:
                    out[(2 * x + dx, 2 * y + dy)] = q[k]
    return out


GLAIVE = glaive_bitmap()
GLAIVE_X4 = epx(epx(GLAIVE))
U_MIN = min(i for i, _ in GLAIVE)
U_MAX = max(i for i, _ in GLAIVE) + 1
V_MIN = -(max(j for _, j in GLAIVE) + 1)
V_MAX = -min(j for _, j in GLAIVE)
HALF_SPAN = max(-U_MIN, U_MAX)                     # the gem to the farther blade tip (1x px along u)


def _darker(c):
    ramp, k = COLOR_INDEX.get(c, (None, 0))
    return RAMP[ramp][k - 1] if ramp is not None and k > 0 else c


def draw_glaive(cv, xf, far=0):
    """The user's glaive placed by xf (local u, v -> rig px), sampled back pixel by pixel from its 4x EPX copy; far: a ramp
    step darker (behind the wielder). Returns the gem's rig px."""
    det = xf.a * xf.d - xf.b * xf.c
    if abs(det) < 1e-4:
        return xf.fwd((0.0, 0.0))
    corners = [xf.fwd((u, v)) for u in (U_MIN, U_MAX) for v in (V_MIN, V_MAX)]
    x0, x1 = int(math.floor(min(p[0] for p in corners))) - 1, int(math.ceil(max(p[0] for p in corners))) + 1
    y0, y1 = int(math.floor(min(p[1] for p in corners))) - 1, int(math.ceil(max(p[1] for p in corners))) + 1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            votes, clear = {}, 0
            for sy in (1.0 / 6, 0.5, 5.0 / 6):                 # 3 x 3 samples a pixel, the majority wins (no sparkle)
                for sx in (1.0 / 6, 0.5, 5.0 / 6):
                    u, v = xf.inv((x + sx, y + sy))
                    c = GLAIVE_X4.get((int(math.floor(u * SUPER)), int(math.floor(-v * SUPER))))
                    if c is None:
                        clear += 1
                    else:
                        votes[c] = votes.get(c, 0) + 1
            if votes and clear < 5:
                c = max(votes.items(), key=lambda kv: (kv[1], -sum(kv[0])))[0]
                cv.put(x, y, _darker(c) if far else c)
    soften_orphans(cv, 14.0)
    return xf.fwd((0.0, 0.0))


def plane_xf(hub, eu, ev, s):
    """Local (u, v) -> rig px for a flat glaive whose axes are the 3D unit vectors eu, ev (projected, scaled by s)."""
    return Xf(s * eu[0], s * ev[0], s * eu[1], s * ev[1], hub[0], hub[1])


# --- the slash ------------------------------------------------------------------------------------------------------------
FRAMES, SAMPLES = 8, 16
TILT_K = 0.55                                      # the swing plane's lean towards the viewer (the ellipse's thickness)
SHOULDER = (1.0, -4.0)                             # 1x px from the wielder's centre, facing right
CENTRE = (3.0, -4.0)                               # the point the hub circles, just in front of the shoulder
HUB_RADIUS = 4.0
THETAS = (212.0, 168.0, 128.0, 92.0, 58.0, 24.0, -8.0, -22.0)   # degrees, frame by frame (frame 0: the wind-up, held)
TRAIL_SPAN = (0.0, 64.0, 70.0, 74.0, 74.0, 70.0, 56.0, 30.0)    # degrees of slash behind each frame's blade
PERSPECTIVE = 0.14
FACE_BLEND = 0.7                                   # how far the blade turns its face to the viewer (a stylised roll)
TIP_RADIUS = HUB_RADIUS + HALF_SPAN
# the attack's reach: the 2026-11-17 glaive's tip (27.4 px from the swing's centre) plus the user's "+3 tiles" (24 px); the
# 2026-11-18 glaive is bigger and fills most of it (user: "make the glaive huge to fit")
REACH_RADIUS = 51.4
SLASH_THICK = 18.0                                 # the slash's depth behind the blade (1x px in the swing plane), thinning to its tail


def swing_axes(kind):
    if kind == 0:                                  # "\": from up-left (behind) to down-right, bulging up-front
        u, n = norm((1.0, 1.0, 0.0)), norm((1.0, -1.0, 0.0))
    else:                                          # "/": from down-left (behind) to up-right, bulging down-front
        u, n = norm((1.0, -1.0, 0.0)), norm((1.0, 1.0, 0.0))
    w = norm(add(mul(n, TILT_K), (0.0, 0.0, math.sqrt(1.0 - TILT_K * TILT_K))))
    return u, w


def swing_point(kind, theta, r):
    u, w = swing_axes(kind)
    t = math.radians(theta)
    d = add(mul(u, math.cos(t)), mul(w, math.sin(t)))
    p = add((CENTRE[0], CENTRE[1], 0.0), mul(d, r))
    return p, d


def face_axis(eu, et):
    """The blade's v axis: the way it moves, rolled FACE_BLEND of the way towards facing the viewer about its own length."""
    px, py = eu[0], eu[1]
    q = norm((-py, px, 0.0)) if abs(px) + abs(py) > 1e-6 else (0.0, 1.0, 0.0)
    if dot(q, et) < 0:
        q = mul(q, -1.0)
    q = norm(add(q, mul(eu, -dot(q, eu))))
    v = norm(add(mul(et, 1.0 - FACE_BLEND), mul(q, FACE_BLEND)))
    return norm(add(v, mul(eu, -dot(v, eu))))


def slash_pose(kind, theta):
    """(hub 3D, e_u radial, e_v leading/rolled, blade normal, scale) for a swing angle."""
    u, w = swing_axes(kind)
    t = math.radians(theta)
    eu = add(mul(u, math.cos(t)), mul(w, math.sin(t)))
    et = add(mul(u, math.sin(t)), mul(w, -math.cos(t)))       # the way it moves (theta falls)
    ev = face_axis(eu, et)
    hub = add((CENTRE[0], CENTRE[1], 0.0), mul(eu, HUB_RADIUS))
    s = 1.0 + PERSPECTIVE * (hub[2] / HUB_RADIUS)
    return hub, eu, ev, cross(eu, ev), s


def theta_at(sample):
    """The swing angle at a sample (two samples a frame; the last frame holds)."""
    f = sample / 2.0
    i = min(FRAMES - 1, int(f))
    j = min(FRAMES - 1, i + 1)
    a = f - i
    return THETAS[i] + (THETAS[j] - THETAS[i]) * a


def projected(kind, theta, r):
    p, _ = swing_point(kind, theta, r)
    sc = 1.0 + PERSPECTIVE * (p[2] / TIP_RADIUS)
    return CENTRE[0] + (p[0] - CENTRE[0]) * sc, CENTRE[1] + (p[1] - CENTRE[1]) * sc


def slash_frame(kind, f):
    """The glaive at the frame's swing angle and ONE slash (user, 2026-11-18): a single crescent in the swing plane over the
    last TRAIL_SPAN degrees along the reach (where the blade's tip and the attack's +3 tiles cut), SLASH_THICK deep right
    behind the blade and thinning to its tail, its outer (cutting) edge a bright line, fading with age. Every pixel is the swing plane inverted (the
    plane's projection is an affine map), so the crescent is exact and smooth."""
    cv, trail = Canvas(), Canvas()
    theta = THETAS[f]
    hub, eu, ev, n, s = slash_pose(kind, theta)
    far = 1 if hub[2] < -0.05 else 0
    span = TRAIL_SPAN[f]
    if span > 0:
        u3, w3 = swing_axes(kind)
        det = u3[0] * w3[1] - u3[1] * w3[0]
        reach = int(math.ceil(REACH_RADIUS)) + 2
        for py in range(int(CENTRE[1]) - reach, int(CENTRE[1]) + reach + 1):
            for px in range(int(CENTRE[0]) - reach, int(CENTRE[0]) + reach + 1):
                dx, dy = px + 0.5 - CENTRE[0], py + 0.5 - CENTRE[1]
                a = (w3[1] * dx - w3[0] * dy) / det
                b = (-u3[1] * dx + u3[0] * dy) / det
                r = math.hypot(a, b)
                d = (math.degrees(math.atan2(b, a)) - theta) % 360.0
                if d > span:
                    continue
                age = d / span
                thick = SLASH_THICK * (1.0 - age) ** 0.65
                r_in = REACH_RADIUS - thick
                if r < r_in or r > REACH_RADIUS or thick < 1.0:
                    continue
                depth = (r - r_in) / thick                    # 0 at the inner edge .. 1 at the cutting edge
                inten = (1.0 - age) ** 0.7 * (0.25 + 0.75 * depth ** 2.0)
                if r > REACH_RADIUS - 1.3 and age < 0.75:
                    inten = max(inten, 0.85)                  # the cutting edge: one bright line
                col = (FEL[7] if inten > 0.8 else FEL[6] if inten > 0.6 else FEL[5] if inten > 0.42 else FEL[4] if inten > 0.27
                       else FEL[3] if inten > 0.15 else None)
                if col is not None:
                    trail.put(px, py, col)
        soften_orphans(trail, 30.0)
    draw_glaive(cv, plane_xf(hub, eu, ev, s), far)
    return cv, trail, far == 0


def sample_points(kind, sample):
    """The hub and the attack's reach (along the blade, in perspective) at a sample."""
    theta = theta_at(sample)
    hub, eu, ev, n, s = slash_pose(kind, theta)
    reach = projected(kind, theta, REACH_RADIUS)
    return (hub[0], hub[1]), reach


# --- the throw and the icon -------------------------------------------------------------------------------------------------
SPIN_FRAMES, SPIN_TILT = 16, 38.0
SPIN_ROWS = 8                                      # the spin sheet in columns of 8 (2026-11-18: under the 2048 px limit)


def spin_frame(k):
    cv = Canvas()
    phi = math.radians(k * 360.0 / SPIN_FRAMES)
    tilt = math.radians(SPIN_TILT)
    X, Y = (1.0, 0.0, 0.0), (0.0, math.cos(tilt), math.sin(tilt))
    eu = add(mul(X, math.cos(phi)), mul(Y, math.sin(phi)))
    ev = add(mul(X, -math.sin(phi)), mul(Y, math.cos(phi)))
    draw_glaive(cv, plane_xf((0.0, 0.0), eu, ev, 1.0), 0)
    return cv


def icon():
    """The user's glaive as drawn: level, its blades curling up, the emblem in the middle."""
    cv = Canvas()
    for (i, j), c in GLAIVE.items():
        cv.put(i, j, c)
    return cv


# ================================================================================================
# The whip
# ================================================================================================
def whip_sheet():
    """8 x 40 (1x): the handle (rows 0-13), a jade bead (15-19), a gilt bead (21-25), the dart (27-39), all pointing down."""
    cv = Canvas()
    # the handle: a gilt pommel ring, a crimson-wrapped grip, a gilt collar, the cord leaving downwards
    cv.part(Xf(), Ellipse(3.5, 1.6, 1.7, 1.5), "gilt", dome(3.0, 1.0, 2.0, lo=4, hi=8, fixed=True), rust=0.0)
    cv.part(Xf(), Capsule((3.5, 3.2), (3.5, 9.6), 1.55), "crimson", face((-0.6, 0.0, 0.8), lo=2, hi=5, ramp_len=6, fixed=True), rust=0.0)
    for y in (4, 6, 8):
        cv.put(3, y, K[1])                            # the wrap's turns
    cv.part(Xf(), Poly([(1.4, 10.2), (5.6, 10.2), (4.6, 12.6), (2.4, 12.6)]), "gilt", flat(6), rust=0.0)
    cv.put(2, 10, G[8])
    # the beads
    cv.part(Xf(), Ellipse(3.5, 17.5, 2.4, 2.3), "ghost", dome(2.6, 16.6, 2.6, lo=2, hi=5, fixed=True), rust=0.0)
    cv.put(2, 16, GH[5])
    cv.part(Xf(), Ellipse(3.5, 23.5, 2.0, 2.2), "gilt", dome(2.8, 22.6, 2.4, lo=4, hi=8, fixed=True), rust=0.0)
    cv.put(3, 22, G[9])
    # the dart: a gilt ring and collar, a long jade leaf blade pointing down
    cv.part(Xf(), Ellipse(3.5, 28.0, 1.6, 1.3), "gilt", flat(6), rust=0.0)
    cv.part(Xf(), Poly([(2.0, 29.4), (5.0, 29.4), (4.6, 31.0), (2.4, 31.0)]), "gilt", flat(5), rust=0.0)
    blade = Poly([(1.0, 31.2), (6.0, 31.2), (6.4, 33.5), (5.0, 36.5), (3.5, 39.6), (2.0, 36.5), (0.6, 33.5)])
    cv.part(Xf(), blade, "ghost", face((-0.55, -0.3, 0.75), lo=2, hi=5, ramp_len=6, fixed=True), rust=0.0)
    for y in range(32, 38):
        cv.put(3, y, GH[2] if y > 33 else GH[3])     # the leaf's spine
    cv.put(2, 32, GH[5])
    finish(cv)
    return cv


def whip_item():
    """The inventory look: the gilt handle low on the left, the crimson cord thrown in one loop, Jadey's jade dart at the top
    right (vanilla's whip icons show the lash coiled like this). The cord is two pixels thick, lit on its upper side and
    shadowed under it (an outline would swallow a cord this thin)."""
    cv = Canvas()
    pts = []
    for k in range(121):
        t = k / 120.0
        a = math.radians(205.0 - 395.0 * t)
        r = 5.2 - 1.4 * t
        pts.append((8.4 + r * math.cos(a) + 5.8 * t, 9.6 + r * math.sin(a) * 0.85 - 5.4 * t))
    cord = set()
    for (x, y) in pts:
        for dx in (0, 1):
            for dy in (0, 1):
                cord.add((int(math.floor(x)) + dx, int(math.floor(y)) + dy))
    for (x, y) in cord:
        below = (x, y + 1) not in cord or (x + 1, y) not in cord
        above = (x, y - 1) not in cord or (x - 1, y) not in cord
        cv.put(x, y, K[1] if below and not above else K[4] if above and not below else K[3])
    cv.part(Xf.pose(-38.0, (0.0, 0.0), (3.4, 14.8)), Capsule((0.0, 0.0), (0.0, -4.4), 1.5), "gilt",
            lambda i: 7 if i.lx < -0.2 else 5, rust=0.0)
    cv.part(Xf(), Ellipse(2.4, 15.6, 1.5, 1.4), "gilt", lambda i: 8 if i.lx + i.ly < 17.6 else 5, rust=0.0)
    tip = pts[-1]
    blade = Xf.pose(42.0, (0.0, 0.0), (tip[0] + 1.4, tip[1] - 1.9))
    cv.part(blade, Poly([(0.0, -5.0), (2.3, -1.2), (1.9, 2.0), (0.0, 3.4), (-1.9, 2.0), (-2.3, -1.2)]), "ghost",
            lambda i: 5 if i.lx < -0.7 else 4 if i.lx < 0.7 else 3, rust=0.0)
    return cv


# ================================================================================================
# The Firework Cannon, its rocket and its burst
# ================================================================================================
def cannon():
    """26 x 12, pointing right: a cinnabar lacquered tube in gilt bands, a jade dragon's head at the muzzle, a fuse at the
    back, an oak stock and grip under it. Kept to 16 colours (D4 rule 5)."""
    cv = Canvas()
    cv.part(Xf(), Poly([(5.0, 7.0), (10.0, 7.0), (9.0, 11.5), (6.4, 11.5)]), "oak", lambda i: 2 if i.lx < 7.4 else 1, rust=0.0)
    cv.part(Xf(), Poly([(0.6, 4.6), (6.0, 4.0), (6.0, 7.6), (1.0, 8.2)]), "oak", lambda i: 2 if i.ly < 6.0 else 1, rust=0.0)
    tube = Poly([(4.0, 2.2), (19.0, 1.8), (19.0, 7.6), (4.0, 7.4)])
    cv.part(Xf(), tube, "crimson", lambda i: 5 if i.ly < 3.6 else 4 if i.ly < 5.6 else 3, rust=0.0)
    for x in (6, 11, 16):
        for y in range(2, 8):
            cv.put(x, y, G[7] if y < 4 else G[5] if y < 6 else G[3])
            cv.put(x + 1, y, G[5] if y < 4 else G[3])
    head = Poly([(18.4, 1.0), (22.0, 0.6), (25.6, 2.6), (25.6, 7.2), (22.6, 8.8), (18.4, 8.4)])
    cv.part(Xf(), head, "ghost", lambda i: 5 if i.lx + i.ly < 23.5 else 4 if i.lx + i.ly < 28.0 else 3, rust=0.0)
    for (x, y, col) in ((24, 4, GH[0]), (24, 5, GH[0]), (25, 5, GH[0]), (21, 2, G[7]), (22, 2, G[5]), (23, 7, GH[3]), (19, 3, GH[5])):
        cv.put(x, y, col)
    for (x, y, col) in ((3, 2, G[3]), (2, 1, G[3]), (1, 0, G[7]), (2, 0, K[5])):
        cv.put(x, y, col)                                # the fuse and its spark
    finish(cv)
    return cv


ROCKET_HEADINGS, ROCKET_CELL = 16, 18


def rocket(k):
    """The firework at heading k (k * 22.5 degrees, 0 = right, clockwise on screen): a fat cinnabar body with a gilt band, a
    gilt cone, a little oak stick and a fizzing spark behind; drawn at the heading (never rotated at runtime). Lit in its own
    space (the top of the body is its lit side), so the light turns with the heading in 22.5 degree steps."""
    cv = Canvas()
    xf = Xf.pose(k * 22.5, (0.0, 0.0), (ROCKET_CELL / 2.0, ROCKET_CELL / 2.0))
    cv.part(xf, Capsule((-7.6, 0.0), (-3.4, 0.0), 0.75), "oak", lambda i: 4 if i.ly < 0.0 else 3, rust=0.0)
    body = Poly([(-3.8, -2.6), (2.4, -2.6), (2.4, 2.6), (-3.8, 2.6)])
    cv.part(xf, body, "crimson", lambda i: 5 if i.ly < -1.2 else 4 if i.ly < 0.6 else 3, rust=0.0)
    cv.part(xf, Poly([(2.2, -2.8), (7.2, 0.0), (2.2, 2.8)]), "gilt", lambda i: 8 if i.ly < -0.6 else 6 if i.ly < 0.8 else 5, rust=0.0)
    cv.part(xf, Poly([(-2.2, -2.7), (-0.8, -2.7), (-0.8, 2.7), (-2.2, 2.7)]), "gilt", lambda i: 7 if i.ly < 0.0 else 5, rust=0.0)
    tail = xf.fwd((-8.8, 0.0))
    cv.put(int(tail[0]), int(tail[1]), EM[3])          # the fuse's spark
    return cv


BURST_FRAMES, BURST_CELL = 6, 48


def burst(k):
    """Frame k of the firework's burst (48 x 48 at 1x): a white-gilt flash, then rays of gilt, jade and aether stars flying
    out, then twinkling sparks fading out (friendly Brass and Aether, plus Jadey's jade). Opaque pixels, drawn added."""
    cv = Canvas()
    c = BURST_CELL / 2.0
    rng = random.Random(17)
    rays = [(rng.uniform(0, 360), rng.uniform(0.8, 1.0), (G, GH, AE)[n % 3]) for n in range(15)]
    if k == 0:
        for y in range(BURST_CELL):
            for x in range(BURST_CELL):
                r = math.hypot(x + 0.5 - c, y + 0.5 - c)
                if r < 3.2:
                    cv.put(x, y, SM[3])
                elif r < 5.6:
                    cv.put(x, y, G[9])
                elif r < 7.4 and (x + y) % 2 == 0:
                    cv.put(x, y, G[8])
        return cv
    reach = (0.0, 9.0, 15.0, 19.0, 21.5, 22.5)[k]
    tail = (0.0, 7.0, 7.0, 5.0, 2.5, 0.0)[k]
    for (ang, sp, ramp) in rays:
        a = math.radians(ang)
        r1 = reach * sp
        hi = len(ramp) - 1
        steps = int(max(1, tail * 2))
        for s in range(steps + 1):
            r = r1 - tail * s / steps
            x, y = c + math.cos(a) * r, c + math.sin(a) * r * 0.92
            col = ramp[hi] if s == 0 else ramp[max(1, hi - 1 - s * 2 // max(1, steps))]
            if k >= 4 and s == 0 and rng.random() < 0.35:
                continue                                  # twinkling out
            cv.put(int(math.floor(x)), int(math.floor(y)), col)
        if k <= 3:                                        # each star's cross
            x, y = int(math.floor(c + math.cos(a) * r1)), int(math.floor(c + math.sin(a) * r1 * 0.92))
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.put(x + dx, y + dy, ramp[max(1, hi - 1)])
    if k == 1:
        for y in range(BURST_CELL):
            for x in range(BURST_CELL):
                if math.hypot(x + 0.5 - c, y + 0.5 - c) < 3.0:
                    cv.put(x, y, G[8])
    return cv


# ================================================================================================
# The pendant, the incense, the buff icons
# ================================================================================================
def pendant():
    """12 x 16: a red cord loop, a gilt bail, a round jade medallion carved as a panda's face (Jadey's)."""
    cv = Canvas()
    for (x, y) in ((4, 0), (5, 0), (6, 0), (7, 0), (3, 1), (8, 1), (3, 2), (8, 2), (4, 3), (7, 3)):
        cv.put(x, y, K[3] if y < 2 else K[2])
    cv.part(Xf(), Poly([(4.0, 3.6), (8.0, 3.6), (7.2, 6.0), (4.8, 6.0)]), "gilt", flat(6), rust=0.0)
    cv.put(5, 4, G[8])
    for ex in (2.6, 9.4):
        cv.part(Xf(), Ellipse(ex, 7.4, 1.7, 1.6), "ghost", flat(2), rust=0.0)       # the ears (dark jade)
    cv.part(Xf(), Ellipse(6.0, 10.6, 5.6, 5.0), "ghost", dome(4.2, 8.6, 6.2, lo=3, hi=5, fixed=True), rust=0.0)
    for (x, y) in ((3, 9), (4, 9), (3, 10), (4, 10), (7, 9), (8, 9), (7, 10), (8, 10), (4, 11), (8, 11)):
        cv.put(x, y, GH[1])                                # the eye patches
    for (x, y) in ((4, 10), (7, 10)):
        cv.put(x, y, GH[5])                                # the eyes
    cv.put(5, 12, GH[1])
    cv.put(6, 12, GH[1])                                   # the nose
    cv.put(5, 13, GH[2])
    cv.put(6, 13, GH[2])
    cv.put(3, 7, GH[5])                                    # the medallion's glint
    finish(cv)
    return cv


def incense():
    """12 x 16: a gilt censer on three feet, a crimson band, a jade incense stick with an ember tip and a curl of smoke."""
    cv = Canvas()
    for (x, y, col) in ((6, 0, SM[2]), (5, 1, SM[1]), (5, 2, SM[2]), (6, 3, SM[1]), (6, 4, SM[1])):
        cv.put(x, y, col)
    cv.put(6, 5, EM[3])
    cv.put(6, 6, EM[2])
    for y in range(7, 10):
        cv.put(6, y, GH[4] if y < 8 else GH[3])
    bowl = Poly([(1.0, 9.0), (11.0, 9.0), (10.0, 12.6), (8.0, 13.8), (4.0, 13.8), (2.0, 12.6)])
    cv.part(Xf(), bowl, "gilt", lambda i: 8 if i.lx + i.ly < 13.0 else 6 if i.lx + i.ly < 18.0 else 4, rust=0.0)
    for x in range(2, 11):
        cv.put(x, 11, K[3] if x < 6 else K[2])
    for (x0, y0, x1) in ((3, 14, 2), (6, 14, 6), (9, 14, 10)):
        cv.put(x0, y0, G[4])
        cv.put(x1, y0 + 1, G[4])
    cv.put(3, 9, G[9])
    finish(cv)
    return cv


def statue_icon():
    """16 x 16 buff: a little jade statue of a person on a gilt plinth."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(8.0, 3.6, 2.4, 2.4), "ghost", dome(7.0, 2.6, 3.0, lo=2, hi=5, fixed=True), rust=0.0)
    cv.part(Xf(), Poly([(5.0, 6.0), (11.0, 6.0), (11.6, 10.0), (10.0, 12.0), (6.0, 12.0), (4.4, 10.0)]), "ghost",
            face((-0.6, -0.4, 0.7), lo=2, hi=5, ramp_len=6, fixed=True), rust=0.0)
    cv.part(Xf(), Poly([(3.0, 12.0), (13.0, 12.0), (13.0, 15.0), (3.0, 15.0)]), "gilt", face((0.0, -0.7, 0.7), lo=3, hi=8, ramp_len=10, fixed=True), rust=0.0)
    for (x, y) in ((7, 7), (8, 8), (8, 9), (9, 10)):
        cv.put(x, y, GH[2])                                 # a crack
    finish(cv)
    return cv


def rest_icon():
    """16 x 16 debuff: the pendant's medallion gone dull, and a little gilt hourglass."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(6.6, 8.6, 5.4, 5.0), "ghost", dome(5.0, 7.0, 6.0, lo=1, hi=3, fixed=True), rust=0.0)
    for (x, y) in ((4, 7), (5, 7), (8, 7), (9, 7)):
        cv.put(x, y, GH[0])
    cv.part(Xf(), Poly([(10.0, 7.0), (15.0, 7.0), (12.5, 11.0)]), "gilt", flat(6), rust=0.0)
    cv.part(Xf(), Poly([(12.5, 11.0), (15.0, 15.0), (10.0, 15.0)]), "gilt", flat(4), rust=0.0)
    cv.put(12, 13, IV[4])
    cv.put(12, 14, IV[3])
    finish(cv)
    return cv


def tag_icon():
    """16 x 16 tag: Jadey's jade dart over a crimson ring."""
    cv = Canvas()
    for a in range(0, 360, 8):
        t = math.radians(a)
        cv.put(int(math.floor(8 + 5.6 * math.cos(t))), int(math.floor(8 + 5.6 * math.sin(t))), K[3] if a < 180 else K[2])
    blade = Xf.pose(45.0, (0.0, 0.0), (8.0, 8.0))
    cv.part(blade, Poly([(0.0, -6.0), (2.2, -1.5), (1.8, 2.5), (0.0, 4.0), (-1.8, 2.5), (-2.2, -1.5)]), "ghost",
            face((-0.55, -0.3, 0.75), lo=2, hi=5, ramp_len=6, fixed=True), rust=0.0)
    cv.put(9, 5, GH[5])
    finish(cv)
    return cv


# ================================================================================================
# Output
# ================================================================================================
def cells(canvases, w, h, ox, oy, glow=False, pad=1):
    """Equal cells stacked vertically, `pad` px (2 in game) between them; (ox, oy) = the cell px of the rig origin."""
    im = Image.new("RGBA", (w, (h + pad) * len(canvases) - pad), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        for (x, y), col in src.items():
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of cell %d is outside its %dx%d cell" % (x, y, k, w, h))
            im.putpixel((cx, cy + k * (h + pad)), col + (255,))
    return im


def columns(canvases, per_column, w, h, ox, oy, pad=1):
    """Cells in columns of `per_column` (top to bottom, then the next column), `pad` px (2 in game) between them: the
    slash's two kinds side by side (kind 0 the first column), so the sheet stays under the 2048 px texture limit."""
    cols = (len(canvases) + per_column - 1) // per_column
    im = Image.new("RGBA", ((w + pad) * cols - pad, (h + pad) * per_column - pad), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        bx, by = (k // per_column) * (w + pad), (k % per_column) * (h + pad)
        for (x, y), col in cv.px.items():
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of cell %d is outside its %dx%d cell" % (x, y, k, w, h))
            im.putpixel((bx + cx, by + cy), col + (255,))
    return im


def bounds(canvases, glow_too=True):
    pts = [p for cv in canvases for p in list(cv.px) + (list(cv.glow) if glow_too else [])]
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs), min(ys), max(xs), max(ys)


def cs_array(name, values, typ="short"):
    body = ", ".join(str(int(round(v))) for v in values)
    return "\t\tpublic static readonly %s[] %s = { %s };\n" % (typ, name, body)


def render():
    slashes, trails, near = [], [], []
    for kind in (0, 1):
        for f in range(FRAMES):
            cv, tr, n = slash_frame(kind, f)
            slashes.append(cv)
            trails.append(tr)
            near.append(1 if n else 0)
    x0, y0, x1, y1 = bounds(slashes + trails)
    ox, oy = -x0 + 1, -y0 + 1
    w, h = x1 - x0 + 3, y1 - y0 + 3
    w += w % 2
    h += h % 2
    hubs, tips = [], []
    for kind in (0, 1):
        for s in range(SAMPLES):
            hub, tip = sample_points(kind, s)
            hubs.append(hub)
            tips.append(tip)
    spins = [spin_frame(k) for k in range(SPIN_FRAMES)]
    sx0, sy0, sx1, sy1 = bounds(spins)
    half = max(-sx0, sx1 + 1, -sy0, sy1 + 1) + 1
    spin_cell = 2 * half
    return dict(slashes=slashes, trails=trails, near=near, cell=(w, h, ox, oy), hubs=hubs, tips=tips, spins=spins,
                spin=(spin_cell, half))


def write_rig(data, path):
    w, h, ox, oy = data["cell"]
    spin_cell, _ = data["spin"]
    src = ["// Generated by art/bosses/jadey/make_jadey_loot_art.py: do not edit (2026-11-18).\n",
           "namespace Cogpunk.Content.Bosses.Jadey.Weapons\n{\n",
           "\t/// <summary>The Jade Cursed Glaives' rig: the slash sheet's cells (2x px; the origin is the wielder's centre),\n",
           "\t/// the shoulder the arm turns on, the hub and the long blade's tip at each of the swing's samples (2x px from the\n",
           "\t/// wielder's centre, facing right; kind 0 first, then kind 1), which frames pass in front of the body, and the\n",
           "\t/// thrown glaive's spin cells.</summary>\n",
           "\tpublic static class JadeGlaiveRigData\n\t{\n",
           "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Gap = 2;\n" % (2 * w, 2 * h, 2 * ox, 2 * oy),
           "\t\tpublic const int FramesPerSlash = %d, SamplesPerSlash = %d, SpinCell = %d, SpinFrames = %d, SpinRows = %d;\n" % (
               FRAMES, SAMPLES, 2 * spin_cell, SPIN_FRAMES, SPIN_ROWS),
           "\t\tpublic const int ShoulderX = %d, ShoulderY = %d;\n" % (round(2 * SHOULDER[0]), round(2 * SHOULDER[1])),
           cs_array("HubX", [2 * p[0] for p in data["hubs"]]),
           cs_array("HubY", [2 * p[1] for p in data["hubs"]]),
           cs_array("TipX", [2 * p[0] for p in data["tips"]]),
           cs_array("TipY", [2 * p[1] for p in data["tips"]]),
           cs_array("Near", data["near"], "byte"),
           "\t}\n}\n"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(src))
    print("wrote", path)


def flat_image(cv, w, h, ox=None, oy=None):
    """One sprite in a w x h box; without an offset it is centred (on whole pixels) in the box."""
    if ox is None or oy is None:
        x0, y0, x1, y1 = bounds([cv], glow_too=False)
        if x1 - x0 + 1 > w or y1 - y0 + 1 > h:
            raise SystemExit("a %dx%d sprite doesn't fit its %dx%d box" % (x1 - x0 + 1, y1 - y0 + 1, w, h))
        ox, oy = -x0 + (w - (x1 - x0 + 1)) // 2, -y0 + (h - (y1 - y0 + 1)) // 2
    return cells([cv], w, h, ox, oy)


def outputs():
    data = render()
    w, h, ox, oy = data["cell"]
    spin_cell, half = data["spin"]
    out = {
        OUT + "Weapons/JadeGlaiveSlash.png": columns(data["slashes"], FRAMES, w, h, ox, oy),
        OUT + "Weapons/JadeGlaiveSlash_Trail.png": columns(data["trails"], FRAMES, w, h, ox, oy),
        OUT + "Weapons/JadeGlaiveThrown.png": columns(data["spins"], SPIN_ROWS, spin_cell, spin_cell, half, half),
        OUT + "Weapons/JadeCursedGlaives.png": flat_image(icon(), U_MAX - U_MIN, V_MAX - V_MIN),
        OUT + "Weapons/JadeShaperWhip.png": flat_image(whip_item(), 18, 18),
        OUT + "Weapons/JadeShaperWhipProjectile.png": flat_image(whip_sheet(), 8, 40),
        OUT + "Weapons/JadeShaperWhipDebuff.png": flat_image(tag_icon(), 16, 16),
        OUT + "Weapons/FireworkCannon.png": flat_image(cannon(), 26, 12),
        OUT + "Weapons/FireworkRocket.png": cells([rocket(k) for k in range(ROCKET_HEADINGS)], ROCKET_CELL, ROCKET_CELL, 0, 0),
        OUT + "Weapons/FireworkRocket_Burst.png": cells([burst(k) for k in range(BURST_FRAMES)], BURST_CELL, BURST_CELL, 0, 0),
        OUT + "Items/JadeShaperPendant.png": flat_image(pendant(), 12, 16),
        OUT + "Items/JadeIncense.png": flat_image(incense(), 12, 16),
        OUT + "Buffs/JadeStatue.png": flat_image(statue_icon(), 16, 16),
        OUT + "Buffs/JadeShaperRest.png": flat_image(rest_icon(), 16, 16),
    }
    return data, out


def preview(path, out, scale=4, bgs=((30, 30, 36), (196, 214, 232))):
    ims = list(out.values())
    width = sum(min(im.width, 200) + 4 for im in ims) + 4
    height = max(min(im.height, 360) for im in ims) + 8
    sheet = Image.new("RGBA", (width * scale, height * scale * len(bgs)), (0, 0, 0, 255))
    for row, bg in enumerate(bgs):
        band = Image.new("RGBA", (width, height), bg + (255,))
        x = 4
        for im in ims:
            crop = im.crop((0, 0, min(im.width, 200), min(im.height, 360)))
            band.alpha_composite(crop, (x, 4))
            x += crop.width + 4
        sheet.paste(band.resize((width * scale, height * scale), Image.NEAREST), (0, row * height * scale))
    sheet.save(path)
    print("preview", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    data, out = outputs()
    for rel, im in out.items():
        export(im, rel)
    write_rig(data, OUT + "Weapons/JadeGlaiveRigData.cs")
    if args.preview:
        preview(args.preview, out)


if __name__ == "__main__":
    main()
