"""Source for the Bottle of Lost Souls (D4), the Cursed Conductor's Expert item (user, 2026-11-06). Run from the repo root:

    python -P art/bosses/cursedconductor/make_lost_souls_art.py

A corked glass flask of ghost-green mist with two lost souls circling inside (the passengers the ghost train never let
off), a brass collar, and a punched railway ticket hanging from it on a string. Drawn at 1x in palette letters and
exported at 2x nearest-neighbour; lit from the top-left; every material outlined in its own ramp's darkest shade.

Output: Content/Bosses/CursedConductor/Items/BottleOfLostSouls.png, 36x144: four frames of 36x34 with 2 px under each
(vanilla's DrawAnimationVertical takes the cell height minus 2), 6 ticks a frame in BottleOfLostSouls.cs. The souls move
by whole pixels round a fixed orbit; the mist, the glass and the glints never move (stable pixels, D4 rule 17).
"""
import math
import os

from PIL import Image

ROOT = os.getcwd()
OUT = "Content/Bosses/CursedConductor/Items/BottleOfLostSouls.png"
W, H, FRAMES, PAD = 18, 17, 4, 1           # art px; PAD rows under each frame (2 px at 2x)

PAL = {                                      # art/palettes/cogpunk.gpl
    "O": (76, 40, 22), "c": (146, 86, 42), "h": (212, 154, 90),                  # Oak 1, 3, 5: the cork
    "B": (90, 58, 23), "b": (184, 138, 51), "y": (223, 185, 78),                 # Brass 1, 3, 4: the collar
    "G": (10, 34, 32), "1": (18, 70, 58), "2": (30, 114, 88), "3": (58, 166, 118),
    "4": (118, 220, 162), "5": (196, 250, 214),                                  # Ghost 0-5: glass and mist
    "w": (238, 241, 243),                                                        # Steam 2: the glass's glint
    "t": (228, 218, 192), "r": (168, 44, 42),                                    # Ivory 4, Crimson 3: the ticket
}

# The flask's outline per row: (left x, right x) of the silhouette, outline included.
PROFILE = {
    0: (6, 9), 1: (6, 9), 2: (6, 9),         # cork
    3: (5, 10), 4: (5, 10),                  # brass collar
    5: (6, 9), 6: (6, 9),                    # neck
    7: (4, 11), 8: (3, 12),                  # shoulder
    9: (2, 13), 10: (2, 13), 11: (2, 13), 12: (2, 13), 13: (2, 13), 14: (2, 13),
    15: (3, 12), 16: (4, 11),
}
BELLY_C = (7.5, 11.8)                        # the orbit's centre
ORBIT = (2.6, 2.0)


def base():
    g = [["."] * W for _ in range(H)]
    for y, (l, r) in PROFILE.items():
        for x in range(l, r + 1):
            g[y][x] = "G"
    # cork: rows 0-2, outline O, lit top-left
    for y in range(0, 3):
        l, r = PROFILE[y]
        for x in range(l, r + 1):
            edge = y == 0 or x in (l, r)
            g[y][x] = "O" if edge else ("h" if (x == l + 1 and y == 1) else "c")
    g[1][8] = "c"
    g[2][7] = "c"
    # brass collar: rows 3-4
    for y in (3, 4):
        l, r = PROFILE[y]
        for x in range(l, r + 1):
            edge = x in (l, r) or y == 4 and x in (l, r)
            g[y][x] = "B" if edge else ("y" if y == 3 and x <= l + 2 else "b")
    g[4][l + 1] = "b"
    # glass interior (neck and belly): mist darker at the walls and to the bottom-right, brighter up the middle
    for y in range(5, 17):
        l, r = PROFILE[y]
        for x in range(l + 1, r):
            if y == 16:
                continue
            nx = (x + 0.5 - BELLY_C[0]) / 5.5
            ny = (y + 0.5 - BELLY_C[1]) / 4.8
            wall = x == l + 1 or x == r - 1 or y == 15 or (y in (7, 8) and (x <= l + 1 or x >= r - 1))
            glow = 1.0 - (nx * nx + ny * ny) * 0.9 - 0.3 * (nx + ny)
            if y <= 6:
                ch = "1" if x == r - 1 else "2"
            elif wall:
                ch = "1" if (nx + ny) > -0.3 else "2"
            elif glow > 0.95:
                ch = "3"
            elif glow > 0.3:
                ch = "2"
            else:
                ch = "1"
            g[y][x] = ch
    # the glass's glints: a curved streak up the lit shoulder, a fleck on the shaded side
    for (x, y) in ((3, 9), (3, 10), (4, 8), (7, 5)):
        g[y][x] = "w"
    g[13][12] = "4"
    g[11][12] = "3"
    # the ticket on its string, hanging off the collar's right end: ivory card, a crimson stripe, the conductor's punch
    for (x, y) in ((11, 4), (12, 4), (13, 5)):
        g[y][x] = "B"
    for y in range(5, 10):
        for x in range(14, 18):
            edge = x in (14, 17) or y in (5, 9)
            g[y][x] = "B" if edge else "t"
    g[7][15] = "r"
    g[7][16] = "r"
    g[6][16] = "B"
    return g


SOUL = [".4.",
        "454",
        ".4."]


def frame(k):
    g = [row[:] for row in base()]
    for s in range(2):
        a = (k / FRAMES + s * 0.5) * 2 * math.pi
        cx = BELLY_C[0] + math.cos(a) * ORBIT[0]
        cy = BELLY_C[1] + math.sin(a) * ORBIT[1]
        ox, oy = int(round(cx - 1.5)), int(round(cy - 1.5))
        # the tail: two pixels behind the soul along its orbit, fading (the souls circle clockwise on screen)
        for back, ch in ((0.85, "4"), (1.45, "3")):
            ta = a - back
            tx = int(round(BELLY_C[0] + math.cos(ta) * ORBIT[0] - 0.5))
            ty = int(round(BELLY_C[1] + math.sin(ta) * ORBIT[1] - 0.5))
            if g[ty][tx] in "123":
                g[ty][tx] = ch
        for dy, row in enumerate(SOUL):
            for dx, ch in enumerate(row):
                x, y = ox + dx, oy + dy
                if ch != "." and g[y][x] in "123":
                    g[y][x] = ch
    return g


def main():
    sheet = Image.new("RGBA", (W, (H + PAD) * FRAMES), (0, 0, 0, 0))
    px = sheet.load()
    for k in range(FRAMES):
        g = frame(k)
        for y in range(H):
            for x in range(W):
                if g[y][x] != ".":
                    px[x, k * (H + PAD) + y] = PAL[g[y][x]] + (255,)
    out = os.path.join(ROOT, OUT)
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out)
    print("wrote %s (%dx%d)" % (OUT, sheet.width * 2, sheet.height * 2))


if __name__ == "__main__":
    main()
