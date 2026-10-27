"""D5 proofs for the Junkyard update of 2026-10-26: the Rust Collector, the Living Tar, the Rust Polisher and the
Mysterious Map, built from the real sprites and the constants parsed out of the C# files, replayed tick by tick.

    python -P tools/sim/junkyard_finds_sim.py --out docs/media --date 2026-10-26 [--only collector,tar,...]

Writes <date>_junkyard-<scene>.gif|png:
    creatures  PNG: every new Junkyard sprite (enemies, gores, projectile, items, the polisher, the arrow's 16 headings).
    collector  the Rust Collector rolling at a player: the acceleration ramp, an overshoot (contact 25), the skid and turn,
               a faster second pass, then a wall at speed: bonk, stunned 45 ticks.
    tar        the Living Tar hopping like a vanilla slime with a target (decompiled AI_001_Slimes: on the ground ai[0]
               grows by 2 a tick from -100; hops at 0, -1000 and -2000: two small hops (2, -6) and a big one (3, -8)),
               throwing a tar glob at the player every time it lands; a hit is 4 damage plus 2 s of Tar Plague.
    polisher   the Rust Polisher tile animating (6 frames, 4 ticks each), assembled from its tile cells the way the game
               draws them (16 px cells, the 2 px gutters dropped), with the Polished Metal recipe.
    map        a player holding the Mysterious Map walking around: the arrow circles them at 46 px and always shows the
               pre-rendered heading closest to the target (16 headings, never rotated), its gem pulsing.

Leaves out: lighting, real tile collision (a height map), vanilla's player animation, network latency.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trashtr0m_loot_sim as loot  # noqa: E402

J = "Content/Junkyard/"
TPF = 3
K = loot.consts(J + "NPCs/RustCollector.cs", J + "NPCs/LivingTar.cs", J + "Projectiles/TarGlob.cs", J + "Tiles/RustPolisherTile.cs",
                J + "Map/MysteriousMapArrowLayer.cs", J + "Items/PolishedMetal.cs")
_gd = re.search(r"GlobDamage = (\d+);", open(J + "NPCs/LivingTar.cs", encoding="utf-8").read())
K["GlobDamageExpert"] = float(_gd.group(1))                 # Expert value (ExpertStats), like every Cogpunk number
KG = loot.consts(J + "Projectiles/TarGlob.cs")              # its TicksPerFrame and Frames clash with the polisher's


def frames(path, w, h, stride, n):
    return loot.frames(path, w, h, stride, n)


# ================================================================================================
# Rust Collector
# ================================================================================================
def scene_collector(out, font):
    sheet = frames(J + "NPCs/RustCollector.png", 32, 32, 32, 11)
    W, H, ground = 960, 300, 250
    wall_x = 900
    bg = loot.backdrop(W, H, ground, sky=((120, 140, 170), (90, 100, 130)), dirt=(170, 140, 90))
    ImageDraw.Draw(bg).rectangle([wall_x, ground - 96, W, ground], fill=(127, 135, 148, 255), outline=(21, 22, 28, 255))
    gif = loot.Gif(font, (W, H))
    pl = loot.player_sprite()
    player_x = 330.0
    x, vx, ramp = 60.0, 0.0, 0.0
    state, timer, frame_counter = "roll", 0, 0.0
    hits, log = [], []
    tick = 0
    last_hit = -99
    for tick in range(480):
        if tick == 250:
            player_x = 850.0                              # the player steps in front of the wall
        timer += 1
        if state == "stunned":
            vx *= 0.9
            if timer >= K["StunTicks"]:
                state, timer, ramp = "roll", 0, 0.0
                log.append((tick, "recovered"))
        else:
            want = 1 if player_x >= x + 13 else -1
            if vx == 0 or (vx > 0) == (want > 0):
                ramp = min(ramp + 1, K["RampTicks"])
                accel = K["BaseAccel"] + (K["MaxAccel"] - K["BaseAccel"]) * ramp / K["RampTicks"]
                vx = max(-K["MaxSpeed"], min(K["MaxSpeed"], vx + want * accel))
            else:
                ramp = 0
                vx = 0.0 if abs(vx) <= K["SkidDecel"] else vx - math.copysign(K["SkidDecel"], vx)
        nx = x + vx
        if nx + 26 > wall_x:                              # the wall: vanilla stops it (collideX)
            if abs(vx) > K["BonkSpeed"]:
                state, timer, ramp = "stunned", 0, 0.0
                log.append((tick, "bonk at %.1f px/tick" % abs(vx)))
                vx = -math.copysign(2.5, vx)
            else:
                vx = 0.0
            nx = min(nx, wall_x - 26)
        x = nx
        if abs(x + 13 - (player_x + 10)) < 23 and tick - last_hit > 40:
            last_hit = tick
            hits.append(tick)
        # FindFrame
        skidding = state == "roll" and vx != 0 and ((vx > 0) != (player_x >= x + 13))
        if state == "stunned":
            fr = K["StunFrame"] + (timer // 6) % 2
        elif skidding and abs(vx) > 1.5:
            fr = K["SkidFrame"]
        else:
            frame_counter = (frame_counter + abs(vx)) % (5.0 * K["RollFrames"])
            fr = (K["FastFrame"] if abs(vx) >= K["FastSpeed"] else 0) + int(frame_counter / 5.0) % K["RollFrames"]
        if tick % TPF == 0:
            img = bg.copy()
            img.alpha_composite(pl, (int(player_x - 20), ground - 56))
            spr = sheet[fr]
            if vx > 0.1:
                spr = spr.transpose(Image.FLIP_LEFT_RIGHT)    # the art faces left
            img.alpha_composite(spr, (int(x - 3), ground - 32 + 4))
            for h in hits:
                if 0 <= tick - h < 40:
                    gif_text(gif, img, (int(player_x), ground - 90 - (tick - h) // 2), "25", (255, 120, 90))
            gif_text(gif, img, (14, 10), "Rust Collector: %s  speed %.1f px/tick  ramp %d/%d" % (
                {"roll": "skidding" if skidding else "rolling", "stunned": "STUNNED %d/%d" % (timer, K["StunTicks"])}[state],
                abs(vx), ramp, K["RampTicks"]), (238, 241, 243), True)
            gif_text(gif, img, (14, 38), "accel %.2f -> %.2f over %d ticks, max %.1f; skid %.2f; no jumping; a wall above %.0f px/tick stuns it" % (
                K["BaseAccel"], K["MaxAccel"], K["RampTicks"], K["MaxSpeed"], K["SkidDecel"], K["BonkSpeed"]))
            gif.push(img)
    gif.save(out)
    print("collector:", log, "contact hits at", hits)


def gif_text(gif, img, xy, s, fill=(238, 241, 243), big=False):
    gif.text(img, xy, s, fill=fill, font=gif.big if big else None)


# ================================================================================================
# Living Tar
# ================================================================================================
def scene_tar(out, font):
    body = frames(J + "NPCs/LivingTar.png", 32, 24, 24, 2)
    glob = frames(J + "Projectiles/TarGlob.png", 16, 16, 18, 3)
    W, H, ground = 960, 330, 280
    bg = loot.backdrop(W, H, ground, sky=((120, 120, 140), (70, 70, 90)), dirt=(160, 132, 90))
    d = ImageDraw.Draw(bg)
    d.rectangle([0, ground - 6, 60, H], fill=(47, 27, 20, 255))         # the tar pool's edge on the left
    gif = loot.Gif(font, (W, H))
    pl = loot.player_sprite(flip=True)
    player = (760.0, ground - 42.0)
    x, y, vx, vy = 140.0, float(ground - 18), 0.0, 0.0
    ai0 = -100.0
    airborne_was = False
    cooldown = 0
    globs = []
    log, player_hits = [], []
    for tick in range(480):
        on_ground = vy == 0 and y + 18 >= ground
        if on_ground:
            vx *= 0.8
            if abs(vx) < 0.1:
                vx = 0.0
            ai0 += 2                                       # +1, +1 more with a target (flag)
            kind = 1 if ai0 >= 0 else (2 if -1000 <= ai0 <= -500 else (3 if -2000 <= ai0 <= -1500 else 0))
            if kind == 3:
                vy, vx, ai0 = -8.0, vx + 3, -200.0
                log.append((tick, "big hop"))
            elif kind:
                vy, vx = -6.0, vx + 2
                ai0 = -120.0 + (-1000.0 if kind == 1 else -2000.0)
                log.append((tick, "hop"))
        vy = min(vy + 0.3, 10.0)
        x += vx
        y += vy
        if y + 18 >= ground:
            y, vy = float(ground - 18), 0.0
        airborne = vy != 0
        if cooldown > 0:
            cooldown -= 1
        if airborne_was and not airborne and cooldown == 0:
            dist = math.hypot(player[0] + 10 - (x + 12), player[1] + 21 - y)
            if dist <= K["ShootRange"]:
                cooldown = K["ShootCooldown"]
                fx, fy = x + 12, y + 4
                ddx, ddy = player[0] + 10 - fx, player[1] + 21 - fy
                tt = max(20.0, min(50.0, abs(ddx) / 7.0))
                gvx = max(-10.0, min(10.0, ddx / tt))
                gvy = max(-11.0, min(6.0, (ddy - 0.5 * K["Gravity"] * tt * tt) / tt))
                globs.append([fx, fy, gvx, gvy, 0, True])
                log.append((tick, "landed: glob"))
        airborne_was = airborne
        for g in globs:
            if not g[5]:
                continue
            g[3] = min(g[3] + K["Gravity"], 12.0)
            g[0] += g[2]
            g[1] += g[3]
            g[4] += 1
            if player[0] < g[0] + 6 and g[0] - 6 < player[0] + 20 and player[1] < g[1] + 6 and g[1] - 6 < player[1] + 42:
                g[5] = False
                player_hits.append(tick)
            elif g[1] + 6 >= ground:
                g[5] = False
        if tick % TPF == 0:
            img = loot.backdrop(W, H, ground) if False else bg.copy()
            img.alpha_composite(pl, (int(player[0] - 20), int(player[1] - 14)))
            spr = body[0 if not airborne else 1].transpose(Image.FLIP_LEFT_RIGHT)   # facing right, towards the player
            img.alpha_composite(spr, (int(x - 4), int(y - 6 + 4)))
            for g in globs:
                if g[5]:
                    img.alpha_composite(glob[(g[4] // KG["TicksPerFrame"]) % 3], (int(g[0] - 8), int(g[1] - 8)))
            for h in player_hits:
                if 0 <= tick - h < 50:
                    gif_text(gif, img, (int(player[0]) - 30, int(player[1]) - 40 - (tick - h) // 2), "%d + Tar Plague 2 s" % K["GlobDamageExpert"], (236, 113, 40))
            gif_text(gif, img, (14, 10), "Living Tar: vanilla slime hops; a tar glob each time it lands", big=True)
            gif_text(gif, img, (14, 38), "60 life, contact 5, glob %d (Classic) + Tar Plague %d ticks on any hit; glob range %d tiles" % (
                K["GlobDamageExpert"], K["TarTicks"], K["ShootRange"] // 16))
            gif.push(img)
    gif.save(out)
    print("tar:", log, "player hit at", player_hits)


# ================================================================================================
# Rust Polisher
# ================================================================================================
def polisher_frame(sheet, f):
    """One animation frame assembled from its 3x3 tile cells exactly as the game draws them: 16 px apart, the 2 px gutters
    dropped (the bottom row is 18 px tall: the base sinks into the floor)."""
    out = Image.new("RGBA", (48, 50), (0, 0, 0, 0))
    y0 = f * K["FrameHeight"]
    for cx in range(3):
        for (cy, sy, h) in ((0, 0, 16), (1, 18, 16), (2, 36, 18)):
            cell = sheet.crop((cx * 18, y0 + sy, cx * 18 + 16, y0 + sy + h))
            out.alpha_composite(cell, (cx * 16, cy * 16))
    return out


def scene_polisher(out, font):
    sheet = loot.load(J + "Tiles/RustPolisherTile.png")
    items = [loot.load(J + p) for p in ("Items/PolisherSchematic.png", "Items/RustPolisher.png")]
    metal = loot.load("Content/Scrap/Items/RustedMetal.png")
    polished = loot.load(J + "Items/PolishedMetal.png")
    W, H, ground = 640, 300, 240
    gif = loot.Gif(font, (W, H))
    bg = loot.backdrop(W, H, ground, sky=((60, 52, 50), (36, 32, 34)), dirt=(79, 85, 98))
    for tick in range(K["Frames"] * K["TicksPerFrame"] * 6):
        if tick % TPF:
            continue
        img = bg.copy()
        f = (tick // K["TicksPerFrame"]) % K["Frames"]
        big = polisher_frame(sheet, f)
        big = big.resize((big.width * 3, big.height * 3), Image.NEAREST)
        img.alpha_composite(big, (40, ground - 150 + 6))
        img.alpha_composite(polisher_frame(sheet, f), (230, ground - 48 + 2))
        x = 330
        for im, label in ((metal, "2 Rusted Metal"), (polished, "-> Polished Metal")):
            z = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            img.alpha_composite(z, (x, 90))
            gif_text(gif, img, (x, 130), label)
            x += 140
        x = 330
        for im in items:
            img.alpha_composite(im, (x, 170))
            x += im.width + 20
        gif_text(gif, img, (14, 10), "Rust Polisher (3x3 station, %d frames x %d ticks): frame %d" % (K["Frames"], K["TicksPerFrame"], f), big=True)
        gif_text(gif, img, (330, 220), "schematic (kept) + 30 bars + 35 cogs + 50 sand")
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Mysterious Map
# ================================================================================================
def scene_map(out, font):
    arrows = frames(J + "Map/MysteriousMapArrow.png", 40, 40, 42, 16)
    glows = frames(J + "Map/MysteriousMapArrow_Glow.png", 40, 40, 42, 16)
    mapi = loot.load(J + "Map/MysteriousMap.png")
    W, H, ground = 820, 420, 300
    bg = loot.backdrop(W, H, ground)
    gif = loot.Gif(font, (W, H))
    pl = loot.player_sprite()
    target = (1500.0, 2200.0)                              # far away, down and to the right (off screen)
    for tick in range(360):
        px = 410 + 300 * math.sin(tick * 2 * math.pi / 360)
        centre = (px, ground - 21.0)
        dx, dy = target[0] - centre[0], target[1] - centre[1]
        ang = math.atan2(dy, dx)
        if tick >= 180:                                    # the target moves: as if the player walked past it
            tgt = (centre[0] - 2000 * math.cos(tick * 0.05), centre[1] - 600 + 900 * math.sin(tick * 0.035))
            ang = math.atan2(tgt[1] - centre[1], tgt[0] - centre[0])
        heading = int(round(ang / (2 * math.pi) * K["Directions"])) % K["Directions"]
        snapped = heading * 2 * math.pi / K["Directions"]
        ax = centre[0] + math.cos(snapped) * K["Radius"]
        ay = centre[1] + math.sin(snapped) * K["Radius"]
        if tick % TPF == 0:
            img = bg.copy()
            img.alpha_composite(pl, (int(px - 20), ground - 56))
            img.alpha_composite(mapi, (int(px + 2), ground - 40))
            pos = (int(round(ax - 20)), int(round(ay - 20)))
            img.alpha_composite(arrows[heading], pos)
            loot.glow_over(img, glows[heading], 0.6 + 0.4 * math.sin(tick / 60 * 3), pos)
            d = ImageDraw.Draw(img)
            ex, ey = centre[0] + math.cos(ang) * 150, centre[1] + math.sin(ang) * 150
            d.line([centre[0], centre[1], ex, ey], fill=(198, 189, 255), width=1)
            gif_text(gif, img, (14, 10), "Mysterious Map: held, a compass arrow circles the player towards the target", big=True)
            gif_text(gif, img, (14, 38), "heading %2d/16 (pre-rendered, 22.5 deg apart); thin line: the true direction" % heading)
            gif.push(img)
    gif.save(out)


# ================================================================================================
# Creature / item sheet
# ================================================================================================
def creatures_png(out, font):
    f = ImageFont.truetype(font, 15)
    z = 3
    groups = [("Rust Collector: roll x4, fast x4, skid, stunned x2", frames(J + "NPCs/RustCollector.png", 32, 32, 32, 11)),
              ("Living Tar, tar glob, Tar Drop", frames(J + "NPCs/LivingTar.png", 32, 24, 24, 2) + frames(J + "Projectiles/TarGlob.png", 16, 16, 18, 3) + [loot.load(J + "Items/TarDrop.png")]),
              ("gores, Polisher Schematic, Rust Polisher, Mysterious Map", [loot.load(J + "Gores/RustCollector_GoreWheel.png"), loot.load(J + "Gores/RustCollector_GorePanel.png"),
                                                                           loot.load(J + "Items/PolisherSchematic.png"), loot.load(J + "Items/RustPolisher.png"), loot.load(J + "Map/MysteriousMap.png")]),
              ("the map's arrow: 16 headings", frames(J + "Map/MysteriousMapArrow.png", 40, 40, 42, 16))]
    rows = []
    for name, ims in groups:
        for bgc in ((24, 22, 30), (150, 180, 210)):
            zz = 2 if "headings" in name else z
            h = max(im.height for im in ims) * zz + 36
            w = sum(im.width * zz + 10 for im in ims) + 20
            row = Image.new("RGBA", (max(w, 600), h), bgc + (255,))
            ImageDraw.Draw(row).text((10, 4), name, fill=(238, 241, 243) if bgc[0] < 100 else (21, 22, 28), font=f)
            x = 10
            for im in ims:
                im2 = im.resize((im.width * zz, im.height * zz), Image.NEAREST)
                row.alpha_composite(im2, (x, 28))
                x += im2.width + 10
            rows.append(row)
    W = max(r.width for r in rows)
    sheet = Image.new("RGBA", (W, sum(r.height for r in rows)), (40, 40, 48, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height
    sheet.convert("RGB").save(out)
    print(out, sheet.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-10-26")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    base = os.path.join(args.out, args.date + "_junkyard-")
    jobs = [("creatures", lambda: creatures_png(base + "creatures.png", args.font)),
            ("collector", lambda: scene_collector(base + "rust-collector.gif", args.font)),
            ("tar", lambda: scene_tar(base + "living-tar.gif", args.font)),
            ("polisher", lambda: scene_polisher(base + "rust-polisher.gif", args.font)),
            ("map", lambda: scene_map(base + "mysterious-map.gif", args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
