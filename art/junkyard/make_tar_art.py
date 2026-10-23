"""Source for the Junkyard's steaming tar (D4). Run from the repo root:

    python -P art/junkyard/make_tar_art.py

The tar is vanilla water with a custom water style (Content/Junkyard/Tar/TarWaterStyle.cs), so its textures follow
vanilla's liquid layouts (decompiled LiquidRenderer / TileDrawing.DrawPartialLiquid / WaterfallManager / Gore, sizes
matching ExampleMod 1.4.4's water style). Outputs, 2x nearest-neighbour, next to the .cs files in Content/Junkyard/Tar/:

    TarWaterStyle.png           48x1360  16 animation frames of 48x80 + the calm surface strip at y = 1280.
                                         Per frame, 16 px cells: x 0 = left side exposed, 16 = middle, 32 = right side
                                         exposed; y 0 = surface, 16/32 = side-exposed bodies, 48-80 = the interior block
                                         (sampled at 4 px offsets for rounded corners, so it is one continuous texture).
    TarWaterStyle_Block.png     306x16   liquid drawn behind half blocks and slopes (only x 0-16 is sampled)
    TarWaterStyle_Slope.png     72x16    4 slope variants on an 18 px stride
    TarWaterfallStyle.png       512x40   16 frames of 32 px: the falling stream (x 0-16, y 0-16) and its lip (y 24-40)
    TarDroplet.png              18x300   15 frames of 18x20: forming 0-4, remnant 5-8, falling 9, splash 10-14
    TarSplash.png               8x28     3 droplets of 8x8 at the modded-dust offsets y 0/10/20
    TarSteam.png                66x100   2 variants (columns) x 3 growth stages (rows) of 32x32, 34 px stride
    TarPlague.png               32x32    debuff icon

Tar is brown-black (Leather 0 body, Iron 0 swirls) with a cold gloss on its crest (Iron 2 dashes, Iron 3 glints) and a
warm Brass 1 sheen. Vanilla draws water at 60% opacity, so the pixels stay opaque here (D4 rule 9) and the see-through
look comes from the game. No outlines on the liquid itself; exposed sides get a one-pixel skin (Iron 1).
Every animated pattern has an 8 px period and moves 1 px per frame (the interior every other frame), so the 16 frames
loop and neighbouring cells line up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scrap"))
from make_scrap_art import PAL, Canvas, export  # noqa: E402

PAL.update({"h": (138, 144, 150)})   # Steam 0, the shadow side of a steam puff

OUT = "Content/Junkyard/Tar/"
FRAMES = 16
CELL = 8                             # 16 px at 2x

# ------------------------------------------------------------------------------------------------
# Liquid body
# ------------------------------------------------------------------------------------------------
# 8x8 interior swirl, tiled; 'i' = Iron 0 swirl on the Leather 0 body.
SWIRL = [
    "llllllll",
    "lliillll",
    "llllllll",
    "lllllill",
    "llllllll",
    "illlllll",
    "llllllll",
    "llllliil",
]
CREST = "kCjkqjCj"                   # glossy crest, 8 px period: gloss dash, warm sheen, glint
UNDER_CREST = "ijiiijii"


def body(x, y, frame):
    """Interior colour at liquid coordinates (x, y); drifts 1 px every other frame."""
    return SWIRL[y % 8][(x + frame // 2) % 8]


def liquid_cell(frame, top, left, right, ox=0, oy=0):
    c = Canvas(CELL, CELL)
    for y in range(CELL):
        for x in range(CELL):
            c.set(x, y, body(ox + x, oy + y, frame))
    if top:
        for x in range(CELL):
            c.set(x, 0, CREST[(ox + x + frame) % 8])
            c.set(x, 1, UNDER_CREST[(ox + x + frame) % 8])
    if left:
        for y in range(1 if top else 0, CELL):
            c.set(0, y, "j")
    if right:
        for y in range(1 if top else 0, CELL):
            c.set(CELL - 1, y, "j")
    return c


def water_frame(sheet, frame, y0, calm=False):
    f = 0 if calm else frame
    # row 0: surface cells (left exposed / middle / right exposed)
    sheet.blit(liquid_cell(f, True, True, False, 0, 0), 0, y0)
    sheet.blit(liquid_cell(f, True, False, False, 8, 0), 8, y0)
    sheet.blit(liquid_cell(f, True, False, True, 16, 0), 16, y0)
    # row 1: one exposed side; the middle cell is a one-tile-wide column's top (both sides + top)
    sheet.blit(liquid_cell(f, False, True, False, 0, 8), 0, y0 + 8)
    sheet.blit(liquid_cell(f, True, True, True, 8, 8), 8, y0 + 8)
    sheet.blit(liquid_cell(f, False, False, True, 16, 8), 16, y0 + 8)
    # row 2: the alternate rows of a side-exposed body; middle = one-tile-wide column body
    sheet.blit(liquid_cell(f, False, True, False, 0, 16), 0, y0 + 16)
    sheet.blit(liquid_cell(f, False, True, True, 8, 16), 8, y0 + 16)
    sheet.blit(liquid_cell(f, False, False, True, 16, 16), 16, y0 + 16)
    # rows 3-4: one continuous interior block
    for y in range(16):
        for x in range(24):
            sheet.set(x, y0 + 24 + y, body(x, y, f))


def make_water():
    sheet = Canvas(24, 40 * (FRAMES + 1))
    for frame in range(FRAMES):
        water_frame(sheet, frame, frame * 40)
    water_frame(sheet, 0, FRAMES * 40, calm=True)
    return sheet


def make_block():
    c = Canvas(153, 8)
    for y in range(8):
        for x in range(153):
            c.set(x, y, CREST[x % 8] if y == 0 else body(x, y, 0))
    return c


def make_slope():
    c = Canvas(36, 8)
    for v in range(4):
        for y in range(8):
            for x in range(8):
                c.set(v * 9 + x, y, body(x, y, 0))
    return c


def make_waterfall():
    """16 frames of 16 px (32 at 2x): stream x 0-7, y 0-7; lip x 0-15, y 12-19. Gloss streaks fall 1 px per frame."""
    c = Canvas(256, 20)
    streaks = {1: "k", 4: "j", 6: "q"}             # column -> streak colour
    for frame in range(FRAMES):
        x0 = frame * 16
        for y in range(8):
            for x in range(8):
                ch = "l"
                if x in streaks and (y - frame) % 8 in (0, 1, 2):
                    ch = streaks[x] if (y - frame) % 8 == 0 else "i"
                c.set(x0 + x, y, ch)
        for y in range(12, 20):
            for x in range(16):
                ch = "j" if y == 12 else body(x, y, frame)
                if y == 13 and (x + frame) % 8 == 2:
                    ch = "k"
                c.set(x0 + x, y, ch)
    return c


# ------------------------------------------------------------------------------------------------
# Droplet gore: 15 frames of 9x10 (18x20 at 2x)
# ------------------------------------------------------------------------------------------------
DROP_FRAMES = [
    [(4, 0, "l")],
    [(4, 0, "l"), (4, 1, "l")],
    [(3, 0, "l"), (4, 0, "j"), (5, 0, "l"), (4, 1, "l")],
    [(3, 0, "l"), (4, 0, "j"), (5, 0, "l"), (3, 1, "l"), (4, 1, "k"), (5, 1, "l"), (4, 2, "l")],
    [(3, 0, "l"), (4, 0, "j"), (5, 0, "l"), (3, 1, "k"), (4, 1, "l"), (5, 1, "l"), (3, 2, "l"), (4, 2, "l"),
     (5, 2, "i"), (4, 3, "i")],
    [(3, 0, "l"), (4, 0, "l"), (5, 0, "l"), (4, 1, "l")],
    [(4, 0, "l"), (4, 1, "i")],
    [(4, 0, "l")],
    [(4, 0, "i")],
    [(4, 0, "l"), (3, 1, "k"), (4, 1, "l"), (5, 1, "l"), (3, 2, "l"), (4, 2, "l"), (5, 2, "i"), (4, 3, "i")],
    [(3, 8, "l"), (4, 8, "j"), (5, 8, "l"), (2, 7, "l"), (6, 7, "l"), (4, 7, "k")],
    [(2, 8, "l"), (6, 8, "l"), (1, 6, "l"), (7, 6, "l"), (4, 6, "l"), (3, 9, "i"), (4, 9, "i"), (5, 9, "i")],
    [(1, 5, "l"), (7, 5, "l"), (0, 7, "i"), (8, 7, "i"), (4, 5, "i"), (2, 9, "i"), (6, 9, "i")],
    [(0, 6, "i"), (8, 6, "i"), (3, 9, "i"), (5, 9, "i")],
    [(1, 9, "i"), (7, 9, "i")],
]


def make_droplet():
    c = Canvas(9, 150)
    for f, pixels in enumerate(DROP_FRAMES):
        for (x, y, ch) in pixels:
            c.set(x, f * 10 + y, ch)
    return c


def make_splash():
    c = Canvas(4, 14)
    blobs = [
        [(1, 1, "k"), (2, 1, "l"), (1, 2, "l"), (2, 2, "i")],
        [(0, 1, "l"), (1, 1, "k"), (2, 1, "l"), (1, 2, "l"), (2, 2, "i")],
        [(1, 0, "l"), (1, 1, "k"), (2, 1, "l"), (1, 2, "l"), (2, 2, "l"), (2, 3, "i")],
    ]
    for f, pixels in enumerate(blobs):
        for (x, y, ch) in pixels:
            c.set(x, f * 5 + y, ch)
    return c


# ------------------------------------------------------------------------------------------------
# Steam puff: soft cloud lobes, lit from the top-left (t), body (s), shadow side (h). No outline (steam).
# ------------------------------------------------------------------------------------------------
STEAM_LOBES = [
    [  # variant A: stage 0, 1, 2 as (dx, dy, r) lobes around the cell centre
        [(0, 1, 2.6), (-1.5, 2, 1.8)],
        [(0, 0, 3.6), (-3, 1.5, 2.6), (2.8, 1.8, 2.4)],
        [(-1, -2, 3.6), (-4.5, 1, 2.8), (3.5, 0, 3.0), (0.5, 3, 2.2), (5.5, -3.5, 1.4)],
    ],
    [  # variant B: leans the other way
        [(0, 1, 2.4), (1.6, 2, 1.8)],
        [(0.5, 0, 3.4), (3, 1.8, 2.6), (-2.6, 2, 2.2)],
        [(1, -2, 3.5), (4.5, 1, 2.8), (-3.5, 0.5, 3.0), (-0.5, 3, 2.0), (-5.5, -3, 1.5)],
    ],
]


def steam_cell(lobes, holes):
    c = Canvas(16, 16)
    cx, cy = 7.5, 9.0
    inside = set()
    for y in range(16):
        for x in range(16):
            for (dx, dy, r) in lobes:
                if (x - cx - dx) ** 2 + (y - cy - dy) ** 2 <= r * r:
                    inside.add((x, y))
                    break
    inside -= holes
    for (x, y) in inside:
        up = (x, y - 1) not in inside or (x - 1, y) not in inside
        down = (x, y + 1) not in inside or (x + 1, y) not in inside
        c.set(x, y, "t" if up and not down else ("h" if down and not up else "s"))
    return c


def make_steam():
    c = Canvas(33, 50)
    holes = [set(), set(), {(7, 8), (8, 9), (3, 10), (11, 6)}]
    for v in range(2):
        for stage in range(3):
            c.blit(steam_cell(STEAM_LOBES[v][stage], holes[stage]), v * 17, stage * 17)
    return c


# ------------------------------------------------------------------------------------------------
# Tar Plague icon (16x16 -> 32x32): a glossy tar drop weeping over a puddle, steam curling off it, and a sickly
# verdigris bubble. Outline = Iron 0 (the tar's darkest shade).
# ------------------------------------------------------------------------------------------------
PLAGUE_ICON = [
    "....t...........",
    "...s.s..........",
    "....s...........",
    "......iii.......",
    ".....ijkji......",
    ".....iqklli.....",
    "....ijklllli....",
    "....ikllllmi....",
    "...ijlllllmli...",
    "...ikllmlllli...",
    "...ijllllllli.vv",
    "....illllllivwuv",
    ".....illlli..vv.",
    "..iiiillllliii..",
    ".illlllllllllli.",
    "..iiiiiiiiiiii..",
]


def make_plague_icon():
    return Canvas.from_rows(PLAGUE_ICON)


if __name__ == "__main__":
    export(make_water(), OUT + "TarWaterStyle.png")
    export(make_block(), OUT + "TarWaterStyle_Block.png")
    export(make_slope(), OUT + "TarWaterStyle_Slope.png")
    export(make_waterfall(), OUT + "TarWaterfallStyle.png")
    export(make_droplet(), OUT + "TarDroplet.png")
    export(make_splash(), OUT + "TarSplash.png")
    export(make_steam(), OUT + "TarSteam.png")
    export(make_plague_icon(), OUT + "TarPlague.png")
