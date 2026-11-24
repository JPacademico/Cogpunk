"""The Jade Token and its spirit fox, v5 2026-11-23. Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--preview FILE]

User, 2026-11-23: "look i already gave you the in game model from a mod that adds this fennekin fox ... use the exact model
just change color and add like 2 golden pixels following the design please" (the user has the author's permission: "its a
friend of mine"). The model (reference/jade_fox_user_2026-11-23.png, an in-game screenshot, 3.95 screen px a sprite px) was
read cell by cell on its own grid (each cell's centre, snapped to the sprite's own five colours; background, the plant behind
it and the ground's checker cut away): FOX below, exactly that sprite (two pixels the screenshot's blur lost were closed: the
outline at the tail's top edge; one stray plant pixel dropped). Nothing redrawn.

Then only:
- **The colours**, one for one (the value of each kept): cream -> pale mint (sage 5), pink -> jade (ghost 4: the ear linings,
  the blush, the soft shading), tan -> sage 3, brown -> ghost 2, the outline -> the darkest jade (ghost 0).
- **Two gilt pixels**: a little charm at its chest, after the 2026-11-18 design's gilt collar.
- **Animations built on this model** (every frame is the model itself; only these change): Idle 0-3 an ear flick and a blink;
  Trot 4-9 hops (the whole fox rises 1-2 px and lands, the ears' tips trailing a pixel at the top); Float 10-13 bobbing a
  pixel, jade motes under it; Settle 14-15 landing; Sleep 16-17 eyes shut, ears relaxed a pixel; Wake 18-20 the eye half open,
  open, the ear flick.
Facing right in the sheet (mirrored; the pet flips by direction). The glow: the jade linings and the motes. Outputs as v4 (21
frames of CELL_W x CELL_H at 1x, 1 px under each; JadeFoxBuff.png, its head; JadeToken.png, the coin). Earlier foxes in
previous/ (v4: the hand-cleaned version the user rejected, 2026-11-23b).
"""
import argparse
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Coghaven/Pets/"
SA, GH, G, SM = RAMP["sage"], RAMP["ghost"], RAMP["gilt"], RAMP["steam"]
CELL_W, CELL_H, FRAMES_N = 26, 24, 21

# The model, exactly (o outline, b brown, t tan, p pink, w cream); faces left, lying
FOX = (
    "..b........b..........",
    ".bwb......bwb.........",
    ".bwwb....bwww.........",
    ".wtwb....bwtwb........",
    "owtwwb..owwtwb........",
    "owtpwb..owwtwo........",
    "optpooooopwtwo........",
    "optbwwwwwbptpo........",
    ".otwwwwwwwbtbooobbb...",
    "..owwwwwowbbowwwwwwbb.",
    "..oowwwoowbbwwwwwwwwwo",
    ".opowwwobpbbwwwwwwwwo.",
    ".owwwwwwwwbpwwwwwwwwo.",
    "..ottbbbttwpbwwwwwwwo.",
    ".bwwwwwwwwwpwbwwwwwwo.",
    ".owpwwwtwwtwwbpwwppo..",
    "owottttpttpwwbppppo...",
    "...owowwowwwwowwpo....",
    ".o.ooooo.ooooboooooo..",
)
FW, FH = len(FOX[0]), len(FOX)
COLOUR = {"o": GH[0], "b": GH[2], "t": SA[3], "p": GH[4], "w": SA[5]}
EYE = ((8, 9), (7, 10), (8, 10), (7, 11))          # the eye's dark pixels (x, y)
EAR_TIPS = ((2, 0), (11, 0))
CHARM = ((10, 13, G[7]), (11, 13, G[5]))            # the two gilt pixels, at its chest


def model(blink=False, half=False, flick=False, relax=False, trail=False):
    """The model's char rows with the small changes the animations need (nothing else moves)."""
    rows = [list(r) for r in FOX]
    if blink or half:
        for (x, y) in EYE:
            rows[y][x] = "w"
        rows[10][7], rows[10][8] = "o", "o"            # shut: one dark line
        if half:
            rows[9][8] = "o"
    if flick:                                          # the back ear's tip flicks a pixel back
        rows[0][11], rows[0][12] = ".", "b"
    if relax or trail:                                 # the ears' tips fold (asleep) or trail (at the top of a hop)
        for (x, y) in EAR_TIPS:
            rows[y][x] = "."
    return rows


def render(rows, dy=0, motes=0):
    """Rows -> (pixels, glow) in the cell: mirrored to face right, the model's last row on the cell's bottom row - dy."""
    px, glow = {}, {}
    top = CELL_H - FH - dy
    left = (CELL_W - FW) // 2
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == ".":
                continue
            q = (left + FW - 1 - x, top + y)
            px[q] = COLOUR[ch]
            if ch == "p" and y <= 7:
                glow[q] = COLOUR[ch]                   # the jade ear linings: "a bit of light"
    for (x, y, c) in CHARM:
        q = (left + FW - 1 - x, top + y)
        if q in px:
            px[q] = c
    if motes:
        for (x, y) in ((left + 5 + motes, CELL_H - 1), (left + 11, CELL_H - 1 - motes % 2), (left + 17 - motes, CELL_H - 1)):
            px[(x, y)] = GH[4]
            glow[(x, y)] = GH[4]
    return px, glow


def frames():
    out = [render(model()), render(model(flick=True)), render(model()), render(model(blink=True))]          # idle
    for dy in (0, 1, 2, 2, 1, 0):                                                                            # trot: hops
        out.append(render(model(trail=dy == 2), dy=dy))
    for k, dy in enumerate((1, 2, 2, 1)):                                                                    # float
        out.append(render(model(), dy=dy, motes=1 + k % 2))
    out += [render(model(), dy=1), render(model())]                                                          # settle
    out += [render(model(blink=True, relax=True)), render(model(blink=True))]                                # sleep
    out += [render(model(half=True)), render(model()), render(model(flick=True))]                            # wake
    assert len(out) == FRAMES_N
    return out


def sheet(fr, glow=False):
    im = Image.new("RGBA", (CELL_W, (CELL_H + 1) * FRAMES_N), (0, 0, 0, 0))
    for k, (px, gl) in enumerate(fr):
        for (x, y), c in (gl if glow else px).items():
            if 0 <= x < CELL_W and 0 <= y < CELL_H:
                im.putpixel((x, y + k * (CELL_H + 1)), tuple(c) + (255,))
    return im


def buff_icon():
    """The buff: its head and ears (the model's left 14 columns, rows 0-15), mirrored, in 16 x 16."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, r in enumerate(FOX[:16]):
        for x, ch in enumerate(r[:14]):
            if ch != ".":
                im.putpixel((15 - x - 1, y), tuple(COLOUR[ch]) + (255,))
    return im


def old_token():
    for sub in (("..", "oldbrasstown"), ("..", "bosses", "trashtr0m"), ("..", "bosses", "jadey")):
        sys.path.insert(0, os.path.join(HERE, *sub))
    spec = importlib.util.spec_from_file_location("fox_prev", os.path.join(HERE, "previous", "make_jade_fox_art_2026-11-19b.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.boxed(mod.token(), 14, 14)


def origin_x():
    """The body's middle (2x): the model's columns 4-17 hold its body; mirrored into the cell."""
    left = (CELL_W - FW) // 2
    return (left + FW - 1 - 10) * 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()
    fr = frames()
    if not args.no_export:
        export(sheet(fr), OUT + "JadeFoxPet.png")
        export(sheet(fr, glow=True), OUT + "JadeFoxPet_Glow.png")
        export(buff_icon(), OUT + "JadeFoxBuff.png")
        export(old_token(), OUT + "JadeToken.png")
        print("cell %d x %d, OriginX %d (2x)" % (CELL_W, CELL_H, origin_x()))
    if args.preview:
        sc = 8
        cols = 7
        rows = (FRAMES_N + cols - 1) // cols
        out = Image.new("RGBA", (cols * (CELL_W * sc + 6) + 6, rows * (CELL_H * sc + 6) + 6), (24, 24, 30, 255))
        for k, (px, gl) in enumerate(fr):
            im = Image.new("RGBA", (CELL_W, CELL_H), (60, 120, 140, 255))
            for (x, y), c in px.items():
                if 0 <= x < CELL_W and 0 <= y < CELL_H:
                    im.putpixel((x, y), tuple(c) + (255,))
            out.alpha_composite(im.resize((CELL_W * sc, CELL_H * sc), Image.NEAREST),
                                (6 + (k % cols) * (CELL_W * sc + 6), 6 + (k // cols) * (CELL_H * sc + 6)))
        out.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
