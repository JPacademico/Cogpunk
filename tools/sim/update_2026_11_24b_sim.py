"""D5 proofs for the second request of 2026-11-24. Run from the repo root:

    python -P tools/sim/update_2026_11_24b_sim.py [--out docs/media] [--only coin,script,stones,reading]

Offline replays with the real sprites and the C# constants (read from the source files). Leaves out: lighting, tiles,
netcode and vanilla's own sprites (the player is the sims' armour mannequin, the target a stand-in dummy).

    coin     the Jade Coin (a GIF): five uses, 60 ticks a second, 4 ticks a GIF frame: a jade bat darting through a target
             dummy (JadeSpirit's cycle: hover BatHover px beside it, dash BatDashSpeed for the last BatDash ticks), the second
             use evolving it into the jade beetle (its flight frames, rams), the third into the floating jade golem (its arm
             sheets following the target, a jade bolt every GolemCycle ticks), the fourth into the jade loong (32 heading
             frames, the head turning at most LoongTurn a tick, the segments LoongSpacing apart), the fifth calling a second
             bat; each hit's damage the coin's 10 x FormDamage (4% crits).
    script   the Ghedalari script (a PNG): every word's rune and pictogram with its meaning; the stones' readings as the
             reading panel draws them, untranslated and translated; the Last Ghedalari's phrases as his chat box shows them.
    stones   the Fundamental Stones asleep (blue cuts) and awake (gold), every style (a PNG).
    reading  Westworld's stone (a GIF, tools/sim/update_2026_11_10_sim.py's street): read untranslated (runes), read again
             after its sigil is researched (pictograms), a Honeyfin dropped beside it (a stand-in fish) taken at the server's
             next look (ScanTicks), the stone waking gold.
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
SPIRIT = "Content/Research/Summons/JadeSpirit.cs"


def label(img, s, x, y, size=9):
    L.label(img, s, x, y, size)


def save_gif(frames, path, ms=66):
    L.save_gif(frames, path, ms)


def float_array(rel, name):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    m = re.search(r"static readonly float\[\] " + name + r" = \{([^}]*)\};", src)
    return [float(v.strip().rstrip("f")) for v in m.group(1).split(",") if v.strip()]


def int_array(rel, name):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    m = re.search(r"\b" + name + r" = \{([^}]*)\}", src)        # also the second of a pair declared together
    return [int(v) for v in m.group(1).split(",") if v.strip()]


def cell(sheet, frame, columns, cw, ch, pad=2):
    col, row = frame % columns, frame // columns
    return sheet.crop((col * (cw + pad), row * (ch + pad), col * (cw + pad) + cw, row * (ch + pad) + ch))


def put_cell(img, im, anchor, ox, oy, cw, flip):
    """DepthLayers.DrawCell's placement: the rig origin on the anchor, mirrored about it."""
    left = anchor[0] - (cw - ox) if flip else anchor[0] - ox
    S.blit(img, S.mirror(im) if flip else im, int(round(left)), int(round(anchor[1] - oy)))


def bands(w, h, floor):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    cols = ((21, 22, 28), (28, 28, 38), (36, 34, 48), (46, 42, 58))
    for k, col in enumerate(cols):
        d.rectangle([0, floor * k // len(cols), w, floor * (k + 1) // len(cols)], fill=col + (255,))
    d.rectangle([0, floor, w, h], fill=(74, 62, 50, 255))
    for x in range(0, w, 16):
        d.rectangle([x, floor, x + 15, floor + 1], fill=(112, 94, 72, 255))
    return img


# ================================================================================================
# The Jade Coin
# ================================================================================================
class Spirit:
    def __init__(self, index, pos):
        self.index = index
        self.pos = list(pos)
        self.vel = [0.0, 0.0]
        self.cycle = 0
        self.form = 0
        self.dir = -1
        self.friendly = False
        self.aim = math.pi / 2
        self.segments = None
        self.cool = 0
        self.burst = -99


def coin_gif(path):
    k = S.consts(SPIRIT, "Content/Research/Summons/JadeCoin.cs")
    fd = float_array(SPIRIT, "FormDamage")
    cool = int_array(SPIRIT, "FormCooldown")
    fw, fh = int_array(SPIRIT, "FormWidth"), int_array(SPIRIT, "FormHeight")
    jr = S.consts("Content/Bosses/Jadey/JadeyRigData.cs")
    br = S.consts("Content/Jungle/NPCs/RhinoBeetleRigData.cs")
    gr = S.consts("Content/Coghaven/NPCs/JadeGolemRigData.cs")
    bat = S.load("Content/Bosses/Jadey/NPCs/JadeBat.png")
    bat_glow = S.load("Content/Bosses/Jadey/NPCs/JadeBat_Glow.png")
    beetle = [S.load("Content/Bosses/Jadey/NPCs/JadeBeetle%s.png" % s) for s in ("_Far", "", "_Near")]
    beetle_glow = S.load("Content/Bosses/Jadey/NPCs/JadeBeetle_Glow.png")
    golem = [S.load("Content/Coghaven/NPCs/JadeGolem%s.png" % s) for s in ("_Far", "")]
    golem_near = S.load("Content/Coghaven/NPCs/JadeGolem_Near.png")
    golem_glow = S.load("Content/Coghaven/NPCs/JadeGolem_Glow.png")
    arm = S.load("Content/Coghaven/NPCs/JadeGolem_Arm.png")
    arm_glow = S.load("Content/Coghaven/NPCs/JadeGolem_ArmGlow.png")
    loong = S.load("Content/Research/Summons/JadeLoong.png")
    loong_glow = S.load("Content/Research/Summons/JadeLoong_Glow.png")
    bolt = S.load("Content/Gems/Projectiles/JadeBolt.png")
    W, H, floor = 600, 300, 268
    bg = bands(W, H, floor)
    px = 110
    owner = (px, floor - 21)
    target = [400, 150]                                  # a floating dummy (the forms all fly)
    tw, th = 32, 44
    uses = (0, 150, 300, 470, 690)
    total = 860
    rnd = random.Random(7)
    spirits = []
    bolts = []
    numbers = []
    flash = -99
    names = ("", "a jade bat", "a jade beetle", "a jade golem", "a jade loong")
    frames = []
    for tick in range(total):
        counters = sum(1 for u in uses if u <= tick)
        needed = min(int(k["MaxSpirits"]), (counters + 3) // 4)
        while len(spirits) < needed:
            spirits.append(Spirit(len(spirits), owner))
        trect = (target[0] - tw / 2, target[1] - th / 2, target[0] + tw / 2, target[1] + th / 2)
        for sp in spirits:
            form = max(0, min(4, counters - 4 * sp.index))
            if form != sp.form:
                sp.form = form
                sp.cycle = 0
                sp.segments = None
                sp.aim = math.pi / 2
                sp.burst = tick
            dmg = int(round(k["Damage"] * fd[form]))
            if sp.cool > 0:
                sp.cool -= 1

            def move_to(spot, speed, inertia):
                dx, dy = spot[0] - sp.pos[0], spot[1] - sp.pos[1]
                dist = math.hypot(dx, dy)
                if dist < 6:
                    sp.vel = [sp.vel[0] * 0.85, sp.vel[1] * 0.85]
                    return
                s = min(speed, dist / 6.0)
                sp.vel = [sp.vel[0] + (dx / dist * s - sp.vel[0]) * inertia, sp.vel[1] + (dy / dist * s - sp.vel[1]) * inertia]

            if form in (1, 2):
                cyc, dash, hover, lift, speed, dspeed = ((k["BatCycle"], k["BatDash"], k["BatHover"], -60, k["BatSpeed"], k["BatDashSpeed"])
                                                         if form == 1 else
                                                         (k["BeetleCycle"], k["BeetleRam"], k["BeetleBack"], -10, k["BeetleSpeed"], k["BeetleRamSpeed"]))
                sp.cycle = (sp.cycle + 1) % int(cyc)
                if sp.cycle < cyc - dash:
                    sp.friendly = False
                    side = -1 if sp.pos[0] < target[0] else 1
                    move_to((target[0] + side * hover, target[1] + lift), speed, 0.14)
                    sp.dir = 1 if target[0] > sp.pos[0] else -1
                else:
                    if sp.cycle == cyc - dash:
                        dx, dy = target[0] - sp.pos[0], target[1] - sp.pos[1]
                        d = math.hypot(dx, dy) or 1
                        sp.vel = [dx / d * dspeed, dy / d * dspeed]
                    sp.friendly = True
                    if abs(sp.vel[0]) > 0.4:
                        sp.dir = 1 if sp.vel[0] > 0 else -1
                sp.pos = [sp.pos[0] + sp.vel[0], sp.pos[1] + sp.vel[1]]
                w2, h2 = fw[form] / 2, fh[form] / 2
                if sp.friendly and sp.cool == 0 and sp.pos[0] + w2 > trect[0] and sp.pos[0] - w2 < trect[2] \
                        and sp.pos[1] + h2 > trect[1] and sp.pos[1] - h2 < trect[3]:
                    crit = rnd.random() < 0.04
                    numbers.append((tick, target[0], target[1] - 30, dmg * (2 if crit else 1), crit))
                    sp.cool = cool[form]
                    flash = tick
            elif form == 3:
                side = 1 if target[0] > owner[0] else -1
                bob = math.sin(tick / 60.0 * 1.6 + sp.index) * 4
                spot = (owner[0] + side * (k["GolemGuard"] + sp.index * k["IdleGap"]), owner[1] + k["GolemHeight"] + bob)
                move_to(spot, k["GolemSpeed"], 0.1)
                sp.pos = [sp.pos[0] + sp.vel[0], sp.pos[1] + sp.vel[1]]
                sp.dir = 1 if target[0] > sp.pos[0] else -1
                bottom = (sp.pos[0], sp.pos[1] + fh[3] / 2)
                shoulder = (bottom[0] + gr["ShoulderX"] * -sp.dir, bottom[1] + gr["ShoulderY"])
                vx, vy = target[0] - shoulder[0], target[1] - shoulder[1]
                lo = math.radians(gr["ArmMinDegrees"])
                hi = math.radians(gr["ArmMinDegrees"] + (gr["ArmFrames"] - 1) * gr["ArmStepDegrees"])
                goal = max(lo, min(hi, math.atan2(vy, abs(vx))))
                sp.aim += max(-k["GolemTurn"], min(k["GolemTurn"], (goal - sp.aim) * k["GolemFollow"]))
                sp.cycle = min(sp.cycle + 1, int(k["GolemCycle"]))
                if sp.cycle >= k["GolemCycle"] and abs(goal - sp.aim) < k["GolemAimError"]:
                    sp.cycle = 0
                    ax, ay = sp.dir * math.cos(sp.aim), math.sin(sp.aim)
                    palm = (shoulder[0] + ax * gr["PalmReach"], shoulder[1] + ay * gr["PalmReach"])
                    dx, dy = target[0] - palm[0], target[1] - palm[1]
                    d = math.hypot(dx, dy) or 1
                    bolts.append([palm[0], palm[1], dx / d * k["BoltSpeed"], dy / d * k["BoltSpeed"], 75, dmg])
            elif form == 4:
                if sp.segments is None:
                    hx, hy = sp.vel if math.hypot(*sp.vel) > 0.1 else (1.0, 0.0)
                    d = math.hypot(hx, hy)
                    sp.segments = [(sp.pos[0] - hx / d * k["LoongSpacing"] * i, sp.pos[1] - hy / d * k["LoongSpacing"] * i)
                                   for i in range(int(k["LoongSegments"]))]
                    if math.hypot(*sp.vel) < 2:
                        sp.vel = [k["LoongIdleSpeed"], -2.0]
                heading = math.atan2(sp.vel[1], sp.vel[0])
                want = math.atan2(target[1] - sp.pos[1], target[0] - sp.pos[0])
                delta = (want - heading + math.pi) % (2 * math.pi) - math.pi
                ang = heading + max(-k["LoongTurn"], min(k["LoongTurn"], delta))
                pace = math.hypot(*sp.vel)
                pace = pace + (k["LoongSpeed"] - pace) * 0.08
                sp.vel = [math.cos(ang) * max(pace, 2), math.sin(ang) * max(pace, 2)]
                sp.pos = [sp.pos[0] + sp.vel[0], sp.pos[1] + sp.vel[1]]
                segs = [tuple(sp.pos)]
                for i in range(1, int(k["LoongSegments"])):
                    px_, py_ = sp.segments[i]
                    fx, fy = segs[i - 1]
                    dx, dy = px_ - fx, py_ - fy
                    d = math.hypot(dx, dy) or 1
                    segs.append((fx + dx / d * k["LoongSpacing"], fy + dy / d * k["LoongSpacing"]))
                sp.segments = segs
                sp.dir = 1 if sp.vel[0] >= 0 else -1
                hit = any(trect[0] - k["LoongBite"] < x < trect[2] + k["LoongBite"] and trect[1] - k["LoongBite"] < y < trect[3] + k["LoongBite"]
                          for (x, y) in segs)
                if hit and sp.cool == 0:
                    crit = rnd.random() < 0.04
                    numbers.append((tick, target[0], target[1] - 30, dmg * (2 if crit else 1), crit))
                    sp.cool = cool[4]
                    flash = tick
        for b in bolts:
            b[0] += b[2]
            b[1] += b[3]
            b[4] -= 1
            if b[4] > 0 and trect[0] < b[0] < trect[2] and trect[1] < b[1] < trect[3]:
                crit = rnd.random() < 0.04
                numbers.append((tick, target[0], target[1] - 30, b[5] * (2 if crit else 1), crit))
                flash = tick
                b[4] = 0
        bolts = [b for b in bolts if b[4] > 0]
        if tick % 4:
            continue
        # --- draw ---
        img = bg.copy()
        v = S.View(W / 2, H / 2, zoom=1)
        v.img = img
        v.x0, v.y0 = 0, 0
        M.put_player(v, px, floor, frame=0)
        d = ImageDraw.Draw(img)
        hurt = tick - flash < 6
        x0, y0 = target[0] - tw / 2, target[1] - th / 2
        d.rectangle((x0, y0, x0 + tw, y0 + th), fill=(236, 122, 88) if hurt else (150, 116, 70), outline=(43, 26, 14))
        d.rectangle((x0 + 8, y0 + 6, x0 + tw - 8, y0 + 16), fill=(222, 180, 132), outline=(43, 26, 14))
        d.line((target[0], y0 + th, target[0], floor), fill=(90, 58, 23), width=2)
        for sp in spirits:
            form = sp.form
            if form == 1:
                f = (tick // int(k["BatFrameTicks"]) + sp.index) % int(jr["BatFrames"])
                im = bat.crop((0, f * (jr["BatHeight"] + 2), jr["BatWidth"], f * (jr["BatHeight"] + 2) + jr["BatHeight"]))
                gl = bat_glow.crop((0, f * (jr["BatHeight"] + 2), jr["BatWidth"], f * (jr["BatHeight"] + 2) + jr["BatHeight"]))
                flip = sp.dir == 1
                at = (int(sp.pos[0] - jr["BatWidth"] / 2) // 2 * 2, int(sp.pos[1] - jr["BatHeight"] / 2) // 2 * 2)
                S.blit(img, S.mirror(im) if flip else im, *at)
                S.blit_add(img, S.mirror(gl) if flip else gl, at[0], at[1], 1.0)
            elif form == 2:
                flap = int(k["BeetleRamFlap"] if sp.friendly else k["BeetleFlap"])
                f = int(br["Fly"]) + (tick // flap + sp.index) % int(br["FlyFrames"])
                anchor = (round(sp.pos[0] / 2) * 2, round((sp.pos[1] + fh[2] / 2) / 2) * 2)
                for plane in beetle:
                    put_cell(img, cell(plane, f, 1, br["CellWidth"], br["CellHeight"]), anchor, br["OriginX"], br["OriginY"], br["CellWidth"], sp.dir == 1)
                g = cell(beetle_glow, f, 1, br["CellWidth"], br["CellHeight"])
                left = anchor[0] - (br["CellWidth"] - br["OriginX"]) if sp.dir == 1 else anchor[0] - br["OriginX"]
                S.blit_add(img, S.mirror(g) if sp.dir == 1 else g, int(left), int(anchor[1] - br["OriginY"]), 1.0 if sp.friendly else 0.65)
            elif form == 3:
                anchor = (round(sp.pos[0] / 2) * 2, round((sp.pos[1] + fh[3] / 2) / 2) * 2)
                aiming = sp.aim < math.pi / 2 - 0.05
                f = int(gr["AimBody"]) if aiming else int(gr["Idle"]) + (tick // 15) % int(gr["IdleFrames"])
                flip = sp.dir == 1
                cols = int(gr["Columns"])
                for plane in golem:
                    put_cell(img, cell(plane, f, cols, gr["CellWidth"], gr["CellHeight"]), anchor, gr["OriginX"], gr["OriginY"], gr["CellWidth"], flip)
                a = max(0, min(int(gr["ArmFrames"]) - 1, int(round((math.degrees(sp.aim) - gr["ArmMinDegrees"]) / gr["ArmStepDegrees"]))))
                if aiming:
                    put_cell(img, cell(arm, a, int(gr["ArmColumns"]), gr["ArmCellWidth"], gr["ArmCellHeight"]), anchor, gr["ArmOriginX"],
                             gr["ArmOriginY"], gr["ArmCellWidth"], flip)
                put_cell(img, cell(golem_near, f, cols, gr["CellWidth"], gr["CellHeight"]), anchor, gr["OriginX"], gr["OriginY"], gr["CellWidth"], flip)
                g = cell(golem_glow, f, cols, gr["CellWidth"], gr["CellHeight"])
                left = anchor[0] - (gr["CellWidth"] - gr["OriginX"]) if flip else anchor[0] - gr["OriginX"]
                S.blit_add(img, S.mirror(g) if flip else g, int(left), int(anchor[1] - gr["OriginY"]), 0.8)
                if aiming:
                    ga = cell(arm_glow, a, int(gr["ArmColumns"]), gr["ArmCellWidth"], gr["ArmCellHeight"])
                    left = anchor[0] - (gr["ArmCellWidth"] - gr["ArmOriginX"]) if flip else anchor[0] - gr["ArmOriginX"]
                    S.blit_add(img, S.mirror(ga) if flip else ga, int(left), int(anchor[1] - gr["ArmOriginY"]), 0.8)
            elif form == 4 and sp.segments:
                n = int(k["LoongSegments"])
                for i in range(n - 1, -1, -1):
                    x, y = sp.segments[i]
                    fx, fy = (sp.vel if i == 0 else (sp.segments[i - 1][0] - x, sp.segments[i - 1][1] - y))
                    hd = int(round(math.atan2(fy, fx) / (2 * math.pi) * k["LoongHeadings"])) % int(k["LoongHeadings"])
                    kind = 0 if i == 0 else 3 if i == n - 1 else 2 if i in (2, 5) else 1
                    st, c = int(k["LoongStride"]), int(k["LoongCell"])
                    im = loong.crop((hd * st, kind * st, hd * st + c, kind * st + c))
                    at = (int(round((x - c / 2) / 2) * 2), int(round((y - c / 2) / 2) * 2))
                    S.blit(img, im, *at)
                    if i == 0:
                        S.blit_add(img, loong_glow.crop((hd * st, 0, hd * st + c, c)), at[0], at[1], 1.0)
            age = tick - sp.burst
            if 0 <= age < 24:                                # the change of form: a ring of jade
                r = 8 + age * 2.2
                for q in range(16):
                    a = q * math.tau / 16
                    bx, by = sp.pos[0] + math.cos(a) * r, sp.pos[1] + math.sin(a) * r
                    col = (118, 220, 162) if q % 2 else (196, 250, 214)
                    d.rectangle((int(bx) // 2 * 2, int(by) // 2 * 2, int(bx) // 2 * 2 + 1, int(by) // 2 * 2 + 1), fill=col)
        for b in bolts:
            S.blit_add(img, bolt, int(b[0] - bolt.width / 2), int(b[1] - bolt.height / 2), 1.0)
        for (at, nx, ny, val, crit) in numbers:
            M.number(v, nx, ny, val, tick - at, crit)
        counters = sum(1 for u in uses if u <= tick)
        forms = [max(0, min(4, counters - 4 * s.index)) for s in spirits]
        title = "JADE COIN: use %d of 5, %d slot%s" % (counters, counters, "" if counters == 1 else "s")
        label(img, title, 6, 6)
        label(img, " + ".join("%s (%d a hit)" % (names[f], int(round(k["Damage"] * fd[f]))) for f in forms if f), 6, 20)
        frames.append(img)
    save_gif(frames, path)


# ================================================================================================
# The Ghedalari script
# ================================================================================================
WORDS = ("dot", "rod", "arrow / towards", "lake / water", "bee", "Ghedalari", "one", "many", "not", "you", "eat", "happy", "gold",
         "stone", "sleep", "sun")


def script_png(path):
    k = S.consts("Content/Secrets/GhedalariScript.cs")
    glyphs = S.load("Content/Secrets/GhedalariGlyphs.png")
    sigils = S.load("Content/Secrets/FundamentalRunes.png")
    cw, ch, sx, sy = int(k["CellW"]), int(k["CellH"]), int(k["StrideX"]), int(k["StrideY"])
    sw, sh, ss = int(k["SigilW"]), int(k["SigilH"]), int(k["SigilStride"])
    src = open(os.path.join(ROOT, "Content/Secrets/GhedalariScript.cs"), encoding="utf-8").read()
    order = re.search(r"enum Word : byte \{([^}]*)\}", src).group(1).replace(" ", "").split(",")

    def rune(i, row=0):
        return glyphs.crop((i * sx, row * sy, i * sx + cw, row * sy + ch))

    def sigil(i):
        return sigils.crop((i * ss, 0, i * ss + sw, sh))

    def phrase(block):
        out = []
        for tok in re.findall(r"W\(Word\.(\w+)\)|\(short\)\(Sigil \+ (?:FundamentalStones\.)?(\w+)\)|(Gap)", block):
            word, sig, gap = tok
            if gap:
                out.append(("gap", 0))
            elif sig:
                out.append(("sigil", {"TarPit": 0, "Westworld": 1, "Ruins": 2, "3": 3, "4": 4}[sig]))
            else:
                out.append(("word", order.index(word)))
        return out

    blocks = re.search(r"Phrases = \{(.*?)\n\t\t\};", src, re.S).group(1)
    phrases = [phrase(b) for b in re.findall(r"new\[\] \{(.*?)\}", blocks, re.S)]
    phrases.append(phrase(re.search(r"WitchDoctorPhrase = \{(.*?)\};", src, re.S).group(1)))
    phrases.append(phrase(re.search(r"DryadPhrase = \{(.*?)\};", src, re.S).group(1)))
    meanings = ("Ghedalari: one ... many: not  (the last of his kind)",
                "you eat bee-water: happy  (honey; his people never knew it)",
                "Ghedalari eat gold: not happy  (he tried)",
                "stone sleep ... stone: not eat",
                "[sun] stone sleep ... you: rod, towards bee-water  (Westworld's stone wants a Honeyfin)",
                "sun > fleur > mountain > cross > wave  (the order the stones wake in)",
                "many you, towards one Ghedalari: happy  (with the Witch Doctor in town)",
                "stone: many suns ... Ghedalari: one  (with the Dryad in town)")
    Wd, Hd = 1000, 760
    img = Image.new("RGBA", (Wd, Hd), (24, 24, 32, 255))
    d = ImageDraw.Draw(img)
    label(img, "THE GHEDALARI SCRIPT: each word's rune (top) and the pictogram a translated stone shows (below), x2", 10, 8, 11)
    for i, name in enumerate(WORDS):
        col, row = i % 8, i // 8
        x, y = 14 + col * 122, 34 + row * 132
        d.rectangle((x - 4, y - 4, x + 110, y + 118), fill=(14, 20, 46, 255), outline=(46, 58, 100, 255))
        S.blit(img, rune(i).resize((cw * 2, ch * 2), Image.NEAREST), x + 4, y + 2)
        S.blit(img, rune(i, 1).resize((cw * 2, ch * 2), Image.NEAREST), x + 4, y + 52)
        label(img, name, x + 46, y + 40, 9)
    y = 306
    label(img, "THE STONES' READINGS (the panel over the stone; a reader who has researched its sigil sees the pictograms)", 10, y, 11)
    inscriptions = re.search(r"Inscriptions = \{(.*?)\n\t\t\};", src, re.S).group(1)
    lines = [re.findall(r"Word\.(\w+)", b) for b in re.findall(r"new\[\] \{([^}]*)\}", inscriptions)]
    for s_, (stone, name) in enumerate(((1, "Westworld (the sun): give it a Honeyfin"), (0, "the tar pit (the fleur): only '...', wakes when touched"))):
        words = [order.index(w) for w in lines[stone]]
        for t, row in enumerate((0, 1)):
            x = 14 + t * 330
            yy = y + 24 + s_ * 92
            wpan = len(words) * (cw + 4) - 4 + 24
            d.rectangle((x, yy, x + wpan * 2, yy + (ch + 24) * 2 - 8), fill=(14, 20, 46, 255), outline=(66, 86, 136, 255))
            for q, w in enumerate(words):
                S.blit(img, rune(w, row).resize((cw * 2, ch * 2), Image.NEAREST), x + 24 + q * (cw + 4) * 2, yy + 20)
            label(img, ("untranslated" if row == 0 else "translated"), x + 4, yy + 2, 8)
        label(img, name, 680, y + 46 + s_ * 92, 9)
    y = 512
    label(img, "THE LAST GHEDALARI'S CHAT (his lines are [ghd] tags: runes, and the stones' sigils by name)", 10, y, 11)
    for p, (ph, mean) in enumerate(zip(phrases, meanings)):
        yy = y + 22 + p * 28
        x = 14
        d.rectangle((x - 4, yy - 2, x + 470, yy + 24), fill=(33, 44, 92, 255))
        for kind, i in ph:
            if kind == "gap":
                x += 8
            elif kind == "sigil":
                S.blit(img, sigil(i), x, yy + 2)
                x += sw + 2
            else:
                S.blit(img, rune(i), x, yy + 1)
                x += cw + 2
        label(img, mean, 486, yy + 6, 8)
    img.save(path)
    print("wrote", path)


# ================================================================================================
# The stones asleep and awake
# ================================================================================================
def stones_png(path):
    tile = S.load("Content/Secrets/FundamentalStoneTile.png")
    glow = S.load("Content/Secrets/FundamentalStoneTile_Glow.png")
    awake = S.load("Content/Secrets/FundamentalStoneTile_Awake.png")
    names = ("fleur (tar pit)", "sun (Westworld)", "mountain (ruins)", "cross", "wave")

    def stone(style, cuts):
        out = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
        for ty in range(6):
            for tx in range(4):
                box = (style * 72 + tx * 18, ty * 18, style * 72 + tx * 18 + 16, ty * 18 + 16)
                out.alpha_composite(tile.crop(box), (tx * 16, ty * 16))
                out.alpha_composite(cuts.crop(box), (tx * 16, ty * 16))   # the game draws the cuts over the slate (PostDraw)
        return out

    img = Image.new("RGBA", (5 * 150 + 20, 2 * 230 + 50), (20, 22, 30, 255))
    label(img, "FUNDAMENTAL STONES: asleep (blue cuts, top) and awake in the puzzle's order (gold, bottom), x2", 10, 8, 11)
    for s in range(5):
        for r, cuts in enumerate((glow, awake)):
            S.blit(img, stone(s, cuts).resize((128, 192), Image.NEAREST), 20 + s * 150, 36 + r * 230)
        label(img, names[s], 20 + s * 150, 36 + 196, 8)
    img.save(path)
    print("wrote", path)


# ================================================================================================
# Westworld's stone: read, translated, woken by a Honeyfin
# ================================================================================================
def reading_gif(path, font="C:/Windows/Fonts/arialbd.ttf"):
    import update_2026_11_10_sim as U
    from old_brass_town_sim import stone_sprite
    west, at, _ = U.westworld_crop(margin=(30, 14))
    W, H = west.width, west.height
    gif = U.Gif(font, (W, H), scale=1.0)
    glyphs = S.load("Content/Secrets/GhedalariGlyphs.png")
    awake_cuts = S.load("Content/Secrets/FundamentalStoneTile_Awake.png")
    ka = S.consts("Content/Secrets/FundamentalStoneAwakening.cs")
    KS = U.KS
    gw, gh, gsx, gsy = U.GLYPH_W, U.GLYPH_H, U.GLYPH_STRIDE, 24
    line = U.INSCRIPTIONS[1]
    stone_x, stone_y = at
    floor = stone_y + 96
    anchor = (stone_x + 32, stone_y)
    base = stone_sprite(1, glow=False)
    gold = base.copy()
    for ty in range(6):
        for tx in range(4):
            fx, fy = (1 * 4 + tx) * 18, ty * 18
            gold.alpha_composite(awake_cuts.crop((fx, fy, fx + 16, fy + 16)), (tx * 16, ty * 16))
    px = float(W - 60)
    opened, age, closing, translated = None, 0, 0, False
    fish, fish_v, landed, taken, woke = None, None, None, None, None
    dust = []
    rnd = random.Random(3)
    notes = [(0, "Westworld's stone, its guardian beaten: right-click it to read it"),
             (95, "untranslated: Ghedalari runes (rod, arrow, lake, bee), one after another"),
             (235, "after researching the Sigil of the Sun (Mystery of the Past), read it again:"),
             (265, "translated: a fishing rod, an arrow to a lake and a bee (honey = 'bee-water')"),
             (400, "drop a Honeyfin next to it: the server takes it at its next look (every %d ticks)" % ka["ScanTicks"]),
             (470, "the sun stone is awake: its cuts glow gold (the first stone of the order)")]
    for tick in range(600):
        if tick < 80:
            px -= 1.6
        elif 385 <= tick < 405:
            px -= 2.0                                     # up to the stone to drop the fish
        if tick == 90 or tick == 250:
            opened, age, closing = True, 0, 0
            translated = tick == 250
        if tick == 215 or tick == 380:
            closing = max(closing, 1)
        if opened:
            age += 1
            if closing > 0:
                closing += 1
                if closing > KS["FadeOutTicks"]:
                    opened, closing = None, 0
        if tick == 410:                                   # the fish leaves the hand, tossed towards the stone
            fish, fish_v = [px - 14, floor - 34], [-2.2, -3.0]
        if fish and landed is None:
            fish_v[1] += 0.3
            fish[0] += fish_v[0]
            fish[1] += fish_v[1]
            if fish[1] >= floor - 8:
                fish[1] = floor - 8
                landed = tick
        if landed is not None and taken is None and tick % int(ka["ScanTicks"]) == 0:
            # the server's look (FundamentalStoneAwakening.StoneNear): a stone tile within FishReachX x FishReachY tiles of the fish
            cx, cy = int(fish[0] // 16), int(fish[1] // 16)
            sx0, sy0 = stone_x // 16, stone_y // 16
            near = any(abs(cx - (sx0 + i)) <= ka["FishReachX"] and abs(cy - (sy0 + j)) <= ka["FishReachY"]
                       for i in range(4) for j in range(6))
            assert near, "the fish landed out of the stone's reach"
            taken = woke = tick                           # the fish is taken, the stone wakes
            for _ in range(30):
                dust.append([anchor[0] + rnd.uniform(-28, 28), stone_y + rnd.uniform(0, 80), rnd.uniform(-1.2, 1.2), -rnd.uniform(0.5, 2.0), 40])
        for d in dust:
            d[0] += d[2]
            d[1] += d[3]
            d[4] -= 1
        dust = [d for d in dust if d[4] > 0]
        if tick % U.TPF:
            continue
        breath = 0.85 + 0.15 * math.sin(tick / 60.0 * 1.57 + 1.3)
        img = west.copy()
        if woke is not None:
            k = min(1.0, (tick - woke) / 20.0)
            img.alpha_composite(U.stone_image(1, breath * (1 - k)) if k < 1 else base, (stone_x, stone_y))
            img.alpha_composite(U.faded(gold, k * breath), (stone_x, stone_y))
        else:
            img.alpha_composite(U.stone_image(1, breath), (stone_x, stone_y))
        img.alpha_composite(U.player_sprite(flip=True), (int(px - 20), int(floor - 56)))
        dr = ImageDraw.Draw(img)
        if fish and taken is None:                        # a stand-in Honeyfin (vanilla's sprite isn't ours to copy)
            fx, fy = int(fish[0]), int(fish[1])
            dr.ellipse((fx - 7, fy - 4, fx + 5, fy + 4), fill=(236, 170, 40, 255), outline=(120, 70, 20, 255))
            dr.polygon([(fx + 5, fy), (fx + 10, fy - 4), (fx + 10, fy + 4)], fill=(236, 170, 40, 255), outline=(120, 70, 20, 255))
            dr.point((fx - 4, fy - 1), fill=(30, 20, 10, 255))
            gif.text(img, (fx - 30, fy - 22), "Honeyfin")
        for d in dust:
            dr.rectangle((int(d[0]) // 2 * 2, int(d[1]) // 2 * 2, int(d[0]) // 2 * 2 + 1, int(d[1]) // 2 * 2 + 1),
                         fill=(223, 185, 78, 255) if d[4] % 2 else (255, 250, 222, 255))
        if opened:
            alpha = min(1.0, age / KS["FadeInTicks"]) * (1.0 - closing / KS["FadeOutTicks"] if closing else 1.0)
            n = len(line)
            gap, pad = 4, 12
            pw, ph = n * gw + (n - 1) * gap + 2 * pad, gh + 2 * pad
            x0, y0 = int(anchor[0] - pw / 2), int(anchor[1] - 10 - ph)
            panel = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            pd = ImageDraw.Draw(panel)
            pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=6, fill=(14, 20, 46, int(230 * alpha)), outline=(60, 76, 130, int(230 * alpha)), width=2)
            img.alpha_composite(panel, (x0, y0))
            row = gsy if translated else 0
            for k, w in enumerate(line):
                shown = (age - KS["FadeInTicks"] / 2 - k * KS["RevealTicks"]) / KS["RevealTicks"]
                if shown <= 0:
                    break
                g = glyphs.crop((w * gsx, row, w * gsx + gw, row + gh))
                b = 1.0 if translated else breath
                img.alpha_composite(U.faded(g, alpha * min(1.0, shown) * b), (x0 + pad + k * (gw + gap), y0 + pad))
        U.note(gif, img, notes, tick)
        gif.push(img)
    gif.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    jobs = (("coin", coin_gif, "2026-11-24_summon-jade-coin.gif"),
            ("script", script_png, "2026-11-24_secrets-ghedalari-script.png"),
            ("stones", stones_png, "2026-11-24_secrets-stones-awake.png"),
            ("reading", reading_gif, "2026-11-24_secrets-westworld-stone.gif"))
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(a.out, file))


if __name__ == "__main__":
    main()
