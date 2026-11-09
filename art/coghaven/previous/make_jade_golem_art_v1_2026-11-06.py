"""Source for the Jade Golem, a Coghaven enemy (D4), and its jade ray, 2026-11-06. Run from the repo root:

    python -P art/coghaven/make_jade_golem_art.py [--preview FILE [--frames A,B]]

Design (user, 2026-11-06, from the user's reference image: a hulking green jade stone golem with a Moai-like bearded head,
glowing green eyes, huge fists and glowing rune bracelets; "a slow tanky jade golem that does heavy contact damage and
stops every 5 seconds to charge a precise jade green electric ray that does great damage at great range; he should
charge for 1.5 seconds, and his arm should point in the direction he is aiming, following the targeted player
dynamically"). A barrel torso of polished jade (the Ghost ramp, the island's jade bricks' own) facing the screen (the
user's 2026-11-06 rule), cracked here and there, with a bronze cog over its glowing jade heart (the Coghaven steampunk
touch) on the torso's axis; boulder shoulders, jade crystals growing out of the hunched back; a Moai head set low and
forward between the shoulders, three-quarter view facing left (D4 rule 13): a heavy brow over two glowing eyes, a long
nose, pursed lips, a long ear, a squared beard of rough jade (Verdigris) carved in strands; long gorilla arms ending in
huge fists, a bronze bracelet with glowing runes on each wrist; short pillar legs on blocky feet of rough jade. Lit from
the top-left; outlines in each ramp's darkest shade.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and arm, one tone a step darker), middle (the near
leg, the body, the head), near (the near arm, its bracelet and the near shoulder boulder over it); the glow sheet holds
the eyes, the heart and the bracelet runes (brightened in game while he charges). Stable pixels (D4 rule 17): the body is
built in its own space and placed by whole-pixel bobs; limbs are lit with their light's turn snapped; far limbs are one
tone; the aiming arm is rendered here for every angle (never rotated at runtime, D4 rule 14).

Frames: Walk x8 (slow, heavy steps), Idle x2, Aim x13 (the near arm pointed from straight up to straight down in 15
degree steps, the legs braced): in game the arm steps through them to follow its target.

Outputs:
    Content/Coghaven/NPCs/JadeGolem.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/JadeGolemRigData.cs     cells, origin, frame runs, the walk step, the fist per aim frame
    Content/Coghaven/Gores/JadeGolem_GoreHead.png, _GoreFist.png, _GoreHeart.png, _GoreCrystal.png
    Content/Coghaven/Projectiles/JadeRay.png       16x70: the ray's electric nodes, three 16x16 crackles 2 px apart
    Content/Coghaven/Projectiles/JadeRay_Orb.png   24x130: the charge gathering in his fist, five 24x24 sizes 2 px apart
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
from westbots import (RAMP, Xf, Poly, Ellipse, box, Canvas, flat, dome, face, P, finish, limb, ik, glint, texture, G)  # noqa: E402
from make_trashtr0m_art import export, to_image, GROUND_CLIP  # noqa: E402
from make_mecharmy_art import fit_cell  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
JD = RAMP["ghost"]                                   # polished jade (0 outline .. 5 the glow's colour)
VD = RAMP["verd"]                                    # rough jade
WHITE = RAMP["steam"][3]
HIP_NEAR, HIP_FAR = (-4.0, -12.0), (4.2, -12.4)
THIGH, SHIN = 4.8, 4.4
SHOULDER_NEAR, SHOULDER_FAR = (-12.0, -30.0), (12.0, -30.4)
UPPER, FORE, FIST_REACH = 8.0, 10.0, 3.2
COLUMNS = 2                                          # 23 tall cells in one column pass 2048 px (the texture limit)
AIM_MIN, AIM_STEP, AIM_FRAMES = -90, 15, 13          # degrees below "forward"; -90 straight up, +90 straight down
JADE_LO, JADE_HI = 1, 3                              # deep jade masses; shade 4 is for highlights, 5 and white for the glow

# Hand-placed details. Digits are gilt shades; u..w jade shades 3..5, X white: v, w and X glow.
HEART = ["....6....",
         "..35763..",
         ".38uvu53.",
         ".7uwXwu4.",
         "57vXXXv64",
         ".6uwXwu3.",
         ".37uvu42.",
         "..24432..",
         "....3...."]
GLOWING = set("vwX")
# The Moai head and its beard, hand-placed (a 10-px face rasterised from polygons lost its eyes to the despeckle pass and
# read as a box): facing left in three-quarter view, lit from the top-left. a..f jade shades 0..5; p..s rough jade
# (Verdigris) 0..3; E, g the eyes' glow (white, jade 5). From the front: the far eye peeking past the lit nose bridge,
# the near eye in its deep socket under the heavy brow, the long ear at the back; the nose's tip, the pouting lip and the
# chin jut forward; the beard hangs in three carved tiers. Stamped after the finishing pass, so no pixel of it moves.
HEAD_ART = ["....aaaaaaa..",
            "...adeeedcca.",
            "...aeedddccba",
            "..aeedddcccba",
            ".aeeeeedddcba",
            ".abbbbbbcbcba",
            ".agdEgbccbcba",
            ".abdbbcccbcba",
            "aedccccccbcba",
            ".abbcccccbcba",
            "aeddcccccbba.",
            ".abbbbcccbba.",
            ".aeddcccbba..",
            ".psrrrqqqp...",
            ".pqqqqqqqp...",
            "..psrrrqqp...",
            "..pqqqqqp....",
            "...psrrqp....",
            "....pppp....."]
HEAD_AT = (-6.0, -42.0)                              # the stencil's top-left in the body's own space
CRACKS = [(-9.0, -27.5), (-8.2, -26.5), (-8.2, -25.5), (-8.9, -24.5), (6.5, -21.0), (7.4, -20.0), (7.4, -19.0), (8.2, -18.0),
          (-6.5, -17.5), (-5.6, -16.5), (5.0, -30.5), (5.8, -29.5), (9.0, -26.5), (9.8, -25.5), (9.8, -24.5), (10.5, -23.5),
          (2.5, -15.5), (3.4, -14.5), (4.2, -13.5)]
CRYSTALS = [(9.4, -33.6, 8.4, 2.6, 1.4), (13.0, -32.6, 6.0, 2.1, 2.4), (6.8, -33.0, 5.2, 1.9, 0.4)]   # base x, y, height, half width, lean


def stamp(cv, glow, rows, x0, y0):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            if ch.isdigit():
                cv.put(x0 + dx, y0 + dy, G[int(ch)])
                continue
            col = {"u": JD[3], "v": JD[4], "w": JD[5], "X": WHITE}[ch]
            if ch in GLOWING:
                cv.put_glow(x0 + dx, y0 + dy, col)
                glow.put_glow(x0 + dx, y0 + dy, col)
            else:
                cv.put(x0 + dx, y0 + dy, col)


def stamp_head(cv, glow, x0, y0):
    jade = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5}
    rough = {"p": 0, "q": 1, "r": 2, "s": 3}
    for dy, row in enumerate(HEAD_ART):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + dx, y0 + dy
            if ch in ("E", "g"):
                col = WHITE if ch == "E" else JD[5]
                cv.put_glow(x, y, col)
                glow.put_glow(x, y, col)
            elif ch in jade:
                cv.put(x, y, JD[jade[ch]])
            else:
                cv.put(x, y, VD[rough[ch]])


class Pose:
    def __init__(self, bob=0, near_foot=(-4.6, 0.0), far_foot=(4.8, 0.0), near_swing=0.0, far_swing=0.0, aim=None):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_swing, self.far_swing = near_swing, far_swing
        self.aim = aim                               # None, or the near arm's angle in degrees below forward


def leg(cv, hip, foot, depth):
    """A short pillar leg on a block foot of rough jade (lifted foot[1] px)."""
    ankle = (foot[0], -3.0 - foot[1])
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)
    limb(cv, hip, knee, 3.9, "ghost", depth, lo=JADE_LO, hi=JADE_HI)
    limb(cv, knee, ankle, 3.6, "ghost", depth, lo=JADE_LO, hi=JADE_HI)
    fx, fy = ankle[0], ankle[1] + 3.0
    shade = flat(1, bevel=False) if depth else face((-0.5, -0.6, 0.7), lo=1, hi=3, ramp_len=4, fixed=True)
    cv.part(Xf(), Poly([(fx - 4.6, fy - 3.6), (fx + 2.8, fy - 3.8), (fx + 3.2, fy), (fx - 5.0, fy)]), "verd", shade, rust=0.0)
    if depth == 0:
        q = P(Xf(), (fx - 2.4, fy - 1.6))
        cv.put(q[0], q[1], VD[0])                    # a toe split
        cv.put(q[0], q[1] + 1, VD[0])
    return knee


def body(mid, glow, p):
    """The middle plane in the body's own space, placed by one whole-pixel translation (D4 rule 17)."""
    oy = p.bob
    bx = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))

    def at(x, y):
        return P(bx, (x, y))
    # the pelvis (rough jade) and the barrel torso (polished jade)
    mid.part(bx, Poly([(-8.6, -16.6), (8.2, -16.6), (7.2, -10.4), (-7.8, -10.4)]), "verd",
             texture(face((-0.5, -0.5, 0.7), lo=1, hi=2, ramp_len=4, fixed=True), "speckle", seed=53, density=0.2, lo=1, hi=3), rust=0.0)
    tin = mid.part(bx, Ellipse(0.0, -24.0, 12.4, 10.6), "ghost",
                   texture(dome(-4.4, -30.0, 14.0, lo=JADE_LO, hi=JADE_HI, gain=1.3, bias=0.15, fixed=True, dither=0.1), "speckle", seed=41,
                           density=0.16, lo=JADE_LO, hi=JADE_HI), shadow=(1, 1), rust=0.0)
    for (gx, gy) in ((-6.4, -31.6), (-8.6, -30.2)):
        q = at(gx, gy)
        if q in tin:
            mid.put(q[0], q[1], JD[4])               # the polish catching the light
    for (x, y) in CRACKS:
        q = at(x, y)
        if q in tin:
            mid.put(q[0], q[1], JD[1])
            if (q[0] + 1, q[1]) in tin:
                mid.put(q[0] + 1, q[1], JD[3])       # the crack's lit lip
    # the far shoulder boulder (the near one sits on the near plane, over the arm)
    sin_ = mid.part(bx, Ellipse(SHOULDER_FAR[0], SHOULDER_FAR[1] - 0.6, 5.2, 4.6), "ghost",
                    texture(dome(SHOULDER_FAR[0] - 1.8, SHOULDER_FAR[1] - 3.0, 6.0, lo=JADE_LO, hi=JADE_HI, fixed=True), "speckle", seed=43,
                            density=0.16, lo=JADE_LO, hi=JADE_HI), rust=0.0)
    gq = at(SHOULDER_FAR[0] - 2.0, SHOULDER_FAR[1] - 3.2)
    if gq in sin_:
        mid.put(gq[0], gq[1], JD[4])
    # jade crystals growing out of the far shoulder: a lit facet and a shadowed one, split along each crystal's axis
    for (cx, cy, h, w, lean) in CRYSTALS:
        cin = mid.part(bx, Poly([(cx - w, cy), (cx + lean, cy - h), (cx + w, cy)]), "ghost",
                       face((-0.6, -0.5, 0.6), lo=3, hi=4, ramp_len=6, gain=1.35, fixed=True), rust=0.0)
        for (x, y) in cin:
            ly = y - oy + 0.5
            axis = cx + lean * (cy - ly) / h
            if x + 0.5 > axis + 0.3:
                mid.put(x, y, JD[2])
            elif x + 0.5 > axis - 0.9:
                mid.put(x, y, JD[5])                 # the ridge catching the light
    x0, y0 = at(-4.4, -24.0)
    stamp(mid, glow, HEART, x0, y0)
    return ((SHOULDER_NEAR[0], SHOULDER_NEAR[1] + oy), (SHOULDER_FAR[0], SHOULDER_FAR[1] + oy))


def arm(cv, glow, shoulder, d, depth, swing=0.0, hanging=True):
    """A long stone arm from the shoulder: hanging (a slight bend, the huge fist by the knee) or pointed along the unit
    direction `d` (aiming). Returns the fist's centre and the point the ray leaves from (the knuckles)."""
    sx, sy = shoulder
    side = -1.0 if d[0] < 0 else 1.0
    if hanging:
        elbow = (sx + side * 2.4 + swing * 0.3, sy + 7.6)
        wrist = (elbow[0] - side * 0.6 + swing, elbow[1] + 9.98)
        u = (0.0, 1.0)
        front = (side, 0.0)                          # a hanging fist shows its knuckles forward
    else:
        elbow = (sx + d[0] * UPPER, sy + d[1] * UPPER)
        wrist = (elbow[0] + d[0] * FORE, elbow[1] + d[1] * FORE)
        u = front = d
    fist = (wrist[0] + u[0] * FIST_REACH, wrist[1] + u[1] * FIST_REACH)
    limb(cv, shoulder, elbow, 3.4, "ghost", depth, lo=JADE_LO, hi=JADE_HI)
    limb(cv, elbow, wrist, 3.9, "ghost", depth, lo=JADE_LO, hi=JADE_HI)
    # the bronze bracelet: a band round the forearm just above the fist, its runes glowing (near arm only: a far rune
    # would flicker, D4 rule 17); the fist goes on over its lower edge
    b0 = (wrist[0] - u[0] * 2.8, wrist[1] - u[1] * 2.8)
    b1 = (wrist[0] - u[0] * 0.6, wrist[1] - u[1] * 0.6)
    limb(cv, b0, b1, 4.4, "gilt", depth, lo=3, hi=8)
    shade = flat(2, bevel=False) if depth else dome(fist[0] - 1.8, fist[1] - 2.0, 5.2, lo=JADE_LO, hi=JADE_HI + 1, fixed=True)
    fin = cv.part(Xf(), Ellipse(fist[0], fist[1], 4.4, 4.1), "ghost", shade, rust=0.0)
    if depth == 0:
        n = (-u[1], u[0])
        mid_b = ((b0[0] + b1[0]) * 0.5, (b0[1] + b1[1]) * 0.5)
        for t in (-1.8, 0.0, 1.8):
            q = P(Xf(), (mid_b[0] + n[0] * t, mid_b[1] + n[1] * t))
            cv.put_glow(q[0], q[1], JD[5] if t else WHITE)
            glow.put_glow(q[0], q[1], JD[5] if t else WHITE)
        fn = (-front[1], front[0])
        for t in (-1.6, 0.0, 1.6):                   # knuckle lines across the fist's front
            q = P(Xf(), (fist[0] + front[0] * 2.4 + fn[0] * t, fist[1] + front[1] * 2.4 + fn[1] * t))
            if q in fin:
                cv.put(q[0], q[1], JD[1])
                r = (q[0] - round(front[0]), q[1] - round(front[1]))
                if r in fin:
                    cv.put(r[0], r[1], JD[3])
    muzzle = (fist[0] + u[0] * 4.6, fist[1] + u[1] * 4.6)
    return fist, muzzle


def aim_dir(deg):
    a = math.radians(deg)
    return (-math.cos(a), math.sin(a))               # facing left: forward is -x, positive angles point down


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    leg(mid, (HIP_NEAR[0], HIP_NEAR[1] + p.bob), p.near_foot, 0)
    sh_near, sh_far = body(mid, glow, p)
    leg(far, (HIP_FAR[0], HIP_FAR[1] + p.bob), p.far_foot, 1)
    arm(far, glow, sh_far, (1.0, 0.0), 1, swing=p.far_swing)
    if p.aim is None:
        _, muzzle = arm(near, glow, sh_near, (-1.0, 0.0), 0, swing=p.near_swing)
    else:
        _, muzzle = arm(near, glow, sh_near, aim_dir(p.aim), 0, hanging=False)
    sx, sy = sh_near
    nin = near.part(Xf(), Ellipse(sx - 0.2, sy - 0.6, 5.2, 4.6), "ghost",
                    texture(dome(sx - 1.8, sy - 3.0, 6.0, lo=JADE_LO, hi=JADE_HI, fixed=True), "speckle", seed=47, density=0.16, lo=JADE_LO,
                            hi=JADE_HI), rust=0.0)
    gq = P(Xf(), (sx - 2.2, sy - 3.2))
    if gq in nin:
        near.put(gq[0], gq[1], JD[4])                # the boulder's polish
    for cv in (far, mid, near):
        finish(cv)
    hx0, hy0 = P(Xf(), (HEAD_AT[0], HEAD_AT[1] + p.bob))
    stamp_head(mid, glow, hx0, hy0)
    return far, mid, near, glow, muzzle


WALK = 8
STRIDE = 5.0


def cycle_foot(phase, n, stride, lift):
    t = (phase % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    nf, ff = cycle_foot(k, WALK, STRIDE, 1.6), cycle_foot(k + WALK // 2, WALK, STRIDE, 1.6)
    swing = math.sin(2 * math.pi * k / WALK) * 1.4
    return Pose(bob=1 if k % 4 in (0, 1) else 0, near_foot=(nf[0] - 4.4, nf[1]), far_foot=(ff[0] + 4.6, ff[1]),
                near_swing=swing, far_swing=-swing)


STANCE = dict(near_foot=(-5.6, 0.0), far_foot=(5.6, 0.0))
FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Idle0", Pose(**STANCE)), ("Idle1", Pose(bob=1, **STANCE))]
          + [("Aim%d" % k, Pose(aim=AIM_MIN + AIM_STEP * k, **STANCE)) for k in range(AIM_FRAMES)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ------------------------------------------------------------------------------------------------------------------------
# The ray: electric nodes (drawn unrotated along the beam in game, D4 rule 14) and the charge gathering in the fist
# ------------------------------------------------------------------------------------------------------------------------
NODES = [["........",
          "...v....",
          "..vwv.v.",
          ".vwXwvw.",
          "..wXXwv.",
          ".vwwXv..",
          "..v.vv..",
          "........"],
         ["........",
          ".v...v..",
          "..vwvw..",
          "..wXXwv.",
          ".vwXXw..",
          "..vwwv..",
          "...v..v.",
          "........"],
         ["........",
          "....v...",
          ".v.vwv..",
          "..wXXwv.",
          ".vwXXwv.",
          "..vwXv..",
          "..v..v..",
          "........"]]
NODE_COL = {"u": JD[3], "v": JD[4], "w": JD[5], "X": WHITE}
ORB_CELL, ORB_SIZES = 12, (1.6, 2.4, 3.2, 4.2, 5.2)


def node_image(rows):
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), NODE_COL[ch] + (255,))
    return im


def orb_image(r):
    """The charge in the fist: a white core in jade rings, a few sparks round it (crisp pixels, no blending)."""
    im = Image.new("RGBA", (ORB_CELL, ORB_CELL), (0, 0, 0, 0))
    c = (ORB_CELL - 1) / 2.0
    for y in range(ORB_CELL):
        for x in range(ORB_CELL):
            d = math.hypot(x - c, y - c)
            col = None
            if d <= r * 0.45:
                col = WHITE
            elif d <= r * 0.75:
                col = JD[5]
            elif d <= r:
                col = JD[4]
            elif d <= r + 1.2 and r > 2.0 and (x * 7 + y * 13) % 5 == 0:
                col = JD[3]                          # sparks
            if col:
                im.putpixel((x, y), col + (255,))
    return im


def sheet(images, pad=1):
    w, h = images[0].size
    out = Image.new("RGBA", (w, (h + pad) * len(images) - pad), (0, 0, 0, 0))
    for k, im in enumerate(images):
        out.alpha_composite(im, (0, k * (h + pad)))
    return out


def export_ray():
    export(sheet([node_image(n) for n in NODES]), OUT + "Projectiles/JadeRay.png")
    export(sheet([orb_image(r) for r in ORB_SIZES]), OUT + "Projectiles/JadeRay_Orb.png")


# ------------------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    head_cv = Canvas()
    stamp_head(head_cv, Canvas(), 0, 0)
    head_px = head_cv.px
    fist = Canvas()
    arm(fist, Canvas(), (0.0, 0.0), (-1.0, 0.0), 0)
    fist_px = {q: c for q, c in fist.px.items() if q[1] >= 10}
    heart = Canvas()
    stamp(heart, Canvas(), HEART, 0, 0)
    crystal = Canvas()
    crystal.part(Xf(), Poly([(-1.8, 0.0), (1.0, -7.0), (1.8, 0.0)]), "ghost", face((-0.6, -0.5, 0.6), lo=2, hi=5, ramp_len=6, fixed=True),
                 rust=0.0)
    finish(crystal)
    return {"JadeGolem_GoreHead": crop(head_px), "JadeGolem_GoreFist": crop(fist_px), "JadeGolem_GoreHeart": crop(heart.px),
            "JadeGolem_GoreCrystal": crop(crystal.px)}


def write_rig(path, cell, muzzles):
    w, h, ox, oy = cell
    mx = ", ".join(str(round(m[0] * 2)) for m in muzzles)
    my = ", ".join(str(round(m[1] * 2)) for m in muzzles)
    L = ["// <auto-generated> by art/coghaven/make_jade_golem_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.NPCs",
         "{",
         "\t/// <summary>The Jade Golem's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells in",
         "\t/// Columns columns, 2 px between them; the origin is the ground point under his hips. Each sequence is Name .. Name + NameFrames - 1.",
         "\t/// Aim frame k points the near arm AimMinDegrees + k x AimStepDegrees below forward (-90 straight up).</summary>",
         "\tpublic static class JadeGolemRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Idle = %d, IdleFrames = 2, Aim = %d, AimFrames = %d;"
         % (WALK, INDEX["Idle0"], INDEX["Aim0"], AIM_FRAMES),
         "\t\tpublic const int AimMinDegrees = %d, AimStepDegrees = %d;" % (AIM_MIN, AIM_STEP),
         "\t\t/// <summary>The near shoulder, game px from the origin (left-facing): the aim is measured from here.</summary>",
         "\t\tpublic const int ShoulderX = %d, ShoulderY = %d;" % (round(SHOULDER_NEAR[0] * 2), round(SHOULDER_NEAR[1] * 2)),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d;" % max(1, round(STRIDE * 2 / (WALK / 2))),
         "\t\t/// <summary>Where the ray leaves his fist in each aim frame, game px from the origin (left-facing).</summary>",
         "\t\tpublic static readonly int[] MuzzleX = { %s };" % mx,
         "\t\tpublic static readonly int[] MuzzleY = { %s };" % my,
         "\t}",
         "}"]
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def grid_cols(canvases, cell, glow=False):
    """Equal cells in COLUMNS columns, left to right, then down, 1 px (2 px in game) between them."""
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", (w * COLUMNS + COLUMNS - 1, (h + 1) * rows - 1), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        bx, by = (k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)
        for (x, y), col in (cv.glow if glow else cv.px).items():
            if y >= GROUND_CLIP:
                continue
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[bx + cx, by + cy] = col + (255,)
    return out


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_cols([fr[idx] for fr in frames], cell), OUT + "NPCs/JadeGolem%s.png" % suffix)
    export(grid_cols([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/JadeGolem_Glow.png")
    muzzles = [frames[INDEX["Aim%d" % k]][4] for k in range(AIM_FRAMES)]
    write_rig(OUT + "NPCs/JadeGolemRigData.cs", cell, muzzles)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")
    export_ray()


def preview(path, names=None, scale=4):
    cw, ch = 64, 56
    chosen = [(n, p) for (n, p) in FRAMES if names is None or n in names]
    cols = min(6, len(chosen))
    rows = (len(chosen) + cols - 1) // cols
    sheet_im = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(chosen):
            far, mid, near, glow, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near, glow):
                t.alpha_composite(to_image(cv.px, -cw // 2 - 6, -ch + 3, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet_im.paste(tile, (0, half * ch * rows))
    sheet_im.resize((sheet_im.width * scale, sheet_im.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames", help="comma-separated frame names for a close-up preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview, a.frames.split(",") if a.frames else None, 8 if a.frames else 4)
    else:
        export_all()
