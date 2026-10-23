"""Source for Trash-Tr0m, the Junkyard boss (D4). Run from the repo root:

    python -P art/bosses/trashtr0m/make_trashtr0m_art.py

Outputs (2x nearest-neighbour, next to Content/Bosses/TrashTr0m/TrashTr0m.cs):
    TrashTr0m.png            216x1020  6 frames of 216x168 (108x84 art) on a 170 px stride (2 px padding)
    TrashTr0m_Glow.png       216x1020  the same frames: eyes, throat and furnace only (drawn at full brightness in code)
    TrashTr0m_Head_Boss.png  32x32     map / boss-bar icon

Design: the upper half of a construction titan (after the Devastator's big hunched head with a grinder mouth), torn
off at the waist and welded back together from scrap. It has no legs: it props itself on its two arms like a
gorilla, hands planted, the ragged waist hanging between them with its spine, wires and pipes showing. Every part is
a different salvaged machine, which is the point (an amalgamation):
    head        a bolted iron housing; brass flange around a two-ring grinder maw (outer ring 12 teeth, inner ring
                8 teeth, counter-rotating), ember throat; a hazard-brass visor with three ember eyes in a slit; a small
                crane boom and hook on top; serrated mandibles on hydraulic rods
    shoulders   left: a tractor tyre bolted on as a pauldron (brass hub, lug nuts, tread); right: a rusted
                dump-truck bed plate with hazard stripes; two exhaust stacks behind it
    torso       riveted iron plates, a pressure gauge, a radiator, a furnace grate, rust and verdigris patch plates,
                weld seams with bright beads, a cable bundle
    arms        left: a brass excavator boom with a chrome piston, gear elbow and a toothed bucket for a hand;
                right: a rust-red crane arm with a cable winch elbow and a three-prong claw
Height 168 px = 4x the player's 42 px hitbox (the brief's maximum). Lit from the top-left; every part is outlined
in ramp 0 of its own material; 48-colour cap for bosses (it uses only Cogpunk palette colours).

Animation (6 frames, TrashTr0m.TicksPerFrame = 6 ticks; 3 while roaring): the outer grinder ring turns 5 degrees
per frame and the inner ring 7.5 degrees the other way, so both loop after 6 frames (one tooth period each); the
torso, head and shoulders settle 1 px on frames 2-3 (an idling engine) while the planted hands stay put; the chrome
pistons pump with them; the dangling wires twitch.
The hands are planted, so the boss never bobs in code: all idle motion is in these frames.
Emitter points used by the C# code (2x frame pixels): exhaust stacks (164, 8) and (180, 16), mouth (93, 92),
waist line y = 150 between x = 66 and 154.
"""
import math
import os
import random
from PIL import Image

ROOT = os.getcwd()
OUT = "Content/Bosses/TrashTr0m/"
W, H = 108, 84
FRAMES = 6
PAD = 1                                           # 1 px at 1x = the 2 px sheet padding

RAMP = {
    "iron": [(21, 22, 28), (46, 50, 59), (79, 85, 98), (127, 135, 148), (183, 191, 202)],
    "brass": [(43, 26, 14), (90, 58, 23), (138, 93, 34), (184, 138, 51), (223, 185, 78), (246, 231, 161)],
    "copper": [(42, 18, 12), (94, 40, 23), (147, 68, 31), (196, 104, 58), (233, 160, 107)],
    "verd": [(23, 52, 48), (42, 94, 82), (71, 145, 126), (140, 201, 176)],
    "leather": [(47, 27, 20), (91, 54, 38), (138, 90, 60)],
    "steam": [(138, 144, 150), (195, 200, 205), (238, 241, 243), (255, 255, 255)],
    "ember": [(77, 20, 10), (163, 48, 26), (236, 113, 40), (255, 199, 90)],
}
WHITE = RAMP["steam"][3]
COLOR_INDEX = {col: (name, k) for name, ramp in RAMP.items() for k, col in enumerate(ramp)}
LIGHT = (-0.55, -0.62, 0.56)                       # top-left, towards the viewer
_ln = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _ln for c in LIGHT)


# ================================================================================================
# Rasterising and shading
# ================================================================================================
def poly_mask(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mask = set()
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px, py = x + 0.5, y + 0.5
            inside = False
            j = len(points) - 1
            for i in range(len(points)):
                xi, yi = points[i]
                xj, yj = points[j]
                if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                mask.add((x, y))
    return mask


def ellipse_mask(cx, cy, rx, ry):
    mask = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                mask.add((x, y))
    return mask


def ring_mask(cx, cy, r0, r1):
    return {(x, y) for (x, y) in ellipse_mask(cx, cy, r1, r1) if math.hypot(x + 0.5 - cx, y + 0.5 - cy) >= r0}


def capsule_mask(p0, p1, r):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln2 = dx * dx + dy * dy or 1e-6
    mask = set()
    for y in range(int(min(y0, y1) - r) - 1, int(max(y0, y1) + r) + 2):
        for x in range(int(min(x0, x1) - r) - 1, int(max(x0, x1) + r) + 2):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / ln2))
            if math.hypot(px - (x0 + t * dx), py - (y0 + t * dy)) <= r:
                mask.add((x, y))
    return mask


def boundary(mask):
    return {(x, y) for (x, y) in mask if any((x + ox, y + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def level(intensity, ramp, lo=1, hi=None, gain=1.0, bias=0.0):
    """Maps a lighting intensity (-1..1) to a ramp index in [lo, hi] with hard steps (no gradients)."""
    hi = len(ramp) - 1 if hi is None else hi
    v = (intensity * gain + bias + 1.0) * 0.5           # 0..1
    idx = lo + int(v * (hi - lo + 1))
    return max(lo, min(hi, idx))


class Sprite:
    """1x canvas of RGB tuples; parts are painted back to front."""

    def __init__(self):
        self.px = {}
        self.glow = {}

    def put(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            self.px[(x, y)] = color

    def put_glow(self, x, y, color):
        """A pixel that is also in the _Glow texture (drawn again at full brightness in game)."""
        if 0 <= x < W and 0 <= y < H:
            self.px[(x, y)] = color
            self.glow[(x, y)] = color

    def darken(self, x, y, steps=1):
        """One step down the pixel's own ramp (never to its outline shade, which stays reserved for edges)."""
        col = self.px.get((x, y))
        if col is None or (x, y) in self.glow or col not in COLOR_INDEX:
            return
        ramp, idx = COLOR_INDEX[col]
        self.px[(x, y)] = RAMP[ramp][max(1 if idx >= 1 else 0, idx - steps)]

    def part(self, mask, ramp, shade, outline=True, shadow=None):
        """Paints a part: shade(x, y) -> ramp index for the inside, ramp 0 on its boundary (its outline).
        shadow=(dx, dy) first darkens, one step, whatever lies within that offset below-right of the part: the shadow
        it casts on the parts behind it (light from the top-left)."""
        if shadow:
            sx, sy = shadow
            steps = max(abs(sx), abs(sy))
            cast = set()
            for (x, y) in mask:
                for k in range(1, steps + 1):
                    cast.add((x + round(sx * k / steps), y + round(sy * k / steps)))
            for q in cast - mask:
                self.darken(*q)
        edge = boundary(mask) if outline else set()
        r = RAMP[ramp]
        for (x, y) in mask:
            self.put(x, y, r[0] if (x, y) in edge else r[shade(x, y)])
        return mask - edge


# --- shading models ------------------------------------------------------------------------------
def flat_bevel(mask, base, ramp_len, hi_step=1, lo_step=1):
    inner = mask - boundary(mask)
    lit = {(x, y) for (x, y) in inner if (x, y - 1) not in inner or (x - 1, y) not in inner}
    dark = {(x, y) for (x, y) in inner if (x, y + 1) not in inner or (x + 1, y) not in inner}

    def shade(x, y):
        if (x, y) in lit and (x, y) not in dark:
            return min(ramp_len - 1, base + hi_step)
        if (x, y) in dark and (x, y) not in lit:
            return max(1, base - lo_step)
        return base
    return shade


def form_bevel(mask, cx, cy, r, ramp_len, gain=1.0, bias=0.0, lo=1, hi=None):
    """Big-form lighting (a broad dome around (cx, cy)) plus a one-pixel bevel on the plate's edges."""
    inner = mask - boundary(mask)
    lit = {(x, y) for (x, y) in inner if (x, y - 1) not in inner or (x - 1, y) not in inner}
    dark = {(x, y) for (x, y) in inner if (x, y + 1) not in inner or (x + 1, y) not in inner}
    hi = ramp_len - 1 if hi is None else hi
    dome = round_shade(cx, cy, r, ramp_len, gain=gain, bias=bias, lo=lo)

    def shade(x, y):
        k = min(hi, dome(x, y))
        if (x, y) in lit and (x, y) not in dark:
            k += 1
        elif (x, y) in dark and (x, y) not in lit:
            k -= 1
        return max(1, min(ramp_len - 1, k))
    return shade


def round_shade(cx, cy, r, ramp_len, gain=1.25, bias=0.0, lo=1):
    def shade(x, y):
        dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
        d2 = min(1.0, dx * dx + dy * dy)
        nz = math.sqrt(1.0 - d2)
        i = dx * LIGHT[0] + dy * LIGHT[1] + nz * LIGHT[2]
        return level(i, [0] * ramp_len, lo=lo, gain=gain, bias=bias)
    return shade


def cyl_shade(p0, p1, r, ramp_len, gain=1.4, bias=0.0, lo=1):
    (x0, y0), (x1, y1) = p0, p1
    ax, ay = x1 - x0, y1 - y0
    ln = math.hypot(ax, ay) or 1e-6
    nx, ny = -ay / ln, ax / ln                          # perpendicular

    def shade(x, y):
        s = ((x + 0.5 - x0) * nx + (y + 0.5 - y0) * ny) / r
        s = max(-1.0, min(1.0, s))
        nz = math.sqrt(1.0 - s * s)
        i = s * nx * LIGHT[0] + s * ny * LIGHT[1] + nz * LIGHT[2]
        return level(i, [0] * ramp_len, lo=lo, gain=gain, bias=bias)
    return shade


# --- small details ---------------------------------------------------------------------------------
def rivet(s, x, y, ramp="iron"):
    r = RAMP[ramp]
    s.put(x, y, r[-1])
    s.put(x + 1, y + 1, r[1])


def bolt(s, x, y, ramp="brass"):
    r = RAMP[ramp]
    s.put(x, y, r[-1])
    s.put(x + 1, y, r[2])
    s.put(x, y + 1, r[2])
    s.put(x + 1, y + 1, r[0])


def line(s, p0, p1, color_at):
    (x0, y0), (x1, y1) = (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1])))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, n = dx + dy, 0
    while True:
        s.put(x0, y0, color_at(n))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
        n += 1


def weld(s, p0, p1):
    """A weld seam: a dark groove with bright beads every other pixel."""
    i = RAMP["iron"]
    line(s, p0, p1, lambda n: i[4] if n % 2 == 0 else i[3])
    line(s, (p0[0] + 1, p0[1] + 1), (p1[0] + 1, p1[1] + 1), lambda n: i[1])


def grime(s, mask, rng, amount, colors):
    """Rust and dirt as short vertical streaks (2-3 px running down from a seam or rivet), never lone pixels (D4)."""
    pts = sorted(mask)
    if not pts:
        return
    for _ in range(int(len(pts) * amount * 0.4)):
        x, y = pts[rng.randrange(len(pts))]
        col = colors[rng.randrange(len(colors))]
        length = 2 + rng.randrange(2)
        if all((x, y + k) in mask for k in range(length)):
            for k in range(length):
                s.put(x, y + k, col)


# ================================================================================================
# The parts (all coordinates at 1x; dy = the body's settle offset for this frame)
# ================================================================================================
def exhaust_stacks(s, dy):
    i, b = RAMP["iron"], RAMP["brass"]
    for (cx, top, w) in ((82, 4, 2.6), (89.5, 8, 2.1)):
        m = poly_mask([(cx - w, top + dy), (cx + w, top + dy), (cx + w, 28 + dy), (cx - w, 28 + dy)])
        s.part(m, "iron", cyl_shade((cx, top), (cx, 28), w, 5, gain=1.5))
        rim = poly_mask([(cx - w - 1, top - 1 + dy), (cx + w + 1, top - 1 + dy), (cx + w + 1, top + 2 + dy), (cx - w - 1, top + 2 + dy)])
        s.part(rim, "brass", cyl_shade((cx, top), (cx, top + 3), w + 1, 6, gain=1.6))
        s.put(int(cx), top + dy, i[0])                   # the soot-black mouth of the stack
        s.put(int(cx) - 1, top + dy, i[0])
        for y in range(top + 6, 26, 5):                  # clamp bands
            s.put(int(cx - w) + 1, y + dy, b[4])
            s.put(int(cx + w) - 1, y + dy, b[1])


def crane_boom(s, dy):
    b, i = RAMP["brass"], RAMP["iron"]
    p0, p1 = (37, 24 + dy), (27, 6 + dy)
    m = capsule_mask(p0, p1, 1.9)
    inner = s.part(m, "brass", cyl_shade(p0, p1, 1.9, 6, gain=1.3, bias=0.2), shadow=(1, 1))
    for k in range(2, 19, 3):                            # lattice bracing
        t = k / 19
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        if (int(x), int(y)) in inner:
            s.put(int(x), int(y), b[1])
    s.part(ellipse_mask(26.5, 6 + dy, 2.3, 2.3), "iron", round_shade(26.5, 6 + dy, 2.3, 5))
    s.put(26, 6 + dy, i[0])
    for y in range(8, 12):                               # hook cable and hook
        s.put(25, y + dy, i[1])
    for (x, y, k) in ((25, 12, 2), (24, 13, 3), (25, 14, 3), (26, 14, 2), (27, 13, 2), (27, 12, 1)):
        s.put(x, y + dy, i[k])


def tyre_shoulder(s, dy):
    cx, cy = 17.5, 24.5 + dy
    i, b = RAMP["iron"], RAMP["brass"]
    tyre = ring_mask(cx, cy, 5.6, 12.1)
    s.part(tyre, "iron", round_shade(cx, cy, 12.1, 4, gain=1.1, bias=-0.35), shadow=(2, 2))
    for k in range(14):                                  # tread notches
        a = math.radians(k * (360 / 14) + 8)
        for r in (11.0, 11.6):
            x, y = int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)
            if (x, y) in tyre:
                s.put(x, y, i[0])
    for k in range(-160, -90, 5):                        # sidewall highlight arc
        a = math.radians(k)
        s.put(int(cx + math.cos(a) * 9.0), int(cy + math.sin(a) * 9.0), i[3])
    s.put(int(cx - 6.5), int(cy - 6.5), i[4])
    hub = ellipse_mask(cx, cy, 5.8, 5.8)
    s.part(hub, "brass", round_shade(cx, cy, 5.8, 6, gain=1.1, bias=-0.1))
    for k in range(5):
        a = math.radians(k * 72 - 90)
        bolt(s, int(cx + math.cos(a) * 3.4), int(cy + math.sin(a) * 3.4), "iron")
    s.put(int(cx), int(cy), b[0])
    s.put(int(cx) - 1, int(cy) - 1, b[5])


def bed_shoulder(s, dy, rng):
    c, i, b = RAMP["copper"], RAMP["iron"], RAMP["brass"]
    pts = [(73, 13), (97, 11), (106, 23), (103, 35), (81, 35), (72, 25)]
    pts = [(x, y + dy) for (x, y) in pts]
    m = poly_mask(pts)
    inner = s.part(m, "copper", form_bevel(m, 80, 8 + dy, 30, 5, gain=1.1, bias=0.0, hi=3), shadow=(2, 2))
    for x0 in (79, 86, 93, 100):                         # ribs of the bed
        for y in range(14, 28):
            if (x0, y + dy) in inner:
                s.put(x0, y + dy, c[4] if y < 16 else c[3])
            if (x0 + 1, y + dy) in inner:
                s.put(x0 + 1, y + dy, c[1])
    for (x, y) in sorted(inner):                          # hazard stripes along the lower lip
        if 29 + dy <= y <= 33 + dy:
            s.put(x, y, b[4] if ((x + y - dy) // 3) % 2 == 0 else i[0])
    for x in range(76, 102, 4):
        rivet(s, x, 14 + dy, "copper")
    grime(s, {p for p in inner if p[1] < 28 + dy}, rng, 0.06, [c[1], c[1], RAMP["leather"][0]])
    for (x, y) in ((88, 20), (89, 21), (95, 23), (82, 24)):
        s.put(x, y + dy, c[1])
        s.put(x - 1, y - 1 + dy, c[4])


def torso(s, dy, rng):
    i, c, b, v = RAMP["iron"], RAMP["copper"], RAMP["brass"], RAMP["verd"]
    waist = []
    x, k = 77, 0
    while x > 32:                                         # ragged, torn waist
        waist.append((x, 72 + (0, 4, 1, 6, 2, 5, 0, 3)[k % 8] + dy))
        x -= 3 + (k % 3)
        k += 1
    waist.append((32, 73 + dy))
    pts = [(24, 19), (84, 19), (87, 31), (82, 57), (78, 71)]
    pts = [(x, y + dy) for (x, y) in pts] + waist + [(30, 57 + dy), (22, 31 + dy)]
    m = poly_mask(pts)
    # a barrel chest: lit on the upper left, rolling into shadow on the lower right
    inner = s.part(m, "iron", form_bevel(m, 36, 24 + dy, 44, 5, gain=1.15, bias=-0.1, hi=3), shadow=(2, 1))
    for px in (38, 70):                                   # plate seams with lit lips
        for y in range(21, 72):
            if (px, y + dy) in inner:
                s.put(px, y + dy, i[1])
                if (px + 1, y + dy) in inner:
                    s.put(px + 1, y + dy, i[3])
    for py in (34, 52):
        for x in range(23, 87):
            if (x, py + dy) in inner:
                s.put(x, py + dy, i[1])
                if (x, py + 1 + dy) in inner:
                    s.put(x, py + 1 + dy, i[3])
    for x in range(27, 83, 4):
        rivet(s, x, 21 + dy)
    for y in range(37, 68, 4):
        rivet(s, 25 + (y - 37) // 8, y + dy)
        rivet(s, 83 - (y - 37) // 7, y + dy)
    rust = poly_mask([(31, 58 + dy), (44, 57 + dy), (45, 68 + dy), (33, 69 + dy)])
    s.part(rust, "copper", flat_bevel(rust, 2, 5))
    for (x, y) in ((33, 60), (42, 59), (34, 66), (43, 66)):
        rivet(s, x, y + dy, "copper")
    grime(s, rust, rng, 0.12, [c[1], c[3], RAMP["leather"][0]])
    verd = poly_mask([(66, 57 + dy), (78, 58 + dy), (77, 67 + dy), (65, 66 + dy)])
    s.part(verd, "verd", flat_bevel(verd, 2, 4))
    for (x, y) in ((67, 59), (75, 60), (67, 64), (75, 64)):
        rivet(s, x, y + dy, "verd")
    weld(s, (31, 57 + dy), (44, 56 + dy))
    weld(s, (65, 56 + dy), (78, 57 + dy))
    weld(s, (23, 32 + dy), (29, 47 + dy))
    weld(s, (85, 32 + dy), (81, 50 + dy))
    # pressure gauge (left chest)
    gx, gy = 28.5, 42.5 + dy
    s.part(ellipse_mask(gx, gy, 5.2, 5.2), "brass", round_shade(gx, gy, 5.2, 6, gain=1.2, bias=-0.1))
    st = RAMP["steam"]
    for (x, y) in ellipse_mask(gx, gy, 3.4, 3.4):
        s.put(x, y, st[2] if (x + y) % 7 else st[1])
    for k in range(5):
        a = math.radians(150 + k * 60)
        s.put(int(gx + math.cos(a) * 2.6), int(gy + math.sin(a) * 2.6), i[1])
    line(s, (gx - 0.5, gy - 0.5), (gx + 2, gy - 2.5), lambda n: RAMP["ember"][1])
    s.put(int(gx) - 1, int(gy) - 2, WHITE)
    # radiator (right chest)
    for y in range(37, 50):
        for x in range(72, 81):
            if (x, y + dy) in inner:
                s.put(x, y + dy, i[1] if y % 2 else (i[3] if x < 79 else i[2]))
    for y in range(36, 51):
        s.put(71, y + dy, i[0])
        s.put(81, y + dy, i[0])
    for x in range(71, 82):
        s.put(x, 36 + dy, i[0])
        s.put(x, 50 + dy, i[0])
    # furnace grate below the head (embers glow between the bars)
    fx0, fx1, fy0, fy1 = 46, 62, 61, 70
    for y in range(fy0, fy1 + 1):
        for x in range(fx0, fx1 + 1):
            if x in (fx0, fx1) or y in (fy0, fy1):
                s.put(x, y + dy, i[0])
            elif (x - fx0) % 3 == 0:
                s.put(x, y + dy, i[3] if y < fy0 + 3 else i[2])
            elif y <= fy0 + 2:
                s.put(x, y + dy, RAMP["ember"][0])
            else:
                s.put_glow(x, y + dy, RAMP["ember"][3] if (x * 3 + y) % 5 else RAMP["ember"][2])
    for x in range(fx0 + 1, fx1, 4):
        rivet(s, x, fy0 - 2 + dy)
    grime(s, inner, rng, 0.02, [i[1], RAMP["leather"][0], c[1]])
    for (x, y) in ((54, 38), (55, 39), (56, 39), (61, 24), (62, 25), (33, 49), (34, 48)):
        s.put(x, y + dy, i[4])
    return waist


def tube(s, points, r, ramp, rings=0):
    """A thick cable or hose along a polyline, shaded as a cylinder; rings > 0 makes it corrugated."""
    mask = set()
    for a, b in zip(points, points[1:]):
        mask |= capsule_mask(a, b, r)
    rr = RAMP[ramp]
    edge = boundary(mask)
    for (x, y) in mask:
        if (x, y) in edge:
            s.put(x, y, rr[0])
            continue
        best, side = 1e9, 0.0
        for a, b in zip(points, points[1:]):
            ax, ay = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(ax, ay) or 1e-6
            t = max(0.0, min(1.0, ((x + 0.5 - a[0]) * ax + (y + 0.5 - a[1]) * ay) / (ln * ln)))
            qx, qy = a[0] + ax * t, a[1] + ay * t
            d = math.hypot(x + 0.5 - qx, y + 0.5 - qy)
            if d < best:
                nx, ny = -ay / ln, ax / ln
                best, side = d, ((x + 0.5 - qx) * nx + (y + 0.5 - qy) * ny) / r
        sd = max(-1.0, min(1.0, side))
        idx = level(-sd * 0.8 + 0.25, rr, lo=1)
        if rings and (x + y) % rings == 0:
            idx = max(1, idx - 1)
        s.put(x, y, rr[idx])


def hoses(s, dy):
    """The cable bundle sagging across the chest and two corrugated hoses from the jaw into the shoulders."""
    tube(s, [(30, 30 + dy), (40, 37 + dy), (55, 39 + dy), (68, 37 + dy), (80, 31 + dy)], 1.6, "leather")
    tube(s, [(27, 52 + dy), (24, 44 + dy), (27, 34 + dy)], 1.5, "iron", rings=2)
    tube(s, [(67, 52 + dy), (75, 44 + dy), (80, 35 + dy)], 1.5, "iron", rings=2)


def waist_guts(s, dy, frame, waist):
    i, c, e, v, b = RAMP["iron"], RAMP["copper"], RAMP["ember"], RAMP["verd"], RAMP["brass"]
    for (x, y) in waist:                                  # raw, bright metal along the tear
        s.put(x, y - 1, i[4])
        s.put(x + 1, y - 1, i[3])
    for k in range(4):                                    # exposed spine
        cy = 72 + k * 3 + dy
        s.part(ellipse_mask(55.5, cy, 2.6 - k * 0.3, 1.7), "iron", round_shade(55.5, cy, 2.6, 5))
    stub = poly_mask([(37, 69 + dy), (42, 69 + dy), (42, 78 + dy), (37, 78 + dy)])
    s.part(stub, "iron", cyl_shade((39.5, 69), (39.5, 78), 2.5, 5, gain=1.5))
    for x in range(38, 41):
        s.put(x, 78 + dy, i[0])
    s.put(39, 80 + dy, i[0])                              # a drop of oil
    stub2 = poly_mask([(68, 68 + dy), (72, 68 + dy), (72, 75 + dy), (68, 75 + dy)])
    s.part(stub2, "brass", cyl_shade((70, 68), (70, 75), 2, 6, gain=1.5))
    s.put(69, 75 + dy, b[0])
    s.put(70, 75 + dy, b[0])
    sway = (0, 1, 1, 0, -1, -1)[frame]
    for (x0, length, ramp, phase) in ((45, 8, "copper", 0), (49, 9, "ember", 2), (61, 7, "verd", 1),
                                      (64, 9, "brass", 3), (75, 6, "copper", 4)):
        r = RAMP[ramp]
        y0 = 73 + dy
        for n in range(length):
            if y0 + n > H - 2:
                break
            off = int(round(sway * (n / length) * (1 if (phase % 2) else -1)))
            x = x0 + off + (1 if n > length // 2 and phase > 2 else 0)
            s.put(x, y0 + n, r[2] if n % 3 else r[1])
    if frame % 2 == 0:                                    # a spark off the live (ember) wire
        s.put_glow(49 - sway, min(H - 1, 73 + 9 + dy), e[3])


def head(s, dy, frame, rng):
    i, b, c, e = RAMP["iron"], RAMP["brass"], RAMP["copper"], RAMP["ember"]
    v = RAMP["verd"]
    hx, hy = 47.0, 41.0 + dy
    # the housing: an oxidised green dome (a nod to the Constructicons' green), casting a heavy shadow on the chest
    shell = ellipse_mask(hx, hy, 21.5, 19.5)
    s.part(shell, "verd", round_shade(hx - 4, hy - 5, 24, 4, gain=1.25, bias=0.1), shadow=(2, 3))
    for a in range(20, 161, 20):                          # rivets round the lower rim
        rad = math.radians(a)
        rivet(s, int(hx + math.cos(rad) * 19.5), int(hy + math.sin(rad) * 17.5), "verd")
    for a in range(200, 341, 28):                         # a weld seam where two housings were joined
        rad = math.radians(a)
        s.put(int(hx + math.cos(rad) * 15), int(hy + math.sin(rad) * 14), i[4])
        s.put(int(hx + math.cos(rad) * 15) + 1, int(hy + math.sin(rad) * 14) + 1, i[2])
    for (x0, y0) in ((27, 37), (64, 37)):                 # cheek vents
        for k in range(4):
            for x in range(x0, x0 + 4):
                s.put(x, y0 + k * 2 + dy, v[0])
                s.put(x, y0 + k * 2 + 1 + dy, v[3] if x == x0 else v[2])
    # brow: a hazard-brass visor bolted across the forehead
    visor = poly_mask([(27, 28 + dy), (37, 23 + dy), (57, 22 + dy), (67, 27 + dy), (66, 32 + dy), (28, 33 + dy)])
    vin = s.part(visor, "brass", form_bevel(visor, 38, 20 + dy, 30, 6, gain=1.1, bias=0.0, lo=2, hi=4), shadow=(0, 2))
    for x in range(30, 65):                               # eye slit
        for y in (28, 29, 30):
            if (x, y + dy) in vin:
                s.put(x, y + dy, i[0] if y != 28 else i[1])
    for (ex, w) in ((33, 4), (41, 5), (50, 4)):           # three eyes, set toward the left (it looks left)
        for x in range(ex, ex + w):
            s.put_glow(x, 29 + dy, e[3] if x < ex + w - 1 else e[2])
            s.put_glow(x, 30 + dy, e[2] if x > ex else e[1])
    for x in range(30, 66, 5):
        rivet(s, x, 25 + dy, "brass")
    for x in range(38, 44):
        s.put(x, 23 + dy, b[5])
    # maw: brass flange with 12 bolts around the grinder
    mx, my = 46.5, 46.0 + dy
    flange = ring_mask(mx, my, 10.6, 13.0)
    s.part(flange, "brass", round_shade(mx, my, 13.0, 6, gain=1.3, bias=0.0), shadow=(1, 1))
    for k in range(12):
        a = math.radians(k * 30 + 15)
        x, y = int(mx + math.cos(a) * 11.8), int(my + math.sin(a) * 11.8)
        lit = math.cos(a) * LIGHT[0] + math.sin(a) * LIGHT[1] > 0
        s.put(x, y, b[5] if lit else b[1])
    cavity = ellipse_mask(mx, my, 10.8, 10.8)
    for (x, y) in cavity:
        s.put(x, y, i[0] if math.hypot(x + 0.5 - mx, y + 0.5 - my) > 9.8 else i[1])
    rot = math.radians(frame * 5)                         # outer ring, 12 teeth, 5 degrees per frame
    for k in range(12):
        a0 = rot + math.radians(k * 30)
        base_l, base_r = a0 - math.radians(11), a0 + math.radians(11)
        tip = a0 + math.radians(5)
        tri = poly_mask([(mx + math.cos(base_l) * 10.4, my + math.sin(base_l) * 10.4),
                         (mx + math.cos(base_r) * 10.4, my + math.sin(base_r) * 10.4),
                         (mx + math.cos(tip) * 6.0, my + math.sin(tip) * 6.0)])
        facing = -(math.cos(a0) * LIGHT[0] + math.sin(a0) * LIGHT[1])     # inward-facing tooth faces
        for (x, y) in tri:
            if (x, y) in cavity:
                ang = math.atan2(y + 0.5 - my, x + 0.5 - mx)
                lead = math.sin(ang - a0) < 0
                k_ = (4 if facing > 0.2 else 3) if lead else (3 if facing > 0.2 else 2)
                s.put(x, y, i[k_])
    rot2 = -math.radians(frame * 7.5)                     # inner drum, 8 teeth, turning back
    for (x, y) in ellipse_mask(mx, my, 5.4, 5.4):
        d = math.hypot(x + 0.5 - mx, y + 0.5 - my)
        s.put(x, y, i[0] if d > 4.6 else i[2] if d > 3.6 else i[1])
    for k in range(8):
        a0 = rot2 + math.radians(k * 45)
        for r, kk in ((4.4, 3), (5.4, 4), (6.2, 3)):
            s.put(int(mx + math.cos(a0) * r), int(my + math.sin(a0) * r), i[kk])
    for (x, y) in ellipse_mask(mx, my, 3.0, 3.0):         # the throat
        d = math.hypot(x + 0.5 - mx, y + 0.5 - my)
        s.put_glow(x, y, e[3] if d < 1.3 else (e[2] if d < 2.3 else e[1]))
    # serrated mandible blades on hydraulic rods
    for side in (-1, 1):
        ox = mx + side * 15
        rod = capsule_mask((ox + side * 5, 50 + dy), (ox + side * 8, 40 + dy), 1.1)
        s.part(rod, "iron", lambda x, y: 4)
        jaw = poly_mask([(ox - side * 2, 46 + dy), (ox + side * 6, 49 + dy), (ox + side * 6, 61 + dy),
                         (ox - side * 2, 67 + dy), (ox - side * 7, 61 + dy)])
        jin = s.part(jaw, "iron", form_bevel(jaw, ox - 4, 44 + dy, 14, 5, gain=1.2, bias=0.05, hi=3), shadow=(1, 2))
        for (x, y) in sorted(jin):                        # brass reinforcing band
            if 54 + dy <= y <= 55 + dy:
                s.put(x, y, b[3] if y == 54 + dy else b[1])
        for (x, y) in sorted(jaw):                        # teeth along the inner edge
            if (x - side, y) not in jaw and y > 56 + dy and y % 2 == 0:
                s.put(x - side, y, i[4])
                s.put(x - side, y + 1, i[2])
        rivet(s, int(ox), 51 + dy)
        rivet(s, int(ox) - side * 2, 59 + dy)
        grime(s, jin, rng, 0.06, [c[1], RAMP["leather"][0]])
    for (x, y) in ((61, 33), (62, 34), (31, 46)):         # dents in the housing
        s.put(x, y + dy, v[1])
        s.put(x - 1, y - 1 + dy, v[3])
    s.put(33, 27 + dy, WHITE)                              # specular glints
    s.put(32, 26 + dy, v[3])
    s.put(39, 23 + dy, WHITE)


def left_arm(s, dy, rng):
    """Brass excavator boom, chrome piston, gear elbow, toothed bucket fist (planted)."""
    b, i, c = RAMP["brass"], RAMP["iron"], RAMP["copper"]
    sh, el = (18, 33 + dy), (11, 53)
    upper = capsule_mask(sh, el, 5.4)
    uin = s.part(upper, "brass", cyl_shade(sh, el, 5.4, 6, gain=1.25, bias=0.05))
    for t in (0.35, 0.7):
        x, y = sh[0] + (el[0] - sh[0]) * t, sh[1] + (el[1] - sh[1]) * t
        for dx in (-3, 2):
            rivet(s, int(x) + dx, int(y), "brass")
        line(s, (x - 4, y + 2), (x + 4, y + 2), lambda n: b[1])
    grime(s, uin, rng, 0.05, [b[1], RAMP["leather"][0]])
    cyl0, cyl1 = (8, 31 + dy), (5, 42)                    # hydraulic piston on the outside
    s.part(capsule_mask(cyl0, cyl1, 2.0), "iron", cyl_shade(cyl0, cyl1, 2.0, 5, gain=1.5))
    s.part(capsule_mask((5, 42), (4, 51), 1.0), "iron", lambda x, y: 4)
    s.put(4, 45, WHITE)
    s.part(capsule_mask((5, 41), (5, 43), 1.6), "brass", lambda x, y: 3)
    fa0, fa1 = (11, 55), (12, 70)
    fore = capsule_mask(fa0, fa1, 5.0)
    fin = s.part(fore, "brass", cyl_shade(fa0, fa1, 5.0, 6, gain=1.25, bias=0.05))
    for y in (59, 65):
        for x in range(7, 17):
            if (x, y) in fin:
                s.put(x, y, b[1])
                if (x, y + 1) in fin:
                    s.put(x, y + 1, b[4])
    # the bucket: a rust-red excavator scoop seen side-on, rounded back to the outside, open mouth toward the body,
    # its teeth dug into the ground
    bucket = poly_mask([(10, 66), (3, 68), (0, 73), (0, 79), (3, 83), (24, 83), (27, 80), (25, 74), (19, 67)])
    bin_ = s.part(bucket, "copper", form_bevel(bucket, 4, 66, 22, 5, gain=1.25, bias=0.05, hi=3), shadow=(1, 1))
    mouth = poly_mask([(19, 70), (24, 75), (25, 80), (17, 80), (15, 74)])
    for (x, y) in mouth:                                  # the dark inside of the scoop; its rim catches the light
        s.put(x, y, i[0] if (x - 1, y) in mouth else c[4])
    for (x, y) in ((4, 71), (5, 72), (3, 76)):            # the curved back's lit edge
        s.put(x, y, c[4])
    for y in range(69, 82, 3):                             # a strengthening rib with rivets along the side plate
        rivet(s, 10, y, "copper")
    for (x, y, k) in ((24, 81, 3), (25, 81, 4), (26, 82, 3), (25, 82, 2), (20, 82, 3), (21, 82, 4), (22, 83, 2),
                      (16, 82, 3), (17, 82, 4), (18, 83, 2)):
        s.put(x, y, i[k])                                  # teeth
    s.part(ellipse_mask(12, 67.5, 2.4, 2.4), "brass", round_shade(12, 67.5, 2.4, 6))   # hinge pin
    grime(s, bin_ - mouth, rng, 0.1, [c[1], RAMP["leather"][0]])
    gx, gy = 11.5, 53.5                                   # gear elbow
    teeth = set()
    for k in range(8):
        a = math.radians(k * 45 + 22)
        teeth |= capsule_mask((gx, gy), (gx + math.cos(a) * 5.8, gy + math.sin(a) * 5.8), 1.2)
    gear = ellipse_mask(gx, gy, 4.8, 4.8) | teeth
    s.part(gear, "iron", round_shade(gx, gy, 5.8, 4, gain=1.0, bias=-0.1), shadow=(1, 1))
    s.part(ellipse_mask(gx, gy, 2.2, 2.2), "brass", round_shade(gx, gy, 2.2, 6, gain=1.1))


def right_arm(s, dy, rng):
    """Rust-red crane arm, cable winch elbow, three-prong claw (planted)."""
    c, i, l = RAMP["copper"], RAMP["iron"], RAMP["leather"]
    sh, el = (91, 32 + dy), (97, 53)
    upper = capsule_mask(sh, el, 5.4)
    uin = s.part(upper, "copper", cyl_shade(sh, el, 5.4, 5, gain=1.25, bias=0.1))
    grime(s, uin, rng, 0.08, [c[1], l[0]])
    for t in (0.3, 0.65):
        x, y = sh[0] + (el[0] - sh[0]) * t, sh[1] + (el[1] - sh[1]) * t
        weld(s, (x - 4, y), (x + 4, y + 1))
    cyl0, cyl1 = (101, 32 + dy), (104, 42)
    s.part(capsule_mask(cyl0, cyl1, 2.0), "iron", cyl_shade(cyl0, cyl1, 2.0, 5, gain=1.5))
    s.part(capsule_mask((104, 42), (105, 51), 1.0), "iron", lambda x, y: 4)
    s.put(105, 45, WHITE)
    s.part(capsule_mask((104, 41), (104, 43), 1.6), "brass", lambda x, y: 3)
    fa0, fa1 = (97, 56), (96, 70)
    fore = capsule_mask(fa0, fa1, 4.8)
    fin = s.part(fore, "copper", cyl_shade(fa0, fa1, 4.8, 5, gain=1.25, bias=0.1))
    grime(s, fin, rng, 0.08, [c[1], l[0]])
    for y in (60, 66):
        for x in range(92, 102):
            if (x, y) in fin:
                s.put(x, y, c[1])
    palm = poly_mask([(86, 69), (106, 69), (107, 77), (85, 77)])
    s.part(palm, "iron", form_bevel(palm, 88, 64, 18, 5, gain=1.1, hi=3), shadow=(1, 1))
    for x in (89, 96, 103):
        rivet(s, x, 71)
    for (fx, lean) in ((88, -1), (96, 0), (104, 1)):
        prong = poly_mask([(fx - 2.5, 76), (fx + 2.5, 76), (fx + 2 + lean, 81), (fx + 1 + lean, 84), (fx - 1.5 + lean, 84), (fx - 2.5 + lean, 80)])
        s.part(prong, "iron", flat_bevel(prong, 3, 5))
        s.put(fx - 1 + lean, 78, i[4])
    wx, wy = 97.5, 53.5                                   # cable winch elbow
    drum = ellipse_mask(wx, wy, 5.4, 5.4)
    s.part(drum, "iron", round_shade(wx, wy, 5.4, 5, gain=1.1), shadow=(1, 1))
    for y in range(49, 59):
        for x in range(93, 103):
            if (x, y) in drum - boundary(drum) and (x + y) % 3 == 0:
                s.put(x, y, l[2] if y < 53 else l[1])
    s.put(97, 53, RAMP["brass"][4])
    s.put(98, 54, RAMP["brass"][1])


def girder(s, dy):
    """The steel bracket bolting the tyre to the torso."""
    m = poly_mask([(23, 16 + dy), (32, 16 + dy), (32, 31 + dy), (23, 31 + dy)])
    s.part(m, "iron", flat_bevel(m, 2, 5), shadow=(1, 2))
    for y in (19, 23, 27):
        s.put(27, y + dy, RAMP["iron"][0])
        s.put(28, y + dy, RAMP["iron"][0])
        s.put(27, y + 1 + dy, RAMP["iron"][3])


# ================================================================================================
# Frames
# ================================================================================================
SETTLE = (0, 0, 1, 1, 0, 0)                               # body offset per frame (1x px)


def draw_frame(frame):
    rng = random.Random(1337)                              # same grime every frame: nothing flickers
    s = Sprite()
    dy = SETTLE[frame]
    exhaust_stacks(s, dy)
    right_arm(s, dy, rng)
    left_arm(s, dy, rng)
    waist = torso(s, dy, rng)
    waist_guts(s, dy, frame, waist)
    hoses(s, dy)
    girder(s, dy)
    bed_shoulder(s, dy, rng)
    tyre_shoulder(s, dy)
    crane_boom(s, dy)
    head(s, dy, frame, rng)
    return s


def to_image(pixels):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = img.load()
    for (x, y), col in pixels.items():
        p[x, y] = col + (255,)
    return img


def sheet(images):
    out = Image.new("RGBA", (W, (H + PAD) * len(images)), (0, 0, 0, 0))
    for k, img in enumerate(images):
        out.alpha_composite(img, (0, k * (H + PAD)))
    return out


def export(img, rel):
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print(f"wrote {rel} ({img.width * 2}x{img.height * 2})")


def make_icon():
    """A dedicated 16x16 head icon (crop-free so it reads at map size): visor, three eyes, the grinder."""
    s = Sprite()
    i, b, e = RAMP["iron"], RAMP["brass"], RAMP["ember"]
    cx, cy = 7.5, 8.5
    s.part(ellipse_mask(cx, cy, 7.4, 7.0), "iron", round_shade(cx, cy, 7.4, 5, gain=1.2, bias=0.1))
    visor = poly_mask([(1, 4), (7.5, 1.5), (14, 4), (14, 6.5), (1, 6.5)])
    s.part(visor, "brass", flat_bevel(visor, 3, 6))
    for x in range(3, 13):
        s.put(x, 5, i[0])
    for x in (4, 7, 10):
        s.put(x, 5, e[3])
        s.put(x + 1, 5, e[2])
    s.part(ring_mask(cx, 10, 3.2, 4.6), "brass", round_shade(cx, 10, 4.6, 6, gain=1.3))
    for (x, y) in ellipse_mask(cx, 10, 3.2, 3.2):
        d = math.hypot(x + 0.5 - cx, y + 0.5 - 10)
        s.put(x, y, e[3] if d < 1.0 else (i[3] if (int(math.degrees(math.atan2(y + 0.5 - 10, x + 0.5 - cx))) // 45) % 2 else i[1]))
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = img.load()
    for (x, y), col in s.px.items():
        if 0 <= x < 16 and 0 <= y < 16:
            p[x, y] = col + (255,)
    return img


if __name__ == "__main__":
    frames = [draw_frame(f) for f in range(FRAMES)]
    export(sheet([to_image(f.px) for f in frames]), OUT + "TrashTr0m.png")
    export(sheet([to_image(f.glow) for f in frames]), OUT + "TrashTr0m_Glow.png")
    export(make_icon(), OUT + "TrashTr0m_Head_Boss.png")
