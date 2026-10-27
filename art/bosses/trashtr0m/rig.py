"""A tiny 2D pixel-art renderer for Cogpunk's layered bosses (D4: drawn at 1x, exported 2x nearest-neighbour).

Parts are shapes in their own local space (polygons, ellipses, capsules, rings) placed by an affine transform (rotate
about a pivot, then translate). A part is rasterised by inverse-mapping every 1x pixel centre into local space, so the
same part can be posed at any angle and still come out as clean pixel art: nothing is rotated as a bitmap, which is
why the C# code never rotates these sprites (rotated pixel art produces mixels).

Shading is done per part with hard steps on the Cogpunk ramps (no gradients): the light comes from the top-left and
towards the viewer, in rig space, and is rotated into each part's local space so a posed part stays lit correctly.
Every part is outlined with ramp 0 of its own material (its darkest shade), and can cast a one-step shadow on what is
already painted below-right of it.

Coordinates: rig space, 1 px = one art pixel, x to the right, y DOWN (so "up" is negative), origin on the ground under
the body pivot. A Canvas keeps pixels in rig space (negative keys allowed) and is cropped when exported.
"""
import math

RAMP = {
    "iron": [(21, 22, 28), (46, 50, 59), (79, 85, 98), (127, 135, 148), (183, 191, 202)],
    "brass": [(43, 26, 14), (90, 58, 23), (138, 93, 34), (184, 138, 51), (223, 185, 78), (246, 231, 161)],
    "copper": [(42, 18, 12), (94, 40, 23), (147, 68, 31), (196, 104, 58), (233, 160, 107)],
    "verd": [(23, 52, 48), (42, 94, 82), (71, 145, 126), (140, 201, 176)],
    "leather": [(47, 27, 20), (91, 54, 38), (138, 90, 60)],
    "steam": [(138, 144, 150), (195, 200, 205), (238, 241, 243), (255, 255, 255)],
    "ember": [(77, 20, 10), (163, 48, 26), (236, 113, 40), (255, 199, 90)],
    "aether": [(34, 26, 69), (70, 58, 147), (124, 107, 224), (198, 189, 255)],
}
WHITE = RAMP["steam"][3]
COLOR_INDEX = {}
for _name, _ramp in RAMP.items():
    for _k, _col in enumerate(_ramp):
        COLOR_INDEX.setdefault(_col, (_name, _k))

_L = (-0.55, -0.62, 0.56)
_ln = math.sqrt(sum(c * c for c in _L))
LIGHT = tuple(c / _ln for c in _L)                    # towards the light: up-left and towards the viewer


# ================================================================================================
# Affine transforms
# ================================================================================================
class Xf:
    """2x3 affine matrix mapping local -> rig space."""

    def __init__(self, a=1.0, b=0.0, c=0.0, d=1.0, tx=0.0, ty=0.0):
        self.a, self.b, self.c, self.d, self.tx, self.ty = a, b, c, d, tx, ty

    @staticmethod
    def pose(angle_deg=0.0, pivot=(0.0, 0.0), offset=(0.0, 0.0)):
        """Rotate by angle_deg (clockwise on screen, since y points down) about pivot, then translate by offset."""
        t = math.radians(angle_deg)
        ca, sa = math.cos(t), math.sin(t)
        px, py = pivot
        # p' = R (p - pivot) + pivot + offset
        return Xf(ca, -sa, sa, ca, px - ca * px + sa * py + offset[0], py - sa * px - ca * py + offset[1])

    def then(self, child):
        """self o child: apply child (a pose in this part's space) first, then self."""
        return Xf(self.a * child.a + self.b * child.c, self.a * child.b + self.b * child.d,
                  self.c * child.a + self.d * child.c, self.c * child.b + self.d * child.d,
                  self.a * child.tx + self.b * child.ty + self.tx, self.c * child.tx + self.d * child.ty + self.ty)

    def fwd(self, p):
        x, y = p
        return (self.a * x + self.b * y + self.tx, self.c * x + self.d * y + self.ty)

    def inv(self, p):
        det = self.a * self.d - self.b * self.c
        x, y = p[0] - self.tx, p[1] - self.ty
        return ((self.d * x - self.b * y) / det, (-self.c * x + self.a * y) / det)

    def vec(self, v):
        return (self.a * v[0] + self.b * v[1], self.c * v[0] + self.d * v[1])

    def rvec(self, v):
        """The rotation part only (a scaled pose keeps unit normals unit)."""
        k = math.sqrt(abs(self.a * self.d - self.b * self.c)) or 1.0
        return ((self.a * v[0] + self.b * v[1]) / k, (self.c * v[0] + self.d * v[1]) / k)

    def inv_vec(self, v):
        det = self.a * self.d - self.b * self.c
        return ((self.d * v[0] - self.b * v[1]) / det, (-self.c * v[0] + self.a * v[1]) / det)

    def angle(self):
        return math.degrees(math.atan2(self.c, self.a))


IDENT = Xf()


# ================================================================================================
# Shapes (local space): inside(x, y) and a local bounding box
# ================================================================================================
class Shape:
    def inside(self, x, y):
        raise NotImplementedError

    def bbox(self):
        raise NotImplementedError

    def __or__(self, other):
        return Union(self, other)

    def __sub__(self, other):
        return Minus(self, other)


class Poly(Shape):
    def __init__(self, pts):
        self.pts = [tuple(map(float, p)) for p in pts]

    def inside(self, x, y):
        pts, inside, j = self.pts, False, len(self.pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside

    def bbox(self):
        xs, ys = [p[0] for p in self.pts], [p[1] for p in self.pts]
        return min(xs), min(ys), max(xs), max(ys)


class Ellipse(Shape):
    def __init__(self, cx, cy, rx, ry):
        self.cx, self.cy, self.rx, self.ry = cx, cy, rx, ry

    def inside(self, x, y):
        return ((x - self.cx) / self.rx) ** 2 + ((y - self.cy) / self.ry) ** 2 <= 1.0

    def bbox(self):
        return self.cx - self.rx, self.cy - self.ry, self.cx + self.rx, self.cy + self.ry


class Ring(Shape):
    def __init__(self, cx, cy, r0, r1):
        self.cx, self.cy, self.r0, self.r1 = cx, cy, r0, r1

    def inside(self, x, y):
        d = math.hypot(x - self.cx, y - self.cy)
        return self.r0 <= d <= self.r1

    def bbox(self):
        return self.cx - self.r1, self.cy - self.r1, self.cx + self.r1, self.cy + self.r1


class Capsule(Shape):
    """A segment with round ends; r0 at p0 tapering to r1 at p1."""

    def __init__(self, p0, p1, r0, r1=None):
        self.p0, self.p1, self.r0 = p0, p1, r0
        self.r1 = r0 if r1 is None else r1

    def param(self, x, y):
        (x0, y0), (x1, y1) = self.p0, self.p1
        dx, dy = x1 - x0, y1 - y0
        ln2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / ln2))
        return t, math.hypot(x - (x0 + t * dx), y - (y0 + t * dy))

    def inside(self, x, y):
        t, d = self.param(x, y)
        return d <= self.r0 + (self.r1 - self.r0) * t

    def bbox(self):
        r = max(self.r0, self.r1)
        return (min(self.p0[0], self.p1[0]) - r, min(self.p0[1], self.p1[1]) - r,
                max(self.p0[0], self.p1[0]) + r, max(self.p0[1], self.p1[1]) + r)


class Union(Shape):
    def __init__(self, *shapes):
        self.shapes = shapes

    def inside(self, x, y):
        return any(s.inside(x, y) for s in self.shapes)

    def bbox(self):
        bs = [s.bbox() for s in self.shapes]
        return min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)


class Minus(Shape):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def inside(self, x, y):
        return self.a.inside(x, y) and not self.b.inside(x, y)

    def bbox(self):
        return self.a.bbox()


def box(x0, y0, x1, y1):
    return Poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


# ================================================================================================
# Lighting helpers
# ================================================================================================
def level(intensity, lo, hi, gain=1.0, bias=0.0):
    """Lighting intensity (-1..1) -> a ramp index in [lo, hi], hard steps."""
    v = (intensity * gain + bias + 1.0) * 0.5
    return max(lo, min(hi, lo + int(v * (hi - lo + 1))))


def lit(nx, ny, nz):
    """n . L for a rig-space normal."""
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


# ================================================================================================
# Rust (part-local value noise, so a patch stays on its part however the part is posed)
# ================================================================================================
RUST_DEFAULT = {"iron": 0.46, "brass": 0.42, "verd": 0.24, "copper": 0.0}
RUST_BOTTOM_BIAS = 0.2                               # rust gathers towards the bottom of each part (water runs down)
RUST_SCALE = 0.72                                     # global multiplier: the trash feel


def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _value_noise(x, y, cell, seed):
    gx, gy = x / cell, y / cell
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(x0, y0, seed), _hash(x0 + 1, y0, seed)
    c, d = _hash(x0, y0 + 1, seed), _hash(x0 + 1, y0 + 1, seed)
    top, bottom = a + (b - a) * sx, c + (d - c) * sx
    return top + (bottom - top) * sy


def rust_noise(x, y, seed):
    """0..1 blotchy noise: big patches (11 px) with ragged edges from a finer octave (4 px)."""
    return 0.72 * _value_noise(x, y, 11.0, seed) + 0.28 * _value_noise(x, y, 4.0, seed + 17)


# ================================================================================================
# Canvas
# ================================================================================================
class Canvas:
    def __init__(self):
        self.px = {}
        self.glow = {}

    def put(self, x, y, col):
        self.px[(x, y)] = col

    def put_glow(self, x, y, col):
        self.px[(x, y)] = col
        self.glow[(x, y)] = col

    def get(self, x, y):
        return self.px.get((x, y))

    def darken(self, x, y, steps=1):
        """One step down the pixel's own ramp, never onto its outline shade (ramp 0 stays for edges)."""
        col = self.px.get((x, y))
        if col is None or (x, y) in self.glow or col not in COLOR_INDEX:
            return
        ramp, idx = COLOR_INDEX[col]
        if idx <= 1:
            return
        self.px[(x, y)] = RAMP[ramp][max(1, idx - steps)]

    def raster(self, xf, shape):
        """Rig-space pixels whose centre maps inside the shape."""
        x0, y0, x1, y1 = shape.bbox()
        corners = [xf.fwd(p) for p in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        cx0 = int(math.floor(min(p[0] for p in corners))) - 1
        cx1 = int(math.ceil(max(p[0] for p in corners))) + 1
        cy0 = int(math.floor(min(p[1] for p in corners))) - 1
        cy1 = int(math.ceil(max(p[1] for p in corners))) + 1
        mask = set()
        for y in range(cy0, cy1 + 1):
            for x in range(cx0, cx1 + 1):
                lx, ly = xf.inv((x + 0.5, y + 0.5))
                if shape.inside(lx, ly):
                    mask.add((x, y))
        return mask

    def part(self, xf, shape, ramp, shade, outline=True, shadow=None, glow=False, depth=0, clip=None, rust=None):
        """Paints a shape. shade(info) -> ramp index for each interior pixel (info: see Info). Returns the interior
        pixel set (rig space) for details. shadow=(dx, dy): darkens what lies that far below-right first. depth > 0
        darkens the whole part that many ramp steps (the far layer of a multiplane sprite). rust (0..1, default by
        material, RUST_DEFAULT): patches of the interior turn to the copper ramp at the same shade, the worst of them
        one step darker, with short drips running down; the noise lives in the part's own space, so the patches stay
        put on a moving part. Lone rust pixels are cleaned up (D4: no orphan pixels)."""
        mask = self.raster(xf, shape)
        if clip is not None:
            mask &= clip
        if not mask:
            return set()
        if shadow:
            sx, sy = shadow
            steps = max(abs(sx), abs(sy))
            cast = set()
            for (x, y) in mask:
                for k in range(1, steps + 1):
                    cast.add((x + round(sx * k / steps), y + round(sy * k / steps)))
            for q in cast - mask:
                self.darken(*q)
        edge = {p for p in mask if any((p[0] + ox, p[1] + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))} if outline else set()
        inner = mask - edge
        info = Info(xf, mask, inner)
        r = RAMP[ramp]
        put = self.put_glow if glow else self.put
        amount = 0.0 if glow else (RUST_DEFAULT.get(ramp, 0.0) if rust is None else rust) * RUST_SCALE
        scale = math.sqrt(abs(xf.a * xf.d - xf.b * xf.c)) or 1.0
        bx0, by0, bx1, by1 = shape.bbox()
        seed = int(bx0 * 7 + by0 * 13 + bx1 * 17 + by1 * 19 + len(ramp) * 31) & 0xFFFF
        cu = RAMP["copper"]
        rusted = {}
        base = {}
        my0 = min(q[1] for q in mask)
        my1 = max(q[1] for q in mask)
        span = max(1, my1 - my0)
        for p in mask:
            if p in edge:
                put(p[0], p[1], r[0])
            else:
                info.at(p)
                k = shade(info)
                if depth:
                    k = max(1, k - depth)
                k = max(0, min(len(r) - 1, k))
                put(p[0], p[1], r[k])
                if amount > 0.0:
                    n = rust_noise(info.lx * scale, info.ly * scale, seed) + RUST_BOTTOM_BIAS * (p[1] - my0) / span
                    if n > 1.0 - amount * 0.62:
                        deep = n > 1.0 - amount * 0.25
                        kk = max(1, min(len(cu) - 1, k - (1 if deep else 0)))
                        rusted[p] = cu[kk]
                        base[p] = r[k]
        if rusted:
            for p in list(rusted):                      # no lone rust pixels
                if not any((p[0] + ox, p[1] + oy) in rusted for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    del rusted[p]
            for p, col in rusted.items():
                put(p[0], p[1], col)
            for (x, y) in rusted:                       # drips under the patches
                if (x, y + 1) in inner and (x, y + 1) not in rusted and _hash(x, y, seed + 5) < 0.3:
                    length = 2 + int(_hash(x, y, seed + 9) * 2)
                    if all((x, y + k) in inner for k in range(1, length + 1)):
                        for k in range(1, length + 1):
                            put(x, y + k, cu[1] if k < length else cu[2])
        return inner


class Info:
    """What a shader sees for one pixel: rig pixel (x, y), its local point (lx, ly), the part's interior, and the
    one-pixel bevels (lit = top/left inner edge, dark = bottom/right inner edge, in rig space)."""

    def __init__(self, xf, mask, inner):
        self.xf, self.mask, self.inner = xf, mask, inner
        self.lit = {p for p in inner if (p[0], p[1] - 1) not in inner or (p[0] - 1, p[1]) not in inner}
        self.dark = {p for p in inner if (p[0], p[1] + 1) not in inner or (p[0] + 1, p[1]) not in inner}
        self.x = self.y = 0
        self.lx = self.ly = 0.0

    def at(self, p):
        self.x, self.y = p
        self.lx, self.ly = self.xf.inv((p[0] + 0.5, p[1] + 0.5))

    def bevel(self):
        """+1 on the lit edge, -1 on the dark edge, 0 inside."""
        p = (self.x, self.y)
        if p in self.lit and p not in self.dark:
            return 1
        if p in self.dark and p not in self.lit:
            return -1
        return 0


# --- shaders (factories returning shade(info) -> index) -------------------------------------------------------------
def flat(k, bevel=True, hi=None):
    def shade(i):
        v = k + (i.bevel() if bevel else 0)
        return v if hi is None else min(hi, v)
    return shade


def face(normal, lo=1, hi=None, gain=1.2, bias=0.0, bevel=True, ramp_len=5):
    """A flat face whose local normal (nx, ny, nz) is turned by the part's transform."""
    hi = ramp_len - 1 if hi is None else hi

    def shade(i):
        wx, wy = i.xf.rvec((normal[0], normal[1]))
        k = level(lit(wx, wy, normal[2]), lo, hi, gain, bias)
        if bevel:
            k += i.bevel()
        return max(1, min(ramp_len - 1, k))
    return shade


def dome(cx, cy, r, lo=1, hi=4, gain=1.25, bias=0.0, bevel=False):
    """A sphere-ish bulge centred on a local point."""
    def shade(i):
        dx, dy = (i.lx - cx) / r, (i.ly - cy) / r
        d2 = min(1.0, dx * dx + dy * dy)
        wx, wy = i.xf.rvec((dx, dy))
        k = level(lit(wx, wy, math.sqrt(1.0 - d2)), lo, hi, gain, bias)
        return max(lo, min(hi, k + (i.bevel() if bevel else 0)))
    return shade


def cyl(p0, p1, r, lo=1, hi=4, gain=1.4, bias=0.0, bands=0, band_lo=None):
    """A cylinder along a local axis; bands > 0 adds corrugation rings every `bands` px along the axis."""
    (x0, y0), (x1, y1) = p0, p1
    ax, ay = x1 - x0, y1 - y0
    ln = math.hypot(ax, ay) or 1e-6
    ux, uy = ax / ln, ay / ln
    nx, ny = -uy, ux

    def shade(i):
        s = ((i.lx - x0) * nx + (i.ly - y0) * ny) / r
        s = max(-1.0, min(1.0, s))
        wx, wy = i.xf.rvec((s * nx, s * ny))
        k = level(lit(wx, wy, math.sqrt(1.0 - s * s)), lo, hi, gain, bias)
        if bands:
            t = (i.lx - x0) * ux + (i.ly - y0) * uy
            if int(math.floor(t)) % bands == 0:
                k = max(band_lo if band_lo is not None else lo, k - 1)
        return k
    return shade


# ================================================================================================
# Details (rig space)
# ================================================================================================
def rivet(cv, xf, p, ramp="iron", inner=None):
    x, y = (int(math.floor(v)) for v in xf.fwd(p))
    r = RAMP[ramp]
    if inner is None or ((x, y) in inner and (x + 1, y + 1) in inner):
        cv.put(x, y, r[-1])
        cv.put(x + 1, y + 1, r[1])


def bolt(cv, xf, p, ramp="brass", inner=None):
    x, y = (int(math.floor(v)) for v in xf.fwd(p))
    r = RAMP[ramp]
    pts = ((x, y, r[-1]), (x + 1, y, r[2]), (x, y + 1, r[2]), (x + 1, y + 1, r[0]))
    if inner is None or all((a, b) in inner for a, b, _ in pts):
        for a, b, c in pts:
            cv.put(a, b, c)


def seg_pixels(p0, p1):
    (x0, y0), (x1, y1) = (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1])))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, out = dx + dy, []
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def seam(cv, xf, p0, p1, ramp, inner, dark=1, light=None):
    """A panel seam: a dark groove whose lower/right lip catches the light (top-left light)."""
    r = RAMP[ramp]
    a, b = xf.fwd(p0), xf.fwd(p1)
    pts = seg_pixels(a, b)
    horizontal = abs(b[0] - a[0]) >= abs(b[1] - a[1])
    lip = (0, 1) if horizontal else (1, 0)
    lcol = r[light if light is not None else min(len(r) - 1, 3)]
    for (x, y) in pts:
        if (x, y) in inner:
            cv.put(x, y, r[dark])
            q = (x + lip[0], y + lip[1])
            if q in inner and q not in pts:
                cv.put(q[0], q[1], lcol)


def line(cv, xf, p0, p1, color_at, inner=None):
    for n, (x, y) in enumerate(seg_pixels(xf.fwd(p0), xf.fwd(p1))):
        if inner is None or (x, y) in inner:
            c = color_at(n)
            if c is not None:
                cv.put(x, y, c)


def weld(cv, xf, p0, p1, inner):
    i = RAMP["iron"]
    line(cv, xf, p0, p1, lambda n: i[4] if n % 2 == 0 else i[3], inner)
    line(cv, xf, (p0[0], p0[1] + 1), (p1[0], p1[1] + 1), lambda n: i[1], inner)


def stripes(cv, region, period=3, a=None, b=None, slope=1):
    """Hazard stripes across a pixel region (rig space): bands of colour a and b along x + slope*y."""
    a = a or RAMP["brass"][4]
    b = b or RAMP["iron"][0]
    for (x, y) in region:
        cv.put(x, y, a if ((x + slope * y) // period) % 2 == 0 else b)


def grime(cv, region, rng, amount, colors):
    """Rust and dirt as short vertical streaks running down from a seam (2-3 px), never lone pixels (D4)."""
    pts = sorted(region)
    if not pts:
        return
    for _ in range(int(len(pts) * amount * 0.4)):
        x, y = pts[rng.randrange(len(pts))]
        col = colors[rng.randrange(len(colors))]
        length = 2 + rng.randrange(2)
        if all((x, y + k) in region for k in range(length)):
            for k in range(length):
                cv.put(x, y + k, col)


def ik(shoulder, hand, l1, l2, bend=1):
    """Two-bone IK: the elbow for a shoulder-hand pair (bend = +1 puts the elbow on the left of the shoulder->hand
    direction, which for an arm reaching forward-left and down is up/back). Unreachable targets are clamped."""
    sx, sy = shoulder
    hx, hy = hand
    dx, dy = hx - sx, hy - sy
    d = max(1e-6, math.hypot(dx, dy))
    d_c = min(d, l1 + l2 - 0.01)
    a = (l1 * l1 - l2 * l2 + d_c * d_c) / (2 * d_c)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / d, dy / d
    mx, my = sx + ux * a, sy + uy * a
    ex, ey = mx + bend * h * uy, my - bend * h * ux
    return (ex, ey), (sx + ux * min(d, l1 + l2), sy + uy * min(d, l1 + l2))
