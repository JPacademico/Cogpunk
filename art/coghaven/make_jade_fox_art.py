"""The Jade Token and its spirit fox, v6 2026-11-23. Run from the repo root:

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
- **Animations made of the model's own parts** (v6; the user, on v5's hops and motes: "use the base model for making
  animation frames ... not creating extra stuff that the base model does not have ... a hoping animation does not need to
  create legs but to add wave motion to its body or tail"). The model is cut into its three parts (`part`): the head with
  its ears (rows 0-13), the body with its paws (rows 14-18) and the tail behind them. A frame (`pose`) only moves those:
  the head bobs on the body a pixel (a squash hides the body's top row; a stretch repeats it), the front leaves the ground
  a pixel, and the tail bends in five column groups (a wave running from its base to its dark tip, the tip at most 2 px).
  The ear tips lean back a pixel when it leaps, the eyes (both) close. Nothing is added: no legs, no motes, no new pixels
  beyond a repeated row or a seam closed with its neighbour.
  Idle 0-3 (rest, tail swish, ear flick, blink; the C# plays them in a long sequence), Trot 4-9 (a bounding hop: crouch,
  push, leave the ground, the tail dragging then whipping up, land), Float 10-13 (a wave travelling down the tail, ears back),
  Settle 14-15, Sleep 16-17 (curled, breathing), Wake 18-20 (a stretch), Jump 21-23 (rising, apex, falling).
Facing right in the sheet (mirrored; the pet flips by direction). The glow: the jade ear linings. Outputs: 24 frames of
CELL_W x CELL_H at 1x, 1 px under each; JadeFoxBuff.png, its head; JadeToken.png, the coin. Earlier foxes in previous/
(v5, the hopping version: 2026-11-23c; the hand-cleaned v4 the user rejected was overwritten).
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
CELL_W, CELL_H, FRAMES_N = 26, 24, 24

# The model, exactly (o outline, b brown, t tan, p pink, w cream); faces left, sitting, the tail curled behind it
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
NEAR_EYE = ((8, 9), (7, 10), (8, 10), (7, 11))      # the near eye's dark pixels (x, y)
FAR_EYE_LOW = (3, 11)                                # the far eye (at the face's edge): (3, 10) and this
EAR_TIPS = ((2, 0), (11, 0))
CHARM = {(10, 13): G[7], (11, 13): G[5]}             # the two gilt pixels, at its chest
NECK = 13                                            # the head's last row; the body starts under it
TAIL_GROUPS = ((12, 13), (14, 15), (16, 17), (18, 19), (20, 21))   # the tail's columns, base to tip


def tail_start(y):
    """The first tail column of a row: the tail sits behind the head and body, their outline (the 'b' seam) theirs."""
    if 9 <= y <= 12:
        return 12
    if y in (8, 13):
        return 13
    return 14 if y > 13 else FW


def part(x, y):
    if x >= tail_start(y):
        return "tail"
    return "head" if y <= NECK else "body"


def features(eyes="open", ears="up"):
    """The model's rows with its small features changed: the eyes (both) half or shut; the ear tips."""
    rows = [list(r) for r in FOX]
    if eyes in ("half", "shut"):
        for (x, y) in NEAR_EYE:
            rows[y][x] = "w"
        rows[10][7], rows[10][8] = "o", "o"            # the near eye shut: one dark line
        rows[FAR_EYE_LOW[1]][FAR_EYE_LOW[0]] = "w"     # the far eye: its line left at row 10
        if eyes == "half":
            rows[9][8] = "o"                          # the lid a pixel up
    if ears == "flick":                               # the back ear's tip flicks a pixel back
        rows[0][11], rows[0][12] = ".", "b"
    elif ears == "back":                              # both tips lean back a pixel (a leap, the float)
        rows[0][2], rows[0][3] = ".", "b"
        rows[0][11], rows[0][12] = ".", "b"
    elif ears == "fold":                              # asleep: the tips fold down
        for (x, y) in EAR_TIPS:
            rows[y][x] = "."
    return rows


def pose(head=0, lift=0, tail=(0, 0, 0, 0, 0), eyes="open", ears="up"):
    """One frame from the model's parts -> {(x, y): (char, source)} in model space (y up = smaller; may go above row 0).

    head: the head's rise on the body (+1 stretch: the body's top row repeated under it; -1 squash: the head covers it).
    lift: the head and body leave the ground by this. tail: each column group's rise over the ground (base to tip)."""
    rows = features(eyes, ears)
    rise = {}
    for g, cols in enumerate(TAIL_GROUPS):
        for c in cols:
            rise[c] = tail[g]
    out = {}
    layers = {"tail": [], "body": [], "head": []}
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                layers[part(x, y)].append((x, y, ch))
    for (x, y, ch) in layers["tail"]:                 # behind
        ny = y - rise.get(x, 0)
        if ny <= FH - 1:                               # never under the ground
            out[(x, ny)] = (ch, (x, y))
    for (x, y, ch) in layers["body"]:
        out[(x, y - lift)] = (ch, (x, y))
    for k in range(max(0, head)):                     # a stretch: the body's top row repeated under the head
        for x, ch in enumerate(rows[NECK + 1]):
            if ch != "." and part(x, NECK + 1) == "body":
                out[(x, NECK - lift - k)] = (ch, (x, NECK + 1))
    for (x, y, ch) in layers["head"]:                 # in front
        out[(x, y - lift - head)] = (ch, (x, y))
    # seams: a pixel the model has, left empty between two moved parts, takes the colour above it (or beside it)
    for (x, y), ch in list(seam_fill(out, lift).items()):
        out[(x, y)] = ch
    return out


def seam_fill(out, lift):
    fill = {}
    for y in range(-4, FH):
        for x in range(FW):
            if (x, y) in out:
                continue
            my = y + lift
            if not (0 <= my < FH) or FOX[my][x] == ".":
                continue
            up, down = out.get((x, y - 1)), out.get((x, y + 1))
            left, right = out.get((x - 1, y)), out.get((x + 1, y))
            if up and down:
                fill[(x, y)] = up
            elif left and right and up:
                fill[(x, y)] = left
    return fill


def render(fr):
    """A pose -> (pixels, glow) in the cell: mirrored to face right, the model's last row on the cell's bottom row."""
    px, glow = {}, {}
    top = CELL_H - FH
    left = (CELL_W - FW) // 2
    for (x, y), (ch, src) in fr.items():
        q = (left + FW - 1 - x, top + y)
        px[q] = CHARM.get(src, COLOUR[ch])
        if ch == "p" and src[1] <= 7 and part(*src) == "head":
            glow[q] = COLOUR[ch]                      # the jade ear linings: "a bit of light"
    return px, glow


# Every frame, as poses of the parts. Tail tuples: each group's rise over the ground, base to tip.
TROT = (
    dict(head=-1, tail=(0, 0, 1, 1, 1)),                       # landed: squashed, the tail still up from the swing
    dict(head=1, tail=(0, 0, 0, 0, 0)),                        # push: the body stretches, the tail down
    dict(head=1, lift=1, tail=(1, 1, 0, 0, -1), ears="back"),  # leaves the ground: the tail drags, its tip dipping
    dict(head=0, lift=1, tail=(1, 1, 1, 0, 0), ears="back"),   # in the air: the wave runs down the tail
    dict(head=0, lift=1, tail=(1, 1, 2, 2, 2)),                # coming down: the tail whips up
    dict(head=0, tail=(0, 1, 1, 2, 2)),                        # touches down, the tail still high
)
FLOAT = (                                                      # a wave travelling from the tail's base to its tip
    dict(tail=(0, 1, 1, 0, 0), ears="back"),
    dict(tail=(0, 0, 1, 1, 0), ears="back"),
    dict(tail=(0, 0, 0, 1, 1), ears="back"),
    dict(tail=(0, 0, 0, 0, -1), ears="back"),
)
JUMP = (
    dict(head=1, tail=(0, 0, 0, 0, -1), ears="back"),          # rising: stretched, the tail dragging below
    dict(head=0, tail=(0, 0, 1, 1, 1)),                        # the top of the arc
    dict(head=0, tail=(0, 1, 1, 2, 2)),                        # falling: the tail streams up
)
FRAMES = (
    [dict(), dict(tail=(0, 0, 0, 1, 1)), dict(ears="flick"), dict(eyes="shut")]                  # idle 0-3
    + list(TROT)                                                                                 # trot 4-9
    + list(FLOAT)                                                                                # float 10-13
    + [dict(head=-1, eyes="half"), dict(head=-1, eyes="shut", ears="fold")]                      # settle 14-15
    + [dict(head=-1, eyes="shut", ears="fold"), dict(head=0, eyes="shut", ears="fold")]          # sleep 16-17
    + [dict(head=-1, eyes="half", ears="fold"), dict(head=1, tail=(0, 0, 1, 1, 1)),              # wake 18-20
       dict(ears="flick")]
    + list(JUMP)                                                                                 # jump 21-23
)


def frames():
    out = [render(pose(**f)) for f in FRAMES]
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


def preview(fr, path, sc=8, cols=6):
    rows = (FRAMES_N + cols - 1) // cols
    out = Image.new("RGBA", (cols * (CELL_W * sc + 6) + 6, rows * (CELL_H * sc + 6) + 6), (24, 24, 30, 255))
    for k, (px, gl) in enumerate(fr):
        im = Image.new("RGBA", (CELL_W, CELL_H), (60, 120, 140, 255) if k % 2 == 0 else (40, 44, 60, 255))
        for (x, y), c in px.items():
            if 0 <= x < CELL_W and 0 <= y < CELL_H:
                im.putpixel((x, y), tuple(c) + (255,))
        out.alpha_composite(im.resize((CELL_W * sc, CELL_H * sc), Image.NEAREST),
                            (6 + (k % cols) * (CELL_W * sc + 6), 6 + (k // cols) * (CELL_H * sc + 6)))
    out.save(path)
    print("preview", path)


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
        print("cell %d x %d, %d frames, OriginX %d (2x)" % (CELL_W, CELL_H, FRAMES_N, origin_x()))
    if args.preview:
        preview(fr, args.preview)


if __name__ == "__main__":
    main()
