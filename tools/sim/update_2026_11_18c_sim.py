"""D5 proofs for the third request of 2026-11-18. Run from the repo root:

    python -P tools/sim/update_2026_11_18c_sim.py [--out docs/media] [--only research,bundle,tip,items]

Offline replays with the real sprites and the C# constants (read from the source files), 60 ticks a second, 3 ticks a GIF
frame (50 ms). Leaves out: lighting, tile collision, netcode, vanilla's own sprites (the vanilla item icons in the research
window, the Spear and the gem bolts are drawn here as stand-ins in their colours; the game draws its own).

    research   the research window at the game's UI size, its nodes and states read from ResearchNodes.cs: the main arch
               (Squire new at its top middle) with the secret nodes beside it (the Scrap Manual's on the right, Just the Tip
               and Bundle Up! on the left), half out of sight at first; the field dragged left, right, up and back (the view
               kept on the nodes by the same clamp as ResearchTreeView.ClampPan); hovering Just the Tip and Squire.
    bundle     the Bundle of Wands: three bursts at three target dummies (4, 10 and 18 tiles): five different gem bolts a
               burst, each at its staff's speed, with its damage (BundleOfWands.cs), more of them landing on the near dummy.
    tip        Just the Tip: a vanilla Spear (decompiled 1.4.4 Item 280 and AI_019_Spears type 49) thrust at a dummy up close
               (hit early in the thrust: 8) and at full reach (hit in the tip window: 10, +25%); a bar under it shows the
               spear's reach over the swing and the window.
    items      a sheet of the new sprites over dark and light backgrounds (a PNG).
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
from update_2026_11_18_sim import ICONS, ICON_COL, save  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
NODES_CS = "Content/Research/ResearchNodes.cs"
LOC = "Localization/en-US_Mods.Cogpunk.hjson"

STANDINS = dict(ICONS)
STANDINS["helm"] = ("...oooooo...", "..oSSSSSSo..", ".oSsSSSSSSo.", ".oSSdddSSSo.", "oSSdooodSSSo", "oSSo...oSSSo", "oSSdooodSSSo",
                    ".oSSSSSSSSo.", ".oBbBbBbBbo.", "..oooooooo..")
STANDINS["spear"] = ("..........oo", ".........oWo", "........oWSo", ".......oSSo.", "......owSo..", ".....owo....", "....owo.....",
                     "...owo......", "..owo.......", ".owo........", "owo.........", "oo..........")
STANDINS["banner"] = ("oooooooooooo", ".oCCCCCCCCo.", ".oCcCCCCcCo.", ".oCCCwwCCCo.", ".oCCwWWwCCo.", ".oCCCwwCCCo.", ".oCCCCCCCCo.",
                      ".oCcCCCCcCo.", ".oCCCooCCCo.", ".oCCo..oCCo.", ".ooo....ooo.")
ICON_OF = {"ItemID.CopperPickaxe": "pick", "ItemID.IronOre": "ore", "ItemID.HermesBoots": "boots", "ItemID.Diamond": "gem",
           "ItemID.SquireGreatHelm": "helm", "ItemID.Spear": "spear"}
MOD_ICON = {"BrassContainer": "Content/Mechanist/Accessories/BrassContainer.png", "TetanusShot": "Content/Bosses/TrashTr0m/Items/TetanusShot.png",
            "ScrapHelmet": "Content/Scrap/Armor/ScrapHelmet.png", "RustedCog": "Content/Scrap/Items/RustedCog.png",
            "Cakti": "Content/Desert/Weapons/Cakti.png", "BundleOfWands": "Content/Research/Weapons/BundleOfWands.png"}


def standin(name):
    rows = STANDINS[name]
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), ICON_COL[ch] + (255,))
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def fit(im, box=36):
    if im.width > box or im.height > box:
        k = max(im.width, im.height) / float(box)
        im = im.resize((max(1, int(im.width / k)), max(1, int(im.height / k))), Image.NEAREST)
    return im


def read_nodes():
    """[(name, column, row, cost, icon image, secret)] in registration order, from ResearchNodes.cs."""
    src = open(os.path.join(ROOT, NODES_CS), encoding="utf-8").read()
    consts = dict(re.findall(r'(\w+) = "(\w+)"', src))
    out = []
    for block in re.findall(r"Add\(new ResearchNode \{(.*?)\n\t\t\t\}\);", src, re.S):
        m = re.search(r"Name = (\w+), Column = (-?\d+), Row = (-?\d+), Cost = (\d+), IconItem = ([^,\n]+),", block)
        if not m:
            continue
        name = consts.get(m.group(1), m.group(1))
        icon_src = m.group(5).strip()
        if icon_src in ICON_OF:
            icon = standin(ICON_OF[icon_src])
        else:
            mm = re.search(r"\.(\w+)>\(\)", icon_src)
            icon = S.load(MOD_ICON[mm.group(1)]) if mm and mm.group(1) in MOD_ICON else standin("gem")
        out.append((name, int(m.group(2)), int(m.group(3)), int(m.group(4)), fit(icon), "Reveal =" in block))
    return out


def loc_nodes():
    src = open(os.path.join(ROOT, LOC), encoding="utf-8").read()
    names = {}
    for m in re.finditer(r'\n\t\t(\w+): \{\n\t\t\tDisplayName: "([^"]+)"\n\t\t\tDescription: "([^"]+)"', src):
        names[m.group(1)] = (m.group(2), m.group(3))
    return names


# ================================================================================================
# The research window
# ================================================================================================
def research_gif(path):
    k = S.consts("Content/Research/UI/ResearchUIState.cs")
    sx, sy, ns, bm, margin = k["SpacingX"], k["SpacingY"], int(k["NodeSize"]), k["BottomMargin"], k["PanMargin"]
    nodes = read_nodes()
    names = loc_nodes()
    frames_img = S.load("Content/Research/UI/ResearchNode.png")
    node_frames = [frames_img.crop((0, q * 58, 56, q * 58 + 56)) for q in range(3)]
    sign = S.load("Content/Research/UI/ResearchKnowledge.png")
    state = {"TheBasics": 2, "MineAndCraft": 2, "Cogpunker": 2, "Jogger": 1, "GemPower": 0, "Squire": 1, "CausesAutism": 0,
             "InACaveWithScraps": 2, "HitTheJoints": 0, "Mandacaru": 1, "JustTheTip": 1, "BundleUp": 0}
    W, H = 800, 600
    wx, wy, ww, wh = 20, 20, 760, 540
    ax0, ay0, ax1, ay1 = wx + 10, wy + 46, wx + ww - 10, wy + wh - 10           # the tree's field
    aw, ah = ax1 - ax0, ay1 - ay0
    rng = random.Random(1118)
    stars = [(rng.randrange(2048), rng.randrange(2048), rng.randrange(4)) for _ in range(260)]
    minc, maxc = min(n[1] for n in nodes), max(n[1] for n in nodes)
    minr, maxr = min(min(n[2] for n in nodes), 0), max(n[2] for n in nodes)

    def clamp(px, py):                                   # ResearchTreeView.ClampPan
        half = ns / 2.0
        x0, x1 = minc * sx - half, maxc * sx + half
        ytop, ybot = ah - bm - maxr * sy - half, ah - bm - minr * sy + half
        a, b = aw / 2.0 - margin - x1, -aw / 2.0 + margin - x0
        c, e = margin - ytop, ah - margin - ybot
        return max(min(a, b), min(max(a, b), px)), max(min(c, e), min(max(c, e), py))

    def rect(n, pan):
        cx = ax0 + aw / 2.0 + pan[0]
        bottom = ay0 + ah - bm + pan[1]
        return int(round(cx + n[1] * sx - ns / 2.0)), int(round(bottom - n[2] * sy - ns / 2.0))

    # (tick, mouse x, mouse y, pressed): a drag left, right, up, back; then hovers
    keys = [(0, 600, 470, False), (30, 600, 470, False), (36, 600, 470, True), (80, 420, 470, True), (86, 420, 470, False),
            (100, 250, 470, False), (106, 250, 470, True), (160, 600, 440, True), (166, 600, 440, False), (176, 400, 300, False),
            (182, 400, 300, True), (214, 400, 380, True), (232, 400, 300, True), (236, 400, 300, False)]

    def mouse(t):
        for (t0, x0, y0, p0), (t1, x1, y1, _) in zip(keys, keys[1:]):
            if t0 <= t < t1:
                u = (t - t0) / float(t1 - t0)
                return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, p0
        return keys[-1][1], keys[-1][2], keys[-1][3]

    tips = {
        "JustTheTip": [("T", names["JustTheTip"][0]), ("W", names["JustTheTip"][1]), ("", ""), ("G", "Costs 1 knowledge point(s) (you have 2)"),
                       ("G", "Research The Basics first"), ("", ""), ("G", "Click to research")],
        "Squire": [("T", names["Squire"][0]), ("W", names["Squire"][1]), ("", ""), ("G", "Research The Basics first"),
                   ("G", "Takes 1 Zombie, Slime or Demon Eye Banner (you have 1)"), ("", ""), ("G", "Click to research")],
    }
    pan = (0.0, 0.0)
    press_at, press_pan, pressing, moved = None, pan, False, False
    hover_plan = [(240, 300, "JustTheTip"), (300, 380, "Squire")]
    frames = []
    for t in range(380):
        mx, my, down = mouse(t)
        hover_name = None
        for (t0, t1, nm) in hover_plan:
            if t0 <= t < t1:
                hover_name = nm
        if hover_name is not None and not down:          # glide to the node being shown
            n = next(n for n in nodes if n[0] == hover_name)
            if t in (240, 300):
                pan = clamp(*((-n[1] * sx * 0.7, 0.0) if hover_name == "JustTheTip" else (0.0, 0.0)))
            x, y = rect(n, pan)
            mx, my = x + ns * 0.6, y + ns * 0.55
        if down and not pressing:
            pressing, press_at, press_pan, moved = True, (mx, my), pan, False
        if pressing:
            if not down:
                pressing = False
            else:
                dx, dy = mx - press_at[0], my - press_at[1]
                if dx * dx + dy * dy > k["DragThreshold"] ** 2:
                    moved = True
                if moved:
                    pan = (press_pan[0] + dx, press_pan[1] + dy)
        pan = clamp(*pan)
        if t % 3:
            continue
        img = Image.new("RGBA", (W, H), (40, 40, 48, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([wx, wy, wx + ww, wy + wh], fill=(21, 22, 28))
        d.rectangle([wx + 2, wy + 2, wx + ww - 2, wy + wh - 2], fill=(90, 58, 23))
        d.rectangle([wx + 4, wy + 4, wx + ww - 4, wy + wh - 4], fill=(184, 138, 51))
        d.rectangle([wx + 8, wy + 8, wx + ww - 8, wy + wh - 8], fill=(21, 22, 28))
        d.rectangle([wx + 10, wy + 10, wx + ww - 10, wy + wh - 10], fill=(24, 20, 36))
        title = S.text("Ancient Research", 16, "title")
        img.alpha_composite(title, (wx + ww // 2 - title.width // 2, wy + 12))
        img.alpha_composite(sign, (wx + 18, wy + 12))
        num = S.text("2", 16, "title", (196, 250, 214), (118, 220, 162), (10, 34, 32))
        img.alpha_composite(num, (wx + 18 + sign.width + 8, wy + 13))
        field = Image.new("RGBA", (aw, ah), (18, 16, 30, 255))
        fd = ImageDraw.Draw(field)
        ox, oy = int(pan[0] * 0.3), int(pan[1] * 0.3)
        for (sx0, sy0, sh) in stars:
            c = ((46, 50, 59), (70, 58, 147), (127, 135, 148), (198, 189, 255))[sh]
            s = 4 if sh == 3 else 2
            fd.rectangle([(sx0 + ox) % aw, (sy0 + oy) % ah, (sx0 + ox) % aw + s - 1, (sy0 + oy) % ah + s - 1], fill=c)
        hovered = None
        for n in nodes:
            x, y = rect(n, pan)
            tile = Image.new("RGBA", (ns, ns), (0, 0, 0, 0))
            st = state.get(n[0], 0)
            tile.alpha_composite(node_frames[st])
            ic = n[4] if st else S.tinted(n[4], (90, 90, 100), 0.5)
            tile.alpha_composite(ic, (ns // 2 - ic.width // 2, ns // 2 - ic.height // 2))
            field.alpha_composite(tile, (x - ax0, y - ay0)) if (-ns < x - ax0 < aw and -ns < y - ay0 < ah) else None
            if x <= mx < x + ns and y <= my < y + ns and not (pressing and moved):
                hovered = n
                fd.rectangle([x - ax0, y - ay0, x - ax0 + ns - 1, y - ay0 + ns - 1], outline=(255, 255, 255))
        hint = S.text("Drag to look around", 10, "plain", (138, 144, 150), (138, 144, 150), (21, 22, 28))
        field.alpha_composite(hint, (10, ah - 24))
        img.alpha_composite(field, (ax0, ay0))
        if hovered is not None and hovered[0] in tips:
            rendered = []
            for tag, line in tips[hovered[0]]:
                col = {"T": (223, 185, 78), "G": (140, 228, 88), "W": (238, 241, 243)}.get(tag)
                rendered.append(S.text(line, 10, "plain", col, col, (21, 22, 28)) if line else None)
            bw = max(r.width for r in rendered if r is not None) + 12
            bh = sum((r.height + 2) if r is not None else 6 for r in rendered) + 10
            tx, ty = min(int(mx) + 14, W - bw - 4), min(int(my) + 10, H - bh - 4)
            d.rectangle([tx, ty, tx + bw, ty + bh], fill=(30, 28, 44), outline=(90, 58, 23))
            yy = ty + 5
            for r in rendered:
                if r is None:
                    yy += 6
                    continue
                img.alpha_composite(r, (tx + 6, yy))
                yy += r.height + 2
        # the cursor: an arrow, a fist while dragging
        cx_, cy_ = int(mx), int(my)
        if pressing and moved:
            d.rectangle([cx_ - 5, cy_ - 5, cx_ + 5, cy_ + 5], fill=(238, 241, 243), outline=(21, 22, 28))
        else:
            d.polygon([(cx_, cy_), (cx_, cy_ + 14), (cx_ + 4, cy_ + 10), (cx_ + 10, cy_ + 10)], fill=(238, 241, 243), outline=(21, 22, 28))
        cap = "drag: the view follows" if pressing and moved else ("hover: " + names[hovered[0]][0] if hovered is not None else
                                                                  "secret nodes beside the arch (left: the world's, right: the Scrap Manual's)")
        L.label(img, cap, wx + 20, wy + wh + 10, size=11)
        frames.append(img)
    save(frames, path, scale=1)


# ================================================================================================
# The Bundle of Wands
# ================================================================================================
GEM_COL = [(184, 58, 190), (223, 185, 78), (96, 122, 172), (78, 212, 106), (206, 74, 56), (224, 230, 236), (236, 113, 40)]


def bundle_gif(path):
    k = S.consts("Content/Research/Weapons/BundleOfWands.cs")
    src = open(os.path.join(ROOT, "Content/Research/Weapons/BundleOfWands.cs"), encoding="utf-8").read()
    speeds = [float(v) for v in re.search(r"boltSpeeds = \{([^}]*)\}", src).group(1).replace("f", "").split(",")]
    sdmg = [int(v) for v in re.search(r"staffDamage = \{([^}]*)\}", src).group(1).split(",")]
    sprite = S.load("Content/Research/Weapons/BundleOfWands.png")
    W, H, floor = 640, 240, 216
    bg = L.backdrop(W, H, floor)
    px = 50
    muzzle = (px + 6 + k["MuzzleOffset"], floor - 30)
    shots = [(10, 4), (80, 10), (150, 18)]                 # (tick, dummy distance from the gems in tiles)
    rng = random.Random(5)
    bolts, numbers, frames = [], [], []
    tally = {}
    for t in range(230):
        shot = max((s0 for s0 in shots if s0[0] <= t), key=lambda q: q[0], default=shots[0])
        dummy = muzzle[0] + shot[1] * 16
        if t == shot[0]:
            order = list(range(7))
            rng.shuffle(order)
            tally[shot[1]] = 0
            for g in order[:int(k["Bolts"])]:
                ang = math.radians(rng.uniform(-k["SpreadDegrees"], k["SpreadDegrees"]))
                v = speeds[g] * rng.uniform(0.94, 1.06)
                dmg = max(1, int(round(k["Damage"] * sdmg[g] / k["AverageStaffDamage"])))
                bolts.append([muzzle[0], muzzle[1], v * math.cos(ang), v * math.sin(ang), g, dmg, [], False, shot[1]])
        for b in bolts:
            b[0] += b[2]
            b[1] += b[3]
            b[6].append((b[0], b[1]))
            b[6] = b[6][-5:]
            d_x = muzzle[0] + b[8] * 16
            if not b[7] and abs(b[0] - d_x) < 9 and floor - 52 < b[1] < floor:
                b[7] = True
                tally[b[8]] = tally.get(b[8], 0) + 1
                numbers.append((d_x - 24 + 12 * (tally[b[8]] - 1), floor - 58, b[5], t, GEM_COL[b[4]]))
        bolts = [b for b in bolts if -20 < b[0] < W + 20 and 0 < b[1] < floor and not b[7]]
        if t % 3:
            continue
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        d = ImageDraw.Draw(img)
        d.rectangle([dummy - 8, floor - 44, dummy + 8, floor - 2], fill=(110, 60, 30), outline=(40, 21, 14))
        d.rectangle([dummy - 4, floor - 52, dummy + 4, floor - 44], fill=(146, 86, 42), outline=(40, 21, 14))
        hand = M.put_player(v, px, floor, frame=3, flip=False)
        rimg, piv = M.rotated(sprite, 0.0, (12, sprite.height // 2))
        img.alpha_composite(rimg, (int(hand[0] - piv[0]), int(hand[1] - piv[1])))
        for b in bolts:
            col = GEM_COL[b[4]]
            for q, (tx, ty) in enumerate(b[6][:-1]):
                d.rectangle([int(tx) - 1, int(ty) - 1, int(tx) + 1, int(ty) + 1], fill=col + (int(70 + 40 * q),))
            x, y = int(b[0]), int(b[1])
            d.polygon([(x, y - 4), (x + 4, y), (x, y + 4), (x - 4, y)], fill=col, outline=(21, 22, 28))
        for (nx, ny, val, t0, col) in numbers:
            age = t - t0
            if 0 <= age < 40:
                tx = S.text(str(val), 11, "plain", col, col, (21, 22, 28))
                img.alpha_composite(S.faded(tx, min(1.0, (40 - age) / 12.0)), (int(nx - tx.width // 2), int(ny - age * 0.9)))
        L.label(img, "BUNDLE OF WANDS: five different gem bolts a burst (28 mana, 40 ticks)", 6, 4)
        L.label(img, "dummy %d tiles away: %d of 5 bolts hit" % (shot[1], tally.get(shot[1], 0)), 6, 20)
        frames.append(img)
    save(frames, path, scale=1)


# ================================================================================================
# Just the Tip
# ================================================================================================
def tip_gif(path):
    # decompiled 1.4.4: Item 280 (the Spear): useAnimation 31, shootSpeed 3.7, damage 8; AI_019_Spears type 49: num4 4,
    # num5 0.85 (out a tick), num6 1.1 (back a tick); the projectile's centre at velocity x num9 from the hand
    kn = S.consts("Content/Research/ResearchNodes.cs")
    max_a, speed, base_dmg = 31, 3.7, 8
    turn = max_a // 3

    def reach(a):
        n2 = min(a, turn)
        n3 = a - n2
        n7 = (max_a - turn) - n3
        n8 = turn - n2
        return speed * (4.0 + 0.85 * n7 - 1.1 * n8)

    def in_tip(a):
        return turn - kn["TipReturnFrames"] <= a < turn + kn["TipThrustFrames"]

    W, H, floor = 520, 260, 200
    bg = L.backdrop(W, H, floor)
    frames = []
    # the far dummy where the spear first touches it in the window's first frame (the tip: centre + 16 px, the dummy 8 px wide)
    far = int(reach(turn + int(kn["TipThrustFrames"]) - 1) + 24) - 1
    scenes = [(0, 150, 48, "up close: hit early in the thrust"), (150, 300, far, "at full reach: hit at the tip (+25%)")]
    for t in range(300):
        scene = next(s for s in scenes if s[0] <= t < s[1])
        local = t - scene[0]
        a = max_a - (local - 20) if 20 <= local < 20 + max_a else None
        px = 140
        dummy = px + scene[2]
        if t % 3:
            continue
        img = bg.copy()
        v = S.View(W / 2, H / 2)
        v.img, v.x0, v.y0 = img, 0, 0
        d = ImageDraw.Draw(img)
        d.rectangle([dummy - 8, floor - 44, dummy + 8, floor - 2], fill=(110, 60, 30), outline=(40, 21, 14))
        d.rectangle([dummy - 4, floor - 52, dummy + 4, floor - 44], fill=(146, 86, 42), outline=(40, 21, 14))
        hand = M.put_player(v, px, floor, frame=3, flip=False)
        hy = floor - 30
        if a is not None:
            r = reach(a)
            tip_x = px + r + 16
            d.line([px + 2, hy, tip_x - 6, hy], fill=(146, 86, 42), width=3)
            d.polygon([(tip_x - 7, hy - 4), (tip_x, hy), (tip_x - 7, hy + 4)], fill=(183, 191, 202), outline=(21, 22, 28))
        # the hit: the first frame the spear's tip reaches the dummy (once a thrust)
        hit_age, hit_val, hit_tip = None, None, False
        for back in range(local + 1):
            aa = max_a - (back - 20) if 20 <= back < 20 + max_a else None
            if aa is not None and px + reach(aa) + 16 >= dummy - 8:
                hit_age = local - back
                hit_tip = in_tip(aa)
                hit_val = int(round(base_dmg * (1 + kn["JustTheTipBonus"]))) if hit_tip else base_dmg
                break
        if hit_age is not None and hit_age < 40:
            col = (255, 199, 90) if hit_tip else (238, 241, 243)
            tx = S.text(str(hit_val) + ("  TIP!" if hit_tip else ""), 12, "plain", col, col, (21, 22, 28))
            img.alpha_composite(S.faded(tx, min(1.0, (40 - hit_age) / 12.0)), (dummy - tx.width // 2, int(floor - 64 - hit_age * 0.8)))
        # the reach over the swing: a bar of the 31 frames, the tip window lit, the current frame marked
        bx, by = 40, floor + 22
        for f in range(max_a):
            aa = max_a - f
            hgt = int(reach(aa) / 3)
            c = (223, 185, 78) if in_tip(aa) else (79, 85, 98)
            d.rectangle([bx + f * 14, by + 30 - hgt, bx + f * 14 + 10, by + 30], fill=c)
            if a is not None and aa == a:
                d.rectangle([bx + f * 14 - 1, by + 30 - hgt - 1, bx + f * 14 + 11, by + 31], outline=(238, 241, 243))
        L.label(img, "JUST THE TIP: " + scene[3], 6, 4)
        L.label(img, "reach over the thrust (gold: the last 3 frames out + the first back)", bx, by + 32, size=8)
        frames.append(img)
    save(frames, path, scale=1)


# ================================================================================================
# The sheet of new sprites
# ================================================================================================
def items_png(path):
    paths = ["Content/Research/Weapons/BundleOfWands.png", "Content/Coghaven/Pets/JadeFoxBuff.png"]
    ims = [S.load(p) for p in paths]
    fox = S.load("Content/Coghaven/Pets/JadeFoxPet.png")
    fh = fox.height // 21
    ims.append(fox.crop((0, 0, fox.width, fh)))
    sc = 3
    w = sum(im.width * sc + 12 for im in ims) + 12
    h = max(im.height for im in ims) * sc + 24
    out = Image.new("RGBA", (w, h * 2), (0, 0, 0, 255))
    for row, bgc in enumerate(((30, 30, 36), (196, 214, 232))):
        band = Image.new("RGBA", (w, h), bgc + (255,))
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
    jobs = (("research", research_gif, "2026-11-18_research-menu.gif"), ("bundle", bundle_gif, "2026-11-18_research-bundle-of-wands.gif"),
            ("tip", tip_gif, "2026-11-18_research-just-the-tip.gif"), ("items", items_png, "2026-11-18_items-c.png"))
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(args.out, file))


if __name__ == "__main__":
    main()
