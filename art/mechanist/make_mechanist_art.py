"""Source for the Mechanist slice's sprites (D4), 2026-10-27. Run from the repo root:

    python -P art/mechanist/make_mechanist_art.py

Drawn at 1x and exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left, ramp-0 outlines.

Polished armor (the first Mechanist set): rusted metal buffed to a shine. A polished steel helmet with a brass brow rim,
a verdigris visor lens and a little pressure gauge for a crest; a polished chest plate with a brass collar and belt
trim, rivets, a gauge on the chest and a small verdigris boiler riding on the back; polished greaves (two legs split by a
dark seam, each with a brass knee cap; redrawn 2026-10-27 so they no longer read as a skirt), a leather belt with a brass
buckle and dark iron boots. Static (no animated parts). Layout:
art/templates/armor_layout.json (shapes only); the armor's own pixels are drawn here with the letter palette of
art/scrap/make_scrap_art.py.

Outputs (Content/Mechanist/):
    Armor/PolishedHelmet_Head.png        40x1120   20 frames of 40x56
    Armor/PolishedChestplate_Body.png    360x224   1.4 composite layout, 9x4 cells
    Armor/PolishedPants_Legs.png         40x1120
    Armor/PolishedHelmet.png, PolishedChestplate.png, PolishedPants.png   item icons
    SteamGauge.png                       32x330    5 frames of 32x64 (stride 66): the tank behind the glass, the steam,
                                                   the overheated steam, the front (cage, glint, valve), the valve turned
    Overheat.png                         32x32     debuff icon: a pressure gauge in the red, venting steam
    Weapons/TrapperChain.png             36x32     item: a coil of chain ending in a dented bear trap
    Weapons/TrapperChainProjectile.png   32x60     2 frames (stride 30) of 32x28: the trap open, snapped shut; pointing right
    Weapons/TrapperChainLink.png         8x10      one chain link (vertical; rotated along the chain in code like vanilla)
    Accessories/GlassContainer.png       20x28     item: a small glass steam tank with iron caps (2026-10-27)
    Accessories/BrassContainer.png       32x32     item: the same tank caged in brass, with a valve wheel (2026-10-27)
    Accessories/PolishedCog.png          28x28     item: a rusted cog buffed back to a shine, steel-rimmed hub (2026-10-28)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from make_scrap_art import Canvas as LCanvas, export as lexport  # noqa: E402  (letter palette, 2x export)
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Ring, Capsule, Union, box, Canvas, flat, face, dome, cyl, line  # noqa: E402
import make_trashtr0m_art as boss  # noqa: E402
from make_trashtr0m_loot import img, img_fit  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Mechanist/"
FW, FH = 20, 28
LAYOUT = json.load(open(os.path.join(ROOT, "art/templates/armor_layout.json")))
I, B, C, V, E, S, LE, A = (RAMP[k] for k in ("iron", "brass", "copper", "verd", "ember", "steam", "leather", "aether"))

# Letter ramps (outline, dark, mid, light[, shine]) for the armor.
STEEL = ("i", "k", "q", "r", "t")          # polished steel: ramp 0 outline, then bright, with a steam-white shine
BRASS = ("B", "D", "E", "F", "G")
DARK = ("i", "j", "k", "q", "r")
LEATHER = ("l", "l", "m", "n", "n")


# ================================================================================================
# Armor helpers
# ================================================================================================
def shade(c, pts, ramp, shine=True):
    """Outline on the silhouette except a lit top-left edge pixel, light just inside the top-left, dark just inside the
    bottom-right, a one-pixel shine (ramp[4]) on the top-left inner corner of every run (polished)."""
    inside = set(pts)
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        dark = (x + 1, y) not in inside or (x, y + 1) not in inside
        if edge and not (lit and not dark and ramp[0] not in ("B", "l")):
            ch = ramp[0]
        elif edge:
            ch = ramp[2]
        elif (x - 1, y - 1) not in inside or (x - 2, y) not in inside or (x, y - 2) not in inside:
            ch = ramp[3]
        elif (x + 1, y + 1) not in inside or (x + 2, y) not in inside or (x, y + 2) not in inside:
            ch = ramp[1]
        else:
            ch = ramp[2]
        c.set(x, y, ch)
    if shine:
        for (x, y) in pts:
            if c.get(x, y) == ramp[3] and (x - 1, y - 1) in inside and c.get(x - 1, y - 1) not in (ramp[3], ramp[4]) \
                    and (x + 1, y) in inside and (x, y + 1) in inside and (x - 1, y) in inside and (x, y - 1) in inside:
                c.set(x, y, ramp[4])
                break


def rows(spans):
    return [(x, y) for y, (x0, x1) in spans.items() for x in range(x0, x1 + 1)]


# ================================================================================================
# Helmet (one 20x28 frame facing right; the head sits at about x 6..14, y 5..14, face on the right)
# ================================================================================================
DOME = {3: (8, 12), 4: (7, 13), 5: (6, 14), 6: (5, 15), 7: (5, 15)}
NECK = {8: (5, 9), 9: (5, 9), 10: (5, 9), 11: (6, 8)}


def helmet_frame():
    c = LCanvas(FW, FH)
    shade(c, rows(DOME), STEEL)
    shade(c, rows(NECK), STEEL, shine=False)
    # the pressure gauge crest: a brass ring round a white face, a dark needle (y 1..3, its bottom row set into the
    # dome). It starts at y 1, not 0: the walk frames lift the head 1 px and a pixel at y -1 would land in the bottom
    # row of the frame above, under the player's feet (fixed 2026-10-27).
    for (x, y, ch) in ((9, 1, "D"), (10, 1, "D"), (8, 2, "D"), (9, 2, "t"), (10, 2, "t"), (11, 2, "B"),
                       (8, 3, "E"), (9, 3, "j"), (10, 3, "s"), (11, 3, "B")):
        c.set(x, y, ch)
    for x in range(5, 16):                                       # brass brow rim with two rivets, the brim at the front
        c.set(x, 8, "B" if x in (5, 15) else ("G" if x in (8, 12) else ("F" if x < 10 else "E")))
    c.set(16, 8, "B")
    for (x, y, ch) in ((12, 9, "i"), (13, 9, "v"), (14, 9, "w"), (15, 9, "i"),     # the visor lens
                       (12, 10, "i"), (13, 10, "u"), (14, 10, "w"), (15, 10, "i"),
                       (12, 11, "i"), (13, 11, "i"), (14, 11, "i"),
                       (11, 10, "C"), (10, 10, "D")):                              # its brass strap
        c.set(x, y, ch)
    for (x, y, ch) in ((6, 9, "D"), (7, 9, "F"), (6, 10, "C"), (7, 10, "D")):     # the ear valve
        c.set(x, y, ch)
    c.set(9, 4, "t")                                              # a second glint on the dome
    return c


def head_sheet():
    sheet = LCanvas(FW, FH * 20)
    frame = helmet_frame()
    for f, dy in enumerate(LAYOUT["head_bob"]):
        cell = LCanvas(FW, FH)
        cell.blit(frame, 0, dy)                                   # clipped to its own cell: nothing spills into a neighbour
        sheet.blit(cell, 0, f * FH)
    return sheet


# ================================================================================================
# Body (1.4 composite: 9x4 cells of 20x28)
# ================================================================================================
TORSO = [                  # x 6..13, y 13..20: polished plate, brass collar and belt trim, rivets, a chest gauge
    "BEEFFEEB",
    "iqrtrqki",
    "iqrDEqki",
    "iqDtsCki",
    "iqrCBqki",
    "iqrqqkki",
    "iqrrqkji",
    "BDEEEDCB",
]
BOILER = [                 # the little boiler on the back, x 2..6, y 12..19 (behind the torso, facing right)
    ".BEB.",
    "iwuwi",
    "iDFDi",
    "ivwvi",
    "ivwvi",
    "iDEDi",
    "ivvvi",
    ".iii.",
]
PAULDRON = [               # front shoulder, x 3..9, y 12..16: a polished dome plate with a brass rim
    "...iii.",
    "..iqrti",
    ".iqrrqi",
    "BEFFEDB",
    ".BCCCB.",
]
BACK_SHOULDER = ["ii", "ri", "qi", "ii"]


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


ARM_PIVOT = {"front": (6.0, 13.5), "back": (14.0, 13.5)}


def limb(mask, pivot, hand_len=2.6):
    """Arm from a template mask: a polished steel sleeve with a brass band at the elbow, a dark iron gauntlet."""
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
        ramp = DARK if hand else (BRASS if band else STEEL)
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
            cell = limb(mask, ARM_PIVOT[side])
        sheet.blit(cell, col * FW, row * FH)
    return sheet


# ================================================================================================
# Legs (20 frames from the template)
# ================================================================================================
# Two legs, not a skirt (user, 2026-10-27): the template's leg silhouette is one solid block that flares at the feet, so
# shading it as one shape with a brass band across it read as a skirt. Every frame is now split into a left and a right
# leg below the crotch (split column per row, hand-picked per unique template shape), each outlined on its own so a
# ramp-0 seam runs between them, with its own brass knee cap and its own dark iron boot.
# spec: frame -> (belt rows, crotch row, {row: split x}); x < split is the left leg.
LEG_SPECS = {
    0: ({21}, 23, {23: 10, 24: 10, 25: 10, 26: 10}),
    5: ({20, 21}, 22, {22: 10, 23: 10, 24: 10, 25: 10, 26: 10}),
    6: ({21}, 22, {22: 10, 23: 10, 24: 10, 25: 10, 26: 10}),
    7: ({20}, 23, {23: 10, 24: 9, 25: 9, 26: 9}),
    8: ({20}, 23, {23: 10, 24: 11, 25: 11, 26: 11}),
    9: ({20}, 23, {23: 10, 24: 10, 25: 10, 26: 10}),
    10: ({21}, 23, {23: 10, 24: 10, 25: 10, 26: 10}),
    13: ({21}, 23, {23: 10, 24: 10, 25: 10, 26: 10}),
    14: ({20}, 22, {22: 10, 23: 10, 24: 10, 25: 10, 26: 10}),
    16: ({20}, 23, {23: 10, 24: 10, 25: 10, 26: 10}),
    17: ({21}, 23, {23: 10, 24: 10, 25: 10, 26: 10}),
}


def _leg_spec(mask):
    """The spec of the first template frame with this exact shape (frames repeat shapes: 1-4, 11 and 19 are 0...)."""
    for f, m in enumerate(LAYOUT["legs"]):
        if m == mask:
            for g in range(f, -1, -1):
                if g in LEG_SPECS and LAYOUT["legs"][g] == mask:
                    return LEG_SPECS[g]
    raise KeyError("no leg spec for this template shape")


def legs_frame(mask):
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = LCanvas(FW, FH)
    if not pts:
        return c
    inside = set(pts)
    belt_rows, crotch, split = _leg_spec(mask)
    part = {}                                                       # pixel -> "belt" | "hip" | "L" | "R"
    for (x, y) in pts:
        if y in belt_rows:
            part[(x, y)] = "belt"
        elif y < crotch:
            part[(x, y)] = "hip"
        else:
            part[(x, y)] = "L" if x < split[y] else "R"

    def outside(x, y):
        return (x, y) not in inside

    # belt: leather, a brass buckle on the front (right) third
    belt = sorted(x for (x, y) in pts if y == max(belt_rows))
    for (x, y), p in part.items():
        if p != "belt":
            continue
        ends = outside(x - 1, y) or outside(x + 1, y)
        c.set(x, y, "l" if ends else ("n" if outside(x - 2, y) else "m"))
    if len(belt) >= 5:
        c.set(belt[-3], max(belt_rows), "F")
        c.set(belt[-2], max(belt_rows), "E")
    # hips: one polished plate, a dark crease above the split
    for (x, y), p in part.items():
        if p != "hip":
            continue
        if outside(x - 1, y) or outside(x + 1, y):
            c.set(x, y, "i")
        elif y == crotch - 1 and x == split.get(crotch, 10):
            c.set(x, y, "k")
        else:
            c.set(x, y, "r" if outside(x - 2, y) else "q")
    # legs: each one shaded on its own
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
                seam = leg == "R" and part.get((x - 1, y)) == "L"   # the line between the legs
                edge = outside(x - 1, y) or outside(x + 1, y)
                if seam or edge:
                    ch = "i"
                elif y == low:
                    ch = "j"                                        # sole
                elif i == 1:
                    ch = "q" if y == low - 1 else "r"               # lit side (boot top / greave)
                elif y == low - 1 or i == len(run) - 1 or (i == len(run) - 2 and outside(run[-1] + 1, y)):
                    ch = "k"                                        # boot, or the shaded side
                else:
                    ch = "q"
                c.set(x, y, ch)
            if y == knee:                                           # brass knee cap on the front of the knee
                inner = [x for x in run if c.get(x, y) != "i"]
                if len(inner) >= 2:
                    c.set(inner[-2], y, "F")
                    c.set(inner[-1], y, "E")
                elif inner:
                    c.set(inner[-1], y, "E")
            if y == top and leg == "R" and height >= 4:             # a shine on the front thigh
                inner = [x for x in run if c.get(x, y) == "r"]
                if inner:
                    c.set(inner[0], y, "t")
    return c


def legs_sheet():
    sheet = LCanvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(legs_frame(mask), 0, f * FH)
    return sheet


def crop(c, pad=0):
    xs = [x for y in range(c.h) for x in range(c.w) if c.g[y][x] != "."]
    ys = [y for y in range(c.h) for x in range(c.w) if c.g[y][x] != "."]
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    out = LCanvas(x1 - x0 + 1, y1 - y0 + 1)
    for y in range(out.h):
        for x in range(out.w):
            out.set(x, y, c.get(x0 + x, y0 + y))
    return out


def body_idle(sheet):
    def cell(col, row):
        out = LCanvas(FW, FH)
        for y in range(FH):
            for x in range(FW):
                out.set(x, y, sheet.get(col * FW + x, row * FH + y))
        return out
    c = LCanvas(FW, FH)
    for col, row in ((2, 2), (0, 0), (2, 0), (0, 1), (1, 1)):
        c.blit(cell(col, row), 0, 0)
    return c


# ================================================================================================
# Steam gauge (UI): 16x32 frames
# ================================================================================================
GW, GH = 16, 32
FILL_TOP, FILL_BOTTOM = 5, 27            # the glass's inside rows (1x), = SteamGaugeSystem.FillTop/FillBottom / 2
GLASS_X0, GLASS_X1 = 4, 11               # the glass's inside columns


def gauge_back():
    cv = Canvas()
    # brass caps: a domed top with a valve stem, a footed base
    cv.part(Xf(), box(2.0, 1.0, 14.0, 5.0), "brass", face((-0.3, -0.6, 0.75), lo=2, hi=4, ramp_len=6), rust=0.0)
    cv.part(Xf(), box(1.0, 27.0, 15.0, 32.0), "brass", face((-0.3, -0.6, 0.75), lo=1, hi=4, ramp_len=6), rust=0.0)
    for x in range(6, 10):
        cv.put(x, 0, B[0] if x in (6, 9) else B[4])
    # the glass tube: dark walls, a dark empty inside
    for y in range(FILL_TOP, FILL_BOTTOM):
        cv.put(GLASS_X0 - 2, y, I[0])
        cv.put(GLASS_X0 - 1, y, I[2])
        cv.put(GLASS_X1 + 1, y, I[1])
        cv.put(GLASS_X1 + 2, y, I[0])
        for x in range(GLASS_X0, GLASS_X1 + 1):
            cv.put(x, y, I[1] if (x + y // 3) % 5 else A[0])
    for x in range(3, 13, 3):                                       # rivets on the caps
        cv.put(x, 2, B[5])
        cv.put(x + 1, 29, B[5])
    return cv


def gauge_fill(hot):
    cv = Canvas()
    ramp = E if hot else S
    for y in range(FILL_TOP, FILL_BOTTOM):
        for x in range(GLASS_X0, GLASS_X1 + 1):
            swirl = (x * 2 + y + (y // 4) * 3) % 7
            if x == GLASS_X0:
                col = ramp[3] if hot else S[3]                      # the lit side of the column
            elif x == GLASS_X1:
                col = ramp[0] if hot else S[0]
            elif swirl < 2:
                col = ramp[1]
            elif swirl < 5:
                col = ramp[2]
            else:
                col = ramp[3] if hot else S[1]
            cv.put(x, y, col)
    for y in range(FILL_TOP, FILL_BOTTOM, 6):                       # bubbles / puffs rising
        cv.put(GLASS_X0 + 2 + (y // 6) % 3, y, WHITE if not hot else E[3])
    return cv


def gauge_front(valve):
    cv = Canvas()
    for y in (12, 20):                                              # brass cage rings round the glass
        for x in range(GLASS_X0 - 2, GLASS_X1 + 3):
            cv.put(x, y, B[0] if x in (GLASS_X0 - 2, GLASS_X1 + 2) else (B[4] if x < 8 else B[3]))
    for y in list(range(FILL_TOP + 1, 10)) + list(range(14, 17)):  # the glass glint
        cv.put(GLASS_X0 + 1, y, WHITE)
    for y in range(7, 26, 4):                                       # tick marks
        cv.put(GLASS_X0 - 1, y, B[4])
    # the valve wheel on the right of the tank and its pipe
    cx, cy = 14, 16
    for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0)) if valve == 0 else ((1, -1), (1, 1), (-1, 1), (-1, -1)):
        cv.put(cx + dx, cy + dy, B[4])
    cv.put(cx, cy, B[1])
    cv.put(GLASS_X1 + 2, cy, I[0])
    for (dx, dy) in ((-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1)) if valve == 0 else \
            ((0, -2), (2, 0), (0, 2), (-2, 0), (1, -2), (-1, 2), (2, 1), (-2, -1)):
        x, y = cx + dx, cy + dy
        if 0 <= x < GW:
            cv.put(x, y, B[2])
    return cv


def gauge_sheet():
    frames = [img(gauge_back(), GW, GH), img(gauge_fill(False), GW, GH), img(gauge_fill(True), GW, GH),
              img(gauge_front(0), GW, GH), img(gauge_front(1), GW, GH)]
    return boss.vertical(frames, pad=1)


# ================================================================================================
# Steam containers (accessories, user-set 2026-10-27): the gauge's glass tank in miniature
# ================================================================================================
GLASS_CONTAINER = [        # 10x14: iron caps with a valve stem, a verdigris-tinted glass tube full of steam (denser at the bottom)
    "....ii....",
    "...iqri...",
    "..iiqkii..",
    ".iqrrqqkji",
    ".vttsssuv.",
    ".vtsstsuv.",
    ".vtssssuv.",
    ".vussssuv.",
    ".vusstsuv.",
    ".vussqsuv.",
    ".vusqqquv.",
    ".iqrqqqkji",
    ".ijkkkkkji",
    "..iiiiiii.",
]
BRASS_CONTAINER = [        # 16x16: the same tank caged in brass, a brass cap and foot, a valve wheel on a side pipe
    ".....BBB........",
    ".....BGB........",
    "...BBEFDBB......",
    "..BFGFFEEDB.....",
    "..BEFEEEDCB.....",
    "...vttssuv......",
    "..BEFEEEDCB.....",
    "...vtsstuv..BBB.",
    "...vtsssuv.BGDDB",
    "...vussqsvCB.E.B",
    "...vusqqqv.BDCCB",
    "..BEFEEEDCB.BBB.",
    "...vusqtuv......",
    "..BEFFEEDCB.....",
    "..BDEEEDDCB.....",
    "...BBBBBBB......",
]


def container_icon(rows):
    for r in rows:
        assert len(r) == len(rows[0]), r
    return LCanvas.from_rows(rows)


# ================================================================================================
# Overheat debuff icon (16x16)
# ================================================================================================
def overheat_icon():
    cv = Canvas()
    # steam venting from the top
    for (cx, cy, r) in ((5.0, 3.0, 2.0), (9.0, 2.0, 2.4), (12.0, 3.5, 1.6)):
        for p in cv.raster(Xf(), Ellipse(cx, cy, r, r * 0.8)):
            cv.put(p[0], p[1], S[2] if (p[0] + p[1]) % 3 else S[1])
    # the gauge: brass bezel, white face, the red zone, the needle pinned past it
    cv.part(Xf(), Ellipse(8.0, 9.5, 6.2, 6.2), "brass", dome(6.0, 7.5, 7.0, lo=1, hi=4, gain=1.3), rust=0.0)
    face_px = cv.raster(Xf(), Ellipse(8.0, 9.5, 4.6, 4.6))
    for (x, y) in face_px:
        ang = math.degrees(math.atan2(y + 0.5 - 9.5, x + 0.5 - 8.0))
        r = math.hypot(x + 0.5 - 8.0, y + 0.5 - 9.5)
        cv.put(x, y, E[1] if (r > 3.0 and -60 < ang < 10) else S[2])
    line(cv, Xf(), (8.0, 9.5), (11.6, 8.2), lambda n: I[0])
    cv.put(8, 9, I[0])
    cv.put(7, 9, B[1])
    for (x, y) in ((4, 9), (5, 6), (8, 5)):
        cv.put(x, y, I[2])                                          # tick marks
    return img(cv, 16, 16)


# ================================================================================================
# Trapper Chain: a dented bear trap on a steel chain
# ================================================================================================
def link(cv, cx, cy, vertical=True):
    """A 4x5 (or 5x4) oval chain link: iron, lit on the top-left, a dark hole."""
    w, h = (4, 5) if vertical else (5, 4)
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    for y in range(h):
        for x in range(w):
            corner = (x in (0, w - 1)) and (y in (0, h - 1))
            if corner:
                continue
            hole = 0 < x < w - 1 and 0 < y < h - 1
            if hole:
                if (vertical and h - 2 > 1 and 1 <= y <= h - 2) or (not vertical and w - 2 > 1):
                    continue
            col = I[4] if (x == 0 or y == 0) else (I[1] if (x == w - 1 or y == h - 1) else I[3])
            cv.put(x0 + x, y0 + y, col)


def bear_trap(cv, ox, oy, shut):
    """The trap pointing right, 16x14 around (ox, oy) = its centre: a spring plate (brass coil), two dented iron jaws
    with steel teeth, open (a V to the right) or snapped shut, a ring on the left for the chain."""
    # the ring the chain hooks into
    for (x, y, col) in ((0, 6, I[0]), (0, 7, I[0]), (1, 5, I[3]), (1, 8, I[1]), (2, 5, I[0]), (2, 8, I[0]), (1, 6, I[4]), (1, 7, I[2])):
        cv.put(ox - 8 + x, oy - 7 + y, col)
    # the base plate with its brass spring coil
    cv.part(Xf(), box(ox - 6.0, oy - 2.0, ox + 0.0, oy + 2.0), "iron", face((-0.3, -0.6, 0.75), lo=1, hi=3), rust=0.5)
    for k in range(3):
        cv.put(ox - 5 + k * 2, oy - 1, B[4])
        cv.put(ox - 5 + k * 2, oy, B[2])
    # the jaws: two half-moons hinged at the plate, open (a V to the right) or snapped shut; steel teeth on the inner edge
    for side in (-1, 1):
        ang = side * (30.0 if not shut else 0.0)
        xf = Xf.pose(ang, (0.0, 0.0), (ox + 0.0, oy + (0.0 if side < 0 else 1.0)))
        jaw = Poly([(0.0, side * 0.2), (2.6, side * 2.9), (6.4, side * 3.2), (8.6, side * 1.6), (8.4, side * -0.6), (0.0, side * -0.6)])
        cv.part(xf, jaw, "iron", dome(3.0, side * 2.6 - 1.0, 6.0, lo=1, hi=4, gain=1.3), rust=0.5)
        for t in (2.0, 4.0, 6.0, 8.0):                              # steel teeth biting inwards
            q = xf.fwd((t - 0.5, side * -0.9))
            cv.put(int(math.floor(q[0])), int(math.floor(q[1])), S[2] if t < 8.0 else S[1])
        d = xf.fwd((5.0, side * 2.0))                               # a dent hammered into the jaw
        cv.darken(int(d[0]), int(d[1]))
        cv.darken(int(d[0]) + 1, int(d[1]))


def trap_frames():
    out = []
    for shut in (False, True):
        cv = Canvas()
        bear_trap(cv, 8, 7, shut)
        out.append(img(cv, 16, 14))
    return out


def chain_link():
    cv = Canvas()
    link(cv, 2, 2.5, vertical=True)
    return img(cv, 4, 5)


def trapper_chain_item():
    cv = Canvas()
    for k in range(5):                                              # the chain from the bottom left
        link(cv, 2.5 + k * 1.8, 14.0 - k * 1.8, vertical=k % 2 == 0)
    xf_cv = Canvas()
    bear_trap(xf_cv, 0, 0, False)
    for (x, y), col in xf_cv.px.items():                            # the trap at the top right (drawn pointing right)
        cv.put(x + 10, y + 5, col)
    return _fit(cv, 18, 16)


def _fit(cv, w, h):
    xs = [x for (x, _) in cv.px]
    ys = [y for (_, y) in cv.px]
    x0, y0 = min(xs), min(ys)
    bw, bh = max(xs) - x0 + 1, max(ys) - y0 + 1
    if bw > w or bh > h:
        # crop to the frame (the trap's ring end may overlap the chain): keep the top-right corner
        return boss.to_image(cv.px, max(xs) - w + 1, y0, w, h)
    return img(cv, w, h, (w - bw) // 2 - x0, (h - bh) // 2 - y0)


def polished_cog_icon():
    """Polished Cog (14x14 -> 28x28): eight brass teeth round a bright brass ring, a polished steel hub with a hole,
    a hard steam-white glint top-left (it was buffed back from rust)."""
    cv = Canvas()
    c = (6.5, 6.5)
    teeth = Union(*[Capsule(c, (c[0] + math.cos(math.radians(a)) * 6.4, c[1] + math.sin(math.radians(a)) * 6.4), 1.3)
                    for a in range(0, 360, 45)])
    cv.part(Xf(), Ellipse(c[0], c[1], 5.0, 5.0) | teeth, "brass", dome(4.5, 4.0, 7.5, lo=1, hi=5, gain=1.4), rust=0.0)
    cv.part(Xf(), Ellipse(c[0], c[1], 3.0, 3.0), "iron", dome(5.5, 5.5, 3.5, lo=2, hi=4, gain=1.3), rust=0.0)
    for (x, y) in ((6, 6), (7, 6), (6, 7), (7, 7)):
        cv.put(x, y, I[0])                                     # the axle hole
    for (x, y, col) in ((3, 2, WHITE), (4, 2, S[2]), (2, 3, S[2])):
        cv.put(x, y, col)
    return boss.to_image(cv.px, -0, -0, 14, 14)


# ================================================================================================
def export_all():
    lexport(head_sheet(), OUT + "Armor/PolishedHelmet_Head.png")
    body = body_sheet()
    lexport(body, OUT + "Armor/PolishedChestplate_Body.png")
    lexport(legs_sheet(), OUT + "Armor/PolishedPants_Legs.png")
    lexport(crop(helmet_frame()), OUT + "Armor/PolishedHelmet.png")
    lexport(crop(body_idle(body)), OUT + "Armor/PolishedChestplate.png")
    lexport(crop(legs_frame(LAYOUT["legs"][5])), OUT + "Armor/PolishedPants.png")
    boss.export(gauge_sheet(), OUT + "SteamGauge.png")
    boss.export(overheat_icon(), OUT + "Overheat.png")
    boss.export(trapper_chain_item(), OUT + "Weapons/TrapperChain.png")
    boss.export(boss.vertical(trap_frames(), pad=1), OUT + "Weapons/TrapperChainProjectile.png")
    boss.export(chain_link(), OUT + "Weapons/TrapperChainLink.png")
    lexport(container_icon(GLASS_CONTAINER), OUT + "Accessories/GlassContainer.png")
    lexport(container_icon(BRASS_CONTAINER), OUT + "Accessories/BrassContainer.png")
    boss.export(polished_cog_icon(), OUT + "Accessories/PolishedCog.png")


if __name__ == "__main__":
    export_all()
