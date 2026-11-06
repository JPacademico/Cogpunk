"""Source for the Hawk Eye, the Coghawk's accessory (D4), 2026-11-04. Run from the repo root:

    python -P art/desert/make_hawk_eye_art.py [--preview FILE]

Design (user, 2026-11-04: "the Coghawk has a chance to drop a hawk eye, an accessory with +5% ranged crit"): the
Coghawk's eye in its brass housing: a round brass lens mount with an amber iris (Ember), a dark pupil and a hot glint,
a brass feather swept back from it like the bird's brow, and a cog's teeth round its rim. Lit from the top-left.

Output: Content/Desert/Items/HawkEye.png (28x28: 14x14 at 1x, exported at 2x).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Canvas, face  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

I, B, E = RAMP["iron"], RAMP["brass"], RAMP["ember"]


def despeckle(cv):
    changes = {}
    for (x, y), col in cv.px.items():
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


def ring(cv, cx, cy, r_out, r_in, ramp, lo, hi):
    """A lit ring (a lens mount, a porthole), per pixel: its own ramp-0 outline outside, lit on the top-left."""
    r = RAMP[ramp]
    pts = set()
    for y in range(int(cy - r_out - 1), int(cy + r_out + 2)):
        for x in range(int(cx - r_out - 1), int(cx + r_out + 2)):
            if r_in <= math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r_out:
                pts.add((x, y))
    for (x, y) in pts:
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        outer = any((x + ox, y + oy) not in pts and math.hypot(x + ox + 0.5 - cx, y + oy + 0.5 - cy) > r_out
                    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if outer:
            cv.put(x, y, r[0])
            continue
        lightness = ((x + 0.5 - cx) * -0.6 + (y + 0.5 - cy) * -0.75) / max(0.5, d)
        cv.put(x, y, r[hi] if lightness > 0.35 else (r[hi - 1] if lightness > -0.35 else r[lo]))
    return pts


def hawk_eye_icon():
    """14x14: a brass lens mount (cog teeth on its rim) round an amber iris with a dark pupil and a hot glint, a brass
    brow feather swept back over it."""
    cv = Canvas()
    feather = Poly([(3.4, 4.6), (6.4, 1.4), (10.4, 0.0), (14.0, 0.0), (12.2, 1.6), (14.0, 2.2), (10.6, 4.2), (7.0, 5.6)])
    finner = cv.part(Xf(), feather, "brass", face((-0.5, -0.6, 0.6), lo=3, hi=4, fixed=True), rust=0.0)
    for (x, y) in ((7, 3), (9, 2), (11, 1), (12, 3)):          # its vanes
        if (x, y) in finner:
            cv.put(x, y, B[2])
    cx, cy = 6.5, 8.5
    for k in range(8):                                          # the cog teeth round the rim
        a = math.radians(k * 45 + 22.5)
        q = (int(math.floor(cx + math.cos(a) * 5.9)), int(math.floor(cy + math.sin(a) * 5.9)))
        cv.put(q[0], q[1], B[0])
    ring(cv, cx, cy, 5.4, 3.3, "brass", 2, 5)
    for y in range(int(cy - 4), int(cy + 4)):
        for x in range(int(cx - 4), int(cx + 4)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < 3.3:
                lit_side = (x + 0.5 - cx) + (y + 0.5 - cy) < -0.6
                cv.put(x, y, E[1] if d > 2.6 else (E[3] if lit_side else E[2]))
    for (x, y) in ((6, 8), (7, 8), (6, 9), (7, 9)):
        cv.put(x, y, I[0])                                      # the pupil
    cv.put(5, 7, WHITE)                                         # a hot glint
    return to_image(cv.px, 0, 0, 14, 14)


def export_all():
    export(hawk_eye_icon(), "Content/Desert/Items/HawkEye.png")


def preview(path):
    im = hawk_eye_icon()
    out = Image.new("RGBA", (36, 18), (36, 40, 48, 255))
    out.alpha_composite(im, (2, 2))
    light = Image.new("RGBA", (18, 18), (150, 180, 210, 255))
    light.alpha_composite(im, (2, 2))
    out.paste(light, (18, 0))
    out.resize((out.width * 8, out.height * 8), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
