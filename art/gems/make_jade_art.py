"""Source for jade and its default gem crafts (D4), 2026-11-09 (user: "a new gem that can be mined underground (same
behaviour and spawn as other default gems from terraria ex: amethyst emerald) called jade, and add the default gem crafts
for it (gem robe, phase saber, big gem)"). Run from the repo root:

    python -P art/gems/make_jade_art.py [--preview FILE]

Drawn at 1x in Cogpunk palette letters (art/scrap/make_scrap_art.py's PAL, plus the jade ramp RAMP["ghost"] as the digits
0-5, dark to light), exported at 2x nearest-neighbour, lit from the top-left, outlines in their ramp's darkest shade.

    JadeTile           jade nuggets set in grey stone: the standard 16x15-frame terrain sheet (art/templates/
                       terrain_exposure.json, 18 px stride), three seamless variants (D4 rule 7: no per-tile seam, the
                       nuggets at least a pixel inside, the outline only on exposed sides; tools/check_tile_seams.py). The
                       game frames it as stone (Main.tileStone), so it melts into the rock like vanilla's gems.
    Jade               the gem: a polished, faceted jade (8x8 -> 16x16)
    LargeJade          the big gem: a large faceted jade with a gilt setting (10x10 -> 20x20)
    JadeRobe           a robe of jade silk with gilt collar, placket, sash, cuffs and hem: the 1.4 body sheet (9x4 cells of
                       20x28, the template's shapes), its skirt as a legs sheet (20 frames: the skirt follows each leg
                       frame's spread, so it sways as the wearer walks) and the item icon; the hands are left bare (the
                       robe hides no hands, as ExampleMod's ExampleRobe)
    JadePhaseblade     a steel emitter hilt with a jade pommel stone and a beam of jade light, pointing top-right (20x20)
    JadePhasesaber     the same beam brighter and longer from a gilt-guarded hilt with a second stone (20x20)

Outputs (Content/Gems/):
    Tiles/JadeTile.png                                  288x270 terrain sheet
    Items/Jade.png, LargeJade.png, JadePhaseblade.png, JadePhasesaber.png, JadeRobe.png
    Items/JadeRobe_Body.png (360x224), JadeRobe_Legs.png (40x1120)
"""
import argparse
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scrap"))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "mechanist"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
import make_scrap_art  # noqa: E402
from make_scrap_art import Canvas, export  # noqa: E402
from rig import RAMP  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Gems/"
for _k, _c in enumerate(RAMP["ghost"]):                # the jade ramp as digits: 0 (outline) .. 5 (shine)
    make_scrap_art.PAL[str(_k)] = _c
for _k, _c in zip("KLMNOP", RAMP["crimson"]):          # crimson as K (outline) .. P (lightest): the staff's red (2026-11-10)
    make_scrap_art.PAL[_k] = _c
from make_oldbrasstown_art import Block  # noqa: E402  (imported after the digits exist)
import make_mechanist_art as mech  # noqa: E402  (the armor template, its torso composite and crop)

FW, FH = mech.FW, mech.FH
LAYOUT = mech.LAYOUT
JADE = ("0", "2", "3", "4", "5")                       # outline, dark, mid, light, shine (mech.shade's order)


# ================================================================================================
# The tile: jade nuggets in grey stone
# ================================================================================================
# Stone: k (iron 2) with lit flecks q and shadow flecks j spread evenly (the edges as busy as the middle, so every variant
# sits by every other); a nugget: a 0 rim, 1-2 dark facets low and right, 3-4 lit facets, a 5 glint top-left.
JADE_ORE = Block(
    variants=[
        ["kkqkkkjk",
         "kq04kkkk",
         "k04530qk",
         "kk0320kk",
         "kjk00kkk",
         "kkkk045k",
         "kqkj032k",
         "kkkkk0jk"],
        ["kjkkqkkk",
         "kkk0kkqk",
         "kq0450kk",
         "kk04530k",
         "kjk0320k",
         "kkkk00kk",
         "k45kqkjk",
         "kk3jkkkk"],
        ["kkkkjkqk",
         "kj045kkk",
         "kk032kkk",
         "kqk00kqk",
         "kkkk0kkk",
         "kjk0450k",
         "kkk0320k",
         "kqkk00kk"],
    ],
    rim_light={"k": "q", "q": "r", "j": "k", "0": "1", "2": "3", "3": "4", "4": "5"},
    rim_dark={"k": "j", "q": "k", "j": "i", "3": "2", "4": "3", "5": "4", "2": "1"},
    outline="i",
    notches=[(5, 5, 2, 2), (2, 3, 5, 5), (6, 4, 3, 1)],
)


# ================================================================================================
# Gems
# ================================================================================================
GEM = ["..0000..",
       ".045540.",
       "04555440",
       "04455430",
       "03444330",
       "02333320",
       ".022220.",
       "..0000.."]

LARGE_GEM = ["...EFFE...",
             "..D0000D..",
             ".D045540D.",
             "D04555443D",
             "E04455433E",
             "E03444332E",
             "D02333321D",
             ".D022221D.",
             "..D0000D..",
             "...DCCD..."]


# ================================================================================================
# The blades (20x20, pointing top-right: the axis is x + y = 19)
# ================================================================================================
def blade(saber):
    c = Canvas(20, 20)
    tip = 18 if saber else 17
    for x in range(20):
        for y in range(20):
            s = x + y - 19                                    # across the axis: -2 .. 2 (the upper-left side lit)
            if abs(s) > 2:
                continue
            if x <= 4:                                         # the hilt: a steel tube, a jade pommel stone
                if x == 0:
                    continue
                ch = {-2: "i", -1: "r", 0: "q", 1: "k", 2: "i"}[s]
                if x == 1 and abs(s) <= 1:
                    ch = {-1: "5", 0: "4", 1: "2"}[s]          # the pommel stone
                elif x == 3 and abs(s) <= 1:
                    ch = {-1: "q", 0: "k", 1: "j"}[s]          # a grip ring
                c.set(x, y, ch)
            elif x <= 6:                                       # the emitter, a gilt collar on the saber
                if saber:
                    ch = {-2: "B", -1: "G", 0: "F", 1: "D", 2: "B"}[s]
                else:
                    ch = {-2: "i", -1: "r", 0: "k", 1: "j", 2: "i"}[s]
                if x == 6 and abs(s) <= 1:
                    ch = {-1: "t" if saber else "r", 0: "q", 1: "k"}[s]
                c.set(x, y, ch)
            elif x <= tip:                                     # the beam of jade light
                if x >= tip - 1 and abs(s) == 2:
                    continue                                   # the rounded tip
                if x == tip and abs(s) == 1:
                    c.set(x, y, "3" if s < 0 else "2")
                    continue
                if saber:
                    ch = {-2: "2", -1: "5", 0: "t", 1: "4", 2: "2"}[s]
                else:
                    ch = {-2: "1", -1: "4", 0: "5", 1: "3", 2: "1"}[s]
                c.set(x, y, ch)
    if saber:                                                  # the crossguard across the emitter, its own stone
        for k in (-3, -2, 2, 3):
            x, y = 6 + k, 13 + k
            if 0 <= x < 20 and 0 <= y < 20:
                c.set(x, y, "F" if k < 0 else "D")
        for (x, y, ch) in ((3, 10, "B"), (9, 16, "B"), (5, 12, "4"), (7, 14, "3")):
            c.set(x, y, ch)
    return c


# ================================================================================================
# The robe
# ================================================================================================
TORSO = [                  # x 6..13, y 13..20, facing right: a gilt collar, a placket down the front, a sash
    "0EFGGFE0",
    "034443E0",
    "034433E0",
    "033432E0",
    "0DFGFFD0",
    "033332E0",
    "023322E0",
    "022221D0",
]
PAULDRON = [               # the front shoulder's sleeve top, x 3..9, y 12..16, a gilt edge
    "...000.",
    "..03450",
    ".034430",
    "0DEFFED",
    ".0CCCD.",
]
BACK_SHOULDER = ["00", "40", "30", "00"]


def torso_cell():
    c = Canvas(FW, FH)
    c.blit(Canvas.from_rows(TORSO), 6, 13)
    return c


def pauldron_cell():
    c = Canvas(FW, FH)
    c.blit(Canvas.from_rows(PAULDRON), 3, 12)
    return c


def back_shoulder_cell():
    c = Canvas(FW, FH)
    c.blit(Canvas.from_rows(BACK_SHOULDER), 14, 13)
    return c


def sleeve(mask, pivot, hand_len=2.2):
    """An arm from the template: a jade sleeve, a gilt cuff, the hand left bare (the wearer's skin shows)."""
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    c = Canvas(FW, FH)
    if not pts:
        return c
    dist = {p: math.hypot(p[0] - pivot[0], p[1] - pivot[1]) for p in pts}
    far = max(dist.values())
    cloth = {p for p in pts if dist[p] < far - hand_len}
    for (x, y) in cloth:
        d = dist[(x, y)]
        cuff = d >= far - hand_len - 1.3
        edge = any((x + dx, y + dy) not in cloth for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in cloth or (x, y - 1) not in cloth
        dark = (x + 1, y) not in cloth or (x, y + 1) not in cloth
        if cuff:
            ch = "D" if edge and dark else ("F" if lit else "E")
        elif edge and not (lit and not dark):
            ch = "0"
        elif lit:
            ch = "4"
        elif dark:
            ch = "2"
        else:
            ch = "3"
        c.set(x, y, ch)
    return c


def body_sheet():
    sheet = Canvas(FW * 9, FH * 4)
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
            cell = sleeve(mask, mech.ARM_PIVOT[side])
        sheet.blit(cell, col * FW, row * FH)
    return sheet


WAIST = 20


def skirt_frame(mask):
    """The robe's skirt for one leg frame: every row from the waist down covers the frame's legs (their span in that
    row, the waist's at least), flaring a pixel each side from the knees; jade silk lit on the left, two folds, a gilt
    placket down the front and a gilt hem."""
    rows = {}
    for y, row in enumerate(mask):
        xs = [x for x, ch in enumerate(row) if ch == "#"]
        if xs and y >= WAIST:
            rows[y] = (min(xs), max(xs))
    c = Canvas(FW, FH)
    if not rows:
        return c
    top = min(rows)
    bottom = max(rows)
    waist = rows[top]
    span = {}
    for y in range(WAIST, bottom + 1):
        x0, x1 = rows.get(y, waist)
        x0, x1 = min(x0, waist[0]), max(x1, waist[1])
        if y >= WAIST + 3:
            x0, x1 = x0 - 1, x1 + 1
        span[y] = (max(0, x0), min(FW - 1, x1))
    inside = {(x, y) for y, (x0, x1) in span.items() for x in range(x0, x1 + 1)}
    for (x, y) in inside:
        x0, x1 = span[y]
        edge = x in (x0, x1) or (x, y + 1) not in inside
        if y == bottom:
            ch = "D" if x in (x0, x1) else ("F" if x < (x0 + x1) // 2 else "E")      # the gilt hem
        elif y == WAIST:
            ch = "0" if x in (x0, x1) else ("F" if x < x1 - 2 else "E")              # the sash's lower edge
        elif edge:
            ch = "0"
        elif x == x1 - 2:
            ch = "E"                                                                  # the placket, at the front
        elif x == x0 + 1:
            ch = "4"                                                                  # the lit side
        elif x == x0 + 3 or x == x1 - 4:
            ch = "2"                                                                  # folds
        else:
            ch = "3"
        c.set(x, y, ch)
    return c


def legs_sheet():
    sheet = Canvas(FW, FH * 20)
    for f, mask in enumerate(LAYOUT["legs"]):
        sheet.blit(skirt_frame(mask), 0, f * FH)
    return sheet


def robe_icon(body):
    c = mech.body_idle(body)
    c.blit(skirt_frame(LAYOUT["legs"][0]), 0, 0)
    return mech.crop(c)


# ================================================================================================
# ================================================================================================
# The Jade Staff, its bolt and the curse's icons (2026-11-09)
# ================================================================================================
STAFF_GEM = (15.5, 4.5)                                # the jade's centre (1x, pixel edges): on the sprite's diagonal
STAFF_GEM_R = 3.2
STAFF_KNOB = (2.0, 18.0)                               # the crimson pommel knob's centre, on the diagonal too
STAFF_KNOB_R = 2.0


def staff_mirror(x, y):
    """The staff's mirror: across the sprite's diagonal from the bottom-left corner to the top-right one (vanilla holds a
    staff by that corner and turns it along the aim, so this line is the aim)."""
    return 19 - y, 19 - x


def staff():
    """20x20, pointing top-right like vanilla's gem staffs (vanilla draws staffs turned 45 degrees, held by the bottom-left
    corner; redrawn 2026-11-10, user: "the jade staff should look more like a terraria gem staffs only with a brass and
    red detail on the staff and the jade gem on the tip"; 2026-11-10b, user: "the gem on the jade staff is not centered"):
    everything is laid symmetric about the sprite's diagonal (<see staff_mirror>), the line vanilla aims along, so the jade
    sits dead on the aim. A slim brass rod (three pixels across: lit, mid, the dark outline), crimson grip wrap, crimson
    band and brass rings bulging a pixel past it each side, a crimson pommel knob at the hand's end, a brass collar under
    the head and a two-pronged brass claw (the upper prong lit, its mirror shaded) cradling a faceted jade lit from the
    top-left. 16 colours (D4 rule 5: items 16 at most)."""
    c = Canvas(20, 20)
    # Across the rod t = x + y (the axis is t = 19: the diagonal), along it s = x - y (the hand's end -12, the collar 6).
    rod = {18: "E", 19: "D", 20: "B"}
    wide = {"ring": ("D", "G", "F", "E", "B"), "red": ("L", "O", "N", "M", "K"), "turn": ("K", "M", "L", "L", "K")}

    def part(s):
        if s in (-12, -11) or s in (-4, -3) or 5 <= s <= 6:
            return "ring"                                          # brass rings and the collar
        if -10 <= s <= -5:
            return "turn" if s % 3 == 0 else "red"                 # the crimson grip wrap, a darker turn every third step
        if 2 <= s <= 3:
            return "red"                                           # the crimson band under the head
        return "rod"

    for y in range(20):
        for x in range(20):
            t, s = x + y, x - y
            if not -12 <= s <= 6:
                continue
            kind = part(s)
            if kind == "rod":
                if 18 <= t <= 20:
                    c.set(x, y, rod[t])
            elif 17 <= t <= 21:
                c.set(x, y, wide[kind][t - 17])
    kx, ky = STAFF_KNOB                                            # the pommel knob, lit from the top-left
    knob = {(x, y) for y in range(14, 20) for x in range(0, 6) if math.hypot(x + 0.5 - kx, y + 0.5 - ky) <= STAFF_KNOB_R}
    for (x, y) in knob:
        edge = any((x + dx, y + dy) not in knob for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        t = (x + 0.5 - kx) + (y + 0.5 - ky)
        c.set(x, y, ("M" if t < -1.2 else "K") if edge else ("P" if t < -0.5 else ("N" if t < 0.5 else "M")))
    # the claw: a prong up the jade's upper-left flank from the collar, its tip curled over the top; the same mirrored
    prong_body, prong_outline, prong_tip = ((11, 5), (11, 4), (11, 3)), ((10, 5), (10, 4), (10, 3), (11, 2)), (12, 2)
    for (x, y) in prong_outline:
        c.set(x, y, "B")
        c.set(*staff_mirror(x, y), "B")
    for (x, y) in prong_body:
        c.set(x, y, "F")
        c.set(*staff_mirror(x, y), "D")
    c.set(*prong_tip, "E")
    c.set(*staff_mirror(*prong_tip), "D")
    gx, gy = STAFF_GEM                                             # the jade, faceted, lit from the top-left
    gem = {(x, y) for y in range(20) for x in range(20) if math.hypot(x + 0.5 - gx, y + 0.5 - gy) <= STAFF_GEM_R}
    for (x, y) in gem:
        px, py = x + 0.5 - gx, y + 0.5 - gy
        edge = any((x + dx, y + dy) not in gem for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        t = (px + py) / (2.0 * STAFF_GEM_R)
        if edge:
            c.set(x, y, "0" if t > -0.3 else "2")
        else:
            c.set(x, y, "4" if t < -0.25 else ("3" if t < 0.2 else "2"))
    for (x, y, ch) in ((14, 2, "5"), (13, 3, "5"), (14, 3, "4")):   # the shine
        c.set(x, y, ch)
    return c


BOLT = ["...5...",
        "..454..",
        ".44544.",
        "5455545",
        ".44544.",
        "..454..",
        "...5..."]


def icon(kind):
    """16x16 buff icons: the curse (a cracked jade gem), turned to jade (a jade bust), the ward (a jade shield)."""
    c = Canvas(16, 16)
    inside = set()
    if kind == "curse":
        inside = {(x, y) for y in range(16) for x in range(16) if abs(x - 7.5) + abs(y - 7.5) <= 7}
    elif kind == "stone":
        inside = {(x, y) for y in range(16) for x in range(16) if math.hypot(x - 7.5, y - 5.0) <= 4.4
                  or (6 <= x <= 9 and 8 <= y <= 11)
                  or (y >= 10 and ((x - 7.5) / 6.6) ** 2 + ((y - 15.5) / 5.0) ** 2 <= 1.0)}
    else:
        for y in range(16):
            for x in range(16):
                half = 6.5 if y < 8 else 6.5 * (15 - y) / 7.0
                if 1 <= y <= 15 and abs(x - 7.5) <= half:
                    inside.add((x, y))
    for (x, y) in inside:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        t = ((x - 7.5) + (y - 7.5)) / 12.0
        if edge:
            ch = ("E" if (x - 7.5) + (y - 7.5) < 0 else "D") if kind == "ward" else "0"
        else:
            ch = "5" if t < -0.55 else ("4" if t < -0.1 else ("3" if t < 0.35 else "2"))
        c.set(x, y, ch)
    if kind == "curse":                                            # the crack, and a wisp of the curse out of it
        for (x, y) in ((8, 3), (7, 4), (8, 5), (7, 6), (7, 7), (8, 8), (9, 9), (8, 10), (8, 11)):
            c.set(x, y, "0")
        for (x, y) in ((10, 2), (11, 1), (12, 1)):
            c.set(x, y, "4")
    elif kind == "stone":                                          # the statue's eyes and mouth, carved
        for (x, y) in ((6, 5), (9, 5), (7, 7), (8, 7)):
            c.set(x, y, "1")
    else:                                                          # the shield's gem
        for (x, y, ch) in ((7, 6, "5"), (8, 6, "4"), (7, 7, "4"), (8, 7, "3"), (7, 8, "3"), (8, 8, "2")):
            c.set(x, y, ch)
    return c


def export_all():
    export(staff(), OUT + "Items/JadeStaff.png")
    export(Canvas.from_rows(BOLT), OUT + "Projectiles/JadeBolt.png")
    export(icon("curse"), OUT + "Buffs/JadeCurse.png")
    export(icon("stone"), OUT + "Buffs/JadePetrified.png")
    export(icon("ward"), OUT + "Buffs/JadeWard.png")
    export(JADE_ORE.sheet(), OUT + "Tiles/JadeTile.png")
    export(Canvas.from_rows(GEM), OUT + "Items/Jade.png")
    export(Canvas.from_rows(LARGE_GEM), OUT + "Items/LargeJade.png")
    export(blade(False), OUT + "Items/JadePhaseblade.png")
    export(blade(True), OUT + "Items/JadePhasesaber.png")
    body = body_sheet()
    export(body, OUT + "Items/JadeRobe_Body.png")
    export(legs_sheet(), OUT + "Items/JadeRobe_Legs.png")
    export(robe_icon(body), OUT + "Items/JadeRobe.png")


def preview(path):
    """The items, the robe's idle and walk frames over dark and light, and a jade vein in stone (3x)."""
    parts = [Canvas.from_rows(GEM), Canvas.from_rows(LARGE_GEM), blade(False), blade(True)]
    body = body_sheet()
    legs = legs_sheet()
    frames = []
    for f in (0, 5, 7, 9, 11, 13):
        c = mech.body_idle(body)
        cell = Canvas(FW, FH)
        for y in range(FH):
            for x in range(FW):
                cell.set(x, y, legs.get(x, f * FH + y))
        c.blit(cell, 0, 0)
        frames.append(c)
    W = 4 + sum(p.w + 4 for p in parts) + len(frames) * (FW + 4)
    out = Image.new("RGBA", (W, 2 * (FH + 8)), (0, 0, 0, 255))
    for row, bg in enumerate(((36, 40, 48, 255), (150, 180, 210, 255))):
        panel = Image.new("RGBA", (W, FH + 8), bg)
        x = 4
        for p in parts + frames:
            panel.alpha_composite(p.image() if hasattr(p, "image") else _img(p), (x, 4))
            x += p.w + 4
        out.paste(panel, (0, row * (FH + 8)))
    out.resize((out.width * 3, out.height * 3), Image.NEAREST).save(path)
    print("preview", path)


def _img(c):
    im = Image.new("RGBA", (c.w, c.h), (0, 0, 0, 0))
    px = im.load()
    for y in range(c.h):
        for x in range(c.w):
            ch = c.get(x, y)
            if ch != ".":
                px[x, y] = make_scrap_art.PAL[ch] + (255,)
    return im


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
