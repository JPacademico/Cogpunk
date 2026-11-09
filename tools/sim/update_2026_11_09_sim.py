"""D5 proofs for the request of 2026-11-09, built from the real sprite sheets, the generated rig data and the constants
parsed out of the C# files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_09_sim.py --out docs/media [--only targeting,whistle,diagonal,sprites,train,items]

Writes:
    2026-11-09_boss-cursed-conductor-targeting.gif   his new rest pose (the lantern held before his chest) and the
                                              lantern attack with no arm movement: a halo swells round the glass for
                                              ThrowWindup ticks and flashes as the bolts fly from it. Two fighters: a
                                              gunner and a swordsman, each doing damage (their running totals over their
                                              heads, decayed as BossNPC does); he targets the closest at first, after 5 s
                                              switches to the top damage dealer among the others (the swordsman) and,
                                              since that one fights in melee, floats in close (his near edge MeleeGap px
                                              from the swordsman's, his turbine just over their feet); after 5 more s he
                                              must switch again (never the same target twice in a row): back to the gunner
                                              and his far hover.
    2026-11-09_boss-cursed-conductor-whistle.gif     the whistle phase in the new pose: the hand up his side to his mouth, the
                                              shriek with the lantern blazing in its hold, and the hand back down at the end
                                              (the 7 s are cut in the middle).
    2026-11-09_boss-cursed-conductor-diagonal.gif    half scale, one 1920x1080 screen round the player: the new passive train,
                                              the Diagonal dive: its 45-degree track and the rift it bursts out of for 1 s,
                                              then the train through the player's position (down to his side, then up).
    2026-11-09_boss-cursed-conductor-sprites.png     all his frames over dark and light (the new rest, whistle, call, point,
                                              tip and dying poses), the lantern's halo frames, the diagonal track piece.
    2026-11-09_weapon-cursed-train-whistle.gif       the Cursed Train Whistle: the first blow calls the little ghost engine,
                                              which floats round its owner; three more blows hitch on three wagons; then
                                              a target dummy in reach: the train runs through it, turns and runs through
                                              again, every segment hitting once a pass (GhostTrainEngine.Steer and
                                              PlaceWagons step for step).
    2026-11-09_items-jade-brass-lawhat.png           Jade, the Large Jade, the Jade Phaseblade and Phasesaber, a jade
                                              cluster (the tile framed as Terraria frames it), the Law Hat, and the Brass
                                              armor's and the Jade Robe's item icons (their worn previews are separate
                                              GIFs from tools/sim/armor_preview.py).

Leaves out: lighting, the planes' parallax, vanilla's player physics (scripted paths), defense, netcode (the sim is the
server and the owner). The melee check is the owner's verdict in game (Core/Combat/MeleeFocus.cs); here the swordsman is
simply marked as a melee fighter. Numbers are Expert's.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, consts, load, player_sprite, TPF  # noqa: E402
from update_2026_11_04_sim import town_backdrop, HURT, STEAM  # noqa: E402
from update_2026_11_04b_sim import Conductor, heading_frame, faded  # noqa: E402
from update_2026_11_05_sim import Train, Bolt, rail_piece, strength, half  # noqa: E402
import terrain  # noqa: E402

BOSS = "Content/Bosses/CursedConductor/"
WEP = BOSS + "Weapons/"
KC = consts(BOSS + "CursedConductor.cs", BOSS + "CursedConductor.Visuals.cs", BOSS + "CursedConductorRigData.cs",
            "Core/Templates/BossNPC.cs", "Core/Combat/MeleeFocus.cs")
KT = consts(BOSS + "Projectiles/GhostTrain.cs")
KW = consts(WEP + "GhostTrainEngine.cs", WEP + "CursedTrainWhistle.cs")
GHOST = (140, 201, 176)
AETHER = (198, 189, 255)
HALO = load(BOSS + "CursedConductor_LanternGlow.png")
RAIL_DIAG = load(BOSS + "Projectiles/GhostTrain_RailDiagonal.png")
BOB = [int(v) for v in open(BOSS + "CursedConductorRigData.cs", encoding="utf-8").read().split("Bob = {")[1].split("}")[0].split(",")]
HIT_W = KC["BodyRight"] - KC["BodyLeft"]
HIT_H = KC["BodyBottom"] - KC["BodyTop"]


def idle_frame(clock):
    return KC["Idle"] + (clock // KC["IdleFrameTicks"]) % KC["IdleFrames"]


def halo_frame(k):
    """DrawLanternGlow: the halo's sheet frame and alpha for the lantern's tick k (None when none)."""
    if k < 0:
        return None
    w = KC["ThrowWindup"]
    if k < w:
        u = k / w
        return min(2, int(u * 3)), 0.35 + 0.65 * u
    if k < w + 6:
        return 3, 1.0
    total = KC["ThrowWindup"] + KC["ThrowRelease"] + KC["ThrowRecover"]
    if k < total:
        return 2, max(0.0, 1.0 - (k - w - 6) / max(1, total - w - 6))
    return None


def draw_halo(img, boss, frame, k, alpha=1.0):
    h = halo_frame(k)
    if h is None:
        return
    f, a = h
    cell = KC["LanternGlowCell"]
    piece = HALO.crop((0, f * (cell + 2), cell, f * (cell + 2) + cell))
    ox, oy = boss.origin
    x = ox + (-KC["LanternX"] if boss.face == 1 else KC["LanternX"]) - cell // 2
    y = oy + KC["LanternY"] + (BOB[frame] if 0 <= frame < len(BOB) else 0) - cell // 2
    img.alpha_composite(faded(piece, a * alpha), (int(round(x)), int(round(y))))


def lantern_point(boss, frame):
    ox, oy = boss.origin
    return (ox + (-KC["LanternX"] if boss.face == 1 else KC["LanternX"]), oy + KC["LanternY"] + (BOB[frame] if 0 <= frame < len(BOB) else 0))


def hover_spot(target, side, melee):
    """CursedConductor.HoverSpot: beside and above, or (the melee hover) his near edge MeleeGap px from the target's and
    his turbine MeleeLift px over their feet."""
    tx, tfeet = target
    tcx, tcy = tx, tfeet - 21
    if melee:
        return (tcx + side * (10 + KC["MeleeGap"] + HIT_W * 0.5), tfeet - KC["MeleeLift"] - HIT_H * 0.5)
    return (tcx + side * KC["HoverOffsetX"], tcy + KC["HoverOffsetY"])


def move_toward(boss, spot, melee, speed):
    """CursedConductor.MoveToward with the melee hover's faster, firmer follow."""
    dx, dy = spot[0] - boss.x, spot[1] - boss.y
    d = math.hypot(dx, dy)
    approach = KC["MeleeApproach"] if melee else KC["HoverApproach"]
    accel = KC["MeleeHoverAccel"] if melee else KC["HoverAccel"]
    top = KC["MeleeHoverSpeed"] if melee else speed
    wx, wy = ((dx / d * min(top, d * approach), dy / d * min(top, d * approach)) if d > 1 else (0.0, 0.0))
    boss.vx += (wx - boss.vx) * accel
    boss.vy += (wy - boss.vy) * accel
    boss.x += boss.vx
    boss.y += boss.vy


def sword_sprite(flip=False):
    """The stand-in player with a Blade of Grass-sized sword held up (40x40 at scale 1: the reach the melee hover keeps)."""
    s = player_sprite(flip)
    im = Image.new("RGBA", (s.width + 40, s.height), (0, 0, 0, 0))
    im.alpha_composite(s, (20, 0))
    d = ImageDraw.Draw(im)
    hx, hy = 20 + (14 if not flip else 26), 30
    d.line([hx, hy, hx + (34 if not flip else -34), hy - 26], fill=(118, 220, 162, 255), width=3)
    d.line([hx - 3, hy + 1, hx + 3, hy - 3], fill=(184, 138, 51, 255), width=2)
    return im


# ================================================================================================
# 1. Targeting, the melee hover and the lantern's glow
# ================================================================================================
def scene_targeting(out, font):
    W, H, G = 1000, 420, 380
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=0.9)
    boss = Conductor()
    gunner, swords = (300.0, float(G)), (700.0, float(G))
    players = [gunner, swords]
    names = ("gunner", "swordsman")
    melee = (False, True)
    dps = (40.0, 62.0)                                             # damage a second each lands on him
    # mid-fight: both have been hitting him a while (the decayed totals' steady state: dps/2 a half second / (1 - decay)),
    # the gunner (the closest at the start) has been the target for 3 s, so the 5 s switches fall at 2 s and 7 s
    damage = [d / 2.0 / (1.0 - KC["DamageDecay"]) for d in dps]
    target, ticks_on = 0, KC["TargetSwitchTicks"] - 120
    side = 1.0
    boss.x, boss.y = hover_spot(gunner, side, False)
    lantern_clock, throw_tick = 0, -1
    bolts, pops = [], []
    rng = random.Random(3)
    notes = [(0, "his rest: the lantern held before his chest (the user's reference); the lantern attack moves no arm"),
             (60, "the cue is a halo of ghost light swelling round the lantern (30 ticks), then the bolts fly from it"),
             (120, "every 5 s: the top damage dealer among the OTHER players becomes the target (the swordsman)"),
             (150, "the swordsman fights in melee: he floats in within Blade of Grass reach (MeleeGap %d px)" % KC["MeleeGap"]),
             (420, "5 s later he must switch again (never the same twice): back to the gunner, far hover")]
    for tick in range(598):
        # BossNPC.UpdateTargeting: decay, then the switch every TargetSwitchTicks to the best of the others
        for i in range(2):
            damage[i] += dps[i] / 60.0
        if tick % KC["DamageDecayInterval"] == 0:
            damage = [d * KC["DamageDecay"] for d in damage]
        ticks_on += 1
        if ticks_on >= KC["TargetSwitchTicks"]:
            target = 1 - target                                    # the best other (only one other here)
            ticks_on = 0
        t = players[target]
        is_melee = melee[target]
        if is_melee and (boss.x - t[0]) * side < -KC["MeleeSideSwitch"]:
            side = -side
        speed = KC["AttackDrift"] if throw_tick >= 0 and not is_melee else KC["HoverSpeed"]
        move_toward(boss, hover_spot(t, side, is_melee), is_melee, speed)
        if abs(t[0] - boss.x) > 8:
            boss.face = 1 if t[0] > boss.x else -1
        frame = idle_frame(tick)
        # the lantern: every LanternInterval ticks a flare, the bolts at ThrowWindup from the glass
        if throw_tick < 0:
            lantern_clock += 1
            if lantern_clock >= KC["LanternInterval"]:
                lantern_clock, throw_tick = 0, 0
        else:
            throw_tick += 1
            if throw_tick == KC["ThrowWindup"]:
                fx, fy = lantern_point(boss, frame)
                tx, ty = t[0], t[1] - 21
                dx, dy = tx - fx, ty - fy
                n = math.hypot(dx, dy) or 1.0
                ax, ay = dx / n * KC["BoltSpeed"], dy / n * KC["BoltSpeed"]
                for k in range(int(KC["Bolts"])):
                    turn = (k - (KC["Bolts"] - 1) * 0.5) * KC["BoltSpread"]
                    c, s = math.cos(turn), math.sin(turn)
                    bolts.append(Bolt(fx, fy, ax * c - ay * s, ax * s + ay * c))
            if throw_tick >= KC["ThrowWindup"] + KC["ThrowRelease"] + KC["ThrowRecover"]:
                throw_tick = -1
        for b in bolts:
            if not b.landed and abs(b.x - t[0]) < 12 and t[1] - 42 < b.y < t[1]:
                b.landed = True
                pops.append((tick, t[0] - 10, t[1] - 70, str(int(KC["BoltDamage"])), HURT))
        bolts = [b for b in bolts if not b.landed and b.update(G) and 0 < b.x < W]
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        boss.draw(img, frame, 1.0, TPF)
        draw_halo(img, boss, frame, throw_tick)
        img.alpha_composite(player_sprite(flip=False), (int(gunner[0] - 20), int(G - 56)))
        sw = sword_sprite(flip=True)
        img.alpha_composite(sw, (int(swords[0] - 40), int(G - 56)))
        for b in bolts:
            b.draw(img)
        for i, p in enumerate(players):                            # running damage (BossNPC's decayed totals) and the target
            bx = int(p[0] - 30)
            d.rectangle([bx, G - 84, bx + 60, G - 78], fill=(30, 26, 22, 255))
            d.rectangle([bx, G - 84, bx + int(min(60, damage[i] / 6.0)), G - 78], fill=(236, 113, 40, 255))
            gif.text(img, (bx - 8, G - 104), "%s %d" % (names[i], damage[i]), fill=STEAM)
            if i == target:
                gif.text(img, (bx + 6, G - 124), "TARGET", fill=(255, 199, 90))
        for (t0, x, y, s, col) in pops:
            if tick - t0 < 40:
                gif.text(img, (int(x), int(y - (tick - t0) * 0.6)), s, fill=col)
        note = [n for (t0, n) in notes if tick >= t0][-1]
        gif.text(img, (8, 6), note)
        gif.text(img, (8, H - 22), "target: %s (%s) | switch in %.1f s | hover: %s" % (
            names[target], "melee" if melee[target] else "ranged", (KC["TargetSwitchTicks"] - ticks_on) / 60.0,
            "MELEE (within reach)" if melee[target] else "far (%d px beside)" % KC["HoverOffsetX"]), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# 2. The whistle in the new pose
# ================================================================================================
def scene_whistle(out, font):
    W, H, G = 420, 300, 280
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.6)
    boss = Conductor()
    boss.face = -1
    boss.x, boss.y = 220.0, G - 4 - HIT_H * 0.5 - 20
    wt = KC["WhistleTicks"]
    timeline = [("idle", t) for t in range(0, 36)] + [("whistle", t) for t in range(0, 168)] + \
               [("whistle", t) for t in range(wt - 24, wt)] + [("idle", t) for t in range(36, 72)]
    for i, (state, t) in enumerate(timeline):
        if state == "idle":
            frame = idle_frame(t)
        elif t < 8 or t >= wt - 8:
            frame = KC["Whistle"]
        elif t < 14:
            frame = KC["Whistle"] + 1
        else:
            frame = KC["Call"] + (t // 8) % KC["CallFrames"]
        if i % TPF:
            continue
        img = bg.copy()
        boss.draw(img, frame, 1.0, TPF)
        label = {KC["Whistle"]: "Whistle0: the hand on its way (an in-between)", KC["Whistle"] + 1: "Whistle1: at his mouth"}.get(frame)
        if label is None:
            label = "Call: the shriek, the lantern blazing in its hold" if state == "whistle" else "rest"
        gif.text(img, (6, 6), "whistle phase (immune %d s) %s" % (wt // 60, "| the middle is cut" if state == "whistle" and t >= wt - 24 else ""))
        gif.text(img, (6, H - 22), label, fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# 3. The diagonal dive
# ================================================================================================
def draw_diagonal(img, entry, exit_, alpha, scale=1.0):
    """DrawDiagonalTrack: a piece every RailDiagonalStep px each way, mirrored for a track running down to the left."""
    if alpha <= 0:
        return
    cell = KC["RailDiagonalCell"]
    piece = faded(RAIL_DIAG, 0.85 * alpha)
    sx = 1 if exit_[0] >= entry[0] else -1
    sy = 1 if exit_[1] >= entry[1] else -1
    if sx * sy < 0:
        piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
    step = KC["RailDiagonalStep"]
    count = int(abs(exit_[0] - entry[0]) / step)
    for k in range(count + 1):
        x, y = entry[0] + sx * step * k, entry[1] + sy * step * k
        img.alpha_composite(piece, (int(round(x - cell / 2)), int(round(y - cell / 2))))


def scene_diagonal(out, font):
    W, H = 1920, 1080
    player = (W / 2, H / 2 + 60)
    bg = town_backdrop(W, H, int(player[1] + 21))
    gif = Gif(font, (W, H), scale=0.5)
    rift = load(BOSS + "Projectiles/GhostRift.png")
    runs = [(1, 1), (1, -1)]                                       # towards his side (right), first down, then up
    tele = KC["PassiveTelegraph"]
    plan = []
    t0 = 20
    for dx, dy in runs:
        plan.append((t0, dx, dy))
        t0 += tele + 120
    trains = []
    total = t0 + 20
    diag = KC["Diagonal"] if "Diagonal" in KC else math.sqrt(0.5)
    half_run = KC["ScreenHalfHeight"] / diag
    for tick in range(total):
        img_needed = tick % TPF == 0
        for (start, dx, dy) in plan:
            if tick == start + tele:
                hx, hy = dx * diag, dy * diag
                entry = (player[0] - hx * half_run, player[1] - 21 - hy * half_run)
                trains.append(Train("diagonal", entry, (hx * KC["PassiveSpeed"], hy * KC["PassiveSpeed"]), 2 * half_run))
        trains = [tr for tr in trains if tr.update()]
        if not img_needed:
            continue
        img = bg.copy()
        for (start, dx, dy) in plan:
            k = tick - start
            if 0 <= k <= tele + 12:
                a = strength(k, tele)
                hx, hy = dx * diag, dy * diag
                entry = (player[0] - hx * half_run, player[1] - 21 - hy * half_run)
                exit_ = (player[0] + hx * half_run, player[1] - 21 + hy * half_run)
                draw_diagonal(img, entry, exit_, a)
                rc = KC["RiftCell"]
                f = max(0, min(KC["RiftFrames"] - 1, int(a * KC["RiftFrames"])))
                img.alpha_composite(faded(rift.crop((0, f * (rc + 2), rc, f * (rc + 2) + rc)), a), (int(entry[0] - rc / 2), int(entry[1] - rc / 2)))
        for tr in trains:
            tr.draw(img)
        img.alpha_composite(player_sprite(), (int(player[0] - 20), int(player[1] - 35)))
        gif.text(img, (16, 12), "the Diagonal dive (2026-11-09): a passive train at 45 degrees through the player, from the top or the bottom",
                 font=gif.big)
        gif.text(img, (16, 44), "1 s of warning (its track and rift), %d px/tick, towards his side; Express / Dive / Diagonal a third each"
                 % KC["PassiveSpeed"], font=gif.big)
        gif.push(img)
    gif.save(out)


# Train routes: the sim's Train class knows "express"/"dive"/"wave"/...; a diagonal is a straight span like them
_visibility = Train.visibility


def _vis(self, p):
    if self.route == "diagonal":
        s = (p[0] - self.sx) * self.ux + (p[1] - self.sy) * self.uy
        return max(0.0, min(1.0, s / KT["FadeIn"])) * max(0.0, min(1.0, (self.span - s) / KT["FadeOut"]))
    return _visibility(self, p)


Train.visibility = _vis


# ================================================================================================
# 4. His frames
# ================================================================================================
def sprites_png(out, font):
    boss = Conductor()
    cw, ch, cols = KC["CellWidth"], KC["CellHeight"], KC["Columns"]
    names = []
    for seq in ("Idle", "Whistle", "Call", "PointIn", "Point", "PointOut", "TipIn", "Tip", "TipOut", "Dying"):
        for k in range(int(KC[seq + "Frames"])):
            names.append((KC[seq] + k, "%s%d" % (seq, k)))
    per_row = 9
    rows = (len(names) + per_row - 1) // per_row
    sheet = Image.new("RGBA", (per_row * cw, 2 * rows * (ch + 18) + 80), (0, 0, 0, 255))
    d = ImageDraw.Draw(sheet)
    for half_, bgc in enumerate(((36, 40, 48, 255), (150, 180, 210, 255))):
        y0 = half_ * rows * (ch + 18)
        d.rectangle([0, y0, sheet.width, y0 + rows * (ch + 18)], fill=bgc)
        for i, (frame, name) in enumerate(names):
            x, y = (i % per_row) * cw, y0 + (i // per_row) * (ch + 18)
            tile = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            for sheet_ in boss.sheets:
                if sheet_ is not None:
                    tile.alpha_composite(boss.cell(sheet_, frame))
            sheet.alpha_composite(tile, (x, y + 16))
            d.text((x + 4, y + 2), name, fill=(238, 241, 243, 255))
    yb = 2 * rows * (ch + 18) + 8
    cell = KC["LanternGlowCell"]
    for k in range(KC["LanternGlowFrames"]):
        sheet.alpha_composite(HALO.crop((0, k * (cell + 2), cell, k * (cell + 2) + cell)), (8 + k * (cell + 8), yb))
    sheet.alpha_composite(RAIL_DIAG, (8 + 4 * (cell + 8) + 20, yb))
    d.text((8, yb + cell + 6), "the lantern's halo (4 frames) and the diagonal track piece", fill=(238, 241, 243, 255))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(out)
    print(out, sheet.size)


# ================================================================================================
# 5. The Cursed Train Whistle
# ================================================================================================
class MiniTrain:
    """GhostTrainEngine.Steer / Record / PlaceWagons step for step (the owner's side)."""
    ENGINE = [load(WEP + "GhostTrainEngine.png"), load(WEP + "GhostTrainEngine_Glow.png")]
    CAR = [load(WEP + "GhostTrainWagon.png"), load(WEP + "GhostTrainWagon_Glow.png")]

    def __init__(self, x, y, vx):
        self.x, self.y, self.vx, self.vy = x, y, vx, 0.0
        self.trail = []                                            # newest last
        self.wagons = 0
        self.places = []

    def steer(self, owner, target, tick):
        speed = math.hypot(self.vx, self.vy)
        angle = math.atan2(self.vy, self.vx) if speed > 0.01 else 0.0
        if target is not None:
            goal, want, turn = target, KW["ChargeSpeed"], KW["ChargeTurn"]
            if (goal[0] - self.x) ** 2 + (goal[1] - self.y) ** 2 < KW["PassThrough"] ** 2:
                turn = 0.0
        else:
            t = tick * KW["OrbitRate"]
            goal = (owner[0] + math.cos(t) * KW["OrbitRadius"], owner[1] - KW["OrbitHeight"] + math.sin(t) * KW["OrbitRadius"] * KW["OrbitFlatten"])
            far = math.hypot(goal[0] - self.x, goal[1] - self.y)
            want, turn = max(KW["IdleSpeed"], min(KW["ChargeSpeed"], far * 0.06)), KW["IdleTurn"]
        tx, ty = goal[0] - self.x, goal[1] - self.y
        if tx * tx + ty * ty > 1 and turn > 0:
            diff = (math.atan2(ty, tx) - angle + math.pi) % (2 * math.pi) - math.pi
            angle += max(-turn, min(turn, diff))
        speed += max(-KW["Accel"], min(KW["Accel"], want - speed))
        speed = max(1.0, speed)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        nx, ny = self.x + self.vx, self.y + self.vy
        if not self.trail or math.hypot(nx - self.trail[-1][0], ny - self.trail[-1][1]) >= KW["TrailStep"]:
            self.trail.append((nx, ny))
            self.trail = self.trail[-int(KW["TrailPoints"]):]
        self.x, self.y = nx, ny
        self.place()

    def place(self):
        """PlaceWagons + SampleTrail: each wagon at FirstSpacing + k Spacing back along the path, its heading over +-10 px."""
        def back(dist):
            acc, prev = 0.0, (self.x, self.y)
            dx, dy = -self.vx, -self.vy
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
            for p in reversed(self.trail):
                seg = math.hypot(p[0] - prev[0], p[1] - prev[1])
                if seg > 0.001:
                    dx, dy = (p[0] - prev[0]) / seg, (p[1] - prev[1]) / seg
                    if acc + seg >= dist:
                        return (prev[0] + dx * (dist - acc), prev[1] + dy * (dist - acc))
                    acc += seg
                    prev = p
            return (prev[0] + dx * (dist - acc), prev[1] + dy * (dist - acc))
        self.places = []
        for k in range(self.wagons):
            dist = KW["FirstSpacing"] + k * KW["Spacing"]
            at, ahead, behind = back(dist), back(max(0.0, dist - 10)), back(dist + 10)
            hx, hy = ahead[0] - behind[0], ahead[1] - behind[1]
            n = math.hypot(hx, hy) or 1.0
            self.places.append((at, (hx / n, hy / n)))

    def segments(self):
        n = math.hypot(self.vx, self.vy) or 1.0
        yield ((self.x, self.y), (self.vx / n, self.vy / n), True)
        for at, h in self.places:
            yield (at, h, False)

    def draw(self, img):
        for (at, (hx, hy), engine) in reversed(list(self.segments())):
            frame, flip = heading_frame(hx, hy)
            cell = 68 if engine else 56
            for j, sheet in enumerate(MiniTrain.ENGINE if engine else MiniTrain.CAR):
                c = sheet.crop((0, frame * (cell + 2), cell, frame * (cell + 2) + cell))
                if flip:
                    c = c.transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(faded(c, KW["Opacity"] if j == 0 else 1.0), (int(round(at[0] - cell / 2)), int(round(at[1] - cell / 2))))


def capsule_hits(center, heading, length, radius, box):
    half_ = length * 0.5 - radius
    for s in range(9):
        u = -half_ + 2 * half_ * s / 8
        px, py = center[0] + heading[0] * u, center[1] + heading[1] * u
        if box[0] - radius < px < box[2] + radius and box[1] - radius < py < box[3] + radius:
            return True
    return False


def scene_train(out, font):
    W, H, G = 860, 380, 350
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    owner = (260.0, float(G - 21))
    whistle = load(WEP + "CursedTrainWhistle.png")
    blows = [20, 90, 130, 170]
    dummy_at, dummy = 300, (640.0, float(G - 24))
    train = None
    cooldowns = {}
    pops = []
    total_hits = [0]
    notes = [(0, "Cursed Train Whistle (%d damage a segment, %d mana): the first blow calls the engine (1 slot)" % (KW["Damage"], KW["Mana"])),
             (90, "every further blow hitches on a wagon (1 slot each), like the Stardust Dragon; it floats round its owner"),
             (dummy_at, "an enemy in reach: it runs straight through, turns (%.2f rad/tick) and runs through again" % KW["ChargeTurn"]),
             (dummy_at + 150, "every segment hits once a pass (%d-tick immunity each): %d per wagon" % (KW["HitCooldown"], KW["Damage"]))]
    for tick in range(560):
        if tick == blows[0]:
            train = MiniTrain(owner[0], owner[1] - KW["OrbitHeight"], KW["IdleSpeed"])
        elif tick in blows[1:] and train is not None:
            train.wagons += 1
        target = dummy if tick >= dummy_at else None
        if train is not None:
            train.steer(owner, target, tick)
            if target is not None:
                box = (dummy[0] - 16, dummy[1] - 24, dummy[0] + 16, dummy[1] + 24)
                for k, (at, h, engine) in enumerate(train.segments()):
                    length = KW["EngineLength"] if engine else KW["CarLength"]
                    radius = KW["EngineRadius"] if engine else KW["CarRadius"]
                    if capsule_hits(at, h, length, radius, box) and tick - cooldowns.get(k, -999) >= KW["HitCooldown"]:
                        cooldowns[k] = tick
                        total_hits[0] += 1
                        pops.append((tick, dummy[0] - 8 + (k % 3) * 8, dummy[1] - 60 - (k % 2) * 12, str(int(KW["Damage"])), AETHER))
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        if tick >= dummy_at:
            d.rectangle([dummy[0] - 16, dummy[1] - 24, dummy[0] + 16, dummy[1] + 24], fill=(138, 90, 60, 255), outline=(47, 27, 20, 255))
            d.line([dummy[0], dummy[1] + 24, dummy[0], G], fill=(91, 54, 38, 255), width=3)
        img.alpha_composite(player_sprite(), (int(owner[0] - 20), int(G - 56)))
        if any(0 <= tick - b < 36 for b in blows):
            img.alpha_composite(whistle, (int(owner[0] - whistle.width / 2), int(G - 56 - whistle.height + 4)))
        if train is not None:
            train.draw(img)
        for (t0, x, y, s, col) in pops:
            if tick - t0 < 40:
                gif.text(img, (int(x), int(y - (tick - t0) * 0.5)), s, fill=col)
        note = [n for (t0, n) in notes if tick >= t0][-1]
        gif.text(img, (8, 6), note)
        slots = 0 if train is None else 1 + train.wagons
        gif.text(img, (8, H - 22), "slots used: %d (engine + %d wagons) | segment hits on the dummy: %d" % (slots, 0 if train is None else train.wagons, total_hits[0]),
                 fill=STEAM)
        gif.push(img)
    gif.save(out)


def measure_passes():
    """The pass period on a still 32x48 target (GhostTrainEngine.PassTicks): the engine's hits after the first few."""
    owner = (0.0, 0.0)
    tr = MiniTrain(-300.0, -100.0, KW["IdleSpeed"])
    target = (0.0, 0.0)
    hits, last = [], -999
    for tick in range(60 * 30):
        tr.steer(owner, target, tick)
        at, h, _ = next(tr.segments())
        if capsule_hits(at, h, KW["EngineLength"], KW["EngineRadius"], (-16, -24, 16, 24)) and tick - last >= KW["HitCooldown"]:
            hits.append(tick)
            last = tick
    gaps = [b - a for a, b in zip(hits, hits[1:])][3:]
    return sum(gaps) / max(1, len(gaps))


# ================================================================================================
# 6. Items
# ================================================================================================
def items_png(out, font):
    gems = "Content/Gems/"
    pics = [(load(gems + "Items/Jade.png"), "Jade"), (load(gems + "Items/LargeJade.png"), "Large Jade"),
            (load(gems + "Items/JadePhaseblade.png"), "Jade Phaseblade"), (load(gems + "Items/JadePhasesaber.png"), "Jade Phasesaber"),
            (load(gems + "Items/JadeRobe.png"), "Jade Robe"), (load("Content/OldBrassTown/Items/LawHat.png"), "Law Hat"),
            (load("Content/Mechanist/Armor/BrassHelmet.png"), "Brass Helmet"), (load("Content/Mechanist/Armor/BrassChestplate.png"), "Brass Chestplate"),
            (load("Content/Mechanist/Armor/BrassGreaves.png"), "Brass Greaves"), (load(WEP + "CursedTrainWhistle.png"), "Cursed Train Whistle"),
            (load(WEP + "GhostTrainBuff.png"), "its buff"), (load(WEP + "CursedLantern.png"), "Cursed Lantern (smaller)")]
    frames = terrain.load_frames("art/templates/terrain_exposure.json")
    sheet = load(gems + "Tiles/JadeTile.png")
    cluster = terrain.render(["..##....", ".####...", "######..", ".#####.#", "..###.##", "...#####"], {"#": sheet}, frames,
                             background=(70, 76, 90))
    col_w = 120
    W = col_w * 6
    out_im = Image.new("RGBA", (W, 2 * 92 + cluster.height + 40), (36, 40, 48, 255))
    d = ImageDraw.Draw(out_im)
    for i, (im, name) in enumerate(pics):
        x, y = (i % 6) * col_w, (i // 6) * 92
        big = im.resize((im.width * 2, im.height * 2), Image.NEAREST) if im.width <= 40 else im
        out_im.alpha_composite(big, (x + (col_w - big.width) // 2, y + 8 + max(0, (60 - big.height) // 2)))
        d.text((x + 6, y + 74), name, fill=(238, 241, 243, 255))
    yc = 2 * 92
    out_im.alpha_composite(cluster, (8, yc + 8))
    d.text((cluster.width + 20, yc + 16), "Jade in the rock (JadeTile, framed by terrain.py).", fill=(238, 241, 243, 255))
    d.text((cluster.width + 20, yc + 34), "In game it frames as stone (Main.tileStone): set in", fill=(238, 241, 243, 255))
    d.text((cluster.width + 20, yc + 52), "stone it shows no outline, like vanilla's gems.", fill=(238, 241, 243, 255))
    out_im = out_im.resize((out_im.width * 2, out_im.height * 2), Image.NEAREST)
    out_im.save(out)
    print(out, out_im.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    jobs = [("targeting", lambda: scene_targeting(os.path.join(args.out, "2026-11-09_boss-cursed-conductor-targeting.gif"), args.font)),
            ("whistle", lambda: scene_whistle(os.path.join(args.out, "2026-11-09_boss-cursed-conductor-whistle.gif"), args.font)),
            ("diagonal", lambda: scene_diagonal(os.path.join(args.out, "2026-11-09_boss-cursed-conductor-diagonal.gif"), args.font)),
            ("sprites", lambda: sprites_png(os.path.join(args.out, "2026-11-09_boss-cursed-conductor-sprites.png"), args.font)),
            ("train", lambda: scene_train(os.path.join(args.out, "2026-11-09_weapon-cursed-train-whistle.gif"), args.font)),
            ("items", lambda: items_png(os.path.join(args.out, "2026-11-09_items-jade-brass-lawhat.png"), args.font)),
            ("passes", lambda: print("train pass period: %.1f ticks (PassTicks %d)" % (measure_passes(), KW["PassTicks"])))]
    only = set(args.only.split(",")) if args.only else None
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
