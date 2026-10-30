"""Source for the Puxa-frango, a rare underground robot, and its Chicken Snapper drop (D4), 2026-10-28. Run from the repo
root:

    python -P art/underground/make_puxafrango_art.py [--preview DIR]

Design (user's reference image, 2026-10-28: a cartoon stalker robot): a hunched, creeping machine on long spindly
limbs. A dark blue-grey box of a body bent far forward, a rounded bucket head pushed out in front on a thin neck, with
a dark cap on top, one big angry eye under a heavy brow, a curved white horn on the snout and a little grille mouth.
Thin light steel limbs with dark bolt joints at every knee, ankle, shoulder and elbow, dark rounded clogs for feet, and
C-shaped pincer claws on the long arms that reach forward: the "chicken snapper". Cogpunk palette: the iron ramp's dark
end for the body, its light end for the limbs (the reference's navy body and pale-blue limbs), steam white for the eye
and the horn, brass trim. Three-quarter view facing left (D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets, like the Mech Army walkers): far (far leg and far arm, a ramp step
darker), middle (body, neck, head), near (near leg and near arm). Limbs posed with two-bone IK per frame.
Frames: walk x8 (a creeping, high-stepping stalk), idle x2 (the claw opening and closing), crouch (the lunge's wind-up),
lunge (stretched out, claw wide open), snap (claw shut), air.

Outputs (Content/Underground/):
    NPCs/PuxaFrango.png, PuxaFrango_Far.png, PuxaFrango_Near.png   grid sheets (cells in PuxaFrangoRigData.cs)
    NPCs/PuxaFrangoRigData.cs                                      generated cell sizes, origin, frame indices
    Items/ChickenSnapper.png                                      the claw as an accessory (32x32)
    Gores/PuxaFrango_GoreHead.png, _GoreClaw.png, _GoreLeg.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Ring, box, Canvas, flat, dome, cyl, rivet, line, stripes, ik  # noqa: E402
from make_trashtr0m_art import fs, export, to_image, GROUND_CLIP  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Underground/"
I, B, S, E = (RAMP[k] for k in ("iron", "brass", "steam", "ember"))
N_FRONT = (-0.8, 0.15, 0.58)
N_SIDE = (0.32, -0.08, 0.94)
THIGH, SHIN = 9.0, 9.5
UPPER, FORE = 8.5, 9.5


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


class Pose:
    def __init__(self, hip=(4.0, -17.0), tilt=-38.0, bob=0.0, near_foot=(-3.0, 0.0), far_foot=(6.0, 0.0),
                 near_hand=(-15.0, -6.0), far_hand=(-9.0, -7.0), claw=0.5, head=(0.0, 0.0), knee_up=False):
        self.hip, self.tilt, self.bob = hip, tilt, bob
        self.near_foot, self.far_foot = near_foot, far_foot        # (x, lift)
        self.near_hand, self.far_hand = near_hand, far_hand
        self.claw = claw                                           # 0 shut .. 1 wide open
        self.head = head
        self.knee_up = knee_up


def joint(cv, p, depth=0):
    """A bolt joint: a dark iron disc with a lighter centre (the reference's riveted knees and elbows)."""
    x, y = p
    cv.part(Xf(), Ellipse(x, y, 1.9, 1.9), "iron", flat(1, bevel=False), depth=depth, outline=False, rust=0.0)
    cv.put(int(math.floor(x)), int(math.floor(y)), I[max(1, 3 - depth)])


def limb(cv, a, b, r, depth):
    """A thin pale steel limb (the reference's pale-blue limbs): no full outline at this size (it would swallow the
    colour); lit pale on the top-left, a dark line along the underside instead."""
    xf = Xf()
    pts = cv.raster(xf, Capsule(a, b, r))
    for (x, y) in pts:
        under = (x, y + 1) not in pts or (x + 1, y) not in pts
        top = (x, y - 1) not in pts or (x - 1, y) not in pts
        if under and not top:
            col = I[max(0, 1 - depth)]
        elif top:
            col = I[4 - depth]
        else:
            col = I[3 - depth]
        cv.put(x, y, col)


def leg(cv, hip, foot, lift, depth):
    ankle = (foot, -2.0 - lift)
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)                 # knee forward
    limb(cv, hip, knee, 1.3, depth)
    limb(cv, knee, ankle, 1.2, depth)
    ax, ay = ankle
    cv.part(Xf(), Poly([(ax + 2.0, ay - 0.5), (ax - 2.0, ay - 1.0), (ax - 4.0, ay + 1.0), (ax - 3.5, ay + 2.0), (ax + 2.5, ay + 2.0)]),
            "iron", fs(N_SIDE, lo=1, hi=2, bias=0.0), depth=depth, rust=0.0)  # the dark clog
    joint(cv, knee, depth)
    joint(cv, ankle, depth)


def claw(cv, c, angle, opening, depth):
    """The C-shaped pincer: a ring with a gap that opens forward (towards `angle`, degrees), the upper jaw a little
    heavier; `opening` 0 (shut, a hairline gap) .. 1 (wide)."""
    cx, cy = c
    gap = 14.0 + 56.0 * opening
    xf = Xf.pose(0.0, (0.0, 0.0), c)
    ring = Ring(0.0, 0.0, 1.6, 3.9)
    pts = cv.raster(xf, ring)
    keep = set()
    for (x, y) in pts:
        a = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx))
        d = (a - angle + 540.0) % 360.0 - 180.0
        if abs(d) > gap * 0.5:
            keep.add((x, y))
    for (x, y) in keep:
        edge = any((x + ox, y + oy) not in keep for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x, y - 1) not in keep or (x - 1, y) not in keep
        cv.put(x, y, I[0] if edge and not lit else (I[max(1, 3 - depth)] if lit else I[max(1, 2 - depth)]))
    # the two jaw tips, a pale steel point each
    for side in (-1, 1):
        a = math.radians(angle + side * (gap * 0.5 + 6.0))
        q = (int(math.floor(cx + math.cos(a) * 3.0)), int(math.floor(cy + math.sin(a) * 3.0)))
        if q in keep:
            cv.put(q[0], q[1], S[1] if depth == 0 else I[3])
    return keep


def arm(cv, shoulder, hand, opening, depth):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)             # elbow back/up
    limb(cv, shoulder, elbow, 1.2, depth)
    limb(cv, elbow, wrist, 1.1, depth)
    joint(cv, shoulder, depth)
    joint(cv, elbow, depth)
    ang = math.degrees(math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]))
    cx, cy = wrist[0] + math.cos(math.radians(ang)) * 3.4, wrist[1] + math.sin(math.radians(ang)) * 3.4
    claw(cv, (cx, cy), ang, opening, depth)
    return (cx, cy)


def body(cv, p):
    """Hunched box body, neck and head. Returns the head xf and the shoulder points (near, far)."""
    hip = (p.hip[0], p.hip[1] + p.bob)
    bx = Xf.pose(p.tilt, (0.0, 0.0), hip)
    shell = cv.part(bx, Poly([(-6.5, -15.5), (-4.0, -17.5), (6.0, -17.5), (8.0, -15.0), (8.5, -1.5), (6.5, 1.0), (-5.0, 1.0), (-6.5, -1.0)]),
                    "iron", fs(N_SIDE, lo=1, hi=3, bias=0.05), shadow=(1, 1), rust=0.0)
    front = cv.part(bx, Poly([(-6.5, -15.5), (-4.0, -17.5), (-3.0, -17.0), (-4.5, 0.0), (-6.5, -1.0)]), "iron", fs(N_FRONT, lo=1, hi=3, bias=0.2), rust=0.0)
    # a riveted belly panel with a hazard band, a vent on the back
    plate = cv.part(bx, box(-2.0, -12.0, 6.0, -3.0), "iron", flat(2), rust=0.0)
    stripes(cv, cv.raster(bx, box(-2.0, -5.0, 6.0, -3.0)) & plate, 2, B[4], I[0])
    for q in ((-1.0, -11.0), (5.0, -11.0)):
        rivet(cv, bx, q, "iron", plate)
    for k in range(3):
        line(cv, bx, (6.8, -13.0 + k * 2.0), (6.8, -12.0 + k * 2.0), lambda n: I[0], shell)
    cv.put(*P(bx, (-5.0, -16.0)), I[3])                            # glint on the top-front corner
    del front
    # neck: a thin pipe from the top-front of the box to the head
    neck_a = bx.fwd((-5.0, -15.0))
    head_c = (neck_a[0] - 6.0 + p.head[0], neck_a[1] - 2.0 + p.head[1])
    cv.part(Xf(), Capsule(neck_a, (head_c[0] + 2.0, head_c[1] + 2.0), 1.1), "iron", cyl(neck_a, head_c, 1.1, lo=2, hi=3), rust=0.0)
    hx = Xf.pose(0.0, (0.0, 0.0), head_c)
    # the head: a rounded bucket, a dark cap, the brow, one big angry eye, the horn, a grille mouth
    head = cv.part(hx, Ellipse(0.5, 0.0, 5.6, 4.8) | box(-4.0, -2.5, 5.0, 3.5), "iron", dome(-1.5, -2.0, 6.0, lo=1, hi=3, gain=1.3, bias=0.1),
                   shadow=(1, 1), rust=0.0)
    cv.part(hx, box(-2.5, -6.5, 4.0, -3.8), "iron", flat(1), rust=0.0)          # the cap
    cv.part(hx, box(-1.0, -7.8, 2.5, -6.2), "iron", flat(1), rust=0.0)
    ex, ey = P(hx, (-2.0, -1.0))
    for (dx, dy, col) in ((-1, 0, S[3]), (0, 0, S[3]), (1, 0, S[2]), (2, 0, S[1]), (-1, 1, S[2]), (0, 1, S[2]), (1, 1, S[1]), (2, 1, S[1])):
        cv.put(ex + dx, ey + dy, col)
    cv.put(ex - 1, ey + 1, I[0])                                   # the pupil, looking forward and down
    cv.put(ex, ey + 1, I[0])
    for k in range(5):                                             # the brow, slanting down to the front (angry)
        cv.put(ex - 2 + k, ey - 2 + (1 if k < 2 else 0), I[0])
    horn = cv.part(hx, Poly([(-3.5, 0.5), (-5.0, -1.5), (-8.5, -4.5), (-9.5, -4.0), (-7.5, 0.0), (-5.0, 2.5)]), "steam",
                   dome(-6.0, -2.0, 4.0, lo=0, hi=2, gain=1.3), rust=0.0)
    del horn
    for x in (-3, -1, 1):                                          # grille mouth
        q = P(hx, (x, 3.0))
        if q in head:
            cv.put(q[0], q[1], I[0])
    return bx.fwd((-3.5, -13.5)), bx.fwd((2.0, -14.0)), hip


def frame(p):
    far, mid, near = Canvas(), Canvas(), Canvas()
    sh_near, sh_far, hip = body(mid, p)
    hip_far = (hip[0] + 1.5, hip[1] - 0.5)
    hip_near = (hip[0] - 1.0, hip[1] + 0.5)
    leg(far, hip_far, p.far_foot[0], p.far_foot[1], 1)
    arm(far, sh_far, p.far_hand, p.claw, 1)
    leg(near, hip_near, p.near_foot[0], p.near_foot[1], 0)
    claw_pt = arm(near, sh_near, p.near_hand, p.claw, 0)
    return far, mid, near, claw_pt


WALK = 8
STRIDE = 10.0


def walk_pose(f):
    def foot(phase):
        t = (phase % WALK) / WALK
        if t < 0.5:                                               # planted, sliding back
            return (-STRIDE / 2 + STRIDE * (t / 0.5), 0.0)
        u = (t - 0.5) / 0.5                                       # a high, creeping step forward
        return (STRIDE / 2 - STRIDE * u, 4.0 * math.sin(math.pi * u))
    nf = foot(f)
    ff = foot(f + WALK // 2)
    bob = -0.8 * abs(math.sin(math.pi * f / (WALK / 2)))
    sway = 2.0 * math.sin(2 * math.pi * f / WALK)
    return Pose(bob=bob, near_foot=(nf[0] + 2.0, nf[1]), far_foot=(ff[0] + 4.0, ff[1]),
                near_hand=(-15.0 + sway, -6.0 + abs(sway) * 0.3), far_hand=(-9.0 - sway, -7.0), claw=0.35 + 0.15 * (f % 2))


FRAMES = [("Walk%d" % k, walk_pose(k)) for k in range(WALK)] + [
    ("Idle0", Pose(claw=0.25)),
    ("Idle1", Pose(bob=-0.5, claw=0.8, near_hand=(-16.0, -7.0))),
    ("Crouch", Pose(hip=(5.0, -14.0), tilt=-50.0, near_foot=(-4.0, 0.0), far_foot=(8.0, 0.0), near_hand=(-4.0, -6.0), far_hand=(0.0, -6.0), claw=1.0)),
    ("Lunge", Pose(hip=(2.0, -15.0), tilt=-62.0, near_foot=(10.0, 1.0), far_foot=(14.0, 2.0), near_hand=(-30.0, -12.0), far_hand=(-25.0, -10.0),
                   claw=1.0, head=(-2.0, 1.0))),
    ("Snap", Pose(hip=(2.0, -15.0), tilt=-58.0, near_foot=(9.0, 0.0), far_foot=(13.0, 1.0), near_hand=(-27.0, -11.0), far_hand=(-22.0, -9.0),
                  claw=0.0, head=(-1.0, 1.0))),
    ("Air", Pose(hip=(4.0, -16.0), tilt=-45.0, near_foot=(2.0, 5.0), far_foot=(7.0, 6.0), near_hand=(-20.0, -14.0), far_hand=(-15.0, -12.0), claw=0.7)),
]
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# Chicken Snapper (the claw as an accessory) and gores
# ================================================================================================
def snapper_icon():
    """16x16 -> 32x32: the pincer claw on a stub of forearm with a bolt, a brass band (it's been polished up)."""
    cv = Canvas()
    limb(cv, (13.0, 13.0), (8.5, 8.5), 1.5, 0)
    cv.part(Xf(), Capsule((11.0, 11.0), (10.0, 10.0), 2.1), "brass", flat(3), rust=0.0)
    joint(cv, (13.0, 13.0))
    keep = set()
    xf_c = (5.5, 5.5)
    cv2 = Canvas()
    keep = claw(cv2, xf_c, -135.0, 0.65, 0)
    # draw the claw bigger than on the robot: scale the ring up by re-rastering a larger ring
    big = Canvas()
    ring = Ring(0.0, 0.0, 2.4, 5.4)
    pts = big.raster(Xf.pose(0.0, (0.0, 0.0), xf_c), ring)
    gap = 48.0
    kept = set()
    for (x, y) in pts:
        a = math.degrees(math.atan2(y + 0.5 - xf_c[1], x + 0.5 - xf_c[0]))
        d = (a + 135.0 + 540.0) % 360.0 - 180.0
        if abs(d) > gap * 0.5:
            kept.add((x, y))
    for (x, y) in kept:
        edge = any((x + ox, y + oy) not in kept for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x, y - 1) not in kept or (x - 1, y) not in kept
        cv.put(x, y, I[0] if edge and not lit else (I[4] if lit and (x + y) % 3 == 0 else (I[3] if lit else I[2])))
    for side in (-1, 1):
        a = math.radians(-135.0 + side * (gap * 0.5 + 8.0))
        q = (int(math.floor(xf_c[0] + math.cos(a) * 4.0)), int(math.floor(xf_c[1] + math.sin(a) * 4.0)))
        if q in kept:
            cv.put(q[0], q[1], S[2])
    del keep, cv2
    return to_image(cv.px, 0, 0, 16, 16)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, c = frame(dict(FRAMES)["Idle0"])
    out = {}
    out["PuxaFrango_GoreHead"] = crop({q: col for q, col in mid.px.items() if q[0] <= -9})
    cx, cy = int(c[0]), int(c[1])
    out["PuxaFrango_GoreClaw"] = crop({q: col for q, col in near.px.items() if abs(q[0] - cx) <= 5 and abs(q[1] - cy) <= 5})
    out["PuxaFrango_GoreLeg"] = crop({q: col for q, col in near.px.items() if q[1] >= -10 and q[0] > -8})
    return out


# ================================================================================================
def write_rig(path, cell):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/underground/make_puxafrango_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Underground.NPCs",
         "{",
         "\t/// <summary>The Puxa-frango's grid sheets (game px, left-facing): far, middle, near planes of equal cells with 2 px",
         "\t/// under each, origin = the ground point under the hip.</summary>",
         "\tpublic static class PuxaFrangoRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Idle = %d, Crouch = %d, Lunge = %d, Snap = %d, Air = %d;"
         % (WALK, INDEX["Idle0"], INDEX["Crouch"], INDEX["Lunge"], INDEX["Snap"], INDEX["Air"]),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d;" % round(STRIDE * 2 / (WALK / 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/PuxaFrango%s.png" % suffix)
    write_rig(OUT + "NPCs/PuxaFrangoRigData.cs", cell)
    export(snapper_icon(), OUT + "Items/ChickenSnapper.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 80, 56
    out = Image.new("RGBA", (cw * 7, ch * 2), (36, 40, 48, 255))
    for k, (n, p) in enumerate(FRAMES):
        far, mid, near, _ = frame(p)
        tile = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cv in (far, mid, near):
            tile.alpha_composite(to_image(cv.px, -cw // 2, -ch + 4, cw, ch))
        out.alpha_composite(tile, ((k % 7) * cw, (k // 7) * ch))
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
