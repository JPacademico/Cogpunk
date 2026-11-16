"""Source for the Jade Beetle (D4, 2026-11-16): Jadey's lesser jade copy of the Rhino Beetle (user: "jade beetle (the jade
version of the rhino beetle we already have, weaker because the beetle is from hardmode)"). Run from the repo root AFTER
art/jungle/make_rhino_beetle_art.py (it recolours that generator's output, so both stay one model):

    python -P art/coghaven/make_jade_beetle_art.py

The recolour, ramp to ramp by shade (every colour stays in the palette; the geometry, frames and RigData are the Rhino
Beetle's): the shell's oak becomes jade (ghost), the body's hide and leather bronze (gilt), the wings' ivory verdigris
and jade, and the spore-green rune on the shell a gilt vein (it would vanish on jade).

Outputs: Content/Bosses/Jadey/NPCs/JadeBeetle.png, _Far.png, _Near.png, _Glow.png, Content/Bosses/Jadey/Gores/JadeBeetle_Gore*.png
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, COLOR_INDEX  # noqa: E402

ROOT = os.getcwd()
SRC = "Content/Jungle/"
DST = "Content/Bosses/Jadey/"

MAP = {
    "oak": [RAMP["ghost"][k] for k in range(6)],
    "hide": [RAMP["gilt"][k] for k in (0, 1, 2, 3, 5, 6, 7)],
    "leather": [RAMP["gilt"][k] for k in (0, 1, 2)],
    "ivory": [RAMP["verd"][0], RAMP["verd"][1], RAMP["verd"][2], RAMP["verd"][3], RAMP["ghost"][4], RAMP["ghost"][5]],
    "ghost": [RAMP["gilt"][k] for k in (1, 3, 5, 6, 8, 9)],
    "denim": [RAMP["ghost"][0]] * 6,
}


def recolour(src, dst):
    im = Image.open(os.path.join(ROOT, src)).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            key = COLOR_INDEX.get((r, g, b))
            if key and key[0] in MAP:
                ramp, k = key
                nr, ng, nb = MAP[ramp][min(k, len(MAP[ramp]) - 1)]
                px[x, y] = (nr, ng, nb, a)
    out = os.path.join(ROOT, dst)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out)
    print("wrote", dst)


def main():
    for suffix in ("", "_Far", "_Near", "_Glow"):
        recolour(SRC + "NPCs/RhinoBeetle%s.png" % suffix, DST + "NPCs/JadeBeetle%s.png" % suffix)
    for gore in ("Horn", "Shell", "Leg"):
        recolour(SRC + "Gores/RhinoBeetle_Gore%s.png" % gore, DST + "Gores/JadeBeetle_Gore%s.png" % gore)


if __name__ == "__main__":
    main()
