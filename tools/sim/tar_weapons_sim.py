"""D5 proofs for the tar and polished-metal weapons of 2026-10-30 (Content/Junkyard/Weapons/), built from the real
sprites and the constants parsed out of the C# files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/tar_weapons_sim.py --out docs/media --date 2026-11-03 [--only sprites,wrench,tarmancer,staff,shower,whip]

Writes:
    <date>_weapons-tar-sprites.png      the four items, their projectiles, effects and buff icons at 2x zoom, on a dark and
                                        a light background.
    <date>_weapon-metal-wrench.gif      swings at a mechanical enemy (+50%); a right-click guard, a Living Tar's lunge
                                        clangs off it (the clash), the riposte ready (its buff); the riposte swing (x2.5);
                                        the cooldown (skipped, labelled); a riposte on a boss (Tar Tyrant): the boss clash
                                        and half a second of slow motion for every entity (one update in five).
    <date>_weapon-tarmancer.gif         two tar slimes (the Living Tar's own sprite, its two frames cycled like a vanilla
                                        slime's, a squash as it spits) hop after the player and spit at two Rust Collectors
                                        every 68 ticks (the Imp Staff's rate, 2026-11-03); each glob coats its target: the
                                        Tar Plague's tick every 30 ticks and half speed.
    <date>_weapon-tar-bone-staff.gif    slow skulls (3.5 px/tick) home in the Book of Skulls' way (1/32 of the turn a tick),
                                        bite the first enemy and burst: a 5-tile circle that hurts the others.
    <date>_weapon-tar-shower.gif        the spray (4 bursts a use, growing, ~16 tiles since 2026-11-03; the old ~12-tile
                                        reach marked) plaguing two walkers; then a 2.5 s charge (the ball's five sizes and
                                        the full rim), the big glob arcing through both enemies, its 6-tile stain, a third
                                        enemy walking into it.
    <date>_weapon-tar-whip.gif          (2026-11-03) the Tar Whip's lash (Projectile.FillWhipControlPoints replayed) on
                                        three walkers: 29, then -10% each, 2 s of Tar Plague; then in the Tyrant set: 25%
                                        faster lashes and 3.5 s of plague (the timers over the enemies).

Leaves out: lighting, vanilla's exact item and arm drawing (the player is a standing sprite, the swing is the item sprite
turned about the hand by vanilla's style-1 formula), tile collision beyond a flat floor, enemy AI (they walk), defense,
crits, network latency. Downtimes are shortened where labelled.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, frames, player_sprite, Enemy, collector_sprite, rotated, glow_over, TPF  # noqa: E402

D = "Content/Junkyard/Weapons/"
# one table per class: several of them share names (Lifetime, Frames, Gravity, UseTime...)
KW = consts(D + "MetalWrench.cs")
KG = consts(D + "MetalWrench.cs", D + "MetalWrenchGuard.cs")
KC = consts(D + "MetalClash.cs")
KM = consts(D + "TarSlimeMinion.cs")
KMS = consts(D + "TarSlimeShot.cs")
KB = consts(D + "TarBoneStaff.cs")
KSK = consts(D + "TyrantSkullBolt.cs")
KS = consts(D + "TarShower.cs")
KSP = consts(D + "TarSpray.cs")
KCH = consts(D + "TarShowerCharge.cs")
KBG = consts(D + "TarShowerBigGlob.cs")
KST = consts(D + "TarStain.cs")
KP = consts("Content/Junkyard/Tar/TarPlayer.cs", "Core/Systems/NPCHaste.cs")
EMBER = (255, 199, 90)
PLAGUE = (196, 160, 120)
AETHER = (198, 189, 255)


def sheet(name, w, h, stride, n):
    return frames(D + name, w, h, stride, n)


def living_tar():
    return load("Content/Junkyard/NPCs/LivingTar.png").crop((0, 0, 32, 24))


class Foe(Enemy):
    """An enemy that walks at `speed`, halved while plagued (NPCHaste.SlowFactor), taking the plague's chunks."""

    def __init__(self, sprite, x, ground, speed=0.0, name="", mech=False, life=200):
        super().__init__(sprite, x, ground, name=name)
        self.speed, self.mech, self.life = speed, mech, life
        self.plague_until = -1
        self.plague_count = 0

    def plague(self, tick, ticks):
        self.plague_until = max(self.plague_until, tick + ticks)

    def walk(self, tick, move=True):
        slowed = tick < self.plague_until
        if move:
            self.x += self.speed * (KP["SlowFactor"] if slowed else 1.0)
        if slowed:
            self.plague_count += 1
            if self.plague_count % KP["TickInterval"] == 0:
                self.hit(tick, KP["TickDamage"], PLAGUE)
        else:
            self.plague_count = 0

    def draw(self, img, gif, tick, cam=(0, 0)):
        spr = self.sprite
        if tick < self.plague_until:
            r, g, b, a = spr.split()
            spr = Image.merge("RGBA", (r.point(lambda v: int(v * 0.55)), g.point(lambda v: int(v * 0.5)), b.point(lambda v: int(v * 0.46)), a))
        img.alpha_composite(spr, (int(self.x - cam[0]), int(self.y - cam[1])))
        for (t0, s, col) in self.numbers:
            if 0 <= tick - t0 < 40:
                gif.text(img, (int(self.x - cam[0]) + 4, int(self.y - cam[1]) - 18 - (tick - t0) // 2), s, fill=col, font=gif.big)


def centre(f):
    return (f.x + f.sprite.width / 2, f.y + f.sprite.height / 2)


def heading(vx, vy, n=16):
    a = math.atan2(vy, vx)
    return int(round(a / (2 * math.pi) * n)) % n


def paste_centre(img, spr, c):
    img.alpha_composite(spr, (int(c[0] - spr.width / 2), int(c[1] - spr.height / 2)))


# ================================================================================================
# Sprites
# ================================================================================================
def sprites_png(out, font):
    items = ["MetalWrench.png", "Tarmancer.png", "TarBoneStaff.png", "TarShower.png", "TarWhip.png"]
    others = ["MetalClash.png", "../NPCs/LivingTar.png", "TarSlimeMinion_Wings.png", "TarSlimeShot.png", "TarWhipProjectile.png", "TarWhipDebuff.png", "TyrantSkullBolt.png", "TyrantSkullBlast.png", "TarSpray.png",
              "TarShowerGlob.png", "TarShowerBigGlob.png", "TarShowerCharge.png", "TarStain.png", "WrenchRiposteBuff.png", "WrenchParryCooldown.png",
              "TarSlimeBuff.png"]
    gif = Gif(font, (10, 10))
    W, H = 1700, 1180
    out_img = Image.new("RGBA", (W, H), (36, 40, 48, 255))
    ImageDraw.Draw(out_img).rectangle([W // 2, 0, W, H], fill=(150, 180, 210, 255))
    for half in (0, 1):
        x0 = half * W // 2 + 16
        x, y = x0, 40
        gif.text(out_img, (x0, 8), "items (2x zoom of the game sprite)" if half == 0 else "on a light background")
        for name in items:
            im = load(D + name)
            big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            out_img.alpha_composite(big, (x, y))
            gif.text(out_img, (x, y + big.height + 2), name[:-4])
            x += big.width + 28
        x, y = x0, 220
        row_h = 0
        for name in others:
            im = load(D + name)
            if im.height > 400:                             # long sheets: the first frames only
                im = im.crop((0, 0, im.width, 400))
            big = im.resize((im.width * 2, im.height * 2), Image.NEAREST) if im.width < 120 else im
            if x + big.width > half * W // 2 + W // 2 - 16:
                x, y = x0, y + row_h + 30
                row_h = 0
            out_img.alpha_composite(big, (x, y))
            gif.text(out_img, (x, y + big.height + 2), name[:-4][:18])
            x += big.width + 18
            row_h = max(row_h, big.height)
    out_img.convert("RGB").save(out)
    print(out, out_img.size)


# ================================================================================================
# Metal Wrench
# ================================================================================================
def swing_rotation(anim, anim_max, direction):
    """Vanilla's style-1 swing (decompiled Player.ItemCheck_ApplyUseStyle_Inner): the item's rotation over the use."""
    return ((anim / anim_max) - 0.5) * (-direction) * 3.5 - direction * 0.3


def draw_wrench_swing(img, wrench, hand, rot):
    """The item sprite (pointing to the top right) turned by `rot` about its handle corner, like vanilla's held item."""
    pad = Image.new("RGBA", (wrench.width * 2, wrench.height * 2))
    pad.alpha_composite(wrench, (wrench.width, 0))          # the handle corner (bottom left) at the pad's centre
    r = pad.rotate(-math.degrees(rot), resample=Image.NEAREST)
    img.alpha_composite(r, (int(hand[0] - pad.width / 2), int(hand[1] - pad.height / 2)))


def draw_guard(img, wrench, hand, raise_):
    axis = KG["RestAngle"] + (KG["GuardAngle"] - KG["RestAngle"]) * raise_
    draw_wrench_swing(img, wrench, hand, axis + math.pi / 4)


def scene_wrench(out, font):
    """Swings at a mechanical enemy; the guard, a Living Tar's lunge clanging off it; the riposte; the cooldown (skipped);
    then next to a boss: the riposte lands, the boss clash, and half a second of slow motion (entities update on one tick
    in five, SlowMotion.PreUpdatePlayers, while the clash itself keeps full speed: CogpunkSets.IgnoresSlowMotion)."""
    wrench = load(D + "MetalWrench.png")
    clash = sheet("MetalClash.png", 64, 64, 66, KC["Frames"])
    riposte_icon = load(D + "WrenchRiposteBuff.png")
    cooldown_icon = load(D + "WrenchParryCooldown.png")
    import tartyrant_sim as tts
    W, H, G = 600, 300, 250
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    pc = (190.0, G - 21.0)
    hand = (pc[0] + 6, pc[1] - 4)
    use = KW["UseTime"]
    mech = Foe(collector_sprite(), pc[0] + 26, G, name="mech", mech=True)
    tar = Foe(living_tar(), pc[0] + 170, G, name="tar")
    boss_anchor = pc[0] + 150
    plan = [("swing", use, "Left click: a slow sword swing (30 ticks), +50% to mechanical enemies"),
            ("swing", use, "Left click: a slow sword swing (30 ticks), +50% to mechanical enemies"),
            ("guard", KW["ParryTicks"], "Right click: on guard for 1 s; a blow in that window clangs off"),
            ("swing_r", use, "Parried! The riposte: the next swing deals x2.5"),
            ("cool", 30, "The parry recovers for 3 s (skipped here)"),
            ("ready", 24, "Next to a boss, a riposte ready (from another parry)"),
            ("swing_b", use + 40, "The riposte lands on a boss: a clash, and every entity slows by 80% for 0.5 s"),
            ("after", 36, "...and time runs on")]
    tick, boss_frame, slow_left, accum = 0, 0, 0, 0.0
    clash_at, clash_t0, clash_big = None, -99, False
    riposte = False
    for mode, length, label in plan:
        anim = use if mode.startswith("swing") else 0
        hit_done = False
        lunge = 0 if mode == "guard" else None
        guard_t = 0
        for t in range(length):
            update = True
            if slow_left > 0:
                slow_left -= 1
                accum += KW["SlowMotionSpeed"]
                update = accum >= 1.0
                if update:
                    accum -= 1.0
            if update:
                boss_frame += 1
                if anim > 0:
                    anim -= 1
                if mode == "guard":
                    guard_t += 1
                    if guard_t > 16 and lunge is not None:   # the Living Tar leaps at the player mid-guard
                        lunge += 1
                        tar.x -= 6.5
                        tar.y = G - tar.sprite.height - 34 * math.sin(min(1.0, lunge / 18.0) * math.pi)
                        if tar.x < pc[0] + 20:
                            lunge = None
                            tar.x, tar.y, tar.vx = pc[0] + 24, G - tar.sprite.height, 4.0
                            clash_at, clash_t0, clash_big = (pc[0] + 22, pc[1] - 6), tick, False
                            riposte = True
                tar.step()
            if mode.startswith("swing") and not hit_done and anim < use * 0.55:
                hit_done = True
                if mode == "swing":
                    mech.hit(tick, int(32 * (1 + KW["MechanicalBonus"] / 100)), EMBER)
                elif mode == "swing_r":
                    tar.hit(tick, int(32 * KW["RiposteMultiplier"]), AETHER)
                    tar.vx = 6.0
                    riposte = False
                    clash_at, clash_t0, clash_big = (tar.x + 4, tar.y + 6), tick, False
                else:
                    riposte = False
                    clash_at, clash_t0, clash_big = (pc[0] + 40, pc[1] - 14), tick, True
                    slow_left, accum = KW["SlowMotionTicks"], 0.0
            if mode == "ready" and t == 0:
                riposte = True
            if tick % TPF == 0:
                img = bg.copy()
                boss_scene = mode in ("ready", "swing_b", "after")
                if boss_scene:
                    tts.draw_boss(img, tts.R["Idle0"] + boss_frame // 8 % tts.R["IdleFrames"], round(boss_anchor), G, False, W, scale=0.6)
                else:
                    mech.draw(img, gif, tick)
                    tar.draw(img, gif, tick)
                img.alpha_composite(player_sprite(), (int(pc[0] - 20), int(pc[1] - 35)))
                if anim > 0:
                    draw_wrench_swing(img, wrench, hand, swing_rotation(anim, use, 1))
                elif mode == "guard" and (lunge is not None or tick - clash_t0 < 10):
                    draw_guard(img, wrench, hand, min(1.0, guard_t / KG["RaiseTicks"]))
                if clash_at is not None and 0 <= tick - clash_t0 < KC["Lifetime"]:
                    glow_over(img, clash[min(KC["Frames"] - 1, (tick - clash_t0) // KC["FrameTicks"])], 1.0, (clash_at[0] - 32, clash_at[1] - 32))
                if boss_scene and clash_big and 0 <= tick - clash_t0 < 40:
                    gif.text(img, (int(pc[0] + 20), int(pc[1] - 70 - (tick - clash_t0) // 6)), str(int(32 * KW["RiposteMultiplier"])), fill=AETHER, font=gif.big)
                if riposte:
                    img.alpha_composite(riposte_icon, (int(pc[0] - 16), int(pc[1] - 76)))
                if mode == "cool":
                    img.alpha_composite(cooldown_icon, (int(pc[0] - 16), int(pc[1] - 76)))
                gif.text(img, (10, 8), label)
                gif.text(img, (10, 28), "32 damage, 6% crit; parry 1 s, cooldown 3 s, riposte x2.5" +
                         ("  |  SLOW MOTION x%.1f" % KW["SlowMotionSpeed"] if slow_left > 0 else ""),
                         fill=AETHER if slow_left > 0 else (238, 241, 243))
                gif.push(img)
            tick += 1
    gif.save(out)


# ================================================================================================
# Tarmancer
# ================================================================================================
def scene_tarmancer(out, font):
    """The minion draws the Living Tar's own sheet (TarSlimeMinion.SheetPath): its two frames cycled like a vanilla slime's
    (a counter of 1 a tick, 2 while moving, a frame every 8), the squashed frame while it spits; the sheet faces left, so
    it is flipped to face the enemies on the right."""
    tar = frames("Content/Junkyard/NPCs/LivingTar.png", 32, 24, 24, 2)
    slime = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in tar]
    shot = sheet("TarSlimeShot.png", 20, 20, 22, 16)
    W, H, G = 640, 300, 250
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    pc = (170.0, G - 21.0)
    foes = [Foe(collector_sprite(), 560, G, speed=-1.0, name="a", mech=True), Foe(collector_sprite(), 640, G, speed=-0.8, name="b", mech=True)]
    slimes = [{"x": pc[0] - 10, "y": G - 14.0, "vx": 0.0, "vy": 0.0, "pos": k, "cool": 20 + k * 22, "spit": 0, "fc": 0, "f": 0} for k in range(2)]
    globs = []
    for tick in range(int(8.5 * 60)):
        for f in foes:
            f.walk(tick, move=f.x > pc[0] + 90)
        for s in slimes:
            home = pc[0] - (34 + s["pos"] * 28)
            grounded = s["y"] >= G - 14.0
            if grounded:
                s["y"] = G - 14.0
                s["vy"] = 0.0
                s["vx"] *= 0.7
                dx = home - s["x"]
                if abs(dx) > 18:
                    s["vx"] = math.copysign(KM["HopSpeedX"], dx)
                    s["vy"] = -KM["HopSpeedY"]
            s["vy"] = min(s["vy"] + KM["Gravity"], KM["MaxFallSpeed"])
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            if s["y"] > G - 14.0:
                s["y"] = G - 14.0
            s["cool"] -= 1
            if s["spit"] > 0:
                s["spit"] -= 1
            if s["spit"] > 0:
                s["f"], s["fc"] = 0, 0                       # the squash while it spits
            else:
                s["fc"] += 2 if (s["vx"] != 0.0 or s["y"] < G - 14.0) else 1
                if s["fc"] >= 8:
                    s["fc"] = 0
                    s["f"] = (s["f"] + 1) % 2
            target = min((f for f in foes if f.x < pc[0] + KM["TargetRange"]), key=lambda f: abs(f.x - s["x"]), default=None)
            if target is not None and s["cool"] <= 0:
                s["cool"] = KM["ShotInterval"]
                s["spit"] = 8
                mouth = (s["x"] + 10, s["y"] - 9)
                c = centre(target)
                time = min(40.0, math.hypot(c[0] - mouth[0], c[1] - mouth[1]) / KM["ShotSpeed"])
                aim = (c[0] + target.speed * time * 0.8, c[1])
                d = math.hypot(aim[0] - mouth[0], aim[1] - mouth[1]) or 1.0
                globs.append([mouth[0], mouth[1], (aim[0] - mouth[0]) / d * KM["ShotSpeed"], (aim[1] - mouth[1]) / d * KM["ShotSpeed"], target])
        for g in list(globs):
            g[0] += g[2]
            g[1] += g[3]
            f = g[4]
            bx = f.box
            if bx[0] < g[0] < bx[2] and bx[1] < g[1] < bx[3]:
                f.hit(tick, 11, EMBER)
                f.plague(tick, KMS["PlagueTicks"])
                globs.remove(g)
            elif g[0] > W + 20:
                globs.remove(g)
        if tick % TPF == 0:
            img = bg.copy()
            for f in foes:
                f.draw(img, gif, tick)
            img.alpha_composite(player_sprite(), (int(pc[0] - 20), int(pc[1] - 35)))
            for s in slimes:
                img.alpha_composite(slime[s["f"]], (int(s["x"] - 16), int(s["y"] + 14 - 20)))
            for g in globs:
                paste_centre(img, shot[heading(g[2], g[3])], (g[0], g[1]))
            gif.text(img, (10, 8), "Tarmancer: Living Tar slimes (1 slot each), 11 damage every %d ticks (the Imp's rate)" % KM["ShotInterval"])
            gif.text(img, (10, 28), "each glob: Tar Plague 2 s = %d every 0.5 s (brown numbers), half speed" % KP["TickDamage"])
            gif.push(img)
    gif.save(out)


# ================================================================================================
# Tar Bone Staff
# ================================================================================================
def scene_staff(out, font):
    bolt = sheet("TyrantSkullBolt.png", 32, 22, 24, 3)
    blast = sheet("TyrantSkullBlast.png", 80, 80, 82, 6)
    W, H, G = 640, 320, 270
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    pc = (80.0, G - 21.0)
    fly = frames("Content/Junkyard/NPCs/RustCollector.png", 40, 40, 40, 11)[9]
    foes = [Foe(collector_sprite(), 440, G, name="a"), Foe(collector_sprite(), 486, G, name="b"), Foe(fly, 456, 0, name="c")]
    foes[2].y = G - 130
    foes[2].ground = 10 ** 6
    skulls = []
    blasts = []
    for tick in range(int(7.5 * 60)):
        if tick % KB["UseTime"] == 0 and tick < 4 * 60:
            aim = (math.cos(math.radians(-25 + (tick // KB["UseTime"]) % 3 * 18)), math.sin(math.radians(-25 + (tick // KB["UseTime"]) % 3 * 18)))
            skulls.append({"x": pc[0] + aim[0] * 34, "y": pc[1] - 10 + aim[1] * 34, "vx": aim[0] * KB["SkullSpeed"], "vy": aim[1] * KB["SkullSpeed"],
                           "target": None, "t": 0})
        for s in list(skulls):
            s["t"] += 1
            if s["target"] is None:
                best, found = KSK["AcquireRange"], None
                for f in foes:
                    c = centre(f)
                    d = abs(s["x"] - c[0]) + abs(s["y"] - c[1])
                    if d < best:
                        best, found = d, f
                s["target"] = found
            if s["target"] is not None:
                c = centre(s["target"])
                dx, dy = c[0] - s["x"], c[1] - s["y"]
                if abs(dx) + abs(dy) < KSK["KeepRange"]:
                    d = math.hypot(dx, dy) or 1.0
                    n = KSK["Steering"]
                    s["vx"] = (s["vx"] * (n - 1) + dx / d * KB["SkullSpeed"]) / n
                    s["vy"] = (s["vy"] * (n - 1) + dy / d * KB["SkullSpeed"]) / n
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            for f in foes:
                bx = f.box
                if bx[0] - 10 < s["x"] < bx[2] + 10 and bx[1] - 10 < s["y"] < bx[3] + 10:
                    f.hit(tick, 33, AETHER)
                    for o in foes:
                        if o is f:
                            continue
                        oc = centre(o)
                        nx = min(max(s["x"], o.box[0]), o.box[2])
                        ny = min(max(s["y"], o.box[1]), o.box[3])
                        if (nx - s["x"]) ** 2 + (ny - s["y"]) ** 2 <= (KSK["BlastDiameter"] / 2) ** 2:
                            o.hit(tick + 1, 33, EMBER)
                    blasts.append((s["x"], s["y"], tick))
                    skulls.remove(s)
                    break
        if tick % TPF == 0:
            img = bg.copy()
            d = ImageDraw.Draw(img)
            for f in foes:
                f.draw(img, gif, tick)
            img.alpha_composite(player_sprite(), (int(pc[0] - 20), int(pc[1] - 35)))
            for s in skulls:
                k = s["t"] // 5 % 3
                spr = bolt[k] if s["vx"] >= 0 else bolt[k].transpose(Image.FLIP_LEFT_RIGHT)
                ang = math.atan2(s["vy"], s["vx"]) if s["vx"] >= 0 else math.atan2(-s["vy"], -s["vx"])
                paste_centre(img, rotated(spr, ang, False), (s["x"], s["y"]))
            for (x, y, t0) in blasts:
                k = (tick - t0) // KSK["BlastFrameTicks"]
                if 0 <= k < KSK["BlastFrames"]:
                    glow_over(img, blast[k], 1.0, (x - 40, y - 40))
                    r = KSK["BlastDiameter"] / 2
                    d.ellipse([x - r, y - r, x + r, y + r], outline=AETHER)
            gif.text(img, (10, 8), "Tar Bone Staff: a slow homing skull (3.5 px/tick, the Book of Skulls' homing)")
            gif.text(img, (10, 28), "33 on the bite, then a 5-tile burst (circle) hits the others for 33; 19 mana")
            gif.push(img)
    gif.save(out)


# ================================================================================================
# Tar-Shower
# ================================================================================================
def scene_shower(out, font):
    gun = load(D + "TarShower.png")
    spray = sheet("TarSpray.png", 24, 24, 26, KSP["Frames"])
    ball = sheet("TarShowerCharge.png", 32, 32, 34, KCH["Stages"] + 1)
    big = sheet("TarShowerBigGlob.png", 32, 32, 34, 16)
    stain = sheet("TarStain.png", 96, 12, 14, 4)
    W, H, G = 680, 300, 250
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    pc = (90.0, G - 21.0)
    muzzle = (pc[0] + 6 + KS["MuzzleDistance"], pc[1] - 4)
    foes = [Foe(collector_sprite(), 360, G, speed=-0.9, name="a", mech=True), Foe(collector_sprite(), 410, G, speed=-0.7, name="b", mech=True)]
    third = Foe(living_tar(), 660, G, speed=-1.0, name="c")
    reach, v = 0.0, KS["SpraySpeed"]                         # the spray's reach: speed x drag over its lifetime
    for _ in range(KSP["Lifetime"]):
        v *= KSP["Drag"]
        reach += v
    old_reach = reach * 7.0 / KS["SpraySpeed"]               # at the old 7 px/tick (before 2026-11-03)
    bursts = []
    glob = None
    stain_at = None
    charge = 0
    spray_ticks = int(2.6 * 60)
    charge_start = spray_ticks + 20
    release = charge_start + KS["MaxChargeTicks"] + 10
    for tick in range(int(9.6 * 60)):
        for f in foes:
            f.walk(tick, move=f.x > pc[0] + 60)
        third.walk(tick, move=tick > release)
        if tick < spray_ticks and tick % KS["UseTime"] == 0:
            k = tick // KS["UseTime"]
            a = math.radians(4) * ((k * 7) % 5 - 2) / 2.0
            v = KS["SpraySpeed"] * (0.95 + 0.05 * ((k * 3) % 3))
            bursts.append([muzzle[0], muzzle[1], math.cos(a) * v, math.sin(a) * v, 0, set()])
        for b in list(bursts):
            b[2] *= KSP["Drag"]
            b[3] = b[3] * KSP["Drag"] + KSP["Gravity"]
            b[0] += b[2]
            b[1] += b[3]
            b[4] += 1
            size = (12, 16, 20, 24, 28)[min(4, b[4] * KSP["Frames"] // KSP["Lifetime"])]
            for f in foes:
                bx = f.box
                if f.name not in b[5] and len(b[5]) < 3 and bx[0] - size / 2 < b[0] < bx[2] + size / 2 and bx[1] - size / 2 < b[1] < bx[3] + size / 2:
                    b[5].add(f.name)
                    f.hit(tick, 8, EMBER)
                    f.plague(tick, KSP["PlagueTicks"])
            if b[4] >= KSP["Lifetime"]:
                bursts.remove(b)
        if charge_start <= tick < release:
            charge = min(KS["MaxChargeTicks"], tick - charge_start)
        if tick == release:
            glob = [muzzle[0] + 8, muzzle[1], 10.0 * math.cos(math.radians(-20)), 10.0 * math.sin(math.radians(-20)), set()]
        if glob is not None:
            glob[3] = min(glob[3] + KBG["Gravity"], 14.0)
            glob[0] += glob[2]
            glob[1] += glob[3]
            for f in foes:
                bx = f.box
                if f.name not in glob[4] and bx[0] - 11 < glob[0] < bx[2] + 11 and bx[1] - 11 < glob[1] < bx[3] + 11:
                    glob[4].add(f.name)
                    f.hit(tick, int(8 * KS["MaxChargeMultiplier"]), AETHER)
                    f.plague(tick, KBG["PlagueTicks"])
            if glob[1] >= G - 11:
                stain_at = (glob[0], G, tick)
                glob = None
        if stain_at is not None and tick - stain_at[2] < KST["Lifetime"]:
            sx = stain_at[0]
            for f in foes + [third]:
                if abs(centre(f)[0] - sx) < KST["HitboxWidth"] / 2 + f.sprite.width / 2 and (tick - stain_at[2]) % KST["CheckInterval"] == 0:
                    if f.plague_until - tick < KST["RefreshBelow"]:
                        f.plague(tick, KST["PlagueTicks"])
        if tick % TPF == 0:
            img = bg.copy()
            if stain_at is not None and tick - stain_at[2] < KST["Lifetime"]:
                k = (tick - stain_at[2]) // KST["TicksPerFrame"] % 4
                img.alpha_composite(stain[k], (int(stain_at[0] - 48), G - 12 + 2))
            for f in foes + [third]:
                f.draw(img, gif, tick)
            if tick < spray_ticks + 20:                      # the reach, now and before
                d = ImageDraw.Draw(img)
                for r_, col, lab in ((old_reach, (195, 200, 205), "old ~%d tiles" % round(old_reach / 16)), (reach, AETHER, "~%d tiles" % round(reach / 16))):
                    x = muzzle[0] + r_
                    d.line([muzzle[0], G + 14, x, G + 14], fill=col + (255,), width=1)
                    d.line([x, G + 8, x, G + 20], fill=col + (255,), width=2)
                    gif.text(img, (int(x) - 40, G + 22 if col == AETHER else G + 32), lab, fill=col)
            img.alpha_composite(player_sprite(), (int(pc[0] - 20), int(pc[1] - 35)))
            img.alpha_composite(gun, (int(pc[0] + 6 - 6), int(pc[1] - 4 - gun.height / 2)))
            for b in bursts:
                k = min(KSP["Frames"] - 1, b[4] * KSP["Frames"] // KSP["Lifetime"])
                paste_centre(img, spray[k], (b[0], b[1]))
            if charge_start <= tick < release:
                full = charge >= KS["MaxChargeTicks"]
                k = KCH["Stages"] if full else min(KCH["Stages"] - 1, int(charge / KS["MaxChargeTicks"] * KCH["Stages"]))
                paste_centre(img, ball[k], (muzzle[0] + 8, muzzle[1] + (tick // 4 % 2 if full else 0)))
            if glob is not None:
                paste_centre(img, big[heading(glob[2], glob[3])], (glob[0], glob[1]))
            if tick < spray_ticks + 20:
                title = "Tar-Shower: a mid-range tar spray (gel ammo), ~%d tiles (4 more since 2026-11-03), 8 a burst" % round(reach / 16)
                sub = "each burst: Tar Plague 2 s (%d every 0.5 s, brown), half speed; through 3 enemies" % KP["TickDamage"]
            elif tick < release:
                title = "Hold right click: the ball swells, x%.2f damage (%.1f / %.1f s)" % (1 + 2 * charge / KS["MaxChargeTicks"], charge / 60, KS["MaxChargeTicks"] / 60)
                sub = "full at 2.5 s: up to 300% of the weapon damage"
            else:
                title = "Full charge: a big glob through every enemy (24 = x3), a 6-tile stain"
                sub = "the stain plagues every enemy that touches it for 5 s"
            gif.text(img, (10, 8), title)
            gif.text(img, (10, 28), sub)
            gif.push(img)
    gif.save(out)


# ================================================================================================
# Tar Whip (2026-11-03) and the Tyrant set's bonus
# ================================================================================================
KWH = consts(D + "TarWhip.cs", D + "TarWhipProjectile.cs", D + "TarWhipDebuff.cs")
KTY = consts("Content/Bosses/TarTyrant/Armor/TyrantSkull.cs")


def rot_about(p, c, a):
    """Vector2.RotatedBy(a, c): x' = cx + dx cos - dy sin, y' = cy + dx sin + dy cos (screen space, y down)."""
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


def whip_points(ai0, time_to_fly, vel, arm, sprite_dir, segments, range_mult, use_animation):
    """Projectile.FillWhipControlPoints, line for line (decompiled 1.4.4): ai0 updates into the lash of time_to_fly
    (itemAnimationMax x 2 updates a tick), the shoot velocity, the arm position."""
    num = ai0 / time_to_fly
    num2, num3 = 0.5, 1.5
    num4 = math.pi * 10.0 * (1.0 - num * num3) * (-sprite_dir) / segments
    num5 = num * num3
    num6 = 0.0
    if num5 > 1.0:
        num6 = (num5 - 1.0) / num2
        num5 = 1.0 + (0.0 - 1.0) * num6
    num7 = use_animation * 2 * num * 1.0
    num8 = math.hypot(*vel) * num7 * num5 * range_mult / segments
    val = val2 = val3 = arm
    num10, num11, num12 = -math.pi / 2, math.pi / 2 + math.pi / 2 * sprite_dir, math.pi / 2
    rot = math.atan2(vel[1], vel[0]) + math.pi / 2
    pts = [arm]
    for i in range(segments):
        num14 = num4 * (i / segments)
        val4 = (val[0] + math.cos(num10) * num8, val[1] + math.sin(num10) * num8)
        val5 = (val3[0] + math.cos(num12) * num8 * 2, val3[1] + math.sin(num12) * num8 * 2)
        val6 = (val2[0] + math.cos(num11) * num8 * 2, val2[1] + math.sin(num11) * num8 * 2)
        num16 = 1.0 - (1.0 - num5) ** 2
        t7 = num16 * 0.9 + 0.1
        val7 = (val5[0] + (val4[0] - val5[0]) * t7, val5[1] + (val4[1] - val5[1]) * t7)
        t8 = num16 * 0.7 + 0.3
        val8 = (val6[0] + (val7[0] - val6[0]) * t8, val6[1] + (val7[1] - val6[1]) * t8)
        sp = (arm[0] + (val8[0] - arm[0]), arm[1] + (val8[1] - arm[1]) * num3)
        pts.append(rot_about(sp, arm, rot + 4.712389 * num6 * num6 * sprite_dir))
        num10 += num14
        num11 += num14
        num12 += num14
        val, val3, val2 = val4, val5, val6
    return pts


def draw_whip(img, sheet_img, pts, sprite_dir):
    """TarWhipProjectile.PreDraw: the tar cord (a 2 px line per gap), then the handle, a vertebra every other joint and
    the fang, each turned to point at the next joint (as every vanilla whip's segments do)."""
    d = ImageDraw.Draw(img)
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=(47, 27, 20, 255), width=2)
    frames_ = {"handle": (0, 24), "tip": (72, 22)}
    for i in range(len(pts) - 1):
        if i == 0:
            y0, hgt = frames_["handle"]
        elif i == len(pts) - 2:
            y0, hgt = frames_["tip"]
        elif i % 2 == 1:
            continue
        else:
            y0, hgt = 24 + (i // 2 % 3) * 16, 16
        seg = sheet_img.crop((0, y0, 14, y0 + hgt))
        if sprite_dir > 0:
            seg = seg.transpose(Image.FLIP_LEFT_RIGHT)
        a, b = pts[i], pts[i + 1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0]) - math.pi / 2
        pad = Image.new("RGBA", (64, 64))
        pad.alpha_composite(seg, (32 - KWH["JointX"], 32 - KWH["JointY"]))      # the joint at the pad's centre
        r = pad.rotate(-math.degrees(ang), resample=Image.NEAREST)
        img.alpha_composite(r, (int(a[0] - 32), int(a[1] - 32)))


def scene_whip(out, font):
    """Lashes at three walkers: 29 damage, -10% for each further enemy in one lash, the tag (+7 for minions), 2 s of Tar
    Plague a lash. Then the same in the Tyrant set: whips 25% faster (24 ticks a lash instead of 30) and the plague 1.5 s
    longer (3.5 s); the timers over the enemies show it."""
    import tartyrant_sim as tts
    sheet_img = load(D + "TarWhipProjectile.png")
    W, H, G = 700, 300, 250
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    pc = (150.0, G - 21.0)
    arm = (pc[0] + 6, pc[1] - 8)
    plain, armored = player_sprite(), tts.tyrant_player()
    foes = [Foe(collector_sprite(), 300 + 46 * k, G, speed=0.0, name=str(k), mech=True) for k in range(3)]
    use = 30                                                 # DefaultToWhip's animationTotalTime (decompiled Item.DefaultToWhip)
    plan = [("plain", 3, use), ("set", 4, int(round(use / (1 + KTY["WhipSpeed"] / 100.0))))]
    tick = 0
    for mode, lashes, anim in plan:
        bonus = KTY["PlagueBonusTicks"] if mode == "set" else 0
        for f in foes:
            f.plague_until = -1
        for lash in range(lashes):
            fly = anim * 2                                   # updates: itemAnimationMax x MaxUpdates (extraUpdates 1)
            hit = set()
            dmg = KWH["Damage"]
            for t in range(anim + (14 if lash == lashes - 1 else 0)):
                for upd in range(2):
                    ai0 = min(fly, t * 2 + upd + 1)
                    pts = whip_points(ai0, fly, (KWH["ShootSpeed"], 0.0), arm, 1, KWH["Segments"], KWH["RangeMultiplier"], use) if t < anim else None
                    if pts:
                        for f in foes:
                            if f.name in hit:
                                continue
                            bx = f.box
                            if any(bx[0] - 9 < p[0] < bx[2] + 9 and bx[1] - 9 < p[1] < bx[3] + 9 for p in pts):
                                hit.add(f.name)
                                f.hit(tick, dmg, EMBER)
                                f.plague(tick, KWH["PlagueTicks"] + bonus)
                                dmg = int(dmg * KWH["MultihitFactor"])
                for f in foes:
                    f.walk(tick, move=False)
                if tick % TPF == 0:
                    img = bg.copy()
                    d = ImageDraw.Draw(img)
                    for f in foes:
                        f.draw(img, gif, tick)
                        left = max(0, f.plague_until - tick)
                        if left:
                            bx = f.box
                            d.rectangle([bx[0], bx[1] - 8, bx[0] + 40 * left / (KWH["PlagueTicks"] + KTY["PlagueBonusTicks"]), bx[1] - 5], fill=PLAGUE + (255,))
                            gif.text(img, (int(bx[0]), int(bx[1]) - 26), "%.1f s" % (left / 60.0), fill=PLAGUE)
                    spr = armored if mode == "set" else plain
                    img.alpha_composite(spr, (int(pc[0] - spr.width / 2), int(G - spr.height + (4 if mode == "set" else 0))) if mode == "set"
                                        else (int(pc[0] - 20), int(pc[1] - 35)))
                    if pts:
                        draw_whip(img, sheet_img, pts, 1)
                    if mode == "plain":
                        gif.text(img, (10, 8), "Tar Whip: %d damage (-10%% per extra enemy), +%d tag damage for minions, %d-tick lash" % (
                            KWH["Damage"], KWH["TagDamage"], anim))
                        gif.text(img, (10, 28), "every lash: Tar Plague %.1f s (%d every 0.5 s, brown), half speed" % (KWH["PlagueTicks"] / 60, KP["TickDamage"]))
                    else:
                        gif.text(img, (10, 8), "In the Tyrant set: whips +%d%% speed (%d-tick lash), the plague +%.1f s (%.1f s)" % (
                            KTY["WhipSpeed"], anim, KTY["PlagueBonusTicks"] / 60, (KWH["PlagueTicks"] + KTY["PlagueBonusTicks"]) / 60), fill=AETHER)
                        gif.text(img, (10, 28), "Tyrant set: +15% / +1 minion +5% / +15% summon damage, 17 defense")
                    gif.push(img)
                tick += 1
    gif.save(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--date", default="2026-11-03")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    only = set(args.only.split(",")) if args.only else None
    p = lambda name: os.path.join(args.out, args.date + "_" + name)   # noqa: E731
    jobs = [("sprites", lambda: sprites_png(p("weapons-tar-sprites.png"), args.font)),
            ("wrench", lambda: scene_wrench(p("weapon-metal-wrench.gif"), args.font)),
            ("tarmancer", lambda: scene_tarmancer(p("weapon-tarmancer.gif"), args.font)),
            ("staff", lambda: scene_staff(p("weapon-tar-bone-staff.gif"), args.font)),
            ("shower", lambda: scene_shower(p("weapon-tar-shower.gif"), args.font)),
            ("whip", lambda: scene_whip(p("weapon-tar-whip.gif"), args.font))]
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
