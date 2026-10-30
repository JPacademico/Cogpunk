"""Source for the Jaeger armor and the Cogpunker Manual (D4), 2026-10-28. Run from the repo root:

    python -P art/mecharmy/make_jaeger_armor.py

The Jaeger miniboss's armour cut down to a person (user-set 2026-10-28: the Jaeger drops one piece at a time): its
verdigris plating, hazard-striped brass trim and furnace reactor. Drawn at 1x, exported at 2x nearest-neighbour,
Cogpunk palette only (the verdigris ramp gets its own ramp-0 outline letter here, the colour the boss art already uses),
lit from the top-left, ramp-0 outlines. Static (no animated parts). Layout: art/templates/armor_layout.json (shapes);
the pixels are drawn here with the letter palette of art/scrap/make_scrap_art.py.

    Jaeger Helmet        a heavy rounded verdigris war-helm with a brass crest ridge, a dark visor band with one long
                         verdigris eye slit (the Jaeger's visor), a brass jaw guard with a hazard stripe, a rivet row
    Jaeger Chestplate    a verdigris chest plate with an ember furnace reactor in a brass ring, a hazard-striped brass
                         belt, big hazard-striped pauldrons, verdigris sleeves with a brass band and iron gauntlets
    Jaeger Greaves       verdigris greaves split into two legs, brass knee caps, iron boots with a piston ram
    Cogpunker Manual     the consumable: a thick leather-bound manual with a brass cog on the cover and a page marker

Outputs (Content/MechArmy/):
    Armor/JaegerHelmet_Head.png        40x1120   20 frames of 40x56
    Armor/JaegerChestplate_Body.png    360x224   1.4 composite layout, 9x4 cells
    Armor/JaegerGreaves_Legs.png       40x1120
    Armor/JaegerHelmet.png, JaegerChestplate.png, JaegerGreaves.png   item icons
    Items/CogpunkerManual.png          32x32
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "mechanist"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
import make_scrap_art  # noqa: E402
from make_scrap_art import Canvas as LCanvas, export as lexport  # noqa: E402
import make_mechanist_art as mech  # noqa: E402  (shade, rows, the template layout and leg specs)

OUT = "Content/MechArmy/"
FW, FH = mech.FW, mech.FH
LAYOUT = mech.LAYOUT
make_scrap_art.PAL["%"] = (23, 52, 48)              # verdigris ramp 0 (RAMP["verd"][0]): the outline of the plating

VERD = ("%", "v", "w", "u", "u")                    # outline, dark, mid, light, shine
BRASS = mech.BRASS
DARK = mech.DARK
rows = mech.rows
shade = mech.shade


def hazard(c, pts, period=2):
    """Brass and dark iron stripes falling to the right."""
    for (x, y) in pts:
        c.set(x, y, "E" if ((x + y) // period) % 2 == 0 else "i")


# ================================================================================================
# Helmet (one 20x28 frame facing right; the head sits at about x 6..14, y 5..14, face on the right)
# ================================================================================================
HELM = {2: (8, 12), 3: (6, 14), 4: (5, 15), 5: (5, 15), 6: (5, 16), 7: (5, 16), 8: (5, 16), 9: (5, 16), 10: (5, 16), 11: (6, 16)}


def helmet_frame():
    c = LCanvas(FW, FH)
    shade(c, rows(HELM), VERD)
    for x in range(8, 13):                                       # brass crest ridge along the top
        c.set(x, 1, "B" if x in (8, 12) else ("G" if x == 9 else "F"))
        c.set(x, 2, "D" if x != 12 else "B")
    for (x, y) in ((7, 4), (9, 4), (11, 4), (13, 4)):            # a rivet row under the crest
        c.set(x, y, "u")
        c.set(x + 1, y + 1, "v")
    for x in range(9, 17):                                       # the visor band: dark iron, one long verdigris eye slit
        c.set(x, 7, "i")
        c.set(x, 8, "u" if 11 <= x <= 15 else "i")
        c.set(x, 9, "i")
    c.set(16, 8, "w")
    c.set(12, 8, "t")                                            # the eye's hot spot
    hazard(c, [(x, 10) for x in range(10, 17)])                  # the jaw guard: brass with a hazard stripe
    for x in range(11, 16):
        c.set(x, 11, "D" if x % 2 else "C")
    c.set(6, 8, "D")                                             # the ear bolt
    c.set(7, 8, "F")
    c.set(7, 9, "C")
    c.set(7, 3, "u")                                             # the glint
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
TORSO = [                  # x 6..13, y 13..20: verdigris plate, the reactor in a brass ring (front of the chest, clear
    "%wuuwwv%",            # of the front pauldron), a hazard-striped belt
    "%wwDEEC%",
    "%wwEzyC%",
    "%wvEyyB%",
    "%wvCBBv%",
    "%wwwvvv%",
    "%wwvvv%%",
    "BEiEiEiB",
]
STACK = [                  # a smokestack on the back, x 3..5, y 10..17 (the Jaeger's), behind the torso
    ".i.",
    "iki",
    "iqi",
    "ikI",
    "iki",
    "iDi",
    "iki",
    "iii",
]
PAULDRON = [               # front shoulder, x 3..8, y 11..15: a verdigris shell with a hazard-striped rim
    "..%%%.",
    ".%uuw%",
    "%uwwv%",
    "EiEiEi",
    ".BCCB.",
]
BACK_SHOULDER = ["%%", "u%", "w%", "Ei", "%%"]


def torso_cell():
    c = LCanvas(FW, FH)
    c.blit(LCanvas.from_rows([r.replace("I", "i") for r in STACK]), 3, 10)
    c.blit(LCanvas.from_rows(TORSO), 6, 13)
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
    """Arm from a template mask: a verdigris sleeve with a brass band at the elbow, a dark iron gauntlet."""
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
        ramp = DARK if hand else (BRASS if band else VERD)
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
# Legs (20 frames from the template): two verdigris greaves, brass knee caps, iron boots with a piston
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

    for (x, y), p in part.items():                               # the belt: hazard-striped brass
        if p == "belt":
            c.set(x, y, "B" if outside(x - 1, y) or outside(x + 1, y) else ("E" if (x // 2) % 2 == 0 else "i"))
    for (x, y), p in part.items():                               # hips: one verdigris plate, a dark crease above the split
        if p != "hip":
            continue
        if outside(x - 1, y) or outside(x + 1, y):
            c.set(x, y, "%")
        elif y == crotch - 1 and x == split.get(crotch, 10):
            c.set(x, y, "v")
        else:
            c.set(x, y, "u" if outside(x - 2, y) else "w")
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
                    ch = "i" if boot else "%"
                elif y == low:
                    ch = "j"                                        # sole
                elif boot:
                    ch = "q" if i == 1 else "k"                     # the iron boot
                elif i == 1:
                    ch = "u"                                        # lit side of the greave
                elif i == len(run) - 1 or (i == len(run) - 2 and outside(run[-1] + 1, y)):
                    ch = "v"
                else:
                    ch = "w"
                c.set(x, y, ch)
            if y == knee:                                           # brass knee cap
                inner = [x for x in run if c.get(x, y) not in ("%", "i")]
                if len(inner) >= 2:
                    c.set(inner[-2], y, "F")
                    c.set(inner[-1], y, "E")
                elif inner:
                    c.set(inner[-1], y, "E")
            if y == low - 1 and len(run) >= 4:                      # the piston ram on the back of the boot
                c.set(run[1], y, "s")
    return c


def legs_sheet():
    sheet = LCanvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(legs_frame(mask), 0, f * FH)
    return sheet


# ================================================================================================
# Cogpunker Manual (16x16): a thick leather-bound manual, a brass cog on the cover, a verdigris page marker
# ================================================================================================
MANUAL = [
    "................",
    "...lllllllll....",
    "..lmnnnnnnnml...",
    "..lnmmmmmmmmls..",
    "..lnmmDmmDmmlss.",
    "..lnmmEFFEmmlst.",
    "..lnmDFBBFDmlst.",
    "..lnmmFBBFmmlst.",
    "..lnmDEFFEDmlst.",
    "..lnmmmDDmmmlst.",
    "..lnmmmmmmmmlst.",
    "..lnmmmmmmmmlst.",
    "..lmmmmmmmmmlss.",
    "..llllwlllllls..",
    "......wv........",
    "......v.........",
]


def manual_icon():
    return LCanvas.from_rows(MANUAL)


# ================================================================================================
def export_all():
    lexport(head_sheet(), OUT + "Armor/JaegerHelmet_Head.png")
    body = body_sheet()
    lexport(body, OUT + "Armor/JaegerChestplate_Body.png")
    lexport(legs_sheet(), OUT + "Armor/JaegerGreaves_Legs.png")
    lexport(mech.crop(helmet_frame()), OUT + "Armor/JaegerHelmet.png")
    lexport(mech.crop(mech.body_idle(body)), OUT + "Armor/JaegerChestplate.png")
    lexport(mech.crop(legs_frame(LAYOUT["legs"][5])), OUT + "Armor/JaegerGreaves.png")
    lexport(manual_icon(), OUT + "Items/CogpunkerManual.png")


if __name__ == "__main__":
    export_all()
