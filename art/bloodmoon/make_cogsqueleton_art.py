"""Source for the Cogsqueleton (D4), the skeleton the Mechromancer raises (user, 2026-11-12: "summon cogsqueletons"; the
design is my call). Run from the repo root:

    python -P art/bloodmoon/make_cogsqueleton_art.py [--preview FILE]

Design: a skeleton of old bone held together with brass. Its ribcage is a brass cog (the teeth stand in for the ribs) with
a spark of the Mechromancer's soul fire in its hub, its pelvis a half-cog, little brass cogs for knees and shoulders, a bone
skull three-quarters to the left with soul-fire eyes and a brass jaw. It walks hunched, claws forward, like vanilla's
skeletons. Vanilla's proportions (a Skeleton stands as tall as a player): 22 art px, 44 in game.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and arm, a step darker), middle (the near leg, the
pelvis, the spine, the cog, the skull), near (the near arm); the glow sheet holds the eyes and the cog's spark. Stable
pixels (D4 rule 17): the body is placed by whole-pixel bobs, the limbs lit with their light's turn snapped.

Frames: Rise x4 (it climbs out of the ground where the Mechromancer's spell marked it: the same crouched body drawn lower
and cut at the ground line, so the earth hides what is still under it), Walk x6.

Outputs:
    Content/BloodMoon/NPCs/Cogsqueleton.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/BloodMoon/NPCs/CogsqueletonRigData.cs
    Content/BloodMoon/Gores/Cogsqueleton_GoreSkull.png, _GoreCog.png, _GoreBone.png
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
from westbots import RAMP, Xf, Ellipse, Canvas, flat, dome, P, finish, limb, G, IV, ST  # noqa: E402
from rig import ik  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/BloodMoon/"
GH = RAMP["ghost"]
THIGH, SHIN = 4.6, 4.4
UPPER, FORE = 3.8, 3.8
HIP_Y = -9.4
WALK = 6
STRIDE = 5.0


class Pose:
    def __init__(self, bob=0, near_foot=(-1.6, 0.0), far_foot=(2.0, 0.0), near_hand=(-6.4, -12.6), far_hand=(-3.0, -13.2),
                 crouch=0, sink=0):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot
        self.near_hand, self.far_hand = near_hand, far_hand
        self.crouch = crouch          # whole px the body is lowered (the rise's last frame: still hunched)
        self.sink = sink              # whole px the whole figure is under the ground (the rise)


def cog(cv, glow, c, r, teeth, rot, lo=3, hi=8, spark=True):
    """A brass cog lit from the top-left, outlined; a soul-fire spark in its hub (glow)."""
    for y in range(int(c[1] - r - 2), int(c[1] + r + 3)):
        for x in range(int(c[0] - r - 2), int(c[0] + r + 3)):
            du, dv = x + 0.5 - c[0], y + 0.5 - c[1]
            rr = math.hypot(du, dv)
            th = math.degrees(math.atan2(dv, du)) - rot
            tooth = math.cos(math.radians(th * teeth)) > 0.25
            outer = r + (1.1 if tooth else 0.0)
            if rr > outer:
                continue
            if spark and rr < 1.0:
                cv.put_glow(x, y, GH[5])
                glow.put_glow(x, y, GH[5])
                continue
            if rr > outer - 0.75 or (spark and rr < 1.6):
                cv.put(x, y, G[1])
                continue
            light = -(du * 0.62 + dv * 0.78) / max(0.8, rr)
            cv.put(x, y, G[max(lo, min(hi, 5 + int(round(light * 2.6))))])


# The skull, placed by hand (8 x 8: three-quarters to the left): digits are ivory shades (0 the outline), D a socket,
# E/e the soul-fire eye (glow), n the nasal hole, T/t brass teeth, j the brass jaw.
SKULL = ("..0000..",
         ".044430.",
         "05544320",
         "0DD4DD30",
         "0DE3De20",
         ".0n43210",
         ".0TtTt0.",
         "..0jj0..")
SKULL_AT = (-5, -24)


def skull(mid, glow, oy):
    x0, y0 = SKULL_AT[0], SKULL_AT[1] + oy
    for dy, row in enumerate(SKULL):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            q = (x0 + dx, y0 + dy)
            if ch.isdigit():
                mid.put(q[0], q[1], IV[int(ch)])
            elif ch in "Dn":
                mid.put(q[0], q[1], IV[0])
            elif ch in "Ee":
                c = GH[5] if ch == "E" else GH[4]
                mid.put_glow(q[0], q[1], c)
                glow.put_glow(q[0], q[1], c)
            elif ch == "T":
                mid.put(q[0], q[1], G[7])
            elif ch == "t":
                mid.put(q[0], q[1], G[4])
            else:
                mid.put(q[0], q[1], G[3])
    mid.put(x0 + 6, y0 + 5, ST[7])                               # a steel rivet at the jaw's hinge
    mid.put(x0 + 6, y0 + 6, ST[3])


def body(mid, glow, p):
    oy = p.bob + p.crouch
    # the pelvis: a brass half-cog under the spine
    for y in range(int(HIP_Y - 1 + oy), int(HIP_Y + 2 + oy)):
        for x in range(-3, 3):
            u = x + 0.5
            if abs(u) <= 2.6 - (y - (HIP_Y - 1 + oy)) * 0.6:
                mid.put(x, y, G[6] if u < 0 else G[4])
    for x in (-3, -1, 1):
        mid.put(x, int(HIP_Y - 2 + oy), G[5])
    mid.put(-1, int(HIP_Y + oy), ST[6])                          # the bolt that holds the hips to the spine
    mid.put(0, int(HIP_Y + oy), ST[4])
    rag = ((-4, 0, 3), (-3, 0, 4), (-2, 0, 4), (-1, 0, 3), (0, 0, 3), (1, 0, 2), (2, 0, 2),
           (-4, 1, 2), (-3, 1, 4), (-2, 1, 3), (-1, 1, 2), (1, 1, 1), (2, 1, 2),
           (-3, 2, 3), (-2, 2, 2), (2, 2, 1), (-3, 3, 1))
    ry = int(HIP_Y + 1 + oy)
    for (dx, dy, k) in rag:
        mid.put(dx, ry + dy, RAMP["crimson"][k])
    # the spine: vertebrae from the pelvis up to the neck, lit on the left
    for y in range(int(-19 + oy), int(HIP_Y - 1 + oy)):
        mid.put(-1, y, IV[5] if y % 2 else IV[3])
        mid.put(0, y, IV[2] if y % 2 else IV[1])
    # the ribs: three bone arcs a side curving round from the spine (the far side's shorter: three-quarters), lit on top
    for (k, y0) in enumerate((-18.4, -16.6, -14.8)):
        for x in range(-5 + k // 2, 3 - k // 2):
            if x in (-1, 0):
                continue
            u = x + 0.5
            y = int(math.floor(y0 + 0.16 * u * u + oy))
            mid.put(x, y, IV[4] if x < 0 else IV[3])
            if (x, y + 1) not in mid.px:
                mid.put(x, y + 1, IV[1])
    # the heart: a little brass cog behind the ribs with a spark of the Mechromancer's soul fire
    cog(mid, glow, (-1.6, -15.8 + oy), 1.9, 6, 10.0, lo=4, hi=8)
    # the neck
    for y in range(int(-20 + oy), int(-18 + oy)):
        mid.put(-2, y, IV[4])
        mid.put(-1, y, IV[2])
    skull(mid, glow, oy)
    return (-2.6, -17.8 + oy), (1.6, -18.0 + oy), (-1.0, HIP_Y + oy), (0.8, HIP_Y - 0.2 + oy)


def bone_limb(cv, a, b, depth):
    """A bone 3-4 px thick, so its outline leaves bone-white inside (vanilla's skeletons: light bones, dark edges)."""
    limb(cv, a, b, 1.55, "ivory", depth, lo=3 if depth == 0 else 2, hi=5 if depth == 0 else 3)


def leg(cv, glow, hip, foot, depth):
    knee, ankle = ik(hip, foot, THIGH, SHIN, -1)
    bone_limb(cv, hip, knee, depth)
    bone_limb(cv, knee, ankle, depth)
    if depth == 0:
        cog(cv, glow, (math.floor(knee[0]) + 0.5, math.floor(knee[1]) + 0.5), 1.3, 6, 0.0, spark=False)   # a brass knee
    q = P(Xf(), ankle)
    fy = min(0, q[1])
    for dx in (-2, -1, 0):                                       # the foot: bone toes pointing forward (left), a heel
        cv.put(q[0] + dx, fy, IV[3 if depth == 0 else 2])
    cv.put(q[0] - 2, fy, IV[1])
    for dx in (-2, -1, 0):
        cv.put(q[0] + dx, fy - 1, IV[4 if depth == 0 and dx > -2 else 2])


def arm(cv, glow, shoulder, hand, depth):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)
    bone_limb(cv, shoulder, elbow, depth)
    bone_limb(cv, elbow, wrist, depth)
    if depth == 0:
        cog(cv, glow, (math.floor(shoulder[0]) + 0.5, math.floor(shoulder[1]) + 0.5), 1.3, 6, 15.0, spark=False)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    a = math.atan2(d[1], d[0])
    h = P(Xf(), (wrist[0] + math.cos(a) * 1.4, wrist[1] + math.sin(a) * 1.4))
    hand = ((0, 0, 4), (-1, 0, 4), (0, 1, 3), (-1, 1, 2), (-2, 0, 3), (-2, 1, 1))   # a bony hand, its fingers curled
    for (dx, dy, k) in hand:
        cv.put(h[0] + dx, h[1] + dy, IV[k if depth == 0 else max(1, k - 2)])


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    hip_near = (-1.0, HIP_Y + p.bob + p.crouch)
    leg(mid, glow, hip_near, p.near_foot, 0)
    sh_near, sh_far, _, hip_far = body(mid, glow, p)
    leg(far, glow, hip_far, p.far_foot, 1)
    arm(far, glow, sh_far, (p.far_hand[0], p.far_hand[1] + p.bob + p.crouch), 1)
    arm(near, glow, sh_near, (p.near_hand[0], p.near_hand[1] + p.bob + p.crouch), 0)
    for cv in (far, mid, near):
        finish(cv)
    if p.sink:
        for cv in (far, mid, near, glow):
            cv.px = {(x, y + p.sink): c for (x, y), c in cv.px.items() if y + p.sink <= 0}
            cv.glow = {(x, y + p.sink): c for (x, y), c in cv.glow.items() if y + p.sink <= 0}
    return far, mid, near, glow


def cycle_foot(phase, n, stride, lift):
    t = (phase % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, -round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    nf, ff = cycle_foot(k, WALK, STRIDE, 1.6), cycle_foot(k + WALK // 2, WALK, STRIDE, 1.6)
    swing = (0, 1, 1, 0, -1, -1)[k]
    return Pose(bob=1 if k % 3 == 1 else 0, near_foot=(nf[0] - 1.6, nf[1]), far_foot=(ff[0] + 2.0, ff[1]),
                near_hand=(-6.4 - swing, -12.6), far_hand=(-3.0 + swing, -13.2))


RISE = (Pose(crouch=2, sink=16, near_hand=(-6.0, -20.0), far_hand=(-2.0, -21.0)),
        Pose(crouch=2, sink=10, near_hand=(-6.4, -18.0), far_hand=(-2.4, -19.0)),
        Pose(crouch=2, sink=5, near_hand=(-6.6, -15.0), far_hand=(-2.8, -15.6)),
        Pose(crouch=1, sink=0, near_hand=(-6.6, -13.6), far_hand=(-3.0, -14.0)))
FRAMES = [("Rise%d" % k, p) for k, p in enumerate(RISE)] + [("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Walk0"])
    return {"Cogsqueleton_GoreSkull": crop({q: c for q, c in mid.px.items() if q[1] <= -19}),
            "Cogsqueleton_GoreCog": crop({q: c for q, c in mid.px.items() if -20 < q[1] <= -11 and q[0] >= -5}),
            "Cogsqueleton_GoreBone": crop({q: c for q, c in near.px.items()})}


def write_rig(path, cell):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/bloodmoon/make_cogsqueleton_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.BloodMoon.NPCs",
         "{",
         "\t/// <summary>The Cogsqueleton's grid sheets (game px, facing left): far, middle, near and glow, equal cells with 2 px",
         "\t/// under each; the origin is the ground under its feet.</summary>",
         "\tpublic static class CogsqueletonRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Rise = 0, RiseFrames = 4, Walk = %d, WalkFrames = %d, WalkStep = %d;" % (INDEX["Walk0"], WALK, int(round(STRIDE * 2 / WALK * 2))),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Cogsqueleton%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Cogsqueleton_Glow.png")
    write_rig(OUT + "NPCs/CogsqueletonRigData.cs", cell)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=8):
    cw, ch = 24, 30
    cols = 5
    rws = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rws), (48, 18, 24, 255))
    for k, (n, p) in enumerate(FRAMES):
        t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cvs in frame(p)[:3]:
            t.alpha_composite(to_image(cvs.px, -cw // 2, -ch + 3, cw, ch))
        sheet.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
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
