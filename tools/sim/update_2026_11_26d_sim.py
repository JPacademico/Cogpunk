"""D5 proofs for the 0.2.3 patch of 2026-11-26 (directional melee). Run from the repo root:

    python -P tools/sim/update_2026_11_26d_sim.py [--out docs/media] [--only swings]

Offline replays with the real sprites and the C# constants, 60 ticks a second (Pillow only; the helpers are
update_2026_11_26c_sim.py's). Leaves out: lighting, sound, netcode, vanilla's own sprites (the player is the Brass armour
on the sims' mannequin, its arm not turned), and the hand's exact place (vanilla's GetFrontHandPosition is approximated:
the shoulder 4 px back and 2 px up, the hand 10 px out along the arm).

    swings     the cursor circling the player while four Cogpunk melee weapons swing on auto-reuse: the Cogspring Sword
               (vanilla's arc, its phantom slash), the Macuahuitl and the Jade Phasesaber (vanilla's arc), and the Firesaw
               (its own alternating curve). Each swing turns the player to the cursor's side as it starts and turns its arc
               by the aim (DirectionalSwing: the cursor's angle in the facing frame, held to +-MaxAim, eased by Follow).
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import update_2026_11_26c_sim as C  # noqa: E402

ROOT = C.ROOT
W, PH = 440, 170


def swings_gif(path):
    d = C.consts("Core/Combat/DirectionalSwing.cs")
    max_aim, follow = d["MaxAim"], d["Follow"]
    v_start, v_end = -1.75 - 0.3 - math.pi / 4, 1.75 - 0.3 - math.pi / 4      # DirectionalSwing.VanillaStart / VanillaEnd
    cog = C.consts("Content/Mechanist/Weapons/CogspringSword.cs")
    mac = C.consts("Content/Junkyard/Weapons/Macuahuitl.cs")
    sab = C.consts("Content/Gems/Items/JadePhasesaber.cs")
    saw = C.consts("Content/Mechanist/Weapons/Firesaw.cs")
    trail = C.load("Content/Mechanist/Weapons/CogspringTrail.png")
    saw_sheet = C.load("Content/Mechanist/Weapons/FiresawSwing.png")
    weapons = [
        dict(name="COGSPRING SWORD", sprite=C.load("Content/Mechanist/Weapons/CogspringSword.png"),
             glow=C.load("Content/Mechanist/Weapons/CogspringSword_Glow.png"), use=int(cog["UseTime"]), grip=cog["CornerToGrip"], kind="vanilla", trail=True),
        dict(name="MACUAHUITL", sprite=C.load("Content/Junkyard/Weapons/Macuahuitl.png"), glow=None, use=int(mac["UseTime"]),
             grip=mac["GripFromCorner"], kind="vanilla", trail=False),
        dict(name="JADE PHASESABER", sprite=C.load("Content/Gems/Items/JadePhasesaber.png"), glow=None, use=int(sab["UseTime"]),
             grip=sab["GripFromCorner"], kind="vanilla", trail=False),
        dict(name="FIRESAW", sprite=None, glow=None, use=int(saw["UseTime"]), grip=0.0, kind="firesaw", trail=False),
    ]

    def ease_in_out(t):
        return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

    def ease_out(t):
        return 1 - (1 - t) ** 3

    def phase(t, a, b):
        return max(0.0, min(1.0, (t - a) / (b - a)))

    def firesaw_angle(done, up):                       # Firesaw.SwingAngle(done, up)
        frm, to = (saw["Low"], saw["High"]) if up else (saw["High"], saw["Low"])
        sign = -1.0 if up else 1.0
        start, over = frm - sign * saw["PullBack"], to + sign * saw["Overshoot"]
        if done < saw["WindEnd"]:
            return frm + (start - frm) * ease_out(phase(done, 0, saw["WindEnd"]))
        if done < saw["SlashEnd"]:
            return start + (to - start) * ease_in_out(phase(done, saw["WindEnd"], saw["SlashEnd"]))
        if done < saw["OverEnd"]:
            return to + (over - to) * ease_out(phase(done, saw["SlashEnd"], saw["OverEnd"]))
        return over + (to - over) * ease_in_out(phase(done, saw["OverEnd"], saw["SettleEnd"]))

    ticks = 240
    px, feet = 220, 140
    center = (px, feet - 21)

    def cursor(t):
        a = -math.pi * 0.15 + t / ticks * math.tau
        return center[0] + math.cos(a) * 150, center[1] + math.sin(a) * 70

    states = [dict(direction=1, aim=0.0, anim=0, ring=[], up=True) for _ in weapons]
    frames = []
    for t in range(ticks):
        mx, my = cursor(t)
        img = Image.new("RGBA", (W, PH * len(weapons) + 4 * (len(weapons) - 1)), (0, 0, 0, 255))
        for k, (wpn, st) in enumerate(zip(weapons, states)):
            use = wpn["use"]
            start = st["anim"] <= 0
            if start:
                st["anim"] = use
                st["ring"] = []
                st["up"] = not st["up"]                   # the Firesaw's alternating slashes (FiresawPlayer.BeginSwing)
            dx, dy = mx - center[0], my - center[1]
            if start:
                st["direction"] = -1 if dx < 0 else 1       # DirectionalSwingPlayer.Tick: ChangeDir as the swing starts
            want = max(-max_aim, min(max_aim, math.atan2(dy, abs(dx))))
            st["aim"] = want if start else st["aim"] + (want - st["aim"]) * follow
            done = 1 - st["anim"] / use
            direction = st["direction"]
            if wpn["kind"] == "vanilla":
                facing = v_start + (v_end - v_start) * done + st["aim"]
            else:
                facing = firesaw_angle(done, st["up"]) + st["aim"]
            world = facing if direction == 1 else math.pi - facing
            blade = (math.cos(world), math.sin(world))
            hand = (center[0] - 4 * direction + blade[0] * 10, center[1] - 2 + blade[1] * 10)
            rot = facing + math.pi / 4 if direction == 1 else -(facing + math.pi / 4)
            st["ring"].append(rot)
            panel = C.backdrop(W, PH, feet)
            C.put_player(panel, px, feet, 0, direction > 0)
            if wpn["kind"] == "vanilla":
                spr = wpn["sprite"]
                loc = (hand[0] - blade[0] * wpn["grip"], hand[1] - blade[1] * wpn["grip"])
                if wpn["trail"]:                          # CogspringTrailLayer (as in update_2026_11_26c_sim)
                    back = min(int(cog["TrailTicks"]), len(st["ring"]) - 1)
                    if back >= 1:
                        def bd(r):
                            base = -3 * math.pi / 4 if direction == -1 else -math.pi / 4
                            return math.cos(base + r), math.sin(base + r)
                        now, then = bd(rot), bd(st["ring"][-1 - back])
                        sweep = math.atan2(then[0] * now[1] - then[1] * now[0], then[0] * now[0] + then[1] * now[1])
                        span = abs(sweep)
                        if span >= cog["TrailMin"]:
                            tw, th, gap = int(cog["TrailW"]), int(cog["TrailH"]), int(cog["Gap"])
                            fi = max(1, min(int(cog["TrailFrames"]), int(span / math.radians(12) + 0.5))) - 1
                            fr = trail.crop((0, fi * (th + gap), tw, fi * (th + gap) + th))
                            cw = sweep > 0
                            o = (int(cog["TrailPivotX"]), int(cog["TrailPivotY"]) if cw else th - int(cog["TrailPivotY"]))
                            fr = fr if cw else C.flip_v(fr)
                            C.put_rotated(panel, fr, math.atan2(now[1], now[0]), o, loc,
                                          cog["TrailOpacity"] * max(0.35, min(1.0, span / cog["TrailFull"])))
                im = spr if direction > 0 else C.mirror(spr)
                o = (0, spr.height) if direction > 0 else (spr.width, spr.height)
                C.put_rotated(panel, im, rot, o, loc)
                if wpn["glow"] is not None:
                    gl = wpn["glow"] if direction > 0 else C.mirror(wpn["glow"])
                    C.put_rotated(panel, gl, rot, o, loc, C.consts("Content/Mechanist/Weapons/CogspringSword.cs")["GlowStrength"])
            else:
                size, gx, gy = int(saw["Size"]), int(saw["GripX"]), int(saw["GripY"])
                fr = saw_sheet.crop((0, 0, size, size))
                im = fr if direction > 0 else C.mirror(fr)
                o = (gx, gy) if direction > 0 else (size - gx, gy)
                C.put_rotated(panel, im, rot, o, hand)
            C.cross(panel, mx, my)
            C.label(panel, "%s: turned to the cursor (+), facing %s" % (wpn["name"], "right" if direction > 0 else "left"), 4, 4)
            img.paste(panel, (0, k * (PH + 4)))
            st["anim"] -= 1
        if t % 2 == 0:
            frames.append(img)
    C.save_gif(frames, path, ms=33, scale=1)


SCENES = {"swings": ("weapon-directional-swings.gif", swings_gif)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    a = ap.parse_args()
    os.chdir(ROOT)
    os.makedirs(a.out, exist_ok=True)
    for n in (a.only.split(",") if a.only else list(SCENES)):
        fname, fn = SCENES[n]
        fn(os.path.join(a.out, "2026-11-26_" + fname))


if __name__ == "__main__":
    main()
