"""D5 simulations of two Junkyard effects, using the real sprites and the constants of the C# code.

    python -P tools/sim/junkyard_effects_sim.py --tar-out docs/media/<date>_junkyard-tar.gif \
        --cache-out docs/media/<date>_junkyard-cache-glow.gif

1. Steaming tar (Content/Junkyard/Tar/): the pool rim and a puddle in the Junkyard, all water drawn with the
   TarWaterStyle textures the way vanilla draws water (decompiled Main.DrawWaters / LiquidRenderer.DrawNormalLiquids:
   16 animation frames, 6 per second without wind, surface cells on top): a background pass at full opacity behind
   the entities (backWaterTarget), then the front pass at 60% after them, so the tar is solid against the backdrop and
   see-through only for what is inside it. TarSteamSystem's rules
   make the steam: every 5 ticks 2 random columns are probed for a surface; a hit lets off a TarSteam puff, one in 7 a
   plume of 5 with a bubble of TarSplash droplets; puffs rise, grow through their 3 drawn stages and fade exactly as
   TarSteam.Update does. A player in Scrap armor walks into the puddle: TarPlayer gives Tar Plague while wet, the
   plague ticks 20 damage every 30 ticks (vanilla DoT number) and halves move speed on top of vanilla water's halved
   movement; after 60 ticks in the tar the player turns back and climbs out, and the plague lingers 40 ticks.
   HP bar and timers are shown.
2. Junkyard cache (Content/Furniture/ScrappyTrunkTile.cs): the buried cache inside its heap at night, with the 0.12 base
   glow swelling for 40 ticks every 120 ticks, and the sparkle at the heap surface above it on each pulse.

Leaves out: real lighting (everything at full brightness; the cache glow is a radial tint), water flow and the
liquid renderer's edge smoothing (only surface and interior cells), wind, sand/stone sprites (stand-ins), the tint
and drips TarPlayer.DrawEffects puts on a plagued player (shown as a darker sprite only).
"""
import argparse
import math
import os
import random
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armor_preview as ap  # noqa: E402
from terrain import load_frames, render  # noqa: E402

# --- mirrored from TarPlayer.cs / TarPlague.cs / TarSteamSystem.cs / TarSteam.cs / ScrappyTrunkTile.cs -------------
TICK_DAMAGE, TICK_INTERVAL, LINGER, MOVE_MULT = 20, 30, 40, 0.5
SAMPLE_INTERVAL, SAMPLES, PLUME_ONE_IN, PLUME_PUFFS = 5, 2, 7, 5
STEAM_SPAWN_ALPHA, STEAM_FADE, STEAM_RISE_ACC, STEAM_MAX_RISE, STEAM_OPACITY = 70, 2, 0.012, 1.3, 0.85
STEAM_STAGE_END, STEAM_CELL, STEAM_STRIDE = (120, 190, 256), 32, 34
PULSE_PERIOD, PULSE_LENGTH, BASE_GLOW, SWELL = 120, 40, 0.12, 0.75
# --- vanilla (decompiled LiquidRenderer, Player, CombatText) ----------------------------------------------------------
WATER_OPACITY, WATER_FRAME_TICKS = 0.6, 10
GRAVITY, MAX_FALL, WET_GRAVITY, WET_MAX_FALL, WET_JUMP, WET_JUMP_TICKS = 0.4, 10.0, 0.2, 5.0, 6.01, 30
RUN_SPEED = 3.0
DOT_COLOR = (255, 60, 70)                             # CombatText.LifeRegen
# ------------------------------------------------------------------------------------------------------------------
TPF = 3
BOB = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3


def tar_sim(out):
    cols, rows = 40, 22
    ground = 9                                        # yard ground row; the pool's surface is 2 rows lower
    pool_top, wall_x0, wall_x1 = ground + 2, 14, 17
    puddle = {22: 2, 23: 3, 24: 3, 25: 3, 26: 3, 27: 3, 28: 3, 29: 2}    # column -> depth (JunkyardPass.MakePuddle)
    heap_top = {32: 8, 33: 7, 34: 6, 35: 6, 36: 5, 37: 6, 38: 7, 39: 7}
    water = set()
    for x in range(0, wall_x0):
        for y in range(pool_top, rows):
            water.add((x, y))
    for x, d in puddle.items():
        for y in range(ground, ground + d):
            water.add((x, y))
    metal_grid, scrap_grid, sand = [], [], set()
    for y in range(rows):
        mrow, srow = "", ""
        for x in range(cols):
            mrow += "#" if wall_x0 <= x <= wall_x1 and y >= ground else "."
            in_heap = x in heap_top and heap_top[x] <= y < ground
            srow += "#" if in_heap else "."
            if x > wall_x1 and y >= ground and (x, y) not in water and not in_heap:
                sand.add((x, y))
        metal_grid.append(mrow)
        scrap_grid.append(srow)
    frames_meta = load_frames("art/templates/terrain_exposure.json")
    metal = render(metal_grid, {"#": Image.open("Content/Junkyard/Tiles/PolishedMetalTile.png").convert("RGBA")}, frames_meta, seed=3)
    scrap = render(scrap_grid, {"#": Image.open("Content/Scrap/Tiles/RustedScrapTile.png").convert("RGBA")}, frames_meta, seed=4)
    tar = Image.open("Content/Junkyard/Tar/TarWaterStyle.png").convert("RGBA")
    steam_sheet = Image.open("Content/Junkyard/Tar/TarSteam.png").convert("RGBA")
    splash_sheet = Image.open("Content/Junkyard/Tar/TarSplash.png").convert("RGBA")
    heads = ap.load_frames("Content/Scrap/Armor/ScrapHelmet_Head.png", 4)
    bodies = ap.load_frames("Content/Scrap/Armor/ScrapBreastplate_Body.png", 4)
    legs = ap.load_frames("Content/Scrap/Armor/ScrapLeggings_Legs.png", 4)

    w, h = cols * 16, rows * 16
    back = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(back)
    for y in range(h):
        t = y / h
        d.line([0, y, w, y], fill=(int(150 - 50 * t), int(180 - 55 * t), int(210 - 40 * t), 255))
    d.rectangle([0, pool_top * 16, wall_x0 * 16, h], fill=(48, 44, 46, 255))      # the shaft's back wall (stand-in)
    for x in range(0, wall_x0 * 16, 24):                                          # junk silhouettes to see through the tar
        d.rectangle([x + 4, pool_top * 16 + 40 + (x * 7) % 50, x + 14, h], fill=(70, 62, 60, 255))
    rng_s = random.Random(5)
    for (x, y) in sand:
        col = (220, 196, 128) if y == ground else (196, 170, 106)
        d.rectangle([x * 16, y * 16, x * 16 + 15, y * 16 + 15], fill=col + (255,))
        for _ in range(3):
            sx, sy = x * 16 + rng_s.randrange(0, 16, 2), y * 16 + rng_s.randrange(0, 16, 2)
            d.rectangle([sx, sy, sx + 1, sy + 1], fill=(184, 150, 92, 255))
    back.alpha_composite(metal)
    back.alpha_composite(scrap)

    def surface_cell(x, y):
        return (x, y) in water and (x, y - 1) not in water

    steam, drops, texts = [], [], []
    rng = random.Random(7)
    # player: 20x42 hitbox, feet at y; starts on the ground right of the puddle and walks left
    px, py = 31 * 16.0, ground * 16.0
    vx, vy = 0.0, 0.0
    hp, plague, tick_timer, damage_ticks = 100, 0, 0, 0
    heading, wet_time, jump, was_wet = -1, 0, 0, False   # walk left; turn back after TURN_BACK ticks in the tar
    TURN_BACK = 35
    gif = []
    total = 420
    for tick in range(total):
        # --- player (owner side: TarPlayer.PostUpdateMiscEffects, TarPlague.Update, UpdateBadLifeRegen) ------------
        feet_tile = (int((px + 10) // 16), int((py - 1) // 16))
        wet = any((int((px + ox) // 16), int((py - oy) // 16)) in water for ox in (2, 10, 18) for oy in (2, 20, 40))
        if wet:
            plague = LINGER
            wet_time += 1
            if wet_time >= TURN_BACK:
                heading = 1
        plagued = plague > 0
        if plagued:
            plague -= 1
            tick_timer += 1
            if tick_timer >= TICK_INTERVAL:
                tick_timer = 0
                hp -= TICK_DAMAGE
                damage_ticks += 1
                texts.append([px + 10, py - 46, 0])
        else:
            tick_timer = 0
        target_speed = RUN_SPEED * (MOVE_MULT if plagued else 1.0)
        vx = heading * target_speed if (heading < 0 or px < 30.4 * 16) else 0.0
        g, mf = (WET_GRAVITY, WET_MAX_FALL) if wet else (GRAVITY, MAX_FALL)

        def floor_at(x_px):
            c = int((x_px + 10) // 16)
            return (ground + puddle[c]) * 16.0 if c in puddle else ground * 16.0
        floor = floor_at(px)
        step = 0.5 if wet else 1.0                         # Collision.WaterCollision moves wet players at half speed
        nx = px + vx * step
        rise = py - floor_at(nx)
        if rise > 16.5:                                    # a wall higher than a step: stop and jump out
            nx = px
            if py >= floor - 1 and jump == 0:
                jump = WET_JUMP_TICKS if wet else 15       # vanilla jumpHeight: the jump speed is held this long
        elif rise > 0.5 and py >= floor - 1:
            py = floor_at(nx)                              # Collision.StepUp: one tile up while walking
        px = nx
        if was_wet and not wet:
            jump = min(jump, 15 // 5)                      # vanilla: leaving water cuts the held jump to jumpHeight / 5
        was_wet = wet
        if jump > 0:
            jump -= 1
            vy = -WET_JUMP
        else:
            vy = min(vy + g, mf)
        py = min(py + vy * step, floor_at(px))
        if py >= floor_at(px):
            vy = 0.0
        # --- steam (TarSteamSystem) ----------------------------------------------------------------------------
        if tick % SAMPLE_INTERVAL == 0:
            for _ in range(SAMPLES):
                x = rng.randrange(cols)
                ys = [y for y in range(rows) if surface_cell(x, y)]
                if not ys:
                    continue
                sy = ys[0] * 16.0
                plume = rng.randrange(PLUME_ONE_IN) == 0
                for i in range(PLUME_PUFFS if plume else 1):
                    vy0 = -rng.uniform(0.6, 1.1) if plume else -rng.uniform(0.2, 0.5)
                    steam.append([x * 16 + rng.uniform(0, 16), sy - 4 - i * 6, rng.uniform(-0.25, 0.25), vy0, STEAM_SPAWN_ALPHA, rng.randrange(2)])
                if plume:
                    for _ in range(4):
                        drops.append([x * 16 + 4 + rng.uniform(0, 8), sy - 2, rng.uniform(-1, 1), -rng.uniform(1.5, 3), 0, rng.randrange(3)])
        for p in steam:                                   # TarSteam.Update
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.97
            p[3] = max(p[3] - STEAM_RISE_ACC, -STEAM_MAX_RISE)
            p[4] += STEAM_FADE
        steam = [p for p in steam if p[4] < 255]
        for q in drops:                                   # water-dust-like droplets (stand-in physics)
            q[0] += q[2]
            q[1] += q[3]
            q[3] += 0.15
            q[4] += 1
        drops = [q for q in drops if q[4] < 40]
        for t_ in texts:
            t_[1] -= 0.6
            t_[2] += 1
        texts = [t_ for t_ in texts if t_[2] < 60]
        if tick % TPF:
            continue
        # --- draw ----------------------------------------------------------------------------------------------
        img = back.copy()
        anim = (tick // WATER_FRAME_TICKS) % 16
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        for (x, y) in water:
            sy = anim * 80 + (0 if surface_cell(x, y) else 48)
            layer.alpha_composite(tar.crop((16, sy, 32, sy + 16)), (x * 16, y * 16))
        img.alpha_composite(layer)                        # background pass: full opacity, behind the entities
        moving = abs(vx) > 0.01 and py >= floor - 0.5
        frame = (tick // 4) % 14 + 6 if moving else (5 if vy < -0.5 else 0)
        sprite = ap.compose(heads[0], bodies[0], legs[0], frame, BOB)
        if plagued:                                       # TarPlayer.DrawEffects tint (r,g,b x0.48/0.45/0.42)
            r, g_, b, a = sprite.split()
            r = r.point(lambda v: int(v * 0.48))
            g_ = g_.point(lambda v: int(v * 0.45))
            b = b.point(lambda v: int(v * 0.42))
            sprite = Image.merge("RGBA", (r, g_, b, a))
        img.alpha_composite(sprite.transpose(Image.FLIP_LEFT_RIGHT) if heading < 0 else sprite, (int(px - 10), int(py - 56)))
        for p in steam:
            alpha = p[4]
            stage = next(k for k, end in enumerate(STEAM_STAGE_END) if alpha < end or k == 2)
            cell = steam_sheet.crop((p[5] * STEAM_STRIDE, stage * STEAM_STRIDE, p[5] * STEAM_STRIDE + STEAM_CELL, stage * STEAM_STRIDE + STEAM_CELL))
            op = (255 - alpha) / 255 * STEAM_OPACITY
            cell.putalpha(cell.getchannel("A").point(lambda v: int(v * op)))
            img.alpha_composite(cell, (int(p[0] - 16), int(p[1] - 16)))
        for q in drops:
            img.alpha_composite(splash_sheet.crop((0, q[5] * 10, 8, q[5] * 10 + 8)), (int(q[0]), int(q[1])))
        # front pass after the entities, at 60% (premultiplied: colour x opacity, like SpriteBatch)
        front = layer.copy()
        front.putalpha(front.getchannel("A").point(lambda v: int(v * WATER_OPACITY)))
        img.alpha_composite(front)
        dd = ImageDraw.Draw(img)
        for (tx, ty, age) in texts:
            dd.text((tx - 8, ty), "20", fill=DOT_COLOR)
        # HUD
        dd.rectangle([w - 132, 6, w - 8, 18], fill=(21, 22, 28))
        dd.rectangle([w - 130, 8, w - 130 + int(120 * max(hp, 0) / 100), 16], fill=(163, 48, 26))
        dd.text((w - 128, 20), f"HP {max(hp, 0)}/100", fill=(21, 22, 28))
        state = "Tar Plague" + (f" (linger {plague})" if plagued and not wet else "") if plagued else "clean"
        dd.text((6, 6), f"tick {tick:3d}  wet: {'yes' if wet else 'no '}  {state}", fill=(21, 22, 28))
        dd.text((6, 18), f"speed {abs(vx) * (0.5 if wet else 1):.2f} px/tick  ticks of 20: {damage_ticks}", fill=(21, 22, 28))
        gif.append(img.convert("RGB"))
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=TPF * 1000 // 60, loop=0)
    print(f"{out}: {len(gif)} frames, {total / 60:.1f} s, {damage_ticks} plague ticks, hp {hp}")


def cache_sim(out):
    frames_meta = load_frames("art/templates/terrain_exposure.json")
    scrap = Image.open("Content/Scrap/Tiles/RustedScrapTile.png").convert("RGBA")
    trunk = Image.open("Content/Furniture/ScrappyTrunkTile.png").convert("RGBA")
    heap = [
        "..........#.........",
        "........#####.......",
        ".......#######......",
        "......#########.....",
        ".....###########....",
        "....####....#####...",
        "...#####....######..",
        "..######....#######.",
        ".##################.",
        "####################",
    ]
    tiles = render(heap, {"#": scrap}, frames_meta, seed=5)
    w, h = tiles.width, tiles.height + 64
    cx, cy = 8 * 16, 5 * 16 + 64                       # chamber: tiles 8..11, rows 5..7 (+64 px of sky)
    gif = []
    for tick in range(0, 2 * PULSE_PERIOD + 30, TPF):
        t = tick % PULSE_PERIOD
        pulse = math.sin(math.pi * t / PULSE_LENGTH) if t < PULSE_LENGTH else 0.0
        glow = BASE_GLOW + SWELL * pulse
        img = Image.new("RGBA", (w, h), (12, 14, 26, 255))
        img.alpha_composite(tiles, (0, 64))
        for x in range(2):
            for y in range(2):
                hgt = 16 if y == 0 else 18
                img.alpha_composite(trunk.crop((36 + x * 18, y * 18, 36 + x * 18 + 16, y * 18 + hgt)), (cx + 16 + x * 16, cy + 16 + y * 16))
        dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dark)
        for yy in range(0, h, 4):                      # night: everything dark except where the cache lights it
            for xx in range(0, w, 4):
                dist = math.hypot(xx - (cx + 32), yy - (cy + 32)) / 16.0
                light = glow * max(0.0, 1.0 - dist / 6.0)
                dd.rectangle([xx, yy, xx + 3, yy + 3], fill=(0, 0, 0, int(220 * (1 - min(1.0, light * 1.6)))))
        img.alpha_composite(dark)
        d = ImageDraw.Draw(img)
        if t < 18:                                     # surface sparkle after each pulse start
            for k in range(4):
                sx = cx + 26 + (k * 13) % 30
                sy = 64 - 6 - (t // 3) - (k % 2) * 4
                d.rectangle([sx, sy, sx + 2, sy + 2], fill=(255, 199, 90))
        d.text((4, 4), f"cache glow {glow:.2f}", fill=(238, 241, 243))
        d.text((4, 16), "pulse every 120 ticks", fill=(195, 200, 205))
        gif.append(img.convert("RGB").resize((w * 2, h * 2), Image.NEAREST))
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=TPF * 1000 // 60, loop=0)
    print(f"{out}: {len(gif)} frames")


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--tar-out")
    ap_.add_argument("--cache-out")
    a = ap_.parse_args()
    if a.tar_out:
        tar_sim(a.tar_out)
    if a.cache_out:
        cache_sim(a.cache_out)


if __name__ == "__main__":
    main()
