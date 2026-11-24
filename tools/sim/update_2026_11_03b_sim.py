"""D5 proofs for the second request of 2026-11-03: the Beat-Boxer and its Spring Punch (Content/Dungeon), the Spring
Gloves and Friendobô (Content/Town), built from the real sprite sheets, the generated rig data and the constants parsed
out of the C# files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_03b_sim.py --out docs/media [--only sprites,boxer,friendobo]

Writes:
    2026-11-03_dungeon-town-sprites.png  every Beat-Boxer frame (its planes composited at the rig origin), the two fists
                                         and the spring cell, the Spring Gloves, and Friendobô's 25 frames and head, at 2x,
                                         on a dark and a light background.
    2026-11-03_dungeon-beat-boxer.gif    the Beat-Boxer walking in at the Angry Bones' pace, the telegraph (fists cocked),
                                         the volley of two spring punches (SpringPunch.Extension, the reach locked when the
                                         volley starts): a standing player takes the glove and is knocked out of the mic's
                                         reach; after the cooldown, a player who jumps too early clears the glove and the
                                         mic catches the fall. Then the drops.
    2026-11-03_town-friendobo.gif        Friendobô in a Weathered Plank room: standing, blinking, walking (frames 2-15),
                                         talking, and throwing a mug at a Rust Collector (frames 21-24, the Tavernkeep's
                                         attack: 24 damage).

Leaves out: lighting, tiles beyond a flat floor, vanilla's exact player physics (approximated: the hurt launch is
decompiled Player.Hurt's, knockback x hit direction sideways and knockback x 7/9 up, with the hostile base 4.5 x the
punch's multiplier; then gravity 0.4, run slowdown 0.2 on the ground and 0.1 in the air, 40 ticks of immunity), vanilla's own sprites (the player is the sims' stand-in, the Ale mug a stand-in), spawning, netcode.
Numbers are Expert's.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, consts, load, player_sprite, collector_sprite, TPF  # noqa: E402
from update_2026_11_03_sim import Planes, numbers  # noqa: E402

KB = consts("Content/Dungeon/NPCs/BeatBoxer.cs", "Content/Dungeon/NPCs/BeatBoxerRigData.cs", "Content/Dungeon/Projectiles/SpringPunch.cs")
KG = consts("Content/Dungeon/Items/SpringGloves.cs")
KF = consts("Content/Town/Friendobo.cs")
EMBER = (255, 199, 90)
HURT = (255, 90, 70)
STEAM = (238, 241, 243)
FIST_W, FIST_H, SPRING_CELL, SPRING_H = 28, 24, 8, 10       # SpringPunch's private drawing sizes
PLAYER_W, PLAYER_H = 20, 42
GRAVITY, JUMP_SPEED, JUMP_HOLD = 0.4, 5.01, 15           # vanilla player (approximated)
IMMUNITY = 40
FR_W, FR_H = 40, 56


def extension(age):
    """SpringPunch.Extension: eased out, held, reeled back."""
    if age < KB["OutTicks"]:
        t = (age + 1.0) / KB["OutTicks"]
        return 1.0 - (1.0 - t) * (1.0 - t)
    if age < KB["OutTicks"] + KB["HoldTicks"]:
        return 1.0
    back = (age - KB["OutTicks"] - KB["HoldTicks"] + 1.0) / KB["BackTicks"]
    return max(0.0, 1.0 - back * back)


def dungeon_backdrop(w, h, ground):
    """Blue dungeon brick behind, a brick floor."""
    img = Image.new("RGBA", (w, h), (30, 34, 56, 255))
    d = ImageDraw.Draw(img)
    for row, y in enumerate(range(0, ground, 16)):
        off = 0 if row % 2 == 0 else 16
        for x in range(-off, w, 32):
            d.rectangle([x + 1, y + 1, x + 30, y + 14], fill=(44, 52, 86, 255))
            d.line([x + 1, y + 1, x + 29, y + 1], fill=(56, 66, 104, 255))
    d.rectangle([0, ground, w, h], fill=(64, 78, 124, 255))
    for x in range(0, w, 32):
        d.line([x, ground, x, h], fill=(40, 48, 82, 255))
    d.line([0, ground, w, ground], fill=(96, 112, 164, 255))
    return img


class Player:
    def __init__(self, x, ground):
        self.x, self.y, self.vx, self.vy = float(x), float(ground), 0.0, 0.0     # y = feet
        self.ground = ground
        self.immune = 0
        self.hold = 0
        self.run = 0                                         # -1, 0, 1: scripted input

    def box(self):
        return (self.x - PLAYER_W / 2, self.y - PLAYER_H, self.x + PLAYER_W / 2, self.y)

    def jump(self):
        if self.y >= self.ground:
            self.vy = -JUMP_SPEED
            self.hold = JUMP_HOLD

    def hurt(self, direction, knockback):
        self.vx = knockback * direction                      # decompiled Player.Hurt
        self.vy = knockback * -7.0 / 9.0
        self.hold = 0
        self.immune = IMMUNITY

    def step(self):
        grounded = self.y >= self.ground
        if self.run:
            self.vx = max(-3.0, min(3.0, self.vx + 0.08 * self.run))
        else:
            slow = 0.2 if grounded else 0.1
            self.vx = 0.0 if abs(self.vx) <= slow else self.vx - math.copysign(slow, self.vx)
        if self.hold > 0:
            self.hold -= 1
            self.vy = -JUMP_SPEED
        else:
            self.vy = min(10.0, self.vy + GRAVITY)
        self.x += self.vx
        self.y += self.vy
        if self.y >= self.ground:
            self.y, self.vy = float(self.ground), 0.0
        if self.immune > 0:
            self.immune -= 1


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


# ================================================================================================
# Beat-Boxer
# ================================================================================================
def scene_boxer(out, font):
    W, H, G = 800, 300, 262
    bg = dungeon_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.25)
    boxer = Planes("Content/Dungeon/NPCs/BeatBoxer", KB)
    glove = load("Content/Dungeon/Projectiles/SpringPunch.png")
    mic = load("Content/Dungeon/Projectiles/SpringPunch_Mic.png")
    coil = load("Content/Dungeon/Projectiles/SpringPunch_Spring.png")
    metal = load("Content/Junkyard/Items/PolishedMetal.png")
    gloves = load("Content/Dungeon/Items/SpringGloves.png")
    p = Player(500, G)
    bx, bvx = 720.0, 0.0
    knock_from, landed_at, knock_distance = None, None, 0.0
    state, timer, cooldown, reach = "walk", 0, 0, 0.0
    walked = 0.0
    punches = []                                             # [arm, age, hit]
    pops, notes = [], []
    volley = 0
    jumped = False
    face = -1
    total = int(7.8 * 60)                                   # ends after volley 2, before the next telegraph
    for tick in range(total):
        timer += 1
        if cooldown > 0:
            cooldown -= 1
        dx = p.x - bx
        direction = 1 if dx >= 0 else -1
        shoulder_y = {0: G + KB["NearShoulderY"], 1: G + KB["FarShoulderY"]}

        def shoulder(arm):
            sx = KB["NearShoulderX"] if arm == 0 else KB["FarShoulderX"]
            return bx + sx * -face, shoulder_y[arm]

        if state == "walk":
            want = direction * KB["WalkSpeed"]
            bvx = min(want, bvx + KB["WalkAccel"]) if bvx < want else max(want, bvx - KB["WalkAccel"])
            face = direction
            pc_y = p.y - PLAYER_H / 2
            if cooldown <= 0 and abs(dx) <= KB["PunchReach"] + KB["Width"] * 0.5 and abs(pc_y - shoulder(0)[1]) < KB["PunchHeight"]:
                reach = max(KB["PunchMinReach"], min(KB["PunchReach"], abs(dx) - KB["Width"] * 0.25))
                state, timer = "windup", 0
                volley += 1
        else:
            decel = KB["WalkAccel"] * 3
            bvx = 0.0 if abs(bvx) <= decel else bvx - math.copysign(decel, bvx)
            if state == "windup" and timer >= KB["WindupTicks"]:
                state, timer = "punch", 0
                punches.append([0, -1, False])
            elif state == "punch":
                if timer == KB["SecondPunchDelay"]:
                    punches.append([1, -1, False])
                if timer >= KB["PunchTicks"]:
                    state, timer, cooldown = "recover", 0, KB["PunchCooldown"]
            elif state == "recover" and timer >= KB["RecoverTicks"]:
                state, timer = "walk", 0
        bx += bvx
        walked += abs(bvx)
        # the player: stands through volley 1, walks back, then jumps too early for volley 2
        if volley >= 1 and state in ("recover", "walk") and p.y >= G and abs(p.vx) < 0.5 and not jumped and cooldown < 60:
            p.run = 1 if p.x < bx - 230 else 0
        else:
            p.run = 0
        if volley == 1 and state == "walk" and not jumped and cooldown <= 2 and abs(p.x - bx) <= KB["PunchReach"] + KB["Width"] * 0.5 + 3 * KB["WalkSpeed"]:
            p.jump()
            jumped = True
            notes.append((tick, "jumps early"))
        p.step()
        if knock_from is not None and landed_at is None and p.y >= G and p.vx == 0.0:
            knock_distance, landed_at = abs(p.x - knock_from), tick      # slid to a stop: how far the punch carried
        # the fists
        for pu in punches:
            pu[1] += 1
        punches = [pu for pu in punches if pu[1] < KB["Lifetime"]]
        fists = []
        for pu in punches:
            arm, age = pu[0], pu[1]
            sx, sy = shoulder(arm)
            fx = sx + face * (FIST_W * 0.5 + reach * extension(age))
            fists.append((arm, sx, sy, fx))
            half = KB["FistSize"] / 2
            fbox = (fx - half, sy - half, fx + half, sy + half)
            if age < KB["OutTicks"] + KB["HoldTicks"] and not pu[2] and p.immune <= 0 and overlaps(fbox, p.box()):
                pu[2] = True
                p.hurt(face, 4.5 * KB["KnockbackMultiplier"])
                knock_from, landed_at = p.x, None
                pops.append((tick, p.x - 12, p.y - 70, str(KB["PunchDamage"]), HURT))
                notes.append((tick, ("the glove" if arm == 0 else "the mic") + " lands: %d, knockback x%g" % (KB["PunchDamage"], KB["KnockbackMultiplier"])))
        if tick % TPF:
            continue
        img = bg.copy()
        if state == "windup":
            frame = KB["Windup"] + (0 if timer < KB["WindupTicks"] / 2 else 1)
        elif state == "punch":
            frame = KB["PunchNear"] if timer < KB["SecondPunchDelay"] else KB["PunchFar"]
        elif state == "recover":
            frame = KB["Idle"]
        elif abs(bvx) > 0.15:
            frame = KB["Walk"] + int(walked / KB["WalkAnimDistance"]) % KB["WalkFrames"]
        else:
            frame = KB["Idle"] + (tick // 16) % 2
        if p.immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        boxer.draw(img, frame, (bx, G), face > 0)
        for (arm, sx, sy, fx) in sorted(fists, key=lambda f: -f[0]):
            length = abs(fx - sx) - FIST_W * 0.5
            cells = int(length // SPRING_CELL)
            for k in range(cells + 1):
                w = SPRING_CELL if k < cells else int(length) - cells * SPRING_CELL
                if w <= 0:
                    continue
                x = sx + k * SPRING_CELL if face > 0 else sx - k * SPRING_CELL - w
                cell = coil.crop((0, 0, w, SPRING_H))
                img.alpha_composite(cell.transpose(Image.FLIP_LEFT_RIGHT) if face > 0 else cell, (int(x), int(sy - SPRING_H * 0.5)))
            tex = mic if arm == 1 else glove
            img.alpha_composite(tex.transpose(Image.FLIP_LEFT_RIGHT) if face > 0 else tex, (int(fx - FIST_W * 0.5), int(sy - FIST_H * 0.5)))
        d = ImageDraw.Draw(img)
        if state in ("windup", "punch"):
            sx, sy = shoulder(0)
            end = sx + face * (FIST_W + reach)
            d.line([sx, G + 14, end, G + 14], fill=EMBER + (255,), width=2)
            gif.text(img, (int(min(sx, end)), G + 20), "reach locked at %.1f tiles (3-7)" % (reach / 16.0), fill=EMBER)
        if state == "windup":
            gif.text(img, (int(bx) - 70, G - 110), "fists cocked: %d ticks" % (KB["WindupTicks"] - timer), fill=EMBER)
        numbers(gif, img, pops, tick)
        live = [s for (t0, s) in notes if 0 <= tick - t0 < 80]
        if live:
            gif.text(img, (10, 48), live[-1], fill=STEAM)
        if landed_at is not None and tick - landed_at < 90:
            gif.text(img, (10, 68), "knocked back %.1f tiles" % (knock_distance / 16.0), fill=EMBER)
        gif.text(img, (10, 8), "Beat-Boxer (Dungeon, after Skeletron): %d life, %d defense, walks %.1f px/tick like the Angry Bones" % (
            KB["Life"], KB["Defense"], KB["WalkSpeed"]))
        gif.text(img, (10, 28), "two spring punches %d ticks apart, %d each (Expert), knockback x%g; volley %d" % (
            KB["SecondPunchDelay"], KB["PunchDamage"], KB["KnockbackMultiplier"], max(1, volley)))
        gif.push(img)
    # the drops
    for _ in range(int(1.6 * 60) // TPF):
        img = bg.copy()
        d = ImageDraw.Draw(img)
        d.rectangle([150, 70, 630, 250], fill=(20, 22, 34, 235), outline=(96, 112, 164, 255))
        img.alpha_composite(metal.resize((metal.width * 3, metal.height * 3), Image.NEAREST), (180, 100))
        gif.text(img, (270, 112), "Polished Metal x2-4 (always)")
        img.alpha_composite(gloves.resize((gloves.width * 3, gloves.height * 3), Image.NEAREST), (172, 168))
        gif.text(img, (270, 170), "Spring Gloves, 1 in %d (20%%)" % KB["GlovesOdds"])
        gif.text(img, (270, 192), "+%g%% damage and knockback per steam an attack uses" % KG["PercentPerSteam"], fill=EMBER)
        gif.text(img, (270, 212), "10-steam parry or charge: +%.0f%%" % (10 * KG["PercentPerSteam"]), fill=(195, 200, 205))
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Friendobô
# ================================================================================================
def plank_room(w, h, ground):
    """The room: Weathered Plank Wall behind (its framed sheet, every cell a centre frame), a Weathered Plank floor."""
    sys.path.insert(0, HERE)
    from terrain import load_frames, render
    wall = load("Content/OldBrassTown/Walls/WeatheredPlankWallTile.png")
    img = Image.new("RGBA", (w, h), (20, 20, 26, 255))
    centre = ((1, 1), (2, 1), (3, 1))
    for ty in range(-1, ground // 16 + 1):
        for tx in range(-1, w // 16 + 1):
            fx, fy = centre[(tx * 7 + ty * 3) % 3]
            img.alpha_composite(wall.crop((fx * 36 + 8, fy * 36 + 8, fx * 36 + 24, fy * 36 + 24)), (tx * 16, ty * 16)) if 0 <= tx * 16 < w and 0 <= ty * 16 < h else None
    frames = load_frames("art/templates/terrain_exposure.json")
    cols = w // 16 + 2
    floor = render(["." * cols, "p" * cols, "p" * cols, "p" * cols], {"p": load("Content/OldBrassTown/Tiles/WeatheredPlankTile.png")}, frames)
    img.alpha_composite(floor.crop((0, 16, min(floor.width, w), min(floor.height, 16 + h - ground))), (0, ground))
    return img


def mug_sprite():
    """A stand-in for vanilla's Ale (projectile 669): a wooden mug with foam."""
    m = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    d.rectangle([2, 4, 8, 11], fill=(138, 90, 60, 255), outline=(47, 27, 20, 255))
    d.rectangle([2, 2, 8, 4], fill=(238, 241, 243, 255), outline=(138, 144, 150, 255))
    d.rectangle([9, 6, 10, 9], outline=(47, 27, 20, 255))
    return m


def scene_friendobo(out, font):
    W, H, G = 470, 210, 178
    bg = plank_room(W, H, G)
    gif = Gif(font, (W, H), scale=2.0)
    sheet = load("Content/Town/Friendobo.png")
    frames = [sheet.crop((0, k * FR_H, FR_W, (k + 1) * FR_H)) for k in range(25)]
    mug = mug_sprite()
    collector = collector_sprite()
    x, facing = 200.0, -1
    script = ([("stand", 0)] * 30 + [("blink", 0)] * 8 + [("stand", 0)] * 16 + [("walk", -1)] * 90 + [("stand", 0)] * 14
              + [("walk", 1)] * 110 + [("talk", 0)] * 70 + [("stand", 0)] * 10 + [("throw", 0)] * 70 + [("stand", 0)] * 30)
    walked = 0.0
    mugs, pops = [], []
    enemy_x = 452.0
    for tick, (act, d) in enumerate(script):
        if act == "walk":
            facing = d
            x += d * 1.0
            walked += 1.0
        throw_t = sum(1 for a, _ in script[:tick] if a == "throw")
        if act == "throw":
            facing = 1
            if throw_t == KF.get("attackDelay", 10):
                mugs.append([x + 10, G - 40, 6.0, -3.2])
        enemy_x -= 0.6 if act in ("throw", "talk") or tick > len(script) - 40 else 0.0
        for m in list(mugs):
            m[3] += 0.2
            m[0] += m[2]
            m[1] += m[3]
            if enemy_x - 12 < m[0] < enemy_x + 12 and m[1] > G - 30:
                pops.append((tick, enemy_x - 10, G - 60, "24", EMBER))
                mugs.remove(m)
            elif m[1] > G:
                mugs.remove(m)
        if tick % TPF:
            continue
        if act == "walk":
            k = 2 + int(walked / 6.0) % 14
        elif act == "blink":
            k = 20
        elif act == "talk":
            k = 19 if (tick // 10) % 2 == 0 else 0
        elif act == "throw":
            k = 21 + min(3, throw_t // 6) if throw_t < 24 else 0
        else:
            k = 0
        img = bg.copy()
        if any(a == "throw" for a, _ in script[:tick + 1]) or tick > len(script) - 140:
            img.alpha_composite(collector.transpose(Image.FLIP_LEFT_RIGHT), (int(enemy_x - collector.width / 2), G - collector.height))
        fr = frames[k] if facing < 0 else frames[k].transpose(Image.FLIP_LEFT_RIGHT)
        img.alpha_composite(fr, (int(x - FR_W / 2), G - 52))
        for m in mugs:
            img.alpha_composite(mug, (int(m[0] - 6), int(m[1] - 6)))
        numbers(gif, img, pops, tick)
        if act == "talk":
            gif.text(img, (int(x) - 110, G - 104), '"Welcome, welcome! Mind the floor,', fill=STEAM)
            gif.text(img, (int(x) - 110, G - 88), 'I polished it this century."', fill=STEAM)
        label = {"stand": "standing (0)", "blink": "blinking (20)", "walk": "walking (2-15)", "talk": "talking (19)", "throw": "throwing a mug (21-24)"}[act]
        gif.text(img, (8, 6), "Friendobô: " + label)
        gif.text(img, (8, 24), "throws the Tavernkeep's Ale: 24 damage, knockback 9", fill=(195, 200, 205))
        gif.text(img, (8, 42), "shop: Rusted Cogs and Scrap %dc, beaten bosses' summons" % KF["ScrapPrice"], fill=(195, 200, 205))
        gif.push(img)
    gif.save(out)


# ================================================================================================
# Sprites
# ================================================================================================
def sprites_png(out, font):
    gif = Gif(font, (10, 10))
    boxer = Planes("Content/Dungeon/NPCs/BeatBoxer", KB)
    glove = load("Content/Dungeon/Projectiles/SpringPunch.png")
    mic = load("Content/Dungeon/Projectiles/SpringPunch_Mic.png")
    coil = load("Content/Dungeon/Projectiles/SpringPunch_Spring.png")
    gloves = load("Content/Dungeon/Items/SpringGloves.png")
    sheet = load("Content/Town/Friendobo.png")
    head = load("Content/Town/Friendobo_Head.png")
    names = ["Walk0", "Walk1", "Walk2", "Walk3", "Walk4", "Walk5", "Idle0", "Idle1", "Windup0", "Windup1", "PunchNear", "PunchFar"]
    W, H = 2040, 900
    img = Image.new("RGBA", (W, H), (36, 40, 48, 255))
    ImageDraw.Draw(img).rectangle([0, H // 2, W, H], fill=(214, 190, 150, 255))
    for half in (0, 1):
        y0 = half * H // 2
        gif.text(img, (12, y0 + 6), "Beat-Boxer (Dungeon), all frames, 2x of the game sprite" + ("" if half == 0 else ", on a light background"),
                 fill=(238, 241, 243) if half == 0 else (21, 22, 28))
        for k, n in enumerate(names):
            tile = Image.new("RGBA", (KB["CellWidth"], KB["CellHeight"]))
            boxer.draw(tile, k, (KB["OriginX"], KB["OriginY"]), False)
            img.alpha_composite(tile.resize((tile.width * 2, tile.height * 2), Image.NEAREST), (12 + k * 164, y0 + 30))
            gif.text(img, (12 + k * 164, y0 + 162), n, fill=(238, 241, 243) if half == 0 else (21, 22, 28))
        x = 12
        for im, n in ((glove, "SpringPunch (glove)"), (mic, "SpringPunch_Mic"), (coil, "SpringPunch_Spring"), (gloves, "Spring Gloves")):
            img.alpha_composite(im.resize((im.width * 4, im.height * 4), Image.NEAREST), (x, y0 + 200))
            gif.text(img, (x, y0 + 320), n, fill=(238, 241, 243) if half == 0 else (21, 22, 28))
            x += 180
        gif.text(img, (760, y0 + 200), "Last Ghedalari (town NPC; the Friendobô until 2026-11-24), 25 frames, 2x", fill=(238, 241, 243) if half == 0 else (21, 22, 28))
        for k in range(25):
            fr = sheet.crop((0, k * FR_H, FR_W, (k + 1) * FR_H))
            img.alpha_composite(fr.resize((FR_W * 2, FR_H * 2), Image.NEAREST), (760 + (k % 13) * 86, y0 + 222 + (k // 13) * 112))
        img.alpha_composite(head.resize((head.width * 3, head.height * 3), Image.NEAREST), (W - 80, y0 + 30))
    img.convert("RGB").save(out)
    print(out, img.size)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a.add_argument("--date", default="2026-11-03", help="the date in the file names (re-rendering a redrawn model: D5 rule 6)")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("sprites", lambda: sprites_png(os.path.join(args.out, args.date + "_dungeon-town-sprites.png"), args.font)),
            ("boxer", lambda: scene_boxer(os.path.join(args.out, args.date + "_dungeon-beat-boxer.gif"), args.font)),
            ("friendobo", lambda: scene_friendobo(os.path.join(args.out, args.date + "_town-friendobo.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
