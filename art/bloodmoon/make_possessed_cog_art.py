"""Source for the Possessed Cog, the Mechromancer's yoyo (D4). Run from the repo root:

    python -P art/bloodmoon/make_possessed_cog_art.py [--preview FILE]

Design (user, 2026-11-16: "a chance to drop 'possessed cog' an yoyo weapon that pierces instead of bouncing off enemies";
the look is my call): a brass cog of eight teeth with a soul trapped in its hub: a ghost-green eye glaring out of a dark
socket, the cog wreathed in soul fire like its master's Soul Fire Cogs. Lit from the top-left, gilt ramp, ramp-0 outline.

Outputs (1x art exported 2x nearest-neighbour):
    Content/BloodMoon/Projectiles/PossessedCogYoyo.png        4 spin frames, 13x13 cells, 1 px under each (11.25 degrees a
                                                              frame: the eight teeth make 45 degrees a full turn, so it loops)
    Content/BloodMoon/Projectiles/PossessedCogYoyo_Glow.png   its soul fire (added onto the scene), the same cells
    Content/BloodMoon/Projectiles/PossessedCogYoyo_Eye.png    the hub's eye, 5x5 cells: 0 centre, 1-8 the pupil towards the
                                                              heading's eighth (0 = right, then clockwise on screen)
    Content/BloodMoon/Weapons/PossessedCog.png                 the inventory icon: the cog, its eye and a loop of string
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, Canvas  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/BloodMoon/"
G, GH, ST, IV, K = RAMP["gilt"], RAMP["ghost"], RAMP["steel"], RAMP["ivory"], RAMP["crimson"]

CELL = 13
SPIN = 4
EYE = 5


def cog(cv, cx, cy, rot, body_r=4.5, tooth=1.3, hub_r=2.0, teeth=8):
    """A brass cog centred on (cx, cy) (pixel centres at +0.5), its teeth turned `rot` degrees: the rim lit from the
    top-left in four gilt steps, a dark groove ring inside the rim, spokes, the hub's socket left dark for the eye (the
    eye sheet is drawn over it); ramp-0 outline round the outside and the socket."""
    inside = {}
    for y in range(int(cy - body_r - tooth - 2), int(cy + body_r + tooth + 3)):
        for x in range(int(cx - body_r - tooth - 2), int(cx + body_r + tooth + 3)):
            du, dv = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(du, dv)
            th = math.degrees(math.atan2(dv, du)) - rot
            is_tooth = math.cos(math.radians(th * teeth)) > 0.3
            outer = body_r + (tooth if is_tooth else 0.0)
            if r <= outer:
                inside[(x, y)] = (du, dv, r, is_tooth)
    for (x, y), (du, dv, r, is_tooth) in inside.items():
        edge = any((x + ox, y + oy) not in inside for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            cv.put(x, y, G[0])
            continue
        if r < hub_r:
            cv.put(x, y, ST[1] if r < hub_r - 0.8 else G[1])           # the socket (the eye goes over it)
            continue
        light = -(du * 0.62 + dv * 0.78) / max(0.8, r)
        if body_r - 1.6 <= r < body_r - 0.8 and not is_tooth:
            k = 3 if light > 0 else 2                                  # the groove inside the rim
        elif hub_r <= r < hub_r + 0.9:
            k = 7 if light > 0.2 else 5                                # the hub's raised collar
        else:
            k = max(4, min(8, 6 + int(round(light * 2.2))))
        cv.put(x, y, G[k])
    return inside


def soul_ring(glow, cx, cy, k, r0=5.8, r1=6.5):
    """Soul fire round the cog: two flickering bands, their bright licks a different few each frame."""
    for y in range(CELL):
        for x in range(CELL):
            du, dv = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(du, dv)
            if r0 <= r <= r1:
                th = (math.degrees(math.atan2(dv, du)) + k * 22.5) % 360
                band = int(th // 30) % 3
                if band == 0:
                    glow.put_glow(x, y, GH[4] if r < (r0 + r1) / 2 else GH[3])
                elif band == 1:
                    glow.put_glow(x, y, GH[3])


def spin_frame(k):
    cv, glow = Canvas(), Canvas()
    c = CELL / 2.0
    cog(cv, c, c, k * 45.0 / SPIN)
    soul_ring(glow, c, c, k)
    for (x, y) in list(glow.glow):
        if (x, y) in cv.px:
            del glow.glow[(x, y)]                                      # the fire never covers the brass
            glow.px.pop((x, y), None)
    return cv, glow


# The eye: a ghost-green iris in a dark ring, a black pupil, a white glint up-left (the light). The pupil moves one
# pixel towards the heading.
DIRS = [(0, 0), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def eye_frame(k):
    cv = Canvas()
    for y in range(EYE):
        for x in range(EYE):
            r = math.hypot(x + 0.5 - EYE / 2.0, y + 0.5 - EYE / 2.0)
            if r <= 2.5:
                cv.put(x, y, GH[0] if r > 1.9 else GH[3] if (x + y) < 4 else GH[2])
    dx, dy = DIRS[k]
    px, py = 2 + dx, 2 + dy
    cv.put(px, py, ST[0])
    gx, gy = (1, 1) if (dx, dy) != (-1, -1) else (2, 1)
    if (gx, gy) != (px, py):
        cv.put(gx, gy, GH[5])
    return cv


def sheet(canvases, cell, glow=False):
    im = Image.new("RGBA", (cell, (cell + 1) * len(canvases) - 1), (0, 0, 0, 0))
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        for (x, y), col in src.items():
            if 0 <= x < cell and 0 <= y < cell:
                im.putpixel((x, y + k * (cell + 1)), col + (255,))
    return im


def icon():
    """16x16: the cog (a bigger one) with its eye looking at the viewer and a loop of crimson string over its top right."""
    cv = Canvas()
    cog(cv, 7.0, 9.0, 11.25, body_r=4.4, tooth=1.5, hub_r=2.0)
    e = eye_frame(0)
    for (x, y), col in e.px.items():
        cv.put(x + 5, y + 7, col)
    # the string: from the hub up and right to a loop at the corner (2 px wide where it bends, crimson with a lit side)
    pts = [(9, 4), (10, 3), (11, 2), (12, 1), (13, 1), (14, 2), (14, 3), (13, 4), (12, 4), (11, 3)]
    for i, (x, y) in enumerate(pts):
        if (x, y) not in cv.px or cv.px[(x, y)] == G[0]:
            cv.put(x, y, K[4] if i % 3 else K[3])
    for (x, y) in ((15, 2), (15, 3), (14, 4), (13, 5), (12, 0), (13, 0), (14, 1), (11, 1)):
        if (x, y) not in cv.px:
            cv.put(x, y, K[1])                                          # its dark outline side
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (x, y), col in cv.px.items():
        if 0 <= x < 16 and 0 <= y < 16:
            im.putpixel((x, y), col + (255,))
    return im


def export_all():
    frames = [spin_frame(k) for k in range(SPIN)]
    export(sheet([f[0] for f in frames], CELL), OUT + "Projectiles/PossessedCogYoyo.png")
    export(sheet([f[1] for f in frames], CELL, glow=True), OUT + "Projectiles/PossessedCogYoyo_Glow.png")
    export(sheet([eye_frame(k) for k in range(len(DIRS))], EYE), OUT + "Projectiles/PossessedCogYoyo_Eye.png")
    export(icon(), OUT + "Weapons/PossessedCog.png")


def preview(path, scale=8):
    frames = [spin_frame(k) for k in range(SPIN)]
    w = (CELL + 2) * SPIN + 18
    img = Image.new("RGBA", (w, CELL + 22), (30, 30, 36, 255))
    for k, (cv, glow) in enumerate(frames):
        for (x, y), col in list(cv.px.items()) + list(glow.glow.items()):
            img.putpixel((x + k * (CELL + 2) + 1, y + 1), col + (255,))
        e = eye_frame(1 + k * 2)
        for (x, y), col in e.px.items():
            img.putpixel((x + k * (CELL + 2) + 5, y + 5), col + (255,))
    img.alpha_composite(icon(), (SPIN * (CELL + 2) + 1, 2))
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
