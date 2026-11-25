"""Source for the Jade Coin summon (D4), 2026-11-24 (user: "a new summon weapon called "jade coin" using a platinum coin +
8 jades. it should summon a jade bat and if used again instead off summoning another bat it should evolve the bat into a
jade beetle and then into a jade golem and then into a jade loong (like defalult terraria cloud hard mode loong, but
smaller and jade colored)"). Run from the repo root:

    python -P art/research/make_jade_coin_art.py [--preview FILE]

The bat, the beetle and the golem are Jadey's and Coghaven's own jade creatures (their sheets are drawn as they are). New
here:

* the JADE LOONG: a small serpentine dragon of jade (a long scaled body, a horned and maned head with gold whiskers, two
  pairs of clawed legs, a tail ending in a flame-shaped tuft), in four segment kinds (head, body, body with legs, tail).
  It turns freely as it flies, so every segment is rendered at HEADINGS headings by the sculpt renderer (D4 rule 14: never
  rotated at runtime), each heading modelled in its own pose: the parts' frames turn, the light stays top-left, the
  checker dither stays in the parts' own space. A segment heading left is modelled mirrored, so its back stays up (as
  vanilla's worms flip). Its eye glows (the _Glow sheet).
* the JADE COIN (the item): a jade disc in a platinum rim with a square hole, as old cash coins are, four gold marks round
  the hole.
* the buff icon: the coin with a jade wisp curling out of it.

Outputs (Content/Research/Summons/):
    JadeLoong.png        the segments: HEADINGS columns (heading k points k x 360/HEADINGS degrees clockwise from right),
                         4 rows (head, body, legs, tail); cells CELL x CELL art px (2x in game) with 1 art px between
    JadeLoong_Glow.png   the same layout: the eyes
    JadeCoin.png         the item (16x16 art)
    JadeCoinBuff.png     the buff icon (16x16 art)
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
from pixkit import Pix, export  # noqa: E402
from rig import RAMP  # noqa: E402

OUT = "Content/Research/Summons/"
HEADINGS = 32
CELL = 30                              # art px; the origin at its middle (32 x 31 art px stay under the 2048 px texture limit)
HEAD = 1.2                             # the head is modelled at this size over the body's scale
SPACING = 8                            # art px between segment centres in game (JadeSpirit.LoongSpacing / 2)
STRIDE = CELL + 1
KINDS = ("head", "body", "legs", "tail")
JADE, EMERALD, GILT, STEEL = RAMP["ghost"], RAMP["emerald"], RAMP["gilt"], RAMP["steel"]
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


def coin(p, cx, cy, r):
    """A jade disc in a platinum rim, a square hole, four gold marks round it; lit from the top-left."""
    for y in range(p.h):
        for x in range(p.w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            if abs(dx) < 1.0 and abs(dy) < 1.0:
                continue                                   # the hole
            lit = -(dx + dy) / (r * 1.41)                  # +1 at the top-left edge
            if d > r - 1.3:                                # the rim: platinum
                p.put(x, y, STEEL, 6 + round(lit * 2))
            elif abs(dx) < 2.0 and abs(dy) < 2.0:          # the hole's gold lip (lit on its far side: it is a hollow)
                p.put(x, y, GILT, 6 + round(-lit * 1.5))
            else:
                p.put(x, y, JADE, 3 + round(lit * 1.4))
    p.outline()
    for (x, y) in ((cx - 0.5, cy - 4.5), (cx - 0.5, cy + 3.5), (cx - 4.5, cy - 0.5), (cx + 3.5, cy - 0.5)):
        p.put(int(x), int(y), GILT, 7, lock=True)          # four marks
    p.put(int(cx - r * 0.55), int(cy - r * 0.6), JADE, 5, lock=True)   # a glint


def item_icon():
    p = Pix(16, 16)
    coin(p, 8.0, 8.0, 7.2)
    return p.image()


def buff_icon():
    p = Pix(16, 16)
    coin(p, 6.5, 9.5, 5.6)
    for (x, y, i) in ((10, 8, 3), (11, 7, 4), (12, 6, 4), (12, 5, 5), (11, 4, 4), (10, 3, 3), (12, 3, 2), (13, 4, 3)):
        p.put(x, y, JADE, i, lock=True)                    # a jade wisp curling up out of it
    p.put(13, 2, GILT, 8, lock=True)                       # its spark
    return p.image()


def export_all():
    sheet, glow = loong_sheets()
    export(sheet, OUT + "JadeLoong.png")
    export(glow, OUT + "JadeLoong_Glow.png")
    export(item_icon(), OUT + "JadeCoin.png")
    export(buff_icon(), OUT + "JadeCoinBuff.png")


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
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
