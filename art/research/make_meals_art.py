"""Source for the four meals of the "Proper Meal" research node (D4), 2026-11-24. Run from the repo root:

    python -P art/research/make_meals_art.py [--preview FILE]

User, 2026-11-24: "unlocks crafting recipes for 4 new meals: 1 - "blue star fruit" ... uses one of any fruit item and a mana
star. 2 - "fish on a spear" using 2 of any fish + a mushroom and a stick ... 3 and 4 - follow the same logic and create one for
ranged and summon class". My designs, item size (14x14 art px, 28x28 in game), lit from the top-left, at most 16 colours:
* Blue Star Fruit: a carambola slice turned blue by the star it was cooked with, a pale glow at its heart, a leaf.
* Fish on a Spear: a fish roasted brown on a sharpened stick, a mushroom cap pushed on below it.
* Deadeye Chili (ranged): a clay bowl of red chili with a fireblossom pepper on top and its steam.
* Firefly Jelly (summon): a stoppered jar of green jelly with a firefly glowing in it.
Each buff icon (16x16 art, 32x32) is its meal on a small plate of the meal's own colour.

Outputs: Content/Research/Meals/<Meal>.png and <Meal>Buff.png
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, preview  # noqa: E402
from rig import RAMP  # noqa: E402

DN, AE, SM, EM, OK, HD, CU, CR, CA, FE, EB, IV = (RAMP[k] for k in
    ("denim", "aether", "steam", "emerald", "oak", "hide", "copper", "crimson", "cactus", "fel", "ember", "ivory"))
OUT = "Content/Research/Meals/"

STAR = (DN[1], DN[3], DN[4], DN[5], AE[3], SM[2])
LEAF = (EM[1], EM[3], EM[4])
WOOD = (OK[0], OK[2], OK[3], OK[4])
ROAST = (HD[0], HD[2], HD[3], HD[4], HD[5], HD[6])
CAP = (CR[0], CR[2], CR[3], IV[4])
CLAY = (CU[0], CU[1], CU[2], CU[3], CU[4])
CHILI = (CR[0], CR[2], CR[3], CR[4], CR[5])
STEAM = (SM[0], SM[1], SM[2])
GLASS = (SM[0], SM[1], SM[2], SM[3])
JELLY = (FE[1], FE[2], FE[3], FE[4], FE[5])
GLOW = (EB[2], EB[3])
CORK = (OK[0], OK[3], OK[4])


def draw(rows, key, w=14, h=14, x0=0, y0=0, skip=()):
    p = Pix(w, h)
    p.rows(x0, y0, rows, key)
    p.outline(skip=skip)
    return p


def blue_star_fruit():
    key = {"a": (STAR, 1), "s": (STAR, 2), "S": (STAR, 3), "L": (STAR, 4), "W": (STAR, 5), "g": (LEAF, 1), "G": (LEAF, 2)}
    rows = (
        "........gG....",
        ".......gGa....",
        "......aSa.....",
        ".....aSLSa....",
        "aaaaaSLWLSaaaa",
        ".aSSSLWWWLSSa.",
        "..aSSLWWWLSa..",
        "...aSSLWLSa...",
        "...aSSSLSSa...",
        "..aSSsaaasSa..",
        "..aSsa...asSa.",
        ".aSsa.....asa.",
        ".aaa.......aa.",
        "..............",
    )
    p = draw(rows, key)
    p.put(6, 6, STAR, 5, lock=True)                         # the glint at its heart
    return p


def fish_on_a_spear():
    key = {"w": (WOOD, 1), "W": (WOOD, 2), "O": (WOOD, 3), "r": (ROAST, 1), "R": (ROAST, 2), "T": (ROAST, 3),
           "Y": (ROAST, 4), "H": (ROAST, 5), "c": (CAP, 1), "C": (CAP, 2), "D": (CAP, 3)}
    rows = (
        "............O.",
        "...........Ow.",
        "......RTYHOw..",
        "....RTYHYOwR..",
        "...RTYTYOwTR..",
        "..RrTTYOwYRr..",
        "..rRRTOwTRr...",
        "..rrROwRRr....",
        "...rOwrrr.....",
        "...CCC........",
        "..cCDCc.......",
        ".Ow.cc........",
        "Ow............",
        "w.............",
    )
    p = draw(rows, key)
    p.put(9, 3, ROAST, 0, lock=True)                        # the fish's eye
    return p


def deadeye_chili():
    key = {"c": (CLAY, 1), "C": (CLAY, 2), "K": (CLAY, 3), "L": (CLAY, 4), "r": (CHILI, 1), "R": (CHILI, 2), "P": (CHILI, 3),
           "Q": (CHILI, 4), "g": (LEAF, 1), "G": (LEAF, 2), "s": (STEAM, 1), "S": (STEAM, 2)}
    rows = (
        ".....S...s....",
        "....s...S.....",
        ".....s...s....",
        ".........gG...",
        "......QPPg....",
        "..RPQRPRRrR...",
        ".RPRRrRPRRrR..",
        "rLKKKKKKKKCCc.",
        ".cLKKKKKKCCc..",
        ".cKKKKKKCCCc..",
        "..cCKKKCCCc...",
        "...cCCCCcc....",
        "....cccc......",
        "..............",
    )
    return draw(rows, key, skip=(tuple(tuple(c) for c in STEAM),))


def firefly_jelly():
    key = {"o": (CORK, 1), "O": (CORK, 2), "g": (GLASS, 1), "G": (GLASS, 2), "W": (GLASS, 3), "j": (JELLY, 1), "J": (JELLY, 2),
           "K": (JELLY, 3), "L": (JELLY, 4), "y": (GLOW, 0), "Y": (GLOW, 1)}
    rows = (
        "....OOOO......",
        "....oOOo......",
        "...gWGGGg.....",
        "..gWGGGGGg....",
        "..gWGGGGGg....",
        "..gWLKKJJg....",
        "..gKLKKKJg....",
        "..gKKyYJJg....",
        "..gKKKyJjg....",
        "..gJKKJJjg....",
        "..gJJJJjjg....",
        "...gggggg.....",
        "..............",
        "..............",
    )
    return draw(rows, key)


MEALS = {"BlueStarFruit": blue_star_fruit, "FishOnASpear": fish_on_a_spear, "DeadeyeChili": deadeye_chili,
         "FireflyJelly": firefly_jelly}


def buff_icon(item_img):
    """The meal on a small pale plate, centred in 16x16."""
    p = Pix(16, 16)
    for x in range(2, 14):
        p.put(x, 14, IV, 3)
        p.put(x, 15, IV, 2)
    for x in (1, 14):
        p.put(x, 14, IV, 2)
    p.outline()
    plate = p.image()
    out = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    out.alpha_composite(plate)
    bbox = item_img.getbbox()
    crop = item_img.crop(bbox)
    out.alpha_composite(crop, ((16 - crop.width) // 2, max(0, 15 - crop.height)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    items = {name: f().image() for name, f in MEALS.items()}
    icons = {name: buff_icon(im) for name, im in items.items()}
    if a.preview:
        preview(list(items.values()) + list(icons.values()), a.preview, scale=8)
        return
    for name, im in items.items():
        export(im, OUT + name + ".png")
        export(icons[name], OUT + name + "Buff.png")


if __name__ == "__main__":
    main()
