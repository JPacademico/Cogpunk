"""D5 proofs for the second request of 2026-11-10, built from the real sprites and the constants parsed out of the C# files,
replayed tick by tick (60 ticks = 1 s).

    python -P tools/sim/update_2026_11_10b_sim.py --out docs/media [--only firesaw,golem,lantern,cloth,chests]

(2026-11-11: the ruins' replay, the drone's scene and the items sheet are update_2026_11_11_sim.py's now: the ruins were
redesigned, the drone renamed the Delivery Drone with a 5 s scan and 30 life (its scene, scene_drone, stays here and is run
from there), and the ruins' blocks darkened. Their 2026-11-10 proofs were deleted.)

Writes:
    2026-11-10_mechanist-firesaw-phantom-slash.gif   the Firesaw's swings with the phantom slash trail (the crescent over the
                                                arc swept in the last three ticks), plain and on fire; 42 a hit (12% crit),
                                                2 steam a swing, 5 on fire.
    2026-11-10_coghaven-jade-golem-palm.gif     the Jade Golem with open hands: the arm follows the player's afterimage (0.5 s
                                                behind, the reticle) smoothly, the ray leaves the palm along the arm; a
                                                running player outruns it, a standing one is hit; a teleport mid-charge is
                                                swept to, not snapped to. The measured per-tick steps are printed and shown.
    2026-11-10_boss-cursed-conductor-lantern-cap.gif the Cursed Lantern firing into the open: at most 4 souls, the oldest
                                                fading when a fifth comes.
    2026-11-10_oldbrasstown-red-cloth.gif       the Mechanical Bull charges a player wearing the Red Cloth: the touch is
                                                dodged (Ole!, 0.7 s of immunity), a charge during the 12 s recharge hurts,
                                                a charge after it is dodged again.
    (2026-11-12: the chests map was dropped: Coghaven has two chests now, shown by update_2026_11_12_sim.py's
    2026-11-12_coghaven-island-chests.png.)

Leaves out: lighting (the glows are drawn at full strength), vanilla's own art (natural stone, the cave and the water are
flat stand-ins), the planes' parallax, the player's exact physics (update_2026_11_03b_sim's approximation), netcode (the sim
is the server and the owner). Numbers are Expert's.
"""
import argparse
import math
import os
import random
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import Gif, backdrop, consts, load, player_sprite, TPF  # noqa: E402
from update_2026_11_04_sim import town_backdrop, STEAM  # noqa: E402
from update_2026_11_06b_sim import Planes, coghaven_backdrop, numbers, note, Sparks  # noqa: E402
from update_2026_11_03b_sim import Player, overlaps, PLAYER_W, PLAYER_H  # noqa: E402
from update_2026_11_10_sim import swing_angle, posed, hand_at, blade, faded, stone_image, seg_box_dist, ease_out  # noqa: E402
from terrain import load_frames  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
MECH = "Content/Mechanist/Weapons/"
COG = "Content/Coghaven/"
SEC = "Content/Secrets/"
RUIN = SEC + "Ruins/"
WEP = "Content/Bosses/CursedConductor/Weapons/"
TOWN = "Content/OldBrassTown/"
KF = consts(MECH + "Firesaw.cs", MECH + "FiresawLayer.cs")
KG = consts(COG + "NPCs/JadeGolem.cs", COG + "NPCs/JadeGolemRigData.cs", COG + "Projectiles/JadeRay.cs")
KL = consts(WEP + "SoulFire.cs", WEP + "CursedLantern.cs")
KC = consts(TOWN + "Accessories/RedCloth.cs", TOWN + "NPCs/MechanicalBull.cs", TOWN + "NPCs/MechanicalBullRigData.cs")
KD = consts("Content/Scrap/NPCs/DeliveryDrone.cs", "Content/Scrap/NPCs/DeliveryDroneSystem.cs")
KR = consts(SEC + "Generation/FundamentalRuinsPass.cs", SEC + "FundamentalStoneTile.cs")
KF.setdefault("TrailStep", math.radians(24))                  # 24f * MathHelper.Pi / 180f (the parser skips MathHelper)
EMBER, JADE, HIT, HURT, RED = (236, 113, 40), (96, 214, 150), (255, 199, 90), (255, 90, 70), (206, 74, 56)
AETHER = (198, 189, 255)


def font_at(path, size):
    return ImageFont.truetype(path, size)


def additive(img, layer, xy, opacity):
    """Adds an RGBA layer onto img at xy (vanilla's alpha-0 draw colour: light added, never darkened), times opacity."""
    x, y = int(xy[0]), int(xy[1])
    box = (max(0, x), max(0, y), min(img.width, x + layer.width), min(img.height, y + layer.height))
    if box[2] <= box[0] or box[3] <= box[1]:
        return
    part = layer.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
    rgb = Image.new("RGB", part.size, (0, 0, 0))
    rgb.paste(part.convert("RGB"), (0, 0), part.getchannel("A"))
    rgb = rgb.point(lambda v: int(v * opacity))
    base = img.crop(box).convert("RGB")
    out = ImageChops.add(base, rgb).convert("RGBA")
    img.paste(out, box[:2])


def turned(cell, pivot, degrees):
    """A cell turned about its pivot by `degrees` (clockwise on screen), point-sampled; returns it and the pivot's offset."""
    r = int(math.hypot(cell.width, cell.height)) + 4
    pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    pad.alpha_composite(cell, (r - pivot[0], r - pivot[1]))
    return pad.rotate(-degrees, resample=Image.NEAREST), r


# ================================================================================================
# (The Fundamental Ruins' replay of the 2026-11-10b pass and the items sheet went with the redesign of 2026-11-11: the
# new replay is update_2026_11_11_sim.py's; the old code is kept in tools/sim/previous/update_2026_11_10b_sim_2026-11-10.py.)
# ================================================================================================


# ================================================================================================
# The Firesaw: the phantom slash
# ================================================================================================
def scene_firesaw(out, font):
    W, H, G = 780, 344, 262
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.2)
    saw, fire = load(MECH + "FiresawSwing.png"), load(MECH + "FiresawFire.png")
    trails = {False: (load(MECH + "FiresawTrail.png"), 168, 96, 76, 92), True: (load(MECH + "FiresawTrailFire.png"), 226, 128, 102, 124)}
    sparks = Sparks()
    px = 250.0
    centre = (px, G - 21.0)
    use = int(KF["UseTime"])
    near_x, far_x = px + 58, px + 112
    dummies = [{"x": near_x, "burn": -999}, {"x": far_x, "burn": -999}]
    schedule = [(20, False), (20 + use, False), (20 + 2 * use, False), (140, True), (140 + use, True), (140 + 2 * use, True),
                (260, False), (260 + use, False)]
    tank = 55
    steam = tank
    crit_on = {1, 6}                                            # which hits roll a crit in this replay (12%: illustrative)
    pops, notes = [], [(0, "Firesaw: %d a hit, 12%% crit, %d steam a swing; a slight phantom slash trails each swing" % (KF["Damage"], KF["Steam"])),
                       (140, "right click: the blade burns, two tiles more reach, On Fire!, %d steam a swing; the trail burns too" % KF["FireSteam"]),
                       (260, "the trail covers the arc the blade swept in the last %d ticks, bright at the blade, fading at its tail" % KF["TrailTicks"])]
    swing, last_start, up = None, -999, True
    hit_this, history, hits = set(), [], 0
    for tick in range(330):
        for (t0, f) in schedule:
            if tick == t0:
                chained = t0 - last_start <= use + 20
                up = (not up) if chained else False
                last_start = t0
                swing = (t0, up, f)
                hit_this = set()
                steam -= KF["FireSteam"] if f else KF["Steam"]
        angle, done, frame = None, 0.0, 0
        if swing and tick - swing[0] < use:
            age = tick - swing[0]
            done = age / use
            angle = swing_angle(done, swing[1])
            frame = (tick // int(KF["FrameTicks"])) % int(KF["Frames"])
            if KF["HitFrom"] <= done < KF["HitTo"]:
                prev = swing_angle(max(0.0, (age - 1) / use), swing[1])
                for i, dmy in enumerate(dummies):
                    if i in hit_this:
                        continue
                    box = (dmy["x"] - 16, G - 48, dmy["x"] + 16, G)
                    for a_ in (angle, (angle + prev) / 2, prev):
                        a, b, r = blade(centre, a_, swing[2])
                        if seg_box_dist(a, b, box) <= r:
                            hit_this.add(i)
                            crit = hits in crit_on
                            hits += 1
                            dmg = int(KF["Damage"]) * (2 if crit else 1)
                            pops.append((tick, dmy["x"] - 12, G - 92 - 10 * i, ("%d!" % dmg) if crit else str(dmg), (255, 140, 60) if crit else HIT))
                            sparks.burst(dmy["x"], G - 30, 1, 6, EMBER if swing[2] else (183, 191, 202))
                            if swing[2]:
                                dmy["burn"] = tick
                            break
        else:
            swing = None
        history.append(angle)
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        for i, dmy in enumerate(dummies):
            x = dmy["x"]
            d.rectangle([x - 16, G - 48, x + 16, G], fill=(138, 90, 60, 255), outline=(47, 27, 20, 255))
            d.line([x, G, x, G + 6], fill=(91, 54, 38, 255), width=3)
            if tick - dmy["burn"] < KF["OnFireTicks"]:
                for k in range(5):
                    fx = x - 12 + (k * 7 + tick) % 26
                    d.polygon([(fx, G - 6), (fx + 4, G - 18 - (k % 3) * 4), (fx + 8, G - 6)], fill=EMBER + (230,))
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        if angle is not None:
            burning = swing[2]
            if KF["WindEnd"] <= done < KF["OverEnd"]:
                back = history[-1 - int(KF["TrailTicks"])] if len(history) > KF["TrailTicks"] else None
                if back is not None:                            # FiresawLayer.AddTrail
                    now_v = (math.cos(angle), math.sin(angle))
                    back_v = (math.cos(back), math.sin(back))
                    sweep = math.atan2(back_v[0] * now_v[1] - back_v[1] * now_v[0], back_v[0] * now_v[0] + back_v[1] * now_v[1])
                    span = abs(sweep)
                    if span >= KF["TrailMin"]:
                        sheet, fw, fh, pvx, pvy = trails[burning]
                        k = max(1, min(int(KF["TrailFrames"]), int(span / KF["TrailStep"] + 0.5))) - 1
                        cell = sheet.crop((0, k * (fh + 2), fw, k * (fh + 2) + fh))
                        pivot = (pvx, pvy)
                        if sweep < 0:
                            cell = cell.transpose(Image.FLIP_TOP_BOTTOM)
                            pivot = (pvx, fh - pvy)
                        h = hand_at(centre, angle)
                        pv = (h[0] - now_v[0] * KF["ArmReach"], h[1] - now_v[1] * KF["ArmReach"])
                        g, r = turned(cell, pivot, math.degrees(angle))
                        opacity = KF["TrailOpacity"] * max(0.35, min(1.0, span / KF["TrailFull"]))
                        additive(img, g, (pv[0] - r, pv[1] - r), opacity)
                for k, op in ((3, 0.13), (2, 0.28), (1, 0.45)):
                    if len(history) > k and history[-1 - k] is not None and (tick - k - swing[0]) / use >= KF["WindEnd"] - 0.05:
                        g, r = posed(saw, frame, int(KF["Size"]), (int(KF["GripX"]), int(KF["GripY"])), history[-1 - k])
                        h = hand_at(centre, history[-1 - k])
                        img.alpha_composite(faded(g, op), (int(h[0] - r), int(h[1] - r)))
            g, r = posed(saw, frame, int(KF["Size"]), (int(KF["GripX"]), int(KF["GripY"])), angle)
            h = hand_at(centre, angle)
            img.alpha_composite(g, (int(h[0] - r), int(h[1] - r)))
            if burning:
                g, r = posed(fire, frame, int(KF["FireSize"]), (int(KF["GripX"]), int(KF["FireGripY"])), angle)
                img.alpha_composite(g, (int(h[0] - r), int(h[1] - r)))
            d.line([centre[0] - 4, centre[1] - 2, h[0], h[1]], fill=(91, 54, 38, 255), width=3)
        sparks.step_draw(d)
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        label = "-" if swing is None else ("%s-slash%s" % ("up" if swing[1] else "down", ", FIRE" if swing[2] else ""))
        gif.text(img, (10, H - 22), "steam %d / %d | swing: %s | 2 steam a swing, 5 on fire (was 4 and 8)" % (steam, tank, label), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Jade Golem: open palms, the afterimage, smooth tracking
# ================================================================================================
def rig_arrays(path):
    src = open(path, encoding="utf-8").read()
    arrays = {}
    for m in re.finditer(r"public static readonly int\[\] (\w+) = \{([^}]*)\};", src):
        arrays[m.group(1)] = [int(v) for v in m.group(2).split(",") if v.strip()]
    return arrays


class GolemSprite:
    """The Jade Golem drawn as JadeGolem.PreDraw does: far, middle, the raised arm (the arm sheet's frame), near, glow."""

    def __init__(self):
        self.k = KG
        self.sheets = [load(COG + "NPCs/JadeGolem" + s + ".png") for s in ("_Far", "", "_Near", "_Glow")]
        self.arm = load(COG + "NPCs/JadeGolem_Arm.png")
        self.arm_glow = load(COG + "NPCs/JadeGolem_ArmGlow.png")

    def cell(self, sheet, frame, cw, ch, cols):
        x0, y0 = frame % cols * (cw + 2), frame // cols * (ch + 2)
        return sheet.crop((x0, y0, x0 + cw, y0 + ch))

    def put(self, img, cell, anchor, ox, oy, cw, flip, alpha=1.0):
        if flip:
            cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
            pos = (int(round(anchor[0] - (cw - ox))), int(round(anchor[1] - oy)))
        else:
            pos = (int(round(anchor[0] - ox)), int(round(anchor[1] - oy)))
        if alpha < 1.0:
            cell.putalpha(cell.getchannel("A").point(lambda a: int(a * alpha)))
        img.alpha_composite(cell, pos)

    def draw(self, img, frame, anchor, flip, arm=None, glow=0.7):
        k = self.k
        cw, ch, ox, oy, cols = int(k["CellWidth"]), int(k["CellHeight"]), int(k["OriginX"]), int(k["OriginY"]), int(k["Columns"])
        aw, ah, aox, aoy, acols = int(k["ArmCellWidth"]), int(k["ArmCellHeight"]), int(k["ArmOriginX"]), int(k["ArmOriginY"]), int(k["ArmColumns"])
        self.put(img, self.cell(self.sheets[0], frame, cw, ch, cols), anchor, ox, oy, cw, flip)
        self.put(img, self.cell(self.sheets[1], frame, cw, ch, cols), anchor, ox, oy, cw, flip)
        if arm is not None:
            self.put(img, self.cell(self.arm, arm, aw, ah, acols), anchor, aox, aoy, aw, flip)
        self.put(img, self.cell(self.sheets[2], frame, cw, ch, cols), anchor, ox, oy, cw, flip)
        self.put(img, self.cell(self.sheets[3], frame, cw, ch, cols), anchor, ox, oy, cw, flip, glow)
        if arm is not None:
            self.put(img, self.cell(self.arm_glow, arm, aw, ah, acols), anchor, aox, aoy, aw, flip, glow)


def scene_golem(out, font):
    W, H, G = 760, 360, 330
    bg = coghaven_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.2)
    sprite = GolemSprite()
    nodes = load(COG + "Projectiles/JadeRay.png")
    orbs = load(COG + "Projectiles/JadeRay_Orb.png")
    gx, face = 600.0, -1                                         # the golem faces left (direction -1)
    shoulder = (gx + KG["ShoulderX"] * -face, G + KG["ShoulderY"])
    hanging, lo, hi = math.pi / 2, math.radians(KG["ArmMinDegrees"]), math.radians(KG["ArmMinDegrees"] + (KG["ArmFrames"] - 1) * KG["ArmStepDegrees"])
    p = Player(150, G)
    trail = []
    track, lock, fire, recover = int(KG["TrackTicks"]), int(KG["LockTicks"]), int(KG["FireTicks"]), int(KG["RecoverTicks"])
    cycle = 30 + int(KG["ChargeTicks"]) + fire + recover
    episodes = [("running", 0), ("standing", cycle), ("teleport", 2 * cycle)]
    total = 3 * cycle + 30
    aim, state, timer, locked = hanging, "walk", 0, 0.0
    pops, notes = [], [(0, "Jade Golem: open palms; the arm follows the player's afterimage (where they were %.1f s ago: the reticle), smoothly" % (KG["AimDelayTicks"] / 60)),
                       (100, "running away: the ray lands on the afterimage behind them"),
                       (cycle, "standing still: the afterimage catches up and the ray leaves the palm along the arm (%d)" % KG["RayDamage"]),
                       (2 * cycle, "a teleport mid-charge: the afterimage jumps, the arm doesn't (at most %.1f degrees a tick)" % math.degrees(KG["AimMaxTurn"]))]
    max_turn = max_palm = max_end = 0.0
    prev_palm = prev_end = None
    ray = None
    hp_pops = []
    for tick in range(total):
        ep = max(e for e in episodes if e[1] <= tick)
        local = tick - ep[1]
        if ep[0] == "running":                                     # scripted input: running away from him
            p.run = -1
            if local == 0:
                p.x = 420.0
        elif ep[0] == "teleport":
            p.run = 0
            if local == 0:
                p.x = 120.0
            if local == 30 + 15:
                p.x = 380.0                                         # a teleport: the mark is elsewhere at once
        else:
            p.run = 0
            if local == 0:
                p.x = 260.0
        p.step()
        p.x = max(30.0, min(470.0, p.x))
        centre = (p.x, p.y - PLAYER_H / 2)
        trail.append(centre)
        trail = trail[-(int(KG["AimDelayTicks"]) + 1):]
        ghost = trail[0]
        # the golem
        if local == 30 and state == "walk":
            state, timer = "charge", 0
        timer += 1
        before = aim
        if state == "charge":
            want = math.atan2(ghost[1] - shoulder[1], abs(ghost[0] - shoulder[0]))
            aim = max(lo, min(hi, aim + max(-KG["AimMaxTurn"], min(KG["AimMaxTurn"], (want - aim) * KG["AimFollow"]))))
            if timer >= track:
                state, timer, locked = "lock", 0, aim
        elif state == "lock":
            aim += (locked - aim) * KG["LockBlend"]
            if timer >= lock:
                aim = locked
                state, timer = "fire", 0
                d_ = (face * math.cos(locked), math.sin(locked))
                start = (shoulder[0] + d_[0] * KG["PalmReach"], shoulder[1] + d_[1] * KG["PalmReach"])
                end = (start[0] + d_[0] * 800, start[1] + d_[1] * 800)
                if end[1] > G:                                      # the floor stops it
                    t_ = (G - start[1]) / max(1e-6, end[1] - start[1])
                    end = (start[0] + (end[0] - start[0]) * t_, G)
                ray = (start, end, tick)
                box = p.box()
                if seg_box_dist(start, end, box) <= KG["Radius"]:
                    hp_pops.append((tick, p.x - 14, p.y - 70, str(int(KG["RayDamage"])), HURT))
                    pops.append((tick, p.x - 30, p.y - 92, "jade curse +1", JADE))
        elif state == "fire":
            if timer >= fire:
                state, timer = "recover", 0
        elif state == "recover":
            aim = min(hanging, aim + KG["RecoverTurn"])
            if timer >= recover:
                state, timer = "walk", 0
        else:
            aim = hanging
        palm = (shoulder[0] + face * math.cos(aim) * KG["PalmReach"], shoulder[1] + math.sin(aim) * KG["PalmReach"])
        end = (palm[0] + face * math.cos(aim) * 400, palm[1] + math.sin(aim) * 400)
        if state in ("charge", "lock", "fire", "recover"):
            max_turn = max(max_turn, abs(aim - before))
            if prev_palm is not None:
                max_palm = max(max_palm, math.hypot(palm[0] - prev_palm[0], palm[1] - prev_palm[1]))
                max_end = max(max_end, math.hypot(end[0] - prev_end[0], end[1] - prev_end[1]))
            prev_palm, prev_end = palm, end
        else:
            prev_palm = prev_end = None
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        aiming = state in ("charge", "lock", "fire") or (state == "recover" and aim < hanging - 0.001)
        arm_k = max(0, min(int(KG["ArmFrames"]) - 1, int(round((math.degrees(aim) - KG["ArmMinDegrees"]) / KG["ArmStepDegrees"]))))
        frame = int(KG["AimBody"]) if aiming else int(KG["Idle"])
        charge = timer / KG["ChargeTicks"] if state == "charge" else (track + timer) / KG["ChargeTicks"] if state == "lock" else 1.0
        sprite.draw(img, frame, (gx, G), face > 0, arm_k if aiming else None, 0.7 + 0.3 * min(1.0, charge) if state in ("charge", "lock") else 0.7)
        if state in ("charge", "lock"):
            dirv = (face * math.cos(locked if state == "lock" else aim), math.sin(locked if state == "lock" else aim))
            alpha = (0.75 if timer % 6 < 3 else 0.3) if state == "lock" else 0.3
            node = faded(nodes.crop((0, 0, 16, 16)), alpha)
            for dd in range(14, 520, 14):
                q = (palm[0] + dirv[0] * dd, palm[1] + dirv[1] * dd)
                if q[1] > G or q[0] < 0:
                    break
                img.alpha_composite(node, (int(q[0] - 8), int(q[1] - 8)))
            if state == "charge":                                    # the reticle on the afterimage
                ghost_img = faded(player_sprite(), 0.28)
                img.alpha_composite(ghost_img, (int(ghost[0] - 20), int(ghost[1] - PLAYER_H / 2 - 35)))
                r = 12 + (0 if timer % 20 < 10 else 2)
                for off in ((r, 0), (-r, 0), (0, r), (0, -r)):
                    img.alpha_composite(faded(nodes.crop((0, 18, 16, 34)), 0.55), (int(ghost[0] + off[0] - 8), int(ghost[1] + off[1] - 8)))
            f = max(0, min(4, int(charge * 5)))
            img.alpha_composite(orbs.crop((0, f * 26, 24, f * 26 + 24)), (int(palm[0] - 12), int(palm[1] - 12)))
        if ray and tick - ray[2] < fire:
            (sx, sy), (ex, ey), t0 = ray
            n = int(math.hypot(ex - sx, ey - sy) / 6)
            fade = 1.0 - (tick - t0) / fire
            for i in range(n):
                q = (sx + (ex - sx) * i / n, sy + (ey - sy) * i / n)
                img.alpha_composite(faded(nodes.crop((0, ((tick // 3 + i) % 3) * 18, 16, ((tick // 3 + i) % 3) * 18 + 16)), fade), (int(q[0] - 8), int(q[1] - 8)))
        img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        numbers(gif, img, pops + hp_pops, tick)
        note(gif, img, notes, tick)
        gif.text(img, (10, H - 44), "measured: the arm turns at most %.2f deg a tick; the palm moves at most %.1f px a tick; the line's point 400 px out at most %.1f px"
                 % (math.degrees(max_turn), max_palm, max_end), fill=STEAM)
        gif.text(img, (10, H - 24), "%s | %s | arm frame %d of %d (5 deg apart)" % (ep[0], state, arm_k, int(KG["ArmFrames"])), fill=STEAM)
        gif.push(img)
    gif.save(out)
    print("golem: max turn %.2f deg/tick (limit %.2f), max palm step %.2f px/tick, max line point step (400 px) %.2f px/tick"
          % (math.degrees(max_turn), math.degrees(KG["AimMaxTurn"]), max_palm, max_end))


# ================================================================================================
# The Cursed Lantern: four souls at most
# ================================================================================================
def scene_lantern(out, font):
    W, H, G = 700, 330, 300
    bg = backdrop(W, H, G, sky=((40, 34, 60), (24, 20, 38)), dirt=(70, 60, 70))
    gif = Gif(font, (W, H), scale=1.2)
    souls_sheet, souls_glow = load(WEP + "SoulFire.png"), load(WEP + "SoulFire_Glow.png")
    lantern = load(WEP + "CursedLantern.png")
    px = 120.0
    souls = []                                                   # [x, y, vx, vy, age, fading, left]
    pops, notes = [(0, "Cursed Lantern: at most %d souls at once; one more and the oldest fades out (%d ticks)" % (KL["MaxSouls"], KL["FadeTicks"]))], []
    use = int(KL["UseTime"])
    shots = 0
    for tick in range(360):
        if tick % use == 0 and tick < 300:
            shots += 1
            live = [s for s in souls if not s[5]]
            if len(live) >= KL["MaxSouls"]:
                oldest = min(live, key=lambda s: s[6])
                oldest[5] = True
                oldest[6] = min(oldest[6], KL["FadeTicks"])
            a = math.radians(-20 - (shots * 9) % 40)
            souls.append([px + 26, G - 40, math.cos(a) * KL["SoulSpeed"], math.sin(a) * KL["SoulSpeed"], 0, False, KL["Lifetime"]])
        for s in souls:
            if s[5]:
                s[2] *= 0.9
                s[3] *= 0.9
            elif s[2] ** 2 + s[3] ** 2 > KL["DriftSpeed"] ** 2:
                s[2] *= KL["Slow"]
                s[3] *= KL["Slow"]
            s[0] += s[2]
            s[1] += s[3]
            s[4] += 1
            s[6] -= 1
        souls = [s for s in souls if s[6] > 0]
        if tick % TPF:
            continue
        img = bg.copy()
        img.alpha_composite(player_sprite(), (int(px - 20), int(G - 56)))
        img.alpha_composite(lantern, (int(px + 6), int(G - 50)))
        for s in souls:
            f = (s[4] // int(KL["FrameTicks"])) % int(KL["Frames"])
            cell = souls_sheet.crop((0, f * 30, 20, f * 30 + 28))
            glow = souls_glow.crop((0, f * 30, 20, f * 30 + 28))
            fade = min(1.0, s[6] / KL["FadeTicks"]) if s[6] < KL["FadeTicks"] else 1.0
            img.alpha_composite(faded(cell, fade), (int(s[0] - 10), int(s[1] - 18)))
            img.alpha_composite(faded(glow, fade), (int(s[0] - 10), int(s[1] - 18)))
        live = sum(1 for s in souls if not s[5])
        fading = sum(1 for s in souls if s[5])
        note(gif, img, pops, tick)
        gif.text(img, (10, H - 24), "souls: %d of %d%s | shots: %d (was: at most 10, the oldest killed outright)" % (
            live, KL["MaxSouls"], (" + %d fading" % fading) if fading else "", shots), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Red Cloth: the bull's charge sidestepped
# ================================================================================================
def scene_cloth(out, font):
    W, H, G = 780, 320, 290
    bg = town_backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.15)
    bull = Planes(TOWN + "NPCs/MechanicalBull", KC)
    cloth_icon, cd_icon = load(TOWN + "Accessories/RedCloth.png"), load(TOWN + "Accessories/RedClothCooldown.png")
    p = Player(220, G)
    hp, cooldown, immune = 400, 0, 0
    pops, notes = [], [(0, "Red Cloth (the Mechanical Bull drops it, 10%%): the next enemy touch is dodged, %.1f s of immunity, then %d s to recharge"
                        % (KC["ImmuneTicks"] / 60, KC["RechargeTicks"] // 60))]
    charges = [(0, "ready: dodged"), (150, "recharging: it hurts"), (330, "12 s after the dodge: ready again")]
    total = 470
    bx, bvx, phase, ptimer, last_hit = 700.0, 0.0, "paw", 0, -999
    cut = {150: "(3 s after the dodge)", 330: "(the 12 s are up)"}
    for tick in range(total):
        for (t0, label) in charges:
            if tick == t0:
                bx, bvx, phase, ptimer = 700.0, 0.0, "paw", 0
                p = Player(220, G)                                   # each charge from the same spot
                immune = 0
                if t0 == 330:
                    cooldown = 0                                     # time skipped: the recharge has run out
                elif t0 == 150:
                    cooldown = int(KC["RechargeTicks"]) - 180            # time skipped: 3 s after the dodge
                notes.append((tick, label + " " + cut.get(t0, "")))
        ptimer += 1
        if phase == "paw" and ptimer >= KC["PawTicks"]:
            phase = "charge"
        if phase == "charge":
            bvx = max(-KC["ChargeSpeed"], bvx - KC["ChargeAccel"])
            bx += bvx
        if cooldown > 0:
            cooldown -= 1
        if immune > 0:
            immune -= 1
        bull_box = (bx - KC["Width"] / 2, G - KC["Height"], bx + KC["Width"] / 2, G)
        if phase == "charge" and overlaps(bull_box, p.box()) and immune == 0 and tick - last_hit > 20:
            last_hit = tick
            if cooldown == 0:
                cooldown, immune = int(KC["RechargeTicks"]), int(KC["ImmuneTicks"])
                pops.append((tick, p.x - 24, G - 100, "Ole!", RED))
            else:
                dmg = int(KC["TrotDamage"] * KC["ChargeDamageMultiplier"])
                hp -= dmg
                pops.append((tick, p.x - 14, G - 90, str(dmg), HURT))
                p.hurt(-1, 9.0)
                immune = 40
        p.step()
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        frame = int(KC["Paw"]) + (ptimer // 8) % 2 if phase == "paw" else int(KC["Charge"]) + (ptimer // 4) % int(KC["ChargeFrames"])
        bull.draw(img, frame, (bx, G), False)
        if immune == 0 or (tick // 6) % 3 != 2:                     # the immunity's blink
            img.alpha_composite(player_sprite(flip=False), (int(p.x - 20), int(p.y - 56)))
        if pops and 0 <= tick - pops[-1][0] < 16 and pops[-1][3] == "Ole!":
            for k in range(14):                                       # the cloth's sweep (RedClothPlayer.Effects)
                a = -1.2 + 2.4 * k / 13
                q = (p.x + math.cos(a) * 22, p.y - PLAYER_H / 2 + math.sin(a) * 26 - (tick - pops[-1][0]))
                d.rectangle([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=RED + (255,))
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        img.alpha_composite(cloth_icon, (W - 120, 34))
        if cooldown > 0:
            img.alpha_composite(cd_icon, (W - 80, 34))
            gif.text(img, (W - 84, 70), "%d s" % math.ceil(cooldown / 60), fill=STEAM)
        else:
            gif.text(img, (W - 84, 40), "ready", fill=(140, 220, 140))
        gif.text(img, (10, H - 22), "player life %d | the bull's charge: %d (Expert)" % (hp, int(KC["TrotDamage"] * KC["ChargeDamageMultiplier"])), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The Delivery Drone (the Amazonian Drone until 2026-11-11)
# ================================================================================================
def scene_drone(out, font):
    W, H, G = 780, 360, 320
    bg = backdrop(W, H, G)
    gif = Gif(font, (W, H), scale=1.15)
    sheet, glow = load("Content/Scrap/NPCs/DeliveryDrone.png"), load("Content/Scrap/NPCs/DeliveryDrone_Glow.png")
    cog = load("Content/Scrap/Items/RustedCog.png")
    loot = load("Content/Gems/Items/JadeStaff.png")
    fw, fh = int(KD["FrameW"]), int(KD["FrameH"])
    player_x = 120.0
    pops, notes = [], [(0, "an item left lying %d s near a player: a Delivery Drone may come for it" % (KD["LyingTicks"] // 60))]
    # part 1: a Jade Staff lying at x 430; part 2: a cog stack at 520, the player shoots
    items = [{"x": 430.0, "img": loot, "here": True, "lying": 0}, {"x": 560.0, "img": cog, "here": False, "lying": 0}]
    drone = None
    life = int(KD["Life"])
    total = 760
    shots = []
    gone_at = None
    for tick in range(total):
        if tick == 10:
            items[0]["lying"] = int(KD["LyingTicks"])                # time skipped: 20 s on the ground
            notes.append((tick, "20 s on the ground (skipped): the drone comes from off screen"))
        if tick == 20:
            drone = {"x": W + 60.0, "y": 60.0, "vx": 0.0, "vy": 0.0, "phase": "approach", "t": 0, "item": 0, "carry": None, "hp": life, "dir": -1}
        if tick == 400:
            items[1]["here"] = True
            drone = {"x": W + 60.0, "y": 50.0, "vx": 0.0, "vy": 0.0, "phase": "approach", "t": 0, "item": 1, "carry": None, "hp": life, "dir": -1}
            notes.append((tick, "another one; this time the player shoots it while it scans"))
        if drone:
            dr = drone
            dr["t"] += 1
            it = items[dr["item"]] if dr["item"] is not None else None
            if dr["phase"] == "approach" and it:
                tx, ty = it["x"], G - 8 - KD["HoverHeight"]
                dx, dy = tx - dr["x"], ty - dr["y"]
                dist = math.hypot(dx, dy)
                sp = min(KD["ApproachSpeed"], dist * 0.12)
                dr["vx"] += ((dx / max(dist, 1e-6)) * sp - dr["vx"]) * KD["ApproachTurn"]
                dr["vy"] += ((dy / max(dist, 1e-6)) * sp - dr["vy"]) * KD["ApproachTurn"]
                dr["dir"] = -1 if dx < 0 else 1
                if dist < 10:
                    dr["phase"], dr["t"] = "scan", 0
                    notes.append((tick, "scanning: %d s, a light a second" % (KD["ScanTicks"] // 60)))
            elif dr["phase"] == "scan" and it:
                bob = math.sin(dr["t"] * 0.08) * 3
                tx, ty = it["x"], G - 8 - KD["HoverHeight"] - bob
                dr["vx"] += ((tx - dr["x"]) * 0.2 - dr["vx"]) * 0.2
                dr["vy"] += ((ty - dr["y"]) * 0.2 - dr["vy"]) * 0.2
                if dr["item"] == 1 and dr["t"] in (60, 61) and not shots:
                    shots.append([player_x + 20, G - 30, tick])
                if dr["t"] >= KD["ScanTicks"]:
                    dr["carry"], it["here"], dr["phase"], dr["t"] = it["img"], False, "flee", 0
                    pops.append((tick, dr["x"] - 20, dr["y"] - 40, "snatched", RED))
            elif dr["phase"] == "flee":
                away = 1 if dr["x"] >= player_x else -1
                dr["vx"] += (away * KD["FleeSpeed"] * 0.8 - dr["vx"]) * KD["FleeTurn"]
                dr["vy"] += (-KD["FleeSpeed"] * 0.6 - dr["vy"]) * KD["FleeTurn"]
                dr["dir"] = away
            dr["x"] += dr["vx"]
            dr["y"] += dr["vy"]
            if dr["phase"] == "flee" and (dr["x"] > W + 80 or dr["y"] < -60):
                notes.append((tick, "out of every player's view: gone, and the item with it"))
                gone_at = tick
                drone = None
        for s in shots:                                               # bullets at the drone
            if drone is None:
                break
            if s[2] > tick or s[2] == -1:
                continue                                              # not fired yet, or spent
            tx, ty = drone["x"], drone["y"]
            dx, dy = tx - s[0], ty - s[1]
            dist = math.hypot(dx, dy)
            s[0] += dx / max(dist, 1e-6) * 26
            s[1] += dy / max(dist, 1e-6) * 26
            if dist < 26:
                s[2] = -1
                drone["hp"] -= 26
                pops.append((tick, drone["x"] - 10, drone["y"] - 50, "26", HIT))
                if drone["phase"] != "flee":
                    it = items[drone["item"]]
                    if abs(it["x"] - drone["x"]) < KD["SnatchRange"]:
                        drone["carry"], it["here"] = it["img"], False
                        pops.append((tick, drone["x"] - 40, drone["y"] - 70, "snatched in a panic!", RED))
                    drone["phase"], drone["t"] = "flee", 0
                    shots.append([player_x + 20, G - 30, tick + 4])
                if drone["hp"] <= 0:
                    items.append({"x": drone["x"], "img": drone["carry"], "here": True, "lying": 0, "fall": drone["y"]})
                    items.append({"x": drone["x"] + 18, "img": cog, "here": True, "lying": 0, "fall": drone["y"]})
                    pops.append((tick, drone["x"] - 30, drone["y"] - 60, "shot down", HIT))
                    notes.append((tick, "shot down: what it stole falls back out, untouched, and a few Rusted Cogs"))
                    drone = None
        shots = [s for s in shots if s[2] != -1]
        for it in items:
            if "fall" in it and it["fall"] < G - 18:
                it["fall"] += 4
        if tick % TPF:
            continue
        img = bg.copy()
        d = ImageDraw.Draw(img)
        img.alpha_composite(player_sprite(), (int(player_x - 20), int(G - 56)))
        for it in items:
            if it["here"] and it["img"] is not None:
                y = it.get("fall", G - 18)
                im = it["img"]
                img.alpha_composite(im, (int(it["x"] - im.width // 2), int(min(y, G - 18) + 18 - im.height)))
        if drone:
            dr = drone
            scanning = dr["phase"] == "scan"
            frame = (3 if dr["carry"] is not None else 0) + (tick // int(KD["FrameTicks"])) % 3
            cell = sheet.crop((0, frame * (fh + 2), fw, frame * (fh + 2) + fh))
            gcell = glow.crop((0, frame * (fh + 2), fw, frame * (fh + 2) + fh))
            flip = dr["dir"] > 0
            if flip:
                cell, gcell = cell.transpose(Image.FLIP_LEFT_RIGHT), gcell.transpose(Image.FLIP_LEFT_RIGHT)
            tl = (int(dr["x"] - fw / 2), int(dr["y"] - fh / 2))
            if scanning:                                            # DeliveryDrone.DrawScan
                it = items[dr["item"]]
                eye = (tl[0] + (fw - KD["EyeX"] if flip else KD["EyeX"]), tl[1] + KD["EyeY"])
                top, bottom = G - 18 - it["img"].height, G
                left, right = it["x"] - it["img"].width / 2 - 4, it["x"] + it["img"].width / 2 + 4
                beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                bd = ImageDraw.Draw(beam)
                rows = max(1, int((bottom - eye[1]) / 2))
                for r in range(rows):
                    t = r / rows
                    l = eye[0] - 1 + (left - eye[0] + 1) * t
                    w_ = 2 + (right - left - 2) * t
                    bd.rectangle([l, eye[1] + r * 2, l + w_, eye[1] + r * 2 + 1], fill=(int(206 * (0.12 + 0.12 * t)), int(74 * (0.12 + 0.12 * t)), int(56 * (0.12 + 0.12 * t)), 255))
                sweep = top + (bottom - top) * (0.5 + 0.5 * math.sin(dr["t"] * 0.15))
                bd.rectangle([left, sweep, right, sweep + 1], fill=(204, 120, 96, 255))
                additive(img, beam, (0, 0), 1.0)
                lit = max(1, min(3, dr["t"] // 60 + 1))
                for k in range(3):
                    x = tl[0] + ((fw - 26 - k * 6) if flip else (26 + k * 6)) - 2
                    d.rectangle([x, tl[1] + 10, x + 3, tl[1] + 13], fill=((236, 122, 88) if k < lit else (84, 20, 28)) + (255,))
            img.alpha_composite(cell, tl)
            img.alpha_composite(gcell, tl)
            if dr["carry"] is not None:
                im = dr["carry"]
                scale = min(1.0, 28 / max(im.width, im.height))
                im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.NEAREST)
                claw = (tl[0] + (fw - KD["ClawX"] if flip else KD["ClawX"]), tl[1] + KD["ClawY"])
                img.alpha_composite(im, (int(claw[0] - im.width / 2), int(claw[1] - 2)))
            gif.text(img, (int(dr["x"] - 18), int(dr["y"] - 40)), "%d/%d" % (max(0, dr["hp"]), life), fill=(255, 140, 120))
        for s in shots:
            if s[2] <= tick:
                d.rectangle([s[0] - 2, s[1] - 1, s[0] + 2, s[1] + 1], fill=(255, 220, 120, 255))
        numbers(gif, img, pops, tick)
        note(gif, img, notes, tick)
        gif.text(img, (10, H - 22), "Delivery Drone: %d life, no contact damage; it scans %d s, snatches, flies off and leaves once nobody can see it"
                 % (life, KD["ScanTicks"] // 60), fill=STEAM)
        gif.push(img)
    gif.save(out)


# ================================================================================================
# The question: Coghaven's chests
# ================================================================================================
def chests_png(out, font_path):
    import coghaven_sim as cs
    isl = cs.Island(obstacle=300, seed=7)
    isl.generate()
    r = cs.Renderer(isl)
    full = r.frame(200)
    font, big = font_at(font_path, 16), font_at(font_path, 22)
    chests = [(ch, x, y) for (ch, x, y) in isl.pieces if ch in "CQ"]
    chests.sort(key=lambda c: (c[1], c[2]))
    half = full.resize((full.width // 2, full.height // 2), Image.NEAREST)
    d = ImageDraw.Draw(half)
    rooms = []
    for n, (ch, x, y) in enumerate(chests, 1):
        X, Y = r.px(x, y)
        X, Y = (X + 16) // 2, (Y + 8) // 2
        col = (255, 215, 60) if ch == "Q" else (255, 90, 70)
        d.ellipse([X - 14, Y - 14, X + 14, Y + 14], outline=col + (255,), width=3)
        d.text((X + 16, Y - 22), str(n), fill=col + (255,), font=big)
        if y > isl.s:
            where = "the engine deck, inside the bronze core under the island"
        elif K_in(x, "MainHallX", 63):
            where = "the Main Hall's ground floor (either side of the throne)"
        elif K_in(x, "PagodaX", 27):
            where = "the pagoda's top floor (the treasure)" if ch == "Q" else "a pagoda floor"
        else:
            where = "the island"
        rooms.append((n, ch, x, y, where))
    sheet = Image.new("RGBA", (half.width, half.height + 60 + 26 * (len(rooms) + 3)), (24, 24, 30, 255))
    sheet.alpha_composite(half, (0, 60))
    gif = Gif(font_path, (10, 10))
    gif.text(sheet, (12, 10), "Coghaven has %d chests (all Dynasty Chests; 7 when only a short pagoda fits under the sky's ceiling)" % len(chests), font=big)
    gif.text(sheet, (12, 36), "red: ordinary chests (3-8 Jade, half of them 20-40 Jade Bricks, plus vanilla's sky-island loot); gold: the pagoda's treasure", font=font)
    y = half.height + 70
    for (n, ch, x, y_, where) in rooms:
        rows = y_ - isl.s
        level = ("%d rows above the terrace" % -rows) if rows < 0 else ("%d rows down inside the island" % rows) if rows > 0 else "on the terrace"
        gif.text(sheet, (12, y), "%d. %s: %s; %d tiles from the island's left end, %s" % (n, "treasure" if ch == "Q" else "chest", where, x, level), font=font)
        y += 26
    gif.text(sheet, (12, y + 6), "the treasure adds 1 in 10 Fledgling Wings, a Lift Turbine, 2 Bronze Cogs, 8-15 Tarnished Brass Bars, 2-4 gold and 8-15 Jade", font=font)
    sheet.convert("RGB").save(out)
    print("%s: %d chests: %s" % (out, len(chests), ", ".join("%s at (%d, %d)" % (c[0], c[1], c[2] - isl.s) for c in chests)))


def K_in(x, key, width):
    import coghaven_sim as cs
    return cs.K[key] <= x < cs.K[key] + width


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media")
    a.add_argument("--only")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    o = lambda name: os.path.join(args.out, name)   # noqa: E731
    jobs = [("firesaw", lambda: scene_firesaw(o("2026-11-10_mechanist-firesaw-phantom-slash.gif"), args.font)),
            ("golem", lambda: scene_golem(o("2026-11-10_coghaven-jade-golem-palm.gif"), args.font)),
            ("lantern", lambda: scene_lantern(o("2026-11-10_boss-cursed-conductor-lantern-cap.gif"), args.font)),
            ("cloth", lambda: scene_cloth(o("2026-11-10_oldbrasstown-red-cloth.gif"), args.font))]
    only = set(args.only.split(",")) if args.only else None
    for name, job in jobs:
        if only is None or name in only:
            job()


if __name__ == "__main__":
    main()
