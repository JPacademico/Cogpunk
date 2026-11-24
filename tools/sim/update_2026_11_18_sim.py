"""D5 proofs for the request of 2026-11-18. Run from the repo root:

    python -P tools/sim/update_2026_11_18_sim.py [--out docs/media] [--only glaives,glaive-frames,turn,jadey,statue,drift,cakti,
                                                                        mace,fox,research,mechromancer,items]

Offline replays with the real sprites and the C# constants (read from the source files), 60 ticks a second, 3 ticks a GIF frame
(50 ms) unless a caption says otherwise. Leaves out: lighting (the fox's light is drawn as a soft disc), tile collision, dust
(palette sparks), netcode, vanilla's own item icons (the research window's three are drawn here as stand-ins; the game draws
the real Copper Pickaxe, Iron Ore and Hermes Boots).

    glaives, glaive-frames, jadey, statue, drift, cakti   the 2026-11-17 replays (jadey_loot_sim.py) re-run on the new art:
                   the user's glaive with one slash a swing; Jadey's mirror-symmetric body; the Cak-ti at 10 damage.
    turn           Jadey turning left and right (her body and arms stay put about her axis; her hitbox drawn).
    mace           the Incense Mace: the censer spun round the hand on its chain (hits for its damage), thrown (x2) into a Rust
                   Collector and pulled back; then the right click: the incense ring rolls out to 25 tiles; the ally inside is
                   blessed, the one outside isn't (a wide shot at 1x).
    fox            (retired 2026-11-19: the fox's tail now sways; update_2026_11_19_sim.py replays it as foxscene)
    fox (was)      the Jade Token's fox: trotting after its owner, floating when left far behind, settling and sleeping when
                   its owner stands still (the 5 s wait shown at 4x), waking when they move; its light a faint jade disc.
    research       (retired: the layout changed later the same day; update_2026_11_18c_sim.py draws the research window now
                   and writes the same file; research_gif below is kept for the record)
    mechromancer   the Mechromancer under the floaty rules: far and drifting with a ranged fighter, close with a melee one.
    items          a sheet of every new sprite over dark and light backgrounds (a PNG).
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import jadey_loot_sim as L  # noqa: E402
import stage as S  # noqa: E402
import make_teaser as M  # noqa: E402

J = "Content/Bosses/Jadey/"


def save(frames, path, scale=1, ms=50):
    out = [f.convert("RGB").resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    pal = [im.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.Dither.NONE) for im in out]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=False, disposal=1)
    print("wrote", path, len(frames), "frames", os.path.getsize(path) // 1024, "KB")


# ================================================================================================
# Jadey turning
# ================================================================================================
def turn_gif(path):
    sheet, kr = L.jadey_sheet()
    kj = S.consts(J + "Jadey.cs", J + "JadeyRigData.cs")
    w, h, floor = 400, 200, 180
    bg = L.backdrop(w, h, floor)
    frames = []
    for t in range(240):
        img = bg.copy()
        flip = (t // 40) % 2 == 1
        x, y = sheet.place(200, floor - 20, flip=flip)
        img.alpha_composite(sheet.frame(kr["Idle"] + (t // 9) % kr["IdleFrames"], flip=flip), (int(x), int(y)))
        d = ImageDraw.Draw(img)
        d.line([200, 30, 200, floor - 10], fill=(236, 122, 88, 255), width=1)
        hw, hh = kr["BodyRight"] - kr["BodyLeft"], -kr["BodyTop"] - 2
        d.rectangle([200 - hw // 2, floor - 20 - hh, 200 + hw // 2, floor - 20], outline=(118, 220, 162, 255))
        L.label(img, "JADEY facing %s: mirrored on her axis (red); hitbox (green)" % ("right" if flip else "left"), 6, 4)
        if t % 3 == 0:
            frames.append(img)
    L.save_gif(frames, path)


# ================================================================================================
# The Incense Mace
# ================================================================================================
def mace_gif(path):
    km = S.consts(J + "Weapons/IncenseMace.cs", J + "Weapons/IncenseAura.cs", J + "Weapons/IncenseMaceHead.cs")
    head = S.load(J + "Weapons/IncenseMaceHead.png")
    link = S.load(J + "Weapons/IncenseMaceChain.png")
    puffs = S.strip(J + "Weapons/IncenseAura.png", 4)
    icon = S.load(J + "Buffs/IncenseBlessing.png")
    rust = S.vanilla_frames("Content/Junkyard/NPCs/RustCollector.png", 11)
    W, H, floor = 900, 300, 270
    bg = L.backdrop(W, H, floor)
    px, ex = 200, 420
    ally_in, ally_out = 470, 700
    frames = []
    hits = []
    parts = S.Particles(4)
    state, theta, hx, hy, out_t = "spin", 0.0, 0.0, 0.0, 0
    flash = -99
    radius = km["AuraRadiusTiles"] * 16
    aura_at = 170
    for t in range(330):
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        hand = (px + 6, floor - 32)
        if t < aura_at:                                   # the flail
            if state == "spin":
                theta += 0.32
                hx, hy = hand[0] + math.cos(theta) * 34, hand[1] + math.sin(theta) * 34
                if t == 70:
                    state, out_t = "out", 0
                if 120 < t and abs(hx - (ex - 10)) < 20 and t % 12 == 0:
                    pass
            elif state == "out":
                out_t += 1
                hx += km["LaunchSpeed"] if "LaunchSpeed" in km else 17.0
                hy += (floor - 22 - hy) * 0.2
                if hx >= ex - 14 and flash < t - 30:
                    hits.append((t, ex, floor - 52, km["Damage"] * 2))
                    flash = t
                    parts.burst(ex, floor - 22, 10, [S.BRASS[4], S.BRASS[3], S.STEAM[2]], speed=(1.0, 3.0), life=(10, 20))
                    state = "back"
                if out_t > 15:
                    state = "back"
            elif state == "back":
                dx, dy = hand[0] - hx, hand[1] - hy
                dist = math.hypot(dx, dy)
                if dist < 16:
                    state = "spin"
                    theta = math.atan2(hy - hand[1], hx - hand[0])
                else:
                    hx, hy = hx + dx / dist * 14, hy + dy / dist * 14
        else:
            hx, hy = hand[0] + 6, hand[1] + 14
        # the enemy
        fr = rust[(t // 5) % 8]
        v.put(M.hit_flash(fr, t - flash, 5), ex - 20, floor - 38)
        # the aura
        if t >= aura_at:
            age = t - aura_at
            if age < km["LifeTicks"]:
                reach = 1 - (1 - min(1.0, age / km["ExpandTicks"])) ** 3
                r = radius * reach + age * 0.4
                fade = 1.0 if age < km["ExpandTicks"] else max(0.0, 1 - (age - km["ExpandTicks"]) / km["FadeTicks"])
                f = 0 if age < km["ExpandTicks"] * 0.4 else 1 if age < km["ExpandTicks"] else 2 if age < km["ExpandTicks"] + km["FadeTicks"] * 0.5 else 3
                for k in range(int(km["Puffs"])):
                    a = k * 2 * math.pi / km["Puffs"]
                    qx, qy = px + math.cos(a) * r, floor - 21 + math.sin(a) * r
                    if -16 < qx < W + 16 and -16 < qy < H:
                        img.alpha_composite(S.faded(puffs[f], 0.85 * fade), (int(qx - 8), int(qy - 8)))
        # the players
        M.put_player(v, px, floor, frame=3 if t < aura_at else 2)
        M.put_player(v, ally_in, floor, frame=0, flip=True, armor="Brass")
        M.put_player(v, ally_out, floor, frame=0, flip=True, armor="Brass")
        if t >= aura_at + 10:
            for (qx, inside) in ((px, True), (ally_in, True), (ally_out, False)):
                if inside:
                    img.alpha_composite(icon, (qx - 16, floor - 86))
            L.label(img, "+10% damage and attack speed, 35 s", ally_in - 70, floor - 100)
            L.label(img, "outside 25 tiles: nothing", ally_out - 60, floor - 100)
        # the chain and the head
        if t < aura_at:
            dx, dy = hx - hand[0], hy - hand[1]
            n = int(math.hypot(dx, dy) // 8)
            for k in range(n):
                cx, cy = hand[0] + dx * (k + 0.5) / max(1, n), hand[1] + dy * (k + 0.5) / max(1, n)
                img.alpha_composite(link, (int(cx - link.width / 2), int(cy - link.height / 2)))
            img.alpha_composite(head, (int(hx - head.width / 2), int(hy - head.height / 2)))
        parts.step()
        parts.draw(v)
        for (at, x2, y2, val) in hits:
            M.number(v, x2, y2, val, t - at, False)
        cap = ("INCENSE MACE: spin it, throw it (x2: %d); 5 steam a use" % (km["Damage"] * 2)) if t < aura_at else \
            "INCENSE MACE, right click (20 steam, 30 s cooldown): an incense ring to 25 tiles blesses allies inside"
        L.label(img, cap, 6, 4)
        if t % 3 == 0:
            frames.append(img)
    save(frames, path, scale=1)


# ================================================================================================
# The Jade Token's fox
# ================================================================================================
def fox_gif(path):
    """The fox after its owner (JadeFoxPet's constants and rules): it trots after them; when they hop a wall too tall for it
    (7 tiles: its jump clears about 4) it gets stuck and, 45 ticks on, floats over as a spirit; the owner stands still, so it
    settles and sleeps (the 5 s wait shown at x4); they walk off, it wakes and follows."""
    k = S.consts("Content/Coghaven/Pets/JadeFoxPet.cs")
    sheet = S.load("Content/Coghaven/Pets/JadeFoxPet.png")
    glow = S.load("Content/Coghaven/Pets/JadeFoxPet_Glow.png")
    n = int(k["FrameCount"])
    fh = sheet.height // n
    wall_l, wall_r, wall_h = 324, 340, 112

    def cell(im, f, flip):
        c = im.crop((0, f * fh, im.width, f * fh + fh))
        return c.transpose(Image.FLIP_LEFT_RIGHT) if flip else c

    W, H, floor = 560, 220, 196
    bg = L.backdrop(W, H, floor)
    bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 110)))
    stone = S.load("Content/Coghaven/Tiles/VaultGearworkTile.png").crop((18, 0, 34, 16))
    for y in range(floor - wall_h, floor, 16):
        bg.alpha_composite(stone, (wall_l, y))
    frames = []
    fx, fy, fvx, fvy = 90.0, float(floor), 0.0, 0.0
    state, st, trot_d, frame, still, stuck = "follow", 0, 0.0, 0, 0, 0
    px, py, pdir = 120.0, float(floor), 1
    for t in range(1150):
        ox, oy = px, py
        if 30 <= t < 110:
            px += 2.2
        elif 110 <= t < 140:
            u = (t - 110) / 30.0
            px = 296 + (380 - 296) * u
            py = floor - 130 * math.sin(math.pi * u)
        elif 140 <= t and px < 500 and t < 1000:
            px, py = min(500.0, px + 2.2), float(floor)
        elif 1000 <= t and px > 400:
            px -= 2.0
            pdir = -1
        owner_moving = abs(px - ox) + abs(py - oy) > 0.25
        st += 1
        target = px - k["FollowOffset"] * pdir
        if state == "follow":
            dx = target - fx
            if abs(dx) > 24:
                fvx = max(-k["RunSpeed"] if "RunSpeed" in k else -7.5, min(7.5, fvx + math.copysign(0.3, dx)))
            else:
                fvx *= 0.85
            nx = fx + fvx
            blocked = fy > floor - wall_h and ((fx <= wall_l - 10 < nx + 10) or (fx >= wall_r + 10 > nx - 10))
            if blocked:
                fvx = 0.0
                nx = wall_l - 10 if fx < wall_l else wall_r + 10
                if fy >= floor:
                    fvy = -7.5                                  # it tries to hop the wall
            fx = nx
            fvy = min(fvy + 0.4, 10.0)
            fy = min(float(floor), fy + fvy)
            if fy >= floor:
                fvy = 0.0
            stuck = stuck + 1 if blocked and abs(dx) > k["StuckDistance"] else 0
            if stuck > 45 or abs(px - fx) > 480:
                state, st, stuck = "float", 0, 0
            still = still + 1 if not owner_moving and abs(dx) <= 24 and fy >= floor else 0
            if still >= k["SleepDelay"]:
                state, st, still = "sleep", 0, 0
            if abs(fvx) > 0.3 and fy >= floor:
                trot_d += abs(fvx)
                if not (k["FrameTrot"] <= frame < k["FrameTrot"] + k["TrotFrames"]):
                    frame = k["FrameTrot"]
                if trot_d >= k["TrotAnimDistance"]:
                    trot_d = 0
                    frame = k["FrameTrot"] + (frame - k["FrameTrot"] + 1) % k["TrotFrames"]
            elif fy < floor:
                frame = k["FrameTrot"] + 1
            else:
                frame = k["FrameIdle"] + (t // k["IdleTicksPerFrame"]) % k["IdleFrames"]
        elif state == "float":
            tx, ty = px - k["FloatBehind"] * pdir, py - k["FloatAbove"]
            dx, dy = tx - fx, ty - fy
            dist = math.hypot(dx, dy) or 1.0
            speed = min(dist / 12 + 2, 14)
            fvx += (dx / dist * speed - fvx) * 0.1
            fvy += (dy / dist * speed - fvy) * 0.1
            fx, fy = fx + fvx, fy + fvy
            frame = k["FrameFloat"] + (st // k["FloatTicksPerFrame"]) % k["FloatFrames"]
            inside = wall_l - 10 < fx < wall_r + 10 and fy > floor - wall_h
            if math.hypot(px - fx, py - fy) < 120 and py >= floor and not inside:
                state, st, fvy = "follow", 0, 0.0
        elif state == "sleep":
            frame = (k["FrameSettle"] + st // k["SettleTicksPerFrame"]) if st < k["SettleTicksPerFrame"] * 2 else                 k["FrameSleep"] + ((st - k["SettleTicksPerFrame"] * 2) // k["SleepTicksPerFrame"]) % 2
            if owner_moving:
                state, st = "wake", 0
        elif state == "wake":
            frame = k["FrameWake"] + min(2, st // k["WakeTicksPerFrame"])
            if st >= k["WakeTicks"]:
                state, st = "follow", 0
        flip = (fvx < -0.2) if abs(fvx) > 0.2 else (px < fx)
        fast = (state == "follow" and still > 30) or (state == "sleep" and 60 < st)
        if t % (12 if fast else 3) == 0:
            img = bg.copy()
            v = S.View(W / 2, H / 2)
            v.img, v.x0, v.y0 = img, 0, 0
            light = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dl = ImageDraw.Draw(light)
            for rr, a in ((46, 36), (32, 56), (20, 76)):
                dl.ellipse([fx - rr, fy - 14 - rr, fx + rr, fy - 14 + rr], fill=(30, 114, 88, a))
            img.alpha_composite(light)
            M.put_player(v, int(px), int(py), frame=0 if not owner_moving else 6 + (t // 3) % 14, flip=pdir < 0)
            c = cell(sheet, frame, flip)
            ox2 = c.width - k["OriginX"] if flip else k["OriginX"]
            at = (int(fx - ox2), int(fy - (fh - k["FootPadding"])))
            img.alpha_composite(c, at)
            img.alpha_composite(cell(glow, frame, flip), at)
            L.label(img, "JADE TOKEN: its spirit fox (%s)%s" % (state, "  - shown x4" if fast else ""), 6, 4)
            frames.append(img)
    L.save_gif(frames, path)


# ================================================================================================
# The research window
# ================================================================================================
ICONS = {
    "pick": ("....oo......", "...oCCo.....", "..oCcCCo....", "...ooCcCo...", ".....oCcoo..", "....owoCo...", "...owo.o....", "..owo.......",
             ".owo........", "owo.........", "oo.........."),
    "ore": ("....oooo....", "..ooSSSSoo..", ".oSSsSSsSSo.", "oSsSSSsSSsSo", "oSSSdSSSdSSo", "oSsSSSSsSSSo", ".oSSSsSSSSo.", "..oooooooo.."),
    "gem": ("...oooooo...", "..oWsWWsWo..", ".oWWsWWsWWo.", "oooooooooooo", ".osWWWWWWso.", "..osWWWWso..", "...osWWso...",
            "....osso....", ".....oo....."),
    "boots": ("..oooo......", ".oWWWWo.....", ".oWwwWo.....", ".oBBBBo.oo..", ".oBbbBo.oWo.", ".oBbbBBoWWo.", ".oBbbbbBBBo.", "oBBBBBBBBBBo",
              "oooooooooooo"),
}
ICON_COL = {"o": (21, 22, 28), "C": (196, 104, 58), "c": (233, 160, 107), "w": (146, 86, 42), "S": (127, 135, 148), "s": (183, 191, 202),
            "d": (79, 85, 98), "W": (238, 241, 243), "B": (184, 138, 51), "b": (223, 185, 78)}


def icon_img(name):
    rows = ICONS[name]
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), ICON_COL[ch] + (255,))
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def research_gif(path):
    """The research window (a mock-up at the game's UI size, the real node frames, knowledge sign and Cogpunk icons; vanilla's
    three icons drawn as stand-ins): two points; hover Cogpunker and research it; the Scrap Manual is read ("Knowledge
    expanded!") and its three secret nodes appear; hover Hit the Joints: 2 points, one left (red)."""
    nodes_img = S.load("Content/Research/UI/ResearchNode.png")
    node_frames = [nodes_img.crop((0, k * 58, 56, k * 58 + 56)) for k in range(3)]
    sign = S.load("Content/Research/UI/ResearchKnowledge.png")
    W, H = 800, 620
    wx, wy, ww, wh = 20, 20, 760, 560
    rng = random.Random(1118)
    stars = [(rng.randrange(ww - 20), rng.randrange(wh - 56), rng.randrange(4)) for _ in range(200)]

    def own(rel):
        im = S.load(rel)
        if im.width > 36 or im.height > 36:
            k = max(im.width, im.height) / 36.0
            im = im.resize((max(1, int(im.width / k)), max(1, int(im.height / k))), Image.NEAREST)
        return im
    nodes = [("The Basics", 0, 0, icon_img("pick"), False), ("Mine and Craft", -1, 1, icon_img("ore"), False),
             ("Cogpunker", 0, 1, own("Content/Mechanist/Accessories/BrassContainer.png"), False), ("Jogger", 1, 1, icon_img("boots"), False),
             ("Gem Power", -1, 2, icon_img("gem"), False), ("Causes Autism", 1, 2, own("Content/Bosses/TrashTr0m/Items/TetanusShot.png"), False),
             ("In a Cave! With Scraps!!", -1, 3, own("Content/Scrap/Armor/ScrapHelmet.png"), True),
             ("Hit the Joints", 0, 3, own("Content/Scrap/Items/RustedCog.png"), True), ("Mandacaru", 1, 3, own("Content/Desert/Weapons/Cakti.png"), True)]
    # (from tick, hovered node, knowledge, states (0 locked, 1 ready, 2 researched), secrets shown)
    script = [(0, None, 2, (2, 0, 1, 0, 0, 1, 0, 0, 0), False), (24, 2, 2, (2, 0, 1, 0, 0, 1, 0, 0, 0), False),
              (66, 2, 1, (2, 0, 2, 0, 0, 1, 0, 0, 0), False), (100, None, 1, (2, 0, 2, 0, 0, 1, 1, 0, 1), True),
              (150, 7, 1, (2, 0, 2, 0, 0, 1, 1, 0, 1), True), (230, None, 1, (2, 0, 2, 0, 0, 1, 1, 0, 1), True)]
    tips = {
        (2, 1): ["Cogpunker", "W|+10 steam capacity", "", "G|Costs 1 (you have 2)", "G|Research The Basics first", "", "G|Click to research"],
        (2, 2): ["Cogpunker", "W|+10 steam capacity", "", "G|Researched"],
        (7, 0): ["Hit the Joints", "W|+10% damage against machines", "", "R|Costs 2 (you have 1)", "G|Research The Basics first", "",
                 "N|Not within your reach yet"],
    }
    frames = []
    for t in range(240):
        hover, know, states, secrets = None, 2, None, False
        for (at, hv, kn, stt, sec) in script:
            if t >= at:
                hover, know, states, secrets = hv, kn, stt, sec
        img = Image.new("RGBA", (W, H), (40, 40, 48, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([wx, wy, wx + ww, wy + wh], fill=(21, 22, 28))
        d.rectangle([wx + 2, wy + 2, wx + ww - 2, wy + wh - 2], fill=(90, 58, 23))
        d.rectangle([wx + 4, wy + 4, wx + ww - 4, wy + wh - 4], fill=(184, 138, 51))
        d.rectangle([wx + 8, wy + 8, wx + ww - 8, wy + wh - 8], fill=(21, 22, 28))
        d.rectangle([wx + 10, wy + 10, wx + ww - 10, wy + wh - 10], fill=(24, 20, 36))
        title = S.text("Ancient Research", 16, "title")
        img.alpha_composite(title, (wx + ww // 2 - title.width // 2, wy + 12))
        img.alpha_composite(sign, (wx + 18, wy + 12))                          # the knowledge sign and the number
        num = S.text(str(know), 16, "title", (196, 250, 214), (118, 220, 162), (10, 34, 32))
        img.alpha_composite(num, (wx + 18 + sign.width + 8, wy + 13))
        fx0, fy0 = wx + 10, wy + 46
        d.rectangle([fx0, fy0, wx + ww - 10, wy + wh - 10], fill=(18, 16, 30))
        for (sx, sy, sh) in stars:
            c = ((46, 50, 59), (70, 58, 147), (127, 135, 148), (198, 189, 255))[sh]
            s = 4 if sh == 3 else 2
            d.rectangle([fx0 + sx, fy0 + sy, fx0 + sx + s - 1, fy0 + sy + s - 1], fill=c)
        cx, bottom = wx + ww // 2, wy + wh - 10 - 64
        reveal = 0.0 if not secrets else min(1.0, (t - 100) / 20.0)
        for k, (name, col, row, icn, secret) in enumerate(nodes):
            if secret and reveal <= 0:
                continue
            x, y = cx + col * 132 - 28, bottom - row * 116 - 28
            tile = Image.new("RGBA", (56, 56), (0, 0, 0, 0))
            tile.alpha_composite(node_frames[states[k]])
            ic = icn if states[k] else S.tinted(icn, (90, 90, 100), 0.5)
            tile.alpha_composite(ic, (28 - ic.width // 2, 28 - ic.height // 2))
            img.alpha_composite(S.faded(tile, reveal) if secret else tile, (x, y))
            if hover == k:
                d.rectangle([x, y, x + 55, y + 55], outline=(255, 255, 255))
            if k == 2 and 66 <= t < 96:
                img.alpha_composite(Image.new("RGBA", (56, 56), (255, 250, 222, int(150 * (1 - (t - 66) / 30)))), (x, y))
        if hover is not None:
            lines = tips[(hover, states[hover])]
            x, y = cx + nodes[hover][1] * 132 + 36, bottom - nodes[hover][2] * 116 - 10
            rendered = []
            for k, ln in enumerate(lines):
                if not ln:
                    rendered.append(None)
                    continue
                tag, body = (ln[0], ln[2:]) if len(ln) > 1 and ln[1] == "|" else ("T", ln)
                col = {"T": (223, 185, 78), "G": (140, 228, 88), "R": (236, 122, 88), "N": (138, 144, 150)}.get(tag, (238, 241, 243))
                rendered.append(S.text(body, 10, "plain", col, col, (21, 22, 28)))
            bw = max((r.width for r in rendered if r is not None), default=10) + 12
            bh = sum((r.height + 2) if r is not None else 6 for r in rendered) + 10
            x = min(x, W - bw - 4)
            d.rectangle([x, y, x + bw, y + bh], fill=(30, 28, 44), outline=(90, 58, 23))
            yy = y + 5
            for r in rendered:
                if r is None:
                    yy += 6
                    continue
                img.alpha_composite(r, (x + 6, yy))
                yy += r.height + 2
        if 66 <= t < 100:
            L.label(img, "Researched: Cogpunker", wx + 20, wy + wh + 6, size=11)
        if 100 <= t < 170:
            L.label(img, "(the Scrap Manual is read)  Knowledge expanded!", wx + 20, wy + wh + 6, size=11)
        if t % 3 == 0:
            frames.append(img)
    save(frames, path, scale=1)


def mechromancer_gif(path):
    """The Mechromancer under the floaty rules (2026-11-18; its own constants and the BossNPC drift's): no touch damage; with
    a ranged fighter it hangs KeepX to the side and KeepY above a point that follows them with a lag, swaying and bobbing;
    once they hold a blade it comes in close, a blade's reach from them, swaying a little. Its float frames from its sheet."""
    k = S.consts("Content/BloodMoon/NPCs/Mechromancer.cs", "Core/Templates/BossNPC.cs")
    sheet, kr = M.sheet_of("Content/BloodMoon/NPCs/Mechromancer", "Content/BloodMoon/NPCs/MechromancerRigData.cs")
    W, H, floor = 760, 320, 300
    bg = L.backdrop(W, H, floor)
    npc_w, npc_h = 40, 92
    px = 380.0
    nx, ny = px + k["KeepX"], floor - 21 - k["KeepY"]
    vx = vy = 0.0
    fx, fy = px, floor - 21.0
    clock = 0
    frames = []
    trail = []
    for t in range(600):
        melee = t >= 270
        run = 2.0 if 470 <= t < 560 else 0.0
        px = min(W - 60.0, px + run)
        tcx, tcy = px, floor - 21.0
        clock = (clock + 1) % int(k["DriftPeriodX"] * k["DriftPeriodY"])
        fx += (tcx - fx) * k["FocusFollow"]
        fy += (tcy - fy) * k["FocusFollow"]
        sway = math.sin(clock * 2 * math.pi / k["DriftPeriodX"])
        bob = math.sin(clock * 2 * math.pi / k["DriftPeriodY"] + math.pi / 2)
        side = -1.0 if nx < fx else 1.0
        if melee:
            gx = fx + side * (10 + k["MeleeGap"] + npc_w / 2 + sway * k["MeleeSwayX"])
            gy = fy + 21 - k["MeleeLift"] - npc_h / 2 + bob * k["MeleeBobY"]
            speed = k["MeleeFloatSpeed"]
        else:
            gx, gy = fx + side * k["KeepX"] + sway * k["SwayX"], fy - k["KeepY"] + bob * k["BobY"]
            speed = k["FloatSpeed"]
        dx, dy = gx - nx, gy - ny
        dist = math.hypot(dx, dy)
        want = (dx / dist * min(speed, dist * 0.08 + 0.4), dy / dist * min(speed, dist * 0.08 + 0.4)) if dist * dist > 64 else (0.0, 0.0)
        vx += (want[0] - vx) * k["FloatAccel"] * 4
        vy += (want[1] - vy) * k["FloatAccel"] * 4
        sp = math.hypot(vx, vy)
        if sp > speed:
            vx, vy = vx / sp * speed, vy / sp * speed
        nx, ny = nx + vx, ny + vy
        trail.append((nx, ny))
        trail = trail[-120:]
        if t % 3:
            continue
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        d = ImageDraw.Draw(img)
        for i, (qx, qy) in enumerate(trail[::4]):
            d.rectangle([int(qx) // 2 * 2, int(qy) // 2 * 2, int(qx) // 2 * 2 + 1, int(qy) // 2 * 2 + 1], fill=(124, 107, 224, 255))
        d.rectangle([int(gx) - 4, int(gy) - 4, int(gx) + 4, int(gy) + 4], outline=S.BRASS[4] + (255,))
        face_right = px > nx
        x, y = sheet.place(nx, ny + npc_h / 2, flip=face_right)
        img.alpha_composite(sheet.frame(kr["Float"] + (t // 8) % kr["FloatFrames"], flip=face_right), (int(x), int(y)))
        if melee:
            M.put_player(v, int(px), floor, frame=0 if run == 0 else 6 + (t // 3) % 14, flip=False)
            d.line([int(px) + 6, floor - 32, int(px) + 26, floor - 52], fill=(118, 220, 162, 255), width=3)    # a blade held up
        else:
            M.put_player(v, int(px), floor, frame=3 if run == 0 else 6 + (t // 3) % 14, flip=False)
        L.label(img, "MECHROMANCER, floaty: no touch damage; %s" % (
            "a melee fighter: it comes in close, a blade's reach away" if melee else "a ranged fighter: far, lagging, swaying and bobbing"), 6, 4)
        frames.append(img)
    save(frames, path, scale=1)


# ================================================================================================
# The sheet of new sprites
# ================================================================================================
def items_png(path):
    paths = [J + "Weapons/JadeCursedGlaives.png", J + "Weapons/IncenseMace.png", J + "Weapons/IncenseMaceHead.png", J + "Weapons/IncenseMaceChain.png",
             J + "Buffs/IncenseBlessing.png", J + "Buffs/IncenseBurntOut.png", "Content/Coghaven/Pets/JadeToken.png",
             "Content/Coghaven/Pets/JadeFoxBuff.png", "Content/Research/Items/AncientResearchBook.png", "Content/Research/Items/AncientResearchTable.png",
             J + "Items/JadeyBag.png", "Content/Bosses/TrashTr0m/Items/TetanusShot.png", "Content/Research/UI/ResearchKnowledge.png"]
    ims = [S.load(p) for p in paths]
    sc = 3
    w = sum(im.width * sc + 12 for im in ims) + 12
    h = max(im.height for im in ims) * sc + 24
    out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
    for row, bg in enumerate(((30, 30, 36), (196, 214, 232))):
        band = Image.new("RGBA", (w, h), bg + (255,))
        x = 12
        for im in ims:
            band.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (x, 12))
            x += im.width * sc + 12
        out.paste(band, (0, row * h))
    out.save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    # 2026-11-24: the glaives GIF is update_2026_11_24_sim.py --only glaive (the throw changed)
    jobs = (("glaive-frames", L.glaive_frames_png, "2026-11-18_jadey-glaives-frames.png"),
            ("turn", turn_gif, "2026-11-18_boss-jadey-turn.gif"), ("jadey", L.jadey_frames_gif, "2026-11-18_boss-jadey.gif"),
            ("statue", L.jadey_statue_gif, "2026-11-18_boss-jadey-statue.gif"), ("drift", L.drift_gif, "2026-11-18_floaty-drift.gif"),
            ("cakti", L.cakti_gif, "2026-11-18_weapon-cakti.gif"), ("mace", mace_gif, "2026-11-18_weapon-incense-mace.gif"),
            ("mechromancer", mechromancer_gif, "2026-11-18_bloodmoon-mechromancer-floaty.gif"),
            ("items", items_png, "2026-11-18_items.png"))
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(args.out, file))


if __name__ == "__main__":
    main()
