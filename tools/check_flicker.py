"""Flicker check for generated multiplane sprites (D4, user 2026-10-29: "the boss quickly changes color on some
animations"). Run from the repo root:

    python -P tools/check_flicker.py <RigData.cs> <layer base path> [--seq Name ...] [--limit PCT] [--out sheet.png]

    e.g. python -P tools/check_flicker.py Content/Bosses/TarTyrant/TarTyrantRigData.cs Content/Bosses/TarTyrant/TarTyrant

It reads the frame tables (FarFrames, BodyFrames, NearFrames: page, x, y, w, h, origin x, origin y per frame) and the
sequences (`Name0 = first, NameFrames = count`) of a generated *RigData.cs, places every plane of every frame at the rig
origin and looks, plane by plane (a near arm passing in front of the body is occlusion, not flicker), for colour that
changes without the shape moving:

* toggles: interior pixels (opaque, with opaque 4-neighbours, in three frames in a row) whose colour goes A -> B -> A.
  Motion makes these too (an edge that moves a pixel and back), so they are reported, not judged.
* flashes: toggles whose middle colour B is nowhere in that pixel's 3x3 art-pixel neighbourhood in the frames before
  and after. Motion can't explain those: a shading band, a rust spot or a highlight changed colour in place. This is
  the flicker the user saw (2026-10-29), and it is what fails a sequence.

Loops (Idle, Move) wrap around and must stay under --loop-limit percent of their interior (default 0.5: a loop plays
for seconds on end, so any flicker shows); other sequences under --limit (default 1.5: a one-frame smear in a swing may
flash a little). Sequences named with --report (a melt, a rise, a death slump: the whole sprite deforms on purpose) are
measured but never fail. Exit code 1 on a failure. --out writes a sheet of the worst triples with the flashing
pixels marked in magenta (and other toggles in yellow), for a look at where it happens.
"""
import argparse
import os
import re
import sys

from PIL import Image

LOOPS = ("Idle", "Move")


def parse(path):
    s = open(path, encoding="utf-8").read()
    arrays = {m.group(1): [int(v) for v in re.findall(r"-?\d+", m.group(2))]
              for m in re.finditer(r"public static readonly (?:short|byte|int)\[\] (\w+) = \{([^}]*)\};", s)}
    consts = {}
    for m in re.finditer(r"const int ([^;]+);", s):
        for part in m.group(1).split(","):
            if "=" in part:
                k, v = (x.strip() for x in part.split("=", 1))
                if re.fullmatch(r"-?\d+", v):
                    consts[k] = int(v)
    seqs = {}
    sheets = [k[:-len("FrameCount")] for k in consts if k.endswith("FrameCount") and k != "FrameCount"]
    for k, v in consts.items():
        if k.endswith("Frames") and k[:-6] + "0" in consts:
            name = k[:-6]
            if any(name.startswith(sheet) and name != sheet for sheet in sheets):
                continue                                     # a run of another sheet (SpikeRise0 of the spike sheet...)
            seqs[name] = (consts[name + "0"], v)
    return arrays, consts, seqs


PLANES = (("Far", "_Far"), ("Body", ""), ("Near", "_Near"))


def frame_image(arrays, consts, base, frame, cache, only=None):
    planes = []
    for layer, suffix in PLANES:
        if only is not None and layer != only:
            continue
        table = arrays.get(layer + "Frames")
        if table is None:
            continue
        page, x, y, w, h, ox, oy = table[frame * 7:frame * 7 + 7]
        if w <= 0:
            continue
        path = base + suffix + ("" if page == 0 else "_Page%d" % page) + ".png"
        if path not in cache:
            cache[path] = Image.open(path).convert("RGBA") if os.path.exists(path) else None
        sheet = cache[path]
        if sheet is not None:
            planes.append((sheet.crop((x, y, x + w, y + h)), ox, oy))
    return planes


def composite(planes, size=640, oy0=560):
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for im, ox, oy in planes:
        out.alpha_composite(im, (size // 2 - ox, oy0 - oy))
    return out


def opaque(px, w, h, x, y):
    return 0 <= x < w and 0 <= y < h and px[x, y][3] > 0


NEAR = [(dx, dy) for dx in (-2, 0, 2) for dy in (-2, 0, 2)]


def analyse(frames):
    """Per triple (i-1, i, i+1): (flashes, toggles, interior size, flash marks, toggle marks)."""
    data = [(f.load(), f.width, f.height) for f in frames]
    n = len(frames)
    out = []
    for i in range(n):
        a, b, c = data[(i - 1) % n], data[i], data[(i + 1) % n]
        w, h = b[1], b[2]
        tog, flash, interior, fmarks, tmarks = 0, 0, 0, [], []
        for y in range(1, h - 1, 2):                       # 2x art: one sample per art pixel
            for x in range(1, w - 1, 2):
                if not all(opaque(p[0], w, h, x + dx, y + dy) for p in (a, b, c) for dx, dy in ((0, 0), (2, 0), (-2, 0), (0, 2), (0, -2))):
                    continue
                interior += 1
                ca, cb, cc = a[0][x, y][:3], b[0][x, y][:3], c[0][x, y][:3]
                if ca != cc or cb == ca:
                    continue
                tog += 1
                moved = False
                for p in (a, c):
                    for dx, dy in NEAR:
                        if opaque(p[0], w, h, x + dx, y + dy) and p[0][x + dx, y + dy][:3] == cb:
                            moved = True
                            break
                    if moved:
                        break
                if moved:
                    tmarks.append((x, y))
                else:
                    flash += 1
                    fmarks.append((x, y))
        out.append((flash, tog, interior, fmarks, tmarks))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rig")
    ap.add_argument("base")
    ap.add_argument("--seq", nargs="*")
    ap.add_argument("--limit", type=float, default=1.5)
    ap.add_argument("--loop-limit", type=float, default=0.5)
    ap.add_argument("--report", nargs="*", default=[],
                    help="sequences that deform the whole sprite on purpose (a melt, a rise, a death slump): measured, never failed")
    ap.add_argument("--out")
    args = ap.parse_args()
    arrays, consts, seqs = parse(args.rig)
    cache = {}
    names = args.seq or list(seqs)
    failed = False
    worst_sheet = []
    for name in names:
        if name not in seqs:
            print("[skip] %s: no such sequence" % name)
            continue
        first, count = seqs[name]
        frames = [composite(frame_image(arrays, consts, args.base, first + k, cache)) for k in range(count)]
        if count < 3:
            print("[ok] %s: %d frames (nothing to compare)" % (name, count))
            continue
        res = None
        for layer, _ in PLANES:                              # plane by plane, summed
            if layer + "Frames" not in arrays:
                continue
            r = analyse([composite(frame_image(arrays, consts, args.base, first + k, cache, layer)) for k in range(count)])
            res = r if res is None else [(a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3], a[4] + b[4]) for a, b in zip(res, r)]
        loop = name in LOOPS
        idx = range(count) if loop else range(1, count - 1)
        worst = max(idx, key=lambda i: res[i][0] / max(1, res[i][2]))
        flash, tog, interior, fmarks, tmarks = res[worst]
        pct = 100.0 * flash / max(1, interior)
        mean = 100.0 * sum(res[i][0] for i in idx) / max(1, sum(res[i][2] for i in idx))
        tmax = max(100.0 * res[i][1] / max(1, res[i][2]) for i in idx)
        ok = pct <= (args.loop_limit if loop else args.limit) or name in args.report
        failed |= not ok
        print("[%s] %-8s %2d frames%s: worst flash %.2f%% of %d interior px at frame %d (mean %.2f%%); toggles incl. motion up to %.2f%%" % (
            ("info" if name in args.report else "ok") if ok else "FAIL", name, count, " (loop)" if loop else "", pct, interior, worst, mean, tmax))
        if args.out:
            trip = [frames[(worst + d) % count].copy() for d in (-1, 0, 1)]
            for marks, col in ((tmarks, (255, 220, 0, 255)), (fmarks, (255, 0, 255, 255))):
                for (x, y) in marks:
                    for dx in (0, 1):
                        for dy in (0, 1):
                            trip[1].putpixel((x - 1 + dx, y - 1 + dy), col)
            worst_sheet.append(trip)
    if args.out and worst_sheet:
        w, h = worst_sheet[0][0].size
        sheet = Image.new("RGBA", (w * 3, h * len(worst_sheet)), (30, 30, 36, 255))
        for r, trip in enumerate(worst_sheet):
            for c, im in enumerate(trip):
                sheet.alpha_composite(im, (c * w, r * h))
        sheet.save(args.out)
        print("wrote", args.out)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
