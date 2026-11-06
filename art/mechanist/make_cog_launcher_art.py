"""Source for the Cog-launcher (D4), redrawn 2026-11-05b. Run from the repo root:

    python -P art/mechanist/make_cog_launcher_art.py [--preview FILE]

Design (user, 2026-11-05: "a mechanist class weapon that shoots a spinning cog"; 2026-11-05b: "it should look like a brass
gun with a clocked cog that is shot with a piston, and not a classic gunpowder gun", and "it should shoot spinning rusted
cogs like the scrap armor does ... and not this golden cog projectile"; the first version, a rebuilt musket firing a gilt
cog, is in previous/make_cog_launcher_art_2026-11-05.py). A gun: it points right (D4 rule 8).
* A steam piston gun all in brass: a riveted brass receiver with a pressure gauge on top (a pale dial, the needle at
  full pressure) and a copper steam line into a steel piston cylinder with two brass bands, a pistol grip wrapped in
  leather bands and a steel trigger, and at the front a brass cup, the back half of a ring, with a Rusted Cog clocked
  into it (the very Rusted Cog item sprite, so the cog on the gun is the cog that flies), the piston's steel ram resting
  behind its hub.
* No barrel, no stock, no flash pan: the piston punches the cog out of the cup.
* Held frames (the game draws these while it is in use, CogLauncherLayer): Fired (the ram punched forward through the
  empty cup), Return (the ram halfway back, the next cog dropping into the cup from above), Loaded (the item sprite).
* Colours: the item cap is 16, and the cog alone has 7, so the gun is built from the cog's rust and leather shades, the
  brass ramp (one shade shared with the cog's worn brass) and four steel shades.

Outputs:
    Content/Mechanist/Weapons/CogLauncher.png        60x32 (the loaded gun: inventory, the world, the Loaded frame)
    Content/Mechanist/Weapons/CogLauncher_Held.png   3 frames of 60x32, stride 34 (Fired, Return, Loaded)
The cog itself is Content/Scrap/Items/RustedCog.png (CogLauncherCog draws it, spinning like the Scrap armor's cog).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, Xf, Poly, Union, box, Canvas, flat, face, cyl, selout  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

B, ST, C, L = RAMP["brass"], RAMP["steel"], RAMP["copper"], RAMP["leather"]
GUN_W, GUN_H = 30, 16
COG_AT = (18, 2)                      # the Rusted Cog's 12x12 top-left in the cup (loaded)
COG_CENTRE = (COG_AT[0] + 5.5, COG_AT[1] + 5.5)
RAM_REST, RAM_FIRED, RAM_RETURN = 0, 7, 3     # art px the ram head is pushed forward
RUSTED_COG = "Content/Scrap/Items/RustedCog.png"
FRAMES = ("Fired", "Return", "Loaded")
# The item cap is 16 colours and the cog alone has 7 (copper 0-4, leather 2, brass 3): the gun uses those, the rest of
# the brass ramp and four steel shades, and every pixel is snapped to this list at the end.
ALLOWED = list(C) + [L[2]] + list(B) + [ST[1], ST[3], ST[5], ST[7]]


def rusted_cog():
    """The Rusted Cog item at 1x (its 2x export halved): the same pixels as the cog the gun fires."""
    im = Image.open(os.path.join(os.getcwd(), RUSTED_COG)).convert("RGBA")
    return im.resize((im.width // 2, im.height // 2), Image.NEAREST)


def snap(img):
    """Every opaque pixel to the nearest allowed colour (the cog's own pixels are already in the list)."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            best = min(ALLOWED, key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2)
            px[x, y] = best + (255,)
    return img


def gun(ram, cog_drop=None):
    """The gun with its ram `ram` art px forward; `cog_drop` = rows the next cog still has to fall into the cup (None: no
    cog in it)."""
    cv = Canvas()
    X = Xf()
    cx, cy = COG_CENTRE
    tank = box(0.0, 4.6, 3.0, 10.4)
    receiver = Poly([(3.0, 2.6), (10.0, 2.6), (11.0, 3.6), (11.0, 11.4), (2.0, 11.4), (2.0, 3.6)])
    gauge = Poly([(4.8, 3.4), (5.6, 1.2), (7.0, 0.4), (8.4, 1.2), (9.2, 3.4)])
    grip = Poly([(3.2, 10.6), (9.0, 10.6), (8.2, 16.0), (2.6, 16.0), (1.6, 14.4)])
    piston = box(8.6, 4.6, 17.4, 10.4)
    # the cup: the back half of a ring round the cog, its open side forward
    cup_pts = []
    for k in range(13):
        a = math.radians(90.0 + 180.0 * k / 12.0)
        cup_pts.append((cx + 8.6 * math.cos(a), cy + 8.6 * math.sin(a)))
    for k in range(12, -1, -1):
        a = math.radians(90.0 + 180.0 * k / 12.0)
        cup_pts.append((cx + 6.0 * math.cos(a), cy + 6.0 * math.sin(a)))
    cup = Poly(cup_pts)
    sil = cv.part(X, Union(tank, receiver, gauge, grip, piston, cup), "brass",
                  face((-0.45, -0.6, 0.7), lo=2, hi=4, ramp_len=6, gain=1.15, bias=-0.05, fixed=True), rust=0.0)
    for x in range(3, 10):                                         # the receiver's lit top edge and its dark underside
        if (x, 3) in sil:
            cv.put(x, 3, B[5] if x < 8 else B[4])
        if (x, 10) in sil:
            cv.put(x, 10, B[2])
    for y in range(4, 10):
        if (3, y) in sil:
            cv.put(3, y, B[4])
    # the copper steam canister at the back, riveted
    tankp = cv.part(X, tank, "copper", cyl((1.5, 4.6), (1.5, 10.4), 1.6, lo=1, hi=4, gain=1.3, fixed=True), outline=False, clip=sil, rust=0.0)
    for (x, y) in ((1, 5), (1, 9)):
        if (x, y) in tankp:
            cv.put(x, y, C[4])
    # the gauge on top: a pale dial in a brass bezel, a dark needle
    for (x, y) in ((6, 1), (7, 1), (6, 2), (7, 2), (8, 2)):
        if (x, y) in sil:
            cv.put(x, y, B[5])
    cv.put(7, 2, C[0])
    cv.put(6, 1, C[0])                                             # the needle, up and left: full pressure
    # the receiver: rivets at its corners, a shaded edge down its front
    for (x, y) in ((4, 4), (9, 4), (4, 9), (9, 9)):
        if (x, y) in sil:
            cv.put(x, y, B[5])
            if (x + 1, y + 1) in sil:
                cv.put(x + 1, y + 1, B[1])
    for y in range(4, 11):
        if (10, y) in sil:
            cv.put(10, y, B[2])
    # the copper steam line from the gauge down into the piston
    for (x, y) in ((9, 3), (10, 3), (11, 4)):
        cv.put(x, y, C[3] if x < 11 else C[2])
    # the grip, wrapped in leather bands, and the steel trigger in its guard
    gripp = cv.part(X, grip, "leather", face((-0.6, -0.3, 0.75), lo=2, hi=2, ramp_len=3, fixed=True), outline=False, clip=sil, rust=0.0)
    for y in (12, 14):
        for x in range(2, 9):
            if (x, y) in gripp:
                cv.put(x, y, C[1])
    for y in (13, 15):
        for x in range(2, 9):
            if (x, y) in gripp and (x - 1, y) not in gripp:
                cv.put(x, y, C[3])                                  # the wrap's lit edge
    for (x, y) in ((9, 12), (10, 13), (11, 13), (12, 12)):
        cv.put(x, y, ST[3])
    cv.put(10, 12, ST[7])
    # the steel piston cylinder, two brass bands
    pist = cv.part(X, piston, "steel", cyl((8.6, 7.5), (17.4, 7.5), 3.0, lo=3, hi=7, gain=1.3, fixed=True), outline=False, clip=sil, rust=0.0)
    for bx in (11, 14):
        for y in range(5, 10):
            if (bx, y) in pist:
                cv.put(bx, y, B[5] if y < 7 else (B[4] if y < 9 else B[2]))
    # the cup's inside, in its own shadow where the cog sits, and its lit rim
    for q in list(cv.px):
        if q in pist:
            continue
        dx, dy = q[0] + 0.5 - cx, q[1] + 0.5 - cy
        r = math.hypot(dx, dy)
        if 6.0 <= r < 6.9 and dx <= 0.5:
            cv.put(q[0], q[1], B[1] if dy > -2 else B[2])            # the inner lip, in the cog's shadow
        elif 6.9 <= r < 8.0 and dx <= 0.5:
            lit_ = (dx + dy) < -3.0
            cv.put(q[0], q[1], B[5] if (dx + dy) < -7.5 else (B[4] if lit_ else B[3]))   # the ring's face, lit top-left
    # the ram: a steel rod out of the cylinder through the cup, its head pushed `ram` px forward
    head_x = 17 + ram
    for x in range(17, head_x):
        cv.put(x, 7, ST[7])
        cv.put(x, 8, ST[3])                                         # the rod
    for y in range(6, 10):
        cv.put(head_x, y, ST[1] if y == 9 else ST[5])
        cv.put(head_x + 1, y, ST[1] if y == 9 else ST[3])           # its head
    selout(cv)
    img = to_image(cv.px, 0, 0, GUN_W, GUN_H)
    if cog_drop is not None:
        cog = rusted_cog()
        y = COG_AT[1] - cog_drop
        if y < 0:
            cog = cog.crop((0, -y, cog.width, cog.height))
            y = 0
        img.alpha_composite(cog, (COG_AT[0], y))
    return snap(img)


def frames():
    return {"Fired": gun(RAM_FIRED), "Return": gun(RAM_RETURN, cog_drop=5), "Loaded": gun(RAM_REST, cog_drop=0)}


def export_all():
    f = frames()
    export(f["Loaded"], "Content/Mechanist/Weapons/CogLauncher.png")
    export(vertical([f[n] for n in FRAMES]), "Content/Mechanist/Weapons/CogLauncher_Held.png")


def preview(path):
    f = frames()
    sheet = Image.new("RGBA", ((GUN_W + 2) * len(FRAMES) + 2, (GUN_H + 2) * 2 + 2), (52, 56, 66, 255))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (sheet.width, GUN_H + 2), bg)
        for k, n in enumerate(FRAMES):
            tile.alpha_composite(f[n], (2 + k * (GUN_W + 2), 1))
        sheet.paste(tile, (0, 1 + half * (GUN_H + 2)))
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
