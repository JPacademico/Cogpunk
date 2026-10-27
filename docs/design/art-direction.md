# Art direction: detailed entities

Set by the user on 2026-10-26. Applies to **bosses, minibosses, detailed mobs and the weapons the user names**. Everything else follows the base pixel-art rules (SKILL.md D4, rules 1-12). Reference implementation: **Trash-Tr0m** (`Content/Bosses/TrashTr0m/`, generator `art/bosses/trashtr0m/`).

## 1. Three-quarter view

Bodies are drawn **side-facing and turned towards the viewer** (a 3/4 view, facing left per D4 rule 8). The front and the near side are both visible, top faces catch the light, and the far side is hidden.

- Model boxy parts with three visible faces (front, near side, top), each shaded from its own normal. Light comes from the top-left and towards the viewer.
- In this view the far limb appears *ahead* of the near one (further forward on screen) and behind the body. The near limb sits in front of the torso's near side.
- Exception: bosses that are **flying heads** (Skeletron-like) may face the camera.

## 2. Multiplane layers (parallax)

Important sprites are split into **up to three layers** that animate independently and read at different depths:

| Layer | Trash-Tr0m | Depth handling |
|---|---|---|
| Far | far arm (crane boom, claw) | baked one ramp step darker in the art, a further x0.88 light in code, parallax shift away from the screen centre |
| Middle | torso, waist, head, jaw (+ `_Glow`) | none (the anchor) |
| Near | near arm (tyre pauldron, boom, fist) | parallax shift towards the screen edge |

Rules:

- **Never rotate or scale at runtime.** Rotated pixel art produces mixels. Render every pose of every layer from a generator instead: parts placed by transforms and rasterised per pixel, limbs posed with two-bone IK (`art/bosses/trashtr0m/rig.py`).
- Draw with `Core/Visuals/DepthLayers`: `DrawFrame` for packed atlas pages (each frame cropped to its own pixels with its rig origin, ground-line clip, `buried` clip for emerging or burrowing; `DrawCell` remains for simple grid sheets) and `Shift` for parallax.
- **Fluid motion (user, 2026-10-26):** no key pose may snap to the next. Give every attack in-betweens: anticipation (the limb leaving its rest, rising, cocking back), a strike frame between the high pose and the impact (D4 rule 10's smear), a settle and a lower after it; open and close jaws in steps; wind-ups and follow-throughs on spits; tweens between death poses. Trash-Tr0m's are listed in `docs/media/2026-10-26_boss-trashtr0m-inbetweens.png`. The shift follows vanilla's background scrolling (decompiled `Main.DrawSurfaceBG`: a layer at `-screenPosition.X * bgParallax`), giving a relative offset of `(anchor - screen centre) * (p - 1)`. It is clamped to a few px and snapped to the 2 px art grid.
- Everything happens in one SpriteBatch pass with no Begin/End and no allocation. This is the same cost as vanilla's multi-part bosses (Skeletron's limbs are extra textures drawn from `Main.DrawNPCDirect`).
- The generator writes a `*RigData.cs` with cell sizes, origins, frame indices and the points the AI needs (hand contacts, mouth). The AI reads the same tables through a pose function of synced state only, so drawing, gameplay and every client agree.
- **Root motion:** a crawler or walker moves only when a planted part drags, by exactly the distance the art moves that part back. The D5 simulation measures the slip of planted parts: it must be 0 px.

## 3. Themed death cinematics

Every boss dies on screen: a scripted, themed breakdown that **locks the camera like its intro**.

- Inherit `Core/Templates/BossNPC`: it refuses the killing blow (`CheckDead`), switches to the dying state (synced), keeps the boss untouchable, and finishes it on the server with `StrikeInstantKill` after `DeathAnimationTicks`. The loot and `OnKill` run then.
- Lock the camera with `Core/Visuals/CinematicCamera.Request(focus, Envelope(...))` for players in range.
- The defeat card is the same for every boss: the boss's name and "Defeated", nothing else (`BossTitleSystem.ShowDefeated`, shown by `BossNPC`).
- Trash-Tr0m (240 ticks): jolt, then small blasts popping across the body, a sag, a slump that hits the ground, eyes flickering out, the last steam escaping, and a final blast that throws parts (tyre, jaw, crest, gear, piston, plate).

## 4. Metal Slug-level detail

- Chunky outlines in each material's ramp 0, and strong 1 px edge highlights on the lit side.
- Dense mechanical detail: rivet rows, bolts, panel seams with lit lips, hydraulic rams with chrome rods, hoses, hazard stripes, weld beads, gauges, grilles.
- Cast shadows between overlapping parts.
- Large flat plates get seams, a part or a decal, not grime noise. Keep grime to short streaks under seams.
- Wear that fits the theme: Trash-Tr0m is rusted (`rig.py` rust: patches of the copper ramp at the same shade, gathering towards the bottom of each part, with short drips; the noise lives in each part's own space so patches stay on a moving limb).
- Colour cap: bosses 48 colours from the Cogpunk palette (Trash-Tr0m's body sheet uses 29).

## Checklist for a new detailed entity

1. Sketch the 3/4 silhouette and decide the layer split (≤ 3).
2. Write a generator under `art/<same path as Content>/` that renders all poses and the `*RigData.cs`.
3. Draw with `DepthLayers` and take AI points from the rig data.
4. Bosses: inherit `BossNPC`, give the intro and the death cinematic `CinematicCamera` locks.
5. `check_sprite.py` on every sheet, plus a D5 simulation that replays the AI with the real sheets (and measures root-motion slip for walkers or crawlers).
