"""D5 proofs for the second request of 2026-11-10, built from the real sprites and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_10b_sim.py --out docs/media [--only ruins,firesaw,golem,lantern,cloth,drone,chests,items]

Writes:
    2026-11-10_secrets-fundamental-ruins.png    FundamentalRuinsPass replayed on a cavern with a spider nest: the nest (its
                                                box in red), the ruins' footprint (twice its area, yellow), the domed arena
                                                with its rune bricks, pillars, puddles and kelp, the stone on its dais in
                                                the forcefield, the wings of ruined chambers and the tunnels out; half scale,
                                                then the arena at full scale.
    2026-11-10_mechanist-firesaw-phantom-slash.gif   the Firesaw's swings with the phantom slash trail (the crescent over the
                                                arc swept in the last three ticks), plain and on fire; 42 a hit (12% crit),
                                                2 steam a swing, 5 on fire.
    2026-11-10_coghaven-jade-golem-palm.gif     the Jade Golem with open hands: the arm follows the player's afterimage (0.5 s
                                                behind, the reticle) smoothly, the ray leaves the palm along the arm; a
                                                running player outruns it, a standing one is hit; a teleport mid-charge is
                                                swept to, not snapped to. The measured per-tick steps are printed and shown.
    2026-11-10_boss-cursed-conductor-lantern-cap.gif the Cursed Lantern firing into the open: at most 4 souls, the oldest
                                                fading when a fifth comes.
    2026-11-10_oldbrasstown-red-cloth.gif       the Mechanical Bull charges a player wearing the Red Cloth: the touch is
                                                dodged (Ole!, 0.7 s of immunity), a charge during the 12 s recharge hurts,
                                                a charge after it is dodged again.
    2026-11-10_scrap-amazonian-drone.gif        an item left lying 20 s: the drone flies in, scans it 3 s, snatches it and
                                                flies out of view; another is shot while scanning (it snatches and runs)
                                                and shot down (the item falls back out).
    2026-11-10_coghaven-chests.png              the question: Coghaven's chests marked and numbered on the island (coghaven_sim's
                                                replay), with where each is and what it holds.
    2026-11-10_items-staff-cloth-drone-ruins.png  the Jade Staff (its gem on the aim line), the Red Cloth and its recharge icon,
                                                the drone's frames and gores, the ruins' blocks, walls, kelp and forcefield.

Leaves out: lighting (the glows are drawn at full strength), vanilla's own art (natural stone, the cave and the water are
flat stand-ins), the planes' parallax, the player's exact physics (update_2026_11_03b_sim's approximation), netcode (the sim
is the server and the owner). Numbers are Expert's.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, player_sprite, TPF  # noqa: E402
from update_2026_11_04_sim import town_backdrop, STEAM  # noqa: E402
from update_2026_11_06b_sim import Planes, coghaven_backdrop, numbers, note, Sparks  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, PLAYER_W, PLAYER_H  # noqa: E402
from update_2026_11_10_sim import swing_angle, posed, hand_at, blade, faded, stone_image, seg_box_dist, ease_out  # noqa: E402
from terrain import load_frames  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
MECH = "Content/Mechanist/Weapons/"
COG = "Content/Coghaven/"
SEC = "Content/Secrets/"
RUIN = SEC + "Ruins/"
WEP = "Content/Bosses/CursedConductor/Weapons/"
TOWN = "Content/OldBrassTown/"
KF = consts(MECH + "Firesaw.cs", MECH + "FiresawLayer.cs")
KG = consts(COG + "NPCs/JadeGolem.cs", COG + "NPCs/JadeGolemRigData.cs", COG + "Projectiles/JadeRay.cs")
KL = consts(WEP + "SoulFire.cs", WEP + "CursedLantern.cs")
KC = consts(TOWN + "Accessories/RedCloth.cs", TOWN + "NPCs/MechanicalBull.cs", TOWN + "NPCs/MechanicalBullRigData.cs")
KD = consts("Content/Scrap/NPCs/AmazonianDrone.cs", "Content/Scrap/NPCs/AmazonianDroneSystem.cs")
KR = consts(SEC + "Generation/FundamentalRuinsPass.cs", SEC + "FundamentalStoneTile.cs")
KF.setdefault("TrailStep", math.radians(24))                  # 24f * MathHelper.Pi / 180f (the parser skips MathHelper)
EMBER, JADE, HIT, HURT, RED = (236, 113, 40), (96, 214, 150), (255, 199, 90), (255, 90, 70), (206, 74, 56)
AETHER = (198, 189, 255)


def font_at(path, size):
    return ImageFont.truetype(path, size)


def additive(img, layer, xy, opacity):
    """Adds an RGBA layer onto img at xy (vanilla's alpha-0 draw colour: light added, never darkened), times opacity."""
    x, y = int(xy[0]), int(xy[1])
    box = (max(0, x), max(0, y), min(img.width, x + layer.width), min(img.height, y + layer.height))
    if box[2] <= box[0] or box[3] <= box[1]:
        return
    part = layer.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
    rgb = Image.new("RGB", part.size, (0, 0, 0))
    rgb.paste(part.convert("RGB"), (0, 0), part.getchannel("A"))
    rgb = rgb.point(lambda v: int(v * opacity))
    base = img.crop(box).convert("RGB")
    out = ImageChops.add(base, rgb).convert("RGBA")
    img.paste(out, box[:2])


def turned(cell, pivot, degrees):
    """A cell turned about its pivot by `degrees` (clockwise on screen), point-sampled; returns it and the pivot's offset."""
    r = int(math.hypot(cell.width, cell.height)) + 4
    pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    pad.alpha_composite(cell, (r - pivot[0], r - pivot[1]))
    return pad.rotate(-degrees, resample=Image.NEAREST), r


# ================================================================================================
# The Fundamental Ruins: FundamentalRuinsPass replayed
# ================================================================================================
STONE_T, BRICK_T, CORAL_T, RUNE_T, WARD_T, KELP_T, STONEOBJ_T = "stone", "brick", "coral", "rune", "ward", "kelp", "obj"
NEST_W, BRICK_W, COLUMN_W, CAVE_W = "nest", "brickw", "columnw", "cavew"


class World:
    """A cavern sample: tiles (kind), walls, water, the nest's spider walls and cobwebs."""

    def __init__(self, w, h, seed):
        self.w, self.h = w, h
        self.rng = random.Random(seed)
        self.tile, self.wall, self.water = {}, {}, set()
        for x in range(w):
            for y in range(h):
                self.tile[(x, y)] = STONE_T
        # winding caves: random walks of round brushes
        for _ in range(14):
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
        # the spider nest: a big pocket in the middle, walled with Spider Wall, cobwebs under its roof
        cx, cy = w // 2 + 6, h // 2 - 4
        self.nest = set()
        for x in range(w):
            for y in range(h):
                u, v = (x - cx) / 31.0, (y - cy) / 21.0
                wob = 0.18 * math.sin(x * 0.4) + 0.14 * math.cos(y * 0.5)
                if u * u + v * v <= 1.0 + wob:
                    self.dig(x, y, NEST_W)
                    self.nest.add((x, y))
        for (x, y) in list(self.nest):
            if self.tile.get((x, y - 1)) == STONE_T and self.rng.random() < 0.35:
                self.tile[(x, y)] = "web"

    def dig(self, x, y, wall):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.tile.pop((x, y), None)
            self.wall[(x, y)] = wall


class Ruins:
    """FundamentalRuinsPass's build, step for step, on a World (its rng stands in for WorldGen.genRand)."""

    def __init__(self, world, seed):
        self.wd, self.rng = world, random.Random(seed)
        xs = [x for (x, _) in world.nest]
        ys = [y for (_, y) in world.nest]
        self.nest_box = (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
        w = max(KR["MinWidth"], min(KR["MaxWidth"], int(round(self.nest_box[2] * 1.41421356))))
        h = max(KR["MinHeight"], min(KR["MaxHeight"], int(round(self.nest_box[3] * 1.41421356))))
        ncx, ncy = self.nest_box[0] + self.nest_box[2] // 2, self.nest_box[1] + self.nest_box[3] // 2
        self.area = (ncx - w // 2, ncy - h // 2, w, h)
        self.kelp = []
        self.stone_at = None

    # cells
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

    def set_wall(self, x, y, wall):
        self.wd.wall[(x, y)] = wall

    def is_air(self, x, y):
        return (x, y) not in self.wd.tile

    def noise(self, x, y):
        def hsh(a, b):
            return ((a * 73856093) ^ (b * 19349663) ^ (1234 * 83492791)) & 0x7FFFFFFF
        gx, gy = x // 4, y // 4
        fx, fy = x / 4.0 - gx, y / 4.0 - gy
        a, b, c, d = (hsh(gx, gy) % 1000 / 1000.0, hsh(gx + 1, gy) % 1000 / 1000.0, hsh(gx, gy + 1) % 1000 / 1000.0,
                      hsh(gx + 1, gy + 1) % 1000 / 1000.0)
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    def shell_block(self, x, y, outer):
        return CORAL_T if outer and self.noise(x, y) < 0.35 else BRICK_T

    # the arena
    @staticmethod
    def inside(dx):
        u = (dx + 0.5) / (KR["ArenaHalf"] + 0.5)
        if abs(u) > 1.0:
            return 0
        return max(KR["ArenaSide"], int(round(KR["ArenaTop"] * math.sqrt(1.0 - u * u))))

    def interior(self, dx, dy):
        return 1 <= dy <= self.inside(dx)

    def build(self):
        ax, ay, aw, ah = self.area
        for p in list(self.wd.nest):                                    # the nest goes: its walls and cobwebs
            if self.wd.wall.get(p) == NEST_W:
                self.wd.wall[p] = None
            if self.wd.tile.get(p) == "web":
                self.wd.tile.pop(p, None)
        self.cx = ax + aw // 2
        self.fy = ay + (ah + KR["ArenaTop"]) // 2
        self.arena()
        self.wing(1)
        self.wing(-1)

    def arena(self):
        cx, fy = self.cx, self.fy
        half, shell, reach = KR["ArenaHalf"], KR["Shell"], KR["ArenaHalf"] + KR["Shell"]
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
                outer = not face and not self.interior(dx + 2, dy) and not self.interior(dx - 2, dy) and not self.interior(dx, dy - 2)
                if face and dy >= 2 and (dx + dy) % KR["RuneEvery"] == 0:
                    self.solid(x, y, RUNE_T)
                else:
                    self.solid(x, y, self.shell_block(x, y, outer and dy > 0))
        for c in (11, 22):
            for dy in range(1, self.inside(c) + 1):
                for dx in (c - 1, c, -c, -c - 1):
                    if self.interior(dx, dy):
                        self.set_wall(cx + dx, fy - dy, COLUMN_W)
        for dy in range(1, KR["DoorHeight"] + 1):
            for k in range(shell):
                self.air(cx + half + k, fy - dy, BRICK_W)
                self.air(cx - half - 1 - k, fy - dy, BRICK_W)
        for side in (1, -1):
            start = KR["PuddleX"] - KR["PuddleWidth"] // 2 if side > 0 else -KR["PuddleX"] - KR["PuddleWidth"] // 2
            for k in range(KR["PuddleWidth"]):
                self.water(cx + start + k, fy, BRICK_W)
        for step in range(1, KR["DaisSteps"] + 1):
            hw = KR["DaisHalf"] + (KR["DaisSteps"] - step) * 2
            for dx in range(-hw, hw):
                self.solid(cx + dx, fy - step, RUNE_T)
        floor_y = fy - KR["DaisSteps"]                                   # FundamentalStones.TryPlace(Ruins, cx - 2, floorY)
        self.stone_at = (cx - 2, floor_y - int(KR["Height"]))
        for dx in range(4):
            for dy in range(int(KR["Height"])):
                self.wd.tile[(cx - 2 + dx, floor_y - int(KR["Height"]) + dy)] = STONEOBJ_T
        bottom, top = fy - KR["DaisSteps"] - 1, fy - KR["DaisSteps"] - int(KR["Height"]) - 2
        for y in range(top + 1, bottom + 1):
            self.solid(cx - 4, y, WARD_T)
            self.solid(cx + 3, y, WARD_T)
        for x in range(cx - 3, cx + 3):
            self.solid(x, top, WARD_T)
        self.ward = (cx - 4, top, 8, bottom - top + 1)
        dx = -half + 2
        while dx < half - 2:
            if abs(dx + 0.5) >= 10:
                self.place_kelp(cx + dx, fy - self.inside(dx), self.rng.randint(KR["KelpMin"], KR["KelpMax"]))
            dx += self.rng.randint(3, 6)

    def place_kelp(self, x, y, length):
        if self.wd.tile.get((x, y - 1)) in (None, KELP_T, WARD_T, STONEOBJ_T):
            return
        for k in range(length):
            if not self.is_air(x, y + k) or not self.is_air(x, y + k + 3) or (x, y + k) in self.wd.water:
                return
            self.wd.tile[(x, y + k)] = KELP_T

    def wing(self, d):
        ax, ay, aw, ah = self.area
        x = self.cx + KR["ArenaHalf"] + KR["Shell"] if d > 0 else self.cx - KR["ArenaHalf"] - KR["Shell"] - 1
        edge = ax + aw - 1 if d > 0 else ax
        floor = last = self.fy
        tower_span = KR["TowerWidth"] + 2 * KR["WingShell"]
        for chamber in range(12):
            room = abs(edge - x) - KR["WingShell"] - tower_span
            if room < KR["ChamberMinWidth"]:
                break
            width = min(self.rng.randint(KR["ChamberMinWidth"], KR["ChamberMaxWidth"]), room)
            height = self.rng.randint(KR["ChamberMinHeight"], KR["ChamberMaxHeight"])
            if chamber > 0:
                floor = max(self.fy - KR["FloorWander"], min(self.fy + KR["FloorWander"], last + self.rng.randint(-1, 1) * KR["FloorStep"]))
            floor = max(ay + height + KR["WingShell"] + 2, min(ay + ah - KR["WingShell"] - 2, floor))
            self.chamber(x, d, width, height, floor, self.fy if chamber == 0 else last)
            x += d * (width + KR["WingShell"])
            last = floor
        if abs(edge - x) + 1 >= KR["TowerWidth"] + KR["WingShell"]:
            self.tower(x, d, last)
            x += d * (KR["TowerWidth"] + KR["WingShell"])
        self.tunnel(x, d, last)

    def tower(self, x0, d, floor):
        ws, tw = KR["WingShell"], KR["TowerWidth"]
        first, last = (x0, x0 + tw - 1) if d > 0 else (x0 - tw + 1, x0)
        left, right = first - ws, last + ws
        top = max(self.area[1] + KR["TowerTopMargin"], floor - KR["TowerMaxHeight"])
        for x in range(left, right + 1):
            for y in range(top - ws, floor + ws):
                if first <= x <= last and top <= y < floor:
                    self.air(x, y, BRICK_W)
                    continue
                if y < top and self.rng.randrange(KR["RoofDecayOneIn"]) == 0:
                    self.air(x, y, None)
                    continue
                outer = x in (left, right) or y in (top - ws, floor + ws - 1)
                self.solid(x, y, self.shell_block(x, y, outer))
        near, far = (first - ws, last + 1) if d > 0 else (last + 1, first - ws)
        for k in range(ws):
            for y in range(floor - KR["DoorHeight"], floor):
                self.air(near + k, y, BRICK_W)
                self.air(far + k, y, BRICK_W)
        on_left = self.rng.random() < 0.5
        y = floor - KR["LedgeEvery"]
        while y > top + 3:
            for k in range(KR["LedgeWidth"]):
                self.solid(first + k if on_left else last - k, y, self.shell_block(first, y, False))
            on_left = not on_left
            y -= KR["LedgeEvery"]
        for _ in range(self.rng.randint(1, 2)):
            if floor - KR["DoorHeight"] - 4 > top + 4:
                wy = self.rng.randint(top + 4, floor - KR["DoorHeight"] - 5)
                for k in range(ws):
                    for yy in range(wy, wy + 3):
                        self.air(far + k, yy, BRICK_W)

    def chamber(self, x0, d, width, height, floor, before):
        ws = KR["WingShell"]
        first, last = (x0, x0 + width - 1) if d > 0 else (x0 - width + 1, x0)
        left, right = first - ws, last + ws
        for x in range(left, right + 1):
            for y in range(floor - height - ws, floor + ws):
                if first <= x <= last and floor - height <= y < floor:
                    self.air(x, y, BRICK_W)
                    continue
                outer = x in (left, right) or y in (floor - height - ws, floor + ws - 1)
                self.solid(x, y, self.shell_block(x, y, outer))
        near, far = (first - ws, last + 1) if d > 0 else (last + 1, first - ws)
        top, bot = min(floor, before) - KR["DoorHeight"], max(floor, before) - 1
        for k in range(ws):
            for y in range(top, bot + 1):
                self.air(near + k, y, BRICK_W)
            for y in range(floor - KR["DoorHeight"], floor):
                self.air(far + k, y, BRICK_W)
        if width >= 13:
            for y in range(floor - height, floor):
                for x in (first + 1, first + 2, last - 1, last - 2):
                    self.set_wall(x, y, COLUMN_W)
        if height >= KR["MezzanineHeight"] and width >= 13:
            for x in range(first + 3, last - 2):
                self.solid(x, floor - 5, BRICK_T)
        for _ in range(self.rng.randint(1, 3)):
            self.place_kelp(self.rng.randint(first + 1, last - 1), floor - height, self.rng.randint(KR["KelpMin"], max(KR["KelpMin"], min(KR["KelpMax"], height - 3))))
        if self.rng.randrange(KR["PuddleOneIn"]) == 0 and width >= 9:
            w = self.rng.randint(2, 4)
            at = self.rng.randint(first + 3, last - w - 1)
            for k in range(w):
                self.water(at + k, floor, BRICK_W)
        if self.rng.randrange(KR["CollapseOneIn"]) == 0 and width >= 11:
            w = self.rng.randint(2, 4)
            at = self.rng.randint(first + 3, last - w - 1)
            for k in range(w):
                for y in range(floor - height - ws, floor - height + 1):
                    self.solid(at + k, y, STONE_T)
                self.solid(at + k, floor - 1, STONE_T)

    def tunnel(self, x, d, floor):
        for step in range(KR["TunnelMax"]):
            col = x + d * step
            if not (0 <= col < self.wd.w):
                return
            if step > KR["WingShell"] and all(self.is_air(col, floor - k) for k in (1, 2, 3)):
                return
            for y in range(floor - KR["TunnelHeight"], floor):
                self.wd.tile.pop((col, y), None)


WALL_LOOKUP = {0: ((9, 3), (10, 3), (11, 3)), 1: ((6, 3), (7, 3), (8, 3)), 2: ((12, 0), (12, 1), (12, 2)), 3: ((1, 4), (3, 4), (5, 4)),
               4: ((9, 0), (9, 1), (9, 2)), 5: ((0, 4), (2, 4), (4, 4)), 6: ((6, 4), (7, 4), (8, 4)), 7: ((1, 2), (2, 2), (3, 2)),
               8: ((6, 0), (7, 0), (8, 0)), 9: ((5, 0), (5, 1), (5, 2)), 10: ((1, 3), (3, 3), (5, 3)), 11: ((4, 0), (4, 1), (4, 2)),
               12: ((0, 3), (2, 3), (4, 3)), 13: ((0, 0), (0, 1), (0, 2)), 14: ((1, 0), (2, 0), (3, 0)), 15: ((1, 1), (2, 1), (3, 1)),
               16: ((6, 1), (7, 1), (8, 1)), 17: ((6, 2), (7, 2), (8, 2)), 18: ((10, 0), (10, 1), (10, 2)), 19: ((11, 0), (11, 1), (11, 2))}
CENTRE = [[2, 0, 0], [0, 1, 4], [0, 3, 0]]
RUIN_BLOCKS = (BRICK_T, CORAL_T, RUNE_T)


def stand_in_stone():
    """Natural stone (vanilla's art isn't in the repo): a grey block sheet in the terrain layout, flat with a few flecks."""
    sheet = Image.new("RGBA", (288, 270), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    rng = random.Random(5)
    for fx in range(16):
        for fy in range(15):
            x0, y0 = fx * 18, fy * 18
            d.rectangle([x0, y0, x0 + 15, y0 + 15], fill=(98, 96, 104, 255))
            for _ in range(5):
                px, py = x0 + rng.randrange(1, 14), y0 + rng.randrange(1, 14)
                d.rectangle([px, py, px + 1, py + 1], fill=(80, 78, 88, 255) if rng.random() < 0.5 else (118, 116, 124, 255))
    return sheet


def render_ruins(world, ruins, x0, y0, x1, y1):
    """The world's cells x0..x1, y0..y1 at 1:1 (16 px a tile), as the game frames them."""
    frames = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
    sheets = {BRICK_T: load(RUIN + "Tiles/FundamentalBrickTile.png"), CORAL_T: load(RUIN + "Tiles/FundamentalCoralTile.png"),
              RUNE_T: load(RUIN + "Tiles/FundamentalRuneTile.png"), WARD_T: load(RUIN + "Tiles/FundamentalWardTile.png"),
              STONE_T: stand_in_stone()}
    glows = {RUNE_T: load(RUIN + "Tiles/FundamentalRuneTile_Glow.png"), WARD_T: load(RUIN + "Tiles/FundamentalWardTile_Glow.png")}
    walls = {BRICK_W: load(RUIN + "Walls/FundamentalBrickWallTile.png"), COLUMN_W: load(RUIN + "Walls/FundamentalColumnWallTile.png")}
    kelp = load(RUIN + "Tiles/FundamentalKelpTile.png")
    W, H = (x1 - x0 + 1) * 16, (y1 - y0 + 1) * 16
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([0, y, W, y], fill=(int(30 + 12 * t), int(28 + 10 * t), int(40 + 8 * t), 255))
    rng = random.Random(7)

    def px(x, y):
        return (x - x0) * 16, (y - y0) * 16
    for (x, y), kind in world.wall.items():                         # walls
        if not (x0 <= x <= x1 and y0 <= y <= y1) or kind is None:
            continue
        X, Y = px(x, y)
        if kind in (CAVE_W, NEST_W):
            d.rectangle([X, Y, X + 15, Y + 15], fill=(52, 46, 54, 255) if kind == CAVE_W else (88, 70, 60, 255))
            if kind == NEST_W:
                d.line([X, Y, X + 15, Y + 15], fill=(120, 100, 90, 255))
            continue
        has = lambda ax, ay: world.wall.get((ax, ay)) == kind or (kind == BRICK_W and world.wall.get((ax, ay)) == COLUMN_W)
        st = (1 if has(x, y - 1) else 0) | (2 if has(x - 1, y) else 0) | (4 if has(x + 1, y) else 0) | (8 if has(x, y + 1) else 0)
        if st == 15:
            st += CENTRE[x % 3][y % 3]
        fx, fy = WALL_LOOKUP[st][rng.randrange(3)]
        img.alpha_composite(walls[kind].crop((fx * 36, fy * 36, fx * 36 + 32, fy * 36 + 32)), (X - 8, Y - 8))
    for (x, y) in world.water:                                      # water (stand-in)
        if x0 <= x <= x1 and y0 <= y <= y1:
            X, Y = px(x, y)
            d.rectangle([X, Y + 2, X + 15, Y + 15], fill=(52, 104, 190, 255))
            d.line([X, Y + 2, X + 15, Y + 2], fill=(120, 170, 230, 255), width=2)
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (x, y), kind in world.tile.items():                          # blocks
        if not (x0 <= x <= x1 and y0 <= y <= y1) or kind in (KELP_T, STONEOBJ_T, "web"):
            continue
        X, Y = px(x, y)

        def same(o):
            if kind in RUIN_BLOCKS:
                return o in RUIN_BLOCKS
            return o == kind
        sig = "".join("-" if same(world.tile.get((x + dx, y + dy))) else "o" for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
        fx, fy = rng.choice(frames[sig])
        img.alpha_composite(sheets[kind].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (X, Y))
        if kind in glows:
            glow_layer.alpha_composite(glows[kind].crop((fx * 18, fy * 18, fx * 18 + 16, fy * 18 + 16)), (X, Y))
    for (x, y), kind in world.tile.items():                          # kelp, cobwebs
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        X, Y = px(x, y)
        if kind == KELP_T:
            tip = world.tile.get((x, y + 1)) != KELP_T
            img.alpha_composite(kelp.crop((x % 3 * 18, (18 if tip else 0), x % 3 * 18 + 16, (18 if tip else 0) + 16)), (X, Y))
        elif kind == "web":
            d.line([X, Y, X + 15, Y + 15], fill=(220, 220, 230, 160))
            d.line([X + 15, Y, X, Y + 15], fill=(220, 220, 230, 160))
    if ruins is not None and ruins.stone_at:                          # the stone on its dais
        sx, sy = ruins.stone_at
        if x0 <= sx <= x1 and y0 <= sy <= y1:
            img.alpha_composite(stone_image(2, 1.0), px(sx, sy))
    additive(img, glow_layer, (0, 0), 0.9)
    return img


def ruins_png(out, font_path):
    world = World(260, 120, seed=11)
    ruins = Ruins(world, seed=3)
    nest_before = render_ruins(world, None, 0, 0, world.w - 1, world.h - 1)
    ruins.build()
    after = render_ruins(world, ruins, 0, 0, world.w - 1, world.h - 1)
    font, big = font_at(font_path, 15), font_at(font_path, 22)
    half_b = nest_before.resize((nest_before.width // 3, nest_before.height // 3), Image.NEAREST)
    half_a = after.resize((after.width // 3, after.height // 3), Image.NEAREST)
    for im, boxes in ((half_b, True), (half_a, True)):
        d = ImageDraw.Draw(im)
        nx, ny, nw, nh = ruins.nest_box
        d.rectangle([nx * 16 // 3, ny * 16 // 3, (nx + nw) * 16 // 3, (ny + nh) * 16 // 3], outline=(230, 60, 60, 255), width=2)
        ax, ay, aw, ah = ruins.area
        d.rectangle([ax * 16 // 3, ay * 16 // 3, (ax + aw) * 16 // 3, (ay + ah) * 16 // 3], outline=(240, 210, 80, 255), width=2)
    cx, fy = ruins.cx, ruins.fy
    crop = after.crop(((cx - 36) * 16, (fy - 30) * 16, (cx + 36) * 16, (fy + 6) * 16))
    W = max(half_a.width, crop.width)
    sheet = Image.new("RGBA", (W, 70 + half_b.height + 40 + half_a.height + 40 + crop.height), (24, 24, 30, 255))
    gif = Gif(font_path, (W, 10))
    y = 10
    nest_area = ruins.nest_box[2] * ruins.nest_box[3]
    ax, ay, aw, ah = ruins.area
    gif.text(sheet, (12, y), "Fundamental Ruins (FundamentalRuinsPass replayed on a cavern with a spider nest)", font=big)
    gif.text(sheet, (12, y + 30), "before: the spider nest (Spider Wall, cobwebs) in its box (red); the ruins' footprint (yellow): %dx%d tiles, %.1fx the nest's box (%dx%d)"
             % (aw, ah, aw * ah / nest_area, ruins.nest_box[2], ruins.nest_box[3]), font=font)
    y += 70
    sheet.alpha_composite(half_b, (0, y))
    y += half_b.height + 6
    gif.text(sheet, (12, y), "after: the nest's walls and webs gone; the domed arena in the middle, a wing of ruined chambers each way, tunnels out to the caves (1/3 scale)", font=font)
    y += 34
    sheet.alpha_composite(half_a, (0, y))
    y += half_a.height + 6
    gif.text(sheet, (12, y), "the arena at full scale: rune bricks in the vault, fluted pillars, two puddles, kelp; the stone on a rune-brick dais inside its forcefield (no room for a player)", font=font)
    y += 34
    sheet.alpha_composite(crop, (0, y))
    sheet.convert("RGB").save(out)
    print("%s: %dx%d; nest box %dx%d (%d cells), footprint %dx%d (x%.2f of the box's area), arena floor row %d, ward %s"
          % (out, sheet.width, sheet.height, ruins.nest_box[2], ruins.nest_box[3], len(world.nest), aw, ah, aw * ah / nest_area, fy, ruins.ward))


# ================================================================================================
# The Firesaw: the phantom slash
# ================================================================================================
def scene_firesaw(out, font):
    W, H, G = 780, 344, 262
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.2)
    saw, fire = load(MECH + "FiresawSwing.png"), load(MECH + "FiresawFire.png")
    trails = {False: (load(MECH + "FiresawTrail.png"), 168, 96, 76, 92), True: (load(MECH + "FiresawTrailFire.png"), 226, 128, 102, 124)}
    sparks = Sparks()
    px = 250.0
    centre = (px, G - 21.0)
    use = int(KF["UseTime"])
    near_x, far_x = px + 58, px + 112
    dummies = [{"x": near_x, "burn": -999}, {"x": far_x, "burn": -999}]
    schedule = [(20, False), (20 + use, False), (20 + 2 * use, False), (140, True), (140 + use, True), (140 + 2 * use, True),
                (260, False), (260 + use, False)]
    tank = 55
    steam = tank
    crit_on = {1, 6}                                            # which hits roll a crit in this replay (12%: illustrative)
    pops, notes = [], [(0, "Firesaw: %d a hit, 12%% crit, %d steam a swing; a slight phantom slash trails each swing" % (KF["Damage"], KF["Steam"])),
                       (140, "right click: the blade burns, two tiles more reach, On Fire!, %d steam a swing; the trail burns too" % KF["FireSteam"]),
                       (260, "the trail covers the arc the blade swept in the last %d ticks, bright at the blade, fading at its tail" % KF["TrailTicks"])]
    swing, last_start, up = None, -999, True
    hit_this, history, hits = set(), [], 0
    for tick in range(330):
        for (t0, f) in schedule:
            if tick == t0:
                chained = t0 - last_start <= use + 20
                up = (not up) if chained else False
                last_start = t0
                swing = (t0, up, f)
                hit_this = set()
                steam -= KF["FireSteam"] if f else KF["Steam"]
        angle, done, frame = None, 0.0, 0
        if swing and tick - swing[0] < use:
            age = tick - swing[0]
            done = age / use
            angle = swing_angle(done, swing[1])
            frame = (tick // int(KF["FrameTicks"])) % int(KF["Frames"])
            if KF["HitFrom"] <= done < KF["HitTo"]:
                prev = swing_angle(max(0.0, (age - 1) / use), swing[1])
                for i, dmy in enumerate(dummies):
                    if i in hit_this:
                        continue
                    box = (dmy["x"] - 16, G - 48, dmy["x"] + 16, G)
                    for a_ in (angle, (angle + prev) / 2, prev):
                        a, b, r = blade(centre, a_, swing[2])
                        if seg_box_dist(a, b, box) <= r:
                            hit_this.add(i)
                            crit = hits in crit_on
                            hits += 1
                            dmg = int(KF["Damage"]) * (2 if crit else 1)
                            pops.append((tick, dmy["x"] - 12, G - 92 - 10 * i, ("%d!" % dmg) if crit else str(dmg), (255, 140, 60) if crit else HIT))
                            sparks.burst(dmy["x"], G - 30, 1, 6, EMBER if swing[2] else (183, 191, 202))
                            if swing[2]:
                                dmy["burn"] = tick
                            break
        else:
            swing = None
        history.append(angle)
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        for i, dmy in enumerate(dummies):
            x = dmy["x"]
            d.rectangle([x - 16, G - 48, x + 16, G], fill=(138, 90, 60, 255), outline=(47, 27, 20, 255))
            d.line([x, G, x, G + 6], fill=(91, 54, 38, 255), width=3)
            if tick - dmy["burn"] < KF["OnFireTicks"]:
                for k in range(5):
                    fx = x - 12 + (k * 7 + tick) % 26
                    d.polygon([(fx, G - 6), (fx + 4, G - 18 - (k % 3) * 4), (fx + 8, G - 6)], fill=EMBER + (230,))
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        if angle is not None:
            burning = swing[2]
            if KF["WindEnd"] <= done < KF["OverEnd"]:
                back = history[-1 - int(KF["TrailTicks"])] if len(history) > KF["TrailTicks"] else None
                if back is not None:                            # FiresawLayer.AddTrail
                    now_v = (math.cos(angle), math.sin(angle))
                    back_v = (math.cos(back), math.sin(back))
                    sweep = math.atan2(back_v[0] * now_v[1] - back_v[1] * now_v[0], back_v[0] * now_v[0] + back_v[1] * now_v[1])
                    span = abs(sweep)
                    if span >= KF["TrailMin"]:
                        sheet, fw, fh, pvx, pvy = trails[burning]
                        k = max(1, min(int(KF["TrailFrames"]), int(span / KF["TrailStep"] + 0.5))) - 1
                        cell = sheet.crop((0, k * (fh + 2), fw, k * (fh + 2) + fh))
                        pivot = (pvx, pvy)
                        if sweep < 0:
                            cell = cell.transpose(Image.FLIP_TOP_BOTTOM)
                            pivot = (pvx, fh - pvy)
                        h = hand_at(centre, angle)
                        pv = (h[0] - now_v[0] * KF["ArmReach"], h[1] - now_v[1] * KF["ArmReach"])
                        g, r = turned(cell, pivot, math.degrees(angle))
                        opacity = KF["TrailOpacity"] * max(0.35, min(1.0, span / KF["TrailFull"]))
                        additive(img, g, (pv[0] - r, pv[1] - r), opacity)
                for k, op in ((3, 0.13), (2, 0.28), (1, 0.45)):
                    if len(history) > k and history[-1 - k] is not None and (tick - k - swing[0]) / use >= KF["WindEnd"] - 0.05:
                        g, r = posed(saw, frame, int(KF["Size"]), (int(KF["GripX"]), int(KF["GripY"])), history[-1 - k])
                        h = hand_at(centre, history[-1 - k])
                        img.alpha_composite(faded(g, op), (int(h[0] - r), int(h[1] - r)))
            g, r = posed(saw, frame, int(KF["Size"]), (int(KF["GripX"]), int(KF["GripY"])), angle)
            h = hand_at(centre, angle)
            img.alpha_composite(g, (int(h[0] - r), int(h[1] - r)))
            if burning:
                g, r = posed(fire, frame, int(KF["FireSize"]), (int(KF["GripX"]), int(KF["FireGripY"])), angle)
                img.alpha_composite(g, (int(h[0] - r), int(h[1] - r)))
            d.line([centre[0] - 4, centre[1] - 2, h[0], h[1]], fill=(91, 54, 38, 255), width=3)
        sparks.step_draw(d)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        label = "-" if swing is None else ("%s-slash%s" % ("up" if swing[1] else "down", ", FIRE" if swing[2] else ""))
        gif.text(img, (10, H - 22), "steam %d / %d | swing: %s | 2 steam a swing, 5 on fire (was 4 and 8)" % (steam, tank, label), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Jade Golem: open palms, the afterimage, smooth tracking
# ================================================================================================
def rig_arrays(path):
    src = open(path, encoding="utf-8").read()
    arrays = {}
    for m in re.finditer(r"public static readonly int\[\] (\w+) = \{([^}]*)\};", src):
        arrays[m.group(1)] = [int(v) for v in m.group(2).split(",") if v.strip()]
    return arrays


class GolemSprite:
    """The Jade Golem drawn as JadeGolem.PreDraw does: far, middle, the raised arm (the arm sheet's frame), near, glow."""

    def __init__(self):
        self.k = KG
        self.sheets = [load(COG + "NPCs/JadeGolem" + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]
        self.arm = load(COG + "NPCs/JadeGolem_Arm.png")
        self.arm_glow = load(COG + "NPCs/JadeGolem_ArmGlow.png")

    def cell(self, sheet, frame, cw, ch, cols):
        x0, y0 = frame % cols * (cw + 2), frame // cols * (ch + 2)
        return sheet.crop((x0, y0, x0 + cw, y0 + ch))

    def put(self, img, cell, anchor, ox, oy, cw, flip, alpha=1.0):
        if flip:
            cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
            pos = (int(round(anchor[0] - (cw - ox))), int(round(anchor[1] - oy)))
        else:
            pos = (int(round(anchor[0] - ox)), int(round(anchor[1] - oy)))
        if alpha < 1.0:
            cell.putalpha(cell.getchannel("A").point(lambda a: int(a * alpha)))
        img.alpha_composite(cell, pos)

    def draw(self, img, frame, anchor, flip, arm=None, glow=0.7):
        k = self.k
        cw, ch, ox, oy, cols = int(k["CellWidth"]), int(k["CellHeight"]), int(k["OriginX"]), int(k["OriginY"]), int(k["Columns"])
        aw, ah, aox, aoy, acols = int(k["ArmCellWidth"]), int(k["ArmCellHeight"]), int(k["ArmOriginX"]), int(k["ArmOriginY"]), int(k["ArmColumns"])
        self.put(img, self.cell(self.sheets[0], frame, cw, ch, cols), anchor, ox, oy, cw, flip)
        self.put(img, self.cell(self.sheets[1], frame, cw, ch, cols), anchor, ox, oy, cw, flip)
        if arm is not None:
            self.put(img, self.cell(self.arm, arm, aw, ah, acols), anchor, aox, aoy, aw, flip)
        self.put(img, self.cell(self.sheets[2], frame, cw, ch, cols), anchor, ox, oy, cw, flip)
        self.put(img, self.cell(self.sheets[3], frame, cw, ch, cols), anchor, ox, oy, cw, flip, glow)
        if arm is not None:
            self.put(img, self.cell(self.arm_glow, arm, aw, ah, acols), anchor, aox, aoy, aw, flip, glow)


def scene_golem(out, font):
    W, H, G = 760, 360, 330
    bg = coghaven_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.2)
    sprite = GolemSprite()
    nodes = load(COG + "Projectiles/JadeRay.png")
    orbs = load(COG + "Projectiles/JadeRay_Orb.png")
    gx, face = 600.0, -1                                         # the golem faces left (direction -1)
    shoulder = (gx + KG["ShoulderX"] * -face, G + KG["ShoulderY"])
    hanging, lo, hi = math.pi / 2, math.radians(KG["ArmMinDegrees"]), math.radians(KG["ArmMinDegrees"] + (KG["ArmFrames"] - 1) * KG["ArmStepDegrees"])
    p = Player(150, G)
    trail = []
    track, lock, fire, recover = int(KG["TrackTicks"]), int(KG["LockTicks"]), int(KG["FireTicks"]), int(KG["RecoverTicks"])
    cycle = 30 + int(KG["ChargeTicks"]) + fire + recover
    episodes = [("running", 0), ("standing", cycle), ("teleport", 2 * cycle)]
    total = 3 * cycle + 30
    aim, state, timer, locked = hanging, "walk", 0, 0.0
    pops, notes = [], [(0, "Jade Golem: open palms; the arm follows the player's afterimage (where they were %.1f s ago: the reticle), smoothly" % (KG["AimDelayTicks"] / 60)),
                       (100, "running away: the ray lands on the afterimage behind them"),
                       (cycle, "standing still: the afterimage catches up and the ray leaves the palm along the arm (%d)" % KG["RayDamage"]),
                       (2 * cycle, "a teleport mid-charge: the afterimage jumps, the arm doesn't (at most %.1f degrees a tick)" % math.degrees(KG["AimMaxTurn"]))]
    max_turn = max_palm = max_end = 0.0
    prev_palm = prev_end = None
    ray = None
    hp_pops = []
    for tick in range(total):
        ep = max(e for e in episodes if e[1] <= tick)
        local = tick - ep[1]
        if ep[0] == "running":                                     # scripted input: running away from him
            p.run = -1
            if local == 0:
                p.x = 420.0
        elif ep[0] == "teleport":
            p.run = 0
            if local == 0:
                p.x = 120.0
            if local == 30 + 15:
                p.x = 380.0                                         # a teleport: the mark is elsewhere at once
        else:
            p.run = 0
            if local == 0:
                p.x = 260.0
        p.step()
        p.x = max(30.0, min(470.0, p.x))
        centre = (p.x, p.y - PLAYER_H / 2)
        trail.append(centre)
        trail = trail[-(int(KG["AimDelayTicks"]) + 1):]
        ghost = trail[0]
        # the golem
        if local == 30 and state == "walk":
            state, timer = "charge", 0
        timer += 1
        before = aim
        if state == "charge":
            want = math.atan2(ghost[1] - shoulder[1], abs(ghost[0] - shoulder[0]))
            aim = max(lo, min(hi, aim + max(-KG["AimMaxTurn"], min(KG["AimMaxTurn"], (want - aim) * KG["AimFollow"]))))
            if timer >= track:
                state, timer, locked = "lock", 0, aim
        elif state == "lock":
            aim += (locked - aim) * KG["LockBlend"]
            if timer >= lock:
                aim = locked
                state, timer = "fire", 0
                d_ = (face * math.cos(locked), math.sin(locked))
                start = (shoulder[0] + d_[0] * KG["PalmReach"], shoulder[1] + d_[1] * KG["PalmReach"])
                end = (start[0] + d_[0] * 800, start[1] + d_[1] * 800)
                if end[1] > G:                                      # the floor stops it
                    t_ = (G - start[1]) / max(1e-6, end[1] - start[1])
                    end = (start[0] + (end[0] - start[0]) * t_, G)
                ray = (start, end, tick)
                box = p.box()
                if seg_box_dist(start, end, box) <= KG["Radius"]:
                    hp_pops.append((tick, p.x - 14, p.y - 70, str(int(KG["RayDamage"])), HURT))
                    pops.append((tick, p.x - 30, p.y - 92, "jade curse +1", JADE))
        elif state == "fire":
            if timer >= fire:
                state, timer = "recover", 0
        elif state == "recover":
            aim = min(hanging, aim + KG["RecoverTurn"])
            if timer >= recover:
                state, timer = "walk", 0
        else:
            aim = hanging
        palm = (shoulder[0] + face * math.cos(aim) * KG["PalmReach"], shoulder[1] + math.sin(aim) * KG["PalmReach"])
        end = (palm[0] + face * math.cos(aim) * 400, palm[1] + math.sin(aim) * 400)
        if state in ("charge", "lock", "fire", "recover"):
            max_turn = max(max_turn, abs(aim - before))
            if prev_palm is not None:
                max_palm = max(max_palm, math.hypot(palm[0] - prev_palm[0], palm[1] - prev_palm[1]))
                max_end = max(max_end, math.hypot(end[0] - prev_end[0], end[1] - prev_end[1]))
            prev_palm, prev_end = palm, end
        else:
            prev_palm = prev_end = None
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        aiming = state in ("charge", "lock", "fire") or (state == "recover" and aim < hanging - 0.001)
        arm_k = max(0, min(int(KG["ArmFrames"]) - 1, int(round((math.degrees(aim) - KG["ArmMinDegrees"]) / KG["ArmStepDegrees"]))))
        frame = int(KG["AimBody"]) if aiming else int(KG["Idle"])
        charge = timer / KG["ChargeTicks"] if state == "charge" else (track + timer) / KG["ChargeTicks"] if state == "lock" else 1.0
        sprite.draw(img, frame, (gx, G), face > 0, arm_k if aiming else None, 0.7 + 0.3 * min(1.0, charge) if state in ("charge", "lock") else 0.7)
        if state in ("charge", "lock"):
            dirv = (face * math.cos(locked if state == "lock" else aim), math.sin(locked if state == "lock" else aim))
            alpha = (0.75 if timer % 6 < 3 else 0.3) if state == "lock" else 0.3
            node = faded(nodes.crop((0, 0, 16, 16)), alpha)
            for dd in range(14, 520, 14):
                q = (palm[0] + dirv[0] * dd, palm[1] + dirv[1] * dd)
                if q[1] > G or q[0] < 0:
                    break
                img.alpha_composite(node, (int(q[0] - 8), int(q[1] - 8)))
            if state == "charge":                                    # the reticle on the afterimage
                ghost_img = faded(player_sprite(), 0.28)
                img.alpha_composite(ghost_img, (int(ghost[0] - 20), int(ghost[1] - PLAYER_H / 2 - 35)))
                r = 12 + (0 if timer % 20 < 10 else 2)
                for off in ((r, 0), (-r, 0), (0, r), (0, -r)):
                    img.alpha_composite(faded(nodes.crop((0, 18, 16, 34)), 0.55), (int(ghost[0] + off[0] - 8), int(ghost[1] + off[1] - 8)))
            f = max(0, min(4, int(charge * 5)))
            img.alpha_composite(orbs.crop((0, f * 26, 24, f * 26 + 24)), (int(palm[0] - 12), int(palm[1] - 12)))
        if ray and tick - ray[2] < fire:
            (sx, sy), (ex, ey), t0 = ray
            n = int(math.hypot(ex - sx, ey - sy) / 6)
            fade = 1.0 - (tick - t0) / fire
            for i in range(n):
                q = (sx + (ex - sx) * i / n, sy + (ey - sy) * i / n)
                img.alpha_composite(faded(nodes.crop((0, ((tick // 3 + i) % 3) * 18, 16, ((tick // 3 + i) % 3) * 18 + 16)), fade), (int(q[0] - 8), int(q[1] - 8)))
        img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        numbers(gif, img, pops + hp_pops, tick)
        note(gif, img, notes, tick)
        gif.text(img, (10, H - 44), "measured: the arm turns at most %.2f deg a tick; the palm moves at most %.1f px a tick; the line's point 400 px out at most %.1f px"
                 % (math.degrees(max_turn), max_palm, max_end), fill=STEAM)
        gif.text(img, (10, H - 24), "%s | %s | arm frame %d of %d (5 deg apart)" % (ep[0], state, arm_k, int(KG["ArmFrames"])), fill=STEAM)
        gif.push(img)
    gif.save(out)
    print("golem: max turn %.2f deg/tick (limit %.2f), max palm step %.2f px/tick, max line point step (400 px) %.2f px/tick"
          % (math.degrees(max_turn), math.degrees(KG["AimMaxTurn"]), max_palm, max_end))


# ================================================================================================
# The Cursed Lantern: four souls at most
# ================================================================================================
def scene_lantern(out, font):
    W, H, G = 700, 330, 300
    bg = backdrop(W, H, G, sky=((40, 34, 60), (24, 20, 38)), dirt=(70, 60, 70))
    gif = Gif(font, (W, H), scale=1.2)
    souls_sheet, souls_glow = load(WEP + "SoulFire.png"), load(WEP + "SoulFire_Glow.png")
    lantern = load(WEP + "CursedLantern.png")
    px = 120.0
    souls = []                                                   # [x, y, vx, vy, age, fading, left]
    pops, notes = [(0, "Cursed Lantern: at most %d souls at once; one more and the oldest fades out (%d ticks)" % (KL["MaxSouls"], KL["FadeTicks"]))], []
    use = int(KL["UseTime"])
    shots = 0
    for tick in range(360):
        if tick % use == 0 and tick < 300:
            shots += 1
            live = [s for s in souls if not s[5]]
            if len(live) >= KL["MaxSouls"]:
                oldest = min(live, key=lambda s: s[6])
                oldest[5] = True
                oldest[6] = min(oldest[6], KL["FadeTicks"])
            a = math.radians(-20 - (shots * 9) % 40)
            souls.append([px + 26, G - 40, math.cos(a) * KL["SoulSpeed"], math.sin(a) * KL["SoulSpeed"], 0, False, KL["Lifetime"]])
        for s in souls:
            if s[5]:
                s[2] *= 0.9
                s[3] *= 0.9
            elif s[2] ** 2 + s[3] ** 2 > KL["DriftSpeed"] ** 2:
                s[2] *= KL["Slow"]
                s[3] *= KL["Slow"]
            s[0] += s[2]
            s[1] += s[3]
            s[4] += 1
            s[6] -= 1
        souls = [s for s in souls if s[6] > 0]
        if tick % TPF:
            continue
        img = bg.copy()
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        img.alpha_composite(lantern, (int(px + 6), int(G - 50)))
        for s in souls:
            f = (s[4] // int(KL["FrameTicks"])) % int(KL["Frames"])
            cell = souls_sheet.crop((0, f * 30, 20, f * 30 + 28))
            glow = souls_glow.crop((0, f * 30, 20, f * 30 + 28))
            fade = min(1.0, s[6] / KL["FadeTicks"]) if s[6] < KL["FadeTicks"] else 1.0
            img.alpha_composite(faded(cell, fade), (int(s[0] - 10), int(s[1] - 18)))
            img.alpha_composite(faded(glow, fade), (int(s[0] - 10), int(s[1] - 18)))
        live = sum(1 for s in souls if not s[5])
        fading = sum(1 for s in souls if s[5])
        note(gif, img, pops, tick)
        gif.text(img, (10, H - 24), "souls: %d of %d%s | shots: %d (was: at most 10, the oldest killed outright)" % (
            live, KL["MaxSouls"], (" + %d fading" % fading) if fading else "", shots), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Red Cloth: the bull's charge sidestepped
# ================================================================================================
def scene_cloth(out, font):
    W, H, G = 780, 320, 290
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.15)
    bull = Planes(TOWN + "NPCs/MechanicalBull", KC)
    cloth_icon, cd_icon = load(TOWN + "Accessories/RedCloth.png"), load(TOWN + "Accessories/RedClothCooldown.png")
    p = Player(220, G)
    hp, cooldown, immune = 400, 0, 0
    pops, notes = [], [(0, "Red Cloth (the Mechanical Bull drops it, 10%%): the next enemy touch is dodged, %.1f s of immunity, then %d s to recharge"
                        % (KC["ImmuneTicks"] / 60, KC["RechargeTicks"] // 60))]
    charges = [(0, "ready: dodged"), (150, "recharging: it hurts"), (330, "12 s after the dodge: ready again")]
    total = 470
    bx, bvx, phase, ptimer, last_hit = 700.0, 0.0, "paw", 0, -999
    cut = {150: "(3 s after the dodge)", 330: "(the 12 s are up)"}
    for tick in range(total):
        for (t0, label) in charges:
            if tick == t0:
                bx, bvx, phase, ptimer = 700.0, 0.0, "paw", 0
                p = Player(220, G)                                   # each charge from the same spot
                immune = 0
                if t0 == 330:
                    cooldown = 0                                     # time skipped: the recharge has run out
                elif t0 == 150:
                    cooldown = int(KC["RechargeTicks"]) - 180            # time skipped: 3 s after the dodge
                notes.append((tick, label + " " + cut.get(t0, "")))
        ptimer += 1
        if phase == "paw" and ptimer >= KC["PawTicks"]:
            phase = "charge"
        if phase == "charge":
            bvx = max(-KC["ChargeSpeed"], bvx - KC["ChargeAccel"])
            bx += bvx
        if cooldown > 0:
            cooldown -= 1
        if immune > 0:
            immune -= 1
        bull_box = (bx - KC["Width"] / 2, G - KC["Height"], bx + KC["Width"] / 2, G)
        if phase == "charge" and overlaps(bull_box, p.box()) and immune == 0 and tick - last_hit > 20:
            last_hit = tick
            if cooldown == 0:
                cooldown, immune = int(KC["RechargeTicks"]), int(KC["ImmuneTicks"])
                pops.append((tick, p.x - 24, G - 100, "Ole!", RED))
            else:
                dmg = int(KC["TrotDamage"] * KC["ChargeDamageMultiplier"])
                hp -= dmg
                pops.append((tick, p.x - 14, G - 90, str(dmg), HURT))
                p.hurt(-1, 9.0)
                immune = 40
        p.step()
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        frame = int(KC["Paw"]) + (ptimer // 8) % 2 if phase == "paw" else int(KC["Charge"]) + (ptimer // 4) % int(KC["ChargeFrames"])
        bull.draw(img, frame, (bx, G), False)
        if immune == 0 or (tick // 6) % 3 != 2:                     # the immunity's blink
            img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        if pops and 0 <= tick - pops[-1][0] < 16 and pops[-1][3] == "Ole!":
            for k in range(14):                                       # the cloth's sweep (RedClothPlayer.Effects)
                a = -1.2 + 2.4 * k / 13
                q = (p.x + math.cos(a) * 22, p.y - PLAYER_H / 2 + math.sin(a) * 26 - (tick - pops[-1][0]))
                d.rectangle([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=RED + (255,))
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        img.alpha_composite(cloth_icon, (W - 120, 34))
        if cooldown > 0:
            img.alpha_composite(cd_icon, (W - 80, 34))
            gif.text(img, (W - 84, 70), "%d s" % math.ceil(cooldown / 60), fill=STEAM)
        else:
            gif.text(img, (W - 84, 40), "ready", fill=(140, 220, 140))
        gif.text(img, (10, H - 22), "player life %d | the bull's charge: %d (Expert)" % (hp, int(KC["TrotDamage"] * KC["ChargeDamageMultiplier"])), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Amazonian Drone
# ================================================================================================
def scene_drone(out, font):
    W, H, G = 780, 360, 320
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.15)
    sheet, glow = load("Content/Scrap/NPCs/AmazonianDrone.png"), load("Content/Scrap/NPCs/AmazonianDrone_Glow.png")
    cog = load("Content/Scrap/Items/RustedCog.png")
    loot = load("Content/Gems/Items/JadeStaff.png")
    fw, fh = int(KD["FrameW"]), int(KD["FrameH"])
    player_x = 120.0
    pops, notes = [], [(0, "an item left lying %d s near a player: an Amazonian Drone may come for it" % (KD["LyingTicks"] // 60))]
    # part 1: a Jade Staff lying at x 430; part 2: a cog stack at 520, the player shoots
    items = [{"x": 430.0, "img": loot, "here": True, "lying": 0}, {"x": 560.0, "img": cog, "here": False, "lying": 0}]
    drone = None
    life = int(KD["Life"])
    total = 760
    shots = []
    gone_at = None
    for tick in range(total):
        if tick == 10:
            items[0]["lying"] = int(KD["LyingTicks"])                # time skipped: 20 s on the ground
            notes.append((tick, "20 s on the ground (skipped): the drone comes from off screen"))
        if tick == 20:
            drone = {"x": W + 60.0, "y": 60.0, "vx": 0.0, "vy": 0.0, "phase": "approach", "t": 0, "item": 0, "carry": None, "hp": life, "dir": -1}
        if tick == 400:
            items[1]["here"] = True
            drone = {"x": W + 60.0, "y": 50.0, "vx": 0.0, "vy": 0.0, "phase": "approach", "t": 0, "item": 1, "carry": None, "hp": life, "dir": -1}
            notes.append((tick, "another one; this time the player shoots it while it scans"))
        if drone:
            dr = drone
            dr["t"] += 1
            it = items[dr["item"]] if dr["item"] is not None else None
            if dr["phase"] == "approach" and it:
                tx, ty = it["x"], G - 8 - KD["HoverHeight"]
                dx, dy = tx - dr["x"], ty - dr["y"]
                dist = math.hypot(dx, dy)
                sp = min(KD["ApproachSpeed"], dist * 0.12)
                dr["vx"] += ((dx / max(dist, 1e-6)) * sp - dr["vx"]) * KD["ApproachTurn"]
                dr["vy"] += ((dy / max(dist, 1e-6)) * sp - dr["vy"]) * KD["ApproachTurn"]
                dr["dir"] = -1 if dx < 0 else 1
                if dist < 10:
                    dr["phase"], dr["t"] = "scan", 0
                    notes.append((tick, "scanning: %d s, a light a second" % (KD["ScanTicks"] // 60)))
            elif dr["phase"] == "scan" and it:
                bob = math.sin(dr["t"] * 0.08) * 3
                tx, ty = it["x"], G - 8 - KD["HoverHeight"] - bob
                dr["vx"] += ((tx - dr["x"]) * 0.2 - dr["vx"]) * 0.2
                dr["vy"] += ((ty - dr["y"]) * 0.2 - dr["vy"]) * 0.2
                if dr["item"] == 1 and dr["t"] in (60, 61) and not shots:
                    shots.append([player_x + 20, G - 30, tick])
                if dr["t"] >= KD["ScanTicks"]:
                    dr["carry"], it["here"], dr["phase"], dr["t"] = it["img"], False, "flee", 0
                    pops.append((tick, dr["x"] - 20, dr["y"] - 40, "snatched", RED))
            elif dr["phase"] == "flee":
                away = 1 if dr["x"] >= player_x else -1
                dr["vx"] += (away * KD["FleeSpeed"] * 0.8 - dr["vx"]) * KD["FleeTurn"]
                dr["vy"] += (-KD["FleeSpeed"] * 0.6 - dr["vy"]) * KD["FleeTurn"]
                dr["dir"] = away
            dr["x"] += dr["vx"]
            dr["y"] += dr["vy"]
            if dr["phase"] == "flee" and (dr["x"] > W + 80 or dr["y"] < -60):
                notes.append((tick, "out of every player's view: gone, and the item with it"))
                gone_at = tick
                drone = None
        for s in shots:                                               # bullets at the drone
            if drone is None:
                break
            if s[2] > tick or s[2] == -1:
                continue                                              # not fired yet, or spent
            tx, ty = drone["x"], drone["y"]
            dx, dy = tx - s[0], ty - s[1]
            dist = math.hypot(dx, dy)
            s[0] += dx / max(dist, 1e-6) * 26
            s[1] += dy / max(dist, 1e-6) * 26
            if dist < 26:
                s[2] = -1
                drone["hp"] -= 26
                pops.append((tick, drone["x"] - 10, drone["y"] - 50, "26", HIT))
                if drone["phase"] != "flee":
                    it = items[drone["item"]]
                    if abs(it["x"] - drone["x"]) < KD["SnatchRange"]:
                        drone["carry"], it["here"] = it["img"], False
                        pops.append((tick, drone["x"] - 40, drone["y"] - 70, "snatched in a panic!", RED))
                    drone["phase"], drone["t"] = "flee", 0
                    shots.append([player_x + 20, G - 30, tick + 4])
                if drone["hp"] <= 0:
                    items.append({"x": drone["x"], "img": drone["carry"], "here": True, "lying": 0, "fall": drone["y"]})
                    items.append({"x": drone["x"] + 18, "img": cog, "here": True, "lying": 0, "fall": drone["y"]})
                    pops.append((tick, drone["x"] - 30, drone["y"] - 60, "shot down", HIT))
                    notes.append((tick, "shot down: what it stole falls back out, untouched, and a few Rusted Cogs"))
                    drone = None
        shots = [s for s in shots if s[2] != -1]
        for it in items:
            if "fall" in it and it["fall"] < G - 18:
                it["fall"] += 4
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        img.alpha_composite(player_sprite(), (int(player_x - 20), int(G - 56)))
        for it in items:
            if it["here"] and it["img"] is not None:
                y = it.get("fall", G - 18)
                im = it["img"]
                img.alpha_composite(im, (int(it["x"] - im.width // 2), int(min(y, G - 18) + 18 - im.height)))
        if drone:
            dr = drone
            scanning = dr["phase"] == "scan"
            frame = (3 if dr["carry"] is not None else 0) + (tick // int(KD["FrameTicks"])) % 3
            cell = sheet.crop((0, frame * (fh + 2), fw, frame * (fh + 2) + fh))
            gcell = glow.crop((0, frame * (fh + 2), fw, frame * (fh + 2) + fh))
            flip = dr["dir"] > 0
            if flip:
                cell, gcell = cell.transpose(Image.FLIP_LEFT_RIGHT), gcell.transpose(Image.FLIP_LEFT_RIGHT)
            tl = (int(dr["x"] - fw / 2), int(dr["y"] - fh / 2))
            if scanning:                                            # AmazonianDrone.DrawScan
                it = items[dr["item"]]
                eye = (tl[0] + (fw - KD["EyeX"] if flip else KD["EyeX"]), tl[1] + KD["EyeY"])
                top, bottom = G - 18 - it["img"].height, G
                left, right = it["x"] - it["img"].width / 2 - 4, it["x"] + it["img"].width / 2 + 4
                beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                bd = ImageDraw.Draw(beam)
                rows = max(1, int((bottom - eye[1]) / 2))
                for r in range(rows):
                    t = r / rows
                    l = eye[0] - 1 + (left - eye[0] + 1) * t
                    w_ = 2 + (right - left - 2) * t
                    bd.rectangle([l, eye[1] + r * 2, l + w_, eye[1] + r * 2 + 1], fill=(int(206 * (0.12 + 0.12 * t)), int(74 * (0.12 + 0.12 * t)), int(56 * (0.12 + 0.12 * t)), 255))
                sweep = top + (bottom - top) * (0.5 + 0.5 * math.sin(dr["t"] * 0.15))
                bd.rectangle([left, sweep, right, sweep + 1], fill=(204, 120, 96, 255))
                additive(img, beam, (0, 0), 1.0)
                lit = max(1, min(3, dr["t"] // 60 + 1))
                for k in range(3):
                    x = tl[0] + ((fw - 26 - k * 6) if flip else (26 + k * 6)) - 2
                    d.rectangle([x, tl[1] + 10, x + 3, tl[1] + 13], fill=((236, 122, 88) if k < lit else (84, 20, 28)) + (255,))
            img.alpha_composite(cell, tl)
            img.alpha_composite(gcell, tl)
            if dr["carry"] is not None:
                im = dr["carry"]
                scale = min(1.0, 28 / max(im.width, im.height))
                im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.NEAREST)
                claw = (tl[0] + (fw - KD["ClawX"] if flip else KD["ClawX"]), tl[1] + KD["ClawY"])
                img.alpha_composite(im, (int(claw[0] - im.width / 2), int(claw[1] - 2)))
            gif.text(img, (int(dr["x"] - 18), int(dr["y"] - 40)), "%d/%d" % (max(0, dr["hp"]), life), fill=(255, 140, 120))
        for s in shots:
            if s[2] <= tick:
                d.rectangle([s[0] - 2, s[1] - 1, s[0] + 2, s[1] + 1], fill=(255, 220, 120, 255))
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.text(img, (10, H - 22), "Amazonian Drone: %d life, no contact damage; it scans %d s, snatches, flies off and leaves once nobody can see it"
                 % (life, KD["ScanTicks"] // 60), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The question: Coghaven's chests
# ================================================================================================
def chests_png(out, font_path):
    import coghaven_sim as cs
    isl = cs.Island(obstacle=300, seed=7)
    isl.generate()
    r = cs.Renderer(isl)
    full = r.frame(200)
    font, big = font_at(font_path, 16), font_at(font_path, 22)
    chests = [(ch, x, y) for (ch, x, y) in isl.pieces if ch in "CQ"]
    chests.sort(key=lambda c: (c[1], c[2]))
    half = full.resize((full.width // 2, full.height // 2), Image.NEAREST)
    d = ImageDraw.Draw(half)
    rooms = []
    for n, (ch, x, y) in enumerate(chests, 1):
        X, Y = r.px(x, y)
        X, Y = (X + 16) // 2, (Y + 8) // 2
        col = (255, 215, 60) if ch == "Q" else (255, 90, 70)
        d.ellipse([X - 14, Y - 14, X + 14, Y + 14], outline=col + (255,), width=3)
        d.text((X + 16, Y - 22), str(n), fill=col + (255,), font=big)
        if y > isl.s:
            where = "the engine deck, inside the bronze core under the island"
        elif K_in(x, "MainHallX", 63):
            where = "the Main Hall's ground floor (either side of the throne)"
        elif K_in(x, "PagodaX", 27):
            where = "the pagoda's top floor (the treasure)" if ch == "Q" else "a pagoda floor"
        else:
            where = "the island"
        rooms.append((n, ch, x, y, where))
    sheet = Image.new("RGBA", (half.width, half.height + 60 + 26 * (len(rooms) + 3)), (24, 24, 30, 255))
    sheet.alpha_composite(half, (0, 60))
    gif = Gif(font_path, (10, 10))
    gif.text(sheet, (12, 10), "Coghaven has %d chests (all Dynasty Chests; 7 when only a short pagoda fits under the sky's ceiling)" % len(chests), font=big)
    gif.text(sheet, (12, 36), "red: ordinary chests (3-8 Jade, half of them 20-40 Jade Bricks, plus vanilla's sky-island loot); gold: the pagoda's treasure", font=font)
    y = half.height + 70
    for (n, ch, x, y_, where) in rooms:
        rows = y_ - isl.s
        level = ("%d rows above the terrace" % -rows) if rows < 0 else ("%d rows down inside the island" % rows) if rows > 0 else "on the terrace"
        gif.text(sheet, (12, y), "%d. %s: %s; %d tiles from the island's left end, %s" % (n, "treasure" if ch == "Q" else "chest", where, x, level), font=font)
        y += 26
    gif.text(sheet, (12, y + 6), "the treasure adds 1 in 10 Fledgling Wings, a Lift Turbine, 2 Bronze Cogs, 8-15 Tarnished Brass Bars, 2-4 gold and 8-15 Jade", font=font)
    sheet.convert("RGB").save(out)
    print("%s: %d chests: %s" % (out, len(chests), ", ".join("%s at (%d, %d)" % (c[0], c[1], c[2] - isl.s) for c in chests)))


def K_in(x, key, width):
    import coghaven_sim as cs
    return cs.K[key] <= x < cs.K[key] + width


# ================================================================================================
# Items
# ================================================================================================
def items_png(out, font_path):
    font = font_at(font_path, 14)
    pics = [("Jade Staff", load("Content/Gems/Items/JadeStaff.png"), 4), ("Red Cloth", load(TOWN + "Accessories/RedCloth.png"), 4),
            ("recharging", load(TOWN + "Accessories/RedClothCooldown.png"), 4)]
    drone = load("Content/Scrap/NPCs/AmazonianDrone.png")
    fw, fh = int(KD["FrameW"]), int(KD["FrameH"])
    for k in range(6):
        pics.append(("drone %d" % k, drone.crop((0, k * (fh + 2), fw, k * (fh + 2) + fh)), 2))
    for name in ("FundamentalBrick", "FundamentalCoral", "FundamentalRune", "FundamentalBrickWall", "FundamentalColumnWall"):
        pics.append((name.replace("Fundamental", "") or name, load(RUIN + "Items/%s.png" % name), 4))
    pics.append(("forcefield", load(RUIN + "Tiles/FundamentalWardTile.png").crop((18, 18, 70, 70)), 3))
    pics.append(("kelp", load(RUIN + "Tiles/FundamentalKelpTile.png"), 4))
    pics.append(("biome", load(SEC + "FundamentalRuinsBiome_Icon.png"), 4))
    cells = []
    for (label, im, s) in pics:
        big = im.resize((im.width * s, im.height * s), Image.NEAREST)
        cell = Image.new("RGBA", (max(big.width, 110) + 20, big.height + 40), (40, 44, 52, 255))
        cell.alpha_composite(big, ((cell.width - big.width) // 2, 8))
        ImageDraw.Draw(cell).text((8, cell.height - 24), label, fill=(238, 241, 243), font=font)
        cells.append(cell)
    rows, row, w = [], [], 0
    for c in cells:
        if w + c.width > 1100 and row:
            rows.append(row)
            row, w = [], 0
        row.append(c)
        w += c.width
    rows.append(row)
    H = sum(max(c.height for c in r) for r in rows)
    sheet = Image.new("RGBA", (1100, H), (24, 24, 30, 255))
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
    o = lambda name: os.path.join(args.out, name)   # noqa: E731
    jobs = [("ruins", lambda: ruins_png(o("2026-11-10_secrets-fundamental-ruins.png"), args.font)),
            ("firesaw", lambda: scene_firesaw(o("2026-11-10_mechanist-firesaw-phantom-slash.gif"), args.font)),
            ("golem", lambda: scene_golem(o("2026-11-10_coghaven-jade-golem-palm.gif"), args.font)),
            ("lantern", lambda: scene_lantern(o("2026-11-10_boss-cursed-conductor-lantern-cap.gif"), args.font)),
            ("cloth", lambda: scene_cloth(o("2026-11-10_oldbrasstown-red-cloth.gif"), args.font)),
            ("drone", lambda: scene_drone(o("2026-11-10_scrap-amazonian-drone.gif"), args.font)),
            ("chests", lambda: chests_png(o("2026-11-10_coghaven-chests.png"), args.font)),
            ("items", lambda: items_png(o("2026-11-10_items-staff-cloth-drone-ruins.png"), args.font))]
    only = set(args.only.split(",")) if args.only else None
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
