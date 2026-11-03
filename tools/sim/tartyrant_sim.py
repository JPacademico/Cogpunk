"""D5 proofs for Tar Tyrant (Content/Bosses/TarTyrant/, reworked 2026-10-29) and the Puxa-frango (Content/Underground/),
built from the real sprite sheets, the generated rig data and the constants parsed out of the C# files, replayed tick by
tick (60 ticks = 1 s).

    python -P tools/sim/tartyrant_sim.py --out docs/media --date 2026-10-29 [--only summon,attacks,bones,melt,rage,death,sprite,hitboxes,loot,
                                                                                puxa]

Writes:
    <date>_boss-tartyrant-summon.gif    a Scrapworm on the hook in the Junkyard's tar: the bite, the reel, the boss rising
                                        out of the tar at the bobber (its rise frames), title card, roar.
    <date>_boss-tartyrant-attacks.gif   the downtime (shortened), then burp (three bubbles that drift, grow and burst into
                                        Living Tar), spit (a fan of three globs, 3-tile puddles) and summon (a row of bone
                                        spikes 6 tiles apart, each warned by its boiling patch, erupting nearest first);
                                        the flung bones keep their own 3.5 s time through all of it.
    <date>_boss-tartyrant-bones.gif     the flung bones up close (2026-10-29, in place of the femur throw): the hump heaves
                                        and boils 30 ticks (the vent overlay), bursts, three bones lobbed at the player's
                                        feet 4 tiles apart; each bounces once and shatters; every 3.5 s, enraged too.
    <date>_boss-tartyrant-melt.gif      the player runs: too far, it melts, the ground boils where the player will be in a
                                        second (its speed x 60 ticks), it rises there.
    <date>_boss-tartyrant-rage.gif      at a third of its life: growl, melt, claws out of the ground under the player ("!"
                                        and 8 tiles of boiling tar, 1.5 s to step out; claws 3 and 4 are skipped to fit
                                        10 s), it rises on the other side and roars, enraged.
    <date>_boss-tartyrant-death.gif     the death at half size (it sheds 1% per 2% of its life): recoil, last roar, the slump
                                        into the puddle, the last bubble, the bones spilling out, "Defeated".
    <date>_boss-tartyrant-sprite.png    the three planes apart and composited, and frames of every sequence, on dark and
                                        light backgrounds.
    <date>_boss-tartyrant-hitboxes.png  the hit strips (red) over frames at full size and at the 51% it ends at, and the
                                        attack hitboxes over their sprites.
    <date>_boss-tartyrant-loot.png      the Tyrant armor pieces, the Serene Tear, the treasure bag, the map head and the gores.
    (The Tyrant armor's claw set bonus and its GIF are gone since the 2026-11-03 summoner rework; the new set bonus is
    shown with the Tar Whip in tools/sim/tar_weapons_sim.py. The worn armor's GIF and PNG come from
    tools/sim/armor_preview.py.)
    <date>_underground-puxa-frango.gif  (2026-10-28, unchanged) the Puxa-frango stalking, crouching, lunging and snapping.

Leaves out: lighting, music, the camera lock (the view is fixed), real dust (simple squares), tile collision beyond a
flat floor and the pool's surface, network latency, the boss's highest-DPS targeting (one player). Downtimes are
shortened where labelled.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from update_2026_10_27_sim import consts, Gif, backdrop, polished_player, TPF  # noqa: E402
from mech_army_sim import arrays, paste, scale_rgb, with_alpha, parallax  # noqa: E402
import armor_preview as ap  # noqa: E402

D = "Content/Bosses/TarTyrant/"
RIG = D + "TarTyrantRigData.cs"
R = consts(RIG)
RA = arrays(RIG)
K = consts(RIG, D + "TarTyrant.cs", D + "TarTyrant.Attacks.cs", D + "TarTyrant.Visuals.cs")
KB = consts(RIG, D + "NPCs/TarTyrantBubble.cs")
KG = consts(D + "Projectiles/TarTyrantGlob.cs")
KP = consts(RIG, D + "Projectiles/TarTyrantPuddle.cs")
KS = consts(RIG, D + "Projectiles/TarTyrantBoneSpike.cs")
KV = consts(RIG, D + "Projectiles/TarTyrantBackBone.cs")
TABLES = arrays(D + "TarTyrant.Visuals.cs")
TABLES.update(arrays(D + "TarTyrant.Attacks.cs"))
KC = consts(RIG, D + "Projectiles/TarTyrantClaw.cs")
U = "Content/Underground/NPCs/"
RP = consts(U + "PuxaFrangoRigData.cs")
KX = consts(U + "PuxaFrangoRigData.cs", U + "PuxaFrango.cs")
EMBER = (255, 199, 90)
TAR_COL = (47, 27, 20, 255)
_cache = {}


def img(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert("RGBA") if os.path.exists(path) else None
    return _cache[path]


def cell(path, k, w, h, rows=None):
    """Frame k of a sheet of equal cells 2 px apart: one column, or columns of `rows` frames."""
    s = img(path)
    x = 0 if rows is None else k // rows * (w + 2)
    y = k * (h + 2) if rows is None else k % rows * (h + 2)
    return s.crop((x, y, x + w, y + h))


def part(layer, frame):
    t = RA[layer + "Frames"][frame * 7:frame * 7 + 7]
    page, x, y, w, h, ox, oy = t
    base = {"Body": "TarTyrant", "Glow": "TarTyrant_Glow", "Near": "TarTyrant_Near", "Far": "TarTyrant_Far"}[layer]
    sheet = img(D + base + ("" if page == 0 else "_Page%d" % page) + ".png")
    if sheet is None or w <= 0:
        return None, 0, 0
    return sheet.crop((x, y, x + w, y + h)), ox, oy


def draw_boss(dst, frame, ax, ay, flip, screen_w, scale=1.0, glow=1.0):
    """DepthLayers.DrawFrame for the four layers: origin on the anchor, 2 px below it at most, mirrored when facing right,
    scaled with nearest-neighbour (the game's point sampling) and snapped to whole pixels."""
    if frame < 0:
        return
    for layer, depth in (("Far", -1), ("Body", 0), ("Glow", 0), ("Near", 1)):
        im, ox, oy = part(layer, frame)
        if im is None:
            continue
        visible = min(im.height, oy + 2)
        if visible <= 0:
            continue
        im = im.crop((0, 0, im.width, visible))
        if layer == "Far":
            im = scale_rgb(im, 0.88)
        if layer == "Glow":
            if glow <= 0:
                continue
            im = with_alpha(im, glow)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        w = im.width
        if scale != 1.0:
            im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.NEAREST)
        sx = parallax(ax, depth, K["MaxParallax"], screen_w) if depth else 0
        left = ax - (w - ox) * scale if flip else ax - ox * scale
        paste(dst, im, round(left + sx), round(ay - oy * scale))


def point(name, frame, ax, ay, flip, scale=1.0):
    x, y = RA[name][frame * 2], RA[name][frame * 2 + 1]
    return (ax - x * scale if flip else ax + x * scale, ay + y * scale)


def strips(frame, ax, ay, flip, scale=1.0):
    out = []
    n = R["Strips"]
    for k in range(n):
        i = (frame * n + k) * 4
        x0, y0, x1, y1 = RA["Hit"][i:i + 4]
        if x1 <= x0 or y1 <= y0:
            continue
        left = ax - x1 * scale if flip else ax + x0 * scale
        out.append((int(left), int(ay + y0 * scale), int((x1 - x0) * scale), int(ay + y1 * scale) - int(ay + y0 * scale)))
    return out


def size_of(life_frac):
    steps = max(0, min(K["SizeSteps"] - 1, int((1.0 - life_frac) * K["SizeSteps"])))
    return 1.0 - K["ShrinkPerStep"] * steps


def table_frame(starts, t):
    k = 0
    for i in range(1, len(starts)):
        if t >= starts[i]:
            k = i
    return k


DEATH_TICKS = TABLES["DeathFrameTicks"]                  # read from the C# (TarTyrant.Visuals.cs)
VENT_STATES = ("Idle", "Walk", "Burp", "Spit", "Summon")   # TarTyrant.VentActive


def roar_frame(t, length):
    if t < 8:
        return R["Roar0"]
    if t < 16:
        return R["Roar0"] + 1
    if t >= length - 8:
        return R["Roar0"] + 5
    return R["Roar0"] + 2 + (t - 16) // 4 % 3


def resolve(state, t, moving=False):
    """TarTyrant.ResolveFrame, line for line (-1: under the tar)."""
    if state == "Emerge":
        return R["Rise0"] + min(R["RiseFrames"] - 1, t * R["RiseFrames"] // K["RiseTicks"]) if t < K["RiseTicks"] else roar_frame(t - K["RiseTicks"], K["RoarTicks"])
    if state == "Idle":
        return R["Move0"] + t // K["MoveFrameTicks"] % R["MoveFrames"] if moving else R["Idle0"] + t // K["IdleFrameTicks"] % R["IdleFrames"]
    if state == "Burp":
        b = K["BurpTick"]
        if t < b:
            return R["Burp0"] + min(K["BurpFrame"] - 1, t * K["BurpFrame"] // b)
        return R["Burp0"] + K["BurpFrame"] if t < b + 8 else R["Burp0"] + min(R["BurpFrames"] - 1, K["BurpFrame"] + 1 + (t - b - 8) // 7)
    if state == "Spit":
        s = K["SpitTick"]
        return R["Spit0"] + min(K["SpitFrame"] - 1, t * K["SpitFrame"] // s) if t < s else R["Spit0"] + min(R["SpitFrames"] - 1, K["SpitFrame"] + (t - s) // 6)
    if state == "Melt":
        if t < K["MeltUnderTick"]:
            return R["Melt0"] + min(R["MeltFrames"] - 1, t // K["MeltFrameTicks"])
        if t < K["MeltRiseTick"]:
            return -1
        return R["Rise0"] + min(R["RiseFrames"] - 1, (t - K["MeltRiseTick"]) // K["RiseFrameTicks"])
    if state == "Summon":
        f, p = K["SummonFieldTick"], K["SummonPlungeTick"]
        if t < f:
            return R["Summon0"] + min(3, t * 4 // f)
        if t < p:
            return R["Summon0"] + 4 + (t - f) // 4 % 2
        if t < p + 3:
            return R["Summon0"] + 6
        if t < p + 8:
            return R["Summon0"] + 7
        return R["Summon0"] + 8 if t < 110 else (R["Summon0"] + 9 if t < 124 else R["Idle0"])
    if state == "Rage":
        if t < K["RageGrowlTicks"]:
            return roar_frame(t, K["RageGrowlTicks"])
        if t < K["RageClawStart"]:
            return R["Melt0"] + min(R["MeltFrames"] - 1, (t - K["RageGrowlTicks"]) // K["MeltFrameTicks"])
        if t < K["RageRiseTick"]:
            return -1
        if t < K["RageRoarTick"]:
            return R["Rise0"] + min(R["RiseFrames"] - 1, (t - K["RageRiseTick"]) // K["RiseFrameTicks"])
        return roar_frame(t - K["RageRoarTick"], K["RoarTicks"])
    if state == "Dying":
        return R["Death0"] + table_frame(DEATH_TICKS, t)
    return R["Idle0"]


class Vent:
    """TarTyrant.UpdateVent / VentFrame, line for line: the count runs in the fighting states, the telegraph frames over
    its last VentTelegraphTicks, the burst frames for VentBurstTicks after the volley."""

    def __init__(self):
        self.timer, self.burst = 0, 0

    def step(self, state):
        """One tick; True on the tick the volley flies."""
        if self.burst > 0:
            self.burst -= 1
        if state not in VENT_STATES:
            self.timer, self.burst = 0, 0
            return False
        self.timer += 1
        if self.timer < K["VentInterval"]:
            return False
        self.timer, self.burst = 0, K["VentBurstTicks"]
        return True

    def frame(self, state):
        if state not in VENT_STATES:
            return -1
        if self.burst > 0:
            k = (K["VentBurstTicks"] - self.burst) * R["VentBurstFrames"] // K["VentBurstTicks"]
            return R["VentBurst0"] + max(0, min(R["VentBurstFrames"] - 1, k))
        t = self.timer - (K["VentInterval"] - K["VentTelegraphTicks"])
        return -1 if t < 0 else R["VentSwell0"] + max(0, min(R["VentSwellFrames"] - 1, t * R["VentSwellFrames"] // K["VentTelegraphTicks"]))


def draw_vent(dst, body_frame, k, ax, ay, flip, scale=1.0):
    """TarTyrant.DrawVent: the overlay's origin on the body frame's Vent point, mirrored and scaled with the body."""
    if k < 0 or body_frame < 0:
        return
    im = cell(D + "TarTyrant_Vent.png", k, R["VentWidth"], R["VentHeight"])
    vx, vy = RA["Vent"][body_frame * 2], RA["Vent"][body_frame * 2 + 1]
    ox = R["VentWidth"] - R["VentOriginX"] if flip else R["VentOriginX"]
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if scale != 1.0:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.NEAREST)
    x = ax + (-vx if flip else vx) * scale
    y = ay + vy * scale
    paste(dst, im, round(x - ox * scale), round(y - R["VentOriginY"] * scale))


class Bone:
    """TarTyrantBackBone: a lob under Gravity, a bounce off the floor, shattered by the next contact."""

    def __init__(self, x, y, vx, vy, kind):
        self.x, self.y, self.vx, self.vy, self.kind, self.age, self.bounces, self.dead = x, y, vx, vy, kind, 0, 0, False

    def step(self, G):
        self.age += 1
        self.vy = min(self.vy + KV["Gravity"], KV["MaxFallSpeed"])
        self.x += self.vx
        self.y += self.vy
        half = KV["HitboxSize"] / 2
        if self.y + half >= G:
            if self.bounces >= KV["MaxBounces"]:
                self.dead = True
                return "shatter"
            self.bounces += 1
            self.y = G - half
            self.vy = -self.vy * KV["BounceDamping"]
            self.vx *= KV["BounceFriction"]
            return "bounce"
        return None

    def sprite(self):
        k = self.age // KV["SpinFrameTicks"] % R["BoneTurns"]
        if self.vx < 0:
            k = (R["BoneTurns"] - k) % R["BoneTurns"]
        return cell(D + "Projectiles/TarTyrantBackBone.png", self.kind * R["BoneTurns"] + k, R["BoneCell"], R["BoneCell"])


def lob(fx, fy, tx, ty, ticks):
    """TarTyrantBackBone.LobVelocity."""
    ticks = max(10.0, ticks)
    vx = (tx - fx) / ticks
    vy = (ty - fy - 0.5 * KV["Gravity"] * ticks * ticks) / ticks
    return max(-12.0, min(12.0, vx)), max(-14.0, min(-2.0, vy))


def volley(body_frame, bx, G, flip, px, pbottom, scale=1.0, scatter=(0.0, 0.0, 0.0)):
    """TarTyrant.SpawnBackBones: VentBones bones from the Vent point at the target's feet, BoneSpread apart."""
    fx, fy = point("Vent", body_frame, bx, G, flip, scale)
    out = []
    for i in range(K["VentBones"]):
        tx = px + (i - (K["VentBones"] - 1) * 0.5) * K["BoneSpread"] + scatter[i % len(scatter)]
        ty = pbottom - 8
        ticks = max(K["BoneMinFlight"], min(K["BoneMaxFlight"], abs(tx - fx) * K["BoneFlightPerPx"]))
        vx, vy = lob(fx, fy, tx, ty, ticks)
        out.append(Bone(fx, fy, vx, vy, i % R["BoneKinds"]))
    return out


def pool_backdrop(W, H, G, pool_right):
    bg = backdrop(W, H, G)
    d = ImageDraw.Draw(bg)
    d.rectangle([0, G, pool_right, H], fill=TAR_COL)
    for y in range(G + 6, H, 10):
        for x in range((y * 7) % 23, pool_right, 23):
            d.line([x, y, x + 6, y], fill=(21, 22, 28, 255))
    for x in range(0, pool_right, 16):
        d.line([x, G, x + 7, G], fill=(79, 85, 98, 255))
    return bg


PLAYER = None


def player(flip=False):
    global PLAYER
    if PLAYER is None:
        PLAYER = polished_player()
    return PLAYER.transpose(Image.FLIP_LEFT_RIGHT) if flip else PLAYER


def draw_player(dst, cx, bottom, flip=False, hurt=False):
    im = player(flip)
    if hurt:
        im = scale_rgb(im, 0.55)                         # the Tar Plague tint
    paste(dst, im, cx - im.width / 2, bottom - im.height + 2)


def splash(d, x, y, w, t, n=6, h=30):
    for k in range(n):
        sx = x - w / 2 + ((t * 13 + k * 47) % max(1, int(w)))
        sy = y - ((t * 5 + k * 17) % h)
        d.rectangle([sx, sy, sx + 3, sy + 3], fill=TAR_COL)


class Bubble:
    def __init__(self, x, y, vx, vy, slot):
        self.x, self.y, self.vx, self.vy, self.age, self.slot = x, y, vx, vy, 0, slot

    def step(self, tx, ty, k):
        self.age += 1
        a = k * 2.4 + self.age * KB["OrbitTurn"]                 # TarTyrantBubble's own spot around the target
        tx += math.cos(a) * KB["OrbitRadius"]
        ty += (math.sin(a) * 0.6 - 0.4) * KB["OrbitRadius"]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy) or 1.0
        wx = dx / dist * KB["DriftSpeed"]
        wy = dy / dist * KB["DriftSpeed"] + math.sin(self.age * 0.07 + self.slot) * 0.4
        self.vx *= KB["LaunchDrag"]
        self.vy *= KB["LaunchDrag"]
        self.vx += (wx - self.vx) * KB["DriftAccel"]
        self.vy += (wy - self.vy) * KB["DriftAccel"]
        self.x += self.vx
        self.y += self.vy

    def frame(self):
        step = min(R["BubbleSizes"] - 1, self.age * R["BubbleSizes"] // KB["GrowTicks"])
        return step * 2 + (self.age // KB["WobbleTicks"]) % 2


class Slime:
    """A Living Tar hop (vanilla slime rhythm, simplified): falls, lands, hops towards the player now and then."""

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy, self.t = x, y, vx, vy, 0

    def step(self, G, px):
        self.t += 1
        self.vy += 0.3
        self.x += self.vx
        self.y += self.vy
        if self.y >= G:
            self.y, self.vy = G, 0.0
            self.vx *= 0.7
            if self.t % 70 == 0:
                self.vy = -5.0
                self.vx = 2.0 if px > self.x else -2.0


def draw_slime(dst, s):
    im = cell("Content/Junkyard/NPCs/LivingTar.png", 0 if s.y >= 470 - 0.5 or s.vy == 0 else 1, 32, 22)
    paste(dst, im, s.x - 16, s.y - 22)


# ================================================================================================
def scene_summon(out, font):
    W, H, G, POOL = 1000, 520, 470, 600
    gif = Gif(font)
    bg = pool_backdrop(W, H, G, POOL)
    worm = img(D + "Summon/Scrapworm.png")
    px = 760
    bobber = (420.0, G - 2.0)
    bite, reel = 45, 70
    for t in range(0, reel + K["EmergeTicks"] + 30):
        if t % TPF:
            continue
        fr = bg.copy()
        d = ImageDraw.Draw(fr)
        e = t - reel
        if e < 0:
            dip = 4 if bite <= t < reel and (t // 3) % 2 == 0 else 0
            d.line([px - 14, G - 58, bobber[0], bobber[1] + dip], fill=(195, 200, 205, 255), width=1)
            d.ellipse([bobber[0] - 3, bobber[1] - 3 + dip, bobber[0] + 3, bobber[1] + 3 + dip], fill=(236, 113, 40, 255))
            paste(fr, worm, px + 20, G - 110)
            gif.text(fr, (px + 54, G - 104), "bait: Scrapworm")
            if t >= bite:
                gif.text(fr, (bobber[0] - 20, G - 40), "a bite...", fill=EMBER)
        else:
            draw_boss(fr, resolve("Emerge", e), round(bobber[0]), G, True, W)
            if e < K["RiseTicks"]:
                splash(d, bobber[0], G, 260, e)
            if e >= K["TitleTick"]:
                gif.text(fr, (W // 2 - 90, 70), "Tar Tyrant", big=True)
                gif.text(fr, (W // 2 - 80, 96), "Monarch of the Mire", fill=(195, 200, 205))
            if K["RiseTicks"] + 16 <= e < K["RiseTicks"] + 46:
                gif.text(fr, (int(bobber[0]) - 30, 120), "ROAR", fill=EMBER, big=True)
        draw_player(fr, px, G, flip=True)
        gif.text(fr, (12, 8), "Scrapworm on the hook in the Junkyard's tar: the bite is Tar Tyrant, pulled out at the bobber")
        gif.text(fr, (12, 28), "it rises out of its puddle in %d frames over %d ticks (harmless, can't be hit), title at %d, roar" % (
            R["RiseFrames"], K["RiseTicks"], K["TitleTick"]))
        gif.push(fr, scale=0.8)
    gif.save(out)


def scene_attacks(out, font):
    W, H, G, POOL = 1100, 540, 490, 0
    gif = Gif(font)
    bg = pool_backdrop(W, H, G, POOL)
    bx, flip = 330.0, True
    px, py, pvy = 760.0, 0.0, 0.0
    bubbles, slimes, globs, puddles, spikes, bones = [], [], [], [], [], []
    vent = Vent()
    short = 30
    schedule = [("Idle", short), ("Burp", K["BurpTicks"]), ("Idle", short), ("Spit", K["SpitTicks"]), ("Idle", short),
                ("Summon", K["SummonTicks"]), ("Idle", 60)]
    seq = []
    for name, n in schedule:
        seq += [(name, t) for t in range(n)]
    for tick, (state, t) in enumerate(seq):
        f = resolve("Idle" if state == "Walk" else state, t)
        if state == "Walk":
            px -= 4.0                                       # the player walks in under its claw
        if state == "Burp" and t == K["BurpTick"]:
            mx, my = point("Mouth", R["Burp0"] + K["BurpFrame"], bx, G, flip)
            for i in range(K["Bubbles"]):
                bubbles.append(Bubble(mx, my, (1.5 + 2.2 * i), -2.5 - 1.8 * (K["Bubbles"] - 1 - i), 7 + i))
        if state == "Spit" and t == K["SpitTick"]:
            fx, fy = point("Mouth", R["Spit0"] + K["SpitFrame"], bx, G, flip)
            for i in range(K["Globs"]):
                tx = px + (i - (K["Globs"] - 1) * 0.5) * K["GlobSpread"]
                ticks = K["GlobFlightTicks"]
                vx = (tx - fx) / ticks
                vy = ((G - fy) - 0.5 * KG["Gravity"] * ticks * ticks) / ticks
                globs.append([fx, fy, vx, vy, 0])
        if state == "Summon" and t == K["SummonFieldTick"]:
            for k in range(-K["SpikeHalfCount"], K["SpikeHalfCount"] + 1):
                x = px + k * K["SpikeSpacing"]
                if -40 < x < W + 40:
                    rank = min(40, int(abs(x - bx) / K["SpikeSpacing"]))
                    spikes.append([x, K["SummonEruptTick"] - K["SummonFieldTick"] + rank * K["SpikeStagger"], 0])
        if vent.step(state):
            bones += volley(f, bx, G, flip, px, G, scatter=(-6.0, 9.0, -12.0))
        for b in bubbles:
            b.step(px, G - 21 - py, b.slot)
            if b.age >= KB["GrowTicks"]:
                slimes.append(Slime(b.x, b.y, -2.0, -2.5))
                slimes.append(Slime(b.x, b.y, 2.0, -2.5))
                b.age = -1
        bubbles = [b for b in bubbles if b.age >= 0]
        for s in slimes:
            s.step(G, px)
        for g in globs:
            g[0] += g[2]
            g[1] += g[3]
            g[3] = min(g[3] + KG["Gravity"], KG["MaxFall"])
            g[4] += 1
            if g[1] >= G - 10:
                puddles.append([g[0], 0])
                g[4] = -1
        globs = [g for g in globs if g[4] >= 0]
        for p in puddles:
            p[1] += 1
        puddles = [p for p in puddles if p[1] < KP["Lifetime"]]
        for s in spikes:
            s[2] += 1
        spikes = [s for s in spikes if s[2] < s[1] + KS["RiseTicks"] + KS["HoldTicks"] + KS["SinkTicks"]]
        for b in bones:
            b.step(G)
        bones = [b for b in bones if not b.dead]
        # the player sidesteps the bone coming up under it
        if state == "Summon" and K["SummonFieldTick"] + 6 <= t < K["SummonFieldTick"] + 22:
            px += 3.0
        if tick % TPF:
            continue
        fr = bg.copy()
        d = ImageDraw.Draw(fr)
        for p in puddles:
            paste(fr, cell(D + "Projectiles/TarTyrantPuddle.png", (p[1] // KP["TicksPerFrame"]) % KP["Frames"], R["PuddleWidth"], R["PuddleHeight"]),
                  p[0] - R["PuddleWidth"] / 2, G - R["PuddleHeight"] + 2)
        for s in spikes:
            e = s[2] - s[1]
            if e < 0:
                k = R["SpikeWarn0"] + (s[2] // KS["WarnFrameTicks"]) % R["SpikeWarnFrames"]
            elif e < KS["RiseTicks"]:
                k = R["SpikeRise0"] + min(R["SpikeRiseFrames"] - 1, e // KS["RiseFrameTicks"])
            elif e < KS["RiseTicks"] + KS["HoldTicks"]:
                k = R["SpikeHold0"] + (e - KS["RiseTicks"]) // KS["HoldFrameTicks"] % R["SpikeHoldFrames"]
            else:
                k = R["SpikeSink0"] + min(R["SpikeSinkFrames"] - 1, (e - KS["RiseTicks"] - KS["HoldTicks"]) // KS["SinkFrameTicks"])
            paste(fr, cell(D + "Projectiles/TarTyrantBoneSpike.png", k, R["SpikeWidth"], R["SpikeHeight"]), s[0] - R["SpikeWidth"] / 2, G - R["SpikeHeight"] + 2)
        draw_boss(fr, f, round(bx), G, flip, W)
        draw_vent(fr, f, vent.frame(state), round(bx), G, flip)
        for b in bones:
            paste(fr, b.sprite(), round(b.x - R["BoneCell"] / 2), round(b.y - R["BoneCell"] / 2))
        for b in bubbles:
            paste(fr, cell(D + "NPCs/TarTyrantBubble.png", b.frame(), R["BubbleCell"], R["BubbleCell"]), b.x - R["BubbleCell"] / 2, b.y - R["BubbleCell"] / 2)
            gif.text(fr, (int(b.x) - 12, int(b.y) - 44), "%.1f" % ((KB["GrowTicks"] - b.age) / 60.0), fill=EMBER)
        for s in slimes:
            draw_slime(fr, s)
        for g in globs:
            paste(fr, cell(D + "Projectiles/TarTyrantGlob.png", (g[4] // 5) % 3, 28, 28), g[0] - 14, g[1] - 14)
        draw_player(fr, px, G - py, flip=px < bx)
        labels = {"Idle": "downtime: %.1f s between attacks (shortened here)" % (K["DowntimeTicks"] / 60.0),
                  "Walk": "the player walks in close...",
                  "Burp": "Burp: %d-tick swell, %d bubbles; each bursts into %d Living Tar after %.0f s unless popped (%d life)" % (
                      K["BurpTick"], K["Bubbles"], KB["SlimesPerBurst"], KB["GrowTicks"] / 60.0, KB["Life"]),
                  "Spit": "Spit: %d-tick rear-back, a fan of %d globs %d tiles apart; tar stays %.0f s (3 tiles, Tar Plague 1 s)" % (
                      K["SpitTick"], K["Globs"], K["GlobSpread"] // 16, KP["Lifetime"] / 60.0),
                  "Summon": "Summon: claw up, tar boils every %d tiles across the screen (%d+ ticks), bones erupt nearest first" % (
                      K["SpikeSpacing"] // 16, K["SummonEruptTick"] - K["SummonFieldTick"])}
        gif.text(fr, (12, 8), labels[state], big=True)
        gif.text(fr, (12, 34), "Expert: glob %d, bone spike %d, flung bone %d, bubble %d contact, body %d contact; every hit: Tar Plague %.0f s" % (
            K["GlobDamage"], K["SpikeDamage"], K["BackBoneDamage"], KB["ContactDamage"], K["ExpertContactDamage"], K["PlagueTicks"] / 60.0))
        gif.text(fr, (12, 54), "and on its own time: bones out of its back every %.1f s (next in %.1f s)" % (
            K["VentInterval"] / 60.0, (K["VentInterval"] - vent.timer) / 60.0), fill=EMBER)
        gif.push(fr, scale=0.82)
    gif.save(out)


def scene_bones(out, font):
    """The flung bones up close: two volleys while it idles (the count kept through an attack in game), the second while
    enraged at a third of its life (the same 3.5 s, drawn at its size then). The player stands, then steps back."""
    W, H, G = 1200, 520, 470
    gif = Gif(font)
    bg = pool_backdrop(W, H, G, 0)
    bx, flip = 300.0, True
    px = 720.0
    vent = Vent()
    vent.timer = K["VentInterval"] - K["VentTelegraphTicks"] - 20
    bones, pops, chips = [], [], []
    hurt = -99
    total = 2 * K["VentInterval"] + 90
    for tick in range(total):
        enraged = tick >= K["VentInterval"] + 40
        scale = size_of(0.33) if enraged else 1.0
        f = resolve("Idle", tick)
        if vent.step("Idle"):
            bones += volley(f, bx, G, flip, px, G, scale, scatter=(-6.0, 9.0, -12.0) if not enraged else (10.0, -4.0, 7.0))
        for b in bones:
            ev = b.step(G)
            if ev == "shatter":
                chips.append([b.x, G - 6, 0])
            if tick - hurt > 40 and abs(b.x - px) < 10 + KV["HitboxSize"] / 2 and G - 42 - KV["HitboxSize"] / 2 < b.y < G + KV["HitboxSize"] / 2:
                hurt = tick
                pops.append([px, G - 70, 0, "%d + Tar Plague" % K["BackBoneDamage"]])
        bones = [b for b in bones if not b.dead]
        chips = [[x, y, a + 1] for x, y, a in chips if a < 16]
        pops = [[a, b2 - 0.6, c + 1, s] for a, b2, c, s in pops if c < 50]
        if tick > K["VentInterval"] + 60 and tick < K["VentInterval"] + 110:
            px += 2.0                                           # the player backs off before the next one
        if tick % TPF:
            continue
        fr = bg.copy()
        d = ImageDraw.Draw(fr)
        draw_boss(fr, f, round(bx), G, flip, W, scale=scale)
        draw_vent(fr, f, vent.frame("Idle"), round(bx), G, flip, scale)
        for b in bones:
            paste(fr, b.sprite(), round(b.x - R["BoneCell"] / 2), round(b.y - R["BoneCell"] / 2))
        for x, y, a in chips:
            for k in range(4):
                cx = x + (k - 1.5) * (2 + a * 0.6)
                cy = y - 6 * math.sin(min(1.0, a / 8.0) * math.pi) - k % 2 * 2 + a * 0.4
                d.rectangle([cx, cy, cx + 3, cy + 3], fill=(195, 200, 205, 255))
        draw_player(fr, px, G, flip=px < bx, hurt=0 <= tick - hurt < 40)
        for a, b2, c, s in pops:
            gif.text(fr, (int(a) - 40, int(b2)), s, fill=EMBER, big=True)
        t = vent.timer - (K["VentInterval"] - K["VentTelegraphTicks"])
        if 0 <= t < K["VentTelegraphTicks"]:
            vx, vy = point("Vent", f, bx, G, flip, scale)
            gif.text(fr, (int(vx) - 40, int(vy) - 70), "it heaves: %.2f s" % ((K["VentTelegraphTicks"] - t) / 60.0), fill=EMBER, big=True)
        gif.text(fr, (12, 8), "Flung bones%s: every %.1f s its hump heaves and boils %d ticks, then %d bones fly out at the player's feet" % (
            " (enraged: a third of its life, %d%% size)" % round(scale * 100) if enraged else "", K["VentInterval"] / 60.0, K["VentTelegraphTicks"],
            K["VentBones"]), big=True)
        gif.text(fr, (12, 34), "%d tiles apart, a high lob (%d-%d ticks); each bounces once and shatters on the next contact; %d damage + Tar Plague 1 s (Expert)" % (
            K["BoneSpread"] // 16, K["BoneMinFlight"], K["BoneMaxFlight"], K["BackBoneDamage"]))
        gif.push(fr, scale=0.8)
    gif.save(out)


TYRANT_PLAYER = None


def tyrant_player(flip=False):
    global TYRANT_PLAYER
    if TYRANT_PLAYER is None:
        a = D + "Armor/"
        h = ap.load_frames(a + "TyrantSkull_Head.png", 1)[0]
        b = ap.load_frames(a + "TyrantCape_Body.png", 1)[0]
        leg = ap.load_frames(a + "TyrantSandals_Legs.png", 1)[0]
        back = Image.open(a + "TyrantCape_Back.png").convert("RGBA")
        TYRANT_PLAYER = ap.compose(h, b, leg, 0, [0] * 20, back=back, skin=True)   # the cape behind, bare skin (stand-in)
    return TYRANT_PLAYER.transpose(Image.FLIP_LEFT_RIGHT) if flip else TYRANT_PLAYER


def scene_melt(out, font):
    W, H, G = 1500, 470, 430
    gif = Gif(font)
    bg = pool_backdrop(W, H, G, 0)
    bx, flip = 200.0, True
    px, vx = 880.0, 3.0
    dest = None
    seq = [("Idle", t) for t in range(30)] + [("Melt", t) for t in range(K["MeltTicks"])] + [("Idle", t) for t in range(30)]
    hurt = 0
    for tick, (state, t) in enumerate(seq):
        f = resolve(state, t)
        if state == "Melt":
            if t == K["MeltUnderTick"]:
                dest = px + max(-K["MaxLead"], min(K["MaxLead"], vx * K["MeltLeadTicks"]))
            if t == K["MeltRiseTick"]:
                bx = dest
                flip = px > bx
            if t >= K["MeltRiseTick"] + K["RiseSolidTick"] and hurt == 0:
                for (x, y, w, h) in strips(f, bx, G, flip):
                    if x < px + 10 and px - 10 < x + w:
                        hurt = 1
        if hurt == 0:
            px += vx
        elif hurt < 40:
            hurt += 1
            px += 6 if px > bx else -6
        if tick % TPF:
            continue
        fr = bg.copy()
        d = ImageDraw.Draw(fr)
        if state == "Melt" and K["MeltUnderTick"] <= t < K["MeltRiseTick"] and dest is not None:
            k = R["ClawWarn0"] + (tick // 6) % R["ClawWarnFrames"]
            paste(fr, cell(D + "Projectiles/TarTyrantClaw.png", k, R["ClawWidth"], R["ClawHeight"], R["ClawRows"]), dest - R["ClawWidth"] / 2, G - R["ClawHeight"] + 2)
            splash(d, dest, G, 120, tick, 5, 20)
            gif.text(fr, (int(dest) - 90, G - 90), "it rises here in %.2f s" % ((K["MeltRiseTick"] - t) / 60.0), fill=EMBER, big=True)
            d.line([px, G - 70, dest, G - 70], fill=EMBER + (255,), width=2)
            gif.text(fr, (int(px) - 40, G - 100), "speed x 60 ticks", fill=EMBER)
        draw_boss(fr, f, round(bx), G, flip, W)
        draw_player(fr, px, G, flip=False, hurt=0 < hurt)
        if 0 < hurt < 40:
            gif.text(fr, (int(px) - 20, G - 120), "%d + Tar Plague" % K["ExpertContactDamage"], fill=EMBER, big=True)
        label = "the target runs: %d+ tiles away (or out of reach %.0f s), it melts into the ground" % (K["FarRange"] // 16, K["OutOfReachTicks"] / 60.0)
        if state == "Melt" and t >= K["MeltUnderTick"]:
            label = "under the tar %.0f s: the ground boils where the player will be; it rises there" % (K["MeltUnderTicks"] / 60.0)
        gif.text(fr, (12, 8), "Melt: " + label, big=True)
        gif.text(fr, (12, 34), "the rise hurts from its 4th frame (bones out): contact %d in Expert; untouchable while under" % K["ExpertContactDamage"])
        gif.push(fr, scale=0.6)
    gif.save(out)


def scene_tail(out, font):
    """2026-10-30 fix (user): the strands of tar up its back are gone; a short tail lies on the pool and drags behind the
    ooze. At game scale over a cavern and a sky backdrop: idle, ooze left at OozeSpeed (the Move frames, 6 ticks each),
    turn, ooze back, idle."""
    W, H, G = 640, 330, 292
    gif = Gif(font)
    dark = pool_backdrop(W, H, G, W)
    d = ImageDraw.Draw(dark)
    d.rectangle([0, 0, W, G - 1], fill=(36, 40, 48, 255))
    light = pool_backdrop(W, H, G, W)
    seq = [("idle", t) for t in range(64)] + [("left", t) for t in range(150)] + [("idle", t) for t in range(24)] + \
          [("right", t) for t in range(150)] + [("idle", t) for t in range(40)]
    bx = 430.0
    for tick, (mode, t) in enumerate(seq):
        moving = mode != "idle"
        if mode == "left":
            bx -= K["OozeSpeed"]
        elif mode == "right":
            bx += K["OozeSpeed"]
        flip = mode == "right" or (mode == "idle" and tick > 64 + 150 + 24 + 150)
        f = resolve("Idle", t, moving=moving)
        if tick % TPF:
            continue
        frames_ = []
        for bg, label in ((dark, "cavern"), (light, "sky")):
            fr = bg.copy()
            draw_boss(fr, f, round(bx), G, flip, W)
            gif.text(fr, (10, 6), "2026-10-30 fix: no strands up its back, a short tail on the pool", big=True)
            gif.text(fr, (10, 30), "%s  |  %s frame %d  |  ooze %.1f px/tick (OozeSpeed)" % (
                label, "Move" if moving else "Idle", (f - R["Move0"]) if moving else (f - R["Idle0"]), K["OozeSpeed"]))
            frames_.append(fr)
        both = Image.new("RGBA", (W, H * 2))
        both.alpha_composite(frames_[0], (0, 0))
        both.alpha_composite(frames_[1], (0, H))
        gif.push(both)
    gif.save(out)


def scene_rage(out, font):
    W, H, G = 1300, 520, 480
    gif = Gif(font)
    bg = pool_backdrop(W, H, G, 0)
    bx, flip = 360.0, True
    px = 820.0
    side = 1 if bx > px else -1
    dist = max(K["RageMinDistance"], min(K["RageMaxDistance"], abs(bx - px)))
    claws = []
    dest = None
    keep = set(range(0, K["RageClawStart"] + 2 * K["ClawEvery"])) | set(range(K["RageClawStart"] + 4 * K["ClawEvery"], K["RageTicks"] + 30))
    cx_target = [0.0]
    dodge = 0.0
    for t in range(0, K["RageTicks"] + 6):
        state = "Rage" if t < K["RageTicks"] else "Idle"
        f = resolve(state, t if state == "Rage" else t - K["RageTicks"])
        if K["RageClawStart"] <= t < K["RageRiseTick"] and (t - K["RageClawStart"]) % K["ClawEvery"] == 0:
            claws.append([px, 0])
            cx_target[0] = px
            dodge = 1.0 if (len(claws) % 2) else -1.0
        if t == K["RagePickTick"]:
            dest = px - side * dist
        if t == K["RageRiseTick"]:
            bx = dest
            flip = px > bx
        for c in claws:
            c[1] += 1
            age = c[1]
            if 24 <= age < 24 + 26:                         # the player reads the "!" and steps out of the 8 tiles
                px += 3.0 * dodge
        claws = [c for c in claws if c[1] < KC["Lifetime"]]
        if t not in keep or t % TPF:
            continue
        fr = bg.copy()
        for c in claws:
            age = c[1]
            if age < KC["WarnTicks"]:
                k = R["ClawWarn0"] + min(R["ClawWarnFrames"] - 1, age * R["ClawWarnFrames"] // KC["WarnTicks"])
            else:
                e = age - KC["WarnTicks"]
                if e < KC["RiseTicks"]:
                    k = R["ClawRise0"] + min(R["ClawRiseFrames"] - 1, e // KC["RiseFrameTicks"])
                elif e < KC["RiseTicks"] + KC["GrabTicks"]:
                    k = R["ClawGrab0"] + min(R["ClawGrabFrames"] - 1, (e - KC["RiseTicks"]) // KC["GrabFrameTicks"])
                else:
                    k = R["ClawSink0"] + min(R["ClawSinkFrames"] - 1, (e - KC["RiseTicks"] - KC["GrabTicks"]) // KC["SinkFrameTicks"])
            paste(fr, cell(D + "Projectiles/TarTyrantClaw.png", k, R["ClawWidth"], R["ClawHeight"], R["ClawRows"]), c[0] - R["ClawWidth"] / 2, G - R["ClawHeight"] + 2)
            if age < KC["WarnTicks"]:
                sign = cell(D + "Projectiles/TarTyrantClaw_Warning.png", age // 4 % 4, R["WarnWidth"], R["WarnHeight"])
                bob = round(math.sin(age * 0.2) * 2) * 2
                paste(fr, sign, c[0] - R["WarnWidth"] / 2, G - KC["SignHeight"] - R["WarnHeight"] + bob)
                gif.text(fr, (int(c[0]) - 40, G - 150), "%.2f s" % ((KC["WarnTicks"] - age) / 60.0), fill=EMBER)
        if t < K["RageRiseTick"] and t >= K["RagePickTick"] and dest is not None:
            paste(fr, cell(D + "Projectiles/TarTyrantClaw.png", R["ClawWarn0"] + (t // 6) % 4, R["ClawWidth"], R["ClawHeight"], R["ClawRows"]), dest - R["ClawWidth"] / 2,
                  G - R["ClawHeight"] + 2)
        draw_boss(fr, f, round(bx), G, flip, W, scale=size_of(0.33))
        draw_player(fr, px, G, flip=px > bx)
        n = sum(1 for c0 in range(K["RageClaws"]) if t >= K["RageClawStart"] + c0 * K["ClawEvery"])
        if t < K["RageGrowlTicks"]:
            label = "a third of its life gone: it growls (untouchable from here to the roar)"
        elif t < K["RageClawStart"]:
            label = "it melts away..."
        elif t < K["RageRiseTick"]:
            label = "claw %d of %d: \"!\" + 8 tiles of boiling tar, %.1f s to get out; %d damage%s" % (
                n, K["RageClaws"], KC["WarnTicks"] / 60.0, K["ClawDamage"], "  (claws 3-4 skipped here)" if n >= 5 else "")
        elif t < K["RageRoarTick"]:
            label = "it rises on the other side of the player"
        else:
            label = "ENRAGED: %.1f s between attacks from now on" % (K["EnragedDowntimeTicks"] / 60.0)
        gif.text(fr, (12, 8), "Rage: " + label, big=True)
        gif.text(fr, (12, 34), "a claw every %.0f s, %d times; it comes back %d-%d tiles away on the far side (Expert numbers)" % (
            K["ClawEvery"] / 60.0, K["RageClaws"], K["RageMinDistance"] // 16, K["RageMaxDistance"] // 16))
        gif.push(fr, scale=0.75)
    gif.save(out)


def scene_death(out, font):
    W, H, G, POOL = 820, 420, 380, 820
    gif = Gif(font)
    bg = pool_backdrop(W, H, G, POOL)
    scale = size_of(0.0)
    gores = []
    names = ("Skull", "Jaw", "Horn", "Claw", "Rib", "Rib", "Femur", "Vertebra")
    for t in range(0, K["DeathTicks"] + 50):
        f = resolve("Dying", min(t, K["DeathTicks"] - 1))
        if t == K["DeathSinkTick"]:
            for k, n in enumerate(names):
                g = img(D + "Gores/TarTyrant_Gore%s.png" % n)
                g = g.resize((max(1, round(g.width * scale)), max(1, round(g.height * scale))), Image.NEAREST)   # gores at its size
                gores.append([W / 2 + (k - 3.5) * 22 * scale * 2, G - 24, (k - 3.5) * 0.7, -3.5 - (k % 3), g])
        for g in gores:
            g[0] += g[2]
            g[1] += g[3]
            g[3] += 0.25
            if g[1] > G - g[4].height * 0.5:
                g[1] = G - g[4].height * 0.5
                g[2] *= 0.8
                g[3] = 0.0
        if t % TPF:
            continue
        fr = bg.copy()
        if t < K["DeathTicks"]:
            draw_boss(fr, f, W // 2, G, False, W, scale=scale)
        for g in gores:
            paste(fr, g[4], g[0] - g[4].width / 2, g[1] - g[4].height / 2)
        if t >= K["DeathCardTick"]:
            gif.text(fr, (W // 2 - 70, 70), "Tar Tyrant", big=True)
            gif.text(fr, (W // 2 - 40, 96), "Defeated", fill=(195, 200, 205))
        gif.text(fr, (12, 8), "Death (%d ticks, camera locked in game), at %d%% size: recoil, last roar, its bones work loose (the femur slides" % (
            K["DeathTicks"], round(scale * 100)))
        gif.text(fr, (12, 28), "out of its back and topples off), the slump, the settling, the last bubble; then the tar lets go of its bones")
        gif.text(fr, (12, 48), "(gores at %d); %d frames, no snaps" % (K["DeathSinkTick"], R["DeathFrames"]))
        gif.push(fr)
    gif.save(out)


def sprite_png(out, font):
    names = [("Far", R["Idle0"]), ("Body", R["Idle0"]), ("Near", R["Idle0"])]
    seqs = ["Idle", "Move", "Burp", "Spit", "Melt", "Rise", "Summon", "Roar", "Death"]
    cw, ch = 330, 300
    cols = 8
    rows = 1 + len(seqs)
    out_img = Image.new("RGBA", (cw * cols, ch * rows * 2), (0, 0, 0, 255))
    gif = Gif(font)
    for half, bgc in enumerate(((30, 30, 36), (150, 190, 230))):
        im = Image.new("RGBA", (cw * cols, ch * rows), bgc + (255,))
        for k, (layer, fr) in enumerate(names):
            p, ox, oy = part(layer, fr)
            ax, ay = k * cw + cw // 2, ch - 12
            paste(im, p if layer != "Far" else scale_rgb(p, 0.88), ax - ox, ay - oy)
            gif.text(im, (k * cw + 8, 6), layer)
        draw_boss(im, R["Idle0"], 3 * cw + cw // 2 + 40, ch - 12, False, 1 << 30)
        gif.text(im, (3 * cw + 8, 6), "composited")
        draw_boss(im, R["Idle0"], 5 * cw + cw // 2, ch - 12, False, 1 << 30, scale=0.75)
        gif.text(im, (5 * cw + 8, 6), "75% (half its life)")
        draw_boss(im, R["Idle0"], 6 * cw + cw // 2 + 20, ch - 12, False, 1 << 30, scale=size_of(0.0))
        gif.text(im, (6 * cw + 8, 6), "51% (the end)")
        for r, name in enumerate(seqs):
            first, count = R[name + "0"], R[name + "Frames"]
            picks = [first + round(j * (count - 1) / max(1, min(cols, count) - 1)) for j in range(min(cols, count))]
            for j, fr in enumerate(picks):
                draw_boss(im, fr, j * cw + cw // 2 + 20, (r + 1) * ch + ch - 12, False, 1 << 30)
            gif.text(im, (8, (r + 1) * ch + 6), "%s (%d frames)" % (name, count))
        out_img.paste(im, (0, half * ch * rows))
    out_img = out_img.resize((out_img.width // 2, out_img.height // 2), Image.NEAREST)
    out_img.save(out)
    print(out, out_img.size)


def hitbox_png(out, font):
    gif = Gif(font)
    frames = [R["Idle0"], R["Burp0"] + 5, R["Summon0"] + 3, R["Roar0"] + 2, R["Rise0"] + 4, R["Death0"] + 16]
    cw, ch = 520, 360
    im = Image.new("RGBA", (cw * 3, ch * 3), (30, 30, 36, 255))
    d = ImageDraw.Draw(im)
    for k, fr in enumerate(frames):
        for col, scale in ((0, 1.0), (1, size_of(0.0))):
            if col == 1 and k >= 3:
                continue
            x0 = (k % 3) * cw if col == 0 else (k % 3) * cw
            y0 = (k // 3) * ch if col == 0 else 2 * ch
            ax, ay = x0 + cw // 2 + 40, y0 + ch - 14
            draw_boss(im, fr, ax, ay, False, 1 << 30, scale=scale)
            for (x, y, w, h) in strips(fr, ax, ay, False, scale):
                d.rectangle([x, y, x + w - 1, y + h - 1], outline=(255, 40, 40, 255))
            gif.text(im, (x0 + 8, y0 + 6), "frame %d at %d%%" % (fr, round(scale * 100)))
    im.save(out)
    print(out, im.size)
    # the attacks' own hitboxes over their sprites
    W = 900
    att = Image.new("RGBA", (W, 260), (30, 30, 36, 255))
    d = ImageDraw.Draw(att)
    G = 240
    spike = cell(D + "Projectiles/TarTyrantBoneSpike.png", R["SpikeHold0"], R["SpikeWidth"], R["SpikeHeight"])
    paste(att, spike, 60 - R["SpikeWidth"] / 2, G - R["SpikeHeight"] + 2)
    d.rectangle([60 - KS["HitboxWidth"] / 2, G - KS["HitboxHeight"], 60 + KS["HitboxWidth"] / 2 - 1, G - 1], outline=(255, 40, 40, 255))
    claw = cell(D + "Projectiles/TarTyrantClaw.png", R["ClawGrab0"], R["ClawWidth"], R["ClawHeight"], R["ClawRows"])
    paste(att, claw, 260 - R["ClawWidth"] / 2, G - R["ClawHeight"] + 2)
    d.rectangle([260 - KC["HitboxWidth"] / 2, G - KC["HitboxHeight"], 260 + KC["HitboxWidth"] / 2 - 1, G - 1], outline=(255, 40, 40, 255))
    for j in range(4):                                       # the flung bones: an 18 px box round each (two kinds, two turns)
        bone = cell(D + "Projectiles/TarTyrantBackBone.png", (j // 2) * R["BoneTurns"] + (j % 2) * 2, R["BoneCell"], R["BoneCell"])
        cx, cy = 420 + j * 50, 150
        paste(att, bone, cx - R["BoneCell"] / 2, cy - R["BoneCell"] / 2)
        h = KV["HitboxSize"] / 2
        d.rectangle([cx - h, cy - h, cx + h - 1, cy + h - 1], outline=(255, 40, 40, 255))
    pud = cell(D + "Projectiles/TarTyrantPuddle.png", 0, R["PuddleWidth"], R["PuddleHeight"])
    paste(att, pud, 650 - R["PuddleWidth"] / 2, G - R["PuddleHeight"] + 2)
    d.rectangle([650 - KP["HitboxWidth"] / 2, G - KP["HitboxHeight"], 650 + KP["HitboxWidth"] / 2 - 1, G - 1], outline=(255, 200, 40, 255))
    for k, step in enumerate((0, 6)):
        bub = cell(D + "NPCs/TarTyrantBubble.png", step * 2, R["BubbleCell"], R["BubbleCell"])
        cx, cy = 780 + k * 70, 150
        paste(att, bub, cx - R["BubbleCell"] / 2, cy - R["BubbleCell"] / 2)
        dia = int(RA["BubbleRadius"][step] * 2 * 0.85)
        d.rectangle([cx - dia / 2, cy - dia / 2, cx + dia / 2 - 1, cy + dia / 2 - 1], outline=(255, 40, 40, 255))
    gif.text(att, (8, 6), "attack hitboxes (red; yellow: the puddle's Tar Plague area): spike, claw (8 tiles), flung bones, puddle (3 tiles), bubble small/burst")
    base, ext = os.path.splitext(out)
    att.save(base + "-attacks" + ext)
    print(base + "-attacks" + ext, att.size)


def loot_png(out, font):
    gif = Gif(font)
    items = [D + "Armor/TyrantSkull.png", D + "Armor/TyrantCape.png", D + "Armor/TyrantSandals.png", D + "Items/SereneTear.png",
             D + "Items/TarTyrantBag.png", D + "TarTyrant_Head_Boss.png"]
    gores = [D + "Gores/TarTyrant_Gore%s.png" % n for n in ("Skull", "Jaw", "Horn", "Claw", "Rib", "Femur", "Vertebra")]
    W, H = 820, 300
    im = Image.new("RGBA", (W, H * 2), (0, 0, 0, 255))
    for half, bgc in enumerate(((30, 30, 36), (150, 190, 230))):
        panel = Image.new("RGBA", (W, H), bgc + (255,))
        x = 16
        for p in items:
            s = img(p)
            big = s.resize((s.width * 3, s.height * 3), Image.NEAREST)
            paste(panel, big, x, 40)
            x += big.width + 24
        x = 16
        for p in gores:
            s = img(p)
            paste(panel, s, x, 200 - s.height // 2)
            x += s.width + 14
        gif.text(panel, (16, 8), "Tyrant Skull / Cape / Sandals (at least one a kill), Serene Tear (Expert), treasure bag, map head (x3); gores")
        im.paste(panel, (0, half * H))
    im.save(out)
    print(out, im.size)


def scene_puxa(out, font):
    W, H, G = 900, 300, 268
    gif = Gif(font)
    bg = backdrop(W, H, G, sky=((60, 56, 70), (36, 34, 44)), dirt=(79, 85, 98), top=(127, 135, 148))
    cw, chh, ox, oy, pad = RP["CellWidth"], RP["CellHeight"], RP["OriginX"], RP["OriginY"], 2
    sheets = [U + "PuxaFrango_Far.png", U + "PuxaFrango.png", U + "PuxaFrango_Near.png"]
    x, vx, y, vy = 120.0, 0.0, 0.0, 0.0
    px, pvx, py, pvy = 640.0, 0.0, 0.0, 0.0
    state, timer, cooldown, fc = "stalk", 0, 0, 0.0
    pops = []
    for tick in range(1, 9 * 60):
        timer += 1
        if cooldown > 0:
            cooldown -= 1
        dx = px - x
        d = 1 if dx >= 0 else -1
        if state == "stalk":
            want = d * KX["StalkSpeed"]
            vx += max(-KX["StalkAccel"], min(KX["StalkAccel"], want - vx))
            if cooldown <= 0 and KX["LungeMinRange"] <= abs(dx) <= KX["LungeRange"]:
                state, timer = "crouch", 0
        elif state == "crouch":
            vx *= 0.8
            if timer >= KX["CrouchTicks"]:
                vx, vy = d * KX["LungeSpeedX"], KX["LungeSpeedY"]
                state, timer = "lunge", 0
        elif state == "lunge":
            if (timer > 6 and y <= 0) or timer >= KX["LungeMaxTicks"]:
                cooldown = KX["LungeCooldown"]
                state, timer = "recover", 0
        elif state == "recover":
            vx *= 0.85
            if timer >= KX["RecoverTicks"]:
                state, timer = "stalk", 0
        if y > 0 or vy > 0:
            y += vy
            vy -= 0.3
            if y <= 0:
                y, vy = 0.0, 0.0
        x += vx
        fc += abs(vx)
        if state == "lunge" and abs(px - x) < 40 and py < 30 and not any(p[3] == "snap" for p in pops):
            k = KX["YankKnockback"]
            pvx = (1 if x > px else -1) * k
            pvy, py = k * 0.6, 0.01
            pops.append([px, G - 70, 0, "snap"])
            pops.append([px, G - 90, 0, "%d" % round(KX["ContactDamage"] * KX["SnapDamageMultiplier"])])
        if py > 0:
            py += pvy
            pvy -= 0.4
            if py <= 0:
                py, pvy = 0.0, 0.0
            pvx *= 0.97
        else:
            pvx *= 0.8
            if state == "stalk" and tick > 300:
                pvx = 1.5
        px = max(20.0, min(W - 20.0, px + pvx))
        pops = [[a, b - 0.5, c + 1, s] for a, b, c, s in pops if c < 50]
        if tick % TPF:
            continue
        if state == "crouch":
            fr = RP["Crouch"]
        elif state == "lunge":
            fr = RP["Lunge"] if timer < KX["SnapTick"] else RP["Snap"]
        elif state == "recover":
            fr = RP["Idle"]
        elif y > 0:
            fr = RP["Air"]
        elif abs(vx) > 0.25:
            fr = int(RP["Walk"] + (fc / RP["WalkStep"]) % RP["WalkFrames"])
        else:
            fr = RP["Idle"]
        frame_img = bg.copy()
        flip = vx > 0.15 or (abs(vx) <= 0.15 and dx > 0)
        for k, s in enumerate(sheets):
            sh = img(s)
            im = sh.crop((0, fr * (chh + pad), cw, fr * (chh + pad) + chh))
            if k == 0:
                im = scale_rgb(im, 0.88)
            if flip:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            paste(frame_img, im, round(x) - (cw - ox if flip else ox), G - round(y) - oy)
        draw_player(frame_img, px, G - py, flip=px > x)
        for a, b, c, s in pops:
            gif.text(frame_img, (int(a) - 14, int(b)), s, fill=EMBER, big=True)
        labels = {"stalk": "stalking (%.1f px/tick)" % KX["StalkSpeed"], "crouch": "crouch: the telegraph (%d ticks, claws open)" % KX["CrouchTicks"],
                  "lunge": "lunge and SNAP: the hit pulls you in", "recover": "recover, %d-tick cooldown" % KX["LungeCooldown"]}
        gif.text(frame_img, (12, 8), "Puxa-frango: " + labels[state], big=True)
        gif.text(frame_img, (12, 34), "Expert: %d life, %d contact, snap x%.1f with a yank towards it; drops the Chicken Snapper 1 in %d" % (
            KX["Life"], KX["ContactDamage"], KX["SnapDamageMultiplier"], KX["SnapperOdds"]))
        gif.push(frame_img)
    gif.save(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-10-30")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    p = lambda name: os.path.join(args.out, args.date + "_" + name)   # noqa: E731
    jobs = [("summon", lambda: scene_summon(p("boss-tartyrant-summon.gif"), args.font)),
            ("attacks", lambda: scene_attacks(p("boss-tartyrant-attacks.gif"), args.font)),
            ("bones", lambda: scene_bones(p("boss-tartyrant-bones.gif"), args.font)),
            ("melt", lambda: scene_melt(p("boss-tartyrant-melt.gif"), args.font)),
            ("tail", lambda: scene_tail(p("boss-tartyrant-tail-fix.gif"), args.font)),
            ("rage", lambda: scene_rage(p("boss-tartyrant-rage.gif"), args.font)),
            ("death", lambda: scene_death(p("boss-tartyrant-death.gif"), args.font)),
            ("sprite", lambda: sprite_png(p("boss-tartyrant-sprite.png"), args.font)),
            ("hitboxes", lambda: hitbox_png(p("boss-tartyrant-hitboxes.png"), args.font)),
            ("loot", lambda: loot_png(p("boss-tartyrant-loot.png"), args.font)),
            ("puxa", lambda: scene_puxa(p("underground-puxa-frango.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
