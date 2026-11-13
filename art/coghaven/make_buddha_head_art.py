"""Source for the Flying Buddha Head (D4), redrawn 2026-11-12 (user, second message of the day: "rework buddha head design
is not matching the quality level. i added a example of a pixelated buddha head on the prompt so you can analise before
redesign the enemy"). The first design (a verdigris bronze head strapped with brass bands, a big cog halo) is kept in
art/coghaven/previous/make_buddha_head_art_v1_2026-11-12.py. Run from the repo root:

    python -P art/coghaven/make_buddha_head_art.py [--preview FILE]

What the reference showed, and this follows (front view, lit from the top-left): a stepped, radiant halo of concentric
rings, white-gold in the middle to orange at the rim; a tall cone of an ushnisha and a skull cap covered in staggered
round snail-shell curls, dark brown, each with an orange highlight; warm golden skin modelled in many small steps (lit in
the middle and the top-left, orange-brown at the edges and under the jaw); long thin arched brows; closed, downcast eyes
whose lids sag in a gentle curve, with lashes; a small urna between the brows; a long straight nose with shaded sides and
a rounded tip; small red lips in a calm smile; a full, rounded chin; long ears with stretched, pierced lobes; a neck with
its beauty folds. Cogpunk's own (my calls): the halo's rim is a turning brass cog, the urna is a jade gem that glows, the
neck ends in a riveted brass collar where the head was cut from its statue (steam vents from it, in code), and for the
smash the eyes open blazing jade.

How it is drawn: the skin is a height field (an oval face with the brow ridge, eye sockets and lids, the nose, lips,
cheeks and chin raised or sunk into it) lit per pixel and put on the gilt ramp in 8 steps; the hair is a lattice of round
curls, each lit on its own bump and on the cap's dome, the gaps between them dark; ears the same way. Every part outlines
itself with its ramp's darkest shade where it meets the empty air and with the next shade where it overlaps a part behind
it (the jaw over the neck, the cheeks over the ears, the curls over the brow). The features are stamped after the shading,
whole pixels, mirrored about the face's middle (pixel x mirrors to -1 - x), so they are crisp and symmetric. Stable pixels
(D4 rule 17): the head never moves inside its frames (the float's bob is in code); only the features change between
frames and the halo's cog turns, redrawn at each angle from its own polar shape.

Planes (DepthLayers grid sheets): far = the halo; middle = the head; no near sheet; the glow sheet = the halo's rings
where they show round the head (it is light), the urna and the open eyes.

Frames: Float x4 (serene, the cog turning a quarter of a tooth a frame), Wrath x3 (the telegraph: the eyes open and blaze,
the brows knit, the mouth sets), Smash x2 (wrathful, the cog spinning), Stunned x4 (dazed eyes rolling, a crack over the
brow, the mouth open).

Outputs:
    Content/Coghaven/NPCs/FlyingBuddhaHead.png, _Far.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/FlyingBuddhaHeadRigData.cs   cells, origin (under the collar's middle), frames
    Content/Coghaven/Gores/FlyingBuddhaHead_GoreHalf.png, _GoreEar.png, _GoreCog.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from rig import RAMP, Canvas, selout, soften_orphans  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
G, OK, E, K, JD, ST, IV = (RAMP[k] for k in ("gilt", "oak", "ember", "crimson", "ghost", "steel", "ivory"))
HAIR = (OK[0], OK[1], OK[2], OK[3], OK[4], E[2])            # the curls: dark brown to an orange highlight
# The skin: warm gold, its shadows shifting to orange-brown (the reference's edges and jaw), its light to cream.
SKIN = (G[0], OK[1], OK[2], OK[3], OK[4], G[6], G[7], E[3], G[8], G[9])


def _norm(x, y, z):
    n = math.sqrt(x * x + y * y + z * z) or 1.0
    return x / n, y / n, z / n


LIGHT = _norm(-0.30, -0.42, 0.86)                           # from the top-left, towards the viewer (y down)


def g2(u, v, cu, cv, su, sv):
    return math.exp(-(((u - cu) / su) ** 2 + ((v - cv) / sv) ** 2))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# --- shapes (u = x + 0.5 and v = y + 0.5: pixel centres, the face's middle at u = 0; the origin under the collar) ----------
FACE_C, FACE_A, FACE_BT, FACE_BB = -25.0, 13.4, 14.5, 15.0   # cheekbone line, half-width, reach up and down


def face_hw(v):
    """The face's half-width at v: a full oval, broad at the cheekbones, rounding into the chin at v = -10."""
    if v < FACE_C:
        t = (FACE_C - v) / FACE_BT
        return FACE_A * (1.0 - t ** 3) ** (1.0 / 3.0) if t < 1.0 else 0.0
    t = (v - FACE_C) / FACE_BB
    return FACE_A * (1.0 - t ** 2.2) ** 0.5 if t < 1.0 else 0.0


def brow_v(au):
    """The brow's line (v) at |u|: from the bridge up into an arch and down to the temple."""
    return -28.6 - 2.2 * math.exp(-((au - 6.6) / 3.6) ** 2)


def face_z(u, v):
    hw = face_hw(v)
    if hw <= 0.0 or abs(u) >= hw:
        return None
    s = u / hw
    t = (v + 24.0) / 17.0
    z = 9.0 * math.sqrt(1.0 - s * s) * math.sqrt(max(0.0, 1.0 - 0.62 * t * t))
    au = abs(u)
    if 1.6 < au < 12.6:                                        # the brow ridge
        z += 0.75 * math.exp(-((v - brow_v(au) - 0.6) / 1.3) ** 2)
    z -= 1.6 * g2(au, v, 5.8, -25.4, 3.5, 2.1)                 # the eye sockets
    z += 0.7 * g2(au, v, 5.8, -26.5, 2.9, 0.9)                 # the upper lids
    if -29.5 < v < -18.8:                                      # the nose: a ridge from the bridge to a rounded tip
        grow = smooth((v + 29.5) / 3.2)
        w = 1.2 + 1.0 * smooth((v + 25.0) / 5.0)
        tip = g2(0.0, v, 0.0, -21.0, 1.0, 1.3)
        end = 1.0 - smooth((v + 19.6) / 0.8)
        z += (2.3 * grow + 1.0 * tip) * math.exp(-(u / w) ** 2) * end
    z += 0.8 * g2(au, v, 2.5, -20.4, 1.0, 0.9)                 # the nostril wings
    z += 0.7 * g2(au, v, 7.8, -19.6, 3.4, 3.0)                 # the cheeks
    z += 0.8 * g2(u, v, 0.0, -16.4, 3.5, 1.4)                  # the lips
    z -= 0.5 * g2(au, v, 4.3, -16.6, 0.9, 1.0)                 # the corners of the mouth
    z -= 0.45 * g2(u, v, 0.0, -14.6, 2.6, 0.6)                 # under the lower lip
    z += 1.0 * g2(u, v, 0.0, -12.9, 3.3, 1.5)                  # the chin
    return z


def lit(zf, u, v, step=0.5):
    """n . L of a height field at (u, v), by central differences (a missing side reuses the middle)."""
    z0 = zf(u, v)
    zl, zr, zu, zd = zf(u - step, v), zf(u + step, v), zf(u, v - step), zf(u, v + step)
    zl = z0 if zl is None else zl
    zr = z0 if zr is None else zr
    zu = z0 if zu is None else zu
    zd = z0 if zd is None else zd
    nx, ny, nz = _norm(-(zr - zl) / (2 * step), -(zd - zu) / (2 * step), 1.0)
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


def neck_hw(v):
    return 6.3 + 0.25 * max(0.0, v + 10.0) if -14.0 <= v <= -4.0 else 0.0


# The hair: the skull's cap and the ushnisha's cone, both covered in curls.
CAP = (0.0, -33.0, 14.2, 13.6)                               # centre and radii of the cap's dome
CONE_BASE, CONE_TOP, CONE_HW = -43.0, -58.0, 7.0


def cone_hw(v):
    if not CONE_TOP <= v <= CONE_BASE:
        return 0.0
    t = (CONE_BASE - v) / (CONE_BASE - CONE_TOP)
    return CONE_HW * max(0.0, 1.0 - t ** 1.7) ** 0.62


def hairline_v(u):
    return -35.0 + 2.6 * (u / 13.0) ** 2


# The curls: 4x4 knobs on a staggered lattice (rows 4 px apart, every other row 2 px over), each lit from the top-left
# with a highlight dot, its corners dark so it reads round; the lattice is symmetric about the face's middle.
CURL = ("DMMD",
        "MHMS",
        "MMSS",
        "DSSD")
CURL_LEVELS = (                                               # by the cap's light where the curl sits: D, S, M, H
    (0, 1, 1, 3),
    (0, 1, 2, 4),
    (0, 2, 3, 5),
    (0, 2, 4, 5),
)
CURL_BOTTOM = -38                                             # the lowest row's top: its knobs hang over the brow


def curl_origins():
    out = []
    for k in range(7):
        y = CURL_BOTTOM - 4 * k
        off = 0 if k % 2 == 0 else 2
        for j in range(-5, 5):
            out.append((4 * j + off, y, k))
    return out


CURLS = curl_origins()


def in_hair_mass(u, v):
    cu, cv, ru, rv = CAP
    if ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2 < 1.0 and v < hairline_v(u):
        return True
    return abs(u) < cone_hw(v)


# --- painting ---------------------------------------------------------------------------------------------------------------
class Painter:
    """One canvas painted part by part, back to front, remembering which part owns each pixel (for the outlines)."""

    def __init__(self, cv):
        self.cv = cv
        self.owner = {}
        self.depth = 0

    def paint(self, pixels, ramp, edge=0, inner=1):
        """pixels: {(x, y): colour}. Outlines the part: its edge pixels touching empty air take ramp[edge], those over
        an earlier part take ramp[inner]."""
        self.depth += 1
        for q, col in pixels.items():
            self.cv.put(q[0], q[1], col)
            self.owner[q] = self.depth
        for (x, y) in pixels:
            nb = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if any(n not in self.owner for n in nb):
                self.cv.put(x, y, ramp[edge])
            elif any(self.owner[n] < self.depth for n in nb):
                self.cv.put(x, y, ramp[inner])


def rows(y0, y1, x0, x1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            yield x, y


def skin_index(i, lo=2, hi=9, gamma=1.1):
    i = max(0.0, min(1.0, i))
    return max(lo, min(hi, int(round(lo + (hi - lo + 0.4) * i ** gamma - 0.2))))


def neck_part():
    """A short, full neck in the jaw's shadow, lit on its left, with one beauty fold."""
    px = {}
    for (x, y) in rows(-14, -5, -9, 8):
        u, v = x + 0.5, y + 0.5
        hw = neck_hw(v)
        if hw and abs(u) < hw:
            s_ = u / hw
            k = 5 if s_ < -0.35 else 4 if s_ < 0.3 else 3
            if v < -9.0:
                k -= 1                                            # under the jaw
            px[(x, y)] = SKIN[k]
    for x in range(-5, 5):                                       # the fold: a soft curve, lit on its lower lip
        if (x, -8) in px:
            px[(x, -8)] = SKIN[2] if x > -3 else SKIN[3]
        if (x, -7) in px and x < 2:
            px[(x, -7)] = SKIN[6] if x < -2 else SKIN[5]
    return px


def collar_part():
    """The riveted brass collar where the head was cut from its statue: a lit top lip, the band, a dark bottom lip."""
    px = {}
    for (x, y) in rows(-6, 0, -11, 10):
        u, v = x + 0.5, y + 0.5
        hw = 8.8 + 0.25 * (v + 6.0)
        if abs(u) >= hw:
            continue
        side = 1 if u < -3.0 else 0 if u < 4.0 else -1
        if y == -6:
            k = 7 + max(0, side)
        elif y <= -2:
            k = 5 + side
        elif y == -1:
            k = 3 + max(0, side)
        else:
            k = 1
        px[(x, y)] = G[k]
    for x in (-8, -4, 3, 7):                                     # rivets, lit on top
        px[(x, -4)] = ST[7] if x < 0 else ST[5]
        px[(x, -3)] = ST[2]
    return px


# The left ear, drawn by hand (tone digits on SKIN; "." is empty): the helix rim lit along its outer edge, the hollow
# inside it, the antihelix, and the long stretched lobe with its pierced slit. The right ear is its mirror, a step darker
# (it turns from the light).
EAR = ("..000.",
       ".07650",
       "076543",
       "075433",
       "065334",
       "065234",
       "065234",
       "065334",
       "065434",
       "056443",
       ".05543",
       ".05442",
       ".06443",
       "056143",
       "056143",
       "056143",
       "056243",
       "056543",
       "045432",
       ".0443.",
       "..00..")
EAR_X, EAR_Y = -18, -33                                        # the map's top-left pixel


def ear_part(side):
    """side -1: the left ear, +1: the right (mirrored, a step darker)."""
    px = {}
    for dy, row in enumerate(EAR):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            k = int(ch)
            x, y = EAR_X + dx, EAR_Y + dy
            if side > 0:
                x = -1 - x
                k = k if k <= 1 else max(1, k - 1)
            px[(x, y)] = SKIN[k]
    return px


def face_part():
    px = {}
    for (x, y) in rows(-40, -10, -14, 13):
        u, v = x + 0.5, y + 0.5
        z = face_z(u, v)
        if z is None:
            continue
        d = max(0.0, lit(face_z, u, v))
        i = 0.03 + 0.95 * d ** 2.6
        hw = face_hw(v)
        rim = max(0.0, abs(u) / hw - 0.62) / 0.38                # the edges turn orange-brown on both sides
        i *= 1.0 - 0.5 * rim ** 1.3
        i -= 0.16 * smooth((v + 15.5) / 4.0) * (1.0 if abs(u) > 3.5 else 0.4)   # the jaw falls into shade
        px[(x, y)] = SKIN[skin_index(i)]
    return px


def hair_light(u, v):
    """The cap's (or the cone's) own light at (u, v): its macro form, lit from the top-left."""
    if abs(u) < cone_hw(v) and v < CONE_BASE + 0.5:
        hw = max(0.5, cone_hw(v))
        n = _norm(0.9 * u / hw, -0.45, math.sqrt(max(0.05, 1.0 - (u / hw) ** 2)))
    else:
        cu, cv, ru, rv = CAP
        a, b = (u - cu) / ru, (v - cv) / rv
        n = _norm(a, b, math.sqrt(max(0.05, 1.0 - min(1.0, a * a + b * b))))
    return n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]


def hair_part():
    """The mass is filled dark (the gaps between the curls), then the curls are stamped over it; the bottom row's knobs
    hang over the brow (a scalloped hairline). The cone's base gets a dark crease where it rises from the cap."""
    mass = set()
    for (x, y) in rows(-60, -30, -16, 15):
        if in_hair_mass(x + 0.5, y + 0.5):
            mass.add((x, y))
    px = {q: HAIR[0] for q in mass}
    for (x0, y0, k) in sorted(CURLS, key=lambda c: c[1]):
        cu, cv = x0 + 2.0, y0 + 2.0
        on_cone = abs(cu) < cone_hw(cv) and cv < CONE_BASE
        if not on_cone and not ((cu / CAP[2]) ** 2 + ((cv - CAP[1]) / CAP[3]) ** 2 < 1.05):
            continue
        light = hair_light(cu, cv)
        level = 3 if light > 0.62 else 2 if light > 0.38 else 1 if light > 0.12 else 0
        tones = dict(zip("DSMH", CURL_LEVELS[level]))
        for dy, row in enumerate(CURL):
            for dx, ch in enumerate(row):
                q = (x0 + dx, y0 + dy)
                inside = q in mass or (k == 0 and dy >= 1 and face_z(q[0] + 0.5, q[1] + 0.5) is not None)
                if not inside or (ch == "D" and q not in mass):
                    continue
                px[q] = HAIR[tones[ch]]
    # the crease round the cone's foot
    for x in range(-8, 8):
        u = x + 0.5
        if abs(u) < cone_hw(CONE_BASE - 0.5):
            q = (x, int(CONE_BASE))
            if q in px:
                px[q] = HAIR[0]
    return px


def features(cv, glow, pose):
    """Brows, eyes, nose, mouth, urna: whole pixels on the finished shading, mirrored about the face's middle."""
    def both(x, y, col, glowing=False, mirror_col=None):
        for k, xx in enumerate((x, -1 - x)):
            c = col if (k == 0 or mirror_col is None) else mirror_col
            if glowing:
                cv.put_glow(xx, y, c)
                glow.put_glow(xx, y, c)
            else:
                cv.put(xx, y, c)

    # brows: long, thin and arched (serene), or knitted down at the bridge (wrath)
    serene = ((-2, -28), (-3, -29), (-4, -30), (-5, -30), (-6, -31), (-7, -31), (-8, -31), (-9, -30), (-10, -30), (-11, -29), (-12, -28))
    knit = ((-2, -27), (-3, -28), (-4, -28), (-5, -29), (-6, -29), (-7, -30), (-8, -30), (-9, -30), (-10, -30), (-11, -29), (-12, -28))
    for (x, y) in (knit if pose.brows else serene):
        both(x, y, SKIN[1], mirror_col=SKIN[1])
    # eyes
    if pose.eyes == "closed":
        lid = ((-9, -27), (-8, -26), (-7, -26), (-6, -26), (-5, -26), (-4, -26), (-3, -27))
        for (x, y) in lid:
            both(x, y, SKIN[1])
        for (x, y) in ((-8, -25), (-6, -25), (-9, -26)):          # lashes, heavier at the outer corner
            both(x, y, SKIN[2], mirror_col=SKIN[2])
        for (x, y) in ((-7, -27), (-6, -27), (-5, -27)):          # the lid's rounded top catches the light
            both(x, y, SKIN[7], mirror_col=SKIN[5])
    elif pose.eyes in ("open", "blaze"):
        top = ((-8, -28), (-7, -28), (-6, -28), (-5, -28), (-4, -28)) if pose.eyes == "blaze" else ((-8, -27), (-7, -27), (-6, -27), (-5, -27), (-4, -27))
        for (x, y) in top:
            both(x, y, SKIN[1])
        both(-9, -27 if pose.eyes == "blaze" else -26, SKIN[1])
        both(-3, -27 if pose.eyes == "blaze" else -26, SKIN[1])
        rows_ = (-27, -26) if pose.eyes == "blaze" else (-26,)
        for y in rows_:
            for x in range(-8, -3):
                both(x, y, IV[5] if x in (-8, -4) else JD[4], glowing=x not in (-8, -4), mirror_col=IV[4] if x in (-8, -4) else JD[4])
        both(-6, rows_[0], JD[5], glowing=True)
        if pose.eyes == "blaze":
            both(-7, -27, JD[5], glowing=True)
        for (x, y) in ((-8, -25), (-7, -25), (-6, -25), (-5, -25), (-4, -25)):
            both(x, y, SKIN[2], mirror_col=SKIN[2])
    elif pose.eyes == "slit":                                     # the first frame of wrath: a gleam under the lids
        for (x, y) in ((-9, -27), (-8, -27), (-7, -27), (-6, -27), (-5, -27), (-4, -27), (-3, -27)):
            both(x, y, SKIN[1])
        for x in range(-8, -3):
            both(x, -26, JD[3] if x != -6 else JD[5], glowing=True)
        for x in (-8, -6, -4):
            both(x, -25, SKIN[2])
    else:                                                         # dazed: heavy lids, the eyes rolling
        for x in range(-9, -2):
            both(x, -27, SKIN[1])
        for x in range(-8, -3):
            both(x, -26, IV[4], mirror_col=IV[3])
        p = (-7, -5, -4, -6)[pose.daze % 4]
        both(p, -26, SKIN[0])
        for x in (-8, -7, -6, -5, -4):
            both(x, -25, SKIN[2])
    # the nose: nostrils under the rounded tip
    both(-2, -20, SKIN[1], mirror_col=SKIN[1])
    both(-1, -19, SKIN[3], mirror_col=SKIN[2])
    # the mouth
    if pose.mouth == "smile":
        for x in (-3, -2, -1):
            both(x, -17, K[3], mirror_col=K[3])
        both(-4, -17, K[1])
        for x in (-3, -2, -1):
            both(x, -16, K[1])
        for x in (-2, -1):
            both(x, -15, K[4], mirror_col=K[4])
        cv.put(-2, -15, K[5])
        both(-5, -18, K[2])                                       # the corners turn up
    elif pose.mouth == "set":
        for x in (-4, -3, -2, -1):
            both(x, -17, K[3])
            both(x, -16, K[1])
        both(-5, -16, K[1])
        for x in (-2, -1):
            both(x, -15, K[4], mirror_col=K[3])
    else:                                                         # open: a shout, or the stunned gape
        for x in (-3, -2, -1):
            both(x, -18, K[3])
        for x in (-3, -2, -1):
            both(x, -17, K[0])
            both(x, -16, K[1] if x == -3 else K[0])
        both(-4, -17, K[2])
        for x in (-2, -1):
            both(x, -15, K[4], mirror_col=K[3])
    # the urna: a jade gem between the brows (it glows; it flares in wrath)
    u_col = (JD[3], JD[4], JD[5])[min(2, pose.glow)]
    both(-1, -30, u_col, glowing=True)
    both(-1, -29, JD[2] if pose.glow == 0 else JD[4], glowing=True)
    if pose.crack:
        for (x, y, col) in ((4, -36, SKIN[0]), (4, -35, SKIN[0]), (3, -34, SKIN[0]), (3, -33, SKIN[1]), (4, -32, SKIN[0]), (5, -31, SKIN[1]),
                            (5, -35, SKIN[7]), (2, -33, SKIN[7])):
            cv.put(x, y, col)


# --- the halo (far plane) ---------------------------------------------------------------------------------------------------
HALO_C = (0.0, -31.0)
RINGS = ((17.5, G[9]), (20.0, G[8]), (22.5, E[3]), (24.6, G[7]), (26.0, E[2]))
RIM_ROOT, RIM_TIP, TEETH = 27.4, 29.6, 16


def halo(far, glow, mid, pose):
    hu, hv = HALO_C
    for y in range(int(hv - RIM_TIP - 2), int(hv + RIM_TIP + 2)):
        for x in range(int(hu - RIM_TIP - 2), int(hu + RIM_TIP + 2)):
            du, dv = x + 0.5 - hu, y + 0.5 - hv
            r = math.hypot(du, dv)
            th = math.degrees(math.atan2(dv, du)) - pose.halo
            tooth = math.cos(math.radians(th * TEETH)) > -0.05
            outer = RIM_TIP if tooth else RIM_ROOT
            if r >= outer:
                continue
            ring = next((c for (rr, c) in RINGS if r < rr), None)
            if ring is not None:
                far.put(x, y, ring)
                if (x, y) not in mid.px:
                    glow.glow[(x, y)] = ring                       # the rings are light: fullbright where they show
                continue
            # the brass cog: lit from the top-left, outlined in its darkest shade
            light = -(du * 0.62 + dv * 0.78) / max(1.0, r)
            if r >= outer - 1.0 or r < RINGS[-1][0] + 0.9:
                col = G[1] if r >= outer - 1.0 else G[3]
            else:
                col = G[max(3, min(8, 5 + int(round(light * 2.6))))]
            far.put(x, y, col)
    # the outline's lit side catches the light
    selout(far)


# --- poses and frames ---------------------------------------------------------------------------------------------------------
class Pose:
    def __init__(self, eyes="closed", glow=0, brows=0, mouth="smile", halo=0.0, crack=False, daze=0):
        self.eyes = eyes            # closed, slit, open, blaze, dazed
        self.glow = glow            # 0..2: the urna's blaze
        self.brows = brows          # 0 serene, 1 knitted
        self.mouth = mouth          # smile, set, open
        self.halo = halo            # degrees the cog has turned
        self.crack = crack
        self.daze = daze


def head(mid):
    p = Painter(mid)
    p.paint(neck_part(), G)
    p.paint(collar_part(), G)
    p.paint(ear_part(-1), G)
    p.paint(ear_part(+1), G)
    p.paint(face_part(), G)
    p.paint(hair_part(), HAIR)
    soften_orphans(mid, 14.0)
    selout(mid)


def frame(pose):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    head(mid)
    features(mid, glow, pose)
    halo(far, glow, mid, pose)
    return far, mid, near, glow


STEP = 360.0 / TEETH / 4.0                     # a quarter of a tooth a frame: the float loops in 4
FRAMES = ([("Float%d" % k, Pose(halo=STEP * k)) for k in range(4)]
          + [("Wrath0", Pose(eyes="slit", glow=1, halo=0.0)),
             ("Wrath1", Pose(eyes="open", glow=2, brows=1, mouth="set", halo=STEP)),
             ("Wrath2", Pose(eyes="blaze", glow=2, brows=1, mouth="set", halo=STEP * 2))]
          + [("Smash%d" % k, Pose(eyes="blaze", glow=2, brows=1, mouth="open", halo=STEP * 2 * k)) for k in range(2)]
          + [("Stunned%d" % k, Pose(eyes="dazed", daze=k, mouth="open", crack=True, halo=0.0)) for k in range(4)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# --- outputs -----------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Stunned0"])
    return {"FlyingBuddhaHead_GoreHalf": crop({q: c for q, c in mid.px.items() if -13 <= q[0] <= -1 and q[1] > -40}),
            "FlyingBuddhaHead_GoreEar": crop({q: c for q, c in mid.px.items() if q[0] >= 13}),
            "FlyingBuddhaHead_GoreCog": crop({q: c for q, c in far.px.items() if q[0] <= -14 and q[1] >= -26})}


def write_rig(path, cell):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/coghaven/make_buddha_head_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.NPCs",
         "{",
         "\t/// <summary>The Flying Buddha Head's grid sheets (game px; it faces the camera): far (the halo), middle (the head),",
         "\t/// near (empty) and the glow, equal cells with 2 px under each; the origin is under the collar's middle.</summary>",
         "\tpublic static class FlyingBuddhaHeadRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Float = 0, FloatFrames = 4, Wrath = %d, WrathFrames = 3, Smash = %d, SmashFrames = 2, Stunned = %d, StunnedFrames = 4;"
         % (INDEX["Wrath0"], INDEX["Smash0"], INDEX["Stunned0"]),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1)):                  # no near plane: nothing is in front of a head
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/FlyingBuddhaHead%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/FlyingBuddhaHead_Glow.png")
    write_rig(OUT + "NPCs/FlyingBuddhaHeadRigData.cs", cell)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=4, names=None):
    names = names or [n for n, _ in FRAMES]
    cw, ch = 64, 64
    cols = min(5, len(names))
    rws = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rws * 2), (0, 0, 0, 0))
    lookup = dict(FRAMES)
    for half, bg in ((0, (34, 40, 46, 255)), (1, (150, 170, 190, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rws), bg)
        for k, n in enumerate(names):
            far, mid, near, glow = frame(lookup[n])
            t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for cvs in (far, mid, near):
                t.alpha_composite(to_image(cvs.px, -cw // 2, -ch + 2, cw, ch))
            tile.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
        sheet.paste(tile, (0, half * ch * rws))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames", help="comma-separated frame names for the preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview, names=a.frames.split(",") if a.frames else None)
    else:
        export_all()
