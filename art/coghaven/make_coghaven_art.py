"""Source for Coghaven's sprites (D4), 2026-11-06. Run from the repo root:

    python -P art/coghaven/make_coghaven_art.py

Coghaven (user, 2026-11-06): a floating island twice the size of a vanilla cloud island, always over the right side of
the map just before the ocean's beach; a base of cloud and cogs held up (in look only) by steam turbines that pump smoke,
and on it a steampunk jade palace in red, bronze and jade, built like a detailed dungeon. Drawn at 1x in Cogpunk palette
letters (PAL below, every colour from art/palettes/cogpunk.gpl: the Ghost ramp is the jade, Crimson the cinnabar lacquer,
Brass/Gilt and Copper the bronze, Verdigris its patina), exported at 2x nearest-neighbour, lit from the top-left.

Blocks (the standard 16x15-frame terrain sheet from art/templates/terrain_exposure.json on an 18 px stride; three
variants, each SEAMLESS inside: no per-tile bevel or seam, details at least a pixel inside the tile, the rim shading of
exposed sides in the block's own ramp, the outline only on exposed sides; tools/check_tile_seams.py):
    PalaceFlagstoneTile   pale stone pavers (2026-11-06, second request: "the floor should not be jade brick, only the roof"),
                          the joints inside the tile, a bronze stud where they cross now and then: every floor of the palace
    JadeBrickTile         polished jade bricks in a staggered bond, the joints inside the tile; a gilt stud now and then
                          (no longer generated; a building block crafted from stone and an emerald)
    CinnabarLacquerTile   red lacquered boards (vertical grain, glossy), gilt nail heads: the palace's pillars and beams
    BronzeGearworkTile    aged bronze machinery, a gear-rack band across it, rivets and verdigris: the island's core
    JadeRoofTile          glazed roof tiles: tubes and channels running down the roof, a gold-glazed tube here and there
Walls (vanilla's wall frame layout, 13x5 frames on a 36 px stride, world-aligned pattern of period 8):
    PalaceFlagstoneWall (the pavers a shade darker: the pagoda's rooms, the shrine, the terraces), JadeBrickWall, CinnabarPanelWall (lacquered panels with gilt studs), BronzeLatticeWall (a fret "window" lattice,
    see-through), BronzeGearworkWall
Furniture-like tiles (frames of whole objects on the 18 px tile stride, AnimationFrameHeight in their .cs):
    LiftTurbineTile       4x6 tiles, 4 frames: a brass turbine that hangs under the island, its rotor turning behind the
                          intake window, smoke pouring from its nozzle (TurbineSmoke dust); _Glow: the fire inside
    BronzeCogTile         6x6 tiles, 12 frames: a bronze cog with a jade hub turning 5 degrees a frame (60 degrees: its
                          six spokes repeat); lit in screen space from the top-left, so the light stays put as it turns
Dust: TurbineSmoke (4 puff sizes). Items: every block and wall, the turbine and the cog; the biome icon.
"""
import json
import math
import os

from PIL import Image

ROOT = os.getcwd()
OUT = "Content/Coghaven/"

PAL = {
    # Ghost 0-5: jade
    "a": (10, 34, 32), "b": (18, 70, 58), "c": (30, 114, 88), "d": (58, 166, 118), "e": (118, 220, 162), "f": (196, 250, 214),
    # Verdigris 0-3: patina
    "v": (23, 52, 48), "w": (42, 94, 82), "x": (71, 145, 126), "y": (140, 201, 176),
    # Crimson 0-5: cinnabar lacquer
    "k": (44, 12, 18), "l": (84, 20, 28), "m": (126, 30, 36), "n": (168, 44, 42), "o": (206, 74, 56), "p": (236, 122, 88),
    # Brass / Gilt: bronze
    "A": (43, 26, 14), "B": (90, 58, 23), "C": (114, 74, 27), "D": (138, 93, 34), "E": (162, 116, 42), "F": (184, 138, 51),
    "G": (205, 163, 63), "H": (223, 185, 78), "I": (246, 231, 161),
    # Copper
    "P": (42, 18, 12), "Q": (94, 40, 23), "R": (147, 68, 31), "S": (196, 104, 58), "T": (233, 160, 107),
    # Iron / Steel
    "0": (21, 22, 28), "1": (46, 50, 59), "2": (61, 66, 78), "3": (79, 85, 98), "4": (102, 109, 123), "5": (127, 135, 148),
    "6": (155, 163, 175), "7": (183, 191, 202), "8": (224, 230, 236),
    # Steam
    "s": (138, 144, 150), "t": (195, 200, 205), "u": (238, 241, 243), "U": (255, 255, 255),
    # Ember
    "X": (77, 20, 10), "Y": (163, 48, 26), "Z": (236, 113, 40), "z": (255, 199, 90),
    # Ivory 0-5: the palace's pale flagstone
    "J": (52, 38, 30), "K": (104, 84, 64), "L": (152, 132, 104), "M": (196, 180, 150), "N": (228, 218, 192), "O": (250, 246, 230),
}


class Canvas:
    """A grid of palette letters ('.' = transparent) with bounds-checked writes."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [["."] * w for _ in range(h)]

    @staticmethod
    def from_rows(rows):
        c = Canvas(len(rows[0]), len(rows))
        for y, row in enumerate(rows):
            assert len(row) == c.w, "ragged row %d: %r" % (y, row)
            c.g[y] = list(row)
        return c

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else "."

    def set(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                if other.g[y][x] != ".":
                    self.set(ox + x, oy + y, other.g[y][x])

    def image(self):
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = img.load()
        for y in range(self.h):
            for x in range(self.w):
                ch = self.g[y][x]
                if ch != ".":
                    px[x, y] = PAL[ch] + (255,)
        return img


def export(canvas_or_img, rel_path):
    img = canvas_or_img.image() if isinstance(canvas_or_img, Canvas) else canvas_or_img
    out = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print("wrote %s (%dx%d)" % (rel_path, img.width * 2, img.height * 2))


# ================================================================================================
# Blocks: three 8x8 variants -> the 16x15 terrain sheet (exposed sides outlined and rim-shaded)
# ================================================================================================
class Block:
    def __init__(self, variants, rim_light, rim_dark, outline):
        self.variants, self.rim_light, self.rim_dark, self.outline = variants, rim_light, rim_dark, outline

    def frame(self, variant, exposure):
        """8x8 art for one terrain frame. exposure = 'TRBL' with 'o'/'d' (exposed) or '-' (joined)."""
        c = Canvas.from_rows(self.variants[variant])
        top, right, bottom, left = (ch != "-" for ch in exposure)
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
        for (ex1, ex2, cx, cy, ix, iy) in ((top, left, 0, 0, 1, 1), (top, right, 7, 0, 6, 1),
                                           (bottom, left, 0, 7, 1, 6), (bottom, right, 7, 7, 6, 6)):
            if ex1 and ex2:                                  # cut outer corners (masonry, not rock: no ragged notches)
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


def with_details(base, details):
    rows = [list(r) for r in base]
    for (x, y), ch in details.items():
        assert 1 <= x <= 6 and 1 <= y <= 6, "a detail must sit a pixel inside the tile: %r" % ((x, y),)
        rows[y][x] = ch
    return ["".join(r) for r in rows]


# Palace Flagstone: square pavers, the joints on column 3 and row 5 (inside the tile, so the edges are paver body and every
# variant meets every other); each paver lit along its top and left edges (the row under the joint, the column right of
# it), shaded along its bottom and right; a speckled stone face; a hairline crack and a bronze stud in the variants.
FLAGSTONE_BASE = ["MMLKNMLM",
                  "MLMKNMMM",
                  "LMMKNMLM",
                  "MMLKNMMM",
                  "LLLKLLLL",
                  "KKKKKKKK",
                  "NNNKNNNN",
                  "MMLKNMLM"]
FLAGSTONE = Block(
    variants=[FLAGSTONE_BASE,
              with_details(FLAGSTONE_BASE, {(5, 1): "L", (6, 2): "L", (6, 3): "K", (1, 2): "N"}),
              with_details(FLAGSTONE_BASE, {(3, 5): "G", (2, 4): "E", (4, 6): "H", (3, 4): "C"})],
    rim_light={"M": "N", "L": "M", "N": "O", "K": "L"},
    rim_dark={"N": "M", "M": "L", "L": "K", "K": "J", "G": "E", "H": "G"},
    outline="J",
)

# Jade Brick: staggered bond, mortar rows 1 and 5 and the joints (x 1 in the upper course, x 5 in the lower) all inside
# the tile, so the edges are brick body and every variant meets every other; each brick lit along its top with a glint
# where it begins. Courses: rows 2-4 and rows 6, 7 and 0 (the lower course runs on into the tile below).
JADE_BRICK_BASE = ["ccccbcdc",
                   "bbbbbbbb",
                   "dbeddddd",
                   "cbdccccc",
                   "cbcccccc",
                   "bbbbbbbb",
                   "dddddbed",
                   "cccccbdc"]
JADE_BRICK = Block(
    variants=[JADE_BRICK_BASE,
              with_details(JADE_BRICK_BASE, {(4, 2): "e", (5, 3): "d", (2, 6): "e", (3, 6): "e"}),
              with_details(JADE_BRICK_BASE, {(3, 3): "H", (4, 3): "G", (3, 4): "G", (4, 4): "E"})],
    rim_light={"c": "d", "d": "e", "b": "c", "e": "e"},
    rim_dark={"d": "c", "c": "b", "e": "d", "b": "a", "H": "G", "G": "E"},
    outline="a",
)

# Cinnabar Lacquer: boards four pixels wide (grooves at x 1 and 5, inside the tile), each lit on its left and glossy;
# the board that runs over the tile's edge keeps its mid shade on both sides of it (columns 7 and 0), so the edges sit at
# the block's average brightness (check_tile_seams' edge bias); gilt nail heads and a knot in the variants.
LACQUER_BASE = ["nlonmlon",
                "nlonmlon",
                "nlpnmlon",
                "nlonmlpn",
                "nlonmlon",
                "nlnnmlon",
                "nlonmlnn",
                "nlonmlon"]
LACQUER = Block(
    variants=[LACQUER_BASE,
              with_details(LACQUER_BASE, {(2, 3): "H", (2, 4): "E", (6, 3): "H", (6, 4): "E"}),
              with_details(LACQUER_BASE, {(3, 4): "l", (3, 5): "m", (6, 1): "p", (6, 2): "p"})],
    rim_light={"m": "n", "n": "o", "o": "p", "l": "m"},
    rim_dark={"o": "n", "n": "m", "m": "l", "l": "k", "p": "o", "H": "G", "E": "C"},
    outline="k",
)

# Bronze Gearwork: a plate with a gear-rack band (teeth every 2 px, so the band runs on across tiles) over a dark seam
# row, rivets, a cog boss and verdigris in the variants.
GEARWORK_BASE = ["DDCDDDCD",
                 "EEEEEEEE",
                 "EBEBEBEB",
                 "DBDBDBDB",
                 "BBBBBBBB",
                 "DEDDDEDD",
                 "DDDCDDDC",
                 "CDDDCDDD"]
GEARWORK = Block(
    variants=[with_details(GEARWORK_BASE, {(2, 5): "H", (3, 6): "B"}),
              with_details(GEARWORK_BASE, {(4, 6): "x", (5, 6): "w", (5, 5): "x"}),
              with_details(GEARWORK_BASE, {(2, 5): "G", (3, 5): "C", (4, 5): "G", (2, 6): "C", (3, 6): "H", (4, 6): "C"})],
    rim_light={"D": "E", "E": "G", "C": "D", "B": "C"},
    rim_dark={"E": "D", "D": "C", "C": "B", "G": "E", "B": "A", "H": "G"},
    outline="A",
)

# Vault Gearwork (2026-11-16, the Jade Vault's unbreakable shell): the gearwork a shade darker, hardened, its gear rack inlaid
# with jade teeth, jade studs in the variants: it reads as the island's machinery but not the same block.
VAULT_BASE = ["CCBCCCBC",
              "DDDDDDDD",
              "DcDcDcDc",
              "CbCbCbCb",
              "BBBBBBBB",
              "CDCCCDCC",
              "CCCBCCCB",
              "BCCCBCCC"]
VAULT = Block(
    variants=[with_details(VAULT_BASE, {(2, 5): "e", (3, 6): "b"}),
              with_details(VAULT_BASE, {(5, 5): "d", (5, 6): "b", (4, 6): "c"}),
              with_details(VAULT_BASE, {(2, 6): "d", (3, 6): "e", (4, 6): "d", (3, 5): "c"})],
    rim_light={"C": "D", "D": "E", "B": "C", "c": "d", "b": "c"},
    rim_dark={"D": "C", "C": "B", "E": "D", "B": "A", "d": "c", "e": "d", "c": "b"},
    outline="A",
)

# Jade Roof Tiles: glazed tubes three pixels wide (lit edge d, body c c: x 2-4 and 6-7-0) and narrow channels (b: x 1 and
# 5) running down the roof; the tile's edge falls inside a tube, so both edge columns sit at the average (check_tile_seams).
# The tile courses end on rows 1 and 5 (each tube's pale glazed cap, a dark gap in each channel); a gold-glazed tube and
# a glint in the variants.
ROOF_BASE = ["cbdccbdc",
             "daeddaed",
             "cbdccbdc",
             "cbdccbdc",
             "cbdccbdc",
             "daeddaed",
             "cbdccbdc",
             "cbdccbdc"]
ROOF = Block(
    variants=[ROOF_BASE,
              with_details(ROOF_BASE, {(2, 3): "H", (3, 3): "G", (2, 4): "G", (3, 4): "E"}),
              with_details(ROOF_BASE, {(2, 3): "e", (3, 3): "d", (6, 2): "e"})],
    rim_light={"c": "d", "d": "e", "b": "c", "e": "f", "a": "b"},
    rim_dark={"e": "d", "d": "c", "c": "b", "b": "a", "f": "e", "H": "G", "G": "E"},
    outline="a",
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
    the tile with an outline. detail(variant, x, y) may swap a letter strictly inside the tile (x, y in 5..10)."""
    sheet = Canvas(13 * 9 * 2, 5 * 9 * 2)
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
                        continue
                    ch = texture((x - 4) % 8, (y - 4) % 8)
                    if detail and 5 <= x <= 10 and 5 <= y <= 10:
                        ch = detail(variant, x, y) or ch
                    c.set(x, y, ch)
            for i in range(4, 12):
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


def flagstone_wall_texture(x, y):
    """The pavers a ramp step under the block: joints K, bodies L, lit edges M."""
    rows = ["LLKJMLLL",
            "LKLJMLLL",
            "KLLJMLKL",
            "LLLJMLLL",
            "KKKJKKKK",
            "JJJJJJJJ",
            "MMMJMMMM",
            "LLKJMLKL"]
    return rows[y][x]


def flagstone_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((9, 6), (9, 7)):
        return "K"
    if variant == 2 and (x, y) == (7, 9):
        return "E"
    return None


def jade_wall_texture(x, y):
    """The brick bond a ramp step under the block: mortar a, bricks b, their tops c."""
    rows = ["bbbbabcb",
            "aaaaaaaa",
            "cadccccc",
            "babbbbbb",
            "babbbbbb",
            "aaaaaaaa",
            "cccccacd",
            "bbbbbacb"]
    return rows[y][x]


def jade_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((7, 7), (8, 6)):
        return "d"
    if variant == 2 and (x, y) == (8, 7):
        return "F"
    return None


def panel_wall_texture(x, y):
    """Lacquered panels a tile square: a dark frame line, a lit bevel under it, a shaded one at the far side, a gilt
    stud in the corner."""
    if x == 0 or y == 0:
        return "k"
    if (x, y) == (1, 1):
        return "G"
    if x == 1 or y == 1:
        return "n"
    if x == 7 or y == 7:
        return "l"
    return "m"


def panel_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((8, 8),):
        return "H"
    if variant == 1 and (x, y) in ((9, 9),):
        return "E"
    if variant == 2 and (x, y) in ((7, 9), (7, 10)):
        return "l"
    return None


def lattice_wall_texture(x, y):
    """A bronze fret lattice, see-through: a bar along the tile's top and left, a square ring inside (the 'hui'
    fret), lit on top and left."""
    rows = ["GGGGGGGG",
            "E.......",
            "E.FFFF..",
            "E.E..D..",
            "E.E..D..",
            "E.DDDD..",
            "E.......",
            "E......."]
    return rows[y][x]


def gearwork_wall_texture(x, y):
    rows = ["CCBCCCBC",
            "DDDDDDDD",
            "DBDBDBDB",
            "CBCBCBCB",
            "BBBBBBBB",
            "CDCCCDCC",
            "CCCBCCCB",
            "BCCCBCCC"]
    return rows[y][x]


def gearwork_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((7, 9), (8, 9)):
        return "w"
    if variant == 2 and (x, y) == (6, 9):
        return "G"
    return None


def vault_wall_texture(x, y):
    rows = ["BBABBBAB",
            "CCCCCCCC",
            "CbCbCbCb",
            "BbBbBbBb",
            "BBBBBBBB",
            "BCBBBCBB",
            "BBBCBBBC",
            "CBBBCBBB"]
    return rows[y][x]


def vault_wall_detail(variant, x, y):
    if variant == 1 and (x, y) in ((7, 9), (8, 9)):
        return "c"
    if variant == 2 and (x, y) == (6, 9):
        return "d"
    return None


def wall_item(texture, outline):
    """12x12: a patch of the wall with an outline (vanilla's wall items show the wall itself)."""
    c = Canvas(12, 12)
    for y in range(12):
        for x in range(12):
            edge = x in (0, 11) or y in (0, 11)
            c.set(x, y, outline if edge else texture(x % 8, y % 8))
    for (x, y) in ((0, 0), (11, 0), (0, 11), (11, 11)):
        c.set(x, y, ".")
    return c


# ================================================================================================
# Shading helpers for the furniture-like tiles
# ================================================================================================
GILT = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]          # dark -> light
JADE = ["a", "b", "c", "d", "e", "f"]
STEEL = ["0", "1", "2", "3", "4", "5", "6", "7", "8"]
COPPER = ["P", "Q", "R", "S", "T"]


def ramp(r, t):
    """t in 0..1 -> a letter of ramp r (whole steps, no dithering)."""
    return r[max(0, min(len(r) - 1, int(round(t * (len(r) - 1)))))]


def outline_pass(c, outline_of, lit_outline_of=None):
    """Outlines every pixel that touches transparency (4-neighbour) with its ramp's darkest shade; on the lit (top/left)
    side a lighter outline when given (selective outlining)."""
    out = [row[:] for row in c.g]
    for y in range(c.h):
        for x in range(c.w):
            ch = c.g[y][x]
            if ch == ".":
                continue
            empty_up = c.get(x, y - 1) == "."
            empty_left = c.get(x - 1, y) == "."
            empty_down = c.get(x, y + 1) == "."
            empty_right = c.get(x + 1, y) == "."
            if empty_up or empty_left or empty_down or empty_right:
                if lit_outline_of and (empty_up or empty_left) and not (empty_down or empty_right):
                    out[y][x] = lit_outline_of(ch)
                else:
                    out[y][x] = outline_of(ch)
    c.g = out


def material_of(ch):
    for r in (GILT, JADE, STEEL, COPPER, ["k", "l", "m", "n", "o", "p"], ["X", "Y", "Z", "z"], ["v", "w", "x", "y"]):
        if ch in r:
            return r
    return None


def dark_outline(ch):
    r = material_of(ch)
    return r[0] if r else ch


def lit_outline(ch):
    r = material_of(ch)
    return r[1] if r else ch


# ================================================================================================
# Lift Turbine: 4x6 tiles (32x48 art), 4 frames of the rotor; a glow layer for the fire inside
# ================================================================================================
TURBINE_W, TURBINE_H, TURBINE_FRAMES = 32, 48, 4
WIN_C, WIN_R = (15.5, 22.5), 7.0


def turbine_frame(k, glow=False):
    c = Canvas(TURBINE_W, TURBINE_H)
    g = Canvas(TURBINE_W, TURBINE_H)
    # the mount: a gearwork plate bolted to the island (rows 0-2) and two struts and a shaft down to the housing
    for y in range(0, 3):
        for x in range(1, 31):
            c.set(x, y, "E" if y == 0 else ("D" if y == 1 else "C"))
    for x in range(3, 30, 4):
        c.set(x, 1, "H")                                    # bolt heads
        c.set(x + 1, 2, "B")
    for (x0, x1) in ((6, 9), (22, 25)):
        for y in range(3, 8):
            for x in range(x0, x1 + 1):
                t = (x - x0) / (x1 - x0)
                c.set(x, y, ramp(GILT, 0.85 - 0.6 * t))
    for y in range(3, 8):
        for x in range(14, 18):
            c.set(x, y, ramp(STEEL, 0.75 - 0.5 * (x - 14) / 3))
    # the cap (rows 7-10) and the housing (rows 11-33): a brass cylinder lit from the left
    for y in range(7, 34):
        x0, x1 = (5, 26) if y == 7 else ((4, 27) if y < 33 else (5, 26))
        for x in range(x0, x1 + 1):
            n = (x + 0.5 - 15.5) / 12.0
            light = 0.55 + 0.45 * math.cos((n + 0.38) * math.pi * 0.55) - 0.25 * max(0.0, n)
            c.set(x, y, ramp(GILT, light * 0.92))
    for y in (9, 10, 30, 31):                                # jade inlay bands
        for x in range(4, 28):
            n = (x + 0.5 - 15.5) / 12.0
            t = 0.75 - 0.5 * max(0.0, n) + (0.15 if y in (9, 30) else -0.1)
            c.set(x, y, ramp(JADE, t))
    for x in range(6, 27, 5):                                # gilt rivets on the bands
        c.set(x, 9, "H")
        c.set(x, 31, "G")
    for y in (12, 28):                                       # seams round the drum
        for x in range(5, 27):
            c.set(x, y, "B")
    # the intake window: a ring of dark bronze, the fire glowing behind the turning rotor
    a0 = k * (math.pi / 2) / TURBINE_FRAMES
    for y in range(13, 32):
        for x in range(6, 26):
            dx, dy = x + 0.5 - WIN_C[0], y + 0.5 - WIN_C[1]
            r = math.hypot(dx, dy)
            if r > WIN_R + 1.0:
                continue
            if r > WIN_R:
                c.set(x, y, "B" if dx + dy > 0 else "C")     # the ring: shaded under the light
                continue
            if r > WIN_R - 1.0:
                c.set(x, y, "A")
                continue
            ang = math.atan2(dy, dx) - a0
            blade = False
            for b in range(4):
                d = (ang - b * math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
                width = 0.42 + 0.9 / max(1.0, r)
                if abs(d) < width and r > 1.2:
                    blade = True
            if r <= 1.6:
                c.set(x, y, "H" if dx + dy < 0 else "F")     # the hub
            elif blade:
                lit = -(dx + dy) / max(1.0, r)
                c.set(x, y, ramp(STEEL, 0.55 + 0.3 * lit))
            else:
                hot = 1.0 - r / WIN_R
                ch = "z" if hot > 0.62 else ("Z" if hot > 0.32 else "Y")
                c.set(x, y, ch)
                g.set(x, y, ch)
    # the lower cone (rows 34-40) and the nozzle (rows 41-47)
    for y in range(34, 41):
        half = 11 - (y - 34) * 5 / 6.0
        for x in range(int(round(15.5 - half)), int(round(15.5 + half)) + 1):
            n = (x + 0.5 - 15.5) / max(1.0, half)
            c.set(x, y, ramp(COPPER, 0.85 - 0.55 * max(0.0, n) - 0.15 * (y - 34) / 6.0))
    for y in range(41, 48):
        for x in range(10, 22):
            n = (x + 0.5 - 15.5) / 6.0
            if y < 44:
                c.set(x, y, ramp(GILT, 0.8 - 0.5 * max(0.0, n) - (0.2 if y == 43 else 0.0)))
            elif 12 <= x <= 19 and y >= 45:
                ch = "z" if 14 <= x <= 17 and y == 47 else ("Z" if y >= 46 else "Y")
                c.set(x, y, ch)
                g.set(x, y, ch)
            else:
                c.set(x, y, ramp(COPPER, 0.6 - 0.35 * max(0.0, n)))
    outline_pass(c, dark_outline, lit_outline)
    return g if glow else c


def tile_cells(frame_canvas, cols, rows):
    """Cuts a whole object into 16x16 tile cells (8x8 art) laid out on the 18 px (9 art px) stride."""
    out = Canvas(cols * 9, rows * 9)
    for ty in range(rows):
        for tx in range(cols):
            for y in range(8):
                for x in range(8):
                    out.set(tx * 9 + x, ty * 9 + y, frame_canvas.get(tx * 8 + x, ty * 8 + y))
    return out


def stack_frames(frames, cols, rows):
    sheet = Canvas(cols * 9, rows * 9 * len(frames))
    for k, f in enumerate(frames):
        sheet.blit(tile_cells(f, cols, rows), 0, k * rows * 9)
    return sheet


# ================================================================================================
# Bronze Cog: 6x6 tiles (48x48 art), 12 frames of 5 degrees (six spokes: the picture repeats every 60 degrees)
# ================================================================================================
COG_SIZE, COG_FRAMES, COG_TEETH, COG_SPOKES = 48, 12, 12, 6
R_TIP, R_ROOT, R_RIM, R_HUB, R_JADE = 23.2, 19.0, 15.0, 6.2, 4.6


def cog_frame(k, size=COG_SIZE, scale=1.0, teeth=COG_TEETH, spokes=COG_SPOKES):
    c = Canvas(size, size)
    cx = cy = size / 2.0
    rot = math.radians(5.0 * k)
    rt, rr, rm, rh, rj = R_TIP * scale, R_ROOT * scale, R_RIM * scale, R_HUB * scale, R_JADE * scale
    region = {}
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            phi = math.atan2(dy, dx) - rot
            if r >= rt:
                continue
            if r >= rr:
                t = (phi * teeth / (2 * math.pi)) % 1.0
                half = 0.26 - 0.08 * (r - rr) / max(0.1, rt - rr)    # teeth taper to their tips
                if abs(t - 0.5) > half:
                    continue
                region[(x, y)] = "tooth"
            elif r >= rm:
                region[(x, y)] = "rim"
            elif r >= rh:
                s = (phi * spokes / (2 * math.pi)) % 1.0
                arc = abs(s - 0.5) * 2 * math.pi * r / spokes        # px from the spoke's centre line
                if arc > 1.7 * scale + 0.3:
                    continue
                region[(x, y)] = "spoke"
            elif r >= rj:
                region[(x, y)] = "hubring"
            else:
                region[(x, y)] = "jade" if r > 1.4 * scale else "pin"
    for (x, y), part in region.items():
        dx, dy = x + 0.5 - cx, y + 0.5 - cy
        r = max(0.5, math.hypot(dx, dy))
        facing = -(dx + dy) / (r * math.sqrt(2.0))                    # +1 towards the top-left light
        if part in ("tooth", "rim"):
            base = 0.58 + 0.26 * facing
        elif part == "spoke":
            base = 0.45 + 0.2 * facing
        elif part == "hubring":
            base = 0.66 + 0.25 * facing
        elif part == "pin":
            base = 0.9
        else:
            base = None
        if part == "jade":
            c.set(x, y, ramp(JADE, 0.55 + 0.3 * facing))
        else:
            c.set(x, y, ramp(GILT, base))
    # bevels in screen space: a lit pixel where the top-left neighbour is empty, a shaded one under the bottom-right
    for (x, y), part in region.items():
        if part in ("jade", "pin"):
            continue
        ch = c.get(x, y)
        r = material_of(ch) or GILT
        i = r.index(ch) if ch in r else 4
        if (x - 1, y - 1) not in region and (x - 1, y) in region or (x, y - 1) not in region and (x - 1, y - 1) not in region:
            c.set(x, y, r[min(len(r) - 1, i + 2)])
        elif (x + 1, y + 1) not in region:
            c.set(x, y, r[max(1, i - 2)])
    # the rim's inner edge and the jade's ring: a dark line where the spokes' gaps begin
    outline_pass(c, dark_outline, lit_outline)
    return c


# ================================================================================================
# TurbineSmoke: four puffs (10x10 art each), growing; the dust fades them in code
# ================================================================================================
def smoke_frames():
    frames = []
    for k, rad in enumerate((1.6, 2.6, 3.5, 4.4)):
        c = Canvas(10, 10)
        lumps = [(5.0, 5.0, rad), (5.0 - rad * 0.45, 5.4, rad * 0.7), (5.0 + rad * 0.5, 5.6, rad * 0.65)]
        for y in range(10):
            for x in range(10):
                inside = [math.hypot(x + 0.5 - lx, y + 0.5 - ly) / lr for (lx, ly, lr) in lumps if lr > 0.6]
                if not inside or min(inside) >= 1.0:
                    continue
                lx, ly, lr = lumps[0]
                facing = -((x + 0.5 - lx) + (y + 0.5 - ly)) / (lr * 1.6)
                c.set(x, y, "u" if facing > 0.35 else ("t" if facing > -0.45 else "s"))
        if k >= 1:
            outline_pass(c, lambda ch: "s", lambda ch: "t")
        frames.append(c)
    sheet = Canvas(10, 10 * 4)
    for k, f in enumerate(frames):
        sheet.blit(f, 0, k * 10)
    return sheet


# ================================================================================================
# Items and the biome icon
# ================================================================================================
def turbine_item():
    """12x16: the turbine in small: mount bar, drum with a jade band, the glowing window, the nozzle."""
    rows = ["BEEEEEEEEEEB",
            "..BDB..BDB..",
            "..BEB..BEB..",
            ".BHGGFEEDCB.",
            ".BbddccbbaB.",
            ".BGGAAAAEDB.",
            ".BGAZzzYADB.",
            ".BFAzZY3ADB.",
            ".BFAY3ZYACB.",
            ".BEGAAAACCB.",
            ".BcddccbbaB.",
            "..BSSRRQQB..",
            "...BSRRQB...",
            "...BHGFDB...",
            "....YZZY....",
            ".....zz....."]
    return Canvas.from_rows(rows)


def cog_item():
    """16x16: the cog in small, drawn by hand (eight chunky teeth, a solid web with four holes, the jade hub)."""
    rows = ["......BB........",
            "...B.BGHB.B.....",
            "..BHBBHGGBHB....",
            "...BGHGFFEFEB.B.",
            ".BBHGFAAAAFEEBEB",
            "BHGGFA.FE.AFDDB.",
            ".BGFA.AcdA.ADB..",
            "..BFAEAdecAEDB..",
            "..BFFEAccbAFDB..",
            ".BGFA.AAAA.ADB..",
            "BGFFDA.ED.AEDDB.",
            ".BBFEDAAAADDDBCB",
            "...BEDDEEDDDB.B.",
            "..BCBBDDDBCCB...",
            "...B.BCCB.B.....",
            "......BB........"]
    return Canvas.from_rows(rows)


def biome_icon():
    """30x30 bestiary icon (15x15 art): the palace's pagoda on a cloud with a cog and a turbine's smoke under it."""
    rows = ["......HH.......",
            ".....acca......",
            "....accdca.....",
            ".....mnml......",
            "...acccdcca....",
            "....mnnnml.....",
            "..acccccdcca...",
            "...mnoonnml....",
            "..ddddddddddd..",
            ".tuuuuttuutut..",
            "tuuuEEGGEEuttt.",
            ".tttEHGGFEtts..",
            "..sstEGGEtss...",
            "....tt.ss......",
            ".....s..t......"]
    return Canvas.from_rows(rows)


def export_all():
    for block, name in ((FLAGSTONE, "PalaceFlagstone"), (JADE_BRICK, "JadeBrick"), (LACQUER, "CinnabarLacquer"), (GEARWORK, "BronzeGearwork"),
                        (ROOF, "JadeRoof"), (VAULT, "VaultGearwork")):
        export(block.sheet(), OUT + "Tiles/%sTile.png" % name)
        if block is not VAULT:                               # the vault's shell is unbreakable: no item
            export(block.item(), OUT + "Items/%s.png" % name)
    walls = (("PalaceFlagstoneWall", flagstone_wall_texture, "J", flagstone_wall_detail),
             ("JadeBrickWall", jade_wall_texture, "a", jade_wall_detail),
             ("CinnabarPanelWall", panel_wall_texture, "k", panel_wall_detail),
             ("BronzeLatticeWall", lattice_wall_texture, "B", None),
             ("BronzeGearworkWall", gearwork_wall_texture, "A", gearwork_wall_detail),
             ("VaultGearworkWall", vault_wall_texture, "A", vault_wall_detail))
    for name, texture, outline, detail in walls:
        export(wall_sheet(texture, outline, detail), OUT + "Walls/%sTile.png" % name)
        if name != "VaultGearworkWall":
            export(wall_item(texture, outline), OUT + "Items/%s.png" % name)
    frames = [turbine_frame(k) for k in range(TURBINE_FRAMES)]
    export(stack_frames(frames, 4, 6), OUT + "Tiles/LiftTurbineTile.png")
    export(stack_frames([turbine_frame(k, glow=True) for k in range(TURBINE_FRAMES)], 4, 6), OUT + "Tiles/LiftTurbineTile_Glow.png")
    export(stack_frames([cog_frame(k) for k in range(COG_FRAMES)], 6, 6), OUT + "Tiles/BronzeCogTile.png")
    export(smoke_frames(), OUT + "Dusts/TurbineSmoke.png")
    export(turbine_item(), OUT + "Items/LiftTurbine.png")
    export(cog_item(), OUT + "Items/BronzeCog.png")
    export(biome_icon(), OUT + "CoghavenBiome_Icon.png")


if __name__ == "__main__":
    export_all()
