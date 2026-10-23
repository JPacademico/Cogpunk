"""D5 simulation of the Junkyard world generation (Content/Junkyard/Generation/JunkyardPass.cs).

    python -P tools/sim/junkyard_sim.py --seed 3 --out-overview docs/media/<date>_junkyard-overview.png \
        --out-detail docs/media/<date>_junkyard-surface.png

Replays the pass's layout and shaping rules with the same constants on a synthetic small world (4200x1200: surface
~300, underworld at 1000; the vanilla left beach end at 340), then renders:
* overview: the whole strip, 2 px per tile, with the full pool depth and the three sections labelled;
* detail: the beach, the junkyard and the pool rim at 1x art scale (8 px per tile) with the real Rusted Scrap,
  Polished Metal and Scrappy Trunk sprites, framed like the game (tools/sim/terrain.py), and every water tile drawn
  as the Junkyard's tar (Content/Junkyard/Tar/TarWaterStyle.png, surface and interior cells, opaque like vanilla's
  background water pass).

Leaves out: vanilla terrain outside the strip (flat stand-in land and stone), sand/stone/water/palm sprites (plain
stand-ins), slopes, lighting, and genRand (Python's RNG: same rules, different rolls).
"""
import argparse
import math
import os
import random
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from terrain import load_frames, render  # noqa: E402

# --- mirrored from JunkyardPass.cs -------------------------------------------------------------
BEACH_MIN, BEACH_MAX, YARD_MIN, YARD_MAX = 18, 22, 100, 123
WALL_THICKNESS, POOL_DROP, POOL_DEPTH_FRACTION = 4, 2, 0.5
MIN_POOL_DEPTH, FLOOR_THICKNESS, BEACH_DROP, SAND_DEPTH = 60, 6, 3, 12
EDGE_MARGIN, VISIBLE_LEFT_WALL, OFF_LIMIT = 2, 4, 40
CACHE_FLOOR_ABOVE_GROUND = 2
# ------------------------------------------------------------------------------------------------
WORLD_W, WORLD_H, UNDERWORLD, BEACH_END, LAND_Y = 420, 1200, 1000, 340, 300


class World:
    def __init__(self):
        self.t = {}          # (x, y) -> tile char
        self.water = set()
        self.extra = {}      # (x, y) -> (kind, data)

    def set(self, x, y, ch):
        self.t[(x, y)] = ch
        self.water.discard((x, y))

    def clear(self, x, y):
        self.t.pop((x, y), None)
        self.water.discard((x, y))

    def get(self, x, y):
        return self.t.get((x, y), ".")


def generate(rng):
    w = World()
    # synthetic vanilla: flat land right of the beach, dirt then stone below
    for x in range(BEACH_END - 10, WORLD_W):
        for y in range(LAND_Y, LAND_Y + 140):
            w.set(x, y, "d" if y < LAND_Y + 30 else "s")
    for x in range(EDGE_MARGIN, BEACH_END):
        for y in range(LAND_Y + 40, LAND_Y + 140):
            w.set(x, y, "s")

    right = BEACH_END
    beach_w = rng.randint(BEACH_MIN, BEACH_MAX)
    yard_w = rng.randint(YARD_MIN, YARD_MAX)
    left_wall_end = OFF_LIMIT + VISIBLE_LEFT_WALL - 1
    beach_left = right - beach_w
    yard_left = beach_left - yard_w
    pool_left, pool_right = left_wall_end + 1, yard_left - WALL_THICKNESS
    ground = LAND_Y
    yard_ground = ground + BEACH_DROP
    pool_top = yard_ground + POOL_DROP
    bottom = pool_top + int((UNDERWORLD - pool_top) * POOL_DEPTH_FRACTION)
    bottom = max(bottom, pool_top + MIN_POOL_DEPTH)
    top = ground - 45

    for x in range(EDGE_MARGIN, yard_left):
        wall = x <= left_wall_end or x >= pool_right
        for y in range(top, bottom + FLOOR_THICKNESS):
            w.clear(x, y)
            if wall:
                if y >= yard_ground:
                    w.set(x, y, "M")
            elif y >= bottom:
                w.set(x, y, "a" if y < bottom + 2 else "s")
            elif y >= pool_top:
                w.water.add((x, y))                        # drawn as tar in the Junkyard

    surface = {}
    for x in range(yard_left, right):
        s = ground + round((right - x) / beach_w * BEACH_DROP) if x >= beach_left else yard_ground
        surface[x] = s
        for y in range(top, s):
            w.clear(x, y)
        for y in range(s, s + SAND_DEPTH):
            w.set(x, y, "a")
        y = s + SAND_DEPTH
        while w.get(x, y) == "." and y < s + SAND_DEPTH + 90:
            w.set(x, y, "a")
            y += 1

    def heap(cx, half, height, bury):
        last = None
        for dx in range(-half, half + 1):
            x = cx + dx
            if x not in surface:
                continue
            pile = 1 - (dx / (half + 1)) ** 2
            bowl = math.sqrt(max(0.0, pile))
            g = surface[x]
            t = g - round(height * pile) - (1 if pile > 0.35 and rng.random() < 1 / 3 else 0)
            if last is not None and abs(t - last) > 2:
                t = last + (2 if t > last else -2)
            last = t
            for y in range(t, g + round(bury * bowl) + 1):
                w.set(x, y, "R")

    def puddle(x0, x1):
        if x1 - x0 + 1 < 5:
            return
        x1 = min(x1, x0 + 8)
        depth = rng.randint(2, 3)
        for x in range(x0, x1 + 1):
            d = depth - 1 if x in (x0, x1) else depth
            for y in range(surface[x], surface[x] + d):
                w.clear(x, y)
                w.water.add((x, y))

    def side_heaps(a, b):
        x = a
        for _ in range(32):
            if x >= b:
                break
            half = rng.randint(5, 9)
            gap = rng.randint(4, 9)
            c = x + gap + half
            if c + half > b:
                puddle(x + 1, b - 1)
                break
            puddle(x + 1, x + gap - 1)
            heap(c, half, rng.randint(4, 8), rng.randint(2, 4))
            x = c + half + 1

    centre = yard_left + yard_w // 2
    centre_half = rng.randint(11, 14)
    heap(centre, centre_half, rng.randint(10, 12), rng.randint(4, 6))
    side_heaps(yard_left + 3, centre - centre_half - 1)
    side_heaps(centre + centre_half + 1, beach_left - 2)
    floor = yard_ground - CACHE_FLOOR_ABOVE_GROUND
    cx = centre - 1
    for dx in range(-1, 3):
        for y in range(floor - 3, floor):
            w.clear(cx + dx, y)
        if w.get(cx + dx, floor) == ".":
            w.set(cx + dx, floor, "R")
    w.extra[(cx, floor - 2)] = ("trunk", None)

    for _ in range(max(2, beach_w // 4)):                  # buried clumps (TileRunner stand-in: small blob)
        x = rng.randint(beach_left + 1, right - 2)
        y = surface[x] + rng.randint(2, 6)
        r = rng.randint(1, 2)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + 1 and w.get(x + dx, y + dy) == "a":
                    w.set(x + dx, y + dy, "R")
    for _ in range(3):
        x = rng.randint(beach_left, right - 1)
        if w.get(x, surface[x]) == "a":
            w.set(x, surface[x], "R")
    palms = []
    x = beach_left + 2
    while x < right - 2 and len(palms) < 4:
        if w.get(x, surface[x]) == "a" and w.get(x, surface[x] - 1) == ".":
            palms.append((x, surface[x]))
        x += rng.randint(4, 6)
    info = dict(right=right, beach_left=beach_left, yard_left=yard_left, pool_left=pool_left, pool_right=pool_right,
                top=top, ground=ground, yard_ground=yard_ground, pool_top=pool_top, bottom=bottom, palms=palms,
                beach_w=beach_w, yard_w=yard_w, centre=centre)
    return w, info


COLOURS = {"a": (220, 196, 128), "s": (100, 104, 112), "d": (130, 92, 62), "R": (147, 68, 31), "M": (127, 135, 148)}
WATER = (47, 27, 20)                                  # tar (Leather 0): every water tile in the Junkyard


def render_overview(w, info, out):
    x0, x1 = 0, WORLD_W
    y0, y1 = info["top"], info["bottom"] + FLOOR_THICKNESS + 30
    s = 2
    img = Image.new("RGB", ((x1 - x0) * s, (y1 - y0) * s + 40), (150, 180, 210))
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        for x in range(x0, x1):
            ch = w.get(x, y)
            col = COLOURS.get(ch)
            if (x, y) in w.water:
                col = WATER
            if col is None and y > LAND_Y + 140:
                col = (60, 62, 70)
            if col:
                d.rectangle([(x - x0) * s, (y - y0) * s, (x - x0) * s + s - 1, (y - y0) * s + s - 1], fill=col)
    d.rectangle([0, 0, OFF_LIMIT * s, (y1 - y0) * s], outline=(255, 80, 80))
    labels = [(info["beach_left"], info["right"], f"1 beach {info['beach_w']}"), (info["yard_left"], info["beach_left"], f"2 junkyard {info['yard_w']}"),
              (EDGE_MARGIN, info["yard_left"], f"3 deep pool {info['pool_right'] - info['pool_left']} wide, {info['bottom'] - info['pool_top']} deep")]
    ybar = (y1 - y0) * s + 4
    for a, b, text in labels:
        d.line([(a - x0) * s, ybar, (b - x0) * s, ybar], fill=(21, 22, 28), width=2)
        d.text(((a - x0) * s + 2, ybar + 4), text, fill=(21, 22, 28))
    d.text((OFF_LIMIT * s + 4, 4), "world border (x<40 unreachable)", fill=(255, 255, 255))
    d.text((info["pool_left"] * s + 4, (info["pool_top"] - y0) * s + 4), "steaming tar: the whole pool", fill=(255, 255, 255))
    d.text((info["pool_left"] * s + 4, (info["bottom"] - y0) * s - 14), f"floor: halfway to the underworld (y={info['bottom']})", fill=(255, 255, 255))
    img.save(out)


def stand_in_tile(col, seed):
    rng = random.Random(seed)
    t = Image.new("RGBA", (16, 16), col + (255,))
    px = t.load()
    for _ in range(10):
        x, y = rng.randrange(0, 16, 2), rng.randrange(0, 16, 2)
        c = tuple(max(0, min(255, v + rng.choice((-18, 14)))) for v in col) + (255,)
        for dx in (0, 1):
            for dy in (0, 1):
                px[x + dx, y + dy] = c
    return t


def render_detail(w, info, out):
    x0 = info["pool_right"] - 26
    x1 = info["right"] + 8
    y0 = info["ground"] - 26
    y1 = info["pool_top"] + 18
    frames = load_frames("art/templates/terrain_exposure.json")
    sheets = {"R": Image.open("Content/Scrap/Tiles/RustedScrapTile.png").convert("RGBA"),
              "M": Image.open("Content/Junkyard/Tiles/PolishedMetalTile.png").convert("RGBA")}
    grid = ["".join(w.get(x, y) if w.get(x, y) in sheets else "." for x in range(x0, x1)) for y in range(y0, y1)]
    img = Image.new("RGBA", ((x1 - x0) * 16, (y1 - y0) * 16), (150, 180, 210, 255))
    stand = {ch: [stand_in_tile(COLOURS[ch], i) for i in range(4)] for ch in "asd"}
    tar = Image.open("Content/Junkyard/Tar/TarWaterStyle.png").convert("RGBA")
    for y in range(y0, y1):
        for x in range(x0, x1):
            ch = w.get(x, y)
            if ch in stand:
                img.alpha_composite(stand[ch][(x * 7 + y) % 4], ((x - x0) * 16, (y - y0) * 16))
            if (x, y) in w.water:
                cell_y = 0 if (x, y - 1) not in w.water else 48
                img.alpha_composite(tar.crop((16, cell_y, 32, cell_y + 16)), ((x - x0) * 16, (y - y0) * 16))
    img.alpha_composite(render(grid, sheets, frames, seed=2))
    trunk = Image.open("Content/Furniture/ScrappyTrunkTile.png").convert("RGBA")
    for (x, y), (kind, data) in w.extra.items():
        if not (x0 <= x < x1 and y0 <= y < y1):
            continue
        if kind == "trunk":
            style = 36
            for cx in range(2):
                for cy in range(2):
                    h = 16 if cy == 0 else 18
                    cell = trunk.crop((style + cx * 18, cy * 18, style + cx * 18 + 16, cy * 18 + h))
                    img.alpha_composite(cell, ((x - x0 + cx) * 16, (y - y0 + cy) * 16))
            dd = ImageDraw.Draw(img)
            cxp, cyp = (x - x0 + 1) * 16, (y - y0 + 1) * 16
            dd.ellipse([cxp - 40, cyp - 40, cxp + 40, cyp + 40], outline=(255, 199, 90))
    d = ImageDraw.Draw(img)
    for (px, py) in info["palms"]:
        if x0 <= px < x1:
            bx, by = (px - x0) * 16 + 8, (py - y0) * 16
            d.rectangle([bx - 3, by - 14 * 16 // 2, bx + 3, by], fill=(122, 92, 60))
            for k in range(-3, 4):
                d.line([bx, by - 14 * 16 // 2, bx + k * 14, by - 14 * 16 // 2 + abs(k) * 8], fill=(71, 145, 126), width=4)
    img = img.resize((img.width // 2, img.height // 2), Image.NEAREST)    # 16 px tiles at 2x art -> 1x art
    d = ImageDraw.Draw(img)
    d.text((4, 4), "pool rim | junkyard heaps + puddles (cache circled) | beach (palm stand-ins)", fill=(21, 22, 28))
    img.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--out-overview", required=True)
    ap.add_argument("--out-detail", required=True)
    a = ap.parse_args()
    w, info = generate(random.Random(a.seed))
    render_overview(w, info, a.out_overview)
    render_detail(w, info, a.out_detail)
    print({k: v for k, v in info.items() if k != "palms"}, "palms", len(info["palms"]))


if __name__ == "__main__":
    main()
