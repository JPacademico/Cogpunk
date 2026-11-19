"""Turning the user's own pixel-art references into Cogpunk sprites (2026-11-18). The user drew (or had drawn) the Jade Cursed
Glaive and the Incense Mace and asked: "just resize to match terraria but keep the detail and style". The references are
upscaled pixel art (each art pixel a ~10 px block, soft at the edges), so:

  1. native(): read each block's centre (median of its middle 40%) on the reference's own grid -> the art at 1:1;
  2. to_palette(): every pixel to the nearest colour (CIELAB) of the ramps the sprite may use; the backdrop to clear;
  3. shrink(): down to Terraria's size by area: a target pixel is filled when enough of its footprint is, and takes the
     colour with the most area, outlines and rims weighted up so thin lines survive (`keep`);
  4. tidy(): D4: lone pixels take their neighbours' colour, one-pixel holes are filled, and every silhouette pixel left with
     a lighter colour than its ramp allows on an edge gets its ramp's darkest shade unless it is a lit rim (`rims`).

Deterministic (no randomness); the grids are measured once and written down (GRIDS), so a rerun gives the same sprite.
"""
import math

from PIL import Image

# the reference's block size and the first block's offset (px), measured by the lowest in-block variance
GRIDS = {
    "glaive": (10.5, 7.0, 3.5),
    "mace": None,               # measured on first use (see measure_grid) and printed
}


def _lin(u):
    u /= 255.0
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def lab(c):
    r, g, b = (_lin(v) for v in c[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def measure_grid(img, lo=8.0, hi=16.0, step=0.05):
    """The block size and offset with the least colour variance inside the blocks (slow: run once, write the result)."""
    import numpy as np
    a = np.asarray(img.convert("RGB"), dtype=float)
    h, w, _ = a.shape
    best = None
    p = lo
    while p <= hi:
        for ox in [p * k / 6 for k in range(6)]:
            for oy in [p * k / 6 for k in range(6)]:
                tot, n = 0.0, 0
                by = oy
                while by < h - p:
                    bx = ox
                    while bx < w - p:
                        blk = a[int(by + p * 0.25):int(by + p * 0.75), int(bx + p * 0.25):int(bx + p * 0.75)]
                        tot += blk.var(axis=(0, 1)).sum()
                        n += 1
                        bx += p * 3
                    by += p * 3
                s = tot / max(1, n)
                if best is None or s < best[0]:
                    best = (s, p, ox, oy)
        p += step
    return best[1:]


def native(path, grid):
    """The reference at 1:1: rows of (r, g, b), one per block (the median of its middle 40%)."""
    img = Image.open(path).convert("RGB")
    p, ox, oy = grid
    w, h = img.size
    cols, rows = int((w - ox) // p), int((h - oy) // p)
    px = img.load()
    out = []
    for r in range(rows):
        row = []
        for c in range(cols):
            x0, x1 = int(ox + c * p + p * 0.3), int(ox + c * p + p * 0.7)
            y0, y1 = int(oy + r * p + p * 0.3), int(oy + r * p + p * 0.7)
            rs, gs, bs = [], [], []
            for y in range(y0, max(y0 + 1, y1)):
                for x in range(x0, max(x0 + 1, x1)):
                    v = px[x, y]
                    rs.append(v[0])
                    gs.append(v[1])
                    bs.append(v[2])
            rs.sort()
            gs.sort()
            bs.sort()
            m = len(rs) // 2
            row.append((rs[m], gs[m], bs[m]))
        out.append(row)
    return out


def to_palette(rows, colours, backdrop, clear_dist=14.0):
    """{(x, y): palette colour} for every block that isn't the backdrop (CIELAB distance under clear_dist)."""
    labs = [(lab(c), c) for c in colours]
    bl = lab(backdrop)
    out = {}
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            lc = lab(c)
            if math.dist(lc, bl) < clear_dist:
                continue
            best = min(labs, key=lambda t: (t[0][0] - lc[0]) ** 2 + (t[0][1] - lc[1]) ** 2 + (t[0][2] - lc[2]) ** 2)
            out[(x, y)] = best[1]
    return out


def shrink(pix, scale, fill=0.42, keep=None):
    """Down by `scale` (> 1) by area: a pixel is filled when `fill` of its footprint is, and takes the colour with the
    most area (each colour's area times keep.get(colour, 1): outlines and rims up, so thin lines survive)."""
    keep = keep or {}
    xs, ys = [x for x, _ in pix], [y for _, y in pix]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0 + 1, max(ys) - y0 + 1
    tw, th = int(math.ceil(w / scale)), int(math.ceil(h / scale))
    out = {}
    for ty in range(th):
        for tx in range(tw):
            fx0, fx1 = tx * scale, (tx + 1) * scale
            fy0, fy1 = ty * scale, (ty + 1) * scale
            area, votes = 0.0, {}
            for y in range(int(math.floor(fy0)), int(math.ceil(fy1))):
                oy = min(fy1, y + 1) - max(fy0, y)
                if oy <= 0:
                    continue
                for x in range(int(math.floor(fx0)), int(math.ceil(fx1))):
                    ox = min(fx1, x + 1) - max(fx0, x)
                    if ox <= 0:
                        continue
                    c = pix.get((x + x0, y + y0))
                    if c is None:
                        continue
                    a = ox * oy
                    area += a
                    votes[c] = votes.get(c, 0.0) + a * keep.get(c, 1.0)
            if area >= fill * scale * scale and votes:
                out[(tx, ty)] = max(votes.items(), key=lambda kv: (kv[1], -sum(kv[0])))[0]
    return out


def tidy(pix, lum_keep=14.0):
    """Lone pixels (no 4-neighbour of their colour, all four filled) take the neighbours' majority unless they are within
    `lum_keep` L* of it (texture); one-pixel holes (all four neighbours filled) are filled with their majority."""
    def L(c):
        return lab(c)[0]
    changes = {}
    for (x, y), col in pix.items():
        nb = [pix.get((x + 1, y)), pix.get((x - 1, y)), pix.get((x, y + 1)), pix.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        major = max(set(nb), key=nb.count)
        if abs(L(col) - L(major)) > lum_keep:
            changes[(x, y)] = major
    pix.update(changes)
    xs, ys = [x for x, _ in pix], [y for _, y in pix]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in pix:
                continue
            nb = [pix.get((x + 1, y)), pix.get((x - 1, y)), pix.get((x, y + 1)), pix.get((x, y - 1))]
            if None not in nb:
                pix[(x, y)] = max(set(nb), key=nb.count)
    return pix


def to_image(pix, pad=0):
    xs, ys = [x for x, _ in pix], [y for _, y in pix]
    x0, y0 = min(xs), min(ys)
    im = Image.new("RGBA", (max(xs) - x0 + 1 + 2 * pad, max(ys) - y0 + 1 + 2 * pad), (0, 0, 0, 0))
    for (x, y), c in pix.items():
        im.putpixel((x - x0 + pad, y - y0 + pad), tuple(c) + (255,))
    return im
