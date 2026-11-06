"""ARCHIVED 2026-11-03: Friendobô's first pass (dark iron limbs, a leather waistcoat, a red bow tie, no apron), kept
in case the user wants this look back. The live generator is art/town/make_friendobo_art.py.

Source for Friendobô, Cogpunk's first town NPC (D4), 2026-11-03. Run from the repo root:

    python -P art/town/make_friendobo_art.py [--preview FILE]

Design (user, 2026-11-03: "an old robot with a monocle and a top hat, bartender-like"): an old iron robot with a round
head under a tall black top hat with a brass band, a brass-rimmed monocle over one lens and a small friendly lamp for
the other (friendly colours: Brass and Aether, D3), a brass handlebar moustache, a white shirt under a leather
waistcoat with brass buttons, a red bow tie and a bar towel over its forearm; thin piston limbs and old boots. It faces
left like every NPC sheet; vanilla draws it (one plane).

Vanilla's town NPC layout (decompiled NPC.VanillaFindFrame for town NPCs, with Main.npcFrameCount 25,
NPCID.Sets.ExtraFramesCount 9 and AttackFrameCount 4, AnimationType = the Guide): 0 standing, 1 in the air, 2-15
walking, 16-17 the two gestures of a chat or a game of rock-paper-scissors (num102 - 5 and - 4), 18 sitting, 19
talking, 20 blinking, 21-24 the throw (an arm back, the throw, the follow-through, back). 40x56 frames with no gap;
the feet stand on row 50 (vanilla draws NPC frames 4 px below the hitbox: decompiled Main.DrawNPCDirect).

Outputs (Content/Town/):
    Friendobo.png         40x1400  25 frames
    Friendobo_Head.png    the map and housing head (hat and face)
    Gores/Friendobo_GoreHead.png, _GoreArm.png, _GoreLeg.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, face, ik, level, lit  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Town/"
I, B, C, E, S, LE, A = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "leather", "aether"))
FW, FH = 20, 28                      # frame at 1x
FOOT_ROW = 25                        # the soles' bottom row (1x): 50-51 in game, the hitbox bottom
CX = 10.0                            # the body's centre column
THIGH, SHIN = 3.4, 3.4
UPPER, FORE = 3.2, 3.2


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


def limb_shade(a, b, r, lo, hi, gain=1.4, step=22.5):
    """A cylinder lit with its axis snapped to `step` degrees: stable shading while a limb sways (D4 rule 17)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln
    sa = round(math.atan2(dy, dx) / math.radians(step)) * math.radians(step)
    snx, sny = -math.sin(sa), math.cos(sa)

    def shade(i):
        t = max(-1.0, min(1.0, ((i.lx - a[0]) * nx + (i.ly - a[1]) * ny) / r))
        return level(lit(t * snx, t * sny, math.sqrt(1.0 - t * t)), lo, hi, gain)
    return shade


def limb(cv, a, b, r, ramp="iron", lo=2, hi=4, depth=0):
    cv.part(Xf(), Capsule(a, b, r), ramp, limb_shade(a, b, r, lo, hi), depth=depth, rust=0.0)


class Pose:
    def __init__(self, bob=0, near_foot=(-1.5, 0.0), far_foot=(1.5, 0.0), near_hand=(-3.6, 16.6), far_hand=(3.0, 16.0),
                 sit=False, mouth=False, blink=False, towel=True):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot     # (x offset, lift)
        self.near_hand, self.far_hand = near_hand, far_hand     # rig points (x from CX, y from the top)
        self.sit, self.mouth, self.blink, self.towel = sit, mouth, blink, towel


def leg(cv, hip, foot_x, lift, depth):
    ankle = (foot_x, FOOT_ROW - 1.6 - lift)
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)
    limb(cv, hip, knee, 1.5, depth=depth)
    limb(cv, knee, ankle, 1.4, depth=depth)
    ax, ay = ankle
    cv.part(Xf(), Poly([(ax + 1.4, ay - 0.4), (ax - 1.2, ay - 0.6), (ax - 2.6, ay + 0.8), (ax - 2.4, ay + 1.6), (ax + 1.6, ay + 1.6)]),
            "leather", flat(1), depth=depth, rust=0.0)          # an old boot


def arm(cv, shoulder, hand, depth, towel=False):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)
    limb(cv, shoulder, elbow, 1.3, depth=depth)
    limb(cv, elbow, wrist, 1.2, depth=depth)
    if towel:                                                   # the bar towel over the forearm
        mx, my = (elbow[0] + wrist[0]) / 2.0, (elbow[1] + wrist[1]) / 2.0
        cv.part(Xf(), Poly([(mx - 1.2, my - 1.0), (mx + 1.4, my - 1.0), (mx + 1.2, my + 2.6), (mx - 1.0, my + 2.2)]), "steam",
                face((-0.4, -0.5, 0.75), lo=0, hi=2, fixed=True), rust=0.0)
    cv.put(int(math.floor(wrist[0])), int(math.floor(wrist[1])), I[3 - depth])   # the hand


def body(cv, glow, p):
    oy = p.bob
    seat = 2 if p.sit else 0
    # torso: a white shirt under a leather waistcoat, brass buttons, a red bow tie
    shirt = cv.part(Xf(), box(CX - 3.4, 11.0 + oy + seat, CX + 3.2, 18.6 + oy + seat), "steam", face((-0.5, -0.3, 0.8), lo=0, hi=2, fixed=True), rust=0.0)
    vest = cv.part(Xf(), Union(box(CX - 0.6, 13.0 + oy + seat, CX + 3.4, 19.6 + oy + seat),
                               box(CX - 3.6, 15.6 + oy + seat, CX - 2.0, 19.6 + oy + seat)),
                   "leather", face((-0.5, -0.3, 0.8), lo=1, hi=2, bias=0.35, fixed=True), rust=0.0)
    for y in (14.6, 16.6, 18.4):                                # brass buttons down the waistcoat's edge
        cv.put(int(CX - 0.2), int(y + oy + seat), B[4])
    for (dx, dy, col) in ((-2, 0, E[2]), (-1, 0, E[1]), (0, 0, E[0]), (1, 0, E[1]), (2, 0, E[2]), (-2, 1, E[1]), (2, 1, E[1])):   # the bow tie
        cv.put(int(CX - 0.5) + dx, int(11.6 + oy + seat) + dy, col)
    for (dx, dy) in ((1, 4), (2, 5), (3, 5)):                   # a watch chain across the waistcoat
        cv.put(int(CX - 0.2) + dx, int(13.0 + oy + seat) + dy, B[4])
    # head: an old iron dome, the monocle, the lamp eye, the moustache
    hc = (CX - 0.4, 7.8 + oy + seat)
    head = cv.part(Xf(), Ellipse(hc[0], hc[1], 3.9, 3.5), "iron", dome(hc[0] - 1.4, hc[1] - 1.4, 4.4, lo=2, hi=4, gain=1.35, bias=0.3, fixed=True),
                   rust=0.0)
    mx, my = int(math.floor(hc[0] - 2.4)), int(math.floor(hc[1] - 0.6))
    for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        cv.put(mx + dx, my + dy, B[4] if dy < 0 or dx < 0 else B[2])   # the monocle's brass rim
    if p.blink:
        cv.put(mx, my, I[1])
    else:
        cv.put_glow(mx, my, S[3])
        glow.put_glow(mx, my, S[3])
    cv.put(mx + 1, my + 2, B[3])                                # its chain
    cv.put(mx + 2, my + 3, B[2])
    ex = int(math.floor(hc[0] + 0.6))
    if p.blink:
        cv.put(ex, my, I[1])
    else:
        cv.put_glow(ex, my, A[3])                               # the friendly lamp eye
        glow.put_glow(ex, my, A[3])
    mouth_y = int(math.floor(hc[1] + 1.8))
    for (dx, col) in ((-4, I[3]), (-3, S[1]), (-2, S[2]), (-1, S[1]), (0, S[2]), (1, I[3])):   # the silver handlebar moustache
        cv.put(int(hc[0]) + dx, mouth_y, col)
    cv.put(int(hc[0]) - 4, mouth_y - 1, I[3])
    cv.put(int(hc[0]) + 1, mouth_y - 1, I[3])
    if p.mouth:
        cv.put(int(hc[0]) - 2, mouth_y + 1, I[0])
        cv.put(int(hc[0]) - 1, mouth_y + 1, I[0])
    # the top hat: a brim, a tall crown, a brass band
    cv.part(Xf(), box(hc[0] - 4.6, hc[1] - 3.6, hc[0] + 4.0, hc[1] - 2.6), "iron", flat(1), rust=0.0)
    cv.part(Xf(), box(hc[0] - 3.0, hc[1] - 9.0, hc[0] + 2.6, hc[1] - 3.2), "iron", face((-0.5, -0.3, 0.8), lo=1, hi=2, fixed=True), rust=0.0)
    for x in range(int(math.floor(hc[0] - 2.0)), int(math.floor(hc[0] + 2.0))):
        cv.put(x, int(math.floor(hc[1] - 4.6)), B[4] if x < hc[0] else B[3])
    del shirt, vest, head
    return (CX - 2.4, 12.6 + oy + seat), (CX + 2.2, 12.8 + oy + seat), (CX - 1.0, 19.4 + oy + seat), (CX + 1.4, 19.4 + oy + seat)


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    sh_near, sh_far, hip_near, hip_far = body(mid, glow, p)
    if p.sit:                                                   # sitting: thighs forward, shins down
        for (cv, hip, d) in ((far, hip_far, 1), (near, hip_near, 0)):
            knee = (hip[0] - 3.2, hip[1] + 0.6)
            limb(cv, hip, knee, 1.5, depth=d)
            limb(cv, knee, (knee[0] - 0.2, FOOT_ROW - 1.6), 1.4, depth=d)
            cv.part(Xf(), box(knee[0] - 2.4, FOOT_ROW - 1.6, knee[0] + 1.2, FOOT_ROW), "leather", flat(1), depth=d, rust=0.0)
    else:
        leg(far, hip_far, CX + p.far_foot[0], p.far_foot[1], 1)
        leg(near, hip_near, CX + p.near_foot[0], p.near_foot[1], 0)
    arm(far, sh_far, (CX + p.far_hand[0], p.far_hand[1] + p.bob), 1, towel=p.towel)
    arm(near, sh_near, (CX + p.near_hand[0], p.near_hand[1] + p.bob), 0)
    cv = Canvas()
    for layer in (far, mid, near):
        cv.px.update(layer.px)
        cv.glow.update(layer.glow)
    despeckle(cv)
    return cv


def walk_pose(k):
    """14 walking frames: a full stride cycle, the arms swinging against the legs, a whole-pixel bob."""
    ph = 2.0 * math.pi * k / 14.0
    nf = (-1.0 + 2.6 * math.cos(ph), max(0.0, round(1.4 * math.sin(ph))))
    ff = (1.0 - 2.6 * math.cos(ph), max(0.0, round(1.4 * math.sin(ph + math.pi))))
    bob = 1 if abs(math.sin(ph)) > 0.7 else 0
    swing = round(1.6 * math.cos(ph))
    return Pose(bob=bob, near_foot=nf, far_foot=ff, near_hand=(-3.6 - swing, 16.6), far_hand=(3.0 + swing, 16.0))


FRAMES = ([Pose(), Pose(near_foot=(-2.0, 2.0), far_foot=(2.2, 1.0), near_hand=(-3.0, 13.5), far_hand=(4.0, 13.0))]
          + [walk_pose(k) for k in range(14)]
          + [Pose(near_hand=(-4.6, 11.0)), Pose(near_hand=(-4.0, 9.0)),            # 16-17: the gestures (a raised hand)
             Pose(sit=True), Pose(mouth=True), Pose(blink=True),                  # 18 sit, 19 talk, 20 blink
             Pose(near_hand=(3.0, 11.0)), Pose(near_hand=(1.0, 8.0)),             # 21-22: the arm back, up
             Pose(near_hand=(-5.0, 11.0)), Pose(near_hand=(-3.6, 15.0))])         # 23-24: the throw, the follow-through


def head_icon():
    """The head for the map and the housing menu: the hat and the face, cropped from the standing frame."""
    cv = frame(FRAMES[0])
    px = {q: c for q, c in cv.px.items() if q[1] <= 11}
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    return to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    cv = frame(FRAMES[0])
    return {"Friendobo_GoreHead": crop({q: c for q, c in cv.px.items() if q[1] <= 11}),
            "Friendobo_GoreArm": crop({q: c for q, c in cv.px.items() if 12 <= q[1] <= 18 and q[0] >= 12}),
            "Friendobo_GoreLeg": crop({q: c for q, c in cv.px.items() if q[1] >= 20})}


def sheet():
    out = Image.new("RGBA", (FW, FH * len(FRAMES)), (0, 0, 0, 0))
    for k, p in enumerate(FRAMES):
        out.alpha_composite(to_image(frame(p).px, 0, 0, FW, FH), (0, k * FH))
    return out


def export_all():
    export(sheet(), OUT + "Friendobo.png")
    export(head_icon(), OUT + "Friendobo_Head.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    sh = sheet()
    cols = 13
    out = Image.new("RGBA", (FW * cols, FH * 2 * 2), (36, 40, 48, 255))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (FW * cols, FH * 2), bg)
        for k in range(len(FRAMES)):
            tile.alpha_composite(sh.crop((0, k * FH, FW, (k + 1) * FH)), ((k % cols) * FW, (k // cols) * FH))
        out.paste(tile, (0, half * FH * 2))
    out.alpha_composite(head_icon(), (2, 2))
    out.resize((out.width * 5, out.height * 5), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
