"""D5 proofs for Trash-Tr0m (Content/Bosses/TrashTr0m/), built from the real sprite sheets, the generated rig data
(TrashTr0mRigData.cs) and the constants parsed straight out of the C# files, replaying the AI tick by tick.

    python -P tools/sim/trashtr0m_sim.py --out docs/media --date 2026-10-26 [--only crawl,slam,...]

Writes <date>_boss-trashtr0m-<scene>.gif|png:
    sprite   PNG: the three multiplane layers apart and composited, over a dark cavern and a light sky, the 7x height
             ruler (294 px = 7 x the player's 42 px hitbox), and the small sprites (shockwave, scrap, key, gores, icon).
    crawl    the crawl: 12-frame cycle, root motion only on drag transitions, planted hands checked for slip every tick
             (the HUD prints the worst slip: it must be 0 px), the camera panning so the arm layers' parallax shows.
    slam     wind-up, impact, the shockwave following a step in the terrain; one player jumps it, one doesn't.
    suck     the 5 s suction: a Hermes-speed runner (6 px/tick) escapes, a 3 px/tick runner is dragged in, lifted,
             swallowed, chewed and spat up; the fall-damage cap is replayed (vanilla formula) and printed. The runner's
             arrows are swallowed on the way.
    spit     the gulp and spit-back volleys of what it swallowed, then (nothing swallowed) the scrap ball lob.
    cogs     (2026-10-27) the automatic cog volley: a cog from the stacks on its back after a 30-tick telegraph, lobbed
             high towards the player, two bounces; every 2.5 s at any life, enraged too (the user's nerf of 2026-10-29;
             it was 1.5 s, 0.75 s from half life).
             (The suck scene now spits the swallowed player out behind the boss.)
    intro    Junkyard Cache -> the heap bursts (tiles cleared in 4 bands, the pedestal kept), the player is thrown back,
             the boss heaves out of the ground under the camera lock and roars; title card.
    death    the scripted breakdown under the camera lock: jolt, sag, slump, eyes out, final blast with gores.

Leaves out: lighting, music, real dust physics (particles are simple squares), vanilla's player animation (a standing
frame slides), tile framing outside the heap, network latency. The screen is a 1600x900 game view shown at half size, so
the 2x art appears at 1x.
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
from terrain import load_frames, render  # noqa: E402

BOSS = "Content/Bosses/TrashTr0m/"
SCREEN_W, SCREEN_H = 1600, 900
TPF = 3                                                # game ticks per GIF frame (20 fps, exact in 10 ms units)
BOB = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3


# ================================================================================================
# Constants straight from the C# (so the simulation can't drift from the code)
# ================================================================================================
def parse_constants():
    consts = {}
    for name in ("TrashTr0m.cs", "TrashTr0m.Attacks.cs", "TrashTr0m.Visuals.cs", "TrashTr0mPlayer.cs", "TrashTr0mSummon.cs",
                 "Projectiles/TrashTr0mShockwave.cs", "Projectiles/TrashTr0mScrapBall.cs", "Projectiles/TrashTr0mChewedScrap.cs",
                 "Projectiles/TrashTr0mCog.cs"):
        src = open(BOSS + name, encoding="utf-8").read()
        prefix = name.split("TrashTr0m")[-1].split(".")[0] + "." if name.startswith("Projectiles/") else ""
        for m in re.finditer(r"const (?:int|float) ([^;]+);", src):
            for part in m.group(1).split(","):
                if "=" not in part:
                    continue
                k, v = (s.strip() for s in part.split("=", 1))
                consts[prefix + k] = v
    # resolve simple expressions (a * b + c, f suffixes, references)
    out = {}
    for _ in range(6):
        for k, v in consts.items():
            if k in out:
                continue
            expr = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
            expr = expr.replace("TrashTr0mRigData.", "RIG_")
            try:
                out[k] = eval(expr, {}, dict(out, **{("RIG_" + a): b for a, b in RIG.items() if isinstance(b, int)}))
            except Exception:
                pass
    return out


def parse_rig():
    src = open(BOSS + "TrashTr0mRigData.cs", encoding="utf-8").read()
    rig = {}
    for m in re.finditer(r"public const int ([^;]+);", src):
        for part in m.group(1).split(","):
            k, v = (s.strip() for s in part.split("="))
            rig[k] = int(v)
    for m in re.finditer(r"public static readonly \w+\[\] (\w+) = \{([^}]*)\}", src):
        rig[m.group(1)] = [int(v) for v in re.findall(r"-?\d+", m.group(2))]
    return rig


RIG = parse_rig()
K = parse_constants()


# ================================================================================================
# Sprites
# ================================================================================================
class Sheets:
    """The packed layer pages (TrashTr0m.png, TrashTr0m_Page1.png, ...) read through the generated frame tables, exactly as
    DepthLayers.DrawFrame reads them: page, rectangle, rig origin."""
    FILES = {"body": "TrashTr0m", "glow": "TrashTr0m_Glow", "near": "TrashTr0m_ArmNear", "far": "TrashTr0m_ArmFar"}
    PRE = {"body": "Body", "glow": "Glow", "near": "Near", "far": "Far"}

    def __init__(self):
        self.pages = {}
        for layer, name in self.FILES.items():
            n = RIG[self.PRE[layer] + "Pages"]
            self.pages[layer] = [Image.open(BOSS + name + ("" if k == 0 else "_Page%d" % k) + ".png").convert("RGBA") for k in range(n)]
        self.cache = {}

    def cell(self, layer, frame):
        key = (layer, frame)
        if key not in self.cache:
            t = RIG[self.PRE[layer] + "Frames"]
            i = frame * RIG["FrameFields"]
            page, x, y, w, h, ox, oy = t[i:i + 7]
            if w <= 0 or h <= 0:
                img = Image.new("RGBA", (2, 2), (0, 0, 0, 0))
            else:
                img = self.pages[layer][page].crop((x, y, x + w, y + h))
            self.cache[key] = (img, ox, oy)
        return self.cache[key]


def darken(img, k):
    r, g, b, a = img.split()
    return Image.merge("RGBA", [ch.point(lambda v: int(v * k)) for ch in (r, g, b)] + [a])


def parallax(anchor_screen, depth, max_shift=None):
    """DepthLayers.Shift (2 px snapped)."""
    max_shift = K.get("MaxParallax", 4) if max_shift is None else max_shift
    hw, hh = SCREEN_W / 2, SCREEN_H / 2
    dx = max(-1.5, min(1.5, (anchor_screen[0] - hw) / hw))
    dy = max(-1.5, min(1.5, (anchor_screen[1] - hh) / hh))
    snap = lambda v: round(v * 0.5) * 2
    lim = max_shift * 1.5
    return (snap(max(-lim, min(lim, dx * max_shift * depth))), snap(max(-lim, min(lim, dy * max_shift * 0.5 * depth))))


def draw_cell(img, cell, anchor, buried, flip, tint=None, overlap=2):
    """DepthLayers.DrawCell."""
    src, ox, oy = cell
    visible = min(src.height, oy + overlap - buried)
    if visible <= 0:
        return
    part = src.crop((0, 0, src.width, visible))
    if flip:
        part = part.transpose(Image.FLIP_LEFT_RIGHT)
        left = anchor[0] - (src.width - ox)
    else:
        left = anchor[0] - ox
    if tint:
        part = darken(part, tint)
    img.alpha_composite(part, (int(round(left)), int(round(anchor[1] + buried - oy))))


def draw_boss(img, sheets, body, arm, anchor, buried=0, flip=False, glow=1.0, use_parallax=True):
    fs = parallax(anchor, -1) if use_parallax else (0, 0)
    ns = parallax(anchor, 1) if use_parallax else (0, 0)
    draw_cell(img, sheets.cell("far", arm), (anchor[0] + fs[0], anchor[1] + fs[1]), buried, flip, tint=0.88)
    draw_cell(img, sheets.cell("body", body), anchor, buried, flip)
    if glow > 0:
        g = sheets.cell("glow", body)
        if glow < 1:
            g = (darken(g[0], glow), g[1], g[2])
        draw_cell(img, g, anchor, buried, flip)
    draw_cell(img, sheets.cell("near", arm), (anchor[0] + ns[0], anchor[1] + ns[1]), buried, flip)


def player_sprite(frame=0, flip=False):
    heads = ap.load_frames("Content/Scrap/Armor/ScrapHelmet_Head.png", 4)
    bodies = ap.load_frames("Content/Scrap/Armor/ScrapBreastplate_Body.png", 4)
    legs = ap.load_frames("Content/Scrap/Armor/ScrapLeggings_Legs.png", 4)
    s = ap.compose(heads[0], bodies[0], legs[0], frame, BOB)
    return s.transpose(Image.FLIP_LEFT_RIGHT) if flip else s


# ================================================================================================
# The AI, ported (mirrors TrashTr0m.Visuals.cs ResolvePose / BuriedPixels and the root motion in TrashTr0m.cs)
# ================================================================================================
def crawl_step(t):
    """TrashTr0m.CrawlStep: 12 frames per CrawlCycleTicks, exact integers."""
    return t * 12 // K["CrawlCycleTicks"]


def resolve_pose(state, t, tick, arg=0):
    """TrashTr0m.ResolvePose, line for line (the in-between timeline of 2026-10-26)."""
    R = RIG
    body = R["BodyIdle0"] + (tick // 8) % 4
    arm = R["RestFrame"]
    if state == "emerge":
        if t < K["RumbleTicks"] + K["RiseTicks"]:
            arm, body = crawl_step(t) % 12, R["BodyIdle0"]
        else:
            roar = t - K["RumbleTicks"] - K["RiseTicks"]
            body = R["BodyJawOpen1"] if roar < 3 else (R["BodyJawOpen2"] if roar < 6 else R["BodySuck0"] + (t // 3) % 4)
    elif state == "crawl":
        arm = (R["RestFrame"] + crawl_step(t)) % 12
        body = R["BodyIdle0"] + (t // 9) % 4
    elif state == "retreat":
        arm = crawl_step(t) % 12
    elif state == "slamwind":
        if arg == 1:
            strike = K["SecondSlamWindupTicks"] - K["StrikeTicks"]
            if t < 4:
                body, arm = R["BodySlamHit"], R["ArmSlamHit"]
            elif t < K["SecondSlamLiftTicks"]:
                body, arm = R["BodySlamSettle"], R["ArmSlamLift"]
            elif t < K["SecondSlamPrepTicks"]:
                body, arm = R["BodySlamWind0"], R["ArmFarSlamPrep"]
            else:
                body = R["BodySlamStrike"] if t >= strike else R["BodySlamWind"]
                arm = R["ArmFarSlamRaise"] if t < K["SecondSlamRaiseTicks"] else (R["ArmFarSlamHigh"] if t < strike else R["ArmFarSlamStrike"])
        elif t < K["SlamLiftTicks"]:
            body, arm = R["BodySlamWind0"], R["ArmSlamRaise0"]
        elif t < K["SlamRiseTicks"]:
            body, arm = R["BodySlamWind"], R["ArmSlamRaise1"]
        else:
            strike = K["SlamWindupTicks"] - K["StrikeTicks"]
            body = R["BodySlamStrike"] if t >= strike else R["BodySlamWind"]
            arm = (R["ArmSlamRaise"] if t < K["SlamRaiseTicks"] else R["ArmSlamHigh"] if t < K["SlamCockTick"]
                   else R["ArmSlamCock"] if t < strike else R["ArmSlamStrike"])
    elif state == "slamrecover":
        body = R["BodySlamHit"] if t < 12 else (R["BodySlamSettle"] if t < 24 else R["BodyIdle0"])
        pre = "ArmFarSlam" if arg == 1 else "ArmSlam"
        arm = R[pre + "Hit"] if t < 20 else (R[pre + "Lift"] if t < 27 else (R[pre + "Lower"] if t < 34 else R["RestFrame"]))
    elif state == "suckwind":
        body = R["BodyJawOpen1"] if t < 15 else (R["BodyJawOpen2"] if t < 30 else R["BodySuck0"] + (t // 3) % 4)
    elif state == "suck":
        body = R["BodySuck0"] + (t // 3) % 4
    elif state in ("swallow", "gulp"):
        body = R["BodyJawOpen2"] if t < 3 else (R["BodyJawOpen1"] if t < 6 else R["BodyGulp0"] + (t // 8) % 2)
    elif state == "spitplayer":
        body = spit_body(t, K["SpitReleaseTick"])
    elif state == "spitscrap":
        iv = K["SpitVolleyInterval"]
        if t < iv:
            body = R["BodySpitWind0"] if t < 6 else R["BodySpitWind"]
        else:
            beat = t % iv
            body = R["BodySpit"] if beat < 3 else (R["BodySpitFollow"] if beat < 6 else R["BodySpitWind"])
    elif state == "spitball":
        body = spit_body(t, K["SpitBallWindTicks"])
    elif state == "dying":
        tw = K["DeathTweenTicks"]
        for limit, name in ((K["DeathSagTick"], "DeathJolt"), (K["DeathSagTick"] + tw, "DeathJoltSag"), (K["DeathSlumpTick"], "DeathSag"),
                            (K["DeathSlumpTick"] + tw, "DeathSagSlump"), (K["DeathDownTick"], "DeathSlump"),
                            (K["DeathDownTick"] + tw, "DeathSlumpDown"), (10 ** 9, "DeathDown")):
            if t < limit:
                body, arm = R["Body" + name], R["Arm" + name]
                break
    return body, arm


def spit_body(t, release):
    """TrashTr0m.SpitBody."""
    if t < release:
        return RIG["BodySpitWind0"] if t < 6 else RIG["BodySpitWind"]
    return RIG["BodySpit"] if t < release + 8 else (RIG["BodySpitFollow"] if t < release + 16 else RIG["BodyIdle0"])


def buried_pixels(state, t):
    full = RIG["BodyMaxHeight"] + 44
    if state == "emerge":
        if t < K["RumbleTicks"]:
            return full
        p = min(1.0, max(0.0, (t - K["RumbleTicks"]) / K["RiseTicks"]))
        eased = 1 - (1 - p) * (1 - p) + 0.035 * math.sin(p * math.tau * 3) * (1 - p)
        return max(0, min(full, int((1 - min(1.0, max(0.0, eased))) * full * 0.5) * 2))
    return 0


def rig_to_world(bottom, facing, x, y):
    """Rig point -> world, where `bottom` is the rig origin (TrashTr0m.RigOrigin)."""
    return (bottom[0] + (-x if facing == 1 else x), bottom[1] + y)


def rig_origin(npc_bottom, facing):
    """TrashTr0m.RigOrigin: the NPC rectangle is centred on the measured body, the rig hangs RigShiftX behind it."""
    return (npc_bottom[0] + K["RigShiftX"] * facing, npc_bottom[1])


def mouth(bottom, facing, body):
    return rig_to_world(bottom, facing, RIG["Mouth"][body * 2], RIG["Mouth"][body * 2 + 1])


def near_hand(bottom, facing, arm):
    return rig_to_world(bottom, facing, RIG["NearContact"][arm * 2], RIG["NearContact"][arm * 2 + 1])


def far_hand(bottom, facing, arm):
    return rig_to_world(bottom, facing, RIG["FarContact"][arm * 2], RIG["FarContact"][arm * 2 + 1])


def suck_pull(boss_bottom, facing, t, player_centre, body):
    """TrashTr0m.GetPull."""
    strength = min(1.0, t / K["SuckRampTicks"])
    m = mouth(boss_bottom, facing, body)
    dx, dy = m[0] - player_centre[0], m[1] - player_centre[1]
    dist = math.hypot(dx, dy)
    if dist > K["SuckRange"] or dist < 1:
        return 0.0, 0.0, False
    falloff = 1.0 if dist < K["SuckFullRange"] else 1 - (dist - K["SuckFullRange"]) / (K["SuckRange"] - K["SuckFullRange"])
    pull = strength * falloff
    convey = math.copysign(min(K["MaxPull"] * pull, abs(dx)), dx)
    if abs(dx) < K["LiftRange"]:
        return convey, max(-K["LiftSpeed"], min(K["LiftSpeed"], dy * 0.12)) * pull, True
    return convey, 0.0, False


def spit_launch(from_bottom, ground, g=0.4):
    rise = (K["MaxSpitFallTiles"] + 1) * 16 - (ground - from_bottom)
    rise = max(160, min(1200, rise))
    v = (g + math.sqrt(g * g + 8 * g * rise)) * 0.5
    return max(6.0, min(32.0, v))


# ================================================================================================
# A simple player (decompiled Player.HorizontalMovement / gravity / jump numbers)
# ================================================================================================
class SimPlayer:
    W, H = 20, 42

    def __init__(self, x, ground, boots=False, name=""):
        self.x, self.y = x, ground - self.H                # top-left
        self.vx = self.vy = 0.0
        self.boots, self.name = boots, name
        self.ground = ground
        self.fall_start = int(self.y / 16)
        self.jump = 0
        self.held = False
        self.hidden = False
        self.spat = 0
        self.damage = []                                   # (tick, amount, text)
        self.controls = 0
        self.extra_fall = 0

    @property
    def centre(self):
        return (self.x + self.W / 2, self.y + self.H / 2)

    @property
    def bottom(self):
        return self.y + self.H

    def on_ground(self):
        return self.vy == 0 and self.bottom >= self.ground - 0.01

    def run(self, direction):
        max_run, acc_run = 3.0, (6.0 if self.boots else 3.0)
        if direction < 0:
            if self.vx > -max_run:
                if self.vx > 0.2:
                    self.vx -= 0.2
                self.vx -= 0.08
            elif self.vx > -acc_run and self.on_ground():
                self.vx -= 0.016
        elif direction > 0:
            if self.vx < max_run:
                if self.vx < -0.2:
                    self.vx += 0.2
                self.vx += 0.08
            elif self.vx < acc_run and self.on_ground():
                self.vx += 0.016
        elif self.on_ground():
            self.vx = 0.0 if abs(self.vx) <= 0.2 else self.vx - math.copysign(0.2, self.vx)
        else:                                              # no input in the air: runSlowdown / 2
            self.vx = 0.0 if abs(self.vx) <= 0.1 else self.vx - math.copysign(0.1, self.vx)

    def start_jump(self):
        if self.on_ground():
            self.jump = 15
            self.vy = -5.01

    def fall_check(self, tick):
        """The vanilla fall-damage block (Player.Update, i == myPlayer, before movement)."""
        if self.vy == 0:
            n = int(self.y / 16) - self.fall_start
            limit = 25 + self.extra_fall
            if n > limit:
                dmg = (n - limit) * 10
                self.damage.append((tick, dmg, "fall"))
            self.fall_start = int(self.y / 16)
        if self.jump > 0:
            self.fall_start = int(self.y / 16)

    def physics(self, pull=0.0, lift=None):
        if self.jump > 0:
            self.vy = -5.01
            self.jump -= 1
        else:
            self.vy = min(self.vy + 0.4, 10.0)
        if lift is not None:
            self.vy = self.vy + (lift - self.vy) * 0.25
        self.vx += pull
        self.x += self.vx
        self.y += self.vy
        if self.bottom >= self.ground:
            self.y = self.ground - self.H
            self.vy = 0.0
            self.jump = 0
        self.vx -= pull
        if self.vy != 0 and self.jump == 0 and abs(self.vx) > 0:
            pass


# ================================================================================================
# Drawing helpers
# ================================================================================================
class Scene:
    def __init__(self, font_path):
        self.font = ImageFont.truetype(font_path, 15)
        self.big = ImageFont.truetype(font_path, 22)
        self.font_path = font_path
        self.frames = []

    def text(self, img, xy, s, fill=(238, 241, 243), shadow=(21, 22, 28), font=None):
        d = ImageDraw.Draw(img)
        f = font or self.font
        for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            d.text((xy[0] + ox, xy[1] + oy), s, fill=shadow, font=f)
        d.text(xy, s, fill=fill, font=f)

    def push(self, img):
        self.frames.append(img.resize((SCREEN_W // 2, SCREEN_H // 2), Image.NEAREST).convert("RGB"))

    def push_half(self, img):
        self.frames.append(img.convert("RGB"))

    def save(self, path):
        pal = [f.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in self.frames]
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=TPF * 1000 // 60, loop=0, optimize=True, disposal=1)
        size = os.path.getsize(path) / 1e6
        print("%s: %d frames, %.1f s, %.1f MB" % (path, len(self.frames), len(self.frames) * TPF / 60, size))


def sky_world(w, h, ground, seed=3, sand=(220, 196, 128)):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([0, y, w, y], fill=(int(150 - 40 * t), int(180 - 50 * t), int(210 - 40 * t), 255))
    rng = random.Random(seed)
    for k in range(5):
        cx = rng.randrange(0, w)
        hw, hh = rng.randrange(140, 260), rng.randrange(80, 160)
        d.polygon([(cx - hw, ground), (cx - hw // 3, ground - hh), (cx + hw // 2, ground - hh + 25), (cx + hw, ground)], fill=(110, 118, 140, 255))
    d.rectangle([0, ground, w, h], fill=sand + (255,))
    for _ in range(w * (h - ground) // 300):
        sx, sy = rng.randrange(0, w, 2), rng.randrange(ground + 2, h, 2)
        d.rectangle([sx, sy, sx + 1, sy + 1], fill=(184, 150, 92, 255))
    d.line([0, ground, w, ground], fill=(196, 170, 106, 255), width=2)
    return img


def particles_step(parts):
    for q in parts:
        q[0] += q[2]
        q[1] += q[3]
        q[3] += q[7]
        q[4] -= 1
    parts[:] = [q for q in parts if q[4] > 0]


def particles_draw(img, parts, cam):
    d = ImageDraw.Draw(img)
    for (x, y, vx, vy, life, colour, size, g) in parts:
        sx, sy = x - cam[0], y - cam[1]
        d.rectangle([sx, sy, sx + size - 1, sy + size - 1], fill=colour)


# ================================================================================================
# Scenes
# ================================================================================================
def scene_crawl(out, font):
    """The loop: CrawlTicks of crawling (two 75-tick cycles), then the attack (suck if a player is within suction range
    of the mouth, slam otherwise), then crawling again. Planted hands are checked for slip every tick."""
    sheets = Sheets()
    sc = Scene(font)
    W, ground = 4200, 760
    world = sky_world(W, 1500, ground)
    bottom = [3300.0, float(ground)]
    facing = -1
    worst_slip = 0.0
    planted, marks = {}, []
    pl = player_sprite(0, flip=False)
    player_x = 1500.0                                      # out of suction range at first: the boss will slam
    crawl = K["CrawlTicks"]
    timeline = [("crawl", crawl), ("decide", 0), ("crawl", crawl), ("decide", 0)]
    tick = 0
    state, t, left = "crawl", 0, crawl
    attack_log = []
    seq = []
    for _ in range(2):
        seq += [("crawl", crawl), ("attack", None)]
    for item in seq:
        name, length = item
        if name == "attack":
            m = mouth(bottom, facing, RIG["BodySuck0"])
            in_range = abs(player_x + 10 - m[0]) <= K["SuckRange"]
            attack = "suckwind" if in_range else "slamwind"
            attack_log.append((tick, attack, abs(player_x - m[0]) / 16))
            steps = [(attack, K["SuckWindupTicks"] if in_range else K["SlamWindupTicks"]), ("suck", 60) if in_range else ("slamrecover", K["SlamRecoverTicks"])]
        else:
            steps = [(name, length)]
        for st, ln in steps:
            for t in range(ln):
                if st == "crawl":
                    if t > 0 and crawl_step(t) != crawl_step(t - 1):
                        prev = (RIG["RestFrame"] + crawl_step(t) - 1) % 12
                        if RIG["CrawlDrag"][prev]:
                            bottom[0] += facing * RIG["CrawlStep"]
                    body, arm = resolve_pose("crawl", t, tick)
                    for nm, fn, cont in (("near", near_hand, RIG["NearContact"]), ("far", far_hand, RIG["FarContact"])):
                        on_ground = cont[arm * 2 + 1] == 0
                        pos = fn(bottom, facing, arm)
                        if on_ground:
                            if nm in planted:
                                worst_slip = max(worst_slip, abs(pos[0] - planted[nm][0]))
                            else:
                                planted[nm] = pos
                                marks.append((pos, nm))
                        else:
                            planted.pop(nm, None)
                else:
                    planted.clear()
                    body, arm = resolve_pose(st, t, tick)
                if tick > 150:
                    player_x = min(player_x + 6.0, 2760.0)      # the player runs in: the next attack is a suck
                if tick % TPF == 0:
                    cam_x, cam_y = int(bottom[0] - SCREEN_W * 0.62), ground - 640
                    img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
                    d = ImageDraw.Draw(img)
                    m = mouth(bottom, facing, RIG["BodySuck0"])
                    d.ellipse([m[0] - K["SuckRange"] - cam_x, m[1] - K["SuckRange"] - cam_y, m[0] + K["SuckRange"] - cam_x, m[1] + K["SuckRange"] - cam_y], outline=(124, 107, 224))
                    for (pos, nm) in marks[-8:]:
                        x = pos[0] - cam_x
                        d.line([x, ground - cam_y + 4, x, ground - cam_y + 16], fill=(163, 48, 26) if nm == "near" else (70, 58, 147), width=2)
                    draw_boss(img, sheets, body, arm, (bottom[0] - cam_x, bottom[1] - cam_y), flip=facing == 1)
                    img.alpha_composite(pl, (int(player_x - 10 - cam_x), int(ground - 56 - cam_y)))
                    label = {"crawl": "Crawl %d/%d (2.5 s)" % (t, crawl), "slamwind": "nobody in suction range -> Slam",
                             "slamrecover": "Slam", "suckwind": "a player in suction range -> Suck", "suck": "Suck"}[st]
                    sc.text(img, (16, 12), label, font=sc.big)
                    sc.text(img, (16, 44), "the body moves %d px only on the 6 drag transitions of each 75-tick cycle (%.2f px/tick); purple ring: suction range %d tiles"
                            % (RIG["CrawlStep"], 6 * RIG["CrawlStep"] / K["CrawlCycleTicks"], K["SuckRange"] // 16))
                    sc.text(img, (16, 66), "worst planted-hand slip so far: %.1f px   (red ticks: near hand plants, blue: far hand)" % worst_slip)
                    sc.push(img)
                tick += 1
    sc.save(out)
    print("crawl/loop: worst planted-hand slip = %.2f px; attacks %s" % (worst_slip, attack_log))
    return worst_slip


def scene_slam(out, font, enraged=False):
    sheets = Sheets()
    sc = Scene(font)
    W, ground = 4200, 760
    world = sky_world(W, 1500, ground)
    step_x0, step_x1, step_h = 1450, 1700, 32                # a 2-tile step the wave climbs and drops
    dw = ImageDraw.Draw(world)
    dw.rectangle([step_x0, ground - step_h, step_x1, ground], fill=(196, 170, 106, 255))
    dw.line([step_x0, ground - step_h, step_x1, ground - step_h], fill=(220, 196, 128, 255), width=2)

    def surface(x):
        return ground - step_h if step_x0 <= x <= step_x1 else ground

    bottom = (2080.0, float(ground))
    facing = -1
    jumper = SimPlayer(1200, ground, name="jumps")
    stander = SimPlayer(950, ground, name="stands")
    wave = None
    parts = []
    rng = random.Random(4)
    pl = player_sprite(0)
    hits = []
    windup, recover = K["SlamWindupTicks"], K["SlamRecoverTicks"]
    if enraged:
        timeline = [("rest", 20), ("slamwind", windup), ("slamwind2", K["SecondSlamWindupTicks"]), ("slamrecover2", recover), ("rest", 110)]
    else:
        timeline = [("rest", 20), ("slamwind", windup), ("slamrecover", recover), ("rest", 100)]
    tick = 0
    wave_w, wave_h = K["Shockwave.HitboxWidth"], K["Shockwave.HitboxHeight"]
    waves = []
    for state, length in timeline:
        for t in range(length):
            impact = None
            if (state == "slamrecover" or state == "slamwind2") and t == 0:
                impact = near_hand(bottom, facing, RIG["ArmSlamHit"])
            if state == "slamrecover2" and t == 0:
                impact = far_hand(bottom, facing, RIG["ArmFarSlamHit"])
            if impact:
                waves.append({"x": impact[0], "bottom": impact[1], "dir": facing, "life": K["Shockwave.Lifetime"], "frame": 0, "hit": set()})
                for _ in range(30):
                    parts.append([impact[0] + rng.uniform(-40, 40), impact[1] - 4, rng.uniform(-4, 4), rng.uniform(-6, -1), 40, (147, 68, 31), 6, 0.3])
            for wave in waves:
                wave["x"] += wave["dir"] * K["ShockwaveSpeed"]
                front = wave["x"] + wave["dir"] * wave_w / 2
                wave["bottom"] = surface(front)
                wave["life"] -= 1
                wave["frame"] = (tick // K["Shockwave.TicksPerFrame"]) % 4
                box = (wave["x"] - wave_w / 2, wave["bottom"] - wave_h, wave["x"] + wave_w / 2, wave["bottom"])
                for p in (jumper, stander):
                    pb = (p.x, p.y, p.x + p.W, p.y + p.H)
                    if pb[0] < box[2] and pb[2] > box[0] and pb[1] < box[3] and pb[3] > box[1] and p.name not in wave["hit"]:
                        wave["hit"].add(p.name)
                        hits.append((p.name, tick))
                        p.damage.append((tick, 120, "slam"))
            waves = [w for w in waves if w["life"] > 0]
            wave = waves[0] if waves else None
            # the jumper jumps when a wave is 220 px away: a vanilla jump keeps the feet above 40 px from 8 to ~45 ticks
            # after take-off, so any jump 160-580 px ahead of the wave's centre clears it at 14 px/tick
            for w in waves:
                if jumper.on_ground() and 0 < (jumper.x + jumper.W / 2 - w["x"]) * w["dir"] < 220:
                    jumper.start_jump()
            for p in (jumper, stander):
                p.ground = surface(p.x + p.W / 2)
                p.physics()
            particles_step(parts)
            if tick % TPF == 0:
                cam_x, cam_y = 780, ground - 640
                if state == "slamrecover" and t < 24:
                    cam_y += int(10 * (1 - t / 24) * math.sin(t * 1.7))
                img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
                pose_state = {"rest": "recover", "slamwind2": "slamwind", "slamrecover2": "slamrecover"}.get(state, state)
                arg = 1 if state in ("slamwind2", "slamrecover2") else 0
                body, arm = resolve_pose(pose_state, t, tick, arg)
                draw_boss(img, sheets, body, arm, (bottom[0] - cam_x, bottom[1] - cam_y), flip=facing == 1)
                fr = Image.open(BOSS + "Projectiles/TrashTr0mShockwave.png").convert("RGBA")
                for w in waves:
                    cell = fr.crop((0, w["frame"] * 62, 88, w["frame"] * 62 + 60))
                    if w["dir"] == 1:
                        cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
                    img.alpha_composite(cell, (int(w["x"] - 44 - cam_x), int(w["bottom"] - 58 - cam_y)))
                    d = ImageDraw.Draw(img)
                    d.rectangle([w["x"] - wave_w / 2 - cam_x, w["bottom"] - wave_h - cam_y,
                                 w["x"] + wave_w / 2 - cam_x, w["bottom"] - cam_y], outline=(255, 199, 90))
                for p in (jumper, stander):
                    img.alpha_composite(pl, (int(p.x - 10 - cam_x), int(p.y - 14 - cam_y)))
                    sc.text(img, (int(p.x - 20 - cam_x), int(p.y - 40 - cam_y)), p.name)
                    for (ht, amount, kind) in p.damage:
                        if tick - ht < 60:
                            sc.text(img, (int(p.x - cam_x), int(p.y - 70 - cam_y - (tick - ht))), str(amount), fill=(255, 199, 90), font=sc.big)
                particles_draw(img, parts, (cam_x, cam_y))
                label = {"rest": "Enraged (below 33%)" if enraged else "", "slamwind": "Slam wind-up %d/%d (telegraph)" % (t, windup),
                         "slamrecover": "Impact! shockwave %.0f px/tick" % K["ShockwaveSpeed"],
                         "slamwind2": "Impact! ... and the far claw follows: wind-up %d/%d" % (t, K["SecondSlamWindupTicks"]),
                         "slamrecover2": "Second impact: two shockwaves"}[state]
                sc.text(img, (16, 12), label, font=sc.big)
                sc.text(img, (16, 44), "wave hitbox %dx%d px (yellow) = the mound in the sprite; a jump clears it; it climbs and drops the 2-tile step" % (wave_w, wave_h))
                sc.text(img, (16, 66), "Expert damage 120 (projectile field %d x2); Classic 60, Master 180" % (120 // 2))
                sc.push(img)
            tick += 1
    sc.save(out)
    print("slam: hits", hits, "jumper damage", jumper.damage, "stander damage", stander.damage)
    return hits


def scene_suck(out, font):
    sheets = Sheets()
    sc = Scene(font)
    W, H, ground = 4400, 2400, 1700
    world = sky_world(W, H, ground)
    bottom = (3000.0, float(ground))
    facing = -1
    hermes = SimPlayer(2620, ground, boots=True, name="Hermes Boots (6 px/tick)")
    hermes.vx = -6.0
    slow = SimPlayer(2700, ground, boots=False, name="no boots (3 px/tick)")
    slow.vx = -3.0
    players = [hermes, slow]
    arrows = []
    eaten = 0
    rng = random.Random(7)
    parts = []
    pl, plr = player_sprite(0), player_sprite(0, flip=True)
    state, t = "suckwind", 0
    swallowed = None
    spat_info = {}
    tick = 0
    log = []
    max_ticks = 600
    cam = [bottom[0] - 1100.0, ground - 650.0]
    while tick < max_ticks:
        body, arm = resolve_pose(state, t, tick)
        m = mouth(bottom, facing, body)
        # --- players -------------------------------------------------------------------------------------------
        for p in players:
            if p.held:
                p.x, p.y = m[0] - p.W / 2, m[1] - p.H / 2
                p.vx = p.vy = 0.0
                p.fall_start = int(p.y / 16)
                continue
            p.fall_check(tick)
            if p.spat:
                tile_y = int(p.y / 16)
                if p.vy < 0:
                    p.fall_start = tile_y
                else:
                    p.fall_start = max(p.fall_start, tile_y - (K["MaxSpitFallTiles"] + p.extra_fall))
                    if p.vy == 0 and p.spat > 2:
                        p.spat = 0
                if p.spat:
                    p.spat += 1
            if state not in ("spitplayer",) or p is not slow:
                p.run(-1 if p.spat == 0 else 0)                      # both run away from the boss (left)
            convey, lift, lifting = (0.0, 0.0, False)
            if state == "suck":
                convey, lift, lifting = suck_pull(bottom, facing, t, p.centre, body)
            p.physics(pull=convey, lift=lift if lifting else None)
            if lifting:
                p.fall_start = int(p.y / 16)
        # arrows from the Hermes runner, aimed back at the boss
        if state in ("suckwind", "suck") and tick % 18 == 0 and tick < 330:
            sx, sy = hermes.centre
            dx, dy = m[0] - sx, m[1] - sy
            ln = math.hypot(dx, dy)
            arrows.append([sx, sy, dx / ln * 10, dy / ln * 10 - 2])
        for a in arrows:
            if state == "suck":
                dx, dy = m[0] - a[0], m[1] - a[1]
                dist = math.hypot(dx, dy)
                pull = min(1.0, t / K["SuckRampTicks"]) * (1.0 if dist < K["SuckFullRange"] else max(0.0, 1 - (dist - K["SuckFullRange"]) / (K["SuckRange"] - K["SuckFullRange"])))
                if dist < K["EatRadius"]:
                    a.append("eaten")
                    eaten += 1
                    continue
                k = K["ProjectileSteer"] * pull
                a[2] += (dx / dist * K["ProjectilePullSpeed"] - a[2]) * k
                a[3] += (dy / dist * K["ProjectilePullSpeed"] - a[3]) * k
            a[3] += 0.1
            a[0] += a[2]
            a[1] += a[3]
        arrows = [a for a in arrows if len(a) == 4 and a[1] < ground]
        # --- boss state ----------------------------------------------------------------------------------------
        if state == "suckwind" and t >= K["SuckWindupTicks"]:
            state, t = "suck", -1
        elif state == "suck":
            box = (m[0] - K["MouthBox"] / 2, m[1] - K["MouthBox"] / 2, m[0] + K["MouthBox"] / 2, m[1] + K["MouthBox"] / 2)
            if t >= K["SuckRampTicks"]:
                for p in players:
                    if p.x < box[2] and p.x + p.W > box[0] and p.y < box[3] and p.y + p.H > box[1]:
                        swallowed = p
                        p.held = True
                        state, t = "swallow", -1
                        log.append("swallowed at tick %d (suction tick %d)" % (tick, t))
                        break
            if state == "suck" and t >= K["SuckTicks"]:
                state, t = "gulp", -1
        elif state == "swallow" and t >= K["SwallowTicks"]:
            state, t = "spitplayer", -1
        elif state == "spitplayer" and t == K["SpitReleaseTick"] and swallowed:
            p = swallowed
            p.held = False
            v0 = spit_launch(p.bottom, bottom[1])
            p.vx, p.vy = -facing * K["SpitSideSpeed"], -v0              # 2026-10-27: out BEHIND the boss
            p.fall_start = int(p.y / 16)
            p.spat = 1
            spat_info = {"v0": v0, "tick": tick, "y0": p.y}
            for _ in range(20):
                parts.append([m[0], m[1], rng.uniform(-5, 1), rng.uniform(-4, 2), 30, (236, 113, 40), 6, 0.1])
        elif state == "spitplayer" and t >= K["SpitPlayerTicks"]:
            state, t = "recover", -1
        if swallowed is not None and swallowed.spat and swallowed.vy == 0 and "landed_x" not in spat_info and tick > spat_info.get("tick", 0) + 5:
            spat_info["landed_x"] = swallowed.x + swallowed.W / 2 - bottom[0]     # + = behind the (left-facing) boss
        if swallowed is not None and swallowed.damage and "done" not in spat_info:
            spat_info["done"] = tick
            spat_info["damage"] = swallowed.damage[-1][1]
            spat_info["apex"] = spat_info.get("apex")
        if swallowed is not None and swallowed.spat and swallowed.vy >= 0 and "apex" not in spat_info:
            spat_info["apex"] = (ground - swallowed.bottom) / 16
        if state == "suck" and t % 2 == 0:
            for _ in range(2):
                ang = (math.pi if facing == -1 else 0) + rng.uniform(-0.9, 0.9)
                dist = rng.uniform(120, 420)
                x, y = m[0] + math.cos(ang) * dist, m[1] + math.sin(ang) * dist
                v = 10
                parts.append([x, y, (m[0] - x) / dist * v, (m[1] - y) / dist * v, int(dist / v), (238, 241, 243), 4, 0.0])
        particles_step(parts)
        # --- camera: follows the swallowed player's flight ------------------------------------------------------
        target_x, target_y = bottom[0] - 1100.0, ground - 650.0
        if swallowed is not None and swallowed.spat:
            target_y = min(target_y, swallowed.y - 300)
            target_x = swallowed.x - 900
        cam[0] += (target_x - cam[0]) * 0.15
        cam[1] += (target_y - cam[1]) * 0.15
        if tick % TPF == 0:
            cx, cy = int(cam[0]), int(cam[1])
            img = world.crop((cx, cy, cx + SCREEN_W, cy + SCREEN_H))
            d = ImageDraw.Draw(img)
            if state == "suck":
                d.ellipse([m[0] - K["SuckRange"] - cx, m[1] - K["SuckRange"] - cy, m[0] + K["SuckRange"] - cx, m[1] + K["SuckRange"] - cy], outline=(124, 107, 224))
                d.ellipse([m[0] - K["SuckFullRange"] - cx, m[1] - K["SuckFullRange"] - cy, m[0] + K["SuckFullRange"] - cx, m[1] + K["SuckFullRange"] - cy], outline=(198, 189, 255))
            draw_boss(img, sheets, body, arm, (bottom[0] - cx, bottom[1] - cy), flip=facing == 1)
            if state == "suck":
                d = ImageDraw.Draw(img)
                d.rectangle([m[0] - K["MouthBox"] / 2 - cx, m[1] - K["MouthBox"] / 2 - cy, m[0] + K["MouthBox"] / 2 - cx, m[1] + K["MouthBox"] / 2 - cy], outline=(255, 199, 90))
            for a in arrows:
                d = ImageDraw.Draw(img)
                d.line([a[0] - cx, a[1] - cy, a[0] - a[2] * 1.5 - cx, a[1] - a[3] * 1.5 - cy], fill=(138, 90, 60), width=3)
            for p in players:
                if not p.held:
                    img.alpha_composite(plr, (int(p.x - 10 - cx), int(p.y - 14 - cy)))
                    sc.text(img, (int(p.x - 60 - cx), int(p.y - 36 - cy)), "%s  %+.1f px/t" % (p.name, p.vx))
                for (ht, amount, kind) in p.damage:
                    if tick - ht < 90:
                        sc.text(img, (int(p.x - cx), int(p.y - 80 - cy)), "-%d fall damage" % amount, fill=(255, 199, 90), font=sc.big)
            particles_draw(img, parts, (cx, cy))
            label = {"suckwind": "Suck wind-up %d/%d: the jaw opens" % (t, K["SuckWindupTicks"]),
                     "suck": "Suck %d/%d  strength %.2f  pull %.1f px/tick" % (t, K["SuckTicks"], min(1, t / K["SuckRampTicks"]), K["MaxPull"] * min(1, t / K["SuckRampTicks"])),
                     "swallow": "Swallowed! chewing %d/%d (the player is hidden and immune)" % (t, K["SwallowTicks"]),
                     "spitplayer": "Spit %d/%d" % (t, K["SpitPlayerTicks"]) + ("  launch %.1f px/tick up, %.1f back over it" % (spat_info["v0"], K["SpitSideSpeed"]) if "v0" in spat_info else ""),
                     "recover": "Recover", "gulp": "Gulp"}[state]
            sc.text(img, (16, 12), label, font=sc.big)
            sc.text(img, (16, 44), "conveyor pull %.1f px/tick (90%% of Hermes 6): Hermes nets %+.1f, no boots nets %+.1f; eaten arrows: %d" % (
                K["MaxPull"], 6 - K["MaxPull"], 3 - K["MaxPull"], eaten))
            if "landed_x" in spat_info:
                sc.text(img, (16, 88), "landed %.0f px behind the rig origin (its back is 190 px behind it)" % spat_info["landed_x"], fill=(198, 189, 255))
            if "apex" in spat_info and spat_info["apex"]:
                sc.text(img, (16, 66), "spit apex %.1f tiles above the ground; fall capped at %d tiles -> at most 200 damage" % (spat_info["apex"], K["MaxSpitFallTiles"]))
            sc.push(img)
        t += 1
        tick += 1
        if "done" in spat_info and tick > spat_info["done"] + 70:
            break
    sc.save(out)
    print("suck:", log, {k: v for k, v in spat_info.items()}, "hermes x moved %.0f px, eaten %d" % (hermes.x - 2620, eaten))
    return spat_info, eaten


def scene_spit(out, font):
    sheets = Sheets()
    sc = Scene(font)
    W, ground = 3600, 760
    world = sky_world(W, 1500, ground)
    bottom = (2600.0, float(ground))
    facing = -1
    target = SimPlayer(1700, ground, name="target")
    chunks, balls, parts = [], [], []
    rng = random.Random(2)
    pl = player_sprite(0)
    chunk_img = Image.open(BOSS + "Projectiles/TrashTr0mChewedScrap.png").convert("RGBA")
    ball_img = Image.open(BOSS + "Projectiles/TrashTr0mScrapBall.png").convert("RGBA")
    timeline = [("gulp", K["GulpTicks"], 6), ("spitscrap", 2 * K["SpitVolleyInterval"] + 8, 6), ("recover", 30, 0),
                ("gulp", K["GulpTicks"], 0), ("spitball", K["SpitBallTicks"] + 70, 0)]
    tick = 0
    for state, length, eaten in timeline:
        left = min(eaten, K["MaxSpitBack"])
        for t in range(length):
            body, arm = resolve_pose(state, t, tick)
            m = mouth(bottom, facing, body)
            if state == "spitscrap" and t > 0 and t % K["SpitVolleyInterval"] == 0 and left > 0:
                n = min(K["SpitVolleySize"], left)
                left -= n
                tc = target.centre
                time = min(90.0, math.hypot(tc[0] - m[0], tc[1] - m[1]) / K["ChewedScrapSpeed"])
                aim = (tc[0] - m[0], tc[1] - 0.5 * K["ChewedScrap.Gravity"] * time * time - m[1])   # TrashTr0m.SpitVolley
                for i in range(n):
                    spread = 0 if n == 1 else -0.22 + 0.44 * i / (n - 1)
                    a = math.atan2(aim[1], aim[0]) + spread
                    chunks.append([m[0], m[1], math.cos(a) * K["ChewedScrapSpeed"], math.sin(a) * K["ChewedScrapSpeed"], 0])
            if state == "spitball" and t == K["SpitBallWindTicks"]:
                d = (target.centre[0] - m[0], target.centre[1] - m[1])
                time = max(30, min(75, abs(d[0]) / 9))
                vx, vy = d[0] / time, (d[1] - 0.5 * K["ScrapBall.Gravity"] * time * time) / time
                balls.append([m[0], m[1], max(-16, min(16, vx)), max(-18, min(10, vy)), 0])
            for c in chunks:
                c[3] = min(c[3] + K["ChewedScrap.Gravity"], 12)
                c[0] += c[2]
                c[1] += c[3]
                c[4] += 1
            for b in balls:
                b[3] = min(b[3] + K["ScrapBall.Gravity"], 16)
                b[0] += b[2]
                b[1] += b[3]
                b[4] += 1
            for lst, dmg in ((chunks, 50), (balls, 100)):
                for c in lst:
                    hit = abs(c[0] - target.centre[0]) < 25 and abs(c[1] - target.centre[1]) < 35
                    if hit and len(c) == 5:
                        target.damage.append((tick, dmg, ""))
                        c.append("hit")
                    if c[1] >= ground:
                        for _ in range(12 if lst is balls else 4):
                            parts.append([c[0], ground - 4, rng.uniform(-4, 4), rng.uniform(-6, -1), 30, (127, 135, 148), 4, 0.3])
            chunks = [c for c in chunks if c[1] < ground]
            balls = [b for b in balls if b[1] < ground]
            particles_step(parts)
            if tick % TPF == 0:
                cam_x, cam_y = 1260, ground - 640
                img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
                draw_boss(img, sheets, body, arm, (bottom[0] - cam_x, bottom[1] - cam_y), flip=facing == 1)
                for c in chunks:
                    f = (c[4] // 5) % 3
                    img.alpha_composite(chunk_img.crop((0, f * 34, 32, f * 34 + 32)), (int(c[0] - 16 - cam_x), int(c[1] - 16 - cam_y)))
                for b in balls:
                    f = (b[4] // 5) % 4
                    img.alpha_composite(ball_img.crop((0, f * 62, 60, f * 62 + 60)), (int(b[0] - 30 - cam_x), int(b[1] - 30 - cam_y)))
                img.alpha_composite(pl, (int(target.x - 10 - cam_x), int(target.y - 14 - cam_y)))
                for (ht, amount, kind) in target.damage:
                    if tick - ht < 45:
                        sc.text(img, (int(target.x - cam_x), int(target.y - 60 - cam_y - (tick - ht))), str(amount), fill=(255, 199, 90), font=sc.big)
                particles_draw(img, parts, (cam_x, cam_y))
                if eaten:
                    label = {"gulp": "Gulp %d/%d (it swallowed %d arrows)" % (t, K["GulpTicks"], eaten),
                             "spitscrap": "Spit back: volleys of %d every %d ticks, 50 damage each (Expert)" % (K["SpitVolleySize"], K["SpitVolleyInterval"]),
                             "recover": "Recover"}.get(state, state)
                else:
                    label = {"gulp": "Gulp %d/%d (it caught nothing)" % (t, K["GulpTicks"]),
                             "spitball": "Scrap ball: a lob aimed to land on the target, 100 damage (Expert)"}.get(state, state)
                sc.text(img, (16, 12), label, font=sc.big)
                sc.push(img)
            tick += 1
    sc.save(out)
    print("spit: target hit", [(d[1]) for d in target.damage])


def build_heap():
    """The Junkyard's central heap around the cache (JunkyardPass.BuildHeap / PlaceCache)."""
    cols, rows, ground = 150, 90, 60
    centre, half, height, bury = 75, 13, 11, 5
    solid = {}
    for x in range(cols):
        for y in range(ground, rows):
            solid[(x, y)] = "a"
    last = None
    for dx in range(-half, half + 1):
        x = centre + dx
        pile = 1 - (dx / (half + 1)) ** 2
        top = ground - round(height * pile)
        if last is not None and abs(top - last) > 2:
            top = last + (2 if top > last else -2)
        last = top
        for y in range(top, ground + round(bury * math.sqrt(max(0.0, pile))) + 1):
            solid[(x, y)] = "R"
    floor = ground - 2
    left = centre - 1
    for dx in range(-1, 3):
        for y in range(floor - 3, floor):
            solid.pop((left + dx, y), None)
    for x in range(left + 3, centre + half + 2):          # the player's tunnel
        for y in range(floor - 3, floor):
            solid.pop((x, y), None)
    return cols, rows, ground, solid, left, floor - 2


def clear_band(solid, cx, ground, step, steps):
    """TrashTr0mSummon.ClearHeapRows."""
    rows = K["BurstRows"]
    per = (rows + steps - 1) // steps
    y0 = ground - rows + step * per
    y1 = min(y0 + per - 1, ground - 1)
    hw = K["BurstHalfWidth"]
    cleared = 0
    for y in range(y0, y1 + 1):
        for x in range(cx - hw, cx + hw + 1):
            if solid.get((x, y)) == "R" and not holds_container(solid, x, y):
                del solid[(x, y)]
                cleared += 1
    return cleared


CHEST = set()


def holds_container(solid, x, y):
    for k in range(1, K["PedestalScan"] + 1):
        q = (x, y - k)
        if q in CHEST:
            return True
        if solid.get(q) != "R":
            return False
    return False


def render_heap_world(cols, rows, ground, solid, left, top):
    meta = load_frames("art/templates/terrain_exposure.json")
    grid = ["".join("#" if solid.get((x, y)) == "R" else "." for x in range(cols)) for y in range(rows)]
    scrap = render(grid, {"#": Image.open("Content/Scrap/Tiles/RustedScrapTile.png").convert("RGBA")}, meta, seed=6)
    world = sky_world(cols * 16, rows * 16, ground * 16)
    world.alpha_composite(scrap)
    trunk = Image.open("Content/Furniture/ScrappyTrunkTile.png").convert("RGBA")
    for x in range(2):
        for y in range(2):
            hgt = 16 if y == 0 else 18
            world.alpha_composite(trunk.crop((36 + x * 18, y * 18, 36 + x * 18 + 16, y * 18 + hgt)), ((left + x) * 16, (top + y) * 16))
    return world


def title_card(sc, img, t, name, epithet, hold):
    fade_in, fade_out, slam = 14, 36, 1.6
    if t < 0:
        return
    if t < fade_in:
        op, scale = t / fade_in, slam + (1 - slam) * t / fade_in
    elif t < fade_in + hold:
        op, scale = 1.0, 1.0
    else:
        op, scale = max(0.0, 1 - (t - fade_in - hold) / fade_out), 1.0
    if op <= 0:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx, cy = img.width // 2, int(img.height / 2 * 0.7)
    nf = ImageFont.truetype(sc.font_path, max(8, int(110 * scale)))
    small = ImageFont.truetype(sc.font_path, 40)
    bb = ld.textbbox((0, 0), name, font=nf)
    nx, ny = cx - (bb[2] - bb[0]) // 2 - bb[0], cy - (bb[3] - bb[1]) // 2 - bb[1]
    for ox in (-4, 0, 4):
        for oy in (-4, 0, 4):
            if ox or oy:
                ld.text((nx + ox, ny + oy), name, font=nf, fill=(77, 20, 10))
    ld.text((nx, ny), name, font=nf, fill=(255, 199, 90))
    eb = ld.textbbox((0, 0), epithet, font=small)
    ex, ey = cx - (eb[2] - eb[0]) // 2 - eb[0], cy - 70 - (eb[3] - eb[1])
    for ox in (-2, 2):
        ld.text((ex + ox, ey), epithet, font=small, fill=(21, 22, 28))
        ld.text((ex, ey + ox), epithet, font=small, fill=(21, 22, 28))
    ld.text((ex, ey), epithet, font=small, fill=(195, 200, 205))
    layer.putalpha(layer.getchannel("A").point(lambda v: int(v * op)))
    img.alpha_composite(layer)


def lock_envelope(t, length, ease_in, ease_out):
    if t < 0 or t > length:
        return 0.0
    a = t / ease_in if ease_in else 1
    b = (length - t) / ease_out if ease_out else 1
    v = max(0.0, min(1.0, min(a, b)))
    return v * v * (3 - 2 * v)


def scene_intro(out, font):
    sheets = Sheets()
    sc = Scene(font)
    cols, rows, ground, solid, left, top = build_heap()
    CHEST.clear()
    CHEST.update({(left + x, top + y) for x in range(2) for y in range(2)})
    world = render_heap_world(cols, rows, ground, solid, left, top)
    boss_ground = top + K["CacheGroundRows"]
    bottom = ((left + 1) * 16.0, boss_ground * 16.0)
    focus = (bottom[0] + 40, bottom[1] - 150)
    player = SimPlayer((left + 4) * 16, (top + 2) * 16, name="player")
    player_ground = (top + 2) * 16
    parts = []
    rng = random.Random(5)
    pl = player_sprite(0, flip=True)
    emerge = K["EmergeTicks"]
    burst, steps = K["BurstTick"], K["BurstTicks"]
    knocked = False
    cleared_total = 0
    for tick in range(-30, emerge + 50):
        t = tick
        state = "emerge" if 0 <= t < emerge else ("crawl" if t >= emerge else "asleep")
        if state == "emerge" and burst <= t < burst + steps:
            cleared_total += clear_band(solid, int(bottom[0] / 16), boss_ground, t - burst, steps)
            world = render_heap_world(cols, rows, ground, solid, left, top)
            if t == burst:
                for _ in range(90):
                    x = bottom[0] + rng.uniform(-240, 240)
                    y = bottom[1] - rng.uniform(0, 180)
                    parts.append([x, y, (x - bottom[0]) * 0.04 + rng.uniform(-2, 2), -rng.uniform(4, 11), 50,
                                  rng.choice([(147, 68, 31), (94, 40, 23), (196, 104, 58), (127, 135, 148)]), 6, 0.35])
        if state == "emerge" and t >= burst and not knocked:
            knocked = True
            c = (bottom[0], bottom[1] - 64)
            dx, dy = player.centre[0] - c[0], player.centre[1] - c[1]
            dist = math.hypot(dx, dy)
            if dist <= K["BurstKnockRange"]:
                power = 1 + (0.45 - 1) * dist / K["BurstKnockRange"]
                player.vx, player.vy = math.copysign(11 * power, dx), -8.5 * power
        # player physics on the (changing) ground
        px = int((player.x + player.W / 2) / 16)
        g = None
        for y in range(int(player.y / 16), rows):
            if (px, y) in solid and (px, y - 1) not in solid:
                g = y * 16
                break
        player.ground = g if g is not None else rows * 16
        player.run(0)
        player.physics()
        if state == "emerge" and t < K["RumbleTicks"] + K["RiseTicks"] and t % 2 == 0:
            for _ in range(1 if t < burst else 3):
                parts.append([bottom[0] + rng.uniform(-200, 200), bottom[1] - 2, rng.uniform(-1.2, 1.2), rng.uniform(-3.5, -1.5), 40,
                              rng.choice([(147, 68, 31), (94, 40, 23)]), 4, 0.12])
        particles_step(parts)
        if (tick + 30) % TPF:
            continue
        lock = lock_envelope(t, emerge, K["CameraEaseTicks"], K["CameraEaseTicks"])
        cam_x = player.centre[0] + (focus[0] - player.centre[0]) * lock - SCREEN_W / 2
        cam_y = player.centre[1] + (focus[1] - player.centre[1]) * lock - SCREEN_H / 2
        if burst <= t < burst + 30:
            cam_y += 14 * (1 - (t - burst) / 30) * math.sin(t * 1.9)
        elif 1 <= t < K["RumbleTicks"] + K["RiseTicks"]:
            cam_y += 3 * math.sin(math.tau * 12 * t / 60)
        cam_x, cam_y = int(cam_x), int(cam_y)
        img = Image.new("RGBA", (SCREEN_W, SCREEN_H), (150, 180, 210, 255))
        img.alpha_composite(world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H)))
        if state != "asleep":
            body, arm = resolve_pose(state, max(0, t - emerge) if state == "crawl" else t, tick)
            buried = buried_pixels(state, t)
            draw_boss(img, sheets, body, arm, (bottom[0] - cam_x, bottom[1] - cam_y), buried=buried)
        img.alpha_composite(pl, (int(player.x - 10 - cam_x), int(player.y - 14 - cam_y)))
        particles_draw(img, parts, (cam_x, cam_y))
        title_card(sc, img, t - K["TitleTick"], "Trash-Tr0m", "Colossus of the Scrapheap", K["TitleHoldTicks"])
        if t < 0:
            label = "the player right-clicks the locked Junkyard Cache without the Lost Key"
        elif state == "emerge":
            label = "Emerge %d/%d%s" % (t, emerge, "  BURST: heap cleared (%d tiles), players near the cache thrown back" % cleared_total if t >= burst else "  rumble")
        else:
            label = "Crawl"
        sc.text(img, (16, 12), label, font=sc.big)
        sc.text(img, (16, 44), "camera lock %.2f   the cache stays on its pedestal; no tiles outside the heap are touched" % lock)
        sc.push(img)
    sc.save(out)
    print("intro: cleared %d heap tiles" % cleared_total)


def scene_death(out, font):
    sheets = Sheets()
    sc = Scene(font)
    W, ground = 3200, 760
    world = sky_world(W, 1500, ground)
    bottom = (1800.0, float(ground))
    gores = [Image.open(BOSS + "Gores/TrashTr0m_Gore%s.png" % n).convert("RGBA") for n in ("Tyre", "Jaw", "Crest", "Gear", "Piston", "Plate")]
    flying = []
    parts = []
    rng = random.Random(8)
    player = (1100, ground)
    pl = player_sprite(0)
    total = K["DeathTicks"]
    for tick in range(-20, total + 50):
        t = tick
        state = "dying" if 0 <= t < total else ("crawl" if t < 0 else "dead")
        if state == "dying" and t < K["DeathBlastTick"] and t % 11 == 0:
            at = (bottom[0] + rng.uniform(-150, 150), bottom[1] - 140 + rng.uniform(-110, 90))
            for i in range(10):
                parts.append([at[0], at[1], rng.uniform(-3, 3), rng.uniform(-3, 3), 24, (255, 199, 90) if i < 4 else (138, 144, 150), 6, -0.02])
        if t == K["DeathBlastTick"]:
            for g in gores:
                flying.append([bottom[0] + rng.uniform(-120, 120), bottom[1] - 140 + rng.uniform(-120, 40), rng.uniform(-7, 7), -rng.uniform(5, 11), g])
            for i in range(60):
                parts.append([bottom[0] + rng.uniform(-150, 150), bottom[1] - rng.uniform(0, 260), rng.uniform(-6, 6), rng.uniform(-8, 2), 40,
                              (255, 199, 90) if i % 3 == 0 else (138, 144, 150), 8, 0.1])
        for f in flying:
            f[3] = min(f[3] + 0.3, 10)
            f[0] += f[2]
            f[1] = min(f[1] + f[3], ground - f[4].height // 2)
            if f[1] >= ground - f[4].height // 2:
                f[2] *= 0.8
        particles_step(parts)
        if (tick + 20) % TPF:
            continue
        lock = lock_envelope(t, total, K["CameraEaseTicks"], 40)
        focus = (bottom[0] + 40, bottom[1] - 150)
        cam_x = player[0] + (focus[0] - player[0]) * lock - SCREEN_W / 2
        cam_y = player[1] - 21 + (focus[1] - player[1] + 21) * lock - SCREEN_H / 2
        for (kt, s) in ((0, 10), (K["DeathSlumpTick"], 10), (K["DeathBlastTick"], 16)):
            if kt <= t < kt + 30:
                cam_y += s * (1 - (t - kt) / 30) * math.sin(t * 1.9)
        cam_x, cam_y = int(cam_x), int(cam_y)
        img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
        if state != "dead":
            body, arm = resolve_pose(state, t if state == "dying" else 0, tick)
            glow = 1.0 if state != "dying" else (0.0 if t >= K["DeathDownTick"] else (0.3 if rng.random() < 0.25 else 0.9))
            draw_boss(img, sheets, body, arm, (bottom[0] - cam_x, bottom[1] - cam_y), glow=glow)
        for f in flying:
            img.alpha_composite(f[4], (int(f[0] - cam_x), int(f[1] - cam_y)))
        img.alpha_composite(pl, (int(player[0] - 10 - cam_x), int(player[1] - 56 - cam_y)))
        particles_draw(img, parts, (cam_x, cam_y))
        if t >= K["DeathBlastTick"]:
            title_card(sc, img, t - K["DeathBlastTick"], "Trash-Tr0m", "Defeated", 90)
        names = [(0, "jolt"), (K["DeathSagTick"], "sag"), (K["DeathSlumpTick"], "slump (thud)"), (K["DeathDownTick"], "down, eyes out"), (K["DeathBlastTick"], "final blast: parts fly off")]
        phase = [n for (k, n) in names if t >= k]
        label = "Dying %d/%d: %s" % (t, total, phase[-1]) if state == "dying" else ("lethal blow lands" if t < 0 else "dies: loot (Lost Key), OnKill")
        sc.text(img, (16, 12), label, font=sc.big)
        sc.text(img, (16, 44), "camera lock %.2f   untouchable while dying; the server finishes it with StrikeInstantKill at tick %d" % (lock, total))
        sc.push(img)
    sc.save(out)


def scene_leave(out, font):
    """The player walks out of the Junkyard: after LeaveGraceTicks with nobody inside, the boss burrows away (Retreat)."""
    sheets = Sheets()
    sc = Scene(font)
    W, ground = 4400, 760
    world = sky_world(W, 1500, ground)
    border = 1700                                          # the Junkyard's edge (left of it is the beach)
    dw = ImageDraw.Draw(world)
    for y in range(0, 1500, 24):
        dw.line([border, y, border, y + 12], fill=(163, 48, 26), width=3)
    bottom = (3000.0, float(ground))
    player = SimPlayer(2300, ground)
    pl = player_sprite(0, flip=False)
    state, t = "crawl", 0
    outside = 0
    tick = 0
    retreat_at = None
    while tick < 360:
        player.run(-1)
        player.physics()
        inside = player.x + player.W / 2 >= border
        if state == "crawl":
            if t % K["JunkyardCheckInterval"] == 0:
                outside = 0 if inside else outside + K["JunkyardCheckInterval"]
                if outside >= K["LeaveGraceTicks"]:
                    state, t, retreat_at = "retreat", 0, tick
        body, arm = resolve_pose(state, t, tick)
        buried = 0
        if state == "retreat":
            q = min(1.0, t / K["RetreatTicks"])
            full = RIG["BodyMaxHeight"] + 44
            buried = max(0, min(full, int(q * q * full * 0.5) * 2))
        if tick % TPF == 0:
            cam_x, cam_y = 1620, ground - 640
            img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
            if not (state == "retreat" and t >= K["RetreatTicks"]):
                draw_boss(img, sheets, body, arm, (bottom[0] - cam_x, bottom[1] - cam_y), buried=buried)
            img.alpha_composite(pl, (int(player.x - 10 - cam_x), int(player.y - 14 - cam_y)))
            sc.text(img, (int(border - cam_x) + 8, 120), "Junkyard edge", fill=(255, 199, 90))
            if state == "crawl":
                label = "player %s the Junkyard; nobody inside for %d/%d ticks" % ("in" if inside else "out of", outside, K["LeaveGraceTicks"])
            else:
                label = "Retreat %d/%d: it burrows back into the ground and despawns" % (min(t, K["RetreatTicks"]), K["RetreatTicks"])
            sc.text(img, (16, 12), label, font=sc.big)
            sc.push(img)
        t += 1
        tick += 1
        if retreat_at is not None and tick > retreat_at + K["RetreatTicks"] + 30:
            break
    sc.save(out)
    print("leave: retreat started at tick", retreat_at)


def hitbox_png(out, font):
    """Every hitbox over the art: the NPC rectangle (broad phase, white), the silhouette strips that decide contact and
    hits (yellow), the suction ranges (purple: normal, light: enraged) and the projectile hitboxes (red) over their
    sprites."""
    sheets = Sheets()
    f = ImageFont.truetype(font, 16)
    poses = [("idle (crawl rest)", RIG["BodyIdle0"], RIG["RestFrame"]), ("near slam impact", RIG["BodySlamHit"], RIG["ArmSlamHit"]),
             ("far claw slam impact", RIG["BodySlamHit"], RIG["ArmFarSlamHit"]), ("suck", RIG["BodySuck1"], RIG["RestFrame"]),
             ("raised fist", RIG["BodySlamWind"], RIG["ArmSlamHigh"]), ("dying (down)", RIG["BodyDeathDown"], RIG["ArmDeathDown"])]
    pw, ph = 620, 470
    img = Image.new("RGBA", (pw * 3, ph * 2 + 220), (240, 240, 236, 255))

    def strips(arr, frame, n):
        out = []
        for k in range(n):
            i = (frame * n + k) * 4
            x0, y0, x1, y1 = arr[i:i + 4]
            if x1 > x0 and y1 > y0:
                out.append((x0, y0, x1, y1))
        return out

    for k, (label, body, arm) in enumerate(poses):
        p = Image.new("RGBA", (pw, ph), (24, 22, 30, 255))
        npc_bottom = (pw // 2 + 20, ph - 50)
        facing = -1
        origin = rig_origin(npc_bottom, facing)
        draw_boss(p, sheets, body, arm, origin, use_parallax=False)
        d = ImageDraw.Draw(p)
        d.line([0, npc_bottom[1], pw, npc_bottom[1]], fill=(90, 60, 40), width=2)
        w, h = K["HitboxWidth"], K["HitboxHeight"]
        d.rectangle([npc_bottom[0] - w // 2, npc_bottom[1] - h, npc_bottom[0] + w // 2, npc_bottom[1]], outline=(238, 241, 243))
        for (x0, y0, x1, y1) in strips(RIG["BodyHit"], body, RIG["BodyStrips"]) + strips(RIG["NearHit"], arm, RIG["ArmStrips"]) + strips(RIG["FarHit"], arm, RIG["ArmStrips"]):
            d.rectangle([origin[0] + x0, origin[1] + y0, origin[0] + x1 - 1, origin[1] + y1 - 1], outline=(255, 199, 90))
        if "suck" in label:
            m = mouth(origin, facing, body)
            d.rectangle([m[0] - K["MouthBox"] / 2, m[1] - K["MouthBox"] / 2, m[0] + K["MouthBox"] / 2, m[1] + K["MouthBox"] / 2], outline=(236, 113, 40), width=2)
        d.text((10, 8), label, fill=(195, 200, 205), font=f)
        img.alpha_composite(p, ((k % 3) * pw, (k // 3) * ph))
    # projectiles
    q = Image.new("RGBA", (pw * 3, 220), (40, 40, 48, 255))
    d = ImageDraw.Draw(q)
    x = 30
    for path, fw, fh, stride, hw, hh, name in (("Projectiles/TrashTr0mShockwave.png", 88, 60, 62, K["Shockwave.HitboxWidth"], K["Shockwave.HitboxHeight"], "shockwave (bottom-aligned)"),
                                              ("Projectiles/TrashTr0mChewedScrap.png", 32, 32, 34, 20, 20, "chewed scrap"),
                                              ("Projectiles/TrashTr0mScrapBall.png", 60, 60, 62, 50, 50, "scrap ball")):
        sheet = Image.open(BOSS + path).convert("RGBA")
        cell = sheet.crop((0, 0, fw, fh)).resize((fw * 2, fh * 2), Image.NEAREST)
        q.alpha_composite(cell, (x, 60))
        if "shockwave" in name:
            bx0, by0 = x + (fw - hw), 60 + (fh - hh) * 2
            d.rectangle([bx0, by0, bx0 + hw * 2 - 1, 60 + fh * 2 - 1], outline=(236, 113, 40), width=2)
        else:
            bx0, by0 = x + (fw - hw), 60 + (fh - hh)
            d.rectangle([bx0, by0, bx0 + hw * 2 - 1, by0 + hh * 2 - 1], outline=(236, 113, 40), width=2)
        d.text((x, 30), "%s %dx%d (2x zoom)" % (name, hw, hh), fill=(195, 200, 205), font=f)
        x += max(fw * 2 + 60, 300)
    d.text((x, 30), "white: NPC rectangle (broad phase)", fill=(238, 241, 243), font=f)
    d.text((x, 54), "yellow: silhouette strips (contact, hits)", fill=(255, 199, 90), font=f)
    d.text((x, 78), "orange: swallow box / projectile hitboxes", fill=(236, 113, 40), font=f)
    d.text((x, 102), "suction: %d tiles (enraged %d)" % (K["SuckRange"] // 16, K["SuckRange"] * K["EnragedSuckScale"] // 16), fill=(198, 189, 255), font=f)
    img.alpha_composite(q, (0, ph * 2))
    img.convert("RGB").save(out)
    print(out, img.size)


def sprite_png(out, font):
    sheets = Sheets()
    f = ImageFont.truetype(font, 18)
    pad = 20
    body, arm = RIG["BodyIdle0"], RIG["RestFrame"]
    panel_w, panel_h = 640, 470
    img = Image.new("RGBA", (panel_w * 3 + pad * 4, panel_h * 2 + pad * 3), (240, 240, 236, 255))
    anchor = (panel_w // 2 + 40, panel_h - 40)
    # row 1: far / body / near alone
    for k, (layer, label) in enumerate((("far", "far layer (arm, baked darker)"), ("body", "middle layer (body) + _Glow"), ("near", "near layer (arm)"))):
        p = Image.new("RGBA", (panel_w, panel_h), (24, 22, 30, 255))
        idx = arm if layer != "body" else body
        draw_cell(p, sheets.cell(layer, idx), anchor, 0, False, tint=0.88 if layer == "far" else None)
        if layer == "body":
            draw_cell(p, sheets.cell("glow", body), anchor, 0, False)
        ImageDraw.Draw(p).text((12, 10), label, fill=(195, 200, 205), font=f)
        img.alpha_composite(p, (pad + k * (panel_w + pad), pad))
    # row 2: composite over a cavern with the ruler, over sky, and small sprites
    p = Image.new("RGBA", (panel_w, panel_h), (24, 22, 30, 255))
    d = ImageDraw.Draw(p)
    d.rectangle([0, anchor[1], panel_w, panel_h], fill=(60, 44, 36, 255))
    draw_boss(p, sheets, body, arm, anchor, use_parallax=False)
    pl = player_sprite(0, flip=True)
    p.alpha_composite(pl, (panel_w - 120, anchor[1] - 56))
    rx = panel_w - 50
    d.line([rx, anchor[1] - 294, rx, anchor[1]], fill=(255, 199, 90), width=2)
    for k in range(8):
        d.line([rx - 6, anchor[1] - 42 * k, rx + 6, anchor[1] - 42 * k], fill=(255, 199, 90), width=2)
    d.text((rx - 170, anchor[1] - 320), "294 px = 7 x 42 (player)", fill=(255, 199, 90), font=f)
    img.alpha_composite(p, (pad, pad * 2 + panel_h))
    p = Image.new("RGBA", (panel_w, panel_h), (150, 180, 210, 255))
    draw_boss(p, sheets, RIG["BodySuck1"], arm, anchor, use_parallax=False)
    ImageDraw.Draw(p).text((12, 10), "suck pose over a light sky", fill=(21, 22, 28), font=f)
    img.alpha_composite(p, (pad * 2 + panel_w, pad * 2 + panel_h))
    p = Image.new("RGBA", (panel_w, panel_h), (40, 40, 48, 255))
    x, y = 16, 50
    smalls = [("Projectiles/TrashTr0mShockwave.png", 62), ("Projectiles/TrashTr0mChewedScrap.png", 34), ("Projectiles/TrashTr0mScrapBall.png", 62),
              ("Items/LostKey.png", 0), ("TrashTr0m_Head_Boss.png", 0)]
    for path, stride in smalls:
        im = Image.open(BOSS + path).convert("RGBA")
        if stride:
            im = im.crop((0, 0, im.width, stride - 2))
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        p.alpha_composite(im, (x, y))
        x += im.width + 16
    ImageDraw.Draw(p).text((12, 10), "shockwave, chewed scrap, scrap ball, Lost Key, map icon (2x zoom)", fill=(195, 200, 205), font=f)
    x, y = 16, 260
    for n in ("Tyre", "Jaw", "Crest", "Gear", "Piston", "Plate"):
        im = Image.open(BOSS + "Gores/TrashTr0m_Gore%s.png" % n).convert("RGBA")
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        p.alpha_composite(im, (x, y))
        x += im.width + 12
    ImageDraw.Draw(p).text((12, 230), "death gores (2x zoom)", fill=(195, 200, 205), font=f)
    img.alpha_composite(p, (pad * 3 + panel_w * 2, pad * 2 + panel_h))
    img.convert("RGB").save(out)
    print(out, img.size)


def inbetweens_png(out, font):
    """Every pose change of the slam, the enraged second slam, the spit and the death, at the tick it happens (the
    in-betweens of 2026-10-26 marked *), each composited from the real layers through resolve_pose."""
    sheets = Sheets()
    f = ImageFont.truetype(font, 15)
    fb = ImageFont.truetype(font, 18)
    new = {RIG[k] for k in RIG if k.startswith("Body") and k[4:] in ("SlamWind0", "SlamStrike", "SlamSettle", "SpitWind0", "SpitFollow",
                                                                     "DeathJoltSag", "DeathSagSlump", "DeathSlumpDown")}
    new_arm = {RIG[k] for k in RIG if k.startswith("Arm") and k[3:] in ("SlamRaise0", "SlamRaise1", "SlamCock", "SlamStrike", "SlamLower",
                                                                        "FarSlamPrep", "FarSlamStrike", "FarSlamLower",
                                                                        "DeathJoltSag", "DeathSagSlump", "DeathSlumpDown")}

    def changes(state, length, arg=0):
        out_, last = [], None
        for t in range(length):
            pose = resolve_pose(state, t, 0, arg)
            if state in ("spitball",):
                pose = (pose[0], RIG["RestFrame"])
            if pose != last:
                out_.append((t, pose))
                last = pose
        return out_

    rows = [("slam wind-up (45 ticks) and recover", [(st, t, pz) for st, n in (("slamwind", K["SlamWindupTicks"]), ("slamrecover", K["SlamRecoverTicks"]))
                                                     for (t, pz) in changes(st, n)]),
            ("enraged: the far claw follows (32 ticks) and recovers", [(st, t, pz) for st, n in (("slamwind", K["SecondSlamWindupTicks"]), ("slamrecover", K["SlamRecoverTicks"]))
                                                                        for (t, pz) in changes(st, n, 1)]),
            ("spit (the ball, released at tick %d)" % K["SpitBallWindTicks"], [("spitball", t, pz) for (t, pz) in changes("spitball", K["SpitBallTicks"])]),
            ("death (240 ticks)", [("dying", t, pz) for (t, pz) in changes("dying", K["DeathTicks"])])]
    cw, ch = 300, 262
    cols = max(len(r[1]) for r in rows)
    img = Image.new("RGBA", (cw * cols + 20, (ch + 30) * len(rows) + 10), (240, 240, 236, 255))
    for r, (label, poses) in enumerate(rows):
        y0 = 10 + r * (ch + 30)
        ImageDraw.Draw(img).text((10, y0), label, fill=(21, 22, 28), font=fb)
        for c, (state, t, (body, arm)) in enumerate(poses):
            cell = Image.new("RGBA", (cw * 2, ch * 2 - 40), (24, 22, 30, 255))
            anchor = (cw + 40, ch * 2 - 70)
            ImageDraw.Draw(cell).line([0, anchor[1], cw * 2, anchor[1]], fill=(90, 60, 40), width=2)
            draw_boss(cell, sheets, body, arm, anchor, use_parallax=False)
            cell = cell.resize((cw, ch - 20), Image.NEAREST)
            star = body in new or arm in new_arm
            ImageDraw.Draw(cell).text((6, 4), "%s t=%d%s" % (state.replace("slam", "").replace("wind", "wind-up") or state, t, "  *" if star else ""),
                                      fill=(255, 199, 90) if star else (195, 200, 205), font=f)
            img.alpha_composite(cell, (10 + c * cw, y0 + 26))
    img.convert("RGB").save(out)
    print(out, img.size)


def scene_cogs(out, font):
    """2026-10-27: the automatic cog volley. Every CogInterval ticks (2.5 s since the user's nerf of 2026-10-29, at any
    life and enraged too) the stacks on its back rattle and puff for CogTelegraphTicks, then cough a loose cog high into
    the air towards the target (TrashTr0m.CogVelocity, +-CogScatter): it comes down on the player, bounces twice and
    breaks on the third tile. The second half of the scene is below a third of its life (enraged): the same pace."""
    sheets = Sheets()
    sc = Scene(font)
    W, ground = 3600, 760
    world = sky_world(W, 1500, ground)
    bottom = (2400.0, float(ground))
    facing = -1
    origin = rig_origin(bottom, facing)
    stack = rig_to_world(origin, facing, K["CogStackX"], K["CogStackY"])
    player = SimPlayer(1840, ground, name="target")
    cog_img = Image.open(BOSS + "Projectiles/TrashTr0mCog.png").convert("RGBA")
    cog_frames = [cog_img.crop((0, k * 26, 24, k * 26 + 24)) for k in range(4)]
    pl = player_sprite(0)
    rng = random.Random(5)
    cogs, parts = [], []
    cog_timer = 0
    total = 2 * 3 * K["CogInterval"] + 30
    hits = []
    for tick in range(total):
        half = tick >= 3 * K["CogInterval"]
        interval = K["CogInterval"]
        cog_timer += 1
        tele = cog_timer - (interval - K["CogTelegraphTicks"])
        if 0 <= tele < K["CogTelegraphTicks"] and tele % 3 == 0:
            parts.append([stack[0] + rng.uniform(-8, 8), stack[1], rng.uniform(-0.4, 0.4), -1.5 - tele * 0.05, 24, (195, 200, 205), 4 + tele // 10, 0.0])
        if cog_timer >= interval:
            cog_timer = 0
            to = (player.centre[0] + rng.uniform(-K["CogScatter"], K["CogScatter"]), player.centre[1])
            dx, dy = to[0] - stack[0], to[1] - stack[1]
            time = max(K["CogMinFlight"], min(K["CogMaxFlight"], abs(dx) * K["CogFlightPerPx"]))
            vx = max(-14, min(14, dx / time))
            vy = max(-20, min(-4, (dy - 0.5 * K["Cog.Gravity"] * time * time) / time))
            cogs.append([stack[0], stack[1], vx, vy, 0, 0, True])
            for _ in range(10):
                parts.append([stack[0], stack[1], rng.uniform(-1.5, 1.5), -rng.uniform(2, 5), 26, (127, 135, 148) if rng.random() < 0.6 else (236, 113, 40), 4, 0.05])
        for c in cogs:
            if not c[6]:
                continue
            c[3] = min(c[3] + K["Cog.Gravity"], 14)
            c[0] += c[2]
            c[1] += c[3]
            c[5] += 1
            if c[1] + 9 >= ground:
                if c[4] >= K["Cog.MaxBounces"]:
                    c[6] = False
                    for _ in range(8):
                        parts.append([c[0], ground - 4, rng.uniform(-2.5, 2.5), -rng.uniform(1, 3.5), 26, (196, 104, 58), 4, 0.3])
                    continue
                c[4] += 1
                c[1] = ground - 9
                c[3] = -c[3] * K["Cog.BounceKeep"]
                for _ in range(4):
                    parts.append([c[0], ground - 4, rng.uniform(-1, 1), -1.5, 16, (236, 113, 40), 4, 0.1])
            pc = player.centre
            if abs(c[0] - pc[0]) < 19 and abs(c[1] - pc[1]) < 30 and (not hits or tick - hits[-1][0] > 30):
                hits.append((tick, 25))
                player.damage.append((tick, 25, "cog"))
        cogs = [c for c in cogs if c[6]]
        particles_step(parts)
        if tick % TPF == 0:
            cam_x, cam_y = 1500, ground - 700
            img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
            body, arm = resolve_pose("crawl", 0, tick)
            draw_boss(img, sheets, R_IDLE(tick), RIG["RestFrame"], (bottom[0] - cam_x, bottom[1] - cam_y), flip=facing == 1)
            img.alpha_composite(pl, (int(player.x - 10 - cam_x), int(player.y - 14 - cam_y)))
            for c in cogs:
                f = (c[5] // 4) % 4
                img.alpha_composite(cog_frames[f], (int(c[0] - 12 - cam_x), int(c[1] - 12 - cam_y)))
            particles_draw(img, parts, (cam_x, cam_y))
            for (ht, amount, kind) in player.damage:
                if tick - ht < 40:
                    sc.text(img, (int(player.x - cam_x), int(player.y - 60 - cam_y - (tick - ht))), str(amount), fill=(255, 199, 90), font=sc.big)
            sc.text(img, (16, 12), ("Enraged (a third of its life): still a cog every %d ticks (%.1f s)" if half else
                                    "A loose cog every %d ticks (%.1f s), all fight long") % (interval, interval / 60.0), font=sc.big)
            sc.text(img, (16, 44), "%d-tick telegraph (the stacks hiss and puff), lobbed high towards the player (+-%d px), 2 bounces, 25 damage (Expert)" % (
                K["CogTelegraphTicks"], K["CogScatter"]))
            sc.push(img)
    sc.save(out)
    print("cogs: hits", hits)


def R_IDLE(tick):
    return RIG["BodyIdle0"] + (tick // 8) % 4


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-10-26")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    base = os.path.join(args.out, args.date + "_boss-trashtr0m-")
    jobs = [("sprite", lambda: sprite_png(base + "sprite.png", args.font)),
            ("crawl", lambda: scene_crawl(base + "loop.gif", args.font)),
            ("slam", lambda: scene_slam(base + "slam.gif", args.font)),
            ("slam2", lambda: scene_slam(base + "slam-enraged.gif", args.font, enraged=True)),
            ("leave", lambda: scene_leave(base + "leave.gif", args.font)),
            ("hitbox", lambda: hitbox_png(base + "hitboxes.png", args.font)),
            ("inbetweens", lambda: inbetweens_png(base + "inbetweens.png", args.font)),
            ("suck", lambda: scene_suck(base + "suck.gif", args.font)),
            ("cogs", lambda: scene_cogs(base + "cogs.gif", args.font)),
            ("spit", lambda: scene_spit(base + "spit.gif", args.font)),
            ("intro", lambda: scene_intro(base + "intro.gif", args.font)),
            ("death", lambda: scene_death(base + "death.gif", args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
