"""Co-op loot check for every Cogpunk boss (D2 rule 10, D3 rule 0; user 2026-11-05b: "make sure coop loot compatibility
is working, boss bags should drop for every player like default terraria does"). Run from the repo root:

    python -P tools/check_boss_loot.py [--root Content]

Why these rules (decompiled tModLoader v2026.08.3.0):
* ItemDropRule.BossBag(id) = DropBasedOnExpertMode(DropNothing(), DropLocalPerClientAndResetsNPCMoneyTo0(id)): in Expert
  and Master, CommonCode.DropItemLocalPerClientAndSetNPCMoneyTo0 makes one item on the server and sends it as an
  instanced item (message 90) to every active player whose npc.playerInteraction[i] is set, so each player who fought
  gets a bag of their own; in Classic nothing (the contents drop through LeadingConditionRule(NotExpert)).
* playerInteraction[i] is set by NPC.PlayerInteraction -> ApplyInteraction when player i strikes the NPC (the server on
  message 28, DamageNPC; NPC.StrikeNPC in singleplayer), credited to npc.realLife for linked parts. PlayerInteraction
  returns early when lastInteraction already equals the player, so code that writes lastInteraction can stop a player
  from ever being credited. NPC.StrikeInstantKill (BossNPC's finishing strike) passes noPlayerInteraction: true and so
  leaves the flags alone.
* An item spawned straight from a boss (Item.NewItem, SafeSpawn.TryNewItem, QuickSpawnItem) is one shared item: in a
  co-op game one player takes it and the others get nothing.

Checks (FAIL exits 1; WARN is informational):
1. FAIL: a boss (NPC.boss = true) whose ModifyNPCLoot has no ItemDropRule.BossBag(...).
2. FAIL: its bag class is missing ItemID.Sets.BossBag[Type] = true, Item.expert = true, Item.consumable = true,
   CanRightClick returning true, or ModifyItemLoot.
3. FAIL: Item.NewItem / TryNewItem / QuickSpawnItem / DropItemInstanced in a boss's folder (outside world generation).
4. FAIL: code anywhere in Content or Core assigning lastInteraction or playerInteraction.
5. FAIL: a boss without NPCID.Sets.MPAllowedEnemies[Type] = true (it could not be summoned by a multiplayer client).
6. WARN: no Classic drops under Conditions.NotExpert, or a bag without the boss's coins (CoinsBasedOnNPCValue).
"""
import argparse
import os
import re
import sys

BOSS_RE = re.compile(r"NPC\.boss\s*=\s*true")
CLASS_RE = re.compile(r"\bclass\s+(\w+)\b")
BAG_RE = re.compile(r"ItemDropRule\.BossBag\s*\(\s*ModContent\.ItemType<(\w+)>\s*\(\s*\)\s*\)")
SPAWN_RE = re.compile(r"\b(Item\.NewItem|TryNewItem|QuickSpawnItem|DropItemInstanced)\s*\(")
INTERACTION_RE = re.compile(r"\b(lastInteraction|playerInteraction\s*\[[^\]]*\])\s*=[^=]")


def cs_files(root):
    for base, _, files in os.walk(root):
        for f in files:
            if f.endswith(".cs") and not f.endswith("RigData.cs"):
                yield os.path.join(base, f)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def loot_text(boss_src, files_by_class):
    """The boss's own source plus the loot helpers it names (TrashTr0mLoot.AddBagContents and so on)."""
    text = boss_src
    for helper in set(re.findall(r"\b(\w+Loot)\.\w+\(", boss_src)):
        if helper in files_by_class:
            text += "\n" + files_by_class[helper]
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="Content")
    a = ap.parse_args()
    sources = {p: strip_comments(read(p)) for p in cs_files(a.root)}
    core = {p: strip_comments(read(p)) for p in cs_files("Core")} if os.path.isdir("Core") else {}
    files_by_class = {}
    for p, src in sources.items():
        for name in CLASS_RE.findall(src):
            files_by_class[name] = files_by_class.get(name, "") + "\n" + src
    fails, warns, bosses = [], [], []
    for p, src in sources.items():
        if not BOSS_RE.search(src):
            continue
        name = (CLASS_RE.findall(src) or ["?"])[0]
        bosses.append(name)
        folder = os.path.dirname(p)
        bag = BAG_RE.search(src)
        if not bag:
            fails.append("%s (%s): ModifyNPCLoot has no ItemDropRule.BossBag(...): its bag would not be one per player" % (name, p))
        else:
            bag_src = files_by_class.get(bag.group(1))
            if not bag_src:
                fails.append("%s: its bag class %s was not found" % (name, bag.group(1)))
            else:
                for (pattern, what) in ((r"ItemID\.Sets\.BossBag\[Type\]\s*=\s*true", "ItemID.Sets.BossBag[Type] = true"),
                                        (r"Item\.expert\s*=\s*true", "Item.expert = true"),
                                        (r"Item\.consumable\s*=\s*true", "Item.consumable = true"),
                                        (r"CanRightClick\s*\(\s*\)\s*(=>\s*true|\{\s*return\s+true\s*;)", "CanRightClick returning true"),
                                        (r"ModifyItemLoot\s*\(", "ModifyItemLoot")):
                    if not re.search(pattern, bag_src):
                        fails.append("%s: bag %s lacks %s" % (name, bag.group(1), what))
                if "CoinsBasedOnNPCValue" not in loot_text(bag_src, files_by_class):
                    warns.append("%s: bag %s has no CoinsBasedOnNPCValue (the bag drop zeroes the boss's own coins; check its gold)"
                                 % (name, bag.group(1)))
        if not re.search(r"NPCID\.Sets\.MPAllowedEnemies\[Type\]\s*=\s*true", src):
            fails.append("%s: NPCID.Sets.MPAllowedEnemies[Type] is not set (a multiplayer client could not summon it)" % name)
        if not re.search(r"new\s+Conditions\.NotExpert\s*\(", loot_text(src, files_by_class)):
            warns.append("%s: no Classic drops under Conditions.NotExpert" % name)
        for q, qsrc in sources.items():
            if os.path.dirname(q).startswith(folder) and "Generation" not in q and "WorldGen" not in q:
                for m in SPAWN_RE.finditer(qsrc):
                    line = qsrc[:m.start()].count("\n") + 1
                    fails.append("%s: %s:%d spawns an item directly (%s): one shared item, not one per player" % (name, q, line, m.group(1)))
    for q, qsrc in list(sources.items()) + list(core.items()):
        for m in INTERACTION_RE.finditer(qsrc):
            line = qsrc[:m.start()].count("\n") + 1
            fails.append("%s:%d assigns %s (vanilla's per-player loot credit; PlayerInteraction skips a player equal to lastInteraction)"
                         % (q, line, m.group(1)))
    print("bosses: %s" % (", ".join(sorted(bosses)) or "none"))
    for w in warns:
        print("[warn] " + w)
    for f in fails:
        print("[FAIL] " + f)
    if not fails:
        print("[ok] every boss drops ItemDropRule.BossBag: one bag per player who struck it, in Expert and Master")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
