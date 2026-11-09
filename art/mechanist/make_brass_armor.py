"""Source for the Brass armor (D4), 2026-11-09 (user: "a new set of armor called Brass armor for the mechanist class (T5
balanced, the last armor for the mechanist in pre-hardmode, like the hellstone armor is the last for melee); its set bonus
should reduce any damage taken during overheat by 35%"). Run from the repo root:

    python -P art/mechanist/make_brass_armor.py

The Mechanist's last pre-Hardmode set, polished brass where the Polished set was buffed steel: a steamfitter's brass
diving helm with a steel-ringed porthole visor of verdigris glass, rivets round it, a copper ear valve and a little steam
stack on the crown; a brass breastplate with a pressure gauge (a white face, its ember needle well into the red: it runs
hot), riveted plates and a steel belt with a brass buckle, a copper boiler on the back with steel hoops, domed brass
pauldrons with steel rims, brass sleeves with a steel elbow band and iron gauntlets; brass greaves split into two legs,
steel knee caps, a leather belt with a brass buckle and iron boots with a copper piston. Drawn at 1x in the palette
letters of art/scrap/make_scrap_art.py, exported at 2x nearest-neighbour, lit from the top-left, ramp-0 outlines, on the
shapes of art/templates/armor_layout.json (the Polished and Jaeger sets' helpers: art/mechanist/make_mechanist_art.py).
Static (no animated parts).

Outputs (Content/Mechanist/Armor/):
    BrassHelmet_Head.png        40x1120   20 frames of 40x56
    BrassChestplate_Body.png    360x224   1.4 composite layout, 9x4 cells
    BrassGreaves_Legs.png       40x1120
    BrassHelmet.png, BrassChestplate.png, BrassGreaves.png   item icons
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from make_scrap_art import Canvas as LCanvas, export as lexport  # noqa: E402
import make_mechanist_art as mech  # noqa: E402

OUT = "Content/Mechanist/Armor/"
FW, FH = mech.FW, mech.FH
LAYOUT = mech.LAYOUT
BRASS = ("B", "D", "E", "F", "G")                   # outline, dark, mid, light, shine
STEEL = mech.STEEL
DARK = mech.DARK
rows = mech.rows
shade = mech.shade


# ================================================================================================
# Helmet (one 20x28 frame facing right; the head sits at about x 6..14, y 5..14, face on the right)
# ================================================================================================
HELM = {3: (8, 12), 4: (6, 14), 5: (5, 15), 6: (5, 15), 7: (5, 16), 8: (5, 16), 9: (5, 16), 10: (5, 16), 11: (5, 16), 12: (6, 15)}


def helmet_frame():
    c = LCanvas(FW, FH)
    shade(c, rows(HELM), BRASS)
    for (x, y, ch) in ((9, 1, "i"), (10, 1, "i"), (9, 2, "q"), (10, 2, "k")):     # the steam stack on the crown (from y 1:
        c.set(x, y, ch)                                                           # the walk frames lift the head 1 px)
    for (x, y, ch) in ((12, 6, "q"), (13, 6, "r"), (14, 6, "q"), (15, 6, "k"),   # the porthole: a steel ring...
                       (11, 7, "q"), (12, 7, "v"), (13, 7, "u"), (14, 7, "w"), (15, 7, "v"), (16, 7, "k"),
                       (11, 8, "q"), (12, 8, "w"), (13, 8, "w"), (14, 8, "v"), (15, 8, "v"), (16, 8, "k"),
                       (11, 9, "k"), (12, 9, "v"), (13, 9, "v"), (14, 9, "v"), (15, 9, "j"), (16, 9, "i"),
                       (12, 10, "k"), (13, 10, "k"), (14, 10, "j"), (15, 10, "i")):          # ...round verdigris glass
        c.set(x, y, ch)
    c.set(13, 7, "t")                                                             # the glass's glint
    for (x, y) in ((11, 6), (16, 6), (11, 10), (16, 10)):                        # rivets round the porthole
        c.set(x, y, "G" if x < 13 else "E")
    for (x, y, ch) in ((6, 8, "d"), (7, 8, "d"), (6, 9, "c"), (7, 9, "d"), (6, 10, "c")):   # the copper ear valve
        c.set(x, y, ch)
    for x in range(6, 16):                                                        # a riveted seam round the crown
        if c.get(x, 5) not in (".", "B"):
            c.set(x, 5, "G" if x % 3 == 0 and x < 11 else ("E" if x % 3 == 0 else c.get(x, 5)))
    c.set(8, 4, "G")                                                              # the dome's glint
    return c


def head_sheet():
    sheet = LCanvas(FW, FH * 20)
    frame = helmet_frame()
    for f, dy in enumerate(LAYOUT["head_bob"]):
        cell = LCanvas(FW, FH)
        cell.blit(frame, 0, dy)
        sheet.blit(cell, 0, f * FH)
    return sheet


# ================================================================================================
# Body (1.4 composite: 9x4 cells of 20x28)
# ================================================================================================
TORSO = [                  # x 6..13, y 13..20: a brass breastplate, the pressure gauge running hot, a steel belt
    "BFGGFFEB",
    "BFEqrqDB",
    "BEqtzrDB",
    "BEqxtqDB",
    "BFDqqDCB",
    "BEGEEDCB",
    "BEEEDDCB",
    "iqkFGkqi",
]
BOILER = [                 # the copper boiler on the back, x 2..6, y 12..19, steel hoops, a brass valve (two copper
    ".BFB.",               # shades keep each sprite within 16 colours)
    "cdddc",
    "ccdcc",
    "ikqki",
    "cdddc",
    "ccdcc",
    "ikqki",
    ".ccc.",
]
PAULDRON = [               # front shoulder, x 3..9, y 12..16: a brass dome with a steel rim and a rivet
    "...BBB.",
    "..BFGEB",
    ".BFGFDB",
    "ikqrqki",
    ".iDDDi.",
]
BACK_SHOULDER = ["BB", "FB", "EB", "ki"]


def torso_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows(BOILER), 2, 12)
    c.blit(LCanvas.from_rows(TORSO), 6, 13)
    return c


def pauldron_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows(PAULDRON), 3, 12)
    return c


def back_shoulder_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows(BACK_SHOULDER), 14, 13)
    return c


def limb(mask, pivot, hand_len=2.6):
    """Arm from a template mask: a brass sleeve with a steel band at the elbow, a dark iron gauntlet."""
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = LCanvas(FW, FH)
    if not pts:
        return c
    inside = set(pts)
    dist = {p: math.hypot(p[0] - pivot[0], p[1] - pivot[1]) for p in pts}
    far = max(dist.values())
    for (x, y) in pts:
        d = dist[(x, y)]
        hand = d >= far - hand_len
        band = not hand and abs(d - far * 0.55) < 0.6
        ramp = DARK if hand else (STEEL if band else BRASS)
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        dark = (x + 1, y) not in inside or (x, y + 1) not in inside
        if edge and not (lit and not dark and ramp is not BRASS):
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
# Legs (20 frames from the template): two brass greaves, steel knee caps, iron boots with a copper piston
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

    belt = sorted(x for (x, y) in pts if y == max(belt_rows))
    for (x, y), p in part.items():                               # the belt: leather, a brass buckle at the front
        if p == "belt":
            ends = outside(x - 1, y) or outside(x + 1, y)
            c.set(x, y, "l" if ends else ("n" if outside(x - 2, y) else "m"))
    if len(belt) >= 5:
        c.set(belt[-3], max(belt_rows), "G")
        c.set(belt[-2], max(belt_rows), "E")
    for (x, y), p in part.items():                               # hips: one brass plate, a dark crease above the split
        if p != "hip":
            continue
        if outside(x - 1, y) or outside(x + 1, y):
            c.set(x, y, "B")
        elif y == crotch - 1 and x == split.get(crotch, 10):
            c.set(x, y, "D")
        else:
            c.set(x, y, "F" if outside(x - 2, y) else "E")
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
            boot = y >= low - 1
            for i, x in enumerate(run):
                seam = leg == "R" and part.get((x - 1, y)) == "L"
                edge = outside(x - 1, y) or outside(x + 1, y)
                if seam or edge:
                    ch = "i" if boot else "B"
                elif y == low:
                    ch = "j"                                        # sole
                elif boot:
                    ch = "q" if i == 1 else "k"                     # the iron boot
                elif i == 1:
                    ch = "F"                                        # lit side of the greave
                elif i == len(run) - 1 or (i == len(run) - 2 and outside(run[-1] + 1, y)):
                    ch = "D"
                else:
                    ch = "E"
                c.set(x, y, ch)
            if y == knee:                                           # steel knee cap
                inner = [x for x in run if c.get(x, y) not in ("B", "i")]
                if len(inner) >= 2:
                    c.set(inner[-2], y, "r")
                    c.set(inner[-1], y, "q")
                elif inner:
                    c.set(inner[-1], y, "q")
            if y == low - 1 and len(run) >= 4:                      # the copper piston on the back of the boot
                c.set(run[1], y, "d")
    return c


def legs_sheet():
    sheet = LCanvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(legs_frame(mask), 0, f * FH)
    return sheet


# ================================================================================================
def export_all():
    lexport(head_sheet(), OUT + "BrassHelmet_Head.png")
    body = body_sheet()
    lexport(body, OUT + "BrassChestplate_Body.png")
    lexport(legs_sheet(), OUT + "BrassGreaves_Legs.png")
    lexport(mech.crop(helmet_frame()), OUT + "BrassHelmet.png")
    lexport(mech.crop(mech.body_idle(body)), OUT + "BrassChestplate.png")
    lexport(mech.crop(legs_frame(LAYOUT["legs"][5])), OUT + "BrassGreaves.png")


if __name__ == "__main__":
    export_all()
