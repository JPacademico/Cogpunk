"""Source for Missing Bones (D4), 2026-11-24: the raptor skeleton mount, its item and its buff. Run from the repo root:

    python -P art/research/make_missing_bones_art.py [--preview FILE] [--gif FILE]

User, 2026-11-24: "unlocks the crafting recipe for a new mount called "missing bones" a raptor skeleton that is fast and make
the player imune to tar poisoning (a way to reach the fundamental stone under the pool)". My design: a raptor rebuilt from
bones (the palette's ivory ramp, lit from the top-left) held together with the Junkyard's tar (black-brown gobs at every joint,
glossy on top), an ember glint in the eye socket. Side view facing right (vanilla's mount sheets face the way the player
does), the tail held out stiff behind, a long low skull with a row of teeth, a ribcage under the spine, small clawed arms
folded, legs bent like a bird's with the raised sickle claw. The rider sits on its hips.

The sheet (vanilla's mount layout, decompiled 1.4.4 Mount.Draw: frames stacked, the frame's middle at the hitbox's middle,
the frame's bottom row on the ground when its height is 42 + heightBoost): 10 frames of 50x36 art px (100x72 in game):
0 standing, 1-8 the run, 9 in the air. The body rises a pixel in frames 2, 3, 6 and 7 (the rider's bob in
MissingBonesMount.Bob matches it). Legs are posed by a two-bone solve (thigh and shin to the ankle) with the foot bones at a
fixed slant, the toe on a stride path that slides back on the ground and lifts on the way forward.

Outputs:
    Content/Research/Mounts/MissingBonesMount_Back.png   100x720  10 frames
    Content/Research/Mounts/MissingBones.png             the item: a raptor skull on a tarred cord
    Content/Research/Mounts/MissingBonesBuff.png         32x32, the buff icon
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, preview  # noqa: E402
from rig import RAMP  # noqa: E402

IV, TR, EB = RAMP["ivory"], RAMP["tar"], RAMP["ember"]
BONE = (IV[0], IV[1], IV[2], IV[3], IV[4], IV[5])          # 0 outline .. 5 highlight
TAR = (TR[0], TR[1], TR[2], TR[3], TR[4])                  # black-brown, glossy grey on top
GLOW = (EB[2], EB[3])
OUT = "Content/Research/Mounts/"
FW, FH, FRAMES = 50, 36, 10
GROUND = 35

FEMUR, TIBIA, META = 8.0, 9.0, 5.5
HIP = (24, 17)                                              # the pelvis (the rider sits over it)
SHOULDER = (33, 14)


def bone(p, a, b, r, far=False, knobs=True):
    """A bone from a to b: r px each side of its axis, lit on its upper-left side, knobs at both ends."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln
    if nx + ny > 0:
        nx, ny = -nx, -ny
    x0, x1 = int(min(ax, bx) - r - 2), int(max(ax, bx) + r + 3)
    y0, y1 = int(min(ay, by) - r - 2), int(max(ay, by) + r + 3)
    lit, mid, dark = (4, 3, 2) if not far else (3, 2, 1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - ax - 0.5) * dx + (py - ay - 0.5) * dy) / (ln * ln)))
            cx, cy = ax + 0.5 + dx * t, ay + 0.5 + dy * t
            rr = r + (0.45 if knobs and (t < 0.12 or t > 0.88) else 0.0)
            if math.hypot(px - cx, py - cy) <= rr:
                side = (px - cx) * nx + (py - cy) * ny
                p.put(x, y, BONE, lit if side > 0.35 else (dark if side < -0.35 else mid))


def tar(p, c, r):
    """A gob of tar at a joint: black-brown, a grey gloss on its top-left."""
    cx, cy = c
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                gloss = (x + 0.5 - cx) + (y + 0.5 - cy) < -r * 0.6
                p.put(x, y, TAR, 3 if gloss else (2 if d < r * 0.6 else 1))


def solve(hip, ankle, l1, l2, bend=1):
    """Two-bone solve: the knee of a thigh l1 and shin l2 from the hip to the ankle; bend +1 puts the knee forward (right)."""
    hx, hy = hip
    ax, ay = ankle
    dx, dy = ax - hx, ay - hy
    d = min(math.hypot(dx, dy), l1 + l2 - 0.01)
    d = max(d, abs(l1 - l2) + 0.01)
    a = math.atan2(dy, dx)
    cos_k = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    k = math.acos(max(-1.0, min(1.0, cos_k)))
    ang = a - bend * k
    return hx + math.cos(ang) * l1, hy + math.sin(ang) * l1


def leg(p, hip, toe, far=False):
    """A hind leg: the foot bones slant up and back from the toe to the ankle, the thigh and shin bend the knee forward."""
    tx, ty = toe
    ankle = (tx - 3.2, ty - 4.4)
    knee = solve(hip, ankle, FEMUR, TIBIA, bend=1)
    bone(p, hip, knee, 1.7, far)
    bone(p, knee, ankle, 1.2, far)
    bone(p, ankle, (tx, ty - 0.5), 0.9, far)
    # the toes: two forward, the sickle claw raised behind
    p.put(int(tx) + 1, int(ty), BONE, 3 if not far else 2)
    p.put(int(tx) + 2, int(ty), BONE, 2 if not far else 1)
    p.put(int(ankle[0]) + 1, int(ankle[1]) + 2, BONE, 4 if not far else 3)
    p.put(int(ankle[0]) + 2, int(ankle[1]) + 1, BONE, 3 if not far else 2)
    tar(p, knee, 1.2)
    tar(p, ankle, 0.9)


SKULL = (                                                   # 13 x 7, facing right: the long skull, a dark socket, the teeth
    "...aaSSLL....",
    "..aSSSLLLSa..",
    ".aSSs..SSSSSa",
    "aSSs.ESSSSsSa",
    "aSsaaasSsaasa",
    ".asTsTsTsTsa.",
    "..aaaaaaaaa..",
)
SKULL_KEY = {"a": (BONE, 1), "s": (BONE, 2), "S": (BONE, 3), "L": (BONE, 4), "T": (BONE, 5), "E": (GLOW, 1)}


class Pose:
    def __init__(self, bob=0, near_toe=(26, GROUND), far_toe=(21, GROUND), head=0, tail=0, arm=0):
        self.bob, self.near_toe, self.far_toe, self.head, self.tail, self.arm = bob, near_toe, far_toe, head, tail, arm


def stride(phase):
    """The toe's point over a stride (phase 0..1): on the ground sliding back for the first half, lifted forward after."""
    reach = 7.0                                              # px either side of the leg's middle
    mid = 24.0
    if phase < 0.5:
        u = phase / 0.5
        return mid + reach - 2 * reach * u, GROUND
    u = (phase - 0.5) / 0.5
    ease = 0.5 - 0.5 * math.cos(math.pi * u)
    return mid - reach + 2 * reach * ease, GROUND - 4.0 * math.sin(math.pi * u)


def run_pose(k):
    ph = k / 8.0
    near = stride(ph)
    far = stride((ph + 0.5) % 1.0)
    bob = -1 if k in (1, 2, 5, 6) else 0                     # frames 2, 3, 6, 7 of the sheet: the body up a pixel
    return Pose(bob=bob, near_toe=near, far_toe=far, head=(1 if k in (3, 7) else 0), tail=(-1 if k in (1, 2, 5, 6) else 0),
                arm=(k // 2) % 2)


FRAME_POSES = ([Pose(near_toe=(28, GROUND), far_toe=(20, GROUND))]
               + [run_pose(k) for k in range(8)]
               + [Pose(bob=-1, near_toe=(30, GROUND - 6), far_toe=(26, GROUND - 7), head=-1, tail=-2, arm=1)])


def frame(pose):
    img = Pix(FW, FH)
    b = pose.bob
    hip = (HIP[0], HIP[1] + b)
    sh = (SHOULDER[0], SHOULDER[1] + b)
    far = Pix(FW, FH)
    leg(far, hip, pose.far_toe, far=True)
    far.outline()
    img.m.update(far.m)
    body = Pix(FW, FH)
    # the tail: a stiff row of vertebrae out behind, tapering, a little up
    tail_end = (2, hip[1] - 4 + pose.tail)
    for k in range(9):
        t0, t1 = k / 9.0, (k + 0.8) / 9.0
        a = (hip[0] - 2 + (tail_end[0] - hip[0] + 2) * t0, hip[1] - 1 + (tail_end[1] - hip[1] + 1) * t0)
        c = (hip[0] - 2 + (tail_end[0] - hip[0] + 2) * t1, hip[1] - 1 + (tail_end[1] - hip[1] + 1) * t1)
        bone(body, a, c, max(0.7, 1.6 - 0.1 * k), knobs=False)
    # the spine and the ribcage under it
    bone(body, hip, sh, 1.5)
    for k, x in enumerate((26, 28, 30, 32)):
        top = hip[1] + (sh[1] - hip[1]) * (x - hip[0]) / (sh[0] - hip[0])
        depth = 5 + (2 if k in (1, 2) else 1)
        bone(body, (x, top + 1), (x - 1.2, top + depth), 0.7, knobs=False)
    bone(body, (26, hip[1] + 6), (32, sh[1] + 6), 0.6, knobs=False)      # the sternum closing the ribs
    # the pelvis: a broad hip bone the rider sits on
    bone(body, (hip[0] - 3, hip[1] - 1), (hip[0] + 3, hip[1] + 1), 1.9)
    # the neck: an S of vertebrae up to the skull
    neck = [(sh[0], sh[1]), (sh[0] + 2, sh[1] - 3), (sh[0] + 3, sh[1] - 6), (sh[0] + 5, sh[1] - 8 + pose.head)]
    for a, c in zip(neck, neck[1:]):
        bone(body, a, c, 1.2, knobs=False)
    # the arm, folded under the chest: upper arm and forearm with claws
    elbow = (sh[0] + 1, sh[1] + 5 + pose.arm)
    hand = (sh[0] + 4, sh[1] + 6 + pose.arm)
    bone(body, (sh[0] + 1, sh[1] + 1), elbow, 0.7)
    bone(body, elbow, hand, 0.6)
    body.put(int(hand[0]) + 1, int(hand[1]) + 1, BONE, 3)
    body.outline()
    img.m.update(body.m)
    near = Pix(FW, FH)
    leg(near, hip, pose.near_toe)
    near.outline()
    img.m.update(near.m)
    # the skull at the neck's top
    skull = Pix(FW, FH)
    sx, sy = neck[-1][0] - 2, neck[-1][1] - 4
    skull.rows(sx, sy, SKULL, SKULL_KEY)
    skull.outline()
    img.m.update(skull.m)
    img.put(sx + 5, sy + 3, GLOW, 1, lock=True)                 # the ember in the socket
    img.put(sx + 4, sy + 3, GLOW, 0, lock=True)
    # tar at the hip and the shoulder (over the bones)
    gob = Pix(FW, FH)
    tar(gob, hip, 1.6)
    tar(gob, sh, 1.3)
    tar(gob, (sh[0] + 3, sh[1] - 6 + pose.head), 0.8)
    gob.outline()
    img.m.update(gob.m)
    return img


def sheet():
    out = Image.new("RGBA", (FW, FH * FRAMES), (0, 0, 0, 0))
    for k, pose in enumerate(FRAME_POSES):
        out.alpha_composite(frame(pose).image(), (0, k * FH))
    return out


def item():
    """The item: the skull on a tarred cord, a vertebra bead."""
    p = Pix(17, 13)
    p.rows(3, 2, SKULL, SKULL_KEY)
    p.outline()
    for (x, y) in ((1, 0), (2, 1), (2, 2), (1, 3)):
        p.put(x, y, TAR, 2)
    p.put(0, 4, BONE, 3)
    p.put(1, 4, BONE, 2)
    p.put(8, 5, GLOW, 1, lock=True)
    p.put(7, 5, GLOW, 0, lock=True)
    return p.image()


def buff_icon():
    p = Pix(16, 16)
    p.rows(1, 5, SKULL, SKULL_KEY)
    p.outline()
    p.put(6, 8, GLOW, 1, lock=True)
    p.put(5, 8, GLOW, 0, lock=True)
    tar(p, (12, 13), 2.0)
    return p.image()


def export_all():
    export(sheet(), OUT + "MissingBonesMount_Back.png")
    export(item(), OUT + "MissingBones.png")
    export(buff_icon(), OUT + "MissingBonesBuff.png")


def frames_preview(path, scale=6):
    sh = sheet()
    cols = 5
    out = Image.new("RGBA", (FW * cols, FH * 2 * 2), (0, 0, 0, 255))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        band = Image.new("RGBA", (FW * cols, FH * 2), bg)
        for k in range(FRAMES):
            band.alpha_composite(sh.crop((0, k * FH, FW, (k + 1) * FH)), ((k % cols) * FW, (k // cols) * FH))
        out.paste(band, (0, half * FH * 2))
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        frames_preview(a.preview)
    else:
        export_all()
