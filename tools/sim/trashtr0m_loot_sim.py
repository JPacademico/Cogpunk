"""D5 proofs for Trash-Tr0m's loot (Content/Bosses/TrashTr0m/Weapons, Items), built from the real sprites and the
constants parsed straight out of the C# files, replaying the weapons tick by tick (60 ticks = 1 s).

    python -P tools/sim/trashtr0m_loot_sim.py --out docs/media --date 2026-10-26 [--only tetanus,launcher,...]

Writes <date>_weapon-<scene>.gif|png:
    loot      PNG: the bag, the four weapons, the held lance, the sentry's frames and every new effect, at 2x zoom over a
              dark and a light background.
    tetanus   (2026-10-27) the 8.5-tile lance aimed in any direction: quick thrusts right, up at a flier and down-left
              behind the player (each hits going out and coming back), then a 2.5 s charge aimed up-right and the charged
              lunge, which now also hits going out and coming back (27 x 2.0, then x1.1 under Tetanus).
    launcher  (2026-10-27) left click: chewed scrap flying dead straight across a whole 1920 px screen (no gravity);
              right click: the big ball on a gravity arc (one bounce), 31 ticks apart; every hit bursts (impact sheet).
    held      PNG: the smaller Scrap Launcher held at three aims, placed the way vanilla draws guns.
    scrapmancer  the junk shockwave rolling a whole screen (1920 px shown at half size), climbing a 2-tile step and
              dropping a 4-tile ledge, hitting each enemy once and throwing it along its path.
    tr0mhead  the sentry's cycle: idle, an enemy walks into reach, the jaw drops, 5 s of suction (enemies dragged in by
              their knockback resistance, chewed for 15 once a second each; 2026-10-27: a flier is dragged in harder,
              FlyerPullScale / FlyerSteerScale), the jaw shuts, 2.5 s of steam, idle.

Leaves out: lighting, tile collision beyond a height map, NPC AI (the enemies just walk), defense, crits, vanilla's
player animation (the player is a standing sprite), network latency.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armor_preview as ap  # noqa: E402

W_DIR = "Content/Bosses/TrashTr0m/Weapons/"
TPF = 3                                                # game ticks per GIF frame (20 fps)


def consts(*paths):
    """`const int/float NAME = value;` from C# files (simple expressions and references resolved)."""
    raw = {}
    for path in paths:
        src = open(path, encoding="utf-8").read()
        for m in re.finditer(r"const (?:int|float) ([^;]+);", src):
            for part in m.group(1).split(","):
                if "=" in part:
                    k, v = (x.strip() for x in part.split("=", 1))
                    raw[k] = v
    out = {}
    for _ in range(6):
        for k, v in raw.items():
            if k in out:
                continue
            expr = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
            expr = re.sub(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", r"\1", expr)   # Class.Member -> Member (never 0.14)
            try:
                out[k] = eval(expr, {}, dict(out))
            except Exception:
                pass
    return out


K = consts(W_DIR + "Tetanus.cs", W_DIR + "TetanusProjectile.cs", W_DIR + "ScrapLauncher.cs", W_DIR + "ScrapLauncherBall.cs",
           W_DIR + "ScrapLauncherChunk.cs",
           W_DIR + "Scrapmancer.cs", W_DIR + "ScrapmancerWave.cs", W_DIR + "Tr0mheadSentry.cs",
           "Content/Bosses/TrashTr0m/Projectiles/TrashTr0mChewedScrap.cs", "Content/Bosses/TrashTr0m/Projectiles/TrashTr0mScrapBall.cs",
           "Content/Bosses/TrashTr0m/Buffs/TetanusDebuff.cs")
K["BallGravity"] = 0.3                                   # TrashTr0mScrapBall.Gravity
_mo = re.search(r"MouthOffset = new\(([-\d.]+)f, ([-\d.]+)f\)", open(W_DIR + "Tr0mheadSentry.cs", encoding="utf-8").read())
K["MouthOffset_X"], K["MouthOffset_Y"] = float(_mo.group(1)), float(_mo.group(2))


def load(path):
    return Image.open(path).convert("RGBA")


def frames(path, w, h, stride, n):
    im = load(path)
    return [im.crop((0, k * stride, w, k * stride + h)) for k in range(n)]


def player_sprite(flip=False):
    heads = ap.load_frames("Content/Scrap/Armor/ScrapHelmet_Head.png", 4)
    bodies = ap.load_frames("Content/Scrap/Armor/ScrapBreastplate_Body.png", 4)
    legs = ap.load_frames("Content/Scrap/Armor/ScrapLeggings_Legs.png", 4)
    s = ap.compose(heads[0], bodies[0], legs[0], 0, [0] * 20)
    return s.transpose(Image.FLIP_LEFT_RIGHT) if flip else s


class Gif:
    def __init__(self, font, size, scale=1.0):
        self.font = ImageFont.truetype(font, 14)
        self.big = ImageFont.truetype(font, 20)
        self.size, self.scale = size, scale
        self.frames = []

    def text(self, img, xy, s, fill=(238, 241, 243), font=None):
        d = ImageDraw.Draw(img)
        f = font or self.font
        for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            d.text((xy[0] + ox, xy[1] + oy), s, fill=(21, 22, 28), font=f)
        d.text(xy, s, fill=fill, font=f)

    def push(self, img):
        if self.scale != 1.0:
            img = img.resize((int(img.width * self.scale), int(img.height * self.scale)), Image.NEAREST)
        self.frames.append(img.convert("RGB"))

    def save(self, path):
        pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in self.frames]
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=TPF * 1000 // 60, loop=0, optimize=True, disposal=1)
        print("%s: %d frames, %.1f s, %.1f MB" % (path, len(self.frames), len(self.frames) * TPF / 60, os.path.getsize(path) / 1e6))


def backdrop(w, h, ground, heights=None, sky=((150, 180, 210), (110, 130, 170)), dirt=(120, 92, 60)):
    """A sky gradient over ground; heights maps x -> ground y (a height map), else flat."""
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([0, y, w, y], fill=tuple(int(a + (b - a) * t) for a, b in zip(*sky)) + (255,))
    for x in range(0, w, 2):
        gy = heights(x) if heights else ground
        d.rectangle([x, gy, x + 1, h], fill=dirt + (255,))
        d.rectangle([x, gy, x + 1, gy + 3], fill=(147, 110, 70, 255))
    return img


def glow_over(img, layer, alpha, xy):
    """Composites a glow layer (opaque pixels) faded by alpha, like Color.White * alpha in game."""
    if alpha <= 0:
        return
    r, g, b, a = layer.split()
    a = a.point(lambda v: int(v * min(1.0, alpha)))
    img.alpha_composite(Image.merge("RGBA", (r, g, b, a)), (int(xy[0]), int(xy[1])))


class Enemy:
    def __init__(self, sprite, x, ground, kb=0.5, name=""):
        self.sprite, self.x, self.ground, self.kb, self.name = sprite, float(x), ground, kb, name
        self.y = float(ground - sprite.height)
        self.vx = self.vy = 0.0
        self.tetanus = 0
        self.numbers = []                                     # (tick, text, colour)

    @property
    def box(self):
        return (self.x, self.y, self.x + self.sprite.width, self.y + self.sprite.height)

    def hit(self, tick, dmg, colour=(255, 199, 90)):
        self.numbers.append((tick, str(dmg), colour))

    def step(self, ground_at=None):
        g = ground_at(self.x + self.sprite.width / 2) if ground_at else self.ground
        self.vy = min(self.vy + 0.3, 10.0)
        self.x += self.vx
        self.y += self.vy
        if self.y + self.sprite.height >= g:
            self.y = g - self.sprite.height
            self.vy = 0.0
            self.vx *= 0.8

    def draw(self, img, gif, tick, cam=(0, 0)):
        spr = self.sprite
        if self.tetanus > tick:
            r, g, b, a = spr.split()
            spr = Image.merge("RGBA", (r.point(lambda v: min(255, int(v * 1.15) + 20)), g.point(lambda v: int(v * 0.8)), b.point(lambda v: int(v * 0.6)), a))
        img.alpha_composite(spr, (int(self.x - cam[0]), int(self.y - cam[1])))
        for (t0, s, col) in self.numbers:
            if 0 <= tick - t0 < 45:
                gif.text(img, (int(self.x - cam[0]) + 4, int(self.y - cam[1]) - 18 - (tick - t0) // 2), s, fill=col, font=gif.big)


def collector_sprite():
    return frames("Content/Junkyard/NPCs/RustCollector.png", 40, 40, 40, 11)[0]


# ================================================================================================
# Tetanus
# ================================================================================================
def extension(p, out_part, hold):
    if p < out_part:
        u = 1 - p / out_part
        return 1 - u * u * u
    if p < out_part + hold:
        return 1.0
    back = (p - out_part - hold) / (1 - out_part - hold)
    return 1 - back * back * (3 - 2 * back)


def seg_hits(box, a, b, width):
    """Collision.CheckAABBvLineCollision approximated: points every 2 px along a->b, the box grown by width / 2."""
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2))
    hw = width / 2
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        if box[0] - hw < x < box[2] + hw and box[1] - hw < y < box[3] + hw:
            return True
    return False


def rotated(sprite, angle, flip_v):
    """The sprite turned to `angle` (radians, screen space) about its centre, flipped vertically first when pointing
    left (TetanusProjectile.PreDraw), nearest-neighbour like the GPU's point sampling."""
    s = sprite.transpose(Image.FLIP_TOP_BOTTOM) if flip_v else sprite
    return s.rotate(-math.degrees(angle), resample=Image.NEAREST, expand=True)


def scene_tetanus(out, font):
    """2026-10-27: an 8.5-tile lance aimed in any direction. Quick thrusts right, up at a flier, down-left behind the
    player (each hits going out and coming back), then a 2.5 s charge aimed up-right and the charged lunge, which now
    also hits twice."""
    lance = load(W_DIR + "TetanusProjectile.png")
    L = K["Length"]
    glow = frames(W_DIR + "TetanusProjectile_Glow.png", lance.width, 18, 20, 6)
    flash = frames(W_DIR + "TetanusFlash.png", 48, 48, 50, 5)
    W, H, ground = 820, 420, 360
    bg = backdrop(W, H, ground)
    gif = Gif(font, (W, H))
    pc = (410.0, ground - 21.0)                          # the player's centre (MountedCenter)
    reach = K["ReachMax"]
    fly = frames("Content/Junkyard/NPCs/RustCollector.png", 40, 40, 40, 11)[9]
    foes = {"right": Enemy(collector_sprite(), pc[0] + reach - 28, ground, name="right"),
            "flier": Enemy(fly, pc[0] + reach * 0.62 - 20, 0, name="flier"),
            "left": Enemy(collector_sprite(), pc[0] - reach + 4, ground, name="left"),
            "high": Enemy(fly, pc[0] + reach * 0.7 - 20, 0, name="high")}
    foes["flier"].y = pc[1] - reach * 0.78 - 20
    foes["high"].y = pc[1] - reach * 0.72 - 20
    foes["high"].x = pc[0] - reach * 0.68 - 20                 # up and behind: the lunge goes up-left
    for k in ("flier", "high"):
        foes[k].ground = foes[k].y + 40
    use = K["UseTime"]
    step_ticks, step_pct, max_steps = K["ChargeStepTicks"], K["ChargeStepPercent"], K["MaxChargeSteps"]
    up_flier = math.atan2(foes["flier"].y + 20 - pc[1], foes["flier"].x + 20 - pc[0])
    up_high = math.atan2(foes["high"].y + 20 - pc[1], foes["high"].x + 20 - pc[0])
    timeline = [("quick", use, 0.0, "right"), ("pause", 14, 0.0, None), ("quick", use, up_flier, "flier"), ("pause", 14, up_flier, None),
                ("quick", use, math.radians(176), "left"), ("pause", 20, math.radians(176), None),
                ("charge", max_steps * step_ticks + 20, up_high, None), ("thrust", K["ThrustTicks"], up_high, "high"), ("pause", 50, up_high, None)]
    tick = 0
    parts = []
    rng = random.Random(3)
    charge_ticks = 0
    for mode, length, aim, target in timeline:
        hit_set = set()
        returning = False
        d = (math.cos(aim), math.sin(aim))
        for t in range(length):
            tip = K["ReachMin"]
            if mode == "charge":
                charge_ticks = min(t + 1, max_steps * step_ticks)
            elif mode != "thrust":
                charge_ticks = 0
            mult = 1.0
            if mode == "quick":
                p = (t + 1) / use
                if p >= K["QuickOut"] + K["QuickHold"] and not returning:
                    returning = True
                    hit_set = set()                       # Array.Clear(localNPCImmunity): the second hit on the way back
                tip = K["ReachMin"] + (K["ReachMax"] - K["ReachMin"]) * extension(p, K["QuickOut"], K["QuickHold"])
            elif mode == "charge":
                tip = K["ReachMin"] - K["DrawBack"] * min(1.0, (t + 1) / 12.0)
                if (t + 1) % step_ticks == 0 and (t + 1) // step_ticks <= max_steps:
                    parts.append([0, "+%d%%" % (step_pct * ((t + 1) // step_ticks)), tick])
            elif mode == "thrust":
                p = (t + 1) / K["ThrustTicks"]
                if p >= K["ThrustOut"] + K["ThrustHold"] and not returning:
                    returning = True
                    hit_set = set()                       # 2026-10-27: the lunge hits again on the way back
                tip = K["ReachMin"] - K["DrawBack"] + (K["ReachMax"] - K["ReachMin"] + K["DrawBack"]) * extension(p, K["ThrustOut"], K["ThrustHold"])
                mult = 1 + min(max_steps, charge_ticks // step_ticks) * step_pct / 100
            if mode in ("quick", "thrust"):
                a = (pc[0] + d[0] * (tip - L + 14), pc[1] + d[1] * (tip - L + 14))
                b = (pc[0] + d[0] * tip, pc[1] + d[1] * tip)
                for f in foes.values():
                    if f.name not in hit_set and seg_hits(f.box, a, b, 10):
                        hit_set.add(f.name)
                        dmg = 27 * mult * (1 + K["DamageTakenPercent"] / 100 if f.tetanus > tick else 1)
                        f.hit(tick, int(dmg), (255, 140, 60) if f.tetanus > tick else (255, 199, 90))
                        f.tetanus = tick + K["DebuffTicks"]
            if tick % TPF == 0:
                img = bg.copy()
                dr = ImageDraw.Draw(img)
                dr.ellipse([pc[0] - reach, pc[1] - reach, pc[0] + reach, pc[1] + reach], outline=(198, 189, 255))
                title = {"quick": "Left click (held): a thrust wherever you aim, hits out and back",
                         "pause": "", "charge": "Hold right click, aimed up: charging +%d%%" % (step_pct * min(max_steps, charge_ticks // step_ticks)),
                         "thrust": "Release: the charged lunge x%.1f, now hits out AND back" % mult}[mode]
                gif.text(img, (14, 10), title, font=gif.big)
                gif.text(img, (14, 38), "27 damage, %.1f-tile reach (purple circle); orange numbers: Tetanus +%d%% taken" % (K["ReachTiles"], K["DamageTakenPercent"]))
                for f in foes.values():
                    f.draw(img, gif, tick)
                facing_left = d[0] < 0
                pl = player_sprite(flip=facing_left)
                img.alpha_composite(pl, (int(pc[0] - 20), int(pc[1] - 35)))
                centre = (pc[0] + d[0] * (tip - L / 2), pc[1] + d[1] * (tip - L / 2))
                shake = rng.choice((-2, 0, 2)) if mode == "charge" and charge_ticks > max_steps * step_ticks / 2 else 0
                spr = rotated(lance, aim, facing_left)
                pos = (int(centre[0] - spr.width / 2), int(centre[1] - spr.height / 2 + shake))
                if mode == "thrust" and t < K["ThrustTicks"] * (K["ThrustOut"] + K["ThrustHold"]):
                    steps = min(max_steps, charge_ticks // step_ticks)
                    for k in (3, 2, 1):
                        glow_over(img, spr, 0.18 * (4 - k), (pos[0] - d[0] * k * (10 + 4 * steps), pos[1] - d[1] * k * (10 + 4 * steps)))
                img.alpha_composite(spr, pos)
                g_amt = min(1.0, charge_ticks / (max_steps * step_ticks)) if mode == "charge" else (0.4 + 0.6 * min(max_steps, charge_ticks // step_ticks) / max_steps if mode == "thrust" else 0)
                if g_amt > 0:
                    glow_over(img, rotated(glow[(tick // 4) % 6], aim, facing_left), g_amt, pos)
                if mode == "thrust":
                    fi = (t - (int(K["ThrustTicks"] * K["ThrustOut"]) - 2)) // 2
                    if 0 <= fi < 5:
                        tx, ty = pc[0] + d[0] * tip, pc[1] + d[1] * tip
                        glow_over(img, flash[fi], 1.0, (tx - 24, ty - 24))
                for (_, s, t0) in parts:
                    if 0 <= tick - t0 < 30:
                        gif.text(img, (int(pc[0] + d[0] * tip - 10), int(pc[1] + d[1] * tip - 40 - (tick - t0) // 2)), s, fill=(198, 189, 255), font=gif.big)
                gif.push(img)
            tick += 1
    gif.save(out)
    print("tetanus:", {k: [n[1] for n in f.numbers] for k, f in foes.items()})


# ================================================================================================
# Scrap Launcher
# ================================================================================================
def impact_frames():
    sheet = load(W_DIR + "ScrapImpact.png")
    small = [sheet.crop((0, k * 50, 48, k * 50 + 48)) for k in range(5)]
    big = [sheet.crop((50, k * 82, 130, k * 82 + 80)) for k in range(5)]
    return small, big


def scene_launcher(out, font):
    """2026-10-27: left click fires chewed scrap dead straight across a whole screen (no gravity), right click lobs the
    big ball (gravity, one bounce) every 31 ticks; both burst on impact. The screen is 1920 px wide, shown at half size."""
    gun = load(W_DIR + "ScrapLauncher.png")
    chunk = frames(W_DIR + "ScrapLauncherChunk.png", 32, 32, 34, 3)
    ball = frames(W_DIR + "ScrapLauncherBall.png", 60, 60, 62, 4)
    small, big = impact_frames()
    W, H, ground = 1920, 600, 520
    bg = backdrop(W, H, ground)
    gif = Gif(font, (W, H), scale=0.5)
    pc = (80.0, ground - 21.0)
    far = Enemy(collector_sprite(), W - 210, ground, name="far")
    near = Enemy(collector_sprite(), 400, ground, name="near")
    foes = [far, near]
    for f in foes:
        f.life = 100
    near.life = 0                                       # it rolls in for the right-click part
    shots, bursts = [], []                              # [x, y, vx, vy, kind, bounces, alive, frame, life] ; [x, y, big, t]
    plan = [("chunk", 0.0), ("chunk", 0.0), ("chunk", 0.0), ("wait2", 0), ("ball", -0.62), ("ball", -0.75), ("wait", 0)]
    tick = 0
    log = []
    for kind, aim in plan:
        length = K["UseTime"] if kind == "chunk" else (K["BigShotUseTime"] if kind == "ball" else (100 if kind == "wait2" else 90))
        for t in range(length):
            if kind == "ball" and near.life <= 0 and not getattr(near, "arrived", False):
                near.life, near.arrived = 120, True
            if t == 0 and kind not in ("wait", "wait2"):
                sp = K["BallSpeed"] if kind == "ball" else K["ChunkSpeed"]
                muzzle = (pc[0] + 30 * math.cos(aim), pc[1] + 30 * math.sin(aim))
                shots.append([muzzle[0], muzzle[1], sp * math.cos(aim), sp * math.sin(aim), kind, 0, True, 0, 0])
            for s in shots:
                if not s[6]:
                    continue
                if s[4] == "ball":
                    s[3] = min(s[3] + K["BallGravity"], 16)  # only the ball falls (2026-10-27)
                s[0] += s[2]
                s[1] += s[3]
                s[8] += 1
                half = 22 if s[4] == "ball" else 10
                box = (s[0] - half, s[1] - half, s[0] + half, s[1] + half)
                for f in foes:
                    fb = f.box
                    if f.life > 0 and s[6] and box[0] < fb[2] and box[2] > fb[0] and box[1] < fb[3] and box[3] > fb[1]:
                        s[6] = False
                        dmg = int(20 * K["BigShotMultiplier"]) if s[4] == "ball" else 20
                        f.hit(tick, dmg)
                        f.life -= dmg
                        kb = 6.5 * (K["BigShotKnockback"] if s[4] == "ball" else 1.0) * 0.4
                        f.vx += kb
                        f.vy = -kb * 0.6
                        bursts.append([s[0], s[1], s[4] == "ball", 0])
                        log.append((tick, s[4], "hit", dmg, int(s[0] - pc[0])))
                if s[6] and s[1] + half >= ground:
                    if s[4] == "ball" and s[5] < K["MaxBounces"]:
                        s[5] += 1
                        s[1] = ground - half
                        s[3] = -s[3] * K["BounceKeep"]
                        s[2] *= K["BounceKeep"]
                    else:
                        s[6] = False
                        bursts.append([s[0], ground - half, s[4] == "ball", 0])
                if s[6] and s[4] == "chunk" and s[8] >= K["Lifetime"]:
                    s[6] = False                          # out of range (a whole screen): it just drops out of sight
                    log.append((tick, "chunk", "range", int(s[0] - pc[0])))
                if tick % 5 == 0:
                    s[7] = (s[7] + 1) % (4 if s[4] == "ball" else 3)
            for f in foes:
                f.step()
            for b in bursts:
                b[3] += 1
            bursts[:] = [b for b in bursts if b[3] < 5 * 3]
            if tick % TPF == 0:
                img = bg.copy()
                for f in foes:
                    if f.life > 0:
                        f.draw(img, gif, tick)
                pl = player_sprite()
                img.alpha_composite(pl, (int(pc[0] - 20), int(pc[1] - 35)))
                ang = 0.0 if kind in ("wait", "wait2") else aim
                g = gun.rotate(-math.degrees(ang), resample=Image.NEAREST, expand=True)
                hx, hy = pc[0] - 2, pc[1]                 # Main.DrawPlayerItemPos: the sprite's centre on MountedCenter
                ox = 6 - gun.width / 2                    # HoldoutOffset X = -6: the hand 6 px from the butt
                img.alpha_composite(g, (int(hx - ox * math.cos(ang) - g.width / 2), int(hy - ox * math.sin(ang) - g.height / 2)))
                for s in shots:
                    if s[6]:
                        spr = ball[s[7]] if s[4] == "ball" else chunk[s[7]]
                        img.alpha_composite(spr, (int(s[0] - spr.width / 2), int(s[1] - spr.height / 2)))
                for (x, y, is_big, bt) in bursts:
                    fr = (big if is_big else small)[min(4, bt // 3)]
                    img.alpha_composite(fr, (int(x - fr.width / 2), int(y - fr.height / 2)))
                gif.text(img, (24, 16), "Left click: chewed scrap, no gravity, a whole screen (1920 px) - 20 dmg, KB 6.5" if kind in ("chunk", "wait2")
                         else "Right click: the big ball, gravity + one bounce, 31 use time - 50 dmg, KB x1.6", font=gif.big)
                gif.text(img, (24, 48), "every hit bursts: brass starburst, scrap shards, steam (no more vanishing)", font=gif.big)
                gif.push(img)
            tick += 1
    gif.save(out)
    print("launcher:", log)


def held_png(out, font):
    """The Scrap Launcher held at each aim, placed the way vanilla does (decompiled ItemCheck_ApplyUseStyle_Inner +
    PlayerDrawLayers useStyle 5): the sprite's vertical centre on MountedCenter, the hand HoldoutOffset.X = 6 px from
    the butt. Before (72x40, offset (-8, 2)) and after (52x24, offset (-6, 0)), over the stand-in player."""
    new = load(W_DIR + "ScrapLauncher.png")
    img = Image.new("RGBA", (520, 150), (150, 180, 210, 255))
    gif = Gif(font, (520, 150))
    pl = player_sprite()
    for k, ang in enumerate((-0.6, 0.0, 0.5)):
        pc = (70 + k * 130, 95)
        img.alpha_composite(pl, (int(pc[0] - 20), int(pc[1] - 35)))
        g = new.rotate(-math.degrees(ang), resample=Image.NEAREST, expand=True)
        ox = 6 - new.width / 2
        img.alpha_composite(g, (int(pc[0] - 2 - ox * math.cos(ang) - g.width / 2), int(pc[1] - ox * math.sin(ang) - g.height / 2)))
    gif.text(img, (8, 6), "Scrap Launcher held (52x24): barrel at arm level, not over the head")
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(out)
    print("wrote", out)


# ================================================================================================
# Scrapmancer
# ================================================================================================
def scene_scrapmancer(out, font):
    wave = frames(W_DIR + "ScrapmancerWave.png", 88, 60, 62, 4)
    staff = load(W_DIR + "Scrapmancer.png")
    W, H = 2000, 640
    base = 520

    def ground_at(x):
        if x < 900:
            return base
        if x < 1400:
            return base - 32                              # a 2-tile step up
        return base + 32                                  # a 4-tile drop (from the step: 64 px)

    bg = backdrop(W, H, base, ground_at)
    gif = Gif(font, (W, H), scale=0.5)
    pl = player_sprite()
    px = 160.0
    foes = [Enemy(collector_sprite(), x, ground_at(x + 16), kb=0.4) for x in (520, 1100, 1650)]
    tick = 0
    w = None
    hits = []
    for t in range(K["Lifetime"] + 60):
        if t == 10:
            w = {"x": px + 40, "bottom": float(ground_at(px + 40)), "frame": 0, "hit": set(), "life": K["Lifetime"]}
        if w and w["life"] > 0:
            w["x"] += K["WaveSpeed"]
            front = w["x"] + K["HitboxWidth"] / 2
            g = ground_at(front)
            if g - w["bottom"] < -K["MaxStepUp"] * 16 or g - w["bottom"] > K["MaxDrop"] * 16:
                w["life"] = 0                             # a wall or a pit breaks it
            w["bottom"] = float(g)
            w["life"] -= 1
            w["frame"] = (tick // K["TicksPerFrame"]) % 4
            box = (w["x"] - K["HitboxWidth"] / 2, w["bottom"] - K["HitboxHeight"], w["x"] + K["HitboxWidth"] / 2, w["bottom"])
            for k, f in enumerate(foes):
                fb = f.box
                if k not in w["hit"] and box[0] < fb[2] and box[2] > fb[0] and box[1] < fb[3] and box[3] > fb[1]:
                    w["hit"].add(k)                       # each enemy once (localNPCHitCooldown -1)
                    f.hit(tick, 33)
                    f.vx = 9 * f.kb * 1.4                 # knockback 9 along the wave (vanilla scales by KB resist)
                    f.vy = -6 * f.kb * 1.4
                    hits.append((tick, k))
        for f in foes:
            f.step(ground_at)
        if tick % TPF == 0:
            img = bg.copy()
            for f in foes:
                f.draw(img, gif, tick)
            img.alpha_composite(pl, (int(px - 20), int(ground_at(px) - 56)))
            sw = staff if t > 12 else staff.transpose(Image.ROTATE_90)
            img.alpha_composite(sw, (int(px - 6), int(ground_at(px) - 70)))
            if w and w["life"] > 0:
                fr = wave[w["frame"]].transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(fr, (int(w["x"] - 44), int(w["bottom"] - 58)))
            gif.text(img, (20, 16), "Scrapmancer: a junk shockwave along the ground, 33 damage, pierces all, knockback 9", font=gif.big)
            gif.text(img, (20, 46), "16 px/tick for 120 ticks = 1920 px (a whole screen); climbs 3 tiles, drops 8; each enemy hit once", font=gif.big)
            gif.push(img)
        tick += 1
    gif.save(out)
    print("scrapmancer hits:", hits)


# ================================================================================================
# Tr0mhead sentry
# ================================================================================================
def scene_tr0mhead(out, font):
    sheet = frames(W_DIR + "Tr0mheadSentry.png", 56, 60, 62, 10)
    glow = frames(W_DIR + "Tr0mheadSentry_Glow.png", 56, 60, 62, 10)
    tar = frames("Content/Junkyard/NPCs/LivingTar.png", 32, 24, 24, 2)[0]
    W, H, ground = 900, 360, 300
    bg = backdrop(W, H, ground)
    gif = Gif(font, (W, H))
    sx = 300.0
    centre = (sx, ground - 22.0)
    mouth = (centre[0] - K["MouthOffset_X"], centre[1] + K["MouthOffset_Y"])
    foes = [Enemy(collector_sprite(), 720, ground, kb=0.4, name="Rust Collector (KB resist 0.4)"),
            Enemy(tar, 560, ground, kb=0.8, name="Living Tar (0.8)"),
            Enemy(collector_sprite(), 30, ground, kb=0.4, name="Rust Collector behind")]
    bat = Enemy(frames("Content/Junkyard/NPCs/RustCollector.png", 40, 40, 40, 11)[4], 140, 0, kb=0.4, name="flier (0.4)")
    bat.y, bat.flier = ground - 170.0, True
    foes.append(bat)
    for f in foes:
        f.walk = -0.9 if f.x > sx else 0.9
        f.flier = getattr(f, "flier", False)
    state, t, facing = "idle", 0, 1
    imm = {}
    tick = 0
    damage = {}
    total = 12 + K["SuckTicks"] + 12 + K["RestTicks"] + 80
    reach2 = K["SuckRange"] ** 2
    for _ in range(total):
        t += 1
        in_reach = [f for f in foes if (f.x + 16 - mouth[0]) ** 2 + (f.y + 12 - mouth[1]) ** 2 <= reach2]
        if state == "idle" and in_reach:
            state, t = "open", 0
        elif state == "open" and t >= K["OpenTicks"]:
            state, t = "suck", 0
        elif state == "suck" and t >= K["SuckTicks"]:
            state, t = "close", 0
        elif state == "close" and t >= K["CloseTicks"]:
            state, t = "rest", 0
        elif state == "rest" and t >= K["RestTicks"]:
            state, t = "idle", 0
        if in_reach:
            near = min(in_reach, key=lambda f: abs(f.x - sx))
            facing = 1 if near.x + 16 >= sx else -1
        mouth = (centre[0] + K["MouthOffset_X"] * -facing, centre[1] + K["MouthOffset_Y"])   # Tr0mheadSentry.Mouth
        for f in foes:
            if state != "suck" and f.vy == 0:
                f.vx = f.walk
            if state == "suck":
                strength = min(1.0, t / K["RampTicks"])
                dx = mouth[0] - (f.x + 16)
                dy = mouth[1] - (f.y + 12)
                d = math.hypot(dx, dy)
                if K["MouthStop"] < d <= K["SuckRange"]:
                    fall = 1.0 if d < K["FullPullRange"] else 1 - (d - K["FullPullRange"]) / (K["SuckRange"] - K["FullPullRange"])
                    steer = K["PullSteer"] * strength * fall * min(1.0, f.kb) * (K["FlyerSteerScale"] if f.flier else 1.0)
                    speed = K["PullSpeed"] * (K["FlyerPullScale"] if f.flier else 1.0)
                    f.vx += (dx / d * speed - f.vx) * steer
                    if f.flier:
                        f.vy += (dy / d * speed - f.vy) * steer
                elif d <= K["MouthStop"]:
                    f.vx *= 0.5
                key = id(f)
                if d <= K["SuckRange"] and imm.get(key, -999) + K["HitCooldown"] <= tick:
                    imm[key] = tick                       # localNPCHitCooldown: one bite per enemy per second
                    f.hit(tick, 15)
                    damage[f.name] = damage.get(f.name, 0) + 15
            if f.flier:                                   # no gravity: it just drifts (hovers when nothing pulls it)
                f.x += f.vx
                f.y += f.vy
                if state != "suck":
                    f.vx, f.vy = 0.6, 0.0
            else:
                f.step()
        frame = {"idle": (t // 20) % 2, "open": 2 if t < K["OpenTicks"] // 2 else 3, "suck": 4 + (t // 3) % 4,
                 "close": 3 if t < K["CloseTicks"] // 2 else 2, "rest": 8 + (t // 15) % 2}[state]
        if tick % TPF == 0:
            img = bg.copy()
            d = ImageDraw.Draw(img)
            if state == "suck":
                d.ellipse([mouth[0] - K["SuckRange"], mouth[1] - K["SuckRange"], mouth[0] + K["SuckRange"], mouth[1] + K["SuckRange"]], outline=(124, 107, 224))
            for f in foes:
                f.draw(img, gif, tick)
            spr = sheet[frame].transpose(Image.FLIP_LEFT_RIGHT) if facing == 1 else sheet[frame]
            gl = glow[frame].transpose(Image.FLIP_LEFT_RIGHT) if facing == 1 else glow[frame]
            pos = (int(sx - 28), int(ground + 2 - 60))
            img.alpha_composite(spr, pos)
            glow_over(img, gl, 1.0 if state == "suck" else (0.35 if state == "rest" else 0.85), pos)
            if state == "suck":
                rng = random.Random(tick)
                for _ in range(4):
                    a = (0 if facing == 1 else math.pi) + rng.uniform(-1.1, 1.1)
                    r = rng.uniform(60, K["SuckRange"])
                    x, y = mouth[0] + math.cos(a) * r, mouth[1] + math.sin(a) * r
                    d.line([x, y, x + (mouth[0] - x) * 0.08, y + (mouth[1] - y) * 0.08], fill=(198, 189, 255) if rng.random() < 0.3 else (238, 241, 243))
            label = {"idle": "Idle: nothing in reach", "open": "An enemy in reach: the jaw drops", "suck": "Sucking %d/%d (5 s max): pulled by KB resistance, chewed 15/s each" % (t, K["SuckTicks"]),
                     "close": "Gulp: the jaw shuts", "rest": "Resting %d/%d (2.5 s): steam" % (t, K["RestTicks"])}[state]
            gif.text(img, (14, 10), label, font=gif.big)
            gif.text(img, (14, 38), "reach %d tiles (purple circle); fliers pulled x%.1f harder; damage: %s" % (K["SuckRange"] // 16, K["FlyerPullScale"], ", ".join("%s %d" % (k.split(" (")[0], v) for k, v in damage.items() if k)))
            gif.push(img)
        tick += 1
    gif.save(out)
    print("tr0mhead damage:", damage)


# ================================================================================================
# Loot sheet (PNG)
# ================================================================================================
def loot_png(out, font):
    f = ImageFont.truetype(font, 15)
    items = [("Treasure Bag", "Content/Bosses/TrashTr0m/Items/TrashTr0mBag.png"), ("Tetanus", W_DIR + "Tetanus.png"),
             ("Scrap Launcher", W_DIR + "ScrapLauncher.png"), ("Scrapmancer", W_DIR + "Scrapmancer.png"),
             ("Tr0mhead", W_DIR + "Tr0mheadStaff.png"), ("Tetanus (debuff)", "Content/Bosses/TrashTr0m/Buffs/TetanusDebuff.png")]
    strips = [("held lance + glow", [load(W_DIR + "TetanusProjectile.png")] + frames(W_DIR + "TetanusProjectile_Glow.png", 112, 18, 20, 6)[:2]),
              ("impact bursts (chunk / ball)", impact_frames()[0] + impact_frames()[1]),
              ("Trash-Tr0m's loose cog", frames("Content/Bosses/TrashTr0m/Projectiles/TrashTr0mCog.png", 24, 24, 26, 4)),
              ("flash ring", frames(W_DIR + "TetanusFlash.png", 48, 48, 50, 5)),
              ("chewed scrap / scrap ball", frames(W_DIR + "ScrapLauncherChunk.png", 32, 32, 34, 3) + frames(W_DIR + "ScrapLauncherBall.png", 60, 60, 62, 4)),
              ("junk shockwave", frames(W_DIR + "ScrapmancerWave.png", 88, 60, 62, 4)),
              ("Tr0mhead: idle, opening, sucking, resting", frames(W_DIR + "Tr0mheadSentry.png", 56, 60, 62, 10))]
    z = 2
    rows = []
    for bgc in ((24, 22, 30), (150, 180, 210)):
        x = 10
        row = Image.new("RGBA", (1900, 210), bgc + (255,))
        d = ImageDraw.Draw(row)
        for name, path in items:
            im = load(path)
            im = im.resize((im.width * z, im.height * z), Image.NEAREST)
            row.alpha_composite(im, (x, 30))
            d.text((x, 6), name, fill=(238, 241, 243) if bgc[0] < 100 else (21, 22, 28), font=f)
            x += max(im.width, 120) + 30
        rows.append(row)
    for name, ims in strips:
        h = max(im.height for im in ims) * z + 40
        row = Image.new("RGBA", (1900, h), (24, 22, 30, 255))
        ImageDraw.Draw(row).text((10, 6), name + " (2x zoom)", fill=(238, 241, 243), font=f)
        x = 10
        for im in ims:
            im = im.resize((im.width * z, im.height * z), Image.NEAREST)
            row.alpha_composite(im, (x, 32))
            x += im.width + 12
        rows.append(row)
    H = sum(r.height for r in rows)
    sheet = Image.new("RGBA", (1900, H), (40, 40, 48, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    sheet.convert("RGB").save(out)
    print(out, sheet.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-10-26")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    base = os.path.join(args.out, args.date + "_weapon-")
    jobs = [("loot", lambda: loot_png(os.path.join(args.out, args.date + "_boss-trashtr0m-loot.png"), args.font)),
            ("tetanus", lambda: scene_tetanus(base + "tetanus.gif", args.font)),
            ("launcher", lambda: scene_launcher(base + "scrap-launcher.gif", args.font)),
            ("held", lambda: held_png(base + "scrap-launcher-held.png", args.font)),
            ("scrapmancer", lambda: scene_scrapmancer(base + "scrapmancer.gif", args.font)),
            ("tr0mhead", lambda: scene_tr0mhead(base + "tr0mhead.gif", args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
