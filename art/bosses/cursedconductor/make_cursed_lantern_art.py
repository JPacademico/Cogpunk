"""Source for the Cursed Lantern (D4), the Cursed Conductor's mage weapon (user, 2026-11-06). Run from the repo root:

    python -P art/bosses/cursedconductor/make_cursed_lantern_art.py

The Conductor's own railway lantern (his gore: an iron frame, a brass cap, a glowing glass) with a lost soul burning in
it: a brass bail handle, a domed brass cap with a chimney, four iron bars round a glass chamber where a soul flame burns
with two dark eyes, a brass foot. Its soul fire is the friendly colour (D3: friendly effects are Brass and Aether), a
violet-blue wisp with a white core, not the Conductor's hostile ghost green. Drawn at 1x in palette letters, exported at
2x nearest-neighbour, lit from the top-left; every material outlined in its ramp's darkest shade.

Redrawn smaller 2026-11-09 (user: "the lantern mage weapon should not be used on the player head! the player should use
it on the hand (smaller lantern) like default terraria books are used"): 10x14 art px, held out in the hand toward the
cursor (vanilla's spell-tome use style); the old 14x20 lantern is LANTERN_2026_11_06 below.

Outputs:
    Content/Bosses/CursedConductor/Weapons/CursedLantern.png        20x28 the item (held out in the hand when used)
    Content/Bosses/CursedConductor/Weapons/SoulFire.png, _Glow.png  20x116: four 20x28 flicker frames, 2 px under each;
                                                                    the glow sheet is the flame's bright inside
"""
import os

from PIL import Image

ROOT = os.getcwd()
OUT = "Content/Bosses/CursedConductor/Weapons/"

PAL = {
    "A": (43, 26, 14), "B": (90, 58, 23), "C": (114, 74, 27), "D": (138, 93, 34), "E": (162, 116, 42), "F": (184, 138, 51),
    "G": (205, 163, 63), "H": (223, 185, 78), "I": (246, 231, 161),                       # Gilt: the brass
    "0": (21, 22, 28), "1": (46, 50, 59), "2": (61, 66, 78), "3": (79, 85, 98), "4": (102, 109, 123),   # Steel: the frame
    "a": (34, 26, 69), "b": (70, 58, 147), "c": (124, 107, 224), "d": (198, 189, 255),    # Aether: the soul
    "u": (238, 241, 243), "U": (255, 255, 255),                                            # Steam: the core
}

LANTERN_2026_11_06 = ["....BBBBBB....",
           "...BH....FB...",
           "..BG......DB..",
           "..B........B..",
           "......BB......",
           ".....BHFB.....",
           "....BGHFDB....",
           "...BGHGFEDB...",
           "..AFFFEEDDCA..",
           "..A0000000A...",
           "..12dbbbcb21..",
           "..12bcddcb21..",
           "..12bdUUdb21..",
           "..12cd0d0c21..",
           "..12cdddcb21..",
           "..12bcdcbb21..",
           "..12abccba21..",
           "..A0000000A...",
           "..ADFFFEDDCA..",
           "...ABBBBBBA..."]


LANTERN = ["...BBBB...",
           "..B....B..",
           "....BB....",
           "...BHFB...",
           "..BGHFDB..",
           ".AFHFEDDA.",
           ".A0000000.",
           ".12bcdc21.",
           ".12cdUd21.",
           ".12dUUd21.",
           ".12bccb21.",
           ".A0000000.",
           ".ADFFEDCA.",
           "..ABBBBA.."]


def lantern():
    w = max(len(r) for r in LANTERN)
    rows = [r.ljust(w, ".") for r in LANTERN]
    return rows


SOUL = [
    ["....d.....",
     "...dc..d..",
     "...cdc.c..",
     "..cdUdcc..",
     ".cdUUUdc..",
     ".cdU0U0dc.",
     ".cdUUUUdc.",
     ".bcdUUdcb.",
     ".bcddddcb.",
     "..bcdddcb.",
     "..abccbba.",
     "...abbba..",
     "....aaa...",
     ".........."],
    [".....d....",
     "..d..cd...",
     "..c.cdc...",
     "..ccdUdc..",
     "..cdUUUdc.",
     ".cd0U0Udc.",
     ".cdUUUUdc.",
     ".bcdUUdcb.",
     ".bcddddcb.",
     ".bcdddcb..",
     ".abbccba..",
     "..abbba...",
     "...aaa....",
     ".........."],
    ["...d......",
     "...cd..d..",
     "..cdc.dc..",
     "..cdUdcc..",
     ".cdUUUdc..",
     ".cdU0U0dc.",
     ".cdUUUUdc.",
     ".bcdUUdcb.",
     ".bcddddcb.",
     "..bcdddcb.",
     "..abcccba.",
     "...abbba..",
     "...aaa....",
     ".........."],
    ["......d...",
     "..d..dc...",
     "..cd.cdc..",
     "..ccdUdc..",
     "..cdUUUdc.",
     ".cd0U0Udc.",
     ".cdUUUUdc.",
     ".bcdUUdcb.",
     ".bcddddcb.",
     ".bcdddcb..",
     ".abccbba..",
     "..abbba...",
     "....aaa...",
     ".........."],
]
GLOW = set("dUu")


def image(rows, keep=None):
    w, h = len(rows[0]), len(rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != "." and (keep is None or ch in keep):
                px[x, y] = PAL[ch] + (255,)
    return im


def sheet(frames, keep=None, pad=1):
    w, h = len(frames[0][0]), len(frames[0])
    out = Image.new("RGBA", (w, (h + pad) * len(frames)), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        out.alpha_composite(image(f, keep), (0, k * (h + pad)))
    return out


def export(im, rel):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)
    print("wrote %s (%dx%d)" % (rel, im.width * 2, im.height * 2))


def main():
    export(image(lantern()), OUT + "CursedLantern.png")
    export(sheet(SOUL), OUT + "SoulFire.png")
    export(sheet(SOUL, keep=GLOW), OUT + "SoulFire_Glow.png")


if __name__ == "__main__":
    main()
