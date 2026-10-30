"""Source for the Tyrant armor (D4): the mage set Tar Tyrant drops (at least one piece a kill). Run from the repo root:

    python -P art/bosses/tartyrant/make_tyrant_armor.py

Berserker redesign (user, 2026-10-30: "it should have a more berserker feel so add horns on the skull and make the cape
leave the chest naked (bra if female character) only with the cape, and the pants only an underwear and sandals"), in
the boss's own colours: glossy brown-black tar (Iron 0 outline, Leather 0/1 body, the cold Iron 2/3 gloss of a wet
surface) and tar-stained fossil bone (Leather outline and stains, Leather 2, Steam 1 dry faces, Brass 5 glints); an ember
in the skull's orbit. Drawn at 1x, exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left.

    Tyrant Skull     the boss's horned Tyrannosaurus skull worn as a hood: the cranium over the head, the long snout over
                     the face with a row of teeth, the ember in the orbit, a thick brow horn swept back over the head (its
                     far pair behind it, a step darker), a nose horn, tar oozing down the back of the neck
    Tyrant Cape      the chest and arms bare (vanilla draws the wearer's own skin there: ArmorIDs.Body.Sets.HidesTopSkin
                     is false, HidesHands is set false in TyrantCape); a tar collar over the back shoulder and a cord to a
                     bone clasp at the throat; for a female wearer a tar bra with a bone bead (the female torso cells, rows
                     2-3, decompiled PlayerDrawSet.CreateCompositeData); the cape itself is a back equip (TyrantCape_Back,
                     ArmorIDs.Body.Sets.IncludedCapeBack): 20 frames behind the wearer, hanging still, swaying when they
                     swing, flaring when they jump, billowing in a seven-frame wave while they walk, its hem ragged and
                     dripping, two bone beads sewn on it
    Tyrant Sandals   bare legs (vanilla draws the leg skin: Legs.Sets.HidesBottomSkin is false): a tar loincloth on a belt of
                     vertebrae, a flap hanging in front and behind, and bone-soled sandals strapped over the feet

Outputs (Content/Bosses/TarTyrant/Armor/):
    TyrantSkull_Head.png      40x1120   20 frames of 40x56
    TyrantCape_Body.png       360x224   1.4 composite layout, 9x4 cells (torso rows 0 and 2: male and female)
    TyrantCape_Back.png       40x1120   the cape, 20 frames (drawn with the body frame, behind the wearer)
    TyrantSandals_Legs.png    40x1120
    TyrantSkull.png, TyrantCape.png, TyrantSandals.png   item icons

No visual glitches (user): every piece stays inside its own 40x56 cell in every frame (the head and cape sheets carry
the walk bob, frames 7-9 and 14-16 one pixel up, and nothing sits above y = 1 so the bob never pushes a pixel into the
frame above); the loincloth covers the template's hip rows exactly and the sandals its bottom rows leg by leg (the split
of LEG_SPECS); tools/sim/armor_preview.py --skin --female --back checks it on a stand-in body.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "mechanist"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
from make_scrap_art import Canvas as LCanvas, export as lexport  # noqa: E402
import make_mechanist_art as mech  # noqa: E402  (shade, rows, the template layout and leg specs)

OUT = "Content/Bosses/TarTyrant/Armor/"
FW, FH = mech.FW, mech.FH
LAYOUT = mech.LAYOUT
BOB = LAYOUT["head_bob"]
rows = mech.rows
shade = mech.shade

TAR = ("i", "l", "l", "m", "k")                     # outline, dark, mid, light, gloss (rig.RAMP["tar"])
SKULL_BONE = ("l", "n", "s", "G", "G")              # the skull as the boss wears it: grey-white, cream on top, stained underneath


# ================================================================================================
# Skull (one 20x28 frame facing right; the head sits at about x 7..14, y 5..12, the eye at 12..13, 9)
# ================================================================================================
SKULL = {2: (8, 12), 3: (6, 14), 4: (5, 16), 5: (5, 18), 6: (5, 19), 7: (6, 19), 8: (7, 18)}
MANE = {4: (3, 5), 5: (3, 5), 6: (3, 6), 7: (3, 6), 8: (3, 7), 9: (4, 8), 10: (4, 8), 11: (5, 7)}
# the brow horn: rooted on the back of the skull's crown, swept back over the tar at the back of the head and tipping
# up to a point; lit along its top, a growth ridge across it, outlined underneath (x, y, letter). Nothing above y = 1:
# the walk bob lifts the frame a pixel and y = 0 would leave the cell.
NEAR_HORN = ((1, 1, "l"), (2, 1, "G"), (3, 1, "s"), (4, 1, "l"),
             (2, 2, "l"), (3, 2, "n"), (4, 2, "G"), (5, 2, "s"), (6, 2, "s"), (7, 2, "l"),
             (3, 3, "l"), (4, 3, "n"), (5, 3, "m"), (6, 3, "n"),
             (4, 4, "l"), (5, 4, "l"))
FAR_HORN = ((9, 1, "l"), (10, 1, "m"), (11, 1, "n"), (12, 1, "l"))   # its pair, peeking over the crown behind
NOSE_HORN = ((16, 3, "s"), (16, 2, "G"), (15, 3, "l"), (17, 3, "l"), (15, 2, "l"), (17, 2, "l"), (16, 1, "l"))


def skull_frame():
    c = LCanvas(FW, FH)
    for (x, y, ch) in FAR_HORN:                                    # behind everything: the skull covers its root
        c.set(x, y, ch)
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
    for (x, y, ch) in NEAR_HORN + NOSE_HORN:                       # the horns over the skull
        c.set(x, y, ch)
    return c


def bobbed_sheet(frame_fn):
    """20 frames of one drawing, each moved by the walk bob and clipped to its own cell."""
    sheet = LCanvas(FW, FH * 20)
    for f, dy in enumerate(BOB):
        cell = LCanvas(FW, FH)
        cell.blit(frame_fn(f), 0, dy)
        sheet.blit(cell, 0, f * FH)
    return sheet


# ================================================================================================
# Cape: the body sheet (bare torso: the collar, the clasp, the female bra) and the back equip (the cape itself)
# ================================================================================================
COLLAR = ((6, 13, "i"), (7, 13, "m"),                              # the cape folded over the back shoulder...
          (6, 14, "i"), (7, 14, "l"), (8, 14, "l"), (9, 14, "l"), (10, 14, "l"),   # ...and its cord round to the throat
          (11, 14, "l"), (12, 14, "G"), (13, 14, "l"), (12, 15, "n"))              # the bone clasp at the throat
BRA = ((6, 15, "i"), (7, 15, "l"), (8, 15, "l"), (9, 15, "m"), (10, 15, "m"), (11, 15, "i"), (13, 15, "i"),
       (6, 16, "i"), (7, 16, "l"), (8, 16, "l"), (9, 16, "l"), (10, 16, "m"), (11, 16, "k"), (12, 16, "s"), (13, 16, "l"),
       (10, 17, "i"), (11, 17, "l"), (12, 17, "l"), (13, 17, "i"))  # a tar band round the chest, its cup in front, a bone bead


def torso_cell(female):
    c = LCanvas(FW, FH)
    for (x, y, ch) in COLLAR:
        c.set(x, y, ch)
    if female:
        for (x, y, ch) in BRA:
            c.set(x, y, ch)
        c.set(12, 15, "l")                                         # the cord meets the cup
    return c


def body_sheet():
    """Only the torso cells carry anything (the collar; the bra in the female rows): the shoulders and arms are bare."""
    sheet = LCanvas(FW * 9, FH * 4)
    for (col, row) in ((0, 0), (1, 0), (0, 2), (1, 2)):
        sheet.blit(torso_cell(female=row == 2), col * FW, row * FH)
    return sheet


CAPE_TOP, CAPE_HEM = 12, 25                                        # behind the neck, down to the calves
CAPE_SPREAD = 4.0                                                  # how far its hem hangs out behind the back


def cape_outline(f):
    """The cape's left (trailing) edge per row and its hem, for player frame f: still (0), swaying with a swing (1-4),
    flared by a jump (5), billowing in a seven-frame wave while walking (6-19). Rows are before the walk bob."""
    left = {}
    hem = CAPE_HEM
    if f == 5:                                                     # the jump: it flares out behind and rides up
        hem = 23
        for y in range(CAPE_TOP, hem + 1):
            left[y] = 5 - int(round((y - CAPE_TOP) * 0.6))
    else:
        if 6 <= f <= 19:
            phase = (f - 6) % 7
            push = (0, 1, 2, 2, 1, 1, 0)[phase]                    # how far the hem trails back
            wave = (0, 0, 1, 1, 1, 0, 0)[phase]                    # a ripple travelling down it
        else:
            push, wave = ((0, 0, 1, 1, 0)[f] if f <= 4 else 0), 0
        for y in range(CAPE_TOP, hem + 1):
            t = (y - CAPE_TOP) / float(hem - CAPE_TOP)
            x = 5 - int(round(CAPE_SPREAD * t)) - int(round(push * t * t))
            if wave and 17 <= y <= 20:
                x -= 1
            left[y] = x
    return left, hem


def cape_frame(f):
    c = LCanvas(FW, FH)
    left, hem = cape_outline(f)
    right = 10                                                     # its front edge stays behind the body
    pts = set()
    for y in range(CAPE_TOP, hem + 1):
        for x in range(left[y], right + 1):
            pts.add((x, y))
    ragged = set()
    for x in range(left[hem], right + 1):                          # the ragged hem: every third pixel hangs one lower
        if (x + f) % 3 == 0:
            ragged.add((x, hem + 1))
    pts |= ragged
    inside = pts
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside and (x, y + 1) in inside and y < hem - 1
        if edge:
            ch = "l" if lit else "i"                               # selective outline: the lit edge one step lighter
        elif x == left[y] + 1 and CAPE_TOP + 2 <= y <= CAPE_TOP + 6:
            ch = "k"                                               # the wet sheen down its lit side
        elif (x - left[y]) in (2, 4) and y > CAPE_TOP + 1:
            ch = "m"                                               # two folds running down it
        else:
            ch = "l"
        c.set(x, y, ch)
    for (x, y, ch) in ((left[hem - 2] + 1, hem - 2, "G"), (left[hem - 2] + 1, hem - 1, "n"),   # two bone beads sewn on near the hem
                       (left[hem - 2] + 3, hem - 1, "s")):
        c.set(x, y, ch)
    drip_x = left[hem] + 2 + (f % 2)                               # a drip off the hem
    c.set(drip_x, hem + 2, "l")
    c.set(drip_x, hem + 3, "i")
    return c


def back_sheet():
    return bobbed_sheet(cape_frame)


# ================================================================================================
# Sandals: a tar loincloth on a belt of vertebrae (the hip rows of the template), bone-soled sandals (its bottom rows),
# the legs between them bare
# ================================================================================================
def legs_frame(mask):
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = LCanvas(FW, FH)
    if not pts:
        return c
    inside = set(pts)
    belt_rows, crotch, split = mech._leg_spec(mask)

    def outside(x, y):
        return (x, y) not in inside

    hips = [(x, y) for (x, y) in pts if y < crotch]
    for (x, y) in hips:
        if y in belt_rows:                                         # the belt: a chain of vertebrae
            ch = "l" if outside(x - 1, y) or outside(x + 1, y) else ("s" if x % 2 == 0 else "n")
        elif outside(x - 1, y) or outside(x + 1, y):
            ch = "i"
        elif y == crotch - 1 and x == split.get(crotch, 10):
            ch = "i"                                               # the crease between the legs
        elif outside(x - 2, y):
            ch = "m"                                               # the lit side of the cloth
        else:
            ch = "l"
        c.set(x, y, ch)
    low_hip = max(y for _, y in hips)
    run = sorted(x for (x, y) in hips if y == low_hip)
    for (x0, side) in ((run[-2], 1), (run[0] + 1, -1)):           # the loincloth's flaps, in front and behind
        for k, y in enumerate((crotch, crotch + 1)):
            for x in (x0, x0 - side) if k == 0 else (x0,):
                c.set(x, y, "l" if k == 0 else "i")
        c.set(x0 + side, crotch, "i")
    for leg in ("L", "R"):
        mine = [(x, y) for (x, y) in pts if y >= crotch and ((x < split.get(y, 10)) == (leg == "L"))]
        if not mine:
            continue
        low = max(y for _, y in mine)
        for y in (low, low - 1):
            run = sorted(x for (x, yy) in mine if yy == y)
            for i, x in enumerate(run):
                if y == low:
                    ch = "l" if i in (0, len(run) - 1) else ("s" if i == len(run) - 2 else "n")   # the bone sole, its toe cap
                elif i % 2 == 0:
                    ch = "l"                                       # the straps over the foot, skin between them
                else:
                    continue
                c.set(x, y, ch)
            if y == low - 1 and run:
                c.set(run[-1], y, "s")                             # a bone toggle on the front strap
    return c


def legs_sheet():
    sheet = LCanvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(legs_frame(mask), 0, f * FH)
    return sheet


# ================================================================================================
# Item icons
# ================================================================================================
CAPE_ICON = [              # 14x15: the cape hung from its bone clasp, folds down it, a ragged dripping hem
    "......ll......",
    ".....lGsl.....",
    "..iiiillliii..",
    ".ilkllmllmlli.",
    ".ilkllmllmlli.",
    "ilkllmlllmllli",
    "illllmlllmllli",
    "illllmllllmlli",
    "illlmllllllmli",
    "illlmlllGllmli",
    "illlmlllnllmli",
    "illllllllllll.",
    "i.il.li.il.li.",
    "..i...i...i...",
    "..........l...",
]
SANDALS_ICON = [           # 16x12: the loincloth on its belt of vertebrae, and the pair of sandals under it
    "..lsnsnsnsnsl...",
    "..ilmlllllmli...",
    "...illlllli.....",
    "....illlli......",
    ".....ilil.......",
    "................",
    "................",
    "..l.l.s....l.l.s",
    ".lnnnnsl..lnnnns",
    "..llll.....llll.",
    "................",
    "................",
]


def icon(rows_):
    return LCanvas.from_rows(rows_)


# ================================================================================================
def export_all():
    lexport(bobbed_sheet(lambda f: skull_frame()), OUT + "TyrantSkull_Head.png")
    lexport(body_sheet(), OUT + "TyrantCape_Body.png")
    lexport(back_sheet(), OUT + "TyrantCape_Back.png")
    lexport(legs_sheet(), OUT + "TyrantSandals_Legs.png")
    lexport(mech.crop(skull_frame()), OUT + "TyrantSkull.png")
    lexport(mech.crop(icon(CAPE_ICON)), OUT + "TyrantCape.png")
    lexport(mech.crop(icon(SANDALS_ICON)), OUT + "TyrantSandals.png")


if __name__ == "__main__":
    export_all()
