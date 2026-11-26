"""D5 proofs for Coghaven (2026-11-06): replays Content/Coghaven/Generation/CoghavenPass.cs step for step (its constants
parsed from the C#, the blueprints read from the generated CoghavenBlueprints.cs) and renders the island with the real
sprite sheets; animates the Lift Turbines' smoke (TurbineSmoke.cs replayed) and the Bronze Cogs; sweeps world sizes to
show the island always finds room in the sky.

    python -P tools/sim/coghaven_sim.py --out docs/media [--only island,underside,sweep] [--seed N]

Writes:
    2026-11-12_coghaven-island.png      the whole island at half scale over the sky (the palace, the cloud-and-cog base,
                                        the turbines), and a full-scale crop of the Main Hall and the pagoda.
    2026-11-06_coghaven-underside.gif   half scale: the turbines' rotors turning and their smoke pouring down, the cogs
                                        turning in their sockets (5 s).
    (stdout) the sweep: for each world size and terrain height, the pagoda and base depth the pass picks, or a skip.

Leaves out: lighting (drawn in daylight), vanilla's own art (the repo has none: clouds, dirt, grass, gold brick, Dynasty
furniture, the throne, the boiler and the sakura trees are flat stand-ins in their colours), tile slopes are drawn as cut
triangles of the real frames, liquids settle as placed, the vanilla islands the site pass moves, netcode. The terrain
under the island is a flat line at the chosen obstacle row.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from terrain import load_frames  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
C = "Content/Coghaven/"
PASS = C + "Generation/CoghavenPass.cs"
BLUEPRINTS = C + "Generation/CoghavenBlueprints.cs"
TILE, STRIDE = 16, 18


def constants(*paths):
    """`const int/float/double NAME = value;` (and comma lists) from C# files."""
    out = {}
    for path in paths:
        src = open(os.path.join(ROOT, path), encoding="utf-8").read()
        for m in re.finditer(r"const (?:int|float|double) ([^;]+);", src):
            for part in m.group(1).split(","):
                if "=" in part:
                    k, v = (x.strip() for x in part.split("=", 1))
                    v = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
                    v = re.sub(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", r"\1", v)
                    try:
                        out[k] = eval(v, {}, dict(out))
                    except Exception:
                        pass
    return out


def blueprints():
    src = open(os.path.join(ROOT, BLUEPRINTS), encoding="utf-8").read()
    plans = {}
    for m in re.finditer(r"public static readonly string\[\] (\w+) = \{(.*?)\};", src, re.S):
        plans[m.group(1)] = [r.replace("\\\\", "\\") for r in re.findall(r'"((?:[^"\\]|\\.)*)",', m.group(2))]
    arrays = {}
    for m in re.finditer(r"public static readonly int\[\] (\w+) = \{([^}]*)\};", src):
        arrays[m.group(1)] = [int(v) for v in m.group(2).split(",") if v.strip()]
    return plans, arrays


K = constants(PASS, BLUEPRINTS, C + "Generation/CoghavenSitePass.cs", C + "Tiles/LiftTurbineTile.cs", C + "Tiles/BronzeCogTile.cs",
              C + "Dusts/TurbineSmoke.cs")
PLANS, ARR = blueprints()
W = K["IslandWidth"]


# ================================================================================================
# The pass, replayed
# ================================================================================================
class Island:
    def __init__(self, obstacle, seed):
        """obstacle: the first occupied row under each column of the band (a list of W + 48: the island's home columns
        start at 24), or one row for all."""
        self.rng = random.Random(seed)
        self.band = obstacle if isinstance(obstacle, list) else [obstacle] * (W + 48)
        self.obstacle = self.band[24:24 + W]
        self.shift = 0
        self.tile = {}                       # (x, y) -> kind
        self.shape = {}                      # (x, y) -> "slopeL" / "slopeR" / "half"
        self.wall = {}                       # (x, y) -> wall kind
        self.water = set()
        self.multi = []                      # (kind, x, y, w, h, style)
        self.pieces = []                     # (char, x, y)
        self.lamps, self.trees = [], []
        self.ok = self.choose()

    # --- heights
    def above(self, pagoda):
        return max(len(PLANS["Gate"]), len(PLANS["MainHall"]), len(pagoda), len(PLANS["Pavilion"])) - 1

    def below(self, i, d, with_turbine=True):
        """CoghavenPass.Below: the rows the island hangs under its surface in column i."""
        u = (i + 0.5 - W / 2) / (W / 2)
        body = max(int(round(d * max(0.0, 1 - u * u) ** K["BottomExponent"])) + K["BottomNoise"], K["MinThickness"])
        turbine = K["Height"] + 1 + K["BottomNoise"] if with_turbine and self.in_turbine_cols(i, 0) else 0
        return body + max(turbine, K["PuffReach"])

    def choose(self):
        """CoghavenPass.ChooseSite + ChooseHeights."""
        for room in (K["MinClearance"], K["LastClearance"]):
            for shift in (0, -12, 12, -24, 24):
                self.shift = shift
                cols = self.band[24 + shift:24 + shift + W]
                self.obstacle = [min(cols[max(0, i - 1):i + 2]) for i in range(W)]
                if self.heights(room):
                    return True
        self.shift = 0
        return False

    def heights(self, room):
        self.kept = None
        if True:
            for name in ("Pagoda5", "Pagoda4", "Pagoda3", "Pagoda2"):
                pagoda = PLANS[name]
                d = K["BaseDepth"]
                while d >= K["MinBaseDepth"]:
                    s_min = K["TopLimit"] + self.above(pagoda)
                    s_max = min(self.obstacle[i] - room - self.below(i, d, False) for i in range(W))
                    preferred = min(self.obstacle[i] - K["PreferredClearance"] - self.below(i, d, True) for i in range(W))
                    if s_min <= s_max:
                        self.depth, self.pagoda, self.pagoda_name, self.clearance = d, pagoda, name, room
                        self.s = max(s_min, min(s_max, preferred))
                        self.kept = [all(self.s + self.below(c, d, True) <= self.obstacle[c] - room for c in range(tx, tx + 4))
                                     for tx in ARR["TurbineX"]]
                        return True
                    d -= K["DepthStep"]
        return False

    # --- the base
    def noise(self, count, amp):
        step = K["NoiseStep"]
        control = [(self.rng.random() * 2 - 1) * amp for _ in range(count // step + 2)]
        return [control[i // step] + (control[i // step + 1] - control[i // step]) * ((i % step) / step) for i in range(count)]

    def profile(self):
        s, d = self.s, self.depth
        nz = self.noise(W, K["BottomNoise"])
        self.top, self.bottom = [0] * W, [0] * W
        for i in range(W):
            u = (i + 0.5 - W / 2) / (W / 2)
            a = abs(u)
            drop = int(round(((a - K["FlatTop"]) / (1 - K["FlatTop"])) ** 2 * K["EdgeDrop"])) if a > K["FlatTop"] else 0
            self.top[i] = s + drop
            dd = int(round(d * max(0.0, 1 - u * u) ** K["BottomExponent"] + nz[i]))
            self.bottom[i] = max(self.top[i] + K["MinThickness"], s + dd)
            if K["PondLeft"] - 1 <= i <= K["PondRight"] + 1:
                self.bottom[i] = max(self.bottom[i], s + K["PondDepth"] + 2)   # cloud under the pond's lining (2026-11-12)
        for k, tx in enumerate(ARR["TurbineX"]):
            if not self.kept[k]:
                continue
            m = max(self.bottom[tx:tx + 4])
            for c in range(tx, tx + 4):
                self.bottom[c] = m

    def in_core(self, i, y):
        dx = abs(i + 0.5 - W / 2) / K["CoreRx"]
        dy = abs(y - (self.s + K["CoreDepth"])) / K["CoreRy"]
        return dx ** K["CoreExponent"] + dy ** K["CoreExponent"] <= 1.0

    def in_turbine_cols(self, i, margin):
        kept = getattr(self, "kept", None)
        return any((kept is None or kept[k]) and tx - margin <= i < tx + 4 + margin for k, tx in enumerate(ARR["TurbineX"]))

    def base(self):
        s = self.s
        for i in range(W):
            terrace = ARR and K["TerraceLeft"] <= i <= K["TerraceRight"]
            keel = abs(i + 0.5 - W / 2) <= K["KeelHalfWidth"]
            for y in range(self.top[i], self.bottom[i] + 1):
                if y < self.top[i] + K["SoilRows"]:
                    if terrace:
                        self.tile[(i, y)] = "stone"                 # Palace Flagstone (2026-11-06, second request)
                        if y > self.top[i]:
                            self.wall[(i, y)] = "stonew"
                    else:
                        self.tile[(i, y)] = "grass" if y == self.top[i] else "dirt"
                elif (self.in_core(i, y) and y <= self.bottom[i] - K["CoreSkin"]) or (keel and y >= s + K["SoilRows"] + 1) \
                        or (self.in_turbine_cols(i, 0) and y > self.bottom[i] - K["MountRows"]):
                    self.tile[(i, y)] = "gear"
                    self.wall[(i, y)] = "gearw"
                else:
                    self.tile[(i, y)] = "cloud"
        for i in range(1, W - 1):
            for y in range(self.top[i] + 1, self.bottom[i]):
                if self.tile.get((i, y)) != "cloud":
                    continue
                if all(0 <= i + dx < W and self.top[i + dx] <= y + dy <= self.bottom[i + dx] for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    self.wall[(i, y)] = "cloudw"

    def blob(self, ci, cy, r, kind, under):
        reach = int(math.ceil(r)) + 1
        for dx in range(-reach, reach + 1):
            i = ci + dx
            if i < 0 or i >= W or self.in_turbine_cols(i, 2):
                continue
            for dy in range(-reach, reach + 1):
                y = cy + dy
                if dx * dx + dy * dy * 1.6 > r * r or (under and y <= self.bottom[i]) or (not under and y >= self.top[i]):
                    continue
                if (i, y) not in self.tile and (i, y) not in self.wall:
                    self.tile[(i, y)] = kind

    def puffs(self):
        for _ in range(K["CloudPuffs"]):
            i = self.rng.randrange(W)
            r = 2.0 + self.rng.random() * 2.5
            kind = "rain" if self.rng.randrange(K["RainCloudOneIn"]) == 0 else "cloud"
            self.blob(i, self.bottom[i] - 1 + int(r * 0.3), r, kind, True)
        for p in range(K["TipTufts"]):
            i = self.rng.randrange(0, 6) if p % 2 == 0 else self.rng.randrange(W - 6, W)
            self.blob(i, self.top[i], 1.5 + self.rng.random() * 1.5, "cloud", False)

    def pond(self):
        s = self.s
        for i in range(K["PondLeft"] - 1, K["PondRight"] + 2):
            for y in range(s, s + K["PondDepth"] + 1):
                if y < self.top[i]:
                    continue
                self.tile.pop((i, y), None)
                self.wall.pop((i, y), None)
                if i in (K["PondLeft"] - 1, K["PondRight"] + 1) or y == s + K["PondDepth"]:
                    self.tile[(i, y)] = "stone"
                else:
                    self.water.add((i, y))

    def sockets(self):
        size = K["Size"]
        for i0, style, lift in zip(ARR["CogSocketX"], ARR["CogSocketStyle"], ARR["CogSocketLift"]):
            sb = min(self.bottom[i0:i0 + size]) - lift
            sy = sb - (size - 1)
            if not all(sy > self.top[c] + K["SoilRows"] and sb + 1 <= self.bottom[c] for c in range(i0, i0 + size)):
                continue
            if any(K["PondLeft"] - 1 <= c <= K["PondRight"] + 1 for c in range(i0, i0 + size)) and sy <= self.s + K["PondDepth"] + 1:
                continue                                         # never into the pond (2026-11-12)
            vx0, vx1 = K["MainHallX"] + K["VaultLeft"] - 1, K["MainHallX"] + K["VaultRight"] + 1
            vy0, vy1 = self.s + K["VaultTop"] - 1, self.s + K["VaultFloor"] + 1
            if i0 <= vx1 and i0 + size - 1 >= vx0 and sy <= vy1 and sb >= vy0:
                continue                                         # CoghavenPass.TouchesVault (2026-11-16): never cut by the vault
            for c in range(i0, i0 + size):
                for y in range(sy, sb + 1):
                    self.tile.pop((c, y), None)
                    self.wall[(c, y)] = "gearw"
            for c in (i0 + 2, i0 + 3):
                self.tile.setdefault((c, sb + 1), "gear")
            self.multi.append(("cog", i0, sy, size, size, style))

    def turbines(self):
        for k, tx in enumerate(ARR["TurbineX"]):
            if not self.kept[k]:
                continue
            m = self.bottom[tx]
            if all(self.tile.get((c, m)) is not None and all((c, y) not in self.tile for y in range(m + 1, m + 7)) for c in range(tx, tx + 4)):
                self.multi.append(("turbine", tx, m + 1, 4, 6, 0))

    def plan(self, rows, x0, y0):
        for by, row in enumerate(rows):
            for bx, ch in enumerate(row):
                if ch == " ":
                    continue
                x, y = x0 + bx, y0 + by
                self.tile.pop((x, y), None)
                self.shape.pop((x, y), None)
                self.water.discard((x, y))
                blocks = {"F": ("stone", "stonew"), "f": ("stone", None), "J": ("jade", "jadew"), "j": ("jade", None),
                          "R": ("lacquer", "panel"), "r": ("lacquer", None),
                          "G": ("gear", "gearw"), "g": ("gear", None), "T": ("roof", None), "Y": ("gold", None),
                          "X": ("vault", "vaultw"), "x": ("vault", None)}      # 2026-11-16: the Jade Vault's shell
                if ch in blocks:
                    kind, wall = blocks[ch]
                    self.tile[(x, y)] = kind
                    if wall:
                        self.wall[(x, y)] = wall
                elif ch in "/\\()-":
                    self.tile[(x, y)] = "stone" if ch in "()" else "roof"
                    self.shape[(x, y)] = {"/": "up_right", "(": "up_right", "\\": "up_left", ")": "up_left", "-": "half"}[ch]
                elif ch in ".,:#;m":
                    self.wall[(x, y)] = {".": "panel", ",": "stonew", ":": "gearw", "#": "lattice", ";": "vaultw", "m": "plaster"}[ch]
                elif ch in "=+%$":
                    self.tile[(x, y)] = "plat"
                    if ch == "=":
                        self.wall[(x, y)] = "panel"
                    elif ch == "%":
                        self.wall[(x, y)] = "gearw"
                    elif ch == "$":
                        self.wall[(x, y)] = "vaultw"
                elif ch in "w~":
                    self.water.add((x, y))
                    if ch == "~":
                        self.wall[(x, y)] = "stonew"
                else:
                    wall = self.wall.get((x, y))                # CoghavenPass.RoomWall: the neighbours' wall, else the cell's own
                    for nx, ny in ((bx - 1, by), (bx + 1, by), (bx, by - 1), (bx, by + 1)):
                        if 0 <= ny < len(rows) and 0 <= nx < len(rows[ny]) and rows[ny][nx] in ".,:#;m":
                            wall = {".": "panel", ",": "stonew", ":": "gearw", "#": "lattice", ";": "vaultw", "m": "plaster"}[rows[ny][nx]]
                            break
                    if wall:
                        self.wall[(x, y)] = wall
                    self.pieces.append((ch, x, y))

    def furnish(self):
        for ch, x, y in self.pieces:
            if ch in "Zz":
                if all((x + dx, y + dy) not in self.tile for dx in range(6) for dy in range(6)) and \
                        all(self.tile.get((x + dx, y + 6)) not in (None, "plat") for dx in (2, 3)):
                    self.multi.append(("cog", x, y, 6, 6, 1 if ch == "z" else 0))
        for lx in ARR["LampX"]:
            if (lx, self.top[lx] - 1) not in self.tile:
                self.lamps.append((lx, self.top[lx] - 1))
        for tx in ARR["TreeX"]:
            if self.tile.get((tx, self.top[tx])) == "grass":
                self.trees.append((tx, self.top[tx]))

    def generate(self):
        if not self.ok:
            return False
        s = self.s
        self.profile()
        self.base()
        self.puffs()
        self.pond()
        self.sockets()
        self.turbines()
        self.plan(PLANS["Vault"], K["MainHallX"], s)      # 2026-11-16: the Jade Vault (was the engine deck)
        self.plan(PLANS["Gate"], K["GateX"], s - (len(PLANS["Gate"]) - 1))
        self.plan(PLANS["MainHall"], K["MainHallX"], s - (len(PLANS["MainHall"]) - 1))
        self.plan(self.pagoda, K["PagodaX"], s - (len(self.pagoda) - 1))
        self.plan(PLANS["Pavilion"], K["PavilionX"], s - (len(PLANS["Pavilion"]) - 1))
        self.furnish()
        return True


# ================================================================================================
# Rendering
# ================================================================================================
WALL_LOOKUP = {0: ((9, 3), (10, 3), (11, 3)), 1: ((6, 3), (7, 3), (8, 3)), 2: ((12, 0), (12, 1), (12, 2)), 3: ((1, 4), (3, 4), (5, 4)),
               4: ((9, 0), (9, 1), (9, 2)), 5: ((0, 4), (2, 4), (4, 4)), 6: ((6, 4), (7, 4), (8, 4)), 7: ((1, 2), (2, 2), (3, 2)),
               8: ((6, 0), (7, 0), (8, 0)), 9: ((5, 0), (5, 1), (5, 2)), 10: ((1, 3), (3, 3), (5, 3)), 11: ((4, 0), (4, 1), (4, 2)),
               12: ((0, 3), (2, 3), (4, 3)), 13: ((0, 0), (0, 1), (0, 2)), 14: ((1, 0), (2, 0), (3, 0)), 15: ((1, 1), (2, 1), (3, 1)),
               16: ((6, 1), (7, 1), (8, 1)), 17: ((6, 2), (7, 2), (8, 2)), 18: ((10, 0), (10, 1), (10, 2)), 19: ((11, 0), (11, 1), (11, 2))}
CENTRE = [[2, 0, 0], [0, 1, 4], [0, 3, 0]]
BLOCK_SHEETS = {"stone": "PalaceFlagstone", "jade": "JadeBrick", "lacquer": "CinnabarLacquer", "gear": "BronzeGearwork", "roof": "JadeRoof",
                "vault": "VaultGearwork"}
WALL_SHEETS = {"stonew": "PalaceFlagstoneWall", "jadew": "JadeBrickWall", "panel": "CinnabarPanelWall", "lattice": "BronzeLatticeWall",
               "gearw": "BronzeGearworkWall", "vaultw": "VaultGearworkWall"}
STAND_IN = {"cloud": (236, 240, 246), "rain": (164, 172, 186), "dirt": (151, 107, 75), "grass": (151, 107, 75), "gold": (214, 176, 66)}


def load(path):
    return Image.open(os.path.join(ROOT, path)).convert("RGBA")


def stand_in_sheet(base, seed, grass=False):
    """A terrain sheet for a vanilla block the repo has no art for: speckled squares, a darker rim on exposed sides
    (grass: a green top on exposed tops)."""
    frames = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
    sheet = Image.new("RGBA", (16 * STRIDE, 15 * STRIDE), (0, 0, 0, 0))
    r = random.Random(seed)
    for signature, cells in frames.items():
        for (fx, fy) in cells:
            tile = Image.new("RGBA", (TILE, TILE))
            d = ImageDraw.Draw(tile)
            for py in range(0, TILE, 2):
                for px in range(0, TILE, 2):
                    v = r.choice((-8, 0, 0, 6))
                    d.rectangle([px, py, px + 1, py + 1], fill=tuple(max(0, min(255, c + v)) for c in base) + (255,))
            dark = tuple(int(c * 0.72) for c in base) + (255,)
            top, right, bottom, left = (ch == "o" for ch in signature)
            if grass and top:
                d.rectangle([0, 0, TILE - 1, 5], fill=(56, 160, 70, 255))
                d.rectangle([0, 0, TILE - 1, 1], fill=(36, 110, 50, 255))
            elif top:
                d.rectangle([0, 0, TILE - 1, 1], fill=dark)
            if bottom:
                d.rectangle([0, TILE - 2, TILE - 1, TILE - 1], fill=dark)
            if left:
                d.rectangle([0, 0, 1, TILE - 1], fill=dark)
            if right:
                d.rectangle([TILE - 2, 0, TILE - 1, TILE - 1], fill=dark)
            sheet.alpha_composite(tile, (fx * STRIDE, fy * STRIDE))
    return sheet


FURNITURE = {  # (left, top) offset in tiles from the anchor cell, (w, h) in tiles, colour, label
    "C": ((0, -1), (2, 2), (150, 36, 30)), "Q": ((0, -1), (2, 2), (214, 176, 66)), "<": ((0, -1), (1, 2), (120, 40, 34)),
    ">": ((0, -1), (1, 2), (120, 40, 34)), "A": ((-1, -1), (3, 2), (110, 40, 30)), "B": ((-1, -3), (3, 4), (96, 36, 28)),
    "S": ((-1, -1), (3, 2), (120, 40, 34)), "P": ((-1, -1), (3, 2), (60, 30, 26)), "K": ((0, -4), (2, 5), (110, 40, 30)),
    "N": ((-1, -3), (3, 4), (214, 176, 66)), "U": ((-1, -2), (3, 3), (184, 138, 51)), "I": ((0, -2), (1, 3), (150, 36, 30)),
    "V": ((0, -1), (2, 2), (214, 176, 66)), "i": ((0, 0), (1, 1), (240, 220, 160)), "L": ((0, 0), (1, 2), (206, 60, 40)),
    "^": ((0, 0), (1, 2), (184, 138, 51)), "O": ((0, 0), (2, 2), (220, 50, 40)), "H": ((-1, 0), (3, 3), (214, 176, 66)),
}


CHEST_STYLE = {"C": 0, "Q": 1, "&": 2}   # the Pagoda Chest (2026-11-17), the Locked Pagoda Chest and the Jade Vault (2026-11-16)


def furniture_sprite(ch):
    if ch in CHEST_STYLE:
        sheet = load(C + "Tiles/CoghavenChestTile.png")
        im = Image.new("RGBA", (2 * TILE, 2 * TILE), (0, 0, 0, 0))
        for ty in range(2):
            for tx in range(2):
                sx, sy = (CHEST_STYLE[ch] * 2 + tx) * STRIDE, ty * STRIDE
                im.alpha_composite(sheet.crop((sx, sy, sx + TILE, sy + TILE)), (tx * TILE, ty * TILE))
        return im, 0, -1
    (ox, oy), (w, h), col = FURNITURE[ch]
    im = Image.new("RGBA", (w * TILE, h * TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dark = tuple(int(c * 0.55) for c in col) + (255,)
    lit = tuple(min(255, int(c * 1.25)) for c in col) + (255,)
    if ch in "LO^":
        d.line([w * TILE // 2 - 1, 0, w * TILE // 2 - 1, 5], fill=dark, width=2)
        d.ellipse([2, 6, w * TILE - 3, h * TILE - 2], fill=col + (255,), outline=dark)
        d.rectangle([w * TILE // 2 - 3, h * TILE // 2, w * TILE // 2 + 1, h * TILE // 2 + 3], fill=(255, 220, 140, 255))
    elif ch == "H":
        d.line([24, 0, 24, 10], fill=dark, width=2)
        d.rectangle([4, 12, 43, 18], fill=col + (255,), outline=dark)
        for cx in (6, 22, 38):
            d.rectangle([cx, 6, cx + 3, 12], fill=(255, 230, 150, 255))
    elif ch in "IV":
        d.rectangle([w * TILE // 2 - 2, 8, w * TILE // 2 + 1, h * TILE - 1], fill=dark)
        d.rectangle([2, 0, w * TILE - 3, 9], fill=(255, 210, 120, 255), outline=dark)
    else:
        d.rectangle([0, 0, w * TILE - 1, h * TILE - 1], fill=col + (255,), outline=dark)
        d.line([2, 2, w * TILE - 3, 2], fill=lit)
        if ch in "CQ":
            d.rectangle([w * TILE // 2 - 3, h * TILE // 2 - 2, w * TILE // 2 + 2, h * TILE // 2 + 3], fill=(250, 230, 150, 255))
    return im, ox, oy


def assemble(sheet, cols, rows, frame, style=0):
    out = Image.new("RGBA", (cols * TILE, rows * TILE), (0, 0, 0, 0))
    for ty in range(rows):
        for tx in range(cols):
            sx = (style * cols + tx) * STRIDE
            sy = frame * rows * STRIDE + ty * STRIDE
            out.alpha_composite(sheet.crop((sx, sy, sx + TILE, sy + TILE)), (tx * TILE, ty * TILE))
    return out


class Renderer:
    def __init__(self, island):
        self.isl = island
        self.frames = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
        self.sheets = {k: load(C + "Tiles/%sTile.png" % v) for k, v in BLOCK_SHEETS.items()}
        self.sheets["cloud"] = stand_in_sheet(STAND_IN["cloud"], 1)
        self.sheets["rain"] = stand_in_sheet(STAND_IN["rain"], 2)
        self.sheets["dirt"] = stand_in_sheet(STAND_IN["dirt"], 3)
        self.sheets["grass"] = stand_in_sheet(STAND_IN["grass"], 4, grass=True)
        self.sheets["gold"] = stand_in_sheet(STAND_IN["gold"], 5)
        self.walls = {k: load(C + "Walls/%sTile.png" % v) for k, v in WALL_SHEETS.items()}
        plaster = Image.new("RGBA", self.walls["panel"].size, (226, 222, 206, 255))   # vanilla White Dynasty Wall: a stand-in
        self.walls["plaster"] = plaster
        self.cog = load(C + "Tiles/BronzeCogTile.png")
        self.turbine = load(C + "Tiles/LiftTurbineTile.png")
        self.turbine_glow = load(C + "Tiles/LiftTurbineTile_Glow.png")
        self.smoke = load(C + "Dusts/TurbineSmoke.png")
        xs = [x for (x, _) in list(island.tile) + list(island.wall)] + [0, W - 1]
        ys = [y for (_, y) in list(island.tile) + list(island.wall)]
        self.x0, self.x1 = min(xs) - 4, max(xs) + 4
        self.y0, self.y1 = min(ys) - 14, max(ys) + 22
        self.static = self.draw_static()

    def px(self, x, y):
        return (x - self.x0) * TILE, (y - self.y0) * TILE

    def same(self, a, b):
        kinds = {"grass": "dirt"}
        return kinds.get(a, a) == kinds.get(b, b)

    def draw_static(self):
        isl = self.isl
        w, h = (self.x1 - self.x0 + 1) * TILE, (self.y1 - self.y0 + 1) * TILE
        img = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(img)
        for y in range(h):
            t = y / h
            d.line([0, y, w, y], fill=(int(96 + 70 * t), int(150 + 50 * t), int(214 + 25 * t), 255))
        rng = random.Random(3)
        for (x, y), kind in isl.wall.items():           # walls (vanilla's frame lookup)
            if kind == "cloudw":
                X, Y = self.px(x, y)
                d.rectangle([X, Y, X + 15, Y + 15], fill=(204, 210, 220, 255))
                continue
            has = lambda ax, ay: (ax, ay) in isl.wall
            st = (1 if has(x, y - 1) else 0) | (2 if has(x - 1, y) else 0) | (4 if has(x + 1, y) else 0) | (8 if has(x, y + 1) else 0)
            if st == 15:
                st += CENTRE[x % 3][y % 3]
            fx, fy = WALL_LOOKUP[st][rng.randrange(3)]
            X, Y = self.px(x, y)
            img.alpha_composite(self.walls[kind].crop((fx * 36, fy * 36, fx * 36 + 32, fy * 36 + 32)), (X - 8, Y - 8))
        for (x, y) in isl.water:
            X, Y = self.px(x, y)
            d.rectangle([X, Y, X + 15, Y + 15], fill=(52, 104, 190, 255))
            if (x, y - 1) not in isl.water:
                d.line([X, Y + 1, X + 15, Y + 1], fill=(120, 170, 230, 255), width=2)
        for (x, y), kind in isl.tile.items():           # blocks (terrain framing, slopes cut)
            if kind == "plat":
                continue
            X, Y = self.px(x, y)
            sig = "".join("-" if self.same(isl.tile.get((x + dx, y + dy)), kind) and isl.tile.get((x + dx, y + dy)) != "plat" else "o"
                          for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
            fx, fy = rng.choice(self.frames[sig])
            cell = self.sheets[kind].crop((fx * STRIDE, fy * STRIDE, fx * STRIDE + TILE, fy * STRIDE + TILE))
            shape = isl.shape.get((x, y))
            if shape:
                mask = Image.new("L", (TILE, TILE), 0)
                md = ImageDraw.Draw(mask)
                if shape == "up_right":
                    md.polygon([(0, TILE), (TILE, 0), (TILE, TILE)], fill=255)
                elif shape == "up_left":
                    md.polygon([(0, 0), (TILE, TILE), (0, TILE)], fill=255)
                else:
                    md.rectangle([0, TILE // 2, TILE, TILE], fill=255)
                cut = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
                cut.paste(cell, (0, 0), mask)
                cell = cut
            img.alpha_composite(cell, (X, Y))
        plat = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        pd = ImageDraw.Draw(plat)
        pd.rectangle([0, 0, 15, 5], fill=(126, 30, 36, 255))
        pd.line([0, 0, 15, 0], fill=(206, 74, 56, 255), width=2)
        pd.rectangle([0, 4, 15, 5], fill=(214, 176, 66, 255))
        for (x, y), kind in isl.tile.items():
            if kind == "plat":
                img.alpha_composite(plat, self.px(x, y))
        for ch, x, y in isl.pieces:                     # furniture stand-ins
            if ch in "Zz":
                continue
            sprite, ox, oy = furniture_sprite(ch)
            X, Y = self.px(x + ox, y + oy)
            img.alpha_composite(sprite, (X, Y))
        for (lx, ly) in isl.lamps:
            sprite, ox, oy = furniture_sprite("I")
            X, Y = self.px(lx + ox, ly + oy)
            img.alpha_composite(sprite, (X, Y))
        for (tx, ty) in isl.trees:                      # sakura stand-ins
            X, Y = self.px(tx, ty)
            d.rectangle([X + 5, Y - 9 * TILE, X + 10, Y], fill=(110, 70, 50, 255))
            d.ellipse([X - 34, Y - 15 * TILE, X + 50, Y - 8 * TILE], fill=(236, 150, 190, 255), outline=(180, 90, 130, 255))
        return img

    def frame(self, tick, smoke=()):
        img = self.static.copy()
        cog_frame = (tick // K["TicksPerFrame"] if False else (tick // 8)) % 12
        tur_frame = (tick // 4) % 4
        for kind, x, y, w, h, style in self.isl.multi:
            X, Y = self.px(x, y)
            if kind == "cog":
                f = cog_frame if style == 0 else 11 - cog_frame
                img.alpha_composite(assemble(self.cog, 6, 6, f), (X, Y))
            else:
                img.alpha_composite(assemble(self.turbine, 4, 6, tur_frame), (X, Y))
                img.alpha_composite(assemble(self.turbine_glow, 4, 6, tur_frame), (X, Y))
        for (sx, sy, age) in smoke:
            k = 0 if age < 12 else 1 if age < 30 else 2 if age < 56 else 3
            alpha = 255 if age < K["Lifetime"] * 0.45 else int(255 * (1 - (age - K["Lifetime"] * 0.45) / (K["Lifetime"] * 0.55)))
            puff = self.smoke.crop((0, k * 20, 20, k * 20 + 20))
            if alpha < 255:
                a = puff.split()[3].point(lambda v: v * alpha // 255)
                puff.putalpha(a)
            img.alpha_composite(puff, (int(sx - self.x0 * TILE - 10), int(sy - self.y0 * TILE - 10)))
        return img


class Smoke:
    """TurbineSmoke.Update, step for step (positions in world px)."""

    def __init__(self, rng):
        self.rng, self.puffs = rng, []

    def emit(self, island):
        for kind, x, y, w, h, style in island.multi:
            if kind != "turbine" or self.rng.randrange(K["SmokeOneIn"]) != 0:
                continue
            nx, ny = (x + 1) * TILE + 16, (y + 5) * TILE + 14
            self.puffs.append([nx - 6 + self.rng.random() * 12, ny + self.rng.random() * 4, self.rng.uniform(-0.6, 0.6),
                               self.rng.uniform(1.3, 2.1), 0])

    def step(self):
        for p in self.puffs:
            p[4] += 1
            p[0] += p[2]
            p[1] += p[3]
            p[3] = p[3] * 0.985 + 0.004
            p[2] *= 0.99
            if p[4] % 24 == 0:
                p[2] += self.rng.uniform(-0.12, 0.12)
        self.puffs = [p for p in self.puffs if p[4] < K["Lifetime"]]

    def view(self):
        return [(p[0], p[1], p[4]) for p in self.puffs]


def text(img, xy, s, font, fill=(238, 241, 243)):
    d = ImageDraw.Draw(img)
    for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        d.text((xy[0] + ox, xy[1] + oy), s, fill=(21, 22, 28), font=font)
    d.text(xy, s, fill=fill, font=font)


def island_png(out, font_path, seed):
    isl = Island(obstacle=300, seed=seed)
    isl.generate()
    r = Renderer(isl)
    full = r.frame(200)
    half = full.resize((full.width // 2, full.height // 2), Image.NEAREST)
    font = ImageFont.truetype(font_path, 15)
    big = ImageFont.truetype(font_path, 22)
    # a full-scale crop: the Main Hall and the pagoda
    cx0, cx1 = (K["MainHallX"] - 2 - r.x0) * TILE, (K["PagodaX"] + 29 - r.x0) * TILE
    top_row = min(y for (_, y) in isl.tile) - 2
    cy0, cy1 = (top_row - r.y0) * TILE, (isl.s + 24 - r.y0) * TILE
    crop = full.crop((cx0, cy0, cx1, cy1))
    sheet = Image.new("RGBA", (max(half.width, crop.width), half.height + crop.height + 40), (30, 30, 40, 255))
    sheet.alpha_composite(half, (0, 0))
    sheet.alpha_composite(crop, (0, half.height + 40))
    text(sheet, (12, 10), "Coghaven: %d tiles wide (vanilla's cloud islands 100-150), a %d-deep base of cloud and cogs, five Lift Turbines, %s" % (
        W, isl.depth, {"Pagoda5": "the five-storey pagoda", "Pagoda4": "a four-storey pagoda", "Pagoda3": "a three-storey pagoda"}[isl.pagoda_name]), big)
    text(sheet, (12, 40), "left to right: the garden and koi pond, the gate, the forecourt, the Main Hall (the throne between two cogs, the gallery and its chest, the stair down),", font)
    text(sheet, (12, 60), "the pagoda (a stair through every floor, the locked treasure at the top, a cog on its mast), the tea pavilion; inside the bronze core, the Jade Vault", font)
    text(sheet, (12, half.height + 12), "full scale: the Main Hall and the pagoda (vanilla's Dynasty furniture, clouds, dirt and gold brick are flat stand-ins)", font)
    sheet.convert("RGB").save(out)
    print("%s: %dx%d" % (out, sheet.width, sheet.height))
    return isl


def underside_gif(out, font_path, seed):
    isl = Island(obstacle=300, seed=seed)
    isl.generate()
    r = Renderer(isl)
    font = ImageFont.truetype(font_path, 14)
    rng = random.Random(9)
    smoke = Smoke(rng)
    for _ in range(140):                                 # the smoke already flowing as the GIF starts
        smoke.emit(isl)
        smoke.step()
    x_lo = (20 - r.x0) * TILE
    x_hi = (200 - r.x0) * TILE
    y_lo = (isl.s + 6 - r.y0) * TILE
    y_hi = r.static.height
    frames = []
    total = 5 * 60
    for tick in range(total):
        smoke.emit(isl)
        smoke.step()
        if tick % 3:
            continue
        img = r.frame(tick, smoke.view()).crop((x_lo, y_lo, x_hi, y_hi))
        img = img.resize((img.width // 2, img.height // 2), Image.NEAREST)
        text(img, (8, 6), "under Coghaven: rotors turning over the fire, smoke pouring down (TurbineSmoke: a puff 1 in %d per drawn tick, %d ticks)" % (
            K["SmokeOneIn"], K["Lifetime"]), font)
        text(img, (8, 24), "cogs turning in the cloud (12 frames of 5 degrees, a turn in 9.6 s; style 1 the other way)", font)
        frames.append(img.convert("RGB"))
    pal = [f.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=50, loop=0, optimize=True, disposal=1)
    print("%s: %d frames, %.1f MB" % (out, len(frames), os.path.getsize(out) / 1e6))


def terrain(rng, base, tall):
    """Synthetic first-obstacle rows under the band's columns (the island's 220 and 24 spare each side): ground rolling
    round `base` (+-12) and clamped like vanilla's Terrain pass (decompiled: the surface stays between 17% and 26% of the
    world's height, 23% near the beach), trees (18 tall, 5 wide) here and there, the Dungeon's entrance half the time (a
    block 30 wide and 40 tall: DungeonEnt's dyStrength 20-25 up from the surface, plus its cap), a living tree (12 wide,
    45 tall) 15% of the time and a pyramid (40 wide, 55 tall) 10% of the time."""
    n = W + 48
    ctrl = [base + rng.uniform(-12, 12) for _ in range(n // 20 + 2)]
    rows = [int(min(tall * 0.26, max(tall * 0.17, ctrl[i // 20] + (ctrl[i // 20 + 1] - ctrl[i // 20]) * (i % 20) / 20))) for i in range(n)]
    for _ in range(rng.randint(3, 9)):
        t = rng.randrange(n - 5)
        for i in range(t, t + 5):
            rows[i] -= 18
    for chance, width, height in ((0.5, 30, 40), (0.15, 12, 45), (0.10, 40, 55)):
        if rng.random() < chance:
            d = rng.randrange(n - width)
            for i in range(d, d + width):
                rows[i] -= height
    return rows


def sweep(seeds):
    """Every world size: the surface over vanilla's whole clamped range, with trees, the Dungeon's entrance, living trees
    and pyramids under the island; the pass's choice for each, or a skip."""
    sizes = {"small": 1200, "medium": 1800, "large": 2400}
    for name, tall in sizes.items():
        lo, hi = int(tall * 0.17), int(tall * 0.26)
        picks, skips, dropped, shifted = {}, 0, 0, 0
        rng = random.Random(tall)
        for k in range(seeds):
            rows = terrain(rng, lo + (hi - lo) * k / max(1, seeds - 1), tall)
            isl = Island(rows, k)
            if not isl.ok:
                skips += 1
                continue
            label = isl.pagoda_name + ("" if isl.clearance == K["MinClearance"] else " (last resort)")
            picks[label] = picks.get(label, 0) + 1
            dropped += isl.kept.count(False)
            assert isl.s - isl.above(isl.pagoda) >= K["TopLimit"]
            assert all(isl.s + isl.below(i, isl.depth, False) <= isl.obstacle[i] - isl.clearance for i in range(W))
            shifted += isl.shift != 0
        print("%-6s surface rows %d-%d (trees; the Dungeon, living trees, pyramids): %s; slid along the band %d; turbines left out %d; skipped %d of %d" % (
            name, lo, hi, ", ".join("%s x%d" % kv for kv in sorted(picks.items())), shifted, dropped, skips, seeds))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--seed", type=int, default=7)
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    if only is None or "sweep" in only:
        sweep(200)
    if only is None or "island" in only:
        island_png(os.path.join(args.out, "2026-11-26_coghaven-palace.png"), args.font, args.seed)   # (2026-11-26: the gate and pavilion posts open; 2026-11-17: a third chest
        # in the Main Hall gallery; 2026-11-16: the
        # Jade Vault under the Main Hall, the Locked Pagoda Chest; before: 2026-11-12_coghaven-island-chests.png)
    if only is None or "underside" in only:
        underside_gif(os.path.join(args.out, "2026-11-06_coghaven-underside.gif"), args.font, args.seed)


if __name__ == "__main__":
    main()
