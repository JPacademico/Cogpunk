"""D5 proofs for the playtest fixes of 2026-11-26. Run from the repo root:

    python -P tools/sim/update_2026_11_26_sim.py [--out docs/media] [--only scorpion,tyrant,arm,glaives,wrench,collector,tar,gauge,trashtr0m,coghaven,water]

Offline replays with the real sprites and the C# constants, 60 ticks a second, 3 ticks a GIF frame (50 ms). "Before" art is
read from git's last commit (HEAD). Leaves out: lighting, sound, netcode, vanilla's own sprites (the player is the sims'
armour mannequin), the composite arm's exact hand placement (the hand is put on the art's hub).

    scorpion   the Cogscorpion's walk before and after the gait fix, walking left with the camera on it: after, its
               planted feet stay put on the ground; before, they slid forward (it looked like it walked backwards).
    tyrant     the Tar Tyrant's idle at a one-block step, before (the claw's talons cut at the ground line) and after
               (the claw raised: every talon above the ground).
    arm        the Jade Coin's third form, the golem's arm: floating beside the player, hanging, then raised and following a
               target (GolemFollow, GolemTurn), a jade bolt every GolemCycle ticks.
    glaives    the Jade Cursed Glaives' slash aimed at the cursor (PackAim: side and tilt), at four cursor positions.
    wrench     the Metal Wrench's slam turning to the cursor's side as each auto-swing starts (the cursor crosses over).
    collector  the Rust Collector rolling into a three-block wall at a crawl and jumping it (WallTilesAhead, the jump speed).
    tar        the Living Tar hopping, facing the player on either side.
    gauge      the steam gauge refilling, before (10 every 30 ticks) and after (the same rate, a little every tick).
    trashtr0m  Trash-Tr0m's attack picks with a player always in range, before (always the suction) and after (never two
               running, 40% when allowed): a PNG.
    coghaven   the gate and the pavilion, before (solid lacquer posts) and after (posts on the panel wall where people walk):
               a PNG from the blueprints.
    water      the Junkyard's water: vanilla's ocean water (what was drawn) and the tar style now drawn there: a PNG.
"""
import argparse
import io
import math
import os
import random
import re
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import stage as S  # noqa: E402
import make_teaser as M  # noqa: E402
import update_2026_11_25_sim as U  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
W, H = 440, 240
FLOOR = 208
STEP = 3


def head_bytes(rel):
    return subprocess.run(["git", "show", "HEAD:" + rel], capture_output=True, cwd=ROOT).stdout


def head_png(rel):
    return Image.open(io.BytesIO(head_bytes(rel))).convert("RGBA")


def head_text(rel):
    return head_bytes(rel).decode("utf-8")


def ints_text(text):
    return {k: int(v) for k, v in re.findall(r"\b(\w+) = (-?\d+)\b", text)}


def short_table(text, name):
    m = re.search(r"static readonly short\[\] " + name + r" = \{([^}]*)\}", text)
    return [int(v) for v in m.group(1).replace("\n", " ").split(",") if v.strip()]


def grid_cell(sheet, k, cw, ch, cols=1, gap=2):
    x, y = (k % cols) * (cw + gap), (k // cols) * (ch + gap)
    return sheet.crop((x, y, x + cw, y + ch))


def put_cell(img, cell, ox, oy, ax, ay, flip):
    """A rig cell drawn as DepthLayers.DrawCell draws it: its origin on (ax, ay), mirrored about it when flipped."""
    if flip:
        S.blit(img, S.mirror(cell), int(ax) - (cell.width - ox), int(ay) - oy)
    else:
        S.blit(img, cell, int(ax) - ox, int(ay) - oy)


def label(img, s, x, y):
    U.label(img, s, x, y)


# ================================================================================================
def scorpion_gif(path):
    rel = "Content/Coghaven/NPCs/Cogscorpion"
    planes_new = [S.darkened(S.load(rel + "_Far.png"), 0.88), S.load(rel + ".png"), S.load(rel + "_Near.png"), S.load(rel + "_Glow.png")]
    planes_old = [S.darkened(head_png(rel + "_Far.png"), 0.88), head_png(rel + ".png"), head_png(rel + "_Near.png"), head_png(rel + "_Glow.png")]
    r = U.ints(rel + "RigData.cs")
    cw, ch = r["CellWidth"], r["CellHeight"]
    speed = 1.5
    frames = []
    dist = 0.0
    for t in range(0, 240, STEP):
        dist = t * speed
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for row, (planes, name) in enumerate(((planes_old, "BEFORE: the planted feet slide forward (it walks backwards)"),
                                              (planes_new, "AFTER: the planted feet stay put on the ground as it walks"))):
            band = U.cave_backdrop(floor=H // 2 - 18, w=W, h=H // 2, scroll=-dist)
            k = r["Walk"] + int(dist // r["WalkStep"]) % r["WalkFrames"]
            for p in planes:
                put_cell(band, grid_cell(p, k, cw, ch), r["OriginX"], r["OriginY"], W // 2, H // 2 - 18, False)
            label(band, name, 6, 4)
            img.alpha_composite(band, (0, row * (H // 2)))
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def tyrant_gif(path):
    rel = "Content/Bosses/TarTyrant/"
    cur_text = open(os.path.join(ROOT, rel + "TarTyrantRigData.cs"), encoding="utf-8").read()
    old_text = head_text(rel + "TarTyrantRigData.cs")
    cache = {}

    def page(old, base, n):
        key = (old, base, n)
        if key not in cache:
            name = base if n == 0 else base + "_Page%d" % n
            cache[key] = head_png(rel + name + ".png") if old else S.load(rel + name + ".png")
        return cache[key]

    def draw(img, old, text, frame, ax, ay):
        for layer, base, dark in (("FarFrames", "TarTyrant_Far", 0.88), ("BodyFrames", "TarTyrant", 1.0), ("NearFrames", "TarTyrant_Near", 1.0)):
            t = short_table(text, layer)
            pg, x, y, w, h, ox, oy = t[frame * 7:frame * 7 + 7]
            im = page(old, base, pg).crop((x, y, x + w, y + h))
            vis = min(h, oy + 2)                               # DepthLayers.GroundOverlap
            im = im.crop((0, 0, w, vis))
            if dark != 1.0:
                im = S.darkened(im, dark)
            S.blit(img, S.mirror(im), int(ax) - (w - ox), int(ay) - oy)   # facing right, as it climbs

    r = ints_text(cur_text)
    frames = []
    for t in range(0, 8 * 10 * 2, STEP):
        k = r["Idle0"] + (t // 10) % r["IdleFrames"]
        img = Image.new("RGBA", (W * 2, 300), (40, 46, 62, 255))
        for col, (old, text, name) in enumerate(((True, old_text, "BEFORE: the claw's talons cut at the ground line"),
                                                 (False, cur_text, "AFTER: the claw raised, every talon above the ground"))):
            band = Image.new("RGBA", (W, 300), (46, 52, 70, 255))
            d = ImageDraw.Draw(band)
            gy = 250
            d.rectangle([0, gy - 16, 296, 300], fill=(70, 50, 38, 255))     # the block it has climbed
            d.rectangle([296, gy, W, 300], fill=(70, 50, 38, 255))          # the lower ground: its claw hangs over the edge
            draw(band, old, text, k, 150, gy - 16)
            label(band, name, 6, 4)
            img.alpha_composite(band, (col * W, 0))
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def arm_gif(path):
    g = U.ints("Content/Coghaven/NPCs/JadeGolemRigData.cs")
    c = S.consts("Content/Research/Summons/JadeSpirit.cs")
    arm = S.load("Content/Coghaven/NPCs/JadeGolem_Arm.png")
    glow = S.load("Content/Coghaven/NPCs/JadeGolem_ArmGlow.png")
    bolt = S.load("Content/Gems/Projectiles/JadeBolt.png")
    bolt = bolt.crop(bolt.getchannel("A").getbbox() or (0, 0, bolt.width, bolt.height))
    px, pfeet = 150, FLOOR
    pc = (px, pfeet - 21)
    aim = math.pi / 2
    sx, sy = px + c["GolemGuard"], pc[1] + c["GolemHeight"]
    vx = vy = 0.0
    cycle = 0
    bolts = []
    target = None
    frames = []
    for t in range(420):
        if t == 90:
            target = [380.0, FLOOR - 40.0, 0]
        if target and t > 90:
            target[1] = FLOOR - 40 - 60 * math.sin((t - 90) / 70.0) ** 2   # it bobs up and down: the arm follows
        side = 1 if not target or target[0] >= px else -1
        bob = math.sin(t / 60.0 * 1.6) * 4
        goal = (px + side * c["GolemGuard"], pc[1] + c["GolemHeight"] + bob)
        vx += ((goal[0] - sx) * 0.1 - vx) * 0.3
        vy += ((goal[1] - sy) * 0.1 - vy) * 0.3
        sx += vx
        sy += vy
        if target:
            ang = math.atan2(target[1] - sy, abs(target[0] - sx))
            lo, hi = math.radians(g["ArmMinDegrees"]), math.radians(g["ArmMinDegrees"] + (g["ArmFrames"] - 1) * g["ArmStepDegrees"])
            ang = max(lo, min(hi, ang))
            aim += max(-c["GolemTurn"], min(c["GolemTurn"], (ang - aim) * c["GolemFollow"]))
            cycle = min(cycle + 1, int(c["GolemCycle"]))
            if cycle >= c["GolemCycle"] and abs(ang - aim) < c["GolemAimError"]:
                cycle = 0
                palm = (sx + side * math.cos(aim) * g["PalmReach"], sy + math.sin(aim) * g["PalmReach"])
                dx, dy = target[0] - palm[0], target[1] - palm[1]
                d = math.hypot(dx, dy) or 1
                bolts.append([palm[0], palm[1], dx / d * c["BoltSpeed"], dy / d * c["BoltSpeed"]])
        else:
            aim = min(math.pi / 2, aim + c["GolemTurn"] * 0.5)
        for b in bolts:
            b[0] += b[2]
            b[1] += b[3]
        bolts = [b for b in bolts if not target or abs(b[0] - target[0]) > 14 or abs(b[1] - target[1]) > 20]
        if t % STEP:
            continue
        img = U.backdrop(floor=FLOOR, w=W, h=H)
        U.put_player(img, px, pfeet, 0, side > 0)
        frame = max(0, min(g["ArmFrames"] - 1, round((math.degrees(aim) - g["ArmMinDegrees"]) / g["ArmStepDegrees"])))
        flip = side > 0
        ax = sx - g["ShoulderX"] * -side
        ay = sy - g["ShoulderY"]
        put_cell(img, grid_cell(arm, frame, g["ArmCellWidth"], g["ArmCellHeight"], g["ArmColumns"]), g["ArmOriginX"], g["ArmOriginY"], ax, ay, flip)
        put_cell(img, grid_cell(glow, frame, g["ArmCellWidth"], g["ArmCellHeight"], g["ArmColumns"]), g["ArmOriginX"], g["ArmOriginY"], ax, ay, flip)
        if target:
            d = ImageDraw.Draw(img)
            d.rectangle([target[0] - 10, target[1] - 18, target[0] + 10, target[1] + 18], outline=(220, 220, 230, 255))
            label(img, "a target", int(target[0]) - 18, int(target[1]) - 32)
        for b in bolts:
            S.blit(img, bolt, int(b[0]) - bolt.width // 2, int(b[1]) - bolt.height // 2)
        label(img, "JADE COIN, third form: the golem's arm floats beside you (no body); hanging when idle, aimed and firing", 6, 4)
        label(img, "a jade bolt every %d ticks once it is on the target (30 a hit, as the golem's)" % c["GolemCycle"], 6, 28)
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def glaives_gif(path):
    rel = "Content/Bosses/Jadey/Weapons/"
    r = U.ints(rel + "JadeGlaiveRigData.cs")
    a = S.arrays(rel + "JadeGlaiveRigData.cs")
    sheet, trail = S.load(rel + "JadeGlaiveSlash.png"), S.load(rel + "JadeGlaiveSlash_Trail.png")
    cw, ch, gap, n = r["CellWidth"], r["CellHeight"], r["Gap"], r["FramesPerSlash"]
    cursors = [(380, 120, "level right"), (330, 20, "up and right"), (60, 200, "down and left"), (230, 0, "straight up")]
    px, pfeet = 220, FLOOR
    pc = (px, pfeet - 21)
    frames = []
    for ci, (mx, my, name) in enumerate(cursors):
        dx, dy = mx - pc[0], my - pc[1]
        side = -1 if dx < 0 else 1
        tilt = math.atan2(dy, abs(dx))
        for kind in (0, 1):
            for f in range(n):
                for _ in range(2):                                # 2 GIF frames a slash frame
                    img = U.backdrop(floor=FLOOR, w=W, h=H)
                    U.put_player(img, px, pfeet, 0, side > 0)
                    s = kind * r["SamplesPerSlash"] + f * 2
                    hub = (a["HubX"][s], a["HubY"][s])
                    rel_x, rel_y = hub[0] - r["ShoulderX"], hub[1] - r["ShoulderY"]
                    cx_, sx_ = math.cos(tilt), math.sin(tilt)
                    hand = (pc[0] + side * r["ShoulderX"] + (rel_x * cx_ - rel_y * sx_) * side, pc[1] + r["ShoulderY"] + rel_x * sx_ + rel_y * cx_)
                    cell = grid_cell(sheet, kind + f * 2, cw, ch, 2, gap) if False else sheet.crop(
                        (kind * (cw + gap), f * (ch + gap), kind * (cw + gap) + cw, f * (ch + gap) + ch))
                    tcell = trail.crop((kind * (cw + gap), f * (ch + gap), kind * (cw + gap) + cw, f * (ch + gap) + ch))
                    ox, oy = r["OriginX"] + hub[0], r["OriginY"] + hub[1]
                    for layer, add in ((tcell, True), (cell, False)):
                        im = layer if side > 0 else S.mirror(layer)
                        o = (ox, oy) if side > 0 else (cw - ox, oy)
                        rot = tilt if side > 0 else -tilt
                        turned, pivot = M.rotated(im, rot, o)
                        if add:
                            S.blit_add(img, turned, int(hand[0]) - pivot[0], int(hand[1]) - pivot[1], 0.85)
                        else:
                            S.blit(img, turned, int(hand[0]) - pivot[0], int(hand[1]) - pivot[1])
                    d = ImageDraw.Draw(img)
                    d.line([(mx - 5, my), (mx + 5, my)], fill=(255, 255, 255, 255))
                    d.line([(mx, my - 5), (mx, my + 5)], fill=(255, 255, 255, 255))
                    label(img, "JADE CURSED GLAIVES: the slash turns towards the cursor (+), here %s" % name, 6, 4)
                    frames.append(img)
    U.save_gif(frames, path, scale=1)


# ================================================================================================
def wrench_gif(path):
    w = S.consts("Content/Junkyard/Weapons/MetalWrench.cs")
    sprite = S.load("Content/Junkyard/Weapons/MetalWrench.png")
    use = int(w["UseTime"])
    ground = 0.95

    def eo(t):
        return 1 - (1 - t) ** 3

    def ei(t):
        return t ** 3

    def phase(d, a, b):
        return max(0.0, min(1.0, (d - a) / (b - a)))

    def slam(d):
        if d < w["LiftEnd"]:
            return ground + (w["RaisedAngle"] - ground) * eo(phase(d, 0, w["LiftEnd"]))
        if d < w["HangEnd"]:
            return w["RaisedAngle"] - w["HangDrift"] * phase(d, w["LiftEnd"], w["HangEnd"])
        if d < w["ImpactAt"]:
            return w["RaisedAngle"] - w["HangDrift"] + (ground - w["RaisedAngle"] + w["HangDrift"]) * ei(phase(d, w["HangEnd"], w["ImpactAt"]))
        if d < w["BounceEnd"]:
            return ground - w["BounceLift"] * math.sin(math.pi * phase(d, w["ImpactAt"], w["BounceEnd"]))
        return ground

    px, pfeet = 220, FLOOR
    frames = []
    direction = 1
    for t in range(use * 6):
        mx = 220 + 170 * math.sin(t / (use * 6) * math.tau * 1.5 + 0.4)    # the cursor sweeps from side to side
        k = t % use
        if k == 0:
            direction = 1 if mx >= px else -1                            # vanilla's first tick of a swing: UseItem turns it
        if t % STEP:
            continue
        img = U.backdrop(floor=FLOOR, w=W, h=H)
        U.put_player(img, px, pfeet, 0, direction > 0)
        ang = slam(k / use)
        hand = (px + direction * 6, pfeet - 30)
        im = sprite if direction > 0 else S.mirror(sprite)
        pivot = (8, sprite.height - 8) if direction > 0 else (sprite.width - 8, sprite.height - 8)
        rot = (ang + math.pi / 4) if direction > 0 else -(ang + math.pi / 4)
        turned, pv = M.rotated(im, rot, pivot)
        S.blit(img, turned, int(hand[0]) - pv[0], int(hand[1]) - pv[1])
        d = ImageDraw.Draw(img)
        my = 120
        d.line([(mx - 5, my), (mx + 5, my)], fill=(255, 255, 255, 255))
        d.line([(mx, my - 5), (mx, my + 5)], fill=(255, 255, 255, 255))
        label(img, "METAL WRENCH: each auto-swing turns to the cursor's side (+) as it starts; never mid-swing", 6, 4)
        label(img, "34 damage (was 38); the right-click parry is gone", 6, 28)
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def collector_gif(path):
    c = S.consts("Content/Junkyard/NPCs/RustCollector.cs")
    sheet = S.vanilla_frames("Content/Junkyard/NPCs/RustCollector.png", int(c["FrameCount"]))
    wall = (250, FLOOR - 48, 300, FLOOR)                                 # three blocks tall
    x, y, vx, vy = 40.0, float(FLOOR), 0.0, 0.0
    ramp, cooldown, fc = 0, 0, 0.0
    frames = []
    jumped = -99
    for t in range(300):
        want = 1
        ramp = min(ramp + 1, c["RampTicks"])
        accel = c["BaseAccel"] + (c["MaxAccel"] - c["BaseAccel"]) * ramp / c["RampTicks"]
        vx = min(2.0, vx + accel)                                         # held to a crawl here: a slow approach (no bonk)
        nx = x + vx
        on_wall = wall[0] - 20 <= x <= wall[2] + 20
        floor_y = wall[1] if wall[0] - 18 <= nx <= wall[2] + 18 and y <= wall[1] + 1 else FLOOR
        blocked = y > wall[1] and wall[0] - 20 <= nx + 20 <= wall[2] and nx < wall[0]
        if blocked:
            vx = 0.0
            nx = x
        x = nx
        if cooldown > 0:
            cooldown -= 1
        if vy == 0 and blocked and cooldown == 0:
            h_tiles = 3
            vy = -max(c["JumpMin"], min(c["JumpMax"], c["JumpBase"] + c["JumpPerTile"] * h_tiles))
            vx = max(vx, c["JumpRun"])
            cooldown = int(c["JumpCooldownTicks"])
            jumped = t
        vy = min(10.0, vy + 0.3) if (vy != 0 or y < floor_y) else 0.0
        y += vy
        floor_y = wall[1] if wall[0] - 18 <= x <= wall[2] + 18 else FLOOR
        if y >= floor_y and vy >= 0:
            y, vy = float(floor_y), 0.0
        fc = (fc + abs(vx)) % 32
        if t % STEP:
            continue
        img = U.backdrop(floor=FLOOR, w=W, h=H)
        d = ImageDraw.Draw(img)
        d.rectangle(wall, fill=(104, 78, 58, 255))
        for yy in range(wall[1], wall[3], 16):
            for xx in range(wall[0], wall[2], 16):
                d.rectangle([xx, yy, xx + 15, yy + 15], outline=(70, 52, 40, 255))
        fr = sheet[int(fc // 8) % int(c["RollFrames"])]
        im = S.mirror(fr)                                                  # its sheet faces left; it rolls right
        S.blit(img, im, int(x) - im.width // 2, int(y) - im.height + 4)
        label(img, "RUST COLLECTOR: blocked at a crawl, it reads the wall in front (3 blocks) and jumps it", 6, 4)
        if t - jumped < 40:
            label(img, "jump: %.1f px/tick" % min(c["JumpMax"], c["JumpBase"] + c["JumpPerTile"] * 3), int(x) - 30, int(y) - 70)
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def tar_gif(path):
    sheet = S.vanilla_frames("Content/Junkyard/NPCs/LivingTar.png", 2)
    x, y, vy = 220.0, float(FLOOR), 0.0
    frames = []
    for t in range(360):
        px = 90 if t < 180 else 350
        if y >= FLOOR and t % 60 == 30:
            vy = -6.0
        vy = vy + 0.3 if (y < FLOOR or vy < 0) else 0.0
        y = min(float(FLOOR), y + vy)
        if t % STEP:
            continue
        img = U.backdrop(floor=FLOOR, w=W, h=H)
        U.put_player(img, px, FLOOR, 0, px < x)
        fr = sheet[1 if y < FLOOR else (t // 10) % 2]
        right = px >= x                                                  # spriteDirection 1: drawn flipped (its sheet faces left)
        im = S.mirror(fr) if right else fr
        S.blit(img, im, int(x) - im.width // 2, int(y) - im.height + 4)
        label(img, "LIVING TAR: it faces its target now (vanilla's slime AI never set the sprite's direction)", 6, 4)
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def gauge_gif(path):
    g = S.consts("Content/Mechanist/SteamGaugeSystem.cs")
    sheet = S.load("Content/Mechanist/SteamGauge.png")
    gw, gh, stride = int(g["Width"]), int(g["Height"]), int(g["Stride"])
    top, bottom = int(g["FillTop"]), int(g["FillBottom"])
    sp = S.consts("Content/Mechanist/SteamPlayer.cs")
    regen, interval = sp["BaseRegenAmount"], sp["RegenIntervalTicks"]
    smax = 55
    frames = []
    old, new, carry, timer = 0, 0, 0.0, 0
    for t in range(0, 220):
        timer += 1
        if timer >= interval:
            timer = 0
            old = min(smax, old + regen)
        amount = regen / interval + carry
        whole = int(amount)
        carry = amount - whole
        new = min(smax, new + whole)
        if t % STEP:
            continue
        img = Image.new("RGBA", (300, 240), (24, 26, 34, 255))
        for col, (val, name) in enumerate(((old, "BEFORE: 10 every 0.5 s"), (new, "AFTER: the same, every tick"))):
            tank = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
            tank.alpha_composite(sheet.crop((0, 0, gw, gh)))
            level = int((bottom - top) * val / smax * 0.5) * 2
            if level > 0:
                tank.alpha_composite(sheet.crop((0, stride + bottom - level, gw, stride + bottom)), (0, bottom - level))
            tank.alpha_composite(sheet.crop((0, 3 * stride, gw, 3 * stride + gh)))
            big = tank.resize((gw * 3, gh * 3), Image.NEAREST)
            img.alpha_composite(big, (30 + col * 150, 30))
            label(img, name, 6 + col * 150, 228)
            label(img, "%d/%d" % (val, smax), 50 + col * 150, 14)
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def trashtr0m_png(path):
    rnd = random.Random(26)
    chance = S.consts("Content/Bosses/TrashTr0m/TrashTr0m.cs")["SuckChance"]
    n = 40
    old = ["suck"] * n
    new, last = [], False
    for _ in range(n):
        suck = not last and rnd.random() < chance
        last = suck
        new.append("suck" if suck else "slam")
    img = Image.new("RGBA", (n * 14 + 20, 124), (24, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for row, seq in enumerate((old, new)):
        for i, a in enumerate(seq):
            col = (67, 160, 150) if a == "suck" else (223, 185, 78)
            d.rectangle([10 + i * 14, 24 + row * 44, 10 + i * 14 + 11, 24 + row * 44 + 18], fill=col + (255,))
        label(img, ("BEFORE: a player in range, so always the suction (%d/%d)" if row == 0 else
                    "AFTER: never two suctions running, %d%% when allowed: %%d of %%d suck" % round(chance * 100)) % (seq.count("suck"), n)
              if row == 0 else ("AFTER: never two suctions running, 40%% when allowed: %d of %d suck" % (seq.count("suck"), n)), 10, 8 + row * 44)
    label(img, "gold: slam, teal: suction (Trash-Tr0m's 40 next attacks with a player always in suction range)", 10, 96)
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save(path)
    print("wrote", path)


# ================================================================================================
def coghaven_png(path):
    key = {"F": (196, 180, 150), "f": (196, 180, 150), "R": (168, 44, 42), "r": (168, 44, 42), "G": (138, 93, 34), "T": (30, 114, 88),
           "Y": (223, 185, 78), "/": (30, 114, 88), "\\": (30, 114, 88), "(": (196, 180, 150), ")": (196, 180, 150), "-": (30, 114, 88),
           "O": (236, 113, 40), "A": (138, 93, 34), ">": (138, 93, 34), "<": (138, 93, 34), "i": (223, 185, 78)}
    wall = (92, 26, 32)

    def plans(text):
        out = {}
        for name in ("Gate", "Pavilion"):
            m = re.search(r"public static readonly string\[\] " + name + r" = \{(.*?)\};", text, re.S)
            out[name] = [s.encode().decode("unicode_escape") for s in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))]
        return out

    old = plans(head_text("Content/Coghaven/Generation/CoghavenBlueprints.cs"))
    new = plans(open(os.path.join(ROOT, "Content/Coghaven/Generation/CoghavenBlueprints.cs"), encoding="utf-8").read())
    cell = 6
    pieces = []
    for name in ("Gate", "Pavilion"):
        for which, plan in (("before", old[name]), ("after", new[name])):
            w, h = len(plan[0]), len(plan)
            im = Image.new("RGBA", (w * cell + 8, h * cell + 22), (120, 170, 220, 255))
            d = ImageDraw.Draw(im)
            for y, line in enumerate(plan):
                for x, ch in enumerate(line):
                    x0, y0 = 4 + x * cell, 18 + y * cell
                    if ch == ".":
                        d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=wall + (255,))
                    elif ch in key:
                        d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=key[ch] + (255,), outline=(0, 0, 0, 70))
            label(im, "%s %s" % (name, which), 4, 3)
            pieces.append(im)
    width = sum(p.width for p in pieces) + 10 * len(pieces)
    height = max(p.height for p in pieces) + 20
    out = Image.new("RGBA", (width, height), (24, 26, 34, 255))
    x = 0
    for p in pieces:
        out.alpha_composite(p, (x, 0))
        x += p.width + 10
    label(out, "red cells: solid lacquer blocks; dark red: the panel wall behind (walk through)", 4, height - 14)
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(path)
    print("wrote", path)


# ================================================================================================
def water_png(path):
    sheet = S.load("Content/Junkyard/Tar/TarWaterStyle.png")
    counts = {}
    for c in sheet.crop((0, 0, 48, 1280)).get_flattened_data():
        if c[3]:
            counts[c] = counts.get(c, 0) + 1
    body = max(counts, key=counts.get)                              # the tar's own colour (a mock: the renderer's cells
    surface = sheet.crop((0, 1280, 16, 1284))                       # aren't drawn here), and its calm surface strip on top
    w, h = 320, 120
    out = Image.new("RGBA", (w * 2 + 10, h + 20), (24, 26, 34, 255))
    for col, name in enumerate(("BEFORE: vanilla's ocean water (its background won)", "AFTER: the Junkyard's tar (its colours)")):
        img = U.backdrop(floor=40, w=w, h=h)
        pool = Image.new("RGBA", (w, h - 50), (0, 0, 0, 0))
        if col == 0:
            pool.paste((44, 92, 176, 255), (0, 0, w, h - 50))
        else:
            pool.paste(body, (0, 0, w, h - 50))
            for xx in range(0, w, 16):
                pool.alpha_composite(surface, (xx, 0))
        img.alpha_composite(S.faded(pool, 0.6), (0, 50))            # vanilla draws water at 0.6 opacity
        label(img, name, 4, 4)
        out.alpha_composite(img, (col * (w + 10), 0))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(path)
    print("wrote", path)


SCENES = {
    "scorpion": ("coghaven-cogscorpion-walk.gif", scorpion_gif),
    "tyrant": ("boss-tartyrant-hand.gif", tyrant_gif),
    "arm": ("summon-jade-coin-arm.gif", arm_gif),
    "glaives": ("weapon-jade-glaives-aim.gif", glaives_gif),
    "wrench": ("weapon-metal-wrench-aim.gif", wrench_gif),
    "collector": ("mob-rust-collector-jump.gif", collector_gif),
    "tar": ("mob-living-tar-facing.gif", tar_gif),
    "gauge": ("mechanist-steam-gauge-fill.gif", gauge_gif),
    "trashtr0m": ("boss-trashtr0m-attacks.png", trashtr0m_png),
    "coghaven": ("coghaven-arches.png", coghaven_png),
    "water": ("junkyard-tar-water.png", water_png),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    a = ap.parse_args()
    os.chdir(ROOT)
    os.makedirs(a.out, exist_ok=True)
    for n in (a.only.split(",") if a.only else list(SCENES)):
        fname, fn = SCENES[n]
        fn(os.path.join(a.out, "2026-11-26_" + fname))


if __name__ == "__main__":
    main()
