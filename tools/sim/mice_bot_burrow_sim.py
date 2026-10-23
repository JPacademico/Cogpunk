"""D5 simulation of the Mice-bot's anti-stuck AI (Content/Scrap/Minions/MiceBotMinion.cs), with the real mouse and Rusted
Scrap sprites and the C# constants.

    python -P tools/sim/mice_bot_burrow_sim.py --out docs/media/<date>_scrap-mice-bot-burrow.gif

Scene (16 px tiles): the owner on the left; a 4-tile-thick wall, 9 tiles tall (higher than the mouse's 5-tile jump),
with slime A behind it; a cave under a 3-tile floor on the right with slime B inside. Replays the minion's modes:
* Run: accelerates 0.6 px/tick² up to 9 (chasing), gravity 0.4, jumps when blocked.
* Target choice every 10 ticks: nearest slime in sight, or behind <= 4 tiles of solid ground measured along the
  straight line (sampled every 4 px), within 640 px of the mouse and 1000 px of the owner.
* Burrow: against the wall (blocked) or standing above the target, it digs along the straight line at 6 px/tick with
  no tile collision, hidden while underground, and pops out on the far side.
* Zip: with no target and no progress toward its spot by the owner for 45 ticks (stuck in the cave), it dashes home
  through the ground.
Bites: contact, 8 damage, 15 ticks of immunity per slime.

Leaves out: step-ups, slopes, lighting, slime AI (they sit still), the target cache's exact timing, tile dust physics.
"""
import argparse
import math
import os
import random
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armor_preview as ap  # noqa: E402
from terrain import load_frames, render  # noqa: E402

# --- mirrored from MiceBotMinion.cs --------------------------------------------------------------------------------
RUN, FOLLOW, CATCH_UP, ACCEL, JUMP, GRAVITY, MAX_FALL = 9.0, 6.0, 10.0, 0.6, 8.0, 0.4, 10.0
BURROW_SPEED, MAX_BURROW_TICKS, NO_PROGRESS, RETARGET = 6.0, 150, 45, 10
MAX_BURROW_TILES, SAMPLE = 4, 4
LIMIT = MAX_BURROW_TILES + SAMPLE / 16
TARGET_RANGE, CLOSE_RANGE, ZIP_STOP, ZIP_MAX = 640.0, 100.0, 96.0, 15.0
PROGRESS_STEP, ARRIVED = 8.0, 40.0
DAMAGE, COOLDOWN, W_M, H_M, RUN_ANIM = 8, 15, 20, 14, 6.0
# ------------------------------------------------------------------------------------------------------------------
TPF = 3
COLS, ROWS, T = 44, 22, 16
GROUND = 12


def build_level():
    solid = set()
    for x in range(COLS):
        for y in range(GROUND, ROWS):
            solid.add((x, y))
    for x in range(30, 41):                      # cave under a 3-tile floor
        for y in range(15, 20):
            solid.discard((x, y))
    for x in range(18, 22):                      # 4 thick, 9 tall: too high to jump
        for y in range(3, GROUND):
            solid.add((x, y))
    return solid


def rect_solid(solid, x, y, w, h):
    for tx in range(int(x // T), int((x + w - 0.001) // T) + 1):
        for ty in range(int(y // T), int((y + h - 0.001) // T) + 1):
            if (tx, ty) in solid:
                return True
    return False


def solid_length(solid, a, b):
    """MiceBotMinion.SolidLengthOnLine: tiles of solid ground on the straight line, sampled every 4 px."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    n = max(1, min(256, int(length / SAMPLE) + 1))
    per = length / n / 16
    total = 0.0
    for k in range(n + 1):
        px, py = a[0] + dx * k / n, a[1] + dy * k / n
        if (int(px // T), int(py // T)) in solid:
            total += per
            if total > LIMIT:
                return total
    return total


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--out", required=True)
    a = ap_.parse_args()
    rng = random.Random(2)
    solid = build_level()
    grid = ["".join("#" if (x, y) in solid else "." for x in range(COLS)) for y in range(ROWS)]
    tiles = render(grid, {"#": Image.open("Content/Scrap/Tiles/RustedScrapTile.png").convert("RGBA")},
                   load_frames("art/templates/terrain_exposure.json"), seed=4)
    sheet = Image.open("Content/Scrap/Minions/MiceBotMinion.png").convert("RGBA")
    fh = sheet.height // 8
    mframes = [sheet.crop((0, i * fh, sheet.width, (i + 1) * fh)) for i in range(8)]
    owner = (6 * T + 8, GROUND * T)              # bottom centre
    owner_sprite = ap.compose(*(ap.load_frames(p, 4)[0] for p in ("Content/Scrap/Armor/ScrapHelmet_Head.png",
                              "Content/Scrap/Armor/ScrapBreastplate_Body.png", "Content/Scrap/Armor/ScrapLeggings_Legs.png")), 0,
                              [0] * 20)
    slimes = [dict(name="A", x=26 * T + 8, bottom=GROUND * T, life=32, imm=0),
              dict(name="B", x=35 * T + 8, bottom=20 * T, life=32, imm=0)]
    m = dict(x=owner[0] + 24.0, y=GROUND * T - H_M, vx=0.0, vy=0.0, mode="run", frame=0, run=0.0, bite=0, dir=1,
             ground=True, wall=False, burrow=0, dug=False, best=1e9, stall=0)
    target, retarget, dust, events, frames = None, 0, [], [], []

    def centre():
        return m["x"] + W_M / 2, m["y"] + H_M / 2

    def reachable(s):
        c = centre()
        sc = (s["x"], s["bottom"] - 10)
        d = math.hypot(sc[0] - c[0], sc[1] - c[1])
        if d >= TARGET_RANGE:
            return None
        if d < CLOSE_RANGE or solid_length(solid, c, sc) <= LIMIT:
            return d
        return None

    def set_mode(mode, note):
        if m["mode"] != mode:
            m["mode"], m["burrow"], m["dug"], m["best"], m["stall"] = mode, 0, False, 1e9, 0
            events.append((tick, note))

    def progress(goal):
        c = centre()
        d = math.hypot(goal[0] - c[0], goal[1] - c[1])
        if d < ARRIVED or d < m["best"] - PROGRESS_STEP:
            m["best"], m["stall"] = min(m["best"], d), 0
            return False
        m["stall"] += 1
        return m["stall"] > NO_PROGRESS

    total = 380
    for tick in range(total):
        grounded, blocked = m["ground"], m["wall"]
        m["ground"] = m["wall"] = False
        if m["bite"]:
            m["bite"] -= 1
        retarget -= 1
        if retarget <= 0 or target is None or target["life"] <= 0:
            retarget = RETARGET
            best = None
            for s in slimes:
                if s["life"] > 0:
                    d = reachable(s)
                    if d is not None and (best is None or d < best[0]):
                        best = (d, s)
            new = best[1] if best else None
            if new is not target:
                target, m["best"], m["stall"] = new, 1e9, 0
        c = centre()
        if m["mode"] == "run":
            goal_x = target["x"] if target else owner[0] - 28
            top = RUN if target else (CATCH_UP if abs(goal_x - c[0]) > 160 else FOLLOW)
            dx = goal_x - c[0]
            wants = abs(dx) > (6 if target else 16)
            if wants:
                m["vx"] = max(-top, min(top, m["vx"] + math.copysign(ACCEL, dx)))
                m["dir"] = 1 if dx > 0 else -1
            else:
                m["vx"] *= 0.8
                if abs(m["vx"]) < 0.05:
                    m["vx"] = 0.0
            if grounded and wants and blocked:
                m["vy"] = -JUMP
            m["vy"] = min(m["vy"] + GRAVITY, MAX_FALL)
            # move with tile collision, one axis at a time
            nx = m["x"] + m["vx"]
            if rect_solid(solid, nx, m["y"], W_M, H_M):
                m["wall"], m["vx"] = True, 0.0
            else:
                m["x"] = nx
            ny = m["y"] + m["vy"]
            if rect_solid(solid, m["x"], ny, W_M, H_M):
                if m["vy"] > 0:
                    m["ground"] = True
                    ny = (int((ny + H_M) // T)) * T - H_M
                    if rect_solid(solid, m["x"], ny, W_M, H_M):
                        ny = m["y"]
                else:
                    ny = m["y"]
                m["vy"] = 0.0
            m["y"] = ny
            c = centre()
            if target is None:
                if progress((owner[0] - 28, owner[1] - H_M / 2)):
                    set_mode("zip", "stuck with no target: zip home")
            else:
                sc = (target["x"], target["bottom"] - 10)
                walled = solid_length(solid, c, sc) > 0
                below = target["bottom"] - 20 > m["y"] + H_M + 8 and abs(sc[0] - c[0]) < 32
                wall_len = solid_length(solid, c, sc)
                if walled and (blocked or (m["ground"] and below)) and 0 < wall_len <= LIMIT:
                    set_mode("burrow", f"burrow: {wall_len:.1f} tiles of ground to slime {target['name']}")
                elif progress(sc) and 0 < wall_len <= LIMIT:
                    set_mode("burrow", f"no progress: burrow {wall_len:.1f} tiles")
        elif m["mode"] == "burrow":
            goal = (target["x"], target["bottom"] - 10) if target else (owner[0], owner[1] - 21)
            dx, dy = goal[0] - c[0], goal[1] - c[1]
            n = math.hypot(dx, dy) or 1.0
            m["vx"] += (dx / n * BURROW_SPEED - m["vx"]) * 0.3
            m["vy"] += (dy / n * BURROW_SPEED - m["vy"]) * 0.3
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            if abs(m["vx"]) > 0.2:
                m["dir"] = 1 if m["vx"] > 0 else -1
            inside = rect_solid(solid, m["x"], m["y"], W_M, H_M)
            m["dug"] = m["dug"] or inside
            m["burrow"] += 1
            if inside and rng.random() < 0.5:
                dust.append((m["x"] + rng.uniform(0, W_M), m["y"] + rng.uniform(0, H_M), tick))
            if not inside and (m["dug"] or target is None):
                set_mode("run", "out the other side")
            elif m["burrow"] > MAX_BURROW_TICKS:
                set_mode("zip", "too long underground: zip home")
        else:                                     # zip
            goal = (owner[0] - 32, owner[1] - 21 - 24)
            dx, dy = goal[0] - c[0], goal[1] - c[1]
            n = math.hypot(dx, dy) or 1.0
            sp = min(n / 10 + 3, ZIP_MAX)
            m["vx"] += (dx / n * sp - m["vx"]) * 0.12
            m["vy"] += (dy / n * sp - m["vy"]) * 0.12
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            if math.hypot(owner[0] - c[0], owner[1] - 21 - c[1]) < ZIP_STOP and not rect_solid(solid, m["x"], m["y"], W_M, H_M):
                set_mode("run", "home")
        # bites
        for s in slimes:
            if s["imm"]:
                s["imm"] -= 1
            sr = (s["x"] - 14, s["bottom"] - 20, s["x"] + 14, s["bottom"])
            if (target is s and s["life"] > 0 and s["imm"] == 0 and m["x"] < sr[2] and sr[0] < m["x"] + W_M
                    and m["y"] < sr[3] and sr[1] < m["y"] + H_M):
                s["life"] -= DAMAGE
                s["imm"], m["bite"] = COOLDOWN, 8
                events.append((tick, f"bite slime {s['name']}: {DAMAGE}"))
        # frame (MiceBotMinion.UpdateFrame)
        if m["bite"]:
            m["frame"] = 7
        elif m["mode"] != "run" or (not m["ground"] and abs(m["vy"]) > 0.5):
            m["frame"] = 6
        elif abs(m["vx"]) > 0.3:
            if not 2 <= m["frame"] < 6:
                m["frame"] = 2
            m["run"] += abs(m["vx"])
            if m["run"] >= RUN_ANIM:
                m["run"], m["frame"] = 0.0, 2 + (m["frame"] - 1) % 4
        else:
            m["frame"] = (tick // 30) % 2
        if tick % TPF:
            continue
        img = Image.new("RGBA", (COLS * T, ROWS * T), (150, 180, 210, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([30 * T, 15 * T, 41 * T, 20 * T], fill=(46, 50, 59))        # cave darkness
        img.alpha_composite(tiles)
        img.alpha_composite(owner_sprite, (int(owner[0]) - 20, int(owner[1]) - 56))
        for s in slimes:
            if s["life"] > 0:
                sr = (s["x"] - 14, s["bottom"] - 20, s["x"] + 14, s["bottom"])
                d.rounded_rectangle(list(sr), 6, fill=(71, 145, 126), outline=(23, 52, 48))
                d.text((sr[0], sr[1] - 12), f"{s['name']} {s['life']}", fill=(238, 241, 243))
        for (x, y, born) in dust:
            if tick - born < 18:
                d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=(147, 68, 31))
        hidden = m["mode"] == "burrow" and rect_solid(solid, m["x"], m["y"], W_M, H_M)
        if not hidden:
            spr = mframes[m["frame"]]
            if m["dir"] < 0:
                spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
            img.alpha_composite(spr, (int(m["x"] + W_M / 2 - spr.width / 2), int(m["y"] + H_M - (spr.height - 2))))
        recent = [e for e in events if tick - e[0] < 60]
        d.text((6, 4), f"Mice-bot: mode {m['mode']}" + (" (underground, hidden)" if hidden else ""), fill=(21, 22, 28))
        if recent:
            d.text((6, 16), recent[-1][1], fill=(163, 48, 26))
        frames.append(img.convert("RGB").resize((img.width * 2, img.height * 2), Image.NEAREST))
    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=TPF * 1000 // 60, loop=0)
    print(a.out, len(frames), "frames")
    for e in events:
        print("  tick", e[0], e[1])


if __name__ == "__main__":
    main()
