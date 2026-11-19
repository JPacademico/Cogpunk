"""The Jade Token and its spirit fox (2026-11-18). Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--preview FILE] [--gif FILE]

User, 2026-11-18: "on the top chest of the main mansion on coghaven add a new pet item that allways spawn there called "jade
token" it should give the player a small jade colored spirit fox (ensure seamless animations and behavior like our other pet
from the mod) that emits a bit of light". Drawn at 1x in the Cogpunk palette with art/bosses/trashtr0m/rig.py's parts
(Canvas, Ellipse, Poly, Capsule, dome/flat shaders, finish), exported 2x (D4).

The fox (redrawn 2026-11-18 after the user's own design, reference/jade_fox_user_2026-11-18.webp: "the fox spirit design is
underwhelming use the design i provided ... (resize and update if needed)"; shrunk as it is, the painting turned to noise at
pet size, so it is redrawn at that size with its parts; the first 2026-11-18 fox is in previous/): pale sage fur (a new Sage
ramp) lit from the top-left, emerald ears and a stripe down its back (a new Emerald ramp), a fluffy ruff, a gilt headpiece
with a jade gem on its brow and a gilt mask line by its glowing eye, a gilt collar with a jade gem and tassel, gilt anklets on
emerald socks, a big pale brush of a tail with a gilt swirl that turns into three tongues of emerald spirit fire, two leaves
drifting round them (the fire's core, its eye and the leaves are also on the glow sheet, drawn full-bright in game: it gives
off a little light). Faces right (the pet flips by direction),
its feet on the cell's bottom row. One `fox(pose)` draws every frame from a few numbers (body bob, stretch, the four feet,
the head, the tail's sway and lift, lying, eyes), so the loops are seamless (each loop's last frame leads into its first):
  Idle 0-3       standing, the tail sweeping, an ear twitch          (loop)
  Trot 4-9       a six-frame trot, diagonal pairs, a one-pixel bob   (loop, by distance travelled)
  Float 10-13    the spirit float when it falls far behind: paws tucked, the tail streaming and rippling (loop)
  Settle 14-15   sitting, then lying down
  Sleep 16-17    curled up, the tail round its nose, breathing       (loop)
  Wake 18-20     the head up, a stretch (front paws out, rump up), standing
Outputs (Content/Coghaven/Pets/): JadeFoxPet.png + JadeFoxPet_Glow.png (21 frames of CELL_W x CELL_H (46 x 30), 1 px apart), JadeToken.png
(the item: a jade coin with a fox's head, a gilt rim), JadeFoxBuff.png (the buff icon).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP, Xf, Poly, Ellipse, Capsule, Union, Canvas, flat, dome, finish  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Coghaven/Pets/"
GH, G, IV, AE, EM, SG = (RAMP[k] for k in ("ghost", "gilt", "ivory", "aether", "emerald", "sage"))
CELL_W, CELL_H = 46, 30                             # 1x; the feet on row CELL_H - 1
OX, OY = 24, 29                                     # the cell px of the rig origin (between the feet, on the ground)


class Pose:
    def __init__(self, bob=0.0, stretch=0.0, feet=None, head=(0.0, 0.0), tail=0.0, lift=0.0, lying=0.0, eyes=1, ears=0, tuck=0.0,
                 wisps=0, curl=0.0, flame=0):
        self.bob, self.stretch = bob, stretch
        self.feet = feet or ((3.6, 0.0), (2.4, 0.0), (-4.4, 0.0), (-5.6, 0.0))   # near front, far front, near hind, far hind
        self.head = head                            # the head's offset from its rest
        self.tail, self.lift = tail, lift           # -1..1 sway of the tail's end, 0..1 how high it is carried
        self.lying = lying                          # 0 standing .. 1 lying flat
        self.eyes = eyes                            # 1 open, 0 shut
        self.ears = ears                            # 0 up, 1 the near ear flicked back
        self.tuck = tuck                            # 0..1 paws drawn up under it (the float)
        self.wisps = wisps                          # 0..3: which spirit wisps under it (the float)
        self.curl = curl                            # 0..1 the tail wrapped round to its nose (asleep)
        self.flame = flame                          # 0..3: the spirit flame's flicker (and its leaves' drift)


def _leg(cv, hip, foot, far):
    """A slender leg (sage; its lower part an emerald sock, a gilt anklet with a jade bead on the near legs; no outline: it is
    two pixels wide)."""
    cv.part(Xf(), Capsule(hip, foot, 1.0), "sage", flat(2 if far else 3, bevel=False), rust=0.0, outline=False)
    fx, fy = foot
    span = max(1.0, fy - hip[1])
    for y in range(int(math.floor(fy)) - 3, int(math.floor(fy)) + 1):
        for x in range(int(math.floor(fx)) - 2, int(math.floor(fx)) + 3):
            if (x, y) in cv.px and cv.px[(x, y)] in SG:
                cv.put(x, y, EM[1] if far else EM[2])
    ay = int(math.floor(fy)) - 4
    for x in range(int(math.floor(fx)) - 2, int(math.floor(fx)) + 3):
        if (x, ay) in cv.px and cv.px[(x, ay)] in SG:
            cv.put(x, ay, G[5] if far else G[7])
    if not far:
        q = (int(math.floor(fx + (hip[0] - fx) * 4.0 / span)), ay)
        if q in cv.px:
            cv.put(q[0], q[1], EM[5])


def tail_points(p, n=7):
    """The tail's spine from its root to where the fur becomes flame: up and back from the rump, its end swaying; curled round
    under its nose when asleep."""
    root = (-6.4 - p.stretch, -9.4 + p.bob + p.lying * 4.0)
    pts = []
    for k in range(n):
        t = k / (n - 1)
        if p.curl > 0:
            a = math.radians(200 - 230 * t * p.curl)
            r = 5.5 + 1.5 * (1 - t)
            pts.append((root[0] + 5.5 + math.cos(a) * r, root[1] + 1.0 + math.sin(a) * r * 0.32))
            continue
        x = root[0] - 6.4 * t + p.tail * 1.4 * t * t
        y = root[1] - (2.0 + 6.0 * p.lift) * t ** 1.1 + 1.6 * t * t * (1 - p.lift) + math.sin(t * math.pi) * p.tail
        pts.append((x, y))
    return pts


FLAME_TONGUES = ((-0.6, -1.0, 7.0), (-1.0, -0.2, 5.2), (0.2, -1.0, 4.2))    # direction (x, y) and length of each tongue


def flame(cv, glow, tip, p, lying):
    """The spirit flame off the tail's end (the user's design): three tongues of emerald fire licking up and back, each a
    teardrop with a bright core, flickering with `p.flame`; its core and tips on the glow sheet; two leaves drifting by."""
    tx, ty = tip
    k = p.flame
    for n, (dx, dy, ln) in enumerate(FLAME_TONGUES):
        if lying:
            ln *= 0.6
        wob = (0.0, 0.6, 0.0, -0.6)[(k + n) % 4]
        length = ln * (1.0 + (0.12 if (k + n) % 2 else -0.08))
        norm = math.hypot(dx, dy) or 1.0
        ux, uy = dx / norm, dy / norm
        nx, ny = -uy, ux
        steps = int(length * 3) + 1
        for s in range(steps + 1):
            t = s / steps
            cx = tx + ux * length * t + nx * wob * math.sin(t * math.pi)
            cy = ty + uy * length * t + ny * wob * math.sin(t * math.pi)
            r = 2.3 * (1.0 - t) ** 0.8 + 0.3
            for yy in range(int(math.floor(cy - r)), int(math.ceil(cy + r)) + 1):
                for xx in range(int(math.floor(cx - r)), int(math.ceil(cx + r)) + 1):
                    d = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                    if d > r:
                        continue
                    inner = d < r * 0.45
                    col = EM[6] if inner and t < 0.5 else EM[5] if inner or t > 0.75 else EM[4] if d < r * 0.8 else EM[3]
                    old = cv.px.get((xx, yy))
                    if old is None or old in SG or (old in EM and EM.index(old) < EM.index(col)):
                        cv.put(xx, yy, col)
                    if col in (EM[6], EM[5]):
                        glow.put_glow(xx, yy, col)
    for n in range(2):                                          # two leaves drifting round the flame
        a = k * 0.9 + n * 3.1
        lx = int(math.floor(tx - 4.0 - n * 3.0 + math.cos(a) * 2.0))
        ly = int(math.floor(ty - 6.0 + n * 4.0 + math.sin(a) * 1.5))
        for (ddx, ddy, col) in ((0, 0, EM[5]), (1, 0, EM[4]), (1, -1, EM[5]), (0, 1, EM[3])):
            glow.put_glow(lx + ddx, ly + ddy, col)


def brush(cv, p, by):
    """The tail: a "C" of pale fur curled up over the rump (four puffs), swaying with `p.tail` and carried by `p.lift`; asleep
    (`p.curl`) it lies wrapped round in front, low. Returns (its pixels, the point its flame rises from)."""
    sway, lift = p.tail, p.lift
    if p.curl > 0:
        cx, cy = 1.0, by + 0.8
        puffs = ((cx - 6.0, cy - 0.8, 3.0), (cx - 2.0, cy + 0.2, 2.8), (cx + 2.4, cy + 0.4, 2.4), (cx + 5.6, cy, 1.9))
        tip = (cx - 7.6, cy - 2.0)
    else:
        cx, cy = -8.6 - p.stretch + sway * 0.6, by - 4.2 - lift * 1.6 + abs(sway) * 0.3
        puffs = ((cx + 2.0, cy + 3.4, 3.6), (cx - 0.6, cy + 0.6, 4.8), (cx - 0.2, cy - 3.4, 4.0), (cx + 2.6, cy - 5.2, 2.8))
        tip = (cx - 2.4 + sway * 0.6, cy - 5.6)
    shape = Union(*[Ellipse(x, y, r, r * 0.92) for (x, y, r) in puffs])
    fur = cv.part(Xf(), shape, "sage", dome(cx - 1.8, cy - 2.6, 6.4, lo=2, hi=5, gain=1.35, fixed=True), rust=0.0)
    for (x, y) in list(fur):                                # the far side greening into flame
        dx, dy = x + 0.5 - tip[0], y + 0.5 - tip[1]
        if dx * dx + dy * dy < 3.4 ** 2:
            cv.put(x, y, EM[3] if (x + y) % 2 else EM[4])
    gx, gy = int(round(cx)), int(round(cy))
    swirl = ((0, 0, G[7]), (1, -1, G[7]), (2, -1, G[6]), (3, 0, G[5]), (3, 1, G[5]), (2, 2, G[4]), (0, 2, G[4]), (-1, 1, G[5]))
    for (dx, dy, col) in swirl:                             # the gilt swirl in the curl
        if (gx + dx, gy + dy) in fur:
            cv.put(gx + dx, gy + dy, col)
    return fur, tip


def fox(p):
    """(canvas, glow) for a pose; rig space: the origin between the feet on the ground, x right (it faces right)."""
    cv, glow = Canvas(), Canvas()
    by = -7.6 + p.bob + p.lying * 3.4                        # the body's centre
    bx = 0.0
    sq = 1.0 - 0.3 * p.lying
    hips = ((3.4 + p.stretch * 0.5, by + 2.0), (2.4 + p.stretch * 0.5, by + 1.8), (-3.6 - p.stretch * 0.5, by + 2.0),
            (-4.6 - p.stretch * 0.5, by + 1.8))
    if p.lying < 0.5:                                       # the far legs, behind everything
        for k in (1, 3):
            fx, fy = p.feet[k]
            _leg(cv, hips[k], (fx, min(fy, 0.0) - p.tuck * 4.0 - 0.1), True)
    # the tail (the user's design): a big round brush of pale fur curled up behind it, as big as its body, a gilt swirl in the
    # curl, its far side greening into the spirit flame that rises off it
    tail, tip = brush(cv, p, by)
    # the body: pale fur, emerald along its back, a gilt swirl on the hip
    body = cv.part(Xf(), Ellipse(bx, by, 5.6 + p.stretch, 3.8 * sq), "sage", dome(bx - 2.2, by - 2.4, 6.6, lo=2, hi=5, gain=1.4, fixed=True),
                   rust=0.0)
    top = {}
    for (x, y) in body:
        if x not in top or y < top[x]:
            top[x] = y
    for (x, y) in body:
        if y == top[x] and x < bx + 4:
            cv.put(x, y, EM[3])
    hx0, hy0 = int(math.floor(bx - 4.0 - p.stretch)), int(math.floor(by))
    for (dx, dy, col) in ((0, 0, G[7]), (1, -1, G[7]), (2, -1, G[6]), (3, 0, G[5]), (1, 1, G[5]), (0, 1, G[4])):
        if (hx0 + dx, hy0 + dy) in body:
            cv.put(hx0 + dx, hy0 + dy, col)
    # the ruff: fluffy pale fur at the chest under the head
    rx_, ry_ = 5.2 + p.stretch, by - 2.4
    cv.part(Xf(), Union(Ellipse(rx_, ry_, 4.2, 4.0), Ellipse(rx_ + 0.6, ry_ + 3.0, 3.4, 2.6), Ellipse(rx_ - 0.8, ry_ - 3.0, 3.6, 3.0)),
            "sage", dome(rx_ - 1.6, ry_ - 2.0, 5.2, lo=3, hi=5, gain=1.15, fixed=True), rust=0.0)
    if p.lying < 0.5:                                       # the near legs
        for k in (0, 2):
            fx2, fy2 = p.feet[k]
            _leg(cv, hips[k], (fx2, min(fy2, 0.0) - p.tuck * 4.0 - 0.1), False)
    else:
        for x in (3, 4, 5, 6, 7):                               # the front paws out on the ground
            cv.put(x + int(p.stretch), -1, SG[3] if x < 6 else EM[2])
    # the head: a pale fox face, a pointed muzzle, a dark nose; big emerald ears (the near one pale inside, the far one gilt-
    # lined); the gilt headpiece with its jade gem on the brow
    hx, hy = 8.4 + p.stretch + p.head[0], by - 8.4 + p.head[1] + p.lying * 1.6
    cv.part(Xf(), Union(Ellipse(hx, hy, 4.6, 4.0), Poly([(hx + 2.4, hy - 0.2), (hx + 6.8, hy + 1.8), (hx + 2.0, hy + 3.2)])), "sage",
            dome(hx - 1.6, hy - 1.8, 5.8, lo=3, hi=5, gain=1.25, fixed=True), rust=0.0)
    for (ex, back, far) in ((hx - 2.8, 0, True), (hx + 1.2, p.ears, False)):
        etip = (ex - 0.2 - back * 1.8, hy - 9.4 + back * 2.4)
        outer = Poly([(ex - 2.8, hy - 2.2), (ex + 2.6, hy - 2.6), etip])
        ear = cv.part(Xf(), outer, "emerald", flat(2 if far else 3, bevel=False), rust=0.0)
        inner = cv.raster(Xf(), Poly([(ex - 1.2, hy - 2.6), (ex + 1.2, hy - 2.8), (ex - 0.1 - back * 1.4, hy - 7.6 + back * 2.0)]))
        for (x, y) in inner:                                     # a pale inside with a gilt rim (both ears, the user's design)
            if (x, y) in ear:
                cv.put(x, y, SG[4] if not far else SG[3])
        for (x, y) in inner:
            if (x + 1, y) in ear and (x + 1, y) not in inner:
                cv.put(x + 1, y, G[6] if not far else G[5])
    for dx in range(-2, 3):                                     # the headpiece's band
        cv.put(int(math.floor(hx)) + dx, int(math.floor(hy - 2.2 - dx * 0.2)), G[7] if dx < 1 else G[5])
    gx, gy = int(math.floor(hx)), int(math.floor(hy - 3.4))
    for (dx, dy, col) in ((0, 0, EM[5]), (0, 1, EM[4]), (-1, 1, G[6]), (1, 1, G[5]), (0, 2, EM[3])):
        cv.put(gx + dx, gy + dy, col)
    cv.put(int(math.floor(hx + 5.8)), int(math.floor(hy + 1.2)), EM[0])                       # the nose
    # the collar: a gilt band over the ruff, a jade gem and its little tassel
    cy0 = by - 3.6
    for dx in range(0, 6):
        cv.put(int(math.floor(rx_ - 2.4 + dx)), int(math.floor(cy0 + dx * 0.25)), G[7] if dx < 3 else G[5])
    gx2, gy2 = int(math.floor(rx_ + 1.4)), int(math.floor(cy0 + 1.2))
    for (dx, dy, col) in ((0, 0, EM[5]), (1, 0, EM[4]), (0, 1, EM[3]), (1, 1, EM[2]), (0, 2, EM[3]), (0, 3, EM[2])):
        cv.put(gx2 + dx, gy2 + dy, col)
    finish(cv)
    # the eye (stamped after the finish), glowing; the mask's gilt line by it
    ex, ey = int(math.floor(hx + 1.8)), int(math.floor(hy - 0.6))
    for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (2, -1), (-1, 0), (2, 0)):    # the gilt mask round the eye
        cv.put(ex + dx, ey + dy, G[7] if dy < 0 else G[5])
    if p.eyes:
        for (dx, dy, col) in ((0, 0, EM[6]), (1, 0, EM[5]), (0, 1, EM[4]), (1, 1, EM[1])):
            cv.put_glow(ex + dx, ey + dy, col)
            glow.put_glow(ex + dx, ey + dy, col)
    else:
        cv.put(ex, ey + 1, EM[1])
        cv.put(ex + 1, ey + 1, EM[1])
    flame(cv, glow, tip, p, p.lying > 0.5)
    for k in range(p.wisps):                                    # spirit wisps under it as it floats
        for (dx, dy, c) in ((-4 + k * 4, 1, EM[5]), (-3 + k * 4, 2, EM[4])):
            cv.put_glow(dx, int(by) + 5 + dy, c)
            glow.put_glow(dx, int(by) + 5 + dy, c)
    return cv, glow


def trot(k):
    """Six-frame trot: diagonal pairs (near front with far hind) swing together; the body bobs a pixel at mid-stride."""
    ph = k / 6.0 * 2 * math.pi

    def foot(base, phase):
        swing = math.sin(ph + phase)
        return (base + 1.8 * swing, -max(0.0, math.cos(ph + phase)) * 1.6)
    feet = (foot(3.6, 0.0), foot(2.4, math.pi), foot(-4.4, math.pi), foot(-5.6, 0.0))
    return Pose(bob=-0.6 if k % 3 == 1 else 0.0, feet=feet, tail=math.sin(ph) * 0.6, lift=0.45, head=(0.0, 0.5 if k % 3 == 1 else 0.0),
                flame=k % 4)


POSES = (
    [Pose(tail=s, lift=0.6, ears=1 if k == 2 else 0, flame=k) for k, s in enumerate((0.0, 0.5, 0.9, 0.5))]               # idle
    + [trot(k) for k in range(6)]                                                                                         # trot
    + [Pose(bob=-1.4, stretch=1.0, tuck=1.0, tail=s, lift=0.15, wisps=w, flame=k)
       for k, (s, w) in enumerate(((-0.8, 1), (0.0, 2), (0.8, 3), (0.0, 2)))]                                             # float
    + [Pose(bob=1.0, lift=0.35, head=(-0.4, 0.8), flame=1), Pose(lying=1.0, lift=0.0, head=(0.4, 1.2), flame=2)]           # settle
    + [Pose(lying=1.0, curl=1.0, eyes=0, head=(0.4, 1.8), flame=0), Pose(lying=1.0, bob=-0.5, curl=1.0, eyes=0, head=(0.4, 1.6), flame=2)]
    + [Pose(lying=1.0, lift=0.2, head=(0.6, -0.4), flame=1),
       Pose(bob=0.8, stretch=1.0, feet=((5.8, 0.0), (5.0, 0.0), (-4.4, 0.0), (-5.6, 0.0)), head=(0.6, 1.2), lift=0.9, flame=3),
       Pose(lift=0.6, flame=0)]                                                                                           # wake
)
FRAMES = len(POSES)


def sheet(glow=False):
    im = Image.new("RGBA", (CELL_W, (CELL_H + 1) * FRAMES), (0, 0, 0, 0))
    for k, p in enumerate(POSES):
        cv, gl = fox(p)
        src = gl.glow if glow else cv.px
        for (x, y), c in src.items():
            cx, cy = x + OX, y + OY
            if not (0 <= cx < CELL_W and 0 <= cy < CELL_H):
                raise SystemExit("frame %d: pixel (%d, %d) outside the %dx%d cell" % (k, x, y, CELL_W, CELL_H))
            im.putpixel((cx, cy + k * (CELL_H + 1)), tuple(c) + (255,))
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
        cv.put(x + 0, y + 0, c)
    return cv


def buff_icon():
    """The buff: the fox's head, its eye alight, the spirit flame of its tail curling behind."""
    cv = Canvas()
    p = Pose(lift=0.9, tail=0.6)
    fx, gl = fox(p)
    for (x, y), c in fx.px.items():
        if y < -3:
            cv.put(x + 1, y + 13, c)
    return cv


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
        OUT + "JadeFoxBuff.png": boxed(buff_icon(), 16, 16),
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
        sc = 6
        cols = 7
        rows = (FRAMES + cols - 1) // cols
        sheet_im = Image.new("RGBA", (cols * (CELL_W * sc + 8), rows * (CELL_H * sc + 8)), (30, 30, 36, 255))
        for k in range(FRAMES):
            cell = Image.new("RGBA", (CELL_W, CELL_H), (30, 30, 36, 255))
            cell.alpha_composite(base.crop((0, k * (CELL_H + 1), CELL_W, k * (CELL_H + 1) + CELL_H)))
            cell.alpha_composite(gl.crop((0, k * (CELL_H + 1), CELL_W, k * (CELL_H + 1) + CELL_H)))
            sheet_im.paste(cell.resize((CELL_W * sc, CELL_H * sc), Image.NEAREST), ((k % cols) * (CELL_W * sc + 8), (k // cols) * (CELL_H * sc + 8)))
        sheet_im.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
