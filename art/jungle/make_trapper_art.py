"""Source for the jungle's Trapper and its spike balls (D4), 2026-10-27. Run from the repo root:

    python -P art/jungle/make_trapper_art.py

Drawn at 1x and exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left, ramp-0 outlines, built
from rig.py parts (two-bone IK for the limbs, so every pose is rendered clean: nothing is rotated as a bitmap).

The Trapper (detailed mob, three-quarter view facing left, D4 rules 13 and 16): half goblin, half cyborg. Grey-green
goblin skin (verdigris), a long ear swept back under a leather hood, a brass lens bolted over one eye with a hostile
ember lamp in it, a leather jerkin with a bandolier, a sack of spike balls on its back (iron spikes poking out), a
riveted brass arm on the near side and a piston leg (iron thigh, brass ram) under it; the far arm and leg are its own,
a ramp step darker (far plane).

Outputs:
    Content/Jungle/NPCs/Trapper.png                 48x624  12 frames of 48x52 (24x26 art): idle x2, run x6, throw:
                                                    wind-up x2 (the ball raised behind the head), release, follow-through.
                                                    Feet on row 23: NPC frames are drawn 4 px low (decompiled
                                                    Main.DrawNPCDirect: + 4f), so they meet the hitbox bottom.
    Content/Jungle/Projectiles/TrapperSpikeBall.png 20x88   4 frames (stride 22) of 20x20 (10x10 art): an iron ball with
                                                    eight spikes, a quarter of a spike period turned each frame
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, box, Canvas, flat, face, dome, cyl, ik, line  # noqa: E402
import make_trashtr0m_art as boss  # noqa: E402
from make_trashtr0m_loot import img  # noqa: E402

I, B, C, V, E, S, LE, A = (RAMP[k] for k in ("iron", "brass", "copper", "verd", "ember", "steam", "leather", "aether"))
W, H = 24, 26
GROUND = 24                                           # first empty row under the feet


def limb(cv, a, b, c, r0, r1, ramp, depth=0, rust=0.0, lo=1, hi=None):
    """Two capsule segments a->b->c (upper and lower), cylinder-shaded."""
    hi = len(RAMP[ramp]) - 1 if hi is None else hi
    cv.part(Xf(), Capsule(a, b, r0, r0 * 0.9), ramp, cyl(a, b, r0, lo=lo, hi=hi), depth=depth, rust=rust)
    cv.part(Xf(), Capsule(b, c, r0 * 0.9, r1), ramp, cyl(b, c, r0, lo=lo, hi=hi), depth=depth, rust=rust)


def spike_ball(cv, cx, cy, r=1.6, spikes=6, turn=0.0):
    """A small spike ball (held in the hand)."""
    for k in range(spikes):
        a = math.radians(turn + k * 360.0 / spikes)
        line(cv, Xf(), (cx + math.cos(a) * (r - 0.2), cy + math.sin(a) * (r - 0.2)), (cx + math.cos(a) * (r + 1.4), cy + math.sin(a) * (r + 1.4)),
             lambda n: I[3] if n else I[1])
    cv.part(Xf(), Ellipse(cx, cy, r, r), "iron", dome(cx - 0.6, cy - 0.6, r * 1.4, lo=1, hi=4), rust=0.0)


def trapper(pose):
    """One 24x26 frame. pose: bob (body y), lean (body x), near/far foot targets, near/far hand targets, ball (hand
    holding a spike ball), blink."""
    cv = Canvas()
    bob, lean = pose.get("bob", 0), pose.get("lean", 0.0)
    hip_n, hip_f = (11.5 + lean, 15.0 + bob), (13.0 + lean, 15.0 + bob)
    sh_n, sh_f = (11.0 + lean, 9.5 + bob), (13.5 + lean, 9.5 + bob)
    # --- far plane: far arm, far leg (a ramp step darker) ---
    fh = pose["far_hand"]
    elbow, hand = ik(sh_f, (fh[0] + lean, fh[1] + bob), 3.4, 3.4, bend=-1)
    limb(cv, sh_f, elbow, hand, 1.2, 1.0, "verd", depth=1)
    cv.part(Xf(), Capsule(elbow, hand, 1.15, 1.05), "leather", flat(1, bevel=False), rust=0.0)   # leather bracer
    ff = pose["far_foot"]
    knee, foot = ik(hip_f, ff, 4.6, 4.6, bend=1)
    limb(cv, hip_f, knee, foot, 1.5, 1.2, "verd", depth=1)
    cv.part(Xf(), box(foot[0] - 2.2, foot[1] - 1.4, foot[0] + 1.2, foot[1] + 0.6), "leather", flat(1), rust=0.0)   # boot
    # --- the sack of spike balls on its back ---
    sx, sy = 16.0 + lean, 11.0 + bob
    sack = cv.part(Xf(), Poly([(sx - 3.0, sy - 3.5), (sx + 2.5, sy - 4.0), (sx + 4.0, sy + 1.0), (sx + 2.5, sy + 4.5), (sx - 3.0, sy + 4.0)]),
                   "leather", dome(sx - 1.5, sy - 2.0, 5.0, lo=1, hi=2, gain=1.2), rust=0.0)
    for (dx, dy) in ((-1.5, -4.5), (1.0, -5.0), (3.2, -3.2)):     # spikes poking out of its mouth
        x, y = int(sx + dx), int(sy + dy)
        cv.put(x, y, I[3])
        cv.put(x, y + 1, I[1])
    line(cv, Xf(), (sx - 2.5, sy - 1.0), (sx + 3.0, sy - 1.5), lambda n: LE[0], sack)   # its drawstring
    # --- torso: leather jerkin, a brass-buckled bandolier ---
    tx, ty = 12.0 + lean, 12.5 + bob
    torso = cv.part(Xf(), Poly([(tx - 3.5, ty - 4.0), (tx + 2.8, ty - 4.2), (tx + 3.2, ty + 3.4), (tx - 3.0, ty + 3.4)]), "leather",
                    face((-0.6, -0.3, 0.75), lo=1, hi=2, ramp_len=3), rust=0.0)
    line(cv, Xf(), (tx - 3.0, ty - 3.6), (tx + 2.8, ty + 2.6), lambda n: B[3] if n % 3 else B[4], torso)   # bandolier
    for x in range(int(tx - 3), int(tx + 3)):                    # belt
        cv.put(x, int(ty + 3), I[0] if x != int(tx - 1) else B[4])
    # --- head: goblin skin, a hood, a swept-back ear, a brass lens with an ember lamp ---
    hx, hy = 9.5 + lean, 5.5 + bob
    cv.part(Xf(), Poly([(hx + 2.0, hy - 0.5), (hx + 8.5, hy - 2.5), (hx + 6.0, hy + 1.5)]), "verd",
            face((-0.2, -0.8, 0.6), lo=1, hi=3, ramp_len=4), rust=0.0)                     # the long ear, swept back
    head = cv.part(Xf(), Ellipse(hx, hy, 3.6, 3.4), "verd", dome(hx - 1.5, hy - 1.5, 4.5, lo=1, hi=3), rust=0.0)
    cv.part(Xf(), Poly([(hx - 4.4, hy + 0.2), (hx - 2.0, hy - 0.2), (hx - 2.0, hy + 1.8)]), "verd", flat(2), rust=0.0)   # the hooked nose
    hood = cv.part(Xf(), Poly([(hx - 3.0, hy - 2.2), (hx - 1.0, hy - 4.6), (hx + 3.2, hy - 4.4), (hx + 4.6, hy - 1.0), (hx + 4.4, hy + 3.4),
                                (hx + 2.0, hy + 1.0), (hx - 0.5, hy - 1.8)]), "leather", dome(hx - 1.0, hy - 4.0, 6.0, lo=1, hi=2), rust=0.0)
    ex, ey = int(hx - 2), int(hy - 1)                             # the brass lens over the eye, ember lamp inside
    for (x, y, col) in ((ex - 1, ey - 1, B[0]), (ex, ey - 1, B[4]), (ex + 1, ey - 1, B[0]), (ex - 1, ey, B[3]), (ex + 1, ey, B[2]),
                        (ex - 1, ey + 1, B[0]), (ex, ey + 1, B[1]), (ex + 1, ey + 1, B[0])):
        cv.put(x, y, col)
    if pose.get("blink"):
        cv.put(ex, ey, E[1])
    else:
        cv.put_glow(ex, ey, E[3])
    mx, my = int(hx - 2), int(hy + 2)                             # the grin and a tooth
    cv.put(mx, my, V[0])
    cv.put(mx + 1, my, V[0])
    cv.put(mx + 1, my - 1 + 1, S[2] if pose.get("grin", True) else V[0])
    # --- near leg: the piston leg (iron thigh, brass ram, an iron foot) ---
    nf = pose["near_foot"]
    knee, foot = ik(hip_n, nf, 4.6, 4.6, bend=1)
    cv.part(Xf(), Capsule(hip_n, knee, 1.6, 1.4), "iron", cyl(hip_n, knee, 1.6, lo=1, hi=4), rust=0.3)
    cv.part(Xf(), Capsule(knee, foot, 1.1, 1.0), "brass", cyl(knee, foot, 1.1, lo=2, hi=5), rust=0.0)
    cv.part(Xf(), Ellipse(knee[0], knee[1], 1.3, 1.3), "iron", dome(knee[0] - 0.5, knee[1] - 0.5, 1.8, lo=2, hi=4), rust=0.0)
    cv.part(Xf(), box(foot[0] - 2.6, foot[1] - 1.2, foot[0] + 1.0, foot[1] + 0.8), "iron", face((-0.3, -0.7, 0.7), lo=1, hi=3), rust=0.2)
    # --- near arm: riveted brass, iron joints, maybe a spike ball in the claw ---
    nh = pose["near_hand"]
    elbow, hand = ik(sh_n, (nh[0] + lean, nh[1] + bob), 3.6, 3.6, bend=pose.get("near_bend", -1))
    cv.part(Xf(), Capsule(sh_n, elbow, 1.4, 1.2), "brass", cyl(sh_n, elbow, 1.4, lo=1, hi=4), rust=0.0)
    cv.part(Xf(), Capsule(elbow, hand, 1.2, 1.1), "brass", cyl(elbow, hand, 1.2, lo=1, hi=4), rust=0.0)
    for p in (sh_n, elbow):
        cv.part(Xf(), Ellipse(p[0], p[1], 1.2, 1.2), "iron", dome(p[0] - 0.5, p[1] - 0.5, 1.6, lo=2, hi=4), rust=0.0)
    cv.put(int(hand[0]), int(hand[1]), I[0])
    if pose.get("ball"):
        spike_ball(cv, hand[0], hand[1] - 1.0, turn=pose.get("ball_turn", 0.0))
    return cv


def poses():
    out = []
    # idle (breathing: the hands sway a pixel, the lamp blinks on the second frame)
    for k in range(2):
        out.append(dict(bob=k, near_foot=(10.0, 23.0), far_foot=(14.5, 23.0), near_hand=(9.0, 16.0 - k * 0.5),
                        far_hand=(15.5, 15.5), blink=k == 1))
    # run (6 frames, legs opposite, arms swinging against them, the body bobbing on the passing frames)
    for k in range(6):
        p = k / 6.0 * math.tau
        sw = math.sin(p)
        lift_n = max(0.0, math.cos(p)) * 2.4
        lift_f = max(0.0, -math.cos(p)) * 2.4
        out.append(dict(bob=0 if k % 3 == 0 else -1 + (k % 3 == 2), lean=-0.5,
                        near_foot=(11.0 - sw * 4.2, 23.0 - lift_n), far_foot=(13.0 + sw * 4.2, 23.0 - lift_f),
                        near_hand=(10.0 + sw * 3.6, 15.0), far_hand=(14.0 - sw * 3.6, 14.8)))
    # throw: wind-up (the ball raised behind the head), wind-up further (leaning back), release (arm out front), follow
    out.append(dict(near_foot=(8.5, 23.0), far_foot=(15.0, 23.0), near_hand=(15.5, 5.5), far_hand=(8.5, 12.5), ball=True,
                    lean=0.5, near_bend=1))
    out.append(dict(near_foot=(8.5, 23.0), far_foot=(15.5, 23.0), near_hand=(17.5, 7.0), far_hand=(8.0, 12.0), ball=True,
                    lean=1.0, near_bend=1, ball_turn=30.0))
    out.append(dict(near_foot=(8.0, 23.0), far_foot=(15.0, 23.0), near_hand=(4.0, 8.5), far_hand=(15.5, 14.0), lean=-1.0,
                    grin=True))
    out.append(dict(near_foot=(8.5, 23.0), far_foot=(14.5, 23.0), near_hand=(5.5, 13.0), far_hand=(15.0, 15.0), lean=-0.5))
    return out


def trapper_frames():
    return [img(trapper(p), W, H) for p in poses()]


def spike_ball_frames():
    """10x10, 4 frames: an iron ball (r 2.6) with eight spikes, turned 11.25 degrees a frame (a quarter of the 45-degree
    spike period), lit from the top-left."""
    out = []
    for f in range(4):
        cv = Canvas()
        c = 4.5
        for k in range(8):
            a = math.radians(f * 11.25 + k * 45.0)
            line(cv, Xf(), (c + math.cos(a) * 2.2, c + math.sin(a) * 2.2), (c + math.cos(a) * 4.6, c + math.sin(a) * 4.6),
                 lambda n, k=k: (I[4] if k in (4, 5) else I[3]) if n >= 1 else I[1])
        cv.part(Xf(), Ellipse(c + 0.5, c + 0.5, 2.7, 2.7), "iron", dome(c - 0.6, c - 0.6, 3.6, lo=1, hi=4, gain=1.3), rust=0.0)
        out.append(img(cv, 10, 10))
    return out


def export_all():
    boss.export(boss.vertical(trapper_frames(), pad=0), "Content/Jungle/NPCs/Trapper.png")
    boss.export(boss.vertical(spike_ball_frames(), pad=1), "Content/Jungle/Projectiles/TrapperSpikeBall.png")


if __name__ == "__main__":
    export_all()
