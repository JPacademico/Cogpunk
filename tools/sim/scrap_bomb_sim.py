"""D5 simulation of the Scrap Bomb: two throws at three target dummies.
Throw 1 hits a dummy directly (43 contact + 32 blast; the blast also reaches the neighbour).
Throw 2 lands on the ground (32 blast only to the dummies inside the 5-tile radius).
The dashed square is the Grenade's 8x8-tile blast, for comparison.
Uses the real projectile sheet and the constants of Content/Scrap/Weapons/ScrapBomb*.cs (keep in sync).

    python -P tools/sim/scrap_bomb_sim.py --out docs/media/<date>_scrap-bomb.gif

Leaves out: tile collision shapes (flat ground only), real dust/gore/lighting (approximated with specks),
knockback and netcode. 3 game ticks per GIF frame (20 fps, exact timing).
"""
import argparse
import math
import random
from PIL import Image, ImageDraw

# --- mirrored from ScrapBomb.cs / ScrapBombProjectile.cs ---------------------------------------
DIRECT_DAMAGE, EXPLOSION_DAMAGE = 43, 32
THROW_SPEED, GRAVITY, MAX_FALL, SPIN = 6.0, 0.2, 16.0, 0.08
FRAME_COUNT, FUSE_TICKS_PER_FRAME = 2, 3
FLIGHT_SIZE = 12
EXPLOSION_RADIUS = 80
GRENADE_HALF = 64          # vanilla Grenade: 8x8-tile square (terraria.wiki.gg, 1.4.4.9 source)
# -----------------------------------------------------------------------------------------------

TICKS_PER_GIF_FRAME = 3
W, H, GROUND = 420, 150, 130
THROWER_X = 40
HAND = (THROWER_X + 8, GROUND - 30)


def trajectory(angle_deg, max_ticks=300):
    x, y = HAND
    vx = THROW_SPEED * math.cos(math.radians(angle_deg))
    vy = -THROW_SPEED * math.sin(math.radians(angle_deg))
    rot = 0.0
    for tick in range(max_ticks):
        vy = min(vy + GRAVITY, MAX_FALL)
        rot += vx * SPIN
        x += vx
        y += vy
        yield tick, x, y, rot


def first_hit(angle, dummies):
    for tick, x, y, rot in trajectory(angle):
        box = (x - FLIGHT_SIZE / 2, y - FLIGHT_SIZE / 2, x + FLIGHT_SIZE / 2, y + FLIGHT_SIZE / 2)
        for i, d in enumerate(dummies):
            if box[2] > d[0] and box[0] < d[2] and box[3] > d[1] and box[1] < d[3]:
                return tick, x, y, i
        if box[3] >= GROUND:
            return tick, x, y, None
    return None


def in_blast(centre, rect):
    cx = min(max(centre[0], rect[0]), rect[2])
    cy = min(max(centre[1], rect[1]), rect[3])
    return (centre[0] - cx) ** 2 + (centre[1] - cy) ** 2 <= EXPLOSION_RADIUS ** 2


def dummy_rect(x):
    return (x - 10, GROUND - 40, x + 10, GROUND)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default="Content/Scrap/Weapons/ScrapBombProjectile.png")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zoom", type=int, default=2)
    a = ap.parse_args()

    sheet = Image.open(a.sheet).convert("RGBA")
    fh = sheet.height // FRAME_COUNT
    frames = [sheet.crop((0, i * fh, sheet.width, i * fh + fh - 2)) for i in range(FRAME_COUNT)]

    # Place the first dummy where a 45-degree throw comes down, the others to its right.
    land = first_hit(45, [])
    t1 = int(land[1]) + 4
    dummies = [dummy_rect(t1), dummy_rect(t1 + 40), dummy_rect(t1 + 110)]

    # Throw 1: the angle whose first contact is dummy 0. Throw 2: lands on the ground just in front of dummy 0.
    throws = []
    for want in (0, None):
        best = None
        for tenth in range(50, 800):
            angle = tenth / 10
            hit = first_hit(angle, dummies)
            if hit is None:
                continue
            if want == 0 and hit[3] == 0:
                best = angle
                break
            if want is None and hit[3] is None and abs(hit[1] - (dummies[0][0] - 35)) < 4:
                best = angle
                break
        throws.append(best)

    rng = random.Random(3)
    gif = []
    popups = []           # (x, y, text, colour, born_tick)
    tick_global = 0
    for throw_index, angle in enumerate(throws):
        if angle is None:
            continue
        hit_tick, hx, hy, target = first_hit(angle, dummies)
        sparks = []
        for tick, x, y, rot in trajectory(angle, hit_tick + 1 + 48):
            exploded = tick > hit_tick
            if tick == hit_tick + 1:
                centre = (hx, hy)
                if target is not None:
                    d = dummies[target]
                    popups.append(((d[0] + d[2]) / 2, d[1] - 6, str(DIRECT_DAMAGE), (233, 160, 107), tick_global))
                for i, d in enumerate(dummies):
                    if in_blast(centre, d):
                        dx = 10 if (target is not None and i == target) else 0
                        popups.append(((d[0] + d[2]) / 2 + dx, d[1] - 18, str(EXPLOSION_DAMAGE), (255, 199, 90), tick_global + 2))
                for _ in range(40):
                    ang = rng.uniform(0, 2 * math.pi)
                    spd = rng.uniform(1.0, 4.5)
                    col = rng.choice([(255, 199, 90), (236, 113, 40), (163, 48, 26), (138, 144, 150), (147, 68, 31)])
                    sparks.append([hx, hy, math.cos(ang) * spd, math.sin(ang) * spd - 1, col])
            for s in sparks:
                s[0] += s[2]; s[1] += s[3]; s[2] *= 0.9; s[3] = s[3] * 0.9 + 0.08

            if tick_global % TICKS_PER_GIF_FRAME == 0:
                img = Image.new("RGBA", (W, H), (150, 180, 210, 255))
                d = ImageDraw.Draw(img)
                d.rectangle([0, GROUND, W, H], fill=(91, 54, 38))
                d.rectangle([0, GROUND, W, GROUND + 1], fill=(71, 145, 126))
                d.rectangle([THROWER_X - 8, GROUND - 42, THROWER_X + 7, GROUND - 1], fill=(79, 85, 98))   # thrower stand-in
                d.rectangle([THROWER_X - 6, GROUND - 42, THROWER_X + 5, GROUND - 31], fill=(127, 135, 148))
                for rect in dummies:                                                                     # target dummy stand-ins
                    d.rectangle(rect, fill=(138, 90, 60), outline=(47, 27, 20))
                if not exploded:
                    sprite = frames[(tick // FUSE_TICKS_PER_FRAME) % FRAME_COUNT]
                    sprite = sprite.rotate(-math.degrees(rot), resample=Image.NEAREST, expand=True)
                    img.alpha_composite(sprite, (int(x - sprite.width / 2), int(y - sprite.height / 2)))
                else:
                    age = tick - hit_tick
                    if age <= 4:
                        r = EXPLOSION_RADIUS * (0.4 + 0.15 * age)
                        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(255, 199, 90))
                    if age <= 30:
                        d.ellipse([hx - EXPLOSION_RADIUS, hy - EXPLOSION_RADIUS, hx + EXPLOSION_RADIUS, hy + EXPLOSION_RADIUS],
                                  outline=(238, 241, 243))
                        for k in range(-GRENADE_HALF, GRENADE_HALF, 8):          # dashed Grenade square
                            for (x0, y0, x1, y1) in ((hx + k, hy - GRENADE_HALF, hx + k + 4, hy - GRENADE_HALF),
                                                     (hx + k, hy + GRENADE_HALF, hx + k + 4, hy + GRENADE_HALF),
                                                     (hx - GRENADE_HALF, hy + k, hx - GRENADE_HALF, hy + k + 4),
                                                     (hx + GRENADE_HALF, hy + k, hx + GRENADE_HALF, hy + k + 4)):
                                d.line([x0, y0, x1, y1], fill=(46, 50, 59))
                    for s in sparks:
                        d.rectangle([s[0] - 1, s[1] - 1, s[0] + 1, s[1] + 1], fill=s[4])
                for (px, py, text, colour, born) in popups:
                    age = tick_global - born
                    if 0 <= age < 60:
                        d.text((px - 6, py - age * 0.4), text, fill=colour, stroke_width=1, stroke_fill=(21, 22, 28))
                label = f"throw {throw_index + 1}: " + (f"direct hit = {DIRECT_DAMAGE} + {EXPLOSION_DAMAGE} blast" if target is not None else f"ground hit = {EXPLOSION_DAMAGE} blast only")
                d.text((6, 4), label, fill=(21, 22, 28))
                d.text((6, 16), f"blast radius {EXPLOSION_RADIUS // 16} tiles ({EXPLOSION_RADIUS} px), dashed = Grenade 8x8", fill=(46, 50, 59))
                gif.append(img.convert("RGB").resize((W * a.zoom, H * a.zoom), Image.NEAREST))
            tick_global += 1

    gif[0].save(a.out, save_all=True, append_images=gif[1:], duration=TICKS_PER_GIF_FRAME * 1000 // 60, loop=0)
    print(f"{a.out}: {len(gif)} frames, {tick_global / 60:.1f} s, throw angles {throws}")


if __name__ == "__main__":
    main()
