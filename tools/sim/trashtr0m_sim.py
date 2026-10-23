"""D5 proofs for Trash-Tr0m (Content/Bosses/TrashTr0m/), from the real sprites and the C# constants.

    python -P tools/sim/trashtr0m_sim.py --sprite-out docs/media/<date>_boss-trashtr0m-sprite.png \
        --intro-out docs/media/<date>_boss-trashtr0m-intro.gif

--sprite-out  PNG: frame 0 over a dark cavern and a light sky at 2x zoom, the _Glow layer alone, the map icon, and a
              Scrap-armoured player beside it with the height ruler (168 px = 4 x the player's 42 px hitbox).
--intro-out   GIF of the summon and the emergence intro as one client sees it: the player digs into the central heap
              and right-clicks the sealed Junkyard Cache; the server spawns the boss over the cache with its hands on
              the heap's slopes (TrashTr0mSummon.FindHandGround); the camera eases onto TrashTr0m.CameraFocus with the smoothstep of
              TrashTr0m.CameraLock (30-tick ease, held for the whole 240-tick intro); the heap rumbles for 45 ticks; the
              boss heaves out of the ground over 135 ticks, drawn clipped at the ground line exactly like PreDraw (even
              pixel steps, three heaves); the name card slams in at tick 135 (BossTitleSystem timings); it roars with
              the grinder at 3 ticks per frame; the camera eases back and the placeholder fight starts (Idle: 6 ticks
              per frame, exhaust puffs). Vanilla's PunchCameraModifier shakes are approximated (decaying sine).
              The screen is a 1920x1080 view rendered at game scale and halved (so the 2x art shows at 1x), with the
              card at the size and place BossTitleSystem draws it.

Leaves out: lighting, music and sounds, real dust physics (debris, sparks and smoke are simple particles), the
vanilla boss bar, chat (the "has awoken!" line is shown as text), and Terraria's Death Text font (a bold system font).
"""
import argparse
import math
import os
import random
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armor_preview as ap  # noqa: E402
from terrain import load_frames, render  # noqa: E402

# --- mirrored from TrashTr0m.cs / TrashTr0mSummon.cs / BossTitleSystem.cs ------------------------------------------
FRAME_W, FRAME_H, FRAME_STRIDE, FRAME_COUNT = 216, 168, 170, 6
TICKS_PER_FRAME, ROAR_TICKS_PER_FRAME = 6, 3
RUMBLE, RISE, ROAR = 45, 135, 60
EMERGE = RUMBLE + RISE + ROAR
TITLE_TICK = RUMBLE + 90
TITLE_HOLD = EMERGE - TITLE_TICK + 45
CAMERA_EASE = 30
TITLE_FADE_IN, TITLE_FADE_OUT, SLAM = 14, 36, 1.6
NAME_COLOR, NAME_SHADOW = (255, 199, 90), (77, 20, 10)
EPITHET_COLOR, EPITHET_SHADOW, RULE_COLOR = (195, 200, 205), (21, 22, 28), (163, 48, 26)
TITLE_CENTRE = 0.7
EXHAUST = [(164, 8), (180, 16)]
WAIST_LEFT, WAIST_RIGHT, WAIST_Y = 66, 154, 150
HAND_COLUMN_OFFSETS, SURFACE_SCAN_ROWS = (-5, -4, 5, 6), 48
# ------------------------------------------------------------------------------------------------------------------
TPF = 3
SCREEN_W, SCREEN_H = 1920, 1080                       # game pixels; the GIF shows it at half size
SKY = 40                                              # rows of open sky above the slice
BOB = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3
BOSS = "Content/Bosses/TrashTr0m/"


def load_sheet():
    sheet = Image.open(BOSS + "TrashTr0m.png").convert("RGBA")
    glow = Image.open(BOSS + "TrashTr0m_Glow.png").convert("RGBA")
    return ([sheet.crop((0, k * FRAME_STRIDE, FRAME_W, k * FRAME_STRIDE + FRAME_H)) for k in range(FRAME_COUNT)],
            [glow.crop((0, k * FRAME_STRIDE, FRAME_W, k * FRAME_STRIDE + FRAME_H)) for k in range(FRAME_COUNT)])


def player_sprite(frame=0, flip=False):
    heads = ap.load_frames("Content/Scrap/Armor/ScrapHelmet_Head.png", 4)
    bodies = ap.load_frames("Content/Scrap/Armor/ScrapBreastplate_Body.png", 4)
    legs = ap.load_frames("Content/Scrap/Armor/ScrapLeggings_Legs.png", 4)
    s = ap.compose(heads[0], bodies[0], legs[0], frame, BOB)
    return s.transpose(Image.FLIP_LEFT_RIGHT) if flip else s


# ------------------------------------------------------------------------------------------------------------------
# Static sheet
# ------------------------------------------------------------------------------------------------------------------
def sprite_png(out):
    frames, glows = load_sheet()
    icon = Image.open(BOSS + "TrashTr0m_Head_Boss.png").convert("RGBA")
    pad, z = 16, 2
    panel_w, panel_h = FRAME_W + 120, FRAME_H + 40
    img = Image.new("RGBA", (panel_w * 3 + pad * 4, panel_h + pad * 2), (240, 240, 236, 255))
    font = ImageFont.load_default()
    # 1: cavern, with a player and the 4x ruler
    p1 = Image.new("RGBA", (panel_w, panel_h), (24, 22, 30, 255))
    ground = 20 + FRAME_H
    ImageDraw.Draw(p1).rectangle([0, ground, panel_w, panel_h], fill=(60, 44, 36, 255))
    p1.alpha_composite(frames[0], (10, ground - FRAME_H))
    pl = player_sprite(0, flip=True)
    p1.alpha_composite(pl, (FRAME_W + 30, ground - 56))
    d = ImageDraw.Draw(p1)
    rx = FRAME_W + 90
    d.line([rx, ground - 168, rx, ground], fill=(255, 199, 90))
    for k in range(5):
        y = ground - 42 * k
        d.line([rx - 4, y, rx + 4, y], fill=(255, 199, 90))
    d.text((rx - 84, ground - 182), "168 px = 4 x 42", fill=(255, 199, 90), font=font)
    # 2: light sky
    p2 = Image.new("RGBA", (panel_w, panel_h), (150, 180, 210, 255))
    p2.alpha_composite(frames[0], (10, 20))
    # 3: glow layer alone + map icon
    p3 = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 255))
    p3.alpha_composite(glows[0], (10, 20))
    p3.alpha_composite(icon, (FRAME_W + 40, 30))
    ImageDraw.Draw(p3).text((FRAME_W + 30, 70), "map icon", fill=(195, 200, 205), font=font)
    ImageDraw.Draw(p3).text((14, 4), "_Glow (eyes, throat, furnace)", fill=(195, 200, 205), font=font)
    for k, p in enumerate((p1, p2, p3)):
        img.alpha_composite(p, (pad + k * (panel_w + pad), pad))
    img = img.resize((img.width * z, img.height * z), Image.NEAREST)
    img.convert("RGB").save(out)
    print(f"{out}: {img.width}x{img.height}")


# ------------------------------------------------------------------------------------------------------------------
# Intro
# ------------------------------------------------------------------------------------------------------------------
def buried_pixels(state, t):
    if state == "emerge":
        if t < RUMBLE:
            return FRAME_H
        p = min(1.0, max(0.0, (t - RUMBLE) / RISE))
        eased = 1 - (1 - p) * (1 - p)
        eased += 0.035 * math.sin(p * math.tau * 3) * (1 - p)
        buried = (1 - min(1.0, max(0.0, eased))) * FRAME_H
        return max(0, min(FRAME_H, int(buried * 0.5) * 2))
    return 0


def camera_lock(t):
    if t < 0 or t > EMERGE:
        return 0.0
    return max(0.0, min(1.0, min(t / CAMERA_EASE, (EMERGE - t) / CAMERA_EASE)))


def title_opacity(t):
    t -= TITLE_TICK
    if t < 0:
        return 0.0, SLAM
    if t < TITLE_FADE_IN:
        return t / TITLE_FADE_IN, SLAM + (1 - SLAM) * t / TITLE_FADE_IN
    if t < TITLE_FADE_IN + TITLE_HOLD:
        return 1.0, 1.0
    return max(0.0, 1 - (t - TITLE_FADE_IN - TITLE_HOLD) / TITLE_FADE_OUT), 1.0


def build_world():
    """A slice of the Junkyard: flat yard ground, the central heap (JunkyardPass.BuildHeap) with the cache chamber,
    and a 3-tall tunnel the player dug into it from the right."""
    cols, rows = 170, 40 + SKY + 30
    ground = 26 + SKY
    centre, half, height, bury = 85, 13, 11, 5
    solid = {}
    for x in range(cols):
        for y in range(ground, rows):
            solid[(x, y)] = "a"                             # sand
    last = None
    for dx in range(-half, half + 1):
        x = centre + dx
        pile = 1 - (dx / (half + 1)) ** 2
        bowl = math.sqrt(max(0.0, pile))
        top = ground - round(height * pile)
        if last is not None and abs(top - last) > 2:
            top = last + (2 if top > last else -2)
        last = top
        for y in range(top, ground + round(bury * bowl) + 1):
            solid[(x, y)] = "R"
    floor = ground - 2                                      # JunkyardPass.CacheFloorAboveGround
    left = centre - 1
    for dx in range(-1, 3):
        for y in range(floor - 3, floor):
            solid.pop((left + dx, y), None)
    for x in range(left + 3, centre + half + 2):            # the player's tunnel
        for y in range(floor - 3, floor):
            solid.pop((x, y), None)
    return cols, rows, ground, solid, left, floor - 2


def hand_ground(solid, left, top):
    floor, ground = top + 2, -1
    for off in HAND_COLUMN_OFFSETS:
        x = left + off
        for y in range(max(1, top - SURFACE_SCAN_ROWS), floor + 1):
            if (x, y) in solid:
                ground = max(ground, y)
                break
    return floor if ground < 0 else min(ground, floor)


def intro_gif(out, font_path):
    frames, glows = load_sheet()
    cols, rows, ground, solid, left, top = build_world()
    meta = load_frames("art/templates/terrain_exposure.json")
    grid = ["".join("#" if solid.get((x, y)) == "R" else "." for x in range(cols)) for y in range(rows)]
    scrap = render(grid, {"#": Image.open("Content/Scrap/Tiles/RustedScrapTile.png").convert("RGBA")}, meta, seed=6)
    world = Image.new("RGBA", (cols * 16, rows * 16))
    d = ImageDraw.Draw(world)
    for y in range(rows * 16):
        t = y / (rows * 16)
        d.line([0, y, cols * 16, y], fill=(int(150 - 40 * t), int(180 - 50 * t), int(210 - 40 * t), 255))
    for (cx, base, hw, hh) in ((500, ground * 16, 160, 100), (2150, ground * 16, 190, 130)):   # far heaps
        d.polygon([(cx - hw, base), (cx - hw // 3, base - hh), (cx + hw // 2, base - hh + 25), (cx + hw, base)], fill=(110, 118, 140, 255))
    rng = random.Random(3)
    for (x, y), ch in solid.items():
        if ch == "a":
            col = (220, 196, 128) if (x, y - 1) not in solid else (196, 170, 106)
            d.rectangle([x * 16, y * 16, x * 16 + 15, y * 16 + 15], fill=col + (255,))
            for _ in range(2):
                sx, sy = x * 16 + rng.randrange(0, 16, 2), y * 16 + rng.randrange(0, 16, 2)
                d.rectangle([sx, sy, sx + 1, sy + 1], fill=(184, 150, 92, 255))
    world.alpha_composite(scrap)
    trunk = Image.open("Content/Furniture/ScrappyTrunkTile.png").convert("RGBA")
    for x in range(2):
        for y in range(2):
            hgt = 16 if y == 0 else 18
            world.alpha_composite(trunk.crop((36 + x * 18, y * 18, 36 + x * 18 + 16, y * 18 + hgt)), ((left + x) * 16, (top + y) * 16))

    boss_bottom_row = hand_ground(solid, left, top)
    boss_x, boss_bottom = (left + 1) * 16.0, boss_bottom_row * 16.0
    focus = (boss_x, boss_bottom - FRAME_H * 0.55)
    player_pos = ((left + 3) * 16.0, (top + 2) * 16.0)       # standing in the tunnel next to the cache (feet)
    pl = player_sprite(0, flip=True)
    hud = ImageFont.truetype(font_path, 15)
    # BossTitleSystem at half scale: Death Text (about 44 px) x 1.25, Mouse Text (about 22 px) x 0.9
    name_px, epithet_px = int(44 * 1.25 * 0.5), int(22 * 0.9 * 0.5) + 1
    rng = random.Random(9)
    particles = []                                           # [x, y, vx, vy, life, colour, size]
    gif = []
    start, end = -45, EMERGE + 150
    frame_counter, frame = 0, 0
    for tick in range(start, end):
        state = "emerge" if 0 <= tick < EMERGE else ("idle" if tick >= EMERGE else "asleep")
        # camera: centred on the player, eased onto the boss while it emerges
        lock = camera_lock(tick)
        lock = lock * lock * (3 - 2 * lock)
        cam_x = player_pos[0] + 10 + (focus[0] - player_pos[0] - 10) * lock - SCREEN_W / 2
        cam_y = player_pos[1] - 21 + (focus[1] - player_pos[1] + 21) * lock - SCREEN_H / 2
        shake_x = shake_y = 0.0
        if 1 <= tick < RUMBLE + RISE:                         # rumble: PunchCameraModifier(UnitY, 3, 12/s, 180)
            p = (tick - 1) / (RUMBLE + RISE)
            shake_y = 3 * (1 - p) * math.sin(math.tau * 12 * tick / 60)
        if RUMBLE + RISE <= tick < RUMBLE + RISE + 40:       # roar: PunchCameraModifier(UnitX, 9, 10/s, 40)
            p = (tick - RUMBLE - RISE) / 40
            shake_x = 9 * (1 - p) * math.sin(math.tau * 10 * tick / 60)
        cam_x, cam_y = round(cam_x + shake_x), round(cam_y + shake_y)
        # animation (FindFrame)
        tpf = ROAR_TICKS_PER_FRAME if state == "emerge" and tick >= RUMBLE + RISE else TICKS_PER_FRAME
        frame_counter += 1
        if frame_counter >= tpf:
            frame_counter = 0
            frame = (frame + 1) % FRAME_COUNT
        buried = buried_pixels(state, tick) if state != "asleep" else FRAME_H
        # particles
        if state == "emerge" and tick < RUMBLE + RISE and tick % 2 == 0:
            for _ in range(1 if tick < RUMBLE else 3):
                x = boss_x - FRAME_W * 0.4 + rng.random() * FRAME_W * 0.8
                particles.append([x, boss_bottom - 2, rng.uniform(-1.2, 1.2), rng.uniform(-3.5, -1.5), 40,
                                  rng.choice([(147, 68, 31), (94, 40, 23), (196, 104, 58)]), 4])
        if state == "emerge" and RUMBLE <= tick < RUMBLE + RISE and tick % 6 == 0:
            for _ in range(2):
                wx = boss_x - FRAME_W / 2 + rng.randint(WAIST_LEFT, WAIST_RIGHT)
                wy = boss_bottom - FRAME_H + buried + WAIST_Y
                if wy < boss_bottom:
                    particles.append([wx, wy, rng.uniform(-1.5, 1.5), rng.uniform(0.5, 2.5), 25, (255, 199, 90), 2])
        roaring = state == "emerge" and tick >= RUMBLE + RISE
        if (roaring and tick % 15 == 0) or (state == "idle" and tick % 24 == 0):
            for _ in range(3 if roaring else 1):
                ex, ey = EXHAUST[rng.randrange(2)]
                particles.append([boss_x - FRAME_W / 2 + ex, boss_bottom - FRAME_H + ey, rng.uniform(-0.4, 0.4),
                                  -rng.uniform(1.5, 2.5), 50, (195, 200, 205), 6])
        for q in particles:
            q[0] += q[2]
            q[1] += q[3]
            q[3] += 0.12 if q[6] < 6 else -0.01
            q[4] -= 1
        particles = [q for q in particles if q[4] > 0]
        if (tick - start) % TPF:
            continue
        # --- draw a screen ---------------------------------------------------------------------------------------
        img = world.crop((cam_x, cam_y, cam_x + SCREEN_W, cam_y + SCREEN_H))
        if buried < FRAME_H:
            visible = FRAME_H - buried
            part = frames[frame].crop((0, 0, FRAME_W, visible))
            gx = round(boss_x - FRAME_W / 2 - cam_x)
            gy = round(boss_bottom - visible - cam_y)
            img.alpha_composite(part, (gx, gy))
        img.alpha_composite(pl, (round(player_pos[0] - 10 - cam_x), round(player_pos[1] - 56 - cam_y)))
        dd = ImageDraw.Draw(img)
        for (x, y, vx, vy, life, colour, size) in particles:
            sx, sy = x - cam_x, y - cam_y
            a = min(1.0, life / 20)
            c = tuple(int(v * a + 140 * (1 - a)) for v in colour) if size == 6 else colour
            dd.rectangle([sx, sy, sx + size - 1, sy + size - 1], fill=c)
        img = img.resize((SCREEN_W // 2, SCREEN_H // 2), Image.NEAREST)
        # title card (half-scale screen)
        op, scale = title_opacity(tick)
        if op > 0:
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            cx, cy = SCREEN_W // 4, int(SCREEN_H / 2 * TITLE_CENTRE)
            nf = ImageFont.truetype(font_path, max(8, int(name_px * scale)))
            small = ImageFont.truetype(font_path, epithet_px)
            name = "Trash-Tr0m"
            bb = ld.textbbox((0, 0), name, font=nf)
            nx, ny = cx - (bb[2] - bb[0]) // 2 - bb[0], cy - (bb[3] - bb[1]) // 2 - bb[1]
            for ox in (-2, 0, 2):
                for oy in (-2, 0, 2):
                    if ox or oy:
                        ld.text((nx + ox, ny + oy), name, font=nf, fill=NAME_SHADOW)
            ld.text((nx, ny), name, font=nf, fill=NAME_COLOR)
            ep = "Colossus of the Scrapheap"
            eb = ld.textbbox((0, 0), ep, font=small)
            ex, ey = cx - (eb[2] - eb[0]) // 2 - eb[0], cy - int(name_px * 0.5) - (eb[3] - eb[1]) - 4
            for ox in (-1, 1):
                ld.text((ex + ox, ey), ep, font=small, fill=EPITHET_SHADOW)
                ld.text((ex, ey + ox), ep, font=small, fill=EPITHET_SHADOW)
            ld.text((ex, ey), ep, font=small, fill=EPITHET_COLOR)
            ry = ey + (eb[3] - eb[1]) // 2 + 3
            ld.rectangle([ex - 7 - 60, ry, ex - 7, ry], fill=RULE_COLOR)
            ld.rectangle([ex + (eb[2] - eb[0]) + 7, ry, ex + (eb[2] - eb[0]) + 7 + 60, ry], fill=RULE_COLOR)
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * op)))
            img.alpha_composite(layer)
        dd = ImageDraw.Draw(img)
        if tick < 0:
            label = "the player right-clicks the sealed Junkyard Cache" if tick >= -24 else "digging into the central heap"
        else:
            label = f"Emerge {tick}/{EMERGE}" if state == "emerge" else "Idle (placeholder fight)"
        dd.text((8, 8), f"tick {tick:4d}  {label}", fill=(21, 22, 28), font=hud)
        dd.text((8, 28), f"camera lock {camera_lock(tick):.2f}   buried {buried} px   invulnerable {'yes' if state != 'idle' else 'no'}",
                fill=(21, 22, 28), font=hud)
        if tick >= 0:
            dd.text((8, SCREEN_H // 2 - 24), "Trash-Tr0m has awoken!", fill=(175, 75, 255), font=hud)
        if -24 <= tick < 0:
            hx, hy = ((left + 1) * 16 - cam_x) // 2, (top * 16 - cam_y - 18) // 2
            dd.rectangle([hx, hy, hx + 6, hy + 6], outline=(255, 255, 255))
        gif.append(img.convert("RGB"))
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=TPF * 1000 // 60, loop=0, optimize=True)
    print(f"{out}: {len(gif)} frames, {(end - start) / 60:.1f} s; boss bottom row {boss_bottom_row} (cache top row {top})")


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--sprite-out")
    ap_.add_argument("--intro-out")
    ap_.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a = ap_.parse_args()
    if a.sprite_out:
        sprite_png(a.sprite_out)
    if a.intro_out:
        intro_gif(a.intro_out, a.font)


if __name__ == "__main__":
    main()
