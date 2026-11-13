"""D5 proofs for the 2026-11-12 request. Run from the repo root:

    python -P tools/sim/update_2026_11_12_sim.py --out docs/media [--only island,scorpion,buddha,combinator,blueprint,station,rocket,items]

Every scene uses the real sprites (Content/...) and the code's own constants (parsed from the C# files), replayed tick by
tick (60 ticks = 1 s). Leaves out: lighting, vanilla's art (players, terrain and Terraria's font are stand-ins), dust (drawn
as a few palette pixels where it matters), netcode.

Writes (docs/media/):
    2026-11-12_coghaven-island-chests.png    the island (coghaven_sim's replay of the pass): the two chests, the 14x6 koi pond
    2026-11-12_coghaven-cogscorpion.gif      walk, the 36-tick tail raise, the strike with the sting's hitbox, the recovery
    2026-11-12_coghaven-buddha-head.gif      float, wrath (45 ticks), the plunge, the quake, 2 s stunned with stars, the rise
    2026-11-12_combinator-station.gif        the station's 4-frame animation (cog, furnace) and the Blueprint's beam and aura
    2026-11-12_combinator-window.png         the window (real UI art) with a combination, the help tip, and combined sprites
                                             made by a port of CombinedSprites (our own weapons: vanilla's art isn't in the repo)
    2026-11-12_mechanist-rocket-boots.gif    Rocket Boots on steam: 2 steam every 6 ticks of thrust, the tank as the limit
    2026-11-12_items-steam-injector-koi.png  the Steam Injector (tile, item, buff icon), the Koi, the Combinator's parts
"""
import argparse
import math
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

FONT = "C:/Windows/Fonts/arialbd.ttf"
BG_SKY = (150, 182, 214, 255)
BG_DARK = (30, 30, 40, 255)


def load(rel):
    return Image.open(os.path.join(ROOT, rel)).convert("RGBA")


def consts(rel, ctx=None):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    out = dict(ctx or {})
    for m in re.finditer(r"const (?:int|float|double) ([^;]+);", src):
        for part in m.group(1).split(","):
            if "=" in part:
                k, v = (x.strip() for x in part.split("=", 1))
                v = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
                v = re.sub(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", r"\1", v)
                try:
                    out[k] = eval(v, {}, dict(out))
                except Exception:
                    pass
    return out


def font(size):
    return ImageFont.truetype(FONT, size)


def text(img, xy, s, size=14, fill=(238, 241, 243)):
    d = ImageDraw.Draw(img)
    f = font(size)
    for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        d.text((xy[0] + ox, xy[1] + oy), s, fill=(21, 22, 28), font=f)
    d.text(xy, s, fill=fill, font=f)


def save_gif(frames, path, ms):
    pal = [f.convert("RGB").quantize(colors=200, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=True, disposal=1)
    print("%s: %d frames, %.2f MB" % (path, len(frames), os.path.getsize(path) / 1e6))


class Grid:
    """A GridWalkerNPC's sheets: equal cells of w x h game px with 2 px under each, origin (ox, oy); far, middle, near, glow."""

    def __init__(self, base, rig):
        r = consts(rig)
        self.w, self.h, self.ox, self.oy = r["CellWidth"], r["CellHeight"], r["OriginX"], r["OriginY"]
        self.r = r
        self.sheets = []
        for suffix in ("_Far", "", "_Near"):
            p = base + suffix + ".png"
            self.sheets.append(load(p) if os.path.exists(os.path.join(ROOT, p)) else None)
        g = base + "_Glow.png"
        self.glow = load(g) if os.path.exists(os.path.join(ROOT, g)) else None

    def cell(self, sheet, k):
        return sheet.crop((0, k * (self.h + 2), self.w, k * (self.h + 2) + self.h))

    def draw(self, img, k, anchor, flip=False, glow=1.0):
        for sheet in self.sheets + ([self.glow] if self.glow is not None and glow > 0 else []):
            if sheet is None:
                continue
            c = self.cell(sheet, k)
            if flip:
                c = c.transpose(Image.FLIP_LEFT_RIGHT)
            ox = self.w - self.ox if flip else self.ox
            img.alpha_composite(c, (int(anchor[0] - ox), int(anchor[1] - self.oy)))


def dummy(img, x, ground, label=None, hurt=0):
    """A player stand-in: 20 x 42, standing on the ground."""
    d = ImageDraw.Draw(img)
    col = (236, 122, 88) if hurt else (96, 122, 172)
    d.rectangle((x - 10, ground - 42, x + 10, ground), fill=col, outline=(21, 22, 28))
    d.rectangle((x - 6, ground - 40, x + 6, ground - 30), fill=(222, 180, 132))
    if label:
        text(img, (x - 24, ground - 60), label, 12)


def ground_strip(img, ground, colour=(110, 60, 30, 255), top=(146, 86, 42, 255)):
    d = ImageDraw.Draw(img)
    d.rectangle((0, ground, img.width, img.height), fill=colour)
    d.rectangle((0, ground, img.width, ground + 3), fill=top)


# --- the island ----------------------------------------------------------------------------------------------------------------
def island_png(out):
    import coghaven_sim as cs
    isl = cs.Island(obstacle=300, seed=7)
    isl.generate()
    r = cs.Renderer(isl)
    full = r.frame(200)
    half = full.resize((full.width // 2, full.height // 2), Image.NEAREST)
    d = ImageDraw.Draw(half)
    chests = [(ch, x, y) for (ch, x, y) in isl.pieces if ch in "CQ"]
    for n, (ch, x, y) in enumerate(chests, 1):
        px, py = r.px(x, y)
        cx, cy = (px + 16) // 2, (py + 8) // 2
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), outline=(255, 199, 90), width=3)
        text(half, (cx + 16, cy - 20), str(n), 18, (255, 199, 90))
    k = cs.K
    pond_cells = (k["PondRight"] - k["PondLeft"] + 1) * k["PondDepth"]
    px0, py0 = r.px(k["PondLeft"] - 1, isl.s - 2)
    px1, py1 = r.px(k["PondRight"] + 2, isl.s + k["PondDepth"] + 2)
    crop = full.crop((px0, py0, px1, py1)).resize(((px1 - px0), (py1 - py0)), Image.NEAREST)
    sheet = Image.new("RGBA", (half.width, half.height + crop.height + 120), BG_DARK)
    sheet.alpha_composite(half, (0, 0))
    sheet.alpha_composite(crop, (12, half.height + 70))
    text(sheet, (12, 10), "Coghaven since 2026-11-12: only 2 chests (gold rings), the koi pond 14 x 6 = %d water tiles (vanilla fishes only in 75+)" % pond_cells, 20)
    text(sheet, (12, 38), "1: the engine deck's boiler hall (inside the bronze core)   2: the pagoda's top room.  Each: vanilla sky-island loot + 3-8 Jade (+ the items to come)", 15)
    text(sheet, (12, half.height + 14), "the pond at full scale: 14 wide, 6 deep, flagstone lining; its Koi is the uncommon catch (in place of the Damselfish)", 15)
    text(sheet, (12, half.height + 36), "(clouds, dirt, grass and vanilla furniture are flat stand-ins; a shallow island leaves out the cog socket under the pond)", 13)
    sheet.convert("RGB").save(out)
    print("%s: %dx%d, %d chests" % (out, sheet.width, sheet.height, len(chests)))


# --- the Cogscorpion ---------------------------------------------------------------------------------------------------------------
def scorpion_gif(out):
    g = Grid("Content/Coghaven/NPCs/Cogscorpion", "Content/Coghaven/NPCs/CogscorpionRigData.cs")
    c = consts("Content/Coghaven/NPCs/Cogscorpion.cs", g.r)
    sting = consts("Content/Coghaven/Projectiles/CogscorpionSting.cs")
    R = g.r
    W, H, ground = 560, 220, 180
    x, vx, fc = 90.0, 0.0, 0.0
    target = 380.0
    state, t, since = "walk", 0, c["CooldownTicks"]
    frames = []
    curse = 0
    for tick in range(330):
        t += 1
        dx = target - x
        if state == "walk":
            since += 1
            want = 1 if dx > 0 else -1
            vx = min(c["WalkSpeed"], vx + c["WalkAccel"]) if want > 0 else max(-c["WalkSpeed"], vx - c["WalkAccel"])
            if abs(dx) < 40:
                vx = 0.0
            x += vx
            if since >= c["CooldownTicks"] and abs(dx) <= c["StrikeRangeX"]:
                state, t = "raise", 0
        elif state == "raise":
            vx *= 0.8
            if t >= c["RaiseTicks"]:
                state, t = "strike", 0
        elif state == "strike":
            if t == c["StrikeWhipTicks"] + 1:
                curse += 1
            if t >= c["StrikeTicks"]:
                state, t = "recover", 0
        elif state == "recover":
            if t >= c["RecoverTicks"]:
                state, t, since = "walk", 0, 0
                target = 470.0                                    # the player backs off
        if state == "walk":
            fc = (fc + abs(vx)) % (R["WalkStep"] * R["WalkFrames"]) if abs(vx) > 0.1 else fc
            k = R["Walk"] + int(fc / R["WalkStep"]) % R["WalkFrames"] if abs(vx) > 0.1 else R["Walk"]
        elif state == "raise":
            k = R["Raise"] + min(R["RaiseFrames"] - 1, t // c["RaiseFrameTicks"])
        elif state == "strike":
            k = R["Strike"] + (0 if t < c["StrikeWhipTicks"] else 1 if t < c["StrikeWhipTicks"] + c["StrikeHoldTicks"] else 2)
        else:
            k = R["Recover"] + min(R["RecoverFrames"] - 1, t // c["RecoverFrameTicks"])
        if tick % 2:
            continue
        img = Image.new("RGBA", (W, H), (40, 46, 56, 255))
        ground_strip(img, ground, (196, 180, 150, 255), (228, 218, 192, 255))
        hurt = state == "strike" and c["StrikeWhipTicks"] <= t < c["StrikeWhipTicks"] + c["StrikeHoldTicks"]
        dummy(img, int(target), ground, "jade curse x%d" % curse if curse else None, hurt=hurt)
        flip = True                                                # it faces right, towards the player
        g.draw(img, k, (x, ground), flip=flip)
        if hurt:
            sx = x - R["StingX"]                                  # mirrored: facing right
            sy = ground + R["StingY"]
            half = sting["Size"] // 2
            ImageDraw.Draw(img).rectangle((sx - half, sy - half, sx + half, sy + half), outline=(118, 220, 162), width=2)
        text(img, (8, 6), "Cogscorpion: %s (tick %d)" % ({"walk": "walking", "raise": "raising its tail: the telegraph, %d ticks" % c["RaiseTicks"],
                                                          "strike": "the strike: the sting's hitbox (green) for %d ticks" % c["StrikeHoldTicks"],
                                                          "recover": "recovering"}[state], t), 14)
        text(img, (8, 26), "sting %d Expert, lays the jade curse; %d life, %d defense, %d contact (simulation: no terrain, no lighting)" % (
            c["StingDamage"], c["Life"], c["Defense"], c["ContactDamage"]), 12)
        frames.append(img.resize((W * 2 // 2, H * 2 // 2), Image.NEAREST))
    save_gif(frames, out, 33)


# --- the Flying Buddha Head --------------------------------------------------------------------------------------------------------
def buddha_gif(out):
    g = Grid("Content/Coghaven/NPCs/FlyingBuddhaHead", "Content/Coghaven/NPCs/FlyingBuddhaHeadRigData.cs")
    c = consts("Content/Coghaven/NPCs/FlyingBuddhaHead.cs", g.r)
    R = g.r
    stars = load("Content/Mechanist/Buffs/StunStars.png")
    W, H, ground = 560, 400, 360
    pos = [140.0, 150.0]                                          # the NPC's bottom middle
    vel = [0.0, 0.0]
    target = 330.0
    state, t, since = "float", 0, c["FloatTicks"] - 40
    frames = []
    height = 96                                                   # NPC.height (FlyingBuddhaHead.SetDefaults)
    for tick in range(420):
        t += 1
        if state == "float":
            since += 1
            goal = (target, ground - 42 - c["HoverHeight"] + height / 2)
            cx, cy = pos[0], pos[1] - height / 2
            to = (goal[0] - cx, goal[1] - cy)
            ln = math.hypot(*to)
            want = (to[0] / ln * c["FloatSpeed"], to[1] / ln * c["FloatSpeed"]) if ln > 8 else (0.0, 0.0)
            vel = [vel[0] + (want[0] - vel[0]) * c["FloatAccel"] * 4, vel[1] + (want[1] - vel[1]) * c["FloatAccel"] * 4]
            sp = math.hypot(*vel)
            if sp > c["FloatSpeed"]:
                vel = [vel[0] / sp * c["FloatSpeed"], vel[1] / sp * c["FloatSpeed"]]
            if since >= c["FloatTicks"] and abs(target - pos[0]) <= c["AimWidth"] and (ground - 42) - pos[1] >= c["MinDrop"]:
                state, t = "wrath", 0
        elif state == "wrath":
            vel = [vel[0] * 0.85, min(vel[1] * 0.85, -0.3)]
            if t == 20:
                target = 430.0                                     # the player dodges aside during the telegraph
            if t >= c["WrathTicks"]:
                state, t, vel = "smash", 0, [0.0, 0.0]
        elif state == "smash":
            vel = [0.0, min(c["SmashSpeed"], vel[1] + c["SmashAccel"])]
            if pos[1] + vel[1] >= ground:
                pos[1] = ground
                vel = [0.0, 0.0]
                state, t = "stunned", 0
        elif state == "stunned":
            vel = [0.0, 0.0]
            if t >= c["StunTicks"]:
                state, t = "rise", 0
        elif state == "rise":
            vel = [vel[0] * 0.9, max(vel[1] - 0.15, -c["RiseSpeed"])]
            if t >= c["RiseTicks"]:
                state, t, since = "float", 0, 0
        if state == "dummy-move":
            pass
        pos = [pos[0] + vel[0], pos[1] + vel[1]]
        if state == "stunned" or state == "smash":
            pos[1] = min(pos[1], ground)
        # the frame (PickFrame)
        if state == "wrath":
            k = R["Wrath"] + min(R["WrathFrames"] - 1, t // 15)
        elif state == "smash":
            k = R["Smash"] + (tick // 6) % R["SmashFrames"]
        elif state == "stunned":
            k = R["Stunned"] + (t // 10) % R["StunnedFrames"]
        else:
            k = R["Float"] + (tick // 8) % R["FloatFrames"]
        if tick % 2:
            continue
        img = Image.new("RGBA", (W, H), (44, 62, 92, 255))
        ground_strip(img, ground, (196, 180, 150, 255), (228, 218, 192, 255))
        dummy(img, int(target), ground)
        bob = round(math.sin(tick * 0.05) * 2) if state in ("float", "rise") else 0
        shake = 2 if state == "wrath" and t % 4 < 2 else 0
        g.draw(img, k, (pos[0] + shake, pos[1] + bob))
        if state == "stunned":
            head = (pos[0], pos[1] - height - 4)
            for s in range(3):
                a = tick * 0.1 + s * 2 * math.pi / 3
                fr = (tick // 8 + s) % 2
                st = stars.crop((0, fr * 12, 10, fr * 12 + 10))
                img.alpha_composite(st, (int(head[0] + math.cos(a) * 22 - 5), int(head[1] + math.sin(a) * 22 * 0.35 - 5)))
        if state == "stunned" and t < 12:
            d = ImageDraw.Draw(img)
            for q in range(10):
                ang = math.pi + q * math.pi / 9
                r = 30 + t * 4
                d.rectangle((pos[0] + math.cos(ang) * r - 2, ground - 4 + math.sin(ang) * 8 - 2, pos[0] + math.cos(ang) * r + 2,
                             ground - 4 + math.sin(ang) * 8 + 2), fill=(195, 200, 205))
        label = {"float": "floating, slow (%.1f px/tick)" % c["FloatSpeed"], "wrath": "wrath: the telegraph, %d ticks (the player steps aside)" % c["WrathTicks"],
                 "smash": "the smash: %d Expert, its only damage" % c["SmashDamage"], "stunned": "stunned %d ticks (2 s): harmless to touch, stars" % c["StunTicks"],
                 "rise": "rising back"}[state]
        text(img, (8, 6), "Flying Buddha Head: " + label, 14)
        text(img, (8, 26), "%d life, %d defense, no contact damage: only the smash hurts (simulation: no lighting, no terrain under it)" % (c["Life"], c["Defense"]), 12)
        frames.append(img)
    save_gif(frames, out, 33)


def buddha_frames_png(out):
    """The redrawn head close up: every frame of the real sheets (far, middle, glow) at 2x game size, on a dark sky."""
    g = Grid("Content/Coghaven/NPCs/FlyingBuddhaHead", "Content/Coghaven/NPCs/FlyingBuddhaHeadRigData.cs")
    R = g.r
    names = [("Float", R["Float"], R["FloatFrames"]), ("Wrath", R["Wrath"], R["WrathFrames"]),
             ("Smash", R["Smash"], R["SmashFrames"]), ("Stunned", R["Stunned"], R["StunnedFrames"])]
    cols, pad, top = 4, 8, 22
    cw, ch = g.w + pad, g.h + pad + top
    img = Image.new("RGBA", (cw * cols, ch * len(names)), (34, 40, 52, 255))
    for row, (name, first, count) in enumerate(names):
        for k in range(count):
            x0, y0 = k * cw, row * ch
            g.draw(img, first + k, (x0 + pad // 2 + g.ox, y0 + top + g.oy))
            text(img, (x0 + 6, y0 + 4), "%s %d" % (name, k), 12)
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save(out)
    print(out)


# --- the Mechromancer (a port of Mechromancer.UpdateState / Cogsqueleton, with the real sprites) -------------------------------------
def int_array(rel, name):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    m = re.search(r"%s = \{([^}]*)\}" % name, src)
    return [int(v) for v in m.group(1).split(",") if v.strip()]


def strip_frames(rel, frames):
    im = load(rel)
    h = im.height // frames
    return [im.crop((0, k * h, im.width, k * h + h)) for k in range(frames)]


def mechromancer_gif(out):
    """A Blood Moon night: it floats in beside the player, summons (two graves burn into the ground, two Cogsqueletons
    climb out and walk at the player), then casts (the staff flares, a volley of three Soul Fire Cogs)."""
    rig = "Content/BloodMoon/NPCs/MechromancerRigData.cs"
    g = Grid("Content/BloodMoon/NPCs/Mechromancer", rig)
    c = consts("Content/BloodMoon/NPCs/Mechromancer.cs", g.r)
    R = g.r
    fire_x, fire_y = int_array(rig, "FireX"), int_array(rig, "FireY")
    sq = Grid("Content/BloodMoon/NPCs/Cogsqueleton", "Content/BloodMoon/NPCs/CogsqueletonRigData.cs")
    sc = consts("Content/BloodMoon/NPCs/Cogsqueleton.cs", sq.r)
    cog = strip_frames("Content/BloodMoon/Projectiles/SoulFireCog.png", 4)
    cog_glow = strip_frames("Content/BloodMoon/Projectiles/SoulFireCog_Glow.png", 4)
    grave = strip_frames("Content/BloodMoon/Projectiles/CogsqueletonGrave.png", 4)
    grave_glow = strip_frames("Content/BloodMoon/Projectiles/CogsqueletonGrave_Glow.png", 4)
    W, H, ground = 640, 340, 300
    target = 440.0
    pos = [120.0, 150.0]                                          # the NPC's bottom middle
    vel = [0.0, 0.0]
    height = 76
    state, t = "float", 0
    script = {60: "summon", 200: "cast", 330: "cast"}
    graves, skeletons, cogs = [], [], []
    frames = []
    for tick in range(420):
        t += 1
        if tick in script and state == "float":
            state, t = script[tick], 0
        face = 1 if target > pos[0] else -1
        if state == "float":
            side = -1.0 if pos[0] < target else 1.0
            goal = (target + side * c["KeepX"], ground - 21 - c["KeepY"])
            to = (goal[0] - pos[0], goal[1] - (pos[1] - height / 2))
            ln = math.hypot(*to)
            want = (to[0] / ln * c["FloatSpeed"], to[1] / ln * c["FloatSpeed"]) if ln > 8 else (0.0, 0.0)
            vel = [vel[0] + (want[0] - vel[0]) * c["FloatAccel"] * 4, vel[1] + (want[1] - vel[1]) * c["FloatAccel"] * 4]
        else:
            vel = [vel[0] * 0.9, vel[1] * 0.9]
        if state == "summon":
            if t == 1:
                for side in (-1, 1):
                    graves.append([target + side * c["GraveOffsetTiles"] * 16 + side * 8, c["SummonTelegraph"]])
            if t >= c["SummonTicks"]:
                state, t = "float", 0
        if state == "cast":
            if t == c["CastTelegraph"]:
                k = R["Cast"] + 2
                fx, fy = pos[0] + fire_x[k] * -face, pos[1] + fire_y[k]
                aim = math.atan2((ground - 21) - fy, target - fx)
                for i in range(int(c["Volley"])):
                    a = aim + (i - (c["Volley"] - 1) / 2.0) * c["CogSpread"]
                    cogs.append([fx, fy, math.cos(a) * c["CogSpeed"], math.sin(a) * c["CogSpeed"], 0])
            if t >= c["CastTicks"]:
                state, t = "float", 0
        pos = [pos[0] + vel[0], pos[1] + vel[1]]
        for gr in graves:
            gr[1] -= 1
            if gr[1] == 0:
                skeletons.append([gr[0], 0, 0.0, 0.0])            # x, age, walked, speed
        graves = [gr for gr in graves if gr[1] > 0]
        for s in skeletons:
            s[1] += 1
            if s[1] > sc["RiseTicks"]:
                d = target - s[0]
                want = (1 if d > 0 else -1) * sc["WalkSpeed"] if abs(d) > 14 else 0.0
                s[3] = min(want, s[3] + sc["WalkAccel"]) if want > s[3] else max(want, s[3] - sc["WalkAccel"])
                s[0] += s[3]
                s[2] += abs(s[3])
        live = []
        for cg in cogs:
            cg[0] += cg[2]
            cg[1] += cg[3]
            cg[4] += 1
            hit = abs(cg[0] - target) < 14 and ground - 42 < cg[1] < ground
            if not hit and cg[1] < ground - 4 and 0 < cg[0] < W and cg[4] < 180:
                live.append(cg)
        cogs = live
        if tick % 2:
            continue
        img = Image.new("RGBA", (W, H), (58, 18, 26, 255))
        d = ImageDraw.Draw(img)
        d.ellipse((520, 24, 580, 84), fill=(196, 42, 40, 255))   # the blood moon
        ground_strip(img, ground, (60, 36, 30, 255), (92, 54, 40, 255))
        for gr in graves:
            k = (tick // 5) % 4
            at = (int(gr[0] - 22), ground - 20)
            img.alpha_composite(grave[k], at)
            img.alpha_composite(grave_glow[k], at)
        hurt = any(abs(s[0] - target) < 16 and s[1] > sc["RiseTicks"] for s in skeletons)
        dummy(img, int(target), ground, hurt=hurt)
        for s in skeletons:
            if s[1] <= sc["RiseTicks"]:
                k = sq.r["Rise"] + min(sq.r["RiseFrames"] - 1, s[1] // 10)
            else:
                k = sq.r["Walk"] + (int(s[2] / sq.r["WalkStep"]) % sq.r["WalkFrames"] if abs(s[3]) > 0.1 else 0)
            sq.draw(img, k, (s[0], ground), flip=target > s[0])
        if state == "cast":
            k = R["Cast"] + (0 if t < 20 else 1 if t < c["CastTelegraph"] else 2 if t < c["CastTelegraph"] + 10 else 3)
        elif state == "summon":
            k = R["Summon"] + (0 if t < 20 else 1 if t < c["SummonTelegraph"] else 2 if t < c["SummonTelegraph"] + 12 else 3)
        else:
            k = R["Float"] + (tick // 8) % R["FloatFrames"]
        bob = (tick // 20) % 2 * 2
        g.draw(img, k, (pos[0], pos[1] - bob), flip=face > 0)
        for cg in cogs:
            k = (cg[4] // 3) % 4
            at = (int(cg[0] - 14), int(cg[1] - 14))
            img.alpha_composite(cog[k], at)
            img.alpha_composite(cog_glow[k], at)
        label = {"float": "floating beside its target (%.1f px/tick, through walls)" % c["FloatSpeed"],
                 "summon": "summon: graves burn where they will rise (%d-tick telegraph), then Cogsqueletons climb out" % c["SummonTelegraph"],
                 "cast": "cast: the staff's fire flares (%d-tick telegraph), then a volley of %d Soul Fire Cogs" % (c["CastTelegraph"], c["Volley"])}[state]
        text(img, (8, 6), "Mechromancer (Blood Moon mini-boss): " + label, 13)
        text(img, (8, 26), "%d life, %d defense, %d contact, cogs %d; Cogsqueletons %d life, %d contact (Expert; simulation: no lighting)"
             % (c["Life"], c["Defense"], c["ContactDamage"], c["CogDamage"], sc["Life"], sc["ContactDamage"]), 12)
        frames.append(img)
    save_gif(frames, out, 33)


def mechromancer_frames_png(out):
    """Every frame of the Mechromancer and the Cogsqueleton (real sheets: far, middle, near, glow) at 2x game size."""
    sets = (("Content/BloodMoon/NPCs/Mechromancer", (("Float", 4), ("Cast", 4), ("Summon", 4))),
            ("Content/BloodMoon/NPCs/Cogsqueleton", (("Rise", 4), ("Walk", 6))))
    rows = []
    for base, seqs in sets:
        g = Grid(base, base + "RigData.cs")
        for name, count in seqs:
            rows.append((g, name, g.r[name], count))
    cw = max(r[0].w for r in rows) + 8
    ch = [r[0].h + 26 for r in rows]
    cols = 6
    img = Image.new("RGBA", (cw * cols, sum(ch)), (58, 18, 26, 255))
    y = 0
    for (g, name, first, count), h in zip(rows, ch):
        for k in range(count):
            x0 = k * cw
            g.draw(img, first + k, (x0 + cw // 2, y + 22 + g.oy))
            text(img, (x0 + 4, y + 4), "%s %d" % (name, k), 12)
        y += h
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save(out)
    print(out)


# --- the combined sprites (a port of CombinedSprites.Build) --------------------------------------------------------------------------
def even(v):
    return int(round(v / 2.0)) * 2                               # C#: (int)Math.Round(v / 2.0) * 2 (both round half to even)


def first_half(x, y, w, h, split, diagonal):
    x &= ~1
    y &= ~1
    if not diagonal:
        return x < split
    return (x + 1) / w + (h - 1 - (y + 1)) / h < 1


def combine(aug, base, diagonal):
    wa, ha = aug.size
    wb, hb = base.size
    dx, dy = even(wa / 2 - wb / 2), even(ha / 2 - hb / 2)
    min_x, min_y = min(0, dx), min(0, dy)
    w, h = max(wa, dx + wb) - min_x, max(ha, dy + hb) - min_y
    a_off, b_off = (-min_x, -min_y), (dx - min_x, dy - min_y)
    split_a, split_b = even(wa / 2), even(wb / 2)
    pa, pb = aug.load(), base.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    po = out.load()
    for y in range(h):
        for x in range(w):
            ax, ay = x - a_off[0], y - a_off[1]
            if 0 <= ax < wa and 0 <= ay < ha and first_half(ax, ay, wa, ha, split_a, diagonal) and pa[ax, ay][3] > 0:
                po[x, y] = pa[ax, ay]
                continue
            bx, by = x - b_off[0], y - b_off[1]
            if 0 <= bx < wb and 0 <= by < hb and not first_half(bx, by, wb, hb, split_b, diagonal):
                po[x, y] = pb[bx, by]
    return out


PAIRS = (   # augment, base, points up-right (the augment's use style), the class
    ("Content/Junkyard/Weapons/Macuahuitl.png", "Content/Junkyard/Weapons/MetalWrench.png", True, "melee"),
    ("Content/Gems/Items/JadePhaseblade.png", "Content/Junkyard/Weapons/Macuahuitl.png", True, "melee"),
    ("Content/Mechanist/Weapons/BarrelGun.png", "Content/Mechanist/Weapons/DiamondCutter.png", False, "Mechanist"),
    ("Content/Mechanist/Weapons/DiamondCutter.png", "Content/Mechanist/Weapons/CogLauncher.png", False, "Mechanist"),
    ("Content/OldBrassTown/Weapons/SheriffsRevolver.png", "Content/Bosses/TrashTr0m/Weapons/ScrapLauncher.png", False, "ranged"),
)


def nine(t, dest_w, dest_h, c):
    out = Image.new("RGBA", (dest_w, dest_h), (0, 0, 0, 0))
    sw, sh = t.size
    sx = (0, c, sw - c, sw)
    sy = (0, c, sh - c, sh)
    dx = (0, c, dest_w - c, dest_w)
    dy = (0, c, dest_h - c, dest_h)
    for j in range(3):
        for i in range(3):
            piece = t.crop((sx[i], sy[j], sx[i + 1], sy[j + 1]))
            size = (dx[i + 1] - dx[i], dy[j + 1] - dy[j])
            if size[0] > 0 and size[1] > 0:
                out.alpha_composite(piece.resize(size, Image.NEAREST), (dx[i], dy[j]))
    return out


def icon(img, size_limit=32):
    w, h = img.size
    s = size_limit / max(w, h) if w > size_limit or h > size_limit else 1.0
    return img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.NEAREST) if s != 1.0 else img


def default_name(aug, base):
    """A port of CombinationRules.DefaultName."""
    aw, bw = aug.split(), base.split()
    if len(aw) == 1 and len(bw) == 1:
        return aw[0][:(len(aw[0]) + 1) // 2] + bw[0][len(bw[0]) // 2:]
    return aw[0] + " " + bw[-1]


def window(state, aug_img, base_img, product, stats, name):
    """The window as CombinatorUI.Draw lays it out (UI px), in one of its two states: "preview" (both inputs in, the
    product slot showing a faint preview, Combine lit) or "product" (the product made, named, Take apart lit)."""
    ui = "Content/Combinator/UI/"
    panel, slot, prod = load(ui + "CombinatorPanel.png"), load(ui + "CombinatorSlot.png"), load(ui + "CombinatorProductSlot.png")
    button, help_ = load(ui + "CombinatorButton.png"), load(ui + "CombinatorHelp.png")
    PW, PH = 312, 288
    win = nine(panel, PW, PH, 16)
    d = ImageDraw.Draw(win)

    def label(xy, s, size=14, fill=(223, 185, 78), centre=True):
        f = font(size)
        w = d.textlength(s, font=f)
        x = xy[0] - w / 2 if centre else xy[0]
        d.text((x + 1, xy[1] + 1), s, fill=(21, 22, 28), font=f)
        d.text((x, xy[1]), s, fill=fill, font=f)

    label((PW / 2, 14), "The Combinator", 16)
    base_r, aug_r, prod_r = (44, 60), (PW - 44 - 52, 60), (PW // 2 - 30, 140)
    label((base_r[0] + 26, 42), "Base", 12, (195, 200, 205))
    label((aug_r[0] + 26, 42), "Augment", 12, (195, 200, 205))
    label((prod_r[0] - 46, prod_r[1] + 22), "Product", 12, (195, 200, 205))
    join = ((base_r[1] + 52) + prod_r[1]) // 2 & ~1
    for (x0, y0, x1, y1) in ((base_r[0] + 26 - 4, base_r[1] + 52, base_r[0] + 26 + 4, join + 4),
                             (aug_r[0] + 26 - 4, aug_r[1] + 52, aug_r[0] + 26 + 4, join + 4),
                             (base_r[0] + 26 - 4, join - 4, aug_r[0] + 26 + 4, join + 4),
                             (PW // 2 - 4, join - 4, PW // 2 + 4, prod_r[1] + 6)):
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(90, 58, 23))
        d.rectangle((x0 + 2, y0 + 2, x1 - 3, y1 - 3), fill=(138, 93, 34))
    win.alpha_composite(slot, base_r)
    win.alpha_composite(slot, aug_r)
    win.alpha_composite(prod, prod_r)
    shown = ((base_img, base_r, 52, 255), (aug_img, aug_r, 52, 255), (product, prod_r, 60, 115)) if state == "preview" else ((product, prod_r, 60, 255),)
    for img, (rx, ry), size, alpha in shown:
        ic = icon(img).copy()
        if alpha < 255:
            ic.putalpha(ic.getchannel("A").point(lambda v, a=alpha: a if v else 0))
        win.alpha_composite(ic, (rx + (size - ic.width) // 2, ry + (size - ic.height) // 2))
    if state == "preview":
        label((PW / 2, prod_r[1] + 70), "Makes %d damage, %d use time" % stats, 11, (223, 185, 78))
    else:
        label((PW / 2, prod_r[1] + 70), "Rename it, or take it apart", 11, (140, 201, 176))
    d.rectangle((20, 222, PW - 21, 245), fill=(90, 58, 23))
    d.rectangle((22, 224, PW - 23, 243), fill=(21, 22, 28))
    label((28, 226), "Name:", 12, (223, 185, 78) if state == "product" else (138, 93, 34), centre=False)
    if state == "product":
        label((80, 226), name, 12, (195, 200, 205), centre=False)
    for (bx, s, lit) in ((20, "Combine", state == "preview"), (PW - 20 - 128, "Take apart", state == "product")):
        b = nine(button.crop((0, 0, 24, 24)), 128, 24, 8)
        if not lit:
            b = Image.blend(Image.new("RGBA", b.size, (0, 0, 0, 0)), b, 1.0)
            b = Image.merge("RGBA", [ch.point(lambda v: v * 120 // 255) if i < 3 else ch for i, ch in enumerate(b.split())])
        win.alpha_composite(b, (bx, 254))
        label((bx + 64, 258), s, 13, (223, 185, 78) if lit else (138, 93, 34))
    win.alpha_composite(help_.crop((0, 22, 22, 44)) if state == "product" else help_.crop((0, 0, 22, 22)), (PW - 34, 8))
    return win


def combinator_png(out):
    aug_p, base_p = PAIRS[0][0], PAIRS[0][1]
    aug_img, base_img = load(aug_p), load(base_p)
    product = combine(aug_img, base_img, True)
    m = consts("Content/Junkyard/Weapons/Macuahuitl.cs")
    w = consts("Content/Junkyard/Weapons/MetalWrench.cs")
    stats = ((m["Damage"] + w["Damage"] + 1) // 2, (m["UseTime"] + w["UseTime"] + 1) // 2)
    name = default_name("Macuahuitl", "Metal Wrench")
    sheet = Image.new("RGBA", (1340, 1300), BG_DARK)
    text(sheet, (16, 10), "The Combinator's window (the real UI art, 2x; Terraria's font stood in by Arial): a Macuahuitl (augment) on a Metal Wrench (base)", 16)
    text(sheet, (16, 34), "left: both in, a faint preview of the product, Combine lit; right: combined, with its default name, Take apart lit, the '?' hovered (its tip below)", 13)
    for k, state in enumerate(("preview", "product")):
        win = window(state, aug_img, base_img, product, stats, name)
        sheet.alpha_composite(win.resize((win.width * 2, win.height * 2), Image.NEAREST), (16 + k * 660, 64))
    tip = ["How the Combinator works", "Put a weapon in Base and another in Augment, then press Combine.",
           "Both must be of the same class (melee, ranged, magic, Mechanist...). Summon weapons and weapons already combined can't go in.",
           "The Augment gives the attack: its projectile and its animation.",
           "The Base gives its passive effects and bonuses (homing, bursts, ammo saving, extra damage to machines...), its crit and its range.",
           "Damage, use time and mana or steam cost are half the sum of the two. Their reforges are ignored; the new weapon can be",
           "reforged at the Goblin Tinkerer like any weapon of its class.",
           "Right click uses the Base's right-click attack if it has one, otherwise the Augment's.",
           "Put a combined weapon in the Product slot to rename it or take it apart: both weapons come back as they went in."]
    tx, ty = 24, 670
    ImageDraw.Draw(sheet).rectangle((tx - 8, ty - 8, tx + 1290, ty + len(tip) * 20 + 4), fill=(21, 22, 28, 235), outline=(138, 93, 34))
    for i, line in enumerate(tip):
        text(sheet, (tx, ty + i * 20), line, 13, (223, 185, 78) if i == 0 else (238, 241, 243))
    y = 880
    text(sheet, (16, y), "Combined sprites made at runtime by CombinedSprites (this is its port): augment's first half + base's second half; swords split on the", 14)
    text(sheet, (16, y + 20), "diagonal, guns down the middle; cuts on the 2 px grid. Shown: augment, base, the combination (our own weapons: vanilla's art isn't in the repo)", 12)
    x, y = 16, y + 48
    for aug_p2, base_p2, diag, cls in PAIRS:
        a, b = load(aug_p2), load(base_p2)
        cimg = combine(a, b, diag)
        col_w = sum(i.width * 2 + 10 for i in (a, b, cimg)) + 20
        if x + col_w > sheet.width - 10:
            x, y = 16, y + 170
        xx = x
        for img in (a, b, cimg):
            sheet.alpha_composite(img.resize((img.width * 2, img.height * 2), Image.NEAREST), (xx, y))
            xx += img.width * 2 + 10
        text(sheet, (x, y + 140), "%s + %s (%s)" % (os.path.basename(aug_p2)[:-4], os.path.basename(base_p2)[:-4], cls), 12)
        x += col_w
    sheet.convert("RGB").save(out)
    print("%s: %dx%d (default name: %s)" % (out, sheet.width, sheet.height, name))


# --- the station and the blueprint -------------------------------------------------------------------------------------------------
def station_frames():
    sheet = load("Content/Combinator/Tiles/CombinatorTile.png")
    frames = []
    for f in range(4):
        obj = Image.new("RGBA", (64, 50), (0, 0, 0, 0))
        for r, (sy, h) in enumerate(((0, 16), (18, 16), (36, 18))):
            for c in range(4):
                tile = sheet.crop((c * 18, f * 56 + sy, c * 18 + 16, f * 56 + sy + h))
                obj.alpha_composite(tile, (c * 16, r * 16))
        frames.append(obj)
    return frames


def station_gif(out):
    st = station_frames()
    bp = load("Content/Combinator/Items/CombinatorBlueprint.png")
    beam = load("Content/Combinator/Items/CombinatorBlueprint_Beam.png")
    aura = load("Content/Combinator/Items/CombinatorBlueprint_Aura.png")
    c = consts("Content/Combinator/Items/CombinatorBlueprint.cs")
    tc = consts("Content/Combinator/Tiles/CombinatorTile.cs")
    frames = []
    W, H = 640, 360
    for tick in range(0, 180, 3):
        img = Image.new("RGBA", (W, H), (58, 24, 22, 255))
        d = ImageDraw.Draw(img)
        d.rectangle((0, 300, 320, H), fill=(84, 20, 28, 255))
        d.rectangle((320, 300, W, H), fill=(236, 113, 40, 255))      # lava under the blueprint (it floats)
        f = (tick // tc["TicksPerFrame"]) % tc["Frames"]
        img.alpha_composite(st[f].resize((128, 100), Image.NEAREST), (90, 200))
        text(img, (40, 160), "The Combinator: cog and furnace, %d frames x %d ticks" % (tc["Frames"], tc["TicksPerFrame"]), 12)
        pulse = 0.75 + 0.25 * math.sin(tick * 2 * math.pi / c["PulseTicks"])
        centre = (480, 220 + round(math.sin(tick * 0.06) * 2))
        light = Image.new("RGB", (W, H), (0, 0, 0))             # added on, as in game (alpha-0 colours in a premultiplied batch)
        for k in range(c["BeamSegments"]):
            fade = 1 - k / c["BeamSegments"]
            add(light, beam, (centre[0] - beam.width // 2, centre[1] - beam.height * (k + 1)), 0.55 * fade * pulse)
        add(light, aura, (centre[0] - aura.width // 2, centre[1] - aura.height // 2), 0.7 * pulse)
        img = Image.merge("RGBA", (*ImageChops.add(img.convert("RGB"), light).split(), img.getchannel("A")))
        img.alpha_composite(bp, (centre[0] - bp.width // 2, centre[1] - bp.height // 2))
        text(img, (330, 250), "Combinator Blueprint: floats where the Wall falls, a beam", 12)
        text(img, (330, 266), "of %d segments and a ring of light, pulsing every %.1f s" % (c["BeamSegments"], c["PulseTicks"] / 60), 12)
        text(img, (8, 6), "The Combinator station and the Wall of Flesh's first-kill Blueprint (simulation: no lighting, sparks left out)", 14)
        frames.append(img)
    save_gif(frames, out, 50)


def add(light, sprite, at, strength):
    """Adds `sprite`'s colours times `strength` onto the `light` buffer (additive blending)."""
    rgb = Image.new("RGB", sprite.size, (0, 0, 0))
    rgb.paste(sprite.convert("RGB"), (0, 0), sprite.getchannel("A"))
    rgb = rgb.point(lambda v: int(v * strength))
    region = light.crop((at[0], at[1], at[0] + sprite.width, at[1] + sprite.height))
    light.paste(ImageChops.add(region, rgb), (at[0], at[1]))


# --- Rocket Boots on steam ---------------------------------------------------------------------------------------------------------
def rocket_gif(out):
    """A rocket flight with a 30-steam tank (the Cogpunker Manual's 20 and a Glass Container's 10): the thrust (vanilla's
    rocket boost, about -0.25 px/tick^2 up to -5 px/tick here) lasts while the tank pays 2 every 6 ticks, then gravity."""
    c = consts("Content/Mechanist/SteamRocketPlayer.cs")
    tank = 30
    steam, window, h, vy, frames = tank, 0, 0.0, 0.0, []
    flying, log = True, []
    scale = 0.3                                                # display px per world px (the flight is ~20 tiles)
    for tick in range(200):
        thrust = flying and (window > 0 or steam >= c["SteamPerWindow"])
        if thrust:
            if window <= 0:
                steam -= c["SteamPerWindow"]
                window = c["WindowTicks"]
            window -= 1
            vy = max(vy - 0.25, -5.0)
        else:
            flying = False
            vy = min(vy + 0.4, 10.0)
        h = max(0.0, h - vy)
        if h == 0.0 and not flying:
            vy = 0.0
        log.append((tick, h))
        if tick % 3:
            continue
        img = Image.new("RGBA", (560, 360), (44, 62, 92, 255))
        d = ImageDraw.Draw(img)
        ground = 330
        d.rectangle((0, ground, 560, 360), fill=(110, 60, 30))
        py = ground - h * scale
        d.rectangle((140, py - 42 * scale * 2, 152, py), fill=(96, 122, 172), outline=(21, 22, 28))
        if thrust:
            d.polygon(((141, py), (151, py), (146, py + 10 + (tick % 2) * 3)), fill=(255, 199, 90))
        d.rectangle((40, 80, 70, 300), outline=(184, 138, 51), width=3)
        level = int(214 * steam / tank)
        d.rectangle((44, 296 - level, 66, 296), fill=(238, 241, 243))
        text(img, (28, 306), "%d / %d" % (steam, tank), 13)
        text(img, (8, 6), "Rocket Boots on steam: %d steam every %d ticks of thrust (0.1 s)" % (c["SteamPerWindow"], c["WindowTicks"]), 14)
        text(img, (8, 26), "a %d-steam tank: %.1f s of thrust (vanilla ~1.2 s, free); empty: no rocket; refills after landing" % (
            tank, tank / c["SteamPerWindow"] * c["WindowTicks"] / 60), 12)
        text(img, (8, 46), "%s" % ("thrust (steam paid each 0.1 s)" if thrust else "out of steam: falling" if h > 0 else "landed"), 12,
             (255, 199, 90) if thrust else (236, 122, 88))
        px0, py0 = 240, 300
        d.line((px0, py0, px0 + 300, py0), fill=(127, 135, 148))
        d.line((px0, py0, px0, py0 - 200), fill=(127, 135, 148))
        for (t0, y0), (t1, y1) in zip(log, log[1:]):
            d.line((px0 + t0 * 1.5, py0 - y0 * 0.4, px0 + t1 * 1.5, py0 - y1 * 0.4), fill=(255, 199, 90))
        text(img, (px0 + 4, py0 + 6), "height over time (rocket physics approximated)", 11)
        frames.append(img)
    save_gif(frames, out, 50)


# --- items -----------------------------------------------------------------------------------------------------------------------------
def items_png(out):
    rows = [("Steam Injector (tile, item, buff)", [station_tile("Content/Mechanist/Stations/SteamInjectorTile.png", 2, 3),
                                                   load("Content/Mechanist/Stations/SteamInjector.png"),
                                                   load("Content/Mechanist/Stations/SteamInjection.png")]),
            ("Koi", [load("Content/Coghaven/Items/Koi.png")]),
            ("The First Half, The Second Half, Combinator Blueprint, The Combinator",
             [load("Content/Combinator/Items/TheFirstHalf.png"), load("Content/Combinator/Items/TheSecondHalf.png"),
              load("Content/Combinator/Items/CombinatorBlueprint.png"), load("Content/Combinator/Items/TheCombinator.png")])]
    sheet = Image.new("RGBA", (1000, 1010), BG_DARK)
    y = 50
    text(sheet, (16, 10), "2026-11-12 sprites at 3x, over dark and light (D4: readable on both)", 18)
    for name, imgs in rows:
        text(sheet, (16, y), name, 14)
        y += 24
        for bg in (BG_DARK, BG_SKY):
            band = Image.new("RGBA", (980, max(i.height for i in imgs) * 3 + 12), bg)
            x = 6
            for im in imgs:
                band.alpha_composite(im.resize((im.width * 3, im.height * 3), Image.NEAREST), (x, 6))
                x += im.width * 3 + 24
            sheet.alpha_composite(band, (10, y))
            y += band.height + 4
        y += 12
    sheet.convert("RGB").save(out)
    print("%s: %dx%d" % (out, sheet.width, sheet.height))


def station_tile(path, cols, rows):
    sheet = load(path)
    heights = (16, 16, 18)
    obj = Image.new("RGBA", (cols * 16, 50), (0, 0, 0, 0))
    y = 0
    for r in range(rows):
        for c in range(cols):
            obj.alpha_composite(sheet.crop((c * 18, r * 18, c * 18 + 16, r * 18 + heights[r])), (c * 16, y))
        y += 16
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    jobs = (("island", island_png, "2026-11-12_coghaven-island-chests.png"),
            ("scorpion", scorpion_gif, "2026-11-12_coghaven-cogscorpion.gif"),
            ("buddha", buddha_gif, "2026-11-12_coghaven-buddha-head.gif"),
            ("buddha-frames", buddha_frames_png, "2026-11-12_coghaven-buddha-head-frames.png"),
            ("mechromancer", mechromancer_gif, "2026-11-12_bloodmoon-mechromancer.gif"),
            ("mechromancer-frames", mechromancer_frames_png, "2026-11-12_bloodmoon-mechromancer-frames.png"),
            ("combinator", combinator_png, "2026-11-12_combinator-window.png"),
            ("station", station_gif, "2026-11-12_combinator-station.gif"),
            ("rocket", rocket_gif, "2026-11-12_mechanist-rocket-boots.gif"),
            ("items", items_png, "2026-11-12_items-steam-injector-koi.png"))
    for key, fn, name in jobs:
        if only is None or key in only:
            fn(os.path.join(a.out, name))


if __name__ == "__main__":
    main()
