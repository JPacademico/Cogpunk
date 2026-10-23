"""D5 simulation of the Scrappybot pet: follow -> owner stands still -> power down and recharge ->
owner moves -> clunky wake-up -> follow. Uses the real sprite sheet and the constants and frame logic of
Content/Scrap/Pets/ScrappybotPet.cs (keep them in sync).

    python -P tools/sim/scrappybot_sim.py --out docs/media/<date>_scrap-scrappybot.gif [--contact sheet.png]

Leaves out: tile collision, jumping, the flight state (its frames are in the contact sheet), lighting and
netcode. Flat ground, 3 game ticks per GIF frame (20 fps, exact timing).
"""
import argparse
import os
from PIL import Image, ImageDraw

# --- mirrored from ScrappybotPet.cs -----------------------------------------------------------
FRAME_COUNT = 16
FRAME_IDLE, FRAME_WALK, FRAME_FLY, FRAME_SETTLE, FRAME_SLEEP, FRAME_WAKE = 0, 1, 5, 7, 9, 12
FOOT_PADDING = 2
SLEEP_DELAY = 300
SETTLE_TICKS_PER_FRAME = 12
SLEEP_TICKS_PER_FRAME = 18
WALK_ANIM_DISTANCE = 9.0
WAKE_END1, WAKE_END2, WAKE_END3, WAKE_TICKS = 3, 9, 12, 18
ACCELERATION, WALK_SPEED, RUN_SPEED, FOLLOW_OFFSET = 0.25, 4.5, 7.0, 48.0
# -----------------------------------------------------------------------------------------------

TICKS_PER_GIF_FRAME = 3
SCENE_W, SCENE_H, GROUND_Y = 360, 110, 92


def owner_script(tick):
    """Owner x position and velocity: walks right, stands still for 7 s, then walks left."""
    if tick < 60:
        return 60 + tick * 3.0, 3.0
    if tick < 60 + 420:
        return 240.0, 0.0
    return 240.0 - (tick - 480) * 3.0, -3.0


def simulate(total_ticks):
    state, timer, still = "follow", 0, 0
    x, vx, frame, walk_dist, direction = 40.0, 0.0, FRAME_IDLE, 0.0, 1
    for tick in range(total_ticks):
        ox, ovx = owner_script(tick)
        odir = 1 if ovx >= 0 else -1
        timer += 1
        if state == "follow":
            dx = ox - odir * FOLLOW_OFFSET - x
            wants = abs(dx) > 24
            if wants:
                max_speed = RUN_SPEED if abs(dx) > 160 else WALK_SPEED
                vx = max(-max_speed, min(max_speed, vx + (1 if dx > 0 else -1) * ACCELERATION))
                direction = 1 if dx > 0 else -1
            else:
                vx *= 0.85
                if abs(vx) < 0.05:
                    vx = 0.0
                direction = 1 if ox >= x else -1
            still = still + 1 if (abs(ovx) < 0.1 and not wants) else 0
            if still >= SLEEP_DELAY:
                state, timer, still = "sleep", 0, 0
        elif state == "sleep":
            vx *= 0.8
            if abs(ovx) > 0.5:
                state, timer = "wake", 0
        elif state == "wake":
            vx = 0.0
            if timer >= WAKE_TICKS:
                state, timer = "follow", 0
        x += vx

        # Frame selection (UpdateFrame).
        t = timer
        if state == "sleep":
            if t < SETTLE_TICKS_PER_FRAME:
                frame = FRAME_SETTLE
            elif t < SETTLE_TICKS_PER_FRAME * 2:
                frame = FRAME_SETTLE + 1
            else:
                frame = FRAME_SLEEP + ((t - SETTLE_TICKS_PER_FRAME * 2) // SLEEP_TICKS_PER_FRAME) % 3
        elif state == "wake":
            frame = FRAME_WAKE + (0 if t < WAKE_END1 else 1 if t < WAKE_END2 else 2 if t < WAKE_END3 else 3)
        elif abs(vx) > 0.3:
            if not (FRAME_WALK <= frame < FRAME_WALK + 4):
                frame = FRAME_WALK
            walk_dist += abs(vx)
            if walk_dist >= WALK_ANIM_DISTANCE:
                walk_dist = 0.0
                frame = FRAME_WALK + (frame - FRAME_WALK + 1) % 4
        else:
            frame = FRAME_IDLE
        yield tick, ox, ovx, x, frame, direction, state, still


def draw_owner(img, ox):
    """Neutral placeholder for the player (no vanilla art is used)."""
    d = ImageDraw.Draw(img)
    x = int(ox)
    d.rectangle([x - 6, GROUND_Y - 42, x + 5, GROUND_Y - 31], fill=(127, 135, 148))   # head
    d.rectangle([x - 8, GROUND_Y - 30, x + 7, GROUND_Y - 1], fill=(79, 85, 98))       # body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default="Content/Scrap/Pets/ScrappybotPet.png")
    ap.add_argument("--out", required=True)
    ap.add_argument("--contact")
    ap.add_argument("--zoom", type=int, default=2)
    a = ap.parse_args()

    sheet = Image.open(a.sheet).convert("RGBA")
    fw, fh = sheet.width, sheet.height // FRAME_COUNT
    frames = [sheet.crop((0, i * fh, fw, (i + 1) * fh)) for i in range(FRAME_COUNT)]
    flipped = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in frames]

    total = 480 + 120
    gif_frames = []
    for tick, ox, ovx, x, frame, direction, state, still in simulate(total):
        if tick % TICKS_PER_GIF_FRAME:
            continue
        img = Image.new("RGBA", (SCENE_W, SCENE_H), (30, 30, 36, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, GROUND_Y, SCENE_W, SCENE_H], fill=(91, 54, 38))
        d.rectangle([0, GROUND_Y, SCENE_W, GROUND_Y + 1], fill=(71, 145, 126))
        draw_owner(img, ox)
        sprite = frames[frame] if direction == 1 else flipped[frame]
        img.alpha_composite(sprite, (int(x - fw / 2), GROUND_Y - (fh - FOOT_PADDING)))
        label = f"{tick / 60:4.1f}s  {state}" + (f"  still {still / 60:.1f}s" if state == "follow" and still else "")
        d.text((6, 4), label, fill=(195, 200, 205))
        img = img.convert("RGB").resize((SCENE_W * a.zoom, SCENE_H * a.zoom), Image.NEAREST)
        gif_frames.append(img)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    gif_frames[0].save(a.out, save_all=True, append_images=gif_frames[1:],
                       duration=TICKS_PER_GIF_FRAME * 1000 // 60, loop=0)
    print(f"{a.out}: {len(gif_frames)} frames, {total / 60:.1f} s")

    if a.contact:
        names = ["idle", "walk1", "walk2", "walk3", "walk4", "fly1", "fly2", "settle1", "settle2",
                 "sleep1", "sleep2", "sleep3", "wake1", "wake2", "wake3", "wake4"]
        z = 3
        cw, ch = fw * z, fh * z + 14
        out = Image.new("RGB", (cw * 8, ch * 2), (60, 64, 72))
        d = ImageDraw.Draw(out)
        for i, f in enumerate(frames):
            cx, cy = (i % 8) * cw, (i // 8) * ch
            out.paste(f.resize((fw * z, fh * z), Image.NEAREST), (cx, cy + 14), f.resize((fw * z, fh * z), Image.NEAREST))
            d.text((cx + 4, cy + 2), f"{i} {names[i]}", fill=(238, 241, 243))
        out.save(a.contact)
        print(f"{a.contact}: frame contact sheet")


if __name__ == "__main__":
    main()
