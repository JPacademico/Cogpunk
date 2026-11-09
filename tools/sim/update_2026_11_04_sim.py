"""D5 proofs for the request of 2026-11-04: the Beat-Boxer's lowered second punch, the Cogtuna (ocean), Old Brass Town's
enemies (the Brass Bandit, the Sheriff and his stars, the Mechanical Bull, the Dinamitrom), the Sheriff Badge's stars and
the new items, built from the real sprite sheets, the generated rig data and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_04_sim.py --out docs/media [--only punch,cogtuna,bandit,sheriff,bull,dinamitrom,badge,items]

Writes:
    2026-11-04_dungeon-beat-boxer-punch.gif   a close-up of one volley: the glove from the near arm, then the microphone
                                             from the far arm, now at chest height (3 px above the first) instead of from
                                             under the head.
    2026-11-04_ocean-cogtuna.gif             the Cogtuna cruising, stalking a swimming player, its telegraph (backing off
                                             and gaping, the throat's furnace lit) and the lunge (90 in Expert); the second
                                             lunge misses a player who swam out of its line.
    2026-11-04_oldbrasstown-bandit.gif        the Brass Bandit: in sight, it draws (30 ticks), fans six shots at the player
                                             as they are then, runs away to reload (2.5 s) and comes back for more.
    (retired) the Sheriff's 2026-11-04 star volley; his stars were reworked on 2026-11-06: tools/sim/update_2026_11_06_sim.py --only sheriff
    2026-11-04_oldbrasstown-bull.gif          the Mechanical Bull: it paws the ground (45 ticks), charges straight, rams the
                                             player (100, knockback x2: thrown about 20 tiles); the next charge is jumped over
                                             and it slams into a wall, stunned.
    2026-11-04_oldbrasstown-dinamitrom.gif    a Dinamitrom hops in, crouches with its fuse flaring (36 ticks), leaps on an arc
                                             to where the player stood and blows up (110, 4 tiles); a second one is shot down
                                             in the air and only pops.
    2026-11-04_oldbrasstown-sheriff-badge.gif three deputy stars over a player, each flying at an enemy on its beat and back.
    2026-11-04_items-eyes.png                 the Shark Eye, the Hawk Eye, the Sheriff Badge, its buff, the stars (hostile and
                                             friendly, spin and telegraph frames), the rusty bullet and the blast frames, at
                                             2x on a dark and a light background.

Leaves out: lighting, tiles beyond a flat floor (and one wall), vanilla's exact player physics (approximated as in
update_2026_11_03b_sim: the hurt launch is decompiled Player.Hurt's, knockback sideways and 7/9 of it up, the hostile
base 4.5 x the attack's multiplier, 40 ticks of immunity), swimming physics (the player drifts), defense, netcode.
Numbers are Expert's.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, consts, load, player_sprite, collector_sprite, TPF  # noqa: E402
from update_2026_11_03_sim import Planes, numbers  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, dungeon_backdrop, extension, PLAYER_W, PLAYER_H, FIST_W, FIST_H, SPRING_CELL, SPRING_H  # noqa: E402
import terrain  # noqa: E402
from smoke import Smoke  # noqa: E402

TOWN = "Content/OldBrassTown/"
KB = consts("Content/Dungeon/NPCs/BeatBoxer.cs", "Content/Dungeon/NPCs/BeatBoxerRigData.cs", "Content/Dungeon/Projectiles/SpringPunch.cs")
KS = consts("Content/Ocean/NPCs/Cogtuna.cs", "Content/Ocean/NPCs/CogtunaRigData.cs")
KD = consts(TOWN + "NPCs/BrassBandit.cs", TOWN + "NPCs/BrassBanditRigData.cs")
KH = consts(TOWN + "NPCs/Sheriff.cs", TOWN + "NPCs/SheriffRigData.cs", TOWN + "Projectiles/SheriffStar.cs")
KU = consts(TOWN + "NPCs/MechanicalBull.cs", TOWN + "NPCs/MechanicalBullRigData.cs")
KM = consts(TOWN + "NPCs/Dinamitrom.cs", TOWN + "NPCs/DinamitromRigData.cs", TOWN + "Projectiles/DinamitromBlast.cs")
KN = consts(TOWN + "Minions/SheriffStarMinion.cs", TOWN + "Minions/SheriffBadge.cs")
EMBER = (255, 199, 90)
HURT = (255, 90, 70)
STEAM = (238, 241, 243)
AETHER = (198, 189, 255)
BRASS = (223, 185, 78)
VANILLA_KB = 4.5
IMMUNITY = 40


def town_backdrop(w, h, ground, wall_x=None, wall_right=False):
    """Old Brass Town: a dim clapboard wall behind, a floor of real Brass Sandstone tiles (and a wall of it, if asked)."""
    img = Image.new("RGBA", (w, h), (46, 36, 30, 255))
    d = ImageDraw.Draw(img)
    for y in range(0, ground, 10):
        d.line([0, y, w, y], fill=(58, 44, 34, 255))
        d.line([0, y + 1, w, y + 1], fill=(38, 30, 26, 255))
    frames = terrain.load_frames("art/templates/terrain_exposure.json")
    sheet = load(TOWN + "Tiles/BrassSandstoneTile.png")
    cols = w // 16 + 2
    rows = (h - ground) // 16 + 2
    grid = ["#" * cols] * rows
    floor = terrain.render(grid, {"#": sheet}, frames, seed=3)
    img.alpha_composite(floor.crop((0, 0, w, h - ground)), (0, ground))
    if wall_x is not None:
        wall = terrain.render(["#####"] * ((ground // 16) + 2), {"#": sheet}, frames, seed=5)
        img.alpha_composite(wall.crop((0, wall.height - ground - 2, wall.width, wall.height)), (wall_x if wall_right else wall_x - wall.width, 0))
    return img


def ocean_backdrop(w, h, surface, floor):
    img = Image.new("RGBA", (w, h), (120, 170, 220, 255))
    d = ImageDraw.Draw(img)
    for y in range(surface, floor):
        t = (y - surface) / max(1, floor - surface)
        col = (int(40 - 20 * t), int(90 - 40 * t), int(150 - 50 * t), 255)
        d.line([0, y, w, y], fill=col)
    d.line([0, surface, w, surface], fill=(160, 200, 235, 255))
    d.rectangle([0, floor, w, h], fill=(196, 168, 108, 255))
    d.line([0, floor, w, floor], fill=(220, 196, 140, 255))
    return img


def heading_frame(vx, vy, n):
    a = math.atan2(vy, vx)
    return int(round((a % (2 * math.pi)) / (2 * math.pi) * n)) % n


def pops_and_notes(gif, img, pops, notes, tick, y=48):
    numbers(gif, img, pops, tick)
    live = [s for (t0, s) in notes if 0 <= tick - t0 < 80]
    if live:
        gif.text(img, (10, y), live[-1], fill=STEAM)


# ================================================================================================
# The Beat-Boxer's two punches, close up
# ================================================================================================
def scene_punch(out, font):
    W, H, G = 300, 130, 112
    bg = dungeon_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=3.0)
    gif.font = gif.font.font_variant(size=7)
    gif.big = gif.big.font_variant(size=9)
    boxer = Planes("Content/Dungeon/NPCs/BeatBoxer", KB)
    glove = load("Content/Dungeon/Projectiles/SpringPunch.png")
    mic = load("Content/Dungeon/Projectiles/SpringPunch_Mic.png")
    coil = load("Content/Dungeon/Projectiles/SpringPunch_Spring.png")
    bx, face, reach = 230.0, -1, 5.0 * 16
    script = ["idle"] * 24 + ["windup"] * KB["WindupTicks"] + ["punch"] * KB["PunchTicks"] + ["idle"] * 30
    script = script * 2
    timer, last = 0, None
    punches = []
    for tick, state in enumerate(script):
        timer = timer + 1 if state == last else 0
        last = state
        if state == "punch" and timer == 0:
            punches.append([0, -1])
        if state == "punch" and timer == KB["SecondPunchDelay"]:
            punches.append([1, -1])
        for pu in punches:
            pu[1] += 1
        punches = [pu for pu in punches if pu[1] < KB["Lifetime"]]
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "windup":
            frame = KB["Windup"] + (0 if timer < KB["WindupTicks"] / 2 else 1)
        elif state == "punch":
            frame = KB["PunchNear"] if timer < KB["SecondPunchDelay"] else KB["PunchFar"]
        else:
            frame = KB["Idle"] + (tick // 16) % 2
        boxer.draw(img, frame, (bx, G), face > 0)
        d = ImageDraw.Draw(img)
        for arm in (0, 1):
            sy = G + (KB["NearShoulderY"] if arm == 0 else KB["FarShoulderY"])
            d.line([4, sy, 18, sy], fill=(EMBER if arm == 0 else BRASS) + (255,), width=1)
        for (arm, age) in sorted(punches, key=lambda p: -p[0]):
            sx = bx + (KB["NearShoulderX"] if arm == 0 else KB["FarShoulderX"]) * -face
            sy = G + (KB["NearShoulderY"] if arm == 0 else KB["FarShoulderY"])
            fx = sx + face * (FIST_W * 0.5 + reach * extension(age))
            length = abs(fx - sx) - FIST_W * 0.5
            cells = int(length // SPRING_CELL)
            for k in range(cells + 1):
                w = SPRING_CELL if k < cells else int(length) - cells * SPRING_CELL
                if w <= 0:
                    continue
                x = sx - k * SPRING_CELL - w
                img.alpha_composite(coil.crop((0, 0, w, SPRING_H)), (int(x), int(sy - SPRING_H * 0.5)))
            img.alpha_composite(mic if arm == 1 else glove, (int(fx - FIST_W * 0.5), int(sy - FIST_H * 0.5)))
        gif.text(img, (22, G + KB["NearShoulderY"] - 5), "1st: the glove (near arm, %d px up)" % -KB["NearShoulderY"], fill=EMBER)
        gif.text(img, (22, G + KB["FarShoulderY"] - 13), "2nd: the mic (far arm, chest height, %d px up)" % -KB["FarShoulderY"], fill=BRASS)
        gif.text(img, (4, 4), "Beat-Boxer: the second punch now leaves from its chest, just above the first")
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Cogtuna
# ================================================================================================
def scene_cogtuna(out, font):
    W, H, SURF, FLOOR = 760, 300, 36, 280
    bg = ocean_backdrop(W, H, SURF, FLOOR)
    gif = Gif(font, (W, H), scale=1.25)
    shark = Planes("Content/Ocean/NPCs/Cogtuna", KS)
    player = player_sprite(flip=False)
    sx, sy, vx, vy = 700.0, 170.0, 0.0, 0.0
    px, py = 200.0, 150.0                                    # the swimmer's centre
    state, timer, cooldown, heading = "cruise", 0, 0, 0.0
    face = -1
    immune = 0
    swum = 0.0
    lunges = 0
    pops, notes = [], []
    total = 8 * 60
    for tick in range(total):
        timer += 1
        if cooldown > 0:
            cooldown -= 1
        if immune > 0:
            immune -= 1
        # the swimmer drifts, then swims up out of the line before the second lunge
        if lunges >= 1 and state in ("stalk", "windup") and py > 90:
            py -= 1.6
        to = (px - sx, py - sy)
        dist = math.hypot(*to)
        if state == "cruise":
            vx += (face * KS["CruiseSpeed"] - vx) * KS["Accel"] * 0.5
            vy += (math.sin(timer * 0.04) * 0.4 - vy) * KS["Accel"] * 0.5
            if dist < KS["DetectRange"] and timer > 30:
                state, timer = "stalk", 0
                notes.append((tick, "a swimmer in the water within %d tiles: it stalks" % (KS["DetectRange"] // 16)))
        elif state == "stalk":
            want = (to[0] / max(1e-6, dist) * KS["StalkSpeed"], to[1] / max(1e-6, dist) * KS["StalkSpeed"])
            vx += (want[0] - vx) * KS["Accel"]
            vy += (want[1] - vy) * KS["Accel"]
            face = 1 if to[0] >= 0 else -1
            if cooldown <= 0 and dist < KS["LungeRange"]:
                state, timer = "windup", 0
                heading = math.atan2(to[1], to[0])
                notes.append((tick, "the telegraph: it backs off and gapes (%d ticks)" % KS["WindupTicks"]))
        elif state == "windup":
            if timer < KS["WindupTicks"] * 2 / 3:
                heading = math.atan2(to[1], to[0])
            hx, hy = math.cos(heading), math.sin(heading)
            vx += (-hx * KS["PullBack"] - vx) * 0.2
            vy += (-hy * KS["PullBack"] - vy) * 0.2
            face = 1 if hx >= 0 else -1
            if timer >= KS["WindupTicks"]:
                state, timer = "lunge", 0
                lunges += 1
        elif state == "lunge":
            vx, vy = math.cos(heading) * KS["LungeSpeed"], math.sin(heading) * KS["LungeSpeed"]
            if timer >= KS["LungeTicks"]:
                state, timer = "recover", 0
        elif state == "recover":
            vx *= 0.95
            vy *= 0.95
            if timer >= KS["RecoverTicks"]:
                state, timer, cooldown = "stalk", 0, KS["LungeCooldown"]
        sx += vx
        sy += vy
        sy = max(SURF + KS["Height"] / 2 + 2, min(FLOOR - KS["Height"] / 2, sy))   # stays under the surface
        swum += max(0.5, math.hypot(vx, vy))
        sbox = (sx - KS["Width"] / 2, sy - KS["Height"] / 2, sx + KS["Width"] / 2, sy + KS["Height"] / 2)
        pbox = (px - PLAYER_W / 2, py - PLAYER_H / 2, px + PLAYER_W / 2, py + PLAYER_H / 2)
        if immune <= 0 and overlaps(sbox, pbox):
            immune = IMMUNITY
            pops.append((tick, px - 12, py - 40, str(KS["ContactDamage"]), HURT))
            notes.append((tick, "the bite: %d (Expert)" % KS["ContactDamage"]))
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "windup":
            frame = KS["Lunge"]
        elif state == "lunge":
            frame = KS["Lunge"] + 1 + (timer // 4) % 2
        elif vy < -KS["TiltSpeed"]:
            frame = KS["Rise"] + int(swum / KS["SwimAnimDistance"]) % KS["RiseFrames"]
        elif vy > KS["TiltSpeed"]:
            frame = KS["Dive"] + int(swum / KS["SwimAnimDistance"]) % KS["DiveFrames"]
        else:
            frame = KS["Swim"] + int(swum / KS["SwimAnimDistance"]) % KS["SwimFrames"]
        if immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player, (int(px - 20), int(py - 28)))
        shark.draw(img, frame, (sx, sy + KS["CenterY"]), face > 0)
        gif.text(img, (10, 8), "Cogtuna (the ocean's water only): %d life, %d defense, %d contact (Expert)" % (KS["Life"], KS["Defense"], KS["ContactDamage"]))
        gif.text(img, (10, 28), "telegraph %d ticks, lunge %d ticks at %g px/tick, then %d ticks of cooldown" % (
            KS["WindupTicks"], KS["LungeTicks"], KS["LungeSpeed"], KS["LungeCooldown"]))
        pops_and_notes(gif, img, pops, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Brass Bandit
# ================================================================================================
def bandit_muzzle(k, x, ground, face, aim):
    keys = (("MuzzleLevelX", "MuzzleLevelY"), ("MuzzleUpX", "MuzzleUpY"), ("MuzzleDownX", "MuzzleDownY"))[aim]
    return x + k[keys[0]] * -face, ground + k[keys[1]]


def aim_index(k, x, ground, face, target):
    mx, my = bandit_muzzle(k, x, ground, face, 0)
    a = math.atan2(target[1] - my, abs(target[0] - mx) + 0.01)
    return 1 if a < -k["LevelBand"] else (2 if a > k["LevelBand"] else 0)


def fire(k, x, ground, face, target, rng_spread=0.0):
    aim = aim_index(k, x, ground, face, target)
    mx, my = bandit_muzzle(k, x, ground, face, aim)
    a = math.atan2(target[1] - my, abs(target[0] - mx) + 0.01)
    a = max(-k["MaxAimAngle"], min(k["MaxAimAngle"], a)) + rng_spread
    speed = k["BulletSpeed"] * 2                             # RustyBullet updates twice a tick
    return [mx, my, face * math.cos(a) * speed, math.sin(a) * speed]


def scene_bandit(out, font):
    W, H, G = 800, 280, 240
    END = W - 40
    bg = town_backdrop(W, H, G, wall_x=END, wall_right=True)
    gif = Gif(font, (W, H), scale=1.25)
    bandit = Planes(TOWN + "NPCs/BrassBandit", KD)
    bullet = load(TOWN + "Projectiles/RustyBullet.png")
    smoke = Smoke((138, 144, 150))
    p = Player(130, G)
    bx, bvx, face = 730.0, 0.0, -1
    state, timer, flee_dir = "walk", 0, 1
    walked = 0.0
    bullets, pops, notes = [], [], []
    volleys = 0
    spreads = (0.0, 0.03, -0.02, 0.04, -0.03, 0.01)
    total = int(9.4 * 60)
    for tick in range(total):
        timer += 1
        target = (p.x, p.y - PLAYER_H / 2)
        dx = p.x - bx
        direction = 1 if dx >= 0 else -1
        if state == "walk":
            want = direction * KD["WalkSpeed"] if abs(dx) > KD["KeepRange"] else 0.0
            bvx = min(want, bvx + KD["WalkAccel"]) if bvx < want else max(want, bvx - KD["WalkAccel"])
            face = direction
            if math.hypot(dx, target[1] - (G - KD["Height"] / 2)) < KD["SightRange"] and timer > 20:
                state, timer = "aim", 0
                volleys += 1
                notes.append((tick, "in sight within %d tiles: it draws and aims (%d ticks)" % (KD["SightRange"] // 16, KD["AimTicks"])))
        elif state == "aim":
            bvx *= 0.7
            face = direction
            if timer >= KD["AimTicks"]:
                state, timer = "shoot", 0
        elif state == "shoot":
            bvx *= 0.7
            face = direction
            if (timer - 1) % KD["ShotInterval"] == 0 and timer <= KD["ShootTicks"]:
                bullets.append(fire(KD, bx, G, face, target, spreads[((timer - 1) // KD["ShotInterval"]) % 6]))
            if timer >= KD["ShootTicks"] + 6:
                state, timer, flee_dir = "flee", 0, -direction
                notes.append((tick, "six shots spent: it runs to reload (%.1f s)" % (KD["ReloadTicks"] / 60)))
        elif state == "flee":
            want = flee_dir * KD["RunSpeed"]
            bvx = min(want, bvx + KD["RunAccel"]) if bvx < want else max(want, bvx - KD["RunAccel"])
            face = flee_dir
            if timer >= KD["ReloadTicks"]:
                state, timer = "walk", 0
        bx += bvx
        if bx > END - KD["Width"] / 2:
            bx = END - KD["Width"] / 2                       # up against the building: it runs in place
        walked += abs(bvx)
        # the player: stands for the first volley, then strafes back and forth to dodge the second
        p.run = 0
        if volleys >= 2 and state in ("aim", "shoot"):
            p.run = 1 if (tick // 40) % 2 == 0 else -1
        p.step()
        p.x = max(30.0, min(W - 30.0, p.x))
        for b in list(bullets):
            smoke.add((b[0], b[1]), (b[0] + b[2], b[1] + b[3]), tick)
            b[0] += b[2]
            b[1] += b[3]
            if not (0 < b[0] < W and 0 < b[1] < G):
                bullets.remove(b)
                continue
            if p.immune <= 0 and overlaps((b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4), p.box()):
                p.immune = IMMUNITY
                pops.append((tick, p.x - 12, p.y - 70, str(KD["BulletDamage"]), HURT))
                bullets.remove(b)
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "aim":
            frame = KD["Aim"] + aim_index(KD, bx, G, face, target)
        elif state == "shoot":
            since = (timer - 1) % KD["ShotInterval"]
            frame = (KD["Shoot"] if since < KD["MuzzleFlashTicks"] and timer <= KD["ShootTicks"] else KD["Aim"]) + aim_index(KD, bx, G, face, target)
        elif state == "flee":
            frame = KD["Reload"] + int(walked / KD["RunStep"]) % KD["ReloadFrames"]
        elif abs(bvx) > 0.15:
            frame = KD["Walk"] + int(walked / KD["WalkStep"]) % KD["WalkFrames"]
        else:
            frame = KD["Walk"]
        if p.immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player_sprite(flip=p.vx < 0), (int(p.x - 20), int(p.y - 56)))
        bandit.draw(img, frame, (bx, G), face > 0)
        smoke.draw(img, tick)
        for b in bullets:
            f = heading_frame(b[2], b[3], KD["BulletHeadings"])
            img.alpha_composite(bullet.crop((0, f * 16, 14, f * 16 + 14)), (int(b[0] - 7), int(b[1] - 7)))
        gif.text(img, (10, 8), "Brass Bandit (Old Brass Town): %d life, %d defense; six rusty bullets of %d (Expert), %d ticks apart" % (
            KD["Life"], KD["Defense"], KD["BulletDamage"], KD["ShotInterval"]))
        if state == "aim":
            gif.text(img, (int(bx) - 60, G - 100), "drawing: %d" % (KD["AimTicks"] - timer), fill=EMBER)
        elif state == "flee":
            gif.text(img, (int(bx) - 40, G - 100), "reloading", fill=STEAM)
        pops_and_notes(gif, img, pops, notes, tick, y=28)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Sheriff and his stars
# ================================================================================================
def star_home(k, x, ground, slot, tick):
    return x + (slot - 1) * 24.0, ground + k["HatTopY"] - 16.0 - (8.0 if slot == 1 else 0.0) - ((tick // 20 + slot) % 2) * 2.0


def scene_sheriff(out, font):
    W, H, G = 800, 300, 262
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.25)
    sheriff = Planes(TOWN + "NPCs/Sheriff", KH)
    star_sheet = load(TOWN + "Projectiles/SheriffStar.png")
    star_glow = load(TOWN + "Projectiles/SheriffStar_Glow.png")
    bullet = load(TOWN + "Projectiles/RustyBullet.png")
    smoke = Smoke((138, 144, 150))
    p = Player(170, G)
    hx, hvx, face = 700.0, 0.0, -1
    state, timer, clock = "walk", 0, 0
    walked = 0.0
    stars = [{"mode": 0, "x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0, "hit": False} for _ in range(3)]
    for s, st in enumerate(stars):
        st["x"], st["y"] = star_home(KH, hx, G, s, 0)
    bullets, pops, notes = [], [], []
    spreads = (0.0, 0.02, -0.02, 0.03, -0.01, 0.01)
    total = int(9.6 * 60)
    for tick in range(total):
        timer += 1
        clock = (clock + 1) % KH["StarCycle"]
        target = (p.x, p.y - PLAYER_H / 2)
        dx = p.x - hx
        direction = 1 if dx >= 0 else -1
        if clock == 1:
            notes.append((tick, "the stars flash: %d ticks, then they fly one by one" % KH["StarTelegraph"]))
        if state == "walk":
            want = direction * KH["WalkSpeed"] if abs(dx) > KH["KeepRange"] else 0.0
            hvx = min(want, hvx + KH["WalkAccel"]) if hvx < want else max(want, hvx - KH["WalkAccel"])
            face = direction
            if timer > 60 and abs(dx) < KH["SightRange"]:
                state, timer = "aim", 0
        elif state == "aim":
            hvx *= 0.7
            face = direction
            if timer >= KH["AimTicks"]:
                state, timer = "shoot", 0
                notes.append((tick, "six shots, %d ticks apart" % KH["ShotInterval"]))
        elif state == "shoot":
            hvx *= 0.7
            face = direction
            if (timer - 1) % KH["ShotInterval"] == 0 and timer <= KH["ShootTicks"]:
                bullets.append(fire(KH, hx, G, face, target, spreads[((timer - 1) // KH["ShotInterval"]) % 6]))
            if timer >= KH["ShootTicks"] + 6:
                state, timer = "reload", 0
                notes.append((tick, "he reloads standing his ground (%d s): the opening" % (KH["ReloadTicks"] // 60)))
        elif state == "reload":
            hvx *= 0.7
            face = direction
            if timer >= KH["ReloadTicks"]:
                state, timer = "walk", 0
        hx += hvx
        walked += abs(hvx)
        # the stars (SheriffStar.AI)
        for s, st in enumerate(stars):
            launch = KH["StarTelegraph"] + s * KH["StarStagger"]
            home = star_home(KH, hx, G, s, tick)
            if clock == launch and st["mode"] == 0:
                ax, ay = target[0] - st["x"], target[1] - st["y"]
                d = math.hypot(ax, ay) or 1.0
                st["vx"], st["vy"], st["mode"], st["hit"] = ax / d * KH["OutSpeed"], ay / d * KH["OutSpeed"], 1, False
            if st["mode"] == 1 and (clock >= launch + KH["OutTicks"] or clock < launch):
                st["mode"] = 2
            if st["mode"] == 2:
                ax, ay = home[0] - st["x"], home[1] - st["y"]
                d = math.hypot(ax, ay)
                if d < KH["HomeSnap"]:
                    st["mode"] = 0
                else:
                    st["vx"], st["vy"] = ax / d * min(KH["ReturnSpeed"], d), ay / d * min(KH["ReturnSpeed"], d)
            if st["mode"] == 0:
                st["x"], st["y"] = home
            else:
                st["x"] += st["vx"]
                st["y"] += st["vy"]
                if p.immune <= 0 and overlaps((st["x"] - 10, st["y"] - 10, st["x"] + 10, st["y"] + 10), p.box()):
                    p.immune = IMMUNITY
                    pops.append((tick, p.x - 12, p.y - 70, str(KH["StarDamage"]), HURT))
        # the player jumps the first star volley, then stands
        p.run = 0
        if clock == KH["StarTelegraph"] - 6 and tick < 200:
            p.jump()
        p.step()
        for b in list(bullets):
            smoke.add((b[0], b[1]), (b[0] + b[2], b[1] + b[3]), tick)
            b[0] += b[2]
            b[1] += b[3]
            if not (0 < b[0] < W and 0 < b[1] < G):
                bullets.remove(b)
                continue
            if p.immune <= 0 and overlaps((b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4), p.box()):
                p.immune = IMMUNITY
                pops.append((tick, p.x - 12, p.y - 70, str(KH["BulletDamage"]), HURT))
                bullets.remove(b)
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "aim":
            frame = KH["Aim"] + aim_index(KH, hx, G, face, target)
        elif state == "shoot":
            since = (timer - 1) % KH["ShotInterval"]
            frame = (KH["Shoot"] if since < KH["MuzzleFlashTicks"] and timer <= KH["ShootTicks"] else KH["Aim"]) + aim_index(KH, hx, G, face, target)
        elif state == "reload":
            frame = KH["Reload"] + (timer // 10) % KH["ReloadFrames"]
        elif abs(hvx) > 0.15:
            frame = KH["Walk"] + int(walked / KH["WalkStep"]) % KH["WalkFrames"]
        else:
            frame = KH["Idle"] + (timer // 20) % KH["IdleFrames"]
        if p.immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        sheriff.draw(img, frame, (hx, G), face > 0)
        for s, st in enumerate(stars):
            launch = KH["StarTelegraph"] + s * KH["StarStagger"]
            telegraph = st["mode"] == 0 and 0 < clock < launch
            spin = KH["FastSpinTicks"] if st["mode"] or telegraph else KH["SpinTicks"]
            f = (tick // spin + s) % KH["StarSpin"] + (KH["StarSpin"] if telegraph else 0)
            cell = KH["StarCell"]
            src = (0, f * (cell + 2), cell, f * (cell + 2) + cell)
            img.alpha_composite(star_sheet.crop(src), (int(st["x"] - cell / 2), int(st["y"] - cell / 2)))
            img.alpha_composite(star_glow.crop(src), (int(st["x"] - cell / 2), int(st["y"] - cell / 2)))
        smoke.draw(img, tick)
        for b in bullets:
            f = heading_frame(b[2], b[3], KD["BulletHeadings"])
            img.alpha_composite(bullet.crop((0, f * 16, 14, f * 16 + 14)), (int(b[0] - 7), int(b[1] - 7)))
        gif.text(img, (10, 8), "Sheriff (rare mini-boss, Old Brass Town): %d life, %d defense, no knockback (Expert)" % (KH["Life"], KH["Defense"]))
        gif.text(img, (10, 28), "three stars every %d s (%d each), six shots of %d, then a %d s reload" % (
            KH["StarCycle"] // 60, KH["StarDamage"], KH["BulletDamage"], KH["ReloadTicks"] // 60))
        pops_and_notes(gif, img, pops, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Mechanical Bull
# ================================================================================================
def scene_bull(out, font):
    W, H, G = 860, 290, 250
    WALL = W - 56
    bg = town_backdrop(W, H, G, wall_x=WALL, wall_right=True)
    gif = Gif(font, (W, H), scale=1.15)
    bull = Planes(TOWN + "NPCs/MechanicalBull", KU)
    p = Player(330, G)
    ux, uvx, face = 60.0, 0.0, 1
    state, timer, cooldown, charge_dir, target_x = "trot", 0, 0, 1, 0.0
    walked = 0.0
    pops, notes = [], []
    charges = 0
    knock_from, knock_landed, knock_dist = None, None, 0.0
    total = int(9.8 * 60)
    for tick in range(total):
        timer += 1
        if cooldown > 0:
            cooldown -= 1
        dx = p.x - ux
        direction = 1 if dx >= 0 else -1
        charging = state == "charge"
        if state == "trot":
            want = direction * KU["TrotSpeed"]
            uvx = min(want, uvx + KU["TrotAccel"]) if uvx < want else max(want, uvx - KU["TrotAccel"])
            face = direction
            if cooldown <= 0 and abs(dx) < KU["ChargeRange"] and abs(p.y - G) < KU["ChargeHeight"] and timer > 30:
                state, timer = "paw", 0
                notes.append((tick, "the telegraph: head down, a hoof scraping, steam snorted (%d ticks)" % KU["PawTicks"]))
        elif state == "paw":
            uvx *= 0.8
            face = direction
            if timer >= KU["PawTicks"]:
                state, timer, charge_dir, target_x = "charge", 0, direction, p.x
                charges += 1
                notes.append((tick, "the charge: straight, it never turns"))
        elif state == "charge":
            want = charge_dir * KU["ChargeSpeed"]
            uvx = min(want, uvx + KU["ChargeAccel"]) if uvx < want else max(want, uvx - KU["ChargeAccel"])
            face = charge_dir
            past = ux > target_x + KU["Overshoot"] if charge_dir > 0 else ux < target_x - KU["Overshoot"]
            if ux + KU["Width"] / 2 + uvx >= WALL:
                ux = WALL - KU["Width"] / 2
                speed = abs(uvx)
                uvx = -charge_dir * 2.0
                state, timer = "stunned", 0
                notes.append((tick, "it slams the wall at %.1f px/tick: stunned for %.1f s" % (speed, KU["StunTicks"] / 60)))
            elif past or timer >= KU["ChargeMaxTicks"] or overlaps((ux - KU["Width"] / 2 - 4, G - KU["Height"] - 4, ux + KU["Width"] / 2 + 4, G + 4), p.box()):
                state, timer = "skid", 0                   # a ram ends the charge (MechanicalBull.RammedSomeone)
        elif state == "skid":
            uvx *= 0.9
            if timer >= KU["SkidTicks"]:
                state, timer, cooldown = "trot", 0, KU["ChargeCooldown"]
        elif state == "stunned":
            uvx *= 0.85
            if timer >= KU["StunTicks"]:
                state, timer, cooldown = "trot", 0, KU["ChargeCooldown"]
        ux += uvx
        walked += abs(uvx)
        # the player: stands for the first charge (thrown towards the wall); for the second it jumps the bull at the last moment
        p.run = 0
        if charges == 2 and state == "charge" and p.y >= G and 0 < p.x - ux < 110 and p.immune <= 0:
            p.jump()
        p.step()
        p.x = max(20.0, min(WALL - 12.0, p.x))
        if knock_from is not None and knock_landed is None and p.y >= G and p.vx == 0.0:
            knock_landed, knock_dist = tick, abs(p.x - knock_from)
        ubox = (ux - KU["Width"] / 2, G - KU["Height"], ux + KU["Width"] / 2, G)
        if p.immune <= 0 and state != "stunned" and overlaps(ubox, p.box()):
            dmg = int(KU["TrotDamage"] * (KU["ChargeDamageMultiplier"] if charging else 1))
            p.hurt(charge_dir if charging else face, VANILLA_KB * (KU["ChargeKnockback"] if charging else 1))
            knock_from, knock_landed = p.x, None
            pops.append((tick, p.x - 12, p.y - 70, str(dmg), HURT))
            if charging:
                notes.append((tick, "rammed: %d, knockback x%g" % (dmg, KU["ChargeKnockback"])))
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "paw":
            frame = KU["Paw"] + (timer // 6) % KU["PawFrames"]
        elif state == "charge":
            frame = KU["Charge"] + int(walked / KU["GallopAnimDistance"]) % KU["ChargeFrames"]
        elif state == "skid":
            frame = KU["Skid"]
        elif state == "stunned":
            frame = KU["Stunned"] + (timer // 6) % KU["StunnedFrames"]
        elif abs(uvx) > 0.15:
            frame = KU["Trot"] + int(walked / KU["TrotAnimDistance"]) % KU["TrotFrames"]
        else:
            frame = KU["Trot"]
        if p.immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player_sprite(flip=True), (int(p.x - 20), int(p.y - 56)))
        bull.draw(img, frame, (ux, G), face > 0)
        d = ImageDraw.Draw(img)
        if state == "paw" and (tick // 6) % 2 == 0:
            nx = ux + KU["NostrilX"] * -face
            d.ellipse([nx - 2, G + KU["NostrilY"] - 4, nx + 8, G + KU["NostrilY"] + 4], fill=STEAM + (255,))
        gif.text(img, (10, 8), "Mechanical Bull (Old Brass Town): %d life, %d defense, %d contact trotting, x%g charging (Expert)" % (
            KU["Life"], KU["Defense"], KU["TrotDamage"], KU["ChargeDamageMultiplier"]))
        pops_and_notes(gif, img, pops, notes, tick, y=28)
        if knock_landed is not None and tick - knock_landed < 100:
            gif.text(img, (10, 48), "thrown %.1f tiles (a vanilla hit: about 5)" % (knock_dist / 16.0), fill=EMBER)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Dinamitrom
# ================================================================================================
def scene_dinamitrom(out, font):
    W, H, G = 760, 280, 240
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.25)
    keg = Planes(TOWN + "NPCs/Dinamitrom", KM)
    blast = load(TOWN + "Projectiles/DinamitromBlast.png")
    p = Player(220, G)
    kegs = [{"x": 700.0, "y": float(G), "vx": 0.0, "vy": 0.0, "state": "hop", "timer": 0, "hop": 20, "alive": True, "shoot": False},
            {"x": 540.0, "y": float(G), "vx": 0.0, "vy": 0.0, "state": "hop", "timer": 0, "hop": 0, "alive": True, "shoot": True, "delay": 170}]
    blasts, pops, notes = [], [], []
    shots = []
    total = int(9.6 * 60)
    for tick in range(total):
        p.step()
        p.x = max(30.0, min(W - 30.0, p.x))
        for k in kegs:
            if not k["alive"] or tick < k.get("delay", 0):
                continue
            k["timer"] += 1
            grounded = k["y"] >= G and k["vy"] >= 0
            dx = p.x - k["x"]
            direction = 1 if dx >= 0 else -1
            if k["state"] == "hop":
                if grounded:
                    k["vx"] *= 0.82
                    k["hop"] += 1
                    if k["hop"] >= KM["HopInterval"]:
                        k["hop"] = 0
                        k["vx"], k["vy"] = direction * KM["HopSpeedX"], -KM["HopSpeedY"]
                if grounded and abs(dx) < KM["LeapRange"] and k["timer"] > 10:
                    k["state"], k["timer"] = "windup", 0
                    notes.append((tick, "the telegraph: crouched, the fuse flaring (%d ticks)" % KM["WindupTicks"]))
            elif k["state"] == "windup":
                k["vx"] *= 0.8
                if k["timer"] >= KM["WindupTicks"]:
                    ddx, ddy = p.x - k["x"], p.y - k["y"]
                    t = max(KM["LeapMinTicks"], min(KM["LeapMaxTicks"], abs(ddx) / 6.0))
                    k["vx"], k["vy"] = ddx / t, max(-KM["LeapMaxUp"], (ddy - 0.5 * KM["Gravity"] * t * t) / t)
                    k["state"], k["timer"] = "leap", 0
                    if k["shoot"]:
                        shots.append([p.x + 10, p.y - 24, 0.0, 0.0, k])
            elif k["state"] == "leap":
                if k["timer"] > 4 and grounded:
                    k["alive"] = False
                    blasts.append([tick, k["x"], k["y"] - KM["Height"] / 2])
                    cx, cy = k["x"], k["y"] - KM["Height"] / 2
                    nx = max(p.box()[0], min(cx, p.box()[2]))
                    ny = max(p.box()[1], min(cy, p.box()[3]))
                    if (cx - nx) ** 2 + (cy - ny) ** 2 <= KM["Radius"] ** 2 and p.immune <= 0:
                        p.hurt(1 if p.x >= cx else -1, KM["BlastKnockback"])
                        pops.append((tick, p.x - 16, p.y - 76, str(KM["BlastDamage"]), HURT))
                        notes.append((tick, "the blast: %d to everyone within %d tiles" % (KM["BlastDamage"], KM["Radius"] // 16)))
            if k["alive"]:
                k["vy"] = min(10.0, k["vy"] + KM["Gravity"])
                k["x"] += k["vx"]
                k["y"] += k["vy"]
                if k["y"] >= G:
                    k["y"], k["vy"] = float(G), 0.0
                kbox = (k["x"] - KM["Width"] / 2, k["y"] - KM["Height"], k["x"] + KM["Width"] / 2, k["y"])
                if k["state"] != "leap" and p.immune <= 0 and overlaps(kbox, p.box()):
                    k["alive"] = False
                    blasts.append([tick, k["x"], k["y"] - KM["Height"] / 2])
        for s in list(shots):                                 # the player's shot at the second keg, mid-leap
            k = s[4]
            if not k["alive"]:
                shots.remove(s)
                continue
            ax, ay = k["x"] - s[0], (k["y"] - KM["Height"] / 2) - s[1]
            d = math.hypot(ax, ay) or 1.0
            s[0] += ax / d * 14
            s[1] += ay / d * 14
            if d < 16:
                k["alive"] = False
                shots.remove(s)
                pops.append((tick, k["x"] - 10, k["y"] - 70, str(KM["Life"]), EMBER))
                notes.append((tick, "shot down first: it only pops, no blast"))
        if tick % TPF:
            continue
        img = bg.copy()
        if p.immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        for k in kegs:
            if not k["alive"] or tick < k.get("delay", 0):
                continue
            face = 1 if p.x >= k["x"] else -1
            grounded = k["y"] >= G
            if k["state"] == "windup":
                frame = KM["Windup"] + (k["timer"] // 3) % KM["WindupFrames"]
            elif k["state"] == "leap":
                frame = KM["Leap"]
            elif not grounded:
                frame = KM["Hop"] + (1 if k["vy"] < 0 else 2)
            elif k["hop"] < 6:
                frame = KM["Hop"] + 3
            elif k["hop"] > KM["HopInterval"] - 6:
                frame = KM["Hop"]
            else:
                frame = KM["Idle"] + (tick // 15) % KM["IdleFrames"]
            keg.draw(img, frame, (k["x"], k["y"]), face > 0)
        d = ImageDraw.Draw(img)
        for s in shots:
            d.ellipse([s[0] - 3, s[1] - 2, s[0] + 3, s[1] + 2], fill=BRASS + (255,))
        for (t0, bx, by) in blasts:
            age = tick - t0
            f = age // KM["TicksPerFrame"]
            if 0 <= f < KM["BlastFrames"]:
                size = KM["BlastSize"]
                cell = blast.crop((0, f * (size + 2), size, f * (size + 2) + size))
                img.alpha_composite(cell, (int(bx - size / 2), int(by - size / 2)))
        gif.text(img, (10, 8), "Dinamitrom (Old Brass Town): %d life, %d defense, no contact damage; blast %d within %d tiles (Expert)" % (
            KM["Life"], KM["Defense"], KM["BlastDamage"], KM["Radius"] // 16))
        pops_and_notes(gif, img, pops, notes, tick, y=28)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Sheriff Badge's stars
# ================================================================================================
def scene_badge(out, font):
    W, H, G = 760, 280, 240
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.25)
    star_sheet = load(TOWN + "Minions/SheriffStarMinion.png")
    star_glow = load(TOWN + "Minions/SheriffStarMinion_Glow.png")
    enemy = collector_sprite()
    px = 200.0
    n = 3
    stars = [{"mode": 0, "x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0, "timer": 0, "heading": 0.0, "hits": set()} for _ in range(n)]
    enemies = [{"x": 560.0 + k * 70, "hp": 120, "hit": {}} for k in range(3)]
    pops = []
    total = int(7.0 * 60)

    def home(i, tick):
        mid = (n - 1) * 0.5
        return px + (i - mid) * KN["RowSpacing"], G - PLAYER_H - KN["HoverHeight"] + abs(i - mid) * 4 - ((tick // 20 + i) % 2) * 2

    for i, st in enumerate(stars):
        st["x"], st["y"] = home(i, 0)
    for tick in range(total):
        for e in enemies:
            if e["hp"] > 0 and e["x"] > px + 60:
                e["x"] -= 0.7
        for i, st in enumerate(stars):
            st["timer"] += 1
            h = home(i, tick)
            if st["mode"] == 1:
                st["vx"], st["vy"] = math.cos(st["heading"]) * KN["DashSpeed"], math.sin(st["heading"]) * KN["DashSpeed"]
                if st["timer"] >= KN["DashTicks"]:
                    st["mode"], st["timer"] = 2, 0
            elif st["mode"] == 2:
                ax, ay = h[0] - st["x"], h[1] - st["y"]
                d = math.hypot(ax, ay)
                if d < KN["HomeSnap"]:
                    st["mode"], st["timer"], st["vx"], st["vy"] = 0, 0, 0.0, 0.0
                else:
                    st["vx"], st["vy"] = ax / d * min(KN["ReturnSpeed"], d), ay / d * min(KN["ReturnSpeed"], d)
            else:
                st["vx"], st["vy"] = (h[0] - st["x"]) * 0.25, (h[1] - st["y"]) * 0.25
                live = [e for e in enemies if e["hp"] > 0 and abs(e["x"] - px) < KN["TargetRange"]]
                if st["timer"] >= KN["MinHoverTicks"] and (tick + i * KN["Stagger"]) % KN["AttackCycle"] == 0 and live:
                    e = min(live, key=lambda e: abs(e["x"] - px))
                    st["heading"] = math.atan2((G - 14) - st["y"], e["x"] - st["x"])
                    st["mode"], st["timer"] = 1, 0
            st["x"] += st["vx"]
            st["y"] += st["vy"]
            if st["mode"]:
                for e in enemies:
                    if e["hp"] > 0 and overlaps((st["x"] - 10, st["y"] - 10, st["x"] + 10, st["y"] + 10), (e["x"] - 14, G - 28, e["x"] + 14, G)):
                        last = e["hit"].get(i, -999)
                        if tick - last >= KN["HitCooldown"]:
                            e["hit"][i] = tick
                            e["hp"] -= KN["Damage"]
                            pops.append((tick, e["x"] - 8, G - 60, str(KN["Damage"]), AETHER))
        if tick % TPF:
            continue
        img = bg.copy()
        img.alpha_composite(player_sprite(flip=False), (int(px - 20), G - 56))
        for e in enemies:
            if e["hp"] > 0:
                img.alpha_composite(enemy, (int(e["x"] - enemy.width / 2), G - enemy.height))
        cell = 26
        for i, st in enumerate(stars):
            spin = KN["SpinTicks"] if st["mode"] == 0 else KN["FastSpinTicks"]
            f = (tick // spin + i) % 6
            src = (0, f * (cell + 2), cell, f * (cell + 2) + cell)
            img.alpha_composite(star_sheet.crop(src), (int(st["x"] - cell / 2), int(st["y"] - cell / 2)))
            img.alpha_composite(star_glow.crop(src), (int(st["x"] - cell / 2), int(st["y"] - cell / 2)))
        gif.text(img, (10, 8), "Sheriff Badge: one star per minion slot, %d damage, one pass each per %d ticks (%d ticks apart)" % (
            KN["Damage"], KN["AttackCycle"], KN["Stagger"]))
        gif.text(img, (10, 28), "each flies at an enemy and back, hitting everything on its way", fill=AETHER)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Items sheet
# ================================================================================================
def items_png(out, font):
    gif = Gif(font, (10, 10))
    icons = [("Shark Eye (+5% melee crit)", load("Content/Ocean/Items/SharkEye.png")),
             ("Hawk Eye (+5% ranged crit)", load("Content/Desert/Items/HawkEye.png")),
             ("Sheriff Badge", load(TOWN + "Minions/SheriffBadge.png")),
             ("its buff", load(TOWN + "Minions/SheriffStarBuff.png"))]
    star = load(TOWN + "Projectiles/SheriffStar.png")
    minion = load(TOWN + "Minions/SheriffStarMinion.png")
    bullet = load(TOWN + "Projectiles/RustyBullet.png")
    blast = load(TOWN + "Projectiles/DinamitromBlast.png")
    W, H = 1240, 560
    img = Image.new("RGBA", (W, H), (36, 40, 48, 255))
    light = Image.new("RGBA", (W, H // 2), (150, 180, 210, 255))
    img.paste(light, (0, H // 2))
    for half in (0, 1):
        y0 = half * (H // 2)
        x = 20
        for name, im in icons:
            img.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.NEAREST), (x, y0 + 40))
            gif.text(img, (x - 4, y0 + 12), name)
            x += 200
        for k in range(12):
            cell = star.crop((0, k * 28, 26, k * 28 + 26)).resize((52, 52), Image.NEAREST)
            img.alpha_composite(cell, (20 + k * 56, y0 + 130))
        gif.text(img, (20, y0 + 112), "the Sheriff's star: 6 spin frames, then 6 with the rim lit (the telegraph)")
        for k in range(6):
            cell = minion.crop((0, k * 28, 26, k * 28 + 26)).resize((52, 52), Image.NEAREST)
            img.alpha_composite(cell, (720 + k * 56, y0 + 130))
        gif.text(img, (720, y0 + 112), "the deputy's star (the minion)")
        for k in range(KD["BulletHeadings"]):
            cell = bullet.crop((0, k * 16, 14, k * 16 + 14))
            img.alpha_composite(cell, (20 + (k % 8) * 34, y0 + 216 + (k // 8) * 18))
        gif.text(img, (20, y0 + 196), "rusty bullet: %d headings (its smoke trail is drawn by the game)" % KD["BulletHeadings"])
        for k in range(7):
            cell = blast.crop((0, k * 130, 128, k * 130 + 128)).resize((64, 64), Image.NEAREST)
            img.alpha_composite(cell, (320 + k * 70, y0 + 192))
        gif.text(img, (320, y0 + 176), "Dinamitrom blast (half size)")
    img.convert("RGB").save(out)
    print(out, img.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a.add_argument("--date", default="2026-11-04", help="date prefix for the cogtuna/bandit/sheriff/bull/dinamitrom proofs")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("punch", lambda: scene_punch(os.path.join(args.out, "2026-11-04_dungeon-beat-boxer-punch.gif"), args.font)),
            ("cogtuna", lambda: scene_cogtuna(os.path.join(args.out, args.date + "_ocean-cogtuna.gif"), args.font)),
            ("bandit", lambda: scene_bandit(os.path.join(args.out, args.date + "_oldbrasstown-bandit.gif"), args.font)),
            ("bull", lambda: scene_bull(os.path.join(args.out, args.date + "_oldbrasstown-bull.gif"), args.font)),
            ("dinamitrom", lambda: scene_dinamitrom(os.path.join(args.out, args.date + "_oldbrasstown-dinamitrom.gif"), args.font)),
            ("badge", lambda: scene_badge(os.path.join(args.out, "2026-11-04_oldbrasstown-sheriff-badge.gif"), args.font)),
            ("items", lambda: items_png(os.path.join(args.out, args.date + "_items-eyes.png"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
