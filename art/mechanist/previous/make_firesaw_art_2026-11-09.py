"""Source for the Firesaw (D4), 2026-11-09 (user: "a new mechanist weapon ... called Firesaw; it should attack in an up and
down motion ... the design should look like a steampunk gasoline pumped chainsaw sword"). Run from the repo root:

    python -P art/mechanist/make_firesaw_art.py [--preview FILE]

A chainsaw sword with a steampunk petrol engine: a riveted brass engine block with cooling fins, a red-lacquered fuel tank
with a brass cap and a pump plunger on top, a pressure gauge running hot, a pull-starter ring, a steel exhaust stub, a
leather-wrapped rear grip where the hand holds it, a steel hand guard, and a long steel guide bar with a groove down its
middle and a rounded nose, its chain of dark teeth running round it (three frames: the chain moves a pixel a frame along
the top and back along the bottom, so it loops). The fire overlay (right click: the blade infused with fire): flames
licking along the bar and a jet of fire past its nose (the +2 tiles), three flickering frames, drawn at full brightness
in game (no glow sheet needed: it is light). Points right (D4 rule 8: held like a gun, turned by the game to its swing).
Lit from the top-left; long ramps (gilt 10, steel 9, crimson 6, hide 7, ember 4); at most 16 colours per sprite.

Outputs (Content/Mechanist/Weapons/):
    Firesaw.png                 the item (frame 0 of the saw)
    FiresawHeld.png             3 frames (the chain moving), 2 px under each
    FiresawHeld_Fire.png        3 frames of the fire overlay (as wide as the saw plus the jet), 2 px under each
Constants the game uses (Content/Mechanist/Weapons/FiresawHeld.cs): GRIP (the pivot in the saw's frame) and the reach.
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP, Xf, Poly, Ellipse, box, Canvas, flat, face, dome, finish  # noqa: E402
from rig import cyl  # noqa: E402
from make_trashtr0m_art import export, to_image, vertical  # noqa: E402

OUT = "Content/Mechanist/Weapons/"
W, H = 48, 16                    # the saw's frame (1x)
JET = 16                         # the fire's jet past the nose (1x): +2 tiles in game
GRIP = (5, 9)                    # where the hand holds it (1x, in the frame): the pivot of the swing
NOSE_X = 46                      # the bar's tip (1x)
FRAMES = 3
TONGUES = (1, 2, 3, 2, 1, 3, 2, 1, 4, 2, 1, 2)       # flame heights over the top edge (1x), rolled along per frame
G, ST, K, HD, E, S = (RAMP[k] for k in ("gilt", "steel", "crimson", "hide", "ember", "steam"))


def saw(k):
    cv = Canvas()
    X = Xf()
    # the guide bar: a long steel blade, lit from the top as a flat bar, a rounded nose
    cv.part(X, box(15.0, 5.0, NOSE_X - 2.0, 11.0), "steel", cyl((15.0, 8.0), (NOSE_X - 2.0, 8.0), 3.0, lo=3, hi=7, gain=1.25, fixed=True),
            rust=0.0)
    cv.part(X, Ellipse(NOSE_X - 2.4, 8.0, 3.0, 3.0), "steel", dome(NOSE_X - 3.4, 7.0, 3.2, lo=3, hi=7, gain=1.25, fixed=True), rust=0.0)
    # the engine block (brass, riveted, cooling fins) and the hand guard before it
    cv.part(X, box(6.0, 3.0, 15.0, 13.0), "gilt", face((-0.55, -0.6, 0.6), lo=3, hi=8, ramp_len=10, gain=1.3, fixed=True), shadow=(1, 1),
            rust=0.0)
    cv.part(X, Poly([(14.6, 2.0), (16.6, 2.0), (17.0, 14.0), (14.6, 14.0)]), "steel", face((-0.6, -0.4, 0.7), lo=2, hi=6, ramp_len=9,
                                                                                              fixed=True), rust=0.0)
    # the red fuel tank behind it, its brass cap, the pump plunger on top
    cv.part(X, box(1.0, 5.0, 6.6, 12.0), "crimson", face((-0.55, -0.6, 0.6), lo=1, hi=5, ramp_len=6, gain=1.3, fixed=True), rust=0.0)
    cv.part(X, box(2.0, 3.6, 4.4, 5.2), "gilt", flat(6), rust=0.0)
    # the rear grip: leather wrapped, under the tank where the hand holds it
    cv.part(X, box(3.0, 11.0, 8.0, 15.4), "hide", face((-0.5, -0.6, 0.6), lo=1, hi=4, ramp_len=7, fixed=True), rust=0.0)
    # the exhaust stub under the bar's root
    cv.part(X, box(11.0, 12.6, 15.0, 14.8), "steel", flat(3), rust=0.0)
    finish(cv)
    put = cv.put
    # stamped details (after the despeckle, which would soften 1-2 px features away)
    for x in (8, 10, 12):                                          # cooling fins down the block
        for y in range(5, 12):
            if (x, y) in cv.px:
                put(x, y, G[2] if y > 6 else G[3])
    for (x, y) in ((7, 4), (13, 4), (7, 12), (13, 12)):              # rivets
        put(x, y, G[9] if x < 10 else G[6])
    for (x, y, col) in ((10, 6, S[3]), (11, 6, S[2]), (10, 7, S[2]), (11, 7, E[2]), (12, 6, G[2]), (12, 7, G[2]), (10, 8, G[2]),
                        (11, 8, G[2])):                              # the pressure gauge, its needle in the red
        put(x, y, col)
    for (x, y, col) in ((3, 2, G[7]), (3, 1, ST[6]), (2, 1, ST[4]), (4, 1, ST[4])):   # the pump plunger's T-handle
        put(x, y, col)
    for (x, y, col) in ((16, 1, G[6]), (17, 1, G[8]), (18, 2, G[6])):  # the pull-starter ring over the guard
        put(x, y, col)
    for y in range(12, 15):                                          # the grip's leather wraps
        put(4, y, HD[1])
        put(6, y, HD[1])
    for x in range(17, NOSE_X - 3):                                  # the groove down the bar's middle
        put(x, 8, ST[2] if x % 6 else ST[1])
    for x in range(17, NOSE_X - 2):                                  # the bar's lit top edge
        if (x, 5) in cv.px:
            put(x, 5, ST[8] if x < 30 else ST[7])
    # the chain: teeth along the top edge moving forward, along the bottom moving back (k shifts them a pixel)
    for x in range(16, NOSE_X - 1):
        top = (x - k) % 3 == 0
        put(x, 4, ST[1] if top else ST[5])
        if top:
            put(x, 3, ST[0])                                         # a tooth's point
        bottom = (x + k) % 3 == 0
        put(x, 11, ST[1] if bottom else ST[4])
        if bottom:
            put(x, 12, ST[0])
    for (dx, dy) in ((0, -1), (1, 0), (0, 1)):                       # round the nose
        x, y = NOSE_X + dx - 1, 8 + dy * 4
        put(x, y, ST[1] if (k + dy) % 2 else ST[4])
    return reduce(to_image(cv.px, 0, 0, W, H))


# D4 rule 5 (items: at most 16 colours): every pixel snapped to the nearest of these shades of its own ramps (all palette
# colours: ramp-0 outlines kept, the gauge's face the lightest steel)
KEEP = ([ST[i] for i in (0, 2, 4, 6, 8)] + [G[i] for i in (0, 3, 5, 7, 9)] + [K[i] for i in (0, 2, 4)] + [HD[i] for i in (0, 2)]
        + [E[2]])


def reduce(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            best = min(KEEP, key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2)
            px[x, y] = best + (255,)
    return im


def fire(k):
    """The flames along the bar and the jet past its nose, frame k: three tongues per few pixels flickering in turn; ember
    1..3 and steam white at the hottest (no outline: light)."""
    cv = Canvas()
    for x in range(16, NOSE_X + JET):
        u = (x - 16) / float(NOSE_X + JET - 16)
        phase = (x * 7 + k * 5) % 9
        if x < NOSE_X:                                             # tongues licking up off the top edge and down off the bottom
            h = TONGUES[(x * 5 + k * 3) % len(TONGUES)]            # uneven heights, rolling along the chain frame by frame
            for y in range(3 - h, 4):
                cv.put(x, y, E[3] if y == 3 else (E[2] if y >= 2 else E[1]))
            h2 = TONGUES[(x * 3 + k * 4 + 2) % len(TONGUES)] // 2 + 1
            for y in range(12, 12 + h2):
                cv.put(x, y, E[3] if y == 12 else (E[2] if y == 13 else E[1]))
        else:                                                      # the jet past the nose: a tapering tongue of fire
            r = max(0.5, 3.6 * (1.0 - (x - NOSE_X) / float(JET)) + (0.6 if phase < 3 else 0.0))
            for y in range(int(8 - r), int(8 + r) + 1):
                d = abs(y - 8) / max(0.5, r)
                cv.put(x, y, S[3] if d < 0.25 and x < NOSE_X + JET // 2 else (E[3] if d < 0.6 else (E[2] if d < 0.9 else E[1])))
    return to_image(cv.px, 0, 0, W + JET, H)


def export_all():
    frames = [saw(k) for k in range(FRAMES)]
    export(frames[0], OUT + "Firesaw.png")
    export(vertical(frames), OUT + "FiresawHeld.png")
    export(vertical([fire(k) for k in range(FRAMES)]), OUT + "FiresawHeld_Fire.png")


def preview(path):
    rows = []
    for k in range(FRAMES):
        im = Image.new("RGBA", (W + JET + 4, H + 4), (36, 40, 48, 255))
        im.alpha_composite(saw(k), (2, 2))
        f = Image.new("RGBA", (W + JET + 4, H + 4), (36, 40, 48, 255))
        f.alpha_composite(saw(k), (2, 2))
        f.alpha_composite(fire(k), (2, 2))
        rows += [im, f]
    sheet = Image.new("RGBA", (rows[0].width * 2, rows[0].height * FRAMES), (0, 0, 0, 255))
    for i, r in enumerate(rows):
        sheet.paste(r, ((i % 2) * r.width, (i // 2) * r.height))
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
