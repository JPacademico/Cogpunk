"""D5 proofs for the 2026-10-27 update, built from the real sprites and the constants parsed out of the C# files,
replaying the code tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_10_27_sim.py --out docs/media --date 2026-10-27 [--only steam,trapper,...]

Writes <date>_<area>-<scene>.gif|png:
    mechanist-steam       the steam gauge left of the hearts (SteamGaugeSystem's layout and frames): with no gear the
                          tank is 0 and the Trapper Chain only clicks ("No steam tank!"); in the full Polished set and a
                          Glass Container (40) it refills, then the chain is thrown (4 steam a throw: 5 - 10%, rounded
                          like C#'s Math.Round) until the tank is empty; the next throw overheats (ember steam, the tank
                          rattles, items lock, the player keeps running) until the 1.5 s wait and the refill of 10 every
                          0.5 s fill it. The waits are shown 4x faster (labelled).
    mechanist-armor       PNG: the Polished set worn (vanilla frame mapping, tools/sim/armor_preview.py) and its icons.
    jungle-trapper        the Trapper: it lobs spike balls at an approaching player (30-tick wind-up), they bounce and lie
                          on the ground; when the player gets within 9 tiles it turns and runs, then throws again.
    weapon-trapper-chain  the Trapper Chain: a close bite on two overlapping enemies (both bitten while the jaws shut,
                          BiteTicks, each once), back fast and thrown again at once; then a long miss to 18 tiles and back. The next
                          throw comes when the trap is back (Player.SetDummyItemTime), at least MinCycleTicks apart.
    junkyard-tar-glob     a Living Tar lobbing globs (TarGlob.AimAt): every frame picks the pre-rendered heading of its
                          velocity, so the glob always points where it flies.
    junkyard-rust-collector  the 0.8x Rust Collector ramping up and ramming a player: knockback 4.5 + 1 per px/tick of
                          its speed, thrown the way it rolled (vanilla Player.Hurt: velocity = (kb x dir, -kb x 7/9)).
    junkyard-rust-polisher the polisher tile's 6 frames (4 ticks each), without the old steam stack.

Leaves out: lighting, tile collision beyond a flat floor, vanilla's player animation (a standing frame slides), network
latency, damage numbers beyond the ones printed.
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

TPF = 3


def consts(*paths):
    raw = {}
    for path in paths:
        for m in re.finditer(r"const (?:int|float) ([^;]+);", open(path, encoding="utf-8").read()):
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
            expr = re.sub(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", r"\1", expr)
            try:
                out[k] = eval(expr, {}, dict(out))
            except Exception:
                pass
    return out


M = "Content/Mechanist/"
K = consts(M + "SteamPlayer.cs", M + "SteamGaugeSystem.cs", M + "Armor/PolishedHelmet.cs", M + "Armor/PolishedChestplate.cs",
           M + "Weapons/TrapperChain.cs", M + "Weapons/TrapperChainProjectile.cs")
KG = consts(M + "Accessories/GlassContainer.cs")
KT = consts("Content/Jungle/NPCs/Trapper.cs", "Content/Jungle/Projectiles/TrapperSpikeBall.cs")
KJ = consts("Content/Junkyard/NPCs/RustCollector.cs", "Content/Junkyard/Projectiles/TarGlob.cs", "Content/Junkyard/NPCs/LivingTar.cs")
KP = consts("Content/Junkyard/Tiles/RustPolisherTile.cs")


def load(p):
    return Image.open(p).convert("RGBA")


def frames(p, w, h, stride, n, x=0):
    im = load(p)
    return [im.crop((x, k * stride, x + w, k * stride + h)) for k in range(n)]


def polished_player(flip=False):
    h = ap.load_frames(M + "Armor/PolishedHelmet_Head.png", 1)[0]
    b = ap.load_frames(M + "Armor/PolishedChestplate_Body.png", 1)[0]
    leg = ap.load_frames(M + "Armor/PolishedPants_Legs.png", 1)[0]
    s = ap.compose(h, b, leg, 0, [0] * 20)
    return s.transpose(Image.FLIP_LEFT_RIGHT) if flip else s


class Gif:
    def __init__(self, font):
        self.font = ImageFont.truetype(font, 14)
        self.big = ImageFont.truetype(font, 18)
        self.frames = []

    def text(self, img, xy, s, fill=(238, 241, 243), big=False):
        d = ImageDraw.Draw(img)
        f = self.big if big else self.font
        for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            d.text((xy[0] + ox, xy[1] + oy), s, fill=(21, 22, 28), font=f)
        d.text(xy, s, fill=fill, font=f)

    def push(self, img, scale=1.0):
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.NEAREST)
        self.frames.append(img.convert("RGB"))

    def save(self, path):
        pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in self.frames]
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=TPF * 1000 // 60, loop=0, optimize=True, disposal=1)
        print("%s: %d frames, %.1f s, %.2f MB" % (path, len(self.frames), len(self.frames) * TPF / 60, os.path.getsize(path) / 1e6))


def backdrop(w, h, ground, sky=((150, 180, 210), (110, 130, 170)), dirt=(120, 92, 60), top=(147, 110, 70)):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([0, y, w, y], fill=tuple(int(a + (b - a) * t) for a, b in zip(*sky)) + (255,))
    d.rectangle([0, ground, w, h], fill=dirt + (255,))
    d.rectangle([0, ground, w, ground + 3], fill=top + (255,))
    return img


# ================================================================================================
# Steam, the gauge, Overheat
# ================================================================================================
class Steam:
    """SteamPlayer, line for line (owner side)."""

    def __init__(self, bonus, cost_mult):
        self.max = max(0, K["BaseSteamMax"] + bonus)
        self.steam = self.max
        self.cost_mult = cost_mult
        self.since = K["RegenDelayTicks"]
        self.timer = 0
        self.overheated = False

    def cost(self, base):
        return max(1, int(round(base * self.cost_mult)))       # Python's round() is banker's, like C#'s Math.Round

    def try_use(self, base):
        """MechanistWeapon.CanUseItem + UseItem."""
        if self.overheated:
            return "locked"
        if self.max < self.cost(base):
            return "notank"                                    # SteamPlayer.NoteNoTank: nothing fires, no overheat
        if self.steam < self.cost(base):
            self.overheated = True
            self.since, self.timer = 0, 0
            return "overheat"
        self.steam = max(0, self.steam - self.cost(base))
        self.since, self.timer = 0, 0
        return "fired"

    def update(self, attacking):
        if attacking:
            self.since = 0
        if self.since < K["RegenDelayTicks"]:
            self.since += 1
            self.timer = 0
        elif self.steam < self.max:
            self.timer += 1
            if self.timer >= K["RegenIntervalTicks"]:
                self.timer = 0
                self.steam = min(self.max, self.steam + K["BaseRegenAmount"])
        if self.overheated and self.steam >= self.max:
            self.overheated = False
            return "cooled"
        return None


def draw_gauge(img, sheet, st, screen_w, rng):
    """SteamGaugeSystem.DrawGauge at the same layout (UI px)."""
    w, h, stride = K["Width"], K["Height"], K["Stride"]
    x = screen_w - 300 - K["GapToHearts"] - w
    y = K["Top"]
    if st.overheated:
        x += rng.choice((-2, 0, 2))
    img.alpha_composite(sheet.crop((0, 0, w, h)), (x, y))
    fill = st.steam / st.max if st.max > 0 else 0.0
    inside = K["FillBottom"] - K["FillTop"]
    level = int(inside * fill * 0.5) * 2
    if level > 0:
        fr = 2 if st.overheated else 1
        top = K["FillBottom"] - level
        img.alpha_composite(sheet.crop((0, fr * stride + top, w, fr * stride + top + level)), (x, y + top))
    regen = st.steam < st.max and st.since >= K["RegenDelayTicks"]
    front = 4 if regen and (TICK[0] // 8) % 2 == 1 else 3
    img.alpha_composite(sheet.crop((0, front * stride, w, front * stride + h)), (x, y))
    return x, y


TICK = [0]


def scene_steam(out, font):
    sheet = load(M + "SteamGauge.png")
    heart = Image.new("RGBA", (22, 20), (0, 0, 0, 0))
    hd = ImageDraw.Draw(heart)
    hd.ellipse([0, 0, 11, 11], fill=(200, 40, 50, 255))
    hd.ellipse([10, 0, 21, 11], fill=(200, 40, 50, 255))
    hd.polygon([(1, 7), (21, 7), (11, 19)], fill=(200, 40, 50, 255))
    SW, SH, ground = 900, 300, 250
    gif = Gif(font)
    bg = backdrop(SW, SH, ground)
    gear = K["SteamCapacity"] + KG["Capacity"]
    st = Steam(0, 1.0)
    rng = random.Random(4)
    px, vx, facing = 240.0, 0.0, 1
    cycle = 24                                             # a mid-range bite: the trap is back after about 24 ticks
    plan = [("bare", 70), ("refill", 200), ("throw", 2000), ("overheat", 2000)]
    pl = polished_player()
    plf = polished_player(flip=True)
    log = []
    tick = 0
    hint = 0
    for phase, length in plan:
        if phase == "refill":
            st = Steam(gear, 1 - K["SteamCostReduction"] / 100)
            st.steam = 0                                   # the gear just went on: an empty tank
        for t in range(length):
            attacking = False
            event = None
            if phase in ("bare", "throw") and t % (20 if phase == "bare" else cycle) == 0:
                event = st.try_use(K["Cost"])
                attacking = event == "fired"
                log.append((tick, event, st.steam))
                if event == "notank" and hint <= 0:
                    hint = K["NoTankHintTicks"]
            hint -= 1
            cooled = st.update(attacking)
            if st.overheated:                              # SteamPlayer.SetControls holds the facing direction
                if px > SW - 120:
                    facing = -1
                elif px < 120:
                    facing = 1
                want = facing * 3.0 * 1.1
                vx += max(-0.2, min(0.2, want - vx))
            else:
                vx = 0.0 if abs(vx) < 0.2 else vx - math.copysign(0.2, vx)
            px += vx
            if cooled:
                log.append((tick, "cooled", st.steam))
            TICK[0] = tick
            fast = (phase == "refill" and t > 30) or (st.overheated and t > 40)
            every = TPF * 4 if fast else TPF
            if tick % every == 0:
                img = bg.copy()
                for k in range(5):
                    img.alpha_composite(heart, (SW - 300 + 4 + k * 26, 32))
                gx, gy = draw_gauge(img, sheet, st, SW, rng)
                gif.text(img, (gx - 98, gy + 70), "Steam: %d/%d" % (st.steam, st.max))
                spr = pl if facing == 1 else plf
                img.alpha_composite(spr, (int(px - 20), ground - 56))
                if phase == "bare" and hint > K["NoTankHintTicks"] - 45:
                    gif.text(img, (int(px) - 50, ground - 80 - (K["NoTankHintTicks"] - hint) // 3), "No steam tank!", fill=(195, 200, 205))
                if st.overheated:
                    d = ImageDraw.Draw(img)
                    for k in range(3):
                        sx = px - facing * (8 + k * 6) + rng.uniform(-3, 3)
                        sy = ground - 40 + rng.uniform(-4, 4) - k * 4
                        d.ellipse([sx - 3 - k, sy - 3 - k, sx + 3 + k, sy + 3 + k], fill=(238, 241, 243, 255))
                label = {"bare": "No Mechanist gear: the tank is 0, the Trapper Chain only clicks (no overheat)",
                         "refill": "Polished set + Glass Container: tank %d, refilling +%d every %d ticks" % (st.max, K["BaseRegenAmount"], K["RegenIntervalTicks"]),
                         "throw": "Throwing the Trapper Chain: %d steam a throw (5 - 10%% set bonus)" % st.cost(K["Cost"]),
                         "overheat": "OVERHEATED: no items, can't stop moving until the tank is full" if st.overheated else "Cooled down: full tank, control back"}[phase]
                gif.text(img, (14, 10), label, big=True)
                sub = "tank %d: %d chestplate + %d Glass Container" % (st.max, K["SteamCapacity"], KG["Capacity"]) if st.max else "tank 0 (base)"
                gif.text(img, (14, 36), sub + ("   x4 speed" if fast else ""))
                if phase == "overheat" and st.overheated:
                    gif.text(img, (14, 56), "refill starts %d ticks (1.5 s) after the last throw" % K["RegenDelayTicks"])
                gif.push(img)
            tick += 1
            if phase == "refill" and st.steam >= st.max and t > 40:
                break
            if phase == "throw" and event == "overheat":
                break
            if phase == "overheat" and not st.overheated and t > 50:
                break
    gif.save(out)
    print("steam:", log[:3], "...", log[-4:])


def armor_png(out, font):
    h = ap.load_frames(M + "Armor/PolishedHelmet_Head.png", 1)[0]
    b = ap.load_frames(M + "Armor/PolishedChestplate_Body.png", 1)[0]
    leg = ap.load_frames(M + "Armor/PolishedPants_Legs.png", 1)[0]
    bob = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3
    poses = [ap.compose(h, b, leg, f, bob) for f in (0, 5, 7, 10, 14, 17)]
    icons = [load(M + p) for p in ("Armor/PolishedHelmet.png", "Armor/PolishedChestplate.png", "Armor/PolishedPants.png", "SteamGauge.png",
                                    "Overheat.png", "Weapons/TrapperChain.png", "Weapons/TrapperChainProjectile.png",
                                    "Accessories/GlassContainer.png", "Accessories/BrassContainer.png")]
    W = 6 * 44 + sum(i.width + 10 for i in icons) + 20
    H = 120
    img = Image.new("RGBA", (W, H * 2), (30, 30, 36, 255))
    img.paste((150, 180, 210, 255), (0, H, W, 2 * H))
    for row in (0, 1):
        x = 6
        for p in poses:
            img.alpha_composite(p, (x, row * H + 30))
            x += 44
        for i in icons:
            crop = i if i.height < 110 else i.crop((0, 0, i.width, 64 if i.width == 32 and i.height > 300 else 58))
            img.alpha_composite(crop, (x, row * H + 30))
            x += i.width + 10
    g = Gif(font)
    g.text(img, (6, 6), "Polished armor worn (idle, jump, walk); icons, gauge, Overheat, chain, Glass/Brass Container")
    img.resize((W * 2, H * 4), Image.NEAREST).save(out)
    print("wrote", out)


# ================================================================================================
# Trapper
# ================================================================================================
def scene_trapper(out, font):
    sheet = frames("Content/Jungle/NPCs/Trapper.png", 48, 52, 52, 12)
    ballf = frames("Content/Jungle/Projectiles/TrapperSpikeBall.png", 20, 20, 22, 4)
    W, H, ground = 1200, 340, 290
    bg = backdrop(W, H, ground, sky=((120, 160, 110), (60, 90, 60)), dirt=(70, 60, 40), top=(60, 120, 50))
    gif = Gif(font)
    pl = polished_player(flip=True)
    tx, tvx, tvy, ty = 820.0, 0.0, 0.0, float(ground)       # trapper bottom-centre
    px = 140.0                                             # the player walks in from the left
    state, timer, cooldown, flee_dir = "stalk", 0, 0, 1
    balls = []
    rng = random.Random(2)
    fc = 0.0
    hits = []
    for tick in range(560):
        timer += 1
        if cooldown > 0:
            cooldown -= 1
        if tick < 420:
            px += 2.4                                      # chasing
        dx = px - tx
        dist = abs(dx)
        facing = 1 if dx > 0 else -1
        if state == "flee":
            want = flee_dir * KT["FleeSpeed"]
            if dist > KT["SafeRange"] or timer >= KT["MaxFleeTicks"]:
                state, timer = ("throw" if cooldown <= 0 else "stalk"), 0
        elif state == "throw":
            want = 0.0
            if timer == KT["ThrowReleaseTick"]:
                hand = (tx + facing * 6, ty - 40 + 8)
                to = (px + rng.uniform(-24, 24), ground - 21)
                d = (to[0] - hand[0], to[1] - hand[1])
                time = max(30, min(60, abs(d[0]) / 6))
                vx = max(-10, min(10, d[0] / time))
                vy = max(-12, min(6, (d[1] - 0.5 * KT["Gravity"] * time * time) / time))
                balls.append([hand[0], hand[1], vx, vy, 0, KT["Lifetime"]])
            if timer >= KT["ThrowTicks"]:
                cooldown, state, timer = KT["ThrowCooldown"], "stalk", 0
        else:
            want = 0.0
            if dist < KT["FleeRange"]:
                flee_dir, state, timer = (1 if dx < 0 else -1), "flee", 0
            elif dist < KT["ThrowRange"] and cooldown <= 0:
                state, timer = "throw", 0
            elif dist > KT["ThrowRange"] * 0.75:
                want = facing * KT["WalkSpeed"]
        tvx = min(want, tvx + KT["Accel"]) if tvx < want else max(want, tvx - KT["Accel"])
        tx = max(60, min(W - 40, tx + tvx))
        for b in balls:
            b[3] = min(b[3] + KT["Gravity"], 12)
            b[0] += b[2]
            b[1] += b[3]
            if b[1] + 7 >= ground:
                b[1] = ground - 7
                if abs(b[3]) > 2:
                    b[3] = -b[3] * KT["Bounce"]
                else:
                    b[3] = 0.0
                b[2] *= KT["RollFriction"]
            b[4] += b[2] * 0.08
            b[5] -= 1
            if abs(b[0] - px) < 17 and abs(b[1] - (ground - 21)) < 28 and (not hits or tick - hits[-1] > 40):
                hits.append(tick)
        balls = [b for b in balls if b[5] > 0]
        # frames (Trapper.FindFrame)
        if state == "throw":
            fr = 8 if timer < 12 else (9 if timer < KT["ThrowReleaseTick"] else (10 if timer < KT["ThrowReleaseTick"] + 6 else 11))
            face = facing
        elif abs(tvx) > 0.2:
            fc = (fc + abs(tvx)) % 36
            fr = 2 + int(fc / 6) % 6
            face = 1 if tvx > 0 else -1
        else:
            fr = (tick // 20) % 2
            face = facing
        if tick % TPF == 0:
            img = bg.copy()
            d = ImageDraw.Draw(img)
            d.line([tx - KT["FleeRange"], ground + 20, tx + KT["FleeRange"], ground + 20], fill=(236, 113, 40), width=3)
            spr = sheet[fr].transpose(Image.FLIP_LEFT_RIGHT) if face == 1 else sheet[fr]
            img.alpha_composite(spr, (int(tx - 24), int(ty - 52 + 4)))
            for b in balls:
                f = int(math.floor(b[4])) % 4
                spr_b = ballf[f]
                if b[5] < KT["FadeTicks"]:
                    a = spr_b.split()[3].point(lambda v, k=b[5] / KT["FadeTicks"]: int(v * k))
                    spr_b = Image.merge("RGBA", spr_b.split()[:3] + (a,))
                img.alpha_composite(spr_b, (int(b[0] - 10), int(b[1] - 10)))
            img.alpha_composite(pl, (int(px - 20), ground - 56))
            gif.text(img, (14, 10), {"stalk": "Stalking", "throw": "Wind-up %d/%d ticks, then a lobbed spike ball" % (min(timer, KT["ThrowReleaseTick"]), KT["ThrowReleaseTick"]),
                                     "flee": "Too close (orange bar: %d tiles): it runs at %.1f px/tick" % (KT["FleeRange"] // 16, KT["FleeSpeed"])}[state], big=True)
            gif.text(img, (14, 36), "Trapper: 250 life, 35 contact; spike balls bounce, then lie on the ground %d s (fade in the last 1 s)" % (KT["Lifetime"] // 60))
            gif.push(img)
    gif.save(out)
    print("trapper: ball hits on the player at ticks", hits)


# ================================================================================================
# Trapper Chain
# ================================================================================================
def scene_chain(out, font):
    heads = frames(M + "Weapons/TrapperChainProjectile.png", 32, 28, 30, 2)
    link = load(M + "Weapons/TrapperChainLink.png")
    foe = frames("Content/Junkyard/NPCs/RustCollector.png", 40, 40, 40, 11)[0]
    W, H, ground = 760, 260, 220
    bg = backdrop(W, H, ground)
    gif = Gif(font)
    pl = polished_player()
    hand = (120.0, ground - 21.0)
    foes = [(250.0, ground - 17.0), (258.0, ground - 23.0)]       # two Rust Collectors (34x34) overlapping
    tick = 0
    pops = []                                                      # (tick, x, y) damage numbers
    log = []
    for n, aim_at in enumerate([(258.0, ground - 20.0), (258.0, ground - 20.0), (700.0, ground - 200.0)]):
        d = (aim_at[0] - hand[0], aim_at[1] - hand[1])
        ln = math.hypot(*d)
        v = (d[0] / ln * K["ThrowSpeed"], d[1] / ln * K["ThrowSpeed"])
        x, y = hand[0], hand[1]
        returning, snapped, bite_age, age = False, False, -1, 0
        bitten = set()
        hw = 11                                                    # the trap's 22x22 hitbox
        for t in range(200):
            age += 1                                               # TrapperChainProjectile.AI: Age++, bite age
            if bite_age >= 0:
                bite_age += 1
            if not returning:
                if math.hypot(x - hand[0], y - hand[1]) > K["MaxReach"]:
                    returning = True
            else:
                to = (hand[0] - x, hand[1] - y)
                dist = math.hypot(*to)
                if dist < 24:
                    break
                u = (to[0] / dist, to[1] / dist)
                v = (v[0] + (u[0] * K["ReturnSpeed"] - v[0]) * 0.25 + u[0] * K["ReturnAccel"],
                     v[1] + (u[1] * K["ReturnSpeed"] - v[1]) * 0.25 + u[1] * K["ReturnAccel"])
            x, y = x + v[0], y + v[1]
            # Projectile.Damage: one pass over every NPC; open jaws, or the tick they shut in (CanHitNPC)
            if n < 2:
                for i, (fx, fy) in enumerate(foes):
                    if i in bitten or (snapped and not 0 <= bite_age < K["BiteTicks"]):
                        continue
                    if abs(x - fx) < hw + 17 and abs(y - fy) < hw + 17:
                        bitten.add(i)
                        pops.append((tick, fx, fy - 30))
                        if not snapped:
                            snapped, returning, bite_age = True, True, 0
            if tick % TPF == 0:
                frame_img(gif, bg, foes, foe, pl, hand, ground, link, heads, (x, y), v, returning, snapped, pops, tick,
                          "Close bite: the jaws bite both overlapping enemies (each once), back fast" if n < 2
                          else "Nothing caught: it reels back at %d tiles, a slower reset" % (K["MaxReach"] // 16),
                          "%d mechanist damage, %d steam a throw; next throw when the trap is back (at least %d ticks apart)"
                          % (K["Damage"], K["Cost"], K["MinCycleTicks"]))
            tick += 1
        wait = max(2, K["MinCycleTicks"] - age)                    # OnKill: SetDummyItemTime(max(2, MinCycle - age))
        log.append((n, "bitten" if bitten else "miss", len(bitten), "round trip", age, "next throw after", age + wait))
        for t in range(wait):
            if tick % TPF == 0:
                frame_img(gif, bg, foes, foe, pl, hand, ground, link, heads, None, v, False, False, pops, tick,
                          "Trap back: this throw's cycle %d ticks" % (age + wait), "")
            tick += 1
    for t in range(45):
        if tick % TPF == 0:
            frame_img(gif, bg, foes, foe, pl, hand, ground, link, heads, None, (1, 0), False, False, pops, tick,
                      "Close bite: %d ticks a throw; a full miss: %d ticks" % (log[0][-1], log[2][-1]), "")
        tick += 1
    gif.save(out)
    for row in log:
        print("chain:", row)


def frame_img(gif, bg, foes, foe, pl, hand, ground, link, heads, at, v, returning, snapped, pops, tick, title, sub):
    img = bg.copy()
    for fx, fy in foes:
        img.alpha_composite(foe, (int(fx - 20), int(fy - 23)))
    img.alpha_composite(pl, (int(hand[0] - 20), ground - 56))
    if at is not None:
        x, y = at
        along = (x - hand[0], y - hand[1])
        length = math.hypot(*along)
        rot = math.degrees(math.atan2(along[1], along[0])) + 90
        lk = link.rotate(-rot, resample=Image.NEAREST, expand=True)
        for k in range(min(64, int(length / 10))):
            cx = hand[0] + along[0] / max(1, length) * (5 + k * 10)
            cy = hand[1] + along[1] / max(1, length) * (5 + k * 10)
            img.alpha_composite(lk, (int(cx - lk.width / 2), int(cy - lk.height / 2)))
        ang = math.atan2(v[1], v[0]) if not returning else math.atan2(-along[1], -along[0]) + math.pi
        head = heads[1 if snapped else 0]
        if math.cos(ang) < 0:
            head = head.transpose(Image.FLIP_TOP_BOTTOM)
        hr = head.rotate(-math.degrees(ang), resample=Image.NEAREST, expand=True)
        img.alpha_composite(hr, (int(x - hr.width / 2), int(y - hr.height / 2)))
    for (t0, px_, py_) in pops:
        if 0 <= tick - t0 < 40:
            gif.text(img, (int(px_) - 8, int(py_) - (tick - t0) // 2), str(K["Damage"]), fill=(236, 113, 40))
    gif.text(img, (14, 10), title, big=True)
    if sub:
        gif.text(img, (14, 36), sub)
    gif.push(img)


# ================================================================================================
# Tar glob, Rust Collector, Rust Polisher
# ================================================================================================
def scene_tar(out, font):
    globs = frames("Content/Junkyard/Projectiles/TarGlob.png", 28, 28, 30, 32)
    tar = frames("Content/Junkyard/NPCs/LivingTar.png", 32, 24, 24, 2)
    W, H, ground = 760, 300, 260
    bg = backdrop(W, H, ground, sky=((140, 130, 110), (90, 80, 70)), dirt=(60, 50, 40))
    gif = Gif(font)
    pl = polished_player(flip=True)
    src = (620.0, ground - 12.0)
    shots = []
    for tick in range(240):
        if tick % 60 == 5:
            to = (rng_x[tick // 60], ground - 21.0)
            d = (to[0] - src[0], to[1] - src[1])
            time = max(20.0, min(50.0, abs(d[0]) / 7.0))
            vx = max(-10, min(10, d[0] / time))
            vy = max(-11, min(6, (d[1] - 0.5 * KJ["Gravity"] * time * time) / time))
            shots.append([src[0], src[1] - 6, vx, vy, 0])
        for s in shots:
            s[3] = min(s[3] + KJ["Gravity"], 12)
            s[0] += s[2]
            s[1] += s[3]
            s[4] += 1
        shots = [s for s in shots if s[1] < ground - 4]
        if tick % TPF == 0:
            img = bg.copy()
            img.alpha_composite(tar[(tick // 20) % 2], (int(src[0] - 16), ground - 24 + 2))
            img.alpha_composite(pl, (120, ground - 56))
            for s in shots:
                k = int(round(math.atan2(s[3], s[2]) / (2 * math.pi) * 16)) % 16
                w = (s[4] % (KJ["TicksPerFrame"] * 2)) // KJ["TicksPerFrame"]
                g = globs[k * 2 + w]
                img.alpha_composite(g, (int(s[0] - 14), int(s[1] - 14)))
            gif.text(img, (14, 10), "Tar Glob: 16 pre-rendered headings x 2 wobbles, picked from its velocity", big=True)
            gif.text(img, (14, 36), "it rises nose-up, tips over at the top of the arc and comes down nose-first (no runtime rotation)")
            gif.push(img)
    gif.save(out)


rng_x = [140.0, 260.0, 380.0, 200.0]


def scene_collector(out, font):
    fr = frames("Content/Junkyard/NPCs/RustCollector.png", 40, 40, 40, 11)
    W, H, ground = 900, 300, 260
    bg = backdrop(W, H, ground, sky=((150, 160, 170), (100, 100, 110)))
    gif = Gif(font)
    pl = polished_player()
    x, vx, ramp, fc = 820.0, 0.0, 0.0, 0.0
    px, pvx, pvy, py = 160.0, 0.0, 0.0, float(ground)
    hit_info = None
    for tick in range(260):
        if hit_info is None:
            ramp = min(ramp + 1, KJ["RampTicks"])
            acc = KJ["BaseAccel"] + (KJ["MaxAccel"] - KJ["BaseAccel"]) * ramp / KJ["RampTicks"]
            vx = max(-KJ["MaxSpeed"], vx - acc)
            if abs((x - 17) - (px + 10)) < 4 or x - 17 <= px + 10:
                speed = abs(vx)
                kb = KJ["BaseKnockback"] + KJ["KnockbackPerSpeed"] * min(speed, KJ["MaxSpeed"])
                pvx, pvy = -kb, -kb * 7 / 9
                hit_info = (tick, speed, kb)
                vx = -2.0
        else:
            vx = min(0.0, vx + KJ["SkidDecel"])
        x += vx
        if hit_info:
            pvy = min(pvy + 0.4, 10)
            px += pvx
            py += pvy
            if py >= ground:
                py, pvy = ground, 0.0
                pvx = 0.0 if abs(pvx) < 0.2 else pvx - math.copysign(0.2, pvx)
            else:
                pvx = 0.0 if abs(pvx) <= 0.1 else pvx - math.copysign(0.1, pvx)   # no keys held in the air: runSlowdown / 2
        fc = (fc + abs(vx)) % 20
        frame = (4 if abs(vx) >= KJ["FastSpeed"] else 0) + int(fc / 5) % 4
        if tick % TPF == 0:
            img = bg.copy()
            img.alpha_composite(fr[frame], (int(x - 20), ground - 40 + 4))
            img.alpha_composite(pl, (int(px - 20), int(py) - 56))
            gif.text(img, (14, 10), "Rust Collector (0.8x a player, 34x34): rolling %.1f px/tick" % abs(vx), big=True)
            if hit_info:
                gif.text(img, (14, 36), "rammed at %.1f px/tick: knockback 4.5 + 1 x %.1f = %.1f -> thrown %.1f px/tick back, %.1f up" % (
                    hit_info[1], min(hit_info[1], KJ["MaxSpeed"]), hit_info[2], hit_info[2], hit_info[2] * 7 / 9), fill=(255, 199, 90))
            gif.push(img)
    gif.save(out)


def scene_polisher(out, font):
    sheet = load("Content/Junkyard/Tiles/RustPolisherTile.png")
    gif = Gif(font)
    for f in range(KP["Frames"] * 3):
        k = f % KP["Frames"]
        tile = Image.new("RGBA", (48, 50), (0, 0, 0, 0))
        y0 = k * KP["FrameHeight"]
        for cx in range(3):
            for (cy, h) in ((0, 16), (1, 16), (2, 18)):
                cell = sheet.crop((cx * 18, y0 + cy * 18, cx * 18 + 16, y0 + cy * 18 + h))
                tile.alpha_composite(cell, (cx * 16, cy * 16))
        img = Image.new("RGBA", (160, 110), (30, 30, 36, 255))
        img.paste((150, 180, 210, 255), (80, 0, 160, 110))
        img.alpha_composite(tile, (16, 40))
        img.alpha_composite(tile, (96, 40))
        g = img.resize((480, 330), Image.NEAREST)
        gif.text(g, (8, 6), "Rust Polisher: 6 frames x %d ticks, no steam stack" % KP["TicksPerFrame"])
        for _ in range(KP["TicksPerFrame"] // 2 or 1):
            gif.frames.append(g.convert("RGB"))
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in gif.frames]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=33, loop=0, optimize=True, disposal=1)
    print("%s: %d frames" % (out, len(gif.frames)))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-10-27")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    p = lambda name: os.path.join(args.out, args.date + "_" + name)   # noqa: E731
    jobs = [("steam", lambda: scene_steam(p("mechanist-steam.gif"), args.font)),
            ("armor", lambda: armor_png(p("mechanist-polished-armor.png"), args.font)),
            ("trapper", lambda: scene_trapper(p("jungle-trapper.gif"), args.font)),
            ("chain", lambda: scene_chain(p("weapon-trapper-chain.gif"), args.font)),
            ("tar", lambda: scene_tar(p("junkyard-tar-glob.gif"), args.font)),
            ("collector", lambda: scene_collector(p("junkyard-rust-collector.gif"), args.font)),
            ("polisher", lambda: scene_polisher(p("junkyard-rust-polisher.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
