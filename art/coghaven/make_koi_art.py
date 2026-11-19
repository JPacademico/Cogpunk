"""Source for the Koi (D4), 2026-11-12 (user: "add a new fish called Koi, it can only be fished on coghaven pond"). Run from
the repo root:

    python -P art/coghaven/make_koi_art.py [--preview FILE]

Design (my calls): a kohaku koi, the classic white fish with red-orange patches, side view facing left like vanilla's fish
items: a plump body lit from the top-left, a red cap on its head and two red saddles on its back (ember, from the palette),
flowing pale fins (the dorsal along its back, the pectoral and the long tail), a dark eye and two little barbels at its
mouth. Outlined in each material's darkest shade (pixkit); at most 16 colours.

Outputs:
    Content/Coghaven/Items/Koi.png          30x24
    Content/Coghaven/Items/JadeEyedKoi.png  30x24 (2026-11-17, user: "a jade-eyed koi a valuable item that can be sold for 2
                                            platinum coins", the Jade Vault's treasure): the same koi cast in gold, its patches
                                            crimson lacquer, its fins gilt, its eye a polished jade with a glint.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, preview  # noqa: E402
from rig import RAMP  # noqa: E402

IV, EM, ST, SM = RAMP["ivory"], RAMP["ember"], RAMP["steel"], RAMP["steam"]
RED = (EM[0], EM[1], EM[2], EM[3])

# 15 x 12 at 1x: a = ivory 2, b = ivory 3, c = ivory 4, d = ivory 5 (the body, dark to light); r/s/t = red 1/2/3 (the
# patches); f/g = the fins (steam 1/2); e = the eye (steel 1)
ROWS = (
    "...............",
    "......fgg......",
    ".....fggggf....",
    "...bcdrrsbbbff.",
    "..bcrrrsscbbbgf",
    ".bcdrrscccbbbgg",
    "bedccccdccbbbgf",
    ".bcccccbbbbabff",
    "..bbbbbaaaaff..",
    "...fgaaaa.ff...",
    "....fg.........",
    "...............",
)
KEY = {
    "a": (IV, 2), "b": (IV, 3), "c": (IV, 4), "d": (IV, 5),
    "r": (RED, 1), "s": (RED, 2), "t": (RED, 3),
    "f": (SM, 1), "g": (SM, 2),
    "e": (ST, 1),
}


def koi():
    p = Pix(15, 12)
    p.rows(0, 0, ROWS, KEY)
    p.outline()
    p.put(1, 6, ST, 1, lock=True)          # the eye
    p.put(1, 5, IV, 5, lock=True)          # its glint
    p.put(0, 7, RED, 1, lock=True)         # a barbel
    return p


G, GH = RAMP["gilt"], RAMP["ghost"]
GOLD_KEY = {
    "a": (G, 4), "b": (G, 6), "c": (G, 7), "d": (G, 8),
    "r": (RED, 1), "s": (RED, 2), "t": (RED, 3),
    "f": (G, 5), "g": (G, 8),
    "e": (GH, 2),
}


def jade_eyed_koi():
    """The Jade Vault's treasure: the koi cast in gold (gilt ramp, lit from the top-left), crimson lacquer patches, gilt fins,
    a jade eye with a glint."""
    p = Pix(15, 12)
    p.rows(0, 0, ROWS, GOLD_KEY)
    p.outline()
    p.put(1, 6, GH, 4, lock=True)          # the jade eye
    p.put(1, 5, GH, 5, lock=True)          # its glint
    p.put(2, 6, GH, 2, lock=True)
    p.put(0, 7, G, 3, lock=True)           # a barbel
    p.put(6, 4, G, 9, lock=True)           # the gold's shine
    p.put(7, 4, G, 9, lock=True)
    return p


def export_all():
    export(koi().image(), "Content/Coghaven/Items/Koi.png")
    export(jade_eyed_koi().image(), "Content/Coghaven/Items/JadeEyedKoi.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview([koi().image(), jade_eyed_koi().image()], a.preview)
    else:
        export_all()
