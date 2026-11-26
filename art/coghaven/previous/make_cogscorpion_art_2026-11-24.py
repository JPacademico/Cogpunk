"""Source for the Cogscorpion (D4), 2026-11-12 (user: "add a new enemy to coghaven being the cogscorpion. it should have a
tail attack that apply jade curse"). Run from the repo root:

    python -P art/coghaven/make_cogscorpion_art.py [--preview FILE]

Design (my calls): a palace guardian of Coghaven built like a scorpion: a long low carapace of riveted bronze plates (gilt),
each plate edged in the palace's red lacquer (crimson), a polished jade head plate (ghost, the island's jade) with two
glowing jade eyes; two big bronze claws on jointed arms; eight thin steel legs with little bronze cogs for knees; a tail of
five bronze segments, each turning on a cog, ending in a bulb of polished jade with a steel sting, glowing as it charges.
Three-quarter side view facing left (D4 rule 13), chunky (D4 rule 18), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far legs and the far claw, flat and a step darker), middle (the
carapace, the head, the tail), near (the near legs and the near claw); the glow sheet holds the eyes and the stinger's
jade. Stable pixels (D4 rule 17): every part lit in its own space; the walk moves only legs and whole pixels; the tail
turns only in the attack's big deliberate moves.

Frames:
- Walk x8: a scorpion's alternating gait (near 1 and 3 with far 2 and 4, against the other four), each foot planted half
  the cycle and sliding back the root motion; the claws bob a pixel.
- Raise x4: the telegraph (36 ticks in the game): the tail coils back and up, the sting glowing brighter, the claws open.
- Strike x3: the tail whips over the head (a smear frame), the sting at full reach in front of the face, the recoil.
- Recover x2: back to the walk's tail.

Outputs:
    Content/Coghaven/NPCs/Cogscorpion.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/CogscorpionRigData.cs   cells, origin, frames, the walk's step, the sting (from the origin, facing left)
    Content/Coghaven/Gores/Cogscorpion_GoreTail.png, _GoreClaw.png, _GoreBody.png
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
from westbots import (RAMP, Xf, Ellipse, Capsule, Union, Poly, Canvas, flat, dome, ik, P, limb, finish, texture)  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
G, ST, K, JD, IV = RAMP["gilt"], RAMP["steel"], RAMP["crimson"], RAMP["ghost"], RAMP["ivory"]
FAR = (2, -1)                                    # the far side's legs and claw: back and up a pixel (whole px)

# --- the rig (art px, facing left, y down, the origin on the ground under the middle) -----------------------------------
BODY = (1.4, -8.0, 12.4, 5.0)                    # the carapace: centre, radii
HEAD = (-11.8, -7.6, 5.6, 4.4)
HIPS = [(-7.4, -5.4), (-2.6, -5.0), (2.4, -5.0), (7.2, -5.4)]
REST = [-14.0, -5.8, 4.6, 13.2]                  # a foot's x at rest
LEG = (4.6, 5.2)                                 # femur, tibia
SHOULDER = (-13.0, -6.4)
TAIL_BASE = (12.4, -9.6)
TAIL_LEN = (6.0, 6.0, 6.0, 5.6, 5.2)
TAIL_R = (2.9, 2.7, 2.5, 2.3, 2.1)
STING_LEN = 6.0
EYE = (-14.8, -10.4)


class Pose:
    def __init__(self, feet=None, tail=None, sting=0, claw=0.0, claws_up=0, bob=0, reach=0.0):
        self.feet = list(feet) if feet else [(0.0, 0.0)] * 8      # near 0-3, far 0-3: (x from rest, lift)
        self.tail = tail or REST_TAIL                             # absolute angles of the five segments and the sting
        self.sting = sting                                        # 0..3: the jade bulb's glow
        self.claw = claw                                          # degrees the pincers open
        self.claws_up = claws_up                                  # whole px the claws rise
        self.bob = bob                                            # whole px the body sits lower
        self.reach = reach                                        # px the near arm reaches forward


REST_TAIL = (-75.0, -105.0, -140.0, -175.0, -205.0, -225.0)
COIL_TAIL = (-58.0, -84.0, -114.0, -148.0, -182.0, -203.0)
STRIKE_TAIL = (-110.0, -160.0, -185.0, -200.0, -210.0, -220.0)


def tween(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# --- shading -------------------------------------------------------------------------------------------------------------
def plates(base, cx, step, seed):
    """Bronze plates in the part's own space: a dark seam every `step` px along x with a lit lip after it, rivets on the
    plates' middles (stable while it moves, D4 rule 17)."""
    def fn(i):
        k = base(i)
        u = (i.lx - cx) / step
        f = u - math.floor(u)
        if f < 0.12:
            k -= 2                                    # the seam
        elif f < 0.26:
            k += 1                                    # the lit lip behind it
        return max(1, min(9, k))
    return texture(fn, "brushed", seed=seed, density=0.06, lo=1, hi=8)


def carapace(mid, T, p):
    cx, cy, rx, ry = BODY
    shade = plates(dome(cx - 4.0, cy - 4.4, 13.0, lo=2, hi=8, gain=1.45, bias=0.05, fixed=True, dither=0.2), cx, 4.6, 71)
    inner = mid.part(T, Ellipse(cx, cy, rx, ry), "gilt", shade, rust=0.0)
    # the red lacquer band along the carapace's lower edge
    for q in list(inner):
        lx, ly = T.inv((q[0] + 0.5, q[1] + 0.5))
        if ly - cy > ry * 0.05 and ly - cy < ry * 0.40:
            mid.put(q[0], q[1], K[3] if (lx - cx) % 4.6 > 0.7 else K[1])
    return inner


def head(mid, T, p):
    cx, cy, rx, ry = HEAD
    inner = mid.part(T, Ellipse(cx, cy, rx, ry), "gilt", dome(cx - 2.0, cy - 2.6, 5.6, lo=2, hi=7, gain=1.4, fixed=True, dither=0.2),
                     shadow=(1, 1), rust=0.0)
    # the jade plate over the head's top, lit from the top-left
    plate = mid.part(T, Ellipse(cx - 0.4, cy - 1.4, rx - 1.6, ry - 1.6), "ghost",
                     dome(cx - 2.0, cy - 3.4, 4.6, lo=1, hi=4, gain=1.5, fixed=True, dither=0.2), rust=0.0, clip=inner)
    return inner | plate


def leg(cv, hip, rest_x, foot, depth):
    """A thin steel leg rising to a cog knee and down to a hooked tip on the ground."""
    femur, tibia = LEG
    ankle = (rest_x + foot[0], -1.0 - foot[1])
    knee, ankle = ik(hip, ankle, femur, tibia, -1 if rest_x < hip[0] else 1)
    if knee[1] > hip[1] - 1.0:                         # scorpion knees stand above the hip
        knee = (knee[0], hip[1] - 1.6)
    limb(cv, hip, knee, 1.45, "steel", depth, lo=3, hi=7)
    limb(cv, knee, ankle, 1.2, "steel", depth, lo=3, hi=6)
    if depth == 0:
        k = P(Xf(), knee)
        for (dx, dy, col) in ((0, 0, G[7]), (1, 0, G[5]), (0, 1, G[4]), (1, 1, G[3])):
            cv.put(k[0] + dx, k[1] + dy, col)        # the knee's little bronze cog
        tip = P(Xf(), ankle)
        cv.put(tip[0], tip[1], ST[1])


def claw(cv, glow, T, p, depth):
    """A jointed bronze arm and a big pincer: the hand and two fingers that open by p.claw."""
    off = FAR if depth else (0, 0)
    up = p.claws_up
    sh = (SHOULDER[0] + off[0], SHOULDER[1] + off[1])
    elbow = (-16.4 + off[0], -11.4 + off[1] - up)
    wrist = (-19.2 + off[0] - p.reach, -9.0 + off[1] - up)
    hand = (-22.0 + off[0] - p.reach, -8.8 + off[1] - up)
    A = T
    limb(cv, A.fwd(sh), A.fwd(elbow), 2.0, "gilt", depth, lo=3, hi=7)
    limb(cv, A.fwd(elbow), A.fwd(wrist), 1.8, "gilt", depth, lo=3, hi=7)
    ramp_lo = 2 if depth else 3
    inner = cv.part(A, Ellipse(hand[0], hand[1], 4.0, 3.2), "gilt",
                    flat(ramp_lo + 1, bevel=False) if depth else dome(hand[0] - 1.4, hand[1] - 1.6, 3.6, lo=3, hi=8, gain=1.5, fixed=True),
                    rust=0.0)
    for sign in (-1, 1):                               # the upper (fixed) and lower (moving) fingers
        ang = math.radians(180.0 + sign * (8.0 + p.claw * (0.5 if sign < 0 else 1.0)))
        base = (hand[0] - 2.6, hand[1] + sign * 1.4)
        tip = (base[0] + math.cos(ang) * 4.4, base[1] + math.sin(ang) * 4.4 * -1)
        cv.part(A, Capsule(base, tip, 1.5, 0.75), "gilt", flat(ramp_lo + (2 if sign < 0 else 1), bevel=False), rust=0.0)
    return inner


def tail(mid, glow, T, p):
    """Five bronze segments on cog joints, each with a lacquer band, then the jade bulb and the steel sting."""
    pts = [TAIL_BASE]
    for ln, ang in zip(TAIL_LEN, p.tail[:5]):
        a = math.radians(ang)
        x, y = pts[-1]
        pts.append((x + math.cos(a) * ln, y + math.sin(a) * ln))
    segs = []
    for k in range(5):
        a, b = pts[k], pts[k + 1]
        segs.append(limb(mid, T.fwd(a), T.fwd(b), TAIL_R[k], "gilt", 0, lo=3, hi=8))
    joints = []
    for k in range(1, 5):                                # the joints' cogs and the lacquer bands
        c = P(T, pts[k])
        joints.append(c)
        for (dx, dy, col) in ((-1, -1, G[8]), (0, -1, G[6]), (-1, 0, G[6]), (0, 0, G[4]), (1, 0, G[3]), (0, 1, G[2])):
            mid.put(c[0] + dx, c[1] + dy, col)
    # the bulb and the sting
    a5 = math.radians(p.tail[5])
    bx, by = pts[5]
    bulb = (bx + math.cos(a5) * 2.6, by + math.sin(a5) * 2.6)
    sting = (bx + math.cos(a5) * STING_LEN + math.cos(a5 + 1.2) * 1.4, by + math.sin(a5) * STING_LEN + math.sin(a5 + 1.2) * 1.4)
    inner = mid.part(T, Ellipse(bulb[0], bulb[1], 3.2, 3.0), "ghost",
                     dome(bulb[0] - 1.2, bulb[1] - 1.4, 3.0, lo=1 + min(1, p.sting), hi=4 + min(1, p.sting // 2), gain=1.5, fixed=True),
                     rust=0.0)
    limb(mid, T.fwd(bulb), T.fwd(sting), 1.2, "steel", 0, lo=4, hi=8)
    return pts, bulb, sting, inner


# --- a frame ---------------------------------------------------------------------------------------------------------------
def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    T = Xf.pose(0.0, (0.0, 0.0), (0.0, float(p.bob)))
    for k in range(4):                                   # the far legs and claw
        hx, hy = HIPS[k]
        leg(far, (hx + FAR[0], hy + FAR[1] + p.bob), REST[k] + FAR[0], p.feet[4 + k], 1)
    claw(far, glow, T, p, 1)
    body = carapace(mid, T, p)
    hd = head(mid, T, p)
    pts, bulb, sting, bulb_in = tail(mid, glow, T, p)
    vent = P(T, (5.0, -13.8))                            # a little steam vent on the back
    for (dx, dy, col) in ((0, 0, ST[6]), (1, 0, ST[4]), (0, 1, ST[4]), (1, 1, ST[2]), (0, -1, ST[2]), (1, -1, ST[1])):
        mid.put(vent[0] + dx, vent[1] + dy, col)
    for k in range(4):                                   # the near legs and claw
        hx, hy = HIPS[k]
        leg(near, (hx, hy + p.bob), REST[k], p.feet[k], 0)
    claw(near, glow, T, p, 0)
    for cv in (far, mid, near):
        finish(cv)
    stamps(mid, glow, T, p, body, bulb, bulb_in)
    return far, mid, near, glow, T.fwd(sting)


def stamps(mid, glow, T, p, body, bulb, bulb_in):
    """Under 3 px, after finish(): the rivets, the eyes, the bulb's glint and its glow."""
    cx, cy, rx, ry = BODY
    for x in (-6.0, -1.4, 3.2, 7.8):                    # a rivet on every plate
        q = P(T, (x, cy - 1.6))
        if q in body:
            mid.put(q[0], q[1], G[9])
            mid.put(q[0] + 1, q[1] + 1, G[2])
    e = P(T, EYE)
    for (dx, dy) in ((0, 0), (2, 0)):                    # two jade eyes on the head plate
        mid.put_glow(e[0] + dx, e[1] + dy, JD[5])
        glow.put_glow(e[0] + dx, e[1] + dy, JD[5])
        mid.put(e[0] + dx, e[1] + dy + 1, JD[1])
    b = P(T, bulb)
    g = (JD[3], JD[4], JD[5], JD[5])[min(3, p.sting)]
    for (dx, dy) in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
        q = (b[0] + dx, b[1] + dy)
        if q in bulb_in:
            if p.sting > 0:
                mid.put_glow(q[0], q[1], g)
                glow.put_glow(q[0], q[1], g)
            elif (dx, dy) == (-1, -1):
                mid.put(q[0], q[1], JD[5])               # the glint


# --- poses -------------------------------------------------------------------------------------------------------------------
WALK = 8
STRIDE = 6.0
LIFT = 1.6


def gait(k, n, stride, lift):
    t = (k % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def walk_pose(k):
    a, b = gait(k, WALK, STRIDE, LIFT), gait(k + WALK // 2, WALK, STRIDE, LIFT)
    feet = [a, b, a, b, b, a, b, a]                      # near 1, 3 with far 2, 4; then the others
    return Pose(feet=feet, claws_up=1 if k % 4 in (1, 2) else 0)


FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Raise%d" % k, Pose(tail=tween(REST_TAIL, COIL_TAIL, (k + 1) / 4.0), sting=min(3, k + 1), claw=6.0 * (k + 1),
                                  claws_up=1, bob=1 if k == 3 else 0)) for k in range(4)]
          + [("Strike0", Pose(tail=tween(COIL_TAIL, STRIKE_TAIL, 0.55), sting=3, claw=20.0, reach=1.0)),
             ("Strike1", Pose(tail=STRIKE_TAIL, sting=3, claw=14.0, reach=2.0, bob=1)),
             ("Strike2", Pose(tail=tween(STRIKE_TAIL, REST_TAIL, 0.3), sting=1, claw=8.0, reach=1.0))]
          + [("Recover0", Pose(tail=tween(STRIKE_TAIL, REST_TAIL, 0.65), claw=4.0)),
             ("Recover1", Pose(tail=tween(STRIKE_TAIL, REST_TAIL, 0.9)))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- outputs -----------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Walk0"])
    return {"Cogscorpion_GoreTail": crop({q: c for q, c in mid.px.items() if q[1] <= -12}),
            "Cogscorpion_GoreClaw": crop({q: c for q, c in near.px.items() if q[0] <= -14}),
            "Cogscorpion_GoreBody": crop({q: c for q, c in mid.px.items() if q[1] > -12 and q[0] > -9})}


def write_rig(path, cell, sting):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/coghaven/make_cogscorpion_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.NPCs",
         "{",
         "\t/// <summary>The Cogscorpion's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells",
         "\t/// with 2 px under each; the origin is the ground point under its middle. The sting (at full reach, Strike1) is from",
         "\t/// the origin, facing left.</summary>",
         "\tpublic static class CogscorpionRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Raise = %d, RaiseFrames = 4, Strike = %d, StrikeFrames = 3, Recover = %d, RecoverFrames = 2;"
         % (WALK, INDEX["Raise0"], INDEX["Strike0"], INDEX["Recover0"]),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d;" % round(STRIDE * 2 / (WALK / 2)),
         "\t\tpublic const int StingX = %d, StingY = %d;" % (round(sting[0] * 2), round(sting[1] * 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Cogscorpion%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Cogscorpion_Glow.png")
    write_rig(OUT + "NPCs/CogscorpionRigData.cs", cell, frames[INDEX["Strike1"]][4])
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=4):
    cw, ch = 72, 48
    cols = 6
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (34, 40, 46, 255)), (1, (150, 170, 190, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
                t.alpha_composite(to_image(cv.px, -cw // 2, -ch + 4, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rows))
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
