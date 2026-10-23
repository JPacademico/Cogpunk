"""Source for the Scrap armor set (D4). Run from the repo root:

    python -P art/scrap/make_scrap_armor.py

Scrap armor is riveted together from heap junk: a dented iron pot helm with a brass brow band, a verdigris goggle,
an exhaust pipe and a cog over the ear; an iron chest plate patched with rusted copper, a leather strap, a rivet-
studded rust pauldron and a cog on the chest; rust-plated greaves with a leather belt, iron knee caps and boots,
and a small cog on the hip. The cogs spin.

How the cogs spin: vanilla draws armor from one equip texture per slot and picks the frame from the player's body
animation, so a texture can't animate on its own clock. Every piece therefore gets COG_FRAMES copies of its equip
sheet that differ only in the cog teeth (frame 0 = the normal autoloaded texture, frame n = <Name>_<Type>_<n>.png).
Core/Visuals/AnimatedEquip swaps the visible slot to the current copy every tick; its summary explains the
decompiled hook order that makes this safe.

Cogs use "ring teeth": a fixed body and hub, plus teeth on the ring of pixels around the body that step one ring
position per frame. A rotated raster of a real gear jitters at 6x6; stepping teeth read as a turning gear with a
steady direction. Shading is fixed in space (light from the top-left) while the teeth move.

Layout: art/templates/armor_layout.json (shapes only; see its _source). Arms, hands and legs follow those shapes and
are shaded here. The helmet, chest plate, pauldron and cogs are drawn by hand below.

Outputs (2x, in Content/Scrap/Armor/):
    ScrapHelmet_Head.png, ScrapHelmet_Head_1..3.png              40x1120 (20 frames of 40x56)
    ScrapBreastplate_Body.png, ScrapBreastplate_Body_1..3.png    360x224 (1.4 composite layout, 9x4 cells)
    ScrapLeggings_Legs.png, ScrapLeggings_Legs_1..3.png          40x1120
    ScrapHelmet.png, ScrapBreastplate.png, ScrapLeggings.png     item icons
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_scrap_art import Canvas, export  # noqa: E402  (shared palette letters and 2x export)

ROOT = os.getcwd()
OUT = "Content/Scrap/Armor"
COG_FRAMES = 4            # keep in sync with ScrapArmor.CogFrames (C#)
FW, FH = 20, 28           # one player frame at 1x art scale

LAYOUT = json.load(open(os.path.join(ROOT, "art/templates/armor_layout.json")))


# --------------------------------------------------------------------------------------------
# Cogs
# --------------------------------------------------------------------------------------------
COG6_RING = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 1), (5, 2), (5, 3), (5, 4),
             (4, 5), (3, 5), (2, 5), (1, 5), (0, 4), (0, 3), (0, 2), (0, 1)]


def cog6(frame, direction=1):
    """6x6 brass cog: 4x4 body with an axle hole, four 2-pixel teeth that step one ring pixel per frame (period 4)."""
    c = Canvas(6, 6)
    for i, (x, y) in enumerate(COG6_RING):
        if (i - direction * frame) % 4 < 2:
            c.set(x, y, "E" if x + y <= 4 else "C")
    body = {
        (1, 1): "E", (2, 1): "F", (3, 1): "E", (4, 1): "D",
        (1, 2): "F", (2, 2): "E", (3, 2): "B", (4, 2): "C",
        (1, 3): "E", (2, 3): "B", (3, 3): "D", (4, 3): "C",
        (1, 4): "D", (2, 4): "C", (3, 4): "C", (4, 4): "B",
    }
    for (x, y), ch in body.items():
        c.set(x, y, ch)
    return c


COG4_RING = [(1, 0), (2, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 2), (0, 1)]


def cog4(frame, direction=1):
    """4x4 brass cog: 2x2 body, two teeth on an 8-pixel ring stepping one pixel per frame (period 4)."""
    c = Canvas(4, 4)
    for i, (x, y) in enumerate(COG4_RING):
        if (i - direction * frame) % 4 == 0:
            c.set(x, y, "E" if x + y <= 2 else "C")
    c.set(1, 1, "F"); c.set(2, 1, "D"); c.set(1, 2, "D"); c.set(2, 2, "B")
    return c


def stamp(canvas, cog, ox, oy):
    canvas.blit(cog, ox, oy)


# --------------------------------------------------------------------------------------------
# Helmet (one 20x28 frame, facing right; shifted by LAYOUT["head_bob"] per frame)
# The player's head sits at about x 6..14, y 5..14 with the face on the right. The pot covers the skull down to
# the brow, a neck guard covers the back, a goggle sits over the eye and the lower face stays open.
# --------------------------------------------------------------------------------------------
def shade_region(c, pts, ramp, lit_bias=0):
    """Fill pixels with a 4-shade ramp (outline, dark, mid, light): outline on the silhouette except its lit
    top-left side, light just inside the top-left edge, dark just inside the bottom-right edge."""
    inside = set(pts)
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        dark = (x + 1, y) not in inside or (x, y + 1) not in inside
        if edge:
            ch = ramp[0]
        elif (x - 1, y - 1) not in inside or (x - 2, y) not in inside or (x, y - 2) not in inside:
            ch = ramp[3]
        elif (x + 1, y + 1) not in inside or (x + 2, y) not in inside or (x, y + 2) not in inside:
            ch = ramp[1]
        else:
            ch = ramp[2]
        c.set(x, y, ch)


def span_rows(rows):
    """{y: (x0, x1)} -> pixel list."""
    return [(x, y) for y, (x0, x1) in rows.items() for x in range(x0, x1 + 1)]


HELMET_DOME = {3: (8, 12), 4: (7, 13), 5: (6, 14), 6: (5, 15), 7: (5, 15)}
HELMET_NECK = {9: (5, 10), 10: (5, 10), 11: (6, 9)}
HELMET_COG = (4, 7)          # top-left of the 6x6 ear cog, over the back of the brow band and neck guard


def helmet_frame(anim):
    c = Canvas(FW, FH)
    # Exhaust stack out of the back of the dome.
    for (x, y, ch) in ((6, 1, "i"), (7, 1, "q"), (8, 1, "i"), (6, 2, "a"), (7, 2, "d"), (8, 2, "a"),
                       (6, 3, "a"), (7, 3, "c"), (8, 3, "a")):
        c.set(x, y, ch)
    shade_region(c, span_rows(HELMET_DOME), ("i", "j", "k", "q"))
    shade_region(c, span_rows(HELMET_NECK), ("i", "j", "k", "q"))
    c.set(9, 4, "r"); c.set(8, 5, "r")                                        # dome glint
    for (x, y, ch) in ((11, 5, "b"), (12, 5, "c"), (10, 6, "b"), (11, 6, "d"), (12, 6, "c"), (11, 7, "b")):
        c.set(x, y, ch)                                                       # rust patch
    for x in range(9, 17):                                                    # brass brow band with rivets,
        c.set(x, 8, "B" if x == 16 else ("F" if x in (10, 13) else ("E" if x < 12 else "D")))   # from the cog to the brim
    for (x, y, ch) in ((12, 9, "B"), (13, 9, "E"), (14, 9, "D"), (15, 9, "B"),   # goggle
                       (12, 10, "D"), (13, 10, "u"), (14, 10, "w"), (15, 10, "C"),
                       (12, 11, "B"), (13, 11, "C"), (14, 11, "C"), (15, 11, "B"),
                       (11, 10, "b"), (10, 10, "a")):                          # copper-wire goggle strap
        c.set(x, y, ch)
    stamp(c, cog6(anim, 1), *HELMET_COG)
    return c


def make_head_sheet(anim):
    sheet = Canvas(FW, FH * 20)
    frame = helmet_frame(anim)
    for f, dy in enumerate(LAYOUT["head_bob"]):
        sheet.blit(frame, 0, f * FH + dy)
    return sheet


# --------------------------------------------------------------------------------------------
# Body (1.4 composite sheet: 9x4 cells of 20x28)
# --------------------------------------------------------------------------------------------
TORSO_ROWS = [               # x 6..13, y 13..20: iron plate, rust patch, rivets, leather strap; cog added on top
    "ijqqkkji",
    "iqrkkkji",
    "ikkmkbji",
    "ijkkmcbi",
    "ikbckmji",
    "ijcdkkmi",
    "ilmlllli",
    "iiiiiiii",
]
TORSO_ORIGIN = (6, 13)
CHEST_COG = (8, 14)          # 6x6 cog on the chest front (turns the other way from the helmet cog)

PAULDRON_ROWS = [            # front shoulder, x 2..9, y 12..16: an iron plate riveted over a rusted one
    "....iii.",
    "..iiqrki",
    ".iqkkkji",
    "abdFcdFa",
    ".abbbba.",
]
PAULDRON_ORIGIN = (2, 12)

BACK_SHOULDER_ROWS = [       # the far shoulder peeking out in front of the chest, x 14..15, y 13..16
    "ii",
    "ki",
    "ji",
    "ii",
]
BACK_SHOULDER_ORIGIN = (14, 13)


def torso_cell(anim):
    c = Canvas(FW, FH)
    c.blit(Canvas.from_rows(TORSO_ROWS), *TORSO_ORIGIN)
    stamp(c, cog6(anim, -1), *CHEST_COG)        # where no tooth sits, the plate's own outline shows through
    return c


def pauldron_cell():
    c = Canvas(FW, FH)
    c.blit(Canvas.from_rows(PAULDRON_ROWS), *PAULDRON_ORIGIN)
    return c


def back_shoulder_cell():
    c = Canvas(FW, FH)
    c.blit(Canvas.from_rows(BACK_SHOULDER_ROWS), *BACK_SHOULDER_ORIGIN)
    return c


ARM_PIVOT = {"front": (6.0, 13.5), "back": (14.0, 13.5)}


def shade_limb(mask, pivot, hand_len=2.6):
    """Arm from a template mask: rust sleeve with a brass band, iron gauntlet on the far end (the hand).
    Outline = the material's darkest shade; interior lit from the top-left."""
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    if not pts:
        return Canvas(FW, FH)
    inside = set(pts)
    dist = {p: math.hypot(p[0] - pivot[0], p[1] - pivot[1]) for p in pts}
    far = max(dist.values())
    c = Canvas(FW, FH)
    for (x, y) in pts:
        d = dist[(x, y)]
        hand = d >= far - hand_len
        band = not hand and abs(d - far * 0.5) < 0.6
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        dark = (x + 1, y) not in inside or (x, y + 1) not in inside
        if hand:
            ramp = ("i", "j", "k", "q")
        elif band:
            ramp = ("B", "C", "D", "E")
        else:
            ramp = ("a", "b", "c", "d")
        if edge and not (lit and not dark and ramp[0] != "B"):
            ch = ramp[0]
        elif lit:
            ch = ramp[3]
        elif dark:
            ch = ramp[1]
        else:
            ch = ramp[2]
        c.set(x, y, ch)
    return c


def make_body_sheet(anim):
    sheet = Canvas(FW * 9, FH * 4)
    cells = LAYOUT["body_cells"]
    for key, mask in cells.items():
        col, row = (int(v) for v in key.split(","))
        if col in (0, 1):
            if row in (0, 2):
                cell = torso_cell(anim)                       # male and female torso, standing and jumping
            elif col == 0:
                cell = pauldron_cell()                        # front shoulder (rows 1 and 3)
            else:
                cell = back_shoulder_cell()
        else:
            side = "front" if (col == 7 or (col <= 6 and row in (0, 1))) else "back"
            cell = shade_limb(mask, ARM_PIVOT[side])
        sheet.blit(cell, col * FW, row * FH)
    return sheet


# --------------------------------------------------------------------------------------------
# Legs (20 frames from the template; belt on the top row, iron boots on the bottom two, rust greaves between)
# --------------------------------------------------------------------------------------------
HIP_COG_OFFSET = (1, 0)      # 4x4 hip cog, from the left end of the belt row


def legs_frame(mask, anim):
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = Canvas(FW, FH)
    if not pts:
        return c
    inside = set(pts)
    top = min(y for _, y in pts)
    bottom = max(y for _, y in pts)
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        dark = (x + 1, y) not in inside or (x, y + 1) not in inside
        if y == top:
            ramp = ("l", "l", "m", "n")                         # leather belt
        elif y >= bottom - 1:
            ramp = ("i", "j", "k", "q")                         # iron boots
        elif y == top + 2:
            ramp = ("i", "j", "k", "q")                         # iron knee caps
        else:
            ramp = ("a", "b", "c", "d")                         # rusted greaves
        if edge and not (lit and not dark):
            ch = ramp[0]
        elif lit:
            ch = ramp[3]
        elif dark:
            ch = ramp[1]
        else:
            ch = ramp[2]
        c.set(x, y, ch)
    # Brass buckle at the front of the belt.
    belt = sorted(x for x, y in pts if y == top)
    c.set(belt[-1] - 1, top, "E")
    # Hip cog over the back of the belt; clipped to the leg silhouette so it never sticks out of the frame.
    cog = cog4(anim, 1)
    ox, oy = belt[0] + HIP_COG_OFFSET[0], top
    for y in range(cog.h):
        for x in range(cog.w):
            ch = cog.get(x, y)
            if ch != "." and (ox + x, oy + y) in inside:
                c.set(ox + x, oy + y, ch)
    return c


def make_legs_sheet(anim):
    sheet = Canvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(legs_frame(mask, anim), 0, f * FH)
    return sheet


# --------------------------------------------------------------------------------------------
# Item icons: the worn pieces in their idle pose, cropped to their bounds.
# --------------------------------------------------------------------------------------------
def crop_to_content(c, pad=0):
    xs = [x for y in range(c.h) for x in range(c.w) if c.g[y][x] != "."]
    ys = [y for y in range(c.h) for x in range(c.w) if c.g[y][x] != "."]
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    out = Canvas(x1 - x0 + 1, y1 - y0 + 1)
    for y in range(out.h):
        for x in range(out.w):
            out.set(x, y, c.get(x0 + x, y0 + y))
    return out


def body_idle(sheet):
    """Idle pose: back arm, torso, front arm and pauldron, composited like the game does."""
    def cell(col, row):
        out = Canvas(FW, FH)
        for y in range(FH):
            for x in range(FW):
                out.set(x, y, sheet.get(col * FW + x, row * FH + y))
        return out
    c = Canvas(FW, FH)
    for col, row in ((2, 2), (0, 0), (2, 0), (0, 1), (1, 1)):
        c.blit(cell(col, row), 0, 0)
    return c


if __name__ == "__main__":
    for anim in range(COG_FRAMES):
        suffix = "" if anim == 0 else f"_{anim}"
        export(make_head_sheet(anim), f"{OUT}/ScrapHelmet_Head{suffix}.png")
        export(make_body_sheet(anim), f"{OUT}/ScrapBreastplate_Body{suffix}.png")
        export(make_legs_sheet(anim), f"{OUT}/ScrapLeggings_Legs{suffix}.png")
    export(crop_to_content(helmet_frame(0)), f"{OUT}/ScrapHelmet.png")
    export(crop_to_content(body_idle(make_body_sheet(0))), f"{OUT}/ScrapBreastplate.png")
    export(crop_to_content(legs_frame(LAYOUT["legs"][5], 0)), f"{OUT}/ScrapLeggings.png")   # jump frame: legs apart
