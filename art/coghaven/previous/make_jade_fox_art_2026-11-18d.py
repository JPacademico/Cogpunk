"""The Jade Token and its spirit fox (2026-11-18). Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--trace] [--preview FILE]

User, 2026-11-18: "on the top chest of the main mansion on coghaven add a new pet item that allways spawn there called "jade
token" it should give the player a small jade colored spirit fox (ensure seamless animations and behavior like our other pet
from the mod) that emits a bit of light". The same day the design came as an image (reference/jade_fox_user_2026-11-18.webp:
upscaled pixel art, ~6 px a pixel), then: "maintain most of the detail density level of the original i sent just remove the
particles and resize without destroying the original design", and, shown the traces made on the way: "Use this version as it
was the best but dechease the size by 60% as the current size its too big." Shown 40% and 60% of it: "keep the 60% version
but polish details that were lost on size deacreasing if possible".

So the fox is that version: the image traced (trace()), made smaller (SCALE: 60% of the 62 x 45 trace the user picked):
  1. the fox alone: the image's largest opaque piece (the floating leaves, sparks and loose wisps are separate pieces: gone);
  2. every pixel to the nearest colour (CIELAB) of the Emerald, Sage and Gilt ramps (they match its greens, pale fur, gold);
  3. the fur's and the fire's shades smoothed: each pixel the median shade of its ramp over a WINDOW px square (the image's
     one-pixel fur strands otherwise turn to noise), outlines and gold left as they are;
  4. each sprite pixel (F px of the image) the most common colour of its patch, outlines weighted down (W_DARK), gold up
     (W_GOLD), filled when 45% of the patch is;
  5. the silhouette outlined with each ramp's darkest shade.
The trace is cached in TRACE_FILE (--trace remakes it); its loose specks (under 4 px) are dropped. Then POLISH: a few pixels
placed by hand where the shrink lost a feature. A sprite pixel is the vote of a 30 x 30 px patch of the image, so a feature
smaller than half a patch (the eye, the forehead gem, the pendant's tassel, the pale paws) loses its patch to the fur round
it; vanilla's small sprites keep their faces because each feature is drawn at a readable size on purpose (a 2-3 px eye with
a glint), and POLISH does that for these few: everything else is the trace. The 2026-11-18 versions before (two procedural
foxes and a hand-finished trace) are in previous/.

Faces right (the pet flips by direction), its feet on the cell's bottom row. Animated by whole-pixel moves of its parts (the
regions in part_of(): the head, the body, the tail and fire, four legs), never resampled (D4: no colour changes in place):
  Idle 0-3       breathing (a pixel), the fire's top swaying and flickering                          (loop)
  Trot 4-9       diagonal pairs: the swinging pair's paws a pixel forward and lifted, the other back; a pixel's bob (loop)
  Float 10-13    the spirit float: paws tucked up, the fire licking                                  (loop)
  Settle 14-15   sinking over its legs
  Sleep 16-17    lying, the forepaws out, the eye shut, the fire low, its head nodding as it breathes (loop)
  Wake 18-20     the eye open, a stretch (forepaws out), standing
Outputs (Content/Coghaven/Pets/): JadeFoxPet.png + JadeFoxPet_Glow.png (21 frames of CELL_W x CELL_H, 1 px apart; the glow
sheet: the fire, the eye and the gems, full-bright in game: "a bit of light"), JadeToken.png (the item: a jade coin with a
fox's head, a gilt rim), JadeFoxBuff.png (the buff: the fox's head, traced the same way at 16 px).
"""
import argparse
import math
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "jadey"))
from westbots import RAMP, Xf, Ellipse, Canvas, dome, finish  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402
import user_art  # noqa: E402

OUT = "Content/Coghaven/Pets/"
REF = "art/coghaven/reference/jade_fox_user_2026-11-18.webp"
GH, G, E, S = (RAMP[k] for k in ("ghost", "gilt", "emerald", "sage"))
PAL = E + S + G
CHARS = "ABCDEFG" + "abcdef" + "0123456789"        # emerald A (darkest) .. G, sage a .. f, gilt 0 .. 9
COLOUR = dict(zip(CHARS, PAL))
DARK = "ABa01"                                      # the outline shades (weighted down)

BASE_F = 18.2                                       # image px per sprite px of the trace the user picked (62 x 45)
SCALE = 0.6                                         # user, 2026-11-18: "keep the 60% version"
F = BASE_F / SCALE
ORIGIN = (179, 117)                                 # the image px where sprite px (0, 0) starts
WINDOW, W_DARK, W_GOLD = 25, 0.6, 1.6               # the picked trace's settings
TRACE_FILE = "art/coghaven/reference/jade_fox_trace_%d.txt" % round(SCALE * 100)
BUFF_FILE = "art/coghaven/reference/jade_fox_trace_buff.txt"
BUFF_F, BUFF_RECT = 30.0, (834, 117, 1310, 540)     # the head alone (image px), traced to fit the 16 x 16 buff icon


# ================================================================================================
# The trace
# ================================================================================================
def _to_lab(rgb):
    v = rgb / 255.0
    lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    x = (lin[..., 0] * 0.4124 + lin[..., 1] * 0.3576 + lin[..., 2] * 0.1805) / 0.95047
    y = lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722
    z = (lin[..., 0] * 0.0193 + lin[..., 1] * 0.1192 + lin[..., 2] * 0.9505) / 1.08883

    def f(t):
        return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)
    fx, fy, fz = f(x), f(y), f(z)
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)


def _boxsum(m, r):
    c = np.cumsum(np.cumsum(np.pad(m.astype(np.int32), ((r + 1, r), (r + 1, r))), axis=0), axis=1)
    return c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]


def _indexed():
    """The image as palette indices (-1 clear): only its largest opaque piece, every pixel the nearest palette colour, the
    fur's and fire's shades smoothed per ramp over WINDOW px."""
    a = np.asarray(Image.open(REF).convert("RGBA")).astype(np.float64)
    h, w = a.shape[:2]
    opaque = a[:, :, 3] >= 200
    label = np.zeros((h, w), dtype=np.int32)
    sizes, cur = {}, 0
    for y in range(h):
        for x in np.nonzero(opaque[y])[0]:
            if label[y, x]:
                continue
            cur += 1
            q = deque([(y, int(x))])
            label[y, x] = cur
            n = 0
            while q:
                cy, cx = q.popleft()
                n += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and opaque[ny, nx] and not label[ny, nx]:
                            label[ny, nx] = cur
                            q.append((ny, nx))
            sizes[cur] = n
    keep = label == max(sizes, key=sizes.get)
    labs = np.array([user_art.lab(c) for c in PAL])
    lab = _to_lab(a[:, :, :3])
    idx = ((lab[:, :, None, :] - labs[None, None, :, :]) ** 2).sum(axis=-1).argmin(axis=-1)
    idx[~keep] = -1
    r = WINDOW // 2
    smooth = idx.copy()
    for shades in ([CHARS.index(c) for c in "bcdef"], [CHARS.index(c) for c in "CDEFG"]):
        member = np.isin(idx, shades)
        tot = np.zeros((h, w), dtype=np.int32)
        cums = []
        for k in shades:
            tot = tot + _boxsum(idx == k, r)
            cums.append(tot.copy())
        half = (tot + 1) // 2
        med = np.full((h, w), shades[-1])
        done = np.zeros((h, w), dtype=bool)
        for k, cu in zip(shades, cums):
            hit = (~done) & (cu >= half)
            med[hit] = k
            done |= hit
        smooth[member] = med[member]
    return smooth


def trace(idx, f, rect=None):
    """Rows of chars: each sprite pixel the most common colour of its f x f patch (outlines x W_DARK, gold x W_GOLD), the
    silhouette outlined with each ramp's darkest shade. rect (x0, y0, x1, y1): only that part of the image."""
    h, w = idx.shape
    x0, y0 = ORIGIN if rect is None else rect[:2]
    x1, y1 = (w, h) if rect is None else rect[2:]
    wt = np.ones(len(PAL))
    for c in DARK:
        wt[CHARS.index(c)] = W_DARK
    for c in "23456789":
        wt[CHARS.index(c)] = W_GOLD
    tw, th = int((x1 - x0) / f) + 2, int((y1 - y0) / f) + 2
    out = {}
    for ty in range(th):
        for tx in range(tw):
            ya, yb = int(round(y0 + ty * f)), int(round(y0 + (ty + 1) * f))
            xa, xb = int(round(x0 + tx * f)), int(round(x0 + (tx + 1) * f))
            blk = idx[max(0, ya):min(h, yb, y1), max(0, xa):min(w, xb, x1)]
            if blk.size == 0:
                continue
            m = blk >= 0
            if m.mean() < 0.45:
                continue
            out[(tx, ty)] = CHARS[int((np.bincount(blk[m], minlength=len(PAL)) * wt).argmax())]
    fin = {}
    for (x, y), ch in out.items():
        edge = any((x + dx, y + dy) not in out for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        fin[(x, y)] = ("A" if ch.isupper() else "a" if ch.islower() else ch) if edge and not ch.isdigit() else ch
    xs, ys = [x for x, _ in fin], [y for _, y in fin]
    return ["".join(fin.get((x, y), ".") for x in range(max(xs) + 1)) for y in range(max(ys) + 1)]


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return [r for r in fh.read().split("\n") if r]


def remake_traces():
    idx = _indexed()
    for path, rows in ((TRACE_FILE, trace(idx, F)), (BUFF_FILE, trace(idx, BUFF_F, BUFF_RECT))):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        print("traced %s (%d x %d)" % (path, max(len(r) for r in rows), len(rows)))


if not (os.path.exists(TRACE_FILE) and os.path.exists(BUFF_FILE)):
    remake_traces()
def _without_specks(rows, smallest=4):
    """The trace less its specks: pieces under `smallest` px (8-connected) are what's left of the fire's loose wisps at this
    size (the user asked the particles out)."""
    pix = {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."}
    seen, drop = set(), set()
    for start in sorted(pix):
        if start in seen:
            continue
        piece, stack = [], [start]
        seen.add(start)
        while stack:
            cx, cy = stack.pop()
            piece.append((cx, cy))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (cx + dx, cy + dy)
                    if q in pix and q not in seen:
                        seen.add(q)
                        stack.append(q)
        if len(piece) < smallest:
            drop.update(piece)
    return ["".join("." if (x, y) in drop else ch for x, ch in enumerate(r)) for y, r in enumerate(rows)]


# The features the shrink lost, placed by hand at 60% (x, y, colour), each on its spot in the image:
POLISH = {
    0.6: (
        (30, 10, "G"), (31, 10, "E"), (32, 10, "B"),                          # the eye: a glint, the iris, the corner under its lid
        (33, 6, "7"), (34, 7, "5"), (33, 7, "F"), (32, 8, "6"), (33, 8, "E"),  # the forehead diamond: a gilt frame, a lit jade
        (34, 8, "4"), (33, 9, "3"),
        (30, 16, "F"), (31, 16, "D"), (31, 17, "6"),                          # the pendant: its lit gem, the gilt bead,
        (31, 18, "E"), (31, 19, "D"), (31, 20, "C"),                          # the green tassel
        (27, 24, "f"), (28, 24, "e"), (29, 24, "d"), (16, 24, "e"), (21, 24, "c"),   # the paws, pale as in the image
    ),
}
# The eye (glowing) and the eye shut (the lid's dark line a row lower, fur over it): at 60%
EYE_OPEN = {0.6: ((30, 10), (31, 10), (32, 10))}
EYE_SHUT = {0.6: ((30, 9, "e"), (31, 9, "f"), (30, 10, "a"), (31, 10, "a"), (32, 10, "e"))}


def _polished(rows):
    grid = [list(r) for r in rows]
    for (x, y, c) in POLISH.get(SCALE, ()):
        if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
            grid[y][x] = c
    return ["".join(r) for r in grid]


TRACED = _polished(_without_specks(_read(TRACE_FILE)))
GROUND = max(y for y, r in enumerate(TRACED) if r.strip("."))


# ================================================================================================
# Parts (regions in the picked trace's px, so they hold at any SCALE)
# ================================================================================================
def part_of(x, y):
    bx, by = (x + 0.5) / SCALE, (y + 0.5) / SCALE
    if by >= 36.5:                                  # below the long fur: the four legs, back to front by column
        return "HN" if bx < 32 else "HF" if bx < 40 else "FN" if bx < 48 else "FF"
    if bx < 26:
        return "tail"
    if bx >= 37.5 and by < 21.5:
        return "head"
    return "body"


PARTS = {k: {} for k in ("tail", "body", "head", "HN", "HF", "FN", "FF")}
for _y, _r in enumerate(TRACED):
    for _x, _ch in enumerate(_r):
        if _ch != ".":
            PARTS[part_of(_x, _y)][(_x, _y)] = _ch
EYE_PX = EYE_OPEN.get(SCALE, ((int(51.5 * SCALE), int(16.5 * SCALE)),))   # the eye (the picked trace's px 51.5, 16.5)
SHUT_PX = EYE_SHUT.get(SCALE, tuple((x, y, "b") for (x, y) in EYE_PX))
FIRE_ROW = int(19 * SCALE)                          # the fire above this row moves (flickers, sways)
CELL_W = max(len(r) for r in TRACED) + 4
CELL_H = GROUND + 1 + 3
SX, SY = 2, CELL_H - 1 - GROUND                     # sprite px -> cell px
OX = SX + int(round(40 * SCALE))                    # cell column under the middle of its body (the pet's OriginX / 2)


class Pose:
    def __init__(self, body=0, head=0, sway=0, phase=0.0, amp=1.0, legs=None, lying=False, eye=True, paws=1):
        self.body = body                            # rows the body, head and tail sit lower (< 0: higher, legs stretched)
        self.head = head                            # rows the head nods lower still (>= 0: no gap at the neck)
        self.sway = sway                            # px the fire's top leans
        self.phase, self.amp = phase, amp           # the fire's flicker
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
    out = {}
    for (x, y), c in pix.items():
        dx = int(round(shift * (y - y0) / n))
        out[(x + dx, y - lift)] = c
    return out


def fox(p):
    """(pixels, glow): {(x, y): char} in sprite px, back to front: far legs, near legs, tail and fire, body, head."""
    layers = []
    if p.lying:
        for k in ("FF", "FN"):
            paw_y = max(y for _, y in PARTS[k])
            layers.append(("legs", {(x + p.paws, y): c for (x, y), c in PARTS[k].items() if y == paw_y}))
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
            layers.append(("legs", leg))
    tail = {}
    for (x, y), c in PARTS["tail"].items():
        if y <= FIRE_ROW:
            w = (FIRE_ROW + 1 - y) / float(FIRE_ROW + 1)
            x += p.sway if y <= FIRE_ROW - 1 else 0
            x += int(round(p.amp * w * math.sin(p.phase + y * 1.3)))
        tail[(x, y + p.body)] = c
    layers.append(("tail", tail))
    layers.append(("body", {(x, y + p.body): c for (x, y), c in PARTS["body"].items()}))
    hy = p.body + p.head
    head = {(x, y + hy): c for (x, y), c in PARTS["head"].items()}
    if not p.eye:
        for (x, y, c) in SHUT_PX:
            if (x, y + hy) in head:
                head[(x, y + hy)] = c
    layers.append(("head", head))
    pix, glow = {}, {}
    for kind, lp in layers:
        for q, c in lp.items():
            if q[1] > GROUND:
                continue
            pix[q] = c
            if c in "FG" or (kind == "tail" and c == "E"):
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
    with the paw lifted while the other pair pushes back; a pixel's bob at mid-stride."""
    ph = k / 6.0 * TAU

    def leg(off):
        s = math.sin(ph + off)
        return (int(round(s)), 1 if math.cos(ph + off) > 0.5 else 0)
    legs = {"FN": leg(0.0), "HF": leg(0.0), "FF": leg(math.pi), "HN": leg(math.pi)}
    return Pose(body=-1 if k % 3 == 1 else 0, legs=legs, sway=-1 if k % 3 == 2 else 0, phase=ph)


TUCK = {"FN": (-1, 1), "FF": (-1, 1), "HN": (1, 1), "HF": (1, 1)}
POSES = (
    [Pose(body=b, sway=s, phase=k / 4.0 * TAU) for k, (b, s) in enumerate(((0, 0), (0, -1), (1, -1), (1, 0)))]           # idle
    + [trot(k) for k in range(6)]                                                                                       # trot
    + [Pose(body=b, legs=TUCK, sway=-1, phase=k / 4.0 * TAU, amp=1.5) for k, b in enumerate((0, -1, -1, 0))]            # float
    + [Pose(body=1, phase=0.6, amp=0.8), Pose(body=2, lying=True, phase=1.4, amp=0.6)]                                  # settle
    + [Pose(body=2, lying=True, eye=False, phase=0.0, amp=0.4), Pose(body=2, head=1, lying=True, eye=False, phase=math.pi, amp=0.4)]
    + [Pose(body=2, lying=True, phase=0.8, amp=0.6),                                                                    # wake
       Pose(body=1, legs={"FN": (1, 0), "FF": (1, 0)}, phase=2.0, amp=0.9),
       Pose(phase=3.2)]
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
    """The buff: the fox's head traced like the fox (BUFF_FILE), centred in 16 x 16."""
    rows = _read(BUFF_FILE)
    w, h = max(len(r) for r in rows), len(rows)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    ox, oy = (16 - w) // 2, max(0, 16 - h)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != "." and 0 <= x + ox < 16 and 0 <= y + oy < 16:
                im.putpixel((x + ox, y + oy), COLOUR[ch] + (255,))
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
    ap.add_argument("--trace", action="store_true", help="remake the cached traces from the image")
    ap.add_argument("--preview")
    args = ap.parse_args()
    if args.trace:
        remake_traces()
        raise SystemExit("traces remade: run again without --trace")
    out = outputs()
    for rel, im in out.items():
        export(im, rel)
    print("cell %d x %d, ground row %d, OriginX %d (2x)" % (CELL_W, CELL_H, GROUND, OX * 2))
    if args.preview:
        base = out[OUT + "JadeFoxPet.png"]
        sc, cols = 8, 7
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
