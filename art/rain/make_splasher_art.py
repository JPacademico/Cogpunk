"""Source for the Splasher, a Cogpunk enemy of the rain (D4), 2026-11-03. Run from the repo root:

    python -P art/rain/make_splasher_art.py [--preview FILE]

Design (user, 2026-11-03: "spawns in the rain, a robot with an umbrella on the head that shoots a water gun, mid
range"): a squat iron walker with a copper diving-helmet head (redrawn 2026-11-04, user: "a detailed face, it looked just
like a blank square": a riveted porthole with two ember eyes glowing behind its glass, a side port, a brass collar, an air
hose; the 2026-11-03 bucket head is in art/rain/previous/) and a pressure gauge on its chest, an umbrella bolted to the top of its head
(red canopy panels on iron ribs, a brass ferrule), a riveted water tank with a sight glass on its back and a hose from it
to a pump-action water gun of brass held in its near hand. Three-quarter view facing left (D4 rule 13), lit from the
top-left.

Three planes (DepthLayers.DrawWalker grid sheets): far (the far leg and the far arm, a ramp step darker), middle (torso,
tank, head, umbrella), near (the near leg and the near arm with the gun); the glow sheet holds the lens. Stable pixels
(D4 rule 17): the body moves by whole pixels in the walk and idle loops and is lit in its own space; limbs are lit in
45-degree steps.

Frames: Walk x6, Idle x2 (the umbrella bobbing), Aim x2 (the shot's telegraph: the gun raised and pumped, the pump
handle sliding), Shoot x2 (the recoil, then settling).

Outputs:
    Content/Rain/NPCs/Splasher.png, Splasher_Far.png, Splasher_Near.png, Splasher_Glow.png   grid sheets
    Content/Rain/NPCs/SplasherRigData.cs                                                     cells, origin, frames, muzzle
    Content/Rain/Projectiles/SplasherWater.png    16 headings (stride 22, 0 = flying right, clockwise): a glob of water
    Content/Rain/Gores/Splasher_GoreHead.png, Splasher_GoreUmbrella.png, Splasher_GoreGun.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from rig import (RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Ring, Union, box, Canvas, flat, dome, cyl, face, rivet, line, ik,  # noqa: E402
                 texture, selout, soften_orphans, glint)
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Rain/"
I, B, C, E, S = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam"))
ST, G, K = (RAMP[k] for k in ("steel", "gilt", "crimson"))   # the long ramps (2026-11-05 redraw)
THIGH, SHIN = 4.2, 4.2
UPPER, FORE = 4.0, 4.0
HIP_Y = -8.0


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


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


class Pose:
    def __init__(self, bob=0, near_foot=(-1.5, 0.0), far_foot=(2.0, 0.0), gun=(-7.0, -12.0), gun_angle=0.0, pump=0.0,
                 umbrella=0, recoil=0):
        self.bob = bob                  # whole px, + = down
        self.near_foot, self.far_foot = near_foot, far_foot   # (x, lift)
        self.gun = gun                  # the near hand (the gun's grip), rig space
        self.gun_angle = gun_angle      # degrees, - = raised (the art faces left: anticlockwise lifts the muzzle)
        self.pump = pump                # 0 .. 1, the pump handle slid back
        self.umbrella = umbrella        # whole px the canopy bobs (+ = down)
        self.recoil = recoil            # whole px the gun is thrown back


def limb(cv, a, b, r, ramp, depth):
    """A thick capsule limb over a long ramp (far plane: one flat tone, D4 rule 17)."""
    n = len(RAMP[ramp])
    if depth > 0:
        cv.part(Xf(), Capsule(a, b, r), ramp, flat(max(2, n // 2 - 1), bevel=False), rust=0.0)
        return
    cv.part(Xf(), Capsule(a, b, r), ramp, cyl(a, b, r, lo=max(2, n // 3), hi=n - 1, snap=45), rust=0.0)


def leg(cv, hip, foot, lift, depth):
    ankle = (foot, -1.6 - lift)
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)                 # the knee forward (left)
    limb(cv, hip, knee, 2.1, "steel", depth)
    limb(cv, knee, ankle, 1.8, "gilt", depth)                     # a brass piston shin
    ax, ay = ankle
    cv.part(Xf(), Poly([(ax + 2.0, ay - 1.0), (ax - 1.8, ay - 1.4), (ax - 3.6, ay + 0.6), (ax - 3.4, ay + 1.9), (ax + 2.2, ay + 1.9)]),
            "steel", flat(3, bevel=False) if depth else face((-0.5, -0.5, 0.7), lo=2, hi=6, ramp_len=9, fixed=True), rust=0.0)   # the foot
    if depth == 0:
        cv.put(int(math.floor(knee[0])), int(math.floor(knee[1])), G[8])   # the knee bolt


def water_gun(cv, grip, angle, pump, recoil, depth):
    """A pump-action water gun pointing left from the grip: a brass body, an iron barrel and flared nozzle, a copper
    reservoir on top, a brass pump handle under the barrel that slides back by `pump`. Returns the muzzle point."""
    xf = Xf.pose(angle, (0.0, 0.0), (grip[0] + recoil, grip[1]))
    cv.part(xf, box(-1.4, -0.6, 1.2, 3.6), "steel", face((-0.5, -0.3, 0.8), lo=2, hi=5, ramp_len=9, snap=45), rust=0.0)   # the grip
    cv.part(xf, Poly([(-6.4, -2.8), (2.6, -2.8), (3.0, -0.6), (1.8, 1.0), (-6.4, 1.0)]), "gilt",
            face((0.0, -0.6, 0.8), lo=3, hi=8, ramp_len=10, gain=1.3, snap=45), rust=0.0)                  # the body
    cv.part(xf, Ellipse(-2.0, -4.0, 2.8, 1.9), "copper", dome(-3.0, -4.8, 3.2, lo=2, hi=4, snap=45), rust=0.0)    # the reservoir
    cv.part(xf, box(-11.0, -2.2, -6.0, 0.2), "steel", cyl((-11.0, -1.0), (-6.0, -1.0), 1.2, lo=3, hi=8, snap=45), rust=0.0)
    cv.part(xf, Poly([(-13.4, -3.0), (-11.0, -2.4), (-11.0, 0.4), (-13.4, 1.0)]), "steel", flat(6), rust=0.0)   # the nozzle
    px = -9.0 + 2.2 * pump
    cv.part(xf, box(px, 0.4, px + 3.2, 2.4), "gilt", flat(6), rust=0.0)                                # the pump handle
    q = P(xf, (-3.2, -4.8))
    cv.put(q[0], q[1], S[3])                                                                            # glint on the reservoir
    return xf.fwd((-13.4, -1.0))


def umbrella(cv, top, bob, depth=0):
    """An umbrella bolted to the head: a brass shaft, a shallow canopy of six red panels (alternating Ember shades on a
    dome lit from the top-left; seams drawn as lines read as glyphs at this size), iron rib tips poking out of its rim,
    a brass ferrule on top."""
    tx, ty = top[0], top[1] + bob
    cv.part(Xf(), box(tx - 0.6, ty - 4.0, tx + 0.8, ty + 0.5), "gilt", flat(6), rust=0.0)
    cy = ty - 4.0
    rx, ry = 11.0, 5.2
    canopy = Ellipse(tx, cy + 0.6, rx, ry) - box(tx - rx - 1.0, cy + 0.6, tx + rx + 1.0, cy + ry + 2.0)
    scallops = Union(*[Ellipse(tx - rx + 1.8 + k * (2 * rx - 3.6) / 5.0, cy + 0.6, 1.9, 1.3) for k in range(6)])
    shape = canopy | scallops
    mask = cv.raster(Xf(), shape)
    edge = {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    ribs = [tx - rx + k * (2 * rx) / 6.0 for k in range(7)]
    for (x, y) in mask:
        if (x, y) in edge:
            cv.put(x, y, K[0])
            continue
        nx, ny = (x + 0.5 - tx) / rx, (y + 0.5 - (cy + 0.6)) / ry
        light = nx * 0.8 + ny * 1.1                          # a dome lit from the top-left (in its own space: it never turns)
        k = 5 if light < -0.85 else (4 if light < -0.3 else (3 if light < 0.35 else 2))
        rx_at = tx + (x + 0.5 - tx) * ry / max(0.6, ry - (y + 0.5 - (cy - ry)))
        panel = sum(1 for b in ribs if b < rx_at)
        if panel % 2 == 0:
            k = max(1, k - 1)                                # alternate panels a shade darker
        cv.put(x, y, K[k])
    for bx in ribs:
        cv.put(int(math.floor(bx)), int(math.floor(cy + 1.6)), ST[7])         # the rib tips
    cv.part(Xf(), Ellipse(tx, cy - ry + 0.4, 1.2, 1.1), "gilt", flat(8), rust=0.0)   # the ferrule


def body(mid, glow, pose):
    """Torso, tank, head and umbrella. Returns the near and far shoulders."""
    oy = pose.bob
    # the water tank on its back: a riveted iron drum, brass bands, a sight glass of water
    tank = mid.part(Xf(), box(2.4, -17.0 + oy, 7.6, -8.6 + oy), "steel", cyl((5.0, -17.0 + oy), (5.0, -8.6 + oy), 2.6, lo=2, hi=7, fixed=True),
                    rust=0.0)
    for y in (-15.0, -10.6):
        mid.part(Xf(), box(2.0, y + oy, 8.0, y + 1.0 + oy), "gilt", flat(6), rust=0.0)
    for y in range(int(-13 + oy), int(-11 + oy)):
        mid.put(6, y, S[1] if y % 2 else S[2])                        # the sight glass: water in it
    # the torso: a rounded box of iron, lit on its top and front, a brass belly plate with rivets, a pressure gauge
    torso = mid.part(Xf(), Union(box(-5.4, -17.4 + oy, 3.8, -8.0 + oy), Ellipse(-0.8, -17.4 + oy, 4.6, 1.6)), "steel",
                     face((-0.45, -0.5, 0.74), lo=3, hi=7, ramp_len=9, gain=1.25, bias=0.2, fixed=True), shadow=(1, 1), rust=0.0)
    plate = mid.part(Xf(), box(-4.4, -13.0 + oy, 1.6, -9.2 + oy), "gilt", face((-0.4, -0.6, 0.7), lo=4, hi=8, ramp_len=10, fixed=True), rust=0.0)
    for x in (-3.2, 0.4):
        rivet(mid, Xf(), (x, -12.2 + oy), "brass", plate)
    for y in (-15.8, -14.2):                                           # rivets down the chest's front seam
        rivet(mid, Xf(), (-4.0, y + oy), "iron", torso)
    gauge = mid.part(Xf(), Ellipse(-1.6, -15.2 + oy, 1.8, 1.7), "gilt", flat(6), rust=0.0)   # the pressure gauge: a brass bezel...
    g = P(Xf(), (-1.6, -15.2 + oy))
    for (dx, dy, col) in ((0, 0, S[2]), (-1, 0, S[2]), (0, -1, S[3]), (-1, -1, S[3])):
        mid.put(g[0] + dx, g[1] + dy, col)                             # ...a white dial...
    mid.put(g[0] - 1, g[1], I[0])                                       # ...and its needle in the red
    mid.put(g[0], g[1] - 1, E[1])
    del gauge
    for y in range(int(-16 + oy), int(-8 + oy)):                       # the hose from the tank round the back
        if (3, y) in torso:
            mid.put(3, y, C[1] if y % 2 else C[2])
    # the head: a copper diving helmet (user, 2026-11-04: "a detailed face, it looked just like a blank square"): a big
    # riveted porthole in front with two ember eyes glowing behind its glass and a wet glint, a small side port, a brass
    # collar bolted to the shoulders, the air hose from the tank to the back of the helmet, the umbrella bolted on top
    hc = (-1.2, -20.4 + oy)
    collar = mid.part(Xf(), Union(box(hc[0] - 3.6, hc[1] + 1.8, hc[0] + 3.6, hc[1] + 3.8), Ellipse(hc[0], hc[1] + 2.8, 4.0, 1.0)), "gilt",
                      face((-0.4, -0.6, 0.7), lo=3, hi=7, ramp_len=10, fixed=True), rust=0.0)
    for x in (-2.6, 0.0, 2.4):
        rivet(mid, Xf(), (hc[0] + x, hc[1] + 2.4), "brass", collar)
    head = mid.part(Xf(), Ellipse(hc[0], hc[1] - 0.8, 4.8, 4.4), "copper", dome(hc[0] - 1.8, hc[1] - 2.6, 5.2, lo=1, hi=4, gain=1.35, bias=0.35, fixed=True),
                    shadow=(1, 1), rust=0.0)
    port_c = (hc[0] - 1.2, hc[1] - 0.4)                                # the front porthole, on the helmet's face
    pc = P(Xf(), port_c)
    ring = [(-2, -1), (-2, 0), (-2, 1), (-1, -2), (0, -2), (1, -2), (2, -1), (2, 0), (2, 1), (-1, 2), (0, 2), (1, 2)]
    for (dx, dy) in ring:
        mid.put(pc[0] + dx, pc[1] + dy, G[8] if (dy < 0 or dx < 0) else G[4])     # its brass rim, lit top-left
    for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        mid.put(pc[0] + dx, pc[1] + dy, ST[3] if dy < 0 else ST[1])      # the dark glass
    for (dx, dy, col) in ((-1, 0, E[3]), (1, 0, E[3]), (-1, 1, E[1]), (1, 1, E[1])):
        mid.put_glow(pc[0] + dx, pc[1] + dy, col)                        # two ember eyes behind it
        glow.put_glow(pc[0] + dx, pc[1] + dy, col)
    mid.put(pc[0] - 1, pc[1] - 1, S[2])                                  # a wet glint on the glass
    for (dx, dy) in ((-3, 0), (0, -3), (3, 0), (0, 3)):
        q = (pc[0] + dx, pc[1] + dy)
        if q in head:
            mid.put(q[0], q[1], G[9] if dy <= 0 else G[5])               # the porthole's four bolts
    sp = P(Xf(), (hc[0] + 2.4, hc[1] - 1.4))                             # the side port
    for (dx, dy, col) in ((0, 0, I[1]), (1, 0, I[1]), (0, -1, B[4]), (1, -1, B[3]), (-1, 0, B[3]), (2, 0, B[2]), (0, 1, B[2]), (1, 1, B[2])):
        q = (sp[0] + dx, sp[1] + dy)
        if q in head:
            mid.put(q[0], q[1], col)
    for k in range(4):                                                   # the air hose to the back of the helmet
        q = P(Xf(), (hc[0] + 4.0 + k * 0.4, hc[1] + 0.4 + k * 1.2))
        mid.put(q[0], q[1], C[2] if k % 2 else C[1])
    umbrella(mid, (hc[0] + 0.4, hc[1] - 3.6), pose.umbrella)
    del tank, torso
    return (-3.4, -15.6 + oy), (1.2, -15.8 + oy)


def frame(pose):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    sh_near, sh_far = body(mid, glow, pose)
    hip_y = HIP_Y + pose.bob
    leg(far, (1.4, hip_y), pose.far_foot[0], pose.far_foot[1], 1)
    leg(near, (-1.8, hip_y + 0.4), pose.near_foot[0], pose.near_foot[1], 0)
    # the far arm reaches the pump; the near arm holds the grip
    gx, gy = pose.gun[0] + pose.recoil, pose.gun[1] + pose.bob
    pump_hand = (gx - 6.0 + 2.2 * pose.pump, gy + 1.8)
    elbow, wrist = ik(sh_far, pump_hand, UPPER, FORE, 1)
    limb(far, sh_far, elbow, 1.9, "steel", 1)
    limb(far, elbow, wrist, 1.7, "steel", 1)
    muzzle = water_gun(near, (gx, gy), pose.gun_angle, pose.pump, 0, 0)
    elbow, wrist = ik(sh_near, (gx + 0.4, gy + 1.0), UPPER, FORE, 1)
    limb(near, sh_near, elbow, 2.0, "steel", 0)
    limb(near, elbow, wrist, 1.8, "steel", 0)
    for cv in (far, mid, near):
        soften_orphans(cv, 14.0)
        selout(cv)
    return far, mid, near, glow, muzzle


WALK = 6
STRIDE = 5.0


def walk_pose(f):
    def foot(phase):
        t = (phase % WALK) / WALK
        if t < 0.5:
            return (-STRIDE / 2 + STRIDE * (t / 0.5), 0.0)
        u = (t - 0.5) / 0.5
        return (STRIDE / 2 - STRIDE * u, round(2.0 * math.sin(math.pi * u)))
    nf, ff = foot(f), foot(f + WALK // 2)
    bob = 1 if f % 3 == 1 else 0
    return Pose(bob=bob, near_foot=(nf[0] - 1.5, nf[1]), far_foot=(ff[0] + 2.0, ff[1]))   # the umbrella rides the body (an extra bob jumped 2 px)


FRAMES = [("Walk%d" % k, walk_pose(k)) for k in range(WALK)] + [
    ("Idle0", Pose()),
    ("Idle1", Pose(umbrella=1)),
    ("Aim0", Pose(gun=(-7.0, -13.0), gun_angle=-6.0, pump=1.0)),
    ("Aim1", Pose(gun=(-7.0, -13.0), gun_angle=-6.0, pump=0.0, bob=1)),
    ("Shoot0", Pose(gun=(-7.0, -13.0), gun_angle=-12.0, recoil=2, umbrella=-1)),
    ("Shoot1", Pose(gun=(-7.0, -13.0), gun_angle=-6.0, recoil=1)),
]
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
# The water it shoots (hostile: steam-white spray; vanilla's water dust gives it its blue in game)
# ================================================================================================
def water_glob(heading_deg, cell=10):
    """A glob of water flying along heading_deg (0 = right, clockwise): a round head, a tapering tail breaking into two
    drops; built pointing right and placed by a transform (never rotated as a bitmap), lit in screen space."""
    cv = Canvas()
    c = (cell - 1) / 2.0
    xf = Xf.pose(heading_deg, (0.0, 0.0), (c + 0.5, c + 0.5))
    shape = Ellipse(1.2, 0.0, 2.4, 2.1) | Poly([(1.0, -1.8), (1.0, 1.8), (-2.6, 0.7), (-4.4, 0.0), (-2.6, -0.7)])
    mask = cv.raster(xf, shape)
    edge = {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    head = xf.fwd((1.2, 0.0))
    for p in mask:
        if p in edge:
            cv.put(p[0], p[1], I[3])
        else:
            d = (p[0] + 0.5 - head[0]) + (p[1] + 0.5 - head[1])
            cv.put(p[0], p[1], S[3] if d < -0.6 else (S[2] if d < 0.8 else S[1]))
    q = xf.fwd((-5.4, 1.2))
    cv.put(int(math.floor(q[0])), int(math.floor(q[1])), S[1])
    return to_image(cv.px, 0, 0, cell, cell)


# ================================================================================================
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow, _ = frame(dict(FRAMES)["Idle0"])
    return {"Splasher_GoreHead": crop({q: c for q, c in mid.px.items() if -24 <= q[1] <= -17 and q[0] < 3}),
            "Splasher_GoreUmbrella": crop({q: c for q, c in mid.px.items() if q[1] < -24}),
            "Splasher_GoreGun": crop({q: c for q, c in near.px.items() if q[0] <= -6})}


def write_rig(path, cell, muzzles):
    w, h, ox, oy = cell
    mx = sum(m[0] for m in muzzles) / len(muzzles)
    my = sum(m[1] for m in muzzles) / len(muzzles)
    L = ["// <auto-generated> by art/rain/make_splasher_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Rain.NPCs",
         "{",
         "\t/// <summary>The Splasher's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells with",
         "\t/// 2 px under each; the origin is the ground point under its hips. Muzzle: the water gun's nozzle in the aim and shoot",
         "\t/// frames, from the origin, facing left.</summary>",
         "\tpublic static class SplasherRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Walk = 0, WalkFrames = %d, Idle = %d, Aim = %d, Shoot = %d;" % (WALK, INDEX["Idle0"], INDEX["Aim0"], INDEX["Shoot0"]),
         "\t\t/// <summary>Game px a planted foot slides back per walk frame (the stride over half the cycle).</summary>",
         "\t\tpublic const int WalkStep = %d;" % round(STRIDE * 2 / (WALK / 2)),
         "\t\tpublic const int MuzzleX = %d, MuzzleY = %d;" % (round(mx * 2), round(my * 2)),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Splasher%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Splasher_Glow.png")
    muzzles = [frames[INDEX[n]][4] for n in ("Aim0", "Aim1", "Shoot1")]
    write_rig(OUT + "NPCs/SplasherRigData.cs", cell, muzzles)
    export(vertical([water_glob(k * 22.5) for k in range(16)]), OUT + "Projectiles/SplasherWater.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 50, 44
    cols = 6
    out = Image.new("RGBA", (cw * cols, ch * 2), (36, 40, 48, 255))
    light = Image.new("RGBA", (cw * cols, ch * 2), (150, 180, 210, 255))
    for k, (n, p) in enumerate(FRAMES):
        far, mid, near, _, _ = frame(p)
        tile = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cv in (far, mid, near):
            tile.alpha_composite(to_image(cv.px, -cw // 2, -ch + 3, cw, ch))
        out.alpha_composite(tile, ((k % cols) * cw, (k // cols) * ch))
        light.alpha_composite(tile, ((k % cols) * cw, (k // cols) * ch))
    both = Image.new("RGBA", (cw * cols, ch * 4))
    both.alpha_composite(out, (0, 0))
    both.alpha_composite(light, (0, ch * 2))
    both = both.resize((both.width * 4, both.height * 4), Image.NEAREST)
    both.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
