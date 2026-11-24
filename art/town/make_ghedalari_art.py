"""Source for the Last Ghedalari, Cogpunk's first town NPC (D4), 2026-11-24. Run from the repo root:

    python -P art/town/make_ghedalari_art.py [--preview FILE]

User, 2026-11-24: "remake our main npc Friendobot it will now be called "last Ghedalari" an ancient humanoid species core
for our mod lore. the design should be based on the draenei for the biological body features (skin color, bigger ears,
hoofs/bended backwards legs, glow eyes without pulpil), and on the zandalari trolls for the culture adornments (armors,
weapons, inka based structures, clothes)", with three reference pictures (a pair of draenei, a pair of Zandalari trolls in
gold armour). They are used for the features and the colours, never traced. The robot he replaces (the Friendo-bot of
2026-11-11) is archived in art/town/previous/make_friendobo_art_2026-11-24.py.

Vanilla's townsfolk, as for the robot (art/town/make_friendobo_art.py's notes, measured on terraria.wiki.gg's sprites): a
20x28 art cell, a big head, limbs 3 px thick, flat areas of 3-4 shades a material, every part outlined in its own darkest
shade, only whole pixels moving between frames. Built from hand-placed parts (ASCII rows) and limbs drawn as 3 px tubes.

Design (my calls inside the user's brief):
* Blue skin (the palette's denim ramp), a long ear swept back from the side of the head, eyes that glow pale lavender and
  white with no pupil, violet-black hair falling down his back.
* A stepped gold headdress (the Inca step on its crest) over a gold brow band; a broad gold collar with a sun disc on a
  bare chest; a stepped gold pauldron on the near shoulder, gold arm bands and bracers.
* A gold belt with a stepped plate, a red loincloth trimmed in teal.
* Legs bent backwards (thigh forward, shin back, a long foot forward) with gold greaves, dark hooves.
* A spear in the far hand: an oak shaft, a leaf-shaped steel head on a gold socket and a red and teal tassel.

Frames (vanilla's town NPC sheet, decompiled NPC.VanillaFindFrame; Main.npcFrameCount 25, ExtraFramesCount 9,
AttackFrameCount 4, AnimationType = the Guide): 0 standing, 1 in the air, 2-15 walking, 16-17 the chat gestures, 18 sitting,
19 talking, 20 blinking, 21-24 the throw (he throws javelins). 40x56 frames with no gap, the soles on row 50; faces left.

Outputs (Content/Town/; the class keeps its old name, Friendobo, for saves):
    Friendobo.png               40x1400  25 frames
    Friendobo_Head.png          the map and housing head
    Friendobo_Shimmer.png, Friendobo_Shimmer_Head.png   the shimmered look (violet skin, jade where the gold was)
    FriendoboEmote.png          68x28, the face emote: 2 frames of vanilla's 34x28
    Gores/Friendobo_GoreHead.png, _GoreArm.png, _GoreLeg.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "templates"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from pixkit import Pix, export  # noqa: E402
from rig import RAMP  # noqa: E402

OUT = "Content/Town/"
FW, FH = 20, 28
SOLE = 25                                    # the hooves' bottom row (1x): 50-51 in game

DN, GI, CR, VD, AE, SM, ST, OK = (RAMP[k] for k in ("denim", "gilt", "crimson", "verd", "aether", "steam", "steel", "oak"))
EM = RAMP["emerald"]

# every ramp's index 0 is its outline (pixkit's outline() writes it)
NORMAL = dict(
    SKIN=(DN[1], DN[3], DN[4], DN[5], AE[3]),
    GOLD=(GI[1], GI[3], GI[5], GI[7], GI[8]),
    RED=(CR[1], CR[2], CR[3], CR[4]),
    TEAL=(VD[0], VD[1], VD[2], VD[3]),
    HAIR=(AE[0], DN[2], AE[1]),
    EYE=(AE[3], SM[3]),
)
# the shimmered look (vanilla's townsfolk each have one): pale violet skin, jade where the gold was, a teal loincloth
SHIMMER = dict(
    SKIN=(AE[0], AE[1], AE[2], AE[3], SM[2]),
    GOLD=(EM[1], EM[2], EM[3], EM[4], EM[5]),
    RED=(CR[1], CR[2], CR[3], CR[4]),
    TEAL=(VD[0], VD[1], VD[2], VD[3]),
    HAIR=(DN[0], DN[2], DN[3]),
    EYE=(EM[5], SM[3]),
)
HOOF = (ST[1], ST[2], ST[3], ST[5])
WOOD = (OK[0], OK[2], OK[3], OK[4])
BLADE = (ST[2], ST[5], ST[7], ST[8])

SKIN = GOLD = RED = TEAL = HAIR = EYE = None
KEY = {}


def set_theme(theme):
    global SKIN, GOLD, RED, TEAL, HAIR, EYE, KEY
    SKIN, GOLD, RED, TEAL, HAIR, EYE = (theme[k] for k in ("SKIN", "GOLD", "RED", "TEAL", "HAIR", "EYE"))
    KEY = {
        "k": (SKIN, 0), "a": (SKIN, 1), "s": (SKIN, 2), "S": (SKIN, 3), "L": (SKIN, 4),
        "q": (GOLD, 0), "x": (HAIR, 0), "z": (RED, 0), "y": (TEAL, 0),
        "g": (GOLD, 1), "G": (GOLD, 2), "Y": (GOLD, 3), "W": (GOLD, 4),
        "r": (RED, 1), "R": (RED, 2), "P": (RED, 3),
        "t": (TEAL, 1), "T": (TEAL, 2), "U": (TEAL, 3),
        "h": (HAIR, 1), "H": (HAIR, 2),
        "e": (EYE, 0), "E": (EYE, 1),
        "f": (HOOF, 1), "F": (HOOF, 2), "v": (HOOF, 3),
        "o": (WOOD, 1), "O": (WOOD, 2), "w": (WOOD, 3),
        "i": (BLADE, 1), "I": (BLADE, 2), "j": (BLADE, 3),
    }


set_theme(NORMAL)

# --- parts as pixel rows (facing left) --------------------------------------------------------------------------------------
HEAD = (                                     # 13 x 11: the stepped crest and its plume, the face, the long ear, the hair
    ".....qWq.....",
    "....qYWYq..T.",
    "...qGYYYGq.TT",
    "..qgGYWYGgqqT",
    "..kLLSSSshhk.",
    ".kLSaaSSsSLLk",
    ".kSSSSSSskkk.",
    "kLSSSSSsHhk..",
    ".kSSSSssHk...",
    "..kSaSssk....",
    "...kkkkk.....",
)
HEAD_AT = (3, 0)
EYES = ((6, 6), (7, 6))                      # the glow's pixels in the frame (E then e), re-stamped after the outline

TORSO = (                                    # 10 x 8: the neck, the gold collar and sun pendant over a red uncu (tunic) with
    "...ksk....",                            # a stepped teal band across the chest, a gold sash, a teal hem
    ".qYYWYYq..",
    "zqGYWYGqz.",
    "zRRqWqRrz.",
    "zPRtUtRrz.",
    "zRqGYGqrz.",
    "zPRRRrrrz.",
    ".zTtUtTz..",
)
TORSO_AT = (5, 11)

PAULDRON = (                                 # 4 x 3: the near shoulder's stepped gold
    ".YW.",
    "YWYY",
    "GYGg",
)


def part(rows, at, dx=0, dy=0):
    p = Pix(FW, FH)
    p.rows(at[0] + dx, at[1] + dy, rows, KEY)
    return p


def blit(dst, src):
    for q, v in src.m.items():
        dst.m[q] = v


def darker(p, steps=1):
    for q, (ramp, i) in list(p.m.items()):
        if i > 1:
            p.m[q] = (ramp, max(1, i - steps))
    return p


def thick(p, a, b, r, ramp, lit, mid, dark):
    """A limb from a to b (pixel centres) r px each side of its axis: lit on its upper-left side, dark on the other."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln
    if nx + ny > 0:
        nx, ny = -nx, -ny
    x0, x1 = int(min(ax, bx) - r - 1), int(max(ax, bx) + r + 2)
    y0, y1 = int(min(ay, by) - r - 1), int(max(ay, by) + r + 2)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - ax - 0.5) * dx + (py - ay - 0.5) * dy) / (ln * ln)))
            cx, cy = ax + 0.5 + dx * t, ay + 0.5 + dy * t
            if math.hypot(px - cx, py - cy) <= r:
                side = (px - cx) * nx + (py - cy) * ny
                p.put(x, y, ramp, lit if side > 0.35 else (dark if side < -0.35 else mid))


# --- limbs ----------------------------------------------------------------------------------------------------------------
def arm(shoulder, hand, far=False, pauldron=False):
    """A blue arm from the shoulder to the hand, a gold bracer at the wrist, the hand a skin knot; the near one wears the
    stepped gold pauldron."""
    p = Pix(FW, FH)
    sx, sy = shoulder
    hx, hy = hand
    ex, ey = sx + (hx - sx) * 0.5, sy + (hy - sy) * 0.5
    thick(p, (sx, sy), (ex, ey), 1.3, SKIN, 3, 2, 1)
    thick(p, (ex, ey), (hx, hy), 1.1, SKIN, 3, 2, 1)
    wx, wy = sx + (hx - sx) * 0.8, sy + (hy - sy) * 0.8              # the bracer
    for ox in (-1, 0):
        p.put(int(round(wx)) + ox, int(round(wy)), GOLD, 3 if ox < 0 else 2)
    for (ox, oy, i) in ((-1, 0, 3), (0, 0, 2), (-1, 1, 2), (0, 1, 2)):  # the hand
        p.put(int(hx) + ox, int(hy) + oy, SKIN, i)
    p.outline()
    if pauldron:
        q = Pix(FW, FH)
        q.rows(int(sx) - 2, int(sy) - 2, PAULDRON, KEY)
        q.outline()
        blit(p, q)
    if far:
        darker(p)
    return p


def spear(hand):
    """The spear upright in the far hand: an oak shaft, a leaf-shaped steel head on a gold socket, a red and teal tassel."""
    p = Pix(FW, FH)
    hx, hy = hand
    x = int(hx)
    top = max(1, hy - 17)
    for y in range(top + 4, min(SOLE, hy + 8)):
        p.put(x, y, WOOD, 2 if y % 5 else 1)
    for y, (x0, x1, lit) in zip(range(top - 1, top + 3), ((0, 0, 3), (-1, 0, 3), (-1, 1, 2), (0, 0, 2))):   # the head
        for xx in range(x + x0, x + x1 + 1):
            p.put(xx, y, BLADE, lit if xx <= x else lit - 1)
    p.put(x, top + 3, GOLD, 3)                                       # the socket
    p.put(x, top + 4, GOLD, 2)
    p.put(x + 1, top + 4, RED, 3)                                    # the tassel
    p.put(x + 1, top + 5, RED, 2)
    p.put(x + 1, top + 6, TEAL, 2)
    p.outline()
    return p


def leg(hip, hoof, lift=0, far=False):
    """A leg bent backwards: a strong thigh forward to the knee, the shin back to the hock (a gold greave), a long foot down to
    the hoof. `hoof` is the hoof's column; it points left (forward)."""
    p = Pix(FW, FH)
    hx, hy = hip
    fy = SOLE - lift
    knee = (hx - 2.0, hy + 3.5)
    hock = (hoof + 2.0, fy - 2.5)
    thick(p, (hx, hy), knee, 1.7, SKIN, 3, 2, 1)
    thick(p, knee, hock, 1.3, SKIN, 3, 2, 1)
    thick(p, hock, (hoof + 0.5, fy - 1.0), 1.0, SKIN, 3, 2, 1)
    gx, gy = knee[0] + (hock[0] - knee[0]) * 0.55, knee[1] + (hock[1] - knee[1]) * 0.55    # the greave over the shin
    for (ox, i) in ((-1, 3), (0, 3), (1, 2)):
        p.put(int(round(gx)) + ox, int(round(gy)), GOLD, i)
    for xx in range(hoof - 1, hoof + 2):                              # the hoof: 3 wide, 2 tall, dark
        p.put(xx, fy - 1, HOOF, 3 if xx == hoof - 1 else 2)
        p.put(xx, fy, HOOF, 1)
    p.outline()
    if far:
        darker(p)
    return p


def sit_leg(hip, far=False):
    p = Pix(FW, FH)
    hx, hy = hip
    knee = (hx - 4, hy)
    thick(p, (hx, hy), knee, 1.5, SKIN, 3, 2, 1)
    hock = (knee[0] + 1, SOLE - 2)
    thick(p, knee, hock, 1.3, SKIN, 3, 2, 1)
    p.put(int(knee[0]), int(knee[1]) + 1, GOLD, 3)
    for xx in range(int(hock[0]) - 2, int(hock[0]) + 1):
        p.put(xx, SOLE - 1, HOOF, 3 if xx == int(hock[0]) - 2 else 2)
        p.put(xx, SOLE, HOOF, 1)
    p.outline()
    if far:
        darker(p)
    return p


# --- frames ---------------------------------------------------------------------------------------------------------------
class Pose:
    def __init__(self, bob=0, near_hoof=7, far_hoof=10, near_lift=0, far_lift=0, near_hand=(12, 20), far_hand=(14, 18),
                 sit=False, mouth=False, blink=False):
        self.bob = bob
        self.near_hoof, self.far_hoof = near_hoof, far_hoof
        self.near_lift, self.far_lift = near_lift, far_lift
        self.near_hand, self.far_hand = near_hand, far_hand
        self.sit, self.mouth, self.blink = sit, mouth, blink


NEAR_SHOULDER, FAR_SHOULDER = (12, 13), (12, 12)
NEAR_HIP, FAR_HIP = (8, 17), (10, 17)


def frame(p):
    img = Pix(FW, FH)
    b = 2 if p.sit else p.bob
    # the far side: the spear, the arm holding it, the leg
    fh = (p.far_hand[0], p.far_hand[1] + b)
    blit(img, darker(spear(fh)))
    blit(img, arm((FAR_SHOULDER[0], FAR_SHOULDER[1] + b), fh, far=True))
    blit(img, sit_leg((FAR_HIP[0], FAR_HIP[1] + b), far=True) if p.sit
         else leg((FAR_HIP[0], FAR_HIP[1] + b), p.far_hoof, p.far_lift, far=True))
    # the near leg, then the tunic over both
    blit(img, sit_leg((NEAR_HIP[0], NEAR_HIP[1] + b)) if p.sit else leg((NEAR_HIP[0], NEAR_HIP[1] + b), p.near_hoof, p.near_lift))
    t = part(TORSO, TORSO_AT, 0, b)
    t.outline()
    blit(img, t)
    rows = list(HEAD)
    if p.mouth:
        rows[8] = ".kSkkkahk...."
        rows[9] = "..kkaakhhk..."
    h = part(rows, HEAD_AT, 0, b)
    h.outline()
    blit(img, h)
    blit(img, arm((NEAR_SHOULDER[0], NEAR_SHOULDER[1] + b), (p.near_hand[0], p.near_hand[1] + b), pauldron=True))
    # the eyes glow over everything (no outline): lavender round a white core, shut to a skin line on a blink
    for k, (x, y) in enumerate(EYES):
        if p.blink:
            img.put(x, y + b, SKIN, 1)
        else:
            img.put(x, y + b, EYE, 1 if k == 0 else 0, lock=True)
    return img


def walk_pose(k):
    ph = 2.0 * math.pi * k / 14.0
    s = math.cos(ph)
    near = 7 + int(round(-3.0 * s))
    far = 10 + int(round(3.0 * s))
    near_lift = 1 if math.sin(ph) > 0.5 else 0
    far_lift = 1 if math.sin(ph) < -0.5 else 0
    bob = -1 if abs(s) < 0.45 else 0
    swing = int(round(2.0 * s))
    return Pose(bob=bob, near_hoof=near, far_hoof=far, near_lift=near_lift, far_lift=far_lift,
                near_hand=(12 + swing, 20), far_hand=(14 - (1 if swing > 0 else 0), 18))


FRAMES = ([Pose(), Pose(near_hoof=5, far_hoof=12, near_lift=1, near_hand=(13, 16), far_hand=(13, 16))]
          + [walk_pose(k) for k in range(14)]
          + [Pose(near_hand=(6, 17)), Pose(near_hand=(7, 13)),                         # 16-17: the gestures
             Pose(sit=True, near_hand=(7, 20)), Pose(mouth=True), Pose(blink=True),   # 18 sit, 19 talk, 20 blink
             Pose(near_hand=(14, 15)), Pose(near_hand=(13, 9)),                         # 21-22: the arm back, up
             Pose(near_hand=(5, 12)), Pose(near_hand=(6, 18))])                         # 23-24: the throw, the follow-through


def image(p):
    return frame(p).image()


def head_only(blink=False):
    h = Pix(14, 13)
    h.rows(0, 0, HEAD, KEY)
    h.outline()
    for k, (x, y) in enumerate(EYES):
        x -= HEAD_AT[0]
        y -= HEAD_AT[1]
        if blink:
            h.put(x, y, SKIN, 1)
        else:
            h.put(x, y, EYE, 1 if k == 0 else 0, lock=True)
    return h


def head_icon():
    im = head_only().image()
    return im.crop(im.getbbox())


EMOTE_W, EMOTE_H = 17, 14


def emote():
    """The face emote (NPCID.Sets.FaceEmote): two frames side by side in vanilla's 34x28 cell (decompiled EmoteBubble.Draw:
    Frame(2, 1, frame)), the head and the head blinking; vanilla draws the bubble round it."""
    out = Image.new("RGBA", (EMOTE_W * 2, EMOTE_H), (0, 0, 0, 0))
    for k in range(2):
        im = head_only(blink=k == 1).image()
        im = im.crop(im.getbbox())
        out.alpha_composite(im, (k * EMOTE_W + (EMOTE_W - im.width) // 2, max(0, EMOTE_H - im.height)))
    return out


def gores():
    def crop(p):
        im = p.image()
        return im.crop(im.getbbox())
    return {"Friendobo_GoreHead": crop(head_only()),
            "Friendobo_GoreArm": crop(arm((4, 2), (4, 9), pauldron=True)),
            "Friendobo_GoreLeg": crop(leg((7, SOLE - 8), 6))}


def sheet():
    out = Image.new("RGBA", (FW, FH * len(FRAMES)), (0, 0, 0, 0))
    for k, p in enumerate(FRAMES):
        out.alpha_composite(image(p), (0, k * FH))
    return out


def export_all():
    set_theme(NORMAL)
    export(sheet(), OUT + "Friendobo.png")
    export(head_icon(), OUT + "Friendobo_Head.png")
    export(emote(), OUT + "FriendoboEmote.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")
    set_theme(SHIMMER)
    export(sheet(), OUT + "Friendobo_Shimmer.png")
    export(head_icon(), OUT + "Friendobo_Shimmer_Head.png")
    set_theme(NORMAL)


def preview(path, scale=6):
    rows = []
    for theme in (NORMAL, SHIMMER):
        set_theme(theme)
        rows.append(sheet())
    set_theme(NORMAL)
    cols = 13
    n = len(FRAMES)
    out = Image.new("RGBA", (FW * cols, FH * 4 * 2), (0, 0, 0, 255))
    for t, sh in enumerate(rows):
        for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
            band = Image.new("RGBA", (FW * cols, FH * 2), bg)
            for k in range(n):
                band.alpha_composite(sh.crop((0, k * FH, FW, (k + 1) * FH)), ((k % cols) * FW, (k // cols) * FH))
            out.paste(band, (0, (t * 2 + half) * FH * 2))
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
