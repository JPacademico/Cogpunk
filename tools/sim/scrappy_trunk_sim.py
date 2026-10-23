"""D5 replay of the Scrappy Trunk world-generation rules (Content/Furniture/Generation/ScrappyTrunkPass.cs and
ScrappyTrunkLoot.cs), with the same constants.

    python -P tools/sim/scrappy_trunk_sim.py --chests 120 --worlds 200 --out docs/media/<date>_furniture-scrappy-trunk-loot.png

Rolls `--worlds` worlds with `--chests` plain Wooden Chests each (a stand-in count; real worlds vary), replaces each with
a trunk at 20%, fills every trunk with the loot table and prints the statistics. The PNG shows four sample trunks
(the real trunk and Rusted Scrap sprites; vanilla items as text, no vanilla art copied) and the summary.

Leaves out: which chests qualify (only plain, unwired Wooden Chests do; this replays the dice, not the world scan),
trinkets (none are flagged yet), genRand (Python's RNG: same rules, different rolls).
"""
import argparse
import random
import statistics
from PIL import Image, ImageDraw

# --- mirrored from ScrappyTrunkPass.cs / ScrappyTrunkLoot.cs --------------------------------------------------------
REPLACE_CHANCE = 20
MIN_SCRAP, MAX_SCRAP, MIN_ORE, MAX_ORE, MIN_COINS, MAX_COINS, SECOND_ORE = 10, 30, 5, 15, 20, 99, 2
ORES = ["Copper Ore", "Tin Ore", "Iron Ore", "Lead Ore", "Silver Ore", "Tungsten Ore", "Gold Ore", "Platinum Ore"]
# ---------------------------------------------------------------------------------------------------------------------


def fill(rng, trinkets=()):
    items = []
    if trinkets:
        items.append((rng.choice(trinkets), 1))
    items.append(("Rusted Scrap", rng.randint(MIN_SCRAP, MAX_SCRAP)))
    first = rng.randrange(len(ORES))
    items.append((ORES[first], rng.randint(MIN_ORE, MAX_ORE)))
    if rng.randrange(SECOND_ORE) == 0:
        second = (first + 1 + rng.randrange(len(ORES) - 1)) % len(ORES)
        items.append((ORES[second], rng.randint(MIN_ORE, MAX_ORE)))
    items.append(("Copper Coin", rng.randint(MIN_COINS, MAX_COINS)))
    return items


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--chests", type=int, default=120)
    a.add_argument("--worlds", type=int, default=200)
    a.add_argument("--seed", type=int, default=9)
    a.add_argument("--out", required=True)
    args = a.parse_args()
    rng = random.Random(args.seed)
    per_world, trunks = [], []
    for _ in range(args.worlds):
        n = sum(1 for _ in range(args.chests) if rng.randrange(100) < REPLACE_CHANCE)
        per_world.append(n)
        trunks.extend(fill(rng) for _ in range(n))
    scrap = [s for t in trunks for (name, s) in t if name == "Rusted Scrap"]
    coins = [s for t in trunks for (name, s) in t if name == "Copper Coin"]
    ore_kinds = [sum(1 for (name, _) in t if name in ORES) for t in trunks]
    ore_counts = {o: 0 for o in ORES}
    for t in trunks:
        for (name, _) in t:
            if name in ORES:
                ore_counts[name] += 1
    lines = [
        f"{args.worlds} worlds x {args.chests} plain Wooden Chests: {statistics.mean(per_world):.1f} trunks per world "
        f"({statistics.mean(per_world) / args.chests * 100:.1f}%, min {min(per_world)}, max {max(per_world)})",
        f"Rusted Scrap {min(scrap)}-{max(scrap)} (avg {statistics.mean(scrap):.1f}); copper coins {min(coins)}-{max(coins)} "
        f"(avg {statistics.mean(coins):.1f}); two ores in {sum(1 for k in ore_kinds if k == 2) / len(trunks) * 100:.0f}% of trunks",
        "ore picks: " + ", ".join(f"{o.split()[0]} {c / len(trunks) * 100:.0f}%" for o, c in ore_counts.items()),
    ]
    for line in lines:
        print(line)

    trunk = Image.open("Content/Furniture/ScrappyTrunk.png").convert("RGBA")
    scrap_icon = Image.open("Content/Scrap/Items/RustedScrap.png").convert("RGBA")
    samples = trunks[:4]
    cell, z = 46, 2
    W = 4 * (5 * cell + 24) + 20
    img = Image.new("RGB", (W, 200), (238, 241, 243))
    d = ImageDraw.Draw(img)
    for k, items in enumerate(samples):
        x0 = 10 + k * (5 * cell + 24)
        big = trunk.resize((trunk.width * z, trunk.height * z), Image.NEAREST)
        img.paste(big, (x0, 8), big)
        d.text((x0 + big.width + 8, 22), f"trunk {k + 1}", fill=(21, 22, 28))
        for i in range(5):
            cx, cy = x0 + i * cell, 80
            d.rectangle([cx, cy, cx + cell - 4, cy + cell - 4], fill=(70, 58, 147), outline=(34, 26, 69))
            if i < len(items):
                name, stack = items[i]
                if name == "Rusted Scrap":
                    icon = scrap_icon.resize((scrap_icon.width * 2, scrap_icon.height * 2), Image.NEAREST)
                    img.paste(icon, (cx + 5, cy + 4), icon)
                else:
                    d.text((cx + 3, cy + 6), name.replace(" Ore", "").replace(" Coin", "\ncoin"), fill=(246, 231, 161))
                d.text((cx + 22, cy + 28), str(stack), fill=(238, 241, 243))
    for i, line in enumerate(lines):
        d.text((10, 140 + i * 16), line, fill=(46, 50, 59))
    img.save(args.out)
    print(args.out, img.size)


if __name__ == "__main__":
    main()
