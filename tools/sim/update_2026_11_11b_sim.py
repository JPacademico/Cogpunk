"""D5 proofs for the second request of 2026-11-11, built from the real sprites and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_11b_sim.py --out docs/media [--only ruins,gate,cutter,barrel,dragonete,beetle,friendobot,items]

Writes:
    2026-11-11_secrets-fundamental-ruins.png   FundamentalRuinsPass (the metroidvania redesign) replayed on a cavern with a
                                               spider nest: the map (FundamentalRuinsLayout's rows, read from the C# file)
                                               carved, its brick shells, the arena under the gate hall with the sealed gate
                                               in its crown, the three rune glyphs on the dead ends, the treasury's chest, the
                                               rubble to mine and the spike pits marked; then the gate hall and arena, and
                                               the three glyphs' wings, closer.
    2026-11-11_secrets-ruins-glyphs-gate.gif   the three rune glyphs lit one after another (each blazes, "n/3"), the gate's
                                               sockets lighting with them; the third opens the gate: the slab goes, the
                                               announcement, and a player standing on it drops into the arena down the
                                               platforms under it.
    2026-11-11_mechanist-diamond-cutter.gif    the Diamond Cutter at four dummies in a row: the instant beam stops in the
                                               third (the three nearest struck, 19 each, a crit 38); then a shot into a wall
                                               (the beam ends on the first solid block).
    2026-11-11_mechanist-barrel-gun.gif        the Barrel Gun dry: fish in an arc, 20 a hit, one stunning a dummy (the stars);
                                               then in the rain: 30 a hit, the fish flying straight and homing in on a
                                               moving dummy.
    2026-11-11_underworld-dragonete-miudo.gif  the Dragonete Miudo hovering off to the side, inhaling (the telegraph) and
                                               spitting a fire bolt; the player jumps it, the bolt burns out: a miss; it
                                               screeches, rears and swoops in with its jaws open, bites, and flies back up.
    2026-11-11_jungle-rhino-beetle.gif         the Rhino Beetle in the Hardmode jungle: a plain touch shoves the player (x1.5
                                               knockback); a ram throws the player far and high (x2 and the toss).
    2026-11-11_town-friendo-bot.gif            the Friendo-bot (and his shimmered form) walking both ways with vanilla's
                                               frame rule, then standing, blinking, talking, the two chat gestures, sitting
                                               and the throw; his face emote.
    2026-11-11_items-cutter-barrel-dragonete-glyphs.png  the sprites: both guns and their projectiles, the stun, every
                                               Dragonete frame and its gores and bolt, the glyphs and the gate dark and lit,
                                               the jungle Rhino Beetle, the Friendo-bot's sheets, head and emote.

Leaves out: lighting (the glows are drawn at full strength), vanilla's own art (natural stone, the stone platforms, the
spikes, the Water Chest, the dummies, the water, the rain, the Ale mug, the chair and the jungle and Underworld blocks are
stand-ins), the planes' parallax, the player's exact physics (approximated as in update_2026_11_03b_sim), defense (the
numbers are the hits' own), netcode (the sim is the server and the owner). Numbers are Expert's.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, consts, load, player_sprite, TPF  # noqa: E402
from update_2026_11_04_sim import STEAM  # noqa: E402
from update_2026_11_06b_sim import Planes, numbers, note  # noqa: E402
from update_2026_11_03b_sim import PLAYER_W, PLAYER_H, GRAVITY, JUMP_SPEED, JUMP_HOLD, IMMUNITY, overlaps  # noqa: E402
from update_2026_11_10_sim import faded, stone_image  # noqa: E402
from update_2026_11_10b_sim import additive, font_at  # noqa: E402
import update_2026_11_11_sim as prev  # noqa: E402
from update_2026_11_11_sim import (World, Ruins, render, sheets, STONE_T, BRICK_T, CORAL_T, RUNE_T, ABRICK_T, ARUNE_T,  # noqa: E402
                                   RUBBLE_T, PLAT_T, KELP_T, OBJ_T, CHEST_T, WEB_T, NEST_W, BRICK_W, COLUMN_W, Runner, Beetle,
                                   flat_backdrop, dummy, patch)

ROOT = os.path.dirname(os.path.dirname(HERE))
SEC = "Content/Secrets/"
RUIN = SEC + "Ruins/"
MECH = "Content/Mechanist/"
KR = consts(SEC + "Generation/FundamentalRuinsPass.cs")
KL = consts(SEC + "Generation/FundamentalRuinsLayout.cs")
KG = consts(RUIN + "Tiles/FundamentalGlyphTile.cs")
KSE = consts(RUIN + "Tiles/FundamentalSealTile.cs")
KS = consts(SEC + "FundamentalStoneTile.cs")
KC = consts(MECH + "Weapons/DiamondCutter.cs")
KCB = consts(MECH + "Weapons/DiamondCutterBeam.cs")
KBG = consts(MECH + "Weapons/BarrelGun.cs")
KF = consts(MECH + "Weapons/BarrelGunFish.cs")
KST = consts(MECH + "Buffs/Stunned.cs")
KD = consts("Content/Underworld/NPCs/DragoneteMiudo.cs", "Content/Underworld/NPCs/DragoneteMiudoRigData.cs")
KDB = consts("Content/Underworld/Projectiles/DragoneteFireBolt.cs")
KB = consts("Content/Jungle/NPCs/RhinoBeetle.cs", "Content/Jungle/NPCs/RhinoBeetleRigData.cs")
EMBER, HIT, HURT, GLOW, CRIT = (236, 113, 40), (255, 199, 90), (255, 90, 70), (198, 189, 255), (255, 150, 60)
ROUTE, PLUG, ARENA, GLYPH, CHEST = (255, 214, 90), (236, 90, 70), (110, 220, 255), (198, 189, 255), (255, 214, 90)
SPIKE_T, GLYPH_T, SEAL_T = "spike", "glyph", "seal"
CELL = int(KL["Cell"])
LW, LH = int(KL["Width"]), int(KL["Height"])
AW, AH = LW * CELL, LH * CELL
CORAL_SHARE = 0.35                                               # FundamentalRuinsPass.CoralShare (a double)


def layout_rows():
    """FundamentalRuinsLayout.Rows, read from the C# file (the map the pass carves)."""
    text = open(os.path.join(ROOT, SEC + "Generation/FundamentalRuinsLayout.cs"), encoding="utf-8").read()
    rows = re.findall(r'^\s*"([^"]+)",\s*$', text, re.M)
    assert len(rows) == LH and all(len(r) == LW for r in rows), (len(rows), set(len(r) for r in rows))
    return rows


ROWS = layout_rows()


# ================================================================================================
# The Fundamental Ruins: FundamentalRuinsPass (2026-11-11b) replayed
# ================================================================================================
class Ruins2(Ruins):
    """FundamentalRuinsPass's build (2026-11-11b), step for step, on a World (its rng stands in for WorldGen.genRand)."""

    def __init__(self, world, seed, flip=False):
        self.wd, self.rng, self.flip = world, random.Random(seed), flip
        xs = [x for (x, _) in world.nest]
        ys = [y for (_, y) in world.nest]
        ncx, ncy = (min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2
        self.area = (ncx - AW // 2, ncy - AH // 2, AW, AH)
        self.carved = set()
        self.glyphs, self.chest_at, self.stone_at, self.seal_at, self.spikes, self.rubble = [], None, None, None, [], []
        self.marks = {}

    def at(self, col, row):
        if not (0 <= row < LH and 0 <= col < LW):
            return "#"
        return ROWS[row][LW - 1 - col if self.flip else col]

    def build(self):
        ax, ay, aw, ah = self.area
        for p in list(self.wd.nest):                              # ClearNest
            if self.wd.wall.get(p) == NEST_W:
                self.wd.wall[p] = None
            if self.wd.tile.get(p) == WEB_T:
                self.wd.tile.pop(p, None)
        for x in range(ax, ax + aw):                              # ClearFootprint + FillFootprint
            for y in range(ay, ay + ah):
                self.wd.water.discard((x, y))
                if self.wd.wall.get((x, y)) == NEST_W:
                    self.wd.wall[(x, y)] = None
                if self.wd.tile.get((x, y)) == WEB_T or self.is_air(x, y):
                    self.wd.tile[(x, y)] = STONE_T
        self.cx = ax + AW // 2
        self.fy = ay + int(KR["ArenaFloorRow"])
        self.half = int(KR["ArenaHalf"])
        self.carve()
        self.shells()
        self.build_arena2()
        self.furnish()

    def carve(self):
        ax, ay = self.area[0], self.area[1]
        for row in range(LH):
            for col in range(LW):
                ch = self.at(col, row)
                if ch in "#A":
                    continue
                x0, y0 = ax + col * CELL, ay + row * CELL
                if ch == "r":
                    self.rubble.append((x0, y0))
                for dy in range(CELL):
                    for dx in range(CELL):
                        x, y = x0 + dx, y0 + dy
                        self.carved.add((x, y))
                        top, bottom = dy == 0, dy == CELL - 1
                        if ch == ",":
                            self.air(x, y, COLUMN_W)
                        elif ch == "=":
                            self.air(x, y, BRICK_W)
                            if top:
                                self.solid(x, y, PLAT_T)
                        elif ch == "-":
                            self.air(x, y, BRICK_W)
                            if top:
                                self.solid(x, y, BRICK_T)
                        elif ch == "~":
                            self.water(x, y, BRICK_W)
                        elif ch == "^":
                            self.air(x, y, BRICK_W)
                            if bottom:
                                self.solid(x, y, SPIKE_T)
                                self.spikes.append((x, y))
                        elif ch == "r":
                            self.solid(x, y, RUBBLE_T)
                            self.wd.wall[(x, y)] = BRICK_W
                        else:
                            self.air(x, y, BRICK_W)

    def shells(self):
        ax, ay = self.area[0], self.area[1]
        depth, every = int(KR["ShellDepth"]), int(KR["VaultRuneEvery"])
        for x in range(ax, ax + AW):
            for y in range(ay, ay + AH):
                if (x, y) in self.carved or self.wd.tile.get((x, y)) != STONE_T:
                    continue
                near = depth + 1
                for oy in range(-depth, depth + 1):
                    for ox in range(-depth, depth + 1):
                        if (x + ox, y + oy) in self.carved and ax <= x + ox < ax + AW and ay <= y + oy < ay + AH:
                            near = min(near, max(abs(ox), abs(oy)))
                if near > depth:
                    continue
                vault = (x, y + 1) in self.carved and y + 1 < ay + AH and ((x - ax) + (y - ay)) % every == 0
                self.solid(x, y, RUNE_T if vault else (CORAL_T if near == depth and self.noise(x, y) < CORAL_SHARE else BRICK_T))
                self.wd.wall[(x, y)] = BRICK_W

    def build_arena2(self):
        """BuildArena (2026-11-11b): the dome, no side door; the gate in its crown; platforms under it to climb back out."""
        cx, fy, half, shell = self.cx, self.fy, self.half, int(KR["Shell"])
        reach = half + shell
        for dx in range(-reach, reach):
            for dy in range(1 - int(KR["FloorDepth"]), int(KR["ArenaTop"]) + shell + 1):
                x, y = cx + dx, fy - dy
                if self.interior(dx, dy):
                    self.air(x, y, BRICK_W)
                    continue
                near = dy <= 0 and abs(dx + 0.5) <= reach
                for ox in range(-shell, shell + 1):
                    for oy in range(-shell, shell + 1):
                        if near:
                            break
                        near = self.interior(dx + ox, dy + oy)
                if not near:
                    continue
                face = self.interior(dx + 1, dy) or self.interior(dx - 1, dy) or self.interior(dx, dy + 1) or self.interior(dx, dy - 1)
                self.solid(x, y, ARUNE_T if face and dy >= 2 and (dx + dy) % int(KR["RuneEvery"]) == 0 else ABRICK_T)
        self.arena = (cx - reach, fy - int(KR["ArenaTop"]) - shell, 2 * reach, int(KR["ArenaTop"]) + shell + int(KR["FloorDepth"]))
        for c in (11, 22):
            if c >= half - 1:
                continue
            for dy in range(1, self.inside(c) + 1):
                for dx in (c - 1, c, -c, -c - 1):
                    if self.interior(dx, dy):
                        self.wd.wall[(cx + dx, fy - dy)] = COLUMN_W
        for side in (1, -1):
            start = int(KR["PuddleX"]) - int(KR["PuddleWidth"]) // 2 if side > 0 else -int(KR["PuddleX"]) - int(KR["PuddleWidth"]) // 2
            for k in range(int(KR["PuddleWidth"])):
                if abs(start + k) >= half - 1:
                    break
                self.water(cx + start + k, fy, BRICK_W)
        for step in range(1, int(KR["DaisSteps"]) + 1):
            w = int(KR["DaisHalf"]) + (int(KR["DaisSteps"]) - step) * 2
            for dx in range(-w, w):
                self.solid(cx + dx, fy - step, ARUNE_T)
        floor_y = fy - int(KR["DaisSteps"])
        self.stone_at = (cx - 2, floor_y - int(KS["Height"]))
        for dx in range(int(KS["Width"])):
            for dy in range(int(KS["Height"])):
                self.wd.tile[(cx - 2 + dx, floor_y - int(KS["Height"]) + dy)] = OBJ_T
        gl, gt = cx - int(KSE["Width"]) // 2, fy - int(KR["ArenaTop"]) - shell      # the gate
        self.seal_at = (gl, gt)
        for dx in range(int(KSE["Width"])):
            for dy in range(int(KSE["Height"])):
                self.wd.tile[(gl + dx, gt + dy)] = SEAL_T
        self.platforms(int(KR["LowPlatformY"]), int(KR["LowPlatformFrom"]), min(int(KR["LowPlatformTo"]), half - 3))
        self.platforms(int(KR["HighPlatformY"]), int(KR["HighPlatformFrom"]), int(KR["HighPlatformTo"]))
        self.platforms(int(KR["LadderY1"]), 0, int(KR["LadderHalf1"]))
        self.platforms(int(KR["LadderY2"]), 0, int(KR["LadderHalf2"]))
        dx = -half + 2
        while dx < half - 2:
            if abs(dx + 0.5) >= 10:
                self.kelp(cx + dx, fy - self.inside(dx), self.rng.randint(int(KR["KelpMin"]), int(KR["KelpMax"])))
            dx += self.rng.randint(3, 6)

    def furnish(self):
        ax, ay = self.area[0], self.area[1]
        left_floor = right_floor = -1
        for row in range(LH):
            for col in range(LW):
                ch = self.at(col, row)
                x0, y0 = ax + col * CELL, ay + row * CELL
                if ch in "123":
                    top = y0 + CELL - int(KG["Height"])
                    if all(self.is_air(x0 + dx, top + dy) for dx in range(int(KG["Width"])) for dy in range(int(KG["Height"]))):
                        for dx in range(int(KG["Width"])):
                            for dy in range(int(KG["Height"])):
                                self.wd.tile[(x0 + dx, top + dy)] = GLYPH_T
                        self.glyphs.append((int(ch) - 1, x0, top))
                elif ch == "c":
                    self.chest_at = (x0, y0)
                    for dx in range(2):
                        for dy in range(2):
                            self.wd.tile[(x0 + dx, y0 + dy)] = CHEST_T
                elif ch == "E":
                    if col == 0:
                        left_floor = max(left_floor, y0 + CELL)
                    elif col == LW - 1:
                        right_floor = max(right_floor, y0 + CELL)
        for x in range(ax + 1, ax + AW - 1):                     # kelp from the ceilings
            for y in range(ay + 1, ay + AH - 4):
                if ((x, y) not in self.carved or self.is_arena(x, y - 1) or not self.is_air(x, y) or self.is_air(x, y - 1)
                        or self.rng.randrange(int(KR["KelpChance"])) != 0):
                    continue
                self.kelp(x, y, self.rng.randint(int(KR["KelpMin"]), int(KR["KelpMax"])))
        if left_floor >= 0:
            self.tunnel(ax - 1, -1, left_floor)
            self.marks["entrance_l"] = (ax, left_floor)
        if right_floor >= 0:
            self.tunnel(ax + AW, 1, right_floor)
            self.marks["entrance_r"] = (ax + AW - 1, right_floor)


# --- the new objects' looks -------------------------------------------------------------------------------------------------
def object_tiles(sheet, col0, tw, th):
    """A multi-tile object rebuilt from its 18 px stride sheet."""
    out = Image.new("RGBA", (tw * 16, th * 16), (0, 0, 0, 0))
    for ty in range(th):
        for tx in range(tw):
            out.alpha_composite(sheet.crop(((col0 + tx) * 18, ty * 18, (col0 + tx) * 18 + 16, ty * 18 + 16)), (tx * 16, ty * 16))
    return out


def glyph_image(style, lit):
    body = object_tiles(load(RUIN + "Tiles/FundamentalGlyphTile.png"), style * 2, 2, 3)
    glow = object_tiles(load(RUIN + "Tiles/FundamentalGlyphTile_Glow.png"), style * 2, 2, 3)
    additive(body, glow, (0, 0), lit)
    return body


def seal_image(lit):
    """The gate with the sockets of the lit glyphs glowing (`lit`: three opacities)."""
    body = object_tiles(load(RUIN + "Tiles/FundamentalSealTile.png"), 0, 9, 3)
    glow = object_tiles(load(RUIN + "Tiles/FundamentalSealTile_Glow.png"), 0, 9, 3)
    for k, col in enumerate((2, 4, 6)):
        cell = glow.crop((col * 16, 16, col * 16 + 16, 32))
        additive(body, cell, (col * 16, 16), lit[k])
    return body


def spike_tile(img, X, Y):
    d = ImageDraw.Draw(img)                                       # a stand-in for vanilla's Spikes
    d.rectangle([X, Y + 10, X + 15, Y + 15], fill=(90, 90, 100, 255))
    for k in range(4):
        d.polygon([(X + k * 4, Y + 10), (X + k * 4 + 2, Y + 1), (X + k * 4 + 4, Y + 10)], fill=(200, 200, 212, 255), outline=(70, 70, 80, 255))


def draw_ruins(world, ruins, x0, y0, x1, y1, lit=(0.2, 0.2, 0.2), seal=True, seal_lit=(0.18, 0.18, 0.18)):
    """render() plus the 2026-11-11b objects: spikes, the glyphs and the gate."""
    img = render(world, x0, y0, x1, y1, stone_at=ruins.stone_at, stone_style=2, shield=KS["ShieldOpacity"], shield_k=0)
    for (x, y) in ruins.spikes:
        if x0 <= x <= x1 and y0 <= y <= y1:
            spike_tile(img, (x - x0) * 16, (y - y0) * 16)
    for (k, gx, gy) in ruins.glyphs:
        if x0 <= gx <= x1 and y0 <= gy <= y1:
            img.alpha_composite(glyph_image(k, lit[k]), ((gx - x0) * 16, (gy - y0) * 16))
    if seal and ruins.seal_at:
        sx, sy = ruins.seal_at
        if x0 <= sx <= x1 and y0 <= sy <= y1:
            img.alpha_composite(seal_image(seal_lit), ((sx - x0) * 16, (sy - y0) * 16))
    return img


def build_world(flip=False):
    world = World(300, 170, seed=11)
    ruins = Ruins2(world, seed=3, flip=flip)
    ruins.build()
    return world, ruins


AREAS = (("west entry", 0, 12), ("east entry", 103, 12), ("west atrium", 13, 3), ("east atrium", 89, 3),
         ("upper gallery", 50, 3), ("sanctum", 50, 11), ("gate hall", 49, 23), ("ARENA", 52, 38), ("drowned crypt", 9, 31),
         ("bell tower", 103, 0), ("collapsed hall", 79, 31), ("catacombs", 30, 50), ("ossuary", 59, 55), ("treasury", 2, 44))


def ruins_png(out, font_path):
    font, big = font_at(font_path, 15), font_at(font_path, 22)
    world, ruins = build_world()
    ax, ay = ruins.area[0], ruins.area[1]
    full = draw_ruins(world, ruins, ax - 8, ay - 4, ax + AW + 8, ay + AH + 4)
    q = 4                                                         # the overview at a quarter
    over = full.resize((full.width // q, full.height // q), Image.NEAREST)
    d = ImageDraw.Draw(over)

    def at(tx, ty):
        return ((tx - (ax - 8)) * 16 // q, (ty - (ay - 4)) * 16 // q)
    for (x, y) in ruins.rubble:
        p0, p1 = at(x, y), at(x + CELL, y + CELL)
        d.rectangle([p0[0], p0[1], p1[0], p1[1]], outline=PLUG, width=2)
    for (k, gx, gy) in ruins.glyphs:
        p = at(gx + 1, gy - 2)
        d.ellipse([p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14], outline=GLYPH, width=3)
        d.text((p[0] - 26, p[1] + 16 if p[1] < 60 else p[1] - 34), "glyph %d" % (k + 1), fill=GLYPH, font=big)
    sx, sy = ruins.seal_at
    p0, p1 = at(sx, sy), at(sx + int(KSE["Width"]), sy + int(KSE["Height"]))
    d.rectangle([p0[0] - 3, p0[1] - 3, p1[0] + 3, p1[1] + 3], outline=ARENA, width=3)
    d.text((p1[0] + 8, p0[1] - 6), "the sealed gate", fill=ARENA, font=font)
    a = ruins.arena
    p0, p1 = at(a[0], a[1]), at(a[0] + a[2], a[1] + a[3])
    d.rectangle([p0[0], p0[1], p1[0], p1[1]], outline=ARENA, width=2)
    if ruins.chest_at:
        p = at(ruins.chest_at[0] + 1, ruins.chest_at[1])
        d.text((p[0] + 10, p[1] - 8), "chest", fill=CHEST, font=font)
    for (name, col, row) in AREAS:
        p = at(ax + col * CELL, ay + row * CELL)
        d.text((p[0] + 2, p[1] + 1), name, fill=(238, 241, 243), font=font, stroke_width=2, stroke_fill=(16, 18, 26))
    # closer: the gate hall and the arena; the three glyphs' shrines
    cx, fy = ruins.cx, ruins.fy
    hall = draw_ruins(world, ruins, cx - 40, fy - 47, cx + 40, fy + 4)
    hall = hall.resize((hall.width // 2, hall.height // 2), Image.NEAREST)

    def close(k, r):
        g = [gl for gl in ruins.glyphs if gl[0] == k][0]
        im = draw_ruins(world, ruins, g[1] - r, g[2] - 10, g[1] + r, g[2] + 6, lit=tuple(1.0 if j == k else 0.25 for j in range(3)))
        return im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    shrines = [close(k, 16) for k in range(3)]
    gap = 12
    title = 44
    W = max(over.width, hall.width + gap + max(s.width for s in shrines)) + 2 * gap
    H = title + over.height + gap + 30 + max(hall.height, sum(s.height + 24 for s in shrines)) + gap
    sheet = Image.new("RGBA", (W, H), (18, 20, 28, 255))
    sd = ImageDraw.Draw(sheet)
    sd.text((gap, 10), "Fundamental Ruins (2026-11-11b): %dx%d tiles; rubble red, glyphs violet, the gate cyan" % (AW, AH),
            fill=(238, 241, 243), font=big)
    sheet.alpha_composite(over, (gap, title))
    y = title + over.height + gap
    sd.text((gap, y), "the gate hall over the arena (1/2): the gate in its crown, the stone, the platforms", fill=ARENA, font=font)
    sheet.alpha_composite(hall, (gap, y + 24))
    yy = y
    names = ("glyph 1: the drowned crypt", "glyph 2: the bell tower", "glyph 3: the ossuary")
    for k, s in enumerate(shrines):
        sd.text((gap * 2 + hall.width, yy), names[k], fill=GLYPH, font=font)
        sheet.alpha_composite(s, (gap * 2 + hall.width, yy + 22))
        yy += s.height + 24 + 4
    sheet.convert("RGB").save(out)
    print("%s: %dx%d" % (out, sheet.width, sheet.height))


# ================================================================================================
# The glyphs and the gate
# ================================================================================================
class Motes:
    def __init__(self):
        self.items = []

    def burst(self, x, y, w, h, n, col, up=False):
        for _ in range(n):
            px, py = x + random.uniform(0, w), y + random.uniform(0, h)
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(1.0, 3.5)
            vx, vy = math.cos(a) * sp, (math.sin(a) * sp if not up else random.uniform(0.5, 3.0))
            self.items.append([px, py, vx, vy, random.randint(20, 40), col])

    def step_draw(self, img, dy=0):
        d = ImageDraw.Draw(img)
        alive = []
        for m in self.items:
            m[0] += m[2]
            m[1] += m[3]
            m[3] += 0.08
            m[4] -= 1
            if m[4] > 0:
                d.rectangle([int(m[0]), int(m[1] + dy), int(m[0]) + 1, int(m[1] + dy) + 1], fill=m[5] + (255,))
                alive.append(m)
        self.items = alive


def scene_gate(out, font):
    world, ruins = build_world()
    cx, fy = ruins.cx, ruins.fy
    x0, y0, x1, y1 = cx - 22, fy - 50, cx + 22, fy - 4
    W, H = (x1 - x0 + 1) * 16, (y1 - y0 + 1) * 16
    gif = Gif(font, (W, H), scale=1.0)
    sx, sy = ruins.seal_at
    seal_px = ((sx - x0) * 16, (sy - y0) * 16)
    lights = (30, 80, 130)                                        # the ticks each glyph is lit at
    lit = [0.0, 0.0, 0.0]
    open_at = lights[2]
    backs = {}
    motes = Motes()
    notes = [(0, "the gate hall: the gate shut in its floor, 0/3 sockets lit (a dark glyph's rune breathes faintly)")]
    pops = []
    # the player stands on the gate, then drops through it onto the platforms under it
    px, py, vy = float((cx) * 16 - x0 * 16), float(seal_px[1]), 0.0
    platforms = [fy - int(KR["HighPlatformY"])]                     # holding down, through the two under the gate
    tick = 0
    while tick < 330:
        tick += 1
        for k, t in enumerate(lights):
            if tick == t:
                lit[k] = 1.0
                notes.append((tick, "glyph %d lit (%d/3): its socket in the gate lights%s" % (k + 1, k + 1, "" if k < 2 else "; the third opens the gate")))
                pops.append((tick, 20 + k * 100, 120, "glyph %d/3" % (k + 1), GLOW))
        opened = tick >= open_at
        if tick == open_at:
            motes.burst(seal_px[0], seal_px[1], 9 * 16, 3 * 16, 70, (150, 156, 170))
            motes.burst(seal_px[0], seal_px[1], 9 * 16, 3 * 16, 30, GLOW)
            notes.append((tick, "\"The sealed gate of the Fundamental Ruins grinds open!\" the slab is gone for good"))
        if opened and tick > open_at + 20:                        # the player falls through
            vy = min(10.0, vy + GRAVITY)
            ny = py + vy
            for p in platforms:
                floor_px = (p - y0) * 16
                if py <= floor_px < ny + 0.01 and vy > 0:
                    ny, vy = float(floor_px), 0.0
                    break
            py = ny
            if tick == open_at + 21:
                notes.append((tick, "the player drops into the arena (through the platforms under the gate: they lead back up and out)"))
        if tick % TPF:
            continue
        key = opened
        if key not in backs:
            backs[key] = draw_ruins(world, ruins, x0, y0, x1, y1, lit=(0, 0, 0), seal=not opened)
        img = backs[key].copy()
        if not opened:
            img.alpha_composite(seal_image(tuple(0.18 + 0.82 * v for v in lit)), seal_px)
        for k in range(3):                                         # the three glyphs, inset
            gimg = glyph_image(k, 0.2 + 0.8 * lit[k]).resize((64, 96), Image.NEAREST)
            bx = 16 + k * 100
            ImageDraw.Draw(img).rectangle([bx - 6, 40, bx + 70, 146], fill=(14, 16, 24, 255), outline=GLOW if lit[k] else (70, 70, 90, 255), width=2)
            img.alpha_composite(gimg, (bx, 46))
        shake = (tick % 6 < 3) and open_at <= tick < open_at + 30
        if shake:
            img = img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, 2), resample=Image.NEAREST)
        img.alpha_composite(player_sprite(), (int(px - 20), int(py - 56)))
        motes.step_draw(img)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Diamond Cutter
# ================================================================================================
def gun_on(img, sprite, hand, angle, holdout):
    """Vanilla's gun draw (useStyle 5, facing right), approximated: the sprite turned about its grip (-HoldoutOffset.X, H/2)."""
    gw, gh = sprite.size
    ox, oy = -holdout[0], gh / 2
    big = Image.new("RGBA", (gw * 3, gh * 3), (0, 0, 0, 0))
    big.alpha_composite(sprite, (int(gw * 1.5 - ox), int(gh * 1.5 - oy)))
    rot = big.rotate(-math.degrees(angle), resample=Image.NEAREST, center=(gw * 1.5, gh * 1.5))
    img.alpha_composite(rot, (int(hand[0] - gw * 1.5), int(hand[1] + holdout[1] - gh * 1.5)))


def beam_strip(length, frame):
    tex = load(MECH + "Weapons/DiamondCutterBeam.png")
    seg, bh = int(KCB["SegmentLength"]), int(KCB["BeamHeight"])
    strip = Image.new("RGBA", (max(1, int(length)), bh), (0, 0, 0, 0))
    t = 0
    while t < length:
        w = int(min(seg, length - t))
        strip.alpha_composite(tex.crop((0, frame * int(KCB["BeamStride"]), w, frame * int(KCB["BeamStride"]) + bh)), (int(t), 0))
        t += seg
    return strip


def draw_beam(img, start, angle, length, age):
    frame = min(int(KCB["BeamFrames"]) - 1, int((max(age, 1) - 1) / KCB["FadeFrameTicks"]))
    fade = 1.0 if frame < int(KCB["BeamFrames"]) - 1 else max(0.0, min(1.0, (KCB["Lifetime"] - age + 1) / KCB["FadeFrameTicks"]))
    strip = beam_strip(length, frame)
    pad = Image.new("RGBA", (strip.width * 2 + 8, strip.width * 2 + 8), (0, 0, 0, 0))
    c = pad.width // 2
    pad.alpha_composite(strip, (c, c - strip.height // 2))
    rot = pad.rotate(-math.degrees(angle), resample=Image.NEAREST, center=(c, c))
    additive(img, rot, (int(start[0] - c), int(start[1] - c)), fade)
    sp = load(MECH + "Weapons/DiamondCutterSpark.png")
    sf = min(int(KCB["SparkFrames"]) - 1, int((max(age, 1) - 1) / KCB["SparkFrameTicks"]))
    size, stride = int(KCB["SparkSize"]), int(KCB["SparkStride"])
    cell = sp.crop((0, sf * stride, size, sf * stride + size))
    end = (start[0] + math.cos(angle) * length, start[1] + math.sin(angle) * length)
    for pt in (start, end):
        additive(img, cell, (int(pt[0] - size / 2), int(pt[1] - size / 2)), fade)


def scene_cutter(out, font):
    W, H, G = 960, 320, 280
    bg = flat_backdrop(W, H, G)
    wall_x = 740                                                   # a pillar for the last shot
    dd = ImageDraw.Draw(bg)
    gun = load(MECH + "Weapons/DiamondCutter.png")
    holdout = (-8, 2)
    dummies = [360, 470, 580, 690]
    gif = Gif(font, (W, H), scale=1.0)
    notes = [(0, "Diamond Cutter: %d damage, %d%% crit, %d use time, %d steam a shot, no ammo; the beam is instant"
              % (KC["Damage"], 4 + KC["CritBonus"], KC["UseTime"], KC["Cost"]))]
    pops, hits = [], {}
    hand = (130.0, G - 28.0)
    up = math.atan2((G - 160) - hand[1], (wall_x - 12) - hand[0])  # at the pillar's middle
    shots = [(20, 0.0, (False, False, False)), (50, 0.0, (False, True, False)), (80, 0.0, (False, False, False)),
             (120, up, (False, False, False))]
    beams = []
    walls_up = False
    tick = 0
    while tick < 200:
        tick += 1
        for (t, ang, crits) in shots:
            if tick != t:
                continue
            start = (hand[0] + math.cos(ang) * KC["MuzzleDistance"], hand[1] + math.sin(ang) * KC["MuzzleDistance"])
            if ang == 0.0:
                xs = sorted(d for d in dummies)[:int(KCB["MaxTargets"])]
                third = xs[-1]
                length = third - start[0]
                for k, x in enumerate(xs):
                    crit = crits[k]
                    dmg = int(KC["Damage"]) * (2 if crit else 1)
                    pops.append((tick, x - 10, G - 90 - k * 4, str(dmg) + ("!" if crit else ""), CRIT if crit else HIT))
                    hits[x] = tick
                if t == 20:
                    notes.append((tick, "it strikes the %d nearest enemies along the line and stops in the %drd; the 4th is untouched"
                                  % (int(KCB["MaxTargets"]), int(KCB["MaxTargets"]))))
                elif t == 50:
                    notes.append((tick, "a crit (12%%): %d; every hit ignores %d%% of the enemy's defense" % (2 * int(KC["Damage"]), int(KCB["ArmorIgnore"] * 100))))
            else:
                walls_up = True
                length = (wall_x - 12 - start[0]) / math.cos(ang)
                notes.append((tick, "aimed up at a stone pillar: the beam ends on the first solid block (platforms let it through)"))
            beams.append([start, ang, length, 0])
        for b in beams:
            b[3] += 1
        beams = [b for b in beams if b[3] <= KCB["Lifetime"]]
        if tick % TPF:
            continue
        img = bg.copy()
        if walls_up:
            d = ImageDraw.Draw(img)
            d.rectangle([wall_x - 12, G - 200, wall_x + 12, G - 120], fill=(80, 82, 92, 255), outline=(40, 40, 48, 255), width=2)
        for x in dummies:
            dummy(img, x, G, hits.get(x, -99) > tick - 10)
        img.alpha_composite(player_sprite(), (int(hand[0] - 26), G - 56))
        ang = beams[-1][1] if beams else 0.0
        gun_on(img, gun, hand, ang, holdout)
        for (start, a, length, age) in beams:
            draw_beam(img, start, a, length, age)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Barrel Gun
# ================================================================================================
def fish_frame(kind, flop):
    sheet = load(MECH + "Weapons/BarrelGunFish.png")
    fw, fh, st = int(KF["FrameWidth"]), int(KF["FrameHeight"]), int(KF["FrameStride"])
    k = kind * int(KF["FlopFrames"]) + flop
    return sheet.crop((0, k * st, fw, k * st + fh))


def draw_fish(img, f):
    im = fish_frame(f["kind"], (f["age"] // int(KF["FrameTicks"])) % int(KF["FlopFrames"]))
    if f["vx"] < 0:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    rot = im.rotate(-math.degrees(math.atan2(f["vy"], f["vx"])), resample=Image.NEAREST, expand=True)
    img.alpha_composite(rot, (int(f["x"] - rot.width / 2), int(f["y"] - rot.height / 2)))


def stars(img, x, top, tick):
    sheet = load(MECH + "Buffs/StunStars.png")
    size, stride = int(KST["StarSize"]), int(KST["StarStride"])
    for k in range(int(KST["StarCount"])):
        a = tick * KST["StarSpin"] + k * 2 * math.pi / KST["StarCount"]
        fr = (tick // 8 + k) % int(KST["StarFrames"])
        cell = sheet.crop((0, fr * stride, size, fr * stride + size))
        img.alpha_composite(cell, (int(x + math.cos(a) * KST["StarOrbit"] - size / 2), int(top - 6 + math.sin(a) * KST["StarOrbit"] * 0.35 - size / 2)))


def rain(img, tick, rng):
    d = ImageDraw.Draw(img)
    for k in range(70):
        x = (k * 37 + tick * 9) % (img.width + 60) - 30
        y = (k * 53 + tick * 14) % img.height
        d.line([x, y, x - 4, y + 12], fill=(150, 170, 210, 255), width=1)


def lob_angle(start, target, speed):
    """The angle whose arc (BarrelGunFish: gravity after GravityDelay ticks) passes nearest the target."""
    best, best_d = 0.0, 1e9
    for k in range(-80, 30):
        a = k / 100.0
        x, y, vx, vy = start[0], start[1], math.cos(a) * speed, math.sin(a) * speed
        for t in range(1, 160):
            if t > KF["GravityDelay"]:
                vy = min(vy + KF["Gravity"], KF["MaxFall"])
            x += vx
            y += vy
            if x >= target[0]:
                if abs(y - target[1]) < best_d:
                    best, best_d = a, abs(y - target[1])
                break
    return best


def scene_barrel(out, font):
    W, H, G = 960, 320, 280
    bg = flat_backdrop(W, H, G)
    gun = load(MECH + "Weapons/BarrelGun.png")
    holdout = (int(KBG["Holdout"]) if "Holdout" in KBG else -14, 2)
    holdout = (-14, 2)
    gif = Gif(font, (W, H), scale=1.0)
    rng = random.Random(4)
    hand = (130.0, G - 28.0)
    notes = [(0, "Barrel Gun: %d damage, never crits, %d use time, %d steam a shot; fish fly in an arc"
              % (KBG["Damage"], KBG["UseTime"], KBG["Cost"]))]
    pops, fish, stunned = [], [], {}
    targets = {"a": [480.0, float(G)], "b": [660.0, float(G)]}
    fly = [760.0, 170.0]
    hits = {}
    tick = 0
    total = 360
    rain_from = 180
    while tick < total:
        tick += 1
        raining = tick >= rain_from
        if tick == rain_from:
            fish = []
            notes.append((tick, "in the rain (or under water): +%d%% damage (%d a hit) and the fish fly straight, homing in"
                          % (int((KBG["EmpoweredDamage"] - 1) * 100), int(KBG["Damage"] * KBG["EmpoweredDamage"]))))
        if tick % int(KBG["UseTime"]) == 1 and tick < total - 40:
            if raining:
                ang = math.atan2(fly[1] - hand[1], fly[0] - hand[0]) - 0.35
            else:
                tx = targets["a" if (tick // int(KBG["UseTime"])) % 2 == 0 else "b"][0]
                muzzle_from = (hand[0] + KBG["MuzzleDistance"] * 0.95, hand[1] - 10)
                ang = lob_angle(muzzle_from, (tx, G - 34.0), KBG["ShotSpeed"])
            sp = KBG["ShotSpeed"]
            fish.append({"x": hand[0] + math.cos(ang) * KBG["MuzzleDistance"], "y": hand[1] + math.sin(ang) * KBG["MuzzleDistance"],
                         "vx": math.cos(ang) * sp, "vy": math.sin(ang) * sp, "age": 0, "kind": rng.randrange(3), "emp": raining})
        if raining:
            fly[1] = 170.0 + 50.0 * math.sin(tick * 0.05)
        alive = []
        for f in fish:
            f["age"] += 1
            if f["emp"]:
                tx, ty = fly[0] - f["x"], fly[1] - f["y"]
                n = math.hypot(tx, ty) or 1.0
                wx, wy = tx / n * KF["HomingSpeed"], ty / n * KF["HomingSpeed"]
                f["vx"] += (wx - f["vx"]) * KF["HomingLerp"]
                f["vy"] += (wy - f["vy"]) * KF["HomingLerp"]
            elif f["age"] > KF["GravityDelay"]:
                f["vy"] = min(f["vy"] + KF["Gravity"], KF["MaxFall"])
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            hit = None
            if f["emp"]:
                if abs(f["x"] - fly[0]) < 16 and abs(f["y"] - fly[1]) < 26:
                    hit = ("fly", fly[0], fly[1] - 20)
            elif not raining:
                for name, (tx, ty) in targets.items():
                    if abs(f["x"] - tx) < 14 and ty - 60 < f["y"] < ty:
                        hit = (name, tx, ty - 70)
            if hit:
                dmg = int(round(KBG["Damage"] * (KBG["EmpoweredDamage"] if f["emp"] else 1.0)))
                pops.append((tick, hit[1] - 10, hit[2], str(dmg), HIT))
                hits[hit[0]] = tick
                if hit[0] == "a" and "a" not in stunned:
                    stunned["a"] = tick
                    notes.append((tick, "a %d%% roll: the dummy is stunned %d s (its AI held, no contact damage; never bosses or mini-bosses)"
                                  % (int(KF["StunChance"] * 100), int(KF["StunTicks"]) // 60)))
                continue
            if f["y"] > G - 2 or f["age"] > KF["Lifetime"]:
                continue
            alive.append(f)
        fish = alive
        if tick % TPF:
            continue
        img = bg.copy()
        if raining:
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, W, G], fill=(20, 30, 50, 90))
        if not raining:
            for name, (tx, ty) in targets.items():
                dummy(img, int(tx), G, hits.get(name, -99) > tick - 10)
            if "a" in stunned and tick - stunned["a"] < KF["StunTicks"]:
                stars(img, targets["a"][0], G - 62, tick)
        else:
            d = ImageDraw.Draw(img)
            fx, fy_ = int(fly[0]), int(fly[1])                      # a dummy hung from a rope, swinging up and down
            d.line([fx, 0, fx, fy_ - 30], fill=(140, 110, 70, 255), width=2)
            lean = 3 if hits.get("fly", -99) > tick - 10 else 0
            d.rounded_rectangle([fx - 12 + lean, fy_ - 28, fx + 12 + lean, fy_ + 4], radius=6, fill=(196, 160, 104, 255), outline=(98, 70, 40, 255), width=2)
            rain(img, tick, rng)
        img.alpha_composite(player_sprite(), (int(hand[0] - 26), G - 56))
        gun_on(img, gun, hand, -0.3, holdout)
        for f in fish:
            draw_fish(img, f)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Dragonete Miudo
# ================================================================================================
def hell_backdrop(W, H, G):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([0, y, W, y], fill=(int(44 + 40 * t), int(16 + 10 * t), int(16 + 6 * t), 255))
    rng = random.Random(6)
    for x in range(0, W, 16):                                      # ash and hellstone stand-ins
        for y in range(G, H, 16):
            base = (58, 36, 40) if y > G else (84, 52, 52)
            d.rectangle([x, y, x + 15, y + 15], fill=base + (255,))
            if rng.random() < 0.3:
                px, py = x + rng.randrange(2, 13), y + rng.randrange(2, 13)
                d.rectangle([px, py, px + 1, py + 1], fill=(236, 113, 40, 255) if y > G else (110, 70, 66, 255))
        if (x // 16) % 7 == 3:
            d.rectangle([x, G - 2, x + 15, G], fill=(255, 150, 60, 255))
    return img


class Dragonet:
    HOVER, INHALE, SPIT, REAR, SWOOP, BITE, RETREAT = range(7)
    NAMES = ("hover", "INHALE (the telegraph)", "spit", "REAR (the screech)", "SWOOP", "BITE", "retreat")

    def __init__(self, x, y):
        self.x, self.y, self.vx, self.vy = x, y, 0.0, 0.0
        self.state, self.timer, self.side, self.missed, self.face = self.HOVER, 0, 1, False, -1

    def change(self, s):
        self.state, self.timer = s, 0

    def anchor(self):
        """DrawAnchor: the origin behind the hitbox's centre by AnchorShift, the bob on the down-beat."""
        fr = self.frame()
        bob = -2 if fr in (int(KD["Fly"]) + 3, int(KD["Fly"]) + 4) else 0
        return (self.x - KD["AnchorShift"] * self.face, self.y + bob)

    def mouth(self):
        ax, ay = self.anchor()
        return (ax - KD["MouthX"] * self.face, ay + KD["MouthY"])

    def box(self):
        return (self.x - KD["Width"] / 2, self.y - KD["Height"], self.x + KD["Width"] / 2, self.y)

    def frame(self):
        s, t = self.state, self.timer
        if s == self.INHALE:
            return int(KD["Inhale"]) + min(2, int(t / (KD["InhaleTicks"] / 3.0)))
        if s == self.SPIT:
            return int(KD["Spit"]) + min(2, int(t / (KD["SpitTicks"] / 3.0)))
        if s == self.SWOOP:
            return int(KD["Swoop"]) + (t // 4) % 2
        if s == self.BITE:
            return int(KD["Bite"]) + min(2, int(t / (KD["BiteTicks"] / 3.0)))
        if s == self.REAR:
            return int(KD["Fly"]) + (t // (int(KD["FlapTicks"]) - 1)) % int(KD["FlyFrames"])
        return int(KD["Fly"]) + (t // int(KD["FlapTicks"])) % int(KD["FlyFrames"])


def scene_dragonete(out, font):
    W, H, G = 1000, 400, 352
    bg = hell_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    planes = Planes("Content/Underworld/NPCs/DragoneteMiudo", KD)
    bolt_sheet = load("Content/Underworld/Projectiles/DragoneteFireBolt.png")
    p = Runner(260.0, G)
    dr = Dragonet(260.0 + KD["HoverDistance"], G - 220.0)
    bolt = None
    notes = [(0, "Dragonete Miudo (%d life, %d defense, %d contact, %d biting): it hovers %d tiles off to the side, %d up"
              % (KD["Life"], KD["Defense"], KD["ContactDamage"], int(KD["ContactDamage"] * KD["BiteMultiplier"]),
                 KD["HoverDistance"] // 16, KD["HoverHeight"] // 16))]
    pops, last = [], None
    tick, end = 0, None
    hover_cd = int(KD["SpitCooldown"]) - 40                     # its first spit soon
    while tick < 900:
        tick += 1
        dr.timer += 1
        px, py = p.x, p.y - PLAYER_H / 2
        to_target = 1 if px >= dr.x else -1
        s = dr.state
        if s == dr.HOVER:
            goal = (px + dr.side * KD["HoverDistance"], py - KD["HoverHeight"] + math.sin(dr.timer * 0.06) * 10)
            gx, gy = goal[0] - dr.x, goal[1] - (dr.y - KD["Height"] / 2)
            n = math.hypot(gx, gy) or 1.0
            sp = min(KD["HoverSpeed"], n * 0.1)
            dr.vx += (gx / n * sp - dr.vx) * KD["HoverAccel"]
            dr.vy += (gy / n * sp - dr.vy) * KD["HoverAccel"]
            dr.face = to_target
            if dr.missed:
                dr.missed = False
                dr.change(dr.REAR)
            elif dr.timer + hover_cd >= KD["SpitCooldown"]:
                hover_cd = 0
                dr.change(dr.INHALE)
        elif s == dr.INHALE:
            dr.vx *= 0.9
            dr.vy *= 0.9
            dr.face = to_target
            if dr.timer >= KD["InhaleTicks"]:
                m = dr.mouth()
                a = math.atan2(py - m[1], px - m[0])
                bolt = {"x": m[0], "y": m[1], "vx": math.cos(a) * KD["BoltSpeed"], "vy": math.sin(a) * KD["BoltSpeed"], "t": 0, "touched": False}
                dr.change(dr.SPIT)
        elif s == dr.SPIT:
            dr.vx *= 0.92
            dr.vy *= 0.92
            if dr.timer >= KD["SpitTicks"]:
                dr.change(dr.HOVER)
        elif s == dr.REAR:
            dr.vx += (-to_target * 1.5 - dr.vx) * 0.1
            dr.vy += (-1.5 - dr.vy) * 0.1
            dr.face = to_target
            if dr.timer >= KD["RearTicks"]:
                dr.change(dr.SWOOP)
        elif s == dr.SWOOP:
            tx, ty = px - dr.x, py - (dr.y - KD["Height"] / 2)
            n = math.hypot(tx, ty) or 1.0
            dr.vx += (tx / n * KD["SwoopSpeed"] - dr.vx) * KD["SwoopSteer"]
            dr.vy += (ty / n * KD["SwoopSpeed"] - dr.vy) * KD["SwoopSteer"]
            dr.face = 1 if dr.vx >= 0 else -1
            jaws = (dr.box()[0] - 6, dr.box()[1] - 6, dr.box()[2] + 6, dr.box()[3] + 6)
            if overlaps(jaws, p.box()):
                dr.change(dr.BITE)
                bite = int(KD["ContactDamage"] * KD["BiteMultiplier"])
                pops.append((tick, p.x - 10, p.y - 80, str(bite), HURT))
                p.vx, p.vy, p.hold, p.immune = 4.5 * dr.face, -4.5 * 7 / 9.0, 0, IMMUNITY
            elif dr.timer >= KD["SwoopMaxTicks"] or (dr.timer > 10 and tx * dr.vx + ty * dr.vy < 0):
                dr.change(dr.RETREAT)
        elif s == dr.BITE:
            dr.vx *= 0.9
            dr.vy *= 0.9
            if dr.timer >= KD["BiteTicks"]:
                dr.change(dr.RETREAT)
        elif s == dr.RETREAT:
            dr.vx += (-to_target * KD["RetreatSpeed"] * 0.6 - dr.vx) * 0.08
            dr.vy += (-KD["RetreatSpeed"] - dr.vy) * 0.08
            dr.face = to_target
            if dr.timer >= KD["RetreatTicks"]:
                dr.change(dr.HOVER)
                end = tick + 60
        dr.x += dr.vx
        dr.y += dr.vy
        if bolt:                                                  # the bolt: straight, burns out or meets the floor
            bolt["t"] += 1
            bolt["x"] += bolt["vx"]
            bolt["y"] += bolt["vy"]
            bb = (bolt["x"] - 6, bolt["y"] - 6, bolt["x"] + 6, bolt["y"] + 6)
            if overlaps(bb, p.box()) and p.immune == 0:
                bolt["touched"] = True
            if bolt["t"] == 18 and not bolt["touched"]:
                p.jump()
            if bolt["y"] >= G or bolt["t"] >= KDB["Lifetime"] or bolt["touched"]:
                if not bolt["touched"]:
                    dr.missed = True
                    notes.append((tick, "the player jumps it: the bolt burns out on the ground untouched - a miss"))
                bolt = None
        p.step()
        if dr.state != last:
            if dr.state == dr.INHALE:
                notes.append((tick, "in sight within %d tiles: it inhales %d ticks (head reared, chest swelling, throat glowing)" % (KD["SpitRange"] // 16, KD["InhaleTicks"])))
            elif dr.state == dr.SPIT:
                notes.append((tick, "...and spits a fire bolt at %.1f px/tick where the player stands (%d; 50%% to burn)" % (KD["BoltSpeed"], KD["BoltDamage"])))
            elif dr.state == dr.REAR:
                notes.append((tick, "it missed: it screeches and rears %d ticks (the second telegraph)..." % KD["RearTicks"]))
            elif dr.state == dr.SWOOP:
                notes.append((tick, "...and swoops in at %.0f px/tick, jaws open, steering after the player" % KD["SwoopSpeed"]))
            elif dr.state == dr.BITE:
                notes.append((tick, "it reaches the player: the bite (x%.1f contact)" % KD["BiteMultiplier"]))
            elif dr.state == dr.RETREAT:
                notes.append((tick, "then it flies back up and away, to spit again"))
            last = dr.state
        if tick % TPF == 0:
            img = bg.copy()
            fr = dr.frame()
            planes.draw(img, fr, dr.anchor(), dr.face == 1, glow=1.0 if dr.state in (dr.INHALE, dr.SPIT) else 0.8)
            if bolt:
                cell = bolt_sheet.crop((0, (bolt["t"] // int(KDB["FrameTicks"])) % int(KDB["Frames"]) * int(KDB["FrameStride"]),
                                        int(KDB["FrameSize"]), (bolt["t"] // int(KDB["FrameTicks"])) % int(KDB["Frames"]) * int(KDB["FrameStride"]) + int(KDB["FrameSize"])))
                rot = cell.rotate(-math.degrees(math.atan2(bolt["vy"], bolt["vx"])), resample=Image.NEAREST, expand=True)
                img.alpha_composite(rot, (int(bolt["x"] - rot.width / 2), int(bolt["y"] - rot.height / 2)))
            sprite = player_sprite(flip=p.face < 0)
            if p.immune and (tick // 3) % 2:
                sprite = faded(sprite, 0.5)
            img.alpha_composite(sprite, (int(p.x - 20), int(p.y - 56)))
            gif.text(img, (10, 34), "dragonet: %s" % Dragonet.NAMES[dr.state], fill=HURT if dr.state in (dr.SWOOP, dr.BITE) else STEAM)
            numbers(gif, img, pops, tick)
            note(gif, img, notes, tick)
            gif.push(img)
        if end is not None and tick >= end:
            break
    print("dragonete: %d ticks" % tick)
    gif.save(out)


# ================================================================================================
# The Rhino Beetle in the jungle: the knockback
# ================================================================================================
def jungle_backdrop(W, H, G):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([0, y, W, y], fill=(int(30 + 20 * t), int(54 + 20 * t), int(36 + 10 * t), 255))
    rng = random.Random(8)
    for k in range(18):                                           # vines and fronds behind
        x = rng.randrange(W)
        d.line([x, 0, x + rng.randrange(-20, 20), rng.randrange(60, 200)], fill=(40, 90, 50, 255), width=3)
    for x in range(0, W, 16):                                     # mud and jungle grass stand-ins
        for y in range(G, H, 16):
            d.rectangle([x, y, x + 15, y + 15], fill=(74, 54, 44, 255) if y > G else (82, 140, 62, 255))
            if y == G:
                d.rectangle([x, y + 8, x + 15, y + 15], fill=(74, 54, 44, 255))
    return img


def scene_beetle(out, font):
    prev.KB = KB                                                  # the old port reads its module's constants
    W, H, G = 1180, 400, 352
    bg = jungle_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    planes = Planes("Content/Jungle/NPCs/RhinoBeetle", KB)
    prev.OBSTACLES = ()
    contact, ram = int(KB["CrawlDamage"]), int(KB["CrawlDamage"] * KB["ChargeDamageMultiplier"])
    notes = [(0, "Rhino Beetle, a rare Hardmode jungle enemy: %d life, %d defense (high armor), %d contact, shrugs off %d%% of knockback"
              % (KB["Life"], KB["Defense"], contact, int(round((1 - KB["KnockbackResist"]) * 100))))]
    pops = []
    p, b = Runner(330.0, G), Beetle(170.0, G)
    phase, last, tick, end = "touch", None, 0, None
    while tick < 900:
        tick += 1
        if phase == "touch" and b.state == Beetle.BRACE:
            b.change(Beetle.CRAWL)                                 # the first contact is a plain touch (held off the charge)
            b.cooldown = 30
        if overlaps(b.box(), p.box()) and p.immune == 0 and b.state != Beetle.DAZED:
            ramming = b.ramming()
            d = b.charge_dir if ramming else (1 if p.x > b.x else -1)
            kb = 4.5 * (KB["RamKnockback"] if ramming else KB["ContactKnockback"])
            p.vx, p.vy, p.hold, p.immune = kb * d, -kb * 7 / 9.0, 0, IMMUNITY
            if ramming:
                p.toss = KB["TossSpeed"]
                pops.append((tick, p.x - 30, p.y - 90, "%d THROWN!" % ram, HURT))
                notes.append((tick, "the ram: %d, x%.0f knockback (about 20 tiles on flat ground) and the horn's toss up (%d px/tick)"
                              % (ram, KB["RamKnockback"], KB["TossSpeed"])))
                end = tick + 150
            else:
                pops.append((tick, p.x - 10, p.y - 80, "%d" % contact, HURT))
                notes.append((tick, "a plain touch: %d, and x%.1f knockback shoves the player away" % (contact, KB["ContactKnockback"])))
                phase = "charge"
        p.step()
        if p.x > W - 30:
            p.x, p.vx = W - 30.0, 0.0
        b.update(p)
        if b.state != last:
            if b.state == Beetle.BRACE and phase != "touch":
                notes.append((tick, "level and in sight: it braces %d ticks (the telegraph)..." % KB["BraceTicks"]))
            elif b.state == Beetle.CHARGE:
                notes.append((tick, "...and charges at up to %.1f px/tick" % KB["ChargeSpeed"]))
            last = b.state
        if tick % TPF == 0:
            img = bg.copy()
            planes.draw(img, b.frame(), (b.x, b.y), b.dir == 1, glow=1.0 if b.state in (Beetle.BRACE, Beetle.CHARGE) else 0.65)
            sprite = player_sprite(flip=p.face < 0)
            if p.immune and (tick // 3) % 2:
                sprite = faded(sprite, 0.5)
            img.alpha_composite(sprite, (int(p.x - 20), int(p.y - 56)))
            gif.text(img, (10, 34), "beetle: %s" % Beetle.NAMES[b.state], fill=HURT if b.ramming() else STEAM)
            numbers(gif, img, pops, tick)
            note(gif, img, notes, tick)
            gif.push(img)
        if end is not None and tick >= end:
            break
    print("beetle: %d ticks, the player at x %.0f" % (tick, p.x))
    gif.save(out)


# ================================================================================================
# The Friendo-bot
# ================================================================================================
def town_backdrop(W, H, G):
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([0, y, W, y], fill=(int(120 + 40 * t), int(160 + 30 * t), int(210 + 10 * t), 255))
    d.rectangle([W // 2 - 160, G - 140, W // 2 + 160, G], fill=(132, 92, 60, 255))           # a house's wooden wall
    for x in range(W // 2 - 160, W // 2 + 160, 16):
        d.line([x, G - 140, x, G], fill=(110, 76, 50, 255))
    for x in range(0, W, 16):
        for y in range(G, H, 16):
            d.rectangle([x, y, x + 15, y + 15], fill=(110, 80, 56, 255) if y > G else (88, 156, 70, 255))
    return img


def town_frame(sheet, k):
    return sheet.crop((0, k * 56, 40, k * 56 + 56))


def scene_friendobot(out, font):
    W, H, G = 900, 300, 250
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    plain = load("Content/Town/Friendobo.png")
    shimmer = load("Content/Town/Friendobo_Shimmer.png")
    emote = load("Content/Town/FriendoboEmote.png")
    notes = [(0, "the Friendo-bot (renamed): vanilla's town NPC sheet at vanilla's density; walking, vanilla's frame rule")]
    # vanilla's walk (NPC.VanillaFindFrame, town NPCs): frameCounter += |vx| * 2 + 1 a tick, a frame past 6; frames 2-15
    bots = [{"x": 300.0, "vx": -1.0, "sheet": plain, "frame": 2, "c": 0.0, "label": "Friendo-bot", "lo": 110, "hi": 400},
            {"x": 600.0, "vx": 1.0, "sheet": shimmer, "frame": 2, "c": 0.0, "label": "shimmered", "lo": 500, "hi": 790}]
    script = [(0, "walk"), (150, "stand"), (175, "blink"), (190, "stand"), (205, "talk"), (235, "gesture16"), (255, "gesture17"),
              (275, "sit"), (320, "throw"), (380, "emote"), (440, "end")]
    mode = "walk"
    mugs = []
    tick = 0
    while tick < 440:
        tick += 1
        for (t, m) in script:
            if tick == t:
                mode = m
                if m == "stand":
                    pass
                elif m == "blink":
                    notes.append((tick, "standing, blinking (frame 20), talking (19), the two chat gestures (16, 17)"))
                elif m == "sit":
                    notes.append((tick, "sitting on a chair (18)"))
                elif m == "throw":
                    notes.append((tick, "an enemy near: he throws a mug like the Tavernkeep (frames 21-24)"))
                elif m == "emote":
                    notes.append((tick, "his face as an emote when other townsfolk talk about him"))
        for b in bots:
            if mode == "walk":
                b["x"] += b["vx"]
                if b["x"] < b["lo"] or b["x"] > b["hi"]:
                    b["vx"] = -b["vx"]
                b["c"] += abs(b["vx"]) * 2 + 1
                if b["c"] > 6:
                    b["c"] = 0
                    b["frame"] += 1
                    if b["frame"] > 15:
                        b["frame"] = 2
            else:
                b["frame"] = {"stand": 0, "blink": 20, "talk": 19 if (tick // 8) % 2 == 0 else 0, "gesture16": 16, "gesture17": 17,
                              "sit": 18, "throw": 21 + min(3, (tick - 320) // 8), "emote": 0, "end": 0}[mode]
                if mode == "throw" and tick - 320 == 24:
                    mugs.append([b["x"] + (14 if b["vx"] > 0 else -14), G - 40.0, 6.0 * (1 if b["vx"] > 0 else -1), -4.0])
        for m in mugs:
            m[0] += m[2]
            m[1] += m[3]
            m[3] += 0.2
        mugs = [m for m in mugs if m[1] < G]
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        for b in bots:
            fr = town_frame(b["sheet"], b["frame"])
            if b["vx"] > 0:
                fr = fr.transpose(Image.FLIP_LEFT_RIGHT)              # the sheet faces left
            x = int(b["x"] - 20)
            if mode == "sit":                                       # a stand-in chair
                d.rectangle([x + 10, G - 24, x + 30, G - 18], fill=(120, 80, 46, 255))
                d.rectangle([x + (26 if b["vx"] > 0 else 10), G - 46, x + (30 if b["vx"] > 0 else 14), G], fill=(120, 80, 46, 255))
            big = fr.resize((80, 112), Image.NEAREST)               # at 2x the game's size, to read the pixels
            img.alpha_composite(big, (int(b["x"] - 40), G - 108))
            gif.text(img, (int(b["x"] - 40), G + 10), b["label"])
            if mode == "emote":
                ex, ey = int(b["x"] - 34), G - 180
                d.rounded_rectangle([ex, ey, ex + 68, ey + 56], radius=10, fill=(250, 250, 250, 255), outline=(60, 60, 70, 255), width=2)
                cell = emote.crop(((tick // 20) % 2 * 34, 0, (tick // 20) % 2 * 34 + 34, 28)).resize((68, 56), Image.NEAREST)
                img.alpha_composite(cell, (ex, ey))
        for m in mugs:
            d.rectangle([int(m[0]) - 4, int(m[1]) - 5, int(m[0]) + 4, int(m[1]) + 5], fill=(214, 170, 90, 255), outline=(120, 80, 40, 255))
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Items
# ================================================================================================
def items_png(out, font_path):
    font = font_at(font_path, 14)
    pics = [("Diamond Cutter", load(MECH + "Weapons/DiamondCutter.png"), 3),
            ("its beam (3 frames) and spark (4)", Image.new("RGBA", (1, 1)), 1),
            ("Barrel Gun", load(MECH + "Weapons/BarrelGun.png"), 3),
            ("Stunned (buff)", load(MECH + "Buffs/Stunned.png"), 3),
            ("stun stars", load(MECH + "Buffs/StunStars.png"), 4)]
    pics[1] = ("the beam, 3 frames", load(MECH + "Weapons/DiamondCutterBeam.png"), 4)
    pics.insert(2, ("the spark, 4 frames", load(MECH + "Weapons/DiamondCutterSpark.png"), 3))
    fish = load(MECH + "Weapons/BarrelGunFish.png")
    pics.append(("its fish: bass, trout, snapper (2 flops)", fish, 3))
    planes = Planes("Content/Underworld/NPCs/DragoneteMiudo", KD)
    names = ["Fly"] * 6 + ["Inhale"] * 3 + ["Spit"] * 3 + ["Swoop"] * 2 + ["Bite"] * 3
    strip = Image.new("RGBA", (6 * 100, 3 * 84), (52, 26, 24, 255))
    dd = ImageDraw.Draw(strip)
    for k in range(int(KD["Frames"])):
        cx, cy = (k % 6) * 100 + 52, (k // 6) * 84 + 76
        planes.draw(strip, k, (cx, cy), False)
        dd.text((cx - 48, cy - 74), "%s %d" % (names[k], k), fill=(230, 210, 200), font=font)
    pics.append(("Dragonete Miudo: every frame (far, middle, near planes and the glow)", strip, 1))
    for g in ("Head", "Wing", "Tail"):
        pics.append(("gore: %s" % g.lower(), load("Content/Underworld/Gores/DragoneteMiudo_Gore%s.png" % g), 2))
    pics.append(("fire bolt, 4 frames", load("Content/Underworld/Projectiles/DragoneteFireBolt.png"), 3))
    for k in range(3):
        pair = Image.new("RGBA", (76, 52), (0, 0, 0, 0))
        pair.alpha_composite(glyph_image(k, 0.2), (0, 2))
        pair.alpha_composite(glyph_image(k, 1.0), (40, 2))
        pics.append(("rune glyph %d: dark, lit" % (k + 1), pair, 2))
    seal = Image.new("RGBA", (144, 104), (0, 0, 0, 0))
    seal.alpha_composite(seal_image((0.18, 0.18, 0.18)), (0, 0))
    seal.alpha_composite(seal_image((1.0, 1.0, 1.0)), (0, 56))
    pics.append(("the sealed gate: shut (no glyph), all three lit", seal, 2))
    bplanes = Planes("Content/Jungle/NPCs/RhinoBeetle", KB)
    strip = Image.new("RGBA", (6 * 124, 92), (40, 64, 44, 255))
    for j, k in enumerate((0, 9, 12, 16, 19, 24)):
        bplanes.draw(strip, k, (j * 124 + 62, 84), False)
    pics.append(("Rhino Beetle (jungle): the shell's vein now spore green", strip, 1))
    for name, path in (("Friendo-bot", "Content/Town/Friendobo.png"), ("shimmered", "Content/Town/Friendobo_Shimmer.png")):
        sh = load(path)
        row = Image.new("RGBA", (13 * 40, 2 * 56), (0, 0, 0, 0))
        for k in range(25):
            row.alpha_composite(sh.crop((0, k * 56, 40, k * 56 + 56)), ((k % 13) * 40, (k // 13) * 56))
        pics.append(("%s: the 25 frames (vanilla's layout)" % name, row, 2))
    pics.append(("map head", load("Content/Town/Friendobo_Head.png"), 3))
    pics.append(("shimmered head", load("Content/Town/Friendobo_Shimmer_Head.png"), 3))
    pics.append(("face emote, 2 frames", load("Content/Town/FriendoboEmote.png"), 3))
    cells = []
    for (label, im, s) in pics:
        big = im.resize((im.width * s, im.height * s), Image.NEAREST)
        cell = Image.new("RGBA", (max(big.width, 140) + 20, big.height + 40), (40, 44, 52, 255))
        cell.alpha_composite(big, ((cell.width - big.width) // 2, 8))
        ImageDraw.Draw(cell).text((8, cell.height - 24), label, fill=(238, 241, 243), font=font)
        cells.append(cell)
    WMAX = 1300
    rows, row, w = [], [], 0
    for c in cells:
        if w + c.width > WMAX and row:
            rows.append(row)
            row, w = [], 0
        row.append(c)
        w += c.width
    rows.append(row)
    H = sum(max(c.height for c in r) for r in rows)
    sheet = Image.new("RGBA", (WMAX, H), (24, 24, 30, 255))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            sheet.alpha_composite(c, (x, y))
            x += c.width
        y += max(c.height for c in r)
    sheet.convert("RGB").save(out)
    print("%s: %dx%d" % (out, sheet.width, sheet.height))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    random.seed(11)
    o = lambda name: os.path.join(args.out, name)   # noqa: E731
    jobs = [("ruins", lambda: ruins_png(o("2026-11-11_secrets-fundamental-ruins.png"), args.font)),
            ("gate", lambda: scene_gate(o("2026-11-11_secrets-ruins-glyphs-gate.gif"), args.font)),
            ("cutter", lambda: scene_cutter(o("2026-11-11_mechanist-diamond-cutter.gif"), args.font)),
            ("barrel", lambda: scene_barrel(o("2026-11-11_mechanist-barrel-gun.gif"), args.font)),
            ("dragonete", lambda: scene_dragonete(o("2026-11-11_underworld-dragonete-miudo.gif"), args.font)),
            ("beetle", lambda: scene_beetle(o("2026-11-11_jungle-rhino-beetle.gif"), args.font)),
            # 2026-11-24: the Friendo-bot became the Last Ghedalari (update_2026_11_24_sim.py --only ghedalari)
            ("items", lambda: items_png(o("2026-11-11_items-cutter-barrel-dragonete-glyphs.png"), args.font))]
    only = set(args.only.split(",")) if args.only else None
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
