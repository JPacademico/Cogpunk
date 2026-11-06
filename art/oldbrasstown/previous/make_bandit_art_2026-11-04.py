"""Source for the Brass Bandit, an enemy of Old Brass Town (D4), 2026-11-04. Run from the repo root:

    python -P art/oldbrasstown/make_bandit_art.py [--preview FILE]

Design (user, 2026-11-04: "a bandit robot that shoots the player on sight with a rusty revolver: six bullets, then it
runs from the player to reload"): a lanky outlaw robot of dusty brass. A riveted iron head under a wide leather
cowboy hat with a brass band, two ember eyes in a dark visor slit (hostile), a red bandana over the lower face knotted
at the back, a brass chest plate crossed by a leather bandolier of brass cartridges, a leather gun belt with a brass
buckle and a holster, copper sleeves over iron forearms, iron piston legs with brass knees and leather riding boots
with brass spurs, and a rusty revolver (copper rust on an iron barrel, a wooden grip). Three-quarter view facing left
(D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and the far arm, a ramp step darker), middle (the
head, hat, torso and belt), near (the near leg and the near arm with the revolver); the glow sheet holds the eyes and the
muzzle flash. Stable pixels (D4 rule 17): the body moves by whole pixels and is lit in its own space; limbs are lit with
their light's turn snapped to 22.5 degrees.

Frames: Walk x6 (a bow-legged amble, the revolver low at its side), Aim x3 (the arm out level, raised 25 degrees,
lowered 25 degrees: the telegraph holds it, the hammer cocked), Shoot x3 (the same aims, kicked up by the shot, a muzzle
flash), Reload x6 (a run, leaning into it, the cylinder swung out and the far hand thumbing cartridges in).

Outputs:
    Content/OldBrassTown/NPCs/BrassBandit.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/OldBrassTown/NPCs/BrassBanditRigData.cs   cells, origin, frames, the three muzzles (from the origin, facing left)
    Content/OldBrassTown/Projectiles/RustyBullet.png  8 headings (stride 14, 0 = flying right, clockwise): a rusty slug
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
from westbots import (RAMP, WHITE, Xf, Poly, Ellipse, Union, box, Canvas, flat, dome, face, P, despeckle, leg, arm, revolver,  # noqa: E402
                      cowboy_hat, bandolier, holster, I, B, C, E, S, LE)
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"
THIGH, SHIN = 4.4, 4.3
UPPER, FORE = 3.5, 3.4
AIM_ANGLES = (0.0, -25.0, 25.0)            # level, up, down (degrees the arm turns; - raises it. The revolver turns by
                                           # -angle: rig.py turns clockwise on screen, which raises a barrel pointing left)
SLEEVE = "iron"
SHOULDER_NEAR = (-2.2, -16.4)


class Pose:
    def __init__(self, bob=0, lean=0, near_foot=(-1.6, 0.0), far_foot=(1.8, 0.0), near_hand=(-3.6, -11.0), far_hand=(2.6, -11.4),
                 gun=0.0, aim=None, recoil=0, flash=False, reload=False):
        self.bob, self.lean = bob, lean                  # whole px: down, forward (-x)
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_hand, self.far_hand = near_hand, far_hand
        self.gun = gun                                   # the revolver's angle while not aiming (it hangs pointing down-forward)
        self.aim = aim                                   # None, or the aim angle (degrees)
        self.recoil, self.flash, self.reload = recoil, flash, reload


def body(mid, glow, p):
    ox, oy = -p.lean, p.bob
    # the gun belt and holster
    belt = mid.part(Xf(), box(-3.4 + ox, -10.8 + oy, 3.2 + ox, -9.0 + oy), "leather", face((-0.4, -0.5, 0.75), lo=1, hi=2, fixed=True), rust=0.0)
    for (dx, col) in ((0, B[4]), (1, B[3])):
        mid.put(int(math.floor(-2.6 + ox)) + dx, int(math.floor(-10.0 + oy)), col)    # the buckle
    mid.put(int(math.floor(-2.6 + ox)), int(math.floor(-10.6 + oy)), B[5])
    # the torso: a brass chest plate, a riveted seam, a lit rim, the bandolier across it
    torso = mid.part(Xf(), Union(box(-3.8 + ox, -16.8 + oy, 3.2 + ox, -10.6 + oy), Ellipse(-0.3 + ox, -16.8 + oy, 3.6, 1.4)), "brass",
                     face((-0.5, -0.4, 0.75), lo=2, hi=4, gain=1.25, bias=0.1, fixed=True), shadow=(1, 1), rust=0.0)
    for y in (-15.4, -12.4):
        q = (int(math.floor(-2.4 + ox)), int(math.floor(y + oy)))
        if q in torso:
            mid.put(q[0], q[1], B[5])
            mid.put(q[0] + 1, q[1] + 1, B[1])
    for y in range(int(math.floor(-16.0 + oy)), int(math.floor(-11.0 + oy))):          # the plate's centre seam
        q = (int(math.floor(0.6 + ox)), y)
        if q in torso:
            mid.put(q[0], q[1], B[2])
    bandolier(mid, (-2.8 + ox, -16.2 + oy), (2.6 + ox, -11.0 + oy), torso, 4)
    # the neck and the head: an iron dome, a dark visor slit with two ember eyes, the bandana over the lower face
    mid.part(Xf(), box(-1.6 + ox, -18.6 + oy, 0.8 + ox, -16.8 + oy), "iron", flat(2), rust=0.0)
    hc = (-0.9 + ox, -20.4 + oy)
    head = mid.part(Xf(), Ellipse(hc[0], hc[1], 3.1, 3.0), "brass", dome(hc[0] - 1.0, hc[1] - 1.2, 3.4, lo=2, hi=5, gain=1.3, bias=0.2, fixed=True),
                    shadow=(1, 1), rust=0.0)
    q = (int(math.floor(hc[0] + 1.8)), int(math.floor(hc[1] - 0.4)))
    if q in head:
        mid.put(q[0], q[1], B[1])                                # the ear bolt
        mid.put(q[0] - 1, q[1] - 1, B[4])
    vy = int(math.floor(hc[1] - 0.8))
    for x in range(int(math.floor(hc[0] - 3.0)), int(math.floor(hc[0] + 1.4))):
        for y in (vy, vy + 1):
            if (x, y) in head:
                mid.put(x, y, I[0])                              # the visor slit, two rows deep
    for ex in (hc[0] - 2.4, hc[0] - 0.4):
        q = (int(math.floor(ex)), vy)
        mid.put_glow(q[0], q[1], E[3])
        glow.put_glow(q[0], q[1], E[3])
    # the bandana: over the mouth, its point hanging on the chest, knotted at the back
    bandana = mid.part(Xf(), Poly([(hc[0] - 3.3, hc[1] + 0.8), (hc[0] + 2.2, hc[1] + 0.6), (hc[0] + 2.0, hc[1] + 2.2), (hc[0] - 0.6, hc[1] + 4.6),
                                   (hc[0] - 2.4, hc[1] + 3.0), (hc[0] - 3.2, hc[1] + 2.0)]), "ember",
                       face((-0.5, -0.4, 0.75), lo=1, hi=2, bias=-0.2, fixed=True), rust=0.0)
    q = (int(math.floor(hc[0] - 1.8)), int(math.floor(hc[1] + 1.6)))
    if q in bandana:
        mid.put(q[0], q[1], S[1])                                # a white polka dot
    knot = (int(math.floor(hc[0] + 2.6)), int(math.floor(hc[1] + 1.0)))
    for (dx, dy, col) in ((0, 0, E[1]), (1, 0, E[1]), (1, 1, E[0]), (2, 1, E[1]), (2, 2, E[0])):
        mid.put(knot[0] + dx, knot[1] + dy, col)                  # the knot and its tail at the back
    # the hat
    cowboy_hat(mid, (hc[0] + 0.2, hc[1] - 6.6), 10.8, 3.9, 5.8, tilt=-4.0)
    del belt, head
    return (SHOULDER_NEAR[0] + ox, SHOULDER_NEAR[1] + oy), (1.8 + ox, -16.6 + oy), (-0.8 + ox, -9.4 + oy), (1.0 + ox, -9.6 + oy)


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
        fist, u = arm(near, sh_near, hand, 0, UPPER, FORE, sleeve=SLEEVE, glove="leather")
        muzzle = revolver(near, (fist[0] + 0.4, fist[1] - 0.2), -p.aim + (12.0 if p.recoil else 0.0), 0, flash=p.flash, glow=glow)
        arm(far, sh_far, (sh_far[0] + 0.6, sh_far[1] + 4.6), 1, UPPER, FORE, sleeve=SLEEVE, glove="leather")   # the far hand at the belt
    elif p.reload:
        fist, u = arm(near, sh_near, (p.near_hand[0] - p.lean, p.near_hand[1] + p.bob), 0, UPPER, FORE, sleeve=SLEEVE, glove="leather")
        revolver(near, (fist[0] + 0.2, fist[1] - 0.2), -55.0, 0, open_cylinder=True)
        arm(far, sh_far, (p.far_hand[0] - p.lean, p.far_hand[1] + p.bob), 1, UPPER, FORE, sleeve=SLEEVE, glove="leather")
    else:
        holster(near, (hip_near[0] - 1.6, hip_near[1] - 0.6))
        arm(near, sh_near, (p.near_hand[0] - p.lean, p.near_hand[1] + p.bob), 0, UPPER, FORE, sleeve=SLEEVE, glove="leather")
        arm(far, sh_far, (p.far_hand[0] - p.lean, p.far_hand[1] + p.bob), 1, UPPER, FORE, sleeve=SLEEVE, glove="leather")
    for cv in (far, mid, near):
        despeckle(cv)
    return far, mid, near, glow, muzzle


WALK = 6
STRIDE = 4.6
RUN_STRIDE = 6.4


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
                near_hand=(-3.6 - swing, -11.0), far_hand=(2.6 + swing, -11.4), gun=62.0)


def reload_pose(k):
    nf, ff = cycle_foot(k, WALK, RUN_STRIDE, 2.4), cycle_foot(k + WALK // 2, WALK, RUN_STRIDE, 2.4)
    return Pose(bob=1 if k % 3 == 1 else 0, lean=1, near_foot=(nf[0] - 1.8, nf[1]), far_foot=(ff[0] + 1.8, ff[1]),
                near_hand=(-5.0, -14.6), far_hand=(-3.2 + (1 if k % 2 else 0), -14.0), reload=True)


FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Aim%d" % k, Pose(aim=a, near_foot=(-2.4, 0.0), far_foot=(2.4, 0.0))) for k, a in enumerate(AIM_ANGLES)]
          + [("Shoot%d" % k, Pose(aim=a, recoil=1, flash=True, near_foot=(-2.4, 0.0), far_foot=(2.4, 0.0))) for k, a in enumerate(AIM_ANGLES)]
          + [("Reload%d" % k, reload_pose(k)) for k in range(WALK)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The rusty bullet (8 headings, never rotated as a bitmap) and the gores
# ================================================================================================
def bullet(heading_deg, cell=7):
    """A rusty slug flying along heading_deg (0 = right, clockwise): a copper head, an iron body, a short steam-grey
    smoke streak behind it."""
    cv = Canvas()
    c = (cell - 1) / 2.0
    xf = Xf.pose(heading_deg, (0.0, 0.0), (c + 0.5, c + 0.5))
    cv.part(xf, Poly([(-3.4, -0.5), (-1.0, -0.6), (-1.0, 0.6), (-3.4, 0.5)]), "steam", flat(1, bevel=False), outline=False, rust=0.0)
    cv.part(xf, Ellipse(0.6, 0.0, 1.9, 1.2), "copper", dome(0.2, -0.4, 2.0, lo=2, hi=4, fixed=True), rust=0.0)
    return to_image(cv.px, 0, 0, cell, cell)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Walk0"])
    _, _, near_aim, _, _ = frame(dict(FRAMES)["Aim0"])
    return {"BrassBandit_GoreHead": crop({q: c for q, c in mid.px.items() if -23 <= q[1] <= -17}),
            "BrassBandit_GoreHat": crop({q: c for q, c in mid.px.items() if q[1] < -23}),
            "BrassBandit_GoreGun": crop({q: c for q, c in near_aim.px.items() if q[0] <= -9})}


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
    export(vertical([bullet(k * 45.0) for k in range(8)]), OUT + "Projectiles/RustyBullet.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 40, 34
    cols = 6
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
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
