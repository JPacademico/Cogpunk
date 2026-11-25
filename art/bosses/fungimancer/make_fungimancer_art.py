"""Source for the Fungimancer (D4), v4 2026-11-23: the 2x2 version, in three parallax planes. Run from the repo root:

    python -P art/bosses/fungimancer/make_fungimancer_art.py [--preview FILE] [--planes FILE]

User, 2026-11-23 (after v3, the reference read at its own 8 px grid): "before this (using this base model) redesign/make a
version of the fungimancer to the expected 2x2 pixel doubling that terraria mods uses. it has to keep core details like
collors and the mushroom cap and head/eyes/belly/frog hand colors, just adapt it ... the current perspective and arm position
is fine" and "work on paralax sectioning animation for him using the base sprite as base, animation frames and transitions
with atenttion and you can remove the blue silluete effect he has".

1. The model at half the resolution (`half_model`): v3's base (reference/fungimancer_base_2026-11-23.png, 125 x 103, the user's
   reference on its grid) reduced 2x2 -> 1 by part, not by colour: each base pixel is given its material (skin, belly, red
   hands and frills, pink arm, the mushroom cap, the outline, the blue rim light); the blue rim (the "blue silhouette") is
   dropped, or takes its neighbours' material where it lies inside the body; each new pixel takes its block's commonest
   material and that material's ramp step nearest its block's lightness, then a 3x3 vote per material removes lone specks
   (the ramp bands stay); a 1 px outline goes round the outside; the base's dark lines between parts
   stay where two or more of a block's pixels were dark; outlines and those lines take the darkest tone of their own part
   (dark green, dark red, dark teal: vanilla's coloured outlines; the face keeps the base's near-black). Then the stamps: HEAD (both eyes, the forehead, the
   open grin with its teeth and tongue: a straight reduction loses them) and SEAT (the orb's empty ring in the cap closed).
   Colours: only the base's own (its 48 are in art/palettes/cogpunk.gpl as Fungimancer 0-47).
2. Its planes (`split_planes`): FAR, the raised (casting) arm and hand, behind the body, carried 4 px further under the shoulder
   so a parallax shift never opens a gap; NEAR, the pink arm on its chest with its red hand, and the red hand resting on its
   belly, in front; MIDDLE, the rest (head, belly, frills, back leg, the far foot, the mushroom cap), filled in under the
   near parts (each hole takes the nearest middle colour in its row) so they can slide over it. In game the far and near
   planes shift with the camera (DepthLayers, up to Fungimancer.MaxParallax), the far one a little darker.
3. Every frame is the model with its parts moved by whole pixels (no resampling: the pixels never flicker), eased. The
   2026-11-25 fight (user: his eight mechanics; "the best one is the one i send on this prompt image, just fix the arm colors to
   match the body like the other arm, only the hand is suposed to be red"): the raised near arm is the far arm's own pixels
   mirrored (RAISE_AXIS, RAISE_DY) in their own colours (green skin, red hand), CHEST_PATCH fills the chest it uncovers, and
   SWING adds in-betweens so no pose jumps:
     Idle 0-5       a breath (the upper body rises a pixel over the belly), the raised hand waving a pixel, the frills' tips
                    lifting; 5 is a blink (the C# plays 0 1 2 3 2 1 and the blink)
     Cast 6-11      the orbit's summoning gesture: wind-up, raise, gather, fling, follow-through, recover
     Croak 12-16    the throat sac swells, swells, full, croaks (the mouth wide), sinks (the defeat's croak)
     Fizzle 17-18   dazed: eyes squeezed shut, the hand drooping (the stun and the defeat's start)
     Intro 19-20    eyes shut, then open
     Raise 21-22    the near hand raised quickly to cast (the delayed spells)
     Shake 23-26    the raised hand shaken (the spell gathering at the fingers)
     Release 27     the spell let go; Lower 28 the hand coming down
     ArmsUp 29-31   both arms rising for the channel; Hold 32-33 the strain (a pixel's tremble); ArmsDown 34-35 lowering
   Overlays drawn over any pose (their two rows follow Lift, the breath): the BURP (Fungimancer_Burp.png: the throat and mouth
   in 5 poses), the hypnotic EYES (Fungimancer_Eyes.png: a spinning rainbow pinwheel, 8 frames, during the channel) and the PUFF
   of magic smoke of the defeat (Fungimancer_Puff.png, 8 frames over the body as it turns into a vanilla Frog).
Outputs (Content/Bosses/Fungimancer/): Fungimancer.png (the middle plane), _Far.png, _Near.png, _Glow.png (grid sheets,
COLUMNS wide, 1 px right of and under each cell at 1x), _Burp.png, _Eyes.png, _Puff.png, FungimancerRigData.cs,
Fungimancer_Head_Boss.png, the fight's sprites (fungimancer_fight.py: spores, missile, polymorph bolt, the three mushrooms,
the buff icons) and the small things (fungimancer_things.py). v1 (procedural), v2 (sculpted), v3 (the reference at full size)
and the generator before the 2026-11-25 fight (make_fungimancer_art_2026-11-25a.py) are in previous/.
"""
import argparse
import math
import os
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, HERE)
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
import fungimancer_things as things  # noqa: E402
import fungimancer_fight as fight  # noqa: E402

OUT = "Content/Bosses/Fungimancer/"
BASE = os.path.join(HERE, "reference", "fungimancer_base_2026-11-23.png")
COLUMNS = 4
AE, SM = RAMP["aether"], RAMP["steam"]

# ==========================================================================================================================
# 1. The model at half resolution
# ==========================================================================================================================
# The base's colours by material (all 48 are the base's own)
OUTLINE = {(8, 4, 6), (7, 11, 28)}
RIM = {(67, 221, 248), (74, 136, 244), (92, 172, 237), (36, 80, 141)}          # the blue rim light: dropped
SEAT_C = {(5, 32, 51), (10, 47, 71), (6, 67, 88), (8, 100, 114), (11, 135, 137), (12, 176, 161)}
SKIN_C = {(22, 36, 17), (25, 56, 10), (38, 79, 7), (52, 105, 7), (75, 138, 13), (112, 188, 34), (109, 121, 11), (39, 89, 58),
          (106, 155, 126)}
BELLY_C = {(56, 74, 54), (81, 99, 72), (106, 124, 89), (129, 146, 104), (130, 136, 89), (157, 174, 129), (167, 174, 123),
           (189, 202, 157), (191, 195, 140), (216, 218, 167), (223, 229, 187), (236, 240, 210), (146, 117, 86), (191, 168, 124),
           (104, 87, 110)}
RED_C = {(54, 5, 11), (84, 7, 16), (117, 10, 17), (151, 14, 21), (188, 24, 23), (229, 52, 26), (243, 129, 43), (201, 177, 44),
         (229, 191, 190)}
PINK_C = {(152, 21, 58), (216, 30, 62), (230, 38, 97)}
RAMPS = {                                                                       # dark to light, from the base
    "skin": ((25, 56, 10), (38, 79, 7), (52, 105, 7), (75, 138, 13), (112, 188, 34)),
    "belly": ((56, 74, 54), (106, 124, 89), (157, 174, 129), (191, 195, 140), (223, 229, 187), (236, 240, 210)),
    "red": ((84, 7, 16), (117, 10, 17), (151, 14, 21), (188, 24, 23), (229, 52, 26), (243, 129, 43)),
    "pink": ((117, 10, 17), (152, 21, 58), (216, 30, 62), (230, 38, 97)),
    "seat": ((10, 47, 71), (6, 67, 88), (8, 100, 114), (11, 135, 137), (12, 176, 161)),
}
DARK, SEAT_DARK = (8, 4, 6), (5, 32, 51)
# the silhouette's outline: the darkest tone of the part it closes (vanilla's coloured outlines, never black); the base's own
RIM_OF = {"skin": (22, 36, 17), "belly": (22, 36, 17), "red": (54, 5, 11), "pink": (54, 5, 11), "seat": SEAT_DARK}
OUTLINES = {DARK, SEAT_DARK, (22, 36, 17), (54, 5, 11)}

# the stamps' letters
C = {"K": DARK, "g": (25, 56, 10), "h": (38, 79, 7), "i": (52, 105, 7), "j": (75, 138, 13), "k": (112, 188, 34),
     "1": (56, 74, 54), "2": (106, 124, 89), "3": (157, 174, 129), "4": (191, 195, 140), "5": (223, 229, 187), "6": (236, 240, 210),
     "r": (84, 7, 16), "s": (117, 10, 17), "t": (151, 14, 21), "u": (188, 24, 23), "v": (229, 52, 26), "w": (243, 129, 43),
     "P": (152, 21, 58), "Q": (216, 30, 62), "R": (230, 38, 97), "n": SEAT_DARK, "A": (10, 47, 71), "B": (6, 67, 88),
     "C": (8, 100, 114), "D": (11, 135, 137), "E": (12, 176, 161), "y": (201, 177, 44), "W": (229, 191, 190), "m": (54, 5, 11)}

# The face, drawn by hand at this size (x20..37, y5..16; ' ' keeps the reduction, '.' clears): the far eye (x21-25) and
# the near eye (x32-37), orange irises lit from the top-left (a pale glint, a yellow lit side), round dark pupils; the
# forehead between them under the frill that arches over the near eye; the snout; the open grin: the upper lip's line, the
# dark maw with two teeth hanging in it, the pink tongue, the lower lip, the pale throat.
HEAD = (
    "         KvusKK...",
    "         KvvKKKKK.",
    "  KKK...KuvKKw6ywK",
    " Ky6wKKKjkjiKywKvK",
    " KwKvKjkkjjiKwvKuK",
    "KKvutKjjjiiiKvuutK",
    "KjKKKjjiiiiiiKKKKh",
    "Kijjjiiiihhhhhhggg",
    ".KKKKKKKKKKKKhgggg",
    ".KKmWmmWmmKKKKgghh",
    ".K2KrQRQrK4443kkjj",
    ".K23KKKKK55545hiij",
)
HEAD_AT = (20, 5)
SEAT = (                                                    # x49..60, y45..50: the cap closed where the orb was cut out
    "AAAAABBnAAn.",
    "BBCCCBBBBAAn",
    "BCDDCCBBBAAn",
    "BCDDCCBBBAAn",
    "BCCCCBBBAnn.",
    "BBCBBAAn....",
)
SEAT_AT = (49, 45)

# Mouth states (x20..37, y13..17), over HEAD's grin: 1 is HEAD's own; 2 the jaw dropped a pixel; 3 two (the tongue is out)
MOUTH_AT = (20, 13)
MOUTH = {
    2: (".KKKKKKKKKKKKhgggg",
        ".KKmWmmWmmmKKKgghh",
        ".K2KmmmmmmmK43kkjj",
        ".K23KrQRQrK545hiij",
        "  .2KKKKKK5554    "),
    3: (".KKKKKKKKKKKKhgggg",
        ".KKmWmmWmmmmKKgghh",
        ".K2KmmmmmmmmK3kkjj",
        ".K23KmmmmmmK545hii",
        "  .23KrrrrK5554   ",
        "   .3KKKKK55      "),
}
# Eyes shut: each eye's inside (far x22-24 y8-10, near x33-36 y7-10) becomes its lid: lit skin, the shut line, shade
BLINK = {(22, 8): "jjj", (22, 9): "KKK", (22, 10): "iii", (33, 7): "kjjj", (33, 8): "jjjj", (33, 9): "KKKK", (33, 10): "iiii"}
TIGHT = {(22, 8): "jjj", (22, 9): "KKK", (22, 10): "KiK", (33, 7): "jjjj", (33, 8): "KjjK", (33, 9): "KKKK", (33, 10): "iKKi"}
EYES = ((22, 8, 25, 11), (33, 7, 37, 11))                    # the irises' boxes (their colours glow)
EYE_GLOW = {C["w"], C["v"], C["u"], C["t"], C["y"], C["6"]}


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def material(c, y):
    if c in OUTLINE:
        return "out"
    if c in RIM:
        return "rim"
    if c in SEAT_C:
        return "seat" if y >= 84 else "rim"
    if c in SKIN_C:
        return "skin"
    if c in PINK_C:
        return "pink"
    if c in RED_C:
        return "red"
    return "belly"


def stamp(px, at, rows):
    x0, y0 = at
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == ".":
                px.pop((x0 + i, y0 + j), None)
            elif ch != " ":
                px[(x0 + i, y0 + j)] = C[ch]


def half_model():
    """The base reduced 2x2 -> 1 by material, outlined, then stamped (see the docstring). Canvas: (W0, H0), 1 px margin."""
    im = Image.open(BASE).convert("RGBA")
    p = im.load()
    bw, bh = im.size
    lab = {(x, y): (material(p[x, y][:3], y), p[x, y][:3]) for y in range(bh) for x in range(bw) if p[x, y][3]}
    for _ in range(3):                                   # rim light inside the body takes its neighbours' material
        for (x, y), (m, c) in list(lab.items()):
            if m != "rim":
                continue
            near = [lab.get((x + dx, y + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
            mats = [n for n in near if n and n[0] not in ("rim", "out")]
            if len(mats) >= 4:
                m2 = Counter(n[0] for n in mats).most_common(1)[0][0]
                lab[(x, y)] = (m2, Counter(n[1] for n in mats if n[0] == m2).most_common(1)[0][0])
    w0, h0 = (bw + 1) // 2 + 2, (bh + 1) // 2 + 2
    mat, level, dark = {}, {}, {}
    for Y in range(h0):
        for X in range(w0):
            subs = [lab.get((2 * (X - 1) + i, 2 * (Y - 1) + j)) for j in (0, 1) for i in (0, 1)]
            subs = [s for s in subs if s and s[0] != "rim"]
            mats = [s for s in subs if s[0] != "out"]
            nd = len(subs) - len(mats)
            dark[(X, Y)] = nd
            if not mats:
                continue
            top = Counter(s[0] for s in mats).most_common(1)[0][0]
            thin = top in ("red", "pink")                # frills and fingers: one pixel of red keeps them
            if len(mats) < (1 if thin else 2) or (len(mats) == 1 and nd >= 2 and not thin):
                continue
            mat[(X, Y)] = top
            cs = [s[1] for s in mats if s[0] == top]
            level[(X, Y)] = sum(lum(c) for c in cs) / len(cs)
    idx = {q: min(range(len(RAMPS[m])), key=lambda i: abs(lum(RAMPS[m][i]) - level[q])) for q, m in mat.items()}
    for _ in range(2):                                   # a 3x3 vote per material: lone specks go, bands stay
        new = {}
        for (x, y), m in mat.items():
            near = [idx[(x + dx, y + dy)] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if mat.get((x + dx, y + dy)) == m]
            best, n = Counter(near).most_common(1)[0]
            new[(x, y)] = best if n >= 4 and idx[(x, y)] != best and near.count(idx[(x, y)]) <= 1 else idx[(x, y)]
        idx = new
    px = {q: RAMPS[m][idx[q]] for q, m in mat.items()}
    for (x, y), m in mat.items():                        # the base's dark lines between parts, in the part's darkest
        if dark.get((x, y), 0) >= 2 and any(mat.get(q) not in (None, m) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
            px[(x, y)] = RIM_OF[m]
    for (x, y), m in list(mat.items()):                  # the outline, outside the silhouette: each part's own darkest
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in mat and q not in px:
                px[q] = RIM_OF[m]
    stamp(px, HEAD_AT, HEAD)
    stamp(px, SEAT_AT, SEAT)
    for (x, y), c in list(px.items()):                   # the stamps' near-black on the silhouette: their part's darkest
        if c == DARK and any(q not in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
            near = Counter(material(px[q], 99 if px[q] in SEAT_C else 0) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                           if q in px and px[q] not in OUTLINES)
            m = near.most_common(1)[0][0] if near else "skin"
            px[(x, y)] = RIM_OF.get(m, RIM_OF["skin"])
    return px, (w0, h0)


MODEL, (W0, H0) = half_model()

# ==========================================================================================================================
# 2. The planes
# ==========================================================================================================================
REDS = set(RAMPS["red"]) | {C["y"], C["W"], C["m"]}
PINKS = set(RAMPS["pink"])
SKINS = set(RAMPS["skin"])
BREATH_SPLIT = 26             # the upper body (above this row) rises on a breath; the row under it is repeated
HAND_TOP = 15                 # the raised arm: its hand above this row moves whole, its forearm bends below it
CHEST_LOW = 32                # the chest arm's hand ends on this row; the hand resting on the belly starts under it
SHOULDER = 28                 # ...down to here, where it goes behind the body


def far_arm(x, y):
    return (y <= SHOULDER and x <= (21 if y >= 20 else 19)) or (x <= 21 and y <= 4) or (x == 20 and 5 <= y <= 9)


def near_region(x, y, c):
    """The pink arm on its chest (with its red hand) and the red hand on its belly: their red/pink pixels."""
    if 38 <= x <= 51 and 16 <= y <= CHEST_LOW and (c in PINKS or (y >= 27 and c in REDS)):
        return "chest"
    if 33 <= x <= 50 and CHEST_LOW < y <= 48 and (c in REDS or c in PINKS):
        return "hand"
    return None


def split_planes():
    far, mid, near = {}, {}, {}
    for (x, y), c in MODEL.items():
        if far_arm(x, y):
            far[(x, y)] = c
        elif near_region(x, y, c):
            near[(x, y)] = c
        else:
            mid[(x, y)] = c
    for (x, y), c in list(mid.items()):                  # the near parts' outlines (dark next to them) go with them
        if c in OUTLINES and any(q in near and near[q] not in OUTLINES for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
            near[(x, y)] = c
            del mid[(x, y)]
    # under the near parts the middle plane is filled in (each hole: the nearest middle colour in its row, not an outline)
    for _ in range(2):
        for (x, y) in sorted(near, key=lambda q: q[1]):
            if (x, y) in mid:
                continue
            best = None
            for d in range(1, 12):
                for q in ((x - d, y), (x + d, y)):
                    c = mid.get(q)
                    if c is not None and c not in OUTLINES and q not in near:
                        best = c
                        break
                if best:
                    break
            if best and any(mid.get(q) for q in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))):
                mid[(x, y)] = best
    # the far arm goes on 4 px under the shoulder (hidden by the body), so a parallax shift never opens a gap there
    for y in range(17, SHOULDER + 1):
        edge = [x for (x, yy) in far if yy == y]
        if not edge:
            continue
        xr = max(edge)
        c = far.get((xr - 1, y), far[(xr, y)])
        for k in range(1, 5):
            if (xr + k, y) in mid:
                far.setdefault((xr + k, y), c if c not in OUTLINES else far[(xr, y)])
    return far, mid, near


FAR0, MID0, NEAR0 = split_planes()

# ==========================================================================================================================
# 3. Poses
# ==========================================================================================================================
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 4, 9, 1
W, H = W0 + 2 * MARGIN_X, H0 + MARGIN_TOP + MARGIN_BOTTOM
SEAT_MID_X = 34                                          # under the seat's middle (the origin)
OX, OY = MARGIN_X + SEAT_MID_X, MARGIN_TOP + H0 - 1      # the origin: under the cap's middle, on its last row
THROAT = (28.0, 18.0)
MOUTH_PT = (26.0, 14.0)
HAND_POINT = (13, 2)                                     # the raised fingers' tips: its spells leave there
SPROUTS = ((21, 23), (36, 21), (28, 31), (44, 27), (17, 34), (49, 15), (31, 40))
SPROUT_CAP, SPROUT_LIGHT, SPROUT_STALK = C["E"], (67, 221, 248), C["W"]


class Pose:
    def __init__(self, breath=0, hand=(0, 0), magic=0, blink=None, sac=0.0, mouth=1, sprouts=0, frills=0, chest=0, near_up=0,
                 tremble=0):
        self.breath, self.hand, self.magic, self.blink, self.sac = breath, hand, magic, blink, sac
        self.mouth, self.sprouts, self.frills, self.chest = mouth, sprouts, frills, chest
        self.near_up = near_up            # the chest arm: 0 resting, 1 swinging up (a smear), 2 raised, 3 swinging down
        self.tremble = tremble            # 0/1: both raised hands a pixel up (the channel's strain; never -1/+1)


def lift_upper(plane, b, keep_lower=True):
    """A breath: the plane's pixels above BREATH_SPLIT rise b px; the split row is repeated under them."""
    if not b:
        return dict(plane)
    out = {}
    for (x, y), c in plane.items():
        if y < BREATH_SPLIT:
            out[(x, y - b)] = c
        elif keep_lower:
            out[(x, y)] = c
    for (x, y), c in plane.items():
        if y == BREATH_SPLIT:
            for k in range(1, b + 1):
                out.setdefault((x, y - k), c)
    return out


def move_hand(plane, dx, dy):
    """The raised hand: rows above HAND_TOP move (dx, dy); the forearm below bends, each row moving the share of it that
    its height up the arm gives (whole pixels), so the arm stays joined; a pixel the bend leaves open takes the one under it."""
    if not (dx or dy):
        return dict(plane)
    out = {}
    span = SHOULDER - HAND_TOP
    for (x, y), c in sorted(plane.items(), key=lambda kv: -kv[0][1]):
        if y <= HAND_TOP:
            f = 1.0
        else:
            f = max(0.0, (SHOULDER - y) / span)
        out[(x + int(round(dx * f)), y + int(round(dy * f)))] = c
    for (x, y), c in plane.items():                      # close gaps a bend opens in a column
        if HAND_TOP - 2 <= y <= SHOULDER and (x, y) not in out:
            up, down = out.get((x, y - 1)), out.get((x, y + 1))
            if up and down:
                out[(x, y)] = down
    return out


def frill_wave(plane, k):
    """The frills' tips (x >= 52, above the back's skin at row 19) rise k px, from x >= 57 one more: they wave on a breath."""
    if not k:
        return dict(plane)

    def tip(q, c):
        return q[1] <= 18 and q[0] >= 52 and c in REDS | OUTLINES
    out = {}
    for (x, y), c in plane.items():
        if tip((x, y), c):
            out[(x, y - (k + (1 if x >= 57 else 0)))] = c
    for q, c in plane.items():
        if not tip(q, c):
            out.setdefault(q, c)
    return out


def ellipse(cx, cy, rx, ry):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                yield (x, y)


def sac(plane, s, lift):
    """The throat sac: a pale bubble under the chin, lit from the top-left, its lower edge outlined."""
    if s <= 0:
        return
    rx, ry = 2.5 + 3.5 * s, 1.5 + 2.5 * s
    cx, cy = THROAT[0], THROAT[1] - lift + 0.5 + 1.5 * s
    pts = set(ellipse(cx, cy, rx, ry))
    for (x, y) in pts:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        edge = any(q not in pts for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        lit = -(u * 0.6 + v * 0.8)
        plane[(x, y)] = (DARK if edge and v > -0.35 else C["3"] if edge else C["6"] if lit > 0.5 else C["5"] if lit > 0.0
                         else C["4"] if lit > -0.45 else C["3"])


def face(plane, p, lift):
    if p.mouth in MOUTH:
        stamp_shift(plane, MOUTH_AT, MOUTH[p.mouth], lift)
    lids = TIGHT if p.blink == "tight" else BLINK if p.blink else None
    if lids:
        for (x, y), row in lids.items():
            for i, ch in enumerate(row):
                plane[(x + i, y - lift)] = C[ch]


def stamp_shift(plane, at, rows, lift):
    stamp(plane, (at[0], at[1] - lift), rows)


def magic(glow, level, hand):
    """Violet light gathering at the raised fingers: a cloud of motes round the tips (a golden-angle scatter), denser and
    wider at level 2, a white core; in the glow sheet (full-bright)."""
    cx, cy = HAND_POINT[0] + hand[0], HAND_POINT[1] + hand[1]
    n = 7 + 6 * level
    for i in range(n):
        a = i * 2.39996 + level * 0.7
        r = 1.0 + (i / n) ** 0.6 * (2.0 + 1.5 * level)
        q = (int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r)))
        glow[q] = SM[3] if r < 1.6 else AE[3] if i % 3 else AE[2]


def sprouts(plane, glow, n, lift):
    """A glowing mushroom of the biome (3 px cap, its lit middle, a pale stalk) per spot, in the glow sheet."""
    shape = ((0, -2, SPROUT_CAP, True), (-1, -1, SPROUT_CAP, True), (0, -1, SPROUT_LIGHT, True), (1, -1, SPROUT_CAP, True),
             (-2, -1, DARK, False), (2, -1, DARK, False), (-1, 0, DARK, False), (0, 0, SPROUT_STALK, False),
             (1, 0, DARK, False), (0, 1, SPROUT_STALK, False))
    for (x, y) in SPROUTS[:n]:
        y -= lift if y < BREATH_SPLIT else 0
        for (dx, dy, c, g) in shape:
            plane[(x + dx, y + dy)] = c
            if g:
                glow[(x + dx, y + dy)] = c


# --- the channel's raised near arm (2026-11-25) ------------------------------------------------------------------------
# The user: "he stops and raises bot arms". The chest arm is raised by mirroring the far (raised) arm's own pixels round the
# near shoulder: the same arm and hand drawing, so the pose is the model's own. Its colours are the far arm's (user, 2026-11-25,
# on the first try's pink arm: "fix the arm colors to match the body like the other arm, only the hand is suposed to be red
# not the whole arm"): green skin, a red hand. Its swing up and down is an in-between: the same arm, lower and further out.
NEAR_SHOULDER = (49, 18)                 # where the chest arm leaves the body, under the frills
RAISE_AXIS, RAISE_DY = 69, -5            # x' = RAISE_AXIS - x, y' = y + RAISE_DY (the far arm's root lands on the shoulder)
RAISED_HAND = (RAISE_AXIS - 13, 2 + RAISE_DY)   # the raised near hand's fingertips (the far hand's HAND_POINT mirrored)


def chest_arm(q, c):
    return near_region(q[0], q[1], c) == "chest" or (c in OUTLINES and 37 <= q[0] <= 52 and 15 <= q[1] <= CHEST_LOW)


def raised_near_arm():
    out = {}
    for (x, y), c in FAR0.items():
        if x > 21:
            continue                                     # the far arm's hidden root under the shoulder
        out[(RAISE_AXIS - x, y + RAISE_DY)] = c          # its own colours: green skin, red hand
    return out


RAISED_NEAR = raised_near_arm()


SWING = {1: (2, 8), 3: (3, 9)}            # the in-between of the swing up (1) and down (3): the raised arm, lower and out


def chest_patch():
    """The middle plane under the chest arm, for when the arm is raised: the outline and red pixels the arm used to hide
    (its own outline left in the middle plane) take the nearest skin or belly colour in their row."""
    patch = {}
    for (x, y), c in MID0.items():
        if not (37 <= x <= 53 and 14 <= y <= CHEST_LOW + 2) or not (c in OUTLINES or c in REDS or c in PINKS):
            continue
        if not any(chest_arm(q, NEAR0[q]) for q in ((x + dx, y + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-1, 0, 1)) if q in NEAR0):
            continue
        best = None
        for d in range(1, 10):
            for q in ((x - d, y), (x + d, y)):
                c2 = MID0.get(q)
                if c2 is not None and c2 not in OUTLINES and c2 not in REDS and c2 not in PINKS:
                    best = c2
                    break
            if best:
                break
        if best:
            patch[(x, y)] = best
    return patch


CHEST_PATCH = chest_patch()


def frame(p):
    """One frame -> (far, mid, near, glow), each {(x, y): rgb} in the cell (margins added)."""
    b = p.breath
    far = move_hand(lift_upper(FAR0, b), *p.hand)
    mid = frill_wave(lift_upper(MID0, b), p.frills)
    near = {}
    for (x, y), c in NEAR0.items():                      # the chest arm rides the breath; the belly hand stays
        chest = chest_arm((x, y), c)
        if chest and p.near_up:
            continue                                     # raised or swinging: drawn below instead
        near[(x, y - (b + p.chest if chest else 0))] = c
    if p.near_up == 2:
        for (x, y), c in RAISED_NEAR.items():            # raised over the frills, trembling a pixel with the far hand
            near[(x, y - b - p.tremble)] = c
    elif p.near_up in SWING:
        dx, dy = SWING[p.near_up]
        for (x, y), c in RAISED_NEAR.items():            # half way up (or down): the same arm, lower and further out
            near[(x + dx, y + dy - b)] = c
    if p.near_up:
        for (x, y), c in CHEST_PATCH.items():            # the chest the arm uncovers
            q = (x, y - b if y < BREATH_SPLIT else y)
            if q in mid:
                mid[q] = c
    sac(mid, p.sac, b)
    face(mid, p, b)
    glow = {}
    for (x0, y0, x1, y1) in EYES:
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = mid.get((x, y - b))
                if c in EYE_GLOW and not p.blink:
                    glow[(x, y - b)] = c
    if p.magic:
        magic(glow, p.magic, (p.hand[0], p.hand[1] - b))
    if p.sprouts:
        sprouts(mid, glow, p.sprouts, b)
    sh = (MARGIN_X, MARGIN_TOP)
    return tuple({(x + sh[0], y + sh[1]): c for (x, y), c in d.items()} for d in (far, mid, near, glow))


FRAMES = (
    [("Idle0", Pose()), ("Idle1", Pose(hand=(-1, 0))), ("Idle2", Pose(breath=1, hand=(-1, -1))),
     ("Idle3", Pose(breath=1, hand=(-1, -1), frills=1)), ("Idle4", Pose(hand=(-1, 0), frills=1)), ("Idle5", Pose(blink=True))]
    + [("Cast0", Pose(hand=(1, 1))), ("Cast1", Pose(hand=(0, -1), magic=1)), ("Cast2", Pose(breath=1, hand=(0, -2), magic=2, chest=0)),
       ("Cast3", Pose(breath=1, hand=(-2, 0), mouth=2)), ("Cast4", Pose(hand=(-2, 1), mouth=2)), ("Cast5", Pose(hand=(-1, 0)))]
    + [("Croak0", Pose(sac=0.3)), ("Croak1", Pose(sac=0.7, breath=1)), ("Croak2", Pose(sac=1.0, breath=1)),
       ("Croak3", Pose(sac=0.8, mouth=3)), ("Croak4", Pose(sac=0.3))]
    + [("Fizzle0", Pose(blink="tight", mouth=2, hand=(1, 1))), ("Fizzle1", Pose(blink=True, mouth=3, hand=(2, 2)))]
    + [("Intro0", Pose(blink=True)), ("Intro1", Pose())]
    # 2026-11-25, the delayed spells ("he raises quickly shakes his raised hand"): up in two frames, shaken (0/1 px, never
    # -1/+1: D4 rule 17), the spell let go with a little fling, lowered
    + [("Raise0", Pose(breath=1, hand=(0, -2), magic=1)), ("Raise1", Pose(breath=1, hand=(0, -4), magic=2, mouth=2))]
    + [("Shake0", Pose(breath=1, hand=(0, -4), magic=2)), ("Shake1", Pose(breath=1, hand=(1, -4), magic=2)),
       ("Shake2", Pose(breath=1, hand=(0, -3), magic=2)), ("Shake3", Pose(breath=1, hand=(1, -3), magic=2))]
    + [("Release0", Pose(hand=(-2, -2), mouth=2, magic=1))]
    + [("Lower0", Pose(hand=(-1, 0)))]
    # the channel ("he stops and raises bot arms"): a breath in, the chest arm swung up (a smear), raised with the far one
    # higher, held trembling, swung down
    + [("ArmsUp0", Pose(hand=(0, -1), chest=1)), ("ArmsUp1", Pose(breath=1, hand=(0, -3), near_up=1, mouth=2)),
       ("ArmsUp2", Pose(breath=1, hand=(0, -4), near_up=2, mouth=2))]
    + [("Hold0", Pose(breath=1, hand=(0, -4), near_up=2, mouth=2)), ("Hold1", Pose(breath=1, hand=(0, -5), near_up=2, mouth=2, tremble=1))]
    + [("ArmsDown0", Pose(hand=(0, -2), near_up=3)), ("ArmsDown1", Pose(hand=(-1, 0)))]
)
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Cast", "Croak", "Fizzle", "Intro", "Raise", "Shake", "Release", "Lower", "ArmsUp", "Hold", "ArmsDown")


# ==========================================================================================================================
# 4. Outputs
# ==========================================================================================================================
def grid(images):
    rows = (len(images) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((W + 1) * COLUMNS, (H + 1) * rows), (0, 0, 0, 0))
    for k, px in enumerate(images):
        bx, by = (k % COLUMNS) * (W + 1), (k // COLUMNS) * (H + 1)
        for (x, y), c in px.items():
            if 0 <= x < W and 0 <= y < H:
                out.putpixel((bx + x, by + y), tuple(c) + (255,))
    return out


def composite(fr):
    out = {}
    for d in fr[:3]:
        out.update(d)
    return out


def write_rig(path):
    xs = sorted(x for (x, y) in MODEL if 12 <= y <= 47)
    left, right = xs[len(xs) // 40] + MARGIN_X - OX, xs[-len(xs) // 40] + MARGIN_X - OX + 1
    top = 6 + MARGIN_TOP - OY
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def rel(x, y):
        return int(round((x + MARGIN_X - OX) * 2)), int(round((y + MARGIN_TOP - OY) * 2))
    near = [rel(HAND_POINT[0] + p.hand[0], HAND_POINT[1] + p.hand[1] - p.breath) for (_, p) in FRAMES]
    near2 = [rel(RAISED_HAND[0], RAISED_HAND[1] - p.breath - p.tremble) if p.near_up == 2 else rel(44.0, 30.0 - p.breath)
             for (_, p) in FRAMES]
    mx, my = rel(*MOUTH_PT)
    tx, ty = rel(*THROAT)
    lines = [
        "// <auto-generated> by art/bosses/fungimancer/make_fungimancer_art.py - do not edit by hand. </auto-generated>",
        "namespace Cogpunk.Content.Bosses.Fungimancer",
        "{",
        "\t/// <summary>The Fungimancer's grid sheets (game px, facing left): its far, middle and near planes and its glow, equal",
        "\t/// cells in <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is under its seat's middle.",
        "\t/// Body*: its hitbox from the origin. Per frame, from the origin, facing left: NearX/NearY the raised (far) hand's",
        "\t/// fingertips (its spells leave them); Near2X/Near2Y the other hand (raised in the channel); Lift the breath (0/1 art",
        "\t/// px the upper body is raised: the overlays follow it). Mouth: the mouth's middle (the burp leaves it). Overlays (the",
        "\t/// burp's throat and mouth, the hypnotic eyes, the death's puff): their own cells and origins, drawn at the body's",
        "\t/// origin; Burp and Eyes cells come in two rows, lift 0 then lift 1.</summary>",
        "\tpublic static class FungimancerRigData",
        "\t{",
        "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
        % (W * 2, H * 2, OX * 2, OY * 2, len(FRAMES), COLUMNS),
    ]
    for k in range(0, len(seq), 4):
        lines.append("\t\tpublic const int " + ", ".join(seq[k:k + 4]) + ";")
    lines += [
        "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, BodyBottom = 0;" % (left * 2, right * 2, top * 2),
        "\t\tpublic const int MouthX = %d, MouthY = %d, ThroatX = %d, ThroatY = %d;" % (mx, my, tx, ty),
        "\t\tpublic const int BurpCellW = %d, BurpCellH = %d, BurpOriginX = %d, BurpOriginY = %d, BurpFrames = %d;" % BURP_RIG,
        "\t\tpublic const int EyeCellW = %d, EyeCellH = %d, EyeOriginX = %d, EyeOriginY = %d, EyeFrames = %d;" % EYE_RIG,
        "\t\tpublic const int PuffCellW = %d, PuffCellH = %d, PuffOriginX = %d, PuffOriginY = %d, PuffFrames = %d;" % PUFF_RIG,
        "\t\tpublic static readonly short[] NearX = { %s };" % ", ".join(str(a) for a, _ in near),
        "\t\tpublic static readonly short[] NearY = { %s };" % ", ".join(str(b) for _, b in near),
        "\t\tpublic static readonly short[] Near2X = { %s };" % ", ".join(str(a) for a, _ in near2),
        "\t\tpublic static readonly short[] Near2Y = { %s };" % ", ".join(str(b) for _, b in near2),
        "\t\tpublic static readonly byte[] Lift = { %s };" % ", ".join(str(p.breath) for _, p in FRAMES),
        "\t}",
        "}",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("wrote", path)


# --- overlays (2026-11-25) -----------------------------------------------------------------------------------------------
FACE_BOX = (15, 11, 42, 29)              # model px (x0, y0, x1, y1 exclusive): the mouth and the throat, never the eyes
BURP_POSES = (dict(sac=0.4), dict(sac=0.8), dict(sac=1.15), dict(sac=0.6, mouth=3), dict(sac=0.2, mouth=2))


def crop_cell(px, box):
    """`px` (cell coords) inside `box` (model coords; one more row on top for the breath) -> (cell, w, h, origin x, y)."""
    x0, y0, x1, y1 = box
    cx0, cy0 = x0 + MARGIN_X, y0 + MARGIN_TOP - 1
    w, h = x1 - x0, y1 - y0 + 1
    cell = {(x - cx0, y - cy0): c for (x, y), c in px.items() if cx0 <= x < cx0 + w and cy0 <= y < cy0 + h}
    return cell, w, h, OX - cx0, OY - cy0


def burp_cells():
    """The burp (user: "he quickly burps a pink ... projectile"; "can be performed on the midle of other attacks"): the throat
    sac swelling and the mouth popping open, as an overlay of the middle plane's face over any body frame (its lift's row)."""
    rows = []
    for b in (0, 1):
        row = []
        for kw in BURP_POSES:
            mid = frame(Pose(breath=b, **kw))[1]
            row.append(crop_cell(mid, FACE_BOX))
        rows.append(row)
    return rows


RAINBOW = (RAMP["crimson"][4], RAMP["ember"][2], RAMP["ember"][3], RAMP["fel"][6], RAMP["emerald"][4], (67, 221, 248),
           RAMP["aether"][2], RAMP["amethyst"][4])
EYE_FRAMES = 8
EYE_BOX = (21, 6, 38, 12)


def ring_order(x0, y0, x1, y1):
    """The border of a box, clockwise from its top-left pixel."""
    top = [(x, y0) for x in range(x0, x1)]
    right = [(x1 - 1, y) for y in range(y0 + 1, y1)]
    bottom = [(x, y1 - 1) for x in range(x1 - 2, x0 - 1, -1)]
    left = [(x0, y) for y in range(y1 - 2, y0, -1)]
    return top + right + bottom + left


def eye_cells():
    """The hypnotic eyes (user: "during this time his eyes become spinnig rainbow colored hipotic pattern"): each iris's rim a
    ring of the rainbow that steps round a pixel a frame (it spins), its middle cycling the other way; 8 frames, full-bright."""
    rows = []
    for b in (0, 1):
        row = []
        for k in range(EYE_FRAMES):
            px = {}
            for (x0, y0, x1, y1) in EYES:
                ring = ring_order(x0, y0, x1, y1)
                for i, (x, y) in enumerate(ring):
                    px[(x + MARGIN_X, y - b + MARGIN_TOP)] = RAINBOW[(i + k) % len(RAINBOW)]
                inner = [(x, y) for y in range(y0 + 1, y1 - 1) for x in range(x0 + 1, x1 - 1)]
                for (x, y) in inner:
                    px[(x + MARGIN_X, y - b + MARGIN_TOP)] = RAINBOW[(len(RAINBOW) - k + 3) % len(RAINBOW)]
            row.append(crop_cell(px, EYE_BOX))
        rows.append(row)
    return rows


PUFF_W, PUFF_H, PUFF_FRAMES = 84, 76, 8


def puff_cell(k, seed=11):
    """The death's puff (user: "he should croack and puff transform into a default terraria frog critter"): a magic poof that
    swells over him in three frames, billows, and thins away; built, not drawn (blobs x noise cut into bands: white at the core,
    pink, violet at the edge), with sparkles. Origin: the body's (under the seat's middle)."""
    import random
    rnd = random.Random(seed)
    blobs = [(rnd.uniform(-24, 24), rnd.uniform(-52, -4), rnd.uniform(12, 18), rnd.uniform(0, math.tau)) for _ in range(13)]
    grow = (0.35, 0.7, 1.0, 1.08, 1.12, 1.1, 0.98, 0.85)[k]
    thin = (0.0, 0.0, 0.0, 0.02, 0.08, 0.2, 0.38, 0.56)[k]
    ox, oy = PUFF_W // 2, PUFF_H - 4
    bands = (RAMP["amethyst"][2], RAMP["amethyst"][4], RAMP["amethyst"][5], RAMP["steam"][1], RAMP["steam"][2], RAMP["steam"][3])
    px = {}
    for y in range(PUFF_H):
        for x in range(PUFF_W):
            v = 0.0
            for (bx, by, r, ph) in blobs:
                cx = ox + bx * (0.7 + 0.3 * grow) + math.cos(ph + k * 0.6) * 1.5
                cy = oy + by * (0.6 + 0.4 * grow) + math.sin(ph + k * 0.6) * 1.5 - k * 1.2
                v = max(v, 1.0 - math.hypot(x + 0.5 - cx, y + 0.5 - cy) / (r * grow))
            n = 0.5 + 0.5 * math.sin(x * 0.45 + y * 0.31 + k * 0.9) * math.cos(x * 0.27 - y * 0.52 - k * 0.4)
            v = v * (0.85 + 0.15 * n) - thin
            if v <= 0.05:
                continue
            f = v * 8.0
            band = min(len(bands) - 1, int(f))
            if (x + y) % 2 == 0 and f - int(f) > 0.78 and band < len(bands) - 1:
                band += 1
            px[(x, y)] = bands[band]
    spr = random.Random(seed + 3)
    for i in range(18):                                   # sparkles of the spell
        q = (int(ox + spr.uniform(-30, 30) * grow), int(oy - 26 + spr.uniform(-26, 22) * grow))
        if q in px and (i + k) % 3:
            px[q] = RAMP["ember"][3] if i % 2 else (67, 221, 248)
    edge = {}
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and 0 <= q[0] < PUFF_W and 0 <= q[1] < PUFF_H:
                edge[q] = RAMP["amethyst"][1]
    px.update(edge)
    return px


def overlay_sheet(rows, w, h):
    out = Image.new("RGBA", ((w + 1) * len(rows[0]), (h + 1) * len(rows)), (0, 0, 0, 0))
    for r, row in enumerate(rows):
        for k, cell in enumerate(row):
            for (x, y), c in cell[0].items():
                out.putpixel((k * (w + 1) + x, r * (h + 1) + y), tuple(c) + (255,))
    return out


_burp = burp_cells()
_eyes = eye_cells()
BURP_RIG = (_burp[0][0][1] * 2, _burp[0][0][2] * 2, _burp[0][0][3] * 2, _burp[0][0][4] * 2, len(BURP_POSES))
EYE_RIG = (_eyes[0][0][1] * 2, _eyes[0][0][2] * 2, _eyes[0][0][3] * 2, _eyes[0][0][4] * 2, EYE_FRAMES)
PUFF_RIG = (PUFF_W * 2, PUFF_H * 2, (PUFF_W // 2) * 2, (PUFF_H - 4) * 2, PUFF_FRAMES)


def crop(px, keep):
    sel = {q: c for q, c in px.items() if keep(q[0] - MARGIN_X, q[1] - MARGIN_TOP)}
    xs, ys = [x for x, _ in sel], [y for _, y in sel]
    return to_image(sel, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    export(grid([f[0] for f in frames]), OUT + "Fungimancer_Far.png")
    export(grid([f[1] for f in frames]), OUT + "Fungimancer.png")
    export(grid([f[2] for f in frames]), OUT + "Fungimancer_Near.png")
    export(grid([f[3] for f in frames]), OUT + "Fungimancer_Glow.png")
    write_rig(OUT + "FungimancerRigData.cs")
    base = composite(frames[0])
    export(crop(base, lambda x, y: 19 <= x <= 38 and 3 <= y <= 17), OUT + "Fungimancer_Head_Boss.png")
    export(overlay_sheet(_burp, _burp[0][0][1], _burp[0][0][2]), OUT + "Fungimancer_Burp.png")
    export(overlay_sheet(_eyes, _eyes[0][0][1], _eyes[0][0][2]), OUT + "Fungimancer_Eyes.png")
    puff = Image.new("RGBA", (PUFF_W, (PUFF_H + 1) * PUFF_FRAMES), (0, 0, 0, 0))
    for k in range(PUFF_FRAMES):
        for (x, y), c in puff_cell(k).items():
            puff.putpixel((x, k * (PUFF_H + 1) + y), tuple(c) + (255,))
    export(puff, OUT + "Fungimancer_Puff.png")
    export(things.bag(), OUT + "Items/FungimancerBag.png")
    export(things.summon_item(), OUT + "Items/RainbowMushroom.png")
    export(things.tile_sheet(), OUT + "Tiles/RainbowMushroomTile.png")
    fight.export_fight(OUT)
    return frames


def sheet_preview(frames, path, sc=4, cols=6, names=None):
    rows = (len(frames) + cols - 1) // cols
    out = Image.new("RGBA", (cols * (W * sc + 8) + 8, rows * (H * sc + 8) + 8), (24, 24, 30, 255))
    for k, fr in enumerate(frames):
        im = Image.new("RGBA", (W, H), (30, 34, 60, 255) if k % 2 == 0 else (52, 58, 84, 255))
        for d in fr[:3]:
            for (x, y), c in d.items():
                if 0 <= x < W and 0 <= y < H:
                    im.putpixel((x, y), tuple(c) + (255,))
        out.alpha_composite(im.resize((W * sc, H * sc), Image.NEAREST), (8 + (k % cols) * (W * sc + 8), 8 + (k // cols) * (H * sc + 8)))
    out.save(path)
    print("preview", path)


def planes_preview(fr, path, sc=6):
    """The three planes of one frame side by side, the composite, and the composite with the planes shifted one art pixel
    each way (the in-game parallax at its widest: far one way, near the other), to check no gap opens."""
    def comp(dfar, dnear):
        out = {}
        for (x, y), c in fr[0].items():
            out[(x + dfar, y)] = tuple(int(v * 0.88) for v in c)
        out.update(fr[1])
        for (x, y), c in fr[2].items():
            out[(x + dnear, y)] = c
        return out
    panels = (fr[0], fr[1], fr[2], comp(0, 0), comp(-1, 1), comp(1, -1))
    out = Image.new("RGBA", (len(panels) * (W * sc + 8) + 8, H * sc + 16), (24, 24, 30, 255))
    for k, d in enumerate(panels):
        im = Image.new("RGBA", (W, H), (30, 34, 60, 255))
        for (x, y), c in d.items():
            if 0 <= x < W and 0 <= y < H:
                im.putpixel((x, y), tuple(c) + (255,))
        out.alpha_composite(im.resize((W * sc, H * sc), Image.NEAREST), (8 + k * (W * sc + 8), 8))
    out.save(path)
    print("planes", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--planes")
    ap.add_argument("--no-export", action="store_true")
    args = ap.parse_args()
    frames = [frame(p) for _, p in FRAMES] if args.no_export else export_all()
    if args.preview:
        sheet_preview(frames, args.preview)
    if args.planes:
        planes_preview(frames[0], args.planes)
    print("cell %d x %d (1x), %d frames, model %d x %d" % (W, H, len(FRAMES), W0, H0))


if __name__ == "__main__":
    main()
