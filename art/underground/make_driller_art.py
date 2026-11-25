"""Source for the Driller (D4), 2026-11-25 (user: "add a new enemy that can spawn on the underground called "driller" a drill
bot that can drill (phase through blocks like a worm) if it gets stuck while chasing the player, behaving like a worm enemy
while driling but a normal chasing enemy while not driling"). Run from the repo root:

    python -P art/underground/make_driller_art.py [--preview FILE]

Design (my calls): a squat Cogpunk mining bot: a brass chassis (gilt) with rivets on a dark steel tread, three wheels in it,
a round porthole whose ember glow is its eye (hostile: the ember ramp), a smokestack at the back, and in front a big steel cone
drill on a brass collar, spiral grooves cut into it (they turn as it spins). Sculpted (art/templates/sculpt.py), lit from the
top-left. One model, two uses:

* Driller.png (+ _Glow): the walker, facing left, its origin on the ground under the tread's middle: Walk 0-3 (the tread's
  teeth run back a pixel a frame, the drill turns, the chassis rocks a pixel on its springs).
* Driller_Drill.png (+ _DrillGlow): drilling through rock: the bot turned along its heading, HEADINGS columns (heading k points
  k x 360/HEADINGS degrees clockwise from right on screen) by SPINS rows (the drill's turn); a heading with its nose left is
  modelled mirrored so its top stays up (as the jade loong does). Never rotated at runtime (D4 rule 14): the light stays
  top-left on every heading. The origin is the cell's middle.

Outputs (Content/Underground/NPCs/): Driller.png, Driller_Glow.png, Driller_Drill.png, Driller_DrillGlow.png, DrillerRigData.cs.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from sculpt import Frame, Ell, Tube, Poly, Part, render  # noqa: E402
from rig import RAMP  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402

OUT = "Content/Underground/NPCs/"
G, ST, EM, IV = RAMP["gilt"], RAMP["steel"], RAMP["ember"], RAMP["ivory"]
HEADINGS, SPINS, WALK = 16, 3, 4
WW, WH, WOX, WOY = 40, 26, 20, 24          # the walker's cell (1x) and origin (ground under the tread's middle)
DC = 34                                     # the drilling cells (square), origin in the middle
DSTRIDE = DC + 1


def model(angle, mirror, spin, roll, bob, origin_y):
    """The bot's parts, built facing right (the drill at +x), turned by `angle` (radians, clockwise on screen) round the
    chassis' middle, mirrored across its own axis when `mirror` (heading left: its top stays up). `spin` 0..SPINS-1 turns the
    drill's grooves, `roll` 0..3 runs the tread's teeth, `bob` whole px the chassis sits lower. `origin_y`: the turning point's
    height over the tread's bottom (the walker turns round the ground)."""
    s = -1.0 if mirror else 1.0
    f = Frame(0.0, 0.0, angle)

    def P(x, y):
        return (x, (y - origin_y) * s)

    def ell(x, y, rx, ry, flat=0.0):
        cx, cy = P(x, y)
        return Ell(cx, cy, rx, ry, flat)

    def tube(pts, radii):
        return Tube([P(x, y) for (x, y) in pts], radii)

    def poly(pts, tilt=(0.0, 0.0)):
        return Poly([P(x, y) for (x, y) in pts], (tilt[0], tilt[1] * s))

    b = bob
    parts = []
    # the tread: a stadium of dark steel, three wheels in it
    parts.append(Part("tread", tube([(-7.6, -2.6), (7.6, -2.6)], [2.6, 2.6]), ST, 0, f, lo=1, hi=4))
    for i, wx in enumerate((-5.4, 0.0, 5.4)):
        parts.append(Part("wheel%d" % i, ell(wx, -2.6, 1.6, 1.6), ST, 1, f, lo=3, hi=7))
    # the chassis: a riveted brass body, a domed top plate, the porthole, the smokestack
    parts.append(Part("stack", tube([(-4.6, -8.0 + b), (-5.0, -13.0 + b)], [1.2, 1.0]), ST, 2, f, lo=2, hi=6))
    parts.append(Part("stackcap", ell(-5.0, -13.4 + b, 1.8, 0.8, 0.3), ST, 3, f, lo=2, hi=6))
    parts.append(Part("chassis", ell(0.0, -7.4 + b, 8.6, 4.4, 0.35), G, 4, f, lo=2, hi=8,
                      lines=[[P(-2.0, -11.0 + b), P(-2.0, -4.0 + b)], [P(4.4, -10.4 + b), P(4.4, -4.2 + b)]],
                      spots=((P(-6.0, -5.0 + b)[0], P(-6.0, -5.0 + b)[1], 1.2, 0.8, -1),)))
    parts.append(Part("top", ell(-0.6, -10.6 + b, 5.0, 1.8, 0.2), G, 5, f, lo=4, hi=9))
    parts.append(Part("rim", ell(3.4, -7.6 + b, 2.4, 2.4, 0.2), ST, 6, f, lo=3, hi=7))
    # the drill: a brass collar, then a steel cone with spiral grooves (fold lines that walk back as it spins)
    parts.append(Part("collar", ell(8.4, -7.0 + b, 1.6, 4.0, 0.3), G, 7, f, lo=3, hi=8))
    grooves = []
    for k in range(4):
        gx = 9.6 + ((k * 2.2 + spin * 0.75) % 8.8)
        r = 3.8 * (1.0 - (gx - 9.0) / 8.6)
        grooves.append([P(gx, -7.0 + b - r), P(gx + 1.4, -7.0 + b + r * 0.2), P(gx + 0.6, -7.0 + b + r)])
    parts.append(Part("cone", tube([(9.0, -7.0 + b), (17.6, -7.0 + b)], [3.8, 0.4]), ST, 8, f, lo=2, hi=8, lines=grooves))
    return parts, f, s


def render_cell(angle, mirror, spin, roll, bob, w, h, ox, oy, origin_y):
    parts, f, s = model(angle, mirror, spin, roll, bob, origin_y)
    px, glow, owner = render(parts, w, h, ox, oy)
    # the porthole's ember eye (after the outline): a 2 x 2 glow, its glint
    ex, ey = f.to_world(3.4, (-7.6 + bob - origin_y) * s)
    e = (int(math.floor(ex + ox)) - 1, int(math.floor(ey + oy)) - 1)
    for (dx, dy, c) in ((0, 0, EM[3]), (1, 0, EM[2]), (0, 1, EM[2]), (1, 1, EM[1])):
        q = (e[0] + dx, e[1] + dy)
        if q in px:
            px[q] = c
            glow[q] = c
    # the tread's teeth: every third pixel along the tread's outer edge a step lighter, running back with `roll`
    for (x, y), name in owner.items():
        if name != "tread":
            continue
        lx, ly = f.to_local(x - ox + 0.5, y - oy + 0.5)
        if abs(ly / s - (-2.6 - origin_y)) > 1.6 and int(math.floor(lx + roll)) % 3 == 0:
            i = ST.index(px[(x, y)]) if px[(x, y)] in ST else 1
            if i > 0:
                px[(x, y)] = ST[min(len(ST) - 1, i + 1)]
    # rivets on the chassis band
    for rx in (-6.4, -3.6, 1.2, 6.6):
        qx, qy = f.to_world(rx, (-6.2 + bob - origin_y) * s)
        q = (int(math.floor(qx + ox)), int(math.floor(qy + oy)))
        if owner.get(q) == "chassis":
            px[q] = G[9]
    return px, glow


def walker_frame(k):
    """Walk frame k, facing left (the model mirrored about x: heading pi, top up)."""
    return render_cell(math.pi, True, k % SPINS, k, 1 if k % 2 else 0, WW, WH, WOX, WOY, 0.0)


def drill_cell(heading, spin):
    angle = heading * 2.0 * math.pi / HEADINGS
    mirror = math.cos(angle) < -1e-6 or (abs(math.cos(angle)) <= 1e-6 and math.sin(angle) < 0)
    return render_cell(angle, mirror, spin, spin, 0, DC, DC, DC / 2.0, DC / 2.0, -7.0)


def to_image(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def walker_sheets():
    frames = [walker_frame(k) for k in range(WALK)]
    main = Image.new("RGBA", (WW, (WH + 1) * WALK), (0, 0, 0, 0))
    glow = Image.new("RGBA", main.size, (0, 0, 0, 0))
    for k, (px, gl) in enumerate(frames):
        main.alpha_composite(to_image(px, WW, WH), (0, k * (WH + 1)))
        glow.alpha_composite(to_image(gl, WW, WH), (0, k * (WH + 1)))
    return main, glow, frames


def drill_sheets():
    main = Image.new("RGBA", (HEADINGS * DSTRIDE, SPINS * DSTRIDE), (0, 0, 0, 0))
    glow = Image.new("RGBA", main.size, (0, 0, 0, 0))
    for sp in range(SPINS):
        for h in range(HEADINGS):
            px, gl = drill_cell(h, sp)
            main.alpha_composite(to_image(px, DC, DC), (h * DSTRIDE, sp * DSTRIDE))
            glow.alpha_composite(to_image(gl, DC, DC), (h * DSTRIDE, sp * DSTRIDE))
    return main, glow


def write_rig(path, frames):
    px = frames[0][0]
    xs = sorted(x for (x, y) in px)
    ys = sorted(y for (x, y) in px)
    left, right, top = (xs[0] - WOX) * 2, (xs[-1] - WOX + 1) * 2, (ys[len(ys) // 25] - WOY) * 2
    L = ["// <auto-generated> by art/underground/make_driller_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Underground.NPCs",
         "{",
         "\t/// <summary>The Driller's sheets (game px). Walker (Driller.png, _Glow): facing left, equal cells with 2 px under each, the",
         "\t/// origin on the ground under the tread's middle. Drilling (Driller_Drill.png, _DrillGlow): Headings columns by Spins",
         "\t/// rows of DrillCell squares, 2 px apart, the origin in the middle; heading k points k x 360/Headings degrees clockwise",
         "\t/// from right. Body*: the walker's hitbox from its origin (the smokestack's tip left out).</summary>",
         "\tpublic static class DrillerRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (WW * 2, WH * 2, WOX * 2, WOY * 2, WALK),
         "\t\tpublic const int DrillCell = %d, DrillStride = %d, Headings = %d, Spins = %d;" % (DC * 2, DSTRIDE * 2, HEADINGS, SPINS),
         "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d;" % (left, right, top),
         "\t}",
         "}"]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    main, glow, frames = walker_sheets()
    export(main, OUT + "Driller.png")
    export(glow, OUT + "Driller_Glow.png")
    dm, dg = drill_sheets()
    export(dm, OUT + "Driller_Drill.png")
    export(dg, OUT + "Driller_DrillGlow.png")
    write_rig(OUT + "DrillerRigData.cs", frames)


def preview(path, sc=5):
    main, _, _ = walker_sheets()
    dm, _ = drill_sheets()
    out = Image.new("RGBA", (max(WALK * (WW * sc + 6), HEADINGS * DC * 2 + 12) + 12, WH * sc * 2 + 24 + SPINS * DSTRIDE * 2 * 2 + 12),
                    (20, 20, 24, 255))
    for half, bg in enumerate(((30, 34, 60), (170, 190, 210))):
        for k in range(WALK):
            cell = main.crop((0, k * (WH + 1), WW, k * (WH + 1) + WH))
            im = Image.new("RGBA", (WW, WH), bg + (255,))
            im.alpha_composite(cell)
            out.alpha_composite(im.resize((WW * sc, WH * sc), Image.NEAREST), (6 + k * (WW * sc + 6), 6 + half * (WH * sc + 6)))
    y0 = WH * sc * 2 + 24
    for half, bg in enumerate(((30, 34, 60), (170, 190, 210))):
        band = Image.new("RGBA", dm.size, bg + (255,))
        band.alpha_composite(dm)
        out.alpha_composite(band.resize((dm.width * 2, dm.height * 2), Image.NEAREST), (6, y0 + half * (dm.height * 2 + 6)))
    out.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
