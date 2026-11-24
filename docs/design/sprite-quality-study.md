# Sprite quality study: vanilla, Calamity, Thorium, Lunar Veil and ours (2026-11-23)

The user's request (2026-11-23): "lets stop a bit the implementations to tackle our most impactfull problem or the mod right now:
sprite quality and animation". They pointed at three resources (the MagicPixel.art MCP, Skillselion's pixel-art skills guide and
the codixel skill), asked to verify their note on Terraria's 2x2 pixel rule ("Mods like calamity sometimes uses details made in
1x1 instead of 2x2"), to analyse how famous mods' sprites are made (Calamity, Lunar Veil, Thorium) including particles, trails,
smoke and glow, to save the results as a rule, and to redesign the weakest sprites (Jadey, the jade fox, the Fungimancer).

This page extends `docs/design/pixel-art-study.md` (vanilla's NPCs, 2026-11-05). The rule that comes out of it is the
`cogpunk-pixel-art` skill (`.claude/skills/cogpunk-pixel-art/SKILL.md`) and D4 rules 19-22 in the cogpunk-dev skill.

## 1. Sources and method

- **Sprites measured in the browser, nothing saved.** Each image was read into a canvas straight from where it is published:
  Calamity's public repository (`CalamityTeam/CalamityModPublic`, branch 1.4.4, 9205 PNGs), Thorium's wiki
  (thoriummod.wiki.gg) and the Terraria Mods wiki (terrariamods.wiki.gg) for Lunar Veil. Thorium and Lunar Veil aren't open
  source; their wiki files are the game sprites. A few wiki files were resized thumbnails (not doubled, hundreds of colours) and
  were dropped. **No sprite was copied into this repository.**
- **The same metrics as `tools/check_detail.py`**, at art-pixel resolution, plus three new ones: the share of 2x2 blocks that
  are one colour (`doubled`: 1.00 means a strict 2x export), the share of semi-transparent pixels, and the hue shift of each
  ramp from its dark third to its light third.
- **The three resources:**
  - *codixel* (github.com/mankidev/codixel, MIT): a Claude Code skill. Its method is adopted in the skill (section 6). It was
    read, not installed: its scripts were not run here.
  - *Skillselion's guide*: points at other skills (omer-metin `pixel-art-sprites`, `pixel-art`; the Aseprite `pixel-plugin`).
    Their rules overlap codixel's: integer scaling, a locked palette, frame budgets ("4 great frames > 12 mediocre"), selective
    outlines, hue shifting, no anti-aliasing against one background.
  - *MagicPixel.art*: a commercial AI pixel-art generator and editor with its own MCP server. It needs an account and an API
    key, and it isn't in the connector directory. Setting it up is the user's choice; prompts and images would go to their
    service.

## 2. The 2x2 rule, verified

The user's note is right. Every solid sprite is drawn at 1x and exported at 2x nearest-neighbour, in vanilla and in all three
mods. The "1x1 details" are real but live only in **effect textures**.

| set | sampled | strict 2x | not doubled | semi-transparent |
|---|---|---|---|---|
| Calamity boss NPC sheets | 24 | 22 | 2 (Boss Checklist portraits, not game art) | 2 slightly |
| Calamity items (weapons) | 24 | 24 | 0 | 0 |
| Calamity projectiles | 24 | 24 | 0 | 0 |
| Calamity tiles | 24 | 24 | 0 | 1 |
| Calamity UI | 24 | 23 | 1 | 1 |
| **Calamity particles** | 24 | 7 | **17** | 3 |
| **Calamity dusts** | 24 | 6 | **18** | 0 |
| Thorium bosses and items | 14 | 14 | 0 | 2 (jelly: 50% of their pixels) |
| Lunar Veil bosses and items (real sprites) | 9 | 9 | 0 | 0 |

- **Effect textures are full resolution and soft**, but almost never semi-transparent. Calamity's bloom set (BloomCircle,
  BloomLine, BloomRing...) is opaque gradients on black, 200 to 2300 colours, drawn with additive blending: black adds nothing,
  brightness is the glow, and the draw colour tints it. Our glow sheets already work this way.
- **Translucent materials** (Thorium's Queen Jellyfish and Jelly Pond Wand) use semi-transparent pixels on purpose, on the
  material only. That is a deliberate exception, not the norm.
- **Rule kept:** sprites strictly 2x (D4). Effect textures may be 1x gradients on black, drawn additively (rule 21).

## 3. The numbers

Medians, at art-pixel resolution (first frame).

| set | colours | interior L* | edge density | patch (px) | neighbour dL* | outline | hue shift |
|---|---|---|---|---|---|---|---|
| vanilla NPCs (38, 2026-11-05) | 22 (15-25) | 40 | 0.73 | 1.9 | 26 | coloured, never black | +10 to +15 (warm) |
| Calamity bosses (12) | 18 (12-41) | 40 (13-58) | 0.55 (0.40-0.70) | 3.5 (2.1-5.2) | 16 (12-24) | mostly coloured; dark themes near black | +-20-30 on the main ramps |
| Thorium bosses (6) | 23 (13-69) | 51 (19-72) | 0.70 (0.63-0.83) | 1.9 (1.5-2.4) | 25 (18-33) | coloured (black only on dark creatures) | 0 to +-28 |
| Thorium items (8) | 17 | 55 | 0.79 | 1.4 | 27 | coloured | small |
| Lunar Veil bosses (5) | 38 (14-114) | 35 | 0.56 | 3.3 | 24 (19-39) | **black** (0.6-1.0 of the edge) | +-6 to +-36 |
| **Fungimancer (ours, v1)** | 33 | 47 | **0.36** | **7.9** | 30 | coloured | ramps fine, little used |
| **Jadey (ours)** | 35 | 43 | 0.50 | 4.3 | 26 | coloured | |
| **jade fox (ours)** | **13** | **75** | 0.60 | 2.7 | 32 | coloured | |

What the numbers say:

- **Big sprites trade density for smoothness.** Calamity's bosses (100-350 art px wide) have bigger patches (3.5) and smaller
  steps (dL* 16) than vanilla's NPCs: long ramps that turn the form slowly. Thorium keeps vanilla's density even on bosses
  (edge 0.70, patch 1.9) and is brighter. Lunar Veil spends colours (38-114) and contrast, with black outlines: a deliberate,
  different style.
- **Ours fail on density, not on palette.** The Fungimancer is half as busy as any reference (edge 0.36, patches of 8 px):
  big flat shapes, which is why it reads as cheap. Jadey is short of Calamity's band. The fox has too few colours, too light a
  body and big jumps between neighbours.
- **Our ramps already shift hue** the right way (warm ramps +13 to +34 degrees towards yellow as they lighten, greens and teals
  towards yellow-green). The failure is using two or three steps of a seven-step ramp per material.

## 4. How the mods build effects (Calamity's source)

- **Pixelated primitives** (`Graphics/Primitives/PrimitivePixelationSystem.cs`): trails and particles flagged `Pixelate` are
  drawn into render targets at **half the screen's size** (one per draw layer: before tiles, before and after NPCs and
  projectiles, after players, dusts, everything), then drawn back up at 2x with point sampling. Smooth curves come out on the
  2x2 grid, the same pixel size as every sprite. This is how soft effects avoid "mixels".
- **Trails as vertex strips** (`PrimitiveRenderer.cs`): positions, tangents, normals, vertices and indices in arrays allocated
  once, a `DynamicVertexBuffer`, width and colour as functions of the point's place along the trail, a shader for the texture.
  Vanilla 1.4.4 has the same building block (`Terraria.Graphics.VertexStrip` with `MiscShaderData`).
- **Particles** (`Particles/GeneralParticleHandler.cs`, after Spirit's and Luminance's managers): typed particles with a
  lifetime and a sheet frame, light-affected or not, drawn batched by blend state (alpha-blended in one batch, additive in
  another), optionally pixelated.
- **Glow**: soft bloom textures (opaque gradients on black) drawn additively under or over glowing parts at low opacity.
- **Metaballs** (`Graphics/Metaballs/MetaballManager.cs`): blobs drawn into a render target, then thresholded and outlined by
  a shader: one smooth body for smoke, goo and fluid instead of many overlapping sprites. Skipped when none are alive; GPU
  targets freed on unload.

Lessons for us (rule 21): batch effects by blend state, never Begin/End per particle; pool them (fixed capacity, no
allocation per tick); draw glow as additive gradients; for curved trails and smoke, prefer a pixelated pass (half-size target,
point-sampled 2x) over many small soft sprites.

## 5. Where ours go wrong (and what the redesigns change)

1. **Flat colour fields.** Bodies are one or two shades over large areas. Model the form with the whole ramp (dark core
   shadow, mid, light, a small highlight), in bands with a dither strip at the band edges only.
2. **No surface.** Skin, fur and cloth have no texture, so big parts read as plastic. Add structure that has a reason (warts,
   folds, fur tufts, seams, scales), one ramp step from the surface, sized to the part.
3. **Small, stiff parts.** Frills as straight sticks, thin arms. Give parts mass and a curve, constant width, taper at the tip.
4. **Faces too small.** Eyes, mouths and expressions drawn at the target size by hand (vanilla's rule), big enough to read.
5. **Animation by part rotation of coarse shapes.** The codixel method: build the character at a higher resolution, pose it
   with bones, and pixelate each frame with one fixed palette, so frames stay consistent and joints don't tear. Our generators
   already draw each pose from shapes (never a rotated bitmap); the redesign raises the sample density instead.

## 6. Method adopted (from codixel and saint11's tutorials)

The full checklist is the `cogpunk-pixel-art` skill. In short:

- **Reference first.** A complex subject starts from the user's image or a written description of its parts. Someone else's
  artwork is used for pose and colours only.
- **Ramps.** Dark steps cooler, light steps warmer, saturation highest in the middle; the highlight end of a mid-tone object
  stays away from white. Use most of the ramp across each material; if one colour covers more than half of a material, widen
  the range.
- **Shading.** Round forms are lit from one light (top-left). Flat, thin things (membranes, cloth, leaves, pages) take their
  tones from their pattern and folds, not from a dome. Flat bands with a dither strip only where two bands meet. Noise only on
  parts over 16 px, as a wide variation, never as per-pixel grain.
- **Order.** Every tone patch has a reason you can name (form, fold, seam, cast shadow, highlight).
- **Lines.** One-pixel lines are pixel-perfect (no L corners) and one fixed colour, one ramp step darker than the area around
  them.
- **Silhouette.** No 1 px bumps, 2 px nubs, 1 px holes or 1 px strips. Thin parts keep one width.
- **Outline.** Selective outline from the sprite's own ramps: the lit side a mid step, the far side the darkest; a rim light
  one step lighter on the edges that face the light.
- **Animation.** Ease in and out, never linear. Anticipation before big moves, follow-through after them. Keep in-betweens
  under about 25 degrees a frame for rotating parts. Loops are seamless (check the last frame next to the first). Small motion
  stays small. Texture lives in part space (D4 rule 17).
- **Proof.** A frame sheet and a GIF, checked frame by frame, and metrics inside the target band, before any game file is
  final.

## 7. The redesigns (2026-11-23)

Drawn with `art/templates/sculpt.py` (section 6's method); earlier versions kept in each folder's `previous/`.

| sprite | before | after |
|---|---|---|
| Fungimancer | 33 colours, edge 0.36, patches 7.9 px | 38 colours, edge 0.50, patches 3.7 px (inside Calamity's boss range); new `frog` and `belly` hue-shifted ramps |
| Jadey | 35 colours, edge 0.50, patches 4.3 px | 34 colours, edge 0.64, patches 2.6 px |
| jade fox | 13 colours, L* 75, dL* 32 | 18 colours, edge 0.61, patches 2.4 px, dL* 30 |

Proofs: `docs/media/2026-11-23_boss-fungimancer-*`, `2026-11-23_boss-jadey-*`, `2026-11-23_pet-jade-fox*`.
