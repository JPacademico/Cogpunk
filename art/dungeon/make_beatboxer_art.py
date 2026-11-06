"""Source for the Beat-Boxer, a Cogpunk enemy of the Dungeon, and its Spring Gloves (D4), 2026-11-03. Run from the repo
root:

    python -P art/dungeon/make_beatboxer_art.py [--preview FILE]

Design (the user's reference image, 2026-11-03: a boxing robot): a heavy steel robot in a boxer's crouch. A big steel
dome of a head with a golden face plate and two round ember lenses (hostile), a grille for a mouth; two speaker
cylinders with brass caps standing up behind its shoulders; a barrel chest with a brass chain round the neck; red
boxing shorts with a white band and a brass buckle; short thick piston legs in heavy boots. The near fist is a red
boxing glove with a white cross on it, the far fist a golden microphone ("beat-boxer"); both fly out on coiled springs.
Three-quarter view facing left (D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and the far arm with the microphone, a ramp step
darker), middle (head, cylinders, torso, shorts), near (the near leg and the near arm with the glove); the glow sheet
holds the lenses. Stable pixels (D4 rule 17): the body moves by whole pixels in the walk and idle loops and is lit in
its own space; limbs in 45-degree steps.

Frames: Walk x6 (a boxer's shuffle), Idle x2 (bouncing on its toes), Windup x2 (the telegraph: both fists drawn back,
the springs squeezed between forearm and fist), PunchNear (the near arm thrown forward, its glove gone on the spring:
SpringPunch draws it), PunchFar (the far arm thrown, the microphone gone, the near glove back on guard).
2026-11-04 (user: "the second punch is coming out of his head, make it lower so it feels like a second hand, just a bit
higher than the first"): the PunchFar frame twists the far shoulder forward and down (`twist`, a boxer's cross) and
throws the far arm at chest height, so its spring leaves 3 px (game) above the first instead of from under the head
(the 2026-11-03 version is in art/dungeon/previous/).

Outputs:
    Content/Dungeon/NPCs/BeatBoxer.png, BeatBoxer_Far.png, BeatBoxer_Near.png, BeatBoxer_Glow.png   grid sheets
    Content/Dungeon/NPCs/BeatBoxerRigData.cs        cells, origin, frames, the spring shoulders (where the coils fix)
    Content/Dungeon/Projectiles/SpringPunch.png     28x24 the red glove (facing left)
    Content/Dungeon/Projectiles/SpringPunch_Mic.png 28x24 the golden microphone (facing left)
    Content/Dungeon/Projectiles/SpringPunch_Spring.png 8x10 one cell of the coil (repeated along the spring)
    Content/Dungeon/Items/SpringGloves.png          32x28 the accessory: a red glove and a coil spring
    Content/Dungeon/Gores/BeatBoxer_GoreHead.png, _GoreGlove.png, _GoreMic.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, cyl, face, rivet, ik, level, lit  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Dungeon/"
I, B, C, E, S = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam"))
THIGH, SHIN = 4.6, 4.6
UPPER, FORE = 4.4, 4.4
# The far fist's guard (the microphone): at chest height in front of the barrel, above the near glove. 2026-11-04 (user:
# "move the hand a bit lower so it does not come from his face"): it was held at (-10, -21), in front of the face plate.
GUARD_FAR = (-9.0, -15.0)


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def despeckle(cv):
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


class Pose:
    def __init__(self, bob=0, lean=0, near_foot=(-4.0, 0.0), far_foot=(4.0, 0.0), near_hand=(-9.0, -12.0), far_hand=GUARD_FAR,
                 near_glove=True, far_glove=True, squeeze=0.0, twist=0):
        self.bob, self.lean = bob, lean                   # whole px: down, back (+x)
        self.twist = twist                                # whole px the far shoulder turns forward (and 1 down) in a cross
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_hand, self.far_hand = near_hand, far_hand
        self.near_glove, self.far_glove = near_glove, far_glove
        self.squeeze = squeeze                            # 0 .. 1: the springs squeezed between forearm and fist (windup)


def limb_shade(a, b, r, lo, hi, gain=1.4, step=22.5):
    """A cylinder lit with its axis snapped to `step` degrees (D4 rule 17): the bands are measured across the real axis,
    so they stay on the limb, but the light only turns when the limb turns past a step, never with a pixel of sway (the
    limbs are drawn in rig space, so rig.py's own snap would see no turn at all)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln
    sa = round(math.atan2(dy, dx) / math.radians(step)) * math.radians(step)
    snx, sny = -math.sin(sa), math.cos(sa)

    def shade(i):
        t = max(-1.0, min(1.0, ((i.lx - a[0]) * nx + (i.ly - a[1]) * ny) / r))
        return level(lit(t * snx, t * sny, math.sqrt(1.0 - t * t)), lo, hi, gain)
    return shade


def limb(cv, a, b, r, ramp, depth, lo=1, hi=4):
    cv.part(Xf(), Capsule(a, b, r), ramp, limb_shade(a, b, r, lo, hi), depth=depth, rust=0.0)


def leg(cv, hip, foot, lift, depth):
    ankle = (foot, -2.2 - lift)
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)                 # knees forward: a crouch
    limb(cv, hip, knee, 2.3, "iron", depth)
    limb(cv, knee, ankle, 2.1, "iron", depth)
    ax, ay = ankle
    cv.part(Xf(), Poly([(ax + 2.4, ay - 0.6), (ax - 2.0, ay - 1.2), (ax - 4.0, ay + 0.8), (ax - 3.6, ay + 2.2), (ax + 2.6, ay + 2.2)]),
            "iron", face((-0.4, -0.6, 0.7), lo=1, hi=3, snap=45), depth=depth, rust=0.0)   # a heavy boot
    cv.part(Xf(), box(ax - 3.2, ay + 1.4, ax + 2.4, ay + 2.2), "brass", flat(2), depth=depth, outline=False, rust=0.0)   # its brass sole
    q = (int(math.floor(knee[0])), int(math.floor(knee[1])))
    cv.put(q[0], q[1], B[max(1, 4 - depth)])                      # the knee bolt


def glove(cv, c, depth, glow=None):
    """The red boxing glove (facing left): a round mitt, a thumb over its top front, a cuff behind, a white cross on its
    side (Ember for the leather, Steam for the cross)."""
    cx, cy = c
    mitt = cv.part(Xf(), Ellipse(cx, cy, 4.4, 3.8), "ember", dome(cx - 1.6, cy - 1.6, 5.2, lo=1, hi=2, gain=1.2, bias=-0.15, fixed=True),
                   depth=depth, rust=0.0)
    cv.part(Xf(), Ellipse(cx - 2.6, cy - 2.6, 1.6, 1.3), "ember", dome(cx - 3.2, cy - 3.2, 2.0, lo=1, hi=2, fixed=True), depth=depth, rust=0.0)
    cv.part(Xf(), box(cx + 3.0, cy - 2.2, cx + 5.2, cy + 2.4), "steam", flat(1 if depth else 2), depth=depth, rust=0.0)   # the cuff
    for (dx, dy) in ((0, -1), (0, 0), (0, 1), (-1, 0), (1, 0)):
        q = (int(math.floor(cx + 0.6)) + dx, int(math.floor(cy + 0.4)) + dy)
        if q in mitt:
            cv.put(q[0], q[1], S[3] if dy <= 0 and dx <= 0 else S[2])   # the white cross
    hl = (int(math.floor(cx - 2.2)), int(math.floor(cy - 1.8)))
    if hl in mitt:
        cv.put(hl[0], hl[1], E[3])                          # a hot glint on the leather
    return mitt


def mic(cv, c, depth):
    """The golden microphone fist (facing left): a grille ball of brass with dark holes, a band, an iron handle-cuff."""
    cx, cy = c
    ball = cv.part(Xf(), Ellipse(cx, cy, 3.8, 3.6), "brass", dome(cx - 1.3, cy - 1.3, 4.6, lo=2, hi=5, gain=1.3, fixed=True),
                   depth=depth, rust=0.0)
    ox, oy = int(round(cx)), int(round(cy))                # the grille rides the ball, not the screen
    for (x, y) in list(ball):
        if (x - ox + y - oy) % 2 == 0 and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 < 6.0 and cv.px.get((x, y)) not in (B[0],):
            cv.put(x, y, B[1] if depth == 0 else B[0])        # the grille
    cv.part(Xf(), box(cx + 2.8, cy - 1.8, cx + 5.4, cy + 1.8), "iron", flat(2), depth=depth, rust=0.0)    # the handle cuff
    q = P(Xf(), (cx - 1.6, cy - 1.8))
    cv.put(q[0], q[1], B[5] if depth == 0 else B[4])
    return ball


def coil(cv, a, b, depth):
    """A squeezed spring between a forearm and its fist (the windup): three steel loops."""
    for k in range(3):
        t = (k + 0.5) / 3.0
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        cv.part(Xf(), Ellipse(x, y, 0.9, 2.0), "iron", flat(3), depth=depth, rust=0.0)


def body(mid, glow, pose):
    oy, ox = pose.bob, pose.lean
    # the speaker cylinders behind the shoulders, brass caps on top
    for k, (x0, h) in enumerate(((2.0, 9.0), (5.4, 7.5))):
        x = x0 + ox
        mid.part(Xf(), box(x, -30.0 + oy + (9.0 - h), x + 3.0, -20.0 + oy), "iron",
                 cyl((x, -25.0), (x + 3.0, -25.0), 1.5, lo=1, hi=3, fixed=True), rust=0.0)
        mid.part(Xf(), box(x - 0.4, -31.2 + oy + (9.0 - h), x + 3.4, -29.6 + oy + (9.0 - h)), "brass", flat(4), rust=0.0)
    # the torso: a barrel of steel, a brass chain round its neck
    torso = mid.part(Xf(), Ellipse(0.2 + ox, -14.0 + oy, 6.6, 6.0), "iron", dome(-2.0 + ox, -17.0 + oy, 7.4, lo=1, hi=4, gain=1.3, bias=0.1, fixed=True),
                     shadow=(1, 1), rust=0.0)
    for k in range(9):                                      # the chain: brass links in a sagging arc
        a = math.radians(200 + k * 17.5)
        x, y = -1.0 + ox + math.cos(a) * 4.6, -18.0 + oy - math.sin(a) * 2.6
        q = (int(math.floor(x)), int(math.floor(y)))
        if q in torso:
            mid.put(q[0], q[1], B[4] if k % 2 == 0 else B[3])
    pq = (int(math.floor(-1.0 + ox)), int(math.floor(-15.0 + oy)))
    for (dx, dy, col) in ((0, 0, B[5]), (1, 0, B[3]), (0, 1, B[3]), (1, 1, B[2])):
        mid.put(pq[0] + dx, pq[1] + dy, col)                # its pendant
    # the shorts: red with a white band and a brass buckle
    shorts = mid.part(Xf(), Union(box(-5.6 + ox, -10.2 + oy, 5.8 + ox, -6.2 + oy), Ellipse(0.1 + ox, -6.4 + oy, 5.7, 1.6)), "ember",
                      face((-0.4, -0.5, 0.75), lo=1, hi=2, gain=1.1, fixed=True), rust=0.0)
    for x in range(int(-5 + ox), int(6 + ox)):
        q = (x, int(math.floor(-9.4 + oy)))
        if q in shorts:
            mid.put(q[0], q[1], S[2] if x < 1 + ox else S[1])
    for (dx, col) in ((0, B[4]), (1, B[3])):
        mid.put(int(math.floor(-2.0 + ox)) + dx, int(math.floor(-9.4 + oy)), col)
    # the head: a steel dome, a golden face plate with two ember lenses and a grille
    hc = (-2.8 + ox, -24.4 + oy)
    head = mid.part(Xf(), Ellipse(hc[0], hc[1], 5.8, 5.2), "iron", dome(hc[0] - 1.8, hc[1] - 2.0, 6.0, lo=1, hi=4, gain=1.35, bias=0.15, fixed=True),
                    shadow=(1, 1), rust=0.0)
    plate = mid.part(Xf(), Union(box(hc[0] - 6.0, hc[1] - 2.4, hc[0] + 0.8, hc[1] + 3.4), Ellipse(hc[0] - 2.6, hc[1] - 2.4, 3.4, 1.5)),
                     "brass", face((-0.6, -0.4, 0.7), lo=3, hi=5, gain=1.25, bias=0.2, fixed=True), rust=0.0)
    for (ex, ey) in ((hc[0] - 4.2, hc[1] - 0.6), (hc[0] - 1.4, hc[1] - 0.6)):
        q = (int(math.floor(ex)), int(math.floor(ey)))
        for (dx, dy, col) in ((0, 0, E[3]), (1, 0, E[2]), (0, 1, E[2]), (1, 1, E[1])):
            mid.put_glow(q[0] + dx, q[1] + dy, col)
            glow.put_glow(q[0] + dx, q[1] + dy, col)
    for x in range(int(math.floor(hc[0] - 4.4)), int(math.floor(hc[0] + 0.4))):
        q = (x, int(math.floor(hc[1] + 2.0)))
        if q in plate:
            mid.put(q[0], q[1], B[1] if x % 2 else B[2])    # the grille mouth
    q = (int(math.floor(hc[0] - 2.4)), int(math.floor(hc[1] - 4.0)))
    if q in head:
        mid.put(q[0], q[1], WHITE)                          # a glint on the dome
    del shorts
    tw = pose.twist
    return (-3.6 + ox, -17.4 + oy), (2.6 + ox - tw, -18.4 + oy + (1 if tw else 0)), (-1.6 + ox, -9.0 + oy), (2.2 + ox, -9.4 + oy)


def arm(cv, shoulder, hand, has_fist, fist, depth, squeeze=0.0):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)
    limb(cv, shoulder, elbow, 2.2, "iron", depth)
    limb(cv, elbow, wrist, 2.0, "iron", depth)
    q = (int(math.floor(elbow[0])), int(math.floor(elbow[1])))
    cv.put(q[0], q[1], B[max(1, 4 - depth)])                # the elbow bolt
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    ux, uy = d[0] / ln, d[1] / ln
    plate = (wrist[0] + ux * 0.8, wrist[1] + uy * 0.8)
    cv.part(Xf(), Ellipse(plate[0], plate[1], 1.4, 2.0), "brass", flat(3), depth=depth, rust=0.0)   # the spring's base plate
    if has_fist:
        gap = 1.0 + 2.6 * squeeze
        c = (plate[0] + ux * (3.4 + gap), plate[1] + uy * (3.4 + gap))
        c = (math.floor(c[0]) + 0.5, math.floor(c[1]) + 0.5)   # whole pixels: a swaying fist moves, it doesn't re-raster
        if squeeze > 0.0:
            coil(cv, plate, (c[0] - ux * 3.0, c[1] - uy * 3.0), depth)
        fist(cv, c, depth)
    return plate


def frame(pose):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    sh_near, sh_far, hip_near, hip_far = body(mid, glow, pose)
    leg(far, hip_far, pose.far_foot[0], pose.far_foot[1], 1)
    leg(near, hip_near, pose.near_foot[0], pose.near_foot[1], 0)
    far_plate = arm(far, sh_far, (pose.far_hand[0] + pose.lean, pose.far_hand[1] + pose.bob), pose.far_glove, mic, 1, pose.squeeze)
    near_plate = arm(near, sh_near, (pose.near_hand[0] + pose.lean, pose.near_hand[1] + pose.bob), pose.near_glove, glove, 0, pose.squeeze)
    for cv in (far, mid, near):
        despeckle(cv)
    return far, mid, near, glow, near_plate, far_plate


WALK = 6
STRIDE = 4.0


def walk_pose(f):
    def foot(phase):
        t = (phase % WALK) / WALK
        if t < 0.5:
            return (STRIDE / 2 - STRIDE * (t / 0.5), 0.0)
        u = (t - 0.5) / 0.5
        return (-STRIDE / 2 + STRIDE * u, round(1.6 * math.sin(math.pi * u)))
    nf, ff = foot(f), foot(f + WALK // 2)
    bob = 1 if f % 3 == 1 else 0
    sway = 1 if f % 3 == 2 else 0
    return Pose(bob=bob, near_foot=(nf[0] - 4.0, nf[1]), far_foot=(ff[0] + 4.0, ff[1]), near_hand=(-9.0 - sway, -12.0),
                far_hand=(GUARD_FAR[0] + sway, GUARD_FAR[1]))


FRAMES = [("Walk%d" % k, walk_pose(k)) for k in range(WALK)] + [
    ("Idle0", Pose()),
    ("Idle1", Pose(bob=1)),
    ("Windup0", Pose(lean=1, near_hand=(-7.0, -13.0), far_hand=(GUARD_FAR[0] - 1.0, GUARD_FAR[1] - 0.5), squeeze=0.5)),
    ("Windup1", Pose(lean=1, bob=1, near_hand=(-6.0, -13.0), far_hand=(GUARD_FAR[0] - 0.5, GUARD_FAR[1] - 0.5), squeeze=1.0)),
    ("PunchNear", Pose(lean=-1, near_hand=(-13.0, -15.0), far_hand=(GUARD_FAR[0] + 1.0, GUARD_FAR[1]), near_glove=False, near_foot=(-6.0, 0.0))),
    ("PunchFar", Pose(lean=-1, near_hand=(-9.0, -12.0), far_hand=(-13.0, -16.0), far_glove=False, near_foot=(-5.0, 0.0), twist=3)),
]
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The flying fists, the spring cell and the accessory
# ================================================================================================
def fist_image(kind):
    cv = Canvas()
    (glove if kind == "glove" else mic)(cv, (6.6, 5.8), 0)
    despeckle(cv)
    return to_image(cv.px, 0, 0, 14, 12)


def spring_cell():
    """One 4x5 cell of the coil (8x10 in game): a steel loop seen from the side, lit on its upper left."""
    rows = (".oo.",
            "ohlo",
            "olmo",
            "omdo",
            ".oo.")
    pal = {"o": I[0], "h": I[4], "l": I[3], "m": I[2], "d": I[1]}
    im = Image.new("RGBA", (4, 5), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                im.putpixel((x, y), pal[ch] + (255,))
    return im


def spring_gloves_icon():
    """16x14: a red glove (white cross) and, behind it, the coil spring it rides on."""
    cv = Canvas()
    for k in range(4):
        cv.part(Xf(), Ellipse(10.8 + k * 1.2, 8.6 - k * 1.2, 1.0, 2.1), "iron", flat(3), rust=0.0)
    glove(cv, (6.2, 6.4), 0)
    despeckle(cv)
    return to_image(cv.px, 0, 0, 16, 14)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _, _ = frame(dict(FRAMES)["Idle0"])
    return {"BeatBoxer_GoreHead": crop({q: c for q, c in mid.px.items() if q[1] <= -19 and q[0] <= 2}),
            "BeatBoxer_GoreGlove": fist_image("glove"),
            "BeatBoxer_GoreMic": fist_image("mic")}


def write_rig(path, cell, near_plate, far_plate):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/dungeon/make_beatboxer_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Dungeon.NPCs",
         "{",
         "\t/// <summary>The Beat-Boxer's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells with",
         "\t/// 2 px under each; the origin is the ground point under its hips. The shoulders are the springs' base plates in the",
         "\t/// punch frames (where the coils are fixed), from the origin, facing left.</summary>",
         "\tpublic static class BeatBoxerRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Idle = %d, IdleFrames = 2, Windup = %d, PunchNear = %d, PunchFar = %d;"
         % (WALK, INDEX["Idle0"], INDEX["Windup0"], INDEX["PunchNear"], INDEX["PunchFar"]),
         "\t\tpublic const int NearShoulderX = %d, NearShoulderY = %d, FarShoulderX = %d, FarShoulderY = %d;"
         % (round(near_plate[0] * 2), round(near_plate[1] * 2), round(far_plate[0] * 2), round(far_plate[1] * 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/BeatBoxer%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/BeatBoxer_Glow.png")
    write_rig(OUT + "NPCs/BeatBoxerRigData.cs", cell, frames[INDEX["PunchNear"]][4], frames[INDEX["PunchFar"]][5])
    export(fist_image("glove"), OUT + "Projectiles/SpringPunch.png")
    export(fist_image("mic"), OUT + "Projectiles/SpringPunch_Mic.png")
    export(spring_cell(), OUT + "Projectiles/SpringPunch_Spring.png")
    export(spring_gloves_icon(), OUT + "Items/SpringGloves.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 50, 44
    cols = 6
    out = Image.new("RGBA", (cw * cols, ch * 2), (36, 40, 48, 255))
    light = Image.new("RGBA", (cw * cols, ch * 2), (150, 180, 210, 255))
    for k, (n, p) in enumerate(FRAMES):
        far, mid, near, _, _, _ = frame(p)
        tile = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cv in (far, mid, near):
            tile.alpha_composite(to_image(cv.px, -cw // 2, -ch + 3, cw, ch))
        out.alpha_composite(tile, ((k % cols) * cw, (k // cols) * ch))
        light.alpha_composite(tile, ((k % cols) * cw, (k // cols) * ch))
    extras = Image.new("RGBA", (cw * cols, 20), (36, 40, 48, 255))
    x = 4
    for im in (fist_image("glove"), fist_image("mic"), spring_cell(), spring_gloves_icon()):
        extras.alpha_composite(im, (x, 3))
        x += im.width + 8
    both = Image.new("RGBA", (cw * cols, ch * 4 + 20))
    both.alpha_composite(out, (0, 0))
    both.alpha_composite(light, (0, ch * 2))
    both.alpha_composite(extras, (0, ch * 4))
    both = both.resize((both.width * 4, both.height * 4), Image.NEAREST)
    both.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
