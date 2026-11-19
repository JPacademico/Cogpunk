"""Cogpunk's teaser trailer (61 s, 1920x1080, 60 fps). Run from the repo root:

    python -P tools/promo/make_teaser.py --music PATH/TO/track.mp3 [--out docs/media/promo/cogpunk-teaser.mp4]
                                         [--logo docs/media/promo/Cogpunk-logo.png] [--ffmpeg PATH] [--encoder h264_nvenc]
                                         [--only 45.47,47.55]      # one span, for a quick look
    python -P tools/promo/make_teaser.py --stills 1.0,14.0,33.9 --out-dir SOME/DIR      # single frames, for review
    python -P tools/promo/make_teaser.py --contact SOME/FILE.png                         # one frame of every shot

What it is: every shot is staged here from the mod's real art and numbers, not captured from a running game (a notice in
the bottom bar says so the whole time, user 2026-11-17): the world
backdrops are the D5 replays of the world-generation passes (tools/promo/plates.py: Coghaven, Westworld, the Fundamental
Ruins, the Junkyard), the bosses are posed by the same ported pose functions that make their proofs (tools/sim/
trashtr0m_sim.py, tartyrant_sim.py) or read from their generated RigData, the weapons use their own sheets and constants
(the Firesaw's swing curve, the Diamond Cutter's beam strip, the Combinator's sprite gluing rule line for line). Leaves out:
the game's lighting and UI, vanilla's art (sand, clouds, Dynasty furniture are the sims' flat stand-ins; the "player" is the
Brass armor's own sheets on a mannequin), netcode.

The cut: the music's accents were measured (a waltz at ~172 BPM: a quiet intro to 12.0 s, the theme to 32.9 s, accents
every two bars, 2.09 s, to 57.0 s, then a fall), and every cut below sits on one of them (CUTS). Stylised: letterbox
bars, a vignette, a flash and a chroma split on each cut, shakes on impacts, brass pixel titles; the logo is composited
at 1080p. Everything else is pixel-exact (tools/promo/stage.py: zooms of 0.5, 1 and 2 only, shown at 3x).
"""
import argparse
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sim"))

import plates  # noqa: E402
import stage as S  # noqa: E402
from stage import (W, H, FPS, HD_W, HD_H, BRASS, STEAM, EMBER, GHOST, IRON, CRIMSON, View, Sheet, Particles, load, consts, text, blit,  # noqa: E402
                   put_centered, ease, ease_out, lerp, faded, tinted, mirror, strip, vanilla_frames)

BAR = 22                                    # the letterbox bars, stage px
NOTICE = "IN-ENGINE  SIMULATION   -   NOT  IN-GAME  FOOTAGE"
NOTICE_ALPHA = 0.8


# ================================================================================================
# Shared actors
# ================================================================================================
_memo = {}


def memo(key, make):
    if key not in _memo:
        _memo[key] = make()
    return _memo[key]


def rig(rel):
    return consts(rel)


def sheet_of(base, rigdata, cols=None):
    """A Sheet from a generated RigData file (CellWidth/CellHeight/OriginX/OriginY, Columns when it has them)."""
    def make():
        k = rig(rigdata)
        return Sheet(base, k["CellWidth"], k["CellHeight"], k["OriginX"], k["OriginY"], cols=cols or k.get("Columns", 1)), k
    return memo(("sheet", base), make)


def player(frame=0, flip=False, armor="Brass"):
    """The player stand-in: the armor's own equip sheets on the sims' mannequin (tools/sim/armor_preview.py), facing right."""
    def make():
        import armor_preview as ap
        names = {"Brass": ("Mechanist/Armor/BrassHelmet_Head", "Mechanist/Armor/BrassChestplate_Body", "Mechanist/Armor/BrassGreaves_Legs"),
                 "Scrap": ("Scrap/Armor/ScrapHelmet_Head", "Scrap/Armor/ScrapBreastplate_Body", "Scrap/Armor/ScrapLeggings_Legs")}[armor]
        cwd = os.getcwd()
        os.chdir(S.ROOT)
        try:
            parts = [ap.load_frames("Content/%s.png" % n, 4)[0] for n in names]
            bob = [0] * 7 + [-1] * 3 + [0] * 4 + [-1] * 3 + [0] * 3
            return [ap.compose(parts[0], parts[1], parts[2], f, bob) for f in range(20)]
        finally:
            os.chdir(cwd)
    frames = memo(("player", armor), make)
    img = frames[frame % 20]
    return mirror(img) if flip else img


WALK = list(range(6, 20))                   # vanilla's walk cycle frames


def put_player(view, x, feet_y, frame=0, flip=False, armor="Brass"):
    img = player(frame, flip, armor)
    view.put(img, x - img.width // 2, feet_y - img.height + 2)
    return (x + (-6 if flip else 6), feet_y - 32)        # the hand


def rotated(sprite, angle, pivot):
    """The sprite turned by `angle` radians (clockwise on screen) about `pivot` (its own px), nearest-neighbour, as the game
    turns swung items: returns (image, pivot in the image)."""
    w, h = sprite.size
    r = int(math.ceil(math.hypot(max(pivot[0], w - pivot[0]), max(pivot[1], h - pivot[1])))) + 2
    pad = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    pad.alpha_composite(sprite, (int(r - pivot[0]), int(r - pivot[1])))
    return pad.rotate(-math.degrees(angle), resample=Image.NEAREST, center=(r, r)), (r, r)


def number(view, x, y, value, age, crit=False):
    """A damage number rising and fading (the game's combat text, in the palette's ember)."""
    if age < 0 or age > 40:
        return
    img = text(str(value), 13 if crit else 11, "plain", EMBER[3] if crit else (255, 224, 150), EMBER[2] if crit else EMBER[3], EMBER[0])
    view.put(faded(img, min(1.0, (40 - age) / 12.0)), x - img.width // 2, y - age * 0.9)


def hit_flash(sprite, age, length=5):
    return tinted(sprite, (255, 255, 255), 0.85 * (1 - age / length)) if 0 <= age < length else sprite


def lower_third(img, t, dur, title, sub=None):
    """A location / weapon name sliding in over the bottom bar: a brass title, a rule with a cog's tooth, a steam-grey sub."""
    if not title:
        return
    a = ease_out(t / 0.28) * (1.0 if t < dur - 0.2 else max(0.0, (dur - t) / 0.2))
    if a <= 0:
        return
    tt = text(title, 22, "title")
    x = int(lerp(-tt.width - 10, 26, ease_out(t / 0.28)))
    y = H - BAR - 31 - tt.height
    d = ImageDraw.Draw(img)
    d.rectangle([x - 2, y + tt.height + 3, x + tt.width + 8, y + tt.height + 4], fill=BRASS[4] + (255,))
    d.rectangle([x - 2, y + tt.height + 5, x + tt.width + 8, y + tt.height + 5], fill=BRASS[1] + (255,))
    d.rectangle([x - 6, y + tt.height + 1, x - 3, y + tt.height + 6], fill=BRASS[5] + (255,))
    blit(img, faded(tt, a), x, y)
    if sub:
        st = text(sub, 10, "plate", STEAM[2], STEAM[0], IRON[0])
        blit(img, faded(st, a), x + 2, y + tt.height + 9)


def big_word(img, t, word, size=44, y=None, hold=9.0, top=BRASS[5], bottom=BRASS[3], outline=BRASS[0]):
    """A word slammed onto the middle of the stage: three frames oversize, then it sits, then it fades."""
    if t < 0 or t > hold:
        return
    slam = t * FPS
    sz = size + (12 if slam < 2 else 6 if slam < 4 else 0)
    tt = text(word, sz, "title", top, bottom, outline)
    a = 1.0 if t < hold - 0.25 else max(0.0, (hold - t) / 0.25)
    put_centered(img, faded(tt, a), W // 2, (H // 2 if y is None else y))


def boss_card(img, t, dur, name, epithet):
    """The game's boss title card, restaged: the epithet small over the name, slammed in, low on the stage."""
    if t < 0.12:
        return
    tt = t - 0.12
    a = 1.0 if t < dur - 0.18 else max(0.0, (dur - t) / 0.18)
    slam = tt * FPS
    nm = text(name, 34 + (10 if slam < 2 else 4 if slam < 4 else 0), "title", EMBER[3], EMBER[2], EMBER[0])
    y = H - BAR - 26 - nm.height // 2
    top = H - BAR - 64
    for k, alpha in enumerate((60, 110, 150)):                                           # a stepped dark band behind the card
        blit(img, Image.new("RGBA", (W, 64 - k * 6), S.INK + (int(alpha * a),)), 0, top + k * 6)
    ImageDraw.Draw(img).rectangle([0, top + 12, W, top + 12], fill=EMBER[1] + (255,))
    put_centered(img, faded(nm, a), W // 2, y)
    if epithet:
        ep = text(epithet, 11, "plate", STEAM[2], STEAM[1], IRON[0])
        put_centered(img, faded(ep, a), W // 2, y - nm.height // 2 - 10)


# ================================================================================================
# Shots (each: frame(t) -> the 640x360 stage image; t in seconds from the shot's start; frames come in order)
# ================================================================================================
class Shot:
    label = None                              # (title, sub) for the lower third
    tint = None                               # a colour grade (multiply)

    def __init__(self, dur):
        self.dur = dur
        self.n = 0

    def frame(self, t):
        raise NotImplementedError

    def shake(self, t):
        return (0, 0)


class Black(Shot):
    def __init__(self, dur, lines=()):
        super().__init__(dur)
        self.lines = lines                    # (time, text, size, y)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), (8, 7, 10, 255))
        for (at, s, size, y) in self.lines:
            if t >= at:
                tt = text(s, size, "title" if size >= 16 else "plate")
                a = min(1.0, (t - at) / 0.25) * (1.0 if t < self.dur - 0.3 else max(0.0, (self.dur - t) / 0.3))
                put_centered(img, faded(tt, a), W // 2, y)
        return img


# --- the intro: brass, steam, clockwork ------------------------------------------------------------------------------
class CogMacro(Shot):
    """A Bronze Cog turning in its socket in Coghaven's cloud, close (zoom 2), night-graded."""
    tint = (150, 165, 215)

    def __init__(self, dur, word):
        super().__init__(dur)
        self.cg = plates.coghaven()
        self.word = word
        kind, x, y, w, h, style = [m for m in self.cg.isl.multi if m[0] == "cog" and m[2] > self.cg.isl.s][2]
        px, py = self.cg.px(x, y)
        self.c = (px + 48, py + 48)

    def frame(self, t):
        self.cg.step()
        v = View(self.c[0] - 14 + t * 5, self.c[1] + 4, zoom=2)
        self.cg.draw(v)
        img = v.out()
        big_word(img, t - 0.16, self.word, 46, hold=self.dur - 0.2)
        return img


class TurbineMacro(Shot):
    """A Lift Turbine under the island, its rotor over the fire, smoke pouring down."""
    tint = (165, 170, 215)

    def __init__(self, dur, word):
        super().__init__(dur)
        self.cg = plates.coghaven()
        self.word = word
        kind, x, y, w, h, style = [m for m in self.cg.isl.multi if m[0] == "turbine"][2]
        px, py = self.cg.px(x, y)
        self.c = (px + 32, py + 70)

    def frame(self, t):
        self.cg.step()
        v = View(self.c[0], self.c[1] - 16 + t * 7, zoom=2)
        self.cg.draw(v)
        img = v.out()
        big_word(img, t, self.word, 46, hold=self.dur - 0.2)
        return img


class HallMacro(Shot):
    """The Main Hall's throne between its two great cogs."""
    tint = (215, 190, 160)

    def __init__(self, dur, word):
        super().__init__(dur)
        self.cg = plates.coghaven()
        self.word = word
        cogs = sorted([m for m in self.cg.isl.multi if m[0] == "cog" and m[2] < self.cg.isl.s - 3], key=lambda m: m[1])[:2]
        xs = [self.cg.px(m[1], m[2])[0] + 48 for m in cogs]
        self.c = (sum(xs) / len(xs), self.cg.px(0, cogs[0][2])[1] + 40)

    def frame(self, t):
        self.cg.step()
        v = View(self.c[0] - 20 + t * 9, self.c[1], zoom=1)
        self.cg.draw(v)
        img = v.out()
        big_word(img, t, self.word, 46, y=H // 2 + 96, hold=self.dur - 0.15)
        return img


class StoneMacro(Shot):
    """The Fundamental Stone under its shield, in the dark."""

    def __init__(self, dur):
        super().__init__(dur)
        self.plate, self.stone, self.gate = plates.ruins()

    def frame(self, t):
        v = View(self.stone[0], self.stone[1] - 30 - t * 6, zoom=2)
        v.plate(self.plate)
        return v.out()


# --- exploration -------------------------------------------------------------------------------------------------------
class Junkyard(Shot):
    label = ("THE JUNKYARD", "A SEA OF RUST AND TAR")

    def __init__(self, dur):
        super().__init__(dur)
        self.plate, self.gy, self.cx = plates.junkyard()
        self.rust = vanilla_frames("Content/Junkyard/NPCs/RustCollector.png", 11)
        self.tar = vanilla_frames("Content/Junkyard/NPCs/LivingTar.png", 2)
        self.roll = [[790.0, 1.3, None], [1650.0, -1.2, None]]                             # Rust Collectors: x, speed, y

    def frame(self, t):
        f = t * FPS
        cam_x = lerp(self.cx - 430, self.cx + 150, ease(t / self.dur) * 0.6 + t / self.dur * 0.4)
        v = View(cam_x, self.gy - 96, zoom=1)
        v.plate(self.plate)
        for k, c in enumerate(self.roll):                                                  # rolling over the heaps, a block at a time
            c[0] += c[1]
            top = plates.junkyard_top(c[0])
            c[2] = top if c[2] is None else c[2] + max(-6, min(6, top - c[2]))
            fr = self.rust[int(f / 5 + k * 3) % 8]
            v.put(mirror(fr) if c[1] > 0 else fr, c[0] - 20, c[2] - 38)
        for k, x0 in enumerate((850, 912, 1470)):                                          # Living Tar hopping on the sand
            ph = (f + k * 23) % 70
            hop = max(0.0, math.sin(min(1.0, ph / 34.0) * math.pi)) * 26
            v.put(self.tar[0 if hop < 4 else 1], x0 + (ph * 0.5 if ph < 34 else 17) - 16, plates.junkyard_top(x0) - 22 - hop)
        return v.out()


class Westworld(Shot):
    label = ("WESTWORLD", "THE OLD BRASS TOWN, BURIED UNDER THE DESERT")

    def __init__(self, dur):
        super().__init__(dur)
        self.plate, self.floor, self.town = plates.westworld()
        self.bandit, self.kb = sheet_of("Content/OldBrassTown/NPCs/BrassBandit", "Content/OldBrassTown/NPCs/BrassBanditRigData.cs")
        self.sheriff, self.ks = sheet_of("Content/OldBrassTown/NPCs/Sheriff", "Content/OldBrassTown/NPCs/SheriffRigData.cs")
        self.bull, self.ku = sheet_of("Content/OldBrassTown/NPCs/MechanicalBull", "Content/OldBrassTown/NPCs/MechanicalBullRigData.cs")
        box = self.plate.convert("L").point(lambda p: 255 if p > 90 else 0).getbbox() or (1300, 0, 3700, 0)
        self.x0, self.x1 = box[0] + 380, box[2] - 380

    def frame(self, t):
        f = t * FPS
        cam_x = lerp(self.x0, self.x1, t / self.dur * 0.62)
        v = View(cam_x, self.floor - 108, zoom=1)
        v.plate(self.plate)
        gy = self.floor
        bx = self.x0 + 340 - f * 0.75                                                      # a Brass Bandit walking the street
        v.sheet(self.bandit, self.kb["Walk"] + int(f * 0.75 / self.kb["WalkStep"]) % self.kb["WalkFrames"], bx, gy)
        sx = self.x0 + 560                                                                 # the Sheriff, at his post
        v.sheet(self.sheriff, self.ks["Idle"] + int(f / 30) % self.ks["IdleFrames"], sx, gy)
        ux = self.x0 - 200 + f * 2.0                                                       # the Mechanical Bull trotting through
        v.sheet(self.bull, self.ku["Trot"] + int(f * 2.0 / self.ku["TrotStep"] / 2) % self.ku["TrotFrames"], ux, gy, flip=True)
        return v.out()


class CoghavenWide(Shot):
    label = ("COGHAVEN", "A JADE PALACE HELD ALOFT BY COGS AND STEAM")

    def __init__(self, dur):
        super().__init__(dur)
        self.cg = plates.coghaven()
        self.head, self.kh = sheet_of("Content/Coghaven/NPCs/FlyingBuddhaHead", "Content/Coghaven/NPCs/FlyingBuddhaHeadRigData.cs")

    def frame(self, t):
        self.cg.step()
        f = t * FPS
        w = self.cg.static.width
        v = View(lerp(w * 0.30, w * 0.66, t / self.dur), self.cg.surface_y - 150 + 40 * t / self.dur, zoom=0.5)
        self.cg.draw(v)
        hx = w * 0.42 + f * 1.3                                                           # a Flying Buddha Head adrift over the court
        hy = self.cg.surface_y - 330 + (int(f / 20) % 2) * 2
        v.sheet(self.head, self.kh["Float"] + int(f / 10) % self.kh["FloatFrames"], hx, hy)
        return v.out()


class Ruins(Shot):
    label = ("THE FUNDAMENTAL RUINS", "SOMETHING SLEEPS BEHIND THE SEALED GATE")

    def __init__(self, dur, lights=(0.7, 1.4, 2.1), leave=2.62):
        super().__init__(dur)
        self.lights, self.leave = lights, leave
        self.plates = [plates.ruins((0.2, 0.2, 0.2), True, tuple(1.0 if j < k else 0.18 for j in range(3))) for k in range(4)]
        self.stone, self.gate = self.plates[0][1], self.plates[0][2]
        self.parts = Particles(3)

    def frame(self, t):
        lit = sum(1 for at in self.lights if t >= at)
        plate = self.plates[lit][0]
        if t < self.leave:                                                                 # close on the gate while its sockets light
            v = View(self.gate[0], self.gate[1] + 30 + t * 4, zoom=2)
        else:                                                                              # then down the hall to the stone
            u = ease((t - self.leave) / (self.dur - self.leave - 0.25))
            v = View(self.gate[0], lerp(self.gate[1] + 120, self.stone[1] - 70, u), zoom=1)
        v.plate(plate)
        for k, at in enumerate(self.lights):                                               # a socket lights: motes off the gate
            if abs(t - at) < 0.5 / FPS:
                self.parts.burst(self.gate[0] - 32 + k * 32, self.gate[1], 14, [GHOST[5], S.STEAM[2], (124, 107, 224), (70, 58, 147)],
                                 speed=(0.4, 2.2), life=(24, 50), gravity=-0.02)
        if int(t * FPS) % 5 == 0:                                                          # the shield's motes
            self.parts.burst(self.stone[0] + random.Random(self.n).uniform(-26, 26), self.stone[1] - 30, 1,
                             [(198, 189, 255), (124, 107, 224), (70, 58, 147)], speed=(0.1, 0.5), life=(30, 60), gravity=-0.03,
                             spread=(-2.2, -0.9))
        self.parts.step()
        self.parts.draw(v)
        self.n += 1
        return v.out()


# --- the class -----------------------------------------------------------------------------------------------------------
class Mechanist(Shot):
    """The player in Brass armor on Coghaven's terrace, close: the steam gauge filling beside them (the HUD's own layers:
    tank, steam cropped to the level, cage), the class's weapons popping up one after another."""

    def __init__(self, dur):
        super().__init__(dur)
        self.cg = plates.coghaven()
        self.x = self.cg.static.width * 0.5 + 345
        self.gy = self.cg.surface_y
        self.layers = strip("Content/Mechanist/SteamGauge.png", 5)
        self.k = consts("Content/Mechanist/SteamGaugeSystem.cs")
        self.icons = [load("Content/Mechanist/Weapons/%s.png" % n) for n in ("Firesaw", "DiamondCutter", "BarrelGun", "CogLauncher", "TrapperChain")]
        self.parts = Particles(5)

    def gauge(self, fill):
        back, steam, hot, front, valve = self.layers
        im = back.copy()
        top = int(self.k["FillBottom"] - (self.k["FillBottom"] - self.k["FillTop"]) * fill) // 2 * 2
        if top < self.k["FillBottom"]:
            im.alpha_composite(steam.crop((0, top, steam.width, self.k["FillBottom"])), (0, top))
        im.alpha_composite(front)
        return im

    def frame(self, t):
        self.cg.step()
        f = int(t * FPS)
        v = View(self.x + 60, self.gy - 34, zoom=2)
        self.cg.draw(v)
        put_player(v, self.x, self.gy, frame=0)
        fill = ease(min(1.0, t / 1.6))                                                     # the steam rising in the glass
        v.put(self.gauge(fill), self.x + 24, self.gy - 72)
        if f % 3 == 0:                                                                     # the armor's vent
            self.parts.burst(self.x - 12, self.gy - 38, 1, [STEAM[3], STEAM[2], STEAM[1], STEAM[0]], speed=(0.3, 0.9), life=(20, 36), gravity=-0.03,
                             spread=(-2.4, -0.8))
        beat = 0.349
        k = int(t / beat)
        if k >= 1:                                                                         # a weapon on every beat
            age = (t - k * beat) * FPS
            ic = self.icons[(k - 1) % len(self.icons)]
            if ic.width > 64:
                ic = ic.crop(ic.getbbox())
            y = self.gy - 44 - ease_out(age / 8.0) * 6
            v.put(hit_flash(ic, age, 5), self.x + 98 - ic.width // 2, y - ic.height // 2)
        self.parts.step()
        self.parts.draw(v)
        img = v.out()
        big_word(img, t - 0.35, "A NEW CLASS", 24, y=64, hold=self.dur - 0.35, top=STEAM[3], bottom=STEAM[1], outline=IRON[0])
        big_word(img, t - 1.4, "THE MECHANIST", 44, y=H - BAR - 36, hold=self.dur - 1.4)
        return img


# --- weapons: a duel on a backdrop -------------------------------------------------------------------------------------
class Duel(Shot):
    """The player on the left, enemies on the right, on one of the world plates."""
    backdrop = "coghaven"

    def __init__(self, dur):
        super().__init__(dur)
        self.parts = Particles(11)
        self.hits = []                                                                     # (frame, x, y, value, crit)
        self.shake_until, self.shake_amp = -1, 0
        if self.backdrop == "coghaven":
            self.cg = plates.coghaven()
            self.gy = self.cg.surface_y
            self.px0 = self.cg.static.width * 0.5 + 330
        elif self.backdrop == "westworld":
            self.plate, self.gy, _ = plates.westworld()
            box = self.plate.convert("L").point(lambda p: 255 if p > 90 else 0).getbbox()
            self.px0 = (box[0] + box[2]) // 2 - 300
        elif self.backdrop == "junkyard":
            self.plate, self.gy, cx = plates.junkyard(True)                                # open ground left of the central heap
            self.px0 = 470
        else:
            self.plate, stone, gate = plates.ruins()
            self.gy = 47 * 16                                                              # the arena's floor (the plate starts 47 rows over it)
            self.px0 = stone[0] - 390

    def view(self, dx=0, dy=0, zoom=1):
        v = View(self.px0 + 150 + dx, self.gy - 86 + dy, zoom=zoom)
        if self.backdrop == "coghaven":
            self.cg.step()
            self.cg.draw(v)
        else:
            v.plate(self.plate)
        return v

    def jolt(self, frames, amp):
        self.shake_until, self.shake_amp = self.n + frames, amp

    def shake(self, t):
        if self.n <= self.shake_until:
            k = self.shake_until - self.n
            return ((k % 2) * self.shake_amp * (1 if k % 4 < 2 else -1), ((k + 1) % 2) * (self.shake_amp // 2))
        return (0, 0)

    def numbers(self, v):
        for (at, x, y, val, crit) in self.hits:
            number(v, x, y, val, self.n - at, crit)

    def finish(self, v):
        self.parts.step()
        self.parts.draw(v)
        self.numbers(v)
        self.n += 1
        return v.out()


class FiresawShot(Duel):
    label = ("FIRESAW", "A CHAINSAW GREATSWORD THAT BURNS ON STEAM")
    backdrop = "coghaven"

    def __init__(self, dur, strike=1.04):
        super().__init__(dur)
        self.strike = strike
        self.golem, self.kg = sheet_of("Content/Coghaven/NPCs/JadeGolem", "Content/Coghaven/NPCs/JadeGolemRigData.cs")
        self.k = consts("Content/Mechanist/Weapons/Firesaw.cs")
        self.blade = strip("Content/Mechanist/Weapons/FiresawFire.png", 3)
        self.trail = strip("Content/Mechanist/Weapons/FiresawTrailFire.png", 6)

    def swing(self, done):
        """Firesaw.SwingAngle's shape: a pull back, the slash from High to Low, an overshoot, a settle."""
        k = self.k
        hi, lo = k["High"], k["Low"]
        if done < k["WindEnd"]:
            return hi - k["PullBack"] * ease_out(done / k["WindEnd"])
        if done < k["SlashEnd"]:
            return lerp(hi - k["PullBack"], lo + k["Overshoot"], ease((done - k["WindEnd"]) / (k["SlashEnd"] - k["WindEnd"])))
        if done < k["SettleEnd"]:
            return lerp(lo + k["Overshoot"], lo, ease((done - k["SlashEnd"]) / (k["SettleEnd"] - k["SlashEnd"])))
        return lo

    def frame(self, t):
        f = t * FPS
        v = self.view(dx=40)
        px = self.px0 + 60
        gx = self.px0 + 300 - min(f, self.strike * FPS) * 0.7                              # the Golem lumbering in
        hit_age = (t - self.strike) * FPS
        if hit_age >= 0:
            gx += min(26, hit_age * 2.4)                                                   # knocked back
        gf = self.kg["Walk"] + int(min(f, self.strike * FPS) * 0.7 / self.kg["WalkStep"]) % self.kg["WalkFrames"]
        x, y = self.golem.place(gx, self.gy)
        v.put(hit_flash(self.golem.frame(gf), hit_age, 8), x, y)
        use = 26 / FPS * 1.6                                                               # the swing (a little slowed, to read)
        start = self.strike - use * 0.42
        done = (t - start) / use
        swinging = 0 <= done <= 1
        hand = put_player(v, px, self.gy, frame=2 if swinging and done < 0.5 else 4 if swinging else 0)
        shoulder = (px + 4, self.gy - 38)
        if swinging:
            ang = self.swing(done)
            blade = self.blade[int(f / 2) % 3]
            img, piv = rotated(blade, ang + math.pi / 4, (self.k["GripX"], self.k["FireGripY"]))
            if 0.24 <= done <= 0.62:                                                       # the phantom slash trail
                kf = min(5, int((done - 0.24) / 0.38 * 6))
                tr, tp = rotated(self.trail[kf], ang, (102, 124))
                v.add(tr, shoulder[0] - tp[0], shoulder[1] - tp[1], 0.6)
            v.put(img, shoulder[0] - piv[0], shoulder[1] - piv[1])
        if abs(hit_age) < 0.5:
            self.hits += [(self.n, gx - 10, self.gy - 96, 84, True), (self.n + 6, gx + 14, self.gy - 80, 42, False)]
            self.parts.burst(gx - 30, self.gy - 60, 34, [EMBER[3], EMBER[2], EMBER[1], EMBER[0]], speed=(1.5, 6.0), life=(14, 34), spread=(-1.2, 0.5))
            self.jolt(10, 4)
        if hit_age > 0 and int(f) % 2 == 0 and hit_age < 50:                                # it burns
            self.parts.burst(gx + random.Random(self.n).uniform(-20, 20), self.gy - 40, 1, [EMBER[3], EMBER[2], EMBER[1]], speed=(0.3, 1.2),
                             life=(12, 24), gravity=-0.08, spread=(-2.2, -0.9))
        return self.finish(v)


class CutterShot(Duel):
    label = ("DIAMOND CUTTER", "AN INSTANT BEAM THROUGH THREE ENEMIES")
    backdrop = "westworld"

    def __init__(self, dur, fire=0.28):
        super().__init__(dur)
        self.fire = fire
        self.bandit, self.kb = sheet_of("Content/OldBrassTown/NPCs/BrassBandit", "Content/OldBrassTown/NPCs/BrassBanditRigData.cs")
        self.gun = load("Content/Mechanist/Weapons/DiamondCutter.png")
        self.beam = strip("Content/Mechanist/Weapons/DiamondCutterBeam.png", 3)
        self.spark = strip("Content/Mechanist/Weapons/DiamondCutterSpark.png", 4)

    def frame(self, t):
        f = t * FPS
        v = self.view(dx=60)
        px = self.px0 + 40
        age = (t - self.fire) * FPS
        again = (t - self.fire - 0.42) * FPS
        hand = put_player(v, px, self.gy, frame=3)
        v.put(self.gun, hand[0] - 6, hand[1] - 14)
        muzzle = (hand[0] + 48, hand[1] - 2)
        xs = [self.px0 + 190, self.px0 + 262, self.px0 + 334]
        for k, ex in enumerate(xs):
            a = age if again < 0 else again
            x, y = self.bandit.place(ex + (max(0, age) * 0.4 if age > 0 else 0), self.gy)
            v.put(hit_flash(self.bandit.frame(self.kb["Aim"] + (k + int(f / 12)) % self.kb["AimFrames"]), a, 6), x, y)
        for a in (age, again):
            if 0 <= a < 12:
                bf = min(2, int(a / 4))
                length = xs[-1] + 30 - muzzle[0]
                for sx in range(0, int(length), 16):
                    v.add(self.beam[bf], muzzle[0] + sx, muzzle[1] - 3, 1.0 if bf < 2 else 0.6)
                sp = self.spark[min(3, int(a / 3))]
                for ex in [muzzle[0]] + xs:
                    v.add(sp, ex - 7, muzzle[1] - 7)
            if abs(a) < 0.5:
                self.hits += [(self.n + k * 2, ex, self.gy - 70 - k * 6, 19, False) for k, ex in enumerate(xs)]
                self.jolt(5, 2)
        return self.finish(v)


class YoyoShot(Duel):
    label = ("POSSESSED COG", "A YOYO THAT GRINDS STRAIGHT THROUGH")
    backdrop = "junkyard"
    tint = (255, 236, 226)

    def __init__(self, dur):
        super().__init__(dur)
        self.cog = strip("Content/BloodMoon/Projectiles/PossessedCogYoyo.png", 4)
        self.glow = strip("Content/BloodMoon/Projectiles/PossessedCogYoyo_Glow.png", 4)
        self.eye = strip("Content/BloodMoon/Projectiles/PossessedCogYoyo_Eye.png", 9)
        self.rust = vanilla_frames("Content/Junkyard/NPCs/RustCollector.png", 11)

    def frame(self, t):
        f = t * FPS
        v = self.view(dx=50)
        px = self.px0 + 50
        hand = put_player(v, px, self.gy, frame=3)
        u = t / self.dur
        yx = px + 40 + 250 * (0.5 - 0.5 * math.cos(u * math.tau * 1.0))                    # out through the line and back
        yy = self.gy - 26 + math.sin(u * math.tau * 2) * 6
        xs = [self.px0 + 170, self.px0 + 226, self.px0 + 282]
        d = v.draw()
        a, b = v.to_view(*hand), v.to_view(yx, yy)
        d.line([a, b], fill=(236, 122, 88, 255), width=1)
        for k, ex in enumerate(xs):
            near = abs(yx - ex) < 22
            fr = self.rust[int(f / 5 + k) % 8]
            v.put(tinted(fr, (255, 255, 255), 0.6) if near and int(f) % 4 < 2 else fr, ex - 20 + (2 if near and int(f) % 2 else 0), self.gy - 38)
            if near and int(f) % 8 == 0:                                                   # a cut every 8 ticks while it is inside
                self.hits.append((self.n, ex + random.Random(self.n).uniform(-8, 8), self.gy - 50, 17, False))
                self.parts.burst(ex, self.gy - 24, 5, [GHOST[5], GHOST[4], BRASS[4], BRASS[2]], speed=(1.0, 3.5), life=(10, 22))
        k = int(f / 3) % 4
        v.put(self.cog[k], yx - 13, yy - 13)
        v.add(self.glow[k], yx - 13, yy - 13)
        v.put(self.eye[1 if math.sin(u * math.tau) > 0 else 5], yx - 5, yy - 5)
        return self.finish(v)


class BarrelShot(Duel):
    label = ("BARREL GUN", "SHOOTS FISH. STUNS WHAT IT HITS")
    backdrop = "coghaven"

    def __init__(self, dur):
        super().__init__(dur)
        self.gun = load("Content/Mechanist/Weapons/BarrelGun.png")
        fish = load("Content/Mechanist/Weapons/BarrelGunFish.png")
        self.fish = [fish.crop((0, k * 18, 24, k * 18 + 16)) for k in range(6)]
        self.scorp, self.ks = sheet_of("Content/Coghaven/NPCs/Cogscorpion", "Content/Coghaven/NPCs/CogscorpionRigData.cs")
        self.shots = []                                                                    # [x, y, vx, vy, kind, born]
        self.stunned = -1

    def frame(self, t):
        f = int(t * FPS)
        v = self.view(dx=50)
        px = self.px0 + 40
        ex = self.px0 + 280
        hand = put_player(v, px, self.gy, frame=3)
        v.put(self.gun, hand[0] - 8, hand[1] - 16)
        if f % 12 == 2 and f < self.dur * FPS - 14:
            self.shots.append([hand[0] + 50, hand[1] - 4, 9.0, -2.2, len(self.shots) % 3, f])
        sf = self.ks["Walk"] if self.stunned >= 0 else self.ks["Walk"] + int(f / 6) % self.ks["WalkFrames"]
        x, y = self.scorp.place(ex, self.gy)
        v.put(hit_flash(self.scorp.frame(sf), f - self.stunned if self.stunned >= 0 else -1, 6), x, y)
        for s in self.shots:
            if s[0] is None:
                continue
            s[0] += s[2]
            s[1] += s[3]
            if f - s[5] > 10:
                s[3] = min(12.0, s[3] + 0.18)
            fr = self.fish[s[4] * 2 + (f // 6) % 2]
            v.put(mirror(fr), s[0] - 12, s[1] - 8)
            if s[0] > ex - 40:
                self.hits.append((self.n, ex - 20, self.gy - 60 - (len(self.hits) % 3) * 8, 20, False))
                self.parts.burst(s[0], s[1], 8, [(144, 168, 208), (96, 122, 172), STEAM[2]], speed=(1.0, 3.5), life=(10, 24))
                self.stunned = f
                self.jolt(4, 2)
                s[0] = None
        if self.stunned >= 0:                                                              # stars round its head
            for k in range(3):
                a = f * 0.2 + k * math.tau / 3
                sx, sy = v.to_view(ex - 30 + math.cos(a) * 16, self.gy - 62 + math.sin(a) * 5)
                v.draw().rectangle([int(sx) // 2 * 2, int(sy) // 2 * 2, int(sx) // 2 * 2 + 3, int(sy) // 2 * 2 + 3], fill=BRASS[5] + (255,))
        return self.finish(v)


class WrenchShot(Duel):
    label = ("METAL WRENCH", "PARRY. TIME SLOWS. STRIKE BACK")
    backdrop = "westworld"

    def __init__(self, dur, parry=0.36):
        super().__init__(dur)
        self.parry = parry
        self.sheriff, self.ks = sheet_of("Content/OldBrassTown/NPCs/Sheriff", "Content/OldBrassTown/NPCs/SheriffRigData.cs")
        self.wrench = load("Content/Junkyard/Weapons/MetalWrench.png")
        self.clash = strip("Content/Junkyard/Weapons/MetalClash.png", 6)
        self.star = strip("Content/OldBrassTown/Weapons/SheriffsBullet.png", 16) if False else None

    def frame(self, t):
        f = t * FPS
        slow = t > self.parry                                                              # the world at a fifth of its speed
        close = slow and t < self.parry + 0.42
        v = self.view(dx=30, dy=46 if close else 0, zoom=2 if close else 1)
        px = self.px0 + 110
        ex = self.px0 + 250
        age = (t - self.parry) * FPS
        hand = put_player(v, px, self.gy, frame=2 if age < 0 else 3)
        ang = -0.9 if age < 0 else lerp(-0.9, 0.5, ease_out(min(1.0, age / 22.0)))
        img, piv = rotated(self.wrench, ang, (10, 58))
        v.put(img, hand[0] - piv[0], hand[1] - piv[1])
        x, y = self.sheriff.place(ex, self.gy)
        sfr = self.ks["Shoot"] + min(self.ks["ShootFrames"] - 1, int(max(0, f - 6) / 5)) if age < 6 else self.ks["Aim"]
        v.put(hit_flash(self.sheriff.frame(sfr), age - 20, 8), x, y)
        if age < 0:                                                                        # his shot flying in
            bx = lerp(ex - 44, px + 20, f / (self.parry * FPS))
            d = v.draw()
            sx, sy = v.to_view(bx, self.gy - 44)
            d.rectangle([int(sx), int(sy), int(sx) + 7, int(sy) + 3], fill=BRASS[5] + (255,))
            d.rectangle([int(sx) + 8, int(sy) + 1, int(sx) + 16, int(sy) + 2], fill=EMBER[2] + (255,))
        elif age < 18 * 3:
            cf = min(5, int(age / 9))                                                      # the clash, in slow motion
            v.add(self.clash[cf], px + 22 - 32, self.gy - 46 - 32)
        if abs(age) < 0.5:
            self.parts.burst(px + 22, self.gy - 46, 26, [STEAM[3], BRASS[5], BRASS[4], EMBER[2]], speed=(1.0, 5.0), life=(20, 44), gravity=0.04)
            self.jolt(8, 3)
        if abs(age - 20) < 0.5:
            self.hits.append((self.n, ex - 10, self.gy - 84, 76, True))
        out = self.finish(v)
        if 0 <= age < 34:
            put_centered(out, text("PARRIED!", 20, "title", STEAM[3], STEAM[1], IRON[0]), W // 2 - 60, 84)
        return out


class JadeShot(Duel):
    label = ("JADE STAFF", "THREE STACKS OF ITS CURSE TURN A FOE TO JADE")
    backdrop = "ruins"

    def __init__(self, dur):
        super().__init__(dur)
        self.staff = load("Content/Gems/Items/JadeStaff.png")
        self.bolt = load("Content/Gems/Projectiles/JadeBolt.png")
        self.beetle, self.kb = sheet_of("Content/Jungle/NPCs/RhinoBeetle", "Content/Jungle/NPCs/RhinoBeetleRigData.cs")
        self.stacks = 0
        self.stone_at = -1

    def frame(self, t):
        f = int(t * FPS)
        v = self.view(dx=80)
        px = self.px0 + 60
        hand = put_player(v, px, self.gy, frame=3, armor="Brass")
        v.put(self.staff, hand[0] - 4, hand[1] - 34)
        tip = (hand[0] + 34, hand[1] - 30)
        charge_x = self.px0 + 380 - min(f, 34) * 5.0
        stone = self.stone_at >= 0
        bf = self.kb["Charge"] + (0 if stone else (f // 3) % self.kb["ChargeFrames"])
        ex = charge_x if not stone else self.px0 + 380 - 34 * 5.0
        x, y = self.beetle.place(ex, self.gy)
        fr = self.beetle.frame(bf)
        v.put(tinted(fr, (96, 214, 150), 0.62) if stone else fr, x, y)
        for k, born in enumerate((4, 14, 24)):                                             # three bolts, three stacks
            age = f - born
            if 0 <= age:
                bx = tip[0] + age * 11.0
                if bx < ex - 40:
                    v.add(self.bolt, bx - 7, tip[1] + (bx - tip[0]) * 0.1 - 7)
                elif self.stacks == k:
                    self.stacks += 1
                    self.parts.burst(ex - 40, self.gy - 30, 8, [GHOST[5], GHOST[4], GHOST[3], GHOST[2]], speed=(1.0, 3.0), life=(12, 26))
                    if self.stacks == 3:
                        self.stone_at = f
                        self.parts.burst(ex - 20, self.gy - 30, 30, [GHOST[5], GHOST[4], GHOST[3], GHOST[1]], speed=(1.0, 5.0), life=(18, 40))
                        self.jolt(8, 3)
        out = self.finish(v)
        if stone and f - self.stone_at < 40:
            put_centered(out, text("PETRIFIED", 18, "title", GHOST[5], GHOST[3], GHOST[0]), W // 2 + 80, 96)
        return out


class SkullShot(Duel):
    label = ("TAR BONE STAFF", "A HOMING SKULL THAT BURSTS IN TAR")
    backdrop = "junkyard"
    tint = (255, 236, 226)

    def __init__(self, dur, burst=0.5):
        super().__init__(dur)
        self.burst = burst
        self.staff = load("Content/Junkyard/Weapons/TarBoneStaff.png")
        self.bolt = strip("Content/Junkyard/Weapons/TyrantSkullBolt.png", 2)
        self.blast = strip("Content/Junkyard/Weapons/TyrantSkullBlast.png", 6)
        self.boom, self.kb = memo("boombot", lambda: (Sheet("Content/MechArmy/NPCs/Boombot", 56, 54, 28, 52), None))

    def frame(self, t):
        f = int(t * FPS)
        v = self.view(dx=70)
        px = self.px0 + 50
        hand = put_player(v, px, self.gy, frame=3, armor="Scrap")
        v.put(self.staff, hand[0] - 6, hand[1] - 38)
        xs = [self.px0 + 250, self.px0 + 300, self.px0 + 350]
        age = f - int(self.burst * FPS)
        for k, ex in enumerate(xs):
            push = min(40, max(0, age) * 3) * (1 if k else 0.6)
            x, y = self.boom.place(ex + push, self.gy - (max(0, 18 - abs(age - 8) * 2.4) if age > 0 else 0))
            v.put(hit_flash(self.boom.frame((f // 5 + k) % 6), age, 8), x, y)
        if age < 0:
            u = f / (self.burst * FPS)
            bx, by = lerp(hand[0] + 30, xs[0], u), self.gy - 60 + math.sin(u * math.pi) * -34 + u * 30
            v.put(mirror(self.bolt[(f // 4) % 2]), bx - 16, by - 18)
        elif age < 18:
            v.add(self.blast[min(5, age // 3)], xs[0] - 40, self.gy - 30 - 40)
        if age == 0:
            self.hits += [(self.n, xs[0], self.gy - 70, 33, False), (self.n + 3, xs[1], self.gy - 78, 16, False), (self.n + 5, xs[2], self.gy - 64, 16, False)]
            self.parts.burst(xs[0], self.gy - 30, 36, [(138, 90, 60), (91, 54, 38), (47, 27, 20), IRON[2]], speed=(1.5, 6.0), life=(16, 40))
            self.jolt(8, 4)
        return self.finish(v)


# --- the Combinator ------------------------------------------------------------------------------------------------------
def combine(aug, base, diagonal):
    """CombinedSprites.Build, line for line: the augment's first half and the base's second half glued on the 2 px grid
    (first half: left of the middle column, or below the anti-diagonal for sprites that point up-right)."""
    wa, ha = aug.size
    wb, hb = base.size
    even = lambda v: int(round(v / 2.0)) * 2                                               # noqa: E731
    dx, dy = even(wa / 2.0 - wb / 2.0), even(ha / 2.0 - hb / 2.0)
    min_x, min_y = min(0, dx), min(0, dy)
    w, h = max(wa, dx + wb) - min_x, max(ha, dy + hb) - min_y
    a_off, b_off = (-min_x, -min_y), (dx - min_x, dy - min_y)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pa, pb, po = aug.load(), base.load(), out.load()

    def first(x, y, ww, hh, split):
        x, y = x & ~1, y & ~1
        if not diagonal:
            return x < split
        return (x + 1.0) / ww + (hh - 1.0 - (y + 1.0)) / hh < 1.0
    sa, sb = even(wa / 2.0), even(wb / 2.0)
    for y in range(h):
        for x in range(w):
            ax, ay = x - a_off[0], y - a_off[1]
            if 0 <= ax < wa and 0 <= ay < ha and first(ax, ay, wa, ha, sa) and pa[ax, ay][3] > 0:
                po[x, y] = pa[ax, ay]
                continue
            bx, by = x - b_off[0], y - b_off[1]
            if 0 <= bx < wb and 0 <= by < hb and not first(bx, by, wb, hb, sb):
                po[x, y] = pb[bx, by]
    return out


class Combinator(Shot):
    """The Combinator: pairs of weapons fly together and fuse into the sprite the game itself would glue."""

    def __init__(self, dur, fuses=(1.04, 2.09), final=3.13):
        super().__init__(dur)
        self.fuses, self.final = fuses, final
        fs = strip("Content/Mechanist/Weapons/Firesaw.png", 1)[0]
        W_ = "Content/"
        pairs = [(fs, load(W_ + "Junkyard/Weapons/Macuahuitl.png"), True, "FIRE", "HUITL"),
                 (load(W_ + "Mechanist/Weapons/DiamondCutter.png"), load(W_ + "Mechanist/Weapons/BarrelGun.png"), False, "DIAMOND", "GUN"),
                 (load(W_ + "Gems/Items/JadeStaff.png"), load(W_ + "Junkyard/Weapons/TarBoneStaff.png"), True, "JADE", "STAFF")]
        self.pairs = [(a, b, combine(a, b, d), n1 + " " + n2 if d or True else n1) for (a, b, d, n1, n2) in pairs]
        sheet = load("Content/Combinator/Tiles/CombinatorTile.png")
        self.station = []
        for k in range(4):                                                                 # the station: 4 x 3 tiles, 4 frames
            im = Image.new("RGBA", (64, 48), (0, 0, 0, 0))
            for ty in range(3):
                for tx in range(4):
                    im.alpha_composite(sheet.crop((tx * 18, k * 56 + ty * 18, tx * 18 + 16, k * 56 + ty * 18 + 16)), (tx * 16, ty * 16))
            self.station.append(im)
        self.wall = load("Content/Coghaven/Walls/BronzeGearworkWallTile.png").crop((18 * 2 + 8, 36 + 8, 18 * 2 + 8 + 32, 36 + 8 + 32)) \
            if False else None
        self.parts = Particles(21)
        self.bg = self.backdrop()
        self.jolt_at = -99

    @staticmethod
    def backdrop():
        """A dark workshop wall: the Bronze Gearwork Wall's own texture tiled, deepened, a floor of Vault Gearwork."""
        wall = load("Content/Coghaven/Walls/VaultGearworkWallTile.png").crop((36 + 8, 36 + 8, 36 + 8 + 16, 36 + 8 + 16))
        floor = load("Content/Coghaven/Tiles/VaultGearworkTile.png").crop((18, 0, 34, 16))
        img = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 255))
        for y in range(0, H // 2, 16):
            for x in range(0, W // 2, 16):
                img.alpha_composite(wall if y < 128 else floor, (x, y))
        dark = S.darkened(img, 0.30)
        for r, k in ((150, 0.42), (112, 0.56), (78, 0.72)):                                 # the forge's light on the wall, in steps
            mask = Image.new("L", img.size, 0)
            ImageDraw.Draw(mask).ellipse([W // 4 - r, 70 - int(r * 0.62), W // 4 + r, 70 + int(r * 0.62)], fill=255)
            dark.paste(S.darkened(img, k), (0, 0), mask)
        return dark

    def shake(self, t):
        k = self.n - self.jolt_at
        return ((k % 2) * 4 * (1 if k % 4 < 2 else -1), 0) if 0 <= k < 8 else (0, 0)

    def frame(self, t):
        f = int(t * FPS)
        img = self.bg.copy()
        st = self.station[(f // 6) % 4]
        blit(img, st, W // 4 - 32, 128 - 48)
        times = list(self.fuses) + [self.final]
        idx = max([k for k, at in enumerate(times) if t >= at - 0.34] or [0])
        a, b, c, name = self.pairs[min(idx, len(self.pairs) - 1)]
        at = times[min(idx, len(times) - 1)]
        u = (t - (at - 0.34)) / 0.34
        cx, cy = W // 4, 54
        if u < 1.0:                                                                        # the two fly in from either side
            e = ease(max(0.0, u))
            blit(img, a, int(lerp(-a.width, cx - a.width // 2 - 6, e)), cy - a.height // 2)
            blit(img, b, int(lerp(W // 2, cx - b.width // 2 + 6, e)), cy - b.height // 2)
        else:
            age = (t - at) * FPS
            blit(img, hit_flash(c, age, 8), cx - c.width // 2, cy - c.height // 2 - (2 if age < 4 else 0))
            if abs(age) < 0.5:
                self.parts.burst(cx * 1.0, cy * 1.0, 40, [STEAM[3], BRASS[5], BRASS[4], EMBER[2], BRASS[2]], speed=(1.0, 5.0), life=(14, 36), size=1,
                                 gravity=0.05)
                self.jolt_at = self.n
        self.parts.step()
        d = ImageDraw.Draw(img)
        for x, y, vx, vy, life, life0, ramp, size, g, drag in self.parts.p:
            col = ramp[min(len(ramp) - 1, int((1 - life / life0) * len(ramp)))]
            d.point((int(x), int(y)), fill=tuple(col) + (255,))
        self.n += 1
        out = img.resize((W, H), Image.NEAREST)                                            # zoom 2
        if u >= 1.0 and idx == len(times) - 1:
            put_centered(out, text("ONE WEAPON. BOTH POWERS.", 14, "plate", STEAM[3], STEAM[1], IRON[0]), W // 2, 46)
        big_word(out, t - 0.05, "THE COMBINATOR", 30, y=H - BAR - 60, hold=self.dur - 0.1)
        return out


# --- bosses ----------------------------------------------------------------------------------------------------------------
class BossShot(Shot):
    card = ("", "")

    def finish_card(self, img, t):
        boss_card(img, t, self.dur, *self.card)
        return img

    def shake(self, t):
        f = int(t * FPS)
        return ((f % 2) * 4 - 2, ((f + 1) % 2) * 2) if getattr(self, "quake", (9, 9))[0] <= t < getattr(self, "quake", (9, 9))[1] else (0, 0)


class TrashTr0mShot(BossShot):
    card = ("TRASH-TR0M", "COLOSSUS OF THE SCRAPHEAP")
    quake = (0.0, 0.5)

    def __init__(self, dur):
        super().__init__(dur)
        self.plate, self.gy, self.cx = plates.junkyard()
        cwd = os.getcwd()
        os.chdir(S.ROOT)
        try:
            import trashtr0m_sim as tt
            self.tt = tt
            self.sheets = memo("tt_sheets", tt.Sheets)
        finally:
            os.chdir(cwd)
        self.parts = Particles(31)

    def frame(self, t):
        f = int(t * FPS)
        tt = self.tt
        x = self.cx + 330
        v = View(x - 60, self.gy - 110, zoom=1)
        v.plate(self.plate)
        body, arm = tt.resolve_pose("emerge", tt.K["RumbleTicks"] + tt.K["RiseTicks"] + f, f)[:2]
        rise = ease_out(min(1.0, t / 0.35))
        buried = int((1 - rise) * 150) // 2 * 2
        layer = Image.new("RGBA", (v.w, v.h), (0, 0, 0, 0))
        ax, ay = v.to_view(x, self.gy)
        tt.draw_boss(layer, self.sheets, body, arm, (ax, ay), buried=buried, flip=False, use_parallax=False)
        v.img.alpha_composite(layer)
        if f < 22 and f % 2 == 0:
            self.parts.burst(x + random.Random(f).uniform(-110, 110), self.gy - 4, 6, [(196, 104, 58), (147, 68, 31), (94, 40, 23), (42, 18, 12)],
                             speed=(2.0, 8.0), life=(20, 46), spread=(-2.6, -0.5), gravity=0.3)
        self.parts.step()
        self.parts.draw(v)
        return self.finish_card(v.out(), t)


class TarTyrantShot(BossShot):
    card = ("TAR TYRANT", "MONARCH OF THE MIRE")
    quake = (0.55, 0.95)

    def __init__(self, dur):
        super().__init__(dur)
        self.plate, self.gy = plates.tar_pool()
        cwd = os.getcwd()
        os.chdir(S.ROOT)
        try:
            import tartyrant_sim as ty
            self.ty = ty
        finally:
            os.chdir(cwd)
        self.parts = Particles(41)

    def frame(self, t):
        f = int(t * FPS)
        ty = self.ty
        x = 700
        v = View(x - 70, self.gy - 104, zoom=1)
        v.plate(self.plate)
        frame = ty.resolve("Emerge", int(f * 1.35))
        ax, ay = v.to_view(x, self.gy)
        cwd = os.getcwd()
        os.chdir(S.ROOT)
        try:
            ty.draw_boss(v.img, frame, ax, ay, False, v.w)
        finally:
            os.chdir(cwd)
        if f < 30 and f % 2 == 0:
            self.parts.burst(x + random.Random(f).uniform(-90, 90), self.gy, 5, [(79, 85, 98), (47, 27, 20), (91, 54, 38), (21, 22, 28)],
                             speed=(2.0, 7.0), life=(18, 40), spread=(-2.5, -0.6), gravity=0.3)
        self.parts.step()
        self.parts.draw(v)
        return self.finish_card(v.out(), t)


class ConductorShot(BossShot):
    card = ("THE CURSED CONDUCTOR", "THE LAST STOP")
    quake = (0.55, 1.0)

    def __init__(self, dur, train_at=0.55):
        super().__init__(dur)
        self.train_at = train_at
        self.plate, self.gy, _ = plates.westworld()
        box = self.plate.convert("L").point(lambda p: 255 if p > 90 else 0).getbbox()
        self.x = (box[0] + box[2]) // 2 + 80
        self.boss, self.k = sheet_of("Content/Bosses/CursedConductor/CursedConductor", "Content/Bosses/CursedConductor/CursedConductorRigData.cs")
        P = "Content/Bosses/CursedConductor/Projectiles/"
        heading = 4                                                                        # of 9: level (they face right)
        self.engine = strip(P + "GhostTrain.png", 9)[heading]
        self.engine_glow = strip(P + "GhostTrain_Glow.png", 9)[heading]
        self.car = strip(P + "GhostTrain_Car.png", 9)[heading]
        self.car_glow = strip(P + "GhostTrain_CarGlow.png", 9)[heading]

    def frame(self, t):
        f = int(t * FPS)
        age = t - self.train_at
        if age < 0:                                                                        # close on him first
            v = View(self.x + 110, self.gy - 104, zoom=2)
        else:
            v = View(self.x - 40, self.gy - 120, zoom=1)
        v.plate(self.plate)
        bob = (f // 20) % 2 * 2
        frame = self.k["Idle"] + (f // 8) % self.k["IdleFrames"] if t < self.train_at - 0.2 else self.k["Point"] + (f // 8) % self.k["PointFrames"]
        if age >= 0:                                                                       # the ghost train through the street, behind him
            tx = self.x + 420 - age * 18 * FPS
            y = self.gy - 146
            for k in range(10):
                cx = tx + 120 + k * 92
                v.put(mirror(self.car), cx, y + 12)
                v.add(mirror(self.car_glow), cx, y + 12, 0.8)
            v.put(mirror(self.engine), tx, y)
            v.add(mirror(self.engine_glow), tx, y, 0.9)
        v.sheet(self.boss, frame, self.x + 110, self.gy - 30 - bob)
        return self.finish_card(v.out(), t)


class JadeyShot(BossShot):
    card = ("JADEY", "A MOLDA-JADE")

    def __init__(self, dur, throw=0.62):
        super().__init__(dur)
        self.throw = throw
        self.cg = plates.coghaven()
        k = consts("Content/Coghaven/Generation/CoghavenBlueprints.cs")
        mid = (k["VaultLeft"] + k["VaultRight"]) // 2
        self.cx, self.floor = self.cg.px(k["MainHallX"] + mid, self.cg.isl.s + k["VaultFloor"])
        self.boss, self.k = sheet_of("Content/Bosses/Jadey/Jadey", "Content/Bosses/Jadey/JadeyRigData.cs")
        self.dart = strip("Content/Bosses/Jadey/Projectiles/JadeyRopeDart.png", 16)
        self.cord = load("Content/Bosses/Jadey/Projectiles/JadeyRopeDart_Cord.png")
        self.near = S.arrays("Content/Bosses/Jadey/JadeyRigData.cs")
        self.parts = Particles(51)

    def frame(self, t):
        self.cg.step()
        f = int(t * FPS)
        k = self.k
        x, y = self.cx + 70, self.floor - 70 - (f // 20) % 2 * 2
        tf = int(self.throw * FPS)
        v = View(x - 20, y - 50, zoom=2) if f < tf else View(self.cx - 10, self.floor - 104, zoom=1)
        self.cg.draw(v)
        if f < 8:
            fr = k["Whip"] + (0 if f < 4 else 1)
        elif f < tf:
            fr = k["Whip"] + 2 + (f // 3) % 2
        else:
            fr = k["Whip"] + 4
        v.sheet(self.boss, fr, x, y)
        paw = (x + self.near["NearX"][fr], y + self.near["NearY"][fr])
        if 8 <= f < tf:                                                                    # the rope dart whirling round her paw
            a = f * 0.7
            bx, by = paw[0] + math.cos(a) * 18, paw[1] + math.sin(a) * 18 * 0.45
            self.cord_to(v, paw, (bx, by))
            hd = int(round(math.atan2(math.cos(a) * 0.45, -math.sin(a)) / (math.tau / 16))) % 16
            v.put(self.dart[hd], bx - 13, by - 13)
        elif f >= tf:                                                                      # thrown: fast, to the floor
            u = min(1.0, (f - tf) * 20.0 / 250.0)
            end = (paw[0] - 230, self.floor - 8)
            bx, by = lerp(paw[0], end[0], u), lerp(paw[1], end[1], u)
            self.cord_to(v, paw, (bx, by))
            hd = int(round(math.atan2(end[1] - paw[1], end[0] - paw[0]) / (math.tau / 16))) % 16
            v.put(self.dart[hd], bx - 13, by - 13)
            if u >= 1.0 and not getattr(self, "bit", False):
                self.bit = True
                self.parts.burst(end[0], end[1], 26, [GHOST[5], GHOST[4], GHOST[3], GHOST[1]], speed=(1.0, 5.0), life=(16, 40), spread=(-2.8, -0.3))
            if u >= 1.0:                                                                   # the three cursed tiles
                d = v.draw()
                sx, sy = v.to_view(end[0] - 24, self.floor - 2)
                for i in range(0, 48, 2):
                    d.rectangle([sx + i, sy - (2 if (i + f // 6) % 10 == 0 else 0), sx + i + 1, sy + 1], fill=GHOST[4 if (i // 2 + f // 6) % 5 else 5] + (255,))
        self.parts.step()
        self.parts.draw(v)
        return self.finish_card(v.out(), t)

    def cord_to(self, v, a, b):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 4)
        for i in range(1, n):
            u = i / n
            v.put(self.cord, int(lerp(a[0], b[0], u)) // 2 * 2, int(lerp(a[1], b[1], u)) // 2 * 2)

    def shake(self, t):
        return (0, 0)


class MechromancerShot(BossShot):
    card = ("THE MECHROMANCER", "IT COMES WITH THE BLOOD MOON")

    def __init__(self, dur):
        super().__init__(dur)
        self.boss, self.k = sheet_of("Content/BloodMoon/NPCs/Mechromancer", "Content/BloodMoon/NPCs/MechromancerRigData.cs")
        self.eye = strip("Content/BloodMoon/NPCs/Mechromancer_Eye.png", 9)
        self.eye_glow = strip("Content/BloodMoon/NPCs/Mechromancer_EyeGlow.png", 9)
        self.grave = strip("Content/BloodMoon/Projectiles/MechromancerGrave.png", 4, gap=0)
        self.grave_glow = strip("Content/BloodMoon/Projectiles/MechromancerGrave_Glow.png", 4, gap=0)
        self.parts = Particles(71)
        self.cog = strip("Content/BloodMoon/Projectiles/SoulFireCog.png", 4, gap=0)
        self.cog_glow = strip("Content/BloodMoon/Projectiles/SoulFireCog_Glow.png", 4, gap=0)
        self.bg = self.blood_moon()
        self.gy = 300

    @staticmethod
    def blood_moon():
        img = plates.dusk_sky(W, H, top=(20, 6, 14), mid=(96, 16, 26), low=(150, 34, 34), horizon=0.84)
        d = ImageDraw.Draw(img)
        d.ellipse([340, 166, 430, 256], fill=(206, 74, 56, 255))
        d.ellipse([358, 184, 378, 204], fill=(168, 44, 42, 255))
        d.ellipse([392, 218, 404, 230], fill=(168, 44, 42, 255))
        d.ellipse([398, 186, 406, 194], fill=(168, 44, 42, 255))
        rng = random.Random(2)
        for k in range(6):
            cx = rng.randrange(0, W)
            hw, hh = rng.randrange(70, 160), rng.randrange(14, 40)
            d.polygon([(cx - hw, 300), (cx - hw // 3, 300 - hh), (cx + hw // 3, 300 - hh + 8), (cx + hw, 300)], fill=(34, 10, 18, 255))
        d.rectangle([0, 300, W, H], fill=(24, 8, 14, 255))
        d.line([0, 300, W, 300], fill=(84, 20, 28, 255), width=2)
        return img

    def frame(self, t):
        f = int(t * FPS)
        k = self.k
        x, y = 260, self.gy - 4 - (f // 20) % 2 * 2
        v = View(x + 50, 269, zoom=2, bg=(0, 0, 0, 255))
        v.plate(self.bg)
        st = f - 6
        if st < 0:
            fr = k["Float"] + (f // 8) % k["FloatFrames"]
        elif st < 10:
            fr = k["Summon"]
        elif st < 20:
            fr = k["Summon"] + 1
        elif st < 70:
            fr = k["Summon"] + 2 + (st // 6) % 2
        else:
            fr = k["Summon"] + 4
        head = (x + k["HeadX"], y + k["HeadY"])

        def eyes(front):
            for i in range(5):
                a = f / 90.0 * math.tau + i * math.tau / 5
                depth = math.sin(a)
                if (depth > 0) != front:
                    continue
                ex, ey = head[0] + math.cos(a) * 34, head[1] + depth * 10 + ((f // 14 + i) % 2) * 2
                v.put(self.eye[1], int(ex - 7) // 2 * 2, int(ey - 7) // 2 * 2)
                v.add(self.eye_glow[1], int(ex - 7) // 2 * 2, int(ey - 7) // 2 * 2, 0.9)
        eyes(False)
        v.sheet(self.boss, fr, x, y)
        eyes(True)
        for i, gx in enumerate((336, 378, 420)):                                           # graves burning into the ground
            if st > 22 + i * 8:
                g = self.grave[(f // 5 + i) % 4]
                v.put(g, gx - 22, self.gy - 18)
                v.add(self.grave_glow[(f // 5 + i) % 4], gx - 22, self.gy - 18, 0.9)
                if st == 23 + i * 8:
                    self.parts.burst(gx, self.gy - 6, 14, [GHOST[5], GHOST[4], GHOST[3], GHOST[1]], speed=(0.6, 3.0), life=(14, 34), spread=(-2.7, -0.4))
        self.parts.step()
        self.parts.draw(v)
        return self.finish_card(v.out(), t)


class Flashes(Shot):
    """A burst of faces on the last accents before the logo: one enemy every few frames, huge."""

    def __init__(self, dur):
        super().__init__(dur)
        G = "Content/"
        golem, kg = sheet_of(G + "Coghaven/NPCs/JadeGolem", G + "Coghaven/NPCs/JadeGolemRigData.cs")
        head, kh = sheet_of(G + "Coghaven/NPCs/FlyingBuddhaHead", G + "Coghaven/NPCs/FlyingBuddhaHeadRigData.cs")
        scorp, ks = sheet_of(G + "Coghaven/NPCs/Cogscorpion", G + "Coghaven/NPCs/CogscorpionRigData.cs")
        beetle, kb = sheet_of(G + "Jungle/NPCs/RhinoBeetle", G + "Jungle/NPCs/RhinoBeetleRigData.cs")
        bull, ku = sheet_of(G + "OldBrassTown/NPCs/MechanicalBull", G + "OldBrassTown/NPCs/MechanicalBullRigData.cs")
        jbeetle = Sheet(G + "Bosses/Jadey/NPCs/JadeBeetle", kb["CellWidth"], kb["CellHeight"], kb["OriginX"], kb["OriginY"])
        self.items = [(golem.frame(kg["Idle"]), (24, 60, 50)), (head.frame(kh["Wrath"] + 2), (70, 44, 16)), (scorp.frame(ks["Strike"]), (60, 16, 22)),
                      (beetle.frame(kb["Charge"]), (22, 46, 26)), (bull.frame(ku["Charge"]), (64, 34, 14)), (jbeetle.frame(kb["Brace"]), (16, 50, 44))]

    def frame(self, t):
        k = min(len(self.items) - 1, int(t / self.dur * len(self.items)))
        spr, col = self.items[k]
        img = Image.new("RGBA", (W // 2, H // 2), col + (255,))
        d = ImageDraw.Draw(img)
        for i in range(-H, W, 22):                                                         # speed lines
            d.polygon([(i, H // 2), (i + 8, H // 2), (i + 8 + H // 2, 0), (i + H // 2, 0)], fill=tuple(min(255, c + 22) for c in col) + (255,))
        box = spr.getbbox() or (0, 0, 1, 1)
        s = spr.crop(box)
        if s.height * 2 <= 150:                                                            # the small ones twice the size
            s = s.resize((s.width * 2, s.height * 2), Image.NEAREST)
        blit(img, s, W // 4 - s.width // 2, H // 4 - s.height // 2)
        return img.resize((W, H), Image.NEAREST)


class LogoCard(Shot):
    """The end card: the logo slammed on (composited at 1080p by the main loop), the island's own smoke rising behind it,
    the lines under it."""

    def __init__(self, dur, lines):
        super().__init__(dur)
        self.lines = lines
        sheet = plates.coghaven().r.smoke
        self.puffs = [S.darkened(sheet.crop((0, k * 20, 20, k * 20 + 20)).resize((40, 40), Image.NEAREST), 0.42) for k in range(4)]
        self.smoke = []                                                                    # [x, y, age, drift]
        self.rng = random.Random(61)

    def frame(self, t):
        f = int(t * FPS)
        img = Image.new("RGBA", (W, H), (12, 10, 14, 255))
        d = ImageDraw.Draw(img)
        for r, col in ((230, (22, 17, 20)), (170, (32, 23, 23)), (110, (44, 30, 26))):       # a stepped glow behind the logo
            d.ellipse([W // 2 - r * 1.5, 150 - r * 0.62, W // 2 + r * 1.5, 150 + r * 0.62], fill=col + (255,))
        if f % 5 == 0:
            self.smoke.append([W // 2 + self.rng.uniform(-200, 200), 84.0, 0, self.rng.uniform(-0.25, 0.25)])
        for p in self.smoke:
            p[0] += p[3]
            p[1] -= 0.7
            p[2] += 1
            k = 0 if p[2] < 14 else 1 if p[2] < 40 else 2 if p[2] < 80 else 3
            blit(img, faded(self.puffs[k], 0.8 * max(0.0, 1 - p[2] / 130.0)), int(p[0]) // 2 * 2 - 20, int(p[1]) // 2 * 2 - 20)
        self.smoke = [p for p in self.smoke if p[2] < 130]
        for (at, s, size, y, kind) in self.lines:
            if t >= at:
                tt = text(s, size, kind) if kind == "title" else text(s, size, kind, STEAM[3], STEAM[1], IRON[0])
                put_centered(img, faded(tt, min(1.0, (t - at) / 0.2)), W // 2, y + (0 if t - at > 0.07 else 3))
        return img


# ================================================================================================
# The cut (seconds; every value is a measured accent of the track)
# ================================================================================================
END = 61.0
LOGO_AT = 56.96


def timeline():
    """[(start, end, make shot, accent)]: accent 0..1 scales the cut's flash and chroma split."""
    T = []

    def add(a, b, make, accent=0.5):
        T.append((a, b, make, accent))
    add(0.00, 2.30, lambda d: CogMacro(d, "BRASS."), 0.0)
    add(2.30, 5.48, lambda d: TurbineMacro(d, "STEAM."), 0.4)
    add(5.48, 7.59, lambda d: HallMacro(d, "CLOCKWORK."), 0.5)
    add(7.59, 8.82, lambda d: StoneMacro(d), 0.5)
    add(8.82, 12.01, lambda d: Black(d, ((0.0, "A NEW AGE OF STEAM", 26, 160), (1.95, "COMES TO TERRARIA", 34, 200))), 0.3)
    add(12.01, 16.05, lambda d: Junkyard(d), 1.0)
    add(16.05, 20.09, lambda d: Westworld(d), 0.8)
    add(20.09, 24.47, lambda d: CoghavenWide(d), 0.8)
    add(24.47, 29.02, lambda d: Ruins(d), 0.6)
    add(29.02, 32.88, lambda d: Mechanist(d), 0.9)
    add(32.88, 34.97, lambda d: FiresawShot(d), 1.0)
    add(34.97, 36.01, lambda d: CutterShot(d), 0.7)
    add(36.01, 37.08, lambda d: YoyoShot(d), 0.7)
    add(37.08, 38.13, lambda d: BarrelShot(d), 0.7)
    add(38.13, 39.17, lambda d: WrenchShot(d), 0.7)
    add(39.17, 40.22, lambda d: JadeShot(d), 0.7)
    add(40.22, 41.26, lambda d: SkullShot(d), 0.7)
    add(41.26, 45.47, lambda d: Combinator(d), 0.9)
    add(45.47, 47.55, lambda d: TrashTr0mShot(d), 1.0)
    add(47.55, 49.64, lambda d: TarTyrantShot(d), 1.0)
    add(49.64, 51.73, lambda d: ConductorShot(d), 1.0)
    add(51.73, 53.82, lambda d: JadeyShot(d), 1.0)
    add(53.82, 55.91, lambda d: MechromancerShot(d), 1.0)
    add(55.91, LOGO_AT, lambda d: Flashes(d), 0.6)
    add(LOGO_AT, END, lambda d: LogoCard(d, ((1.04, "A STEAMPUNK MOD FOR TERRARIA", 15, 258, "plate"), (2.09, "COMING SOON", 28, 290, "title"),
                                              (1.57, "MUSIC BY ERICK JUAN", 12, 326, "plate"))), 1.0)
    return T


class Teaser:
    def __init__(self, logo_path):
        self.T = timeline()
        self.k = -1
        self.shot = None
        logo = Image.open(logo_path).convert("RGBA")
        lw = 1380
        self.logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
        self.logo_big = {}
        # the notice (user, 2026-11-17: "add in the teaser trailer a small tooltip that notifies that is an in engine
        # simulation and not in game footage"): pixel text, shown 3x like the stage, in the bottom bar the whole time
        note = text(NOTICE, 9, "plate", STEAM[2], STEAM[0], IRON[0])
        self.notice = note.resize((note.width * S.SCALE, note.height * S.SCALE), Image.NEAREST)

    def seek(self, t):
        for k, (a, b, make, accent) in enumerate(self.T):
            if a <= t < b:
                if k != self.k:
                    self.k = k
                    self.shot = make(b - a)
                return a, b, accent
        return None

    def frame(self, t):
        """The finished 1080p RGB frame at time t (call with increasing t)."""
        got = self.seek(t)
        if got is None:
            return np.zeros((HD_H, HD_W, 3), np.uint8)
        a, b, accent = got
        lt = t - a
        img = self.shot.frame(lt)
        if self.shot.label:
            lower_third(img, lt, b - a, *self.shot.label)
        since = lt * FPS
        flash = accent * 0.85 * max(0.0, 1 - since / 5.0) if a > 0 else 0.0
        chroma = int(round(accent * 3 * max(0.0, 1 - since / 4.0))) if a > 0 else 0
        fade = min(1.0, t / 0.6) * min(1.0, max(0.0, (END - t) / 0.9))
        if isinstance(self.shot, LogoCard):
            flash = max(flash, 1.0 - since / 9.0)
        arr = S.post(img, flash=flash, fade=fade, shake=self.shot.shake(lt), chroma=chroma, tint=self.shot.tint,
                     vig=0.5 if not isinstance(self.shot, (Black, LogoCard)) else 0.25)
        if not isinstance(self.shot, LogoCard):
            arr[:BAR] = 0                                                                  # the letterbox
            arr[H - BAR:] = 0
        frame = S.upscale(arr)
        if isinstance(self.shot, LogoCard):                                                # the logo, at 1080p
            s = 1.0 + 0.5 * max(0.0, 1 - since / 7.0) ** 2
            if s > 1.001:
                key = round(s, 2)
                if key not in self.logo_big:
                    self.logo_big[key] = self.logo.resize((int(self.logo.width * key), int(self.logo.height * key)), Image.BILINEAR)
                lg = self.logo_big[key]
            else:
                lg = self.logo
            alpha = min(1.0, since / 3.0) * min(1.0, max(0.0, (END - t) / 0.9))
            S.hd_overlay(frame, lg, HD_W // 2 - lg.width // 2, 440 - lg.height // 2, alpha)
        fade = min(1.0, t / 0.6) * min(1.0, max(0.0, (END - t) / 0.9))
        S.hd_overlay(frame, self.notice, HD_W - self.notice.width - 30, HD_H - BAR * S.SCALE // 2 - self.notice.height // 2,
                     NOTICE_ALPHA * fade)
        return frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--music")
    ap.add_argument("--out", default="docs/media/promo/cogpunk-teaser.mp4")
    ap.add_argument("--logo", default="docs/media/promo/Cogpunk-logo.png")
    ap.add_argument("--ffmpeg")
    ap.add_argument("--encoder")
    ap.add_argument("--bitrate", default="16M", help="the average bitrate for encoders without a constant-quality mode here")
    ap.add_argument("--venc", default="", help="extra encoder options, e.g. \"-preset p7 -tune hq\"")
    ap.add_argument("--stills")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--contact")
    ap.add_argument("--only", help="a,b: render only this span of seconds (review)")
    args = ap.parse_args()
    os.chdir(S.ROOT)
    teaser = Teaser(args.logo)
    if args.stills or args.contact:
        if args.contact:
            times = [a + min(b - a - 0.05, max(0.35, (b - a) * 0.55)) for (a, b, _, _) in teaser.T]
        else:
            times = sorted(float(x) for x in args.stills.split(","))
        shots = []
        last, t, frame = None, 0.0, None
        for want in times:
            got = [x for x in teaser.T if x[0] <= want < x[1]][0]
            if got is not last or t > want + 1e-6:                                         # a new shot: play it from its start
                teaser.k, t, last = -1, got[0], got
            while t <= want + 1e-6:
                frame = teaser.frame(t)
                t += 1.0 / FPS
            im = Image.fromarray(frame)
            if args.contact:
                im = im.resize((480, 270), Image.BILINEAR)
                ImageDraw.Draw(im).text((4, 4), "%.2f s" % want, fill=(255, 255, 0))
                shots.append(im)
            else:
                path = os.path.join(args.out_dir, "still_%06.2f.png" % want)
                im.save(path)
                print("wrote", path)
        if args.contact:
            cols = 5
            rows = (len(shots) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * 480, rows * 270))
            for i, im in enumerate(shots):
                sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
            sheet.save(args.contact)
            print("wrote", args.contact)
        return
    if not args.music:
        raise SystemExit("--music PATH is required to render the teaser")
    start, end = 0.0, END
    if args.only:
        start, end = (float(x) for x in args.only.split(","))
    ffmpeg = S.find_ffmpeg(args.ffmpeg)
    os.makedirs(os.path.dirname(os.path.join(S.ROOT, args.out)), exist_ok=True)
    enc = S.Encoder(ffmpeg, os.path.join(S.ROOT, args.out), music=args.music, music_start=start, duration=end - start, encoder=args.encoder, bitrate=args.bitrate, extra=args.venc.split(),
                    audio_fade=1.6 if end >= END else 0.05)
    n = int(round((end - start) * FPS))
    t0 = time.time()
    first = [x for x in teaser.T if x[0] <= start < x[1]][0][0]
    t = first
    while t < start - 1e-6:                                                                # warm the shot up to the span's start
        teaser.frame(t)
        t += 1.0 / FPS
    for i in range(n):
        enc.write(teaser.frame(start + i / FPS))
        if i % 300 == 0:
            print("frame %d / %d  (%.0f s)" % (i, n, time.time() - t0), flush=True)
    code = enc.close()
    print("encoded with %s -> %s (exit %d, %.0f s)" % (enc.enc, args.out, code, time.time() - t0))


if __name__ == "__main__":
    main()
