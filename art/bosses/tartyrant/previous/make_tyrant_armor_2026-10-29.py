"""ARCHIVED 2026-10-30: the generator as it stood on 2026-10-29 (third round), kept so the look can be restored. Running it
overwrites the current assets (it writes the same Content/ paths). Run from the repo root.
"""
"""Source for the Tyrant armor (D4), 2026-10-29: the mage set Tar Tyrant drops (at least one piece a kill). Run from the
repo root:

    python -P art/bosses/tartyrant/make_tyrant_armor.py

The boss cut down to a person, in its own colours (the first design, restored 2026-10-29): glossy brown-black tar (Iron 0
outline, Leather 0/1 body, the cold Iron 2/3 gloss of a wet surface) and tar-stained fossil bone (Leather outline, Leather
2 stains, Steam 1 dry faces, Brass 5 glints); an ember in the skull's orbit. Drawn at 1x, exported at 2x nearest-neighbour,
Cogpunk palette only, lit from the top-left, ramp-0 outlines. Static (no animated parts). Layout: art/templates/
armor_layout.json (shapes); the pixels are drawn here with the letter palette of art/scrap/make_scrap_art.py, the same way
as art/mecharmy/make_jaeger_armor.py.

    Tyrant Skull     the boss's Tyrannosaurus skull worn as a hood: the cranium over the head, the long snout jutting
                     forward over the face with a row of teeth hanging from it, the orbit with an ember in it, the
                     antorbital hole and nostril full of tar, tar oozing down the back of the neck
    Tyrant Cape      a tar-soaked tunic under a breastplate of ribs, a tar cape hanging down the back (shoulder to hip,
                     ragged hem, a drip), a vertebra for a shoulder guard, tar sleeves with a bone bracer
    Tyrant Sandals   tar-wrapped legs split into two, a belt of vertebrae, bone knee guards, bone sandals strapped on

Outputs (Content/Bosses/TarTyrant/Armor/):
    TyrantSkull_Head.png      40x1120   20 frames of 40x56
    TyrantCape_Body.png       360x224   1.4 composite layout, 9x4 cells
    TyrantSandals_Legs.png    40x1120
    TyrantSkull.png, TyrantCape.png, TyrantSandals.png   item icons
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "mechanist"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "trashtr0m"))
from make_scrap_art import Canvas as LCanvas, export as lexport  # noqa: E402
import make_mechanist_art as mech  # noqa: E402  (shade, rows, the template layout and leg specs)

OUT = "Content/Bosses/TarTyrant/Armor/"
FW, FH = mech.FW, mech.FH
LAYOUT = mech.LAYOUT
rows = mech.rows
shade = mech.shade

TAR = ("i", "l", "l", "m", "k")                     # outline, dark, mid, light, gloss (rig.RAMP["tar"])
BONE = ("l", "m", "n", "s", "G")                    # outline, stain, mid, dry face, glint (rig.RAMP["bone"])
SKULL_BONE = ("l", "n", "s", "G", "G")              # the skull as the boss wears it: grey-white, cream on top, stained underneath


# ================================================================================================
# Skull (one 20x28 frame facing right; the head sits at about x 7..14, y 5..12, the eye at 12..13, 9)
# ================================================================================================
SKULL = {2: (8, 12), 3: (6, 14), 4: (5, 16), 5: (5, 18), 6: (5, 19), 7: (6, 19), 8: (7, 18)}
MANE = {4: (3, 5), 5: (3, 5), 6: (3, 6), 7: (3, 6), 8: (3, 7), 9: (4, 8), 10: (4, 8), 11: (5, 7)}


def skull_frame():
    c = LCanvas(FW, FH)
    shade(c, rows(MANE), TAR, shine=False)                         # tar oozing down the back of the neck
    c.set(4, 6, "k")
    c.set(4, 7, "m")
    for (x, y, ch) in ((5, 12, "l"), (6, 12, "i"), (5, 13, "k"), (5, 14, "i")):   # a drip off it
        c.set(x, y, ch)
    shade(c, rows(SKULL), SKULL_BONE)
    for (x, y, ch) in ((9, 4, "i"), (10, 4, "z"), (9, 5, "x"), (10, 5, "i"), (11, 5, "l"),   # the orbit, an ember in it
                       (13, 6, "i"), (14, 6, "l"), (15, 6, "l"), (14, 5, "n"),             # the antorbital hole, tar inside
                       (17, 5, "i"), (18, 6, "n"),                                         # the nostril
                       (7, 6, "n"), (8, 7, "n"), (12, 3, "n"), (16, 7, "n")):              # stains and a crack
        c.set(x, y, ch)
    for x in range(8, 19):                                         # the upper jaw's edge over the face
        c.set(x, 8, "l" if x in (8, 18) else ("n" if x % 2 else "m"))
    for x in (14, 16):                                             # teeth hanging from it, ahead of the wearer's face
        c.set(x, 9, "s")
        c.set(x + 1, 9, "l")
    c.set(18, 9, "G")
    c.set(19, 9, "l")
    return c


def head_sheet():
    sheet = LCanvas(FW, FH * 20)
    frame = skull_frame()
    for f, dy in enumerate(LAYOUT["head_bob"]):
        cell = LCanvas(FW, FH)
        cell.blit(frame, 0, dy)                                    # clipped to its own cell
        sheet.blit(cell, 0, f * FH)
    return sheet


# ================================================================================================
# Body (1.4 composite: 9x4 cells of 20x28)
# ================================================================================================
TORSO = [                  # x 6..13, y 13..20: a tar tunic under a breastplate of three ribs, a vertebra belt
    "illmmlli",
    "ilssGssi",
    "ilmllmmi",
    "ilnsssni",
    "ilmllmli",
    "illnssli",
    "illmmlli",
    "lnsnsnsl",
]
CAPE = [                   # x 2..6, y 12..22: the tar cape down the back, a ragged hem and a drip
    ".iii.",
    "ilmmi",
    "ilmki",
    "ilmmi",
    "ilmmi",
    "illki",
    "ilmmi",
    "illmi",
    "illli",
    "ilili",
    ".i.i.",
]
CLASP = [                  # a knuckle of bone pinning the cape at the shoulder, x 5..7, y 12..13
    "lsl",
    "lnl",
]
PAULDRON = [               # front shoulder, x 3..8, y 11..15: a vertebra for a shoulder guard, its spine sticking up
    "...l..",
    "..lsl.",
    ".lsGsl",
    "lsssnl",
    ".lnml.",
]
BACK_SHOULDER = ["ii", "mi", "li", "li", "ii"]


def torso_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows(CAPE), 2, 12)
    c.blit(LCanvas.from_rows(TORSO), 6, 13)
    c.blit(LCanvas.from_rows(CLASP), 5, 12)
    return c


def pauldron_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows(PAULDRON), 3, 11)
    return c


def back_shoulder_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows(BACK_SHOULDER), 14, 12)
    return c


def limb(mask, pivot, hand_len=2.6):
    """Arm from a template mask: a tar sleeve, a bone bracer just above the hand, the hand in a dark tar glove."""
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = LCanvas(FW, FH)
    if not pts:
        return c
    inside = set(pts)
    dist = {p: math.hypot(p[0] - pivot[0], p[1] - pivot[1]) for p in pts}
    far = max(dist.values())
    glove = ("i", "i", "l", "l", "m")
    for (x, y) in pts:
        d = dist[(x, y)]
        hand = d >= far - hand_len
        band = not hand and abs(d - (far - hand_len - 1.0)) < 0.6
        ramp = glove if hand else (BONE if band else TAR)
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        dark = (x + 1, y) not in inside or (x, y + 1) not in inside
        if edge and not (lit and not dark and ramp is BONE):
            ch = ramp[0]
        elif lit:
            ch = ramp[3]
        elif dark:
            ch = ramp[1]
        else:
            ch = ramp[2]
        c.set(x, y, ch)
    return c


def body_sheet():
    sheet = LCanvas(FW * 9, FH * 4)
    for key, mask in LAYOUT["body_cells"].items():
        col, row = (int(v) for v in key.split(","))
        if col in (0, 1):
            if row in (0, 2):
                cell = torso_cell()
            elif col == 0:
                cell = pauldron_cell()
            else:
                cell = back_shoulder_cell()
        else:
            side = "front" if (col == 7 or (col <= 6 and row in (0, 1))) else "back"
            cell = limb(mask, mech.ARM_PIVOT[side])
        sheet.blit(cell, col * FW, row * FH)
    return sheet


# ================================================================================================
# Legs (20 frames from the template): two tar-wrapped legs, a vertebra belt, bone knee guards, bone sandals
# ================================================================================================
def legs_frame(mask):
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = LCanvas(FW, FH)
    if not pts:
        return c
    inside = set(pts)
    belt_rows, crotch, split = mech._leg_spec(mask)
    part = {}
    for (x, y) in pts:
        if y in belt_rows:
            part[(x, y)] = "belt"
        elif y < crotch:
            part[(x, y)] = "hip"
        else:
            part[(x, y)] = "L" if x < split[y] else "R"

    def outside(x, y):
        return (x, y) not in inside

    for (x, y), p in part.items():                               # the belt: a chain of vertebrae
        if p == "belt":
            c.set(x, y, "l" if outside(x - 1, y) or outside(x + 1, y) else ("s" if x % 2 == 0 else "n"))
    for (x, y), p in part.items():                               # hips: tar, a dark crease above the split
        if p != "hip":
            continue
        if outside(x - 1, y) or outside(x + 1, y):
            c.set(x, y, "i")
        elif y == crotch - 1 and x == split.get(crotch, 10):
            c.set(x, y, "i")
        else:
            c.set(x, y, "m" if outside(x - 2, y) else "l")
    for leg in ("L", "R"):
        mine = {px for px, p in part.items() if p == leg}
        if not mine:
            continue
        low = max(y for _, y in mine)
        top = min(y for _, y in mine)
        height = low - top + 1
        knee = low - 2 if height <= 4 else low - 3
        for y in range(top, low + 1):
            run = sorted(x for (x, yy) in mine if yy == y)
            if not run:
                continue
            for i, x in enumerate(run):
                seam = leg == "R" and part.get((x - 1, y)) == "L"
                edge = outside(x - 1, y) or outside(x + 1, y)
                if y == low:
                    ch = "l" if edge or seam else "n"               # the bone sole
                elif y == low - 1:
                    ch = "i" if edge or seam else ("s" if i in (1, len(run) - 2) else "l")   # the sandal's straps
                elif seam or edge:
                    ch = "i"
                elif (y - top) % 2 == 1:
                    ch = "l"                                        # the tar wraps, band by band
                elif i == 1:
                    ch = "k"                                        # the wet gloss on the lit side
                else:
                    ch = "m"
                c.set(x, y, ch)
            if y == knee:                                           # a bone knee guard
                inner = [x for x in run if c.get(x, y) not in ("i",)]
                if len(inner) >= 2:
                    c.set(inner[-2], y, "G")
                    c.set(inner[-1], y, "s")
                elif inner:
                    c.set(inner[-1], y, "s")
    return c


def legs_sheet():
    sheet = LCanvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(legs_frame(mask), 0, f * FH)
    return sheet


# ================================================================================================
def export_all():
    lexport(head_sheet(), OUT + "TyrantSkull_Head.png")
    body = body_sheet()
    lexport(body, OUT + "TyrantCape_Body.png")
    lexport(legs_sheet(), OUT + "TyrantSandals_Legs.png")
    lexport(mech.crop(skull_frame()), OUT + "TyrantSkull.png")
    lexport(mech.crop(mech.body_idle(body)), OUT + "TyrantCape.png")
    lexport(mech.crop(legs_frame(LAYOUT["legs"][5])), OUT + "TyrantSandals.png")


if __name__ == "__main__":
    export_all()
