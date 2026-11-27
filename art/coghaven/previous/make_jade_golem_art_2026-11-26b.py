"""Source for the Jade Golem, a Coghaven enemy (D4), and its jade ray. Run from the repo root:

    python -P art/coghaven/make_jade_golem_art.py [--preview FILE [--frames A,B]] [--walk-gif FILE]

Version 3 (2026-11-26b, the user: "rework jade golems design, it should be more sideways im gonna provide a reference art for
a jade golem and a reference art for the default terraria ice golem so you can analise for the redesign. after redesigning,
work on maching arm laser and targeting animations frames and colors to the new design"): turned to the side as vanilla's
Ice Golem walks (his torso in profile: a chest bulging forward and a hump behind, his head thrust forward between his
shoulders, one arm in front of him and one behind, his legs striding under him), and built as the jade golem reference is
(our own drawing, its look only): saturated emerald stone (the palette's emerald ramp; the island's pale ghost jade before)
carved into blocky plates split by dark seams, each plate lit on its own and catching the light on its top-left lip; a
heavy-browed Moai head in profile with one glowing eye and a beard of rough stone; a stone band of glowing runes round
each wrist; a bronze belt whose round disc in front holds his glowing core; a skirt of stone leaves under it; jade
crystals on his back. The open palms stay (2026-11-10b: the ray leaves the palm), the ray and its charge recoloured in
the emerald glow. Versions 1 and 2 are in art/coghaven/previous/ (v2, facing the screen: make_jade_golem_art_2026-11-26.py).

Version 2 (2026-11-09, the user: "no Terraria quality nor Metal Slug pixel density ... the jade golem is currently with a
horrible walking animation that does not fit properly, ensure good animation like the Jaeger's movement"); version 1 is
kept in art/coghaven/previous/.

Design (user, 2026-11-06, from the user's reference image: a hulking green jade stone golem with a Moai-like bearded
head, glowing green eyes, huge fists and glowing rune bracelets): about 2.9 times the player, hunched like a great ape. A
barrel torso of polished jade (the Ghost ramp, the island's jade bricks' own) facing the screen (user, 2026-11-06),
built of two carved blocks (a chest and a belly with a seam between them), marbled with pale veins, a bronze cog over its
glowing heart on the torso's axis; boulder shoulders set wide, jade crystals growing out of the far one; the Moai head
(hand-placed, so nothing eats its features) sunk forward between them: a heavy brow over deep sockets with glowing eyes,
a long hooked nose, a jutting lip and chin, a long ear, a beard of rough jade (Verdigris) carved in three tiers; long
arms, the forearms thicker than the upper arms, huge knuckled fists, a bronze bracelet with glowing runes on each wrist;
a rough-jade pelvis under a riveted bronze belt; short pillar legs on block feet with split toes. Lit from the top-left.

Walk (the Jaeger's, art/mecharmy): a 16-frame cycle in which each foot is planted for 8 frames and slides back exactly
WALK_STEP a frame (the root motion: in game the frame advances with the distance walked, so a planted foot never slips),
heel strike at the front, toe-off behind, then swung forward through a LIFT-px arc; the body is lowest at each heel
strike and rises through mid-stance; the arms hang still and only ride the bob (user, 2026-11-09: "remove the arms
animation from the golem while he's walking as it's a bit glitchy"; they swung 4 px against the legs).

Three planes (DepthLayers.DrawWalker grid sheets in COLUMNS columns): far (the far leg and arm, one tone a step darker),
middle (the near leg, the pelvis, the body, the head), near (the near arm, its bracelet and the near shoulder boulder);
the glow sheet holds the eyes, the heart and the runes (brightened in game while he charges). Stable pixels (D4 rule 17):
the body is built in its own space and placed by whole-pixel bobs; limbs are lit with their light's turn snapped; far
limbs are one tone; the aiming arm is rendered here for every angle (never rotated at runtime, D4 rule 14).

Frames: Walk x16, Idle x4, Aim x13 (the near arm pointed from straight up to straight down in 15 degree steps, the legs
braced): in game the arm steps through them to follow its target.

Outputs:
    Content/Coghaven/NPCs/JadeGolem.png, _Far.png, _Near.png, _Glow.png   grid sheets
    Content/Coghaven/NPCs/JadeGolemRigData.cs     cells, origin, frame runs, the walk step, the fist per aim frame
    Content/Coghaven/Gores/JadeGolem_GoreHead.png, _GoreFist.png, _GoreHeart.png, _GoreCrystal.png
    Content/Coghaven/Projectiles/JadeRay.png       16x52: the ray's electric nodes, three 16x16 crackles 2 px apart
    Content/Coghaven/Projectiles/JadeRay_Orb.png   24x128: the charge gathering in his fist, five 24x24 sizes 2 px apart
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from westbots import (RAMP, Xf, Poly, Ellipse, Union, box, Canvas, flat, dome, face, P, finish, limb, ik, G, _hash)  # noqa: E402
from make_trashtr0m_art import export, to_image, GROUND_CLIP  # noqa: E402
from make_mecharmy_art import fit_cell  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Coghaven/"
JD = RAMP["emerald"]                                 # jade stone (0 outline .. 5 the glow's colour, 6 its white-green); v3
VD = RAMP["frog"]                                    # rough jade: the dull greens (beard, feet, skirt, rune bands)
WHITE = RAMP["steam"][3]
COLUMNS = 3                                          # 33 tall cells: one column would pass the 2048 px texture limit

# --- proportions (1x art px, y up negative, the origin on the ground under the hips; v3: in profile, facing left) ----------
HIP_NEAR, HIP_FAR = (-2.0, -19.0), (2.2, -19.4)
THIGH, SHIN = 8.6, 8.2
ANKLE_Y = -4.6
SHOULDER_NEAR, SHOULDER_FAR = (-2.5, -40.5), (4.0, -41.5)
UPPER, FORE, FIST = 11.0, 12.0, 6.4
HEAD_AT = (-16.0, -56.0)                             # the head stencil's top-left in the body's own space (sunk between the shoulders)
CHEST = (-4.0, -35.0, 10.0, 10.5)                    # the torso: the chest bulging forward ...
BACK = (4.5, -36.0, 8.8, 10.0)                       # ... the hump behind ...
WAIST = [(-11.5, -32.0), (10.5, -32.0), (9.5, -22.5), (-10.5, -22.5)]   # ... and the waist under them
PLATE = 3.8                                          # the stone plates' size (art px across)
AIM_MIN, AIM_STEP, AIM_FRAMES = -90, 5, 37           # degrees below "forward"; -90 straight up, +90 straight down
ARM_COLUMNS = 8                                      # the aiming arm's own sheet (2026-11-10b): 37 cells in 8 columns
JADE_LO, JADE_HI = 1, 4

# --- hand-placed parts ----------------------------------------------------------------------------------------------------
# The Moai head in profile (facing left, lit from the top-left): a flat top, a heavy brow jutting forward over a deep socket
# with one glowing eye, a long nose, a jutting lip and chin, a beard of rough stone in tiers. a..f jade 0..5, p..s rough
# jade 0..3, E and g the eye's glow (white, jade 5). Stamped after the finishing pass.
HEAD_ART = ["....aaaaaaaaa...",
            "...aefeeedddca..",
            "..aefeeeddddcba.",
            "..aeeeedddddcba.",
            ".aeeeedddddccba.",
            "afffeedddddccba.",
            "abbbbbbcdddccba.",
            ".abgEbbcdddccba.",
            ".abbbbcddddccba.",
            "..adbcdddddccba.",
            ".aedcdddddcccba.",
            "aeeddddddcccba..",
            "afeddddddcccba..",
            "aedcccccccccba..",
            ".abbbcccccccba..",
            "..aeddcccccba...",
            ".abbbbbccccba...",
            ".aeddddcccba....",
            "..aeddccccba....",
            "..psrrrqqqp.....",
            "..psrrrqqp......",
            "...psrrqqp......",
            "...pqqqqp.......",
            "....psqp........",
            ".....pp........."]
# The core in the belt's disc (a bronze rim round a glowing jade heart, seen side on). Digits are gilt shades; u jade 3;
# v, w, X glow (jade 4, jade 5, white).
HEART = [".464.",
         "47vw6",
         "5wXw7",
         "5wXv6",
         "47vw5",
         ".353."]
GLOWING = set("vwX")
# Pale veins in the stone and carved cracks (body space): (x, y) chains drawn light (veins) or dark with a lit lip.
VEINS = [[(-11, -38), (-10, -37), (-9, -37)], [(6, -41), (7, -40), (7, -39)], [(-6, -27), (-5, -26), (-4, -26)]]
CRACKS = [[(2, -30), (3, -29), (3, -28), (4, -27)], [(-8, -43), (-7, -42)], [(10, -34), (11, -33)]]
CRYSTALS = [(7.6, -43.4, 8.0, 2.6, 1.8), (11.8, -40.6, 6.2, 2.2, 2.8), (4.4, -44.6, 5.0, 2.0, 0.9)]   # base x, y, height, half width, lean


# Jade's mottling: each Ghost shade swapped for the Verdigris shade nearest it in lightness (5-6 L* apart, so the
# finishing pass keeps it, where a one-step Ghost texture is 16-20 L* and is wiped as noise), in 2-px dashes counted in
# the part's own space so it rides with the part (D4 rule 17).
SWAP = {JD[1]: VD[1], JD[2]: VD[3], JD[3]: VD[4], JD[4]: VD[5]}   # v3: the frog greens just darker than the stone, never its yellows


def mottle(cv, pixels, ox, oy, seed, density=0.32):
    for (x, y) in pixels:
        col = cv.px.get((x, y))
        if col not in SWAP:
            continue
        lx, ly = x - ox, y - oy
        h = (((lx // 2) * 73856093) ^ (ly * 19349663) ^ (seed * 83492791)) & 0xFFFF
        if h / 65535.0 < density:
            cv.put(x, y, SWAP[col])


def limb_mottle(cv, pixels, a, b, seed, density=0.3):
    """The mottling on a limb, counted along and across its own axis (from joint a towards b), so it turns with the limb."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    for (x, y) in pixels:
        col = cv.px.get((x, y))
        if col not in SWAP:
            continue
        px, py = x + 0.5 - a[0], y + 0.5 - a[1]
        s_, t_ = int(math.floor((px * ux + py * uy) / 2.0)), int(math.floor(-px * uy + py * ux))
        h = ((s_ * 73856093) ^ (t_ * 19349663) ^ (seed * 83492791)) & 0xFFFF
        if h / 65535.0 < density:
            cv.put(x, y, SWAP[col])


def stone_plates(base, spacing, seed, lo=JADE_LO, hi=JADE_HI):
    """Carved stone plates in the part's own space (v3, the reference's blocky jade): Voronoi cells about `spacing` px
    across; a dark seam where two meet; each plate a ramp step lighter or darker than the light gives it (its own tilt); a
    lit lip along its top-left edge. Stable on a moving part (its own space, D4 rule 17)."""
    def fn(i):
        k = base(i)
        lx, ly = i.lx, i.ly
        gx, gy = int(math.floor(lx / spacing)), int(math.floor(ly / spacing))
        d1, d2, own = 1e9, 1e9, None
        for cx in (gx - 1, gx, gx + 1):
            for cy in (gy - 1, gy, gy + 1):
                px = (cx + 0.18 + 0.64 * _hash(cx, cy, seed)) * spacing
                py = (cy + 0.18 + 0.64 * _hash(cx, cy, seed + 7)) * spacing
                d = (lx - px) ** 2 + (ly - py) ** 2
                if d < d1:
                    d1, d2, own = d, d1, (cx, cy, px, py)
                elif d < d2:
                    d2 = d
        d1, d2 = math.sqrt(d1), math.sqrt(d2)
        if d2 - d1 < 0.7:
            return 0                                     # the seam: the stone's darkest
        cx, cy, px, py = own
        tilt = _hash(cx, cy, seed + 3)
        k += -1 if tilt < 0.25 else 1 if tilt > 0.8 else 0
        if d2 - d1 < 1.7 and (lx - px) * 0.6 + (ly - py) * 0.8 < -0.4:
            k += 1                                       # the lip on its top-left edge catches the light
        return max(lo, min(hi + 1, k))
    return fn


def limb_rings(cv, pixels, a, b, spacing=3.6, offset=1.2):
    """Carved rings round a stone limb (v3): every `spacing` px along its axis (from joint a towards b) a dark seam, and the
    row after it lit (its lip), counted in the limb's own axis so they ride with it (D4 rule 17). The outline is kept."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    ux, uy = dx / ln, dy / ln
    for (x, y) in pixels:
        col = cv.px.get((x, y))
        if col is None or col == JD[0] or (x, y) in cv.glow:
            continue
        t = (x + 0.5 - a[0]) * ux + (y + 0.5 - a[1]) * uy - offset
        if t <= 0.5 or t >= ln - 0.5:
            continue
        f = t / spacing - math.floor(t / spacing)
        if f < 0.22:
            cv.put(x, y, JD[1])                          # the seam
        elif f < 0.44 and col in JD:
            cv.put(x, y, JD[min(5, JD.index(col) + 1)])  # the lip after it catches the light


def stamp_head(cv, glow, x0, y0):
    jade = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 3, "f": 4}      # v3: the body's own range (its plates top out at 4-5)
    rough = {"p": 0, "q": 1, "r": 2, "s": 3}
    for dy, row in enumerate(HEAD_ART):
        for dx, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + dx, y0 + dy
            if ch in ("E", "g"):
                col = WHITE if ch == "E" else JD[5]
                cv.put_glow(x, y, col)
                glow.put_glow(x, y, col)
            elif ch in jade:
                cv.put(x, y, JD[jade[ch]])
            else:
                cv.put(x, y, VD[rough[ch]])


def stamp_heart(cv, glow, x0, y0):
    for dy, row in enumerate(HEART):
        for dx, ch in enumerate(row):
            if ch in ". ":
                continue
            x, y = x0 + dx, y0 + dy
            if ch.isdigit():
                cv.put(x, y, G[int(ch)])
                continue
            col = {"u": JD[3], "v": JD[4], "w": JD[5], "X": WHITE}[ch]
            if ch in GLOWING:
                cv.put_glow(x, y, col)
                glow.put_glow(x, y, col)
            else:
                cv.put(x, y, col)


class Pose:
    def __init__(self, bob=0, near_foot=(-5.0, 0.0), far_foot=(5.4, 0.0), near_hand=(0.0, 0.0), far_hand=(0.0, 0.0), aim=None):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot      # (x, lift) of each ankle
        self.near_hand, self.far_hand = near_hand, far_hand      # hand offsets from the hanging rest point
        self.aim = aim                                           # None, or the near arm's angle in degrees below forward


# ------------------------------------------------------------------------------------------------------------------------
# Parts
# ------------------------------------------------------------------------------------------------------------------------
def foot_block(cv, ankle, depth):
    """A block foot of rough jade with split toes, under the ankle (toes forward, left)."""
    ax, ay = ankle
    sole = ay + 4.6
    shade = flat(1, bevel=False) if depth else face((-0.5, -0.6, 0.7), lo=1, hi=3, ramp_len=4, fixed=True)
    fin = cv.part(Xf(), Poly([(ax - 5.6, ay - 1.6), (ax + 3.6, ay - 1.8), (ax + 4.4, sole), (ax - 7.4, sole), (ax - 7.0, ay + 1.0)]),
                  "frog", shade, rust=0.0)
    if depth == 0:
        for tx in (ax - 5.0, ax - 2.6):              # the toes' splits
            for ty in (sole - 1.6, sole - 0.6):
                q = P(Xf(), (tx, ty))
                if q in fin:
                    cv.put(q[0], q[1], VD[0])
        q = P(Xf(), (ax - 6.0, ay + 0.2))
        if q in fin:
            cv.put(q[0], q[1], VD[3])                # the toes' lit tip


def leg(cv, hip, foot, depth):
    ankle = (foot[0], ANKLE_Y - foot[1])
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)
    thigh = limb(cv, hip, knee, 5.4, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
    shin = limb(cv, knee, ankle, 4.8, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
    if depth == 0:
        limb_mottle(cv, thigh, hip, knee, 11)
        limb_mottle(cv, shin, knee, ankle, 13)
        limb_rings(cv, thigh, hip, knee)
        limb_rings(cv, shin, knee, ankle, offset=0.6)
    foot_block(cv, ankle, depth)
    if depth == 0:                                    # the kneecap catching the light
        q = P(Xf(), (knee[0] - 1.6, knee[1] - 0.6))
        cv.put(q[0], q[1], JD[4])
        cv.put(q[0] + 1, q[1], JD[3])
    return knee


# --- the open hands (2026-11-10b, user: "the hands of the jade golem should be an open palm hand and the jade laser has to
# come out from the hand"; they were knuckled fists) ----------------------------------------------------------------------
PALM_OFF = 3.4                                       # the palm's centre past the wrist, along the forearm
PALM_DEPTH, PALM_SPAN = 3.4, 5.6                     # aimed: the palm's half-thickness along the arm, its half-width across
HANG_LEN, HANG_SPAN = 4.2, 4.4                       # hanging: the palm's half-length down the arm, its half-width
FINGER_R = 1.7
# aimed: four fingers up off the palm's top edge (across the arm), fanned towards the aim: (base along the arm, fan angle
# in degrees towards the aim, length); the palm faces the aim and the ray leaves its face
AIM_FINGERS = ((-2.4, -30.0, 4.8), (-0.8, -10.0, 6.0), (0.8, 10.0, 6.2), (2.4, 30.0, 5.0))
# hanging: three fingers down off the palm, slightly spread, and the thumb on the front: (base across, fan angle, length)
HANG_FINGERS = ((-2.0, -12.0, 5.2), (0.0, 2.0, 6.2), (2.0, 16.0, 5.4))
PALM_FRONT = PALM_DEPTH + 1.2                        # the ray leaves the palm's face this far past the palm's centre
PALM_REACH = UPPER + FORE + PALM_OFF + PALM_FRONT    # the shoulder to that point (1x px), the same at every angle


def rotate_towards(n, u, deg):
    """The unit vector n turned `deg` degrees towards u (u perpendicular to n)."""
    a = math.radians(deg)
    return (n[0] * math.cos(a) + u[0] * math.sin(a), n[1] * math.cos(a) + u[1] * math.sin(a))


def open_hand(cv, glow, wrist, u, front, depth, aimed):
    """A huge open stone hand off the wrist. Aimed: the palm faces along the arm `u` (the ray's way), four fingers spread
    up across it (towards n, turned to the arm's upper side), the thumb forward and down; a glowing rune slit on the palm's
    face (near plane). Hanging: the palm down the arm, three fingers spread down, the thumb on the `front` side. Returns
    the palm's centre and where the ray leaves it."""
    n = (-u[1], u[0])                                # the arm's upper side (up for an arm pointed forward)
    palm = (wrist[0] + u[0] * PALM_OFF, wrist[1] + u[1] * PALM_OFF)
    turn = math.degrees(math.atan2(u[1], u[0]))
    xf = Xf.pose(turn, (0.0, 0.0), palm)             # local x along the arm, local y across it
    if aimed:
        shade = flat(2, bevel=False) if depth else dome(-1.4, -2.0, 5.2, lo=JADE_LO, hi=JADE_HI + 1, fixed=True)
        inner = cv.part(xf, Ellipse(0.0, 0.0, PALM_DEPTH, PALM_SPAN), "emerald", shade, rust=0.0)
        for (t, fan, ln) in AIM_FINGERS:
            base = (palm[0] + n[0] * (PALM_SPAN - 1.2) + u[0] * t, palm[1] + n[1] * (PALM_SPAN - 1.2) + u[1] * t)
            d = rotate_towards(n, u, fan)
            limb(cv, base, (base[0] + d[0] * ln, base[1] + d[1] * ln), FINGER_R, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
        tb = (palm[0] - n[0] * PALM_SPAN * 0.35 + u[0] * PALM_DEPTH * 0.5, palm[1] - n[1] * PALM_SPAN * 0.35 + u[1] * PALM_DEPTH * 0.5)
        td = rotate_towards((-n[0], -n[1]), u, 55.0)
        limb(cv, tb, (tb[0] + td[0] * 4.4, tb[1] + td[1] * 4.4), FINGER_R, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
    else:
        shade = flat(2, bevel=False) if depth else dome(-1.8, -1.6, 5.0, lo=JADE_LO, hi=JADE_HI + 1, fixed=True)
        inner = cv.part(xf, Ellipse(0.0, 0.0, HANG_LEN, HANG_SPAN), "emerald", shade, rust=0.0)
        across = (front[0] - u[0] * (front[0] * u[0] + front[1] * u[1]), front[1] - u[1] * (front[0] * u[0] + front[1] * u[1]))
        la = math.hypot(*across) or 1.0
        across = (across[0] / la, across[1] / la)    # the hand's front, square to the arm
        for (t, fan, ln) in HANG_FINGERS:
            base = (palm[0] + u[0] * (HANG_LEN - 1.0) + across[0] * t, palm[1] + u[1] * (HANG_LEN - 1.0) + across[1] * t)
            d = rotate_towards(u, across, fan)
            limb(cv, base, (base[0] + d[0] * ln, base[1] + d[1] * ln), FINGER_R, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
        tb = (palm[0] + across[0] * (HANG_SPAN - 0.8) - u[0] * 0.6, palm[1] + across[1] * (HANG_SPAN - 0.8) - u[1] * 0.6)
        td = rotate_towards(across, u, 40.0)
        limb(cv, tb, (tb[0] + td[0] * 4.0, tb[1] + td[1] * 4.0), FINGER_R, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
    if depth == 0:
        limb_mottle(cv, inner, wrist, palm, 23)
        if aimed:                                    # the rune slit on the palm's face, where the ray comes out
            for t, col in ((-1.8, JD[5]), (-0.6, WHITE), (0.6, WHITE), (1.8, JD[5])):
                q = P(Xf(), (palm[0] + u[0] * (PALM_DEPTH - 0.6) + n[0] * t, palm[1] + u[1] * (PALM_DEPTH - 0.6) + n[1] * t))
                cv.put_glow(q[0], q[1], col)
                glow.put_glow(q[0], q[1], col)
        else:                                        # a rune in the palm, dimly glowing
            q = P(Xf(), (palm[0] + across[0] * 0.4, palm[1] + across[1] * 0.4))
            cv.put_glow(q[0], q[1], JD[5])
            glow.put_glow(q[0], q[1], JD[5])
    muzzle = (palm[0] + u[0] * PALM_FRONT, palm[1] + u[1] * PALM_FRONT)
    return palm, muzzle


def arm(cv, glow, shoulder, depth, hand_off=(0.0, 0.0), aim=None):
    """A long stone arm from the shoulder: hanging (the open hand by the knee, swung by `hand_off`) or pointed `aim`
    degrees below forward, palm out. Returns the palm's centre and where the ray leaves it (the palm's face)."""
    sx, sy = shoulder
    if aim is None:                                  # v3: in profile, both arms hang a little forward, elbows back
        rest = (sx - 3.0 + hand_off[0], sy + 20.4 + hand_off[1])
        elbow, wrist = ik(shoulder, rest, UPPER, FORE, 1)
        u = (wrist[0] - elbow[0], wrist[1] - elbow[1])
        ln = math.hypot(*u) or 1.0
        u = (u[0] / ln, u[1] / ln)
        front = (-1.0, 0.0)
    else:
        a = math.radians(aim)
        u = (-math.cos(a), math.sin(a))              # facing left: forward is -x
        elbow = (sx + u[0] * UPPER, sy + u[1] * UPPER)
        wrist = (elbow[0] + u[0] * FORE, elbow[1] + u[1] * FORE)
        front = u
    upper = limb(cv, shoulder, elbow, 4.8, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
    fore = limb(cv, elbow, wrist, 5.8, "emerald", depth, lo=JADE_LO, hi=JADE_HI)
    if depth == 0:
        limb_mottle(cv, upper, shoulder, elbow, 17)
        limb_mottle(cv, fore, elbow, wrist, 19)
        limb_rings(cv, upper, shoulder, elbow, offset=2.0)
        limb_rings(cv, fore, elbow, wrist, spacing=3.2)
    # the stone band round the wrist, its runes glowing (v3: the reference's rune bands; near arm only: a far rune would
    # flicker, D4 rule 17)
    b0 = (wrist[0] - u[0] * 4.6, wrist[1] - u[1] * 4.6)
    b1 = (wrist[0] - u[0] * 1.8, wrist[1] - u[1] * 1.8)
    limb(cv, b0, b1, 6.4, "frog", depth, lo=1, hi=4)
    if depth == 0:
        n = (-u[1], u[0])
        mb = ((b0[0] + b1[0]) * 0.5, (b0[1] + b1[1]) * 0.5)
        for t, col in ((-2.6, JD[5]), (-0.8, WHITE), (1.0, JD[5]), (2.8, JD[5])):
            q = P(Xf(), (mb[0] + n[0] * t, mb[1] + n[1] * t))
            cv.put_glow(q[0], q[1], col)
            glow.put_glow(q[0], q[1], col)
    palm, muzzle = open_hand(cv, glow, wrist, u, front, depth, aim is not None)   # the hand over the bracelet's end
    return palm, muzzle


def boulder(cv, at, depth, seed_crack=None):
    """A shoulder boulder in its own space, placed by whole pixels (its marks ride with it, D4 rule 17)."""
    ox, oy = int(round(at[0])), int(round(at[1]))
    xf = Xf.pose(0.0, (0.0, 0.0), (ox, oy))
    shade = flat(2, bevel=False) if depth else dome(-2.0, -3.0, 7.0, lo=JADE_LO, hi=JADE_HI, gain=1.3, fixed=True)
    inner = cv.part(xf, Ellipse(0.0, 0.0, 6.4, 5.6), "emerald", shade, rust=0.0)
    if depth == 0:
        mottle(cv, inner, ox, oy, 7)
        for (dx, dy, c) in ((-3, -3, JD[5]), (-2, -3, JD[4]), (-3, -2, JD[4]), (1, 1, JD[1]), (2, 2, JD[1]), (2, 1, JD[3])):
            q = P(xf, (dx + 0.5, dy + 0.5))
            if q in inner:
                cv.put(q[0], q[1], c)
    return inner


def body(mid, glow, p):
    """The middle plane in the body's own space, placed by one whole-pixel translation (D4 rule 17). v3: in profile."""
    oy = p.bob
    bx = Xf.pose(0.0, (0.0, 0.0), (0.0, oy))

    def at(x, y):
        return P(bx, (x, y))
    # the torso: the chest bulging forward, the hump behind, the waist under them, carved into plates
    torso = Union(Ellipse(*CHEST), Ellipse(*BACK), Poly(WAIST))
    shade = stone_plates(dome(CHEST[0] - 4.5, CHEST[1] - 6.5, 18.0, lo=JADE_LO, hi=JADE_HI, gain=1.3, bias=0.15, fixed=True), PLATE, 3)
    tin = mid.part(bx, torso, "emerald", shade, shadow=(1, 1), rust=0.0)
    mottle(mid, tin, 0, oy, 3, density=0.26)
    for chain in VEINS:
        for (x, y) in chain:
            q = at(x + 0.5, y + 0.5)
            if q in tin and mid.px.get(q) != JD[0]:
                mid.put(q[0], q[1], JD[4])
    for chain in CRACKS:
        for (x, y) in chain:
            q = at(x + 0.5, y + 0.5)
            if q in tin:
                mid.put(q[0], q[1], JD[0])
                if (q[0] + 1, q[1]) in tin:
                    mid.put(q[0] + 1, q[1], JD[3])
    # the skirt: three leaves of rough stone hanging from the belt over the hips, each split from the next by a seam
    for k, pts in enumerate(([(-12.2, -21.4), (-5.2, -21.4), (-5.8, -17.0), (-8.4, -13.0), (-11.6, -16.6)],
                             [(-5.6, -21.4), (2.2, -21.4), (1.6, -16.4), (-1.6, -12.4), (-5.2, -16.2)],
                             [(1.8, -21.4), (10.6, -21.4), (9.8, -17.2), (6.4, -13.6), (2.6, -16.8)])):
        mid.part(bx, Poly(pts), "frog", face((-0.4, -0.5, 0.75), lo=2 + (k == 1), hi=5, ramp_len=8, fixed=True), rust=0.0)
    # (each leaf pointed, as the reference's skirt of stone leaves)
    # the bronze belt over the waist's bottom, its rivets, and the disc in front that holds his core
    belt = mid.part(bx, box(-12.0, -25.0, 11.4, -21.0), "gilt", face((-0.4, -0.7, 0.65), lo=3, hi=7, ramp_len=10, fixed=True), rust=0.0)
    ry = at(0.0, -23.0)[1]
    for (x, y) in belt:
        if y == ry and x % 4 == 0:
            mid.put(x, y, G[9])                       # rivets
            if (x + 1, y + 1) in belt:
                mid.put(x + 1, y + 1, G[2])
    mid.part(bx, Ellipse(-12.6, -23.0, 2.6, 3.4), "gilt", dome(-13.4, -24.4, 3.4, lo=3, hi=8, gain=1.4, fixed=True), rust=0.0)
    # the crystals on his back
    for (bxx, byy, h, w, lean) in CRYSTALS:
        cin = mid.part(bx, Poly([(bxx - w, byy), (bxx + lean, byy - h), (bxx + w, byy)]), "emerald",
                       face((-0.6, -0.5, 0.6), lo=3, hi=5, ramp_len=7, gain=1.35, fixed=True), rust=0.0)
        for (x, y) in cin:
            ly = y - oy + 0.5
            axis = bxx + lean * (byy - ly) / h
            if x + 0.5 > axis + 0.4:
                mid.put(x, y, JD[2])                  # the shadowed facet
            elif x + 0.5 > axis - 0.8:
                mid.put(x, y, JD[6])                  # the ridge catching the light
    return ((SHOULDER_NEAR[0], SHOULDER_NEAR[1] + oy), (SHOULDER_FAR[0], SHOULDER_FAR[1] + oy))


def aim_dir(deg):
    a = math.radians(deg)
    return (-math.cos(a), math.sin(a))


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    leg(mid, (HIP_NEAR[0], HIP_NEAR[1] + p.bob), p.near_foot, 0)
    sh_near, sh_far = body(mid, glow, p)
    leg(far, (HIP_FAR[0], HIP_FAR[1] + p.bob), p.far_foot, 1)
    arm(far, glow, sh_far, 1, hand_off=p.far_hand)
    muzzle = None
    if p.aim != "body":                              # the aiming stance's near arm is the arm sheet's (arm_frame)
        _, muzzle = arm(near, glow, sh_near, 0, hand_off=p.near_hand, aim=p.aim)
    boulder(near, (sh_near[0], sh_near[1] - 1.0), 0)
    for cv in (far, mid, near):
        finish(cv)
    hx, hy = P(Xf(), (HEAD_AT[0], HEAD_AT[1] + p.bob))
    stamp_head(mid, glow, hx, hy)
    cx, cy = P(Xf(), (-15.0, -26.0 + p.bob))
    stamp_heart(mid, glow, cx, cy)                   # the core in the belt's disc
    return far, mid, near, glow, muzzle


# ------------------------------------------------------------------------------------------------------------------------
# Animation: the Jaeger's walk
# ------------------------------------------------------------------------------------------------------------------------
WALK = 16
WALK_STEP = 1.5                                      # 1x px a planted foot slides back per frame (= the root motion)
STRIDE = WALK_STEP * WALK / 2                        # 12 px a step
HALF = STRIDE / 2.0
LIFT = 5.0
FOOT_NEAR_X, FOOT_FAR_X = -1.6, 1.8                  # the feet's tracks (v3: in profile, one under the other)
ARM_SWING = 0.0                                      # 2026-11-09 (user): no arm swing in the walk (was 4.0)


def foot_cycle(f):
    """(x, lift) of a foot at walk frame f: planted for frames 0..8 sliding back WALK_STEP a frame (heel strike at -HALF
    on frame 0, toe-off at +HALF on frame 8), then swung forward through an arc."""
    f %= WALK
    half = WALK // 2
    if f <= half:
        return -HALF + WALK_STEP * f, 0.0
    t = (f - half) / half
    return HALF - STRIDE * t, LIFT * math.sin(math.pi * t)


def walk_pose(f):
    nx, nl = foot_cycle(f)
    fx, fl = foot_cycle(f + WALK // 2)
    phase = 2.0 * math.pi * f / WALK
    bob = -int(round(2.0 * abs(math.sin(phase))))    # lowest at each heel strike, up through mid-stance (whole px)
    swing = ARM_SWING * math.cos(phase)
    return Pose(bob=bob, near_foot=(FOOT_NEAR_X + nx, nl), far_foot=(FOOT_FAR_X + fx, fl),
                near_hand=(swing, -abs(swing) * 0.4), far_hand=(-swing, -abs(swing) * 0.4))


def idle_pose(k):
    breathe = (0, -1, -1, 0)[k]
    return Pose(bob=breathe, near_foot=(FOOT_NEAR_X - 4.0, 0.0), far_foot=(FOOT_FAR_X + 3.6, 0.0), near_hand=(0.6, breathe * 0.5),
                far_hand=(1.4, breathe * 0.5))


STANCE = dict(near_foot=(FOOT_NEAR_X - 5.0, 0.0), far_foot=(FOOT_FAR_X + 4.6, 0.0), far_hand=(3.0, -1.0))
FRAMES = ([("Walk%d" % k, walk_pose(k)) for k in range(WALK)]
          + [("Idle%d" % k, idle_pose(k)) for k in range(4)]
          + [("Aim", Pose(aim="body", **STANCE))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


def arm_frame(k):
    """Aim frame k: the near arm alone (the arm sheet, drawn between the middle plane and the near boulder), pointed
    AIM_MIN + k x AIM_STEP degrees below forward from the braced stance's shoulder; its canvas, its glow and the muzzle."""
    near, glow = Canvas(), Canvas()
    _, muzzle = arm(near, glow, SHOULDER_NEAR, 0, aim=AIM_MIN + AIM_STEP * k)
    finish(near)
    return near, glow, muzzle


# ------------------------------------------------------------------------------------------------------------------------
# The ray: electric nodes (drawn unrotated along the beam in game, D4 rule 14) and the charge gathering in the fist
# ------------------------------------------------------------------------------------------------------------------------
NODES = [["........",
          "...v....",
          "..vwv.v.",
          ".vwXwvw.",
          "..wXXwv.",
          ".vwwXv..",
          "..v.vv..",
          "........"],
         ["........",
          ".v...v..",
          "..vwvw..",
          "..wXXwv.",
          ".vwXXw..",
          "..vwwv..",
          "...v..v.",
          "........"],
         ["........",
          "....v...",
          ".v.vwv..",
          "..wXXwv.",
          ".vwXXwv.",
          "..vwXv..",
          "..v..v..",
          "........"]]
NODE_COL = {"u": JD[3], "v": JD[4], "w": JD[5], "X": WHITE}
ORB_CELL, ORB_SIZES = 12, (1.6, 2.4, 3.2, 4.2, 5.2)


def node_image(rows):
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), NODE_COL[ch] + (255,))
    return im


def orb_image(r):
    """The charge in the fist: a white core in jade rings, a few sparks round it (crisp pixels, no blending)."""
    im = Image.new("RGBA", (ORB_CELL, ORB_CELL), (0, 0, 0, 0))
    c = (ORB_CELL - 1) / 2.0
    for y in range(ORB_CELL):
        for x in range(ORB_CELL):
            d = math.hypot(x - c, y - c)
            col = None
            if d <= r * 0.45:
                col = WHITE
            elif d <= r * 0.75:
                col = JD[5]
            elif d <= r:
                col = JD[4]
            elif d <= r + 1.2 and r > 2.0 and (x * 7 + y * 13) % 5 == 0:
                col = JD[3]
            if col:
                im.putpixel((x, y), col + (255,))
    return im


def sheet(images, pad=1):
    w, h = images[0].size
    out = Image.new("RGBA", (w, (h + pad) * len(images) - pad), (0, 0, 0, 0))
    for k, im in enumerate(images):
        out.alpha_composite(im, (0, k * (h + pad)))
    return out


def export_ray():
    export(sheet([node_image(n) for n in NODES]), OUT + "Projectiles/JadeRay.png")
    export(sheet([orb_image(r) for r in ORB_SIZES]), OUT + "Projectiles/JadeRay_Orb.png")


# ------------------------------------------------------------------------------------------------------------------------
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    head_cv = Canvas()
    stamp_head(head_cv, Canvas(), 0, 0)
    hand = Canvas()
    arm(hand, Canvas(), (-6.0, -20.0), 0)
    finish(hand)
    hand_px = {q: c for q, c in hand.px.items() if q[1] >= -6}
    heart = Canvas()
    stamp_heart(heart, Canvas(), 0, 0)
    crystal = Canvas()
    crystal.part(Xf(), Poly([(-2.4, 0.0), (1.0, -8.0), (2.4, 0.0)]), "emerald", face((-0.6, -0.5, 0.6), lo=3, hi=5, ramp_len=6, fixed=True),
                 rust=0.0)
    finish(crystal)
    return {"JadeGolem_GoreHead": crop(head_cv.px), "JadeGolem_GoreHand": crop(hand_px), "JadeGolem_GoreHeart": crop(heart.px),
            "JadeGolem_GoreCrystal": crop(crystal.px)}


def write_rig(path, cell, acell, muzzles):
    w, h, ox, oy = cell
    aw, ah, aox, aoy = acell
    mx = ", ".join(str(round(m[0] * 2)) for m in muzzles)
    my = ", ".join(str(round(m[1] * 2)) for m in muzzles)
    T = "\t"
    L = ["// <auto-generated> by art/coghaven/make_jade_golem_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.NPCs",
         "{",
         T + "/// <summary>The Jade Golem's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells in",
         T + "/// Columns columns, 2 px between them; the origin is the ground point under his hips. Each sequence is Name .. Name +",
         T + "/// NameFrames - 1. While he aims, the body is frame AimBody and the near arm comes from the arm sheets (_Arm, _ArmGlow):",
         T + "/// arm frame k points it ArmMinDegrees + k x ArmStepDegrees below forward (-90 straight up), drawn over the middle",
         T + "/// plane and under the near one.</summary>",
         T + "public static class JadeGolemRigData",
         T + "{",
         T * 2 + "public const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
         % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
         T * 2 + "public const int Walk = 0, WalkFrames = %d, Idle = %d, IdleFrames = 4, AimBody = %d;" % (WALK, INDEX["Idle0"], INDEX["Aim"]),
         T * 2 + "public const int ArmFrames = %d, ArmMinDegrees = %d, ArmStepDegrees = %d, ArmColumns = %d;"
         % (AIM_FRAMES, AIM_MIN, AIM_STEP, ARM_COLUMNS),
         T * 2 + "/// <summary>The arm sheets' cells: the arm's reach only; their origin is the same ground point (below the cell).</summary>",
         T * 2 + "public const int ArmCellWidth = %d, ArmCellHeight = %d, ArmOriginX = %d, ArmOriginY = %d;" % (aw * 2, ah * 2, aox * 2, aoy * 2),
         T * 2 + "/// <summary>The near shoulder, game px from the origin (left-facing): the aim is measured from here.</summary>",
         T * 2 + "public const int ShoulderX = %d, ShoulderY = %d;" % (round(SHOULDER_NEAR[0] * 2), round(SHOULDER_NEAR[1] * 2)),
         T * 2 + "/// <summary>Game px from the shoulder, along the arm, to where the ray leaves the open palm (every angle).</summary>",
         T * 2 + "public const float PalmReach = %.1ff;" % (PALM_REACH * 2),
         T * 2 + "/// <summary>Game px a planted foot slides back per walk frame: the walk frame advances with this much distance",
         T * 2 + "/// walked, so the planted foot never slips (the Jaeger's root motion).</summary>",
         T * 2 + "public const int WalkStep = %d;" % round(WALK_STEP * 2),
         T * 2 + "/// <summary>Where the ray leaves the palm in each arm frame, game px from the origin (left-facing).</summary>",
         T * 2 + "public static readonly int[] MuzzleX = { %s };" % mx,
         T * 2 + "public static readonly int[] MuzzleY = { %s };" % my,
         T + "}",
         "}"]
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def grid_cols(canvases, cell, glow=False):
    """Equal cells in COLUMNS columns, left to right, then down, 1 px (2 px in game) between them."""
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", (w * COLUMNS + COLUMNS - 1, (h + 1) * rows - 1), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        bx, by = (k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)
        for (x, y), col in (cv.glow if glow else cv.px).items():
            if y >= GROUND_CLIP:
                continue
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[bx + cx, by + cy] = col + (255,)
    return out


def arm_cell(arms):
    """The arm sheet's cell (1x width, height, origin x, origin y): just the arm's reach, the origin still the ground point
    under the hips (it lies below the cell), so the same anchor places it."""
    xs = [x for (cv, g, _) in arms for (x, y) in list(cv.px) + list(g.px)]
    ys = [y for (cv, g, _) in arms for (x, y) in list(cv.px) + list(g.px)]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    return (x1 - x0 + 1, y1 - y0 + 1, -x0, -y0)


def grid_n(canvases, cell, columns, glow=False):
    """Equal cells in `columns` columns (1 px, 2 px in game, between them); every pixel must fit in its cell."""
    w, h, ox, oy = cell
    rows = (len(canvases) + columns - 1) // columns
    out = Image.new("RGBA", (w * columns + columns - 1, (h + 1) * rows - 1), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        bx, by = (k % columns) * (w + 1), (k // columns) * (h + 1)
        for (x, y), col in (cv.glow if glow else cv.px).items():
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of arm frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[bx + cx, by + cy] = col + (255,)
    return out


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_cols([fr[idx] for fr in frames], cell), OUT + "NPCs/JadeGolem%s.png" % suffix)
    export(grid_cols([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/JadeGolem_Glow.png")
    arms = [arm_frame(k) for k in range(AIM_FRAMES)]
    acell = arm_cell(arms)
    export(grid_n([a[0] for a in arms], acell, ARM_COLUMNS), OUT + "NPCs/JadeGolem_Arm.png")
    export(grid_n([a[1] for a in arms], acell, ARM_COLUMNS, glow=True), OUT + "NPCs/JadeGolem_ArmGlow.png")
    write_rig(OUT + "NPCs/JadeGolemRigData.cs", cell, acell, [a[2] for a in arms])
    stale = os.path.join(ROOT, OUT + "Gores/JadeGolem_GoreFist.png")
    if os.path.exists(stale):
        os.remove(stale)                             # the fist's gore: the hands are open since 2026-11-10b
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")
    export_ray()


def render(p, cw, ch, ox, oy, arm_k=None):
    """A frame composed as the game draws it: far, middle, (the aiming arm), near, glow."""
    far, mid, near, glow, _ = frame(p)
    layers = [far, mid]
    if arm_k is not None:
        a, ag, _ = arm_frame(arm_k)
        layers += [a, ag]
    layers += [near, glow]
    t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    for cv in layers:
        t.alpha_composite(to_image(cv.px, -ox, -oy, cw, ch))
    return t


def preview(path, names=None, scale=4):
    cw, ch = 100, 80
    chosen = [(n, p, None) for (n, p) in FRAMES if names is None or n in names]
    for n in (names or ()):                          # "Arm<k>": the aim body with arm frame k
        if n.startswith("Arm"):
            chosen.append((n, FRAMES[INDEX["Aim"]][1], int(n[3:])))
    cols = min(6, len(chosen))
    rows = (len(chosen) + cols - 1) // cols
    sheet_im = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 0))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k, (n, p, ak) in enumerate(chosen):
            tile.alpha_composite(render(p, cw, ch, cw // 2 + 6, ch - 3, ak), ((k % cols) * cw, (k // cols) * ch))
        sheet_im.paste(tile, (0, half * ch * rows))
    sheet_im.resize((sheet_im.width * scale, sheet_im.height * scale), Image.NEAREST).save(path)
    print("preview", path)


def walk_gif(path):
    """The walk cycle in place over a ground line, the frame advanced with the distance walked (the root motion), 4x."""
    cw, ch = 100, 80
    frames = []
    for k in range(WALK * 2):
        im = Image.new("RGBA", (cw, ch), (150, 180, 210, 255))
        for x in range(cw):
            for y in range(ch - 3, ch):
                im.putpixel((x, y), (96, 84, 66, 255))
        im.alpha_composite(render(walk_pose(k % WALK), cw, ch, cw // 2 + 6, ch - 3))
        frames.append(im.resize((cw * 4, ch * 4), Image.NEAREST).convert("RGB"))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=70, loop=0)
    print("walk gif", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames", help="comma-separated frame names for a close-up preview")
    ap.add_argument("--walk-gif")
    a = ap.parse_args()
    if a.walk_gif:
        walk_gif(a.walk_gif)
    elif a.preview:
        preview(a.preview, a.frames.split(",") if a.frames else None, 6 if a.frames else 3)
    else:
        export_all()
