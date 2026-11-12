"""Source for the Fundamental Ruins' sprites (D4), 2026-11-10b (user: "add a new area called Fundamental Ruins ... this area
should be like ancient ruin themed (based on world of warcraft ancient naga ruins, with small puddles of water). The
Fundamental stone of this area should be inside a forcefield"). Run from the repo root:

    python -P art/secrets/make_fundamental_ruins_art.py [--preview FILE]

A sunken temple of sea-worn teal stone: big carved ashlar with a wave-scroll band, crusted with coral where the sea
reached it, its holiest walls set with deep blue rune bricks that still glow; fluted columns and kelp hanging from the
vaults. The Fundamental Stone at its heart sits in a forcefield: a lattice of pale aether light. Drawn at 1x in palette
letters (make_coghaven_art's PAL plus Denim and Aether below, every colour from art/palettes/cogpunk.gpl), exported at 2x
nearest-neighbour, lit from the top-left.

Blocks (the standard 16x15-frame terrain sheet, three seamless variants, outlines only on exposed sides;
tools/check_tile_seams.py; they merge with each other in game, Main.tileMerge, so a wall of mixed blocks is one clump):
    FundamentalBrickTile    teal ashlar in a staggered bond, the joints inside the tile; a carved wave scroll and a
                            barnacle in the variants
    FundamentalCoralTile    the same stone overgrown with coral: pink-red knobs and branches, lit on top
    FundamentalRuneTile     deep blue stone, each block a carved rune (FundamentalRuneTile_Glow: the rune's light)
    FundamentalWardTile     the forcefield: a diamond lattice of aether light, see-through, a bright rim where it ends
                            (FundamentalWardTile_Glow: the lattice again, pulsed in game)
Walls (vanilla's wall frame layout): FundamentalBrickWallTile (the bond a step darker), FundamentalColumnWallTile (fluted
column drums, for pillars two tiles wide).
Decoration: FundamentalKelpTile (1x1 hanging kelp, three strands x two pieces: a stalk and its tip).
Items: the blocks, the walls; the biome icon (a broken arch round a glowing tablet).
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "coghaven"))
import make_coghaven_art as cg  # noqa: E402
from make_coghaven_art import Block, Canvas, export, wall_sheet, wall_item, with_details  # noqa: E402

DENIM = ["g", "h", "i", "j", "q", "r"]                 # Denim 0..5 (art/palettes/cogpunk.gpl)
for _k, _c in zip(DENIM, [(18, 21, 38), (31, 38, 68), (46, 58, 100), (66, 86, 136), (96, 122, 172), (144, 168, 208)]):
    cg.PAL[_k] = _c
AETHER = ["V", "W", "9", "&"]                          # Aether 0..3
for _k, _c in zip(AETHER, [(34, 26, 69), (70, 58, 147), (124, 107, 224), (198, 189, 255)]):
    cg.PAL[_k] = _c

OUT = "Content/Secrets/Ruins/"

# ================================================================================================
# Blocks
# ================================================================================================
# Fundamental Brick: the Verdigris ramp (v w x y) as sea-worn stone; a staggered bond (mortar rows 1 and 5, joints at x 1
# in the upper course and x 5 in the lower, all inside the tile, so every edge is brick body and every variant meets every
# other); each brick lit along its top. The steel-dark '1' is the mortar's deepest shade.
BRICK_BASE = ["wwwwwvxw",
              "vvvvvvvv",
              "xvyxxxxx",
              "wvxwwwww",
              "wvwwwwww",
              "vvvvvvvv",
              "xxxxxvyx",
              "wwwwwvxw"]
BRICK = Block(
    variants=[BRICK_BASE,
              with_details(BRICK_BASE, {(3, 3): "v", (4, 3): "x", (5, 3): "v", (6, 3): "x", (2, 6): "w", (3, 6): "y", (4, 6): "w"}),   # a wave scroll
              with_details(BRICK_BASE, {(3, 3): "t", (4, 3): "s", (3, 4): "s", (6, 6): "o", (5, 6): "m"})],                            # a barnacle, a coral speck
    rim_light={"w": "x", "x": "y", "v": "w", "y": "y"},
    rim_dark={"y": "x", "x": "w", "w": "v", "v": "1", "t": "s", "s": "2", "o": "m"},
    outline="1",
)

# Coralstone: the stone (v w x) grown over with coral: knobs of Crimson (m n o p) lit on top, a branch reaching across; the
# coral sits a pixel inside the tile and the stone between runs on over the edges.
CORAL_BASE = ["wwxwwwxw",
              "wnowwvww",
              "xmnwxwow",
              "wwvwwnpw",
              "wxwopwmw",
              "wwwmnwww",
              "xwwwwxnw",
              "wvwwwwww"]
CORAL = Block(
    variants=[CORAL_BASE,
              with_details(CORAL_BASE, {(2, 2): "p", (3, 2): "o", (2, 3): "n", (5, 6): "o", (6, 6): "p"}),
              with_details(CORAL_BASE, {(1, 5): "o", (2, 5): "p", (2, 4): "n", (6, 1): "o", (6, 2): "n"})],
    rim_light={"w": "x", "x": "y", "v": "w", "n": "o", "o": "p", "m": "n"},
    rim_dark={"y": "x", "x": "w", "w": "v", "v": "1", "p": "o", "o": "n", "n": "m", "m": "l"},
    outline="1",
)

# Rune Brick: deep Denim stone blocks (h i j, joints at row 1 and x 1 inside the tile), a rune carved into each (g: the
# carving's depth; it glows in game through the glow sheet). Each variant a different rune.
RUNE_BASE = ["iiiiiiji",
             "hhhhhhhh",
             "jhjiiiii",
             "ihiiiiii",
             "ihiiiiii",
             "ihiiiiii",
             "ihiiiiii",
             "ihiiiiii"]
RUNES = [{(3, 3): "g", (4, 3): "g", (5, 3): "g", (4, 4): "g", (4, 5): "g", (3, 6): "g", (5, 6): "g"},     # a trident
         {(3, 3): "g", (5, 3): "g", (4, 4): "g", (3, 5): "g", (5, 5): "g", (4, 6): "g"},                    # crossed waves
         {(4, 2): "g", (3, 3): "g", (5, 3): "g", (4, 4): "g", (3, 5): "g", (5, 5): "g", (4, 6): "g"}]       # an eye
RUNE = Block(
    variants=[with_details(RUNE_BASE, r) for r in RUNES],
    rim_light={"i": "j", "j": "q", "h": "i"},
    rim_dark={"j": "i", "i": "h", "h": "g", "q": "j"},
    outline="g",
)


def rune_glow_sheet(sheet):
    """The rune's light: every carved 'g' strictly inside a tile (not the outline) becomes the rune's glow."""
    glow = Canvas(sheet.w, sheet.h)
    for y in range(sheet.h):
        for x in range(sheet.w):
            if sheet.get(x, y) == "g" and 2 <= x % 9 <= 6 and 2 <= y % 9 <= 6:
                glow.set(x, y, "r" if (x + y) % 3 else "u")
    return glow


# Forcefield: a diamond lattice of aether light (lines where (x + y) or (x - y) is a multiple of 4: the lattice runs on
# across tiles, period 8), its crossings brightest; between the lines nothing (the stone shows through). Exposed sides: a
# bright rim (the field's skin) instead of a dark outline.
def ward_base():
    rows = []
    for y in range(8):
        row = ""
        for x in range(8):
            a, b = (x + y) % 4 == 0, (x - y) % 4 == 0
            row += "&" if a and b else ("9" if a or b else ".")
        rows.append(row)
    return rows


class Ward(Block):
    """A see-through block: the lattice inside, the rim on exposed sides (no rim shading: there is no body to shade)."""

    def frame(self, variant, exposure):
        c = Canvas.from_rows(self.variants[variant])
        top, right, bottom, left = (ch != "-" for ch in exposure)
        for i in range(8):
            if top:
                c.set(i, 0, "W" if i % 2 else "9")
            if bottom:
                c.set(i, 7, "W" if i % 2 else "9")
            if left:
                c.set(0, i, "W" if i % 2 else "9")
            if right:
                c.set(7, i, "W" if i % 2 else "9")
        return c


WARD = Ward(variants=[ward_base(), ward_base(), ward_base()], rim_light={}, rim_dark={}, outline="W")


def ward_glow(sheet):
    glow = Canvas(sheet.w, sheet.h)
    for y in range(sheet.h):
        for x in range(sheet.w):
            ch = sheet.get(x, y)
            if ch in ("&", "9"):
                glow.set(x, y, "&" if ch == "&" else "9")
    return glow


# ================================================================================================
# Walls (world-aligned textures, period 8)
# ================================================================================================
def brick_wall_texture(x, y):
    """The bond a ramp step under the block: mortar '1', bricks v, their tops w."""
    rows = ["vvvvv1wv",
            "11111111",
            "w1wwwwww",
            "v1vvvvvv",
            "v1vvvvvv",
            "11111111",
            "wwwww1ww",
            "vvvvv1wv"]
    return rows[y][x]


def brick_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((7, 7), (8, 7)):
        return "w"                                     # a carved notch
    if variant == 2 and (x, y) == (8, 8):
        return "m"                                     # a coral speck
    return None


def column_wall_texture(x, y):
    """Fluted column drums: flutes four pixels across (lit edge x, body w, shadow v, groove 1), a drum joint every eight
    rows (the drums stack)."""
    if y == 0:
        return "1"
    if y == 1:
        return "x"
    return ["x", "w", "w", "v"][x % 4]


# ================================================================================================
# Kelp: 1x1 hanging decoration (8x8 frames on the 18 px stride): frame x = strand (3), frame y = 0 stalk, 1 tip
# ================================================================================================
KELP = [
    (["..xv....",
      "..wv....",
      "...wv...",
      "...xw...",
      "..wv.d..",
      "..xv.c..",
      "...wvb..",
      "...xw..."],
     ["..xv....",
      "..wvd...",
      "...wc...",
      "...xw...",
      "..wv....",
      "...v....",
      "...x....",
      "........"]),
    ([".....wv.",
      "....xv..",
      "....wv..",
      "..d.xw..",
      "..cbwv..",
      ".....wv.",
      ".....xv.",
      ".....wv."],
     [".....wv.",
      "....xv..",
      "....wv..",
      "...xw...",
      "...wv...",
      "....v...",
      "........",
      "........"]),
    (["...wv...",
      "...xv...",
      "....wv..",
      "....xvd.",
      "...wv.c.",
      "...xv...",
      "..wv....",
      "..xv...."],
     ["...wv...",
      "...xv...",
      "....wv..",
      "....xv..",
      "...dw...",
      "...c....",
      "........",
      "........"]),
]


def kelp_sheet():
    sheet = Canvas(3 * 9, 2 * 9)
    for k, (stalk, tip) in enumerate(KELP):
        sheet.blit(Canvas.from_rows(stalk), k * 9, 0)
        sheet.blit(Canvas.from_rows(tip), k * 9, 9)
    return sheet


# ================================================================================================
# The biome icon (30x30 at 2x)
# ================================================================================================
def biome_icon():
    rows = ["...............",
            "....1111111....",
            "...1xwwwwwx1...",
            "..1xw1111wwx1..",
            "..1w1.....1w1..",
            "..1w1.hqh.1w1..",
            "..1w1.qrq.1w1..",
            "..1w1.qrq.1w1..",
            "..1x1.hqh.1x1..",
            "..1w1.hhh.1w..",
            "..1w1.....1...",
            ".11x11111111o1.",
            ".1wwwxwwwwwnp1.",
            ".1vvvvvvvvvvv1.",
            "..11111111111.."]
    rows = [r.ljust(15, ".")[:15] for r in rows]
    return Canvas.from_rows(rows)


def export_all():
    for name, block in (("FundamentalBrick", BRICK), ("FundamentalCoral", CORAL), ("FundamentalRune", RUNE)):
        sheet = block.sheet()
        export(sheet, OUT + "Tiles/%sTile.png" % name)
        export(block.item(), OUT + "Items/%s.png" % name)
        if block is RUNE:
            export(rune_glow_sheet(sheet), OUT + "Tiles/%sTile_Glow.png" % name)
    ward = WARD.sheet()
    export(ward, OUT + "Tiles/FundamentalWardTile.png")
    export(ward_glow(ward), OUT + "Tiles/FundamentalWardTile_Glow.png")
    export(wall_sheet(brick_wall_texture, "1", brick_wall_detail), OUT + "Walls/FundamentalBrickWallTile.png")
    export(wall_item(brick_wall_texture, "1"), OUT + "Items/FundamentalBrickWall.png")
    export(wall_sheet(column_wall_texture, "1"), OUT + "Walls/FundamentalColumnWallTile.png")
    export(wall_item(column_wall_texture, "1"), OUT + "Items/FundamentalColumnWall.png")
    export(kelp_sheet(), OUT + "Tiles/FundamentalKelpTile.png")
    export(biome_icon(), "Content/Secrets/FundamentalRuinsBiome_Icon.png")


def preview(path):
    """A little ruin built from the sheets' item frames: brick, coral, runes, ward, columns, kelp (8x)."""
    cells = [BRICK.item(0), BRICK.item(1), BRICK.item(2), CORAL.item(0), RUNE.item(0), RUNE.item(1), WARD.item(0)]
    im = Image.new("RGBA", (len(cells) * 10, 10), (40, 44, 52, 255))
    for k, c in enumerate(cells):
        im.alpha_composite(c.image(), (k * 10 + 1, 1))
    im.resize((im.width * 8, im.height * 8), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
