"""Source for the Fungimancer (D4), v2 2026-11-23. Run from the repo root:

    python -P art/bosses/fungimancer/make_fungimancer_art.py [--preview FILE]

User, 2026-11-19: "a new secret boss to the blue mushroom area called "Fungimancer" a magic dumb frog like creature ...
Reference for the design on the example image of the prompt (floaty boss)". 2026-11-23: "provide a redesign of our most bellow
average sprites like Jadey, Fox spirit, fungimancer (this one is extra ugly currently) keeping the theme but reworking with
found data analisis" (docs/design/sprite-quality-study.md; the cogpunk-pixel-art skill). v1 (coarse shapes drawn at 1x: edge
density 0.36, patches of 8 px) is in previous/make_fungimancer_art_2026-11-19.py.

The reference (reference/fungimancer_user_2026-11-19.png, a painting) gives the pose, proportions and colours only: a fat
frog sitting on a floating glowing mushroom, a pale belly, a wide head with big bulging orange eyes and slit pupils, red
frills sweeping back off the head, arms turning from green to red hands, violet magic.

How it is made (the skill's "model, then pixelate"): every part is a shape with a real surface normal, sampled 4 x 4 times per
art pixel (art/templates/sculpt.py); a pixel takes the part covering most of it and its shade from the part's mean normal
under one top-left light, in flat bands of a hue-shifted ramp (the new `frog` and `belly` ramps: teal shadows, yellow-green
light), dithered only at band edges in the part's own space. The skin has structure, not noise: warts that bend the light
(lit on their top-left, shaded under), darker blotches on the back, folds across the belly; the frills are tubes with a
ridge; the cap is a dome with gills and glowing spots. Selective outline (the darkest step on the far side and against parts
behind, a middle step on the lit side), a rim light inside the lit outline, a cast shadow on parts behind. The face is placed
by hand at the target size: slit pupils looking two ways (the dumb look), glints, a wide grin with a tooth and the tip of the
tongue poking out.

Three planes (D4 rule 13): far (the far arm), middle (the seat, legs, body, head, frills), near (the near arm). Faces left.
Frames and outputs as v1 (FungimancerRigData's names; the game code reads the same constants):
  Idle 0-3  Cast 4-7  Croak 8-11  Tongue 12-14  Fizzle 15-16  Intro 17-18  Death 19-22
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, HERE)
from sculpt import Frame, Ell, Tube, Part, render  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
import fungimancer_things as things  # noqa: E402

OUT = "Content/Bosses/Fungimancer/"
COLUMNS = 4
FR, BE, K, EM, DN, AE, SM, G = (RAMP[k] for k in ("frog", "belly", "crimson", "ember", "denim", "aether", "steam", "gilt"))
W, H = 72, 82                      # the cell (1x); the origin under the stalk at (OX, OY)
OX, OY = 36, 78
LIFT = 7.0                         # the frog sits on top of the cap's dome: every frog part this far above its rig numbers
GROUND_CLIP = 3

# --- the rig (art px, facing left, y negative up) ----------------------------------------------------------------------------
BODY = (1.0, -30.0, 19.0, 17.0)
BELLY = (-3.5, -26.0, 13.0, 13.0)
HEAD = (-2.5, -46.5, 17.0, 10.5)
EYE_N, EYE_F = (-11.0, -55.5, 6.0), (6.5, -56.5, 5.0)
SHOULDER_N, SHOULDER_F = (-13.0, -35.0), (14.0, -36.0)
MOUTH = (-17.0, -43.0)
# warts on the back and sides (body frame; scattered once with a fixed seed, kept off the belly), blotches one step
# darker; the belly's small bumps (the reference's pale belly) and folds
BODY_WARTS = ((13.6, -6.1, 0.9), (3.5, -13.9, 1.0), (-12.2, -6.9, 1.3), (8.4, -3.1, 0.9), (14.4, 5.4, 1.4), (-7.1, -10.7, 1.6), (4.9, -6.7, 1.7), (8.3, 9.2, 1.4), (8.1, -9.7, 1.4), (-1.7, -13.3, 1.5), (1.9, -8.7, 1.1), (10.5, 6.0, 1.4), (-15.9, -2.8, 1.5), (11.1, 1.4, 1.0), (13.4, -1.2, 1.6), (7.8, 13.7, 1.1), (-2.1, -10.0, 0.9), (11.4, -10.1, 1.1), (16.4, -3.7, 1.5), (-11.6, -10.9, 1.3), (3.4, 14.7, 1.8), (11.0, -4.8, 1.0), (4.6, -10.7, 1.2), (12.7, 10.2, 1.0), (17.0, 2.0, 1.7), (7.2, -13.5, 1.6))
BODY_BLOTCH = ((10, -7, 3.2, 2.2, -1), (15, 6, 2.6, 2.0, -1), (-14, -8, 2.2, 1.6, -1), (4, -12, 2.0, 1.4, -1))
HEAD_WARTS = ((-7.9, -5.0, 1.2), (7.9, -1.2, 0.8), (12.5, -1.9, 0.8), (11.8, 2.0, 0.9), (4.1, -0.3, 1.3), (-0.6, -7.6, 0.9), (2.2, 2.2, 0.9), (7.7, -5.3, 0.9), (0.1, -2.9, 0.9), (-4.0, -2.1, 1.1))
THIGH_WARTS = ((-2.6, -3.9, 1.4), (1.4, 1.3, 1.0), (-5.6, -1.9, 1.3), (0.7, 4.7, 1.3), (-2.8, 0.0, 1.1), (7.3, -0.8, 1.4))
BELLY_BUMPS = ((-7.6, -2.4, 0.7), (-2.1, 5.3, 1.0), (1.3, 8.7, 1.0), (-7.4, 2.3, 0.9), (8.4, -0.6, 1.0), (-3.1, -2.4, 0.8), (5.9, 6.9, 0.9), (0.1, -4.8, 0.8), (-10.4, 3.4, 0.8), (-2.1, 9.1, 0.7), (-2.8, 2.3, 0.9), (4.8, -2.8, 0.7), (5.6, 2.8, 0.8), (-0.5, -8.1, 0.8))
BELLY_FOLDS = (((-9, 5), (-4, 6.5), (2, 6.5), (8, 5)), ((-7, 9), (-2, 10), (4, 9.6)))
FRILLS = (((9.0, -53.0), (18.0, -60.0), (26.0, -58.0), 2.2), ((12.0, -49.0), (22.0, -52.0), (29.0, -47.0), 2.1),
          ((12.5, -45.0), (21.0, -44.0), (27.0, -38.5), 2.0), ((6.0, -56.0), (12.0, -64.0), (19.0, -66.0), 1.8),
          ((10.0, -41.0), (16.0, -36.0), (19.0, -30.0), 1.6))
CAP_SPOTS = ((-30, -11, 1.5), (-25, -14, 1.8), (-19, -16, 1.3), (25, -14, 1.7), (30, -11, 1.4), (19, -16, 1.2))
CAP_DOTS = ((-26.0, -11.0, 1.6, 1.0, 1), (-20.0, -14.5, 1.4, 1.0, 1), (-13.0, -16.5, 1.6, 1.0, 1), (12.0, -16.8, 1.5, 1.0, 1),
            (19.0, -14.8, 1.7, 1.1, 1), (27.0, -11.2, 1.4, 1.0, 1), (-31.0, -9.6, 1.1, 0.8, 1), (31.5, -9.4, 1.0, 0.8, 1))
SPROUTS = ((-11.0, -38.0), (13.0, -40.0), (-15.0, -24.0), (16.0, -25.0), (3.0, -19.0), (-3.0, -60.0), (9.0, -31.0))


class HalfEll(Ell):
    """The top of an ellipsoid, cut flat `cut` px under its centre (a mushroom's cap)."""

    def __init__(self, cx, cy, rx, ry, cut=1.0, flat=0.0):
        super().__init__(cx, cy, rx, ry, flat)
        self.cut = cut

    def sample(self, lx, ly):
        return None if ly > self.cy + self.cut else super().sample(lx, ly)


class Pose:
    def __init__(self, near=(-13.5, -21.0), far=(13.0, -22.0), sac=0.0, mouth=0, eyes=0, breath=0.0, bloat=0.0, shrooms=0,
                 magic=0, frill=0.0, lean=0.0):
        self.near, self.far = near, far
        self.sac, self.mouth, self.eyes, self.breath = sac, mouth, eyes, breath
        self.bloat, self.shrooms, self.magic = bloat, shrooms, magic
        self.frill = frill                         # the frills' sway (radians about their roots: follow-through)
        self.lean = lean                           # px the head leans forward (a croak, a lunge)


def ellpart(name, c, ramp, z, lo=1, hi=None, s=1.0, **kw):
    cx, cy, rx, ry = c
    return Part(name, Ell(0.0, 0.0, rx * s, ry * s), ramp, z, frame=Frame(cx, cy), lo=lo, hi=hi, **kw)


def arm(parts, name, shoulder, hand, z, plane, dim=0, magic=False):
    """Green upper arm, the forearm turning red, a red hand: palm and three long fingers with round pads."""
    sx, sy = shoulder
    hx, hy = hand
    mx, my = (sx + hx) / 2.0, (sy + hy) / 2.0
    dx, dy = hx - sx, hy - sy
    ln = math.hypot(dx, dy) or 1.0
    px, py = -dy / ln, dx / ln
    if px < 0:
        px, py = -px, -py
    elbow = (mx + px * 2.6, my + py * 2.6 + 1.5)
    hi_f, hi_k = 7 - dim, 5 - dim
    parts.append(Part(name + "Upper", Tube([shoulder, elbow], [2.9, 2.5]), FR, z, lo=1, hi=hi_f, plane=plane))
    parts.append(Part(name + "Fore", Tube([elbow, hand], [2.5, 2.1]), K, z + 0.1, lo=1, hi=hi_k, plane=plane))
    ux, uy = (hx - elbow[0]), (hy - elbow[1])
    ul = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ul, uy / ul
    parts.append(Part(name + "Palm", Ell(0.0, 0.0, 2.7, 2.3), K, z + 0.2, frame=Frame(hx, hy), lo=1, hi=hi_k, plane=plane))
    for k, spread in enumerate((-0.75, 0.0, 0.72)):
        c, s_ = math.cos(spread), math.sin(spread)
        fx, fy = ux * c - uy * s_, ux * s_ + uy * c
        length = (4.2, 4.9, 4.0)[k]
        tip = (hx + fx * length, hy + fy * length)
        parts.append(Part(name + "Finger%d" % k, Tube([(hx + fx * 1.5, hy + fy * 1.5), tip], [1.15, 0.95]), K, z + 0.3, lo=1,
                          hi=hi_k, plane=plane))
        parts.append(Part(name + "Pad%d" % k, Ell(0.0, 0.0, 1.35, 1.35), K, z + 0.4, frame=Frame(*tip), lo=2, hi=hi_k,
                          plane=plane))


def model(p):
    """The parts of one pose."""
    parts = []
    s = 1.0 + 0.2 * p.bloat
    # the seat: a pale blue stalk, violet gills, the glowing blue cap
    parts.append(Part("Stalk", Tube([(0.0, 1.0), (0.0, -7.0)], [3.4, 4.4]), DN, 1, lo=3, hi=5))
    parts.append(Part("Gills", Ell(0.0, -8.0, 31.0, 3.0, flat=0.7), AE, 2, lo=1, hi=2, dither=0.0,
                      lines=tuple(((x, -8.2), (x * 1.06, -6.6)) for x in range(-28, 29, 4))))
    parts.append(Part("Cap", HalfEll(0.0, -9.0, 33.0, 10.0, cut=0.6), DN, 2.5, lo=2, hi=5, gain=1.2, spots=CAP_DOTS))
    # the far leg (behind the body), the body, the belly, the near leg
    parts.append(ellpart("ThighFar", (16.5, -18.0, 9.0, 7.5), FR, 3, hi=6, bumps=THIGH_WARTS, bump_gain=1.6))
    parts.append(ellpart("FootFar", (21.5, -12.6, 6.4, 2.6), K, 3.2, hi=4))
    for k in range(3):
        parts.append(ellpart("ToeFar%d" % k, (25.5 + k * 1.9, -12.0 + (k == 1) * -0.4, 1.35, 1.3), K, 3.3, hi=4))
    parts.append(Part("Body", Ell(0.0, 0.0, BODY[2] * s, BODY[3] * s), FR, 4, frame=Frame(BODY[0], BODY[1]), lo=1, hi=7,
                      bumps=BODY_WARTS, spots=BODY_BLOTCH, bump_gain=1.7))
    parts.append(Part("Belly", Ell(0.0, 0.0, BELLY[2] * s + p.breath * 0.5, BELLY[3] * s + p.breath * 0.5), BE, 5,
                      frame=Frame(BELLY[0], BELLY[1]), lo=1, hi=5, lines=BELLY_FOLDS, dither=0.1, bumps=BELLY_BUMPS,
                      bump_gain=1.3))
    parts.append(ellpart("ThighNear", (-16.0, -17.5, 9.5, 7.5), FR, 6, bumps=THIGH_WARTS, bump_gain=1.6))
    parts.append(ellpart("FootNear", (-22.5, -12.6, 7.0, 2.8), K, 6.2, hi=5))
    for k in range(3):
        parts.append(ellpart("ToeNear%d" % k, (-27.5 - k * 2.0, -12.0 + (k == 1) * -0.4, 1.45, 1.35), K, 6.3, hi=5))
    # the frills: tubes off the back of the head, a ridge down each; they sway about their roots
    for k, (a, m, b, r) in enumerate(FRILLS):
        rot = p.frill * (1.0 + 0.15 * k)
        c, s_ = math.cos(rot), math.sin(rot)

        def turn(q, a=a):
            dx, dy = q[0] - a[0], q[1] - a[1]
            return (a[0] + dx * c - dy * s_, a[1] + dx * s_ + dy * c)
        pts = [a, turn(m), turn(b)]
        parts.append(Part("Frill%d" % k, Tube(pts, [r, r * 0.72, 0.7]), K, 6.8 - k * 0.01, lo=1, hi=5,
                          lines=((pts[0], pts[1], pts[2]),)))
    hx, hy = HEAD[0] - p.lean, HEAD[1]
    parts.append(Part("Head", Ell(0.0, 0.0, HEAD[2] * (1 + 0.1 * p.bloat), HEAD[3] * (1 + 0.1 * p.bloat)), FR, 7,
                      frame=Frame(hx, hy), lo=1, hi=7, bumps=HEAD_WARTS, bump_gain=1.6))
    if p.sac > 0.0:
        parts.append(Part("Sac", Ell(0.0, 0.0, 5.5 + 6.5 * p.sac, 3.0 + 4.8 * p.sac), BE, 7.4,
                          frame=Frame(hx - 5.0, hy + 8.0 + 2.0 * p.sac), lo=2, hi=5))
    if p.mouth:
        h = 2.6 if p.mouth == 1 else 4.4
        parts.append(Part("Maw", Ell(0.0, 0.0, 11.0, h, flat=0.5), K, 7.6, frame=Frame(hx - 5.0, hy + 4.4), lo=1, hi=2,
                          outline=False, dither=0.0))
        parts.append(Part("Tongue", Ell(0.0, 0.0, 6.0, h * 0.5), K, 7.7, frame=Frame(hx - 3.0, hy + 4.4 + h * 0.45), lo=3, hi=4,
                          outline=False))
    for (ex, ey, r) in (EYE_N, EYE_F):
        ex -= p.lean
        r *= 1.0 + 0.18 * p.bloat
        parts.append(Part("Mound", Ell(0.0, 0.0, r + 1.5, r + 1.2), FR, 8, frame=Frame(ex, ey + 0.4), lo=1, hi=6))
        if p.eyes != 2:
            parts.append(Part("Eye", Ell(0.0, 0.0, r, r), EM, 9, frame=Frame(ex, ey), lo=1, hi=3, gain=1.3))
    for k in range(min(p.shrooms, len(SPROUTS))):
        x, y = SPROUTS[k]
        parts.append(Part("SproutStalk%d" % k, Tube([(x, y + 1.6), (x, y - 0.8)], [1.0, 0.9]), DN, 10, lo=4, hi=5))
        parts.append(Part("SproutCap%d" % k, HalfEll(0.0, 0.0, 3.4, 2.6, cut=0.4), DN, 10.1, frame=Frame(x, y - 1.2), lo=3, hi=5,
                          glow_from=5))
    arm(parts, "Far", SHOULDER_F, p.far, 0, "far", dim=2)
    arm(parts, "Near", SHOULDER_N, p.near, 20, "near")
    for q in parts:                                          # the frog sits on the dome: lift all but the seat
        if q.name in ("Stalk", "Gills", "Cap"):
            continue
        if isinstance(q.shape, Tube) and q.frame.x == 0.0 and q.frame.y == 0.0:
            q.shape.pts = [(x, y - LIFT) for (x, y) in q.shape.pts]
        else:
            q.frame = Frame(q.frame.x, q.frame.y - LIFT, q.frame.a, q.frame.sx, q.frame.sy)
    return parts


def stamp_face(px, glow, p, owner):
    """The features at the target size, by hand (after the render: they are smaller than its cleanup)."""
    def put(x, y, c, g=False, seat=False):
        q = (int(math.floor(x)) + OX, int(math.floor(y - (0.0 if seat else LIFT))) + OY)
        px[q] = c
        if g:
            glow[q] = c
    for (ex, ey, r), look in ((EYE_N, (-1.4, 0.3) if p.eyes == 0 else (1.6, 0.4)), (EYE_F, (1.4, -1.0) if p.eyes == 0 else (-1.6, 0.5))):
        ex -= p.lean
        r *= 1.0 + 0.18 * p.bloat
        if p.eyes == 2:
            for x in range(int(ex - r + 1), int(ex + r)):
                put(x, ey + 0.6, FR[0])                     # shut: the lid's line
            continue
        cx, cy = ex + look[0], ey + look[1]
        for dy in (-2, -1, 0, 1, 2) if r >= 5.5 else (-1, 0, 1, 2):
            put(cx, cy + dy, K[0])                          # the slit pupil
        put(cx + 1, cy, K[1])
        put(ex - r * 0.5, ey - r * 0.55, SM[3], True)        # the glint
        put(ex - r * 0.5 + 1, ey - r * 0.55, SM[2])
        put(ex - r * 0.5, ey - r * 0.55 + 1, SM[1])
        put(cx + 1, cy - 1, EM[3], True)
    hx, hy = HEAD[0] - p.lean, HEAD[1]
    if p.mouth == 0:                                        # the dopey grin: a long line, its front corner down
        for x in range(int(hx - 15), int(hx + 10)):
            y = hy + 3.8 + 0.010 * (x - hx + 3) ** 2 - (1.0 if x < hx - 12 else 0.0) * -1.0
            put(x, y, FR[0])
        put(hx - 9, hy + 4.8, (236, 226, 200))               # a tooth
        put(hx - 14, hy + 5.2, K[4])                         # the tip of the tongue at the corner
        put(hx - 15, hy + 5.6, K[3])
    else:
        for x in (hx - 12, hx - 7, hx + 1):
            put(x, hy + 4.4 - (2.6 if p.mouth == 1 else 4.4) + 1, (236, 226, 200))
    for (sx, sy, r) in CAP_SPOTS:                           # the cap's glowing spots
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= r * r and owner.get((int(math.floor(sx + dx)) + OX, int(math.floor(sy + dy)) + OY)) == "Cap":
                    c = SM[3] if dx * dx + dy * dy <= (r * 0.5) ** 2 else SM[1]
                    put(sx + dx, sy + dy, c, True, seat=True)
    if p.magic:
        hx2, hy2 = p.near
        pts = ((0, -1), (-1, 0), (1, 0), (0, 1), (0, 0), (-1, -1), (1, -1))
        if p.magic == 2:
            pts += ((-2, -3), (2, -3), (0, -4), (-3, -1), (3, -1))
        for (dx, dy) in pts:
            c = SM[3] if (dx, dy) == (0, 0) else AE[3] if (dx + dy) % 2 == 0 else AE[2]
            glow[(int(hx2 + dx) + OX, int(hy2 + dy - 1 - LIFT) + OY)] = c


def frame(p):
    parts = model(p)
    planes = {}
    for plane in ("far", "mid", "near"):
        sel = [q for q in parts if q.plane == plane]
        planes[plane] = render(sel, W, H, OX, OY)
    far, mid, near = planes["far"], planes["mid"], planes["near"]
    glow = dict(mid[1])
    stamp_face(mid[0], glow, p, mid[2])
    glow.update(near[1])
    return far[0], mid[0], near[0], glow


REST_N, REST_F = (-13.5, -21.0), (13.0, -22.0)
CAST = ((-20.0, -33.0), (-19.0, -50.0), (-30.0, -42.0), (-20.0, -28.0))
SWAY = (0.0, 0.04, 0.07, 0.04)
FRAMES = ([("Idle%d" % k, Pose(breath=(0, 1, 2, 1)[k], eyes=2 if k == 3 else 0, frill=SWAY[k])) for k in range(4)]
          + [("Cast%d" % k, Pose(near=h, magic=(0, 2, 1, 0)[k], mouth=1 if k == 2 else 0, frill=(-0.04, -0.08, 0.1, 0.05)[k]))
             for k, h in enumerate(CAST)]
          + [("Croak%d" % k, Pose(sac=s, mouth=1 if k == 2 else 0, far=(14.0, -26.0), lean=(0, 1, 2, 1)[k],
                                  frill=(0.02, -0.05, 0.09, 0.03)[k])) for k, s in enumerate((0.35, 0.85, 1.0, 0.4))]
          + [("Tongue%d" % k, Pose(mouth=m, near=(-17.0, -26.0), lean=(1, 2, 1)[k], frill=(0.0, 0.08, 0.04)[k]))
             for k, m in enumerate((1, 2, 1))]
          + [("Fizzle%d" % k, Pose(eyes=1, mouth=1 if k == 0 else 2, near=(-19.0, -40.0) if k == 0 else (-16.0, -30.0),
                                   frill=(-0.06, 0.06)[k])) for k in range(2)]
          + [("Intro%d" % k, Pose(eyes=2 if k == 0 else 0, breath=1)) for k in range(2)]
          + [("Death%d" % k, Pose(bloat=bl, shrooms=n, eyes=1, mouth=1 if k else 0, frill=0.05 * k)) for k, (bl, n) in
             enumerate(((0.25, 1), (0.5, 3), (0.75, 5), (1.0, 7)))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Cast", "Croak", "Tongue", "Fizzle", "Intro", "Death")


def grid(images):
    rows = (len(images) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((W + 1) * COLUMNS, (H + 1) * rows), (0, 0, 0, 0))
    for k, px in enumerate(images):
        bx, by = (k % COLUMNS) * (W + 1), (k // COLUMNS) * (H + 1)
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < min(H, OY + GROUND_CLIP):
                out.putpixel((bx + x, by + y), tuple(c) + (255,))
    return out


def write_rig(path, frames):
    mid0 = frames[0][2]
    xs = sorted(x - OX for (x, y) in mid0 if y - OY > HEAD[1] - LIFT)
    left, right = xs[2], xs[-3] + 1
    top = int(EYE_N[1] - EYE_N[2] - 1 - LIFT)
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def arr(name, vals):
        return "\t\tpublic static readonly short[] %s = { %s };" % (name, ", ".join(str(v) for v in vals))
    lines = [
        "// <auto-generated> by art/bosses/fungimancer/make_fungimancer_art.py - do not edit by hand. </auto-generated>",
        "namespace Cogpunk.Content.Bosses.Fungimancer",
        "{",
        "\t/// <summary>The Fungimancer's grid sheets (game px, facing left): far, middle, near and glow, equal cells in",
        "\t/// <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is under its seat's stalk. Body*: its hitbox",
        "\t/// from the origin. Per frame, from the origin, facing left: NearX/NearY the near hand (its spells leave it); Mouth: the",
        "\t/// mouth's front corner (the tongue leaves it); Throat: under the chin (the croak's ring).</summary>",
        "\tpublic static class FungimancerRigData",
        "\t{",
        "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
        % (W * 2, H * 2, OX * 2, OY * 2, len(FRAMES), COLUMNS),
        "\t\tpublic const int " + ", ".join(seq[:4]) + ";",
        "\t\tpublic const int " + ", ".join(seq[4:]) + ";",
        "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, BodyBottom = 0;" % (left * 2, right * 2, top * 2),
        "\t\tpublic const int MouthX = %d, MouthY = %d, ThroatX = %d, ThroatY = %d;"
        % (round(MOUTH[0] * 2), round((MOUTH[1] - LIFT) * 2), round((HEAD[0] - 5) * 2), round((HEAD[1] + 9 - LIFT) * 2)),
        arr("NearX", [round(p.near[0] * 2) for (_, p) in FRAMES]),
        arr("NearY", [round((p.near[1] - 1 - LIFT) * 2) for (_, p) in FRAMES]),
        "\t}",
        "}",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("wrote", path)


def crop(px, keep):
    sel = {q: c for q, c in px.items() if keep(q[0] - OX, q[1] - OY)}
    xs, ys = [x for x, _ in sel], [y for _, y in sel]
    return to_image(sel, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def export_all():
    frames = []
    for name, p in FRAMES:
        far, mid, near, glow = frame(p)
        frames.append((name, far, mid, near, glow))
        print(".", end="", flush=True)
    print()
    for key, idx in (("", 2), ("_Far", 1), ("_Near", 3), ("_Glow", 4)):
        export(grid([fr[idx] for fr in frames]), OUT + "Fungimancer%s.png" % key)
    write_rig(OUT + "FungimancerRigData.cs", frames)
    mid0 = frames[0][2]
    export(crop(mid0, lambda x, y: abs(x - HEAD[0]) <= 14 and HEAD[1] - LIFT - 16 <= y <= HEAD[1] - LIFT + 8), OUT + "Fungimancer_Head_Boss.png")
    dead = frames[INDEX["Death3"]][2]
    export(crop(dead, lambda x, y: y <= HEAD[1] - LIFT + 7), OUT + "Gores/Fungimancer_GoreHead.png")
    export(crop(dead, lambda x, y: HEAD[1] - LIFT + 7 < y <= -20), OUT + "Gores/Fungimancer_GoreBody.png")
    export(crop(dead, lambda x, y: y > -20), OUT + "Gores/Fungimancer_GoreSeat.png")
    export(things.spore_bolt(), OUT + "Projectiles/SporeBolt.png")
    export(things.shroom_spike(), OUT + "Projectiles/ShroomSpike.png")
    export(things.tongue_tip(), OUT + "Projectiles/FungimancerTongue.png")
    export(things.bag(), OUT + "Items/FungimancerBag.png")
    export(things.summon_item(), OUT + "Items/RainbowMushroom.png")
    export(things.tile_sheet(), OUT + "Tiles/RainbowMushroomTile.png")
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames", help="comma list of frame names to render only (a quick look)")
    args = ap.parse_args()
    if args.frames:
        pick = args.frames.split(",")
        frames = []
        for name, p in FRAMES:
            if name in pick:
                far, mid, near, glow = frame(p)
                frames.append((name, far, mid, near, glow))
    else:
        frames = export_all()
    if args.preview:
        sc = 4
        cols = min(6, len(frames))
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * (W * sc + 8) + 8, rows * (H * sc + 8) + 8), (24, 24, 30, 255))
        for k, (name, far, mid, near, glow) in enumerate(frames):
            im = Image.new("RGBA", (W, H), (30, 38, 66, 255))
            for layer in (far, mid, near, glow):
                for (x, y), c in layer.items():
                    if 0 <= x < W and 0 <= y < H:
                        im.putpixel((x, y), tuple(c) + (255,))
            sheet.alpha_composite(im.resize((W * sc, H * sc), Image.NEAREST), (8 + (k % cols) * (W * sc + 8), 8 + (k // cols) * (H * sc + 8)))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
