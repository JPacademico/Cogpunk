"""D5 proofs for the 0.2.2 patch of 2026-11-26 (the third request that day). Run from the repo root:

    python -P tools/sim/update_2026_11_26c_sim.py [--out docs/media] [--only glaives,cogspring,wave,refractor,overheat]

Offline replays with the real sprites and the C# constants (read from the .cs files), 60 ticks a second. Pillow only (no
numpy: this one runs where the promo stage's helpers can't). Leaves out: lighting, sound, netcode, vanilla's own sprites
(the player is the Brass armour on the sims' mannequin, tools/sim/armor_preview.py), the composite arm's exact hand
placement (the hand is put on the art's hub), and for the Cogspring Sword vanilla's exact hand positions per third of the
swing (approximated; the angles are vanilla's: (itemAnimation / max - 0.5) x -direction x 3.5 - direction x 0.3).

    glaives    the Jade Cursed Glaives with the cursor circling the player: before (0.2.1: the aim taken once, as each slash
               started; the body facing the way it walked) and after (0.2.2: the slash turns to the cursor every tick,
               AimFollow, and the body faces it).
    cogspring  the Cogspring Sword's basic attack: vanilla's swing (use time 30) drawn as the game draws it, its lights over
               it and the green phantom slash under it (CogspringTrailLayer's frame choice, opacity, pivot and flip), facing
               right then left.
    wave       Trash-Tr0m's slam wave over bumps of 4, 6 and 8 tiles and a 9-tile drop: before (climb 3, drop 6, 1008 px)
               and after (climb 8, drop 10, the nearest surface, 1920 px), the camera following each wave.
    refractor  the Jade Refractor's wind-up: 60 ticks of motes drawn into the lens, its star growing and quickening, the
               line flickering in the last 12, then the flash and the laser; let go and held again.
    overheat   an overheated player switching direction every 10 ticks: before (vanilla's run brakes against the old way:
               the speed stays near 0, the player nearly still) and after (a new direction turns the speed round).
"""
import argparse
import functools
import math
import os
import re
import sys

from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import armor_preview as AP  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
W, H = 440, 220
FLOOR = 180


# ================================================================================================
# Helpers (Pillow only)
# ================================================================================================
@functools.lru_cache(maxsize=None)
def load(rel):
    return Image.open(os.path.join(ROOT, rel)).convert("RGBA")


def consts(*rels):
    """`const int/float NAME = value;` from C# files (the sims' reader, as stage.consts)."""
    out = {}
    for rel in rels:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for m in re.finditer(r"const (?:int|float|double) ([^;]+);", src):
            for part in m.group(1).split(","):
                if "=" in part:
                    k, v = (x.strip() for x in part.split("=", 1))
                    v = re.sub(r"//.*", "", v)
                    v = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
                    v = re.sub(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", r"\1", v)
                    v = v.replace("(int)", "int")
                    try:
                        out[k] = eval(v, {"int": int, "MathHelper": None}, dict(out))
                    except Exception:
                        pass
    return out


def arrays(rel):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"static readonly (?:int|short|sbyte|byte)\[\] (\w+) = \{([^}]*)\};", src):
        out[m.group(1)] = [int(v) for v in m.group(2).replace("\n", " ").split(",") if v.strip()]
    return out


def blit(dst, src, x, y):
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if sx0 or sy0 or sx1 < src.width or sy1 < src.height:
        src = src.crop((sx0, sy0, sx1, sy1))
    dst.alpha_composite(src, (x + sx0, y + sy0))


def blit_add(dst, src, x, y, strength=1.0):
    """The game's additive draw (alpha-0 colour under premultiplied blending): dst.rgb += src.rgb x src.a x strength."""
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    s = src.crop((sx0, sy0, sx1, sy1))
    box = (x + sx0, y + sy0, x + sx1, y + sy1)
    mask = s.getchannel("A").point(lambda v: int(v * max(0.0, min(1.0, strength))))
    light = Image.composite(s.convert("RGB"), Image.new("RGB", s.size, (0, 0, 0)), mask)
    under = dst.crop(box).convert("RGB")
    dst.paste(ImageChops.add(under, light).convert("RGBA"), box)


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def flip_v(img):
    return img.transpose(Image.FLIP_TOP_BOTTOM)


def rotated(sprite, angle, pivot):
    """The sprite turned by `angle` radians (clockwise on screen) about `pivot`, nearest-neighbour (the game's point
    sampling): (image, pivot in it)."""
    w, h = sprite.size
    r = int(math.ceil(math.hypot(max(pivot[0], w - pivot[0]), max(pivot[1], h - pivot[1])))) + 2
    pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    pad.alpha_composite(sprite, (int(round(r - pivot[0])), int(round(r - pivot[1]))))
    return pad.rotate(-math.degrees(angle), resample=Image.NEAREST, center=(r, r)), (r, r)


def put_rotated(dst, sprite, angle, pivot, at, add=None):
    img, pv = rotated(sprite, angle, pivot)
    if add is None:
        blit(dst, img, int(at[0]) - pv[0], int(at[1]) - pv[1])
    else:
        blit_add(dst, img, int(at[0]) - pv[0], int(at[1]) - pv[1], add)


def label(img, s, x, y):
    d = ImageDraw.Draw(img)
    box = d.textbbox((x, y), s)
    d.rectangle([box[0] - 2, box[1] - 1, box[2] + 2, box[3] + 1], fill=(14, 14, 18, 255))
    d.text((x, y), s, fill=(238, 241, 243, 255))


def save_gif(frames, path, ms=50, scale=2):
    big = [f.convert("RGB").resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    sample = Image.new("RGB", (big[0].width, big[0].height * 4))
    for i, k in enumerate(range(0, len(big), max(1, len(big) // 4))):
        if i < 4:
            sample.paste(big[k], (0, i * big[0].height))
    pal = sample.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    out = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in big]
    out[0].save(path, save_all=True, append_images=out[1:], duration=ms, loop=0, optimize=False, disposal=1)
    print("wrote", path, len(frames), "frames", os.path.getsize(path) // 1024, "KB")


@functools.lru_cache(maxsize=None)
def player_frames():
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        names = ("Mechanist/Armor/BrassHelmet_Head", "Mechanist/Armor/BrassChestplate_Body", "Mechanist/Armor/BrassGreaves_Legs")
        parts = [AP.load_frames("Content/%s.png" % n, 4)[0] for n in names]
        bob = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3
        return tuple(AP.compose(parts[0], parts[1], parts[2], f, bob) for f in range(20))
    finally:
        os.chdir(cwd)


def put_player(img, x, feet, frame=0, right=True):
    p = player_frames()[frame % 20]
    p = p if right else mirror(p)
    blit(img, p, int(x) - p.width // 2, int(feet) - p.height + 2)


def backdrop(w=W, h=H, floor=FLOOR, sky=((22, 30, 44), (26, 36, 52), (30, 42, 60), (34, 48, 68)), ground=(58, 46, 40)):
    img = Image.new("RGBA", (w, h), sky[0] + (255,))
    d = ImageDraw.Draw(img)
    for i, col in enumerate(sky):
        d.rectangle([0, floor * i // len(sky), w, floor * (i + 1) // len(sky)], fill=col + (255,))
    if floor + 3 >= h:
        return img                                                # no ground strip (the scene draws its own tiles)
    d.rectangle([0, floor, w, h], fill=ground + (255,))
    for x in range(0, w, 16):
        d.rectangle([x, floor, x + 15, floor + 2], fill=(92, 120, 70, 255))
        d.rectangle([x + 15, floor + 3, x + 15, h], fill=(44, 34, 30, 255))
    return img


def cross(img, x, y, colour=(255, 255, 255, 255)):
    d = ImageDraw.Draw(img)
    d.line([(x - 5, y), (x + 5, y)], fill=colour)
    d.line([(x, y - 5), (x, y + 5)], fill=colour)


# ================================================================================================
# The Jade Cursed Glaives
# ================================================================================================
def glaives_gif(path):
    rel = "Content/Bosses/Jadey/Weapons/"
    r = consts(rel + "JadeGlaiveRigData.cs")
    a = arrays(rel + "JadeGlaiveRigData.cs")
    c = consts(rel + "JadeCursedGlaives.cs", rel + "JadeGlaiveSlash.cs")
    sheet, trail = load(rel + "JadeGlaiveSlash.png"), load(rel + "JadeGlaiveSlash_Trail.png")
    cw, ch, gap, n, samples = r["CellWidth"], r["CellHeight"], r["Gap"], r["FramesPerSlash"], r["SamplesPerSlash"]
    use = int(c["UseTime"])
    follow = c["AimFollow"]
    ph = 200
    px, feet = 220, 150
    pc = (px, feet - 21)
    slashes = 8
    total = slashes * use

    def cursor(t):
        ang = -math.pi / 2 + t / total * math.tau * 1.25           # round the player, a turn and a quarter
        return pc[0] + math.cos(ang) * 120, pc[1] + math.sin(ang) * 70

    def draw(panel, kind, age, side, tilt, body_right):
        prog = max(0.0, min(1.0, age / use))
        f = min(n - 1, int(prog * n))
        s = kind * samples + f * 2
        hub = (a["HubX"][s], a["HubY"][s])
        rx, ry = hub[0] - r["ShoulderX"], hub[1] - r["ShoulderY"]
        ct, st = math.cos(tilt), math.sin(tilt)
        body = 1 if body_right else -1
        hand = (pc[0] + body * r["ShoulderX"] + (rx * ct - ry * st) * side, pc[1] + r["ShoulderY"] + rx * st + ry * ct)
        box = (kind * (cw + gap), f * (ch + gap), kind * (cw + gap) + cw, f * (ch + gap) + ch)
        cell, tcell = sheet.crop(box), trail.crop(box)
        ox, oy = r["OriginX"] + hub[0], r["OriginY"] + hub[1]
        near = a["Near"][kind * n + f] if kind * n + f < len(a["Near"]) else 1

        def slash():
            for layer, add in ((tcell, 0.85), (cell, None)):
                im = layer if side > 0 else mirror(layer)
                o = (ox, oy) if side > 0 else (cw - ox, oy)
                put_rotated(panel, im, tilt if side > 0 else -tilt, o, hand, add)
        if not near:
            slash()
        put_player(panel, px, feet, 0, body_right)
        if near:
            slash()

    frames = []
    before = {"tilt": 0.0, "side": 1}
    after = {"tilt": 0.0, "side": 1}
    for t in range(total):
        kind, age = (t // use) % 2, t % use + 1
        mx, my = cursor(t)
        dx, dy = mx - pc[0], my - pc[1]
        side = -1 if dx < 0 else 1
        want = math.atan2(dy, abs(dx))
        if age == 1:                                              # the slash spawns aimed at the cursor (both versions)
            before["side"], before["tilt"] = side, want
            after["side"], after["tilt"] = side, want
        else:                                                     # 0.2.2: TrackCursor, every tick
            after["side"] = side
            after["tilt"] = max(-math.pi / 2, min(math.pi / 2, after["tilt"] + (want - after["tilt"]) * follow))
        if t % 2:
            continue
        img = Image.new("RGBA", (W, 2 * ph + 4), (0, 0, 0, 255))
        for k, (state, body_right, name) in enumerate((
                (before, True, "0.2.1: aimed once as it starts; the body keeps facing the way it walked (right)"),
                (after, after["side"] > 0, "0.2.2: follows the cursor (+) every tick; the body faces the slash"))):
            panel = backdrop(W, ph, feet)
            draw(panel, kind, age, state["side"], state["tilt"], body_right)
            cross(panel, mx, my)
            label(panel, name, 4, 4)
            img.paste(panel, (0, k * (ph + 4)))
        frames.append(img)
    save_gif(frames, path, ms=33, scale=1)


# ================================================================================================
# The Cogspring Sword
# ================================================================================================
def cogspring_gif(path):
    rel = "Content/Mechanist/Weapons/"
    c = consts(rel + "CogspringSword.cs")
    sword, glow, trail = load(rel + "CogspringSword.png"), load(rel + "CogspringSword_Glow.png"), load(rel + "CogspringTrail.png")
    use = int(c["UseTime"])
    tw, th, tpx, tpy, gapt = int(c["TrailW"]), int(c["TrailH"]), int(c["TrailPivotX"]), int(c["TrailPivotY"]), int(c["Gap"])
    frames_n, step = int(c["TrailFrames"]), math.radians(12)
    trail_ticks, tmin, tfull, topacity = int(c["TrailTicks"]), c["TrailMin"], c["TrailFull"], c["TrailOpacity"]
    glow_strength = c["GlowStrength"]
    px, feet = 220, FLOOR
    pos = (px - 10, feet - 42)                                    # the player's top-left (a 20 x 42 hitbox)

    def item_rotation(anim, direction):
        return (anim / use - 0.5) * -direction * 3.5 - direction * 0.3

    def item_location(anim, direction):
        third = anim / use
        cx = pos[0] + 10
        if third < 0.333:
            return cx + 12 * direction, pos[1] + 24
        if third < 0.666:
            return cx + 12 * direction, pos[1] + 14
        return cx - 12 * direction, pos[1] + 14

    def blade_dir(rot, direction):
        base = -3 * math.pi / 4 if direction == -1 else -math.pi / 4
        return math.cos(base + rot), math.sin(base + rot)

    frames = []
    ring = []
    for swing in range(4):
        direction = 1 if swing < 2 else -1
        ring = []
        for anim in range(use, 0, -1):
            rot = item_rotation(anim, direction)
            ring.append(rot)
            loc = item_location(anim, direction)
            img = backdrop()
            body = 1 if anim / use > 0.666 else 2 if anim / use > 0.333 else 3
            put_player(img, px, feet, body, direction > 0)
            # the phantom slash (CogspringTrailLayer.Draw)
            back = min(trail_ticks, len(ring) - 1)
            if back >= 1:
                now = blade_dir(rot, direction)
                then = blade_dir(ring[-1 - back], direction)
                sweep = math.atan2(then[0] * now[1] - then[1] * now[0], then[0] * now[0] + then[1] * now[1])
                span = abs(sweep)
                if span >= tmin:
                    k = max(1, min(frames_n, int(span / step + 0.5))) - 1
                    fr = trail.crop((0, k * (th + gapt), tw, k * (th + gapt) + th))
                    clockwise = sweep > 0
                    o = (tpx, tpy if clockwise else th - tpy)
                    fr = fr if clockwise else flip_v(fr)
                    opacity = topacity * max(0.35, min(1.0, span / tfull))
                    put_rotated(img, fr, math.atan2(now[1], now[0]), o, loc, opacity)
            # the sword as vanilla draws a swing: its corner on itemLocation, turned by itemRotation; the lights over it
            spr, gl = (sword, glow) if direction > 0 else (mirror(sword), mirror(glow))
            o = (0, sword.height) if direction > 0 else (sword.width, sword.height)
            put_rotated(img, spr, rot, o, loc)
            put_rotated(img, gl, rot, o, loc, glow_strength)
            label(img, "COGSPRING SWORD 0.2.2: vanilla's swing (use time %d), its lights, the phantom slash under it" % use, 4, 4)
            label(img, "facing %s" % ("right" if direction > 0 else "left"), 4, 18)
            if anim % 2 == 0:
                frames.append(img)
    save_gif(frames, path, ms=33, scale=2)


# ================================================================================================
# Trash-Tr0m's slam wave
# ================================================================================================
def wave_gif(path):
    rel = "Content/Bosses/TrashTr0m/"
    c = consts(rel + "TrashTr0m.Attacks.cs", rel + "Projectiles/TrashTr0mShockwave.cs")
    sprite = load(rel + "Projectiles/TrashTr0mShockwave.png")
    speed = c["ShockwaveSpeed"]
    hw, hh = int(c["HitboxWidth"]), int(c["HitboxHeight"])
    fw, fh, stride, nframes, tpf = 88, 60, 62, int(c["Frames"]), int(c["TicksPerFrame"])
    # the ground: row 30 (y 480) with bumps of 4, 6 and 8 tiles and a 9-tile drop, over 2200 px
    cols = 140
    top = [30] * cols
    for x0, x1, hgt in ((16, 19, 4), (34, 36, 6), (52, 56, 8), (72, 74, 3)):
        for x in range(x0, x1 + 1):
            top[x] = 30 - hgt
    for x in range(88, cols):
        top[x] = 39                                               # a 9-tile drop
    for x0, x1, hgt in ((104, 107, 7), (120, 121, 5)):
        for x in range(x0, x1 + 1):
            top[x] = 39 - hgt

    def solid(x, y):
        return 0 <= x < cols and y >= top[x]

    def surface_old(wx, bottom):
        step, drop = 3, 6
        x = int(wx // 16)
        row = int((bottom - 1) // 16) + 1
        air = not solid(x, row - step - 1)
        for y in range(row - step, row + drop + 1):
            s = solid(x, y)
            if s and air:
                return y * 16
            air = not s
        return None

    def surface_new(wx, bottom):
        step, drop = int(c["MaxStepUp"]), int(c["MaxDrop"])
        x = int(wx // 16)
        row = int((bottom - 1) // 16) + 1
        if solid(x, row):
            for y in range(row, row - step - 1, -1):
                if not solid(x, y - 1):
                    return y * 16
            return None
        for y in range(row + 1, row + drop + 1):
            if solid(x, y):
                return y * 16
        return None

    def run(find, life):
        cxw, bottom = 3 * 16.0, 30 * 16.0
        out = []
        for t in range(life):
            front = cxw + hw / 2
            g = find(front, bottom)
            if g is None:
                out.append((cxw, bottom, t, True))
                return out
            bottom = g
            cxw += speed
            out.append((cxw, bottom, t, False))
        return out

    old = run(surface_old, 72)
    new = run(surface_new, int(c["Lifetime"]))
    lane = 200
    frames = []
    for t in range(max(len(old), len(new)) + 12):
        img = Image.new("RGBA", (W, 2 * lane + 4), (0, 0, 0, 255))
        for k, (track, name, rng) in enumerate(((old, "before: climbs 3, drops 6, runs 1008 px", 1008),
                                                (new, "0.2.2: climbs %d, drops %d to the nearest surface, runs %d px"
                                                 % (int(c["MaxStepUp"]), int(c["MaxDrop"]), int(c["RangePx"])), int(c["RangePx"])))):
            i = min(t, len(track) - 1)
            cxw, bottom, age, broke = track[i]
            camx = cxw - W / 2
            camy = bottom - 130                                   # the camera follows the wave
            panel = backdrop(W, lane, lane, ground=(0, 0, 0))
            d = ImageDraw.Draw(panel)
            for x in range(cols):
                sx = x * 16 - camx
                if sx < -16 or sx > W:
                    continue
                for y in range(top[x], top[x] + 14):
                    sy = y * 16 - camy
                    if sy > lane:
                        break
                    shade = (96, 78, 62) if y == top[x] else (70, 56, 46)
                    d.rectangle([sx, sy, sx + 15, sy + 15], fill=shade + (255,))
                    d.rectangle([sx + 15, sy, sx + 15, sy + 15], fill=(48, 38, 32, 255))
            gone = broke or t >= len(track)
            if not gone:
                frame = (age // tpf) % nframes
                spr = mirror(sprite.crop((0, frame * stride, fw, frame * stride + fh)))   # the art rolls left: mirrored for right
                blit(panel, spr, int(cxw - fw / 2 - camx), int(bottom + 2 - fh - camy))
            dist = cxw - 3 * 16.0
            label(panel, name, 4, 4)
            label(panel, "%s  %4d / %d px" % ("BROKE" if broke and t >= i else "running" if not gone else "done", dist, rng), 4, 18)
            img.paste(panel, (0, k * (lane + 4)))
        if t % 2 == 0:
            frames.append(img)
    save_gif(frames, path, ms=33, scale=1)


# ================================================================================================
# The Jade Refractor's wind-up
# ================================================================================================
def refractor_gif(path):
    rel = "Content/Research/Weapons/"
    c = consts(rel + "JadeRefractorBeam.cs", rel + "JadeRefractor.cs")
    gun, beam, spark = load(rel + "JadeRefractor.png"), load(rel + "JadeRefractorBeam.png"), load(rel + "JadeRefractorSpark.png")
    wind, pre, motes, ring = int(c["WindUpTicks"]), int(c["PreFireTicks"]), int(c["Motes"]), c["MoteRing"]
    seg, bh, bstride, bframes, bft = int(c["SegmentLength"]), int(c["BeamHeight"]), int(c["BeamStride"]), int(c["BeamFrames"]), int(c["BeamFrameTicks"])
    ss, sframes, sstride, sft = int(c["SparkSize"]), int(c["SparkFrames"]), int(c["SparkStride"]), int(c["SparkFrameTicks"])
    grip = (15, 21)
    muzzle_off = (48, -6)
    px, feet = 110, FLOOR
    hand = (px, feet - 21)
    wall_x = 410
    frames = []
    age = 0
    held = list(range(0, 130)) + [None] * 16 + list(range(0, 50))
    for t, k in enumerate(held):
        img = backdrop()
        d = ImageDraw.Draw(img)
        d.rectangle([wall_x, 40, W, FLOOR], fill=(86, 92, 104, 255))
        my = 70 + 20 * math.sin(t / 40.0)
        dx, dy = wall_x - hand[0], my - hand[1]
        ln = math.hypot(dx, dy)
        dirv = (dx / ln, dy / ln)
        put_player(img, px, feet, 0, True)
        if k is None:
            label(img, "let go: the beam is gone; held again, it winds up again", 4, 4)
            frames.append(img)
            continue
        age += 1
        windup = min(wind, k + 1)
        charge = windup / wind
        firing = windup >= wind
        normal = (-dirv[1], dirv[0])
        lens = (hand[0] + dirv[0] * muzzle_off[0] + normal[0] * muzzle_off[1], hand[1] + dirv[1] * muzzle_off[0] + normal[1] * muzzle_off[1])
        length = math.hypot(wall_x - lens[0], my - lens[1]) if (firing or windup >= wind - pre) else 0

        def draw_beam(opacity, stars):
            f0 = age // bft
            piece, tt = 0, 0.0
            while tt < length:
                wpx = int(min(seg, length - tt))
                if wpx <= 0:
                    break
                f = ((f0 - piece) % bframes + bframes) % bframes
                src = beam.crop((0, f * bstride, wpx, f * bstride + bh))
                at = (lens[0] + dirv[0] * tt, lens[1] + dirv[1] * tt)
                put_rotated(img, src, math.atan2(dirv[1], dirv[0]), (0, bh / 2), at, opacity)
                tt += seg
                piece += 1
            if stars:
                sf = (age // sft) % sframes
                st = spark.crop((0, sf * sstride, ss, sf * sstride + ss))
                blit_add(img, st, lens[0] - ss // 2, lens[1] - ss // 2)
                blit_add(img, st, lens[0] + dirv[0] * length - ss // 2, lens[1] + dirv[1] * length - ss // 2)

        if firing:
            draw_beam(1.0, True)
            label(img, "the laser: 1 steam a use from here", 4, 4)
        else:
            mote = spark.crop((0, (sframes - 1) * sstride, ss, (sframes - 1) * sstride + ss))
            for m in range(motes):
                phase = (m / motes + charge * 1.5) % 1.0
                rr = ring * (1 - phase) * (1 - 0.6 * charge)
                ang = m * math.tau / motes + charge * 2.5
                at = (lens[0] + math.cos(ang) * rr, lens[1] + math.sin(ang) * rr)
                alpha = (0.25 + 0.55 * charge) * math.sin(phase * math.pi)
                blit_add(img, mote, round(at[0]) - ss // 2, round(at[1]) - ss // 2, alpha)
            rate = max(1, sft - int(charge * 2))
            sf = (age // rate) % sframes
            st = spark.crop((0, sf * sstride, ss, sf * sstride + ss))
            blit_add(img, st, round(lens[0]) - ss // 2, round(lens[1]) - ss // 2, 0.2 + 0.8 * charge * charge)
            if windup >= wind - pre and length > 0 and (age & 2) == 0:
                draw_beam(0.3, False)
            label(img, "wind-up %d / %d ticks: no beam, no hits, no steam" % (windup, wind), 4, 4)
        put_rotated(img, gun, math.atan2(dirv[1], dirv[0]), grip, hand)
        cross(img, wall_x - 2, my)
        frames.append(img)
    save_gif([f for i, f in enumerate(frames) if i % 2 == 0], path, ms=33, scale=2)


# ================================================================================================
# The overheat's turns
# ================================================================================================
def overheat_gif(path):
    max_run, acc, slow = 3.0, 0.08, 0.2                          # vanilla's defaults (Player.ResetEffects / HorizontalMovement)

    def held(t):
        if t < 40:
            return 1
        return -1 if ((t - 40) // 10) % 2 == 0 else 1             # switching every 10 ticks

    def step(v, h, last, fixed):
        if fixed and last != 0 and h != last and v * h < 0:
            v = h * min(abs(v), max_run)                          # SteamPlayer.SetControls (0.2.2)
        if h < 0 and v > -max_run:
            if v > slow:
                v -= slow
            v -= acc
        elif h > 0 and v < max_run:
            if v < -slow:
                v += slow
            v += acc
        return max(-max_run, min(max_run, v))

    lane = 110
    ticks = 240
    sims = []
    for fixed in (False, True):
        v, x, last, rows = 0.0, 60.0, 0, []
        for t in range(ticks):
            h = held(t)
            v = step(v, h, last, fixed)
            last = h
            x += v
            rows.append((x, v, h))
        sims.append(rows)
    frames = []
    for t in range(0, ticks, 3):
        img = Image.new("RGBA", (W, 2 * lane + 4), (0, 0, 0, 255))
        for k, (rows, name) in enumerate(((sims[0], "before: each turn brakes first (0.28 px/tick a tick)"),
                                          (sims[1], "0.2.2: a new direction keeps the speed"))):
            panel = backdrop(W, lane, lane - 20)
            x, v, h = rows[t]
            sx = (x % (W + 40)) - 20
            frame = 6 + (t // 3) % 14 if abs(v) > 0.3 else 0
            put_player(panel, sx, lane - 20, frame, v >= 0 if abs(v) > 0.3 else h > 0)
            d = ImageDraw.Draw(panel)
            gx, gy, gw = 250, 30, 180
            d.rectangle([gx, gy, gx + gw, gy + 40], fill=(14, 14, 18, 255))
            d.line([(gx, gy + 20), (gx + gw, gy + 20)], fill=(70, 70, 80, 255))
            for i in range(0, t + 1, 2):
                vx = rows[i][1]
                d.point((gx + int(i / ticks * gw), gy + 20 - int(vx / max_run * 18)), fill=(118, 220, 162, 255))
            label(panel, name, 4, 4)
            label(panel, "overheated, held: %s   speed %+.2f px/tick" % ("right" if h > 0 else "left", v), 4, 18)
            img.paste(panel, (0, k * (lane + 4)))
        frames.append(img)
    save_gif(frames, path, ms=50, scale=2)


SCENES = {
    "glaives": ("weapon-jade-glaives-tracking.gif", glaives_gif),
    "cogspring": ("weapon-cogspring-swing.gif", cogspring_gif),
    "wave": ("boss-trashtr0m-wave-climb.gif", wave_gif),
    "refractor": ("weapon-jade-refractor-windup.gif", refractor_gif),
    "overheat": ("mechanist-overheat-turns.gif", overheat_gif),
}


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
