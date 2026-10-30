"""D5 proof for the Cogpunker Manual's steam dash (Content/Mechanist/SteamDashPlayer.cs, 2026-10-28), replaying the
dash tick by tick with the constants parsed out of the C# file and the player wearing the real Jaeger armor sheets.

    python -P tools/sim/steam_dash_sim.py --out docs/media/2026-10-28_mechanist-steam-dash.gif

Shows: a dash (DashSpeed px/tick for DashTicks ticks, flat, then it slows to a run) through a volley of hostile bolts,
which pass through the player during the dash and its grace ticks; the steam it costs and the refill (SteamPlayer:
1.5 s delay, then 10 every 0.5 s) on a 20-steam tank (the manual's own +20); the 4 s cooldown bar; a dash refused
while it cools down; then a dash into an enemy: the contact hit lands, knocks the player back and ends the
dash. Leaves out: lighting, tile collision (flat floor), vanilla's real afterimage draw (three faded copies here),
dust physics (simple puffs), network latency.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from update_2026_10_27_sim import consts, Gif, backdrop, TPF  # noqa: E402
import armor_preview as ap  # noqa: E402

KD = consts("Content/Mechanist/SteamDashPlayer.cs")
KS = consts("Content/Mechanist/SteamPlayer.cs")
A = "Content/MechArmy/Armor/"


def jaeger_player():
    h = ap.load_frames(A + "JaegerHelmet_Head.png", 1)[0]
    b = ap.load_frames(A + "JaegerChestplate_Body.png", 1)[0]
    leg = ap.load_frames(A + "JaegerGreaves_Legs.png", 1)[0]
    return ap.compose(h, b, leg, 0, [0] * 20)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", default="docs/media/2026-10-28_mechanist-steam-dash.gif")
    a.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    args = a.parse_args()
    W, H, G = 960, 300, 260
    gif = Gif(args.font)
    bg = backdrop(W, H, G)
    me = jaeger_player()
    me_l = me.transpose(Image.FLIP_LEFT_RIGHT)
    tank = KD["ManualSteamMax"]
    steam, since, regen_t = tank, KS["RegenDelayTicks"], 0
    x, vx, facing = 120.0, 0.0, 1
    dash, grace, cooldown, hurt = 0, 0, 0, 0
    trail, puffs, bolts, notes = [], [], [], []
    enemy_x = 760.0
    script = {128: "dash", 180: "dash", 400: "dash"}   # the second is refused (cooldown); the third runs into the enemy
    dodged = 0
    for tick in range(1, 9 * 60):
        if tick in (14, 20, 26):                        # a volley of hostile bolts from the right, arriving as it dashes
            bolts.append([W + 10, G - 24.0, True])
        want = script.get(tick)
        if want and dash == 0:
            if cooldown > 0:
                notes.append([x, "cooldown %.1f s" % (cooldown / 60), 60])
            elif steam < KD["SteamCost"]:
                notes.append([x, "click: %d steam < %d" % (steam, KD["SteamCost"]), 60])
            else:
                steam -= KD["SteamCost"]
                since, regen_t = 0, 0
                dash, grace, cooldown = KD["DashTicks"], KD["DashTicks"] + KD["ProjectileGraceTicks"], KD["CooldownTicks"]
                facing = 1
                for k in range(14):
                    puffs.append([x, G - 22, k, 0])
        # movement
        if dash > 0:
            vx = facing * KD["DashSpeed"]
        elif hurt > 0:
            vx *= 0.92
        else:
            vx *= 0.8
            if 200 < tick < 380:
                vx = 1.5                                 # walks on towards the enemy while the tank refills
        x += vx
        if dash > 0:
            trail.append(x)
            trail = trail[-4:]
            puffs.append([x - facing * 12, G - 22 + (tick % 3) * 8 - 8, -1, 0])
            dash -= 1
            if dash == 0:
                vx *= KD["EndSpeedFactor"]
        else:
            trail = trail[1:] if trail else trail
        if grace > 0:
            grace -= 1
        if cooldown > 0:
            cooldown -= 1
        if hurt > 0:
            hurt -= 1
        # contact with the enemy: the hit lands and the knockback ends the dash
        if abs(x - enemy_x) < 26 and hurt == 0:
            dash, hurt = 0, 40
            vx = -8.0
            notes.append([x, "contact hit: knocked back, dash over", 80])
        # bolts: pass through during the dash and its grace
        for b in bolts:
            if not b[2]:
                continue
            b[0] -= 7
            if abs(b[0] - x) < 10:
                if grace > 0:
                    if b[2] is True:
                        dodged += 1
                        notes = [n for n in notes if not n[1].startswith("passes through")]
                        notes.append([x, "passes through (%d)" % dodged, 40])
                    b[2] = "through"
                else:
                    b[2] = False
                    notes.append([x, "hit", 40])
            if b[0] < -20:
                b[2] = False
        # steam refill (SteamPlayer)
        if since < KS["RegenDelayTicks"]:
            since += 1
        elif steam < tank:
            regen_t += 1
            if regen_t >= KS["RegenIntervalTicks"]:
                regen_t = 0
                steam = min(tank, steam + KS["BaseRegenAmount"])
        puffs = [[px - 0.6 * (1 if k < 0 else 0) + (0 if k < 0 else (k % 7 - 3) * 0.5), py - 0.4, k, age + 1] for px, py, k, age in puffs if age < 24]
        notes = [[nx, s, t - 1] for nx, s, t in notes if t > 0]
        if tick % TPF:
            continue
        img = bg.copy()
        dd = ImageDraw.Draw(img)
        # the enemy: a dark block
        dd.rectangle([enemy_x - 14, G - 36, enemy_x + 14, G], fill=(79, 85, 98, 255), outline=(21, 22, 28, 255))
        gif.text(img, (int(enemy_x) - 22, G - 54), "enemy")
        for px, py, k, age in puffs:
            r = 3 + age // 3
            col = (238, 241, 243, 255) if age < 12 else (195, 200, 205, 255)
            dd.ellipse([px - r, py - r, px + r, py + r], outline=col, width=2)
        for k, tx in enumerate(trail[:-1]):
            ghost = me.copy()
            al = ghost.getchannel("A").point(lambda v, k=k: int(v * (0.2 + 0.15 * k)))
            ghost.putalpha(al)
            img.alpha_composite(ghost, (int(tx - ghost.width / 2), G - ghost.height + 2))
        body = me if facing > 0 else me_l
        if hurt and (tick // 3) % 2:
            body = Image.eval(body, lambda v: v)
        img.alpha_composite(body, (int(x - body.width / 2), G - body.height + 2))
        for b in bolts:
            if b[2]:
                dd.line([b[0], b[1], b[0] + 12, b[1]], fill=(236, 113, 40, 255), width=4)
        for nx, s, t in notes:
            gif.text(img, (int(nx) - 50, G - 90), s, fill=(255, 199, 90))
        # HUD: the steam gauge and the cooldown
        dd.rectangle([12, 56, 212, 70], outline=(21, 22, 28, 255), fill=(46, 50, 59, 255))
        dd.rectangle([12, 56, 12 + 200 * steam / tank, 70], fill=(195, 200, 205, 255))
        gif.text(img, (220, 54), "steam %d/%d" % (steam, tank))
        dd.rectangle([12, 78, 212, 86], outline=(21, 22, 28, 255), fill=(46, 50, 59, 255))
        dd.rectangle([12, 78, 12 + 200 * (1 - cooldown / KD["CooldownTicks"]), 86], fill=(184, 138, 51, 255))
        gif.text(img, (220, 74), "ready" if cooldown == 0 else "cooldown %.1f s" % (cooldown / 60))
        gif.text(img, (12, 8), "Steam dash (Cogpunker Manual): %d px/tick for %d ticks, %d steam, %d s cooldown; +%d max steam" % (
            KD["DashSpeed"], KD["DashTicks"], KD["SteamCost"], KD["CooldownTicks"] // 60, KD["ManualSteamMax"]))
        gif.text(img, (12, 28), "projectiles pass through for the dash + %d ticks; enemies you dash into still hit you" % KD["ProjectileGraceTicks"])
        gif.push(img)
    gif.save(args.out)
    print("bolts dodged:", dodged)


if __name__ == "__main__":
    main()
