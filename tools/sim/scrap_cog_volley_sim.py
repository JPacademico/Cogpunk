"""D5 simulation of the Scrap armor set bonus: while the player moves, a Scrap Cog is lobbed every 0.75 s. With an
enemy within 25 tiles it is aimed at it (the low ballistic arc for gravity 0.3 px/tick² at 10 px/tick, mirrored from
ScrapArmorPlayer.AimLob); with none it is thrown from the player's back, up and behind them. Gravity (max fall 16)
bends it into an arc; it breaks on the first enemy (70 damage) or bounces off up to 3 walls/floors and breaks on the
4th contact. Standing still pauses the volley; once the slimes are dead the cogs fly out behind the player. Uses the real armor sheets
(tools/sim/armor_preview.py composition), the Rusted Cog sprite, and the constants of
Content/Scrap/Armor/ScrapArmorPlayer.cs + ScrapCogProjectile.cs.

    python -P tools/sim/scrap_cog_volley_sim.py --out docs/media/<date>_scrap-armor-cog-lob.gif

Leaves out: lighting, uneven terrain (flat arena), enemy AI (stand-in slimes hop on a timer), knockback, netcode.
3 game ticks per GIF frame (20 fps, exact timing).
"""
import argparse
import math
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armor_preview as ap  # noqa: E402

# --- mirrored from ScrapArmorPlayer.cs / ScrapCogProjectile.cs ----------------------------------
COG_INTERVAL, COG_DAMAGE, COG_SPEED, LAUNCH_BACK, LAUNCH_UP = 45, 70, 10.0, 0.8, 0.6
COG_RANGE, BACK_OFFSET, MIN_AIM_DISTANCE = 25 * 16, 10.0, 8.0
MAX_BOUNCES, BOUNCE_DAMPING, LIFETIME, SPIN, SIZE = 3, 0.85, 150, 0.35, 18
GRAVITY, MAX_FALL = 0.3, 16.0
MOVING_SPEED = 0.5
CHEST_OFFSET_Y = -4
# -------------------------------------------------------------------------------------------------
RUN_SPEED = 3.0 * 1.12            # vanilla max run speed 3 px/tick, +12% from the set bonus
TICKS_PER_GIF_FRAME = 3
W, H, GROUND, WALL, CEILING = 640, 200, 176, 620, 20
BOB = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3


def aim_lob(dx, dy):
    """ScrapArmorPlayer.AimLob: low-arc launch velocity through (dx, dy) (y down), 45 degrees when out of reach."""
    g, v = GRAVITY, COG_SPEED
    side = 1.0 if dx >= 0 else -1.0
    x, up = max(abs(dx), MIN_AIM_DISTANCE), -dy
    root = v ** 4 - g * (g * x * x + 2 * up * v * v)
    if root < 0:
        return side * v * math.sqrt(0.5), -v * math.sqrt(0.5)
    a = math.atan((v * v - math.sqrt(root)) / (g * x))
    return side * v * math.cos(a), -v * math.sin(a)


class Slime:
    def __init__(self, x, life, hop_period, hop_phase, hop_height=46.0):
        self.x, self.life, self.period, self.phase, self.hop = x, life, hop_period, hop_phase, hop_height
        self.y = GROUND
        self.dead_at = None

    def update(self, tick):
        t = (tick + self.phase) % self.period
        self.y = GROUND - max(0.0, math.sin(math.pi * t / 30.0) * self.hop) if t < 30 else GROUND

    def rect(self):
        return (self.x - 14, self.y - 20, self.x + 14, self.y)


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--out", required=True)
    ap_.add_argument("--zoom", type=int, default=2)
    ap_.add_argument("--hop-phase", type=int, default=0)
    a = ap_.parse_args()

    heads = ap.load_frames("Content/Scrap/Armor/ScrapHelmet_Head.png", 4)
    bodies = ap.load_frames("Content/Scrap/Armor/ScrapBreastplate_Body.png", 4)
    legs = ap.load_frames("Content/Scrap/Armor/ScrapLeggings_Legs.png", 4)
    cog_img = Image.open("Content/Scrap/Items/RustedCog.png").convert("RGBA")

    slimes = [Slime(330, 70, 9999, 0), Slime(560, 70, 34, a.hop_phase, hop_height=60.0)]
    px, timer = 30.0, 0
    launches = []                   # (x, y, tick, label) for the "aimed" / "behind" tags
    cogs = []                       # dicts: x, y, vx, vy, rot, bounces, age
    popups, sparks = [], []
    frames = []
    total = 240
    for tick in range(total):
        if tick < 150:
            vx = RUN_SPEED                           # walk right: two aimed cogs, then two thrown behind
        else:
            vx = 0.0                                 # stand still: the volley pauses
        px += vx
        for s in slimes:
            s.update(tick)

        # set bonus (ScrapArmorPlayer.PostUpdate)
        chest = (px, GROUND - 21 + CHEST_OFFSET_Y)
        if abs(vx) >= MOVING_SPEED:
            if timer < COG_INTERVAL:
                timer += 1
            else:
                direction = 1 if vx > 0 else -1          # Player.direction follows the walk
                best, best_d = None, COG_RANGE ** 2      # FindTarget (flat arena: always in line of sight)
                for s in slimes:
                    if s.life <= 0:
                        continue
                    d2 = (s.x - chest[0]) ** 2 + (s.y - 10 - chest[1]) ** 2
                    if d2 < best_d:
                        best, best_d = s, d2
                if best is not None:
                    cvx, cvy = aim_lob(best.x - chest[0], best.y - 10 - chest[1])
                    sx, label = chest[0], "aimed"
                else:
                    cvx, cvy = -LAUNCH_BACK * direction * COG_SPEED, -LAUNCH_UP * COG_SPEED
                    sx, label = chest[0] - direction * BACK_OFFSET, "behind"
                cogs.append(dict(x=sx, y=chest[1], vx=cvx, vy=cvy, rot=0.0, bounces=0, age=0, x0=sx, kind=label))
                launches.append((sx, chest[1] - 30, tick, label))
                timer = 0

        # projectiles (ScrapCogProjectile)
        for c in cogs:
            if c.get("dead"):
                continue
            c["age"] += 1
            c["vy"] = min(c["vy"] + GRAVITY, MAX_FALL)
            c["rot"] += SPIN * (1 if c["vx"] >= 0 else -1)
            nx, ny = c["x"] + c["vx"], c["y"] + c["vy"]
            hit_tile = False
            if ny + SIZE / 2 >= GROUND:
                c["vy"] = -c["vy"] * BOUNCE_DAMPING; ny = GROUND - SIZE / 2; hit_tile = True
            if ny - SIZE / 2 <= CEILING:
                c["vy"] = -c["vy"] * BOUNCE_DAMPING; ny = CEILING + SIZE / 2; hit_tile = True
            if nx + SIZE / 2 >= WALL:
                c["vx"] = -c["vx"] * BOUNCE_DAMPING; nx = WALL - SIZE / 2; hit_tile = True
            if nx - SIZE / 2 <= 0:
                c["vx"] = -c["vx"] * BOUNCE_DAMPING; nx = SIZE / 2; hit_tile = True
            c["x"], c["y"] = nx, ny
            if hit_tile:
                if c["bounces"] >= MAX_BOUNCES:
                    c["dead"] = True
                    sparks.append((c["x"], c["y"], tick, "break"))
                    continue
                if c["bounces"] == 0 and "first_dx" not in c:
                    c["first_dx"] = abs(c["x"] - c["x0"])
                c["bounces"] += 1
                sparks.append((c["x"], c["y"], tick, f"bounce {c['bounces']}"))
            for s in slimes:
                r = s.rect()
                if s.life > 0 and r[0] < c["x"] + SIZE / 2 and c["x"] - SIZE / 2 < r[2] and r[1] < c["y"] + SIZE / 2 and c["y"] - SIZE / 2 < r[3]:
                    s.life -= COG_DAMAGE
                    popups.append((s.x, r[1] - 4, str(COG_DAMAGE), tick))
                    c["dead"] = True
                    sparks.append((c["x"], c["y"], tick, ""))
                    break
            if c["age"] >= LIFETIME:
                c["dead"] = True

        if tick % TICKS_PER_GIF_FRAME:
            continue
        img = Image.new("RGBA", (W, H), (150, 180, 210, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, GROUND, W, H], fill=(91, 54, 38))
        d.rectangle([0, GROUND, W, GROUND + 1], fill=(71, 145, 126))
        d.rectangle([0, 0, W, CEILING], fill=(79, 85, 98), outline=(21, 22, 28))
        d.rectangle([WALL, 0, W, H], fill=(79, 85, 98), outline=(21, 22, 28))
        for s in slimes:
            if s.life > 0:
                x0, y0, x1, y1 = s.rect()
                d.rounded_rectangle([x0, y0, x1, y1], 6, fill=(71, 145, 126), outline=(23, 52, 48))
                d.text((x0, y0 - 12), f"{max(s.life, 0)}", fill=(21, 22, 28))
        anim = (tick // 6) % 4
        pose = 6 + (tick // 3) % 14 if abs(vx) > 0 else 0
        player = ap.compose(heads[anim], bodies[anim], legs[anim], pose, BOB)
        if vx < 0:
            player = player.transpose(Image.FLIP_LEFT_RIGHT)
        img.alpha_composite(player, (int(px) - 20, GROUND - 56))
        for c in cogs:
            if c.get("dead"):
                continue
            spr = cog_img.rotate(-math.degrees(c["rot"]), resample=Image.NEAREST, expand=True)
            img.alpha_composite(spr, (int(c["x"] - spr.width / 2), int(c["y"] - spr.height / 2)))
        for (sx, sy, born, label) in sparks:
            age = tick - born
            if 0 <= age < 12:
                for k in range(6):
                    ang = k * math.pi / 3 + born
                    rr = 3 + age
                    d.rectangle([sx + math.cos(ang) * rr - 1, sy + math.sin(ang) * rr - 1, sx + math.cos(ang) * rr + 1, sy + math.sin(ang) * rr + 1], fill=(196, 104, 58))
            if label and 0 <= age < 30:
                d.text((sx - 16, sy - 22), label, fill=(46, 50, 59))
        for (x, y, born, label) in launches:
            if 0 <= tick - born < 30:
                d.text((x - 14, y), label, fill=(163, 48, 26) if label == "behind" else (42, 94, 82))
        for (x, y, text, born) in popups:
            age = tick - born
            if 0 <= age < 50:
                d.text((x - 8, y - age * 0.4), text, fill=(255, 199, 90), stroke_width=1, stroke_fill=(21, 22, 28))
        alive = any(s.life > 0 for s in slimes)
        state = ("moving: cogs aimed at the nearest slime" if alive else "moving, no enemy: cogs thrown behind") if abs(vx) > 0 else "standing still: volley paused"
        d.text((6, 4), f"Scrap armor set bonus - {state}", fill=(238, 241, 243))
        d.text((6, 16), f"next cog in {max(0, COG_INTERVAL - timer)} ticks (fires every {COG_INTERVAL} ticks of movement)", fill=(195, 200, 205))
        frames.append(img.convert("RGB").resize((W * a.zoom, H * a.zoom), Image.NEAREST))

    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=TICKS_PER_GIF_FRAME * 1000 // 60, loop=0)
    bounces = sum(1 for sp in sparks if sp[3].startswith("bounce"))
    hits = sum(1 for p in popups)
    firsts = [round(c["first_dx"] / 16, 1) for c in cogs if "first_dx" in c]
    print("cog kinds:", [c["kind"] for c in cogs])
    print(f"{a.out}: {len(frames)} frames, {total / 60:.1f} s, cogs fired {len(cogs)}, enemy hits {hits}, bounces {bounces}, "
          f"first tile contact (tiles ahead) {firsts}")


if __name__ == "__main__":
    main()
