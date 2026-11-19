"""The Jade Token and its spirit fox (2026-11-18). Run from the repo root:

    python -P art/coghaven/make_jade_fox_art.py [--preview FILE] [--gif FILE]

User, 2026-11-18: "on the top chest of the main mansion on coghaven add a new pet item that allways spawn there called "jade
token" it should give the player a small jade colored spirit fox (ensure seamless animations and behavior like our other pet
from the mod) that emits a bit of light". Drawn at 1x in the Cogpunk palette with art/bosses/trashtr0m/rig.py's parts
(Canvas, Ellipse, Poly, Capsule, dome/flat shaders, finish), exported 2x (D4).

The fox: a small fox of carved jade light (Ghost ramp, lit as domes in each part's own space from the top-left), a pale
blaze on its chest, dark jade ear tips and socks, a big brush of a tail ending in a spirit flame (the flame and its eye are
also on the glow sheet, drawn full-bright in game: it gives off a little light). Faces right (the pet flips by direction),
its feet on the cell's bottom row. One `fox(pose)` draws every frame from a few numbers (body bob, stretch, the four feet,
the head, the tail's sway and lift, lying, eyes), so the loops are seamless (each loop's last frame leads into its first):
  Idle 0-3       standing, the tail sweeping, an ear twitch          (loop)
  Trot 4-9       a six-frame trot, diagonal pairs, a one-pixel bob   (loop, by distance travelled)
  Float 10-13    the spirit float when it falls far behind: paws tucked, the tail streaming and rippling (loop)
  Settle 14-15   sitting, then lying down
  Sleep 16-17    curled up, the tail round its nose, breathing       (loop)
  Wake 18-20     the head up, a stretch (front paws out, rump up), standing
Outputs (Content/Coghaven/Pets/): JadeFoxPet.png + JadeFoxPet_Glow.png (21 frames of CELL_W x CELL_H, 1 px apart), JadeToken.png
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
GH, G, IV, AE = (RAMP[k] for k in ("ghost", "gilt", "ivory", "aether"))
CELL_W, CELL_H = 34, 18                             # 1x; the feet on row CELL_H - 1
OX, OY = 18, 17                                     # the cell px of the rig origin (between the feet, on the ground)


class Pose:
    def __init__(self, bob=0.0, stretch=0.0, feet=None, head=(0.0, 0.0), tail=0.0, lift=0.0, lying=0.0, eyes=1, ears=0, tuck=0.0,
                 wisps=0, curl=0.0):
        self.bob, self.stretch = bob, stretch
        self.feet = feet or ((3.4, 0.0), (2.4, 0.0), (-3.6, 0.0), (-4.6, 0.0))   # near front, far front, near hind, far hind
        self.head = head                            # the head's offset from its rest
        self.tail, self.lift = tail, lift           # -1..1 sway of the tail's end, 0..1 how high it is carried
        self.lying = lying                          # 0 standing .. 1 lying flat
        self.eyes = eyes                            # 1 open, 0 shut
        self.ears = ears                            # 0 up, 1 the near ear flicked back
        self.tuck = tuck                            # 0..1 paws drawn up under it (the float)
        self.wisps = wisps                          # 0..3: which spirit wisps under it (the float)
        self.curl = curl                            # 0..1 the tail wrapped round to its nose (asleep)


def _leg(cv, hip, foot, far):
    """A slim jade leg from the body to the ground (no outline: two pixels wide, it would be all outline), a dark sock."""
    cv.part(Xf(), Capsule(hip, foot, 0.9), "ghost", flat(2 if far else 3, bevel=False), rust=0.0, outline=False)
    fx, fy = int(math.floor(foot[0])), int(math.floor(foot[1]))
    cv.put(fx, fy - 1, GH[1] if far else GH[2])
    cv.put(fx + 1, fy - 1, GH[1] if far else GH[2])


def tail_points(p, n=7):
    """The tail's spine from its root to the flame: up and back from the rump, its end swaying; curled round to the nose
    when asleep."""
    root = (-4.6 - p.stretch, -7.0 + p.bob + p.lying * 3.6)
    pts = []
    for k in range(n):
        t = k / (n - 1)
        if p.curl > 0:
            a = math.radians(200 - 240 * t * p.curl)               # round under the body to the front
            r = 4.5 + 1.5 * (1 - t)
            pts.append((root[0] + 4.5 + math.cos(a) * r, root[1] - 1.4 + math.sin(a) * r * 0.3))
            continue
        x = root[0] - 5.6 * t + p.tail * 1.4 * t * t
        y = root[1] - (1.6 + 4.6 * p.lift) * t ** 1.1 + 1.4 * t * t * (1 - p.lift) + math.sin(t * math.pi) * p.tail * 1.0
        pts.append((x, y))
    return pts


def fox(p):
    """(canvas, glow) for a pose; rig space: the origin between the feet on the ground, x right (it faces right)."""
    cv, glow = Canvas(), Canvas()
    by = -5.6 + p.bob + p.lying * 3.2                       # the body's centre
    bx = -0.6
    sq = 1.0 - 0.3 * p.lying
    hips = ((2.6 + p.stretch * 0.5, by + 1.4), (1.8 + p.stretch * 0.5, by + 1.2), (-3.4 - p.stretch * 0.5, by + 1.4), (-4.2 - p.stretch * 0.5, by + 1.2))
    if p.lying < 0.5:                                       # the far legs, a step darker, behind everything
        for k in (1, 3):
            fx, fy = p.feet[k]
            _leg(cv, hips[k], (fx, min(fy, 0.0) - p.tuck * 3.0 - 0.1), True)
    # the tail: one fluffy shape (a union of puffs along its spine), its tip pale, the spirit flame on the glow sheet
    pts = tail_points(p)
    radii = [2.0, 2.8, 3.2, 3.3, 3.0, 2.4, 1.6]
    scale = 1.0 - 0.25 * p.curl
    shape = Union(*[Ellipse(x, y, radii[k] * scale, radii[k] * scale * 0.9) for k, (x, y) in enumerate(pts)])
    cx_t, cy_t = pts[3]
    tail = cv.part(Xf(), shape, "ghost", dome(cx_t - 1.2, cy_t - 1.4, 4.6, lo=2, hi=4, gain=1.3, fixed=True), rust=0.0)
    tx, ty = pts[-1]
    for (x, y) in tail:
        if (x + 0.5 - tx) ** 2 + (y + 0.5 - ty) ** 2 < 2.4 ** 2:
            cv.put(x, y, GH[5] if (x + 0.5 - tx) + (y + 0.5 - ty) < 0.5 else IV[4])   # the pale tip
    for (dx, dy, c) in ((0, -1, GH[5]), (-1, -1, AE[3]), (-1, -2, GH[5]), (-2, -2, AE[3]), (-2, -3, GH[4])):
        q = (int(math.floor(tx)) + dx, int(math.floor(ty)) + dy)
        cv.put_glow(q[0], q[1], c)
        glow.put_glow(q[0], q[1], c)
    # the body, its pale chest
    cv.part(Xf(), Ellipse(bx, by, 4.8 + p.stretch, 3.0 * sq), "ghost", dome(bx - 1.8, by - 2.0, 5.6, lo=2, hi=5, gain=1.4, fixed=True), rust=0.0)
    for (dx, dy, c) in ((3, 0, IV[4]), (3, 1, IV[3]), (2, 1, IV[4]), (3, -1, IV[5])):
        cv.put(int(math.floor(bx + p.stretch)) + dx, int(math.floor(by)) + dy, c)
    if p.lying < 0.5:                                       # the near legs
        for k in (0, 2):
            fx2, fy2 = p.feet[k]
            _leg(cv, hips[k], (fx2, min(fy2, 0.0) - p.tuck * 3.0 - 0.1), False)
    else:
        for x in (3, 4, 5, 6):                                  # the front paws out on the ground
            cv.put(x + int(p.stretch), -1, GH[3] if x < 6 else GH[1])
    # the head: big and round (a young fox), big ears with pale insides and dark tips, a pointed muzzle with a white cheek,
    # a dark nose
    hx, hy = 5.0 + p.stretch + p.head[0], by - 3.6 + p.head[1] + p.lying * 0.6
    cv.part(Xf(), Union(Ellipse(hx, hy, 3.5, 3.1), Poly([(hx + 1.8, hy - 0.4), (hx + 6.0, hy + 1.2), (hx + 1.8, hy + 2.6)])), "ghost",
            dome(hx - 1.2, hy - 1.4, 4.4, lo=2, hi=5, gain=1.3, fixed=True), rust=0.0)
    for (ex, back, far) in ((hx - 1.8, 0, True), (hx + 0.6, p.ears, False)):
        tip = (ex - 0.2 - back * 1.8, hy - 7.0 + back * 1.8)
        ear = cv.part(Xf(), Poly([(ex - 1.9, hy - 1.8), (ex + 1.7, hy - 2.1), tip]), "ghost", flat(3 if far else 4, bevel=False), rust=0.0)
        cv.put(int(math.floor(tip[0])), int(math.floor(tip[1])) + 1, GH[0])
        q = (int(math.floor(ex)), int(math.floor(hy - 3.0)))
        if q in ear and not far:
            cv.put(q[0], q[1], IV[4])                       # the near ear's pale inside
    for (dx, dy, c) in ((2, 1, IV[5]), (3, 1, IV[4]), (2, 2, IV[4]), (3, 2, IV[4]), (4, 2, IV[3]), (1, 2, IV[5])):   # the cheek
        cv.put(int(math.floor(hx)) + dx, int(math.floor(hy)) + dy, c)
    cv.put(int(math.floor(hx + 5.4)), int(math.floor(hy + 1.0)), GH[0])         # the nose
    finish(cv)
    ex, ey = int(math.floor(hx + 1.4)), int(math.floor(hy - 0.6))
    if p.eyes:
        for (dx, dy, c) in ((0, 0, GH[5]), (0, 1, GH[4])):
            cv.put_glow(ex + dx, ey + dy, c)
            glow.put_glow(ex + dx, ey + dy, c)
    else:
        cv.put(ex, ey + 1, GH[1])
        cv.put(ex + 1, ey + 1, GH[1])
    for k in range(p.wisps):                                    # spirit wisps under it as it floats
        for (dx, dy, c) in ((-3 + k * 3, 1, AE[3]), (-2 + k * 3, 2, GH[4])):
            cv.put_glow(dx, int(by) + 4 + dy, c)
            glow.put_glow(dx, int(by) + 4 + dy, c)
    return cv, glow


def trot(k):
    """Six-frame trot: diagonal pairs (near front with far hind) swing together; the body bobs a pixel at mid-stride."""
    ph = k / 6.0 * 2 * math.pi

    def foot(base, phase):
        swing = math.sin(ph + phase)
        x = base + 1.6 * swing
        y = -max(0.0, math.cos(ph + phase)) * 1.4
        return (x, y)
    feet = (foot(3.4, 0.0), foot(2.4, math.pi), foot(-3.6, math.pi), foot(-4.6, 0.0))
    return Pose(bob=-0.5 if k % 3 == 1 else 0.0, feet=feet, tail=math.sin(ph) * 0.6, lift=0.35, head=(0.0, 0.5 if k % 3 == 1 else 0.0))


POSES = (
    [Pose(tail=s, lift=0.55, ears=1 if k == 2 else 0) for k, s in enumerate((0.0, 0.6, 1.0, 0.6))]          # idle
    + [trot(k) for k in range(6)]                                                                                # trot
    + [Pose(bob=-1.0, stretch=1.0, tuck=1.0, tail=s, lift=0.1, wisps=w) for s, w in ((-0.8, 1), (0.0, 2), (0.8, 3), (0.0, 2))]  # float
    + [Pose(bob=0.8, lift=0.3, head=(-0.4, 0.6)), Pose(lying=1.0, lift=0.0, head=(0.4, 1.0))]                  # settle
    + [Pose(lying=1.0, curl=1.0, eyes=0, head=(0.4, 1.4)), Pose(lying=1.0, bob=-0.4, curl=1.0, eyes=0, head=(0.4, 1.2))]  # sleep
    + [Pose(lying=1.0, lift=0.2, head=(0.6, -0.4)), Pose(bob=0.6, stretch=1.0, feet=((5.4, 0.0), (4.6, 0.0), (-3.6, 0.0), (-4.6, 0.0)),
                                                         head=(0.6, 1.0), lift=0.9), Pose(lift=0.6)]                   # wake
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
