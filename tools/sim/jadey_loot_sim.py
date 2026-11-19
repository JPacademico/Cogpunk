"""D5 proofs for Jadey's loot and the crafting manuals (2026-11-17). Run from the repo root:

    python -P tools/sim/jadey_loot_sim.py [--out docs/media] [--only glaives,glaive-frames,cannon,pendant,manuals,items,
                                                                      jadey,statue,drift,cakti,cakti-sprites]

Offline replays with the real sprites and the C# constants (read from the source files), tick by tick at 60 ticks a second,
shown at 3 ticks a GIF frame (50 ms, exact). What they leave out: the game's lighting, tile collision (the floor and the
wall are drawn where the replay says they are), the vanilla whip's own lash curve (its art is shown in the item sheet), dust
(drawn as palette sparks), netcode.

    glaives        the Jade Cursed Glaives: four slashes crossing in X's (kinds 0, 1, 0, 1 from JadeGlaiveRigData's frames,
                   far frames behind the wielder, near ones in front, the trail added), each hit a jade curse stack on a
                   Cogscorpion (three: it turns to jade for 150 ticks), then the throw: 16 px/tick out to 18 tiles, back at
                   18 px/tick turning 0.2 a tick, one hit each way (x1.5 on jade), caught within 24 px.
    glaive-frames  every slash frame of both kinds over the wielder, with its trail (a PNG).
    cannon         the Firework Cannon: three rockets at 14 px/tick: one strikes a Rust Collector in a pack (30% strike, the
                   burst's 100% on all within 44 px, a stun), one bursts on a wall, one at 22 tiles.
    pendant        the Jade-shaper Pendant: a lethal blow from a Jade Golem turns the wearer into a jade statue for 150 ticks;
                   its touches only push (knockback 4.5 x direction, x 7/9 up, every 6 ticks at most); then the statue cracks
                   and the 3-minute recharge shows.
    manuals        the four manuals floating where they fell: a whole art pixel up and down over 120 ticks, their auras
                   pulsing over 90 ticks, sparks rising.
    items          a sheet of every new item and buff icon over dark and light backgrounds (a PNG).
    jadey          every sequence of Jadey's (her rounder panda body, 2026-11-17 second request) and the statue's frames.
    statue         her statue at 80% life: three coins (1-2 minions each), jade creeping up her, 480 ticks of stone (shown at
                   double speed in the middle of the hold), then she drinks the minions still alive (+15%).
    drift          the floaty drift (BossNPC): Jadey's spot follows a running player through a lagged focus, swaying and bobbing,
                   kept in her hall.
    cakti          the Cak-ti: spikes stick in a Rust Collector; it dies and they fly out every way, one into the next.
    cakti-sprites  the Cak-ti and its spike's 16 headings over dark and light backgrounds (a PNG).
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import stage as S  # noqa: E402
import make_teaser as M  # noqa: E402

J = "Content/Bosses/Jadey/"
W, H = 480, 240                     # the view (game px); shown at 2x


def save_gif(frames, path, ms=50):
    out = [f.convert("RGB").resize((f.width * 2, f.height * 2), Image.NEAREST) for f in frames]
    pal = [im.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.Dither.NONE) for im in out]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=False, disposal=1)
    print("wrote", path, len(frames), "frames", os.path.getsize(path) // 1024, "KB")


def backdrop(w, h, floor):
    """A plain dusk backdrop in stepped bands over a floor of Vault Gearwork (its own tile art), for the weapon replays."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    bands = ((21, 22, 28), (28, 28, 38), (36, 34, 48), (46, 42, 58))
    for k, col in enumerate(bands):
        d.rectangle([0, floor * k // len(bands), w, floor * (k + 1) // len(bands)], fill=col + (255,))
    tile = S.load("Content/Coghaven/Tiles/VaultGearworkTile.png").crop((18, 0, 34, 16))
    for y in range(floor, h, 16):
        for x in range(0, w, 16):
            img.alpha_composite(tile, (x, y))
    return img


def label(img, s, x, y, size=9):
    S.blit(img, S.text(s, size, "plate", S.STEAM[3], S.STEAM[1], S.IRON[0]), x, y)


# ================================================================================================
# The glaives
# ================================================================================================
class Glaives:
    def __init__(self):
        self.k = S.consts(J + "Weapons/JadeGlaiveRigData.cs")
        self.a = S.arrays(J + "Weapons/JadeGlaiveRigData.cs")
        self.c = S.consts(J + "Weapons/JadeCursedGlaives.cs", J + "Weapons/JadeGlaiveThrown.cs", J + "Weapons/JadeGlaiveSlash.cs")
        self.sheet = S.load(J + "Weapons/JadeGlaiveSlash.png")
        self.trail = S.load(J + "Weapons/JadeGlaiveSlash_Trail.png")
        self.spin = S.load(J + "Weapons/JadeGlaiveThrown.png")

    def cell(self, img, k):
        cw, ch, gap, n = self.k["CellWidth"], self.k["CellHeight"], self.k["Gap"], self.k["FramesPerSlash"]
        x, y = (k // n) * (cw + gap), (k % n) * (ch + gap)
        return img.crop((x, y, x + cw, y + ch))

    def spin_frame(self, f):
        c, rows = self.k["SpinCell"], self.k.get("SpinRows", self.k["SpinFrames"])
        x, y = f // rows * (c + self.k["Gap"]), f % rows * (c + self.k["Gap"])
        return self.spin.crop((x, y, x + c, y + c))

    def sample(self, kind, p):
        n = self.k["SamplesPerSlash"]
        s = min(max(p, 0.0), 1.0) * (n - 1)
        i = min(int(s), n - 2)
        f = s - i
        a, b = kind * n + i, kind * n + i + 1
        lerp = lambda u, v: u + (v - u) * f   # noqa: E731
        return ((lerp(self.a["HubX"][a], self.a["HubX"][b]), lerp(self.a["HubY"][a], self.a["HubY"][b])),
                (lerp(self.a["TipX"][a], self.a["TipX"][b]), lerp(self.a["TipY"][a], self.a["TipY"][b])))

    def frame_of(self, kind, p):
        n = self.k["FramesPerSlash"]
        return kind * n + min(n - 1, int(p * n))


def capsule_hits(a, b, r, rect):
    x0, y0, x1, y1 = rect
    for k in range(9):
        t = k / 8.0
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        dx = max(x0 - px, 0, px - x1)
        dy = max(y0 - py, 0, py - y1)
        if dx * dx + dy * dy <= r * r:
            return True
    return False


def glaives_gif(path):
    g = Glaives()
    floor = 200
    bg = backdrop(W, H, floor)
    scorp, ks = M.sheet_of("Content/Coghaven/NPCs/Cogscorpion", "Content/Coghaven/NPCs/CogscorpionRigData.cs")
    use = g.c["UseTime"]
    slashes = 6
    throw_at = slashes * use + 10
    pcx, pcy = 110, floor - 21                    # the wielder's centre (a 42 px tall player stands on the floor)
    ex = pcx + 92                                   # the scorpion's foot centre: past the old reach, inside the new one
    stacks, stone_until = 0, -1
    hits = []
    parts = S.Particles(3)
    frames = []
    glaive = None                                  # [x, y, vx, vy, phase, hits this phase, spin]
    hit_once = set()
    total = throw_at + 70
    for tick in range(total):
        img = bg.copy()
        v = S.View(W / 2, H / 2, zoom=1)
        v.img = img
        v.x0, v.y0 = 0, 0
        slash = tick // use if tick < slashes * use else -1
        kind = slash % 2 if slash >= 0 else 0
        p = (tick % use) / float(use) if slash >= 0 else 0.0
        stone = tick < stone_until
        efr = ks["Walk"] if stone else ks["Walk"] + (tick // 6) % ks["WalkFrames"]
        erect = (ex - 26, floor - 26, ex + 26, floor)
        sp = g.cell(g.sheet, g.frame_of(kind, p))
        tr = g.cell(g.trail, g.frame_of(kind, p))
        near = g.a["Near"][g.frame_of(kind, p)] if slash >= 0 else 0
        ox, oy = pcx - g.k["OriginX"], pcy - g.k["OriginY"]
        # the scorpion
        x, y = scorp.place(ex, floor)
        fr = scorp.frame(efr)
        v.put(S.tinted(fr, (96, 214, 150), 0.62) if stone else fr, x, y)
        if slash >= 0:
            S.blit_add(img, tr, ox, oy, 0.85)
            if not near:
                img.alpha_composite(sp, (ox, oy))
        M.put_player(v, pcx, floor, frame=3 if slash >= 0 else 0)
        if slash >= 0 and near:
            img.alpha_composite(sp, (ox, oy))
        # the slash's hits (each enemy once a slash, not in the wind-up)
        if slash >= 0 and p >= 1.0 / g.k["FramesPerSlash"] and slash not in hit_once:
            hub, tip = g.sample(kind, p)
            if capsule_hits((pcx + hub[0], pcy + hub[1]), (pcx + tip[0], pcy + tip[1]), g.c["BladeRadius"], erect):
                hit_once.add(slash)
                hits.append((tick, ex, floor - 40, int(g.c["Damage"] * (g.c["PetrifiedBonus"] if stone else 1.0)), stone))
                parts.burst(ex - 8, floor - 18, 6, [S.GHOST[5], S.GHOST[4], S.GHOST[3]], speed=(0.8, 2.5), life=(10, 20))
                if not stone:
                    stacks += 1
                    if stacks >= 3:
                        stacks, stone_until = 0, tick + 150
                        parts.burst(ex, floor - 14, 18, [S.GHOST[5], S.GHOST[4], S.GHOST[2]], speed=(1.0, 3.5), life=(16, 30))
        # the throw
        if tick == throw_at:
            glaive = [pcx, pcy, g.c["ThrowSpeed"], 0.0, 0, 0, 0, 0.0]
        if glaive is not None:
            gx, gy, gvx, gvy, phase, hp, spin, travelled = glaive
            if phase == 0:
                travelled += math.hypot(gvx, gvy)
                if travelled >= g.c["RangePx"]:
                    phase, hp = 1, 0
            else:
                hx, hy = pcx - gx, pcy - gy
                d = math.hypot(hx, hy)
                if d < g.c["CatchDistance"]:
                    glaive = None
                else:
                    wx, wy = hx / d * g.c["ReturnSpeed"], hy / d * g.c["ReturnSpeed"]
                    gvx += (wx - gvx) * g.c["ReturnTurn"]
                    gvy += (wy - gvy) * g.c["ReturnTurn"]
            if glaive is not None:
                gx, gy = gx + gvx, gy + gvy
                spin += 1
                grect = (gx - 18, gy - 18, gx + 18, gy + 18)
                if hp == 0 and not (grect[2] < erect[0] or grect[0] > erect[2] or grect[3] < erect[1] or grect[1] > erect[3]):
                    hp = 1
                    dmg = int(g.c["Damage"] * (g.c["PetrifiedBonus"] if tick < stone_until else 1.0))
                    hits.append((tick, ex, floor - 46, dmg, tick < stone_until))
                    parts.burst(ex, floor - 14, 14, [S.GHOST[5], S.GHOST[4], S.GHOST[2]], speed=(1.0, 4.0), life=(14, 28))
                glaive = [gx, gy, gvx, gvy, phase, hp, spin, travelled]
                f = (spin // g.c["SpinTicks"]) % g.k["SpinFrames"]
                if gvx < 0:
                    f = (g.k["SpinFrames"] - f) % g.k["SpinFrames"]
                sf = g.spin_frame(f)
                img.alpha_composite(sf, (int(gx - sf.width / 2), int(gy - sf.height / 2)))
        parts.step()
        parts.draw(v)
        for (at, x, y, val, crit) in hits:
            M.number(v, x, y, val, tick - at, crit)
        if stacks and not stone:
            label(img, "CURSE x%d" % stacks, ex - 24, floor - 70)
        if stone:
            label(img, "PETRIFIED", ex - 26, floor - 70)
        label(img, "JADE CURSED GLAIVES: one wide slash a swing (reach +3 tiles); right click: throw; x1.5 on jade", 6, 6)
        if tick % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


def glaive_frames_png(path):
    g = Glaives()
    cw, ch = g.k["CellWidth"], g.k["CellHeight"]
    n = g.k["FramesPerSlash"]
    out = Image.new("RGBA", ((cw + 8) * n + 8, (ch + 8) * 2 + 8), (30, 30, 36, 255))
    for kind in range(2):
        for f in range(n):
            k = kind * n + f
            cell = Image.new("RGBA", (cw, ch), (30, 30, 36, 255))
            S.blit_add(cell, g.cell(g.trail, k), 0, 0, 0.85)
            if not g.a["Near"][k]:
                cell.alpha_composite(g.cell(g.sheet, k))
            pl = M.player(3)
            S.blit(cell, pl, g.k["OriginX"] - pl.width // 2, g.k["OriginY"] - pl.height // 2 + 1)
            if g.a["Near"][k]:
                cell.alpha_composite(g.cell(g.sheet, k))
            out.paste(cell, (8 + f * (cw + 8), 8 + kind * (ch + 8)))
    out.resize((out.width * 3, out.height * 3), Image.NEAREST).save(path)
    print("wrote", path)


# ================================================================================================
# The Firework Cannon
# ================================================================================================
def cannon_gif(path):
    k = S.consts(J + "Weapons/FireworkCannon.cs", J + "Weapons/FireworkRocket.cs")
    floor = 200
    bg = backdrop(W, H, floor)
    d = ImageDraw.Draw(bg)
    wall_x = 330
    tile = S.load("Content/Coghaven/Tiles/VaultGearworkTile.png").crop((18, 0, 34, 16))
    for y in range(40, 112, 16):
        bg.alpha_composite(tile, (wall_x, y))                                      # a wall in the upper shot's way
    rocket = S.load(J + "Weapons/FireworkRocket.png")
    burst = S.load(J + "Weapons/FireworkRocket_Burst.png")
    rc, bc, gap = k["Cell"], k["BurstCell"], k["Gap"]
    gun = S.load(J + "Weapons/FireworkCannon.png")
    rust = S.vanilla_frames("Content/Junkyard/NPCs/RustCollector.png", 11)
    stars = S.strip("Content/Mechanist/Buffs/StunnedStars.png", 2) if S.exists("Content/Mechanist/Buffs/StunnedStars.png") else None
    pcx, pcy = 50, floor - 21
    enemies = [[230.0, 0, -1], [262.0, 0, -1], [292.0, 0, -1]]                     # x, hit flash tick, stunned until
    shots = [(0, 0.0), (36, -0.42), (72, -0.12)]                                     # fire tick, aim (radians)
    rockets = []
    hits, parts = [], S.Particles(5)
    frames = []
    for tick in range(150):
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        for e in enemies:
            fr = rust[(tick // 5) % 8] if tick >= e[2] else rust[0]
            v.put(M.hit_flash(fr, tick - e[1], 6) if e[1] else fr, e[0] - 20, floor - 38)
            if tick < e[2]:
                for s in range(3):
                    a = tick * 0.2 + s * 2.09
                    sx, sy = int(e[0] + math.cos(a) * 12), int(floor - 44 + math.sin(a) * 4)
                    d2 = ImageDraw.Draw(img)
                    d2.rectangle([sx // 2 * 2, sy // 2 * 2, sx // 2 * 2 + 3, sy // 2 * 2 + 3], fill=S.BRASS[5] + (255,))
        for (at, aim) in shots:
            if tick == at:
                rockets.append([pcx + 36 * math.cos(aim), pcy + 36 * math.sin(aim), k["ShootSpeed"] * math.cos(aim),
                                k["ShootSpeed"] * math.sin(aim), 0, 0.0, -1])
        M.put_player(v, pcx, floor, frame=3)
        img.alpha_composite(gun, (pcx - 6, pcy - 14))
        for r in rockets:
            x, y, vx, vy, state, travelled, age = r
            if state == 0:
                x, y = x + vx, y + vy
                travelled += math.hypot(vx, vy)
                target = None
                for e in enemies:
                    if abs(x - e[0]) < 18 and floor - 34 < y < floor:
                        target = e
                if target is not None:
                    target[1] = tick
                    hits.append((tick, target[0], floor - 50, int(round(k["Damage"] * k["ContactShare"])), False))
                    state, age = 1, 0
                elif wall_x <= x <= wall_x + 16 and 40 <= y <= 112:
                    state, age = 1, 0
                elif travelled >= k["RangePx"]:
                    state, age = 1, 0
                if state == 1:
                    for n, e in enumerate(enemies):                              # the burst: every enemy within its radius
                        dx = max(e[0] - 18 - x, 0, x - (e[0] + 18))
                        dy = max(floor - 34 - y, 0, y - floor)
                        if dx * dx + dy * dy <= k["BurstRadius"] ** 2:
                            e[1] = tick
                            hits.append((tick + 1, e[0] + 6, floor - 60 - n * 4, k["Damage"], False))
                            if n == 1:
                                e[2] = tick + k["StunTicks"]                      # the one stun in four
                if state == 0:
                    hd = int(round(math.atan2(vy, vx) / (2 * math.pi) * 16)) % 16
                    img.alpha_composite(rocket.crop((0, hd * (rc + gap), rc, hd * (rc + gap) + rc)), (int(x - rc / 2), int(y - rc / 2)))
                    if tick % 2 == 0:
                        parts.burst(x - vx * 0.6, y - vy * 0.6, 1, [S.BRASS[5], S.GHOST[4], S.BRASS[3]], speed=(0.2, 0.8), life=(6, 12))
            if state == 1:
                age += 1
                f = min(k["BurstFrames"] - 1, age // k["BurstFrameTicks"])
                if age < k["BurstTicks"]:
                    S.blit_add(img, burst.crop((0, f * (bc + gap), bc, f * (bc + gap) + bc)), int(x - bc / 2), int(y - bc / 2),
                               1.0 if f < k["BurstFrames"] - 2 else 0.6)
            r[:] = [x, y, vx, vy, state, travelled, age]
        parts.step()
        parts.draw(v)
        for (at, x, y, val, crit) in hits:
            M.number(v, x, y, val, tick - at, crit)
        label(img, "FIREWORK CANNON  (21 mana: strike 30%, burst 100% within 44 px, 1 in 4 stuns)", 6, 6)
        if tick % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


# ================================================================================================
# The pendant
# ================================================================================================
def pendant_gif(path):
    k = S.consts(J + "Items/JadeShaperPendant.cs", J + "JadeShaperPlayer.cs")
    floor = 200
    bg = backdrop(W, H, floor)
    golem, kg = M.sheet_of("Content/Coghaven/NPCs/JadeGolem", "Content/Coghaven/NPCs/JadeGolemRigData.cs")
    statue_icon = S.load(J + "Buffs/JadeStatue.png")
    rest_icon = S.load(J + "Buffs/JadeShaperRest.png")
    px, pvx, pvy, py = 330.0, 0.0, 0.0, 0.0                   # feet x, velocity, height over the floor
    gx = 470.0
    statue_from, statue_to = -1, -1
    gate = 0
    parts = S.Particles(9)
    frames = []
    life = 12
    for tick in range(270):
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        statue = statue_from <= tick < statue_to
        gx = max(gx - 1.4, px + 34) if tick < 240 else gx + 1.2           # the golem walks in and leans on the statue
        touching = gx - px < 40
        gate = max(0, gate - 1)
        if touching and tick < 240:
            if statue_from < 0:
                statue_from, statue_to = tick, tick + k["StatueTicks"]           # the blow that would kill: the pendant saves
                life = 1
                parts.burst(px, floor - 20, 22, [S.GHOST[5], S.GHOST[4], S.GHOST[2]], speed=(1.0, 3.5), life=(16, 30))
                statue = True
            if statue and gate == 0:
                pvx, pvy, gate = -4.5, -4.5 * 7 / 9, k["PushGateTicks"]       # its knockback still lands
        px += pvx
        py = min(0.0, py + pvy)
        pvy = pvy + 0.4 if py < 0 else 0.0
        if py >= 0:
            pvx = 0.0 if abs(pvx) <= 0.2 else pvx - math.copysign(0.2, pvx)   # a statue doesn't walk: it slides to a stop
        if tick == statue_to:
            parts.burst(px, floor - 20, 26, [S.GHOST[5], S.GHOST[4], S.GHOST[3], S.GHOST[1]], speed=(1.0, 4.0), life=(16, 34))
        gf = kg["Walk"] + (tick // kg["WalkStep"]) % kg["WalkFrames"]
        v.sheet(golem, gf, gx, floor, flip=False)
        pl = M.player(0)
        if statue:
            pl = S.tinted(pl, (96, 214, 150), 0.55)
        v.put(pl, px - pl.width // 2, floor + py - pl.height + 2)
        parts.step()
        parts.draw(v)
        label(img, "JADE-SHAPER PENDANT", 6, 6)
        label(img, "LIFE %d" % life, 6, 20)
        if statue:
            img.alpha_composite(statue_icon, (6, 34))
            label(img, "JADE STATUE %.1fs: no damage, still knocked back" % ((statue_to - tick) / 60.0), 42, 44)
        elif statue_from >= 0 and tick >= statue_to:
            img.alpha_composite(rest_icon, (6, 34))
            label(img, "JADE-SHAPER'S REST: 3:00", 42, 44)
        if tick % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


# ================================================================================================
# The manuals
# ================================================================================================
def manuals_gif(path):
    k = S.consts("Content/Manuals/CraftingManual.cs")
    names = ("ScrapManual", "StickyPages", "SheriffsLawBook", "JadeShaperManual")
    books = [S.load("Content/Manuals/Items/%s.png" % n) for n in names]
    auras = [S.load("Content/Manuals/Items/%s_Aura.png" % n) for n in names]
    sparks = {"ScrapManual": S.EMBER, "StickyPages": S.EMBER, "SheriffsLawBook": S.BRASS, "JadeShaperManual": S.GHOST}
    w, h = 360, 120
    bg = Image.new("RGBA", (w, h), (20, 18, 26, 255))
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 96, w, h], fill=(46, 50, 59, 255))
    d.line([0, 96, w, 96], fill=(79, 85, 98, 255), width=2)
    parts = S.Particles(4)
    frames = []
    period = 360                                       # the bob (120) and the pulse (90) both close in 360 ticks
    rng = random.Random(3)
    for tick in range(period):
        img = bg.copy()
        v = S.View(w / 2, h / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        for n, (bk, au) in enumerate(zip(books, auras)):
            t = tick + n * 37
            pulse = 0.7 + 0.3 * math.sin(t * 2 * math.pi / k["PulseTicks"])
            bob = int(round(math.sin(t * 2 * math.pi / k["BobTicks"]) * (k["BobPixels"] / 2.0))) * 2
            cx, cy = 50 + n * 86, 62 + bob
            S.blit_add(img, au, cx - au.width // 2, cy - au.height // 2, 0.8 * pulse)
            img.alpha_composite(bk, (cx - bk.width // 2, cy - bk.height // 2))
            if rng.random() < 1.0 / k["SparkOneIn"]:
                ramp = sparks[names[n]]
                parts.burst(cx + rng.uniform(-12, 12), cy + rng.uniform(-8, 10), 1, [ramp[-1], ramp[-2], ramp[-3]], speed=(0.4, 1.1),
                            life=(20, 40), gravity=-0.0, spread=(-math.pi / 2 - 0.2, -math.pi / 2 + 0.2))
        parts.step()
        parts.draw(v)
        label(img, "CRAFTING MANUALS: a boss's first defeat, one for every player", 6, 4)
        if tick % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


# ================================================================================================
# The items sheet
# ================================================================================================
def items_png(path):
    paths = [J + "Weapons/JadeCursedGlaives.png", J + "Weapons/JadeShaperWhip.png", J + "Weapons/FireworkCannon.png",
             J + "Items/JadeShaperPendant.png", J + "Items/JadeIncense.png", "Content/Coghaven/Items/JadeEyedKoi.png",
             "Content/Manuals/Items/JadeShaperManual.png", "Content/Manuals/Items/ScrapManual.png", "Content/Manuals/Items/SheriffsLawBook.png",
             "Content/Manuals/Items/StickyPages.png", J + "Buffs/JadeStatue.png", J + "Buffs/JadeShaperRest.png",
             J + "Weapons/JadeShaperWhipDebuff.png", J + "Weapons/JadeShaperWhipProjectile.png"]
    ims = [S.load(p) for p in paths]
    sc = 3
    w = sum(im.width * sc + 12 for im in ims) + 12
    h = max(im.height for im in ims) * sc + 24
    out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
    for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
        band = Image.new("RGBA", (w, h), bg + (255,))
        x = 12
        for im in ims:
            band.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (x, 12))
            x += im.width * sc + 12
        out.paste(band, (0, row * h))
    out.save(path)
    print("wrote", path)



# ================================================================================================
# Jadey (2026-11-17 second request): her rounder body, her statue, the floaty drift
# ================================================================================================
def jadey_sheet():
    return M.sheet_of("Content/Bosses/Jadey/Jadey", "Content/Bosses/Jadey/JadeyRigData.cs")


def jadey_frames_gif(path):
    """Every sequence of hers in order (the new body), and the statue's frames as the fight plays them."""
    sheet, k = jadey_sheet()
    seqs = [("IDLE", k["Idle"], 6, 2), ("ROPE DART", k["Whip"], 6, 1), ("PETRIFYING SEAL", k["Zone"], 6, 1), ("CHANNEL", k["Channel"], 4, 2),
            ("LASERS", k["Laser"], 4, 2), ("INTRO", k["Intro"], 4, 1), ("STATUE", k["Death"], 7, 1),
            ("DEATH", k["Death"], 8, 1)]
    frames = []
    for name, first, n, loops in seqs:
        for _ in range(loops):
            for i in range(n):
                im = Image.new("RGBA", (k["CellWidth"] + 60, k["CellHeight"] + 36), (30, 30, 36, 255))
                im.alpha_composite(sheet.frame(first + i), (30, 8))
                label(im, "%s %d/%d" % (name, i + 1, n), 4, im.height - 16)
                frames.append(im)
    save_gif(frames, path, ms=110)


def jadey_statue_gif(path):
    """Her statue at 80% life: three coins (a flick each, 12 ticks apart), each 1-2 minions; jade creeps up her (20 ticks), she
    holds as a statue (no damage) for 480 ticks; the minions still alive, she drains them (her channel: 72 ticks, +15%)."""
    k = S.consts("Content/Bosses/Jadey/Jadey.cs", "Content/Bosses/Jadey/JadeyRigData.cs", "Content/Bosses/Jadey/Projectiles/JadeCoin.cs")
    a = S.arrays("Content/Bosses/Jadey/JadeyRigData.cs")
    sheet, kr = jadey_sheet()
    floor = 200
    w = W
    bg = backdrop(w, H, floor)
    golem, kg = M.sheet_of("Content/Coghaven/NPCs/JadeGolem", "Content/Coghaven/NPCs/JadeGolemRigData.cs")
    bat_sheet = S.load("Content/Bosses/Jadey/NPCs/JadeBat.png")
    bat_h = (bat_sheet.height) // 4
    bat_frames = [bat_sheet.crop((0, i * bat_h, bat_sheet.width, i * bat_h + bat_h - 2)) for i in range(4)]
    beetle = S.Sheet("Content/Bosses/Jadey/NPCs/JadeBeetle", 120, 68, 60, 66)
    coin_sheet = S.strip("Content/Bosses/Jadey/Projectiles/JadeCoin.png", k["CoinFrames"])
    jx, jy = 240, floor - 40                                   # her rig origin (she floats)
    rng = __import__("random").Random(5)
    coins, minions = [], []
    parts = S.Particles(12)
    hits = []
    start = 0
    petrify = k["PetrifyAt"]
    end = petrify + k["StatueTicks"]
    total = end + k["ChannelTicks"] + 24
    frames = []
    life, life_max = 5600, 7000
    for t in range(total):
        img = bg.copy()
        v = S.View(w / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        # her frame (the statue's frame rule, Jadey.Attacks BodyFrame)
        flick = -1
        for c in range(k["StatueCoins"]):
            at = c * k["StatueCoinGap"]
            if at <= t < at + k["FlickTicks"] + 1:
                flick = t - at
        if t >= end:
            ct = t - end
            body = kr["Channel"] + (0 if ct < 10 else 1 if ct < 20 else 2 + (ct // 6) % 2 if ct < k["ChannelTicks"] else 1)
        elif t < petrify:
            body = kr["Idle"] + (t // 9) % kr["IdleFrames"]
        elif t < petrify + k["PetrifyTurnTicks"]:
            body = kr["Death"] + min(4, (t - petrify) * 5 // k["PetrifyTurnTicks"])
        else:
            body = kr["Death"] + (6 if t >= end - k["StatueCrackWarn"] else 5)
        far = body
        if flick >= 0 and t < petrify:                              # her idle frames all let the far arm flick (FlickOk)
            far = kr["Flick"] + min(kr["FlickFrames"] - 1, flick * kr["FlickFrames"] // (k["FlickTicks"] + 1))
        x, y = sheet.place(jx, jy)
        img.alpha_composite(sheet.frame(body, far_i=far), (int(x), int(y)))
        # the coins (thrown at a flick's top from her far paw: left, near the target, right)
        for c in range(k["StatueCoins"]):
            if t == c * k["StatueCoinGap"] + k["FlickTicks"] // 2:
                fx, fy = jx + a["FarX"][kr["Flick"] + 3] * 1.0, jy + a["FarY"][kr["Flick"] + 3] * 1.0
                d = -1.0 if c == 0 else 1.0 if c == k["StatueCoins"] - 1 else -0.35
                coins.append([fx, fy, d * rng.uniform(2.6, 4.2), -rng.uniform(6.0, 7.2), -1, rng.randint(1, 2), rng.randrange(3), rng.randrange(3)])
        for cn in coins:
            cx, cy, vx, vy, landed, count, k1, k2 = cn
            if landed < 0:
                vy += 0.3
                cx, cy = cx + vx, cy + vy
                if cy >= floor - 4:
                    cy, landed = floor - 4, t
            if landed >= 0 and t == landed + k["HatchTicks"]:
                for i in range(count):
                    kind = k1 if i == 0 else k2
                    dx = 0 if count == 1 else (-18 if i == 0 else 18)
                    minions.append([cx + dx, kind, t, rng.uniform(0, 6.28)])
                    parts.burst(cx + dx, floor - 10, 14, [S.GHOST[5], S.GHOST[4], S.GHOST[3]], speed=(0.8, 3.0), life=(12, 26))
            cn[:] = [cx, cy, vx, vy, landed, count, k1, k2]
            if landed < 0 or t < landed + k["HatchTicks"]:
                f = 0 if landed >= 0 else (t // 4) % k["CoinFrames"]
                img.alpha_composite(coin_sheet[f], (int(cx - coin_sheet[f].width / 2), int(cy - coin_sheet[f].height / 2)))
        # the minions (until she drinks them)
        drink = k["ChannelTicks"]
        for m in minions:
            mx, kind, born, ph = m
            if t >= end + drink:
                continue
            age = t - born
            if kind == 0:
                gx = mx + math.sin(age * 0.02 + ph) * 18
                golem_frame = kg["Walk"] + (age // kg["WalkStep"]) % kg["WalkFrames"]
                v.sheet(golem, golem_frame, gx, floor)
            elif kind == 1:
                bf = bat_frames[(age // 4) % 4]
                img.alpha_composite(bf, (int(mx + math.sin(age * 0.05 + ph) * 26 - bf.width / 2), int(floor - 70 + math.sin(age * 0.11) * 10)))
            else:
                bx = mx + math.sin(age * 0.025 + ph) * 24
                v.sheet(beetle, (age // 4) % 8, bx, floor)
            if end <= t < end + drink and t % 2 == 0:
                parts.burst(mx + rng.uniform(-10, 10), floor - 30, 1, [S.GHOST[5], S.GHOST[4]], speed=(0.5, 1.5), life=(10, 22))
        if t == end + drink:
            heal = int(life_max * k["HealFraction"])
            life = min(life_max, life + heal)
            hits.append((t, jx, jy - 110, heal, False))
            parts.burst(jx, jy - 40, 30, [S.GHOST[5], S.GHOST[4], S.GHOST[2]], speed=(1.0, 3.5), life=(16, 34))
        if t == end:
            parts.burst(jx, jy - 40, 30, [S.GHOST[5], S.GHOST[4], S.GHOST[3], S.GHOST[1]], speed=(1.0, 4.0), life=(16, 34))
        parts.step()
        parts.draw(v)
        for (at, x2, y2, val, crit) in hits:
            if 0 <= t - at < 40:
                im2 = S.text("+%d" % val, 11, "plain", (196, 250, 214), (58, 166, 118), (10, 34, 32))
                img.alpha_composite(S.faded(im2, min(1.0, (40 - (t - at)) / 12.0)), (int(x2 - im2.width / 2), int(y2 - (t - at) * 0.8)))
        label(img, "JADEY'S STATUE (each 20% of her life): 3 coins, 1-2 minions each; jade 8 s or till they die", 6, 4)
        fast = petrify + k["PetrifyTurnTicks"] + 12 <= t < end - k["StatueCrackWarn"] - 12
        state = "throwing coins" if t < petrify else "drinking her minions (+15%)" if t >= end else \
            "a jade statue: no damage" + (" (shown x2)" if fast else "")
        label(img, "LIFE %d / %d  -  %s" % (life, life_max, state), 6, 18)
        if t % (6 if fast else 3) == 0:                         # the long hold at double speed: the GIF stays under 10 s
            frames.append(img)
    save_gif(frames, path)


def drift_gif(path):
    """BossNPC's floaty drift on Jadey (her constants; the view is her hall, kept with her ClampToArena margins): her hover spot
    follows a running player through a lagged focus and sways side to side and bobs; with the player near a wall she crosses
    to the roomier side (RoomySide); the trail is her centre over the last 2 s, the brass box her spot."""
    kb = S.consts("Core/Templates/BossNPC.cs")
    kj = S.consts("Content/Bosses/Jadey/Jadey.cs")
    sheet, kr = jadey_sheet()
    w, h = 640, 260
    floor = 230
    bg = backdrop(w, h, floor)
    hw, hh = kr["BodyRight"] - kr["BodyLeft"], -kr["BodyTop"] - 2
    ax0, ax1 = kj["ArenaMarginX"] + hw / 2, w - kj["ArenaMarginX"] - hw / 2
    ay0, ay1 = kj["ArenaMarginTop"] + hh / 2, floor - kj["ArenaMarginBottom"] - hh / 2
    px = 250.0
    nx, ny = px + kj["HoverX"], floor - 21 - kj["HoverY"]
    vx = vy = 0.0
    fx, fy = px, floor - 21.0
    trail = []
    frames = []
    for t in range(480):
        img = bg.copy()
        v = S.View(w / 2, h / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        run = 3.0 if 90 <= t < 190 else -3.0 if 300 <= t < 420 else 0.0
        px = min(w - 40.0, max(40.0, px + run))
        tcx, tcy = px, floor - 21.0
        fx += (tcx - fx) * kb["FocusFollow"]
        fy += (tcy - fy) * kb["FocusFollow"]
        sway = math.sin(t * 2 * math.pi / kb["DriftPeriodX"])
        bob = math.sin(t * 2 * math.pi / kb["DriftPeriodY"] + math.pi / 2)
        side = -1.0 if nx < fx else 1.0
        room, other = (fx - ax0, ax1 - fx) if side < 0 else (ax1 - fx, fx - ax0)             # Jadey.RoomySide
        if room < kj["HoverX"] * kj["WallRoomShare"] and other > room + kj["SideSwitchMargin"]:
            side = -side
        sx, sy = fx + side * kj["HoverX"] + sway * kj["SwayX"], fy - kj["HoverY"] + bob * kj["BobY"]
        sx, sy = min(ax1, max(ax0, sx)), min(ay1, max(ay0, sy))
        dx, dy = sx - nx, sy - ny
        d = math.hypot(dx, dy)
        want = min(kj["HoverSpeed"], d * kj["HoverApproach"])
        wx, wy = (dx / d * want, dy / d * want) if d > 1 else (0.0, 0.0)
        vx += (wx - vx) * kj["HoverAccel"]
        vy += (wy - vy) * kj["HoverAccel"]
        nx, ny = nx + vx, ny + vy
        trail.append((nx, ny))
        trail = trail[-120:]
        d2 = ImageDraw.Draw(img)
        for i, (qx, qy) in enumerate(trail[::4]):
            col = S.GHOST[2] if i < len(trail[::4]) - 8 else S.GHOST[4]
            d2.rectangle([int(qx) // 2 * 2, int(qy) // 2 * 2, int(qx) // 2 * 2 + 1, int(qy) // 2 * 2 + 1], fill=col + (255,))
        x, y = sheet.place(nx, ny + hh / 2, flip=nx < px)
        img.alpha_composite(sheet.frame(kr["Idle"] + (t // 9) % kr["IdleFrames"], flip=nx < px), (int(x), int(y)))
        d2.rectangle([int(sx) - 4, int(sy) - 4, int(sx) + 4, int(sy) + 4], outline=S.BRASS[4] + (255,))
        M.put_player(v, int(px), floor, frame=0 if run == 0 else 6 + (t // 3) % 14, flip=run < 0)
        label(img, "FLOATY BOSSES: a lagged follow, a slow sway and a bob (Jadey; the box: her spot)", 6, 4)
        if t % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


# ================================================================================================
# The Cak-ti
# ================================================================================================
def fling_seed(starts, other_x, floor, k, tries=200):
    """The first seed whose random spray (one uniform angle a spike, straight at FlingSpeed for FlingTicks, stopped by the
    floor) sends a spike into the Collector behind: the directions stay random, the replay just shows a spray that hits."""
    for seed in range(tries):
        r = random.Random(seed)
        angles = [r.uniform(0, 2 * math.pi) for _ in starts]
        for (x, y), a in zip(starts, angles):
            for step in range(1, k["FlingTicks"] + 1):
                qx, qy = x + math.cos(a) * k["FlingSpeed"] * step, y + math.sin(a) * k["FlingSpeed"] * step
                if qy > floor:
                    break
                if abs(qx - other_x) < 18 and floor - 34 < qy < floor:
                    return angles
    return [random.Random(0).uniform(0, 2 * math.pi) for _ in starts]


def cakti_gif(path):
    """Spikes from the Cak-ti (11-tick use) stick in a Rust Collector (Embed: 70% of the way in from where they hit); it dies;
    its spikes fly out every way, one hitting the Collector behind it (fling_seed)."""
    k = S.consts("Content/Desert/Weapons/Cakti.cs", "Content/Desert/Weapons/CaktiSpike.cs")
    gun = S.load("Content/Desert/Weapons/Cakti.png")
    sheet = S.load("Content/Desert/Weapons/CaktiSpike.png")
    cell, gap = k["Cell"], k["Gap"]
    spikes_img = [sheet.crop((0, i * (cell + gap), cell, i * (cell + gap) + cell)) for i in range(k["Headings"])]
    rust = S.vanilla_frames("Content/Junkyard/NPCs/RustCollector.png", 11)
    floor = 200
    bg = backdrop(W, H, floor)
    pcx, pcy = 60, floor - 21
    enemies = [[300.0, 1, 0, -99], [372.0, 1, 0, -99]]            # x, alive, life lost, hit flash
    life = 100
    rng = __import__("random").Random(8)
    shots, stuck, flung = [], [], []
    hits, parts = [], S.Particles(14)
    frames = []
    fire_until = 11 * 10
    died_at = -1
    for t in range(220):
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        for e in enemies:
            if e[1]:
                fr = rust[(t // 5) % 8]
                v.put(M.hit_flash(fr, t - e[3], 5), e[0] - 20, floor - 38)
        M.put_player(v, pcx, floor, frame=3)
        img.alpha_composite(gun, (pcx - 2, pcy - 14))
        if t < fire_until and t % k["UseTime"] == 0:
            aim = rng.uniform(-0.05, 0.05) * 0 + (-0.02 if (t // k["UseTime"]) % 2 else 0.02)
            shots.append([pcx + 34, pcy - 2, 15.5 * math.cos(aim), 15.5 * math.sin(aim)])
        for s_ in list(shots):
            for _ in range(2):                                         # extraUpdates 1
                s_[0] += s_[2]
                s_[1] += s_[3]
                e = enemies[0]
                if e[1] and abs(s_[0] - e[0]) < 18 and floor - 34 < s_[1] < floor:
                    hd = int(round(math.atan2(s_[3], s_[2]) / (2 * math.pi) * 16)) % 16
                    stuck.append([(s_[0] - e[0]) * k["Embed"], (s_[1] - (floor - 18)) * k["Embed"], hd, t])
                    hits.append((t, e[0], floor - 50, k["Damage"] + 7, False))
                    e[2] += k["Damage"] + 7
                    e[3] = t
                    shots.remove(s_)
                    if e[2] >= life and died_at < 0:
                        e[1], died_at = 0, t
                        parts.burst(e[0], floor - 20, 20, [S.IRON[3], S.IRON[2], S.BRASS[3], S.BRASS[1]], speed=(1.0, 4.0), life=(14, 30))
                        starts = [(e[0] + ox, floor - 18 + oy) for (ox, oy, hd2, born) in stuck]
                        for (fx0, fy0), a in zip(starts, fling_seed(starts, enemies[1][0], floor, k)):   # flung out every way
                            flung.append([fx0, fy0, k["FlingSpeed"] * math.cos(a), k["FlingSpeed"] * math.sin(a), t])
                        stuck.clear()
                    break
            else:
                hd = int(round(math.atan2(s_[3], s_[2]) / (2 * math.pi) * 16)) % 16
                sp = spikes_img[hd]
                img.alpha_composite(sp, (int(s_[0] - cell / 2), int(s_[1] - cell / 2)))
                if s_[0] > W:
                    shots.remove(s_)
        e = enemies[0]
        for (ox, oy, hd, born) in stuck:
            sp = spikes_img[hd]
            img.alpha_composite(sp, (int(e[0] + ox - cell / 2), int(floor - 18 + oy - cell / 2)))
        for f_ in list(flung):
            f_[0] += f_[2]
            f_[1] += f_[3]
            other = enemies[1]
            if other[1] and abs(f_[0] - other[0]) < 18 and floor - 34 < f_[1] < floor:
                hits.append((t, other[0], floor - 50 - len(hits) % 3 * 6, k["Damage"] + 7, False))
                other[3] = t
                flung.remove(f_)
                continue
            if t - f_[4] > k["FlingTicks"] or f_[1] > floor:
                flung.remove(f_)
                continue
            hd = int(round(math.atan2(f_[3], f_[2]) / (2 * math.pi) * 16)) % 16
            img.alpha_composite(spikes_img[hd], (int(f_[0] - cell / 2), int(f_[1] - cell / 2)))
        parts.step()
        parts.draw(v)
        for (at, x2, y2, val, crit) in hits:
            M.number(v, x2, y2, val, t - at, crit)
        label(img, "CAK-TI: %d + the bullet's 7, use %d; spikes stick 5 s; a kill flings them out every way" % (k["Damage"], k["UseTime"]), 6, 4)
        if t % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


def cakti_png(path):
    """The Cak-ti (x4) and its spike's 16 pre-rendered headings (x3) over dark and light backgrounds (a PNG)."""
    k = S.consts("Content/Desert/Weapons/CaktiSpike.cs")
    gun = S.load("Content/Desert/Weapons/Cakti.png")
    sheet = S.load("Content/Desert/Weapons/CaktiSpike.png")
    cell, gap = k["Cell"], k["Gap"]
    spikes = [sheet.crop((0, i * (cell + gap), cell, i * (cell + gap) + cell)) for i in range(k["Headings"])]
    sg, ss, per_row = 4, 3, 8
    step = cell * ss + 6
    w = 12 + gun.width * sg + 24 + step * per_row + 12
    h = max(gun.height * sg, step * ((len(spikes) + per_row - 1) // per_row)) + 24
    out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
    for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
        band = Image.new("RGBA", (w, h), bg + (255,))
        band.alpha_composite(gun.resize((gun.width * sg, gun.height * sg), Image.NEAREST), (12, 12))
        x0 = 12 + gun.width * sg + 24
        for i, sp in enumerate(spikes):
            band.alpha_composite(sp.resize((cell * ss, cell * ss), Image.NEAREST), (x0 + (i % per_row) * step, 12 + (i // per_row) * step))
        out.paste(band, (0, row * h))
    out.save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = (("glaives", glaives_gif, "2026-11-17_jadey-glaives.gif"), ("glaive-frames", glaive_frames_png, "2026-11-17_jadey-glaives-frames.png"),
            ("cannon", cannon_gif, "2026-11-17_jadey-firework-cannon.gif"), ("pendant", pendant_gif, "2026-11-17_jadey-pendant.gif"),
            ("manuals", manuals_gif, "2026-11-17_manuals-floating.gif"), ("items", items_png, "2026-11-17_jadey-loot-items.png"),
            ("jadey", jadey_frames_gif, "2026-11-17_boss-jadey.gif"), ("statue", jadey_statue_gif, "2026-11-17_boss-jadey-statue.gif"),
            ("drift", drift_gif, "2026-11-17_floaty-drift.gif"), ("cakti", cakti_gif, "2026-11-17_weapon-cakti.gif"),
            ("cakti-sprites", cakti_png, "2026-11-17_weapon-cakti-sprites.png"))
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(args.out, file))


if __name__ == "__main__":
    main()
