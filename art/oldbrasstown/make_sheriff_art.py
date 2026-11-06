"""Source for the Sheriff, Old Brass Town's rare mini-boss, his sheriff stars and the Sheriff Badge (D4). Run from the
repo root:

    python -P art/oldbrasstown/make_sheriff_art.py [--preview FILE]

Design (user, 2026-11-04: "a sheriff robot mini boss with three sheriff stars that float above him and attack the player
then come back to him every 2 seconds; he also shoots six bullets then reloads; hard to kill; drops the sheriff badge, a
summon weapon whose flying sheriff stars hover above the player and attack enemies"). Redrawn 2026-11-05 (user: "not
matching the necessary pixel art detail quality (Metal Slug level)"; docs/design/pixel-art-study.md; the 2026-11-04
version is in art/oldbrasstown/previous/): a broad, heavy robot lawman in vanilla's chunky proportions. A polished
nickel-steel head with a heavy brow, two ember eyes (hostile), a nose plate, a big ivory handlebar moustache with curled
tips over a steel jaw grille, and riveted cheek plates; a big felt hat with a band of gilt conchos and a gilt star; a long
hide duster to the knees (lapels, a back seam, pocket flaps, its tails swinging as he walks) open over a gilt waistcoat
with a big gilt sheriff's star and a watch chain; a gun belt with a gilt buckle; thick hide sleeves over steel forearms
with gilt cuffs, hide gloves; dark denim trousers with steel knee caps; riding boots with steel toe caps and gilt spurs;
and a polished nickel revolver with an ivory grip (no rust: the law keeps its gun clean). Three-quarter view facing left
(D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and the far arm, flat and a step darker), middle (the
near leg drawn first so the coat covers its thigh, then the coat, waistcoat, head and hat), near (the near arm and the
revolver); the glow sheet holds the eyes and the muzzle flash. Stable pixels (D4 rule 17): the middle plane is built in
the body's own space and placed by whole-pixel bobs, limbs are lit with their light's turn snapped, far limbs one tone.

Frames: Walk x6, Idle x2, Aim x3 (level, up, down), Shoot x3 (the same, kicked by the shot, a muzzle flash), Reload x4
(the cylinder swung out, the far hand thumbing cartridges in).

The stars (5 points have 72-degree symmetry: 6 spin frames of 12 degrees loop): brass with an ember gem for the
Sheriff's (hostile, D3) and an aether gem for the Sheriff Badge's minion (friendly), each with a glow sheet (the gem, and
the rim lit for the attack telegraph).

Outputs:
    Content/OldBrassTown/NPCs/Sheriff.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/OldBrassTown/NPCs/SheriffRigData.cs        cells, origin, frames, the three muzzles, the hat's top
    Content/OldBrassTown/Projectiles/SheriffStar.png, _Glow.png              6 spin frames + 6 telegraph frames (rim lit)
    Content/OldBrassTown/Minions/SheriffStarMinion.png, _Glow.png             6 spin frames (the minion; aether gem)
    Content/OldBrassTown/Minions/SheriffBadge.png      28x28 the summon item: the star in a brass ring
    Content/OldBrassTown/Minions/SheriffStarBuff.png   32x32 the minion buff icon
    Content/OldBrassTown/Gores/Sheriff_GoreHead.png, _GoreHat.png, _GoreBadge.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from westbots import (RAMP, WHITE, Xf, Poly, Ellipse, Union, box, Canvas, flat, dome, face, P, finish, leg, arm, revolver,  # noqa: E402
                      cowboy_hat, texture, glint, I, B, C, E, S, LE, ST, G, H, D, IV)
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"
A = RAMP["aether"]
THIGH, SHIN = 4.7, 4.6
UPPER, FORE = 4.2, 4.0
AIM_ANGLES = (0.0, -25.0, 25.0)
HIP_Y = -11.2
HEAD = (-0.9, -26.8)
SHOULDER_NEAR, SHOULDER_FAR = (-3.8, -21.4), (3.6, -21.6)
ARM = dict(r_upper=2.2, r_fore=1.9, sleeve="hide")


class Pose:
    def __init__(self, bob=0, near_foot=(-1.8, 0.0), far_foot=(2.2, 0.0), near_hand=(-3.6, -14.0), far_hand=(4.0, -14.2),
                 aim=None, recoil=0, flash=False, reload=False, tails=0, load=0):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_hand, self.far_hand = near_hand, far_hand
        self.aim, self.recoil, self.flash, self.reload = aim, recoil, flash, reload
        self.tails = tails                               # whole px the coat tails swing back (+) or forward (-)
        self.load = load                                 # 0 / 1 / 2: the far hand at the belt, on its way, at the cylinder


def badge_points(cx, cy, r_out, r_in):
    pts = []
    for k in range(10):
        a = math.radians(-90.0 + k * 36.0)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def body(mid, glow, p):
    """The middle plane in the body's own space, placed by one whole-pixel translation (D4 rule 17)."""
    oy = p.bob
    bx = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))

    def at(x, y):
        return P(bx, (x, y))
    t = p.tails
    # --- the duster: hide from the shoulders to the knees, its tails behind; the waistcoat shows in its open front ------
    coat = Poly([(-4.8, -22.6), (4.4, -22.6), (5.4, -14.6), (6.4 + t, -5.0), (2.4 + t * 0.5, -4.2), (-1.2, -5.0), (-5.2, -4.6),
                 (-6.0, -13.8)])
    coat_shade = texture(face((-0.5, -0.4, 0.75), lo=2, hi=5, ramp_len=7, gain=1.25, bias=0.25, fixed=True, dither=0.14), "speckle",
                         seed=21, density=0.1)
    cinner = mid.part(bx, coat, "hide", coat_shade, shadow=(1, 1), rust=0.0)
    for y in range(-21, -6):                                          # the coat's back seam, stitched
        q = at(3.4, y + 0.5)
        if q in cinner and y % 3 != 0:
            mid.put(q[0], q[1], H[1])
    for (x0, y0) in ((-4.6, -10.0), (2.6, -10.0)):                    # pocket flaps on the coat's skirt
        for dx in range(3):
            q = at(x0 + dx, y0)
            if q in cinner:
                mid.put(q[0], q[1], H[1])
                if (q[0], q[1] - 1) in cinner:
                    mid.put(q[0], q[1] - 1, H[5])
    # the waistcoat in the coat's open front (crimson, so the gilt star stands out), the badge on it, a watch chain
    vest = Poly([(-3.0, -22.0), (2.0, -22.0), (1.8, -12.0), (-2.8, -12.0)])
    vinner = mid.part(bx, vest, "crimson", texture(face((-0.5, -0.4, 0.75), lo=2, hi=4, ramp_len=6, gain=1.3, bias=0.2, fixed=True),
                                                    "weave", seed=13), rust=0.0)
    for y in (-15.0, -13.0):
        q = at(-2.2, y)
        if q in vinner:
            mid.put(q[0], q[1], G[7])                                 # its gilt buttons
            mid.put(q[0] + 1, q[1] + 1, RAMP["crimson"][1])
    for (dx, dy) in ((0, 0), (1, 1), (2, 1), (3, 0)):
        q = at(-1.4 + dx, -13.8 + dy)
        if q in vinner:
            mid.put(q[0], q[1], G[9] if dx % 2 == 0 else G[5])         # the watch chain
    # the sheriff's star, hand-placed (a 7-px star rasterised from a polygon is all outline): lit top-left
    sx, sy = at(-0.4, -18.6)
    badge = ("...9...",
             "...8...",
             "8889766",
             ".78875.",
             "..765..",
             ".65.54.",
             ".5...4.")
    for j, row in enumerate(badge):
        for i, ch in enumerate(row):
            if ch != ".":
                mid.put(sx + i - 3, sy + j - 3, G[int(ch)])
    # the lapels: lit felt folds either side of the opening, the opening's lit edge down the coat
    for (pts, k) in ((((-4.2, -22.4), (-2.2, -22.4), (-3.2, -18.2)), 6), (((1.6, -22.4), (3.4, -22.4), (2.4, -18.6)), 3)):
        for q in mid.raster(bx, Poly(pts)):
            mid.put(q[0], q[1], H[k])
    for y in range(-18, -12):
        q = at(-3.4, y + 0.5)
        if q in cinner:
            mid.put(q[0], q[1], H[5])
    # the gun belt across the coat's opening
    mid.part(bx, box(-5.2, -12.6, 4.8, -10.8), "hide", face((-0.4, -0.6, 0.75), lo=1, hi=3, ramp_len=7, fixed=True), rust=0.0)
    qx, qy = at(-4.6, -12.2)
    for (dx, dy, k) in ((0, 0, 9), (1, 0, 7), (2, 0, 6), (0, 1, 6), (1, 1, 4), (2, 1, 4)):
        mid.put(qx + dx, qy + dy, G[k])                               # the buckle
    # --- the neck and the head: polished nickel, a heavy brow, ember eyes, the moustache, the jaw grille ----------------
    mid.part(bx, box(-2.2, -24.2, 1.2, -22.0), "steel", face((-0.5, -0.5, 0.7), lo=2, hi=4, ramp_len=9, fixed=True), rust=0.0)
    hx, hy = HEAD
    head = mid.part(bx, Ellipse(hx, hy, 4.9, 4.6), "steel", dome(hx - 1.6, hy - 1.8, 5.4, lo=3, hi=7, gain=1.35, bias=0.3, fixed=True,
                                                                  dither=0.18), shadow=(1, 1), rust=0.0)
    g = at(hx - 2.8, hy - 2.4)
    glint(mid, g[0], g[1], "steel", cross=True)
    ey = at(0.0, hy - 0.8)[1]
    x0, x1 = at(hx - 4.4, 0.0)[0], at(hx + 1.6, 0.0)[0]
    for x in range(x0, x1):
        if (x, ey - 1) in head:
            mid.put(x, ey - 1, ST[2])                                 # the heavy brow
        if (x, ey - 2) in head and x < x1 - 1:
            mid.put(x, ey - 2, ST[6])                                 # its lit ridge
    for ex in (hx - 3.2, hx - 0.8):
        q = (at(ex, 0.0)[0], ey)
        for (dx, col) in ((0, E[3]), (1, E[2])):
            if (q[0] + dx, q[1]) in head:
                mid.put_glow(q[0] + dx, q[1], col)
                glow.put_glow(q[0] + dx, q[1], col)
    nose = at(hx - 4.6, hy + 0.6)
    mid.put(nose[0], nose[1], ST[5])                                  # the nose plate
    mid.put(nose[0], nose[1] + 1, ST[3])
    my = ey + 2
    mx = at(hx, 0.0)[0]
    tash = ((-5, -1, 3), (-5, 0, 4), (-4, 0, 5), (-3, 0, 5), (-2, 0, 4), (-1, 0, 4), (0, 0, 5), (1, 0, 4), (2, 0, 3), (2, -1, 2),
            (-4, 1, 2), (-3, 1, 3), (-2, 1, 3), (-1, 1, 2), (0, 1, 3), (1, 1, 2))
    for (dx, dy, k) in tash:
        mid.put(mx + dx, my + dy, IV[k])                              # the handlebar moustache, its tips curled up
    for x in range(mx - 3, mx + 2):
        q = (x, my + 2)
        if q in head:
            mid.put(q[0], q[1], ST[2] if x % 2 else ST[4])            # the jaw grille
    q = at(hx + 2.6, hy + 0.4)                                        # a riveted cheek plate
    for (dx, dy, k) in ((0, 0, 6), (1, 1, 3), (0, 1, 4)):
        if (q[0] + dx, q[1] + dy) in head:
            mid.put(q[0] + dx, q[1] + dy, ST[k])
    cowboy_hat(mid, (hx + 0.4, hy - 11.2 + oy), 18.4, 7.0, 9.6, star=True, tilt=-3.0, lo=3)
    return ((SHOULDER_NEAR[0], SHOULDER_NEAR[1] + oy), (SHOULDER_FAR[0], SHOULDER_FAR[1] + oy), (-1.0, HIP_Y + oy),
            (1.4, HIP_Y - 0.2 + oy))


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    # the near leg goes first on the middle plane, so the coat covers its thigh
    hip_near = (-1.0, HIP_Y + p.bob)
    leg(mid, hip_near, p.near_foot[0], p.near_foot[1], 0, THIGH, SHIN, r_thigh=2.3, r_shin=2.1)
    sh_near, sh_far, _, hip_far = body(mid, glow, p)
    leg(far, hip_far, p.far_foot[0], p.far_foot[1], 1, THIGH, SHIN, r_thigh=2.3, r_shin=2.1)
    muzzle = None
    if p.aim is not None:
        a = math.radians(p.aim)
        reach = UPPER + FORE - 0.4
        hand = (sh_near[0] - math.cos(a) * reach + p.recoil, sh_near[1] + math.sin(a) * reach)
        fist, u = arm(near, sh_near, hand, 0, UPPER, FORE, **ARM)
        muzzle = revolver(near, (fist[0] + 0.6, fist[1] - 0.6), -p.aim + (14.0 if p.recoil else 0.0), 0, style="nickel", flash=p.flash,
                          glow=glow, barrel=7.2)
        arm(far, sh_far, (sh_far[0] + 0.8, sh_far[1] + 6.6), 1, UPPER, FORE, **ARM)
    elif p.reload:
        fist, u = arm(near, sh_near, (-6.4, -17.4 + p.bob), 0, UPPER, FORE, **ARM)
        revolver(near, (fist[0] + 0.2, fist[1] - 0.4), -50.0, 0, style="nickel", open_cylinder=True, barrel=7.2)
        far_hand = ((0.8, -14.6), (-1.8, -15.8), (-4.0, -16.8))[p.load]     # at the belt, on the way, at the cylinder
        arm(far, sh_far, (far_hand[0], far_hand[1] + p.bob), 1, UPPER, FORE, **ARM)
    else:
        fist, u = arm(near, sh_near, (p.near_hand[0], p.near_hand[1] + p.bob), 0, UPPER, FORE, **ARM)
        revolver(near, (fist[0] + 0.2, fist[1] - 0.4), -70.0, 0, style="nickel", barrel=7.2)   # held low, pointing at the ground
        arm(far, sh_far, (p.far_hand[0], p.far_hand[1] + p.bob), 1, UPPER, FORE, **ARM)
    for cv in (far, mid, near):
        finish(cv)
        for q, c in list(cv.px.items()):
            if c == G[3]:
                cv.px[q] = G[4]                                         # the colour budget (D4 rule 5: 32): a stray cast shade
    return far, mid, near, glow, muzzle


WALK = 6
STRIDE = 5.2


def cycle_foot(phase, n, stride, lift):
    t = (phase % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    nf, ff = cycle_foot(k, WALK, STRIDE, 1.8), cycle_foot(k + WALK // 2, WALK, STRIDE, 1.8)
    swing = 1 if k in (1, 2) else (-1 if k in (4, 5) else 0)
    return Pose(bob=1 if k % 3 == 1 else 0, near_foot=(nf[0] - 1.8, nf[1]), far_foot=(ff[0] + 2.2, ff[1]),
                near_hand=(-3.6 - swing, -14.0), far_hand=(4.0 + swing, -14.2), tails=1 if k in (0, 1, 3, 4) else 0)


FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Idle0", Pose()), ("Idle1", Pose(bob=1, tails=1))]
          + [("Aim%d" % k, Pose(aim=a, near_foot=(-3.0, 0.0), far_foot=(3.0, 0.0))) for k, a in enumerate(AIM_ANGLES)]
          + [("Shoot%d" % k, Pose(aim=a, recoil=1, flash=True, near_foot=(-3.0, 0.0), far_foot=(3.0, 0.0))) for k, a in enumerate(AIM_ANGLES)]
          + [("Reload%d" % k, Pose(reload=True, load=(0, 1, 2, 1)[k])) for k in range(4)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The stars, the badge and the buff icon
# ================================================================================================
def star_points(cx, cy, r_out, r_in, rot_deg, n=5):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot_deg - 90.0 + k * 180.0 / n)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


STAR = 13                                   # the star's cell at 1x (26 game px)


def star(rot, gem, rim_lit=False, size=STAR, r_out=6.3, r_in=3.0):
    """A five-point brass star turned `rot` degrees: the half facing the top-left light bright, a lit ridge down each
    point's axis (a bevelled badge), measured in the star's own turn (so the spin reads as a turning star), a gem at its
    centre. `rim_lit` lights the outline too (the attack's telegraph, drawn at full brightness from the glow sheet).
    Returns the colour and glow canvases."""
    cv, gl = Canvas(), Canvas()
    c = size / 2.0
    shape = Poly(star_points(c, c, r_out, r_in, rot))
    mask = cv.raster(Xf(), shape)
    edge = {q for q in mask if any((q[0] + ox, q[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for q in mask:
        dx, dy = q[0] + 0.5 - c, q[1] + 0.5 - c
        d = math.hypot(dx, dy)
        if q in edge:
            col = B[4] if rim_lit else B[1]
            cv.put(q[0], q[1], col)
            if rim_lit:
                gl.put_glow(q[0], q[1], col)
            continue
        a = math.degrees(math.atan2(dy, dx))
        rel = (a - (rot - 90.0)) % 72.0
        off = min(rel, 72.0 - rel)                              # 0 on a point's axis, 36 between two points
        light = (dx * -0.6 + dy * -0.75) / max(1.0, d)
        k = 4 if light > 0.2 else (3 if light > -0.45 else 2)
        if off < 10.0 and d > 1.6:
            k += 1                                              # the ridge
        cv.put(q[0], q[1], B[min(5, k)])
    g = (int(math.floor(c)), int(math.floor(c)))
    ramp = E if gem == "ember" else A
    for (dx, dy, col) in ((0, 0, ramp[2]), (-1, 0, ramp[3]), (0, -1, ramp[3]), (-1, -1, ramp[3]), (0, 1, ramp[1]), (1, 0, ramp[1]),
                          (1, 1, ramp[1]), (-1, 1, ramp[2]), (1, -1, ramp[2])):
        cv.put_glow(g[0] + dx, g[1] + dy, col)
        gl.put_glow(g[0] + dx, g[1] + dy, col)
    return cv, gl


SPIN = 6


def star_sheets(gem):
    frames, glows = [], []
    for rim in ((False, True) if gem == "ember" else (False,)):
        for k in range(SPIN):
            cv, gl = star(k * 12.0, gem, rim_lit=rim)
            frames.append(to_image(cv.px, 0, 0, STAR, STAR))
            glows.append(to_image(gl.glow, 0, 0, STAR, STAR))
    return vertical(frames), vertical(glows)


def badge_icon():
    """14x14: the star (aether gem: it's yours now) inside a brass ring."""
    cv = Canvas()
    c = 6.5
    for y in range(14):
        for x in range(14):
            d = math.hypot(x + 0.5 - c - 0.5, y + 0.5 - c - 0.5)
            if 5.6 <= d <= 6.9:
                outer = d > 6.3
                lit = (x - c) + (y - c) < 0
                cv.put(x, y, B[0] if outer else (B[4] if lit else B[2]))
    s, _ = star(0.0, "aether", size=14, r_out=5.4, r_in=2.6)
    cv.px.update(s.px)
    return to_image(cv.px, 0, 0, 14, 14)


def buff_icon():
    s, _ = star(0.0, "aether", size=16, r_out=7.2, r_in=3.4)
    return to_image(s.px, 0, 0, 16, 16)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Idle0"])
    top = int(math.floor(HEAD[1] - 4.8))
    return {"Sheriff_GoreHead": crop({q: c for q, c in mid.px.items() if top <= q[1] <= int(math.floor(HEAD[1] + 4.0))}),
            "Sheriff_GoreHat": crop({q: c for q, c in mid.px.items() if q[1] < top}),
            "Sheriff_GoreBadge": crop(star(0.0, "ember")[0].px)}


def write_rig(path, cell, muzzles, hat_top):
    w, h, ox, oy = cell
    m = ["MuzzleLevelX = %d, MuzzleLevelY = %d" % (round(muzzles[0][0] * 2), round(muzzles[0][1] * 2)),
         "MuzzleUpX = %d, MuzzleUpY = %d" % (round(muzzles[1][0] * 2), round(muzzles[1][1] * 2)),
         "MuzzleDownX = %d, MuzzleDownY = %d" % (round(muzzles[2][0] * 2), round(muzzles[2][1] * 2))]
    L = ["// <auto-generated> by art/oldbrasstown/make_sheriff_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.OldBrassTown.NPCs",
         "{",
         "\t/// <summary>The Sheriff's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells with",
         "\t/// 2 px under each; the origin is the ground point under his hips. Aim and Shoot hold three frames each: level, up and",
         "\t/// down (<see cref=\"AimAngle\"/> degrees); the muzzles are from the origin, facing left; HatTopY is the hat's crown. The",
         "\t/// star sheets hold <see cref=\"StarSpin\"/> spin frames of <see cref=\"StarCell\"/> px (the hostile one then as many",
         "\t/// telegraph frames, the rim lit).</summary>",
         "\tpublic static class SheriffRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Idle = %d, IdleFrames = 2, Aim = %d, AimFrames = 3, Shoot = %d, ShootFrames = 3, Reload = %d, ReloadFrames = 4;"
         % (WALK, INDEX["Idle0"], INDEX["Aim0"], INDEX["Shoot0"], INDEX["Reload0"]),
         "\t\tpublic const int AimAngle = %d, HatTopY = %d;" % (abs(int(AIM_ANGLES[1])), round(hat_top * 2)),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d;" % round(STRIDE * 2 / (WALK / 2)),
         "\t\tpublic const int %s;" % ", ".join(m),
         "\t\tpublic const int StarSpin = %d, StarCell = %d;" % (SPIN, STAR * 2),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Sheriff%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Sheriff_Glow.png")
    hat_top = min(y for (_, y) in frames[INDEX["Idle0"]][1].px)
    write_rig(OUT + "NPCs/SheriffRigData.cs", cell, [frames[INDEX["Aim%d" % k]][4] for k in range(3)], hat_top)
    sheet, glow = star_sheets("ember")
    export(sheet, OUT + "Projectiles/SheriffStar.png")
    export(glow, OUT + "Projectiles/SheriffStar_Glow.png")
    sheet, glow = star_sheets("aether")
    export(sheet, OUT + "Minions/SheriffStarMinion.png")
    export(glow, OUT + "Minions/SheriffStarMinion_Glow.png")
    export(badge_icon(), OUT + "Minions/SheriffBadge.png")
    export(buff_icon(), OUT + "Minions/SheriffStarBuff.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 48, 46
    cols = 6
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2 + 16), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
                t.alpha_composite(to_image(cv.px, -cw // 2 - 4, -ch + 3, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
    extras = Image.new("RGBA", (cw * cols, 16), (36, 40, 48, 255))
    x = 2
    for k in range(SPIN):
        cv, _ = star(k * 12.0, "ember")
        extras.alpha_composite(to_image(cv.px, 0, 0, STAR, STAR), (x, 1))
        x += STAR + 1
    for k in range(SPIN):
        cv, _ = star(k * 12.0, "aether")
        extras.alpha_composite(to_image(cv.px, 0, 0, STAR, STAR), (x, 1))
        x += STAR + 1
    extras.alpha_composite(badge_icon(), (x + 4, 1))
    sheet.paste(extras, (0, ch * rows * 2))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
