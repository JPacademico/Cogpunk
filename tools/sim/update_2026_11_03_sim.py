"""D5 proofs for the content of 2026-11-03: the Coghawk (Content/Desert), the Splasher (Content/Rain) and the Rusted Nail
(Content/Underground), built from the real sprite sheets, the generated rig data and the constants parsed out of the C#
files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_03_sim.py --out docs/media [--only sprites,coghawk,splasher,nail]

Writes:
    2026-11-03_enemies-sprites.png         every frame of the Coghawk and the Splasher (their planes composited at the rig
                                           origin), the water glob's headings and the Rusted Nail, at 2x on a dark and a
                                           light background.
    2026-11-03_desert-coghawk.gif          the Coghawk circling (flap loop), the telegraph (a screech, wings flared, flying to
                                           the top of its arc), the swoop (Coghawk.DoSwoop's parabola, steered a tick ahead);
                                           the first time the player jumps and it passes under them, the second time they
                                           stand and take the talons. Its hitbox is outlined during the swoops.
    2026-11-03_rain-splasher.gif           the Splasher walking in through the rain, stopping 12 tiles off, pumping its gun
                                           (the telegraph) and firing a burst of four globs lobbed onto the player
                                           (SplasherWater.AimAt), Wet on a hit; a second burst after the cooldown.
    2026-11-03_underground-rusted-nail.gif a Rust Collector rams a player wearing the Rusted Nail: it takes 30 and Tetanus and
                                           is knocked back; its second ram, under Tetanus, takes 33 (+10%).

Leaves out: lighting, tile collision beyond a flat floor, the player's own movement beyond the scripted jump, vanilla's
exact knockback and immunity frames (approximated), spawning, netcode. Numbers are Expert's.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, frames, player_sprite, collector_sprite, TPF  # noqa: E402

KH = consts("Content/Desert/NPCs/Coghawk.cs", "Content/Desert/NPCs/CoghawkRigData.cs")
KS = consts("Content/Rain/NPCs/Splasher.cs", "Content/Rain/NPCs/SplasherRigData.cs")
KW = consts("Content/Rain/Projectiles/SplasherWater.cs")
KN = consts("Content/Underground/Items/RustedNail.cs", "Content/Bosses/TrashTr0m/Buffs/TetanusDebuff.cs")
KR = consts("Content/Junkyard/NPCs/RustCollector.cs")
EMBER = (255, 199, 90)
HURT = (255, 90, 70)
STEAM = (238, 241, 243)
AETHER = (198, 189, 255)
RUST = (233, 160, 107)


class Planes:
    """A grid enemy's sheets: far, middle, near and glow cells drawn at the origin, mirrored when it faces right (the
    art faces left), like DepthLayers.DrawWalker (parallax left out)."""

    def __init__(self, base, k):
        self.k = k
        self.sheets = [load(base + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]

    def draw(self, img, frame, anchor, face_right):
        cw, ch, ox, oy = self.k["CellWidth"], self.k["CellHeight"], self.k["OriginX"], self.k["OriginY"]
        for sheet in self.sheets:
            cell = sheet.crop((0, frame * (ch + 2), cw, frame * (ch + 2) + ch))
            if face_right:
                cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(cell, (int(round(anchor[0] - (cw - ox))), int(round(anchor[1] - oy))))
            else:
                img.alpha_composite(cell, (int(round(anchor[0] - ox)), int(round(anchor[1] - oy))))


def numbers(gif, img, pops, tick):
    for (t0, x, y, s, col) in pops:
        if 0 <= tick - t0 < 45:
            gif.text(img, (int(x), int(y - (tick - t0) // 2)), s, fill=col, font=gif.big)


# ================================================================================================
# Coghawk
# ================================================================================================
def scene_coghawk(out, font):
    W, H, G = 760, 400, 350
    bg = backdrop(W, H, G, sky=((236, 208, 160), (214, 168, 112)), dirt=(206, 170, 110))
    gif = Gif(font, (W, H), scale=1.2)
    hawk = Planes("Content/Desert/NPCs/Coghawk", KH)
    player = player_sprite()
    px = 300.0                                                # the player's centre x; feet on the ground at G
    py_feet, pvy = float(G), 0.0
    jump_t = -1
    hx, hy = 560.0, G - 13.0 - KH["HoverHeight"]             # the hawk's centre
    vx = vy = 0.0
    state, timer = "hover", KH["SwoopCooldown"] - 40
    ai2 = ai3 = 0.0
    swoops, pops = 0, []
    hit_this_swoop, dodge_shown = False, -99
    total = 6 * 60 + 40
    for tick in range(total):
        timer += 1
        pcx, pcy = px, py_feet - 21.0
        if state == "hover":
            side = 1.0 if hx >= px else -1.0
            gx, gy = px + side * KH["HoverSide"], pcy - KH["HoverHeight"] + math.sin(timer * 0.05) * 12.0
            dx, dy = gx - hx, gy - hy
            d = math.hypot(dx, dy) or 1.0
            wx, wy = dx / d * KH["HoverSpeed"], dy / d * KH["HoverSpeed"]
            vx += (wx - vx) * KH["HoverAccel"]
            vy += (wy - vy) * KH["HoverAccel"]
            face = 1 if px >= hx else -1
            if timer >= KH["SwoopCooldown"]:
                state, timer = "windup", 0
                ai2 = 1.0 if px >= hx else -1.0
        elif state == "windup":
            direction = 1 if ai2 >= 0 else -1
            lx, ly = px, G - KH["SkimHeight"] - KH["Height"] / 2.0
            sx, sy = lx - direction * KH["SwoopHalfWidth"], ly - KH["SwoopDepth"]
            dx, dy = sx - hx, sy - hy
            d = math.hypot(dx, dy) or 1.0
            sp = min(KH["HoverSpeed"] * 1.6, d * 0.2)
            vx += (dx / d * sp - vx) * 0.2
            vy += (dy / d * sp - vy) * 0.2
            face = direction
            if timer >= KH["WindupTicks"]:
                state, timer = "swoop", 0
                ai2, ai3 = direction * lx, ly
                swoops += 1
                hit_this_swoop = False
        elif state == "swoop":
            direction = 1 if ai2 >= 0 else -1
            lx, ly = abs(ai2), ai3
            u = min(1.0, (timer + 1.0) / KH["SwoopTicks"])
            s = 2.0 * u - 1.0
            nx, ny = lx + direction * KH["SwoopHalfWidth"] * s, ly - KH["SwoopDepth"] * s * s
            sx, sy = nx - hx, ny - hy
            ln = math.hypot(sx, sy)
            if ln > KH["SwoopMaxSpeed"]:
                sx, sy = sx / ln * KH["SwoopMaxSpeed"], sy / ln * KH["SwoopMaxSpeed"]
            vx, vy = sx, sy
            face = direction
            if swoops == 1 and timer == KH["SwoopTicks"] // 2 - 12 and jump_t < 0:
                jump_t, pvy = 0, -5.01                        # the player jumps 12 ticks before the low point
            if timer >= KH["SwoopTicks"]:
                state, timer = "recover", 0
        else:
            vx *= 0.97
            vy = max(vy - 0.3, -KH["HoverSpeed"])
            face = 1 if vx > 0 else -1
            if timer >= KH["RecoverTicks"]:
                state, timer = "hover", 0
        hx += vx
        hy += vy
        # the player's jump: vanilla holds jumpSpeed 5.01 for 15 ticks, then gravity 0.4 (decompiled Player.JumpMovement)
        if jump_t >= 0:
            jump_t += 1
            if jump_t > 15:
                pvy = min(pvy + 0.4, 10.0)
            py_feet += pvy
            if py_feet >= G:
                py_feet, pvy, jump_t = float(G), 0.0, -2
        hb = (hx - KH["Width"] / 2, hy - KH["Height"] / 2, hx + KH["Width"] / 2, hy + KH["Height"] / 2)
        pb = (px - 10, py_feet - 42, px + 10, py_feet)
        overlap = hb[0] < pb[2] and hb[2] > pb[0] and hb[1] < pb[3] and hb[3] > pb[1]
        if state == "swoop" and overlap and not hit_this_swoop:
            hit_this_swoop = True
            pops.append((tick, px - 10, py_feet - 70, str(KH["ContactDamage"]), HURT))
        if state == "swoop" and swoops == 1 and abs(hx - px) < 8 and not overlap and dodge_shown < 0:
            dodge_shown = tick
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        if state == "windup":
            frame = KH["Screech"] + (timer // KH["ScreechTicks"]) % KH["ScreechFrames"]
        elif state == "swoop":
            frame = KH["Dive"] if vy > 2 else (KH["Climb"] if vy < -2 else KH["Skim"])
        elif state == "recover":
            frame = KH["Flap"] + (timer // (KH["FlapTicks"] - 2)) % KH["FlapFrames"]
        else:
            frame = KH["Glide"] if vy > 1.2 else KH["Flap"] + (timer // KH["FlapTicks"]) % KH["FlapFrames"]
        img.alpha_composite(player, (int(px - 20), int(py_feet - 42 - 14)))
        hawk.draw(img, frame, (hx, hy + KH["Height"] / 2), face > 0)
        if state == "swoop":
            d.rectangle(hb, outline=(255, 40, 40, 255))
            if swoops == 1 and 0 <= tick - dodge_shown < 60:
                gif.text(img, (int(px) - 30, int(py_feet) - 130), "dodged!", fill=AETHER, font=gif.big)
        if state == "windup":
            gif.text(img, (int(hx) - 50, int(hy) - 56), "SCREECH (%d ticks)" % (KH["WindupTicks"] - timer), fill=EMBER)
        numbers(gif, img, pops, tick)
        gif.text(img, (10, 8), "Coghawk: circles 10 tiles over its target; every %.1f s a %d-tick screech, then a %d-tick swoop" % (
            KH["SwoopCooldown"] / 60, KH["WindupTicks"], KH["SwoopTicks"]))
        gif.text(img, (10, 28), ("swoop 1: the player jumps, it skims %d px over the sand and passes under" % KH["SkimHeight"]) if swoops <= 1 else
                 "swoop 2: the player stands: %d damage (Expert; the Vulture's 30 +20%%), %d life, %d defense" % (
                     KH["ContactDamage"], KH["Life"], KH["Defense"]))
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Splasher
# ================================================================================================
def water_aim(frm, to):
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    t = max(14.0, min(40.0, abs(dx) / 9.0))
    vx = dx / t
    vy = (dy - 0.5 * KW["Gravity"] * t * t) / t
    return max(-11.0, min(11.0, vx)), max(-10.0, min(8.0, vy))


def rain_layer(w, h, tick):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for k in range(70):
        x = (k * 97 + tick * 3) % (w + 60) - 30
        y = (k * 53 + tick * 9) % h
        d.line([x, y, x - 3, y + 10], fill=(200, 215, 235, 140), width=1)
    return img


def scene_splasher(out, font):
    W, H, G = 720, 340, 290
    bg = backdrop(W, H, G, sky=((90, 104, 128), (60, 70, 92)), dirt=(96, 84, 64))
    gif = Gif(font, (W, H), scale=1.2)
    bot = Planes("Content/Rain/NPCs/Splasher", KS)
    water = frames("Content/Rain/Projectiles/SplasherWater.png", 20, 20, 22, 16)
    player = player_sprite()
    px = 150.0
    sx, svx = 430.0, 0.0
    state, timer, cooldown = "walk", 0, 0
    walked = 0.0
    globs, pops, wet = [], [], -999
    for tick in range(int(6.2 * 60)):
        timer += 1
        if cooldown > 0:
            cooldown -= 1
        dx = px - sx
        direction = -1 if dx < 0 else 1
        if state == "walk":
            close = abs(dx) < KS["StandRange"]
            want = 0.0 if close else direction * KS["WalkSpeed"]
            svx = min(want, svx + KS["WalkAccel"]) if svx < want else max(want, svx - KS["WalkAccel"])
            if cooldown <= 0 and abs(dx) < KS["ShootRange"]:
                state, timer = "aim", 0
        elif state == "aim":
            svx = max(0.0, abs(svx) - KS["WalkAccel"] * 2) * (1 if svx > 0 else -1)
            if timer >= KS["AimTicks"]:
                state, timer = "shoot", 0
        else:
            svx = 0.0
            if (timer - 1) % KS["BurstInterval"] == 0 and timer <= KS["BurstShots"] * KS["BurstInterval"]:
                frm = (sx + KS["MuzzleX"] * -direction, G + KS["MuzzleY"])
                vx, vy = water_aim(frm, (px, G - 21))
                a = ((timer // KS["BurstInterval"]) % 3 - 1) * KS["ShotSpread"]
                vx, vy = vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)
                globs.append([frm[0], frm[1], vx, vy])
            if timer >= KS["ShootTicks"]:
                state, timer, cooldown = "walk", 0, KS["ShotCooldown"]
        sx += svx
        walked += abs(svx)
        for g in list(globs):
            g[3] = min(g[3] + KW["Gravity"], 12.0)
            g[0] += g[2]
            g[1] += g[3]
            if px - 10 < g[0] < px + 10 and G - 42 < g[1] < G:
                pops.append((tick, px - 10, G - 80, str(KS["WaterDamage"]), HURT))
                wet = tick
                globs.remove(g)
            elif g[1] >= G:
                globs.remove(g)
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "aim":
            frame = KS["Aim"] + (timer // 8) % 2
        elif state == "shoot":
            since = (timer - 1) % KS["BurstInterval"]
            frame = KS["Shoot"] if timer <= KS["BurstShots"] * KS["BurstInterval"] + 1 and since < 3 else KS["Shoot"] + 1
        elif abs(svx) > 0.15:
            frame = KS["Walk"] + int(walked / KS["WalkAnimDistance"]) % KS["WalkFrames"]
        else:
            frame = KS["Idle"] + (tick // 24) % 2
        img.alpha_composite(player, (int(px - 20), int(G - 42 - 14)))
        bot.draw(img, frame, (sx, G), direction > 0)
        for g in globs:
            h = int(round(math.atan2(g[3], g[2]) / (2 * math.pi) * 16)) % 16
            img.alpha_composite(water[h], (int(g[0] - 10), int(g[1] - 10)))
        img.alpha_composite(rain_layer(W, H, tick))
        if 0 <= tick - wet < 120:
            gif.text(img, (int(px) - 16, G - 110), "Wet", fill=(140, 190, 255))
        if state == "aim":
            gif.text(img, (int(sx) - 60, G - 120), "pumping (%d ticks)" % (KS["AimTicks"] - timer), fill=EMBER)
        numbers(gif, img, pops, tick)
        d = ImageDraw.Draw(img)
        d.line([px, G + 16, px + KS["StandRange"], G + 16], fill=(195, 200, 205, 255))
        gif.text(img, (int(px + KS["StandRange"]) - 60, G + 20), "stands off at %d tiles" % (KS["StandRange"] // 16), fill=(195, 200, 205))
        gif.text(img, (10, 8), "Splasher (rain only): walks in, keeps %d tiles off, pumps its gun %d ticks, fires %d globs %d ticks apart" % (
            KS["StandRange"] // 16, KS["AimTicks"], KS["BurstShots"], KS["BurstInterval"]))
        gif.text(img, (10, 28), "each glob %d (Expert), lobbed onto the target, Wet on a hit; every %.0f s; %d life, %d defense" % (
            KS["WaterDamage"], KS["ShotCooldown"] / 60, KS["Life"], KS["Defense"]))
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Rusted Nail
# ================================================================================================
def scene_nail(out, font):
    W, H, G = 640, 300, 250
    bg = backdrop(W, H, G, sky=((52, 46, 54), (34, 30, 38)), dirt=(84, 70, 58))
    gif = Gif(font, (W, H), scale=1.4)
    nail = load("Content/Underground/Items/RustedNail.png")
    player = player_sprite()
    rc = collector_sprite()
    px = 170.0
    cx, cvx, cvy, cy = 520.0, 0.0, 0.0, float(G - rc.height)
    tetanus_until, pops, rams, cooldown = -1, [], 0, 0
    for tick in range(int(5.4 * 60)):
        if cooldown > 0:
            cooldown -= 1
        if cooldown == 0 and cvy == 0.0:
            cvx = max(-KR["MaxSpeed"], cvx - KR["MaxAccel"])  # it charges at the player (RustCollector's top acceleration)
        elif cvy == 0.0:
            cvx *= 0.88                                       # skidding to a stop after the knockback
        cvy = cvy + 0.3 if cy < G - rc.height or cvy < 0 else 0.0
        cx += cvx
        cy = min(G - rc.height, cy + cvy)
        if cy >= G - rc.height and cvy > 0:
            cvy = 0.0
        if cx < px + 10 and cooldown == 0:                    # the ram lands: the player is hurt, the nail bites back
            rams += 1
            pops.append((tick, px - 14, G - 80, str(KR.get("ContactDamage", 25)), HURT))
            dmg = KN["ThornDamage"] if tick >= tetanus_until else int(KN["ThornDamage"] * KN["DamageTakenMultiplier"])
            pops.append((tick, cx + 8, G - 70, str(dmg), RUST))
            tetanus_until = tick + KN["TetanusTicks"]
            cvx, cvy = 7.0, -4.0                              # vanilla's thorns knockback (10), approximated
            cooldown = 50
        if tick % TPF:
            continue
        img = bg.copy()
        img.alpha_composite(player, (int(px - 20), int(G - 42 - 14)))
        spr = rc
        if tick < tetanus_until:
            r, g, b, a = spr.split()
            spr = Image.merge("RGBA", (r.point(lambda v: min(255, int(v * 1.15) + 20)), g.point(lambda v: int(v * 0.8)), b.point(lambda v: int(v * 0.6)), a))
            gif.text(img, (int(cx) - 6, int(cy) - 24), "Tetanus %.1f s" % ((tetanus_until - tick) / 60), fill=RUST)
        img.alpha_composite(spr, (int(cx), int(cy)))
        big = nail.resize((nail.width * 2, nail.height * 2), Image.NEAREST)
        img.alpha_composite(big, (W - big.width - 12, 52))
        numbers(gif, img, pops, tick)
        gif.text(img, (10, 8), "Rusted Nail: an enemy whose touch lands takes %d (the Cactus set's Expert thorns)" % KN["ThornDamage"])
        gif.text(img, (10, 28), ("and gets Tetanus %d s: +%d%% damage taken" % (KN["TetanusTicks"] // 60, KN["DamageTakenPercent"])) if rams < 2 else
                 "its second ram, still under Tetanus: %d (+%d%%)" % (int(KN["ThornDamage"] * KN["DamageTakenMultiplier"]), KN["DamageTakenPercent"]))
        gif.push(img)
    gif.save(out)


def sprites_png(out, font):
    gif = Gif(font, (10, 10))
    hawk = Planes("Content/Desert/NPCs/Coghawk", KH)
    bot = Planes("Content/Rain/NPCs/Splasher", KS)
    water = frames("Content/Rain/Projectiles/SplasherWater.png", 20, 20, 22, 16)
    nail = load("Content/Underground/Items/RustedNail.png")
    W, H = 1980, 760
    img = Image.new("RGBA", (W, H), (36, 40, 48, 255))
    ImageDraw.Draw(img).rectangle([0, H // 2, W, H], fill=(214, 190, 150, 255))
    names_h = ["Flap0", "Flap1", "Flap2", "Flap3", "Glide", "Screech0", "Screech1", "Dive", "Skim", "Climb"]
    names_s = ["Walk0", "Walk1", "Walk2", "Walk3", "Walk4", "Walk5", "Idle0", "Idle1", "Aim0", "Aim1", "Shoot0", "Shoot1"]
    for half in (0, 1):
        y0 = half * H // 2
        gif.text(img, (12, y0 + 6), "Coghawk (desert), all frames, 2x of the game sprite" + ("" if half == 0 else ", on a light background"))
        for k, n in enumerate(names_h):
            tile = Image.new("RGBA", (KH["CellWidth"], KH["CellHeight"]))
            hawk.draw(tile, k, (KH["OriginX"], KH["OriginY"]), False)
            big = tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST)
            img.alpha_composite(big, (12 + k * 156, y0 + 30))
            gif.text(img, (12 + k * 156, y0 + 152), n)
        gif.text(img, (12, y0 + 178), "Splasher (rain), all frames")
        for k, n in enumerate(names_s):
            tile = Image.new("RGBA", (KS["CellWidth"], KS["CellHeight"]))
            bot.draw(tile, k, (KS["OriginX"], KS["OriginY"]), False)
            big = tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST)
            img.alpha_composite(big, (12 + k * 132, y0 + 200))
            gif.text(img, (12 + k * 132, y0 + 344), n)
        for k in range(0, 16, 2):
            img.alpha_composite(water[k].resize((40, 40), Image.NEAREST), (1620 + (k // 2 % 4) * 44, y0 + 30 + (k // 8) * 44))
        gif.text(img, (1620, y0 + 120), "SplasherWater (8 of 16)")
        img.alpha_composite(nail.resize((128, 128), Image.NEAREST), (1620, y0 + 190))
        gif.text(img, (1760, y0 + 250), "Rusted Nail")
    img.convert("RGB").save(out)
    print(out, img.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("sprites", lambda: sprites_png(os.path.join(args.out, "2026-11-03_enemies-sprites.png"), args.font)),
            ("coghawk", lambda: scene_coghawk(os.path.join(args.out, "2026-11-03_desert-coghawk.gif"), args.font)),
            ("splasher", lambda: scene_splasher(os.path.join(args.out, "2026-11-03_rain-splasher.gif"), args.font)),
            ("nail", lambda: scene_nail(os.path.join(args.out, "2026-11-03_underground-rusted-nail.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
