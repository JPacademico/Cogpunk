"""Source for the Sheriff's Revolver, its bullet and cylinder pips, the Broken Whistle and the Cursed Whistle (D4),
2026-11-04. Run from the repo root:

    python -P art/oldbrasstown/make_revolver_art.py [--preview FILE]

Designs (user, 2026-11-04; the looks are my calls):
* Sheriff's Revolver (a gun: it points right, D4 rule 8). Redrawn 2026-11-05 (user: "remake the sheriff pistol design,
  it should look like a polished brass powerful magnum revolver"; the 2026-11-04 version is in previous/): a big-bore
  magnum all in polished brass (the gilt ramp, 10 shades, so the metal can gleam): a long heavy barrel with a vent rib
  on top and a full-length underlug, a dark bore, a tall front sight, a big fluted cylinder with its lit lips, a heavy
  frame with an engraved scroll, a steel hammer cocked back, a steel trigger guard, and an ivory grip with a brass
  sheriff's star inlaid. One outlined silhouette with the parts shaded inside it (small parts drown in their own
  outlines) and long specular lines along the barrel.
* Its bullet: a brass slug with an aether glint at its base (friendly colours, D3), 16 headings (0 = right, clockwise),
  each drawn at its heading (never rotated as a bitmap); its smoke trail is drawn by the game (Core/Visuals/SmokeTrails).
* The cylinder pips shown over the holder's head: a brass round, and an empty chamber.
* Broken Whistle: a train conductor's brass hand whistle (a round chamber, a flat mouthpiece, a lanyard ring), cracked
  across its chamber, a chip gone from its rim and its ring snapped open.
* Cursed Whistle: the same whistle stapled back together with iron, its brass gone green with verdigris and a ghostly
  green glow in its window (the Cursed Conductor's ghost train is that green).

Outputs:
    Content/OldBrassTown/Weapons/SheriffsRevolver.png          52x28
    Content/OldBrassTown/Weapons/SheriffsBullet.png            16 headings, 14 px cells, stride 16
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
from rig import RAMP, Xf, Poly, Ellipse, Ring, Union, box, Canvas, flat, dome, face, cyl, glint, selout  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

I, B, C, E, S, A, V, LE, BO = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "aether", "verd", "leather", "bone"))
GUN_W, GUN_H = 26, 14
G, ST, IV = RAMP["gilt"], RAMP["steel"], RAMP["ivory"]
BULLET_HEADINGS = 16
BULLET_CELL = 7
ROUND = 4
WHISTLE = 14


def revolver():
    """26x14 at 1x, pointing right, the grip down and back: the polished brass magnum."""
    cv = Canvas()
    grip_shape = Poly([(2.6, 6.6), (7.8, 6.6), (7.0, 13.8), (2.6, 13.8), (1.4, 12.4)])
    frame_shape = Poly([(4.0, 2.2), (11.4, 2.2), (12.4, 3.4), (12.4, 8.2), (7.4, 8.8), (4.0, 7.6)])
    cyl_shape = box(11.0, 1.2, 16.2, 8.2)
    barrel_shape = box(15.6, 1.8, 25.8, 5.4)
    rib_shape = box(15.6, 0.8, 25.6, 2.0)
    lug_shape = box(15.6, 5.0, 25.2, 7.8)
    hammer_shape = Poly([(2.4, 0.2), (4.6, 0.2), (6.0, 3.4), (3.8, 3.4)])
    sil = cv.part(Xf(), Union(grip_shape, frame_shape, cyl_shape, barrel_shape, rib_shape, lug_shape, hammer_shape), "gilt",
                  face((-0.4, -0.6, 0.7), lo=3, hi=7, ramp_len=10, gain=1.3, fixed=True), rust=0.0)
    # the ivory grip and its inlaid brass star
    grip = cv.part(Xf(), grip_shape, "ivory", face((-0.6, -0.3, 0.75), lo=2, hi=5, ramp_len=6, gain=1.2, bias=0.2, fixed=True),
                   outline=False, clip=sil, rust=0.0)
    for (dx, dy, k) in ((0, -1, 8), (-1, 0, 8), (0, 0, 9), (1, 0, 6), (0, 1, 5), (-1, 1, 4), (1, 1, 4)):
        if (4 + dx, 10 + dy) in grip:
            cv.put(4 + dx, 10 + dy, G[k])
    for x in range(3, 8):                                          # the grip's seam to the frame
        if (x, 6) in sil:
            cv.put(x, 6, IV[1])
    # the steel hammer, cocked back
    cv.part(Xf(), hammer_shape, "steel", face((-0.5, -0.5, 0.7), lo=4, hi=7, ramp_len=9, fixed=True), outline=False, clip=sil, rust=0.0)
    # the frame: an engraved scroll
    for (x, y, k) in ((6, 5, 3), (7, 4, 3), (8, 4, 3), (9, 5, 3), (8, 6, 4), (6, 6, 8), (9, 4, 8)):
        if (x, y) in sil:
            cv.put(x, y, G[k])
    # the fluted cylinder: dark grooves with lit lips, its front and back seams, a glint
    cylp = cv.part(Xf(), cyl_shape, "gilt", cyl((11.0, 4.6), (16.2, 4.6), 3.6, lo=3, hi=8, gain=1.4, fixed=True), outline=False, clip=sil,
                   rust=0.0)
    for x in (12, 14):
        for y in (3, 4, 5, 6):
            if (x, y) in cylp:
                cv.put(x, y, G[2] if y < 6 else G[1])
                if (x + 1, y) in cylp:
                    cv.put(x + 1, y, G[8] if y < 5 else G[6])
    for y in range(1, 9):
        for x in (11, 16):
            if (x, y) in sil:
                cv.put(x, y, G[2])
    glint(cv, 13, 2, "gilt")
    # the barrel: the vent rib's specular line, the barrel's lit flank, the underlug, the bore, the front sight
    for x in range(16, 26):
        if (x, 1) in sil:
            cv.put(x, 1, G[9] if x % 4 else G[8])                   # the vent rib
        if (x, 2) in sil:
            cv.put(x, 2, G[4] if x % 2 else G[3])                   # its vents
        if (x, 3) in sil:
            cv.put(x, 3, G[8])                                      # the barrel's long highlight
        if (x, 4) in sil:
            cv.put(x, 4, G[6])
        if (x, 5) in sil and x < 25:
            cv.put(x, 5, G[2])                                      # the seam over the underlug
        if (x, 6) in sil and x < 25:
            cv.put(x, 6, G[7] if x < 22 else G[6])                  # the underlug's lit top
        if (x, 7) in sil and x < 25:
            cv.put(x, 7, G[4])
    for y in (3, 4):
        if (25, y) in sil:
            cv.put(25, y, ST[1])                                    # the dark bore
    cv.put(24, 0, G[8])                                              # the tall front sight
    cv.put(25, 0, G[5])
    # the steel trigger guard and the trigger
    for (x, y) in ((7, 9), (8, 10), (9, 10), (10, 10), (11, 9)):
        cv.put(x, y, ST[2])
    cv.put(9, 9, ST[6])
    selout(cv)
    return to_image(cv.px, 0, 0, GUN_W, GUN_H)


def bullet(heading_deg):
    """A brass slug flying along heading_deg (0 = right, clockwise), an aether glint at its base (friendly, D3)."""
    cv = Canvas()
    c = BULLET_CELL / 2.0
    xf = Xf.pose(heading_deg, (0.0, 0.0), (c, c))
    cv.part(xf, Ellipse(0.4, 0.0, 2.2, 1.3), "gilt", dome(0.2, -0.4, 2.2, lo=4, hi=8, fixed=True), rust=0.0)
    q = xf.fwd((-1.2, 0.0))
    x, y = int(q[0]), int(q[1])
    if (x, y) in cv.px:
        cv.put(x, y, A[2])
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
    export(vertical([bullet(k * 360.0 / BULLET_HEADINGS) for k in range(BULLET_HEADINGS)]), "Content/OldBrassTown/Weapons/SheriffsBullet.png")
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
