"""D5 simulation of the biome title banner (Core/UI/BiomeTitleSystem.cs): the player walks into the Junkyard, the title
fades in over 12 ticks, holds 180 ticks (3 s) and fades out over 30 ticks, at the top centre of a 1920x1080 screen
(drawn here at half size). Uses the real ornament texture and the system's colours and timings.

    python -P tools/sim/biome_title_sim.py --out docs/media/<date>_junkyard-title.gif [--text "The Junkyard"]

Leaves out: Terraria's "Death Text" font (a bold system font stands in), UI scale settings, the HUD.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

# --- mirrored from BiomeTitleSystem.cs ----------------------------------------------------------
FADE_IN, HOLD, FADE_OUT = 12, 180, 30
TEXT_COLOR, SHADOW_COLOR = (223, 185, 78), (43, 26, 14)
TOP_FRACTION, SPREAD = 0.16, 2.5
# ------------------------------------------------------------------------------------------------
TICKS_PER_FRAME = 3
SCREEN_W, SCREEN_H, HALF = 1920, 1080, 0.5


def opacity(t):
    if t < 0:
        return 0.0
    if t < FADE_IN:
        return t / FADE_IN
    if t < FADE_IN + HOLD:
        return 1.0
    return max(0.0, 1.0 - (t - FADE_IN - HOLD) / FADE_OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="The Junkyard")
    ap.add_argument("--backdrop", default="docs/media/2026-10-22_junkyard-surface.png")
    ap.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    a = ap.parse_args()

    w, h = int(SCREEN_W * HALF), int(SCREEN_H * HALF)
    backdrop = Image.open(a.backdrop).convert("RGBA")
    scale = h / backdrop.height
    backdrop = backdrop.resize((int(backdrop.width * scale), h), Image.NEAREST)
    ornament = Image.open("Assets/UI/BiomeTitleOrnament.png").convert("RGBA")
    font = ImageFont.truetype(a.font, int(44 * HALF * 1.1))
    lead_in = 24                                     # ticks of walking before the biome edge is crossed
    frames = []
    total = lead_in + FADE_IN + HOLD + FADE_OUT + 15
    for tick in range(0, total, TICKS_PER_FRAME):
        t = tick - lead_in
        pan = int(min(tick, lead_in + 60) * 2.2)     # camera drifting left, into the biome
        img = Image.new("RGBA", (w, h), (150, 180, 210, 255))
        x0 = max(0, min(backdrop.width - w, backdrop.width - w - pan))
        img.alpha_composite(backdrop.crop((x0, 0, x0 + w, h)), (0, 0))
        o = opacity(t)
        if o > 0:
            layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            bbox = d.textbbox((0, 0), a.text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            cx, cy = w // 2, int(h * TOP_FRACTION)
            x, y = cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1]
            sp = max(1, round(SPREAD * HALF))
            for dx in (-sp, 0, sp):
                for dy in (-sp, 0, sp):
                    if dx or dy:
                        d.text((x + dx, y + dy), a.text, font=font, fill=SHADOW_COLOR + (255,))
            d.text((x, y), a.text, font=font, fill=TEXT_COLOR + (255,))
            half = ornament.width // 2
            left = ornament.crop((0, 0, half, ornament.height))
            right = ornament.crop((half, 0, ornament.width, ornament.height))
            oy = cy - ornament.height // 2 + 1
            layer.alpha_composite(left, (cx - tw // 2 - half - 4, oy))
            layer.alpha_composite(right, (cx + tw // 2 + 4, oy))
            alpha = layer.getchannel("A").point(lambda v: int(v * o))
            layer.putalpha(alpha)
            img.alpha_composite(layer)
        d = ImageDraw.Draw(img)
        state = "outside" if t < 0 else ("fade in" if t < FADE_IN else ("hold 3 s" if t < FADE_IN + HOLD else ("fade out" if t < FADE_IN + HOLD + FADE_OUT else "done")))
        d.text((6, h - 16), f"tick {max(t, 0):3d}  {state}", fill=(21, 22, 28))
        frames.append(img.convert("RGB"))
    frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=TICKS_PER_FRAME * 1000 // 60, loop=0)
    print(f"{a.out}: {len(frames)} frames, {total / 60:.1f} s")


if __name__ == "__main__":
    main()
