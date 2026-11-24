"""Source for the Friendo-bot, Cogpunk's first town NPC (D4). Run from the repo root:

    python -P art/town/make_friendobo_art.py [--preview FILE]

Redrawn 2026-11-11 (user: "rework on friendo-bot npc (this should be his name now, replace it) it has to match default
terraria npc pixel density animations/behavior and details. you are free to change the design how you want to match the
quality level"; the 2026-11-04 rig-drawn version is archived in art/town/previous/make_friendobo_art_2026-11-11.py).

Vanilla's townsfolk, measured on terraria.wiki.gg's sprites (the Cyborg 12x24 art px, the Steampunker 11x25, the
Tavernkeep 16x24): a big head (9-10 art px with the hair or hat), a short torso, short legs, limbs 3 px thick, big flat
areas of 3-4 shades a material, every part outlined in its own darkest shade (the near arm too, over the body). So this
version is built from hand-placed parts, not a rig: each part (hat and head, torso, apron, a leg, an arm) is drawn at
1x as pixels, outlined on its own and laid over the ones behind it, and only whole pixels move between frames.

Design (old bartender robot, user 2026-11-03: "an old robot with a monocle and a top hat, bartender-like"):
* A short black top hat with a brass band, tipped back on a riveted copper head lit from the top-left.
* One big round lens for an eye in a brass monocle ring (aether blue, glowing: the friendly colours), a white handlebar
  moustache over a grille mouth, a brass ear bolt.
* A white collar and a black bow tie, a copper waistcoat with brass buttons over a white shirt front, a white bar apron.
* Steel piston arms with brass shoulder caps and round steel grippers; a white bar towel over the far arm.
* Steel legs with brass knees, dark boots with brass toe caps.

Vanilla's town NPC sheet (decompiled NPC.VanillaFindFrame for town NPCs, Main.npcFrameCount 25, NPCID.Sets
ExtraFramesCount 9 and AttackFrameCount 4, AnimationType = the Guide): 0 standing, 1 in the air, 2-15 walking, 16-17
the two gestures of a chat, 18 sitting, 19 talking, 20 blinking, 21-24 the throw (the Tavernkeep's mugs). 40x56 frames
with no gap; the soles on row 50 (vanilla draws NPC frames 4 px below the hitbox: decompiled Main.DrawNPCDirect). It
faces left like every NPC sheet (D4 rule 8).

Outputs (Content/Town/):
    Friendobo.png               40x1400  25 frames
    Friendobo_Head.png          the map and housing head (hat and face)
    Friendobo_Shimmer.png, Friendobo_Shimmer_Head.png   the shimmered look (chrome, navy, a green lens)
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
SOLE = 25                                    # the soles' bottom row (1x): 50-51 in game

CU, BR, GI, ST, IR, SM, AE, HD = (RAMP[k] for k in ("copper", "brass", "gilt", "steel", "iron", "steam", "aether", "hide"))
HAT = (ST[0], ST[1], ST[2], ST[3])                          # a black hat: steel's darkest shades
CLOTH = (ST[2], SM[0], SM[1], SM[2])                          # white cloth: outlined in dark grey (its own darkest is light)
LENS = (AE[0], AE[1], AE[2], AE[3])
BOOT = (HD[0], HD[1], HD[2], HD[3])
STEEL = (ST[0], ST[3], ST[5], ST[6], ST[7])
COPPER = tuple(CU)
BRASS = (BR[0], BR[2], BR[3], BR[4], BR[5])
VEST = tuple(RAMP["crimson"])                                 # a bartender's red waistcoat
NORMAL = dict(COPPER=COPPER, VEST=VEST, LENS=LENS)
# The shimmered look (vanilla's townsfolk each have one, NPCID.Sets.ShimmerTownTransform): a polished chrome head, a navy
# waistcoat and a green lens (my calls).
SHIMMER = dict(COPPER=(ST[0], ST[4], ST[6], ST[7], ST[8]), VEST=tuple(RAMP["denim"]),
               LENS=tuple(RAMP["ghost"][k] for k in (0, 2, 4, 5)))


def set_theme(theme):
    """Swaps the materials the parts are drawn in (the shimmered look) and rebuilds the part keys."""
    global COPPER, VEST, LENS, HEAD_KEY, TORSO_KEY
    COPPER, VEST, LENS = theme["COPPER"], theme["VEST"], theme["LENS"]
    HEAD_KEY = {
        "1": (HAT, 1), "2": (HAT, 2), "3": (HAT, 3),
        "y": (BRASS, 3), "b": (BRASS, 2), "Y": (BRASS, 4),
        "c": (COPPER, 1), "o": (COPPER, 2), "O": (COPPER, 3), "P": (COPPER, 4),
        "m": (BRASS, 3), "M": (BRASS, 4),
        "E": (LENS, 2), "L": (LENS, 3), "e": (LENS, 1),
        "W": (CLOTH, 3), "w": (CLOTH, 2), "g": (CLOTH, 1),
        "i": (STEEL, 0), "r": (BRASS, 4),
    }
    TORSO_KEY = {
        "W": (CLOTH, 3), "w": (CLOTH, 2), "g": (CLOTH, 1),
        "k": (HAT, 1), "K": (HAT, 2),
        "V": (VEST, 4), "v": (VEST, 3), "u": (VEST, 2),
        "y": (BRASS, 4), "s": (STEEL, 2), "S": (STEEL, 3),
    }


# --- parts as pixel rows: a letter -> (ramp, shade); outlined on their own -------------------------------------------
HEAD_KEY = TORSO_KEY = None
HEAD = (                                     # 11 x 13: the top hat, the round copper head, facing left
    "...12221...",
    "...32221...",
    "...32221...",
    "...Yyyyb...",
    ".132222221.",
    "...PPOOo...",
    "..PPOOOooc.",
    ".PmMmOOooc.",
    ".PMLEmOroc.",
    ".PmEEmOooc.",
    ".WWWmOoooc.",
    "WWgWiiooc..",
    "....cccc...",
)
HEAD_AT = (4, 0)                             # its top-left in the standing frame

TORSO = (                                    # 9 x 8: the neck, the collar and bow tie, the waistcoat over the shirt
    "...sS....",
    "..WWWWv..",
    ".VkKkWvv.",
    "VVVWWvvvu",
    "VVyWWyvvu",
    "VVVWWvvvu",
    "VVVyVvvvu",
    ".VVVVvvu.",
)
TORSO_AT = (5, 12)
APRON = (                                    # 8 x 4, tied at the waist, the front only, to the knees
    "WWWWWWw.",
    "WWWWWwg.",
    "WWWWwwg.",
    ".gggggg.",
)
APRON_AT = (5, 19)
set_theme(NORMAL)


def part(rows, key, at, dx=0, dy=0):
    p = Pix(FW, FH)
    p.rows(at[0] + dx, at[1] + dy, rows, key)
    return p


def blit(dst, src, darker=0):
    for q, (ramp, i) in src.m.items():
        dst.m[q] = (ramp, max(0, i - darker) if i > 0 else 0)


# --- limbs ----------------------------------------------------------------------------------------------------------------
def thick(p, a, b, r, ramp, lit, mid, dark):
    """A limb from a to b (pixel centres) r px each side of its axis: lit on its upper-left side, dark on the other."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln                     # the axis' left normal
    if nx + ny > 0:
        nx, ny = -nx, -ny                          # point it to the upper left (the light)
    x0, x1 = int(min(ax, bx) - r - 1), int(max(ax, bx) + r + 2)
    y0, y1 = int(min(ay, by) - r - 1), int(max(ay, by) + r + 2)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - ax - 0.5) * dx + (py - ay - 0.5) * dy) / (ln * ln)))
            cx, cy = ax + 0.5 + dx * t, ay + 0.5 + dy * t
            d = math.hypot(px - cx, py - cy)
            if d <= r:
                side = (px - cx) * nx + (py - cy) * ny
                p.put(x, y, ramp, lit if side > 0.35 else (dark if side < -0.35 else mid))


def arm(at, hand, far=False, towel=False):
    """A piston arm from the shoulder `at` to the hand: a brass shoulder cap, a steel arm 3 px thick with a brass elbow,
    a round steel gripper (bare metal, so it reads against the white shirt)."""
    p = Pix(FW, FH)
    sx, sy = at
    hx, hy = hand
    ex, ey = sx + (hx - sx) * 0.5, sy + (hy - sy) * 0.5
    thick(p, (sx, sy), (ex, ey), 1.5, STEEL, 4, 3, 2)
    thick(p, (ex, ey), (hx, hy), 1.3, STEEL, 4, 3, 2)
    for (ox, oy, i) in ((-1, -1, 4), (0, -1, 3), (-1, 0, 3), (0, 0, 2)):   # the shoulder cap
        p.put(int(sx) + ox, int(sy) + oy, BRASS, i)
    p.put(int(round(ex)), int(round(ey)), BRASS, 3)                        # the elbow
    for (ox, oy, i) in ((-1, 0, 4), (0, 0, 3), (1, 0, 2), (-1, 1, 3), (0, 1, 2), (1, 1, 2)):   # the gripper
        p.put(int(hx) + ox, int(hy) + oy, STEEL, i)
    if towel:                                    # a bar towel over the forearm
        for (ox, oy, i) in ((0, 0, 3), (1, 0, 3), (0, 1, 3), (1, 1, 2), (0, 2, 2), (1, 2, 1)):
            p.put(int(round(ex)) + ox, int(round(ey)) + oy, CLOTH, i)
    p.outline()
    if far:
        for q, (ramp, i) in list(p.m.items()):
            if i > 1:
                p.m[q] = (ramp, i - 1)
    return p


def leg(hip, foot, lift=0, far=False):
    """A steel leg from the hip to the boot: thigh and shin in one 3 px piston, a brass knee, a dark boot with a brass
    toe cap. `foot` is the boot's heel column; the boot points left (forward)."""
    p = Pix(FW, FH)
    hx, hy = hip
    fx = foot
    ankle = (fx + 1, SOLE - 2 - lift)
    thick(p, (hx, hy), ankle, 1.4, STEEL, 4, 3, 2)
    kx, ky = int(round((hx + ankle[0]) / 2.0)), int(round((hy + ankle[1]) / 2.0))
    p.put(kx, ky, BRASS, 4)                        # the knee
    p.put(kx + 1, ky, BRASS, 2)
    for x in range(fx - 2, fx + 2):                # the boot: 4 wide, 2 tall, the toe forward
        for y in (SOLE - 1 - lift, SOLE - lift):
            p.put(x, y, BOOT, 3 if y == SOLE - 1 - lift and x < fx + 1 else 2)
    p.put(fx - 2, SOLE - lift, BRASS, 3)           # the toe cap
    p.put(fx - 2, SOLE - 1 - lift, BRASS, 4)
    p.outline()
    if far:
        for q, (ramp, i) in list(p.m.items()):
            if i > 1:
                p.m[q] = (ramp, i - 1)
    return p


# --- frames ---------------------------------------------------------------------------------------------------------------
class Pose:
    def __init__(self, bob=0, near_foot=8, far_foot=11, near_lift=0, far_lift=0, near_hand=(11, 21), far_hand=(10, 20),
                 sit=False, mouth=False, blink=False, head_dy=0):
        self.bob = bob                              # whole px the body is raised (-) or lowered (+)
        self.near_foot, self.far_foot = near_foot, far_foot     # the boots' heel columns
        self.near_lift, self.far_lift = near_lift, far_lift
        self.near_hand, self.far_hand = near_hand, far_hand     # the grippers, before the bob
        self.sit, self.mouth, self.blink, self.head_dy = sit, mouth, blink, head_dy


NEAR_SHOULDER, FAR_SHOULDER = (11, 15), (10, 14)
NEAR_HIP, FAR_HIP = (8, 20), (11, 20)


def frame(p):
    img = Pix(FW, FH)
    b = p.bob
    if p.sit:
        b = 2
    # the far side: arm, leg
    blit(img, arm((FAR_SHOULDER[0], FAR_SHOULDER[1] + b), (p.far_hand[0], p.far_hand[1] + b), far=True, towel=True))
    if p.sit:
        blit(img, sit_leg(FAR_HIP[0] + 1, b, far=True))
    else:
        blit(img, leg((FAR_HIP[0], FAR_HIP[1] + b), p.far_foot, p.far_lift, far=True))
    # the torso, the near leg, the apron
    t = part(TORSO, TORSO_KEY, TORSO_AT, 0, b)
    t.outline()
    blit(img, t)
    if p.sit:
        blit(img, sit_leg(NEAR_HIP[0], b))
    else:
        blit(img, leg((NEAR_HIP[0], NEAR_HIP[1] + b), p.near_foot, p.near_lift))
    a = part(APRON, TORSO_KEY, APRON_AT, 0, b if not p.sit else b - 2)
    a.outline()
    blit(img, a)
    # the head
    rows = list(HEAD)
    if p.blink:                                     # the lens dims
        rows = [r.replace("L", "e").replace("E", "e") for r in rows]
    if p.mouth:                                     # the grille drops open
        rows[11] = "WWgW..ooc.."
        rows[12] = "...iicccc.."
    h = part(rows, HEAD_KEY, HEAD_AT, 0, b + p.head_dy)
    h.outline()
    blit(img, h)
    # the near arm, over everything
    blit(img, arm((NEAR_SHOULDER[0], NEAR_SHOULDER[1] + b), (p.near_hand[0], p.near_hand[1] + b)))
    return img


def sit_leg(hx, b, far=False):
    """Sitting: the thigh forward, the shin down, the boot on the ground."""
    p = Pix(FW, FH)
    hy = NEAR_HIP[1] + b - 1
    knee = (hx - 4, hy)
    thick(p, (hx, hy), knee, 1.4, STEEL, 4, 3, 2)
    thick(p, knee, (knee[0], SOLE - 2), 1.3, STEEL, 4, 3, 2)
    p.put(knee[0], knee[1] - 1, BRASS, 4)
    for x in range(knee[0] - 2, knee[0] + 2):
        for y in (SOLE - 1, SOLE):
            p.put(x, y, BOOT, 3 if y == SOLE - 1 else 2)
    p.put(knee[0] - 2, SOLE, BRASS, 3)
    p.outline()
    if far:
        for q, (ramp, i) in list(p.m.items()):
            if i > 1:
                p.m[q] = (ramp, i - 1)
    return p


def walk_pose(k):
    """14 walking frames: a full stride (the boots 3 px either side of their rest), the near boot lifted on its way
    forward, the far one on its way back, the arms swinging against the legs, a 1 px bob up as the legs pass."""
    ph = 2.0 * math.pi * k / 14.0
    s = math.cos(ph)
    near = 8 + int(round(-3.0 * s))
    far = 11 + int(round(3.0 * s))
    near_lift = 1 if math.sin(ph) > 0.5 else 0
    far_lift = 1 if math.sin(ph) < -0.5 else 0
    bob = -1 if abs(s) < 0.45 else 0
    swing = int(round(2.0 * s))
    return Pose(bob=bob, near_foot=near, far_foot=far, near_lift=near_lift, far_lift=far_lift,
                near_hand=(11 + swing, 21), far_hand=(10 - swing, 20))


FRAMES = ([Pose(), Pose(near_foot=6, far_foot=13, near_lift=1, far_lift=0, near_hand=(14, 17), far_hand=(7, 17))]
          + [walk_pose(k) for k in range(14)]
          + [Pose(near_hand=(7, 17)), Pose(near_hand=(7, 14)),                           # 16-17: the gestures
             Pose(sit=True, near_hand=(8, 21)), Pose(mouth=True), Pose(blink=True),     # 18 sit, 19 talk, 20 blink
             Pose(near_hand=(15, 16)), Pose(near_hand=(14, 11)),                          # 21-22: the arm back, up
             Pose(near_hand=(6, 14)), Pose(near_hand=(7, 19))])                           # 23-24: the throw, the follow-through


def image(p):
    return frame(p).image()


def head_icon():
    """The map and housing head: the hat and the face, cropped from the standing frame."""
    h = part(HEAD, HEAD_KEY, (0, 0))
    h.outline()
    im = h.image()
    return im.crop(im.getbbox())


EMOTE_W, EMOTE_H = 17, 14


def emote():
    """The face emote other townsfolk show when they talk about him (NPCID.Sets.FaceEmote): two frames side by side in
    vanilla's 34x28 cell (decompiled EmoteBubble.Draw: a mod emote's texture is Frame(2, 1, frame)), the head and the head
    blinking; vanilla draws the bubble round it."""
    out = Pix(EMOTE_W * 2, EMOTE_H)
    for k in range(2):
        rows = list(HEAD) if k == 0 else [r.replace("L", "e").replace("E", "e") for r in HEAD]
        h = Pix(EMOTE_W * 2, EMOTE_H)
        h.rows(k * EMOTE_W + 3, 0, rows, HEAD_KEY)
        h.outline()
        out.m.update(h.m)
    return out.image()


def gores():
    def crop(p):
        im = p.image()
        return im.crop(im.getbbox())
    h = part(HEAD, HEAD_KEY, (0, 0))
    h.outline()
    return {"Friendobo_GoreHead": crop(h),
            "Friendobo_GoreArm": crop(arm((3, 2), (3, 8))),
            "Friendobo_GoreLeg": crop(leg((6, SOLE - 7), 5))}


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
    sh = sheet()
    cols = 13
    rows = 2
    out = Image.new("RGBA", (FW * cols, FH * rows * 2), (36, 40, 48, 255))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (FW * cols, FH * rows), bg)
        for k in range(len(FRAMES)):
            tile.alpha_composite(sh.crop((0, k * FH, FW, (k + 1) * FH)), ((k % cols) * FW, (k // cols) * FH))
        out.paste(tile, (0, half * FH * rows))
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
