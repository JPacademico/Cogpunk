"""Sculpt: model a creature at sub-pixel density, then pixelate it per part (2026-11-23, the cogpunk-pixel-art skill's
"model, then pixelate" method, after codixel). Every art pixel is SS x SS samples; each sample knows which part is in front
and the surface normal there; a pixel takes the part that covers most of its samples (the mode: colours never mix across
a part boundary, edges come out smooth), and its shade from the part's mean normal under one light, in flat bands of the
part's ramp with a checker dither only in a narrow strip at band edges (the checker counted in the part's own space, so it
stays put when the part moves). Then: structured texture (bumps that bend the normal, spots one ramp step off, pixel-perfect
fold lines), a selective outline (the darkest step on the far side and against parts behind, a middle step on the lit side),
a rim light one step up just inside the lit outline, a one-pixel cast shadow on parts behind, and hand-placed features.

Shapes are in art pixels (1x), y down; a part's texture lives in its own frame (anchor + angle), so it moves with the part.
"""
import math

LIGHT = (-0.55, -0.70, 0.46)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)


class Frame:
    """A part's own frame: anchor (x, y) and angle (radians); to_local maps art px to the part's coordinates."""

    def __init__(self, x=0.0, y=0.0, angle=0.0, sx=1.0, sy=1.0):
        self.x, self.y, self.a, self.sx, self.sy = x, y, angle, sx, sy
        self.c, self.s = math.cos(angle), math.sin(angle)

    def to_local(self, x, y):
        dx, dy = x - self.x, y - self.y
        return (dx * self.c + dy * self.s) / self.sx, (-dx * self.s + dy * self.c) / self.sy

    def to_world(self, lx, ly):
        lx, ly = lx * self.sx, ly * self.sy
        return self.x + lx * self.c - ly * self.s, self.y + lx * self.s + ly * self.c

    def rot(self, nx, ny):
        return nx * self.c - ny * self.s, nx * self.s + ny * self.c


class Ell:
    """An ellipsoid seen from the front: (cx, cy) the centre and (rx, ry) the radii in the part's frame; `flat` squashes the
    normal towards the viewer (0: a sphere, 1: a flat disc)."""

    def __init__(self, cx, cy, rx, ry, flat=0.0):
        self.cx, self.cy, self.rx, self.ry, self.flat = cx, cy, rx, ry, flat

    def bbox(self):
        r = max(self.rx, self.ry)
        return self.cx - r, self.cy - r, self.cx + r, self.cy + r

    def sample(self, lx, ly):
        u, v = (lx - self.cx) / self.rx, (ly - self.cy) / self.ry
        d2 = u * u + v * v
        if d2 > 1.0:
            return None
        nz = math.sqrt(1.0 - d2)
        k = 1.0 - self.flat
        n = (u * k, v * k, nz + self.flat)
        m = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        return n[0] / m, n[1] / m, n[2] / m


class Tube:
    """A tube along a polyline (pts with radii): round across its axis, its ends round. For limbs, frills, tongues."""

    def __init__(self, pts, radii):
        self.pts, self.radii = pts, radii

    def bbox(self):
        r = max(self.radii)
        xs, ys = [p[0] for p in self.pts], [p[1] for p in self.pts]
        return min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r

    def sample(self, lx, ly):
        best = None
        for (a, b), (ra, rb) in zip(zip(self.pts, self.pts[1:]), zip(self.radii, self.radii[1:])):
            vx, vy = b[0] - a[0], b[1] - a[1]
            ln2 = vx * vx + vy * vy or 1e-9
            t = max(0.0, min(1.0, ((lx - a[0]) * vx + (ly - a[1]) * vy) / ln2))
            px, py = a[0] + vx * t, a[1] + vy * t
            r = ra + (rb - ra) * t
            dx, dy = lx - px, ly - py
            d = math.hypot(dx, dy)
            if d <= r and (best is None or d / r < best[0]):
                best = (d / r, dx / (d or 1.0), dy / (d or 1.0))
        if best is None:
            return None
        q, ux, uy = best
        nz = math.sqrt(max(0.0, 1.0 - q * q))
        return ux * q, uy * q, nz


class Poly:
    """A flat polygon facing the viewer (a membrane, a plate): its normal straight out, `tilt` leaning it towards (tx, ty)."""

    def __init__(self, pts, tilt=(0.0, 0.0)):
        self.pts, self.tilt = pts, tilt

    def bbox(self):
        xs, ys = [p[0] for p in self.pts], [p[1] for p in self.pts]
        return min(xs), min(ys), max(xs), max(ys)

    def sample(self, lx, ly):
        inside = False
        n = len(self.pts)
        j = n - 1
        for i in range(n):
            xi, yi = self.pts[i]
            xj, yj = self.pts[j]
            if (yi > ly) != (yj > ly) and lx < (xj - xi) * (ly - yi) / (yj - yi + 1e-12) + xi:
                inside = not inside
            j = i
        if not inside:
            return None
        tx, ty = self.tilt
        m = math.sqrt(tx * tx + ty * ty + 1.0)
        return tx / m, ty / m, 1.0 / m


class Part:
    """A part: a shape in its frame, a ramp (darkest first), a depth (higher is in front), a shading range [lo, hi] of the
    ramp, texture (bumps (x, y, r) that bend the normal outwards, spots (x, y, rx, ry, steps), fold lines [(x, y)...] one step
    darker), whether it glows (its pixels also go to the glow layer at this ramp index or more), an outline flag."""

    def __init__(self, name, shape, ramp, z, frame=None, lo=1, hi=None, gain=1.15, bias=0.0, ambient=0.18, dither=0.18,
                 bumps=(), spots=(), lines=(), glow_from=None, outline=True, plane="mid", bump_gain=1.0, bump_step=True):
        self.name, self.shape, self.ramp, self.z = name, shape, ramp, z
        self.frame = frame or Frame()
        self.lo, self.hi = lo, (len(ramp) - 1 if hi is None else hi)
        self.gain, self.bias, self.ambient, self.dither = gain, bias, ambient, dither
        self.bumps, self.spots, self.lines = bumps, spots, lines
        self.glow_from, self.outline, self.plane = glow_from, outline, plane
        self.bump_gain = bump_gain
        self.bump_step = bump_step

    def world_bbox(self):
        x0, y0, x1, y1 = self.shape.bbox()
        pts = [self.frame.to_world(x, y) for x in (x0, x1) for y in (y0, y1)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def normal_at(self, wx, wy):
        lx, ly = self.frame.to_local(wx, wy)
        n = self.shape.sample(lx, ly)
        if n is None:
            return None
        nx, ny, nz = n
        for (bx, by, br) in self.bumps:                        # a wart: a small dome on the surface
            du, dv = (lx - bx) / br, (ly - by) / br
            d2 = du * du + dv * dv
            if d2 < 1.0:
                w = 0.85 * self.bump_gain * (1.0 - d2)
                nx, ny = nx + du * w, ny + dv * w
        nx, ny = self.frame.rot(nx, ny)
        m = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        return nx / m, ny / m, nz / m


def render(parts, w, h, ox, oy, ss=4, light=LIGHT):
    """Renders the parts into a w x h cell (art px), the rig origin at (ox, oy). Returns (px, glow, owner): pixel colours,
    glow colours and the owning part per pixel, keyed (x, y) in cell coordinates."""
    parts = sorted(parts, key=lambda p: p.z)
    top = {}                                                   # sample (sx, sy) -> (z, index, normal)
    for idx, part in enumerate(parts):
        x0, y0, x1, y1 = part.world_bbox()
        sx0, sy0 = max(0, int(math.floor((x0 + ox) * ss))), max(0, int(math.floor((y0 + oy) * ss)))
        sx1, sy1 = min(w * ss - 1, int(math.ceil((x1 + ox) * ss))), min(h * ss - 1, int(math.ceil((y1 + oy) * ss)))
        for sy in range(sy0, sy1 + 1):
            wy = (sy + 0.5) / ss - oy
            for sx in range(sx0, sx1 + 1):
                wx = (sx + 0.5) / ss - ox
                n = part.normal_at(wx, wy)
                if n is not None:
                    top[(sx, sy)] = (part.z, idx, n)
    owner, normal = {}, {}
    half = ss * ss // 2
    for y in range(h):
        for x in range(w):
            counts = {}
            sums = {}
            for j in range(ss):
                for i in range(ss):
                    t = top.get((x * ss + i, y * ss + j))
                    if t is None:
                        continue
                    _, idx, n = t
                    counts[idx] = counts.get(idx, 0) + 1
                    s = sums.setdefault(idx, [0.0, 0.0, 0.0])
                    s[0] += n[0]
                    s[1] += n[1]
                    s[2] += n[2]
            covered = sum(counts.values())
            if covered < half:
                continue
            idx = max(counts, key=lambda k: (counts[k], parts[k].z))
            s = sums[idx]
            m = math.sqrt(s[0] ** 2 + s[1] ** 2 + s[2] ** 2) or 1.0
            owner[(x, y)] = idx
            normal[(x, y)] = (s[0] / m, s[1] / m, s[2] / m)
    # shade in bands, dither at band edges (part space)
    index = {}
    for (x, y), idx in owner.items():
        part = parts[idx]
        n = normal[(x, y)]
        lit = n[0] * light[0] + n[1] * light[1] + n[2] * light[2]
        v = max(0.0, min(1.0, part.ambient + (1.0 - part.ambient) * max(0.0, lit) * part.gain + part.bias))
        span = part.hi - part.lo + 1
        f = v * span
        k = int(f)
        frac = f - k
        lx, ly = part.frame.to_local(x - ox + 0.5, y - oy + 0.5)
        if part.dither > 0.0 and ((int(math.floor(lx)) + int(math.floor(ly))) & 1) == 0:
            if frac > 1.0 - part.dither:
                k += 1
            elif frac < part.dither:
                k -= 1
        k = part.lo + max(0, min(span - 1, k))
        if part.bump_step:                                    # a wart steps the colour: up on its lit side, down under it
            ll = math.hypot(light[0], light[1]) or 1.0
            for (bx, by, br) in part.bumps:
                du, dv = (lx - bx) / br, (ly - by) / br
                if du * du + dv * dv < 1.0:
                    t = -(du * light[0] + dv * light[1]) / ll
                    if t < -0.25:
                        k += 1
                    elif t > 0.3:
                        k -= 1
                    break
        for (sx_, sy_, rx, ry, steps) in part.spots:
            if ((lx - sx_) / rx) ** 2 + ((ly - sy_) / ry) ** 2 <= 1.0:
                k += steps
        index[(x, y)] = max(1, min(len(part.ramp) - 1, k))
    # fold lines: pixel-perfect, one step darker
    for idx, part in enumerate(parts):
        for line in part.lines:
            for (a, b) in zip(line, line[1:]):
                ax, ay = part.frame.to_world(*a)
                bx, by = part.frame.to_world(*b)
                steps = int(max(abs(bx - ax), abs(by - ay))) + 1
                last = None
                for k in range(steps + 1):
                    t = k / max(1, steps)
                    q = (int(math.floor(ax + (bx - ax) * t + ox)), int(math.floor(ay + (by - ay) * t + oy)))
                    if q == last or owner.get(q) != idx:
                        continue
                    index[q] = max(1, index[q] - 1)
                    last = q
    # outline, rim light, cast shadow
    out = {}
    for (x, y), idx in owner.items():
        part = parts[idx]
        k = index[(x, y)]
        if part.outline:
            behind = []
            edge_lit = edge_dark = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                o = owner.get(q)
                if o is None or parts[o].z < part.z and o != idx:
                    lit_side = (dx * light[0] + dy * light[1]) > 0.1
                    if o is None:
                        if lit_side:
                            edge_lit = True
                        else:
                            edge_dark = True
                    else:
                        behind.append(q)
                        edge_dark = edge_dark or not lit_side
            if edge_dark:
                k = 0
            elif edge_lit:
                k = max(1, min(k, (part.lo + part.hi) // 2))
            elif behind:
                k = max(1, k - 2)
        out[(x, y)] = k
    for (x, y), idx in owner.items():                          # rim light just inside a lit outline
        part = parts[idx]
        if out[(x, y)] in (0,) or not part.outline:
            continue
        for dx, dy in ((-1, 0), (0, -1)):
            q = (x + dx, y + dy)
            if owner.get(q) == idx and out[q] != index[q]:     # the neighbour towards the light is the outline
                out[(x, y)] = min(len(part.ramp) - 1, out[(x, y)] + 1)
                break
    for (x, y), idx in owner.items():                          # a cast shadow on parts behind, under and right of a front part
        part = parts[idx]
        for dx, dy in ((1, 1), (0, 1)):
            q = (x + dx, y + dy)
            o = owner.get(q)
            if o is not None and parts[o].z < part.z and out[q] > 1:
                out[q] = max(1, out[q] - 1)
    px, glow = {}, {}
    for (x, y), idx in owner.items():
        part = parts[idx]
        c = part.ramp[out[(x, y)]]
        px[(x, y)] = c
        if part.glow_from is not None and out[(x, y)] >= part.glow_from:
            glow[(x, y)] = c
    return px, glow, {q: parts[i].name for q, i in owner.items()}


def hue_ramp(stops, n):
    """A ramp of n colours through the given RGB stops (darkest first), interpolated in RGB: for building new palette ramps."""
    out = []
    for k in range(n):
        t = k / (n - 1) * (len(stops) - 1)
        i = min(len(stops) - 2, int(t))
        f = t - i
        a, b = stops[i], stops[i + 1]
        out.append(tuple(int(round(a[c] + (b[c] - a[c]) * f)) for c in range(3)))
    return out
