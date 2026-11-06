"""Shared parts for Old Brass Town's gunslinger robots (the Brass Bandit and the Sheriff), 2026-11-04. Imported by
make_bandit_art.py and make_sheriff_art.py; not run on its own.

Rig space as in art/bosses/trashtr0m/rig.py: 1 px = one art pixel, y down, the origin on the ground under the hips,
facing left. Limbs are capsules lit across their real axis with the light's turn snapped to 22.5 degrees (D4 rule 17:
stable while they sway); bodies and hats are lit in their own space (fixed=True). Every part outlines itself with its
own ramp's darkest shade (D4 rule 3).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, face, ik, level, lit  # noqa: E402,F401

I, B, C, E, S, LE = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "leather"))


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def despeckle(cv):
    """Lone pixels (no 4-neighbour of the same colour, all four filled) take their neighbours' majority (D4 rule 4)."""
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


def limb_shade(a, b, r, lo, hi, gain=1.4, step=22.5):
    """A cylinder lit across its real axis, the light's turn snapped to `step` degrees (stable while it sways)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln
    sa = round(math.atan2(dy, dx) / math.radians(step)) * math.radians(step)
    snx, sny = -math.sin(sa), math.cos(sa)

    def shade(i):
        t = max(-1.0, min(1.0, ((i.lx - a[0]) * nx + (i.ly - a[1]) * ny) / r))
        return level(lit(t * snx, t * sny, math.sqrt(1.0 - t * t)), lo, hi, gain)
    return shade


def limb(cv, a, b, r, ramp, depth, lo=1, hi=3, outline=True):
    """A capsule limb. On the far plane (depth > 0) it is one flat tone under its outline: a far limb is small and dark,
    and its swinging light bands flashed (check_flicker, the Brass Bandit's walk, 2026-11-04)."""
    if depth > 0:
        return cv.part(Xf(), Capsule(a, b, r), ramp, flat(max(lo, hi - 1), bevel=False), outline=outline, depth=depth, rust=0.0)
    return cv.part(Xf(), Capsule(a, b, r), ramp, limb_shade(a, b, r, lo, hi), outline=outline, depth=depth, rust=0.0)


def leg(cv, hip, foot_x, lift, depth, thigh, shin, r_thigh=1.6, r_shin=1.4, trousers="iron", boot="leather", spur=True,
        knee_ramp="brass"):
    """A leg from the hip to a boot on the ground (lifted `lift` px): an iron piston thigh and shin, a brass knee joint, a
    leather riding boot with a brass spur at the heel. Returns the knee."""
    ankle = (foot_x, -1.6 - lift)
    knee, ankle = ik(hip, ankle, thigh, shin, -1)                # knees forward (left)
    limb(cv, hip, knee, r_thigh, trousers, depth, lo=1, hi=4 if trousers == "iron" else 3)
    limb(cv, knee, ankle, r_shin, trousers, depth, lo=1, hi=4 if trousers == "iron" else 3)
    ax, ay = ankle
    bh = BOOT_HEIGHT
    boot_pts = [(ax + 1.6, ay - bh), (ax - 1.0, ay - bh), (ax - 1.4, ay + 0.2), (ax - 3.2, ay + 0.8), (ax - 3.2, ay + 1.7), (ax + 1.8, ay + 1.7)]
    binner = cv.part(Xf(), Poly(boot_pts), boot, face((-0.5, -0.5, 0.7), lo=1, hi=2, fixed=True), depth=depth, rust=0.0)
    for (dx, dy) in ((0.0, -bh + 0.6),):                         # the boot's turned-down cuff, lit
        q = P(Xf(), (ax - 0.6 + dx, ay + dy))
        if q in binner:
            cv.put(q[0], q[1], LE[2])
            cv.put(q[0] + 1, q[1], LE[2])
    if spur:
        s = P(Xf(), (ax + 2.4, ay + 0.6))
        cv.put(s[0], s[1], B[max(1, 4 - depth)])
        cv.put(s[0] + 1, s[1], B[max(1, 3 - depth)])
    if depth == 0:                                                  # the knee joint (near plane only: on the far one a moving
        q = P(Xf(), knee)                                           # one-pixel bolt reads as flicker, D4 rule 17)
        cv.put(q[0], q[1], RAMP[knee_ramp][4])
    return knee


BOOT_HEIGHT = 2.4


def arm(cv, shoulder, hand, depth, upper, fore, r_upper=1.5, r_fore=1.3, sleeve="copper", forearm="iron", bend=1, cuff=True,
        glove="iron"):
    """An arm from the shoulder to the hand: a sleeve over the upper arm, an iron forearm, a cuff, a fist. Returns the
    wrist and the forearm's direction."""
    elbow, wrist = ik(shoulder, hand, upper, fore, bend)
    limb(cv, shoulder, elbow, r_upper, sleeve, depth, lo=1, hi=4 if sleeve == "iron" else 3)
    limb(cv, elbow, wrist, r_fore, forearm, depth, lo=2, hi=4)
    if depth == 0:
        q = P(Xf(), elbow)
        cv.put(q[0], q[1], B[3])                                    # the elbow bolt (near plane only)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    fist = (wrist[0] + u[0] * 0.8, wrist[1] + u[1] * 0.8)
    if glove == "leather":
        cv.part(Xf(), Ellipse(fist[0], fist[1], 1.3, 1.3), "leather", flat(2), depth=depth, rust=0.0)
    else:
        cv.part(Xf(), Ellipse(fist[0], fist[1], 1.3, 1.3), glove, flat(3 - depth), rust=0.0)
    return fist, u


def revolver(cv, grip, angle, depth, rust=True, recoil=0.0, open_cylinder=False, scale=1.0, flash=False, glow=None, barrel=5.2):
    """A six-shooter pointing left from the hand at `grip` (the top of the grip), turned by `angle` degrees (+ raises the
    muzzle: rig.py turns clockwise on screen, and clockwise lifts a barrel that points left): an iron barrel (copper rust patches when `rust`), a fluted cylinder (swung out
    when reloading), the hammer, a wooden grip, the trigger guard. Returns the muzzle point (rig space)."""
    xf = Xf.pose(angle, (0.0, 0.0), (grip[0] + recoil, grip[1]))
    if scale != 1.0:
        xf = xf.then(Xf(scale, 0.0, 0.0, scale, 0.0, 0.0))
    cv.part(xf, Poly([(-0.2, -0.4), (1.6, -0.4), (2.8, 2.8), (1.0, 3.2)]), "leather", face((-0.5, -0.3, 0.8), lo=1, hi=2, fixed=True),
            depth=depth, rust=0.0)                                                                       # the grip
    frame_inner = cv.part(xf, Poly([(-2.0, -2.6), (1.4, -2.6), (2.0, -1.6), (1.6, -0.2), (-2.0, -0.2)]), "iron",
                          face((-0.4, -0.6, 0.7), lo=2, hi=4, fixed=True), depth=depth, rust=0.0)        # the frame
    if open_cylinder:
        cyl = cv.part(xf, Ellipse(-0.6, 0.8, 1.4, 1.2), "iron", dome(-1.0, 0.4, 1.6, lo=2, hi=4, fixed=True), depth=depth, rust=0.0)
        q = P(xf, (-0.6, 0.8))
        cv.put(q[0], q[1], I[0])                                    # its empty chamber
    else:
        cyl = cv.part(xf, box(-1.6, -3.0, 0.8, -0.4), "iron", face((-0.3, -0.7, 0.65), lo=2, hi=4, fixed=True), depth=depth, rust=0.0)
        for x in (-0.8, 0.2):                                       # the flutes
            q = P(xf, (x, -1.6))
            if q in cyl:
                cv.put(q[0], q[1], I[1])
    bx = -1.6 - barrel
    barrel_inner = cv.part(xf, box(bx, -2.6, -1.6, -1.2), "iron", face((0.0, -0.8, 0.6), lo=2, hi=4, fixed=True), depth=depth,
                           rust=0.55 if rust else 0.0, seed=41)
    q = P(xf, (bx + 0.4, -3.0))
    cv.put(q[0], q[1], I[max(1, 3 - depth)])                        # the front sight
    q = P(xf, (1.6, -3.2))
    cv.put(q[0], q[1], I[max(1, 3 - depth)])                        # the hammer
    q = P(xf, (-0.6, 0.6))
    if not open_cylinder:
        cv.put(q[0], q[1], I[1])                                    # the trigger guard
    if rust:
        for (x, y) in ((bx + 2.0, -2.0), (bx + 3.8, -1.6)):
            q = P(xf, (x, y))
            if q in barrel_inner:
                cv.put(q[0], q[1], C[2])
    if flash and glow is not None:                                  # the muzzle flash (glow: drawn at full brightness)
        m = xf.fwd((bx - 0.8, -1.9))
        for (dx, dy, col) in ((0, 0, E[3]), (-1, 0, E[3]), (-2, 0, E[2]), (-1, -1, E[2]), (-1, 1, E[2]), (-3, 0, E[1]), (0, -1, E[2]), (0, 1, E[2])):
            x, y = int(math.floor(m[0])) + dx, int(math.floor(m[1])) + dy
            cv.put_glow(x, y, col)
            glow.put_glow(x, y, col)
    del frame_inner
    return xf.fwd((bx - 0.4, -1.9))


def holster(cv, at, depth=0):
    """A leather holster on the hip with the revolver's wooden grip sticking out of it (the gun put away)."""
    x, y = at
    cv.part(Xf(), Poly([(x - 1.2, y), (x + 1.4, y), (x + 1.0, y + 4.4), (x - 0.4, y + 4.8), (x - 1.4, y + 1.6)]), "leather",
            face((-0.5, -0.3, 0.8), lo=1, hi=2, fixed=True), depth=depth, rust=0.0)
    cv.part(Xf(), Poly([(x - 0.4, y - 2.4), (x + 1.2, y - 2.6), (x + 1.4, y + 0.2), (x - 0.4, y + 0.2)]), "leather", flat(2), depth=depth, rust=0.0)
    q = P(Xf(), (x - 0.6, y - 0.4))
    cv.put(q[0], q[1], I[3])                                        # the hammer peeking out


def cowboy_hat(cv, top_center, brim_w, crown_h, crown_w, ramp="leather", band="brass", band_lit=4, depth=0, star=False, tilt=0.0):
    """A cowboy hat seen in three-quarter view, facing left: a wide brim curling up at its ends, a pinched crown with a
    dent on top, a band round the crown (and a little brass star on it for the Sheriff). Returns the crown's interior."""
    cx, cy = top_center
    xf = Xf.pose(tilt, (cx, cy + crown_h), (0.0, 0.0))
    hw = brim_w / 2.0
    brim = Poly([(cx - hw - 0.6, cy + crown_h - 1.6), (cx - hw + 1.6, cy + crown_h - 0.2), (cx + hw - 1.6, cy + crown_h - 0.2),
                 (cx + hw + 0.6, cy + crown_h - 1.4), (cx + hw + 0.2, cy + crown_h + 0.8), (cx - hw - 0.2, cy + crown_h + 0.8)])
    r = RAMP[ramp]
    binner = cv.part(xf, brim, ramp, face((-0.3, -0.8, 0.5), lo=1, hi=2, bias=0.3, fixed=True), depth=depth, rust=0.0)
    cw = crown_w / 2.0
    crown = Poly([(cx - cw, cy + crown_h), (cx - cw + 0.4, cy + 1.2), (cx - cw + 1.4, cy + 0.2), (cx - 0.4, cy + 0.9), (cx + 0.6, cy + 0.2),
                  (cx + cw - 0.8, cy + 0.6), (cx + cw, cy + crown_h)])
    cinner = cv.part(xf, crown, ramp, face((-0.55, -0.45, 0.7), lo=1, hi=len(r) - 1, gain=1.2, bias=0.35, fixed=True), depth=depth, rust=0.0)
    for x in range(int(math.floor(cx - cw + 1)), int(math.floor(cx + cw))):
        q = P(xf, (x + 0.5, cy + crown_h - 1.1))
        if q in cinner:
            cv.put(q[0], q[1], RAMP[band][band_lit] if x < cx - 0.5 else RAMP[band][band_lit - 1])
    if star:
        q = P(xf, (cx - cw * 0.45, cy + crown_h - 1.1))
        for (dx, dy, col) in ((0, 0, B[5]), (0, -1, B[4]), (-1, 0, B[4]), (1, 0, B[3]), (0, 1, B[3])):
            cv.put(q[0] + dx, q[1] + dy, col)
    for k in range(int(brim_w) - 2):                                 # the brim's lit upper edge
        q = P(xf, (cx - hw + 1.0 + k, cy + crown_h - 0.5))
        if q in binner and k % 4 != 3:
            cv.put(q[0], q[1], r[min(len(r) - 1, 2)])
    return cinner


def bandolier(cv, a, b, inner, n):
    """A leather strap two pixels wide from `a` to `b` across a chest (its lower edge a shade darker), with brass
    cartridges along it."""
    pts = []
    steps = int(math.hypot(b[0] - a[0], b[1] - a[1]) * 2) + 1
    for k in range(steps + 1):
        u = k / steps
        q = P(Xf(), (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
        if q not in pts:
            pts.append(q)
    band = set()
    for q in pts:
        for dy in (0, 1):
            r = (q[0], q[1] + dy)
            if r in inner:
                band.add(r)
    for r in band:
        cv.put(r[0], r[1], LE[1] if (r[0], r[1] + 1) in band else LE[0])
    shells = [q for q in pts if q in band]
    for k in range(n):
        if shells:
            q = shells[int((k + 0.5) / n * len(shells))]
            cv.put(q[0], q[1], B[4])
    return band
