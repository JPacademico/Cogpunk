---
name: cogpunk-dev
description: Mandatory rules and workflow for ALL work on Cogpunk, the steampunk tModLoader (Terraria) content mod. Covers weapons, items, armor, the Mechanist class and Steam Pressure resource, biomes, tiles, world generation, mobs, bosses, AI and attack patterns, projectiles, animations, sprites and pixel art, sounds, netcode, balance, and visual verification (GIFs). Use it before writing, changing, or reviewing any Cogpunk code or asset, and when reporting a finished feature or fix.
---

# Cogpunk development skill

Cogpunk is a steampunk content mod for tModLoader. The project overview is in `README.md`, and the toolchain, paths, and scaffolding specs are in `SETUP.md`. This skill is the **operating manual**. Its six Core Directives (D0–D5) apply to **every** feature, fix, and asset. **D0 (no crashes) is the most important and wins every conflict.** A task is not done until all applicable directives are checked off with evidence (§6).

---

## 0. Ground truth (verified 2026-10-20; re-check monthly)

| Fact | Value |
|---|---|
| Target | **tModLoader stable, 1.4.4 line** (monthly `v2026.MM.x`; October 2026 stable = `v2026.08.3.0`) |
| Not a target | The tModLoader `1.4.5` branch / `1.4.5-dev` Steam beta (contributors only, unstable, don't publish) |
| SDK / language | .NET **8** SDK (pinned with `global.json`), C# `LangVersion latest` |
| Repo / mod folder | `C:\tML\ModSources\Cogpunk` (data folder set with `-tmlsavedirectory C:\tML`; see SETUP §3) |
| Build | `dotnet build` in the repo folder, then *Build + Reload* in-game. Close or disable the mod first if `Cogpunk.tmod` is locked. |
| Compile check without Steam | `dotnet msbuild -restore -t:Compile -p:RunAnalyzers=false` against the reference build in `C:\tML\_reference\tModLoader-v2026.08.3.0` (`..\tModLoader.targets` points there until Steam tModLoader is installed, which rewrites it on launch). Output: `obj/Debug/net8.0/Cogpunk.dll`. |
| Decompiler | `ilspycmd` (dotnet global tool, `%USERPROFILE%\.dotnet\tools`). Vanilla source: `ilspycmd -t Terraria.Projectile C:\tML\_reference\tModLoader-v2026.08.3.0\tModLoader.dll`. Decompiled files are cached in `C:\tML\_reference\decomp\` (Main, NPC, Projectile, Item, Dust, Gore, ModContent, Mod...). |
| Architecture | `Core/` = engine (no content), `Content/<Slice>/` = gameplay grouped by feature. See §3.0 and SETUP §8.2. |
| API reference, in priority order | (1) ExampleMod **branch `1.4.4`**: `https://raw.githubusercontent.com/tModLoader/tModLoader/1.4.4/ExampleMod/<path>` (2) the tModLoader wiki (3) DeepWiki MCP, which indexes the **1.4.5** default branch, so cross-check it against 1.4.4 |
| Vanilla numbers | terraria.wiki.gg (1.4.4 values). **Never from memory.** |

**Never invent an API.** If you aren't sure a hook or field exists in 1.4.4, open the matching ExampleMod file (§2.1) or the tModLoader 1.4.4 source before using it.

---

## 1. Core Directives

### D0: No crashes, guaranteed (top priority)

Cogpunk must never crash the game, the server, or world generation, and must never cause a **console loop** (an error or log line repeating every tick). If an implementation *could* crash or loop, check it against the vanilla limits below. Use decompiled vanilla code (`ilspycmd`) when behavior is unclear, then guard, fix, or redesign it **before** it ships. D0 beats every other directive: if a faster or prettier version is riskier, choose the safe one.

**Vanilla limits** (verified by decompiling tModLoader v2026.08.3.0):

| Limit | Value | What vanilla does at the limit |
|---|---|---|
| NPCs | `Main.maxNPCs` = 200 (array of 201) | `NPC.NewNPC` returns **200**, a dummy slot. Treating it as a real NPC corrupts state. |
| Projectiles | `Main.maxProjectiles` = 1000 (array of 1001) | `Projectile.NewProjectile` **never fails: it overwrites the oldest projectile**, which can be a boss attack or a player's minion. |
| Dust | `Main.maxDust` = 6000 | `Dust.NewDust` returns **6000** (dummy) when full, when paused, and in other early-out cases |
| Items | `Main.maxItems` = 400 | `Item.NewItem` returns **400** (dummy) |
| Gore | `Main.maxGore` = 600 | `Gore.NewGore` returns **600** (dummy) |
| Players | `Main.maxPlayers` = 255 (array of 256) | Index 255 is the server / "no player". Never treat it as a real player. |
| Player buffs | 44 + extra slots requested by mods | Further buffs are dropped |
| `NPC.ai` / `localAI` | 4 entries each | Index 4+ throws `IndexOutOfRangeException` |
| `Projectile.ai` / `localAI` | 3 entries each | Index 3+ throws |
| Tiles | `0 ≤ x < Main.maxTilesX`, `0 ≤ y < Main.maxTilesY` | `Main.tile[x, y]` out of range throws. Edits near the edge break framing. |
| Type IDs | `0 < type < ItemLoader.ItemCount / NPCLoader.NPCCount / ProjectileLoader.ProjectileCount` | An invalid id makes `SetDefaults` index out of range and crashes |
| Packet IDs | Cogpunk packets use a byte id (≤ 256 types) | `PacketRegistry` refuses more at load time |
| Server textures | `ModContent.HasAsset` is always false and `Asset.Value` is not loaded on a dedicated server | Touching texture `.Value` on the server crashes or misbehaves |

MUST:
1. **Spawn only through `Core/Safety/SafeSpawn`** (`TryNewNPC`, `TryNewProjectile`, `TryNewDust`, `TryNewItem`) and handle `false`. These validate type ids and NaN, refuse instead of overwriting, keep reserve slots for vanilla (100 projectiles, 20 NPCs), and enforce server-only NPC and item spawns. `critical: true` only for a spawn that must happen, such as the boss itself.
2. **Tiles:** any computed, random or networked coordinate goes through `TileSafety.InWorld` / `TryGetTile` before `Main.tile[x, y]`.
3. **Every loop has a fixed cap.** No `while (!placed)` without an attempt counter, no recursion without a depth limit. That includes world generation, pathfinding and retry logic.
4. **No feedback loops:** an `OnHit` that spawns a projectile that triggers `OnHit` again, or an `OnKill` that spawns copies of itself, needs a generation counter or a cooldown. Exponential spawns are a crash.
5. **Math:** use `SafeNormalize(Vector2.Zero)`, `MathSafety.SafeDivide`, and check `MathSafety.IsFinite` before using computed positions or velocities. `Main.rand.Next(n)` needs `n > 0`, and `Next(min, max)` needs `max > min`, otherwise it throws.
6. **Logging:** only through `Core/Safety/SafeLog`, which reports each key at most 3 times. Never log per tick, and never interpolate strings in a hot path: use the `Warn(key, format, arg)` overloads.
7. **Network:** packets inherit `CogpunkPacket`. `Receive` reads exactly what was written and **validates every index** (player < `Main.maxPlayers` and active, npc < `Main.maxNPCs` and active, tile coordinates in world) before using it. `PacketRegistry` catches exceptions and drops the packet.
8. **World generation:** passes inherit `SafeGenPass`, which catches exceptions so world creation continues, and are inserted with `GenPassUtils.InsertAfter`, which falls back to appending if the anchor pass is missing.
9. **Save data:** read `TagCompound` keys with `ContainsKey` or `Get*`, which return defaults. Never assume a key exists. Older worlds and players must load. Save by name, never by numeric id (as `WorldFlagSystem` does).
10. **Assets:** content inherits `Core/Templates` bases (`CogpunkItem`, `CogpunkNPC`, `CogpunkProjectile`, `CogpunkTile`, `CogpunkWall`, `CogpunkBuff`), whose missing-texture fallback means missing art never blocks loading. Never touch `Texture2D` or `.Value` on a dedicated server (`if (!Main.dedServ)`).
11. **Drawing:** every `SpriteBatch.End()` is matched by a `Begin()` that restores the previous state, even on early return. An unbalanced Begin/End throws every frame.
12. **Unloading:** set static fields to null and clear static collections in `Unload` (`CogpunkMod.Unload`, `ModSystem.Unload`). Reset per-world state in `ClearWorld` / `OnWorldUnload`.
13. **Cross-mod:** only through `CrossMod.TryCall` (try/catch, optional). Never a hard dependency.
14. **No IL edits or detours without a fallback.** If one is unavoidable, wrap the edit in try/catch and log once, so a vanilla or tModLoader update disables the feature instead of crashing the game.
15. **Catch at boundaries, not everywhere.** Use try/catch around packet handlers, world-generation passes, save-data loading, cross-mod calls and IL edits. Never use it inside per-tick loops (exceptions are slow, and swallowing them hides bugs). Fix the root cause instead.

Verify: list each risk this change touches (spawns, loops, indices, tiles, NaN, network, save data, assets, drawing) and how it's guarded. When a vanilla method's behavior matters, decompile it and quote the relevant lines in the report. Then stress-test the worst case, for example a boss attack with the projectile array nearly full, or worldgen on a small and a large world.

### D1: Optimization

**Hot paths** are everything that runs every tick or every frame: `AI`, `PreAI/PostAI`, `Update*`, `PostUpdate*`, `UpdateEquip`, `UpdateAccessory`, `UpdateArmorSet`, `ModifyHit*`, `OnHit*`, `PreDraw/PostDraw`, `FindFrame`, `AnimateTile`, `NearbyEffects`, `ModSystem.PostUpdate*`, UI `Draw`/`Update`.

MUST:
1. **Zero heap allocations in hot paths.** No `new` of classes, arrays or lists, no LINQ, no lambdas or closures, no string concatenation or interpolation, no `params` calls, no boxing. Preallocate in `SetStaticDefaults`/`Load` and reuse.
2. Iterate entities with the allocation-free iterators `foreach (NPC npc in Main.ActiveNPCs)`, `Main.ActiveProjectiles`, `Main.ActivePlayers`. Compare ranges with `Vector2.DistanceSquared(a, b) < r * r`.
3. **Assets:** request once and cache an `Asset<Texture2D>` in a static field during `Load()`/`SetStaticDefaults()`, inside `if (!Main.dedServ)`. Set statics to `null` in `Unload()`. Use `.Value` when drawing. Never use `AssetRequestMode.ImmediateLoad` inside update or draw.
4. **Visual-only work runs on clients only:** dust, gore, particles, screen shake, telegraph drawing and sound go inside `if (!Main.dedServ)`. Throttle dust with `Main.rand.NextBool(n)`, at most about 3 dust per entity per tick unless it's a one-shot burst.
5. **Drawing:** don't `End()`/`Begin()` the `SpriteBatch` per entity. If you change the blend state, restore the exact previous state. Group additive glows together.
6. **Globals:** every `GlobalNPC`/`GlobalItem`/`GlobalProjectile` overrides `AppliesToEntity` to narrow its scope. Use `InstancePerEntity => true` only when it actually stores per-entity data.
7. **Netcode:** set `netUpdate = true` only when state changes, never every tick. Packets carry the minimum: `byte` enums, `WriteFlags` for booleans, no strings.
8. Every projectile has a finite `timeLeft`. Keep boss hostile projectiles at **≤ 100 alive per boss** and `extraUpdates ≤ 2` unless the change report justifies more.
9. World generation uses bounded loops and `WorldGen.genRand`. Tile per-frame hooks are O(1) and allocation-free. Use `ModTileEntity` only for real per-tile state.
10. Cache config objects (`ModContent.GetInstance<T>()`) instead of looking them up repeatedly in hot paths.

Verify: review each touched hot path line by line against 1–10. For new systems that touch many entities, and for every boss, profile a stress scenario with Visual Studio Diagnostic Tools (CPU + .NET Object Allocation) and note the result in the report.

### D2: Co-op compatibility

| Code | Runs on | Guard / owner |
|---|---|---|
| NPC AI decisions, spawning NPCs or hostile projectiles, drops, tile and world changes, downed flags | **Server** (or singleplayer) | `if (Main.netMode != NetmodeID.MultiplayerClient)` |
| `ModSystem.PostUpdateWorld` | Server or singleplayer only | — |
| Player weapons (`Shoot`), held-projectile input, keybinds (`ProcessTriggers`), UI, camera | **Owning client** | `Projectile.owner == Main.myPlayer`, `player.whoAmI == Main.myPlayer` |
| Dust, gore, sound, drawing, `FindFrame` | Clients | `!Main.dedServ`. No gameplay logic here. |

MUST:
1. **Never** use `Main.LocalPlayer` / `Main.myPlayer` in NPC AI, world logic, or tile logic. Use `NPC.TargetClosest()`, `NPC.HasValidTarget`, `Main.player[NPC.target]`.
2. **Synced state:** `NPC.ai[0..3]` and `Projectile.ai[0..2]` are synced automatically. `localAI[]` is **not** synced, so use it only for client-local, visual, or deterministic counters. Never index past `[3]`. Put extra state in `SendExtraAI(BinaryWriter)` / `ReceiveExtraAI(BinaryReader)`, written and read in the same order. Set `netUpdate = true` when state changes.
3. **Gameplay randomness** is rolled on the server (NPCs) or by the owner (player projectiles), stored in synced state, and then synced. Visual randomness can be local.
4. **ModPlayer** fields that other clients can see (auras, visible Pressure effects, set-bonus visuals) need `SyncPlayer` + `CopyClientState` + `SendClientChanges`, plus a `CogpunkPacket` subclass (`Core/Networking`). The server relays it to the other clients with `ignoreClient: sender`.
5. **World flags** go through `Core/Systems/WorldFlagSystem`, which saves by name and syncs on `WorldData`. Register the flag in `Load()`. Boss kills use `NPC.SetEventFlagCleared(ref WorldFlagSystem.Flag(id), -1)` in `OnKill`. For other changes made on the server, call `NetMessage.SendData(MessageID.WorldData)`.
6. **Boss summon items:** in singleplayer use `NPC.SpawnOnPlayer(player.whoAmI, type)`. A multiplayer client sends `NetMessage.SendData(MessageID.SpawnBossUseLicenseStartEvent, number: player.whoAmI, number2: type)`. Set `NPCID.Sets.MPAllowedEnemies[Type] = true`.
7. **Chat:** use `Main.NewText` in singleplayer and `ChatHelper.BroadcastChatMessage(NetworkText.FromKey(key), color)` on the server.
8. **Items:** use `ModifyWeaponDamage` and similar hooks instead of mutating `Item.damage`. Call `Item.NetStateChanged()` after behavior-affecting changes. Custom data goes through `ModItem.NetSend`/`NetReceive`.
9. **Tile entities** are server-owned. Sync them with `MessageID.TileEntitySharing`.
10. **Design bosses for groups:** retarget at the start of every attack, scale health with vanilla scaling plus `ApplyDifficultyAndPlayerScaling(int numPlayers, float balance, float bossAdjustment)`, give per-player loot via `ItemDropRule.BossBag` (Expert and Master only, D3 rule 0), and use `MasterModeDropOnAllPlayers` for pets.

Verify, using the test matrix in SETUP §8.7:
- [ ] **Singleplayer.**
- [ ] **Host & Play + a 2nd client** (`start-tModLoader.bat` → `localhost`).
- [ ] **Dedicated server** (`TerrariaServer` profile + 2 clients) whenever server-side logic changed.

Check that both clients see the same positions, frames, attacks and phases. There should be no duplicate projectiles or drops and no rubber-banding. A player joining mid-fight gets the current state, and a player leaving or dying doesn't break the fight.

### D3: Balance

MUST:
0. **Expert first (user directive, 2026-10-27).** Cogpunk is meant to be played on **Expert**, so every stat and number we define (and every number the user gives) is the **Expert value**: what a player sees in an Expert world. Compare it with the anchor's **Expert** stats (vanilla x2 life and contact damage for normal enemies; bosses per the wiki's Expert column). Classic and Master follow vanilla's ratios (decompiled `GameModeData`: enemy life and damage x1 / x2 / x3), so Classic gets half and Master 1.5x:
   - **NPCs:** call `SetExpertStats(life, damage, defense)` (`Core/Templates/CogpunkNPC`) in `SetDefaults`. It stores half in `SetDefaults` and snaps Expert onto the exact number in `ApplyDifficultyAndPlayerScaling` (`ExpertStats.Base` / `ExpertStats.Snap`). Defense isn't mode-scaled. Bosses with their own player scaling call `ExpertStats.Snap` in their override (see `TrashTr0m`).
   - **Hostile projectiles:** `ExpertStats.HostileProjectile(NPC, expertDamage)` (hostile hits are x2 in every mode, decompiled `Projectile.Damage`; odd numbers land on the next even one).
   - **Player-side numbers** (weapons, armor, accessories) aren't mode-scaled, and modded debuffs aren't in `LongerExpertDebuff`, so the written number is the number.
   - **Boss treasure bags drop only in Expert and Master:** `ItemDropRule.BossBag` (decompiled: `DropBasedOnExpertMode(DropNothing(), ...)`); Classic gets the bag's contents through `LeadingConditionRule(new Conditions.NotExpert())`. Never give a bag another source.
1. Every combat-relevant addition or change (weapon, ammo, armor, accessory, buff or debuff, enemy, boss) updates `docs/balance/*.csv` (schema in SETUP §8.8) **in the same change**. Fill in the target numbers **before** coding.
2. Choose a **vanilla anchor** of the same tier and role (table below) and copy its stats from terraria.wiki.gg.
3. **Weapons:** `eff_dps = damage × (60/use_time) × (1 + crit/100) × shots_per_use` must be within **±15%** of the anchor. Up to **+25%** is allowed only with a written trade-off in `tradeoff_note`, such as ramp-up, self-damage, ammo cost or Overheat risk. Count Mechanist Pressure bonuses at their **average** uptime (measured in playtest; assume 50% until measured).
4. **Armor:** total defense within ±2 of the anchor set, with a set-bonus value comparable to the anchor's.
5. **Enemies and bosses:** set life, defense and damage relative to the anchor's Expert stats (rule 0). Measure time-to-kill (TTK) in **Expert** with 1 player and tier gear (loadouts in `docs/balance/loadouts.md`), then check that Classic and Master stay playable, and test at least 2 players.
6. **Progression gates:** nothing beats the next vanilla gate's power, and recipes only use materials available at that tier.
7. **Hostile projectile damage** can end up scaled twice by game mode, so never pass `NPC.damage` blindly. Use `ExpertStats.HostileProjectile(NPC, expertDamage)` (rule 0) and **measure** the damage taken in Expert.
8. Vanilla stretches debuff durations on players in Expert and Master only for buffs in `BuffID.Sets.LongerExpertDebuff` (vanilla ones; modded buffs are not in it), so a modded debuff's written duration is its Expert duration.
9. **Crit (user rule, 2026-10-23):** every weapon has the vanilla **4% base crit** unless the user asks for another value. Leave `Item.crit = 0` (the player's Generic 4% supplies it; `Item.crit = 4` means 8%). Summon damage skips vanilla's crit roll (`SummonDamageClass.UseStandardCritCalcs` is false), so minions roll `Projectile.CritChance` themselves in `ModifyHitNPC` (`modifiers.SetCrit()`), and the summon item adds the hidden `CritChance` tooltip line back (see `MiceBot`/`MiceBotMinion`).

| Tier | Gate (already beaten) | Example anchors (pick the same class or role) | Boss anchor | Initial TTK target |
|---|---|---|---|---|
| T0 | nothing | Gold/Platinum Broadsword · Wand of Sparking · Finch Staff | King Slime · Eye of Cthulhu | 60–90 s |
| T1 | Eye of Cthulhu | Light's Bane / Blood Butcherer · Musket / The Undertaker · Vilethorn / Crimson Rod | Eater of Worlds / Brain of Cthulhu | 60–120 s |
| T2 | Evil boss | Blade of Grass · Bee's Knees · Space Gun · Hornet Staff | Queen Bee · Skeletron | 90–120 s |
| T3 | Skeletron | Muramasa · Handgun · Water Bolt | Deerclops | 90–150 s |
| T4 | Pre-WoF endgame | Night's Edge · Phoenix Blaster · Imp Staff | Wall of Flesh | 90–150 s |
| T5 | Wall of Flesh | Breaker Blade · Clockwork Assault Rifle · Laser Rifle · Spider Staff | Queen Slime · first mech boss | 120–180 s |
| T6 | Mechanical bosses | Excalibur · Megashark · Optic Staff | Plantera | 120–180 s |
| T7 | Plantera | Terra Blade · Venus Magnum · Pygmy Staff | Golem · Empress of Light | 150–210 s |
| T8 | Golem | Stynger · Razorblade Typhoon · Tempest Staff | Duke Fishron · Lunatic Cultist | 150–240 s |
| T9 | Lunatic Cultist | Daybreak · Vortex Beater · Nebula Arcanum · Stardust Dragon Staff | Moon Lord | 180–300 s |
| T10 | Moon Lord | Meowmere · S.D.M.G. · Last Prism · (ceiling: Zenith) | — (superboss) | 240–360 s |

Anchor names are examples. Always confirm each one's tier and current stats on the wiki. TTK targets are starting values to be tuned in playtests.

**Attack-pattern fairness** (bosses and minibosses):
- Every damaging attack has a visible telegraph, plus an audible one when possible: **≥ 30 ticks** at T0–T4, **≥ 20 ticks** at T5–T8, **≥ 12 ticks** at T9–T10.
- Every attack can be dodged with tier-appropriate mobility. T0–T4 attacks must be dodgeable **without wings**. T5 and up can assume wings.
- No unavoidable or off-screen damage without an on-screen indicator. Turn off contact damage during spawn and phase transitions (`NPC.damage = 0` / `dontTakeDamage`, as in ExampleMod).
- In multiplayer, spread targeted attacks across players, either by cycling targets or by aiming volleys at each nearby player, so co-op adds pressure rather than guaranteed deaths.
- Boss projectiles set `cooldownSlot = ImmunityCooldownID.Bosses`. Bosses despawn when there's no valid target (`NPC.EncourageDespawn`, as in ExampleMod).
- Color-code by allegiance: **hostile** effects use the Ember and Steam ramps, **friendly** effects use Brass and Aether. Players must be able to read the screen in a 4-player fight.

### D4: Pixel art

MUST:
1. Draw at **1×** and export **200% nearest-neighbor**. Every 2×2 block must be uniform, and dimensions must be even. Never enlarge with `Item.scale` / `NPC.scale` (it creates mixels).
2. Use only colors from `art/palettes/cogpunk.gpl`. A new color counts as a palette change, which must be justified and listed in the report.
3. Light comes from the **top-left**. Use 3–5 shades per material ramp. The outline is ramp index 0 (the darkest shade of that material). Selective lighter outlining on the lit side is allowed, but no pure-black outlines.
4. Banned: pillow shading, banding, gradients, filters, soft brushes, blur, orphan pixels, and jaggy lines (keep line steps consistent).
5. Color caps per sprite: **items ≤ 16, enemies ≤ 32, bosses ≤ 48**.
6. **Terrain sheets** are generated from `art/templates/terrain_exposure.json`, which records which sides of each of the 240 standard frames are exposed (see `tile_frame()` in `art/scrap/make_scrap_art.py`). Never copy vanilla or template pixels.
7. **Seamless blocks (the clump look of vanilla ores and stone).** Tiles of the same block must merge into one clump with no visible grid:
   - No per-tile bevel, seam or border. Outlines only appear on exposed sides, which is the clump's perimeter, and the exposure table already handles that.
   - Details (cogs, rivets, plates) sit at least 1 px inside the tile.
   - Tile edges are plain background texture with the same brightness as the interior, so every variant can sit next to every other.
   - Rim shading on exposed edges stays in the block's own ramp.
   - `python -P tools/check_tile_seams.py <sheet>` must pass (seam ratio ≤ 1.25, edge bias ≤ 0.06). Then preview a mass with `tools/sim/terrain.py`.
   - Applies to every block sheet. Rusted Scrap went from seam ratio 3.25 to 0.71 under this rule.
8. Follow the sheet specs and orientation rules in SETUP §8.4: vertical sheets with equal frames and 2 px padding; tiles on an 18 px stride; walls on a 36 px stride; armor Head/Legs 40×1120 and Body 360×224; NPCs face left; arrows point up; swords and staffs point top-right; guns point right.
9. **No semi-transparent pixels.** Glows go in a `_Glow` texture with additive drawing. Fades happen in code.
10. **Animation:** time frames in game ticks (60 per second), keep volume consistent (no popping), use smears for swings, add anticipation frames before telegraphed attacks, and give small mobs 2–4-frame idle loops.
11. Readability: the silhouette must read at 100% zoom on both dark (cavern) and light (sky) backgrounds.
12. Commit the source (`.aseprite`, or the generator script under `art/`) at `art/<same path as Content>/` and the 2× PNG next to its `.cs`. AI-generated art (SpriteCook and similar) is **concept only** and must be redrawn or cleaned up.

**Art direction for detailed entities (user rule, 2026-10-26).** Applies to bosses, minibosses, detailed mobs and the weapons the user names. Full write-up: `docs/design/art-direction.md`.

13. **Three-quarter view.** Bodies are drawn side-facing and turned towards the viewer (facing left, D4 rule 8): front and near side both visible, top faces lit. Only bosses that are flying heads (Skeletron-like) may face the camera.
14. **Multiplane layers.** Split the sprite into up to **three** layers (far / middle / near, e.g. far arm, torso, near arm). Each layer animates on its own and is drawn with `Core/Visuals/DepthLayers`: one SpriteBatch pass, a parallax shift of at most a few px snapped to the 2 px grid (vanilla's background formula, decompiled `Main.DrawSurfaceBG`), and the far layer baked one ramp step darker. Never rotate or scale these sprites at runtime: render every pose from a generator (rigged parts and two-bone IK, see `art/bosses/trashtr0m/rig.py`), so each frame stays clean pixel art. (One user-made exception, 2026-10-29: Tar Tyrant shrinks 1% per 2% of its life, like vanilla's King Slime, so its layers are drawn at that scale with the game's point sampling and the top-left snapped to whole pixels; its hit strips, AI points and the vent overlay on its back scale with it.) The generator writes the rig data (cell sizes, origins, contact and emitter points) to a `*RigData.cs` file that the AI and drawing read, so art and code can't drift apart. **Weathering must not flicker (user, 2026-10-28):** rust, grime and decals live in each part's own space. Place a moving part by its transform (`Xf.pose(0, (0, 0), joint)` for a part that rides a joint), never by baking the pose into its shape's coordinates; give a part that stretches with the pose a fixed `seed=`; pass the part's transform to `grime(..., xf=...)`. Check it by rendering consecutive frames side by side (Trash-Tr0m's rust swam and re-rolled every frame before this).
15. **Every boss gets a themed death cinematic** that locks the camera like its intro: inherit `Core/Templates/BossNPC` (dying state, death length, finishing strike on the server) and request the camera through `Core/Visuals/CinematicCamera`.
16. **Metal Slug-level detail**: chunky ramp-0 outlines, dense mechanical detail (rivets, plates, hoses, pistons, hazard stripes, weld beads), strong 1 px edge highlights, cast shadows between parts, little or no grime noise on large plates. Big plain areas get panel seams, a part or a decal.

17. **Stable pixels: no colour flicker between frames (user, 2026-10-29; Trash-Tr0m's rust and Tar Tyrant's shading both "changed colour" between frames).** A generator must not let a part's colours crawl over it as it moves:
   - Light each part in its own space: `fixed=True` on `rig.py`'s `face`/`dome`/`cyl` for parts that only wobble (bodies, skulls, plates, rigid bones), `snap=45` for limbs and spin frames (the light follows big turns in 45-degree steps, never small ones). A mass built as a union of posed shapes is shaded with a dome evaluated in its own space (`space_dome` in `art/bosses/tartyrant/make_tartyrant_art.py`), never in rig space.
   - Subtle loops (idle, walk, breathing) move parts by **whole pixels** only (integer offsets); fractional scales and small rotations are for big, deliberate moves, and a lean that turns a whole mass is replaced by an offset where it can be.
   - Highlights, gloss, rust and decals live in the part's space; nothing is derived from the per-frame silhouette.
   - A shake alternates 0 and 1 px, not -1 and +1 (a 2 px jump reads as flicker).
   - Finish each canvas with a despeckle (no lone pixels) and, optionally, a selective outline on the lit side.
   - Check it: `python -P tools/check_flicker.py <RigData.cs> <layer base> --report <deforming sequences>` must exit 0: loops under 0.5% flashing pixels per frame triple, other sequences under 1.5%; melts, rises and death slumps that deform the whole sprite are reported, not judged. It measures plane by plane (occlusion is not flicker) and tells motion from flicker (a colour that moved a pixel is motion).

Verify: `python -P tools/check_sprite.py <png...> --palette art/palettes/cogpunk.gpl --max-colors <cap>` must exit 0, and for generated animations `tools/check_flicker.py` (rule 17). Then check a 2× preview over dark and light backgrounds. For animated sprites, also make the D5 GIF.

### D5: Visual proof (GIF)

**Applies to** any feature or fix with a visible result.
- **A GIF is mandatory when anything moves:** animated sprites, projectiles, held-weapon motion, AI and attack patterns, boss phases, tile animations, dust or particle effects, UI animation.
- Static visuals need a PNG image instead.
- Purely non-visual changes (numbers, netcode) should say "no visual component" and give the test evidence.

**In-game capture is not required.** Build the proof from the animation frames or from the most efficient simulation that shows the behavior.

MUST:
1. **Pick the cheapest method that shows the behavior:**
   - **Animated sprites** (items, projectiles, NPCs, tiles, glows): `python -P tools/sheet2gif.py <sheet> --frames N --ticks T --contact <tmp.png>`, using the same frame count and ticks-per-frame as the code.
   - **Motion and behavior** (projectile paths, attack patterns, boss phases, telegraphs, dust bursts): an offline simulation, for example a Python/Pillow script that composites the real sprites over a plain or biome-colored background. It replays the AI's timing and math tick by tick (60 ticks = 1 s), using the same constants as the C# code.
   - **Blocks:** `tools/sim/terrain.py` assembles real tile frames with Terraria's framing (from `art/templates/terrain_exposure.json`). Use it to show a new block in context.
   - **Static visuals:** a PNG of the sprite at 2× zoom over dark and light backgrounds. Compose several related sprites into one sheet when that's clearer.
   - In-game capture (`tools/record-gif.ps1`, ScreenToGif) is optional. Use it only when a simulation can't represent the behavior faithfully.
2. **Deliver it:** show the GIF or PNG in the response (send it to the user as a file) **and/or** save it to `docs/media/YYYY-MM-DD_<area>-<feature>[-fix].gif|png` (Git LFS for GIFs). Mention the path or attachment in the report.
3. **Specs:** ≤ 10 s, ≤ 10 MB, nearest-neighbor scaling only, looping forever. Use ticks-per-frame values that are multiples of 3 (or 25/50 fps) so timing is exact. For fixes, show the fixed behavior. A `…-before` image is optional.
4. **Faithful:** simulations reuse the real textures and the real constants (speeds, timers, frame counts, telegraph durations). Say in the report that it's a simulation and what it leaves out, such as lighting, tile collision or netcode.
5. **Self-review:** open the contact sheet or PNG with the Read tool and confirm it shows the claimed behavior before reporting.
6. **Clear outdated proofs (user, 2026-10-28: project size).** When a fix or update changes a model, sprite or animation, delete every `docs/media` GIF/PNG that shows the old version (whatever its date), fix any doc that links to one, and regenerate only the proofs the change needs (the sims under `tools/sim/` re-render from the real sheets). Proofs of things the change didn't touch stay. List what was deleted in the report.

Simulation scripts are throwaway unless reusable. Reusable ones go in `tools/sim/`.

---

## 2. Workflow for every task

1. **Classify** the task: content type, tier (T0–T10), archetype (Gunsmith / Brawler / Tinker / vanilla class), and which directives apply.
2. **Context:** read the README scope and the existing code in the area. Check terraria.wiki.gg for **vanilla name collisions**: vanilla already has *Cog*, *Steampunk Boiler*, *Tinkerer's Workshop*, *Steampunk* armor and wings, and *Clockwork Assault Rifle*.
3. **API lookup:** open the matching ExampleMod 1.4.4 file (§2.1).
4. **Balance first (D3):** pick the anchor and write the target row in the CSV.
5. **Implement** with the patterns in §3. Add localization for en-US and pt-BR. No hard-coded player-facing strings.
6. **Art (D4):** draw in `.aseprite`, export, then run `check_sprite.py`.
7. **Build:** `dotnet build` must give **0 errors and 0 new warnings**. Then *Build + Reload*.
8. **Test:** the D2 matrix, plus D3 measurements (DPS Meter, Target Dummy, `CogBal-*` worlds).
9. **Visual proof (D5).**
10. **Report** using the §6 template.

### 2.1 ExampleMod reference map (branch `1.4.4`, paths verified)

| Need | File |
|---|---|
| Mechanist damage class | `Content/DamageClasses/ExampleDamageClass.cs` |
| Steam Pressure resource + bar | `Common/Players/ExampleResourcePlayer.cs`, `Common/UI/ExampleResourceUI/` |
| Vent hotkey | `Common/Systems/KeybindSystem.cs`, `Common/Players/ExampleKeybindPlayer.cs` |
| Armor and set bonus | `Content/Items/Armor/`, `Common/Players/ExampleArmorSetBonusPlayer.cs` |
| Boss: phases, minions, loot, netcode, despawn | `Content/NPCs/MinionBoss/MinionBossBody.cs` |
| Boss summon item / treasure bag | `Content/Items/Consumables/MinionBossSummonItem.cs`, `MinionBossBag.cs` |
| Worm enemy | `Content/NPCs/ExampleWorm.cs`, `Content/NPCs/Worm.cs` |
| Downed flags + sync | `Common/Systems/DownedBossSystem.cs` |
| Boss Checklist / cross-mod | `Common/Systems/ModIntegrationsSystem.cs` |
| Packets | `ExampleMod.Networking.cs` |
| Biomes, backgrounds, water | `Content/Biomes/`, `Common/Systems/ExampleBiomeTileCount.cs` |
| Ore + world-gen pass | `Content/Tiles/ExampleOre.cs` (`ExampleOreSystem`, `ExampleOrePass`) |
| Animated tile / glowmask tile | `Content/Tiles/ExampleAnimatedTile.cs`, `ExampleAnimatedGlowmaskTile.cs` |
| Animated item | `Content/Items/ExampleSoul.cs` |
| Held / swing / homing / animated projectiles | `Content/Projectiles/ExampleHeldProjectileWeaponProjectile.cs`, `ExampleCustomSwingProjectile.cs`, `ExampleHomingProjectile.cs`, `ExampleAdvancedAnimatedProjectile.cs` |
| Sentries (Tinker) / minions | `Content/Projectiles/Minions/ExampleSentry.cs`, `ExampleSimpleMinion.cs` |

---

## 3. Implementation patterns

### 3.0 Architecture (decided 2026-10-20)

The structure was chosen after comparing Calamity (type-based, 60+ top-level folders), Starlight River (`Core/` + type-based `Content/`) and Spirit Reforged (feature-based `Content/<Feature>/`):

- **`Core/`** is the engine, with no player-facing content. It contains `Networking/` (`CogpunkPacket`, `PacketRegistry`), `Safety/` (`SafeSpawn`, `SafeLog`, `TileSafety`, `MathSafety`, `SpawnBudgetSystem`), `Templates/` (abstract bases, `StateMachineNPC`, `BossNPC`, `GridWalkerNPC`, `TextureFallback`), `Systems/` (`WorldFlagSystem`, `CrossMod`, `NPCHaste`), `Events/` (`CogpunkInvasion` and its director, spawn rules, progress bar; see §3.9), `WorldGeneration/` (`SafeGenPass`, `GenPassUtils`), `Visuals/` (`AnimatedEquip`, `DepthLayers`, `CinematicCamera`), `UI/` (`BiomeTitleSystem`, `BossTitleSystem`), `Hooks/` (`SceneOverlayRegistry`: the one reflection touch, see §3.8) and `Configs/`. When a new cross-cutting mechanic is needed (UI framework, particles, primitives), add `Core/<Area>/`.
- **`Content/<Slice>/`** holds one folder per cohesive piece of content: a biome (`Content/Foundry/`), a boss (`Content/Bosses/Boilerheart/`), the class (`Content/Mechanist/`), a shared material set (`Content/Materials/`). Inside a slice, use type subfolders as needed: `Items/`, `Tiles/`, `Walls/`, `NPCs/`, `Projectiles/`, `Buffs/`, `Biome/`, `WorldGen/`, `Gores/`, plus the slice's own `ModSystem`/`ModPlayer` at its root. A slice must not depend on another slice's internals. Shared code moves to `Core/`.
- **`Assets/`** holds only shared assets (placeholder, shared effects, sounds, music). A content texture sits next to its `.cs`.
- A tiny boilerplate companion class may share a file with its main class (a placed tile and its item). Two or more companions means split the file.

### 3.1 Files, namespaces, assets
- Class name = file name = texture name, and the namespace mirrors the folder (`Cogpunk.Content.Items.Weapons.Mechanist`). If they don't match, you get a missing-texture exception.
- Equip textures need `[AutoloadEquip(EquipType.Head)]` with a `_Head` texture (and likewise `_Body`/`_Legs`). Gores go in any `Gores/` folder.
- **Armor that leaves skin bare, and capes** (the Tyrant set, 2026-10-30; decompiled `PlayerDrawLayers` / `PlayerDrawSet`): vanilla draws the wearer's torso, arm and leg skin under armor (`ArmorIDs.Body.Sets.HidesTopSkin` / `Legs.Sets.HidesBottomSkin` default false) and never the shirt or pants, so transparent armor pixels show skin; hands are hidden for modded bodies unless `ArmorIDs.Body.Sets.HidesHands[Item.bodySlot] = false` (ExampleMod 1.4.4's ExampleRobe). A female wearer's torso and shoulders come from rows 2-3 of the body sheet (`CreateCompositeData`: Y += 2 when not Male): a bra goes there, no extra texture. A real cape is a back equip: `EquipLoader.AddEquipTexture(Mod, path, EquipType.Back, name: ...)` in `Load()` (clients only, a fixed path checked with `ModContent.HasAsset`), then `ArmorIDs.Body.Sets.IncludedCapeBack` and `IncludedCapeBackFemale` set to its slot in `SetStaticDefaults`; it is a 20-frame 40x56 strip drawn with the body frame behind everything (`DrawPlayer_10_BackAcc`, centred on the torso), so it carries the walk bob in its frames and animates per player frame. Preview: `tools/sim/armor_preview.py --back <cape> --skin --female`.
- Sounds: `new SoundStyle("Cogpunk/Assets/Sounds/Weapons/SteamVent")` with `.ogg`/`.wav`. Music: `MusicLoader.GetMusicSlot(Mod, "Assets/Music/<Name>")`.
- Never rename a released class without `[LegacyName("OldName")]`.

### 3.2 Mechanist class & Steam (built 2026-10-27, `Content/Mechanist/`)
- **Steam works like mana (user-set 2026-10-27), not the pressure-builds-up idea of the first README.** `MechanistDamage : DamageClass` inherits Generic in full (so its base crit is Generic's 4%) and nothing else. Items set `Item.DamageType = ModContent.GetInstance<MechanistDamage>();`; bonuses use `player.GetCritChance<MechanistDamage>() += 6;` etc.
- `SteamPlayer : ModPlayer` (owner-only state, like the local mana counter): `Steam`, `SteamMax` (= `BaseSteamMax` **0** + `SteamMaxBonus`: only gear grants a tank, user-set 2026-10-27), `SteamRegen` (10), `SteamCostMultiplier` (1). Gear adds to the bonus fields every tick (they reset in `ResetEffects`). The refill waits `RegenDelayTicks` (1.5 s) after the last Mechanist attack, then adds `SteamRegen` every `RegenIntervalTicks` (0.5 s).
- **Steam as mana** (the Serene Tear, Tar Tyrant's Expert item, 2026-10-29): `SteamPlayer.SteamAsMana` zeroes a mana cost the tank covers in `ModifyManaCost` (the true cost measured with the hook switched off) and takes the steam in `OnConsumeMana` (vanilla calls it with 0, decompiled `Player.CheckMana`); `OverheatImmune` makes `TriggerOverheat` a plain refusal; `SteamRegenMultiplier` scales each refill with the fraction carried over.
- **Steam containers** (`Content/Mechanist/Accessories/`) inherit `SteamContainer`: an accessory that adds `SteamCapacity`, one container worn at a time (`CanAccessoryBeEquippedWith`). Glass Container (+10, 10% of plain Wooden Chests via `GlassContainerPass`), Brass Container (+15, +4% mechanist damage; crafted at the Rust Polisher). World-gen chest loot uses `Core/WorldGeneration/WoodenChests.IsPlain`.
- **Every Mechanist weapon inherits `MechanistWeapon`**, sets `SteamCost`, and overrides `CanUseMechanist` (never `CanUseItem`, which is sealed). It pays in `UseItem` (once per use, decompiled `Player.ApplyItemTime`) and adds the "Uses N steam" tooltip line. Using one without enough steam **overheats** the player (`Overheat` buff mirrors `SteamPlayer.Overheated`): `noItems`, forced movement in `SteamPlayer.SetControls`, until the tank is full. A weapon that costs more than the whole tank (no gear) can't be used and doesn't overheat (`SteamPlayer.NoteNoTank`: a click and a "No steam tank!" hint, at most once a second; a red tooltip line).
- The gauge (`SteamGaugeSystem`, client-only) draws left of the hearts (`Main.screenWidth - 300`), hover shows the numbers; it only shows while steam matters (Mechanist weapon held, Mechanist gear, a tank that isn't full, an overheat).
- A *Vent* keybind, if added later, is a `ModKeybind` handled in `ProcessTriggers` (owner only), and its world effect is an **owner-spawned projectile**, not a direct NPC hit.
- **Permanent steam and the steam dash** (2026-10-28): the `CogpunkerManual` (Jaeger drop, once per character, saved by `SteamDashPlayer` as `CogpunkerManual`) adds +20 through `SteamPlayer.SteamMaxInnate` (re-added every tick in `PostUpdateEquips`; it alone doesn't keep the gauge up) and teaches the dash: `SteamDashSystem.Keybind` (default F) or a vanilla-style double tap when no other dash is equipped; 15 steam through `SteamPlayer.TrySpendFlat` (no weapon discount), 4 s cooldown; `CanBeHitByProjectile` false for the dash + 6 ticks (hostile projectiles are checked on the hit player's client, so it needs no sync); a contact hit ends the dash (`OnHitByNPC`) so the knockback lands. Looks: `armorEffectDrawShadowEOCShield` in `FrameEffects` (vanilla resets it in `PlayerFrame` just before), steam dust; a `SteamDashPacket` tells other clients to replay them.

### 3.3 Weapons & projectiles
- Player projectiles are created in `Shoot` / `UseItem` on the owner. Any later client-side change goes through `if (Projectile.owner == Main.myPlayer) { …; Projectile.netUpdate = true; }`.
- Animated held weapons use `Item.noUseGraphic = true` + `Item.channel = true` + a held projectile with `Main.projFrames[Type] = n`.
- Projectile frames: `if (++Projectile.frameCounter >= T) { Projectile.frameCounter = 0; Projectile.frame = (Projectile.frame + 1) % Main.projFrames[Type]; }`
- **Trinkets and accessories:** every pre-Hardmode one that isn't a boss drop sets `CogpunkSets.ScrappyTrunkTrinket[Type] = true;` in `SetStaticDefaults`, so the Scrappy Trunks that replace 20% of Wooden Chests can hold it (`Content/Furniture/ScrappyTrunkLoot`). Exception: an accessory with its own user-set chest rate (the Glass Container, 10% of Wooden Chests) stays out of the set, or every trunk would hold one while the set is small.
- **Mechanical enemies:** Cogpunk robots and machines set `CogpunkSets.Mechanical[Type] = true;` (the Screwdriver's +50%).

### 3.4 NPC / boss AI state machine (template)

Bosses and complex enemies inherit `Core/Templates/StateMachineNPC`. It owns `ai[0]` (state) and `ai[1]` (timer), seals `AI()`, and recovers from NaN. `ChangeState` is ignored on multiplayer clients and syncs only on change.

```csharp
public class Boilerheart : StateMachineNPC
{
    private enum Phase { Spawn, RivetVolley, VentDash, Overheat }

    private ref float Counter => ref NPC.ai[2];   // ai[2], ai[3] are free; localAI[] is NOT synced

    protected override void UpdateState() {        // runs every tick on every side; allocation-free
        if (!NPC.HasValidTarget) NPC.TargetClosest();
        if (!NPC.HasValidTarget) { NPC.EncourageDespawn(10); return; }

        switch ((Phase)State) {
            case Phase.Spawn:       DoSpawn();       break;
            case Phase.RivetVolley: DoRivetVolley(); break;
            case Phase.VentDash:    DoVentDash();    break;
            case Phase.Overheat:    DoOverheat();    break;
        }
    }

    // Only the server picks the next attack; clients follow the synced ai[].
    private void PickNextAttack() {
        if (!IsAuthority) return;
        NPC.TargetClosest();                         // retarget every attack (co-op)
        ChangeState(Main.rand.Next((int)Phase.RivetVolley, (int)Phase.Overheat)); // max > min (D0)
    }

    private void FireRivet(Vector2 velocity) {
        if (!IsAuthority) return;
        int damage = ExpertStats.HostileProjectile(NPC, RivetDamage);   // D3 rules 0 and 7: the Expert number
        SafeSpawn.TryNewProjectile(NPC.GetSource_FromAI(), NPC.Center, velocity,
            ModContent.ProjectileType<RivetBolt>(), damage, 0f, out _);   // D0: never overwrites
    }
}
```

- Telegraphs are drawn in `PreDraw`/`PostDraw`, or with dust inside `!Main.dedServ`. Their **timing** comes from synced `Timer` / `State`.
- Boss setup: `NPC.boss = true`, `NPC.BossBar`, `Music`, `NPCID.Sets.MPAllowedEnemies[Type] = true`, `NPCID.Sets.BossBestiaryPriority.Add(Type)`, and debuff immunities through `NPCID.Sets.SpecificDebuffImmunity`.
- Loot goes in `ModifyNPCLoot` only: `LeadingConditionRule(new Conditions.NotExpert())` for Classic drops, `ItemDropRule.BossBag` (the bag drops **only in Expert and Master**, D3 rule 0), `MasterModeCommonDrop` (relic), `MasterModeDropOnAllPlayers` (pet). Everything else goes in `OnKill`.
- Animate in `FindFrame(int frameHeight)` with `Main.npcFrameCount[Type] = n` set in `SetStaticDefaults`. Keep it purely visual.
- **Bosses inherit `Core/Templates/BossNPC`** (2026-10-26), a `StateMachineNPC` with a scripted death. Put the per-tick logic in `UpdateBoss()`; `UpdateState` is sealed so every boss reports itself for the spawn rule below. `CheckDead` refuses the killing blow, puts life back to 1 and switches to `DyingState`; `UpdateDeath()` (call it every tick while dying) keeps it untouchable and, after `DeathAnimationTicks`, finishes it on the server with `NPC.StrikeInstantKill` + SyncNPC, which runs the loot and `OnKill`. Clients accept the finishing strike within `FinishGrace` ticks of the end.
- **Boss-fight rules (user, 2026-10-26), for every boss:**
  - The **defeat card** shows only the boss's name and "Defeated" (`BossTitleSystem.ShowDefeated`). `BossNPC.UpdateDeath` shows it at `DefeatCardTick` for players within 150 tiles; never add an epithet or flavour line to it.
  - **No natural spawns during a boss fight**: `Core/Systems/BossFightSpawnRule` sets `maxSpawns = 0` (decompiled `NPC.SpawnNPC`: `nearbyActiveNPCs < maxSpawns`) for players within `BossNPC.SpawnBlockRange` (300 tiles) of a living `BossNPC`. Minions a boss spawns itself are not natural spawns and still appear.
  - A **biome boss despawns** with its leaving animation (burrow, fly off...) when no living player has been in its biome for a short grace (Trash-Tr0m: Junkyard, 60 ticks). Check it on the server on an interval, not every tick.
  - **Hitboxes match the art**: the art generator exports silhouette strips per frame (`*Hit` in `*RigData.cs`); contact damage returns the touched strip from `ModifyCollisionData`, and melee (`CanCollideWithPlayerMeleeAttack`) and projectiles (`CanBeHitByProjectile`, only when the projectile's own rectangle overlaps the NPC rectangle) hit only the strips. Attack projectiles get their hitbox measured from their sprite (`TrashTr0m.Hitboxes.cs`, `docs/media/2026-10-28_boss-trashtr0m-hitboxes.png`).
- **Camera locks** (intros and deaths) go through `Core/Visuals/CinematicCamera.Request(focus, strength)` every update on clients, with `CinematicCamera.Envelope(tick, length, easeIn, easeOut)` for the ease. The strongest request of the update wins; no request releases the camera.
- **Layered bosses** draw their far, middle and near layers with `DepthLayers.DrawFrame` (packed atlas pages: every frame cropped to its own pixels and shelf-packed by the generator into pages of at most 2048x2048, with a per-frame rectangle and rig origin; ground-line clip, emergence `buried` clip) from tables in a generated `*RigData.cs`. Grid sheets (`DrawCell`) waste the union of all poses in every cell and ran out of room at 20 body frames; the packed atlas fits more frames in less texture memory. AI points (mouth, hands) come from the same tables through a pose function that depends only on synced state (`TrashTr0m.ResolvePose`), so the server and every client agree.
- **Bosses summoned by fishing** (Tar Tyrant, 2026-10-28: a Scrapworm in the Junkyard's tar, like the Truffle Worm and Duke Fishron): vanilla hard-codes the Truffle Worm, so a modded bait uses `ModPlayer.CatchFish` (runs on the bobber owner's client after vanilla's roll): set `npcSpawn` to the boss (and `itemDrop` to 0) only where the summon is allowed and none is alive, else nothing bites (it must never be a super bait); `CanConsumeBait` returns true for it. Vanilla then pulls the NPC out at the bobber (`NPC.NewNPC` in singleplayer, message 130 to the server), so the boss announces itself ("has awoken") and scales life in `OnSpawn` (server/singleplayer) and rises from that spot.
- **Bosses on liquid**: a boss that glides on a pool treats a tile holding more than a quarter of liquid as a surface in its ground search (`TarTyrant.FindSurface`), so it rides the tar instead of sinking to the bottom; still bounded and through `TileSafety`.
- **Focus on the top damage dealer** (Tar Tyrant, 2026-10-29): the server credits each hit in `HitEffect` to `NPC.lastInteraction` (vanilla sets it to the attacker just before the strike: decompiled `MessageBuffer` case 28, and `NPC.StrikeNPC` in singleplayer), decays the totals on an interval and retargets the top one at every attack, else the closest player. The per-player array is allocated in `SetDefaults` (a `ModNPC` clone shares reference fields with its template).
- **Destroyable boss projectiles are NPCs** (Tar Tyrant's bubbles, like vanilla's Detonating Bubble): a small `CogpunkNPC` with no loot, `CheckActive` false, its own capped count; what it turns into (Living Tar from a burst) is spawned by the server and flagged so it drops nothing (`LivingTar.FromBoss` + `PreKill`).
- **Telegraphs on their own clock** (Trash-Tr0m's cogs, Tar Tyrant's flung bones, 2026-10-29): an automatic volley keeps its own timer through every attack, so its telegraph can't be baked into the body's frames. Every side counts the timer (reset in the phases where it pauses) and the server sends its count in `SendExtraAI`; the telegraph is an overlay sheet (`TarTyrant_Vent.png`: swell frames, then burst frames) drawn at a per-frame rig point the generator writes (`R.Vent`), mirrored and scaled with the body, with the sound and dust keyed to the same count.
- **Animations tweened from key poses** (Tar Tyrant's generator, 2026-10-29): a `Pose` of numbers and points, `tween(a, b, t)` with easing, every sequence built from key poses so no move snaps; tar squashes through one transform while bones are placed rigidly at points of it (`place`), so they stick out of the tar as it slumps.
- **Bosses that move a player** (suction, grabs, launches) never change the player on the server: every side runs the same math from the synced boss state in a `ModPlayer`, and only the owner's result counts (see `TrashTr0mPlayer`). Pulls are a *conveyor*: add the pull to the velocity in `PreUpdateMovement` and take it off again in `PostUpdate`, scaled by how much of it collision let through, so it subtracts from run speed instead of building up. Vanilla only resets `fallStart` on the ground or while jumping, so a launch must track the apex itself and cap the fall if the damage is meant to be bounded.
- **Boss intros** (first used by Trash-Tr0m, 2026-10-23): an `Emerge` state whose synced timer drives everything on each client: the sprite drawn clipped at a ground line in `PreDraw` (even pixel steps), `BossTitleSystem.Show(DisplayName, epithet, hold)` once per client (a `localAI` flag), a camera lock through `CinematicCamera` for players within range, `PunchCameraModifier` shakes behind the `ScreenShake` config, `dontTakeDamage` and no contact damage until it ends. One-shot intro sounds remember the last tick played (`localAI`) so a timer resync never repeats them. A boss summoned by world interaction (a locked chest) or by an item with a custom spawn point sends a `CogpunkPacket` that the server validates and answers with `SafeSpawn.TryNewNPC(..., critical: true)`. A boss that bursts out of terrain clears only its own natural tiles, directly (`Tile.ClearTile`, no drops or per-tile dust), in a few bands over several ticks, each band reframed and sent as one tile square (`TrashTr0mSummon.ClearHeapRows`).

### 3.5 Biomes, tiles, world generation
- `ModBiome`: `IsBiomeActive` reads a tile count gathered in `ModSystem.TileCountsAvailable(ReadOnlySpan<int> tileCounts)`. Also set `Music`, backgrounds, `WaterStyle`, and the bestiary icon (`_Icon`).
- Spawns: `SpawnChance(NPCSpawnInfo info) => info.Player.InModBiome<FoundryBiome>() ? 0.25f : 0f;` (tune it in D3).
- World generation: `ModifyWorldGenTasks(List<GenPass> tasks, ref double totalWeight)`. Find the vanilla pass by name (for example `"Shinies"`), insert a `GenPass` after it, and use only `WorldGen.genRand`. Set `progress.Message` from localization.
- Animated tiles use `AnimationFrameHeight` + `AnimateTile(ref int frame, ref int frameCounter)`, kept O(1).
- **Replacing a vanilla region** (the Junkyard replaces the left beach/ocean): insert one late `SafeGenPass` after "Micro Biomes" (Calamity's Sulphurous Sea uses the same slot), rebuild the whole strip (`GenVars.leftBeachEnd` = 300–380 tiles on every world size), unregister `Main.chest`/`Main.sign` entries inside it first. **Keep vanilla's big structures out instead of shrinking around them** (2026-10-22): right after "Reset" mirror a left Dungeon to the right (`JunkyardLayoutPass`: every side-dependent pick is made in Reset, mirroring uses no RNG), right after "Terrain" claim the footprint with `GenVars.structures.AddProtectedStructure` so every `CanPlace`-aware structure stays out (`JunkyardReservePass`), and swap the vanilla "Shimmer" pass for a capped wrapper that places it past the footprint and falls back to vanilla (`ShimmerPlacementPass`, via `GenPassUtils.Replace`); `ShimmerMakeBiome` and the Dungeon never ask the structure map. After reserving, `CanPlace` always fails inside your own area, so the region's last safety net scans tiles (dungeon/temple brick and walls, Shimmer liquid) instead. No custom liquids in 1.4.4 (no ModLiquid; liquid arrays are sized `LiquidID.Count` = 4). **A biome liquid is vanilla water restyled the Calamity way** (2026-10-23, Sulphurous Sea pattern): `ModBiome.WaterStyle` returns a `ModWaterStyle` (client-only; textures: water 48x1360 = 16 frames of 80 px + the calm surface strip at y 1280, `_Block` 306x16, `_Slope` 72x16; waterfall 512x40; droplet gore 18x300; from `art/junkyard/make_tar_art.py`), and a `ModPlayer` applies the liquid's effect while `Player.wet` inside the biome (see `Content/Junkyard/Tar/`). Vanilla draws water opaque in a background pass and at 60% in front of entities, so keep the texture opaque. Only for something that must not behave like water, fall back to non-solid tiles drawn by a vanilla `Overlay` at `RenderLayers.Entities` (register/unregister through `Core/Hooks/SceneOverlayRegistry`). Store the region as rectangles in a `ModSystem` (saved by name, sent in `NetSend`) and test them in `IsBiomeActive`: O(1), no tile counting.
- **Biome intro title:** `BiomeTitleSystem.Show(DisplayName)` from `ModBiome.OnEnter`, guarded by `player.whoAmI == Main.myPlayer` (client-local UI, nothing synced).
- **Spawn pools:** a biome that hosts only Cogpunk creatures removes entry 0 (vanilla's own choice) in `GlobalNPC.EditSpawnPool`, tested on the spawn tile, keeping invasions and pillar zones (`JunkyardSpawnRules`).

### 3.6 Animations: quick API
| Object | API |
|---|---|
| Item (inventory and world) | `Main.RegisterItemAnimation(Type, new DrawAnimationVertical(ticksPerFrame, frames));` + `ItemID.Sets.AnimatesAsSoul[Type] = true;` |
| Projectile | `Main.projFrames[Type] = n;` + `frameCounter` in `AI` |
| NPC | `Main.npcFrameCount[Type] = n;` + `FindFrame` |
| Tile | `AnimationFrameHeight`, `AnimateTile`, `AnimateIndividualTile` |
| Glow | `_Glow` texture drawn in `PostDraw` with full brightness or additive blend |
| Layered boss (multiplane rig) | Generator under `art/` renders each layer's poses, packs them into atlas pages (`Name.png`, `Name_Page1.png`...) and writes `*RigData.cs`; `PreDraw` returns false and calls `DepthLayers.DrawFrame` far -> middle (+ `_Glow`) -> near with `DepthLayers.Shift` parallax. **No pose snaps (user, 2026-10-26):** every attack reaches its key poses through in-betweens (lift, rise, cock back, a strike/smear frame, settle, lower; jaw and spit wind-ups and follow-throughs; death tweens), chosen in the pose function from the synced timer. Root motion: move the NPC only on frame changes where a planted part drags, by exactly the art's step (`TrashTr0m.DoCrawl`; the sim checks 0 px hand slip). |
| Small layered enemy (grid planes) | Three vertical grid sheets of equal cells (`Name_Far`, `Name` = the NPC texture, `Name_Near`, optional `Name_Glow`) from a generator that also writes the cell sizes and origins to a `*RigData.cs`; inherit `Core/Templates/GridWalkerNPC` (moved out of the Mech Army 2026-10-28; `MechWalker` adds the machines' haste and immunities) or call `DepthLayers.DrawWalker` (horizontal parallax only, so feet stay planted). |
| Armor (worn) | `AnimatedEquip.Register(this, EquipType.X, frames, ticks)` in the item's `Load()`, plus `<Name>_<Type>_<n>.png` copies of the equip sheet (n = 1..frames-1). Frame 0 stays the `[AutoloadEquip]` texture. Swapped in `FrameEffects`; shows frame 0 while paused. Preview: `tools/sim/armor_preview.py`; armor layout shapes: `art/templates/armor_layout.json`. |

### 3.7 Localization & cross-mod
- tModLoader keeps adding keys to `Localization/en-US_Mods.Cogpunk.hjson`. Mirror every new key into `pt-BR_Mods.Cogpunk.hjson` in the same change.
- Cross-mod integration goes only through `ModLoader.TryGetMod("BossChecklist", out Mod bc)` + `bc.Call(...)` in `PostSetupContent` (ExampleMod `ModIntegrationsSystem`). No hard `modReferences` to content mods.

### 3.9 Invasions and area buffs (built 2026-10-27, `Core/Events/`, first used by `Content/MechArmy/`)
- **An invasion inherits `Core/Events/CogpunkInvasion`** (a `ModSystem`), which re-implements vanilla's goblin-army rules line for line (decompiled `Main.StartInvasion`, `UpdateInvasion_Inner`, `InvasionWarning`, `NPC.SpawnNPC`, `NPC.NPCLoot`, `Main.DrawInvasionProgress`): size 80 + 40 per player with 5 Life Crystals, the approach from a world edge at `desiredWorldEventsUpdateRate` tiles a tick with "approaching from the west/east" (at once, then every 3600 ticks) and "has arrived", surface players within 3000 px of it (or near a town NPC 2 in 3 once it is mid-world) getting only its roster at spawnRate 20 / maxSpawns 5 x (2 + 0.3 x players), kill credit per roster NPC (`KillValue`, vanilla's `InvasionSlotCount`), "has been defeated" plus a `WorldFlagSystem` downed flag. The subclass supplies `FlagName`, `CanHappen` (the progression gate), `NaturalChanceDenominator`, `KillValue`, `FillPool` (the roster: weights, caps, minibosses by `Progress`), `IconPath` and `BarColor`; localization under `Mods.Cogpunk.Events.<ClassName>` (`DisplayName`, `ApproachingWest`, `ApproachingEast`, `Arrived`, `Defeated`).
- **One invasion at a time:** it won't start while any invasion (vanilla or Cogpunk) or the Old One's Army runs; `InvasionItemGuard` refuses the Goblin Battle Standard, Pirate Map and Snow Globe while one of ours runs; `InvasionDirector` cancels a vanilla invasion that starts during ours (or on the dawn ours wins) before vanilla's first warning. The dawn roll skips lunar events, lanterns, a morning Eclipse and the OOA, like vanilla's.
- **D2:** the server owns the state and saves it with the world (by name, clamped on load); clients get `Active`/`Size`/`SizeStart` in `NetSend` (joining players) and `InvasionStatePacket` (start, each kill with a "show the bar" flag, the end). The progress bar (`InvasionProgressBar`) is client UI in vanilla's layout and fade, shown after a kill or while near the invasion in vanilla's "near invasions" mode, and sits above vanilla's bar if a moon event shows one.
- **Spawns** go through `InvasionRules` (global `EditSpawnRate`/`EditSpawnPool`), which decides each player's zone once per tick (`CogpunkInvasion.ZoneOf`, server only) so other rules can defer to it (the Junkyard's rate does). The boss rule still wins: no spawns near a living `BossNPC`. A big NPC that must not spawn inside terrain overrides `ModNPC.SpawnNPC` to search a clear spot and returns `Main.maxNPCs` when there is none (see `Jaeger`, named `Yager` until 2026-10-28: `[LegacyName("Yager")]`).
- **Testing:** a `ModCommand` per invasion (`/mecharmy start|stop|win|status`), singleplayer or the dedicated server console only.
- **Area buffs on enemies** (the Annoy-o-tron's alarm) use `Core/Systems/NPCHaste` (+50% speed, refreshed by the source every few ticks on every side from synced positions, no packets). Cogpunk NPCs set `CogpunkSets.SelfHasting` and read `NPCHaste.FactorOf(NPC)` in their AI (top speed, acceleration, animation rate: root motion stays exact); every other enemy gets a generic extra half step in `PostAI` through `Collision.TileCollision` (horizontal only for walkers). Hasted enemies pulse ember red (`DrawEffects`).
- **Kamikaze enemies** detonate on the server (touch test against player hitboxes with a few px of slack), spawn a synced hostile blast through `SafeSpawn` (a circle in `Colliding`, hurting only in its first ticks), credit the invasion and remove themselves with `SyncNPC`; killed first, they only pop. Vanilla hurts players with knockback 4.5 whatever a hostile projectile's own value is, so a stronger push goes in `ModifyHitPlayer` (`modifiers.Knockback *=`).
- **Random mishaps are rolled on the server and replayed from synced state** (the Boombot's trip, 2026-10-28: a 2% roll every 60 ticks of sprinting; stumble, fall, roll on its momentum, fizz for the telegraph, blow up where it stops). The launch velocity rides the state change; friction and wall bounces run the same on every side; a hitbox that changes with the state (the ball while rolling) is fitted every tick on every side, bottom kept in place.
- **Drops:** event enemies drop coins at their goblin anchor's `value` (set `NPC.value` to the anchor's decompiled number, so every mode scales the same) and slice materials through `ModifyNPCLoot`. A drop whose odds change once it has dropped in a world (the Alarm Head: 1 in 10, then 1 in 100) subclasses `CommonDrop`: it picks `chanceDenominator` from a `WorldFlagSystem` flag in `TryDroppingItem` (server), sets the flag on success and sends `WorldData`, and reports the current odds to the bestiary (`AlarmHeadDrop`).
- **Friendly support minions** (the Alarm Head's Alarmobô, 2026-10-28) buff players without packets: every client runs the minion and calls `AlarmPlayer.Hear()` for its own local player when in range; the count is keyed by `Main.GameUpdateCount` and read on the next tick in `PostUpdateEquips` (vanilla updates players before projectiles). Several stack.

### 3.8 Ready for the 1.4.5 port
Prefer public tModLoader hooks. IL edits, `On_` detours and reflection on vanilla internals are a last resort. If you must use one, put it in `Core/Hooks/` with a comment saying why and which vanilla method it touches.

---

## 4. Anti-patterns → fix

| Anti-pattern | Fix |
|---|---|
| `Main.npc.Where(...)` / `new List<>()` in `AI` | `foreach (NPC n in Main.ActiveNPCs)` with preallocated buffers |
| `Main.LocalPlayer` inside NPC AI | `Main.player[NPC.target]` after `TargetClosest()` |
| `Main.rand` deciding an attack on every side | Roll on the server, store in `ai[]`, `netUpdate = true` |
| `Projectile.NewProjectile` from NPC AI with no netMode guard | `if (Main.netMode != NetmodeID.MultiplayerClient)` |
| Dust or sound spawned on a dedicated server | `if (!Main.dedServ)` |
| `ModContent.Request<Texture2D>(…, ImmediateLoad)` in `PreDraw` | Cached static `Asset<Texture2D>` |
| Mutating `Item.damage` at runtime | `ModifyWeaponDamage` |
| `Item.scale = 2f` to make a sprite bigger | Redraw at the larger size (D4) |
| Semi-transparent pixels for glow | `_Glow` texture + additive draw |
| `Projectile.NewProjectile` / `NPC.NewNPC` called directly | `SafeSpawn.TryNewProjectile` / `TryNewNPC`, and handle `false` |
| `while (!found) { … }` in world generation | `for (int attempt = 0; attempt < MaxAttempts && !found; attempt++)` |
| `Mod.Logger.Warn(...)` inside `AI`/`Update` | `SafeLog.Warn(key, format, arg)` (rate-limited, deferred formatting) |
| `Vector2.Normalize(v)` | `v.SafeNormalize(Vector2.Zero)` |
| Per-tile bevel or seam lines on a block (a visible grid) | D4 rule 7: seamless interior, outline only on exposed sides, `check_tile_seams.py` |
| "Done" without a GIF for an animated change | D5: build a GIF from the frames or a simulation, self-review it, and attach it or save it to `docs/media/` |
| Balance numbers picked by feel | D3: anchor + CSV row |

---

## 5. Definition of Done (copy into the report)

- [ ] **D0** Crash and loop risks listed and guarded (SafeSpawn, TileSafety, loop caps, NaN, packet validation, save defaults, SafeLog). Vanilla behavior checked by decompiling where relevant.
- [ ] **D1** Hot paths reviewed. No allocations, LINQ or uncached assets. Visuals client-only. Profiled if it's a boss or a many-entity system.
- [ ] **D2** Singleplayer ✔ · Host + client ✔ · Dedicated server ✔ or n/a, with sync points listed.
- [ ] **D3** `docs/balance/*.csv` row with anchor, numbers, delta % and modes tested.
- [ ] **D4** `check_sprite.py` passes for every new or changed PNG, `check_tile_seams.py` for every block sheet, and `check_flicker.py` for every generated animation (rule 17). `.aseprite` source committed.
- [ ] **D5** GIF (from frames or a simulation) or PNG for static visuals, self-reviewed, then shown in the response and/or saved to `docs/media/`. Otherwise, "no visual component". Media of models or animations this change made outdated deleted (D5 rule 6).
- [ ] Builds with 0 errors and 0 new warnings. en-US + pt-BR keys added. No vanilla name collisions. No hard content-mod dependency.

## 6. Report template (end of every feature or fix)

```markdown
## <Feature / fix name>: done
**Tier / archetype:** T? · <Gunsmith|Brawler|Tinker|vanilla class>
**Changed:** <files>
**Visual proof (D5):** <attached | docs/media/<…>.gif|png> · method: <sprite frames | simulation (omits …) | in-game> | no visual component
**Balance (D3):** docs/balance/<file>.csv → <row> · anchor <vanilla item> · Δ <±x%> · modes <C/E/M> · players <1/2>
**No-crash (D0):** <risks touched → guards used · decompiled checks>
**Co-op (D2):** SP ✔ · Host+client ✔ · Dedicated ✔/n-a · synced via <ai[] / ExtraAI / packet / WorldData>
**Performance (D1):** <hot paths touched + notes / profiler result>
**Pixel art (D4):** check_sprite ✔ (<colors>/<cap>) · palette changes: <none|…>
**Known issues / follow-ups:** <…>
```
