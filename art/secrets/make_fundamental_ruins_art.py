"""Source for the Fundamental Ruins' sprites and the Fundamental Stones' shield (D4). First drawn 2026-11-10 (user: "this area
should be like ancient ruin themed (based on world of warcraft ancient naga ruins, with small puddles of water)"; that
version is in previous/); redrawn 2026-11-11 (user: "the colors of the block are too bright, make it darker to fit the
underground ruin theme"; "the blocks of the main arena should be unbreakable"; blocked passages to mine out; "rework the
shield for the fundamental stones: not a physical wall but only an effect/visual cue"). Run from the repo root:

    python -P art/secrets/make_fundamental_ruins_art.py [--preview FILE]

A sunken temple of dark sea-worn stone: the Verdigris ramp's deep end (v w, a rare lit x) over near-black mortar (steel 0),
crusted with dark coral where the sea reached it, its holiest walls in deep blue rune bricks that still glow; the arena
built of Ancient Brick (slate blocks with verdigris seams and a carved groove: it reads as a different, older stone, and it
is the one that can't be broken); collapses of rubble in the tunnels. Drawn at 1x in palette letters (make_coghaven_art's
PAL plus Denim and Aether below, every colour from art/palettes/cogpunk.gpl), exported at 2x nearest-neighbour, lit from
the top-left.

Blocks (the standard 16x15-frame terrain sheet, three seamless variants, outlines only on exposed sides;
tools/check_tile_seams.py; in game they all merge, Main.tileMerge, so a wall of mixed blocks is one clump):
    FundamentalBrickTile       dark teal ashlar in a staggered bond, the joints inside the tile; a wave scroll, a barnacle
    FundamentalCoralTile       the same stone overgrown with dark coral
    FundamentalRuneTile        deep blue stone, a carved rune in each block (FundamentalRuneTile_Glow: the rune's light);
                               the arena's unbreakable rune bricks use the same sheets
    FundamentalArenaBrickTile  Ancient Brick: slate ashlar with verdigris mortar and a carved groove (unbreakable in game)
    FundamentalRubbleTile      a collapse: broken stone chunks in dark gaps, ragged where exposed (the passages to mine out)
Walls (vanilla's wall frame layout): FundamentalBrickWallTile (the bond in near-black), FundamentalColumnWallTile (fluted
drums, dark).
Decoration: FundamentalKelpTile (1x1 hanging kelp, three strands x two pieces: a stalk and its tip).
The shield: Content/Secrets/FundamentalShield.png, 6 frames of a 52x64 (1x) dome round a Fundamental Stone: a rim of aether
light and a diamond lattice drifting upward inside it (the lattice repeats every 6 rows, so the six frames loop), drawn in
game additively and pulsing, over the stone while its guardian lives.
Items: the blocks and walls a player can mine; the biome icon.
"""
import argparse
import math
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
# Fundamental Brick (dark): Verdigris w bodies shaded to v low in each course, near-black mortar (steel 0) in rows 1 and 5
# and the joints at x 1 (upper course) and x 5 (lower course), all inside the tile; each brick's top lit with a single x.
BRICK_BASE = ["wwwwv0ww",
              "00000000",
              "w0xwwwww",
              "v0wwwvww",
              "v0vvwvvv",
              "00000000",
              "wwwww0xw",
              "vvwvv0vv"]
BRICK = Block(
    variants=[BRICK_BASE,
              with_details(BRICK_BASE, {(3, 3): "v", (4, 3): "x", (5, 3): "v", (6, 3): "w", (2, 6): "v", (3, 6): "x", (4, 6): "v"}),   # a wave scroll
              with_details(BRICK_BASE, {(3, 3): "2", (4, 3): "3", (3, 4): "2", (6, 6): "m", (6, 4): "l"})],                            # a barnacle, coral specks
    rim_light={"w": "x", "v": "w", "0": "v", "x": "x"},
    rim_dark={"x": "w", "w": "v", "v": "0", "3": "2", "2": "1", "m": "l"},
    outline="0",
)

# Coralstone (dark): the stone (v w) grown over with dark coral, knobs of Crimson l m n with a rare o lit on top; the coral
# sits a pixel inside the tile and the stone between runs on over the edges.
CORAL_BASE = ["wvwwvwww",
              "vmnvwlwv",
              "wlmvwvnw",
              "vvwvwmov",
              "wvvnovlv",
              "vwvlmvvw",
              "wvvvvwmv",
              "vwwvwvvw"]
CORAL = Block(
    variants=[CORAL_BASE,
              with_details(CORAL_BASE, {(2, 2): "o", (3, 2): "n", (2, 3): "m", (5, 6): "n", (6, 6): "o"}),
              with_details(CORAL_BASE, {(1, 5): "n", (2, 5): "o", (2, 4): "m", (6, 1): "n", (6, 2): "m"})],
    rim_light={"w": "x", "v": "w", "m": "n", "n": "o", "l": "m"},
    rim_dark={"x": "w", "w": "v", "v": "0", "o": "n", "n": "m", "m": "l", "l": "k"},
    outline="0",
)

# Rune Brick: deep Denim stone blocks (h i, joints at row 1 and x 1 inside the tile), a rune carved into each (g: the
# carving's depth; it glows in game through the glow sheet). Each variant a different rune.
RUNE_BASE = ["hhhhhhih",
             "gggggggg",
             "igiihhhh",
             "hghhhhhh",
             "hghhhhhh",
             "hghhhhhh",
             "hghhhhhh",
             "hghhhhhh"]
RUNES = [{(3, 3): "g", (4, 3): "g", (5, 3): "g", (4, 4): "g", (4, 5): "g", (3, 6): "g", (5, 6): "g"},     # a trident
         {(3, 3): "g", (5, 3): "g", (4, 4): "g", (3, 5): "g", (5, 5): "g", (4, 6): "g"},                    # crossed waves
         {(4, 2): "g", (3, 3): "g", (5, 3): "g", (4, 4): "g", (3, 5): "g", (5, 5): "g", (4, 6): "g"}]       # an eye
RUNE = Block(
    variants=[with_details(RUNE_BASE, r) for r in RUNES],
    rim_light={"h": "i", "i": "j"},
    rim_dark={"i": "h", "h": "g", "j": "i"},
    outline="g",
)


def rune_glow_sheet(sheet):
    """The rune's light: every carved 'g' strictly inside a tile (not the outline, not the mortar rows) glows."""
    glow = Canvas(sheet.w, sheet.h)
    for y in range(sheet.h):
        for x in range(sheet.w):
            if sheet.get(x, y) == "g" and 2 <= x % 9 <= 6 and 2 <= y % 9 <= 6:
                glow.set(x, y, "r" if (x + y) % 3 else "u")
    return glow


# Ancient Brick (the arena, unbreakable in game): slate ashlar (steel 1 2 3) in the same staggered bond as the brick, its
# mortar Verdigris (v: the sea in the joints), a carved groove (steel 1) along the middle of each course and its top lit
# with a steel 4: an older, harder stone that doesn't read as the brick around it.
ARENA_BASE = ["22223v23",
              "vvvvvvvv",
              "2v422222",
              "1v111111",
              "2v322232",
              "vvvvvvvv",
              "33333v43",
              "11111v11"]
ARENA = Block(
    variants=[ARENA_BASE,
              with_details(ARENA_BASE, {(3, 3): "0", (4, 3): "0", (5, 6): "4", (6, 6): "3"}),     # a chip in the groove
              with_details(ARENA_BASE, {(4, 2): "w", (5, 2): "v", (4, 4): "w"})],                   # verdigris weeping
    rim_light={"2": "3", "3": "4", "1": "2", "v": "w", "4": "4"},
    rim_dark={"4": "3", "3": "2", "2": "1", "1": "0", "v": "0", "w": "v"},
    outline="0",
)


class Rubble(Block):
    """A collapse: ragged notches where exposed (natural, not masonry), the cut corners kept."""

    NOTCHES = [(5, 2, 3, 6), (2, 5, 6, 3), (6, 4, 1, 4)]   # (top x, right y, bottom x, left y) per variant

    def frame(self, variant, exposure):
        c = super().frame(variant, exposure)
        top, right, bottom, left = (ch != "-" for ch in exposure)
        nt, nr, nb, nl = self.NOTCHES[variant]
        o = self.outline
        if top:
            c.set(nt, 0, ".")
            c.set(nt, 1, o)
        if bottom:
            c.set(nb, 7, ".")
            c.set(nb, 6, o)
        if left:
            c.set(0, nl, ".")
            c.set(1, nl, o)
        if right:
            c.set(7, nr, ".")
            c.set(6, nr, o)
        return c


# Rubble: broken chunks of the ruins' stone (w v) and slate (2 1) jumbled with near-black gaps (0) between them, a chunk's
# top lit (x 3): the passages a collapse closed, mined out to go on.
RUBBLE_BASE = ["wvv02w3v",
               "vv0221v0",
               "00w0x10w",
               "x0vw0vww",
               "wv0vv0v0",
               "0v220wv0",
               "w01v0vwx",
               "v0wv0v0v"]
RUBBLE = Rubble(
    variants=[RUBBLE_BASE,
              with_details(RUBBLE_BASE, {(2, 3): "x", (3, 3): "w", (5, 5): "3", (6, 6): "v"}),
              with_details(RUBBLE_BASE, {(1, 1): "3", (2, 1): "2", (4, 4): "x", (5, 4): "0"})],
    rim_light={"w": "x", "v": "w", "2": "3", "1": "2"},
    rim_dark={"x": "w", "w": "v", "v": "0", "3": "2", "2": "1", "1": "0"},
    outline="0",
)


# ================================================================================================
# Walls (world-aligned textures, period 8)
# ================================================================================================
def brick_wall_texture(x, y):
    """The bond in near-black: mortar 0, bricks 1 (steel), their tops v."""
    rows = ["11111011",
            "00000000",
            "v0vvvvvv",
            "10111111",
            "10111111",
            "00000000",
            "vvvvv0vv",
            "11111011"]
    return rows[y][x]


def brick_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((7, 7), (8, 7)):
        return "v"                                     # a carved notch
    if variant == 2 and (x, y) == (8, 8):
        return "l"                                     # a coral speck
    return None


def column_wall_texture(x, y):
    """Fluted column drums, dark: flutes four pixels across (lit edge w, body v, shadow 1, groove 0), a drum joint every
    eight rows (the drums stack)."""
    if y == 0:
        return "0"
    if y == 1:
        return "w"
    return ["w", "v", "v", "1"][x % 4]


# ================================================================================================
# Kelp: 1x1 hanging decoration (8x8 frames on the 18 px stride): frame x = strand (3), frame y = 0 stalk, 1 tip
# ================================================================================================
KELP = [
    (["..wv....",
      "..vv....",
      "...wv...",
      "...wv...",
      "..wv.d..",
      "..wv.c..",
      "...vvb..",
      "...wv..."],
     ["..wv....",
      "..wvd...",
      "...wc...",
      "...wv...",
      "..wv....",
      "...v....",
      "...w....",
      "........"]),
    ([".....wv.",
      "....wv..",
      "....vv..",
      "..d.wv..",
      "..cbwv..",
      ".....wv.",
      ".....wv.",
      ".....vv."],
     [".....wv.",
      "....wv..",
      "....vv..",
      "...wv...",
      "...vv...",
      "....v...",
      "........",
      "........"]),
    (["...wv...",
      "...wv...",
      "....vv..",
      "....wvd.",
      "...wv.c.",
      "...wv...",
      "..vv....",
      "..wv...."],
     ["...wv...",
      "...wv...",
      "....vv..",
      "....wv..",
      "...dv...",
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
# The Fundamental Stones' shield: a dome of aether light, 6 frames
# ================================================================================================
SHIELD_W, SHIELD_H, SHIELD_FRAMES = 52, 64, 6
SHIELD_STONE = (10, 16)                                # the stone's top-left inside the shield's frame (1x)


def shield_frame(k):
    """The dome: straight sides up to a round top (a capsule standing on the ground), a two-pixel rim (& outside, 9
    inside), inside it a diamond lattice (W, a 9 where its lines cross) drifting up a pixel a frame, and three sparks
    climbing the rim. Open at the bottom (it stands on the stone's floor)."""
    c = Canvas(SHIELD_W, SHIELD_H)
    cx, top_r = (SHIELD_W - 1) / 2.0, SHIELD_W / 2.0 - 0.5
    cy = top_r                                         # the round top's centre

    def inside(x, y, shrink=0.0):
        r = top_r - shrink
        if y + 0.5 >= cy:
            return abs(x + 0.5 - (cx + 0.5)) <= r
        return math.hypot(x + 0.5 - (cx + 0.5), y + 0.5 - cy) <= r

    for y in range(SHIELD_H):
        for x in range(SHIELD_W):
            if not inside(x, y):
                continue
            if not inside(x, y, 1.0):
                c.set(x, y, "&")                       # the outer rim
            elif not inside(x, y, 2.0):
                c.set(x, y, "9")                       # its inner glow
            else:
                yy = y + k                             # the lattice drifts up a pixel a frame (period 6: the frames loop)
                a, b = (x + yy) % 6 == 0, (x - yy) % 6 == 0
                if a and b:
                    c.set(x, y, "9")
                elif a or b:
                    c.set(x, y, "W")
    for s in range(3):                                 # sparks climbing the rim, one a third of the way round each
        t = ((k + 2 * s) % SHIELD_FRAMES) / SHIELD_FRAMES
        ang = math.pi * (1.0 - t)                      # from the left side over the top to the right
        x = int(round(cx + math.cos(ang) * (top_r - 1)))
        y = int(round(cy - math.sin(ang) * (top_r - 1)))
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            c.set(x + dx, y + dy, "u")
    return c


def shield_sheet():
    sheet = Canvas(SHIELD_W, (SHIELD_H + 1) * SHIELD_FRAMES - 1)
    for k in range(SHIELD_FRAMES):
        sheet.blit(shield_frame(k), 0, k * (SHIELD_H + 1))
    return sheet


# ================================================================================================
# The biome icon (30x30 at 2x)
# ================================================================================================
def biome_icon():
    rows = ["...............",
            "....0000000....",
            "...0wvvvvvw0...",
            "..0wv0000vvw0..",
            "..0v0.....0v0..",
            "..0v0.hqh.0v0..",
            "..0v0.qrq.0v0..",
            "..0v0.qrq.0v0..",
            "..0w0.hqh.0w0..",
            "..0v0.hhh.0v...",
            "..0v0.....0....",
            ".00w00000000n0.",
            ".0vvvwvvvvvmo0.",
            ".01111111111110",
            "..00000000000.."]
    rows = [r.ljust(15, ".")[:15] for r in rows]
    return Canvas.from_rows(rows)


def export_all():
    for name, block in (("FundamentalBrick", BRICK), ("FundamentalCoral", CORAL), ("FundamentalRune", RUNE),
                        ("FundamentalArenaBrick", ARENA), ("FundamentalRubble", RUBBLE)):
        sheet = block.sheet()
        export(sheet, OUT + "Tiles/%sTile.png" % name)
        if name in ("FundamentalBrick", "FundamentalCoral", "FundamentalRune"):
            export(block.item(), OUT + "Items/%s.png" % name)
        if block is RUNE:
            export(rune_glow_sheet(sheet), OUT + "Tiles/%sTile_Glow.png" % name)
    for stale in ("Tiles/FundamentalWardTile.png", "Tiles/FundamentalWardTile_Glow.png"):   # the ward is a drawn shield now
        path = os.path.join(os.getcwd(), OUT + stale)
        if os.path.exists(path):
            os.remove(path)
    export(wall_sheet(brick_wall_texture, "0", brick_wall_detail), OUT + "Walls/FundamentalBrickWallTile.png")
    export(wall_item(brick_wall_texture, "0"), OUT + "Items/FundamentalBrickWall.png")
    export(wall_sheet(column_wall_texture, "0"), OUT + "Walls/FundamentalColumnWallTile.png")
    export(wall_item(column_wall_texture, "0"), OUT + "Items/FundamentalColumnWall.png")
    export(kelp_sheet(), OUT + "Tiles/FundamentalKelpTile.png")
    export(shield_sheet(), "Content/Secrets/FundamentalShield.png")
    export(biome_icon(), "Content/Secrets/FundamentalRuinsBiome_Icon.png")


def preview(path):
    """The blocks' item frames side by side and a shield frame over dark (8x)."""
    cells = [BRICK.item(0), BRICK.item(1), CORAL.item(0), RUNE.item(0), ARENA.item(0), RUBBLE.item(0)]
    im = Image.new("RGBA", (len(cells) * 10 + SHIELD_W + 4, SHIELD_H + 2), (30, 30, 36, 255))
    for k, c in enumerate(cells):
        im.alpha_composite(c.image(), (k * 10 + 1, 1))
    im.alpha_composite(shield_frame(0).image(), (len(cells) * 10 + 2, 1))
    im.resize((im.width * 6, im.height * 6), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
