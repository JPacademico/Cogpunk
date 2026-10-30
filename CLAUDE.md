# Cogpunk: project rules for Claude

Cogpunk is a steampunk content mod for **tModLoader (Terraria)**. It adds weapons, a new class (the *Mechanist*, with a Steam Pressure resource), armor, biomes, mobs, bosses, materials, animations and attack patterns.
Overview: [README.md](README.md) · Toolchain and scaffolding specs: [SETUP.md](SETUP.md) · **Operating manual: [.claude/skills/cogpunk-dev/SKILL.md](.claude/skills/cogpunk-dev/SKILL.md). Load it before any code or asset work.**

## Core Directives (every feature, fix and asset)

0. **D0 No crashes, guaranteed. This is the most important directive and wins every conflict.** Nothing may crash the game, server or world generation, or cause a console loop (an error or log line repeating every tick). Anything that *could* is checked against the vanilla limits (SKILL.md D0, verified by decompiling with `ilspycmd`) and guarded or redesigned. Spawn only via `Core/Safety/SafeSpawn`, log only via `SafeLog`, bounds-check tiles with `TileSafety`, cap every loop, validate every packet index, and inherit the `Core/Templates` bases.
1. **D1 Optimization:** no allocations, LINQ or uncached assets in per-tick or draw code. Visuals run on clients only (`!Main.dedServ`). Sync only on change.
2. **D2 Co-op compatibility:** the server decides NPC, world and random outcomes. Player projectiles are owner-only. Test singleplayer, host + client, and a dedicated server when there is server logic.
3. **D3 Balance:** every combat stat gets a row in `docs/balance/*.csv` against a same-tier vanilla anchor (±15% effective DPS). **Cogpunk is played on Expert (user, 2026-10-27): every stat and number we define is the Expert value**, compared with the anchor's Expert stats and tested in Expert first; Classic gets half and Master 1.5x through vanilla's ratios (`Core/Templates/ExpertStats`, `CogpunkNPC.SetExpertStats`). **Boss treasure bags drop only in Expert and Master** (`ItemDropRule.BossBag`).
4. **D4 Pixel art:** drawn at 1× and exported 2× nearest-neighbor, Cogpunk palette only, lit from the top-left, ramp-colored outlines, no mixels or semi-transparent pixels. `tools/check_sprite.py` must pass. **Blocks connect seamlessly** like vanilla ores: no per-tile seams or bevels, outlines only on the clump's exposed edges, and `tools/check_tile_seams.py` must pass. **Detailed entities** (bosses, minibosses, detailed mobs, weapons the user names): three-quarter side view (flying-head bosses excepted), up to three multiplane parallax layers drawn with `Core/Visuals/DepthLayers` from generator-rendered poses (never rotated at runtime), Metal Slug-level detail, and every boss gets a themed death cinematic that locks the camera like its intro (`Core/Templates/BossNPC` + `Core/Visuals/CinematicCamera`). See SKILL.md D4 rules 13-16 and [docs/design/art-direction.md](docs/design/art-direction.md).
5. **D5 Visual proof:** any feature or fix with an animated result **must include a GIF**. Static sprites need a PNG. Build it from the animation frames (`tools/sheet2gif.py`) or a lightweight offline simulation that uses the real sprites and constants; in-game capture is **not** required. Show it in the response and/or save it to `docs/media/YYYY-MM-DD_<area>-<feature>.gif|png`, and self-review it before reporting. **When a change alters a model or animation, delete the `docs/media` GIFs/PNGs that show the outdated version** (user, 2026-10-28: project size); regenerate only the proofs the change needs.

## Facts that are easy to get wrong

- Target the **tModLoader stable 1.4.4 line** (.NET 8, pinned by `global.json`). Don't build against the `1.4.5` / `1.4.5-dev` branch.
- The tModLoader GitHub default branch is **`1.4.5`**. Read ExampleMod from **`/1.4.4/ExampleMod/`**.
- Pull vanilla stats from terraria.wiki.gg, never from memory. Never invent tModLoader APIs; check them in the ExampleMod 1.4.4 source first.
- `NPC.ai[0..3]` and `Projectile.ai[0..2]` are synced. `localAI[]` is not.
- Mod folder = `C:\tML\ModSources\Cogpunk` (outside OneDrive). Build with `dotnet build`, then *Build + Reload* in-game. Until Steam tModLoader is installed, compile-check with `dotnet msbuild -restore -t:Compile -p:RunAnalyzers=false`.
- Architecture: `Core/` = engine (no content), `Content/<Slice>/` = gameplay grouped by feature (biome, boss, class). See SKILL.md §3.0.
- Finish every feature or fix with the report template in SKILL.md §6.
