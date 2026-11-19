"""World backdrops ("plates") for Cogpunk's teaser, rendered by the same replays that make the D5 proofs (tools/sim): the
passes' own constants and blueprints, the real tile sheets. Run from the repo root (the sims open files relative to it).

    coghaven()   the island (CoghavenPass replayed): static plate + its animated cogs, turbines and smoke
    westworld()  Old Brass Town's street, lit by its torches and lanterns (OldBrassTownPass replayed)
    ruins()      the Fundamental Ruins' gate hall and arena, the stone under its shield (FundamentalRuinsPass replayed)
    junkyard()   the Junkyard's central heap of Rusted Scrap round the cache, at dusk
    tar_pool()   the Junkyard's tar pool (the Tar Tyrant's)

Vanilla blocks the repo has no art for (sand, clouds, dirt, Dynasty furniture) are the sims' flat stand-ins.
"""
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
sys.path.insert(0, HERE)

from stage import ROOT, load  # noqa: E402

TILE = 16
_cache = {}


def once(fn):
    def wrapped(*a):
        key = (fn.__name__,) + a
        if key not in _cache:
            _cache[key] = fn(*a)
        return _cache[key]
    return wrapped


class Coghaven:
    """The island plate (its own sky baked in) and what moves on it."""

    def __init__(self):
        import coghaven_sim as cg
        self.cg = cg
        self.isl = cg.Island(obstacle=300, seed=7)
        self.isl.generate()
        self.r = cg.Renderer(self.isl)
        self.static = self.r.static
        self.smoke = cg.Smoke(random.Random(9))
        for _ in range(160):                               # the smoke already flowing
            self.smoke.emit(self.isl)
            self.smoke.step()
        self._cog, self._tur = {}, {}
        self.tick = 0

    def px(self, tx, ty):
        """Plate px of tile (tx, ty) (island columns from its left edge, world rows)."""
        return (tx - self.r.x0) * TILE, (ty - self.r.y0) * TILE

    @property
    def surface_y(self):
        return self.px(0, self.isl.s)[1]

    def step(self):
        self.tick += 1
        self.smoke.emit(self.isl)
        self.smoke.step()

    def cog(self, f):
        if f not in self._cog:
            self._cog[f] = self.cg.assemble(self.r.cog, 6, 6, f)
        return self._cog[f]

    def turbine(self, f):
        if f not in self._tur:
            im = self.cg.assemble(self.r.turbine, 4, 6, f)
            im.alpha_composite(self.cg.assemble(self.r.turbine_glow, 4, 6, f))
            self._tur[f] = im
        return self._tur[f]

    def draw(self, view, ox=0, oy=0):
        """The plate at world (ox, oy), then the cogs, turbines and smoke at this tick."""
        view.plate(self.static, ox, oy)
        cog_frame = (self.tick // 8) % 12
        tur_frame = (self.tick // 4) % 4
        for kind, x, y, w, h, style in self.isl.multi:
            X, Y = self.px(x, y)
            if kind == "cog":
                view.put(self.cog(cog_frame if style == 0 else 11 - cog_frame), ox + X, oy + Y)
            else:
                view.put(self.turbine(tur_frame), ox + X, oy + Y)
        k_life = self.cg.K["Lifetime"]
        for (sx, sy, age) in self.smoke.view():
            k = 0 if age < 12 else 1 if age < 30 else 2 if age < 56 else 3
            puff = self.r.smoke.crop((0, k * 20, 20, k * 20 + 20))
            if age > k_life * 0.45:
                alpha = max(0.0, 1 - (age - k_life * 0.45) / (k_life * 0.55))
                puff.putalpha(puff.getchannel("A").point(lambda v: int(v * alpha)))
            view.put(puff, ox + int(sx - self.r.x0 * TILE - 10), oy + int(sy - self.r.y0 * TILE - 10))


@once
def coghaven():
    return Coghaven()


@once
def westworld():
    """(plate, street floor y in px, (x of the town's left end, x of its right end))."""
    import old_brass_town_sim as obt
    k = obt.constants(obt.PASS)
    bps, order = obt.blueprints()
    town = obt.Town(k, bps, order, 7)
    img = obt.draw_town(town, lit=True)
    sx, floor, shift = town.stone
    return img, floor * TILE, town


@once
def ruins(lit=(0.2, 0.2, 0.2), seal=True, seal_lit=(0.18, 0.18, 0.18)):
    """The gate hall over the arena (81 x 52 tiles): (plate, stone centre px, gate centre px)."""
    import update_2026_11_11b_sim as ub
    if "ruins_world" not in _cache:
        _cache["ruins_world"] = ub.build_world()
    world, r = _cache["ruins_world"]
    x0, y0, x1, y1 = r.cx - 40, r.fy - 47, r.cx + 40, r.fy + 4
    img = ub.draw_ruins(world, r, x0, y0, x1, y1, lit=lit, seal=seal, seal_lit=seal_lit)
    stone = ((r.stone_at[0] - x0 + 2) * TILE, (r.stone_at[1] - y0 + 3) * TILE) if r.stone_at else (img.width // 2, img.height - 160)
    gate = ((r.seal_at[0] - x0) * TILE + 72, (r.seal_at[1] - y0) * TILE + 24) if r.seal_at else (img.width // 2, 300)
    return img, stone, gate


def dusk_sky(w, h, top=(38, 30, 62), mid=(150, 74, 60), low=(236, 150, 84), horizon=0.72):
    """A banded dusk sky (hard steps: a pixel-art gradient), a low sun."""
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    bands = 22
    hz = int(h * horizon)
    for b in range(bands):
        f = b / (bands - 1)
        col = tuple(int(top[i] + (mid[i] - top[i]) * min(1.0, f * 1.6)) if f < 0.62 else int(mid[i] + (low[i] - mid[i]) * (f - 0.62) / 0.38)
                    for i in range(3))
        d.rectangle([0, hz * b // bands, w, hz * (b + 1) // bands], fill=col + (255,))
    d.rectangle([0, hz, w, h], fill=low + (255,))
    return img


HEAPS = {False: ((22, 9, 7), (44, 6, 5), (106, 8, 6), (130, 10, 8)),      # the yard's other heaps: (column, half width, height)
         True: ((14, 9, 7), (108, 6, 5), (132, 10, 8))}                    # the duel plate: columns 26..61 stay open ground


@once
def junkyard(duel=False):
    """(plate, ground y in px, heap centre x in px): the central heap of Rusted Scrap round the Junkyard Cache, smaller
    heaps either side, sand to the horizon (a stand-in: vanilla's), under a dusk sky with far heaps in silhouette.
    duel=True leaves a stretch of open ground left of the central heap (columns 26..61) for the weapon shots."""
    import trashtr0m_sim as tt
    from terrain import load_frames, render
    cols, rows, ground, solid, left, top = tt.build_heap()
    rng = random.Random(4)
    for (cx, half, height) in HEAPS[duel]:
        last = None
        for dx in range(-half, half + 1):
            pile = 1 - (dx / (half + 1)) ** 2
            t = ground - round(height * pile) + rng.choice((0, 0, 1))
            if last is not None and abs(t - last) > 2:
                t = last + (2 if t > last else -2)
            last = t
            for y in range(t, ground + 2):
                solid[(cx + dx, y)] = "R"
    w, h = cols * TILE, rows * TILE
    gy = ground * TILE
    world = dusk_sky(w, h, horizon=gy / h)
    d = ImageDraw.Draw(world)
    for k in range(7):                                      # far heaps: silhouettes against the sun
        cx = rng.randrange(0, w)
        hw, hh = rng.randrange(120, 260), rng.randrange(50, 130)
        d.polygon([(cx - hw, gy), (cx - hw // 3, gy - hh), (cx + hw // 4, gy - hh + 18), (cx + hw, gy)], fill=(74, 40, 46, 255))
    d.ellipse([w // 2 + 150, gy - 150, w // 2 + 250, gy - 50], fill=(255, 214, 130, 255))   # the low sun
    d.rectangle([0, gy, w, h], fill=(150, 104, 70, 255))    # sand in the last light (stand-in)
    for _ in range(w * (h - gy) // 260):
        sx, sy = rng.randrange(0, w, 2), rng.randrange(gy + 2, h, 2)
        d.rectangle([sx, sy, sx + 1, sy + 1], fill=(126, 84, 58, 255))
    d.line([0, gy, w, gy], fill=(196, 140, 90, 255), width=2)
    meta = load_frames(os.path.join(ROOT, "art/templates/terrain_exposure.json"))
    grid = ["".join("#" if solid.get((x, y)) == "R" else "." for x in range(cols)) for y in range(rows)]
    scrap = render(grid, {"#": load("Content/Scrap/Tiles/RustedScrapTile.png")}, meta, seed=6)
    world.alpha_composite(scrap)
    trunk = load("Content/Furniture/ScrappyTrunkTile.png")
    for x in range(2):
        for y in range(2):
            hgt = 16 if y == 0 else 18
            world.alpha_composite(trunk.crop((36 + x * 18, y * 18, 36 + x * 18 + 16, y * 18 + hgt)), ((left + x) * TILE, (top + y) * TILE))
    _cache[("junkyard_top", duel)] = [min([y for y in range(rows) if solid.get((x, y)) == "R"] + [ground]) * TILE for x in range(cols)]
    return world, gy, (left + 1) * TILE


def junkyard_top(x_px, duel=False):
    """The y (px) of the junkyard's surface under world x: the top of the scrap there, or the sand."""
    junkyard(duel)
    tops = _cache[("junkyard_top", duel)]
    return tops[max(0, min(len(tops) - 1, int(x_px) // TILE))]


@once
def tar_pool(w=1280, h=720, ground=520):
    """The Junkyard's tar pool at dusk (the Tar Tyrant's): the dusk sky, the pool's glossy black surface with a rim of sand."""
    world = dusk_sky(w, h, top=(30, 26, 52), mid=(110, 60, 60), low=(190, 110, 70), horizon=ground / h)
    d = ImageDraw.Draw(world)
    rng = random.Random(8)
    for k in range(5):
        cx = rng.randrange(0, w)
        hw, hh = rng.randrange(140, 280), rng.randrange(60, 150)
        d.polygon([(cx - hw, ground), (cx - hw // 3, ground - hh), (cx + hw // 4, ground - hh + 22), (cx + hw, ground)], fill=(60, 34, 40, 255))
    d.rectangle([0, ground, w, h], fill=(26, 18, 16, 255))                     # the tar
    for x in range(0, w, 2):                                                    # its gloss: broken highlights on the surface
        if rng.random() < 0.55:
            d.rectangle([x, ground, x + 1, ground + 1], fill=(79, 85, 98, 255) if rng.random() < 0.7 else (127, 135, 148, 255))
    for _ in range(60):
        x, y = rng.randrange(0, w, 2), rng.randrange(ground + 6, h, 4)
        d.rectangle([x, y, x + rng.choice((4, 8, 14)), y + 1], fill=(47, 27, 20, 255))
    return world, ground
