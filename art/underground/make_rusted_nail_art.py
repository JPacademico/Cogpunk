"""Source for the Rusted Nail accessory (D4), 2026-11-03. Run from the repo root:

    python -P art/underground/make_rusted_nail_art.py [--preview FILE]

A big old nail, bent a little near its point, eaten by rust (copper patches placed by fixed hashes along the shank), a
flat head lit on its top-left rim, the point catching a glint of clean iron. Drawn at 1x (16x16), exported at 2x.

Output: Content/Underground/Items/RustedNail.png (32x32)
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Ellipse, Capsule, Canvas, cyl, dome  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

I, C = RAMP["iron"], RAMP["copper"]


def _h(x, y):
    v = (x * 374761393 + y * 668265263 + 0x5EED) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


def rusted_nail():
    """16x16: the shank from under the head (top left) to a bend and on to the point (bottom right), lit as a cylinder in
    its own space; rust in patches along it, heavier on its shadow side and towards the point (fixed hashes of each
    pixel's place along the shank, so it's the same every export), pits in the worst of it."""
    cv = Canvas()
    a, b, tip = (4.6, 4.6), (11.2, 11.6), (14.0, 15.0)
    s1 = cv.part(Xf(), Capsule(a, b, 1.9, 1.6), "iron", cyl(a, b, 1.9, lo=1, hi=4, fixed=True), rust=0.0)
    s2 = cv.part(Xf(), Capsule(b, tip, 1.6, 0.5), "iron", cyl(b, tip, 1.6, lo=1, hi=4, fixed=True), rust=0.0)
    shank = s1 | s2
    for (x, y) in sorted(shank):
        t = (x + y) / 26.0                                  # 0 at the head .. 1 at the point
        side = (x - y) * 0.7                                # + = the lower-right (shadow) side
        n = _h(x // 2, y // 2) * 0.6 + _h(x, y) * 0.4
        if n + side * 0.18 + (0.3 if 0.2 < t < 0.45 or 0.58 < t < 0.85 else 0.0) > 0.66:
            cur = cv.px[(x, y)]
            k = RAMP["iron"].index(cur) if cur in RAMP["iron"] else 2
            cv.put(x, y, C[max(1, min(3, k))])
            if n > 0.93:
                cv.put(x, y, C[1])                          # a pit
    # the head: a flat cap seen a little from above, its rim lit on the top-left
    head = cv.part(Xf.pose(-45.0, (0.0, 0.0), (3.6, 3.6)), Ellipse(0.0, 0.0, 1.9, 4.2), "iron",
                   dome(-0.9, -1.6, 4.2, lo=1, hi=4, gain=1.3, bias=0.15, fixed=True), rust=0.0)
    for (x, y) in head:
        if x + y >= 9 and _h(x, y) > 0.55:
            cv.put(x, y, C[2])                              # rust creeping round the cap's underside
    cv.put(2, 2, WHITE)                                     # a glint on the head's rim
    cv.put(14, 14, I[4])                                    # the point, still sharp under the rust
    return to_image(cv.px, 0, 0, 16, 16)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    im = rusted_nail()
    if args.preview:
        big = im.resize((im.width * 12, im.height * 12), Image.NEAREST)
        bg = Image.new("RGBA", (big.width * 2 + 20, big.height + 20), (36, 40, 48, 255))
        bg.paste((150, 180, 210, 255), (big.width + 15, 0, bg.width, bg.height))
        bg.alpha_composite(big, (5, 10))
        bg.alpha_composite(big, (big.width + 15, 10))
        bg.save(args.preview)
        print("preview", args.preview)
    else:
        export(im, "Content/Underground/Items/RustedNail.png")
