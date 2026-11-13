"""Source for the Combinator and its parts (D4), 2026-11-12 (user: "the first half / the second half / combinator
blueprint ... combined to craft a new hardmode crafting station called The Combinator ... it should open a stylized
cogpunk menu"). Run from the repo root:

    python -P art/combinator/make_combinator_art.py [--preview FILE]

Design (my calls), lit from the top-left, outlined in each material's darkest shade (pixkit), at most 16 colours an item:
* The Combinator (a 4x3 tile, 4 frames): a steam press of brass and iron. A hopper on each side (the base's, tagged with a
  jade stud, and the augment's, tagged red) feeds pipes into the press in the middle, where a big cog turns (a quarter of a
  tooth a frame) under a gauge; a furnace window glows under it (flickering) and the output tray sits in front, on a
  cast-iron plinth; a steam stack on top.
* The First Half and The Second Half: the press's core split down the middle, a half cog on the outer side of each, the cut
  side showing the gears inside; the first half carries the hopper, the second the press head and its chute.
* The Combinator Blueprint: a rolled-up blueprint, blue paper with white lines of a cog on it, sealed with red wax; its beam
  (a column of light, drawn added on and faded in code) and its ring of light.
* The window (UI): a brass-framed iron panel (a nine-slice: rivets only in the corners, plain edges, so it stretches clean),
  brass slots with corner rivets, a gilt product slot ringed with cog teeth and jade studs, brass buttons (normal and lit),
  and a little cog with a question mark for the help.

Outputs (Content/Combinator/):
    Tiles/CombinatorTile.png (72x224: 4 x 3 tiles, 18 px stride, 4 frames of 56), Tiles/CombinatorTile_Highlight.png
    Items/TheCombinator.png, Items/TheFirstHalf.png, Items/TheSecondHalf.png, Items/CombinatorBlueprint.png,
    Items/CombinatorBlueprint_Beam.png (16x32), Items/CombinatorBlueprint_Aura.png
    UI/CombinatorPanel.png (48x48), UI/CombinatorSlot.png (52x52), UI/CombinatorProductSlot.png (60x60),
    UI/CombinatorButton.png (24x48: normal over lit), UI/CombinatorHelp.png (22x44: normal over lit)
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, preview  # noqa: E402
from rig import RAMP  # noqa: E402

BR, ST, K, EM, SM, JD, DN, GI = (RAMP[k] for k in ("brass", "steel", "crimson", "ember", "steam", "ghost", "denim", "gilt"))
IRON = (ST[0], ST[1], ST[3], ST[5])
OUT = "Content/Combinator/"


# --- the station --------------------------------------------------------------------------------------------------------------
def cog(p, cx, cy, r_root, r_tip, teeth, angle, ramp, lo, hi):
    """A cog drawn fresh at `angle` from its polar shape (the teeth on cos(teeth * theta)), lit from the top-left; a dark hub."""
    for y in range(int(cy - r_tip - 1), int(cy + r_tip + 2)):
        for x in range(int(cx - r_tip - 1), int(cx + r_tip + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            th = math.atan2(dy, dx) - angle
            outer = r_tip if math.cos(teeth * th) > 0.15 else r_root
            if r > outer:
                continue
            lit = -(dx + dy) / (math.sqrt(2) * max(1.0, r))
            k = lo + int(round((hi - lo) * (0.5 + 0.5 * lit)))
            if r < 1.6:
                k = lo
            p.put(x, y, ramp, max(lo, min(hi, k)))


def station(frame):
    p = Pix(32, 25)
    # the plinth
    p.rect(1, 21, 30, 24, IRON, 1)
    p.rect(2, 21, 29, 21, IRON, 2)
    for x in (3, 10, 21, 28):
        p.put(x, 23, IRON, 3)
    # the press housing in the middle
    p.rect(9, 5, 22, 20, BR, 2)
    p.rect(9, 5, 22, 6, BR, 3)
    p.rect(9, 5, 9, 20, BR, 3)
    # the hoppers: funnels wide at the top, each with its tag stud, and a pipe down into the press
    for side in (0, 1):
        x0 = 1 if side == 0 else 22
        for row in range(7):
            for x in range(x0 + row // 2, x0 + 9 - row // 2):
                p.put(x, 3 + row, BR, 3 if row < 2 else 2)
        p.rect(x0, 2, x0 + 8, 2, IRON, 3)                    # the steel rim
        p.put(x0 + 4, 5, JD if side == 0 else K, 4 if side == 0 else 2)
        p.rect(x0 + 4, 10, x0 + 5, 13, BR, 2)
        if side == 0:
            p.rect(x0 + 4, 13, 9, 14, BR, 2)
        else:
            p.rect(22, 13, x0 + 5, 14, BR, 2)
    # the steam stack on top
    p.rect(15, 0, 16, 4, IRON, 2)
    p.rect(14, 0, 17, 0, IRON, 3)
    # the gauge over the cog
    p.rect(14, 6, 17, 8, SM, 2)
    p.put(15, 7, K, 2)
    p.put(16, 6, K, 2)
    # the big cog, a quarter of a tooth a frame (8 teeth: 45 degrees a tooth)
    cog(p, 16.0, 13.5, 3.6, 4.8, 8, frame * math.radians(45.0 / 4.0), (BR[1], BR[3], BR[4], BR[5]), 1, 3)   # brass's own shades (16 colours)
    # the furnace window under it, flickering
    for x in range(12, 20):
        p.put(x, 18, EM, 2 if (x + frame) % 3 else 3)
        p.put(x, 19, EM, 1 if (x + frame) % 2 else 2)
    # the output tray
    p.rect(11, 20, 20, 20, IRON, 3)
    p.outline()
    for (x, y) in ((10, 6), (21, 6), (10, 19), (21, 19)):     # rivets
        p.put(x, y, BR, 5, lock=True)
    return p


def tile_sheet(frames):
    """Each 1x frame cut into 8 px tiles laid out with 1 px gaps (4 x 3, the bottom row 9 tall), frames stacked on a 28 px
    stride: vanilla's 18 px tile stride and 56 px animation frame at 2x."""
    rows = ((0, 8), (8, 8), (16, 9))
    out = Image.new("RGBA", (4 * 9, 28 * len(frames)), (0, 0, 0, 0))
    for f, img in enumerate(frames):
        for r, (y0, h) in enumerate(rows):
            for c in range(4):
                tile = img.crop((c * 8, y0, c * 8 + 8, y0 + h))
                out.alpha_composite(tile, (c * 9, f * 28 + r * 9))
    return out


def highlight(img):
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


# --- the parts ----------------------------------------------------------------------------------------------------------------
def half(second):
    """The core split down the middle: a half cog on the outer side, the housing, the cut side's gears."""
    p = Pix(13, 15)
    p.rect(3, 2, 12, 13, BR, 2)
    p.rect(3, 2, 12, 3, BR, 3)
    p.rect(3, 2, 3, 13, BR, 3)
    cog(p, 3.0, 8.0, 3.2, 4.4, 8, 0.2, GI, 3, 8)              # the half cog on the outer side
    for y in range(3, 13):                                     # the cut: dark, gears showing
        p.put(12, y, IRON, 1)
        p.put(11, y, IRON, 2 if y % 3 else 3)
    if not second:                                             # the hopper on top
        p.rect(5, 0, 10, 0, IRON, 3)
        p.rect(6, 1, 9, 1, BR, 3)
        p.put(7, 5, JD, 4)
    else:                                                      # the press head and its chute
        p.rect(6, 9, 9, 10, IRON, 2)
        p.rect(7, 11, 8, 14, IRON, 3)
        p.put(7, 5, K, 3)
    p.outline()
    for (x, y) in ((5, 3), (10, 3), (5, 12), (10, 12)):
        p.put(x, y, BR, 5, lock=True)
    if second:
        return p.image().transpose(Image.FLIP_LEFT_RIGHT)      # the right half: the cog on the right
    return p.image()


def blueprint():
    p = Pix(15, 14)
    # the paper, partly unrolled: blue with white lines of a cog
    p.rect(2, 3, 12, 11, DN, 3)
    p.rect(2, 3, 12, 3, DN, 4)
    p.rect(0, 2, 1, 12, DN, 2)                                # the left roll
    p.rect(13, 2, 14, 12, DN, 2)                              # the right roll
    p.put(0, 2, DN, 3)
    p.put(13, 2, DN, 3)
    for (x, y) in ((6, 5), (7, 5), (8, 5), (5, 6), (9, 6), (5, 7), (9, 7), (5, 8), (9, 8), (6, 9), (7, 9), (8, 9), (7, 4), (4, 7), (10, 7), (7, 10)):
        p.put(x, y, SM, 2)                                   # the cog drawn on it
    p.put(7, 7, SM, 3)
    p.outline()
    for (x, y, k) in ((11, 10, 3), (12, 10, 2), (11, 11, 2), (12, 11, 1)):   # the red wax seal
        p.put(x, y, K, k, lock=True)
    return p


def beam():
    """A column of light 8 px wide, 16 tall, tiling: a white-gold core, gilt towards its edges."""
    p = Pix(8, 16)
    for y in range(16):
        for x, k in ((0, 6), (7, 6), (1, 7), (6, 7), (2, 8), (5, 8)):
            p.put(x, y, GI, k)
        p.put(3, y, GI, 9 if y % 4 else 8)
        p.put(4, y, GI, 9 if (y + 2) % 4 else 8)
    return p


def aura():
    p = Pix(20, 20)
    for y in range(20):
        for x in range(20):
            r = math.hypot(x + 0.5 - 10.0, y + 0.5 - 10.0)
            if 8.0 <= r < 9.2:
                p.put(x, y, GI, 8)
            elif 6.6 <= r < 7.2 and (x + y) % 3 == 0:
                p.put(x, y, GI, 7)
    for (x, y) in ((10, 0), (19, 10), (0, 9), (9, 19)):
        p.put(x, y, GI, 9)
    return p


# --- the window ---------------------------------------------------------------------------------------------------------------
def panel():
    """A nine-slice (8 px corners at 1x): a brass frame round an iron plate; rivets only in the corners."""
    p = Pix(24, 24)
    p.rect(0, 0, 23, 23, IRON, 1)
    p.rect(1, 1, 22, 22, BR, 2)
    p.rect(1, 1, 22, 1, BR, 4)
    p.rect(1, 1, 1, 22, BR, 3)
    p.rect(1, 22, 22, 22, BR, 1)
    p.rect(22, 1, 22, 22, BR, 1)
    p.rect(3, 3, 20, 20, IRON, 1)
    p.rect(4, 4, 19, 19, IRON, 0)
    p.put(0, 0, IRON, 0)
    for (x, y) in ((2, 2), (21, 2), (2, 21), (21, 21)):
        p.put(x, y, GI, 8, lock=True)
    return p


def slot(size, product=False):
    p = Pix(size, size)
    p.rect(0, 0, size - 1, size - 1, IRON, 0)
    ramp = GI if product else BR
    hi = 8 if product else 4
    p.rect(1, 1, size - 2, size - 2, ramp, 3 if product else 2)
    p.rect(1, 1, size - 2, 1, ramp, hi)
    p.rect(1, 1, 1, size - 2, ramp, hi - 1)
    p.rect(3, 3, size - 4, size - 4, IRON, 1)
    p.rect(4, 4, size - 5, size - 5, IRON, 0)
    if product:                                                # cog teeth round the frame and jade studs
        for k in range(4, size - 4, 4):
            for (x, y) in ((k, 0), (k + 1, 0), (k, size - 1), (k + 1, size - 1), (0, k), (0, k + 1), (size - 1, k), (size - 1, k + 1)):
                p.put(x, y, GI, 5)
        for (x, y) in ((2, 2), (size - 3, 2), (2, size - 3), (size - 3, size - 3)):
            p.put(x, y, JD, 4, lock=True)
    else:
        for (x, y) in ((2, 2), (size - 3, 2), (2, size - 3), (size - 3, size - 3)):
            p.put(x, y, GI, 8, lock=True)
    return p


def button(lit):
    p = Pix(12, 12)
    p.rect(0, 0, 11, 11, IRON, 0)
    p.rect(1, 1, 10, 10, BR, 3 if lit else 2)
    p.rect(1, 1, 10, 1, BR, 5 if lit else 4)
    p.rect(1, 1, 1, 10, BR, 4 if lit else 3)
    p.rect(1, 10, 10, 10, BR, 1)
    p.rect(10, 1, 10, 10, BR, 1)
    return p


QMARK = ("..xx.", ".x..x", "....x", "...x.", "..x..", ".....", "..x..")


def help_icon(lit):
    p = Pix(11, 11)
    cog(p, 5.5, 5.5, 4.0, 5.4, 8, 0.0, GI, 3 if not lit else 4, 7 if not lit else 9)
    p.outline()
    for dy, row in enumerate(QMARK):
        for dx, ch in enumerate(row):
            if ch == "x":
                p.put(3 + dx, 2 + dy, IRON, 0, lock=True)
    return p


def stack(images):
    w = max(im.width for im in images)
    out = Image.new("RGBA", (w, sum(im.height for im in images)), (0, 0, 0, 0))
    y = 0
    for im in images:
        out.alpha_composite(im, (0, y))
        y += im.height
    return out


def export_all():
    frames = [station(f).image() for f in range(4)]
    sheet = tile_sheet(frames)
    export(sheet, OUT + "Tiles/CombinatorTile.png")
    export(tile_sheet([highlight(f) for f in frames]), OUT + "Tiles/CombinatorTile_Highlight.png")   # traced whole, then cut
    export(frames[0], OUT + "Items/TheCombinator.png")
    export(half(False), OUT + "Items/TheFirstHalf.png")
    export(half(True), OUT + "Items/TheSecondHalf.png")
    export(blueprint().image(), OUT + "Items/CombinatorBlueprint.png")
    export(beam().image(), OUT + "Items/CombinatorBlueprint_Beam.png")
    export(aura().image(), OUT + "Items/CombinatorBlueprint_Aura.png")
    export(panel().image(), OUT + "UI/CombinatorPanel.png")
    export(slot(26).image(), OUT + "UI/CombinatorSlot.png")
    export(slot(30, product=True).image(), OUT + "UI/CombinatorProductSlot.png")
    export(stack([button(False).image(), button(True).image()]), OUT + "UI/CombinatorButton.png")
    export(stack([help_icon(False).image(), help_icon(True).image()]), OUT + "UI/CombinatorHelp.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview([station(0).image(), station(1).image(), half(False), half(True), blueprint().image(), beam().image(), aura().image(),
                 panel().image(), slot(26).image(), slot(30, True).image(), button(False).image(), help_icon(False).image()], a.preview)
    else:
        export_all()
