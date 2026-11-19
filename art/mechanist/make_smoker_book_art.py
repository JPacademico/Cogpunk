"""Source for the Smoker Book (D4), 2026-11-19. Run from the repo root:

    python -P art/mechanist/make_smoker_book_art.py [--preview FILE]

User, 2026-11-19: "add a new mechanist weapon that can be found on hell chests called "smoker book" a weapon that shoots mid
range big area (10% smaller than player in high) quick smoke trail that pieces and does damage to everything onthe way,
costs 8 steam". The look is my call:
* The book: a soot-blackened iron-bound tome (the iron ramp), its spine on the left, brass corner caps and a brass clasp,
  a round pressure gauge set in the cover (a pale dial, the needle in the red), ivory page edges down its right side, and
  a little brass smokestack on its top edge, a curl of soot over it. Held like vanilla's spell tomes (useStyle Shoot).
* The smoke: four puffs of soot (iron greys into the steam's), each a cluster of round lobes shaded as one soft mass lit
  from the top-left, a darker underside (no half-transparent pixels: the game fades the whole puff as it ages).

Outputs (Content/Mechanist/Weapons/):
    SmokerBook.png          the item, 28x34 (14x17 at 1x)
    SmokerBookSmoke.png     4 puffs of 20x20 at 1x (40x40), 1 px apart (2 at 2x)
"""
import argparse
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Mechanist/Weapons/"
IR, G, IV, SM, K = (RAMP[k] for k in ("iron", "gilt", "ivory", "steam", "crimson"))
PUFF = 20
PUFFS = 4

# The book by hand (14 x 17): o iron outline, 1-4 iron shades, g/G/H brass (gilt 3/6/8), p/P pages (ivory 3/5), d the dial,
# n the needle, s the soot curl
BOOK = (
    "........ss....",
    ".......s..s...",
    "........gG....",
    "........gH....",
    ".oooooooggoo..",
    "o1222222222Pp.",
    "o1GH33333HGPp.",
    "o1H3333333HPp.",
    "o13333gGg33Pp.",
    "o1333gdddg3Pp.",
    "o1333Gdnd33Pp.",
    "o1333gdddg3Pp.",
    "o13333ggg33Pp.",
    "o1333333333Pp.",
    "o1H333333gHPp.",
    "o1GHo2222oGPp.",
    ".oooooooooooo.",
)
BOOK_LEGEND = {"o": IR[0], "1": IR[1], "2": IR[2], "3": IR[1], "4": IR[3], "g": G[3], "G": G[6], "H": G[8], "p": IV[3],
               "P": IV[5], "d": IV[5], "n": K[4], "s": SM[1]}


def book():
    px = {}
    for y, row in enumerate(BOOK):
        for x, ch in enumerate(row):
            if ch != ".":
                px[(x, y)] = BOOK_LEGEND[ch]
    # the cover's leather grain: a lit stripe along the top, a few scuffs
    for (x, y) in ((3, 7), (4, 7), (8, 13), (4, 12)):
        if px.get((x, y)) == IR[1]:
            px[(x, y)] = IR[2]
    return to_image(px, 0, 0, 14, 17)


def puff(seed):
    """A soot puff: lobes (circles) round the middle make its shape; it is shaded as one soft mass (a bevel: the light from
    the top-left falls on the edges facing it, the far edges sink into shadow), so no seams show between the lobes."""
    rnd = random.Random(seed)
    lobes = [(10.0, 10.5, 6.2)]
    for k in range(5):
        a = k / 5.0 * math.tau + rnd.uniform(-0.4, 0.4)
        lobes.append((10.0 + math.cos(a) * rnd.uniform(4.0, 5.0), 10.5 + math.sin(a) * rnd.uniform(3.4, 4.6), rnd.uniform(3.2, 4.4)))
    mask = [[0.0] * (PUFF + 8) for _ in range(PUFF + 8)]           # 4 px of margin round the cell
    shape = set()
    for y in range(PUFF):
        for x in range(PUFF):
            if any((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r for (cx, cy, r) in lobes):
                shape.add((x, y))
                mask[y + 4][x + 4] = 1.0

    def soft(x, y):                                               # the mask averaged over a 5 x 5 square
        tot = 0.0
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                yy, xx = y + 4 + dy, x + 4 + dx
                if 0 <= yy < PUFF + 8 and 0 <= xx < PUFF + 8:
                    tot += mask[yy][xx]
        return tot / 25.0

    ramp = (IR[1], IR[2], IR[3], SM[0], SM[1])                     # soot greys, lighter than iron: smoke, not stone
    px = {}
    for (x, y) in shape:
        v = soft(x + 2, y + 2) - soft(x - 2, y - 2)               # > 0 where the light's side is open (the lit rim)
        k = 4 if v > 0.5 else 3 if v > 0.22 else 2 if v > -0.18 else 1 if v > -0.5 else 0
        if (x + 1, y) not in shape or (x, y + 1) not in shape:
            k = min(k, 1)                                         # the underside's edge
        px[(x, y)] = ramp[k]
    return to_image(px, 0, 0, PUFF, PUFF)


def smoke_sheet():
    out = Image.new("RGBA", (PUFF, PUFFS * (PUFF + 1) - 1), (0, 0, 0, 0))
    for k in range(PUFFS):
        out.alpha_composite(puff(1900 + k * 7), (0, k * (PUFF + 1)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    b, s = book(), smoke_sheet()
    export(b, OUT + "SmokerBook.png")
    export(s, OUT + "SmokerBookSmoke.png")
    if args.preview:
        sc = 8
        sheet = Image.new("RGBA", (14 * sc + PUFF * sc * PUFFS + 60, max(17, PUFF) * sc * 2 + 30), (20, 20, 24, 255))
        for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
            y0 = 10 + row * (PUFF * sc + 10)
            band = Image.new("RGBA", (sheet.width - 20, PUFF * sc), bg + (255,))
            band.alpha_composite(b.resize((14 * sc, 17 * sc), Image.NEAREST), (0, 0))
            for k in range(PUFFS):
                p = s.crop((0, k * (PUFF + 1), PUFF, k * (PUFF + 1) + PUFF))
                band.alpha_composite(p.resize((PUFF * sc, PUFF * sc), Image.NEAREST), (14 * sc + 10 + k * PUFF * sc, 0))
            sheet.alpha_composite(band, (10, y0))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
