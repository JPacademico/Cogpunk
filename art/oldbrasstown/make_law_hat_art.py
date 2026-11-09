"""Source for the Law Hat (D4), 2026-11-09 (user: "a new accessory that can be dropped by the sheriff mini boss (20% chance)
called law hat; it should give +10% ranged crit to weapons that consume bullets"). Run from the repo root:

    python -P art/oldbrasstown/make_law_hat_art.py

The Sheriff's own hat (westbots.cowboy_hat, the helper his sprite uses: a pinched leather crown, a band of gilt conchos
with his gilt star, a wide brim curling up at its ends), drawn as an item at 1x, finished like his sprite (despeckle, the
lit outline), exported at 2x nearest-neighbour. Lit from the top-left; long ramps (D4 rule 18), at most 16 colours.

Output:
    Content/OldBrassTown/Items/LawHat.png   about 38x22 (the hat cropped to its pixels)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP, Canvas, cowboy_hat, finish  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/OldBrassTown/Items/LawHat.png"


STAR = ((0, -2, 8), (-2, -1, 7), (-1, -1, 8), (0, -1, 9), (1, -1, 8), (2, -1, 6), (-1, 0, 8), (0, 0, 9), (1, 0, 6),
        (-1, 1, 6), (1, 1, 4))


def law_hat():
    cv = Canvas()
    cowboy_hat(cv, (9.0, 0.6), 17.4, 7.0, 9.6, star=False, lo=3)
    finish(cv)
    # the law's star on the band, stamped after the despeckle (a 3 px feature would be softened away): five points, lit
    # from the top-left (gilt 9 to 4)
    sx, sy = 5, 5
    for (dx, dy, k) in STAR:
        cv.put(sx + dx, sy + dy, RAMP["gilt"][k])
    xs = [x for (x, _) in cv.px]
    ys = [y for (_, y) in cv.px]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0 + 1, max(ys) - y0 + 1
    return to_image(cv.px, x0, y0, w, h)


if __name__ == "__main__":
    export(law_hat(), OUT)
