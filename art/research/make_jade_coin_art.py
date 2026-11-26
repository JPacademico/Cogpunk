"""Source for the Jade Coin summon (D4), 2026-11-24 (user: "a new summon weapon called "jade coin" using a platinum coin +
8 jades. it should summon a jade bat and if used again instead off summoning another bat it should evolve the bat into a
jade beetle and then into a jade golem and then into a jade loong (like defalult terraria cloud hard mode loong, but
smaller and jade colored)"). Run from the repo root:

    python -P art/research/make_jade_coin_art.py [--coin] [--preview FILE]

The bat, the beetle and the golem are Jadey's and Coghaven's own jade creatures (their sheets are drawn as they are). New
here:

* the JADE LOONG: a small serpentine dragon of jade (a long scaled body, a horned and maned head with gold whiskers, two
  pairs of clawed legs, a tail ending in a flame-shaped tuft), in four segment kinds (head, body, body with legs, tail).
  It turns freely as it flies, so every segment is rendered at HEADINGS headings by the sculpt renderer (D4 rule 14: never
  rotated at runtime), each heading modelled in its own pose: the parts' frames turn, the light stays top-left, the
  checker dither stays in the parts' own space. A segment heading left is modelled mirrored, so its back stays up (as
  vanilla's worms flip). Its eye glows (the _Glow sheet).
* the JADE COIN (the item), redrawn 2026-11-25 from the user's example ("perform a design rework for the jade coin sprite
  so it looks more like this prompt picture example coin (remove the green effect arround it if necessary)"): a ring of
  carved jade blocks round a recessed jade disc that carries a raised leaf (a pointed leaf with a dark midrib and a leaf
  curling up either side of its stem), in the emerald ramp; the example's green aura and motes are left out. The design
  before it (a jade disc in a platinum rim with a square hole) is kept in previous/make_jade_coin_art_2026-11-24.py.
* the buff icon: the same coin at 16 px.
* the SPIRIT'S COIN (2026-11-26, the user: "the jade coin summons should be a floaty jade coin above the player while theres
  no enemies to target, and transform (smooth quick tranform animation) when theres enemies in range"): the buff icon's coin
  turning about its upright axis in eight frames (front, three-quarter, edge, three-quarter back, back ...): the turned faces
  are the front's own columns, picked evenly (the rims stay on the edges: no new colours, no mixels), the back mirrored, the
  edge a lit rim of jade; and the BURST that covers the change: a jade star whose rays grow into a ring of sparks and scatter,
  five frames (no outline: it is light).

Outputs (Content/Research/Summons/):
    JadeLoong.png        the segments: HEADINGS columns (heading k points k x 360/HEADINGS degrees clockwise from right),
                         4 rows (head, body, legs, tail); cells CELL x CELL art px (2x in game) with 1 art px between
    JadeLoong_Glow.png   the same layout: the eyes
    JadeCoin.png         the item (20x20 art, 40x40 in game)
    JadeCoinBuff.png     the buff icon (16x16 art)
    JadeSpirit_Coin.png  the spirit's coin turning: 8 frames of 16 x 16 art stacked, 1 art px under each
    JadeSpirit_Burst.png the change's burst: 5 frames of 24 x 24 art stacked, 1 art px under each
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from sculpt import Ell, Frame, Part, Poly, Tube, render  # noqa: E402
from pixkit import Pix, export, sheet  # noqa: E402
from rig import RAMP  # noqa: E402

OUT = "Content/Research/Summons/"
HEADINGS = 32
CELL = 30                              # art px; the origin at its middle (32 x 31 art px stay under the 2048 px texture limit)
HEAD = 1.2                             # the head is modelled at this size over the body's scale
SPACING = 8                            # art px between segment centres in game (JadeSpirit.LoongSpacing / 2)
STRIDE = CELL + 1
KINDS = ("head", "body", "legs", "tail")
JADE, EMERALD, GILT, STEEL = RAMP["ghost"], RAMP["emerald"], RAMP["gilt"], RAMP["steel"]
STEAM = RAMP["steam"]
COIN = EMERALD                         # the coin: the bright green of the user's example (2026-11-25)
EYE = GILT[7]                          # warm gold: stands out of the jade (whose light end is near white)


def m(points, mirror):
    return [(x, -y if mirror else y) for (x, y) in points]


def segment_parts(kind, angle, mirror):
    """The parts of one segment kind at `angle` (radians, clockwise from right on screen), mirrored across its own axis
    when heading left. Local frame: +x forward, -y its back (up when it heads right)."""
    f = Frame(0.0, 0.0, angle)
    s = -1.0 if mirror else 1.0

    k = HEAD if kind == "head" else 1.0

    def ell(cx, cy, rx, ry, flat=0.0):
        return Ell(cx * k, cy * s * k, rx * k, ry * k, flat)

    def tube(pts, radii):
        return Tube(m([(x * k, y * k) for (x, y) in pts], mirror), [r * k for r in radii])

    def poly(pts):
        return Poly(m([(x * k, y * k) for (x, y) in pts], mirror))

    def bumps(lst):
        return tuple((x * k, y * s * k, r * k) for (x, y, r) in lst)

    def line(pts):
        return m([(x * k, y * k) for (x, y) in pts], mirror)

    parts = []
    if kind == "head":
        # a loong's head in profile: a long muzzle with an upturned nose, a brow over the eye, gold antlers swept back, a
        # flowing mane behind, a gold barbel trailing from the lip
        parts.append(Part("horn_far", tube([(-0.4, -3.4), (-4.0, -6.6), (-7.6, -7.4)], [1.0, 0.8, 0.5]), GILT, 0, f, lo=3, hi=6,
                          dither=0.0))
        parts.append(Part("mane", poly([(-2.6, -3.8), (-10.0, -3.6), (-6.6, -1.6), (-11.0, 0.4), (-7.0, 1.4), (-9.6, 3.8),
                                        (-3.4, 3.0)]), EMERALD, 1, f, lo=1, hi=4, dither=0.0))
        parts.append(Part("jaw", ell(3.6, 2.4, 4.6, 1.2, 0.3), JADE, 2, f, lo=2, hi=5))
        parts.append(Part("skull", ell(-0.8, -0.6, 4.2, 3.8), JADE, 3, f, lo=1, hi=5,
                          bumps=bumps([(-2.2, -2.2, 1.3), (0.6, -2.8, 1.0)])))
        parts.append(Part("snout", ell(4.6, 0.0, 4.8, 2.2), JADE, 4, f, lo=1, hi=5,
                          lines=[line([(2.6, 1.7), (8.6, 1.1)])]))
        parts.append(Part("nose", ell(8.6, -0.8, 1.5, 1.5), JADE, 5, f, lo=2, hi=5))
        parts.append(Part("horn", tube([(-1.2, -2.8), (-5.0, -5.6), (-9.4, -6.0)], [1.2, 0.9, 0.6]), GILT, 6, f, lo=4, hi=8,
                          dither=0.0))
        parts.append(Part("tine", tube([(-4.4, -5.4), (-5.2, -8.4)], [0.7, 0.5]), GILT, 6, f, lo=4, hi=8, dither=0.0))
        parts.append(Part("whisker", tube([(8.2, 1.0), (5.0, 3.6), (0.8, 4.4), (-3.0, 5.8)], [0.6, 0.55, 0.5, 0.45]), GILT, 7, f,
                          lo=5, hi=8, dither=0.0, outline=False))
    elif kind in ("body", "legs"):
        parts.append(Part("fin", poly([(-3.4, -3.4), (-1.4, -6.8), (1.8, -3.6)]), GILT, 0, f, lo=3, hi=7, dither=0.0))
        if kind == "legs":
            parts.append(Part("leg_far", tube([(1.6, 2.4), (0.0, 5.4), (1.4, 7.6)], [1.3, 1.0, 0.8]), JADE, 1, f, lo=1, hi=3))
        parts.append(Part("trunk", tube([(-6.4, 0.0), (6.4, 0.0)], [4.4, 4.4]), JADE, 2, f, lo=1, hi=5,
                          bumps=bumps([(-3.2, -1.2, 1.3), (0.0, -1.6, 1.3), (3.2, -1.2, 1.3), (-1.6, 0.9, 1.2), (1.6, 0.9, 1.2)])))
        parts.append(Part("belly", ell(0.0, 2.9, 5.8, 1.6, 0.5), JADE, 3, f, lo=3, hi=5,
                          lines=[m([(-2.0, 2.0), (-2.0, 4.0)], mirror), m([(2.0, 2.0), (2.0, 4.0)], mirror)]))
        if kind == "legs":
            parts.append(Part("leg", tube([(-0.6, 2.6), (-2.6, 5.6), (-1.0, 8.0)], [1.5, 1.1, 0.9]), JADE, 4, f, lo=1, hi=5))
            parts.append(Part("claw", poly([(-2.2, 7.6), (1.6, 7.8), (0.6, 9.4), (-1.4, 9.0)]), GILT, 5, f, lo=3, hi=7,
                              dither=0.0))
    else:  # tail
        parts.append(Part("tuft", poly([(-3.4, -0.6), (-9.6, -3.8), (-7.6, -0.2), (-10.6, 2.6), (-4.8, 2.2)]), GILT, 0, f,
                          lo=3, hi=7, dither=0.0))
        parts.append(Part("fin", poly([(-0.6, -2.4), (1.0, -5.0), (3.2, -2.6)]), GILT, 1, f, lo=2, hi=6, dither=0.0))
        parts.append(Part("tail", tube([(6.4, 0.0), (-1.4, 0.3), (-5.4, 0.7)], [4.4, 2.6, 1.0]), JADE, 2, f, lo=1, hi=5,
                          bumps=bumps([(1.6, -1.2, 1.2), (-1.4, -0.8, 1.0)])))
    return parts


EYE_AT = ((1.0, -1.5), (1.9, -1.5))        # the head's eye (two pixels along the muzzle), in its local frame before HEAD
BROW_AT = (1.4, -2.6)                      # the brow's shadow over it


def render_segment(kind, k):
    angle = k * 2.0 * math.pi / HEADINGS
    mirror = math.cos(angle) < -1e-6 or (abs(math.cos(angle)) <= 1e-6 and math.sin(angle) < 0)
    parts = segment_parts(kind, angle, mirror)
    o = CELL / 2.0
    px, glow, owner = render(parts, CELL, CELL, o, o)
    if kind == "head":                     # the eye: stamped after the outline, glowing gold, a brow's shadow over it
        frame = Frame(0.0, 0.0, angle)

        def at(lx, ly):
            ly = -ly if mirror else ly
            wx, wy = frame.to_world(lx * HEAD, ly * HEAD)
            return int(math.floor(wx + o)), int(math.floor(wy + o))

        b = at(*BROW_AT)
        if b in px:
            px[b] = JADE[0]
        for e in EYE_AT:
            q = at(*e)
            if q in px:
                px[q] = EYE
                glow[q] = EYE
    return px, glow


def to_image(px, w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    data = img.load()
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            data[x, y] = tuple(c) + (255,)
    return img


def loong_sheets():
    sheet = Image.new("RGBA", (HEADINGS * STRIDE, len(KINDS) * STRIDE), (0, 0, 0, 0))
    glow = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    for row, kind in enumerate(KINDS):
        for k in range(HEADINGS):
            px, gl = render_segment(kind, k)
            sheet.alpha_composite(to_image(px, CELL, CELL), (k * STRIDE, row * STRIDE))
            glow.alpha_composite(to_image(gl, CELL, CELL), (k * STRIDE, row * STRIDE))
    return sheet, glow


def coin_tones(n, ring_in, disc, seams, outer_at):
    """The coin's tones before its emblem: a ring of jade blocks (a raised half-round, so the outer row is lit at the
    top-left and the inner row at the bottom-right) split by one-pixel seams, a dark groove, and a recessed disc whose
    top-left rim lies in the lip's shadow and whose bottom-right rim catches the light. A dict (x, y) -> tone."""
    c, R = n / 2, n / 2
    cells = {}
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            d = math.hypot(dx, dy)
            if d <= R:
                cells[(x, y)] = (dx, dy, d)
    edge = {q for q in cells if any((q[0] + a, q[1] + b) not in cells for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    tone = {}
    for (x, y), (dx, dy, d) in cells.items():
        face = (-dx - dy) / (math.sqrt(2) * d)             # +1 facing the light (top-left)
        if d > ring_in:
            if (x, y) in seams and (x, y) not in edge:     # seams never cut the outline
                tone[(x, y)] = 1
            elif (x, y) in edge:
                tone[(x, y)] = 4                           # the outline pass recolours it
            elif face > 0.35:
                tone[(x, y)] = 5 if d > outer_at else 3
            elif face < -0.35:
                tone[(x, y)] = 3 if d > outer_at else 5
            else:
                tone[(x, y)] = 4
        elif d > disc:
            tone[(x, y)] = 0                               # the groove
        else:
            tone[(x, y)] = 2                               # the disc
    for (x, y), t in list(tone.items()):
        dx, dy, d = cells[(x, y)]
        if t == 2 and any(tone.get((x + a, y + b)) == 0 and cells[(x + a, y + b)][2] > disc
                          for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            face = (-dx - dy) / (math.sqrt(2) * max(d, 0.01))
            tone[(x, y)] = 1 if face > 0.75 else 3 if face < -0.6 else 2
    return tone


def coin(n, ring_in, disc, seams, outer_at, emblem):
    """The coin at n x n art px: its tones, the selective outline, then the raised emblem (stamped after the outline,
    one ramp step per tone digit) casting a one-pixel shadow down and right onto the disc."""
    tone = coin_tones(n, ring_in, disc, seams, outer_at)
    p = Pix(n, n)
    for (x, y), t in tone.items():
        p.put(x, y, COIN, t)
    p.outline()
    raised = set()
    for y, row in enumerate(emblem):
        for x, ch in enumerate(row):
            if ch.isdigit():
                p.put(x, y, COIN, int(ch), lock=True)
                raised.add((x, y))
    for (x, y) in raised:
        for (a, b) in ((1, 0), (0, 1), (1, 1)):
            q = (x + a, y + b)
            if q not in raised and tone.get(q) == 2:
                p.put(q[0], q[1], COIN, 1, lock=True)
    return p


# The emblem (the user's example, 2026-11-25): a pointed jade leaf, lit on its left half, a dark midrib, and a leaf curling
# up on either side of its stem. Digits are emerald ramp steps; '.' leaves the coin as it is.
EMBLEM_ITEM = [
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "............6.......",
    "...........654......",
    "..........6244......",
    ".........65244......",
    ".....6..65244.5.....",
    ".....65.55244.5.....",
    ".....55.5244.44.....",
    "......54524.44......",
    ".......44444........",
]
SEAMS_ITEM = {(11, 1), (11, 2), (14, 4), (15, 4), (16, 4), (17, 8), (18, 8), (15, 14), (16, 14), (17, 14),
              (10, 17), (10, 18), (5, 15), (5, 16), (5, 17), (1, 10), (2, 10), (5, 2), (5, 3), (5, 4)}
EMBLEM_BUFF = [
    "................",
    "................",
    "................",
    "................",
    ".........6......",
    "........654.....",
    ".......6524.....",
    "....6.6524.5....",
    "....5.5524.4....",
    "....5.524.4.....",
    ".....44444......",
]
SEAMS_BUFF = {(9, 1), (9, 2), (12, 4), (13, 4), (13, 8), (14, 8), (11, 12), (11, 13), (6, 13), (6, 14),
              (2, 11), (3, 11), (1, 6), (2, 6), (4, 2), (4, 3)}


def item_icon():
    """20 x 20 art (40 x 40 in game): ten blocks of varied length round the disc."""
    return coin(20, 7.0, 5.9, SEAMS_ITEM, 8.0, EMBLEM_ITEM).image()


def buff_icon():
    """16 x 16 art (the 32 x 32 buff icon): the same coin, eight blocks."""
    return coin(16, 5.4, 4.4, SEAMS_BUFF, 6.3, EMBLEM_BUFF).image()


SPIN = (16, 11, 3, -11, -16, -11, 3, 11)                # the turning coin's widths: negative = its back (mirrored)


def squeeze(face, width):
    """The coin's face seen turned: `width` of its columns, picked evenly so the first and last are its rims."""
    w, h = face.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x0 = (w - width) // 2
    for j in range(width):
        src = int(round(j * (w - 1) / max(1, width - 1)))
        out.paste(face.crop((src, 0, src + 1, h)), (x0 + j, 0))
    return out


def edge_on(n=16):
    """The coin seen edge on: three columns of its rim (dark, lit jade, mid), rounded at the ends."""
    p = Pix(n, n)
    x = n // 2 - 1
    for y in range(1, n - 1):
        p.put(x, y, COIN, 2)
        p.put(x + 1, y, COIN, 4 if y < n // 2 else 3)
        p.put(x + 2, y, COIN, 2)
    p.outline()
    p.put(x + 1, 3, COIN, 6, lock=True)                   # the rim's glint (top-left light)
    return p.image()


def spirit_coin_sheet():
    face = buff_icon()
    frames = []
    for w in SPIN:
        if abs(w) <= 3:
            frames.append(edge_on())
        elif w > 0:
            frames.append(squeeze(face, w))
        else:
            frames.append(squeeze(face.transpose(Image.FLIP_LEFT_RIGHT), -w))
    return sheet(frames)


def burst_frame(k, n=24):
    """The change's burst, frame k of 5: a star (k 0), its rays out to a ring (1), a broken ring of sparks (2), scattering
    (3), the last motes (4). Emerald's light end and white; no outline."""
    p = Pix(n, n)
    c = n / 2 - 0.5
    radius = (2, 5, 8, 10, 11)[k]
    if k <= 1:
        ray = (6, 9)[k]
        for d in range(0, ray + 1):                        # the four long rays, thinning
            tone = 6 if d <= 1 else 5 if d <= ray // 2 else 4
            for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p.put(int(c + 0.5 + a * d), int(c + 0.5 + b * d), COIN, tone)
        for d in range(1, (3, 5)[k]):                      # the short diagonals
            for (a, b) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                p.put(int(c + 0.5 + a * d), int(c + 0.5 + b * d), COIN, 5 if d == 1 else 4)
        p.put(int(c + 0.5), int(c + 0.5), STEAM, 3)
        if k == 0:
            for (a, b) in ((1, 0), (0, 1), (1, 1)):
                p.put(int(c + 0.5) + a, int(c + 0.5) + b, STEAM, 2)
    if k >= 1:
        count = (0, 16, 12, 8, 6)[k]
        for i in range(count):
            ang = i * 2 * math.pi / count + k * 0.3
            x, y = int(round(c + math.cos(ang) * radius)), int(round(c + math.sin(ang) * radius))
            tone = (6, 6, 5, 4, 3)[k]
            p.put(x, y, COIN, tone)
            if k <= 2:                                     # the near sparks are two pixels long, along the ring
                p.put(x + (1 if math.sin(ang) < 0 else -1), y, COIN, tone - 1)
    return p.image()


def spirit_burst_sheet():
    return sheet([burst_frame(k) for k in range(5)])


def export_coin():
    export(item_icon(), OUT + "JadeCoin.png")
    export(buff_icon(), OUT + "JadeCoinBuff.png")
    export(spirit_coin_sheet(), OUT + "JadeSpirit_Coin.png")
    export(spirit_burst_sheet(), OUT + "JadeSpirit_Burst.png")


def export_all():
    sheet, glow = loong_sheets()
    export(sheet, OUT + "JadeLoong.png")
    export(glow, OUT + "JadeLoong_Glow.png")
    export_coin()


def preview(path):
    """The loong laid along a curve at 4x over dark and light, a heading wheel of every segment, the coin and the icon."""
    sheet, _ = loong_sheets()
    cells = {(row, k): sheet.crop((k * STRIDE, row * STRIDE, k * STRIDE + CELL, row * STRIDE + CELL))
             for row in range(len(KINDS)) for k in range(HEADINGS)}
    W, H = 150, 70
    bgs = ((30, 30, 36), (196, 214, 232))
    out = Image.new("RGBA", (W * 4, H * 4 * len(bgs) + 4 * (len(KINDS) * STRIDE + 4) + 80), (20, 20, 24, 255))
    for bi, bg in enumerate(bgs):
        scene = Image.new("RGBA", (W, H), bg + (255,))
        # a serpent along a sine curve: the head at the right
        pts = [(118.0, 30.0)]
        t = 0.0
        while len(pts) < 9:                                # walk a sine curve SPACING px at a time, as the game spaces them
            t += 0.02
            q = (118.0 - t * 40.0, 30.0 + 14.0 * math.sin(t * 2.4))
            if math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) >= SPACING:
                pts.append(q)
        for i in range(len(pts) - 1, -1, -1):
            if i == 0:
                kind = 0
            elif i == len(pts) - 1:
                kind = 3
            else:
                kind = 2 if i in (2, 5) else 1
            a = pts[i - 1] if i > 0 else (pts[0][0] + (pts[0][0] - pts[1][0]), pts[0][1] + (pts[0][1] - pts[1][1]))
            b = pts[i]
            ang = math.atan2(a[1] - b[1], a[0] - b[0]) % (2 * math.pi)
            k = int(round(ang / (2 * math.pi / HEADINGS))) % HEADINGS
            scene.alpha_composite(cells[(kind, k)], (int(b[0] - CELL / 2), int(b[1] - CELL / 2)))
        out.alpha_composite(scene.resize((W * 4, H * 4), Image.NEAREST), (0, bi * H * 4))
    y0 = H * 4 * len(bgs) + 4
    big = sheet
    out.alpha_composite(big.crop((0, 0, min(big.width, W * 4), big.height)), (0, y0))
    out.alpha_composite(item_icon().resize((64, 64), Image.NEAREST), (8, out.height - 72))
    out.alpha_composite(buff_icon().resize((64, 64), Image.NEAREST), (80, out.height - 72))
    out.save(path)
    print("wrote", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--coin", action="store_true", help="export only the coin and its buff icon")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    elif a.coin:
        export_coin()
    else:
        export_all()
