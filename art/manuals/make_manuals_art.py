"""Source for the crafting manuals (D4), 2026-11-17. Run from the repo root:

    python -P art/manuals/make_manuals_art.py [--preview FILE]

User, 2026-11-17: every Cogpunk boss leaves a manual on its first defeat ("a visual cue so players don't miss it (floaty and a
glow)"): the Jade-shaper Manual (Jadey), the Scrap Manual (Trash-Tr0m), the Sheriff's Law Book (the Cursed Conductor) and the
Sticky Pages (the Tar Tyrant). Each is a small book seen in three-quarter view, lit from the top-left (rig.py parts, 1x,
exported 2x): a cover in its boss's material, a spine with two trim bands, the page block showing at the fore-edge and the
foot, the corners capped, an emblem on the cover. The Sticky Pages are loose pages glued together with tar instead.

Each also gets an aura (`_Aura`, 24 x 24 at 1x): a ring of sparkle pixels in its colour with four short rays, drawn added
in game behind the floating book (opaque pixels, faded in code: D4 rule 9).

Outputs: Content/Manuals/Items/{JadeShaperManual,ScrapManual,SheriffsLawBook,StickyPages,FungiManual}.png (28 x 32) and *_Aura.png (48 x 48).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import (RAMP, Xf, Poly, Ellipse, Canvas, flat, finish)  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Manuals/Items/"
GH, G, K, ST, IV, CU, HI, TAR, BR, EM = (RAMP[k] for k in ("ghost", "gilt", "crimson", "steel", "ivory", "copper", "hide", "tar",
                                                           "brass", "ember"))
W, H = 14, 16


def cover_shade(lo, hi):
    """A flat cover lit from the top-left: the light corner bright, the far edge one step down."""
    def shade(i):
        d = i.lx + i.ly
        return hi if d < 9.0 else lo + 1 if d < 17.0 else lo
    return shade


def book(cover, cover_lo, cover_hi, trim, trim_k, emblem):
    """A closed book: spine on the left, the page block at the fore-edge and the foot, capped corners, an emblem."""
    cv = Canvas()
    cv.part(Xf(), Poly([(3.0, 2.0), (13.0, 2.0), (13.0, 15.0), (3.0, 15.0)]), "ivory", lambda i: 4 if (int(i.ly) % 2) else 3, rust=0.0)
    cv.part(Xf(), Poly([(2.0, 1.0), (12.0, 1.0), (12.0, 14.0), (2.0, 14.0)]), cover, cover_shade(cover_lo, cover_hi), rust=0.0)
    cv.part(Xf(), Poly([(0.6, 1.0), (3.2, 1.0), (3.2, 14.6), (0.6, 14.6)]), cover, lambda i: max(1, cover_lo - 1 if i.lx > 2.0 else cover_lo),
            rust=0.0)
    for y in (3, 11):
        for x in range(1, 3):
            cv.put(x, y, trim[trim_k + (1 if x == 1 else 0)])
    for (x, y) in ((11, 1), (11, 2), (10, 1), (11, 13), (10, 13), (11, 12)):
        cv.put(x, y, trim[trim_k + (1 if y < 5 else 0)])
    emblem(cv)
    finish(cv)
    return cv


def jade_emblem(cv):
    """A jade coin with its square hole and a gilt rim (Jadey's coins)."""
    cv.part(Xf(), Ellipse(7.5, 7.5, 3.4, 3.4), "gilt", lambda i: 8 if i.lx + i.ly < 14.0 else 6 if i.lx + i.ly < 16.0 else 4, rust=0.0,
            outline=False)
    cv.part(Xf(), Ellipse(7.5, 7.5, 2.3, 2.3), "ghost", lambda i: 5 if i.lx + i.ly < 14.4 else 4, rust=0.0, outline=False)
    for (x, y) in ((7, 7), (8, 7), (7, 8), (8, 8)):
        cv.put(x, y, GH[1])                                     # the square hole


def scrap_emblem(cv):
    """A brass cog, a rust patch and two rivets on the steel cover."""
    for a in range(0, 360, 45):
        t = math.radians(a)
        cv.put(int(round(7.5 + 3.2 * math.cos(t) - 0.5)), int(round(7.5 + 3.2 * math.sin(t) - 0.5)), BR[3])
    cv.part(Xf(), Ellipse(7.5, 7.5, 2.4, 2.4), "brass", lambda i: 5 if i.lx + i.ly < 14.6 else 3, rust=0.0)
    cv.put(7, 7, BR[0])
    for (x, y) in ((4, 11), (5, 11), (5, 12), (10, 3)):
        cv.put(x, y, CU[2] if (x + y) % 2 else CU[3])
    for (x, y) in ((4, 3), (10, 11)):
        cv.put(x, y, ST[7])


def law_emblem(cv):
    """A brass sheriff's star over a gilt title band on the leather cover."""
    for x in range(4, 11):
        cv.put(x, 3, G[7] if x < 7 else G[5])
    pts = []
    for k in range(10):
        r = 3.4 if k % 2 == 0 else 1.5
        t = math.radians(-90 + k * 36)
        pts.append((7.5 + r * math.cos(t), 8.4 + r * math.sin(t)))
    cv.part(Xf(), Poly(pts), "brass", lambda i: 5 if i.lx + i.ly < 15.6 else 4, rust=0.0, outline=False)
    cv.put(7, 8, BR[3])                                         # the star's boss


def mushroom_emblem(cv):
    """A glowing mushroom of the blue biome on the blue cover (the Fungimancer's, 2026-11-19): a pale stalk, a bright cap
    with three spots."""
    DN, SM = RAMP["denim"], RAMP["steam"]
    cv.part(Xf(), Poly([(6.6, 8.4), (8.4, 8.4), (8.6, 12.0), (6.4, 12.0)]), "steam", lambda i: 2 if i.lx < 7.6 else 1, rust=0.0,
            outline=False)
    cv.part(Xf(), Ellipse(7.5, 7.6, 3.8, 2.6), "denim", lambda i: 5 if i.lx + i.ly < 13.4 else 4, rust=0.0, outline=False)
    for (x, y) in ((6, 6), (9, 7), (7, 8)):
        cv.put(x, y, SM[3])
    for x in range(5, 11):
        cv.put(x, 9, DN[2])                                     # the gills' shadow under the cap


def sticky_pages():
    """Loose pages glued together by tar: three ivory leaves askew, tar oozing between them and dripping off the foot."""
    cv = Canvas()
    for (xf, k) in ((Xf.pose(-8.0, (7.0, 8.0)), 2), (Xf.pose(6.0, (7.0, 8.0), (0.6, 0.0)), 3), (Xf.pose(-2.0, (7.0, 8.0), (-0.4, 0.4)), 4)):
        cv.part(xf, Poly([(2.0, 1.5), (12.0, 1.5), (12.0, 14.0), (2.0, 14.0)]), "ivory",
                lambda i, k=k: k + 1 if i.lx + i.ly < 9.0 else k, rust=0.0)
    for y in (5, 7, 9):
        for x in range(4, 10):
            if (x + y) % 3:
                cv.put(x, y, IV[2])                             # lines of writing
    for (x, y, k) in ((6, 1, 1), (7, 1, 2), (6, 2, 1), (10, 6, 1), (11, 6, 2), (11, 7, 1), (3, 10, 1), (3, 11, 2), (4, 11, 1),
                      (7, 13, 1), (8, 13, 2), (7, 14, 1), (8, 14, 1), (8, 15, 1)):
        cv.put(x, y, TAR[k])
    cv.put(8, 13, TAR[4])                                       # the tar's gloss
    cv.put(6, 1, TAR[3])
    finish(cv)
    return cv


def aura(ramp, hi):
    """A ring of sparkle pixels and four short rays (24 x 24): drawn added in game, pulsing."""
    cv = Canvas()
    c = 12.0
    for a in range(0, 360, 10):
        t = math.radians(a)
        r = 9.6 + (0.6 if a % 30 == 0 else 0.0)
        x, y = int(math.floor(c + r * math.cos(t))), int(math.floor(c + r * math.sin(t)))
        cv.put(x, y, ramp[hi] if a % 30 == 0 else ramp[hi - 1])
    for a in (45, 135, 225, 315):
        t = math.radians(a)
        for r, k in ((11.4, hi), (12.4, hi - 1)):
            cv.put(int(math.floor(c + r * math.cos(t))), int(math.floor(c + r * math.sin(t))), ramp[k])
    for a in range(0, 360, 30):
        t = math.radians(a + 15)
        cv.put(int(math.floor(c + 6.6 * math.cos(t))), int(math.floor(c + 6.6 * math.sin(t))), ramp[hi - 2])
    return cv


def manuals():
    return {
        "JadeShaperManual": (book("ghost", 2, 4, G, 6, jade_emblem), aura(GH, 5)),
        "ScrapManual": (book("steel", 3, 6, CU, 2, scrap_emblem), aura(CU, 4)),
        "SheriffsLawBook": (book("hide", 2, 5, G, 6, law_emblem), aura(G, 9)),
        "StickyPages": (sticky_pages(), aura(EM, 3)),
        "FungiManual": (book("denim", 1, 3, G, 6, mushroom_emblem), aura(RAMP["denim"], 5)),
    }


def image(cv, w, h):
    return to_image(cv.px, 0, 0, w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    shown = []
    for name, (bk, au) in manuals().items():
        export(image(bk, W, H), OUT + name + ".png")
        export(image(au, 24, 24), OUT + name + "_Aura.png")
        shown += [image(bk, W, H), image(au, 24, 24)]
    if args.preview:
        scale = 6
        w = sum(im.width * scale + 8 for im in shown) + 8
        h = max(im.height for im in shown) * scale + 16
        out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
        for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
            band = Image.new("RGBA", (w, h), bg + (255,))
            x = 8
            for im in shown:
                band.alpha_composite(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, 8))
                x += im.width * scale + 8
            out.paste(band, (0, row * h))
        out.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
