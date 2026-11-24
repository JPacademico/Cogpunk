"""Source for the Fungimancer (D4), v3 2026-11-23. Run from the repo root:

    python -P art/bosses/fungimancer/make_fungimancer_art.py [--preview FILE] [--frames Idle0,Cast2,...]

User, 2026-11-23: "redesign the fungimancer following the reference image (on the prompt) ... the animations have to be built
on top of the redesign and not the redesign having to follow the animations, its a rework so adapt the animations after."
The reference (reference/fungimancer_user_2026-11-23.webp) is pixel art on an 8 px grid: a fat frog-mage sitting on a teal
mushroom pad, one red hand raised casting, the other on its chest, a pale folded belly, big orange eyes, a dopey grin with
teeth, red frills down its back, big red webbed feet, violet magic swirling round it. It was read on its own grid (8 px a
sprite px, each cell's centre), the frog and its seat cut from the background and the swirls (the magic is the game's
effects, not the sprite), mirrored to face left (Cogpunk's boss art faces left), and its colours reduced to 48 (Lab k-means,
one fixed palette for every frame): reference/fungimancer_base_2026-11-23.png, 125 x 103, the model. v1 (procedural) and v2
(sculpted) are in previous/.

Every frame is that model; the animations change only these, by hand-sized region edits in its own pixels and palette:
  Idle 0-3     the raised hand waves a pixel; a blink
  Cast 4-7     violet light gathers round the raised hand, the hand rises two pixels, flings forward, settles
  Croak 8-11   a pale throat sac swells under the chin, holds, croaks (the mouth open), sinks
  Tongue 12-14 the mouth gapes (teeth, a pink tongue inside), wide, closing
  Fizzle 15-16 the spell goes wrong: eyes shut tight, the mouth hanging open (dumb)
  Intro 17-18  eyes shut, then open
  Death 19-22  glowing mushrooms sprout on it, one, three, five, seven; its eyes shut
Outputs (Content/Bosses/Fungimancer/): Fungimancer.png and _Glow.png (grid sheets, COLUMNS wide, 1 px right of and under each
cell at 1x), FungimancerRigData.cs, Fungimancer_Head_Boss.png, Gores/*, and the small things (fungimancer_things.py). The far
and near planes of v1/v2 are gone: the model is one plane.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, HERE)
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
import fungimancer_things as things  # noqa: E402

OUT = "Content/Bosses/Fungimancer/"
BASE = os.path.join(HERE, "reference", "fungimancer_base_2026-11-23.png")
COLUMNS = 4
AE, SM = RAMP["aether"], RAMP["steam"]
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 2, 3, 1

# the model's own colours (from its 48)
DARK = (8, 4, 6)
SKIN = ((25, 56, 10), (38, 79, 7), (52, 105, 7), (75, 138, 13), (112, 188, 34))
BELLY = ((130, 136, 89), (191, 195, 140), (223, 229, 187), (236, 240, 210))
MAW = ((54, 5, 11), (84, 7, 16))
TONGUE = ((216, 30, 62), (230, 38, 97))
TOOTH = (229, 191, 190)
EYE_COLS = {(243, 129, 43), (229, 52, 26), (201, 177, 44), (188, 24, 23), (151, 14, 21)}
HAND_COLS = {(229, 52, 26), (188, 24, 23), (151, 14, 21), (117, 10, 17), (84, 7, 16), (54, 5, 11), (243, 129, 43), DARK}
SPROUT_CAP, SPROUT_LIGHT, SPROUT_STALK = (12, 176, 161), (67, 221, 248), TOOTH

# regions of the model (its own px, facing left)
EYES = ((41, 12, 51, 21), (60, 11, 73, 22))
MOUTH = (53.0, 23.0)
THROAT = (56.0, 31.0)
HAND = (8, 0, 42, 21)               # the raised (casting) hand: its red pixels above the wrist
HAND_POINT = (17, 2)                # where its spells leave it: the raised fingers' tips
SPROUTS = ((40, 45), (70, 40), (55, 60), (88, 56), (33, 68), (97, 30), (62, 80))


def load_base():
    im = Image.open(BASE).convert("RGBA")
    p = im.load()
    return {(x, y): p[x, y][:3] for y in range(im.height) for x in range(im.width) if p[x, y][3]}, im.size


MODEL, (MW, MH) = load_base()
W, H = MW + 2 * MARGIN_X, MH + MARGIN_TOP + MARGIN_BOTTOM
OX, OY = MARGIN_X + 62, MARGIN_TOP + MH        # the origin: under the seat's middle, on the row below the sprite


class Pose:
    def __init__(self, hand=(0, 0), magic=0, blink=False, sac=0.0, mouth=0, sprouts=0):
        self.hand, self.magic, self.blink, self.sac, self.mouth, self.sprouts = hand, magic, blink, sac, mouth, sprouts


def move_hand(px, dx, dy):
    """The raised hand's red pixels (and their dark outline) above its wrist moved (dx, dy); the vacated pixels cleared,
    the wrist's top row stretched to close any gap."""
    if not (dx or dy):
        return px
    x0, y0, x1, y1 = HAND
    sel = {q: c for q, c in px.items() if x0 <= q[0] < x1 and y0 <= q[1] < y1 and c in HAND_COLS}
    out = {q: c for q, c in px.items() if q not in sel}
    for (x, y), c in sel.items():
        out[(x + dx, y + dy)] = c
    if dy < 0:                                       # close the gap under a raised hand with the wrist's colours
        for x in range(x0, x1):
            for k in range(1, -dy + 1):
                if (x, y1 - k) in sel and (x + dx, y1 - k + dy + 1) not in out:
                    out[(x + dx, y1 - k + dy + 1)] = sel[(x, y1 - k)]
    return out


def blink(px):
    out = dict(px)
    for (x0, y0, x1, y1) in EYES:
        eye = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if px.get((x, y)) in EYE_COLS]
        if not eye:
            continue
        mid = sum(y for _, y in eye) / len(eye)
        for (x, y) in eye:
            out[(x, y)] = DARK if abs(y - mid) < 0.6 else (SKIN[3] if y < mid else SKIN[2])
    return out


def ellipse(cx, cy, rx, ry):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                yield (x, y)


def sac(px, s):
    """The throat sac: a pale bubble under the chin, lit from the top-left, its lower edge outlined."""
    if s <= 0:
        return px
    out = dict(px)
    rx, ry = 3.5 + 6.0 * s, 2.5 + 4.0 * s
    cx, cy = THROAT[0], THROAT[1] + 2.0 * s
    pts = set(ellipse(cx, cy, rx, ry))
    for (x, y) in pts:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        lit = -(u * 0.6 + v * 0.8)
        edge = any(q not in pts for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        if edge and v > 0.1:
            out[(x, y)] = DARK
        elif edge:
            out[(x, y)] = BELLY[1]
        else:
            out[(x, y)] = BELLY[3] if lit > 0.35 else BELLY[2] if lit > -0.2 else BELLY[1]
    return out


def mouth(px, level):
    """The mouth open: a dark red maw under the grin's line, teeth along its top, a pink tongue in its bottom."""
    if not level:
        return px
    out = dict(px)
    cx, cy = MOUTH
    rx, ry = 8.5, 1.6 + 1.3 * level
    pts = set(ellipse(cx, cy + ry * 0.5, rx, ry))
    for (x, y) in pts:
        v = (y + 0.5 - (cy + ry * 0.5)) / ry
        edge = any(q not in pts for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        out[(x, y)] = DARK if edge else (MAW[0] if v < 0.2 else TONGUE[0] if level > 1 and v > 0.45 else MAW[1])
    for x in range(int(cx - rx + 2), int(cx + rx - 1), 3):
        y = min(y for (xx, y) in pts if xx == x) + 1 if any(xx == x for (xx, _) in pts) else None
        if y is not None:
            out[(x, y)] = TOOTH
    return out


def magic(px, glow, level, hand):
    """Violet light gathering at the raised fingers (the reference's magic): a cloud of motes round the fingertips, denser and
    brighter at level 2, a white core; drawn in the open air round the hand (never over its own pixels)."""
    cx, cy = HAND_POINT[0] + hand[0], HAND_POINT[1] + hand[1]
    n = 14 + 10 * level
    for i in range(n):
        a = i * 2.39996 + level * 0.7                           # golden-angle spiral: an even, organic scatter
        r = 1.5 + (i / n) ** 0.6 * (4.0 + 2.5 * level)
        q = (int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r)))
        if q in px and px[q] != DARK:
            continue
        c = SM[3] if r < 2.5 else AE[3] if i % 3 else AE[2]
        px[q] = c
        glow[q] = c


def sprouts(px, glow, n):
    for (x, y) in SPROUTS[:n]:
        for (dx, dy, c, g) in ((0, 1, SPROUT_STALK, False), (0, 2, SPROUT_STALK, False), (-1, 0, SPROUT_CAP, True), (0, 0, SPROUT_LIGHT, True),
                               (1, 0, SPROUT_CAP, True), (0, -1, SPROUT_CAP, True), (-2, 1, DARK, False), (2, 1, DARK, False)):
            px[(x + dx, y + dy)] = c
            if g:
                glow[(x + dx, y + dy)] = c


def frame(p):
    px = dict(MODEL)
    px = move_hand(px, *p.hand)
    if p.blink:
        px = blink(px)
    px = sac(px, p.sac)
    px = mouth(px, p.mouth)
    glow = {q: c for q, c in px.items() if c in EYE_COLS and any(q[0] >= e[0] and q[0] < e[2] and q[1] >= e[1] and q[1] < e[3] for e in EYES)}
    if p.magic:
        magic(px, glow, p.magic, p.hand)
    if p.sprouts:
        sprouts(px, glow, p.sprouts)
    shift = (MARGIN_X, MARGIN_TOP)
    return ({(x + shift[0], y + shift[1]): c for (x, y), c in px.items()},
            {(x + shift[0], y + shift[1]): c for (x, y), c in glow.items()})


FRAMES = ([("Idle0", Pose()), ("Idle1", Pose(hand=(-1, -1))), ("Idle2", Pose()), ("Idle3", Pose(blink=True))]
          + [("Cast0", Pose(magic=1)), ("Cast1", Pose(hand=(0, -2), magic=2)), ("Cast2", Pose(hand=(-3, 1), magic=2, mouth=1)),
             ("Cast3", Pose(hand=(-1, 0)))]
          + [("Croak%d" % k, Pose(sac=s, mouth=1 if k == 2 else 0)) for k, s in enumerate((0.35, 0.85, 1.0, 0.4))]
          + [("Tongue0", Pose(mouth=1)), ("Tongue1", Pose(mouth=2)), ("Tongue2", Pose(mouth=1))]
          + [("Fizzle0", Pose(blink=True, mouth=1)), ("Fizzle1", Pose(blink=True, mouth=2, hand=(1, 1)))]
          + [("Intro0", Pose(blink=True)), ("Intro1", Pose())]
          + [("Death%d" % k, Pose(sprouts=n, blink=k >= 2, mouth=1 if k == 3 else 0)) for k, n in enumerate((1, 3, 5, 7))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Cast", "Croak", "Tongue", "Fizzle", "Intro", "Death")


def grid(images):
    rows = (len(images) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((W + 1) * COLUMNS, (H + 1) * rows), (0, 0, 0, 0))
    for k, px in enumerate(images):
        bx, by = (k % COLUMNS) * (W + 1), (k // COLUMNS) * (H + 1)
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                out.putpixel((bx + x, by + y), tuple(c) + (255,))
    return out


def write_rig(path):
    xs = sorted(x for (x, y) in MODEL if 25 <= y <= 95)
    left, right = xs[len(xs) // 40] + MARGIN_X - OX, xs[-len(xs) // 40] + MARGIN_X - OX + 1
    top = 10 + MARGIN_TOP - OY
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def rel(x, y):
        return (x + MARGIN_X - OX) * 2, (y + MARGIN_TOP - OY) * 2
    near = [rel(HAND_POINT[0] + p.hand[0], HAND_POINT[1] + p.hand[1]) for (_, p) in FRAMES]
    mx, my = rel(*MOUTH)
    tx, ty = rel(*THROAT)
    lines = [
        "// <auto-generated> by art/bosses/fungimancer/make_fungimancer_art.py - do not edit by hand. </auto-generated>",
        "namespace Cogpunk.Content.Bosses.Fungimancer",
        "{",
        "\t/// <summary>The Fungimancer's grid sheets (game px, facing left): the model and its glow, equal cells in",
        "\t/// <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is under its seat's middle. Body*: its",
        "\t/// hitbox from the origin. Per frame, from the origin, facing left: NearX/NearY the raised hand (its spells leave it);",
        "\t/// Mouth: the mouth's middle (the tongue leaves it); Throat: under the chin (the croak).</summary>",
        "\tpublic static class FungimancerRigData",
        "\t{",
        "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
        % (W * 2, H * 2, OX * 2, OY * 2, len(FRAMES), COLUMNS),
        "\t\tpublic const int " + ", ".join(seq[:4]) + ";",
        "\t\tpublic const int " + ", ".join(seq[4:]) + ";",
        "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, BodyBottom = 0;" % (left * 2, right * 2, top * 2),
        "\t\tpublic const int MouthX = %d, MouthY = %d, ThroatX = %d, ThroatY = %d;" % (mx, my, tx, ty),
        "\t\tpublic static readonly short[] NearX = { %s };" % ", ".join(str(a) for a, _ in near),
        "\t\tpublic static readonly short[] NearY = { %s };" % ", ".join(str(b) for _, b in near),
        "\t}",
        "}",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("wrote", path)


def crop(px, keep):
    sel = {q: c for q, c in px.items() if keep(q[0] - MARGIN_X, q[1] - MARGIN_TOP)}
    xs, ys = [x for x, _ in sel], [y for _, y in sel]
    return to_image(sel, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    export(grid([f[0] for f in frames]), OUT + "Fungimancer.png")
    export(grid([f[1] for f in frames]), OUT + "Fungimancer_Glow.png")
    for stale in ("Fungimancer_Far.png", "Fungimancer_Near.png"):     # v1/v2's planes: the model is one plane now
        if os.path.exists(OUT + stale):
            os.remove(OUT + stale)
            print("removed", OUT + stale)
    write_rig(OUT + "FungimancerRigData.cs")
    base = frames[0][0]
    export(crop(base, lambda x, y: 41 <= x <= 73 and 9 <= y <= 28), OUT + "Fungimancer_Head_Boss.png")
    dead = frames[INDEX["Death3"]][0]
    export(crop(dead, lambda x, y: y < 30), OUT + "Gores/Fungimancer_GoreHead.png")
    export(crop(dead, lambda x, y: 30 <= y < 82), OUT + "Gores/Fungimancer_GoreBody.png")
    export(crop(dead, lambda x, y: y >= 82), OUT + "Gores/Fungimancer_GoreSeat.png")
    export(things.spore_bolt(), OUT + "Projectiles/SporeBolt.png")
    export(things.shroom_spike(), OUT + "Projectiles/ShroomSpike.png")
    export(things.tongue_tip(), OUT + "Projectiles/FungimancerTongue.png")
    export(things.bag(), OUT + "Items/FungimancerBag.png")
    export(things.summon_item(), OUT + "Items/RainbowMushroom.png")
    export(things.tile_sheet(), OUT + "Tiles/RainbowMushroomTile.png")
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames")
    args = ap.parse_args()
    if args.frames:
        pick = args.frames.split(",")
        frames = [frame(p) for (n, p) in FRAMES if n in pick]
    else:
        frames = export_all()
    if args.preview:
        sc = 3
        cols = min(4, len(frames))
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * (W * sc + 8) + 8, rows * (H * sc + 8) + 8), (24, 24, 30, 255))
        for k, (px, gl) in enumerate(frames):
            im = Image.new("RGBA", (W, H), (30, 34, 60, 255))
            for (x, y), c in px.items():
                if 0 <= x < W and 0 <= y < H:
                    im.putpixel((x, y), tuple(c) + (255,))
            sheet.alpha_composite(im.resize((W * sc, H * sc), Image.NEAREST), (8 + (k % cols) * (W * sc + 8), 8 + (k // cols) * (H * sc + 8)))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
