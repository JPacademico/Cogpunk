"""Source for the Cogfish, the Tar Immunity Potion and its buff icon (D4), 2026-11-26 (user: "add a new fish that can be
fished on the tar pit called "cogfish" it should be using in crafting for tar imunity potion"). Run from the repo root:

    python -P art/junkyard/make_cogfish_art.py [--preview FILE]

Design (my calls):
- Cogfish (19 x 13 art): a stocky fish of oily dark iron (the tar it swims in), lit from the top-left with one wet glint, a
  pale brass belly plate, a brass cog for a dorsal fin (its teeth showing over the back), a riveted brass gill plate, a forked
  copper tail and a little ember eye. Facing left.
- Tar Immunity Potion (10 x 14 art, vanilla's potion size): a round flask of clear glass (steel's light tones at its rim, a
  steam glint) filled with black tar, a brass cork with a cog's rim.
- Tar Immunity (16 x 16 art, a buff icon): a brass-rimmed shield over a drop of tar, the drop's glint.

Outputs: Content/Junkyard/Items/Cogfish.png, Content/Junkyard/Items/TarImmunityPotion.png, Content/Junkyard/Buffs/TarImmunity.png
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, preview  # noqa: E402
from rig import RAMP  # noqa: E402

IRON, BRASS, COPPER, EMBER, STEEL, STEAM = RAMP["iron"], RAMP["brass"], RAMP["copper"], RAMP["ember"], RAMP["steel"], RAMP["steam"]
TAR = (IRON[0], (47, 27, 20), IRON[1], (91, 54, 38), IRON[2])        # the tar's own blacks and browns (the palette's)


def lit(dx, dy, r):
    """-1 (shadow, bottom-right) .. 1 (light, top-left)."""
    return -(dx * 0.62 + dy * 0.78) / max(0.01, r)


def cogfish():
    p = Pix(19, 13)
    cx, cy, rx, ry = 8.4, 7.4, 6.6, 3.6
    # the cog fin first (behind the back): a gear of six teeth, its upper half over the back
    gx, gy = 8.0, 3.4
    for y in range(0, 7):
        for x in range(3, 14):
            dx, dy = x + 0.5 - gx, y + 0.5 - gy
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            tooth = (math.cos(a * 6.0) > 0.25) and d < 3.6
            if d < 2.5 or tooth:
                p.put(x, y, BRASS, 3 + round(lit(dx, dy, 3.0) * 1.5))
    # the body: an ellipse, domed from the top-left, its belly a brass plate
    for y in range(13):
        for x in range(19):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                if dy > 0.45 and -0.75 < dx < 0.55:
                    p.put(x, y, BRASS, 2 + round(lit(dx, dy * 0.6, 1.0) * 1.2))
                else:
                    p.put(x, y, IRON, 2 + round(lit(dx, dy, 1.0) * 1.3))
    # the tail: a solid fan of copper joined to the body, forked only at its tips
    fan = ((14, 6, 8), (15, 5, 9), (16, 4, 10), (17, 3, 6), (17, 8, 11), (18, 2, 4), (18, 10, 12))
    for (x, y0, y1) in fan:
        for y in range(y0, y1 + 1):
            p.put(x, y, COPPER, 3 if y <= 7 else 2)
    # the gill plate: an arc of brass
    for (x, y) in ((6, 5), (6, 6), (6, 7), (6, 8), (7, 9)):
        p.put(x, y, BRASS, 4 if y < 7 else 3)
    p.outline()
    # stamps after the outline
    p.put(3, 6, EMBER, 3, lock=True)                                   # the eye
    p.put(3, 7, EMBER, 1, lock=True)
    p.put(9, 5, IRON, 4, lock=True)                                    # the wet glint on the back
    p.put(10, 5, IRON, 3, lock=True)
    for (x, y) in ((8, 8), (10, 8), (12, 8)):                          # rivets along the flank
        p.put(x, y, BRASS, 4, lock=True)
    for (x, y, i) in ((15, 6, 4), (15, 7, 3), (15, 8, 2), (16, 5, 4), (16, 6, 3), (16, 9, 2), (17, 4, 3), (17, 9, 2)):
        p.put(x, y, COPPER, i, lock=True)                              # the fan's rays, lit from the top-left
    p.put(8, 2, BRASS, 5, lock=True)                                   # the cog's glint
    p.put(8, 3, IRON, 1, lock=True)                                    # its axle
    return p.image()


def potion():
    p = Pix(10, 14)
    cx, cy, r = 5.0, 9.4, 4.4
    for y in range(14):
        for x in range(10):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d <= r:
                if d > r - 1.0:
                    p.put(x, y, STEEL, 6 + round(lit(dx, dy, r) * 1.5))   # the glass rim
                else:
                    level = 1 + round(lit(dx, dy, r) * 1.2)                 # the tar inside
                    p.put(x, y, TAR, max(0, level))
    for y in range(3, 6):                                              # the neck
        for x in range(4, 7):
            p.put(x, y, STEEL, 7 if x == 4 else 5)
    for x in range(3, 8):                                              # the cork, a cog's rim
        p.put(x, 1, BRASS, 4 if x < 5 else 3)
        p.put(x, 2, BRASS, 3 if x < 5 else 2)
    p.put(4, 0, BRASS, 4)
    p.put(6, 0, BRASS, 3)
    p.outline()
    p.put(3, 8, STEAM, 2, lock=True)                                   # the glass's glint
    p.put(3, 9, STEEL, 8, lock=True)
    p.put(6, 11, TAR, 4, lock=True)                                    # the tar's sheen
    return p.image()


def buff_icon():
    p = Pix(16, 16)
    for y in range(1, 15):                                             # the shield: wide at the top, a point below
        half = 6.5 if y < 8 else 6.5 - (y - 8) * 0.95
        for x in range(16):
            dx = x + 0.5 - 8.0
            if abs(dx) <= half:
                edge = abs(dx) > half - 1.2 or y < 2 or (y >= 8 and abs(dx) > half - 1.6)
                if edge:
                    p.put(x, y, BRASS, 3 + round(lit(dx, y - 7.5, 7.0) * 1.5))
                else:
                    p.put(x, y, STEEL, 4 + round(lit(dx, y - 7.5, 7.0) * 1.2))
    drop = {3: (7, 8), 4: (7, 8), 5: (6, 9), 6: (6, 9), 7: (5, 10), 8: (5, 10), 9: (5, 10), 10: (6, 9), 11: (7, 8)}
    for y, (x0, x1) in drop.items():                                   # a drop of tar on it
        for x in range(x0, x1 + 1):
            p.put(x, y, TAR, 1 + round(lit(x + 0.5 - 7.5, y + 0.5 - 7.5, 3.5) * 1.3))
    p.outline()
    p.put(6, 6, STEAM, 1, lock=True)                                   # the drop's glint
    p.put(6, 7, TAR, 4, lock=True)
    return p.image()


def export_all():
    images = [cogfish(), potion(), buff_icon()]
    export(images[0], "Content/Junkyard/Items/Cogfish.png")
    export(images[1], "Content/Junkyard/Items/TarImmunityPotion.png")
    export(images[2], "Content/Junkyard/Buffs/TarImmunity.png")
    return images


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    imgs = export_all()
    if a.preview:
        preview(imgs, a.preview, scale=8)
