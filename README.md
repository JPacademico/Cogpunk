# Cogpunk

> A steampunk content mod for **Terraria** built on **tModLoader**: brass, steam, clockwork and aether, from the first copper pickaxe to post–Moon Lord.

| | |
|---|---|
| **Status** | M0 framework done. First content: the Rusted Scrap slice (block, world gen, materials, Scrappybot pet, Scrap Bomb, Scrap armor), 2026-10-21; the Junkyard biome (replaces the left beach), 2026-10-22; Junkyard tar pool and spawn rules, first boss Trash-Tr0m (summon + intro), 2026-10-23; Trash-Tr0m's full fight (3/4-view multiplane rework, crawl, slam, suction, Lost Key, Junkbait summon, death cinematic), 2026-10-26; then its loot (treasure bag, Tetanus, Scrap Launcher, Scrapmancer, Tr0mhead Staff), in-between animation frames, the cache's Polisher Schematic (Rust Polisher station) and Mysterious Map, and the Junkyard's first enemies (Rust Collector, Living Tar), 2026-10-26; the Mechanist class and its Steam, the Trapper, and the **Mech Army** invasion (Rogue Mice-bots, Boombots, Annoy-o-trons, Trappers and the Jaeger miniboss; after Trash-Tr0m, the goblin army's rules), 2026-10-27; its drops (Rusted Metal, Scrap Bombs, the Alarm Head summon, the Jaeger armor, the Cogpunker Manual and its steam dash), 2026-10-28; Tar Tyrant (T2, fished out of the Junkyard tar with a Scrapworm), the Puxa-frango, the Polished Cog, 2026-10-28; Tar Tyrant reworked as a T3 boss (a hunched mass of tar with dinosaur bones sticking out of it and a horned skull, 100 tweened frames, four attacks and bones flung out of its back every 3.5 s, sheds Living Tar and shrinks as it bleeds, an enrage with tar claws; drops Bones, Tar Drops, at least one piece of the Tyrant mage armor (a berserker's horned skull, cape, loincloth and sandals) and the Serene Tear), 2026-10-29/30; Trash-Tr0m's cogs slowed to one every 2.5 s, 2026-10-29; Condensed Tar (4 Tar Drops at a Solidifier), 2026-10-30 |
| **Platform** | tModLoader stable (1.4.4 line, monthly `v2026.MM.x` releases), C# / .NET 8 |
| **Mode support** | Singleplayer, host-and-play and dedicated-server multiplayer |
| **Languages** | English (source), Brazilian Portuguese (`pt-BR`) |
| **Setup guide** | [SETUP.md](SETUP.md) |
| **Dev rules for Claude** | [.claude/skills/cogpunk-dev/SKILL.md](.claude/skills/cogpunk-dev/SKILL.md) and [CLAUDE.md](CLAUDE.md) |

---

## 1. Vision

Cogpunk adds a full **industrial-steampunk layer** to Terraria's progression. You find the ruins of a forgotten clockwork civilization, salvage its machines, and take on the automatons that still guard them. The mod adds a new **class** built around managing steam pressure, plus weapons for every vanilla class, armor sets, biomes, enemies, bosses, materials, and hand-animated pixel art that looks like it belongs next to vanilla Terraria.

## 2. Objectives

These are the conditions that count as success. Each one maps to a [Core Directive](#4-core-directives-non-negotiable).

0. **Never crashes.** No implementation may crash the game, a server or world generation, or flood the log in a loop. This is the most important objective. *(D0)*
1. **Cohesive progression.** Steampunk content at every major vanilla tier, from pre-boss to post–Moon Lord. It never skips vanilla gates: no Hardmode-strength gear before the Wall of Flesh.
2. **A complete new class.** A *Mechanist* class (working name) with its own resource, playable from start to finish with weapons, armor, and accessories at every tier.
3. **Co-op first.** Every feature works on a dedicated server and in host-and-play with 2+ players, with no desyncs, duplicate drops, or "ghost" projectiles. *(D2)*
4. **Light on performance.** No allocations in per-tick code. Boss fights with several players run at a steady 60 FPS on the team's reference PC. *(D1)*
5. **Fair balance, built for Expert.** Cogpunk is meant to be played on Expert: every combat number is the Expert value, checked against a vanilla anchor of the same tier in Expert. Classic and Master scale from it the way vanilla does, and boss treasure bags drop only in Expert and Master. *(D3)*
6. **Vanilla-grade pixel art.** All art is hand-made: drawn at 1×, exported at 2×, with a locked palette and no mixels. *(D4)*
7. **Proven visually.** Every animated feature or fix comes with a GIF, and every static sprite with a PNG. Both are built from the animation frames or a quick simulation, so no in-game recording is needed. *(D5)*

## 3. Design pillars

| Pillar | Meaning in practice |
|---|---|
| **Brass & Steam** | Industrial, clockwork, pressure and heat. Materials are brass, copper, iron, verdigris and, late in the game, aether. Effects are steam puffs, sparks, rivets and gears. |
| **Mechanical mastery** | Risk and reward through steam management: every Mechanist attack spends steam, the tank only refills once you stop attacking, and firing on an empty tank overheats you. |
| **Vanilla-faithful** | The mod reads, sounds, and plays like a Terraria update, not a different game. It respects vanilla UI, controls, and progression pacing. |
| **Play together** | Bosses and events are designed for groups. They retarget, have readable telegraphs, and give every player their own loot. |

## 4. Core Directives (non-negotiable)

Every feature, fix, and asset must meet all six. **D0 is the most important and wins every conflict.** The full rules and checklists are in the [project skill](.claude/skills/cogpunk-dev/SKILL.md).

| ID | Directive | One-line rule |
|---|---|---|
| **D0** | **No crashes, guaranteed** | Nothing may crash the game, server or world generation, or cause a console loop. Anything that could is checked against vanilla's limits (verified by decompiling) and guarded or redesigned. Spawns, logging, tiles, packets and world generation go through the crash-safe `Core/` framework. |
| **D1** | **Optimization** | No allocations, LINQ, or uncached assets in per-tick or draw code. Visuals only run on clients. Netcode only syncs when something changes. |
| **D2** | **Co-op compatibility** | The server decides world, NPC, and random outcomes. Projectiles from players belong to their owner. Every change is tested in singleplayer, host plus client, and on a dedicated server when there is server logic. |
| **D3** | **Balance** | Every combat stat has a row in `docs/balance/` with a vanilla anchor of the same tier, staying within ±15% of the anchor's effective DPS unless there's a documented trade-off. |
| **D4** | **Pixel art** | Drawn at 1× and exported at 2× nearest-neighbor. Uses the Cogpunk palette, lit from the top-left, with ramp-colored outlines and no mixels or semi-transparent pixels. |
| **D5** | **Visual proof** | Any animated feature or fix includes a GIF, and static visuals include a PNG. Both are generated from animation frames or a lightweight simulation (in-game capture is optional), then shown in the response and/or saved to `docs/media/`. |

## 5. Content scope

| Area | What Cogpunk adds | tModLoader building blocks |
|---|---|---|
| **Weapons** | Steampunk weapons for melee, ranged, magic, and summoner, plus the Mechanist arsenal: steam firearms, piston gauntlets, and deployable automatons. Many use animated held projectiles. | `ModItem`, `ModProjectile` (held projectiles), `Item.DamageType` |
| **Class system** | The *Mechanist* damage class with a **Steam** resource (built 2026-10-27, user-set): Mechanist weapons spend steam the way magic weapons spend mana. A player has no tank of their own: Mechanist armor and steam containers (Glass Container from Wooden Chests, Brass Container from the Rust Polisher) give the capacity. After 1.5 s without attacking it refills 10 every 0.5 s. Firing without enough steam causes *Overheat*: no items and no stopping until the tank is full again. A steampunk gauge sits left of the hearts. First set: Polished armor (Rust Polisher). It has 3 planned archetypes: **Gunsmith** (ranged-style), **Brawler** (melee-style), and **Tinker** (sentries and automatons). | `DamageClass`, `ModPlayer` resource, UI layer |
| **Armors** | One set per tier for each archetype, plus vanilla-class sets, with set bonuses that interact with Pressure. | `[AutoloadEquip]` `_Head/_Body/_Legs`, `UpdateArmorSet` |
| **Biomes** | 3 biomes. *The Foundry*: underground industrial ruins (pre-Hardmode). *Skyport*: floating docks and airship wrecks (Hardmode). *The Clockcore*: deep mechanical heart (late game). | `ModBiome`, tile counts, backgrounds, `ModWaterStyle`, world generation passes |
| **Underground** | The **Puxa-frango**, a rare cave robot that stalks, lunges and yanks you in with its pincers (drops the Chicken Snapper); the **Scrapworm**, a rare critter caught with a bug net. | `ModNPC` (`GridWalkerNPC`), `SpawnChance`, critters (`catchItem`) |
| **Events** | Invasions built on vanilla's goblin-army rules (`Core/Events/CogpunkInvasion`). First: the **Mech Army** (after Trash-Tr0m; at dawn with the goblin army's odds, ahead of vanilla's invasions): Rogue Mice-bots, Boombots that blow up on contact, Annoy-o-trons whose alarm speeds up every enemy around them, Trappers, and from halfway through the Jaeger, a jaeger-sized miniboss. They drop coins at the goblins' values, Rusted Metal, Scrap Bombs (Boombot), the Alarm Head summon (Annoy-o-tron), the Jaeger armor and the Cogpunker Manual (Jaeger). Hardmode adds enemies and buffs (to be designed). | `ModSystem`, spawn pools, a progress bar UI layer, a `ModCommand` for testing |
| **Mobs** | 4–6 enemies per biome: crawlers, flyers, turrets, tanks, and casters, each with its own role and readable attacks. | `ModNPC`, `SpawnChance`, bestiary entries, banners |
| **Bosses** | 3 main bosses and an optional superboss, each with phases, telegraphed attack patterns, Expert/Master variants, treasure bags, relics, and trophies. | `ModNPC` (`boss = true`), loot rules, `BossBag`, Boss Checklist integration |
| **Materials** | Ore, bars, salvaged components, and two crafting stations, all integrated with vanilla recipes. | `ModTile` ore, `ModItem`, `Recipe`, world generation |
| **Animations** | Animated items, projectiles, NPCs, tiles, glowmasks, gores, and dusts. | `DrawAnimationVertical`, `Main.projFrames`, `FindFrame`, `AnimateTile`, `ModDust`, `ModGore` |
| **Attack patterns** | State-machine AI with synced state, telegraphs, phase transitions, and co-op targeting. | `NPC.ai[]` + `netUpdate`, `SendExtraAI` / `ReceiveExtraAI` |

### Proposed progression map (draft, working names)

> All names below are **placeholders** for design review. Vanilla already uses *Cog*, *Steampunk Boiler*, *Tinkerer's Workshop*, the *Steampunk* armor and wings, and *Clockwork Assault Rifle*, so don't reuse those names.

| Tier | Vanilla gate | Cogpunk content (draft) |
|---|---|---|
| T0 | Pre-boss | *Foundry* biome generated in the cavern layer. *Zincite* ore, *Brass Bar* (Zincite + Copper/Tin bar), *Steam Forge* crafting station, starter Mechanist weapons, *Gearwork Scrap* drops |
| T2–T3 | Post-evil boss / Skeletron | Boss 1, *Boilerheart*, summoned in the Foundry. Brass armor sets, first Pressure accessories |
| T4 | Pre–Wall of Flesh | Foundry depths, Overheat-tier weapons |
| T5–T6 | Early Hardmode / post-mechs | *Skyport* biome, Boss 2 *The Clockwork Leviathan* (an airship with breakable cannons, co-op friendly), *Steam Core* material, *Clockwork Assembler* station |
| T7–T8 | Post-Plantera / Golem | *Clockcore* biome, Boss 3 *The Grand Orrery* (rotating clockwork rings and celestial bullet patterns), *Aether Spring* material |
| T10 | Post–Moon Lord (optional) | Superboss *Chronarch* (time manipulation patterns), endgame Mechanist set |

## 6. Technical baseline

- **tModLoader stable** on Steam, 1.4.4 line, updated monthly on the 1st. **.NET 8 SDK**, C# `LangVersion latest`.
- **Terraria 1.4.5** came out in January 2026, but tModLoader's 1.4.5 port is still in development. Its `1.4.5-dev` Steam branch is for contributors only, and you shouldn't publish mods on it. Cogpunk targets 1.4.4 stable and will port with **tModPorter** and `MigrationGuide_1.4.5.md` once the 1.4.5 stable release ships. To keep that port cheap, prefer public tModLoader hooks over IL edits, detours, or reflection.
- Code follows the official **ExampleMod** (branch **`1.4.4`**) patterns and `.editorconfig`.
- Art is made in Aseprite, with source files in `art/` and 2× PNG exports next to the C# class that uses them.

## 7. Roadmap

| Milestone | Goal | Exit criteria |
|---|---|---|
| **M0: Scaffolding** (in progress) | Repo, toolchain, and an empty mod that builds and loads | Builds with no warnings. Loads in singleplayer and in host plus client. GIF/sprite tooling verified. Test worlds created. |
| **M1: Vertical slice** | Foundry biome, Zincite → Brass chain, Steam Forge, Mechanist core (class, Pressure, UI, Vent), 3 weapons (one per archetype), 1 armor set, 4 mobs, Boilerheart | All five directives met. Balance rows filled in. A GIF for every animated piece. Playtested in co-op. |
| **M2: Pre-Hardmode complete** | All T0–T4 content | Same as M1, plus a full pre-Hardmode playthrough in co-op |
| **M3: Hardmode** | Skyport, Clockwork Leviathan, T5–T6 content | Same as M1 |
| **M4: Late game** | Clockcore, Grand Orrery, T7–T10 content | Same as M1 |
| **M5: Release** | Polish, pt-BR translation, Boss Checklist integration, final balance pass, Workshop page | Published on the Steam Workshop |
| **M6: 1.4.5 port** | Move to tModLoader 1.4.5 once it's stable | tModPorter run. Migration guide applied. Regression test matrix passes. |

## 8. Out of scope (for now)

- Subworlds or dimensions (SubworldLibrary), new invasions or events, and town NPCs. These can be revisited after M3.
- Hard dependencies on other content mods. Integration only goes through weak references and `Mod.Call` (for example Boss Checklist).
- Mobile and console. tModLoader only runs on PC.

## 9. Repository layout

```
Cogpunk/                          ← repo root = C:\tML\ModSources\Cogpunk
├─ CogpunkMod.cs                  Mod entry point (thin): Load/Unload, packet dispatch
├─ Cogpunk.csproj · build.txt · description*.txt · icon.png (80²) · icon_small.png (30²)
├─ global.json · .editorconfig · .gitignore · .gitattributes · Properties/launchSettings.json
├─ Core/                          ENGINE: no player-facing content
│  ├─ Networking/                 CogpunkPacket (one class per message), PacketRegistry (crash-safe dispatch)
│  ├─ Safety/                     SafeSpawn, SpawnBudgetSystem, SafeLog, TileSafety, MathSafety   (D0)
│  ├─ Templates/                  CogpunkItem/NPC/Projectile/Tile/Wall/Buff, StateMachineNPC, TextureFallback
│  ├─ Systems/                    WorldFlagSystem (named, saved, synced flags), CrossMod (safe Mod.Call)
│  ├─ WorldGeneration/            SafeGenPass, GenPassUtils.InsertAfter
│  └─ Configs/                    CogpunkClientConfig (visuals and accessibility only)
├─ Content/                       GAMEPLAY, one folder per feature slice (added from M1 on):
│  ├─ Mechanist/                    class system: DamageClass, Pressure ModPlayer, UI, Vent keybind
│  ├─ Foundry/                      biome slice: Biome/ Tiles/ Walls/ Items/ NPCs/ WorldGen/ + FoundrySystem.cs
│  ├─ Bosses/<Boss>/                boss + minions, projectiles, summon item, bag, relic, trophy, gores
│  └─ Materials/  Arsenal/<Class>/  shared materials, weapons that belong to no single slice
├─ Assets/                        shared only: Textures/Placeholder.png, Sounds/, Music/, Effects/
├─ Localization/                  en-US_Mods.Cogpunk.hjson · pt-BR_Mods.Cogpunk.hjson
├─ art/                           palettes/cogpunk.gpl · scaffold/ · .aseprite sources mirroring Content/   ← not in .tmod
├─ docs/                          balance/*.csv + loadouts.md · design/ · media/ (D5 GIF/PNG)              ← not in .tmod
├─ tools/                         check_sprite.py · sheet2gif.py · sim/ · record-gif.ps1 (optional)        ← not in .tmod
└─ .claude/skills/cogpunk-dev/SKILL.md · CLAUDE.md · README.md · SETUP.md
```

How the structure was chosen, and its rules: [SKILL.md §3.0](.claude/skills/cogpunk-dev/SKILL.md).

## 10. Docs index

| File | Purpose |
|---|---|
| [README.md](README.md) | This overview: vision, objectives, scope, roadmap |
| [SETUP.md](SETUP.md) | Toolchain, plugins, dev mods, and scaffolding data and procedure |
| [CLAUDE.md](CLAUDE.md) | Always-loaded project rules for Claude Code |
| [.claude/skills/cogpunk-dev/SKILL.md](.claude/skills/cogpunk-dev/SKILL.md) | Detailed development skill: directives, workflow, API patterns, Definition of Done |
