"""Source for the Sheriff, Old Brass Town's rare mini-boss, his sheriff stars and the Sheriff Badge (D4), 2026-11-04.
Run from the repo root:

    python -P art/oldbrasstown/make_sheriff_art.py [--preview FILE]

Design (user, 2026-11-04: "a sheriff robot mini boss with three sheriff stars that float above him and attack the player
then come back to him every 2 seconds; he also shoots six bullets then reloads; hard to kill; drops the sheriff badge, a
summon weapon whose flying sheriff stars hover above the player and attack enemies"): a tall, broad robot lawman. An
iron head lit from the top-left with two ember eyes (hostile) under a heavy brow, a brass handlebar moustache over an
iron jaw plate, a big leather hat with a brass band and a little star on it, a long leather duster coat to the knees
(its tails swinging as he walks) open over a brass waistcoat with the sheriff's star badge and a watch chain, leather
sleeves over iron forearms, leather gloves, dark iron trousers, riding boots with brass spurs, and a polished revolver
(no rust: the law keeps its gun clean). Three-quarter view facing left (D4 rule 13).

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and the far arm, a ramp step darker), middle (the
near leg drawn first so the coat covers its thigh, then the coat, waistcoat, head and hat), near (the near arm and the
revolver); the glow sheet holds the eyes and the muzzle flash. Stable pixels (D4 rule 17): whole-pixel bobs, parts lit in
their own space, limbs with their light's turn snapped, far limbs one flat tone.

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
from westbots import (RAMP, WHITE, Xf, Poly, Ellipse, Union, box, Canvas, flat, dome, face, P, despeckle, leg, arm, revolver,  # noqa: E402
                      cowboy_hat, I, B, C, E, S, LE)
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"
A = RAMP["aether"]
THIGH, SHIN = 5.0, 5.0
UPPER, FORE = 4.0, 3.9
AIM_ANGLES = (0.0, -25.0, 25.0)
SLEEVE = "leather"
HIP_Y = -10.8


class Pose:
    def __init__(self, bob=0, near_foot=(-1.8, 0.0), far_foot=(2.0, 0.0), near_hand=(-3.0, -12.6), far_hand=(3.4, -12.8),
                 aim=None, recoil=0, flash=False, reload=False, tails=0, load=0):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_hand, self.far_hand = near_hand, far_hand
        self.aim, self.recoil, self.flash, self.reload = aim, recoil, flash, reload
        self.tails = tails                               # whole px the coat tails swing back (+) or forward (-)
        self.load = load                                 # 0 / 1 / 2: the far hand at the belt, on its way, at the cylinder


def star_badge(cv, at):
    """The sheriff's star on the waistcoat: five points, a lit centre, a glint."""
    x, y = at
    rows = ("..b..",
            "bbBbb",
            ".bBd.",
            ".b.d.")
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            col = {"b": B[4], "B": B[5], "d": B[2]}.get(ch)
            if col:
                cv.put(x + i - 2, y + j - 1, col)
    cv.put(x - 1, y, WHITE)


def body(mid, glow, p):
    oy = p.bob
    # the coat: leather from the shoulders to the knees, its tails behind; the waistcoat shows in its open front
    t = p.tails
    coat = Poly([(-4.2, -20.2 + oy), (3.8, -20.2 + oy), (4.6, -13.0 + oy), (5.4 + t, -5.2 + oy), (2.0 + t * 0.5, -4.6 + oy),
                 (-1.0, -5.4 + oy), (-4.4, -5.0 + oy), (-5.0, -12.6 + oy)])
    cinner = mid.part(Xf(), coat, "leather", face((-0.5, -0.4, 0.75), lo=1, hi=2, gain=1.2, bias=0.15, fixed=True), shadow=(1, 1), rust=0.0)
    for y in range(int(math.floor(-19.0 + oy)), int(math.floor(-6.0 + oy))):     # the coat's back seam
        q = (3, y)
        if q in cinner and y % 3 != 0:
            mid.put(q[0], q[1], LE[0])
    for (x0, y0) in ((-4.0, -9.0), (2.6, -9.0)):                                # pocket flaps on the coat's skirt
        for dx in range(3):
            q = (int(math.floor(x0)) + dx, int(math.floor(y0 + oy)))
            if q in cinner:
                mid.put(q[0], q[1], LE[0])
                if (q[0], q[1] - 1) in cinner:
                    mid.put(q[0], q[1] - 1, LE[2])
    # the waistcoat in the coat's open front (clear of the near arm), the badge on it, a watch chain
    vest = Poly([(-2.6, -19.6 + oy), (1.8, -19.6 + oy), (1.6, -11.0 + oy), (-2.4, -11.0 + oy)])
    vinner = mid.part(Xf(), vest, "brass", face((-0.5, -0.4, 0.75), lo=2, hi=4, gain=1.25, fixed=True), rust=0.0)
    for y in (-15.6, -13.4):
        q = (-2, int(math.floor(y + oy)))
        if q in vinner:
            mid.put(q[0], q[1], B[1])                           # its buttons
    for (dx, dy) in ((0, 0), (1, 1), (2, 1)):
        q = (-1 + dx, int(math.floor(-13.0 + oy)) + dy)
        if q in vinner:
            mid.put(q[0], q[1], B[5] if dx % 2 == 0 else B[3])  # the watch chain
    star_badge(mid, (0, int(math.floor(-17.6 + oy))))
    # the lapels: lit leather folds either side of the opening, and the opening's lit edge down the coat
    for (pts, col) in ((((-3.6, -20.0), (-2.0, -20.0), (-2.8, -16.6)), LE[2]), (((1.4, -20.0), (2.8, -20.0), (2.0, -17.0)), LE[1])):
        lap = mid.raster(Xf(), Poly([(x, y + oy) for (x, y) in pts]))
        for q in lap:
            mid.put(q[0], q[1], col)
    for y in range(int(math.floor(-16.4 + oy)), int(math.floor(-11.0 + oy))):
        q = (-3, y)
        if q in cinner:
            mid.put(q[0], q[1], LE[2])
    # the gun belt across the coat's opening
    mid.part(Xf(), box(-4.6, -11.4 + oy, 4.2, -9.8 + oy), "leather", flat(1), rust=0.0)
    for (dx, col) in ((0, B[4]), (1, B[3])):
        mid.put(-4 + dx, int(math.floor(-10.6 + oy)), col)          # the buckle
    # the neck and the head
    mid.part(Xf(), box(-1.8, -22.2 + oy, 0.8, -20.0 + oy), "iron", flat(2), rust=0.0)
    hc = (-0.8, -24.0 + oy)
    head = mid.part(Xf(), Ellipse(hc[0], hc[1], 3.6, 3.3), "iron", dome(hc[0] - 1.2, hc[1] - 1.4, 4.0, lo=2, hi=4, gain=1.35, bias=0.25, fixed=True),
                    shadow=(1, 1), rust=0.0)
    ey = int(math.floor(hc[1] - 0.8))
    for x in range(int(math.floor(hc[0] - 3.4)), int(math.floor(hc[0] + 1.0))):
        q = (x, ey - 1)
        if q in head:
            mid.put(q[0], q[1], I[1])                           # the heavy brow
    for ex in (hc[0] - 2.6, hc[0] - 0.4):
        q = (int(math.floor(ex)), ey)
        mid.put_glow(q[0], q[1], E[3])
        glow.put_glow(q[0], q[1], E[3])
    nose = (int(math.floor(hc[0] - 3.6)), ey + 1)
    mid.put(nose[0], nose[1], I[3])                             # the nose plate
    my = ey + 2
    for (dx, col) in ((-4, B[3]), (-3, B[4]), (-2, B[4]), (-1, B[3]), (0, B[4]), (1, B[3])):
        mid.put(int(math.floor(hc[0])) + dx, my, col)             # the handlebar moustache...
    mid.put(int(math.floor(hc[0])) - 5, my - 1, B[3])           # ...its curled tips
    mid.put(int(math.floor(hc[0])) + 2, my - 1, B[2])
    for x in range(int(math.floor(hc[0] - 3.0)), int(math.floor(hc[0] + 1.0))):
        q = (x, my + 1)
        if q in head:
            mid.put(q[0], q[1], I[1] if x % 2 else I[2])          # the jaw plate's grille
    cowboy_hat(mid, (hc[0] + 0.3, hc[1] - 8.0), 13.2, 4.6, 7.2, star=True, tilt=-3.0)
    del head
    return (-2.6, -19.0 + oy), (2.4, -19.2 + oy), (-1.0, HIP_Y + oy), (1.2, HIP_Y - 0.2 + oy)


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    # the near leg goes first on the middle plane, so the coat covers its thigh
    hip_near = (-1.0, HIP_Y + p.bob)
    leg(mid, hip_near, p.near_foot[0], p.near_foot[1], 0, THIGH, SHIN, r_thigh=1.8, r_shin=1.6)
    sh_near, sh_far, _, hip_far = body(mid, glow, p)
    leg(far, hip_far, p.far_foot[0], p.far_foot[1], 1, THIGH, SHIN, r_thigh=1.8, r_shin=1.6)
    muzzle = None
    if p.aim is not None:
        a = math.radians(p.aim)
        reach = UPPER + FORE - 0.4
        hand = (sh_near[0] - math.cos(a) * reach + p.recoil, sh_near[1] + math.sin(a) * reach)
        fist, u = arm(near, sh_near, hand, 0, UPPER, FORE, r_upper=1.8, r_fore=1.5, sleeve=SLEEVE, glove="leather")
        muzzle = revolver(near, (fist[0] + 0.4, fist[1] - 0.2), -p.aim + (14.0 if p.recoil else 0.0), 0, rust=False, flash=p.flash, glow=glow,
                          barrel=6.0)
        arm(far, sh_far, (sh_far[0] + 0.8, sh_far[1] + 6.2), 1, UPPER, FORE, r_upper=1.8, r_fore=1.5, sleeve=SLEEVE, glove="leather")
    elif p.reload:
        fist, u = arm(near, sh_near, (-6.0, -16.4 + p.bob), 0, UPPER, FORE, r_upper=1.8, r_fore=1.5, sleeve=SLEEVE, glove="leather")
        revolver(near, (fist[0] + 0.2, fist[1] - 0.2), -50.0, 0, rust=False, open_cylinder=True, barrel=6.0)
        far_hand = ((0.6, -13.4), (-1.6, -14.6), (-3.6, -15.6))[p.load]       # at the belt, on the way, at the cylinder
        far_hand = (far_hand[0], far_hand[1] + p.bob)
        arm(far, sh_far, far_hand, 1, UPPER, FORE, r_upper=1.8, r_fore=1.5, sleeve=SLEEVE, glove="leather")
    else:
        fist, u = arm(near, sh_near, (p.near_hand[0], p.near_hand[1] + p.bob), 0, UPPER, FORE, r_upper=1.8, r_fore=1.5, sleeve=SLEEVE,
                      glove="leather")
        revolver(near, (fist[0] + 0.2, fist[1] - 0.2), -70.0, 0, rust=False, barrel=6.0)   # held low, pointing at the ground
        arm(far, sh_far, (p.far_hand[0], p.far_hand[1] + p.bob), 1, UPPER, FORE, r_upper=1.8, r_fore=1.5, sleeve=SLEEVE, glove="leather")
    for cv in (far, mid, near):
        despeckle(cv)
    return far, mid, near, glow, muzzle


WALK = 6
STRIDE = 5.0


def cycle_foot(phase, n, stride, lift):
    t = (phase % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    nf, ff = cycle_foot(k, WALK, STRIDE, 1.8), cycle_foot(k + WALK // 2, WALK, STRIDE, 1.8)
    swing = 1 if k in (1, 2) else (-1 if k in (4, 5) else 0)
    return Pose(bob=1 if k % 3 == 1 else 0, near_foot=(nf[0] - 1.8, nf[1]), far_foot=(ff[0] + 2.0, ff[1]),
                near_hand=(-3.0 - swing, -12.6), far_hand=(3.4 + swing, -12.8), tails=1 if k in (0, 1, 3, 4) else 0)


FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Idle0", Pose()), ("Idle1", Pose(bob=1, tails=1))]
          + [("Aim%d" % k, Pose(aim=a, near_foot=(-2.8, 0.0), far_foot=(2.8, 0.0))) for k, a in enumerate(AIM_ANGLES)]
          + [("Shoot%d" % k, Pose(aim=a, recoil=1, flash=True, near_foot=(-2.8, 0.0), far_foot=(2.8, 0.0))) for k, a in enumerate(AIM_ANGLES)]
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
    return {"Sheriff_GoreHead": crop({q: c for q, c in mid.px.items() if -28 <= q[1] <= -20}),
            "Sheriff_GoreHat": crop({q: c for q, c in mid.px.items() if q[1] < -28}),
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
    cw, ch = 44, 40
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
