"""D5 proofs for the request of 2026-11-10, built from the real sprites and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s). (The ghost train's new colours are re-rendered by update_2026_11_09_sim.py --only
train, which now writes 2026-11-10_weapon-cursed-train-whistle.gif.)

    python -P tools/sim/update_2026_11_10_sim.py --out docs/media [--only jade,jumps,stones,reading,lantern,loop]

(The Firesaw's, the Jade Golem's and the items sheet's scenes moved to update_2026_11_10b_sim.py with the second request of
the day: the Firesaw's phantom slash, the Golem's open palms and smooth aim, the Jade Staff's centred gem. The helpers here
are still imported by it.)

Writes:
    2026-11-10_gems-jade-staff-homing.gif      the redrawn Jade Staff held and turned to the cursor like vanilla's gem staffs;
                                               three bolts turn a Jade Golem to jade (an Imperial Defender until that enemy
                                               was removed, 2026-11-11); bolts fired over it curve down
                                               into it (they home in on enemies turned to jade); then a boss stand-in already
                                               turned to jade twice: six hits turn it a third time, and after that it is
                                               immune for the rest of the fight.
    2026-11-10_enemies-mirror-jump.gif         the Beat-Boxer walks at the player and jumps when the player jumps
                                               (GridWalkerNPC.MirrorJump: 8 px/tick, ~6.7 tiles); a double jump in the air isn't
                                               mirrored (it isn't on the ground). (The Imperial Defender jumped beside it until
                                               it was removed, 2026-11-11.)
    2026-11-10_secrets-fundamental-stones.png  the five Fundamental Stones over dark and light (their sigils), Westworld's at
                                               the west end of its street (old_brass_town_sim's replay of the pass), the tar
                                               pit's on the pool's floor under the tar, and the runes.
    2026-11-10_secrets-fundamental-stone-reading.gif   a player walks to Westworld's stone and right-clicks it: its line of
                                               runes lights up glyph by glyph over it; walking away fades it.
    2026-11-10_boss-cursed-conductor-lantern-ghost.gif  two lantern attacks whose three bolts all land: only the first of
                                               each opens a rift, so one ghost a lantern attack.
    2026-11-10_boss-cursed-conductor-loop-ghosts.gif    half scale: the loop's three laps; two ghosts rise on the first lap
                                               only (LoopGhostLaps), none after.

Leaves out: lighting (but for the stone's glow), the planes' parallax, vanilla's exact player physics (approximated as in
update_2026_11_03b_sim), the arm's composite drawing (the hand is placed as Player.GetFrontHandPosition is, without its
3 px turn), the reading panel's vanilla frame (drawn as a plain dark panel), defense, netcode (the sim is the server and the
owner). Vanilla's graveyard Ghost is drawn as the older sims' stand-in. Numbers are Expert's.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, player_sprite, TPF  # noqa: E402
from update_2026_11_04_sim import town_backdrop, STEAM  # noqa: E402
from update_2026_11_06b_sim import Planes, coghaven_backdrop, numbers, note, Sparks, seg_box_dist  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, dungeon_backdrop, PLAYER_W, PLAYER_H  # noqa: E402

MECH = "Content/Mechanist/Weapons/"
GEMS = "Content/Gems/"
COG = "Content/Coghaven/"
SEC = "Content/Secrets/"
WEP = "Content/Bosses/CursedConductor/Weapons/"
KF = consts(MECH + "Firesaw.cs")
KJ = consts(GEMS + "Items/JadeStaff.cs", GEMS + "Projectiles/JadeBolt.cs", GEMS + "JadeCurseNPC.cs")
KG = consts(COG + "NPCs/JadeGolem.cs", COG + "NPCs/JadeGolemRigData.cs", COG + "Projectiles/JadeRay.cs")
KB = consts("Content/Dungeon/NPCs/BeatBoxer.cs", "Content/Dungeon/NPCs/BeatBoxerRigData.cs")
KW = consts("Core/Templates/GridWalkerNPC.cs")
KS = consts(SEC + "FundamentalStoneTile.cs", SEC + "FundamentalStoneReading.cs")
EMBER, JADE, HIT, HURT, GLOW = (236, 113, 40), (96, 214, 150), (255, 199, 90), (255, 90, 70), (144, 168, 208)
INSCRIPTIONS = [[int(v) for v in row.split(",")] for row in
                __import__("re").findall(r"new byte\[\] \{([^}]*)\}", open(SEC + "FundamentalStones.cs", encoding="utf-8").read())]


def lerp(a, b, t):
    return a + (b - a) * t


def phase(t, a, b):
    return 0.0 if b <= a else max(0.0, min(1.0, (t - a) / (b - a)))


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t):
    return 4.0 * t ** 3 if t < 0.5 else 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def faded(im, alpha):
    if alpha >= 1.0:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, alpha))))
    return out


def tinted(im, col):
    """Vanilla's draw colour on a sprite: each channel multiplied (DrawEffects' r, g, b)."""
    r, g, b, a = im.split()
    return Image.merge("RGBA", (r.point(lambda v: v * col[0] // 255), g.point(lambda v: v * col[1] // 255), b.point(lambda v: v * col[2] // 255), a))


# ================================================================================================
# The Firesaw
# ================================================================================================
def swing_angle(done, up):
    """Firesaw.SwingAngle step for step."""
    frm, to = (KF["Low"], KF["High"]) if up else (KF["High"], KF["Low"])
    sign = -1.0 if up else 1.0
    start, over = frm - sign * KF["PullBack"], to + sign * KF["Overshoot"]
    if done < KF["WindEnd"]:
        return lerp(frm, start, ease_out(phase(done, 0.0, KF["WindEnd"])))
    if done < KF["SlashEnd"]:
        return lerp(start, to, ease_in_out(phase(done, KF["WindEnd"], KF["SlashEnd"])))
    if done < KF["OverEnd"]:
        return lerp(to, over, ease_out(phase(done, KF["SlashEnd"], KF["OverEnd"])))
    return lerp(over, to, ease_in_out(phase(done, KF["OverEnd"], KF["SettleEnd"])))


def posed(sheet, frame, size, grip, angle):
    """A frame of a swung sheet turned about its grip as vanilla draws a held swing (the sprite points to its top right, so
    it turns by the blade's angle + 45 degrees), point-sampled like the game; returns it and the grip's offset in it."""
    cell = sheet.crop((0, frame * (size + 2), size, frame * (size + 2) + size))
    r = int(math.hypot(size, size)) + 4
    pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    pad.alpha_composite(cell, (r - grip[0], r - grip[1]))
    return pad.rotate(-math.degrees(angle + math.pi / 4), resample=Image.NEAREST), r


def hand_at(centre, angle):
    """Player.GetFrontHandPosition (Full, facing right, upright): the shoulder 4 px back and 2 up, the arm 10 px long."""
    return (centre[0] - 4 + 10 * math.cos(angle), centre[1] - 2 + 10 * math.sin(angle))


def blade(centre, angle, fire):
    """The hit capsule (Firesaw.BladeHits): from BladeStart to the reach along the blade, FireBelow under it on fire."""
    h = hand_at(centre, angle)
    d = (math.cos(angle), math.sin(angle))
    n = (-d[1], d[0])
    reach, below, radius = (KF["FireReach"], KF["FireBelow"], KF["FireRadius"]) if fire else (KF["Reach"], 0.0, KF["BladeRadius"])
    a = (h[0] + d[0] * KF["BladeStart"], h[1] + d[1] * KF["BladeStart"])
    b = (h[0] + d[0] * reach + n[0] * below, h[1] + d[1] * reach + n[1] * below)
    return a, b, radius


# ================================================================================================
# The Jade Staff: aimed like a gem staff, homing on the petrified, the boss cap
# ================================================================================================
class Target:
    """JadeCurseNPC.Apply on the server: stacks, the turn to jade, the ward, and a boss's cap."""

    def __init__(self, x, boss, petrified_before=0):
        self.x, self.boss = x, boss
        self.need = int(KJ["BossStacks"] if boss else KJ["Stacks"])
        self.stacks = self.curse = self.stone = self.ward = 0
        self.petrifications = petrified_before
        self.skip, self.counter = 0.0, 0.0

    def hit(self):
        if self.ward > 0 or self.stone > 0:
            return "immune" if self.boss and self.petrifications >= KJ["BossPetrifyLimit"] else ("frozen" if self.stone else "warded")
        if self.boss and self.petrifications >= KJ["BossPetrifyLimit"]:
            return "immune"
        self.stacks += 1
        if self.stacks >= self.need:
            self.stacks, self.curse = 0, 0
            self.petrifications += 1
            self.stone, self.ward = int(KJ["PetrifyTicks"]), int(KJ["WardTicks"])
            return "JADE! %d/%d" % (self.petrifications, KJ["BossPetrifyLimit"]) if self.boss else "JADE!"
        self.curse = int(KJ["CurseTicks"])
        return "x%d" % self.stacks

    def tick(self):
        for f in ("curse", "stone", "ward"):
            setattr(self, f, max(0, getattr(self, f) - 1))
        if self.curse == 0:
            self.stacks = 0
        if self.stone > 0:
            return False
        if self.stacks == 0:
            self.skip = 0.0
            return True
        self.skip += KJ["SlowPerStack"] * self.stacks
        if self.skip >= 1.0:
            self.skip -= 1.0
            return False
        return True


class JadeBoltSim:
    """JadeBolt.AI step for step: the centreline point, the homing turn, the weave."""

    def __init__(self, pos, course):
        self.pos, self.course, self.age, self.alive, self.hit = pos, course, 0.0, True, set()

    @staticmethod
    def side(c):
        n = math.hypot(c[0], c[1]) or 1.0
        return (-c[1] / n, c[0] / n)

    def offset(self, age):
        return KJ["WaveAmplitude"] * math.sin(2 * math.pi * age / KJ["WavePeriod"])

    def update(self, petrified):
        s = self.side(self.course)
        o = self.offset(self.age)
        line = (self.pos[0] - s[0] * o, self.pos[1] - s[1] * o)
        best, bd = None, KJ["HomingRange"] ** 2
        for (tid, cx, cy) in petrified:
            dd = (cx - line[0]) ** 2 + (cy - line[1]) ** 2
            if tid not in self.hit and dd < bd:
                best, bd = (cx, cy), dd
        self.homing = best is not None
        if best:
            speed = math.hypot(*self.course)
            now = math.atan2(self.course[1], self.course[0])
            want = math.atan2(best[1] - line[1], best[0] - line[0])
            turn = max(-KJ["HomingTurn"], min(KJ["HomingTurn"], (want - now + math.pi) % (2 * math.pi) - math.pi))
            self.course = (math.cos(now + turn) * speed, math.sin(now + turn) * speed)
        s = self.side(self.course)
        o = self.offset(self.age + 1)
        self.pos = (line[0] + self.course[0] + s[0] * o, line[1] + self.course[1] + s[1] * o)
        self.age += 1


def scene_jade(out, font):
    W, H, G = 800, 330, 300
    BOSS_FLOOR = G - 150                                       # the boss stand-in stands on a ledge: its bolts fly over the Golem
    FOE_HALF, FOE_H = 28, 104                                  # JadeGolem.SetDefaults: 56 x 104
    BOSS_IN = 270                                              # it appears for its part only
    bg = coghaven_backdrop(W, H, G, ledges=[(640, 768, BOSS_FLOOR)])
    gif = Gif(font, (W, H), scale=1.15)
    golem = Planes(COG + "NPCs/JadeGolem", KG)
    bolt_img = load(GEMS + "Projectiles/JadeBolt.png")
    staff = load(GEMS + "Items/JadeStaff.png")
    px = 90.0
    centre = (px, G - 21.0)
    foe = Target(520.0, False)
    boss = Target(705.0, True, petrified_before=2)
    use = int(KJ["UseTime"])
    casts = [(10 + k * use, "foe") for k in range(3)] + [(150 + k * use, "over") for k in range(3)] \
        + [(280 + k * use, "boss") for k in range(8)]
    bolts, pops = [], []
    trail = []
    notes = [(0, "Jade Staff: held and turned to the cursor like vanilla's gem staffs; a weaving bolt (%d damage, %d mana)" % (KJ["Damage"], KJ["Mana"])),
             (60, "three hits turn the Jade Golem to jade for 2.5 s"),
             (150, "bolts fired over it home in on it: they chase enemies turned to jade (within %d tiles)" % (KJ["HomingRange"] // 16)),
             (280, "a boss already turned to jade twice (fast-forward): six more stacks turn it a third time..."),
             (525, "...and after the third it is immune to the curse for the rest of the fight")]
    cursor = (foe.x, G - 36.0)
    for tick in range(597):
        aim_goal = {"foe": (foe.x, G - 52.0), "over": (foe.x + 40, G - 200.0), "boss": (boss.x, BOSS_FLOOR - 45.0)}
        current = [c for c in casts if c[0] <= tick]
        kind = current[-1][1] if current else "foe"
        goal = aim_goal[kind]
        cursor = (lerp(cursor[0], goal[0], 0.25), lerp(cursor[1], goal[1], 0.25))
        for (t0, k) in casts:
            if tick == t0:
                dx, dy = cursor[0] - centre[0], cursor[1] - centre[1]
                n = math.hypot(dx, dy) or 1.0
                bolts.append(JadeBoltSim(centre, (dx / n * KJ["ShotSpeed"], dy / n * KJ["ShotSpeed"])))
        present = (foe, boss) if tick >= BOSS_IN else (foe,)
        petrified = [(i, t.x, G - 52.0 if not t.boss else BOSS_FLOOR - 45.0) for i, t in enumerate(present) if t.stone > 0]
        for b in bolts:
            if not b.alive:
                continue
            b.update(petrified)
            trail.append((tick, b.pos))
            for i, t in enumerate(present):
                half = 30 if t.boss else FOE_HALF
                floor = BOSS_FLOOR if t.boss else G
                top = floor - (90 if t.boss else FOE_H)
                if i not in b.hit and t.x - half < b.pos[0] < t.x + half and top < b.pos[1] < floor:
                    b.hit.add(i)
                    label = t.hit()
                    pops.append((tick, t.x - 40, floor - (130 if t.boss else 110), "%d %s" % (KJ["Damage"], label),
                                 JADE if "JADE" in label or label in ("frozen",) else (STEAM if label in ("warded", "immune") else HIT)))
                    if len(b.hit) >= 2:
                        b.alive = False
            if b.pos[1] > G or b.pos[0] > W + 20 or b.age > KJ["Lifetime"]:
                b.alive = False
        moved = foe.tick()
        boss.tick()
        if moved and foe.x > 330:
            foe.x -= KG["WalkSpeed"]
            foe.counter = (foe.counter + KG["WalkSpeed"]) % (KG["WalkStep"] * KG["WalkFrames"])
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        frame = int(KG["Walk"] + int(foe.counter / KG["WalkStep"]) % int(KG["WalkFrames"]))
        golem.draw(layer, frame, (foe.x, G), False)
        img.alpha_composite(tinted(layer, JADE) if foe.stone > 0 else layer)
        bx = boss.x
        if tick >= BOSS_IN:
            d.rectangle([bx - 30, BOSS_FLOOR - 90, bx + 30, BOSS_FLOOR], fill=JADE + (255,) if boss.stone > 0 else (120, 70, 60, 255),
                        outline=(47, 27, 20, 255))
            gif.text(img, (int(bx - 18), int(BOSS_FLOOR - 56)), "boss", fill=STEAM)
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        using = any(t0 <= tick < t0 + use for (t0, _) in casts)
        if using:                                              # Item.staff: the sprite's diagonal along the aim, held at its corner
            aim = math.atan2(cursor[1] - centre[1], cursor[0] - centre[0])
            hx, hy = centre[0] + math.cos(aim) * 6 - 2, centre[1] + math.sin(aim) * 6 - 4
            r = 60
            pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
            pad.alpha_composite(staff, (r, r - staff.height))
            rot = pad.rotate(-math.degrees(aim + math.pi / 4), resample=Image.NEAREST)
            img.alpha_composite(rot, (int(hx - r), int(hy - r)))
        for (t0, p) in trail:
            if tick - t0 < 10:
                d.point((p[0], p[1]), fill=JADE + (255,))
        for b in bolts:
            if b.alive:
                img.alpha_composite(bolt_img, (int(b.pos[0] - bolt_img.width / 2), int(b.pos[1] - bolt_img.height / 2)))
        cx, cy = cursor                                        # the cursor
        d.line([cx - 7, cy, cx - 2, cy], fill=(255, 255, 255, 255), width=2)
        d.line([cx + 2, cy, cx + 7, cy], fill=(255, 255, 255, 255), width=2)
        d.line([cx, cy - 7, cx, cy - 2], fill=(255, 255, 255, 255), width=2)
        d.line([cx, cy + 2, cx, cy + 7], fill=(255, 255, 255, 255), width=2)
        homing = any(b.alive and getattr(b, "homing", False) for b in bolts)
        for t, name in ((foe, "Golem"), (boss, "boss")) if tick >= BOSS_IN else ((foe, "Golem"),):
            if t.stone:
                state = "JADE %.1f s" % (t.stone / 60)
            elif t.boss and t.petrifications >= KJ["BossPetrifyLimit"]:
                state = "IMMUNE (turned to jade %d/%d)" % (t.petrifications, KJ["BossPetrifyLimit"])
            elif t.ward:
                state = "ward %.1f s" % (t.ward / 60)
            else:
                state = "stacks %d/%d%s" % (t.stacks, t.need, (" | jade %d/%d" % (t.petrifications, KJ["BossPetrifyLimit"])) if t.boss else "")
            lx, ly = (t.x - 250, BOSS_FLOOR - 112) if t.boss else (t.x - 60, G - 160)
            gif.text(img, (int(lx), int(ly)), "%s: %s" % (name, state), fill=JADE if t.stone or t.stacks else STEAM)
        if homing:
            gif.text(img, (10, H - 22), "a bolt is homing in on an enemy turned to jade", fill=JADE)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The mirrored jump: the Beat-Boxer (the Imperial Defender's half went with it, 2026-11-11)
# ================================================================================================
class Walker:
    def __init__(self, planes, k, x, ground, speed, jump_frame):
        self.p, self.k, self.x, self.y, self.vx, self.vy = planes, k, x, float(ground), 0.0, 0.0
        self.ground, self.speed, self.jump_frame = ground, speed, jump_frame
        self.counter, self.cooldown, self.rising, self.face = 0.0, 0, False, 1
        self.jumps = 0

    def grounded(self):
        return self.y >= self.ground and self.vy == 0.0

    def update(self, target):
        """GridWalkerNPC.Run towards the target (stopping a little short in the sim) and MirrorJump."""
        dx = target.x - self.x
        want = (1 if dx > 0 else -1) * self.speed if abs(dx) > 70 else 0.0
        self.vx = min(want, self.vx + 0.07) if self.vx < want else max(want, self.vx - 0.07)
        self.face = 1 if dx > 0 else -1
        if self.cooldown > 0:
            self.cooldown -= 1
        rising = target.vy < KW["MirrorJumpRise"]
        started = rising and not self.rising
        self.rising = rising
        if started and self.cooldown == 0 and self.grounded() and abs(dx) <= KW["MirrorJumpRangeX"] \
                and abs((target.y - 21) - (self.y - 30)) <= KW["MirrorJumpRangeY"]:
            self.vy = -KW["MirrorJumpSpeed"]
            self.cooldown = int(KW["MirrorJumpCooldown"])
            self.jumps += 1
        self.vy = min(10.0, self.vy + 0.3) if (self.vy != 0.0 or self.y < self.ground) else self.vy
        self.x += self.vx
        self.y += self.vy
        if self.y >= self.ground:
            self.y, self.vy = float(self.ground), 0.0
        if self.grounded() and abs(self.vx) > 0.15:
            self.counter = (self.counter + abs(self.vx)) % (self.k["WalkStep"] * self.k["WalkFrames"]) if "WalkStep" in self.k else self.counter + abs(self.vx)

    def frame(self):
        if not self.grounded():
            return self.jump_frame
        if abs(self.vx) > 0.15:
            step = self.k["WalkStep"] if "WalkStep" in self.k else 4.0
            return int(self.k["Walk"] + int(self.counter / step) % int(self.k["WalkFrames"]))
        return int(self.k["Idle"])


def scene_jumps(out, font):
    W, H, G = 900, 320, 292
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    p = Player(450.0, G)
    boxer = Walker(Planes("Content/Dungeon/NPCs/BeatBoxer", KB), KB, 700.0, G, KB["WalkSpeed"], int(KB["Walk"] + 2))
    jumps = {60: "jump", 150: "jump", 240: "jump", 262: "double"}
    notes = [(0, "the Beat-Boxer walks at the player..."),
             (60, "...and jump when the player jumps (%.0f px/tick: about %.1f tiles; within %d x %d tiles)" % (
                 KW["MirrorJumpSpeed"], KW["MirrorJumpSpeed"] ** 2 / 0.6 / 16, KW["MirrorJumpRangeX"] // 16, KW["MirrorJumpRangeY"] // 16)),
             (262, "a double jump in the air: it isn't on the ground, so it doesn't jump again")]
    for tick in range(360):
        if tick in jumps:
            if jumps[tick] == "jump":
                p.jump()
            else:
                p.vy, p.hold = -5.01, 12                       # a Cloud in a Bottle's second jump (approximated)
        p.step()
        boxer.update(p)
        if tick % TPF:
            continue
        img = bg.copy()
        for w in (boxer,):
            w.p.draw(img, w.frame(), (w.x, w.y), w.face == 1)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        gif.text(img, (W - 250, 40), "Beat-Boxer (right): %d jumps" % boxer.jumps, fill=STEAM)
        gif.text(img, (W // 2 - 60, 40), "player: %d jumps" % sum(1 for t in jumps if t <= tick), fill=STEAM)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Fundamental Stones
# ================================================================================================
def stone_image(style, glow=1.0):
    from old_brass_town_sim import stone_sprite
    base = stone_sprite(style, glow=False)
    if glow > 0:
        lit = stone_sprite(style, glow=True)
        base = Image.blend(base, lit, max(0.0, min(1.0, glow))) if glow < 1.0 else lit
    return base


def westworld_crop(lit=False, margin=(22, 14)):
    """Old Brass Town's replay with its stone (old_brass_town_sim.Town, seed 7), cropped round the stone."""
    import old_brass_town_sim as obt
    k = obt.constants(obt.PASS)
    bps, order = obt.blueprints()
    town = obt.Town(k, bps, order, 7)
    img = obt.draw_town(town, lit=lit)
    sx, floor, shift = town.stone
    x0, y0 = (sx - margin[0] // 3) * 16, (floor - margin[1]) * 16
    return img.crop((x0, y0, x0 + margin[0] * 16 + 64, y0 + margin[1] * 16 + 48)), (sx * 16 - x0, (floor - 6) * 16 - y0), shift


def tar_pit_crop():
    """The tar pit's floor (JunkyardPass: two rows of sand on stone under the tar) with its stone in the middle; the tar is
    vanilla water restyled (drawn over it at 60%, as vanilla draws water in front)."""
    W, H = 30 * 16, 14 * 16
    img = Image.new("RGBA", (W, H), (26, 20, 16, 255))
    d = ImageDraw.Draw(img)
    floor = 10 * 16
    for x in range(0, W, 16):
        for row in range(4):
            col = (196, 168, 112) if row < 2 else (104, 96, 92)
            d.rectangle([x, floor + row * 16, x + 15, floor + row * 16 + 15], fill=col + (255,))
            d.line([x, floor + row * 16, x + 15, floor + row * 16], fill=tuple(max(0, c - 30) for c in col) + (255,))
    img.alpha_composite(stone_image(0), (W // 2 - 32, floor - 96))
    tar = Image.new("RGBA", (W, floor), (40, 26, 18, 153))
    img.alpha_composite(tar, (0, 0))
    glow_only = Image.new("RGBA", (64, 96), (0, 0, 0, 0))     # the cuts' light (the glow is drawn with the tile, under the tar)
    gl = load(SEC + "FundamentalStoneTile_Glow.png")
    for ty in range(6):
        for tx in range(4):
            glow_only.alpha_composite(gl.crop((tx * 18, ty * 18, tx * 18 + 16, ty * 18 + 16)), (tx * 16, ty * 16))
    img.alpha_composite(faded(glow_only, 0.45), (W // 2 - 32, floor - 96))
    return img


def stones_png(out, font):
    from PIL import ImageFont
    f = ImageFont.truetype(font, 16)
    rows = []
    for bg in ((22, 24, 30, 255), (150, 180, 210, 255)):
        row = Image.new("RGBA", (5 * 140 + 20, 220), bg)
        for s in range(5):
            row.alpha_composite(stone_image(s).resize((128, 192), Image.NEAREST), (20 + s * 140, 14))
        rows.append(row)
    west, at, shift = westworld_crop()
    pit = tar_pit_crop()
    runes = load(SEC + "FundamentalRunes.png")
    runes = runes.resize((runes.width * 2, runes.height * 2), Image.NEAREST)
    W = max(rows[0].width, west.width + pit.width + 60) + 40
    H = 40 + sum(r.height for r in rows) + 40 + max(west.height, pit.height) + 50 + runes.height + 50
    sheet = Image.new("RGBA", (W, H), (28, 28, 34, 255))
    d = ImageDraw.Draw(sheet)
    d.text((20, 12), "The five Fundamental Stones (4x6 tiles; at 2x here), each with its own sigil; their runes glow (the _Glow sheet)",
           font=f, fill=(238, 241, 243))
    y = 40
    for r in rows:
        sheet.alpha_composite(r, (20, y))
        y += r.height
    y += 10
    d.text((20, y), "Westworld (the pass replayed, seed 7, map-lit):", font=f, fill=(238, 241, 243))
    d.text((20, y + 20), "the street's west end, a niche cut into the rock", font=f, fill=(238, 241, 243))
    d.text((40 + west.width, y), "The tar pit: on the pool's floor,", font=f, fill=(238, 241, 243))
    d.text((40 + west.width, y + 20), "in its middle, under the tar", font=f, fill=(238, 241, 243))
    y += 46
    sheet.alpha_composite(west, (20, y))
    sheet.alpha_composite(pit, (40 + west.width, y))
    y += max(west.height, pit.height) + 14
    d.text((20, y), "The runes (FundamentalRunes.png): the five sigils, then eleven runes (2x)", font=f, fill=(238, 241, 243))
    sheet.alpha_composite(runes, (20, y + 26))
    sheet.convert("RGB").save(out, optimize=True)
    print(out, sheet.size)


def scene_reading(out, font):
    west, at, _ = westworld_crop(margin=(30, 14))
    W, H = west.width, west.height
    gif = Gif(font, (W, H), scale=1.0)
    runes = load(SEC + "FundamentalRunes.png")
    stone_x, stone_y = at
    floor = stone_y + 96
    anchor = (stone_x + 32, stone_y)                          # the stone's top centre
    px = float(W - 60)
    line = INSCRIPTIONS[1]
    opened, age, closing, style = None, 0, 0, 1
    notes = [(0, "Westworld's Fundamental Stone: walk up and right-click it (the cursor shows its name)"),
             (90, "its runes light up one by one over it (%d ticks apart)" % KS["RevealTicks"]),
             (250, "walking more than %d tiles away (or reading it again) fades them" % (KS["CloseRange"] // 16))]
    for tick in range(380):
        if tick < 80:
            px -= 1.6
        elif tick > 240:
            px += 2.4
        if tick == 90:
            opened, age, closing = True, 0, 0
        if opened:
            age += 1
            if closing == 0 and (age >= KS["HoldTicks"] or abs(px - anchor[0]) > KS["CloseRange"]):
                closing = 1
            if closing > 0:
                closing += 1
                if closing > KS["FadeOutTicks"]:
                    opened = None
        if tick % TPF:
            continue
        breath = 0.85 + 0.15 * math.sin(tick / 60.0 * 1.57 + style * 1.3)
        img = west.copy()
        img.alpha_composite(stone_image(1, breath), (stone_x, stone_y))
        img.alpha_composite(player_sprite(flip=True), (int(px - 20), int(floor - 56)))
        if 60 <= tick < 92:                                    # the cursor over the stone, its name
            cx, cy = anchor[0] + 6, anchor[1] + 40
            d = ImageDraw.Draw(img)
            d.polygon([(cx, cy), (cx + 10, cy + 12), (cx + 4, cy + 12), (cx, cy + 18)], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255))
            gif.text(img, (int(cx + 14), int(cy + 14)), "Fundamental Stone")
        if opened:
            alpha = min(1.0, age / KS["FadeInTicks"]) * (1.0 - closing / KS["FadeOutTicks"] if closing else 1.0)
            n = len(line)
            gw, gh, gap, pad = 14, 18, 4, 12
            pw, ph = n * gw + (n - 1) * gap + 2 * pad, gh + 2 * pad
            x0, y0 = int(anchor[0] - pw / 2), int(anchor[1] - 10 - ph)
            panel = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            pd = ImageDraw.Draw(panel)
            pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=6, fill=(14, 20, 46, int(230 * alpha)), outline=(60, 76, 130, int(230 * alpha)), width=2)
            img.alpha_composite(panel, (x0, y0))
            for k, g in enumerate(line):
                shown = (age - KS["FadeInTicks"] / 2 - k * KS["RevealTicks"]) / KS["RevealTicks"]
                if shown <= 0:
                    break
                glyph = runes.crop((g * 16, 0, g * 16 + gw, gh))
                b = breath if k == 0 else 1.0
                img.alpha_composite(faded(glyph, alpha * min(1.0, shown) * b), (x0 + pad + k * (gw + gap), y0 + pad))
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Cursed Conductor's ghosts: one a lantern attack, two a loop
# ================================================================================================
def scene_lantern_ghost(out, font):
    import update_2026_11_05_sim as c5
    from update_2026_11_04b_sim import Conductor
    from update_2026_11_09_sim import draw_halo, lantern_point, idle_frame, hover_spot
    KC = c5.KC
    W, H, G = 900, 420, 380
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.0)
    boss = Conductor()
    p = Player(560.0, G)
    boss.x, boss.y = hover_spot((p.x, p.y), -1.0, False)
    boss.face = 1
    bolts, rifts, ghosts, pops = [], [], [], []
    throw_t, volley, claimed = -1, 0, set()
    notes = [(0, "the lantern: a fan of %d cursed bolts; the first of a fan to strike a block opens a ghost rift..." % KC["Bolts"]),
             (70, "...the rest just burst: one ghost a lantern attack (it was one per bolt that landed)"),
             (200, "the second attack: again three bolts down, again one rift")]
    for tick in range(330):
        if tick in (10, 150):
            throw_t = 0
            volley += 1
        if throw_t >= 0:
            throw_t += 1
            if throw_t == KC["ThrowWindup"]:
                fx, fy = lantern_point(boss, idle_frame(tick))
                tx, ty = p.x + 30, G - 6                         # the player dodged: the fan lands round their feet
                dx, dy = tx - fx, ty - fy
                n = math.hypot(dx, dy) or 1.0
                ax, ay = dx / n * KC["BoltSpeed"], dy / n * KC["BoltSpeed"]
                for k in range(int(KC["Bolts"])):
                    turn = (k - (KC["Bolts"] - 1) * 0.5) * KC["BoltSpread"]
                    c, s = math.cos(turn), math.sin(turn)
                    b = c5.Bolt(fx, fy, ax * c - ay * s, ax * s + ay * c)
                    b.volley = volley
                    bolts.append(b)
            if throw_t >= KC["ThrowWindup"] + KC["ThrowRelease"] + KC["ThrowRecover"]:
                throw_t = -1
        for b in list(bolts):
            if not b.update(G):
                bolts.remove(b)
                if b.landed:
                    if b.volley not in claimed:                # CursedConductor.ClaimVolleyGhost
                        claimed.add(b.volley)
                        rifts.append(c5.Rift(b.x, G - 14, KC["RiftDelay"]))
                        pops.append((tick, b.x - 30, G - 60, "rift", (140, 201, 176)))
                    else:
                        pops.append((tick, b.x - 20, G - 40, "burst", STEAM))
        for r in list(rifts):
            if not r.update():
                rifts.remove(r)
                ghosts.append(c5.Ghost(r.x, r.y - 10))
        for g in ghosts:
            g.update((p.x, p.y - PLAYER_H / 2))
        if tick % TPF:
            continue
        img = bg.copy()
        frame = idle_frame(tick)
        boss.draw(img, frame, 1.0, TPF)
        draw_halo(img, boss, frame, throw_t)
        for r in rifts:
            r.draw(img)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        for g in ghosts:
            g.draw(img)
        for b in bolts:
            b.draw(img)
        gif.text(img, (10, H - 22), "lantern attacks: %d | ghosts raised: %d" % (volley, len(ghosts) + len(rifts)), fill=STEAM)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.push(img)
    gif.save(out)


def scene_loop_ghosts(out, font):
    import update_2026_11_05_sim as c5
    from update_2026_11_04b_sim import Conductor
    KC, KT = c5.KC, c5.KT
    KCC = consts("Content/Bosses/CursedConductor/CursedConductor.cs")
    laps_with_ghosts = int(KCC["LoopGhostLaps"])
    W, H, G = 1920, 1080, 980
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W // 2, H // 2), scale=1.0)
    boss = Conductor()
    p = c5.Player(W / 2 - 100, G)
    c5.place_boss(boss, (p.x, p.y - c5.PLAYER_H / 2), 1)
    locked = (p.x, p.y - c5.PLAYER_H / 2)
    trains, rifts, ghosts, notes = [], [], [], []
    total = KC["LoopTicks"] + 30
    for t in range(total):
        if t == KC["LoopTelegraph"]:
            top = (locked[0], locked[1] - KC["LoopRadius"])
            trains.append(c5.Train("loop", (top[0] + KC["LoopApproach"], top[1]), (-KC["LoopSpeed"], 0.0), locked[0], locked[1]))
        for lap in range(int(KT["LoopLaps"])):
            if t == KC["LoopTelegraph"] + KC["LoopEnter"] + lap * KC["LapTicks"] + 4:
                if lap < laps_with_ghosts:
                    a = 0.7 + lap * 1.3
                    off = (math.cos(a) * KC["LoopGhostRadius"], math.sin(a) * KC["LoopGhostRadius"])
                    rifts.append(c5.Rift(locked[0] + off[0], locked[1] + off[1], KC["LoopGhostDelay"]))
                    rifts.append(c5.Rift(locked[0] - off[0], locked[1] - off[1], KC["LoopGhostDelay"]))
                    notes.append((t, "lap %d: two ghosts rise on opposite sides inside the ring" % (lap + 1)))
                else:
                    notes.append((t, "lap %d: no more ghosts (2 at most while it circles; it was 2 every lap)" % (lap + 1)))
        for r in list(rifts):
            if not r.update():
                rifts.remove(r)
                ghosts.append(c5.Ghost(r.x, r.y))
        for g in ghosts:
            g.update((p.x, p.y - c5.PLAYER_H / 2))
        trains = [tr for tr in trains if tr.update()]
        boss.move_toward((p.x + KC["HoverOffsetX"], p.y - c5.PLAYER_H / 2 + KC["HoverOffsetY"]), KC["HoverSpeed"])
        if t % 3:
            continue
        img = bg.copy()
        ring = c5.strength(t, KC["LoopTelegraph"] + KC["LoopEnter"])
        if ring > 0:
            piece = c5.rail_piece("ring", ring)
            cell = KC["RailCell"]
            for k in range(KC["RingDots"]):
                a = c5.TWO_PI * k / KC["RingDots"]
                img.alpha_composite(piece, (int(locked[0] + math.cos(a) * KC["LoopRadius"] - cell / 2), int(locked[1] + math.sin(a) * KC["LoopRadius"] - cell / 2)))
        boss.draw(img, c5.idle_frame(t))
        for r in rifts:
            r.draw(img)
        img.alpha_composite(player_sprite(), (int(p.x - 20), int(p.y - 56)))
        for g in ghosts:
            g.draw(img)
        for tr in trains:
            tr.draw(img)
        out_img = c5.half(img)
        gif.text(out_img, (10, 8), "The Loop (2026-11-10): %d laps round the trapped player; two ghosts on the first lap only" % KT["LoopLaps"])
        live = [s for (t0, s) in notes if 0 <= t - t0 < 110]
        if live:
            gif.text(out_img, (10, 26), live[-1], fill=(184, 138, 51))
        gif.text(out_img, (10, H // 2 - 22), "ghosts raised: %d" % (len(ghosts) + len(rifts)), fill=STEAM)
        gif.push(out_img)
    gif.save(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    o = lambda name: os.path.join(args.out, name)   # noqa: E731
    jobs = [("jade", lambda: scene_jade(o("2026-11-10_gems-jade-staff-homing.gif"), args.font)),
            ("jumps", lambda: scene_jumps(o("2026-11-10_enemies-mirror-jump.gif"), args.font)),
            ("stones", lambda: stones_png(o("2026-11-10_secrets-fundamental-stones.png"), args.font)),
            ("reading", lambda: scene_reading(o("2026-11-10_secrets-fundamental-stone-reading.gif"), args.font)),
            ("lantern", lambda: scene_lantern_ghost(o("2026-11-10_boss-cursed-conductor-lantern-ghost.gif"), args.font)),
            ("loop", lambda: scene_loop_ghosts(o("2026-11-10_boss-cursed-conductor-loop-ghosts.gif"), args.font))]
    only = set(args.only.split(",")) if args.only else None
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
