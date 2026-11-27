"""D5 visual proof for the 0.4.0 update batch (2026-11-27):
- Jade Golem 25% smaller (34x78 vs old 46x104, PalmReach 46.9 px) walking, tracking, locking, and firing next to the player.
- Spark research chain showcase: normal spark (1.0 s) vs Better Sparks (2.0 s, longer straight reach + arc) + Sparkling! ignition + Induced Combustion (2-4 spark burst on enemy kill).
"""
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import stage as S  # noqa: E402
import update_2026_11_25_sim as U  # noqa: E402
import update_2026_11_26_sim as V  # noqa: E402


def cell(sheet, k, cw, ch, cols=1, gap=2):
    return V.grid_cell(sheet, k, cw, ch, cols, gap)


def put(img, c, ox, oy, ax, ay, flip=False):
    V.put_cell(img, c, ox, oy, ax, ay, flip)


def float_const(rel_path, name):
    txt = open(os.path.join(S.ROOT, rel_path), encoding="utf-8").read()
    m = re.search(rf"\b{name}\s*=\s*([0-9.]+)f?", txt)
    return float(m.group(1)) if m else 0.0


def build_proof(out_path):
    rel = "Content/Coghaven/NPCs/JadeGolem"
    r = U.ints(rel + "RigData.cs")
    palm_reach = float_const(rel + "RigData.cs", "PalmReach")
    c = S.consts("Content/Coghaven/Projectiles/JadeRay.cs", "Content/Coghaven/NPCs/JadeGolem.cs")
    rc = S.consts("Content/Research/ResearchNodes.cs")

    far = S.darkened(S.load(rel + "_Far.png"), 0.88)
    mid, near, glow = S.load(rel + ".png"), S.load(rel + "_Near.png"), S.load(rel + "_Glow.png")
    arm, armg = S.load(rel + "_Arm.png"), S.load(rel + "_ArmGlow.png")
    nodes = S.load("Content/Coghaven/Projectiles/JadeRay.png")
    orb = S.load("Content/Coghaven/Projectiles/JadeRay_Orb.png")
    driller_sheet = S.load("Content/Underground/NPCs/Driller.png")
    driller_r = U.ints("Content/Underground/NPCs/DrillerRigData.cs")
    sparkler_tex = S.load("Content/Mechanist/Weapons/Sparkler.png")

    cw, ch, cols = r["CellWidth"], r["CellHeight"], r["Columns"]
    Wd, Hd = 540, 290
    top_floor = 152
    bot_floor = 270
    STEP = 3

    px, pchest = 68, top_floor - 24
    gx, dist = 445.0, 0.0
    walk, idle = 108, 18
    charge, fire, recover = int(c["ChargeTicks"]), int(c["FireTicks"]), int(c["RecoverTicks"])
    lock = int(c["LockTicks"])
    aim = math.pi / 2
    total = walk + idle + charge + fire + recover + 24

    # Pre-simulate Spark comparison + Induced Combustion in bottom lane (ticks 0..total-1)
    rng = random.Random(404)
    sparks_std = []     # [x, y, vx, vy, ai0, alive]
    sparks_better = []  # [x, y, vx, vy, ai0, extra, half, alive, burst]
    target_alive = True
    target_burn = 0
    target_x = 350.0
    combust_flashes = 0

    frames = []
    for t in range(total):
        # Spawn a side-by-side spark pair at t=6 and t=126
        if t in (6, 126):
            sparks_std.append([86.0, bot_floor - 54.0, 4.2, -0.35, 0.0, True])
            sparks_better.append([86.0, bot_floor - 18.0, 4.6, 0.02, 0.0, 0, False, True, False])
            if t == 6:
                target_alive = True
                target_burn = 0

        # Update standard sparks (60 ticks = 1.0 s)
        for sp in sparks_std:
            if not sp[5]:
                continue
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[4] += 1.0
            if sp[4] > 15.0:
                sp[3] += 0.14
                sp[2] *= 0.98
            if sp[4] >= 60.0 or sp[1] >= bot_floor - 34:
                sp[5] = False

        # Update Better Sparks (+60 ticks = 2.0 s, longer straight flight + Induced Combustion on kill)
        for sp in sparks_better:
            if not sp[7]:
                continue
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[4] += 1.0
            if sp[4] >= 4.0 and sp[5] < int(rc["BetterSparksExtraTicks"]):
                if sp[5] < int(rc["BetterSparksExtraTicks"]) // 2:
                    sp[4] -= 1.0
                    sp[5] += 1
                else:
                    sp[6] = not sp[6]
                    if sp[6]:
                        sp[4] -= 1.0
                        sp[5] += 1
            if sp[4] > 15.0:
                sp[3] += 0.14
                sp[2] *= 0.98
            # Check hit on Driller target at target_x
            if not sp[8] and target_alive and abs(sp[0] - target_x) < 20 and abs(sp[1] - (bot_floor - 14)) < 18:
                sp[7] = False
                target_burn = 36
                if t > 80:
                    # Second shot finishes enemy -> Induced Combustion (3 sparks around it, non-chaining!)
                    target_alive = False
                    combust_flashes = 15
                    count = 4
                    base_a = -math.pi * 0.85
                    for bi in range(count):
                        ang = base_a + (math.pi * 0.7) * bi / (count - 1) + rng.uniform(-0.12, 0.12)
                        spd = rng.uniform(3.2, 4.6)
                        sparks_better.append([
                            target_x, bot_floor - 14.0,
                            math.cos(ang) * spd, math.sin(ang) * spd - 1.1,
                            0.0, 0, False, True, True
                        ])
                continue
            if sp[4] >= 60.0 or sp[1] >= bot_floor - 2:
                sp[7] = False

        if target_burn > 0:
            target_burn -= 1
        if combust_flashes > 0:
            combust_flashes -= 1

        # Update Jade Golem in top lane
        anchor = (gx, top_floor)
        shoulder = (gx + r["ShoulderX"], top_floor + r["ShoulderY"])
        goal = math.atan2(pchest - shoulder[1], abs(px - shoulder[0]))
        aiming = False
        phase = "walk"
        if t < walk:
            gx -= c["WalkSpeed"] * 1.4
            dist += c["WalkSpeed"] * 1.4
            k = r["Walk"] + int(dist // r["WalkStep"]) % r["WalkFrames"]
        elif t < walk + idle:
            phase = "idle"
            k = r["Idle"] + ((t - walk) // 15) % r["IdleFrames"]
        else:
            k = r["AimBody"]
            aiming = True
            tt = t - walk - idle
            if tt < charge - lock:
                phase = "charge"
                aim += max(-c["AimMaxTurn"], min(c["AimMaxTurn"], (goal - aim) * c["AimFollow"]))
            elif tt < charge:
                phase = "lock"
            elif tt < charge + fire:
                phase = "fire"
            else:
                phase = "recover"
                aim = min(math.pi / 2, aim + c["RecoverTurn"])

        if t % STEP:
            continue

        # Render two-tier stage
        img = U.backdrop(floor=bot_floor, w=Wd, h=Hd)
        draw = ImageDraw.Draw(img)
        # Upper platform for Jade Golem
        draw.rectangle([0, top_floor, Wd, top_floor + 8], fill=(40, 52, 46, 255))
        draw.line([(0, top_floor), (Wd, top_floor)], fill=(96, 152, 116, 255), width=2)

        # Old 46x104 vs new 34x78 subtle dashed reference box at right for scale proof
        ref_x = 496
        draw.rectangle([ref_x - 23, top_floor - 104, ref_x + 23, top_floor - 1], outline=(90, 110, 100, 255), width=1)
        draw.rectangle([ref_x - 17, top_floor - 78, ref_x + 17, top_floor - 1], outline=(96, 224, 148, 255), width=1)

        # Top lane: Player + 75%-scale Jade Golem
        U.put_player(img, px, top_floor, 0, True)
        put(img, cell(far, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        put(img, cell(mid, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        ak = max(0, min(r["ArmFrames"] - 1, round((math.degrees(aim) - r["ArmMinDegrees"]) / r["ArmStepDegrees"])))
        if aiming:
            put(img, cell(arm, ak, r["ArmCellWidth"], r["ArmCellHeight"], r["ArmColumns"]), r["ArmOriginX"], r["ArmOriginY"], *anchor)
        put(img, cell(near, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        put(img, cell(glow, k, cw, ch, cols), r["OriginX"], r["OriginY"], *anchor)
        if aiming:
            put(img, cell(armg, ak, r["ArmCellWidth"], r["ArmCellHeight"], r["ArmColumns"]), r["ArmOriginX"], r["ArmOriginY"], *anchor)
            d = (-math.cos(aim), math.sin(aim))
            palm = (shoulder[0] + d[0] * palm_reach, shoulder[1] + d[1] * palm_reach)
            dot = cell(nodes, 0, 16, 16)
            if phase in ("charge", "lock"):
                alpha = 0.75 if phase == "lock" and (t // 3) % 2 == 0 else 0.3 if phase == "lock" else 0.22
                s = 14.0
                while s < 420:
                    q = (palm[0] + d[0] * s, palm[1] + d[1] * s)
                    if q[0] < 0 or q[1] > top_floor:
                        break
                    S.blit(img, S.faded(dot, alpha), int(q[0]) - 8, int(q[1]) - 8)
                    s += 14.0
                tt = t - walk - idle
                ok = min(4, int(tt / charge * 5))
                S.blit(img, cell(orb, ok, 24, 24), int(palm[0]) - 12, int(palm[1]) - 12)
            elif phase == "fire":
                tt = t - walk - idle - charge
                fade = 1.0 - tt / max(1, fire)
                s = 0.0
                while s < 450:
                    q = (palm[0] + d[0] * s, palm[1] + d[1] * s)
                    if q[0] < 0 or q[1] > top_floor:
                        break
                    S.blit(img, S.faded(cell(nodes, (int(s / 6) + t) % 3, 16, 16), fade), int(q[0]) - 8, int(q[1]) - 8)
                    s += 6.0

        # Bottom lane: Player with Sparkler + Standard vs Better Sparks + Induced Combustion
        U.put_player(img, 58, bot_floor, 0, True)
        S.blit(img, sparkler_tex, 62, bot_floor - 30)
        # Lane divider line for standard spark (upper sub-lane)
        draw.line([(76, bot_floor - 34), (280, bot_floor - 34)], fill=(70, 70, 82, 255), width=1)

        if target_alive:
            dk = (t // 6) % driller_r.get("Frames", 4)
            put(img, cell(driller_sheet, dk, driller_r["CellWidth"], driller_r["CellHeight"], driller_r.get("Columns", 1)),
                driller_r["OriginX"], driller_r["OriginY"], target_x, bot_floor)
            if target_burn > 0:
                for fi in range(3):
                    fx = int(target_x - 12 + fi * 11 + ((t + fi * 3) % 5) - 2)
                    fy = int(bot_floor - 22 - ((t + fi * 4) % 8))
                    draw.rectangle([fx, fy, fx + 3, fy + 3], fill=(255, 150, 36, 255))
                    draw.rectangle([fx + 1, fy - 2, fx + 2, fy], fill=(255, 232, 92, 255))
        elif combust_flashes > 0:
            r_ring = (16 - combust_flashes) * 2
            draw.ellipse([target_x - r_ring, bot_floor - 14 - r_ring, target_x + r_ring, bot_floor - 14 + r_ring],
                         outline=(255, 188, 64, 255), width=2)

        # Draw standard sparks (dimmer ember, vanishes at 1.0 s)
        for sp in sparks_std:
            if sp[5] and sp[4] >= 4.0:
                sx, sy = int(sp[0]), int(sp[1])
                draw.rectangle([sx - 2, sy - 2, sx + 2, sy + 2], fill=(235, 118, 34, 255))
                draw.rectangle([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 220, 110, 255))

        # Draw Better Sparks + Induced Combustion sparks (bright gold-orange core + trail)
        for sp in sparks_better:
            if sp[7] and sp[4] >= 4.0:
                sx, sy = int(sp[0]), int(sp[1])
                tx, ty = int(sp[0] - sp[2] * 1.3), int(sp[1] - sp[3] * 1.3)
                draw.rectangle([tx - 1, ty - 1, tx + 1, ty + 1], fill=(224, 92, 28, 255))
                draw.rectangle([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 152, 42, 255))
                draw.rectangle([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 244, 168, 255))

        U.label(img, "0.4.0 TOP: Jade Golem 25% smaller (34x78 vs old 46x104 box on right)", 6, 4, width=92)
        U.label(img, "BOTTOM: base spark (1s, top) vs Sparkling! + Better Sparks (2s) + Induced Combustion (2-4 spark kill burst)",
                6, top_floor + 12, width=98)
        frames.append(img)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    U.save_gif(frames, out_path, scale=1)
    print(f"wrote {out_path} ({len(frames)} frames)")


if __name__ == "__main__":
    out = os.path.join(S.ROOT, "docs", "media", "2026-11-27_0.4.0-jade-golem-sparks.gif")
    build_proof(out)
