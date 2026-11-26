"""Source for the Cogspring Sword (D4), 2026-11-19. Run from the repo root:

    python -P art/mechanist/make_cogspring_art.py [--preview FILE]

User, 2026-11-19: "add a new weapon called "Cogspring sword" a sword mechanist weapon (under molten sword, 12% less dps on
basic attacks) that can charge attack at right mouse for up to 4x the damage ... example image on the prompt for design.
crafts with brass + rusted cogs + chains". The design (reference/cogspring_sword_user_2026-11-19.png): a steampunk sabre in
bronze, a wrapped grip inside a curved knuckle guard, a hilt block with green lights and a big cog on its back, a round
glowing core (a lightning bolt in a ring of lights) where the blade starts, and a broad straight blade with a clipped tip,
a patina-green panel of circuit lines down its middle and a glowing line along the edge side.

Drawn along the sprite's diagonal, pointing top-right like every swung sword (D4 rule 8), the Firesaw's way: across the
blade t = x + y (the axis is t = AXIS; a = t - AXIS, less is the lit upper-left side), along it s = x - y (the pommel's end
-34, the tip +31); each part is a band of s and a, so its edges cross the blade square; round parts (the cog, the core) are
circles in pixel space. Lit from the top-left, ramp-0/1 outlines, Cogpunk palette (gilt for the bronze, verd for the
patina, hide for the wrap, ghost for the green light).

Outputs (Content/Mechanist/Weapons/):
    CogspringSword.png        the sword, 80x80: the item and the sprite drawn in the hand
    CogspringSword_Glow.png   its lights alone (the core, the hilt's lamps, the edge line), drawn full-bright in game,
                              brighter as the charge builds
    CogspringTrail.png        the phantom slash (0.2.2): TRAIL_FRAMES green crescents, each TRAIL_STEP degrees longer,
                              pivoting on the sprite's bottom-left corner (where vanilla holds a swung item), drawn added
Constants the game uses (CogspringSword.cs): the grip (GRIP_S on the axis: the swing's pivot), the blade's span.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

OUT = "Content/Mechanist/Weapons/"
SIZE = 40                          # the frame (1x)
AXIS = 39                          # t on the blade's axis (the diagonal from the bottom-left corner to the top-right)
G, V, HD, GH = (RAMP[k] for k in ("gilt", "verd", "hide", "ghost"))

POMMEL = (-38, -34, 3)             # s from, s to, half-width in a
GRIP = (-33, -22, 2)
GRIP_S = -27                       # the hand on the axis: the swing's pivot
DGUARD = (-31, -19)                # the knuckle guard's bar, at a 5..6, joined to the pommel and the hilt
HILT = (-21, -15, 5)
COG = (7, 25, 4.6, 3.3)            # centre pixel (s -18, a -7), tooth radius, body radius
# The cog, stamped by hand (a 10 x 10 gear reads at this size where a computed one blurs): four square teeth on the
# sides, four on the corners, the axle hole in the middle; placed with its top-left at COG_AT.
COG_ROWS = ("....XX....",
            ".X..XX..X.",
            ".XXXXXXXX.",
            "..XXXXXX..",
            "XXXX..XXXX",
            "XXXX..XXXX",
            "..XXXXXX..",
            ".XXXXXXXX.",
            ".X..XX..X.",
            "....XX....")
COG_PX = {(x, y) for y, r in enumerate(COG_ROWS) for x, c in enumerate(r) if c == "X"}
COG_AT = (2, 20)
CORE = (15, 24, 5.3, 3.2)          # centre pixel (s -9, a 0), ring radius, light radius
BLADE = (-3, 35, 4)                 # s from, the spine's tip, half-width in a
PANEL = (2, -2, 1)                 # the patina panel: from s 6, a -2 .. 1, to 3 short of the tip's cut
GLOW_A = 2                         # the glowing line along the edge side


def blade_end(a):
    """The blade's last s at a: the clipped tip, the spine reaching furthest."""
    return BLADE[1] - (a + BLADE[2])


def part_at(x, y):
    if not (0 <= x < SIZE and 0 <= y < SIZE):
        return None
    t, s = x + y, x - y
    a = t - AXIS
    if math.hypot(x - CORE[0], y - CORE[1]) <= CORE[2]:
        return "core"
    if (x - COG_AT[0], y - COG_AT[1]) in COG_PX:
        return "cog"
    if HILT[0] <= s <= HILT[1] and abs(a) <= HILT[2]:
        return "hilt"
    if BLADE[0] <= s and -BLADE[2] <= a <= BLADE[2] and s <= blade_end(a):
        return "blade"
    if GRIP[0] <= s <= GRIP[1] and abs(a) <= GRIP[2]:
        return "grip"
    if POMMEL[0] <= s <= POMMEL[1] and abs(a) <= POMMEL[2]:
        if s == POMMEL[0] and abs(a) >= 2:
            return None                                            # its rounded end
        return "pommel"
    if DGUARD[0] <= s <= DGUARD[1] and a in (5, 6):
        return "dguard"
    if s in (-33, -32) and 3 <= a <= 6:
        return "dguard"                                            # the bar's root at the pommel
    if s in (-21, -20) and a in (6, 7):
        return "dguard"                                            # and at the hilt
    return None


def is_out(x, y, part):
    return any(part_at(x + dx, y + dy) != part for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def sword():
    """(pixels, glow): {(x, y): colour}."""
    px, glow = {}, {}
    for y in range(SIZE):
        for x in range(SIZE):
            part = part_at(x, y)
            if part is None:
                continue
            t, s = x + y, x - y
            a = t - AXIS
            out = is_out(x, y, part)
            if part == "pommel":
                px[(x, y)] = G[1] if out and a >= 0 else (G[2] if out else (G[8] if a <= -1 else G[5]))
            elif part == "grip":                                   # leather wraps, a dark turn every third step
                if out:
                    px[(x, y)] = HD[0]
                else:
                    px[(x, y)] = HD[1] if (s - GRIP[0]) % 3 == 0 else (HD[4] if a < 0 else HD[2])
            elif part == "dguard":
                px[(x, y)] = G[6] if a <= 5 and not out else (G[4] if a <= 5 else G[1])
            elif part == "hilt":                                   # a bronze block: a frame round a darker plate
                frame = abs(a) >= HILT[2] - 1 or s in (HILT[0], HILT[1])
                if out:
                    px[(x, y)] = G[3] if a < -2 else G[1]
                elif frame:
                    px[(x, y)] = G[8] if a < 0 or s == HILT[0] else G[5]
                else:
                    px[(x, y)] = G[4] if a < 0 else G[3]
            elif part == "cog":
                cx, cy = x - COG_AT[0] - 4.5, y - COG_AT[1] - 4.5
                lit = cx + cy < 0
                if (x - COG_AT[0], y - COG_AT[1]) in ((4, 4), (5, 4), (4, 5), (5, 5)):
                    continue                                   # the axle hole (open)
                if out:
                    px[(x, y)] = G[4] if lit else G[1]
                elif math.hypot(cx, cy) <= 2.2:
                    px[(x, y)] = G[8] if lit else G[5]         # the hub
                else:
                    px[(x, y)] = G[7] if lit else G[4]
            elif part == "core":
                r = math.hypot(x - CORE[0], y - CORE[1])
                lit = (x - CORE[0]) + (y - CORE[1]) < -1
                if out:
                    px[(x, y)] = G[2] if lit else G[1]
                elif r > CORE[3] + 1.0:                            # the bronze ring, its lamps every other step
                    ang = math.atan2(y - CORE[1], x - CORE[0])
                    lamp = int(round((ang + math.pi) / (math.pi / 6))) % 2 == 0 and r > CORE[2] - 1.2
                    if lamp:
                        px[(x, y)] = GH[4]
                        glow[(x, y)] = GH[5]
                    else:
                        px[(x, y)] = G[7] if lit else G[4]
                elif r > CORE[3]:
                    px[(x, y)] = G[1]                              # the ring's inner lip
                else:
                    px[(x, y)] = GH[2] if r > 2.2 else GH[3]       # the light: a teal glass
                    glow[(x, y)] = GH[3] if r > 2.2 else GH[4]
            else:                                                  # the blade
                end = blade_end(a)
                if a == -BLADE[2] or (s == end and a < 0):
                    px[(x, y)] = G[5]                              # the spine: a lighter outline on the lit side
                elif out:
                    px[(x, y)] = G[1]
                elif a == -BLADE[2] + 1:
                    px[(x, y)] = G[9]                              # the spine's bright bevel
                elif a == BLADE[2] - 1:
                    px[(x, y)] = G[6]                              # the edge's bevel
                elif a == GLOW_A and BLADE[0] + 1 <= s <= end - 2:
                    px[(x, y)] = GH[4]
                    glow[(x, y)] = GH[5]
                elif PANEL[1] <= a <= PANEL[2] and PANEL[0] <= s <= end - 3:
                    edge = a in (PANEL[1], PANEL[2]) or s in (PANEL[0], end - 3)
                    trace = (s % 6 == 0 and a <= 0) or (a == -1 and s % 6 in (1, 2, 3))
                    px[(x, y)] = V[0] if edge else (V[2] if trace else V[1])
                else:
                    px[(x, y)] = G[7] if a < 0 else G[5]
    # stamped details (after the parts: 1 px features)
    for (s, a) in ((-20, -4), (-16, -4), (-20, 3), (-16, 3)):      # the hilt's lamps (green) in its plate
        if (AXIS + a + s) % 2:
            a += 1
        q = ((AXIS + a + s) // 2, (AXIS + a - s) // 2)
        if q in px:
            px[q] = GH[4]
            glow[q] = GH[5]
    bolt = tuple((x, y + 4) for (x, y) in ((15, 18), (14, 19), (15, 19), (16, 20), (15, 21), (16, 21), (15, 22)))
    for q in bolt:                                                 # the core's lightning bolt
        if q in px:
            px[q] = GH[5]
            glow[q] = (255, 255, 255) if q in ((15, 23), (16, 24)) else GH[5]
    return px, glow


# --- the phantom slash (0.2.2, user 2026-11-26: "add a phantom slash trail for the swings as it is a visual rule for our
# melee weapons"): the Firesaw's crescents (make_firesaw_art.py), pivoting where vanilla holds a swung sprite, its bottom-left
# corner on the blade's axis (the swing is vanilla's since 0.2.2), in the core's green light. Distances along the axis from
# the corner: (s + 40) / sqrt(2) at 1x, so the core's middle (s -9) is 21.9 and the tip (s 35) 53.0.
TRAIL_FRAMES = 8
TRAIL_STEP = 12                   # degrees: frame k spans (k + 1) * TRAIL_STEP (CogspringTrailLayer.TrailStep)
TRAIL_PAD = 2
TRAIL_IN = 22.0                   # 1x: from the core out
TRAIL_OUT = 53.5                  # 1x: the tip's track
PHANTOM = [GH[1], GH[2], GH[3], GH[4], GH[5]]        # dark to bright: the core's green light


def trail_geometry():
    """(width, height, pivot x, pivot y) of a crescent frame, in 1x pixels: the longest tail reaches back past the pivot."""
    span = math.radians(TRAIL_FRAMES * TRAIL_STEP)
    left = int(math.ceil(max(0.0, -TRAIL_OUT * math.cos(span)))) + TRAIL_PAD
    w = left + int(math.ceil(TRAIL_OUT)) + TRAIL_PAD
    top = int(math.ceil(TRAIL_OUT)) + TRAIL_PAD
    h = top + TRAIL_PAD
    return w, h, left, top


def crescent(k):
    """Frame k: the crescent spanning (k + 1) * TRAIL_STEP degrees behind a blade lying along +x from the pivot (a clockwise
    sweep on screen leaves it counter-clockwise behind the blade). Bright at the blade and towards the tip (the tip moves
    fastest), thinning from the inside and fading along the tail; every pixel a ramp colour (drawn added in game)."""
    w, h, px0, py0 = trail_geometry()
    span = math.radians((k + 1) * TRAIL_STEP)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = img.load()
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - px0, y + 0.5 - py0
            r = math.hypot(dx, dy)
            ang = math.atan2(-dy, dx)                    # counter-clockwise from the blade (screen y is down)
            if ang < -0.02 or ang > span or r > TRAIL_OUT:
                continue
            u = max(0.0, ang) / span                     # 0 at the blade, 1 at the tail's end
            inner = TRAIL_IN + (TRAIL_OUT - TRAIL_IN) * 0.8 * u ** 0.9
            if r < inner:
                continue
            depth = (r - TRAIL_IN) / max(1.0, TRAIL_OUT - TRAIL_IN)
            level = (1.0 - u) ** 1.1 * (0.15 + 0.85 * depth ** 1.6)
            if r > TRAIL_OUT - 1.3 and u < 0.55:         # the rim the tip draws: a bright line, fading along the tail
                level = max(level, 1.0 - u * 0.9)
            if ang * r < 1.2 and u < 0.2:                # the blade's own edge
                level = max(level, 0.8 * depth + 0.2)
            n = len(PHANTOM)
            idx = int(level * n + 0.15)
            if idx <= 0:
                continue
            p[x, y] = PHANTOM[min(n, idx) - 1] + (255,)
    return img


def export_all():
    px, glow = sword()
    img = to_image(px, 0, 0, SIZE, SIZE)
    gl = to_image(glow, 0, 0, SIZE, SIZE)
    export(img, OUT + "CogspringSword.png")
    export(gl, OUT + "CogspringSword_Glow.png")
    export(vertical([crescent(k) for k in range(TRAIL_FRAMES)]), OUT + "CogspringTrail.png")
    w, h, tx, ty = trail_geometry()
    print("trail: frame %dx%d 1x = TrailW %d, TrailH %d (game px); pivot (%d, %d) 1x = TrailPivotX %d, TrailPivotY %d"
          % (w, h, 2 * w, 2 * h, tx, ty, 2 * tx, 2 * ty))
    gx, gy = (AXIS + GRIP_S) / 2.0, (AXIS - GRIP_S) / 2.0
    tip = max(((x, y) for (x, y) in px), key=lambda q: q[0] - q[1])
    reach = math.hypot(tip[0] - gx, tip[1] - gy) * 2
    print("grip (1x) %.1f, %.1f -> GripX %d, GripY %d (2x); tip %s, reach from the grip %.0f px (2x)"
          % (gx, gy, round(gx * 2), round(gy * 2), tip, reach))
    return img, gl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    img, gl = export_all()
    if args.preview:
        sc = 8
        w = SIZE * sc
        sheet = Image.new("RGBA", (w * 3 + 40, w + 20), (20, 20, 24, 255))
        for i, bg in enumerate(((30, 30, 36), (196, 214, 232))):
            band = Image.new("RGBA", (w, w), bg + (255,))
            band.alpha_composite(img.resize((w, w), Image.NEAREST))
            sheet.alpha_composite(band, (10 + i * (w + 10), 10))
        lit = img.copy()
        lit.alpha_composite(gl)
        band = Image.new("RGBA", (w, w), (12, 12, 16, 255))
        band.alpha_composite(lit.resize((w, w), Image.NEAREST))
        sheet.alpha_composite(band, (10 + 2 * (w + 10), 10))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
