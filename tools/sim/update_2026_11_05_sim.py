"""D5 proofs for the request of 2026-11-05: the Sheriff's Revolver redrawn as a polished brass magnum (precise left click,
the 0.33 s fan, ricochets +50%, smoke trails), the Cog-launcher, and the reworked Cursed Conductor (bigger, no contact
damage, passive trains from the screen edge, the lantern's cursed bolts and their ghosts, the 3-lap loop, the whistle's
immune waves, the explosion of his death), built from the real sprite sheets, the generated rig data and the constants
parsed out of the C# files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_05_sim.py --out docs/media [--only revolver,cogs,intro,passive,lantern,loop,whistle,death,sprites]

Writes:
    2026-11-05_weapon-sheriffs-revolver.gif   the magnum's six aimed shots (within 1 degree; thin smoke trails that fade in
                                              0.5 s), ricochets onto a second enemy for 1.5x, the six-round count and the
                                              1.5 s reload, then the right-click fan: six in 20 ticks for 20 steam.
    2026-11-05_weapon-cog-launcher.gif        cogs fired across a room (7 steam each): one passes through two enemies,
                                              rebounds off the wall and cuts back through them for +50%; a cog breaks on its
                                              fourth wall.
    2026-11-05_boss-cursed-conductor-intro.gif    the bigger, darker Conductor materializes and tips his cap under the title
                                              card, then his main attack: a wide fan of straight cursed bolts.
    2026-11-05_boss-cursed-conductor-passive.gif  half scale, one 1920x1080 screen: the passive trains every 3 s with no
                                              gesture of his: an Express from the screen edge away from him that vanishes
                                              at the edge towards him, a Dive from the top, a Dive from the bottom (1 s
                                              warnings: the track and the rift it bursts out of).
    2026-11-05_boss-cursed-conductor-lantern.gif  a bolt curses the player (6 s), two strike the floor: rifts open and ghosts
                                              rise from them 1.5 s later and drift after the player; a cursed player hit
                                              by a wagon takes half the train's damage, +25%.
    2026-11-05_boss-cursed-conductor-loop.gif     half scale: the ring of lights round a player, the train in and round for
                                              3 laps, two ghosts rising on opposite sides inside the ring every lap.
    2026-11-05_boss-cursed-conductor-whistle.gif  half scale: at 70% he stops and shrieks, immune for 7 s: the wave express
                                              left to right then right to left (each shown first as a line of lights),
                                              ghosts rising out of the ground one a second.
    2026-11-05_boss-cursed-conductor-death.gif    he slumps, his lantern and eyes go out, the last train comes for him and
                                              blows him to bits, "Defeated".
    2026-11-05_boss-cursed-conductor-sprites.png  his frames (three planes and glow, on a dark and a light ground), the
                                              train's headings, the rift, the curse's icon, the bits, the bolt, the
                                              Cog-launcher and its cog, the magnum and its bullet.

Leaves out: lighting (the town is drawn dim, the ghosts at full brightness), the planes' parallax, vanilla's player
physics (approximated as in update_2026_11_03b_sim), defense, netcode. His ghosts use vanilla's graveyard Ghost sprite in
game; vanilla's art is not in this repository, so the proofs draw a plain stand-in ghost. Numbers are Expert's.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, consts, load, player_sprite  # noqa: E402
from update_2026_11_03_sim import Planes, numbers  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, PLAYER_W, PLAYER_H  # noqa: E402
from update_2026_11_04_sim import town_backdrop, KD, EMBER, HURT, STEAM, BRASS  # noqa: E402
from update_2026_11_04b_sim import Bullet, Conductor, heading_frame, faded, mist, draw_mist, step_mist, title  # noqa: E402
from smoke import Smoke  # noqa: E402

BOSS = "Content/Bosses/CursedConductor/"
TOWN = "Content/OldBrassTown/"
MECH = "Content/Mechanist/Weapons/"
KC = consts(BOSS + "CursedConductor.cs", BOSS + "CursedConductor.Visuals.cs", BOSS + "CursedConductorRigData.cs")
KT = consts(BOSS + "Projectiles/GhostTrain.cs")
KF = consts(BOSS + "Projectiles/ConductorFlame.cs")
KG = consts(BOSS + "NPCs/ConductorGhost.cs")
KU = consts(BOSS + "Buffs/ConductorCurse.cs")
KR = consts(TOWN + "Weapons/SheriffsRevolver.cs", TOWN + "Weapons/SheriffsRevolverPlayer.cs", TOWN + "Weapons/SheriffsBullet.cs",
            TOWN + "Weapons/RevolverCylinderLayer.cs")
KL = consts(MECH + "CogLauncher.cs", MECH + "CogLauncherCog.cs")
TWO_PI = 2 * math.pi
KC["LapTicks"] = int(TWO_PI * KC["LoopRadius"] / KC["LoopSpeed"])
KC["LoopRun"] = int(KT["LoopLaps"] * KC["LapTicks"])
KC["LoopTicks"] = KC["LoopTelegraph"] + KC["LoopEnter"] + KC["LoopRun"] + int(KT["Length"] / KC["LoopSpeed"]) + 10
GHOST = (140, 201, 176)
CURSE = (118, 220, 162)
IMMUNITY = 40


def boss_planes():
    b = Conductor()
    return b


# ================================================================================================
# Shared: the ghost train (GhostTrain.cs step for step), bolts, rifts, stand-in ghosts
# ================================================================================================
class Train:
    ENGINE = [load(BOSS + "Projectiles/GhostTrain.png"), load(BOSS + "Projectiles/GhostTrain_Glow.png")]
    CAR = [load(BOSS + "Projectiles/GhostTrain_Car.png"), load(BOSS + "Projectiles/GhostTrain_CarGlow.png")]

    def __init__(self, route, pos, vel, ai1, ai2=0.0):
        self.route, self.ai1, self.ai2 = route, ai1, ai2
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.age = 0
        self.started = False
        self.circling = self.leaving = False
        self.time_left = KT["MaxLifetime"]
        self.hit_segment = -1

    def begin(self):
        self.started = True
        self.sx, self.sy = self.x, self.y
        self.speed = max(1.0, math.hypot(self.vx, self.vy))
        self.ux, self.uy = self.vx / self.speed, self.vy / self.speed
        n = KT["TrailLength"]
        self.trail = [None] * n
        for i in range(n):
            self.trail[(n - i) % n] = (self.sx - self.ux * self.speed * i, self.sy - self.uy * self.speed * i)
        self.head, self.filled = 0, n
        self.span = max(0.0, self.ai1)
        if self.route == "loop":
            self.cx, self.cy = self.ai1, self.ai2
            self.approach = max(0.0, (self.cx - self.sx) * self.ux + (self.cy - self.sy) * self.uy)
            tx, ty = self.sx + self.ux * self.approach, self.sy + self.uy * self.approach
            rx, ry = tx - self.cx, ty - self.cy
            self.radius = max(48.0, math.hypot(rx, ry))
            self.angle = math.atan2(ry, rx)
            cross = rx * self.vy - ry * self.vx
            self.omega = self.speed / self.radius * (1 if cross >= 0 else -1)
            life = int((self.approach + KT["LoopLaps"] * TWO_PI * self.radius + KT["Length"] + 60 * 16) / self.speed)
        elif self.route == "farewell":
            life = KT["FarewellTicks"]
        elif self.route == "wave":
            self.phase = self.ai2
            self.base_y = self.sy - KT["WaveAmplitude"] * math.sin(self.phase)
            life = int((self.span + KT["Length"] + KT["FadeIn"]) * 1.5 / self.speed) + 4
        else:
            life = int((self.span + KT["Length"] + KT["FadeIn"]) / self.speed) + 4
        self.time_left = max(30, min(KT["MaxLifetime"], life))

    def update(self):
        if not self.started:
            self.begin()
        self.age += 1
        if self.route == "loop" and not self.leaving:
            travelled = self.age * self.speed
            if self.circling or travelled >= self.approach:
                self.circling = True
                a = self.angle + self.omega * (self.age - self.approach / self.speed)
                if (travelled - self.approach) / self.radius >= KT["LoopLaps"] * TWO_PI:
                    self.leaving = True
                    s = (1 if self.omega > 0 else -1) * self.speed
                    self.vx, self.vy = -math.sin(a) * s, math.cos(a) * s
                else:
                    self.vx = self.cx + math.cos(a) * self.radius - self.x
                    self.vy = self.cy + math.sin(a) * self.radius - self.y
        elif self.route == "wave":
            run = self.age * self.speed
            tx = self.sx + self.ux * run
            ty = self.base_y + KT["WaveAmplitude"] * math.sin(self.phase + TWO_PI * run / KT["WaveLength"])
            self.vx, self.vy = tx - self.x, ty - self.y
        elif self.route == "farewell" and self.age * self.speed >= self.ai1:
            a = math.atan2(self.vy, self.vx)
            diff = (-math.pi / 2 - a + math.pi) % TWO_PI - math.pi
            a += max(-KT["FarewellTurn"], min(KT["FarewellTurn"], diff))
            self.vx, self.vy = math.cos(a) * self.speed, math.sin(a) * self.speed
        n = KT["TrailLength"]
        self.head = (self.head + 1) % n
        self.trail[self.head] = (self.x + self.vx, self.y + self.vy)
        self.x += self.vx
        self.y += self.vy
        self.time_left -= 1
        return self.time_left > 0

    def back(self, distance):
        n = KT["TrailLength"]
        idx = self.head
        if distance <= 0:
            return self.trail[idx]
        acc = 0.0
        for _ in range(self.filled - 1):
            prev = (idx - 1) % n
            a, b = self.trail[idx], self.trail[prev]
            seg = math.hypot(a[0] - b[0], a[1] - b[1])
            if acc + seg >= distance:
                f = (distance - acc) / seg if seg > 0.001 else 0.0
                return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            acc += seg
            idx = prev
        return self.trail[idx]

    def segment(self, k):
        back = 0.0 if k == 0 else KT["FirstSpacing"] + (k - 1) * KT["Spacing"]
        mid = self.back(back)
        ahead, behind = self.back(max(0.0, back - 12)), self.back(back + 12)
        hx, hy = ahead[0] - behind[0], ahead[1] - behind[1]
        n = math.hypot(hx, hy) or 1.0
        return mid, (hx / n, hy / n)

    def visibility(self, p):
        if self.route not in ("express", "dive", "wave"):
            return 1.0
        if self.route == "wave":
            s = (p[0] - self.sx) * (1 if self.ux >= 0 else -1)
        else:
            s = (p[0] - self.sx) * self.ux + (p[1] - self.sy) * self.uy
        return max(0.0, min(1.0, s / KT["FadeIn"])) * max(0.0, min(1.0, (self.span - s) / KT["FadeOut"]))

    def hits(self, box):
        if self.route == "farewell" or self.age <= 2:
            return -1
        for k in range(int(KT["Cars"]) + 1):
            mid, (hx, hy) = self.segment(k)
            if self.visibility(mid) < KT["Solid"]:
                continue
            half = (KT["EngineLength"] if k == 0 else KT["CarLength"]) * 0.5 - 8
            thick = KT["EngineThickness"] if k == 0 else KT["CarThickness"]
            for s in range(9):
                u = -half + 2 * half * s / 8
                px, py = mid[0] + hx * u, mid[1] + hy * u
                if box[0] - thick / 2 < px < box[2] + thick / 2 and box[1] - thick / 2 < py < box[3] + thick / 2:
                    return k
        return -1

    def fade(self):
        return max(0.0, min(1.0, self.time_left / KT["FadeTicks"])) if self.route == "farewell" else 1.0

    def draw(self, img):
        f = self.fade()
        for k in range(int(KT["Cars"]), -1, -1):
            mid, (hx, hy) = self.segment(k)
            vis = self.visibility(mid) * f
            if vis <= 0.02:
                continue
            frame, flip = heading_frame(hx, hy)
            cell = KC["EngineCell"] if k == 0 else KC["CarCell"]
            sheets = Train.ENGINE if k == 0 else Train.CAR
            for j, sheet in enumerate(sheets):
                c = sheet.crop((0, frame * (cell + 2), cell, frame * (cell + 2) + cell))
                if flip:
                    c = c.transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(faded(c, (KT["Opacity"] if j == 0 else 1.0) * vis), (int(round(mid[0] - cell / 2)), int(round(mid[1] - cell / 2))))


class Bolt:
    SHEET = load(BOSS + "Projectiles/ConductorFlame.png")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy, self.t = x, y, vx, vy, 0
        self.landed = False

    def update(self, ground, walls=()):
        self.x += self.vx
        self.y += self.vy
        self.t += 1
        if self.y >= ground - 6 or any(abs(self.x - w) < 6 for w in walls):
            self.landed = True
            return False
        return self.t < KF["Lifetime"]

    def draw(self, img):
        cell = KC["FlameCell"]
        f = (self.t // KF["FrameTicks"]) % KC["FlameFrames"]
        img.alpha_composite(Bolt.SHEET.crop((0, f * (cell + 2), cell, f * (cell + 2) + cell)), (int(self.x - cell / 2), int(self.y - cell / 2)))


def throw_bolts(boss, target, count):
    fx, fy = boss.point("Throw")
    dx, dy = target[0] - fx, target[1] - fy
    n = math.hypot(dx, dy) or 1.0
    ax, ay = dx / n * KC["BoltSpeed"], dy / n * KC["BoltSpeed"]
    out = []
    for k in range(count):
        turn = (k - (count - 1) * 0.5) * KC["BoltSpread"]
        c, s = math.cos(turn), math.sin(turn)
        out.append(Bolt(fx, fy, ax * c - ay * s, ax * s + ay * c))
    return out


RIFT = load(BOSS + "Projectiles/GhostRift.png")
RAIL = load(BOSS + "Projectiles/GhostTrain_Rail.png")
CURSE_ICON = load(BOSS + "Buffs/ConductorCurse.png")


class Rift:
    def __init__(self, x, y, delay):
        self.x, self.y, self.delay, self.t = x, y, delay, 0

    def update(self):
        self.t += 1
        return self.t < self.delay

    def draw(self, img):
        cell = KC["RiftCell"]
        k = max(0, min(KC["RiftFrames"] - 1, int(self.t / self.delay * KC["RiftFrames"])))
        img.alpha_composite(RIFT.crop((0, k * (cell + 2), cell, k * (cell + 2) + cell)), (int(self.x - cell / 2), int(self.y - cell / 2)))


def ghost_sprite(flip=False):
    """A plain stand-in for vanilla's graveyard Ghost (its art is not in this repository): a pale hooded wisp, 24x44."""
    im = Image.new("RGBA", (24, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([2, 2, 21, 24], fill=(226, 232, 238, 170))
    d.polygon([(2, 14), (22, 14), (20, 40), (14, 34), (10, 42), (6, 34), (2, 40)], fill=(226, 232, 238, 150))
    d.rectangle([7, 10, 9, 13], fill=(20, 24, 32, 220))
    d.rectangle([14, 10, 16, 13], fill=(20, 24, 32, 220))
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


class Ghost:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.age = 0
        self.flash = 0

    def update(self, target):
        self.age += 1
        dx, dy = target[0] - self.x, target[1] - self.y
        self.vx = max(-KG["MaxSpeedX"], min(KG["MaxSpeedX"], self.vx + (1 if dx > 0 else -1) * KG["AccelX"]))
        self.vy = max(-KG["MaxSpeedY"], min(KG["MaxSpeedY"], self.vy + (1 if dy - 8 > 0 else -1) * KG["AccelY"]))
        self.x += self.vx
        self.y += self.vy

    def alpha(self):
        a = max(KG["Alpha"], 255 - int(self.age * (255 - KG["Alpha"]) / KG["FadeInTicks"]))
        return (255 - a) / 255.0

    def draw(self, img):
        img.alpha_composite(faded(ghost_sprite(self.vx > 0), self.alpha() * 1.6), (int(self.x - 12), int(self.y - 22)))

    def box(self):
        return (self.x - 12, self.y - 22, self.x + 12, self.y + 22)


def strength(t, length):
    if t <= 0:
        return 0.0
    if t <= length:
        return max(0.0, min(1.0, t / (length / 3.0)))
    return max(0.0, min(1.0, 1.0 - (t - length) / 12.0))


def rail_piece(kind, alpha):
    cell = KC["RailCell"]
    k = {"level": 0, "upright": 1, "ring": 2}[kind]
    return faded(RAIL.crop((0, k * (cell + 2), cell, k * (cell + 2) + cell)), 0.85 * alpha)


def draw_track(img, entry, exit_, kind, alpha):
    """The passive train's track between its entry and exit (every 16 px), and the rift it comes out of."""
    if alpha <= 0:
        return
    piece = rail_piece(kind, alpha)
    cell = KC["RailCell"]
    dx, dy = exit_[0] - entry[0], exit_[1] - entry[1]
    n = math.hypot(dx, dy) or 1.0
    s = 0.0
    while s <= n:
        img.alpha_composite(piece, (int(round(entry[0] + dx / n * s - cell / 2)), int(round(entry[1] + dy / n * s - cell / 2))))
        s += 16
    k = max(0, min(KC["RiftFrames"] - 1, int(alpha * KC["RiftFrames"])))
    rc = KC["RiftCell"]
    img.alpha_composite(faded(RIFT.crop((0, k * (rc + 2), rc, k * (rc + 2) + rc)), alpha), (int(entry[0] - rc / 2), int(entry[1] - rc / 2)))


def idle_frame(tick):
    return KC["Idle"] + (tick // KC["IdleFrameTicks"]) % KC["IdleFrames"]


def throw_frame(k):
    return KC["Throw"] + (0 if k < 12 else 1 if k < KC["ThrowWindup"] else 2 if k < KC["ThrowWindup"] + KC["ThrowRelease"] else 3)


def half(img):
    return img.resize((img.width // 2, img.height // 2), Image.NEAREST)


# ================================================================================================
# The Sheriff's Revolver (the magnum)
# ================================================================================================
def scene_revolver(out, font):
    W, H, G = 860, 300, 262
    WALL = 800
    bg = town_backdrop(W, H, G, wall_x=WALL, wall_right=True)
    gif = Gif(font, (W, H), scale=1.0)
    bandit = Planes(TOWN + "NPCs/BrassBandit", KD)
    gun = load(TOWN + "Weapons/SheriffsRevolver.png")
    bullet_sheet = load(TOWN + "Weapons/SheriffsBullet.png")
    pips = load(TOWN + "Weapons/SheriffsRevolver_Round.png")
    smoke = Smoke()
    targets = [{"x": x, "y": G - KD["Height"] / 2, "flash": 0} for x in (470, 612, 720)]
    p = Player(130, G)
    rounds, reload, steam = KR["Chambers"], 0, 100
    bullets, pops, notes = [], [], []
    muzzle_y = G - 30
    shots = [(20, "shot", (470, G - 24)), (43, "shot", (WALL, G - 150)), (66, "shot", (612, G - 24)),
             (89, "shot", (470, G - 18)), (112, "shot", (720, G - 26)), (135, "shot", (420, G + 6))]
    fan_start = 260
    for k in range(KR["Chambers"]):
        shots.append((fan_start + k * KR["BurstInterval"], "fan", (612, G - 24)))
    total = fan_start + 30 + KR["ReloadTicks"] + 40
    rng = random.Random(4)
    spread = math.radians(KR["AimSpread"])
    for tick in range(total):
        for (t0, kind, aim) in shots:
            if t0 == tick and rounds > 0 and reload == 0:
                if kind == "fan" and t0 == fan_start:
                    steam -= KR["BurstSteamCost"]
                    notes.append((tick, "right click: the cylinder fanned, a shot every %d ticks: all six inside %.2f s, for %d steam"
                                  % (KR["BurstInterval"], 5 * KR["BurstInterval"] / 60, KR["BurstSteamCost"])))
                mx, my = p.x + KR["MuzzleDistance"], muzzle_y
                ang = math.atan2(aim[1] - my, aim[0] - mx)
                ang += rng.uniform(-KR["BurstSpread"], KR["BurstSpread"]) if kind == "fan" else rng.uniform(-spread, spread)
                bullets.append(Bullet(mx, my, math.cos(ang) * KR["ShotSpeed"], math.sin(ang) * KR["ShotSpeed"]))
                rounds -= 1
                if rounds == 0:
                    reload = KR["ReloadTicks"]
                    notes.append((tick, "six shots: the reload (%.1f s) starts at once" % (KR["ReloadTicks"] / 60)))
        if tick == 22:
            notes.append((tick, "left click: within %d degree of the aim; a thin smoke trail fades in half a second" % KR["AimSpread"]))
        if reload > 0:
            reload -= 1
            if reload == 0:
                rounds = KR["Chambers"]
        for b in bullets:
            for _ in range(2):
                if not b.alive:
                    break
                ox, oy = b.x, b.y
                b.x += b.vx
                b.y += b.vy
                smoke.add((ox, oy), (b.x, b.y), tick)
                b.life -= 1
                wall = b.x >= WALL - 4
                floor = b.y >= G - 2
                if wall or floor or b.x < 0 or b.y < 0 or b.life <= 0:
                    if b.bounces >= 1 or b.life <= 0 or b.x < 0 or b.y < 0:
                        b.alive = False
                        break
                    fall = (-b.vx, b.vy) if wall else (b.vx, -b.vy)
                    b.x = min(b.x, WALL - 5.0)
                    b.y = min(b.y, G - 3.0)
                    b.bounce(targets, None, fall)
                    continue
                for t in targets:
                    if id(t) in b.hit:
                        continue
                    box = (t["x"] - KD["Width"] / 2, G - KD["Height"], t["x"] + KD["Width"] / 2, G)
                    if overlaps((b.x - 4, b.y - 4, b.x + 4, b.y + 4), box):
                        b.hit.add(id(t))
                        t["flash"] = 6
                        ricochet = b.bounces >= 1
                        dmg = int(KR["Damage"] * (KR["RicochetBonus"] if ricochet else 1.0))
                        pops.append((tick, t["x"] - 10, G - KD["Height"] - 22, str(dmg), (255, 236, 140) if ricochet else BRASS))
                        if ricochet:
                            b.alive = False
                            notes.append((tick, "a ricochet onto an enemy: x%.1f (%d)" % (KR["RicochetBonus"], dmg)))
                        else:
                            b.bounce(targets, t, (-b.vx, -b.vy))
                        break
        bullets = [b for b in bullets if b.alive]
        for t in targets:
            t["flash"] = max(0, t["flash"] - 1)
        if tick % 3:
            continue
        img = bg.copy()
        for t in targets:
            bandit.draw(img, KD["Walk"], (t["x"], G), False)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        img.alpha_composite(gun, (int(p.x - 2), int(muzzle_y - round(gun.height * 0.57))))   # the grip at the hand, any size
        loaded = int((1.0 - reload / KR["ReloadTicks"]) * KR["Chambers"]) if reload > 0 else rounds
        mid = (KR["Chambers"] - 1) / 2.0
        for k in range(KR["Chambers"]):
            px = p.x + (k - mid) * KR["Spacing"] - KR["Size"] / 2
            py = p.y - PLAYER_H - KR["Rise"] + abs(k - mid) * 2 - KR["Size"] / 2
            src = pips.crop((0, (0 if k < loaded else 1) * KR["Stride"], KR["Size"], (0 if k < loaded else 1) * KR["Stride"] + KR["Size"]))
            img.alpha_composite(faded(src, 0.75 if reload > 0 else 1.0), (int(round(px)), int(round(py))))
        smoke.draw(img, tick)
        for b in bullets:
            a = math.atan2(b.vy, b.vx)
            f = int(round((a % TWO_PI) / TWO_PI * KR["Headings"])) % KR["Headings"]
            img.alpha_composite(bullet_sheet.crop((0, f * 16, 14, f * 16 + 14)), (int(b.x - 7), int(b.y - 7)))
        gif.text(img, (10, 8), "Sheriff's Revolver, a polished brass magnum: %d damage, %d use time, 6%% crit; ricochets x%.1f; "
                 "%d rounds, %.1f s reload" % (KR["Damage"], KR["UseTime"], KR["RicochetBonus"], KR["Chambers"], KR["ReloadTicks"] / 60))
        gif.text(img, (10, 26), "steam %d   rounds %s" % (steam, ("reloading %.1f s" % (reload / 60)) if reload else str(rounds)),
                 fill=EMBER if reload else STEAM)
        numbers(gif, img, pops, tick)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 70]
        if live:
            gif.text(img, (10, 44), live[-1], fill=BRASS)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Cog-launcher
# ================================================================================================
def scene_cogs(out, font):
    W, H, G = 860, 300, 262
    LEFT, RIGHT, TOP = 40, 820, 60
    bg = town_backdrop(W, H, G, wall_x=RIGHT, wall_right=True)
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, LEFT, G], fill=(70, 54, 40, 255))
    d.rectangle([0, 0, W, TOP], fill=(70, 54, 40, 255))
    gif = Gif(font, (W, H), scale=1.0)
    bandit = Planes(TOWN + "NPCs/BrassBandit", KD)
    launcher = load(MECH + "CogLauncher.png")
    cog_sheet = load(MECH + "CogLauncherCog.png")
    targets = [{"x": x, "flash": 0} for x in (430, 540)]
    p = Player(110, G)
    steam = 100
    cogs, pops, notes = [], [], []
    muzzle = (p.x + KL["MuzzleDistance"], G - 34)
    fire_at = {10: (RIGHT, G - 34), 70: (RIGHT, G - 140), 150: (600, TOP)}
    total = 300
    for tick in range(total):
        if tick in fire_at:
            aim = fire_at[tick]
            a = math.atan2(aim[1] - muzzle[1], aim[0] - muzzle[0])
            cogs.append({"x": muzzle[0], "y": muzzle[1], "vx": math.cos(a) * KL["ShotSpeed"], "vy": math.sin(a) * KL["ShotSpeed"],
                         "bounces": 0, "pen": KL["Pierce"] + 1, "hit": {}, "frame": 0, "t": 0, "alive": True})
            steam -= KL["Cost"]
            if tick == 10:
                notes.append((tick, "%d steam a shot: the cog flies straight (no drop), passes through %d enemies" % (KL["Cost"], KL["Pierce"])))
            if tick == 150:
                notes.append((tick, "a cog rebounds off %d walls; the next one breaks it" % KL["MaxBounces"]))
        for c in cogs:
            if not c["alive"]:
                continue
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            c["t"] += 1
            if c["t"] % KL["SpinTicks"] == 0:
                c["frame"] = (c["frame"] + (1 if c["vx"] >= 0 else KL["SpinFrames"] - 1)) % KL["SpinFrames"]
            wall = c["x"] >= RIGHT - 9 or c["x"] <= LEFT + 9
            ceil_floor = c["y"] <= TOP + 9 or c["y"] >= G - 9
            if wall or ceil_floor:
                if c["bounces"] >= KL["MaxBounces"] or c["t"] >= KL["Lifetime"]:
                    c["alive"] = False
                    notes.append((tick, "its fourth wall: the cog breaks"))
                    continue
                c["bounces"] += 1
                if wall:
                    c["vx"] = -c["vx"]
                if ceil_floor:
                    c["vy"] = -c["vy"]
                c["x"] = max(LEFT + 10, min(RIGHT - 10, c["x"]))
                c["y"] = max(TOP + 10, min(G - 10, c["y"]))
            for t in targets:
                box = (t["x"] - KD["Width"] / 2, G - KD["Height"], t["x"] + KD["Width"] / 2, G)
                key = id(t)
                last = c["hit"].get(key)
                if overlaps((c["x"] - 9, c["y"] - 9, c["x"] + 9, c["y"] + 9), box) and (last is None or c["t"] - last >= KL["HitCooldown"]):
                    again = last is not None
                    c["hit"][key] = c["t"]
                    dmg = int(KL["Damage"] * (KL["RepeatBonus"] if again else 1.0))
                    t["flash"] = 6
                    pops.append((tick, t["x"] - 10, G - KD["Height"] - 22, str(dmg), (255, 236, 140) if again else BRASS))
                    if again:
                        notes.append((tick, "back through an enemy it already cut: +%d%% (%d)" % (round((KL["RepeatBonus"] - 1) * 100), dmg)))
                    c["pen"] -= 1
                    if c["pen"] <= 0:
                        c["alive"] = False
                    break
        if tick % 3:
            continue
        img = bg.copy()
        for t in targets:
            bandit.draw(img, KD["Walk"], (t["x"], G), False)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        img.alpha_composite(launcher, (int(p.x - 8), int(G - 44)))
        cell = KL["Cell"]
        for c in cogs:
            if c["alive"]:
                f = c["frame"]
                img.alpha_composite(cog_sheet.crop((0, f * (cell + 2), cell, f * (cell + 2) + cell)), (int(c["x"] - cell / 2), int(c["y"] - cell / 2)))
        gif.text(img, (10, 8), "Cog-launcher (Mechanist): %d damage, %d use time, 5%% crit, %d steam a shot; pierces %d, rebounds off %d walls, "
                 "+%d%% on a repeat hit" % (KL["Damage"], KL["UseTime"], KL["Cost"], KL["Pierce"], KL["MaxBounces"],
                                           round((KL["RepeatBonus"] - 1) * 100)), )
        gif.text(img, (10, 26), "steam %d" % steam)
        numbers(gif, img, pops, tick)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 70]
        if live:
            gif.text(img, (10, TOP + 6), live[-1], fill=BRASS)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Cursed Conductor
# ================================================================================================
def place_boss(boss, target, side):
    boss.x = target[0] + side * KC["HoverOffsetX"]
    boss.y = target[1] + KC["HoverOffsetY"]
    boss.face_target(target[0])


def scene_intro(out, font):
    W, H, G = 760, 460, 420
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    rng = random.Random(7)
    p = Player(220, G)
    place_boss(boss, (p.x, p.y - PLAYER_H / 2), 1)
    parts, bolts, pops = [], [], []
    total = KC["IntroTicks"] + 140
    throw_t = -1
    for tick in range(total):
        intro = tick < KC["IntroTicks"]
        t = tick
        if intro and t < KC["FadeTicks"] and t % 2 == 0:
            mist(parts, boss.x, boss.y, 2, rng)
        if not intro:
            boss.move_toward((p.x + KC["HoverOffsetX"], p.y - PLAYER_H / 2 + KC["HoverOffsetY"]), 2.5)
            if throw_t < 0 and tick >= KC["IntroTicks"] + 20:
                throw_t = 0
            if throw_t >= 0:
                throw_t += 1
                if throw_t == KC["ThrowWindup"]:
                    bolts += throw_bolts(boss, (p.x, p.y - PLAYER_H / 2), KC["Bolts"])
        p.run = 0
        if throw_t == KC["ThrowWindup"] + 6:
            p.jump()
        p.step()
        for b in list(bolts):
            if not b.update(G):
                bolts.remove(b)
        step_mist(parts)
        if tick % 3:
            continue
        img = bg.copy()
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        if intro:
            frame = idle_frame(tick) if (t < KC["TipStart"] or t >= KC["TipEnd"]) else KC["Tip"] + (0 if t < KC["TipRaise"] else 1 if t < KC["TipBow"] else 2)
            alpha = min(1.0, t / KC["FadeTicks"])
        else:
            frame = throw_frame(throw_t) if 0 <= throw_t < KC["ThrowTicks"] else idle_frame(tick)
            alpha = 1.0
        boss.draw(img, frame, alpha)
        draw_mist(img, parts)
        for b in bolts:
            b.draw(img)
        if intro and t >= KC["TitleTick"]:
            title(gif, img, W, 60, "Cursed Conductor", "The Last Stop", min(1.0, (t - KC["TitleTick"]) / 20))
        gif.text(img, (10, 8), "Cursed Conductor (bigger: %dx%d px art cell): %d life, %d defense, no contact damage (Expert)"
                 % (KC["CellWidth"], KC["CellHeight"], KC["ExpertLife"], KC["BaseDefense"]))
        if not intro:
            gif.text(img, (10, 26), "his main attack, every %.1f s: %d straight cursed bolts, %d degrees apart (%d each)" % (
                KC["LanternInterval"] / 60, KC["Bolts"], round(math.degrees(KC["BoltSpread"])), KC["BoltDamage"]), fill=CURSE)
        gif.push(img)
    gif.save(out)


def scene_passive(out, font):
    """Half scale: one 1920x1080 screen round the player; the boss on the right."""
    W, H, G = 1920, 1080, 980
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W // 2, H // 2), scale=1.0)
    boss = Conductor()
    p = Player(W / 2, G)
    place_boss(boss, (p.x, p.y - PLAYER_H / 2), 1)
    trains, pops, notes = [], [], []
    interval, tele = KC["PassiveInterval"], KC["PassiveTelegraph"]
    plan = [("express", 1), ("dive", 1), ("dive", -1)]
    pending = None
    clock = interval - tele - 20
    k_plan = 0
    total = 3 * interval + 160
    immune = 0
    for tick in range(total):
        center = (p.x, p.y - PLAYER_H / 2)
        if pending is None and k_plan < len(plan):
            clock += 1
            if clock >= interval - tele:
                kind, d = plan[k_plan]
                k_plan += 1
                if kind == "express":
                    d = 1 if boss.x > center[0] else -1
                    entry, exit_ = (center[0] - d * KC["ScreenHalfWidth"], center[1]), (center[0] + d * KC["ScreenHalfWidth"], center[1])
                    notes.append((tick, "an Express at the farthest fighter: in from the screen edge away from him, out at the edge towards him"))
                else:
                    entry, exit_ = (center[0], center[1] - d * KC["ScreenHalfHeight"]), (center[0], center[1] + d * KC["ScreenHalfHeight"])
                    notes.append((tick, "a Dive %s (50%% each): %.1f s of warning, no gesture of his" % ("from the top" if d > 0 else "from the bottom", tele / 60)))
                pending = [0, kind, entry, exit_]
        if pending is not None:
            pending[0] += 1
            if pending[0] == tele:
                kind, entry, exit_ = pending[1], pending[2], pending[3]
                dx, dy = exit_[0] - entry[0], exit_[1] - entry[1]
                n = math.hypot(dx, dy)
                trains.append(Train(kind, entry, (dx / n * KC["PassiveSpeed"], dy / n * KC["PassiveSpeed"]), n))
                clock = 0
            if pending[0] > tele + 12:
                pending = None
        # the player dodges: jumps the express, steps aside from the dives
        p.run = 0
        if pending is not None and pending[1] == "dive" and pending[0] > 12:
            p.run = 1                                          # the warning seen: step out of the column
        for tr in trains:
            if tr.route == "express" and tr.age < 200:
                lead = (tr.x - p.x) * (1 if tr.vx < 0 else -1)
                if 0 < lead < 260 and p.y >= p.ground:
                    p.jump()
            if tr.route == "dive" and tr.age < 30:
                p.run = 1
        p.step()
        p.x = max(60.0, min(W - 60.0, p.x))
        boss.move_toward((p.x + KC["HoverOffsetX"], p.y - PLAYER_H / 2 + KC["HoverOffsetY"]), KC["HoverSpeed"])
        boss.face_target(p.x)
        box = (p.x - PLAYER_W / 2, p.y - PLAYER_H, p.x + PLAYER_W / 2, p.y)
        for tr in list(trains):
            if not tr.update():
                trains.remove(tr)
                continue
            k = tr.hits(box)
            if k >= 0 and immune <= 0:
                immune = IMMUNITY
                dmg = KC["TrainDamage"] * (1.0 if k == 0 else KT["CarDamageScale"])
                pops.append((tick, p.x - 10, p.y - 80, "%d%s" % (dmg, " (head on)" if k == 0 else " (a wagon)"), HURT))
        immune -= 1
        if tick % 3:
            continue
        img = bg.copy()
        if pending is not None:
            kind, entry, exit_ = pending[1], pending[2], pending[3]
            draw_track(img, entry, exit_, "level" if kind == "express" else "upright", strength(pending[0], tele))
        boss.draw(img, idle_frame(tick))
        img.alpha_composite(player_sprite(flip=p.vx < 0), (int(p.x - 20), int(p.y - 56)))
        for tr in trains:
            tr.draw(img)
        frame = half(img)
        gif.text(frame, (10, 8), "Passive trains (half scale, one 1920x1080 screen): every %.0f s at the farthest fighter (%.0f s below half "
                 "his life), %.1f s of warning (%.1f s below half)" % (interval / 60, KC["EnragedPassiveInterval"] / 60, tele / 60,
                                                                       KC["EnragedPassiveTelegraph"] / 60))
        gif.text(frame, (10, 26), "%d wagons: %d head on, %d from a wagon (Expert)" % (KT["Cars"], KC["TrainDamage"], KC["TrainDamage"] * KT["CarDamageScale"]),
                 fill=GHOST)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 110]
        if live:
            gif.text(frame, (10, 44), live[-1], fill=BRASS)
        numbers(gif, frame, [(t0, x / 2, y / 2, s, c) for (t0, x, y, s, c) in pops], tick)
        gif.push(frame)
    gif.save(out)


def scene_lantern(out, font):
    W, H, G = 900, 460, 420
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    p = Player(300, G)
    place_boss(boss, (p.x, p.y - PLAYER_H / 2), 1)
    bolts, rifts, ghosts, trains, pops, notes = [], [], [], [], [], []
    cursed, immune, throw_t = 0, 0, -1
    total = 420
    for tick in range(total):
        if tick == 10:
            throw_t = 0
        if throw_t >= 0:
            throw_t += 1
            if throw_t == KC["ThrowWindup"]:
                bolts += throw_bolts(boss, (p.x, p.y - PLAYER_H / 2 - 4), KC["Bolts"])
            if throw_t >= KC["ThrowTicks"]:
                throw_t = -1
        if tick == 250:
            trains.append(Train("express", (p.x - KC["ScreenHalfWidth"], p.y - PLAYER_H / 2 - 18), (KC["PassiveSpeed"], 0.0), 2 * KC["ScreenHalfWidth"]))
        p.step()
        box = (p.x - PLAYER_W / 2, p.y - PLAYER_H, p.x + PLAYER_W / 2, p.y)
        for b in list(bolts):
            alive = b.update(G)
            if alive and overlaps((b.x - 6, b.y - 6, b.x + 6, b.y + 6), box):
                cursed = KU["Ticks"]
                pops.append((tick, p.x - 10, p.y - 80, str(KC["BoltDamage"]), HURT))
                notes.append((tick, "a bolt hits: cursed for %d s (+%d%% from the train and the ghosts)" % (KU["Ticks"] / 60, round((KU["DamageTaken"] - 1) * 100))))
                bolts.remove(b)
                continue
            if not alive:
                bolts.remove(b)
                if b.landed:
                    rifts.append(Rift(b.x, G - 14, KC["RiftDelay"]))
                    if len(rifts) == 1:
                        notes.append((tick, "the others strike the floor: a rift opens where each landed..."))
        for r in list(rifts):
            if not r.update():
                rifts.remove(r)
                ghosts.append(Ghost(r.x, r.y - 10))
                notes.append((tick, "...and %.1f s later a ghost rises (%d life, %d contact, slower than vanilla's)" % (KC["RiftDelay"] / 60, KG["ExpertLife"], KG["ExpertDamage"])))
        for g in ghosts:
            g.update((p.x, p.y - PLAYER_H / 2))
        for tr in list(trains):
            if not tr.update():
                trains.remove(tr)
                continue
            k = tr.hits(box)
            if k > 0 and immune <= 0:
                immune = IMMUNITY
                dmg = int(KC["TrainDamage"] * KT["CarDamageScale"] * (KU["DamageTaken"] if cursed > 0 else 1.0))
                pops.append((tick, p.x - 10, p.y - 80, str(dmg), HURT))
                notes.append((tick, "a wagon on a cursed player: %d x %.1f (half the train) x %.2f (cursed) = %d" % (
                    KC["TrainDamage"], KT["CarDamageScale"], KU["DamageTaken"], dmg)))
        immune -= 1
        cursed = max(0, cursed - 1)
        if tick % 3:
            continue
        img = bg.copy()
        boss.draw(img, throw_frame(throw_t) if throw_t >= 0 else idle_frame(tick))
        for r in rifts:
            r.draw(img)
        pl = player_sprite()
        if cursed:
            tint = Image.new("RGBA", pl.size, CURSE + (0,))
            tint.putalpha(pl.split()[3].point(lambda v: int(v * 0.35)))
            pl = pl.copy()
            pl.alpha_composite(tint)
        img.alpha_composite(pl, (int(p.x - 20), int(p.y - 56)))
        if cursed:
            img.alpha_composite(CURSE_ICON, (int(p.x - 16), int(p.y - PLAYER_H - 48)))
        for g in ghosts:
            g.draw(img)
        for b in bolts:
            b.draw(img)
        for tr in trains:
            tr.draw(img)
        gif.text(img, (10, 8), "The lantern (every %.1f s): straight cursed bolts, %d degrees apart; a hit curses for %d s; a bolt that lands "
                 "opens a ghost rift" % (KC["LanternInterval"] / 60, round(math.degrees(KC["BoltSpread"])), KU["Ticks"] / 60))
        gif.text(img, (10, 26), "(the ghost drawn here is a stand-in: in game it is vanilla's graveyard Ghost)", fill=GHOST)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 80]
        if live:
            gif.text(img, (10, 44), live[-1], fill=BRASS)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


def scene_loop(out, font):
    W, H, G = 1920, 1080, 980
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W // 2, H // 2), scale=1.0)
    boss = Conductor()
    p = Player(W / 2 - 100, G)
    place_boss(boss, (p.x, p.y - PLAYER_H / 2), 1)
    locked = (p.x, p.y - PLAYER_H / 2)
    trains, rifts, ghosts, notes = [], [], [], []
    total = KC["LoopTicks"] + 30
    for t in range(total):
        if t == KC["LoopTelegraph"]:
            top = (locked[0], locked[1] - KC["LoopRadius"])
            trains.append(Train("loop", (top[0] + KC["LoopApproach"], top[1]), (-KC["LoopSpeed"], 0.0), locked[0], locked[1]))
            notes.append((t, "the train runs round the trapped player for %d laps (%d px/tick, a bit faster)" % (KT["LoopLaps"], KC["LoopSpeed"])))
        for lap in range(int(KT["LoopLaps"])):
            if t == KC["LoopTelegraph"] + KC["LoopEnter"] + lap * KC["LapTicks"] + 4:
                a = 0.7 + lap * 1.3
                off = (math.cos(a) * KC["LoopGhostRadius"], math.sin(a) * KC["LoopGhostRadius"])
                rifts.append(Rift(locked[0] + off[0], locked[1] + off[1], KC["LoopGhostDelay"]))
                rifts.append(Rift(locked[0] - off[0], locked[1] - off[1], KC["LoopGhostDelay"]))
                notes.append((t, "lap %d: two ghosts rise on opposite sides inside the ring" % (lap + 1)))
        for r in list(rifts):
            if not r.update():
                rifts.remove(r)
                ghosts.append(Ghost(r.x, r.y))
        for g in ghosts:
            g.update((p.x, p.y - PLAYER_H / 2))
        trains = [tr for tr in trains if tr.update()]
        boss.move_toward((p.x + KC["HoverOffsetX"], p.y - PLAYER_H / 2 + KC["HoverOffsetY"]), KC["HoverSpeed"])
        if t % 3:
            continue
        img = bg.copy()
        ring = strength(t, KC["LoopTelegraph"] + KC["LoopEnter"])
        if ring > 0:
            piece = rail_piece("ring", ring)
            cell = KC["RailCell"]
            for k in range(KC["RingDots"]):
                a = TWO_PI * k / KC["RingDots"]
                img.alpha_composite(piece, (int(locked[0] + math.cos(a) * KC["LoopRadius"] - cell / 2), int(locked[1] + math.sin(a) * KC["LoopRadius"] - cell / 2)))
        frame = KC["Call"] + (t // 8) % KC["CallFrames"] if t < KC["LoopTelegraph"] else idle_frame(t)
        boss.draw(img, frame)
        for r in rifts:
            r.draw(img)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        for g in ghosts:
            g.draw(img)
        for tr in trains:
            tr.draw(img)
        out_img = half(img)
        gif.text(out_img, (10, 8), "The Loop (rare: every %d-%d s, a random fighter): %.0f s of ring, then %d laps; no passive train meanwhile, "
                 "and the lantern never aims at the trapped player" % (KC["LoopIntervalMin"] / 60, KC["LoopIntervalMax"] / 60,
                                                                       KC["LoopTelegraph"] / 60, KT["LoopLaps"]))
        live = [s for (t0, s) in notes if 0 <= t - t0 < 110]
        if live:
            gif.text(out_img, (10, 26), live[-1], fill=BRASS)
        gif.push(out_img)
    gif.save(out)


def scene_whistle(out, font):
    W, H, G = 1920, 1080, 980
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W // 2, H // 2), scale=1.0)
    boss = Conductor()
    p = Player(W / 2, G)
    place_boss(boss, (p.x, p.y - PLAYER_H / 2), 1)
    trains, rifts, ghosts, notes = [], [], [], []
    rng = random.Random(9)
    locked, phase = None, 0.0
    total = KC["WhistleTicks"] + 40
    for t in range(total):
        if t == 0:
            notes.append((t, "70%% of his life gone: he stops, shrieks and can't be hurt for %d s" % (KC["WhistleTicks"] / 60)))
        if t in (KC["WavePass1"], KC["WavePass2"]):
            locked = (p.x, p.y - PLAYER_H / 2 - 40)
            phase = rng.uniform(0, TWO_PI)
            notes.append((t, "the wave express: %s (a line of lights first)" % ("left to right" if t == KC["WavePass1"] else "right to left")))
        if t in (KC["WavePass1"] + KC["WaveTelegraph"], KC["WavePass2"] + KC["WaveTelegraph"]):
            d = 1 if t < KC["WavePass2"] else -1
            start = (locked[0] - d * KC["ScreenHalfWidth"], locked[1] + KT["WaveAmplitude"] * math.sin(phase))
            trains.append(Train("wave", start, (d * KC["WaveSpeed"], 0.0), 2 * KC["ScreenHalfWidth"], phase))
        if KC["WavePass1"] <= t < KC["WhistleTicks"] - 30 and (t - KC["WavePass1"]) % KC["GroundGhostInterval"] == 0:
            x = p.x + rng.uniform(-KC["GroundGhostReach"], KC["GroundGhostReach"])
            rifts.append(Rift(x, G - 10, KC["GroundGhostDelay"]))
        for r in list(rifts):
            if not r.update():
                rifts.remove(r)
                ghosts.append(Ghost(r.x, r.y - 20))
        for g in ghosts:
            g.update((p.x, p.y - PLAYER_H / 2))
        trains = [tr for tr in trains if tr.update()]
        if t % 3:
            continue
        img = bg.copy()
        if locked is not None:
            for k, start_t in enumerate((KC["WavePass1"], KC["WavePass2"])):
                local = t - start_t
                if 0 <= local <= KC["WaveTelegraph"] + 12:
                    a = strength(local, KC["WaveTelegraph"])
                    piece = rail_piece("ring", a)
                    cell = KC["RailCell"]
                    d = 1 if k == 0 else -1
                    run = 0.0
                    while run <= 2 * KC["ScreenHalfWidth"]:
                        x = locked[0] - d * KC["ScreenHalfWidth"] + d * run
                        y = locked[1] + KT["WaveAmplitude"] * math.sin(phase + TWO_PI * run / KT["WaveLength"])
                        img.alpha_composite(piece, (int(x - cell / 2), int(y - cell / 2)))
                        run += KC["WaveDot"]
        frame = KC["Whistle"] if t < 8 else KC["Whistle"] + 1 if t < 14 else KC["Call"] + (t // 8) % KC["CallFrames"]
        boss.draw(img, frame if t < KC["WhistleTicks"] else idle_frame(t))
        for r in rifts:
            r.draw(img)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        for g in ghosts:
            g.draw(img)
        for tr in trains:
            tr.draw(img)
        out_img = half(img)
        if t < KC["WhistleTicks"]:
            gif.text(out_img, (int(boss.x / 2) - 30, int(boss.y / 2) - 90), "IMMUNE %.1f s" % ((KC["WhistleTicks"] - t) / 60), fill=CURSE)
        gif.text(out_img, (10, 8), "The whistle (at 70%%, 40%% and 10%% of his life): immune %d s, two wave expresses in %.1f s, a ghost out of the "
                 "ground every %d s" % (KC["WhistleTicks"] / 60, (KC["WhistleTicks"] - KC["WavePass1"]) / 60, KC["GroundGhostInterval"] / 60))
        live = [s for (t0, s) in notes if 0 <= t - t0 < 110]
        if live:
            gif.text(out_img, (10, 26), live[-1], fill=BRASS)
        gif.push(out_img)
    gif.save(out)


def scene_death(out, font):
    W, H, G = 760, 460, 420
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    p = Player(220, G)
    place_boss(boss, (p.x, p.y - PLAYER_H / 2), 1)
    bits = [load(BOSS + "Gores/CursedConductor_Bit%d.png" % k) for k in range(KC["Bits"])]
    shells = [load(BOSS + "Gores/CursedConductor_GoreCap.png"), load(BOSS + "Gores/CursedConductor_GoreLantern.png"),
              load(BOSS + "Gores/CursedConductor_GoreTurbine.png")]
    rng = random.Random(5)
    trains, pieces, parts = [], [], []
    total = KC["DeathTicks"] + 40
    for t in range(total):
        if t == KC["FarewellTick"]:
            trains.append(Train("farewell", (boss.x + KC["FarewellReach"], boss.y), (-KC["FarewellSpeed"], 0.0), KC["FarewellReach"]))
        if t == KC["PickupTick"]:
            for k in range(KC["DeathBits"]):
                im = bits[k % len(bits)].resize((bits[k % len(bits)].width, bits[k % len(bits)].height), Image.NEAREST)
                pieces.append([boss.x + rng.uniform(-40, 40), boss.y + rng.uniform(-60, 60), rng.uniform(-6, 6) - rng.uniform(3, 9),
                               rng.uniform(-6, 6) - rng.uniform(1, 4), im])
            for k, im in enumerate(shells):
                pieces.append([boss.x, boss.y - 40 + k * 30, -rng.uniform(4, 8), -rng.uniform(3, 6), im])
            mist(parts, boss.x, boss.y, 30, rng)
        for pc in pieces:
            pc[0] += pc[2]
            pc[1] += pc[3]
            pc[3] = min(10.0, pc[3] + 0.25)
            if pc[1] > G - 4:
                pc[1] = G - 4
                pc[2] *= 0.6
                pc[3] = 0.0
        trains = [tr for tr in trains if tr.update()]
        step_mist(parts)
        if t % 3:
            continue
        img = bg.copy()
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        boss.pumping = t < KC["PickupTick"]
        if t < KC["PickupTick"]:
            boss.draw(img, KC["Dying"] + min(KC["DyingFrames"] - 1, t // 30))
        else:
            boss.step_smoke(KC["Dying"] + KC["DyingFrames"] - 1, 3)         # the last puffs drift off
            boss.draw_smoke(img, 1.0)
        for pc in pieces:
            img.alpha_composite(pc[4], (int(pc[0]), int(pc[1])))
        draw_mist(img, parts)
        for tr in trains:
            tr.draw(img)
        if t >= KC["DeathTicks"] - 60:
            title(gif, img, W, 80, "Cursed Conductor", "Defeated", min(1.0, (t - (KC["DeathTicks"] - 60)) / 20))
        gif.text(img, (10, 8), "His death: the turbine sputters, the last train comes and blows him to bits (%d pieces, his cap, lantern and turbine)"
                 % KC["DeathBits"])
        gif.push(img)
    gif.save(out)


def sprites_png(out, font):
    gif = Gif(font, (10, 10))
    boss = Conductor()
    cw, ch, cols = KC["CellWidth"], KC["CellHeight"], KC["Columns"]
    frames = KC["Frames"]
    per_row = 9
    rows = (frames + per_row - 1) // per_row
    W = per_row * (cw + 6) + 20
    H = 2 * rows * (ch + 6) + 520
    img = Image.new("RGBA", (W, H), (20, 22, 26, 255))
    for half_k, bgc in enumerate(((44, 48, 58, 255), (150, 180, 210, 255))):
        for f in range(frames):
            x = 10 + (f % per_row) * (cw + 6)
            y = 30 + half_k * rows * (ch + 6) + (f // per_row) * (ch + 6)
            cell = Image.new("RGBA", (cw, ch), bgc)
            for n, sheet in enumerate(boss.sheets):
                if sheet is None:
                    continue
                cell.alpha_composite(boss.cell(sheet, f))
                if n == 1 and boss.rotor is not None:             # the turbine's vanes (frame f's turn), riding the bob
                    k = f % KC["RotorFrames"]
                    rw, rh = KC["RotorWidth"], KC["RotorHeight"]
                    cell.alpha_composite(boss.rotor.crop((0, k * (rh + 2), rw, k * (rh + 2) + rh)),
                                         (KC["OriginX"] + KC["RotorX"], KC["OriginY"] + KC["RotorY"] + boss.bob(f)))
            img.alpha_composite(cell, (x, y))
    gif.text(img, (10, 8), "Cursed Conductor (2026-11-05b: the turbine, the lantern in his near hand): %d frames, %dx%d px cells, two planes + glow + the vanes"
             % (frames, cw, ch))
    y0 = 40 + 2 * rows * (ch + 6)
    x = 10
    for k in range(KC["Headings"]):
        for j, (sheet, cell) in enumerate(((Train.ENGINE[0], KC["EngineCell"]), (Train.CAR[0], KC["CarCell"]))):
            c = sheet.crop((0, k * (cell + 2), cell, k * (cell + 2) + cell))
            img.alpha_composite(c, (x, y0 + j * 126))
        x += 124
    y1 = y0 + 240
    gif.text(img, (10, y1), "rift (a ghost rises from it) | the curse's icon | the bits of his death | the cursed bolt | the turbine's vanes and smoke (the magnum: 2026-11-05_weapons-cog-launcher-magnum.png)")
    x = 10
    rc = KC["RiftCell"]
    for k in range(KC["RiftFrames"]):
        img.alpha_composite(RIFT.crop((0, k * (rc + 2), rc, k * (rc + 2) + rc)).resize((rc * 2, rc * 2), Image.NEAREST), (x, y1 + 24))
        x += rc * 2 + 6
    img.alpha_composite(CURSE_ICON.resize((64, 64), Image.NEAREST), (x + 10, y1 + 24))
    x += 90
    for k in range(KC["Bits"]):
        b = load(BOSS + "Gores/CursedConductor_Bit%d.png" % k)
        img.alpha_composite(b.resize((b.width * 4, b.height * 4), Image.NEAREST), (x, y1 + 30))
        x += b.width * 4 + 8
    fc = KC["FlameCell"]
    for k in range(KC["FlameFrames"]):
        img.alpha_composite(Bolt.SHEET.crop((0, k * (fc + 2), fc, k * (fc + 2) + fc)).resize((fc * 2, fc * 2), Image.NEAREST), (x + 10, y1 + 24))
        x += fc * 2 + 6
    rw, rh = KC["RotorWidth"], KC["RotorHeight"]
    for k in range(KC["RotorFrames"]):
        r = boss.rotor.crop((0, k * (rh + 2), rw, k * (rh + 2) + rh))
        img.alpha_composite(r.resize((rw * 3, rh * 3), Image.NEAREST), (x + 20, y1 + 24 + k * (rh * 3 + 6)))
    sc = KC["SmokeCell"]
    for k in range(KC["SmokeFrames"]):
        pf = boss.smoke_sheet.crop((0, k * (sc + 2), sc, k * (sc + 2) + sc))
        img.alpha_composite(pf.resize((sc * 2, sc * 2), Image.NEAREST), (x + 120 + k * (sc * 2 + 6), y1 + 24))
    turbine = load(BOSS + "Gores/CursedConductor_GoreTurbine.png")
    img.alpha_composite(turbine.resize((turbine.width * 2, turbine.height * 2), Image.NEAREST), (x + 120, y1 + 90))
    x += 120 + KC["SmokeFrames"] * (sc * 2 + 6) + 30
    img.save(out)
    print(out, img.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a.add_argument("--date", default="2026-11-06", help="date prefix of the Cursed Conductor's proofs (his torso turned to the screen 2026-11-06)")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("revolver", lambda: scene_revolver(os.path.join(args.out, "2026-11-05_weapon-sheriffs-revolver.gif"), args.font)),
            # "cogs": the Cog-launcher was redrawn 2026-11-05b; its proof is tools/sim/update_2026_11_05b_sim.py (launcher)
            ("intro", lambda: scene_intro(os.path.join(args.out, "2026-11-05_boss-cursed-conductor-intro.gif"), args.font)),
            ("passive", lambda: scene_passive(os.path.join(args.out, "2026-11-05_boss-cursed-conductor-passive.gif"), args.font)),
            ("lantern", lambda: scene_lantern(os.path.join(args.out, args.date + "_boss-cursed-conductor-lantern.gif"), args.font)),
            ("loop", lambda: scene_loop(os.path.join(args.out, "2026-11-05_boss-cursed-conductor-loop.gif"), args.font)),
            ("whistle", lambda: scene_whistle(os.path.join(args.out, "2026-11-05_boss-cursed-conductor-whistle.gif"), args.font)),
            ("death", lambda: scene_death(os.path.join(args.out, args.date + "_boss-cursed-conductor-death.gif"), args.font)),
            ("sprites", lambda: sprites_png(os.path.join(args.out, args.date + "_boss-cursed-conductor-sprites.png"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
