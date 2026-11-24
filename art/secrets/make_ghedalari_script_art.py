"""Source for the Ghedalari script (D4), 2026-11-24. Run from the repo root:

    python -P art/secrets/make_ghedalari_script_art.py [--preview FILE]

User, 2026-11-24: "rework so the runes (the Ghedalari language) are a custom created runic/symbolical language for our mod lore
and the translation to make sense so players that are immersed on the lore can actualy learn the language, it should convey
meaning through symbols but the symbols before translating have to be more abstract so players actualy need to translate to
learn" ... "It should only actualy show our symbols for fishing rod lake and bee when translated, while untransleted it should
show the Ghedalari symbols for it which you have to properly create based on runic symbols."

Every word has two forms, drawn on one 9x11 art px cell (18x22 in game):
* the RUNE: what the stones and the Last Ghedalari show. Straight one-pixel strokes (upright, level and at 45 degrees, as runes
  are cut), pale aether blue with a white mark where the word has its "eye". Each rune is its pictogram worn down to strokes,
  keeping the one feature a reader can learn it by: the rod's hook, the arrow's barb, the lake's two waves, the bee's wings
  over its body, the Ghedalari's two ears, the sun's rays, the stone's slab...
* the PICTOGRAM: what a translation shows (a stone's node researched in the Mystery of the Past): a small coloured picture of
  the thing, outlined, lit from the top-left (a brown rod with its line and hook, blue water, a striped bee...).
The tar pit's stone says only "...": the DOT is the same in both forms.

The words (their index is GhedalariScript.Word in the code): DOT, ROD, ARROW, LAKE, BEE, GHEDALARI, ONE, MANY, NOT, YOU, EAT,
HAPPY, GOLD, STONE, SLEEP, SUN. "Honey" has no word of its own: the Ghedalari never met it and call it bee-water (LAKE BEE,
as Westworld's stone writes it: "a lake + a bee").

Output: Content/Secrets/GhedalariGlyphs.png: the runes on the first row, the pictograms on the second; cells 18x22 on a
20 x 24 px stride.
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export  # noqa: E402
from rig import RAMP  # noqa: E402

CW, CH, SX, SY = 9, 11, 10, 12                             # art px: the cell and the stride (2 game px of gap)
OUT = "Content/Secrets/GhedalariGlyphs.png"
WORDS = ("DOT", "ROD", "ARROW", "LAKE", "BEE", "GHEDALARI", "ONE", "MANY", "NOT", "YOU", "EAT", "HAPPY", "GOLD", "STONE",
         "SLEEP", "SUN")

AE, DN, SM, OK, GI, CR, ST, EM = (RAMP[k] for k in ("aether", "denim", "steam", "oak", "gilt", "crimson", "steel", "emerald"))
RUNE = (DN[5], SM[3])                                       # the strokes, the mark

# --- the runes: '#' a stroke, '*' the mark -----------------------------------------------------------------------------------
RUNES = {
    "DOT": (".........", ".........", ".........", ".........", ".........", ".........", ".........", "...##....",
            "...##....", ".........", "........."),
    # the rod: a rising staff, the line dropping from its tip, the hook turned back at the foot
    "ROD": (".....#...", "....##...", "....#.#..", "...#..#..", "...#..#..", "..#...#..", "..#...#..", ".#...#*..",
            ".#.......", "#........", "........."),
    # the arrow ("towards", "then"): a staff, and the barb that points the way, cut apart from it
    "ARROW": ("#........", "#..#.....", "#...#....", "#....#...", "#.....*..", "#....#...", "#...#....", "#..#.....",
              "#........", ".........", "........."),
    # the lake: two waves cut as zigzags over the basin's line
    "LAKE": (".........", ".........", "#...#...#", ".#.#.#.#.", "..#...#..", "#...#...#", ".#.#.#.#.", "..#...#..",
             ".........", "#########", "........."),
    # the bee: a diamond body, a bar for its stripes, two wing strokes over it
    "BEE": ("#.......#", ".#.....#.", "..#...#..", "...#*#...", "..#...#..", ".#######.", "..#...#..", "...#.#...",
            "....#....", ".........", "........."),
    # the Ghedalari: a tall upright, its head marked, two long ears swept back from it, the legs bent back at the foot
    "GHEDALARI": ("....*....", "#...#...#", ".#..#..#.", "..#.#.#..", "....#....", "....#....", "....#....", "....#....",
                  "....##...", "....#.#..", "........."),
    "ONE": ("....#....", "....#....", "....#....", "....#....", "....#....", "....#....", "....#....", "....#....",
            "....#....", "....#....", "........."),
    # many: three uprights bound at the foot
    "MANY": ("#...#...#", "#...#...#", "#...#...#", "#...#...#", "#...#...#", "#...#...#", "#...#...#", "#...#...#",
             "#########", ".........", "........."),
    # not: a cross closed by a bar
    "NOT": ("#.......#", ".#.....#.", "..#...#..", "...#.#...", "....#....", "...#.#...", "..#...#..", ".#.....#.",
            "#.......#", "#########", "........."),
    # you: an upright with a closed head, one arm raised in greeting
    "YOU": ("...###...", "...#*#...", "...###...", "....#...#", "....#..#.", "....###..", "....#....", "....#....",
            "...#.#...", "..#...#..", "........."),
    # eat: an open mouth (a V) with a morsel falling in
    "EAT": ("....#....", ".........", "#...#...#", ".#.....#.", "..#...#..", "...#.#...", "....#....", ".........",
            ".........", ".........", "........."),
    # happy: a smile cut in three strokes, the eye's mark above
    "HAPPY": (".........", "....*....", ".........", "#.......#", "#.......#", ".#.....#.", "..#####..", ".........",
              ".........", ".........", "........."),
    # gold: a diamond (the coin seen edgewise in the light) with its glint
    "GOLD": ("....#....", "...#.#...", "..#...#..", ".#..*..#.", "#.......#", ".#.....#.", "..#...#..", "...#.#...",
             "....#....", ".........", "........."),
    # stone: the slab, its cut line down the middle
    "STONE": ("..#####..", "..#...#..", "..#.#.#..", "..#.#.#..", "..#.*.#..", "..#.#.#..", "..#.#.#..", "..#...#..",
              ".#######.", "#########", "........."),
    # sleep: a closed lid (a level stroke) with the lashes hanging
    "SLEEP": (".........", ".........", ".........", ".........", "#########", ".#..#..#.", "#...#...#", ".........",
              ".........", ".........", "........."),
    # sun: a ring cut as a diamond, four rays
    "SUN": ("....#....", "....#....", "...#.#...", "..#...#..", "##..*..##", "..#...#..", "...#.#...", "....#....",
            "....#....", ".........", "........."),
}

# --- the pictograms: letters for colours ------------------------------------------------------------------------------------
P_KEY = {
    "o": (OK, 0), "w": (OK, 2), "W": (OK, 3),               # wood
    "l": (SM, 1), "L": (SM, 2),                             # the fishing line, white
    "i": (ST, 2), "I": (ST, 5),                             # the hook, steel
    "b": (DN, 1), "B": (DN, 3), "C": (DN, 4), "D": (DN, 5),  # water
    "y": (GI, 1), "Y": (GI, 5), "Z": (GI, 7), "X": (GI, 8),  # gold, the bee's yellow
    "k": (ST, 1), "K": (ST, 3),                             # the bee's black stripes, eyes
    "s": (AE, 3), "S": (SM, 2),                             # wings, glint
    "u": (DN, 2), "U": (DN, 4), "V": (DN, 5), "e": (AE, 3), "E": (SM, 3),   # a Ghedalari's blue skin, his eye glow
    "r": (CR, 1), "R": (CR, 3), "P": (CR, 4),               # red
    "g": (EM, 1), "G": (EM, 3), "H": (EM, 5),               # green
    "d": (ST, 3), "D2": (ST, 6),
}
PICTOS = {
    "DOT": RUNES["DOT"],
    "ROD": (".......wo", "......wo.", "......wl.", ".....wo.l", ".....w..l", "....wo..l", "....w...l", "...wo...I",
            "..wo...iI", ".wo......", "oo......."),
    "ARROW": (".........", "....rr...", ".....RRr.", "......RPr", "rRRRRRPPr", "......RPr", ".....RRr.", "....rr...",
              ".........", ".........", "........."),
    "LAKE": (".........", ".........", "b.......b", "bD.D.D.Db", "bCDCDCDCb", "bBCBCBCBb", "bBBBBBBBb", ".bBBBBBb.",
             "..bbbbb..", ".........", "........."),
    "BEE": (".s.....s.", "sSs...sSs", ".sSs.sSs.", "..sZZZs..", ".YZkZkZY.", "YZZkZkZZY", ".YZkZkZY.", "..yYYYy..",
            "...yyy...", ".........", "........."),
    "GHEDALARI": ("..YYYY...", ".YXZZY...", ".uVVVu..U", "uVEeVUuU.", "uVVVVUu..", ".uVVUu...", "..uUUu...", "..ru.ur..",
                  ".rRRRRr..", "rRPPPRRr.", "........."),
    "ONE": (".........", ".........", ".........", "...YY....", "..YXZY...", "..YZZY...", "...YY....", ".........",
            ".........", ".........", "........."),
    "MANY": (".........", ".........", "....Y....", "...YXY...", "....Y....", ".Y.....Y.", "YXY...YXY", ".Y.....Y.",
             ".........", ".........", "........."),
    "NOT": ("r.......r", "rR.....Rr", ".rR...Rr.", "..rR.Rr..", "...rPr...", "..rR.Rr..", ".rR...Rr.", "rR.....Rr",
            "r.......r", ".........", "........."),
    "YOU": ("..wwwww..", ".wWWWWWw.", "...uVu...", "...VVV...", "..rRRRr..", ".uRPPRu..", "..rRRRr..", "...r.r...",
            "...w.w...", "..ww.ww..", "........."),
    "EAT": ("....ww...", "...wWw...", ".........", "rrrrrrrrr", "rLLLLLLLr", "rr.....rr", ".rPPPPPr.", "..rrrrr..",
            ".........", ".........", "........."),
    "HAPPY": ("..yyyyy..", ".yZZZZZy.", "yZkZZZkZy", "yZZZZZZZy", "yZkZZZkZy", "yZZkkkZZy", ".yZZZZZy.", "..yyyyy..",
              ".........", ".........", "........."),
    "GOLD": ("..yyyyy..", ".yXXZZZy.", "yXZZZZZYy", "yZZYYYZYy", "yZZYZZZYy", "yZZYYYZYy", "yZZZZZYYy", ".yYYYYYy.",
             "..yyyyy..", ".........", "........."),
    "STONE": ("..bbbbb..", ".bCCCCBb.", ".bCDsDBb.", ".bCDsDBb.", ".bCssDBb.", ".bCDsDBb.", ".bCDsDBb.", ".bCCCCBb.",
              "kkkkkkkkk", "kKKKKKKKk", "........."),
    "SLEEP": (".....XXXX", "........X", ".......X.", "......X..", "uuuuuXXXX", "uVVVVu...", ".uuuuu...", ".u.u.u...",
              ".........", ".........", "........."),
    "SUN": ("....Y....", ".Y..Y..Y.", "..yZZZy..", ".yZXXZZy.", "YyZXZZZyY", ".yZZZZZy.", "..yZZZy..", ".Y..Y..Y.",
            "....Y....", ".........", "........."),
}


def rune(word):
    p = Pix(CW, CH)
    for y, row in enumerate(RUNES[word]):
        for x, ch in enumerate(row):
            if ch == "#":
                p.put(x, y, RUNE, 0)
            elif ch == "*":
                p.put(x, y, RUNE, 1)
    return p.image()


def picto(word):
    p = Pix(CW, CH)
    rows = PICTOS[word]
    if word == "DOT":
        return rune(word)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in P_KEY:
                ramp, i = P_KEY[ch]
                p.put(x, y, ramp, i, lock=True)
    return p.image()


def sheet():
    out = Image.new("RGBA", (SX * len(WORDS), SY * 2), (0, 0, 0, 0))
    for k, w in enumerate(WORDS):
        assert len(RUNES[w]) == CH and all(len(r) == CW for r in RUNES[w]), w
        assert len(PICTOS[w]) == CH and all(len(r) == CW for r in PICTOS[w]), w
        out.alpha_composite(rune(w), (k * SX, 0))
        out.alpha_composite(picto(w), (k * SX, SY))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    im = sheet()
    if a.preview:
        bg = Image.new("RGBA", im.size, (14, 20, 46, 255))
        bg.alpha_composite(im)
        bg.resize((im.width * 6, im.height * 6), Image.NEAREST).save(a.preview)
        print("preview", a.preview)
        return
    export(im, OUT)


if __name__ == "__main__":
    main()
