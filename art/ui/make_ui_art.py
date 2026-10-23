"""Source for shared UI sprites (D4). Run from the repo root:

    python -P art/ui/make_ui_art.py

Outputs (2x nearest-neighbour):
    Assets/UI/BiomeTitleOrnament.png   96x24: left half = brass cog + riveted bar, right half = bar + cog.
                                       Core/UI/BiomeTitleSystem draws the halves either side of a biome title.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scrap"))
from make_scrap_art import Canvas, export, make_cog  # noqa: E402

# The Rusted Cog item recoloured to clean brass: copper ramp -> brass ramp, grime -> darker brass.
TO_BRASS = {"a": "B", "b": "C", "c": "D", "d": "E", "e": "F", "l": "C", "m": "D", "n": "E", "F": "G", "E": "F"}


def brass_cog():
    cog = make_cog()
    out = Canvas(cog.w, cog.h)
    for y in range(cog.h):
        for x in range(cog.w):
            ch = cog.get(x, y)
            if ch != ".":
                out.set(x, y, TO_BRASS.get(ch, ch))
    return out


def left_half():
    c = Canvas(24, 12)
    for x in range(11, 24):                    # riveted bar: lit top edge, dark bottom edge
        c.set(x, 4, "B")
        c.set(x, 5, "F" if x % 4 else "G")
        c.set(x, 6, "D")
        c.set(x, 7, "B")
    c.set(23, 4, "."); c.set(23, 7, ".")      # tapered tip
    c.blit(brass_cog(), 0, 0)
    return c


def make_ornament():
    sheet = Canvas(48, 12)
    sheet.blit(left_half(), 0, 0)
    right = left_half()
    for y in range(12):                        # mirror only the bar (symmetric shading) ...
        for x in range(11, 24):
            ch = right.get(x, y)
            if ch != ".":
                sheet.set(47 - x, y, ch)
    sheet.blit(brass_cog(), 36, 0)             # ... the cog stays lit from the top-left
    return sheet


if __name__ == "__main__":
    export(make_ornament(), "Assets/UI/BiomeTitleOrnament.png")
