"""The Jade Token and its spirit fox (2026-11-18). Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--preview FILE]

User, 2026-11-18: "on the top chest of the main mansion on coghaven add a new pet item that allways spawn there called "jade
token" it should give the player a small jade colored spirit fox (ensure seamless animations and behavior like our other pet
from the mod) that emits a bit of light". Then, the same day: "the fox spirit design is underwelming use the design i provided
on the example image of this prompt (resise and update if needed)", and, after a redraw that was still too plain: "verify the
jade fox as you simplified too much! maintain most of the detail density level of the original i sent just remove the
particles and resize without destroying the original design. you are making it too simplistic wich is ruining ani facil
detailt it should have. adjust the behaviour animations after".

So the fox IS the user's design (reference/jade_fox_user_2026-11-18.webp: upscaled pixel art, ~6 px a pixel, ~184 x 131 art
pixels), shrunk a third (each sprite pixel ~3 x 3 of its pixels, 18.2 px of the image) into the Cogpunk palette (the
Emerald, Sage and Gilt ramps match its greens, pale fur and gold), the floating leaves and sparks left out:
  * the body (fur, the hip, the collar's gilt scrolls, the gilt vine on the near foreleg) is the image itself, traced:
    every pixel the most common palette colour of its 18 x 18 patch, the fur's and flame's shades first smoothed over a
    25 px window so their one-pixel strands don't turn to noise, outlines weighted down, gold up (BODY);
  * what can't survive the shrink is redrawn pixel by pixel on the same grid, side by side with the image: the head (the
    tall emerald ears with their gilt rims and pale inner fur, the gilt headpiece with its jade diamond, the gilt mask and
    its curl round the big glowing eye, the muzzle and nose, the fur tufts and the green mane: HEAD), the four slender legs
    under the long fur (gilt bracelets with jade gems on the forelegs, the gilt chevron on the near hind leg, the bronze
    band on the far one, emerald far legs: NF, FF, NH, FH), the collar's jade pendant with its bead and green tassel
    (PENDANT), and the hip's gilt spiral (HIP_SWIRL);
  * the tail and its spirit fire are drawn as strokes along the image's own curves (tail_and_flame): the four tongues
    licking up and out (one curling over at the top), the pale tail rolled round a green heart with its gilt swirl, the
    green strands sweeping back under the rump; drawn from numbers, the fire can flicker frame by frame.
The 2026-11-18 procedural foxes (two) are in previous/.

Faces right (the pet flips by direction), lit from the top-left; its feet on the cell's bottom row. Parts, back to front:
far hind leg, far foreleg, near hind leg, near foreleg, the tail and fire, the body (with the pendant), the head; every
frame is the parts moved by whole pixels (and the legs sheared row by row), so no pixel changes colour in place (D4):
  Idle 0-3       standing, breathing (a pixel), the tail swaying a pixel, the fire flickering        (loop)
  Trot 4-9       a six-frame trot: diagonal pairs swing (sheared), the swinging paw lifted, a pixel's bob (loop, by distance)
  Float 10-13    the spirit float: paws tucked under, the tail streaming, the fire licking higher    (loop)
  Settle 14-15   sinking down over its legs
  Sleep 16-17    lying, the forepaws out, eyes shut, the fire low, breathing                         (loop)
  Wake 18-20     the head up and eyes open, a stretch (forepaws out, chest low), standing
Outputs (Content/Coghaven/Pets/): JadeFoxPet.png + JadeFoxPet_Glow.png (21 frames of CELL_W x CELL_H (66 x 46), 1 px apart;
the glow sheet: the fire, the eye, the gems, full-bright in game: "a bit of light"), JadeToken.png (the item: a jade coin with
a fox's head, a gilt rim), JadeFoxBuff.png (the buff: the fox's face from HEAD).
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
# the maps' colours: emerald A (darkest) .. G, sage a .. f, gilt 0 .. 9
COLOUR = {}
for _i, _c in enumerate(E):
    COLOUR["ABCDEFG"[_i]] = _c
for _i, _c in enumerate(S):
    COLOUR["abcdef"[_i]] = _c
for _i, _c in enumerate(G):
    COLOUR["0123456789"[_i]] = _c

GROUND = 42                                         # sprite row of the feet's bottom pixels
CELL_W, CELL_H = 66, 46                             # 1x
SX, SY = 2, CELL_H - 1 - GROUND                     # sprite px -> cell px
OX = 42                                             # cell column under the middle of its body (the pet's OriginX / 2)

# ================================================================================================
# The parts (sprite px: x right, y down, the feet's bottom row GROUND). Each is (x0, y0, rows); "." is clear.
# ================================================================================================
HEAD = (36, 0, [
    "...........A..............",
    "..........A8A.............",
    ".........AE7A.............",
    ".........AEB7A.........AA.",
    "........AECB7A........AE7A",
    "........AEbC7A.......AEC6A",
    "........AEbbB7A.....AEDC6A",
    ".......AEBbce7A..A.AEDC7CA",
    ".......AEBcefd7AAfAADCC7BA",
    ".......ADCdfef7AAeAECB6ecA",
    "......ADCBefdef7Ade75CefdA",
    ".....AEDBcefed67ce7GE5efeA",
    "....AEFEBdfed477767FE41efA",
    "....ADECceffe3dde16ED31eeA",
    "....Acedcefffeffed6DC2eDA.",
    ".AEAdeec167777AAAAe52eDEA.",
    "AEDededce641f6ACEDA1feDEA.",
    "Aefeededce624f6GFEAfffCDA.",
    "Adefeefedef3266AAAAfffeBA.",
    "deffefefeffedeffeffffdAA..",
    "cdefedefedefedeefedcbbA...",
    "bcdefedefedeffedeedcbA....",
])
# the eye shut (asleep): its lid a dark line, fur over it (sprite px of HEAD's rows 15-18, columns 50-54)
EYE_SHUT = (50, 15, ["effee", "ffeee", "6AAAe", "6effe"])
EYE_PX = ((51, 16), (52, 16), (53, 16), (51, 17), (52, 17), (53, 17))      # the eye's glowing pixels

BODY = (26, 19, [
    ".............afffedcffeeefffffffa",
    ".............aafeddddfeebeeeeeea",
    ".............aGfeeeeeeccbbbAaaa",
    ".....aaAAAaaABd744Ceeeeddbba",
    ".....aeeAAEEEedc65CD5eeeddccAA",
    "....aeDeeddDDefee7557eeeddddcA",
    "..Eeeedddddddffeee657CAA762BA",
    "..Beeedddddbbffffeee77757ED44",
    "..edeeedddbDbbBfeefffe637EE3a",
    "..eddeedddbBbbbeeefffeed3e3cda",
    "..eddeeedddBeebeeffeffedd4cdda",
    "Beeddeeeeddeeebbeeeefffdd7cda",
    "BeeddeeeedbbeeebbeeffddBBBBBA",
    "feddddfdddAaeead7Cbeddd",
    "effddffddda.aA.ed7bdddB",
    "bfaddaddaB.....ada7baBB",
    "Aa.aa.aa.a.....aa.Ba.aa",
])
# the hip's gilt spiral (the user's design): an arc hooked at the right over the haunch and down to the thigh, a curl in it
HIP_SWIRL = (
    [(36.8, 25.0), (36.6, 23.8), (35.2, 23.1), (33.5, 23.2), (31.9, 24.2), (30.9, 25.8), (30.3, 27.6), (29.6, 29.3), (28.4, 30.4)],
    [(31.0, 27.3), (31.9, 26.4), (33.0, 26.5), (33.5, 27.5), (32.9, 28.3), (32.0, 28.4)],
)
PENDANT = (49, 23, [
    ".1661..",
    "176651.",
    "7FED5..",
    "7GED4..",
    "6EDC3..",
    "5DCB2..",
    "15431..",
    ".171...",
    ".151...",
    ".AEDA..",
    ".AFDA..",
    "AEFCBA.",
    "AEECBA.",
    "ADECBA.",
    ".AAAA..",
])
# the legs: the long fur hangs over their tops (the body is drawn over them)
NF = (42, 34, [".AefecA.",
               ".AdfecA.",
               "1677641.",
               "17FE531.",
               "16EC421.",
               ".14531..",
               ".AeffdA.",
               ".AefcfdA",
               ".AAAAAAA"])
FF = (47, 32, [".ACDCBA",
               ".ACDCBA",
               ".ABDCBA",
               ".ABCCBA",
               ".ABCCBA",
               ".156641",
               ".16ED31",
               "..1431.",
               ".AdedcA",
               ".AdeedcA",
               ".AAAAAAA"])
NH = (25, 34, [".AdecA.",
               ".AdecA.",
               ".A7d6A.",
               ".Ae75A.",
               ".Ad4cA.",
               ".AeecA.",
               "AefedA.",
               "AefcedA",
               "AAAAAAA"])
FH = (32, 33, ["ACDDCBA.",
               "AEDDCBA.",
               "AEDCCBA.",
               "AEDCCBA.",
               ".ACDCBA.",
               ".134321.",
               ".ACDCBA.",
               ".AdedcA.",
               ".AdeedcA",
               ".AAAAAAA"])
PAW_ROWS = 3                                        # a leg's last rows are its paw (shown when it lies down)

# ================================================================================================
# The tail and its spirit fire: strokes along the image's curves (sprite px)
# ================================================================================================
FLAME_MASS = [(2.6, 16.6), (3.0, 12.0), (6.0, 9.0), (10.0, 7.0), (14.6, 6.0), (18.6, 8.0), (19.2, 12.6), (17.6, 17.0), (13.0, 19.0),
              (7.0, 19.4)]
FLAME_TONGUES = (                                   # (points root -> tip, radius at the root, at the tip), back to front
    ([(7.0, 19.0), (5.0, 20.2), (3.6, 22.2), (3.0, 25.0), (3.4, 27.8), (4.8, 29.8), (6.6, 31.0)], 1.5, 0.6),        # down the left
    ([(8.0, 13.6), (6.0, 11.6), (3.6, 10.6), (1.6, 11.0), (1.0, 12.6), (2.0, 14.0)], 1.5, 0.6),                      # out left, curling
    ([(5.6, 17.4), (6.2, 14.2), (8.2, 12.0), (11.0, 11.0), (14.0, 11.2), (16.6, 12.6), (17.6, 14.6), (16.6, 16.4)], 2.1, 0.8),
    ([(9.0, 13.0), (9.4, 9.6), (11.0, 7.0), (13.0, 5.2), (15.6, 4.6), (18.0, 5.6), (19.0, 7.4), (18.4, 9.0), (16.8, 9.4)], 1.6, 0.55),
)
TAIL_BALL = (11.8, 25.6, 6.9, 7.2)                  # the rolled tail: centre, radii
TAIL_STRANDS = (                                    # green strands fanning from its heart back under the rump (body, core)
    ([(13.0, 23.6), (16.5, 22.8), (20.0, 23.0), (23.0, 24.2), (25.8, 25.6)], 1.2, 0.5, "D", "E"),
    ([(13.4, 25.8), (17.0, 25.6), (20.6, 26.6), (24.0, 28.2), (27.4, 29.0)], 1.4, 0.6, "D", "E"),
    ([(13.0, 28.0), (16.4, 28.8), (19.8, 30.4), (23.0, 31.8), (27.0, 32.4)], 1.4, 0.6, "C", "D"),
    ([(11.6, 30.2), (14.6, 31.8), (18.2, 33.2), (22.0, 34.0), (26.0, 34.4)], 1.2, 0.5, "C", "D"),
)
TAIL_UNDERSIDE = ([(8.0, 31.0), (12.0, 33.6), (17.0, 35.0), (22.0, 35.6), (27.4, 35.4)], 1.6, 1.4)
TAIL_GOLD = (
    [(13.8, 20.8), (15.6, 20.4), (17.2, 21.2), (17.9, 22.6), (17.3, 23.6)],
    [(13.2, 22.8), (11.6, 22.6), (10.2, 23.6), (9.7, 25.2), (10.2, 27.0), (11.8, 28.2), (13.6, 28.6)],
)
FLAME_TOP = 19.0                                    # the fire moves more the higher it is (none below this row)


def _cover(pts, r0, r1):
    """{(x, y): (s, nd, side)} for the pixels within a stroke: s 0..1 along it, nd the distance over the radius there, side
    > 0 when the pixel is on the stroke's lower-right (shadow) side."""
    segs, tot = [], 0.0
    for a, b in zip(pts, pts[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, tot, ln))
        tot += ln
    tot = tot or 1.0
    rmax = max(r0, r1) + 1.0
    x0 = int(math.floor(min(p[0] for p in pts) - rmax))
    x1 = int(math.ceil(max(p[0] for p in pts) + rmax))
    y0 = int(math.floor(min(p[1] for p in pts) - rmax))
    y1 = int(math.ceil(max(p[1] for p in pts) + rmax))
    out = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cx, cy = x + 0.5, y + 0.5
            best = None
            for (a, b, start, ln) in segs:
                if ln <= 1e-6:
                    continue
                t = max(0.0, min(1.0, ((cx - a[0]) * (b[0] - a[0]) + (cy - a[1]) * (b[1] - a[1])) / (ln * ln)))
                px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                d = math.hypot(cx - px, cy - py)
                s = (start + t * ln) / tot
                r = r0 + (r1 - r0) * s
                if d <= r and (best is None or d / r < best[1]):
                    nx, ny = (b[1] - a[1]) / ln, -(b[0] - a[0]) / ln        # the segment's normal
                    side = (cx - px) * 0.7 + (cy - py) * 0.7
                    best = (s, d / r, side)
            if best is not None:
                out[(x, y)] = best
    return out


def _poly_fill(poly):
    out = set()
    x0, x1 = int(math.floor(min(p[0] for p in poly))), int(math.ceil(max(p[0] for p in poly)))
    y0, y1 = int(math.floor(min(p[1] for p in poly))), int(math.ceil(max(p[1] for p in poly)))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cx, cy, inside = x + 0.5, y + 0.5, False
            for i in range(len(poly)):
                (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
                if (ay > cy) != (by > cy) and cx < (bx - ax) * (cy - ay) / (by - ay) + ax:
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def _gold(pix, pts, r=0.72):
    """A gilt line: lit core, a darker shadow side and a dark brown underline on its lower right."""
    body = _cover(pts, r, r)
    under = _cover(pts, r + 0.7, r + 0.7)
    for (x, y), (s, nd, side) in under.items():
        if (x, y) not in body and side > 0:
            pix[(x, y)] = "2"
    for (x, y), (s, nd, side) in body.items():
        pix[(x, y)] = "7" if nd < 0.45 and side <= 0 else "6" if side <= 0.15 else "4"


def _flicker(pts, phase, amp):
    """The fire's points moved by a travelling wave: none at FLAME_TOP and below, the most at the top."""
    out = []
    for (x, y) in pts:
        w = max(0.0, min(1.0, (FLAME_TOP - y) / 12.0))
        out.append((x + amp * w * math.sin(phase + y * 0.55), y + amp * 0.4 * w * math.cos(phase + y * 0.55)))
    return out


def tail_and_flame(phase=0.0, amp=1.0, low=0.0):
    """{(x, y): char} the tail and its fire; phase (radians) and amp move the fire, low (0..1) sinks the tongues (asleep)."""
    pix = {}

    def sink(pts):
        return [(x, y + low * max(0.0, FLAME_TOP - y) * 0.45) for (x, y) in pts]

    for (x, y) in _poly_fill(sink(_flicker(FLAME_MASS, phase, amp))):
        pix[(x, y)] = "C" if y > 16 else "D"
    for k, (pts, r0, r1) in enumerate(FLAME_TONGUES):      # pale lime tongues, a soft green rim parting each from the last
        pts = sink(_flicker(pts, phase + k * 1.3, amp))
        for q in _cover(pts, r0 + 0.8, r1 + 0.8):
            pix[q] = "D"
        for q, (s, nd, side) in _cover(pts, r0, r1).items():
            pix[q] = "G" if nd < 0.4 and side <= 0.1 else "E" if side > 0.3 and nd > 0.65 else "F"
    cx, cy, rx, ry = TAIL_BALL                      # the rolled tail: pale fur lit top-left, a darker ring, a green heart
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = math.hypot(dx, dy)
            if d > 1.0:
                continue
            if d < 0.4:
                pix[(x, y)] = "E" if dx + dy < -0.1 else "D"
                continue
            v = 1.0 - d * 0.45 - (dx + dy) * 0.3
            if 0.56 < d < 0.66:
                v -= 0.2
            pix[(x, y)] = "f" if v > 0.8 else "e" if v > 0.58 else "d" if v > 0.4 else "c" if v > 0.22 else "b"
    for q, (s, nd, side) in _cover(*TAIL_UNDERSIDE).items():
        pix[q] = "e" if nd < 0.4 and side <= 0 else "d" if side <= 0.3 else "c"
    for (pts, r0, r1, body, core) in TAIL_STRANDS:
        for q in _cover(pts, r0 + 0.7, r1 + 0.7):
            pix[q] = "B"
        for q, (s, nd, side) in _cover(pts, r0, r1).items():
            pix[q] = core if nd < 0.45 and side <= 0.2 else body
    for pts in TAIL_GOLD:
        _gold(pix, pts)
    edge = []
    for (x, y), ch in pix.items():
        if any((x + dx, y + dy) not in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            edge.append(((x, y), "a" if ch in "abcdef" else "1" if ch in "0123456789" else "A" if y >= FLAME_TOP else "B"))
    for q, ch in edge:
        pix[q] = ch
    return pix


# ================================================================================================
# Poses
# ================================================================================================
class Pose:
    def __init__(self, body=0, head=(0, 0), tail=(0, 0), legs=None, lying=False, eyes=True, phase=0.0, amp=1.0, low=0.0,
                 paws=0):
        self.body = body                            # rows the body (and head, tail, pendant) sits lower
        self.head = head                            # the head's extra offset
        self.tail = tail                            # the tail's extra offset
        self.legs = legs or {}                      # leg -> (paw shift x, lift): the paw sheared that far, the leg raised
        self.lying = lying                          # legs folded under: only the paws show, out in front
        self.eyes = eyes
        self.phase, self.amp, self.low = phase, amp, low
        self.paws = paws                            # lying: how far the forepaws reach out in front


def _part_pixels(part):
    x0, y0, rows = part
    out = {}
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".":
                out[(x0 + i, y0 + j)] = ch
    return out


def _leg(part, shift, lift):
    """A leg with its paw sheared `shift` px (the top fixed: each row moves in proportion) and raised `lift` rows."""
    x0, y0, rows = part
    n = len(rows)
    out = {}
    for j, r in enumerate(rows):
        dx = int(round(shift * j / max(1, n - 1)))
        for i, ch in enumerate(r):
            if ch != ".":
                out[(x0 + i + dx, y0 + j - lift)] = ch
    return out


def _paw(part, dx):
    x0, y0, rows = part
    out = {}
    for j, r in enumerate(rows[-PAW_ROWS:]):
        for i, ch in enumerate(r):
            if ch != ".":
                out[(x0 + i + dx, GROUND - PAW_ROWS + 1 + j)] = ch
    return out


def _body_pixels():
    pix = _part_pixels(BODY)
    for pts in HIP_SWIRL:
        _gold(pix, pts, 0.68)
    pix.update(_part_pixels(PENDANT))
    return pix


BODY_PX = _body_pixels()
HEAD_PX = _part_pixels(HEAD)
SHUT_PX = _part_pixels(EYE_SHUT)
LEGS = {"FH": FH, "FF": FF, "NH": NH, "NF": NF}


def fox(p):
    """(pixels, glow) of a pose: {(x, y): char} in sprite px, layered back to front."""
    layers = []
    if p.lying:
        layers.append(("legs", _paw(FF, p.paws)))
        layers.append(("legs", _paw(NF, p.paws + 1)))
    else:
        for name in ("FH", "FF", "NH", "NF"):
            shift, lift = p.legs.get(name, (0, 0))
            layers.append(("legs", _leg(LEGS[name], shift, lift)))
    tail = tail_and_flame(p.phase, p.amp, p.low)
    layers.append(("tail", {(x + p.tail[0], y + p.body + p.tail[1]): c for (x, y), c in tail.items()}))
    layers.append(("body", {(x, y + p.body): c for (x, y), c in BODY_PX.items()}))
    head = dict(HEAD_PX)
    if not p.eyes:
        head.update(SHUT_PX)
    hx, hy = p.head[0], p.head[1] + p.body
    layers.append(("head", {(x + hx, y + hy): c for (x, y), c in head.items()}))
    pix, glow = {}, {}
    for kind, lp in layers:
        for q, c in lp.items():
            if kind != "legs" and q[1] > GROUND:
                continue
            pix[q] = c
            lit = c in "FG" or (kind == "tail" and c == "E")
            if lit:
                glow[q] = c
            else:
                glow.pop(q, None)
    if p.eyes:
        for (x, y) in EYE_PX:
            q = (x + hx, y + hy)
            if q in pix and pix[q] in "CDEFG":
                glow[q] = pix[q]
    return pix, glow


TAU = 2 * math.pi


def trot(k):
    """Six frames: diagonal pairs (near fore with far hind, far fore with near hind) swing a sheared stride, the swinging paw
    lifted a row; a pixel's bob at mid-stride."""
    ph = k / 6.0 * TAU

    def leg(off):
        swing = math.sin(ph + off)
        return (int(round(2.4 * swing)), 1 if math.cos(ph + off) > 0.45 else 0)
    legs = {"NF": leg(0.0), "FH": leg(0.0), "FF": leg(math.pi), "NH": leg(math.pi)}
    return Pose(body=-1 if k % 3 == 1 else 0, legs=legs, head=(0, 1 if k % 3 == 1 else 0), tail=(0, -1 if k % 3 == 2 else 0),
                phase=k / 6.0 * TAU)


TUCK = {"NF": (-3, 3), "FF": (-3, 3), "NH": (3, 3), "FH": (3, 3)}
POSES = (
    [Pose(body=b, tail=(tx, 0), phase=k / 4.0 * TAU) for k, (b, tx) in enumerate(((0, 0), (0, -1), (1, -1), (1, 0)))]       # idle
    + [trot(k) for k in range(6)]                                                                                           # trot
    + [Pose(body=b, legs=TUCK, tail=(-1, -1), phase=k / 4.0 * TAU, amp=1.5) for k, b in enumerate((0, -1, -1, 0))]          # float
    + [Pose(body=3, head=(0, 1), tail=(0, 0), phase=0.6, amp=0.8, low=0.2),                                                 # settle
       Pose(body=6, head=(0, 1), tail=(0, -2), phase=1.4, amp=0.6, low=0.4)]
    + [Pose(body=7, head=(1, 1), tail=(0, -3), lying=True, eyes=False, phase=0.0, amp=0.35, low=0.6, paws=3),              # sleep
       Pose(body=6, head=(1, 1), tail=(0, -3), lying=True, eyes=False, phase=math.pi, amp=0.35, low=0.6, paws=3)]
    + [Pose(body=7, head=(0, -1), tail=(0, -3), lying=True, phase=0.8, amp=0.6, low=0.4, paws=3),                          # wake
       Pose(body=3, head=(1, 2), tail=(0, -2), legs={"NF": (4, 0), "FF": (4, 0)}, phase=2.0, amp=0.9),
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
    """The buff: a portrait from HEAD (the ears' bases with their gilt rims, the jade diamond, the gilt mask, the glowing eye,
    the muzzle), full-bleed like vanilla's buff icons."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x, y), c in HEAD_PX.items():
        bx, by = x - 44, y - 5
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
    if args.preview:
        base, gl = out[OUT + "JadeFoxPet.png"], out[OUT + "JadeFoxPet_Glow.png"]
        sc = 4
        cols = 4
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
