"""D5 proofs for the 2026-11-19 request. Run from the repo root:

    python -P tools/sim/update_2026_11_19_sim.py [--out docs/media] [--only fox,...]

Offline replays with the real sprites and the C# constants (read from the source files), 60 ticks a second. Leaves out:
lighting, tile collision, netcode and vanilla's own sprites (drawn as stand-ins where needed; the game draws its own).

    fox        the Jade Token's fox up close (the user kept the 60% trace, 2026-11-19: "just ensure a tail sway up and dow
               animation while moving"): its trot cycle (TROT_TAIL) and its spirit float (FLOAT_TAIL) side by side, the
               tail's tip rising and dipping a pixel at a time while the root stays on the rump.
    foxscene   the fox after its owner (update_2026_11_18_sim.fox_gif): trotting, stuck at a wall and floating over it,
               settling and sleeping, waking and following.
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import jadey_loot_sim as L  # noqa: E402
import stage as S  # noqa: E402
from update_2026_11_18_sim import save, fox_gif as fox_scene_gif  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


# ================================================================================================
# The fox's tail sway
# ================================================================================================
def fox_gif(path):
    k = S.consts("Content/Coghaven/Pets/JadeFoxPet.cs")
    sheet = S.load("Content/Coghaven/Pets/JadeFoxPet.png")
    glow = S.load("Content/Coghaven/Pets/JadeFoxPet_Glow.png")
    n = int(k["FrameCount"])
    fh = sheet.height // n
    Z = 3
    pw, ph = sheet.width * Z + 24, fh * Z + 34
    W, H = pw * 2 + 10, ph + 10

    def cell(f):
        c = sheet.crop((0, f * fh, sheet.width, f * fh + fh))
        c.alpha_composite(glow.crop((0, f * fh, sheet.width, f * fh + fh)))
        return c.resize((c.width * Z, c.height * Z), Image.NEAREST)

    frames = []
    for t in range(0, 144, 3):                                  # 3 ticks a GIF frame (50 ms)
        img = Image.new("RGBA", (W, H), (18, 18, 24, 255))
        for i, (name, first, count, ticks) in enumerate((
                ("TROT: TAIL SWAYS", int(k["FrameTrot"]), int(k["TrotFrames"]), 3),
                ("FLOAT: TAIL SWAYS", int(k["FrameFloat"]), int(k["FloatFrames"]), int(k["FloatTicksPerFrame"])))):
            x0 = 5 + i * (pw + 0)
            panel = L.backdrop(pw - 4, ph, ph - 6)
            f = first + (t // ticks) % count
            panel.alpha_composite(cell(f), (12, ph - 6 - fh * Z + int(k["FootPadding"]) * Z))
            L.label(panel, "%s  (frame %d)" % (name, f), 6, 4)
            img.alpha_composite(panel, (x0, 5))
        frames.append(img)
    save(frames, path, scale=1, ms=50)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = (("fox", fox_gif, "2026-11-19_pet-jade-fox-tail-sway.gif"), ("foxscene", fox_scene_gif, "2026-11-19_pet-jade-fox.gif"),)
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(args.out, file))


if __name__ == "__main__":
    main()
