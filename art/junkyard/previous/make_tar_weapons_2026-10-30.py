"""ARCHIVED 2026-11-03: the generator as it stood on 2026-10-30, kept so the first Metal Wrench (thin, cog pommel) and the
aether-eyed tar slime minion can be restored. Running it overwrites the current assets (it writes the same Content/ paths).
Its imports expect to sit in art/junkyard/: copy it back there to run it.
"""
"""Source for the Junkyard's tar and polished-metal weapons of 2026-10-30 (D4; the user named them, so Metal Slug-level
detail at their sizes). Run from the repo root:

    python -P art/junkyard/make_tar_weapons.py [--preview FILE]

Drawn at 1x and exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left, every part outlined in
ramp 0 of its own material (rig.py parts, the rod rasteriser of art/bosses/trashtr0m/make_trashtr0m_loot.py, pixel
details on top). Friendly effects use Brass, Steam and Aether (D3 colour coding); tar keeps its own ramp (rig.RAMP["tar"]),
the bone Tar Tyrant's (rig.RAMP["bone"]). Outputs (Content/Junkyard/Weapons/):

    MetalWrench.png             40x40   item and swing: a big adjustable wrench of polished metal, its grip wrapped in
                                        condensed tar, a rusted cog for a pommel and a brass thumbwheel (Blade of Grass
                                        size, user-set); points to the top right like every sword
    MetalClash.png              64x394  6 frames (stride 66): the clash, a starburst of brass and white with sparks flying
    WrenchRiposteBuff.png       32x32   buff icon: the wrench with a spark at its jaw (the empowered riposte)
    WrenchParryCooldown.png     32x32   debuff icon: the wrench under a turning arrow (the parry is cooling down)
    Tarmancer.png               44x44   item: a claw of tar (user-set), three glossy talons, an aether gem in its back
    TarSlimeMinion.png          36x208  7 frames (stride 30) of 36x28, facing right: idle x2, jump, fall, spit, fly x2
                                        (little tar wings); aether eyes and a brass cog in it (friendly, not the Living Tar)
    TarSlimeBuff.png            32x32   buff icon: a tar slime
    TarSlimeShot.png            20x350  16 headings (stride 22, 0 = flying right, clockwise): a friendly tar glob
    TarBoneStaff.png            44x44   item: a femur wrapped in tar with a little tyrant skull on top, an aether ember
                                        in its eye; points to the top right (Item.staff)
    TyrantSkullBolt.png         32x70   3 frames (stride 24) of 32x22, facing right: the skull it shoots, jaw snapping
    TyrantSkullBlast.png        80x490  6 frames (stride 82): the 5-tile burst of tar and bone where it bites
    TarShower.png               52x28   item and held gun, nozzle to the right: a brass tar tank, a polished-metal pump
                                        with a gauge, a hose, a flared nozzle with tar on its lip
    TarSpray.png                24x126  5 frames (stride 26): a burst of spray growing as it flies
    TarShowerGlob.png           20x350  16 headings (stride 22): the part-charged shot
    TarShowerBigGlob.png        32x542  16 headings (stride 34): the full-charge glob
    TarStain.png                96x50   4 frames (stride 14) of 96x12: the 6-tile stain it leaves, bottom row on the ground
    TarShowerCharge.png         32x202  6 frames (stride 34): the ball of tar swelling at the nozzle (5 sizes, then full)
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Ring, Capsule, Union, Canvas, flat, dome, cyl, line  # noqa: E402
import make_trashtr0m_art as boss  # noqa: E402
from make_trashtr0m_loot import rod, hcyl, boxed  # noqa: E402


OUT = "Content/Junkyard/Weapons/"
I, B, C, E, S, LE, A, T, BN = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "leather", "aether", "tar", "bone"))


def img(cv, w, h, dx=0, dy=0):
    return boss.to_image(cv.px, -dx, -dy, w, h)


def img_fit(cv, w, h, name=""):
    xs = [x for (x, _) in cv.px]
    ys = [y for (_, y) in cv.px]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    if bw > w or bh > h:
        raise SystemExit("%s: art is %dx%d, does not fit %dx%d" % (name, bw, bh, w, h))
    return img(cv, w, h, (w - bw) // 2 - min(xs), (h - bh) // 2 - min(ys))


def vertical(frames, pad=1):
    return boss.vertical(frames, pad)


def export(im, rel):
    boss.export(im, OUT + rel)


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def edge_of(mask):
    return {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def despeckle(cv):
    """No lone pixels (D4): a pixel whose four neighbours are all opaque and all another colour takes the commonest."""
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


# ================================================================================================
# Painter for small round parts (tar, bone): each pixel lit by its own part's normal (top-left light), a narrow
# specular band for wet tar, a z-buffer so later parts sit in front
# ================================================================================================
LIGHT = (-0.6, -0.8)
_L3 = (-0.48, -0.64, 0.6)
_HV = (_L3[0], _L3[1], _L3[2] + 1.0)
HALF = tuple(c / math.sqrt(sum(v * v for v in _HV)) for c in _HV)


def lit_colour(nx, ny, nz, ramp, lo, hi, gloss, power=26.0):
    lit = nx * LIGHT[0] + ny * LIGHT[1] + nz * 0.45
    idx = lo + int(round((hi - lo) * max(0.0, min(1.0, (lit + 0.2) / 1.1))))
    col = ramp[max(lo, min(hi, idx))]
    if gloss:
        sp = max(0.0, nx * HALF[0] + ny * HALF[1] + nz * HALF[2]) ** power
        if sp > 0.9 and len(gloss) > 1:
            col = gloss[1]
        elif sp > 0.55:
            col = gloss[0]
    return col


def _nearest(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ll))
    return t, (p[0] - (a[0] + dx * t), p[1] - (a[1] + dy * t))


def tube(px, pts, r0, r1, ramp, z=0, lo=1, hi=None, zbuf=None, gloss=None):
    """A tapered tube along pts (r0 at the first point, r1 at the last), lit as a cylinder."""
    n = len(pts) - 1
    hi = len(ramp) - 1 if hi is None else hi
    R = max(r0, r1) + 1
    out = set()
    for y in range(int(min(q[1] for q in pts) - R), int(max(q[1] for q in pts) + R) + 1):
        for x in range(int(min(q[0] for q in pts) - R), int(max(q[0] for q in pts) + R) + 1):
            c = (x + 0.5, y + 0.5)
            best = None
            for j in range(n):
                t, off = _nearest(c, pts[j], pts[j + 1])
                r = r0 + (r1 - r0) * (j + t) / n
                d = math.hypot(*off)
                if d <= r and (best is None or d / r < best[0]):
                    best = (d / r, off, r)
            if best is None or (zbuf is not None and zbuf.get((x, y), -99) > z):
                continue
            nx, ny = best[1][0] / best[2], best[1][1] / best[2]
            px[(x, y)] = lit_colour(nx, ny, math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny)), ramp, lo, hi, gloss)
            if zbuf is not None:
                zbuf[(x, y)] = z
            out.add((x, y))
    return out


def ball(px, c, rx, ry, ramp, z=0, lo=1, hi=None, zbuf=None, gloss=None):
    hi = len(ramp) - 1 if hi is None else hi
    out = set()
    for y in range(int(c[1] - ry - 1), int(c[1] + ry + 2)):
        for x in range(int(c[0] - rx - 1), int(c[0] + rx + 2)):
            nx, ny = (x + 0.5 - c[0]) / rx, (y + 0.5 - c[1]) / ry
            if nx * nx + ny * ny > 1.0 or (zbuf is not None and zbuf.get((x, y), -99) > z):
                continue
            px[(x, y)] = lit_colour(nx, ny, math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny)), ramp, lo, hi, gloss)
            if zbuf is not None:
                zbuf[(x, y)] = z
            out.add((x, y))
    return out


def outline(px, region, dark, light=None):
    """Ramp-0 outline round a region, the lit side (open to the top or the left) one step lighter."""
    ed = edge_of(region)
    for p in ed:
        lit = ((p[0] - 1, p[1]) not in region or (p[0], p[1] - 1) not in region) and (p[0] + 1, p[1]) in region and (p[0], p[1] + 1) in region
        px[p] = light if (lit and light is not None) else dark
    return ed


def curve(a, m, b, n=6):
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * m[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * m[1] + t * t * b[1])
            for t in [j / n for j in range(n + 1)]]


def to_canvas(px, glow=()):
    cv = Canvas()
    for q, col in px.items():
        (cv.put_glow if q in glow else cv.put)(q[0], q[1], col)
    return cv


TAR_BODY = [T[1], T[1], T[2], T[2]]                         # tar's tones: deep shade, shade, lit (gloss on top)
TAR_GLOSS = (T[3], T[4])


# ================================================================================================
# Metal Wrench: polished metal, a tar-wrapped grip, a rusted cog pommel, a brass thumbwheel
# ================================================================================================
# The wrench is drawn along the diagonal x + y = WRENCH_AXIS (up and to the right) in bands: s = x + y - WRENCH_AXIS
# across it (s < 0 towards the light), t = x - y along it, so every edge is a clean 45-degree staircase. The head is a
# pixel map: a round open-end jaw, its mouth opening to the top right.
WRENCH_AXIS = 19
WRENCH_HEAD = ("..XXXX..",
               ".XXXX...",
               "XXXX...X",
               "XXXX..XX",
               "XXXXXXXX",
               "XXXXXXXX",
               ".XXXXXX.",
               "..XXXX..")
WRENCH_HEAD_AT = (11, 1)                                    # the head map's top-left
WRENCH_HEAD_C = (15.0, 5.0)                                 # its centre (pixel corners)
POMMEL_C, POMMEL_R = (2.6, 16.6), 2.5                       # the rusted cog's centre and radius


def wrench_bands(px):
    """The handle: pommel cog, ferrule, condensed-tar grip, ferrule, polished shaft with a brass thumbwheel."""
    def shaft(s, t, lo, hi):
        return "1" if lo else ("0" if hi else {-1: I[4], 0: I[3]}.get(s, I[2]))

    def brass(s, t, lo, hi):
        return B[0] if (lo or hi) else (B[4] if s < 0 else (B[3] if s == 0 else B[2]))

    def wheel(s, t, lo, hi):
        if lo or hi:
            return B[0]
        if t % 2:
            return B[1]                                     # the knurling
        return B[5] if s <= -2 else (B[4] if s < 0 else (B[3] if s == 0 else B[2]))

    def grip(s, t, lo, hi):
        if lo:
            return T[1]
        if hi:
            return T[0]
        if t % 2 == 0:
            return T[0] if s >= 0 else T[1]                 # the wraps of condensed tar, glossy between them
        return T[3] if s == -1 else (T[2] if s == 0 else T[1])

    segs = ((-9, -9, -2, 2, brass), (-8, -3, -2, 2, grip), (-2, -2, -2, 2, brass), (2, 3, -3, 3, wheel), (-1, 6, -2, 2, shaft))
    for y in range(20):
        for x in range(20):
            s, t = x + y - WRENCH_AXIS, x - y
            for (t0, t1, s0, s1, paint) in segs:
                if t0 <= t <= t1 and s0 <= s <= s1:
                    col = paint(s, t, s == s0, s == s1)
                    px[(x, y)] = I[1] if col == "1" else (I[0] if col == "0" else col)
                    break


def wrench_pommel(px):
    """A rusted cog: a disc of copper lit from the top-left, four teeth, a dark hub."""
    disc = {(x, y) for x in range(0, 7) for y in range(13, 20)
            if (x + 0.5 - POMMEL_C[0]) ** 2 + (y + 0.5 - POMMEL_C[1]) ** 2 <= POMMEL_R ** 2}
    for (x, y) in disc:
        v = -((x + 0.5 - POMMEL_C[0]) + (y + 0.5 - POMMEL_C[1])) / POMMEL_R
        px[(x, y)] = C[3] if v > 0.0 else (C[2] if v > -0.9 else C[1])
    teeth = {(int(math.floor(POMMEL_C[0] + math.cos(a) * (POMMEL_R + 0.6))), int(math.floor(POMMEL_C[1] + math.sin(a) * (POMMEL_R + 0.6))))
             for a in (math.radians(d) for d in (0, 90, 180, 270))}
    region = disc | teeth
    for q in teeth:
        px[q] = C[2]
    outline(px, region, C[0])
    hub = (int(POMMEL_C[0]), int(POMMEL_C[1]))
    px[hub] = C[0]
    px[(hub[0] - 1, hub[1] - 1)] = B[4]                        # a glint of the brass under the rust


def wrench_head(px):
    mask = set()
    for j, row in enumerate(WRENCH_HEAD):
        for i, ch in enumerate(row):
            if ch == "X":
                mask.add((WRENCH_HEAD_AT[0] + i, WRENCH_HEAD_AT[1] + j))
    hc = WRENCH_HEAD_C

    def in_mouth(q):
        rx, ry = q[0] + 0.5 - hc[0], q[1] + 0.5 - hc[1]
        return (rx - ry) > 0.3 and abs(rx + ry) / math.sqrt(2) < 1.0

    for q in mask:
        x, y = q
        rx, ry = x + 0.5 - hc[0], y + 0.5 - hc[1]
        nb = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if any(n not in mask for n in nb):
            mouth_wall = any(n not in mask and in_mouth(n) for n in nb)
            if mouth_wall and rx + ry > 0:
                px[q] = I[3]                                # the mouth's lit wall
            elif not mouth_wall and (x - 1, y) not in mask and (x, y - 1) not in mask:
                px[q] = I[1]                                # selective outline on the lit side
            else:
                px[q] = I[0]
        else:
            v = -(rx + ry)
            px[q] = I[4] if v > 1.6 else (I[3] if v > -0.6 else (I[2] if v > -2.4 else I[1]))
    px[(13, 3)] = WHITE                                     # a hard glint on the polished head
    px[(12, 4)] = I[4]


def metal_wrench():
    px = {}
    wrench_bands(px)
    wrench_pommel(px)
    wrench_head(px)
    return img(to_canvas(px), 20, 20)


# ================================================================================================
# The clash: a starburst (friendly brass, steam and a touch of aether)
# ================================================================================================
def clash_frames():
    out = []
    c = 15.5
    for f in range(6):
        cv = Canvas()
        ray_long = (5, 13, 15, 12, 7, 0)[f]
        ray_short = (3, 7, 8, 6, 0, 0)[f]
        core = (2.4, 3.2, 2.6, 1.8, 0.0, 0.0)[f]
        if core > 0:
            for p in cv.raster(Xf(), Ellipse(c, c, core, core)):
                cv.put(p[0], p[1], WHITE)
            for p in cv.raster(Xf(), Ring(c, c, core, core + 1.2)):
                cv.put(p[0], p[1], B[5])
        for k in range(8):
            a = math.radians(k * 45 + (0 if f < 3 else 12))
            length = ray_long if k % 2 == 0 else ray_short
            start = int(core) + (0 if f < 3 else 3)
            for d in range(start, start + length):
                x = int(round(c + math.cos(a) * d - 0.5))
                y = int(round(c + math.sin(a) * d - 0.5))
                if not (0 <= x < 32 and 0 <= y < 32):
                    continue
                if f >= 3 and (d // 2) % 2 == 1:
                    continue                               # the rays break into streaks
                frac = (d - start) / max(1, length)
                col = WHITE if frac < 0.3 else (S[2] if frac < 0.55 else (B[5] if frac < 0.8 else B[4]))
                cv.put(x, y, col)
                if k % 2 == 0 and frac < 0.5 and f in (1, 2):   # the long rays are two pixels wide near the core
                    nx, ny = int(round(-math.sin(a))), int(round(math.cos(a)))
                    cv.put(x + nx, y + ny, B[5] if frac < 0.3 else B[4])
        if f >= 2:                                        # sparks flying off between the rays
            for k in range(10):
                a = math.radians(22.5 + k * 36 + f * 7)
                d = 5 + f * 2.6 + (k % 3)
                x, y = int(round(c + math.cos(a) * d - 0.5)), int(round(c + math.sin(a) * d - 0.5))
                x2, y2 = int(round(c + math.cos(a) * (d + 1.5) - 0.5)), int(round(c + math.sin(a) * (d + 1.5) - 0.5))
                for (px, py, col) in ((x, y, B[4] if f < 4 else B[3]), (x2, y2, S[2] if f < 4 else A[3])):
                    if 0 <= px < 32 and 0 <= py < 32:
                        cv.put(px, py, col)
        if f == 2:                                        # a ring of brass going out
            for p in cv.raster(Xf(), Ring(c, c, 9.0, 10.2)):
                ang = math.atan2(p[1] + 0.5 - c, p[0] + 0.5 - c)
                if int((ang + math.pi) / (math.pi / 8)) % 2 == 0:
                    cv.put(p[0], p[1], B[4])
        out.append(img(cv, 32, 32))
    return out


# ================================================================================================
# Buff icons (16x16)
# ================================================================================================
def small_wrench(cv, origin=(2.6, 13.4)):
    rod(cv, origin, -45.0, 9.0, lambda t: (1.6, "copper", 1, 3) if t < 1.6 else ((1.4, "tar", 1, 2) if t < 5.0 else (1.0, "iron", 2, 4)),
        lambda t, u, col: (T[0] if 1.6 <= t < 5.0 and int(t) % 2 == 0 else (I[4] if t >= 5.0 and u < -0.2 else None)))
    xf = Xf.pose(-45.0, (0.0, 0.0), origin)
    jaw = cv.part(xf, Ellipse(10.4, 0.0, 2.9, 2.8), "iron", dome(9.4, -1.6, 3.8, lo=1, hi=4, gain=1.3), rust=0.0)
    for q in cv.raster(xf, Poly([(10.6, -0.9), (14.5, -2.0), (14.5, 1.8), (10.6, 0.9)])):
        cv.px.pop(q, None)
    for q in edge_of({q for q in cv.raster(xf, Ellipse(10.4, 0.0, 2.9, 2.8)) if q in cv.px}):
        cv.put(q[0], q[1], I[0])
    return xf


def riposte_icon():
    cv = Canvas()
    xf = small_wrench(cv)
    cx, cy = P(xf, (13.4, 0.0))
    for (dx, dy, col) in ((0, 0, WHITE), (1, 0, B[5]), (-1, 0, B[5]), (0, 1, B[5]), (0, -1, B[5]), (2, 0, B[4]), (0, -2, B[4]),
                          (-2, 0, B[4]), (0, 2, B[4]), (1, -1, S[2]), (-1, 1, S[2])):
        cv.put(cx + dx, cy + dy, col)
    return img_fit(cv, 16, 16, "riposte icon")


def cooldown_icon():
    cv = Canvas()
    small_wrench(cv)
    for p in cv.raster(Xf(), Ring(8.0, 8.0, 5.6, 7.0)):    # a turning arrow round it (aether: friendly)
        ang = math.degrees(math.atan2(p[1] + 0.5 - 8.0, p[0] + 0.5 - 8.0))
        if -150.0 < ang < 120.0:
            cv.put(p[0], p[1], A[2] if ang < 0 else A[1])
    for (x, y) in ((12, 13), (13, 13), (13, 12), (11, 14)):
        cv.put(x, y, A[3])                                 # the arrow's head
    return img_fit(cv, 16, 16, "cooldown icon")


# ================================================================================================
# Tarmancer: a claw of tar
# ================================================================================================
def tarmancer():
    """A claw of tar (user-set): a forearm of tar from the bottom left, a hand, three hooked talons fanning to the top
    right, wet highlights, an aether gem in the back of the hand (friendly: the summoning focus), a drip off the wrist."""
    px, z = {}, {}
    arm = tube(px, [(1.5, 20.5), (5.5, 16.2), (9.4, 12.6)], 2.7, 3.3, TAR_BODY, 0, zbuf=z, gloss=TAR_GLOSS)
    hand = ball(px, (11.4, 10.4), 4.0, 3.6, TAR_BODY, 1, zbuf=z, gloss=TAR_GLOSS)
    region = arm | hand
    for k, (a, m, b) in enumerate((((10.0, 8.4), (10.2, 3.2), (14.6, 0.9)), ((12.8, 8.6), (16.8, 4.4), (20.6, 5.2)),
                                   ((13.4, 11.8), (18.0, 10.8), (20.4, 14.2)))):
        region |= tube(px, curve(a, m, b), 2.1, 0.6, TAR_BODY, 2 + k, zbuf=z, gloss=TAR_GLOSS)
    outline(px, region, T[0], T[1])
    for (x, y, col) in ((11, 10, A[3]), (12, 10, A[2]), (11, 11, A[2]), (12, 11, A[1]), (10, 11, A[1]), (13, 11, A[0]),
                        (11, 12, A[0]), (12, 12, A[0]), (11, 9, A[1]), (12, 9, A[1]), (10, 10, A[1]), (13, 10, A[1])):
        px[(x, y)] = col
    px[(11, 10)] = WHITE
    for (x, y, col) in ((7, 15, T[2]), (7, 16, T[2]), (7, 17, T[3]), (6, 17, T[0]), (8, 17, T[0]), (7, 18, T[0])):
        px[(x, y)] = col
    cv = to_canvas(px, glow={(11, 10), (12, 10), (11, 11)})
    despeckle(cv)
    return img(cv, 22, 22)


# ================================================================================================
# The tar slime minion (facing right): a friendly blob with aether eyes, a brass cog in it
# ================================================================================================
SLIME_W, SLIME_H = 18, 14


def slime(w, h, mouth=False, wings=0, lift=0):
    """A tar slime in an 18x14 cell, its bottom on row 13 (minus lift): a glossy dome lit by its own normal, two aether
    eyes on its front (right), a half-swallowed brass cog at the back. wings: 0 none, 1 up, 2 down (two little flaps of
    tar on its back while it flies); mouth: open on the front, a glob on its way out."""
    px, z = {}, {}
    cx, bottom = 9.0, 13.0 - lift
    rx, ry = w / 2.0, h
    dome_px = ball(px, (cx, bottom), rx, ry, TAR_BODY, 0, zbuf=z, gloss=TAR_GLOSS)
    for q in [q for q in dome_px if q[1] >= bottom]:
        del px[q]
    body = {q for q in dome_px if q[1] < bottom}
    if wings:
        wy = int(bottom - ry * 0.72)
        for side in (-1, 1):
            wx = int(cx + side * rx * 0.35)
            tip = (wx + side * 3, wy - (3 if wings == 1 else 0))
            mid = (wx + side * 2, wy - (2 if wings == 1 else 1))
            flap = tube(px, [(wx + 0.5, wy + 0.5), (mid[0] + 0.5, mid[1] + 0.5), (tip[0] + 0.5, tip[1] + 0.5)], 1.3, 0.6, TAR_BODY, -1, zbuf=z)
            body |= flap
    outline(px, body, T[0], T[1])
    gx, gy = int(cx - rx * 0.62), int(bottom - 3)
    for (x, y, col) in ((gx, gy, B[3]), (gx + 1, gy, B[2]), (gx, gy + 1, B[2]), (gx + 1, gy + 1, B[1]), (gx - 1, gy + 1, B[1]), (gx + 1, gy - 1, B[1])):
        if (x, y) in body and px.get((x, y)) != T[0]:
            px[(x, y)] = col
    ey, ex = int(bottom - ry * 0.55), int(cx + rx * 0.3)
    glow = set()
    for (x, y, col) in ((ex, ey, A[3]), (ex, ey + 1, A[1]), (ex + 3, ey, A[2]), (ex + 3, ey + 1, A[1])):
        if (x, y) in body:
            px[(x, y)] = col
            if col in (A[3], A[2]):
                glow.add((x, y))
    if mouth:
        my = int(bottom - ry * 0.25)
        for x in range(int(cx + rx * 0.35), int(cx + rx) + 1):
            if (x, my) in body:
                px[(x, my)] = T[0]
            if (x, my + 1) in body:
                px[(x, my + 1)] = T[1]
        tx = int(cx + rx) + 1
        for (x, y, col) in ((tx, my - 1, T[0]), (tx + 1, my - 1, T[0]), (tx, my, T[3]), (tx + 1, my, T[1]), (tx + 2, my, T[0]),
                            (tx, my + 1, T[0]), (tx + 1, my + 1, T[0])):
            if 0 <= x < SLIME_W:
                px[(x, y)] = col
    cv = to_canvas(px, glow)
    despeckle(cv)
    return img(cv, SLIME_W, SLIME_H)


def slime_frames():
    return [slime(15.0, 9.0), slime(16.0, 8.0), slime(12.0, 12.0), slime(15.0, 9.5, lift=0), slime(16.0, 9.0, mouth=True),
            slime(13.0, 9.0, wings=1, lift=2), slime(13.0, 9.0, wings=2, lift=1)]


def slime_buff_icon():
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    icon.alpha_composite(slime(16.0, 11.0).crop((1, 0, 17, 14)), (0, 1))
    return icon


# ================================================================================================
# Tar globs (pre-rendered headings: never rotated at runtime)
# ================================================================================================
def glob(heading_deg, size, cell, aether=True):
    """A flying glob of tar pointing along heading_deg (0 = right, clockwise): a fat head, a tapering tail, two drips
    breaking off. Built pointing right and placed by a transform (rasterised, never rotated as a bitmap); the gloss is
    lit in screen space from the top-left whatever the heading; an aether glint on the head (friendly)."""
    cv = Canvas()
    s = size
    c = (cell - 1) / 2.0
    xf = Xf.pose(heading_deg, (0.0, 0.0), (c + 0.5, c + 0.5))
    shape = Ellipse(1.4 * s, 0.0, 3.0 * s, 2.7 * s) | Poly([(1.2 * s, -2.3 * s), (1.2 * s, 2.3 * s), (-3.2 * s, 1.0 * s), (-6.0 * s, 0.3 * s), (-3.2 * s, -1.0 * s)])
    mask = cv.raster(xf, shape)
    for (lx, ly) in ((-6.6 * s, 1.6 * s), (-5.0 * s, -1.8 * s)):
        q = P(xf, (lx, ly))
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)) if s >= 1.3 else ((0, 0),):
            if (q[0] + dx, q[1] + dy) not in mask:
                cv.put(q[0] + dx, q[1] + dy, T[0] if (q[0] + q[1] + dx) % 2 else T[1])
    ed = edge_of(mask)
    for p in mask:
        cv.put(p[0], p[1], T[0] if p in ed else T[1])
    head = xf.fwd((1.4 * s, 0.0))
    for p in mask - ed:
        dx, dy = p[0] + 0.5 - (head[0] - 1.1 * s), p[1] + 0.5 - (head[1] - 1.1 * s)
        if dx * dx + dy * dy <= 1.4 * s * s:
            cv.put(p[0], p[1], T[4] if dx + dy < 0 else T[3])
        elif 0.9 * s < (p[0] + 0.5 - head[0]) + (p[1] + 0.5 - head[1]) < 2.6 * s:
            cv.put(p[0], p[1], T[2])
    if aether:
        q = (int(math.floor(head[0] - 0.8 * s)), int(math.floor(head[1] - 0.8 * s)))
        if q in mask:
            cv.put_glow(q[0], q[1], A[3])
    return img(cv, cell, cell)


def glob_frames(size, cell):
    return [glob(k * 22.5, size, cell) for k in range(16)]


# ================================================================================================
# Tar Bone Staff and its skull
# ================================================================================================
# The tyrant skull, hand-drawn (14 wide, facing right; letters of make_trashtr0m_loot.PIX: bone q r s u f, tar 0,
# aether D, teeth v): a deep T. rex skull, the orbit at the back with an aether ember in it, the antorbital opening full of
# tar, a row of teeth. The jaw has three poses (closed, half, open): the skull it shoots snaps its jaw as it flies.
SKULL_TOP = ("....q...........",
             "...qfq..........",
             "..qfuqqqqqq.....",
             ".qfu0uuuffuuqq..",
             "qfuDquu000uuuuq.",
             "qsuuqsu000suuuuq",
             "qssssuussssussuq",
             ".qvqvqvqvqvqvqq.")
SKULL_JAWS = ((".qrsssssssssq...",
               "..qqqqqqqqqq....",
               "................"),
              (".q000000000q....",
               ".qrsvsvsvsvq....",
               "..qqqqqqqqq....."),
              (".q00000000000q..",
               ".qr000000000q...",
               ".qrsvsvsvsq....."))
GLOW_LETTERS = set("ABCDZ")


def paint_map(px, rows, x0, y0, glow=None):
    pal = {"q": BN[0], "r": BN[1], "s": BN[2], "u": BN[3], "f": BN[4], "0": T[0], "v": S[2], "D": A[3], "C": A[2]}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal:
                px[(x0 + i, y0 + j)] = pal[ch]
                if glow is not None and ch in GLOW_LETTERS:
                    glow.add((x0 + i, y0 + j))


def tar_bone_staff():
    """A femur wrapped in bands of tar, the little tyrant skull on top of it (facing right, up the staff), tar running
    down from under the skull; 22x22, points to the top right (Item.staff)."""
    px, z = {}, {}
    bone = BN[1:]                                           # lit bone: Leather 1 deep shade up to the Brass 5 highlight
    knob = ball(px, (2.6, 19.4), 2.5, 2.3, bone, 1, lo=0, zbuf=z) | ball(px, (4.4, 20.4), 1.8, 1.6, bone, 1, lo=0, zbuf=z)
    head = ball(px, (10.6, 11.4), 2.3, 2.3, bone, 1, lo=0, zbuf=z)
    outline(px, knob | head, BN[0], BN[1])
    cv = Canvas()
    rod(cv, (3.4, 18.6), -45.0, 9.4, lambda t: (1.8, "bone", 3, 4),
        lambda t, u, col: (T[0] if int(t) in (2, 6) and abs(u) < 1.4 else (T[3] if int(t) in (3, 7) and u < -0.3 else
                                                                         (T[1] if int(t) in (3, 7) else None))))
    for q, col in cv.px.items():                            # the shaft (tar wrapped round it in two bands) between the ends
        if q not in knob and q not in head:
            px[q] = col
    glow = set()
    paint_map(px, SKULL_TOP + SKULL_JAWS[0][:2], 6, 1, glow)
    for (x, y, col) in ((11, 12, T[1]), (11, 13, T[1]), (11, 14, T[3]), (10, 14, T[0]), (12, 14, T[0]), (11, 15, T[0])):
        px[(x, y)] = col                                    # tar dripping down the bone
    cv = to_canvas(px, glow)
    despeckle(cv)
    return img_fit(cv, 22, 22, "Tar Bone Staff")


def skull_bolt_frames():
    out = []
    for jaw in SKULL_JAWS:
        px, glow = {}, set()
        paint_map(px, SKULL_TOP + jaw, 0, 0, glow)
        out.append(img(to_canvas(px, glow), 16, 11))
    return out


def blast_frames():
    """The bite's burst (40x40, 5 tiles across): an aether flash, then a ring of tar and bone shards flying out, then
    falling droplets."""
    out = []
    c = 19.5
    for f in range(6):
        cv = Canvas()
        r = (4.0, 9.0, 13.0, 16.0, 18.0, 19.0)[f]
        if f <= 1:
            for p in cv.raster(Xf(), Ellipse(c, c, 3.0 + f * 2.0, 3.0 + f * 2.0)):
                d = math.hypot(p[0] + 0.5 - c, p[1] + 0.5 - c)
                cv.put(p[0], p[1], WHITE if d < 1.6 + f else (A[3] if d < 3.0 + f * 1.5 else A[2]))
        if f >= 1:
            ring = cv.raster(Xf(), Ring(c, c, max(0.0, r - 3.2 + f * 0.3), r))
            for p in ring:
                ang = math.atan2(p[1] + 0.5 - c, p[0] + 0.5 - c)
                if f >= 3 and int((ang + math.pi) / (math.pi / 9)) % 2 == 1:
                    continue
                d = math.hypot(p[0] + 0.5 - c, p[1] + 0.5 - c)
                lit = math.cos(ang - math.radians(225.0)) > 0.3
                cv.put(p[0], p[1], T[0] if d > r - 0.9 else (T[3] if lit else T[1]))
        for k in range(8):                                 # bone shards tumbling out
            a = math.radians(k * 45 + 20)
            d = 3 + f * 3.2
            x, y = int(round(c + math.cos(a) * d - 0.5)), int(round(c + math.sin(a) * d - 0.5)) + (f * f) // 6
            if 1 <= f <= 4 and 0 <= x < 39 and 0 <= y < 39:
                cv.put(x, y, BN[4] if k % 2 else BN[3])
                cv.put(x + 1, y, BN[2])
        if f >= 4:                                         # droplets falling
            for k in range(10):
                a = math.radians(k * 36 + 10)
                d = r - 2 + (k % 3)
                x, y = int(round(c + math.cos(a) * d - 0.5)), int(round(c + math.sin(a) * d - 0.5)) + (f - 3) * 2
                if 0 <= x < 39 and 0 <= y < 39:
                    cv.put(x, y, T[1])
                    cv.put(x, y + 1, T[0])
        out.append(img(cv, 40, 40))
    return out


# ================================================================================================
# Tar-Shower: a polished-metal tar sprayer with a brass tank (nozzle to the right)
# ================================================================================================
def tar_shower():
    cv = Canvas()
    # the brass tank on top: a horizontal cylinder with riveted bands and a sight glass of tar
    hcyl(cv, 3, 15, 0, 5, "brass")
    for x in (5, 13):
        hcyl(cv, x, x, 0, 5, "brass", hi=2, ends=False)
    for x in range(7, 12):
        cv.put(x, 3, T[1] if x % 2 else T[2])              # the sight glass: tar inside
        cv.put(x, 2, T[3] if x == 8 else B[4])
    cv.put(4, 1, WHITE)
    for x in (4, 14):
        cv.put(x, 3, B[1])
    # the pump body of polished metal, a pressure gauge on it
    boxed(cv, 5, 18, 6, 10, "iron", 4, 3, 2)
    for x in range(6, 18):
        cv.put(x, 7, I[4] if x % 4 else S[2])              # polished: its lit top edge
    gauge = cv.part(Xf(), Ellipse(8.5, 8.5, 1.8, 1.8), "brass", flat(3), rust=0.0)
    cv.put(8, 8, S[2])
    cv.put(9, 8, S[1])
    cv.put(8, 9, S[1])
    cv.put(9, 9, I[0])                                     # the needle
    cv.put(13, 8, B[4])
    cv.put(16, 8, B[4])                                    # rivets
    # the hose from the tank's front down into the pump
    for (x, y, col) in ((16, 2, LE[0]), (17, 2, LE[1]), (17, 3, LE[1]), (18, 4, LE[1]), (18, 5, LE[0]), (17, 4, LE[0]), (16, 3, LE[0]), (17, 5, LE[0])):
        cv.put(x, y, col)
    # the barrel and the flared nozzle, tar on its lip
    hcyl(cv, 18, 23, 7, 10, "iron")
    for x in range(19, 23):
        cv.put(x, 8, I[4] if x % 3 else S[2])
    boxed(cv, 23, 25, 6, 11, "brass", 4, 3, 2)
    cv.put(25, 8, T[1])
    cv.put(25, 9, T[1])
    cv.put(24, 12, T[1])
    cv.put(24, 13, T[0])
    cv.put(23, 12, T[0])
    cv.put(25, 12, T[0])
    # the stock behind, a leather grip and an iron trigger under the pump
    boxed(cv, 0, 5, 7, 10, "leather", 2, 1, 1)
    for (x, y) in ((11, 11), (12, 12), (12, 11)):
        cv.put(x, y, I[1])
    grip = cv.part(Xf(), Poly([(6.5, 10.0), (10.5, 10.0), (9.5, 14.0), (5.5, 14.0)]), "leather", flat(1), rust=0.0)
    for q in grip:
        if (q[0] + q[1]) % 3 == 0:
            cv.put(q[0], q[1], LE[2] if q[0] < 8 else LE[0])
    despeckle(cv)
    return img(cv, 26, 14)


def spray_frames():
    """A burst of tar spray (12x12): a few droplets that grow and spread as it flies (frame = age)."""
    out = []
    for f in range(5):
        cv = Canvas()
        n = 2 + f
        for k in range(n):
            a = math.radians(k * 137.5 + f * 21)
            d = f * 1.15 * (0.5 + (k % 3) * 0.3)
            r = 1.1 + f * 0.45 - (k % 2) * 0.35
            cx, cy = 5.5 + math.cos(a) * d, 5.5 + math.sin(a) * d
            mask = cv.raster(Xf(), Ellipse(cx, cy, r, r))
            ed = edge_of(mask)
            for p in mask:
                cv.put(p[0], p[1], T[0] if p in ed else T[1])
            if r > 1.3:
                q = (int(cx - r * 0.4), int(cy - r * 0.4))
                if q in mask and q not in ed:
                    cv.put(q[0], q[1], T[3] if f < 3 else T[2])
        out.append(img(cv, 12, 12))
    return out


STAIN_W, STAIN_H = 48, 6


def stain_frames():
    """The 6-tile stain (48x6, the bottom row on the ground): flat glossy tar, bubbles swelling and popping, a ring of
    gloss sliding across it."""
    out = []
    for k in range(4):
        cv = Canvas()
        pin = cv.part(Xf(), Ellipse(24.0, 5.0, 23.5, 2.6), "tar", dome(16.0, 3.0, 24.0, lo=1, hi=2, gain=1.1, fixed=True), rust=0.0)
        x0 = 8 + k * 6
        for x in range(x0, x0 + 8):
            if (x, 3) in pin:
                cv.put(x, 3, T[3] if x % 3 else T[4])
        for j, bx in enumerate((10, 25, 38)):
            ph = (k + j * 2) % 4
            if ph < 2:
                r = 0.9 + ph * 0.8
                bub = cv.part(Xf(), Ellipse(bx, 4.4 - r * 0.5, r + 0.3, r), "tar", flat(2), rust=0.0)
                if bub:
                    cv.put(bx - 1, int(4.0 - r), T[4])
            elif ph == 2:
                cv.put(bx - 1, 3, T[2])
                cv.put(bx + 1, 3, T[2])
        out.append(img(cv, STAIN_W, STAIN_H))
    return out


def charge_frames():
    """The ball of tar swelling at the nozzle (16x16): five sizes wobbling, then the full charge with an aether rim."""
    out = []
    for f, r in enumerate((2.0, 3.0, 4.0, 5.0, 6.0, 6.6)):
        px = {}
        c = (7.5, 7.5)
        region = ball(px, c, r * (1.05 if f % 2 else 0.97), r * (0.95 if f % 2 else 1.03), TAR_BODY, gloss=TAR_GLOSS)
        ed = outline(px, region, T[0], T[1])
        glow = set()
        if f == 5:
            for q in ed:
                ang = math.atan2(q[1] + 0.5 - c[1], q[0] + 0.5 - c[0])
                px[q] = A[2] if math.cos(ang - math.radians(225.0)) > 0 else A[1]
                glow.add(q)
        out.append(img(to_canvas(px, glow), 16, 16))
    return out


# ================================================================================================
def build():
    return {
        "MetalWrench.png": metal_wrench(),
        "MetalClash.png": vertical(clash_frames()),
        "WrenchRiposteBuff.png": riposte_icon(),
        "WrenchParryCooldown.png": cooldown_icon(),
        "Tarmancer.png": tarmancer(),
        "TarSlimeMinion.png": vertical(slime_frames()),
        "TarSlimeBuff.png": slime_buff_icon(),
        "TarSlimeShot.png": vertical(glob_frames(0.85, 10)),
        "TarBoneStaff.png": tar_bone_staff(),
        "TyrantSkullBolt.png": vertical(skull_bolt_frames()),
        "TyrantSkullBlast.png": vertical(blast_frames()),
        "TarShower.png": tar_shower(),
        "TarSpray.png": vertical(spray_frames()),
        "TarShowerGlob.png": vertical(glob_frames(0.95, 10)),
        "TarShowerBigGlob.png": vertical(glob_frames(1.5, 16)),
        "TarStain.png": vertical(stain_frames()),
        "TarShowerCharge.png": vertical(charge_frames()),
    }


def preview(path):
    sheets = build()
    row_h = 0
    tiles = []
    for name, im in sheets.items():
        tiles.append((name, im))
    W = 900
    x = y = 8
    out = Image.new("RGBA", (W, 1400), (36, 40, 48, 255))
    light = Image.new("RGBA", (W, 1400), (150, 180, 210, 255))
    for name, im in tiles:
        big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        if x + big.width > W - 8:
            x, y = 8, y + row_h + 8
            row_h = 0
        out.alpha_composite(big, (x, y))
        light.alpha_composite(big, (x, y))
        x += big.width + 10
        row_h = max(row_h, big.height)
    h = y + row_h + 8
    both = Image.new("RGBA", (W * 2, h))
    both.alpha_composite(out.crop((0, 0, W, h)), (0, 0))
    both.alpha_composite(light.crop((0, 0, W, h)), (W, 0))
    both.save(path)
    print("preview", path, both.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        for name, im in build().items():
            export(im, name)
