"""Source for shared furniture sprites (D4). Run from the repo root:

    python -P art/furniture/make_furniture_art.py

Outputs (2x nearest-neighbour):
    Content/Furniture/ScrappyTrunkTile.png            72x114: 2 styles (trunk, Junkyard cache) x 3 lid frames
    Content/Furniture/ScrappyTrunkTile_Highlight.png  72x114: smart-cursor outline (white edge pixels)
    Content/Furniture/ScrappyTrunk.png                item icon

Chest sheet layout (tModLoader ExampleChest, 1.4.4): each style is 2 tiles wide (16 + 2 px gutter each) and each lid
frame is 16 + 2 + 18 + 2 = 38 px tall (CoordinateHeights 16, 18). Frame 0 = closed, 1 = opening, 2 = open; the game
animates them when the chest is opened. At 1x the chest art is 16x17, cut into an 8x8 top row and an 8x9 bottom row.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scrap"))
from make_scrap_art import Canvas, PAL, export  # noqa: E402

PAL.setdefault("W", (255, 255, 255))          # Steam 3, used only by the highlight texture

# Rust plates (copper ramp), iron straps (or brass on the cache), brass latch, dark interior.
TRUNK_CLOSED = [
    ".aaaaaaaaaaaaaa.",
    "adedkddddddkdeda",
    "adccqccccccqccda",
    "acbcjcbccbcjcbca",
    "acccjcccccmjccca",
    "abbbjbbbbbbjbbba",
    "aaaaiaaEDaaiaaaa",
    "adcckccEDcckccda",
    "acccjccBBccjccca",
    "acbcjccDCccjcbca",
    "accmjcccccmjccca",
    "acccjccccccjccca",
    "abbcjbbbbbbjcbba",
    "abbbjbbbbbbjbbba",
    "aaaajaaaaaaj aaa".replace(" ", "a"),
    ".aiaa......aaia.",
    ".ii..........ii.",
]
TRUNK_OPENING = [
    ".aaaaaaaaaaaaaa.",
    "adedkddddddkdeda",
    "abbbjbbbbbbjbbba",
    "aaaaiaaaaaaiaaaa",
    "alllllllllllllla",
    "allEllllllllElla",
] + TRUNK_CLOSED[6:]
TRUNK_OPEN = [
    ".aaaaaaaaaaaaaa.",
    "abbbjbbbbbbjbbba",
    "alllllllllllllla",
    "allllElllllllla.".replace(".", "a"),
    "alEllllFllEllla.".replace(".", "a"),
    "allllEllllllllla",
] + TRUNK_CLOSED[6:]

# The cache: brass straps and trim instead of iron, a cog boss on the lid.
CACHE_SWAP = {"k": "E", "j": "D", "q": "F", "i": "C"}


def cache_variant(rows, lid_cog):
    out = ["".join(CACHE_SWAP.get(ch, ch) for ch in row) for row in rows]
    c = Canvas.from_rows(out)
    if lid_cog:
        for (x, y, ch) in ((7, 2, "F"), (8, 2, "E"), (6, 3, "E"), (7, 3, "B"), (8, 3, "D"), (9, 3, "C"), (7, 4, "D"), (8, 4, "C")):
            c.set(x, y, ch)
    return c


def cut_into_cells(chest):
    """16x17 chest art -> 18x19 tile frame with 1-px gutters (8x8 top cells, 8x9 bottom cells)."""
    frame = Canvas(18, 19)
    for y in range(17):
        for x in range(16):
            ch = chest.get(x, y)
            if ch == ".":
                continue
            fx = x + (1 if x >= 8 else 0)
            fy = y + (1 if y >= 8 else 0)
            frame.set(fx, fy, ch)
    return frame


def outline(c):
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        for x in range(c.w):
            if c.get(x, y) == ".":
                continue
            if any(c.get(x + dx, y + dy) == "." for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.set(x, y, "W")
    return out


def make_sheets():
    frames = [TRUNK_CLOSED, TRUNK_OPENING, TRUNK_OPEN]
    sheet = Canvas(36, 57)
    highlight = Canvas(36, 57)
    for style in range(2):
        for f, rows in enumerate(frames):
            chest = Canvas.from_rows(rows) if style == 0 else cache_variant(rows, lid_cog=(f == 0))
            sheet.blit(cut_into_cells(chest), style * 18, f * 19)
            highlight.blit(cut_into_cells(outline(chest)), style * 18, f * 19)
    return sheet, highlight


if __name__ == "__main__":
    for rows in (TRUNK_CLOSED, TRUNK_OPENING, TRUNK_OPEN):
        assert all(len(r) == 16 for r in rows) and len(rows) == 17, "trunk art must be 16x17"
    sheet, highlight = make_sheets()
    export(sheet, "Content/Furniture/ScrappyTrunkTile.png")
    export(highlight, "Content/Furniture/ScrappyTrunkTile_Highlight.png")
    export(Canvas.from_rows(TRUNK_CLOSED[:15]), "Content/Furniture/ScrappyTrunk.png")
