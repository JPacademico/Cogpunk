"""Source for the Toadstool (D4), 2026-11-25 (user: "a new enemy called toadstoll that spawns on mushroom biomes and its a
medium frog with small mushrooms growing on his back that try to jump at the player and deals contact damage and causes
confusion, they also burst into a spore cloud when killed"). Run from the repo root:

    python -P art/bosses/fungimancer/make_toadstool_art.py [--preview FILE] [--gif FILE]

Design (my calls): a squat warty toad of the glowing mushroom fields, kin of the Fungimancer: swampy green skin over a pale
belly (the palette's frog and belly ramps), a wide mouth, big orange eyes on bumps, and three glowing mushrooms of the biome
growing out of its back (the Fungimancer's own teal seat colours; their caps glow). Three-quarter side view facing left, lit
from the top-left, sculpted (art/templates/sculpt.py: parts with real normals, pixelated per part, warts that step one ramp
step, selective outlines). Two planes: far (the far legs and the far eye's bump) and middle (everything else); the glow sheet
holds the caps' light and the eyes.

Frames (the C# picks them from the synced state):
    Idle 0-2     breathing: the throat sac swells (0, small, full) - the C# plays 0 1 2 1
    Crouch 3     the anticipation before a leap: body pressed down, head low
    Leap 4       the launch: stretched up, hind legs thrown back
    Air 5        the top of the arc: legs tucked
    Fall 6       coming down: front legs reaching
    Land 7       the squash on landing
The same frames are the player's toad form while polymorphed by the Fungimancer (Content/Bosses/Fungimancer/Polymorph).

Also: the spore cloud (Projectiles/SporeCloud.png, 32 x 32 art, 6 frames: billowing then thinning) that it bursts into and that
the Fungimancer's falling mushrooms leave; built, not drawn (a value per pixel from a few drifting blobs and noise, cut at
thresholds, banded with edge dither; the brightest small and in the middle).

Outputs (Content/Bosses/Fungimancer/): NPCs/Toadstool.png (middle), NPCs/Toadstool_Far.png, NPCs/Toadstool_Glow.png,
NPCs/ToadstoolRigData.cs, Projectiles/SporeCloud.png.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
from sculpt import Frame, Ell, Tube, Part, render  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Bosses/Fungimancer/"
FROG, BELLY, EMB, AM = RAMP["frog"], RAMP["belly"], RAMP["ember"], RAMP["amethyst"]
# the Fungimancer's mushroom seat, darkest first, and its glow (all in the palette: Fungimancer 0-47)
CAP = ((5, 32, 51), (10, 47, 71), (6, 67, 88), (8, 100, 114), (11, 135, 137), (12, 176, 161), (67, 221, 248))
STALK = BELLY
DARK = (8, 4, 6)                                            # the Fungimancer's near-black (its pupils)
W, H, OX, OY = 34, 28, 17, 26                               # the render cell (1x) round the rig origin (ground, under the middle)


class Pose:
    def __init__(self, crouch=0.0, stretch=0.0, tuck=0.0, reach=0.0, squash=0.0, sac=0.0, lift=0):
        self.crouch, self.stretch, self.tuck, self.reach, self.squash, self.sac, self.lift = crouch, stretch, tuck, reach, squash, sac, lift


def parts(p):
    """The toad's parts for a pose. Origin on the ground under its middle, facing left (head at -x), y down."""
    dy = 1.6 * p.crouch - 1.4 * p.stretch + 1.0 * p.squash - p.lift   # the body's height change (down +)
    sx = 1.0 + 0.10 * p.squash - 0.06 * p.stretch                       # wider when squashed, narrower when stretched
    sy = 1.0 - 0.14 * p.squash + 0.12 * p.stretch - 0.08 * p.crouch
    body = Frame(1.0, -6.4 + dy, -0.12 * p.stretch + 0.06 * p.reach, sx, sy)
    headf = Frame(-7.4, -8.2 + dy + 0.8 * p.crouch, -0.10 * p.stretch + 0.04 * p.reach - 0.05 * p.crouch, sx, sy)
    out = []
    # far legs (plane far): the far hind thigh and foot, the far forearm
    hind_far = Frame(7.4, -4.0 + dy * 0.7, 0.0)
    if p.stretch > 0.3 or p.tuck > 0.3 or p.reach > 0.3:
        foot = (11.0 + 3.0 * p.stretch - 2.0 * p.tuck, 1.2 + 2.0 * p.stretch - 2.4 * p.tuck - 1.0 * p.reach)
    else:
        foot = (4.6, 3.4 - dy * 0.7)
    out.append(Part("hind_far", Ell(0.0, 0.0, 3.6, 2.6), FROG, 0, hind_far, lo=1, hi=4, plane="far"))
    out.append(Part("foot_far", Tube([(1.0, 1.6), foot], [1.1, 0.8]), FROG, 1, hind_far, lo=1, hi=4, plane="far"))
    fa_end = (-5.0 - 2.0 * p.reach + 1.0 * p.tuck, -0.6 - 2.4 * p.reach - 1.4 * p.tuck + 1.6 * p.stretch)
    out.append(Part("arm_far", Tube([(-3.2, -4.6 + dy), (-4.2, -2.0 + dy * 0.5), fa_end], [1.2, 1.0, 0.9]), FROG, 1, None, lo=1, hi=4,
                    plane="far"))
    out.append(Part("eye_far", Ell(-4.6, -12.4 + dy + 0.6 * p.crouch, 1.9, 1.8), FROG, 2, None, lo=2, hi=5, plane="far"))
    # the middle: body, belly, head, near legs, mushrooms
    warts = ((-2.6, -4.2, 1.3), (2.4, -4.8, 1.2), (5.6, -2.6, 1.1), (0.0, -2.0, 1.0), (-4.4, -1.6, 0.9), (6.8, 0.4, 0.9))
    out.append(Part("body", Ell(0.0, 0.0, 9.6, 6.0), FROG, 3, body, lo=1, hi=6, bumps=warts,
                    spots=((3.6, -1.6, 2.0, 1.2, -1), (-1.0, 0.6, 1.6, 1.0, -1))))
    out.append(Part("belly", Ell(-3.4, 2.6, 6.4, 3.3, 0.3), BELLY, 4, body, lo=2, hi=5))
    out.append(Part("head", Ell(0.0, 0.0, 5.6, 4.1), FROG, 5, headf, lo=1, hi=6, bumps=((1.6, -2.4, 1.0),),
                    lines=[[(-5.2, 1.2), (-2.6, 1.9), (0.4, 1.8), (3.6, 0.6)]]))
    if p.sac > 0.0:
        r = 1.4 + 1.6 * p.sac
        out.append(Part("sac", Ell(-2.2, 3.4 + 0.6 * p.sac, r + 0.6, r * 0.8, 0.2), BELLY, 6, headf, lo=2, hi=5))
    out.append(Part("eye", Ell(0.6, -3.8 + 0.4 * p.crouch, 2.3, 2.2), FROG, 7, headf, lo=2, hi=6))
    hind = Frame(5.0, -3.6 + dy * 0.7, 0.0)
    if p.stretch > 0.3 or p.tuck > 0.3 or p.reach > 0.3:
        hfoot = (9.0 + 3.0 * p.stretch - 2.0 * p.tuck, 1.4 + 2.2 * p.stretch - 2.6 * p.tuck - 1.0 * p.reach)
    else:
        hfoot = (-3.6, 3.4 - dy * 0.7)
    out.append(Part("thigh", Ell(0.0, 0.0, 4.4, 3.1), FROG, 8, hind, lo=1, hi=6, bumps=((1.0, -1.4, 0.9),)))
    out.append(Part("foot", Tube([(0.4, 2.0), hfoot], [1.2, 0.9]), FROG, 9, hind, lo=1, hi=5))
    na_end = (-9.2 - 2.4 * p.reach + 1.0 * p.tuck, -0.6 - 2.6 * p.reach - 1.6 * p.tuck + 1.8 * p.stretch)
    out.append(Part("arm", Tube([(-6.0, -4.6 + dy), (-7.4, -2.0 + dy * 0.5), na_end], [1.4, 1.1, 1.0]), FROG, 9, None, lo=1, hi=5))
    # mushrooms on its back: stalks then caps (in the body's frame, so they ride it)
    # each stands clear of the back (a stalk from the skin, a domed cap over it), so the three read apart
    for i, (mx, my, rx, ry, base) in enumerate(((-1.8, -9.6, 3.0, 2.2, -5.4), (3.6, -8.6, 2.5, 1.9, -5.0), (7.6, -5.8, 2.0, 1.6, -3.2))):
        out.append(Part("stalk%d" % i, Tube([(mx + 0.2, base), (mx, my + 0.6)], [0.9, 0.75]), STALK, 10 + 2 * i, body, lo=3, hi=5))
        out.append(Part("cap%d" % i, Ell(mx, my, rx, ry, 0.12), CAP, 11 + 2 * i, body, lo=1, hi=6, glow_from=5,
                        spots=((mx - rx * 0.4, my + ry * 0.05, 0.6, 0.5, 1), (mx + rx * 0.3, my + ry * 0.35, 0.55, 0.45, 1))))
    return out, headf, body


def frame(p):
    """One frame -> (far, mid, glow) dicts in cell coordinates."""
    ps, headf, body = parts(p)
    far_parts = [q for q in ps if q.plane == "far"]
    mid_parts = [q for q in ps if q.plane != "far"]
    far, _, _ = render(far_parts, W, H, OX, OY)
    far = {q: dim(c) for q, c in far.items()}
    mid, glow, owner = render(mid_parts, W, H, OX, OY)
    # the eyes (after the outline): an orange iris lit from the top-left, a dark slit pupil, a glint
    ex, ey = headf.to_world(0.6, -3.8 + 0.4 * p.crouch)
    ex, ey = int(math.floor(ex + OX)) - 1, int(math.floor(ey + OY)) - 1
    for (dx, dy, c) in ((0, 0, EMB[3]), (1, 0, EMB[2]), (0, 1, EMB[2]), (1, 1, EMB[1])):
        q = (ex + dx, ey + dy)
        if q in mid:
            mid[q] = c
            if c != DARK:
                glow[q] = c
    for (dx, dy) in ((0, 1), (1, 1)):
        q = (ex + dx, ey + dy)
        if q in mid:
            mid[q] = DARK if dx == 1 else mid[q]                           # the slit pupil
    if (ex, ey) in mid:
        glow[(ex, ey)] = EMB[3]
    fx, fy = headf.to_world(-4.4, -0.6)                                   # the nostril
    q = (int(math.floor(fx + OX)), int(math.floor(fy + OY)))
    if q in mid and owner.get(q) == "head":
        mid[q] = FROG[1]
    return far, mid, glow


def dim(c):
    """The far plane a step darker (DepthLayers draws it a little darker again)."""
    for ramp in (FROG, BELLY, CAP, STALK):
        if c in ramp:
            i = ramp.index(c)
            return ramp[max(0, i - 1)]
    return c


FRAMES = (
    ("Idle0", Pose()), ("Idle1", Pose(sac=0.5)), ("Idle2", Pose(sac=1.0)),
    ("Crouch", Pose(crouch=1.0)), ("Leap", Pose(stretch=1.0, lift=1)), ("Air", Pose(tuck=1.0, lift=2)),
    ("Fall", Pose(reach=1.0, lift=1)), ("Land", Pose(squash=1.0)),
)
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def to_image(px, w=W, h=H):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def grid(images):
    out = Image.new("RGBA", (W, (H + 1) * len(images)), (0, 0, 0, 0))
    for k, im in enumerate(images):
        out.alpha_composite(im, (0, k * (H + 1)))
    return out


def body_box(frames):
    """The hitbox from the idle frame's body (not the mushrooms' tips): x from the near arm's toes to the thigh's back, y from
    the eye bumps' tops to the ground; game px from the origin."""
    _, mid, _ = frames[0]
    xs = sorted(x for (x, y) in mid)
    ys = sorted(y for (x, y) in mid)
    left, right = xs[1] - OX, xs[-2] - OX + 1
    top = ys[len(ys) // 30] - OY
    return left * 2, right * 2, top * 2


def write_rig(path, frames):
    left, right, top = body_box(frames)
    L = ["// <auto-generated> by art/bosses/fungimancer/make_toadstool_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Bosses.Fungimancer.NPCs",
         "{",
         "\t/// <summary>The Toadstool's grid sheets (game px, facing left): far and middle planes and the glow, equal cells with",
         "\t/// 2 px under each; the origin is the ground point under its middle. Body*: its hitbox from the origin (the idle",
         "\t/// frame's body, the mushrooms' tips left out).</summary>",
         "\tpublic static class ToadstoolRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (W * 2, H * 2, OX * 2, OY * 2, len(FRAMES)),
         "\t\tpublic const int Idle = 0, IdleFrames = 3, Crouch = %d, Leap = %d, Air = %d, Fall = %d, Land = %d;"
         % (INDEX["Crouch"], INDEX["Leap"], INDEX["Air"], INDEX["Fall"], INDEX["Land"]),
         "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d;" % (left, right, top),
         "\t}",
         "}"]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


# --- the spore cloud --------------------------------------------------------------------------------------------------------
CLOUD = 32
CLOUD_FRAMES = 6
CLOUD_RAMP = (AM[0], AM[1], AM[2], AM[3], AM[4], AM[5])


def spore_cloud(k, seed=7):
    """Frame k of the cloud: blobs that drift out and grow then thin; a value per pixel (blobs x soft noise), cut into the
    amethyst ramp's bands with a checker only at band edges; teal specks of glowing spores scattered in it."""
    rnd = random.Random(seed)
    blobs = [(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(6.5, 9.5), rnd.uniform(0, math.tau)) for _ in range(9)]
    grow = (0.6, 0.9, 1.05, 1.05, 0.95, 0.82)[k]
    thin = (0.0, 0.0, 0.05, 0.18, 0.36, 0.55)[k]
    spread = (0.55, 0.8, 0.95, 1.02, 1.08, 1.12)[k]
    px = {}
    c = CLOUD / 2
    for y in range(CLOUD):
        for x in range(CLOUD):
            v = 0.0
            for (bx, by, r, ph) in blobs:
                cx = c + bx * spread + math.cos(ph + k * 0.5) * 0.8
                cy = c + by * spread + math.sin(ph + k * 0.5) * 0.8
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / (r * grow)
                v = max(v, 1.0 - d)
            n = 0.5 + 0.5 * math.sin(x * 0.9 + y * 0.7 + k) * math.cos(x * 0.5 - y * 1.1 - k * 0.7)
            v = v * (0.82 + 0.18 * n) - thin
            if v <= 0.06:
                continue
            band = min(5, int(v * 7.0))
            frac = v * 7.0 - int(v * 7.0)
            if (x + y) % 2 == 0 and frac > 0.8 and band < 5:
                band += 1
            px[(x, y)] = CLOUD_RAMP[max(1, band)]
    # glowing spores: teal specks, a fixed set that drifts outwards
    spr = random.Random(seed + 1)
    for i in range(14):
        a = spr.uniform(0, math.tau)
        r = spr.uniform(2, 11) * spread
        q = (int(c + math.cos(a) * r), int(c + math.sin(a) * r))
        if q in px and (i + k) % 3:
            px[q] = CAP[6] if i % 2 else CAP[5]
    # outline: the darkest amethyst round the cloud
    edge = {}
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and 0 <= q[0] < CLOUD and 0 <= q[1] < CLOUD:
                edge[q] = AM[0]
    px.update(edge)
    return px


def cloud_sheet():
    out = Image.new("RGBA", (CLOUD, (CLOUD + 1) * CLOUD_FRAMES), (0, 0, 0, 0))
    for k in range(CLOUD_FRAMES):
        out.alpha_composite(to_image(spore_cloud(k), CLOUD, CLOUD), (0, k * (CLOUD + 1)))
    return out


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    export(grid([to_image(f[0]) for f in frames]), OUT + "NPCs/Toadstool_Far.png")
    export(grid([to_image(f[1]) for f in frames]), OUT + "NPCs/Toadstool.png")
    export(grid([to_image(f[2]) for f in frames]), OUT + "NPCs/Toadstool_Glow.png")
    write_rig(OUT + "NPCs/ToadstoolRigData.cs", frames)
    export(cloud_sheet(), OUT + "Projectiles/SporeCloud.png")
    return frames


def preview(path, frames, sc=6):
    cols = len(frames)
    out = Image.new("RGBA", (cols * (W * sc + 6) + 6, 2 * (H * sc + 6) + 6 + CLOUD * sc // 2 + 12), (20, 20, 24, 255))
    for row, bg in enumerate(((30, 34, 60), (170, 190, 210))):
        for k, (far, mid, glow) in enumerate(frames):
            im = Image.new("RGBA", (W, H), bg + (255,))
            fl = to_image(far)
            im.alpha_composite(fl)
            im.alpha_composite(to_image(mid))
            out.alpha_composite(im.resize((W * sc, H * sc), Image.NEAREST), (6 + k * (W * sc + 6), 6 + row * (H * sc + 6)))
    y = 2 * (H * sc + 6) + 12
    for k in range(CLOUD_FRAMES):
        im = Image.new("RGBA", (CLOUD, CLOUD), (30, 34, 60, 255))
        im.alpha_composite(to_image(spore_cloud(k), CLOUD, CLOUD))
        out.alpha_composite(im.resize((CLOUD * sc // 2, CLOUD * sc // 2), Image.NEAREST), (6 + k * (CLOUD * sc // 2 + 6), y))
    out.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args()
    fr = [frame(p) for _, p in FRAMES] if a.no_export else export_all()
    if a.preview:
        preview(a.preview, fr)
