"""Source for the Fungimancer, the glowing mushroom biome's secret boss, and its things (D4), 2026-11-19. Run from the repo
root:

    python -P art/bosses/fungimancer/make_fungimancer_art.py [--preview FILE]

User, 2026-11-19: "add a new secret boss to the blue mushroom area called "Fungimancer" a magic dumb frog like creature ...
Reference for the design on the example image of the prompt (floaty boss)". The reference (a painting, kept in
reference/fungimancer_user_2026-11-19.png) is redrawn here as pixel art in the Cogpunk palette, its body plan and colours
kept, nothing traced: a fat frog (the cactus ramp) with a pale belly (sage), a wide head with big bulging orange eyes
(ember) on top, slit pupils that look two ways at once (the "dumb" part), a dopey mouth, red frills sweeping back off the
head (crimson) and arms going from green to red hands; it sits on the cap of a floating glowing mushroom (the biome's
blue: denim, violet gills, pale spots that glow), its magic violet (aether).

Three planes (D4 rule 13, drawn with Core/Visuals/DepthLayers): far (the far arm), middle (the seat, the body, the head),
near (the near arm). The art faces left; each frame is a pose of the same parts (no part redrawn, nothing rotated at
runtime). Frames (FungimancerRigData's names):
  Idle 0-3      breathing, a blink on the last
  Cast 4-7      the near hand rises, lights up violet, flings forward, comes back (the spore bolts)
  Croak 8-11    the throat sac swells, holds, croaks (the mushroom bloom), sinks
  Tongue 12-14  the mouth opens wide, stays open (the tongue is drawn by the game), shuts
  Fizzle 15-16  the spell goes wrong: eyes crossed, a dumb open mouth (the dumb moment)
  Intro 17-18   eyes shut, then open (rising out of the spores)
  Death 19-22   it bloats, glowing mushrooms sprout all over it, bloats more (then bursts: gores)

Outputs (Content/Bosses/Fungimancer/):
    Fungimancer.png, _Far.png, _Near.png, _Glow.png    grid sheets (COLUMNS wide), 2 px right of and under each cell
    FungimancerRigData.cs                              cells, frame indices, hitbox, points per frame
    Fungimancer_Head_Boss.png                          the map icon
    Gores/Fungimancer_Gore{Head,Body,Seat}.png
    Projectiles/SporeBolt.png (4 frames), ShroomSpike.png (4 frames), FungimancerTongue.png (the tongue's tip)
    Items/FungimancerBag.png, Items/RainbowMushroom.png, Tiles/RainbowMushroomTile.png (3 styles)
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
from rig import RAMP, Xf, Ellipse, Capsule, Poly, Canvas, dome  # noqa: E402
from westbots import finish, limb  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Bosses/Fungimancer/"
COLUMNS = 4
GROUND_CLIP = 2
CA, SA, K, EM, DN, AE, SM, IV = (RAMP[k] for k in ("cactus", "sage", "crimson", "ember", "denim", "aether", "steam", "ivory"))

# --- the rig (1x px, facing left, y negative up; the origin under the seat's stalk) ----------------------------------------
SEAT_C, SEAT_R = (0.0, -9.0), (28.0, 9.0)
BODY_C, BODY_R = (1.0, -29.0), (18.5, 16.5)
BELLY_C, BELLY_R = (-3.0, -26.5), (12.5, 12.5)
HEAD_C, HEAD_R = (-2.0, -46.0), (16.5, 9.5)
EYE_N, EYE_F = (-10.0, -54.5, 6.0), (7.5, -55.5, 5.0)
SHOULDER_N, SHOULDER_F = (-13.0, -35.0), (14.0, -36.0)
MOUTH = (-15.5, -42.5)                     # the corner of the mouth at the front (the tongue leaves it)
# the frills: red tendrils off the back of the head, each a root, a bend and a tip (they sweep back and droop)
FRILLS = (((10.0, -51.0), (19.0, -58.0), (26.0, -56.0), 2.0), ((12.0, -47.0), (22.0, -51.0), (28.0, -47.0), 1.9),
          ((12.0, -43.0), (21.0, -43.0), (26.0, -37.0), 1.8), ((7.0, -55.0), (13.0, -63.0), (20.0, -64.0), 1.6),
          ((10.0, -39.0), (17.0, -35.0), (20.0, -29.0), 1.5))
SPROUTS = ((-11.0, -38.0), (13.0, -40.0), (-15.0, -24.0), (16.0, -25.0), (3.0, -19.0), (-3.0, -60.0), (9.0, -31.0))


class Pose:
    def __init__(self, near=(-13.5, -21.5), far=(13.0, -22.5), sac=0.0, mouth=0, eyes=0, breath=0, bloat=0.0, shrooms=0, magic=0):
        self.near, self.far = near, far             # the hands (the arms reach from the shoulders)
        self.sac = sac                              # 0..1: the throat sac's swell
        self.mouth = mouth                          # 0 shut (a dopey line), 1 open, 2 wide open
        self.eyes = eyes                            # 0 two ways at once, 1 crossed, 2 shut
        self.breath = breath                        # px the belly swells
        self.bloat = bloat                          # 0..1: the death's swelling
        self.shrooms = shrooms                      # glowing mushrooms sprouted on it
        self.magic = magic                          # 0 none, 1 lit, 2 bright (violet light in the near hand)


def seat(mid):
    """The floating glowing mushroom: a pale stalk, violet gills under a blue cap, three glowing spots."""
    cx, cy = SEAT_C
    mid.part(Xf(), Capsule((0.0, 0.0), (0.0, -8.0), 3.4, 4.4), "steam", lambda i: 2 if i.lx < -0.5 else 1, rust=0.0)
    mid.part(Xf(), Ellipse(cx, cy + 1.6, SEAT_R[0] - 2.0, 3.0), "aether", lambda i: 2 if (int(i.lx) % 3) else 1, rust=0.0)
    mid.part(Xf(), Ellipse(cx, cy, SEAT_R[0], SEAT_R[1]) - Poly([(-40.0, cy + 1.0), (40.0, cy + 1.0), (40.0, 9.0), (-40.0, 9.0)]),
             "denim", dome(cx - 8.0, cy - 7.0, 22.0, lo=2, hi=5, gain=1.15, fixed=True, dither=0.12), rust=0.0)
    for (x, y) in ((-23, -11), (-22, -11), (-22, -12), (-12, -14), (-11, -14), (12, -14), (13, -14), (13, -13), (23, -11), (24, -11)):
        mid.put_glow(x, y, SM[3] if (x + y) % 2 else DN[5])


def thigh(mid, at, foot, depth):
    """A folded frog leg on the seat: the green haunch and the red foot with three toes ahead of it."""
    x, y = at
    mid.part(Xf(), Ellipse(x, y, 8.5, 6.5), "cactus", dome(x - 2.0, y - 3.0, 9.0, lo=1, hi=4 - depth, gain=1.2, fixed=True), rust=0.0)
    fx, fy = foot
    mid.part(Xf(), Ellipse(fx, fy, 6.0, 2.4), "crimson", dome(fx - 1.5, fy - 1.0, 6.0, lo=2, hi=5 - depth, fixed=True), rust=0.0)
    for k in range(3):
        tx = fx - 5.4 + k * 2.2
        mid.part(Xf(), Ellipse(tx, fy + 0.6, 1.3, 1.3), "crimson", lambda i: 4 - depth, rust=0.0)


def body(mid, glow, p):
    s = 1.0 + 0.22 * p.bloat
    bx, by = BODY_C
    mid.part(Xf(), Ellipse(bx, by, BODY_R[0] * s, BODY_R[1] * s), "cactus", dome(bx - 6.0, by - 8.0, 22.0 * s, lo=1, hi=4, gain=1.25,
             fixed=True, dither=0.12), rust=0.0)
    ex, ey = BELLY_C
    r = BELLY_R[0] * s + p.breath * 0.5
    mid.part(Xf(), Ellipse(ex, ey, r, BELLY_R[1] * s + p.breath * 0.5), "sage", dome(ex - 4.0, ey - 5.0, 15.0 * s, lo=2, hi=5, gain=1.2,
             fixed=True, dither=0.12), rust=0.0)
    for k in range(3):                                           # the belly's folds
        y = int(ey + 3 + k * 3)
        for x in range(int(ex - 7 + k), int(ex + 6 - k)):
            if mid.get(x, y) in (SA[3], SA[4]) and (x + k) % 4:
                mid.put(x, y, SA[2])


def head(mid, glow, p):
    s = 1.0 + 0.12 * p.bloat
    hx, hy = HEAD_C
    for (a, m, b, r) in FRILLS:                                  # behind the head: their roots go under it
        limb(mid, a, m, r, "crimson", 0, lo=2, hi=5)
        limb(mid, m, b, r * 0.6, "crimson", 0, lo=2, hi=5)
    mid.part(Xf(), Ellipse(hx, hy, HEAD_R[0] * s, HEAD_R[1] * s), "cactus", dome(hx - 6.0, hy - 6.0, 18.0, lo=1, hi=4, gain=1.25,
             fixed=True, dither=0.12), rust=0.0)
    if p.sac > 0.0:                                              # the throat sac, swelling out in front of the chin
        r = 5.0 + 6.0 * p.sac
        mid.part(Xf(), Ellipse(hx - 5.0, hy + 7.0 + 2.0 * p.sac, r, 3.0 + 4.0 * p.sac), "ivory",
                 dome(hx - 8.0, hy + 4.0, 9.0 + 6.0 * p.sac, lo=3, hi=5, fixed=True), rust=0.0)
    # the mouth: a long dopey line, its front corner turned down; open: a red maw (a pink tongue inside)
    if p.mouth == 0:
        for x in range(int(hx - 15), int(hx + 10)):
            y = int(round(hy + 3.6 + 0.012 * (x - hx + 2) ** 2 - (1.0 if x < hx - 12 else 0.0) * -1.0))
            mid.put(x, y, CA[0])
        mid.put(int(hx - 9), int(hy + 4.6), IV[5])               # a tooth showing (dumb)
    else:
        h = 2.8 if p.mouth == 1 else 4.6
        mid.part(Xf(), Ellipse(hx - 4.0, hy + 4.2, 11.5, h), "crimson", lambda i: 1 if i.ly < hy + 3.6 else 2, rust=0.0)
        mid.part(Xf(), Ellipse(hx - 2.0, hy + 4.0 + h * 0.5, 6.0, h * 0.45), "crimson", lambda i: 4, rust=0.0, outline=False)
        for x in (int(hx - 12), int(hx - 7), int(hx + 2)):
            mid.put(x, int(hy + 4.2 - h + 1), IV[5])
    # the eyes: bulging on top, an orange ball, a slit pupil each looking its own way (crossed when the spell fails)
    for (ex, ey, r), look in ((EYE_N, (-1.6, 0.4) if p.eyes == 0 else (1.4, 0.6)), (EYE_F, (1.2, -1.4) if p.eyes == 0 else (-1.6, 0.6))):
        r *= 1.0 + 0.2 * p.bloat
        mid.part(Xf(), Ellipse(ex, ey, r + 1.2, r + 1.0), "cactus", dome(ex - 2.0, ey - 2.5, r + 3.0, lo=1, hi=4, fixed=True), rust=0.0)
        if p.eyes == 2:
            for x in range(int(ex - r + 1), int(ex + r)):
                mid.put(x, int(ey + 0.5), CA[0])                  # shut: a lid's line
            continue
        mid.part(Xf(), Ellipse(ex, ey, r, r), "ember", dome(ex - 1.8, ey - 2.2, r + 1.5, lo=1, hi=3, gain=1.4, fixed=True), rust=0.0)
        px, py = int(round(ex + look[0])), int(round(ey + look[1]))
        for dy in (-1, 0, 1):
            mid.put(px, py + dy, K[0])                            # the slit
        mid.put(px + 1, py, K[1])
        gx, gy = int(ex - r * 0.5), int(ey - r * 0.55)
        mid.put(gx, gy, SM[3])                                    # the glint
        mid.put(gx + 1, gy, SM[2])
        glow[(px + 1, py - 1)] = EM[2]


def sprouts(mid, glow, n):
    """Glowing mushrooms sprouting on it (the death): a pale stalk pixel, a blue cap that glows."""
    for k in range(min(n, len(SPROUTS))):
        x, y = SPROUTS[k]
        mid.part(Xf(), Capsule((x, y + 1.5), (x, y - 1.0), 1.0, 0.9), "steam", lambda i: 2, rust=0.0)
        mid.part(Xf(), Ellipse(x, y - 2.0, 3.4, 2.2) - Poly([(x - 5.0, y - 1.2), (x + 5.0, y - 1.2), (x + 5.0, y + 5.0), (x - 5.0, y + 5.0)]),
                 "denim", lambda i: 5 if i.lx < x - 0.5 else 4, rust=0.0)
        glow[(int(x - 1), int(y - 3))] = SM[3]
        glow[(int(x + 1), int(y - 2))] = DN[5]


def arm(cv, glow, shoulder, hand, depth, magic):
    """An arm: the green upper arm, the forearm turning red, a red hand of three long fingers spread."""
    sx, sy = shoulder
    hx, hy = hand
    ex, ey = (sx * 0.55 + hx * 0.45 + 2.0, sy * 0.55 + hy * 0.45 + 2.5)
    limb(cv, (sx, sy), (ex, ey), 2.6, "cactus", depth, lo=1, hi=4 - depth)
    limb(cv, (ex, ey), (hx, hy), 2.3, "crimson", depth, lo=2, hi=5 - depth)
    dx, dy = hx - ex, hy - ey
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    for spread in (-0.7, 0.0, 0.7):
        c, s = math.cos(spread), math.sin(spread)
        fx, fy = ux * c - uy * s, ux * s + uy * c
        tip = (hx + fx * 4.2, hy + fy * 4.2)
        limb(cv, (hx, hy), tip, 1.0, "crimson", depth, lo=3, hi=5 - depth)
        cv.part(Xf(), Ellipse(tip[0], tip[1], 1.2, 1.2), "crimson", lambda i: 4 - depth, rust=0.0)
    if magic:
        for (dx2, dy2) in ((0, -1), (-1, 0), (1, 0), (0, 1), (0, 0), (-1, -1), (1, -1)) + (((-2, -3), (2, -3), (0, -4), (-3, -1), (3, -1))
                                                                                    if magic == 2 else ()):
            glow[(int(hx + dx2), int(hy + dy2 - 1))] = SM[3] if (dx2, dy2) == (0, 0) else AE[3] if (dx2 + dy2) % 2 == 0 else AE[2]


def frame(p):
    far, mid, near = Canvas(), Canvas(), Canvas()
    glow = {}
    arm(far, glow, SHOULDER_F, p.far, 1, 0)
    finish(far)
    seat(mid)
    thigh(mid, (16.0, -17.0), (21.0, -13.0), 1)
    body(mid, glow, p)
    head(mid, glow, p)
    thigh(mid, (-16.0, -16.5), (-22.0, -12.5), 0)
    sprouts(mid, glow, p.shrooms)
    finish(mid)
    arm(near, glow, SHOULDER_N, p.near, 0, p.magic)
    finish(near)
    for q, c in glow.items():
        mid.glow[q] = c
    return far, mid, near


REST_N, REST_F = (-13.5, -21.5), (13.0, -22.5)
CAST = ((-20.0, -33.0), (-19.0, -50.0), (-30.0, -42.0), (-20.0, -28.0))
FRAMES = ([("Idle%d" % k, Pose(breath=b, eyes=2 if k == 3 else 0)) for k, b in enumerate((0, 1, 2, 1))]
          + [("Cast%d" % k, Pose(near=h, magic=(0, 2, 1, 0)[k], mouth=1 if k == 2 else 0)) for k, h in enumerate(CAST)]
          + [("Croak%d" % k, Pose(sac=s, mouth=1 if k == 2 else 0, far=(14.0, -26.0))) for k, s in enumerate((0.35, 0.85, 1.0, 0.4))]
          + [("Tongue%d" % k, Pose(mouth=m, near=(-17.0, -26.0))) for k, m in enumerate((1, 2, 1))]
          + [("Fizzle%d" % k, Pose(eyes=1, mouth=1 if k == 0 else 2, near=(-19.0, -40.0) if k == 0 else (-16.0, -30.0))) for k in range(2)]
          + [("Intro%d" % k, Pose(eyes=2 if k == 0 else 0, breath=1)) for k in range(2)]
          + [("Death%d" % k, Pose(bloat=bl, shrooms=n, eyes=1, mouth=1 if k else 0)) for k, (bl, n) in
             enumerate(((0.25, 1), (0.5, 3), (0.75, 5), (1.0, 7)))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Cast", "Croak", "Tongue", "Fizzle", "Intro", "Death")


def render_all():
    out = []
    for name, p in FRAMES:
        far, mid, near = frame(p)
        out.append((name, far, mid, near, p))
    return out


def fit_cell(frames):
    pts = [q for (_, far, mid, near, _) in frames for cv in (far, mid, near) for q in list(cv.px) + list(cv.glow)]
    xs = [x for x, y in pts if y < GROUND_CLIP]
    ys = [y for x, y in pts if y < GROUND_CLIP]
    ox = max(-min(xs), max(xs) + 1)
    return 2 * ox, GROUND_CLIP - min(ys), ox, -min(ys)


def grid(canvases, cell, glow=False):
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((w + 1) * COLUMNS, (h + 1) * rows), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        bx, by = (k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)
        for (x, y), col in src.items():
            if y >= GROUND_CLIP:
                continue
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[bx + cx, by + cy] = col + (255,)
    return out


def body_box(mid):
    """The hitbox (1x, from the origin): the seat's cap, the body and the head to the eyes' tops (not the frills' tips)."""
    xs = sorted(x for (x, y) in mid.px if y > HEAD_C[1])
    return xs[2], xs[-3] + 1, int(EYE_N[1] - EYE_N[2] - 1), 0


def write_rig(path, cell, frames):
    w, h, ox, oy = cell
    left, right, top, bottom = body_box(frames[0][2])
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def arr(name, vals):
        return "\t\tpublic static readonly short[] %s = { %s };" % (name, ", ".join(str(v) for v in vals))
    lines = [
        "// <auto-generated> by art/bosses/fungimancer/make_fungimancer_art.py - do not edit by hand. </auto-generated>",
        "namespace Cogpunk.Content.Bosses.Fungimancer",
        "{",
        "\t/// <summary>The Fungimancer's grid sheets (game px, facing left): far, middle, near and glow, equal cells in",
        "\t/// <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is under its seat's stalk. Body*: its hitbox",
        "\t/// from the origin. Per frame, from the origin, facing left: NearX/NearY the near hand (its spells leave it); Mouth: the",
        "\t/// mouth's front corner (the tongue leaves it); Throat: under the chin (the croak's ring).</summary>",
        "\tpublic static class FungimancerRigData",
        "\t{",
        "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
        % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
        "\t\tpublic const int " + ", ".join(seq[:4]) + ";",
        "\t\tpublic const int " + ", ".join(seq[4:]) + ";",
        "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, BodyBottom = %d;" % (left * 2, right * 2, top * 2, bottom * 2),
        "\t\tpublic const int MouthX = %d, MouthY = %d, ThroatX = %d, ThroatY = %d;"
        % (round(MOUTH[0] * 2), round(MOUTH[1] * 2), round((HEAD_C[0] - 4) * 2), round((HEAD_C[1] + 9) * 2)),
        arr("NearX", [round(p.near[0] * 2) for (_, _, _, _, p) in frames]),
        arr("NearY", [round((p.near[1] - 1) * 2) for (_, _, _, _, p) in frames]),
        "\t}",
        "}",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("wrote", path)


def head_icon(mid):
    hx, hy = HEAD_C
    px = {(x, y): c for (x, y), c in mid.px.items() if abs(x - hx) <= 13 and hy - 14 <= y <= hy + 8}
    xs, ys = [x for x, _ in px], [y for _, y in px]
    return to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def gores(mid):
    hy = HEAD_C[1]
    parts = {"Fungimancer_GoreHead": {q: c for q, c in mid.px.items() if q[1] <= hy + 6},
             "Fungimancer_GoreBody": {q: c for q, c in mid.px.items() if hy + 6 < q[1] <= -15},
             "Fungimancer_GoreSeat": {q: c for q, c in mid.px.items() if q[1] > -15}}
    out = {}
    for name, px in parts.items():
        xs, ys = [x for x, _ in px], [y for _, y in px]
        out[name] = to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    return out


# --- projectiles and things ------------------------------------------------------------------------------------------------
def spore_bolt():
    """A spore of violet light: a round glow (aether) round a bright core, sparkles turning round it, 4 frames, 9 px."""
    out = Image.new("RGBA", (9, 4 * 10 - 1), (0, 0, 0, 0))
    for k in range(4):
        px = {}
        for y in range(9):
            for x in range(9):
                d = math.hypot(x - 4, y - 4)
                if d <= 3.3:
                    px[(x, y)] = AE[3] if d < 1.2 else AE[2] if d < 2.4 else AE[1]
        a = k * math.pi / 2
        for (r, off) in ((4.2, 0.0), (4.2, math.pi)):
            q = (int(round(4 + r * math.cos(a + off))), int(round(4 + r * math.sin(a + off))))
            if 0 <= q[0] < 9 and 0 <= q[1] < 9:
                px[q] = DN[5]
        px[(3, 3)] = SM[3]
        for (x, y), c in px.items():
            out.putpixel((x, y + k * 10), c + (255,))
    return out


def shroom_spike():
    """A glowing mushroom bursting up out of the ground, 4 frames of 14 x 18: a bump, the stalk rising, the cap open, the cap
    with spores (it lingers that way while it hurts)."""
    out = Image.new("RGBA", (14, 4 * 19 - 1), (0, 0, 0, 0))
    for k in range(4):
        cv = Canvas()
        rise = (3.0, 8.0, 12.0, 12.0)[k]
        base = 17.5
        cv.part(Xf(), Capsule((7.0, base), (7.0, base - rise), 2.2, 1.8), "steam", lambda i: 2 if i.lx < 6.8 else 1, rust=0.0)
        if k >= 1:
            cap_w = (3.5, 6.4, 6.6)[k - 1]
            cy = base - rise - 1.0
            cv.part(Xf(), Ellipse(7.0, cy + 1.0, cap_w, 4.4 if k > 1 else 2.6) - Poly([(0.0, cy + 1.2), (14.0, cy + 1.2), (14.0, 20.0), (0.0, 20.0)]),
                    "denim", dome(5.0, cy - 2.5, 7.0, lo=2, hi=5, fixed=True), rust=0.0)
            cv.part(Xf(), Ellipse(7.0, cy + 1.0, cap_w - 0.6, 0.9), "aether", lambda i: 2, rust=0.0, outline=False)
            if k >= 2:
                for (x, y) in ((5, int(cy - 1)), (9, int(cy))):
                    cv.put(x, y, SM[3])
            if k == 3:
                for (x, y) in ((2, int(cy - 4)), (11, int(cy - 3)), (7, int(cy - 5))):
                    cv.put(x, y, AE[3])
        finish(cv)
        for (x, y), c in cv.px.items():
            if 0 <= x < 14 and 0 <= y < 18:
                out.putpixel((x, y + k * 19), c + (255,))
    return out


def tongue_tip():
    cv = Canvas()
    cv.part(Xf(), Ellipse(3.5, 3.5, 3.2, 2.8), "crimson", dome(2.6, 2.4, 3.6, lo=3, hi=5, fixed=True), rust=0.0)
    finish(cv)
    return to_image(cv.px, 0, 0, 7, 7)


def bag():
    """The treasure bag: a blue cloth sack tied with a violet cord, a glowing mushroom stitched on it."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(8.0, 10.0, 6.5, 5.6), "denim", dome(6.0, 8.0, 8.0, lo=2, hi=4, fixed=True), rust=0.0)
    cv.part(Xf(), Poly([(5.0, 3.0), (11.0, 3.0), (9.6, 5.6), (6.4, 5.6)]), "denim", lambda i: 3, rust=0.0)
    for x in range(6, 11):
        cv.put(x, 5, AE[2] if x % 2 else AE[3])
    cv.part(Xf(), Ellipse(8.0, 9.6, 2.6, 1.6), "steam", lambda i: 3 if i.lx < 8.0 else 2, rust=0.0, outline=False)
    cv.put(8, 11, SM[1])
    cv.put(8, 12, SM[1])
    finish(cv)
    return to_image(cv.px, 0, 0, 16, 16)


RAINBOW = (K[4], EM[3], RAMP["gilt"][8], CA[4], DN[5], AE[3])


def rainbow_mushroom(w, cap_rx, cap_ry, stalk_h, cx, base):
    """A glowing mushroom whose cap runs through the rainbow in bands (red at the crown to violet at the rim), a pale stalk."""
    cv = Canvas()
    cv.part(Xf(), Capsule((cx, base), (cx, base - stalk_h), 1.3, 1.1), "steam", lambda i: 2 if i.lx < cx - 0.2 else 1, rust=0.0)
    top = base - stalk_h - 0.6
    shape = Ellipse(cx, top, cap_rx, cap_ry) - Poly([(-5.0, top + 0.8), (w + 5.0, top + 0.8), (w + 5.0, base + 5.0), (-5.0, base + 5.0)])
    cv.part(Xf(), shape, "steam", lambda i: 3, rust=0.0)
    for (x, y), _ in list(cv.px.items()):
        dx, dy = (x + 0.5 - cx) / cap_rx, (y + 0.5 - top) / max(cap_ry, 0.1)
        if dy <= 0.2 and dx * dx + dy * dy <= 1.0:
            r = math.sqrt(dx * dx + dy * dy)
            band = min(len(RAINBOW) - 1, int(r * len(RAINBOW)))
            edge = any((x + ox, y + oy) not in cv.px for ox, oy in ((1, 0), (-1, 0), (0, -1)))
            cv.px[(x, y)] = RAMP["plum"][0] if edge else RAINBOW[band]
    return cv


def tile_sheet():
    """Three rainbow mushrooms (1 x 1 tile each, 8 x 8 at 1x, 9 px apart: 18 at 2x) of different heights."""
    out = Image.new("RGBA", (27, 9), (0, 0, 0, 0))
    for k, (rx, ry, sh) in enumerate(((3.4, 2.6, 2.6), (3.0, 2.4, 3.6), (3.6, 2.8, 2.0))):
        cv = rainbow_mushroom(8, rx, ry, sh, 3.8, 7.6)
        for (x, y), c in cv.px.items():
            if 0 <= x < 8 and 0 <= y < 8:
                out.putpixel((x + k * 9, y), c + (255,))
    return out


def summon_item():
    cv = rainbow_mushroom(14, 6.0, 4.6, 5.0, 7.0, 13.0)
    return to_image(cv.px, 0, 0, 14, 14)


def export_all():
    frames = render_all()
    cell = fit_cell(frames)
    for key, idx, glow in (("", 2, False), ("_Far", 1, False), ("_Near", 3, False), ("_Glow", 2, True)):
        export(grid([fr[idx] for fr in frames], cell, glow), OUT + "Fungimancer%s.png" % key)
    write_rig(OUT + "FungimancerRigData.cs", cell, frames)
    export(head_icon(frames[0][2]), OUT + "Fungimancer_Head_Boss.png")
    for name, im in gores(frames[INDEX["Death3"]][2]).items():
        export(im, OUT + "Gores/" + name + ".png")
    export(spore_bolt(), OUT + "Projectiles/SporeBolt.png")
    export(shroom_spike(), OUT + "Projectiles/ShroomSpike.png")
    export(tongue_tip(), OUT + "Projectiles/FungimancerTongue.png")
    export(bag(), OUT + "Items/FungimancerBag.png")
    export(summon_item(), OUT + "Items/RainbowMushroom.png")
    export(tile_sheet(), OUT + "Tiles/RainbowMushroomTile.png")
    print("cell (1x) %dx%d, origin %d,%d" % cell)
    return frames, cell


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    frames, cell = export_all()
    if args.preview:
        w, h, ox, oy = cell
        sc = 3
        n = len(frames)
        sheet = Image.new("RGBA", (w * 2 * sc * 6 + 70, (h * 2 * sc + 10) * ((n + 5) // 6) + 10), (24, 24, 30, 255))
        for k, (name, far, mid, near, p) in enumerate(frames):
            im = Image.new("RGBA", (w, h), (36, 44, 72, 255))
            for cv, glow in ((far, False), (mid, False), (near, False), (mid, True)):
                for (x, y), c in (cv.glow if glow else cv.px).items():
                    if y < GROUND_CLIP and 0 <= x + ox < w and 0 <= y + oy < h:
                        im.putpixel((x + ox, y + oy), c + (255,))
            big = im.resize((w * 2 * sc, h * 2 * sc), Image.NEAREST)
            sheet.alpha_composite(big, (10 + (k % 6) * (w * 2 * sc + 10), 10 + (k // 6) * (h * 2 * sc + 10)))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
