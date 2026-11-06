"""Source for the Junkyard's tar and polished-metal weapons of 2026-10-30 (D4; the user named them, so Metal Slug-level
detail at their sizes). Run from the repo root:

    python -P art/junkyard/make_tar_weapons.py [--preview FILE]

Drawn at 1x and exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left, every part outlined in
ramp 0 of its own material (rig.py parts, the rod rasteriser of art/bosses/trashtr0m/make_trashtr0m_loot.py, pixel
details on top). Friendly effects use Brass, Steam and Aether (D3 colour coding); tar keeps its own ramp (rig.RAMP["tar"]),
the bone Tar Tyrant's (rig.RAMP["bone"]). Outputs (Content/Junkyard/Weapons/):

    MetalWrench.png             68x68   item and swing (redrawn twice on 2026-11-03: "a big thick metal wrench" at the
                                        Blade of Grass's 1.4.4 sprite size, then the user's own reference image): a pipe
                                        wrench of polished steel, a long silver handle with a hanging hole, the frame and
                                        its heel jaw, the knurled nut, the hook jaw; points to the top right like every
                                        sword (the reference points top-left: mirrored)
    MetalClash.png              64x394  6 frames (stride 66): the clash, a starburst of brass and white with sparks flying
    WrenchRiposteBuff.png       32x32   buff icon: the wrench with a spark at its jaw (the empowered riposte)
    WrenchParryCooldown.png     32x32   debuff icon: the wrench under a turning arrow (the parry is cooling down)
    Tarmancer.png               44x44   item: a claw of tar (user-set), three glossy talons, an aether gem in its back
    TarSlimeMinion_Wings.png    64x50   2 frames (stride 26) of 64x24: the minion's tar wings, up and down, drawn behind
                                        it in flight (the minion itself draws the Living Tar's sheet since 2026-11-03)
    TarSlimeBuff.png            32x32   buff icon: the Living Tar
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
    TarWhip.png                 32x32   item (2026-11-03): the Tar Whip coiled, a bone handle, tar-stained vertebrae, a fang
    TarWhipProjectile.png       14x94   the lash, segments facing down, the joint at (7, 8) of each: the bone handle (24),
                                        three vertebrae (16 each), the tyrant's fang at the tip (22)
    TarWhipDebuff.png           32x32   the tag's icon: a vertebra dipped in tar
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, HERE)                                    # make_junkyard_loot (the Living Tar), run with -P
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Ring, Capsule, Union, Canvas, box, flat, dome, cyl, line  # noqa: E402
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
# Metal Wrench: a pipe wrench from the user's reference image (2026-11-03, second request). Earlier looks, kept in
# art/junkyard/previous/: the thin one with a cog pommel (make_tar_weapons_2026-10-30.py, "it looks like a robot arm")
# and the thick open-end wrench of the same morning (make_tar_weapons_2026-11-03.py).
# ================================================================================================
# 34x34 art (68x68 in game, the Blade of Grass's 1.4.4 sprite size): a long silver handle with a hanging hole at the
# bottom left (where the hand holds it in a swing), the frame and its heel jaw, the knurled adjusting nut on the hook
# jaw's shank, the hook jaw across the head, the mouth opening to the top left (the reference points top-left and opens
# right: mirrored). It is built in its own space, u along the wrench from the handle end and v across it, and placed
# at -45 degrees, so every edge is a clean 45-degree staircase. The top-left light falls on the wrench from exactly -v
# (screen (-1, -1) is local (0, -1) at this angle).
WRENCH_SIZE = 34
WRENCH_START = (3.4, 33.1)                                  # screen point of local (0, 0)
HANDLE_U0, HANDLE_U1, HANDLE_W0, HANDLE_W1 = 0.6, 20.5, 2.2, 3.0   # the handle: its end, the frame, half-widths there
HOLE_U = 2.7                                                # the hanging hole near its end
FRAME_U0, FRAME_U1, FRAME_W = 19.5, 28.0, 5.0               # the frame the heel jaw is part of
HEEL_U0, HEEL_V = 24.0, -8.6                                # the heel jaw: from here to the frame's top, out to HEEL_V (-v)
NUT_U0, NUT_U1, NUT_V0, NUT_V1 = 28.0, 31.6, -1.4, 5.6      # the knurled adjusting nut round the hook jaw's shank
SHANK_V0, SHANK_V1 = 1.0, 4.8                               # the hook jaw's shank, along the +v side
HOOK_U0, HOOK_U1, HOOK_V = 32.0, 36.4, -9.2                 # the hook jaw: across the head, its teeth facing the heel
GRIP_HAND_U = 6.5                                           # where the hand holds it (MetalWrenchGuard.GripInset)


def wrench_xf(scale=1.0, start=WRENCH_START):
    """Local (u, v) -> screen: u up and to the right, v down and to the right; `scale` shrinks it for the icons."""
    k = math.sqrt(0.5) * scale
    return Xf(k, k, -k, k, start[0], start[1])


def wrench_shapes():
    """Three parts: the hook jaw with its shank (behind), the handle with the frame and its heel jaw, the nut (in front)."""
    body = Union(Poly([(HANDLE_U0 + 1.6, -HANDLE_W0), (HANDLE_U1, -HANDLE_W1), (HANDLE_U1, HANDLE_W1), (HANDLE_U0 + 1.6, HANDLE_W0)]),
                 Ellipse(HANDLE_U0 + 1.6, 0.0, 1.6, HANDLE_W0),
                 Poly([(FRAME_U0, -HANDLE_W1), (FRAME_U0 + 3.0, -FRAME_W), (FRAME_U1, -FRAME_W), (FRAME_U1, FRAME_W),
                       (FRAME_U0, HANDLE_W1 + 0.4)]),
                 box(HEEL_U0, HEEL_V, FRAME_U1, -FRAME_W + 0.5)) - Ellipse(HOLE_U, 0.0, 0.6, 0.6)
    hook = Union(box(FRAME_U0 + 1.0, SHANK_V0, HOOK_U1, SHANK_V1),
                 box(HOOK_U0, HOOK_V + 0.6, HOOK_U1, SHANK_V1),
                 Poly([(HOOK_U0 - 0.9, HOOK_V), (HOOK_U1, HOOK_V), (HOOK_U1, HOOK_V + 2.0), (HOOK_U0, HOOK_V + 2.0)]))
    nut = box(NUT_U0, NUT_V0, NUT_U1, NUT_V1)
    return body, hook, nut


def teeth(cv, xf, inner, u, v0, v1, facing):
    """Teeth along a jaw face at u (a dark notch every other pixel), facing +u (1) or -u (-1)."""
    for k, v in enumerate([v0 + 0.5 + n for n in range(int(v1 - v0))]):
        q = P(xf, (u - 0.6 * facing, v))
        if q in inner and k % 2 == 0:
            cv.put(q[0], q[1], I[1])


def wrench_parts(scale=1.0, start=WRENCH_START, detail=True):
    """The pipe wrench (the user's reference, 2026-11-03) as a canvas: the hook jaw and its shank behind, the handle with
    the frame and its heel jaw, the knurled nut in front; polished steel lit from -v (the top-left)."""
    xf = wrench_xf(scale, start)
    cv = Canvas()
    body, hook, nut = wrench_shapes()

    def body_shade(i):
        u, v = i.lx, i.ly
        if math.hypot(u - HOLE_U, v) < 1.3:
            return 3 if v > 0.2 else 2                      # round the hole: its far wall catches the light
        if u < FRAME_U0:                                    # the handle: a lit edge, the silver face, the shadow edge
            w = HANDLE_W0 + (HANDLE_W1 - HANDLE_W0) * max(0.0, min(1.0, (u - HANDLE_U0) / (HANDLE_U1 - HANDLE_U0)))
            return 4 if v < 0.4 else (3 if v < w - 0.9 else 2)
        if v < -FRAME_W + 0.5:                              # the heel jaw
            return 4 if u < HEEL_U0 + 1.2 else 3
        return 4 if v < 0.0 else (3 if v < 2.4 else 2)

    def hook_shade(i):
        if i.ly < 0.0:
            return 4
        return 3 if i.ly < 2.6 else 2

    kin = cv.part(xf, hook, "iron", hook_shade, rust=0.0)
    bin_ = cv.part(xf, body, "iron", body_shade, rust=0.0)
    nin = cv.part(xf, nut, "iron", lambda i: 3 if int(math.floor(i.ly + 1.0)) % 2 == 0 else 2, rust=0.0)   # the knurling
    despeckle(cv)                                           # before the details: a glint is one pixel on purpose
    if detail:
        teeth(cv, xf, bin_, FRAME_U1, HEEL_V, -FRAME_W + 0.5, 1)
        teeth(cv, xf, kin, HOOK_U0, HOOK_V + 0.6, NUT_V0, -1)
        for (u, v) in ((u_, -1.5) for u_ in range(5, 19)):  # a steam-white shine along the handle's lit face
            q = P(xf, (u, v))
            if q in bin_:
                cv.put(q[0], q[1], S[2])
        for (u, v) in ((12.0, -1.7), (HOOK_U0 + 1.4, HOOK_V + 0.6), (FRAME_U0 + 4.0, -FRAME_W + 0.6), (HEEL_U0 + 0.6, HEEL_V + 0.6)):
            q = P(xf, (u, v))                               # white glints on the polished lit edges
            if q in bin_ or q in kin:
                cv.put(q[0], q[1], WHITE)
    del nin
    return cv


def metal_wrench():
    return img(wrench_parts(), WRENCH_SIZE, WRENCH_SIZE)


def wrench_grip_inset():
    """Game px from the bottom-left corner to the hand on the grip, along both axes (MetalWrenchGuard.GripInset)."""
    x, y = wrench_xf().fwd((GRIP_HAND_U, 0.0))
    return round(x * 2), round((WRENCH_SIZE - y) * 2)


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
def small_wrench(cv):
    """The icons' pipe wrench (16x16) in integer bands along the diagonal x + y = 16 (s across it, t along it), since a
    scaled-down copy of the big one loses its jaws: the silver handle lit on its top-left line, the frame with the heel
    jaw, the hook jaw across the head, the mouth open to the top left. Returns the hook's tip (the riposte's spark)."""
    mask, dark = set(), set()
    for y in range(16):
        for x in range(16):
            s_, t_ = x + y + 1.0 - 16.0, x - y
            handle = abs(s_) <= 2.0 and -13.0 <= t_ <= 2.0
            frame = -3.0 <= s_ <= 3.0 and 1.0 <= t_ <= 5.0
            heel = -5.0 <= s_ <= -3.0 and 3.0 <= t_ <= 5.0
            hook = -5.0 <= s_ <= 3.0 and 8.0 <= t_ <= 10.0
            shank = 1.0 <= s_ <= 3.0 and 4.0 <= t_ <= 10.0
            if handle or frame or heel or hook or shank:
                mask.add((x, y))
                if shank and 5.0 <= t_ <= 7.0:
                    dark.add((x, y))                         # the knurled nut
    edge = edge_of(mask)
    for (x, y) in mask:
        s_ = x + y + 1.0 - 16.0
        if (x, y) in edge:
            col = I[0]
        elif (x, y) in dark:
            col = I[2] if (x + y) % 2 else I[3]
        else:
            col = S[2] if s_ < -1.5 else (I[4] if s_ < 0.5 else I[3])
        cv.put(x, y, col)
    return (11, 3)


def riposte_icon():
    cv = Canvas()
    cx, cy = small_wrench(cv)
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
# The tar slime minion: since 2026-11-03 it IS the Living Tar (user: "look exactly like the tar slime enemies"); the
# projectile draws Content/Junkyard/NPCs/LivingTar.png itself. Only its flight wings and the buff icon are drawn here.
# ================================================================================================
WING_W, WING_H = 32, 12                                     # the Living Tar's 16x12 cell sits at (8, 6) in a wing cell


def slime_wings():
    """Two bat-like flaps of tar on the slime's upper flanks (drawn behind it while it flies, like vanilla's Baby
    Slime's): frame 0 raised, frame 1 lowered. Each is a membrane with a scalloped trailing edge, built pointing out
    from its root and turned about it (rasterised, never rotated as a bitmap); glossy on the lit top edge, ramp-0
    outline, the root hidden behind the body."""
    out = []
    flap = Poly([(0.0, -2.6), (3.6, -4.4), (9.8, -5.0), (9.0, -2.4), (7.4, -1.0), (6.4, 0.6), (4.6, 0.8), (3.4, 2.4), (1.6, 1.8), (0.0, 2.6)])
    for f in range(2):
        cv = Canvas()
        for side in (-1, 1):
            root = (16.0 + side * 3.5, 8.0)
            angle = (-18.0 if f == 0 else 16.0) * side
            xf = Xf.pose(angle, (0.0, 0.0), root) if side > 0 else Xf(-1.0, 0.0, 0.0, 1.0, root[0], root[1]).then(Xf.pose(-angle))
            cv.part(xf, flap, "tar", lambda i: 3 if i.ly < -3.0 else (2 if i.ly < -0.4 else 1), rust=0.0)
        despeckle(cv)
        out.append(img(cv, WING_W, WING_H))
    return out


def slime_buff_icon():
    """The Living Tar's first frame (its own pixels) on the 16x16 icon."""
    import make_junkyard_loot
    body = make_junkyard_loot.living_tar_frames()[0]
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    icon.alpha_composite(body, (0, 4))
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
# Tar Whip (2026-11-03): the Spinal Tap's spine dipped in condensed tar, a tyrant's fang for a tip
# ================================================================================================
# TarWhipProjectile.png, 7 px wide at 1x (14 in game), segments facing down with their joint at (3.5, 4): the handle
# (12 rows), three vertebrae (8 rows each), the fang (11 rows). Bone is Tar Tyrant's tar-stained bone (rig.RAMP["bone"]).
WHIP_W = 7
WHIP_HANDLE_H, WHIP_SEG_H, WHIP_TIP_H = 12, 8, 11
WHIP_JOINT = (3.5, 4.0)


def whip_handle():
    """A bone handle wrapped in two bands of tar, the knob of the femur at its butt (above the hand)."""
    px, z = {}, {}
    bone = BN[1:]
    knob = ball(px, (3.5, 1.8), 2.6, 1.8, bone, 1, lo=0, zbuf=z)
    shaft = tube(px, [(3.5, 2.5), (3.5, 11.2)], 1.6, 1.4, bone, 0, lo=0, zbuf=z)
    region = knob | shaft
    outline(px, region, BN[0], BN[1])
    for y in (5, 8):                                         # the tar wraps
        for x in range(1, 6):
            if (x, y) in region and (x, y) not in edge_of(region):
                px[(x, y)] = T[3] if x == 2 else T[1]
    cv = to_canvas(px)
    return img(cv, WHIP_W, WHIP_HANDLE_H)


def whip_vertebra(kind):
    """A vertebra round the joint: its body (an oval of bone lit from the top-left), two little transverse processes, the
    lower half coated in glossy tar with a drip (kind 0-2 move the drip and the gloss, so the spine doesn't repeat)."""
    px, z = {}, {}
    bone = BN[1:]
    c = (3.5, 4.0)
    body = ball(px, c, 2.4, 2.0, bone, 1, lo=0, zbuf=z)
    nubs = set()
    for side in (-1, 1):
        nubs |= ball(px, (c[0] + side * 2.6, c[1] + 0.4), 0.9, 0.7, bone, 0, lo=0, zbuf=z)
    region = body | nubs
    outline(px, region, BN[0], BN[1])
    inner = region - edge_of(region)
    for (x, y) in inner:
        if y >= 5:
            px[(x, y)] = T[1] if (x + kind) % 3 else T[2]     # the tar coat on its lower half
    gx = (2, 4, 3)[kind]
    if (gx, 5) in inner:
        px[(gx, 5)] = T[3]                                   # the coat's gloss
    dx = (4, 2, 5)[kind]
    if (dx, 6) in region:                                    # the drip hanging off it
        px[(dx, 7)] = T[0]
    cv = to_canvas(px)
    return img(cv, WHIP_W, WHIP_SEG_H)


def whip_fang():
    """The tip: a tyrant's fang hanging from a last knot of tar, curved a little to the side, a cream glint on its edge."""
    px, z = {}, {}
    knot = ball(px, (3.5, 3.8), 2.3, 1.9, TAR_BODY, 1, zbuf=z, gloss=TAR_GLOSS)
    tooth = tube(px, curve((3.5, 5.0), (2.4, 8.0), (3.6, 10.6), n=6), 1.8, 0.4, BN[1:], 0, lo=0, zbuf=z)
    outline(px, knot | tooth, T[0], T[1])
    for (x, y) in ((2, 6), (2, 7)):
        if (x, y) in tooth:
            px[(x, y)] = BN[4]                               # the glint along its lit edge
    cv = to_canvas(px)
    return img(cv, WHIP_W, WHIP_TIP_H)


def whip_sheet():
    parts = [whip_handle()] + [whip_vertebra(k) for k in range(3)] + [whip_fang()]
    out = Image.new("RGBA", (WHIP_W, sum(p.height for p in parts)), (0, 0, 0, 0))
    y = 0
    for p in parts:
        out.alpha_composite(p, (0, y))
        y += p.height
    return out


def tar_whip_item():
    """The inventory sprite (16x16): the spine coiled once in a loop (a tube of bone, banded with tar at every vertebra),
    the bone handle at the bottom left, the fang hanging out of the loop at the top right."""
    px, z = {}, {}
    bone = BN[1:]
    loop = [(9.0 + math.cos(math.radians(a)) * 4.4, 7.2 - math.sin(math.radians(a)) * 3.8) for a in range(200, -161, -30)]
    region = tube(px, loop, 1.5, 1.3, bone, 2, lo=0, zbuf=z)
    region |= tube(px, [(1.6, 14.4), (3.4, 12.6), (5.4, 10.6)], 1.8, 1.5, bone, 3, lo=0, zbuf=z)
    region |= tube(px, curve((13.0, 5.4), (15.0, 3.4), (14.0, 1.2), n=4), 1.2, 0.5, bone, 4, lo=0, zbuf=z)
    outline(px, region, BN[0], BN[1])
    inner = region - edge_of(region)
    for k, (x, y) in enumerate(loop):                        # tar between the vertebrae
        q = (int(math.floor(x)), int(math.floor(y)))
        if k % 2 == 1 and q in inner:
            px[q] = T[1]
            for n in ((q[0] + 1, q[1]), (q[0], q[1] + 1)):
                if n in inner:
                    px[n] = T[0]
    for q in ((2, 13), (4, 11)):                             # tar wraps on the handle
        if q in inner:
            px[q] = T[1]
    cv = to_canvas(px)
    despeckle(cv)
    return img_fit(cv, 16, 16, "Tar Whip")


def tar_whip_tag_icon():
    """The tag's icon (16x16): one vertebra drawn big, its lower half in glossy tar, a drip falling off."""
    px, z = {}, {}
    bone = BN[1:]
    body = ball(px, (8.0, 7.0), 5.0, 4.0, bone, 1, lo=0, zbuf=z)
    nubs = ball(px, (2.4, 7.8), 1.8, 1.3, bone, 0, lo=0, zbuf=z) | ball(px, (13.6, 7.8), 1.8, 1.3, bone, 0, lo=0, zbuf=z)
    spine = tube(px, [(8.0, 3.0), (8.0, 0.8)], 1.2, 0.8, bone, 2, lo=0, zbuf=z)
    region = body | nubs | spine
    outline(px, region, BN[0], BN[1])
    inner = region - edge_of(region)
    for (x, y) in inner:
        if y >= 8:
            px[(x, y)] = T[2] if (x, y - 1) not in inner or y == 8 else T[1]
    for (x, y) in ((5, 8), (6, 8)):
        if (x, y) in inner:
            px[(x, y)] = T[3]
    for (x, y, col) in ((10, 11, T[1]), (10, 12, T[1]), (10, 13, T[0])):   # a drip hanging off the coat
        px[(x, y)] = col
    cv = to_canvas(px)
    despeckle(cv)
    return img(cv, 16, 16)


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
        "TarSlimeMinion_Wings.png": vertical(slime_wings()),
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
        "TarWhip.png": tar_whip_item(),
        "TarWhipProjectile.png": whip_sheet(),
        "TarWhipDebuff.png": tar_whip_tag_icon(),
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
