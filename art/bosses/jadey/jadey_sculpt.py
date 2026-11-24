"""Jadey's body, sculpted (2026-11-23, the sprite-quality study: "provide a redesign of our most bellow average sprites like
Jadey ... keeping the theme but reworking with found data analisis"). The 2026-11-16..18 design is kept: a panda jademancer
in a jade qipao sitting cross-legged on a floating crimson cushion, a rope dart in her near paw, a jade gem on her brow. What
changes is how she is drawn (the cogpunk-pixel-art skill, art/templates/sculpt.py): every part a shape with a surface normal
sampled 4 x 4 per art pixel and pixelated per part, the ramps used over their length, structure on the big areas (a brocade
motif one step off the qipao, folds, fur tufts on the cheeks and the black fur, the cushion's piping and seams), selective
outlines, a rim light, cast shadows. make_jadey_art.frame() calls draw() for the far, middle and near planes; her poses, frame
list, rig data and small sprites stay where they were.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
from sculpt import Frame, Ell, Tube, Poly, Part, render  # noqa: E402


class HalfTop(Ell):
    """The top of an ellipsoid down to `cut` px under its centre (a cap of hair)."""

    def __init__(self, cx, cy, rx, ry, cut):
        super().__init__(cx, cy, rx, ry)
        self.cut = cut

    def sample(self, lx, ly):
        return None if ly > self.cy + self.cut else super().sample(lx, ly)

from rig import RAMP  # noqa: E402

ST, IV, GH, G, K, AE = (RAMP[k] for k in ("steel", "ivory", "ghost", "gilt", "crimson", "aether"))
W, H, OX, OY = 84, 72, 42, 64      # the render cell (1x) round the rig origin (under the cushion's middle)
HEAD_C = (0.0, -36.8)
GEM = (-0.4, -41.6)
SH_NEAR, SH_FAR = (-15.0, -24.6), (15.0, -24.6)
UPPER, FORE = 6.2, 6.0

# the qipao's brocade: little four-petal flowers in a half-drop grid, one step lighter (its own space)
BROCADE = tuple((x + (2 if (y // 4) % 2 else 0), y, 0.9, 0.9, 1) for y in range(-8, 10, 4) for x in range(-10, 11, 4))


def ik(shoulder, hand, upper, fore, bend):
    sx, sy = shoulder
    hx, hy = hand
    dx, dy = hx - sx, hy - sy
    d = max(1e-3, min(upper + fore - 0.01, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    cos_b = max(-1.0, min(1.0, (upper * upper + d * d - fore * fore) / (2 * upper * d)))
    b = math.acos(cos_b) * bend
    elbow = (sx + math.cos(a + b) * upper, sy + math.sin(a + b) * upper)
    ux, uy = (hx - elbow[0]), (hy - elbow[1])
    ul = math.hypot(ux, uy) or 1.0
    wrist = (elbow[0] + ux / ul * min(fore, ul), elbow[1] + uy / ul * min(fore, ul))
    return elbow, wrist


def arm_parts(parts, name, shoulder, hand, bend, plane, dim, palms):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, bend)
    hi = 4 - dim
    parts.append(Part(name + "Upper", Tube([shoulder, elbow], [3.4, 3.0]), ST, 10, lo=1, hi=hi, plane=plane, bump_step=False,
                      lines=(((shoulder[0] + (elbow[0] - shoulder[0]) * 0.5 + 1.0, shoulder[1] + (elbow[1] - shoulder[1]) * 0.5),
                              (elbow[0] + 0.6, elbow[1] - 0.4)),)))
    parts.append(Part(name + "Fore", Tube([elbow, wrist], [3.0, 2.7]), ST, 10.1, lo=1, hi=hi, plane=plane, bump_step=False))
    ux, uy = wrist[0] - elbow[0], wrist[1] - elbow[1]
    ul = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ul, uy / ul
    c0 = (wrist[0] - ux * 1.6, wrist[1] - uy * 1.6)
    c1 = (wrist[0] - ux * 0.2, wrist[1] - uy * 0.2)
    parts.append(Part(name + "Cuff", Tube([c0, c1], [3.0, 3.0]), GH, 10.2, lo=1, hi=4 - dim, plane=plane, bump_step=False))
    paw = (wrist[0] + ux * 1.3, wrist[1] + uy * 1.3)
    parts.append(Part(name + "Paw", Ell(0.0, 0.0, 3.1, 2.8), ST, 10.3, frame=Frame(*paw), lo=1, hi=hi, plane=plane))
    if palms and dim == 0:
        parts.append(Part(name + "Pad", Ell(0.0, 0.0, 1.6, 1.3), IV, 10.4, frame=Frame(paw[0] + ux * 0.6, paw[1] + uy * 0.6), lo=2,
                          hi=4, plane=plane, outline=False))
    return paw, c1


def model(p, far_hand, near_hand, only_far):
    parts = []
    far_paw, far_cuff = arm_parts(parts, "Far", SH_FAR, far_hand, -1, "far", 1, p.palms)
    if only_far:
        return parts, None, far_paw, None, far_cuff
    sw = p.sway
    # the cushion: a plump crimson pillow, gilt piping round its middle, tassels at its corners
    parts.append(Part("Cushion", Ell(0.0, 0.0, 19.5, 5.3), K, 1, frame=Frame(0.0, -4.4), lo=1, hi=5,
                      lines=(((-15.0, 2.2), (-6.0, 3.4), (6.0, 3.4), (15.0, 2.2)),)))
    parts.append(Part("Piping", Tube([(-18.6, -3.4), (-9.0, -2.6), (0.0, -2.4), (9.0, -2.6), (18.6, -3.4)], [0.65] * 5), G, 1.2, lo=3,
                      hi=8, outline=False, bump_step=False))
    for side in (-1, 1):
        top = (side * 19.6, -4.6)
        end = (side * 20.2 + sw * 0.8, -0.4)
        parts.append(Part("Cord%d" % side, Tube([top, end], [0.6, 0.6]), G, 1.3, lo=3, hi=7, outline=False))
        parts.append(Part("Tassel%d" % side, Tube([(end[0], end[1] - 0.4), (end[0] + sw * 0.4, end[1] + 2.6)], [1.4, 1.0]), G, 1.4,
                          lo=2, hi=7))
    # the crossed legs: black thighs, jade-wrapped shins crossing in front, the far foot behind
    parts.append(Part("ThighFar", Ell(0.0, 0.0, 9.0, 4.4), ST, 2, frame=Frame(7.8, -10.0, 0.08), lo=1, hi=3))
    parts.append(Part("ThighNear", Ell(0.0, 0.0, 9.0, 4.4), ST, 2.2, frame=Frame(-7.8, -10.0, -0.08), lo=1, hi=4))
    parts.append(Part("ShinFar", Tube([(13.5, -8.4), (-6.5, -7.0)], [2.6, 2.3]), GH, 2.6, lo=1, hi=3, bump_step=False,
                      lines=(((8.0, -9.6), (8.0, -6.0)), ((2.0, -9.0), (2.0, -5.6)))))
    parts.append(Part("FootFar", Ell(0.0, 0.0, 2.8, 2.1), ST, 2.7, frame=Frame(-8.6, -6.8), lo=1, hi=3))
    parts.append(Part("ShinNear", Tube([(-13.5, -8.2), (6.6, -6.8)], [2.7, 2.4]), GH, 3, lo=1, hi=5, bump_step=False,
                      lines=(((-8.0, -9.6), (-8.0, -5.8)), ((-2.0, -9.2), (-2.0, -5.4)))))
    parts.append(Part("FootNear", Ell(0.0, 0.0, 2.9, 2.2), ST, 3.1, frame=Frame(8.8, -6.7), lo=1, hi=4))
    # the qipao: a rounded torso and hips, folds under the chest, the brocade; the collar; the sash and its knot
    parts.append(Part("Hips", Ell(0.0, 0.0, 12.6, 5.4), GH, 4, frame=Frame(0.0, -14.2), lo=1, hi=4,
                      lines=(((-8.0, 1.6), (-3.0, 3.0)), ((3.0, 3.0), (8.0, 1.6)))))
    parts.append(Part("Torso", Ell(0.0, 0.0, 11.4, 9.6), GH, 4.2, frame=Frame(0.0, -21.8), lo=1, hi=5, spots=BROCADE,
                      lines=(((-6.5, 5.0), (-3.0, 6.6)), ((3.0, 6.6), (6.5, 5.0)), ((-2.0, -2.0), (-1.0, 1.0)))))
    parts.append(Part("Sash", Tube([(-11.6, -16.8), (-4.0, -16.0), (4.0, -16.0), (11.6, -16.8)], [1.5, 1.4, 1.4, 1.5]), K, 4.4,
                      lo=1, hi=5, bump_step=False))
    parts.append(Part("Knot", Ell(0.0, 0.0, 2.3, 2.0), K, 4.5, frame=Frame(9.4, -16.6), lo=2, hi=5))
    for k, dx in enumerate((-0.6, 1.4)):
        parts.append(Part("SashEnd%d" % k, Tube([(9.4 + dx, -15.2), (10.0 + dx + sw * 0.7, -11.0 + k)], [1.1, 0.8]), K, 4.45, lo=1,
                          hi=4))
    parts.append(Part("Collar", Ell(0.0, 0.0, 5.0, 2.3), GH, 4.6, frame=Frame(0.0, -30.4), lo=2, hi=5))
    parts.append(Part("Opening", Tube([(-4.4, -30.2), (-1.0, -28.0), (3.6, -26.4), (7.4, -23.2)], [0.6, 0.6, 0.6, 0.6]), G, 4.7, lo=4,
                      hi=8, outline=False, bump_step=False))
    parts.append(Part("CollarEdge", Tube([(-5.0, -31.6), (0.0, -32.4), (5.0, -31.6)], [0.55, 0.55, 0.55]), G, 4.65, lo=4, hi=8,
                      outline=False, bump_step=False))
    # the head: white fur, cheek tufts, the muzzle, black ears and eye patches
    hx, hy = HEAD_C
    for side, r in ((-1, 3.4), (1, 3.2)):
        parts.append(Part("Ear%d" % side, Ell(0.0, 0.0, r, r * 0.95), ST, 5.6, frame=Frame(hx + side * 8.6, hy - 8.2), lo=1, hi=4))
    parts.append(Part("Head", Ell(0.0, 0.0, 10.8, 9.2), IV, 6, frame=Frame(hx, hy), lo=3, hi=5, dither=0.0, gain=1.25))   # clean white fur
    for side in (-1, 1):
        x0 = hx + side * 9.4
        parts.append(Part("Tuft%d" % side, Poly([(x0, hy + 0.6), (x0 + side * 3.0, hy + 3.6), (x0 + side * 0.4, hy + 3.2),
                                                (x0 + side * 2.2, hy + 6.2), (x0 - side * 1.6, hy + 4.8)]), IV, 5.9, lo=2, hi=4, dither=0.0))
    # the face's soft parts have no outline: an outline ring round the muzzle and patches made a mask (2026-11-23 review)
    parts.append(Part("Muzzle", Ell(0.0, 0.0, 4.0, 2.6), IV, 6.3, frame=Frame(hx - 0.4, hy + 3.6), lo=4, hi=5, outline=False,
                      dither=0.0))
    parts.append(Part("Nose", Ell(0.0, 0.0, 1.4, 0.95), ST, 6.5, frame=Frame(hx - 0.4, hy + 2.4), lo=1, hi=3, outline=False))
    parts.append(Part("PatchNear", Ell(0.0, 0.0, 3.1, 2.5), ST, 6.4, frame=Frame(hx - 4.7, hy - 0.1, -0.35), lo=1, hi=3,
                      outline=False))
    parts.append(Part("PatchFar", Ell(0.0, 0.0, 2.9, 2.4), ST, 6.4, frame=Frame(hx + 4.3, hy - 0.1, 0.35), lo=1, hi=3,
                      outline=False))
    # the hair: bangs over the brow, a fringe, the top knot with its jade pin, the gilt circlet
    parts.append(Part("Hair", HalfTop(0.0, 0.0, 10.4, 5.0, 1.2), ST, 6.6, frame=Frame(hx, hy - 6.6), lo=1, hi=4,
                      lines=(((-6.0, -1.0), (-3.0, 2.5)), ((2.0, -2.0), (4.0, 2.0)))))
    for k, (x0, x1) in enumerate(((-8.0, -5.0), (5.6, 8.4))):     # side locks framing the face
        parts.append(Part("Fringe%d" % k, Poly([(hx + x0, hy - 5.6), (hx + x1, hy - 5.6), (hx + (x0 + x1) / 2 - 0.6, hy - 1.2)]), ST, 6.65,
                          lo=1, hi=3, dither=0.0))
    parts.append(Part("Bun", Ell(0.0, 0.0, 4.5, 3.9), ST, 6.7, frame=Frame(hx, hy - 13.6), lo=1, hi=4,
                      lines=(((-2.0, -2.0), (1.0, 1.5)),)))
    parts.append(Part("Pin", Tube([(hx - 5.2, hy - 15.4), (hx + 5.6, hy - 12.6)], [0.75, 0.75]), GH, 6.8, lo=3, hi=5, bump_step=False))
    parts.append(Part("PinBead", Ell(0.0, 0.0, 1.3, 1.3), GH, 6.85, frame=Frame(hx + 6.0, hy - 12.4), lo=3, hi=5, glow_from=5))
    parts.append(Part("Circlet", Tube([(hx - 8.0, hy - 5.0), (hx - 4.0, hy - 5.6), (hx + 4.0, hy - 5.6), (hx + 8.0, hy - 5.0)],
                                      [0.55] * 4), G, 6.9, lo=4, hi=8, outline=False, bump_step=False))
    near_paw, near_cuff = arm_parts(parts, "Near", SH_NEAR, near_hand, 1, "near", 0, p.palms)
    return parts, near_paw, far_paw, near_cuff, far_cuff


def stamp(px, glow, p, near_cuff, far_cuff):
    """The face, the gem and the small gilt, by hand at the target size (rig coordinates)."""
    hx, hy = HEAD_C

    def put(x, y, c, g=False):
        q = (int(math.floor(x)), int(math.floor(y)))
        if q in px:
            px[q] = c
            if g:
                glow[q] = c
    for ex in (hx - 5.4, hx + 3.6):                          # the eyes in their patches
        ey = hy - 0.6
        if p.eyes == 0:
            put(ex, ey + 0.5, ST[0])
            put(ex + 1, ey + 0.5, ST[0])
        elif p.eyes == 3:
            put(ex, ey + 0.5, GH[4], True)
            put(ex + 1, ey + 0.5, GH[3])
            put(ex, ey - 0.5, ST[0])
            put(ex + 1, ey - 0.5, ST[0])
        else:
            g = p.eyes == 2
            for (dx, dy, c) in ((0, 0, GH[5]), (1, 0, GH[4]), (2, 0, GH[3]), (0, 1, GH[4]), (1, 1, GH[3]), (2, 1, GH[2])):
                put(ex + dx, ey + dy, c, True if g or (dx, dy) == (0, 0) else False)
            put(ex, ey, (250, 252, 240), True)               # the glint
    if p.mouth == 1:                                         # the smirk
        for (dx, dy) in ((-2, 0), (-1, 1), (0, 1), (1, 0)):
            put(hx - 0.4 + dx, hy + 4.4 + dy, ST[1])
    elif p.mouth == 2:
        for (dx, dy, c) in ((-1, 0, ST[0]), (0, 0, ST[0]), (-1, 1, K[2]), (0, 1, K[3])):
            put(hx - 0.4 + dx, hy + 4.6 + dy, c)
    else:
        put(hx - 1.4, hy + 4.6, ST[1])
        put(hx + 0.6, hy + 4.6, ST[1])
    for x in (hx - 8.4, hx + 7.4):                           # rosy cheeks
        put(x, hy + 2.6, K[4])
        put(x + 1, hy + 2.6, K[5])
    for (dx, dy) in ((-1, 0), (0, 0), (1, 0)):               # the purple streak down the bangs
        put(hx - 6.0 + dx * 0.6, hy - 6.6 + dy + dx, AE[2])
    put(hx - 6.6, hy - 5.4, AE[3])
    gx, gy = GEM[0], GEM[1] + 0.4                            # the brow gem in its gilt setting, on the circlet
    gem = (GH[5], GH[4], GH[3]) if p.gem else (GH[4], GH[3], GH[2])
    for (dx, dy, c) in ((0, 0, gem[0]), (1, 0, gem[1]), (0, 1, gem[1]), (1, 1, gem[2]), (-1, 0, G[7]), (2, 0, G[5]), (-1, 1, G[6]),
                        (2, 1, G[4])):
        put(gx + dx, gy + dy, c, dx in (0, 1))
    if p.gem >= 2:
        for (dx, dy) in ((0, -1), (1, -1), (-1, 2), (2, 2)):
            glow[(int(math.floor(gx + dx)), int(math.floor(gy + dy)))] = GH[4]
    for (x, y) in ((0.0, -27.2), (0.0, -23.6), (0.0, -20.0)):  # the frog buttons down her axis
        put(x - 1, y, G[7])
        put(x, y, G[8])
        put(x + 1, y, G[5])
    for cuff in (near_cuff, far_cuff):                       # a gilt band on each cuff
        if cuff:
            put(cuff[0], cuff[1], G[7])


def draw(far, mid, near, glow, p, far_hand, near_hand, only_far=False):
    """Renders her into the canvases (rig coordinates); returns (near paw, far paw)."""
    parts, near_paw, far_paw, near_cuff, far_cuff = model(p, far_hand, near_hand, only_far)
    out = {}
    for plane in ("far", "mid", "near"):
        sel = [q for q in parts if q.plane == plane]
        if not sel:
            continue
        px, gl, _ = render(sel, W, H, OX, OY)
        out[plane] = ({(x - OX, y - OY): c for (x, y), c in px.items()}, {(x - OX, y - OY): c for (x, y), c in gl.items()})
    for plane, cv in (("far", far), ("mid", mid), ("near", near)):
        if plane in out:
            cv.px.update(out[plane][0])
            for q, c in out[plane][1].items():
                cv.put_glow(q[0], q[1], c)
                glow.put_glow(q[0], q[1], c)
    if not only_far:
        stamp(mid.px, mid.glow, p, None, None)
        for q, c in mid.glow.items():
            glow.put_glow(q[0], q[1], c)
        stamp(near.px, near.glow, p, near_cuff, None)
        stamp(far.px, far.glow, p, None, far_cuff)
    for paw, light, cv in ((near_paw, p.hand_glow, near), (far_paw, p.far_glow, far)):   # jade light in a paw
        if not light or paw is None:
            continue
        rad = 1.6 + light * 0.8
        cx, cy = paw[0], paw[1] - 2.2
        for y in range(int(cy - rad - 1), int(cy + rad + 2)):
            for x in range(int(cx - rad - 1), int(cx + rad + 2)):
                dd = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if dd <= rad and (x, y) not in cv.px:
                    col = GH[5] if dd < rad * 0.4 else GH[4] if dd < rad * 0.75 else GH[3]
                    cv.put_glow(x, y, col)
                    glow.put_glow(x, y, col)
    return near_paw, far_paw
