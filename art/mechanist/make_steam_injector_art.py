"""Source for the Steam Injector (D4), 2026-11-12 (user: "add a new buff station called steam injector; sold by the
friendo-bot npc costing 35 gold; upon use (right mouse), it gives +10 max steam and -5% steam consumption"). Run from the
repo root:

    python -P art/mechanist/make_steam_injector_art.py [--preview FILE]

Design (my calls): a 2x3 tile buff station like vanilla's (the Ammo Box, the Sharpening Station): a brass pressure tank on a
cast-iron foot, two steel hoops riveted round it, a gauge with a red needle on its front and a red valve wheel on top; on
its right a big brass injector, a syringe with a glass window full of steam, a steel plunger and its needle, fed by a copper
pipe from the tank. Lit from the top-left; outlines in each material's darkest shade (pixkit); at most 16 colours.

Outputs:
    Content/Mechanist/Stations/SteamInjectorTile.png            36x56 (2 x 3 tiles, 18 px stride, the last row 18 tall)
    Content/Mechanist/Stations/SteamInjectorTile_Highlight.png  its smart-interact outline (white)
    Content/Mechanist/Stations/SteamInjector.png                32x50, the item
    Content/Mechanist/Stations/SteamInjection.png               32x32, the buff icon
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

BR, ST, K, C, SM, IV = RAMP["brass"], RAMP["steel"], RAMP["crimson"], RAMP["copper"], RAMP["steam"], RAMP["ivory"]
IRON = (ST[0], ST[1], ST[3], ST[3], ST[5])               # the cast-iron foot and the hoops (4 shades: the cap)
OUT = "Content/Mechanist/Stations/"
W, H = 16, 25                                             # 2 x 3 tiles at 1x, the bottom row 9 tall (sinks 1 into the floor)


def injector():
    p = Pix(W, H)
    # the foot: a wide cast-iron plinth with two bolts
    p.rect(0, 21, 12, 24, IRON, 2)
    p.rect(1, 21, 11, 21, IRON, 4)
    for x in (2, 10):
        p.put(x, 23, IRON, 4)
    # the tank: a brass cylinder lit on its left
    for x in range(2, 11):
        k = 4 if x <= 3 else 3 if x <= 7 else 2
        p.rect(x, 6, x, 20, BR, k)
    p.rect(3, 5, 9, 5, BR, 3)                              # its rounded shoulder
    p.rect(4, 4, 8, 4, BR, 2)
    for x in (3, 4):
        p.put(x, 7, BR, 5)                                 # a highlight down the lit side
        p.put(3, 8 + x, BR, 5)
    # two steel hoops with rivets
    for y in (8, 17):
        for x in range(2, 11):
            p.put(x, y, IRON, 3 if x <= 4 else 2)
    # the gauge: an ivory face in a steel rim, a red needle
    for (x, y) in ((5, 11), (6, 11), (7, 11), (4, 12), (8, 12), (4, 13), (8, 13), (4, 14), (8, 14), (5, 15), (6, 15), (7, 15)):
        p.put(x, y, IRON, 2)
    p.rect(5, 12, 7, 14, IV, 5)
    # the valve wheel on its stem
    p.rect(6, 2, 6, 3, IRON, 3)
    p.rect(4, 1, 8, 1, K, 3)
    p.put(4, 2, K, 2)
    p.put(8, 2, K, 2)
    p.rect(4, 0, 8, 0, K, 4)
    # the copper pipe from the tank to the injector
    p.rect(11, 10, 12, 10, BR, 2)
    p.put(11, 11, BR, 1)
    # the injector: a brass barrel with a glass window of steam, a steel plunger, the needle
    p.rect(12, 7, 14, 17, BR, 3)
    p.rect(12, 7, 12, 17, BR, 4)
    p.rect(13, 9, 13, 15, SM, 2)
    p.rect(12, 5, 14, 5, IRON, 3)                          # the plunger's T
    p.rect(13, 6, 13, 6, IRON, 2)
    p.rect(13, 18, 13, 20, IRON, 4)                        # the needle
    p.put(13, 20, IRON, 2)
    p.outline()
    # stamps after the outline: the needle of the gauge, the rivets' glints
    p.put(6, 13, K, 3, lock=True)
    p.put(7, 12, K, 3, lock=True)
    for (x, y) in ((3, 8), (9, 8), (3, 17), (9, 17)):
        p.put(x, y, IRON, 4, lock=True)
    return p


def tile_sheet(img):
    """The 1x object cut into 8 px tiles and laid out with 1 px gaps (2 x 3, the bottom row 9 tall): vanilla's 18 px
    stride at 2x."""
    rows = ((0, 8), (8, 8), (16, 9))
    out = Image.new("RGBA", (2 * 9, 28), (0, 0, 0, 0))
    for r, (y0, h) in enumerate(rows):
        for c in range(2):
            tile = img.crop((c * 8, y0, c * 8 + 8, y0 + h))
            out.alpha_composite(tile, (c * 9, r * 9))
    return out


def highlight(img):
    """White on the silhouette's edge pixels (a pixel with an empty 4-neighbour)."""
    w, h = img.size
    src = img.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or src[nx, ny][3] == 0:
                    dst[x, y] = (255, 255, 255, 255)
                    break
    return out


def buff_icon():
    p = Pix(16, 16)
    # a brass syringe lying diagonally, steam in its window, a puff out of its needle
    for k in range(9):
        x, y = 3 + k, 12 - k
        p.put(x, y, BR, 3)
        p.put(x + 1, y, BR, 2)
        p.put(x, y - 1, BR, 4)
    for k in range(2, 6):
        p.put(3 + k, 12 - k, SM, 2)
    p.put(13, 2, IRON, 3)
    p.put(14, 1, IRON, 3)
    p.put(2, 13, IRON, 4)
    p.put(1, 14, IRON, 4)
    p.outline()
    for (x, y, k) in ((1, 9, 2), (2, 9, 3), (1, 10, 2), (3, 8, 2), (12, 13, 2), (13, 13, 3), (13, 12, 2)):
        p.put(x, y, SM, k, lock=True)
    return p


def export_all():
    obj = injector().image()
    sheet = tile_sheet(obj)
    export(sheet, OUT + "SteamInjectorTile.png")
    export(tile_sheet(highlight(obj)), OUT + "SteamInjectorTile_Highlight.png")   # traced whole, then cut
    export(obj, OUT + "SteamInjector.png")
    export(buff_icon().image(), OUT + "SteamInjection.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview([injector().image(), buff_icon().image()], a.preview)
    else:
        export_all()
