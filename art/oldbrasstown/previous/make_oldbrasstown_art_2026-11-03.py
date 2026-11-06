"""ARCHIVED 2026-11-03: the first Weathered Plank Wall (short staggered boards that read as brick), kept in case the
user wants it back. The live generator is art/oldbrasstown/make_oldbrasstown_art.py.

Source for Old Brass Town's blocks, walls and materials (D4), 2026-11-03. Run from the repo root:

    python -P art/oldbrasstown/make_oldbrasstown_art.py

Old Brass Town (user, 2026-11-03: "an old west themed area in the underground desert, like Calamity's Sunken Sea"): a
buried frontier town of weathered boards and tarnished brass in a cavern of brass-veined sandstone. Drawn at 1x in
Cogpunk palette letters (art/scrap/make_scrap_art.py's PAL), exported at 2x nearest-neighbour, lit from the top-left.

Blocks (the standard 16x15-frame terrain sheet from art/templates/terrain_exposure.json, 18 px stride; three variants,
each SEAMLESS inside (D4 rule 7: no per-tile bevel or seam, details at least a pixel inside the tile, the rim shading of
exposed sides kept in the block's own ramp, the outline only on exposed sides; tools/check_tile_seams.py):
    BrassSandstoneTile          the cavern's rock: warm sandstone in strata, a fleck of brass gone green here and there
    TarnishedBrassOreTile       nuggets of brass ringed with verdigris in a darker sandstone matrix
    WeatheredPlankTile          sun-bleached boards, staggered butt joints, nail heads (the town's buildings)
    TarnishedBrassPlatingTile   brass sheets with patina blooms and rivets, plate seams inside the tile (roofs, the bank)
Walls (vanilla's wall frame layout: 13x5 frames on a 36 px stride, a 4-neighbour style picking the frame and 3 variants,
decompiled Framing.wallFrameLookup; each 32x32 frame is the tile and 8 px reaching into its neighbours, so the pattern is
world-aligned (period 8) and the variants only differ inside, where no neighbour overlaps):
    BrassSandstoneWall          the cavern's darker strata behind everything
    WeatheredPlankWall          the buildings' board walls, a ramp step darker than the block
Items (2x): BrassSandstone, TarnishedBrassOre, WeatheredPlank, TarnishedBrassPlating (16x16, the free-standing block),
TarnishedBrassBar (a tarnished ingot), BrassSandstoneWall and WeatheredPlankWall (wall items), and the biome's bestiary
icon OldBrassTownBiome_Icon (30x30).
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
from make_scrap_art import Canvas, PAL, export  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/OldBrassTown/"


# ================================================================================================
# Terrain frames: a block's three 8x8 variants -> the 16x15 sheet (exposed sides outlined, rim-shaded, notched)
# ================================================================================================
class Block:
    def __init__(self, variants, rim_light, rim_dark, outline, notches):
        self.variants, self.rim_light, self.rim_dark, self.outline, self.notches = variants, rim_light, rim_dark, outline, notches

    def frame(self, variant, exposure):
        """8x8 art for one terrain frame. exposure = 'TRBL' with 'o'/'d' (exposed) or '-' (joined)."""
        c = Canvas.from_rows(self.variants[variant])
        top, right, bottom, left = (ch != "-" for ch in exposure)
        nt, nr, nb, nl = self.notches[variant]
        o = self.outline
        for i in range(8):                                   # rim shading just inside exposed edges
            if top:
                c.set(i, 1, self.rim_light.get(c.get(i, 1), c.get(i, 1)))
            if left:
                c.set(1, i, self.rim_light.get(c.get(1, i), c.get(1, i)))
            if bottom:
                c.set(i, 6, self.rim_dark.get(c.get(i, 6), c.get(i, 6)))
            if right:
                c.set(6, i, self.rim_dark.get(c.get(6, i), c.get(6, i)))
        for i in range(8):                                   # the outline on exposed sides only
            if top:
                c.set(i, 0, o)
            if bottom:
                c.set(i, 7, o)
            if left:
                c.set(0, i, o)
            if right:
                c.set(7, i, o)
        if nt is not None:                                   # ragged notches (natural rock only)
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
        for (ex1, ex2, cx, cy, ix, iy) in ((top, left, 0, 0, 1, 1), (top, right, 7, 0, 6, 1),
                                           (bottom, left, 0, 7, 1, 6), (bottom, right, 7, 7, 6, 6)):
            if ex1 and ex2:                                  # rounded outer corners
                c.set(cx, cy, ".")
                c.set(ix, iy, o)
        return c

    def sheet(self):
        table = json.load(open(os.path.join(ROOT, "art/templates/terrain_exposure.json")))
        sheet = Canvas(16 * 9, 15 * 9)                        # 8x8 frames + 1 px gutter = 18 px stride at 2x
        for key, exposure in table.items():
            fx, fy = (int(v) for v in key.split(","))
            sheet.blit(self.frame((fx + fy * 2) % 3, exposure), fx * 9, fy * 9)
        return sheet

    def item(self, variant=0):
        return self.frame(variant, "oooo")


# Brass Sandstone: warm sandstone in strata (rows 2 and 6 darker in every variant, so the beds run on across tiles with
# a period of 4 rows); a brass fleck gone green (G/F with verdigris w) inside one variant, grit in the others.
# Letters (PAL): e/d copper 4/3 (peach, orange), E/F brass 3/4 (ochre, straw), D brass 2, n/m leather 2/1, G brass 5,
# w/v verdigris 2/1.
SANDSTONE = Block(
    variants=[
        ["eEdEeEdE",
         "EeFeEeFe",
         "eDdEdeDd",
         "eEeEFeEe",
         "FeEGweEe",
         "dFeEweFe",
         "DdeDdEed",
         "EeEdFeEd"],
        ["EeFeEdEe",
         "eEeEeFeE",
         "dDeDdEDe",
         "FeEeEeEF",
         "eEdeEeEe",
         "EeEeFdeE",
         "eDdEDdeD",
         "dFeEeEeF"],
        ["eEdEFeEe",
         "FeEeEeEd",
         "DdeDdEDd",
         "eEFeEeFe",
         "EeEeEeEe",
         "eEeGFeEe",
         "dDeDdeDE",
         "EeEFeEdE"],
    ],
    rim_light={"e": "e", "E": "F", "F": "F", "d": "e", "D": "E", "n": "d", "w": "u"},
    rim_dark={"e": "d", "E": "D", "F": "E", "d": "n", "D": "C", "n": "m", "G": "F", "w": "v"},
    outline="m",
    notches=[(5, 5, 2, 2), (2, 3, 5, 5), (6, 4, 3, 1)],
)

# Tarnished Brass Ore: brass nuggets (G/F/E, lit top-left, D shadow) ringed in verdigris (w/v) in a dark sandstone
# matrix (m inside, a lighter n/D at the edges so the tile's border matches its average); every nugget sits at least a
# pixel inside the tile.
ORE = Block(
    variants=[
        ["nnDnnnDn",
         "nGGFnmnD",
         "DFFEDwmn",
         "nEEDvmnD",
         "nwvmnmDn",
         "DmnmnGFD",
         "nmDnmEDn",
         "nnDnnDnD"],
        ["DnnnDnnD",
         "nmnmmGFn",
         "nDwvmEDD",
         "nwuwvmnD",
         "nvwvmnmn",
         "DmvmnDmD",
         "nmnDmmnn",
         "nDnnnDnn"],
        ["DnDDnnDn",
         "nmmnDmmD",
         "DmGFmnwD",
         "nmFEDvmD",
         "nnDvmnmn",
         "nmnmmGFD",
         "DnmnmFDn",
         "nDDDnDnn"],
    ],
    rim_light={"m": "n", "n": "d", "D": "E", "v": "w", "w": "u", "E": "F", "F": "G"},
    rim_dark={"n": "m", "m": "l", "D": "C", "d": "n", "w": "v", "G": "F", "F": "E", "E": "D"},
    outline="l",
    notches=[(4, 3, 2, 5), (2, 5, 5, 2), (5, 2, 3, 4)],
)

# Weathered Planks: boards 3 rows deep (a sun-bleached top edge q, the grain n/m) under a dark gap m on rows 1 and 5, so
# no gap lies on a tile edge and the boards run on across tiles (rows 6, 7 and the next tile's 0 are one board); butt
# joints (l) staggered inside the tile, iron nail heads (k) beside them.
PLANK = Block(
    variants=[
        ["nnmnlnnm",
         "mmmmlmmm",
         "qqnqlqqn",
         "nmnklknn",
         "mnnnlnmn",
         "mmmmmmlm",
         "qnqqqqlq",
         "nnmnnkln"],
        ["nmnlnnmn",
         "mmmlmmmm",
         "qqnlqqnq",
         "nnklknmn",
         "mnnlnnnm",
         "mlmmmmmm",
         "qlqqnqqn",
         "klknnmnn"],
        ["mnnnnnln",
         "mmmmmmlm",
         "nqqqnqlq",
         "nmnnnklk",
         "nnmnnnln",
         "mmlmmmmm",
         "qqlqqnqq",
         "nklknnmn"],
    ],
    rim_light={"n": "q", "m": "n", "q": "r", "l": "m", "k": "q"},
    rim_dark={"n": "m", "q": "n", "m": "l", "k": "j"},
    outline="l",
    notches=[(None, None, None, None)] * 3,
)

# Tarnished Brass Plating: brass sheets (F/E, a bright G glint) with a seam row inside (D, row 3 in every variant: the
# sheets run on in rows), rivets (C dark, G lit) and patina blooms (w/v/u) where the brass has gone green.
PLATING = Block(
    variants=[
        ["FEFFEFEF",
         "EGFEFwvE",
         "FEFCFEFF",
         "DDDDDDDD",
         "FEFFEGFE",
         "EFwFFEFE",
         "FvuEFCFF",
         "EFEFFEFE"],
        ["EFFEFEFF",
         "FCFFGFEF",
         "EFEFEFFE",
         "DDDDDDDD",
         "FEFEwFEF",
         "EFGFvuFE",
         "FEFEFEFC",
         "FFEFEFFE"],
        ["FEFEFFEF",
         "EFwvFEFE",
         "FEuEFCFF",
         "DDDDDDDD",
         "EFCFEFEF",
         "FEFEFGFE",
         "EFEFwFEF",
         "FEFFEFEF"],
    ],
    rim_light={"E": "F", "F": "G", "D": "E", "C": "D", "w": "u", "v": "w"},
    rim_dark={"F": "E", "E": "D", "D": "C", "G": "F", "u": "w", "w": "v"},
    outline="B",
    notches=[(None, None, None, None)] * 3,
)


# ================================================================================================
# Walls: vanilla's wall frame layout (decompiled Framing.wallFrameLookup), 13x5 frames of 16x16 art on an 18 px stride
# ================================================================================================
WALL_LOOKUP = {   # style (1 up, 2 left, 4 right, 8 down; 15 + centre variants 16-19) -> the three variant frames
    0: ((9, 3), (10, 3), (11, 3)), 1: ((6, 3), (7, 3), (8, 3)), 2: ((12, 0), (12, 1), (12, 2)), 3: ((1, 4), (3, 4), (5, 4)),
    4: ((9, 0), (9, 1), (9, 2)), 5: ((0, 4), (2, 4), (4, 4)), 6: ((6, 4), (7, 4), (8, 4)), 7: ((1, 2), (2, 2), (3, 2)),
    8: ((6, 0), (7, 0), (8, 0)), 9: ((5, 0), (5, 1), (5, 2)), 10: ((1, 3), (3, 3), (5, 3)), 11: ((4, 0), (4, 1), (4, 2)),
    12: ((0, 3), (2, 3), (4, 3)), 13: ((0, 0), (0, 1), (0, 2)), 14: ((1, 0), (2, 0), (3, 0)), 15: ((1, 1), (2, 1), (3, 1)),
    16: ((6, 1), (7, 1), (8, 1)), 17: ((6, 2), (7, 2), (8, 2)), 18: ((10, 0), (10, 1), (10, 2)), 19: ((11, 0), (11, 1), (11, 2)),
}


def wall_sheet(texture, outline, detail=None):
    """texture(x, y) -> letter for world-aligned art pixel (x, y) (period 8). Each frame: the tile's 8x8 at (4, 4), plus
    the 4 px borders of the sides that connect (and the corners between two connected sides); an exposed side stops at
    the tile with an outline. detail(variant, x, y) may swap a letter strictly inside the tile (x, y in 5..10), so the
    three variants differ where no neighbour's frame overlaps."""
    sheet = Canvas(13 * 9 * 2, 5 * 9 * 2)                    # 13x5 frames, 18 px (1x) stride
    for style, frames in WALL_LOOKUP.items():
        bits = 15 if style >= 15 else style
        up, left, right, down = bool(bits & 1), bool(bits & 2), bool(bits & 4), bool(bits & 8)
        for variant, (fx, fy) in enumerate(frames):
            c = Canvas(16, 16)
            x0 = 0 if left else 4
            x1 = 16 if right else 12
            y0 = 0 if up else 4
            y1 = 16 if down else 12
            for y in range(y0, y1):
                for x in range(x0, x1):
                    in_x, in_y = 4 <= x < 12, 4 <= y < 12
                    if not in_x and not in_y and not ((x < 4 and left or x >= 12 and right) and (y < 4 and up or y >= 12 and down)):
                        continue                             # a corner only between two connected sides
                    ch = texture((x - 4) % 8, (y - 4) % 8)
                    if detail and 5 <= x <= 10 and 5 <= y <= 10:
                        ch = detail(variant, x, y) or ch
                    c.set(x, y, ch)
            for i in range(4, 12):                           # outline the exposed sides of the tile itself
                if not up:
                    c.set(i, 4, outline)
                if not down:
                    c.set(i, 11, outline)
                if not left:
                    c.set(4, i, outline)
                if not right:
                    c.set(11, i, outline)
            sheet.blit(c, fx * 18, fy * 18)
    return sheet


def sandstone_wall_texture(x, y):
    """Dark strata (a ramp step under the block): beds on rows 2 and 6 like the block's."""
    rows = ["DnDCDnDn",
            "nDnDnDCD",
            "mCmnmCmm",
            "DnDnDCDn",
            "nDCDnDnD",
            "DnDnDnCn",
            "CmmCmnmC",
            "nDnDCDnD"]
    return rows[y][x]


def plank_wall_texture(x, y):
    """Boards a step darker than the block: n/m grain, q -> n tops, the l gap rows; butt joints every 8 px, staggered."""
    rows = ["nmnnlnmn",
            "mmlmlmmm",
            "mlmmlmlm",
            "llllllll",
            "nnmnnnln",
            "mmmlmmlm",
            "lmmmmmlm",
            "llllllll"]
    return rows[y][x]


def sandstone_wall_detail(variant, x, y):
    if variant == 1 and (x, y) == (7, 8):
        return "v"                                           # a speck of green
    if variant == 2 and (x, y) in ((6, 7), (7, 7)):
        return "E"
    return None


def plank_wall_detail(variant, x, y):
    if variant == 1 and (x, y) == (6, 5):
        return "j"                                           # a nail head
    if variant == 2 and (x, y) == (9, 9):
        return "j"
    return None


# ================================================================================================
# Items
# ================================================================================================
def brass_bar():
    """14x10: an ingot of tarnished brass, lit top-left, a patina bloom on its face, a stamped dimple."""
    return Canvas.from_rows([
        "...BBBBBBBBBB.",
        "..BGFFFFGFFFBB",
        ".BFFFEFFFwvFDB",
        "BFFEFFFFFuwEDB",
        "BEEEEEEEEEEDDB",
        "BDDDDDDDDDDCDB",
        "BCCDDCDDDDCCB.",
        "BBBBBBBBBBBBB.",
        "..............",
        "..............",
    ])


def wall_item(texture):
    """12x12: a patch of the wall with an outline (vanilla's wall items show the wall itself)."""
    c = Canvas(12, 12)
    for y in range(12):
        for x in range(12):
            edge = x in (0, 11) or y in (0, 11)
            c.set(x, y, "l" if edge else texture(x % 8, y % 8))
    for (x, y) in ((0, 0), (11, 0), (0, 11), (11, 11)):
        c.set(x, y, ".")
    return c


def biome_icon():
    """30x30 bestiary icon (15x15 art): a false-front building of boards under a brass sign, in its sandstone cave."""
    rows = ["mmmmmmmmmmmmmmm",
            "meEeEeEeEeEeEem",
            "mEe..........em",
            "me..BBBBBBBB..m",
            "mE..BGFFFFEB..m",
            "me..BBBBBBBB..m",
            "mE.lllllllll..m",
            "me.lqqqnqqql..m",
            "mE.lnnlnnmnl..m",
            "me.lqqlrrqql..m",
            "mE.lnmlrrnnl..m",
            "me.lqqlrrqqlE.m",
            "mdDddDddDddDddm",
            "mDdDnDdDnDdDdDm",
            "mmmmmmmmmmmmmmm"]
    return Canvas.from_rows(rows)


def export_all():
    for block, name in ((SANDSTONE, "BrassSandstone"), (ORE, "TarnishedBrassOre"), (PLANK, "WeatheredPlank"), (PLATING, "TarnishedBrassPlating")):
        export(block.sheet(), OUT + "Tiles/%sTile.png" % name)
        export(block.item(), OUT + "Items/%s.png" % name)
    export(wall_sheet(sandstone_wall_texture, "m", sandstone_wall_detail), OUT + "Walls/BrassSandstoneWallTile.png")
    export(wall_sheet(plank_wall_texture, "l", plank_wall_detail), OUT + "Walls/WeatheredPlankWallTile.png")
    export(wall_item(sandstone_wall_texture), OUT + "Items/BrassSandstoneWall.png")
    export(wall_item(plank_wall_texture), OUT + "Items/WeatheredPlankWall.png")
    export(brass_bar(), OUT + "Items/TarnishedBrassBar.png")
    export(biome_icon(), OUT + "OldBrassTownBiome_Icon.png")


if __name__ == "__main__":
    export_all()
