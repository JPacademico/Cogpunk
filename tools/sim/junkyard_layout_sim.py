"""D5 simulation: how the Junkyard keeps vanilla's big structures away (Content/Junkyard/Generation/).

    python -P tools/sim/junkyard_layout_sim.py --rolls 300 --out docs/media/<date>_junkyard-structure-clearance.png

For each world size, rolls the side-dependent choices of vanilla's "Reset" pass (decompiled WorldGen: dungeon side,
beach widths, Dungeon x) and the "Shimmer" pass's position ranges many times, then plots them twice:
* vanilla: where the Dungeon and the Shimmer land without Cogpunk;
* Cogpunk: after JunkyardLayoutPass (mirrors a left Dungeon to the right), JunkyardReservePass (claims the footprint)
  and ShimmerPlacementPass (Shimmer x starts past the footprint + its 125-tile radius).
The red box is the reserved Junkyard footprint; a Shimmer marker is red when its 125-tile radius cuts into it.

Leaves out: real terrain (worldSurface/rockLayer use typical fractions of the world height), the Dungeon's actual
extent (its location is plotted as a 160-tile band), ShimmerMakeBiome's evil-stone retries, genRand (Python's RNG).
"""
import argparse
import random
from PIL import Image, ImageDraw

# --- mirrored from vanilla Reset/Shimmer passes and the Cogpunk passes ----------------------------------------------
BEACH_CENTER, BEACH_RANGE, DUNGEON_EXTRA, JUNGLE_EXTRA = 320, 20, 40, 20      # GenVars.beachSand* (Reset)
RESERVE_PADDING, BEACH_BELOW_SURFACE, BEACH_DROP, POOL_DROP = 30, 15, 3, 2      # JunkyardReservePass / JunkyardPass
MIN_POOL_DEPTH, FLOOR, DEPTH_FRACTION = 60, 6, 0.5
SHIMMER_RADIUS, CLEARANCE = 125, 10                                            # ShimmerPlacementPass
# ----------------------------------------------------------------------------------------------------------------------
SIZES = [("small", 4200, 1200), ("medium", 6400, 1800), ("large", 8400, 2400)]


def roll_world(rng, w, h):
    side = 1 if rng.randrange(2) else -1
    left_beach = rng.randrange(BEACH_CENTER - BEACH_RANGE, BEACH_CENTER + BEACH_RANGE)
    right_beach = w - rng.randrange(BEACH_CENTER - BEACH_RANGE, BEACH_CENTER + BEACH_RANGE)
    left_beach += DUNGEON_EXTRA if side == 1 else JUNGLE_EXTRA
    right_beach -= DUNGEON_EXTRA if side == -1 else JUNGLE_EXTRA
    dungeon = rng.randrange(left_beach + 50, int(w * 0.2)) if side == -1 else rng.randrange(int(w * 0.8), right_beach - 50)
    surface, rock = int(h * 0.27), int(h * 0.36)
    y_min = (surface + rock) // 2 + 50
    y_max = min(((h - 250) * 2 + rock) // 3, h - 460)
    return dict(side=side, left_beach=left_beach, right_beach=right_beach, dungeon=dungeon, surface=surface, rock=rock,
                y_min=y_min, y_max=max(y_max, y_min + 50))


def vanilla_shimmer(rng, w, wd):
    x = rng.randrange(int(w * 0.89), w - 200) if wd["side"] < 0 else rng.randrange(200, int(w * 0.11))
    return x, rng.randrange(wd["y_min"], wd["y_max"])


def cogpunk(rng, w, h, wd):
    wd = dict(wd)
    if wd["side"] < 0:                                   # JunkyardLayoutPass: mirror
        wd["side"] = 1
        wd["left_beach"], wd["right_beach"] = w - wd["right_beach"], w - wd["left_beach"]
        wd["dungeon"] = w - wd["dungeon"]
    right = min(wd["left_beach"], w // 4) + RESERVE_PADDING
    top = wd["surface"] + BEACH_BELOW_SURFACE + BEACH_DROP + POOL_DROP
    floor = top + int((h - 200 - top) * DEPTH_FRACTION)
    floor = max(top + MIN_POOL_DEPTH, min(floor, h - 260)) + FLOOR
    reserve = (0, 0, right, floor + RESERVE_PADDING)
    min_x = max(200, right + SHIMMER_RADIUS + CLEARANCE)
    max_x = int(w * 0.11) if int(w * 0.11) > min_x else int(w * 0.2)
    shimmer = (rng.randrange(min_x, max_x), rng.randrange(wd["y_min"], wd["y_max"]))
    return wd, reserve, shimmer


def cuts_reserve(shimmer, reserve):
    x, y = shimmer
    return x - SHIMMER_RADIUS < reserve[2] and y - SHIMMER_RADIUS < reserve[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rolls", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    panel_w, scale_x = 840, None
    rows = []
    stats = []
    for name, w, h in SIZES:
        van_d, van_s, cog_d, cog_s = [], [], [], []
        reserve = None
        for _ in range(a.rolls):
            wd = roll_world(rng, w, h)
            van_d.append(wd["dungeon"])
            van_s.append(vanilla_shimmer(rng, w, wd))
            cwd, reserve_i, shim = cogpunk(rng, w, h, wd)
            cog_d.append(cwd["dungeon"])
            cog_s.append((shim, reserve_i))
            reserve = reserve_i if reserve is None or reserve_i[3] > reserve[3] else reserve
        van_cut = sum(1 for s in van_s if cuts_reserve(s, reserve))
        van_left = sum(1 for d in van_d if d < w / 2)
        cog_cut = sum(1 for s, r in cog_s if cuts_reserve(s, r))
        cog_left = sum(1 for d in cog_d if d < w / 2)
        stats.append((name, van_left, van_cut, cog_left, cog_cut))
        rows.append((name, w, h, reserve, van_d, van_s, cog_d, [s for s, _ in cog_s], van_cut, van_left, cog_cut, cog_left))

    ph = 150
    img = Image.new("RGB", (panel_w * 2 + 30, 40 + len(rows) * (ph + 40)), (238, 241, 243))
    d = ImageDraw.Draw(img)
    d.text((10, 8), f"Junkyard structure clearance: {a.rolls} rolled worlds per size (left: vanilla, right: with Cogpunk)", fill=(21, 22, 28))
    for i, (name, w, h, reserve, van_d, van_s, cog_d, cog_s, van_cut, van_left, cog_cut, cog_left) in enumerate(rows):
        y0 = 40 + i * (ph + 40)
        for j, (dungeons, shimmers, label) in enumerate(((van_d, van_s, f"vanilla - Dungeon left in {van_left}/{a.rolls}, "
                                                            f"Shimmer cuts the Junkyard in {van_cut}/{a.rolls}"),
                                                           (cog_d, cog_s, f"Cogpunk - Dungeon left in {cog_left}/{a.rolls}, "
                                                            f"Shimmer cuts the Junkyard in {cog_cut}/{a.rolls}"))):
            x0 = 10 + j * (panel_w + 10)
            sx, sy = panel_w / w, ph / h
            d.rectangle([x0, y0, x0 + panel_w, y0 + ph], fill=(150, 180, 210))
            surface = int(h * 0.27)
            d.rectangle([x0, y0 + surface * sy, x0 + panel_w, y0 + ph], fill=(110, 92, 74))
            d.rectangle([x0, y0 + (h - 200) * sy, x0 + panel_w, y0 + ph], fill=(77, 20, 10))
            d.rectangle([x0, y0, x0 + reserve[2] * sx, y0 + reserve[3] * sy], outline=(163, 48, 26), width=2)
            for dx in dungeons:
                d.rectangle([x0 + (dx - 80) * sx, y0 + (surface - 20) * sy, x0 + (dx + 80) * sx, y0 + (surface + 140) * sy],
                            outline=(70, 58, 147))
            for (shx, shy) in shimmers:
                col = (236, 113, 40) if cuts_reserve((shx, shy), reserve) else (42, 94, 82)
                d.rectangle([x0 + shx * sx - 1, y0 + shy * sy - 1, x0 + shx * sx + 1, y0 + shy * sy + 1], fill=col)
            d.text((x0 + 4, y0 + ph + 4), f"{name} {w}x{h}: {label}", fill=(21, 22, 28))
    d.text((10, img.height - 16), "red box: reserved Junkyard footprint | purple: Dungeon band | dots: Shimmer centres "
           "(orange = its 125-tile radius cuts the footprint, teal = clear)", fill=(46, 50, 59))
    img.save(a.out)
    for s in stats:
        print("%-6s vanilla: dungeon left %3d, shimmer cuts %3d | cogpunk: dungeon left %3d, shimmer cuts %3d" % s)


if __name__ == "__main__":
    main()
