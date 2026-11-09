"""D5 proofs for the second request of 2026-11-06, built from the real sprite sheets and the constants parsed out of the C#
files, replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_06b_sim.py --out docs/media [--only defender|golem|lantern]

Writes:
    2026-11-09_coghaven-imperial-defender.gif   the Imperial Defender marches at a gunner; once every 8 s he plants his
                                                feet and raises the dadao for 2 s: shots from the front are knocked away
                                                ("Parried!", sparks off the blade), until the gunner jumps over him and
                                                shoots his back (full damage); then he lowers the blade and turns.
    2026-11-09_coghaven-jade-golem.gif          the Jade Golem walks, stops and charges for 1.5 s: his arm swings up and
                                                follows the player climbing a ledge (one 15-degree frame every 3 ticks),
                                                the charge gathers in his fist, a faint dotted line shows the aim; it
                                                locks for the last 0.3 s (the line blinks), then the ray fires.
    2026-11-09_boss-cursed-conductor-lantern-weapon.gif   the Cursed Lantern held out in the hand toward the aim, like
                                                vanilla's spell tomes (useStyle Shoot: the item turned to the aim at the
                                                hand, as vanilla draws it), slow souls leaving its glass; those within 10
                                                tiles of an enemy (the ring drawn round the first one) home in and burst on
                                                it, the rest slow down and float where they were let go.

Leaves out: lighting, the planes' parallax, vanilla's player physics (scripted paths), defense on the player, netcode (the
sim is the server). Numbers are Expert's.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, player_sprite, TPF  # noqa: E402

COG = "Content/Coghaven/"
KD = consts(COG + "NPCs/ImperialDefender.cs", COG + "NPCs/ImperialDefenderRigData.cs")
KG = consts(COG + "NPCs/JadeGolem.cs", COG + "NPCs/JadeGolemRigData.cs", COG + "Projectiles/JadeRay.cs")
LAN = "Content/Bosses/CursedConductor/Weapons/"
KL = consts(LAN + "CursedLantern.cs", LAN + "SoulFire.cs")
EMBER, STEAM, JADE, AETHER, HURT = (255, 199, 90), (238, 241, 243), (118, 220, 162), (198, 189, 255), (236, 113, 40)


def int_array(path, name):
    m = re.search(name + r"\s*=\s*\{([^}]*)\}", open(path, encoding="utf-8").read())
    return [int(v) for v in m.group(1).split(",")]


MUZZLE_X = int_array(COG + "NPCs/JadeGolemRigData.cs", "MuzzleX")
MUZZLE_Y = int_array(COG + "NPCs/JadeGolemRigData.cs", "MuzzleY")


class Planes:
    """A grid enemy's far, middle, near and glow cells (in k["Columns"] columns), drawn at the origin and mirrored when it
    faces right, like DepthLayers.DrawWalker (parallax left out)."""

    def __init__(self, base, k):
        self.k = k
        self.sheets = [load(base + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]

    def draw(self, img, frame, anchor, face_right, glow=1.0):
        cw, ch, ox, oy = self.k["CellWidth"], self.k["CellHeight"], self.k["OriginX"], self.k["OriginY"]
        cols = int(self.k.get("Columns", 1))
        x0, y0 = frame % cols * (cw + 2), frame // cols * (ch + 2)
        for i, sheet in enumerate(self.sheets):
            cell = sheet.crop((x0, y0, x0 + cw, y0 + ch))
            if i == 3 and glow < 1.0:
                cell.putalpha(cell.getchannel("A").point(lambda a: int(a * glow)))
            if face_right:
                cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
                img.alpha_composite(cell, (int(round(anchor[0] - (cw - ox))), int(round(anchor[1] - oy))))
            else:
                img.alpha_composite(cell, (int(round(anchor[0] - ox)), int(round(anchor[1] - oy))))


def coghaven_backdrop(w, h, ground, ledges=()):
    """The island's sky over Palace Flagstone (the real tile's top and middle frames), with optional stone ledges."""
    img = backdrop(w, h, ground, sky=((170, 206, 236), (120, 160, 208)), dirt=(152, 132, 104))
    tiles = load(COG + "Tiles/PalaceFlagstoneTile.png")
    top, mid = tiles.crop((18, 0, 34, 16)), tiles.crop((18, 18, 34, 34))
    for (x0, x1, y) in [(0, w, ground)] + list(ledges):
        for x in range(x0, x1, 16):
            img.alpha_composite(top, (x, y))
            for yy in range(y + 16, h, 16):
                img.alpha_composite(mid, (x, yy))
    return img


def numbers(gif, img, pops, tick):
    for (t0, x, y, s, col) in pops:
        if 0 <= tick - t0 < 45:
            gif.text(img, (int(x), int(y - (tick - t0) // 2)), s, fill=col, font=gif.big)


def note(gif, img, notes, tick):
    live = [s for (t0, s) in notes if t0 <= tick]
    if live:
        gif.text(img, (10, 8), live[-1], fill=STEAM)


class Sparks:
    def __init__(self):
        self.items = []

    def burst(self, x, y, direction, n=6, col=EMBER):
        for _ in range(n):
            self.items.append([x, y, direction * random.uniform(1.5, 4.0), random.uniform(-3.0, 0.5), 16, col])

    def step_draw(self, d):
        for s in self.items:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.25
            s[4] -= 1
            d.rectangle([s[0] - 1, s[1] - 1, s[0] + 1, s[1] + 1], fill=s[5] + (255,))
        self.items = [s for s in self.items if s[4] > 0]


# ================================================================================================
# The Imperial Defender
# ================================================================================================
def scene_defender(out, font):
    W, H, G = 640, 230, 200
    bg = coghaven_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.5)
    knight = Planes(COG + "NPCs/ImperialDefender", KD)
    guard_in, guard_out = KD["GuardInFrames"] * KD["FrameTicks"], KD["GuardOutFrames"] * KD["FrameTicks"]
    march_ticks = KD["ParryEvery"] - guard_in - KD["ParryTicks"] - guard_out
    kx, face = 470.0, -1
    state, timer, marched, counter = "march", 0, march_ticks - 60, 0.0
    px, py, p_face = 180.0, float(G), 1
    shots, pops, sparks = [], [], Sparks()
    notes = [(0, "Imperial Defender: marches, heavy contact (%d)" % KD["ContactDamage"]),
             (60, "every 8 s: the guard, held %d ticks (2 s)" % KD["ParryTicks"]),
             (95, "hits from the front: parried (1 damage, shots destroyed)"),
             (150, "his feet stay planted: hits from behind land in full")]
    jump0, jump_len = 120, 46
    for tick in range(330):
        # --- the gunner (scripted): shoots, then jumps over him and shoots his back ---------------------------------
        if jump0 <= tick < jump0 + jump_len:
            u = (tick - jump0) / jump_len
            px = 240.0 + (540.0 - 240.0) * u
            py = G - 4 * 92 * u * (1 - u)
            p_face = 1
        elif tick >= jump0 + jump_len:
            px, py, p_face = 540.0, float(G), -1
        elif tick >= 95:
            px = min(240.0, px + 3.0)
        fire_every = 16
        if tick % fire_every == 0 and py >= G - 1 and not (jump0 <= tick < jump0 + jump_len):
            shots.append([px + 16 * p_face, G - 34, 9.0 * p_face])
        # --- the Defender --------------------------------------------------------------------------------------------
        timer += 1
        if state == "march":
            marched += 1
            want = 1 if px > kx else -1
            vx = want * KD["MarchSpeed"]
            if abs(px - kx) > 40:
                kx += vx
                counter = (counter + abs(vx)) % (KD["WalkStep"] * KD["WalkFrames"])
            face = want
            frame = KD["Walk"] + int(counter / KD["WalkStep"]) % int(KD["WalkFrames"])
            if marched >= march_ticks:
                state, timer, marched = "in", 0, 0
        elif state == "in":
            frame = KD["GuardIn"] + min(KD["GuardInFrames"] - 1, timer // KD["FrameTicks"])
            if timer >= guard_in:
                state, timer = "guard", 0
        elif state == "guard":
            frame = KD["Guard"] + (timer // 10) % KD["GuardFrames"]
            if timer >= KD["ParryTicks"]:
                state, timer = "out", 0
        else:
            frame = KD["GuardOut"] + min(KD["GuardOutFrames"] - 1, timer // KD["FrameTicks"])
            if timer >= guard_out:
                state, timer = "march", 0
        box = (kx - KD["Width"] / 2 if "Width" in KD else kx - 14, G - 58, kx + 14, G)
        for s in shots:
            s[0] += s[2]
            if box[0] <= s[0] <= box[2] and box[1] <= s[1] <= box[3] and s[2] != 0:
                from_front = (s[0] - s[2] - kx) * face >= 0
                if state == "guard" and from_front:
                    blade = (kx + KD["GuardBladeX"] * -face, G + KD["GuardBladeY"])
                    sparks.burst(blade[0], blade[1], face)
                    pops.append((tick, kx - 34, G - 92, "Parried!", EMBER))
                else:
                    pops.append((tick, kx - 10, G - 86, "20", HURT))     # 30 - defense 20 / 2
                s[2] = 0
        shots = [s for s in shots if s[2] != 0 and 0 <= s[0] <= W]
        # --- draw ------------------------------------------------------------------------------------------------------
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        knight.draw(img, frame, (kx, G), face == 1)
        img.alpha_composite(player_sprite(flip=p_face < 0), (int(px - 20), int(py - 56)))
        for s in shots:
            d.line([s[0] - 4, s[1], s[0] + 4, s[1]], fill=(255, 231, 160, 255), width=2)
        sparks.step_draw(d)
        gif.text(img, (10, H - 22), "state: %s" % {"march": "march", "in": "guard up", "guard": "GUARD (parry)", "out": "guard down"}[state],
                 fill=EMBER if state == "guard" else STEAM)
        note(gif, img, notes, tick)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Jade Golem
# ================================================================================================
def seg_box_dist(a, b, box):
    """Distance from the segment a-b to the box (0 if they touch); sampled every 2 px (a proof, not the game's test)."""
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2))
    best = 1e9
    for i in range(n + 1):
        x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
        dx = max(box[0] - x, 0, x - box[2])
        dy = max(box[1] - y, 0, y - box[3])
        best = min(best, math.hypot(dx, dy))
    return best


def scene_golem(out, font):
    W, H, G = 720, 350, 320
    ledge = (300, 412, G - 144)                               # a stone ledge nine tiles up
    bg = coghaven_backdrop(W, H, G, ledges=[ledge])
    gif = Gif(font, (W, H), scale=1.25)
    golem = Planes(COG + "NPCs/JadeGolem", KG)
    nodes = load(COG + "Projectiles/JadeRay.png")
    orbs = load(COG + "Projectiles/JadeRay_Orb.png")
    node0 = nodes.crop((0, 0, 16, 16))
    faint, bright = node0.copy(), node0.copy()
    faint.putalpha(faint.getchannel("A").point(lambda a: int(a * 0.25)))
    bright.putalpha(bright.getchannel("A").point(lambda a: int(a * 0.75)))
    aim_frames, hanging = int(KG["AimFrames"]), int(KG["AimFrames"]) - 1
    gx, face = 600.0 + 120 * KG["WalkSpeed"], -1
    lead = 120                                                # two seconds of the walk first (the Jaeger's planted feet)
    state, timer, walked, counter, arm, locked = "walk", 0, KG["WalkTicks"] - 40 - lead, 0.0, hanging, 0.0
    pops, ray = [], None
    notes = [(0, "Jade Golem: the Jaeger's walk, each foot planted 8 frames (%d px/frame = the root motion)" % KG["WalkStep"]),
             (lead - 30, "slow, tanky (%d life, %d def), heavy contact (%d)" % (KG["Life"], KG["Defense"], KG["ContactDamage"])),
             (lead + 40, "every 5 s: stops, charges %d ticks (1.5 s); the arm follows the player %d ticks late" % (KG["ChargeTicks"], KG["AimDelayTicks"])),
             (lead + 40 + KG["TrackTicks"], "the aim locks where the player was 0.75 s before (the ring): keep moving"),
             (lead + 40 + KG["ChargeTicks"], "the ray: %d damage, up to 50 tiles" % KG["RayDamage"])]

    def player_at(tick):
        """Scripted: backs away from the golem, climbs the ledge, jumps on it (the arm follows), lands and stands."""
        top = float(ledge[2])
        tick -= lead
        if tick < 0:
            return 520.0, float(G)
        if tick < 50:
            return 520.0 - tick * 2.2, float(G)
        if tick < 74:
            u = (tick - 50) / 24
            return 410.0 - 30 * u, G - (G - top) * min(1.0, u * 1.4) - 34 * math.sin(math.pi * u)
        if 86 <= tick < 110:
            u = (tick - 86) / 24
            return 380.0, top - 4 * 80 * u * (1 - u)
        return 380.0, top

    def elevation(a, b):
        return math.atan2(b[1] - a[1], abs(b[0] - a[0]))

    def frame_for(elev):
        return max(0, min(aim_frames - 1, round((math.degrees(elev) - KG["AimMinDegrees"]) / KG["AimStepDegrees"])))

    def muzzle(k):
        return (gx + MUZZLE_X[k] * -face, G + MUZZLE_Y[k])

    def solid(x, y):
        return y >= G or (ledge[0] <= x < ledge[1] and y >= ledge[2])

    def ray_length(a, d):
        for i in range(1, int(KG["MaxLength"] / 8) + 1):
            if solid(a[0] + d[0] * i * 8, a[1] + d[1] * i * 8):
                return i * 8.0
        return KG["MaxLength"]

    history = []                                              # the mark's centre, a point a tick (JadeGolem.RecordMark)

    for tick in range(260 + lead):
        px, py = player_at(tick)
        pc = (px, py - 21)
        history.append(pc)
        mark = history[max(0, len(history) - 1 - KG["AimDelayTicks"])]   # where the player was 0.75 s ago (DelayedMark)
        timer += 1
        if state == "walk":
            arm = hanging
            walked += 1
            gx -= KG["WalkSpeed"]
            counter = (counter + KG["WalkSpeed"]) % (KG["WalkStep"] * KG["WalkFrames"])
            frame = KG["Walk"] + int(counter / KG["WalkStep"]) % int(KG["WalkFrames"])
            if walked >= KG["WalkTicks"]:
                state, timer, walked = "charge", 0, 0
        elif state == "charge":
            shoulder = (gx + KG["ShoulderX"] * -face, G + KG["ShoulderY"])
            want = frame_for(elevation(shoulder, mark))
            if timer % KG["AimSweepTicks"] == 0 and arm != want:
                arm += 1 if want > arm else -1
            frame = KG["Aim"] + arm
            if timer >= KG["TrackTicks"]:
                locked = elevation(muzzle(want), mark)
                state, timer = "lock", 0
        elif state == "lock":
            arm = frame_for(locked)
            frame = KG["Aim"] + arm
            if timer >= KG["LockTicks"]:
                a = muzzle(arm)
                d = (face * math.cos(locked), math.sin(locked))
                ray = (tick, a, d, ray_length(a, d))
                box = (px - 10, py - 42, px + 10, py)
                b = (a[0] + d[0] * ray[3], a[1] + d[1] * ray[3])
                if seg_box_dist(a, b, box) <= KG["Radius"]:
                    pops.append((tick, px - 18, py - 80, str(int(KG["RayDamage"])), HURT))
                state, timer = "fire", 0
        elif state == "fire":
            frame = KG["Aim"] + arm
            if timer >= KG["FireTicks"] if "FireTicks" in KG else timer >= KG["Lifetime"]:
                state, timer = "recover", 0
        else:
            if timer % 2 == 0 and arm < hanging:
                arm += 1
            frame = KG["Idle"] if arm >= hanging else KG["Aim"] + arm
            if timer >= KG["RecoverTicks"]:
                state, timer = "walk", 0
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        charging = state in ("charge", "lock")
        glow = 0.7 + 0.3 * min(1.0, (timer if state == "charge" else KG["TrackTicks"] + timer) / KG["ChargeTicks"]) if charging else 0.7
        golem.draw(img, frame, (gx, G), face == 1, glow)
        img.alpha_composite(player_sprite(flip=False), (int(px - 20), int(py - 56)))
        if state in ("charge", "lock", "fire"):
            m = muzzle(arm)
            if state != "fire":
                dirv = (face * math.cos(locked), math.sin(locked)) if state == "lock" else \
                    (face * math.cos(elevation(m, mark)), math.sin(elevation(m, mark)))
                if state == "charge":                         # the delayed point the arm is following (a sim marker)
                    d.ellipse([mark[0] - 7, mark[1] - 7, mark[0] + 7, mark[1] + 7], outline=(118, 220, 162, 200), width=1)
                dot = bright if (state == "lock" and timer % 6 < 3) else faint
                length = ray_length(m, dirv)
                dd = 14.0
                while dd < length:
                    img.alpha_composite(dot, (int(m[0] + dirv[0] * dd - 8), int(m[1] + dirv[1] * dd - 8)))
                    dd += 14.0
            charge = timer / KG["ChargeTicks"] if state == "charge" else (KG["TrackTicks"] + timer) / KG["ChargeTicks"] if state == "lock" else 1.0
            f = max(0, min(4, int(charge * 5)))
            orb = orbs.crop((0, f * 26, 24, f * 26 + 24))
            if state == "fire":
                orb.putalpha(orb.getchannel("A").point(lambda a, t=timer: int(a * max(0.0, 1 - t / KG["Lifetime"]))))
            img.alpha_composite(orb, (int(m[0] - 12), int(m[1] - 12)))
        if ray and tick - ray[0] < KG["Lifetime"]:
            t0, a, dv, length = ray
            fade = 1 - (tick - t0) / KG["Lifetime"]
            nrm = (-dv[1], dv[0])
            for i in range(int(length / 6) + 1):
                h = (i * 73 + (tick // 3) * 151) & 7
                fr = nodes.crop((0, ((i + tick // 3) % 3) * 18, 16, ((i + tick // 3) % 3) * 18 + 16))
                fr.putalpha(fr.getchannel("A").point(lambda v, f_=fade: int(v * f_)))
                x = a[0] + dv[0] * i * 6 + nrm[0] * (h % 5 - 2) - 8
                y = a[1] + dv[1] * i * 6 + nrm[1] * (h % 5 - 2) - 8
                img.alpha_composite(fr, (int(x), int(y)))
        label = {"walk": "walk", "charge": "CHARGE (tracking)", "lock": "LOCKED", "fire": "FIRE", "recover": "recover"}[state]
        gif.text(img, (10, H - 22), "state: %s   arm frame: %d (%+d deg)" % (label, arm, KG["AimMinDegrees"] + arm * KG["AimStepDegrees"]),
                 fill=JADE if state in ("charge", "lock", "fire") else STEAM)
        note(gif, img, notes, tick)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Cursed Lantern
# ================================================================================================
def scene_lantern(out, font):
    W, H, G = 680, 260, 230
    bg = coghaven_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.3)
    soul_sheet, soul_glow = load(LAN + "SoulFire.png"), load(LAN + "SoulFire_Glow.png")
    lantern = load(LAN + "CursedLantern.png")
    knight = Planes(COG + "NPCs/ImperialDefender", KD)
    px = 120.0
    souls, pops, bursts = [], [], Sparks()
    aim = 0.0
    enemy_x, enemy_hp, counter = 640.0, KD["Life"], 0.0
    notes = [(0, "Cursed Lantern: %d damage, %d use time, %d mana; slow souls (%.1f px/tick)" % (KL["Damage"], KL["UseTime"], KL["Mana"], KL["SoulSpeed"])),
             (12, "held out in the hand like a spell tome (2026-11-09), souls leave its glass"),
             (60, "with no enemy within 10 tiles (the ring), a soul coasts, slows and floats"),
             (170, "an enemy inside the ring: the souls home in on it")]
    random.seed(7)
    for tick in range(330):
        if tick < 110 and tick % KL["UseTime"] == 0:
            ang = math.radians(-34 + 11 * (len(souls) % 5))
            aim = ang
            # CursedLantern.Shoot: from the hand's pivot (the player's centre) out GlassReach px along the aim
            souls.append({"x": px + math.cos(ang) * KL["GlassReach"], "y": G - 21 + math.sin(ang) * KL["GlassReach"],
                          "vx": KL["SoulSpeed"] * math.cos(ang), "vy": KL["SoulSpeed"] * math.sin(ang), "age": 0, "alive": True})
        if tick >= 90:
            enemy_x -= KD["MarchSpeed"]
            counter = (counter + KD["MarchSpeed"]) % (KD["WalkStep"] * KD["WalkFrames"])
        ec = (enemy_x, G - 29)
        for s in souls:
            if not s["alive"]:
                continue
            s["age"] += 1
            dx, dy = ec[0] - s["x"], ec[1] - s["y"]
            dist = math.hypot(dx, dy)
            if dist < KL["HomingRange"]:
                wx, wy = dx / dist * KL["ChaseSpeed"], dy / dist * KL["ChaseSpeed"]
                s["vx"] += (wx - s["vx"]) * KL["Turn"]
                s["vy"] += (wy - s["vy"]) * KL["Turn"]
            elif math.hypot(s["vx"], s["vy"]) > KL["DriftSpeed"]:
                s["vx"] *= KL["Slow"]
                s["vy"] *= KL["Slow"]
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            if abs(s["x"] - enemy_x) < 14 and G - 58 < s["y"] < G:
                s["alive"] = False
                dmg = int(KL["Damage"] - KD["Defense"] / 2)
                enemy_hp -= dmg
                pops.append((tick, enemy_x - 10, G - 90, str(dmg), AETHER))
                bursts.burst(s["x"], s["y"], -1, n=8, col=AETHER)
            if s["age"] >= KL["Lifetime"]:
                s["alive"] = False
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        frame = KD["Walk"] + int(counter / KD["WalkStep"]) % int(KD["WalkFrames"])
        knight.draw(img, frame, (enemy_x, G), False)
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        if tick < 110 + KL["UseTime"]:                    # held out toward the aim while in use (vanilla's gun-style draw)
            held = lantern.rotate(-math.degrees(aim), resample=Image.NEAREST, expand=True)
            hx, hy = px + 4 + math.cos(aim) * 12, G - 21 + math.sin(aim) * 12
            img.alpha_composite(held, (int(hx - held.width / 2), int(hy - held.height / 2)))
        first = next((s for s in souls if s["alive"]), None)
        if first:
            r = KL["HomingRange"]
            d.ellipse([first["x"] - r, first["y"] - r, first["x"] + r, first["y"] + r], outline=(198, 189, 255, 140), width=1)
        for s in souls:
            if not s["alive"]:
                continue
            f = (s["age"] // KL["FrameTicks"]) % KL["Frames"]
            cell = (0, f * 30, 20, f * 30 + 28)
            fade = min(1.0, (KL["Lifetime"] - s["age"]) / 30.0)
            bob = (s["age"] // 20) % 2 * 2
            for sheet in (soul_sheet, soul_glow):
                c = sheet.crop(cell)
                if fade < 1.0:
                    c.putalpha(c.getchannel("A").point(lambda a, f_=fade: int(a * f_)))
                img.alpha_composite(c, (int(s["x"] - 10), int(s["y"] - 18 + bob)))
        bursts.step_draw(d)
        note(gif, img, notes, tick)
        numbers(gif, img, pops, tick)
        gif.push(img)
    gif.save(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    random.seed(11)
    jobs = [("defender", lambda: scene_defender(os.path.join(args.out, "2026-11-09_coghaven-imperial-defender.gif"), args.font)),
            ("golem", lambda: scene_golem(os.path.join(args.out, "2026-11-09_coghaven-jade-golem.gif"), args.font)),
            ("lantern", lambda: scene_lantern(os.path.join(args.out, "2026-11-09_boss-cursed-conductor-lantern-weapon.gif"), args.font))]
    for name, job in jobs:
        if args.only in (None, name):
            job()


if __name__ == "__main__":
    main()
