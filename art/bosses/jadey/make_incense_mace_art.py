"""The Incense Mace's art (2026-11-18). Run from the repo root:

    python -P art/bosses/jadey/make_incense_mace_art.py [--preview FILE]

User, 2026-11-18: "add a new weapon to Jadey weapon pool called "Incense mace" ... the base art of the weapon is on the image
prompt" (reference/incense_mace_user_2026-11-18.jpg: a gilt censer pierced with crosses on a gilt chain from a turned wooden
handle with a gilt pommel). The reference is upscaled pixel art (21 px a pixel); user_art.py reads it on its own grid, puts it
in the palette (gilt, oak, hide, steel); shrunk by area its 2 px links and pierced crosses blurred away, so the weapon is
redrawn here pixel by pixel at sprite size after it (the layout, the materials and their colours are the user's):
  * IncenseMace.png: the whole weapon as the user drew it (the item): the oak handle and gilt pommel, the arching chain, the
    censer hanging from it.
  * IncenseMaceHead.png: the censer alone (the flail's head), with its hanger ring.
  * IncenseMaceChain.png: one gilt link of its chain (drawn here: 4 x 6 px, a ring lit from the top-left), drawn along the
    chain in game.
  * IncenseAura.png: the aura's smoke puff, 4 frames of 8 x 8 px (curling up, full, thinning, a wisp), pale incense
    (Steam and Aether), placed round the ring in game (never scaled or turned).
  * Buffs/IncenseBlessing.png and Buffs/IncenseBurntOut.png: the censer with its smoke rising; burnt out, dark, a thread of
    grey smoke.
Drawn at 1x in the Cogpunk palette, exported 2x (D4).
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
import user_art  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Bosses/Jadey/"
REF = "art/bosses/jadey/reference/incense_mace_user_2026-11-18.jpg"
GRID = (21.0, 2.0, 20.0)                           # the reference's pixel and its first pixel's offset (measured)
BACKDROP = (182, 206, 230)
ICON_SCALE = 1.75
HEAD_SCALE = 1.3
HEAD_BOX = (31, 16, 51, 39)                        # the censer and its hanger on the reference's grid (x0, y0, x1, y1)
G, OK, HI, ST, SM, AE = (RAMP[k] for k in ("gilt", "oak", "hide", "steel", "steam", "aether"))


def reference():
    rows = user_art.native(REF, GRID)
    return user_art.to_palette(rows, G + OK + HI + ST, BACKDROP, clear_dist=12.0)


def keep():
    return {G[0]: 1.4, G[1]: 1.25, OK[0]: 1.3, ST[0]: 1.3, G[8]: 1.2, G[9]: 1.2}


LIGHT = (-0.5, -0.62, 0.6)


def _norm(v):
    n = sum(c * c for c in v) ** 0.5 or 1.0
    return tuple(c / n for c in v)


def censer(px, cx, cy, r, cross_dx):
    """The user's censer redrawn at sprite size (shrunk, its piercings blurred away): a gilt sphere lit from the top-left
    (G2 shadow .. G8 glint), a darker seam round its middle where its halves meet, a cross pierced either side of the seam's
    centre (dark, a shade lit on their upper-left lip), the lit-side rim a step lighter, the shadow side's outline G0."""
    L = _norm(LIGHT)
    body = set()
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / (r * 0.94)
            d2 = dx * dx + dy * dy
            if d2 > 1.0:
                continue
            body.add((x, y))
            nz = (1.0 - d2) ** 0.5
            i = dx * L[0] + dy * L[1] + nz * L[2]
            k = max(2, min(8, int(round(2.0 + 7.0 * max(0.0, i)))))
            px[(x, y)] = G[k]
    for (x, y) in body:
        edge = any((x + ex, y + ey) not in body for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            lit = (x + 0.5 - cx) + (y + 0.5 - cy) < -r * 0.3
            px[(x, y)] = G[3] if lit else G[0]
    seam = int(round(cy))
    for x in range(int(cx - r), int(cx + r) + 1):
        if (x, seam) in body and (x, seam) in px and px[(x, seam)] not in (G[0], G[3]):
            k = G.index(px[(x, seam)])
            px[(x, seam)] = G[max(1, k - 2)]
    for side in (-1, 1):
        ox, oy = int(round(cx + side * cross_dx - 0.5)), seam - 2
        for (dx, dy) in ((0, 0), (0, 1), (-1, 1), (1, 1), (0, 2)):
            if (ox + dx, oy + dy) in body:
                px[(ox + dx, oy + dy)] = G[0]
        if (ox - 1, oy) in body:
            px[(ox - 1, oy)] = G[4]
    return body


def icon(pix=None):
    """The whole weapon as the user drew it, at sprite size: the oak handle up from its gilt pommel to a gilt collar, the
    chain arching over to the censer's hanger, the censer hanging to the right."""
    px = {}
    # the handle: a 3 px rod of turned oak, lit on its upper-left side, rings of darker grain
    a, b = (4.0, 25.0), (9.0, 12.0)
    steps = 40
    for s_ in range(steps + 1):
        t = s_ / steps
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for w in (-1, 0, 1):
            q = (int(round(x + w)), int(round(y)))
            ring = int(t * 13) % 3 == 0
            px[q] = OK[0] if w == 1 else (OK[2] if ring else OK[4]) if w == -1 else (OK[1] if ring else OK[3])
    for (x, y, c) in ((3, 25, G[7]), (4, 25, G[6]), (5, 25, G[4]), (3, 26, G[5]), (4, 26, G[4]), (5, 26, G[2]), (4, 27, ST[5]),
                      (3, 27, ST[6]), (5, 27, ST[3]), (2, 26, G[1]), (6, 26, G[1]), (4, 28, G[1])):
        px[(x, y)] = c                                           # the pommel
    for (x, y, c) in ((8, 11, G[7]), (9, 11, G[6]), (10, 11, G[4]), (8, 12, G[5]), (10, 12, G[3]), (9, 10, G[5])):
        px[(x, y)] = c                                           # the collar
    # the chain: a quadratic arc from the collar over to the hanger, links two px long (a lit link, a dark joint)
    p0, p1, p2 = (9.0, 9.5), (14.0, -3.0), (21.0, 8.0)
    n = 34
    last = None
    for k in range(n + 1):
        t = k / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        q = (int(round(x)), int(round(y)))
        if q == last:
            continue
        last = q
        j = len([1 for _ in range(k)]) // 2
        px[q] = G[7] if (q[0] + q[1]) % 3 else G[2]
        if (q[0], q[1] + 1) not in px:
            px[(q[0], q[1] + 1)] = G[1]
    censer(px, 21.5, 15.5, 6.2, 2.6)
    for (x, y, c) in ((21, 8, G[6]), (20, 9, G[7]), (22, 9, G[4]), (21, 9, G[2])):
        px[(x, y)] = c                                           # the censer's cap and hanger
    return px


def head(pix=None):
    """The censer alone (the flail's head): the same censer, a little bigger, its cap and hanger ring on top."""
    px = {}
    censer(px, 7.0, 9.5, 6.6, 2.8)
    for (x, y, c) in ((6, 1, G[6]), (7, 1, G[5]), (5, 2, G[7]), (8, 2, G[3]), (6, 3, G[2]), (7, 3, G[2]),   # the ring
                      (5, 3, G[6]), (8, 3, G[4]), (6, 2, G[1]), (7, 2, G[1])):
        px[(x, y)] = c
    return px


def chain_link():
    rows = (".ab.", "a..c", "a..c", "b..c", "c..d", ".cd.")
    col = {"a": G[7], "b": G[6], "c": G[4], "d": G[2]}
    return {(x, y): col[ch] for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != "."}


PUFFS = (
    ("........", "........", "...ab...", "..abbc..", "..bbcc..", "...cc...", "........", "........"),
    ("........", "..aab...", ".abbbbc.", "aabbbccc", ".bbbccd.", ".bccccd.", "..cddd..", "........"),
    ("........", "..ab....", ".ab..bc.", "ab....cc", ".b....c.", ".bc..cd.", "..cdd...", "........"),
    ("........", "........", "...a....", "..b..c..", ".......c", "..c..d..", "....d...", "........"),
)


def puff(k):
    col = {"a": SM[3], "b": SM[2], "c": AE[3], "d": SM[1]}
    return {(x, y): col[ch] for y, row in enumerate(PUFFS[k]) for x, ch in enumerate(row) if ch != "."}


def censer_icon(lit):
    """A 16 x 16 buff icon: the censer at the bottom (pierced, on its hook) and its smoke above; burnt out, dark and a thread
    of grey."""
    px = {}
    ball = ("..abba..", ".abbbbc.", "abbddbbc", "abdbbdbc", "bbbddbcc", ".bccccd.", "..cddd..")
    shade = {"a": G[8], "b": G[6], "c": G[4], "d": G[1]} if lit else {"a": G[4], "b": G[3], "c": G[2], "d": G[0]}
    for y, row in enumerate(ball):
        for x, ch in enumerate(row):
            if ch != ".":
                px[(x + 4, y + 9)] = shade[ch]
    for (x, y) in ((7, 8), (8, 8), (7, 7), (8, 6)):              # the hanger
        px[(x, y)] = G[6] if lit else G[3]
    if lit:
        smoke = ((6, 5, SM[3]), (5, 4, SM[2]), (5, 3, AE[3]), (6, 2, SM[2]), (7, 1, AE[3]), (9, 5, SM[2]), (10, 4, AE[3]), (10, 3, SM[3]),
                 (9, 2, SM[2]), (11, 2, AE[3]), (4, 1, SM[1]))
    else:
        smoke = ((8, 5, SM[1]), (9, 4, SM[0]), (9, 3, SM[1]), (8, 2, SM[0]))
    for (x, y, c) in smoke:
        px[(x, y)] = c
    return px


def image_of(px, w=None, h=None):
    xs, ys = [x for x, _ in px], [y for _, y in px]
    x0, y0 = min(xs), min(ys)
    w = w or max(xs) - x0 + 1
    h = h or max(ys) - y0 + 1
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        im.putpixel((x - x0, y - y0), tuple(c) + (255,))
    return im


def boxed(px, w, h):
    """px placed on a w x h canvas at its own coordinates (0, 0 the top-left)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def strip(frames, cell, gap=1):
    im = Image.new("RGBA", (cell, (cell + gap) * len(frames) - gap), (0, 0, 0, 0))
    for k, px in enumerate(frames):
        for (x, y), c in px.items():
            im.putpixel((x, y + k * (cell + gap)), tuple(c) + (255,))
    return im


def outputs():
    pix = reference()
    return {
        OUT + "Weapons/IncenseMace.png": image_of(icon()),
        OUT + "Weapons/IncenseMaceHead.png": image_of(head()),
        OUT + "Weapons/IncenseMaceChain.png": boxed(chain_link(), 4, 6),
        OUT + "Weapons/IncenseAura.png": strip([puff(k) for k in range(4)], 8),
        OUT + "Buffs/IncenseBlessing.png": boxed(censer_icon(True), 16, 16),
        OUT + "Buffs/IncenseBurntOut.png": boxed(censer_icon(False), 16, 16),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    out = outputs()
    for rel, im in out.items():
        export(im, rel)
    if args.preview:
        ims = list(out.values())
        sc = 6
        w = sum(im.width * sc + 16 for im in ims) + 16
        h = max(im.height * sc for im in ims) + 32
        sheet = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
        for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
            band = Image.new("RGBA", (w, h), bg + (255,))
            x = 16
            for im in ims:
                band.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (x, 16))
                x += im.width * sc + 16
            sheet.paste(band, (0, row * h))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
