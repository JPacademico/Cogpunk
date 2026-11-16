"""Source for Coghaven's chests and the Pagoda Key (D4, 2026-11-16). Run from the repo root:

    python -P art/coghaven/make_coghaven_chests_art.py [--preview FILE]

User, 2026-11-16: "the pagoda chest on coghaven should be locked and can only be opened with a key obtained on hardmode
(just like default terraria biome chests of the dungeon), this 'pagoda key' will be dropped by a future boss on hardmode";
"the chest should be located on the middle of this room and behave like trashtr0m chest ... The chest can only be opened
after Jadey has been killed". The looks are my calls:
    style 0  Pagoda Chest          red lacquer, a little curved roof of jade tiles for a lid (the pagoda's own roofs), gilt
                                    corner brackets and a gilt latch plate, gilt feet
    style 1  Locked Pagoda Chest   the same with a jade padlock hung on the latch and a gilt chain across the front
    style 2  Jade Vault            carved jade (the ghost ramp, verdigris mottle) in gilt bands, a gilt-ringed soul seal on its
                                    front (its eye glows while the vault is sealed: the tile lights it)
    Pagoda Key                     a jade key whose bow is a tiny pagoda roof, a red silk tassel

Chest sheet layout (tModLoader ExampleChest 1.4.4, as art/furniture/make_furniture_art.py): each style is 2 tiles wide (16
+ 2 px gutter each) and each lid frame 38 px tall (CoordinateHeights 16, 18): frame 0 closed, 1 opening, 2 open. At 1x a
chest is 16x17, cut into an 8x8 top row and an 8x9 bottom row with 1 px gutters.

Outputs (2x nearest-neighbour):
    Content/Coghaven/Tiles/CoghavenChestTile.png, _Highlight.png    108x114: 3 styles x 3 lid frames
    Content/Coghaven/Items/PagodaChest.png                          the item icon (style 0)
    Content/Coghaven/Items/PagodaKey.png
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP  # noqa: E402

ROOT = os.getcwd()
K, G, GH, VD, ST, IV = RAMP["crimson"], RAMP["gilt"], RAMP["ghost"], RAMP["verd"], RAMP["steel"], RAMP["ivory"]
W, H = 16, 17
STYLES = 3


def blank():
    return [[None] * W for _ in range(H)]


def lid(px, lift, style):
    """The lid, `lift` px raised (0 shut). A Pagoda Chest's is a curved roof of jade tiles (tube columns lit, mid, dark)
    with a gilt ridge and upturned eave tips; the vault's a slab of jade in gilt bands."""
    top = 1 - lift
    jade = style == 2
    for y in range(top, top + 6):
        if y < 0:
            continue
        row = y - top
        inset = (2 if row == 0 else 1 if row == 1 else 0)
        for x in range(inset, W - inset):
            edge = x == inset or x == W - 1 - inset or row == 0 or row == 5
            if jade:
                col = GH[0] if edge else (GH[3] if (x + row) % 5 == 0 else GH[2] if x > 9 else GH[3] if x < 4 else GH[2])
                if not edge and (x * 7 + row * 3) % 11 == 0:
                    col = VD[2]
                if row == 2 and not edge:
                    col = G[7] if x < 8 else G[5]        # the gilt band round the slab
            else:
                k = x % 3
                col = GH[0] if edge else (GH[4] if k == 0 else GH[3] if k == 1 else GH[2])
                if row == 1 and not edge:
                    col = G[8] if x < 8 else G[6]        # the gilt ridge
            px[y][x] = col
    if not jade and top + 1 >= 0:                        # the eave tips turned up
        for (x, dy) in ((0, 0), (W - 1, 0)):
            if 0 <= top + dy < H:
                px[top + dy][x] = GH[0]
        if top >= 0:
            px[top][1] = GH[3]
            px[top][W - 2] = GH[2]
    for x in range(1, W - 1):                            # the lid's gilt lower edge
        y = top + 6
        if 0 <= y < H:
            px[y][x] = G[6] if x < 8 else G[4]
    px_y = top + 6
    if 0 <= px_y < H:
        px[px_y][0] = G[1]
        px[px_y][W - 1] = G[1]


def body(px, style):
    """Rows 7-16: the chest's box: lacquer (or carved jade), gilt corner brackets, the latch (or the seal), gilt feet."""
    jade = style == 2
    for y in range(7, 16):
        for x in range(W):
            edge = x in (0, W - 1) or y == 15
            if jade:
                col = GH[0] if edge else (GH[3] if x < 6 else GH[2])
                if not edge and (x * 5 + y * 3) % 9 == 0:
                    col = VD[2] if x > 5 else VD[3]
            else:
                col = K[0] if edge else (K[4] if x < 5 else K[3] if x < 11 else K[2])
                if not edge and y == 8:
                    col = K[5] if x < 8 else K[4]        # the lit top edge of the box
            px[y][x] = col
    for (x0, x1) in ((1, 2), (13, 14)):                  # gilt corner brackets top and bottom
        for x in range(x0, x1 + 1):
            for y in (8, 9, 13, 14):
                if (y in (8, 13)) or x == (x0 if x0 < 8 else x1):
                    px[y][x] = G[7] if x < 8 else G[5]
    if jade:                                             # gilt bands down the box and the soul seal
        for y in range(7, 15):
            px[y][3] = G[6]
            px[y][12] = G[4]
        for (dx, dy, col) in ((-1, -1, G[8]), (0, -1, G[7]), (1, -1, G[6]), (-2, 0, G[7]), (2, 0, G[4]), (-2, 1, G[6]), (2, 1, G[3]),
                              (-1, 2, G[5]), (0, 2, G[4]), (1, 2, G[3]), (-1, 0, GH[1]), (1, 0, GH[1]), (0, 0, GH[5]), (-1, 1, GH[1]),
                              (0, 1, GH[4]), (1, 1, GH[1])):
            px[10 + dy][7 + dx] = col
            px[10 + dy][8 + dx] = px[10 + dy][8 + dx] if dx < 0 else col
    else:                                                # the latch plate
        for y in range(8, 12):
            for x in range(6, 10):
                px[y][x] = G[8] if (x == 6 or y == 8) else G[5] if (x == 9 or y == 11) else G[7]
        px[10][7] = ST[0]
        px[10][8] = ST[1]
    for (x0, x1) in ((1, 2), (13, 14)):                  # feet
        for x in range(x0, x1 + 1):
            px[16][x] = G[4] if x < 8 else G[2]
        px[15][x0] = G[1]
        px[15][x1] = G[1]


def padlock(px):
    """A jade padlock on the latch and a gilt chain across the box (style 1)."""
    for x in range(1, W - 1):
        if 6 <= x <= 9:
            continue
        if px[12][x] is not None:
            px[12][x] = G[7] if x % 2 else G[4]
    for (x, y, col) in ((7, 10, GH[0]), (8, 10, GH[0]), (6, 11, GH[0]), (9, 11, GH[0]), (6, 12, GH[0]), (9, 12, GH[0]),
                        (7, 11, GH[4]), (8, 11, GH[3]), (7, 12, GH[3]), (8, 12, GH[2]), (6, 13, GH[0]), (7, 13, GH[0]), (8, 13, GH[0]),
                        (9, 13, GH[0]), (7, 9, G[7]), (8, 9, G[5])):
        px[y][x] = col
    px[12][8] = ST[0]                                    # the keyhole


def interior(px, rows):
    """The open box's dark inside (and a glint of treasure) where the lid has lifted off."""
    for y in rows:
        for x in range(1, W - 1):
            px[y][x] = ST[0] if y == rows[0] else ST[1]
    if len(rows) >= 2:
        px[rows[-1]][4] = G[8]
        px[rows[-1]][11] = G[7]


def chest(style, frame):
    px = blank()
    body(px, style)
    if style == 1 and frame == 0:
        padlock(px)
    if frame == 0:
        lid(px, 0, style)
    elif frame == 1:
        interior(px, [6, 7])
        lid(px, 2, style)
    else:
        interior(px, [5, 6, 7])
        lid(px, 4, style)
    return px


def outline_of(px):
    out = blank()
    for y in range(H):
        for x in range(W):
            if px[y][x] is None:
                continue
            if any(not (0 <= x + dx < W and 0 <= y + dy < H) or px[y + dy][x + dx] is None for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = (255, 255, 255)
    return out


def cut(px, sheet, ox, oy):
    """16x17 chest art -> its 18x19 tile frame (1 px gutters after column 8 and row 8) on the sheet."""
    for y in range(H):
        for x in range(W):
            col = px[y][x]
            if col is None:
                continue
            fx = x + (1 if x >= 8 else 0)
            fy = y + (1 if y >= 8 else 0)
            sheet.putpixel((ox + fx, oy + fy), col + (255,))


def sheets():
    sheet = Image.new("RGBA", (18 * STYLES, 19 * 3), (0, 0, 0, 0))
    high = Image.new("RGBA", (18 * STYLES, 19 * 3), (0, 0, 0, 0))
    for style in range(STYLES):
        for f in range(3):
            px = chest(style, f)
            cut(px, sheet, style * 18, f * 19)
            cut(outline_of(px), high, style * 18, f * 19)
    return sheet, high


def to_img(px, w=W, h=H):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            if px[y][x] is not None:
                im.putpixel((x, y), px[y][x] + (255,))
    return im


KEY = ("....oooo....",
       "...oJJJJo...",
       "..oJKKKJJo..",
       ".oooooooooo.",
       "...oHGGo....",
       "...oG..Go...",
       "...oG..Go...",
       "....oHGo....",
       ".....oGo....",
       ".....oGo....",
       ".....oGoo...",
       ".....oGHGo..",
       ".....oGoo...",
       ".....oGHo...",
       ".....oGo....",
       "......o.....")


def key_icon():
    """The Pagoda Key: a jade key, its bow a tiny pagoda roof, a red silk tassel hanging from the roof's eave."""
    cols = {"o": GH[0], "J": GH[3], "K": GH[4], "H": GH[4], "G": GH[2]}
    px = [[None] * 14 for _ in range(16)]
    for y, row in enumerate(KEY):
        for x, ch in enumerate(row):
            if ch in cols:
                px[y][x + 1] = cols[ch]
    for (x, y) in ((1, 4), (1, 5), (0, 6), (1, 6), (2, 6), (0, 7), (2, 7), (1, 8)):
        px[y][x] = K[4] if (x + y) % 2 else K[3]
    px[3][1] = G[6]
    return to_img(px, 14, 16)


def export(img, rel):
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    big = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    big.save(out)
    print("wrote %s (%dx%d)" % (rel, big.width, big.height))


def export_all():
    sheet, high = sheets()
    export(sheet, "Content/Coghaven/Tiles/CoghavenChestTile.png")
    export(high, "Content/Coghaven/Tiles/CoghavenChestTile_Highlight.png")
    export(to_img(chest(0, 0))[0:15] if False else to_img(chest(0, 0)), "Content/Coghaven/Items/PagodaChest.png")
    export(key_icon(), "Content/Coghaven/Items/PagodaKey.png")


def preview(path, scale=8):
    sheet, _ = sheets()
    out = Image.new("RGBA", (sheet.width + 24, sheet.height + 4), (40, 44, 52, 255))
    out.alpha_composite(sheet, (2, 2))
    out.alpha_composite(key_icon(), (sheet.width + 6, 4))
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
