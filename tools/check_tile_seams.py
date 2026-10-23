"""Check that a block's tile sheet connects seamlessly (D4 "seamless blocks" rule). Exit code 1 on failure.

    python -P tools/check_tile_seams.py SHEET.png [--table art/templates/terrain_exposure.json] [--max-ratio 1.25]

Same-type blocks must merge into one clump with no visible grid, like vanilla ores and stone: only the
clump's outer perimeter gets an outline. Two measurements over the joined ("----") frames, at 1x art scale:

* seam ratio: average luminance step across tile boundaries divided by the average step inside tiles,
  measured on random grids of interior frames. A per-tile bevel or seam line pushes this well above 1.
* edge bias: how much each frame's outer rows/columns differ in brightness from the frame as a whole.
  A darker bottom edge or a lighter top edge (a bevel) shows up here even if the ratio passes.
"""
import argparse
import json
import random
import sys
from PIL import Image

ART = 8          # art pixels per tile
STRIDE = 18      # frame stride at 2x


def luminance(rgb):
    r, g, b = rgb
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def interior_frames(sheet, table):
    frames = []
    for key, signature in table.items():
        if signature != "----":
            continue
        fx, fy = (int(v) for v in key.split(","))
        tile = sheet.crop((fx * STRIDE, fy * STRIDE, fx * STRIDE + 16, fy * STRIDE + 16)).resize((ART, ART), Image.NEAREST)
        px = tile.load()
        frames.append([[luminance(px[x, y][:3]) if px[x, y][3] else None for x in range(ART)] for y in range(ART)])
    return frames


def seam_ratio(frames, grid=16, seeds=8):
    boundary, inside = [], []
    for seed in range(seeds):
        rng = random.Random(seed)
        cells = [[rng.choice(frames) for _ in range(grid)] for _ in range(grid)]
        size = grid * ART

        def lum(x, y):
            return cells[y // ART][x // ART][y % ART][x % ART]

        for y in range(size):
            for x in range(size):
                a = lum(x, y)
                for nx, ny in ((x + 1, y), (x, y + 1)):
                    if nx >= size or ny >= size:
                        continue
                    b = lum(nx, ny)
                    if a is None or b is None:
                        continue
                    crosses = (nx // ART != x // ART) or (ny // ART != y // ART)
                    (boundary if crosses else inside).append(abs(a - b))
    return (sum(boundary) / len(boundary)) / max(sum(inside) / len(inside), 1e-6)


def edge_bias(frame):
    values = [v for row in frame for v in row if v is not None]
    mean = sum(values) / len(values)
    edges = {
        "top": frame[0], "bottom": frame[ART - 1],
        "left": [row[0] for row in frame], "right": [row[ART - 1] for row in frame],
    }
    return max(abs(sum(e) / len(e) - mean) for e in edges.values() if None not in e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--table", default="art/templates/terrain_exposure.json")
    ap.add_argument("--max-ratio", type=float, default=1.25)
    ap.add_argument("--max-edge-bias", type=float, default=0.06)
    a = ap.parse_args()

    sheet = Image.open(a.sheet).convert("RGBA")
    frames = interior_frames(sheet, json.load(open(a.table)))
    if not frames:
        print("no interior frames found")
        sys.exit(1)
    ratio = seam_ratio(frames)
    bias = max(edge_bias(f) for f in frames)
    ok = ratio <= a.max_ratio and bias <= a.max_edge_bias
    print(f"[{'ok' if ok else 'FAIL'}] {a.sheet}: seam ratio {ratio:.2f} (max {a.max_ratio}), "
          f"edge bias {bias:.3f} (max {a.max_edge_bias}), {len(frames)} interior frames")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
