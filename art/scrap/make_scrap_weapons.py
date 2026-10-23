"""Source for the scrap arsenal sprites (D4). Run from the repo root:

    python -P art/scrap/make_scrap_weapons.py

Outputs (2x nearest-neighbour, next to their .cs files):
    Content/Scrap/Weapons/Screwdriver.png            32x32 inventory icon, points top-right
    Content/Scrap/Weapons/ScrewdriverProjectile.png  54x14 held thrust sprite, points right (rotated in code)
    Content/Scrap/Weapons/ScrappyWand.png            32x32 staff, points top-right (Item.staff)
    Content/Scrap/Weapons/ScrappyWandBolt.png        12x8 spark, points right
    Content/Scrap/Weapons/ScrappyBow.png             16x32 bow, faces right (string on the left)
    Content/Scrap/Minions/MiceBotMinion.png          32x176: 8 frames of 32x22 (16x11 art), facing right
    Content/Scrap/Minions/MiceBot.png                32x32 item (the mouse, wound up)
    Content/Scrap/Minions/MiceBotBuff.png            32x32 buff icon

Rods (screwdriver, wand) are rasterised from a profile along an axis: a pixel belongs to a segment when its distance
across the axis is within the segment's half-width, and it is shaded by which side of the axis it sits on (lit from
the top-left), so 45-degree icons come out as clean pixel staircases instead of rotated art.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_scrap_art import Canvas, export  # noqa: E402


# --------------------------------------------------------------------------------------------
# Rod rasteriser
# --------------------------------------------------------------------------------------------
def draw_rod(c, origin, direction, segments):
    """segments: list of (length, half_width, (outline, dark, mid, light)). origin = start of the first segment
    (pixel-centre coordinates); direction = unit axis. Lit side = the side facing up-left."""
    ox, oy = origin
    dx, dy = direction
    px, py = -dy, dx                           # perpendicular, flipped to point at the lower right (the shadow side)
    if px + py < 0:
        px, py = -px, -py
    total = sum(s[0] for s in segments)
    for y in range(c.h):
        for x in range(c.w):
            rx, ry = x - ox, y - oy
            along = rx * dx + ry * dy
            across = rx * px + ry * py         # > 0: shadow side (lower right)
            if along < -0.5 or along > total + 0.5:
                continue
            start = 0.0
            for (length, half, ramp) in segments:
                if along <= start + length + 0.5:
                    break
                start += length
            outline, dark, mid, light = ramp
            if abs(across) > half + 0.35:
                continue
            if abs(across) > half - 0.65:
                ch = outline
            elif across < -0.4:
                ch = light
            elif across > 0.4:
                ch = dark
            else:
                ch = mid
            c.set(x, y, ch)
    return c


IRON = ("i", "j", "k", "q")
SHAFT = ("i", "k", "q", "r")
WOOD = ("l", "m", "n", "d")
BRASS = ("C", "D", "E", "F")
RUST = ("a", "b", "c", "d")

DIAG = (1 / math.sqrt(2), -1 / math.sqrt(2))   # up-right


# --------------------------------------------------------------------------------------------
# Screwdriver: an old screwdriver ground to a sharp point - grooved wooden handle, brass ferrule, steel shaft.
# The held sprite is hand-drawn (27x7 art -> 54x14, point at the right end, axis on row 3 so the point is one pixel).
# --------------------------------------------------------------------------------------------
SCREWDRIVER_HELD = [
    # handle (10)  ferrule (2)  shaft (12)    point (3)
    ".llllllll." + ".." + "............" + "...",
    "lnndnndnnl" + "CC" + "iiiiiiiiiiii" + "i..",
    "lnmlnmlnml" + "FE" + "rrrrrrrrrrrr" + "ri.",
    "lmmlmmlmml" + "ED" + "qqqqqqqqqqqq" + "qri",
    "lmmlmmlmml" + "ED" + "kkkkkkkkkkkk" + "ki.",
    "lmmmmmmmml" + "CC" + "iiiiiiiiiiii" + "i..",
    ".llllllll." + ".." + "............" + "...",
]


def make_screwdriver_projectile():
    return Canvas.from_rows(SCREWDRIVER_HELD)


def make_screwdriver_icon():
    c = Canvas(16, 16)
    # the last two segments taper the shaft to a one-pixel point
    draw_rod(c, (1.5, 14.5), DIAG, [(6.0, 1.9, WOOD), (1.6, 1.6, BRASS), (7.4, 0.95, SHAFT), (1.0, 0.6, SHAFT), (1.2, 0.3, SHAFT)])
    for (x, y) in ((3, 12), (5, 10)):           # handle grooves
        if c.get(x, y) not in ".":
            c.set(x, y, "l")
    return c


# --------------------------------------------------------------------------------------------
# Scrappy Wand: an iron pipe wrapped in a rusted plate, weld beads, a brass claw holding a topaz.
# --------------------------------------------------------------------------------------------
TOPAZ = [
    ".CC.",
    "CzFC",
    "CyzC",
    ".CC.",
]


def make_scrappy_wand():
    c = Canvas(16, 16)
    draw_rod(c, (1.5, 14.5), DIAG, [(3.0, 1.3, IRON), (5.0, 1.9, RUST), (3.5, 1.3, IRON), (2.2, 1.9, BRASS)])
    for (x, y) in ((6, 9), (8, 7)):             # weld beads where the plate meets the pipe
        if c.get(x, y) not in ".":
            c.set(x, y, "r")
    c.blit(Canvas.from_rows(TOPAZ), 11, 1)
    c.set(12, 2, "G")                           # the gem's glint, top-left
    return c


def make_wand_bolt():
    return Canvas.from_rows([
        "..EFz.",
        "DEFGGz",
        "DEFGGz",
        "..EFz.",
    ])


# --------------------------------------------------------------------------------------------
# Scrappy Bow: two riveted iron plates welded into limbs, a leather-wrapped brass grip, a cobweb string.
# --------------------------------------------------------------------------------------------
SCRAPPY_BOW = [
    ".ii.....",
    ".ikj....",
    ".s.kj...",
    ".s..kj..",
    ".s..crb.",
    ".s...qja",
    ".s...kji",
    ".s..CEFC",
    ".s..CDEC",
    ".s...kji",
    ".s...kja",
    ".s..crb.",
    ".s..kj..",
    ".s.kj...",
    ".ikj....",
    ".ii.....",
]


def make_scrappy_bow():
    return Canvas.from_rows(SCRAPPY_BOW)


# --------------------------------------------------------------------------------------------
# Mice-bot: a clockwork mouse on two wheels with a wind-up key on its back (16x11 frames, facing right).
# --------------------------------------------------------------------------------------------
MOUSE_W, MOUSE_H = 16, 11


def mouse(bob=0, key=0, wheel=0, mouth=False, pounce=False, tail=0, sniff=False):
    c = Canvas(MOUSE_W, MOUSE_H)
    body = set()
    cx, cy, rx, ry = 6.8, 6.4 + bob, 4.8, 2.8
    if pounce:
        cx, cy, rx, ry = 7.2, 5.6 + bob, 5.6, 2.3
    for y in range(MOUSE_H):
        for x in range(MOUSE_W):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                body.add((x, y))
    hx, hy = (11.4, 5.4 + bob) if not pounce else (12.6, 4.4 + bob)
    for y in range(MOUSE_H):
        for x in range(MOUSE_W):
            if math.hypot(x - hx, (y - hy) * 1.15) <= 2.3:
                body.add((x, y))
    nose = (int(hx + 3 - (0 if not sniff else 0)), int(round(hy + 0.6)))
    body.add((nose[0] - 1, nose[1]))
    body.add(nose)
    for (x, y) in body:
        dx, dy = x - cx, y - cy
        if y <= cy - ry + 1.2:
            ch = "d"
        elif y >= cy + ry - 0.8:
            ch = "b"
        else:
            ch = "c"
        c.set(x, y, ch)
    # outline the silhouette with the rust ramp's darkest shade
    edge = {(x, y) for (x, y) in body if any((x + ox, y + oy) not in body for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    for (x, y) in edge:
        c.set(x, y, "a")
    # rim light under the top outline (lit from the top-left), rim shadow over the bottom one
    for (x, y) in body - edge:
        if (x, y - 1) in edge and x < hx + 1:
            c.set(x, y, "d")
        elif (x, y + 1) in edge:
            c.set(x, y, "b")
    # a riveted plate seam across the back
    seam = int(round(cx + 0.5))
    for (x, y) in sorted(body - edge):
        if x == seam and c.get(x, y) == "c":
            c.set(x, y, "b")
    rivet = (int(round(cx - 2.5)), int(round(cy + 0.4)))
    if rivet in body - edge:
        c.set(*rivet, "e")
    c.set(nose[0], nose[1], "i")                # iron nose tip
    if sniff:
        c.set(nose[0], nose[1] - 1, "i")
    # eye: verdigris glow like Scrappybot's (friendly bots), with a dark socket behind it
    ex, ey = int(hx + 0.5), int(round(hy - 0.4))
    c.set(ex, ey, "u")
    c.set(ex - 1, ey, "a")
    if mouth:                                   # bite: the lower jaw drops open
        c.set(nose[0], nose[1] + 1, "a")
        c.set(nose[0] - 1, nose[1] + 1, ".")
        c.set(nose[0], nose[1], "x")
    def top_of(col):                            # first body row in a column (the outline)
        return min((y for (x, y) in body if x == col), default=MOUSE_H - 1)

    # brass ear sitting on the head's outline
    ear_x = int(hx - 1)
    ear_y = top_of(ear_x) - 2
    for (x, y, ch) in ((ear_x, ear_y, "C"), (ear_x + 1, ear_y, "C"), (ear_x - 1, ear_y + 1, "C"), (ear_x, ear_y + 1, "E"),
                       (ear_x + 1, ear_y + 1, "F"), (ear_x + 2, ear_y + 1, "C")):
        c.set(x, y, ch)
    # wind-up key on the back: a two-lobed brass bow on a stem, wide when side-on, a thin bar when edge-on
    kx = int(round(cx - 1.5))
    ky = top_of(kx) - 1
    c.set(kx, ky, "D")
    if key == 0:
        for (x, y, ch) in ((kx - 2, ky - 1, "C"), (kx - 1, ky - 1, "F"), (kx, ky - 1, "D"), (kx + 1, ky - 1, "E"), (kx + 2, ky - 1, "C"),
                           (kx - 2, ky - 2, "C"), (kx - 1, ky - 2, "C"), (kx + 1, ky - 2, "C"), (kx + 2, ky - 2, "C")):
            c.set(x, y, ch)
    else:
        for (x, y, ch) in ((kx, ky - 1, "E"), (kx, ky - 2, "C")):
            c.set(x, y, ch)
    # wire tail, attached to the rearmost body pixel of its row and curling up behind
    ty = int(round(cy))
    tx = min((x for (x, y) in body if y == ty), default=1)
    tails = [((tx - 1, ty), (tx - 2, ty - 1), (tx - 2, ty - 2)),
             ((tx - 1, ty), (tx - 2, ty), (tx - 3, ty - 1)),
             ((tx - 1, ty - 1), (tx - 2, ty - 2), (tx - 2, ty - 3))]
    for k, (x, y) in enumerate(tails[tail % len(tails)]):
        c.set(x, y, "k" if k == 0 else "j")
    # two small iron wheels; the spoke highlight moves as they turn
    if not pounce:
        for wx in (4, 9):
            wy = int(round(cy + ry)) + 0
            for (x, y, ch) in ((wx, wy, "i"), (wx + 1, wy, "i"), (wx, wy + 1, "i"), (wx + 1, wy + 1, "i")):
                c.set(x, y, ch)
            c.set(wx + (wheel % 2), wy + (wheel // 2 % 2), "q")
    else:
        for wx in (5, 10):
            c.set(wx, int(round(cy + ry)), "i")
    return c


def make_mouse_frames():
    return [
        mouse(key=0),                                    # 0 idle A
        mouse(key=1, sniff=True, tail=2),                # 1 idle B: key turns, nose twitches
        mouse(key=0, wheel=0, tail=0),                   # 2-5 run
        mouse(key=1, wheel=1, tail=1, bob=-1),
        mouse(key=0, wheel=2, tail=0),
        mouse(key=1, wheel=3, tail=1, bob=-1),
        mouse(key=1, pounce=True, tail=2),               # 6 jump / zip
        mouse(key=0, pounce=True, mouth=True, tail=1),   # 7 bite
    ]


def make_mouse_sheet(frames):
    sheet = Canvas(MOUSE_W, MOUSE_H * len(frames))
    for i, f in enumerate(frames):
        sheet.blit(f, 0, i * MOUSE_H)
    return sheet


def make_mouse_icon(frame):
    c = Canvas(16, 16)
    c.blit(frame, 0, 3)
    return c


if __name__ == "__main__":
    export(make_screwdriver_icon(), "Content/Scrap/Weapons/Screwdriver.png")
    export(make_screwdriver_projectile(), "Content/Scrap/Weapons/ScrewdriverProjectile.png")
    export(make_scrappy_wand(), "Content/Scrap/Weapons/ScrappyWand.png")
    export(make_wand_bolt(), "Content/Scrap/Weapons/ScrappyWandBolt.png")
    export(make_scrappy_bow(), "Content/Scrap/Weapons/ScrappyBow.png")
    frames = make_mouse_frames()
    export(make_mouse_sheet(frames), "Content/Scrap/Minions/MiceBotMinion.png")
    export(make_mouse_icon(frames[0]), "Content/Scrap/Minions/MiceBot.png")
    export(make_mouse_icon(frames[1]), "Content/Scrap/Minions/MiceBotBuff.png")
