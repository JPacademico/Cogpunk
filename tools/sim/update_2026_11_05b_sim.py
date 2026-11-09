"""D5 proofs for the second request of 2026-11-05: the Cursed Conductor's turbine (its vanes and smoke) and his lantern in
the near hand, the Cog-launcher redrawn as a brass piston gun firing spinning Rusted Cogs, the Metal Wrench's slam, and
the smaller magnum, built from the real sprite sheets, the generated rig data and the constants parsed out of the C#
files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_05b_sim.py --out docs/media [--only turbine,launcher,wrench,items,arcs]

Writes:
    2026-11-05_boss-cursed-conductor-turbine.gif  2x zoom: he hovers on his turbine, the vanes spinning past its window
                                                  (a frame every 2 ticks), soot pumped out of the bell (a puff every 3
                                                  ticks); the lantern swung up over his near shoulder and forward across
                                                  his chest, the bolts flying from it; facing right (all of it mirrored);
                                                  furious (the vanes twice as fast, a puff every 2 ticks); dying (the vanes
                                                  slowing, the smoke sputtering, the exhaust and the lantern going out).
    2026-11-05_weapon-cog-launcher.gif            the piston gun fires a Rusted Cog every 24 ticks (the ram punched out, back
                                                  with the next cog dropping in, loaded: CogLauncherLayer's frames), the cog
                                                  turning 0.35 rad a tick like the Scrap armor's, straight through two
                                                  enemies, off the walls and back through them for +50%.
    2026-11-05_weapon-metal-wrench.gif            the slam: heaved up and back, a hang, down to the foot line in a sixth of
                                                  the use (the smear trailing it), the strike's dust and sparks, the recoil,
                                                  the rest; three slams on a Rust Collector (+50%: mechanical) and a Living
                                                  Tar, one in the air (it stops at the feet: a whiff), one facing left, a
                                                  riposte (x2.5); then every tick of one slam overlaid.
    2026-11-05_weapons-cog-launcher-magnum.png    the Cog-launcher (inventory) and its three held frames, the Rusted Cog as
                                                  the game turns it; the magnum before and after (26x14 -> 22x12 at 1x) in
                                                  the stand-in player's hand.
    2026-11-05_design-directional-melee-arcs.png  the melee study's proposal (docs/design/melee-mechanics-study.md):
                                                  vanilla's swing arc, then the same arc turned to the cursor (up, ahead,
                                                  down); not in the mod.

Leaves out: lighting (the town is drawn dim), vanilla's exact player drawing (the stand-in player is the Scrap armor, its
front arm drawn as a line along the composite arm's rotation), tile collision beyond a flat floor and walls, enemy AI,
defense, crits, netcode. Numbers are Expert's.
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
from trashtr0m_loot_sim import Gif, consts, load, player_sprite, collector_sprite, TPF  # noqa: E402
from update_2026_11_03_sim import Planes, numbers  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps  # noqa: E402
from update_2026_11_04_sim import town_backdrop, KD, EMBER, BRASS, STEAM  # noqa: E402
from update_2026_11_04b_sim import Conductor, KC, faded  # noqa: E402

BOSS = "Content/Bosses/CursedConductor/"
TOWN = "Content/OldBrassTown/"
MECH = "Content/Mechanist/Weapons/"
JUNK = "Content/Junkyard/Weapons/"
KL = consts(MECH + "CogLauncher.cs", MECH + "CogLauncherCog.cs", MECH + "CogLauncherLayer.cs")
KW = consts(JUNK + "MetalWrench.cs", JUNK + "MetalWrenchSmearLayer.cs")
KF = consts(BOSS + "Projectiles/ConductorFlame.cs")
_hold = re.search(r"Holdout = new\(([-\d.]+)f, ([-\d.]+)f\)", open(MECH + "CogLauncher.cs", encoding="utf-8").read())
HOLDOUT = (float(_hold.group(1)), float(_hold.group(2)))
_op = re.search(r"Opacity = \{([^}]*)\}", open(JUNK + "MetalWrenchSmearLayer.cs", encoding="utf-8").read())
SMEAR = [float(v.strip().rstrip("f")) for v in _op.group(1).split(",")]
AETHER = (198, 189, 255)
GHOST = (140, 201, 176)


def pad_rotate(sprite, origin, angle):
    """The sprite turned by `angle` (radians, clockwise on screen) about `origin` (sprite px), nearest-neighbour like the
    GPU's point sampling; returns the turned image and where `origin` now is inside it."""
    w, h = sprite.size
    R = int(math.ceil(math.hypot(max(origin[0], w - origin[0]), max(origin[1], h - origin[1])))) + 2
    pad = Image.new("RGBA", (2 * R, 2 * R))
    pad.alpha_composite(sprite, (int(R - origin[0]), int(R - origin[1])))
    return pad.rotate(-math.degrees(angle), resample=Image.NEAREST), (R, R)


def paste_at(img, sprite, origin, angle, at, alpha=1.0):
    turned, (ox, oy) = pad_rotate(sprite, origin, angle)
    if alpha < 1.0:
        turned = faded(turned, alpha)
    img.alpha_composite(turned, (int(round(at[0] - ox)), int(round(at[1] - oy))))


# ================================================================================================
# The Conductor's turbine
# ================================================================================================
def scene_turbine(out, font):
    W, H, G = 460, 300, 290
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=2.0)
    boss = Conductor()
    boss.x, boss.y = W * 0.5, 150.0
    flame = load(BOSS + "Projectiles/ConductorFlame.png")
    fc = KC["FlameCell"]
    bolts = []
    plan = [("idle", 96, -1, "the turbine: vanes a frame / %d ticks, soot from the bell" % KC["RotorTicks"]),
            ("throw", 54, -1, "the lantern: up, then forward across his chest"),
            ("idle", 66, 1, "facing right: all of it mirrors with him"),
            ("fury", 84, 1, "furious: vanes 2x, a puff every %d ticks" % KC["FurySmokeInterval"]),
            ("dying", 120, 1, "dying: vanes slow, smoke sputters, lights out")]
    tick = 0
    for mode, length, face, label in plan:
        boss.face = face
        boss.furious = mode == "fury"
        for t in range(length):
            if mode == "throw":
                k = t
                frame = KC["Throw"] + (0 if k < 12 else 1 if k < KC["ThrowWindup"] else 2 if k < KC["ThrowWindup"] + KC["ThrowRelease"] else 3)
                if k == KC["ThrowWindup"]:
                    sx, sy = boss.point("Throw")
                    for j in range(KC["Bolts"]):
                        a = math.pi + (j - (KC["Bolts"] - 1) / 2) * KC["BoltSpread"] + 0.25
                        bolts.append([sx, sy, math.cos(a) * KC["BoltSpeed"], math.sin(a) * KC["BoltSpeed"], 0])
            elif mode == "dying":
                frame = KC["Dying"] + min(KC["DyingFrames"] - 1, t // 30)
            else:
                frame = KC["Idle"] + (tick // KC["IdleFrameTicks"]) % KC["IdleFrames"]
            for b in bolts:
                b[0] += b[2]
                b[1] += b[3]
                b[4] += 1
            bolts = [b for b in bolts if 0 < b[0] < W and 0 < b[1] < H and b[4] < 90]
            if tick % TPF == 0:
                img = bg.copy()
                boss.draw(img, frame, 1.0, ticks=TPF)
                for b in bolts:
                    f = (b[4] // KF.get("FrameTicks", 4)) % KC["FlameFrames"]
                    img.alpha_composite(flame.crop((0, f * (fc + 2), fc, f * (fc + 2) + fc)), (int(b[0] - fc / 2), int(b[1] - fc / 2)))
                gif.text(img, (6, 4), label)
                gif.text(img, (6, 20), "frame %d | vanes %d/%d | puffs %d" % (frame, boss.rotor_frame(frame), KC["RotorFrames"], len(boss.puffs)),
                         fill=GHOST)
                gif.push(img)
            tick += 1
    gif.save(out)


# ================================================================================================
# The Cog-launcher
# ================================================================================================
def held_frames():
    sheet = load(MECH + "CogLauncher_Held.png")
    fw, fh, st = KL["FrameWidth"], KL["FrameHeight"], KL["Stride"]
    return [sheet.crop((0, k * st, fw, k * st + fh)) for k in range(3)]


def launcher_frame(use_tick, use_max):
    done = use_tick / use_max
    return KL["FiredFrame"] if done < KL["FiredUntil"] else KL["ReturnFrame"] if done < KL["ReturnUntil"] else KL["LoadedFrame"]


def draw_gun(img, gun, hand, angle):
    """Vanilla's gun hold (DrawPlayer_27_HeldItem, useStyle 5): the sprite's point (-HoldoutOffset.X, H/2) on the hand,
    HoldoutOffset.Y lower, turned by the aim (facing right)."""
    paste_at(img, gun, (-HOLDOUT[0], gun.height / 2), angle, (hand[0], hand[1] + HOLDOUT[1]))


def scene_launcher(out, font):
    W, H, G = 860, 300, 262
    LEFT, RIGHT, TOP = 40, 820, 60
    bg = town_backdrop(W, H, G, wall_x=RIGHT, wall_right=True)
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, LEFT, G], fill=(70, 54, 40, 255))
    d.rectangle([0, 0, W, TOP], fill=(70, 54, 40, 255))
    gif = Gif(font, (W, H), scale=1.0)
    bandit = Planes(TOWN + "NPCs/BrassBandit", KD)
    held = held_frames()
    cog = load("Content/Scrap/Items/RustedCog.png")
    targets = [{"x": x, "flash": 0} for x in (430, 540)]
    p = Player(110, G)
    hand = (p.x + 6, G - 30)
    steam = 100
    cogs, pops, notes, puffs = [], [], [], []
    fire_at = {10: (RIGHT, G - 34), 34: (RIGHT, G - 60), 58: (RIGHT, G - 140), 150: (600, TOP), 174: (RIGHT, G - 34)}
    use_t, use_max, aim_angle = -1, KL["UseTime"], 0.0
    total = 320
    rng = random.Random(3)
    for tick in range(total):
        if tick in fire_at:
            aim = fire_at[tick]
            aim_angle = math.atan2(aim[1] - hand[1], aim[0] - hand[0])
            mx, my = hand[0] + math.cos(aim_angle) * KL["MuzzleDistance"], hand[1] + math.sin(aim_angle) * KL["MuzzleDistance"]
            cogs.append({"x": mx, "y": my, "vx": math.cos(aim_angle) * KL["ShotSpeed"], "vy": math.sin(aim_angle) * KL["ShotSpeed"],
                         "bounces": 0, "pen": KL["Pierce"] + 1, "hit": {}, "rot": 0.0, "t": 0, "alive": True})
            for _ in range(4):                                     # CogLauncherCog.PistonPuff: steam blown back out of the cup
                a = aim_angle + math.pi + rng.uniform(-0.6, 0.6)
                s = rng.uniform(0.8, 2.0)
                puffs.append([mx, my, math.cos(a) * s, math.sin(a) * s - 0.4, 0])
            steam -= KL["Cost"]
            use_t = 0
            if tick == 10:
                notes.append((tick, "the piston punches the clocked Rusted Cog out of the cup (%d steam); the next drops in as the ram returns" % KL["Cost"]))
            if tick == 58:
                notes.append((tick, "the cog spins like the Scrap armor's (%.2f rad a tick) but flies straight: no drop" % KL["SpinSpeed"]))
            if tick == 150:
                notes.append((tick, "it passes through %d enemies and rebounds off %d walls; the next wall breaks it" % (KL["Pierce"], KL["MaxBounces"])))
        if use_t >= 0:
            use_t += 1
            if use_t >= use_max:
                use_t = -1
        for pf in puffs:
            pf[0] += pf[2]
            pf[1] += pf[3]
            pf[2] *= 0.92
            pf[3] *= 0.92
            pf[4] += 1
        puffs = [pf for pf in puffs if pf[4] < 24]
        for c in cogs:
            if not c["alive"]:
                continue
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            c["t"] += 1
            c["rot"] += KL["SpinSpeed"] * (1 if c["vx"] >= 0 else -1)
            wall = c["x"] >= RIGHT - 9 or c["x"] <= LEFT + 9
            ceil_floor = c["y"] <= TOP + 9 or c["y"] >= G - 9
            if wall or ceil_floor:
                if c["bounces"] >= KL["MaxBounces"] or c["t"] >= KL["Lifetime"]:
                    c["alive"] = False
                    notes.append((tick, "its fourth wall: the cog breaks, rust flaking off"))
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
        if tick % TPF:
            continue
        img = bg.copy()
        for t in targets:
            bandit.draw(img, KD["Walk"], (t["x"], G), False)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        k = launcher_frame(use_t, use_max) if use_t >= 0 else KL["LoadedFrame"]
        draw_gun(img, held[k], hand, aim_angle if use_t >= 0 else 0.0)
        dd = ImageDraw.Draw(img)
        for pf in puffs:
            r = 2 + pf[4] // 6
            dd.ellipse([pf[0] - r, pf[1] - r, pf[0] + r, pf[1] + r], fill=(206, 214, 222, 255))
        for c in cogs:
            if c["alive"]:
                paste_at(img, cog, (cog.width / 2, cog.height / 2), c["rot"], (c["x"], c["y"]))
        gif.text(img, (10, 8), "Cog-launcher (Mechanist), a brass piston gun: %d damage, %d use time, 5%% crit, %d steam a shot; pierces %d, "
                 "rebounds off %d walls, +%d%% on a repeat hit" % (KL["Damage"], KL["UseTime"], KL["Cost"], KL["Pierce"], KL["MaxBounces"],
                                                                    round((KL["RepeatBonus"] - 1) * 100)))
        frame_name = ("fired: the ram punched out", "the ram returns, the next cog drops in", "loaded")[k] if use_t >= 0 else "holstered"
        gif.text(img, (10, 26), "steam %d   |   the gun: %s" % (steam, frame_name), fill=STEAM)
        numbers(gif, img, pops, tick)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 70]
        if live:
            gif.text(img, (10, TOP + 6), live[-1], fill=BRASS)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Metal Wrench's slam (MetalWrench.cs and Core/Combat/SwingPose.cs, step for step)
# ================================================================================================
def clamp(v, a, b):
    return max(a, min(b, v))


def phase(t, a, b):
    return 1.0 if b <= a and t >= b else (0.0 if b <= a else clamp((t - a) / (b - a), 0.0, 1.0))


def ground_angle(scale=1.0, drop=23.0):
    reach = 10.0 + KW["HeadEnd"] * scale
    below = 3.0 + KW["HeadRadius"] * scale
    r = math.hypot(reach, below)
    return clamp(math.asin(clamp(drop / r, -1.0, 1.0)) - math.atan2(below, reach), KW["RestMin"], KW["RestMax"])


def slam_angle(done, ground):
    if done < KW["LiftEnd"]:
        u = phase(done, 0.0, KW["LiftEnd"])
        return ground + (KW["RaisedAngle"] - ground) * (1 - (1 - u) ** 3)
    if done < KW["HangEnd"]:
        return KW["RaisedAngle"] - KW["HangDrift"] * phase(done, KW["LiftEnd"], KW["HangEnd"])
    if done < KW["ImpactAt"]:
        u = phase(done, KW["HangEnd"], KW["ImpactAt"])
        a = KW["RaisedAngle"] - KW["HangDrift"]
        return a + (ground - a) * u ** 3
    if done < KW["BounceEnd"]:
        return ground - KW["BounceLift"] * math.sin(math.pi * phase(done, KW["ImpactAt"], KW["BounceEnd"]))
    return ground


def rot(v, a):
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def world_angle(direction, facing):
    return facing if direction == 1 else math.pi - facing


def hand_of(centre, direction, facing):
    """Player.GetFrontHandPosition(Full, facing - pi/2 mirrored), decompiled."""
    w = world_angle(direction, facing)
    v = (math.cos(w) * 10.0, math.sin(w) * 10.0)
    if direction == -1:
        o = rot((0.0, -3.0), w)
        v = (v[0] + 4.0 + o[0], v[1] - 2.0 + o[1])
    else:
        o = rot((0.0, 3.0), w)
        v = (v[0] - 4.0 + o[0], v[1] - 2.0 + o[1])
    return (centre[0] + v[0], centre[1] + v[1])


def blade_point(direction, hand, facing, along, below):
    w = world_angle(direction, facing)
    d = (math.cos(w), math.sin(w))
    n = (-d[1], d[0])
    if direction == -1:
        n = (-n[0], -n[1])
    return (hand[0] + d[0] * along + n[0] * below, hand[1] + d[1] * along + n[1] * below)


def capsule_hits(a, b, r, box):
    """Sampled along the segment (step < r): enough for the proof (the game's SwingPose.CapsuleHitsRect is exact)."""
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / max(1.0, r * 0.5)) + 1)
    for k in range(n + 1):
        t = k / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        dx = max(box[0] - x, 0.0, x - box[2])
        dy = max(box[1] - y, 0.0, y - box[3])
        if dx * dx + dy * dy <= r * r:
            return True
    return False


def blade_hits(direction, centre, facing, box):
    hand = hand_of(centre, direction, facing)
    return (capsule_hits(blade_point(direction, hand, facing, KW["HeadStart"], 0), blade_point(direction, hand, facing, KW["HeadEnd"], 0),
                         KW["HeadRadius"], box)
            or capsule_hits(blade_point(direction, hand, facing, KW["ShaftStart"], KW["ShaftBelow"]),
                            blade_point(direction, hand, facing, KW["HeadStart"], KW["ShaftBelow"]), KW["ShaftRadius"], box))


def draw_wrench(img, wrench, direction, centre, facing, alpha=1.0):
    """Vanilla's held swing (origin at the handle corner: bottom-left, or bottom-right flipped facing left), turned by
    itemRotation, and the composite front arm as a line from the shoulder to the hand."""
    hand = hand_of(centre, direction, facing)
    r = facing + math.pi / 4 if direction == 1 else -(facing + math.pi / 4)
    spr = wrench if direction == 1 else wrench.transpose(Image.FLIP_LEFT_RIGHT)
    origin = (0, spr.height) if direction == 1 else (spr.width, spr.height)
    paste_at(img, spr, origin, r, hand, alpha)
    if alpha >= 1.0:
        sh = (centre[0] - 4 * direction, centre[1] - 2)
        d = ImageDraw.Draw(img)
        d.line([sh, hand], fill=(94, 40, 23, 255), width=5)
        d.line([sh, hand], fill=(147, 68, 31, 255), width=3)
    return hand


def scene_wrench(out, font):
    W, H, G = 760, 300, 250
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.25)
    wrench = load(JUNK + "MetalWrench.png")
    tar = load("Content/Junkyard/NPCs/LivingTar.png").crop((0, 0, 32, 24))
    mech = collector_sprite()
    use = KW["UseTime"]
    ground = ground_angle()
    p = Player(300, G)
    foes = [{"spr": mech, "x": 372.0, "name": "mech", "mech": True}, {"spr": tar, "x": 398.0, "name": "tar", "mech": False},
            {"spr": tar, "x": 208.0, "name": "tar2", "mech": False}]
    plan = [("slam", 1, False, False, "Left click: the slam: heaved up and back, a hang, then down to the foot line in a sixth of the use"),
            ("slam", 1, False, False, "it strikes the ground: the ground's dust and sparks, a thud, a small punch of the camera"),
            ("slam", 1, False, False, "same %d-tick use time: only the animation is faster (it hits while it comes down and recoils)" % use),
            ("jump", 1, False, False, "in the air it stops at the feet too (the foot line): a whiff, no dust"),
            ("wait", 1, False, False, "(landing)"),
            ("slam", -1, False, False, "facing left: the same slam mirrored"),
            ("slam", 1, True, False, "a riposte (after a parry): the slam deals x%.1f" % KW["RiposteMultiplier"]),
            ("onion", 1, False, True, "one slam, every tick of it: the lift, the hang, the fast drop (the smear), the strike, the recoil")]
    pops, dust = [], []
    shake = 0
    tick = 0
    rng = random.Random(9)
    for mode, direction, riposte, onion, label in plan:
        anim = use
        hit_done = set()
        jumped = False
        length = {"onion": 110, "wait": 36}.get(mode, use)
        for t in range(length):
            if mode == "jump" and not jumped:
                p.jump()
                jumped = True
            p.step()
            centre = (p.x, p.y - 21)
            if mode not in ("onion", "wait"):
                anim_now = anim
                done = 1.0 - anim_now / use
                prev = 1.0 - (anim_now + 1) / use
                facing = slam_angle(done, ground)
                if prev < KW["ImpactAt"] <= done:
                    jaw = blade_point(direction, hand_of(centre, direction, facing), facing, KW["HeadEnd"] * 0.85, KW["HeadRadius"] * 0.6)
                    if p.y >= G and jaw[1] >= G - 12:
                        for _ in range(12):
                            dust.append([jaw[0] + rng.uniform(-8, 8), G - 2, rng.uniform(-2.5, 2.5), -rng.uniform(1.5, 4.0), 0,
                                         (147, 110, 70) if rng.random() < 0.7 else (183, 191, 202)])
                        pops.append((tick, jaw[0] - 26, G - 96, "THUD", (223, 185, 78)))
                        shake = 6
                    else:
                        pops.append((tick, jaw[0] - 20, p.y - 70, "whiff", (183, 191, 202)))
                if KW["HangEnd"] <= done < KW["BounceEnd"]:
                    for f in foes:
                        if f["name"] in hit_done:
                            continue
                        if (direction == 1) != (f["x"] > p.x):
                            continue
                        box = (f["x"], G - f["spr"].height, f["x"] + f["spr"].width, G)
                        before = slam_angle(prev, ground)
                        if any(blade_hits(direction, centre, a, box) for a in (facing, (facing + before) / 2, before)):
                            hit_done.add(f["name"])
                            dmg = KW["Damage"] * (1 + KW["MechanicalBonus"] / 100 if f["mech"] else 1) * (KW["RiposteMultiplier"] if riposte else 1)
                            pops.append((tick, f["x"], G - f["spr"].height - 24, str(int(dmg)), AETHER if riposte else EMBER))
                anim -= 1
            for dp in dust:
                dp[0] += dp[2]
                dp[1] += dp[3]
                dp[3] += 0.25
                dp[4] += 1
            dust = [dp for dp in dust if dp[4] < 30 and dp[1] <= G]
            if tick % TPF == 0:
                img = bg.copy()
                for f in foes:
                    img.alpha_composite(f["spr"], (int(f["x"]), int(G - f["spr"].height)))
                img.alpha_composite(player_sprite(flip=direction == -1), (int(p.x - 20), int(p.y - 56)))
                if mode == "onion":
                    for k in range(use):
                        d_ = 1.0 - (use - k) / use
                        a = slam_angle(d_, ground)
                        fast = KW["HangEnd"] <= d_ < KW["ImpactAt"] + 1.0 / use
                        draw_wrench(img, wrench, 1, centre, a, 0.75 if fast else 0.28)
                    draw_wrench(img, wrench, 1, centre, ground)          # where it comes to rest, solid
                    dd = ImageDraw.Draw(img)
                    dd.line([0, G, W, G], fill=(223, 185, 78, 255), width=1)
                    gif.text(img, (int(p.x + 90), G - 16), "the foot line: it never goes below", fill=(223, 185, 78))
                elif mode != "wait":
                    if KW["HangEnd"] <= 1.0 - (anim + 1) / use < KW["ImpactAt"] + 1.0 / use:
                        for k, op in enumerate(SMEAR):          # MetalWrenchSmearLayer: the ticks before, fainter each
                            d_ = 1.0 - (anim + 1 + k + 1) / use
                            if d_ < KW["HangEnd"]:
                                break
                            draw_wrench(img, wrench, direction, centre, slam_angle(d_, ground), op)
                    draw_wrench(img, wrench, direction, centre, slam_angle(1.0 - (anim + 1) / use, ground))
                    if riposte:
                        hand = hand_of(centre, direction, slam_angle(1.0 - (anim + 1) / use, ground))
                        ImageDraw.Draw(img).ellipse([hand[0] - 3, hand[1] - 3, hand[0] + 3, hand[1] + 3], fill=(246, 231, 161, 255))
                dd = ImageDraw.Draw(img)
                for dp in dust:
                    dd.rectangle([dp[0], dp[1], dp[0] + 2, dp[1] + 2], fill=dp[5] + (255,))
                numbers(gif, img, pops, tick)
                gif.text(img, (10, 8), label)
                done_now = 1.0 - (anim + 1) / use if mode not in ("onion", "wait") else 1.0
                ph = ("lift" if done_now < KW["LiftEnd"] else "hang" if done_now < KW["HangEnd"] else "SLAM" if done_now < KW["ImpactAt"]
                      else "recoil" if done_now < KW["BounceEnd"] else "rest")
                gif.text(img, (10, 26), "Metal Wrench: %d damage, %d use time; +%d%% on mechanical enemies   |   %s" % (
                    KW["Damage"], use, KW["MechanicalBonus"], ph if mode != "onion" else "every tick overlaid"), fill=STEAM)
                if shake > 0:
                    shake -= 1
                    img = img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, -2 if shake % 2 else 0))
                gif.push(img)
            tick += 1
    gif.save(out)


# ================================================================================================
# The items: the Cog-launcher and the magnum before and after
# ================================================================================================
def old_magnum():
    """The 26x14 magnum of 2026-11-05 (art/oldbrasstown/previous/make_revolver_art_2026-11-05.py), drawn at 2x."""
    sys.path.insert(0, os.path.join(os.getcwd(), "art", "bosses", "trashtr0m"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("old_magnum", os.path.join("art", "oldbrasstown", "previous", "make_revolver_art_2026-11-05.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    im = mod.revolver()
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def items_png(out, font):
    gif = Gif(font, (10, 10))
    W, H = 980, 420
    img = Image.new("RGBA", (W, H), (36, 40, 48, 255))
    ImageDraw.Draw(img).rectangle([W // 2, 0, W, H], fill=(150, 180, 210, 255))
    launcher = load(MECH + "CogLauncher.png")
    held = held_frames()
    cog = load("Content/Scrap/Items/RustedCog.png")
    for half in (0, 1):
        x0 = half * W // 2 + 14
        gif.text(img, (x0, 8), "Cog-launcher (2x the game's pixels): the item, then its held frames" if half == 0 else "on a light background")
        img.alpha_composite(launcher.resize((launcher.width * 2, launcher.height * 2), Image.NEAREST), (x0, 30))
        for k, name in enumerate(("fired", "return", "loaded")):
            fx = x0 + k * 150
            img.alpha_composite(held[k].resize((held[k].width * 2, held[k].height * 2), Image.NEAREST), (fx, 110))
            gif.text(img, (fx, 178), name)
        gif.text(img, (x0, 206), "the Rusted Cog it fires, as the game turns it")
        for k in range(4):
            turned, _ = pad_rotate(cog, (cog.width / 2, cog.height / 2), 0.35 * k)
            img.alpha_composite(turned.resize((turned.width * 2, turned.height * 2), Image.NEAREST), (x0 + k * 90, 222))
    # the magnum before and after, in the stand-in player's hand
    new = load(TOWN + "Weapons/SheriffsRevolver.png")
    try:
        old = old_magnum()
    except Exception as e:                                      # the previous generator should always run; say so if not
        print("old magnum not rendered:", e)
        old = None
    y = 300
    gif.text(img, (14, y - 18), "the magnum in the hand: before (52x28) and after (44x24, user: 'decrease a bit the size')")
    for k, (gun, name) in enumerate(((old, "before"), (new, "after"))):
        if gun is None:
            continue
        px = 60 + k * 200
        img.alpha_composite(player_sprite(), (px - 20, y + 4))
        img.alpha_composite(gun, (px + 4, y + 30 - round(gun.height * 0.57)))
        gif.text(img, (px - 20, y + 66), "%s: %dx%d" % (name, gun.width, gun.height))
    img.convert("RGB").save(out)
    print(out, img.size)


# ================================================================================================
# The directional melee study's diagram (docs/design/melee-mechanics-study.md): vanilla's swing arc and the same arc
# turned to the cursor
# ================================================================================================
def vanilla_blade(anim, amax):
    """Vanilla's style-1 swing (decompiled Player.ItemCheck_ApplyUseStyle_Inner) as a facing-frame blade angle: the item
    rotation ((anim/max - 0.5) * -3.5 - 0.3, facing right) less the sprite's own 45 degrees."""
    return ((anim / amax) - 0.5) * -3.5 - 0.3 - math.pi / 4


def arcs_png(out, font):
    gif = Gif(font, (10, 10))
    W, H = 1020, 360
    img = Image.new("RGBA", (W, H), (36, 40, 48, 255))
    sword = load(JUNK + "MetalWrench.png")
    G = 290
    d = ImageDraw.Draw(img)
    d.rectangle([0, G, W, H], fill=(120, 92, 60, 255))
    cases = [("vanilla: the arc the way he faces", 0.0, (255, 199, 90)),
             ("aimed up (the cursor 60 deg above)", -1.05, (198, 189, 255)),
             ("aimed ahead", 0.0, (198, 189, 255)),
             ("aimed down (60 deg below)", 1.05, (198, 189, 255))]
    amax = 24
    for k, (name, offset, col) in enumerate(cases):
        cx = 130 + k * 250
        centre = (cx, G - 21)
        img.alpha_composite(player_sprite(), (int(cx - 20), int(G - 56)))
        for anim in range(amax, 0, -2):
            a = vanilla_blade(anim, amax) + offset
            draw_wrench(img, sword, 1, centre, a, 0.22 if anim != 2 else 0.9)
        if k > 0:
            aim = offset - 0.3                                   # where vanilla's front half points, turned
            d.line([centre, (centre[0] + math.cos(offset) * 110, centre[1] + math.sin(offset) * 110)], fill=col + (255,), width=1)
        gif.text(img, (cx - 110, 16), name, fill=col)
    gif.text(img, (10, H - 26), "proposal only (not in the mod): the same 24-tick arc turned by the cursor's angle, clamped +-75 deg; "
             "faded = every 2nd tick, solid = the end", fill=(238, 241, 243))
    img.convert("RGB").save(out)
    print(out, img.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a.add_argument("--date", default="2026-11-06", help="date prefix of the Cursed Conductor's proofs (his torso turned to the screen 2026-11-06)")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("turbine", lambda: scene_turbine(os.path.join(args.out, args.date + "_boss-cursed-conductor-turbine.gif"), args.font)),
            ("launcher", lambda: scene_launcher(os.path.join(args.out, "2026-11-05_weapon-cog-launcher.gif"), args.font)),
            ("wrench", lambda: scene_wrench(os.path.join(args.out, "2026-11-05_weapon-metal-wrench.gif"), args.font)),
            ("items", lambda: items_png(os.path.join(args.out, "2026-11-05_weapons-cog-launcher-magnum.png"), args.font)),
            ("arcs", lambda: arcs_png(os.path.join(args.out, "2026-11-05_design-directional-melee-arcs.png"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
