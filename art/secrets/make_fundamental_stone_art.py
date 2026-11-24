"""Source for the Fundamental Stones (D4), 2026-11-10 (user, with a reference image of a rune tablet on a pedestal: "the
secret puzzle: add 5 Fundamental stones (design reference on the second image) on the map; they should be a fixed
background (can't be mined and don't block the player's path, like a background wall) interactable object that always
generates on 5 fixed spots on the map ... these stones can be read with the right mouse click, saying random
glyphs/runes"). Run from the repo root:

    python -P art/secrets/make_fundamental_stone_art.py [--preview FILE]

A 4x6-tile monolith (32x48 at 1x): a tablet of dark blue slate with an arched top and a ring cut through its crown,
chipped at the edges, a crack down its face, standing in a grey stone pedestal of two steps with a brass plaque riveted to
its front. Cut into the slate: a diamond with the stone's sigil in it (one of five: an upward fleur, a sun, a mountain, a
cross, a wave: each stone its own, the tile's style), a ring of twelve rune marks round it and three rune pairs above and
below. The cuts are drawn in dim slate on the stone and lit on the glow sheet (pale blue with white-hot cores), which the
game draws at full brightness, breathing slowly. Lit from the top-left; ramp-0 outlines; 15 colours.

The reading (the right click) shows a line of runes from FundamentalRunes.png: 16 glyphs 7x9 (1x), the five sigils
first, then eleven runes, pale blue with white cores.

Outputs (Content/Secrets/):
    FundamentalStoneTile.png        360x108: 5 styles side by side, each 4x6 tiles on vanilla's 18 px stride
    FundamentalStoneTile_Glow.png   the same layout: the lit cuts
    FundamentalStoneTile_Awake.png  the same layout: the cuts of an awake stone (2026-11-24: gold, white-hot hearts; a stone
                                    woken in the puzzle's order glows gold instead of blue)
    FundamentalRunes.png            256x18: 16 glyphs of 14x18 on a 16 px stride
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Secrets/"
TW, TH = 4, 6                     # the stone in tiles
W, H = TW * 8, TH * 8             # 32x48 at 1x
STYLES = 5
D, ST, G, S = RAMP["denim"], RAMP["steel"], RAMP["gilt"], RAMP["steam"]
GLOW_DIM = D[3]                   # a cut on the stone itself (dark when the glow ebbs)
GLOW_LIT, GLOW_HOT = D[5], S[3]   # the glow sheet: pale blue, white-hot at the heart
AWAKE_LIT, AWAKE_HOT = G[7], G[9] # the awake sheet: gold, a white-gold heart
CENTER = (15.5, 21.0)             # the diamond's middle

# The five sigils (5x7), drawn in the diamond and as the first five glyphs of the reading: '#' a cut, '*' its hot heart.
SIGILS = [
    ["..*..",                     # 0 the tar pit's: an upward fleur (the reference's)
     ".***.",
     "*.#.*",
     "..#..",
     ".###.",
     "..#..",
     ".#.#."],
    [".###.",                     # 1 Westworld's: a sun
     "#...#",
     "#.*.#",
     "#...#",
     ".###.",
     "#.#.#",
     "....."],
    ["..#..",                     # 2 a mountain
     "..#..",
     ".#*#.",
     ".#.#.",
     "#...#",
     "#####",
     "....."],
    ["..#..",                     # 3 a cross
     "..#..",
     "##*##",
     "..#..",
     "..#..",
     ".#.#.",
     "....."],
    ["#...#",                     # 4 a wave
     ".#.#.",
     "..*..",
     "#...#",
     ".#.#.",
     "..#..",
     "....."],
]

# Eleven runes (5x7), staves and branches like old carved alphabets (my call: invented, no real script).
RUNES = [
    ["#....", "##...", "#.#..", "#..#.", "#....", "#....", "#...."],
    ["..#..", ".#.#.", "#...#", "..#..", "..#..", "..#..", "..#.."],
    ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    ["#####", "#....", "#....", "###..", "#....", "#....", "#####"],
    ["..#..", "..#..", "#.#.#", ".###.", "..#..", "..#..", "..#.."],
    ["#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"],
    [".###.", "#...#", "....#", "...#.", "..#..", "..#..", "..#.."],
    ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    ["#....", "#....", "#..#.", "#.#.#", "##...", "#....", "#...."],
    [".#.#.", ".#.#.", ".###.", "..#..", ".###.", ".#.#.", ".#.#."],
    ["..#..", ".#...", "#####", "...#.", "..#..", ".#...", "#...."],
]


def tablet_shape():
    """The slate's pixels: 20 wide (x 6..25), from the arched crown (y 3) down into the pedestal (y 41), chipped edges."""
    px = set()
    for y in range(3, 42):
        for x in range(6, 26):
            if y < 9:                                              # the arched top: a half ellipse
                dx = (x + 0.5 - 16.0) / 10.0
                dy = (y + 0.5 - 9.0) / 6.0
                if dx * dx + dy * dy > 1.0:
                    continue
            px.add((x, y))
    for (x, y) in ((6, 15), (6, 16), (25, 27), (25, 26), (25, 33), (6, 36), (7, 36)):   # chips out of the edges
        px.discard((x, y))
    for y in range(4, 8):                                          # the ring cut through the crown
        for x in range(14, 18):
            if (x, y) in ((14, 4), (17, 4), (14, 7), (17, 7)):
                continue
            if 15 <= x <= 16 and 5 <= y <= 6:
                px.discard((x, y))                                 # the hole
    return px


def stone(style):
    """The stone (32x48 at 1x) of `style`, and its glow."""
    px, gl = {}, {}
    slate = tablet_shape()
    for (x, y) in slate:                                           # the slate, lit from the top-left
        out = any((x + dx, y + dy) not in slate for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if out:
            lit = (x - 1, y) not in slate or (x, y - 1) not in slate   # an edge facing the light (left or top)
            px[(x, y)] = D[1] if lit and x < 16 else D[0]
        else:
            t = (x - 6) / 19.0 + (y - 3) / 76.0                    # darker towards the lower right
            px[(x, y)] = D[3] if t < 0.22 else (D[2] if t < 0.75 else D[1])
    for (x, y) in ((9, 12), (10, 13), (10, 14), (11, 15), (21, 30), (22, 31), (22, 32), (23, 33)):   # a crack, a scratch
        if (x, y) in px:
            px[(x, y)] = D[0]
    # the pedestal: two steps of grey stone, lit along their tops and left ends, a brass plaque on the lower step
    for y in range(40, 48):
        x0, x1 = (4, 27) if y < 44 else (1, 30)
        for x in range(x0, x1 + 1):
            top = y in (40, 44)
            edge = x in (x0, x1) or y in (43, 47)
            if edge and not top:
                px[(x, y)] = ST[0] if x == x1 or y in (43, 47) else ST[2]
            elif top:
                px[(x, y)] = ST[6] if x < x1 else ST[2]
            else:
                px[(x, y)] = ST[4] if x < (x0 + x1) // 2 + 4 else ST[2]
    for y in (45, 46):                                             # the brass plaque
        for x in range(12, 20):
            px[(x, y)] = G[7] if y == 45 else G[4]
    for x in (12, 19):
        px[(x, 45)] = G[1]
        px[(x, 46)] = G[1]
    for x in (13, 18):
        px[(x, 45)] = G[4]                                         # its rivets
    for x in range(14, 18):
        px[(x, 46)] = G[1]                                         # an engraved line

    def cut(x, y, hot=False):
        if (x, y) in slate:
            px[(x, y)] = GLOW_DIM
            gl[(x, y)] = GLOW_HOT if hot else GLOW_LIT

    cx, cy = CENTER
    for k in range(-7, 8):                                         # the diamond: |dx|/6 + |dy|/8 = 1
        for (sx, sy) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            dy = abs(k)
            dx = 6.0 * (1.0 - dy / 8.0)
            cut(int(math.floor(cx + sx * dx)), int(math.floor(cy + sy * dy)))
    for j, row in enumerate(SIGILS[style]):                        # the stone's sigil in the diamond
        for i, ch in enumerate(row):
            if ch != ".":
                cut(13 + i, 18 + j, hot=ch == "*")
    for n in range(12):                                            # a ring of rune marks round it
        a = n * math.tau / 12.0 + 0.26
        r = 9.0 if n % 2 == 0 else 8.4
        x, y = int(math.floor(cx + r * math.cos(a) * 0.95)), int(math.floor(cy + r * math.sin(a) * 1.25))
        cut(x, y)
        if n % 3 == 0:
            cut(x + (1 if math.cos(a) > 0 else -1), y)
    for (rx, ry, rune) in ((8, 33, 2), (14, 33, 5), (20, 33, 9)):  # three rune pairs under the ring, two over it
        for j, row in enumerate(RUNES[rune][:5]):
            for i, ch in enumerate(row[:4]):
                if ch == "#":
                    cut(rx + i, ry + j)
    for (rx, ry, rune) in ((9, 9, 0), (19, 9, 4)):
        for j, row in enumerate(RUNES[rune][:4]):
            for i, ch in enumerate(row[:4]):
                if ch == "#":
                    cut(rx + i, ry + j)
    return px, gl


def tile_sheet(canvases):
    """The styles side by side, each cut into 8x8 tiles on vanilla's stride (1 px gap at 1x: 18 px at 2x)."""
    sheet = Image.new("RGBA", (STYLES * TW * 9, TH * 9), (0, 0, 0, 0))
    for st, px in enumerate(canvases):
        im = to_image(px, 0, 0, W, H)
        for ty in range(TH):
            for tx in range(TW):
                piece = im.crop((tx * 8, ty * 8, tx * 8 + 8, ty * 8 + 8))
                sheet.alpha_composite(piece, ((st * TW + tx) * 9, ty * 9))
    return sheet


def glyph(rows, scale_to=(7, 9)):
    """A 7x9 glyph from a 5x7 pattern: pale blue strokes, white-hot hearts ('*'), a pixel of margin all round."""
    px = {}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                px[(1 + i, 1 + j)] = GLOW_HOT if ch == "*" else GLOW_LIT
    return px


def runes_sheet():
    glyphs = SIGILS + RUNES
    sheet = Image.new("RGBA", (len(glyphs) * 8, 9), (0, 0, 0, 0))
    for k, rows in enumerate(glyphs):
        sheet.alpha_composite(to_image(glyph(rows), 0, 0, 7, 9), (k * 8, 0))
    return sheet


def export_all():
    stones = [stone(s) for s in range(STYLES)]
    export(tile_sheet([px for px, _ in stones]), OUT + "FundamentalStoneTile.png")
    export(tile_sheet([gl for _, gl in stones]), OUT + "FundamentalStoneTile_Glow.png")
    awake = [{k: (AWAKE_HOT if c == GLOW_HOT else AWAKE_LIT) for k, c in gl.items()} for _, gl in stones]
    export(tile_sheet(awake), OUT + "FundamentalStoneTile_Awake.png")
    export(runes_sheet(), OUT + "FundamentalRunes.png")


def preview(path):
    """Every style over dark and light, its glow on top (4x), and the runes."""
    cells = []
    for bg in ((22, 24, 30, 255), (150, 180, 210, 255)):
        row = Image.new("RGBA", ((W + 4) * STYLES, H + 4), bg)
        for s in range(STYLES):
            px, gl = stone(s)
            row.alpha_composite(to_image(px, 0, 0, W, H), (2 + s * (W + 4), 2))
            row.alpha_composite(to_image(gl, 0, 0, W, H), (2 + s * (W + 4), 2))
        cells.append(row)
    runes = Image.new("RGBA", ((W + 4) * STYLES, 13), (22, 24, 30, 255))
    runes.alpha_composite(runes_sheet(), (2, 2))
    out = Image.new("RGBA", (cells[0].width, sum(c.height for c in cells) + runes.height), (0, 0, 0, 255))
    y = 0
    for c in cells + [runes]:
        out.paste(c, (0, y))
        y += c.height
    out.resize((out.width * 4, out.height * 4), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
