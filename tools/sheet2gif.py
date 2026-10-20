"""Turn a Terraria sprite sheet into a looping preview GIF (sprite-level visual proof).

Usage: python tools/sheet2gif.py SHEET.png --frames N [--ticks 5] [--scale 2] [--horizontal] [--out PATH] [--contact PNG]
--ticks is game ticks per frame (60 ticks = 1 s), i.e. the same threshold your frameCounter uses.
GIF delays are stored in 10 ms units, so tick values that are multiples of 3 play back exactly.
"""
import argparse
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--ticks", type=int, default=5, help="game ticks per frame (60 per second)")
    ap.add_argument("--scale", type=int, default=2, help="extra nearest-neighbour zoom for viewing")
    ap.add_argument("--bg", default="1e1e24", help="background hex; GIF has no partial alpha")
    ap.add_argument("--horizontal", action="store_true", help="frames laid out left-to-right")
    ap.add_argument("--out")
    ap.add_argument("--contact", help="also write all frames side by side to this PNG (for review)")
    a = ap.parse_args()

    sheet = Image.open(a.sheet).convert("RGBA")
    w, h = sheet.size
    fw, fh = (w // a.frames, h) if a.horizontal else (w, h // a.frames)
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

    frames = []
    for i in range(a.frames):
        box = (i * fw, 0, (i + 1) * fw, fh) if a.horizontal else (0, i * fh, fw, (i + 1) * fh)
        f = Image.new("RGBA", (fw, fh), bg)
        f.alpha_composite(sheet.crop(box))
        if a.scale > 1:
            f = f.resize((fw * a.scale, fh * a.scale), Image.NEAREST)
        frames.append(f.convert("RGB"))

    ms = round(a.ticks * 1000 / 60)
    out = a.out or a.sheet.rsplit(".", 1)[0] + "_preview.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=False)
    if a.contact:
        strip = Image.new("RGB", (frames[0].width * len(frames), frames[0].height))
        for i, f in enumerate(frames):
            strip.paste(f, (i * f.width, 0))
        strip.save(a.contact)
    print(f"{out}: {a.frames} frames of {fw}x{fh}px (x{a.scale}) at {ms} ms/frame")


if __name__ == "__main__":
    main()
