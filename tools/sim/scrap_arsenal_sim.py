"""D5 simulations of the scrap arsenal, using the real sprites and the constants of the C# code.

    python -P tools/sim/scrap_arsenal_sim.py --which all --out-dir docs/media --date <date>

Writes <date>_scrap-screwdriver.gif, -wand.gif, -bow.gif and -mice-bot.gif (3 game ticks per GIF frame, 20 fps).
* Screwdriver (Screwdriver.cs / ScrewdriverProjectile.cs): two thrusts over 31 ticks each; the tip eases from 40 to
  104 px = 6.5 tiles (SmoothStep), the shaft (grip to tip, 10 px wide) is the hitbox, and local immunity is cleared at the turn, so
  each dummy is hit once going out and once coming back. The second dummy is in the Mechanical set: +50%.
* Scrappy Wand (ScrappyWand.cs / ScrappyWandBolt.cs): three bursts; bolts at ticks 0, 4 and 8 of each 26-tick cycle,
  13 px per update with 2 updates per tick; bolts 2 and 3 stray up to 9 degrees; 9 mana per burst.
* Scrappy Bow (ScrappyBow.cs): four volleys every 30 ticks of 1-5 arrows (rolled), extras stray up to 5 degrees at
  90-100% speed. Arrows follow vanilla aiStyle 1 (decompiled Projectile.AI_001: +0.1 px/tick gravity after 15 ticks)
  at 7 + 3 px/tick (the bow's speed plus a Wooden Arrow's).
* Mice-bot (MiceBotMinion.cs): the mouse idles by its owner, spots a hopping slime, runs at it (0.6 px/tick² up to
  9 px/tick), pounces just high enough when the slime hops above it, bites every 15 ticks (local immunity) for 8 damage, then runs home.

Leaves out: lighting, terrain (flat ground; no step-ups), knockback, crits, NPC AI (stand-in dummies and slimes),
the player's arm animation (fixed pose), vanilla arrow and target sprites (plain stand-ins), netcode.
Python's RNG stands in for Main.rand (same rules, different rolls).
"""
import argparse
import math
import os
import random
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armor_preview as ap  # noqa: E402

# --- mirrored from the C# code -------------------------------------------------------------------------------------
SD_DAMAGE, SD_USE, SD_REACH_MIN, SD_REACH_MAX, SD_LENGTH, SD_WIDTH, SD_GRIP, SD_MECH = 20, 31, 40.0, 104.0, 54.0, 10.0, 8.0, 50
WAND_DAMAGE, WAND_SHOTS, WAND_DELAY, WAND_CYCLE, WAND_MANA, WAND_SPREAD, WAND_SPEED, WAND_MUZZLE, BOLT_LIFE = 18, 3, 4, 26, 9, 9.0, 13.0, 40.0, 60
BOW_DAMAGE, BOW_USE, BOW_MIN, BOW_MAX, BOW_SPREAD, BOW_SPEED, ARROW_SPEED = 20, 30, 1, 5, 5.0, 7.0, 3.0
MICE_DAMAGE, MICE_COOLDOWN, MICE_RUN, MICE_FOLLOW, MICE_CATCH_UP, MICE_ACCEL = 8, 15, 9.0, 6.0, 10.0, 0.6
MICE_JUMP, MICE_GRAVITY, MICE_MAX_FALL, MICE_RUN_ANIM, MICE_W, MICE_H, MICE_TARGET_RANGE = 8.0, 0.4, 10.0, 6.0, 20, 14, 640.0
# --------------------------------------------------------------------------------------------------------------------
TPF = 3
BOB = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3
SKY, GROUND_COL, GRASS = (150, 180, 210, 255), (91, 54, 38), (71, 145, 126)
INK, SUB, GOLD = (21, 22, 28), (46, 50, 59), (255, 199, 90)


def smoothstep(a, b, t):
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t * t * (3 - 2 * t)


def player_sprite(frame=0, flip=False):
    heads = ap.load_frames("Content/Scrap/Armor/ScrapHelmet_Head.png", 4)
    bodies = ap.load_frames("Content/Scrap/Armor/ScrapBreastplate_Body.png", 4)
    legs = ap.load_frames("Content/Scrap/Armor/ScrapLeggings_Legs.png", 4)
    img = ap.compose(heads[0], bodies[0], legs[0], frame, BOB)
    return img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img


def scene(w, h, ground):
    img = Image.new("RGBA", (w, h), SKY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, ground, w, h], fill=GROUND_COL)
    d.rectangle([0, ground, w, ground + 1], fill=GRASS)
    return img, d


def popup(d, popups, tick):
    for (x, y, text, born, col) in popups:
        age = tick - born
        if 0 <= age < 40:
            d.text((x - 8, y - age * 0.5), text, fill=col, stroke_width=1, stroke_fill=INK)


def save(frames, out, zoom=2):
    frames = [f.convert("RGB").resize((f.width * zoom, f.height * zoom), Image.NEAREST) for f in frames]
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=TPF * 1000 // 60, loop=0)


def rect_hits_line(rect, a, b, width):
    """AABB vs thick segment, sampled every 2 px along the segment (stand-in for Collision.CheckAABBvLineCollision)."""
    x0, y0, x1, y1 = rect
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2))
    for k in range(n + 1):
        t = k / n
        px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        if x0 - width / 2 <= px <= x1 + width / 2 and y0 - width / 2 <= py <= y1 + width / 2:
            return True
    return False


# ------------------------------------------------------------------------------------------------------------------
def sim_screwdriver(out):
    W, H, G = 480, 150, 126
    proj = Image.open("Content/Scrap/Weapons/ScrewdriverProjectile.png").convert("RGBA")
    px = 240.0
    centre = (px, G - 21)
    dummies = [dict(rect=(330, G - 40, 350, G), mech=False, label="dummy"),           # right: 5.6-6.9 tiles
               dict(rect=(130, G - 40, 150, G), mech=True, label="mechanical")]        # left
    plan = [(0, 1), (SD_USE + 20, -1)]                                                 # (start tick, direction)
    total = 2 * SD_USE + 50
    popups, frames, hits = [], [], []
    for tick in range(total):
        active = None
        for (start, direction) in plan:
            if start <= tick < start + SD_USE:
                active = (start, direction)
        img, d = scene(W, H, G)
        for dm in dummies:
            x0, y0, x1, y1 = dm["rect"]
            d.rectangle([x0, y0, x1, y1], fill=(79, 85, 98) if dm["mech"] else (138, 90, 60), outline=INK)
            d.text((x0 - 10, y1 + 6), dm["label"], fill=(238, 241, 243))
        facing = active[1] if active else 1
        img.alpha_composite(player_sprite(3 if active else 0, flip=facing < 0), (int(px) - 20, G - 56))
        if active:
            start, direction = active
            time_left = SD_USE - (tick - start)            # Projectile.timeLeft after the clamp
            half = SD_USE / 2
            returning = time_left < half
            key = (start, returning)
            progress = time_left / half if returning else (SD_USE - time_left) / half
            tip_d = smoothstep(SD_REACH_MIN, SD_REACH_MAX, progress)
            mid = (centre[0] + direction * (tip_d - SD_LENGTH / 2), centre[1])
            tip = (centre[0] + direction * tip_d, centre[1])
            grip = (centre[0] + direction * (tip_d - SD_LENGTH + SD_GRIP), centre[1])
            spr = proj if direction > 0 else proj.transpose(Image.FLIP_LEFT_RIGHT)
            img.alpha_composite(spr, (int(mid[0] - spr.width / 2), int(mid[1] - spr.height / 2)))
            for dm in dummies:
                if key not in dm.setdefault("hit", set()) and rect_hits_line(dm["rect"], grip, tip, SD_WIDTH):
                    dm["hit"].add(key)
                    dmg = int(SD_DAMAGE * (1 + SD_MECH / 100)) if dm["mech"] else SD_DAMAGE
                    popups.append(((dm["rect"][0] + dm["rect"][2]) / 2 - (8 if returning else 0), dm["rect"][1] - (20 if returning else 6),
                                   f"{dmg} {'back' if returning else 'out'}", tick, GOLD))
                    hits.append((tick, dm["label"], "back" if returning else "out", dmg))
            d.text((6, 18), f"tip {tip_d / 16:.1f} tiles ({'returning' if returning else 'thrusting'})", fill=SUB)
        # 6.5-tile ruler
        for k in range(7):
            x = centre[0] + facing * k * 16
            d.line([x, G + 14, x, G + 18], fill=(238, 241, 243))
        d.line([centre[0], G + 16, centre[0] + facing * SD_REACH_MAX, G + 16], fill=(238, 241, 243))
        d.text((centre[0] + facing * SD_REACH_MAX - (40 if facing < 0 else 0), G + 20), "6.5 tiles", fill=(238, 241, 243))
        popup(d, popups, tick)
        d.text((6, 4), "Screwdriver: 31-tick thrust to 6.5 tiles, hits going out and coming back", fill=INK)
        if tick % TPF == 0:
            frames.append(img)
    save(frames, out)
    print(out, len(frames), "frames; hits:", hits)


# ------------------------------------------------------------------------------------------------------------------
def sim_wand(out, rng):
    W, H, G = 480, 200, 176
    bolt = Image.open("Content/Scrap/Weapons/ScrappyWandBolt.png").convert("RGBA")
    wand = Image.open("Content/Scrap/Weapons/ScrappyWand.png").convert("RGBA")
    px, centre = 50.0, (50.0, G - 21)
    target = (380, G - 64, 404, G - 16)
    aim_at = ((target[0] + target[2]) / 2, (target[1] + target[3]) / 2)
    base = math.atan2(aim_at[1] - centre[1], aim_at[0] - centre[0])
    bolts, popups, frames = [], [], []
    mana, fired = 40, 0
    bursts = 3
    for tick in range(bursts * WAND_CYCLE + 40):
        cycle, t = divmod(tick, WAND_CYCLE)
        if cycle < bursts:
            if t == 0:
                mana -= WAND_MANA                       # paid once when the animation starts
            if t % WAND_DELAY == 0 and t // WAND_DELAY < WAND_SHOTS:
                shot = t // WAND_DELAY + 1              # ItemUsesThisAnimation as the Shoot hook sees it
                ang = base + (math.radians(rng.uniform(-WAND_SPREAD, WAND_SPREAD)) if shot > 1 else 0.0)
                bolts.append(dict(x=centre[0] + math.cos(ang) * WAND_MUZZLE, y=centre[1] + math.sin(ang) * WAND_MUZZLE,
                                  vx=math.cos(ang) * WAND_SPEED, vy=math.sin(ang) * WAND_SPEED, life=BOLT_LIFE, rot=ang, shot=shot))
                fired += 1
        for b in bolts:
            for _ in range(2):                          # extraUpdates = 1
                if b["life"] <= 0:
                    break
                b["x"] += b["vx"]
                b["y"] += b["vy"]
                b["life"] -= 1
                if target[0] <= b["x"] <= target[2] and target[1] <= b["y"] <= target[3]:
                    popups.append((b["x"], target[1] - 6, str(WAND_DAMAGE), tick, GOLD))
                    b["life"] = 0
        if tick % TPF:
            continue
        img, d = scene(W, H, G)
        d.rectangle(list(target), fill=(138, 90, 60), outline=INK)
        img.alpha_composite(player_sprite(3), (int(px) - 20, G - 56))
        w = wand.rotate(-math.degrees(base) - 45, resample=Image.NEAREST, expand=True)
        img.alpha_composite(w, (int(centre[0] + math.cos(base) * 14 - w.width / 2), int(centre[1] + math.sin(base) * 14 - w.height / 2)))
        for b in bolts:
            if b["life"] > 0:
                spr = bolt.rotate(-math.degrees(b["rot"]), resample=Image.NEAREST, expand=True)
                img.alpha_composite(spr, (int(b["x"] - spr.width / 2), int(b["y"] - spr.height / 2)))
        popup(d, popups, tick)
        d.text((6, 4), "Scrappy Wand: 3-bolt burst every 26 ticks; only the first bolt is on target", fill=INK)
        d.text((6, 16), f"mana {mana}/40 (9 per burst)   bolts fired {fired}", fill=SUB)
        frames.append(img)
    save(frames, out)
    print(out, len(frames), "frames; hits", len(popups), "of", fired)


# ------------------------------------------------------------------------------------------------------------------
def sim_bow(out, rng):
    W, H, G = 520, 200, 176
    bow = Image.open("Content/Scrap/Weapons/ScrappyBow.png").convert("RGBA")
    px, centre = 50.0, (50.0, G - 21)
    target = (430, G - 56, 454, G)
    base = math.atan2(((target[1] + target[3]) / 2) - centre[1] - 14, target[0] - centre[0])
    arrows, popups, frames, counts = [], [], [], []
    volleys = 4
    for tick in range(volleys * BOW_USE + 50):
        cycle, t = divmod(tick, BOW_USE)
        if cycle < volleys and t == 0:
            n = rng.randint(BOW_MIN, BOW_MAX)
            counts.append(n)
            for i in range(n):
                ang, speed = base, BOW_SPEED + ARROW_SPEED
                if i > 0:
                    ang += math.radians(rng.uniform(-BOW_SPREAD, BOW_SPREAD))
                    speed *= rng.uniform(0.9, 1.0)
                arrows.append(dict(x=centre[0], y=centre[1], vx=math.cos(ang) * speed, vy=math.sin(ang) * speed, age=0, live=True))
        for a in arrows:
            if not a["live"]:
                continue
            a["age"] += 1
            if a["age"] >= 15:
                a["vy"] = min(a["vy"] + 0.1, 16.0)
            a["x"] += a["vx"]
            a["y"] += a["vy"]
            if target[0] <= a["x"] <= target[2] and target[1] <= a["y"] <= target[3]:
                popups.append((a["x"], target[1] - 6, str(BOW_DAMAGE + 5), tick, GOLD))
                a["live"] = False
            elif a["y"] >= G or a["x"] > W:
                a["live"] = False
        if tick % TPF:
            continue
        img, d = scene(W, H, G)
        d.rectangle(list(target), fill=(138, 90, 60), outline=INK)
        img.alpha_composite(player_sprite(3), (int(px) - 20, G - 56))
        img.alpha_composite(bow, (int(centre[0] + 8), int(centre[1] - bow.height / 2)))
        for a in arrows:
            if a["live"]:
                ang = math.atan2(a["vy"], a["vx"])
                tail = (a["x"] - math.cos(ang) * 14, a["y"] - math.sin(ang) * 14)
                d.line([tail, (a["x"], a["y"])], fill=(138, 90, 60), width=2)
                d.rectangle([a["x"] - 1, a["y"] - 1, a["x"] + 1, a["y"] + 1], fill=(183, 191, 202))
        popup(d, popups, tick)
        last = counts[-1] if counts else 0
        d.text((6, 4), "Scrappy Bow: 1-5 arrows per shot, one arrow consumed", fill=INK)
        d.text((6, 16), f"this volley: {last} arrow{'s' if last != 1 else ''}   volleys so far: {counts}", fill=SUB)
        frames.append(img)
    save(frames, out)
    print(out, len(frames), "frames; volleys", counts, "hits", len(popups), "of", sum(counts))


# ------------------------------------------------------------------------------------------------------------------
def sim_mice(out):
    W, H, G = 560, 160, 136
    sheet = Image.open("Content/Scrap/Minions/MiceBotMinion.png").convert("RGBA")
    fh = sheet.height // 8
    mframes = [sheet.crop((0, i * fh, sheet.width, (i + 1) * fh)) for i in range(8)]
    owner_x = 60.0
    m = dict(x=owner_x + 28.0, y=G - MICE_H, vx=0.0, vy=0.0, frame=0, run=0.0, bite=0, dir=1, ground=True)
    slime = dict(x=520.0, y=G, life=64, vx=-1.1, vy=0.0, dead_at=None)
    immunity, popups, frames, bites = 0, [], [], 0
    total = 330
    for tick in range(total):
        # slime: creeps left, hops every 50 ticks
        if slime["life"] > 0:
            slime["vy"] = slime["vy"] + 0.4 if slime["y"] < G or slime["vy"] < 0 else 0.0
            if tick % 50 == 25 and slime["y"] >= G:
                slime["vy"] = -6.0
            slime["x"] += slime["vx"]
            slime["y"] = min(G, slime["y"] + slime["vy"])
        srect = (slime["x"] - 14, slime["y"] - 20, slime["x"] + 14, slime["y"])
        mcx = m["x"] + MICE_W / 2
        target = slime["life"] > 0 and abs(slime["x"] - mcx) < MICE_TARGET_RANGE
        grounded = m["ground"]
        if m["bite"] > 0:
            m["bite"] -= 1
        if target:
            dx, top = slime["x"] - mcx, MICE_RUN
        else:
            dx = (owner_x + 28) - mcx
            top = MICE_CATCH_UP if abs(dx) > 160 else MICE_FOLLOW
        wants = abs(dx) > (6 if target else 16)
        if wants:
            m["vx"] = max(-top, min(top, m["vx"] + math.copysign(MICE_ACCEL, dx)))
            m["dir"] = 1 if dx > 0 else -1
        else:
            m["vx"] *= 0.8
            if abs(m["vx"]) < 0.05:
                m["vx"] = 0.0
        if grounded and target and slime["y"] < (m["y"] + MICE_H) - 20 and abs(dx) < 160:
            height = (m["y"] + MICE_H) - (slime["y"] - 10)             # up to the slime's middle
            m["vy"] = -min(MICE_JUMP, math.sqrt(2 * MICE_GRAVITY * max(height, 0.0)))
        m["vy"] = min(m["vy"] + MICE_GRAVITY, MICE_MAX_FALL)
        m["x"] += m["vx"]
        m["y"] += m["vy"]
        m["ground"] = False
        if m["y"] + MICE_H >= G:
            m["y"], m["vy"], m["ground"] = G - MICE_H, 0.0, True
        # contact bite with 15 ticks of local immunity
        if immunity > 0:
            immunity -= 1
        mrect = (m["x"], m["y"], m["x"] + MICE_W, m["y"] + MICE_H)
        if target and immunity == 0 and mrect[0] < srect[2] and srect[0] < mrect[2] and mrect[1] < srect[3] and srect[1] < mrect[3]:
            slime["life"] -= MICE_DAMAGE
            immunity, m["bite"] = MICE_COOLDOWN, 8
            bites += 1
            popups.append((slime["x"], srect[1] - 4, str(MICE_DAMAGE), tick, GOLD))
            if slime["life"] <= 0:
                slime["dead_at"] = tick
        # frame selection mirrored from MiceBotMinion.UpdateFrame
        if m["bite"] > 0:
            m["frame"] = 7
        elif not m["ground"] and abs(m["vy"]) > 0.5:
            m["frame"] = 6
        elif abs(m["vx"]) > 0.3:
            if not 2 <= m["frame"] < 6:
                m["frame"] = 2
            m["run"] += abs(m["vx"])
            if m["run"] >= MICE_RUN_ANIM:
                m["run"] = 0.0
                m["frame"] = 2 + ((m["frame"] - 2 + 1) % 4)
        else:
            m["frame"] = (tick // 30) % 2
        if tick % TPF:
            continue
        img, d = scene(W, H, G)
        img.alpha_composite(player_sprite(0), (int(owner_x) - 20, G - 56))
        if slime["life"] > 0:
            d.rounded_rectangle(list(srect), 6, fill=(71, 145, 126), outline=(23, 52, 48))
            d.text((srect[0], srect[1] - 12), str(slime["life"]), fill=INK)
        spr = mframes[m["frame"]]
        if m["dir"] < 0:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        img.alpha_composite(spr, (int(m["x"] + MICE_W / 2 - spr.width / 2), int(m["y"] + MICE_H - (spr.height - 2))))
        popup(d, popups, tick)
        state = "biting" if m["bite"] else ("chasing" if target else ("returning" if abs(dx) > 16 else "idle by its owner"))
        d.text((6, 4), f"Mice-bot: 8 damage per bite, 15 ticks between bites - {state}", fill=INK)
        d.text((6, 16), f"speed {abs(m['vx']):.1f} px/tick (max 9)   bites {bites}", fill=SUB)
        frames.append(img)
    save(frames, out)
    print(out, len(frames), "frames; bites", bites, "slime died at tick", slime["dead_at"])


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--which", default="all", choices=["all", "screwdriver", "wand", "bow", "mice"])
    a.add_argument("--out-dir", default="docs/media")
    a.add_argument("--date", required=True)
    a.add_argument("--seed", type=int, default=4)
    args = a.parse_args()
    rng = random.Random(args.seed)
    path = lambda name: os.path.join(args.out_dir, f"{args.date}_scrap-{name}.gif")  # noqa: E731
    if args.which in ("all", "screwdriver"):
        sim_screwdriver(path("screwdriver"))
    if args.which in ("all", "wand"):
        sim_wand(path("wand"), rng)
    if args.which in ("all", "bow"):
        sim_bow(path("bow"), rng)
    if args.which in ("all", "mice"):
        sim_mice(path("mice-bot"))


if __name__ == "__main__":
    main()
