"""Source for the Cursed Conductor, Old Brass Town's boss, its ghost train and its loot (D4), 2026-11-04. Run from the
repo root:

    python -P art/bosses/cursedconductor/make_conductor_art.py [--preview FILE]

Design (user, 2026-11-04: "a new boss called Cursed Conductor (T5, same tier as wall of flesh), a train conductor robot
that calls a spirit of a big flying ghost train to attack the player in different patterns"; the look is my call): a
tall robot train conductor whose curse keeps him floating, his legs long gone: below the ragged hem of his coat he is
a tail of ghost-green mist. An iron head lit from the top-left, two round ghost-green lamp eyes, a bushy steam-white
walrus moustache over a grille jaw, a conductor's cap (indigo, a flat top, a shiny black visor, a brass cord and a
brass badge), a double-breasted indigo uniform coat with two rows of brass buttons, lapels, a white collar, a brass
watch chain and a brass shoulder board; indigo sleeves with brass cuffs, iron hands. In the near hand his brass
whistle on a chain; in the far hand a railway lantern (a brass cap, an iron cage, a globe of ghost flame).
Three-quarter view facing left (D4 rule 13).

Three planes (DepthLayers.DrawWalker grid sheets): far (the far arm and the lantern, a ramp step darker), middle (the
ghost tail, the coat, the head and the cap), near (the near arm and the whistle); the glow sheet holds the eyes, the
ghost tail, the lantern's flame and the whistle's breath, each only where no nearer plane covers it. Stable pixels (D4
rule 17): whole-pixel bobs, the tail built row by row from whole-pixel spans (its colours move with it), bodies lit in
their own space, limbs with their light's turn snapped, far limbs one flat tone.

Frames: Idle x6 (floating: the bob, the tail swaying, the coat's back tail fluttering), Whistle x4 (the whistle up to
the mouth, then blowing: the train's call), Point x2 (the arm out, sending the train), Throw x4 (the lantern swung back,
higher, overhead where its flames fly, forward), Call x2 (the lantern raised high and the whistle blowing: the train's
loop and dive), Tip x3 (the intro: a hand to the visor, the cap raised, a bow), Dying x4 (slumping, the eyes and the
lantern going out, the tail fading).

The ghost train (hostile: ghost green, an ember headlamp): an engine (a boiler with glowing bands, a flared stack, a
steam dome, a cab with a ghost driver in its lit window, three drivers on a connecting rod, a cowcatcher) and a
passenger car (four lit windows, ghost passengers in two, two bogies), each drawn at 9 headings from straight up to
straight down facing right (-90 to +90 degrees, 22.5 apart; the left half is the same frames mirrored at runtime, so
it never rides upside down), drawn at each heading (never rotated as a bitmap). The game draws it translucent, its
windows and headlamp solid from the glow sheets.

Outputs (2x):
    Content/Bosses/CursedConductor/CursedConductor.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Bosses/CursedConductor/CursedConductorRigData.cs     cells, origin, sequences, points, the body box
    Content/Bosses/CursedConductor/CursedConductor_Head_Boss.png  32x32 the map icon
    Content/Bosses/CursedConductor/Projectiles/GhostTrain.png, _Glow.png, _Car.png, _CarGlow.png   9 headings each
    Content/Bosses/CursedConductor/Projectiles/GhostTrain_Rail.png   the telegraph: a level and an upright stretch of
                                                                      ghost track, and a ring marker
    Content/Bosses/CursedConductor/Projectiles/ConductorFlame.png     4 frames of ghost fire
    Content/Bosses/CursedConductor/Items/CursedConductorBag.png       36x36 the treasure bag
    Content/Bosses/CursedConductor/Gores/CursedConductor_GoreCap.png, _GoreHead.png, _GoreLantern.png, _GoreCoat.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "mecharmy"))
from westbots import (RAMP, Xf, Poly, Ellipse, Union, Capsule, box, Canvas, flat, dome, face, P, despeckle, limb, ik,  # noqa: E402
                      I, B, S)
from rig import cyl  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Bosses/CursedConductor/"
A, V, E = RAMP["aether"], RAMP["verd"], RAMP["ember"]

# --- the conductor's rig (1x, y down, the origin at the tip of the ghost tail, facing left) ----------------------------
HEM_Y = -12.0                    # the coat's hem (its tatters reach a row lower)
SH_NEAR = (-5.6, -33.0)
SH_FAR = (5.4, -33.6)
UPPER, FORE = 6.2, 6.0
REST_NEAR = (-7.2, -25.4)
REST_FAR = (11.0, -23.2)
MOUTH = (-7.6, -38.4)            # where the whistle meets the moustache (head at rest)


class Pose:
    def __init__(self, phase=0, bob=0, near=REST_NEAR, far=REST_FAR, whistle="hand", puff=0, flame=2, head=0, cap=0, slump=0,
                 tail=1.0, eyes=3, flutter=0, point=False):
        self.phase, self.bob = phase, bob
        self.near, self.far = near, far
        self.whistle, self.puff = whistle, puff         # "hand" / "mouth"; 0-2 puffs of breath
        self.flame = flame                              # the lantern: 3 bright (telegraph), 2 lit, 1 dim, 0 out
        self.head, self.cap = head, cap                 # whole px the head drops (bow, slump), the cap is raised
        self.slump = slump                              # whole px the whole body sinks
        self.tail = tail                                # the ghost tail's length (1 = to the origin)
        self.eyes = eyes                                # 3 bright .. 0 out
        self.flutter = flutter                          # whole px the coat's back tail swings out
        self.point = point


def fl(v):
    return int(math.floor(v))


# ================================================================================================
# The conductor
# ================================================================================================
def ghost_tail(mid, p):
    """The ghost tail from under the hem down to its tip: one whole-pixel span per row (its colours move with it),
    tapering, trailing behind (to the right) and swaying with the phase, the tip curling; a dark rim, a bright streak
    down its lit side, and a loose wisp curling beside it."""
    top = fl(HEM_Y + p.bob + p.slump) - 1
    tip = 0 if p.tail >= 1.0 else -int(round((1.0 - p.tail) * 9))
    n = max(1, tip - top)
    wave = 2.0 * math.pi * p.phase / 6.0
    for j in range(n + 1):
        y = top + j
        t = j / n
        half = int(round(5.6 * (1.0 - t) ** 0.75))
        sway = 1.8 * t * t * math.sin(wave + t * 2.6)
        cx = int(round(0.6 + 2.2 * t + sway))
        for x in range(cx - half, cx + half + 1):
            if x in (cx - half, cx + half) or y == tip:
                col = V[0] if t > 0.5 else V[1]
            elif x == cx - half + 1 and t < 0.8:
                col = V[3]
            elif x == cx + half - 1 and half >= 3:
                col = V[1]
            else:
                col = V[2]
            mid.put_glow(x, y, col)
    if p.tail >= 0.8:                                              # the loose wisp: three pixels curling off its back
        k = p.phase % 6
        wx = 7 + (0, 1, 1, 0, 0, -1)[k]
        wy = top + 4 + (0, 0, 1, 1, 0, 0)[k]
        for (dx, dy, col) in ((0, 0, V[1]), (1, 1, V[1]), (1, 2, V[0])):
            if (wx + dx, wy + dy) not in mid.px:
                mid.put_glow(wx + dx, wy + dy, col)


def body(mid, p):
    """The coat, the collar, the buttons and the chain, the head and the cap. Returns the shoulders and the mouth."""
    oy = p.bob + p.slump
    f = p.flutter
    hem = [(10.8 + f, -11.0), (8.8 + f, -12.8), (7.0, -10.8), (4.6, -12.6), (2.2, -10.6), (-0.4, -12.4), (-2.8, -10.6),
           (-5.2, -12.4), (-7.4, -10.8), (-9.6, -12.0)]
    pts = [(-6.8, -34.6), (6.2, -34.6), (7.6, -30.0), (7.2, -22.0), (9.6 + f, -16.0)] + hem + [(-9.2, -15.6), (-7.2, -22.0), (-7.8, -30.0)]
    coat = mid.part(Xf(), Poly([(x, y + oy) for (x, y) in pts]), "aether", flat(1), shadow=(1, 1), rust=0.0)
    for y in range(fl(-33.0 + oy), fl(-23.0 + oy)):                 # a fold of light down the chest's lit side
        q = (-7 + (1 if y > fl(-27.0 + oy) else 0), y)
        if q in coat and (q[0] - 1, q[1]) in coat:
            mid.put(q[0], q[1], A[2])
    # the skirt's front opening, off-centre (three-quarter view)
    for y in range(fl(-22.0 + oy), fl(-11.6 + oy)):
        q = (-3 - (1 if y >= fl(-17.0 + oy) else 0), y)
        if q in coat:
            mid.put(q[0], q[1], A[0])
    # the lapels and the white collar
    for pts_, col in ((((-6.4, -34.4), (-3.6, -34.4), (-4.8, -29.6)), A[2]), (((-0.2, -34.4), (2.6, -34.4), (0.6, -30.2)), A[2])):
        for q in mid.raster(Xf(), Poly([(x, y + oy) for (x, y) in pts_])):
            if q in coat:
                mid.put(q[0], q[1], col)
    for (x, y, col) in ((-3, -34, S[2]), (-2, -34, S[2]), (-1, -34, S[1]), (-3, -33, S[1]), (-1, -33, S[0]), (-2, -33, A[0])):
        mid.put(x, y + oy, col)                                    # the collar and a dark tie
    # two rows of brass buttons, and the watch chain to the far pocket
    for row, y in enumerate((-31, -28, -25)):
        for x in (-5, -1):
            if (x, y + oy) in coat:
                mid.put(x, y + oy, B[5] if row == 0 and x == -5 else B[4])
                if (x + 1, y + oy) in coat:
                    mid.put(x + 1, y + oy, B[2])
    for k, (x, y) in enumerate(((0, -24), (1, -23), (2, -23), (3, -23), (4, -24))):
        mid.put(x, y + oy, B[5] if k % 2 == 0 else B[3])
    # the brass shoulder board on the far shoulder
    for (x, y, col) in ((4, -35, B[4]), (5, -35, B[4]), (6, -35, B[3]), (4, -34, B[2]), (5, -34, B[2]), (6, -34, B[1])):
        mid.put(x, y + oy, col)
    # the neck
    mid.part(Xf(), box(-3.2, -36.4 + oy, 0.4, -34.4 + oy), "iron", flat(2), rust=0.0)
    # the head: a rounded iron box, lit from the top-left
    hy = oy + p.head
    hpts = [(-7.2, -44.8), (2.8, -44.8), (3.8, -43.8), (3.8, -37.2), (2.6, -35.8), (-6.4, -35.8), (-7.6, -37.2), (-7.8, -43.6)]
    head = mid.part(Xf(), Poly([(x, y + hy) for (x, y) in hpts]), "iron", dome(-4.0, -42.6 + hy, 7.0, lo=2, hi=4, gain=1.3, bias=0.2,
                    fixed=True), shadow=(1, 1), rust=0.0)
    ey = fl(-41.6 + hy)
    for x in range(-7, 0):
        if (x, ey - 1) in head:
            mid.put(x, ey - 1, I[1])                               # the brow
    eye = {3: (V[3], V[2]), 2: (V[2], V[1]), 1: (V[1], V[1]), 0: (I[1], I[0])}[p.eyes]
    for ex in (-6, -3):                                            # two round lamp eyes
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            col = eye[0] if (dx, dy) == (0, 0) else eye[1]
            if p.eyes > 0:
                mid.put_glow(ex + dx, ey + dy, col)
            else:
                mid.put(ex + dx, ey + dy, col)
    my = ey + 2                                                    # the walrus moustache
    for x in range(-8, 0):
        mid.put(x, my, S[2] if -7 <= x <= -3 else S[1])
        mid.put(x, my + 1, S[1] if -7 <= x <= -2 else S[0])
    for (x, y) in ((-9, my + 1), (-9, my + 2), (-8, my + 2), (0, my + 1), (0, my + 2)):
        mid.put(x, y, S[0])
    for x in range(-6, 1):
        q = (x, my + 2)
        if q in head:
            mid.put(q[0], q[1], I[1] if x % 2 else I[2])              # the grille jaw
    mid.part(Xf(), Ellipse(2.4, -40.4 + hy, 1.3, 1.4), "brass", flat(3), rust=0.0)   # the ear bolt
    # the cap
    cy0 = -44.6 + hy - p.cap
    crown = mid.part(Xf(), Poly([(-7.4, cy0 + 0.4), (3.6, cy0 + 0.4), (4.6, cy0 - 5.4), (-7.0, cy0 - 5.8)]), "aether",
                     flat(1), rust=0.0)
    for x in range(-7, 5):
        q = (x, fl(cy0 - 0.6))
        if q in crown:
            mid.put(q[0], q[1], B[4] if x < -2 else B[3])          # the brass cord
    bx, by = -4, fl(cy0 - 3.0)
    for (dx, dy, col) in ((0, 0, B[5]), (1, 0, B[4]), (0, 1, B[4]), (1, 1, B[2]), (-1, 0, B[3])):
        if (bx + dx, by + dy) in crown:
            mid.put(bx + dx, by + dy, col)                         # the badge on the crown's front
    visor = mid.part(Xf(), Poly([(-12.0, cy0 + 1.2), (-6.6, cy0 - 0.2), (-5.8, cy0 + 1.2), (-7.2, cy0 + 2.0), (-11.4, cy0 + 2.0)]),
                     "iron", flat(1, bevel=False), rust=0.0)
    for x in range(-11, -6):
        q = (x, fl(cy0 + 1.0))
        if q in visor:
            mid.put(q[0], q[1], I[3])                               # its gloss
            break
    del visor
    return (SH_NEAR[0], SH_NEAR[1] + oy), (SH_FAR[0], SH_FAR[1] + oy), (MOUTH[0], MOUTH[1] + hy)


def sleeve_arm(cv, shoulder, hand, depth, bend=1):
    """An indigo sleeve from the shoulder to the hand, a brass cuff, an iron hand. Returns the hand's centre and the
    forearm's direction."""
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, bend)
    limb(cv, shoulder, elbow, 2.2, "aether", depth, lo=1, hi=2)
    limb(cv, elbow, wrist, 2.0, "aether", depth, lo=1, hi=2)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    cv.part(Xf(), Capsule((wrist[0] - u[0] * 1.4, wrist[1] - u[1] * 1.4), (wrist[0] - u[0] * 0.4, wrist[1] - u[1] * 0.4), 2.1), "brass",
            flat(3 - depth, bevel=False), depth=0, rust=0.0)
    fist = (wrist[0] + u[0] * 1.2, wrist[1] + u[1] * 1.2)
    cv.part(Xf(), Ellipse(fist[0], fist[1], 1.8, 1.8), "iron", flat(3 - depth), rust=0.0)
    if depth == 0:
        q = P(Xf(), elbow)
        cv.put(q[0], q[1], A[2])                                   # the elbow's lit crease
    return fist, u


def lantern(cv, hand, flame):
    """A railway lantern hanging from the (far) hand: a brass cap and bail, a glass globe of ghost flame in an iron cage,
    an iron base. Its glass glows (put_glow) unless it is out."""
    x, y = hand
    cv.part(Xf(), Poly([(x - 0.6, y + 0.6), (x + 0.6, y + 0.6), (x + 0.6, y + 1.6), (x - 0.6, y + 1.6)]), "iron", flat(2), rust=0.0)
    cv.part(Xf(), Poly([(x - 1.8, y + 1.4), (x + 1.8, y + 1.4), (x + 2.4, y + 2.8), (x - 2.4, y + 2.8)]), "brass", flat(2), rust=0.0)
    glass = cv.raster(Xf(), Ellipse(x, y + 5.0, 2.5, 2.6))
    cx, cy = fl(x), fl(y + 5.0)
    for q in glass:
        core = abs(q[0] - cx) <= 0 and abs(q[1] - cy) <= 1
        if flame >= 2:
            col = (S[3] if flame == 3 else V[3]) if core else (V[3] if (q[0] - cx) + (q[1] - cy) < 0 else V[2])
            cv.put_glow(q[0], q[1], col)
        elif flame == 1:
            cv.put_glow(q[0], q[1], V[2] if core else V[1])
        else:
            cv.put(q[0], q[1], I[2] if (q[0] - cx) + (q[1] - cy) < -1 else I[1])
    for q in glass:                                               # the cage: two bars across the glass
        if q[0] in (cx - 2, cx + 2) or (q[1] == cy - 2 and q[0] == cx):
            cv.put(q[0], q[1], I[1])
            cv.glow.pop(q, None)
    cv.part(Xf(), box(x - 2.4, y + 7.4, x + 2.4, y + 8.8), "iron", flat(2), rust=0.0)
    return (x, y + 5.0)


def whistle(near, fist, p, mouth):
    """The brass whistle: in the fist at rest (its chain down to the top button), at the mouth when blowing (its breath
    a puff of steam out of its window, in the glow)."""
    fx, fy = fl(fist[0]), fl(fist[1])
    if p.whistle == "mouth":
        mx, my = fl(mouth[0]), fl(mouth[1])
        for (x, y, col) in ((mx - 1, my, B[4]), (mx, my, B[3]), (mx - 2, my, B[5]), (mx - 2, my + 1, B[2]), (mx - 1, my + 1, B[2])):
            near.put(x, y, col)
        puff = ((mx - 3, my - 2), (mx - 4, my - 3), (mx - 3, my - 3))[:max(0, p.puff) + 1] if p.puff else ()
        big = ((mx - 5, my - 4), (mx - 4, my - 4), (mx - 5, my - 3), (mx - 6, my - 5)) if p.puff >= 2 else ()
        for q in tuple(puff) + big:
            near.put_glow(q[0], q[1], S[3] if q in puff[:1] else S[2])
        return (mx - 2, my)
    for (x, y, col) in ((fx - 2, fy, B[4]), (fx - 3, fy, B[5]), (fx - 3, fy + 1, B[2]), (fx - 2, fy + 1, B[2])):
        near.put(x, y, col)
    for (x, y) in ((fx - 1, fy + 2), (fx, fy + 3), (fx + 1, fy + 3)):
        near.put(x, y, B[2])                                       # the chain
    return (fx - 3, fy)


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    ghost_tail(mid, p)
    sh_near, sh_far, mouth = body(mid, p)
    oy = p.bob + p.slump
    ffist, _ = sleeve_arm(far, sh_far, (p.far[0], p.far[1] + oy), 1, bend=1)
    lamp = lantern(far, ffist, p.flame)
    if p.whistle == "mouth":
        hand = (mouth[0] + 1.6, mouth[1] + 1.4)
    else:
        hand = (p.near[0], p.near[1] + oy)
    nfist, u = sleeve_arm(near, sh_near, hand, 0, bend=1)
    tip = whistle(near, nfist, p, mouth)
    finger = None
    if p.point:
        fx, fy = fl(nfist[0] + u[0] * 2.0), fl(nfist[1] + u[1] * 2.0)
        near.put(fx, fy, I[3])
        near.put(fx - 1, fy, I[2])
        finger = (fx - 1, fy)
    for cv in (far, mid, near):
        despeckle(cv)
    for q, col in near.glow.items():
        glow.put_glow(q[0], q[1], col)
    for q, col in mid.glow.items():
        if q not in near.px:
            glow.put_glow(q[0], q[1], col)
    for q, col in far.glow.items():
        if q not in mid.px and q not in near.px:
            glow.put_glow(q[0], q[1], col)
    return far, mid, near, glow, {"lamp": lamp, "whistle": tip, "finger": finger, "mouth": mouth}


IDLE_BOB = (0, -1, -1, -1, 0, 0)
IDLE_FLUTTER = (0, 0, 1, 1, 1, 0)
IDLE_SWAY = (0.0, 0.0, 0.6, 0.6, 0.0, -0.4)


def idle(k, **kw):
    far = (REST_FAR[0] + IDLE_SWAY[k], REST_FAR[1])
    args = dict(phase=k, bob=IDLE_BOB[k], flutter=IDLE_FLUTTER[k], far=far)
    args.update(kw)
    return Pose(**args)


THROW_HANDS = ((12.2, -27.4), (12.6, -37.0), (5.2, -45.6), (10.0, -38.4))
TIP_HANDS = ((-8.2, -44.6), (-8.2, -46.6), (-8.2, -43.8))

FRAMES = ([("Idle%d" % k, idle(k)) for k in range(6)]
          + [("Whistle0", idle(0, near=(-8.8, -31.0))), ("Whistle1", idle(1, whistle="mouth")),
             ("Whistle2", idle(2, whistle="mouth", puff=1)), ("Whistle3", idle(3, whistle="mouth", puff=2))]
          + [("Point%d" % k, idle(2 * k, near=(-17.4, -34.2), point=True)) for k in range(2)]
          + [("Throw%d" % k, idle((k + 1) % 6, far=THROW_HANDS[k], flame=3 if k < 3 else 2)) for k in range(4)]
          + [("Call%d" % k, idle(2 + k, whistle="mouth", puff=1 + k, far=(7.6, -45.6), flame=3)) for k in range(2)]
          + [("Tip0", idle(0, near=TIP_HANDS[0])), ("Tip1", idle(1, near=TIP_HANDS[1], cap=2)),
             ("Tip2", idle(2, near=TIP_HANDS[2], cap=1, head=1))]
          + [("Dying0", Pose(phase=0, head=1, near=(-6.2, -22.6), far=(7.6, -21.0), eyes=2, flame=2)),
             ("Dying1", Pose(phase=1, head=2, slump=1, near=(-5.6, -21.4), far=(7.2, -20.2), eyes=1, flame=1, tail=0.8)),
             ("Dying2", Pose(phase=2, head=3, slump=2, near=(-5.2, -20.6), far=(6.8, -19.6), eyes=1, flame=0, tail=0.55)),
             ("Dying3", Pose(phase=3, head=4, slump=3, near=(-5.0, -20.0), far=(6.6, -19.0), eyes=0, flame=0, tail=0.3))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Whistle", "Point", "Throw", "Call", "Tip", "Dying")


# ================================================================================================
# The ghost train
# ================================================================================================
HEADINGS = [-90.0 + 22.5 * k for k in range(9)]
TRAIN_SCALE = 1.3
ENGINE_CELL = 60
CAR_CELL = 48


def train_xf(heading, cell):
    c = cell / 2.0
    return Xf.pose(heading, (0.0, 0.0), (c, c)).then(Xf(TRAIN_SCALE, 0.0, 0.0, TRAIN_SCALE, 0.0, 0.0))


def ghost_face(lo=1, hi=2):
    return face((-0.5, -0.6, 0.65), lo=lo, hi=hi, gain=1.25, ramp_len=4, snap=22.5)


def wheel(cv, xf, x, y, r):
    cv.part(xf, Ellipse(x, y, r, r), "verd", flat(1, bevel=False), rust=0.0)
    q = P(xf, (x, y))
    cv.put(q[0], q[1], V[3])


def engine(heading):
    """The engine at `heading`, its middle at the cell's centre. Returns the colour and glow canvases."""
    cv, gl = Canvas(), Canvas()
    xf = train_xf(heading, ENGINE_CELL)
    for wx in (-9.6, -4.0, 1.6):
        wheel(cv, xf, wx, 6.0, 2.7)
    wheel(cv, xf, 9.6, 7.2, 1.7)
    for k in range(12):                                            # the connecting rod across the drivers
        q = P(xf, (-9.6 + k * 1.0, 6.0))
        cv.put(q[0], q[1], S[1])
    cv.part(xf, box(-15.8, 2.6, 13.8, 4.2), "verd", flat(1), rust=0.0)
    boiler = cv.part(xf, box(-6.4, -5.4, 12.4, 2.6), "verd", cyl((-6.4, -1.4), (12.4, -1.4), 4.1, lo=1, hi=3, snap=22.5), rust=0.0)
    for bx in (-2.4, 3.0, 8.4):                                    # its bands glow
        for k in range(10):
            q = P(xf, (bx, -5.0 + k * 0.8))
            if q in boiler:
                cv.put_glow(q[0], q[1], V[3])
                gl.put_glow(q[0], q[1], V[3])
    cv.part(xf, Ellipse(12.6, -1.4, 2.0, 3.9), "verd", flat(1), rust=0.0)          # the smokebox's round front
    cv.part(xf, Ellipse(0.4, -5.6, 2.3, 1.5), "verd", flat(2), rust=0.0)           # the steam dome
    cv.part(xf, Poly([(8.2, -5.0), (10.4, -5.0), (10.8, -8.2), (13.0, -12.2), (5.6, -12.2), (7.8, -8.2)]), "verd", ghost_face(),
            rust=0.0)                                                                # the balloon stack
    cv.part(xf, box(5.2, -13.4, 13.4, -12.0), "verd", flat(2), rust=0.0)           # its rim
    cv.part(xf, Ellipse(4.2, -6.0, 1.2, 1.2), "verd", flat(2), rust=0.0)           # the bell
    cv.part(xf, box(-16.0, -9.0, -6.2, 2.6), "verd", ghost_face(), rust=0.0)       # the cab
    cv.part(xf, box(-17.6, -11.0, -5.0, -9.0), "verd", flat(2), rust=0.0)          # its roof
    for q in cv.raster(xf, box(-14.0, -7.2, -8.4, -3.0)):          # the cab window, lit from inside
        cv.put_glow(q[0], q[1], V[3])
        gl.put_glow(q[0], q[1], V[3])
    for (lx, ly) in ((-12.0, -5.6), (-11.4, -5.6), (-12.0, -4.6), (-11.4, -4.6), (-11.0, -3.6), (-12.6, -3.6), (-11.8, -6.6)):
        q = P(xf, (lx, ly))                                        # the ghost driver looking out
        cv.put_glow(q[0], q[1], V[1])
        gl.put_glow(q[0], q[1], V[1])
    cv.part(xf, box(11.4, -9.0, 15.6, -5.2), "verd", flat(1), rust=0.0)          # the box headlamp on the smokebox
    for q in cv.raster(xf, box(13.6, -8.2, 15.4, -6.0)):            # its lens: an ember eye (hostile)
        cv.put_glow(q[0], q[1], E[2])
        gl.put_glow(q[0], q[1], E[2])
    q = P(xf, (14.0, -7.6))
    cv.put_glow(q[0], q[1], E[3])
    gl.put_glow(q[0], q[1], E[3])
    catcher = cv.part(xf, Poly([(13.0, 2.6), (15.8, 2.6), (20.0, 8.6), (13.0, 8.6)]), "verd", flat(1), rust=0.0)
    for k in range(7):                                             # its slats
        q = P(xf, (14.2 + k * 0.9, 4.6 + k * 0.6))
        if q in catcher:
            cv.put(q[0], q[1], V[0])
    return cv, gl


def car(heading):
    """A passenger car at `heading`, its middle at the cell's centre."""
    cv, gl = Canvas(), Canvas()
    xf = train_xf(heading, CAR_CELL)
    for bx in (-8.0, 8.0):                                         # two bogies
        for wx in (-2.4, 2.4):
            wheel(cv, xf, bx + wx, 6.4, 1.8)
        cv.part(xf, box(bx - 4.0, 4.4, bx + 4.0, 5.6), "verd", flat(1, bevel=False), rust=0.0)
    cv.part(xf, box(-12.4, 3.6, 12.4, 5.0), "verd", flat(1), rust=0.0)             # the underframe
    for ex in (-14.6, 13.0):
        cv.part(xf, box(ex, 1.6, ex + 1.6, 3.2), "verd", flat(1, bevel=False), rust=0.0)   # the couplers
    body_ = cv.part(xf, box(-13.0, -6.6, 13.0, 3.8), "verd", ghost_face(), rust=0.0)
    cv.part(xf, Union(box(-13.6, -8.0, 13.6, -6.4), box(-11.2, -9.4, 11.2, -7.6)), "verd", flat(2), rust=0.0)   # the roof
    passengers = {0: ((0.8, -3.4), (1.6, -3.4), (0.8, -2.4), (1.6, -2.4), (0.4, -1.6), (2.0, -1.6)),
                  2: ((0.8, -3.0), (1.6, -3.0), (0.6, -2.0), (1.8, -2.0))}
    for w, wx in enumerate((-10.6, -4.8, 1.0, 6.8)):              # four lit windows, ghost passengers in two
        for q in cv.raster(xf, box(wx, -4.8, wx + 3.6, -1.0)):
            cv.put_glow(q[0], q[1], V[3])
            gl.put_glow(q[0], q[1], V[3])
        for (lx, ly) in passengers.get(w, ()):
            q = P(xf, (wx + lx, ly))
            cv.put_glow(q[0], q[1], V[1])
            gl.put_glow(q[0], q[1], V[1])
    for k in range(26):                                            # the waist band under the windows
        q = P(xf, (-12.6 + k, 0.6))
        if q in body_:
            cv.put(q[0], q[1], V[1])
    return cv, gl


def train_sheets(fn, cell):
    frames, glows = [], []
    for h in HEADINGS:
        cv, gl = fn(h)
        for (x, y) in list(cv.px):
            if not (0 <= x < cell and 0 <= y < cell):
                raise SystemExit("train pixel (%d, %d) outside its %d cell at heading %.1f" % (x, y, cell, h))
        frames.append(to_image(cv.px, 0, 0, cell, cell))
        glows.append(to_image(gl.glow, 0, 0, cell, cell))
    return vertical(frames), vertical(glows)


RAIL_CELL = 21


def rails():
    """The telegraph pieces (1x 21x21 cells): a level stretch of ghost track (two rails 20 px apart, the band the train
    fills, with a sleeper), the same upright, and a ring marker (a ghost-light dot) for the loop."""
    level_, upright, dot = Canvas(), Canvas(), Canvas()
    for x in range(8):
        for (y, col) in ((0, V[2]), (1, V[0]), (19, V[0]), (20, V[2])):
            level_.put(x, y, col)
            upright.put(y, x, col)
    for y in range(2, 19, 3):
        level_.put(3, y, V[1])
        level_.put(4, y, V[1])
        upright.put(y, 3, V[1])
        upright.put(y, 4, V[1])
    for (x, y, col) in ((10, 9, V[2]), (9, 10, V[2]), (10, 10, V[3]), (11, 10, V[2]), (10, 11, V[2]), (9, 9, V[1]), (11, 11, V[1]),
                        (11, 9, V[1]), (9, 11, V[1])):
        dot.put(x, y, col)
    return vertical([to_image(c.px, 0, 0, RAIL_CELL, RAIL_CELL) for c in (level_, upright, dot)])


FLAME = 12
FLAME_FRAMES = 4


# Ghost fire, drawn by hand (12x12 at 1x): a = dark rim (verd 0), b = flame (verd 2), c = bright flame (verd 3), d = the
# white-hot heart (steam 3). Its three tongues lick up in turn; the heart stays put (stable pixels).
FLAME_ART = (
    ("....a.......",
     "...aba...a..",
     "...abba.aba.",
     "..abcbaabba.",
     "..abccbbcba.",
     ".abccccccba.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
    (".......a....",
     "..a...aba...",
     ".aba.abba...",
     ".abbaabcba..",
     ".abcbbccba..",
     ".abccccccba.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
    ("......a.....",
     ".....aba....",
     "..a..abba...",
     ".aba.abcba..",
     ".abbabccba..",
     ".abcbcccbaa.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
    ("............",
     "...a....a...",
     "..aba..aba..",
     "..abba.abba.",
     "..abcbabcba.",
     ".abccbbccba.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
)


def flame(k):
    cv = Canvas()
    cols = {"a": V[0], "b": V[2], "c": V[3], "d": S[3]}
    for y, row in enumerate(FLAME_ART[k]):
        for x, ch in enumerate(row):
            if ch in cols:
                cv.put(x, y, cols[ch])
    return to_image(cv.px, 0, 0, FLAME, FLAME)


# ================================================================================================
# The bag, the map icon, the gores
# ================================================================================================
def treasure_bag():
    """18x18: an indigo sack tied with a brass chain, the Conductor's whistle hanging from it, ghost mist curling out."""
    cv = Canvas()
    X = Xf()
    cv.part(X, Union(Ellipse(9.0, 11.8, 7.2, 5.6), Poly([(5.8, 6.2), (12.2, 6.2), (13.8, 9.0), (4.2, 9.0)])), "aether",
            dome(6.0, 8.6, 10.0, lo=1, hi=2, gain=1.3, bias=0.15), shadow=(1, 1), rust=0.0)
    cv.part(X, Poly([(6.6, 2.4), (11.4, 2.4), (12.2, 6.2), (5.8, 6.2)]), "aether", flat(2), rust=0.0)
    for x in range(5, 14):
        cv.put(x, 6, B[4] if x % 2 else B[3])                      # the brass chain round its neck
    for (x, y, col) in ((10, 7, B[2]), (10, 8, B[2]), (11, 9, B[4]), (12, 9, B[5]), (13, 9, B[3]), (11, 10, B[2]), (12, 10, B[2])):
        cv.put(x, y, col)                                          # the whistle hanging from it
    for (x, y, col) in ((8, 1, V[2]), (9, 0, V[3]), (7, 0, V[1]), (10, 1, V[2]), (9, 1, V[3])):
        cv.put(x, y, col)                                          # ghost mist out of its mouth
    for (x, y) in ((6, 12), (6, 13), (7, 14)):
        cv.put(x, y, A[2])                                          # a lit fold
    return to_image(cv.px, 0, 0, 18, 18)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def head_icon(mid):
    """16x16 (32 in game): the head and the cap of the Idle pose."""
    px = {q: c for q, c in mid.px.items() if q[1] <= -35 and q[0] >= -12}
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    im.alpha_composite(crop(px), ((16 - w) // 2, (16 - h) // 2))
    return im


def gores(far, mid):
    cap = {q: c for q, c in mid.px.items() if q[1] <= -45 or (q[0] <= -8 and q[1] <= -43)}          # the crown and the visor
    head = {q: c for q, c in mid.px.items() if -45 < q[1] <= -35 and q[0] >= -10 and q not in cap}
    coat = {q: c for q, c in mid.px.items() if -35 < q[1] <= -10 and c in A + B + S}
    lamp = {q: c for q, c in far.px.items() if q[1] >= -24 and q[0] >= 5}
    return {"CursedConductor_GoreCap": crop(cap), "CursedConductor_GoreHead": crop(head), "CursedConductor_GoreCoat": crop(coat),
            "CursedConductor_GoreLantern": crop(lamp)}


# ================================================================================================
# Export
# ================================================================================================
def body_box(mid):
    """The hitbox (1x): the coat, the head and the cap (not the tail, not the visor's tip): left, right, top, hem."""
    pts = [q for q in mid.px if q[1] <= HEM_Y]
    xs = sorted(x for (x, _) in pts)
    return xs[2], xs[-1] + 1, min(y for (_, y) in pts), int(HEM_Y)


COLUMNS = 2                      # the grid wraps: 25 frames in one column would be 2750 px tall (D0: textures <= 2048)


def grid_columns(canvases, cell, glow=False):
    """grid_layer's equal cells, wrapped into COLUMNS columns, 1 px (2 px in game) right of and under each cell
    (DepthLayers.DrawCell with columns); every pixel must fit in its cell."""
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((w + 1) * COLUMNS, (h + 1) * rows), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        one = grid_layer([cv], cell, glow=glow)
        out.alpha_composite(one.crop((0, 0, w, h)), ((k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)))
    return out


def write_rig(path, cell, frames):
    w, h, ox, oy = cell
    idle = frames[INDEX["Idle0"]]
    left, right, top, hem = body_box(idle[1])
    pts = idle[4]
    throw = frames[INDEX["Throw2"]][4]["lamp"]
    blow = frames[INDEX["Whistle2"]][4]["whistle"]
    call = frames[INDEX["Call0"]][4]["lamp"]
    finger = frames[INDEX["Point0"]][4]["finger"]
    eyes = (-4.5, -40.6)
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def pt(name, p):
        return "%sX = %d, %sY = %d" % (name, round(p[0] * 2), name, round(p[1] * 2))
    L = ["// <auto-generated> by art/bosses/cursedconductor/make_conductor_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Bosses.CursedConductor",
         "{",
         "\t/// <summary>The Cursed Conductor's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal",
         "\t/// cells in <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is the tip of his ghost tail.",
         "\t/// Body* is his hitbox from the origin (the coat,",
         "\t/// the head and the cap); the points are from the origin, facing left: the lantern at rest, thrown (Throw2) and",
         "\t/// raised (Call0), the whistle blowing (Whistle2), the pointing finger (Point0), the eyes. The ghost train's sheets",
         "\t/// hold <see cref=\"Headings\"/> headings each (straight up to straight down, facing right, 22.5 degrees apart).</summary>",
         "\tpublic static class CursedConductorRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
         % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
         "\t\tpublic const int %s;" % ", ".join(seq[:4]),
         "\t\tpublic const int %s;" % ", ".join(seq[4:]),
         "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, HemY = %d;" % (left * 2, right * 2, top * 2, hem * 2),
         "\t\tpublic const int %s, %s;" % (pt("Lantern", pts["lamp"]), pt("Throw", throw)),
         "\t\tpublic const int %s, %s;" % (pt("Raised", call), pt("Whistle", blow)),
         "\t\tpublic const int %s, %s;" % (pt("Finger", finger), pt("Eyes", eyes)),
         "\t\tpublic const int Headings = %d, EngineCell = %d, CarCell = %d, RailCell = %d, FlameCell = %d, FlameFrames = %d;"
         % (len(HEADINGS), ENGINE_CELL * 2, CAR_CELL * 2, RAIL_CELL * 2, FLAME * 2, FLAME_FRAMES),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_columns([fr[idx] for fr in frames], cell), OUT + "CursedConductor%s.png" % suffix)
    export(grid_columns([fr[3] for fr in frames], cell, glow=True), OUT + "CursedConductor_Glow.png")
    write_rig(OUT + "CursedConductorRigData.cs", cell, frames)
    export(head_icon(frames[0][1]), OUT + "CursedConductor_Head_Boss.png")
    sheet, glow = train_sheets(engine, ENGINE_CELL)
    export(sheet, OUT + "Projectiles/GhostTrain.png")
    export(glow, OUT + "Projectiles/GhostTrain_Glow.png")
    sheet, glow = train_sheets(car, CAR_CELL)
    export(sheet, OUT + "Projectiles/GhostTrain_Car.png")
    export(glow, OUT + "Projectiles/GhostTrain_CarGlow.png")
    export(rails(), OUT + "Projectiles/GhostTrain_Rail.png")
    export(vertical([flame(k) for k in range(FLAME_FRAMES)]), OUT + "Projectiles/ConductorFlame.png")
    export(treasure_bag(), OUT + "Items/CursedConductorBag.png")
    for name, im in gores(frames[0][0], frames[0][1]).items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    """Every frame on a dark and a light backdrop, the train's headings, the flame and the bag, 3x."""
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    w, h, ox, oy = cell
    cols = 9
    rows = (len(FRAMES) + cols - 1) // cols
    panels = []
    for bg in ((36, 40, 48, 255), (150, 180, 210, 255)):
        tile = Image.new("RGBA", (w * cols, h * rows), bg)
        for k, fr in enumerate(frames):
            t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            for cv in fr[:3]:
                t.alpha_composite(to_image(cv.px, -ox, -oy, w, h))
            t.alpha_composite(to_image(fr[3].glow, -ox, -oy, w, h))
            tile.alpha_composite(t, ((k % cols) * w, (k // cols) * h))
        panels.append(tile)
    trains = Image.new("RGBA", (ENGINE_CELL * 9 + 8, ENGINE_CELL + CAR_CELL + 4), (36, 40, 48, 255))
    for k, hd in enumerate(HEADINGS):
        cv, _ = engine(hd)
        trains.alpha_composite(to_image(cv.px, 0, 0, ENGINE_CELL, ENGINE_CELL), (k * ENGINE_CELL, 0))
        cv, _ = car(hd)
        trains.alpha_composite(to_image(cv.px, 0, 0, CAR_CELL, CAR_CELL), (k * ENGINE_CELL, ENGINE_CELL + 2))
    extras = Image.new("RGBA", (trains.width, 24), (36, 40, 48, 255))
    for k in range(FLAME_FRAMES):
        extras.alpha_composite(flame(k), (2 + k * 12, 2))
    extras.alpha_composite(treasure_bag(), (60, 2))
    extras.alpha_composite(rails(), (90, 0)) if False else None
    W = max(panels[0].width, trains.width)
    sheet = Image.new("RGBA", (W, panels[0].height * 2 + trains.height + extras.height), (0, 0, 0, 255))
    sheet.paste(panels[0], (0, 0))
    sheet.paste(panels[1], (0, panels[0].height))
    sheet.paste(trains, (0, panels[0].height * 2))
    sheet.paste(extras, (0, panels[0].height * 2 + trains.height))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)
    print("preview", path, cell)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
