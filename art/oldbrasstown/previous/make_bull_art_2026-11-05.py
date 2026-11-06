"""Source for the Mechanical Bull, an enemy of Old Brass Town (D4), 2026-11-04. Run from the repo root:

    python -P art/oldbrasstown/make_bull_art.py [--preview FILE]

Design (user, 2026-11-04: "a mechanical bull that charges then rams the player, dealing massive contact damage and
knockback"): a steam-driven bull of riveted iron. A deep barrel of a body with a brass band round its middle and plate
seams, a boiler dome on its shoulders with a brass smokestack (steam in game), a heavy low head with a copper muzzle
plate, a brass ring through its nose, two ember eyes (hostile) and long brass horns sweeping forward, four piston legs
with brass knee bolts and iron hooves, and a chain for a tail. Three-quarter side view facing left (D4 rule 13), lit
from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far legs and the far horn, a ramp step darker), middle (the
body, the boiler, the head and the near horn), near (the near legs); the glow sheet holds the eyes. Stable pixels (D4
rule 17): the body moves by whole pixels and is lit in its own space; the head turns only for the big deliberate moves
(lowered for the charge); far limbs are one flat tone.

Frames: Trot x6 (diagonal pairs), Paw x2 (the telegraph: head down, horns levelled, the near fore hoof scraping), Charge
x4 (a gallop, head low), Skid (front legs braced, leaning back), Stunned x2 (head hanging, a shudder).

Outputs:
    Content/OldBrassTown/NPCs/MechanicalBull.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/OldBrassTown/NPCs/MechanicalBullRigData.cs   cells, origin, frames, the nostrils and the stack (from the origin,
                                                         facing left)
    Content/OldBrassTown/Gores/MechanicalBull_GoreHead.png, _GoreHorn.png, _GoreLeg.png
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
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, dome, face, ik, P, despeckle, limb, finish, texture, glint,  # noqa: E402
                      I, B, C, E, S, LE, ST, G, H, K)
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"
UPPER, LOWER = 4.6, 4.6
SHOULDER = (-9.0, -12.0)
HIP = (9.0, -12.4)
NECK = (-14.0, -19.0)
NOSTRIL = (-26.0, -14.6)
HEAD_SCALE = 1.22
STACK_TOP = (-3.6, -32.0)


class Pose:
    def __init__(self, bob=0, lean=0, head=0.0, feet=None, shudder=0):
        self.bob, self.lean = bob, lean           # whole px: body down, body back (+x)
        self.head = head                          # degrees the head turns down about the neck (+ = lowered)
        self.shudder = shudder                    # whole px the body shakes (0 / 1, never -1 / +1)
        # feet: (near fore, far fore, near hind, far hind): (x, lift) from each joint's rest point
        self.feet = feet or ((0.0, 0.0), (1.0, 0.0), (0.0, 0.0), (1.0, 0.0))


def hoof(cv, at, depth):
    x, y = at
    cv.part(Xf(), Poly([(x - 2.0, y - 1.2), (x + 1.8, y - 1.2), (x + 2.0, y + 1.6), (x - 2.4, y + 1.6)]), "steel",
            flat(3, bevel=False) if depth else face((-0.5, -0.5, 0.7), lo=2, hi=5, ramp_len=9, fixed=True), rust=0.0)
    if depth == 0:
        for dx, k in ((-1.2, 8), (-0.2, 6), (0.8, 5)):
            cv.put(int(math.floor(x + dx)), int(math.floor(y - 0.6)), G[k])      # the hoof's gilt band


def bull_leg(cv, joint, foot, depth, bend):
    """A piston leg from its joint to a hoof on the ground (`foot` = (x, lift)): a thick upper, a thinner lower."""
    ankle = (foot[0], -1.6 - foot[1])
    knee, ankle = ik(joint, ankle, UPPER, LOWER, bend)
    limb(cv, joint, knee, 2.5, "steel", depth, lo=3, hi=7)
    limb(cv, knee, ankle, 1.6, "steel", depth, lo=4, hi=8)                      # a chrome piston rod
    if depth == 0:
        q = P(Xf(), knee)
        cv.put(q[0], q[1], G[8])                                                 # the gilt knee bolt
        cv.put(q[0] + 1, q[1] + 1, G[4])
    hoof(cv, (ankle[0], ankle[1]), depth)


def barrel_shade():
    """The barrel's steel modelled over the long ramp (2026-11-05: the hard 3-band iron read flat), lit from the
    top-left in the body's own space (stable), the band edges dithered, a little cast-iron speckle."""
    return texture(dome(-7.0, -27.0, 15.5, lo=2, hi=7, gain=1.35, bias=0.2, fixed=True, dither=0.16), "speckle", seed=31, density=0.08)


def body(mid, glow, p):
    ox, oy = p.lean + p.shudder, p.bob
    T = Xf.pose(0.0, (0.0, 0.0), (float(ox), float(oy)))
    # the barrel: chest, belly, rump; plates lit from the top-left in its own space
    shape = Union(Ellipse(-7.5, -18.0, 7.6, 7.8), Ellipse(2.5, -16.4, 10.0, 5.6), Ellipse(11.0, -17.2, 6.0, 5.6))   # hump, barrel, haunch
    inner = mid.part(T, shape, "steel", barrel_shade(), shadow=(1, 1), rust=0.0)
    for x in range(-15, 15):                                       # the back's rolled ridge, bright
        top = min((y for (qx, y) in inner if qx == P(T, (x + 0.5, -17.0))[0]), default=None)
        if top is not None and x not in (1, 2, 3, -8, 10):
            mid.put(P(T, (x + 0.5, -17.0))[0], top, ST[8] if x < 4 else ST[6])
    # its brass band round the middle, riveted
    band = mid.raster(T, box(1.2, -25.0, 3.6, -10.0)) & inner
    for q in band:
        lx, ly = T.inv((q[0] + 0.5, q[1] + 0.5))
        mid.put(q[0], q[1], G[8] if ly < -21.0 else (G[7] if ly < -18.0 else (G[5] if ly < -14.5 else G[3])))
    for y in (-21.6, -17.4, -13.4):
        q = P(T, (2.2, y))
        if q in band:
            mid.put(q[0], q[1], G[9])
            mid.put(q[0] + 1, q[1] + 1, G[1])
    # plate seams, a lit lip behind each, rivets
    for x in (-8.0, 10.0):
        for k in range(10):
            ly = -22.0 + k * 1.0
            q = P(T, (x + 0.6 * math.sin(k * 0.35), ly))
            if q in inner and q not in band:
                mid.put(q[0], q[1], ST[2])
                if (q[0] + 1, q[1]) in inner:
                    mid.put(q[0] + 1, q[1], ST[7] if ly < -18.0 else ST[5])
    for (x, y) in ((-11.0, -22.4), (-5.6, -22.8), (7.4, -21.6), (13.0, -20.0), (-12.0, -14.0), (12.0, -14.6)):
        q = P(T, (x, y))
        if q in inner and (q[0] + 1, q[1] + 1) in inner:
            mid.put(q[0], q[1], ST[8])
            mid.put(q[0] + 1, q[1] + 1, ST[2])
    # the rodeo saddle on a crimson blanket (gilt trim), its stitching and its gilt horn
    blanket = mid.part(T, Poly([(-1.6, -24.4), (9.4, -23.4), (10.0, -18.4), (-1.2, -18.8)]), "crimson",
                       texture(face((-0.5, -0.6, 0.65), lo=3, hi=5, ramp_len=6, bias=0.15, fixed=True), "weave", seed=17), rust=0.0)
    for x in range(-1, 10):
        q = P(T, (x + 0.5, -19.2))
        if q in blanket:
            mid.put(q[0], q[1], G[7] if x % 2 == 0 else G[5])                 # the gilt fringe
    saddle = mid.part(T, Poly([(0.2, -26.0), (3.0, -25.0), (6.4, -25.2), (8.6, -26.6), (8.8, -22.6), (0.6, -22.4)]), "hide",
                      texture(face((-0.5, -0.6, 0.65), lo=2, hi=6, ramp_len=7, gain=1.3, bias=0.2, fixed=True), "speckle", seed=19), rust=0.0)
    for x in (1.6, 3.6, 5.6, 7.6):
        q = P(T, (x, -23.0))
        if q in saddle:
            mid.put(q[0], q[1], H[5])                                          # stitches
    for (dx, dy, k) in ((0, 0, 9), (1, 0, 7), (0, 1, 6), (1, 1, 4), (0, 2, 5)):
        q = P(T, (-0.4 + dx, -27.6 + dy))
        mid.put(q[0], q[1], G[k])                                              # the saddle horn
    # the boiler dome on the shoulders and its smokestack
    mid.part(T, Ellipse(-6.0, -25.4, 4.6, 2.6), "copper", dome(-7.6, -27.0, 5.0, lo=2, hi=4, gain=1.3, fixed=True, dither=0.15), rust=0.0)
    stack = mid.part(T, box(-5.0, -31.0, -2.4, -26.6), "gilt", face((-0.6, -0.2, 0.75), lo=3, hi=8, ramp_len=10, gain=1.3, fixed=True), rust=0.0)
    mid.part(T, box(-5.6, -32.4, -1.8, -30.6), "steel", face((-0.5, -0.6, 0.6), lo=3, hi=7, ramp_len=9, fixed=True), rust=0.0)
    q = P(T, (-4.4, -29.4))
    if q in stack:
        glint(mid, q[0], q[1], "gilt")
    # the tail: a short chain from the rump
    for k in range(5):
        q = P(T, (15.4 + k * 0.5, -19.0 + k * 1.4))
        mid.put(q[0], q[1], ST[6] if k % 2 == 0 else ST[2])
    for (dx, dy, k) in ((0, 0, 4), (1, 0, 5), (0, 1, 3), (1, 1, 4), (0, 2, 3)):
        q = P(T, (17.6 + dx, -11.6 + dy))
        mid.put(q[0], q[1], K[k])                                              # a crimson tassel on the chain
    return T


def head(mid, far, glow, T, p):
    """The head on the neck pivot, turned down by p.head; the near horn on the middle plane, the far one on the far."""
    H = T.then(Xf.pose(-p.head, NECK, (0.0, 1.0))).then(Xf(HEAD_SCALE, 0.0, 0.0, HEAD_SCALE, NECK[0] * (1 - HEAD_SCALE), NECK[1] * (1 - HEAD_SCALE)))
    # the far horn first (behind the head)
    for (cv, depth, dx, dy) in ((far, 1, 2.0, -0.6),):
        pts = [(-17.0 + dx, -22.2 + dy), (-19.4 + dx, -24.6 + dy), (-22.4 + dx, -25.4 + dy), (-24.4 + dx, -24.4 + dy)]
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            cv.part(H, Capsule(a, b, 1.6 - k * 0.3, 1.3 - k * 0.3), "gilt", flat(4, bevel=False), rust=0.0)
    shape = Poly([(-14.6, -22.6), (-18.4, -23.2), (-22.6, -21.6), (-26.4, -18.4), (-27.0, -14.6), (-24.6, -12.4), (-19.0, -12.6), (-14.0, -14.6)])
    hinner = mid.part(H, shape, "steel", texture(face((-0.55, -0.45, 0.7), lo=2, hi=7, ramp_len=9, gain=1.35, bias=0.15, fixed=True,
                                                       dither=0.15), "speckle", seed=33, density=0.08), shadow=(1, 1), rust=0.0)
    for (x0, y0, x1, y1) in ((-15.4, -21.6, -21.6, -21.0),):      # the brow's lit ridge
        for k in range(7):
            u = k / 6.0
            q = P(H, (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
            if q in hinner:
                mid.put(q[0], q[1], ST[8] if k < 4 else ST[7])
    muzzle = Poly([(-24.0, -18.6), (-26.8, -17.0), (-27.2, -14.4), (-24.8, -12.6), (-22.0, -13.4), (-22.4, -17.2)])
    minner = mid.part(H, muzzle, "copper", face((-0.6, -0.3, 0.75), lo=2, hi=4, fixed=True), rust=0.0)
    q = P(H, (-26.0, -15.8))
    if q in minner:
        mid.put(q[0], q[1], C[0])                                                # the nostril
    # the nose ring: brass, through the muzzle
    for (x, y) in ((-26.6, -13.0), (-27.2, -12.2), (-26.6, -11.4), (-25.6, -11.6)):
        q = P(H, (x, y))
        mid.put(q[0], q[1], G[8] if y < -12.0 else G[5])
    # the eye: ember, under a heavy iron brow
    e = P(H, (-20.6, -19.0))
    for (dx, dy, col) in ((0, 0, E[3]), (1, 0, E[2])):
        mid.put_glow(e[0] + dx, e[1] + dy, col)
        glow.put_glow(e[0] + dx, e[1] + dy, col)
    for dx in range(-1, 3):
        q = (e[0] + dx, e[1] - 1)
        if q in hinner:
            mid.put(q[0], q[1], ST[1])
    # cheek rivets
    for (x, y) in ((-17.2, -16.0), (-16.0, -20.4)):
        q = P(H, (x, y))
        if q in hinner and (q[0] + 1, q[1] + 1) in hinner:
            mid.put(q[0], q[1], ST[8])
            mid.put(q[0] + 1, q[1] + 1, ST[2])
    # the near horn: a long brass sweep forward and up, lit along its top
    pts = [(-16.6, -21.6), (-19.2, -24.4), (-22.6, -25.6), (-25.4, -24.6), (-26.6, -22.8)]
    horn = set()
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        horn |= mid.part(H, Capsule(a, b, 1.9 - k * 0.32, 1.6 - k * 0.32), "gilt", flat(6, bevel=False), rust=0.0)
    for q in horn:                                                # lit along its top, shaded under it, a glint at the bend
        if (q[0], q[1] - 1) not in horn:
            mid.put(q[0], q[1], G[8])
        elif (q[0], q[1] + 1) not in horn:
            mid.put(q[0], q[1], G[4])
    tip = P(H, (-22.6, -25.4))
    if tip in horn:
        mid.put(tip[0], tip[1], G[9])
    return H


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    nf, ff, nh, fh = p.feet
    ox, oy = p.lean + p.shudder, p.bob
    sx, sy = SHOULDER[0] + ox, SHOULDER[1] + oy
    hx, hy = HIP[0] + ox, HIP[1] + oy
    bull_leg(far, (sx + 2.0, sy - 0.6), (SHOULDER[0] + 2.0 + ff[0], ff[1]), 1, -1)
    bull_leg(far, (hx + 2.0, hy - 0.6), (HIP[0] + 2.0 + fh[0], fh[1]), 1, 1)
    T = body(mid, glow, p)
    H = head(mid, far, glow, T, p)
    bull_leg(near, (sx, sy), (SHOULDER[0] + nf[0], nf[1]), 0, -1)
    bull_leg(near, (hx, hy), (HIP[0] + nh[0], nh[1]), 0, 1)
    for cv in (far, mid, near):
        finish(cv)
    return far, mid, near, glow, H.fwd(NOSTRIL), T.fwd(STACK_TOP)


TROT = 6
STRIDE = 5.0


def gait(k, n, stride, lift):
    t = (k % n) / n
    if t < 0.5:
        return (stride / 2 - stride * (t / 0.5), 0.0)
    u = (t - 0.5) / 0.5
    return (-stride / 2 + stride * u, round(lift * math.sin(math.pi * u)))


def trot_pose(k):
    a, b = gait(k, TROT, STRIDE, 1.6), gait(k + TROT // 2, TROT, STRIDE, 1.6)
    return Pose(bob=1 if k % 3 == 1 else 0, feet=(a, (b[0] + 1.0, b[1]), b, (a[0] + 1.0, a[1])))


def charge_pose(k):
    # a gallop: the fores together, then the hinds, stretched long, the head low and level
    phases = (((-4.0, 1.0), (-3.0, 0.0), (4.0, 0.0), (5.0, 1.0)),
              ((-1.0, 2.0), (0.0, 2.0), (2.0, 0.0), (2.0, 0.0)),
              ((3.0, 0.0), (4.0, 0.0), (-3.0, 1.0), (-2.0, 2.0)),
              ((1.0, 0.0), (2.0, 1.0), (-1.0, 2.0), (0.0, 2.0)))
    return Pose(bob=1 if k in (1, 3) else 0, head=22.0, feet=phases[k])


FRAMES = ([("Trot%d" % k, trot_pose(k)) for k in range(TROT)]
          + [("Paw0", Pose(head=24.0, lean=1, feet=((2.6, 1.0), (1.0, 0.0), (0.0, 0.0), (1.0, 0.0)))),
             ("Paw1", Pose(head=24.0, lean=1, bob=1, feet=((-1.0, 0.0), (1.0, 0.0), (0.0, 0.0), (1.0, 0.0))))]
          + [("Charge%d" % k, charge_pose(k)) for k in range(4)]
          + [("Skid", Pose(head=8.0, lean=2, feet=((-4.0, 0.0), (-3.0, 0.0), (1.0, 0.0), (2.0, 0.0))))]
          + [("Stunned0", Pose(head=34.0, bob=1)), ("Stunned1", Pose(head=34.0, bob=1, shudder=1))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _, _ = frame(dict(FRAMES)["Trot0"])
    return {"MechanicalBull_GoreHead": crop({q: c for q, c in mid.px.items() if q[0] <= -15 and q[1] > -24}),
            "MechanicalBull_GoreHorn": crop({q: c for q, c in mid.px.items() if q[1] <= -24 and q[0] <= -16}),
            "MechanicalBull_GoreLeg": crop({q: c for q, c in near.px.items() if q[0] < 0})}


def write_rig(path, cell, nostril, stack):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/oldbrasstown/make_bull_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.OldBrassTown.NPCs",
         "{",
         "\t/// <summary>The Mechanical Bull's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal",
         "\t/// cells with 2 px under each; the origin is the ground point under its middle. The nostrils (in the paw frames) and",
         "\t/// the smokestack's mouth are from the origin, facing left.</summary>",
         "\tpublic static class MechanicalBullRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Trot = 0, TrotFrames = %d, Paw = %d, PawFrames = 2, Charge = %d, ChargeFrames = 4, Skid = %d, Stunned = %d, StunnedFrames = 2;"
         % (TROT, INDEX["Paw0"], INDEX["Charge0"], INDEX["Skid"], INDEX["Stunned0"]),
         "\t\t/// <summary>Game px a planted hoof slides back per trot frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int TrotStep = %d;" % round(STRIDE * 2 / (TROT / 2)),
         "\t\tpublic const int NostrilX = %d, NostrilY = %d, StackX = %d, StackY = %d;" % (round(nostril[0] * 2), round(nostril[1] * 2),
                                                                                          round(stack[0] * 2), round(stack[1] * 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/MechanicalBull%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/MechanicalBull_Glow.png")
    paw = frames[INDEX["Paw0"]]
    write_rig(OUT + "NPCs/MechanicalBullRigData.cs", cell, paw[4], frames[INDEX["Trot0"]][5])
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 70, 40
    cols = 5
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _, _, _ = frame(p)
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cv in (far, mid, near):
                t.alpha_composite(to_image(cv.px, -cw // 2 - 2, -ch + 3, cw, ch))
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
