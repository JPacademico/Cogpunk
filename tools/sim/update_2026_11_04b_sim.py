"""D5 proofs for the second request of 2026-11-04: the Sheriff's Revolver and the Cursed Conductor, built from the real
sprite sheets, the generated rig data and the constants parsed out of the C# files, replayed tick by tick (60 ticks =
1 s).

    python -P tools/sim/update_2026_11_04b_sim.py --out docs/media [--only revolver,intro,trains,loop,death,sprites]

Writes:
    2026-11-04_weapon-sheriffs-revolver.gif     six shots at three stand-in targets: each bullet ricochets once, off the
                                                enemy it hit (towards the nearest other one) or off the wall and the floor
                                                (towards the nearest enemy); the cylinder's six rounds over the player's
                                                head count down, the 1.5 s reload refills them; the right-click fan (six in
                                                0.5 s for 20 steam), then the gun holstered mid-reload: drawn again, the
                                                reload has kept running (swapping never refills it).
    2026-11-04_boss-cursed-conductor-intro.gif  he materializes out of ghost mist, tips his cap under the title card, and
                                                swings his lantern: three lobbed ghost flames.
    2026-11-04_boss-cursed-conductor-trains.gif the Express (the whistle, a ghost track along the player's row; the train
                                                thunders across from his side and is jumped over) and the Dive (the lantern
                                                raised, the track upright over the player's column; the train plunges
                                                through it, the player steps aside).
    2026-11-04_boss-cursed-conductor-loop.gif   the Loop at half scale (the 1x art): the ring of lights round the player,
                                                the train in along its top tangent and round for 1.25 laps, two volleys of
                                                ghost fire thrown in.
    2026-11-04_boss-cursed-conductor-death.gif  he slumps, his lantern and eyes go out, the last train comes for his spirit:
                                                the shell falls apart (cap, head, coat, lantern), the train climbs away and
                                                fades, "Defeated".
    2026-11-04_boss-cursed-conductor-sprites.png every frame of his three planes and glow (on a dark and a light ground), the
                                                train's 9 headings (engine and car, with their glow), the ghost fire, the
                                                track pieces, the bag, the map icon, the whistles and the gores.

Leaves out: lighting (the town is drawn dim, the ghosts at full brightness), the planes' parallax, vanilla's player
physics (approximated as in update_2026_11_03b_sim), defense, netcode, the enraged double passes (in the captions).
Numbers are Expert's.
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
from trashtr0m_loot_sim import Gif, consts, load, player_sprite  # noqa: E402
from update_2026_11_03_sim import Planes, numbers  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, PLAYER_W, PLAYER_H  # noqa: E402
from update_2026_11_04_sim import town_backdrop, KD, EMBER, HURT, STEAM, BRASS  # noqa: E402

BOSS = "Content/Bosses/CursedConductor/"
TOWN = "Content/OldBrassTown/"
KC = consts(BOSS + "CursedConductor.cs", BOSS + "CursedConductor.Visuals.cs", BOSS + "CursedConductorRigData.cs",
            BOSS + "Projectiles/GhostTrain.cs", BOSS + "Projectiles/ConductorFlame.cs")
_KB = consts(BOSS + "CursedConductor.cs")
_KT = consts(BOSS + "Projectiles/GhostTrain.cs")
KC["FadeTicks"] = _KB["FadeTicks"]                                   # the boss's fade-in (the train's own is TrainFade)
KC["TrainFade"] = _KT["FadeTicks"]
KC.setdefault("LoopRun", int(KC["LoopLaps"] * 2 * math.pi * KC["LoopRadius"] / KC["LoopSpeed"]))   # MathHelper.TwoPi
KC.setdefault("LoopTicks", KC["LoopTelegraph"] + KC["LoopEnter"] + KC["LoopRun"] + 6)
_bob = re.search(r"sbyte\[\] Bob = \{([^}]*)\}", open(BOSS + "CursedConductorRigData.cs", encoding="utf-8").read())
BOB = [int(v) for v in _bob.group(1).split(",")] if _bob else []      # each frame's bob (2026-11-05b, the turbine's vanes ride it)


def optional(path):
    return load(path) if os.path.exists(path) else None
KR = consts(TOWN + "Weapons/SheriffsRevolver.cs", TOWN + "Weapons/SheriffsRevolverPlayer.cs", TOWN + "Weapons/SheriffsBullet.cs",
            TOWN + "Weapons/RevolverCylinderLayer.cs")
GHOST = (140, 201, 176)
IMMUNITY = 40


def faded(im, alpha):
    if alpha >= 1.0:
        return im
    r, g, b, a = im.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * max(0.0, alpha)))))


# ================================================================================================
# The Sheriff's Revolver
# ================================================================================================
class Bullet:
    """SheriffsBullet: 2 updates a tick, one ricochet (an enemy it hit, excluded, or a wall/floor), always towards the
    nearest enemy in sight within the bounce range, else a mirror bounce / straight back."""

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.bounces, self.hit, self.alive, self.life = 0, set(), True, KR["Lifetime"]

    def bounce(self, targets, exclude, fallback):
        self.bounces = 1
        speed = math.hypot(self.vx, self.vy)
        best, best_d = None, KR["BounceRange"] ** 2
        for t in targets:
            if t is exclude or id(t) in self.hit:
                continue
            d = (t["x"] - self.x) ** 2 + (t["y"] - self.y) ** 2
            if d < best_d:
                best, best_d = t, d
        hx, hy = (best["x"] - self.x, best["y"] - self.y) if best else fallback
        n = math.hypot(hx, hy) or 1.0
        self.vx, self.vy = hx / n * speed, hy / n * speed
        return best


def scene_revolver(out, font):
    W, H, G = 860, 300, 262
    WALL = 800
    bg = town_backdrop(W, H, G, wall_x=WALL, wall_right=True)
    gif = Gif(font, (W, H), scale=1.0)
    bandit = Planes(TOWN + "NPCs/BrassBandit", KD)
    gun = load(TOWN + "Weapons/SheriffsRevolver.png")
    bullet_sheet = load(TOWN + "Weapons/SheriffsBullet.png")
    pips = load(TOWN + "Weapons/SheriffsRevolver_Round.png")
    targets = [{"x": x, "y": G - KD["Height"] / 2, "flash": 0, "name": n} for x, n in ((470, "A"), (612, "B"), (720, "C"))]
    p = Player(130, G)
    rounds, reload, steam = KR["Chambers"], 0, 100
    held = True
    bullets, pops, notes = [], [], []
    muzzle_y = G - 30
    # the script: (tick, kind, aim point)
    shots = [(20, "shot", (470, G - 24)), (43, "shot", (WALL, G - 150)), (66, "shot", (612, G - 24)),
             (89, "shot", (470, G - 18)), (112, "shot", (720, G - 26)), (135, "shot", (420, G + 6))]
    fan_start = 250
    for k in range(KR["Chambers"]):
        shots.append((fan_start + k * KR["BurstInterval"], "fan", (612, G - 24)))
    holster_at, draw_at = fan_start + 45, fan_start + 95
    total = fan_start + 30 + KR["ReloadTicks"] + 60
    rng = random.Random(4)
    for tick in range(total):
        for (t0, kind, aim) in shots:
            if t0 == tick and rounds > 0 and reload == 0:
                if kind == "fan" and t0 == fan_start:
                    steam -= KR["BurstSteamCost"]
                    notes.append((tick, "right click: the whole cylinder fanned in half a second for %d steam" % KR["BurstSteamCost"]))
                mx, my = p.x + KR["MuzzleDistance"], muzzle_y
                dx, dy = aim[0] - mx, aim[1] - my
                n = math.hypot(dx, dy)
                ang = math.atan2(dy, dx) + (rng.uniform(-KR["BurstSpread"], KR["BurstSpread"]) if kind == "fan" else 0.0)
                bullets.append(Bullet(mx, my, math.cos(ang) * KR["ShotSpeed"], math.sin(ang) * KR["ShotSpeed"]))
                rounds -= 1
                if rounds == 0:
                    reload = KR["ReloadTicks"]
                    notes.append((tick, "six shots: the reload (%.1f s) starts at once" % (KR["ReloadTicks"] / 60)))
        if tick == holster_at:
            held = False
            notes.append((tick, "the gun put away mid-reload: the rounds are the player's, the reload keeps running"))
        if tick == draw_at:
            held = True
            notes.append((tick, "drawn again: still reloading (swapping never refills the cylinder)"))
        if reload > 0:
            reload -= 1
            if reload == 0:
                rounds = KR["Chambers"]
        for b in bullets:
            for _ in range(2):                                     # extraUpdates 1: two moves a tick
                if not b.alive:
                    break
                b.x += b.vx
                b.y += b.vy
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
                        pops.append((tick, t["x"] - 10, G - KD["Height"] - 22, str(KR["Damage"]), BRASS))
                        if b.bounces >= 1:
                            b.alive = False
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
            if t["flash"]:
                gif.text(img, (int(t["x"]) - 4, G - KD["Height"] - 6), "*", fill=STEAM)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        if held:
            img.alpha_composite(gun, (int(p.x + 2), int(muzzle_y - 14)))
            loaded = int((1.0 - reload / KR["ReloadTicks"]) * KR["Chambers"]) if reload > 0 else rounds
            mid = (KR["Chambers"] - 1) / 2.0
            for k in range(KR["Chambers"]):
                px = p.x + (k - mid) * KR["Spacing"] - KR["Size"] / 2
                py = p.y - PLAYER_H - KR["Rise"] + abs(k - mid) * 2 - KR["Size"] / 2
                src = pips.crop((0, (0 if k < loaded else 1) * KR["Stride"], KR["Size"], (0 if k < loaded else 1) * KR["Stride"] + KR["Size"]))
                img.alpha_composite(faded(src, 0.75 if reload > 0 else 1.0), (int(round(px)), int(round(py))))
        for b in bullets:
            a = math.atan2(b.vy, b.vx)
            f = int(round((a % (2 * math.pi)) / (2 * math.pi) * 8)) % 8
            img.alpha_composite(bullet_sheet.crop((0, f * 16, 14, f * 16 + 14)), (int(b.x - 7), int(b.y - 7)))
        gif.text(img, (10, 8), "Sheriff's Revolver: %d damage, %d use time, 6%% crit; a bullet that ricochets once, towards an enemy; "
                 "%d rounds, %.1f s reload" % (KR["Damage"], KR["UseTime"], KR["Chambers"], KR["ReloadTicks"] / 60))
        gif.text(img, (10, 26), "steam %d   rounds %s" % (steam, ("reloading %.1f s" % (reload / 60)) if reload else str(rounds)),
                 fill=EMBER if reload else STEAM)
        if not held:
            gif.text(img, (int(p.x) - 30, int(p.y) - 90), "(holstered)", fill=STEAM)
        numbers(gif, img, pops, tick)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 70]
        if live:
            gif.text(img, (10, 44), live[-1], fill=BRASS)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Cursed Conductor
# ================================================================================================
class Conductor:
    """His 2-column grid sheets drawn at the rig origin, mirrored when he faces right (the art faces left), faded as a
    whole like his Fade in game. 2026-11-05b: no far sheet any more (skipped when missing); the turbine's vanes drawn
    over the middle plane on their own clock (RotorTicks, slowing in the Dying frames) and its smoke puffs drawn behind
    him (CursedConductor.Visuals.cs UpdateSmoke/DrawSmoke step for step, `ticks` game ticks per draw: the scenes draw
    every TPF ticks). `pumping` False stops new puffs (blown to bits)."""

    def __init__(self):
        self.sheets = [optional(BOSS + "CursedConductor" + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]
        self.rotor = optional(BOSS + "CursedConductor_Rotor.png")
        self.smoke_sheet = optional(BOSS + "CursedConductor_Smoke.png")
        self.puffs = []
        self.clock = 0
        self.pumping = True
        self.furious = False
        self.rng = random.Random(11)
        self.x, self.y = 0.0, 0.0                                  # NPC centre
        self.vx = self.vy = 0.0
        self.face = -1                                             # spriteDirection: 1 = facing right

    def cell(self, sheet, frame):
        cw, ch, cols = KC["CellWidth"], KC["CellHeight"], KC["Columns"]
        x, y = frame % cols * (cw + 2), frame // cols * (ch + 2)
        return sheet.crop((x, y, x + cw, y + ch))

    @property
    def origin(self):
        shift = (KC["BodyLeft"] + KC["BodyRight"]) // 2
        bottom = self.y + KC["HitboxHeight"] / 2
        return (self.x + shift * self.face, bottom - KC.get("BodyBottom", KC["HemY"]))

    def point(self, name):
        ox, oy = self.origin
        x, y = KC[name + "X"], KC[name + "Y"]
        return (ox + (-x if self.face == 1 else x), oy + y)

    def bob(self, frame):
        return BOB[frame] if 0 <= frame < len(BOB) else 0

    def step_smoke(self, frame, ticks):
        """UpdateSmoke, `ticks` times: drift (drag, a little rise) and a new puff out of the bell every interval."""
        dying = "Dying" in KC and frame >= KC["Dying"]
        interval = KC["DyingSmokeInterval"] if dying else (KC["FurySmokeInterval"] if self.furious else KC["SmokeInterval"])
        for _ in range(ticks):
            self.clock += 1
            for pf in self.puffs:
                pf["age"] += 1
                pf["vx"] *= KC["SmokeDrag"]
                pf["vy"] = pf["vy"] * KC["SmokeDrag"] - KC["SmokeRise"]
                pf["x"] += pf["vx"]
                pf["y"] += pf["vy"]
            self.puffs = [pf for pf in self.puffs if pf["age"] < pf["life"]]
            if self.pumping and self.clock % interval == 0 and len(self.puffs) < KC["SmokeCapacity"]:
                ex, ey = self.point("Exhaust")
                ey += self.bob(frame)
                self.puffs.append({"x": ex + self.rng.uniform(-KC["SmokeSpread"], KC["SmokeSpread"]), "y": ey,
                                   "vx": self.rng.uniform(-0.6, 0.6) + self.vx * 0.4,
                                   "vy": KC["SmokeSpeed"] * self.rng.uniform(0.85, 1.15) + self.vy * 0.4,
                                   "age": 0, "life": KC["SmokeLife"] + self.rng.randint(-6, 6), "flip": self.rng.random() < 0.5})

    def draw_smoke(self, img, alpha):
        if self.smoke_sheet is None:
            return
        cell = KC["SmokeCell"]
        for pf in self.puffs:
            t = pf["age"] / pf["life"]
            k = min(KC["SmokeFrames"] - 1, int(t * KC["SmokeFrames"]))
            im = self.smoke_sheet.crop((0, k * (cell + 2), cell, k * (cell + 2) + cell))
            if pf["flip"]:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            a = KC["SmokeOpacity"] * (1.0 if t < 0.6 else 1.0 - (t - 0.6) / 0.4) * alpha
            img.alpha_composite(faded(im, a), (int(round(pf["x"] - cell / 2)), int(round(pf["y"] - cell / 2))))

    def rotor_frame(self, frame):
        ticks = KC["FuryRotorTicks"] if self.furious else KC["RotorTicks"]
        if "Dying" in KC and frame >= KC["Dying"]:
            ticks = KC["RotorTicks"] + 2 * (frame - KC["Dying"])
        return (self.clock // max(1, ticks)) % KC["RotorFrames"]

    def draw(self, img, frame, alpha=1.0, ticks=3):
        cw, ox, oy = KC["CellWidth"], KC["OriginX"], KC["OriginY"]
        self.step_smoke(frame, ticks)
        self.draw_smoke(img, alpha)
        gx, gy = self.origin
        for n, sheet in enumerate(self.sheets):
            if sheet is None:
                continue
            c = self.cell(sheet, frame)
            if self.face == 1:
                c = c.transpose(Image.FLIP_LEFT_RIGHT)
                pos = (int(round(gx - (cw - ox))), int(round(gy - oy)))
            else:
                pos = (int(round(gx - ox)), int(round(gy - oy)))
            img.alpha_composite(faded(c, alpha), pos)
            if n == 1 and self.rotor is not None:               # the vanes over the drum, under the near plane
                k = self.rotor_frame(frame)
                rw, rh = KC["RotorWidth"], KC["RotorHeight"]
                r = self.rotor.crop((0, k * (rh + 2), rw, k * (rh + 2) + rh))
                if self.face == 1:
                    r = r.transpose(Image.FLIP_LEFT_RIGHT)
                    rx = gx - KC["RotorX"] - rw
                else:
                    rx = gx + KC["RotorX"]
                img.alpha_composite(faded(r, alpha), (int(round(rx)), int(round(gy + KC["RotorY"] + self.bob(frame)))))

    def move_toward(self, spot, max_speed):
        dx, dy = spot[0] - self.x, spot[1] - self.y
        d = math.hypot(dx, dy)
        wx, wy = ((dx / d * min(max_speed, d * 0.06), dy / d * min(max_speed, d * 0.06)) if d > 1 else (0.0, 0.0))
        self.vx += (wx - self.vx) * KC["HoverAccel"]
        self.vy += (wy - self.vy) * KC["HoverAccel"]
        self.x += self.vx
        self.y += self.vy

    def face_target(self, tx):
        if abs(tx - self.x) > 8:
            self.face = 1 if tx > self.x else -1


def heading_frame(hx, hy):
    a = math.degrees(math.atan2(hy, hx))
    flip = a > 90.5 or a < -90.5
    if flip:
        a = 180 - a if a > 0 else -180 - a
    return max(0, min(KC["Headings"] - 1, int(round((a + 90) / 22.5)))), flip


class Train:
    """GhostTrain, step for step: the route from the spawn state, the engine's trail, the cars following it."""
    ENGINE = [load(BOSS + "Projectiles/GhostTrain.png"), load(BOSS + "Projectiles/GhostTrain_Glow.png")]
    CAR = [load(BOSS + "Projectiles/GhostTrain_Car.png"), load(BOSS + "Projectiles/GhostTrain_CarGlow.png")]

    def __init__(self, route, pos, vel, ai1, ai2=0.0):
        self.route, self.ai1, self.ai2 = route, ai1, ai2
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.age = 0
        self.started = False
        self.circling = self.leaving = False
        self.time_left = KC["MaxLifetime"]

    def begin(self):
        self.started = True
        self.sx, self.sy = self.x, self.y
        self.speed = max(1.0, math.hypot(self.vx, self.vy))
        ux, uy = self.vx / self.speed, self.vy / self.speed
        n = KC["TrailLength"]
        self.trail = [None] * n
        for i in range(n):
            self.trail[(n - i) % n] = (self.sx - ux * self.speed * i, self.sy - uy * self.speed * i)
        self.head, self.filled = 0, n
        if self.route == "loop":
            self.cx, self.cy = self.ai1, self.ai2
            self.approach = max(0.0, (self.cx - self.sx) * ux + (self.cy - self.sy) * uy)
            tx, ty = self.sx + ux * self.approach, self.sy + uy * self.approach
            rx, ry = tx - self.cx, ty - self.cy
            self.radius = max(48.0, math.hypot(rx, ry))
            self.angle = math.atan2(ry, rx)
            cross = rx * self.vy - ry * self.vx
            self.omega = self.speed / self.radius * (1 if cross >= 0 else -1)
            life = int((self.approach + KC["LoopLaps"] * 2 * math.pi * self.radius + KC["Length"] + 60 * 16) / self.speed)
        elif self.route == "farewell":
            life = KC["FarewellTicks"]
        else:
            life = int((self.ai1 + KC["Length"]) / self.speed) + 2
        self.time_left = max(30, min(KC["MaxLifetime"], life))

    def update(self):
        if not self.started:
            self.begin()
        self.age += 1
        if self.route == "loop" and not self.leaving:
            travelled = self.age * self.speed
            if self.circling or travelled >= self.approach:
                self.circling = True
                a = self.angle + self.omega * (self.age - self.approach / self.speed)
                if (travelled - self.approach) / self.radius >= KC["LoopLaps"] * 2 * math.pi:
                    self.leaving = True
                    s = (1 if self.omega > 0 else -1) * self.speed
                    self.vx, self.vy = -math.sin(a) * s, math.cos(a) * s
                else:
                    self.vx = self.cx + math.cos(a) * self.radius - self.x
                    self.vy = self.cy + math.sin(a) * self.radius - self.y
        elif self.route == "farewell" and self.age * self.speed >= self.ai1:
            a = math.atan2(self.vy, self.vx)
            diff = (-math.pi / 2 - a + math.pi) % (2 * math.pi) - math.pi
            a += max(-KC["FarewellTurn"], min(KC["FarewellTurn"], diff))
            self.vx, self.vy = math.cos(a) * self.speed, math.sin(a) * self.speed
        n = KC["TrailLength"]
        self.head = (self.head + 1) % n
        self.trail[self.head] = (self.x + self.vx, self.y + self.vy)
        self.x += self.vx
        self.y += self.vy
        self.time_left -= 1
        return self.time_left > 0

    def back(self, distance):
        n = KC["TrailLength"]
        ticks = max(0.0, min(self.filled - 2, distance / self.speed))
        k = int(ticks)
        f = ticks - k
        a, b = self.trail[(self.head - k) % n], self.trail[(self.head - k - 1) % n]
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    def segment(self, k):
        back = 0.0 if k == 0 else KC["FirstSpacing"] + (k - 1) * KC["Spacing"]
        mid = (self.x, self.y) if k == 0 else self.back(back)
        ahead = (self.x + self.vx, self.y + self.vy) if k == 0 else self.back(back - self.speed)
        hx, hy = ahead[0] - mid[0], ahead[1] - mid[1]
        n = math.hypot(hx, hy) or 1.0
        return mid, (hx / n, hy / n)

    def hits(self, box):
        if self.route == "farewell" or self.age <= 2:
            return False
        for k in range(KC["Cars"] + 1):
            mid, (hx, hy) = self.segment(k)
            half = (KC["EngineLength"] if k == 0 else KC["CarLength"]) * 0.5 - 8
            thick = KC["EngineThickness"] if k == 0 else KC["CarThickness"]
            for s in range(9):                                  # the thick line, sampled
                u = -half + 2 * half * s / 8
                px, py = mid[0] + hx * u, mid[1] + hy * u
                if box[0] - thick / 2 < px < box[2] + thick / 2 and box[1] - thick / 2 < py < box[3] + thick / 2:
                    return True
        return False

    def fade(self):
        return max(0.0, min(1.0, self.time_left / KC["TrainFade"])) if self.route == "farewell" else 1.0

    def draw(self, img):
        f = self.fade()
        for k in range(KC["Cars"], -1, -1):
            mid, (hx, hy) = self.segment(k)
            frame, flip = heading_frame(hx, hy)
            cell = KC["EngineCell"] if k == 0 else KC["CarCell"]
            sheets = Train.ENGINE if k == 0 else Train.CAR
            for j, sheet in enumerate(sheets):
                c = sheet.crop((0, frame * (cell + 2), cell, frame * (cell + 2) + cell))
                if flip:
                    c = c.transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(faded(c, (KC["Opacity"] if j == 0 else 1.0) * f), (int(round(mid[0] - cell / 2)), int(round(mid[1] - cell / 2))))


class Flame:
    SHEET = load(BOSS + "Projectiles/ConductorFlame.png")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy, self.t = x, y, vx, vy, 0

    def update(self, ground):
        self.vy = min(KC["MaxFall"], self.vy + KC["Gravity"])
        self.x += self.vx
        self.y += self.vy
        self.t += 1
        return self.y < ground - 8 and self.t < KC["Lifetime"]

    def draw(self, img):
        cell = KC["FlameCell"]
        f = (self.t // KC["FrameTicks"]) % KC["FlameFrames"]
        img.alpha_composite(Flame.SHEET.crop((0, f * (cell + 2), cell, f * (cell + 2) + cell)), (int(self.x - cell / 2), int(self.y - cell / 2)))


def throw_flames(boss, target, count):
    fx, fy = boss.point("Throw")
    dx, dy = target[0] - fx, target[1] - fy
    n = math.hypot(dx, dy) or 1.0
    ax, ay = dx / n * KC["FlameSpeed"], dy / n * KC["FlameSpeed"] - KC["FlameLift"]
    out = []
    for k in range(count):
        turn = (k - (count - 1) * 0.5) * KC["FlameSpread"]
        c, s = math.cos(turn), math.sin(turn)
        out.append(Flame(fx, fy, ax * c - ay * s, ax * s + ay * c))
    return out


RAIL = load(BOSS + "Projectiles/GhostTrain_Rail.png")


def telegraph_strength(t, length):
    if t <= 0:
        return 0.0
    if t <= length:
        return max(0.0, min(1.0, t / (length / 3.0)))
    return max(0.0, min(1.0, 1.0 - (t - length) / 12.0))


def draw_rails(img, kind, locked, strength, w, h):
    if strength <= 0:
        return
    cell = KC["RailCell"]
    piece = {"level": 0, "upright": 1, "ring": 2}[kind]
    src = faded(RAIL.crop((0, piece * (cell + 2), cell, piece * (cell + 2) + cell)), 0.85 * strength)
    if kind == "level":
        for x in range(-16, w + 16, 16):
            img.alpha_composite(src, (x - 8, int(round(locked[1] - cell / 2))))
    elif kind == "upright":
        for y in range(-16, h + 16, 16):
            img.alpha_composite(src, (int(round(locked[0] - cell / 2)), y - 8))
    else:
        for k in range(40):
            a = 2 * math.pi * k / 40
            img.alpha_composite(src, (int(round(locked[0] + math.cos(a) * KC["LoopRadius"] - cell / 2)),
                                      int(round(locked[1] + math.sin(a) * KC["LoopRadius"] - cell / 2))))


def idle_frame(tick):
    return KC["Idle"] + (tick // KC["IdleFrameTicks"]) % KC["IdleFrames"]


def throw_frame(t, start):
    k = t - start
    return KC["Throw"] + (0 if k < 12 else 1 if k < KC["LanternWindup"] else 2 if k < KC["LanternWindup"] + KC["LanternRelease"] else 3)


def whistle_frame(t):
    return KC["Whistle"] + (0 if t < 10 else 1 if t < 16 else 2 + (t // 6) % 2)


def mist(parts, x, y, n, rng):
    for _ in range(n):
        parts.append([x + rng.uniform(-14, 14), y + rng.uniform(-10, 10), rng.uniform(-0.5, 0.5), rng.uniform(-1.2, -0.2), rng.randint(20, 40)])


def draw_mist(img, parts):
    d = ImageDraw.Draw(img)
    for m in parts:
        a = max(0, min(255, m[4] * 8))
        d.rectangle([int(m[0]), int(m[1]), int(m[0]) + 3, int(m[1]) + 3], fill=GHOST + (a,))


def step_mist(parts):
    for m in parts:
        m[0] += m[2]
        m[1] += m[3]
        m[4] -= 1
    parts[:] = [m for m in parts if m[4] > 0]


def title(gif, img, w, y, name, sub, alpha):
    if alpha <= 0:
        return
    tw = gif.big.getlength(name)
    gif.text(img, (int(w / 2 - tw / 2), y), name, fill=tuple(int(c * alpha) for c in STEAM), font=gif.big)
    sw = gif.font.getlength(sub)
    gif.text(img, (int(w / 2 - sw / 2), y + 26), sub, fill=tuple(int(c * alpha) for c in GHOST))


def scene_intro(out, font):
    W, H, G = 680, 420, 380
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    rng = random.Random(7)
    p = Player(200, G)
    side = 1
    boss.x, boss.y = p.x + side * KC["HoverOffsetX"], p.y - PLAYER_H / 2 + KC["HoverOffsetY"]
    parts, flames, pops = [], [], []
    state, t = "intro", 0
    total = KC["IntroTicks"] + 40 + KC["LanternTicks"] + 70
    for tick in range(total):
        t += 1
        target = (p.x, p.y - PLAYER_H / 2)
        boss.face_target(p.x)
        if state == "intro":
            if t < KC["FadeTicks"] and t % 2 == 0:
                mist(parts, boss.x + rng.uniform(-30, 30), boss.y + rng.uniform(-50, 50), 2, rng)
            if t >= KC["IntroTicks"]:
                state, t = "hover", 0
        elif state == "hover":
            boss.move_toward((p.x + side * KC["HoverOffsetX"], target[1] + KC["HoverOffsetY"]), KC["HoverSpeed"])
            if t >= 40:
                state, t = "lantern", 0
        elif state == "lantern":
            boss.move_toward((p.x + side * KC["HoverOffsetX"], target[1] + KC["HoverOffsetY"]), KC["AttackDrift"])
            if t == KC["LanternWindup"]:
                flames += throw_flames(boss, target, KC["Flames"])
            if t >= KC["LanternTicks"]:
                state, t = "hover", 0
        p.run = 0
        start = KC["IntroTicks"] + 40                              # the lantern's windup begins: it runs (the flames land behind it)
        if start < tick < start + KC["LanternWindup"] + 30:
            p.run = -1
        p.step()
        for f in list(flames):
            if not f.update(G):
                flames.remove(f)
                mist(parts, f.x, f.y, 4, rng)
            elif p.immune <= 0 and overlaps((f.x - 8, f.y - 8, f.x + 8, f.y + 8), p.box()):
                p.immune = IMMUNITY
                pops.append((tick, p.x - 10, p.y - 70, str(KC["FlameDamage"]), HURT))
                flames.remove(f)
        step_mist(parts)
        if tick % 3:
            continue
        img = bg.copy()
        if state == "intro":
            alpha = min(1.0, t / KC["FadeTicks"])
            frame = idle_frame(tick) if t < KC["TipStart"] or t >= KC["TipEnd"] else KC["Tip"] + (0 if t < KC["TipRaise"] else 1 if t < KC["TipBow"] else 2)
        elif state == "lantern":
            alpha, frame = 1.0, throw_frame(t, 0)
        else:
            alpha, frame = 1.0, idle_frame(tick)
        img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        boss.draw(img, frame, alpha)
        for f in flames:
            f.draw(img)
        draw_mist(img, parts)
        if state == "intro" and t >= KC["TitleTick"]:
            k = t - KC["TitleTick"]
            title(gif, img, W, 70, "Cursed Conductor", "The Last Stop", min(1.0, k / 20.0))
        elif state != "intro" and tick < KC["IntroTicks"] + 45:
            title(gif, img, W, 70, "Cursed Conductor", "The Last Stop", max(0.0, 1.0 - (tick - KC["IntroTicks"]) / 45.0))
        gif.text(img, (10, 8), "Cursed Conductor (Old Brass Town): %d life, %d defense, %d contact (Expert); he materializes and tips his cap" % (
            KC["ExpertLife"], KC["BaseDefense"], KC["ExpertContactDamage"]))
        if state == "lantern":
            gif.text(img, (10, 26), "the lantern swung back (%d ticks, its flame flaring), then %d lobbed ghost flames of %d" % (
                KC["LanternWindup"], KC["Flames"], KC["FlameDamage"]), fill=GHOST)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


def scene_trains(out, font):
    W, H, G = 960, 520, 470
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    p = Player(300, G)
    side = 1
    boss.x, boss.y = p.x + side * KC["HoverOffsetX"], p.y - PLAYER_H / 2 + KC["HoverOffsetY"]
    trains, pops = [], []
    express_len = KC["ExpressTelegraph"] + KC["ExpressWait"]
    dive_len = KC["DiveTelegraph"] + KC["DiveWait"]
    plan = [("hover", 30), ("express", express_len), ("hover", 40), ("dive", dive_len), ("hover", 50)]
    locked = None
    tick = 0
    for (state, length) in plan:
        for t in range(1, length + 1):
            tick += 1
            target = (p.x, p.y - PLAYER_H / 2)
            boss.face_target(p.x)
            boss.move_toward((p.x + side * KC["HoverOffsetX"], target[1] + KC["HoverOffsetY"]),
                             KC["HoverSpeed"] if state == "hover" else KC["AttackDrift"])
            if t == 1 and state in ("express", "dive"):
                locked = target
            if state == "express" and t == KC["ExpressTelegraph"]:
                trains.append(Train("express", (locked[0] + side * KC["ExpressReach"], locked[1]), (-side * KC["TrainSpeed"], 0.0),
                                    2 * KC["ExpressReach"] + KC["TrainLength"]))
            if state == "dive" and t == KC["DiveTelegraph"]:
                trains.append(Train("dive", (locked[0], locked[1] - KC["DiveHeight"]), (0.0, KC["TrainSpeed"]), 2 * KC["DiveHeight"] + KC["TrainLength"]))
            # the player: jumps the Express when its engine is ~10 ticks off; steps aside out of the Dive's column
            p.run = 0
            for tr in trains:
                if tr.route == "express" and tr.started and 0 < tr.x - p.x < 330 and p.y >= G:
                    p.jump()
            if state == "dive" and 8 < t < 40:
                p.run = -1
            p.step()
            for tr in list(trains):
                if not tr.update():
                    trains.remove(tr)
                    continue
                if p.immune <= 0 and tr.hits(p.box()):
                    p.immune = IMMUNITY
                    pops.append((tick, p.x - 10, p.y - 70, str(KC["TrainDamage"]), HURT))
            if tick % 3:
                continue
            img = bg.copy()
            if state == "express":
                draw_rails(img, "level", locked, telegraph_strength(t, KC["ExpressTelegraph"]), W, H)
            elif state == "dive":
                draw_rails(img, "upright", locked, telegraph_strength(t, KC["DiveTelegraph"]), W, H)
            if state == "express":
                frame = whistle_frame(t) if t < KC["ExpressTelegraph"] else KC["Point"] + (t // 10) % KC["PointFrames"]
            elif state == "dive":
                frame = KC["Call"] + (t // 8) % KC["CallFrames"] if t < KC["DiveTelegraph"] else idle_frame(tick)
            else:
                frame = idle_frame(tick)
            if p.immune <= 0 or (tick // 3) % 2 == 0:
                img.alpha_composite(player_sprite(flip=boss.x < p.x), (int(p.x - 20), int(p.y - 56)))
            boss.draw(img, frame)
            for tr in trains:
                tr.draw(img)
            gif.text(img, (10, 8), "Cursed Conductor: the ghost train, %d (Expert) to everything it touches, %d px/tick, ~%d tiles long" % (
                KC["TrainDamage"], KC["TrainSpeed"], int(KC["TrainLength"] / 16)))
            if state == "express":
                gif.text(img, (10, 26), "EXPRESS: the whistle (%d ticks) and a ghost track along your row as thick as the train; it comes from "
                         "%d tiles to his side: jump it" % (KC["ExpressTelegraph"], int(KC["ExpressReach"] / 16)), fill=GHOST)
            elif state == "dive":
                gif.text(img, (10, 26), "DIVE: the lantern raised (%d ticks), the track upright over your column; it plunges from %d tiles up: "
                         "step aside" % (KC["DiveTelegraph"], int(KC["DiveHeight"] / 16)), fill=GHOST)
            gif.text(img, (10, 44), "enraged (50%% life): both come twice, the second Express from his other side (%d / %d-tick telegraphs)" % (
                KC["ExpressRepeatTelegraph"], KC["DiveRepeatTelegraph"]), fill=STEAM)
            numbers(gif, img, pops, tick)
            gif.push(img)
    gif.save(out)


def scene_loop(out, font):
    R = KC["LoopRadius"]
    W, H = int(2 * R + 360), int(2 * R + 200)
    G = int(H / 2 + 60)
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=0.5)
    gif.font = gif.font.font_variant(size=26)
    gif.big = gif.big.font_variant(size=36)
    boss = Conductor()
    p = Player(W / 2, G)
    side = 1
    boss.x, boss.y = p.x + side * KC["HoverOffsetX"], p.y - PLAYER_H / 2 + KC["HoverOffsetY"]
    trains, flames, pops = [], [], []
    locked = None
    rng = random.Random(3)
    parts = []
    total = KC["LoopTicks"] + 40
    for t in range(1, total + 1):
        target = (p.x, p.y - PLAYER_H / 2)
        boss.face_target(p.x)
        boss.move_toward((p.x + side * KC["HoverOffsetX"], target[1] + KC["HoverOffsetY"]), KC["AttackDrift"])
        if t == 1:
            locked = target
        if t == KC["LoopTelegraph"]:
            top = (locked[0], locked[1] - R)
            trains.append(Train("loop", (top[0] + side * KC["LoopApproach"], top[1]), (-side * KC["LoopSpeed"], 0.0), locked[0], locked[1]))
        if t in (KC["LoopVolley1"], KC["LoopVolley2"]):
            flames += throw_flames(boss, target, KC["Flames"])
        # the player dodges the flames, staying well inside the ring
        p.run = 0                                            # on the windup's cue (the lantern swung back, flaring), it runs
        if KC["LoopVolley1"] - KC["LanternWindup"] < t < KC["LoopVolley1"] + 40:
            p.run = -1
        if t == KC["LoopVolley2"] + 2:
            p.jump()                                         # the second volley: a jump as it is thrown (they land under it)
        p.step()
        for tr in list(trains):
            if not tr.update():
                trains.remove(tr)
            elif p.immune <= 0 and tr.hits(p.box()):
                p.immune = IMMUNITY
                pops.append((t, p.x - 10, p.y - 70, str(KC["TrainDamage"]), HURT))
        for f in list(flames):
            if not f.update(G):
                flames.remove(f)
                mist(parts, f.x, f.y, 4, rng)
            elif p.immune <= 0 and overlaps((f.x - 8, f.y - 8, f.x + 8, f.y + 8), p.box()):
                p.immune = IMMUNITY
                pops.append((t, p.x - 10, p.y - 70, str(KC["FlameDamage"]), HURT))
                flames.remove(f)
        step_mist(parts)
        if t % 3:
            continue
        img = bg.copy()
        draw_rails(img, "ring", locked, telegraph_strength(t, KC["LoopTelegraph"] + KC["LoopEnter"]), W, H)
        if t < KC["LoopTelegraph"]:
            frame = KC["Call"] + (t // 8) % KC["CallFrames"]
        else:
            frame = idle_frame(t)
            for v in (KC["LoopVolley1"], KC["LoopVolley2"]):
                if v - KC["LanternWindup"] < t <= v + KC["LanternRelease"] + KC["LanternRecover"]:
                    frame = throw_frame(t, v - KC["LanternWindup"])
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        boss.draw(img, frame)
        for tr in trains:
            tr.draw(img)
        for f in flames:
            f.draw(img)
        draw_mist(img, parts)
        gif.text(img, (20, 14), "LOOP: the lantern raised and the whistle (%d ticks), a ring of lights %d tiles round you; the train comes in "
                 "along its top" % (KC["LoopTelegraph"], int(R / 16)))
        gif.text(img, (20, 48), "and runs round it for %.2f laps at %d px/tick (it never crosses the inside), while he lobs %d flames in, twice" % (
            KC["LoopLaps"], KC["LoopSpeed"], KC["Flames"]), fill=GHOST)
        numbers(gif, img, pops, t)
        gif.push(img)
    gif.save(out)


def scene_death(out, font):
    W, H, G = 900, 460, 420
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    p = Player(220, G)
    side = 1
    boss.x, boss.y = 470.0, G - 160.0
    boss.face = -1
    trains, gores, parts = [], [], []
    rng = random.Random(11)
    gore_names = ("CursedConductor_GoreCap", "CursedConductor_GoreHead", "CursedConductor_GoreCoat", "CursedConductor_GoreLantern")
    gore_imgs = [load(BOSS + "Gores/" + n + ".png") for n in gore_names]
    for t in range(1, KC["DeathTicks"] + 30):
        boss.vx *= 0.85
        boss.vy *= 0.85
        if t == KC["FarewellTick"]:
            trains.append(Train("farewell", (boss.x + side * KC["FarewellReach"], boss.y), (-side * KC["FarewellSpeed"], 0.0), KC["FarewellReach"]))
        if t == KC["PickupTick"]:
            for k, im in enumerate(gore_imgs):
                gores.append([boss.x + rng.uniform(-16, 16) - im.width / 2, boss.y - KC["HitboxHeight"] / 2 + k * 20, rng.uniform(-2, 2),
                              rng.uniform(-3, -1), im])
            mist(parts, boss.x, boss.y, 24, rng)
        for tr in list(trains):
            if not tr.update():
                trains.remove(tr)
        for g in gores:
            g[3] = min(10.0, g[3] + 0.2)
            g[0] += g[2]
            g[1] += g[3]
            if g[1] + g[4].height >= G:
                g[1], g[2], g[3] = G - g[4].height, g[2] * 0.6, 0.0
        step_mist(parts)
        if t % 3:
            continue
        img = bg.copy()
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        if t < KC["PickupTick"]:
            boss.draw(img, KC["Dying"] + min(KC["DyingFrames"] - 1, t // 30))
        for g in gores:
            img.alpha_composite(g[4], (int(g[0]), int(g[1])))
        for tr in trains:
            tr.draw(img)
        draw_mist(img, parts)
        gif.text(img, (10, 8), "Cursed Conductor's death (camera locked): he slumps, his lantern and eyes go out (%d frames over 2 s)" % KC["DyingFrames"])
        if t >= KC["FarewellTick"]:
            gif.text(img, (10, 26), "the last train comes for his spirit (harmless): his empty shell falls apart as it passes, and it climbs away",
                     fill=GHOST)
        if t >= KC["DeathTicks"] - 60:
            title(gif, img, W, 90, "Cursed Conductor", "Defeated", min(1.0, (t - KC["DeathTicks"] + 60) / 20.0))
        gif.push(img)
    gif.save(out)


def sprites_png(out, font):
    sheets = [load(BOSS + "CursedConductor" + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]
    boss = Conductor()
    cw, ch = KC["CellWidth"], KC["CellHeight"]
    n = KC["Frames"]
    cols = 9
    rows = (n + cols - 1) // cols
    panels = []
    for bg in ((40, 34, 32, 255), (150, 180, 210, 255)):
        panel = Image.new("RGBA", (cw * cols, ch * rows), bg)
        for k in range(n):
            c = Image.new("RGBA", (cw, ch))
            for s in sheets:
                c.alpha_composite(boss.cell(s, k))
            panel.alpha_composite(c, ((k % cols) * cw, (k // cols) * ch))
        panels.append(panel)
    trains = Image.new("RGBA", (KC["EngineCell"] * 9, KC["EngineCell"] + KC["CarCell"]), (40, 34, 32, 255))
    for k in range(9):
        for row, (cell, pair) in enumerate(((KC["EngineCell"], Train.ENGINE), (KC["CarCell"], Train.CAR))):
            for sheet in pair:
                trains.alpha_composite(sheet.crop((0, k * (cell + 2), cell, k * (cell + 2) + cell)),
                                       (k * KC["EngineCell"] + (KC["EngineCell"] - cell) // 2, row * KC["EngineCell"]))
    extras = [load(BOSS + "Projectiles/ConductorFlame.png"), RAIL, load(BOSS + "Items/CursedConductorBag.png"),
              load(BOSS + "CursedConductor_Head_Boss.png"), load(BOSS + "Items/CursedWhistle.png"), load(TOWN + "Items/BrokenWhistle.png")]
    extras += [load(BOSS + "Gores/CursedConductor_Gore%s.png" % g) for g in ("Cap", "Head", "Coat", "Lantern")]
    W = max(panels[0].width, trains.width)
    H = panels[0].height * 2 + trains.height + 170 + 60
    gif = Gif(font, (1, 1))
    W = max(W, int(gif.font.getlength("Cursed Conductor: 25 frames x 3 planes + glow (Idle 6, Whistle 4, Point 2, Throw 4, Call 2, Tip 3, "
                                       "Dying 4), 2x game scale, on the town's dark and on a light ground")) + 10)
    sheet = Image.new("RGBA", (W + 40, H), (28, 28, 34, 255))
    gif.text(sheet, (20, 6), "Cursed Conductor: %d frames x 3 planes + glow (Idle 6, Whistle 4, Point 2, Throw 4, Call 2, Tip 3, Dying 4), "
             "2x game scale, on the town's dark and on a light ground" % n)
    y = 30
    for panel in panels:
        sheet.alpha_composite(panel, (20, y))
        y += panel.height
    gif.text(sheet, (20, y + 4), "the ghost train: engine and passenger car, 9 headings each (up to down, facing right; mirrored for the left), "
             "with their glow (windows, headlamp, boiler bands)")
    sheet.alpha_composite(trains, (20, y + 26))
    y += trains.height + 34
    x = 20
    for im in extras:
        big = im.resize((im.width * 2, im.height * 2), Image.NEAREST) if im.height <= 64 else im
        sheet.alpha_composite(big, (x, y))
        x += big.width + 18
    gif.text(sheet, (20, y + 150), "ghost fire (4 frames), the track pieces (level, upright, ring light), the bag, the map icon, the Cursed and the "
             "Broken Whistle, the 4 gores (x2 where small)")
    sheet.convert("RGB").save(out, optimize=True)
    print(out, sheet.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("revolver", lambda: scene_revolver(os.path.join(args.out, "2026-11-04_weapon-sheriffs-revolver.gif"), args.font)),
            ("intro", lambda: scene_intro(os.path.join(args.out, "2026-11-04_boss-cursed-conductor-intro.gif"), args.font)),
            ("trains", lambda: scene_trains(os.path.join(args.out, "2026-11-04_boss-cursed-conductor-trains.gif"), args.font)),
            ("loop", lambda: scene_loop(os.path.join(args.out, "2026-11-04_boss-cursed-conductor-loop.gif"), args.font)),
            ("death", lambda: scene_death(os.path.join(args.out, "2026-11-04_boss-cursed-conductor-death.gif"), args.font)),
            ("sprites", lambda: sprites_png(os.path.join(args.out, "2026-11-04_boss-cursed-conductor-sprites.png"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
