"""Source for the Rainbow Robe (D4), 2026-11-24 (user: "add a new node called "rgbt" ... unlocks ... the crafting of the rainbow
robe a powerfull mage chest piece"). Run from the repo root:

    python -P art/research/make_rainbow_robe_art.py [--preview FILE]

The Jade Robe's cut (art/gems/make_jade_art.py: the 1.4 body sheet, the skirt that follows each leg frame, the item icon), its
silk re-dyed in the seven gems and jade as horizontal bands, two art pixels each from the collar down: ruby, amber, topaz,
jade, emerald, sapphire, amethyst, diamond, round again. Each jade shade maps to the same step of the band's gem ramp
(crimson, copper, brass, ghost, emerald, denim, amethyst, steel), so the folds and the light stay where the robe's own
shading put them; the gilt collar, placket, sash, cuffs and hem are kept.

Outputs (Content/Research/Armor/):
    RainbowRobe.png (item), RainbowRobe_Body.png (360x224), RainbowRobe_Legs.png (40x1120)
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gems"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
import make_jade_art as J  # noqa: E402
from rig import RAMP  # noqa: E402

OUT = "Content/Research/Armor/"
JADE = [tuple(c) for c in RAMP["ghost"]]               # the robe's silk, dark to light (index 0 the outline)
CU, BR, EM, DN, AM, ST, CR, GH = (RAMP[k] for k in ("copper", "brass", "emerald", "denim", "amethyst", "steel", "crimson", "ghost"))
BANDS = [                                              # six steps each, the jade ramp's order (0 outline .. 5 shine)
    CR,                                                # ruby
    (CU[0], CU[1], CU[2], CU[3], CU[4], BR[5]),        # amber
    BR,                                                # topaz
    GH,                                                # jade
    (EM[0], EM[1], EM[2], EM[3], EM[4], EM[5]),        # emerald
    DN,                                                # sapphire
    AM,                                                # amethyst
    (ST[2], ST[4], ST[5], ST[6], ST[7], ST[8]),        # diamond
]
BAND_PX = 2
TOP = 13                                               # the collar's row in a 20x28 cell: the bands count from it


def dye(img, cell_h=J.FH, top=TOP):
    """Each jade pixel takes its band's gem ramp at the same step; the band from the row inside its cell."""
    out = img.copy()
    px = out.load()
    for y in range(img.height):
        band = BANDS[((y % cell_h) - top) // BAND_PX % len(BANDS)]     # 1x: the art row inside its cell
        for x in range(img.width):
            c = px[x, y]
            if c[3] == 0:
                continue
            rgb = c[:3]
            if rgb in JADE:
                k = JADE.index(rgb)
                px[x, y] = tuple(band[min(k, len(band) - 1)]) + (255,)
    return out


ICON_BANDS = [BANDS[0], BANDS[2], BANDS[4], BANDS[5], BANDS[6]]   # the icon: five gems, two shades each (the 16-colour cap)


def dye_icon(img):
    """The item icon (13x15 art px): five gem bands, each in two shades (the jade's dark half -> the gem's mid step, its
    light half -> the gem's light step), so the icon stays within an item's 16 colours."""
    out = img.copy()
    px = out.load()
    for y in range(img.height):
        band = ICON_BANDS[(y // BAND_PX) % len(ICON_BANDS)]
        for x in range(img.width):
            c = px[x, y]
            if c[3] == 0 or c[:3] not in JADE:
                continue
            k = JADE.index(c[:3])
            px[x, y] = tuple(band[2] if k <= 2 else band[4]) + (255,)
    return out


def build():
    body = J.body_sheet()
    legs = J.legs_sheet()
    icon = J.robe_icon(body)
    return {"RainbowRobe_Body": dye(body.image()), "RainbowRobe_Legs": dye(legs.image()), "RainbowRobe": dye_icon(icon.image())}


def save(img, rel):
    path = os.path.join(os.getcwd(), rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    big = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    big.save(path)
    print("wrote %s (%dx%d)" % (rel, big.width, big.height))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    imgs = build()
    if a.preview:
        tiles = [imgs["RainbowRobe"], imgs["RainbowRobe_Body"], imgs["RainbowRobe_Legs"].crop((0, 0, 20, 28 * 4))]
        w = sum(t.width for t in tiles) + 40
        h = max(t.height for t in tiles) + 20
        out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
        for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
            band = Image.new("RGBA", (w, h), bg + (255,))
            out.alpha_composite(band, (0, row * h))
            x = 10
            for t in tiles:
                out.alpha_composite(t, (x, row * h + 10))
                x += t.width + 10
        out.resize((out.width * 4, out.height * 4), Image.NEAREST).save(a.preview)
        print("preview", a.preview)
        return
    for name, img in imgs.items():
        save(img, OUT + name + ".png")


if __name__ == "__main__":
    main()
