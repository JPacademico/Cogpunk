"""D5 proofs for the 2026-11-23 sprite redesigns (the sprite-quality study). Run from the repo root:

    python -P tools/sim/update_2026_11_23_sim.py [--out docs/media] [--only fungimancer,...]

    fungimancer   the Fungimancer, 2x2 version (v4) in three planes: every sequence at its in-game timing (BodyFrame), the
                  planes shifting as it drifts across the screen (the parallax); over the glowing mushroom biome's blue.
    fungimancer-ba  v3 (the reference at its own grid) and v4 (the 2x2 version) side by side at their in-game size, x2.
    fox        the jade fennec up close, every sequence at its in-game timing (JadeFoxPet.cs): trotting at its walk (the
               ground sliding under it), idle (IdleSequence), the spirit float, a ledge jump (rising, top, falling), settling,
               sleeping and waking. Its frames are the model's own parts moved (v6), no legs or motes.
    jadey, jadey-statue, jadey-turn  the redrawn Jadey: every sequence, her statue phase, her turn (jadey_loot_sim's and
               update_2026_11_18_sim's replays, which read her current sheets).
"""
import argparse
import math
import os
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "promo"))
import jadey_loot_sim as L  # noqa: E402
from update_2026_11_18_sim import save  # noqa: E402
import stage as S  # noqa: E402
from update_2026_11_18_sim import turn_gif as jadey_turn_gif  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FB = "Content/Bosses/Fungimancer/"


def rig(path):
    text = open(path, encoding="utf-8").read()
    return {k: int(v) for k, v in re.findall(r"(\w+) = (-?\d+)", text)}


def cell(sheets, r, k):
    w, h, cols = r["CellWidth"], r["CellHeight"], r["Columns"]
    x, y = (k % cols) * (w + 2), (k // cols) * (h + 2)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for s in sheets:
        out.alpha_composite(s.crop((x, y, x + w, y + h)))
    return out


def fungimancer_gif(path):
    """v4 (2026-11-23, the 2x2 version in three planes): every sequence at its in-game timing (Fungimancer.BodyFrame), the
    planes drawn as DepthLayers draws them (far shifted against the camera and 12% darker, near with it, up to MaxParallax,
    on the 2 px grid) while the boss drifts across the screen, so the parallax shows; the glow sheet on top."""
    r = rig(FB + "FungimancerRigData.cs")
    src = open(os.path.join(ROOT, FB + "Fungimancer.cs"), encoding="utf-8").read()
    max_par = float(re.search(r"MaxParallax = ([\d.]+)f", src).group(1))
    cycle = [int(v) for v in re.search(r"IdleCycle = \{([^}]*)\}", src).group(1).split(",")]
    load = lambda k: Image.open(FB + "Fungimancer%s.png" % k).convert("RGBA")
    far, mid, near, glow = load("_Far"), load(""), load("_Near"), load("_Glow")
    dark = Image.new("RGBA", far.size)
    dark.putdata([(int(a * 0.88), int(b * 0.88), int(c * 0.88), d) for (a, b, c, d) in far.get_flattened_data()])
    idle = [("IDLE", r["Idle"] + cycle[i % len(cycle)], 10) for i in range(12)] + [("IDLE (a blink)", r["Idle"] + 5, 8)]
    plan = ([("INTRO: eyes shut", r["Intro"], 90), ("INTRO", r["Intro"] + 1, 60)] + idle
            + [("CAST", r["Cast"] + k, t) for k, t in enumerate((6, 8, 10, 6, 8, 10))] + idle[:6]
            + [("CAST? FIZZLE (dumb)", r["Fizzle"] + k, t) for k, t in enumerate((20, 40))] + idle[:6]
            + [("CROAK", r["Croak"] + k, t) for k, t in enumerate((10, 10, 10, 16, 24))] + idle[:6]
            + [("TONGUE", r["Tongue"] + k, t) for k, t in enumerate((36, 36, 8))] + idle[:6]
            + [("DEATH", r["Death"] + k, 43) for k in range(4)])
    W, H = 420, 250

    def snap(v):
        return round(v * 0.5) * 2

    frames, tick = [], 0
    for (label, k, ticks) in plan:
        for t in range(0, ticks, 3):
            img = Image.new("RGBA", (W, H), (14, 20, 44, 255))
            d = ImageDraw.Draw(img)
            for i, col in enumerate(((18, 26, 58), (22, 32, 70), (26, 40, 84))):
                d.rectangle([0, H - 50 + i * 16, W, H], fill=col + (255,))
            ax = W // 2 + int(150 * math.sin((tick + t) / 160.0))           # the drift across the screen
            ay = H - 34 + int(round(3 * math.sin((tick + t) / 40.0)))      # its float bob
            dx = max(-1.5, min(1.5, (ax - W / 2) / (W / 2)))
            for sheet, depth in ((dark, -1), (mid, 0), (near, 1), (glow, 0)):
                shift = snap(max(-1.5 * max_par, min(1.5 * max_par, dx * max_par * depth)))
                img.alpha_composite(cell([sheet], r, k), (ax - r["OriginX"] + shift, ay - r["OriginY"]))
            L.label(img, "FUNGIMANCER 2x2 (v4): %s   frame %d" % (label, k), 6, 4)
            L.label(img, "parallax: far %+d px, near %+d px" % (snap(-dx * max_par), snap(dx * max_par)), 6, 18)
            frames.append(img)
        tick += ticks
    save(frames, path, scale=2, ms=50)


def fungimancer_ba(path):
    """v3 (the reference at its own grid, 125 x 103 art px) and v4 (the 2x2 version, 65 x 54), both at their in-game size
    (2x), with their detail numbers."""
    fdir = os.path.join(ROOT, "art", "bosses", "fungimancer")
    sys.path.insert(0, fdir)
    sys.path.insert(0, os.path.join(ROOT, "art", "bosses", "trashtr0m"))
    sys.path.insert(0, os.path.join(ROOT, "art", "oldbrasstown"))
    code = open(os.path.join(fdir, "previous", "make_fungimancer_art_2026-11-23b.py"), encoding="utf-8").read()
    code = code.replace("HERE = os.path.dirname(os.path.abspath(__file__))", "HERE = %r" % fdir)   # it lives in previous/
    v3 = type(sys)("fungi_v3")
    exec(compile(code, "fungi_v3", "exec"), v3.__dict__)
    px, gl = v3.frame(v3.Pose())
    a = Image.new("RGBA", (v3.W, v3.H), (0, 0, 0, 0))
    for (x, y), c in list(px.items()) + list(gl.items()):
        if 0 <= x < v3.W and 0 <= y < v3.H:
            a.putpixel((x, y), tuple(c) + (255,))
    a = a.resize((a.width * 2, a.height * 2), Image.NEAREST)
    r = rig(FB + "FungimancerRigData.cs")
    b = cell([Image.open(FB + "Fungimancer%s.png" % k).convert("RGBA") for k in ("_Far", "", "_Near", "_Glow")], r, r["Idle"])
    panels = (("v3: 125 x 103 art px", a), ("v4 (2x2): 65 x 54 art px", b))
    Wd = sum(p.width for _, p in panels) + 20 * (len(panels) + 1)
    Hd = max(p.height for _, p in panels) + 40
    out = Image.new("RGBA", (Wd, Hd), (14, 20, 44, 255))
    x = 20
    for label, p in panels:
        out.alpha_composite(p, (x, Hd - 10 - p.height))
        L.label(out, label, x, 6)
        x += p.width + 20
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.convert("RGB").save(path)
    print("wrote", path)


# ================================================================================================
# The jade fennec's animations (v6: its own parts moved)
# ================================================================================================
def fox_gif(path):
    src = open(os.path.join(ROOT, "Content/Coghaven/Pets/JadeFoxPet.cs"), encoding="utf-8").read()
    k = S.consts("Content/Coghaven/Pets/JadeFoxPet.cs")
    seq = [int(v) for v in re.search(r"IdleSequence = \{([^}]*)\}", src).group(1).split(",")]
    sheet = S.load("Content/Coghaven/Pets/JadeFoxPet.png")
    glow = S.load("Content/Coghaven/Pets/JadeFoxPet_Glow.png")
    n = int(k["FrameCount"])
    fh = sheet.height // n
    Z = 3
    walk, jump, grav = 4.5, 7.5, 0.4                       # WalkSpeed, JumpSpeed, Gravity (JadeFoxPet.cs, private)

    def cell(f):
        c = sheet.crop((0, f * fh, sheet.width, f * fh + fh))
        c.alpha_composite(glow.crop((0, f * fh, sheet.width, f * fh + fh)))
        return c.resize((c.width * Z, c.height * Z), Image.NEAREST)

    pw, ph = sheet.width * Z + 40, fh * Z + 44
    jh = ph + 150                                          # the jump panel: room for the arc
    W, H = pw * 3 + 20, ph + jh + 15

    def trot(t):
        frame, d = int(k["FrameTrot"]), 0.0
        for _ in range(t):
            d += walk
            if d >= k["TrotAnimDistance"]:
                d = 0.0
                frame = int(k["FrameTrot"]) + (frame - int(k["FrameTrot"]) + 1) % int(k["TrotFrames"])
        return frame

    def sleep_wake(t):                                     # settle, sleep 150 ticks, wake, idle
        t %= 240
        st, sl, wk = int(k["SettleTicksPerFrame"]), int(k["SleepTicksPerFrame"]), int(k["WakeTicksPerFrame"])
        if t < st * 2:
            return int(k["FrameSettle"]) + t // st, "SETTLE"
        if t < 174:
            return int(k["FrameSleep"]) + (t - st * 2) // sl % 2, "SLEEP"
        if t < 174 + wk * 3:
            return int(k["FrameWake"]) + min(2, (t - 174) // wk), "WAKE"
        return int(k["FrameIdle"]), "IDLE"

    def jump_at(t):                                        # a ledge jump every 90 ticks, trotting in between
        t %= 90
        vy, y = -jump, 0.0
        for _ in range(t):
            y += vy
            vy += grav
            if y >= 0:
                return 0.0, None
        if abs(vy) <= 0.5:
            return y, int(k["FrameJump"]) + 1
        return y, int(k["FrameJump"]) + (0 if vy < -1.8 else 1 if vy < 1.8 else 2)

    frames = []
    for t in range(0, 240, 3):                             # 3 ticks a GIF frame (50 ms), 4 s
        img = Image.new("RGBA", (W, H), (18, 18, 24, 255))
        panels = []
        f = trot(t)
        panels.append(("TROT at its walk (frame %d)" % f, f, 0, (t * walk) % 16))
        f = int(k["FrameIdle"]) + seq[(t // int(k["IdleTicksPerFrame"])) % len(seq)]
        panels.append(("IDLE (frame %d)" % f, f, 0, None))
        f = int(k["FrameFloat"]) + (t // int(k["FloatTicksPerFrame"])) % int(k["FloatFrames"])
        panels.append(("SPIRIT FLOAT (frame %d)" % f, f, -12, None))
        f, name = sleep_wake(t)
        panels.append(("%s (frame %d)" % (name, f), f, 0, None))
        for i, (name, f, dy, scroll) in enumerate(panels):
            panel = L.backdrop(pw, ph, ph - 8)
            if scroll is not None:                         # the ground slides under the trotting fox
                d = ImageDraw.Draw(panel)
                for x in range(-16, pw + 16, 16):
                    xx = int(x - scroll * Z / 2) % (pw + 16) - 8
                    d.rectangle([xx, ph - 8, xx + 1, ph - 7], fill=(90, 160, 130, 255))
            panel.alpha_composite(cell(f), (20, ph - 8 - fh * Z + int(k["FootPadding"]) * Z + dy))
            L.label(panel, name, 6, 4)
            img.alpha_composite(panel, (5 + (i % 3) * (pw + 5), 5 + (i // 3) * (ph + 5)))
        y, jf = jump_at(t)
        jf = jf if jf is not None else trot(t)
        panel = L.backdrop(pw * 2 + 5, jh, jh - 8)
        panel.alpha_composite(cell(jf), (pw - sheet.width * Z // 2, jh - 8 - fh * Z + int(k["FootPadding"]) * Z
                                         + int(round(y * Z / 2))))
        L.label(panel, "LEDGE JUMP (frame %d): rising, top, falling" % jf if jf >= k["FrameJump"]
                else "LEDGE JUMP: landed, trotting (frame %d)" % jf, 6, 4)
        img.alpha_composite(panel, (5 + pw + 5, 5 + ph + 5))
        frames.append(img)
    save(frames, path, scale=1, ms=50)


# ================================================================================================
# The Dragonete Miudo's wing beat (the 2026-11-19 request: "take example from default terraria demon enemy wings")
# ================================================================================================
def dragonete_gif(path):
    """Its fly cycle at FlapTicks (DragoneteMiudo.cs): ten eased in-betweens a beat, the far, middle and near planes and the
    glow composited, x3, over the Underworld's dark red."""
    base = "Content/Underworld/NPCs/DragoneteMiudo"
    r = rig(base + "RigData.cs")
    k = S.consts("Content/Underworld/NPCs/DragoneteMiudo.cs")
    tick = int(k["FlapTicks"])
    layers = [Image.open(base + s + ".png").convert("RGBA") for s in ("_Far", "", "_Near", "_Glow") if os.path.exists(base + s + ".png")]
    w, h = r["CellWidth"], r["CellHeight"]

    def frame(i):
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for lay in layers:
            out.alpha_composite(lay.crop((0, i * (h + 2), w, i * (h + 2) + h)))
        return out.resize((w * 3, h * 3), Image.NEAREST)

    n = r["FlyFrames"]
    W, H = w * 3 + 40, h * 3 + 40
    frames = []
    for t in range(0, tick * n * 4, tick):
        img = Image.new("RGBA", (W, H), (34, 12, 14, 255))
        img.alpha_composite(frame(r["Fly"] + (t // tick) % n), (20, 30))
        L.label(img, "DRAGONETE MIUDO: wing beat, %d frames of %d ticks (frame %d)" % (n, tick, (t // tick) % n), 6, 6)
        frames.append(img)
    save(frames, path, scale=1, ms=tick * 1000 // 60)


# ================================================================================================
# The 2026-11-19 batch's item sprites
# ================================================================================================
def items_png(path):
    """The batch's sprites as the game draws them (2x), then x3, over dark and light: Bandit's Dream, the Cogspring Sword,
    the Smoker Book, the Bundle of Wands (redrawn 2026-11-23 on the user's layout), the Rainbow Mushroom, the Calcified bone
    and the Slimed! icon."""
    items = (("Bandit's Dream", "Content/Research/Weapons/BanditsDream.png"),
             ("Cogspring Sword", "Content/Mechanist/Weapons/CogspringSword.png"),
             ("Smoker Book", "Content/Mechanist/Weapons/SmokerBook.png"),
             ("Bundle of Wands (new)", "Content/Research/Weapons/BundleOfWands.png"),
             ("Rainbow Mushroom", "Content/Bosses/Fungimancer/Items/RainbowMushroom.png"),
             ("Calcified bone", "Content/Research/CalcifiedBone.png"),
             ("Slimed!", "Content/Research/ResearchSlimed.png"))
    Z = 3
    ims = []
    for name, rel in items:
        im = S.load(rel)
        if name == "Calcified bone":
            im = im.crop((0, 0, im.width, im.width))          # its first frame
        ims.append((name, im.resize((im.width * Z, im.height * Z), Image.NEAREST)))
    cw = max(im.width for _, im in ims) + 30
    ch = max(im.height for _, im in ims) + 40
    out = Image.new("RGBA", (cw * len(ims), ch * 2), (0, 0, 0, 255))
    for row, bg in enumerate(((24, 24, 30), (196, 204, 214))):
        for i, (name, im) in enumerate(ims):
            cell = Image.new("RGBA", (cw, ch), bg + (255,))
            cell.alpha_composite(im, ((cw - im.width) // 2, 26 + (ch - 26 - im.height) // 2))
            if row == 0:
                L.label(cell, name, 4, 4)
            out.alpha_composite(cell, (i * cw, row * ch))
    out.convert("RGB").save(path)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/media")
    ap.add_argument("--only")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    jobs = (("fungimancer", fungimancer_gif, "2026-11-23_boss-fungimancer-redesign.gif"),
            ("fungimancer-ba", fungimancer_ba, "2026-11-23_boss-fungimancer-2x2.png"),
            ("fox", fox_gif, "2026-11-23_pet-jade-fox-animation.gif"),
            ("dragonete", dragonete_gif, "2026-11-23_mob-dragonete-wings.gif"),
            ("items", items_png, "2026-11-23_items-2026-11-19-batch.png"),
            ("jadey", L.jadey_frames_gif, "2026-11-23_boss-jadey-redesign.gif"),
            ("jadey-statue", L.jadey_statue_gif, "2026-11-23_boss-jadey-statue.gif"),
            ("jadey-turn", jadey_turn_gif, "2026-11-23_boss-jadey-turn.gif"))
    for name, fn, file in jobs:
        if only is None or name in only:
            fn(os.path.join(args.out, file))


if __name__ == "__main__":
    main()
