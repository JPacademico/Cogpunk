"""Source for the Rhino Beetle (D4), 2026-11-11 (user: "add a new enemy to populate the ruins: rhino beetle (ensure good
sprite and animations)"; the same day, second request, it became a rare Hardmode jungle enemy: "make the rhino a rare
enemy of the jungle on hardmode instead of the ruins now"). Run from the repo root:

    python -P art/jungle/make_rhino_beetle_art.py [--preview FILE]

Design (my calls): a giant rhinoceros beetle of the deep jungle. A glossy mahogany shell (Oak, lit from the top-left, a
cream gloss on the dome), lengthwise grooves on its elytra and a spore-lit vein on them like a sprouting leaf, glowing
the jungle's bioluminescent green (the ghost ramp; it was the ruins' blue rune until 2026-11-11b), a crust of moss on
the rear slope; a domed pronotum with a short forked horn pointing forward over a long curved horn rising from the head
(the pincer every rhino beetle is known by); a glossy black eye with the spores' green in it; little clubbed antennae;
six legs, the fore tibiae toothed for digging.
Three-quarter side view facing left (D4 rule 13), chunky (D4 rule 18).

Three planes (DepthLayers.DrawWalker grid sheets): far (the far legs and antenna, and in flight the far elytron and
wing, flat and a step darker), middle (the shell, the pronotum, the head and both horns), near (the near legs, and in
flight the near elytron and wing); the glow sheet holds the eye's glint and, while the shell is closed, the vein. Stable
pixels (D4 rule 17): every part is lit in its own space and placed by whole pixels; the head turns only for the big
deliberate moves (levelled for the charge, the toss), never inside a loop.

Frames:
- Walk x8: a tripod gait (near fore, far middle and near hind legs against the other three), each foot planted half the
  cycle and sliding back the root motion (the Jaeger's rule, docs/design/pixel-art-study.md), lifting in an arc; the
  antennae twitch.
- Brace x3: the telegraph: the front sinks, the horn levels at the target, the fore legs scrape in turn.
- Charge x4: a fast scuttle with the horn levelled, long strides.
- Toss x3: the horn scoops under, flicks up and settles (the ram throws the player up).
- Skid: legs braced forward, the front reared back. Dazed x2: the head hanging after a wall, a shudder.
- TakeOff x2: the elytra lift and the wings unfold. Fly x4: elytra held up, the wings beating, legs tucked.

Outputs:
    Content/Jungle/NPCs/RhinoBeetle.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Jungle/NPCs/RhinoBeetleRigData.cs   cells, origin, frames, strides, the horn's tip (from the origin, facing left)
    Content/Jungle/Gores/RhinoBeetle_GoreHorn.png, _GoreShell.png, _GoreLeg.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, ik, P, limb, finish, texture,  # noqa: E402
                      OK, IV, D, H, S)
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Jungle/"
V = RAMP["verd"]
G = RAMP["ghost"]                            # the spores' bioluminescent green

# --- the rig (art px, facing left, y down, the origin on the ground under the middle) ----------------------------------
SHELL = (4.0, -9.4, 12.4, 7.4)               # the elytra: centre, radii
PRONOTUM = (-8.4, -9.8, 6.6, 6.2)
HEAD = (-15.0, -6.8, 3.9, 3.2)
NECK = (-12.6, -7.6)                         # the head's pivot
HINGE = (-3.6, -14.6)                        # the elytra's hinge
WING_ROOT = (-2.4, -13.0)
HIPS = {"f": (-10.0, -4.6), "m": (-2.6, -4.0), "h": (5.0, -4.0)}
REST = {"f": -16.4, "m": -1.2, "h": 12.2}    # a foot's x at rest
BONES = {"f": (4.6, 5.0, -1), "m": (3.9, 4.4, 1), "h": (4.8, 5.4, 1)}   # femur, tibia, which way the knee bends
FAR = (2, -1)                                # the far side's legs and wings: back and up a pixel (whole px)

CEPHALIC = [(-16.6, -8.0, 2.7), (-19.4, -11.4, 2.45), (-20.8, -15.2, 2.1), (-20.6, -18.8, 1.75), (-19.4, -21.6, 1.45),
            (-17.6, -23.6, 1.15)]
CEPHALIC_PRONG = ((-19.6, -21.8), (-21.8, -23.6), 1.05)      # the fork at the tip
THORACIC = [(-9.6, -14.4, 2.3), (-12.8, -16.0, 1.85), (-15.8, -16.6, 1.35)]
THORACIC_PRONG = ((-15.0, -16.6), (-16.6, -18.4), 0.95)
HORN_TIP = (-17.6, -23.6)
RUNE = ((0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-1, -1), (-2, -2), (1, -1), (2, -2))   # a sprouting vein, its heart at (0, 0)
RUNE_AT = (7.0, -9.0)
CORAL = ((0, 0, 1), (1, 0, 2), (2, 0, 1), (-1, 1, 1), (0, 1, 2), (1, 1, 2), (2, 1, 0), (0, 2, 0), (1, 2, 0))   # moss
CORAL_AT = (11.6, -5.6)                      # grown on the shell's rear slope


class Pose:
    def __init__(self, bob=0, front=0, head=0.0, feet=None, shudder=0, elytra=None, wing=None, antenna=0):
        self.bob = bob                  # whole px the whole body sits lower (+)
        self.front = front              # whole px the pronotum and head sink (+) or rear (-) against the shell
        self.head = head                # degrees the head and its horn turn down (+) about the neck
        self.shudder = shudder          # whole px (0 / 1)
        # feet: near/far x fore/middle/hind: (x from rest, lift)
        self.feet = dict(feet) if feet else {}
        for k in ("nf", "nm", "nh", "ff", "fm", "fh"):
            self.feet.setdefault(k, (0.0, 0.0))
        self.elytra = elytra            # None: closed on the back; else degrees lifted
        self.wing = wing                # None: folded away; else (the beat's angle, - = tip up; how far it is spread)
        self.antenna = antenna          # 0 / 1: the clubs' twitch (whole px)


# --- parts ---------------------------------------------------------------------------------------------------------------
def grooves(cx, cy, rx, ry):
    """The elytra's lengthwise grooves: arcs that follow the dome's top, in the shell's own space (stable)."""
    def is_groove(lx, ly):
        if ly > cy + 1.5 or lx < cx - rx * 0.8:
            return False
        d = math.hypot((lx - cx) / rx, (ly - cy) / ry)
        return abs(d - 0.52) < 0.055 or abs(d - 0.78) < 0.05
    return is_groove


def shell_shade(cx, cy, rx, ry):
    base = texture(dome(cx - 3.6, cy - 4.2, 12.5, lo=1, hi=5, gain=1.4, bias=0.08, fixed=True, dither=0.28), "speckle", seed=41,
                   density=0.07, lo=1, hi=5)                 # the elytra's fine pitting
    groove = grooves(cx, cy, rx, ry)

    def shade(i):
        k = base(i)
        if (i.ly - cy) / ry > 0.74:
            k = min(k, 2)                                   # the rim along the bottom (the epipleura), in shadow
        if groove(i.lx, i.ly):
            k -= 1
        return max(1, k)
    return shade


def shell(mid, glow, T, p):
    """The closed elytra: the big glossy dome of the back."""
    cx, cy, rx, ry = SHELL
    inner = mid.part(T, Ellipse(cx, cy, rx, ry), "oak", shell_shade(cx, cy, rx, ry), rust=0.0)
    return inner


def abdomen(mid, T):
    """Under the lifted elytra: the soft ringed abdomen (Hide, darker), its segments in its own space."""
    cx, cy, rx, ry = SHELL
    base = dome(cx - 3.0, cy - 3.0, 12.0, lo=2, hi=4, gain=1.2, fixed=True)

    def shade(i):
        k = base(i)
        if int(math.floor(i.lx - cx + 40)) % 3 == 0:
            k -= 1                                          # the rings between the segments
        return max(1, k)
    return mid.part(T, Ellipse(cx + 0.6, cy + 1.2, rx - 0.8, ry - 1.4), "hide", shade, rust=0.0)


def pronotum(mid, F):
    cx, cy, rx, ry = PRONOTUM
    return mid.part(F, Ellipse(cx, cy, rx, ry), "hide", texture(dome(cx - 2.4, cy - 3.2, 7.6, lo=1, hi=4, gain=1.55, bias=-0.22,
                                                                      fixed=True, dither=0.26), "speckle", seed=43, density=0.05,
                                                                 lo=1, hi=4), shadow=(1, 1), rust=0.0)


def horn(cv, X, pts, prong, depth=0):
    """A horn as one shape (no seams): a flat mid tone, lit along its top, dark along its underside."""
    caps = [Capsule((a[0], a[1]), (b[0], b[1]), a[2], b[2]) for a, b in zip(pts, pts[1:])]
    caps.append(Capsule(prong[0], prong[1], prong[2]))
    inner = cv.part(X, Union(*caps), "hide", flat(2, bevel=False), rust=0.0)
    for q in list(inner):
        if (q[0], q[1] - 1) not in inner:
            cv.put(q[0], q[1], H[3] if depth == 0 else H[2])  # lit along its top
        elif (q[0] + 1, q[1]) not in inner or (q[0], q[1] + 1) not in inner:
            cv.put(q[0], q[1], H[1])                        # dark along its underside
    return inner


def head(mid, far, F, p):
    """The head on its neck pivot, turned down by p.head, with the long curved horn; antennae and mouthparts."""
    Hx = F.then(Xf.pose(-p.head, NECK, (0.0, 0.0)))
    cx, cy, rx, ry = HEAD
    # the far antenna first, behind everything (the far plane)
    antenna(far, Hx, p, 1)
    hinner = mid.part(Hx, Ellipse(cx, cy, rx, ry), "hide", dome(cx - 1.6, cy - 2.0, 4.6, lo=1, hi=3, gain=1.4, bias=-0.1, fixed=True, dither=0.2),
                      rust=0.0)
    hinner |= horn(mid, Hx, CEPHALIC, CEPHALIC_PRONG)
    antenna(mid, Hx, p, 0)
    return Hx, hinner


def antenna(cv, Hx, p, depth):
    """A little lamellate antenna: a two-pixel stalk from under the horn's root, a club that twitches by a pixel."""
    dx, dy = (FAR[0] - 1, FAR[1]) if depth else (0, 0)
    stalk = ((-18.6, -5.4), (-19.6, -5.4))
    for (x, y) in stalk:
        q = P(Hx, (x + dx, y + dy))
        cv.put(q[0], q[1], H[1] if depth else H[3])
    club = P(Hx, (-21.6 + dx, -6.4 + dy - p.antenna))
    for (ox, oy, k) in ((0, 0, 5), (1, 0, 4), (0, 1, 2), (1, 1, 1)):
        cv.put(club[0] + ox, club[1] + oy, H[max(1, k - 2 * depth)])


def thoracic(mid, F):
    return horn(mid, F, THORACIC, THORACIC_PRONG)


def leg(cv, key, hip, rest_x, foot, depth):
    """A leg from its hip to a foot on the ground (`foot` = (x from rest, lift)): a thick femur, a toothed tibia (the
    fore legs dig), a short tarsus with its claw on the ground row."""
    femur, tibia, bend = BONES[key]
    ankle = (rest_x + foot[0], -1.2 - foot[1])
    knee, ankle = ik(hip, ankle, femur, tibia, bend)
    limb(cv, hip, knee, 1.65, "hide", depth, lo=1, hi=4)
    limb(cv, knee, ankle, 1.3, "hide", depth, lo=1, hi=3)
    reach = -1.0 if key == "f" else (1.0 if key == "h" else 0.6)
    toe = (ankle[0] + 2.2 * reach, ankle[1] + 0.4)
    limb(cv, ankle, toe, 1.0, "hide", depth, lo=1, hi=3)
    if depth == 0:
        claw = P(Xf(), (toe[0] + 0.9 * reach, toe[1] + 0.2))
        cv.put(claw[0], claw[1], H[0])
        k = P(Xf(), (knee[0] - 0.4, knee[1] - 0.6))            # the knee's glossy cap
        cv.put(k[0], k[1], H[5])
        if key == "f":                                      # two teeth on the tibia's outer edge
            tx, ty = ankle[0] - knee[0], ankle[1] - knee[1]
            ln = math.hypot(tx, ty) or 1.0
            nx, ny = ty / ln, -tx / ln                       # outward: away from the knee's bend
            if bend < 0:
                nx, ny = -nx, -ny
            for u in (0.4, 0.75):
                q = P(Xf(), (knee[0] + tx * u + nx * 1.7, knee[1] + ty * u + ny * 1.7))
                cv.put(q[0], q[1], H[1])


def wing(cv, T, angle, depth, spread=1.0):
    """A hind wing unfolded from under the elytra: a long membrane (Ivory) with dark veins and a stiff leading edge,
    beating about its root. Opaque (no semi-transparent pixels, D4 rule 4)."""
    off = (FAR[0], FAR[1]) if depth else (0, 0)
    root = (WING_ROOT[0] + off[0], WING_ROOT[1] + off[1])
    W = T.then(Xf.pose(angle, root, (0.0, 0.0))).then(Xf(spread, 0.0, 0.0, 1.0, root[0] * (1 - spread), 0.0))   # - turns the tip up
    shape = Poly([(root[0], root[1] - 1.4), (root[0] + 6.0, root[1] - 3.8), (root[0] + 14.0, root[1] - 4.4),
                  (root[0] + 20.4, root[1] - 2.8), (root[0] + 22.0, root[1] - 0.2), (root[0] + 19.6, root[1] + 2.4),
                  (root[0] + 11.0, root[1] + 3.0), (root[0] + 3.0, root[1] + 1.8)])

    def shade(i):
        x, y = i.lx - root[0], i.ly - root[1]
        if y < -2.6 + 0.02 * x:
            return 1 if depth else 2                         # the stiff leading edge
        if abs(y - (-0.6 + 0.03 * x)) < 0.5 or (x > 7.0 and abs(y - (1.4 - 0.02 * x)) < 0.45) or (x > 12 and abs(x - 15.0) < 0.5):
            return 1 if depth else 2                         # the veins
        return 2 if depth else (4 if y < 0.6 else 3)
    return cv.part(W, shape, "ivory", shade, rust=0.0)


def elytron(cv, T, angle, depth):
    """A lifted elytron: the shell's half, swung up about its hinge and foreshortened as it spreads out to the side."""
    off = (FAR[0], FAR[1]) if depth else (0, 0)
    hx, hy = HINGE[0] + off[0], HINGE[1] + off[1]
    E = T.then(Xf.pose(-angle, (hx, hy), (0.0, 0.0))).then(Xf(0.86, 0.0, 0.0, 0.5, hx * (1 - 0.86), hy * (1 - 0.5)))
    cx, cy, rx, ry = SHELL
    shape = Ellipse(cx + off[0], cy + off[1], rx, ry)
    if depth:
        return cv.part(E, shape, "oak", flat(2, bevel=False), rust=0.0)
    return cv.part(E, shape, "oak", shell_shade(cx, cy, rx, ry), rust=0.0), E


# --- a frame ---------------------------------------------------------------------------------------------------------------
def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    ox, oy = p.shudder, p.bob
    T = Xf.pose(0.0, (0.0, 0.0), (float(ox), float(oy)))
    F = Xf.pose(0.0, (0.0, 0.0), (float(ox), float(oy + p.front)))
    flying = p.elytra is not None
    # the far side: legs, then (flying) the far wing and elytron
    for key, fk in (("f", "ff"), ("m", "fm"), ("h", "fh")):    # flying, the tucked far legs go behind the body on the
        hx, hy = HIPS[key]                                          # middle plane (the far wing has the far plane to itself)
        leg(mid if flying else far, key, (hx + FAR[0] + ox, hy + FAR[1] + oy), REST[key] + FAR[0], p.feet[fk], 1)
    if p.wing is not None:
        wing(far, T, p.wing[0] - 6.0, 1, p.wing[1])
    # the middle: shell (or, flying, the far elytron, the abdomen under it and the near elytron), pronotum, horns, head.
    # Both lifted elytra stay on this plane, so a beating wing on the near or far plane only passes in front of or
    # behind them (occlusion) instead of repainting a plane's own pixels every beat (check_flicker).
    el = None
    if flying:
        elytron(mid, T, p.elytra + 4.0, 1)
        abdomen(mid, T)
        sh = set()
    else:
        sh = shell(mid, glow, T, p)
    pronotum(mid, F)
    thoracic(mid, F)
    Hx, _ = head(mid, far, F, p)
    if flying:
        el = elytron(mid, T, p.elytra, 0)
    # the near side: legs, then (flying) the near wing and elytron
    for key, nk in (("f", "nf"), ("m", "nm"), ("h", "nh")):    # flying, the tucked legs ride on the middle plane: the
        hx, hy = HIPS[key]                                          # beating wing has the near plane to itself
        leg(mid if flying else near, key, (hx + ox, hy + oy), REST[key], p.feet[nk], 0)
    if p.wing is not None:
        wing(near, T, p.wing[0], 0, p.wing[1])
    for cv in (far, mid, near):
        finish(cv)
    stamps(mid, near, glow, T, F, Hx, sh, el)
    return far, mid, near, glow, Hx.fwd(HORN_TIP)


def stamps(mid, near, glow, T, F, Hx, sh, el):
    """Features under 3 px, placed after finish() (its despeckle would eat them, docs/design/pixel-art-study.md): the
    gloss on the dome and the pronotum, the moss, the spore vein and the eye."""
    def gloss(cv, X, pts, inner):
        for (x, y, col) in pts:
            q = P(X, (x, y))
            if inner is None or q in inner:
                cv.put(q[0], q[1], col)
    pron_gloss = ((-11.6, -14.0, IV[4]), (-10.6, -14.6, IV[4]), (-9.6, -14.8, IV[3]), (-12.4, -13.0, H[6]), (-8.6, -14.8, H[5]))
    gloss(mid, F, pron_gloss, None)
    if sh:
        gloss(mid, T, ((-3.2, -14.2, OK[5]), (-2.2, -15.2, IV[4]), (-1.2, -15.6, IV[4]), (0.0, -15.8, IV[4]), (1.2, -16.0, OK[5]),
                       (-3.8, -13.0, OK[5])), sh)
        c = P(T, CORAL_AT)
        for (dx, dy, k) in CORAL:
            if (c[0] + dx, c[1] + dy) in sh:
                mid.put(c[0] + dx, c[1] + dy, V[k])
        c = P(T, RUNE_AT)
        for (dx, dy) in RUNE:                                  # the vein glows the spores' green, brightest at its heart
            col = G[5] if (dx, dy) == (0, 0) else (G[4] if dx == 0 else G[3])
            mid.put_glow(c[0] + dx, c[1] + dy, col)
            glow.put_glow(c[0] + dx, c[1] + dy, col)
    elif el is not None:
        inner, E = el
        gloss(mid, E, ((-2.2, -15.2, IV[4]), (-1.2, -15.6, IV[4]), (0.0, -15.8, OK[5])), inner)
        c = P(E, RUNE_AT)
        for (dx, dy) in RUNE:                                  # the vein dims while the shell is open
            if (c[0] + dx, c[1] + dy) in inner:
                mid.put(c[0] + dx, c[1] + dy, G[2] if (dx, dy) != (0, 0) else G[3])
    for (x, y, col) in ((-20.2, -14.0, IV[3]), (-20.2, -15.0, H[5]), (-19.4, -11.0, H[5])):   # a glint on the horn's bend
        q = P(Hx, (x, y))
        if mid.px.get(q) in (H[2], H[3]):
            mid.put(q[0], q[1], col)
    e = P(Hx, (-14.4, -8.2))                                   # the eye: glossy black, the spores' green glinting in it
    for (dx, dy, col) in ((0, 0, D[1]), (1, 0, D[0]), (0, 1, D[0]), (1, 1, D[0])):
        mid.put(e[0] + dx, e[1] + dy, col)
    mid.put_glow(e[0], e[1], G[5])
    glow.put_glow(e[0], e[1], G[5])


# --- poses -------------------------------------------------------------------------------------------------------------------
WALK = 8
STRIDE = 8.0            # art px a planted foot slides back over half the cycle: 2 a frame
LIFT = 2.0
CHARGE = 4
CHARGE_STRIDE = 10.0


def gait(k, n, stride, lift):
    t = (k % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def tripods(k, n, stride, lift):
    a, b = gait(k, n, stride, lift), gait(k + n // 2, n, stride, lift)
    return {"nf": a, "fm": a, "nh": a, "ff": b, "nm": b, "fh": b}


def walk_pose(k):
    return Pose(feet=tripods(k, WALK, STRIDE, LIFT), antenna=1 if k % 4 in (1, 2) else 0)


def charge_pose(k):
    return Pose(front=1, head=16.0, feet=tripods(k, CHARGE, CHARGE_STRIDE, LIFT))


TUCK = {"nf": (3.6, 2.6), "ff": (3.6, 2.6), "nm": (0.0, 3.0), "fm": (0.0, 3.0), "nh": (-4.4, 2.6), "fh": (-4.4, 2.6)}

FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Brace0", Pose(front=1, head=9.0)),
             ("Brace1", Pose(front=1, head=18.0, feet={"nf": (2.4, 0.0), "ff": (-1.0, 1.0)}, antenna=1)),
             ("Brace2", Pose(front=1, head=18.0, feet={"nf": (-1.0, 1.0), "ff": (2.4, 0.0)}))]
          + [("Charge%d" % k, charge_pose(k)) for k in range(CHARGE)]
          + [("Toss0", Pose(front=2, head=30.0, feet={"nf": (-2.0, 0.0), "ff": (-2.0, 0.0)})),
             ("Toss1", Pose(front=-1, head=-24.0, feet={"nf": (1.0, 0.0), "ff": (1.0, 0.0), "nh": (-1.0, 0.0), "fh": (-1.0, 0.0)})),
             ("Toss2", Pose(front=0, head=-9.0))]
          + [("Skid", Pose(front=-1, head=4.0, feet={k: (-3.0, 0.0) for k in ("nf", "ff", "nm", "fm", "nh", "fh")}))]
          + [("Dazed0", Pose(front=1, head=12.0, feet={"nf": (-2.0, 0.0), "ff": (-2.0, 0.0), "nh": (2.0, 0.0), "fh": (2.0, 0.0)}, antenna=1)),
             ("Dazed1", Pose(front=1, head=12.0, shudder=1, feet={"nf": (-2.0, 1.0), "ff": (-2.0, 0.0), "nh": (2.0, 0.0), "fh": (2.0, 1.0)}))]
          + [("TakeOff0", Pose(bob=-1, elytra=16.0)),
             ("TakeOff1", Pose(bob=-2, elytra=28.0, wing=(-16.0, 0.6), feet={k: (v[0] * 0.5, v[1] * 0.5) for k, v in TUCK.items()}))]
          + [("Fly%d" % k, Pose(bob=-2, elytra=32.0, wing=(w, 1.0), feet=TUCK))
             for k, w in enumerate((-44.0, -10.0, 26.0, -10.0))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- outputs -----------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Walk0"])
    return {"RhinoBeetle_GoreHorn": crop({q: c for q, c in mid.px.items() if q[0] <= -13 and q[1] <= -3}),
            "RhinoBeetle_GoreShell": crop({q: c for q, c in mid.px.items() if q[0] >= -3}),
            "RhinoBeetle_GoreLeg": crop({q: c for q, c in near.px.items() if q[0] >= 2})}


def write_rig(path, cell, tip):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/jungle/make_rhino_beetle_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Jungle.NPCs",
         "{",
         "\t/// <summary>The Rhino Beetle's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells",
         "\t/// with 2 px under each; the origin is the ground point under its middle. The horn's tip (in the charge) is from the",
         "\t/// origin, facing left.</summary>",
         "\tpublic static class RhinoBeetleRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Brace = %d, BraceFrames = 3, Charge = %d, ChargeFrames = %d, Toss = %d, TossFrames = 3;"
         % (WALK, INDEX["Brace0"], INDEX["Charge0"], CHARGE, INDEX["Toss0"]),
         "\t\tpublic const int Skid = %d, Dazed = %d, DazedFrames = 2, TakeOff = %d, TakeOffFrames = 2, Fly = %d, FlyFrames = 4;"
         % (INDEX["Skid"], INDEX["Dazed0"], INDEX["TakeOff0"], INDEX["Fly0"]),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame and per charge frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d, ChargeStep = %d;" % (round(STRIDE * 2 / (WALK / 2)), round(CHARGE_STRIDE * 2 / (CHARGE / 2))),
         "\t\tpublic const int HornTipX = %d, HornTipY = %d;" % (round(tip[0] * 2), round(tip[1] * 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/RhinoBeetle%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/RhinoBeetle_Glow.png")
    write_rig(OUT + "NPCs/RhinoBeetleRigData.cs", cell, frames[INDEX["Charge0"]][4])
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=4):
    cw, ch = 64, 48
    cols = 6
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (34, 40, 46, 255)), (1, (150, 170, 190, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
                t.alpha_composite(to_image(cv.px, -cw // 2 - 2, -ch + 4, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
