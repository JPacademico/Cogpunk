"""Source for Jadey, a Molda-Jade, Coghaven's boss (D4), and her small sprites. Run from the repo root:

    python -P art/bosses/jadey/make_jadey_art.py [--preview FILE] [--frames Idle0,Whip3,...]

Design (user, 2026-11-16: "The boss should be called 'Jadey, a molda-jade' a panda jademancer (inspiration for design on
image of the prompt)"; the reference: a panda woman with black hair streaked purple in a top knot, a green-and-black outfit
with gilt rope ties and green leg wraps, a green jade crystal in hand, lounging on a rock; "she should float";
"ensure quality pixel art and color density, also smooth frame animation for the boss"). My calls on the details: she
sits cross-legged on a crimson silk cushion with gilt tassels that floats on jade light; a big round panda head (white fur,
black eye patches round bright jade eyes, black ears), black hair with bangs and a top knot pinned with jade, a purple
streak down her bangs, a gilt circlet with a jade gem on her brow (her lasers leave it); a sleeveless jade qipao top with a
high collar, gilt trim and three gilt frog buttons down her axis, a crimson sash knotted at her side; black panda arms and
legs, jade wraps with gilt bands round her shins; her weapon a rope dart: a jade blade on a crimson silk cord with gilt
beads, coiled in her near paw (the game draws it when it spins and flies).

Three-quarter view facing left (D4 rule 13), the torso facing the screen and symmetric about its axis (2026-11-06), lit from
the top-left. Three planes (grid sheets drawn with DepthLayers.DrawCell): far (her far arm, one ramp step darker), middle
(cushion, legs, body, head), near (her near arm and its coil). The far arm has its own frames: each body frame's own far
arm, then the coin flick (FlickN), drawn instead of the frame's own when she flicks a coin while that arm rests (the game
picks: JadeyRigData.FlickOk). Stable pixels (D4 rule 17): the body never moves inside a frame set (the float's bob is in
code), parts are lit in their own space, hair strands and tassels sway by whole pixels.

Frames (in-betweens everywhere, no pose snaps): Idle x6, Whip x6 (raise, raise, spin, spin, throw, recover), Zone x6
(rise, rise, high, high, slam, recover), Channel x4 (spread, spread, glow, glow), Laser x4 (to the brow, focus, fire,
recover), Intro x4 (eyes shut, half, open, the smirk), Death x8 (jade creeps up her from the cushion over five frames, a
statue, cracks, cracks), Flick x4 (far arm only: cock, flick, follow, settle).

Outputs (1x art, exported 2x nearest-neighbour):
    Content/Bosses/Jadey/Jadey.png, _Far.png, _Near.png, _Glow.png    grid sheets (Columns wide)
    Content/Bosses/Jadey/JadeyRigData.cs                              cells, frame indices, hitbox, points per frame
    Content/Bosses/Jadey/Jadey_Head_Boss.png                          the map / boss bar head
    Content/Bosses/Jadey/Projectiles/JadeyRopeDart.png               the dart's blade, 16 headings (no runtime rotation)
    Content/Bosses/Jadey/Projectiles/JadeyRopeDart_Cord.png          a cord link
    Content/Bosses/Jadey/Projectiles/JadeCoin.png                    the coin spinning, 6 frames, and its _Glow
    Content/Bosses/Jadey/Projectiles/JadeCursedGround.png            the curse on three tiles, 4 flickers (and _Glow)
    Content/Bosses/Jadey/Projectiles/JadePetrifyZone.png             the zone's glyph ring piece, 4 flickers (and _Glow)
    Content/Bosses/Jadey/Items/JadeyBag.png                          her treasure bag
    Content/Bosses/Jadey/Gores/Jadey_Gore*.png                       jade shards of her statue
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
from westbots import (RAMP, Xf, Poly, Ellipse, Capsule, Union, Canvas, flat, dome, face, P, finish, limb, texture)  # noqa: E402
from rig import ik, COLOR_INDEX  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
sys.path.insert(0, HERE)
import jadey_sculpt  # noqa: E402  (2026-11-23: her body, sculpted)

ROOT = os.getcwd()
OUT = "Content/Bosses/Jadey/"
ST, IV, GH, VD, G, K, AE = (RAMP[k] for k in ("steel", "ivory", "ghost", "verd", "gilt", "crimson", "aether"))

CX = 0.0
GROUND_CLIP = 4                                   # rows under the origin that are still part of the sprite (the glow ring)
SH_NEAR, SH_FAR = (CX - 15.0, -24.6), (CX + 15.0, -24.6)    # 2026-11-18: out at her sides, mirror-symmetric (no lean on a turn)
ARM_OUT = 5.4                                     # every hand pose moves out with the shoulders (2026-11-17; +3 2026-11-18)
UPPER, FORE = 6.2, 6.0
HEAD_C = (CX, -36.8)                              # 2026-11-18: on the axis (was -0.6)
GEM = (CX - 0.4, -41.6)                           # the brow gem's centre (its pixels are stamped)
REST_NEAR, REST_FAR = (CX - 13.2, -14.6), (CX + 13.2, -14.6)     # mirror-symmetric (2026-11-18)


class Pose:
    def __init__(self, near=REST_NEAR, far=REST_FAR, sway=0, eyes=1, mouth=0, gem=0, coil=True, palms=0, jade=0.0, cracks=0,
                 hand_glow=0, far_glow=0):
        self.near, self.far = near, far
        self.sway = sway                          # -1/0/1: hair strands, tassels and the dangling dart swing by whole pixels
        self.eyes = eyes                          # 0 shut, 1 open, 2 glowing (the channel), 3 half
        self.mouth = mouth                        # 0 calm, 1 smirk, 2 open (a cry)
        self.gem = gem                            # 0..2: the brow gem's glow
        self.coil = coil                          # the rope dart coiled in the near paw (False while it spins or flies)
        self.palms = palms                        # 0 paws closed, 1 open palms (casting)
        self.jade = jade                          # 0..1: how far up her the death's jade has crept
        self.cracks = cracks                      # 0..2: the statue's cracks
        self.hand_glow = hand_glow                # 0..2: jade light in the near paw
        self.far_glow = far_glow                  # 0..2: in the far paw


# --- the cushion and the float ----------------------------------------------------------------------------------------------
def cushion(mid, glow, p):
    """A plump crimson silk cushion (lit from the top-left in its own space, its top face a step brighter), a gilt seam piped
    round its middle, gilt-capped tassels at its corners swinging with `sway`; jade light under it (glow only: the float)."""
    shape = Union(Ellipse(CX, -4.0, 18.6, 4.6), Ellipse(CX, -2.6, 17.2, 3.6))       # 2026-11-17: under a rounder body
    inner = mid.part(Xf(), shape, "crimson", texture(dome(CX - 6.0, -8.0, 15.0, lo=1, hi=4, gain=1.55, fixed=True, dither=0.16),
                                                      "weave", seed=51), shadow=(1, 1), rust=0.0)
    for x in range(-18, 19):                                   # the piped seam round its middle, catching the light on the left
        q = (x, -3)
        if q in inner:
            mid.put(x, -3, G[7] if x < -5 else G[5] if x < 6 else G[3])
            if (x, -2) in inner:
                mid.put(x, -2, K[1])
    for side in (-1, 1):
        tx = int(CX + side * 18.4) - (1 if side > 0 else 0)
        for (dx, dy, col) in ((0, -5, G[8] if side < 0 else G[6]), (0, -4, G[6] if side < 0 else G[4]), (side, -4, G[3]),
                              (0, -3, G[2])):
            mid.put(tx + dx, dy, col)
        for k in range(4):                                     # the tassel's threads, swinging
            x = tx + (p.sway * side if k >= 2 else 0)
            mid.put(x, -2 + k, K[4] if k < 2 else K[3] if k < 3 else K[2])
    for x in range(-16, 17):                                   # the float: a ring of jade light under the cushion
        y = 2 if abs(x) < 13 else 1
        col = GH[4] if (x + p.sway * 2) % 4 == 0 else GH[3]
        glow.put_glow(x, y, col)
        if abs(x) < 10:
            glow.put_glow(x, y + 1, GH[2] if (x + p.sway) % 2 else GH[3])
    return inner


# --- the legs, crossed --------------------------------------------------------------------------------------------------------
def legs(mid, p):
    """Black panda legs folded in the lotus over the cushion: one rounded mass (the thighs out to the knees, lit along its
    top), the two shins crossing in front in jade wraps between gilt bands (the near shin over the far), the soles' ivory
    pads turned up at the crossing."""
    lap = Poly([(CX - 16.8, -6.0), (CX - 15.6, -10.8), (CX - 10.0, -13.8), (CX + 10.0, -13.8), (CX + 15.4, -11.0), (CX + 16.6, -6.0),
                (CX + 10.6, -4.6), (CX - 10.6, -4.6)])
    inner = mid.part(Xf(), lap, "steel", texture(dome(CX - 5.0, -14.0, 14.0, lo=1, hi=4, gain=1.4, fixed=True, dither=0.16),
                                                  "brushed", seed=71, density=0.12), shadow=(1, 1), rust=0.0)
    shins = (((CX + 13.6, -8.4), (CX - 5.6, -6.4)), ((CX - 14.0, -8.6), (CX + 5.4, -6.8)))   # far shin first, near over it
    for k, (a, b) in enumerate(shins):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / ln, dy / ln
        nx, ny = -uy, ux
        for t in range(0, int(ln) + 1):
            for w in (-1.5, -0.5, 0.5, 1.5):
                q = P(Xf(), (a[0] + ux * t + nx * w, a[1] + uy * t + ny * w))
                if q not in inner:
                    continue
                band = t in (2, int(ln) - 3)
                if band:
                    col = G[7] if w < 0 else G[4]
                elif 2 < t < int(ln) - 3:
                    col = (GH[4] if w < -1 else GH[3] if w < 0.6 else GH[2]) if k == 1 else (GH[3] if w < -1 else GH[2] if w < 0.6 else GH[1])
                else:
                    continue
                mid.put(q[0], q[1], col)
    for (fx, fy, k) in ((CX + 5.6, -10.6, 0), (CX - 6.2, -10.2, 1)):   # the soles, turned up
        q = P(Xf(), (fx, fy))
        pads = ((0, 0, IV[4]), (1, 0, IV[3]), (0, 1, IV[3]), (1, 1, IV[2]), (-1, -1, IV[4]), (1, -1, IV[4]), (2, -1, IV[3]))
        for (dx, dy, col) in pads[:5 if k else 7]:
            mid.put(q[0] + dx, q[1] + dy, col)
    return inner


# --- the body -----------------------------------------------------------------------------------------------------------------
def torso(mid, p):
    """Black panda shoulders; a sleeveless jade qipao top tapering from a high collar to her waist, gilt trim, three gilt frog
    buttons on the axis, a jade flap over her lap edged in gilt; a crimson sash with a gilt knot at her near side."""
    mid.part(Xf(), Ellipse(CX, -25.2, 15.6, 4.6), "steel", dome(CX - 5.0, -28.0, 11.0, lo=1, hi=4, gain=1.4, fixed=True), rust=0.0)
    flap = Poly([(CX - 8.4, -16.4), (CX + 8.4, -16.4), (CX + 10.4, -11.6), (CX + 6.6, -9.4), (CX, -8.8), (CX - 6.6, -9.4),
                 (CX - 10.4, -11.6)])
    fl = mid.part(Xf(), flap, "ghost", texture(face((-0.4, -0.3, 0.86), lo=1, hi=3, ramp_len=6, gain=1.4, fixed=True, dither=0.14),
                                               "weave", seed=59), shadow=(1, 1), rust=0.0)
    for (x, y) in list(fl):
        if y >= max(yy for (xx, yy) in fl if xx == x) - 0:
            mid.put(x, y, G[6] if x < CX else G[4])            # its gilt hem
    top = Poly([(CX - 6.2, -29.6), (CX + 6.2, -29.6), (CX + 11.4, -27.0), (CX + 13.6, -23.0), (CX + 14.0, -19.6), (CX + 13.0, -16.4),
                (CX + 10.6, -14.6), (CX - 10.6, -14.6), (CX - 13.0, -16.4), (CX - 14.0, -19.6), (CX - 13.6, -23.0), (CX - 11.4, -27.0)])
    inner = mid.part(Xf(), top, "ghost", texture(dome(CX - 5.0, -26.0, 15.0, lo=1, hi=4, gain=1.6, bias=-0.1, fixed=True,
                                                       dither=0.18), "weave", seed=57), shadow=(1, 1), rust=0.0)
    for (x, y) in list(inner):                                 # verdigris mottle in the silk (one shade, part space)
        if ((x * 7 + y * 13) % 11 == 0) and mid.px.get((x, y)) in (GH[2], GH[3]):
            mid.put(x, y, VD[2] if mid.px[(x, y)] == GH[3] else VD[1])
    for (x, y) in list(inner):                                 # gilt piping down the armholes
        if (x - 1, y) not in inner and (x - 1, y) in mid.px and y > -27 and x < CX:
            mid.put(x, y, G[6])
        if (x + 1, y) not in inner and (x + 1, y) in mid.px and y > -27 and x > CX:
            mid.put(x, y, G[4])
    collar = Poly([(CX - 3.4, -30.6), (CX + 3.4, -30.6), (CX + 4.0, -27.6), (CX - 4.0, -27.6)])
    cl = mid.part(Xf(), collar, "ghost", face((-0.4, -0.6, 0.7), lo=2, hi=4, ramp_len=6, fixed=True), rust=0.0)
    for x in range(-4, 5):
        if (x, -28) in cl:
            mid.put(x, -28, G[7] if x < 0 else G[5])
    for y in (-26, -23, -20):                                  # frog buttons on the axis
        for (dx, dy, col) in ((-1, 0, G[8]), (0, 0, G[6]), (1, 0, G[4]), (0, 1, G[2])):
            mid.put(int(CX) + dx, y + dy, col)
    for x in range(-13, 14):                                   # a gilt cloud-scroll band over the sash
        q = (x, -19)
        if q in inner:
            k = (x + 8) % 4
            mid.put(x, -19, (G[7], G[5], G[3], G[5])[k] if x < CX else (G[5], G[4], G[2], G[4])[k])
            if k == 0 and (x, -20) in inner:
                mid.put(x, -20, G[4] if x < CX else G[3])
    for x in range(-13, 14):                                   # the sash
        for (y, k) in ((-18, 4), (-17, 2)):
            if (x, y) in inner or (x, y) in mid.px:
                mid.put(x, y, K[k + (1 if x < -2 else 0)])
    knot = (int(CX) - 10, -17)
    for (dx, dy, col) in ((0, -1, G[8]), (-1, 0, G[7]), (0, 0, G[5]), (1, 0, G[4]), (0, 1, G[3]), (-1, 2, K[3]), (-1, 3, K[2]),
                          (1, 2, K[3]), (1, 3, K[2])):
        mid.put(knot[0] + dx, knot[1] + dy, col)
    return inner


# --- the head -----------------------------------------------------------------------------------------------------------------
def head(mid, glow, p):
    """A big round panda head: white fur (ivory, lit as a dome in its own space), chubby at the cheeks; round black ears;
    black hair, a cap with a parted fringe (the brow gem shows in the parting) and a top knot pinned with jade; a purple
    streak down the fringe on her near side. Eyes, patches, nose, mouth and the gem are stamped after the finish (small
    details: art-direction lesson of 2026-11-09)."""
    hx, hy = HEAD_C
    for (ex, ey) in ((hx - 8.0, hy - 7.4), (hx + 7.6, hy - 7.8)):   # ears, behind the head
        ear = mid.part(Xf(), Ellipse(ex, ey, 3.5, 3.2), "steel", dome(ex - 1.0, ey - 1.0, 4.0, lo=1, hi=4, fixed=True), rust=0.0)
        q = P(Xf(), (ex + 0.4, ey + 0.6))
        if q in ear:
            mid.put(q[0], q[1], ST[3])
    face_shape = Union(Ellipse(hx, hy - 0.6, 10.0, 8.4), Ellipse(hx, hy + 2.0, 10.8, 6.4))
    face_px = mid.part(Xf(), face_shape, "ivory", texture(dome(hx - 3.5, hy - 4.5, 11.5, lo=2, hi=5, gain=1.6, bias=-0.06, fixed=True, dither=0.2),
                                                          "speckle", seed=61, density=0.05), shadow=(1, 1), rust=0.0)
    cap = Poly([(hx - 9.8, hy - 2.6), (hx - 8.6, hy - 7.4), (hx - 4.0, hy - 10.2), (hx + 2.6, hy - 10.4), (hx + 8.4, hy - 7.6),
                (hx + 9.8, hy - 2.8), (hx + 7.8, hy - 5.0), (hx + 5.0, hy - 4.0), (hx + 2.4, hy - 5.4), (hx + 0.6, hy - 7.0),
                (hx - 2.4, hy - 7.0), (hx - 4.0, hy - 4.6), (hx - 6.6, hy - 5.4), (hx - 8.6, hy - 3.6)])
    hair = mid.part(Xf(), cap, "steel", texture(dome(hx - 3.0, hy - 10.0, 10.0, lo=1, hi=5, gain=1.45, fixed=True, dither=0.18), "brushed",
                                                seed=67, density=0.16), shadow=(1, 1), rust=0.0)
    bun = mid.part(Xf(), Ellipse(hx + 1.4, hy - 12.0, 3.6, 2.8), "steel", dome(hx + 0.2, hy - 13.2, 4.0, lo=1, hi=5, fixed=True), rust=0.0)
    for k in range(6):                                         # the jade hairpin through the bun, a bead at its end
        q = P(Xf(), (hx - 2.6 + k * 1.3, hy - 14.2 + k * 0.55))
        mid.put(q[0], q[1], GH[4] if k < 2 else GH[3])
    q = P(Xf(), (hx - 3.4, hy - 14.6))
    for (dx, dy, col) in ((0, 0, GH[5]), (-1, 0, GH[3]), (0, -1, GH[4]), (-1, -1, GH[2])):
        mid.put(q[0] + dx, q[1] + dy, col)
    for k in range(6):                                         # the purple streak down the fringe on her near side
        x = int(hx - 6.0 + k * 0.5)
        y = int(hy - 9.6 + k)
        for dx in (0, 1):
            if (x + dx, y) in hair:
                mid.put(x + dx, y, AE[2] if dx == 0 else AE[1])
    return face_px, hair


def stamp_face(mid, glow, p):
    """The small details, placed by hand after the finish: the eye patches (big black teardrops slanting out and down), the
    eyes in them (jade irises, a white glint; shut: a lid line), the nose, the mouth, the circlet and its jade gem."""
    hx, hy = int(round(HEAD_C[0])), int(round(HEAD_C[1]))
    near = [(x, -1) for x in range(-6, -2)] + [(x, 0) for x in range(-7, -2)] + [(x, 1) for x in range(-7, -2)] \
        + [(x, 2) for x in range(-7, -3)] + [(-6, 3), (-5, 3)]
    far = [(x, -1) for x in range(3, 6)] + [(x, 0) for x in range(3, 7)] + [(x, 1) for x in range(3, 7)] + [(x, 2) for x in range(4, 7)] \
        + [(5, 3), (6, 3)]
    for (dx, dy) in near + far:
        mid.put(hx + dx, hy + dy, ST[1] if dy < 2 else ST[0])
    eyes = ((-5, 0), (4, 0))
    for k, (ex, ey) in enumerate(eyes):
        x, y = hx + ex, hy + ey
        if p.eyes == 0:                                        # shut: a curved lid line
            mid.put(x - 1, y + 1, ST[3])
            mid.put(x, y + 1, ST[4])
            mid.put(x + 1, y + 1, ST[3])
            continue
        iris = (GH[4], GH[3]) if p.eyes != 2 else (GH[5], GH[4])
        mid.put_glow(x, y, iris[0])
        glow.put_glow(x, y, iris[0])
        mid.put_glow(x, y + 1, iris[1])
        glow.put_glow(x, y + 1, iris[1])
        if p.eyes != 3:
            mid.put_glow(x + 1, y + 1, iris[1])
            glow.put_glow(x + 1, y + 1, iris[1])
            mid.put(x + 1, y, IV[5])                           # the glint
        if p.eyes == 2:                                        # the channel: jade light spilling from the eyes
            for (dx, dy, col) in ((-1, 0, GH[3]), (2, 1, GH[3]), (0, -1, GH[4]), (1, 2, GH[3]), (-1, 1, GH[4])):
                mid.put_glow(x + dx, y + dy, col)
                glow.put_glow(x + dx, y + dy, col)
    for (dx, dy, col) in ((-2, 4, ST[0]), (-1, 4, ST[0]), (0, 4, ST[1]), (-1, 5, ST[0])):   # the nose
        mid.put(hx + dx, hy + dy, col)
    mouth = {0: ((-2, 7, ST[2]), (-1, 6, ST[1]), (0, 7, ST[2])),
             1: ((-3, 6, ST[2]), (-2, 7, ST[2]), (-1, 6, ST[1]), (0, 7, ST[2]), (1, 6, ST[2])),
             2: ((-2, 7, ST[1]), (-1, 7, K[2]), (0, 7, ST[1]), (-1, 6, ST[1]), (-1, 8, ST[1]))}[p.mouth]
    for (dx, dy, col) in mouth:
        mid.put(hx + dx, hy + dy, col)
    for (dx, dy) in ((-8, 4), (-7, 5), (6, 4), (7, 5)):        # blush on the cheeks
        q = (hx + dx, hy + dy)
        if q in mid.px and mid.px[q] in RAMP["ivory"]:
            mid.put(q[0], q[1], K[5])
    gx, gy = int(round(GEM[0])), int(round(GEM[1]))            # the circlet showing in the parting, the gem in its middle
    for dx in range(-3, 4):
        q = (gx + dx, gy + 1)
        if q in mid.px and mid.px[q] in RAMP["ivory"]:
            mid.put(q[0], q[1], G[6] if dx < 0 else G[4])
    gem_cols = ((GH[3], GH[4], GH[2]), (GH[4], GH[5], GH[3]), (GH[5], GH[5], GH[4]))[p.gem]
    for (dx, dy, k) in ((0, 0, 1), (-1, 0, 0), (1, 0, 2), (0, -1, 0), (0, 1, 2)):
        col = gem_cols[k]
        mid.put_glow(gx + dx, gy + dy, col)
        glow.put_glow(gx + dx, gy + dy, col)
    for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        mid.put(gx + dx, gy + dy, G[7] if dx < 0 else G[4])
    if p.gem >= 2:                                             # the gem flaring: a cross of light
        for (dx, dy) in ((-2, 0), (2, 0), (0, -2), (0, 2), (-3, 0), (3, 0)):
            col = GH[4] if abs(dx) + abs(dy) == 2 else GH[3]
            glow.put_glow(gx + dx, gy + dy, col)


# --- the arms -----------------------------------------------------------------------------------------------------------------
def arm(cv, glow, shoulder, hand, depth, bend, palms, light):
    """A black panda arm: a thick upper arm and forearm (steel), a jade cuff with a gilt band at the wrist, a round paw
    (open, its ivory pads out, when casting). light 1..2 puts jade light in the paw. Returns the paw's centre."""
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, bend)
    limb(cv, shoulder, elbow, 3.5, "steel", depth, lo=1, hi=4)
    limb(cv, elbow, wrist, 3.1, "steel", depth, lo=1, hi=4)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    cuff = (wrist[0] - u[0] * 1.2, wrist[1] - u[1] * 1.2)
    cf = cv.part(Xf(), Capsule((cuff[0] - u[0] * 0.8, cuff[1] - u[1] * 0.8), (cuff[0] + u[0] * 0.8, cuff[1] + u[1] * 0.8), 2.9),
                 "ghost", flat(2, bevel=False) if depth else flat(3), rust=0.0)
    if depth == 0:
        q = P(Xf(), cuff)
        if q in cf:
            cv.put(q[0], q[1], G[6])
    paw = (wrist[0] + u[0] * 1.2, wrist[1] + u[1] * 1.2)
    if depth > 0:
        cv.part(Xf(), Ellipse(paw[0], paw[1], 2.9, 2.7), "steel", flat(2, bevel=False), rust=0.0)
    else:
        pw = cv.part(Xf(), Ellipse(paw[0], paw[1], 3.0, 2.8), "steel", dome(paw[0] - 0.9, paw[1] - 0.9, 3.6, lo=1, hi=4, fixed=True), rust=0.0)
        if palms:                                              # open palm: the pads
            q = P(Xf(), (paw[0] + u[0] * 0.6, paw[1] + u[1] * 0.6))
            for (dx, dy, col) in ((0, 0, IV[3]), (1, 0, IV[2]), (-1, -1, IV[4]), (0, -1, IV[4]), (1, -1, IV[3])):
                if (q[0] + dx, q[1] + dy) in pw:
                    cv.put(q[0] + dx, q[1] + dy, col)
    if light:
        c = (paw[0] + u[0] * 2.2, paw[1] + u[1] * 2.2)
        rad = 1.6 + light * 0.8
        for y in range(int(c[1] - rad - 1), int(c[1] + rad + 2)):
            for x in range(int(c[0] - rad - 1), int(c[0] + rad + 2)):
                dd = math.hypot(x + 0.5 - c[0], y + 0.5 - c[1])
                if dd <= rad and (x, y) not in cv.px:
                    col = GH[5] if dd < rad * 0.4 else GH[4] if dd < rad * 0.75 else GH[3]
                    cv.put_glow(x, y, col)
                    glow.put_glow(x, y, col)
    return paw


def coil(near, paw, sway):
    """The rope dart at rest: a loop of crimson silk cord under the near paw, gilt beads on it, the jade blade hanging."""
    px, py = int(round(paw[0])), int(round(paw[1]))
    loop = ((0, 2), (-1, 3), (-2, 4), (-2, 5), (-1, 6), (0, 6), (1, 5), (1, 4), (1, 3))
    for k, (dx, dy) in enumerate(loop):
        near.put(px + dx, py + dy, K[4] if k % 3 else G[7])
        if (px + dx + 1, py + dy) not in near.px:
            near.put(px + dx + 1, py + dy, K[2])
    bx, by = px - 1 + sway, py + 7
    blade = ((0, 0, GH[0]), (0, 1, GH[4]), (1, 1, GH[0]), (-1, 1, GH[0]), (0, 2, GH[3]), (1, 2, GH[0]), (-1, 2, GH[0]), (0, 3, GH[2]),
             (0, 4, GH[0]))
    for (dx, dy, col) in blade:
        near.put(bx + dx, by + dy, col)


# --- a frame ------------------------------------------------------------------------------------------------------------------
def jade_over(cv, level, cracks, seed=0):
    """The death: her colours below a line rising from the cushion turn to jade, by lightness (each pixel's own shade:
    stable), the glow left alone; cracks are dark seams across the statue."""
    if level <= 0 and cracks <= 0:
        return
    if not cv.px:
        return
    y_top = min(y for (_, y) in cv.px)
    y_bot = max(y for (_, y) in cv.px)
    line = y_bot - (y_bot - y_top + 1) * level
    for (x, y), col in list(cv.px.items()):
        if (x, y) in cv.glow or y < line or col not in COLOR_INDEX:
            continue
        ramp, idx = COLOR_INDEX[col]
        n = len(RAMP[ramp])
        f = idx / max(1, n - 1)
        k = 0 if idx == 0 else max(1, min(5, int(round(1 + f * 4))))
        cv.put(x, y, GH[k] if (x * 5 + y * 3 + seed) % 7 else VD[max(0, min(3, k - 1))])
    if cracks:
        paths = (((-2, -44), (1, -38), (-1, -31), (2, -24), (0, -16)), ((6, -30), (9, -22), (7, -14), (11, -8)),
                 ((-9, -26), (-6, -19), (-10, -12), (-7, -6)))[:cracks + 1]
        for path in paths:
            for (a, b) in zip(path, path[1:]):
                steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
                for s in range(steps + 1):
                    x = int(round(a[0] + (b[0] - a[0]) * s / max(1, steps)))
                    y = int(round(a[1] + (b[1] - a[1]) * s / max(1, steps)))
                    if (x, y) in cv.px and (x, y) not in cv.glow:
                        cv.put(x, y, GH[0])
                        if (x + 1, y) in cv.px and (x + 1, y) not in cv.glow:
                            cv.put(x + 1, y, GH[4])


def frame(p, flick=None):
    """(far, mid, near, glow, points). `flick`: render only the far arm in that flick pose (the overlay frames).
    2026-11-23: her body is sculpted (jadey_sculpt.draw, the sprite-quality redesign); the old drawing functions above are
    kept for reference and for previous/make_jadey_art_2026-11-18.py."""
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    far_hand = flick if flick is not None else p.far
    far_hand = (far_hand[0] + ARM_OUT, far_hand[1])
    near_hand = (p.near[0] - ARM_OUT, p.near[1])
    near_paw, far_paw = jadey_sculpt.draw(far, mid, near, glow, p, far_hand, near_hand, only_far=flick is not None)
    if flick is not None:
        return far, Canvas(), Canvas(), glow, {"far": far_paw}
    if p.coil:
        coil(near, near_paw, p.sway)
    if p.jade > 0 or p.cracks:
        for cv in (far, mid, near):
            jade_over(cv, p.jade, p.cracks if cv is mid else 0)
    pts = {"near": near_paw, "far": far_paw, "gem": GEM, "eyes": (HEAD_C[0] - 0.5, HEAD_C[1])}
    return far, mid, near, glow, pts


IDLE_SWAY = (0, 1, 1, 0, -1, -1)
WHIP_RAISE = ((CX - 14.0, -22.0), (CX - 12.4, -33.0))
WHIP_SPIN = ((CX - 10.6, -45.2), (CX - 9.6, -44.0))
WHIP_THROW = (CX - 21.4, -30.0)
WHIP_RECOVER = (CX - 17.0, -22.0)
ZONE_RISE = (((CX - 15.0, -24.0), (CX + 14.6, -24.2)), ((CX - 13.6, -36.0), (CX + 13.2, -36.2)))
ZONE_HIGH = ((CX - 11.8, -45.0), (CX + 11.4, -45.2))
ZONE_SLAM = ((CX - 9.0, -18.6), (CX + 8.6, -18.8))
SPREAD = (((CX - 15.4, -22.0), (CX + 15.0, -22.2)), ((CX - 18.2, -27.0), (CX + 17.8, -27.2)))
LASER_HAND = ((CX - 9.0, -33.0), (CX - 5.6, -39.6))
FLICK = ((CX + 12.8, -16.4), (CX + 12.6, -18.4), (CX + 12.2, -21.0), (CX + 11.9, -23.6), (CX + 12.1, -21.8), (CX + 12.6, -18.2))

FRAMES = ([("Idle%d" % k, Pose(sway=IDLE_SWAY[k], eyes=1 if k != 4 else 3)) for k in range(6)]
          + [("Whip0", Pose(near=WHIP_RAISE[0], sway=1)),
             ("Whip1", Pose(near=WHIP_RAISE[1], sway=1, coil=False)),
             ("Whip2", Pose(near=WHIP_SPIN[0], sway=0, coil=False, mouth=1)),
             ("Whip3", Pose(near=WHIP_SPIN[1], sway=-1, coil=False, mouth=1)),
             ("Whip4", Pose(near=WHIP_THROW, sway=-1, coil=False, palms=1, mouth=2)),
             ("Whip5", Pose(near=WHIP_RECOVER, sway=0, coil=False))]
          + [("Zone0", Pose(near=ZONE_RISE[0][0], far=ZONE_RISE[0][1], palms=1, hand_glow=1, far_glow=1, gem=1)),
             ("Zone1", Pose(near=ZONE_RISE[1][0], far=ZONE_RISE[1][1], palms=1, hand_glow=1, far_glow=1, gem=1, sway=1)),
             ("Zone2", Pose(near=ZONE_HIGH[0], far=ZONE_HIGH[1], palms=1, hand_glow=2, far_glow=2, gem=2, sway=1, mouth=1)),
             ("Zone3", Pose(near=ZONE_HIGH[0], far=ZONE_HIGH[1], palms=1, hand_glow=1, far_glow=2, gem=2, sway=0, mouth=1)),
             ("Zone4", Pose(near=ZONE_SLAM[0], far=ZONE_SLAM[1], palms=1, hand_glow=2, far_glow=2, gem=1, sway=-1, mouth=2)),
             ("Zone5", Pose(near=(CX - 12.6, -16.6), far=(CX + 12.2, -16.8), palms=1, sway=0))]
          + [("Channel0", Pose(near=SPREAD[0][0], far=SPREAD[0][1], palms=1, eyes=1, gem=1)),
             ("Channel1", Pose(near=SPREAD[1][0], far=SPREAD[1][1], palms=1, eyes=2, gem=1, sway=1)),
             ("Channel2", Pose(near=SPREAD[1][0], far=SPREAD[1][1], palms=1, eyes=2, gem=2, hand_glow=1, far_glow=1, sway=1)),
             ("Channel3", Pose(near=SPREAD[1][0], far=SPREAD[1][1], palms=1, eyes=2, gem=2, hand_glow=2, far_glow=2, sway=0))]
          + [("Laser0", Pose(near=LASER_HAND[0], gem=1)),
             ("Laser1", Pose(near=LASER_HAND[1], gem=2, eyes=3)),
             ("Laser2", Pose(near=LASER_HAND[1], gem=2, eyes=1, mouth=1)),
             ("Laser3", Pose(near=LASER_HAND[0], gem=1))]
          + [("Intro0", Pose(eyes=0)), ("Intro1", Pose(eyes=3)), ("Intro2", Pose(eyes=1)), ("Intro3", Pose(eyes=1, mouth=1, sway=1))]
          + [("Death%d" % k, Pose(eyes=0 if k > 1 else 3, mouth=2 if k < 3 else 0, jade=min(1.0, (k + 1) / 5.0), cracks=max(0, k - 5)))
             for k in range(8)])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Whip", "Zone", "Channel", "Laser", "Intro", "Death")
FLICK_OK = ("Idle", "Whip", "Laser", "Intro")              # frame sets whose far arm rests: the coin flick may replace it
COLUMNS = 4


# --- small sprites ------------------------------------------------------------------------------------------------------------
DART_HEADINGS = 16
DART_CELL = 13


def dart(k):
    """The rope dart's jade blade pointing along heading k (k * 22.5 degrees, 0 = right, clockwise on screen): a leaf
    blade lit from the top-left in its own space, a gilt collar and ring at its tail, drawn at the heading (rasterised per
    heading: never rotated at runtime)."""
    cv = Canvas()
    a = k * 22.5
    xf = Xf.pose(a, (0.0, 0.0), (DART_CELL / 2.0, DART_CELL / 2.0))
    blade = Poly([(5.6, 0.0), (1.6, -2.0), (-1.2, -1.6), (-1.2, 1.6), (1.6, 2.0)])
    cv.part(xf, blade, "ghost", face((-0.5, -0.6, 0.6), lo=2, hi=5, ramp_len=6, snap=22.5), rust=0.0)
    cv.part(xf, Ellipse(-2.6, 0.0, 1.5, 1.4), "gilt", dome(-3.0, -0.4, 1.8, lo=3, hi=8, snap=22.5), rust=0.0)
    return cv


def cord_link():
    cv = Canvas()
    for (x, y, col) in ((0, 0, K[4]), (1, 0, K[3]), (0, 1, K[2]), (1, 1, K[1])):
        cv.put(x, y, col)
    return cv


COIN_FRAMES, COIN_CELL = 6, 9


def coin(k):
    """A jade coin with a square gilt-rimmed hole (the old cash coin), spinning: its width narrows to an edge and back."""
    cv, glow = Canvas(), Canvas()
    widths = (4.0, 3.2, 1.8, 0.7, 1.8, 3.2)
    w = widths[k]
    c = COIN_CELL / 2.0
    for y in range(COIN_CELL):
        for x in range(COIN_CELL):
            dx, dy = (x + 0.5 - c) / max(0.35, w), (y + 0.5 - c) / 4.0
            r = math.hypot(dx, dy)
            if r > 1.0:
                continue
            edge = r > 0.78
            if w < 1.0:
                col = G[5] if y < c else G[3]
            elif edge:
                col = G[6] if (x < c and y < c) else G[3]
            elif abs(x + 0.5 - c) < 0.9 * w / 4.0 + 0.4 and abs(y + 0.5 - c) < 1.0:
                col = ST[0]                                    # the square hole
            else:
                col = GH[4] if (x + y) < COIN_CELL - 1 else GH[3]
                glow.put_glow(x, y, GH[3])
            cv.put(x, y, col)
    return cv, glow


GROUND_FRAMES = 4


def cursed_ground(k):
    """The curse on three tiles (48x6 px over their tops): jade cracks in the surface glowing, motes rising, flickering."""
    cv, glow = Canvas(), Canvas()
    for x in range(24):
        y = 2
        col = GH[3] if (x + k) % 5 else GH[4]
        cv.put_glow(x, y, col)
        glow.put_glow(x, y, col)
        if (x * 3 + k) % 7 == 0:
            cv.put_glow(x, 1, GH[2])
            glow.put_glow(x, 1, GH[2])
        if (x * 5 + k * 3) % 11 == 0:
            for dy in range(1, 3):
                cv.put_glow(x, 1 - dy, GH[4] if dy == 1 else GH[5])
                glow.put_glow(x, 1 - dy, GH[4] if dy == 1 else GH[5])
    return cv, glow


ZONE_FRAMES = 4


def zone_piece(k):
    """One tile-wide piece (8 art px) of the petrify zone's glyph line on the ground: a jade rune band, flickering; the game
    lays 12 of them and the shards rise from them at the snap."""
    cv, glow = Canvas(), Canvas()
    glyphs = ((1, 0), (2, 1), (3, 0), (5, 1), (6, 0))
    for x in range(8):
        col = GH[3] if (x + k) % 4 else GH[4]
        cv.put_glow(x, 3, col)
        glow.put_glow(x, 3, col)
    for (x, y) in glyphs:
        col = GH[5] if (x + k) % 3 == 0 else GH[4]
        cv.put_glow(x, y + 1, col)
        glow.put_glow(x, y + 1, col)
    return cv, glow


BAT_W, BAT_H, BAT_FRAMES = 20, 14, 4


def bat(k):
    """A jade bat, one of Jadey's coin minions: a carved jade body (lit as a dome in its own space) with a gilt collar,
    pointed ears, glowing jade eyes; membrane wings of verdigris on jade ribs, beating over four frames (up, level, down,
    level). Faces left like every NPC sheet (D4 rule 8). Returns (canvas, glow) in a BAT_W x BAT_H box."""
    cv, glow = Canvas(), Canvas()
    cx, cy = BAT_W / 2.0 - 1.0, BAT_H / 2.0 + 0.5
    lift = (-4.0, -1.0, 2.6, -1.0)[k]
    for side in (-1, 1):                                       # the wings, the far one first and a step darker
        tip = (cx + side * 9.0, cy + lift - (1.0 if side < 0 else 0.0))
        elbow = (cx + side * 5.0, cy + lift * 0.6 - 2.0)
        shape = Poly([(cx + side * 1.6, cy - 1.6), elbow, tip, (cx + side * 8.0, cy + lift * 0.5 + 1.6), (cx + side * 6.6, cy + lift * 0.45 + 1.2),
                      (cx + side * 5.6, cy + lift * 0.3 + 2.4), (cx + side * 4.2, cy + lift * 0.2 + 1.4), (cx + side * 3.0, cy + 2.4)])
        wing = cv.part(Xf(), shape, "verd", flat(1 if side > 0 else 2, bevel=False), rust=0.0)
        for t in range(1, 4):                                  # the ribs
            q = P(Xf(), (cx + side * (1.6 + (tip[0] - cx) * side * t / 4.0 * side), cy - 1.0 + (lift - 0.6) * t / 4.0))
            if q in wing:
                cv.put(q[0], q[1], GH[3] if side < 0 else GH[2])
    body = cv.part(Xf(), Union(Ellipse(cx, cy, 3.4, 3.2), Ellipse(cx, cy + 1.6, 2.4, 2.4)), "ghost",
                   dome(cx - 1.2, cy - 1.4, 4.2, lo=1, hi=5, gain=1.4, fixed=True), rust=0.0)
    for (dx, dy) in ((-2, -3), (-1, -4), (1, -3), (2, -4)):     # ears
        cv.put(int(cx) + dx, int(cy) + dy, GH[0] if dy == -4 else GH[3])
    for dx in (-2, -1, 0, 1, 2):                               # the gilt collar
        q = (int(cx) + dx, int(cy) + 1)
        if q in body:
            cv.put(q[0], q[1], G[7] if dx < 0 else G[5])
    for (dx, dy) in ((-2, -1), (0, -1)):                       # the eyes (facing left: both on the near side of the face)
        cv.put_glow(int(cx) + dx, int(cy) + dy, GH[5])
        glow.put_glow(int(cx) + dx, int(cy) + dy, GH[5])
    finish(cv)
    return cv, glow


def bag():
    """Her treasure bag: jade silk tied with a gilt cord, a crimson tassel, a pagoda-roof clasp."""
    cv = Canvas()
    body = Poly([(3.0, 7.0), (13.0, 7.0), (15.0, 12.0), (14.0, 15.0), (2.0, 15.0), (1.0, 12.0)])
    cv.part(Xf(), body, "ghost", dome(5.0, 9.0, 9.0, lo=1, hi=4, fixed=True), rust=0.0)
    neck = Poly([(5.0, 3.0), (11.0, 3.0), (10.0, 7.0), (6.0, 7.0)])
    cv.part(Xf(), neck, "ghost", flat(3), rust=0.0)
    for x in range(5, 12):
        cv.put(x, 6, G[7] if x < 8 else G[5])
    for (x, y, col) in ((7, 1, G[6]), (8, 1, G[6]), (6, 2, G[5]), (9, 2, G[5]), (12, 7, K[4]), (13, 8, K[3]), (13, 9, K[2])):
        cv.put(x, y, col)
    for (x, y) in ((7, 11), (8, 11), (8, 10)):
        cv.put(x, y, G[7])
    return cv


# --- outputs ------------------------------------------------------------------------------------------------------------------
def fit_cell(canvas_sets):
    xs = [x for cvs in canvas_sets for cv in cvs for (x, y) in list(cv.px) + list(cv.glow) if y < GROUND_CLIP]
    ys = [y for cvs in canvas_sets for cv in cvs for (x, y) in list(cv.px) + list(cv.glow) if y < GROUND_CLIP]
    x0, x1, y0 = min(xs), max(xs), min(ys)
    ox = max(-x0, x1 + 1)
    return (2 * ox, GROUND_CLIP - y0, ox, -y0)


def grid(canvases, cell, glow=False):
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((w + 1) * COLUMNS, (h + 1) * rows), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        bx, by = (k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)
        for (x, y), col in src.items():
            if y >= GROUND_CLIP:
                continue
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[bx + cx, by + cy] = col + (255,)
    return out


def vertical(canvases, size_w, size_h, glow=False, trailing=False):
    """Cells stacked vertically, 1 px (2 in game) between them; `trailing` keeps that gap under the last cell too, so the
    sheet's height divides evenly by its frames (vanilla's NPC frames: texture height / Main.npcFrameCount)."""
    im = Image.new("RGBA", (size_w, (size_h + 1) * len(canvases) - (0 if trailing else 1)), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        for (x, y), col in src.items():
            if 0 <= x < size_w and 0 <= y < size_h:
                im.putpixel((x, y + k * (size_h + 1)), col + (255,))
    return im


def body_box(mid):
    """The hitbox (1x, from the origin): the cushion, the body and the head (not the ears' tips, the bun or the arms)."""
    pts = list(mid.px)
    xs = sorted(x for (x, _) in pts)
    ys = sorted(y for (_, y) in pts)
    return xs[3], xs[-3] + 1, int(HEAD_C[1] - 9.0), 0


def head_icon(mid):
    hx, hy = int(HEAD_C[0]), int(HEAD_C[1])
    px = {(x - hx + 12, y - hy + 14): c for (x, y), c in mid.px.items() if abs(x - hx) <= 11 and hy - 14 <= y <= hy + 9}
    xs = [x for x, _ in px]
    ys = [y for _, y in px]
    return to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def gores(frames):
    mid = frames[INDEX["Death5"]][1]
    hx, hy = HEAD_C
    parts = {"Jadey_GoreHead": {q: c for q, c in mid.px.items() if q[1] <= hy + 8},
             "Jadey_GoreBody": {q: c for q, c in mid.px.items() if hy + 8 < q[1] <= -10},
             "Jadey_GoreCushion": {q: c for q, c in mid.px.items() if q[1] > -8}}
    out = {}
    for name, px in parts.items():
        xs = [x for x, _ in px]
        ys = [y for _, y in px]
        out[name] = to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    return out


def write_rig(path, cell, frames, flicks):
    w, h, ox, oy = cell
    left, right, top, bottom = body_box(frames[0][1])
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def arr(name, vals, typ="short"):
        return "\t\tpublic static readonly %s[] %s = { %s };" % (typ, name, ", ".join(str(v) for v in vals))
    near = [fr[4]["near"] for fr in frames]
    farp = [fr[4]["far"] for fr in frames] + [f[4]["far"] for f in flicks]
    ok = [1 if any(n.startswith(s) for s in FLICK_OK) else 0 for (n, _) in FRAMES]
    L = ["// <auto-generated> by art/bosses/jadey/make_jadey_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Bosses.Jadey",
         "{",
         "\t/// <summary>Jadey's grid sheets (game px, facing left): far, middle, near and glow, equal cells in <see cref=\"Columns\"/>",
         "\t/// columns with 2 px right of and under each; the origin is under the middle of her cushion. The far sheet holds the",
         "\t/// body frames' own far arms, then <see cref=\"Flick\"/> (the coin flick, drawn instead of a frame's own far arm where",
         "\t/// <see cref=\"FlickOk\"/>). Body*: her hitbox from the origin. Per frame, from the origin, facing left: NearX/NearY the",
         "\t/// near paw (the rope dart's cord leaves it), FarX/FarY the far paw (coins leave it; past the body frames: the flick",
         "\t/// frames'). Gem: the brow gem (her lasers leave it); Eyes: between her eyes.</summary>",
         "\tpublic static class JadeyRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
         % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
         "\t\tpublic const int %s;" % ", ".join(seq[:4]),
         "\t\tpublic const int %s;" % ", ".join(seq[4:]),
         "\t\tpublic const int Flick = %d, FlickFrames = %d, FarFrames = %d;" % (len(FRAMES), len(flicks), len(FRAMES) + len(flicks)),
         "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, BodyBottom = %d;" % (left * 2, right * 2, top * 2, bottom * 2),
         "\t\tpublic const int GemX = %d, GemY = %d, EyesX = %d, EyesY = %d;" % (round(GEM[0] * 2 + 1), round(GEM[1] * 2 + 1),
                                                                             round(HEAD_C[0] * 2), round(HEAD_C[1] * 2)),
         "\t\tpublic const int DartCell = %d, DartHeadings = %d, CoinCell = %d, CoinFrames = %d, GroundFrames = %d, PetrifyFrames = %d;"
         % (DART_CELL * 2, DART_HEADINGS, COIN_CELL * 2, COIN_FRAMES, GROUND_FRAMES, ZONE_FRAMES),
         "		public const int BatWidth = %d, BatHeight = %d, BatFrames = %d;" % (BAT_W * 2, BAT_H * 2, BAT_FRAMES),
         arr("NearX", [round(q[0] * 2) for q in near]),
         arr("NearY", [round(q[1] * 2) for q in near]),
         arr("FarX", [round(q[0] * 2) for q in farp]),
         arr("FarY", [round(q[1] * 2) for q in farp]),
         arr("FlickOk", [bool(v) and "true" or "false" for v in ok], "bool"),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def render_all():
    frames = [frame(p) for _, p in FRAMES]
    flicks = [frame(FRAMES[0][1], flick=h) for h in FLICK]
    return frames, flicks


def export_all():
    frames, flicks = render_all()
    cell = fit_cell([fr[:4] for fr in frames] + [fl[:1] for fl in flicks])
    export(grid([fr[0] for fr in frames] + [fl[0] for fl in flicks], cell), OUT + "Jadey_Far.png")
    export(grid([fr[1] for fr in frames], cell), OUT + "Jadey.png")
    export(grid([fr[2] for fr in frames], cell), OUT + "Jadey_Near.png")
    export(grid([fr[3] for fr in frames], cell, glow=True), OUT + "Jadey_Glow.png")
    write_rig(OUT + "JadeyRigData.cs", cell, frames, flicks)
    export(head_icon(frames[0][1]), OUT + "Jadey_Head_Boss.png")
    export(vertical([dart(k) for k in range(DART_HEADINGS)], DART_CELL, DART_CELL), OUT + "Projectiles/JadeyRopeDart.png")
    export(vertical([cord_link()], 2, 2), OUT + "Projectiles/JadeyRopeDart_Cord.png")
    coins = [coin(k) for k in range(COIN_FRAMES)]
    export(vertical([c[0] for c in coins], COIN_CELL, COIN_CELL), OUT + "Projectiles/JadeCoin.png")
    export(vertical([c[1] for c in coins], COIN_CELL, COIN_CELL, glow=True), OUT + "Projectiles/JadeCoin_Glow.png")
    grounds = [cursed_ground(k) for k in range(GROUND_FRAMES)]
    export(vertical([g[0] for g in grounds], 24, 4), OUT + "Projectiles/JadeCursedGround.png")
    zones = [zone_piece(k) for k in range(ZONE_FRAMES)]
    export(vertical([z[0] for z in zones], 8, 4), OUT + "Projectiles/JadePetrifyZone.png")
    b = bag()
    export(to_image(b.px, 0, 0, 16, 16), OUT + "Items/JadeyBag.png")
    bats = [bat(k) for k in range(BAT_FRAMES)]
    export(vertical([bb[0] for bb in bats], BAT_W, BAT_H, trailing=True), OUT + "NPCs/JadeBat.png")
    export(vertical([bb[1] for bb in bats], BAT_W, BAT_H, glow=True, trailing=True), OUT + "NPCs/JadeBat_Glow.png")
    for name, im in gores(frames).items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path, scale=4, names=None, bg=(36, 30, 40)):
    names = names or [n for n, _ in FRAMES]
    lookup = dict(FRAMES)
    cw, ch = 46, 60
    cols = min(8, len(names))
    rws = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rws), bg + (255,))
    for k, n in enumerate(names):
        far, mid, near, glow, _ = frame(lookup[n])
        t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cvs in (far, mid, near):
            t.alpha_composite(to_image(cvs.px, -cw // 2, -ch + 5, cw, ch))
        sheet.alpha_composite(t, ((k % cols) * cw, (k // cols) * ch))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--frames")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview, names=a.frames.split(",") if a.frames else None)
    else:
        export_all()
