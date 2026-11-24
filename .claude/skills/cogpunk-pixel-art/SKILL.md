---
name: cogpunk-pixel-art
description: Mandatory method and quality bar for every Cogpunk sprite, animation and visual effect (tModLoader pixel art) - bosses, mobs, pets, weapons, items, tiles, projectiles, glow, trails, smoke and particles. Use it before drawing, redrawing, animating or reviewing any Cogpunk art or art generator (art/**/*.py), together with the cogpunk-dev skill.
---

# Cogpunk pixel art: method and quality bar

Made from the 2026-11-23 study (`docs/design/sprite-quality-study.md`: vanilla, Calamity, Thorium and Lunar Veil measured)
and the vanilla study of 2026-11-05 (`docs/design/pixel-art-study.md`). It extends D4 in the cogpunk-dev skill (rules 13-22);
when they disagree, D0 and the user's explicit words win.

You are not a painter: you write code that places pixels. Sprites drawn "from imagination" with a few big shapes come out flat
and cheap (the Fungimancer v1: edge density 0.36, patches of 8 px). Work from structure, measure, and look at every step.

## 1. Before drawing

1. **Know the subject.** A complex subject (a creature, a character, a boss, a pet) starts from the user's reference image or
   a written list of its parts. Someone else's artwork (a painting, a card, another game) is used for pose, proportions and
   colours only, never traced pixel for pixel; say so once if the user's reference looks like that. The user's own pixel art is
   the source sprite (memory: use the user's own art).
2. **Look for an earlier approved version** (`art/**/previous/`, the user's picks in memory) and match it unless asked
   otherwise. Copy the generator aside before redrawing (keep previous designs).
3. **Pick the size from the role**, in art pixels (1x): items 12-24, weapons 16-40, mobs 20-48 tall, pets 16-30, bosses 50-120.
   Bigger is not better: a bigger sprite needs proportionally more structure.
4. **Write down the structure that shows at that size**: for each part, its material (ramp), its form (round or flat), the
   features it carries (eyes, warts, seams, folds, rivets), the light (top-left), what it overlaps.

## 2. Drawing (in the generator)

- **The 2x rule.** Draw at 1x, export 2x nearest-neighbour (`export`). Never 1x detail on a sprite, never a non-integer scale.
- **Ramps.** Only the Cogpunk palette (`art/palettes/cogpunk.gpl`, `rig.RAMP`); a new ramp is added to both and reported.
  Ramps shift hue: darker steps cooler (towards blue or purple), lighter steps warmer (towards yellow), saturation highest in
  the middle, the light end of a mid-tone material well short of white. Check a new ramp the way the study did.
- **Use the ramp.** Each material spans at least 4 steps of its ramp across the sprite: a core shadow, mid tones, a light side,
  a small highlight. If one colour covers more than half of a material, widen the range. Highlights are small and at the
  source of the light.
- **Round or flat.** Round forms (bodies, heads, gems, barrels, mushrooms' caps) are lit from one light. Flat, thin things
  (membranes, cloth, leaves, pages, wings) are not dome-lit: their tones come from their pattern, folds and the shadows of what
  lies on them.
- **Bands and dither.** Shade in flat bands; dither only in a narrow strip where two bands meet (`level(..., dither=)`), never
  over a whole area. No smooth gradients with many colours.
- **Texture with a reason.** Every tone patch comes from something you can name: the form, a fold, a seam, a vein, a wart, a
  fur tuft, a cast shadow, a highlight. Details move the colour by one fixed ramp step. Noise only on parts over 16 px, as a
  wide soft variation, never per-pixel grain. Texture lives in the part's own space so it doesn't crawl when the part moves
  (D4 rule 17).
- **Lines.** One-pixel lines (seams, cracks, veins, hair) are pixel-perfect (no L corners) and one fixed colour, one ramp step
  darker than what is around them.
- **Shapes.** Build round shapes from round parts; repeated parts (fingers, petals, spines) vary a little in size and angle and
  read as separate (a gap or a dark crease); thin parts keep one width and taper only at the tip; joined parts touch.
- **Silhouette.** No 1 px bumps, 2 px nubs, 1 px holes or 1 px strips. Thin pixels (one-pixel limbs) at most 3%.
- **Faces and small features.** Eyes, mouths, gems, rivets: placed by hand at the target size after `finish()` (which would
  erase lone pixels), big enough to read: an eye of a boss is 3+ px with a pupil and a glint.
- **Outline.** Selective outline from the sprite's own ramps: a mid step on the lit side, the darkest on the far side; never
  black (vanilla never uses black; Lunar Veil's black outlines are a different style we don't follow). A rim light one step
  lighter on edges facing the light. `westbots.finish` does the selout.
- **Depth.** Detailed entities: up to three planes (far, middle, near, D4 rule 13), the far plane one or two steps darker,
  parts that overlap cast a one-pixel shadow on what is behind them.

### Complex creatures: model, then pixelate (codixel's method)

For organic subjects (creatures, faces, fur, scales), coarse shapes at 1x come out flat. Instead:

1. Model the subject at **4x the art size** with smooth shapes and per-part shading (still one light, still the ramps).
2. **Pose it with bones** at that size (parts turn about their joints; each part keeps its own texture space).
3. **Pixelate each frame** to the art size per part: the most common colour of each 4x4 cell (mode, never an average), the
   part's own ramp only, so colours never mix across a part boundary.
4. **Clean up** each part: remove stray pixels (but keep eyes and highlights), smooth the silhouette, then stamp the small
   features by hand and finish with the selective outline.
5. Use **one fixed palette for every frame**, so a frame never gains or loses a colour.

The renderer for this is `art/templates/sculpt.py` (`Part`, `Ell`, `Tube`, `Poly`, `Frame`, `render`): parts with real
normals sampled 4 x 4 per art pixel, pixelated per part by majority, banded with edge-only dither, warts and details that
step one ramp step (`bumps`, `bump_step`), spots, pixel-perfect fold lines, selective outline, rim light and cast shadows.
Worked examples (2026-11-23): `art/bosses/fungimancer/make_fungimancer_art.py`, `art/bosses/jadey/jadey_sculpt.py` (a new
body under an existing rig and frame list), `art/coghaven/make_jade_fox_art.py`. Lessons from those redesigns:
- Soft face parts (muzzles, eye patches, cheeks, noses) get **no outline**: an outline ring round them turns a face into a mask.
- Flat shapes (`Poly`: ears, tufts, fringes) get **no dither**: a constant normal sits inside a dither strip and becomes a
  checkerboard.
- A pale material (white fur) uses its ramp's upper half (`lo` 3+): dark bands and dither on it read as dirt.
- Texture must step by a fixed ramp step to show (`bump_step`); bending the normal alone barely moves a band edge.
- A seat or a base the subject rests on must show its form: lift the subject onto it rather than sinking into it.

## 3. Animation

- **Timing.** Ease in and out, never linear. Anticipation before a big move, follow-through after it (tails, ears, frills,
  cloth lag a frame or two). Rotating parts move at most about 25 degrees a frame; add in-betweens when a pose jumps further.
- **Budget.** "4 great frames beat 12 mediocre ones": idle 4-6, walk or trot 6-8, wing beat 5-10, attack 4-8 (wind-up,
  strike, hold, recover). Vanilla's Demon: 5 frames of 5 ticks a wing beat.
- **Loops are seamless.** Put the last frame next to the first on the proof sheet; the step between them is one more frame.
- **Small motion stays small**: breathing is a pixel, a sway a pixel or two at the tip, never the whole sprite jittering.
- **Stable pixels** (D4 rule 17): a part's colours stay on the part; `tools/check_flicker.py` for generated animations.

## 4. Effects (glow, bloom, trails, smoke, particles)

- **Glow and bloom**: a glow layer (the sprite's lit parts) drawn full-bright, or a soft 1x gradient texture, opaque on black,
  drawn additively (black adds nothing). No semi-transparent pixels except for a translucent material (jelly, glass), and
  only on it.
- **Smoke and fire** are built, not drawn: a value per pixel (the shape of the thing times noise moving the way the material
  moves), cut at a threshold, coloured in flat bands with dither strips; the brightest part small, at the source; smoke grows
  wider, curls and thins as it rises, and fades by its whole puff, never by semi-transparent pixels in the sprite.
- **Trails**: vertex strips (vanilla 1.4.4 `Terraria.Graphics.VertexStrip`), or a short chain of the sprite's own fading
  copies (the smear, D4 rule 10). Width and colour fall off along the trail.
- **On the grid**: soft curves (trails, smoke, rings) are drawn into a half-size render target and back at 2x with point
  sampling (Calamity's `PrimitivePixelationSystem`), so they sit on the sprites' 2x2 grid.
- **Cost** (D1): pool particles (fixed capacity, no allocation per tick), batch them by blend state (one Begin/End per blend
  group), cap them per entity, clients only.

## 5. Checks (all of them, every time)

1. `python -P tools/check_sprite.py <png...>` (the palette, no mixels, no semi-transparent pixels, the colour cap).
2. `python -P tools/check_detail.py <RigData.cs> <layer base> --frames ...` for detailed entities, and `--png` for a single
   frame. Target band (the study): edge density at least 0.55 (aim 0.60-0.75), patches at most 3.5 px (aim 2-3), neighbour
   dL* 16-30, interior L* 30-60, 20-45 colours (bosses up to 60), thin at most 3%, no black outline.
3. `python -P tools/check_flicker.py` for animations.
4. **Look at it**: a frame sheet at 4x over dark and light backgrounds, the frames numbered, the last next to the first, and
   the reference beside it. Fix one thing at a time.
5. **Proof** (D5): the GIF and the sheet to the user before calling it done; delete proofs of the outdated version.
