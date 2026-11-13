"""Check that every Cogpunk weapon has decided what it lends the Combinator as a base. Exit code 1 on failure.

    python -P tools/check_combinator.py [--root .]

The Combinator (Content/Combinator) can take any non-summon weapon. As a base, a weapon lends its passives (homing, a
debuff, ammo saving...), which no game keeps in data, so each Cogpunk weapon must say what they are (2026-11-12,
"compatibility for all future weapons"), in one of three places:

* its ModItem implements ``ICombinatorPassives`` (Core/Combat/CombinatorTrait.cs) and adds its own traits;
* it is registered in ``CombinatorTraits.PostSetupContent`` (``ModContent.ItemType<Name>()``);
* it is listed in ``CombinatorTraits.NoPassives`` (``nameof(Name)``): it has none, and that was decided.

A weapon here is a class deriving (directly or through our bases) from ModItem that sets ``Item.damage`` or calls a
vanilla ``DefaultTo...`` weapon helper, and is not a summon weapon (``DamageClass.Summon``/``SummonMeleeSpeed``, a whip),
a consumable or ammo, like ``CombinationRules.Check``. Also flags names in the lists that no longer exist.
"""
import argparse
import pathlib
import re
import sys

ITEM_BASES = {"ModItem"}
CLASS_RE = re.compile(r"^[ \t]*((?:\w+[ \t]+)*)class\s+(\w+)\s*(?:<[^>]*>)?\s*:\s*([\w.<>, ]+?)\s*(?:where\b|\{|$)", re.M)
WEAPON_HELPERS = ("DefaultToBow", "DefaultToMagicWeapon", "DefaultToRangedWeapon", "DefaultToStaff", "DefaultToSpear",
                  "DefaultToSword", "DefaultToThrownWeapon")
SUMMON_RE = re.compile(r"DamageClass\.(Summon|SummonMeleeSpeed)\b|DefaultToWhip")
NOT_WEAPON_RE = re.compile(r"Item\.consumable\s*=\s*true|Item\.ammo\s*=\s*(?!AmmoID\.None)|Item\.accessory\s*=\s*true")


def class_bodies(text):
    """(name, bases, body, abstract) for each class: the body runs to the next class declaration."""
    found = list(CLASS_RE.finditer(text))
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        bases = [b.strip().split("<")[0].split(".")[-1] for b in m.group(3).split(",")]
        yield m.group(2), bases, text[m.end():end], "abstract" in m.group(1).split()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = pathlib.Path(args.root)

    classes = {}
    for folder in ("Core", "Content"):                       # our item bases (CogpunkItem) live in Core
        for path in sorted((root / folder).rglob("*.cs")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for name, bases, body, abstract in class_bodies(text):
                classes[name] = (bases, body, path, abstract)

    # every class that is (transitively) a ModItem
    items = set()
    changed = True
    while changed:
        changed = False
        for name, (bases, _, _, _) in classes.items():
            if name not in items and any(b in ITEM_BASES or b in items for b in bases):
                items.add(name)
                changed = True

    traits_path = root / "Content/Combinator/Combination/CombinatorTraits.cs"
    traits = traits_path.read_text(encoding="utf-8")
    registered = set(re.findall(r"Register\(\s*ModContent\.ItemType<(\w+)>\(\)", traits))
    no_list = re.search(r"NoPassives\s*=\s*\{(.*?)\};", traits, re.S)
    if not no_list:
        print(f"FAIL: {traits_path}: no NoPassives list found")
        return 1
    no_passives = set(re.findall(r"nameof\((\w+)\)|\"(\w+)\"", no_list.group(1)))
    no_passives = {a or b for a, b in no_passives}

    weapons, declared = [], set()
    for name in sorted(items):
        bases, body, path, abstract = classes[name]
        if abstract or path.relative_to(root).parts[0] != "Content":
            continue
        sets_damage = re.search(r"Item\.damage\s*=", body) or any(h in body for h in WEAPON_HELPERS)
        if not sets_damage or SUMMON_RE.search(body) or NOT_WEAPON_RE.search(body):
            continue
        weapons.append((name, path))
        if "ICombinatorPassives" in bases:
            declared.add(name)

    failures = []
    for name, path in weapons:
        homes = (name in registered) + (name in no_passives) + (name in declared)
        rel = path.relative_to(root).as_posix()
        if homes == 0:
            failures.append(f"{rel}: {name} is a weapon the Combinator can take but says nothing of its passives: implement "
                            f"ICombinatorPassives, register it in CombinatorTraits, or add nameof({name}) to NoPassives")
        elif homes > 1:
            failures.append(f"{rel}: {name} is in more than one place (registered / NoPassives / ICombinatorPassives)")
    weapon_names = {n for n, _ in weapons}
    for stale in sorted((registered | no_passives) - weapon_names):
        if stale not in classes:
            failures.append(f"{traits_path.relative_to(root).as_posix()}: {stale} is listed but no such class exists")

    print(f"{len(weapons)} weapons: {len(registered & weapon_names)} registered, {len(no_passives & weapon_names)} with no "
          f"passives, {len(declared)} declaring their own")
    if failures:
        for f in failures:
            print("FAIL:", f)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
