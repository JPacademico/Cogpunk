"""Source for the Junkyard slice sprites (D4). Run from the repo root:

    python -P art/junkyard/make_junkyard_art.py

Outputs (2x nearest-neighbour, next to their .cs files):
    Content/Junkyard/Tiles/PolishedMetalTile.png    288x270 terrain sheet (seamless welded plating)
    Content/Junkyard/Items/PolishedMetal.png        16x16
    Content/Junkyard/Items/Junkbait.png             28x28 boss summon (a ball of scrap glazed in grease)
    Content/Junkyard/JunkyardBiome_Icon.png         30x30 bestiary filter icon

Polished Metal follows the D4 "seamless blocks" rule like Rusted Scrap: plain plate texture at the tile edges, welds,
patch plates and rivets at least one pixel inside, outlines only on exposed sides (art/templates/terrain_exposure.json).
The pool's tar is vanilla water drawn with a custom water style; its textures come from art/junkyard/make_tar_art.py.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scrap"))
from make_scrap_art import PAL, Canvas, export, make_cog  # noqa: E402

# Palette letters this slice adds (all from art/palettes/cogpunk.gpl): Aether 0/1 and Verdigris 0 for the oil sheen.
PAL.update({"A": (34, 26, 69), "P": (70, 58, 147), "V": (23, 52, 48)})

ROOT = os.getcwd()


# --------------------------------------------------------------------------------------------
# Polished Metal (iron ramp: i outline, j, k, q base, r glint)
# --------------------------------------------------------------------------------------------
METAL_VARIANTS = [
    [  # A: riveted patch plate with a polished glint
        "qqqqqqqq",
        "qkkkkkqq",
        "qkrrqkqq",
        "qkqqqkqq",
        "qkkkkkqq",
        "qqqqqqqq",
        "qqqqrrrq",
        "qqqqqqqq",
    ],
    [  # B: weld bead across the plate
        "qqqqqqqq",
        "qqrrrqqq",
        "qqqqqqqq",
        "qqqqqqqq",
        "qjkjkjkq",
        "qqqqqqqq",
        "qqqqqrrq",
        "qqqqqqqq",
    ],
    [  # C: two rivet pairs and a brushed streak
        "qqqqqqqq",
        "qrqqqqrq",
        "qjqqqqjq",
        "qqqqqqqq",
        "qqrrrqqq",
        "qrqqqqrq",
        "qjqqqqjq",
        "qqqqqqqq",
    ],
]
METAL_RIM_LIGHT = {"q": "r", "k": "q", "j": "k", "r": "r"}
METAL_RIM_DARK = {"q": "k", "r": "q", "k": "j", "j": "j"}


def terrain_frame(rows, exposure, rim_light, rim_dark, outline):
    """8x8 art for one terrain frame. exposure = 'TRBL' with 'o'/'d' (exposed) or '-' (joined)."""
    c = Canvas.from_rows(rows)
    top, right, bottom, left = (ch != "-" for ch in exposure)
    for i in range(8):
        if top:
            c.set(i, 1, rim_light.get(c.get(i, 1), c.get(i, 1)))
        if left:
            c.set(1, i, rim_light.get(c.get(1, i), c.get(1, i)))
        if bottom:
            c.set(i, 6, rim_dark.get(c.get(i, 6), c.get(i, 6)))
        if right:
            c.set(6, i, rim_dark.get(c.get(6, i), c.get(6, i)))
    for i in range(8):
        if top:
            c.set(i, 0, outline)
        if bottom:
            c.set(i, 7, outline)
        if left:
            c.set(0, i, outline)
        if right:
            c.set(7, i, outline)
    for (ex1, ex2, cx, cy, ix, iy) in ((top, left, 0, 0, 1, 1), (top, right, 7, 0, 6, 1),
                                       (bottom, left, 0, 7, 1, 6), (bottom, right, 7, 7, 6, 6)):
        if ex1 and ex2:
            c.set(cx, cy, "."); c.set(ix, iy, outline)
    return c


def make_terrain_sheet(variants, rim_light, rim_dark, outline):
    table = json.load(open(os.path.join(ROOT, "art/templates/terrain_exposure.json")))
    sheet = Canvas(16 * 9, 15 * 9)
    for key, exposure in table.items():
        fx, fy = (int(v) for v in key.split(","))
        sheet.blit(terrain_frame(variants[(fx + fy * 2) % len(variants)], exposure, rim_light, rim_dark, outline), fx * 9, fy * 9)
    return sheet


def make_metal_icon():
    """The item reads as a single welded cube: square corners instead of the terrain frame's rounded ones."""
    c = terrain_frame(METAL_VARIANTS[0], "oooo", METAL_RIM_LIGHT, METAL_RIM_DARK, "i")
    for (cx, cy, ix, iy, inner) in ((0, 0, 1, 1, "r"), (7, 0, 6, 1, "r"), (0, 7, 1, 6, "q"), (7, 7, 6, 6, "k")):
        c.set(cx, cy, "i")
        c.set(ix, iy, inner)
    return c


# --------------------------------------------------------------------------------------------
# Junkbait (boss summon): a ball of scrap glazed in grease, 16x16 art -> 32x32. A brass cog pokes out of the top right;
# rust plates show through a dark grease coat (i j k) that catches a curved glossy
# highlight on the lit top-left (q r) and an oily sheen low on the right (A P); grease drips hang off the bottom.
# Outline = Iron 0 (i), the grease's darkest shade (D4 rule 3).
# --------------------------------------------------------------------------------------------
JB_SIZE = 16
# Ball silhouette, one (first, last) column pair per row from y = 3 down; drips are added separately.
JB_BALL = {3: (4, 9), 4: (2, 11), 5: (1, 12), 6: (1, 12), 7: (1, 12), 8: (1, 12), 9: (1, 12), 10: (1, 12),
           11: (1, 12), 12: (2, 11), 13: (3, 10), 14: (5, 8)}
JB_CX, JB_CY = 6.5, 8.6
# Half-buried brass cog, top right: hub hole in grease black (i), '.' between the teeth lets the ball show through.
JB_GEAR = [
    "...CC...",
    ".C.EE.C.",
    ".CFEEDC.",
    "CEFiiDDC",
    "CEEiiDDC",
    ".CEDDDC.",
    ".C.DD.C.",
    "...CC...",
]
JB_GEAR_AT = (8, 0)


def make_junkbait():
    c = Canvas(JB_SIZE, JB_SIZE)
    ball = {(x, y) for y, (x0, x1) in JB_BALL.items() for x in range(x0, x1 + 1)}
    for (x, y) in ball:
        c.set(x, y, "j")
    # brass cog on the top right
    gx, gy = JB_GEAR_AT
    c.blit(Canvas.from_rows(JB_GEAR), gx, gy)
    gear = {(gx + x, gy + y) for y, row in enumerate(JB_GEAR) for x, ch in enumerate(row) if ch != "."}
    # outline the ball where it meets the background (never over the cog)
    solid = ball | gear
    for (x, y) in ball - gear:
        if any((x + ox, y + oy) not in solid for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            c.set(x, y, "i")
    # shading inside the outline: lit from the top-left, the grease's shadow side one shade down
    for (x, y) in ball - gear:
        if c.get(x, y) != "j":
            continue
        dx, dy = x - JB_CX, y - JB_CY
        r = math.hypot(dx, dy)
        facing = (-dx - dy) / (max(r, 0.01) * math.sqrt(2))
        if facing < -0.4 and r > 4.2:
            c.set(x, y, "i")
        elif facing > 0.6 and r > 4.0:
            c.set(x, y, "k")                     # gloss crescent along the lit rim
    # specular core, scrap showing through, oily sheen low on the right
    for (x, y, ch) in ((3, 6, "q"), (4, 5, "r"), (3, 5, "q"), (5, 4, "q"),
                       (3, 9, "d"), (4, 9, "c"), (3, 10, "c"), (4, 10, "c"), (5, 10, "b"), (4, 11, "b"),
                       (6, 6, "d"), (7, 6, "c"), (6, 7, "c"), (7, 7, "b"),
                       (8, 11, "q"), (9, 11, "k"),
                       (8, 13, "A"), (9, 12, "P"), (10, 12, "A"), (11, 11, "A")):
        c.set(x, y, ch)
    # grease drips hanging off the bottom: a long one and a short one
    for (x, y, ch) in ((4, 14, "i"), (4, 15, "i"), (9, 14, "i")):
        c.set(x, y, ch)
    return c


# --------------------------------------------------------------------------------------------
# Bestiary icon: a rusted cog on a little scrap heap (15x15 art -> 30x30)
# --------------------------------------------------------------------------------------------
def make_biome_icon():
    c = Canvas(15, 15)
    heap = [
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        "...............",
        ".......aa......",
        ".....aabdaa....",
        "...aabdcbcdaa..",
        "..abdcbmbcdcba.",
        ".abcbmcbcbmcbca",
        "aaaaaaaaaaaaaaa",
    ]
    c.blit(Canvas.from_rows(heap), 0, 0)
    cog = make_cog()
    c.blit(cog, 2, 0)
    return c


if __name__ == "__main__":
    export(make_terrain_sheet(METAL_VARIANTS, METAL_RIM_LIGHT, METAL_RIM_DARK, "i"), "Content/Junkyard/Tiles/PolishedMetalTile.png")
    export(make_metal_icon(), "Content/Junkyard/Items/PolishedMetal.png")
    export(make_junkbait(), "Content/Junkyard/Items/Junkbait.png")
    export(make_biome_icon(), "Content/Junkyard/JunkyardBiome_Icon.png")
