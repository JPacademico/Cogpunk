"""Source for the Cog-launcher and its cog (D4), 2026-11-05. Run from the repo root:

    python -P art/mechanist/make_cog_launcher_art.py [--preview FILE]

Design (user, 2026-11-05: "a mechanist class weapon that shoots a spinning cog, crafted using a musket + 8 brass bars + 4
polished metal + 23 rusted cogs"; the look is my call, drawn with the long ramps of docs/design/pixel-art-study.md):
* Cog-launcher (a gun: it points right, D4 rule 8): the Musket rebuilt. An oak stock with its grain and a gilt butt
  plate, a steel lock with a gilt pressure gauge (a white dial and a red needle), a gilt drum magazine on top with a cog
  showing in its window, a copper steam line from the drum to the barrel, a long steel barrel with two gilt bands and a
  wide flared muzzle, a steel trigger guard.
* Its cog: a polished cog of eight teeth (gilt, a steel hub and four spokes), lit from the top-left in every frame (the
  light does not spin with it), 4 frames of 11.25 degrees (an 8-tooth cog repeats every 45, so they loop), each drawn
  at its turn (never rotated as a bitmap).

Outputs:
    Content/Mechanist/Weapons/CogLauncher.png        56x24
    Content/Mechanist/Weapons/CogLauncherCog.png     4 frames, 24 px cells, stride 26
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, Xf, Poly, Ellipse, Union, box, Canvas, flat, dome, face, cyl, texture, glint, selout, lit, level  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

G, ST, OK, C, K, S = RAMP["gilt"], RAMP["steel"], RAMP["oak"], RAMP["copper"], RAMP["crimson"], RAMP["steam"]
GUN_W, GUN_H = 28, 12
COG = 12
SPIN = 4


def launcher():
    cv = Canvas()
    stock_shape = Poly([(0.4, 6.0), (8.6, 4.8), (10.4, 5.4), (10.4, 8.2), (5.0, 9.4), (1.2, 11.8), (0.2, 11.8)])
    lock_shape = box(9.4, 3.6, 14.6, 8.4)
    drum_shape = Ellipse(12.4, 2.8, 3.0, 2.6)
    barrel_shape = box(13.8, 4.4, 25.8, 7.0)
    muzzle_shape = Poly([(24.6, 3.0), (27.8, 2.2), (27.8, 9.0), (24.6, 8.2)])
    sil = cv.part(Xf(), Union(stock_shape, lock_shape, drum_shape, barrel_shape, muzzle_shape), "steel",
                  face((-0.4, -0.6, 0.7), lo=3, hi=7, ramp_len=9, fixed=True), rust=0.0)
    stock = cv.part(Xf(), stock_shape, "oak", texture(face((-0.5, -0.5, 0.7), lo=2, hi=5, ramp_len=6, gain=1.3, bias=0.15, fixed=True), "grain", seed=3),
                    outline=False, clip=sil, rust=0.0)
    for y in range(6, 12):                                         # the gilt butt plate
        if (0, y) in sil:
            cv.put(0, y, G[7] if y < 9 else G[5])
        if (1, y) in stock:
            cv.put(1, y, G[4])
    drum = cv.part(Xf(), drum_shape, "gilt", dome(11.2, 1.6, 3.4, lo=3, hi=8, fixed=True), outline=False, clip=sil, rust=0.0)
    for (x, y, k) in ((12, 2, 2), (13, 2, 2), (12, 3, 2), (13, 3, 1)):  # its window, a cog's tooth in it
        if (x, y) in drum:
            cv.put(x, y, G[k])
    cv.put(12, 2, ST[6])
    glint(cv, 11, 1, "gilt")
    # the gauge on the lock plate: a gilt ring, a white dial, a red needle
    for (x, y, col) in ((10, 5, G[8]), (11, 5, G[6]), (10, 6, G[6]), (11, 6, S[3]), (12, 6, G[4]), (11, 7, G[4]), (12, 5, G[5])):
        cv.put(x, y, col)
    cv.put(11, 6, K[4])
    # the barrel: its lit top line, two gilt bands, the steam line from the drum along it
    for x in range(14, 25):
        if (x, 5) in sil:
            cv.put(x, 5, ST[8] if x % 4 else ST[7])
        if (x, 6) in sil:
            cv.put(x, 6, ST[4])
    for bx in (17, 22):
        for y in range(4, 8):
            if (bx, y) in sil:
                cv.put(bx, y, G[8] if y < 6 else G[5])
    for (x, y) in ((15, 3), (16, 3), (17, 3), (18, 3), (19, 4)):
        cv.put(x, y, C[3] if x % 2 else C[2])                       # the copper steam line
    # the flared muzzle: its dark bore and lit rim
    for y in range(4, 8):
        if (27, y) in sil:
            cv.put(27, y, ST[1])
    for y in range(3, 9):
        if (25, y) in sil:
            cv.put(25, y, ST[7] if y < 6 else ST[5])
    # the trigger guard and the trigger
    for (x, y) in ((10, 9), (11, 10), (12, 10), (13, 9)):
        cv.put(x, y, ST[2])
    cv.put(12, 9, ST[6])
    selout(cv)
    return to_image(cv.px, 0, 0, GUN_W, GUN_H)


def cog(turn):
    """The cog at `turn` degrees: 8 teeth on a ring, a steel hub with four spokes; lit top-left in rig space."""
    cv = Canvas()
    c = COG / 2.0
    teeth = 8
    # square teeth round a solid ring
    shapes = [Ellipse(c, c, 4.6, 4.6)]
    for k in range(teeth):
        a = math.radians(turn + k * 360.0 / teeth)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        w, r0, r1 = 1.15, 3.8, 5.95
        shapes.append(Poly([(c + ux * r0 + vx * w, c + uy * r0 + vy * w), (c + ux * r1 + vx * w, c + uy * r1 + vy * w),
                            (c + ux * r1 - vx * w, c + uy * r1 - vy * w), (c + ux * r0 - vx * w, c + uy * r0 - vy * w)]))
    ring = cv.part(Xf(), Union(*shapes), "gilt", dome(c - 1.6, c - 1.6, 6.4, lo=3, hi=8, gain=1.3), rust=0.0)
    hole = cv.raster(Xf(), Ellipse(c, c, 2.2, 2.2))
    for q in hole:
        cv.px.pop(q, None)                                          # the open centre between the spokes
    for k in range(4):                                              # four steel spokes and a hub
        a = math.radians(turn + 45.0 * (k % 2) + 90.0 * (k // 2))
        for t in (0.6, 1.4, 2.2):
            x, y = int(math.floor(c + math.cos(a) * t)), int(math.floor(c + math.sin(a) * t))
            cv.put(x, y, ST[6] if (x + y) < COG else ST[4])
            x2, y2 = int(math.floor(c - math.cos(a) * t)), int(math.floor(c - math.sin(a) * t))
            cv.put(x2, y2, ST[6] if (x2 + y2) < COG else ST[4])
    h = (int(math.floor(c)) - 1, int(math.floor(c)) - 1)
    for (dx, dy, k) in ((0, 0, 8), (1, 0, 6), (0, 1, 6), (1, 1, 3)):
        cv.put(h[0] + dx, h[1] + dy, ST[k])
    del ring
    return to_image(cv.px, 0, 0, COG, COG)


def export_all():
    export(launcher(), "Content/Mechanist/Weapons/CogLauncher.png")
    export(vertical([cog(k * 45.0 / SPIN) for k in range(SPIN)]), "Content/Mechanist/Weapons/CogLauncherCog.png")


def preview(path):
    sheet = Image.new("RGBA", (GUN_W + 4 + (COG + 2) * SPIN, max(GUN_H, COG) + 4), (52, 56, 66, 255))
    sheet.alpha_composite(launcher(), (2, 2))
    for k in range(SPIN):
        sheet.alpha_composite(cog(k * 45.0 / SPIN), (GUN_W + 4 + k * (COG + 2), 2))
    sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
