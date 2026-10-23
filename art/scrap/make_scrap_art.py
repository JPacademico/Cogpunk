"""Source for every Rusted Scrap slice sprite (D4). Run from the repo root:

    python -P art/scrap/make_scrap_art.py

All sprites are authored at 1x with Cogpunk palette letters, then exported at 2x nearest-neighbour.
Light comes from the top-left; outlines use ramp index 0 of their material.

Outputs (next to their .cs files):
    Content/Scrap/Tiles/RustedScrapTile.png   288x270 terrain sheet (16x15 frames, 18 px stride)
    Content/Scrap/Items/RustedScrap.png       16x16
    Content/Scrap/Items/RustedCog.png         24x24
    Content/Scrap/Items/RustedMetal.png       24x20
    Content/Scrap/Pets/Scrappybot.png         24x24 (pet item: the robot folded up asleep)
    Content/Scrap/Pets/ScrappybotBuff.png     32x32
    Content/Scrap/Pets/ScrappybotPet.png      32x576 (16 frames of 32x36, see FRAMES below)
    Content/Scrap/Weapons/ScrapBomb.png       24x12
    Content/Scrap/Weapons/ScrapBombProjectile.png  24x28 (2 fuse frames of 24x14)

The terrain sheet uses art/templates/terrain_exposure.json, which records, for each frame of the
standard Terraria terrain layout, which sides are exposed ("o"), dirt-merged ("d") or joined ("-").
It was extracted from the frame layout of tModLoader's ExampleBlock.png (MIT); no template pixels are copied.
"""
import json
import math
import os
from PIL import Image

ROOT = os.getcwd()

PAL = {
    # Copper (rust)
    "a": (42, 18, 12), "b": (94, 40, 23), "c": (147, 68, 31), "d": (196, 104, 58), "e": (233, 160, 107),
    # Leather (dark rust / grime)
    "l": (47, 27, 20), "m": (91, 54, 38), "n": (138, 90, 60),
    # Iron
    "i": (21, 22, 28), "j": (46, 50, 59), "k": (79, 85, 98), "q": (127, 135, 148), "r": (183, 191, 202),
    # Brass
    "B": (43, 26, 14), "C": (90, 58, 23), "D": (138, 93, 34), "E": (184, 138, 51), "F": (223, 185, 78), "G": (246, 231, 161),
    # Verdigris (robot eye glow / charge lights)
    "v": (42, 94, 82), "w": (71, 145, 126), "u": (140, 201, 176),
    # Ember (thruster flame)
    "x": (163, 48, 26), "y": (236, 113, 40), "z": (255, 199, 90),
    # Steam
    "s": (195, 200, 205), "t": (238, 241, 243),
}

LIGHTEN = {"a": "b", "b": "c", "c": "d", "d": "e", "e": "e", "l": "m", "m": "n", "n": "d",
           "j": "k", "k": "q", "q": "r", "r": "r", "C": "D", "D": "E", "E": "F", "F": "F"}
DARKEN = {v: k for k, v in LIGHTEN.items() if k != v}
DARKEN.update({"e": "d", "n": "m", "d": "c", "r": "q", "F": "E"})


class Canvas:
    """A grid of palette letters ('.' = transparent) with bounds-checked writes."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [["."] * w for _ in range(h)]

    @staticmethod
    def from_rows(rows):
        c = Canvas(len(rows[0]), len(rows))
        for y, row in enumerate(rows):
            assert len(row) == c.w, f"ragged row {y}: {row!r}"
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
    print(f"wrote {rel_path} ({img.width * 2}x{img.height * 2})")


# --------------------------------------------------------------------------------------------
# Rusted Scrap terrain tile: compacted, rust-red junk. Lighter and redder than dirt (which is a yellow-brown
# around 151,107,75) so heaps read as scrap at a glance: a copper-rust mottle (c) with dark rust pits (b)
# and brown grime (m, n). The interior is SEAMLESS (D4 "seamless blocks" rule): no per-tile
# bevel or seam, junk pieces (a cog, a bent rod, a crumpled plate) sit at least one pixel inside the tile, and
# the tile edges are plain background mottle, so any variant can sit next to any other and a mass of scrap
# reads as one clump. Only exposed sides get an outline (see tile_frame).
# Terraria picks a variant at random per tile. Checked by tools/check_tile_seams.py.
# --------------------------------------------------------------------------------------------
TILE_VARIANTS = [
    [  # A: small dull-brass cog, upper left
        "cbmncmbc",
        "mDEDcbcn",
        "nElCCcmc",
        "cDCCmnbc",
        "bmCncbcm",
        "cmcnbmnc",
        "ncbmncmb",
        "cnbcmbnc",
    ],
    [  # B: rivet and a short iron rod, lower right
        "cnmbcmcn",
        "bcqcncmc",
        "mncbmncm",
        "ncmcmcbn",
        "cbnmcjkc",
        "mcbcjkqb",
        "cnmbcmcn",
        "mbncnmbc",
    ],
    [  # C: crumpled rusted plate, centre
        "cmbncbmn",
        "ncbmncmc",
        "mbddecnb",
        "cmdcmbcm",
        "bncbbmnc",
        "mcncmbnc",
        "cnmbcncm",
        "nbmcnmbc",
    ],
]
# Rim shading just inside exposed edges, kept in the rust/brown family so outlines don't glow orange.
TILE_RIM_LIGHT = {"l": "m", "m": "n", "n": "n", "b": "c", "c": "n", "d": "d", "j": "k", "k": "q", "C": "D", "D": "E"}
TILE_RIM_DARK = {"n": "m", "m": "b", "b": "l", "c": "b", "d": "c", "k": "j", "q": "k", "D": "C", "E": "D"}
# Per-variant notch positions that make exposed edges look ragged: (top x, right y, bottom x, left y).
NOTCHES = [(5, 5, 2, 2), (2, 2, 5, 5), (6, 4, 3, 3)]


def tile_frame(variant, exposure):
    """8x8 art for one terrain frame. exposure = 'TRBL' with 'o'/'d' (exposed) or '-' (joined)."""
    c = Canvas.from_rows(TILE_VARIANTS[variant])
    top, right, bottom, left = (ch != "-" for ch in exposure)
    nt, nr, nb, nl = NOTCHES[variant]

    # 1. Rim lighting just inside exposed edges (lit from the top-left).
    for i in range(8):
        if top:
            c.set(i, 1, TILE_RIM_LIGHT.get(c.get(i, 1), c.get(i, 1)))
        if left:
            c.set(1, i, TILE_RIM_LIGHT.get(c.get(1, i), c.get(1, i)))
        if bottom:
            c.set(i, 6, TILE_RIM_DARK.get(c.get(i, 6), c.get(i, 6)))
        if right:
            c.set(6, i, TILE_RIM_DARK.get(c.get(6, i), c.get(6, i)))
    # 2. Outline exposed edges with the rust ramp's darkest shade.
    for i in range(8):
        if top:
            c.set(i, 0, "a")
        if bottom:
            c.set(i, 7, "a")
        if left:
            c.set(0, i, "a")
        if right:
            c.set(7, i, "a")
    # 3. Ragged notches: cut one pixel and pull the outline inward.
    if top:
        c.set(nt, 0, "."); c.set(nt, 1, "a")
    if bottom:
        c.set(nb, 7, "."); c.set(nb, 6, "a")
    if left:
        c.set(0, nl, "."); c.set(1, nl, "a")
    if right:
        c.set(7, nr, "."); c.set(6, nr, "a")
    # 4. Rounded outer corners where two exposed sides meet.
    for (ex1, ex2, cx, cy, ix, iy) in ((top, left, 0, 0, 1, 1), (top, right, 7, 0, 6, 1),
                                       (bottom, left, 0, 7, 1, 6), (bottom, right, 7, 7, 6, 6)):
        if ex1 and ex2:
            c.set(cx, cy, "."); c.set(ix, iy, "a")
    return c


def make_tile_sheet():
    table = json.load(open(os.path.join(ROOT, "art/templates/terrain_exposure.json")))
    sheet = Canvas(16 * 9, 15 * 9)  # 8x8 art frames + 1 px gutter = 18 px stride at 2x
    for key, exposure in table.items():
        fx, fy = (int(v) for v in key.split(","))
        variant = (fx + fy * 2) % 3
        sheet.blit(tile_frame(variant, exposure), fx * 9, fy * 9)
    return sheet


# --------------------------------------------------------------------------------------------
# Items
# --------------------------------------------------------------------------------------------
def make_scrap_item():
    return tile_frame(0, "oooo")  # the cog variant as a free-standing block


def make_cog():
    """12x12 rusted gear: 8 teeth, worn brass showing through the rust on the lit side."""
    size, cx, cy = 12, 5.5, 5.5
    teeth, r_body, r_tooth, r_hole = 8, 3.9, 5.7, 1.3
    solid = [[False] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            ang = (math.atan2(dy, dx) + math.pi / teeth) % (2 * math.pi)
            in_tooth = (ang * teeth / (2 * math.pi)) % 1.0 < 0.5
            solid[y][x] = r_hole < r <= (r_tooth if in_tooth else r_body)

    def s(x, y):
        return 0 <= x < size and 0 <= y < size and solid[y][x]

    c = Canvas(size, size)
    for y in range(size):
        for x in range(size):
            if not solid[y][x]:
                continue
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            facing = (-dx - dy) / (max(r, 0.01) * math.sqrt(2))
            if not (s(x - 1, y) and s(x + 1, y) and s(x, y - 1) and s(x, y + 1)):
                ch = "a"
            elif r < r_hole + 1.6:
                ch = "b" if facing > 0 else "d"      # hub: inner bevel is lit from the opposite side
            elif facing > 0.55:
                ch = "e"
            elif facing > 0.05:
                ch = "d"
            elif facing > -0.45:
                ch = "c"
            else:
                ch = "b"
            c.set(x, y, ch)
    # Worn brass glints on the lit teeth, rust grime on the shadow side.
    for (x, y, ch) in ((3, 2, "F"), (2, 3, "E"), (6, 1, "E"), (8, 8, "m"), (7, 9, "l"), (9, 6, "m"), (4, 8, "n")):
        if c.get(x, y) not in (".", "a"):
            c.set(x, y, ch)
    return c


def make_metal():
    """12x10 rusted plate with a torn corner, two rivets and scratches down to bare iron."""
    return Canvas.from_rows([
        "aaaaaaaaa...",
        "aeeddddcaa..",
        "aedqrdcccaa.",
        "adcqkcccmca.",
        "adcccmcccba.",
        "adcnccccbbaa",
        "adcccqcmcbba",
        "adccqrqccbba",
        "abbbbbbbbbba",
        "aaaaaaaaaaaa",
    ])


# --------------------------------------------------------------------------------------------
# Scrappybot: a small rusted box robot with binocular eyes on a short neck and tank treads.
# 16x18 art frames (bottom row is padding), facing right. Built from parts so every frame
# keeps the same proportions.
# --------------------------------------------------------------------------------------------
FRAME_W, FRAME_H = 16, 18
FRAMES = [
    "idle",
    "walk1", "walk2", "walk3", "walk4",
    "fly1", "fly2",
    "settle1", "settle2",
    "sleep1", "sleep2", "sleep3",
    "wake1", "wake2", "wake3", "wake4",
]


def draw_treads(c, ty, phase):
    for x in range(3, 13):
        c.set(x, ty, "i")
        c.set(x, ty + 2, "i")
        c.set(x, ty + 1, "q" if (x + phase) % 4 == 0 else "k")
    c.set(2, ty + 1, "i")
    c.set(13, ty + 1, "i")
    c.set(3, ty, "j")       # lit top-left of the track
    c.set(4, ty + 1, "r")   # front and rear wheel hubs
    c.set(11, ty + 1, "r")


def draw_body(c, bx, by, lights, arm):
    x0, x1, y0, y1 = bx, bx + 8, by, by + 6
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                ch = "B"
            elif y == y0 + 1:
                ch = "E" if x == x1 - 1 else ("G" if x == x0 + 1 else "F")
            elif x == x0 + 1:
                ch = "F"
            elif y == y1 - 1:
                ch = "C" if x == x1 - 1 else "D"
            elif x == x1 - 1:
                ch = "D"
            else:
                ch = "E"
            c.set(x, y, ch)
    for x in range(x0 + 1, x1):          # panel seam across the front
        c.set(x, y0 + 3, "D")
    c.set(x1 - 1, y0 + 3, "C")
    # Rust and grime.
    c.set(x0 + 2, y0 + 2, "d"); c.set(x0 + 3, y0 + 2, "c"); c.set(x0 + 6, y1 - 1, "c"); c.set(x0 + 5, y1 - 1, "b")
    c.set(x0 + 6, y0 + 4, "m")
    # Charge strip: three small lights on the lower front.
    for i in range(3):
        c.set(x0 + 2 + i, y1 - 2, "u" if i < lights else "j")
    # Side arm.
    ay = {"up": y0 + 2, "mid": y0 + 3, "down": y0 + 4}.get(arm)
    if ay is not None:
        c.set(x1 + 1, ay, "k"); c.set(x1 + 2, ay, "q")
        c.set(x1 + 2, ay - 1 if arm == "up" else ay + 1, "k")   # little claw


def draw_eye(c, x, y, state):
    rows = {
        "open":   ["kqq", "jut", "jjk"],
        "wide":   ["qtq", "jtt", "jjk"],
        "half":   ["kkk", "jwu", "jjk"],
        "closed": ["kqq", "qqq", "jjk"],
    }[state]
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            c.set(x + dx, y + dy, ch)


def draw_head(c, ex, ey, state, tilt=0):
    draw_eye(c, ex, ey, state)
    draw_eye(c, ex + 4, ey + tilt, state)
    c.set(ex + 3, ey + 1 + max(tilt, 0), "j")   # bridge between the lenses


def robot(bx=3, by=7, ty=14, neck=1, eye_state="open", tilt=0, lights=2, arm="mid", phase=0,
          springs=False, flame=0):
    c = Canvas(FRAME_W, FRAME_H)
    draw_treads(c, ty, phase)
    draw_body(c, bx, by, lights, arm)
    ex = bx + 3
    ey = by - neck - 3
    for y in range(by - neck, by):                  # neck
        c.set(ex + 3, y, "k")
    draw_head(c, ex, ey, eye_state, tilt)
    if springs:                                     # body jolted up off the treads
        for x in (bx + 2, bx + 6):
            c.set(x, by + 7, "k")
    if flame:
        for fx in (4, 10):
            if flame == 1:
                c.set(fx, ty + 3, "z"); c.set(fx + 1, ty + 3, "z"); c.set(fx, ty + 4, "y"); c.set(fx + 1, ty + 4, "x")
            else:
                c.set(fx, ty + 3, "y"); c.set(fx + 1, ty + 3, "z"); c.set(fx + 1, ty + 4, "y")
    return c


def make_pet_frames():
    f = {}
    f["idle"] = robot()
    arms = ["mid", "down", "mid", "up"]
    for i in range(4):
        bob = 1 if i in (1, 3) else 0
        f[f"walk{i + 1}"] = robot(by=7 + bob, phase=i, arm=arms[i])
    f["fly1"] = robot(by=5, ty=12, arm="down", flame=1)
    f["fly2"] = robot(by=5, ty=12, arm="down", flame=2)
    f["settle1"] = robot(eye_state="half", lights=1, arm="down")
    f["settle2"] = robot(neck=0, eye_state="closed", lights=1, arm=None)
    for i in range(3):
        f[f"sleep{i + 1}"] = robot(neck=0, eye_state="closed", lights=i + 1, arm=None)
    f["wake1"] = robot(by=6, neck=2, eye_state="wide", lights=3, arm="up", springs=True)
    f["wake2"] = robot(neck=3, eye_state="open", tilt=1, lights=3, arm="up")
    f["wake3"] = robot(bx=2, neck=2, eye_state="open", tilt=-1, lights=2, arm="mid")
    f["wake4"] = robot(bx=4, neck=1, eye_state="open", lights=2, arm="down")
    return f


def make_pet_sheet(frames):
    sheet = Canvas(FRAME_W, FRAME_H * len(FRAMES))
    for i, name in enumerate(FRAMES):
        sheet.blit(frames[name], 0, i * FRAME_H)
    return sheet


# --------------------------------------------------------------------------------------------
# Scrap Bomb: a slim hand-made pipe bomb, only a little thicker than a Glowstick (8x8 art). A three-pixel
# rusted pipe between two chunky iron end caps, a brass and an iron wire wrap, a grime spot, and a fuse out
# of the right cap. 12x6 art, two fuse-spark frames.
# --------------------------------------------------------------------------------------------
BOMB_ROWS = [
    "............",   # spark row, filled per frame
    "ii.......iil",   # cap tops and the fuse
    "qkedEddqdkj.",   # lit top of the pipe; brass wrap (E) and iron wrap (q)
    "kjcmDcckcjj.",
    "jiaaCaaiaji.",   # pipe outline (copper 0) under the wraps
    "ii.......ii.",   # cap bottoms
]


def make_scrap_bomb(spark):
    c = Canvas.from_rows(BOMB_ROWS)
    if spark == 0:
        c.set(11, 0, "z")
    else:
        c.set(11, 0, "y"); c.set(10, 0, "z")
    return c


def make_bomb_sheet():
    sheet = Canvas(12, 14)                       # two 12x7 frames (bottom row of each is padding)
    sheet.blit(make_scrap_bomb(0), 0, 0)
    sheet.blit(make_scrap_bomb(1), 0, 7)
    return sheet


def crop(c, x, y, w, h):
    out = Canvas(w, h)
    for yy in range(h):
        for xx in range(w):
            out.set(xx, yy, c.get(x + xx, y + yy))
    return out


if __name__ == "__main__":
    export(make_tile_sheet(), "Content/Scrap/Tiles/RustedScrapTile.png")
    export(make_scrap_item(), "Content/Scrap/Items/RustedScrap.png")
    export(make_cog(), "Content/Scrap/Items/RustedCog.png")
    export(make_metal(), "Content/Scrap/Items/RustedMetal.png")
    pet = make_pet_frames()
    export(make_pet_sheet(pet), "Content/Scrap/Pets/ScrappybotPet.png")
    export(crop(pet["idle"], 0, 1, 16, 16), "Content/Scrap/Pets/ScrappybotBuff.png")
    export(crop(pet["sleep3"], 2, 4, 12, 13), "Content/Scrap/Pets/Scrappybot.png")
    export(make_scrap_bomb(0), "Content/Scrap/Weapons/ScrapBomb.png")
    export(make_bomb_sheet(), "Content/Scrap/Weapons/ScrapBombProjectile.png")
