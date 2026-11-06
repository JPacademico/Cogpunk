"""Source for the Brass Bandit, an enemy of Old Brass Town (D4). Run from the repo root:

    python -P art/oldbrasstown/make_bandit_art.py [--preview FILE]

Design (user, 2026-11-04: "a bandit robot that shoots the player on sight with a rusty revolver: six bullets, then it
runs from the player to reload"). Redrawn 2026-11-05 (user: "not matching the necessary pixel art detail quality (Metal
Slug level)"; docs/design/pixel-art-study.md; the 2026-11-04 version is in art/oldbrasstown/previous/): a stocky outlaw
robot in vanilla's 2.5-heads proportions. A polished gilt kettle of a head with a riveted ear bolt, a dark steel visor
slit and two ember eyes (hostile), a crimson bandana over the lower face (folds, two ivory polka dots, a knot with two
tails at the back), a big felt cowboy hat (a crease, a band of gilt conchos, a bullet hole through the crown), a hide
vest over a denim shirt with gilt buttons, a hide bandolier of gilt cartridges, a gun belt with a big gilt buckle and a
stitched holster, thick denim sleeves over steel forearms with gilt cuffs, hide gloves, denim jeans with steel knee caps,
big riding boots with steel toe caps and gilt spurs, and a chunky rusty six-shooter (a steel frame with copper rust, an
oak grip with its grain). Three-quarter view facing left (D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and the far arm, flat and a step darker), middle (the
head, hat, torso and belt), near (the near leg and the near arm with the revolver); the glow sheet holds the eyes and the
muzzle flash. Stable pixels (D4 rule 17): the body moves by whole pixels and is lit and textured in its own space; limbs
are lit with their light's turn snapped to 22.5 degrees.

Frames: Walk x6 (a bow-legged amble, the hand by the holster), Aim x3 (the arm out level, raised 25 degrees, lowered 25
degrees: the telegraph holds it, the hammer cocked), Shoot x3 (the same aims, kicked up by the shot, a muzzle flash),
Reload x6 (a run, leaning into it, the cylinder swung out and the far hand thumbing cartridges in).

Outputs:
    Content/OldBrassTown/NPCs/BrassBandit.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/OldBrassTown/NPCs/BrassBanditRigData.cs   cells, origin, frames, the three muzzles (from the origin, facing left)
    Content/OldBrassTown/Projectiles/RustyBullet.png  16 headings (stride 16, 0 = flying right, clockwise): a rusty slug
    Content/OldBrassTown/Gores/BrassBandit_GoreHead.png, _GoreHat.png, _GoreGun.png
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
from westbots import (RAMP, Xf, Poly, Ellipse, Union, box, Canvas, flat, dome, face, P, finish, leg, arm, revolver,  # noqa: E402
                      cowboy_hat, bandolier, holster, texture, glint, ST, G, H, K, D, IV, E)
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"
THIGH, SHIN = 3.9, 3.9
UPPER, FORE = 3.4, 3.3
AIM_ANGLES = (0.0, -25.0, 25.0)            # level, up, down (degrees the arm turns; - raises it. The revolver turns by
                                           # -angle: rig.py turns clockwise on screen, which raises a barrel pointing left)
SHOULDER_NEAR = (-3.4, -16.4)
SHOULDER_FAR = (2.8, -16.8)
HIP_NEAR, HIP_FAR = (-1.0, -10.0), (1.4, -10.2)
HEAD = (-0.8, -22.4)


class Pose:
    def __init__(self, bob=0, lean=0, near_foot=(-1.6, 0.0), far_foot=(1.8, 0.0), near_hand=(-4.6, -11.6), far_hand=(3.6, -12.0),
                 aim=None, recoil=0, flash=False, reload=False, tails=0):
        self.bob, self.lean = bob, lean                  # whole px: down, forward (-x)
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_hand, self.far_hand = near_hand, far_hand
        self.aim = aim                                   # None, or the aim angle (degrees)
        self.recoil, self.flash, self.reload = recoil, flash, reload
        self.tails = tails                               # whole px the bandana's tails flutter up


def fl(v):
    return int(math.floor(v))


def body(mid, glow, p):
    """The middle plane, built in the body's own space and placed by one whole-pixel translation (the bob and the lean),
    so its texture and dither ride with it (D4 rule 17)."""
    ox, oy = -p.lean, p.bob
    bx = Xf.pose(0.0, (0.0, 0.0), (ox, oy))

    def at(x, y):
        return P(bx, (x, y))
    # --- the gun belt: hide, a big gilt buckle with a glint --------------------------------------------------------------
    mid.part(bx, box(-4.8, -11.8, 4.4, -9.6), "hide", texture(face((-0.4, -0.6, 0.75), lo=2, hi=5, ramp_len=7, bias=0.15, fixed=True),
                                                             "speckle", seed=2), rust=0.0)
    qx, qy = at(-3.6, -11.4)
    for (dx, dy, k) in ((0, 0, 9), (1, 0, 7), (2, 0, 6), (0, 1, 6), (1, 1, 4), (2, 1, 3)):
        mid.put(qx + dx, qy + dy, G[k])
    # --- the torso: a denim shirt, a hide vest open over it, gilt buttons, the bandolier ---------------------------------
    torso = mid.part(bx, Union(box(-5.0, -17.2, 4.6, -11.0), Ellipse(-0.2, -17.2, 4.8, 1.5)), "denim",
                     texture(face((-0.5, -0.45, 0.75), lo=2, hi=5, ramp_len=6, bias=0.25, fixed=True, dither=0.15), "weave", seed=4),
                     shadow=(1, 1), rust=0.0)
    vest_shade = texture(face((-0.55, -0.4, 0.75), lo=2, hi=6, ramp_len=7, gain=1.3, bias=0.2, fixed=True), "speckle", seed=6, density=0.1)
    front = mid.part(bx, Poly([(-5.2, -17.4), (-2.8, -18.0), (-1.8, -11.0), (-5.2, -11.0)]), "hide", vest_shade, rust=0.0)
    back = mid.part(bx, Poly([(1.2, -18.2), (4.8, -17.2), (4.8, -11.0), (1.6, -11.0)]), "hide", vest_shade, rust=0.0)
    for y in (-16.6, -14.6, -12.6):                                   # the vest's stitched front edge
        q = at(-2.4 + (0.6 if y > -14 else 0.0), y)
        if q in front:
            mid.put(q[0], q[1], H[5])
    for y in (-15.6, -13.4):                                          # gilt buttons on the shirt
        q = at(-0.6, y)
        if q in torso:
            mid.put(q[0], q[1], G[8])
            mid.put(q[0] + 1, q[1] + 1, D[1])
    bandolier(mid, (-4.4 + ox, -17.0 + oy), (4.2 + ox, -11.6 + oy), torso | front | back, 5)
    # --- the neck and the head: a gilt kettle, the visor slit, two ember eyes -------------------------------------------
    mid.part(bx, box(-2.2, -19.4, 1.0, -17.2), "steel", face((-0.5, -0.5, 0.7), lo=2, hi=4, ramp_len=9, fixed=True), rust=0.0)
    hx, hy = HEAD
    head = mid.part(bx, Ellipse(hx, hy, 4.5, 4.6), "gilt",
                    dome(hx - 1.6, hy - 1.8, 5.0, lo=3, hi=8, gain=1.35, bias=0.3, fixed=True, dither=0.18), shadow=(1, 1), rust=0.0)
    g = at(hx - 3.0, hy - 1.8)
    glint(mid, g[0], g[1], "gilt", cross=True)
    q = at(hx + 2.4, hy - 0.6)                                        # the riveted ear bolt
    for (dx, dy, k) in ((0, 0, 6), (1, 0, 4), (0, 1, 3), (1, 1, 2), (-1, 0, 3)):
        if (q[0] + dx, q[1] + dy) in head:
            mid.put(q[0] + dx, q[1] + dy, ST[k])
    vy = at(0.0, hy - 1.4)[1]
    x0, x1 = at(hx - 4.6, 0.0)[0], at(hx + 1.8, 0.0)[0]
    for x in range(x0, x1):
        for y, k in ((vy, 1), (vy + 1, 3)):
            if (x, y) in head:
                mid.put(x, y, ST[k])                                  # the visor slit, two rows deep, lit below
    for ex in (hx - 3.4, hx - 1.2):
        q = (at(ex, 0.0)[0], vy)
        for (dx, col) in ((0, E[3]), (1, E[2])):
            if (q[0] + dx, q[1]) in head:
                mid.put_glow(q[0] + dx, q[1], col)
                glow.put_glow(q[0] + dx, q[1], col)
    # --- the bandana: over the mouth, its point on the chest, folds, polka dots, the knot and its tails ------------------
    bandana = mid.part(bx, Poly([(hx - 4.7, hy + 1.6), (hx + 3.0, hy + 1.2), (hx + 2.8, hy + 3.4), (hx + 0.0, hy + 6.8),
                                 (hx - 2.4, hy + 5.2), (hx - 4.5, hy + 3.6)]), "crimson",
                       texture(face((-0.5, -0.45, 0.75), lo=3, hi=5, ramp_len=6, bias=0.1, fixed=True), "weave", seed=8), rust=0.0)
    for k in range(3):                                                # two folds running down to the point
        for (fx, fy) in ((hx - 2.4 + k * 0.6, hy + 2.8 + k), (hx + 0.8 + k * 0.2, hy + 2.6 + k)):
            q = at(fx, fy)
            if q in bandana:
                mid.put(q[0], q[1], K[2])
    for (dx, dy) in ((-3.2, 2.6), (-0.6, 4.2)):
        q = at(hx + dx, hy + dy)
        if q in bandana:
            mid.put(q[0], q[1], IV[4])                                # ivory polka dots
    knot = at(hx + 3.1, hy + 1.8)
    for (dx, dy, k) in ((0, 0, 3), (1, 0, 2), (1, 1, 1), (2, 1 - p.tails, 3), (3, 1 - p.tails, 2), (2, 2, 2), (3, 3, 1)):
        mid.put(knot[0] + dx, knot[1] + dy, K[k])
    # --- the hat --------------------------------------------------------------------------------------------------------
    cowboy_hat(mid, (hx + 0.5 + ox, hy - 10.6 + oy), 15.6, 6.4, 8.4, tilt=-5.0, hole=True, lo=3)
    return ((SHOULDER_NEAR[0] + ox, SHOULDER_NEAR[1] + oy), (SHOULDER_FAR[0] + ox, SHOULDER_FAR[1] + oy),
            (HIP_NEAR[0] + ox, HIP_NEAR[1] + oy), (HIP_FAR[0] + ox, HIP_FAR[1] + oy))


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    sh_near, sh_far, hip_near, hip_far = body(mid, glow, p)
    leg(far, hip_far, p.far_foot[0] - p.lean, p.far_foot[1], 1, THIGH, SHIN)
    leg(near, hip_near, p.near_foot[0] - p.lean, p.near_foot[1], 0, THIGH, SHIN)
    muzzle = None
    if p.aim is not None:
        a = math.radians(p.aim)
        reach = UPPER + FORE - 0.4
        hand = (sh_near[0] - math.cos(a) * reach + p.recoil, sh_near[1] + math.sin(a) * reach)
        fist, u = arm(near, sh_near, hand, 0, UPPER, FORE)
        muzzle = revolver(near, (fist[0] + 0.6, fist[1] - 0.6), -p.aim + (12.0 if p.recoil else 0.0), 0, flash=p.flash, glow=glow)
        arm(far, sh_far, (sh_far[0] + 0.8, sh_far[1] + 4.8), 1, UPPER, FORE)    # the far hand at the belt
    elif p.reload:
        fist, u = arm(near, sh_near, (p.near_hand[0] - p.lean, p.near_hand[1] + p.bob), 0, UPPER, FORE)
        revolver(near, (fist[0] + 0.2, fist[1] - 0.4), -55.0, 0, open_cylinder=True)
        arm(far, sh_far, (p.far_hand[0] - p.lean, p.far_hand[1] + p.bob), 1, UPPER, FORE)
    else:
        holster(near, (hip_near[0] - 2.0, hip_near[1] - 0.4))
        arm(near, sh_near, (p.near_hand[0] - p.lean, p.near_hand[1] + p.bob), 0, UPPER, FORE)
        arm(far, sh_far, (p.far_hand[0] - p.lean, p.far_hand[1] + p.bob), 1, UPPER, FORE)
    for cv in (far, mid, near):
        finish(cv)
    return far, mid, near, glow, muzzle


WALK = 6
STRIDE = 4.8
RUN_STRIDE = 6.6


def cycle_foot(phase, n, stride, lift):
    t = (phase % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    nf, ff = cycle_foot(k, WALK, STRIDE, 1.6), cycle_foot(k + WALK // 2, WALK, STRIDE, 1.6)
    swing = 1 if k in (1, 2) else (-1 if k in (4, 5) else 0)
    return Pose(bob=1 if k % 3 == 1 else 0, near_foot=(nf[0] - 1.6, nf[1]), far_foot=(ff[0] + 1.8, ff[1]),
                near_hand=(-4.6 - swing, -11.6), far_hand=(3.6 + swing, -12.0), tails=1 if k % 3 == 2 else 0)


def reload_pose(k):
    nf, ff = cycle_foot(k, WALK, RUN_STRIDE, 2.4), cycle_foot(k + WALK // 2, WALK, RUN_STRIDE, 2.4)
    return Pose(bob=1 if k % 3 == 1 else 0, lean=1, near_foot=(nf[0] - 1.8, nf[1]), far_foot=(ff[0] + 1.8, ff[1]),
                near_hand=(-5.6, -14.6), far_hand=(-3.6 + (1 if k % 3 == 1 else 0), -14.0), reload=True, tails=1 if k % 3 == 2 else 0)


FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Aim%d" % k, Pose(aim=a, near_foot=(-2.6, 0.0), far_foot=(2.6, 0.0))) for k, a in enumerate(AIM_ANGLES)]
          + [("Shoot%d" % k, Pose(aim=a, recoil=1, flash=True, near_foot=(-2.6, 0.0), far_foot=(2.6, 0.0), tails=1)) for k, a in enumerate(AIM_ANGLES)]
          + [("Reload%d" % k, reload_pose(k)) for k in range(WALK)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The rusty bullet (16 headings, never rotated as a bitmap) and the gores
# ================================================================================================
HEADINGS = 16


def bullet(heading_deg, cell=7):
    """A rusty slug flying along heading_deg (0 = right, clockwise): a copper nose, a steel jacket. (Its smoke trail
    is drawn by the game, Core/Visuals/SmokeTrails.)"""
    cv = Canvas()
    c = (cell - 1) / 2.0
    xf = Xf.pose(heading_deg, (0.0, 0.0), (c + 0.5, c + 0.5))
    cv.part(xf, Ellipse(-0.6, 0.0, 1.6, 1.05), "steel", flat(4, bevel=False), rust=0.0)
    cv.part(xf, Ellipse(0.9, 0.0, 1.5, 1.05), "copper", dome(0.4, -0.4, 1.8, lo=2, hi=4, fixed=True), outline=False, rust=0.0)
    return to_image(cv.px, 0, 0, cell, cell)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Walk0"])
    _, _, near_aim, _, _ = frame(dict(FRAMES)["Aim0"])
    top = fl(HEAD[1] - 4.6)
    return {"BrassBandit_GoreHead": crop({q: c for q, c in mid.px.items() if top <= q[1] <= fl(HEAD[1] + 3.6)}),
            "BrassBandit_GoreHat": crop({q: c for q, c in mid.px.items() if q[1] < top}),
            "BrassBandit_GoreGun": crop({q: c for q, c in near_aim.px.items() if q[0] <= -10})}


def write_rig(path, cell, muzzles):
    w, h, ox, oy = cell
    m = ["MuzzleLevelX = %d, MuzzleLevelY = %d" % (round(muzzles[0][0] * 2), round(muzzles[0][1] * 2)),
         "MuzzleUpX = %d, MuzzleUpY = %d" % (round(muzzles[1][0] * 2), round(muzzles[1][1] * 2)),
         "MuzzleDownX = %d, MuzzleDownY = %d" % (round(muzzles[2][0] * 2), round(muzzles[2][1] * 2))]
    L = ["// <auto-generated> by art/oldbrasstown/make_bandit_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.OldBrassTown.NPCs",
         "{",
         "\t/// <summary>The Brass Bandit's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells",
         "\t/// with 2 px under each; the origin is the ground point under its hips. Aim and Shoot hold three frames each: level, up",
         "\t/// and down (<see cref=\"AimAngle\"/> degrees); the muzzles are from the origin, facing left.</summary>",
         "\tpublic static class BrassBanditRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Aim = %d, AimFrames = 3, Shoot = %d, ShootFrames = 3, Reload = %d, ReloadFrames = %d;"
         % (WALK, INDEX["Aim0"], INDEX["Shoot0"], INDEX["Reload0"], WALK),
         "\t\tpublic const int AimAngle = %d;" % abs(int(AIM_ANGLES[1])),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d, RunStep = %d;" % (round(STRIDE * 2 / (WALK / 2)), round(RUN_STRIDE * 2 / (WALK / 2))),
         "\t\tpublic const int %s;" % ", ".join(m),
         "\t\t/// <summary>Headings of the rusty bullet's sheet (0 = flying right, clockwise).</summary>",
         "\t\tpublic const int BulletHeadings = %d;" % HEADINGS,
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/BrassBandit%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/BrassBandit_Glow.png")
    write_rig(OUT + "NPCs/BrassBanditRigData.cs", cell, [frames[INDEX["Aim%d" % k]][4] for k in range(3)])
    export(vertical([bullet(k * 360.0 / HEADINGS) for k in range(HEADINGS)]), OUT + "Projectiles/RustyBullet.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 44, 38
    cols = 6
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, glow, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near, glow):
                t.alpha_composite(to_image(cv.px, -cw // 2 - 4, -ch + 3, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
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
