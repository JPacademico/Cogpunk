"""D5 proof and blueprint check for Old Brass Town (2026-11-03): replays Content/OldBrassTown/Generation/OldBrassTownPass.cs
step by step (the same rules and the constants parsed out of the C#, with Python's random in place of WorldGen.genRand)
on a stand-in underground desert, and renders it with the town's real block and wall sheets.

    python -P tools/sim/old_brass_town_sim.py --out docs/media [--seed 7] [--check] [--sweep N] [--chests]

--check only validates the blueprints in OldBrassTownBlueprints.cs (rows of one width; every piece of furniture inside
the grid, on free cells, not overlapping another, standing on a block or a platform; mugs on a table or a platform;
lanterns under a solid block) and exits 1 on a problem. Every run does it first. --sweep N generates N seeds on each
world size (and on the smallest deserts the town accepts) and reports the buildings, the strongbox and the buried cache.

Writes:
    2026-11-04_oldbrasstown-town.png    the generated cavern on a small world's desert (whole, map-lit), a close-up of the
                                        street lit by its torches, lanterns and lamp posts, and two more seeds (the
                                        buildings shuffled per side and mirrored, the gaps and the ore differ).
    2026-11-03_oldbrasstown-blocks.png  the four blocks as clumps (vanilla's terrain framing), the two walls as patches
                                        (vanilla's wall framing), the items and the biome icon, at 2x.
    2026-11-04_oldbrasstown-chests.png  (--chests only) the buried cache under its lamp post and the bank vault's locked
                                        Brass Strongbox (2026-11-04, OldBrassTownPass.BuryCache / PlaceVault), the
                                        strongbox's frames, the key and the loot items.

Stand-ins (vanilla's art isn't in the repo): the desert hive around the town (hardened sand and sandstone with caves),
vanilla's furniture (tables, chairs, piano, bookcase, keg, barrels, gold chest, mugs, chain lanterns, desert torches,
lamp posts), wood platforms and beams, the glass and iron fence walls, and water are drawn in simple shapes. Lighting is
a flood fill (0.9 a tile through air, 0.55 into blocks), not vanilla's engine. Leaves out: slopes, chests' contents
(listed in the caption), framing of the hive's own tiles.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from terrain import load_frames, render, TILE, STRIDE  # noqa: E402

PASS = "Content/OldBrassTown/Generation/OldBrassTownPass.cs"
BLUEPRINTS = "Content/OldBrassTown/Generation/OldBrassTownBlueprints.cs"
T = "Content/OldBrassTown/"
SOLID = set("sobpHh")                                     # town blocks and the hive stand-ins
FOOT = {"T": (-1, 1, -1, 0), "n": (-1, 1, -1, 0), "o": (-1, 1, -3, 0), "c": (0, 0, -1, 0), "C": (0, 0, -1, 0),
        "X": (0, 1, -1, 0), "G": (0, 1, -1, 0), "k": (0, 1, -1, 0), "L": (0, 0, 0, 1), "m": (0, 0, 0, 0),
        "t": (0, 0, 0, 0), "l": (0, 0, -5, 0)}
STANDS = set("TnocCXGkl")
STAGE = {"m": 1, "L": 2, "t": 3}
LIGHTS = {"t": ((255, 214, 140), 1.0), "L": ((255, 232, 176), 1.0), "l": ((255, 238, 190), 1.15)}
PAL = {"B": (43, 26, 14), "C": (90, 58, 23), "D": (138, 93, 34), "E": (184, 138, 51), "F": (223, 185, 78), "G": (246, 231, 161),
       "i": (21, 22, 28), "j": (46, 50, 59), "k": (79, 85, 98), "q": (127, 135, 148), "r": (183, 191, 202), "l": (47, 27, 20),
       "m": (91, 54, 38), "n": (138, 90, 60), "s": (195, 200, 205), "t": (238, 241, 243), "y": (236, 113, 40), "z": (255, 199, 90),
       "x": (163, 48, 26), "w": (71, 145, 126)}


# ================================================================================================
# The C# sources
# ================================================================================================
def constants(path):
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"const (?:int|double|float) ([^;]+);", src):
        for part in m.group(1).split(","):
            if "=" in part:
                k, v = (x.strip() for x in part.split("=", 1))
                v = v.rstrip("f")
                if re.fullmatch(r"-?\d+(\.\d+)?", v):
                    out[k] = float(v) if "." in v else int(v)
    return out


def blueprints():
    src = open(os.path.join(ROOT, BLUEPRINTS), encoding="utf-8").read()
    bps = {}
    for m in re.finditer(r'public static readonly Blueprint (\w+) = new\(\s*"(\w+)",\s*new\[\] \{(.*?)\}\);', src, re.S):
        bps[m.group(1)] = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(3))
    order = re.search(r"Blueprint\[\] All = \{([^}]*)\}", src).group(1)
    return bps, [n.strip() for n in order.split(",")]


def check_blueprint(rows):
    errs = []
    w = len(rows[0]) if rows else 0
    if not rows or any(len(r) != w for r in rows):
        return ["rows are not one width"]
    h = len(rows)

    def at(x, y):
        return rows[y][x] if 0 <= x < w and 0 <= y < h else None
    claimed = {}
    for y in range(h):
        for x in range(w):
            ch = rows[y][x]
            if ch not in FOOT:
                continue
            dx0, dx1, dy0, dy1 = FOOT[ch]
            for dy in range(dy0, dy1 + 1):
                for dx in range(dx0, dx1 + 1):
                    c = at(x + dx, y + dy)
                    if c is None:
                        errs.append("%s at (%d,%d) leaves the grid" % (ch, x, y))
                        continue
                    if (dx, dy) != (0, 0) and c not in ".WF":
                        errs.append("%s at (%d,%d): cell (%d,%d) is %r" % (ch, x, y, x + dx, y + dy, c))
                    if (x + dx, y + dy) in claimed:
                        errs.append("%s at (%d,%d) overlaps %s" % (ch, x, y, claimed[(x + dx, y + dy)]))
                    claimed[(x + dx, y + dy)] = "%s(%d,%d)" % (ch, x, y)
            if ch in STANDS:
                for dx in range(dx0, dx1 + 1):
                    if at(x + dx, y + 1) not in set("PBS") | set("pa"):
                        errs.append("%s at (%d,%d) stands on %r" % (ch, x, y, at(x + dx, y + 1)))
            if ch == "L" and at(x, y - 1) not in set("PBS"):
                errs.append("L at (%d,%d) hangs from %r" % (x, y, at(x, y - 1)))
    for y in range(h):
        for x in range(w):
            if rows[y][x] == "m" and not (claimed.get((x, y + 1), "").startswith("T") or at(x, y + 1) in ("p", "a")):
                errs.append("m at (%d,%d) is not on a table or a platform" % (x, y))
    return errs


# ================================================================================================
# The generation, mirrored from OldBrassTownPass
# ================================================================================================
class Town:
    def __init__(self, k, bps, order, seed, hive_width=320):
        self.k, self.bps, self.order = k, bps, order
        self.rng = random.Random(seed)
        width = max(k["MinWidth"], min(k["MaxWidth"], round(hive_width * k["WidthFraction"])))
        height = max(k["MinHeight"], min(k["MaxHeight"], round(width * k["HeightRatio"])))
        self.rx, self.ry = width / 2.0, height / 2.0
        self.width, self.height = width, height
        hx = math.ceil(self.rx) + k["ShellThickness"] + k["ShellNoise"] + 1
        hy = math.ceil(self.ry) + k["ShellThickness"] + k["ShellNoise"] + 1
        pad = k["TunnelLength"] + 12
        self.W, self.H = 2 * hx + 1 + 2 * pad, 2 * hy + 1 + 24
        self.cx, self.cy = self.W // 2, 12 + hy
        self.floor = self.cy + round(self.ry * k["FloorLevel"])
        self.tile = [[None] * self.W for _ in range(self.H)]
        self.wall = [["hw"] * self.W for _ in range(self.H)]
        self.water = set()
        self.pieces = []                                  # placed furniture: (kind, x, y)
        self.occupied = {}                                # (x, y) -> kind of the furniture there
        self.chests = []
        self.cache_spots = []                             # the lamp posts' columns (OldBrassTownPass.cacheSpots)
        self.cache = None                                 # the buried cache's chest, bottom left (x, y)
        self.vault = None                                 # the bank vault's strongbox, bottom left (x, y)
        self.built = []
        self.tunnels = []
        self.hive()
        self.generate()

    # --- the stand-in desert hive: hardened sand in bands of sandstone, cave pockets (cellular automaton) ---------------
    def hive(self):
        r = random.Random(self.rng.random())
        cave = [[r.random() < 0.46 for _ in range(self.W)] for _ in range(self.H)]
        for _ in range(5):
            nxt = [[False] * self.W for _ in range(self.H)]
            for y in range(self.H):
                for x in range(self.W):
                    n = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                            if (dx or dy) and (not (0 <= x + dx < self.W and 0 <= y + dy < self.H) or not cave[y + dy][x + dx]))
                    nxt[y][x] = n < 4
            cave = nxt
        for y in range(self.H):
            for x in range(self.W):
                if not cave[y][x]:
                    band = (y + 3.0 * math.sin(x / 11.0) + 2.0 * math.sin(x / 4.3)) / 6.0
                    self.tile[y][x] = "H" if int(math.floor(band)) % 3 == 0 else "h"

    # --- OldBrassTownPass.Generate -----------------------------------------------------------------------------------
    def generate(self):
        self.profile()
        self.carve()
        self.roughen()
        self.stalactites()
        self.ore()
        queued = []
        self.street(queued)
        self.furnish(queued)
        self.bury_cache()
        self.dig(-1)
        self.dig(1)
        self.area = (self.left, self.top, self.right - self.left + 1, self.bottom - self.top + 1)

    def noise(self, count, amplitude):
        step = self.k["NoiseStep"]
        control = [self.rng.random() * amplitude for _ in range(count // step + 2)]
        return [control[i // step] + (control[i // step + 1] - control[i // step]) * ((i % step) / step) for i in range(count)]

    def profile(self):
        k = self.k
        hx = math.ceil(self.rx) + k["ShellThickness"] + k["ShellNoise"] + 1
        self.left, self.right = self.cx - hx, self.cx + hx
        n = self.right - self.left + 1
        shell, ceiling = self.noise(n, k["ShellNoise"]), self.noise(n, k["CeilingNoise"])
        self.air_top, self.air_bot, self.rock_top, self.rock_bot = [1] * n, [0] * n, [1] * n, [0] * n
        self.top, self.bottom = 10 ** 9, -10 ** 9
        for i in range(n):
            dx = self.left + i - self.cx
            u = dx / self.rx
            if abs(u) < 1.0:
                self.air_top[i] = math.ceil(self.cy - self.ry * self.roof(u) + ceiling[i])
                self.air_bot[i] = min(self.floor - 1, math.floor(self.cy + self.ry * math.sqrt(1.0 - u * u)))
            ox, oy = self.rx + k["ShellThickness"] + shell[i], self.ry + k["ShellThickness"] + shell[i]
            v = dx / ox
            if abs(v) < 1.0:
                self.rock_top[i], self.rock_bot[i] = math.floor(self.cy - oy * self.roof(v)), math.ceil(self.cy + oy * math.sqrt(1.0 - v * v))
                self.top, self.bottom = min(self.top, self.rock_top[i]), max(self.bottom, self.rock_bot[i])

    def roof(self, u):
        p = self.k["CeilingExponent"]
        return (1.0 - abs(u) ** p) ** (1.0 / p)

    def roughen(self):
        n = len(self.rock_top)
        for _ in range(n // self.k["RoughSpacing"]):
            i = self.rng.randrange(n)
            if self.rock_top[i] > self.rock_bot[i]:
                continue
            x = self.left + i
            y = self.rock_top[i] if self.rng.random() < 0.5 else self.rock_bot[i]
            radius = 1.5 + self.rng.random() * 2.0
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    ax, ay = x + dx, y + dy
                    if dx * dx + dy * dy <= radius * radius and not self.in_footprint(ax, ay) and 0 <= ay < self.H and self.tile[ay][ax] in ("h", "H"):
                        self.tile[ay][ax] = "s"

    def stalactites(self):
        n = len(self.rock_top)
        self.spikes = 0
        for _ in range(n // self.k["StalactiteSpacing"]):
            i = self.rng.randrange(n)
            if i + 1 >= n or self.air_top[i] > self.air_bot[i] or self.air_top[i + 1] > self.air_bot[i + 1]:
                continue
            length = self.rng.randint(2, 5)
            root = max(self.air_top[i], self.air_top[i + 1])
            tip = root + length - 1
            if tip >= self.floor - self.k["StalactiteClearance"]:
                continue
            for (col, y0, y1) in ((i, self.air_top[i], tip), (i + 1, self.air_top[i + 1], root + length // 2 - 1)):
                for y in range(y0, y1 + 1):
                    if self.tile[y][self.left + col] is None:
                        self.tile[y][self.left + col] = "s"
            self.spikes += 1

    def in_footprint(self, x, y):
        i = x - self.left
        return 0 <= i < len(self.rock_top) and self.rock_top[i] <= y <= self.rock_bot[i]

    def is_air(self, x, y):
        i = x - self.left
        return 0 <= i < len(self.air_top) and self.air_top[i] <= y <= self.air_bot[i]

    def carve(self):
        for i in range(len(self.rock_top)):
            x = self.left + i
            for y in range(self.rock_top[i], self.rock_bot[i] + 1):
                self.wall[y][x] = "bsw"
                self.tile[y][x] = None if self.air_top[i] <= y <= self.air_bot[i] else "s"

    def ore(self):
        n = len(self.rock_top)
        self.ore_tiles = 0
        for _ in range(max(4, n // self.k["OreVeinSpacing"])):
            for _attempt in range(10):
                i = self.rng.randrange(n)
                if self.rock_top[i] > self.rock_bot[i]:
                    continue
                x, y = self.left + i, self.rng.randint(self.rock_top[i], self.rock_bot[i])
                if self.is_air(x, y):
                    continue
                radius = 1.2 + self.rng.random() * 1.2
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        reach = radius * (0.85 + self.rng.random() * 0.3)
                        ox, oy = x + dx, y + dy
                        if dx * dx + dy * dy > reach * reach or oy in (self.floor, self.floor + 1) or not self.in_footprint(ox, oy):
                            continue
                        if self.tile[oy][ox] == "s":
                            self.tile[oy][ox] = "o"
                            self.ore_tiles += 1
                break

    def is_street(self, i):
        return self.air_bot[i] == self.floor - 1 and self.air_bot[i] - self.air_top[i] + 1 >= self.k["MinStreetHeadroom"]

    def street(self, queued):
        k = self.k
        cols = [self.left + i for i in range(len(self.air_top)) if self.is_street(i)]
        if not cols:
            return
        lo, hi = cols[0] + k["StreetMargin"], cols[-1] - k["StreetMargin"]
        a, b, c, d = "Store", "Sheriff", "Bank", "WaterTower"
        if self.rng.random() < 0.5:
            a, b = b, a
        if self.rng.random() < 0.5:
            c, d = d, c
        row = [a, b, "Saloon", c, d]
        if self.rng.random() < 0.5:
            row.reverse()
        gaps = [self.rng.randint(k["MinGap"], k["MaxGap"]) for _ in row]

        def length():
            return sum(len(self.bps[n][0]) + (gaps[j] if j < len(row) - 1 else 0) for j, n in enumerate(row))
        for guard in range(len(self.order)):
            if len(row) <= 1 or length() <= hi - lo + 1:
                break
            drop = len(row) - 1 if row[-1] != "Saloon" and (guard % 2 == 0 or row[0] == "Saloon") else 0
            row.pop(drop)
            gaps.pop(drop)
        if length() > hi - lo + 1:
            return
        x = lo + (hi - lo + 1 - length()) // 2
        self.lamp(queued, x - 3)
        for j, name in enumerate(row):
            rows = self.bps[name]
            w, h = len(rows[0]), len(rows)
            if self.fits(rows, x):
                self.build(rows, x, self.floor - (h - 1), queued)
                self.built.append((name, x, self.floor - (h - 1), w, h))
            gap = gaps[j] if j < len(row) - 1 else 0
            if gap >= k["LampGap"]:
                self.lamp(queued, x + w + gap // 2)
            x += w + gap
        self.lamp(queued, x + 2)

    def lamp(self, queued, x):
        self.cache_spots.append(x)
        if self.is_air(x, self.floor - 1):
            queued.append(("l", x, self.floor - 1))

    def fits(self, rows, x0):
        y0 = self.floor - (len(rows) - 1)
        for bx in range(len(rows[0])):
            i = x0 + bx - self.left
            if i < 0 or i >= len(self.air_top) or self.air_top[i] > self.air_bot[i]:
                return False
            for by in range(len(rows)):
                if rows[by][bx] != " ":
                    if y0 + by < self.air_top[i] + self.k["HeadRoom"]:
                        return False
                    break
        return True

    def build(self, rows, x0, y0, queued):
        for by, line in enumerate(rows):
            for bx, ch in enumerate(line):
                if ch == " ":
                    continue
                x, y = x0 + bx, y0 + by
                kept = self.wall[y][x]
                self.tile[y][x] = None
                self.water.discard((x, y))
                wall = {"W": "glass", "F": "fence", "a": kept, "I": kept}.get(ch, "pw")
                if ch in {"P": 1, "B": 1, "S": 1}:
                    self.tile[y][x] = {"P": "p", "B": "b", "S": "s"}[ch]
                elif ch in ("p", "a"):
                    self.tile[y][x] = "plat"
                elif ch == "I":
                    self.tile[y][x] = "beam"
                elif ch == "w":
                    self.water.add((x, y))
                elif ch not in ".DWF":
                    left, right = line[bx - 1] if bx > 0 else " ", line[bx + 1] if bx + 1 < len(line) else " "
                    wall = "fence" if "F" in (left, right) else "pw"
                    queued.append((ch, x, y))
                self.wall[y][x] = wall

    # --- furniture: TileObject.CanPlace approximated --------------------------------------------------------------------
    def free(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H and self.tile[y][x] is None and (x, y) not in self.occupied

    def support(self, x, y):
        return 0 <= y < self.H and self.tile[y][x] in SOLID | {"plat"}

    def can_place(self, kind, x, y):
        dx0, dx1, dy0, dy1 = FOOT[kind]
        if not all(self.free(x + dx, y + dy) for dx in range(dx0, dx1 + 1) for dy in range(dy0, dy1 + 1)):
            return False
        if kind in STANDS:
            return all(self.support(x + dx, y + 1) for dx in range(dx0, dx1 + 1))
        if kind == "m":
            return self.occupied.get((x, y + 1)) == "T" or self.tile[y + 1][x] == "plat"
        if kind == "L":
            return self.tile[y - 1][x] in SOLID
        if kind == "t":
            return self.wall[y][x] is not None or any(self.tile[y + dy][x + dx] in SOLID for dx, dy in ((-1, 0), (1, 0), (0, 1)))
        return True

    def furnish(self, queued):
        self.skipped = []
        for stage in range(4):
            for kind, x, y in queued:
                if STAGE.get(kind, 0) != stage:
                    continue
                if not self.can_place(kind, x, y):
                    self.skipped.append((kind, x, y))
                    continue
                dx0, dx1, dy0, dy1 = FOOT[kind]
                for dy in range(dy0, dy1 + 1):
                    for dx in range(dx0, dx1 + 1):
                        self.occupied[(x + dx, y + dy)] = kind
                self.pieces.append((kind, x, y))
                if kind in "XG":
                    self.chests.append((kind, x, y))
                if kind == "G":
                    self.vault = (x, y)

    # --- OldBrassTownPass.BuryCache: a gold chest in a pocket of rock under a lamp post, two planks over it ------------
    def can_bury(self, gx):
        k = self.k
        for x in range(gx - 2, gx + 4):
            for y in range(self.floor, self.floor + k["CacheDepth"] + k["CacheHeight"] + 2):
                if not (0 <= x < self.W and 0 <= y < self.H) or not self.in_footprint(x, y) or self.is_air(x, y):
                    return False
        return True

    def bury_cache(self):
        k = self.k
        count = len(self.cache_spots)
        start = self.rng.randrange(count) if count else 0
        for j in range(count):
            gx = self.cache_spots[(start + j) % count] - 1
            if not self.can_bury(gx):
                continue
            top = self.floor + k["CacheDepth"]
            floor = top + k["CacheHeight"]
            for x in range(gx - 1, gx + 3):
                for y in range(top, floor):
                    self.tile[y][x] = None
            for x in (gx, gx + 1):
                self.tile[floor][x] = "s"
                self.tile[self.floor][x] = "p"
            self.cache = (gx, floor - 1)
            self.pieces.append(("cache", gx, floor - 1))
            self.chests.append(("cache", gx, floor - 1))
            return

    def dig(self, d):
        k = self.k
        n = len(self.air_top)
        start = next((i if d < 0 else n - 1 - i for i in range(n) if self.air_top[i if d < 0 else n - 1 - i] <= self.air_bot[i if d < 0 else n - 1 - i]), None)
        if start is None:
            return
        x, fl = self.left + start, self.air_bot[start]
        start_floor, opened, dug = fl, 0, 0
        for step in range(1, k["TunnelLength"] + 1):
            x += d
            if step % 4 == 0:
                fl = max(start_floor - k["TunnelDrift"], min(start_floor, fl + self.rng.choice((-1, 0))))
            if not (0 <= x < self.W):
                break
            cells = range(fl - k["TunnelHeight"] + 1, fl + 1)
            if all(self.tile[y][x] is None for y in cells) and not self.in_footprint(x, fl):
                opened += 1
                if opened >= 2:
                    break
                continue
            opened = 0
            for y in cells:
                self.tile[y][x] = None
            if self.tile[fl + 1][x] is None:
                self.tile[fl + 1][x] = "s"
            dug += 1
        self.tunnels.append(dug)


# ================================================================================================
# Rendering
# ================================================================================================
def stand_in_sheet(base, seed):
    """A terrain sheet for a vanilla block the repo has no art for: speckled squares, a darker rim on exposed sides."""
    table = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
    sheet = Image.new("RGBA", (16 * STRIDE, 15 * STRIDE), (0, 0, 0, 0))
    r = random.Random(seed)
    for signature, cells in table.items():
        for (fx, fy) in cells:
            tile = Image.new("RGBA", (TILE, TILE))
            d = ImageDraw.Draw(tile)
            for py in range(0, TILE, 2):
                for px in range(0, TILE, 2):
                    v = r.choice((-10, 0, 0, 8))
                    d.rectangle([px, py, px + 1, py + 1], fill=tuple(max(0, min(255, c + v)) for c in base) + (255,))
            dark = tuple(int(c * 0.55) for c in base) + (255,)
            top, right, bottom, left = (ch == "o" for ch in signature)
            if top:
                d.rectangle([0, 0, TILE - 1, 1], fill=dark)
            if bottom:
                d.rectangle([0, TILE - 2, TILE - 1, TILE - 1], fill=dark)
            if left:
                d.rectangle([0, 0, 1, TILE - 1], fill=dark)
            if right:
                d.rectangle([TILE - 2, 0, TILE - 1, TILE - 1], fill=dark)
            sheet.alpha_composite(tile, (fx * STRIDE, fy * STRIDE))
    return sheet


WALL_LOOKUP = {0: ((9, 3), (10, 3), (11, 3)), 1: ((6, 3), (7, 3), (8, 3)), 2: ((12, 0), (12, 1), (12, 2)), 3: ((1, 4), (3, 4), (5, 4)),
               4: ((9, 0), (9, 1), (9, 2)), 5: ((0, 4), (2, 4), (4, 4)), 6: ((6, 4), (7, 4), (8, 4)), 7: ((1, 2), (2, 2), (3, 2)),
               8: ((6, 0), (7, 0), (8, 0)), 9: ((5, 0), (5, 1), (5, 2)), 10: ((1, 3), (3, 3), (5, 3)), 11: ((4, 0), (4, 1), (4, 2)),
               12: ((0, 3), (2, 3), (4, 3)), 13: ((0, 0), (0, 1), (0, 2)), 14: ((1, 0), (2, 0), (3, 0)), 15: ((1, 1), (2, 1), (3, 1)),
               16: ((6, 1), (7, 1), (8, 1)), 17: ((6, 2), (7, 2), (8, 2)), 18: ((10, 0), (10, 1), (10, 2)), 19: ((11, 0), (11, 1), (11, 2))}
CENTRE = [[2, 0, 0], [0, 1, 4], [0, 3, 0]]                # decompiled Framing.centerWallFrameLookup, [i % 3][j % 3]


def art(rows, colours):
    """ASCII art pixels (2x2 screen px each) -> image; '.' transparent."""
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y, line in enumerate(rows):
        for x, ch in enumerate(line):
            if ch != ".":
                d.rectangle([x * 2, y * 2, x * 2 + 1, y * 2 + 1], fill=colours.get(ch, PAL.get(ch, (255, 0, 255))) + (255,))
    return im


FURNITURE = {   # anchor offset in tiles (left, top) from the anchor cell, and the stand-in art (8 art px a tile)
    "T": ((-1, -1), ["........................", "........................", "qnnnnnnnnnnnnnnnnnnnnnnq", "nmmmmmmmmmmmmmmmmmmmmmmn",
                     ".lmm................mml.", "..mm................mm..", "..mm................mm..", "..mm................mm..",
                     "..mm................mm..", "..mm................mm..", "..mm................mm..", "..mm................mm..",
                     "..mm................mm..", "..mm................mm..", ".lmml..............lmml.", ".llll..............llll."]),
    "c": ((0, -1), ["......l.", ".....lnl", ".....lnl", ".....lnl", ".....lnl", ".....lnl", ".....lnl", ".lllllnl",
                    "lnnnnnnl", "lmmmmmml", ".lm..lm.", ".lm..lm.", ".lm..lm.", ".lm..lm.", ".lm..lm.", ".ll..ll."]),
    "n": ((-1, -1), ["........................", "..llllllllllllllllllll..", ".lmmmmmmmmmmmmmmmmmmmmml", ".lmnnnnnnnnnnnnnnnnnnnml",
                     ".lmmmmmmmmmmmmmmmmmmmmml", ".ltitititititititititml", ".lttttttttttttttttttttml", ".lmmmmmmmmmmmmmmmmmmmmml",
                     ".lmnnnnnnnnnnnnnnnnnnnml", ".lmnnEnnnnnnnnnnnnnEnnml", ".lmnnnnnnnnnnnnnnnnnnnml", ".lmmmmmmmmmmmmmmmmmmmmml",
                     ".lm..................ml", ".lm..................ml", ".lm..................ml", ".ll..................ll"]),
    "o": ((-1, -3), ["llllllllllllllllllllllll", "lmmmmmmmmmmmmmmmmmmmmmml", "lmxxDwqxxwwDDxqqwxDDxwml", "lmxxDwqxxwwDDxqqwxDDxwml",
                     "lmxxDwqxxwwDDxqqwxDDxwml", "lmxxDwqxxwwDDxqqwxDDxwml", "lmxxDwqxxwwDDxqqwxDDxwml", "lmnnnnnnnnnnnnnnnnnnnnml",
                     "lmmmmmmmmmmmmmmmmmmmmmml", "lmwDDxxqqDwwxDDqxxwDDqml", "lmwDDxxqqDwwxDDqxxwDDqml", "lmwDDxxqqDwwxDDqxxwDDqml",
                     "lmwDDxxqqDwwxDDqxxwDDqml", "lmwDDxxqqDwwxDDqxxwDDqml", "lmnnnnnnnnnnnnnnnnnnnnml", "lmmmmmmmmmmmmmmmmmmmmmml",
                     "lmqxxDwwqDDxxwqqDxxwDDml", "lmqxxDwwqDDxxwqqDxxwDDml", "lmqxxDwwqDDxxwqqDxxwDDml", "lmqxxDwwqDDxxwqqDxxwDDml",
                     "lmqxxDwwqDDxxwqqDxxwDDml", "lmnnnnnnnnnnnnnnnnnnnnml", "lmmmmmmmmmmmmmmmmmmmmmml", "lm....................ml",
                     "lm....................ml", "lm....................ml", "lm....................ml", "lm....................ml",
                     "lmnnnnnnnnnnnnnnnnnnnnml", "lmmmmmmmmmmmmmmmmmmmmmml", "lml..................lml", "lll..................lll"]),
    "k": ((0, -1), ["................", "................", "....llllllll....", "..llnnnnnnnnll..", ".lnnkkkkkkkknnl.", ".lnnnnnnnnnnnnnl",
                    "lnnnnnnnnnnnnnnl", "lmkkkkkkkkkkkkml", "lmmmmmmmmmmmmmml", "lmmmmmmmmmmmmmml", ".lmkkkkkkkkkkml.", ".lmmmmmmmmmmmml.",
                    "..llmmmmmmmmll..", "...lml....lml...", "...lll....lll...", "................"]),
    "X": ((0, -1), ["....llllllll....", "...lnnnnnnnnl...", "..lnqnnnnnnnnl..", "..lkkkkkkkkkkl..", "..lnnnnnnnnnml..", ".lnqnnnnnnnnnml.",
                    ".lnnnnnnnnnnnml.", ".lkkkkkkkkkkkkl.", ".lnqnnnnnnnnnml.", ".lnnnnnnnnnnnml.", "..lnnnnnnnnnml..", "..lkkkkkkkkkkl..",
                    "..lnnnnnnnnnml..", "...lmmmmmmmml...", "....llllllll....", "................"]),
    "G": ((0, -1), ["................", "..BBBBBBBBBBBB..", ".BGFFFFFFFFFFEB.", ".BFFFFFFFFFFFDB.", ".BEEEEEEEEEEEDB.", ".BBBBBBBBBBBBBB.",
                    ".BFFFFFkkFFFFDB.", ".BFFFFkjjkFFFDB.", ".BFEFFFkkFFFEDB.", ".BFFFFFFFFFFFDB.", ".BEFFFFFFFFFEDB.", ".BFFFFFFFFFFFDB.",
                    ".BEEEEEEEEEEEDB.", ".BDDDDDDDDDDDCB.", "..BBBBBBBBBBBB..", "................"]),
    "m": ((0, 0), ["........", "..tttt..", ".tssssl.", ".lnnnnlm", ".lnqnnl.m", ".lnnnnlm", ".lmmmml.", "..llll.."]),
    "L": ((0, 0), ["...kk...", "...jj...", "...kk...", "...jj...", "...kk...", "..BBBB..", ".BFFFFB.", ".BzzzzB.", ".BzGGzB.",
                   ".BzGGzB.", ".BzzzzB.", ".BFFFFB.", "..BBBB..", "...BB...", "........", "........"]),
    "t": ((0, 0), ["...zz...", "..zGGz..", "..zyGz..", "...yy...", "...ll...", "...nl...", "...nl...", "...ll..."]),
    "l": ((0, -5), ["..BBBB..", ".BFFFFB.", "BzGGGGzB", "BzGGGGzB", "BzzzzzzB", ".BFFFFB.", "..BjjB..", "...jk..."]
                   + ["...jk..."] * 34 + ["..jjkk..", ".jjkkkk.", ".iiiiii.", "........"]),
}
FURNITURE["C"] = (FURNITURE["c"][0], [line[::-1] for line in FURNITURE["c"][1]])


def strongbox_sprite(locked, lid=0):
    """The Brass Strongbox as the game draws it: the 2x2 frame of its style and lid frame, tiles 16 px apart (the
    sheet's 2 px gaps dropped), the bottom tiles 18 tall so it sinks 2 px into the floor."""
    sheet = Image.open(os.path.join(ROOT, T + "Tiles/BrassStrongboxTile.png")).convert("RGBA")
    fx, fy = (36 if locked else 0), lid * 38
    out = Image.new("RGBA", (32, 34), (0, 0, 0, 0))
    for dx in range(2):
        for dy in range(2):
            h = 16 if dy == 0 else 18
            out.alpha_composite(sheet.crop((fx + dx * 18, fy + dy * 18, fx + dx * 18 + 16, fy + dy * 18 + h)), (dx * 16, dy * 16))
    return out


def furniture_sprite(kind, cache={}):
    if kind not in cache:
        cache[kind] = art(FURNITURE[kind][1], {})
    return cache[kind]


def draw_town(town, lit=False):
    """The whole patch at 16 px a tile: walls, water, blocks, platforms and beams, furniture; optionally torch-lit."""
    frames = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
    W, H = town.W, town.H
    img = Image.new("RGBA", (W * TILE, H * TILE), (20, 18, 24, 255))
    sheets = {"bsw": Image.open(os.path.join(ROOT, T + "Walls/BrassSandstoneWallTile.png")).convert("RGBA"),
              "pw": Image.open(os.path.join(ROOT, T + "Walls/WeatheredPlankWallTile.png")).convert("RGBA")}
    r = random.Random(3)
    for y in range(H):
        for x in range(W):
            wall = town.wall[y][x]
            if wall is None:
                continue
            if wall in sheets:
                has = lambda ax, ay: 0 <= ax < W and 0 <= ay < H and town.wall[ay][ax] is not None
                st = (1 if has(x, y - 1) else 0) | (2 if has(x - 1, y) else 0) | (4 if has(x + 1, y) else 0) | (8 if has(x, y + 1) else 0)
                if st == 15:
                    st += CENTRE[x % 3][y % 3]
                fx, fy = WALL_LOOKUP[st][r.randrange(3)]
                img.alpha_composite(sheets[wall].crop((fx * 36, fy * 36, fx * 36 + 32, fy * 36 + 32)), (x * TILE - 8, y * TILE - 8))
    d = ImageDraw.Draw(img)
    for y in range(H):
        for x in range(W):
            wall, px, py = town.wall[y][x], x * TILE, y * TILE
            if wall == "hw":
                d.rectangle([px, py, px + 15, py + 15], fill=(74, 58, 44, 255))
                if (x * 7 + y * 3) % 5 == 0:
                    d.rectangle([px + 4, py + 6, px + 9, py + 7], fill=(62, 48, 36, 255))
            elif wall == "glass":
                d.rectangle([px, py, px + 15, py + 15], fill=(118, 150, 170, 255))
                d.line([px, py + 15, px + 15, py + 15], fill=(84, 104, 120, 255), width=2)
                d.line([px + 15, py, px + 15, py + 15], fill=(84, 104, 120, 255), width=2)
                d.rectangle([px + 3, py + 3, px + 5, py + 5], fill=(190, 214, 228, 255))
            elif wall == "fence":
                d.rectangle([px, py, px + 15, py + 15], fill=(40, 34, 32, 255))
                for bx in (2, 10):
                    d.rectangle([px + bx, py, px + bx + 3, py + 15], fill=PAL["k"] + (255,))
                    d.line([px + bx, py, px + bx, py + 15], fill=PAL["q"] + (255,))
    for (x, y) in town.water:
        d.rectangle([x * TILE, y * TILE, x * TILE + 15, y * TILE + 15], fill=(44, 92, 176, 255))
        d.line([x * TILE, y * TILE + 2, x * TILE + 15, y * TILE + 2], fill=(84, 132, 210, 255))
    grid = ["".join((town.tile[y][x] if town.tile[y][x] in SOLID else ".") for x in range(W)) for y in range(H)]
    blocks = {"s": "BrassSandstone", "o": "TarnishedBrassOre", "p": "WeatheredPlank", "b": "TarnishedBrassPlating"}
    tile_sheets = {c: Image.open(os.path.join(ROOT, T + "Tiles/%sTile.png" % n)).convert("RGBA") for c, n in blocks.items()}
    tile_sheets["h"] = stand_in_sheet((176, 146, 100), 1)
    tile_sheets["H"] = stand_in_sheet((148, 106, 70), 2)
    img.alpha_composite(render(grid, tile_sheets, frames, seed=5))
    plat = art(["qqqqqqqq", "nnnnnnnn", "mlmmmmlm", ".l....l."], {})
    beam = art(["..lnnl..", "..lnml..", "..lnnl..", "..lmnl..", "..lnnl..", "..lnml..", "..lnnl..", "..lmnl.."], {})
    for y in range(H):
        for x in range(W):
            if town.tile[y][x] == "plat":
                img.alpha_composite(plat, (x * TILE, y * TILE))
            elif town.tile[y][x] == "beam":
                img.alpha_composite(beam, (x * TILE, y * TILE))
    for kind, x, y in town.pieces:
        if kind == "G":
            img.alpha_composite(strongbox_sprite(locked=True), (x * TILE, (y - 1) * TILE))
            continue
        (ox, oy), _ = FURNITURE["G" if kind == "cache" else kind]
        img.alpha_composite(furniture_sprite("G" if kind == "cache" else kind), ((x + ox) * TILE, (y + oy) * TILE))
    if lit:
        img = apply_light(town, img)
    return img


def apply_light(town, img):
    """Flood-filled light from the town's torches, lanterns and lamp posts (and a faint ambient), per tile, smoothed."""
    W, H = town.W, town.H
    light = [[(0.0, 0.0, 0.0)] * W for _ in range(H)]
    for kind, x, y in town.pieces:
        if kind not in LIGHTS:
            continue
        colour, power = LIGHTS[kind]
        sy = y - 5 if kind == "l" else y + (1 if kind == "L" else 0)
        frontier, seen = [(x, sy, power)], {}
        while frontier:
            nxt = []
            for (fx, fy, p) in frontier:
                if p < 0.04 or seen.get((fx, fy), 0.0) >= p:
                    continue
                seen[(fx, fy)] = p
                solid = town.tile[fy][fx] in SOLID
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ax, ay = fx + dx, fy + dy
                    if 0 <= ax < W and 0 <= ay < H:
                        nxt.append((ax, ay, p * (0.55 if solid or town.tile[ay][ax] in SOLID else 0.9)))
            frontier = nxt
        for (lx, ly), p in seen.items():
            old = light[ly][lx]
            light[ly][lx] = tuple(max(o, min(1.0, p) * c / 255.0) for o, c in zip(old, colour))
    lm = Image.new("RGB", (W, H))
    lm.putdata([tuple(int(255 * max(v, 0.1)) for v in light[y][x]) for y in range(H) for x in range(W)])
    lm = lm.resize((W * TILE, H * TILE), Image.BILINEAR)
    from PIL import ImageChops
    return Image.merge("RGBA", (*ImageChops.multiply(img.convert("RGB"), lm).split(), img.split()[3]))


def town_png(out, font_path, seed):
    k = constants(PASS)
    bps, order = blueprints()
    font, big = ImageFont.truetype(font_path, 16), ImageFont.truetype(font_path, 22)
    town = Town(k, bps, order, seed)
    full = draw_town(town)
    x0, y0 = (town.left - k["TunnelLength"] - 6) * TILE, (town.top - 6) * TILE
    x1, y1 = (town.right + k["TunnelLength"] + 7) * TILE, (town.bottom + 7) * TILE
    overview = full.crop((max(0, x0), max(0, y0), min(full.width, x1), min(full.height, y1)))
    overview = overview.resize((overview.width // 3, overview.height // 3), Image.BOX)
    lit = draw_town(town, lit=True)
    sx = (town.cx - 52) * TILE
    sy = (min(town.air_top[town.cx - town.left - 30:town.cx - town.left + 30]) - 2) * TILE
    close = lit.crop((sx, sy, sx + 104 * TILE, (town.floor + 3) * TILE))
    extra = []
    for s in (seed + 1, seed + 2):
        t2 = Town(k, bps, order, s)
        im = draw_town(t2)
        im = im.crop(((t2.left - 2) * TILE, (t2.top - 2) * TILE, (t2.right + 3) * TILE, (t2.bottom + 3) * TILE))
        extra.append((s, t2, im.resize((im.width // 5, im.height // 5), Image.BOX)))
    W = max(overview.width, close.width, sum(e[2].width for e in extra) + 20) + 40
    H = 60 + overview.height + 50 + close.height + 50 + max(e[2].height for e in extra) + 90
    sheet = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sheet)
    names = ", ".join(b[0] for b in town.built)
    d.text((20, 14), "Old Brass Town (seed %d): a %dx%d cavern %d%% across a small world's underground desert, %d buildings: %s" % (
        seed, town.width, town.height, round(100 * k["WidthFraction"]), len(town.built), names), font=big, fill=(238, 241, 243))
    y = 60
    sheet.alpha_composite(overview, (20, y))
    y += overview.height + 8
    d.text((20, y), "Whole, map-lit, 1/3 scale: the ragged Brass Sandstone shell (%d+ tiles) with %d Tarnished Brass Ore tiles, the street, "
           "mine tunnels %s tiles long into the hive (stand-in: hardened sand and sandstone)" % (
               k["ShellThickness"], town.ore_tiles, " and ".join(str(t) for t in town.tunnels)), font=font, fill=(195, 200, 205))
    y += 42
    sheet.alpha_composite(close, (20, y))
    y += close.height + 8
    d.text((20, y), "The street at game scale, lit by its desert torches, chain lanterns and lamp posts; %d chests (barrels: bars, cogs, silver, "
           "potions, cowboy vanity 1 in 3; the bank vault's locked Brass Strongbox; the buried cache under a lamp post); vanilla furniture "
           "drawn as stand-ins" % len(town.chests), font=font, fill=(195, 200, 205))
    y += 42
    x = 20
    for s, t2, im in extra:
        sheet.alpha_composite(im, (x, y))
        d.text((x, y + im.height + 6), "seed %d: %s" % (s, ", ".join(b[0] for b in t2.built)), font=font, fill=(195, 200, 205))
        x += im.width + 20
    sheet.convert("RGB").save(out, optimize=True)
    print(out, sheet.size, "| built:", names, "| chests:", len(town.chests), "| ore:", town.ore_tiles, "| tunnels:", town.tunnels,
          "| skipped furniture:", town.skipped)
    return town


def blocks_png(out, font_path):
    font = ImageFont.truetype(font_path, 16)
    frames = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
    grid = ["...ssssss.....oooooo....pppppppp....bbbbbbb..",
            "..sssssssss..oooooooo..pppppppppp..bbbbbbbbb.",
            ".ssssssssss..ooooooooo.pppp..pppp..bbbbbbbbb.",
            ".sss..sssss...ooooooo..pppppppppp...bbbbbbb..",
            "..ssssssss.....ooooo....pppppppp.....bbbbb...",
            "...ssss.........ooo......pppppp.......bbb...."]
    sheets = {c: Image.open(os.path.join(ROOT, T + "Tiles/%sTile.png" % n)).convert("RGBA") for c, n in
              (("s", "BrassSandstone"), ("o", "TarnishedBrassOre"), ("p", "WeatheredPlank"), ("b", "TarnishedBrassPlating"))}
    blocks = render(grid, sheets, frames, background=(46, 40, 52), seed=2)
    walls = []
    mask = ["..########..", ".##########.", "############", "############", ".#####..####", "..###....##."]
    r = random.Random(3)
    for name in ("BrassSandstoneWallTile", "WeatheredPlankWallTile"):
        sheet = Image.open(os.path.join(ROOT, T + "Walls/%s.png" % name)).convert("RGBA")
        im = Image.new("RGBA", (12 * 16 + 16, 6 * 16 + 16), (46, 40, 52, 255))
        has = lambda x, y: 0 <= x < 12 and 0 <= y < 6 and mask[y][x] == "#"
        for y in range(6):
            for x in range(12):
                if not has(x, y):
                    continue
                st = (1 if has(x, y - 1) else 0) | (2 if has(x - 1, y) else 0) | (4 if has(x + 1, y) else 0) | (8 if has(x, y + 1) else 0)
                if st == 15:
                    st += CENTRE[x % 3][y % 3]
                fx, fy = WALL_LOOKUP[st][r.randrange(3)]
                im.alpha_composite(sheet.crop((fx * 36, fy * 36, fx * 36 + 32, fy * 36 + 32)), (x * 16, y * 16))
        walls.append(im)
    items = ["BrassSandstone", "TarnishedBrassOre", "WeatheredPlank", "TarnishedBrassPlating", "TarnishedBrassBar", "BrassSandstoneWall", "WeatheredPlankWall"]
    W = blocks.width * 2 + 40
    H = 40 + blocks.height * 2 + 40 + walls[0].height * 2 + 40 + 120
    out_im = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(out_im)
    d.text((20, 10), "Old Brass Town blocks (2x of the game's 16 px tiles): Brass Sandstone, Tarnished Brass Ore, Weathered Planks, "
           "Tarnished Brass Plating (vanilla terrain framing)", font=font, fill=(238, 241, 243))
    out_im.alpha_composite(blocks.resize((blocks.width * 2, blocks.height * 2), Image.NEAREST), (20, 40))
    y = 40 + blocks.height * 2 + 12
    d.text((20, y), "Walls (vanilla wall framing): Brass Sandstone Wall, Weathered Plank Wall (clapboard)", font=font, fill=(238, 241, 243))
    x = 20
    for im in walls:
        out_im.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.NEAREST), (x, y + 26))
        x += im.width * 2 + 30
    y += 26 + walls[0].height * 2 + 16
    x = 20
    for name in items:
        im = Image.open(os.path.join(ROOT, T + "Items/%s.png" % name)).convert("RGBA")
        out_im.alpha_composite(im.resize((im.width * 3, im.height * 3), Image.NEAREST), (x, y))
        x += max(im.width * 3, 60) + 26
    icon = Image.open(os.path.join(ROOT, T + "OldBrassTownBiome_Icon.png")).convert("RGBA")
    out_im.alpha_composite(icon.resize((icon.width * 3, icon.height * 3), Image.NEAREST), (x + 20, y))
    d.text((20, y + 96), "items at 3x: the four blocks, Tarnished Brass Bar, the two walls; the biome's bestiary icon", font=font, fill=(195, 200, 205))
    out_im.convert("RGB").save(out, optimize=True)
    print(out, out_im.size)


def chests_png(out, font_path, seed):
    """The D5 proof of the two chests (2026-11-04): the buried cache in its pocket under a lamp post and the bank
    vault's strongbox, cut out of a generated town (2x of game scale); the strongbox's frames; the key and the loot items."""
    k = constants(PASS)
    bps, order = blueprints()
    font, big = ImageFont.truetype(font_path, 16), ImageFont.truetype(font_path, 20)
    town = Town(k, bps, order, seed)
    assert town.cache and town.vault, "seed %d: no cache or no vault" % seed
    full = draw_town(town)
    lit = draw_town(town, lit=True)
    gx, gy = town.cache
    cut = full.crop(((gx - 10) * TILE, (town.floor - 9) * TILE, (gx + 12) * TILE, (town.floor + k["CacheDepth"] + k["CacheHeight"] + 4) * TILE))
    bank = next(b for b in town.built if b[0] == "Bank")
    vault = lit.crop(((bank[1] - 1) * TILE, (bank[2] - 1) * TILE, (bank[1] + bank[3] + 1) * TILE, (town.floor + 2) * TILE))
    cut, vault = (im.resize((im.width * 2, im.height * 2), Image.NEAREST) for im in (cut, vault))
    frames = [strongbox_sprite(locked, lid) for locked in (True, False) for lid in range(3)]
    icons = [T + "Items/SheriffsKey.png", T + "Items/BrassStrongbox.png", T + "Weapons/SheriffsRevolver.png", T + "Items/BrokenWhistle.png"]
    icons = [Image.open(os.path.join(ROOT, path)).convert("RGBA") for path in icons]
    lines = ["Old Brass Town's two chests (seed %d): the buried cache holds vanilla Gold Chest loot + the Sheriff's Key," % seed,
             "which opens the bank vault's locked Brass Strongbox (vanilla Gold Chest loot + the Sheriff's Revolver + a Broken Whistle)"]
    caption1 = ("Left, map-lit: the cache sealed %d rows under the street beneath a lamp post, two Weathered Planks over it the "
                "only hint. Right, torch-lit: the bank vault and its locked strongbox (2x of game scale)." % k["CacheDepth"])
    caption2 = ("3x: the strongbox locked (shut, ajar, open: vanilla's sheet layout; a locked chest never opens) and unlocked; "
                "the Sheriff's Key, the strongbox item, the Sheriff's Revolver, the Broken Whistle")
    row_w = sum(im.width * 3 + 14 for im in frames) + 26 + sum(im.width * 3 + 40 for im in icons)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    text_w = max(probe.textlength(t, font=f) for t, f in ((lines[0], big), (lines[1], big), (caption1, font), (caption2, font)))
    W = int(max(40 + cut.width + 20 + vault.width, 40 + row_w, 40 + text_w))
    H = 80 + max(cut.height, vault.height) + 50 + 34 * 3 + 70
    sheet = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sheet)
    d.text((20, 10), lines[0], font=big, fill=(238, 241, 243))
    d.text((20, 36), lines[1], font=big, fill=(238, 241, 243))
    y = 70
    sheet.alpha_composite(cut, (20, y))
    sheet.alpha_composite(vault, (20 + cut.width + 20, y))
    y += max(cut.height, vault.height) + 8
    d.text((20, y), caption1, font=font, fill=(195, 200, 205))
    y += 36
    x = 20
    for k2, im in enumerate(frames):
        sheet.alpha_composite(im.resize((im.width * 3, im.height * 3), Image.NEAREST), (x, y))
        x += im.width * 3 + (40 if k2 == 2 else 14)
    for im in icons:
        sheet.alpha_composite(im.resize((im.width * 3, im.height * 3), Image.NEAREST), (x + 10, y + 51 - im.height * 3 // 2))
        x += im.width * 3 + 40
    d.text((20, y + 34 * 3 + 12), caption2, font=font, fill=(195, 200, 205))
    sheet.convert("RGB").save(out, optimize=True)
    print(out, sheet.size, "| cache at", town.cache, "| vault at", town.vault)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--seed", type=int, default=7)
    a.add_argument("--check", action="store_true")
    a.add_argument("--sweep", type=int, default=0, help="generate this many seeds on each world size and report what didn't fit")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a.add_argument("--chests", action="store_true", help="only the strongbox / buried cache proof")
    args = a.parse_args()
    bps, order = blueprints()
    bad = 0
    for name in order:
        errs = check_blueprint(bps.get(name, []))
        rows = bps.get(name, [""])
        print("[%s] %-10s %dx%d" % ("ok" if not errs else "FAIL", name, len(rows[0]), len(rows)))
        for e in errs:
            print("    " + e)
        bad += len(errs)
    if bad or args.check:
        sys.exit(1 if bad else 0)
    if args.sweep:
        k = constants(PASS)
        for hive, label in ((320, "small"), (484, "medium"), (640, "large")):
            counts, skipped, spikes, vaults, caches = {}, 0, 0, 0, 0
            for s in range(args.sweep):
                t = Town(k, bps, order, s, hive)
                counts[len(t.built)] = counts.get(len(t.built), 0) + 1
                skipped += len(t.skipped)
                spikes += t.spikes
                vaults += t.vault is not None
                caches += t.cache is not None
            print("%s world (hive %d): %dx%d cavern; buildings built per seed %s; furniture skipped %d; stalactites %.1f a town; "
                  "strongbox %d/%d, buried cache %d/%d" % (label, hive, t.width, t.height, dict(sorted(counts.items())), skipped,
                                                          spikes / args.sweep, vaults, args.sweep, caches, args.sweep))
        for hive in (140, 180, 240):                      # the smallest deserts the town accepts (MinHiveWidth)
            vaults = caches = 0
            for s in range(args.sweep):
                t = Town(k, bps, order, s, hive)
                vaults += t.vault is not None
                caches += t.cache is not None
            print("hive %d: %dx%d cavern; strongbox %d/%d, buried cache %d/%d" % (hive, t.width, t.height, vaults, args.sweep, caches, args.sweep))
        sys.exit(0)
    if args.chests:
        chests_png(os.path.join(args.out, "2026-11-04_oldbrasstown-chests.png"), args.font, args.seed)
        return
    town_png(os.path.join(args.out, "2026-11-04_oldbrasstown-town.png"), args.font, args.seed)
    blocks_png(os.path.join(args.out, "2026-11-03_oldbrasstown-blocks.png"), args.font)


if __name__ == "__main__":
    main()
