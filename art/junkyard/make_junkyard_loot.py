"""Source for the Junkyard's creatures and finds of 2026-10-26 (D4). Run from the repo root:

    python -P art/junkyard/make_junkyard_loot.py

Drawn at 1x and exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left, ramp-0 outlines (the
rig.py parts and the rod / pixel-map helpers of art/bosses/trashtr0m/make_trashtr0m_loot.py). Enemies face left and
use hostile Ember for their lamps; the Mysterious Map's arrow uses friendly Brass and Aether. Outputs:

    Content/Junkyard/NPCs/RustCollector.png            40x440  11 frames of 40x40 (20x20 art; 2026-10-27: 0.8x a
                                                               player, redrawn): roll x4, fast roll x4 (leaning in,
                                                               motion streaks, the beacon flashing, the stack puffing),
                                                               skid, stunned x2. Wheels touch row 17: NPC frames are drawn
                                                               4 px low (decompiled Main.DrawNPCDirect: + 4f), so they
                                                               meet the hitbox bottom.
    Content/Junkyard/Gores/RustCollector_GoreWheel.png  a roller;  RustCollector_GorePanel.png  a bent side panel
    Content/Junkyard/NPCs/LivingTar.png                32x48   2 frames of 32x24 (squashed, stretched), slime layout
    Content/Junkyard/Projectiles/TarGlob.png           28x960  32 frames (stride 30): 16 headings (0 = flying right,
                                                               clockwise) x 2 wobbles, a teardrop of tar with a tail of
                                                               drips trailing behind (2026-10-27: it must read as a
                                                               projectile)
    Content/Junkyard/Items/TarDrop.png                 20x24   a glossy drop of tar
    Content/Junkyard/Items/CondensedTar.png            28x22   (2026-10-30) four drops boiled down at a Solidifier: a hard
                                                               brick of tar, glossy on top, a bubble caught in its face
    Content/Junkyard/Items/PolisherSchematic.png       32x28   a grease-stained blueprint of the polisher
    Content/Junkyard/Items/RustPolisher.png            48x50   item: the polisher
    Content/Junkyard/Tiles/RustPolisherTile.png        54x336  6 frames of a 3x3 tile (18 px stride, rows 16/16/18,
                                                               56 px per frame): the buffing wheel turns, sparks fly,
                                                               the gauge needle trembles (2026-10-27: the steam stack
                                                               and its puff on the top right are gone)
    Content/Junkyard/Map/MysteriousMap.png             32x28   item: an old, torn map with an X
    Content/Junkyard/Map/MysteriousMapArrow.png        40x670  16 headings (stride 42), heading 0 = right, clockwise:
                                                               a brass compass needle with a cog hub
    Content/Junkyard/Map/MysteriousMapArrow_Glow.png   40x670  its aether tip and hub gem
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Union, box, Canvas, flat, face, dome, cyl, line, stripes, seam, rivet  # noqa: E402
import make_trashtr0m_art as boss  # noqa: E402
from make_trashtr0m_loot import blit, img, img_fit, rod, boxed, hcyl, _h  # noqa: E402

I, B, C, V, E, S, LE, A = (RAMP[k] for k in ("iron", "brass", "copper", "verd", "ember", "steam", "leather", "aether"))


def export(im, rel):
    boss.export(im, rel)


def vertical(frames, pad=1):
    return boss.vertical(frames, pad)


# ================================================================================================
# Rust Collector: a headless scrap bin on two rollers (facing left, 3/4 view)
# ================================================================================================
def roller(cv, cx, cy, r, phase, blur=False):
    """A roller wheel: a dark rubber-and-iron tyre with a lit rim on its top-left, a bright iron disc, three dark spokes
    turned by phase (0..1 of a third of a turn; smeared when blur), a brass hub."""
    cv.part(Xf(), Ellipse(cx, cy, r, r), "iron", dome(cx - 1, cy - 1, r * 1.3, lo=1, hi=2, gain=1.2, bias=0.1), rust=0.0)
    disc = cv.part(Xf(), Ellipse(cx, cy, r - 1.1, r - 1.1), "iron", dome(cx - 0.8, cy - 0.8, r, lo=2, hi=4, gain=1.4, bias=0.2),
                   outline=False, rust=0.0)
    for k in range(3):
        a = math.radians(phase * 120.0 + k * 120.0)
        for d in (0.9, 1.7):
            x, y = int(math.floor(cx + math.cos(a) * d)), int(math.floor(cy + math.sin(a) * d))
            if (x, y) in disc:
                cv.put(x, y, I[1] if not blur else I[2])
        if blur:
            a2 = a + math.radians(40.0)
            x, y = int(math.floor(cx + math.cos(a2) * 1.7)), int(math.floor(cy + math.sin(a2) * 1.7))
            if (x, y) in disc:
                cv.put(x, y, I[2])
    hx, hy = int(math.floor(cx)), int(math.floor(cy))
    cv.put(hx, hy, B[4])
    cv.put(hx - 1, hy, B[3])
    cv.put(hx, hy - 1, B[3])
    cv.put(hx - 1, hy - 1, B[5])


def rust_collector(phase, lean=0.0, lamp=True, streaks=False, sparks=False, dizzy=-1, rattle=0, beacon=0, puff=0):
    """One 20x20 frame (2026-10-27: 0.8x a player, more detail). A riveted iron bin on two brass-hubbed rollers joined
    by a tread guard, facing left: the lit front face with a sensor slit and its ember lamp, the near side with panel
    seams, a dent and a hazard band, a scooping bumper, a hopper heaped with rust flakes (a cog and a pipe sticking out),
    a warning beacon on the hopper's front corner and an exhaust stack at the back. lean shears the body (+ forward =
    left, the way it rolls), rattle lifts it a pixel, beacon 1/2 lights the beacon, puff draws exhaust smoke."""
    cv = Canvas()
    shear = Xf(1.0, lean, 0.0, 1.0, -lean * 13.5, -rattle)  # x += lean * (y - 13.5): the bottom stays put
    # exhaust stack at the back (behind the hopper)
    for y in range(1, 6):
        q = shear.fwd((16.5, y + 0.5))
        x = int(math.floor(q[0]))
        cv.put(x, y - rattle, I[0])
        cv.put(x + 1, y - rattle, I[3] if y > 1 else B[4])
        cv.put(x + 2, y - rattle, I[0] if y > 1 else B[3])
    q = shear.fwd((16.5, 0.5))
    cv.put(int(math.floor(q[0])), -rattle, B[0])
    cv.put(int(math.floor(q[0])) + 2, -rattle, B[0])
    # rust flakes heaped in the open hopper (they jiggle with the phase), a cog and a pipe end sticking out
    rng = random.Random(7 + int(phase * 3) + rattle)
    for x in range(2, 16):
        top = (1 if 5 <= x <= 12 else 2) + (rng.random() < 0.25)
        for y in range(top, 5):
            q = shear.fwd((x + 0.5, y + 0.5))
            col = C[4] if y == top and x < 10 else (C[3] if y == top else (C[2], C[3], C[1], C[2])[rng.randrange(4)])
            cv.put(int(math.floor(q[0])), int(math.floor(q[1])), C[0] if x in (2, 15) and y == top else col)
    for (x, y, col) in ((9, 0, B[0]), (10, 0, B[3]), (8, 1, B[0]), (9, 1, B[4]), (10, 1, B[1]), (11, 1, B[0]), (9, 2, B[2]), (10, 2, B[1])):
        q = shear.fwd((x + 0.5, y + 0.5 - rattle))
        cv.put(int(math.floor(q[0])), int(math.floor(q[1])), col)   # a half-buried brass cog
    for (x, y, col) in ((13, 1, I[0]), (13, 2, I[3]), (14, 1, I[0]), (14, 2, I[1])):
        q = shear.fwd((x + 0.5, y + 0.5 - rattle))
        cv.put(int(math.floor(q[0])), int(math.floor(q[1])), col)   # a pipe end
    # body: the lit front face (left), the near side, the hopper rim on top
    front = cv.part(shear, Poly([(1.0, 4.0), (7.5, 4.0), (7.5, 14.0), (1.0, 14.0)]), "iron",
                    face((-0.85, 0.1, 0.5), lo=2, hi=4, gain=1.2, bias=0.2, ramp_len=5), rust=0.25)
    side = cv.part(shear, Poly([(7.5, 4.0), (18.5, 4.0), (18.5, 14.0), (7.5, 14.0)]), "iron",
                   face((0.4, 0.0, 0.9), lo=2, hi=3, gain=1.2, bias=0.05, ramp_len=5), rust=0.35)
    cv.part(shear, Poly([(0.5, 3.0), (19.0, 3.0), (19.0, 4.5), (0.5, 4.5)]), "iron", flat(4, bevel=False), rust=0.0)
    band = cv.raster(shear, box(7.5, 11.5, 18.5, 14.0)) & side
    stripes(cv, band, 2, B[4], I[0])
    seam(cv, shear, (13.0, 5.0), (13.0, 11.0), "iron", side)               # panel seam
    for (x, y) in ((9.0, 5.5), (16.5, 5.5), (9.0, 10.0), (16.5, 10.0), (2.5, 12.5), (6.0, 12.5)):
        rivet(cv, shear, (x, y), "iron", side | front)
    for (x, y) in ((14.5, 7.5), (15.5, 8.5), (14.5, 8.5)):                 # a dent in the side panel
        qq = shear.fwd((x, y))
        cv.darken(int(qq[0]), int(qq[1]))
    # the sensor slit on the front: one ember lamp (no head)
    for x in range(2, 7):
        q = shear.fwd((x + 0.5, 6.5))
        cv.put(int(math.floor(q[0])), int(math.floor(q[1])), I[0])
    q = shear.fwd((2.5, 6.5))
    lx, ly = int(math.floor(q[0])), int(math.floor(q[1]))
    if lamp:
        cv.put_glow(lx, ly, E[3])
        cv.put_glow(lx + 1, ly, E[2])
    else:
        cv.put(lx, ly, E[0])
    # a vent grille under the slit
    for (y) in (8, 10):
        line(cv, shear, (2.0, y + 0.5), (6.0, y + 0.5), lambda n: I[1], front)
    # warning beacon on the hopper's front corner (flashes while charging)
    bq = shear.fwd((2.5, 2.5))
    bx, by = int(math.floor(bq[0])), int(math.floor(bq[1]))
    cv.put(bx, by + 1, I[0])
    cv.put(bx + 1, by + 1, I[0])
    if beacon:
        cv.put_glow(bx, by, E[3] if beacon == 1 else E[2])
        cv.put_glow(bx + 1, by, E[2] if beacon == 1 else E[1])
    else:
        cv.put(bx, by, E[1])
        cv.put(bx + 1, by, E[0])
    # the scoop bumper at the front, hazard striped
    scoop = cv.part(Xf(), Poly([(-0.5, 11.0), (3.0, 11.0), (3.0, 16.5), (0.5, 16.5)]), "brass", flat(3), rust=0.0)
    stripes(cv, scoop, 2, B[4], I[0], slope=-1)
    # tread guard joining the rollers
    cv.part(Xf(), box(5.0, 13.0, 16.0, 15.0), "iron", flat(2, bevel=False), rust=0.0)
    # rollers
    roller(cv, 6.0, 14.5, 3.2, phase, blur=streaks)
    roller(cv, 15.0, 14.5, 3.2, phase + 0.5, blur=streaks)
    if puff:                                                # exhaust smoke off the back stack
        for k in range(puff):
            cx, cy = 18.5 + k * 1.2, -0.5 - k * 0.8
            for p in cv.raster(Xf(), Ellipse(cx, cy, 1.1 + k * 0.5, 0.9 + k * 0.4)):
                if p[1] >= 0:
                    cv.put(p[0], p[1], S[1] if (p[0] + p[1]) % 3 else S[0])
    if streaks:                                             # motion lines trailing behind (it rolls left)
        for (x0, y, ln) in ((19, 6, 2), (19, 9, 1), (18, 17, 2)):
            for k in range(ln):
                cv.put(x0 + k, y, S[1] if k == 0 else S[0])
    if sparks:                                              # skidding: sparks off the front roller
        for (x, y, col) in ((1, 17, E[3]), (0, 16, E[2]), (2, 16, E[3]), (0, 15, E[1])):
            cv.put_glow(x, y, col)
    if dizzy >= 0:                                          # stunned: a spinning star over the hopper
        for (x, y) in (((5, -1), (11, -1)), ((8, -1), (14, 0)))[dizzy]:
            cv.put(x, y + 1, WHITE)
    return cv


def rust_collector_old(phase, lean=0.0, lamp=True, streaks=False, sparks=False, dizzy=-1, rattle=0):
    """The 2026-10-26 16x16 design, kept for reference (not exported)."""
    cv = Canvas()
    shear = Xf(1.0, lean, 0.0, 1.0, -lean * 10.5, -rattle)   # x += lean * (y - 10.5): the bottom stays put
    # rust flakes heaped in the open hopper (they jiggle with the phase)
    rng = random.Random(7 + int(phase * 3) + rattle)
    for x in range(2, 14):
        top = (0 if 5 <= x <= 10 else 1) + (rng.random() < 0.25)
        for y in range(top, 3):
            q = shear.fwd((x + 0.5, y + 0.5))
            col = C[4] if y == top and x < 9 else (C[3] if y == top else (C[2], C[3], C[1], C[2])[rng.randrange(4)])
            cv.put(int(math.floor(q[0])), int(math.floor(q[1])), C[0] if x in (2, 13) and y == top else col)
    # body: the lit front face (left), the near side, the hopper rim on top
    front = cv.part(shear, Poly([(1.0, 3.0), (6.5, 3.0), (6.5, 10.5), (1.0, 10.5)]), "iron",
                    face((-0.85, 0.1, 0.5), lo=2, hi=4, gain=1.2, bias=0.2, ramp_len=5), rust=0.2)
    side = cv.part(shear, Poly([(6.5, 3.0), (14.5, 3.0), (14.5, 10.5), (6.5, 10.5)]), "iron",
                   face((0.4, 0.0, 0.9), lo=2, hi=3, gain=1.2, bias=0.05, ramp_len=5), rust=0.3)
    cv.part(shear, Poly([(1.0, 2.0), (14.5, 2.0), (14.5, 3.5), (1.0, 3.5)]), "iron", flat(4, bevel=False), rust=0.0)
    band = cv.raster(shear, box(6.5, 8.5, 14.5, 10.5)) & side
    stripes(cv, band, 2, B[4], I[0])
    for (x, y) in ((8.0, 4.5), (13.0, 4.5)):
        q = shear.fwd((x, y))
        cv.put(int(q[0]), int(q[1]), I[4])
    # the sensor slit on the front: one ember lamp (no head)
    for x in range(2, 6):
        q = shear.fwd((x + 0.5, 5.5))
        cv.put(int(math.floor(q[0])), int(math.floor(q[1])), I[0])
    q = shear.fwd((2.5, 5.5))
    lx, ly = int(math.floor(q[0])), int(math.floor(q[1]))
    if lamp:
        cv.put_glow(lx, ly, E[3])
        cv.put_glow(lx + 1, ly, E[2])
    else:
        cv.put(lx, ly, E[0])
    # the scoop bumper at the front, hazard striped
    scoop = cv.part(Xf(), Poly([(-0.5, 8.5), (2.5, 8.5), (2.5, 12.5), (0.5, 12.5)]), "brass", flat(3), rust=0.0)
    stripes(cv, scoop, 2, B[4], I[0], slope=-1)
    # rollers
    roller(cv, 5.0, 11.5, 2.6, phase, blur=streaks)
    roller(cv, 11.5, 11.5, 2.6, phase + 0.5, blur=streaks)
    if streaks:                                             # motion lines trailing behind (it rolls left)
        for (x0, y, ln) in ((15, 4, 3), (15, 7, 2), (14, 13, 2)):
            for k in range(ln):
                cv.put(x0 + k, y, S[1] if k == 0 else S[0])
    if sparks:                                              # skidding: sparks off the front roller
        for (x, y, col) in ((1, 13, E[3]), (0, 12, E[2]), (2, 12, E[3]), (0, 14, E[1])):
            cv.put_glow(x, y, col)
    if dizzy >= 0:                                          # stunned: a spinning star over the hopper
        for (x, y) in (((4, 0), (9, -1)), ((6, -1), (11, 0)))[dizzy]:
            cv.put(x, y + 1, WHITE)
    return cv


def rust_collector_frames():
    frames = []
    for k in range(4):
        frames.append(rust_collector(k / 4.0, rattle=k % 2))
    for k in range(4):
        frames.append(rust_collector(k / 4.0 + 0.125, lean=-0.15, streaks=True, rattle=k % 2, beacon=1 + k % 2, puff=1 + k % 2))
    frames.append(rust_collector(0.1, lean=0.18, sparks=True, beacon=1))
    frames.append(rust_collector(0.0, lean=0.07, lamp=False, dizzy=0))
    frames.append(rust_collector(0.0, lean=-0.07, lamp=False, dizzy=1))
    return [img(cv, 20, 20) for cv in frames]


def rust_collector_gores():
    wheel = Canvas()
    roller(wheel, 3.5, 3.5, 2.8, 0.2)
    panel = Canvas()
    p = panel.part(Xf.pose(-12.0, (4.0, 3.0)), Poly([(0.5, 0.5), (7.5, 1.0), (7.0, 5.5), (1.0, 5.0)]), "iron",
                   face((0.4, 0.0, 0.9), lo=1, hi=3, ramp_len=5), rust=0.5)
    stripes(panel, panel.raster(Xf.pose(-12.0, (4.0, 3.0)), box(0.5, 3.8, 7.5, 5.5)) & p, 2, B[4], I[0])
    return img(wheel, 8, 8), img_fit(panel, 10, 8, "RustCollector_GorePanel")


# ================================================================================================
# Living Tar: a slime of steaming tar (2 frames, slime layout), its glob and its drop
# ================================================================================================
TAR = LE[0]


def tar_body(cv, cx, bottom, w, h, seed, eyes=True):
    """A tar mound: I0 outline, L0 body with I0 swirls, cold gloss (I2/I3) on the top-left, a warm brass sheen, bubbles,
    a cog half-swallowed, two ember eyes."""
    rx, ry = w / 2.0, h
    cy = bottom
    mask = set()
    for y in range(int(bottom - h) - 1, int(bottom) + 1):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0 and y < bottom:
                mask.add((x, y))
    edge = {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    rng = random.Random(seed)
    for p in mask:
        if p in edge:
            cv.put(p[0], p[1], I[0])
            continue
        x, y = p
        n = _h(x, y, seed)
        cv.put(x, y, I[0] if n > 0.86 else TAR)
    # gloss: a crescent of cold highlight on the upper left, a warm sheen below it
    for p in mask - edge:
        x, y = p
        dx = (x + 0.5 - (cx - rx * 0.35)) / (rx * 0.55)
        dy = (y + 0.5 - (cy - ry * 0.68)) / (ry * 0.28)
        if dx * dx + dy * dy <= 1.0:
            cv.put(x, y, I[3] if dy < -0.2 and dx < 0.2 else I[2])
        elif (x + 0.5 - cx) > rx * 0.35 and (y + 0.5 - cy) > -ry * 0.45 and _h(x, y, seed + 3) > 0.6:
            cv.put(x, y, B[1])
    # bubbles on the skin
    for k in range(2):
        bx = int(cx + rng.uniform(-rx * 0.5, rx * 0.6))
        by = int(cy - ry * rng.uniform(0.25, 0.6))
        if (bx, by) in mask - edge and (bx + 1, by) in mask - edge:
            cv.put(bx, by, I[2])
            cv.put(bx + 1, by, I[0])
    # a cog stuck in the tar near the back
    gx, gy = int(cx + rx * 0.45), int(cy - 2)
    for (x, y, col) in ((gx, gy, B[3]), (gx + 1, gy, B[2]), (gx, gy + 1, B[2]), (gx + 1, gy + 1, B[1]), (gx - 1, gy, B[1]), (gx + 2, gy + 1, B[1])):
        if (x, y) in mask - edge:
            cv.put(x, y, col)
    if eyes:                                                # two ember eyes, low on the front (facing left)
        ey = int(cy - ry * 0.45)
        ex = int(cx - rx * 0.5)
        for (x, col) in ((ex, E[3]), (ex + 3, E[2])):
            if (x, ey) in mask - edge:
                cv.put_glow(x, ey, col)


def living_tar_frames():
    frames = []
    for k, (w, h) in enumerate(((15.0, 8.0), (13.0, 10.0))):
        cv = Canvas()
        tar_body(cv, 8.0, 10.0, w, h, 11)
        if k == 1:                                          # a wisp of steam off the top
            cv.put(9, 0, S[1])
            cv.put(10, 1, S[0])
        frames.append(img(cv, 16, 12))
    return frames


def tar_glob(heading_deg, wobble):
    """A flying glob of tar, 14x14, pointing along heading_deg (0 = right, clockwise): a fat head in front, a tapering
    tail of tar behind it and two drips breaking off the tail. The shape is built pointing right and placed by a
    transform (rasterised, never rotated as a bitmap); the gloss is lit in screen space from the top-left whatever the
    heading. wobble 0/1 squashes the head and flicks the tail."""
    cv = Canvas()
    xf = Xf.pose(heading_deg, (0.0, 0.0), (7.0, 7.0))
    hr, vr = (3.3, 2.8) if wobble == 0 else (3.0, 3.1)
    flick = 0.6 if wobble == 0 else -0.6
    shape = Ellipse(1.6, 0.0, hr, vr) | Poly([(1.4, -2.4), (1.4, 2.4), (-3.5, 1.2 + flick * 0.5), (-6.4, flick), (-3.5, -1.0 + flick * 0.5)])
    mask = cv.raster(xf, shape)
    drips = set()
    for (lx, ly, r) in ((-6.8, flick * 1.6 + 1.6, 0.8), (-5.2, -1.9 + flick, 0.6)) if wobble == 0 else ((-7.2, flick * 1.4 - 1.4, 0.8), (-5.0, 2.0 + flick, 0.6)):
        q = xf.fwd((lx, ly))
        x, y = int(math.floor(q[0])), int(math.floor(q[1]))
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            if (x + dx, y + dy) not in mask:
                drips.add((x + dx, y + dy))
    edge = {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for p in mask:
        cv.put(p[0], p[1], I[0] if p in edge else TAR)
    head = xf.fwd((1.6, 0.0))
    for p in mask - edge:                                   # gloss: cold on the head's top-left, warm sheen below-right
        dx, dy = p[0] + 0.5 - (head[0] - 1.2), p[1] + 0.5 - (head[1] - 1.2)
        if dx * dx + dy * dy <= 1.3:
            cv.put(p[0], p[1], I[3] if dx + dy < 0 else I[2])
        elif 0.9 < (p[0] + 0.5 - head[0]) + (p[1] + 0.5 - head[1]) < 3.0:
            cv.put(p[0], p[1], B[1])
    for p in drips:                                         # 2x2 drips: outline-dark tar
        cv.put(p[0], p[1], I[0] if (p[0] + p[1]) % 2 else TAR)
    return cv


def tar_glob_frames():
    out = []
    for k in range(16):
        for w in range(2):
            out.append(img(tar_glob(k * 22.5, w), 14, 14))
    return out


def tar_drop():
    cv = Canvas()
    mask = set()
    for y in range(0, 12):
        for x in range(0, 10):
            px, py = x + 0.5 - 5.0, y + 0.5
            r = 0.0 if py < 2 else min(3.8, (py - 1.5) * 0.9) if py < 7 else math.sqrt(max(0.0, 3.9 ** 2 - (py - 7.6) ** 2))
            if abs(px) <= r:
                mask.add((x, y))
    edge = {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for p in mask:
        cv.put(p[0], p[1], I[0] if p in edge else TAR)
    for (x, y, col) in ((3, 6, I[3]), (3, 7, I[2]), (4, 5, I[2]), (3, 8, I[2]), (6, 9, B[1]), (7, 8, B[1]), (5, 3, I[2])):
        if (x, y) in mask - edge:
            cv.put(x, y, col)
    cv.put(4, 6, WHITE)
    return img(cv, 10, 12)


CONDENSED_TAR = (        # 14x11: a brick of hardened tar in 3/4 view; its top catches the light, a bubble is trapped in its face
    "...oooooooo...",
    "..ommhhgmmmo..",
    ".omhgmmmmmmmo.",
    ".ommmmmgmmmdo.",
    "oommmmmmmmddoo",
    "odmmmddddddddo",
    "oddddddddddddo",
    "oddddddwgddddo",
    "oddddddgoddddo",
    ".oddddddddddo.",
    "..oooooooooo..",
)
CONDENSED_COLOURS = {"o": I[0], "d": TAR, "m": LE[1], "g": I[2], "h": I[3], "w": WHITE}


def condensed_tar():
    """Condensed Tar (2026-10-30): the pixel map above (tar's own colours: Iron 0 outline, Leather 0/1, the Iron 2/3 gloss)."""
    cv = Canvas()
    for y, row in enumerate(CONDENSED_TAR):
        for x, ch in enumerate(row):
            if ch in CONDENSED_COLOURS:
                cv.put(x, y, CONDENSED_COLOURS[ch])
    return img(cv, 14, 11)


# ================================================================================================
# Polisher Schematic, Mysterious Map
# ================================================================================================
def polisher_schematic():
    """A blueprint (aether paper, steam linework) of the polisher's wheel and motor, rolled on a brass rod at the top,
    a grease stain and a torn corner."""
    cv = Canvas()
    for y in range(2, 14):
        for x in range(1, 15):
            if (x, y) == (14, 13) or (x, y) == (13, 13) or (x, y) == (14, 12):
                continue                                    # torn corner
            edge = x in (1, 14) or y == 13
            cv.put(x, y, A[0] if edge else A[1])
    for y in range(3, 13, 3):                               # the grid
        for x in range(2, 14):
            if cv.get(x, y) == A[1]:
                cv.put(x, y, A[2] if x % 2 else A[1])
    for p in cv.raster(Xf(), Ellipse(5.5, 8.0, 3.2, 3.2)) - cv.raster(Xf(), Ellipse(5.5, 8.0, 2.2, 2.2)):
        cv.put(p[0], p[1], S[2])                            # the buffing wheel
    cv.put(5, 8, S[2])
    for x in range(9, 13):                                  # the motor
        cv.put(x, 6, S[2])
        cv.put(x, 9, S[2])
    for y in range(6, 10):
        cv.put(9, y, S[2])
        cv.put(12, y, S[2])
    line(cv, Xf(), (6.0, 5.0), (10.0, 6.0), lambda n: S[1])  # the belt
    for (x, y) in ((11, 11), (12, 11), (11, 12), (10, 12), (12, 10)):
        cv.put(x, y, LE[1])                                 # grease
    hcyl(cv, 0, 15, 0, 2, "brass")                          # the roller rod
    cv.put(0, 1, B[0])
    cv.put(15, 1, B[0])
    return img(cv, 16, 14)


def mysterious_map():
    """Old parchment (Brass 5/4) torn at the edges, a dotted route in leather, an ember X, a compass rose."""
    cv = Canvas()
    rng = random.Random(4)
    for y in range(1, 13):
        for x in range(1, 15):
            if (x in (1, 14) or y in (1, 12)) and rng.random() < 0.3:
                continue                                    # ragged edges
            cv.put(x, y, B[5] if (x + y * 2) % 7 else B[4])
    pts = {p for p in cv.px}
    for p in list(pts):
        if any((p[0] + ox, p[1] + oy) not in pts for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cv.put(p[0], p[1], B[2])
    for (x, y) in ((3, 10), (4, 9), (5, 9), (6, 8), (7, 7), (8, 7), (9, 6)):
        if (x + y) % 2 == 0:
            cv.put(x, y, LE[1])                             # the dotted route
    for (x, y) in ((10, 4), (12, 4), (11, 5), (10, 6), (12, 6)):
        cv.put(x, y, E[1])                                  # X marks the spot
    for (x, y, col) in ((3, 3, LE[1]), (3, 2, LE[0]), (2, 3, LE[2]), (4, 3, LE[2]), (3, 4, LE[2])):
        cv.put(x, y, col)                                   # compass rose
    for (x, y) in ((8, 11), (9, 11), (12, 9)):
        cv.put(x, y, B[3])                                  # stains
    return img(cv, 16, 14)


def map_arrow(heading_deg):
    """A bold brass arrow pointing along heading_deg (screen space, clockwise from right): an arrowhead and shaft lit on
    their upper half and shaded on the lower half (local space, so every heading keeps the same read), a cog at the tail
    and an aether gem set in the head. 20x20, centred; rendered per heading, never rotated at runtime."""
    cv = Canvas()
    xf = Xf.pose(heading_deg, (0.0, 0.0), (10.0, 10.0))
    head = Poly([(1.5, -4.6), (9.4, 0.0), (1.5, 4.6), (3.0, 0.0)])
    shaft = box(-5.5, -1.7, 3.5, 1.7)
    two_tone = lambda i: 5 if i.ly < -0.6 else (4 if i.ly < 0.6 else 2)   # noqa: E731
    cv.part(xf, shaft | head, "brass", two_tone, rust=0.0)
    teeth = Union(*[Capsule((-6.0, 0.0), (-6.0 + math.cos(math.radians(a)) * 3.3, math.sin(math.radians(a)) * 3.3), 0.9) for a in range(0, 360, 60)])
    cv.part(xf, Ellipse(-6.0, 0.0, 2.3, 2.3) | teeth, "iron", dome(-7.0, -1.0, 3.4, lo=1, hi=4), rust=0.0)
    hub = xf.fwd((-6.0, 0.0))
    cv.put(int(math.floor(hub[0])), int(math.floor(hub[1])), B[4])
    for (lx, ly, col) in ((4.6, 0.0, A[3]), (3.6, 0.0, A[2]), (5.6, 0.0, A[2]), (4.6, -0.9, A[2]), (4.6, 0.9, A[1])):
        q = xf.fwd((lx, ly))
        cv.put_glow(int(math.floor(q[0])), int(math.floor(q[1])), col)
    tip = xf.fwd((8.6, 0.0))
    cv.put_glow(int(math.floor(tip[0])), int(math.floor(tip[1])), WHITE)
    return cv


def map_arrow_frames():
    frames, glows = [], []
    for k in range(16):
        cv = map_arrow(k * 22.5)
        frames.append(img(cv, 20, 20))
        glows.append(img(cv, 20, 20, glow=True))
    return frames, glows


# ================================================================================================
# Rust Polisher: a 3x3 bench grinder (24x25 art, sliced into tile cells)
# ================================================================================================
def polisher_picture(f):
    """Frame f (0..5) of the polisher, 24 wide and 25 tall; row 24 is the one that sinks into the floor."""
    cv = Canvas()
    # the bench: cast-iron top, legs, a drawer of rusted plates
    boxed(cv, 1, 22, 14, 17, "iron", 3, 2, 1)
    for x in range(2, 22, 4):
        cv.put(x, 15, I[4])
    for (x0, x1) in ((2, 4), (19, 21)):
        for x in range(x0, x1 + 1):
            for y in range(18, 25):
                cv.put(x, y, I[0] if x in (x0, x1) else (I[2] if x == x0 + 1 else I[1]))
    boxed(cv, 6, 17, 18, 22, "copper", 3, 2, 1)             # the drawer of rusted metal
    for x in range(8, 16, 3):
        cv.put(x, 19, C[4])
        cv.put(x + 1, 20, C[1])
    cv.put(11, 21, B[4])                                    # its handle
    cv.put(12, 21, B[3])
    for x in range(1, 23):
        cv.put(x, 24, I[0])                                 # the foot rail, into the floor
        if 2 <= x <= 21:
            cv.put(x, 23, I[1] if x % 3 else I[2])
    # the motor: a brass drum lying on the bench, with a riveted band
    hcyl(cv, 9, 18, 7, 13, "brass")
    for x in (11, 15):
        cv.put(x, 9, B[5])
        cv.put(x + 1, 10, B[1])
    for y in range(8, 13):
        cv.put(13, y, B[1] if y % 2 else B[4])
    # the pressure gauge on the motor's end, its needle trembling
    cv.part(Xf(), Ellipse(18.5, 10.0, 2.2, 2.2), "brass", flat(3), rust=0.0)
    cv.put(18, 10, S[2])
    cv.put(19, 9, S[2])
    nd = [(19, 9), (19, 10), (19, 9), (18, 9), (19, 9), (19, 10)][f]
    cv.put(nd[0], nd[1], E[1])
    # the belt from the motor's pulley to the wheel
    line(cv, Xf(), (9.0, 8.0), (5.0, 5.0), lambda n: LE[0])
    line(cv, Xf(), (9.0, 12.0), (5.0, 12.0), lambda n: LE[0])
    # the buffing wheel: a cloth disc (steam rim) on an iron hub, marks turning with f
    for p in cv.raster(Xf(), Ellipse(5.0, 9.0, 4.4, 4.6)):
        rx, ry = p[0] + 0.5 - 5.0, p[1] + 0.5 - 9.0
        d = math.hypot(rx / 4.4, ry / 4.6)
        if d > 0.86:
            col = S[0]
        elif rx + ry < -1.5:
            col = S[2]
        else:
            col = S[1]
        cv.put(p[0], p[1], col)
    for k in range(3):                                      # the cloth's stitched marks rotate
        a = math.radians(f * 20.0 + k * 120.0)
        cv.put(int(math.floor(5.0 + math.cos(a) * 3.0)), int(math.floor(9.0 + math.sin(a) * 3.2)), S[0])
    cv.part(Xf(), Ellipse(5.0, 9.0, 1.5, 1.5), "iron", flat(3), rust=0.0)
    # the plate held to the wheel, rusty on one side and polished bright where it touches
    for x in range(0, 3):
        for y in range(12, 15):
            cv.put(x, y, C[2] if x == 0 else (I[4] if y == 12 else I[3]))
    sparks = [((1, 11), (0, 10)), ((2, 10), (0, 9)), ((1, 10), (0, 11)), ((2, 11), (1, 9)), ((0, 10), (2, 9)), ((1, 9), (0, 11))][f]
    for k, (x, y) in enumerate(sparks):
        cv.put(x, y, B[5] if k == 0 else B[4])
    return cv


def polisher_tile_frames():
    """Slices each picture into the 3x3 tile layout: cells 8 wide (+1 gap), rows 8, 8 and 9 tall (+1 gap each)."""
    frames = []
    for f in range(6):
        pic = img(polisher_picture(f), 24, 25)
        from PIL import Image
        out = Image.new("RGBA", (27, 28), (0, 0, 0, 0))
        for cx in range(3):
            for (cy, y0, h) in ((0, 0, 8), (1, 8, 8), (2, 16, 9)):
                cell = pic.crop((cx * 8, y0, cx * 8 + 8, y0 + h))
                out.alpha_composite(cell, (cx * 9, cy * 9))
        frames.append(out)
    return frames


def export_all():
    rc = rust_collector_frames()
    export(vertical(rc, pad=0), "Content/Junkyard/NPCs/RustCollector.png")
    wheel, panel = rust_collector_gores()
    export(wheel, "Content/Junkyard/Gores/RustCollector_GoreWheel.png")
    export(panel, "Content/Junkyard/Gores/RustCollector_GorePanel.png")
    export(vertical(living_tar_frames(), pad=0), "Content/Junkyard/NPCs/LivingTar.png")
    export(vertical(tar_glob_frames()), "Content/Junkyard/Projectiles/TarGlob.png")
    export(tar_drop(), "Content/Junkyard/Items/TarDrop.png")
    export(condensed_tar(), "Content/Junkyard/Items/CondensedTar.png")
    export(polisher_schematic(), "Content/Junkyard/Items/PolisherSchematic.png")
    export(img(polisher_picture(0), 24, 25), "Content/Junkyard/Items/RustPolisher.png")
    export(vertical(polisher_tile_frames(), pad=0), "Content/Junkyard/Tiles/RustPolisherTile.png")
    export(mysterious_map(), "Content/Junkyard/Map/MysteriousMap.png")
    frames, glows = map_arrow_frames()
    export(vertical(frames), "Content/Junkyard/Map/MysteriousMapArrow.png")
    export(vertical(glows), "Content/Junkyard/Map/MysteriousMapArrow_Glow.png")


if __name__ == "__main__":
    export_all()
