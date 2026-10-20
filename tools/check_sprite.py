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
