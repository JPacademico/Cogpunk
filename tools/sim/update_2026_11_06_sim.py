"""D5 proofs for the request of 2026-11-06, built from the real sprite sheets and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_06_sim.py --out docs/media [--only sheriff]

Writes:
    2026-11-06_oldbrasstown-sheriff-stars.gif   the Sheriff's reworked stars: one thrown every 2 s (a 30-tick flash and
                                                chime each) with 36 tiles of reach; the first misses (the player jumps it)
                                                and bites into the street, the second hits and flies home, the third misses
                                                into the wall; then the stuck ones rattle for 30 ticks with a dotted ember
                                                line marking their way home and tear back through the player.
    2026-11-06_boss-tartyrant-armor-claw.gif    the Tyrant set's restored tar claw: every 4 s the ground boils under the
                                                closest Living Tar and the claw bursts up, snaps shut and sinks (112: 100
                                                magic x the skull's +12%), worn by a player in the full set.

Leaves out: lighting, the planes' parallax, vanilla's player physics (approximated as in update_2026_11_03b_sim), defense,
netcode (the sim is the server: it decides the throws, the touches and the recall). Numbers are Expert's.
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, player_sprite, TPF  # noqa: E402
import armor_preview as ap  # noqa: E402
from update_2026_11_03_sim import Planes  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, PLAYER_W, PLAYER_H  # noqa: E402
from update_2026_11_04_sim import town_backdrop, aim_index, fire, heading_frame, pops_and_notes, KD, HURT, STEAM  # noqa: E402
from smoke import Smoke  # noqa: E402

TOWN = "Content/OldBrassTown/"
KH = consts(TOWN + "NPCs/Sheriff.cs", TOWN + "NPCs/SheriffRigData.cs", TOWN + "Projectiles/SheriffStar.cs")
ARMOR = "Content/Bosses/TarTyrant/Armor/"
KA = consts(ARMOR + "TyrantClaw.cs", ARMOR + "TyrantClawRigData.cs", ARMOR + "TyrantArmorPlayer.cs", ARMOR + "TyrantSkull.cs")
KT = consts("Content/Junkyard/NPCs/LivingTar.cs")
IMMUNITY = 40
DOT_DIM, DOT_LIT = (163, 48, 26, 255), (255, 199, 90, 255)
HOME, OUT, STUCK, RECALL, BACK = range(5)


# ================================================================================================
# The Sheriff's stars (SheriffStar.AI, step for step)
# ================================================================================================
def star_home(hx, ground, slot, tick):
    return hx + (slot - 1) * 24.0, ground + KH["HatTopY"] - 16.0 - (8.0 if slot == 1 else 0.0) - ((tick // 20 + slot) % 2) * 2.0


def launch_tick(slot):
    return KH["StarTelegraph"] + slot * KH["StarShotInterval"]


class Star:
    def __init__(self, slot, x, y):
        self.slot, self.x, self.y = slot, x, y
        self.vx = self.vy = 0.0
        self.mode, self.flight, self.held, self.frame = HOME, 0, 0, 0

    def box(self):
        return (self.x - 10, self.y - 10, self.x + 10, self.y + 10)

    def set_mode(self, mode):
        if self.mode != mode:
            self.mode, self.flight = mode, 0
            if mode == STUCK:
                self.held = self.frame % KH["StarSpin"]

    def stop(self, fvx, fvy):
        d = math.hypot(fvx, fvy)
        if d > 0:
            self.x += fvx / d * KH["EmbedDepth"]
            self.y += fvy / d * KH["EmbedDepth"]
        self.vx = self.vy = 0.0
        self.set_mode(STUCK)

    def move(self, solid):
        """Vanilla's tile collision, approximated: sub-steps of 1 px until the 20x20 box would enter a solid cell."""
        steps = int(math.ceil(max(abs(self.vx), abs(self.vy))))
        if steps <= 0:
            return
        sx, sy = self.vx / steps, self.vy / steps
        for _ in range(steps):
            nx, ny = self.x + sx, self.y + sy
            if solid((nx - 10, ny - 10, nx + 10, ny + 10)):
                self.stop(self.vx, self.vy)
                return
            self.x, self.y = nx, ny

    def update(self, clock, home, armed, target, player_box, solid):
        events = []
        launch = launch_tick(self.slot)
        if self.mode == HOME:
            self.x, self.y = home
            if clock == launch and armed:
                ax, ay = target[0] - self.x, target[1] - self.y
                d = math.hypot(ax, ay) or 1.0
                self.vx, self.vy = ax / d * KH["OutSpeed"], ay / d * KH["OutSpeed"]
                self.set_mode(OUT)
                events.append("throw")
        elif self.mode == OUT:
            self.flight += 1
            if self.flight >= KH["OutTicks"]:
                self.stop(0.0, 0.0)
                events.append("hang")
            elif overlaps(self.box(), player_box):
                self.set_mode(BACK)
                events.append("touch")
        elif self.mode == STUCK:
            if KH["RecallTick"] <= clock < KH["StarCycle"]:
                self.set_mode(RECALL)
                events.append("recall")
        if self.mode in (RECALL, BACK):
            ax, ay = home[0] - self.x, home[1] - self.y
            d = math.hypot(ax, ay)
            if d < KH["HomeSnap"]:
                self.set_mode(HOME)
                self.x, self.y = home
            else:
                speed = KH["RecallSpeed"] if self.mode == RECALL else KH["BackSpeed"]
                self.vx, self.vy = ax / d * min(speed, d), ay / d * min(speed, d)
        if self.mode == OUT:
            before = self.mode
            self.move(solid)
            if self.mode != before:
                events.append("stick")
        elif self.mode in (RECALL, BACK):
            self.x += self.vx
            self.y += self.vy
        return events

    def hurts(self):
        return self.mode in (OUT, RECALL)

    def sprite_frame(self, clock, tick, armed):
        launch = launch_tick(self.slot)
        throw_tg = self.mode == HOME and armed and launch - KH["StarTelegraph"] <= clock < launch
        recall_tg = self.mode == STUCK and KH["RecallTelegraphTick"] <= clock < KH["RecallTick"]
        spin = KH["FastSpinTicks"] if (self.mode != HOME or throw_tg) else KH["SpinTicks"]
        turn = (tick // spin + self.slot) % KH["StarSpin"]
        if self.mode == STUCK:
            flash = recall_tg and (tick // KH["RattleTicks"]) % 2 == 0
            self.frame = self.held + (KH["StarSpin"] if flash else 0)
        else:
            self.frame = turn + (KH["StarSpin"] if throw_tg or self.mode == RECALL else 0)
        return self.frame, recall_tg


def way_home(d, star, home, tick):
    """SheriffStar.DrawWayHome: 4x4 px embers every 16 px on the 2 px grid, the lit one marching homewards."""
    ax, ay = home[0] - star.x, home[1] - star.y
    length = math.hypot(ax, ay)
    if length < KH["DotSpacing"]:
        return
    ux, uy = ax / length * KH["DotSpacing"], ay / length * KH["DotSpacing"]
    march = (tick // 3) % 3
    for k in range(1, min(KH["MaxDots"], int(length // KH["DotSpacing"])) + 1):
        px, py = int(star.x + ux * k), int(star.y + uy * k)
        px -= px % 2
        py -= py % 2
        col = DOT_LIT if (k + 3 - march) % 3 == 0 else DOT_DIM
        d.rectangle([px - 2, py - 2, px + 1, py + 1], fill=col)


def scene_sheriff(out, font):
    W, H, G = 1000, 330, 290
    WALL = 190                                               # the clapboard house's sandstone wall, left of this x
    bg = town_backdrop(W, H, G, wall_x=WALL)
    gif = Gif(font, (W, H), scale=1.0)
    sheriff = Planes(TOWN + "NPCs/Sheriff", KH)
    sheet = load(TOWN + "Projectiles/SheriffStar.png")
    glow = load(TOWN + "Projectiles/SheriffStar_Glow.png")
    bullet = load(TOWN + "Projectiles/RustyBullet.png")
    smoke = Smoke((138, 144, 150))

    def solid(box):
        return box[3] > G or box[0] < WALL

    p = Player(400, G)
    hx, hvx, face = 880.0, 0.0, -1
    state, timer, clock = "walk", 0, 0
    walked = 0.0
    stars = []
    for s in range(KH["StarCount"]):
        x, y = star_home(hx, G, s, 0)
        stars.append(Star(s, x, y))
    bullets, pops, notes = [], [], []
    spreads = (0.0, 0.02, -0.02, 0.03, -0.01, 0.01)
    total = 9 * 60 + 30
    for tick in range(total):
        timer += 1
        clock = (clock + 1) % KH["StarCycle"]
        target = (p.x, p.y - PLAYER_H / 2)
        dx = p.x - hx
        direction = 1 if dx >= 0 else -1
        armed = math.hypot(target[0] - hx, target[1] - (G - KH["Height"] / 2)) < KH["StarEngageRange"]
        # the gun (Sheriff.UpdateState), unchanged
        if state == "walk":
            want = direction * KH["WalkSpeed"] if abs(dx) > KH["KeepRange"] else 0.0
            hvx = min(want, hvx + KH["WalkAccel"]) if hvx < want else max(want, hvx - KH["WalkAccel"])
            face = direction
            if timer > 150 and abs(dx) < KH["SightRange"]:
                state, timer = "aim", 0
        elif state == "aim":
            hvx *= 0.7
            if timer >= KH["AimTicks"]:
                state, timer = "shoot", 0
        elif state == "shoot":
            hvx *= 0.7
            if (timer - 1) % KH["ShotInterval"] == 0 and timer <= KH["ShootTicks"]:
                bullets.append(fire(KH, hx, G, face, target, spreads[((timer - 1) // KH["ShotInterval"]) % 6]))
            if timer >= KH["ShootTicks"] + 6:
                state, timer = "reload", 0
        elif state == "reload":
            hvx *= 0.7
            if timer >= KH["ReloadTicks"]:
                state, timer = "walk", -400
        hx += hvx
        walked += abs(hvx)
        # the stars
        for st in stars:
            home = star_home(hx, G, st.slot, tick)
            for e in st.update(clock, home, armed, target, p.box(), solid):
                if e == "throw":
                    notes.append((tick, "star %d of 3 thrown at the player's spot (36 tiles of reach)" % (st.slot + 1)))
                elif e == "stick":
                    notes.append((tick, "a miss bites into the terrain and stays there"))
                elif e == "touch":
                    notes.append((tick, "a hit: the star flies home, harmless"))
                elif e == "recall" and st.slot == 0:
                    notes.append((tick, "the recall: the stuck stars tear loose and fly home through everything"))
            if st.hurts() and p.immune <= 0 and overlaps(st.box(), p.box()):
                p.immune = IMMUNITY
                pops.append((tick, p.x - 12, p.y - 70, str(KH["StarDamage"]), HURT))
        if clock == KH["RecallTelegraphTick"]:
            notes.append((tick, "after the third throw: the stuck stars rattle, their way home marked (30 ticks)"))
        # the player: jumps the first throw (it bites into the street behind him), takes the second, jumps before the
        # third so it is aimed high and sails over him into the wall, then stands on the recall's line and is cut by it
        p.run = 0
        if tick == launch_tick(0) + 14:
            p.jump()
        if tick == launch_tick(2) - 8:
            p.jump()
        if tick == launch_tick(0) + KH["StarCycle"] + 4:
            p.jump()
        p.step()
        p.x = max(WALL + 24, min(W - 24, p.x))
        for b in list(bullets):
            smoke.add((b[0], b[1]), (b[0] + b[2], b[1] + b[3]), tick)
            b[0] += b[2]
            b[1] += b[3]
            if not (WALL < b[0] < W and 0 < b[1] < G):
                bullets.remove(b)
                continue
            if p.immune <= 0 and overlaps((b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4), p.box()):
                p.immune = IMMUNITY
                pops.append((tick, p.x - 12, p.y - 70, str(KH["BulletDamage"]), HURT))
                bullets.remove(b)
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        if state == "aim":
            frame = KH["Aim"] + aim_index(KH, hx, G, face, target)
        elif state == "shoot":
            since = (timer - 1) % KH["ShotInterval"]
            frame = (KH["Shoot"] if since < KH["MuzzleFlashTicks"] and timer <= KH["ShootTicks"] else KH["Aim"]) + aim_index(KH, hx, G, face, target)
        elif state == "reload":
            frame = KH["Reload"] + (timer // 10) % KH["ReloadFrames"]
        elif abs(hvx) > 0.15:
            frame = KH["Walk"] + int(walked / KH["WalkStep"]) % KH["WalkFrames"]
        else:
            frame = KH["Idle"] + (timer // 20) % KH["IdleFrames"]
        if p.immune <= 0 or (tick // 3) % 2 == 0:
            img.alpha_composite(player_sprite(flip=p.vx < -0.1), (int(p.x - 20), int(p.y - 56)))
        sheriff.draw(img, frame, (hx, G), face > 0)
        cell = KH["StarCell"]
        for st in stars:
            f, recall_tg = st.sprite_frame(clock, tick, armed)
            sx = int(st.x - cell / 2)
            if recall_tg:
                way_home(d, st, star_home(hx, G, st.slot, tick), tick)
                sx += (tick // KH["RattleTicks"]) % 2 * 2
            src = (0, f * (cell + 2), cell, f * (cell + 2) + cell)
            img.alpha_composite(sheet.crop(src), (sx, int(st.y - cell / 2)))
            img.alpha_composite(glow.crop(src), (sx, int(st.y - cell / 2)))
        smoke.draw(img, tick)
        for b in bullets:
            f = heading_frame(b[2], b[3], KD["BulletHeadings"])
            img.alpha_composite(bullet.crop((0, f * 16, 14, f * 16 + 14)), (int(b[0] - 7), int(b[1] - 7)))
        gif.text(img, (10, 8), "Sheriff's stars, reworked: one every %d s, %d tiles of reach, %d damage each (Expert)" % (
            KH["StarShotInterval"] // 60, KH["OutSpeed"] * KH["OutTicks"] // 16, KH["StarDamage"]))
        gif.text(img, (10, 28), "misses stick in the terrain; after the third throw they fly home through the players (clock %d / %d)" % (
            clock, KH["StarCycle"]))
        pops_and_notes(gif, img, pops, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Tyrant set's tar claw (TyrantArmorPlayer + TyrantClaw, step for step)
# ================================================================================================
def tyrant_player(flip=False):
    """A player in the full Tyrant set (armor_preview's composer: skin under the bare parts, the cape behind)."""
    head = ap.load_frames(ARMOR + "TyrantSkull_Head.png", 1)[0]
    body = ap.load_frames(ARMOR + "TyrantCape_Body.png", 1)[0]
    legs = ap.load_frames(ARMOR + "TyrantSandals_Legs.png", 1)[0]
    back = ap.load_frames(ARMOR + "TyrantCape_Back.png", 1)[0]
    s = ap.compose(head, body, legs, 0, [0] * 20, back=back, skin=True)
    return s.transpose(Image.FLIP_LEFT_RIGHT) if flip else s


def claw_frame(age):
    if age < KA["WarnTicks"]:
        return KA["Warn0"] + min(KA["WarnFrames"] - 1, age // KA["WarnFrameTicks"])
    e = age - KA["WarnTicks"]
    if e < KA["RiseTicks"]:
        return KA["Rise0"] + min(KA["RiseFrames"] - 1, e // KA["RiseFrameTicks"])
    e -= KA["RiseTicks"]
    if e < KA["GrabTicks"]:
        return KA["Grab0"] + min(KA["GrabFrames"] - 1, e // KA["GrabFrameTicks"])
    e -= KA["GrabTicks"]
    return KA["Sink0"] + min(KA["SinkFrames"] - 1, e // KA["SinkFrameTicks"])


def claw_reach(age):
    e = age - KA["WarnTicks"]
    if e < 0:
        return 0.0
    if e < KA["RiseTicks"]:
        return (0.25, 0.62, 1.0, 1.0)[min(3, e // KA["RiseFrameTicks"])]
    return 1.0 if e < KA["RiseTicks"] + KA["GrabTicks"] else 0.0


def scene_claw(out, font):
    W, H, G = 760, 300, 250
    bg = backdrop(W, H, G, sky=((120, 150, 190), (90, 104, 140)), dirt=(91, 54, 38))
    gif = Gif(font, (W, H), scale=1.25)
    sheet = load(ARMOR + "TyrantClaw.png")
    tar = load("Content/Junkyard/NPCs/LivingTar.png")
    me = tyrant_player()
    rng = random.Random(6)
    px = 150.0
    damage = int(KA["ClawDamage"] * (1 + KA["Damage"] / 100.0))
    enemies = [{"x": x, "life": KT["Life"], "hop": rng.randrange(40)} for x in (420.0, 560.0, 690.0)]
    claws, pops, notes, splashes = [], [], [], []
    timer = KA["ClawInterval"] - 60                       # the charge is a second from full as the scene opens
    total = int(9.5 * 60)
    for tick in range(total):
        live = [e for e in enemies if e["life"] > 0]
        for e in live:
            e["hop"] += 1
            if e["x"] > px + 60:
                e["x"] -= 0.35
        # TyrantArmorPlayer.PostUpdate: charge, then the closest enemy in range with ground under it
        if timer < KA["ClawInterval"]:
            timer += 1
        elif live:
            target = min(live, key=lambda e: abs(e["x"] - px))
            if abs(target["x"] - px) < KA["ClawRange"]:
                claws.append({"x": target["x"], "age": 0, "hit": set()})
                notes.append((tick, "4 s charged: the claw erupts under the closest enemy"))
                timer = 0
        for c in claws:
            age = c["age"]
            if age < KA["WarnTicks"] and age % 2 == 0:
                for _ in range(2):
                    splashes.append([c["x"] + rng.uniform(-KA["HitboxWidth"] / 2, KA["HitboxWidth"] / 2), G - 2,
                                     rng.uniform(-0.8, 0.8), -rng.uniform(1.5, 3.0), 18])
            if age == KA["WarnTicks"]:
                for _ in range(10):
                    splashes.append([c["x"] + rng.uniform(-KA["HitboxWidth"] / 2, KA["HitboxWidth"] / 2), G - 4,
                                     rng.uniform(-2.5, 2.5), -rng.uniform(2.5, 5.0), 24])
            if KA["HurtStart"] <= age < KA["HurtEnd"]:
                h = int(KA["HitboxHeight"] * claw_reach(age))
                box = (c["x"] - KA["HitboxWidth"] / 2, G - h, c["x"] + KA["HitboxWidth"] / 2, G)
                for i, e in enumerate(enemies):
                    if e["life"] > 0 and i not in c["hit"] and overlaps(box, (e["x"] - 12, G - 18, e["x"] + 12, G)):
                        c["hit"].add(i)
                        e["life"] -= damage
                        pops.append((tick, e["x"] - 14, G - 60, str(damage), (198, 189, 255)))
            c["age"] += 1
        claws = [c for c in claws if c["age"] < KA["Lifetime"]]
        for sp in splashes:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[3] += 0.2
            sp[4] -= 1
        splashes = [sp for sp in splashes if sp[4] > 0]
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        img.alpha_composite(me, (int(px - 20), G - 56))
        for e in enemies:
            if e["life"] > 0:
                f = (e["hop"] // 12) % 2
                img.alpha_composite(tar.crop((0, f * 24, 32, f * 24 + 24)), (int(e["x"] - 16), G - 22))
        for c in claws:
            f = claw_frame(c["age"])
            cell = sheet.crop((0, f * (KA["Height"] + 2), KA["Width"], f * (KA["Height"] + 2) + KA["Height"]))
            img.alpha_composite(cell, (int(c["x"] - KA["Width"] / 2), G + 2 - KA["Height"]))
        for sp in splashes:
            x, y = int(sp[0]) // 2 * 2, int(sp[1]) // 2 * 2
            d.rectangle([x, y, x + 1, y + 1], fill=(47, 27, 20, 255))
        bar = int(120 * min(1.0, timer / KA["ClawInterval"]))
        d.rectangle([px - 60, G - 78, px + 60, G - 74], fill=(21, 22, 28, 255))
        d.rectangle([px - 60, G - 78, px - 60 + bar, G - 74], fill=(91, 54, 38, 255) if bar < 120 else (138, 90, 60, 255))
        gif.text(img, (10, 8), "Tyrant set bonus, restored: the tar claw every %d s, %d magic (%d with the skull's +%d%%), 5 tiles wide" % (
            KA["ClawInterval"] // 60, KA["ClawDamage"], damage, KA["Damage"]))
        gif.text(img, (10, 28), "set: +%d%% summon and magic crit; skull: +%d%% summon and magic damage, +1 minion" % (KA["SetCrit"], KA["Damage"]))
        gif.text(img, (10, 48), "cape: +12% whip speed, -10% mana cost; sandals: immunity to fall damage")
        pops_and_notes(gif, img, pops, notes, tick, y=68)
        gif.push(img)
    gif.save(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = [("sheriff", lambda: scene_sheriff(os.path.join(args.out, "2026-11-06_oldbrasstown-sheriff-stars.gif"), args.font)),
            ("claw", lambda: scene_claw(os.path.join(args.out, "2026-11-06_boss-tartyrant-armor-claw.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
