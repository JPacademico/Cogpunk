# Graph Report - C:\tML\ModSources\Cogpunk  (2026-10-23)

## Corpus Check
- 174 files · ~362,971 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1176 nodes · 1681 edges · 114 communities (68 shown, 46 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 122 edges (avg confidence: 0.84)
- Token cost: 390,217 input · 0 output

## Community Hubs (Navigation)
- Furniture & Armor Art Scripts
- Projectile Base & Scrap Cog
- Mice-bot Summon Item
- Petroleum Physics
- Shimmer Relocation Pass
- Item Base & Junkbait
- Junkyard Bounds System
- Junkyard Layout & Build Passes
- Junkyard Visual Proofs
- Junkyard Biome & Title
- Mice-bot Minion AI
- Scrap Bomb
- Petroleum Overlay Rendering
- Scrappybot Pet Item
- Armor Preview Tooling
- Scrap Armor Cog Volley
- Scrap Weapons Namespace
- Screwdriver Thrust Projectile
- D0 Safety Layer Concepts
- World-Gen Pass Registration
- Architecture & Co-op Concepts
- Mechanist & ExampleMod Refs
- Scrappy Trunk Tile
- Ground Truth & Done Criteria
- D1 Optimization & Anti-patterns
- Scrap Weapon Art Script
- Mod Packaging & Docs
- SafeLog
- GenPassUtils
- D3 Balance Rules
- Bosses & Progression Plan
- Junkyard Art Script
- Scaffold Art Script
- Scrappy Trunk Loot
- Junkyard Namespace
- Petroleum Tile
- Screwdriver Item
- Scrap Bomb Proofs
- Packet Base Class
- Scrappybot Pet Proofs
- Tile Seam Checker
- Fake Liquid & 1.4.5 Port
- Packet Registry
- Client Config
- Scrappy Trunk World Gen
- Texture Fallback & Pet Files
- D5 Visual Proof Tooling
- D4 Pixel Art Rules
- Mod Icons & Placeholder
- Mod Entry Point
- Trunk Cache Glow
- Scrap Armor Files
- Structure Clearance Sim
- Mice-bot Buff
- Scrappy Trunk Item
- Polished Metal
- Rusted Scrap Tile
- Sprite Checker
- Packet Dispatch
- Scrap Content Overview
- Trunk Loot Sim
- Cogpunk Named Sets
- Cog Set Bonus Proofs
- Rusted Cog Sprite
- Rusted Metal Sprite
- Mice-bot Sprites
- Junkbait Proof
- Petroleum Pool Proofs
- Screwdriver Proofs
- Sheet-to-GIF Tool
- Project File
- Arsenal Sprite Sheet Proof
- Container Name Hook
- Scrappybot Item Sprite
- Scrappybot Buff Icon
- Scrappybot Pet Sheet
- Screwdriver Sprites
- Petroleum Sinking Proof
- Structure Clearance Proof
- Trunk Loot Proof
- Mice-bot Burrow Proof
- Chest
- Tile
- Junkbait Item Sprite (dark scrap ball wi
- float
- Player
- bool
- float
- int
- Petroleum Tile Spritesheet (dark oily ti
- int
- Scrap Breastplate body cog-animation fra
- Scrap Breastplate body cog-animation fra
- Scrap Helmet head cog-animation frame 2
- Scrap Helmet head cog-animation frame 3
- Scrap Leggings legs cog-animation frame 
- Scrap Leggings legs cog-animation frame 
- EntitySource_ItemUse_WithAmmo
- Scrappy Bow Item Sprite (brass-limbed bo
- Scrappy Wand Sprite (rusty copper-tipped
- Scrappy Wand Bolt Projectile Sprite (sma
- Scrappy Bow GIF (1-5 arrows per shot, on
- Mice-bot Minion GIF (8 damage per bite, 
- Screwdriver GIF (31-tick thrust, hits go
- Scrappy Wand GIF (3-bolt burst every 26 
- GameConfiguration
- GenerationProgress
- Item
- PlayerDrawLayer
- PlayerDrawSet
- Position
- ExampleMod (branch 1.4.4)
- Core Toolchain Install (winget, IDE)

## God Nodes (most connected - your core abstractions)
1. `Canvas` - 34 edges
2. `Cogpunk.Core.Safety` - 31 edges
3. `MiceBotMinion` - 31 edges
4. `JunkyardPass` - 24 edges
5. `ScrappyTrunkTile` - 22 edges
6. `BiomeTitleSystem` - 20 edges
7. `ScrappybotPet` - 18 edges
8. `ScrapBombProjectile` - 18 edges
9. `JunkyardSystem` - 16 edges
10. `D0 No Crashes` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Proposed Progression Map` --semantically_similar_to--> `Vanilla Name Collisions`  [INFERRED] [semantically similar]
  README.md → .claude/skills/cogpunk-dev/SKILL.md
- `Junkyard cache glow GIF: chest inside heap pulses glow every 120 ticks with sparks` --references--> `ScrappyTrunkTile`  [INFERRED]
  docs/media/2026-10-22_junkyard-cache-glow.gif → Content/Furniture/ScrappyTrunkTile.cs
- `AnimatedEquip` --references--> `Scrap Helmet head cog-animation frame 1`  [INFERRED]
  Core/Visuals/AnimatedEquip.cs → Content/Scrap/Armor/ScrapHelmet_Head_1.png
- `Junkyard worldgen overview: deep pool 155 wide x 347 deep (floor y=652, 8 sludge rows) beside world border, junkyard 118, beach 19` --references--> `JunkyardPass`  [INFERRED]
  docs/media/2026-10-22_junkyard-overview.png → Content/Junkyard/Generation/JunkyardPass.cs
- `Out of Scope` --rationale_for--> `CrossMod`  [INFERRED]
  README.md → Core/Systems/CrossMod.cs

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Safety Layer enforcing D0** — _claude_skills_cogpunk_dev_skill_safespawn, _claude_skills_cogpunk_dev_skill_safelog, _claude_skills_cogpunk_dev_skill_tilesafety, _claude_skills_cogpunk_dev_skill_mathsafety, _claude_skills_cogpunk_dev_skill_safegenpass, _claude_skills_cogpunk_dev_skill_cogpunkpacket, _claude_skills_cogpunk_dev_skill_core_templates [EXTRACTED 1.00]
- **Junkyard World-Gen Pipeline** — _claude_skills_cogpunk_dev_skill_junkyardlayoutpass, _claude_skills_cogpunk_dev_skill_junkyardreservepass, _claude_skills_cogpunk_dev_skill_shimmerplacementpass, _claude_skills_cogpunk_dev_skill_genpassutils, _claude_skills_cogpunk_dev_skill_fake_liquid_overlay [EXTRACTED 1.00]
- **Art and Visual Verification Toolchain** — _claude_skills_cogpunk_dev_skill_check_sprite_py, _claude_skills_cogpunk_dev_skill_check_tile_seams_py, _claude_skills_cogpunk_dev_skill_sheet2gif_py, _claude_skills_cogpunk_dev_skill_terrain_sim_py, _claude_skills_cogpunk_dev_skill_armor_preview_py, _claude_skills_cogpunk_dev_skill_docs_media [INFERRED 0.85]
- **Scrap Weapon Sprites (rusty scrap palette)** — content_scrap_weapons_screwdriver_screwdriver_sprite, content_scrap_weapons_screwdriverprojectile_screwdriverprojectile_sprite, content_scrap_weapons_scrappywand_scrappywand_sprite [INFERRED 0.85]
- **Mice-bot sprite family (item, buff, minion share clockwork-mouse design)** — content_scrap_minions_micebot_micebot_sprite, content_scrap_minions_micebotbuff_micebotbuff_sprite, content_scrap_minions_micebotminion_micebotminion_sprite [INFERRED 0.95]
- **Petroleum pool visual proofs** — docs_media_2026_10_22_junkyard_petroleum_overview_image, docs_media_2026_10_22_junkyard_petroleum_surface_image, docs_media_2026_10_22_junkyard_petroleum_image [INFERRED 0.85]
- **Junkyard footprint reservation vs Dungeon/Shimmer** — docs_media_2026_10_22_junkyard_structure_clearance_image [INFERRED 0.85]
- **Scrap arsenal offline-simulation visual proofs (D5)** — docs_media_2026_10_22_scrap_bow_image, docs_media_2026_10_22_scrap_wand_image, docs_media_2026_10_22_scrap_screwdriver_image, docs_media_2026_10_22_scrap_mice_bot_image, docs_media_2026_10_22_scrap_arsenal_sprites_image, concept_d5_offline_visual_proof [INFERRED 0.85]
- **Scrap armor cog set bonus variants (aim vs lob)** — docs_media_2026_10_22_scrap_armor_cog_aim_image, docs_media_2026_10_22_scrap_armor_cog_lob_image, concept_scrap_armor_set_bonus_cogs [INFERRED 0.85]
- **Screwdriver visual proof set** — docs_media_2026_10_23_scrap_screwdriver_sprites_image, docs_media_2026_10_23_scrap_screwdriver_image [INFERRED 0.85]
- **Crash-safe Core framework (D0)** — core_safety_safespawn_cogpunk_core_safety_safespawn, core_safety_safelog_cogpunk_core_safety_safelog, core_safety_tilesafety_cogpunk_core_safety_tilesafety, core_safety_mathsafety_cogpunk_core_safety_mathsafety, core_networking_packetregistry_cogpunk_core_networking_packetregistry, core_worldgeneration_safegenpass_cogpunk_core_worldgeneration_safegenpass, core_systems_crossmod_cogpunk_core_systems_crossmod [EXTRACTED 1.00]
- **Seamless block art pipeline** — _claude_skills_cogpunk_dev_skill_terrain_exposure_template, _claude_skills_cogpunk_dev_skill_seamless_blocks [EXTRACTED 1.00]
- **Mechanist class system** — readme_mechanist, readme_steam_pressure, readme_overheat, _claude_skills_cogpunk_dev_skill_pressureplayer, _claude_skills_cogpunk_dev_skill_vent_keybind [INFERRED 0.85]
- **Scrap Breastplate body cog animation frame set** — content_scrap_armor_scrapbreastplate_body_sprite, content_scrap_armor_scrapbreastplate_body_1_sprite, content_scrap_armor_scrapbreastplate_body_2_sprite, content_scrap_armor_scrapbreastplate_body_3_sprite [INFERRED 0.85]
- **Scrap Helmet head cog animation frame set** — content_scrap_armor_scraphelmet_head_sprite, content_scrap_armor_scraphelmet_head_1_sprite, content_scrap_armor_scraphelmet_head_2_sprite, content_scrap_armor_scraphelmet_head_3_sprite [INFERRED 0.85]
- **Scrap Leggings legs cog animation frame set** — content_scrap_armor_scrapleggings_legs_sprite, content_scrap_armor_scrapleggings_legs_1_sprite, content_scrap_armor_scrapleggings_legs_2_sprite, content_scrap_armor_scrapleggings_legs_3_sprite [INFERRED 0.85]
- **Junkyard biome visual assets** — content_junkyard_junkyardbiome_icon_sprite, content_junkyard_tiles_polishedmetaltile_sprite, assets_ui_biometitleornament_sprite [INFERRED 0.75]
- **Seamless tile framing sheets** — content_junkyard_tiles_polishedmetaltile_sprite, content_scrap_tiles_rustedscraptile_sprite [INFERRED 0.85]
- **Scrappy Trunk chest textures** — content_furniture_scrappytrunk_sprite, content_furniture_scrappytrunktile_sprite, content_furniture_scrappytrunktile_highlight_sprite [INFERRED 0.95]
- **Junkyard biome visual proofs (worldgen, sludge, cache, title)** — docs_media_2026_10_22_junkyard_overview_proof, docs_media_2026_10_22_junkyard_surface_proof, docs_media_2026_10_22_junkyard_sludge_proof, docs_media_2026_10_22_junkyard_cache_glow_proof, docs_media_2026_10_22_junkyard_title_proof [INFERRED 0.85]
- **Scrap armor visual proofs (walk cycle, offset fix, cog volley)** — docs_media_2026_10_21_scrap_armor_proof, docs_media_2026_10_21_scrap_armor_proof_sheet, docs_media_2026_10_22_scrap_armor_walk_offset_check_proof, docs_media_2026_10_22_scrap_armor_cog_volley_proof [INFERRED 0.85]
- **Core Directives D0-D5** — _claude_skills_cogpunk_dev_skill_d0_no_crashes, _claude_skills_cogpunk_dev_skill_d1_optimization, _claude_skills_cogpunk_dev_skill_d3_balance, _claude_skills_cogpunk_dev_skill_d4_pixel_art, _claude_skills_cogpunk_dev_skill_d5_visual_proof [EXTRACTED 1.00]
- **D3 Balance Measurement Pipeline** — _claude_skills_cogpunk_dev_skill_d3_balance, _claude_skills_cogpunk_dev_skill_tier_anchor_table, setup_balance_sheet_schema, docs_balance_loadouts_balance_loadouts, setup_test_worlds [INFERRED 0.85]
- **Pixel Art & Visual Proof Tooling** — setup_check_sprite_py, setup_check_tile_seams_py, setup_sheet2gif_py, setup_cogpunk_palette, _claude_skills_cogpunk_dev_skill_terrain_exposure_template [INFERRED 0.85]
- **Scaffold art set (icon, small icon, placeholder)** — docs_media_2026_10_20_scaffold_icons_image, icon_image, icon_small_image, assets_textures_placeholder_image [INFERRED 0.85]
- **Rusted Scrap world generation** — docs_media_2026_10_21_scrap_overview_image, docs_media_2026_10_21_scrap_overview_surface_heaps, docs_media_2026_10_21_scrap_overview_underground_nodes [INFERRED 0.85]

## Communities (114 total, 46 thin omitted)

### Community 0 - "Furniture & Armor Art Scripts"
Cohesion: 0.06
Nodes (55): cache_variant(), cut_into_cells(), make_sheets(), outline(), Source for shared furniture sprites (D4). Run from the repo root: python -P…, 16x17 chest art -> 18x19 tile frame with 1-px gutters (8x8 top cells, 8x9…, back_shoulder_cell(), body_idle() (+47 more)

### Community 1 - "Projectile Base & Scrap Cog"
Cohesion: 0.05
Nodes (25): CogpunkProjectile, ScrapCogProjectile, Color, float, int, string, Vector2, PetState (+17 more)

### Community 2 - "Mice-bot Summon Item"
Cohesion: 0.05
Nodes (29): MiceBot, EntitySource_ItemUse_WithAmmo, List, Player, Vector2, ScrappyBow, EntitySource_ItemUse_WithAmmo, float (+21 more)

### Community 3 - "Petroleum Physics"
Cohesion: 0.05
Nodes (26): PetroleumPlayer, bool, Color, float, int, Scrap Breastplate body cog-animation frame 1, Scrap Breastplate body equip sheet (9x4 composite: torso with cog emblem, arm swing poses, shoulders), ScrapBreastplate (+18 more)

### Community 4 - "Shimmer Relocation Pass"
Cohesion: 0.07
Nodes (26): biome, BitArray, ShimmerPlacementPass, GameConfiguration, GenerationProgress, int, string, ScrapMoundPass (+18 more)

### Community 5 - "Item Base & Junkbait"
Cohesion: 0.05
Nodes (20): CogpunkItem, Junkbait, int, Player, PolishedMetal, ScrapHelmet, int, Item (+12 more)

### Community 6 - "Junkyard Bounds System"
Cohesion: 0.07
Nodes (16): BinaryReader, BinaryWriter, JunkyardSystem, Rectangle, string, SpawnBudgetSystem, VanillaRecipeGroups, string (+8 more)

### Community 7 - "Junkyard Layout & Build Passes"
Cohesion: 0.08
Nodes (18): JunkyardLayoutPass, GameConfiguration, GenerationProgress, JunkyardPass, Chest, float, GameConfiguration, GenerationProgress (+10 more)

### Community 8 - "Junkyard Visual Proofs"
Cohesion: 0.08
Nodes (29): Rusted Scrap tile recolor before/after: brighter orange rust flecks, seamless clumps, Junkyard cache glow GIF: chest inside heap pulses glow every 120 ticks with sparks, Junkyard worldgen overview: deep pool 155 wide x 347 deep (floor y=652, 8 sludge rows) beside world border, junkyard 118, beach 19, Repulsing sludge GIF: player bounced off 8 sludge rows above pool water (depth/vy readout), Junkyard surface: pool rim, scrap heaps with puddles, central heap cache, beach with palm stand-ins, background(), cache_sim(), main() (+21 more)

### Community 9 - "Junkyard Biome & Title"
Cohesion: 0.07
Nodes (22): Asset, BiomeTitleOrnament (brass gear-ended bar ornament), JunkyardBiome, Player, JunkyardBiome icon (rusty scrap heap), Vector2, BiomeTitleSystem, Color (+14 more)

### Community 10 - "Mice-bot Minion AI"
Cohesion: 0.12
Nodes (11): MiceBotMinion, Mode, bool, Color, float, HitModifiers, int, NPC (+3 more)

### Community 11 - "Scrap Bomb"
Cohesion: 0.07
Nodes (19): ScrapBomb, float, int, LocalizedText, Player, Vector2, ScrapBomb item sprite (pipe bomb), ScrapBombProjectile (+11 more)

### Community 12 - "Petroleum Overlay Rendering"
Cohesion: 0.10
Nodes (11): PetroleumOverlay, PetroleumOverlaySystem, float, GameTime, SpriteBatch, string, Vector2, SceneOverlayRegistry (+3 more)

### Community 13 - "Scrappybot Pet Item"
Cohesion: 0.10
Nodes (19): Scrappybot, EntitySource_ItemUse_WithAmmo, Player, Vector2, ScrappybotBuff, Player, CogpunkBuff, CogpunkItem (+11 more)

### Community 14 - "Armor Preview Tooling"
Cohesion: 0.17
Nodes (24): Scrap Armor walk GIF: animated walk cycle on dark and sky backgrounds (frame/cog counter), Scrap Armor PNG: 12-frame walk sheet on dark and light backgrounds, Scrap armor walk offset check: old preview (bug) vs game-accurate head bob on frames 7-8, 14-15, cell(), compose(), load_frames(), main(), D5 preview of an armor set worn by a stand-in player, replaying vanilla's frame… (+16 more)

### Community 15 - "Scrap Armor Cog Volley"
Cohesion: 0.13
Nodes (13): ScrapArmorPlayer, bool, float, int, NPC, Vector2, Scrap armor set bonus cog volley GIF: fires a cog every 45 ticks of movement at 140-HP dummies, HurtModifiers (+5 more)

### Community 16 - "Scrap Weapons Namespace"
Cohesion: 0.18
Nodes (6): CrossMod, Cogpunk.Content.Scrap.Minions, Cogpunk.Content.Scrap.Items, Cogpunk.Core.Safety, Cogpunk.Content.Scrap.Weapons, Cogpunk.Core.Systems

### Community 17 - "Screwdriver Thrust Projectile"
Cohesion: 0.12
Nodes (9): ScrewdriverProjectile, Color, float, HitModifiers, NPC, Rectangle, CogpunkSets, bool (+1 more)

### Community 18 - "D0 Safety Layer Concepts"
Cohesion: 0.15
Nodes (17): CogpunkPacket, Core Templates Bases (CogpunkItem/NPC/Projectile/Tile/Wall/Buff), CrossMod.TryCall, D0 No Crashes, GenPassUtils, Junkyard Vanilla Region Replacement, JunkyardLayoutPass, JunkyardReservePass (+9 more)

### Community 19 - "World-Gen Pass Registration"
Cohesion: 0.15
Nodes (7): RustedScrapWorldGen, GenPass, List, Cogpunk.Core.WorldGeneration, Cogpunk.Content.Scrap.Tiles, Cogpunk.Content.Junkyard.Generation, Cogpunk.Content.Scrap.Generation

### Community 20 - "Architecture & Co-op Concepts"
Cohesion: 0.17
Nodes (16): Core/Content Slice Architecture, BiomeTitleSystem, Cogpunk Development Skill, D2 Co-op Compatibility, README.md, SETUP.md, StateMachineNPC, Synced ai[] vs localAI[] State (+8 more)

### Community 21 - "Mechanist & ExampleMod Refs"
Cohesion: 0.12
Nodes (16): ExampleMod 1.4.4 Reference, ExampleMod Reference Map, en-US / pt-BR Localization Mirroring, Mechanist Class (MechanistDamage), Mechanist DamageClass & PressurePlayer, PressurePlayer (Steam Pressure), Vanilla Name Collisions, Vent Keybind (+8 more)

### Community 22 - "Scrappy Trunk Tile"
Cohesion: 0.14
Nodes (6): ScrappyTrunkTile, int, uint, ScrappyTrunkTile_Highlight (smart-cursor outline mask, near-blank), Point, SmartInteractScanSettings

### Community 23 - "Ground Truth & Done Criteria"
Cohesion: 0.14
Nodes (14): docs/balance CSV Sheets, check_tile_seams.py, Definition of Done, Ground Truth (Toolchain Facts), Report Template, terraria.wiki.gg (Vanilla Numbers), tModLoader 1.4.4 Stable Target, Vanilla Entity Limits (+6 more)

### Community 24 - "D1 Optimization & Anti-patterns"
Cohesion: 0.15
Nodes (13): Anti-patterns Table, Boilerheart (example boss), D1 Optimization, Hot Paths, RivetBolt, SafeLog, SafeSpawn, Seamless Blocks Rule (+5 more)

### Community 25 - "Scrap Weapon Art Script"
Cohesion: 0.19
Nodes (7): draw_rod(), make_mouse_frames(), make_scrappy_wand(), make_screwdriver_icon(), mouse(), Source for the scrap arsenal sprites (D4). Run from the repo root: python -P…, segments: list of (length, half_width, (outline, dark, mid, light)). origin =…

### Community 26 - "Mod Packaging & Docs"
Cohesion: 0.18
Nodes (13): build.txt Mod Build Config, buildIgnore (art/docs/tools/py/ps1 excluded from .tmod), Mod Description (in-game), Steam Workshop Description, Boss Checklist Integration, CLAUDE.md, Cogpunk Mod (README overview), Junkyard Biome (replaces left beach) (+5 more)

### Community 27 - "SafeLog"
Cohesion: 0.19
Nodes (6): SafeLog, Dictionary, int, Exception, ILog, object

### Community 28 - "GenPassUtils"
Cohesion: 0.24
Nodes (8): GenPass, List, GenPass, List, GenPassUtils, GenPass, List, Func

### Community 29 - "D3 Balance Rules"
Cohesion: 0.22
Nodes (11): Attack-Pattern Fairness, 4% Base Crit Rule, D3 Balance, Effective DPS Formula, MiceBot / MiceBotMinion, Tier T0-T10 Vanilla Anchor Table, Tier Table T0-T10, Balance Loadouts (D3 reference gear) (+3 more)

### Community 30 - "Bosses & Progression Plan"
Cohesion: 0.27
Nodes (11): StateMachineNPC Boss AI Pattern (Boilerheart example), Boilerheart (Boss 1), Chronarch (Superboss), The Clockwork Leviathan (Boss 2), Content Scope, The Grand Orrery (Boss 3), Proposed Progression Map, Skyport Biome (+3 more)

### Community 31 - "Junkyard Art Script"
Cohesion: 0.24
Nodes (8): make_metal_icon(), make_petroleum_sheet(), make_terrain_sheet(), petroleum_cell(), Source for the Junkyard slice sprites (D4). Run from the repo root: python -P…, The item reads as a single welded cube: square corners instead of the terrain…, 8x8 art for one terrain frame. exposure = 'TRBL' with 'o'/'d' (exposed) or '-'…, terrain_frame()

### Community 32 - "Scaffold Art Script"
Cohesion: 0.29
Nodes (8): gear_mask(), hole_core(), make_icon(), make_small_icon(), Source for the scaffold sprites (icon.png, icon_small.png,…, Pixel-centre test: True where the gear (body + teeth, minus the hole) is solid., Flat brass face lit from the top-left: lit rim, shadowed rim, ramp-0 outline., shade_gear()

### Community 33 - "Scrappy Trunk Loot"
Cohesion: 0.24
Nodes (6): ScrappyTrunkLoot, Chest, int, List, Cogpunk.Content.Furniture, UnifiedRandom

### Community 34 - "Junkyard Namespace"
Cohesion: 0.20
Nodes (4): Cogpunk.Content.Junkyard, Cogpunk.Content.Junkyard.Items, Cogpunk.Core.Hooks, Cogpunk.Content.Junkyard.Tiles

### Community 35 - "Petroleum Tile"
Cohesion: 0.18
Nodes (4): PetroleumTile, int, SpriteBatch, short

### Community 36 - "Screwdriver Item"
Cohesion: 0.20
Nodes (6): Screwdriver, EntitySource_ItemUse_WithAmmo, int, LocalizedText, Player, Vector2

### Community 37 - "Scrap Bomb Proofs"
Cohesion: 0.27
Nodes (10): Blast radius 4 tiles (64 px), no tile damage, Scrap Bomb buff GIF: direct hit 43 + 32 blast, 5-tile (80px) radius vs Grenade 8x8, Direct hit 51 + 32 blast damage, Scrap Bomb Throw Simulation GIF, dummy_rect(), first_hit(), in_blast(), main() (+2 more)

### Community 38 - "Packet Base Class"
Cohesion: 0.22
Nodes (5): CogpunkPacket, BinaryReader, Mod, ILoadable, ModPacket

### Community 39 - "Scrappybot Pet Proofs"
Cohesion: 0.27
Nodes (9): Follow state: pet walks behind player over terrain, Scrappybot Pet Behavior Simulation GIF, draw_owner(), main(), owner_script(), D5 simulation of the Scrappybot pet: follow -> owner stands still -> power down…, Owner x position and velocity: walks right, stands still for 7 s, then walks…, Neutral placeholder for the player (no vanilla art is used). (+1 more)

### Community 40 - "Tile Seam Checker"
Cohesion: 0.29
Nodes (9): After: seamless merged scrap texture, Before: visible per-tile seams on heap and cave node, Rusted Scrap Tile Seamless Before/After, edge_bias(), interior_frames(), luminance(), main(), Check that a block's tile sheet connects seamlessly (D4 "seamless blocks"… (+1 more)

### Community 41 - "Fake Liquid & 1.4.5 Port"
Cohesion: 0.22
Nodes (9): Fake Liquid via Overlay, 1.4.5 Port Readiness, SceneOverlayRegistry, Out of Scope, Technical Baseline, tModPorter, In-game Developer Mods (DragonLens, Modders Toolkit, Boss Checklist), Maintenance (monthly stable, 1.4.5 watch) (+1 more)

### Community 42 - "Packet Registry"
Cohesion: 0.22
Nodes (5): PacketRegistry, bool, int, List, Cogpunk.Core.Networking

### Community 43 - "Client Config"
Cohesion: 0.22
Nodes (6): ConfigScope, CogpunkClientConfig, bool, float, Cogpunk.Core.Configs, ModConfig

### Community 44 - "Scrappy Trunk World Gen"
Cohesion: 0.25
Nodes (6): ScrappyTrunkPass, ScrappyTrunkWorldGen, GameConfiguration, GenerationProgress, int, Cogpunk.Content.Furniture.Generation

### Community 45 - "Texture Fallback & Pet Files"
Cohesion: 0.28
Nodes (4): TextureFallback, string, Cogpunk.Core.Templates, Cogpunk.Content.Scrap.Pets

### Community 46 - "D5 Visual Proof Tooling"
Cohesion: 0.32
Nodes (8): AnimatedEquip, tools/sim/armor_preview.py, D5 Visual Proof, docs/media Visual Proof Folder, Offline Simulation Proof, sheet2gif.py, tools/record-gif.ps1 (untested draft), tools/sheet2gif.py

### Community 47 - "D4 Pixel Art Rules"
Cohesion: 0.36
Nodes (8): check_sprite.py, Cogpunk Palette (cogpunk.gpl), D4 Pixel Art, terrain_exposure.json Template, tools/sim/terrain.py, tools/check_sprite.py, Cogpunk Master Palette (cogpunk.gpl), Sprite Specifications (2x scale, 18px tile stride, armor sheets)

### Community 48 - "Mod Icons & Placeholder"
Cohesion: 0.29
Nodes (8): Placeholder Texture Sprite, Missing-texture fallback (gray checker with gold question mark), Icons shown on dark and light backgrounds, Scaffold Icons Preview, Brass cog with glowing orange core on dark slate frame, Cogpunk Mod Icon, Small brass cog with orange core (mod browser icon), Cogpunk Small Mod Icon

### Community 49 - "Mod Entry Point"
Cohesion: 0.29
Nodes (3): CogpunkMod, Cogpunk, Mod

### Community 50 - "Trunk Cache Glow"
Cohesion: 0.29
Nodes (3): Tile, SpriteBatch, TileDrawInfo

### Community 52 - "Structure Clearance Sim"
Cohesion: 0.48
Nodes (6): cogpunk(), cuts_reserve(), main(), D5 simulation: how the Junkyard keeps vanilla's big structures away…, roll_world(), vanilla_shimmer()

### Community 53 - "Mice-bot Buff"
Cohesion: 0.33
Nodes (3): CogpunkBuff, MiceBotBuff, Player

### Community 54 - "Scrappy Trunk Item"
Cohesion: 0.33
Nodes (3): ScrappyTrunk, ScrappyTrunk item sprite (rusty chest), ScrappyTrunkTile sheet (2x2 chest frames, open/closed/locked)

### Community 55 - "Polished Metal"
Cohesion: 0.33
Nodes (4): PolishedMetal item sprite (steel block), PolishedMetalTile, int, PolishedMetalTile framing sheet (grey metal plates)

### Community 56 - "Rusted Scrap Tile"
Cohesion: 0.40
Nodes (3): CogpunkTile, RustedScrapTile, int

### Community 57 - "Sprite Checker"
Cohesion: 0.60
Nodes (4): check(), load_gpl(), main(), Check sprites against the Cogpunk pixel-art rules (D4). Exit code 1 if any file…

### Community 59 - "Scrap Content Overview"
Cohesion: 0.50
Nodes (4): Extractinator table from Rusted Scrap: Rusted Cog 66%, Rusted Metal 33%, Scrappybot 1%, Scrap Content Overview, Surface scrap heaps, heights 3-6, one per left-side biome, Underground silt nodes converted (1 in 10); needs Gold/Platinum pickaxe (55%)

### Community 60 - "Trunk Loot Sim"
Cohesion: 0.67
Nodes (3): fill(), main(), D5 replay of the Scrappy Trunk world-generation rules…

### Community 61 - "Cogpunk Named Sets"
Cohesion: 0.67
Nodes (3): CogpunkSets, Mechanical Enemies Set (Screwdriver +50%), Scrappy Trunk Loot

### Community 62 - "Cog Set Bonus Proofs"
Cohesion: 1.00
Nodes (3): Scrap Armor Set Bonus: Movement-Triggered Cogs, Scrap Armor Cog Aim GIF (set bonus: cogs aimed at nearest slime, every 45 ticks of movement), Scrap Armor Cog Lob GIF (set bonus: lobs a cog ahead while moving)

### Community 63 - "Rusted Cog Sprite"
Cohesion: 0.67
Nodes (3): Extractinator drop from Rusted Scrap (66%), Rusted Cog Item Sprite, Rusty orange gear icon (crafting material)

### Community 64 - "Rusted Metal Sprite"
Cohesion: 0.67
Nodes (3): Extractinator drop from Rusted Scrap (33%), Rusted Metal Item Sprite, Rusty copper-colored metal plate with rivets

### Community 65 - "Mice-bot Sprites"
Cohesion: 0.67
Nodes (3): Mice-bot Summon Item Sprite (rusty clockwork mouse), Mice-bot Buff Icon (clockwork mouse), Mice-bot Minion Spritesheet (vertical walk/burrow frames)

### Community 66 - "Junkbait Proof"
Cohesion: 0.67
Nodes (3): Junkbait Sprite & Recipe Preview (PNG), Junkbait Recipe (Scrappybot + 10 Rusted Scrap + 10 Copper/Tin Bar @ Anvil), Junkbait Not Usable Until Junkyard Boss Exists (Never Consumed)

### Community 67 - "Petroleum Pool Proofs"
Cohesion: 0.67
Nodes (3): Petroleum Pool Worldgen Overview (PNG), Junkyard Surface: Pool Rim, Heaps, Puddles, Cache, Beach (PNG), Deep Petroleum Pool Layout (155 wide, 347 deep, 8 petroleum rows, floor halfway to underworld, past x<40 world border)

### Community 68 - "Screwdriver Proofs"
Cohesion: 0.67
Nodes (3): Screwdriver Thrust Simulation (GIF), Screwdriver Sprites Proof (PNG), Screwdriver 31-tick thrust to 6.5 tiles, hits on extend and retract

## Ambiguous Edges - Review These
- `Config File Contents (build.txt, global.json, .gitignore, .gitattributes)` → `buildIgnore (art/docs/tools/py/ps1 excluded from .tmod)`  [AMBIGUOUS]
  build.txt · relation: conceptually_related_to
- `ScrapBombProjectile` → `ScrapBombProjectile sprite (2-frame pipe bomb, lit fuse)`  [AMBIGUOUS]
  Content/Scrap/Weapons/ScrapBombProjectile.png · relation: references

## Knowledge Gaps
- **105 isolated node(s):** `Microsoft.NET.Sdk`, `Cogpunk`, `SurfaceBiome`, `PetState`, `Chronarch (Superboss)` (+100 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **46 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Config File Contents (build.txt, global.json, .gitignore, .gitattributes)` and `buildIgnore (art/docs/tools/py/ps1 excluded from .tmod)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `ScrapBombProjectile` and `ScrapBombProjectile sprite (2-frame pipe bomb, lit fuse)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `Cogpunk.Core.Safety` connect `Scrap Weapons Namespace` to `Projectile Base & Scrap Cog`, `Junkyard Namespace`, `Mice-bot Summon Item`, `Shimmer Relocation Pass`, `Junkyard Bounds System`, `Packet Registry`, `Scrappy Trunk World Gen`, `Texture Fallback & Pet Files`, `Petroleum Overlay Rendering`, `Mod Entry Point`, `World-Gen Pass Registration`, `Scrap Armor Files`, `SafeLog`?**
  _High betweenness centrality (0.452) - this node is a cross-community bridge._
- **Why does `CrossMod` connect `Scrap Weapons Namespace` to `Fake Liquid & 1.4.5 Port`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Why does `Out of Scope` connect `Fake Liquid & 1.4.5 Port` to `Scrap Weapons Namespace`?**
  _High betweenness centrality (0.182) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Canvas` (e.g. with `cut_into_cells()` and `make_sheets()`) actually correct?**
  _`Canvas` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `JunkyardPass` (e.g. with `Junkyard worldgen overview: deep pool 155 wide x 347 deep (floor y=652, 8 sludge rows) beside world border, junkyard 118, beach 19` and `Junkyard surface: pool rim, scrap heaps with puddles, central heap cache, beach with palm stand-ins`) actually correct?**
  _`JunkyardPass` has 2 INFERRED edges - model-reasoned connections that need verification._