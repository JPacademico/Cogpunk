"""Source for the Jade Claws (D4), 2026-11-24. Run from the repo root:

    python -P art/gems/make_jade_claws_art.py [--preview FILE]

User, 2026-11-24: "add a new weapon/mining tool called "jade claws" ... example for design on prompt image": a painting of a
gauntlet of dark plum lacquer banded and scrolled in gold, a violet stone set in its back, a pale steel crescent where the
claws leave it, long green crystal claws, and brown leather straps hanging loose (three claws since 2026-11-24, user: "it should only
have 3 claws and all three properly conected to the base"). Drawn at item size after its layout
and colours (not traced: a painting shrinks to noise), in the palette's plum and amethyst (the lacquer), gilt (the gold),
emerald (the jade crystal), steel and leather.

A swung tool, so it points to the top-right like vanilla's swords and pickaxes (D4 rule 8): the gauntlet at the bottom-left
(where the hand holds it), the claws reaching up and right. 22x22 art px (44x44 in game, the size of a long pickaxe). At most
16 colours (D4 rule 5).

Output: Content/Gems/Items/JadeClaws.png
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

PL, AM, GI, EM, ST, LE = (RAMP[k] for k in ("plum", "amethyst", "gilt", "emerald", "steel", "leather"))
LACQUER = (PL[0], PL[1], PL[2], AM[2])                    # 0 outline .. 3 lit
GOLD = (GI[1], GI[5], GI[7], GI[7])                       # (the top shade kept for the 16-colour cap)
JADE = (EM[1], EM[3], EM[4], EM[5], EM[6])
STEEL = (PL[0], ST[5], ST[7])                             # outlined in the lacquer's darkest
STRAP = (PL[0], LE[1], LE[2])
GEM = (AM[2], AM[4], AM[4])
W = H = 22
OUT = "Content/Gems/Items/JadeClaws.png"

# the tool's axis: from the grip (bottom-left) towards the claws' tips (top-right)
UX, UY = 1 / math.sqrt(2), -1 / math.sqrt(2)              # along the tool
VX, VY = 1 / math.sqrt(2), 1 / math.sqrt(2)               # across it (positive: down-right)
ORIGIN = (4.0, 17.5)                                       # the gauntlet's back end


def uv(x, y):
    dx, dy = x + 0.5 - ORIGIN[0], y + 0.5 - ORIGIN[1]
    return dx * UX + dy * UY, dx * VX + dy * VY


def light(nu, nv):
    """A shade step from a normal given in (u, v): lit towards the top-left (-x, -y) in the image."""
    nx, ny = nu * UX + nv * VX, nu * UY + nv * VY
    return -(nx + ny) / math.sqrt(2)


def gauntlet(p):
    """The lacquered gauntlet: a rounded cylinder along the axis, gold bands at both ends, a gold scroll, the violet stone."""
    for y in range(H):
        for x in range(W):
            u, v = uv(x, y)
            if 0.0 <= u <= 9.5 and abs(v) <= 3.6 - (0.8 if u < 1.0 else 0.0):
                l = light(0.0, v / 3.6)
                ramp, shade = LACQUER, (3 if l > 0.45 else 2 if l > -0.2 else 1)
                if 0.0 <= u < 1.6 or 7.8 <= u <= 9.5:           # the gold bands
                    ramp, shade = GOLD, (3 if l > 0.45 else 2 if l > -0.2 else 1)
                p.put(x, y, ramp, shade)
    # the gold scroll on its back and the violet stone set in it
    for (u, v) in ((3.0, -1.8), (4.0, -2.4), (5.0, -2.0), (5.5, -1.0), (3.5, 1.6), (4.5, 2.2), (5.5, 1.8)):
        x = ORIGIN[0] + u * UX + v * VX
        y = ORIGIN[1] + u * UY + v * VY
        p.put(int(x), int(y), GOLD, 2)
    gx, gy = ORIGIN[0] + 5.0 * UX, ORIGIN[1] + 5.0 * UY
    p.put(int(gx), int(gy), GEM, 2, lock=True)
    p.put(int(gx) - 1, int(gy), GEM, 1, lock=True)
    p.put(int(gx), int(gy) + 1, GEM, 0, lock=True)


def crescent(p):
    """The pale steel crescent across the gauntlet's front end, its horns swept back."""
    for y in range(H):
        for x in range(W):
            u, v = uv(x, y)
            arc = 9.4 - 0.15 * v * v
            if abs(u - arc) <= 0.7 and abs(v) <= 3.8:
                p.put(x, y, STEEL, 2 if v < -1 else 1)


def line(x0, y0, x1, y1):
    """Bresenham's pixels from (x0, y0) to (x1, y1)."""
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    x, y = x0, y0
    for _ in range(64):
        pts.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return pts


# the three claws (art px): a root inside the steel crescent and a tip, each scanned along its long direction as a band
# that narrows from 3 px to 1 (user, 2026-11-24: "it should only have 3 claws and all three properly conected to the base";
# the first pass had a fourth that floated past the crescent's lower horn, and the claws ran together)
CLAWS = (((9.5, 9.5), (13.0, 1.0)), ((11.5, 10.5), (19.0, 3.0)), ((12.5, 12.5), (21.0, 8.0)))


def claws(p):
    """Three long jade crystals growing out of the crescent towards the top-right, spread like fingers: each a band scanned
    along its long axis (rows for the steep ones, columns for the flat one), 3 px at the root, 1 at the tip, its lit edge
    (top-left) light, its far edge the crystal's darkest, a glint near the tip. A pixel belongs to one claw only, so they
    never run together. Thin parts take no outline (it would swallow them): the dark edge stands in."""
    owner = {}
    for k, ((rx, ry), (tx, ty)) in enumerate(CLAWS):
        steep = abs(ty - ry) >= abs(tx - rx)
        n = int(max(abs(ty - ry), abs(tx - rx))) + 1
        for i in range(n + 1):
            t = i / float(n)                                   # 0 at the root, 1 at the tip
            cx, cy = rx + (tx - rx) * t, ry + (ty - ry) * t
            half = 1.25 * (1.0 - t) + 0.25
            if steep:
                y = int(round(cy))
                x0, x1 = int(round(cx - half)), int(round(cx + half))
                cells = [(x, y) for x in range(x0, x1 + 1)]
            else:
                x = int(round(cx))
                y0, y1 = int(round(cy - half)), int(round(cy + half))
                cells = [(x, y) for y in range(y0, y1 + 1)]
            for j, (x, y) in enumerate(cells):
                if (x, y) in owner and owner[(x, y)] != k:
                    continue
                owner[(x, y)] = k
                last = len(cells) - 1
                if t > 0.9:
                    shade = 4                                  # the tip's glint
                elif j == 0:
                    shade = 3 if t > 0.5 else 2                # the lit edge
                elif j == last and last > 0:
                    shade = 0                                  # the far edge, the crystal's darkest
                else:
                    shade = 1
                p.put(x, y, JADE, shade)


def straps(p):
    """The two leather straps hanging loose off the gauntlet's back end."""
    for pts in (((3, 18), (2, 18), (1, 19), (1, 20), (2, 21)), ((5, 19), (4, 20), (4, 21))):
        for (x, y) in pts:
            p.put(x, y, STRAP, 2)


def sprite():
    p = Pix(W, H)
    straps(p)
    gauntlet(p)
    crescent(p)
    claws(p)
    p.outline(skip=(tuple(tuple(c) for c in JADE), tuple(tuple(c) for c in STRAP)))
    return p.image()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    im = sprite()
    if a.preview:
        preview([im], a.preview, scale=10)
    else:
        export(im, OUT)
