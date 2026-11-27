"""Source for the 0.3.0 early-game progression sprites (D4), 2026-11-27. Run from the repo root:

    python -P art/scrap/make_early_progression_art.py

Outputs (all 2x nearest-neighbour, strictly on art/palettes/cogpunk.gpl, <= 16 colours per item):
    Content/Mechanist/Weapons/Sparkler.png                          42x22
    Content/Scrap/Weapons/Flintsword.png                            52x52
    Content/Scrap/Weapons/FlintswordTrail.png                       96x718 (8 crescent frames of 96x88, 2 px gap)
    Content/Scrap/Weapons/HandMadeGun.png                           36x22
    Content/Scrap/Weapons/HandMadeBullet.png                        12x222 (16 headings of 12x12, 2 px gap)
    Content/Scrap/Armor/SpareHelmet.png + _Head[,_1..3].png         item + 40x1120 equip sheets
    Content/Scrap/Armor/SpareVest.png + _Body[,_1..3].png           item + 360x224 equip sheets
    Content/Scrap/Armor/SpareBoots.png + _Legs[,_1..3].png          item + 40x1120 equip sheets
    Content/Research/Items/OreGps.png                               28x28
    Content/Research/Items/DrillerExtractor.png                     44x22
    Content/Research/Items/DrillerExtractorProjectile.png + _Glow   862x160 (16 headings x 3 spins of 52x52, 2 px gap)
"""
import json
import math
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.getcwd()
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from sculpt import Frame, Ell, Tube, Part, render  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export as export_img, vertical  # noqa: E402

LAYOUT = json.load(open(os.path.join(ROOT, "art/templates/armor_layout.json"), encoding="utf-8"))

# Palette ramps (every RGB tuple is in art/palettes/cogpunk.gpl)
BRASS = [(43, 26, 14), (90, 58, 23), (138, 93, 34), (184, 138, 51), (223, 185, 78), (246, 231, 161)]
COPPER = [(42, 18, 12), (94, 40, 23), (147, 68, 31), (196, 104, 58), (233, 160, 107)]
IRON = [(21, 22, 28), (46, 50, 59), (79, 85, 98), (127, 135, 148), (183, 191, 202)]
OAK = [(40, 21, 14), (76, 40, 22), (110, 60, 30), (146, 86, 42), (180, 116, 60), (212, 154, 90)]
LEATHER = [(47, 27, 20), (91, 54, 38), (138, 90, 60)]
EMBER = [(77, 20, 10), (163, 48, 26), (236, 113, 40), (255, 199, 90)]
GHOST = [(10, 34, 32), (18, 70, 58), (30, 114, 88), (58, 166, 118), (118, 220, 162), (196, 250, 214)]
GILT = RAMP["gilt"]
STEEL = RAMP["steel"]


def to_rgba(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = im.load()
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h and c is not None:
            p[x, y] = tuple(c) + (255,)
    return im


# ============================================================================================
# 1. Sparkler (21x11 1x -> 42x22 2x, points right): oak stock, brass cog chamber, flared copper bell
# ============================================================================================
def make_sparkler():
    w, h = 21, 11
    px = {}
    # Oak grip & stock (x 1..6, y 4..9)
    stock = [(1, 7), (1, 8), (2, 6), (2, 7), (2, 8), (2, 9), (3, 5), (3, 6), (3, 7), (3, 8),
             (4, 4), (4, 5), (4, 6), (4, 7), (5, 4), (5, 5), (5, 6), (6, 4), (6, 5), (6, 6)]
    stock_s = set(stock)
    for (x, y) in stock:
        out = any((x + dx, y + dy) not in stock_s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        px[(x, y)] = COPPER[0] if out else (COPPER[3] if y <= 5 else COPPER[1])
    # Iron trigger guard
    for (x, y) in ((5, 7), (6, 7), (7, 7), (7, 6)):
        px[(x, y)] = IRON[1]
    # Brass steam chamber + cog wheel (x 6..12, y 2..6)
    for y in range(2, 7):
        for x in range(6, 13):
            if (x in (6, 12) and y in (2, 6)):
                continue
            out = y in (2, 6) or x in (6, 12)
            px[(x, y)] = BRASS[1] if out else (BRASS[4] if y == 3 else BRASS[3])
    # Stamped cog teeth & axle on side of chamber (cx=9, cy=4)
    for (x, y, c) in ((9, 1, BRASS[2]), (8, 4, BRASS[4]), (10, 4, BRASS[2]), (9, 4, IRON[0]), (8, 3, BRASS[5])):
        px[(x, y)] = c
    # Copper barrel & blunderbuss flare (x 12..19, y 1..7)
    for x in range(12, 20):
        half = 1 if x < 16 else (2 if x < 18 else 3)
        cy = 4
        for y in range(cy - half, cy + half + 1):
            out = y in (cy - half, cy + half) or x == 19
            if x == 19 and abs(y - cy) <= 1:
                px[(x, y)] = EMBER[3] if y == cy else EMBER[2]      # glowing spark in the bore
            elif out:
                px[(x, y)] = COPPER[1] if y < cy else COPPER[0]
            elif y < cy:
                px[(x, y)] = COPPER[4] if x in (14, 17) else COPPER[3]
            elif y > cy:
                px[(x, y)] = COPPER[1]
            else:
                px[(x, y)] = COPPER[2]
    # Iron barrel band at x=15
    for y in range(3, 6):
        px[(15, y)] = IRON[0] if y == 5 else (IRON[3] if y == 3 else IRON[2])
    export_img(to_rgba(px, w, h), "Content/Mechanist/Weapons/Sparkler.png")


# ============================================================================================
# 2. Flintsword (26x26 1x -> 52x52 2x, points top-right) + FlintswordTrail.png
# ============================================================================================
def make_flintsword():
    size = 26
    axis = 25
    px = {}
    for y in range(size):
        for x in range(size):
            t, s = x + y, x - y
            a = t - axis
            # Pommel: s -24..-21, |a| <= 2
            if -24 <= s <= -21 and abs(a) <= 2 and not (s == -24 and abs(a) == 2):
                out = s in (-24, -21) or abs(a) == 2
                px[(x, y)] = IRON[0] if out else (IRON[3] if a < 0 else IRON[2])
            # Leather grip: s -20..-13, |a| <= 1
            elif -20 <= s <= -13 and abs(a) <= 1:
                px[(x, y)] = LEATHER[0] if abs(a) == 1 else (LEATHER[2] if (s % 2 == 0 and a <= 0) else LEATHER[1])
            # Crossguard: s -12..-10, |a| <= 5
            elif -12 <= s <= -10 and abs(a) <= 5:
                out = s in (-12, -10) or abs(a) == 5
                px[(x, y)] = BRASS[0] if out and a > 0 else (BRASS[1] if out else (BRASS[4] if a < 0 else BRASS[3]))
            # Broad iron/platinum-tier blade with flint spine: s -9..23
            elif -9 <= s <= 23:
                tip_cut = 23 - abs(a)
                if abs(a) <= 3 and s <= tip_cut:
                    if a == -3:
                        # Lit upper-left flint striker edge
                        px[(x, y)] = IRON[1] if s % 4 == 0 else IRON[2]
                    elif a == 3 or s == tip_cut:
                        px[(x, y)] = IRON[0]
                    elif a == -2:
                        px[(x, y)] = IRON[4]
                    elif a == -1:
                        px[(x, y)] = IRON[3]
                    elif a == 0:
                        px[(x, y)] = IRON[1] if -6 <= s <= 15 else IRON[2]  # central fuller groove
                    elif a == 1:
                        px[(x, y)] = IRON[3]
                    else:
                        px[(x, y)] = IRON[2]
    # Stamped brass striker cog & ember flint spark at the guard (around x=6..10, y=15..19)
    cog = [
        ".BB.",
        "BFEB",
        "BEDB",
        ".BB.",
    ]
    cmap = {"B": BRASS[1], "D": BRASS[2], "E": BRASS[4], "F": BRASS[5]}
    for dy, row in enumerate(cog):
        for dx, ch in enumerate(row):
            if ch in cmap:
                px[(5 + dx, 14 + dy)] = cmap[ch]
    # Flint stone + warm spark glint on the upper guard
    px[(9, 14)] = IRON[1]
    px[(10, 13)] = EMBER[2]
    px[(9, 13)] = EMBER[3]
    export_img(to_rgba(px, size, size), "Content/Scrap/Weapons/Flintsword.png")

    # Phantom slash crescents: 48x44 1x -> 96x88 2x, pivot (6, 42) 1x -> (12, 84) 2x
    tw, th, px0, py0 = 48, 44, 6, 42
    t_in, t_out = 13.0, 36.5
    phantom = [EMBER[0], EMBER[1], EMBER[2], EMBER[3], BRASS[5]]
    frames = []
    for k in range(8):
        span = math.radians((k + 1) * 12)
        im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        p = im.load()
        for y in range(th):
            for x in range(tw):
                dx, dy = x + 0.5 - px0, y + 0.5 - py0
                r = math.hypot(dx, dy)
                ang = math.atan2(-dy, dx)
                if ang < -0.02 or ang > span or r > t_out:
                    continue
                u = max(0.0, ang) / span
                inner = t_in + (t_out - t_in) * 0.78 * (u ** 0.9)
                if r < inner:
                    continue
                depth = (r - t_in) / max(1.0, t_out - t_in)
                level = ((1.0 - u) ** 1.1) * (0.15 + 0.85 * (depth ** 1.5))
                if r > t_out - 1.2 and u < 0.55:
                    level = max(level, 1.0 - u * 0.9)
                if ang * r < 1.2 and u < 0.2:
                    level = max(level, 0.8 * depth + 0.2)
                idx = int(level * len(phantom) + 0.15)
                if idx > 0:
                    p[x, y] = phantom[min(len(phantom), idx) - 1] + (255,)
        frames.append(im)
    export_img(vertical(frames), "Content/Scrap/Weapons/FlintswordTrail.png")


# ============================================================================================
# 3. Hand-made Gun (18x11 1x -> 36x22 2x) + HandMadeBullet (16 headings of 6x6 1x -> 12x12 2x)
# ============================================================================================
def make_hand_made_gun():
    w, h = 18, 11
    px = {}
    # Crude wooden grip bound with leather (x 1..5, y 4..9)
    grip = [(1, 8), (1, 9), (2, 6), (2, 7), (2, 8), (2, 9), (3, 5), (3, 6), (3, 7), (3, 8),
            (4, 4), (4, 5), (4, 6), (4, 7), (5, 4), (5, 5), (5, 6)]
    gs = set(grip)
    for (x, y) in grip:
        out = any((x + dx, y + dy) not in gs for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        px[(x, y)] = OAK[0] if out else (LEATHER[1] if y == 7 else (OAK[4] if x <= 3 else OAK[2]))
    # Trigger
    px[(5, 7)] = IRON[1]
    px[(6, 7)] = IRON[1]
    # Rusted cog wheel hammer mechanism (x 4..8, y 1..5)
    for (x, y, c) in ((5, 1, BRASS[1]), (6, 1, BRASS[2]), (4, 2, BRASS[1]), (5, 2, BRASS[5]), (6, 2, BRASS[4]), (7, 2, BRASS[1]),
                      (4, 3, BRASS[1]), (5, 3, BRASS[3]), (6, 3, IRON[0]), (7, 3, BRASS[2]), (5, 4, BRASS[2]), (6, 4, BRASS[1])):
        px[(x, y)] = c
    # Copper pipe barrel strapped with iron clamps (x 6..16, y 2..5)
    for x in range(6, 17):
        clamp = x in (9, 13)
        ramp = IRON if clamp else COPPER
        px[(x, 2)] = ramp[1] if x < 15 else ramp[0]
        px[(x, 3)] = ramp[4]
        px[(x, 4)] = ramp[2]
        px[(x, 5)] = ramp[0]
    # Front iron sight & muzzle opening
    px[(15, 1)] = IRON[2]
    px[(16, 3)] = IRON[0]
    px[(16, 4)] = IRON[0]
    # Under-barrel support rod
    for x in range(7, 15):
        px[(x, 6)] = IRON[1] if x % 2 == 0 else IRON[0]
    export_img(to_rgba(px, w, h), "Content/Scrap/Weapons/HandMadeGun.png")

    # HandMadeBullet: 16 headings of 6x6 (1x) -> 12x12 (2x) on 14 px stride
    bframes = []
    for k in range(16):
        ang = k * 2.0 * math.pi / 16.0
        dx, dy = math.cos(ang), math.sin(ang)
        pxb = {}
        body = set()
        for y in range(6):
            for x in range(6):
                rx, ry = x - 2.5, y - 2.5
                along = rx * dx + ry * dy
                across = abs(-rx * dy + ry * dx)
                if -2.1 <= along <= 2.2 and across <= (1.25 if along < 1.0 else 0.85):
                    body.add((x, y))
        for (x, y) in body:
            out = any((x + ox, y + oy) not in body for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            rx, ry = x - 2.5, y - 2.5
            along = rx * dx + ry * dy
            lit = (x + y) <= 4
            if out:
                pxb[(x, y)] = COPPER[0] if not lit else COPPER[1]
            elif along > 0.4:
                pxb[(x, y)] = BRASS[5] if lit else BRASS[4]
            else:
                pxb[(x, y)] = COPPER[4] if lit else COPPER[3]
        bframes.append(to_rgba(pxb, 6, 6))
    export_img(vertical(bframes), "Content/Scrap/Weapons/HandMadeBullet.png")


# ============================================================================================
# 4. Spare Armor (Wood armor + spinning brass cogs: Helmet, Vest, Boots)
# ============================================================================================
FW, FH = 20, 28
COG_FRAMES = 4
COG6_RING = [(1, 0), (2, 0), (3, 0), (4, 0), (5, 1), (5, 2), (5, 3), (5, 4),
             (4, 5), (3, 5), (2, 5), (1, 5), (0, 4), (0, 3), (0, 2), (0, 1)]
COG4_RING = [(1, 0), (2, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 2), (0, 1)]


def cog6_px(anim, direction=1):
    px = {}
    for i, (x, y) in enumerate(COG6_RING):
        if (i - direction * anim) % 4 < 2:
            px[(x, y)] = BRASS[3] if x + y <= 4 else BRASS[1]
    body = {
        (1, 1): BRASS[3], (2, 1): BRASS[4], (3, 1): BRASS[3], (4, 1): BRASS[2],
        (1, 2): BRASS[4], (2, 2): BRASS[3], (3, 2): BRASS[0], (4, 2): BRASS[1],
        (1, 3): BRASS[3], (2, 3): BRASS[0], (3, 3): BRASS[2], (4, 3): BRASS[1],
        (1, 4): BRASS[2], (2, 4): BRASS[1], (3, 4): BRASS[1], (4, 4): BRASS[0],
    }
    px.update(body)
    return px


def cog4_px(anim, direction=1):
    px = {}
    for i, (x, y) in enumerate(COG4_RING):
        if (i - direction * anim) % 4 == 0:
            px[(x, y)] = BRASS[3] if x + y <= 2 else BRASS[1]
    px.update({(1, 1): BRASS[4], (2, 1): BRASS[2], (1, 2): BRASS[2], (2, 2): BRASS[0]})
    return px


def spare_helmet_frame(anim):
    px = {}
    # Wooden cap with plank seams & leather brow strap
    dome = [(x, y) for y, (x0, x1) in {3: (8, 13), 4: (7, 14), 5: (6, 15), 6: (5, 15), 7: (5, 16)}.items() for x in range(x0, x1 + 1)]
    neck = [(x, y) for y, (x0, x1) in {8: (5, 11), 9: (5, 10), 10: (6, 9)}.items() for x in range(x0, x1 + 1)]
    pts = set(dome + neck)
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in pts for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in pts or (x, y - 1) not in pts
        if edge:
            px[(x, y)] = OAK[1] if (lit and y <= 5) else OAK[0]
        elif x == 10:                                             # plank seam
            px[(x, y)] = OAK[1]
        elif y <= 4 or x <= 7:
            px[(x, y)] = OAK[4]
        elif y >= 7:
            px[(x, y)] = OAK[2]
        else:
            px[(x, y)] = OAK[3]
    px[(8, 4)] = OAK[5]
    px[(9, 4)] = OAK[5]
    # Leather strap across brow + iron rivets
    for x in range(9, 16):
        px[(x, 7)] = IRON[3] if x in (11, 14) else (LEATHER[2] if x < 13 else LEATHER[1])
    # Spinning 6x6 brass cog over the ear (x=4, y=6)
    for (cx, cy), c in cog6_px(anim, 1).items():
        px[(4 + cx, 6 + cy)] = c
    return px


def spare_body_sheet(anim):
    sheet = Image.new("RGBA", (FW * 9, FH * 4), (0, 0, 0, 0))
    cells = LAYOUT["body_cells"]
    # Wooden slat vest with copper mana/steam capsule & chest cog
    torso_px = {}
    for y in range(13, 21):
        for x in range(6, 14):
            out = x in (6, 13) or y in (13, 20)
            if y == 19:
                torso_px[(x, y)] = LEATHER[0] if x in (6, 13) else (BRASS[4] if x == 11 else LEATHER[1])
            elif out:
                torso_px[(x, y)] = OAK[0]
            elif x == 9:
                torso_px[(x, y)] = OAK[1]                         # vertical wood slat seam
            elif x <= 8:
                torso_px[(x, y)] = OAK[4] if y <= 16 else OAK[3]
            else:
                torso_px[(x, y)] = OAK[3] if y <= 15 else OAK[2]
    # Small copper steam/mana vial strapped on left rib (x=6..7, y=15..18)
    for (x, y, c) in ((6, 15, COPPER[1]), (7, 15, COPPER[4]), (6, 16, GHOST[3]), (7, 16, GHOST[4]),
                      (6, 17, COPPER[1]), (7, 17, COPPER[3])):
        torso_px[(x, y)] = c
    for (cx, cy), c in cog6_px(anim, -1).items():
        torso_px[(8 + cx, 13 + cy)] = c
    torso_im = to_rgba(torso_px, FW, FH)

    # Wooden pauldron with brass rivet
    pauldron_px = {}
    p_rows = {12: (5, 8), 13: (4, 9), 14: (3, 9), 15: (3, 8)}
    p_set = {(x, y) for y, (x0, x1) in p_rows.items() for x in range(x0, x1 + 1)}
    for (x, y) in p_set:
        edge = any((x + dx, y + dy) not in p_set for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        pauldron_px[(x, y)] = OAK[0] if edge else (OAK[4] if y <= 13 else OAK[2])
    pauldron_px[(6, 14)] = BRASS[4]
    pauldron_im = to_rgba(pauldron_px, FW, FH)

    back_sh = to_rgba({(14, 13): OAK[0], (15, 13): OAK[0], (14, 14): OAK[2], (15, 14): OAK[0],
                       (14, 15): OAK[1], (15, 15): OAK[0]}, FW, FH)

    def limb_im(mask, pivot):
        pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
        if not pts:
            return Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        inside = set(pts)
        dist = {p: math.hypot(p[0] - pivot[0], p[1] - pivot[1]) for p in pts}
        far = max(dist.values())
        lpx = {}
        for (x, y) in pts:
            d = dist[(x, y)]
            cuff = abs(d - far * 0.55) < 0.7
            hand = d >= far - 2.3
            edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            lit = (x - 1, y) not in inside or (x, y - 1) not in inside
            if hand:
                lpx[(x, y)] = LEATHER[0] if edge else (LEATHER[2] if lit else LEATHER[1])
            elif cuff:
                lpx[(x, y)] = BRASS[0] if edge else (BRASS[4] if lit else BRASS[2])
            else:
                lpx[(x, y)] = OAK[0] if edge else (OAK[4] if lit else OAK[2])
        return to_rgba(lpx, FW, FH)

    for key, mask in cells.items():
        col, row = (int(v) for v in key.split(","))
        if col in (0, 1):
            if row in (0, 2):
                cell = torso_im
            elif col == 0:
                cell = pauldron_im
            else:
                cell = back_sh
        else:
            pivot = (6.0, 13.5) if (col == 7 or (col <= 6 and row in (0, 1))) else (14.0, 13.5)
            cell = limb_im(mask, pivot)
        sheet.alpha_composite(cell, (col * FW, row * FH))
    return sheet


def spare_legs_frame(mask, anim):
    pts = [(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"]
    if not pts:
        return Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    inside = set(pts)
    top = min(y for _, y in pts)
    bottom = max(y for _, y in pts)
    px = {}
    for (x, y) in pts:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        if y == top:
            px[(x, y)] = LEATHER[0] if edge else LEATHER[2]
        elif y >= bottom - 1:
            px[(x, y)] = LEATHER[0] if edge else (LEATHER[2] if lit else LEATHER[1])
        else:
            px[(x, y)] = OAK[0] if edge else (OAK[4] if lit else OAK[2])
    belt = sorted(x for x, y in pts if y == top)
    if len(belt) >= 2:
        px[(belt[-1] - 1, top)] = BRASS[4]
    ox, oy = belt[0] + 1, top
    for (cx, cy), c in cog4_px(anim, 1).items():
        if (ox + cx, oy + cy) in inside:
            px[(ox + cx, oy + cy)] = c
    return to_rgba(px, FW, FH)


def crop_rgba(im):
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def make_spare_armor():
    out = "Content/Scrap/Armor"
    for anim in range(COG_FRAMES):
        suf = "" if anim == 0 else f"_{anim}"
        head_sheet = Image.new("RGBA", (FW, FH * 20), (0, 0, 0, 0))
        hframe = to_rgba(spare_helmet_frame(anim), FW, FH)
        for f, dy in enumerate(LAYOUT["head_bob"]):
            head_sheet.alpha_composite(hframe, (0, f * FH + dy))
        export_img(head_sheet, f"{out}/SpareHelmet_Head{suf}.png")

        body_sheet = spare_body_sheet(anim)
        export_img(body_sheet, f"{out}/SpareVest_Body{suf}.png")

        legs_sheet = Image.new("RGBA", (FW, FH * 20), (0, 0, 0, 0))
        for f, mask in enumerate(LAYOUT["legs"]):
            legs_sheet.alpha_composite(spare_legs_frame(mask, anim), (0, f * FH))
        export_img(legs_sheet, f"{out}/SpareBoots_Legs{suf}.png")

        if anim == 0:
            export_img(crop_rgba(hframe), f"{out}/SpareHelmet.png")
            # Composite idle body icon
            idle = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
            for col, row in ((2, 2), (0, 0), (2, 0), (0, 1), (1, 1)):
                cell = body_sheet.crop((col * FW, row * FH, (col + 1) * FW, (row + 1) * FH))
                idle.alpha_composite(cell, (0, 0))
            export_img(crop_rgba(idle), f"{out}/SpareVest.png")
            export_img(crop_rgba(spare_legs_frame(LAYOUT["legs"][5], 0)), f"{out}/SpareBoots.png")


# ============================================================================================
# 5. Ore GPS (14x14 1x -> 28x28 2x): pocket brass radar compass with glowing green screen & blip
# ============================================================================================
def make_ore_gps():
    w, h = 14, 14
    px = {}
    # Antenna nub at top-left (x=4..5, y=0..2)
    for (x, y, c) in ((4, 0, COPPER[3]), (5, 0, COPPER[1]), (4, 1, IRON[3]), (5, 1, IRON[1]), (4, 2, IRON[2]), (5, 2, IRON[1])):
        px[(x, y)] = c
    # Side cog dial on right (x=12..13, y=6..9)
    for (x, y, c) in ((12, 6, BRASS[3]), (13, 6, BRASS[0]), (12, 7, BRASS[4]), (13, 7, BRASS[2]),
                      (12, 8, BRASS[2]), (13, 8, BRASS[0]), (12, 9, BRASS[1])):
        px[(x, y)] = c
    # Round brass body (centre 6.0, 7.5, radius 5.3)
    for y in range(2, 14):
        for x in range(1, 12):
            r = math.hypot(x - 6.0, y - 7.5)
            if r > 5.4:
                continue
            lit = (x - 6.0) + (y - 7.5) < -0.5
            if r > 4.3:
                px[(x, y)] = BRASS[1] if (r > 4.9 and not lit) else (BRASS[2] if r > 4.9 else (BRASS[5] if lit else BRASS[3]))
            elif r > 3.5:
                px[(x, y)] = BRASS[0]                             # inner bezel
            else:
                # Radar screen
                grid = (x == 6 or y == 8)
                px[(x, y)] = GHOST[2] if grid else GHOST[0]
    # Radar sweep line + bright ore blip at top-right of screen
    px[(6, 7)] = GHOST[3]
    px[(7, 6)] = GHOST[4]
    px[(8, 5)] = GHOST[5]
    px[(8, 6)] = GHOST[4]
    px[(4, 9)] = GHOST[2]
    export_img(to_rgba(px, w, h), "Content/Research/Items/OreGps.png")


# ============================================================================================
# 6. Driller Extractor (item 22x11 1x -> 44x22 2x; projectile 16 headings x 3 spins of 26x26 1x -> 52x52 2x)
# ============================================================================================
def driller_extractor_cell(angle, mirror, spin, w, h, ox, oy):
    s = -1.0 if mirror else 1.0
    f = Frame(0.0, 0.0, angle)

    def P(x, y):
        return (x, y * s)

    parts = [
        # Rear D-grip
        Part("grip", Tube([P(-9.5, -2.2), P(-9.5, 2.2)], [1.1, 1.1]), STEEL, 0, f, lo=1, hi=5),
        Part("strut", Tube([P(-9.2, 0.0), P(-6.0, 0.0)], [1.4, 1.6]), STEEL, 1, f, lo=2, hi=6),
        # Brass housing + top sifter hopper chute
        Part("hopper", Tube([P(-3.2, -3.2), P(-4.2, -5.8)], [1.8, 2.4]), GILT, 2, f, lo=2, hi=8),
        Part("body", Ell(-2.0, 0.0, 5.2, 3.6, 0.3), GILT, 3, f, lo=2, hi=8,
             lines=[[P(-4.0, -3.0), P(-4.0, 3.0)], [P(0.5, -3.0), P(0.5, 3.0)]]),
        Part("collar", Ell(3.2, 0.0, 1.5, 3.5, 0.25), STEEL, 4, f, lo=2, hi=7),
    ]
    grooves = []
    for k in range(3):
        gx = 4.2 + ((k * 2.4 + spin * 0.8) % 7.2)
        r = 3.2 * max(0.15, 1.0 - (gx - 3.8) / 7.8)
        grooves.append([P(gx, -r), P(gx + 1.1, r * 0.2), P(gx + 0.5, r)])
    parts.append(Part("cone", Tube([(3.8, 0.0), (11.4, 0.0)], [3.3, 0.45]), STEEL, 5, f, lo=2, hi=8, lines=grooves))

    px, glow, owner = render(parts, w, h, ox, oy)
    # Glowing green/amber extractor indicator lamp on housing
    lx, ly = f.to_world(-1.5, -1.0 * s)
    q = (int(math.floor(lx + ox)), int(math.floor(ly + oy)))
    for (dx, dy, c) in ((0, 0, GHOST[5]), (1, 0, GHOST[3])):
        pt = (q[0] + dx, q[1] + dy)
        if pt in px:
            px[pt] = c
            glow[pt] = c
    return px, glow


def make_driller_extractor():
    # Item icon: facing right (angle 0), 22x11 1x -> 44x22 2x (clamped to <= 16 colours for item cap)
    px, _ = driller_extractor_cell(0.0, False, 0, 22, 11, 10.5, 6.2)
    remap = {GILT[8]: GILT[7], STEEL[8]: STEEL[7]}
    px = {k: remap.get(v, v) for k, v in px.items()}
    export_img(to_rgba(px, 22, 11), "Content/Research/Items/DrillerExtractor.png")

    # Projectile sheet: 16 headings (columns) x 3 spins (rows), cell 26x26 (1x) -> 52x52 (2x), stride 27 (1x) -> 54 (2x)
    headings, spins, cell, stride = 16, 3, 26, 27
    sheet_w = headings * stride - 1
    sheet_h = spins * stride - 1
    main = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    glow = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for sp in range(spins):
        for hd in range(headings):
            angle = hd * 2.0 * math.pi / headings
            mirror = math.cos(angle) < -1e-6 or (abs(math.cos(angle)) <= 1e-6 and math.sin(angle) < 0)
            cpx, cglow = driller_extractor_cell(angle, mirror, sp, cell, cell, cell / 2.0, cell / 2.0)
            main.alpha_composite(to_rgba(cpx, cell, cell), (hd * stride, sp * stride))
            glow.alpha_composite(to_rgba(cglow, cell, cell), (hd * stride, sp * stride))
    export_img(main, "Content/Research/Items/DrillerExtractorProjectile.png")
    export_img(glow, "Content/Research/Items/DrillerExtractorProjectile_Glow.png")


if __name__ == "__main__":
    make_sparkler()
    make_flintsword()
    make_hand_made_gun()
    make_spare_armor()
    make_ore_gps()
    make_driller_extractor()
    print("Generated all 0.3.0 early-progression sprites.")
