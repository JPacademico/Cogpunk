"""The Fungimancer's small things (2026-11-19, kept from v1 when the boss was redrawn on 2026-11-23): its spore bolt, the
mushroom that bursts out of the ground, the tongue's tip, the treasure bag, the Rainbow Mushroom (item and tile)."""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
from rig import RAMP, Xf, Ellipse, Capsule, Poly, Canvas, dome  # noqa: E402
from westbots import finish  # noqa: E402
from make_trashtr0m_art import to_image  # noqa: E402

CA, SA, K, EM, DN, AE, SM, IV = (RAMP[k] for k in ("cactus", "sage", "crimson", "ember", "denim", "aether", "steam", "ivory"))


# --- projectiles and things ------------------------------------------------------------------------------------------------
def spore_bolt():
    """A spore of violet light: a round glow (aether) round a bright core, sparkles turning round it, 4 frames, 9 px."""
    out = Image.new("RGBA", (9, 4 * 10 - 1), (0, 0, 0, 0))
    for k in range(4):
        px = {}
        for y in range(9):
            for x in range(9):
                d = math.hypot(x - 4, y - 4)
                if d <= 3.3:
                    px[(x, y)] = AE[3] if d < 1.2 else AE[2] if d < 2.4 else AE[1]
        a = k * math.pi / 2
        for (r, off) in ((4.2, 0.0), (4.2, math.pi)):
            q = (int(round(4 + r * math.cos(a + off))), int(round(4 + r * math.sin(a + off))))
            if 0 <= q[0] < 9 and 0 <= q[1] < 9:
                px[q] = DN[5]
        px[(3, 3)] = SM[3]
        for (x, y), c in px.items():
            out.putpixel((x, y + k * 10), c + (255,))
    return out


def shroom_spike():
    """A glowing mushroom bursting up out of the ground, 4 frames of 14 x 18: a bump, the stalk rising, the cap open, the cap
    with spores (it lingers that way while it hurts)."""
    out = Image.new("RGBA", (14, 4 * 19 - 1), (0, 0, 0, 0))
    for k in range(4):
        cv = Canvas()
        rise = (3.0, 8.0, 12.0, 12.0)[k]
        base = 17.5
        cv.part(Xf(), Capsule((7.0, base), (7.0, base - rise), 2.2, 1.8), "steam", lambda i: 2 if i.lx < 6.8 else 1, rust=0.0)
        if k >= 1:
            cap_w = (3.5, 6.4, 6.6)[k - 1]
            cy = base - rise - 1.0
            cv.part(Xf(), Ellipse(7.0, cy + 1.0, cap_w, 4.4 if k > 1 else 2.6) - Poly([(0.0, cy + 1.2), (14.0, cy + 1.2), (14.0, 20.0), (0.0, 20.0)]),
                    "denim", dome(5.0, cy - 2.5, 7.0, lo=2, hi=5, fixed=True), rust=0.0)
            cv.part(Xf(), Ellipse(7.0, cy + 1.0, cap_w - 0.6, 0.9), "aether", lambda i: 2, rust=0.0, outline=False)
            if k >= 2:
                for (x, y) in ((5, int(cy - 1)), (9, int(cy))):
                    cv.put(x, y, SM[3])
            if k == 3:
                for (x, y) in ((2, int(cy - 4)), (11, int(cy - 3)), (7, int(cy - 5))):
                    cv.put(x, y, AE[3])
        finish(cv)
        for (x, y), c in cv.px.items():
            if 0 <= x < 14 and 0 <= y < 18:
                out.putpixel((x, y + k * 19), c + (255,))
    return out


def tongue_tip():
    cv = Canvas()
    cv.part(Xf(), Ellipse(3.5, 3.5, 3.2, 2.8), "crimson", dome(2.6, 2.4, 3.6, lo=3, hi=5, fixed=True), rust=0.0)
    finish(cv)
    return to_image(cv.px, 0, 0, 7, 7)


def bag():
    """The treasure bag: a blue cloth sack tied with a violet cord, a glowing mushroom stitched on it."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(8.0, 10.0, 6.5, 5.6), "denim", dome(6.0, 8.0, 8.0, lo=2, hi=4, fixed=True), rust=0.0)
    cv.part(Xf(), Poly([(5.0, 3.0), (11.0, 3.0), (9.6, 5.6), (6.4, 5.6)]), "denim", lambda i: 3, rust=0.0)
    for x in range(6, 11):
        cv.put(x, 5, AE[2] if x % 2 else AE[3])
    cv.part(Xf(), Ellipse(8.0, 9.6, 2.6, 1.6), "steam", lambda i: 3 if i.lx < 8.0 else 2, rust=0.0, outline=False)
    cv.put(8, 11, SM[1])
    cv.put(8, 12, SM[1])
    finish(cv)
    return to_image(cv.px, 0, 0, 16, 16)


RAINBOW = (K[4], EM[3], RAMP["gilt"][8], CA[4], DN[5], AE[3])


def rainbow_mushroom(w, cap_rx, cap_ry, stalk_h, cx, base):
    """A glowing mushroom whose cap runs through the rainbow in bands (red at the crown to violet at the rim), a pale stalk."""
    cv = Canvas()
    cv.part(Xf(), Capsule((cx, base), (cx, base - stalk_h), 1.3, 1.1), "steam", lambda i: 2 if i.lx < cx - 0.2 else 1, rust=0.0)
    top = base - stalk_h - 0.6
    shape = Ellipse(cx, top, cap_rx, cap_ry) - Poly([(-5.0, top + 0.8), (w + 5.0, top + 0.8), (w + 5.0, base + 5.0), (-5.0, base + 5.0)])
    cv.part(Xf(), shape, "steam", lambda i: 3, rust=0.0)
    for (x, y), _ in list(cv.px.items()):
        dx, dy = (x + 0.5 - cx) / cap_rx, (y + 0.5 - top) / max(cap_ry, 0.1)
        if dy <= 0.2 and dx * dx + dy * dy <= 1.0:
            r = math.sqrt(dx * dx + dy * dy)
            band = min(len(RAINBOW) - 1, int(r * len(RAINBOW)))
            edge = any((x + ox, y + oy) not in cv.px for ox, oy in ((1, 0), (-1, 0), (0, -1)))
            cv.px[(x, y)] = RAMP["plum"][0] if edge else RAINBOW[band]
    return cv


def tile_sheet():
    """Three rainbow mushrooms (1 x 1 tile each, 8 x 8 at 1x, 9 px apart: 18 at 2x) of different heights."""
    out = Image.new("RGBA", (27, 9), (0, 0, 0, 0))
    for k, (rx, ry, sh) in enumerate(((3.4, 2.6, 2.6), (3.0, 2.4, 3.6), (3.6, 2.8, 2.0))):
        cv = rainbow_mushroom(8, rx, ry, sh, 3.8, 7.6)
        for (x, y), c in cv.px.items():
            if 0 <= x < 8 and 0 <= y < 8:
                out.putpixel((x + k * 9, y), c + (255,))
    return out


def summon_item():
    cv = rainbow_mushroom(14, 6.0, 4.6, 5.0, 7.0, 13.0)
    return to_image(cv.px, 0, 0, 14, 14)


