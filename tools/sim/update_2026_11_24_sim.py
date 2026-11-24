"""D5 proofs for the request of 2026-11-24. Run from the repo root:

    python -P tools/sim/update_2026_11_24_sim.py [--out docs/media] [--only ghedalari,mount,refractor,glaive,research,items,scorpion]

Offline replays with the real sprites and the C# constants (read from the source files), 60 ticks a second, 3 ticks a GIF
frame (50 ms), shown at 2x. Leaves out: lighting, tile collision, netcode and vanilla's own sprites (the player is the sims'
armour mannequin; vanilla item icons in the research window are stand-ins; the javelin is a stand-in).

    ghedalari  the Last Ghedalari (Friendobo.png, vanilla's town frame rules): a walk across with the Guide's frame clock,
                 a blink, a word, a javelin thrown with frames 21-24; his shimmered form beside him.
    mount        Missing Bones: a run with the mount's frame clock (a frame every RunFrameDelay px), a leap (frame 9) into a
                 tar pool, the sink (SinkSpeed, halved by vanilla's water) to the floor, a walk on it, the paddle up
                 (RiseSpeed) and out; the rider on its hips at RiderOffset with the art's bob.
    refractor    the Jade Refractor held at a line of three dummies: the beam re-aimed at the cursor (AimFollow a tick), a hit
                 on each every HitInterval ticks, a curse stack on the first hit and every CurseEvery-th, jade after three,
                 x1.5 while jade; the beam's shimmer frames and the sparks.
    glaive       the Jade Cursed Glaives (tools/sim/jadey_loot_sim.py's replay, now with the 2026-11-24 throw: 22 tiles, two
                 turns a tick and the fan's blur).
    research     the research window (a PNG): the tab strip, the main tree with the new nodes (teasers as question marks)
                 and the Mystery of the Past with its five sigils.
    items        the new sprites over dark and light backgrounds (a PNG).
    scorpion     the Cogscorpion's walk (its three planes): it only walks and touches now.
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
W, H = 480, 240


def save_gif(frames, path):
    L.save_gif(frames, path)


def bands(w, h, floor, cols=((21, 22, 28), (28, 28, 38), (36, 34, 48), (46, 42, 58)), ground=(74, 62, 50)):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    for k, col in enumerate(cols):
        d.rectangle([0, floor * k // len(cols), w, floor * (k + 1) // len(cols)], fill=col + (255,))
    d.rectangle([0, floor, w, h], fill=ground + (255,))
    for x in range(0, w, 16):
        d.rectangle([x, floor, x + 15, floor + 1], fill=(112, 94, 72, 255))
    return img


def label(img, s, x, y, size=9):
    L.label(img, s, x, y, size)


def cells(path, cw, ch, n, gap=0):
    sh = S.load(path)
    return [sh.crop((0, k * (ch + gap), cw, k * (ch + gap) + ch)) for k in range(n)]


# ================================================================================================
# The Last Ghedalari
# ================================================================================================
def ghedalari_gif(path):
    vw, vh = 240, 120                                     # a closer view than the others: a town NPC is small
    floor = 100
    bg = bands(vw, vh, floor)
    plain = cells("Content/Town/Friendobo.png", 40, 56, 25)
    shim = cells("Content/Town/Friendobo_Shimmer.png", 40, 56, 25)
    jav = Image.new("RGBA", (28, 4), (0, 0, 0, 0))
    jd = ImageDraw.Draw(jav)
    jd.rectangle([0, 1, 21, 2], fill=(146, 86, 42, 255))
    jd.rectangle([22, 0, 27, 3], fill=(183, 191, 202, 255))
    frames = []
    x, counter, frame = 170.0, 0.0, 2
    total = 330
    javelin = None
    for tick in range(total):
        img = bg.copy()
        if tick < 150:                                    # walking left, then back right (vanilla's town frame rule)
            vx = -1.0 if tick < 100 else 1.0
            x += vx
            counter += abs(vx) * 2 + 1
            if counter > 6:
                counter = 0
                frame = frame + 1 if frame < 15 else 2
            cur, flip = frame, vx > 0
        elif tick < 175:
            cur, flip = (20 if tick < 158 else 0), True
        elif tick < 215:
            cur, flip = (19 if (tick // 8) % 2 == 0 else 0), True
        elif tick < 247:
            cur, flip = 21 + min(3, (tick - 215) // 8), True
            if tick == 239:
                javelin = [x + 10, floor - 40, 11.0, -3.0]
        else:
            cur, flip = 0, True
        spr = plain[cur]
        S.blit(img, S.mirror(spr) if flip else spr, int(x) - 20, floor - 52)
        # the shimmered form, standing and blinking beside him
        sf = shim[20 if (tick // 50) % 4 == 3 and tick % 50 < 8 else 0]
        S.blit(img, sf, 196, floor - 52)
        if javelin is not None:
            javelin[0] += javelin[2]
            javelin[1] += javelin[3]
            javelin[3] += 0.18
            ang = math.atan2(javelin[3], javelin[2])
            r, piv = M.rotated(jav, ang, (14, 2))
            S.blit(img, r, int(javelin[0]) - piv[0], int(javelin[1]) - piv[1])
            if javelin[0] > vw + 40 or javelin[1] > floor:
                javelin = None
        label(img, "THE LAST GUEDALARIAN: walk, blink, talk, javelin", 4, 4)
        if tick % 3 == 0:
            frames.append(img.resize((vw * 2, vh * 2), Image.NEAREST))
    save_gif(frames, path)


def ghedalari_png(path):
    """The 25 frames, plain and shimmered, over dark and light."""
    plain = S.load("Content/Town/Friendobo.png")
    shim = S.load("Content/Town/Friendobo_Shimmer.png")
    cols = 13
    # two rows: the plain and the shimmered sheets over dark and light (4 bands of 2 rows)
    big = Image.new("RGBA", (40 * cols, 56 * 2 * 4), (0, 0, 0, 255))
    y = 0
    for sh in (plain, shim):
        for bg in ((36, 40, 48, 255), (150, 180, 210, 255)):
            band = Image.new("RGBA", (40 * cols, 56 * 2), bg)
            for k in range(25):
                band.alpha_composite(sh.crop((0, k * 56, 40, (k + 1) * 56)), ((k % cols) * 40, (k // cols) * 56))
            big.paste(band, (0, y))
            y += 56 * 2
    big.resize((big.width * 2, big.height * 2), Image.NEAREST).save(path)
    print("wrote", path)


# ================================================================================================
# Missing Bones
# ================================================================================================
def mount_gif(path):
    k = S.consts("Content/Research/Mounts/MissingBonesMount.cs")
    fw, fh, nf = int(k["FrameWidth"]), int(k["FrameHeight"]), int(k["Frames"])
    sheet = cells("Content/Research/Mounts/MissingBonesMount_Back.png", fw, fh, nf)
    bob = [0, 0, 2, 2, 0, 0, 2, 2, 0, 0]
    floor = 120
    pool_x0, pool_x1, pool_floor = 250, 470, 232
    bg = bands(W, H, floor)
    d = ImageDraw.Draw(bg)
    d.rectangle([pool_x0, floor - 2, pool_x1, pool_floor], fill=(47, 27, 20, 255))            # the tar (water drawn as tar)
    d.rectangle([pool_x0, floor - 2, pool_x1, floor + 1], fill=(91, 54, 38, 255))
    d.rectangle([pool_x0 - 6, floor, pool_x0 - 1, pool_floor + 4], fill=(79, 85, 98, 255))   # the pit's unbreakable walls
    d.rectangle([pool_x1 + 1, floor, pool_x1 + 6, pool_floor + 4], fill=(79, 85, 98, 255))
    d.rectangle([pool_x0, pool_floor + 1, pool_x1, pool_floor + 4], fill=(79, 85, 98, 255))
    sink = k["SinkSpeed"] / 2.0                       # velocities: vanilla's water moves the player at half
    rise = k["RiseSpeed"] / 2.0
    frames = []
    x, y, vy = 30.0, float(floor), 0.0
    travelled, frame = 0.0, 1
    phase = "run"
    for tick in range(420):
        img = bg.copy()
        speed = 0.0
        if phase == "run":
            speed = min(6.0, 2.0 + tick * 0.12)
            x += speed
            if x >= pool_x0 - 60:
                phase, vy = "leap", -6.0
        elif phase == "leap":
            speed = 5.0
            x += speed
            vy += 0.4
            y += vy
            if y >= floor and x > pool_x0:
                phase = "sink"
        elif phase == "sink":
            speed = 1.0
            x += speed
            y = min(pool_floor, y + sink)
            if y >= pool_floor:
                phase, t0 = "floor", tick
        elif phase == "floor":
            speed = 3.0
            x += speed
            if x >= pool_x1 - 110:
                phase = "rise"
        elif phase == "rise":
            speed = 1.0
            x += speed
            y -= rise
            if y <= floor - 30:
                phase, vy = "out", -2.0
        elif phase == "out":
            speed = 3.0
            x += speed
            vy += 0.4
            y = min(y + vy, floor - 30 + 200)
        travelled += speed
        if phase in ("leap", "out") or (phase == "rise"):
            frame = 9 if phase != "rise" else 1 + int(travelled / k["RunFrameDelay"] * 2) % 8
        elif speed > 0:
            frame = 1 + int(travelled / k["RunFrameDelay"]) % 8
        b = bob[frame]
        fx, fy = int(x) - fw // 2, int(y) - fh
        S.blit(img, sheet[frame], fx, fy)
        rider = M.player(0)
        S.blit(img, rider, int(x) - rider.width // 2, int(y) - int(k["RiderOffset"]) - b - rider.height + 2)
        if phase in ("sink", "floor", "rise") or (pool_x0 < x < pool_x1 and y > floor):
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            od.rectangle([pool_x0, floor, pool_x1, pool_floor], fill=(47, 27, 20, 110))
            img.alpha_composite(ov)
        label(img, "MISSING BONES: run %g / dash %g; no Tar Plague; it sinks in liquids and paddles up holding jump" % (k["RunSpeed"], k["DashSpeed"]), 6, 6)
        if phase in ("sink", "floor", "rise"):
            label(img, {"sink": "sinking", "floor": "walking the pit's floor", "rise": "paddling up"}[phase], 300, 22)
        if tick % 3 == 0:
            frames.append(img)
        if x > W + 60:
            break
    save_gif(frames, path)


# ================================================================================================
# The Jade Refractor
# ================================================================================================
def refractor_gif(path):
    kb = S.consts("Content/Research/Weapons/JadeRefractorBeam.cs", "Content/Research/Weapons/JadeRefractor.cs",
                  "Content/Mechanist/Weapons/DiamondCutterBeam.cs")
    gun = S.load("Content/Research/Weapons/JadeRefractor.png")
    beam = cells("Content/Research/Weapons/JadeRefractorBeam.png", 16, 6, 4, gap=2)
    spark = cells("Content/Research/Weapons/JadeRefractorSpark.png", 14, 14, 4, gap=2)
    floor = 200
    bg = bands(W, H, floor)
    px = 70
    hand = (px + 4, floor - 22)
    targets = [(250, floor), (320, floor), (390, floor)]
    stacks = [0, 0, 0]
    stone = [-1, -1, -1]
    ward = [-1, -1, -1]
    curse_count = [0, 0, 0]
    last_hit = [-99, -99, -99]
    numbers = []
    frames = []
    aim = math.radians(-35)
    for tick in range(300):
        img = bg.copy()
        v = S.View(W / 2, H / 2, zoom=1)
        v.img = img
        v.x0, v.y0 = 0, 0
        goal = math.radians(-35 + min(1.0, tick / 50.0) * 35 + (2.0 * math.sin(tick / 9.0) if tick >= 60 else 0.0))
        aim += (goal - aim) * kb["AimFollow"]
        d = (math.cos(aim), math.sin(aim))
        normal = (-d[1], d[0])
        start = (hand[0] + d[0] * kb.get("MuzzleX", 48) + normal[0] * -6, hand[1] + d[1] * 48 + normal[1] * -6)
        # the line: to the 3rd dummy it crosses, else 60 tiles
        length = 900.0
        crossed = []
        for i, (tx, ty) in enumerate(targets):
            rx0, ry0, rx1, ry1 = tx - 12, ty - 40, tx + 12, ty
            # slab test along the line
            tin, tout = -1e9, 1e9
            ok = True
            for s0, dd, lo, hi in ((start[0], d[0], rx0 - 3, rx1 + 3), (start[1], d[1], ry0 - 3, ry1 + 3)):
                if abs(dd) < 1e-5:
                    if not (lo <= s0 <= hi):
                        ok = False
                    continue
                a, b = (lo - s0) / dd, (hi - s0) / dd
                if a > b:
                    a, b = b, a
                tin, tout = max(tin, a), min(tout, b)
            if ok and tin <= tout and tout > 0:
                crossed.append((max(tin, 0), tout, i))
        crossed.sort()
        if len(crossed) >= 3:
            length = (crossed[2][0] + crossed[2][1]) / 2.0
        elif crossed:
            length = 900.0
        # the dummies
        for i, (tx, ty) in enumerate(targets):
            body = Image.new("RGBA", (24, 40), (0, 0, 0, 0))
            bd = ImageDraw.Draw(body)
            jade = tick < stone[i]
            col = (96, 214, 150, 255) if jade else (146, 86, 42, 255)
            bd.rectangle([8, 0, 15, 39], fill=col)
            bd.rectangle([0, 8, 23, 14], fill=col)
            bd.rectangle([4, 0, 19, 6], fill=(196, 180, 150, 255) if not jade else (140, 238, 128, 255))
            S.blit(img, body, tx - 12, ty - 40)
            if stacks[i] and not jade:
                label(img, "x%d" % stacks[i], tx - 8, ty - 54)
        # hits: every HitInterval ticks on each crossed dummy (the first three)
        for (tin, tout, i) in crossed[:3]:
            if tick - last_hit[i] >= kb["HitInterval"] and tick > 20:
                last_hit[i] = tick
                jade = tick < stone[i]
                dmg = int(round(kb["Damage"] * (kb["PetrifiedBonus"] if jade else 1.0)))
                numbers.append((tick, targets[i][0], targets[i][1] - 44, dmg, jade))
                n = curse_count[i]
                curse_count[i] = (n + 1) % int(kb["CurseEvery"])
                if n == 0 and not jade and tick >= ward[i]:
                    stacks[i] += 1
                    if stacks[i] >= 3:
                        stacks[i] = 0
                        stone[i] = tick + 150
                        ward[i] = tick + 600
        # the beam: its pieces with a shimmer running along it, the sparks
        ang = math.atan2(d[1], d[0])
        piece = 0
        t = 0.0
        f0 = tick // int(kb["BeamFrameTicks"])
        while t < length and t < 600:
            w = int(min(16, length - t))
            if w <= 0:
                break
            seg = beam[(f0 - piece) % 4].crop((0, 0, w, 6))
            r, piv = M.rotated(seg, ang, (0, 3))
            S.blit_add(img, r, int(start[0] + d[0] * t) - piv[0], int(start[1] + d[1] * t) - piv[1], 1.0)
            t += 16
            piece += 1
        sp = spark[(tick // int(kb["SparkFrameTicks"])) % 4]
        S.blit_add(img, sp, int(start[0]) - 7, int(start[1]) - 7)
        S.blit_add(img, sp, int(start[0] + d[0] * length) - 7, int(start[1] + d[1] * length) - 7)
        # the player and the refractor in the hand
        M.put_player(v, px, floor, frame=3)
        r, piv = M.rotated(gun, ang, (15, 21))
        S.blit(img, r, hand[0] - piv[0], hand[1] - piv[1])
        for (at, nx, ny, val, crit) in numbers:
            M.number(v, nx, ny, val, tick - at, crit)
        label(img, "JADE REFRACTOR: a held jade laser; %d a hit every %d ticks on the first 3 enemies; the jade curse; x1.5 on jade"
              % (kb["Damage"], kb["HitInterval"]), 6, 6)
        if tick % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


# ================================================================================================
# The research window
# ================================================================================================
ICON_FILES = {"BrassContainer": "Content/Mechanist/Accessories/BrassContainer.png", "TetanusShot": "Content/Bosses/TrashTr0m/Items/TetanusShot.png",
              "ScrapHelmet": "Content/Scrap/Armor/ScrapHelmet.png", "RustedCog": "Content/Scrap/Items/RustedCog.png",
              "Cakti": "Content/Desert/Weapons/Cakti.png", "BundleOfWands": "Content/Research/Weapons/BundleOfWands.png",
              "BanditsDream": "Content/Research/Weapons/BanditsDream.png", "SheriffsRevolver": "Content/OldBrassTown/Weapons/SheriffsRevolver.png",
              "CondensedTar": "Content/Junkyard/Items/CondensedTar.png", "MissingBones": "Content/Research/Mounts/MissingBones.png",
              "FishOnASpear": "Content/Research/Meals/FishOnASpear.png", "Jade": "Content/Gems/Items/Jade.png",
              "JadeRefractor": "Content/Research/Weapons/JadeRefractor.png", "TheCombinator": "Content/Combinator/Items/TheCombinator.png",
              "RainbowRobe": "Content/Research/Armor/RainbowRobe.png", "JadeCoin": "Content/Research/Summons/JadeCoin.png"}
STAND_COL = {"ItemID": (127, 135, 148)}


def stand_icon(colour):
    im = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, 15, 15], fill=colour + (255,))
    d.rectangle([4, 4, 15, 5], fill=tuple(min(255, c + 50) for c in colour) + (255,))
    return im


def fit(im, box=36):
    if im.width > box or im.height > box:
        k = max(im.width, im.height) / float(box)
        im = im.resize((max(1, int(im.width / k)), max(1, int(im.height / k))), Image.NEAREST)
    return im


def read_nodes():
    """[(name, tab, column, row, icon, teaser, glyph)] from ResearchNodes.cs: the Add blocks and the AddSigil calls."""
    src = open(os.path.join(ROOT, "Content/Research/ResearchNodes.cs"), encoding="utf-8").read()
    consts = dict(re.findall(r'(\w+) = "(\w+)"', src))
    out = []
    for block in re.findall(r"Add\(new ResearchNode \{(.*?)\n\t\t\t\}\);", src, re.S):
        m = re.search(r"Name = (\w+), Column = (-?\d+), Row = (-?\d+), Cost = (\d+), IconItem = ([^,\n]+),", block)
        if not m:
            continue
        icon_src = m.group(5).strip()
        mm = re.search(r"\.(\w+)>\(\)", icon_src)
        if mm and mm.group(1) in ICON_FILES:
            icon = S.load(ICON_FILES[mm.group(1)])
        else:
            h = abs(hash(icon_src)) % 6
            icon = stand_icon(((196, 104, 58), (127, 135, 148), (140, 201, 176), (168, 44, 42), (223, 185, 78), (96, 122, 172))[h])
        out.append((consts.get(m.group(1), m.group(1)), 0, int(m.group(2)), int(m.group(3)), fit(icon), "Teaser = true" in block, -1))
    stones = {"Fleur": 0, "Sun": 1, "Mountain": 2, "Cross": 3, "Wave": 4}
    for m in re.finditer(r"AddSigil\((\w+), FundamentalStonesIndex\.(\w+), (-?\d+), (-?\d+),", src):
        out.append((consts.get(m.group(1), m.group(1)), 1, int(m.group(3)), int(m.group(4)), None, True, stones[m.group(2)]))
    return out


def research_png(path):
    k = S.consts("Content/Research/UI/ResearchUIState.cs")
    sx, sy, ns, bm = k["SpacingX"], k["SpacingY"], int(k["NodeSize"]), k["BottomMargin"]
    frames_img = S.load("Content/Research/UI/ResearchNode.png")
    node_frames = [frames_img.crop((0, q * 58, 56, q * 58 + 56)) for q in range(3)]
    runes = S.load("Content/Secrets/FundamentalRunes.png")
    sign = S.load("Content/Research/UI/ResearchKnowledge.png")
    nodes = read_nodes()
    unlocked = {"TheBasics", "MineAndCraft", "Cogpunker", "Jogger", "AlchemyInitiate", "SigilFleur"}
    revealed = {"FulfillingConcoction", "Seasoning", "ProperMeal", "EfficientFuel", "Reconstructed", "SigilFleur", "SigilSun"}
    hidden_secrets = {"InACaveWithScraps", "HitTheJoints", "Mandacaru", "BringAKnife", "TriggerFinger", "GreenIsGood", "GreenDiamond"}
    panels = []
    for tab, title in ((0, "Ancient Research"), (1, "Mystery of the Past")):
        Wp, Hp = 1000, 640
        img = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, Wp - 1, Hp - 1], fill=(21, 22, 28, 255))
        d.rectangle([2, 2, Wp - 3, Hp - 3], fill=(90, 58, 23, 255))
        d.rectangle([4, 4, Wp - 5, Hp - 5], fill=(184, 138, 51, 255))
        d.rectangle([8, 8, Wp - 9, Hp - 9], fill=(21, 22, 28, 255))
        d.rectangle([10, 10, Wp - 11, Hp - 11], fill=(24, 20, 36, 255))
        S.blit(img, S.text("Ancient Research", 20, "plate", S.BRASS[4], S.BRASS[3], S.BRASS[0]), Wp // 2 - 90, 14)
        S.blit(img, sign, 28, 22)
        S.blit(img, S.text("3", 18, "plate", (140, 201, 176), (100, 160, 140), S.IRON[0]), 28 + sign.width + 8, 18)
        # the tab strip
        tx = 20
        for t, name in enumerate(("Ancient Research", "Mystery of the Past")):
            txt = S.text(name, 12, "plate", (128, 150, 238) if t == tab == 1 else S.BRASS[4] if t == tab else S.STEAM[0],
                         S.BRASS[3] if t == tab else S.STEAM[0], S.IRON[0])
            w = txt.width + 28
            d.rectangle([tx, 48, tx + w, 74], fill=(21, 22, 28, 255))
            d.rectangle([tx + 2, 50, tx + w - 2, 74], fill=((223, 185, 78) if t == tab else (90, 58, 23)) + (255,))
            d.rectangle([tx + 4, 52, tx + w - 4, 74], fill=((24, 20, 36) if t == tab else (21, 22, 28)) + (255,))
            S.blit(img, txt, tx + 14, 55)
            tx += w + 6
        fx0, fy0, fx1, fy1 = 20, 76, Wp - 20, Hp - 20
        d.rectangle([fx0, fy0, fx1, fy1], fill=((16, 22, 46) if tab == 1 else (18, 16, 30)) + (255,))
        rng = random.Random(1118)
        for _ in range(260):
            x, y, shade = fx0 + rng.randrange(fx1 - fx0), fy0 + rng.randrange(fy1 - fy0), rng.randrange(4)
            c = ((46, 50, 59), (70, 58, 147), (127, 135, 148), (198, 189, 255))[shade]
            d.rectangle([x, y, x + (3 if shade == 3 else 1), y + (3 if shade == 3 else 1)], fill=c + (255,))
        cx = (fx0 + fx1) / 2.0
        bottom = fy1 - bm - 10
        rects = {}
        for (name, t, c, r, icon, teaser, glyph) in nodes:
            if t != tab:
                continue
            if name in hidden_secrets:
                continue
            x = int(round(cx + c * sx * 0.66 - ns / 2))                    # squeezed to fit columns -5..5 (the game pans instead)
            y = int(round(bottom - r * sy * 0.82 - ns / 2))
            rects[name] = (x, y)
        # links (Alchemy Initiate -> Fulfilling Concoction sideways, Seasoning -> Proper Meal up)
        for a, b in (("AlchemyInitiate", "FulfillingConcoction"), ("Seasoning", "ProperMeal")):
            if a in rects and b in rects:
                (ax, ay), (bx, by) = rects[a], rects[b]
                if abs(ay - by) < 10:
                    p0, p2 = (ax, ay + ns / 2), (bx + ns, by + ns / 2)
                    p1 = ((p0[0] + p2[0]) / 2, p0[1] - abs(p2[0] - p0[0]) * 0.25)
                else:
                    p0, p2 = (ax + ns / 2, ay), (bx + ns / 2, by + ns)
                    p1 = ((p0[0] + p2[0]) / 2 + (p2[1] - p0[1]) * 0.25, (p0[1] + p2[1]) / 2)
                col = (223, 185, 78) if a in unlocked else (127, 135, 148)
                for s in range(41):
                    q = s / 40.0
                    x = (1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * p1[0] + q * q * p2[0]
                    y = (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * p1[1] + q * q * p2[1]
                    d.rectangle([int(x) & ~1, int(y) & ~1, (int(x) & ~1) + 1, (int(y) & ~1) + 1], fill=col + (255,))
        for (name, t, c, r, icon, teaser, glyph) in nodes:
            if name not in rects or t != tab:
                continue
            x, y = rects[name]
            shown = not teaser or name in revealed
            state = 2 if name in unlocked else (1 if shown and name in ("FulfillingConcoction", "Seasoning", "EfficientFuel", "SigilSun") else 0)
            img.alpha_composite(node_frames[state if shown else 0], (x, y))
            if not shown:
                S.blit(img, S.text("?", 26, "plate", (138, 144, 150), (110, 116, 122), S.IRON[0]), x + 20, y + 12)
                continue
            if glyph >= 0:
                g = runes.crop((glyph * 16, 0, glyph * 16 + 14, 18)).resize((28, 36), Image.NEAREST)
                img.alpha_composite(g, (x + 14, y + 10))
            else:
                ic = icon if state else S.darkened(icon, 0.55)
                img.alpha_composite(ic, (x + 28 - ic.width // 2, y + 28 - ic.height // 2))
        label(img, "the %s tab (sample states: researched gold, ready jade, locked grey; teasers as ?)" % title, 30, Hp - 40)
        panels.append(img)
    out = Image.new("RGBA", (panels[0].width, panels[0].height * 2 + 10), (0, 0, 0, 255))
    out.alpha_composite(panels[0], (0, 0))
    out.alpha_composite(panels[1], (0, panels[0].height + 10))
    out.save(path)
    print("wrote", path)


# ================================================================================================
# Items
# ================================================================================================
def items_png(path):
    files = ["Content/Gems/Items/JadeClaws.png", "Content/Research/Weapons/JadeRefractor.png", "Content/Research/Mounts/MissingBones.png",
             "Content/Research/Mounts/MissingBonesBuff.png", "Content/Research/Meals/BlueStarFruit.png", "Content/Research/Meals/FishOnASpear.png",
             "Content/Research/Meals/DeadeyeChili.png", "Content/Research/Meals/FireflyJelly.png", "Content/Research/Meals/BlueStarFruitBuff.png",
             "Content/Research/Meals/FishOnASpearBuff.png", "Content/Research/Meals/DeadeyeChiliBuff.png", "Content/Research/Meals/FireflyJellyBuff.png",
             "Content/Town/Friendobo_Head.png", "Content/Town/Friendobo_Shimmer_Head.png", "Content/Town/FriendoboEmote.png",
             # the second request of 2026-11-24: the Rainbow Robe, the Jade Coin and its buff
             "Content/Research/Armor/RainbowRobe.png", "Content/Research/Summons/JadeCoin.png", "Content/Research/Summons/JadeCoinBuff.png"]
    ims = [S.load(f) for f in files]
    scale, gap = 3, 10
    w = sum(im.width * scale + gap for im in ims) + gap
    h = max(im.height for im in ims) * scale + 2 * gap
    out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
    for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
        band = Image.new("RGBA", (w, h), bg + (255,))
        out.alpha_composite(band, (0, row * h))
        x = gap
        for im in ims:
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            out.alpha_composite(big, (x, row * h + gap))
            x += big.width + gap
    out.save(path)
    print("wrote", path)


# ================================================================================================
# The Cogscorpion
# ================================================================================================
def scorpion_gif(path):
    k = S.consts("Content/Coghaven/NPCs/CogscorpionRigData.cs")
    cw, ch, ox, oy = int(k["CellWidth"]), int(k["CellHeight"]), int(k["OriginX"]), int(k["OriginY"])
    planes = [S.load("Content/Coghaven/NPCs/Cogscorpion%s.png" % s) for s in ("_Far", "", "_Near")]
    glow = S.load("Content/Coghaven/NPCs/Cogscorpion_Glow.png")
    floor = 190
    bg = bands(W, H, floor)
    frames = []
    x = 420.0
    for tick in range(180):
        img = bg.copy()
        frame = int(k["Walk"]) + (tick // 6) % int(k["WalkFrames"])
        if tick % 6 == 0 and tick:
            x -= k["WalkStep"]
        for pl in planes:
            cell = pl.crop((0, frame * (ch + 2), cw, frame * (ch + 2) + ch))
            S.blit(img, cell, int(x) - ox, floor - oy)
        gcell = glow.crop((0, frame * (ch + 2), cw, frame * (ch + 2) + ch))
        S.blit_add(img, gcell, int(x) - ox, floor - oy, 0.8)
        label(img, "COGSCORPION: it walks at you and hurts by touch only (the tail strike is gone)", 6, 6)
        if tick % 3 == 0:
            frames.append(img)
    save_gif(frames, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    jobs = (("ghedalari", ghedalari_gif, "2026-11-24_town-last-ghedalari.gif"),
            ("ghedalari", ghedalari_png, "2026-11-24_town-last-ghedalari-frames.png"),
            ("mount", mount_gif, "2026-11-24_mount-missing-bones.gif"),
            ("refractor", refractor_gif, "2026-11-24_weapon-jade-refractor.gif"),
            ("glaive", L.glaives_gif, "2026-11-24_jadey-glaives.gif"),
            ("research", research_png, "2026-11-24_research-tabs.png"),
            ("items", items_png, "2026-11-24_items-research-batch.png"),
            ("scorpion", scorpion_gif, "2026-11-24_coghaven-cogscorpion-walk.gif"))
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(a.out, file))


if __name__ == "__main__":
    main()
