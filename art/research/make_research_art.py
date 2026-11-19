"""The research update's art (2026-11-18). Run from the repo root:

    python -P art/research/make_research_art.py [--preview FILE]

User, 2026-11-18: "every player should start with a "Ancient research book" a material (as example on the prompt image) that
can be used with wood and clay to craft a "ancient research table". this research table structure can be interacted with
right click and it should open a menu with nodes ... the inspiration for the menu design is on this prompt as image".
Drawn by hand at 1x in the Cogpunk palette (pixel maps: these are small enough that every pixel is chosen), exported 2x (D4).
  * Items/AncientResearchBook.png: the reference's tome, upright, its cover facing: red leather, gilt corner plates with bone
    inlays, a gilt-ringed jade eye in the middle, blue gems either side of it and pearls above and below, violet page edges
    down its right side and under it, a violet ribbon hanging out, a red chain on its spine.
  * Tiles/AncientResearchTableTile.png (+ _Highlight): a 3x2 oak table (18 px tile stride at 2x, the bottom row 18 tall), the
    book open on it glowing jade (light in game), a clay ink pot with a quill on the left, a clay jar on the right.
  * Items/AncientResearchTable.png: the table as an item.
  * UI/ResearchNode.png: a node's square in its three states (locked: dark iron; ready: jade; researched: gilt), 28 x 28,
    each with the reference's deep violet field, 1 px apart.
  * UI/ResearchKnowledge.png (2026-11-18): the knowledge point's sign, the book's jade eye in a gilt diamond (the window's
    header shows it with the number instead of the words).
  * Content/Bosses/TrashTr0m/Items/TetanusShot.png (2026-11-18): the Tetanus Shot, a glass syringe of green serum.
  * Weapons/BundleOfWands.png (2026-11-18): the Bundle of Wands, after the user's design (see BUNDLE).
  * Weapons/BanditsDream.png, CalcifiedBone.png, ResearchSlimed.png (2026-11-19): the gunblade after the user's photo,
    Calcified's spinning bone, the Slimed! debuff icon (see bandits_dream, calcified_bone, slimed_icon).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Research/"
K, G, GH, IV, AE, DN, OK, CU, ST = (RAMP[k] for k in ("crimson", "gilt", "ghost", "ivory", "aether", "denim", "oak", "copper", "steel"))


def pixmap(rows, legend):
    px = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                px[(x, y)] = legend[ch]
    return px


BOOK = (
    "OOOOOOOOOOOOO...",
    "OgGGgRRRgGGgOv..",
    "OGIgRRRRRgIgOVv.",
    "OGgRRrprRrgGOVV.",
    "OgRRrrrrrrrgOVV.",
    "OdRRrgGGgrrdOVV.",
    "ObRrgeewegrbOVV.",
    "OdRrGeEEeGrdOVV.",
    "OBrrgeeeegrBOVu.",
    "OdrrrghhgrrdOVu.",
    "OgrrrrprrrrgOVu.",
    "OGgrrrrrrrgGOVu.",
    "OGIgrrrrrgIhOuu.",
    "OgGGgrrrgGhhOuO.",
    "OOOOOOOOOmOOOO..",
    ".........mm.....",
)
BOOK_LEGEND = {"O": K[0], "R": K[3], "r": K[2], "d": K[1], "G": G[7], "g": G[5], "h": G[3], "I": IV[4], "e": GH[3], "E": GH[1],
               "w": GH[5], "b": DN[5], "B": DN[3], "p": IV[5], "v": AE[3], "V": AE[2], "u": AE[1], "m": AE[2]}


def book():
    px = pixmap(BOOK, BOOK_LEGEND)
    for y in (3, 5, 7, 9, 11):                                  # the chain down the spine
        px[(0, y)] = K[2] if y % 4 == 3 else K[1]
    return px


TABLE = (
    "..........,'',..........",
    ".........,'..',.........",
    "....q...GvvvvvvG........",
    "...cq..GvVvvvvVvG...jj..",
    "..cCCc.GVVvAvvVVG..jJJj.",
    "..cCCc.ggggggggggg.jJJj.",
    "..cccc.............jjjj.",
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "tttttttttttttttttttttttt",
    "oLLo................oLLo",
    ".LL..................LL.",
    ".LL..................LL.",
    ".LL..................LL.",
    ".LL..................LL.",
    ".LL..................LL.",
    ".Ll..................Ll.",
    "oooo................oooo",
)
TABLE_LEGEND = {"T": OK[4], "t": OK[2], "o": OK[0], "L": OK[3], "l": OK[1], "G": G[6], "g": G[4], "v": IV[5], "V": IV[3], "A": AE[2],
                ",": GH[3], "'": GH[5], "c": CU[2], "C": CU[3], "q": IV[4], "j": CU[1], "J": CU[3]}


def table():
    return pixmap(TABLE, TABLE_LEGEND)


def image(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def tile_sheet(img):
    """The 24 x 17 table cut into 8 px tiles with 1 px gaps (3 x 2, the bottom row 9 tall): 18 px stride at 2x."""
    out = Image.new("RGBA", (3 * 9, 9 + 10), (0, 0, 0, 0))
    for r, (y0, h) in enumerate(((0, 8), (8, 9))):
        for c in range(3):
            out.alpha_composite(img.crop((c * 8, y0, c * 8 + 8, y0 + h)), (c * 9, r * 9))
    return out


def highlight(img):
    w, h = img.size
    src = img.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or src[nx, ny][3] == 0:
                    dst[x, y] = (255, 255, 255, 255)
                    break
    return out


STARS = {(7, 9), (19, 6), (12, 15), (21, 18), (8, 20), (16, 23), (23, 11)}


def node_frame(state):
    """28 x 28: an outline, a 2 px band lit from the top-left, an inner line, the violet field; rivets in the corners."""
    band = ((ST[3], ST[2]), (GH[4], GH[2]), (G[7], G[4]))[state]
    rivet = (ST[4], G[6], GH[4])[state]
    px = {}
    for y in range(28):
        for x in range(28):
            edge = min(x, y, 27 - x, 27 - y)
            if edge == 0:
                c = ST[0]
            elif edge <= 2:
                c = band[0] if (x < 27 - y) else band[1]
            elif edge == 3:
                c = ST[0]
            else:
                c = AE[1] if (x, y) in STARS else AE[0]
            px[(x, y)] = c
    for (cx, cy) in ((4, 4), (22, 4), (4, 22), (22, 22)):
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            px[(cx + dx, cy + dy)] = rivet if (dx, dy) == (0, 0) else ST[0] if (dx, dy) == (1, 1) else band[1]
    return px


KNOWLEDGE = (
    "......o.......",
    ".....oGo......",
    "....oGgGo.....",
    "...oGg.gGo....",
    "..oGgeeegGo...",
    ".oGgeEEwegGo..",
    "oGg.eEEEe.gGo.",
    ".oGgeEEEegGo..",
    "..oGgeeegGo...",
    "...oGg.gGo....",
    "....oGgGo.....",
    ".....oGo......",
    "......o.......",
)
KNOWLEDGE_LEGEND = {"o": K[0], "G": G[7], "g": G[4], "e": GH[3], "E": GH[1], "w": GH[5]}


def knowledge():
    """The knowledge point's sign (the research window's header): the book's jade eye in a gilt diamond."""
    px = pixmap(KNOWLEDGE, KNOWLEDGE_LEGEND)
    for (x, y) in ((6, 0), (0, 6), (12, 6), (6, 12)):          # sparks at its points
        px[(x, y)] = GH[5]
    return px


SHOT = (
    "..........oo",
    ".........oSo",
    "........oSo.",
    ".......oBBo.",
    "......oWfBo.",
    ".....oWffo..",
    "....oWffo...",
    "...oWffo....",
    "..oBBBo.....",
    ".oPoo.......",
    "oPPo........",
    "oo..........",
)
SHOT_LEGEND = {"o": ST[0], "S": ST[6], "B": G[6], "W": IV[5], "f": RAMP["fel"][4], "P": G[4]}


def shot():
    """The Tetanus Shot: a glass syringe of green serum, a gilt hub and plunger, its steel needle up to the right."""
    return pixmap(SHOT, SHOT_LEGEND)


# The Bundle of Wands (2026-11-18, the user's design: reference/bundle_of_wands_user_2026-11-18.png, a blurred photo of a
# small sprite: a maroon grip at the left, the bundled shafts of the seven gem staffs bound by two bands, their gem tips in
# gilt fittings at the right; too blurred to trace pixel by pixel, so drawn on its layout and colours). Redrawn 2026-11-19
# (user: "the handle to staff base connection is abrupt and ugly and the metal lines are too big looking out of place"):
# the seven rods (amber, ruby, the magenta amethyst (the Amethyst ramp), topaz, sapphire, diamond, emerald) run from their
# gems at the head and converge, lit from the top-left, into a gilt binding ring and a leather-wrapped crimson grip with a
# gilt pommel; the two bands are a pixel wide, inside the bundle's outline, no brighter than the rods. Held like a gun,
# pointing right; 30 x 12 at 1x.
EB, AM, EM, HD = (RAMP[k] for k in ("ember", "amethyst", "emerald", "hide"))
BUNDLE_W, BUNDLE_H = 30, 12
# the seven rods, top to bottom at the head: (dark, mid, light)
RODS = [(EB[1], EB[2], EB[3]), (K[3], K[4], K[5]), (AM[2], AM[3], AM[4]), (G[5], G[7], G[8]), (DN[3], DN[4], DN[5]),
        (ST[5], ST[7], ST[8]), (EM[2], EM[3], EM[4])]
GRIP_X0, GRIP_X1 = 1, 8            # the wrapped grip
ROD_X0, ROD_X1 = 8, 22             # the rods: from the grip's binding to the head
BANDS = (12, 18)


def bundle():
    px = {}
    # rods: each a line from its place at the grip (rows 5..8, packed) to its place at the head (rows 3..9)
    for k, (dk, md, lt) in enumerate(RODS):
        y0 = 5 + k * 3.0 / 6.0
        y1 = 3 + k
        for x in range(ROD_X0, ROD_X1 + 1):
            t = (x - ROD_X0) / float(ROD_X1 - ROD_X0)
            y = int(round(y0 + (y1 - y0) * (t ** 0.7)))
            # lit from the top-left: the upper rods and the head end lighter, the grip end darker
            if t < 0.2:
                c = dk
            elif k <= 2 and 0.35 < t < 0.75:
                c = lt
            elif k >= 5 and t < 0.5:
                c = dk
            else:
                c = md
            px[(x, y)] = c
    # fill gaps between rods (a bundle, not a fan): a pixel between two rod pixels in a column takes the darker neighbour
    for x in range(ROD_X0, ROD_X1 + 1):
        ys = sorted(y for (xx, y) in px if xx == x)
        for y in range(ys[0], ys[-1] + 1):
            if (x, y) not in px:
                px[(x, y)] = ST[2]
    # thin bands: a pixel wide, only over the bundle, no brighter than the rods (user: "the metal lines are too big")
    for bx in BANDS:
        ys = sorted(y for (xx, y) in px if xx == bx)
        for i, y in enumerate(ys):
            px[(bx, y)] = ST[6] if i == 0 else ST[5] if i < len(ys) - 1 else ST[4]
    # the grip: crimson wood wrapped in leather (diagonal turns), tapering to a gilt pommel
    for x in range(GRIP_X0, GRIP_X1):
        for y in range(5, 9):
            wrap = (x + y) % 3 == 0
            px[(x, y)] = HD[4] if wrap and y == 5 else HD[2] if wrap else (K[2] if y == 5 else K[1])
    for y in range(5, 9):                          # the binding where the rods leave the grip: a gilt ring
        px[(GRIP_X1, y)] = G[7] if y == 5 else G[5] if y < 8 else G[3]
    for (x, y, c) in ((0, 6, G[6]), (0, 7, G[4])):  # the pommel
        px[(x, y)] = c
    # the head: the gems in their gilt fittings (as before)
    head = (
        "..SSS...",
        ".SoAYS..",
        "SogaAhS.",
        "SghPQgGS",
        "SoGHgyHS",
        "SgbCDWdS",
        "SoBdDgS.",
        "SgRTrS..",
        "SorRS...",
        "SgFES...",
        "SSSSS...",
    )
    legend = {"S": ST[0], "o": G[1], "g": G[4], "h": G[6], "A": EB[2], "Y": EB[3], "a": EB[1], "P": AM[3], "Q": AM[4], "G": G[7],
              "H": G[8], "y": G[5], "b": DN[3], "C": DN[5], "D": ST[8], "W": IV[5], "d": ST[6], "B": DN[4], "R": K[4], "T": K[5],
              "r": K[3], "F": EM[4], "E": EM[3]}
    for j, row in enumerate(head):
        for i, ch in enumerate(row):
            if ch != ".":
                px[(22 + i, j)] = legend[ch]
    # the outline: a dark pixel round everything (ramp-dark: the grip's crimson, the rest steel)
    out = dict(px)
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and 0 <= q[0] < BUNDLE_W and 0 <= q[1] < BUNDLE_H:
                out[q] = K[0] if q[0] <= GRIP_X1 else ST[0]
    return out



# ================================================================================================
# 2026-11-19: Bandit's Dream, Calcified's bone, the Slimed! debuff
# ================================================================================================
BONE, DEN, STM = RAMP["bone"], RAMP["denim"], RAMP["steam"]
BANDIT_LEGEND = dict({str(i): G[i] for i in range(10)},
                     x=ST[0], a=ST[1], b=ST[2], c=ST[3], d=ST[4], e=ST[5], f=ST[6], g=ST[7], h=ST[8],
                     A=OK[0], B=OK[1], C=OK[2], D=OK[3], E=OK[4], F=OK[5])
# The blade by columns: x -> top and bottom rows. Under the barrel its back is hidden; past the muzzle the spine runs on and
# rises to the upswept tip; the belly (a saw by the guard) curves up to meet it.
BANDIT_TOP = {x: 6 for x in range(15, 25)}
BANDIT_TOP.update({x: 5 for x in range(25, 34)})
BANDIT_TOP.update({34: 4, 35: 4, 36: 3, 37: 2, 38: 1, 39: 0})
BANDIT_BOT = {15: 12, 16: 12}
BANDIT_BOT.update({x: 11 for x in range(17, 27)})
BANDIT_BOT.update({27: 10, 28: 10, 29: 10, 30: 9, 31: 9, 32: 8, 33: 8, 34: 7, 35: 6, 36: 5, 37: 4, 38: 3, 39: 1})
# The gun, by hand (x, run): brass in gilt digits (0 the outline), the hammer and trigger steel, the grip oak
BANDIT_GUN = {
    0: [(2, "aa")],
    1: [(2, "afa")],
    2: [(3, "aea"), (7, "00000"), (22, "0")],
    3: [(3, "000"), (6, "0"), (7, "89987"), (12, "0"), (13, "000000000000")],
    4: [(3, "076"), (6, "0"), (7, "75857"), (12, "0"), (13, "88968896889"), (24, "x")],
    5: [(3, "065"), (6, "0"), (7, "64746"), (12, "0"), (13, "55455455455"), (24, "0")],
    6: [(3, "056"), (6, "0"), (7, "53635"), (12, "0"), (13, "54")],
    7: [(3, "045"), (6, "0"), (7, "42524"), (12, "0"), (13, "43")],
    8: [(3, "034"), (6, "1"), (7, "00000"), (12, "1"), (13, "32")],
    9: [(2, "AFDB"), (6, "000000000")],
    10: [(1, "AFEDA"), (7, "3"), (8, "c"), (10, "3")],
    11: [(1, "AEDCA"), (7, "4"), (10, "3")],
    12: [(0, "AED7CA"), (8, "43")],
    13: [(0, "ADCCBA")],
    14: [(0, "AAAAA")],
}


def bandits_dream():
    """Bandit's Dream (user, 2026-11-19, a photo: an engraved brass cap-and-ball revolver whose barrel runs on into a long
    curved Damascus blade, a saw on its belly by the guard, a slot along it, an upswept tip, a wooden grip). A gun: it points
    right (D4 rule 8), 40 x 15 at 1x. The blade by columns (outlined, its spine's bevel and its honed edge lit, Damascus
    waves inside), then the gun over it by hand: the hammer, the fluted cylinder, the engraved barrel with its bore and
    sight, the frame, the guard and trigger, the grip with a brass pin."""
    px = {}
    for x in range(15, 40):
        t, b = BANDIT_TOP[x], BANDIT_BOT[x]
        for y in range(t, b + 1):
            if y in (t, b) or x == 39:
                c = "a"
            elif y == b - 1:
                c = "h" if (x + y) % 4 else "g"                     # the honed edge
            elif y == t + 1:
                c = "g" if x % 5 else "f"                           # the spine's bevel
            else:
                v = math.sin(x * 0.9 + y * 2.3) + 0.5 * math.sin(x * 0.37 - y * 1.1)
                c = "f" if v > 0.7 else "e" if v > -0.4 else "d"    # Damascus waves (part space: fixed in the blade)
            px[(x, y)] = c
    for x in range(19, 27):                                         # the slot
        px[(x, 9)] = "b"
    for x in range(17, 26, 2):                                      # the saw teeth
        px[(x, 12)] = "a"
    for q in ((15, 13), (16, 13), (14, 14)):                        # the hook under the blade's root
        px[q] = "a"
    for y, runs in BANDIT_GUN.items():
        for x0, run in runs:
            for i, ch in enumerate(run):
                if ch != ".":
                    px[(x0 + i, y)] = ch
    return {q: BANDIT_LEGEND[c] for q, c in px.items()}


def calcified_bone():
    """Calcified's flying bone (user, 2026-11-19: "launches a small bone fliyng"): a small dog-bone, 8 spin poses over a
    half turn (a bone looks the same end for end), each drawn at its own angle (never a rotated bitmap), clockwise frame
    to frame; 7 x 7 cells 1 px apart (CalcifiedBone: Cell 14, Stride 16 at 2x). Cream lit up-left, a brown shadow line
    on its lower right (the outline where it faces away from the light)."""
    def seg_d(px, py, ax, ay, bx, by):
        vx, vy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px - ax - t * vx, py - ay - t * vy)

    sheet = Image.new("RGBA", (7, 8 * 8 - 1), (0, 0, 0, 0))
    for k in range(8):
        # the bone as shapes (a shaft, a pair of knobs at each end) at this angle, each pixel filled when 42% of it is
        # covered (6 x 6 samples): clean at every angle, unlike a rasterized line
        a = math.pi * k / 8.0
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        shape = set()
        for y in range(7):
            for x in range(7):
                hit = 0
                for sy in range(6):
                    for sx in range(6):
                        px, py = x + (sx + 0.5) / 6, y + (sy + 0.5) / 6
                        inside = seg_d(px, py, 3.5 - 1.9 * dx, 3.5 - 1.9 * dy, 3.5 + 1.9 * dx, 3.5 + 1.9 * dy) <= 0.6
                        for s in (-1, 1):
                            for o in (-1, 1):
                                kx, ky = 3.5 + s * 2.35 * dx + o * 0.72 * nx, 3.5 + s * 2.35 * dy + o * 0.72 * ny
                                inside = inside or math.hypot(px - kx, py - ky) <= 0.8
                        hit += inside
                if hit >= 0.42 * 36:
                    shape.add((x, y))
        cell = {}
        for (x, y) in shape:
            lit = (x - 1, y) not in shape or (x, y - 1) not in shape
            cell[(x, y)] = BONE[4] if lit else BONE[3]
        for (x, y) in shape:
            for q in ((x + 1, y), (x, y + 1)):
                if q not in shape and 0 <= q[0] < 7 and 0 <= q[1] < 7:
                    cell[q] = BONE[1]
        for (x, y), c in cell.items():
            sheet.putpixel((x, y + k * 8), tuple(c) + (255,))
    return sheet


def slimed_icon():
    """The Slimed! debuff (an enemy a player touches with the node unlocked): a dome of blue gel dripping, three drips of
    different lengths, a glint top-left. 16 x 16, the denim ramp shaded from the top-left, outlined in its darkest."""
    shape = set()
    for y in range(16):
        for x in range(16):
            if ((x + 0.5 - 8) / 6.6) ** 2 + ((y + 0.5 - 7.5) / 5.2) ** 2 <= 1.0 and y <= 10:
                shape.add((x, y))
    for (x0, y1) in ((4, 13), (8, 15), (11, 12)):                   # the drips: a column, a bead at the long ones' ends
        for y in range(9, y1 + 1):
            shape.add((x0, y))
        if y1 >= 13:
            shape.update({(x0 - 1, y1 - 1), (x0 + 1, y1 - 1), (x0 - 1, y1), (x0 + 1, y1)})
    for x in range(2, 15):                                          # the puddle's flat lower edge
        shape.add((x, 10))
    px = {}
    for (x, y) in shape:
        edge = any((x + dx, y + dy) not in shape for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            px[(x, y)] = DEN[0]
            continue
        v = 1.0 - math.hypot(x - 5.0, y - 3.5) / 9.0
        px[(x, y)] = DEN[5] if v > 0.72 else DEN[4] if v > 0.5 else DEN[3] if v > 0.25 else DEN[2]
    for q in ((5, 3), (6, 3), (5, 4)):                              # the glint
        if q in px:
            px[q] = STM[3]
    return px


def outputs():
    tab = image(table(), 24, 17)
    nodes = Image.new("RGBA", (28, 28 * 3 + 2), (0, 0, 0, 0))
    for s in range(3):
        nodes.alpha_composite(image(node_frame(s), 28, 28), (0, s * 29))
    return {
        OUT + "Items/AncientResearchBook.png": image(book(), 16, 16),
        OUT + "Items/AncientResearchTable.png": tab,
        OUT + "Tiles/AncientResearchTableTile.png": tile_sheet(tab),
        OUT + "Tiles/AncientResearchTableTile_Highlight.png": tile_sheet(highlight(tab)),
        OUT + "UI/ResearchNode.png": nodes,
        OUT + "UI/ResearchKnowledge.png": image(knowledge(), 14, 13),
        "Content/Bosses/TrashTr0m/Items/TetanusShot.png": image(shot(), 12, 12),
        OUT + "Weapons/BundleOfWands.png": image(bundle(), 30, 12),
        OUT + "Weapons/BanditsDream.png": image(bandits_dream(), 40, 15),
        OUT + "CalcifiedBone.png": calcified_bone(),
        OUT + "ResearchSlimed.png": image(slimed_icon(), 16, 16),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    out = outputs()
    for rel, im in out.items():
        export(im, rel)
    if args.preview:
        ims = list(out.values())
        sc = 6
        w = sum(im.width * sc + 16 for im in ims) + 16
        h = max(im.height * sc for im in ims) + 32
        sheet = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
        for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
            band = Image.new("RGBA", (w, h), bg + (255,))
            x = 16
            for im in ims:
                band.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (x, 16))
                x += im.width * sc + 16
            sheet.paste(band, (0, row * h))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
