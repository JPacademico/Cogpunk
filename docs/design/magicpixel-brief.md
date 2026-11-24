# MagicPixel brief: Cogpunk's technical rules for generated sprites (2026-11-23)

The user installed the MagicPixel MCP so Claude can generate and edit sprites ("it has tokens for art generation so be precise
with it, specifiying technical rules for our terraria sprite generation and providing examples"). Generation spends their
tokens, so every request states these rules, and one request asks for one thing. Output is a proposal: it goes through the
checks below like any art, then into the generator that owns the sprite (never dropped into Content/ directly).

## Setup (once)

- The server is registered as `magicpixel` (HTTP, https://magicpixel.art/mcp). It authenticates with OAuth: run `claude`, type
  `/mcp`, pick `magicpixel`, Authenticate. A logged-in website alone isn't enough.
- MCP tools load when a session starts: after authenticating, start a new session.

## Rules to put in every request

1. **Size and scale**: draw at 1x on an exact pixel grid, the size given in art pixels (items 12-24, weapons 16-40, mobs 20-48
   tall, pets 16-30, bosses 50-120). We export 2x nearest-neighbour ourselves: ask for 1x, never upscaled.
2. **No anti-aliasing, no semi-transparent pixels, no blur**: every pixel fully opaque or fully clear; hard edges.
3. **Palette**: name the colours (hex) of the Cogpunk ramps to use, or attach the source sprite and say "keep its exact
   palette". At most about 48 colours for a boss, 16-24 for a mob or a weapon, under 16 for an item or a pet.
4. **Outline**: a 1 px outline in the darkest step of each part's own ramp (never pure black); lit from the top-left.
5. **Facing**: bosses and creatures face left (the game flips them); guns and swung weapons point right or top-right.
6. **Background**: transparent, nothing else in the canvas (no glow haze, no floor, no particles: effects are the game's).
7. **Animations**: an edit of the given frame, "keep the silhouette, palette and pixel density; change only <part>", one
   frame per request, the same canvas size and position (so frames stack without shifting).

## Example requests

- *Edit a frame (the Fungimancer, 125 x 103):* "Edit this sprite: open the frog's mouth wide, showing the upper teeth and a
  pink tongue inside. Keep everything else pixel-identical: same canvas, palette, outline and position. 1x, no anti-aliasing,
  no semi-transparency, transparent background."
- *A new frame from a model (the jade fennec, 22 x 19):* "Edit this sprite: the fox standing on four short legs, mid-trot
  (near foreleg forward, far hind leg forward), the same head, ears and colours. Same 1x scale and palette, 26 x 24 canvas,
  feet on the bottom row, transparent background."
- *A new item (16 x 16):* "A jade crystal shard item icon, 16 x 16 px at 1x, lit from the top-left, a 1 px outline in the
  darkest jade (#0a2220), colours only from: #0a2220 #12463a #1e7258 #3aa676 #76dca2 #c4fad6 (+ #fffade for one glint), no
  anti-aliasing, transparent background."

## Checks on anything generated

`tools/check_sprite.py --palette art/palettes/cogpunk.gpl` (snap to the palette first if needed), `tools/check_detail.py` for
creatures, a look at 4x over dark and light backgrounds next to the source, and the user's approval (the cogpunk-pixel-art
skill, section 5).
