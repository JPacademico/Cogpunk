# Pixel-art study: vanilla Terraria's NPCs and ours (2026-11-05)

The user's request (2026-11-05): "most of the recent enemies (except Beat-Boxer, Cogshark and Coghawk) are not matching the necessary pixel art detail quality (Metal Slug level), so first analyse Terraria NPC sprite quality and compare, then save the technical results that could improve your pixel art design quality in comparison with the techniques used by default Terraria."

This page records what was measured and the rules that came out of it. It is the reference for D4 rule 18 (SKILL.md) and for `tools/check_detail.py`.

## 1. Method

- **Vanilla:** 38 single frames of vanilla NPCs, taken from terraria.wiki.gg's NPC images for study only and **not copied into this repository**. They cover humanoids with guns and hats (Pirate Deckhand, Corsair, Crossbower, Captain and Deadeye, Skeleton Commando and Sniper, Tactical Skeleton, Martian Officer, Ray Gunner, Gigazapper, Arms Dealer, Steampunker, Cyborg, Mechanic, Tax Collector, Goblins), armor (Possessed Armor, Armored Skeleton, Paladin, Rusty Armored Bones), machines and beasts (Granite Golem, Martian Walker, Scutlix, Unicorn, Hellhound, Werewolf, Mimic, Mothron) and a boss (Deerclops).
- **Ours:** the first frame of our enemies, with the far, middle, near and glow planes composited. The user approved three of them: the Beat-Boxer, Cogshark (now Cogtuna) and Coghawk. The user rejected the other five: the Brass Bandit, Sheriff, Mechanical Bull, Dinamitrom and Splasher.
- **Grid:** every frame was measured at art-pixel resolution, after undoing the 2x export.
- **What was measured:**
  - Size, colours, fill, and the share of thin (one-pixel) pixels.
  - Lightness (CIE L*): the median, the interior, and the outline.
  - Edge density: how often two neighbouring pixels differ in colour.
  - Cluster mean: the average size of a same-colour patch.
  - Neighbour contrast: the mean L* step between neighbours that differ.
  - Orphan ratio: interior pixels that match none of their 8 neighbours.
  - Ramps: shades per hue family, and the hue shift from dark to light.

## 2. Results

| metric | vanilla p25 | vanilla median | vanilla p75 | approved (3) | rejected (5) |
|---|---|---|---|---|---|
| colours | 15 | 22 | 25 (richest 39-50) | 14-17 | 13-19 |
| interior L* | 33 | 40 | 49 | 38-43 | **21-40** (Bandit 21, Sheriff 29) |
| median L* | 21 | 27 | 40 | 11-36 | **12-36** (Bandit/Sheriff 12) |
| edge density | 0.68 | 0.73 | 0.76 | 0.42-0.47 | 0.37-0.50 |
| cluster mean (px) | 1.7 | 1.9 | 2.2 | 5.1-7.1 | 4.3-7.5 |
| neighbour dL* | 23 | 26 | 28 | 33-44 | 27-38 |
| thin pixels | 0.4% | 0.8% | 1.3% | 0.2-2.4% | **1.1-6.7%** (Bandit 6.7%, Sheriff 6.0%) |
| fill | 0.56 | 0.63 | 0.70 | 0.39-0.57 | 0.40-0.66 |
| outline black | 0 | 0 | 0 | 0 | 0 |
| shades per ramp (3+) | 4 | 6 | 7 (up to 16) | 5-7 | 2-9 |
| orphan ratio | 0.12 | 0.19 | 0.21 | 0.01-0.03 | 0.01-0.07 |

Warm ramps shift about +10 to +15 degrees of hue toward yellow from dark to light. Greys stay neutral or cool.

## 3. What vanilla does

1. **Chibi proportions.** A humanoid is about 21-25 art px tall, and the head with its hat takes 40-50% of that. Legs are short, and weapons are big and chunky (the Skeleton Commando's rocket launcher is as big as its torso). Limbs are 2-3 art px thick. Under 2% of pixels are one-pixel-wide parts.
2. **Long material ramps in small steps.** The median ramp has 6 shades, and the richest have up to 16. Each step is about 8-14 L*. Warm materials shift toward yellow as they brighten, and cool greys stay neutral.
3. **Coloured outlines.** An outline is the darkest shade of the material it bounds, never pure black: its L* averages 15, against an interior of 40. The lit top-left side is often a step lighter (selective outlining).
4. **Dense, small-step detail.** About 3 in 4 neighbouring pixels differ, but by only one shade (a mean of about 26 L*), so forms look modelled, not posterised. Same-colour patches average about 2 px.
5. **Low-contrast single pixels as texture.** 12-21% of interior pixels match no neighbour. These are not noise: each is one shade off its surroundings, and together they read as cloth, leather and metal grain.
6. **Mid-value bodies.** The interior averages L* 40, so a sprite reads on both cavern and sky backgrounds. Dark sprites (wraiths, shadows) are the exception.
7. **Colour counts.** Most use 15-25 colours. The most detailed townsfolk and pirates use 39-50 (Pirate Captain 48, Steampunker 49, Mechanic 50).

## 4. What failed in ours

- **The cowboys** (Bandit, Sheriff):
  - Too dark: median L* 12, interior 21-29. Leather had only 3 shades in the palette, and they wore it head to toe.
  - Lanky: one-pixel limbs (capsule radius 1.3-1.6), 6-7% thin pixels, small heads (radius 3).
- **Everyone, approved ones included:**
  - Flat. Shading came in 2-4 big steps (neighbour dL* 27-44), so patches were large: 4-7.5 px against vanilla's 2.
  - Despeckled to nothing. The orphan ratio was about 0.02 against vanilla's 0.19.
- **Small props drowned in their own outlines.** Each gun part and hat brim drew its own outline, so a 3-px barrel was all outline.
- **The approved three passed on other grounds:** chunky shapes (head radius 5.8, limbs 2-2.3) and readable values. That is the floor; the texture and ramp work below is the step up.

## 5. Rules for detailed mobs and bosses (D4 rule 18, checked by `tools/check_detail.py`)

### Hard limits (the tool fails)

- Interior L* at least 30.
- Thin pixels at most 3%.
- Black outlines at most 5%.
- At least 18 colours.

### Targets (the tool warns)

- Median L* at least 21.
- Edge density at least 0.55 (vanilla's lowest tenth is 0.62).
- Cluster mean at most 3.5 px.
- Neighbour dL* between 16 and 32.
- Colours within the caps: enemies 32, bosses 48.

### Proportions

- About 2.5 heads tall, with the head and hat 40% of the height.
- Limbs at least 3 art px thick (capsule radius 1.8 or more).
- Big boots, hats and guns.

### Palette (added 2026-11-05, 42 colours)

| ramp | shades | what it is |
|---|---|---|
| `steel` | 9 | iron with in-between shades |
| `gilt` | 10 | brass with in-between shades and a gleam |
| `hide` | 7 | leather extended up to tan |
| `crimson` | 6 | new |
| `denim` | 6 | new |
| `ghost` | 6 | new |
| `oak` | 6 | new |
| `ivory` | 6 | new |

The old ramps keep their indices, so older art regenerates unchanged.

### Shading

- Run long ramps from `lo=2-3` up to `hi=len-1`, biased a little toward the light.
- Use `level(..., dither=)` (`face`/`dome`/`cyl` take `dither=0.15-0.2`). It puts a part-space checker on band edges.

### Texture

- `rig.texture(shade, kind)` adds felt, weave, grain, speckle or brushed texture, one shade either way, in the part's own space.
- Finish each canvas with `westbots.finish`: `rig.soften_orphans` keeps one-shade texture and removes noise, then `rig.selout` lightens the lit-side outline.

### Small props

- Draw one outlined silhouette (`Union`), then shade the parts inside it with `outline=False, clip=`, with dark seams between them.
- Size every part to whole pixel rows. A box from y0 to y1 covers the pixel centres between them, so a barrel needs 4 rows to keep 2 interior rows.

### Stable texture (D4 rule 17)

- Texture and dither are hashed in the part's own coordinates.
- Build moving parts in their own space and place them by a whole-pixel translation (`Xf.pose(0, (0, 0), (ox, oy))`). Baking the bob into the coordinates made the 2026-11-05 Bandit's weave crawl: `check_flicker` read 4%.

### Glints

- `rig.glint` puts the ramp's top shade, with a one-shade cross, on polished metal.
- At most a few glints per part.

## 6. Metal Slug notes (what we take, no assets)

- Chunky cartoon proportions and big readable props.
- Polished metal with hard speculars.
- Dense mechanical detail: rivets, seams, bolts, belts and buckles.
- Strong secondary motion: smoke, recoil, coat tails and spurs.
- Effects that sell the impact: muzzle flashes, smoke trails, debris and gores.

## 7. After the redraw (2026-11-05, first frame of each)

| enemy | colours | interior L* | edge density | cluster (px) | thin |
|---|---|---|---|---|---|
| Brass Bandit | 13 → 31 | 21 → 37 | 0.46 → 0.58 | 4.5 → 3.0 | 6.7% → 0.9% |
| Sheriff | 14 → 29 | 29 → 42 | 0.50 → 0.58 | 4.3 → 3.1 | 6.0% → 1.5% |
| Mechanical Bull | 16 → 32 | 43 → 47 | 0.37 → 0.48 | 7.5 → 4.6 | 1.1% → 1.5% |
| Dinamitrom | 16 → 28 | 39 → 43 | 0.47 → 0.55 | 4.9 → 4.1 | 2.3% → 2.5% |
| Splasher | 19 → 30 | 40 → 40 | 0.48 → 0.53 | 4.5 → 3.7 | 1.9% → 0.6% |

- **Proof:** `docs/media/2026-11-05_art-study-before-after.png`.
- **Still below vanilla:** the Bull's and the Dinamitrom's edge density and patch size. They are big, smooth machines, and the next pass would add more plate detail.
- **Previous generators** are in `art/<area>/previous/`. To run one, copy it back next to its folder's other files (it imports by relative path).
