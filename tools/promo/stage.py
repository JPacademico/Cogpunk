"""The stage of Cogpunk's teaser (tools/promo/make_teaser.py): a tiny pixel-perfect compositor.

Everything is drawn in game pixels (the sprites' own 2x art) on a 640x360 stage, through a camera whose zoom is 0.5, 1 or
2 only (0.5 drops every other pixel of the doubled art: exact 1x art; never a fractional scale), then shown at 3x:
1920x1080 with every art pixel a clean 3 or 6 px square. Nothing is rotated or blurred except where the game itself
rotates (swung weapons) and for the HD overlays (the logo), which are composited at 1080p.

Helpers: cached image loading, the generated *RigData.cs constants and tables (read with the sims' regexes), layered grid
sheets (far / middle / near / glow, DepthLayers.DrawCell's layout), a clipped blit, a View (camera), pixel text with a
brass gradient, numpy post effects (flash, fade, shake, chroma split, vignette), and the ffmpeg encoder pipe.
"""
import functools
import glob
import math
import os
import re
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H, SCALE, FPS = 640, 360, 3, 60
HD_W, HD_H = W * SCALE, H * SCALE

# the Cogpunk palette's ramps used for titles and effects (art/palettes/cogpunk.gpl)
BRASS = [(43, 26, 14), (90, 58, 23), (138, 93, 34), (184, 138, 51), (223, 185, 78), (246, 231, 161)]
GILT_TOP = (255, 250, 222)
STEAM = [(138, 144, 150), (195, 200, 205), (238, 241, 243), (255, 255, 255)]
EMBER = [(77, 20, 10), (163, 48, 26), (236, 113, 40), (255, 199, 90)]
GHOST = [(10, 34, 32), (18, 70, 58), (30, 114, 88), (58, 166, 118), (118, 220, 162), (196, 250, 214)]
IRON = [(21, 22, 28), (46, 50, 59), (79, 85, 98), (127, 135, 148), (183, 191, 202)]
CRIMSON = [(44, 12, 18), (84, 20, 28), (126, 30, 36), (168, 44, 42), (206, 74, 56), (236, 122, 88)]
INK = (14, 12, 16)


# ================================================================================================
# Assets
# ================================================================================================
@functools.lru_cache(maxsize=None)
def load(rel):
    return Image.open(os.path.join(ROOT, rel)).convert("RGBA")


def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))


def consts(*rels):
    """`const int/float/double NAME = value;` (and comma lists) from C# files (the sims' reader)."""
    out = {}
    for rel in rels:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for m in re.finditer(r"const (?:int|float|double) ([^;]+);", src):
            for part in m.group(1).split(","):
                if "=" in part:
                    k, v = (x.strip() for x in part.split("=", 1))
                    v = re.sub(r"(\d+(?:\.\d+)?)f\b", r"\1", v)
                    v = re.sub(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\b", r"\1", v)
                    try:
                        out[k] = eval(v, {}, dict(out))
                    except Exception:
                        pass
    return out


def arrays(rel):
    """`static readonly int[]/short[]/sbyte[] Name = { ... };` tables from a generated RigData file."""
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"static readonly (?:int|short|sbyte|byte)\[\] (\w+) = \{([^}]*)\};", src):
        out[m.group(1)] = [int(v) for v in m.group(2).replace("\n", " ").split(",") if v.strip()]
    return out


def blit(dst, src, x, y):
    """Alpha-composites src onto dst at (x, y), clipped to dst (PIL refuses negative destinations)."""
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if sx0 or sy0 or sx1 < src.width or sy1 < src.height:
        src = src.crop((sx0, sy0, sx1, sy1))
    dst.alpha_composite(src, (x + sx0, y + sy0))


def blit_add(dst, src, x, y, strength=1.0):
    """Adds src's light onto dst (the game's additive glows): dst.rgb += src.rgb * src.a * strength, clipped."""
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    s = np.asarray(src.crop((sx0, sy0, sx1, sy1)), dtype=np.float32)
    box = (x + sx0, y + sy0, x + sx1, y + sy1)
    d = np.asarray(dst.crop(box), dtype=np.float32)
    d[..., :3] = np.minimum(255.0, d[..., :3] + s[..., :3] * (s[..., 3:4] / 255.0) * strength)
    d[..., 3] = np.maximum(d[..., 3], s[..., 3] * min(1.0, strength))
    dst.paste(Image.fromarray(d.astype(np.uint8), "RGBA"), box)


_mirrors = {}


def mirror(img):
    """The image flipped left-right, cached by identity (the source is kept alive so its id is never reused)."""
    got = _mirrors.get(id(img))
    if got is None or got[0] is not img:
        if len(_mirrors) > 4096:
            _mirrors.clear()
        got = _mirrors[id(img)] = (img, img.transpose(Image.FLIP_LEFT_RIGHT))
    return got[1]


def tinted(img, rgb, amount=1.0):
    """The image's shape filled with a colour (hit flashes, silhouettes), blended by amount."""
    solid = Image.new("RGBA", img.size, tuple(rgb) + (0,))
    solid.putalpha(img.getchannel("A"))
    return Image.blend(img, solid, amount) if amount < 1.0 else solid


def faded(img, alpha):
    if alpha >= 1.0:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * max(0.0, alpha))))
    return out


def darkened(img, k):
    r, g, b, a = img.split()
    return Image.merge("RGBA", [ch.point(lambda v: int(v * k)) for ch in (r, g, b)] + [a])


class Sheet:
    """A layered grid sheet set as DepthLayers.DrawCell reads it: `base`.png (the middle plane) with optional `_Far`,
    `_Near` and `_Glow` twins, equal cells `cw` x `ch` in `cols` columns, `pad` px between them, the rig origin at
    (ox, oy) in each cell. frame(i) is the planes stacked (far a step darker), cached."""

    def __init__(self, base, cw, ch, ox, oy, cols=1, pad=2, far="_Far", near="_Near", glow="_Glow"):
        self.base, self.cw, self.ch, self.ox, self.oy, self.cols, self.pad = base, cw, ch, ox, oy, cols, pad
        self.mid = load(base + ".png")
        self.far = load(base + far + ".png") if far and exists(base + far + ".png") else None
        self.near = load(base + near + ".png") if near and exists(base + near + ".png") else None
        self.glow = load(base + glow + ".png") if glow and exists(base + glow + ".png") else None
        self._cache = {}

    def cell(self, img, i):
        x, y = (i % self.cols) * (self.cw + self.pad), (i // self.cols) * (self.ch + self.pad)
        return img.crop((x, y, x + self.cw, y + self.ch))

    def frame(self, i, flip=False, far_i=None, glow=1.0):
        key = (i, flip, far_i, glow)
        if key not in self._cache:
            out = Image.new("RGBA", (self.cw, self.ch), (0, 0, 0, 0))
            if self.far is not None:
                out.alpha_composite(darkened(self.cell(self.far, i if far_i is None else far_i), 0.88))
            out.alpha_composite(self.cell(self.mid, i))
            if self.near is not None:
                out.alpha_composite(self.cell(self.near, i))
            if self.glow is not None and glow > 0:
                out.alpha_composite(faded(self.cell(self.glow, i), glow))
            self._cache[key] = out.transpose(Image.FLIP_LEFT_RIGHT) if flip else out
        return self._cache[key]

    def place(self, x, y, flip=False):
        """The top-left of a frame whose rig origin stands at world (x, y)."""
        return (x - (self.cw - self.ox) if flip else x - self.ox, y - self.oy)


def strip(rel, n, gap=2, horizontal=False):
    """A vertical (or horizontal) strip of n equal frames with `gap` px between them -> a list of images."""
    img = load(rel)
    if horizontal:
        w = (img.width + gap) // n - gap
        return [img.crop((k * (w + gap), 0, k * (w + gap) + w, img.height)) for k in range(n)]
    h = (img.height + gap) // n - gap
    return [img.crop((0, k * (h + gap), img.width, k * (h + gap) + h)) for k in range(n)]


def vanilla_frames(rel, n):
    """A vanilla-layout NPC or projectile sheet: n equal frames stacked with no gap."""
    img = load(rel)
    h = img.height // n
    return [img.crop((0, k * h, img.width, (k + 1) * h)) for k in range(n)]


# ================================================================================================
# The camera
# ================================================================================================
class View:
    """One frame's camera: world px (cx, cy) at the middle of the stage, zoom 0.5, 1 or 2. Draw in world coordinates;
    out() gives the 640x360 stage image."""

    def __init__(self, cx, cy, zoom=1.0, bg=(0, 0, 0, 255)):
        self.zoom = zoom
        self.w, self.h = int(round(W / zoom)), int(round(H / zoom))
        step = 2 if zoom < 1 else 1                      # at 0.5 the camera moves in whole art pixels
        self.x0 = int(round((cx - self.w / 2) / step)) * step
        self.y0 = int(round((cy - self.h / 2) / step)) * step
        self.img = Image.new("RGBA", (self.w, self.h), bg)

    def plate(self, plate, px=0, py=0):
        """A big backdrop whose top-left is at world (px, py)."""
        box = (self.x0 - px, self.y0 - py, self.x0 - px + self.w, self.y0 - py + self.h)
        sx0, sy0 = max(0, box[0]), max(0, box[1])
        sx1, sy1 = min(plate.width, box[2]), min(plate.height, box[3])
        if sx1 > sx0 and sy1 > sy0:
            self.img.alpha_composite(plate.crop((sx0, sy0, sx1, sy1)), (sx0 - box[0], sy0 - box[1]))

    def put(self, sprite, wx, wy):
        blit(self.img, sprite, wx - self.x0, wy - self.y0)

    def add(self, sprite, wx, wy, strength=1.0):
        blit_add(self.img, sprite, wx - self.x0, wy - self.y0, strength)

    def sheet(self, sheet, i, wx, wy, flip=False, **kw):
        x, y = sheet.place(wx, wy, flip)
        self.put(sheet.frame(i, flip, **kw), x, y)

    def draw(self):
        return ImageDraw.Draw(self.img)

    def to_view(self, wx, wy):
        return wx - self.x0, wy - self.y0

    def out(self):
        if self.zoom == 1:
            return self.img
        return self.img.resize((W, H), Image.NEAREST)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


# ================================================================================================
# Pixel text
# ================================================================================================
FONT_FILES = {"title": ("ROCKB.TTF", "georgiab.ttf", "arialbd.ttf"), "plate": ("COPRGTB.TTF", "arialbd.ttf"),
              "plain": ("arialbd.ttf",)}


@functools.lru_cache(maxsize=None)
def font(kind, size):
    for name in FONT_FILES[kind]:
        path = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


@functools.lru_cache(maxsize=512)
def text(s, size=22, kind="title", top=BRASS[5], bottom=BRASS[3], outline=BRASS[0], shadow=True, track=0):
    """Pixel text (no antialiasing): a vertical two-colour gradient, a 1 px outline in the ramp's darkest shade and a drop
    shadow, like the game's brass banners. Returns an RGBA image."""
    ft = font(kind, size)
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    probe.fontmode = "1"
    widths = [probe.textlength(ch, font=ft) for ch in s]
    w = int(sum(widths) + track * max(0, len(s) - 1)) + 8
    bb = probe.textbbox((0, 0), s or " ", font=ft)
    h = bb[3] + 8
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    x = 3.0
    for ch, cw in zip(s, widths):
        d.text((int(round(x)), 3), ch, font=ft, fill=255)
        x += cw + track
    box = mask.getbbox() or (0, 0, 1, 1)
    grad = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(grad)
    y0, y1 = box[1], box[3]
    for y in range(h):
        f = 0.0 if y1 <= y0 else max(0.0, min(1.0, (y - y0) / (y1 - y0 - 1 or 1)))
        f = 0.0 if f < 0.45 else 1.0 if f > 0.75 else (f - 0.45) / 0.3      # a hard band, not a smooth gradient
        gd.line([0, y, w, y], fill=tuple(int(lerp(a, b, f)) for a, b in zip(top, bottom)) + (255,))
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    fat = mask.filter(ImageFilter.MaxFilter(3))
    if shadow:
        out.paste(Image.new("RGBA", (w, h), INK + (255,)), (2, 2), fat)
    out.paste(Image.new("RGBA", (w, h), tuple(outline) + (255,)), (0, 0), fat)
    out.paste(grad, (0, 0), mask)
    return out.crop(out.getbbox() or (0, 0, 1, 1))


def put_centered(dst, img, cx, cy):
    blit(dst, img, int(cx - img.width / 2), int(cy - img.height / 2))


# ================================================================================================
# Post effects (numpy, on the 640x360 stage)
# ================================================================================================
_VIGNETTE = None


def vignette(strength=0.55):
    global _VIGNETTE
    if _VIGNETTE is None or _VIGNETTE[0] != strength:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        v = 1.0 - strength * np.clip((d - 0.45) / 0.55, 0, 1) ** 1.6
        v = np.round(v * 16) / 16                         # stepped, like a pixel-art gradient
        _VIGNETTE = (strength, v[..., None])
    return _VIGNETTE[1]


def post(img, flash=0.0, fade=1.0, shake=(0, 0), chroma=0, vig=0.55, tint=None, flash_color=(255, 255, 255)):
    """The stage image -> an RGB uint8 array with the cut's effects: a camera shake (whole px), an R/B split, a tint
    (multiply), the vignette, a flash towards flash_color and a fade to black."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    if shake != (0, 0):
        a = np.roll(a, (int(shake[1]), int(shake[0])), axis=(0, 1))
    if chroma:
        a[..., 0] = np.roll(a[..., 0], -chroma, axis=1)
        a[..., 2] = np.roll(a[..., 2], chroma, axis=1)
    if tint is not None:
        a *= np.asarray(tint, dtype=np.float32) / 255.0
    if vig:
        a *= vignette(vig)
    if flash > 0:
        a += (np.asarray(flash_color, dtype=np.float32) - a) * min(1.0, flash)
    if fade < 1.0:
        a *= max(0.0, fade)
    return np.clip(a, 0, 255).astype(np.uint8)


def upscale(arr):
    return np.repeat(np.repeat(arr, SCALE, axis=0), SCALE, axis=1)


def hd_overlay(frame, overlay, x, y, alpha=1.0):
    """Blends an RGBA PIL image onto the 1080p RGB frame array at (x, y), clipped."""
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(overlay.width, HD_W - x), min(overlay.height, HD_H - y)
    if sx1 <= sx0 or sy1 <= sy0 or alpha <= 0:
        return
    o = np.asarray(overlay.crop((sx0, sy0, sx1, sy1)), dtype=np.float32)
    a = o[..., 3:4] / 255.0 * alpha
    region = frame[y + sy0:y + sy1, x + sx0:x + sx1].astype(np.float32)
    frame[y + sy0:y + sy1, x + sx0:x + sx1] = (region + (o[..., :3] - region) * a).astype(np.uint8)


# ================================================================================================
# Particles (stage space; deterministic per shot: seeded, stepped once per frame)
# ================================================================================================
class Particles:
    def __init__(self, seed=1):
        self.rng = np.random.default_rng(seed)
        self.p = []                                       # [x, y, vx, vy, life, life0, colour ramp, size, gravity, drag]

    def burst(self, x, y, n, ramp, speed=(1.0, 4.0), life=(18, 40), size=2, gravity=0.12, spread=(0.0, math.tau), drag=0.98):
        for _ in range(n):
            a = self.rng.uniform(*spread)
            s = self.rng.uniform(*speed)
            lf = int(self.rng.integers(life[0], life[1] + 1))
            self.p.append([x, y, math.cos(a) * s, math.sin(a) * s, lf, lf, ramp, size, gravity, drag])

    def step(self):
        for q in self.p:
            q[0] += q[2]
            q[1] += q[3]
            q[3] += q[8]
            q[2] *= q[9]
            q[3] *= q[9]
            q[4] -= 1
        self.p = [q for q in self.p if q[4] > 0]

    def draw(self, view):
        d = view.draw()
        for x, y, vx, vy, life, life0, ramp, size, g, drag in self.p:
            f = life / life0
            col = ramp[min(len(ramp) - 1, int((1 - f) * len(ramp)))]
            sx, sy = view.to_view(x, y)
            sx, sy = int(sx) // 2 * 2, int(sy) // 2 * 2
            d.rectangle([sx, sy, sx + size - 1, sy + size - 1], fill=tuple(col) + (255,))


# ================================================================================================
# Encoding
# ================================================================================================
def find_ffmpeg(explicit=None):
    """ffmpeg: --ffmpeg, then COGPUNK_FFMPEG, then PATH, then a build bundled with an installed editor (CapCut)."""
    cands = [explicit, os.environ.get("COGPUNK_FFMPEG"), shutil.which("ffmpeg")]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        cands += sorted(glob.glob(os.path.join(local, "CapCut", "Apps", "*", "ffmpeg.exe")), reverse=True)
    for c in cands:
        if c and os.path.exists(c):
            return c
    raise SystemExit("ffmpeg not found: pass --ffmpeg PATH, set COGPUNK_FFMPEG, or `winget install --id Gyan.FFmpeg -e` (SETUP.md)")


def pick_encoder(ffmpeg, wanted=None):
    """The first H.264 encoder that really encodes here (hardware ones are listed even without their hardware)."""
    order = [wanted] if wanted else ["libx264", "h264_nvenc", "h264_qsv", "h264_amf", "h264_mf"]
    for enc in order:
        try:
            r = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=640x360:r=30:d=0.2",
                                "-c:v", enc, "-f", "null", "-"], capture_output=True, timeout=60)
            if r.returncode == 0:
                return enc
        except Exception:
            pass
    raise SystemExit("no working H.264 encoder in this ffmpeg build")


class Encoder:
    """Pipes 1920x1080 RGB frames to ffmpeg, with the music cut to the teaser's length and faded out."""

    def __init__(self, ffmpeg, out, music=None, music_start=0.0, duration=60.0, audio_fade=2.0, encoder=None, bitrate="16M", extra=()):
        enc = pick_encoder(ffmpeg, encoder)
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (HD_W, HD_H),
               "-r", str(FPS), "-i", "-"]
        if music:
            cmd += ["-ss", "%.3f" % music_start, "-t", "%.3f" % duration, "-i", music]
        cmd += ["-map", "0:v:0"]
        if music:
            cmd += ["-map", "1:a:0", "-af", "afade=t=in:st=0:d=0.05,afade=t=out:st=%.3f:d=%.3f" % (max(0.0, duration - audio_fade), audio_fade),
                    "-c:a", "aac", "-b:a", "192k"]
        if not extra and enc == "h264_nvenc":
            # constant quality: an average-bitrate encode starves the cuts (flash + shake) and smears the pixels for a
            # second after each, while padding the still shots; constant QP 24 is sharper at half the size (measured)
            extra = ("-preset", "slow", "-rc", "constqp", "-qp", "24", "-bf", "2", "-g", "120")
        cmd += ["-c:v", enc] + list(extra) + ["-b:v", bitrate, "-maxrate", "%dM" % (2 * int(bitrate.rstrip("M"))), "-bufsize", "32M", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-t", "%.3f" % duration, out]
        self.enc = enc
        self.last = None
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, frame):
        self.last = frame.tobytes()
        self.proc.stdin.write(self.last)

    def close(self):
        try:
            if self.last is not None:                     # one spare frame past -t: ffmpeg may cut the pipe's last one short
                self.proc.stdin.write(self.last)
            self.proc.stdin.close()
        except OSError:
            pass
        return self.proc.wait()
