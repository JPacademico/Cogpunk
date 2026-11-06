"""Source for the Sheriff's Revolver, its bullet and cylinder pips, the Broken Whistle and the Cursed Whistle (D4),
2026-11-04. Run from the repo root:

    python -P art/oldbrasstown/make_revolver_art.py [--preview FILE]

Designs (user, 2026-11-04; the looks are my calls):
* Sheriff's Revolver (a gun: it points right, D4 rule 8): a long polished barrel with a brass front sight, a fluted iron
  cylinder, a brass-plated frame with an engraved scroll, the hammer cocked, and an ivory grip with a brass sheriff's
  star inlaid in it.
* Its bullet: a brass slug with an aether streak behind it (friendly colours, D3), 8 headings (0 = right, clockwise),
  each drawn at its heading (never rotated as a bitmap).
* The cylinder pips shown over the holder's head: a brass round, and an empty chamber.
* Broken Whistle: a train conductor's brass hand whistle (a round chamber, a flat mouthpiece, a lanyard ring), cracked
  across its chamber, a chip gone from its rim and its ring snapped open.
* Cursed Whistle: the same whistle stapled back together with iron, its brass gone green with verdigris and a ghostly
  green glow in its window (the Cursed Conductor's ghost train is that green).

Outputs:
    Content/OldBrassTown/Weapons/SheriffsRevolver.png          44x26
    Content/OldBrassTown/Weapons/SheriffsBullet.png            8 headings, 14 px cells, stride 16
    Content/OldBrassTown/Weapons/SheriffsRevolver_Round.png    2 frames, 8 px, stride 10
    Content/OldBrassTown/Items/BrokenWhistle.png               28x28
    Content/Bosses/CursedConductor/Items/CursedWhistle.png     28x28
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, Xf, Poly, Ellipse, Ring, box, Canvas, flat, dome, face  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

I, B, C, E, S, A, V, LE, BO = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "aether", "verd", "leather", "bone"))
GUN_W, GUN_H = 22, 13
BULLET_CELL = 7
ROUND = 4
WHISTLE = 14


def revolver():
    """22x13 at 1x, pointing right, the grip down and back."""
    cv = Canvas()
    # the ivory grip (the bone ramp: leather shadows, a steam-white face, a cream glint), a brass star inlaid
    grip = cv.part(Xf(), Poly([(3.2, 5.4), (7.4, 5.4), (6.6, 12.8), (2.4, 12.8), (1.6, 11.4)]), "bone",
                   face((-0.6, -0.3, 0.75), lo=2, hi=3, gain=1.1, fixed=True), rust=0.0)
    for (dx, dy, col) in ((0, -1, B[4]), (-1, 0, B[4]), (0, 0, B[5]), (1, 0, B[3]), (0, 1, B[2])):
        if (4 + dx, 9 + dy) in grip:
            cv.put(4 + dx, 9 + dy, col)
    # the hammer, cocked back over the frame
    cv.part(Xf(), Poly([(2.4, 0.6), (4.2, 0.6), (5.2, 3.4), (3.4, 3.4)]), "iron", flat(3), rust=0.0)
    # the brass frame, one engraved scroll line along it
    frame = cv.part(Xf(), Poly([(3.6, 2.6), (10.0, 2.6), (10.8, 3.8), (10.8, 6.8), (6.6, 7.4), (3.6, 6.4)]), "brass",
                    face((-0.4, -0.6, 0.7), lo=2, hi=4, gain=1.2, fixed=True), rust=0.0)
    for (x, y) in ((5, 5), (6, 4), (7, 4), (8, 5)):
        if (x, y) in frame:
            cv.put(x, y, B[2])
    # the trigger guard and the trigger
    for (x, y) in ((7, 8), (8, 8), (9, 8), (10, 7)):
        cv.put(x, y, I[1])
    cv.put(8, 7, I[3])
    # the fluted cylinder, polished
    cyl = cv.part(Xf(), box(9.6, 1.6, 13.6, 6.6), "iron", face((-0.3, -0.7, 0.65), lo=3, hi=4, gain=1.3, fixed=True), rust=0.0)
    for x in (10, 12):
        for y in (3, 4):
            if (x, y) in cyl:
                cv.put(x, y, I[2])
    # the ejector rod under the barrel, then the long polished barrel: its lit top edge, the brass front sight
    cv.part(Xf(), box(13.2, 4.4, 18.8, 6.0), "iron", flat(2), rust=0.0)
    barrel = cv.part(Xf(), box(13.0, 1.8, 21.8, 4.6), "iron", flat(3, bevel=False), rust=0.0)
    for x in range(14, 21):
        if (x, 2) in barrel:
            cv.put(x, 2, I[4])
        if (x, 3) in barrel and x % 3 == 0:
            cv.put(x, 3, I[2])
    cv.put(20, 0, B[1])
    cv.put(20, 1, B[3])
    return to_image(cv.px, 0, 0, GUN_W, GUN_H)


def bullet(heading_deg):
    """A brass slug flying along heading_deg (0 = right, clockwise), a short aether streak behind it."""
    cv = Canvas()
    c = BULLET_CELL / 2.0
    xf = Xf.pose(heading_deg, (0.0, 0.0), (c, c))
    cv.part(xf, Poly([(-3.5, -0.55), (-0.6, -0.8), (-0.6, 0.8), (-3.5, 0.55)]), "aether", flat(2, bevel=False), outline=False, rust=0.0)
    cv.part(xf, Ellipse(0.7, 0.0, 1.9, 1.25), "brass", dome(0.2, -0.4, 2.0, lo=3, hi=4, fixed=True), rust=0.0)
    return to_image(cv.px, 0, 0, BULLET_CELL, BULLET_CELL)


def rounds():
    """Frame 0: a brass round seen from its base (a lit rim, a primer); frame 1: an empty, dark chamber."""
    rim = ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3))
    full, empty = Canvas(), Canvas()
    for q in rim:
        full.put(q[0], q[1], B[1])
        empty.put(q[0], q[1], I[3])
    for (x, y, col) in ((1, 1, B[5]), (2, 1, B[4]), (1, 2, B[4]), (2, 2, B[3])):
        full.put(x, y, col)
    for (x, y, col) in ((1, 1, I[0]), (2, 1, I[0]), (1, 2, I[0]), (2, 2, I[1])):
        empty.put(x, y, col)
    return vertical([to_image(full.px, 0, 0, ROUND, ROUND), to_image(empty.px, 0, 0, ROUND, ROUND)])


WHISTLE_TILT = -18.0                   # the mouthpiece a little down-left, the ring up-right (an item held at a slant)


def whistle(cursed):
    """14x14: a conductor's hand whistle at a slant: its round barrel facing us, the broad flat mouthpiece running off its
    top to the left (the dark lip at its end), the window where the air escapes, a lanyard ring on the barrel's back."""
    cv = Canvas()
    ramp = "verd" if cursed else "brass"
    lo, hi = (1, 3) if cursed else (2, 4)
    rl = len(RAMP[ramp])
    xf = Xf.pose(WHISTLE_TILT, (0.0, 0.0), (7.6, 7.4))
    # local space: the barrel's centre at (1.6, 1.0), the mouthpiece along its top to the left, the ring at its back
    cv.part(xf, Ring(4.6, -3.0, 0.8, 1.9), "iron", flat(3, bevel=False), rust=0.0)
    if not cursed:
        ring_px = sorted((q for q in cv.px), key=lambda q: (q[1], -q[0]))
        for q in ring_px[:2]:
            cv.px.pop(q, None)                                                # the ring snapped open
    cv.part(xf, Poly([(-6.6, -3.2), (0.4, -3.4), (0.4, 1.2), (-6.6, 0.2)]), ramp,
            face((-0.2, -0.9, 0.45), lo=lo, hi=hi, gain=1.2, ramp_len=rl), rust=0.0)
    for ly in (-2.4, -1.4, -0.4):                                             # the mouthpiece's dark lip
        x, y = (int(v // 1) for v in xf.fwd((-6.0, ly)))
        if (x, y) in cv.px:
            cv.put(x, y, V[1] if cursed else B[1])
    body = cv.part(xf, Ellipse(1.6, 1.0, 4.4, 4.4), ramp, dome(0.6, 0.0, 5.0, lo=lo, hi=hi, gain=1.3), rust=0.0)
    for q in cv.raster(xf, Ellipse(1.9, 1.3, 2.4, 2.4)):                      # the barrel's end face, one step down
        if q in body:
            cv.darken(*q)
    for lp in ((-0.4, -3.0), (0.6, -3.0)):                                    # the window where the air escapes
        x, y = (int(v // 1) for v in xf.fwd(lp))
        if cursed:
            cv.put_glow(x, y, V[3])
        else:
            cv.put(x, y, I[0])
    crack = ((3.6, -2.6), (3.0, -1.6), (3.8, -0.6), (3.2, 0.4), (4.0, 1.4), (3.4, 2.4), (4.0, 3.4))
    for k, lp in enumerate(crack):
        x, y = (int(v // 1) for v in xf.fwd(lp))
        if (x, y) not in body:
            continue
        if cursed:
            cv.put(x, y, I[3] if k % 2 else V[0])                               # the old crack, stapled shut with iron
        else:
            cv.put(x, y, B[1])
    if cursed:
        for lp in ((1.4, 0.8), (2.4, 0.8)):
            x, y = (int(v // 1) for v in xf.fwd(lp))
            cv.put_glow(x, y, V[3])                                           # the ghost inside, looking out
    else:
        rim = [q for q in body if q not in cv.raster(xf, Ellipse(1.6, 1.0, 3.6, 3.6))]
        for q in sorted(rim, key=lambda p: -(p[0] * 2 + p[1]))[:2]:
            cv.px.pop(q, None)                                                # a chip gone from its rim
    return to_image(cv.px, 0, 0, WHISTLE, WHISTLE)


def export_all():
    export(revolver(), "Content/OldBrassTown/Weapons/SheriffsRevolver.png")
    export(vertical([bullet(k * 45.0) for k in range(8)]), "Content/OldBrassTown/Weapons/SheriffsBullet.png")
    export(rounds(), "Content/OldBrassTown/Weapons/SheriffsRevolver_Round.png")
    export(whistle(False), "Content/OldBrassTown/Items/BrokenWhistle.png")
    export(whistle(True), "Content/Bosses/CursedConductor/Items/CursedWhistle.png")


def preview(path):
    """Dark and light backdrops, 6x."""
    sheet = Image.new("RGBA", (96, 64), (0, 0, 0, 0))
    for row, bg in enumerate(((36, 40, 48, 255), (150, 180, 210, 255))):
        panel = Image.new("RGBA", (96, 32), bg)
        panel.alpha_composite(revolver(), (2, 2))
        panel.alpha_composite(whistle(False), (28, 2))
        panel.alpha_composite(whistle(True), (46, 2))
        panel.alpha_composite(rounds(), (64, 2))
        for k in range(8):
            panel.alpha_composite(bullet(k * 45.0), (2 + k * 9, 20))
        sheet.paste(panel, (0, row * 32))
    sheet.resize((sheet.width * 6, sheet.height * 6), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
