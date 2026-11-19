"""The Jade Token and its spirit fox (2026-11-18, redrawn 2026-11-19). Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--preview FILE]

User, 2026-11-18: "on the top chest of the main mansion on coghaven add a new pet item that allways spawn there called "jade
token" it should give the player a small jade colored spirit fox (ensure seamless animations and behavior like our other pet
from the mod) that emits a bit of light". The design came as an image (reference/jade_fox_user_2026-11-18.webp); after traces
of it at 40% and 60% (the user: "keep the 60% version"), 2026-11-19: "The polish is worse, you dont have to maintain the gold
details if it would damage actual boddy format or face expression. Also if i gave you the base model why then not just redraw
at smaller size and less pixels (like the smaller model i sent as example before) without ruining the idea and face
expresssion instead of compacting/resizing it which causes quality loss", and, while it was being drawn: "forget the green
effects of the tail just make it a bit longer fenekin fox tail right now its too round".

So the fox is drawn by hand at pet size (FOX, 36 x 27 at 1x, the trace's size and layout), every pixel chosen like a vanilla
critter's: the user's fox in clean clusters lit from the top-left, the jade ears with pale insides (the far one behind), the
face kept readable (a big jade eye with a glint under its lid, the gilt mask's arc round it, the pointed muzzle and nose),
the white ruff and the gilt collar with its jade pendant, slender legs (the near ones pale with gilt bracelets, the far ones
jade), and a long fluffy brush of a tail sweeping back and curling up (no spirit fire since 2026-11-19). The traced and the
earlier foxes are in previous/.

Faces right (the pet flips by direction), its feet on the cell's bottom row. Animated by whole-pixel moves of its parts (the
regions in part_of(): the head, the body, the tail, four legs), never resampled (D4: no colour changes in place):
  Idle 0-3       breathing (a pixel), the tail's tip swaying                                           (loop)
  Trot 4-9       diagonal pairs: the swinging pair's paws a pixel forward and lifted, the other back; a pixel's bob (loop)
  Float 10-13    the spirit float: paws tucked up, the tail streaming back                             (loop)
  Settle 14-15   sinking over its legs
  Sleep 16-17    lying, the forepaws out, the eye shut, its head nodding as it breathes               (loop)
  Wake 18-20     the eye open, a stretch (forepaws out), standing
Outputs (Content/Coghaven/Pets/): JadeFoxPet.png + JadeFoxPet_Glow.png (21 frames of CELL_W x CELL_H, 1 px apart; the glow
sheet: the eye and the jade gems, full-bright in game: "a bit of light"), JadeToken.png (the item: a jade coin with a fox's
head, a gilt rim), JadeFoxBuff.png (the buff: the fox's head).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP, Xf, Ellipse, Canvas, dome, finish  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Coghaven/Pets/"
GH, G, E, S = (RAMP[k] for k in ("ghost", "gilt", "emerald", "sage"))
CHARS = "ABCDEFG" + "abcdef" + "0123456789"        # emerald A (darkest) .. G, sage a .. f, gilt 0 .. 9
COLOUR = dict(zip(CHARS, E + S + G))

FOX = (
    "...........................A........",
    "..........................AEA.......",
    "..........................AEDA....AA",
    ".........................AEeDA...AEA",
    "....aaa..................AEefDA.AEDA",
    "...affea.................ADefeDAADeA",
    "..affffa.................ACeffeDDeDA",
    "..affffea...............AaeffffeefeA",
    "..affffeea..............aef7777ffffa",
    "..afffdfeea............aef76aaaffffa",
    "..afffffffea...........aef6aGEEafffA",
    "..aefdfffffeaa.........adef6CEDafea.",
    "..aeeffffdfffeaaa......adeffaafeeca.",
    "...aeefdffffdfffea..aaaaddeeffeccaa.",
    "...aeeeedfffffaaaaaaefdaadeeedcaa...",
    "....adeeeeeeffaeffffffeeffeedca.....",
    ".....adddeddeeafffffeefe77665a......",
    "......aaddddddaffffeeefeeff7Fa......",
    "........aaaaaaaeeeeeeeeeedeeEa......",
    "..............aeeeddddeededdDa......",
    ".............bdddddcccddadcda.......",
    ".............bcccccbbbbba..aea......",
    ".............aeeaACBA....aeeaACBA...",
    ".............aeeaACBA....aeeaACBA...",
    ".............a64aACBA....a75aA4BA...",
    ".............aeeeaCDA....aeffaCDA...",
    ".............aaaaaAAA....aaaaaAAA...",
)
GROUND = len(FOX) - 1                               # the paws' bottom row
EYE_PX = ((28, 10), (29, 10), (30, 10), (28, 11), (29, 11), (30, 11))             # the eye's glowing pixels
EYE_SHUT = ((28, 9, "f"), (29, 9, "f"), (30, 9, "f"), (28, 10, "a"), (29, 10, "a"), (30, 10, "a"),
            (28, 11, "e"), (29, 11, "f"), (30, 11, "e"))                          # the lid's line a row lower, fur over it
TAIL_TIP_ROW = 10                                   # the tail sways above this row
CELL_W = len(FOX[0]) + 4
CELL_H = GROUND + 1 + 3
SX, SY = 2, CELL_H - 1 - GROUND                     # sprite px -> cell px
OX = SX + 22                                        # cell column under the middle of its body (the pet's OriginX / 2)


def part_of(x, y):
    """The part a pixel of FOX belongs to: the four legs below the belly (back to front by column), the tail behind the
    rump, the head above the ruff, the body the rest."""
    if y >= 22:
        if x <= 16 or (x == 17 and y >= 25):
            return "HN"
        if x <= 20:
            return "HF"
        if x <= 28 or (x == 29 and y >= 25):
            return "FN"
        return "FF"
    if x <= 14 and y <= 18:
        return "tail"
    if x >= 22 and y <= 12:
        return "head"
    return "body"


PARTS = {k: {} for k in ("tail", "body", "head", "HN", "HF", "FN", "FF")}
for _y, _r in enumerate(FOX):
    for _x, _ch in enumerate(_r):
        if _ch != ".":
            PARTS[part_of(_x, _y)][(_x, _y)] = _ch


class Pose:
    def __init__(self, body=0, head=0, sway=0, legs=None, lying=False, eye=True, paws=1):
        self.body = body                            # rows the body, head and tail sit lower (< 0: higher, legs stretched)
        self.head = head                            # rows the head nods lower still (>= 0: no gap at the neck)
        self.sway = sway                            # px the tail's tip leans (- back, + forward)
        self.legs = legs or {}                      # leg -> (paw shift, lift)
        self.lying = lying                          # legs folded under: only the forepaws show, out in front
        self.eye = eye
        self.paws = paws                            # lying: how far the forepaws reach out


def _leg(pix, shift, lift):
    """A leg with its paw row shifted `shift` px (the rows above shifted in proportion) and raised `lift` rows (its top
    under the fur)."""
    if not pix:
        return {}
    y0, y1 = min(y for _, y in pix), max(y for _, y in pix)
    n = max(1, y1 - y0)
    return {(x + int(round(shift * (y - y0) / n)), y - lift): c for (x, y), c in pix.items()}


def fox(p):
    """(pixels, glow): {(x, y): char} in sprite px, back to front: far legs, near legs, tail, body, head."""
    layers = []
    if p.lying:
        for k in ("FF", "FN"):
            paw_y = max(y for _, y in PARTS[k])
            layers.append({(x + p.paws, y): c for (x, y), c in PARTS[k].items() if y >= paw_y - 1})
    else:
        for k in ("HF", "FF", "HN", "FN"):
            shift, lift = p.legs.get(k, (0, 0))
            leg = _leg(PARTS[k], shift, lift)
            if p.body < 0 and leg:                  # the body raised: the legs' tops stretched up under it
                top = min(y for _, y in leg)
                for (x, y), c in list(leg.items()):
                    if y == top:
                        for d in range(1, -p.body + 1):
                            leg[(x, y - d)] = c
            layers.append(leg)
    tail = {}
    for (x, y), c in PARTS["tail"].items():
        dx = p.sway if y < TAIL_TIP_ROW - 3 else (int(math.copysign(1, p.sway)) if p.sway and y < TAIL_TIP_ROW else 0)
        tail[(x + dx, y + p.body)] = c
    layers.append(tail)
    layers.append({(x, y + p.body): c for (x, y), c in PARTS["body"].items()})
    hy = p.body + p.head
    head = {(x, y + hy): c for (x, y), c in PARTS["head"].items()}
    if not p.eye:
        for (x, y, c) in EYE_SHUT:
            if (x, y + hy) in head:
                head[(x, y + hy)] = c
    layers.append(head)
    pix, glow = {}, {}
    for lp in layers:
        for q, c in lp.items():
            if q[1] > GROUND:
                continue
            pix[q] = c
            if c in "FG":
                glow[q] = c
            else:
                glow.pop(q, None)
    if p.eye:
        for (x, y) in EYE_PX:
            q = (x, y + hy)
            if q in pix and pix[q] in "CDEFG":
                glow[q] = pix[q]
    return pix, glow


TAU = 2 * math.pi


def trot(k):
    """Six frames: the near foreleg with the far hind leg, then the far foreleg with the near hind leg, swing a pixel forward
    with the paw lifted while the other pair pushes back; a pixel's bob at mid-stride; the tail's tip bouncing."""
    ph = k / 6.0 * TAU

    def leg(off):
        s = math.sin(ph + off)
        return (int(round(s)), 1 if math.cos(ph + off) > 0.5 else 0)
    legs = {"FN": leg(0.0), "HF": leg(0.0), "FF": leg(math.pi), "HN": leg(math.pi)}
    return Pose(body=-1 if k % 3 == 1 else 0, legs=legs, sway=-1 if k % 3 == 2 else 0)


TUCK = {"FN": (-1, 2), "FF": (-1, 2), "HN": (1, 2), "HF": (1, 2)}
POSES = (
    [Pose(body=b, sway=s) for (b, s) in ((0, 0), (0, -1), (1, -1), (1, 0))]                                        # idle
    + [trot(k) for k in range(6)]                                                                                   # trot
    + [Pose(body=b, legs=TUCK, sway=s) for (b, s) in ((0, -1), (-1, -2), (-1, -1), (0, -2))]                        # float
    + [Pose(body=2), Pose(body=4, lying=True)]                                                                      # settle
    + [Pose(body=5, lying=True, eye=False), Pose(body=5, head=1, lying=True, eye=False)]                           # sleep
    + [Pose(body=5, lying=True, sway=-1),                                                                           # wake
       Pose(body=2, legs={"FN": (1, 0), "FF": (1, 0)}, sway=1),
       Pose()]
)
FRAMES = len(POSES)


def sheet(glow=False):
    im = Image.new("RGBA", (CELL_W, (CELL_H + 1) * FRAMES), (0, 0, 0, 0))
    for k, p in enumerate(POSES):
        pix, gl = fox(p)
        for (x, y), c in (gl if glow else pix).items():
            cx, cy = x + SX, y + SY
            if not (0 <= cx < CELL_W and 0 <= cy < CELL_H):
                raise SystemExit("frame %d: pixel (%d, %d) outside the %dx%d cell" % (k, x, y, CELL_W, CELL_H))
            im.putpixel((cx, cy + k * (CELL_H + 1)), COLOUR[c] + (255,))
    return im


def token():
    """The Jade Token: a round jade coin, a gilt rim lit top-left, a fox's head in relief on its face."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(7.0, 7.0, 6.6, 6.6), "gilt", dome(5.0, 5.0, 7.0, lo=3, hi=8, gain=1.3, fixed=True), rust=0.0)
    cv.part(Xf(), Ellipse(7.0, 7.0, 5.0, 5.0), "ghost", dome(5.6, 5.4, 6.0, lo=1, hi=4, gain=1.2, fixed=True), rust=0.0, outline=False)
    head = ((5, 4, GH[5]), (8, 4, GH[5]), (5, 5, GH[4]), (6, 5, GH[4]), (7, 5, GH[4]), (8, 5, GH[4]), (5, 6, GH[4]), (6, 6, GH[0]),
            (7, 6, GH[4]), (8, 6, GH[0]), (6, 7, GH[4]), (7, 7, GH[4]), (6, 8, GH[3]), (7, 8, GH[2]), (4, 3, GH[4]), (9, 3, GH[3]))
    finish(cv)
    for (x, y, c) in head:                                      # the relief, stamped after the finish (small details)
        cv.put(x, y, c)
    return cv


def buff_icon():
    """The buff: the fox's head from FOX (its ears, the gilt mask, the jade eye, the muzzle), centred in 16 x 16."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x, y), c in PARTS["head"].items():
        bx, by = x - 21, y + 1
        if 0 <= bx < 16 and 0 <= by < 16:
            im.putpixel((bx, by), COLOUR[c] + (255,))
    return im


def boxed(cv, w, h, dx=0, dy=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs, ys = [x for x, _ in cv.px], [y for _, y in cv.px]
    ox = (w - (max(xs) - min(xs) + 1)) // 2 - min(xs) + dx
    oy = (h - (max(ys) - min(ys) + 1)) // 2 - min(ys) + dy
    for (x, y), c in cv.px.items():
        if 0 <= x + ox < w and 0 <= y + oy < h:
            im.putpixel((x + ox, y + oy), tuple(c) + (255,))
    return im


def outputs():
    return {
        OUT + "JadeFoxPet.png": sheet(),
        OUT + "JadeFoxPet_Glow.png": sheet(glow=True),
        OUT + "JadeToken.png": boxed(token(), 14, 14),
        OUT + "JadeFoxBuff.png": buff_icon(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    out = outputs()
    for rel, im in out.items():
        export(im, rel)
    print("cell %d x %d, ground row %d, OriginX %d (2x)" % (CELL_W, CELL_H, GROUND, OX * 2))
    if args.preview:
        base = out[OUT + "JadeFoxPet.png"]
        sc, cols = 6, 7
        rows = (FRAMES + cols - 1) // cols
        sheet_im = Image.new("RGBA", (cols * (CELL_W * sc + 8), rows * (CELL_H * sc + 8)), (30, 30, 36, 255))
        for k in range(FRAMES):
            cell = Image.new("RGBA", (CELL_W, CELL_H), (30, 30, 36, 255))
            cell.alpha_composite(base.crop((0, k * (CELL_H + 1), CELL_W, k * (CELL_H + 1) + CELL_H)))
            sheet_im.paste(cell.resize((CELL_W * sc, CELL_H * sc), Image.NEAREST), ((k % cols) * (CELL_W * sc + 8), (k // cols) * (CELL_H * sc + 8)))
        sheet_im.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
