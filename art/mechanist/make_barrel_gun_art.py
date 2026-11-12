"""Source for the Barrel Gun (D4), 2026-11-11 (user, with a reference image of a red-staved, iron-hooped barrel on a dark
gun frame: "add a new mechanist weapon that can be found in wood crates (5%). it should be called barrel gun and shoot
fish at 24 use time 4 steam each, dealing 20 damage and with a chance to stun enemies (only stun basic enemies, not
bosses or mini bosses) it can't crit and gains 50% more damage and homing when it's raining or underwater"). Run from the
repo root:

    python -P art/mechanist/make_barrel_gun_art.py [--preview FILE]

Design (after the reference): a gun that points right (D4 rule 8).
* The body is a fish barrel lying on its side, its open end forward: red staves lit from the top-left (crimson), two
  dark seams along them, three steel hoops round it; the mouth a dark hole in a lighter rim.
* Under it a dark iron frame: a rail, a raked grip, a trigger in its guard.
* Behind it a brass steam canister with a steel valve wheel on top and a pipe into the barrel (it's a Mechanist's).
* Its fish (BarrelGunFish): three kinds, a green bass, a silver trout with a pink stripe and a red snapper, each in two
  flops (tail up, tail down), drawn pointing right.
* The stun (Stunned): the buff icon, a pale spiral with two gold stars; and the stars that circle a stunned enemy's
  head (StunStars), two twinkles.
At most 16 colours a sprite (D4 rule 5).

Outputs:
    Content/Mechanist/Weapons/BarrelGun.png        60x32
    Content/Mechanist/Weapons/BarrelGunFish.png    24x16 a frame, 6 frames (bass, trout, snapper x 2 flops), stride 18
    Content/Mechanist/Buffs/Stunned.png            32x32
    Content/Mechanist/Buffs/StunStars.png          10x10 a frame, 2 frames, stride 12
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export, sheet, preview  # noqa: E402
from rig import RAMP  # noqa: E402

CR, BR, GI = RAMP["crimson"], RAMP["brass"], RAMP["gilt"]
_ST, GH, IV, SM, AE = RAMP["steel"], RAMP["ghost"], RAMP["ivory"], RAMP["steam"], RAMP["aether"]
ST = (_ST[0], _ST[2], _ST[3], _ST[5], _ST[7])            # the hoops and the frame: dark iron to a bright edge
BRC = (BR[0], BR[3], BR[4], BR[5])                       # the canister
OUT_W = "Content/Mechanist/Weapons/"
OUT_B = "Content/Mechanist/Buffs/"
W, H = 30, 16
MOUTH = (28, 6)                                          # the barrel's mouth (1x), where the fish leave

# the barrel's profile: column -> (top row, bottom row)
PROFILE = {7: (4, 8), 8: (3, 9), 9: (2, 10), 10: (2, 10)}
PROFILE.update({x: (1, 11) for x in range(11, 22)})
PROFILE.update({22: (2, 10), 23: (2, 10), 24: (3, 9)})


def gun():
    p = Pix(W, H)
    # the frame under the barrel: the rail, the grip, the trigger guard
    for x in range(6, 23):
        p.put(x, 12, ST, 2)
    for y, (x0, x1) in ((13, (8, 11)), (14, (7, 10)), (15, (7, 10))):
        for x in range(x0, x1 + 1):
            p.put(x, y, ST, 3 if x == x0 else 2)
    for (x, y) in ((13, 13), (16, 13), (13, 14), (16, 14), (14, 15), (15, 15)):
        p.put(x, y, ST, 2)
    p.put(14, 13, ST, 4)                                 # the trigger
    # the steam canister behind, its valve wheel and its pipe into the barrel
    for y in range(5, 11):
        for x in range(1, 7):
            p.put(x, y, BRC, 3 if y == 5 else (2 if y < 8 else 1))
    for (x, y, i) in ((3, 3, 4), (4, 3, 3), (3, 4, 2), (4, 4, 2), (2, 3, 2), (5, 3, 2)):   # the wheel on its stem
        p.put(x, y, ST, i)
    p.put(6, 6, BRC, 2)
    p.put(6, 7, BRC, 1)
    # the barrel: staves lit from the top-left, two seams along them
    for x, (t, b) in PROFILE.items():
        for y in range(t, b + 1):
            u = (y - t) / max(1, b - t)                  # 0 at its top, 1 at its bottom
            i = 5 if u < 0.15 else (4 if u < 0.35 else (3 if u < 0.6 else (2 if u < 0.85 else 1)))
            p.put(x, y, CR, i)
        mid = (t + b) / 2
        for seam in (mid - 2.5, mid + 2.5):              # the seams follow the bulge
            p.put(x, int(round(seam)), CR, 1)
    # the hoops
    for x0 in (9, 15, 21):
        t, b = PROFILE[x0]
        for x in (x0, x0 + 1):
            tt, bb = PROFILE[x]
            for y in range(tt - (1 if x == x0 + 1 and x0 == 15 else 0), bb + 1):
                u = (y - tt) / max(1, bb - tt)
                p.put(x, y, ST, (4 if u < 0.3 else (3 if u < 0.7 else 2)) - (1 if x == x0 + 1 else 0))
    # the mouth: a lighter rim round a dark hole
    for y in range(3, 10):
        p.put(25, y, CR, 4 if y < 6 else 3)
    for y in range(4, 9):
        for x in (26, 27):
            p.put(x, y, CR, 0)
        p.put(28, y, CR, 3)
    p.put(26, 3, CR, 4)
    p.put(27, 3, CR, 3)
    p.put(26, 9, CR, 2)
    p.put(27, 9, CR, 2)
    p.outline(skip=())
    # stamps: rivets on the hoops, a glint on the canister, the wood's grain
    for x0 in (9, 15, 21):
        t, _ = PROFILE[x0]
        p.put(x0, t + 1, ST, 4)
    p.put(2, 6, BRC, 3)
    for (x, y) in ((12, 3), (18, 2), (14, 9), (20, 10)):
        p.shift(x, y, -1)
    return p


# --- the fish ----------------------------------------------------------------------------------------------------------
FISH_ROWS = (
    (  # the tail flicked up
        "............",
        "....ddd.....",
        "o..dmmmmd...",
        "oo.dlllmmd..",
        ".oodmmmmmeg.",
        "oo.bbbbbbmmk",
        "o...bbbbbm..",
        ".....f.f....",
    ),
    (  # the tail swung down
        "............",
        "....ddd.....",
        "...dmmmmd...",
        "...dlllmmd..",
        "ooodmmmmmeg.",
        ".oobbbbbbmmk",
        "oo..bbbbbm..",
        "o....f.f....",
    ),
)


def _kind(ramp, o, d, m, l, f, e, stripe=None):
    """A fish's key: its own ramp for the body (index 0 its outline), the belly a cream whose outline is the fish's."""
    belly = (ramp[o], IV[4])
    lit = (ramp[l],) if stripe is None else (stripe,)
    return {"o": (ramp, o), "d": (ramp, d), "m": (ramp, m), "l": ((ramp[o],) + lit, 1), "b": (belly, 1), "f": (ramp, f),
            "e": (ramp, e), "g": (SM, 3), "k": (ramp, o)}


FISH_KINDS = (
    _kind(GH[1:], 0, 1, 2, 3, 1, 0),                         # bass: green back, cream belly
    _kind((_ST[0], _ST[3], _ST[5], _ST[7]), 1, 2, 3, 3, 2, 0, stripe=CR[4]),   # trout: silver, a pink stripe
    _kind(CR[1:], 0, 1, 2, 3, 1, 0),                         # snapper: red, a pale belly
)


def fish():
    frames = []
    for key in FISH_KINDS:
        for rows in FISH_ROWS:
            p = Pix(12, 8)
            p.rows(0, 0, rows, key)
            p.outline(lit=False)
            p.rows(0, 0, [r.replace("o", ".").replace("d", ".").replace("m", ".").replace("l", ".").replace("b", ".")
                          .replace("f", ".") for r in rows], key)      # the eye and its glint over the outline
            frames.append(p.image())
    return frames


# --- the stun ----------------------------------------------------------------------------------------------------------
STAR_ROWS = (("..a..", ".aba.", "abcba", ".aba.", "..a.."), (".....", "..a..", ".aca.", "..a..", "....."))


def stars():
    key = {"a": (GI, 5), "b": (GI, 7), "c": (GI, 9)}
    out = []
    for rows in STAR_ROWS:
        p = Pix(5, 5)
        p.rows(0, 0, rows, key)
        out.append(p.image())
    return out


ICON_ROWS = (
    "................",
    "..............a.",
    ".....ssss....aba",
    "...ss....ss...a.",
    "..s..ssss..s....",
    ".s..s....s..s...",
    ".s.s..ss..s.s...",
    "s..s.s..s.s..s..",
    "s..s.s.ts.s..s..",
    "s..s..ss..s..s..",
    ".s..s....s..s...",
    ".s...ssss..s....",
    "..s.......s.....",
    "a..ss...ss......",
    "bc...sss........",
    "a...............",
)


def icon():
    p = Pix(16, 16)
    p.rows(0, 0, ICON_ROWS, {"s": (AE, 2), "t": (AE, 3), "a": (GI, 5), "b": (GI, 9), "c": (GI, 7)})
    # the spiral's lit half a step brighter
    for (x, y), (ramp, i) in list(p.m.items()):
        if ramp == tuple(tuple(c) for c in AE) and x + y < 14:
            p.put(x, y, AE, 3)
    return p.image()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    g = gun()
    print("gun colours:", len(g.colours()))
    export(g.image(), OUT_W + "BarrelGun.png")
    f = fish()
    export(sheet(f), OUT_W + "BarrelGunFish.png")
    export(icon(), OUT_B + "Stunned.png")
    export(sheet(stars()), OUT_B + "StunStars.png")
    if a.preview:
        preview([g.image()] + f + [icon()] + stars(), a.preview, scale=5)


if __name__ == "__main__":
    main()
