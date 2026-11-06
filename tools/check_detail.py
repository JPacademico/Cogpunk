"""Detail check for Cogpunk's detailed mobs and bosses (D4 rule 18, 2026-11-05): measures a frame the way the pixel-art
study measured vanilla Terraria's NPCs (docs/design/pixel-art-study.md) and compares it with the targets taken from
vanilla's middle half.

    python -P tools/check_detail.py <RigData.cs> <layer base> [--frames 0,6] [--report]
    python -P tools/check_detail.py --png <image.png> [...]          (a single 2x frame, e.g. an item)

<layer base> is the middle sheet without ".png" (Content/OldBrassTown/NPCs/BrassBandit); the _Far, _Near and _Glow sheets
next to it are composited in that order for each frame. Frames come from the grid layout in the rig data (CellWidth,
CellHeight, Columns, 2 px padding). Exit 1 when a hard rule fails (pure-black outlines, one-pixel limbs, a dark body,
too few colours); the soft targets are reported as warnings.
"""
import argparse
import os
import re
import sys

from PIL import Image

PAD = 2

# Vanilla's middle half (38 frames, 2026-11-05) and the hard floors (D4 rule 18).
HARD = {
    "interior_L": (30.0, None),     # mid-value bodies (vanilla p25 33.4; our cowboys were 21-29)
    "thin": (None, 0.03),           # no one-pixel limbs (vanilla p90 1.8%; our cowboys 6-7%)
    "outline_black": (None, 0.05),  # coloured outlines, never black
    "colors": (18, None),           # enough shades to model forms (vanilla median 22)
}
SOFT = {
    "L_p50": (21.0, None),          # vanilla p25 21.4
    "edge_density": (0.55, None),   # vanilla p10 0.62, median 0.73 (ours were 0.37-0.50)
    "cluster_mean": (None, 3.5),    # vanilla p90 2.5 (ours were 4.3-7.5)
    "contrast_dL": (16.0, 32.0),    # vanilla p10-p90 21-30: many small steps, not a few big jumps
    "colors": (None, 48),
}


def lab_l(c):
    def lin(u):
        u /= 255.0
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    y = 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])
    return 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y


def to_art(im):
    """2x game texture -> 1x art pixels (the top-left of each 2x2 block)."""
    w, h = im.size
    return im.resize((w // 2, h // 2), Image.NEAREST) if w % 2 == 0 and h % 2 == 0 else im


def metrics(art):
    w, h = art.size
    p = art.load()
    col = {(x, y): p[x, y][:3] for y in range(h) for x in range(w) if p[x, y][3] >= 128}
    if not col:
        return None
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    L = {}

    def lum(c):
        if c not in L:
            L[c] = lab_l(c)
        return L[c]
    boundary = [q for q in col if any((q[0] + dx, q[1] + dy) not in col for dx, dy in N4)]
    interior = [q for q in col if q not in set(boundary)]
    bset = set(boundary)
    interior = [q for q in col if q not in bset]
    xs = [q[0] for q in col]
    ys = [q[1] for q in col]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    la = sorted(lum(c) for c in col.values())
    seen = set()
    clusters = 0
    for q0, c in col.items():
        if q0 in seen:
            continue
        clusters += 1
        stack = [q0]
        seen.add(q0)
        while stack:
            x, y = stack.pop()
            for dx, dy in N4:
                r = (x + dx, y + dy)
                if r not in seen and col.get(r) == c:
                    seen.add(r)
                    stack.append(r)
    pairs = diff = 0
    dls = []
    for (x, y), c in col.items():
        for dx, dy in ((1, 0), (0, 1)):
            o = col.get((x + dx, y + dy))
            if o is not None:
                pairs += 1
                if o != c:
                    diff += 1
                    dls.append(abs(lum(c) - lum(o)))
    thin = sum(1 for (x, y) in col if ((x - 1, y) not in col and (x + 1, y) not in col) or ((x, y - 1) not in col and (x, y + 1) not in col))
    orphans = sum(1 for q in interior if not any(col.get((q[0] + dx, q[1] + dy)) == col[q] for dx, dy in N8))
    return {
        "art_w": bw, "art_h": bh, "fill": len(col) / (bw * bh), "colors": len(set(col.values())),
        "L_p50": la[len(la) // 2], "interior_L": sum(lum(col[q]) for q in interior) / max(1, len(interior)),
        "outline_L": sum(lum(col[q]) for q in boundary) / max(1, len(boundary)),
        "outline_black": sum(1 for q in boundary if max(col[q]) < 24) / max(1, len(boundary)),
        "edge_density": diff / max(1, pairs), "cluster_mean": len(col) / clusters,
        "contrast_dL": sum(dls) / max(1, len(dls)), "thin": thin / len(col),
        "orphans": orphans / max(1, len(interior)),
    }


def rig_consts(path):
    text = open(path, encoding="utf-8").read()
    return {k: int(v) for k, v in re.findall(r"(\w+)\s*=\s*(-?\d+)\b", text)}


def frame_image(base, consts, frame):
    cw, ch = consts["CellWidth"], consts["CellHeight"]
    cols = max(1, consts.get("Columns", 1))
    x0 = frame % cols * (cw + PAD)
    y0 = frame // cols * (ch + PAD)
    cell = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    for suffix in ("_Far", "", "_Near", "_Glow"):
        path = base + suffix + ".png"
        if os.path.exists(path):
            sheet = Image.open(path).convert("RGBA")
            cell.alpha_composite(sheet.crop((x0, y0, x0 + cw, y0 + ch)))
    return cell


def judge(name, m, report):
    hard_fail = []
    warn = []
    for k, (lo, hi) in HARD.items():
        if (lo is not None and m[k] < lo) or (hi is not None and m[k] > hi):
            hard_fail.append(k)
    for k, (lo, hi) in SOFT.items():
        if (lo is not None and m[k] < lo) or (hi is not None and m[k] > hi):
            warn.append(k)
    line = (f"{name}: {m['art_w']}x{m['art_h']} art px, {m['colors']} colours, median L* {m['L_p50']:.1f}, interior L* "
            f"{m['interior_L']:.1f}, edge density {m['edge_density']:.2f}, cluster {m['cluster_mean']:.2f} px, "
            f"neighbour dL* {m['contrast_dL']:.1f}, thin {m['thin'] * 100:.1f}%, black outline {m['outline_black'] * 100:.0f}%, "
            f"fill {m['fill']:.2f}")
    print(line)
    for k in hard_fail:
        print(f"  FAIL {k} = {m[k]:.3f} (rule {HARD[k]})")
    for k in warn:
        print(f"  warn {k} = {m[k]:.3f} (vanilla target {SOFT[k]})")
    return not hard_fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rig", nargs="?")
    ap.add_argument("base", nargs="?")
    ap.add_argument("--frames", default="0")
    ap.add_argument("--png", nargs="*")
    ap.add_argument("--report", action="store_true", help="never fail, only report")
    a = ap.parse_args()
    ok = True
    if a.png:
        for path in a.png:
            m = metrics(to_art(Image.open(path).convert("RGBA")))
            if m:
                ok &= judge(os.path.basename(path), m, a.report)
    else:
        consts = rig_consts(a.rig)
        for f in (int(v) for v in a.frames.split(",")):
            m = metrics(to_art(frame_image(a.base, consts, f)))
            if m:
                ok &= judge(f"{os.path.basename(a.base)} frame {f}", m, a.report)
    sys.exit(0 if ok or a.report else 1)


if __name__ == "__main__":
    main()
