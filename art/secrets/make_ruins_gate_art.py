"""Source for the Fundamental Ruins' rune glyphs and their sealed gate (D4), 2026-11-11 (user: "the door to the arena is
sealed shut until the player activates 3 rune glyphs on the area, placed on the dead ends"). Run from the repo root:

    python -P art/secrets/make_ruins_gate_art.py [--preview FILE]

In the ruins' own stones (art/secrets/make_fundamental_ruins_art.py: deep blue rune stone, slate Ancient Brick, aether
light), lit from the top-left:
* FundamentalGlyphTile (2x3 tiles, three styles): a slab of blue rune stone with a rounded top on a slate foot, its rune
  cut deep in the middle: 1 the waves (the drowned crypt), 2 the eye (the bell tower), 3 the crescent (the ossuary).
  The glow sheet holds the cut rune's light (drawn added onto the slab: faint while dark, blazing once lit).
* FundamentalSealTile (9x3 tiles): a slab of Ancient Brick, its top a worn floor, a carved band of runes along it and three
  gilt-rimmed sockets (glyph 1, 2, 3 in tile columns 2, 4, 6 of its middle row), the middle one in a great carved ring.
  The glow sheet holds each socket's light (only a lit glyph's socket is drawn).
Tile sheets on vanilla's 18 px stride (16 px tiles, 2 px gaps). At most 16 colours a sheet (D4 rule 5).

Outputs (Content/Secrets/Ruins/Tiles/):
    FundamentalGlyphTile.png, FundamentalGlyphTile_Glow.png    108x54 (3 styles x 2 tiles, 3 rows)
    FundamentalSealTile.png, FundamentalSealTile_Glow.png      162x54 (9 tiles, 3 rows)
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, preview as kit_preview  # noqa: E402
from rig import RAMP  # noqa: E402

OUT = "Content/Secrets/Ruins/Tiles/"
ST, DN, AE, GI, VD = RAMP["steel"], RAMP["denim"], RAMP["aether"], RAMP["gilt"], RAMP["verd"]
SLATE = (ST[0], ST[2], ST[3], ST[4], ST[5])                 # Ancient Brick's slate
RUNE = (DN[0], DN[1], DN[2], DN[3], DN[4])                  # the blue rune stone
LIGHT = (AE[1], AE[2], AE[3])                               # the glow sheets' light
RIM = (GI[1], GI[4], GI[6], GI[8])                          # the sockets' gilt rims

GLYPHS = (
    ("........",                                            # 1: the waves
     ".##..##.",
     "#..##..#",
     "........",
     ".##..##.",
     "#..##..#",
     "........",
     ".##..##.",
     "#..##..#",
     "........"),
    ("...##...",                                            # 2: the eye
     "..#..#..",
     ".#....#.",
     "#..##..#",
     "#.####.#",
     "#..##..#",
     ".#....#.",
     "..#..#..",
     "...##...",
     "...##..."),
    ("..####..",                                            # 3: the crescent
     ".#....#.",
     "#......#",
     "#..##...",
     "#..##...",
     "#......#",
     ".#....#.",
     "..####..",
     "...##...",
     "..####.."),
)


def glyph(k):
    """One glyph, 16x24 at 1x: the slab and its foot; and its glow (the cut rune)."""
    p = Pix(16, 24)
    for y in range(20, 24):                                 # the slate foot
        for x in range(0, 16):
            p.put(x, y, SLATE, 4 if y == 20 else (3 if x < 6 else 2))
    for y in range(1, 20):                                  # the slab: a rounded top, lit on its left
        x0, x1 = (4, 11) if y == 1 else ((3, 12) if y == 2 else (2, 13))
        for x in range(x0, x1 + 1):
            p.put(x, y, RUNE, 4 if x <= x0 + 1 else (2 if x >= x1 - 1 else 3))
    p.outline()
    rows = GLYPHS[k]
    g = Pix(16, 24)
    for dy, row in enumerate(rows):                         # the rune cut into it, and its light
        for dx, ch in enumerate(row):
            if ch == "#":
                p.put(4 + dx, 6 + dy, RUNE, 0)
                g.put(4 + dx, 6 + dy, LIGHT, 2 if (dx + dy) % 3 else 1)
    for (x, y) in ((4, 3), (11, 3), (4, 17), (11, 17)):     # four carved studs round it
        p.put(x, y, RUNE, 1)
    return p.image(), g.image()


def seal():
    """The gate's slab, 72x24 at 1x, and its sockets' glow."""
    p = Pix(72, 24)
    for y in range(24):
        for x in range(72):
            if y <= 1:
                i = 4 if y == 0 else 3                      # the worn floor on top
            elif y >= 21:
                i = 1                                       # its underside, the arena's ceiling
            else:
                i = 3 if (x // 6 + y // 4) % 2 == 0 else 2  # ashlar courses
            p.put(x, y, SLATE, i)
    for x in range(72):                                     # the courses' joints
        for y in (5, 9, 13, 17):
            if (x + (y // 4) * 3) % 6 == 0 or y in (5, 17):
                p.put(x, y, SLATE, 1)
    for x in range(3, 69):                                  # a carved band of runes
        if x % 4 in (0, 1) and x not in range(14, 26) and x not in range(30, 42) and x not in range(46, 58):
            p.put(x, 7 + (x // 4) % 2, RUNE, 2)
            p.put(x, 16 - (x // 4) % 2, RUNE, 2)
    g = Pix(72, 24)
    for k, cx in enumerate((20, 36, 52)):                   # the sockets: gilt rims round dark wells
        r = 6 if k == 1 else 4
        for y in range(12 - r - 1, 12 + r + 2):
            for x in range(cx - r - 1, cx + r + 2):
                d2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - 12) ** 2
                if d2 <= (r + 0.5) ** 2:
                    if d2 >= (r - 0.6) ** 2:
                        p.put(x, y, RIM, 3 if x + y < cx + 12 else 1)
                    else:
                        p.put(x, y, RUNE, 1 if d2 > 4.5 else 0)
                        g.put(x, y, LIGHT, 2 if d2 <= 2.5 else (1 if d2 <= 6.5 else 0))
        if k == 1:                                          # the great ring round the middle one
            for y in range(1, 23):
                for x in range(cx - 11, cx + 12):
                    d2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - 12) ** 2
                    if 8.6 ** 2 <= d2 <= 9.6 ** 2:
                        p.put(x, y, RUNE, 3 if y < 12 else 2)
    p.outline()
    return p.image(), g.image()


def tiles(img, tw, th):
    """A 1x object split into 8x8 tiles laid out on the 9 px (18 px at 2x) stride."""
    out = Image.new("RGBA", (tw * 9, th * 9), (0, 0, 0, 0))
    for ty in range(th):
        for tx in range(tw):
            out.alpha_composite(img.crop((tx * 8, ty * 8, tx * 8 + 8, ty * 8 + 8)), (tx * 9, ty * 9))
    return out


def export_all(preview_path=None):
    body, glow = Image.new("RGBA", (54, 27), (0, 0, 0, 0)), Image.new("RGBA", (54, 27), (0, 0, 0, 0))
    shown = []
    for k in range(3):
        im, gl = glyph(k)
        body.alpha_composite(tiles(im, 2, 3), (k * 18, 0))
        glow.alpha_composite(tiles(gl, 2, 3), (k * 18, 0))
        lit = im.copy()
        lit.alpha_composite(gl)
        shown += [im, lit]
    export(body, OUT + "FundamentalGlyphTile.png")
    export(glow, OUT + "FundamentalGlyphTile_Glow.png")
    s, sg = seal()
    export(tiles(s, 9, 3), OUT + "FundamentalSealTile.png")
    export(tiles(sg, 9, 3), OUT + "FundamentalSealTile_Glow.png")
    lit = s.copy()
    lit.alpha_composite(sg)
    if preview_path:
        kit_preview(shown + [s, lit], preview_path, scale=5)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    export_all(a.preview)
