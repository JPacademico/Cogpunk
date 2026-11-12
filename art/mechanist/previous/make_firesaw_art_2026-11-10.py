"""Source for the Firesaw (D4). Redrawn 2026-11-10 (user, with a reference image of a chainsaw greatsword called "Flame":
"redesign the firesaw, it needs more steampunk ... it should slash like a sword now (cool animation like the melee rework
mods do), and on the right mouse button it should gain a fire effect that increases range and applies fire on the
enemy"). The 2026-11-09 look (a held chainsaw pointing right) is kept in previous/make_firesaw_art_2026-11-09.py. Run from
the repo root:

    python -P art/mechanist/make_firesaw_art.py [--preview FILE]

A chainsaw greatsword drawn along the sprite's diagonal, pointing top-right like every swung sword (D4 rule 8):
- a red fuel canister for a pommel (lit red lacquer, a brass neck, an ember flame stamped on it);
- a leather-wrapped grip, and a brass fuel line running beside it from the canister's neck to the engine;
- the engine as the guard: a brass-framed housing across the blade painted with yellow-and-black hazard stripes, rivets in
  its corners, a pressure gauge with its needle in the red, and a steam chimney with a brass cap off its lit side;
- the bar: a brass ferrule where it leaves the engine, a long steel blade lit along its spine, a row of punched holes down
  its middle, and the chain along its cutting edge (the lower-right side, which leads a down-swing: SwingPose's "below"
  side), a tooth sticking out every third link, the bar rounding off at the nose.
Three frames: the chain runs a link a frame towards the nose (links and teeth repeat every three, so it loops). The fire
overlay (right click): flames licking off the teeth, heat along the spine and a jet of fire past the nose, two tiles long
(+32 game px), three flickering frames, drawn at full brightness in game (it is light). Lit from the top-left, ramp-0
outlines (a lighter outline on the lit spine), at most 16 colours per sprite (D4 rule 5).

Coordinates: across the blade t = x + y (the axis is t = AXIS; less is the lit upper-left side, a = t - AXIS), along it
s = x - y (the canister's end -34, the nose +37). Every part is a band of s and a, so its edges cross the blade square.

Outputs (Content/Mechanist/Weapons/):
    Firesaw.png         the item (frame 0), 80x80
    FiresawSwing.png    3 frames (the chain running), 80x80 each, 2 px under each: drawn in the hand by the game
    FiresawFire.png     3 frames of the fire overlay, 104x104 each (the saw's frame grown up and right for the jet; their
                        bottom-left corners meet), 2 px under each
Constants the game uses (Content/Mechanist/Weapons/Firesaw.cs): the grip (the swing's pivot), the blade's span, the jet.
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

OUT = "Content/Mechanist/Weapons/"
SIZE = 40                         # the saw's frame (1x)
AXIS = 39                         # t on the blade's axis (the diagonal from the bottom-left corner to the top-right)
FIRE_SIZE = 52                    # the fire's frame (1x): the saw's grown 12 px up and right, its bottom-left corner shared
FIRE_SHIFT = FIRE_SIZE - SIZE     # the saw's pixel (x, y) is the fire frame's (x, y + FIRE_SHIFT)
GRIP_S = -17                      # the hand on the axis: pixel (11, 28), the swing's pivot
FRAMES = 3
NOSE_S = 37                       # the blade's tip
JET_S = 60                        # the jet's end: 23 s-steps past the nose = 16 art px = 32 game px (two tiles)
ST, G, K, HD, E, S = (RAMP[k] for k in ("steel", "gilt", "crimson", "hide", "ember", "steam"))

CAN = (-34, -25, 4)               # the fuel canister: s from, s to, half-width in a
CAN_STRAP = (-30, -29)            # a brass strap round its middle
NECK = (-24, -23, 3)              # its brass neck
GRIP = (-22, -13, 2)              # the leather grip
HOSE = (-24, -12)                 # the fuel line, at a = 5 (its outline at 6)
HOUSING = (-12, -2, 9)            # the engine housing (the guard)
CHIMNEY = (-8, -6, -13)           # the steam chimney: s from, s to, its outer a (it rises from the housing's lit side)
BLADE = (-1, NOSE_S)              # the bar: a from -6 (the spine) to 5 (the chain's links), the teeth at 6
FERRULE = (-1, 0)                 # the brass collar where the bar leaves the engine


def blade_span(s):
    """The bar's extent across at s: (spine a, links a); the nose rounds off the last six steps."""
    d = NOSE_S - s
    cut = max(0, 6 - d)
    return -6 + cut, 5 - cut // 2


def part_at(x, y):
    """Which part the pixel (x, y) of the saw's frame belongs to, or None."""
    if not (0 <= x < SIZE and 0 <= y < SIZE):
        return None
    t, s = x + y, x - y
    a = t - AXIS
    if CAN[0] <= s <= CAN[1] and abs(a) <= CAN[2]:
        if s in (CAN[0], CAN[1]) and abs(a) == CAN[2]:
            return None                                            # the cylinder's rounded rims
        return "strap" if CAN_STRAP[0] <= s <= CAN_STRAP[1] else "can"
    if NECK[0] <= s <= NECK[1] and abs(a) <= NECK[2]:
        return "neck"
    if GRIP[0] <= s <= GRIP[1] and abs(a) <= GRIP[2]:
        return "grip"
    if HOSE[0] <= s <= HOSE[1] and a in (5, 6) and not (s <= NECK[1] and a == 6):
        return "hose"
    if HOUSING[0] <= s <= HOUSING[1] and abs(a) <= HOUSING[2]:
        return "housing"
    if CHIMNEY[0] <= s <= CHIMNEY[1] and CHIMNEY[2] <= a < -HOUSING[2]:
        return "chimney"
    if BLADE[0] <= s <= BLADE[1]:
        lo, hi = blade_span(s)
        if lo <= a <= hi:
            return "ferrule" if FERRULE[0] <= s <= FERRULE[1] else "blade"
        if a == hi + 1 and s <= NOSE_S - 2 and ((s - BLADE[0]) // 2) % 3 == 0:
            return "tooth"                                         # placed per frame below (the chain runs)
    return None


def is_out(x, y, part):
    """True if a 4-neighbour of (x, y) is not this part: the part's outline."""
    return any(part_at(x + dx, y + dy) != part for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def saw(k):
    """Frame k: the chain run k links towards the nose."""
    px = {}
    for y in range(SIZE):
        for x in range(SIZE):
            part = part_at(x, y)
            if part is None or part == "tooth":
                continue
            t, s = x + y, x - y
            a = t - AXIS
            out = is_out(x, y, part)
            if part == "can":                                      # red lacquer, lit from the top-left
                if out:
                    px[(x, y)] = K[3] if a < -2 else K[0]
                else:
                    px[(x, y)] = K[5] if a <= -2 else (K[3] if a <= 2 else K[0])
            elif part in ("neck", "strap"):
                px[(x, y)] = G[1] if out and a >= 0 else (G[7] if a < 0 else G[4])
            elif part == "grip":                                   # leather wraps, a darker turn every third step
                if out:
                    px[(x, y)] = HD[0]
                else:
                    px[(x, y)] = HD[2] if (s - GRIP[0]) % 3 == 0 else (HD[4] if a <= 0 else HD[2])
            elif part == "hose":
                px[(x, y)] = G[7] if a == 5 else G[1]
            elif part == "housing":                                # a brass frame round hazard stripes
                frame = abs(a) >= HOUSING[2] - 1 or s in (HOUSING[0], HOUSING[1])
                if out:
                    px[(x, y)] = G[4] if a < -2 and s > HOUSING[0] else G[1]
                elif frame:
                    px[(x, y)] = G[7] if a < 0 or s == HOUSING[0] else G[4]
                else:
                    px[(x, y)] = E[3] if (x // 2) % 2 == 0 else ST[0]   # upright stripes: diagonal across the housing
            elif part == "chimney":
                if a == CHIMNEY[2]:
                    px[(x, y)] = G[7] if s < CHIMNEY[1] else G[1]  # its brass cap
                else:
                    px[(x, y)] = ST[0] if out and s == CHIMNEY[1] else (ST[6] if s == CHIMNEY[0] else ST[4])
            elif part == "ferrule":
                px[(x, y)] = G[1] if out and a > 0 else (G[9] if a <= -4 else (G[7] if a <= 1 else G[4]))
            else:                                                  # the bar
                lo, hi = blade_span(s)
                step = (s - BLADE[0]) // 2
                if a == lo:
                    px[(x, y)] = ST[4]                             # the spine: a lighter outline on the lit side
                elif a == lo + 1:
                    px[(x, y)] = ST[8]
                elif a <= -2:
                    px[(x, y)] = ST[6]
                elif a <= 1:
                    px[(x, y)] = ST[4]
                elif a < hi - 1:
                    px[(x, y)] = ST[2]
                elif a == hi - 1:
                    px[(x, y)] = ST[2] if (step + k) % 3 else ST[4]   # the chain's rivets catch the light, running
                else:
                    px[(x, y)] = ST[0]                             # the links' outer edge
    for y in range(SIZE):                                          # the teeth: every third link, running with the chain
        for x in range(SIZE):
            t, s = x + y, x - y
            a = t - AXIS
            if not (BLADE[0] <= s <= NOSE_S - 2):
                continue
            lo, hi = blade_span(s)
            step = (s - BLADE[0]) // 2
            if a == hi + 1:
                phase = (step + k) % 3
                if phase == 0:
                    px[(x, y)] = ST[6]                             # a tooth's bright cutting tip...
                elif phase == 1:
                    px[(x, y)] = ST[2]                             # ...and its body, then a gap
    # stamped details (after the parts: 1 px features)
    for s in range(BLADE[0] + 5, NOSE_S - 6, 6):                   # the punched holes down the bar's middle
        a = -1
        if (AXIS + a + s) % 2:
            s += 1
        x, y = (AXIS + a + s) // 2, (AXIS + a - s) // 2
        if (x, y) in px:
            px[(x, y)] = ST[0]
            if (x, y + 1) in px:
                px[(x, y + 1)] = ST[2]                             # the hole's lit lower lip
    for (s, a) in ((HOUSING[0] + 1, -7), (HOUSING[1] - 1, -7), (HOUSING[0] + 1, 7), (HOUSING[1] - 1, 7)):   # rivets
        if (AXIS + a + s) % 2:
            a += 1
        x, y = (AXIS + a + s) // 2, (AXIS + a - s) // 2
        if (x, y) in px:
            px[(x, y)] = G[9] if a < 0 else G[7]
    gx, gy = (AXIS - 4 - 7) // 2, (AXIS - 4 + 7) // 2              # the pressure gauge on the housing's lit side
    for (dx, dy, col) in ((0, 0, ST[8]), (1, 0, ST[8]), (0, 1, ST[8]), (1, 1, K[3]), (-1, 0, G[1]), (2, 0, G[1]), (0, -1, G[1]),
                          (1, -1, G[1]), (-1, 1, G[1]), (2, 1, G[1]), (0, 2, G[1]), (1, 2, G[1])):
        if (gx + dx, gy + dy) in px:
            px[(gx + dx, gy + dy)] = col
    fx, fy = (AXIS - 1 - 32) // 2, (AXIS - 1 + 32) // 2            # the ember flame stamped on the canister
    for (dx, dy, col) in ((0, -1, E[3]), (0, 0, E[3]), (-1, 0, K[5]), (1, 0, K[5]), (0, 1, E[3])):
        if (fx + dx, fy + dy) in px:
            px[(fx + dx, fy + dy)] = col
    return to_image(px, 0, 0, SIZE, SIZE)


TONGUES = (2, 3, 4, 3, 2, 4, 5, 3, 2, 3, 4, 2)


def fire(k):
    """The flames off the teeth, heat along the spine and the jet past the nose, frame k (in the fire frame: the saw's
    shifted down FIRE_SHIFT). Ember 1..3 and steam white at the hottest (no outline: light)."""
    px = {}
    for y in range(FIRE_SIZE):
        for x in range(FIRE_SIZE):
            sy = y - FIRE_SHIFT                                    # the same point in the saw's frame
            t, s = x + sy, x - sy
            a = t - AXIS
            if BLADE[0] + 1 <= s <= NOSE_S:
                lo, hi = blade_span(s)
                step = (s - BLADE[0]) // 2
                h = TONGUES[(step * 5 + k * 7) % len(TONGUES)]     # uneven tongues off the teeth, flickering frame by frame
                d = a - hi
                if 1 <= d <= h:
                    px[(x, y)] = S[3] if d == 1 and (step + k) % 4 == 0 else (E[3] if d <= 2 else (E[2] if d < h else E[1]))
                elif d <= 0 and a >= hi - 1 and (step + k) % 2 == 0:
                    px[(x, y)] = E[3]                              # the links glowing
                elif a == lo - 1 and (step * 3 + k) % 4 == 0:
                    px[(x, y)] = E[2]                              # a lick of heat along the spine
            elif NOSE_S < s <= JET_S:                              # the jet: a tapering tongue along the axis
                u = (s - NOSE_S) / float(JET_S - NOSE_S)
                flick = 0.7 if ((s // 2) * 7 + k * 5) % 9 < 3 else 0.0
                r = max(0.6, 5.0 * (1.0 - u) + flick)
                dd = abs(a + 1.0) / r
                if dd <= 1.0:
                    px[(x, y)] = S[3] if dd < 0.32 and u < 0.5 else (E[3] if dd < 0.6 else (E[2] if dd < 0.85 else E[1]))
    return to_image(px, 0, 0, FIRE_SIZE, FIRE_SIZE)


def export_all():
    frames = [saw(k) for k in range(FRAMES)]
    export(frames[0], OUT + "Firesaw.png")
    export(vertical(frames), OUT + "FiresawSwing.png")
    export(vertical([fire(k) for k in range(FRAMES)]), OUT + "FiresawFire.png")


def preview(path):
    """Each frame plain and burning, over dark and light (5x)."""
    cells = []
    for bg in ((36, 40, 48, 255), (150, 180, 210, 255)):
        for k in range(FRAMES):
            plain = Image.new("RGBA", (FIRE_SIZE + 4, FIRE_SIZE + 4), bg)
            plain.alpha_composite(saw(k), (2, 2 + FIRE_SHIFT))
            hot = Image.new("RGBA", (FIRE_SIZE + 4, FIRE_SIZE + 4), bg)
            hot.alpha_composite(saw(k), (2, 2 + FIRE_SHIFT))
            hot.alpha_composite(fire(k), (2, 2))
            cells += [plain, hot]
    cw, ch = cells[0].size
    sheet = Image.new("RGBA", (cw * FRAMES * 2, ch * 2), (0, 0, 0, 255))
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % (FRAMES * 2)) * cw, (i // (FRAMES * 2)) * ch))
    sheet.resize((sheet.width * 5, sheet.height * 5), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
