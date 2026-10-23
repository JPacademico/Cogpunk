"""Assemble block tiles the way Terraria frames them, for D5 previews of new blocks.

Each tile looks at its four neighbours: a side is "exposed" when the neighbour is not the same material
(blocks without merge flags behave this way). The exposure signature (T R B L) picks a frame from the
standard terrain layout, using art/templates/terrain_exposure.json, and one of its random variants.

Usage from another script:
    from terrain import load_frames, render
    frames = load_frames("art/templates/terrain_exposure.json")
    img = render(["..##..", ".####."], {"#": sheet_image}, frames, background=(30, 30, 36))

Leaves out: slopes and half blocks, lighting, and merging between different materials.
"""
import json
import random
from PIL import Image

TILE = 16      # on-screen size of one tile at 1x game zoom
STRIDE = 18    # frame stride in the sheet (16 px + 2 px gutter)


def load_frames(table_path):
    """Signature 'TRBL' (o = exposed, - = joined) -> list of (frame_x, frame_y). Dirt-merge frames are skipped."""
    table = json.load(open(table_path))
    frames = {}
    for key, signature in table.items():
        if "d" in signature:
            continue
        fx, fy = (int(v) for v in key.split(","))
        frames.setdefault(signature, []).append((fx, fy))
    return frames


def render(grid, sheets, frames, background=None, seed=1):
    """grid: list of equal-length strings, '.' = empty, any other char = a key of `sheets`."""
    rng = random.Random(seed)
    h, w = len(grid), len(grid[0])
    img = Image.new("RGBA", (w * TILE, h * TILE), (background + (255,)) if background else (0, 0, 0, 0))

    def cell(x, y):
        return grid[y][x] if 0 <= x < w and 0 <= y < h else "."

    for y in range(h):
        for x in range(w):
            m = cell(x, y)
            if m == ".":
                continue
            signature = "".join("-" if cell(x + dx, y + dy) == m else "o"
                                for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
            fx, fy = rng.choice(frames[signature])
            tile = sheets[m].crop((fx * STRIDE, fy * STRIDE, fx * STRIDE + TILE, fy * STRIDE + TILE))
            img.alpha_composite(tile, (x * TILE, y * TILE))
    return img
