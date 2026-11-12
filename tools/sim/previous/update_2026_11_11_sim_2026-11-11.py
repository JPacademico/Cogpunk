"""D5 proofs for the request of 2026-11-11, built from the real sprites and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_11_sim.py --out docs/media [--only ruins,shield,macuahuitl,beetle,drone,items]

Writes:
    2026-11-11_secrets-fundamental-ruins.png   FundamentalRuinsPass (the redesign) replayed on a cavern with a spider nest:
                                               the nest and the footprint; the ruins built in it (the left route marked:
                                               the entrance, three collapses of rubble, two shafts, the gallery, the pool,
                                               the arena's one door; the right entrance's dead end and its Water Chest; the
                                               unbreakable arena outlined); then the arena, the left route and the dead end
                                               closer.
    2026-11-11_secrets-stone-shield.gif        Westworld's stone sealed in its shield (the cursor names it sealed, a right
                                               click only says its guardian still lives); the Cursed Conductor falls (the
                                               world flag): the shield shatters; now a right click reads its runes.
    2026-11-11_weapon-macuahuitl.gif           the Macuahuitl swung like vanilla's swords (25 ticks a swing) at three
                                               training dummies: the first strike on each deals x2 (a crit on it x4), every
                                               later one plain.
    2026-11-11_ruins-rhino-beetle.gif          the Rhino Beetle in the ruins: it crawls up, braces (the telegraph) and
                                               charges; the ram tosses the player up; the next charge is jumped over and it
                                               skids; one into the wall leaves it dazed; the player climbs to a ledge out of
                                               reach: it takes off, flies over the player and drops.
    2026-11-11_scrap-delivery-drone.gif        the drone renamed the Delivery Drone (30 life, a 5 s scan): update_2026_11_10b_sim's
                                               scene, run with the new constants.
    2026-11-11_items-macuahuitl-ruins-beetle.png  the Macuahuitl, the ruins' darker blocks (with the new Ancient Brick and
                                               Rubble), the stone's shield frames, the Rhino Beetle's frames and gores, the
                                               drone's frames.

Leaves out: lighting (the glows are drawn at full strength), vanilla's own art (natural stone, the stone platforms, the
Water Chest, the dummies and the water are stand-ins), the planes' parallax, the player's exact physics (approximated as in
update_2026_11_03b_sim), defense (the numbers are the hits' own), netcode (the sim is the server and the owner). Numbers
are Expert's.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, consts, load, player_sprite, TPF  # noqa: E402
from update_2026_11_04_sim import STEAM  # noqa: E402
from update_2026_11_06b_sim import Planes, numbers, note  # noqa: E402
from update_2026_11_03b_sim import PLAYER_W, PLAYER_H, GRAVITY, JUMP_SPEED, JUMP_HOLD, IMMUNITY, overlaps  # noqa: E402
from update_2026_11_10_sim import faded, stone_image, westworld_crop, INSCRIPTIONS, lerp  # noqa: E402
from update_2026_11_10b_sim import additive, font_at, scene_drone  # noqa: E402
from terrain import load_frames  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
SEC = "Content/Secrets/"
RUIN = SEC + "Ruins/"
KR = consts(SEC + "Generation/FundamentalRuinsPass.cs", SEC + "FundamentalStoneTile.cs")
KS = consts(SEC + "FundamentalStoneTile.cs", SEC + "FundamentalStoneReading.cs")
KM = consts("Content/Junkyard/Weapons/Macuahuitl.cs")
KB = consts(RUIN + "NPCs/RhinoBeetle.cs", RUIN + "NPCs/RhinoBeetleRigData.cs")
EMBER, JADE, HIT, HURT, GLOW = (236, 113, 40), (96, 214, 150), (255, 199, 90), (255, 90, 70), (144, 168, 208)
ROUTE, PLUG, ARENA, DEAD = (255, 214, 90), (236, 90, 70), (110, 220, 255), (190, 150, 255)
AREA_SCALE, CORAL_SHARE = 1.41421356, 0.35                    # FundamentalRuinsPass's doubles (the parser reads int/float)


# ================================================================================================
# The Fundamental Ruins: FundamentalRuinsPass (2026-11-11) replayed
# ================================================================================================
STONE_T, BRICK_T, CORAL_T, RUNE_T = "stone", "brick", "coral", "rune"
ABRICK_T, ARUNE_T, RUBBLE_T, PLAT_T, KELP_T, OBJ_T, CHEST_T, WEB_T = "abrick", "arune", "rubble", "plat", "kelp", "obj", "chest", "web"
NEST_W, BRICK_W, COLUMN_W, CAVE_W = "nest", "brickw", "columnw", "cavew"
RUIN_BLOCKS = (BRICK_T, CORAL_T, RUNE_T, ABRICK_T, ARUNE_T, RUBBLE_T)        # RuinBlocks.Merge: one clump
SOLID = RUIN_BLOCKS + (STONE_T,)
OBJECTS = (KELP_T, OBJ_T, CHEST_T)                                           # Main.tileFrameImportant: a tunnel stops at them


class World:
    """A cavern sample: tiles (kind), walls, water, a spider nest (Spider Wall and cobwebs) in the middle."""

    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.rng = random.Random(seed)
        self.tile, self.wall, self.water = {}, {}, set()
        for x in range(w):
            for y in range(h):
                self.tile[(x, y)] = STONE_T
        for _ in range(14):                                   # winding caves: random walks of round brushes
            x, y = self.rng.uniform(0, w), self.rng.uniform(0, h)
            a = self.rng.uniform(0, 2 * math.pi)
            for _ in range(160):
                r = self.rng.uniform(2.0, 4.5)
                for dx in range(-5, 6):
                    for dy in range(-5, 6):
                        if dx * dx + dy * dy <= r * r:
                            self.dig(int(x + dx), int(y + dy), CAVE_W)
                a += self.rng.uniform(-0.5, 0.5)
                x, y = x + math.cos(a) * 1.6, y + math.sin(a) * 0.9
        cx, cy = w // 2 + 6, h // 2 - 4                          # the nest
        self.nest = set()
        for x in range(w):
            for y in range(h):
                u, v = (x - cx) / 31.0, (y - cy) / 21.0
                if u * u + v * v <= 1.0 + 0.18 * math.sin(x * 0.4) + 0.14 * math.cos(y * 0.5):
                    self.dig(x, y, NEST_W)
                    self.nest.add((x, y))
        for (x, y) in list(self.nest):
            if self.tile.get((x, y - 1)) == STONE_T and self.rng.random() < 0.35:
                self.tile[(x, y)] = WEB_T

    def dig(self, x, y, wall):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.tile.pop((x, y), None)
            self.wall[(x, y)] = wall


class Ruins:
    """FundamentalRuinsPass's build (2026-11-11), step for step, on a World (its rng stands in for WorldGen.genRand)."""

    def __init__(self, world, seed):
        self.wd, self.rng = world, random.Random(seed)
        xs = [x for (x, _) in world.nest]
        ys = [y for (_, y) in world.nest]
        self.nest_box = (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
        w = max(KR["MinWidth"], min(KR["MaxWidth"], int(round(self.nest_box[2] * AREA_SCALE))))
        h = max(KR["MinHeight"], min(KR["MaxHeight"], int(round(self.nest_box[3] * AREA_SCALE))))
        ncx, ncy = self.nest_box[0] + self.nest_box[2] // 2, self.nest_box[1] + self.nest_box[3] // 2
        self.area = (ncx - w // 2, ncy - h // 2, w, h)
        self.plugs, self.marks = [], {}
        self.stone_at = self.chest_at = None

    # --- cells ---
    def solid(self, x, y, kind):
        self.wd.tile[(x, y)] = kind
        self.wd.water.discard((x, y))

    def air(self, x, y, wall):
        self.wd.tile.pop((x, y), None)
        self.wd.water.discard((x, y))
        self.wd.wall[(x, y)] = wall

    def water(self, x, y, wall):
        self.air(x, y, wall)
        self.wd.water.add((x, y))

    def is_air(self, x, y):
        return (x, y) not in self.wd.tile

    def is_arena(self, x, y):
        return self.wd.tile.get((x, y)) in (ABRICK_T, ARUNE_T)

    def brick(self, x, y, kind):
        if not self.is_arena(x, y):
            self.solid(x, y, kind)

    def open(self, x, y):
        if not self.is_arena(x, y):
            self.air(x, y, BRICK_W)

    @staticmethod
    def noise(x, y):
        def hsh(a, b):
            return ((a * 73856093) ^ (b * 19349663) ^ (1234 * 83492791)) & 0x7FFFFFFF
        gx, gy = x // 4, y // 4
        fx, fy = x / 4.0 - gx, y / 4.0 - gy
        a, b, c, d = (hsh(gx, gy) % 1000 / 1000.0, hsh(gx + 1, gy) % 1000 / 1000.0, hsh(gx, gy + 1) % 1000 / 1000.0,
                      hsh(gx + 1, gy + 1) % 1000 / 1000.0)
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    def shell_block(self, x, y, outer):
        return CORAL_T if outer and self.noise(x, y) < CORAL_SHARE else BRICK_T

    # --- the build ---
    def build(self):
        ax, ay, aw, ah = self.area
        for p in list(self.wd.nest):                              # ClearNest: the nest's walls and webs go
            if self.wd.wall.get(p) == NEST_W:
                self.wd.wall[p] = None
            if self.wd.tile.get(p) == WEB_T:
                self.wd.tile.pop(p, None)
        for x in range(ax, ax + aw):                              # FillFootprint: its open spaces become stone
            for y in range(ay, ay + ah):
                self.wd.water.discard((x, y))
                if self.is_air(x, y):
                    self.wd.tile[(x, y)] = STONE_T
        self.half = max(KR["ArenaMinHalf"], min(KR["ArenaMaxHalf"], (aw - 2 * KR["SideMin"]) // 2 - KR["Shell"]))
        self.cx = ax + aw // 2
        self.fy = ay + ah - KR["FloorMargin"]
        self.build_arena()
        self.build_left()
        self.build_right()

    def inside(self, dx):
        u = (dx + 0.5) / (self.half + 0.5)
        if abs(u) > 1.0:
            return 0
        return max(KR["ArenaSide"], int(round(KR["ArenaTop"] * math.sqrt(1.0 - u * u))))

    def interior(self, dx, dy):
        return 1 <= dy <= self.inside(dx)

    def build_arena(self):
        cx, fy, half, shell = self.cx, self.fy, self.half, KR["Shell"]
        reach = half + shell
        for dx in range(-reach, reach):
            for dy in range(1 - KR["FloorDepth"], KR["ArenaTop"] + shell + 1):
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
                self.solid(x, y, ARUNE_T if face and dy >= 2 and (dx + dy) % KR["RuneEvery"] == 0 else ABRICK_T)
        self.arena = (cx - reach, fy - KR["ArenaTop"] - shell, 2 * reach, KR["ArenaTop"] + shell + KR["FloorDepth"])
        for c in (11, 22):                                         # ColumnX
            if c >= half - 1:
                continue
            for dy in range(1, self.inside(c) + 1):
                for dx in (c - 1, c, -c, -c - 1):
                    if self.interior(dx, dy):
                        self.wd.wall[(cx + dx, fy - dy)] = COLUMN_W
        for dy in range(1, KR["DoorHeight"] + 1):                  # its one door, on the left
            for k in range(shell):
                self.air(cx - half - 1 - k, fy - dy, BRICK_W)
        for side in (1, -1):
            start = KR["PuddleX"] - KR["PuddleWidth"] // 2 if side > 0 else -KR["PuddleX"] - KR["PuddleWidth"] // 2
            for k in range(KR["PuddleWidth"]):
                if abs(start + k) >= half - 1:
                    break
                self.water(cx + start + k, fy, BRICK_W)
        for step in range(1, KR["DaisSteps"] + 1):
            w = KR["DaisHalf"] + (KR["DaisSteps"] - step) * 2
            for dx in range(-w, w):
                self.solid(cx + dx, fy - step, ARUNE_T)
        floor_y = fy - KR["DaisSteps"]                             # FundamentalStones.TryPlace(Ruins, cx - 2, floorY)
        self.stone_at = (cx - 2, floor_y - int(KR["Height"]))
        for dx in range(int(KR["Width"])):
            for dy in range(int(KR["Height"])):
                self.wd.tile[(cx - 2 + dx, floor_y - int(KR["Height"]) + dy)] = OBJ_T
        self.platforms(KR["LowPlatformY"], KR["LowPlatformFrom"], min(KR["LowPlatformTo"], half - 3))
        self.platforms(KR["HighPlatformY"], KR["HighPlatformFrom"], KR["HighPlatformTo"])
        dx = -half + 2
        while dx < half - 2:
            if abs(dx + 0.5) >= 10:
                self.kelp(cx + dx, fy - self.inside(dx), self.rng.randint(KR["KelpMin"], KR["KelpMax"]))
            dx += self.rng.randint(3, 6)

    def platforms(self, dy, frm, to):
        for k in range(frm, to + 1):
            for dx in (k - 1, -k):
                if self.interior(dx, dy):
                    self.solid(self.cx + dx, self.fy - dy, PLAT_T)

    def kelp(self, x, y, length):
        if self.wd.tile.get((x, y - 1)) not in SOLID:
            return
        for k in range(length):
            if not self.is_air(x, y + k) or not self.is_air(x, y + k + 3):
                return
            if (x, y + k) not in self.wd.water:
                self.wd.tile[(x, y + k)] = KELP_T

    def corridor(self, x0, x1, floor, height, open_ends, puddle):
        a, b, ps = min(x0, x1), max(x0, x1), KR["PassShell"]
        for x in range(a - ps, b + ps + 1):
            end = x < a or x > b
            for y in range(floor - height - ps, floor + ps):
                inside = not end and floor - height <= y < floor
                if inside or (end and open_ends and floor - height <= y < floor):
                    self.open(x, y)
                    continue
                if self.is_air(x, y) and self.wd.wall.get((x, y)) == BRICK_W:
                    continue
                outer = y == floor - height - ps or y == floor + ps - 1 or x == a - ps or x == b + ps
                vault = y == floor - height - 1 and not end and (x - a) % KR["VaultRuneEvery"] == KR["VaultRuneEvery"] // 2
                self.brick(x, y, RUNE_T if vault else self.shell_block(x, y, outer))
        x = a + 2
        while x < b - 1:
            self.kelp(x, floor - height, self.rng.randint(KR["KelpMin"], max(KR["KelpMin"], min(KR["KelpMax"], height - 3))))
            x += KR["KelpEvery"] + self.rng.randint(0, 2)
        if puddle and b - a >= 10:
            w = self.rng.randint(2, 3)
            at = self.rng.randint(a + 3, b - w - 3)
            for k in range(w):
                if not self.is_arena(at + k, floor):
                    self.water(at + k, floor, BRICK_W)

    def shaft(self, x0, top, bottom, skip_a0, skip_a1, skip_b0, skip_b1):
        ps, sw = KR["PassShell"], KR["ShaftWidth"]
        for x in range(x0 - ps, x0 + sw + ps):
            for y in range(top, bottom + 1):
                if x0 <= x < x0 + sw:
                    self.open(x, y)
                elif not (self.is_air(x, y) and self.wd.wall.get((x, y)) == BRICK_W):
                    self.brick(x, y, self.shell_block(x, y, x == x0 - ps or x == x0 + sw + ps - 1))
        left = True
        y = bottom - KR["LedgeEvery"] + 1
        while y > top + 2:
            if not (skip_a0 <= y <= skip_a1 or skip_b0 <= y <= skip_b1):
                for k in range(KR["LedgeWidth"]):
                    self.brick(x0 + k if left else x0 + sw - 1 - k, y, BRICK_T)
                left = not left
            y -= KR["LedgeEvery"]

    def plug(self, x0, top, bottom):
        self.plugs.append((x0, top, bottom))
        for x in range(x0, x0 + KR["PlugWidth"]):
            for y in range(top, bottom + 1):
                if not self.is_arena(x, y):
                    self.solid(x, y, RUBBLE_T)

    def build_left(self):
        ax, ay, aw, ah = self.area
        ch, ps, sw = KR["CorridorHeight"], KR["PassShell"], KR["ShaftWidth"]
        left, door = ax, self.cx - self.half - KR["Shell"]
        ya, yg, fy = ay + KR["EntranceRow"], ay + KR["GalleryRow"], self.fy
        yb = (ya + fy) // 2
        s1 = door - 2 - ps - sw
        s2 = left + 1 + ps
        self.corridor(left, s1 + sw - 1, ya, ch, False, True)
        self.plug(left + (s1 - left) // 3, ya - ch, ya - 1)
        gallery_end = min(self.cx + self.half - 6, ax + aw - 1 - KR["SideMin"])
        self.corridor(s1, gallery_end, yg, ch, False, True)
        for x in range(gallery_end - 3, gallery_end + 1):
            for y in range(yg - ch, yg):
                self.solid(x, y, RUBBLE_T if (x + y) % 3 == 0 else STONE_T)
        self.shaft(s1, yg - ch, yb - 1, ya - ch, ya - 1, yb - ch, yb - 1)
        self.corridor(s1 + sw - 1, s2, yb, ch, False, False)
        mid = (s1 + s2) // 2
        self.plug(mid + 2, yb - ch, yb - 1)
        pool = max(s2 + sw + 1, mid - 2 - KR["PoolWidth"])
        x = pool
        while x < pool + KR["PoolWidth"] and x < mid + 2:
            for y in range(yb, yb + ps):
                self.water(x, y, BRICK_W)
            x += 1
        self.shaft(s2, yb - ch, fy - 1, yb - ch, yb - 1, fy - KR["DoorHeight"], fy - 1)
        self.corridor(s2, door - 1, fy, KR["DoorHeight"], False, True)
        self.plug(max(s2 + sw + 2, door - 1 - ps - KR["PlugWidth"] - 3), fy - KR["DoorHeight"], fy - 1)
        for y in range(fy - KR["DoorHeight"], fy):
            for x in range(door - ps, door):
                self.open(x, y)
        self.marks.update(entrance_l=(left, ya), shaft1=(s1 + sw // 2, (yg + yb) // 2), shaft2=(s2 + sw // 2, (yb + fy) // 2),
                          gallery=(gallery_end - 2, yg - ch // 2), pool=(pool + 2, yb), door=(door - 1, fy - 3),
                          route=[(left - 6, ya - 2), (s1 + 2, ya - 2), (s1 + 2, yb - 2), (s2 + 2, yb - 2), (s2 + 2, fy - 2),
                                 (door + 2, fy - 2), (self.cx - 2, fy - 4)])
        self.tunnel(left - 1, -1, ya)

    def build_right(self):
        """BuildRight: the red herring at the left way's levels, down to a dead end behind the arena's wall."""
        ax, ay, aw, ah = self.area
        ch, ps, sw, rh = KR["CorridorHeight"], KR["PassShell"], KR["ShaftWidth"], KR["RoomHeight"]
        right, fy = ax + aw - 1, self.fy
        wall = self.cx + self.half + KR["Shell"]
        ya = ay + KR["EntranceRow"]
        yb = (ya + fy) // 2
        u1 = wall + 2 + ps
        u2 = right - ps - sw + 1
        room0, room1 = wall, wall + KR["RoomWidth"] - 1
        for x in range(room0 - ps, room1 + ps + 1):
            for y in range(fy - rh - ps, fy + ps):
                if room0 <= x <= room1 and fy - rh <= y < fy:
                    self.open(x, y)
                else:
                    outer = y == fy - rh - ps or y == fy + ps - 1 or x == room1 + ps
                    self.brick(x, y, self.shell_block(x, y, outer))
        self.corridor(u1, right, ya, ch, False, True)
        self.shaft(u1, ya - ch, yb - 1, ya - ch, ya - 1, yb - ch, yb - 1)
        self.corridor(u1, u2 + sw - 1, yb, ch, False, True)
        self.shaft(u2, yb - ch, fy - 1, yb - ch, yb - 1, fy - ch, fy - 1)
        self.corridor(room1 + 1, u2 + sw - 1, fy, ch, False, True)
        for x in range(room1 + 1, room1 + ps + 1):
            for y in range(fy - ch, fy):
                self.open(x, y)
        for _ in range(2):
            self.kelp(self.rng.randint(room0 + 2, room1 - 2), fy - rh, self.rng.randint(KR["KelpMin"], KR["KelpMax"] - 1))
        self.water(room1 - 2, fy, BRICK_W)
        self.water(room1 - 1, fy, BRICK_W)
        cx0, cy0 = room0 + 3, fy - 1                               # AddBuriedChest(x + 1, y - 1): the chest at (x, y - 1)..
        self.chest_at = (cx0, cy0 - 1)
        for dx in range(2):
            for dy in range(2):
                self.wd.tile[(cx0 + dx, cy0 - 1 + dy)] = CHEST_T
        self.marks.update(entrance_r=(right, ya), room=(room0, fy - rh, room1, fy), wall=wall,
                          route_r=[(right + 6, ya - 2), (u1 + 2, ya - 2), (u1 + 2, yb - 2), (u2 + 2, yb - 2), (u2 + 2, fy - 2),
                                   (room0 + 4, fy - 2)])
        self.tunnel(right + 1, 1, ya)

    def tunnel(self, x, d, floor):
        for step in range(KR["TunnelMax"]):
            col = x + d * step
            if not (2 <= col < self.wd.w - 2):
                return
            if step > 2 and all(self.is_air(col, floor - k) for k in (1, 2, 3)):
                return
            if any(self.wd.tile.get((col, y)) in OBJECTS for y in range(floor - KR["TunnelHeight"], floor)):
                return
            for y in range(floor - KR["TunnelHeight"], floor):
                self.wd.tile.pop((col, y), None)


# --- rendering ------------------------------------------------------------------------------------------------------------
WALL_LOOKUP = {0: ((9, 3), (10, 3), (11, 3)), 1: ((6, 3), (7, 3), (8, 3)), 2: ((12, 0), (12, 1), (12, 2)), 3: ((1, 4), (3, 4), (5, 4)),
               4: ((9, 0), (9, 1), (9, 2)), 5: ((0, 4), (2, 4), (4, 4)), 6: ((6, 4), (7, 4), (8, 4)), 7: ((1, 2), (2, 2), (3, 2)),
               8: ((6, 0), (7, 0), (8, 0)), 9: ((5, 0), (5, 1), (5, 2)), 10: ((1, 3), (3, 3), (5, 3)), 11: ((4, 0), (4, 1), (4, 2)),
               12: ((0, 3), (2, 3), (4, 3)), 13: ((0, 0), (0, 1), (0, 2)), 14: ((1, 0), (2, 0), (3, 0)), 15: ((1, 1), (2, 1), (3, 1)),
               16: ((6, 1), (7, 1), (8, 1)), 17: ((6, 2), (7, 2), (8, 2)), 18: ((10, 0), (10, 1), (10, 2)), 19: ((11, 0), (11, 1), (11, 2))}
CENTRE = [[2, 0, 0], [0, 1, 4], [0, 3, 0]]
_SHEETS = {}


def stand_in_stone():
    """Natural stone (vanilla's art isn't in the repo): a grey block sheet in the terrain layout, flat with a few flecks."""
    sheet = Image.new("RGBA", (288, 270), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    rng = random.Random(5)
    for fx in range(16):
        for fy in range(15):
            x0, y0 = fx * 18, fy * 18
            d.rectangle([x0, y0, x0 + 15, y0 + 15], fill=(84, 82, 90, 255))
            for _ in range(5):
                px, py = x0 + rng.randrange(1, 14), y0 + rng.randrange(1, 14)
                d.rectangle([px, py, px + 1, py + 1], fill=(68, 66, 76, 255) if rng.random() < 0.5 else (102, 100, 110, 255))
    return sheet


def sheets():
    if not _SHEETS:
        _SHEETS.update(
            frames=load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json")),
            tiles={BRICK_T: load(RUIN + "Tiles/FundamentalBrickTile.png"), CORAL_T: load(RUIN + "Tiles/FundamentalCoralTile.png"),
                   RUNE_T: load(RUIN + "Tiles/FundamentalRuneTile.png"), ABRICK_T: load(RUIN + "Tiles/FundamentalArenaBrickTile.png"),
                   ARUNE_T: load(RUIN + "Tiles/FundamentalRuneTile.png"), RUBBLE_T: load(RUIN + "Tiles/FundamentalRubbleTile.png"),
                   STONE_T: stand_in_stone()},
            glows={RUNE_T: load(RUIN + "Tiles/FundamentalRuneTile_Glow.png"), ARUNE_T: load(RUIN + "Tiles/FundamentalRuneTile_Glow.png")},
            walls={BRICK_W: load(RUIN + "Walls/FundamentalBrickWallTile.png"), COLUMN_W: load(RUIN + "Walls/FundamentalColumnWallTile.png")},
            kelp=load(RUIN + "Tiles/FundamentalKelpTile.png"),
            shield=load(SEC + "FundamentalShield.png"))
    return _SHEETS


def shield_frame(k):
    sh = sheets()["shield"]
    w, h, gap = int(KS["ShieldW"]), int(KS["ShieldH"]), int(KS["ShieldGap"])
    return sh.crop((0, k * (h + gap), w, k * (h + gap) + h))


def render(world, x0, y0, x1, y1, stone_at=None, stone_style=2, shield=0.0, shield_k=0, seed=7):
    """The world's cells x0..x1, y0..y1 at 1:1 (16 px a tile), framed as the game frames them; the stone with its shield
    added at `shield` opacity (FundamentalStoneTile.SpecialDraw)."""
    S = sheets()
    W, H = (x1 - x0 + 1) * 16, (y1 - y0 + 1) * 16
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([0, y, W, y], fill=(int(22 + 10 * t), int(22 + 8 * t), int(30 + 8 * t), 255))
    rng = random.Random(seed)

    def px(x, y):
        return (x - x0) * 16, (y - y0) * 16
    for (x, y), kind in world.wall.items():
        if not (x0 <= x <= x1 and y0 <= y <= y1) or kind is None:
            continue
        X, Y = px(x, y)
        if kind in (CAVE_W, NEST_W):
            d.rectangle([X, Y, X + 15, Y + 15], fill=(44, 40, 48, 255) if kind == CAVE_W else (80, 64, 56, 255))
            if kind == NEST_W:
                d.line([X, Y, X + 15, Y + 15], fill=(112, 94, 84, 255))
            continue
        has = lambda ax, ay: world.wall.get((ax, ay)) in (BRICK_W, COLUMN_W) if kind == BRICK_W else world.wall.get((ax, ay)) == kind  # noqa: E731
        st = (1 if has(x, y - 1) else 0) | (2 if has(x - 1, y) else 0) | (4 if has(x + 1, y) else 0) | (8 if has(x, y + 1) else 0)
        if st == 15:
            st += CENTRE[x % 3][y % 3]
        fx, fy = WALL_LOOKUP[st][rng.randrange(3)]
        img.alpha_composite(S["walls"][kind].crop((fx * 36, fy * 36, fx * 36 + 32, fy * 36 + 32)), (X - 8, Y - 8))
    for (x, y) in world.water:
        if x0 <= x <= x1 and y0 <= y <= y1:
            X, Y = px(x, y)
            d.rectangle([X, Y + 2, X + 15, Y + 15], fill=(40, 84, 160, 255))
            d.line([X, Y + 2, X + 15, Y + 2], fill=(100, 150, 214, 255), width=2)
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (x, y), kind in world.tile.items():
        if not (x0 <= x <= x1 and y0 <= y <= y1) or kind not in S["tiles"]:
            continue
        X, Y = px(x, y)
        group = RUIN_BLOCKS if kind in RUIN_BLOCKS else (kind,)
        sig = "".join("-" if world.tile.get((x + dx, y + dy)) in group else "o" for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
        fx, fy = rng.choice(S["frames"][sig])
        img.alpha_composite(S["tiles"][kind].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (X, Y))
        if kind in S["glows"]:
            glow_layer.alpha_composite(S["glows"][kind].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (X, Y))
    chest_drawn = set()
    for (x, y), kind in world.tile.items():
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        X, Y = px(x, y)
        if kind == KELP_T:
            tip = world.tile.get((x, y + 1)) != KELP_T
            img.alpha_composite(S["kelp"].crop((x % 3 * 18, (18 if tip else 0), x % 3 * 18 + 16, (18 if tip else 0) + 16)), (X, Y))
        elif kind == PLAT_T:                                          # a stand-in for vanilla's Stone Platform
            d.rectangle([X, Y, X + 15, Y + 7], fill=(112, 112, 120, 255))
            d.line([X, Y, X + 15, Y], fill=(150, 150, 158, 255))
            d.line([X, Y + 7, X + 15, Y + 7], fill=(70, 70, 80, 255))
        elif kind == WEB_T:
            d.line([X, Y, X + 15, Y + 15], fill=(220, 220, 230, 160))
            d.line([X + 15, Y, X, Y + 15], fill=(220, 220, 230, 160))
        elif kind == CHEST_T and world.tile.get((x - 1, y)) != CHEST_T and world.tile.get((x, y - 1)) != CHEST_T and (x, y) not in chest_drawn:
            chest_drawn.add((x, y))                                   # a stand-in for vanilla's Water Chest
            d.rectangle([X + 1, Y + 6, X + 30, Y + 31], fill=(58, 92, 150, 255), outline=(24, 34, 62, 255))
            d.rectangle([X + 1, Y + 4, X + 30, Y + 13], fill=(84, 124, 186, 255), outline=(24, 34, 62, 255))
            d.rectangle([X + 13, Y + 11, X + 18, Y + 18], fill=(236, 196, 90, 255), outline=(120, 80, 30, 255))
    if stone_at and x0 <= stone_at[0] <= x1 and y0 <= stone_at[1] <= y1:
        sx, sy = px(*stone_at)
        img.alpha_composite(stone_image(stone_style, 1.0), (sx, sy))
        if shield > 0:
            additive(img, shield_frame(shield_k), (sx - KS["ShieldStoneX"], sy - KS["ShieldStoneY"]), shield)
    additive(img, glow_layer, (0, 0), 0.9)
    return img


def ruins_png(out, font_path):
    world = World(260, 120, seed=11)
    ruins = Ruins(world, seed=3)
    before = render(world, 0, 0, world.w - 1, world.h - 1)
    ruins.build()
    after = render(world, 0, 0, world.w - 1, world.h - 1, ruins.stone_at, shield=KS["ShieldOpacity"])
    font, big = font_at(font_path, 15), font_at(font_path, 22)
    third = lambda im: im.resize((im.width // 3, im.height // 3), Image.NEAREST)  # noqa: E731
    small_b, small_a = third(before), third(after)
    t = 16 / 3.0
    ax, ay, aw, ah = ruins.area
    for im in (small_b, small_a):
        d = ImageDraw.Draw(im)
        nx, ny, nw, nh = ruins.nest_box
        d.rectangle([nx * t, ny * t, (nx + nw) * t, (ny + nh) * t], outline=(230, 60, 60, 255), width=2)
        d.rectangle([ax * t, ay * t, (ax + aw) * t, (ay + ah) * t], outline=(240, 210, 80, 255), width=2)
    d = ImageDraw.Draw(small_a)
    rx, ry, rw, rh = ruins.arena
    d.rectangle([rx * t, ry * t, (rx + rw) * t, (ry + rh) * t], outline=ARENA + (255,), width=2)
    pts = [(x * t + t / 2, y * t + t / 2) for (x, y) in ruins.marks["route"]]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=ROUTE + (255,), width=2)
    for k, (x0, top, bottom) in enumerate(ruins.plugs):
        d.rectangle([x0 * t - 2, top * t - 2, (x0 + KR["PlugWidth"]) * t + 2, (bottom + 1) * t + 2], outline=PLUG + (255,), width=2)
    r0, rt, r1, rb = ruins.marks["room"]
    d.rectangle([r0 * t, rt * t, (r1 + 1) * t, rb * t], outline=DEAD + (255,), width=2)
    pts = [(x * t + t / 2, y * t + t / 2) for (x, y) in ruins.marks["route_r"]]
    for p0, p1 in zip(pts, pts[1:]):
        d.line([p0, p1], fill=DEAD + (255,), width=2)
    gif = Gif(font_path, (10, 10))

    def label(im, xy, s, col):
        gif.text(im, (int(xy[0]), int(xy[1])), s, fill=col, font=font)
    m = ruins.marks
    label(small_a, (m["entrance_l"][0] * t - 120, m["entrance_l"][1] * t - 40), "left entrance", ROUTE)
    label(small_a, (m["entrance_r"][0] * t - 40, m["entrance_r"][1] * t - 46), "right entrance", DEAD)
    for k, (x0, top, bottom) in enumerate(ruins.plugs):
        label(small_a, (x0 * t - 10, (bottom + 1) * t + 4), "rubble %d" % (k + 1), PLUG)
    label(small_a, (m["gallery"][0] * t - 150, m["gallery"][1] * t - 30), "gallery: its vault fell in", ROUTE)
    label(small_a, (m["shaft1"][0] * t + 14, m["shaft1"][1] * t), "shaft 1", ROUTE)
    label(small_a, (m["shaft2"][0] * t - 64, m["shaft2"][1] * t), "shaft 2", ROUTE)
    label(small_a, (m["pool"][0] * t - 30, m["pool"][1] * t + 14), "pool", ROUTE)
    label(small_a, (rx * t + 30, ry * t - 22), "arena: unbreakable Ancient Brick, one door", ARENA)
    label(small_a, (r0 * t - 30, rb * t + 10), "dead end behind the arena's wall: Water Chest", DEAD)
    # closer views
    cx, fy, half = ruins.cx, ruins.fy, ruins.half
    arena_img = render(world, cx - half - 6, fy - KR["ArenaTop"] - 5, cx + half + 5, fy + 4, ruins.stone_at, shield=KS["ShieldOpacity"])
    arena_img = arena_img.resize((arena_img.width * 2 // 3, arena_img.height * 2 // 3), Image.NEAREST)
    lx0, ly0 = ax - 10, ay - 2
    left_img = render(world, lx0, ly0, cx - half + 2, fy + 4)
    left_img = left_img.resize((left_img.width // 2, left_img.height // 2), Image.NEAREST)
    dd = ImageDraw.Draw(left_img)
    for k, (x0, top, bottom) in enumerate(ruins.plugs):
        dd.rectangle([(x0 - lx0) * 8 - 2, (top - ly0) * 8 - 2, (x0 + KR["PlugWidth"] - lx0) * 8 + 2, (bottom + 1 - ly0) * 8 + 2],
                     outline=PLUG + (255,), width=2)
        label(left_img, ((x0 - lx0) * 8 - 6, (bottom + 1 - ly0) * 8 + 4), "rubble %d" % (k + 1), PLUG)
    rx0 = ruins.marks["wall"] - 6
    right_img = render(world, rx0, ly0, ax + aw + 8, fy + 4)
    right_img = right_img.resize((right_img.width // 2, right_img.height // 2), Image.NEAREST)
    r0, rt, r1, rb = ruins.marks["room"]
    dd = ImageDraw.Draw(right_img)
    dd.rectangle([(r0 - rx0) * 8 - 2, (rt - ly0) * 8 - 2, (r1 + 1 - rx0) * 8 + 2, (rb - ly0) * 8 + 2], outline=DEAD + (255,), width=2)
    W = max(small_a.width, arena_img.width, left_img.width + 10 + right_img.width)
    parts = [("Fundamental Ruins, redesigned (FundamentalRuinsPass replayed on a cavern with a spider nest)", None, big),
             ("before: the spider nest (red box) and the ruins' footprint (yellow): %dx%d tiles, %.1fx the nest's box (%dx%d), "
              "filled solid before the ruins are carved (1/3 scale)" % (aw, ah, aw * ah / float(ruins.nest_box[2] * ruins.nest_box[3]),
                                                                       ruins.nest_box[2], ruins.nest_box[3]), small_b, font),
             ("after: the left way in (yellow): corridor, rubble 1, shaft 1 down (it climbs to the gallery too), corridor west, "
              "rubble 2, the pool, shaft 2, rubble 3, the arena's door", small_a, font),
             ("the right way in (violet): corridor, shaft, corridor back, shaft, corridor into a dead end behind the arena's wall "
              "(a Water Chest); the arena (cyan): one door, unbreakable walls", None, font)]
    rows = []
    for text, im, f in parts:
        rows.append(("text", text, f))
        if im is not None:
            rows.append(("img", im, None))
    rows.append(("text", "the arena (2/3 scale): the third Fundamental Stone on its rune-brick dais in its shield (sealed until the "
                 "ruins' boss falls; none yet), stone platforms, puddles, kelp", font))
    rows.append(("img", arena_img, None))
    rows.append(("text", "1/2 scale: the left route, its three collapses of Rubble (any pickaxe, a little slower than stone; they drop "
                 "Fundamental Bricks); the right route and its dead end (violet)", font))
    rows.append(("pair", (left_img, right_img), None))
    Htot = sum(34 if r[0] == "text" else ((r[1].height if r[0] == "img" else max(r[1][0].height, r[1][1].height)) + 8) for r in rows) + 20
    sheet = Image.new("RGBA", (W + 20, Htot), (20, 20, 26, 255))
    y = 10
    for kind, v, f in rows:
        if kind == "text":
            gif.text(sheet, (12, y), v, font=f)
            y += 34
        elif kind == "img":
            sheet.alpha_composite(v, (10, y))
            y += v.height + 8
        else:
            sheet.alpha_composite(v[0], (10, y))
            sheet.alpha_composite(v[1], (20 + v[0].width, y))
            y += max(v[0].height, v[1].height) + 8
    sheet.convert("RGB").save(out)
    print("%s: %dx%d; footprint %dx%d, arena half %d (%d wide), floor row %d, plugs %s, chest %s, stone %s"
          % (out, sheet.width, sheet.height, aw, ah, half, ruins.arena[2], fy, ruins.plugs, ruins.chest_at, ruins.stone_at))


# ================================================================================================
# The stone's shield: sealed, the guardian falls, it shatters, the stone reads
# ================================================================================================
class Motes:
    """PurificationPowder dust stand-ins: pale blue points, no gravity, slowing, fading."""

    def __init__(self):
        self.items = []

    def add(self, x, y, vx, vy, life, size=2):
        self.items.append([x, y, vx, vy, life, life, size])

    def step(self):
        for m in self.items:
            m[0] += m[2]
            m[1] += m[3]
            m[2] *= 0.94
            m[3] *= 0.94
            m[4] -= 1
        self.items = [m for m in self.items if m[4] > 0]

    def draw(self, img):
        d = ImageDraw.Draw(img)
        for (x, y, _, _, life, full, s) in self.items:
            a = life / float(full)
            col = (int(150 + 100 * a), int(200 + 50 * a), 255, 255)
            d.rectangle([x, y, x + s - 1, y + s - 1], fill=col)


def chat_line(gif, img, s, H, col=(255, 240, 200)):
    gif.text(img, (12, H - 30), s, fill=col)


def scene_shield(out, font):
    west, at, _ = westworld_crop(margin=(30, 14))
    W, H = west.width, west.height
    gif = Gif(font, (W, H), scale=1.0)
    runes = load(SEC + "FundamentalRunes.png")
    sx, sy = at
    floor = sy + 96
    anchor = (sx + 32, sy)
    centre = (sx + 32, sy + 48)
    px = float(W - 60)
    line = INSCRIPTIONS[1]
    motes = Motes()
    rng = random.Random(4)
    sealed = True
    opened, age, closing = None, 0, 0
    DOWN = 230                                                # the Cursed Conductor falls (CursedConductorSystem.Downed)
    notes = [(0, "Westworld's stone, sealed: a shield over it (not a wall: it just can't be used yet)"),
             (60, "the cursor names it sealed; a right click only says why"),
             (DOWN, "the Cursed Conductor is defeated (a world flag, synced to every client)..."),
             (DOWN + 12, "...the shield shatters for good; now the stone can be read"),
             (DOWN + 110, "a right click lights its runes (the 2026-11-10 reading)")]
    said = None
    for tick in range(560):
        if tick < 50:
            px -= 1.6
        elif tick > 470:
            px += 2.4
        if tick == 100:
            said = (tick, "A primordial shield hums around the stone. Its guardian still lives.")
        if tick == DOWN:
            sealed = False
            for _ in range(40):                                # FundamentalStoneTile.Shatter: 40 motes outward
                x, y = centre[0] - 40 + rng.random() * 80, centre[1] - 56 + rng.random() * 112
                dx, dy = x - centre[0], y - centre[1]
                n = math.hypot(dx, dy) or 1.0
                v = rng.uniform(2.0, 5.0)
                motes.add(x, y, dx / n * v, dy / n * v, rng.randint(30, 50), 3)
        if sealed and rng.random() < 1 / 12.0:               # EmitParticles: a mote now and then
            motes.add(sx - 16 + rng.random() * 96, sy - 24 + rng.random() * 104, 0.0, -0.6, 50)
        if tick == DOWN + 120:
            opened, age, closing = True, 0, 0
        if opened:
            age += 1
            if closing == 0 and age >= KS["HoldTicks"]:
                closing = 1
            if closing > 0:
                closing += 1
                if closing > KS["FadeOutTicks"]:
                    opened = None
        motes.step()
        if tick % TPF:
            continue
        breath = 0.85 + 0.15 * math.sin(tick / 60.0 * 1.57 + 1.3)
        img = west.copy()
        img.alpha_composite(stone_image(1, breath), (sx, sy))
        if sealed:
            pulse = 0.8 + 0.2 * math.sin(tick / 60.0 * 2.4 + sx / 16 * 0.31)
            k = (tick // int(KS["ShieldFrameTicks"])) % int(KS["ShieldFrames"])
            additive(img, shield_frame(k), (sx - KS["ShieldStoneX"], sy - KS["ShieldStoneY"]), KS["ShieldOpacity"] * pulse)
        motes.draw(img)
        img.alpha_composite(player_sprite(flip=True), (int(px - 20), int(floor - 56)))
        hover = (60 <= tick < 104) or (DOWN + 80 <= tick < DOWN + 122)
        if hover:
            cx, cy = anchor[0] + 6, anchor[1] + 40
            d = ImageDraw.Draw(img)
            d.polygon([(cx, cy), (cx + 10, cy + 12), (cx + 4, cy + 12), (cx, cy + 18)], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255))
            gif.text(img, (int(cx + 14), int(cy + 14)), "Fundamental Stone (sealed: its guardian still lives)" if sealed else "Fundamental Stone")
        if said and tick - said[0] < 120:
            chat_line(gif, img, said[1], H)
        if opened:
            alpha = min(1.0, age / KS["FadeInTicks"]) * (1.0 - closing / KS["FadeOutTicks"] if closing else 1.0)
            n = len(line)
            gw, gh, gap, pad = 14, 18, 4, 12
            pw, ph = n * gw + (n - 1) * gap + 2 * pad, gh + 2 * pad
            x0, y0 = int(anchor[0] - pw / 2), int(anchor[1] - 10 - ph)
            panel = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            pd = ImageDraw.Draw(panel)
            pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=6, fill=(14, 20, 46, int(230 * alpha)), outline=(60, 76, 130, int(230 * alpha)), width=2)
            img.alpha_composite(panel, (x0, y0))
            for k, g in enumerate(line):
                shown = (age - KS["FadeInTicks"] / 2 - k * KS["RevealTicks"]) / KS["RevealTicks"]
                if shown <= 0:
                    break
                img.alpha_composite(faded(runes.crop((g * 16, 0, g * 16 + gw, gh)), alpha * min(1.0, shown)), (x0 + pad + k * (gw + gap), y0 + pad))
        gif.text(img, (W - 260, 34), "shield: %s" % ("SEALED (Conductor alive)" if sealed else "gone (Conductor defeated)"),
                 fill=GLOW if sealed else JADE)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Macuahuitl: vanilla's swing, the first cut
# ================================================================================================
def flat_backdrop(w, h, ground, seed=3):
    """A dark cavern over a floor of Fundamental Brick (the real tile, framed)."""
    S = sheets()
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([0, y, w, y], fill=(int(30 + 12 * t), int(30 + 10 * t), int(40 + 8 * t), 255))
    rng = random.Random(seed)
    for x in range(0, w, 16):
        for y in range(ground, h, 16):
            sig = ("o" if y == ground else "-") + "---"
            fx, fy = rng.choice(S["frames"][sig])
            img.alpha_composite(S["tiles"][BRICK_T].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (x, y))
    return img


def dummy(img, x, ground, hit):
    """A stand-in for vanilla's Target Dummy: a straw sack on a post (it wobbles when hit)."""
    d = ImageDraw.Draw(img)
    lean = 3 if hit else 0
    d.rectangle([x - 2, ground - 22, x + 2, ground - 1], fill=(110, 76, 44, 255))
    d.rounded_rectangle([x - 12 + lean, ground - 48, x + 12 + lean, ground - 20], radius=6, fill=(196, 160, 104, 255), outline=(98, 70, 40, 255), width=2)
    d.ellipse([x - 8 + lean, ground - 62, x + 8 + lean, ground - 46], fill=(214, 182, 120, 255), outline=(98, 70, 40, 255), width=2)
    d.line([x - 12 + lean, ground - 36, x + 12 + lean, ground - 36], fill=(140, 40, 40, 255), width=3)


def macuahuitl_hand(cx, top, done):
    """Player.ItemCheck_ApplyUseStyle, useStyle 1 (Swing) facing right, for a 68 px frame: where the sprite's corner sits by
    the swing's third, and itemRotation."""
    anim = 1.0 - done                                         # itemAnimation / itemAnimationMax: 1 -> 0
    if anim < 0.333:
        loc = (cx + 6, top + 24)
    elif anim < 0.666:
        loc = (cx + 6, top + 14)
    else:
        loc = (cx - 6, top + 14)
    rot = (anim - 0.5) * -3.5 - 0.3
    return loc, rot


def scene_macuahuitl(out, font):
    W, H, G = 860, 300, 262
    bg = flat_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    club = load("Content/Junkyard/Weapons/Macuahuitl.png")
    size = club.width
    use = int(KM["UseTime"])
    dmg, mult = int(KM["Damage"]), int(KM["FirstHitMultiplier"])
    px = 90.0
    dummies = [{"x": 230.0, "struck": False, "hit": 0, "swings": 4}, {"x": 470.0, "struck": False, "hit": 0, "swings": 3},
               {"x": 710.0, "struck": False, "hit": 0, "swings": 4}]
    crits = {(1, 0), (2, 2)}                                   # (dummy, its hit number): crits for the demo (12% in game)
    pops, hits_on = [], [0, 0, 0]
    notes = [(0, "Macuahuitl: %d a hit, %d ticks a swing (%.1f a second), %d%% crit (%d%% + the player's 4%%), swung like vanilla's swords"
              % (dmg, use, 60.0 / use, KM["CritBonus"] + 4, KM["CritBonus"]))]
    target, swing_t, swings_left, struck_this = 0, 0, 0, set()
    loc, rot = (px, G - 30), 0.0
    for tick in range(720):
        if swing_t == 0 and target < 3:
            goal = dummies[target]["x"] - 52
            if abs(goal - px) > 1.0:
                px += math.copysign(min(2.0, abs(goal - px)), goal - px)
            else:
                if swings_left == 0:
                    swings_left = dummies[target]["swings"]
                swing_t, struck_this = use, set()               # autoReuse: the next swing at once
                swings_left -= 1
        if swing_t > 0:
            done = 1.0 - swing_t / float(use)
            loc, rot = macuahuitl_hand(px, G - PLAYER_H, done)
            ang = rot - math.pi / 4                            # the club points along the sprite's diagonal
            reach = size * 1.3
            for i, dm in enumerate(dummies):
                box = (dm["x"] - 14, G - 62, dm["x"] + 14, G)
                hit = any(box[0] <= loc[0] + math.cos(ang) * reach * u <= box[2] and box[1] <= loc[1] + math.sin(ang) * reach * u <= box[3]
                          for u in (0.3, 0.45, 0.6, 0.75, 0.9))
                if hit and i not in struck_this:                # one hit per enemy a swing (vanilla's per-swing immunity)
                    struck_this.add(i)
                    first = not dm["struck"]
                    dm["struck"] = True
                    crit = (i, hits_on[i]) in crits
                    hits_on[i] += 1
                    n = dmg * (mult if first else 1) * (2 if crit else 1)
                    tag = ("  FIRST CUT x%d" % (mult * (2 if crit else 1))) if first else ""
                    pops.append((tick, dm["x"] - 30, G - 110, "%d%s%s" % (n, "!" if crit else "", tag), EMBER if first else (HIT if crit else STEAM)))
                    dm["hit"] = 8
                    if first and i == 0:
                        notes.append((tick, "the first strike on each enemy cuts deep: x%d (%d)" % (mult, dmg * mult)))
                    elif first and crit:
                        notes.append((tick, "a crit on the first strike: x%d (%d)" % (mult * 2, dmg * mult * 2)))
                    elif hits_on[i] == 2 and i == 0:
                        notes.append((tick, "every later strike on it is plain: %d (%d with a crit)" % (dmg, dmg * 2)))
            swing_t -= 1
            if swing_t == 0 and swings_left == 0:
                target += 1
        for dm in dummies:
            dm["hit"] = max(0, dm["hit"] - 1)
        if tick % TPF:
            continue
        img = bg.copy()
        for dm in dummies:
            dummy(img, int(dm["x"]), G, dm["hit"] > 0)
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        if swing_t > 0:
            r = int(math.hypot(size, size)) + 4
            pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
            pad.alpha_composite(club, (r, r - size))           # the sprite's bottom-left corner on the pivot
            img.alpha_composite(pad.rotate(-math.degrees(rot), resample=Image.NEAREST), (int(loc[0] - r), int(loc[1] - r)))
        numbers(gif, img, pops, tick)
        gif.text(img, (W - 330, 34), "hits:  " + "   ".join("dummy %d: %d" % (i + 1, hits_on[i]) for i in range(3)), fill=STEAM)
        note(gif, img, notes, tick)
        gif.push(img)
        if target >= 3 and tick > 40 and all(t0 + 45 < tick for (t0, *_r) in pops[-1:]):
            break
    gif.save(out)


# ================================================================================================
# The Rhino Beetle
# ================================================================================================
OBSTACLES = ((96, 160, 4 * 16), (820, 868, 4 * 16), (900, 1100, 7 * 16))   # (x from, x to, height): a step each way, the ledge
# (x from, x to, height in px, solid): a stone platform 4 tiles up (one-way: walked under, jumped through, stood on) and
# the ledge, 7 tiles up: out of a jump's reach
OBSTACLES = ((790, 862, 4 * 16, False), (900, 1100, 7 * 16, True))
LEDGE_X, LEDGE_UP = 900, 7 * 16


def ground_at(x, feet, G):
    """The floor under x for something whose feet are at `feet` (tops are one-way: you stand on what you are over)."""
    best = G
    for (a, b, up, _) in OBSTACLES:
        if a <= x < b and feet <= G - up + 1:
            best = min(best, G - up)
    return best


def blocked(x0, x1, half, feet, G):
    """Moving from x0 to x1 (centres) with this half-width and feet: where a solid face stops it, or None."""
    for (a, b, up, solid) in OBSTACLES:
        if not solid or feet <= G - up + 1:
            continue
        if x0 + half <= a < x1 + half:                         # running right into its left face
            return a - half
        if x1 - half < b <= x0 - half:                         # running left into its right face
            return b + half
    return None


class Runner:
    """The scripted player: vanilla-ish run, jump, gravity; hurt knockback (decompiled Player.Hurt) and the beetle's toss
    applied the tick after (RhinoTossPlayer.PreUpdateMovement)."""

    def __init__(self, x, G):
        self.x, self.y, self.vx, self.vy = float(x), float(G), 0.0, 0.0
        self.G, self.hold, self.immune, self.run, self.toss = G, 0, 0, 0, 0.0
        self.face = -1

    def box(self):
        return (self.x - PLAYER_W / 2, self.y - PLAYER_H, self.x + PLAYER_W / 2, self.y)

    def grounded(self):
        return self.vy == 0.0 and self.y >= ground_at(self.x, self.y, self.G) - 0.01

    def jump(self):
        if self.grounded():
            self.vy, self.hold = -JUMP_SPEED, JUMP_HOLD

    def step(self):
        if self.toss > 0:
            self.vy = min(self.vy, -self.toss)
            self.toss = 0.0
        on = self.grounded()
        if self.run:
            self.vx = max(-3.0, min(3.0, self.vx + 0.12 * self.run))
            self.face = self.run
        else:
            slow = 0.2 if on else 0.06
            self.vx = 0.0 if abs(self.vx) <= slow else self.vx - math.copysign(slow, self.vx)
        if self.hold > 0:
            self.hold -= 1
            self.vy = -JUMP_SPEED
        else:
            self.vy = min(10.0, self.vy + GRAVITY)
        nx = self.x + self.vx
        stop = blocked(self.x, nx, PLAYER_W / 2, self.y, self.G)
        if stop is not None:
            nx, self.vx = stop, 0.0
        self.x = nx
        self.y += self.vy
        f = ground_at(self.x, self.y - self.vy, self.G)
        if self.y >= f and self.vy >= 0:
            self.y, self.vy = float(f), 0.0
        if self.immune > 0:
            self.immune -= 1


class Beetle:
    """RhinoBeetle.UpdateState, state for state (the server's decisions and every side's movement), on the same floor."""
    CRAWL, BRACE, CHARGE, TOSS, SKID, DAZED, TAKEOFF, FLY, LAND = range(9)
    NAMES = ("crawl", "brace", "CHARGE", "toss", "skid", "dazed", "take off", "fly", "land")

    def __init__(self, x, G):
        self.x, self.y, self.vx, self.vy = float(x), float(G), 0.0, 0.0
        self.G = G
        self.state, self.timer, self.dir, self.cooldown = self.CRAWL, 0, 1, 0
        self.charge_dir, self.target_x, self.stuck, self.fly_cd = 1, 0.0, 0, 0
        self.counter, self.collide_x, self.vx_before = 0.0, False, 0.0
        self.w, self.h = KB["Width"], KB["Height"]

    def box(self):
        return (self.x - self.w / 2, self.y - self.h, self.x + self.w / 2, self.y)

    def inflated(self, k):
        b = self.box()
        return (b[0] - k, b[1] - k, b[2] + k, b[3] + k)

    def grounded(self):
        return self.vy == 0.0 and self.y >= ground_at(self.x, self.y, self.G) - 0.01

    def airborne(self):
        return self.state == self.FLY or (self.state == self.TAKEOFF and self.timer > KB["TakeOffTicks"] // 2)

    def change(self, s):
        self.state, self.timer = s, 0

    def ramming(self):
        return self.state == self.CHARGE or (self.state == self.TOSS and self.timer <= KB["TossTicks"] // 2)

    def run(self, d, speed, accel, jump):
        want = d * speed
        self.vx = min(want, self.vx + accel) if self.vx < want else max(want, self.vx - accel)
        if d != 0 and self.collide_x and self.grounded():
            self.vy = -jump

    def update(self, p):
        self.timer += 1
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.fly_cd > 0:
            self.fly_cd -= 1
        dx = p.x - self.x
        d = 1 if dx >= 0 else -1
        s = self.state
        if s == self.BRACE:
            self.run(0, 0.0, KB["CrawlAccel"] * 4, KB["JumpSpeed"])
            self.dir = d
            if self.timer >= KB["BraceTicks"]:
                self.charge_dir = d
                self.change(self.CHARGE)
        elif s == self.CHARGE:
            cd = self.charge_dir
            if self.timer == 1:
                self.target_x = p.x
            self.run(cd, KB["ChargeSpeed"], KB["ChargeAccel"], KB["JumpSpeed"] * 0.6)
            self.dir = cd
            if self.collide_x and abs(self.vx_before) > KB["WallStunSpeed"]:
                self.vx = -cd * 2.0
                self.change(self.DAZED)
            elif overlaps(self.inflated(4), p.box()):
                self.change(self.TOSS)
            elif (self.x > self.target_x + KB["Overshoot"] if cd > 0 else self.x < self.target_x - KB["Overshoot"]) or self.timer >= KB["ChargeMaxTicks"]:
                self.change(self.SKID)
        elif s in (self.TOSS, self.SKID, self.DAZED):
            self.vx *= {self.TOSS: 0.85, self.SKID: 0.9, self.DAZED: 0.85}[s]
            if self.timer >= {self.TOSS: KB["TossTicks"], self.SKID: KB["SkidTicks"], self.DAZED: KB["DazedTicks"]}[s]:
                self.cooldown = KB["ChargeCooldown"]
                self.change(self.CRAWL)
        elif s == self.TAKEOFF:
            self.vx *= 0.85
            if self.airborne():
                self.vy = max(self.vy - 0.3, -KB["LiftSpeed"])
            if self.timer >= KB["TakeOffTicks"]:
                self.change(self.FLY)
        elif s == self.FLY:
            tx, ty = p.x - self.x, (p.y - PLAYER_H / 2 - KB["FlyHover"]) - (self.y - self.h / 2)
            n = math.hypot(tx, ty)
            want = (tx / n * KB["FlySpeed"], ty / n * KB["FlySpeed"]) if n * n > 64 else (0.0, 0.0)
            sx, sy = want[0] - self.vx, want[1] - self.vy
            m = math.hypot(sx, sy)
            if m > KB["FlyAccel"]:
                sx, sy = sx / m * KB["FlyAccel"], sy / m * KB["FlyAccel"]
            self.vx += sx
            self.vy += sy
            if abs(self.vx) > 0.15:
                self.dir = 1 if self.vx > 0 else -1
            over = abs(p.x - self.x) < KB["DropRangeX"] and self.y < p.y - PLAYER_H
            if self.timer >= KB["FlyMaxTicks"] or (over and self.timer > 30):
                self.change(self.LAND)
        elif s == self.LAND:
            self.vx *= 0.96
            if (self.grounded() and self.timer > 2) or self.timer >= KB["LandMaxTicks"]:
                self.fly_cd = KB["FlyCooldown"]
                self.change(self.CRAWL)
        else:
            self.run(d, KB["CrawlSpeed"], KB["CrawlAccel"], KB["JumpSpeed"])
            if abs(self.vx) > 0.15:
                self.dir = 1 if self.vx > 0 else -1
            self.stuck = self.stuck + 1 if abs(self.vx) < KB["StuckSpeed"] else 0
            dy = p.y - self.y
            if self.fly_cd <= 0 and self.grounded() and abs(dx) < KB["FlyRangeX"] and (dy < -KB["FlyRise"] or self.stuck >= KB["StuckTicks"]):
                self.stuck = 0
                self.change(self.TAKEOFF)
            elif self.grounded() and self.cooldown <= 0 and abs(dx) < KB["ChargeRange"] and abs(dy) < KB["ChargeHeight"]:
                self.dir = d
                self.change(self.BRACE)
        # movement (vanilla's NPC collision, approximated): gravity unless airborne, solid faces, the floor
        if not self.airborne():
            self.vy = min(10.0, self.vy + 0.3)
        self.vx_before = self.vx
        nx = self.x + self.vx
        stop = blocked(self.x, nx, self.w / 2, self.y, self.G)
        self.collide_x = stop is not None
        if stop is not None:
            nx, self.vx = stop, 0.0
        self.x = nx
        self.y += self.vy
        f = ground_at(self.x, self.y - self.vy, self.G)
        if self.y >= f and self.vy >= 0:
            self.y, self.vy = float(f), 0.0
        # FindFrame's distance counters (every tick, as the game calls it)
        if self.state == self.CHARGE:
            self.counter = (self.counter + abs(self.vx)) % (KB["ChargeStep"] * KB["ChargeFrames"])
        elif self.state == self.CRAWL and abs(self.vx) > 0.15:
            self.counter = (self.counter + abs(self.vx)) % (KB["WalkStep"] * KB["WalkFrames"])

    def frame(self):
        s, t = self.state, self.timer
        if s == self.BRACE:
            return KB["Brace"] if t < 8 else KB["Brace"] + 1 + (t // 8) % 2
        if s == self.CHARGE:
            return KB["Charge"] + int(self.counter / KB["ChargeStep"]) % KB["ChargeFrames"]
        if s == self.TOSS:
            return KB["Toss"] + min(KB["TossFrames"] - 1, int(t / (KB["TossTicks"] / 3.0)))
        if s == self.SKID:
            return KB["Skid"]
        if s == self.DAZED:
            return KB["Dazed"] + (t // 6) % KB["DazedFrames"]
        if s == self.TAKEOFF:
            return KB["TakeOff"] + min(KB["TakeOffFrames"] - 1, int(t / (KB["TakeOffTicks"] / 2.0)))
        if s == self.FLY:
            return KB["Fly"] + (t // KB["FlapTicks"]) % KB["FlyFrames"]
        if s == self.LAND:
            return KB["TakeOff"] if self.grounded() else KB["TakeOff"] + 1
        if abs(self.vx) > 0.15:
            return KB["Walk"] + int(self.counter / KB["WalkStep"]) % KB["WalkFrames"]
        return KB["Walk"]


def beetle_backdrop(W, H, G):
    """A hall of the ruins: brick and column walls behind, a Fundamental Brick floor (a rune brick now and then), a stone
    platform (stand-in) and the ledge, framed like the game."""
    world = World.__new__(World)
    world.w, world.h = W // 16 + 1, H // 16 + 1
    world.tile, world.wall, world.water = {}, {}, set()
    gy = G // 16
    for x in range(world.w):
        for y in range(world.h):
            world.wall[(x, y)] = COLUMN_W if (x // 4) % 6 == 0 else BRICK_W
            px = x * 16
            if y >= gy or any(solid and o0 <= px < o1 and y >= gy - up // 16 for (o0, o1, up, solid) in OBSTACLES):
                world.tile[(x, y)] = RUNE_T if (y == gy and x % 9 == 4) else BRICK_T
            elif any(not solid and o0 <= px < o1 and y == gy - up // 16 for (o0, o1, up, solid) in OBSTACLES):
                world.tile[(x, y)] = PLAT_T
    return render(world, 0, 0, world.w - 1, world.h - 1, seed=9).crop((0, 0, W, H))


def scene_beetle(out, font):
    W, H, G = 1000, 380, 336
    bg = beetle_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    planes = Planes(RUIN + "NPCs/RhinoBeetle", KB)
    contact = int(KB["CrawlDamage"])
    ram = int(contact * KB["ChargeDamageMultiplier"])
    pops = []
    notes = [(0, "Rhino Beetle (%d life, %d defense, %d contact): it crawls up at %.1f px/tick"
              % (KB["Life"], KB["Defense"], contact, KB["CrawlSpeed"]))]
    # scene 1: the open floor (a ram, a jumped charge); scene 2: the wall, the ledge out of reach (a daze, the flight)
    p, b = Runner(500.0, G), Beetle(60.0, G)
    scene, phase, last_state, charges, end, card = 1, "stand", None, 0, None, 0
    tick, frames_out = 0, 0
    while tick < 2400:
        tick += 1
        if card > 0:                                         # a title card between the scenes
            card -= 1
            if card % TPF == 0:
                img = bg.copy()
                gif.text(img, (W // 2 - 260, H // 2 - 40), "next: a charge into a wall, and a player out of reach", font=gif.big)
                gif.push(img)
            if card == 0:
                p, b = Runner(820.0, G), Beetle(250.0, G)
                phase, last_state = "bait", None
            continue
        # --- the player's script, keyed to what the beetle does ---
        if scene == 1:
            if phase == "stand" and charges >= 2 and b.state == Beetle.CHARGE and abs(b.x - p.x) < 120:
                p.jump()                                    # the second charge: jumped over
                phase = "jumped"
            elif phase == "jumped" and b.state == Beetle.CRAWL and b.timer > 50:
                scene, card = 2, 60
                notes.append((tick, ""))
                continue
        else:
            if phase == "bait" and b.state == Beetle.CHARGE and abs(b.x - p.x) < 100:
                p.jump()                                    # up through the platform as it comes
                phase = "hop"
            elif phase == "hop" and p.grounded() and p.y < G - 1:
                phase = "on_platform"
            elif phase == "on_platform" and b.state == Beetle.DAZED and b.timer > 20:
                p.run = 1
                p.jump()                                    # and up onto the ledge
                phase = "to_ledge"
            elif phase == "to_ledge" and p.grounded() and p.y <= G - LEDGE_UP + 0.5:
                phase = "ledge"
            if phase == "ledge" and p.x > LEDGE_X + 50:
                p.run, p.face = 0, -1
        # --- contact: decided on the hit player's own client ---
        if overlaps(b.box(), p.box()) and p.immune == 0 and b.state != Beetle.DAZED:
            ramming = b.ramming()
            hurt_dir = b.charge_dir if ramming else (1 if p.x > b.x else -1)
            p.vx, p.vy, p.hold, p.immune = 4.5 * hurt_dir, -4.5 * 7 / 9.0, 0, IMMUNITY
            if ramming:
                p.toss = KB["TossSpeed"]
                pops.append((tick, p.x - 30, p.y - 90, "%d TOSSED!" % ram, HURT))
                notes.append((tick, "the ram: x%.1f contact (%d) and the horn flings the player up (%d px/tick)"
                              % (KB["ChargeDamageMultiplier"], ram, KB["TossSpeed"])))
            else:
                pops.append((tick, p.x - 10, p.y - 80, "%d" % contact, HURT))
        p.step()
        b.update(p)
        if b.state != last_state:
            if b.state == Beetle.BRACE:
                notes.append((tick, "level with it and in sight within %d tiles: it braces %d ticks (front down, horn levelled, a scrape)"
                              % (KB["ChargeRange"] // 16, KB["BraceTicks"])))
            elif b.state == Beetle.CHARGE:
                charges += 1
                notes.append((tick, "...and charges straight at up to %.1f px/tick%s" % (KB["ChargeSpeed"], ": jump it!" if charges == 2 else "")))
            elif b.state == Beetle.SKID:
                notes.append((tick, "it doesn't turn: it overshoots by %d tiles and skids" % (KB["Overshoot"] // 16)))
            elif b.state == Beetle.DAZED:
                notes.append((tick, "the player hops onto the platform: the charge meets the wall at speed, dazed %.2f s (no contact damage)"
                              % (KB["DazedTicks"] / 60.0)))
            elif b.state == Beetle.TAKEOFF:
                notes.append((tick, "the player is %d+ tiles above it: it opens its shell and takes off" % (KB["FlyRise"] // 16)))
            elif b.state == Beetle.FLY:
                notes.append((tick, "it flies to hover %d tiles over the player (%.1f px/tick, up to %d s)..."
                              % (KB["FlyHover"] // 16, KB["FlySpeed"], KB["FlyMaxTicks"] // 60)))
            elif b.state == Beetle.LAND:
                notes.append((tick, "...and over him it folds its wings and drops"))
                end = tick + 140
            last_state = b.state
        if tick % TPF == 0:
            img = bg.copy()
            fr = b.frame()
            dip = 2 if fr == KB["Fly"] + 2 else 0                # DrawAnchor: the hover bob on the down-beat
            planes.draw(img, fr, (b.x, b.y + dip), b.dir == 1, glow=1.0 if b.state in (Beetle.BRACE, Beetle.CHARGE) else 0.65)
            sprite = player_sprite(flip=p.face < 0)
            if p.immune and (tick // 3) % 2:
                sprite = faded(sprite, 0.5)
            img.alpha_composite(sprite, (int(p.x - 20), int(p.y - 56)))
            hurt_now = ram if b.ramming() else (0 if b.state == Beetle.DAZED else contact)
            gif.text(img, (10, 34), "beetle: %s  (contact %d)" % (Beetle.NAMES[b.state], hurt_now), fill=HURT if b.ramming() else STEAM)
            numbers(gif, img, pops, tick)
            note(gif, img, notes, tick)
            gif.push(img)
            frames_out += 1
        if end is not None and tick >= end:
            break
    print("beetle scene: %d ticks, scene %d, phase %s, %d charges" % (tick, scene, phase, charges))
    gif.save(out)


# ================================================================================================
# Items: the Macuahuitl, the ruins' blocks, the shield, the beetle, the drone
# ================================================================================================
def patch(kind, n=4, seed=2):
    """An n x n clump of a block, framed (one clump: the ruins' blocks merge)."""
    S = sheets()
    rng = random.Random(seed)
    img = Image.new("RGBA", (n * 16, n * 16), (0, 0, 0, 0))
    for x in range(n):
        for y in range(n):
            sig = "".join("-" if 0 <= x + dx < n and 0 <= y + dy < n else "o" for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
            fx, fy = rng.choice(S["frames"][sig])
            img.alpha_composite(S["tiles"][kind].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (x * 16, y * 16))
            if kind in S["glows"]:
                additive(img, S["glows"][kind].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (x * 16, y * 16), 0.9)
    return img


def items_png(out, font_path):
    font = font_at(font_path, 14)
    pics = [("Macuahuitl", load("Content/Junkyard/Weapons/Macuahuitl.png"), 3)]
    for label, kind in (("Fundamental Brick", BRICK_T), ("Coralstone", CORAL_T), ("Rune Brick", RUNE_T),
                        ("Ancient Brick", ABRICK_T), ("Rubble", RUBBLE_T)):
        pics.append((label, patch(kind), 2))
    for name in ("FundamentalBrick", "FundamentalCoral", "FundamentalRune", "FundamentalBrickWall", "FundamentalColumnWall"):
        pics.append((name.replace("Fundamental", ""), load(RUIN + "Items/%s.png" % name), 3))
    shield_strip = Image.new("RGBA", (6 * 108, 130), (16, 18, 26, 255))
    for k in range(int(KS["ShieldFrames"])):
        cell = Image.new("RGBA", (104, 128), (16, 18, 26, 255))
        cell.alpha_composite(stone_image(2, 1.0), (int(KS["ShieldStoneX"]), int(KS["ShieldStoneY"])))
        additive(cell, shield_frame(k), (0, 0), KS["ShieldOpacity"])
        shield_strip.alpha_composite(cell, (k * 108, 0))
    pics.append(("the stone's shield, 6 frames (%d ticks each), added at %d%%" % (KS["ShieldFrameTicks"], int(KS["ShieldOpacity"] * 100)), shield_strip, 1))
    planes = Planes(RUIN + "NPCs/RhinoBeetle", KB)
    names = ["Walk"] * 8 + ["Brace"] * 3 + ["Charge"] * 4 + ["Toss"] * 3 + ["Skid"] + ["Dazed"] * 2 + ["TakeOff"] * 2 + ["Fly"] * 4
    strip = Image.new("RGBA", (9 * 124, 3 * 92), (40, 44, 52, 255))
    dd = ImageDraw.Draw(strip)
    for k in range(int(KB["Frames"])):
        cx, cy = (k % 9) * 124 + 62, (k // 9) * 92 + 80
        planes.draw(strip, k, (cx, cy), False)
        dd.text((cx - 58, cy - 78), "%s %d" % (names[k], k), fill=(200, 200, 210), font=font)
    pics.append(("Rhino Beetle: every frame (far, middle, near planes and the glow)", strip, 1))
    for g in ("Horn", "Shell", "Leg"):
        pics.append(("gore: %s" % g.lower(), load(RUIN + "Gores/RhinoBeetle_Gore%s.png" % g), 3))
    dk = consts("Content/Scrap/NPCs/DeliveryDrone.cs")
    drone = load("Content/Scrap/NPCs/DeliveryDrone.png")
    fw, fh = int(dk["FrameW"]), int(dk["FrameH"])
    for k in range(min(6, drone.height // (fh + 2))):
        pics.append(("Delivery Drone %d" % k, drone.crop((0, k * (fh + 2), fw, k * (fh + 2) + fh)), 2))
    cells = []
    for (label, im, s) in pics:
        big = im.resize((im.width * s, im.height * s), Image.NEAREST)
        cell = Image.new("RGBA", (max(big.width, 120) + 20, big.height + 40), (40, 44, 52, 255))
        cell.alpha_composite(big, ((cell.width - big.width) // 2, 8))
        ImageDraw.Draw(cell).text((8, cell.height - 24), label, fill=(238, 241, 243), font=font)
        cells.append(cell)
    WMAX = 1200
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
            ("shield", lambda: scene_shield(o("2026-11-11_secrets-stone-shield.gif"), args.font)),
            ("macuahuitl", lambda: scene_macuahuitl(o("2026-11-11_weapon-macuahuitl.gif"), args.font)),
            ("beetle", lambda: scene_beetle(o("2026-11-11_ruins-rhino-beetle.gif"), args.font)),
            ("drone", lambda: scene_drone(o("2026-11-11_scrap-delivery-drone.gif"), args.font)),
            ("items", lambda: items_png(o("2026-11-11_items-macuahuitl-ruins-beetle.png"), args.font))]
    only = set(args.only.split(",")) if args.only else None
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
