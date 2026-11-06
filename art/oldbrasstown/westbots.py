"""Shared parts for Old Brass Town's gunslinger robots (the Brass Bandit and the Sheriff). Imported by make_bandit_art.py,
make_sheriff_art.py and the Cursed Conductor's generator; not run on its own.

2026-11-05 redraw (user: "most of the recent enemies are not matching the necessary pixel art detail quality (Metal
Slug level)"; measured in docs/design/pixel-art-study.md): the 2026-11-04 parts (art/oldbrasstown/previous/westbots.py)
were lanky (one-pixel limbs, capsule radius 1.3-1.6), dark (leather had 3 shades, median L* 12) and flat (two-step
shading). These are chunky (vanilla's 2.5-heads proportions: limbs 3-4 px thick, big boots, big hats, big guns),
modelled with the long ramps (steel 9 shades, gilt 10, hide 7, denim 6, crimson 6, oak 6, ivory 6) in small steps,
textured in each part's own space (felt, weave, grain, speckle; stable while it moves, D4 rule 17), and finished with a
selective lit-side outline and a despeckle that keeps one-shade texture (rig.selout, rig.soften_orphans).

Rig space as in art/bosses/trashtr0m/rig.py: 1 px = one art pixel, y down, the origin on the ground under the hips,
facing left. Limbs are lit across their real axis with the light's turn snapped to 22.5 degrees; bodies and hats are
lit in their own space (fixed=True). Every part outlines itself with its own ramp's darkest shade (D4 rule 3).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import (RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Union, Minus, box, Canvas, flat, dome, face, cyl, ik, level, lit,  # noqa: E402,F401
                 shaded, texture, selout, soften_orphans, glint, seg_pixels, _hash)

I, B, C, E, S, LE = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "leather"))
ST, G, H, K, D, OK, IV = (RAMP[k] for k in ("steel", "gilt", "hide", "crimson", "denim", "oak", "ivory"))


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def despeckle(cv):
    """Lone pixels (no 4-neighbour of the same colour, all four filled) take their neighbours' majority (D4 rule 4).
    The old, strict pass (kept for older art); new art finishes with finish()."""
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


def finish(cv, lit_outline=True):
    """The redraw's finishing pass: noise goes, one-shade texture stays, the lit side's outline catches the light."""
    soften_orphans(cv, 14.0)
    if lit_outline:
        selout(cv)


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


def limb(cv, a, b, r, ramp, depth, lo=None, hi=None, outline=True):
    """A capsule limb over a long ramp. On the far plane (depth > 0) it is one flat tone under its outline: a far limb
    is small and dark, and its swinging light bands flashed (check_flicker, 2026-11-04)."""
    n = len(RAMP[ramp])
    lo = (max(2, n // 3) if n >= 6 else 1) if lo is None else lo        # the upper part of a long ramp: mid-value limbs
    hi = n - 1 if hi is None else hi
    if depth > 0:
        return cv.part(Xf(), Capsule(a, b, r), ramp, flat(max(lo, (lo + hi) // 2 - depth), bevel=False), outline=outline,
                       depth=0, rust=0.0)
    return cv.part(Xf(), Capsule(a, b, r), ramp, limb_shade(a, b, r, lo, hi), outline=outline, depth=depth, rust=0.0)


BOOT_HEIGHT = 3.4


def boot(cv, ankle, depth, ramp="hide", spur=True, toe="steel"):
    """A riding boot round the ankle: a shaft, a heel, a long toe pointing left, a sole a shade down, a steel toe cap and
    a gilt rowel spur at the heel (near plane). Built round (0, 0) and placed at the ankle by a translation, so its
    texture rides with it (D4 rule 17)."""
    ax, ay = ankle
    xf = Xf.pose(0.0, (0.0, 0.0), (ax, ay))
    bh = BOOT_HEIGHT
    pts = [(2.0, -bh), (-1.4, -bh), (-1.6, -0.4), (-4.4, 0.4), (-4.8, 1.4), (-4.4, 2.2), (2.4, 2.2), (2.6, 0.8)]
    r = RAMP[ramp]
    if depth > 0:
        inner = cv.part(xf, Poly(pts), ramp, flat(2, bevel=False), rust=0.0)
    else:
        inner = cv.part(xf, Poly(pts), ramp, texture(face((-0.5, -0.55, 0.7), lo=2, hi=len(r) - 2, ramp_len=len(r), fixed=True),
                                                    "speckle", seed=11, density=0.1), rust=0.0)
    sole = P(xf, (0.0, 1.6))[1]
    cuff = P(xf, (0.0, -bh + 1.0))[1]
    for (x, y) in list(inner):
        if y == sole:
            cv.put(x, y, r[1])                                       # the sole, a shade under the leather
        elif y == cuff and depth == 0:
            cv.put(x, y, r[min(len(r) - 2, 4)])                      # the shaft's turned-down cuff catches the light
    if depth == 0 and toe:
        t = RAMP[toe]
        q = P(xf, (-3.8, 0.6))
        for (dx, dy, k) in ((0, 0, 6), (1, 0, 5), (0, 1, 4)):
            if (q[0] + dx, q[1] + dy) in inner:
                cv.put(q[0] + dx, q[1] + dy, t[k])
    if spur:
        sx, sy = P(xf, (3.0, 0.8))
        cols = (G[8], G[6], G[4]) if depth == 0 else (G[4], G[3], G[2])
        cv.put(sx, sy, cols[0])
        cv.put(sx + 1, sy, cols[1])
        cv.put(sx + 1, sy - 1, cols[2])
        cv.put(sx + 1, sy + 1, cols[2])
    return inner


def leg(cv, hip, foot_x, lift, depth, thigh, shin, r_thigh=2.1, r_shin=1.9, trousers="denim", boot_ramp="hide", spur=True,
        knee_ramp="steel"):
    """A leg from the hip to a boot on the ground (lifted `lift` px): thick trousers over the thigh and the shin, a steel
    knee cap, a riding boot. Returns the knee."""
    ankle = (foot_x, -2.4 - lift)
    knee, ankle = ik(hip, ankle, thigh, shin, -1)                # knees forward (left)
    limb(cv, hip, knee, r_thigh, trousers, depth)
    limb(cv, knee, ankle, r_shin, trousers, depth)
    boot(cv, ankle, depth, boot_ramp, spur)
    if depth == 0:                                                # the knee cap (near plane only: a moving bolt on the far
        q = P(Xf(), knee)                                         # plane read as flicker, D4 rule 17)
        k = RAMP[knee_ramp]
        cv.put(q[0] - 1, q[1], k[7])
        cv.put(q[0], q[1], k[5])
        cv.put(q[0] - 1, q[1] + 1, k[4])
    return knee


def arm(cv, shoulder, hand, depth, upper, fore, r_upper=1.9, r_fore=1.7, sleeve="denim", forearm="steel", bend=1, glove="hide",
        cuff="gilt"):
    """An arm from the shoulder to the hand: a thick sleeve, a steel forearm, a gilt cuff ring, a leather fist. Returns
    the fist and the forearm's direction."""
    elbow, wrist = ik(shoulder, hand, upper, fore, bend)
    limb(cv, shoulder, elbow, r_upper, sleeve, depth)
    limb(cv, elbow, wrist, r_fore, forearm, depth)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    if depth == 0 and cuff:
        c = RAMP[cuff]
        q = P(Xf(), (wrist[0] - u[0] * 0.6, wrist[1] - u[1] * 0.6))
        cv.put(q[0], q[1], c[7])
        cv.put(q[0], q[1] + 1, c[4])
    fist = (wrist[0] + u[0] * 0.9, wrist[1] + u[1] * 0.9)
    g = RAMP[glove]
    if depth > 0:
        cv.part(Xf(), Ellipse(fist[0], fist[1], 1.7, 1.6), glove, flat(2, bevel=False), rust=0.0)
    else:
        cv.part(Xf(), Ellipse(fist[0], fist[1], 1.8, 1.7), glove, dome(fist[0] - 0.8, fist[1] - 0.8, 2.4, lo=2, hi=len(g) - 2,
                                                                       fixed=True), rust=0.0)
    return fist, u


def revolver(cv, grip, angle, depth, style="rusty", recoil=0.0, open_cylinder=False, flash=False, glow=None, barrel=6.8):
    """A chunky six-shooter pointing left from the hand at `grip` (the top of the grip), turned by `angle` degrees (+
    raises the muzzle: rig.py turns clockwise on screen, which lifts a barrel pointing left). style "rusty" (the Bandit:
    a steel frame with copper rust, an oak grip with its grain) or "nickel" (the Sheriff: bright steel, an ivory grip, a
    gilt hammer). One outlined silhouette (small props drown in per-part outlines, 2026-11-05), the grip, the cylinder
    (swung out when reloading) and the barrel shaded inside it with dark seams between them, the front sight, the hammer
    and the trigger guard. Returns the muzzle point (rig space)."""
    xf = Xf.pose(angle, (0.0, 0.0), (grip[0] + recoil, grip[1]))
    nickel = style == "nickel"
    lo, hi = (4, 7) if nickel else (3, 6)
    bx = -2.2 - barrel
    grip_shape = Poly([(-0.4, -0.4), (2.6, -0.4), (4.2, 4.2), (3.8, 5.4), (1.2, 5.4), (0.0, 3.8)])
    frame_shape = Poly([(-2.8, -4.6), (2.2, -4.6), (3.2, -2.8), (2.8, 0.6), (-2.8, 0.6)])
    barrel_shape = box(bx, -4.6, -2.0, -0.6)
    cyl_shape = Ellipse(-0.8, 1.8, 2.4, 2.2) if open_cylinder else box(-2.6, -5.6, 1.2, 0.6)
    sil = cv.part(xf, Union(grip_shape, frame_shape, barrel_shape, cyl_shape), "steel",
                  face((-0.4, -0.6, 0.7), lo=lo, hi=hi, ramp_len=9, fixed=True), rust=0.0 if nickel else 0.4, seed=41)
    grip_ramp = "ivory" if nickel else "oak"
    gr = RAMP[grip_ramp]
    grip_shade = face((-0.5, -0.3, 0.8), lo=2, hi=len(gr) - 1, ramp_len=len(gr), bias=0.25, fixed=True)
    if not nickel:
        grip_shade = texture(grip_shade, "grain", seed=5)
    grip_px = cv.part(xf, grip_shape, grip_ramp, grip_shade, outline=False, clip=sil, rust=0.0)
    q = P(xf, (2.0, 2.4))
    if q in grip_px:
        cv.put(q[0], q[1], G[7] if nickel else ST[6])               # the grip screw
    for k in range(5):                                              # the seam between the grip and the frame
        qq = P(xf, (-0.2 + k * 0.6, 0.0))
        if qq in sil:
            cv.put(qq[0], qq[1], gr[1])
    cyl_shade = dome(-1.4, 0.8, 2.4, lo=lo, hi=hi + 1, fixed=True) if open_cylinder else dome(-1.6, -2.6, 3.4, lo=lo, hi=hi + 1, fixed=True)
    cyl = cv.part(xf, cyl_shape, "steel", cyl_shade, outline=False, clip=sil, rust=0.0)
    if open_cylinder:
        for (x, y) in ((-0.8, 1.4), (-1.8, 0.8), (0.2, 2.0)):
            qq = P(xf, (x, y))
            if qq in cyl:
                cv.put(qq[0], qq[1], ST[1])                         # its empty chambers
    else:
        for y in (-3.8, -1.6):                                      # the flutes
            for x in (-1.8, -0.6, 0.4):
                qq = P(xf, (x, y))
                if qq in cyl:
                    cv.put(qq[0], qq[1], ST[lo - 1])
        for y in range(-6, 1):                                      # the cylinder's front and back seams
            for x in (-2.6, 1.2):
                qq = P(xf, (x, y + 0.5))
                if qq in sil:
                    cv.put(qq[0], qq[1], ST[1])
    for k in range(int(barrel)):                                    # the barrel's lit top line
        qq = P(xf, (bx + 0.6 + k, -3.6))
        if qq in sil:
            cv.put(qq[0], qq[1], ST[hi + 1] if k % 3 else ST[min(8, hi + 2)])
    for k in range(int(barrel) - 1):                                # the ejector rod's groove along its underside
        qq = P(xf, (bx + 1.2 + k, -1.5))
        if qq in sil and k % 2 == 0:
            cv.put(qq[0], qq[1], ST[lo - 1])
    qq = P(xf, (bx + 0.5, -5.1))
    cv.put(qq[0], qq[1], ST[hi])                                    # the front sight
    hammer = G if nickel else ST
    qq = P(xf, (2.2, -5.4))
    cv.put(qq[0], qq[1], hammer[6])                                 # the hammer
    cv.put(qq[0] + 1, qq[1] - 1, hammer[4])
    if not open_cylinder:
        qq = P(xf, (-0.4, 1.2))
        cv.put(qq[0], qq[1], ST[1])                                 # the trigger guard
        cv.put(qq[0] - 1, qq[1] + 1, ST[2])
        cv.put(qq[0], qq[1] + 1, ST[1])
    if flash and glow is not None:                                  # the muzzle flash (glow: drawn at full brightness)
        m = xf.fwd((bx - 1.0, -2.6))
        for (dx, dy, col) in ((0, 0, E[3]), (-1, 0, E[3]), (-2, 0, E[3]), (-3, 0, E[2]), (-1, -1, E[2]), (-1, 1, E[2]), (-2, -1, E[1]),
                              (-2, 1, E[1]), (-4, 0, E[1]), (0, -1, E[2]), (0, 1, E[2]), (-3, -2, E[1]), (-3, 2, E[1])):
            x, y = int(math.floor(m[0])) + dx, int(math.floor(m[1])) + dy
            cv.put_glow(x, y, col)
            glow.put_glow(x, y, col)
    return xf.fwd((bx - 0.4, -2.6))


def holster(cv, at, style="rusty"):
    """A leather holster on the hip, its stitching a shade up, the revolver's grip sticking out of it (the gun put away).
    Built round (0, 0), placed at `at`."""
    xf = Xf.pose(0.0, (0.0, 0.0), at)
    inner = cv.part(xf, Poly([(-1.6, 0.0), (1.8, 0.0), (1.4, 5.2), (-0.4, 5.8), (-1.8, 2.0)]), "hide",
                    face((-0.5, -0.3, 0.8), lo=2, hi=4, ramp_len=7, fixed=True), rust=0.0)
    for k in (0, 2):
        q = P(xf, (-0.8 + 0.3 * k, 1.0 + k * 1.1))
        if q in inner:
            cv.put(q[0], q[1], H[5])                                # stitches
    grip_ramp = "ivory" if style == "nickel" else "oak"
    cv.part(xf, Poly([(-0.6, -3.0), (1.4, -3.2), (1.8, 0.4), (-0.6, 0.4)]), grip_ramp,
            face((-0.5, -0.4, 0.8), lo=2, hi=4, ramp_len=6, fixed=True), rust=0.0)
    q = P(xf, (-0.8, -0.6))
    cv.put(q[0], q[1], ST[6])                                       # the hammer peeking out


def cowboy_hat(cv, top_center, brim_w, crown_h, crown_w, ramp="hide", band="gilt", depth=0, star=False, tilt=0.0, hole=False,
               lo=2, hi=None):
    """A cowboy hat in three-quarter view, facing left: a pinched crown (a crease on top, felt texture, a band of gilt
    conchos round it; a gilt star on the band for the Sheriff, a bullet hole through the crown for the Bandit) and in
    front of it a wide brim curling up at its ends, its top lit and its underside a shade down; the brim joins the crown
    without an outline between them. Returns the crown's interior."""
    r = RAMP[ramp]
    hi = len(r) - 2 if hi is None else hi
    # built round (0, 0) (the crown's top centre) and placed at top_center by the pose: its felt rides with it (rule 17)
    xf = Xf.pose(tilt, (0.0, crown_h), top_center)
    cx, cy = 0.0, 0.0
    hw = brim_w / 2.0
    by = cy + crown_h
    cw = crown_w / 2.0
    crown = Poly([(cx - cw, by + 0.4), (cx - cw + 0.2, cy + 1.8), (cx - cw + 1.0, cy + 0.4), (cx - 1.0, cy + 1.0), (cx - 0.2, cy + 1.6),
                  (cx + 0.8, cy + 0.6), (cx + cw - 0.6, cy + 0.8), (cx + cw, cy + 2.0), (cx + cw + 0.2, by + 0.4)])
    crown_px = cv.part(xf, crown, ramp, texture(face((-0.6, -0.45, 0.7), lo=lo, hi=hi, ramp_len=len(r), gain=1.25, bias=0.3,
                                                     fixed=True, dither=0.16), "felt", seed=9), rust=0.0)
    for k in range(3):                                                # the crease down the front of the crown
        q = P(xf, (cx - 0.4 - 0.2 * k, cy + 1.6 + k))
        if q in crown_px:
            cv.put(q[0], q[1], r[lo])
    bnd = RAMP[band]
    band_y = by - 1.0
    for x in range(int(math.floor(cx - cw + 1)), int(math.floor(cx + cw + 1))):
        q = P(xf, (x + 0.5, band_y))
        if q in crown_px:
            k = 7 if x < cx - 0.5 else 5
            if (x - int(cx)) % 3 == 0:
                k = 8 if x < cx - 0.5 else 6                          # conchos
            cv.put(q[0], q[1], bnd[min(len(bnd) - 1, k)])
            q2 = (q[0], q[1] + 1)
            if q2 in crown_px:
                cv.put(q2[0], q2[1], bnd[4])
    if star:
        q = P(xf, (cx - cw * 0.4, band_y - 0.4))
        for (dx, dy, k) in ((0, 0, 9), (0, -1, 8), (-1, 0, 8), (1, 0, 6), (0, 1, 6), (-1, 1, 4), (1, -1, 7)):
            cv.put(q[0] + dx, q[1] + dy, G[k])
    if hole:
        q = P(xf, (cx + cw * 0.35, cy + 2.4))
        if q in crown_px:
            cv.put(q[0], q[1], r[0])
            cv.put(q[0] + 1, q[1] + 1, r[min(len(r) - 1, hi + 1)])     # the hole's lit lower rim
    brim = Poly([(cx - hw - 0.8, by - 2.6), (cx - hw + 0.4, by - 1.2), (cx - hw + 2.6, by - 0.4), (cx + hw - 2.6, by - 0.4),
                 (cx + hw - 0.4, by - 1.2), (cx + hw + 0.8, by - 2.4), (cx + hw + 0.8, by + 1.0), (cx + hw - 2.2, by + 2.4),
                 (cx - hw + 2.2, by + 2.4), (cx - hw - 0.6, by + 1.0)])
    crown_all = set(crown_px)
    for q in list(cv.px):
        if any((q[0] + dx, q[1] + dy) in crown_px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            crown_all.add(q)
    brim_px = cv.part(xf, brim, ramp, texture(face((-0.3, -0.85, 0.45), lo=lo, hi=hi, ramp_len=len(r), bias=0.3, fixed=True),
                                               "felt", seed=3), merge=crown_all, rust=0.0)
    under = int(math.floor(by + 1.4))
    for (x, y) in brim_px:
        if y >= under:
            cv.put(x, y, r[max(1, lo - 1)])                          # the brim's underside
    for k in range(int(brim_w) - 3):                                  # the brim's lit upper edge
        q = P(xf, (cx - hw + 1.2 + k, by - 0.2))
        if q in brim_px and k % 5 != 4:
            cv.put(q[0], q[1], r[min(len(r) - 1, hi + (1 if k < brim_w * 0.4 else 0))])
    return crown_px


def bandolier(cv, a, b, inner, n):
    """A leather strap two pixels wide from `a` to `b` across a chest (its lower edge a shade darker), with gilt
    cartridges along it, each with a glint."""
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
        cv.put(r[0], r[1], H[3] if (r[0], r[1] + 1) in band else H[1])
    shells = [q for q in pts if q in band]
    for k in range(n):
        if shells:
            q = shells[int((k + 0.5) / n * len(shells))]
            cv.put(q[0], q[1], G[8])
            if (q[0], q[1] + 1) in band:
                cv.put(q[0], q[1] + 1, G[5])
    return band
