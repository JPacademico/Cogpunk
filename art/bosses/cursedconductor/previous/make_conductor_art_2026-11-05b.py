"""Source for the Cursed Conductor, Old Brass Town's boss, his ghost train and its loot (D4). Run from the repo root:

    python -P art/bosses/cursedconductor/make_conductor_art.py [--preview FILE]

Design (user, 2026-11-04: "a new boss called Cursed Conductor (T5, same tier as wall of flesh), a train conductor robot
that calls a spirit of a big flying ghost train to attack the player in different patterns"). Redrawn 2026-11-05 (user:
"the cursed conductor should also be a bit bigger and more menacing"; the long ramps of docs/design/pixel-art-study.md;
the 2026-11-04 version is in previous/): a third bigger, a tall robot conductor, his legs long gone. Reworked 2026-11-05b
(user: "rework the cursed conductor bottom half design (the train is fine): it should have a turbine that pumps smoke on
the bottom instead of the ghost floaty bottom; also the perspective for his lantern arm is visually ugly as it seems it
is being thrown from his back"; the 2026-11-05 version is previous/make_conductor_art_2026-11-05.py): below the tattered
hem of his coat hangs a steel turbine drum, brass-banded and riveted, its vanes spinning past a window in its side (an
overlay sheet the game animates on its own clock), above a flared brass exhaust bell glowing ghost-green inside; the game
pumps soot-black smoke out of it (its puff sheet is drawn here). The lantern hangs from his near-side (right) hand now, in front of the
coat, and the throw swings it up and back over that shoulder and forward across his chest. A cracked steel skull of a face lit from
the top-left, angry brow plates sloping into a V over two deep sockets with ghost-green pupils, ghost light leaking
from the crack, a drooping ivory walrus moustache over a jaw of steel teeth, a riveted gilt ear bolt; a tall conductor's
cap (navy felt, a gilt cord, a gilt winged-wheel badge, a black gloss visor); a long double-breasted navy coat (woven,
lapels, an ivory collar and a crimson tie, two rows of gilt buttons, gilt epaulettes with fringe, a leather belt with a
gilt buckle, a watch chain) torn in two places where ghost light shows through; navy sleeves with gilt cuffs and bony
steel hands. In the near hand his gilt whistle on a chain; in the far hand a big railway lantern (a gilt cap and bail,
a steel cage, a globe of ghost flame). Three-quarter view facing left (D4 rule 13): the coat's front is turned to the
left, so its right flank is the side nearest us, and both arms are drawn in front of the coat (the whistle hand reaches
forward, the lantern arm hangs on the near flank).

Two planes since 2026-11-05b (DepthLayers.DrawWalker grid sheets; the far plane held the lantern arm, and nothing is
behind him now): middle (the turbine, the coat, the head and the cap), near (the whistle arm and the whistle, then the
lantern arm and the lantern); the glow sheet holds the eyes, the crack, the coat's tears, the exhaust's glow, the lantern's flame and the
whistle's breath, each only where no nearer plane covers it. Stable pixels (D4 rule 17): whole-pixel bobs, the body and
the turbine built in their own space and placed by one translation, limbs with their light's turn snapped.

Frames: Idle x6 (floating: the bob, the coat's back tail fluttering), Whistle x4 (the whistle up to
the mouth, then blowing: the train's call), Point x2 (the arm out, sending the train), Throw x4 (the lantern swung back,
higher, overhead where its bolts fly, forward), Call x2 (the lantern raised high and the whistle blowing: the loop and
the whistle phase), Tip x3 (the intro: a hand to the visor, the cap raised, a bow), Dying x4 (slumping, the eyes, the
lantern and the exhaust going out). The turbine's vanes: 4 frames of the drum's window (8 vanes, a quarter of a vane's
spacing a frame, foreshortened round the drum, so the loop is seamless); its smoke: 5 frames of a soot puff growing and
breaking up.

The ghost train (hostile: ghost green, an ember headlamp): an engine (a boiler with glowing bands, a flared stack, a
steam dome, a cab with a ghost driver in its lit window, three drivers on a connecting rod, a cowcatcher) and a
passenger car (four lit windows, ghost passengers in two, two bogies), each drawn at 9 headings from straight up to
straight down facing right (-90 to +90 degrees, 22.5 apart; the left half is the same frames mirrored at runtime, so
it never rides upside down), drawn at each heading (never rotated as a bitmap). The game draws it translucent, its
windows and headlamp solid from the glow sheets.

Outputs (2x):
    Content/Bosses/CursedConductor/CursedConductor.png, _Near.png, _Glow.png   grid sheets (no _Far since 2026-11-05b)
    Content/Bosses/CursedConductor/CursedConductor_Rotor.png, _Smoke.png   the turbine's vanes (4 frames), its smoke (5)
    Content/Bosses/CursedConductor/CursedConductorRigData.cs     cells, origin, sequences, points, the body box
    Content/Bosses/CursedConductor/CursedConductor_Head_Boss.png  the map icon
    Content/Bosses/CursedConductor/Projectiles/GhostTrain.png, _Glow.png, _Car.png, _CarGlow.png   9 headings each
    Content/Bosses/CursedConductor/Projectiles/GhostTrain_Rail.png   the telegraph: a level and an upright stretch of
                                                                      ghost track, and a ring marker
    Content/Bosses/CursedConductor/Projectiles/ConductorFlame.png     4 frames of cursed ghost fire (his lantern's bolt)
    Content/Bosses/CursedConductor/Projectiles/GhostRift.png          4 frames: a ghost rift opening (where a ghost rises)
    Content/Bosses/CursedConductor/Buffs/ConductorCurse.png           32x32 the curse's icon: a punched ghost ticket
    Content/Bosses/CursedConductor/Items/CursedConductorBag.png       36x36 the treasure bag
    Content/Bosses/CursedConductor/Gores/CursedConductor_GoreCap.png, _GoreHead.png, _GoreLantern.png, _GoreCoat.png,
                                                                        _GoreTurbine.png
    Content/Bosses/CursedConductor/Gores/CursedConductor_Bit0.png .. _Bit5.png   tiny pieces: his death's explosion
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "mecharmy"))
from westbots import (RAMP, Xf, Poly, Ellipse, Union, Capsule, box, Canvas, flat, dome, face, P, despeckle, limb, ik,  # noqa: E402
                      finish, texture, glint, I, B, S)
from rig import cyl  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Bosses/CursedConductor/"
A, V, E = RAMP["aether"], RAMP["verd"], RAMP["ember"]
D, GH, G, ST, IV, K, H = (RAMP[k] for k in ("denim", "ghost", "gilt", "steel", "ivory", "crimson", "hide"))

# --- the conductor's rig (1x, y down, the origin under the turbine's exhaust bell, facing left) ----------------------
HEM_Y = -17.0                    # the coat's hem (its tatters reach a row lower)
SH_NEAR = (-7.8, -45.2)          # the whistle arm's shoulder (the coat's front, turned left)
SH_LAMP = (7.4, -46.0)           # the lantern arm's shoulder (the near flank; 2026-11-05b: in front, it was behind)
UPPER, FORE = 8.2, 8.0
REST_NEAR = (-9.8, -34.6)
REST_LAMP = (11.8, -31.4)        # the lantern hangs at his near side, in front of the coat
# the turbine (2026-11-05b): a steel drum under the hem, a vane window, a flared brass exhaust bell
TURB_CX = 1.0
# rows from the hem down (the ground clip drops rows below 0, so the cone's tip is row 0): the drum to row -7 (rivets
# at -14, the window -12..-9 in its frame, the band at -7), the bell -6..-2, the cone and the fire round it -2..0
DRUM_L, DRUM_R, DRUM_TOP, DRUM_BOT = -8.6, 10.6, -18.0, -6.0
ROTOR = (-6, -12, 15, 4)         # the vane window: left, top, width, height (art px from the origin, at rest)
ROTOR_FRAMES, VANES = 4, 8
BELL = ((-7.4, -6.6), (9.4, -6.6), (11.8, -1.6), (-9.8, -1.6))
CONE = ((-0.6, -2.4), (2.6, -2.4), (1.8, 0.9), (0.2, 0.9))
EXHAUST = (1.0, 0.0)             # where the smoke comes out (the bell's mouth, round the tail cone)
SMOKE = 12
SMOKE_FRAMES = 5
MOUTH = (-10.4, -51.2)           # where the whistle meets the moustache (head at rest)
EYES = (-5.0, -54.0)


class Pose:
    def __init__(self, phase=0, bob=0, near=REST_NEAR, far=REST_LAMP, whistle="hand", puff=0, flame=2, head=0, cap=0, slump=0,
                 exhaust=3, eyes=3, flutter=0, point=False, lamp_bend=1):
        self.phase, self.bob = phase, bob
        self.near, self.far = near, far                 # the whistle hand, the lantern hand
        self.lamp_bend = lamp_bend                      # which way the lantern arm's elbow bends (+1 back, -1 out)
        self.whistle, self.puff = whistle, puff         # "hand" / "mouth"; 0-2 puffs of breath
        self.flame = flame                              # the lantern: 3 bright (telegraph), 2 lit, 1 dim, 0 out
        self.head, self.cap = head, cap                 # whole px the head drops (bow, slump), the cap is raised
        self.slump = slump                              # whole px the whole body sinks
        self.exhaust = exhaust                          # the exhaust's glow: 3 bright .. 0 out
        self.eyes = eyes                                # 3 bright .. 0 out
        self.flutter = flutter                          # whole px the coat's back tail swings out
        self.point = point


def fl(v):
    return int(math.floor(v))


# ================================================================================================
# The conductor
# ================================================================================================
def turbine(mid, p):
    """The turbine under the hem, built in the body's space and placed by the same whole-pixel translation (stable): a
    steel drum lit from the left as a cylinder, rivets round its top, the vane window in a gilt frame (dark: the vanes are
    the game's overlay, rotor()), a riveted gilt band at its foot, two gilt intake pipes up under the coat; under it the
    flared brass exhaust bell, its rolled lip lit, its flare in shadow, and a steel tail cone out of its mouth with the
    cursed fire glowing ghost-green round it (put_glow, dimmer as it dies). Drawn before the coat, whose hem covers the
    drum's top."""
    oy = p.bob + p.slump
    T = Xf.pose(0.0, (0.0, 0.0), (0.0, float(oy)))
    # the bell first, so the drum's foot band laps over its top edge (one seam, not two outlines)
    bell = mid.part(T, Poly(list(BELL)), "gilt", cyl((TURB_CX, -5.6), (TURB_CX, 1.0), 10.6, lo=2, hi=7, gain=1.25, bias=-0.05, fixed=True,
                                                     dither=0.15), shadow=(1, 1), rust=0.0)
    for x in range(-9, 12):                                        # the rolled lip at the mouth, lit on the left
        q = P(T, (x + 0.5, -2.5))
        if q in bell and (q[0] - 1, q[1]) in bell and (q[0] + 1, q[1]) in bell:
            mid.put(q[0], q[1], G[7] if x < -2 else (G[5] if x < 5 else G[3]))
    for x in range(-6, 9):                                         # the flare's shadow under the band
        q = P(T, (x + 0.5, -5.5))
        if q in bell:
            mid.put(q[0], q[1], G[3] if x < 3 else G[2])
    q = P(T, (-4.5, -3.5))
    if q in bell:
        glint(mid, q[0], q[1], "gilt")
    drum = mid.part(T, box(DRUM_L, DRUM_TOP, DRUM_R, DRUM_BOT), "steel",
                    cyl((TURB_CX, DRUM_TOP), (TURB_CX, DRUM_BOT), 10.0, lo=3, hi=8, gain=1.3, fixed=True, dither=0.16), shadow=(1, 1), rust=0.0)
    # the coat's shadow across its top: the rows just under the hem one band darker (two at the back)
    for y in (-16, -15):
        for x in range(int(DRUM_L), int(DRUM_R) + 1):
            q = P(T, (x + 0.5, y + 0.5))
            if q in drum and mid.px.get(q) in ST:
                k = ST.index(mid.px[q])
                mid.put(q[0], q[1], ST[max(1, k - (1 if x < 3 else 2))])
    # rivets round its top, just under the hem
    for x in (-7, -4, -1, 2, 5, 8):
        q = P(T, (x + 0.5, -13.5))
        if q in drum:
            mid.put(q[0], q[1], ST[8] if x < 2 else ST[6])
            if (q[0] + 1, q[1] + 1) in drum:
                mid.put(q[0] + 1, q[1] + 1, ST[2])
    # the vane window in a gilt frame: a dark recess (the overlay's vanes spin across it)
    x0, y0, w, h = ROTOR
    for x in range(x0 - 1, x0 + w + 1):
        for y in (y0 - 1, y0 + h):
            q = P(T, (x + 0.5, y + 0.5))
            if q in drum:
                lit_ = x < 1
                mid.put(q[0], q[1], (G[8] if lit_ else G[5]) if y == y0 - 1 else (G[5] if lit_ else G[3]))
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            q = P(T, (x + 0.5, y + 0.5))
            if q in drum:
                mid.put(q[0], q[1], ST[1] if y == y0 else ST[0])
        for x in (x0 - 1, x0 + w):
            q = P(T, (x + 0.5, y + 0.5))
            if q in drum:
                mid.put(q[0], q[1], G[6] if x < 0 else G[3])
    # the riveted gilt band at its foot (its last row)
    for x in range(int(DRUM_L) + 1, int(DRUM_R)):
        q = P(T, (x + 0.5, -6.5))
        if q in drum:
            mid.put(q[0], q[1], G[7] if x < -3 else (G[6] if x < 4 else G[4]))
            if x % 3 == 1:
                mid.put(q[0], q[1], G[9] if x < 3 else G[7])
    # the gilt intake pipes from its shoulders up under the coat
    for (px_, top) in ((-9.4, -18.6), (10.2, -18.6)):
        mid.part(T, box(px_, top, px_ + 2.4, -14.6), "gilt", face((-0.6, -0.2, 0.75), lo=3, hi=7, ramp_len=10, fixed=True), rust=0.0)
    # the steel tail cone out of the mouth, the cursed fire round it
    cone = mid.part(T, Poly(list(CONE)), "steel", face((-0.6, -0.3, 0.75), lo=3, hi=7, ramp_len=9, fixed=True), rust=0.0)
    level_ = {3: (GH[5], GH[4], GH[3]), 2: (GH[4], GH[3], GH[2]), 1: (GH[3], GH[2], GH[1]), 0: None}[p.exhaust]
    if level_:
        for x in range(-7, 10):                                    # the ring of fire round the cone, under the lip
            q = P(T, (x + 0.5, -0.5))
            if q not in cone:
                mid.put_glow(q[0], q[1], level_[0] if -2 <= x <= 4 else (level_[1] if -5 <= x <= 7 else level_[2]))
        for x in range(-3, 6):
            q = P(T, (x + 0.5, 0.5))
            if q not in cone:
                mid.put_glow(q[0], q[1], level_[1] if -1 <= x <= 3 else level_[2])


def body(mid, p):
    """The coat, the collar, the buttons and the chain, the head and the cap, built in the body's own space and placed by
    one whole-pixel translation (D4 rule 17). Returns the shoulders and the mouth."""
    oy = p.bob + p.slump
    T = Xf.pose(0.0, (0.0, 0.0), (0.0, float(oy)))
    f = p.flutter

    def at(x, y, xf=T):
        return P(xf, (x, y))
    hem = [(14.6 + f, -15.0), (12.0 + f, -17.8), (9.4, -14.8), (6.2, -17.4), (3.0, -14.6), (-0.4, -17.2), (-3.6, -14.4),
           (-6.8, -16.8), (-9.8, -14.6), (-12.8, -16.6)]
    pts = [(-9.4, -47.0), (8.6, -47.0), (10.6, -40.6), (10.2, -30.0), (13.4 + f, -21.6)] + hem + [(-12.6, -21.0), (-10.0, -30.0), (-10.8, -40.6)]
    coat = mid.part(T, Poly(pts), "denim", texture(face((-0.5, -0.45, 0.75), lo=1, hi=3, ramp_len=6, gain=1.3, bias=-0.05, fixed=True,
                                                         dither=0.15), "weave", seed=41), shadow=(1, 1), rust=0.0)
    for y in range(-45, -31):                                      # a fold of light down the chest's lit side
        q = at(-9.0 + (1.0 if y > -38 else 0.0), y + 0.5)
        if q in coat:
            mid.put(q[0], q[1], D[3])
            if (q[0] + 1, q[1]) in coat and y % 3 == 0:
                mid.put(q[0] + 1, q[1], D[2])
    for y in range(-29, -15):                                      # the skirt's front opening, off-centre (3/4 view)
        q = at(-4.0 - (1.0 if y >= -22 else 0.0), y + 0.5)
        if q in coat:
            mid.put(q[0], q[1], D[0])
            if (q[0] - 1, q[1]) in coat:
                mid.put(q[0] - 1, q[1], D[2])                      # its lit lip
    for y in range(-28, -18):                                      # skirt folds
        for x0 in (5.0, -8.0):
            q = at(x0 + 0.2 * (y + 28), y + 0.5)
            if q in coat and y % 2 == 0:
                mid.put(q[0], q[1], D[1])
    # the lapels and the ivory collar with a crimson tie
    for pts_, k in ((((-8.8, -46.8), (-5.0, -46.8), (-6.4, -40.0)), 3), (((-0.6, -46.8), (3.2, -46.8), (0.8, -40.6)), 2)):
        for q in mid.raster(T, Poly(pts_)):
            if q in coat:
                mid.put(q[0], q[1], D[k])
    cx0, cy0 = at(-4.0, -46.6)
    for (dx, dy, col) in ((0, 0, IV[5]), (1, 0, IV[4]), (2, 0, IV[3]), (-1, 0, IV[4]), (0, 1, K[4]), (1, 1, K[3]), (0, 2, K[3]),
                          (1, 2, K[2]), (0, 3, K[2])):
        mid.put(cx0 + dx, cy0 + dy, col)
    # the epaulettes, gilt boards with a fringe
    for (x0, y0, w) in ((-10.2, -47.6, 4), (5.4, -48.2, 4)):
        q = at(x0, y0)
        for dx in range(w):
            mid.put(q[0] + dx, q[1], G[8] if dx < 2 else G[6])
            mid.put(q[0] + dx, q[1] + 1, G[5] if dx < 2 else G[4])
            if dx % 2 == 0:
                mid.put(q[0] + dx, q[1] + 2, G[7] if dx < 2 else G[4])   # the fringe
    # two rows of gilt buttons, the leather belt and its buckle, the watch chain
    for row, y in enumerate((-43.0, -39.0, -35.0, -31.0)):
        for x in (-7.4, -1.6):
            q = at(x, y)
            if q in coat:
                mid.put(q[0], q[1], G[9] if row == 0 and x < -5 else G[8])
                mid.put(q[0] + 1, q[1], G[5])
                if (q[0], q[1] + 1) in coat:
                    mid.put(q[0], q[1] + 1, D[0])
    belt = mid.part(T, box(-10.4, -29.4, 10.4, -27.4), "hide", face((-0.4, -0.6, 0.75), lo=1, hi=3, ramp_len=7, fixed=True), rust=0.0)
    bq = at(-6.4, -29.0)
    for (dx, dy, k) in ((0, 0, 9), (1, 0, 7), (2, 0, 6), (0, 1, 6), (1, 1, 4), (2, 1, 4)):
        mid.put(bq[0] + dx, bq[1] + dy, G[k])
    for k, (x, y) in enumerate(((0.0, -33.0), (1.0, -32.0), (2.0, -32.0), (3.0, -31.6), (4.0, -32.0), (5.0, -33.0))):
        q = at(x, y)
        mid.put(q[0], q[1], G[8] if k % 2 == 0 else G[5])
    del belt
    # two tears in the skirt, ghost light behind them
    for (tx, ty, w, h) in ((5.4, -22.4, 1.5, 0.9),):
        for q in mid.raster(T, Ellipse(tx, ty, w, h)):
            if q in coat:
                lit_ = (q[0] - at(tx, ty)[0]) + (q[1] - at(tx, ty)[1]) <= 0
                mid.put_glow(q[0], q[1], GH[4] if lit_ else GH[3])
        q = at(tx - w - 0.4, ty + h)
        if q in coat:
            mid.put(q[0], q[1], D[0])                              # a frayed edge
    # the neck
    mid.part(T, box(-5.0, -49.4, -0.4, -46.8), "steel", face((-0.5, -0.5, 0.7), lo=2, hi=4, ramp_len=9, fixed=True), rust=0.0)
    # --- the head: a cracked steel skull of a face ----------------------------------------------------------------------
    Hx = Xf.pose(0.0, (0.0, 0.0), (0.0, float(oy + p.head)))
    hpts = [(-10.2, -60.6), (2.8, -60.6), (4.2, -59.2), (4.4, -50.8), (3.0, -48.6), (-1.0, -47.6), (-7.8, -47.6), (-10.6, -49.6),
            (-11.0, -58.6)]
    head = mid.part(Hx, Poly(hpts), "steel", dome(-6.0, -58.0, 9.0, lo=2, hi=6, gain=1.35, bias=0.05, fixed=True, dither=0.15),
                    shadow=(1, 1), rust=0.0)
    g = at(-8.0, -59.0, Hx)
    glint(mid, g[0], g[1], "steel", cross=True)
    # the brows: two plates sloping into a V (angry), lit along their tops
    for (a, b) in (((-10.6, -57.6), (-5.6, -56.0)), ((-3.6, -56.0), (1.4, -57.8))):
        for k in range(6):
            u = k / 5.0
            q = at(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Hx)
            if q in head:
                mid.put(q[0], q[1], ST[1])
                if (q[0], q[1] - 1) in head:
                    mid.put(q[0], q[1] - 1, ST[7])
    # the sockets and the ghost-green pupils (out when he dies)
    for (ex, w) in ((-7.6, 2.3), (-2.4, 1.9)):
        sock = mid.raster(Hx, Ellipse(ex, -54.0, w, 1.8))
        for q in sock:
            if q in head:
                mid.put(q[0], q[1], ST[0])                          # deep, dark sockets
        c = at(ex, -54.4, Hx)
        level = {3: (GH[5], GH[4], GH[3]), 2: (GH[4], GH[3], GH[2]), 1: (GH[3], GH[2], GH[1]), 0: None}[p.eyes]
        if level:
            for (dx, dy, k) in ((-1, 0, 0), (0, 0, 1), (1, 0, 2), (-1, 1, 1), (0, 1, 2)):
                mid.put_glow(c[0] + dx, c[1] + dy, level[k])        # a burning ghost-green pupil
    # the crack down the brow, ghost light leaking out of it
    crack = ((-0.4, -60.4), (0.4, -59.4), (1.0, -58.4), (0.6, -57.4), (1.4, -56.4))
    for k, pt in enumerate(crack):
        q = at(pt[0], pt[1], Hx)
        if q in head:
            if p.eyes > 0 and k % 2 == 1:
                mid.put_glow(q[0], q[1], GH[3])
            else:
                mid.put(q[0], q[1], ST[0])
    # the nose slit, the drooping ivory moustache, the jaw of steel teeth
    q = at(-10.8, -52.4, Hx)
    mid.put(q[0], q[1], ST[1])
    mx, my = at(-11.6, -51.2, Hx)
    tash = []
    for dx in range(0, 11):
        tash.append((dx, 0, 5 if dx < 6 else 4))
        tash.append((dx, 1, 4 if dx < 7 else 3))
    tash += [(-1, 1, 3), (-1, 2, 3), (-1, 3, 2), (0, 2, 2), (11, 1, 2), (11, 2, 2), (10, 2, 1)]
    for (dx, dy, k) in tash:
        mid.put(mx + dx, my + dy, IV[k])
    for dx in range(1, 10):
        q = (mx + dx, my + 2)
        if q in head:
            mid.put(q[0], q[1], ST[7] if dx % 2 else ST[1])          # the teeth
        q2 = (mx + dx, my + 3)
        if q2 in head:
            mid.put(q2[0], q2[1], ST[4] if dx % 2 else ST[0])
    q = at(2.6, -54.0, Hx)                                         # the riveted gilt ear bolt
    for (dx, dy, k) in ((0, 0, 8), (1, 0, 6), (0, 1, 5), (1, 1, 3)):
        if (q[0] + dx, q[1] + dy) in head:
            mid.put(q[0] + dx, q[1] + dy, G[k])
    # --- the cap ----------------------------------------------------------------------------------------------------------
    Cx = Xf.pose(0.0, (0.0, 0.0), (0.0, float(oy + p.head - p.cap)))
    cb = -60.4
    crown = mid.part(Cx, Poly([(-10.8, cb + 0.4), (4.8, cb + 0.4), (6.2, cb - 7.2), (-10.4, cb - 7.8)]), "denim",
                     texture(face((-0.5, -0.5, 0.7), lo=1, hi=3, ramp_len=6, gain=1.3, bias=0.0, fixed=True), "felt", seed=43), rust=0.0)
    for x in range(-11, 7):                                        # the gilt cord
        q = at(x + 0.5, cb - 1.0, Cx)
        if q in crown:
            mid.put(q[0], q[1], G[8] if x < -3 else G[6])
            q2 = (q[0], q[1] + 1)
            if q2 in crown:
                mid.put(q2[0], q2[1], G[4])
    bq = at(-4.6, cb - 4.6, Cx)                                    # the winged-wheel badge
    for (dx, dy, k) in ((0, 0, 9), (1, 0, 7), (0, 1, 7), (1, 1, 5), (-1, 0, 8), (-2, -1, 7), (2, 0, 6), (3, -1, 5), (-1, 1, 5),
                        (2, 1, 4)):
        if (bq[0] + dx, bq[1] + dy) in crown:
            mid.put(bq[0] + dx, bq[1] + dy, G[k])
    for x in range(-10, 6):                                        # the crown's lit top edge
        q = at(x + 0.5, cb - 7.2, Cx)
        if q in crown and x < 2:
            mid.put(q[0], q[1], D[4])
    visor = mid.part(Cx, Poly([(-17.0, cb + 1.6), (-9.6, cb - 0.6), (-8.2, cb + 1.6), (-10.0, cb + 3.0), (-16.2, cb + 3.0)]), "steel",
                     face((0.0, -0.8, 0.6), lo=1, hi=3, ramp_len=9, fixed=True), rust=0.0)
    for x in range(-16, -10):
        q = at(x + 0.5, cb + 1.4, Cx)
        if q in visor and x < -12:
            mid.put(q[0], q[1], ST[6])                              # its gloss
    del visor
    return (SH_NEAR[0], SH_NEAR[1] + oy), (SH_LAMP[0], SH_LAMP[1] + oy), (MOUTH[0], MOUTH[1] + oy + p.head)


def sleeve_arm(cv, shoulder, hand, depth, bend=1):
    """A navy sleeve from the shoulder to the hand, a gilt cuff, a bony steel hand. Returns the hand's centre and the
    forearm's direction."""
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, bend)
    limb(cv, shoulder, elbow, 2.9, "denim", depth, lo=1, hi=3)
    limb(cv, elbow, wrist, 2.6, "denim", depth, lo=1, hi=3)
    d = (wrist[0] - elbow[0], wrist[1] - elbow[1])
    ln = math.hypot(*d) or 1.0
    u = (d[0] / ln, d[1] / ln)
    cv.part(Xf(), Capsule((wrist[0] - u[0] * 1.6, wrist[1] - u[1] * 1.6), (wrist[0] - u[0] * 0.4, wrist[1] - u[1] * 0.4), 2.7), "gilt",
            flat(6 if depth == 0 else 3, bevel=False), rust=0.0)
    fist = (wrist[0] + u[0] * 1.4, wrist[1] + u[1] * 1.4)
    cv.part(Xf(), Ellipse(fist[0], fist[1], 2.1, 2.0), "steel", flat(5 if depth == 0 else 3), rust=0.0)
    for k in range(3):                                             # bony fingers curled over the grip
        q = P(Xf(), (fist[0] + u[0] * 2.0 - u[1] * (k - 1) * 1.2, fist[1] + u[1] * 2.0 + u[0] * (k - 1) * 1.2))
        cv.put(q[0], q[1], ST[6 if depth == 0 else 3] if k != 2 else ST[3 if depth == 0 else 2])
    if depth == 0:
        q = P(Xf(), elbow)
        cv.put(q[0], q[1], D[3])                                   # the elbow's lit crease
    return fist, u


def lantern(cv, hand, flame):
    """A big railway lantern hanging from the hand (the near plane since 2026-11-05b): a gilt bail and cap, a glass globe of
    ghost flame in a steel cage, a steel base, lit like the near arm (the cap from the top-left). Its glass glows
    (put_glow) unless it is out."""
    x, y = hand
    for k in range(3):
        q = P(Xf(), (x - 1.2 + k * 1.2, y + 0.8 + (0.6 if k == 1 else 0.0)))
        cv.put(q[0], q[1], G[6] if k < 2 else G[4])                # the bail
    cv.part(Xf(), Poly([(x - 2.6, y + 1.8), (x + 2.6, y + 1.8), (x + 3.4, y + 3.8), (x - 3.4, y + 3.8)]), "gilt",
            face((-0.5, -0.6, 0.7), lo=4, hi=8, ramp_len=10, gain=1.3, fixed=True), rust=0.0)
    glass = cv.raster(Xf(), Ellipse(x, y + 7.4, 3.5, 3.7))
    cx, cy = fl(x), fl(y + 7.4)
    for q in glass:
        core = abs(q[0] - cx) <= 1 and abs(q[1] - cy) <= 1
        if flame >= 2:
            col = (GH[5] if flame == 3 else GH[4]) if core else (GH[4] if (q[0] - cx) + (q[1] - cy) < 0 else GH[3])
            cv.put_glow(q[0], q[1], col)
        elif flame == 1:
            cv.put_glow(q[0], q[1], GH[3] if core else GH[2])
        else:
            cv.put(q[0], q[1], ST[3] if (q[0] - cx) + (q[1] - cy) < -1 else ST[1])
    for q in glass:                                               # the cage: two bars down the glass and one across
        if q[0] in (cx - 2, cx + 2) or (q[1] == cy - 2 and abs(q[0] - cx) <= 1):
            cv.put(q[0], q[1], ST[2])
            cv.glow.pop(q, None)
    cv.part(Xf(), box(x - 3.4, y + 11.0, x + 3.4, y + 12.8), "steel", face((-0.5, -0.6, 0.7), lo=3, hi=6, ramp_len=9, fixed=True), rust=0.0)
    return (x, y + 7.4)


def whistle(near, fist, p, mouth):
    """The gilt whistle: in the fist at rest (its chain down to the top button), at the mouth when blowing (its breath a
    puff of steam out of its window, in the glow)."""
    fx, fy = fl(fist[0]), fl(fist[1])
    if p.whistle == "mouth":
        mx, my = fl(mouth[0]), fl(mouth[1])
        for (x, y, k) in ((mx - 1, my, 7), (mx, my, 5), (mx - 2, my, 8), (mx - 3, my, 9), (mx - 3, my + 1, 4), (mx - 2, my + 1, 4),
                          (mx - 1, my + 1, 3)):
            near.put(x, y, G[k])
        puff = ((mx - 4, my - 2), (mx - 5, my - 3), (mx - 4, my - 3))[:max(0, p.puff) + 1] if p.puff else ()
        big = ((mx - 6, my - 4), (mx - 5, my - 4), (mx - 6, my - 3), (mx - 7, my - 5), (mx - 7, my - 4)) if p.puff >= 2 else ()
        for q in tuple(puff) + big:
            near.put_glow(q[0], q[1], S[3] if q in puff[:1] else S[2])
        return (mx - 3, my)
    for (x, y, k) in ((fx - 2, fy, 7), (fx - 3, fy, 9), (fx - 4, fy, 8), (fx - 4, fy + 1, 4), (fx - 3, fy + 1, 4), (fx - 2, fy + 1, 3)):
        near.put(x, y, G[k])
    for (x, y) in ((fx - 1, fy + 2), (fx, fy + 3), (fx + 1, fy + 3), (fx + 2, fy + 4)):
        near.put(x, y, G[4])                                       # the chain
    return (fx - 4, fy)


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    turbine(mid, p)
    sh_near, sh_lamp, mouth = body(mid, p)
    oy = p.bob + p.slump
    if p.whistle == "mouth":
        hand = (mouth[0] + 2.0, mouth[1] + 1.8)
    else:
        hand = (p.near[0], p.near[1] + oy)
    nfist, u = sleeve_arm(near, sh_near, hand, 0, bend=1)
    tip = whistle(near, nfist, p, mouth)
    finger = None
    if p.point:
        fx, fy = fl(nfist[0] + u[0] * 2.6), fl(nfist[1] + u[1] * 2.6)
        for k in range(3):
            near.put(fx - k, fy, ST[6 - k])                         # a long bony finger
        finger = (fx - 2, fy)
    # the lantern arm last: on the near flank, in front of the coat and of the whistle arm when it swings across
    lfist, _ = sleeve_arm(near, sh_lamp, (p.far[0], p.far[1] + oy), 0, bend=p.lamp_bend)
    lamp = lantern(near, lfist, p.flame)
    for cv in (far, mid, near):
        finish(cv)
    for q, col in near.glow.items():
        glow.put_glow(q[0], q[1], col)
    for q, col in mid.glow.items():
        if q not in near.px:
            glow.put_glow(q[0], q[1], col)
    for q, col in far.glow.items():
        if q not in mid.px and q not in near.px:
            glow.put_glow(q[0], q[1], col)
    return far, mid, near, glow, {"lamp": lamp, "whistle": tip, "finger": finger, "mouth": mouth,
                                  "exhaust": (EXHAUST[0], EXHAUST[1] + oy), "bob": oy}


IDLE_BOB = (0, -1, -1, -1, 0, 0)
IDLE_FLUTTER = (0, 0, 1, 1, 1, 0)
IDLE_SWAY = (0.0, 0.0, 0.8, 0.8, 0.0, -0.6)


def idle(k, **kw):
    far = (REST_LAMP[0] + IDLE_SWAY[k], REST_LAMP[1])
    args = dict(phase=k, bob=IDLE_BOB[k], flutter=IDLE_FLUTTER[k], far=far)
    args.update(kw)
    return Pose(**args)


# the lantern's throw (2026-11-05b: forward, in front of him): swung back at his side, up and back over the shoulder
# (the flare: the telegraph), then across his chest at full reach (the release: the bolts fly from it), then down in
# front of his belly; each with the way its elbow bends
THROW_HANDS = (((16.0, -40.0), 1), ((15.0, -53.0), -1), ((-3.0, -41.2), 1), ((3.4, -35.2), 1))
THROW_WHISTLE = (-12.4, -33.4)                 # the whistle hand drawn back out of the lantern's way (the same plane)
TIP_HANDS = ((-11.2, -60.6), (-11.2, -63.4), (-11.2, -59.6))

FRAMES = ([("Idle%d" % k, idle(k)) for k in range(6)]
          + [("Whistle0", idle(0, near=(-12.0, -42.2))), ("Whistle1", idle(1, whistle="mouth")),
             ("Whistle2", idle(2, whistle="mouth", puff=1)), ("Whistle3", idle(3, whistle="mouth", puff=2))]
          + [("Point%d" % k, idle(2 * k, near=(-23.6, -46.4), point=True)) for k in range(2)]
          + [("Throw%d" % k, idle((k + 1) % 6, far=THROW_HANDS[k][0], lamp_bend=THROW_HANDS[k][1], near=THROW_WHISTLE,
                                   flame=3 if k < 3 else 2)) for k in range(4)]
          + [("Call%d" % k, idle(2 + k, whistle="mouth", puff=1 + k, far=(10.0, -61.4), lamp_bend=-1, flame=3)) for k in range(2)]
          + [("Tip0", idle(0, near=TIP_HANDS[0])), ("Tip1", idle(1, near=TIP_HANDS[1], cap=2)),
             ("Tip2", idle(2, near=TIP_HANDS[2], cap=1, head=1))]
          + [("Dying0", Pose(phase=0, head=1, near=(-8.4, -30.6), far=(11.0, -28.6), eyes=2, flame=2, exhaust=3)),
             ("Dying1", Pose(phase=1, head=2, slump=1, near=(-7.6, -29.0), far=(10.6, -27.4), eyes=1, flame=1, exhaust=2)),
             ("Dying2", Pose(phase=2, head=3, slump=2, near=(-7.0, -28.0), far=(10.2, -26.6), eyes=1, flame=0, exhaust=1)),
             ("Dying3", Pose(phase=3, head=4, slump=3, near=(-6.8, -27.2), far=(10.0, -25.8), eyes=0, flame=0, exhaust=0))])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}
SEQUENCES = ("Idle", "Whistle", "Point", "Throw", "Call", "Tip", "Dying")


# ================================================================================================
# The ghost train
# ================================================================================================
HEADINGS = [-90.0 + 22.5 * k for k in range(9)]
TRAIN_SCALE = 1.3
ENGINE_CELL = 60
CAR_CELL = 48


def train_xf(heading, cell):
    c = cell / 2.0
    return Xf.pose(heading, (0.0, 0.0), (c, c)).then(Xf(TRAIN_SCALE, 0.0, 0.0, TRAIN_SCALE, 0.0, 0.0))


def ghost_face(lo=1, hi=2):
    return face((-0.5, -0.6, 0.65), lo=lo, hi=hi, gain=1.25, ramp_len=4, snap=22.5)


def wheel(cv, xf, x, y, r):
    cv.part(xf, Ellipse(x, y, r, r), "verd", flat(1, bevel=False), rust=0.0)
    q = P(xf, (x, y))
    cv.put(q[0], q[1], V[3])


def engine(heading):
    """The engine at `heading`, its middle at the cell's centre. Returns the colour and glow canvases."""
    cv, gl = Canvas(), Canvas()
    xf = train_xf(heading, ENGINE_CELL)
    for wx in (-9.6, -4.0, 1.6):
        wheel(cv, xf, wx, 6.0, 2.7)
    wheel(cv, xf, 9.6, 7.2, 1.7)
    for k in range(12):                                            # the connecting rod across the drivers
        q = P(xf, (-9.6 + k * 1.0, 6.0))
        cv.put(q[0], q[1], S[1])
    cv.part(xf, box(-15.8, 2.6, 13.8, 4.2), "verd", flat(1), rust=0.0)
    boiler = cv.part(xf, box(-6.4, -5.4, 12.4, 2.6), "verd", cyl((-6.4, -1.4), (12.4, -1.4), 4.1, lo=1, hi=3, snap=22.5), rust=0.0)
    for bx in (-2.4, 3.0, 8.4):                                    # its bands glow
        for k in range(10):
            q = P(xf, (bx, -5.0 + k * 0.8))
            if q in boiler:
                cv.put_glow(q[0], q[1], V[3])
                gl.put_glow(q[0], q[1], V[3])
    cv.part(xf, Ellipse(12.6, -1.4, 2.0, 3.9), "verd", flat(1), rust=0.0)          # the smokebox's round front
    cv.part(xf, Ellipse(0.4, -5.6, 2.3, 1.5), "verd", flat(2), rust=0.0)           # the steam dome
    cv.part(xf, Poly([(8.2, -5.0), (10.4, -5.0), (10.8, -8.2), (13.0, -12.2), (5.6, -12.2), (7.8, -8.2)]), "verd", ghost_face(),
            rust=0.0)                                                                # the balloon stack
    cv.part(xf, box(5.2, -13.4, 13.4, -12.0), "verd", flat(2), rust=0.0)           # its rim
    cv.part(xf, Ellipse(4.2, -6.0, 1.2, 1.2), "verd", flat(2), rust=0.0)           # the bell
    cv.part(xf, box(-16.0, -9.0, -6.2, 2.6), "verd", ghost_face(), rust=0.0)       # the cab
    cv.part(xf, box(-17.6, -11.0, -5.0, -9.0), "verd", flat(2), rust=0.0)          # its roof
    for q in cv.raster(xf, box(-14.0, -7.2, -8.4, -3.0)):          # the cab window, lit from inside
        cv.put_glow(q[0], q[1], V[3])
        gl.put_glow(q[0], q[1], V[3])
    for (lx, ly) in ((-12.0, -5.6), (-11.4, -5.6), (-12.0, -4.6), (-11.4, -4.6), (-11.0, -3.6), (-12.6, -3.6), (-11.8, -6.6)):
        q = P(xf, (lx, ly))                                        # the ghost driver looking out
        cv.put_glow(q[0], q[1], V[1])
        gl.put_glow(q[0], q[1], V[1])
    cv.part(xf, box(11.4, -9.0, 15.6, -5.2), "verd", flat(1), rust=0.0)          # the box headlamp on the smokebox
    for q in cv.raster(xf, box(13.6, -8.2, 15.4, -6.0)):            # its lens: an ember eye (hostile)
        cv.put_glow(q[0], q[1], E[2])
        gl.put_glow(q[0], q[1], E[2])
    q = P(xf, (14.0, -7.6))
    cv.put_glow(q[0], q[1], E[3])
    gl.put_glow(q[0], q[1], E[3])
    catcher = cv.part(xf, Poly([(13.0, 2.6), (15.8, 2.6), (20.0, 8.6), (13.0, 8.6)]), "verd", flat(1), rust=0.0)
    for k in range(7):                                             # its slats
        q = P(xf, (14.2 + k * 0.9, 4.6 + k * 0.6))
        if q in catcher:
            cv.put(q[0], q[1], V[0])
    return cv, gl


def car(heading):
    """A passenger car at `heading`, its middle at the cell's centre."""
    cv, gl = Canvas(), Canvas()
    xf = train_xf(heading, CAR_CELL)
    for bx in (-8.0, 8.0):                                         # two bogies
        for wx in (-2.4, 2.4):
            wheel(cv, xf, bx + wx, 6.4, 1.8)
        cv.part(xf, box(bx - 4.0, 4.4, bx + 4.0, 5.6), "verd", flat(1, bevel=False), rust=0.0)
    cv.part(xf, box(-12.4, 3.6, 12.4, 5.0), "verd", flat(1), rust=0.0)             # the underframe
    for ex in (-14.6, 13.0):
        cv.part(xf, box(ex, 1.6, ex + 1.6, 3.2), "verd", flat(1, bevel=False), rust=0.0)   # the couplers
    body_ = cv.part(xf, box(-13.0, -6.6, 13.0, 3.8), "verd", ghost_face(), rust=0.0)
    cv.part(xf, Union(box(-13.6, -8.0, 13.6, -6.4), box(-11.2, -9.4, 11.2, -7.6)), "verd", flat(2), rust=0.0)   # the roof
    passengers = {0: ((0.8, -3.4), (1.6, -3.4), (0.8, -2.4), (1.6, -2.4), (0.4, -1.6), (2.0, -1.6)),
                  2: ((0.8, -3.0), (1.6, -3.0), (0.6, -2.0), (1.8, -2.0))}
    for w, wx in enumerate((-10.6, -4.8, 1.0, 6.8)):              # four lit windows, ghost passengers in two
        for q in cv.raster(xf, box(wx, -4.8, wx + 3.6, -1.0)):
            cv.put_glow(q[0], q[1], V[3])
            gl.put_glow(q[0], q[1], V[3])
        for (lx, ly) in passengers.get(w, ()):
            q = P(xf, (wx + lx, ly))
            cv.put_glow(q[0], q[1], V[1])
            gl.put_glow(q[0], q[1], V[1])
    for k in range(26):                                            # the waist band under the windows
        q = P(xf, (-12.6 + k, 0.6))
        if q in body_:
            cv.put(q[0], q[1], V[1])
    return cv, gl


def train_sheets(fn, cell):
    frames, glows = [], []
    for h in HEADINGS:
        cv, gl = fn(h)
        for (x, y) in list(cv.px):
            if not (0 <= x < cell and 0 <= y < cell):
                raise SystemExit("train pixel (%d, %d) outside its %d cell at heading %.1f" % (x, y, cell, h))
        frames.append(to_image(cv.px, 0, 0, cell, cell))
        glows.append(to_image(gl.glow, 0, 0, cell, cell))
    return vertical(frames), vertical(glows)


RAIL_CELL = 21


def rails():
    """The telegraph pieces (1x 21x21 cells): a level stretch of ghost track (two rails 20 px apart, the band the train
    fills, with a sleeper), the same upright, and a ring marker (a ghost-light dot) for the loop."""
    level_, upright, dot = Canvas(), Canvas(), Canvas()
    for x in range(8):
        for (y, col) in ((0, V[2]), (1, V[0]), (19, V[0]), (20, V[2])):
            level_.put(x, y, col)
            upright.put(y, x, col)
    for y in range(2, 19, 3):
        level_.put(3, y, V[1])
        level_.put(4, y, V[1])
        upright.put(y, 3, V[1])
        upright.put(y, 4, V[1])
    for (x, y, col) in ((10, 9, V[2]), (9, 10, V[2]), (10, 10, V[3]), (11, 10, V[2]), (10, 11, V[2]), (9, 9, V[1]), (11, 11, V[1]),
                        (11, 9, V[1]), (9, 11, V[1])):
        dot.put(x, y, col)
    return vertical([to_image(c.px, 0, 0, RAIL_CELL, RAIL_CELL) for c in (level_, upright, dot)])


FLAME = 12
FLAME_FRAMES = 4


# Ghost fire, drawn by hand (12x12 at 1x): a = dark rim (verd 0), b = flame (verd 2), c = bright flame (verd 3), d = the
# white-hot heart (steam 3). Its three tongues lick up in turn; the heart stays put (stable pixels).
FLAME_ART = (
    ("....a.......",
     "...aba...a..",
     "...abba.aba.",
     "..abcbaabba.",
     "..abccbbcba.",
     ".abccccccba.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
    (".......a....",
     "..a...aba...",
     ".aba.abba...",
     ".abbaabcba..",
     ".abcbbccba..",
     ".abccccccba.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
    ("......a.....",
     ".....aba....",
     "..a..abba...",
     ".aba.abcba..",
     ".abbabccba..",
     ".abcbcccbaa.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
    ("............",
     "...a....a...",
     "..aba..aba..",
     "..abba.abba.",
     "..abcbabcba.",
     ".abccbbccba.",
     ".abccddccba.",
     ".abcddddcba.",
     ".abcddddcba.",
     "..abcddcba..",
     "...abccba...",
     "....aaaa...."),
)


def flame(k):
    cv = Canvas()
    cols = {"a": V[0], "b": V[2], "c": V[3], "d": S[3]}
    for y, row in enumerate(FLAME_ART[k]):
        for x, ch in enumerate(row):
            if ch in cols:
                cv.put(x, y, cols[ch])
    return to_image(cv.px, 0, 0, FLAME, FLAME)


# ================================================================================================
# The bag, the map icon, the gores
# ================================================================================================
def treasure_bag():
    """18x18: an indigo sack tied with a brass chain, the Conductor's whistle hanging from it, ghost mist curling out."""
    cv = Canvas()
    X = Xf()
    cv.part(X, Union(Ellipse(9.0, 11.8, 7.2, 5.6), Poly([(5.8, 6.2), (12.2, 6.2), (13.8, 9.0), (4.2, 9.0)])), "aether",
            dome(6.0, 8.6, 10.0, lo=1, hi=2, gain=1.3, bias=0.15), shadow=(1, 1), rust=0.0)
    cv.part(X, Poly([(6.6, 2.4), (11.4, 2.4), (12.2, 6.2), (5.8, 6.2)]), "aether", flat(2), rust=0.0)
    for x in range(5, 14):
        cv.put(x, 6, B[4] if x % 2 else B[3])                      # the brass chain round its neck
    for (x, y, col) in ((10, 7, B[2]), (10, 8, B[2]), (11, 9, B[4]), (12, 9, B[5]), (13, 9, B[3]), (11, 10, B[2]), (12, 10, B[2])):
        cv.put(x, y, col)                                          # the whistle hanging from it
    for (x, y, col) in ((8, 1, V[2]), (9, 0, V[3]), (7, 0, V[1]), (10, 1, V[2]), (9, 1, V[3])):
        cv.put(x, y, col)                                          # ghost mist out of its mouth
    for (x, y) in ((6, 12), (6, 13), (7, 14)):
        cv.put(x, y, A[2])                                          # a lit fold
    return to_image(cv.px, 0, 0, 18, 18)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def head_icon(mid):
    """20x20 (40 in game): the head and the cap of the Idle pose."""
    px = {q: c for q, c in mid.px.items() if q[1] <= -47 and q[0] >= -15}
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    im = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    part = crop(px)
    if part.width > 20 or part.height > 20:
        part = part.crop((max(0, part.width - 20), max(0, part.height - 20), part.width, part.height))
    im.alpha_composite(part, ((20 - part.width) // 2, (20 - part.height) // 2))
    return im


def gores(far, mid, near):
    cap = {q: c for q, c in mid.px.items() if q[1] <= -61 or (q[0] <= -11 and q[1] <= -57)}          # the crown and the visor
    head = {q: c for q, c in mid.px.items() if -61 < q[1] <= -47 and q[0] >= -12 and q not in cap}
    coat = {q: c for q, c in mid.px.items() if -47 < q[1] <= -17 and c in D + G + IV + K}
    lamp = {q: c for q, c in near.px.items() if q[1] >= -31 and q[0] >= 7}
    turbine_ = {q: c for q, c in mid.px.items() if q[1] > -16}
    return {"CursedConductor_GoreCap": crop(cap), "CursedConductor_GoreHead": crop(head), "CursedConductor_GoreCoat": crop(coat),
            "CursedConductor_GoreLantern": crop(lamp), "CursedConductor_GoreTurbine": crop(turbine_)}


# ================================================================================================
# The rift, the curse's icon and the bits of his death (2026-11-05)
# ================================================================================================
RIFT = 16
RIFT_FRAMES = 4


def rift(k):
    """A ghost rift opening where a ghost will rise (the ghost's spawn telegraph): a ring of ghost light that widens over
    four frames, a dark hollow inside, two motes rising; the last frame bright (it is coming). Drawn at full brightness
    from its own sheet (no glow sheet: it is light)."""
    cv = Canvas()
    c = RIFT / 2.0
    r = (2.6, 4.0, 5.4, 6.6)[k]
    for y in range(RIFT):
        for x in range(RIFT):
            dx, dy = x + 0.5 - c, (y + 0.5 - c) * 1.6               # flattened: a rift on the ground or in the air
            d = math.hypot(dx, dy)
            if r - 1.2 <= d <= r:
                lit_ = dx + dy < 0
                col = GH[5] if (k == 3 and lit_) else (GH[4] if lit_ else GH[3])
                cv.put(x, y, col)
            elif d < r - 1.2 and k >= 1:
                cv.put(x, y, GH[1] if d > r - 2.4 else GH[0])
    for (mx, my) in ((c - 2.0, c - 2.0 - k), (c + 1.5, c - 3.0 - k * 0.6)):
        q = (fl(mx), fl(my))
        if 0 <= q[0] < RIFT and 0 <= q[1] < RIFT:
            cv.put(q[0], q[1], GH[4])
    return to_image(cv.px, 0, 0, RIFT, RIFT)


def curse_icon():
    """16x16 (32 in game): a ghost-green punched ticket, the Conductor's Curse."""
    cv = Canvas()
    X = Xf.pose(-12.0, (8.0, 8.0), (0.0, 0.0))
    t = cv.part(X, box(2.0, 4.0, 14.0, 12.0), "ivory", face((-0.5, -0.6, 0.65), lo=2, hi=4, ramp_len=6, fixed=True), rust=0.0)
    for (lx, ly) in ((4.0, 6.0), (5.0, 6.0), (6.0, 6.0), (7.0, 6.0), (4.0, 8.0), (5.0, 8.0), (6.0, 8.0)):
        q = P(X, (lx + 0.5, ly + 0.5))
        if q in t:
            cv.put(q[0], q[1], IV[1])                              # the printed lines
    for q in cv.raster(X, Ellipse(11.0, 8.0, 1.6, 1.6)):
        cv.put(q[0], q[1], GH[0])                                  # the punched hole...
    for (lx, ly, k) in ((10.0, 6.0, 4), (12.0, 6.0, 3), (13.0, 9.0, 3), (9.0, 10.0, 4), (11.0, 11.0, 2)):
        q = P(X, (lx + 0.5, ly + 0.5))
        cv.put(q[0], q[1], GH[k])                                  # ...ghost light seeping out of it
    for x in range(2, 14):
        q = P(X, (x + 0.5, 4.5))
        if q in cv.px and x % 2 == 0:
            cv.put(q[0], q[1], GH[3])                              # a ghost-green edge: cursed
    return to_image(cv.px, 0, 0, 16, 16)


def rotor(k):
    """The vanes in the drum's window, frame k of ROTOR_FRAMES: VANES vanes round the drum, each a quarter of their
    spacing further round per frame (so the loop is seamless), projected onto its front half (foreshortened towards the
    edges: x = cx + R sin a); a vane facing the light (the left) is bright steel, one facing away dark; the gaps are the
    recess. Transparent outside the window, so the drum's own frame shows round it."""
    x0, y0, w, h = ROTOR
    cv = Canvas()
    R = w / 2.0
    cx = w / 2.0
    for v in range(VANES):
        a = 2.0 * math.pi * (v + k / ROTOR_FRAMES) / VANES
        if math.cos(a) <= 0.05:
            continue                                               # behind the drum
        x = int(math.floor(cx + R * math.sin(a) * 0.98))
        if not 0 <= x < w:
            continue
        side = math.sin(a)                                         # -1 left (lit) .. +1 right (shadow)
        top, body_ = (ST[8], ST[6]) if side < -0.35 else ((ST[7], ST[5]) if side < 0.35 else (ST[5], ST[3]))
        for y in range(h):
            cv.put(x, y, top if y == 1 else (body_ if y < h - 1 else ST[2]))
        if side < 0.2 and 0 <= x + 1 < w and (x + 1, 1) not in cv.px:
            cv.put(x + 1, 1, ST[2])                                # the vane's shadowed edge
    return to_image(cv.px, 0, 0, w, h)


def smoke_puff(k):
    """A soot puff, frame k of SMOKE_FRAMES (12x12 at 1x): small and dense out of the bell, lit ghost-green from below
    in the first two frames, then bigger, lighter, and breaking up (a part-space hash takes bites out of it); lit from
    the top-left; no outline (smoke), no semi-transparent pixels (the game fades it)."""
    cv = Canvas()
    r = (2.4, 3.4, 4.3, 5.0, 5.6)[k]
    c = SMOKE / 2.0
    for y in range(SMOKE):
        for x in range(SMOKE):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            d = math.hypot(dx, dy * 1.1)
            if d > r:
                continue
            if k >= 3:
                hsh = (x * 73 + y * 151 + k * 29) % 11
                if hsh < (3 if k == 3 else 6) and d > r * 0.45:
                    continue                                       # breaking up
            light = -(dx + dy) / max(0.001, r)
            shade = 1 + (k >= 2) + (1 if light > 0.25 else 0) + (1 if light > 0.75 else 0)
            col = ST[min(5, shade)]
            if k <= 1 and dy > r * 0.45:
                col = GH[2] if k == 0 else GH[1]                    # the cursed fire under it
            cv.put(x, y, col)
    return to_image(cv.px, 0, 0, SMOKE, SMOKE)


BITS = (("gilt", (3, 2), (8, 6, 4)), ("denim", (3, 3), (4, 3, 2)), ("steel", (2, 2), (7, 5, 3)), ("ghost", (2, 2), (5, 4, 3)),
        ("ivory", (2, 1), (5, 4, 3)), ("steel", (3, 2), (6, 4, 2)))


def bits():
    """Six tiny pieces of him (2-3 art px each) for the explosion when the last train hits him: brass, coat, plate, a
    wisp, a tooth, a bolt; lit top-left, a darker lower edge (no outline: they are specks)."""
    out = []
    for ramp, (w, h), (lit_, mid_, dark) in BITS:
        r = RAMP[ramp]
        cv = Canvas()
        for y in range(h):
            for x in range(w):
                cv.put(x, y, r[lit_] if (x == 0 and y == 0) else (r[dark] if y == h - 1 and h > 1 else r[mid_]))
        out.append(to_image(cv.px, 0, 0, w, h))
    return out


# ================================================================================================
# Export
# ================================================================================================
def body_box(mid):
    """The hitbox (1x): the coat, the head and the cap (not the visor's tip) down to the hem, and since 2026-11-05b the
    turbine under it to the bell's mouth: left, right, top, hem, bottom."""
    pts = [q for q in mid.px if q[1] <= HEM_Y]
    xs = sorted(x for (x, _) in pts)
    bottom = max(y for (_, y) in mid.px if y < 1) + 1              # the tail cone's tip (row 0: the ground clip drops below)
    return xs[2], xs[-1] + 1, min(y for (_, y) in pts), int(HEM_Y), bottom


COLUMNS = 2                      # the grid wraps: 25 frames in one column would be 2750 px tall (D0: textures <= 2048)


def grid_columns(canvases, cell, glow=False):
    """grid_layer's equal cells, wrapped into COLUMNS columns, 1 px (2 px in game) right of and under each cell
    (DepthLayers.DrawCell with columns); every pixel must fit in its cell."""
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((w + 1) * COLUMNS, (h + 1) * rows), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        one = grid_layer([cv], cell, glow=glow)
        out.alpha_composite(one.crop((0, 0, w, h)), ((k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)))
    return out


def write_rig(path, cell, frames):
    w, h, ox, oy = cell
    idle = frames[INDEX["Idle0"]]
    left, right, top, hem, bottom = body_box(idle[1])
    pts = idle[4]
    throw = frames[INDEX["Throw2"]][4]["lamp"]
    blow = frames[INDEX["Whistle2"]][4]["whistle"]
    call = frames[INDEX["Call0"]][4]["lamp"]
    finger = frames[INDEX["Point0"]][4]["finger"]
    eyes = EYES
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def pt(name, p):
        return "%sX = %d, %sY = %d" % (name, round(p[0] * 2), name, round(p[1] * 2))
    L = ["// <auto-generated> by art/bosses/cursedconductor/make_conductor_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Bosses.CursedConductor",
         "{",
         "\t/// <summary>The Cursed Conductor's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal",
         "\t/// cells in <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is under his turbine's",
         "\t/// exhaust bell. Body* is his hitbox from the origin (the coat, the head and the cap, and the turbine down to",
         "\t/// <see cref=\"BodyBottom\"/>); the points are from the origin, facing left: the lantern at rest, thrown (Throw2) and",
         "\t/// raised (Call0), the whistle blowing (Whistle2), the pointing finger (Point0), the eyes, the exhaust's mouth. The",
         "\t/// vane window (Rotor*) is the turbine's overlay sheet, drawn at the window moved by <see cref=\"Bob\"/> (each frame's",
         "\t/// whole-pixel bob). The ghost train's sheets hold <see cref=\"Headings\"/> headings each (straight up to straight",
         "\t/// down, facing right, 22.5 degrees apart).</summary>",
         "\tpublic static class CursedConductorRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
         % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
         "\t\tpublic const int %s;" % ", ".join(seq[:4]),
         "\t\tpublic const int %s;" % ", ".join(seq[4:]),
         "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, HemY = %d, BodyBottom = %d;" % (left * 2, right * 2, top * 2, hem * 2,
                                                                                                    bottom * 2),
         "\t\tpublic const int %s, %s;" % (pt("Lantern", pts["lamp"]), pt("Throw", throw)),
         "\t\tpublic const int %s, %s;" % (pt("Raised", call), pt("Whistle", blow)),
         "\t\tpublic const int %s, %s;" % (pt("Finger", finger), pt("Eyes", eyes)),
         "\t\tpublic const int Headings = %d, EngineCell = %d, CarCell = %d, RailCell = %d, FlameCell = %d, FlameFrames = %d;"
         % (len(HEADINGS), ENGINE_CELL * 2, CAR_CELL * 2, RAIL_CELL * 2, FLAME * 2, FLAME_FRAMES),
         "\t\tpublic const int RiftCell = %d, RiftFrames = %d, Bits = %d;" % (RIFT * 2, RIFT_FRAMES, len(BITS)),
         "\t\tpublic const int %s, RotorX = %d, RotorY = %d, RotorWidth = %d, RotorHeight = %d, RotorFrames = %d;"
         % (pt("Exhaust", EXHAUST), ROTOR[0] * 2, ROTOR[1] * 2, ROTOR[2] * 2, ROTOR[3] * 2, ROTOR_FRAMES),
         "\t\tpublic const int SmokeCell = %d, SmokeFrames = %d;" % (SMOKE * 2, SMOKE_FRAMES),
         "\t\t/// <summary>Each frame's whole-pixel bob (game px, + down): the turbine's vanes ride it.</summary>",
         "\t\tpublic static readonly sbyte[] Bob = { %s };" % ", ".join(str(int(fr[4]["bob"]) * 2) for fr in frames),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("", 1), ("_Near", 2)):
        export(grid_columns([fr[idx] for fr in frames], cell), OUT + "CursedConductor%s.png" % suffix)
    far_sheet = os.path.join(ROOT, OUT + "CursedConductor_Far.png")
    if os.path.exists(far_sheet):
        os.remove(far_sheet)                                       # nothing is behind him any more
        print("removed", OUT + "CursedConductor_Far.png")
    export(grid_columns([fr[3] for fr in frames], cell, glow=True), OUT + "CursedConductor_Glow.png")
    export(vertical([rotor(k) for k in range(ROTOR_FRAMES)]), OUT + "CursedConductor_Rotor.png")
    export(vertical([smoke_puff(k) for k in range(SMOKE_FRAMES)]), OUT + "CursedConductor_Smoke.png")
    write_rig(OUT + "CursedConductorRigData.cs", cell, frames)
    export(head_icon(frames[0][1]), OUT + "CursedConductor_Head_Boss.png")
    sheet, glow = train_sheets(engine, ENGINE_CELL)
    export(sheet, OUT + "Projectiles/GhostTrain.png")
    export(glow, OUT + "Projectiles/GhostTrain_Glow.png")
    sheet, glow = train_sheets(car, CAR_CELL)
    export(sheet, OUT + "Projectiles/GhostTrain_Car.png")
    export(glow, OUT + "Projectiles/GhostTrain_CarGlow.png")
    export(rails(), OUT + "Projectiles/GhostTrain_Rail.png")
    export(vertical([flame(k) for k in range(FLAME_FRAMES)]), OUT + "Projectiles/ConductorFlame.png")
    export(treasure_bag(), OUT + "Items/CursedConductorBag.png")
    export(vertical([rift(k) for k in range(RIFT_FRAMES)]), OUT + "Projectiles/GhostRift.png")
    export(curse_icon(), OUT + "Buffs/ConductorCurse.png")
    for k, im in enumerate(bits()):
        export(im, OUT + "Gores/CursedConductor_Bit%d.png" % k)
    for name, im in gores(frames[0][0], frames[0][1], frames[0][2]).items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    """Every frame on a dark and a light backdrop, the train's headings, the flame and the bag, 3x."""
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    w, h, ox, oy = cell
    cols = 9
    rows = (len(FRAMES) + cols - 1) // cols
    panels = []
    for bg in ((36, 40, 48, 255), (150, 180, 210, 255)):
        tile = Image.new("RGBA", (w * cols, h * rows), bg)
        for k, fr in enumerate(frames):
            t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            for n_, cv in enumerate(fr[:3]):
                t.alpha_composite(to_image(cv.px, -ox, -oy, w, h))
                if n_ == 1:                                        # the vanes over the drum, under the near plane
                    t.alpha_composite(rotor(k % ROTOR_FRAMES), (ox + ROTOR[0], oy + ROTOR[1] + int(fr[4]["bob"])))
            t.alpha_composite(to_image(fr[3].glow, -ox, -oy, w, h))
            tile.alpha_composite(t, ((k % cols) * w, (k // cols) * h))
        panels.append(tile)
    trains = Image.new("RGBA", (ENGINE_CELL * 9 + 8, ENGINE_CELL + CAR_CELL + 4), (36, 40, 48, 255))
    for k, hd in enumerate(HEADINGS):
        cv, _ = engine(hd)
        trains.alpha_composite(to_image(cv.px, 0, 0, ENGINE_CELL, ENGINE_CELL), (k * ENGINE_CELL, 0))
        cv, _ = car(hd)
        trains.alpha_composite(to_image(cv.px, 0, 0, CAR_CELL, CAR_CELL), (k * ENGINE_CELL, ENGINE_CELL + 2))
    extras = Image.new("RGBA", (trains.width, 24), (36, 40, 48, 255))
    for k in range(FLAME_FRAMES):
        extras.alpha_composite(flame(k), (2 + k * 12, 2))
    extras.alpha_composite(treasure_bag(), (60, 2))
    extras.alpha_composite(rails(), (90, 0)) if False else None
    W = max(panels[0].width, trains.width)
    sheet = Image.new("RGBA", (W, panels[0].height * 2 + trains.height + extras.height), (0, 0, 0, 255))
    sheet.paste(panels[0], (0, 0))
    sheet.paste(panels[1], (0, panels[0].height))
    sheet.paste(trains, (0, panels[0].height * 2))
    sheet.paste(extras, (0, panels[0].height * 2 + trains.height))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)
    print("preview", path, cell)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
