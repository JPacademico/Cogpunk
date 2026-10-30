"""D5 proofs for the Mech Army invasion (2026-10-27): the real sprites (Content/MechArmy, 2x art = game px) and the
constants parsed out of the C# files and the generated MechArmyRigData.cs, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/mech_army_sim.py --out docs/media --date 2026-10-28 [--only roster,alarm,boombot,jaeger,progress,sprites,alarmhead]

Writes <date>_event-mech-army-<scene>.gif|png:
    roster    the four enemies animating (three planes each, DepthLayers' horizontal parallax), the Jaeger walking with
              its root motion next to a player for scale.
    alarm     two lanes of three Rogue Mice-bots racing a player: without and with an Annoy-o-tron escorting them (its
              alarm ring, 15 tiles since 2026-10-28; hasted enemies pulse red and run 50% faster; it keeps pace).
    boombot   (2026-10-28) a Boombot sprinting at a player, beeping faster as it closes in (fuse flares), detonating on
              touch (the blast sheet, 70 in Expert, knockback 7); a second one trips (forced here; 2% a second of
              sprinting in game): stumbles, falls face first, rolls on its momentum (roll frames by distance), stops,
              fizzes for the telegraph and blows up where it lies, short of the player.
    alarmhead (2026-10-28) the Alarm Head's two friendly Alarmobos following a running player, the 15-tile ring of each,
              and the stacked bonus (+20% movement and +10% attack speed each) that a second player gets in and out of range.
    jaeger     the Jaeger turning to a player behind it (30 ticks), walking at it (root motion: 6 px per frame change, 8 ticks
              a frame), heel strikes, and the contact: 100 in Expert, thrown with knockback 13. Prints the planted-foot slip.
    progress  the invasion's chat warnings and progress bar (the vanilla layout, mocked: vanilla's bar texture is not in
              the repo), from "approaching" to "defeated", with the Jaeger joining at 50%.
    sprites   PNG: every frame of every enemy (planes composited) over a dark and a light background (D4 check).

Leaves out: lighting, tile collision beyond a flat floor, the pounce of the Mice-bots in the alarm lanes, the player's
own animation (a standing frame slides) and its exact physics after a hit (gravity 0.4, a simple ground friction),
network latency.
"""
import argparse
import math
import os
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "art", "mecharmy"))
from update_2026_10_27_sim import consts, Gif, backdrop, polished_player, TPF  # noqa: E402
import make_mecharmy_art as art  # noqa: E402

D = "Content/MechArmy/"
RIG = D + "MechArmyRigData.cs"


def arrays(path):
    s = open(path, encoding="utf-8").read()
    return {m.group(1): [int(v) for v in re.findall(r"-?\d+", m.group(2))]
            for m in re.finditer(r"public static readonly (?:short|byte|int)\[\] (\w+) = \{([^}]*)\};", s)}


R = consts(RIG)
RA = arrays(RIG)
KM = consts(RIG, D + "NPCs/MechWalker.cs", "Core/Templates/GridWalkerNPC.cs", D + "NPCs/RogueMiceBot.cs")
KB = consts(RIG, D + "NPCs/MechWalker.cs", "Core/Templates/GridWalkerNPC.cs", D + "NPCs/Boombot.cs", D + "Projectiles/BoombotBlast.cs")
KA = consts(RIG, D + "NPCs/MechWalker.cs", "Core/Templates/GridWalkerNPC.cs", D + "NPCs/AnnoyOTron.cs", "Core/Systems/NPCHaste.cs")
KY = consts(RIG, D + "NPCs/Jaeger.cs")
KI = consts(D + "MechArmyInvasion.cs", "Core/Events/CogpunkInvasion.cs")
PAD = R["CellPadding"]

_cache = {}


def sheet(name):
    if name not in _cache:
        for path in (D + "NPCs/" + name + ".png", D + "Minions/" + name + ".png", name):
            if os.path.exists(path):
                _cache[name] = Image.open(path).convert("RGBA")
                break
        else:
            _cache[name] = None                          # a plane this sprite doesn't have (DepthLayers skips it too)
    return _cache[name]


def cell(name, frame, cw, ch):
    im = sheet(name)
    return None if im is None else im.crop((0, frame * (ch + PAD), cw, frame * (ch + PAD) + ch))


def scale_rgb(im, k):
    r, g, b, a = im.split()
    return Image.merge("RGBA", tuple(c.point(lambda v: int(v * k)) for c in (r, g, b)) + (a,))


def with_alpha(im, k):
    r, g, b, a = im.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * k))))


def tint(im, col, amount):
    over = Image.new("RGBA", im.size, col + (255,))
    mixed = Image.blend(im, over, amount)
    mixed.putalpha(im.getchannel("A"))
    return mixed


def paste(dst, im, x, y):
    x, y = int(round(x)), int(round(y))
    l, t = max(0, x), max(0, y)
    r, b = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if r <= l or b <= t:
        return
    dst.alpha_composite(im.crop((l - x, t - y, r - x, b - y)), (l, t))


def parallax(anchor_x, depth, max_shift, screen_w):
    """DepthLayers.Shift, horizontal part: (anchor - centre) / half-width, clamped, times the depth, snapped to 2 px."""
    half = screen_w / 2.0
    dx = max(-1.5, min(1.5, (anchor_x - half) / half))
    v = max(-max_shift * 1.5, min(max_shift * 1.5, dx * max_shift * depth))
    return round(v * 0.5) * 2


WALKERS = {"mice": ("RogueMiceBot", "Mice"), "boombot": ("Boombot", "Boombot"), "annoy": ("AnnoyOTron", "Annoy"),
           "alarmobo": ("AlarmoboMinion", "Annoy")}


def draw_walker(dst, kind, frame, ax, ay, flip, screen_w, glow=1.0, red=0.0, beacon_frame=0):
    name, key = WALKERS[kind]
    cw, ch, ox, oy = R[key + "CellWidth"], R[key + "CellHeight"], R[key + "OriginX"], R[key + "OriginY"]
    layers = ((name + "_Far", -1), (name, 0))
    for layer, depth in layers + ((name + "_Glow", 0), (name + "_Near", 1)):
        im = cell(layer, frame, cw, ch)
        if im is None:
            continue
        if layer.endswith("_Glow"):
            if glow <= 0:
                continue
            im = with_alpha(im, glow)
        elif depth < 0:
            im = scale_rgb(im, 0.88)
        if red > 0 and not layer.endswith("_Glow"):
            im = tint(im, (236, 113, 40), red)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        sx = parallax(ax, depth, KM["MaxParallax"], screen_w) if depth else 0
        left = ax - (cw - ox if flip else ox) + sx
        paste(dst, im, left, ay - oy)
        if kind in ("annoy", "alarmobo") and layer == name:
            bob = RA["AnnoyBeaconY"][frame]
            for b in (name + "_Beacon", name + "_BeaconGlow"):
                bim = cell(b, beacon_frame, cw, ch)
                if flip:
                    bim = bim.transpose(Image.FLIP_LEFT_RIGHT)
                paste(dst, bim, ax - (cw - ox if flip else ox), ay - oy + bob)


def jaeger_part(layer, frame):
    t = RA["Jaeger" + layer + "Frames"][frame * 7:frame * 7 + 7]
    page, x, y, w, h, ox, oy = t
    base = {"Body": "Jaeger", "Glow": "Jaeger_Glow", "Near": "Jaeger_Near", "Far": "Jaeger_Far"}[layer]
    name = base if page == 0 else base + "_Page%d" % page
    if w <= 0:
        return None, 0, 0
    return sheet(name).crop((x, y, x + w, y + h)), ox, oy


def draw_jaeger(dst, frame, ax, ay, flip, screen_w, glow=0.9):
    for layer, depth in (("Far", -1), ("Body", 0), ("Glow", 0), ("Near", 1)):
        im, ox, oy = jaeger_part(layer, frame)
        if im is None:
            continue
        visible = min(im.height, oy + 2)
        im = im.crop((0, 0, im.width, visible))
        if layer == "Far":
            im = scale_rgb(im, 0.88)
        if layer == "Glow":
            im = with_alpha(im, glow)
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        sx = parallax(ax, depth, KY["MaxParallax"], screen_w) if depth else 0
        paste(dst, im, ax - (im.width - ox if flip else ox) + sx, ay - oy)


def jaeger_strips(frame, ax, ay, flip):
    n = R["JaegerStrips"]
    out = []
    for k in range(n):
        x0, y0, x1, y1 = RA["JaegerHit"][(frame * n + k) * 4:(frame * n + k) * 4 + 4]
        if x1 <= x0:
            continue
        left = ax - x1 if flip else ax + x0
        out.append((left, ay + y0, left + (x1 - x0), ay + y1))
    return out


def hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


PLAYER = None


def player_img(flip=False):
    global PLAYER
    if PLAYER is None:
        PLAYER = polished_player()
    return PLAYER.transpose(Image.FLIP_LEFT_RIGHT) if flip else PLAYER


def draw_player(dst, cx, bottom, flip=False):
    im = player_img(flip)
    paste(dst, im, cx - im.width / 2, bottom - im.height + 2)


def pop(gif, img, xy, s, col=(255, 199, 90)):
    gif.text(img, (int(xy[0]), int(xy[1])), s, fill=col, big=True)


# ================================================================================================
# Scenes
# ================================================================================================
def scene_roster(out, font):
    W, H, G = 960, 420, 392
    gif = Gif(font)
    bg = backdrop(W, H, G)
    ticks = 8 * 60
    yx = 820.0
    phase = 0.0
    tpf = KY["TicksPerFrame"]
    step = R["JaegerStep"]
    beep = 0
    for t in range(ticks):
        before = int(phase // tpf)
        phase = (phase + 1) % (tpf * R["JaegerWalkFrames"])
        after = int(phase // tpf)
        if after != before:
            yx -= step                                   # root motion: left-facing, moving left
        if t % TPF:
            continue
        img = bg.copy()
        # small enemies on the left, each cycling its run/drive frames by distance at its top speed
        dist_m = t * KM["RunSpeed"]
        fm = int(R["MiceRun"] + (dist_m / KM["RunAnimDistance"]) % R["MiceRunFrames"])
        draw_walker(img, "mice", fm, 70, G, False, W)
        dist_b = t * KB["RunSpeed"]
        fb = int(R["BoombotRun"] + (dist_b / KB["RunAnimDistance"]) % R["BoombotRunFrames"])
        lamp = 1.0 if (t // 6) % 4 == 0 else 0.55
        draw_walker(img, "boombot", fb, 210, G, False, W, glow=lamp)
        dist_a = t * KA["FollowSpeed"]
        fa = int(R["AnnoyDrive"] + (dist_a / KA["RunAnimDistance"]) % R["AnnoyDriveFrames"])
        draw_walker(img, "annoy", fa, 340, G, False, W, beacon_frame=(t // KA["BeaconTicks"]) % R["BeaconFrames"])
        draw_jaeger(img, R["JaegerWalk"] + after % R["JaegerWalkFrames"], round(yx), G, False, W, glow=0.8 + 0.2 * math.sin(t / 20))
        draw_player(img, 935, G)
        gif.text(img, (22, G + 8), "Rogue Mice-bot")
        gif.text(img, (180, G + 8), "Boombot")
        gif.text(img, (296, G + 8), "Annoy-o-tron")
        gif.text(img, (905, G + 8), "player")
        gif.text(img, (12, 10), "Mech Army: three planes each (far, middle + glow, near), horizontal parallax", big=True)
        gif.text(img, (12, 36), "Jaeger: 302 px tall (the player ~50 px), walking 0.75 px/tick by root motion: %d px a frame, %d ticks a frame" % (step, tpf))
        gif.push(img)
    gif.save(out)


def scene_alarm(out, font):
    W, H = 960, 320
    lanes = (140, 300)
    gif = Gif(font)
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        d.line([0, y, W, y], fill=(118 + y // 8, 150 + y // 10, 190, 255))
    for g in lanes:
        d.rectangle([0, g, W, g + 18], fill=(120, 92, 60, 255))
        d.rectangle([0, g, W, g + 3], fill=(147, 110, 70, 255))
    rng = KA["AlarmRange"]
    goal = 880.0

    class Mob:
        def __init__(self, x):
            self.x, self.vx, self.fc, self.haste, self.done = x, 0.0, 0.0, 0, None

    mice = [[Mob(x) for x in (60.0, 100.0, 140.0)] for _ in lanes]
    annoy = Mob(16.0)
    annoy_fc = 0.0
    tick = 0
    while tick < 9 * 60:
        tick += 1
        # Annoy-o-tron (lane 2): follow the closest mouse, keep pace, sound the alarm every AlarmRefresh ticks
        leader = min(mice[1], key=lambda m: abs(m.x - annoy.x))
        dx = leader.x - annoy.x
        direction = 1 if abs(dx) > KA["KeepDistance"] else 0
        speed = max(KA["FollowSpeed"], min(KA["MaxFollowSpeed"], abs(leader.vx) + KA["PaceMargin"]))
        accel = KA["Accel"] * speed / KA["FollowSpeed"]
        want = direction * speed
        annoy.vx = min(want, annoy.vx + accel) if annoy.vx < want else max(want, annoy.vx - accel)
        annoy.x += annoy.vx
        annoy_fc += abs(annoy.vx)
        if tick % KA["AlarmRefresh"] == 0:
            for m in mice[1]:
                if abs(m.x - annoy.x) <= rng:
                    m.haste = max(m.haste, KA["HasteTicks"])
        for lane, ms in enumerate(mice):
            for m in ms:
                if m.done is not None:
                    continue
                h = KA["Factor"] if m.haste > 0 else 1.0
                want = KM["RunSpeed"] * h
                m.vx = min(want, m.vx + KM["Accel"] * h)
                m.x += m.vx
                m.fc += abs(m.vx)
                if m.haste > 0:
                    m.haste -= 1
                if m.x >= goal:
                    m.done = tick
        if all(m.done is not None for ms in mice for m in ms) and tick > max(m.done for ms in mice for m in ms) + 45:
            break
        if tick % TPF:
            continue
        img = bg.copy()
        dd = ImageDraw.Draw(img)
        for lane, g in enumerate(lanes):
            draw_player(img, 915, g, flip=True)
        # the alarm ring (10 tiles), dashed ember
        cx, cy = annoy.x, lanes[1] - 44
        for a in range(0, 360, 6):
            if (a // 6) % 2 == 0:
                r0 = math.radians(a)
                r1 = math.radians(a + 4)
                dd.line([cx + math.cos(r0) * rng, cy + math.sin(r0) * rng, cx + math.cos(r1) * rng, cy + math.sin(r1) * rng], fill=(236, 113, 40, 255), width=2)
        fa = int(R["AnnoyDrive"] + (annoy_fc / KA["RunAnimDistance"]) % R["AnnoyDriveFrames"]) if abs(annoy.vx) > 0.3 else R["AnnoyIdle"]
        draw_walker(img, "annoy", fa, round(annoy.x), lanes[1], True, W, beacon_frame=(tick // KA["BeaconTicks"]) % R["BeaconFrames"])
        pulse = 0.5 + 0.5 * math.sin(tick / 60 * 12)
        for lane, ms in enumerate(mice):
            for m in ms:
                f = int(R["MiceRun"] + (m.fc / KM["RunAnimDistance"]) % R["MiceRunFrames"])
                red = (0.18 + 0.17 * pulse) if m.haste > 0 else 0.0
                draw_walker(img, "mice", f, round(min(m.x, goal)), lanes[lane], True, W, red=red)
        t1 = [m.done for m in mice[0] if m.done]
        t2 = [m.done for m in mice[1] if m.done]
        gif.text(img, (12, 8), "No alarm: top speed %.1f px/tick, acceleration %.2f" % (KM["RunSpeed"], KM["Accel"]))
        gif.text(img, (12, lanes[0] + 22), "With an Annoy-o-tron: +50%% (%.1f px/tick) within %d tiles; it keeps pace (up to %.0f)" % (KM["RunSpeed"] * KA["Factor"], rng // 16, KA["MaxFollowSpeed"]))
        if t1:
            gif.text(img, (650, 8), "last arrival %.2f s" % (max(t1) / 60) if len(t1) == 3 else "first arrival %.2f s" % (min(t1) / 60), fill=(255, 199, 90))
        if t2:
            gif.text(img, (650, lanes[0] + 22), "last arrival %.2f s" % (max(t2) / 60) if len(t2) == 3 else "first arrival %.2f s" % (min(t2) / 60), fill=(255, 199, 90))
        gif.push(img)
    print("alarm: last mouse in %.2f s without, %.2f s with" % (max(m.done for m in mice[0]) / 60, max(m.done for m in mice[1]) / 60))
    gif.save(out)


ROLL_ANIM = 2 * math.pi * R["BoombotRadius"] / R["BoombotRollFrames"]   # = Boombot.RollAnimDistance
NPC_GRAVITY = 0.3                                     # vanilla NPC gravity (decompiled NPC.UpdateNPC_UpdateGravity)


def scene_boombot(out, font):
    W, H, G = 960, 260, 228
    gif = Gif(font)
    bg = backdrop(W, H, G)
    blast_sheet = Image.open(D + "Projectiles/BoombotBlast.png").convert("RGBA")
    bs = R["BlastSize"]

    class Bot:
        def __init__(self, x, start, trip_at=None):
            self.x, self.vx, self.vy, self.y, self.fc, self.start = x, 0.0, 0.0, 0.0, 0.0, start
            self.beep, self.lamp = 0, 0
            self.state, self.t, self.at = "wait", 0, None   # wait, run, trip, fall, roll, fizz, blown
            self.trip_at, self.roll_frame = trip_at, 0

    px, pvx, py, pvy = 860.0, 0.0, 0.0, 0.0            # player centre x, velocity, height above ground
    a = Bot(40.0, 1)                                   # reaches the player and detonates
    b = Bot(20.0, 200, trip_at=330.0)                  # trips (forced: in game a 2% roll each second at a sprint)
    pops = []
    for tick in range(1, 10 * 60):
        for bot in (a, b):
            if bot.state == "wait" and tick >= bot.start:
                bot.state, bot.t = "run", 0
            if bot.state in ("wait", "blown"):
                continue
            bot.t += 1
            if bot.state == "run":
                bot.vx = min(KB["RunSpeed"], bot.vx + KB["Accel"])
                if bot.trip_at is not None and bot.x >= bot.trip_at:
                    bot.state, bot.t = "trip", 0
            elif bot.state == "trip":
                bot.vx *= 0.94
                if bot.t >= KB["TripTicks"]:
                    bot.vx = max(abs(bot.vx) * KB["FallPush"], KB["MinRollSpeed"])
                    bot.vy = KB["FallHop"]
                    bot.state, bot.t = "fall", 0
            elif bot.state == "roll":
                bot.vx *= KB["RollFriction"]
                bot.fc += abs(bot.vx)
                while bot.fc >= ROLL_ANIM:
                    bot.fc -= ROLL_ANIM
                    bot.roll_frame = (bot.roll_frame + 1) % R["BoombotRollFrames"]
                if abs(bot.vx) < KB["RollStopSpeed"] or bot.t >= KB["RollMaxTicks"]:
                    bot.state, bot.t = "fizz", 0
            elif bot.state == "fizz":
                bot.vx *= 0.8
                if bot.t >= KB["FizzTicks"]:
                    bot.state, bot.t, bot.at = "blown", tick, (bot.x, G - R["BoombotRadius"])
            if bot.state == "fall":
                bot.y += bot.vy
                bot.vy -= NPC_GRAVITY
                if bot.y <= 0 and bot.t > 4:
                    bot.y, bot.vy = 0.0, 0.0
                    bot.state, bot.t = "roll", 0
            bot.x += bot.vx
            if bot.state == "run":
                bot.fc += abs(bot.vx)
            if bot.lamp > 0:
                bot.lamp -= 1
            dist = abs(px - bot.x)
            if bot.state == "run" and dist <= KB["BeepRange"]:
                bot.beep -= 1
                if bot.beep <= 0:
                    close = 1 - dist / KB["BeepRange"]
                    bot.beep = int(KB["BeepSlowest"] + (KB["BeepFastest"] - KB["BeepSlowest"]) * close * close)
                    bot.lamp = KB["LampFlashTicks"]
            elif bot.state == "fizz":
                bot.beep -= 1
                if bot.beep <= 0:
                    bot.beep, bot.lamp = KB["BeepFastest"], KB["LampFlashTicks"]
            m = KB["TouchMargin"]
            top = KB["RollHeight"] if bot.state in ("roll", "fizz") else KB["Height"]
            if bot.state != "blown" and hit((bot.x - 13 - m, G - bot.y - top - m, bot.x + 13 + m, G - bot.y + m), (px - 10, G - 42 - py, px + 10, G - py)):
                bot.state, bot.at, bot.t = "blown", (bot.x, G - 17), tick
                k = KB["BlastKnockback"]
                pvx, pvy, py = k * (1 if px >= bot.x else -1), k * 7 / 9, 0.01
                pops.append([px, G - 70, 0, "%d" % KB["BlastDamage"]])
        if py > 0:
            py += pvy
            pvy -= 0.4
            if py <= 0:
                py, pvy = 0.0, 0.0
            pvx *= 0.97
        else:
            pvx *= 0.8
        px = max(20.0, min(W - 20.0, px + pvx))
        pops = [[x, y - 0.6, age + 1, s] for x, y, age, s in pops if age < 50]
        if tick % TPF:
            continue
        img = bg.copy()
        draw_player(img, px, G - py, flip=True)
        for bot in (a, b):
            ax = round(bot.x)
            if bot.state == "run":
                f = int(R["BoombotRun"] + (bot.fc / KB["RunAnimDistance"]) % R["BoombotRunFrames"])
                draw_walker(img, "boombot", f, ax, G, True, W, glow=1.0 if bot.lamp > 0 else 0.55)
                if bot.lamp > 0:
                    gif.text(img, (ax - 14, G - 70), "beep", fill=(255, 199, 90))
            elif bot.state == "trip":
                draw_walker(img, "boombot", R["BoombotTrip"], ax, G, True, W)
                gif.text(img, (ax - 30, G - 70), "a foot catches!", fill=(255, 199, 90))
            elif bot.state == "fall":
                draw_walker(img, "boombot", R["BoombotTrip"] if bot.t < 6 else R["BoombotFall"], ax, G - round(bot.y), True, W)
            elif bot.state in ("roll", "fizz"):
                fizz = bot.state == "fizz"
                glow = (0.7 + 0.3 * ((bot.t // 3) % 2)) if fizz else 0.55
                draw_walker(img, "boombot", R["BoombotRoll"] + bot.roll_frame, ax, G, True, W, glow=glow)
                if fizz:
                    dd = ImageDraw.Draw(img)
                    for k in range(3):
                        ang = (tick * 0.7 + k * 2.1)
                        sx, sy = ax + math.cos(ang) * (6 + k * 3), G - 30 + math.sin(ang) * 5
                        dd.rectangle([sx, sy, sx + 2, sy + 2], fill=(255, 199, 90, 255))
                    gif.text(img, (ax - 44, G - 72), "fizzing: %d ticks" % (KB["FizzTicks"] - bot.t), fill=(255, 199, 90))
                else:
                    gif.text(img, (ax - 30, G - 66), "rolling %.1f" % abs(bot.vx), fill=(238, 241, 243))
            elif bot.state == "blown" and tick - bot.t < KB["LifeTicks"]:
                age = tick - bot.t
                fr = min(R["BlastFrames"] - 1, age // KB["TicksPerFrame"])
                im = blast_sheet.crop((0, fr * (bs + 2), bs, fr * (bs + 2) + bs))
                fade = 1.0 if age < KB["LifeTicks"] - 8 else max(0.0, (KB["LifeTicks"] - age) / 8)
                paste(img, with_alpha(im, fade), bot.at[0] - bs / 2, bot.at[1] - bs / 2)
        for x, y, age, s in pops:
            pop(gif, img, (x - 10, y), s)
        gif.text(img, (12, 8), "Boombot: %.0f px/tick, %d life; touch -> blast %d in Expert within %d px, knockback %.0f; spent: no loot" % (KB["RunSpeed"], KB["Life"], KB["BlastDamage"], KB["Radius"], KB["BlastKnockback"]))
        gif.text(img, (12, 28), "Trip: %d%% each %d ticks at a sprint -> stumble %d t, fall, roll (friction %.3f), fizz %d t, blast where it stops" % (round(KB["TripChance"] * 100), KB["TripCheckInterval"], KB["TripTicks"], KB["RollFriction"], KB["FizzTicks"]))
        gif.push(img)
    gif.save(out)


def scene_alarmhead(out, font):
    """The Alarm Head: two friendly Alarmobos follow a running player; a second player walks in and out of range."""
    W, H, G = 960, 300, 268
    gif = Gif(font)
    bg = backdrop(W, H, G)
    KH = consts(D + "Minions/AlarmoboMinion.cs", D + "Minions/AlarmPlayer.cs", D + "NPCs/AnnoyOTron.cs")
    rng = KH["AlarmRange"]
    owner_x, owner_v = 140.0, 0.0
    bots = [[60.0, 0.0, 0.0], [20.0, 0.0, 0.0]]          # x, vx, distance (drive frames)
    other_x = 900.0
    for tick in range(1, 8 * 60):
        # the owner runs right for 4 s, then stands; the second player walks left through the pack and out again
        target_v = 2.6 if tick < 200 else 0.0
        owner_v += max(-0.2, min(0.2, target_v - owner_v))
        owner_x += owner_v
        other_x += -1.6 if tick < 280 else 2.2
        for k, bot in enumerate(bots):
            spot = owner_x - (KH["FollowOffset"] + KH["FollowSpacing"] * k)
            dx = spot - bot[0]
            if abs(dx) > 20:
                mx = KH["RunSpeed"] if abs(dx) > 160 else KH["WalkSpeed"]
                bot[1] = max(-mx, min(mx, bot[1] + (1 if dx > 0 else -1) * KH["Acceleration"]))
            else:
                bot[1] *= 0.85
            bot[0] += bot[1]
            bot[2] += abs(bot[1])
        if tick % TPF:
            continue
        img = bg.copy()
        dd = ImageDraw.Draw(img)
        for bot in bots:                               # each Alarmobo's ring, dashed verdigris
            cx, cy = bot[0], G - 40
            for ang in range(0, 360, 8):
                if (ang // 8) % 2 == 0:
                    r0, r1 = math.radians(ang), math.radians(ang + 5)
                    dd.line([cx + math.cos(r0) * rng, cy + math.sin(r0) * rng, cx + math.cos(r1) * rng, cy + math.sin(r1) * rng],
                            fill=(140, 201, 176, 255), width=3)
        for bot in bots:
            moving = abs(bot[1]) > 0.3
            f = int(R["AnnoyDrive"] + (bot[2] / KH["RunAnimDistance"]) % R["AnnoyDriveFrames"]) if moving else R["AnnoyIdle"] + (tick // 8) % 2
            draw_walker(img, "alarmobo", f, round(bot[0]), G, bot[1] > 0.15 or not moving, W, beacon_frame=(tick // KH["BeaconTicks"]) % R["BeaconFrames"])
        draw_player(img, owner_x, G)
        draw_player(img, other_x, G, flip=True)
        def heard(x):
            return sum(1 for bot in bots if abs(bot[0] - x) <= rng)
        for x, label in ((owner_x, "owner"), (other_x, "ally")):
            n = heard(x)
            gif.text(img, (int(x) - 40, G - 76), "%s: %d in range" % (label, n), fill=(140, 201, 176) if n else (195, 200, 205))
            if n:
                gif.text(img, (int(x) - 40, G - 92), "+%d%% move, +%d%% attack" % (n * KH["MoveSpeedPerAlarm"], n * KH["AttackSpeedPerAlarm"]), fill=(255, 241, 51))
        gif.text(img, (12, 8), "Alarm Head: each Alarmobo (1 minion slot) follows its owner; every player within %d tiles of one" % (rng // 16))
        gif.text(img, (12, 28), "gets +%d%% movement and +%d%% attack speed, stacking per Alarmobo in range (owner or not)" % (KH["MoveSpeedPerAlarm"], KH["AttackSpeedPerAlarm"]))
        gif.push(img)
    gif.save(out)


def scene_jaeger(out, font):
    W, H, G = 960, 430, 400
    gif = Gif(font)
    bg = backdrop(W, H, G)
    tpf, step, nwalk = KY["TicksPerFrame"], R["JaegerStep"], R["JaegerWalkFrames"]
    yx, direction = 360.0, -1                          # facing left; the player starts behind it
    state, timer, phase, turn_to = "walk", 0, 0.0, 0
    px, pvx, py, pvy, immune = 900.0, 0.0, 0.0, 0.0, 0
    puffs, pops = [], []
    shake = 0
    planted_world = {}
    for tick in range(1, 9 * 60):
        timer += 1
        frame = None
        if state == "turn":
            if timer == KY["TurnTicks"] // 2:
                direction = turn_to
            if timer >= KY["TurnTicks"]:
                state, timer = "walk", 0
            frame = R["JaegerIdle"] + (timer // 16) % R["JaegerIdleFrames"]
        else:
            if (px - yx) * direction < 0 and abs(px - yx) > KY["TurnHysteresis"]:
                state, timer, turn_to = "turn", 0, -direction
                frame = R["JaegerIdle"]
            else:
                before = int(phase // tpf)
                phase = (phase + 1) % (tpf * nwalk)
                after = int(phase // tpf)
                if after != before:
                    yx += direction * step               # root motion
                    if RA["JaegerFootfall"][after % nwalk]:
                        puffs.append([yx, 0])
                        shake = 8
                frame = R["JaegerWalk"] + after % nwalk
                # planted foot check: the near ankle while planted (walk frames 0..12), in world px
                f = after % nwalk
                if f <= nwalk // 2:
                    ax = art.FOOT_NEAR_X + art.foot_cycle(f)[0]
                    world = yx + (ax * 2 if direction < 0 else -ax * 2)
                    cycle = int(tick // (tpf * nwalk))
                    planted_world.setdefault((cycle, direction), []).append(world)
        # the player walks at the Jaeger after it turns, gets hit and thrown
        if immune > 0:
            immune -= 1
        if py > 0 or pvy != 0:
            py += pvy
            pvy -= 0.4
            if py <= 0:
                py, pvy = 0.0, 0.0
            pvx *= 0.97                                  # air drag (approximated)
            px = max(20.0, min(W - 20.0, px + pvx))
        else:
            pvx *= 0.8
            px += pvx
            if state == "walk" and tick > 60 and abs(pvx) < 0.5:
                px -= 1.5 if px > yx else -1.5
        flip = direction == 1
        if frame is not None and immune == 0:
            pbox = (px - 10, G - 42 - py, px + 10, G - py)
            if any(hit(s, pbox) for s in jaeger_strips(frame, yx, G, flip)):
                k = KY["KnockbackStrength"]
                pvx = k * (1 if px >= yx else -1)
                pvy = k * 7 / 9
                py = 0.01
                immune = 40
                pops.append([px, G - 80, 0, "100"])
        puffs = [[x, a + 1] for x, a in puffs if a < 24]
        pops = [[x, y - 0.6, a + 1, s] for x, y, a, s in pops if a < 60]
        if shake > 0:
            shake -= 1
        if tick % TPF:
            continue
        img = bg.copy()
        dd = ImageDraw.Draw(img)
        for x, a in puffs:
            r = 6 + a
            for off in (-50, 50):
                dd.ellipse([x + off - r, G - r // 2 - 4, x + off + r, G + r // 2 - 4], outline=(195, 200, 205, 255), width=2)
        draw_jaeger(img, frame, round(yx), G, flip, W)
        draw_player(img, px, G - py, flip=px > yx)
        for x, y, a, s in pops:
            pop(gif, img, (x - 16, y), s)
        if shake:
            img = img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, -2 if shake % 2 else 2), resample=Image.NEAREST)
        slips = [max(v) - min(v) for v in planted_world.values() if len(v) > 1]
        gif.text(img, (12, 8), "Jaeger: walks %.2f px/tick (%d px a frame change, %d ticks a frame); turns after %d ticks when you get %d px behind" % (step / tpf, step, tpf, KY["TurnTicks"], KY["TurnHysteresis"]))
        gif.text(img, (12, 28), "contact %d in Expert, knockback %.0f (vanilla 4.5); planted-foot slip: %d px" % (KY["ContactDamage"], KY["KnockbackStrength"], max(slips) if slips else 0))
        gif.push(img)
    slips = [max(v) - min(v) for v in planted_world.values() if len(v) > 1]
    print("jaeger: planted-foot slip over %d stances: max %s px" % (len(slips), max(slips) if slips else "n/a"))
    gif.save(out)


def scene_progress(out, font):
    W, H = 720, 400
    gif = Gif(font)
    icon = Image.open(D + "MechArmyIcon.png").convert("RGBA")
    size = KI["BaseSize"] + KI["SizePerPlayer"] * 1
    msgs = []
    kills = 0
    alpha = 0.0
    display = 0
    jaeger_seen = False
    for tick in range(0, 10 * 60):
        if tick == 10:
            msgs.append("The Mech Army is approaching from the west!")
        if tick == 120:
            msgs.append("The Mech Army has arrived!")
        if 150 <= tick and kills < size and tick % 4 == 0:
            kills += 1 if kills < size * 0.5 or jaeger_seen else 1
            display = 160
            if kills >= size * KI["JaegerFrom"] and not jaeger_seen:
                jaeger_seen = True
                msgs.append("(50%: the Jaeger can now spawn, 1 in 30, one at a time)")
            if jaeger_seen and kills >= size * 0.75 and "(Jaeger down: 10 kills)" not in msgs:
                kills = min(size, kills + KI["JaegerKillValue"])
                msgs.append("(Jaeger down: 10 kills)")
        if kills >= size and "The Mech Army has been defeated!" not in msgs:
            msgs.append("The Mech Army has been defeated!")
        if display > 0:
            display -= 1
        alpha = max(0.0, min(1.0, alpha + (0.05 if display > 0 else -0.05)))
        if tick % TPF:
            continue
        img = Image.new("RGBA", (W, H), (36, 44, 60, 255))
        dd = ImageDraw.Draw(img)
        for k, m in enumerate(msgs[-6:]):
            col = (175, 75, 255) if not m.startswith("(") else (195, 200, 205)
            gif.text(img, (14, H - 150 + k * 20), m, fill=col)
        if alpha > 0:
            sc = 0.5 + alpha * 0.5
            bw, bh = int(200 * sc), int(45 * sc)
            cx, cy = W - 120, H - 40
            box = Image.new("RGBA", (bw, bh), (63, 65, 151, int(255 * 0.785 * alpha)))
            paste(img, box, cx - bw / 2, cy - bh / 2)
            pct = int((kills / size) * 100)
            fill = kills / size
            barw, barh = 169 * sc, 8 * sc
            dd.rectangle([cx - barw / 2, cy + 2, cx + barw / 2, cy + 2 + barh], fill=(0, 0, 0, int(255 * alpha)))
            dd.rectangle([cx - barw / 2, cy + 2, cx - barw / 2 + barw * fill, cy + 2 + barh], fill=(255, 241, 51, int(255 * alpha)))
            gif.text(img, (cx - 40, cy - 16), "Cleared %d%%" % pct)
            nb = Image.new("RGBA", (int(190 * sc), int(34 * sc)), (71 // 2, 145 // 2, 126 // 2, int(200 * alpha)))
            paste(img, nb, cx - 95 * sc - 10, cy - 60)
            paste(img, icon, cx - 95 * sc - 4, cy - 60 + (34 * sc - 32) / 2)
            gif.text(img, (int(cx - 95 * sc + 34), int(cy - 56)), "Mech Army")
        gif.text(img, (14, 10), "Mech Army invasion: vanilla's rules (size %d + %d per player with 5 Life Crystals: %d for one player)" % (KI["BaseSize"], KI["SizePerPlayer"], size))
        gif.text(img, (14, 30), "Progress bar: vanilla's layout and fade (mocked here), the Jaeger's icon in a cog")
        gif.push(img)
    gif.save(out)


def sprites_png(out, font):
    """Every frame of every enemy, planes composited, over a dark and a light background, at 2x game px."""
    rows = [("mice", R["MiceFrames"]), ("boombot", R["BoombotFrames"]), ("annoy", R["AnnoyFrames"]), ("alarmobo", R["AnnoyFrames"])]
    cw, ch = 64, 80
    jaeger_frames = list(range(0, R["JaegerWalkFrames"], 4)) + [R["JaegerIdle"]]
    W = max(cw * max(n for _, n in rows), 160 * len(jaeger_frames))
    YH = 320
    H = ch * len(rows) + YH
    out_img = Image.new("RGBA", (W * 2, H), (0, 0, 0, 255))
    for half, bg in enumerate(((30, 30, 36), (150, 190, 230))):
        img = Image.new("RGBA", (W, H), bg + (255,))
        for r, (kind, n) in enumerate(rows):
            for k in range(n):
                draw_walker(img, kind, k, k * cw + cw // 2, r * ch + ch - 8, False, 1 << 30, beacon_frame=k % R["BeaconFrames"])
        for k, f in enumerate(jaeger_frames):
            draw_jaeger(img, f, 80 + k * 160, H - 6, False, 1 << 30)
        out_img.paste(img, (half * W, 0))
    out_img.save(out)
    print(out, out_img.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-10-28")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    p = lambda name: os.path.join(args.out, args.date + "_event-mech-army-" + name)   # noqa: E731
    jobs = [("roster", lambda: scene_roster(p("roster.gif"), args.font)),
            ("alarm", lambda: scene_alarm(p("alarm.gif"), args.font)),
            ("boombot", lambda: scene_boombot(p("boombot.gif"), args.font)),
            ("jaeger", lambda: scene_jaeger(p("jaeger.gif"), args.font)),
            ("progress", lambda: scene_progress(p("progress.gif"), args.font)),
            ("sprites", lambda: sprites_png(p("sprites.png"), args.font)),
            ("alarmhead", lambda: scene_alarmhead(p("alarmhead.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
