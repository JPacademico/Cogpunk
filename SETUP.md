# Cogpunk: Technical Setup & Scaffolding Data

> Everything needed to go from an empty PC to a Cogpunk mod that builds, loads, and can be tested in co-op, plus the exact data and conventions for the first scaffolding (milestone **M0**).
> Facts were verified on **2026-10-20**. Re-check §1 whenever tModLoader ships a new monthly stable build.

---

## 0. TL;DR checklist

- [ ] Steam + Terraria (owned) + **tModLoader** (free, Steam app `1281930`)
- [ ] **.NET 8 SDK** x64 (already installed: `8.0.318` ✔)
- [ ] IDE: **Visual Studio 2022 17.8+** (or 2026) with *.NET desktop development*, or **VS Code + C# Dev Kit**
- [ ] tModLoader data folder **moved out of OneDrive** with `-tmlsavedirectory C:\tML` (§3). The folder exists ✔; the `cli-argsConfig.txt` line is still to do after installing tModLoader.
- [x] Repo at `C:\tML\ModSources\Cogpunk` with `git` + `git lfs` (done 2026-10-20)
- [ ] Art: **Aseprite** (or Pixelorama), the Cogpunk palette (§8.5), `tools/check_sprite.py`
- [ ] Visual proof (D5): `tools/sheet2gif.py` + Pillow simulations (§8.9). ffmpeg/ScreenToGif are optional, for in-game capture only.
- [ ] Dev mods: DragonLens, Modders Toolkit, Recipe Browser, Boss Checklist (§6)
- [ ] Claude Code: project skill + `CLAUDE.md` (in repo), DeepWiki MCP, optional csharp-lsp / Aseprite MCP / SpriteCook (§7)
- [ ] Follow the scaffolding procedure (§9) and finish the M0 exit criteria

---

## 1. Platform baseline (verified 2026-10-20)

| Component | Version / requirement | Notes |
|---|---|---|
| **Terraria** | Must be owned on Steam (app `105600`) | Terraria itself is at 1.4.5.x. tModLoader is a separate Steam app that only checks ownership. |
| **tModLoader** | Stable **`v2026.08.3.0`** ("October 2026 Stable Update"), **1.4.4 line** | Stable builds come out monthly on the 1st and can contain breaking changes. |
| tModLoader 1.4.5 port | In development on the `1.4.5` branch / Steam beta `1.4.5-dev` | For contributors only. **Don't develop or publish on it.** It will be ported later with tModPorter and `MigrationGuide_1.4.5.md`. |
| **.NET SDK** | **8.0.x x64** | The tModLoader wiki: *"Don't download the .NET 10.0 or .NET 9.0 versions, those will not work."* If a newer SDK is also installed, pin 8.0 with `global.json` (§8.3). |
| Language | C# `LangVersion latest` (from the generated `.csproj`) | |
| **Visual Studio** | 2022 **v17.8+** (the version the wiki requires) | VS 2026 (v18) should work too, but the tModLoader wiki only documents 2022. Fall back to 2022 if launch profiles misbehave. |
| Reference code | **ExampleMod, branch `1.4.4`** | ⚠ The tModLoader GitHub repo's **default branch is now `1.4.5`**. Always browse `…/tree/1.4.4/ExampleMod`. |

## 2. This machine: audit (2026-10-20)

| Item | State |
|---|---|
| .NET SDK / runtime | ✔ SDK `8.0.318`, runtime `8.0.21` |
| Git / Git LFS | ✔ `2.47.0` / ✔ `3.5.1` |
| VS Code | ✔ installed (extensions: GitLens, Live Server). C# Dev Kit is **missing** |
| winget | ✔ `1.29` |
| Python + Pillow | ✔ Python 3.14 + Pillow 12.3 (used by `tools/*.py`) |
| Steam / Terraria / tModLoader | ✗ not installed. Reference build `v2026.08.3.0` from the official GitHub release is in `C:\tML\_reference\` and used for compile checks and decompiling (SHA-256 verified against the release digest) |
| ilspycmd (decompiler) | ✔ `9.1.0.7988` (dotnet global tool) |
| ffmpeg, Aseprite, gh CLI | ✗ not installed |
| **Documents folder** | ⚠ Redirected to **OneDrive** (`C:\Users\jorda\OneDrive\Documentos`). tModLoader's default data folder would be `…\OneDrive\Documentos\My Games\Terraria\tModLoader\`. See §3. |
| This repo folder | `C:\Users\jorda\OneDrive\Documentos\GitHub\Cogpunk` (inside OneDrive, not a git repo yet) |

## 3. Workspace layout & OneDrive (decision: recommended layout)

**Why it matters**
- `Cogpunk.csproj` contains `<Import Project="..\tModLoader.targets" />`. tModLoader writes `tModLoader.targets` into **ModSources**, so the mod folder has to sit **directly inside ModSources**.
- Your Documents folder is synced by OneDrive. Builds rewrite `bin/`, `obj/` and `.tmod` constantly, which fights with sync and git. Users have reported tModLoader errors in OneDrive folders, such as *"The cloud file provider is not running"* and failures creating the `Mods` and `ResourcePacks` folders.

**Recommended layout**

```
C:\tML\                         ← tModLoader data folder (outside OneDrive)
├─ ModSources\
│  ├─ tModLoader.targets        (written by tModLoader)
│  └─ Cogpunk\                  ← THE GIT REPO (move these docs here during M0)
├─ Mods\  Players\  Worlds\  Logs\ …
```

1. Create `C:\tML`.
2. Create `cli-argsConfig.txt` in the **tModLoader install folder** (by default `C:\Program Files (x86)\Steam\steamapps\common\tModLoader\`) containing:
   ```
   -tmlsavedirectory C:\tML
   ```
   `-tmlsavedirectory` sets the folder exactly as given, without appending `\tModLoader`. Arguments in this file apply to **every** launch, including Steam and the debugger.
3. Launch tModLoader once. It creates `C:\tML\ModSources\tModLoader.targets`.
4. The repo lives at `C:\tML\ModSources\Cogpunk`. Use the git remote, not OneDrive, as the backup.

> Side effect: players and worlds for **all** your modded play now live in `C:\tML`. That also keeps dev saves separate from personal ones.
> Alternative (not recommended): keep the defaults, mark the ModSources folder *Always keep on this device*, and pause OneDrive while building.

## 4. Core toolchain: install

Run these in PowerShell (package IDs verified with `winget show` on 2026-10-20):

```powershell
winget install --id Valve.Steam -e
```
Then, in Steam: own **Terraria** (`steam://store/105600`) and install **tModLoader** (`steam://install/1281930`). Launch tModLoader once **after** §3 step 2.

```powershell
# .NET 8 SDK is already installed (8.0.318); run this only on a new machine
winget install --id Microsoft.DotNet.SDK.8 -e
```

**IDE (pick one primary):**

```powershell
# Visual Studio 2022 Community + ".NET desktop development" workload (best debugger, Edit & Continue)
winget install --id Microsoft.VisualStudio.2022.Community -e --override "--add Microsoft.VisualStudio.Workload.ManagedDesktop --includeRecommended --passive"
```

```powershell
# VS Code (already installed): required + useful extensions
code --install-extension ms-dotnettools.csdevkit
code --install-extension laktak.hjson
code --install-extension EditorConfig.EditorConfig
```

VS Code hot reload is **off by default**. Add these to your user `settings.json`:

```json
"csharp.experimental.debug.hotReload": true,
"csharp.debug.hotReloadOnSave": true
```

Build from VS Code with `dotnet msbuild`, or `dotnet build`, from the mod folder. Debug with **Run and Debug** (Ctrl+Shift+D) and a mod `.cs` file open. JetBrains Rider is also supported (free for non-commercial use). See the tModLoader wiki page *Developing with Rider*.

**GitHub CLI** (for PRs, issues and Claude's `gh` usage):

```powershell
winget install --id GitHub.cli -e
```

## 5. Art, audio & capture tools

| Tool | Role | Install | Notes |
|---|---|---|---|
| **Aseprite** (recommended) | Main pixel-art and animation editor. Its CLI batch-exports sprite sheets. | Paid: Steam or aseprite.org. Can also be **compiled from source** for free. Not on winget. | Needed by the Aseprite MCP (§7). CLI: `Aseprite.exe -b in.aseprite --sheet out.png --sheet-type vertical` |
| Pixelorama | Free alternative editor | `winget install --id OramaInteractive.Pixelorama -e` | Also: LibreSprite, Piskel (web), GIMP, Paint.NET |
| ffmpeg (optional) | In-game window capture → GIF, only when a simulation isn't enough | `winget install --id Gyan.FFmpeg -e` | Used by `tools/record-gif.ps1` |
| ScreenToGif (optional) | Manual GIF recording and frame editing | `winget install --id NickeManarin.ScreenToGif -e` | Only if someone wants an in-game clip |
| ShareX | Alternative recorder and screenshots | `winget install --id ShareX.ShareX -e` | Optional |
| Audacity | Edit and clean up sound effects | `winget install --id Audacity.Audacity -e` | Export `.ogg` (music) and `.wav`/`.ogg` (sound effects) |
| jsfxr / ChipTone (web) | Prototype sound effects quickly | Browser | Steam hiss, clanks, pistons |
| **TEdit** | Terraria world editor: inspect world generation, build test arenas | `winget install --id TEdit.TEdit -e` | |
| **ilspycmd** | Decompiles `tModLoader.dll` to read vanilla and tModLoader behavior (D0 checks) | `dotnet tool install --global ilspycmd --version 9.1.0.7988` | 9.1 runs on .NET 8. Example: `ilspycmd -t Terraria.Projectile <tML>\tModLoader.dll`. ILSpy GUI (`winget install --id icsharpcode.ILSpy -e`) is optional. |
| TConvert (or another XNB extractor) | Extract vanilla textures **for reference only** | GitHub | Keep extracted files in `reference/` (git-ignored). **Never ship vanilla assets.** |
| Shader tools (later) | Compile `.fx` → `.xnb` | fxcompiler / EasyXnb (shader model 3) | Use `ps_2_0` unless you need SM3. Load **client-side only**. Modders Toolkit has a live Shader Tool. |

## 6. In-game developer mods (Steam Workshop)

Install from tModLoader → *Workshop* → *Download Mods*. They're for development only, so **never add them as `modReferences`**. Check each one's Workshop page to confirm it's updated for the current stable build.

| Mod | Use for |
|---|---|
| **DragonLens** | Admin and dev toolbox: spawn items and NPCs, time and weather, god mode, inspection |
| **Modders Toolkit** | Live editing of textures, dust, projectiles and shaders, plus hitbox visualization. The wiki recommends it for sprite iteration. |
| Cheat Sheet *or* HERO's Mod | Pick **one** if DragonLens is missing something |
| **Recipe Browser** | Check recipes and progression placement |
| **Boss Checklist** | Integration target: Cogpunk registers its bosses with `Mod.Call` (weak, optional) |
| Structure Helper | Save and paste structures for biome world generation. **Decide** whether it becomes a runtime dependency or stays a dev-only tool. |

Vanilla tools for testing: **Journey mode** (god mode, time, spawn rate, difficulty slider), the **Target Dummy**, and the **DPS Meter** accessory (needed for D3).

## 7. Claude Code plugins & MCP servers (efficiency)

| Tool | Type | Why it helps | Install / config | Caveats |
|---|---|---|---|---|
| **`cogpunk-dev` skill + `CLAUDE.md`** | Project skill | Enforces D1–D5, the workflow, API patterns and the Definition of Done | Already in this repo (`.claude/skills/cogpunk-dev/SKILL.md`) | Keep it updated as conventions change |
| **DeepWiki MCP** | Remote MCP (no auth) | Ask questions about the tModLoader source and its wiki without cloning | `claude mcp add -s user -t http deepwiki https://mcp.deepwiki.com/mcp` | It indexes the **default branch (`1.4.5`)**. Confirm answers against the `1.4.4` source before using an API. |
| **csharp-lsp** | Official plugin (`claude-plugins-official`) | Go-to-definition, find references, and type errors right after edits | `/plugin marketplace add anthropics/claude-plugins-official`, then `/plugin install csharp-lsp@claude-plugins-official`, then `dotnet tool install --global csharp-ls` | The latest `csharp-ls` needs the **.NET 10 SDK**. Install it **only after** `global.json` (§8.3) pins builds to 8.0, and check that `dotnet --version` in the repo still prints `8.0.x`. Optional; install after M0. |
| **pixel-mcp** (Aseprite MCP) | Local MCP (Go) | Claude can create and edit `.aseprite` files: palettes, layers, frames, tags, sprite-sheet export | Needs Go 1.23+ (`winget install --id GoLang.Go -e`) and Aseprite 1.3.10+. Clone `github.com/willibrandon/pixel-mcp`, build it (`make build` or the equivalent `go build`), set `aseprite_path` in its `config.json` (see its README for the Windows path), then `claude mcp add -s user pixel-mcp -- C:\tools\pixel-mcp\bin\pixel-mcp.exe` | Alternatives: `diivi/aseprite-mcp` (Python, shading and dithering helpers). Output still has to pass D4 and `check_sprite.py`. |
| **SpriteCook** | Plugin (Anthropic Directory) | AI-generated sprites, tilesets and short animations for **concepts and placeholders** | Install from the claude.ai plugin directory | Generated art **never ships as-is**. It must be redrawn or cleaned up to the 2× grid and palette (D4). |
| Built-in browser / Claude in Chrome | Built in | Look up vanilla stats on terraria.wiki.gg for D3 anchors, and read tModLoader docs | Nothing to install | |

## 8. Scaffolding data

### 8.1 Mod identity

| Field | Value |
|---|---|
| Internal name (`ModName`, folder, `AssemblyName`, root namespace) | **`Cogpunk`**. Keep it **forever**, since renaming breaks saves. Check that it's unique on the Workshop before the first publish (no existing "Cogpunk" mod turned up on 2026-10-20). |
| Display name | `Cogpunk` |
| Author | **TBD** (team or studio name) |
| Version | `0.1.0` at M0. Bump the minor version per milestone and the patch per fix. `1.0.0` at release (M5). tModLoader accepts 2–4 numeric parts. |
| `side` | `Both` (default) |
| Localization | `en-US` (source of truth) + `pt-BR` |
| License / `includeSource` | **TBD.** Decide before the repo goes public. |

### 8.2 Folder tree

```
Cogpunk/                          ← repo root = C:\tML\ModSources\Cogpunk
├─ CogpunkMod.cs                  Mod entry point (thin): Load/Unload, packet dispatch
├─ Cogpunk.csproj · build.txt · description*.txt · icon.png (80²) · icon_small.png (30²)
├─ global.json · .editorconfig · .gitignore · .gitattributes · Properties/launchSettings.json
├─ Core/                          ENGINE: no player-facing content
│  ├─ Networking/                 CogpunkPacket (one class per message), PacketRegistry (crash-safe dispatch)
│  ├─ Safety/                     SafeSpawn, SpawnBudgetSystem, SafeLog, TileSafety, MathSafety   (D0)
│  ├─ Templates/                  CogpunkItem/NPC/Projectile/Tile/Wall/Buff, StateMachineNPC, TextureFallback
│  ├─ Systems/                    WorldFlagSystem (named, saved, synced flags), CrossMod (safe Mod.Call), NPCHaste (area speed buffs)
│  ├─ Events/                     CogpunkInvasion (vanilla-rule invasions), InvasionDirector, InvasionRules, InvasionProgressBar
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

Rules: `Core/` never references `Content/`. A slice never reaches into another slice's internals, and shared code moves to `Core/`. Namespaces mirror folders. See SKILL.md §3.0.

### 8.3 Config file contents

**`build.txt`** (case-sensitive keys; `#` comments out a line):
```
displayName = Cogpunk
author = TBD
version = 0.1.0
hideCode = false
hideResources = false
includeSource = true
buildIgnore = *.csproj, *.user, *.md, *.aseprite, *.ase, global.json, obj\*, bin\*, .vs\*, art\*, docs\*, tools\*, reference\*
```
> `buildIgnore` keeps art sources, GIFs, docs and tools **out of the shipped `.tmod`**. Dot-folders (`.claude`, `.git`, `.vs`), `bin/`, `obj/` and `build.txt` are excluded by default.

**`description.txt`**:
```
Cogpunk: a steampunk overhaul of brass, steam and clockwork.
New Mechanist class, weapons, armor, biomes, enemies and bosses. Built for co-op.
```

**`global.json`** pins builds to the .NET 8 SDK even if 9 or 10 is installed:
```json
{
  "sdk": {
    "version": "8.0.100",
    "rollForward": "latestFeature"
  }
}
```

**`.gitignore`**:
```gitignore
bin/
obj/
*.tmod
.vs/
.idea/
*.user
*.suo
.claude/settings.local.json
reference/
Thumbs.db
Desktop.ini
```

**`.gitattributes`** (GIFs and audio go through LFS; check your git host's LFS quota):
```gitattributes
* text=auto
*.cs       text eol=crlf
*.csproj   text eol=crlf
*.hjson    text eol=crlf
*.png      binary
*.aseprite binary
*.ase      binary
*.xnb      binary
*.gif      filter=lfs diff=lfs merge=lfs -text
*.ogg      filter=lfs diff=lfs merge=lfs -text
*.wav      filter=lfs diff=lfs merge=lfs -text
*.mp3      filter=lfs diff=lfs merge=lfs -text
```

**`.editorconfig`**: copy ExampleMod's verbatim (tabs, width 4, CRLF, tModLoader diagnostic suppressions):
`https://raw.githubusercontent.com/tModLoader/tModLoader/1.4.4/ExampleMod/.editorconfig`

**`Properties/launchSettings.json`**: keep the generated `Terraria` and `TerrariaServer` profiles. Add a quick-start profile that skips the menus straight into the dev world:
```json
"Terraria (CogDev)": {
  "commandName": "Executable",
  "executablePath": "$(DotNetName)",
  "commandLineArgs": "$(tMLPath) -skipselect \"CogDev:CogDev\"",
  "workingDirectory": "$(tMLSteamPath)"
}
```

### 8.4 Sprite specifications (verified against ExampleMod `1.4.4` files)

| Asset | Spec | Evidence |
|---|---|---|
| **Pixel scale** | 1 art pixel = **2×2** texture pixels. Draw at 1×, then resize **200% nearest-neighbor**. Never use `Item.scale` / `NPC.scale` to enlarge art (it creates mixels). | tModLoader *Spriting* wiki. Every 2×2 block of `ExampleSword.png` (40×40) and `ExampleBlock.png` is uniform. |
| Max texture | 2048×2048 exported (1024×1024 at 1×) | Spriting wiki |
| Frame sheets | Vertical, equal frame heights, **2 px** padding between frames (1 art px). Animation frames evenly spaced. | Spriting wiki |
| **Tiles** | 16×16 frames + 2 px gutter = **18 px stride**. A standard terrain sheet is **288×270** (16×15 frames). Start from `ExampleBlock.png`'s layout. | `ExampleBlock.png` / `ExampleOre.png` = 288×270 |
| **Walls** | 32×32 frames, **36 px stride**. Sheet **468×180** (13×5). | `ExampleWall.png` = 468×180 |
| **Armor head / legs** | **40×1120** = 20 frames of 40×56 | `ExampleLeggings_Legs.png` = 40×1120 |
| **Armor body** (1.4 layout) | **360×224** = 9×4 grid of 40×56 | `ExampleBreastplate_Body.png` = 360×224 |
| Town NPC (if ever) | 40×56 frames, 25 frames = 40×1400 | `ExamplePerson.png` |
| Mod icons | `icon.png` 80×80 · `icon_small.png` 30×30 · `icon_workshop.png` ≤512×512 | Basic Modding Guide |
| Orientation | NPCs **face left**. Arrows **point up**. Staffs and swords point **top-right**. Guns point **right**. | Spriting wiki (plus vanilla convention for swords and guns) |
| Glowmask | `<Name>_Glow.png`, same size, only the glowing pixels | Spriting wiki / ExampleMod |
| Transparency | **No semi-transparent pixels** (premultiplied-alpha artifacts). Do fades and glows in code with additive drawing. | Spriting wiki |

### 8.5 Cogpunk master palette (`art/palettes/cogpunk.gpl`)

Ramps run dark → light, with hue shift: shadows go redder or cooler, highlights warmer. Each ramp's index 0 is the **outline** color for that material. Use pure black only for the deepest cast shadows.

```
GIMP Palette
Name: Cogpunk
Columns: 6
#
 43  26  14	Brass 0 #2b1a0e
 90  58  23	Brass 1 #5a3a17
138  93  34	Brass 2 #8a5d22
184 138  51	Brass 3 #b88a33
223 185  78	Brass 4 #dfb94e
246 231 161	Brass 5 #f6e7a1
 42  18  12	Copper 0 #2a120c
 94  40  23	Copper 1 #5e2817
147  68  31	Copper 2 #93441f
196 104  58	Copper 3 #c4683a
233 160 107	Copper 4 #e9a06b
 21  22  28	Iron 0 #15161c
 46  50  59	Iron 1 #2e323b
 79  85  98	Iron 2 #4f5562
127 135 148	Iron 3 #7f8794
183 191 202	Iron 4 #b7bfca
 23  52  48	Verdigris 0 #173430
 42  94  82	Verdigris 1 #2a5e52
 71 145 126	Verdigris 2 #47917e
140 201 176	Verdigris 3 #8cc9b0
 47  27  20	Leather 0 #2f1b14
 91  54  38	Leather 1 #5b3626
138  90  60	Leather 2 #8a5a3c
138 144 150	Steam 0 #8a9096
195 200 205	Steam 1 #c3c8cd
238 241 243	Steam 2 #eef1f3
255 255 255	Steam 3 #ffffff
 77  20  10	Ember 0 #4d140a
163  48  26	Ember 1 #a3301a
236 113  40	Ember 2 #ec7128
255 199  90	Ember 3 #ffc75a
 34  26  69	Aether 0 #221a45
 70  58 147	Aether 1 #463a93
124 107 224	Aether 2 #7c6be0
198 189 255	Aether 3 #c6bdff
```

Soft color caps per sprite: **items ≤ 16**, **enemies ≤ 32**, **bosses ≤ 48**. Adding a color to the palette is a deliberate change: update the `.gpl` and note it in the change report.

### 8.6 Naming conventions

| Thing | Rule | Example |
|---|---|---|
| C# class / file / texture | Same PascalCase name. The namespace mirrors the folder (texture autoloading depends on it). | `Content/Items/Weapons/Mechanist/RivetRepeater.cs` + `.png`, `namespace Cogpunk.Content.Items.Weapons.Mechanist` |
| Equip textures | `_Head`, `_Body`, `_Legs` with `[AutoloadEquip(EquipType.X)]` | `BrassHelmet_Head.png` |
| Extra textures | `_Glow`, `_Flame`, `_Highlight`, `_Head_Boss` (map icon), `_Bestiary` | `Boilerheart_Head_Boss.png` |
| Gores | Inside any `Gores/` folder (autoloaded) | `Content/NPCs/Bosses/Boilerheart/Gores/BoilerheartGore1.png` |
| Localization | tModLoader generates keys automatically: `Mods.Cogpunk.Items.<Name>.DisplayName` / `.Tooltip` | Never hard-code player-facing strings |
| Sounds | `Assets/Sounds/<Category>/<Name>.ogg` via `SoundStyle` | `Assets/Sounds/Weapons/SteamVent` |
| Packets | One `CogpunkPacket` subclass per message, named `<Thing>Packet`, placed in its slice (or `Core/Networking` if shared) | `Content/Mechanist/PressureSyncPacket.cs` |
| Renames after release | Forbidden without `[LegacyName("OldName")]` | Otherwise saved items become "Unloaded" |
| Art sources | `art/<same path as Content>/<Name>.aseprite` | `art/Items/Weapons/Mechanist/RivetRepeater.aseprite` |
| Media (D5) | `docs/media/YYYY-MM-DD_<area>-<feature>[-fix].gif` | `docs/media/2026-11-03_boss-boilerheart-phase2.gif` |

### 8.7 Test worlds, characters & capture settings

| Name | Type | Purpose |
|---|---|---|
| `CogDev` character + `CogDev` world | **Journey**, small, seed `cogpunk` | Fast iteration: god mode, time and spawn control, quick-start profile |
| `CogBal` character (Classic) + worlds `CogBal-Classic`, `CogBal-Expert`, `CogBal-Master` | Medium, seed `cogpunk` | Balance passes (D3) with tier loadouts from `docs/balance/loadouts.md` |
| `CogMP-A` / `CogMP-B` characters | Classic | The two clients in co-op tests (D2) |

> Journey characters can't enter non-Journey worlds, and the reverse is also true. Regenerate the worlds after any world-generation change.

**Optional in-game capture settings** (D5 normally uses frames or simulations, see SKILL D5): windowed **1280×720**, Zoom **100%**, UI scale **100%**, Frame Skip **Off**, Lighting **Color**, daytime unless the feature needs night, a clean hotbar, and the boss bar visible for boss clips.

**Co-op test on one PC:** client 1 picks *Host & Play*. Client 2 starts with a double-click on `start-tModLoader.bat` (in the tModLoader install folder), runs windowed, and joins via IP `localhost`. For server-side code, use the **`TerrariaServer`** launch profile and connect two clients to `localhost`. Unfocused clients update less often, so take that into account when judging jitter.

### 8.8 Balance sheet schema (`docs/balance/`)

`weapons.csv`
```
internal_name,class,archetype,tier,anchor_vanilla,anchor_eff_dps,damage,use_time,knockback,crit,shots_per_use,pierce,eff_dps,delta_pct,tradeoff_note,tested_on
```
`armor.csv`
```
set,tier,anchor_set,head_def,body_def,legs_def,total_def,anchor_total_def,set_bonus,class_bonuses,tested_on
```
`bosses.csv`
```
boss,tier,anchor_boss,life_expert,defense,contact_dmg,proj_dmg,target_ttk_s,ttk_1p_s,ttk_2p_s,ttk_4p_s,modes_tested,tested_on
```
`npcs.csv`
```
npc,biome,tier,anchor_npc,life,defense,contact_dmg,proj_dmg,spawn_chance,banner,tested_on
```
`accessories.csv`
```
accessory,class,tier,source,anchor_vanilla,effects,anchor_effects,value_note,tested_on
```
`events.csv` (invasions and events)
```
event,tier,gate,anchor_event,natural_start,size,roster,miniboss,kill_values,rates,tested_on
```
`hazards.csv` (environmental damage: tar, gas, hot pipes...)
```
hazard,biome,tier,anchor_vanilla,damage,interval_ticks,dps,anchor_dps,effects,linger_ticks,delta_pct,tradeoff_note,tested_on
```
**Every enemy and boss number is the Expert value** (user directive 2026-10-27, SKILL D3 rule 0): life, contact and projectile damage as a player sees them in an Expert world, with Classic and Master in brackets where useful, compared with the anchor's Expert stats. `eff_dps = damage × (60 / use_time) × (1 + crit/100) × shots_per_use`, where base crit is 4%. Write any hit-rate or pierce assumptions in `tradeoff_note`. `delta_pct = (eff_dps / anchor_eff_dps − 1) × 100`.

### 8.9 Tool scripts (`tools/`; create in M0)

Both Python scripts were **tested on 2026-10-20** against ExampleMod sprites with Python 3.14 + Pillow 12.3. Run them as `python -P tools/<script>.py …`.

**`tools/check_sprite.py`** checks D4 for each file and exits 1 on failure:
```python
"""Check sprites against the Cogpunk pixel-art rules (D4). Exit code 1 if any file fails.

Usage: python tools/check_sprite.py PNG [PNG ...] [--palette art/palettes/cogpunk.gpl] [--max-colors 16]
Checks: even size <= 2048, every 2x2 block uniform (no mixels), no semi-transparent pixels,
colour count (warning), and palette membership when --palette is given.
"""
import argparse
import sys
from PIL import Image


def load_gpl(path):
    colors = set()
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            colors.add(tuple(int(p) for p in parts[:3]))
    return colors


def check(path, palette, max_colors):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    errors, warnings = [], []

    if w % 2 or h % 2:
        errors.append(f"size {w}x{h} is not even (art must be exported at 2x)")
    if w > 2048 or h > 2048:
        errors.append(f"size {w}x{h} exceeds 2048x2048")

    mixels = 0
    for y in range(0, h - 1, 2):
        for x in range(0, w - 1, 2):
            if not (px[x, y] == px[x + 1, y] == px[x, y + 1] == px[x + 1, y + 1]):
                mixels += 1
    if mixels:
        errors.append(f"{mixels} 2x2 blocks are not uniform (mixels / 1x detail / wrong offset)")

    opaque, semi = set(), 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 255:
                opaque.add((r, g, b))
            elif a:
                semi += 1
    if semi:
        errors.append(f"{semi} semi-transparent pixels (do transparency/glow in code)")
    if len(opaque) > max_colors:
        warnings.append(f"{len(opaque)} colours (soft cap {max_colors})")
    if palette:
        off = opaque - palette
        if off:
            sample = ", ".join("#%02x%02x%02x" % c for c in sorted(off)[:5])
            errors.append(f"{len(off)} colours not in palette (e.g. {sample})")

    status = "FAIL" if errors else "ok"
    print(f"[{status}] {path} {w}x{h}, {len(opaque)} colours")
    for e in errors:
        print(f"    error: {e}")
    for m in warnings:
        print(f"    warn:  {m}")
    return not errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--palette")
    ap.add_argument("--max-colors", type=int, default=16)
    a = ap.parse_args()
    palette = load_gpl(a.palette) if a.palette else None
    results = [check(f, palette, a.max_colors) for f in a.files]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
```

**`tools/sheet2gif.py`** turns a sprite sheet into a looping preview GIF, plus an optional contact strip:
```python
"""Turn a Terraria sprite sheet into a looping preview GIF (sprite-level visual proof).

Usage: python tools/sheet2gif.py SHEET.png --frames N [--ticks 5] [--scale 2] [--horizontal] [--out PATH] [--contact PNG]
--ticks is game ticks per frame (60 ticks = 1 s), i.e. the same threshold your frameCounter uses.
GIF delays are stored in 10 ms units, so tick values that are multiples of 3 play back exactly.
"""
import argparse
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--ticks", type=int, default=5, help="game ticks per frame (60 per second)")
    ap.add_argument("--scale", type=int, default=2, help="extra nearest-neighbour zoom for viewing")
    ap.add_argument("--bg", default="1e1e24", help="background hex; GIF has no partial alpha")
    ap.add_argument("--horizontal", action="store_true", help="frames laid out left-to-right")
    ap.add_argument("--out")
    ap.add_argument("--contact", help="also write all frames side by side to this PNG (for review)")
    a = ap.parse_args()

    sheet = Image.open(a.sheet).convert("RGBA")
    w, h = sheet.size
    fw, fh = (w // a.frames, h) if a.horizontal else (w, h // a.frames)
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

    frames = []
    for i in range(a.frames):
        box = (i * fw, 0, (i + 1) * fw, fh) if a.horizontal else (0, i * fh, fw, (i + 1) * fh)
        f = Image.new("RGBA", (fw, fh), bg)
        f.alpha_composite(sheet.crop(box))
        if a.scale > 1:
            f = f.resize((fw * a.scale, fh * a.scale), Image.NEAREST)
        frames.append(f.convert("RGB"))

    ms = round(a.ticks * 1000 / 60)
    out = a.out or a.sheet.rsplit(".", 1)[0] + "_preview.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=False)
    if a.contact:
        strip = Image.new("RGB", (frames[0].width * len(frames), frames[0].height))
        for i, f in enumerate(frames):
            strip.paste(f, (i * f.width, 0))
        strip.save(a.contact)
    print(f"{out}: {a.frames} frames of {fw}x{fh}px (x{a.scale}) at {ms} ms/frame")


if __name__ == "__main__":
    main()
```

**`tools/check_tile_seams.py`** enforces the D4 seamless-block rule. It lays out random grids of a sheet's joined frames, compares luminance steps across tile boundaries with steps inside tiles, and measures per-tile edge bias. Exit code 1 means a visible grid.

**Visual proof without the game (default for D5):** use `sheet2gif.py` for sprite animations. For motion and attack patterns, write a small Pillow script in `tools/sim/` that pastes the real sprites onto a background, steps the same constants tick by tick (60 ticks = 1 s), and saves a GIF the same way `sheet2gif.py` does. Then show the result in the response and/or save it to `docs/media/`.

**`tools/record-gif.ps1`** (optional) captures the game window and turns it into a GIF plus a review contact sheet. ⚠ **Untested draft** (needs ffmpeg and the game).
```powershell
<#
.SYNOPSIS  Record the tModLoader window and convert it to a pixel-art-safe GIF (Directive D5).
.EXAMPLE   powershell -ExecutionPolicy Bypass -File tools/record-gif.ps1 -Name boss-boilerheart-phase2 -Seconds 8 -Crop "640:360:320:180"
#>
param(
    [Parameter(Mandatory = $true)][string]$Name,   # <area>-<feature>[-fix], kebab-case
    [int]$Seconds = 8,                              # keep <= 10
    [ValidateSet(25, 50)][int]$Fps = 25,            # GIF delays are 10 ms units: 25/50 fps play back exactly
    [string]$Crop = "",                             # ffmpeg crop "w:h:x:y" (prefer cropping over scaling)
    [int]$Countdown = 3,
    [string]$OutDir = "docs/media"
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "ffmpeg not found: winget install --id Gyan.FFmpeg -e" }

$window = Get-Process | Where-Object { $_.MainWindowTitle -match '^(Terraria|tModLoader)' } | Select-Object -First 1
if (-not $window) { throw "tModLoader window not found. Start the game windowed at 1280x720 first." }
$title = $window.MainWindowTitle

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$gif   = Join-Path $OutDir ("{0}_{1}.gif" -f (Get-Date -Format "yyyy-MM-dd"), $Name)
$raw   = Join-Path $env:TEMP "cogpunk_capture.mkv"
$sheet = Join-Path $env:TEMP ("cogpunk_{0}_sheet.png" -f $Name)

Write-Host "Capturing '$title' for $Seconds s, starting in $Countdown s..."
Start-Sleep -Seconds $Countdown
& ffmpeg -hide_banner -loglevel error -y -f gdigrab -framerate 50 -draw_mouse 0 -i "title=$title" -t $Seconds -c:v ffv1 $raw

$vf = "fps=$Fps"
if ($Crop) { $vf += ",crop=$Crop" }
$vf += ",split[a][b];[a]palettegen=max_colors=256:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle"
& ffmpeg -hide_banner -loglevel error -y -i $raw -vf $vf -loop 0 $gif

# 12 evenly spaced frames for self-review (not committed)
$step = [Math]::Max(1, [Math]::Ceiling($Seconds * $Fps / 12))
& ffmpeg -hide_banner -loglevel error -y -i $gif -vf "select='not(mod(n\,$step))',scale=480:-1:flags=neighbor,tile=4x3" -frames:v 1 $sheet

$sizeMB = [Math]::Round((Get-Item $gif).Length / 1MB, 2)
Write-Host "GIF:   $gif ($sizeMB MB)"
Write-Host "Sheet: $sheet"
if ($sizeMB -gt 10) { Write-Warning "GIF is over 10 MB: shorten -Seconds or add -Crop." }
Remove-Item $raw -ErrorAction SilentlyContinue
```

## 9. Scaffolding procedure (M0)

**Progress (2026-10-20):**
- **Done:** steps 4–7 (the repo exists at `C:\tML\ModSources\Cogpunk`; the `Core/` framework compiles against the reference build with 0 warnings and 0 errors), 10 (`check_sprite.py` passes on the icons and placeholder) and the git init.
- **Still open:**
  - Steps 1–3: install Steam and tModLoader, write `cli-argsConfig.txt`. Skip *Create Mod*, since the project files already exist.
  - Step 8: test worlds.
  - Step 9: the in-game and co-op smoke test.
  - Step 11.
  - The first commit.

1. **Install** everything in §4 and §5. At minimum: Steam, tModLoader, an IDE, ffmpeg and an art editor.
2. **Move the data folder** (§3): create `C:\tML`, write `cli-argsConfig.txt`, and launch tModLoader once. Then check that `C:\tML\ModSources\tModLoader.targets` exists.
3. **Generate the skeleton in-game:** *Workshop → Develop Mods → Create Mod*. Use ModName `Cogpunk`, Display Name `Cogpunk`, Author TBD. If the form requires a sample item name, use `DebugBlade` and delete it after the first build.
4. **Move these docs** (`README.md`, `SETUP.md`, `CLAUDE.md`, `.claude/`) from `…\OneDrive\Documentos\GitHub\Cogpunk` into `C:\tML\ModSources\Cogpunk`.
5. **Initialize git:** run `git init`, `git lfs install`, then add `.gitignore`, `.gitattributes`, `global.json`, ExampleMod's `.editorconfig`, and the `build.txt` / `description.txt` from §8.3.
6. **Create the folder tree** (§8.2), the empty `pt-BR_Mods.Cogpunk.hjson`, `art/palettes/cogpunk.gpl` (§8.5), the `docs/balance/*.csv` headers (§8.8), and the `tools/` scripts (§8.9).
7. **Build:** run `dotnet build` in the repo, which must finish with zero errors and zero warnings. Then use *Build + Reload* in-game.
8. **Create the test characters and worlds** (§8.7) and add the `Terraria (CogDev)` launch profile.
9. **Co-op smoke test:** host and play with one client plus a second client via `start-tModLoader.bat` → `localhost`. Then do the same on the `TerrariaServer` profile.
10. **Validate the tools:** run `check_sprite.py` on `icon.png` and `sheet2gif.py` on a test sheet. `record-gif.ps1` is optional.
11. **Claude tooling:** add DeepWiki MCP. Optionally add csharp-lsp, pixel-mcp and SpriteCook (§7).
12. **First commit**, then push to the remote.

**M0 is done when:** the build is clean, the mod loads in singleplayer and in host-plus-client, all three tools work, the test worlds exist, and the docs are in the repo.

## 10. Maintenance

- **Monthly tModLoader stable (the 1st of each month):** rebuild, read the release notes and the *Update Migration Guide*, run the singleplayer and co-op smoke tests, and fix any breaking changes before doing feature work.
- **1.4.5:** watch the tModLoader GitHub issue *"1.4.5 Update Information"* and the Steam news. When tModLoader 1.4.5 goes **stable**, start M6: tModPorter, then `MigrationGuide_1.4.5.md`, then the full regression test.

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| tModLoader can't find the .NET SDK | Install the **x64** .NET 8 SDK. If it ended up under `Program Files (x86)`, it's 32-bit, so reinstall. Restart the PC. |
| Build uses the wrong SDK after installing .NET 10 | Make sure `global.json` is present. `dotnet --version` in the repo must print `8.0.x`. |
| `project.assets.json not found` | `dotnet restore`, then build again |
| `Cogpunk.tmod` *in use by another process* | Disable the mod and reload, or close tModLoader before building outside the game |
| Missing texture exception | Class name, file name, namespace and folder don't match (§8.6) |
| Build fails with *tModLoader.targets not found* | Launch tModLoader once (it writes `C:\tML\ModSources\tModLoader.targets`), or keep the reference one pointing at `C:\tML\_reference\…\tMLMod.targets` |
| "Cloud file provider is not running" or folder creation errors | The data folder is in OneDrive. Apply §3. |
| Can't join locally | Mod set or version mismatch, or port 7777 in use or blocked |
| Blurry or "double-size" pixels | Art isn't on the 2× grid, or `scale` was used. Run `check_sprite.py`. |
| Dark fringes on translucent pixels | Premultiplied alpha. Remove the semi-transparent pixels and fade in code instead. |

## 12. Sources

- tModLoader releases: <https://github.com/tModLoader/tModLoader/releases>
- tModLoader 1.4.5 update info (issue #5070): <https://github.com/tModLoader/tModLoader/issues/5070>
- tModLoader October 2026 Stable Update: <https://steamcommunity.com/games/1281930/announcements/detail/719043624313028698>
- Guide for developers (.NET 8, VS 17.8+): <https://github.com/tModLoader/tModLoader/wiki/tModLoader-guide-for-developers>
- Basic Modding Guide (ModSources, Create Mod, icons): <https://github.com/tModLoader/tModLoader/wiki/Basic-tModLoader-Modding-Guide>
- Developing with VS Code (hot reload): <https://github.com/tModLoader/tModLoader/wiki/Developing-with-Visual-Studio-Code>
- build.txt reference: <https://github.com/tModLoader/tModLoader/wiki/build.txt>
- Command line (`-tmlsavedirectory`, `-skipselect`, `cli-argsConfig.txt`): <https://github.com/tModLoader/tModLoader/wiki/Command-Line>
- Basic Netcode (multiplayer testing): <https://github.com/tModLoader/tModLoader/wiki/Basic-Netcode>
- Spriting (2×2 art, padding, orientation): <https://github.com/tModLoader/tModLoader/wiki/Spriting>
- Expert Shader Guide: <https://github.com/tModLoader/tModLoader/wiki/Expert-Shader-Guide>
- ExampleMod 1.4.4: <https://github.com/tModLoader/tModLoader/tree/1.4.4/ExampleMod>
- OneDrive + tModLoader reports: <https://steamcommunity.com/app/1281930/discussions/0/595136186401444586>, <https://steamcommunity.com/workshop/filedetails/discussion/2939737748/4366878398990366358>
- DeepWiki MCP: <https://docs.devin.ai/work-with-devin/deepwiki-mcp>
- csharp-lsp plugin / csharp-ls: <https://github.com/anthropics/claude-plugins-official>, <https://github.com/razzmatazz/csharp-language-server>
- pixel-mcp (Aseprite MCP): <https://github.com/willibrandon/pixel-mcp> · diivi/aseprite-mcp: <https://github.com/diivi/aseprite-mcp>
