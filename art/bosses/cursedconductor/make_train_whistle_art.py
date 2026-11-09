"""Source for the Cursed Train Whistle and its ghost train minion (D4), 2026-11-09 (user: "a new weapon to the cursed
conductor weapon pool called cursed whistle: summon weapon that summons a train minion (smaller than the boss train so it's
not too visually aggressive), but only the head of the train, and using it to summon more adds wagons to the train"). Run
from the repo root:

    python -P art/bosses/cursedconductor/make_train_whistle_art.py [--preview FILE]

The Conductor's ghost train (make_conductor_art.py's engine and passenger car: a boiler with glowing bands, a balloon
stack, a cab with a ghost driver, drivers on a connecting rod, a cowcatcher; four lit windows, two bogies) redrawn small
(MINI_SCALE, about 0.6 of his: the engine 56 game px long against his 115) and turned to the friendly side (D3: friendly
effects are Brass and Aether): aether-blue ghost light instead of his ghost green, a brass lamp where his has an ember
eye, lavender windows. Drawn at each of 9 headings from straight up to straight down facing right (the game mirrors the
left half, never rotates), translucent in game with the windows and lamp solid from the glow sheets.

The item: a locomotive's brass steam whistle (a riveted bell on a steel stem, its mouth slot, a valve with a pull lever and
its cord), a curl of aether ghost light rising out of it. The buff icon: the little engine's face.

Outputs (Content/Bosses/CursedConductor/Weapons/):
    GhostTrainEngine.png, _Glow.png    68x630: 9 headings in 68x68 cells, 2 px under each
    GhostTrainWagon.png, _Glow.png     56x522: 9 headings in 56x56 cells
    CursedTrainWhistle.png             the item
    GhostTrainBuff.png                 32x32 the buff icon
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
from westbots import RAMP, Xf, Poly, Ellipse, Union, box, Canvas, flat, face, dome, P, finish, glint  # noqa: E402
from rig import cyl  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

OUT = "Content/Bosses/CursedConductor/Weapons/"
A, G, ST, S = RAMP["aether"], RAMP["gilt"], RAMP["steel"], RAMP["steam"]
HEADINGS = [-90.0 + 22.5 * k for k in range(9)]
MINI_SCALE = 0.78
ENGINE_CELL = 34
CAR_CELL = 28


def train_xf(heading, cell):
    c = cell / 2.0
    return Xf.pose(heading, (0.0, 0.0), (c, c)).then(Xf(MINI_SCALE, 0.0, 0.0, MINI_SCALE, 0.0, 0.0))


def ghost_face(lo=1, hi=2):
    return face((-0.5, -0.6, 0.65), lo=lo, hi=hi, gain=1.25, ramp_len=4, snap=22.5)


def wheel(cv, xf, x, y, r):
    cv.part(xf, Ellipse(x, y, r, r), "aether", flat(1, bevel=False), rust=0.0)
    q = P(xf, (x, y))
    cv.put(q[0], q[1], A[3])


def engine(heading):
    """The little engine at `heading`, its middle at the cell's centre (the Conductor's engine, aether and brass)."""
    cv, gl = Canvas(), Canvas()
    xf = train_xf(heading, ENGINE_CELL)
    for wx in (-9.6, -4.0, 1.6):
        wheel(cv, xf, wx, 6.0, 2.7)
    wheel(cv, xf, 9.6, 7.2, 1.7)
    for k in range(12):                                            # the connecting rod across the drivers
        q = P(xf, (-9.6 + k * 1.0, 6.0))
        cv.put(q[0], q[1], G[5])
    cv.part(xf, box(-15.8, 2.6, 13.8, 4.2), "aether", flat(1), rust=0.0)
    boiler = cv.part(xf, box(-6.4, -5.4, 12.4, 2.6), "aether", cyl((-6.4, -1.4), (12.4, -1.4), 4.1, lo=1, hi=3, snap=22.5), rust=0.0)
    for bx in (-2.4, 3.0, 8.4):                                    # its bands glow
        for k in range(10):
            q = P(xf, (bx, -5.0 + k * 0.8))
            if q in boiler:
                cv.put_glow(q[0], q[1], A[3])
                gl.put_glow(q[0], q[1], A[3])
    cv.part(xf, Ellipse(12.6, -1.4, 2.0, 3.9), "aether", flat(1), rust=0.0)          # the smokebox's round front
    cv.part(xf, Ellipse(0.4, -5.6, 2.3, 1.5), "gilt", flat(6), rust=0.0)             # a brass steam dome
    cv.part(xf, Poly([(8.2, -5.0), (10.4, -5.0), (10.8, -8.2), (13.0, -12.2), (5.6, -12.2), (7.8, -8.2)]), "aether", ghost_face(),
            rust=0.0)                                                                # the balloon stack
    cv.part(xf, box(5.2, -13.4, 13.4, -12.0), "gilt", flat(7), rust=0.0)           # its brass rim
    cv.part(xf, box(-16.0, -9.0, -6.2, 2.6), "aether", ghost_face(), rust=0.0)     # the cab
    cv.part(xf, box(-17.6, -11.0, -5.0, -9.0), "aether", flat(2), rust=0.0)        # its roof
    for q in cv.raster(xf, box(-14.0, -7.2, -8.4, -3.0)):          # the cab window, lit from inside
        cv.put_glow(q[0], q[1], A[3])
        gl.put_glow(q[0], q[1], A[3])
    for (lx, ly) in ((-12.0, -5.6), (-11.4, -5.6), (-12.0, -4.6), (-11.4, -4.6), (-11.8, -6.6)):
        q = P(xf, (lx, ly))                                        # the ghost driver looking out
        cv.put_glow(q[0], q[1], A[1])
        gl.put_glow(q[0], q[1], A[1])
    cv.part(xf, box(11.4, -9.0, 15.6, -5.2), "aether", flat(1), rust=0.0)          # the box headlamp on the smokebox
    for q in cv.raster(xf, box(13.6, -8.2, 15.4, -6.0)):            # its lens: a warm brass light (friendly)
        cv.put_glow(q[0], q[1], G[8])
        gl.put_glow(q[0], q[1], G[8])
    q = P(xf, (14.0, -7.6))
    cv.put_glow(q[0], q[1], G[9])
    gl.put_glow(q[0], q[1], G[9])
    catcher = cv.part(xf, Poly([(13.0, 2.6), (15.8, 2.6), (20.0, 8.6), (13.0, 8.6)]), "gilt", flat(4), rust=0.0)
    for k in range(7):                                             # its slats
        q = P(xf, (14.2 + k * 0.9, 4.6 + k * 0.6))
        if q in catcher:
            cv.put(q[0], q[1], G[1])
    return cv, gl


def car(heading):
    """A little passenger car at `heading`, its middle at the cell's centre."""
    cv, gl = Canvas(), Canvas()
    xf = train_xf(heading, CAR_CELL)
    for bx in (-8.0, 8.0):                                         # two bogies
        for wx in (-2.4, 2.4):
            wheel(cv, xf, bx + wx, 6.4, 1.8)
        cv.part(xf, box(bx - 4.0, 4.4, bx + 4.0, 5.6), "aether", flat(1, bevel=False), rust=0.0)
    cv.part(xf, box(-12.4, 3.6, 12.4, 5.0), "aether", flat(1), rust=0.0)           # the underframe
    for ex in (-14.6, 13.0):
        cv.part(xf, box(ex, 1.6, ex + 1.6, 3.2), "gilt", flat(4, bevel=False), rust=0.0)   # brass couplers
    body_ = cv.part(xf, box(-13.0, -6.6, 13.0, 3.8), "aether", ghost_face(), rust=0.0)
    cv.part(xf, Union(box(-13.6, -8.0, 13.6, -6.4), box(-11.2, -9.4, 11.2, -7.6)), "aether", flat(2), rust=0.0)   # the roof
    passengers = {0: ((0.8, -3.4), (1.6, -3.4), (0.8, -2.4), (1.6, -2.4), (0.4, -1.6), (2.0, -1.6)),
                  2: ((0.8, -3.0), (1.6, -3.0), (0.6, -2.0), (1.8, -2.0))}
    for w, wx in enumerate((-10.6, -4.8, 1.0, 6.8)):              # four lit windows, ghost passengers in two
        for q in cv.raster(xf, box(wx, -4.8, wx + 3.6, -1.0)):
            cv.put_glow(q[0], q[1], A[3])
            gl.put_glow(q[0], q[1], A[3])
        for (lx, ly) in passengers.get(w, ()):
            q = P(xf, (wx + lx, ly))
            cv.put_glow(q[0], q[1], A[1])
            gl.put_glow(q[0], q[1], A[1])
    for k in range(26):                                            # a brass waist band under the windows
        q = P(xf, (-12.6 + k, 0.6))
        if q in body_:
            cv.put(q[0], q[1], G[5])
    return cv, gl


def train_sheets(fn, cell):
    frames, glows = [], []
    for h in HEADINGS:
        cv, gl = fn(h)
        for (x, y) in list(cv.px):
            if not (0 <= x < cell and 0 <= y < cell):
                raise SystemExit("mini train pixel (%d, %d) outside its %d cell at heading %.1f" % (x, y, cell, h))
        frames.append(to_image(cv.px, 0, 0, cell, cell))
        glows.append(to_image(gl.glow, 0, 0, cell, cell))
    return vertical(frames), vertical(glows)


def whistle_item():
    """A locomotive's brass steam whistle, upright: the riveted bell lit as a cylinder from the left, its domed cap, the
    dark mouth slot near its foot, a steel stem into a valve with a pull lever and its cord; a curl of aether light out
    of the cap (a soul in the whistle)."""
    cv = Canvas()
    X = Xf()
    cv.part(X, box(2.6, 5.0, 9.4, 13.0), "gilt", cyl((6.0, 5.0), (6.0, 13.0), 3.4, lo=2, hi=8, gain=1.3, fixed=True, dither=0.15),
            shadow=(1, 1), rust=0.0)                               # the bell
    cv.part(X, Ellipse(6.0, 5.0, 3.0, 1.8), "gilt", dome(4.6, 3.8, 3.4, lo=3, hi=9, gain=1.35, fixed=True), rust=0.0)   # its cap
    cv.part(X, box(5.0, 13.0, 7.0, 15.6), "steel", cyl((6.0, 13.0), (6.0, 15.6), 1.0, lo=2, hi=6, fixed=True), rust=0.0)  # the stem
    cv.part(X, box(3.8, 15.4, 8.2, 17.6), "steel", face((-0.5, -0.6, 0.7), lo=2, hi=6, ramp_len=9, fixed=True), rust=0.0)  # the valve
    cv.part(X, Poly([(8.0, 15.6), (12.6, 14.0), (13.0, 15.0), (8.2, 16.8)]), "gilt", flat(6), rust=0.0)   # the pull lever
    finish(cv)
    for x in range(4, 9):                                          # the mouth slot, stamped after the despeckle
        cv.put(x, 11, ST[0] if x > 4 else ST[1])
    for (x, y) in ((3, 7), (3, 10)):                               # rivets on the lit side
        cv.put(x, y, G[9])
    for y in range(17, 20):                                        # the pull cord hanging off the lever
        cv.put(12, y, G[3] if y < 19 else G[5])
    for (x, y, col) in ((6, 2, A[3]), (5, 1, A[2]), (7, 1, A[2]), (6, 0, A[2]), (4, 0, A[1]), (8, 2, A[1]), (7, 3, A[2])):
        cv.put(x, y, col)                                          # the soul's light curling out of the cap
    xs = [x for (x, _) in cv.px]
    ys = [y for (_, y) in cv.px]
    x0, y0 = min(xs), min(ys)
    return to_image(cv.px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


# The buff icon, drawn by hand (16x16 at 1x): the little engine side on, running right. a/1/2/3 = aether 0-3 (outline,
# dark, mid, lit), o/g/G = gilt 1/5/8 (the stack's rim, the lamp), w = steam white (the lamp's hot spot).
BUFF = ["................",
        "................",
        ".........oooo...",
        ".........gGGg...",
        "..........a3a...",
        ".aaaa.....a2a...",
        ".a33a.....a2a...",
        ".a33aaaaaaa1aaa.",
        ".a22a3333333gGa.",
        ".a12a2222222Gwa.",
        ".a11a1111111gga.",
        ".aaaaaaaaaaaaaa.",
        "..a2a.a2a..a2a..",
        "..aaa.aaa..aaa..",
        "................",
        "................"]


def buff_icon():
    """16x16: the little engine side on, running right: its cab with a lit window, an aether boiler lit along its top, a
    stack with a brass rim, a brass lamp with a hot spot at the front, three wheels."""
    pal = {"a": A[0], "1": A[1], "2": A[2], "3": A[3], "o": G[1], "g": G[5], "G": G[8], "w": S[3]}
    px = {(x, y): pal[ch] for y, row in enumerate(BUFF) for x, ch in enumerate(row) if ch in pal}
    return to_image(px, 0, 0, 16, 16)


def export_all():
    sheet, glow = train_sheets(engine, ENGINE_CELL)
    export(sheet, OUT + "GhostTrainEngine.png")
    export(glow, OUT + "GhostTrainEngine_Glow.png")
    sheet, glow = train_sheets(car, CAR_CELL)
    export(sheet, OUT + "GhostTrainWagon.png")
    export(glow, OUT + "GhostTrainWagon_Glow.png")
    export(whistle_item(), OUT + "CursedTrainWhistle.png")
    export(buff_icon(), OUT + "GhostTrainBuff.png")


def preview(path):
    trains = Image.new("RGBA", (ENGINE_CELL * 9 + 8, ENGINE_CELL + CAR_CELL + 4), (36, 40, 48, 255))
    for k, hd in enumerate(HEADINGS):
        cv, _ = engine(hd)
        trains.alpha_composite(to_image(cv.px, 0, 0, ENGINE_CELL, ENGINE_CELL), (k * ENGINE_CELL, 0))
        cv, _ = car(hd)
        trains.alpha_composite(to_image(cv.px, 0, 0, CAR_CELL, CAR_CELL), (k * ENGINE_CELL, ENGINE_CELL + 2))
    items = Image.new("RGBA", (trains.width, 24), (150, 180, 210, 255))
    items.alpha_composite(whistle_item(), (4, 2))
    items.alpha_composite(buff_icon(), (30, 4))
    sheet = Image.new("RGBA", (trains.width, trains.height + items.height), (0, 0, 0, 255))
    sheet.paste(trains, (0, 0))
    sheet.paste(items, (0, trains.height))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
