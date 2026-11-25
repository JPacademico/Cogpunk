"""D5 proofs for the requests of 2026-11-25 (the alpha batch). Run from the repo root:

    python -P tools/sim/update_2026_11_25_sim.py [--out docs/media] [--only spells,burp,channel,death,toadstool,lizard,driller,slowmo,floaty,items]

Offline replays with the real sprites and the C# constants (read from the source files), 60 ticks a second, 3 ticks a GIF
frame (50 ms), shown at 2x. Leaves out: lighting, sound, netcode, vanilla's own sprites (the player is the sims' armour
mannequin, bullets are stand-in streaks, and the Frog the Fungimancer turns into is a stand-in for vanilla's critter) and tile
collision beyond the floors and blocks drawn. The boss's own hover is held still in the attack replays (the floaty replay
shows it).

    spells     the Fungimancer's idle mechanics (a floaty mushroom every RainInterval over the player, bursting into its
               spore cloud on the floor; a rainbow laser every LaserInterval through the player: telegraph, then the beam)
               under three delayed spells, each cast with CastFrame's timing (the hand raised, shaken, released) and his
               Downtime between them: five rainbow spores hanging SporeHover and fired SporeGap apart; six spores bursting
               out in a fan after FanDelay; a mushroom missile turning to its target for MissileDelay, then bouncing.
    burp       the burp (its overlay over the idle body, BurpRelease) and the polymorph bolt (StartSpeed, Accel, Turn) that
               turns the player into a Toadstool for PolymorphTicks (Toadstool.FrameFor from the player's motion); then the
               orbit: six OrbitMushrooms circling at Radius (Spin a tick), swelling at SwellAt, hatching at Hatch into
               Toadstools that leap at the player.
    channel    the channel: arms up (ChannelRaise), the hold with the spinning eyes, the mushroom growing over his hands in
               six stages for ChannelTicks; left standing it blows up (the white flash, the player shell-shocked); a second
               channel where the player's shots break it and he is stunned (StunTicks).
    death      the defeat: dazed, the croak (CroakStart), the puff (PuffTick, PuffFrameTicks) and the frog (HideTick).
    toadstool  the Toadstool: sitting, the crouch, Leap's ballistic arc, the landing; killed, its spore cloud.
    lizard     the Crystal Lizard: pottering, startled (AlertRange), fleeing at FleeSpeed (the camera follows), digging away
               after FleeTicks (DigTicks, sinking as Buried cuts it).
    driller    the Driller: rolling after a player on a rock ledge, stuck at the wall (StuckTicks), boring in (BoreTicks),
               drilling through the rock steering at DrillTurn (the 16 pre-drawn headings and 3 spins), surfacing in open air.
    slowmo     a crit kill: SlowMotion's zone (CritKillSlowMotion.Ticks at ZoneSpeed, one tick in five) over everything near
               it, the zone against the screen in an inset; a second crit kill inside the world-wide cooldown doesn't slow.
    floaty     a floaty boss's melee approach (BossNPC: MeleeBlendTicks, MeleeFocusFollow, MeleeTrack*): the Fungimancer
               hovering at range, sliding into a melee player's reach over 1.5 s and tracking them slowly, then back out.
    items      the new sprites (a PNG): the 23 enemy banners, the Cogpunk accessory slot (locked), the Demon Table, the
               "Who is he?" icon and the Tearstone.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import jadey_loot_sim as L  # noqa: E402
import stage as S  # noqa: E402
import make_teaser as M  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FB = "Content/Bosses/Fungimancer/"
UG = "Content/Underground/NPCs/"
W, H = 440, 270
FLOOR = 236
STEP = 3                                   # game ticks a GIF frame
SPECTRUM = [(206, 74, 56), (236, 113, 40), (255, 199, 90), (196, 246, 48), (78, 212, 106), (67, 221, 248), (124, 107, 224),
            (228, 112, 230)]


def ints(rel):
    """Every `Name = int` in a C# file (the generated RigData files)."""
    text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    return {k: int(v) for k, v in re.findall(r"\b(\w+) = (-?\d+)\b", text)}


def label(img, s, x, y, width=84):
    """A caption, wrapped at a space after `width` characters (11 px a line)."""
    while len(s) > width:
        cut = s.rfind(" ", 0, width)
        cut = cut if cut > 0 else width
        L.label(img, s[:cut], x, y)
        s, y = s[cut:].lstrip(), y + 11
    L.label(img, s, x, y)


def save_gif(frames, path, ms=50, scale=2):
    """With one palette for every frame (from a sample of them), so the encoder stores only what changed between frames.
    The busy boss replays are written at 1x (game pixels: the sprites are drawn 2x already, so they stay crisp), a quarter
    of the bytes (the project's size: user, 2026-10-28); the rest at 2x like the other sims' proofs."""
    big = [f.convert("RGB").resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    sample = Image.new("RGB", (big[0].width, big[0].height * 4))
    for i, k in enumerate(range(0, len(big), max(1, len(big) // 4))):
        if i < 4:
            sample.paste(big[k], (0, i * big[0].height))
    pal = sample.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    out = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in big]
    out[0].save(path, save_all=True, append_images=out[1:], duration=ms, loop=0, optimize=False, disposal=1)
    print("wrote", path, len(frames), "frames", os.path.getsize(path) // 1024, "KB")


def class_consts(rel, name):
    """The constants of one class in a C# file (FungimancerProjectiles.cs defines Life and Speed in several classes)."""
    text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    m = re.search(r"class\s+" + name + r"\b", text)
    body = text[m.start():]
    nxt = re.search(r"\n\s*public\s+(?:sealed\s+)?class\s+", body[10:])
    body = body[:nxt.start() + 10] if nxt else body
    out = {}
    for cm in re.finditer(r"const (?:int|float|double) ([^;]+);", body):
        for part in cm.group(1).split(","):
            if "=" in part:
                k, v = (x.strip() for x in part.split("=", 1))
                v = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
                try:
                    out[k] = eval(v, {}, dict(out))
                except Exception:
                    pass
    return out


def backdrop(floor=FLOOR, w=W, h=H):
    """The glowing mushroom biome's dark blue in stepped bands over a mushroom-grass floor."""
    img = Image.new("RGBA", (w, h), (12, 18, 40, 255))
    d = ImageDraw.Draw(img)
    for i, col in enumerate(((14, 22, 50), (18, 28, 62), (22, 34, 74), (26, 40, 86))):
        d.rectangle([0, floor * i // 4, w, floor * (i + 1) // 4], fill=col + (255,))
    d.rectangle([0, floor, w, h], fill=(38, 44, 70, 255))
    for x in range(0, w, 16):
        d.rectangle([x, floor, x + 15, floor + 3], fill=(60, 110, 170, 255))
        d.rectangle([x + 4, floor + 7, x + 6, floor + 9], fill=(48, 56, 84, 255))
    return img


def cave_backdrop(floor=FLOOR, w=W, h=H, scroll=0):
    """The underground: stone-grey bands and a dirt floor whose blocks scroll with the camera."""
    img = Image.new("RGBA", (w, h), (20, 18, 22, 255))
    d = ImageDraw.Draw(img)
    for i, col in enumerate(((24, 22, 26), (30, 27, 31), (36, 32, 36), (42, 37, 40))):
        d.rectangle([0, floor * i // 4, w, floor * (i + 1) // 4], fill=col + (255,))
    d.rectangle([0, floor, w, h], fill=(70, 50, 38, 255))
    off = -(int(scroll) % 16)
    for x in range(off, w, 16):
        d.rectangle([x, floor, x + 15, floor + 1], fill=(104, 78, 58, 255))
        d.rectangle([x + 15, floor, x + 15, h], fill=(58, 42, 32, 255))
        d.rectangle([x + 5, floor + 8, x + 7, floor + 9], fill=(84, 62, 46, 255))
    return img


def player_img(frame=0, facing_right=True):
    return M.player(frame, flip=not facing_right)


def put_player(img, x, feet, frame=0, facing_right=True):
    p = player_img(frame, facing_right)
    S.blit(img, p, int(x) - p.width // 2, int(feet) - p.height + 2)


def additive_dot(img, x, y, size, rgb, strength=1.0):
    dot = Image.new("RGBA", (size, size), tuple(int(c * strength) for c in rgb) + (255,))
    S.blit_add(img, dot, int(x) - size // 2, int(y) - size // 2)


def flash(img, amount):
    if amount <= 0:
        return img
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    return Image.blend(img, white, min(1.0, amount))


def stars(img, x, y, t):
    """Shell-shocked / stunned: yellow stars circling the head (the game's YellowStarDust ring)."""
    for k in range(3):
        a = t * 0.25 + k * math.tau / 3
        additive_dot(img, x + math.cos(a) * 14, y + math.sin(a) * 4, 4, (255, 222, 90))


def frog_standin():
    """A stand-in for vanilla's Frog critter (its own sprite isn't in the repo)."""
    im = Image.new("RGBA", (20, 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([2, 4, 18, 13], fill=(64, 140, 60, 255), outline=(24, 60, 30, 255))
    d.ellipse([3, 1, 8, 6], fill=(64, 140, 60, 255), outline=(24, 60, 30, 255))
    d.ellipse([12, 1, 17, 6], fill=(64, 140, 60, 255), outline=(24, 60, 30, 255))
    d.point([(5, 3), (14, 3)], fill=(10, 10, 10, 255))
    return im


# ================================================================================================
# The Fungimancer and his spells
# ================================================================================================
class Fung:
    def __init__(self):
        self.r = ints(FB + "FungimancerRigData.cs")
        self.a = S.arrays(FB + "FungimancerRigData.cs")
        self.c = S.consts(FB + "FungimancerRigData.cs", FB + "Fungimancer.cs")
        src = open(os.path.join(ROOT, FB + "Fungimancer.cs"), encoding="utf-8").read()
        self.cycle = [int(v) for v in re.search(r"IdleCycle = \{([^}]*)\}", src).group(1).split(",")]
        ld = lambda s: S.load(FB + "Fungimancer%s.png" % s)   # noqa: E731
        self.far = S.darkened(ld("_Far"), 0.88)
        self.mid, self.near, self.glow = ld(""), ld("_Near"), ld("_Glow")
        self.burp, self.eyes, self.puff = ld("_Burp"), ld("_Eyes"), ld("_Puff")

    @staticmethod
    def cell(sheet, k, cw, ch, cols):
        x, y = (k % cols) * (cw + 2), (k // cols) * (ch + 2)
        return sheet.crop((x, y, x + cw, y + ch))

    def draw(self, img, k, ax, ay, burp=-1, eye=-1):
        r = self.r
        k = max(0, min(r["Frames"] - 1, k))
        lift = self.a["Lift"][k]
        cw, ch, cols = r["CellWidth"], r["CellHeight"], r["Columns"]
        x0, y0 = int(ax) - r["OriginX"], int(ay) - r["OriginY"]
        S.blit(img, self.cell(self.far, k, cw, ch, cols), x0, y0)
        S.blit(img, self.cell(self.mid, k, cw, ch, cols), x0, y0)
        if burp >= 0:
            S.blit(img, self.cell(self.burp, lift * r["BurpFrames"] + burp, r["BurpCellW"], r["BurpCellH"], r["BurpFrames"]),
                   int(ax) - r["BurpOriginX"], int(ay) - r["BurpOriginY"])
        S.blit(img, self.cell(self.glow, k, cw, ch, cols), x0, y0)
        if eye >= 0:
            S.blit(img, self.cell(self.eyes, lift * r["EyeFrames"] + eye, r["EyeCellW"], r["EyeCellH"], r["EyeFrames"]),
                   int(ax) - r["EyeOriginX"], int(ay) - r["EyeOriginY"])
        S.blit(img, self.cell(self.near, k, cw, ch, cols), x0, y0)

    def draw_puff(self, img, f, ax, ay):
        r = self.r
        S.blit(img, self.cell(self.puff, f, r["PuffCellW"], r["PuffCellH"], 1), int(ax) - r["PuffOriginX"], int(ay) - r["PuffOriginY"])

    def idle(self, clock):
        if clock % 200 < 8:
            return self.r["Idle"] + 5
        return self.r["Idle"] + self.cycle[clock // 10 % len(self.cycle)]

    def cast(self, t, clock):
        r, c = self.r, self.c
        if t < 3:
            return r["Raise"]
        if t < 6:
            return r["Raise"] + 1
        if t < c["ConjureTick"]:
            return r["Shake"] + (t - 6) // 3 % r["ShakeFrames"]
        if t < c["ConjureTick"] + 4:
            return r["Release"]
        if t < c["ConjureTick"] + 10:
            return r["Lower"]
        return self.idle(clock)

    def orbit(self, t, clock):
        r, rel = self.r, self.c["OrbitRelease"]
        if t >= self.c["OrbitTicks"]:
            return self.idle(clock)
        return r["Cast"] + (0 if t < 6 else 1 if t < 14 else 2 if t < rel else 3 if t < 30 else 4 if t < 38 else 5)

    def channel(self, t):
        r, c = self.r, self.c
        up, ticks = c["ChannelRaise"], c["ChannelTicks"]
        if t < 4:
            return r["ArmsUp"]
        if t < 8:
            return r["ArmsUp"] + 1
        if t < up:
            return r["ArmsUp"] + 2
        if t < up + ticks:
            return r["Hold"] + t // 6 % r["HoldFrames"]
        return r["ArmsDown"] + min(r["ArmsDownFrames"] - 1, (t - up - ticks) // 4)

    def burp_frame(self, bt):
        if bt < 0 or bt >= self.c["BurpTicks"]:
            return -1
        return 0 if bt < 5 else 1 if bt < 10 else 2 if bt < self.c["BurpRelease"] else 3 if bt < 22 else 4

    def hand(self, k, ax, ay):
        return ax + self.a["NearX"][k], ay + self.a["NearY"][k]

    def channel_point(self, k, ax, ay):
        a = (ax + self.a["NearX"][k], ay + self.a["NearY"][k])
        b = (ax + self.a["Near2X"][k], ay + self.a["Near2Y"][k])
        return (a[0] + b[0]) / 2, min(a[1], b[1]) - 4

    def mouth(self, ax, ay):
        return ax + self.r["MouthX"], ay + self.r["MouthY"]


class Art:
    """The spells' and minions' sheets."""

    def __init__(self):
        self.spore = S.strip(FB + "Projectiles/RainbowSpore.png", 6)
        self.bolt = S.strip(FB + "Projectiles/PolymorphBolt.png", 4)
        mis = S.load(FB + "Projectiles/MushroomMissile.png")
        P = FB + "Projectiles/FungimancerProjectiles.cs"
        k = {"Spore": class_consts(P, "RainbowSpore"), "Missile": class_consts(P, "MushroomMissile"),
             "Bolt": class_consts(P, "PolymorphBolt"), "Laser": class_consts(P, "RainbowLaser")}
        self.headings, stride, cell = k["Missile"]["Headings"], k["Missile"]["Stride"], k["Missile"]["Cell"]
        self.missile = [mis.crop((h * stride, 0, h * stride + cell, cell)) for h in range(self.headings)]
        self.floaty = [self.stack(a, b) for a, b in zip(S.strip(FB + "NPCs/FloatyMushroom.png", 3), S.strip(FB + "NPCs/FloatyMushroom_Glow.png", 3))]
        self.orbit = [self.stack(a, b) for a, b in zip(S.strip(FB + "NPCs/OrbitMushroom.png", 4), S.strip(FB + "NPCs/OrbitMushroom_Glow.png", 4))]
        self.channel = [self.stack(a, b) for a, b in zip(S.strip(FB + "NPCs/ChannelMushroom.png", 6), S.strip(FB + "NPCs/ChannelMushroom_Glow.png", 6))]
        self.cloud = S.strip(FB + "Projectiles/SporeCloud.png", 6)
        self.k = k
        self.m = S.consts(FB + "NPCs/FungimancerMushrooms.cs")
        self.sc = S.consts(FB + "Projectiles/SporeCloud.cs")

    @staticmethod
    def stack(a, b):
        out = a.copy()
        out.alpha_composite(b)
        return out

    def missile_frame(self, angle):
        h = int(round(angle / math.tau * self.headings)) % self.headings
        return self.missile[h]

    def draw_cloud(self, img, cx, cy, age):
        life, frames, fade_ticks = self.sc["Lifetime"], self.sc["Frames"], self.sc["FadeTicks"]
        if age >= life:
            return
        f = min(frames - 1, age * frames // life)
        left = life - age
        fade = left / fade_ticks if left < fade_ticks else 1.0
        S.blit(img, S.faded(self.cloud[f], fade), int(cx) - 32, int(cy) - 32)


class Toad:
    """The Toadstool's planes as DepthLayers stacks them, and its frame rule (Toadstool.FrameFor)."""

    def __init__(self):
        self.r = ints(FB + "NPCs/ToadstoolRigData.cs")
        self.c = S.consts(FB + "NPCs/Toadstool.cs")
        cw, ch = self.r["CellWidth"], self.r["CellHeight"]
        far = S.darkened(S.load(FB + "NPCs/Toadstool_Far.png"), 0.88)
        mid, glow = S.load(FB + "NPCs/Toadstool.png"), S.load(FB + "NPCs/Toadstool_Glow.png")
        self.frames = []
        for k in range(self.r["Frames"]):
            box = (0, k * (ch + 2), cw, k * (ch + 2) + ch)
            im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for s in (far, mid, glow):
                im.alpha_composite(s.crop(box))
            self.frames.append(im)
        self.shift = -(self.r["BodyLeft"] + self.r["BodyRight"]) // 2

    def frame_for(self, phase, vy, timer):
        r = self.r
        if phase == 1:
            return r["Crouch"]
        if phase == 2:
            return r["Leap"] if vy < -3 else r["Fall"] if vy > 3 else r["Air"]
        if phase == 3:
            return r["Land"]
        step = timer // 10 % 4
        return r["Idle"] + (1 if step == 3 else step)

    def draw(self, img, k, bx, by, facing_right):
        r = self.r
        im = self.frames[k]
        if facing_right:
            ax = bx - self.shift
            S.blit(img, S.mirror(im), int(ax) - (r["CellWidth"] - r["OriginX"]), int(by) - r["OriginY"])
        else:
            ax = bx + self.shift
            S.blit(img, im, int(ax) - r["OriginX"], int(by) - r["OriginY"])


class ToadBody:
    """One Toadstool's sit / crouch / leap / land cycle (Toadstool.cs's AI on flat ground)."""

    def __init__(self, toad, x, y, rnd, sit=None):
        self.t, self.x, self.y, self.vx, self.vy = toad, float(x), float(y), 0.0, 0.0
        self.phase, self.timer, self.rnd = 0, 0, rnd
        self.sit = sit if sit is not None else rnd.randint(int(toad.c["SitMin"]), int(toad.c["SitMax"]))
        self.right = False
        self.floor = y

    def leap(self, tx, ty):
        c = self.t.c
        dx = max(-c["LeapReachX"], min(c["LeapReachX"], tx - self.x))
        dy = max(-c["LeapReachY"], min(c["LeapReachY"], ty - self.y))
        t = max(28.0, min(50.0, abs(dx) / 5.0))
        self.vx = max(-c["MaxLeapVX"], min(c["MaxLeapVX"], dx / t))
        self.vy = max(-c["MaxLeapVY"], min(-c["MinLeapVY"], (dy - 0.5 * c["NPCGravity"] * t * t) / t))
        if abs(self.vx) > 0.1:
            self.right = self.vx > 0

    def tick(self, tx, ty):
        c = self.t.c
        self.timer += 1
        if self.phase == 0:
            self.right = tx > self.x
            if self.timer >= self.sit:
                self.phase, self.timer = 1, 0
        elif self.phase == 1:
            if self.timer >= c["CrouchTicks"]:
                self.phase, self.timer = 2, 0
                self.leap(tx, ty)
        elif self.phase == 2:
            self.vy = min(10.0, self.vy + c["NPCGravity"])
            self.x += self.vx
            self.y += self.vy
            if self.y >= self.floor and self.vy > 0:
                self.y, self.vx, self.vy = self.floor, 0.0, 0.0
                self.phase, self.timer = 3, 0
        elif self.phase == 3:
            if self.timer >= c["LandTicks"]:
                self.phase, self.timer = 0, 0
                self.sit = self.rnd.randint(int(c["SitMin"]), int(c["SitMax"]))

    def draw(self, img):
        self.t.draw(img, self.t.frame_for(self.phase, self.vy, self.timer), self.x, self.y, self.right)


def spells_gif(path):
    """The idle mechanics under three delayed spells."""
    f, art = Fung(), Art()
    c, k, sp, ms = f.c, art.k["Laser"], art.k["Spore"], art.k["Missile"]
    rnd = random.Random(25)
    base = backdrop()
    ax, ay = 318, 178
    px, pfeet = 92, FLOOR
    pc = (px, pfeet - 21)
    # the attack plan: (start tick, phase)
    spores_at = 30
    fan_at = spores_at + c["ConjureTick"] + c["SporeHover"] + (c["SporeCount"] - 1) * c["SporeGap"] + 6 + c["Downtime"]
    missile_at = fan_at + c["ConjureTick"] + c["FanDelay"] + 6 + c["Downtime"]
    end = missile_at + c["ConjureTick"] + c["MissileDelay"] + 6 + 70
    shrooms, clouds, lasers, spores, missile, hits = [], [], [], [], None, []
    frames = []
    for tick in range(end):
        # --- the idle mechanics ---------------------------------------------------------------------------------------------
        if tick % c["RainInterval"] == 20:
            shrooms.append([px + rnd.uniform(-70, 70), -10.0, 0])
        if tick % c["LaserInterval"] == 60:
            lasers.append([tick, rnd.choice((math.pi / 4, -math.pi / 4))])
        for s in shrooms:
            s[2] += 1
            vx = math.sin(s[2] * art.m["SwayRate"]) * art.m["SwayX"]
            s[0] += vx
            s[1] += art.m["FallSpeed"]
            s.append(vx) if len(s) == 3 else s.__setitem__(3, vx)
            if s[1] >= FLOOR - 12 and s[2] > art.m["Grace"]:
                clouds.append([s[0], FLOOR - 26, 0])
                s[2] = -1
        shrooms = [s for s in shrooms if s[2] >= 0]
        for cl in clouds:
            cl[2] += 1
        clouds = [cl for cl in clouds if cl[2] < art.sc["Lifetime"]]
        # --- the attacks ------------------------------------------------------------------------------------------------------
        caption = "idle: a falling mushroom every %.0f s, a rainbow laser every %.0f s" % (c["RainInterval"] / 60, c["LaserInterval"] / 60)
        body = f.idle(tick)
        for start, name in ((spores_at, "spores"), (fan_at, "fan"), (missile_at, "missile")):
            t = tick - start
            if 0 <= t < c["ConjureTick"] + 12:
                body = f.cast(t, tick)
            if t == c["ConjureTick"]:
                hx, hy = f.hand(f.cast(t, tick), ax, ay)
                if name == "spores":
                    for i in range(int(c["SporeCount"])):
                        a = -math.pi / 2 + (i - (c["SporeCount"] - 1) * 0.5) * 0.42
                        spores.append({"x": hx + math.cos(a) * 44, "y": hy + math.sin(a) * 44, "vx": math.cos(a) * 2, "vy": math.sin(a) * 2,
                                       "age": 0, "fire": c["SporeHover"] + i * c["SporeGap"], "spread": 0.0, "i": i})
                elif name == "fan":
                    for i in range(int(c["FanCount"])):
                        a = i * math.tau / c["FanCount"]
                        spread = (i - (c["FanCount"] - 1) * 0.5) * (c["FanSpread"] / (c["FanCount"] - 1)) * 2
                        spores.append({"x": hx + math.cos(a) * 14, "y": hy + math.sin(a) * 14, "vx": 0.0, "vy": 0.0, "age": 0,
                                       "fire": c["FanDelay"], "spread": spread, "i": i})
                else:
                    missile = {"x": hx, "y": hy, "vx": 0.0, "vy": 0.0, "age": 0, "angle": math.pi, "bounces": 0}
            if 0 <= t < c["ConjureTick"] + {"spores": c["SporeHover"] + 26, "fan": c["FanDelay"] + 6, "missile": c["MissileDelay"] + 40}[name]:
                caption = {"spores": "SPORES: 5 hang %.1f s, then fire %d ticks apart (140 each, confusing)" % (c["SporeHover"] / 60, c["SporeGap"]),
                           "fan": "FAN: 6 spores hang %.1f s, then burst in a fan (120 each)" % (c["FanDelay"] / 60),
                           "missile": "MISSILE: turns to its target %.1f s, shoots, bounces 3 times (180)" % (c["MissileDelay"] / 60)}[name]
        for s in spores:
            s["age"] += 1
            if s["age"] < s["fire"]:
                s["vx"] *= 0.88
                s["vy"] *= 0.88
                s["y"] += math.sin((s["age"] + s["i"] * 13) * 0.12) * 0.25
            elif s["age"] == s["fire"]:
                dx, dy = pc[0] - s["x"], pc[1] - s["y"]
                d = math.hypot(dx, dy) or 1
                a = math.atan2(dy, dx) + s["spread"]
                s["vx"], s["vy"] = math.cos(a) * sp["Speed"], math.sin(a) * sp["Speed"]
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            if s["age"] > s["fire"] and (abs(s["x"] - pc[0]) < 12 and abs(s["y"] - pc[1]) < 22):
                hits.append([tick, "140 + CONFUSED"])
                s["dead"] = True
            if s["y"] > FLOOR or s["x"] < -20 or s["x"] > W + 20 or s["y"] < -40:
                s["dead"] = True
        spores = [s for s in spores if not s.get("dead")]
        if missile:
            m = missile
            m["age"] += 1
            if m["age"] < c["MissileDelay"]:
                m["angle"] = math.atan2(pc[1] - m["y"], pc[0] - m["x"])
                m["y"] += math.sin(m["age"] * 0.15) * 0.3
            elif m["age"] == c["MissileDelay"]:
                m["vx"], m["vy"] = math.cos(m["angle"]) * ms["Speed"], math.sin(m["angle"]) * ms["Speed"]
            else:
                m["x"] += m["vx"]
                m["y"] += m["vy"]
                bounced = False
                if m["y"] > FLOOR - 8:
                    m["y"], m["vy"], bounced = FLOOR - 8, -m["vy"], True
                if m["x"] < 8 or m["x"] > W - 8:
                    m["vx"], bounced = -m["vx"], True
                if m["y"] < 8:
                    m["vy"], bounced = -m["vy"], True
                if bounced:
                    m["bounces"] += 1
                    if m["bounces"] > ms["MaxBounces"]:
                        clouds.append([m["x"], m["y"], 30])
                        missile = None
                if missile:
                    m["angle"] = math.atan2(m["vy"], m["vx"])
        # --- draw -------------------------------------------------------------------------------------------------------------
        if tick % STEP:
            continue
        img = base.copy()
        for cl in clouds:
            art.draw_cloud(img, cl[0], cl[1], cl[2])
        for (t0, a) in lasers:
            age = tick - t0
            if age >= k["Life"]:
                continue
            beam = age >= k["Telegraph"]
            strength = (1 - (age - k["Telegraph"]) / k["BeamTicks"] * 0.6) if beam else 0.25 + 0.55 * age / k["Telegraph"]
            step = 4 if beam else 10
            dx, dy = math.cos(a), math.sin(a)
            for i in range(-80, 81):
                x, y = pc[0] + dx * i * step, pc[1] + dy * i * step
                if -8 <= x <= W + 8 and -8 <= y <= H + 8:
                    col = SPECTRUM[(i // (4 if beam else 1) + tick // 3) % 8]
                    if beam:
                        additive_dot(img, x, y, 6, col, strength)
                        additive_dot(img, x, y, 2, (255, 255, 255), strength)
                    else:
                        additive_dot(img, x, y, 2, col, strength)
        put_player(img, px, pfeet, 0, True)
        f.draw(img, body, ax, ay)
        for s in shrooms:
            vx = s[3] if len(s) > 3 else 0
            fr = 0 if vx < -0.45 else 2 if vx > 0.45 else 1
            S.blit(img, art.floaty[fr], int(s[0]) - 12, int(s[1]) - 12)
        for s in spores:
            S.blit(img, art.spore[(tick // 4 + s["i"]) % 6], int(s["x"]) - 8, int(s["y"]) - 8)
        if missile:
            S.blit(img, art.missile_frame(missile["angle"]), int(missile["x"]) - 16, int(missile["y"]) - 16)
        for (t0, s) in hits:
            if tick - t0 < 40:
                label(img, s, px - 30, pfeet - 70 - (tick - t0) // 3)
        label(img, "FUNGIMANCER (Expert): " + caption, 6, 4)
        label(img, "tick %d  (downtime between attacks %.1f s)" % (tick, c["Downtime"] / 60), 6, 30)
        frames.append(img)
    save_gif(frames, path, scale=1)


def burp_gif(path):
    """The burp's polymorph, then the orbiting mushrooms hatching into Toadstools."""
    f, art, toad = Fung(), Art(), Toad()
    c, mc = f.c, art.m
    bk = art.k["Bolt"]
    rnd = random.Random(7)
    base = backdrop()
    ax, ay = 300, 176
    px, pfeet, pvy = 110.0, float(FLOOR), 0.0
    burp_at, orbit_at = 20, 300
    toad_until = -1
    bolt = None
    caps, toads = [], []
    frames = []
    end = orbit_at + c["OrbitRelease"] + mc["Hatch"] + 150
    puff_at = -999
    for tick in range(end):
        bt = tick - burp_at
        if bt == c["BurpRelease"]:
            mx, my = f.mouth(ax, ay)
            a = math.atan2(pfeet - 21 - my, px - mx)
            bolt = {"x": mx, "y": my, "a": a, "v": bk["StartSpeed"], "age": 0}
        if bolt:
            bolt["age"] += 1
            want = math.atan2(pfeet - 21 - bolt["y"], px - bolt["x"])
            turn = (want - bolt["a"] + math.pi) % math.tau - math.pi
            bolt["a"] += max(-bk["Turn"], min(bk["Turn"], turn))
            bolt["v"] = min(bk["MaxSpeed"], bolt["v"] + bk["Accel"])
            bolt["x"] += math.cos(bolt["a"]) * bolt["v"]
            bolt["y"] += math.sin(bolt["a"]) * bolt["v"]
            if abs(bolt["x"] - px) < 12 and abs(bolt["y"] - (pfeet - 21)) < 22:
                bolt = None
                toad_until = tick + bk["PolymorphTicks"]
                puff_at = tick
        toad_on = tick < toad_until
        if tick == toad_until:
            puff_at = tick
        # the polymorphed player hops about (its jumps; vanilla's player gravity ~0.4)
        if toad_on and pfeet >= FLOOR and (tick - puff_at) % 50 == 20:
            pvy = -6.5
        pvy = pvy + 0.4 if pfeet < FLOOR or pvy < 0 else 0.0
        pfeet = min(float(FLOOR), pfeet + pvy)
        ot = tick - orbit_at
        if ot == c["OrbitRelease"]:
            for i in range(int(c["OrbitCount"])):
                caps.append({"a": i * math.tau / c["OrbitCount"], "age": 0, "i": i})
        for cap in caps:
            cap["age"] += 1
            cap["a"] += mc["Spin"]
            if cap["age"] == mc["Hatch"]:
                cx, cy = ax + math.cos(cap["a"]) * mc["Radius"], ay - 47 + math.sin(cap["a"]) * mc["Radius"]
                for n in range(1 + cap["i"] % 2):
                    if len(toads) < mc["MaxToads"]:
                        body = ToadBody(toad, cx + n * 18, FLOOR, rnd, sit=rnd.randint(10, 40))
                        body.y, body.phase, body.vy, body.vx = cy, 2, 0.0, rnd.uniform(-1.5, 1.5)
                        toads.append(body)
                cap["gone"] = True
        caps = [cp for cp in caps if not cp.get("gone")]
        for tb in toads:
            tb.tick(px, FLOOR)
        if tick % STEP:
            continue
        img = base.copy()
        if 0 <= ot < c["OrbitTicks"]:
            body = f.orbit(ot, tick)
        else:
            body = f.idle(tick)
        f.draw(img, body, ax, ay, burp=f.burp_frame(bt))
        for cap in caps:
            cx, cy = ax + math.cos(cap["a"]) * mc["Radius"], ay - 47 + math.sin(cap["a"]) * mc["Radius"]
            fr = cap["age"] // 15 % 2 if cap["age"] < mc["SwellAt"] else 2 + (cap["age"] - mc["SwellAt"]) // 8 % 2
            S.blit(img, art.orbit[fr], int(cx) - 16, int(cy) - 16)
        for tb in toads:
            tb.draw(img)
        if toad_on:
            phase = 2 if pfeet < FLOOR else 0
            toad.draw(img, toad.frame_for(phase, pvy, tick), px, pfeet, True)
        else:
            put_player(img, px, pfeet, 0, True)
        if 0 <= tick - puff_at < 12:
            for i in range(10):
                a = i * math.tau / 10 + tick
                additive_dot(img, px + math.cos(a) * (tick - puff_at) * 2, pfeet - 20 + math.sin(a) * (tick - puff_at) * 2, 3,
                             (228, 112, 230) if i % 2 else (67, 221, 248))
        if bolt:
            S.blit(img, art.bolt[(tick // 4) % 4], int(bolt["x"]) - 12, int(bolt["y"]) - 12)
        if bt < 0 or bt < 120:
            cap_txt = "BURP every %.0f s: the throat overlay, a polymorph bolt (speeds up, homes softly; 70)" % (c["BurpCooldown"] / 60)
        else:
            cap_txt = ""
        if toad_on:
            cap_txt = "POLYMORPHED %.1f s: a Toadstool (can walk and jump, no items, wings or hooks; other players can hit it)" % (
                (toad_until - tick) / 60)
        if ot >= 0:
            cap_txt = "ORBIT: 6 mushrooms circle him (7 tiles); at %.0f s they hatch into 1-2 Toadstools each (at most %d)" % (
                mc["Hatch"] / 60, mc["MaxToads"])
        label(img, "FUNGIMANCER (Expert): " + cap_txt, 6, 4)
        label(img, "tick %d" % tick, 6, 30)
        frames.append(img)
    save_gif(frames, path, scale=1)


def channel_gif(path):
    """Two channels: one left standing (the blast), one broken (the stun)."""
    f, art = Fung(), Art()
    c, mc = f.c, art.m
    base = backdrop()
    ax, ay = 290, 196
    px = 100
    frames = []
    up, ticks = c["ChannelRaise"], c["ChannelTicks"]
    stage_size = [(32, 22), (40, 30), (52, 36), (60, 44), (72, 52), (84, 58)]
    for run in (0, 1):
        life = mc["Life"]
        broke = -1
        stun = -1
        total = up + ticks + 140 if run == 0 else up + 200 + c["StunTicks"] + 30
        shots = []
        for t in range(total):
            channeling = t < up + ticks and broke < 0
            k = f.channel(t) if broke < 0 else f.r["Fizzle"] + (t - broke) // 10 % f.r["FizzleFrames"] if t - broke < c["StunTicks"] else f.idle(t)
            if run == 1 and channeling and t > up + 20 and t % 6 == 0:
                cxp, cyp = f.channel_point(k, ax, ay)
                shots.append([px + 10, FLOOR - 30, cxp, cyp - 20, 0])
            for s in shots:
                s[4] += 1
            if run == 1 and channeling:
                life -= 3600 / 170.0 if t > up + 24 else 0
                if life <= 0:
                    broke = t
            shots = [s for s in shots if s[4] < 10]
            if t % STEP:
                continue
            img = base.copy()
            blast_age = t - (up + ticks) if run == 0 else -1
            f.draw(img, k, ax, ay, eye=(t // 4) % f.r["EyeFrames"] if channeling and t >= 8 else -1)
            if channeling and t >= up:
                age = t - up
                stage = min(5, age * 6 // ticks)
                cxp, cyp = f.channel_point(k, ax, ay)
                S.blit(img, art.channel[stage], int(cxp) - 42, int(cyp) - 72)
                w_, h_ = stage_size[stage]
                d = ImageDraw.Draw(img)
                d.rectangle([int(cxp) - w_ // 2, int(cyp) - h_, int(cxp) + w_ // 2 - 1, int(cyp) - 1], outline=(240, 60, 60, 255))
            for s in shots:
                q = s[4] / 10
                x, y = s[0] + (s[2] - s[0]) * q, s[1] + (s[3] - s[1]) * q
                additive_dot(img, x, y, 3, (255, 199, 90))
            put_player(img, px, FLOOR, 0, True)
            if 0 <= blast_age < 90:
                stars(img, px, FLOOR - 50, t)
            if broke >= 0 and 0 <= t - broke < c["StunTicks"]:
                stars(img, ax - 6, ay - 120, t)
            if broke >= 0 and t - broke < 16:
                for i in range(16):
                    a = i * math.tau / 16
                    additive_dot(img, ax + math.cos(a) * (t - broke) * 4, ay - 150 + math.sin(a) * (t - broke) * 4, 4, SPECTRUM[i % 8])
            if run == 0:
                cap_txt = ("CHANNEL: arms up, eyes spinning, half damage taken; the mushroom grows 6 stages in %.0f s (red: its hitbox)" % (ticks / 60)
                           if channeling else "LEFT STANDING: it blows up (360, the whole arena), flash, ears ringing, players stunned 1.5 s")
            else:
                cap_txt = ("CHANNEL again: the player's shots race its %d life" % mc["Life"] if channeling
                           else "BROKEN: he is stunned %.0f s" % (c["StunTicks"] / 60))
            label(img, "FUNGIMANCER (Expert): " + cap_txt, 6, 4)
            if run == 1 and channeling:
                label(img, "mushroom life %d" % max(0, life), 6, 30)
            if 0 <= blast_age < 36:
                img = flash(img, 0.9 * (1 - blast_age / 36))
                label(img, "*ring* (sound muffled 2 s)", px - 30, FLOOR - 80)
            frames.append(img)
    save_gif(frames, path, scale=1)


def death_gif(path):
    f = Fung()
    c = f.c
    base = backdrop()
    ax, ay = 220, 200
    frog = frog_standin()
    frames = []
    for t in range(int(c["DeathTicks"]) + 60):
        if t % STEP:
            continue
        img = base.copy()
        if t < c["HideTick"]:
            if t < c["CroakStart"]:
                k = f.r["Fizzle"] + t // 8 % f.r["FizzleFrames"]
            else:
                k = f.r["Croak"] + max(0, min(2, (t - c["CroakStart"]) * 3 // max(1, c["PuffTick"] - c["CroakStart"])))
            f.draw(img, k, ax, ay)
        else:
            S.blit(img, frog, ax - 10, FLOOR - 14)
        if t >= c["PuffTick"]:
            pf = (t - c["PuffTick"]) // c["PuffFrameTicks"]
            if pf < f.r["PuffFrames"]:
                f.draw_puff(img, pf, ax, ay)
        txt = ("DEFEAT: dazed" if t < c["CroakStart"] else "the croak (his throat swells)" if t < c["PuffTick"]
               else "the puff of magic smoke..." if t < c["HideTick"] + 20 else "...a Frog (vanilla's critter; stand-in here)")
        label(img, "FUNGIMANCER: " + txt, 6, 4)
        if t >= c["DeathTicks"] - 20:
            S.blit(img, S.text("FUNGIMANCER DEFEATED", 16, "title"), W // 2 - 110, 40)
        frames.append(img)
    save_gif(frames, path)


def toadstool_gif(path):
    toad, art = Toad(), Art()
    rnd = random.Random(3)
    base = backdrop()
    px = 360
    body = ToadBody(toad, 90, FLOOR, rnd, sit=40)
    frames = []
    dead_at, cloud = -1, None
    for t in range(560):
        tx = px if t < 300 else 120
        if dead_at < 0:
            body.tick(tx, FLOOR)
        if t == 470:
            dead_at = t
            cloud = [body.x, FLOOR - 26, 0]
        if cloud:
            cloud[2] += 1
        if t % STEP:
            continue
        img = base.copy()
        if cloud:
            art.draw_cloud(img, cloud[0], cloud[1], cloud[2])
        if dead_at < 0:
            body.draw(img)
        put_player(img, px if t < 300 else 300, FLOOR, 0, px < body.x if t < 300 else False)
        ph = ["sitting", "crouch (the croak)", "leap", "landing"][body.phase]
        label(img, "TOADSTOOL (Expert 320 life, 70 touch + Confused 2 s): " + (ph if dead_at < 0 else "killed: its spore cloud (24, 4x4 tiles)"), 6, 4)
        frames.append(img)
    save_gif(frames, path)


def lizard_gif(path):
    r = ints(UG + "CrystalLizardRigData.cs")
    c = S.consts(UG + "CrystalLizard.cs")
    cw, ch = r["CellWidth"], r["CellHeight"]
    far = S.darkened(S.load(UG + "CrystalLizard_Far.png"), 0.88)
    mid, glow = S.load(UG + "CrystalLizard.png"), S.load(UG + "CrystalLizard_Glow.png")
    cells = []
    for kk in range(r["Frames"]):
        box = (0, kk * (ch + 2), cw, kk * (ch + 2) + ch)
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for s in (far, mid, glow):
            im.alpha_composite(s.crop(box))
        cells.append(im)
    shift = -(r["BodyLeft"] + r["BodyRight"]) // 2
    x, vx, px = 300.0, -0.5, 20.0
    phase, timer, fc = "calm", 0, 0.0
    cam = 0.0
    frames = []
    for t in range(560):
        timer += 1
        if phase == "calm":
            px += 2.2
            x += vx
            if timer % 120 == 60:
                vx = -vx
            if abs(x - px) < c["AlertRange"]:
                phase, timer = "alert", 0
        elif phase == "alert":
            vx = 0.0
            if timer >= 8:
                phase = "flee"
        elif phase == "flee":
            px += 2.2
            vx = min(c["FleeSpeed"], vx + c["FleeAccel"])
            x += vx
            if timer >= c["FleeTicks"]:
                phase, timer = "dig", 0
        elif phase == "dig":
            vx = 0.0
            if timer >= c["DigTicks"]:
                phase, timer = "gone", 0
        cam = max(cam, x - 280) if phase in ("flee", "dig", "gone") else cam
        if abs(vx) > 0.2:
            fc = (fc + abs(vx)) % (r["RunStep"] * r["RunFrames"])
        if t % STEP:
            continue
        img = cave_backdrop(scroll=cam)
        if phase == "calm":
            kk = r["Run"] + int(fc // r["RunStep"]) % r["RunFrames"] if abs(vx) > 0.2 else r["Idle"] + timer // 30 % r["IdleFrames"]
        elif phase == "alert":
            kk = r["Alert"]
        elif phase == "flee":
            kk = r["Run"] + int(fc // r["RunStep"]) % r["RunFrames"]
        else:
            kk = r["Dig"] + min(r["DigFrames"] - 1, timer * r["DigFrames"] // c["DigTicks"])
        buried = int(min(1.0, timer / c["DigTicks"]) * ch) & ~1 if phase == "dig" else 0
        right = vx > 0 or phase in ("flee", "dig")
        if phase != "gone":
            im = cells[kk]
            visible = min(ch, r["OriginY"] + 2 - buried)
            if visible > 0:
                im = im.crop((0, 0, cw, visible))
                sx = x - cam
                if right:
                    S.blit(img, S.mirror(cells[kk]).crop((0, 0, cw, visible)), int(sx - shift) - (cw - r["OriginX"]), FLOOR + buried - r["OriginY"])
                else:
                    S.blit(img, im, int(sx + shift) - r["OriginX"], FLOOR + buried - r["OriginY"])
        if phase == "dig":
            for i in range(6):                              # dirt thrown up either side (the game's Dirt dust)
                a = (i * 2.4 + timer * 0.3) % math.tau
                rr = (timer * 3 + i * 7) % 18
                additive_dot(img, x - cam + math.cos(a) * rr, FLOOR - 2 - abs(math.sin(a)) * rr, 3, (120, 90, 60))
        put_player(img, px - cam, FLOOR, (t // 4) % 14 + 6, True)
        txt = {"calm": "pottering about", "alert": "startled (a player within %d tiles)" % (c["AlertRange"] / 16),
               "flee": "fleeing at %.1f px/tick: %.1f s left to kill it" % (c["FleeSpeed"], max(0, (c["FleeTicks"] - timer) / 60)),
               "dig": "digging away (hittable for the first %d ticks)" % c["DigVulnerableTicks"], "gone": "gone: no loot"}[phase]
        label(img, "CRYSTAL LIZARD (160 life, 32 defense, harmless): " + txt, 6, 4)
        frames.append(img)
    save_gif(frames, path)


def driller_gif(path):
    r = ints(UG + "DrillerRigData.cs")
    c = S.consts(UG + "Driller.cs")
    cw, ch = r["CellWidth"], r["CellHeight"]
    mid, glow = S.load(UG + "Driller.png"), S.load(UG + "Driller_Glow.png")
    cells = []
    for kk in range(r["Frames"]):
        box = (0, kk * (ch + 2), cw, kk * (ch + 2) + ch)
        im = mid.crop(box)
        im.alpha_composite(glow.crop(box))
        cells.append(im)
    drill = S.load(UG + "Driller_Drill.png")
    dglow = S.load(UG + "Driller_DrillGlow.png")
    shift = -(r["BodyLeft"] + r["BodyRight"]) // 2
    hw, hh = r["BodyRight"] - r["BodyLeft"], -r["BodyTop"]
    rock = (236, FLOOR - 96, 400, FLOOR)                     # a rock block the player stands on
    ptx, pty = 330, rock[1]
    x, y, vx, vy = 40.0, float(FLOOR), 0.0, 0.0             # bottom centre
    phase, timer, still = "roll", 0, 0
    frames = []

    def solid(px_, py_):
        return rock[0] <= px_ < rock[2] and rock[1] <= py_ < rock[3]

    for t in range(470):
        timer += 1
        if phase == "roll":
            vx = min(c["RollSpeed"], vx + c["RollAccel"])
            nx = x + vx
            if solid(nx + hw / 2, y - 2):
                vx = 0.0
                still += 1
            else:
                x = nx
            vy = min(10.0, vy + 0.3)
            ny = y + vy
            floor_y = rock[1] if rock[0] <= x < rock[2] else FLOOR
            if ny >= floor_y:
                ny, vy = floor_y, 0.0
            y = ny
            if still >= c["StuckTicks"]:
                phase, timer = "bore", 0
        elif phase == "bore":
            if timer >= c["BoreTicks"]:
                phase, timer = "drill", 0
                vx, vy = 1.0, 2.0
        elif phase == "drill":
            cx, cy = x, y - hh / 2
            want = math.atan2(pty - 30 - cy, ptx - cx)
            cur = math.atan2(vy, vx)
            turn = (want - cur + math.pi) % math.tau - math.pi
            cur += max(-c["DrillTurn"], min(c["DrillTurn"], turn))
            sp = min(c["DrillSpeed"], math.hypot(vx, vy) + c["DrillAccel"])
            vx, vy = math.cos(cur) * sp, math.sin(cur) * sp
            x += vx
            y += vy
            inside = any(solid(x + dx, y - dy) for dx in (-hw / 2, 0, hw / 2) for dy in (0, hh / 2, hh))
            if timer >= c["MinDrillTicks"] and not inside and y < rock[1]:
                phase, timer = "fall", 0
        elif phase == "fall":
            vx *= 0.9
            vy = min(10.0, vy + 0.3)
            x += vx
            y += vy
            floor_y = rock[1] if rock[0] <= x < rock[2] else FLOOR
            if y >= floor_y:
                y, vy = floor_y, 0.0
                phase, timer = "roll2", 0
        elif phase == "roll2":
            vx = max(-c["RollSpeed"], min(c["RollSpeed"], (ptx - 20 - x) * 0.05))
            x += vx
        if t % STEP:
            continue
        img = cave_backdrop()
        d = ImageDraw.Draw(img)
        d.rectangle(rock, fill=(86, 80, 84, 255))
        for yy in range(rock[1], rock[3], 16):
            for xx in range(rock[0], rock[2], 16):
                d.rectangle([xx, yy, xx + 15, yy + 15], outline=(64, 58, 62, 255))
                d.rectangle([xx + 3, yy + 4, xx + 5, yy + 5], fill=(104, 98, 102, 255))
        d.rectangle([rock[0], rock[1], rock[2], rock[1] + 2], fill=(110, 104, 108, 255))
        put_player(img, ptx, pty, 0, False)
        if phase == "drill":
            ang = math.atan2(vy, vx)
            h = int(round(ang / math.tau * r["Headings"])) % r["Headings"]
            spin = (t // 3) % r["Spins"]
            box = (h * r["DrillStride"], spin * r["DrillStride"], h * r["DrillStride"] + r["DrillCell"], spin * r["DrillStride"] + r["DrillCell"])
            im = drill.crop(box)
            im.alpha_composite(dglow.crop(box))
            S.blit(img, im, int(x) - r["DrillCell"] // 2, int(y - hh / 2) - r["DrillCell"] // 2)
            if any(solid(x + dx, y - hh / 2) for dx in (-10, 0, 10)):
                for i in range(3):
                    additive_dot(img, x - vx * 3 + (i - 1) * 5, y - hh / 2 - vy * 3 + (t % 4), 3, (120, 100, 80))
        else:
            step = 3 if phase == "bore" else 6 if abs(vx) > 0.2 else 14
            kk = (t // step) % r["Frames"]
            S.blit(img, S.mirror(cells[kk]), int(x - shift) - (cw - r["OriginX"]), int(y) - r["OriginY"])
        txt = {"roll": "rolling after the player" if still == 0 else "stuck at the wall: %.1f s" % (still / 60),
               "bore": "boring in (the drill revs)", "drill": "drilling: a worm's head through the rock (16 headings, 3 spins)",
               "fall": "surfaced in open air: falls", "roll2": "rolling again"}[phase]
        label(img, "DRILLER (240 life, 48 touch): " + txt, 6, 4)
        frames.append(img)
    save_gif(frames, path)


def slowmo_gif(path):
    """A crit kill slows everything near it (SlowMotion's zone); a second one inside the cooldown doesn't."""
    toad, art = Toad(), Art()
    k = S.consts("Core/Combat/CritKillSlowMotion.cs")
    sm = S.consts("Core/Systems/SlowMotion.cs")
    ticks, cooldown, speed = int(k["Ticks"]), int(k["CooldownTicks"]), sm["ZoneSpeed"]
    src = open(os.path.join(ROOT, "Core/Combat/CritKillSlowMotion.cs"), encoding="utf-8").read()
    zm = re.search(r"ZoneHalf = new\(([\d.]+)f \* ([\d.]+)f / 2f, ([\d.]+)f \* ([\d.]+)f / 2f\)", src)
    zone = (int(float(zm.group(1)) * float(zm.group(2))), int(float(zm.group(3)) * float(zm.group(4))))
    crit_at, crit_x = -1, 0.0
    rnd = random.Random(11)
    base = backdrop()
    px = 70
    target = ToadBody(toad, 300, FLOOR, rnd, sit=999)
    other = ToadBody(toad, 380, FLOOR, rnd, sit=30)
    shrooms = [[200.0, -20.0, 0], [260.0, -120.0, 0], [150.0, -60.0, 0]]
    bullets, dust, clouds = [], [], []
    frames = []
    zone_left, acc, cool = 0, 0.0, 0
    kills = 0
    t = 0
    second_kill_tick = -1
    while t < 330:
        held = zone_left > 0
        update = True
        if held:
            acc += speed
            update = acc >= 1.0
            if update:
                acc -= 1.0
            zone_left -= 1
        if cool > 0:
            cool -= 1
        if update:
            if t % 12 == 0 and t < 300:
                bullets.append([px + 14, FLOOR - 28, 0])
            for b in bullets:
                b[0] += 12
                b[2] += 1
            hit_target = None
            for b in bullets:
                for tb in (target, other):
                    if tb and abs(b[0] - tb.x) < 20 and not b[1] < 0:
                        hit_target = tb
                        b[1] = -999
            bullets = [b for b in bullets if b[1] > 0 and b[0] < W + 10]
            if hit_target is not None:
                hit_target.hits = getattr(hit_target, "hits", 0) + 1
                if hit_target.hits >= 3:
                    kills += 1
                    clouds.append([hit_target.x, FLOOR - 26, 0])
                    for i in range(14):
                        a = rnd.uniform(0, math.tau)
                        dust.append([hit_target.x, FLOOR - 20, math.cos(a) * 3, math.sin(a) * 3 - 1, 0])
                    crit_at, crit_x = t, hit_target.x
                    if cool == 0:
                        zone_left, acc, cool = ticks, 0.0, cooldown
                    else:
                        second_kill_tick = t
                    if hit_target is target:
                        target = None
                    else:
                        other = None
            for tb in (target, other):
                if tb:
                    tb.tick(px, FLOOR)
            for s in shrooms:
                s[2] += 1
                s[0] += math.sin(s[2] * 0.05) * 1.1
                s[1] += 1.5
                if s[1] > FLOOR - 12:
                    s[1] = -20.0
            for dd in dust:
                dd[0] += dd[2]
                dd[1] += dd[3]
                dd[3] += 0.12
                dd[4] += 1
            dust = [dd for dd in dust if dd[4] < 40]
            for cl in clouds:
                cl[2] += 1
            clouds = [cl for cl in clouds if cl[2] < art.sc["Lifetime"]]
        if t % STEP == 0:
            img = base.copy()
            for cl in clouds:
                art.draw_cloud(img, cl[0], cl[1], cl[2])
            for s in shrooms:
                S.blit(img, art.floaty[1], int(s[0]) - 12, int(s[1]) - 12)
            for tb in (target, other):
                if tb:
                    tb.draw(img)
            put_player(img, px, FLOOR, 0, True)
            for b in bullets:
                ImageDraw.Draw(img).rectangle([int(b[0]) - 6, int(b[1]), int(b[0]) + 2, int(b[1]) + 1], fill=(255, 199, 90, 255))
            for dd in dust:
                additive_dot(img, dd[0], dd[1], 3, (78, 212, 106))
            if held or zone_left > 0:
                label(img, "CRIT KILL: everything within the zone at %d%% speed for %.2f s" % (speed * 100, ticks / 60), 6, 4)
                ImageDraw.Draw(img).rectangle([0, 0, W - 1, H - 1], outline=(255, 199, 90, 255), width=2)
            elif second_kill_tick >= 0 and t - second_kill_tick < 90:
                label(img, "another crit kill: no slow motion (world cooldown, %.1f s left)" % (cool / 60), 6, 4)
            else:
                label(img, "crit-kill slow motion (server config, on by default; %d s cooldown for the whole world)" % (cooldown // 60), 6, 4)
            label(img, "tick %d%s" % (t, "  (held: entities update 1 tick in %d)" % round(1 / speed) if held else ""), 6, 30)
            # the inset: the zone against the screen (1920 x 1080), 1/24 scale
            ox_, oy_ = W - 130, 34
            zw, zh = int(zone[0] / 24), int(zone[1] / 24)
            sw, sh = 1920 // 24, 1080 // 24
            d = ImageDraw.Draw(img)
            d.rectangle([ox_, oy_, ox_ + zw, oy_ + zh], outline=(255, 199, 90, 255))
            d.rectangle([ox_ + (zw - sw) // 2, oy_ + (zh - sh) // 2, ox_ + (zw + sw) // 2, oy_ + (zh + sh) // 2], outline=(195, 200, 205, 255))
            label(img, "zone %dx%d, screen 1920x1080" % zone, ox_ - 96, oy_ + zh + 3)
            if crit_at >= 0 and t - crit_at < 40:
                label(img, "CRIT!", int(crit_x) - 14, FLOOR - 60 - (t - crit_at) // 2)
            frames.append(img)
        t += 1
    save_gif(frames, path)


def floaty_gif(path):
    """BossNPC's melee approach on the Fungimancer: the blend, the slow focus, the steering."""
    f = Fung()
    b = S.consts("Core/Templates/BossNPC.cs")
    c = f.c
    w, h = c["HitboxWidth"], c["HitboxHeight"]
    pw, ph = 20, 42
    px = 120.0
    cx, cy = 330.0, 110.0
    vx = vy = 0.0
    blend = 0.0
    focus = None
    clock = 0
    frames = []
    for t in range(720):
        melee = 150 <= t < 520
        if melee and t > 260:
            px = 120 + 90 * (1 - math.cos((t - 260) * math.tau / 260))     # walks right and back while in melee
        pcx, pcy = px, FLOOR - ph / 2
        if focus is None:
            focus = [pcx, pcy]
        step = 1 / b["MeleeBlendTicks"]
        blend = max(0.0, min(1.0, blend + (step if melee else -step)))
        m = blend * blend * (3 - 2 * blend)
        follow = b["FocusFollow"] + (b["MeleeFocusFollow"] - b["FocusFollow"]) * m
        focus[0] += (pcx - focus[0]) * follow
        focus[1] += (pcy - focus[1]) * follow
        clock += 1
        sway = math.sin(clock * math.tau / b["DriftPeriodX"])
        bob = math.sin(clock * math.tau / b["DriftPeriodY"] + math.pi / 2)
        side = -1 if cx < focus[0] else 1
        near = (focus[0] + side * (pw / 2 + c["MeleeGap"] + w / 2 + sway * c["MeleeSwayX"]),
                focus[1] + ph / 2 - c["MeleeLift"] - h / 2 + bob * c["MeleeBobY"])
        far = (focus[0] + side * c["HoverX"] + sway * c["SwayX"], focus[1] - c["HoverY"] + bob * c["BobY"])
        spot = (far[0] + (near[0] - far[0]) * m, far[1] + (near[1] - far[1]) * m)
        mx = c["HoverSpeed"] + (b["MeleeTrackSpeed"] - c["HoverSpeed"]) * m
        close = c["HoverApproach"] + (b["MeleeTrackApproach"] - c["HoverApproach"]) * m
        turn = c["HoverAccel"] + (b["MeleeTrackAccel"] - c["HoverAccel"]) * m
        dx, dy = spot[0] - cx, spot[1] - cy
        dist = math.hypot(dx, dy)
        want = (dx / dist * min(mx, dist * close), dy / dist * min(mx, dist * close)) if dist > 1 else (0.0, 0.0)
        vx += (want[0] - vx) * turn
        vy += (want[1] - vy) * turn
        cx += vx
        cy += vy
        if t % STEP:
            continue
        img = backdrop()
        f.draw(img, f.idle(t), cx, cy + h / 2)
        put_player(img, px, FLOOR, 0, cx > px)
        d = ImageDraw.Draw(img)
        d.rectangle([10, 34, 110, 40], outline=(195, 200, 205, 255))
        d.rectangle([11, 35, 11 + int(98 * m), 39], fill=(255, 199, 90, 255))
        label(img, "FLOATY BOSS: " + ("the player holds a gun: ranged hover" if not melee else "the player holds a sword: into melee reach over %.1f s, then slow tracking" % (b["MeleeBlendTicks"] / 60)), 6, 4)
        label(img, "melee blend %.2f  speed %.1f px/tick" % (m, math.hypot(vx, vy)), 120, 30)
        frames.append(img)
    save_gif(frames, path, scale=1)


def items_png(path):
    banners = sorted(os.listdir(os.path.join(ROOT, "Content/Banners/Items")))
    ims = [("", S.load("Content/Banners/Items/" + n)) for n in banners if n.endswith(".png")]
    tile = S.load("Content/Banners/EnemyBannerTile.png")
    extras = [("Cogpunk slot (locked)", None), ("", S.load("Content/Equipment/CogpunkSlot_Back.png")),
              ("", S.load("Content/Equipment/CogpunkSlot_Lock.png")), ("", S.load("Content/Equipment/CogpunkSlot_Cog.png")),
              ("Demon Table", S.load("Content/Research/Altar/DemonTable.png")), ("", S.load("Content/Research/Altar/DemonTableTile.png")),
              ("Who is he?", S.load("Content/Research/UI/WhoIsHe.png")), ("Tearstone", S.load("Content/Underground/Items/Tearstone.png"))]
    scale, gap = 2, 8
    rows = [ims, [("", tile)], [e for e in extras if e[1] is not None]]
    widths = [sum(im.width * scale + gap for _, im in row) + gap for row in rows]
    heights = [max(im.height for _, im in row) * scale + 2 * gap for row in rows]
    w = max(widths)
    out = Image.new("RGBA", (w, sum(heights) * 2 + 60), (0, 0, 0, 255))
    y = 0
    for bg in ((30, 30, 36), (196, 214, 232)):
        for row, hh in zip(rows, heights):
            band = Image.new("RGBA", (w, hh), bg + (255,))
            out.alpha_composite(band, (0, y))
            x = gap
            for _, im in row:
                big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
                out.alpha_composite(big, (x, y + gap))
                x += big.width + gap
            y += hh
    label(out, "23 enemy banners (items, then the placed tile styles); the Cogpunk slot (back, lock, cog), the Demon Table, Who is he?, the Tearstone", 6, y + 8)
    out.save(path)
    print("wrote", path)


SCENES = {
    "spells": ("boss-fungimancer-spells.gif", spells_gif),
    "burp": ("boss-fungimancer-burp-orbit.gif", burp_gif),
    "channel": ("boss-fungimancer-channel.gif", channel_gif),
    "death": ("boss-fungimancer-death.gif", death_gif),
    "toadstool": ("mob-toadstool.gif", toadstool_gif),
    "lizard": ("mob-crystal-lizard.gif", lizard_gif),
    "driller": ("mob-driller.gif", driller_gif),
    "slowmo": ("combat-crit-slowmo.gif", slowmo_gif),
    "floaty": ("boss-floaty-melee.gif", floaty_gif),
    "items": ("items-alpha-batch.png", items_png),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    a = ap.parse_args()
    os.chdir(ROOT)
    os.makedirs(a.out, exist_ok=True)
    names = a.only.split(",") if a.only else list(SCENES)
    for n in names:
        fname, fn = SCENES[n]
        fn(os.path.join(a.out, "2026-11-25_" + fname))


if __name__ == "__main__":
    main()
