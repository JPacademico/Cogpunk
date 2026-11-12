"""Source for Friendobô, Cogpunk's first town NPC (D4). Run from the repo root:

    python -P art/town/make_friendobo_art.py [--preview FILE]

Design (user, 2026-11-03: "an old robot with a monocle and a top hat, bartender-like"). Redrawn 2026-11-04 (user: "rework
the Friendobô design, it lacks detail and diverges from Terraria quality; ensure walking legs, the NPC was missing them";
the 2026-11-03 version, whose long apron hid both legs, is archived in art/town/previous/make_friendobo_art_2026-11-03b.py,
and the first dark pass beside it):

* A tall black top hat with a lit left edge and a brass band, its brim wider than the head.
* An old iron dome of a head lit from the top-left, a brass ear bolt, a brass-rimmed monocle with a steam-white lens over
  one eye and a small aether lamp for the other (friendly colours, D3), an iron nose, a big white handlebar moustache and
  a grille for a mouth.
* A black bow tie on a white collar, a copper waistcoat (lit edges, brass buttons, a watch chain), white shirt sleeves
  rolled up and held by brass garters, silver piston forearms, iron hands, a white bar towel over the far forearm.
* A short white bar apron, tied at the waist, that stops above the knees and only covers the front, so both legs show.
* Dark trousers to the knee, brass knee joints, silver piston shins and leather boots with brass toe caps: clearly
  separate legs that stride in the walk (14 frames, the arms swinging against them, a whole-pixel bob).

It faces left like every NPC sheet; vanilla draws it (one plane). Vanilla's town NPC layout (decompiled
NPC.VanillaFindFrame for town NPCs, with Main.npcFrameCount 25, NPCID.Sets.ExtraFramesCount 9 and AttackFrameCount 4,
AnimationType = the Guide): 0 standing, 1 in the air, 2-15 walking, 16-17 the two gestures of a chat, 18 sitting,
19 talking, 20 blinking, 21-24 the throw. 40x56 frames with no gap; the feet stand on row 50 (vanilla draws NPC frames
4 px below the hitbox: decompiled Main.DrawNPCDirect).

Outputs (Content/Town/):
    Friendobo.png         40x1400  25 frames
    Friendobo_Head.png    the map and housing head (hat and face)
    Gores/Friendobo_GoreHead.png, _GoreArm.png, _GoreLeg.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, COLOR_INDEX, Xf, Poly, Ellipse, Capsule, box, Canvas, flat, dome, face, ik, level, lit  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Town/"
I, B, C, E, S, LE, A = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam", "leather", "aether"))
FW, FH = 20, 28                      # frame at 1x
FOOT_ROW = 25                        # the soles' bottom row (1x): 50-51 in game, the hitbox bottom
CX = 10.0                            # the body's centre column
HIP_Y = 18.4
THIGH, SHIN = 3.6, 3.4
UPPER, FORE = 3.0, 3.2


def despeckle(cv):
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


def P(p):
    return int(math.floor(p[0])), int(math.floor(p[1]))


def part(cv, xf, shape, ramp, shade, **kw):
    """A part with no outline of its own: at this size (a 20x28 frame) per-part outlines left the apron, the legs and the
    boots nothing but outline (2026-11-04). The figure gets one silhouette outline at the end (outline_silhouette)."""
    kw["outline"] = False
    return cv.part(xf, shape, ramp, shade, **kw)


def outline_silhouette(cv):
    """Every pixel on the figure's edge (a 4-neighbour empty) takes its own material's darkest shade (D4 rule 3:
    ramp-coloured outlines; white cloth gets iron's mid grey, its own darkest shade being a light grey); glows keep their
    colour."""
    edge = [q for q in cv.px if q not in cv.glow and any((q[0] + ox, q[1] + oy) not in cv.px for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for q in edge:
        col = cv.px[q]
        if col in COLOR_INDEX:
            ramp, _ = COLOR_INDEX[col]
            cv.px[q] = RAMP[ramp][0] if ramp != "steam" else RAMP["iron"][1]


def limb_shade(a, b, r, lo, hi, gain=1.4, step=22.5):
    """A cylinder lit with its axis snapped to `step` degrees: stable shading while a limb sways (D4 rule 17)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / ln, dx / ln
    sa = round(math.atan2(dy, dx) / math.radians(step)) * math.radians(step)
    snx, sny = -math.sin(sa), math.cos(sa)

    def shade(i):
        t = max(-1.0, min(1.0, ((i.lx - a[0]) * nx + (i.ly - a[1]) * ny) / r))
        return level(lit(t * snx, t * sny, math.sqrt(1.0 - t * t)), lo, hi, gain)
    return shade


def limb(cv, a, b, r, ramp="iron", lo=2, hi=4, outline=True, far=False):
    """A capsule limb; on the far side one flat tone a step darker (a small far limb's swinging bands flashed)."""
    if far:
        return part(cv, Xf(), Capsule(a, b, r), ramp, flat(max(1, hi - 2), bevel=False), rust=0.0)
    return part(cv, Xf(), Capsule(a, b, r), ramp, limb_shade(a, b, r, lo, hi), rust=0.0)


class Pose:
    def __init__(self, bob=0, near_foot=(-1.4, 0.0), far_foot=(1.6, 0.0), near_hand=(-4.4, 17.4), far_hand=(3.2, 17.2),
                 sit=False, mouth=False, blink=False, towel=True):
        self.bob = bob
        self.near_foot, self.far_foot = near_foot, far_foot     # (x offset from CX, lift)
        self.near_hand, self.far_hand = near_hand, far_hand     # (x offset from CX, y)
        self.sit, self.mouth, self.blink, self.towel = sit, mouth, blink, towel


def leg(cv, hip, foot_x, lift, far):
    """Dark trousers to a brass knee joint, a silver piston shin, a leather boot with a brass toe cap."""
    ankle = (foot_x, FOOT_ROW - 1.4 - lift)
    knee, ankle = ik(hip, ankle, THIGH, SHIN, -1)
    limb(cv, hip, knee, 1.5, lo=1, hi=3, far=far)                          # trousers
    limb(cv, knee, ankle, 1.1, lo=3, hi=4, far=far)                        # the piston shin
    k = P(knee)
    cv.put(k[0], k[1], B[2] if far else B[4])                             # the knee joint
    ax, ay = ankle
    part(cv, Xf(), Poly([(ax + 1.4, ay - 0.6), (ax - 1.0, ay - 0.8), (ax - 2.6, ay + 0.6), (ax - 2.6, ay + 1.4), (ax + 1.6, ay + 1.4)]),
            "leather", flat(1 if far else 2), rust=0.0)                     # the boot
    t = P((ax - 2.0, ay + 0.6))
    cv.put(t[0], t[1], B[2] if far else B[4])                             # its brass toe cap


def arm(cv, shoulder, hand, far, towel=False):
    elbow, wrist = ik(shoulder, hand, UPPER, FORE, 1)
    roll = (shoulder[0] + (elbow[0] - shoulder[0]) * 0.5, shoulder[1] + (elbow[1] - shoulder[1]) * 0.5)
    limb(cv, roll, elbow, 0.9, lo=2, hi=3, far=far)                        # a piston upper arm under the rolled sleeve
    limb(cv, shoulder, roll, 1.3, ramp="steam", lo=1, hi=2, far=far)       # the white shirt sleeve, rolled up high
    limb(cv, elbow, wrist, 0.9, lo=2, hi=4, outline=False, far=far)        # a silver piston forearm
    g = P(roll)
    cv.put(g[0], g[1], B[2] if far else B[4])                             # the brass sleeve garter
    if towel:                                                             # the bar towel over the forearm
        mx, my = (elbow[0] + wrist[0]) / 2.0, (elbow[1] + wrist[1]) / 2.0
        part(cv, Xf(), Poly([(mx - 1.2, my - 0.8), (mx + 1.4, my - 0.8), (mx + 1.0, my + 2.8), (mx - 1.0, my + 2.4)]), "steam",
                flat(1 if far else 2), rust=0.0)
    h = P(wrist)
    cv.put(h[0], h[1], I[2] if far else I[3])                             # the hand
    cv.put(h[0], h[1] + 1, I[1] if far else I[2])


def body(cv, glow, p):
    oy = p.bob + (2 if p.sit else 0)
    # the torso: a white shirt showing in the narrow V of a wide copper waistcoat
    part(cv, Xf(), box(CX - 3.4, 11.4 + oy, CX + 3.2, 18.8 + oy), "steam", face((-0.5, -0.3, 0.8), lo=1, hi=2, fixed=True), rust=0.0)
    vest = part(cv, Xf(), Poly([(CX - 3.8, 12.4 + oy), (CX - 1.2, 12.4 + oy), (CX - 0.4, 14.6 + oy), (CX + 0.4, 12.4 + oy),
                               (CX + 3.6, 12.4 + oy), (CX + 3.8, 19.6 + oy), (CX - 4.0, 19.6 + oy)]),
                   "copper", face((-0.5, -0.3, 0.8), lo=2, hi=3, bias=0.15, fixed=True), rust=0.0)
    for y in range(int(math.floor(13.4 + oy)), int(math.floor(19.2 + oy))):      # its lit front edge, its shaded back panel
        q = (int(math.floor(CX - 3.2)), y)
        if q in vest:
            cv.put(q[0], q[1], C[4])
        q = (int(math.floor(CX + 2.6)), y)
        if q in vest:
            cv.put(q[0], q[1], C[1])
    for y in (15.6, 17.6):
        cv.put(int(math.floor(CX - 0.6)), int(math.floor(y + oy)), B[4])          # brass buttons
    for (dx, dy, col) in ((1, 3, B[4]), (2, 4, B[3]), (3, 4, B[4])):
        cv.put(int(math.floor(CX - 0.6)) + dx, int(math.floor(12.6 + oy)) + dy, col)   # the watch chain
    # the head: an old iron dome lit from the top-left, an ear bolt, a jaw grille
    hc = (CX - 0.4, 8.0 + oy)
    head = part(cv, Xf(), Ellipse(hc[0], hc[1], 3.9, 3.5), "iron", dome(hc[0] - 1.4, hc[1] - 1.4, 4.4, lo=2, hi=4, gain=1.35, bias=0.35, fixed=True),
                   rust=0.0)
    ear = P((hc[0] + 2.4, hc[1] + 0.4))
    cv.put(ear[0], ear[1], B[4])
    cv.put(ear[0] + 1, ear[1], B[2])
    mx, my = int(math.floor(hc[0] - 2.4)), int(math.floor(hc[1] - 0.6))
    for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        cv.put(mx + dx, my + dy, B[5] if (dy < 0 and dx < 1) else (B[4] if dy < 1 and dx < 0 else B[2]))   # the monocle's rim
    if p.blink:
        cv.put(mx, my, I[1])
    else:
        cv.put_glow(mx, my, S[3])
        glow.put_glow(mx, my, S[3])
    cv.put(mx + 1, my + 2, B[3])                                              # its chain to the waistcoat
    cv.put(mx + 2, my + 3, B[2])
    ex = int(math.floor(hc[0] + 0.8))
    if p.blink:
        cv.put(ex, my, I[1])
    else:
        cv.put_glow(ex, my, A[3])                                             # the friendly lamp eye
        glow.put_glow(ex, my, A[3])
    cv.put(ex, my - 1, I[1])                                                  # its brow
    nose = (int(math.floor(hc[0] - 3.6)), my + 1)
    cv.put(nose[0], nose[1], I[3])
    mouth_y = int(math.floor(hc[1] + 1.8))
    for (dx, col) in ((-4, S[1]), (-3, S[3]), (-2, S[2]), (-1, S[3]), (0, S[2]), (1, S[1])):   # the white handlebar moustache
        cv.put(int(hc[0]) + dx, mouth_y, col)
    cv.put(int(hc[0]) - 5, mouth_y - 1, S[2])
    cv.put(int(hc[0]) + 2, mouth_y - 1, S[1])
    for x in range(int(hc[0]) - 3, int(hc[0]) + 1):                           # the grille mouth
        q = (x, mouth_y + 1)
        if q in head:
            cv.put(q[0], q[1], I[0] if p.mouth and x in (int(hc[0]) - 2, int(hc[0]) - 1) else (I[1] if x % 2 else I[2]))
    # the top hat: brim, tall crown (a lit left edge), a brass band
    top = hc[1] - 8.4
    part(cv, Xf(), box(hc[0] - 5.0, hc[1] - 3.6, hc[0] + 4.2, hc[1] - 2.6), "iron", flat(1), rust=0.0)
    crown = part(cv, Xf(), box(hc[0] - 3.2, top, hc[0] + 2.8, hc[1] - 3.2), "iron", face((-0.5, -0.3, 0.8), lo=1, hi=2, fixed=True), rust=0.0)
    for y in range(int(math.floor(top + 1)), int(math.floor(hc[1] - 3.4))):
        q = (int(math.floor(hc[0] - 2.4)), y)
        if q in crown:
            cv.put(q[0], q[1], I[3])                                          # the crown's lit edge
    for x in range(int(math.floor(hc[0] - 2.4)), int(math.floor(hc[0] + 2.2))):
        cv.put(x, int(math.floor(hc[1] - 4.4)), B[4] if x < hc[0] else B[3])    # the brass band
    del head
    return (CX - 3.4, 13.2 + oy), (CX + 2.2, 13.0 + oy), (CX - 1.0, HIP_Y + oy), (CX + 1.4, HIP_Y - 0.2 + oy)


def bow_tie(cv, p):
    """The black bow tie on its white collar, drawn last so the near sleeve never hides it."""
    y = int(math.floor(12.0 + p.bob + (2 if p.sit else 0)))
    x = int(math.floor(CX - 0.6))
    for (dx, dy, col) in ((-2, 0, I[1]), (-1, 0, I[0]), (0, 0, I[2]), (1, 0, I[0]), (2, 0, I[1]), (-2, 1, I[0]), (2, 1, I[0]),
                          (-1, -1, S[2]), (1, -1, S[2])):
        cv.put(x + dx, y + dy, col)


def apron(cv, p):
    """The short white bar apron: tied at the waist, over the front only, stopping above the knees (both legs show)."""
    oy = p.bob
    if p.sit:
        shape = Poly([(CX - 3.4, 20.0 + oy + 2), (CX + 1.6, 20.0 + oy + 2), (CX + 1.2, 22.2 + oy + 2), (CX - 3.8, 22.2 + oy + 2)])
    else:
        shape = Poly([(CX - 3.6, 18.6 + oy), (CX + 1.4, 18.6 + oy), (CX + 1.6, 21.4 + oy), (CX - 4.0, 21.4 + oy)])
    inner = part(cv, Xf(), shape, "steam", face((-0.5, -0.3, 0.8), lo=1, hi=3, bias=0.1, fixed=True), rust=0.0)
    if not p.sit:
        for y in range(int(math.floor(19.6 + oy)), int(math.floor(21.0 + oy))):   # a fold
            q = (int(math.floor(CX - 1.0)), y)
            if q in inner:
                cv.put(q[0], q[1], S[0])
        cv.put(int(math.floor(CX + 2.2)), int(math.floor(18.8 + oy)), S[1])        # the apron string's knot at the back


def frame(p):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    sh_near, sh_far, hip_near, hip_far = body(mid, glow, p)
    if p.sit:                                                   # sitting: thighs forward, shins down
        for (cv, hip, f) in ((far, hip_far, True), (near, hip_near, False)):
            knee = (hip[0] - 3.2, hip[1] + 0.6)
            limb(cv, hip, knee, 1.5, lo=1, hi=3, far=f)
            limb(cv, knee, (knee[0] - 0.2, FOOT_ROW - 1.4), 1.1, lo=3, hi=4, far=f)
            part(cv, Xf(), box(knee[0] - 2.4, FOOT_ROW - 1.4, knee[0] + 1.2, FOOT_ROW), "leather", flat(1 if f else 2), rust=0.0)
    else:
        leg(far, hip_far, CX + p.far_foot[0], p.far_foot[1], True)
        leg(near, hip_near, CX + p.near_foot[0], p.near_foot[1], False)
    front = Canvas()                                            # the apron: over the near leg, under the near arm
    apron(front, p)
    arm(far, sh_far, (CX + p.far_hand[0], p.far_hand[1] + p.bob), True, towel=p.towel)
    hand = Canvas()
    arm(hand, sh_near, (CX + p.near_hand[0], p.near_hand[1] + p.bob), False)
    bow_tie(hand, p)
    for q in list(far.px):                                      # the far limbs a step darker: they read behind
        if q not in far.glow:
            far.darken(*q)
    cv = Canvas()
    for layer in (far, mid, near, front, hand):
        cv.px.update(layer.px)
        cv.glow.update(layer.glow)
    despeckle(cv)
    outline_silhouette(cv)
    return cv


def walk_pose(k):
    """14 walking frames: a full stride cycle (the feet apart, then passing), the arms swinging against the legs, a
    whole-pixel bob at the passing points."""
    ph = 2.0 * math.pi * k / 14.0
    stride = 3.0
    nf = (-0.6 + stride * math.cos(ph), max(0.0, round(1.6 * math.sin(ph))))
    ff = (0.8 - stride * math.cos(ph), max(0.0, round(1.6 * math.sin(ph + math.pi))))
    bob = 1 if abs(math.sin(ph)) > 0.7 else 0
    swing = round(1.6 * math.cos(ph))                          # -2..2, each held 2+ frames
    return Pose(bob=bob, near_foot=nf, far_foot=ff, near_hand=(-4.4 + swing, 17.4), far_hand=(3.2 - swing, 17.2))


FRAMES = ([Pose(), Pose(near_foot=(-2.2, 2.0), far_foot=(2.4, 1.0), near_hand=(-3.0, 14.0), far_hand=(4.0, 13.6))]
          + [walk_pose(k) for k in range(14)]
          + [Pose(near_hand=(-4.6, 11.4)), Pose(near_hand=(-4.0, 9.4)),          # 16-17: the gestures (a raised hand)
             Pose(sit=True), Pose(mouth=True), Pose(blink=True),                # 18 sit, 19 talk, 20 blink
             Pose(near_hand=(3.0, 11.4)), Pose(near_hand=(1.0, 8.4)),           # 21-22: the arm back, up
             Pose(near_hand=(-5.0, 11.4)), Pose(near_hand=(-3.6, 15.4))])       # 23-24: the throw, the follow-through


def head_icon():
    """The head for the map and the housing menu: the hat and the face, cropped from the standing frame."""
    cv = frame(FRAMES[0])
    px = {q: c for q, c in cv.px.items() if q[1] <= 11}
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    return to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    cv = frame(FRAMES[0])
    return {"Friendobo_GoreHead": crop({q: c for q, c in cv.px.items() if q[1] <= 11}),
            "Friendobo_GoreArm": crop({q: c for q, c in cv.px.items() if 12 <= q[1] <= 18 and q[0] >= 12}),
            "Friendobo_GoreLeg": crop({q: c for q, c in cv.px.items() if q[1] >= 21})}


def sheet():
    out = Image.new("RGBA", (FW, FH * len(FRAMES)), (0, 0, 0, 0))
    for k, p in enumerate(FRAMES):
        px = frame(p).px
        for (x, y) in px:
            if not (0 <= x < FW and 0 <= y < FH):
                raise SystemExit("frame %d: pixel (%d, %d) outside its %dx%d frame" % (k, x, y, FW, FH))
        out.alpha_composite(to_image(px, 0, 0, FW, FH), (0, k * FH))
    return out


def export_all():
    export(sheet(), OUT + "Friendobo.png")
    export(head_icon(), OUT + "Friendobo_Head.png")
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    sh = sheet()
    cols = 13
    out = Image.new("RGBA", (FW * cols, FH * 2 * 2), (36, 40, 48, 255))
    for half, bg in ((0, (36, 40, 48, 255)), (1, (150, 180, 210, 255))):
        tile = Image.new("RGBA", (FW * cols, FH * 2), bg)
        for k in range(len(FRAMES)):
            tile.alpha_composite(sh.crop((0, k * FH, FW, (k + 1) * FH)), ((k % cols) * FW, (k // cols) * FH))
        out.paste(tile, (0, half * FH * 2))
    out.resize((out.width * 5, out.height * 5), Image.NEAREST).save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
