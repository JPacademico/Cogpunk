"""D5 proofs for the 0.2.0 batch of 2026-11-26 (the second request that day). Run from the repo root:

    python -P tools/sim/update_2026_11_26b_sim.py [--out docs/media] [--only golem,coin,lizard,gems,scorpion,slowmo,items,research]

Offline replays with the real sprites and the C# constants, 60 ticks a second. Leaves out: lighting, sound, netcode,
vanilla's own sprites (the player is the sims' armour mannequin; vanilla items in the research mock are named, not drawn).

    golem     the Jade Golem v3 (sideways): walking (the planted feet), stopping, aiming at the player (the arm sheet's frame
              for each angle, AimFollow/AimMaxTurn), the charge in his palm, the dotted aim line, the lock, the ray, the arm
              lowered again; the ray's nodes and the charge in the new emerald glow.
    coin      the Jade Coin's spirits: a jade coin over the player's head between fights; a target in range: the coin spins
              up and bursts into its creature (TransformTicks, the burst over the change), it fights; the target gone,
              CoinGrace ticks later it bursts back into its coin and floats home. Two spirits: the bat and the golem's arm.
    lizard    the Crystal Lizard hit while running: it lets go of its tail (the sheets' tailless column), which lies
              twitching (CrystalLizard_Tail's jerks, slower and weaker, the strong ones a hop) and fades.
    gems      a PNG: the lizard in each of its eight gems, with and without its tail, and the tail's four curls.
    scorpion  a PNG (the Cogscorpion before and after: 85% of its size, beside the player) and a GIF (its walk now).
    slowmo    a crit kill's slow motion before (0.33 s, one update in five: a shutter, then full speed at once) and after
              (0.7 s, eased down, the glide between updates, eased back up), a bolt flying through it, the speed below.
    items     a PNG: the Cogfish, the Tar Immunity Potion and its buff, the three redrawn banners, and the Jade Cursed
              Glaives with the artifact tag.
    research  a PNG: where the four new research nodes sit (as question marks and revealed) and the Artifacts tab.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import stage as S  # noqa: E402
import update_2026_11_25_sim as U  # noqa: E402
import update_2026_11_26_sim as V  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
W, H = 440, 240
FLOOR = 208
STEP = 3


def label(img, s, x, y, width=84):
    U.label(img, s, x, y, width)


def cell(sheet, k, cw, ch, cols=1, gap=2):
    return V.grid_cell(sheet, k, cw, ch, cols, gap)


def put(img, c, ox, oy, ax, ay, flip=False):
    V.put_cell(img, c, ox, oy, ax, ay, flip)


# ================================================================================================
def golem_gif(path):
    rel = "Content/Coghaven/NPCs/JadeGolem"
    r = U.ints(rel + "RigData.cs")
    c = S.consts("Content/Coghaven/Projectiles/JadeRay.cs", "Content/Coghaven/NPCs/JadeGolem.cs")
    far = S.darkened(S.load(rel + "_Far.png"), 0.88)
    mid, near, glow = S.load(rel + ".png"), S.load(rel + "_Near.png"), S.load(rel + "_Glow.png")
    arm, armg = S.load(rel + "_Arm.png"), S.load(rel + "_ArmGlow.png")
    nodes, orb = S.load("Content/Coghaven/Projectiles/JadeRay.png"), S.load("Content/Coghaven/Projectiles/JadeRay_Orb.png")
    cw, ch, cols = r["CellWidth"], r["CellHeight"], r["Columns"]
    Wd, Hd, floor = 520, 250, 228
    px, pchest = 70, floor - 40
    gx, dist = 470.0, 0.0
    walk, idle, charge, fire, recover = 150, 24, int(c["ChargeTicks"]), int(c["FireTicks"]), int(c["RecoverTicks"])
    lock = int(c["LockTicks"])
    aim = math.pi / 2
    frames = []
    total = walk + idle + charge + fire + recover + 20
    for t in range(total):
        img = U.backdrop(floor=floor, w=Wd, h=Hd)
        U.put_player(img, px, floor, 0, True)
        anchor = (gx, floor)
        shoulder = (gx + r["ShoulderX"], floor + r["ShoulderY"])
        goal = math.atan2(pchest - shoulder[1], abs(px - shoulder[0]))
        aiming = False
        phase = "walk"
        if t < walk:
            gx -= c["WalkSpeed"] * 1.4
            dist += c["WalkSpeed"] * 1.4
            k = r["Walk"] + int(dist // r["WalkStep"]) % r["WalkFrames"]
        elif t < walk + idle:
            phase = "idle"
            k = r["Idle"] + ((t - walk) // 15) % r["IdleFrames"]
        else:
            k = r["AimBody"]
            aiming = True
            tt = t - walk - idle
            if tt < charge - lock:
                phase = "charge"
                aim += max(-c["AimMaxTurn"], min(c["AimMaxTurn"], (goal - aim) * c["AimFollow"]))
            elif tt < charge:
                phase = "lock"
            elif tt < charge + fire:
                phase = "fire"
            else:
                phase = "recover"
                aim = min(math.pi / 2, aim + c["RecoverTurn"])
        if t % STEP:
            continue
        put(img, cell(far, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        put(img, cell(mid, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        lo = math.radians(r["ArmMinDegrees"])
        ak = max(0, min(r["ArmFrames"] - 1, round((math.degrees(aim) - r["ArmMinDegrees"]) / r["ArmStepDegrees"])))
        if aiming:
            put(img, cell(arm, ak, r["ArmCellWidth"], r["ArmCellHeight"], r["ArmColumns"]), r["ArmOriginX"], r["ArmOriginY"], *anchor)
        put(img, cell(near, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        put(img, cell(glow, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        if aiming:
            put(img, cell(armg, ak, r["ArmCellWidth"], r["ArmCellHeight"], r["ArmColumns"]), r["ArmOriginX"], r["ArmOriginY"], *anchor)
            reach = 62.0
            d = (-math.cos(aim), math.sin(aim))
            palm = (shoulder[0] + d[0] * reach, shoulder[1] + d[1] * reach)
            dot = cell(nodes, 0, 16, 16)
            if phase in ("charge", "lock"):
                alpha = 0.75 if phase == "lock" and (t // 3) % 2 == 0 else 0.3 if phase == "lock" else 0.22
                s = 14.0
                while s < 420:
                    q = (palm[0] + d[0] * s, palm[1] + d[1] * s)
                    if q[0] < 0 or q[1] > floor:
                        break
                    S.blit(img, S.faded(dot, alpha), int(q[0]) - 8, int(q[1]) - 8)
                    s += 14.0
                tt = t - walk - idle
                ok = min(4, int(tt / charge * 5))
                S.blit(img, cell(orb, ok, 24, 24), int(palm[0]) - 12, int(palm[1]) - 12)
            elif phase == "fire":
                tt = t - walk - idle - charge
                fade = 1.0 - tt / fire
                s = 0.0
                while s < 460:
                    q = (palm[0] + d[0] * s, palm[1] + d[1] * s)
                    if q[0] < 0 or q[1] > floor:
                        break
                    S.blit(img, S.faded(cell(nodes, (int(s / 6) + t) % 3, 16, 16), fade), int(q[0]) - 8, int(q[1]) - 8)
                    s += 6.0
        label(img, "JADE GOLEM v3, sideways (as vanilla's Ice Golem): emerald stone plates, a Moai head with one glowing eye, "
                   "rune bands, the core in his belt's disc", 6, 4)
        cap = {"walk": "walking: each planted foot stays put (the Jaeger's root motion)", "idle": "stops every 5 s",
               "charge": "aims (one of 37 arm frames), follows you, the charge gathers in his palm",
               "lock": "locked (the last 0.3 s): the aim line blinks", "fire": "the ray (the emerald glow)",
               "recover": "lowers his arm"}[phase]
        label(img, cap, 6, Hd - 18)
        frames.append(img)
    U.save_gif(frames, path, scale=1)


# ================================================================================================
def coin_gif(path):
    c = S.consts("Content/Research/Summons/JadeSpirit.cs")
    g = U.ints("Content/Coghaven/NPCs/JadeGolemRigData.cs")
    j = U.ints("Content/Bosses/Jadey/JadeyRigData.cs")
    coin = S.load("Content/Research/Summons/JadeSpirit_Coin.png")
    burst = S.load("Content/Research/Summons/JadeSpirit_Burst.png")
    bat = S.load("Content/Bosses/Jadey/NPCs/JadeBat.png")
    arm, armg = S.load("Content/Coghaven/NPCs/JadeGolem_Arm.png"), S.load("Content/Coghaven/NPCs/JadeGolem_ArmGlow.png")
    T, grace, bticks = int(c["TransformTicks"]), int(c["CoinGrace"]), int(c["BurstTicks"])
    Wp = 300
    frames = []
    state = [dict(morph=0.0, idle=999, shown=False, burst=0, x=0.0, y=0.0, aim=math.pi / 2) for _ in range(2)]
    for t in range(420):
        target = 90 <= t < 250
        img = Image.new("RGBA", (Wp * 2, 250), (0, 0, 0, 255))
        for side, form in enumerate(("bat", "arm")):
            st = state[side]
            band = U.backdrop(floor=FLOOR, w=Wp, h=250)
            px, feet = 90, FLOOR
            enemy = (230.0, FLOOR - 50 - 25 * math.sin(t / 30.0)) if target else None
            st["idle"] = 0 if target else st["idle"] + 1
            wanted = target or (st["morph"] > 0 and st["idle"] < grace)
            st["morph"] = max(0.0, min(T, st["morph"] + (1 if wanted else -1)))
            shown = st["morph"] >= T * 0.5
            if shown != st["shown"]:
                st["shown"] = shown
                st["burst"] = bticks
            home = (px, feet - 42 - c["CoinHeight"] + 3 * math.sin(t / 60.0 * 2.4))
            if st["morph"] <= 0 or t == 0:
                st["x"] += (home[0] - st["x"]) * 0.15 if t else home[0]
                st["y"] += (home[1] - st["y"]) * 0.15 if t else home[1]
            awake = st["morph"] >= T
            if awake and enemy:
                if form == "bat":
                    a = t / 14.0
                    goal = (enemy[0] + math.cos(a) * 40, enemy[1] + math.sin(a) * 18)
                    st["x"] += (goal[0] - st["x"]) * 0.12
                    st["y"] += (goal[1] - st["y"]) * 0.12
                else:
                    goal = (px + c["GolemGuard"], feet - 21 + c["GolemHeight"])
                    st["x"] += (goal[0] - st["x"]) * 0.1
                    st["y"] += (goal[1] - st["y"]) * 0.1
                    ang = math.atan2(enemy[1] - st["y"], abs(enemy[0] - st["x"]))
                    st["aim"] += max(-c["GolemTurn"], min(c["GolemTurn"], (ang - st["aim"]) * c["GolemFollow"]))
            if t % STEP:
                st["burst"] = max(0, st["burst"] - 1)
                continue
            U.put_player(band, px, feet, 0, True)
            if enemy:
                d = ImageDraw.Draw(band)
                d.rectangle([enemy[0] - 10, enemy[1] - 14, enemy[0] + 10, enemy[1] + 14], outline=(220, 220, 230, 255))
                label(band, "a target", int(enemy[0]) - 18, int(enemy[1]) - 28)
            x, y = st["x"], st["y"]
            if not st["shown"]:
                turn = max(1, int(c["CoinTurnTicks"]) - int(st["morph"])) if st["morph"] > 0 else int(c["CoinTurnTicks"])
                f = (t // turn) % int(c["CoinFrames"])
                S.blit(band, cell(coin, f, 32, 32), int(x) - 16, int(y) - 16)
            elif form == "bat":
                f = (t // 4) % j["BatFrames"]
                S.blit(band, S.mirror(cell(bat, f, j["BatWidth"], j["BatHeight"])), int(x) - j["BatWidth"] // 2, int(y) - j["BatHeight"] // 2)
            else:
                ak = max(0, min(g["ArmFrames"] - 1, round((math.degrees(st["aim"]) - g["ArmMinDegrees"]) / g["ArmStepDegrees"])))
                ax, ay = x - g["ShoulderX"] * -1, y - g["ShoulderY"]
                for sheet in (arm, armg):
                    put(band, cell(sheet, ak, g["ArmCellWidth"], g["ArmCellHeight"], g["ArmColumns"]), g["ArmOriginX"], g["ArmOriginY"],
                        ax, ay, True)
            if st["burst"] > 0:
                bf = min(4, (bticks - st["burst"]) * 5 // bticks)
                S.blit(band, cell(burst, bf, 48, 48), int(x) - 24, int(y) - 24)
            st["burst"] = max(0, st["burst"] - 1)
            label(band, "the bat" if form == "bat" else "the golem's arm", 6, 26)
            img.alpha_composite(band, (side * Wp, 0))
        if t % STEP:
            continue
        label(img, "JADE COIN: a coin over your head between fights; a target in range: it spins up and bursts into its creature "
                   "(0.23 s); 0.75 s after its last target it bursts back and floats home", 6, 4, 110)
        frames.append(img)
    U.save_gif(frames, path, scale=1)


# ================================================================================================
def lizard_sheets():
    rel = "Content/Underground/NPCs/CrystalLizard"
    r = U.ints(rel + "RigData.cs")
    return r, S.darkened(S.load(rel + "_Far.png"), 0.88), S.load(rel + ".png"), S.load(rel + "_Glow.png")


def draw_lizard(img, r, far, mid, glw, frame, gem, tailless, ax, ay, flip=False):
    cw, ch = r["CellWidth"], r["CellHeight"]
    put(img, cell(far, frame, cw, ch), r["OriginX"], r["OriginY"], ax, ay, flip)
    put(img, cell(mid, frame * r["MiddleColumns"] + gem + (r["GemCount"] if tailless else 0), cw, ch, r["MiddleColumns"]),
        r["OriginX"], r["OriginY"], ax, ay, flip)
    put(img, cell(glw, frame * r["GemCount"] + gem, cw, ch, r["GemCount"]), r["OriginX"], r["OriginY"], ax, ay, flip)


def lizard_gif(path):
    r, far, mid, glw = lizard_sheets()
    tail = S.load("Content/Underground/Gores/CrystalLizard_Tail.png")
    tc = S.consts("Content/Underground/Gores/CrystalLizardTail.cs")
    twitch, fadet = int(tc["TwitchTicks"]), int(tc["FadeTicks"])
    gem = 4                                                            # a ruby lizard
    Wd = 520
    x, dist = 420.0, 0.0
    tailless = False
    gore = None
    frames = []
    for t in range(330):
        img = U.cave_backdrop(floor=FLOOR, w=Wd, h=H)
        if t == 40:
            tailless = True
            join = (x + r["TailJoinX"], FLOOR + r["TailJoinY"])
            gore = dict(x=join[0] - r["TailBaseX"], y=join[1] - r["TailBaseY"], vx=1.2, vy=-2.2, age=0, alpha=0, row=0)
        if t < 200:
            x -= 3.2
            dist += 3.2
        if gore:
            gore["vy"] = min(gore["vy"] + 0.25, 9.0)
            gore["x"] += gore["vx"]
            gore["y"] += gore["vy"]
            ground = FLOOR - r["TailCellHeight"]
            grounded = gore["y"] >= ground
            if grounded:
                gore["y"] = ground
                gore["vy"] = 0.0
                gore["vx"] *= 0.8
            age = gore["age"]
            if age < twitch:
                period = 9 + age // 6
                strength = 3 if age < 90 else 2 if age < 170 else 1
                phase = age % period
                gore["row"] = phase + 1 if phase < strength else max(0, 2 * strength - phase - 1)
                if phase == 0 and strength == 3 and grounded and (age // period) % 2 == 0:
                    gore["vy"] = -1.6
                    gore["vx"] = 0.6 if (age // period) % 4 == 0 else -0.6
            else:
                gore["row"] = 0
                gore["alpha"] = min(255, (age - twitch) * 255 // fadet)
            gore["age"] += 1
        if t % STEP:
            continue
        if gore and gore["alpha"] < 255:
            g = cell(tail, gore["row"], r["TailCellWidth"], r["TailCellHeight"], 2)
            S.blit(img, S.faded(g, 1.0 - gore["alpha"] / 255.0), int(gore["x"]), int(gore["y"]))
        if x > -60:
            k = r["Run"] + int(dist // max(1, r["RunStep"])) % r["RunFrames"]
            draw_lizard(img, r, far, mid, glw, k, gem, tailless, x, FLOOR)
        if 40 <= t < 46:
            d = ImageDraw.Draw(img)
            d.text((x - 6, FLOOR - 70), "hit!", fill=(255, 230, 180, 255))
        label(img, "CRYSTAL LIZARD: a ruby lizard's crystals are rubies (its drop). Hit, it lets go of its tail: the tail lies "
                   "twitching, slower and weaker, the strong jerks a hop, 4 s, then fades", 6, 4)
        frames.append(img)
    U.save_gif(frames, path, scale=1)


def gems_png(path):
    r, far, mid, glw = lizard_sheets()
    names = ("amethyst", "topaz", "sapphire", "emerald", "ruby", "diamond", "amber", "jade")
    cw = 118
    img = Image.new("RGBA", (cw * 8 + 12, 300), (24, 26, 34, 255))
    for gem in range(8):
        for row, tailless in enumerate((False, True)):
            band = U.cave_backdrop(floor=70, w=cw - 6, h=86)
            draw_lizard(band, r, far, mid, glw, r["Idle"], gem, tailless, (cw - 6) // 2 - 6, 70)
            img.alpha_composite(band, (6 + gem * cw, 26 + row * 92))
        label(img, names[gem], 10 + gem * cw, 212)
    tail = S.load("Content/Underground/Gores/CrystalLizard_Tail.png")
    for k in range(4):
        S.blit(img, cell(tail, k, r["TailCellWidth"], r["TailCellHeight"], 2), 12 + k * 70, 240)
    label(img, "CRYSTAL LIZARD: its crystals are the gem it drops (with and without its tail), and the dropped tail's four curls",
          6, 4, 120)
    img.save(path)
    print("wrote", path)


# ================================================================================================
def scorpion_png(path):
    rel = "Content/Coghaven/NPCs/Cogscorpion"
    import re
    old_text = V.head_text(rel + "RigData.cs")
    ro = {k: int(v) for k, v in re.findall(r"\b(\w+) = (-?\d+)\b", old_text)}
    rn = U.ints(rel + "RigData.cs")
    img = U.cave_backdrop(floor=180, w=520, h=220)
    for col, (planes, r, name) in enumerate(((
            [S.darkened(V.head_png(rel + "_Far.png"), 0.88), V.head_png(rel + ".png"), V.head_png(rel + "_Near.png")], ro, "BEFORE: 380 life"),
            ([S.darkened(S.load(rel + "_Far.png"), 0.88), S.load(rel + ".png"), S.load(rel + "_Near.png")], rn, "AFTER: 85% of its size, 320 life"))):
        ax = 150 + col * 250
        for p in planes:
            put(img, cell(p, 0, r["CellWidth"], r["CellHeight"]), r["OriginX"], r["OriginY"], ax, 180)
        U.put_player(img, ax - 90, 180, 0, True)
        label(img, name, ax - 110, 30)
    label(img, "COGSCORPION beside the player, before and after (user: 'decrease a bit the size and health')", 6, 4)
    img.save(path)
    print("wrote", path)


def scorpion_gif(path):
    rel = "Content/Coghaven/NPCs/Cogscorpion"
    r = U.ints(rel + "RigData.cs")
    planes = [S.darkened(S.load(rel + "_Far.png"), 0.88), S.load(rel + ".png"), S.load(rel + "_Near.png"), S.load(rel + "_Glow.png")]
    frames = []
    for t in range(0, 240, STEP):
        dist = t * 1.5
        img = U.cave_backdrop(floor=FLOOR, w=W, h=H, scroll=-dist)
        k = r["Walk"] + int(dist // r["WalkStep"]) % r["WalkFrames"]
        for p in planes:
            put(img, cell(p, k, r["CellWidth"], r["CellHeight"]), r["OriginX"], r["OriginY"], W // 2, FLOOR)
        U.put_player(img, W // 2 - 110, FLOOR, 0, True)
        label(img, "COGSCORPION at 85% of its size: its walk (the planted feet stay put), the player for scale", 6, 4)
        frames.append(img)
    U.save_gif(frames, path)


# ================================================================================================
def slowmo_gif(path):
    c = S.consts("Core/Systems/SlowMotion.cs")
    k = S.consts("Core/Combat/CritKillSlowMotion.cs")
    bolt = S.load("Content/Gems/Projectiles/JadeBolt.png")
    bolt = bolt.crop(bolt.getchannel("A").getbbox() or (0, 0, bolt.width, bolt.height))
    total_new, ease_in, ease_out, slow = int(k["Ticks"]), int(c["EaseInTicks"]), int(c["EaseOutTicks"]), c["ZoneSpeed"]

    def speed_new(tick):
        if tick >= total_new:
            return 1.0
        e_in, e_out = min(ease_in, total_new // 3), min(ease_out, total_new - min(ease_in, total_new // 3))
        if tick < e_in:
            u = 1.0 - (tick + 1.0) / (e_in + 1.0)
        elif tick >= total_new - e_out:
            u = (tick - (total_new - e_out) + 1.0) / (e_out + 1.0)
        else:
            return slow
        u = u * u * (3 - 2 * u)
        return slow + (1 - slow) * u

    def speed_old(tick):
        return slow if tick < 20 else 1.0

    start, v = 40, 3.0
    runs = {}
    for name, fn, glide in (("old", speed_old, False), ("new", speed_new, True)):
        pos, acc, step, drawn, speeds = 20.0, 0.0, v, [], []
        for t in range(170):
            zone = t >= start and (t - start) < (20 if name == "old" else total_new)
            if zone:
                sp = fn(t - start)
                acc += sp
                upd = acc >= 1.0
                if upd:
                    acc -= 1.0
            else:
                sp, upd, acc = 1.0, True, 0.0
            if upd:
                pos += v
            speeds.append(sp)
            drawn.append(pos + (step * acc if glide and zone else 0.0))
        runs[name] = (drawn, speeds)
    frames = []
    for t in range(0, 170, 2):
        img = Image.new("RGBA", (W, 300), (18, 20, 30, 255))
        for row, (name, title) in enumerate((("old", "BEFORE: 0.33 s; one update in five (a shutter), then full speed at once"),
                                             ("new", "AFTER: 0.7 s; eased down, gliding between its updates, eased back up"))):
            y0 = 26 + row * 136
            band = U.backdrop(floor=70, w=W, h=80)
            drawn, speeds = runs[name]
            S.blit(band, bolt, int(drawn[t]) - bolt.width // 2, 40 - bolt.height // 2)
            if t >= start:
                label(band, "crit kill", 4, 60)
            img.alpha_composite(band, (0, y0))
            d = ImageDraw.Draw(img)
            gy = y0 + 84
            d.rectangle([0, gy, W, gy + 40], fill=(10, 12, 18, 255))
            for i in range(1, min(t + 1, len(speeds))):
                x0, x1 = (i - 1) * W / 170.0, i * W / 170.0
                d.line([(x0, gy + 38 - speeds[i - 1] * 34), (x1, gy + 38 - speeds[i] * 34)], fill=(126, 230, 160, 255), width=2)
            d.line([(t * W / 170.0, gy), (t * W / 170.0, gy + 40)], fill=(255, 211, 92, 255))
            label(img, title, 6, y0 - 22)
            label(img, "speed", W - 40, gy + 2)
        frames.append(img)
    U.save_gif(frames, path, ms=33, scale=1)


# ================================================================================================
def items_png(path):
    img = Image.new("RGBA", (640, 300), (24, 26, 34, 255))
    x = 16
    for rel, name in (("Content/Junkyard/Items/Cogfish.png", "Cogfish"), ("Content/Junkyard/Items/TarImmunityPotion.png", "Tar Immunity Potion"),
                      ("Content/Junkyard/Buffs/TarImmunity.png", "Tar Immunity (buff)")):
        im = S.load(rel)
        big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        S.blit(img, big, x, 40)
        label(img, name, x, 110, 22)
        x += max(big.width, 90) + 30
    for rel, name in (("Content/Banners/Items/JadeGolemBanner.png", "Jade Golem"), ("Content/Banners/Items/CogscorpionBanner.png", "Cogscorpion"),
                      ("Content/Banners/Items/CrystalLizardBanner.png", "Crystal Lizard")):
        im = S.load(rel)
        big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        S.blit(img, big, x, 24)
        label(img, name, x - 10, 130, 16)
        x += 70
    glaive = S.load("Content/Bosses/Jadey/Weapons/JadeCursedGlaives.png")
    S.blit(img, glaive, 16, 170)
    d = ImageDraw.Draw(img)
    tx = 32 + glaive.width
    d.rectangle([tx - 6, 160, tx + 330, 290], fill=(30, 34, 60, 255), outline=(70, 80, 130, 255))
    lines = (("Jade Cursed Glaives", (255, 211, 92)), ("Artifact: one per world", (126, 230, 160)), ("35 melee damage", (230, 230, 230)),
             ("12% critical strike chance", (230, 230, 230)), ("1% from an enemy killed while turned to jade", (190, 190, 200)),
             ("never combined, never stolen, a knowledge point", (190, 190, 200)), ("on the first pickup", (190, 190, 200)))
    for i, (s, col) in enumerate(lines):
        d.text((tx, 166 + i * 17), s, fill=col + (255,))
    label(img, "0.2.0: the Cogfish and the Tar Immunity Potion, the three redrawn banners, the glaives as an artifact (tooltip mock)",
          6, 4, 110)
    img.save(path)
    print("wrote", path)


def research_png(path):
    frames = S.load("Content/Research/UI/ResearchNode.png")
    img = Image.new("RGBA", (760, 380), (18, 16, 30, 255))
    d = ImageDraw.Draw(img)

    def node(cx, cy, state, text, sub, teaser=False):
        f = frames.crop((0, state * 58, 56, state * 58 + 56))
        S.blit(img, f, cx - 28, cy - 28)
        if teaser:
            d.text((cx - 4, cy - 8), "?", fill=(138, 144, 150, 255))
        else:
            d.text((cx - 22, cy - 6), text[:8], fill=(238, 241, 243, 255))
        label(img, sub, cx - 54, cy + 32, 22)

    # the main tab: the row under The Basics and the new row under it (secrets go beside or below the arch)
    d.text((20, 30), "Ancient Research (main tab): the new secrets, as question marks and revealed", fill=(223, 185, 78, 255))
    node(120, 110, 0, "", "Passive Income: '?' until a piggy bank opens", teaser=True)
    node(250, 110, 1, "Piggy", "revealed: 1 point, a copper coin a second")
    node(400, 110, 0, "", "Twinkling: '?' until a Crystal Lizard dies", teaser=True)
    node(530, 110, 1, "Diamond", "revealed: 1 point, rarer gems, +1-3 gold")
    node(120, 250, 0, "", "You Broke It!: '?' until a reforge", teaser=True)
    node(250, 250, 1, "Tinker", "revealed: 30 Rusted Cogs, -40% on a bad one")
    node(400, 250, 2, "Tinker", "researched: shows its child")
    node(530, 250, 1, "Toolbox", "Build Terraria 2: 1 point, fewer bad rolls")
    d.line([(430, 250), (500, 250)], fill=(223, 185, 78, 255), width=2)
    # the Artifacts tab
    d.rectangle([600, 40, 750, 340], fill=(12, 26, 22, 255), outline=(126, 230, 160, 255))
    d.text((612, 48), "Artifacts tab", fill=(126, 230, 160, 255))
    f = frames.crop((0, 2 * 58, 56, 2 * 58 + 56))
    S.blit(img, f, 647, 110)
    glaive = S.load("Content/Bosses/Jadey/Weapons/JadeCursedGlaives.png")
    g = glaive.resize((glaive.width // 3, glaive.height // 3), Image.NEAREST)
    S.blit(img, g, 675 - g.width // 2, 138 - g.height // 2)
    label(img, "the glaives' record, lit once found; '?' until then", 606, 180, 22)
    img.save(path)
    print("wrote", path)


SCENES = {
    "golem": ("mob-jade-golem-v3.gif", golem_gif),
    "coin": ("summon-jade-coin-transform.gif", coin_gif),
    "lizard": ("mob-crystal-lizard-tail.gif", lizard_gif),
    "gems": ("mob-crystal-lizard-gems.png", gems_png),
    "scorpion": ("coghaven-cogscorpion-size.png", scorpion_png),
    "scorpionwalk": ("coghaven-cogscorpion-walk.gif", scorpion_gif),
    "slowmo": ("combat-slowmo-smooth.gif", slowmo_gif),
    "items": ("items-0.2.0.png", items_png),
    "research": ("research-nodes-artifacts.png", research_png),
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
