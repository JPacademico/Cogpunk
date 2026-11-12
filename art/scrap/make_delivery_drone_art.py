"""Source for the Delivery Drone (D4; the Amazonian Drone until 2026-11-11), 2026-11-10b (user: "a new rare enemy that can spawn anywhere when there are dropped
items or coins on the ground for more than 20 seconds called Amazonian drone, a scrappy thief drone that steals dropped
items and then flies away"). Run from the repo root:

    python -P art/scrap/make_delivery_drone_art.py [--preview FILE]

A scrappy delivery drone gone rogue, seen from the side facing left: its body is a battered cardboard parcel (two shades
of board, a strip of tape round it, a torn corner), strapped into a rusty iron frame; two arms reach out to a rotor at
each end (brass hubs, the blades a blur seen edge-on); a bent antenna with a red tip; under the front a camera dome with
a red eye; under the middle a grabber claw on a short neck, two hooked prongs open (hunting) or shut (carrying); rivets
on the frame's straps. Lit from the top-left, ramp outlines, 16 colours.

Frames (rotors spin: three blade positions; the claw open or shut): 0-2 open, 3-5 shut. 32x22 at 1x, exported 2x,
stacked with 2 px between them. The glow sheet holds the eye and the antenna's tip (full bright in game).

Outputs:
    Content/Scrap/NPCs/DeliveryDrone.png, DeliveryDrone_Glow.png    64x44 frames, 6 of them
    Content/Scrap/Gores/DeliveryDrone_GoreRotor.png, _GoreBox.png    what falls when it is shot down
Constants the game uses (Content/Scrap/NPCs/DeliveryDrone.cs): the frame size, the eye and the claw's points.
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
import make_scrap_art  # noqa: E402
from make_scrap_art import Canvas, export  # noqa: E402
from rig import RAMP  # noqa: E402

for _k, _c in zip("123456", RAMP["oak"]):              # cardboard: the oak ramp, 1 (outline) .. 6 (lit)
    make_scrap_art.PAL[_k] = _c
make_scrap_art.PAL["R"] = RAMP["crimson"][4]           # the eye's red
make_scrap_art.PAL["H"] = RAMP["crimson"][5]           # its highlight
make_scrap_art.PAL["Q"] = RAMP["crimson"][2]           # its dark ring

OUT = "Content/Scrap/"
W, H = 32, 22
FRAMES = 6
EYE = (7, 15)                                          # 1x: the eye's centre (the scan beam leaves here)
CLAW = (16, 21)                                        # 1x: under the claw (a carried item hangs from here)

BODY = [  # the parcel in its frame, rows 7..14 (x 9..23); '.' clear
    "..iiiiiiiiiiiiiii..",
    ".ij5555555555554ji.",
    ".ij5444444444444ji.",
    ".ijqqqqqqqqqqqqqji.",
    ".ij5554444433333ji.",
    ".ij4443333322222ji.",
    ".ij3332222211111ji.",
    "..iiiiiiiiiiiiiii..",
]


def blades(c, cx, y, k):
    """A rotor seen edge-on at (cx, y): the brass hub and the blade's blur, its length by frame k (spinning)."""
    half = (6, 4, 2)[k % 3]
    for x in range(cx - half, cx + half + 1):
        c.set(x, y, "s" if abs(x - cx) < half else "q")
    c.set(cx - half - 1, y, "k") if k % 3 == 0 else None
    c.set(cx, y, "F")
    c.set(cx, y + 1, "D")
    c.set(cx - 1, y + 1, "B")
    c.set(cx + 1, y + 1, "B")
    c.set(cx, y + 2, "k")                              # the motor's shaft


def frame(k):
    c = Canvas(W, H)
    rotor = k % 3
    shut = k >= 3
    # the arms: thin iron struts from the frame out to the motors
    for x in range(3, 10):
        c.set(x, 8, "k")
        c.set(x, 9, "j")
    for x in range(23, 29):
        c.set(x, 8, "k")
        c.set(x, 9, "j")
    for (x, y) in ((4, 6), (4, 7), (27, 6), (27, 7)):    # the motor pods
        c.set(x, y, "q")
    for (x, y) in ((3, 6), (3, 7), (5, 7), (26, 7), (28, 6), (28, 7)):
        c.set(x, y, "j")
    blades(c, 4, 3, rotor)
    blades(c, 27, 3, rotor + 1)
    # the parcel in its frame
    for dy, row in enumerate(BODY):
        for dx, ch in enumerate(row):
            if ch != ".":
                c.set(7 + dx, 7 + dy, ch)
    for (x, y, ch) in ((22, 8, "2"), (22, 9, "1"), (21, 8, "3")):   # a torn corner
        c.set(x, y, ch)
    for (x, y) in ((10, 8), (19, 8), (10, 13), (19, 13)):  # rivets on the frame's straps
        c.set(x, y, "q")
    # the antenna, bent back, a red tip
    for (x, y) in ((18, 6), (18, 5), (19, 4), (20, 3)):
        c.set(x, y, "k")
    c.set(21, 2, "R")
    # the camera dome under the front, its red eye
    for (x, y, ch) in ((6, 14, "j"), (7, 14, "k"), (8, 14, "k"), (9, 14, "j"), (5, 15, "j"), (6, 15, "Q"), (7, 15, "R"),
                       (8, 15, "Q"), (9, 15, "k"), (10, 15, "j"), (6, 16, "j"), (7, 16, "Q"), (8, 16, "k"), (9, 16, "j"),
                       (7, 17, "j"), (8, 17, "j")):
        c.set(x, y, ch)
    c.set(6, 15, "H")
    # the claw: a neck, a hinge, two hooked prongs
    for y in (15, 16):
        c.set(16, y, "k")
        c.set(15, y, "j")
    c.set(14, 17, "j"), c.set(15, 17, "q"), c.set(16, 17, "q"), c.set(17, 17, "j")
    if shut:
        prongs = ((14, 18), (14, 19), (15, 20), (17, 18), (17, 19), (16, 20))
    else:
        prongs = ((13, 18), (12, 19), (12, 20), (13, 21), (18, 18), (19, 19), (19, 20), (18, 21))
    for (x, y) in prongs:
        c.set(x, y, "k")
    return c


def glow(k):
    """The eye and the antenna's tip, full bright."""
    c = Canvas(W, H)
    c.set(7, 15, "R")
    c.set(6, 15, "H")
    c.set(21, 2, "R")
    return c


def stack(frames, pad=1):
    out = Canvas(W, (H + pad) * len(frames) - pad)
    for i, f in enumerate(frames):
        for y in range(H):
            for x in range(W):
                ch = f.get(x, y)
                if ch != ".":
                    out.set(x, i * (H + pad) + y, ch)
    return out


def gore_rotor():
    c = Canvas(14, 5)
    for x in range(1, 13):
        c.set(x, 1, "s" if 2 < x < 11 else "q")
    for (x, y, ch) in ((6, 2, "F"), (7, 2, "D"), (6, 3, "B"), (7, 3, "j"), (6, 4, "k")):
        c.set(x, y, ch)
    return c


def gore_box():
    c = Canvas(12, 9)
    rows = ["111111111111",
            "155555555541",
            "154444444441",
            "1qqqqqqqqqq1",
            "154443333321",
            "143332222211",
            "1333222211..",
            "12221111....",
            "1111........"]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                c.set(x, y, ch)
    return c


def preview(path):
    tiles = []
    for k in range(FRAMES):
        f = frame(k)
        im = Image.new("RGBA", (W, H), (150, 180, 210, 255))
        for y in range(H):
            for x in range(W):
                ch = f.get(x, y)
                if ch != ".":
                    im.putpixel((x, y), make_scrap_art.PAL[ch] + (255,))
        tiles.append(im.resize((W * 8, H * 8), Image.NEAREST))
    sheet = Image.new("RGBA", (W * 8 * 3 + 16, H * 8 * 2 + 8), (30, 30, 36, 255))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % 3) * (W * 8 + 8), (k // 3) * (H * 8 + 8)))
    sheet.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export(stack([frame(k) for k in range(FRAMES)]), OUT + "NPCs/DeliveryDrone.png")
        export(stack([glow(k) for k in range(FRAMES)]), OUT + "NPCs/DeliveryDrone_Glow.png")
        export(gore_rotor(), OUT + "Gores/DeliveryDrone_GoreRotor.png")
        export(gore_box(), OUT + "Gores/DeliveryDrone_GoreBox.png")
        print("frame %dx%d (game px %dx%d), eye (%d, %d), claw (%d, %d) game px" % (W, H, 2 * W, 2 * H, 2 * EYE[0] + 1, 2 * EYE[1] + 1,
                                                                                 2 * CLAW[0], 2 * CLAW[1]))
