"""Source for the Flying Buddha Head (D4), 2026-11-12 (user: "add a new enemy to coghaven called 'Flying Buddha head' it
should float around and try to smash the player. high damage but slow and it should stay stunned for 2 seconds after
smashing"). Run from the repo root:

    python -P art/coghaven/make_buddha_head_art.py [--preview FILE]

Design (my calls): a colossal bronze Buddha head broken off a palace statue and kept aloft by Coghaven's machinery. It
faces the camera (D4 rule 13: flying heads may), lit from the top-left: a bronze face (gilt) weathered green in patches
(verdigris, in the face's own space), the cranial bump (ushnisha) covered in rows of snail-shell curls, long earlobes, a
jade urna on the brow that glows, and two riveted brass bands strapped round it where it cracked (steampunk repair). At
rest its eyes are closed and serene; for the smash they open, blazing jade, and the brows knit. Behind it a great bronze
cog halo with a jade inner ring turns on its own clock (the far plane), and steam jets out of the cut neck (dust, in code).

Planes (DepthLayers grid sheets): far (the halo), middle (the head), no near sheet (nothing is in front); the glow sheet holds
the urna and the open eyes. Stable pixels (D4 rule 17): the head never moves inside its frames (the float's bob is the
whole sprite, in code); the halo's cog is drawn fresh at each angle from its own polar shape.

Frames:
- Float x4: serene, eyes closed, the halo turning a quarter of a tooth each frame (a loop).
- Wrath x3: the telegraph: the eyes open and blaze brighter, the brows knit, the urna flares (the halo keeps turning).
- Smash x2: the wrathful face, mouth set, as it plunges.
- Stunned x4: after the impact: a crack over the brow, the eyes dazed (alternating), the halo slowed.

Outputs:
    Content/Coghaven/NPCs/FlyingBuddhaHead.png, _Far.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/FlyingBuddhaHeadRigData.cs   cells, origin (the chin's middle), frames
    Content/Coghaven/Gores/FlyingBuddhaHead_GoreHalf.png, _GoreEar.png, _GoreCog.png
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
from westbots import (RAMP, Xf, Ellipse, Capsule, Union, Poly, Canvas, flat, dome, P, finish, texture, _hash)  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
G, V, JD, ST, K, IV = RAMP["gilt"], RAMP["verd"], RAMP["ghost"], RAMP["steel"], RAMP["crimson"], RAMP["ivory"]

# --- the head (art px, facing the camera, y down; the origin under the chin's middle) ----------------------------------------
FACE = (0.0, -17.0, 13.0, 15.0)                # centre, radii
USHNISHA = (0.0, -32.0, 9.0, 6.0)
EARS = ((-14.0, -21.0, -15.0, -9.0), (14.0, -21.0, 15.0, -9.0))   # top and lobe of each ear
NECK = (-7.0, -4.0, 7.0, 1.0)
HALO = (0.0, -20.0)                            # the cog's hub
HALO_R = (19.0, 23.0, 26.0)                    # the jade ring's edge, the cog's root, its tips
TEETH = 12


class Pose:
    def __init__(self, eyes="closed", glow=0, brows=0, mouth=0, halo=0.0, crack=False, daze=0):
        self.eyes = eyes            # "closed", "open" or "dazed"
        self.glow = glow            # 0..3: the eyes' and the urna's blaze
        self.brows = brows          # 0 serene, 1 knitted
        self.mouth = mouth          # 0 smile, 1 set
        self.halo = halo            # degrees the halo has turned
        self.crack = crack          # the brow cracked by the impact
        self.daze = daze            # 0 / 1: which dazed eye frame


def patina(seed):
    """Verdigris patches in the face's own space (value noise on a coarse grid, stable)."""
    def is_patch(x, y):
        cx, cy = math.floor(x / 4.0), math.floor(y / 4.0)
        return _hash(int(cx), int(cy), seed) < 0.16 and _hash(int(x), int(y), seed + 1) > 0.18
    return is_patch


def face_shade():
    base = dome(-4.0, -24.0, 17.0, lo=2, hi=8, gain=1.45, bias=0.06, fixed=True, dither=0.22)
    green = patina(83)

    def shade(i):
        k = base(i)
        return k
    return shade, green


def head(mid, glow, p):
    T = Xf()
    shade, green = face_shade()
    # the ears first (they sit behind the cheeks)
    for (ex, ey, lx, ly) in EARS:
        ear = Union(Capsule((ex, ey), (lx, ly), 2.4, 2.0), Ellipse(lx, ly + 1.4, 3.0, 2.8))
        inner = mid.part(T, ear, "gilt", dome(ex - 2.0, ey - 2.0, 8.0, lo=2, hi=7, gain=1.35, fixed=True), rust=0.0)
        for y in range(int(ly - 1), int(ly + 3)):         # the lobe's stretched hole
            q = (int(math.floor(lx)) + (1 if lx > 0 else -2), y)
            if q in inner:
                mid.put(q[0], q[1], G[1])
    neck = mid.part(T, Poly([(NECK[0], NECK[1]), (NECK[2], NECK[1]), (NECK[2] - 1.0, NECK[3]), (NECK[0] + 1.0, NECK[3])]), "steel",
                    dome(-3.0, -3.0, 8.0, lo=2, hi=6, gain=1.3, fixed=True), rust=0.0)
    face = mid.part(T, Ellipse(*FACE), "gilt", shade, rust=0.0)
    cap = mid.part(T, Ellipse(*USHNISHA), "gilt", dome(-3.0, -36.0, 9.0, lo=2, hi=7, gain=1.4, fixed=True), rust=0.0)
    # verdigris over the bronze (the face's own space)
    for q in list(face | cap):
        if green(q[0], q[1]):
            col = mid.px.get(q)
            if col in G:
                k = G.index(col)
                mid.put(q[0], q[1], V[max(0, min(3, (k - 1) // 2))])
    # the snail-shell curls on the cap and the hairline: little bronze knobs, lit at their top-left
    for row, (y, xs) in enumerate(((-37.0, (-5, -1, 3)), (-34.0, (-7, -3, 1, 5)), (-31.0, (-9, -5, -1, 3, 7)), (-28.0, (-11, -7, -3, 1, 5, 9)))):
        for x in xs:
            c = P(T, (x, y))
            for (dx, dy, col) in ((0, 0, G[8]), (1, 0, G[6]), (0, 1, G[5]), (1, 1, G[3]), (2, 0, G[1]), (2, 1, G[1]), (0, 2, G[1]), (1, 2, G[1])):
                if (c[0] + dx, c[1] + dy) in (cap | face):
                    mid.put(c[0] + dx, c[1] + dy, col)
    return face, cap, neck


def bands(mid, face, cap):
    """Two riveted brass bands strapped round the head where it cracked (steampunk repair): one across the brow, one
    down the right cheek."""
    T = Xf()
    for y in range(-27, -25):
        for x in range(-14, 15):
            if (x, y) in face:
                mid.put(x, y, G[8] if y == -27 else G[5])
    for x in (-11, -5, 5, 11):
        if (x, -26) in face:
            mid.put(x, -26, ST[7])
            mid.put(x, -25, ST[3])
    for y in range(-24, -6):
        for x in (8, 9):
            if (x, y) in face:
                mid.put(x, y, G[7] if x == 8 else G[4])
    for y in (-21, -15, -9):
        if (8, y) in face:
            mid.put(8, y, ST[7])
            mid.put(9, y, ST[3])


def features(mid, glow, p, face):
    """The eyes, brows, nose, mouth and the urna: stamped after finish() so they stay crisp. Drawn on the left side and
    mirrored about the face's middle (pixel x mirrors to -1 - x)."""
    def both(x, y, col, glowing=False):
        for xx in (x, -1 - x):
            if glowing:
                mid.put_glow(xx, y, col)
                glow.put_glow(xx, y, col)
            else:
                mid.put(xx, y, col)

    # brows: arched (serene) or knitted down towards the nose (wrath)
    brow = ((-9, -22), (-8, -23), (-7, -23), (-6, -23), (-5, -22)) if p.brows == 0 else ((-9, -24), (-8, -23), (-7, -23), (-6, -22), (-5, -21))
    for (x, y) in brow:
        both(x, y, G[2])
    # eyes
    if p.eyes == "closed":
        for (x, y, col) in ((-9, -19, G[2]), (-8, -18, G[1]), (-7, -18, G[1]), (-6, -18, G[1]), (-5, -19, G[2]), (-8, -20, G[6]), (-7, -20, G[6])):
            both(x, y, col)
    elif p.eyes == "open":
        for (x, y) in ((-8, -19), (-7, -19), (-6, -19), (-7, -20), (-7, -18)):
            both(x, y, IV[4])
        for (x, y) in ((-9, -19), (-5, -19), (-8, -20), (-6, -20), (-8, -18), (-6, -18)):
            both(x, y, G[1])
        iris = (JD[3], JD[4], JD[5], JD[5])[min(3, p.glow)]
        for (x, y) in (((-7, -19), (-6, -19), (-7, -20)) if p.glow >= 2 else ((-7, -19),)):
            both(x, y, iris, glowing=True)
    else:                                                  # dazed, alternating
        pts = ((-8, -19), (-7, -20), (-6, -19), (-7, -18)) if p.daze == 0 else ((-8, -20), (-6, -20), (-7, -19), (-8, -18), (-6, -18))
        for (x, y) in pts:
            both(x, y, G[1])
    # the nose: a broad bridge lit on its left
    for y in range(-17, -11):
        mid.put(-2, y, G[7])
        mid.put(-1, y, G[6])
        mid.put(0, y, G[5])
        mid.put(1, y, G[3])
    for (x, y, col) in ((-3, -11, G[3]), (-2, -11, G[2]), (-1, -11, G[2]), (0, -11, G[2]), (1, -11, G[2]), (2, -11, G[3])):
        mid.put(x, y, col)
    # the mouth: a calm smile or set lips
    lips = ((-4, -8), (-3, -7), (-2, -7), (-1, -7)) if p.mouth == 0 else ((-4, -7), (-3, -7), (-2, -7), (-1, -7))
    for (x, y) in lips:
        both(x, y, K[1])
    both(-1, -6, G[6])
    # the urna, between the brows
    u = (JD[3], JD[4], JD[5], JD[5])[min(3, p.glow)]
    for (x, y) in ((-1, -24), (-1, -25)):
        both(x, y, u, glowing=True)
    if p.crack:
        for (x, y) in ((3, -31), (3, -30), (2, -29), (2, -28), (3, -27), (4, -26), (4, -25), (5, -24)):
            mid.put(x, y, G[0])


def halo(far, p):
    """The cog halo: TEETH teeth on a bronze rim, spokes to a jade inner ring; drawn at angle p.halo from its polar shape."""
    hx, hy = HALO
    r_ring, r_root, r_tip = HALO_R
    for y in range(int(hy - r_tip - 1), int(hy + r_tip + 2)):
        for x in range(int(hx - r_tip - 1), int(hx + r_tip + 2)):
            dx, dy = x + 0.5 - hx, y + 0.5 - hy
            r = math.hypot(dx, dy)
            th = math.degrees(math.atan2(dy, dx)) - p.halo
            tooth = math.cos(math.radians(th * TEETH)) > 0.1
            outer = r_tip if tooth else r_root
            if r > outer or r < r_ring - 3.0:
                continue
            # light from the top-left on the rim; the jade ring inside
            lightness = -(dx + dy) / (math.sqrt(2) * max(1.0, r))
            if r < r_ring:
                k = 3 + (1 if lightness > 0.3 else 0) - (1 if lightness < -0.4 else 0)
                far.put(x, y, JD[max(1, min(4, k))])
            elif r > outer - 1.0 or r < r_ring + 1.0:
                far.put(x, y, G[1])                        # the rim's dark edge (its outline)
            else:
                k = 4 + int(round(lightness * 2.5))
                far.put(x, y, G[max(2, min(8, k))])
    # spokes from the ring in to the hub hide behind the head; the hub itself is hidden too


# --- a frame ---------------------------------------------------------------------------------------------------------------
def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    halo(far, p)
    face, cap, neck = head(mid, glow, p)
    finish(mid)
    bands(mid, face, cap)
    features(mid, glow, p, face)
    return far, mid, near, glow


STEP = 360.0 / TEETH / 4.0                     # a quarter of a tooth a frame: the float loops in 4
FRAMES = ([("Float%d" % k, Pose(halo=STEP * k)) for k in range(4)]
          + [("Wrath%d" % k, Pose(eyes="open", glow=k + 1, brows=1 if k >= 1 else 0, halo=STEP * k)) for k in range(3)]
          + [("Smash%d" % k, Pose(eyes="open", glow=3, brows=1, mouth=1, halo=STEP * (k * 2))) for k in range(2)]
          + [("Stunned%d" % k, Pose(eyes="dazed", daze=k % 2, crack=True, halo=STEP * (k // 2))) for k in range(4)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- outputs -----------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Stunned0"])
    return {"FlyingBuddhaHead_GoreHalf": crop({q: c for q, c in mid.px.items() if q[0] <= 0 and q[0] >= -13}),
            "FlyingBuddhaHead_GoreEar": crop({q: c for q, c in mid.px.items() if q[0] >= 13}),
            "FlyingBuddhaHead_GoreCog": crop({q: c for q, c in far.px.items() if q[0] <= -12 and q[1] >= -24})}


def write_rig(path, cell):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/coghaven/make_buddha_head_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.NPCs",
         "{",
         "\t/// <summary>The Flying Buddha Head's grid sheets (game px; it faces the camera): far (the halo), middle (the head),",
         "\t/// near (empty) and the glow, equal cells with 2 px under each; the origin is under the chin's middle.</summary>",
         "\tpublic static class FlyingBuddhaHeadRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Float = 0, FloatFrames = 4, Wrath = %d, WrathFrames = 3, Smash = %d, SmashFrames = 2, Stunned = %d, StunnedFrames = 4;"
         % (INDEX["Wrath0"], INDEX["Smash0"], INDEX["Stunned0"]),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1)):                  # no near plane: nothing is in front of a head
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/FlyingBuddhaHead%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/FlyingBuddhaHead_Glow.png")
    write_rig(OUT + "NPCs/FlyingBuddhaHeadRigData.cs", cell)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=4):
    cw, ch = 60, 56
    cols = 5
    rows = (len(FRAMES) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (34, 40, 46, 255)), (1, (150, 170, 190, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p) in enumerate(FRAMES):
            far, mid, near, _ = frame(p)
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
