"""Source for Trash-Tr0m's loot (D4, art direction of 2026-10-26: the user named these weapons, so Metal Slug-level detail).
Run from the repo root:

    python -P art/bosses/trashtr0m/make_trashtr0m_loot.py

Drawn at 1x and exported at 2x nearest-neighbour, Cogpunk palette only, lit from the top-left, every part outlined in
ramp 0 of its own material (the lit edge of a rod one step lighter, D4 rule 3's selective outline). Three techniques:
    * rods (lance, staffs, legs) are rasterised from a cross-section profile along an axis, so the same lance comes out
      as a clean horizontal sprite and as a clean 45-degree staircase for its icon;
    * bulky machinery (the launcher, the bag) is built from rig.py parts sized 3 px or more, so the outline never eats
      the shading, with details placed pixel by pixel on top;
    * the Tr0mhead is a hand-drawn pixel map (head, jaw, tripod); its jaw drops by translation, never by rotation.
Friendly effects use Brass and Aether (D3 colour coding): the boss's hostile Ember never appears on the player's side
except as the boss's own eyes on its treasure bag. Outputs (Content/Bosses/TrashTr0m/):

    Items/TrashTr0mBag.png                     36x36   treasure bag: a riveted scrap sack with the boss's brow and eyes
    Weapons/Tetanus.png                        84x84   item: the lance, point to the top right
    Weapons/TetanusProjectile.png              112x18  held lance, point to the right (rotated to the aim in code)
    Weapons/TetanusProjectile_Glow.png         112x120 6 frames (stride 20): a glint running up the needle, glowing rust
    Weapons/TetanusFlash.png                   48x250  5 frames (stride 50): the ring that bursts from the point
    Weapons/ScrapLauncher.png                  52x24   item/held gun, muzzle to the right (2026-10-27: smaller, the
                                                       barrel on the sprite's centre line so it sits at the hand)
    Weapons/ScrapLauncherChunk.png             32x102  3 frames (stride 34): chewed scrap, brass and aether glints
    Weapons/ScrapLauncherBall.png              60x248  4 frames (stride 62): the big scrap ball
    Weapons/ScrapImpact.png                    130x410 the shots' impact burst: 5 frames of 48 (left column) and of 80
                                                       (right column, from x 50), stride size + 2
    Weapons/Scrapmancer.png                    48x48   item: a small open palm of rusted plates, an aether stone in it
    Weapons/ScrapmancerWave.png                88x248  4 frames (stride 62): the friendly junk shockwave, rolling left
    Weapons/Tr0mheadStaff.png                  40x48   item: only the little Tr0m head (2026-10-27: no staff)
    Weapons/Tr0mheadSentry.png                 56x620  10 frames (stride 62), facing left: idle x2, jaw opening x2,
                                                       sucking x4 (the vortex turning), resting x2 (eyes dim, steam)
    Weapons/Tr0mheadSentry_Glow.png            56x620  eyes and throat
    Buffs/TetanusDebuff.png                    32x32   debuff icon: a rusted nail through a cracked plate
    Projectiles/TrashTr0mCog.png               24x104  4 frames (stride 26): the loose rusted cog the boss's stacks
                                                       cough up, spinning (ring teeth), an ember-hot hub (hostile)

The sentry's mouth point (relative to its hitbox centre, facing left) is printed for Tr0mheadSentry.MouthOffset.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import (RAMP, WHITE, Xf, Poly, Ellipse, Ring, Capsule, Union, box, Canvas, flat, face, dome,  # noqa: E402
                 cyl, rivet, bolt, line, stripes)
import make_trashtr0m_art as boss  # noqa: E402

OUT = "Content/Bosses/TrashTr0m/"
I, B, C, V, E, S, LE, A = (RAMP[k] for k in ("iron", "brass", "copper", "verd", "ember", "steam", "leather", "aether"))

# Pixel-map palette: one character per palette colour ('.' = transparent).
PIX = {".": None}
for _chars, _ramp in (("01234", "iron"), ("abcdef", "brass"), ("ghijk", "copper"), ("mnop", "verd"), ("qrs", "leather"),
                      ("tuvw", "steam"), ("xyzZ", "ember"), ("ABCD", "aether")):
    for _k, _ch in enumerate(_chars):
        PIX[_ch] = RAMP[_ramp][_k]
GLOW_CHARS = set("ABCDZ")                                  # drawn full-bright too (the _Glow textures)


def blit(cv, rows, x0, y0, glow_chars=GLOW_CHARS, swap=None):
    """Paints a pixel map (list of equal-length strings) with its top-left at (x0, y0)."""
    w = len(rows[0])
    for y, row in enumerate(rows):
        assert len(row) == w, "pixel map row %d is %d wide, expected %d: %r" % (y, len(row), w, row)
        for x, ch in enumerate(row):
            if swap and ch in swap:
                ch = swap[ch]
            col = PIX[ch]
            if col is None:
                continue
            if ch in glow_chars:
                cv.put_glow(x0 + x, y0 + y, col)
            else:
                cv.put(x0 + x, y0 + y, col)


def img(cv, w, h, dx=0, dy=0, glow=False):
    """The canvas as a w x h image, its pixels moved by (dx, dy) (1x)."""
    return boss.to_image(cv.glow if glow else cv.px, -dx, -dy, w, h)


def img_fit(cv, w, h, name=""):
    """The canvas centred in a w x h image; fails loudly if the art doesn't fit (never crops silently)."""
    xs = [x for (x, _) in cv.px]
    ys = [y for (_, y) in cv.px]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    if bw > w or bh > h:
        raise SystemExit("%s: art is %dx%d, does not fit %dx%d" % (name, bw, bh, w, h))
    return img(cv, w, h, (w - bw) // 2 - min(xs), (h - bh) // 2 - min(ys))


def vertical(frames, pad=1):
    return boss.vertical(frames, pad)


def export(im, rel):
    boss.export(im, OUT + rel)


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def _h(a, b, seed):
    v = (a * 73856093 ^ b * 19349663 ^ seed * 83492791) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


# ================================================================================================
# Rods: a cross-section profile along an axis
# ================================================================================================
def rod(cv, origin, angle_deg, length, section, detail=None):
    """Paints a rod from origin along angle_deg (0 = right, -45 = up-right, 135 = down-left). section(t) -> (half
    width, ramp, lo, hi) or None, t in px along the axis. Across the rod, u < 0 is the lit side (towards the top-left):
    the lit edge pixel is outlined one step lighter (ramp 1), then the body from ramp hi down to lo, and a ramp-0 outline
    on the dark side. detail(t, u, colour) may return a replacement colour (or None to keep it)."""
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    if px + py < 0:
        px, py = -px, -py
    ox, oy = origin
    pad = 7
    xs = (ox, ox + dx * length)
    ys = (oy, oy + dy * length)
    for y in range(int(min(ys)) - pad, int(max(ys)) + pad + 1):
        for x in range(int(min(xs)) - pad, int(max(xs)) + pad + 1):
            rx, ry = x + 0.5 - ox, y + 0.5 - oy
            t = rx * dx + ry * dy
            u = rx * px + ry * py
            if t < -0.5 or t > length + 0.5:
                continue
            sec = section(max(0.0, min(length, t)))
            if sec is None:
                continue
            hw, ramp, lo, hi = sec
            if abs(u) > hw + 0.3:
                continue
            r = RAMP[ramp]
            if u > hw - 0.7:
                col = r[0]
            elif u < -hw + 0.7:
                col = r[1]
            else:
                band = (u + hw - 0.7) / max(0.01, 2.0 * hw - 1.4)
                col = r[max(lo, min(hi, hi - int(band * (hi - lo + 1))))]
            if detail is not None:
                col = detail(t, u, col) or col
            cv.put(x, y, col)


# ================================================================================================
# Tetanus: a long, thin, rusted needle of a lance
# ================================================================================================
LANCE_LEN = 56                                             # 2026-10-27: longer (was 44)
NEEDLE = 18.0                                              # where the needle leaves the socket
THIN = 40.0                                                # where it narrows to 3 px
POINT = 49.0                                               # where it is filed to a point


def lance_section(t):
    if t < 3.0:
        return (2.0, "brass", 2, 5)                        # pommel knob
    if t < 4.0:
        return (3.0, "brass", 2, 4)                        # ferrule
    if t < 12.0:
        return (2.2, "leather", 1, 2)                      # wrapped grip
    if t < 13.0:
        return (3.0, "brass", 2, 4)                        # ferrule
    if t < 16.0:
        return (4.3, "brass", 2, 5)                        # cog guard
    if t < 18.0:
        return (2.6, "iron", 2, 4)                         # socket
    if t < THIN:
        return (2.2, "iron", 2, 4)                         # the needle, 5 px
    if t < POINT:
        return (1.3, "iron", 3, 4)                         # 3 px
    return (max(0.45, 1.3 - (t - POINT) * 0.17), "iron", 4, 4)   # filed to a point


def lance_detail(t, u, col):
    ti = int(t)
    if 4.0 <= t < 12.0 and abs(u) < 1.4:                   # leather wrap: diagonal bands
        return LE[0] if (ti + int(math.floor(u + 0.5))) % 3 == 0 else None
    if 13.0 <= t < 16.0:
        if abs(u) > 3.4 and ti == 14:
            return B[1]                                    # teeth notches on the cog's rim
        if abs(u) < 0.6 and ti == 14:
            return B[1]                                    # the hub
    if 16.0 <= t < 18.0 and abs(u) < 0.6 and ti == 16:
        return I[4]                                        # a rivet on the socket
    if NEEDLE <= t < POINT - 1.0 and col not in (I[0], I[1]):   # rust on the needle, never on its edges
        n = _h(ti // 2, int(math.floor(u + 3)), 3)
        if n > 0.58 and (t < THIN - 1.0 or n > 0.8):
            return C[3] if col == I[4] else C[2]
        if _h(ti, int(math.floor(u + 3)), 9) > 0.9:
            return C[1]
    if t >= POINT and u < 0.25:                            # the filed point: bright and clean
        return S[2] if t < POINT + 4.5 else WHITE
    return None


def lance(cv, origin, angle):
    rod(cv, origin, angle, LANCE_LEN, lance_section, lance_detail)


def tetanus_projectile():
    cv = Canvas()
    lance(cv, (0.0, 4.5), 0.0)
    return img(cv, LANCE_LEN, 9)


def tetanus_glow_frames():
    """A brass glint running up the needle (one sweep over 6 frames), the rust smouldering brass, an aether spark at the
    point. Opaque pixels; the code fades the layer in with the charge."""
    base = Canvas()
    lance(base, (0.0, 4.5), 0.0)
    out = []
    for f in range(6):
        cv = Canvas()
        for (x, y), col in base.px.items():
            if x >= int(NEEDLE) and col in (C[3], C[2]):
                cv.put(x, y, B[3] if (x + y + f) % 3 else B[4])
        gx = int(NEEDLE) + f * int((POINT - NEEDLE) / 5)
        for k, colr in enumerate((B[4], B[5], WHITE, B[5])):
            x = gx + k
            for y in range(2, 6):
                if base.get(x, y) in (I[4], S[2]):
                    cv.put(x, y, colr)
                    break
        tip = LANCE_LEN - 1
        cv.put(tip, 4, A[3] if f % 2 == 0 else WHITE)
        cv.put(tip - 1, 4, A[2])
        if f % 2 == 0:
            cv.put(tip, 3, A[2])
            cv.put(tip, 5, A[2])
        out.append(img(cv, LANCE_LEN, 9))
    return out


def tetanus_flash_frames():
    """24x24 radial burst: core star, expanding ring with four spikes, breaking ring, last sparks (brass and aether)."""
    out = []
    c = 11.5
    for f in range(5):
        cv = Canvas()
        r = (2.0, 5.0, 7.5, 9.5, 11.0)[f]
        width = (2.2, 1.6, 1.2, 1.0, 0.8)[f]
        if f == 0:
            for p in cv.raster(Xf(), Ellipse(c, c, 2.6, 2.6)):
                cv.put(p[0], p[1], WHITE)
            for k in range(4):
                a = math.radians(k * 90)
                for d in range(3, 7):
                    q = (int(c + math.cos(a) * d), int(c + math.sin(a) * d))
                    cv.put(q[0], q[1], A[3] if d < 5 else A[2])
        else:
            for p in cv.raster(Xf(), Ring(c, c, r - width, r + width * 0.6)):
                ang = math.atan2(p[1] + 0.5 - c, p[0] + 0.5 - c)
                if f >= 3 and int((ang + math.pi) / (math.pi / 6)) % 2 == 1:
                    continue                                   # the ring breaks up
                outer = math.hypot(p[0] + 0.5 - c, p[1] + 0.5 - c) > r
                cv.put(p[0], p[1], (B[5] if not outer else B[4]) if f < 3 else (A[3] if not outer else A[2]))
            for k in range(4):                                 # spikes along the diagonals
                a = math.radians(45 + k * 90)
                for d in range(int(r - 1), int(r + 3 - f * 0.5)):
                    q = (int(round(c + math.cos(a) * d - 0.5)), int(round(c + math.sin(a) * d - 0.5)))
                    if 0 <= q[0] < 24 and 0 <= q[1] < 24:
                        cv.put(q[0], q[1], WHITE if f < 2 else A[3])
            if f <= 2:
                for p in cv.raster(Xf(), Ellipse(c, c, 1.5 - f * 0.4, 1.5 - f * 0.4)):
                    cv.put(p[0], p[1], A[3])
        out.append(img(cv, 24, 24))
    return out


def tetanus_item():
    cv = Canvas()
    lance(cv, (1.5, 40.5), -45.0)                          # butt bottom-left, point top-right
    return img_fit(cv, 42, 42, "Tetanus")


# ================================================================================================
# Scrap Launcher: the boss's jaw and grinder made into a hand cannon (muzzle right)
# ================================================================================================
def hcyl(cv, x0, x1, y0, y1, ramp, hi=None, lo=1, ends=True):
    """A horizontal cylinder filling rows y0..y1 (inclusive): ramp-0 outline round it (only top and bottom when not
    ends, for a band round something), the interior shaded from the lit top row (ramp hi) down to ramp lo."""
    r = RAMP[ramp]
    hi = len(r) - 1 if hi is None else hi
    n = y1 - y0 - 1
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if y in (y0, y1) or (ends and x in (x0, x1)):
                cv.put(x, y, r[0])
            else:
                k = y - y0 - 1
                cv.put(x, y, r[max(lo, hi - (k * (hi - lo + 1)) // max(1, n))])


def boxed(cv, x0, x1, y0, y1, ramp, top, body, bottom):
    """A lit box: ramp-0 outline, a lit top row, the body, a shaded bottom row."""
    r = RAMP[ramp]
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if y in (y0, y1) or x in (x0, x1):
                cv.put(x, y, r[0])
            elif y == y0 + 1:
                cv.put(x, y, r[top])
            elif y == y1 - 1:
                cv.put(x, y, r[bottom])
            else:
                cv.put(x, y, r[body])


def scrap_launcher():
    """26x12 (2026-10-27: was 36x20 and drawn over the player's head): the boss's jaw as the muzzle, its grinder gear on
    a riveted housing, its cement-mixer drum as the magazine, a leather grip. Muzzle to the right. The barrel runs along
    rows 3-6, so vanilla's gun drawing (the sprite's vertical centre on the player's centre, decompiled
    Player.ItemCheck_ApplyUseStyle_Inner + PlayerDrawLayers) keeps it at arm level; the grip hangs below the hand."""
    cv = Canvas()
    # butt plate: a brass cog seen edge-on
    for y in range(2, 8):
        cv.put(0, y, B[0])
        cv.put(1, y, B[4] if y < 4 else (B[3] if y < 6 else B[2]))
    cv.put(1, 2, B[0])
    cv.put(1, 7, B[0])
    # housing: riveted iron box, hazard band along its bottom
    boxed(cv, 2, 13, 1, 7, "iron", 3, 2, 1)
    for x in range(3, 13):
        cv.put(x, 6, B[4] if (x // 2) % 2 == 0 else I[0])
    for x in range(3, 13):                                  # the lit top edge
        cv.put(x, 2, I[3] if x % 4 else I[4])
    cv.put(3, 3, I[4])
    cv.put(4, 4, I[1])
    # grinder gear on the housing's side
    gc = (8.5, 4.0)
    teeth = Union(*[Capsule(gc, (gc[0] + math.cos(math.radians(a)) * 2.6, gc[1] + math.sin(math.radians(a)) * 2.6), 0.7) for a in range(0, 360, 60)])
    cv.part(Xf(), Ellipse(gc[0], gc[1], 1.8, 1.8) | teeth, "brass", dome(gc[0] - 1, gc[1] - 1, 3.0, lo=2, hi=5, gain=1.3), rust=0.0)
    cv.put(8, 4, B[0])
    cv.put(7, 3, B[5])
    # barrel with a brass band
    hcyl(cv, 13, 20, 2, 6, "iron")
    hcyl(cv, 16, 17, 1, 7, "brass", ends=False)
    # the jaw: hazard-striped brass upper plate, iron lower plate, fangs, an aether gleam in the throat
    boxed(cv, 20, 25, 0, 4, "brass", 4, 3, 2)
    for x in range(21, 25):
        cv.put(x, 1, B[4] if x % 2 == 0 else I[0])
    boxed(cv, 20, 25, 5, 8, "iron", 3, 2, 1)
    for x in range(21, 26):
        cv.put(x, 4, S[2] if x % 2 == 1 else I[0])          # upper fangs
        cv.put(x, 5, S[1] if x % 2 == 0 else I[0])          # lower fangs
    cv.put(25, 4, I[0])
    cv.put_glow(24, 4, A[2])
    cv.put_glow(25, 5, A[1])
    cv.put(22, 7, B[4])
    cv.put(21, 1, WHITE)
    # trigger guard and the leather grip under the back
    for (x, y) in ((8, 8), (9, 8), (9, 9), (9, 10), (8, 10)):
        cv.put(x, y, I[1])
    grip = cv.part(Xf(), Poly([(2.5, 7.0), (7.5, 7.0), (6.5, 12.0), (2.0, 12.0)]), "leather",
                   face((-0.5, -0.2, 0.85), lo=1, hi=2, ramp_len=3), rust=0.0)
    for y in (9, 11):
        line(cv, Xf(), (2.5, y), (6.5, y), lambda n: LE[0], grip)
    # the mixer-drum magazine under the barrel: spiral fins, a brass end cap
    drum = cv.part(Xf(), Ellipse(14.0, 9.0, 3.6, 2.9), "verd", dome(12.5, 7.5, 4.5, lo=1, hi=3, gain=1.3, bias=0.15), rust=0.0)
    for k in range(2):
        x0 = 12.0 + k * 2.5
        line(cv, Xf(), (x0, 7.0), (x0 + 1.5, 11.5), lambda n: V[0], drum)
    for y in range(7, 11):
        cv.put(17, y, B[0])
        cv.put(16, y, B[3] if y < 9 else B[2])
    return img(cv, 26, 12)


def scrap_launcher_old():
    """The 2026-10-26 36x20 design, kept for reference (not exported)."""
    cv = Canvas()
    # exhaust stack (rim, pipe) rising from the housing's back
    for x in range(5, 10):
        cv.put(x, 0, B[0] if x in (5, 9) else (B[5] if x == 6 else B[4]))
    for y in (1, 2):
        cv.put(6, y, I[0])
        cv.put(7, y, I[3])
        cv.put(8, y, I[1])
    # butt plate: a brass cog seen edge-on
    for y in range(3, 12):
        cv.put(0, y, B[0])
        cv.put(1, y, B[4] if y < 6 else (B[3] if y < 9 else B[2]))
        cv.put(2, y, B[0] if y % 2 else B[2])
    cv.put(1, 3, B[0])
    cv.put(1, 11, B[0])
    # housing: riveted iron box, hazard band along its bottom
    boxed(cv, 2, 20, 2, 11, "iron", 3, 2, 1)
    for x in range(3, 20):
        cv.put(x, 9, B[4] if (x // 2) % 2 == 0 else I[0])
        cv.put(x, 10, I[0] if (x // 2) % 2 == 0 else B[3])
    for x in (4, 8, 16):
        cv.put(x, 4, I[4])
        cv.put(x + 1, 5, I[1])
    cv.put(3, 3, I[4])
    for x in range(4, 20):                                  # the lit top edge
        cv.put(x, 3, I[3] if x % 4 else I[4])
    # grinder gear on the housing's side
    gc = (12.0, 6.5)
    teeth = Union(*[Capsule(gc, (gc[0] + math.cos(math.radians(a)) * 3.4, gc[1] + math.sin(math.radians(a)) * 3.4), 0.8) for a in range(0, 360, 45)])
    cv.part(Xf(), Ellipse(gc[0], gc[1], 2.4, 2.4) | teeth, "brass", dome(gc[0] - 1, gc[1] - 1, 3.8, lo=2, hi=5, gain=1.3), rust=0.0)
    cv.put(12, 6, B[0])
    cv.put(11, 5, B[5])
    # barrel with two brass bands
    hcyl(cv, 20, 30, 4, 9, "iron")
    for x0 in (22, 27):
        hcyl(cv, x0, x0 + 1, 3, 10, "brass", ends=False)
    # the jaw: hazard-striped brass upper plate, iron lower plate, fangs, a dark throat with an aether gleam
    boxed(cv, 30, 35, 1, 6, "brass", 4, 3, 2)
    for x in range(31, 35):
        cv.put(x, 2, B[4] if (x + 2) % 2 == 0 else I[0])
        cv.put(x, 3, I[0] if (x + 2) % 2 == 0 else B[4])
    boxed(cv, 30, 35, 7, 12, "iron", 3, 2, 1)
    for x in range(31, 36):
        cv.put(x, 6, S[2] if x % 2 == 1 else I[0])          # upper fangs
        cv.put(x, 7, S[1] if x % 2 == 0 else I[0])          # lower fangs
    cv.put(35, 6, I[0])
    for (x, col) in ((34, A[2]), (35, A[1])):
        cv.put_glow(x, 6 if x == 34 else 7, col)
    cv.put(33, 10, B[4])
    cv.put(32, 2, WHITE)
    # trigger guard and the leather grip under the back
    for (x, y) in ((10, 12), (11, 12), (12, 12), (12, 13), (12, 14), (11, 14), (10, 14)):
        cv.put(x, y, I[1])
    grip = cv.part(Xf(), Poly([(3.0, 11.0), (9.5, 11.0), (8.5, 19.5), (2.0, 19.5)]), "leather",
                   face((-0.5, -0.2, 0.85), lo=1, hi=2, ramp_len=3), rust=0.0)
    for y in (13, 15, 17):
        line(cv, Xf(), (3.0, y), (8.5, y), lambda n: LE[0], grip)
    # the mixer-drum magazine under the middle: spiral fins, a brass end cap
    drum = cv.part(Xf(), Ellipse(16.5, 14.5, 5.0, 4.5), "verd", dome(14.5, 12.5, 6.0, lo=1, hi=3, gain=1.3, bias=0.15), rust=0.0)
    for k in range(3):
        x0 = 12.5 + k * 3.0
        line(cv, Xf(), (x0, 11.0), (x0 + 2.5, 18.5), lambda n: V[0], drum)
        line(cv, Xf(), (x0 + 1.0, 11.0), (x0 + 3.5, 18.5), lambda n: V[3] if n % 2 == 0 else V[2], drum)
    for y in range(12, 18):
        cv.put(21, y, B[0])
        cv.put(20, y, B[3] if y < 15 else B[2])
    return img(cv, 36, 20)


def friendly_clump(cv, cx, cy, r, ang, aether):
    """The boss's scrap clump without its ember core, with brass and aether glints instead (friendly colours)."""
    boss.scrap_clump(cv, cx, cy, r, ang, random.Random(5), hot=False)
    xf = Xf.pose(ang, (cx, cy))
    glints = ((-0.5, -0.5, A[3]), (0.5, -0.5, A[2]), (-0.5, 0.5, A[2])) if aether else ((-0.5, -0.5, B[5]), (0.5, -0.5, B[4]))
    for (gx, gy, col) in glints:
        q = P(xf, (cx + gx, cy + gy))
        cv.put_glow(q[0], q[1], col)


def launcher_chunk_frames():
    out = []
    for f in range(3):
        cv = Canvas()
        friendly_clump(cv, 8, 8, 5.5, f * 40, aether=True)
        out.append(img(cv, 16, 16))
    return out


def launcher_ball_frames():
    out = []
    for f in range(4):
        cv = Canvas()
        friendly_clump(cv, 15, 15, 13.0, f * 22.5, aether=False)
        xf = Xf.pose(f * 22.5, (15, 15))
        cv.part(xf, Ring(15, 21, 3.0, 5.5), "iron", dome(13, 19, 6, lo=1, hi=3))
        cv.part(xf, Capsule((6, 9), (12, 5), 1.6), "steam", flat(2, bevel=False))
        for (x, y) in ((19, 9), (20, 9), (9, 18)):             # aether sparks caught in the lumps
            q = P(xf, (x, y))
            if cv.get(*q) is not None:
                cv.put_glow(q[0], q[1], A[2])
        out.append(img(cv, 30, 30))
    return out


# ================================================================================================
# Scrapmancer: a crane-boom scepter, the boss's three-prong claw closed around an aether core
# ================================================================================================
def boom_section(t):
    if t < 4.0:
        return None                                        # the pommel cog is a part
    if t < 5.0 or 12.0 <= t < 13.0 or 20.0 <= t < 21.0:
        return (2.6, "brass", 2, 5)                        # brass collars
    if t < 24.0:
        return (1.9, "copper", 2, 4)                       # the boom
    if t < 26.0:
        return (2.8, "iron", 2, 4)                         # the claw's wrist
    return None


def boom_detail(t, u, col):
    ti = int(t)
    if 5.0 <= t < 24.0 and col not in (C[0], C[1]) and not (12.0 <= t < 13.0 or 20.0 <= t < 21.0):
        if (ti % 3 == 0) and abs(u) < 1.0:
            return C[1]                                    # lattice rungs
    return None


def scrapmancer():
    """24x24 (2026-10-27: a small open hand, not a staff): a palm of rusted iron plates riveted at every knuckle, the
    fingers spread, a brass wrist cuff, an aether stone set in the palm. Built upright (fingers up, palm to the viewer,
    thumb on the left) and turned 45 degrees so the fingers point to the top right, like every swung item (D4 rule 8);
    the parts are rasterised in place, never rotated as a bitmap. Fingers are 3 px across so each keeps a shaded core
    inside its outline."""
    cv = Canvas()
    xf = Xf.pose(45.0, (0.0, 0.0), (12.0, 12.5))
    # wrist cuff (brass, a hazard band) under the palm
    cuff = cv.part(xf, box(-4.6, 7.4, 4.6, 11.8), "brass", face((-0.3, -0.4, 0.85), lo=2, hi=4, ramp_len=6), rust=0.0)
    for q in cuff:
        lx, ly = xf.inv((q[0] + 0.5, q[1] + 0.5))
        if 9.0 < ly < 10.4:
            cv.put(q[0], q[1], B[4] if int(math.floor((lx + ly) * 0.7)) % 2 == 0 else I[0])
    # the palm: a riveted plate, rusted
    palm = cv.part(xf, Poly([(-5.6, -1.6), (5.6, -1.6), (6.0, 4.6), (4.4, 7.9), (-4.4, 7.9), (-6.0, 4.4)]), "iron",
                   dome(-1.5, 0.5, 8.5, lo=1, hi=4, gain=1.3), rust=1.0)
    # fingers: two segments each with a brass knuckle rivet between, spread like an open hand
    for k, (bx, ang, ln) in enumerate(((-4.0, -16.0, 8.4), (-1.3, -5.0, 9.8), (1.4, 5.0, 9.2), (4.0, 16.0, 7.4))):
        a = math.radians(ang - 90.0)
        base = (bx, -0.8)
        knuckle = (bx + math.cos(a) * ln * 0.5, -0.8 + math.sin(a) * ln * 0.5)
        tip = (bx + math.cos(a) * ln, -0.8 + math.sin(a) * ln)
        cv.part(xf, Capsule(base, knuckle, 1.55), "iron", cyl(base, knuckle, 1.55, lo=1, hi=4, gain=1.4), rust=0.85)
        cv.part(xf, Capsule(knuckle, tip, 1.45, 1.2), "iron", cyl(knuckle, tip, 1.45, lo=1, hi=4, gain=1.4), rust=0.9)
        q = xf.fwd(knuckle)
        cv.put(int(math.floor(q[0])), int(math.floor(q[1])), B[4])
        cv.put(int(math.floor(q[0])) + 1, int(math.floor(q[1])) + 1, B[2])
    # the thumb, out to the left
    t0, t1 = (-5.0, 5.0), (-9.8, 2.6)
    cv.part(xf, Capsule(t0, t1, 1.6, 1.25), "iron", cyl(t0, t1, 1.6, lo=1, hi=4, gain=1.4), rust=0.9)
    q = xf.fwd(((t0[0] + t1[0]) * 0.5, (t0[1] + t1[1]) * 0.5))
    cv.put(int(math.floor(q[0])), int(math.floor(q[1])), B[4])
    for p in ((-3.8, 6.2), (3.6, 6.2)):                    # rivets holding the palm plate
        rivet(cv, xf, p, "iron", palm)
    # the aether stone in the palm (glow)
    c = xf.fwd((0.0, 3.0))
    cx, cy = int(math.floor(c[0])), int(math.floor(c[1]))
    stone = ((0, -1, A[3]), (-1, 0, A[3]), (0, 0, WHITE), (1, 0, A[2]), (0, 1, A[2]), (1, 1, A[1]), (-1, -1, A[2]),
             (1, -1, A[2]), (-1, 1, A[1]), (2, 0, A[0]), (0, 2, A[0]), (-2, 0, A[0]), (0, -2, A[0]))
    for (dx, dy, col) in stone:
        cv.put_glow(cx + dx, cy + dy, col)
    return img_fit(cv, 24, 24, "Scrapmancer")


def scrapmancer_old():
    """The 2026-10-26 crane-boom scepter, kept for reference (not exported)."""
    cv = Canvas()
    o = (2.0, 29.0)
    d = (math.cos(math.radians(-45.0)), math.sin(math.radians(-45.0)))
    at = lambda t, u=0.0: (o[0] + d[0] * t + d[1] * -u * -1.0, o[1] + d[1] * t + d[0] * u)   # noqa: E731
    # the pommel: a brass cog
    pc = at(2.0)
    teeth = Union(*[Capsule(pc, (pc[0] + math.cos(math.radians(a)) * 3.4, pc[1] + math.sin(math.radians(a)) * 3.4), 0.9) for a in range(0, 360, 45)])
    cv.part(Xf(), Ellipse(pc[0], pc[1], 2.4, 2.4) | teeth, "brass", dome(pc[0] - 1, pc[1] - 1, 3.6, lo=1, hi=5, gain=1.3), rust=0.0)
    cv.put(int(pc[0]), int(pc[1]), B[0])
    rod(cv, o, -45.0, 26.0, boom_section, boom_detail)
    # the claw: three iron prongs opening from the wrist and curling round the core
    wrist = at(25.5)
    core = at(31.0)
    for side in (-1, 0, 1):
        base = (wrist[0] + side * 2.2 * 0.7071, wrist[1] + side * 2.2 * 0.7071)
        tip_dir = math.radians(-45.0 + side * 52.0)
        mid = (base[0] + math.cos(tip_dir) * 4.5, base[1] + math.sin(tip_dir) * 4.5)
        tip = (mid[0] + math.cos(math.radians(-45.0 - side * 40.0)) * 3.0, mid[1] + math.sin(math.radians(-45.0 - side * 40.0)) * 3.0)
        cv.part(Xf(), Capsule(base, mid, 1.3, 1.1), "iron", cyl(base, mid, 1.2, lo=1, hi=4, gain=1.4), rust=0.0)
        cv.part(Xf(), Capsule(mid, tip, 1.0, 0.6), "iron", flat(3), rust=0.0)
    # the aether core: a faceted crystal, lit from inside (glow)
    cx, cy = core
    gem = Poly([(cx - 3.5, cy), (cx, cy - 3.5), (cx + 3.5, cy), (cx, cy + 3.5)])
    for p in cv.raster(Xf(), gem):
        rx, ry = p[0] + 0.5 - cx, p[1] + 0.5 - cy
        edge = abs(rx) + abs(ry) > 2.6
        if edge:
            col = A[0]
        elif rx + ry < -0.6:
            col = A[3] if abs(rx) + abs(ry) > 1.2 else WHITE
        elif rx + ry > 0.6:
            col = A[1]
        else:
            col = A[2]
        cv.put_glow(p[0], p[1], col)
    return img_fit(cv, 32, 32, "Scrapmancer")


def friendly_wave_frames():
    """The boss's shockwave (same 44x30 layout and rolling crest) in friendly colours: a dark scrap mound, billows of
    brass dust, aether sparks and an aether crack at its foot."""
    frames = []
    for f in range(4):
        cv = Canvas()
        lean = f * 1.5
        mound = Poly([(2, 30), (6 - lean, 18), (14 - lean, 9), (22 - lean * 0.5, 6), (32, 11), (40, 20), (43, 30)])
        cv.part(Xf(), mound, "leather", dome(14 - lean, 8, 26, lo=1, hi=2, gain=1.2, bias=0.1), rust=0.0)
        for k in range(5):                                 # billowing brass dust along the crest (soft: B3-B5 only)
            cx, cy = 8 + k * 7 - lean * (1 - k / 5), 12 + abs(k - 1.5) * 2.5 + (f + k) % 2
            r = 4.5 - abs(k - 2) * 0.5
            cv.part(Xf(), Ellipse(cx, cy, r, r * 0.85), "brass", dome(cx - 1.5, cy - 1.5, r * 1.3, lo=3, hi=5, gain=1.0, bias=0.2), rust=0.0)
        for k in range(4):                                 # scrap half buried in the mound
            x, y = 6 + k * 9 - lean * 0.5, 22 + (k % 2) * 3
            cv.part(Xf.pose((k * 50 + f * 20) % 360, (x, y)), Poly([(x - 2.5, y - 1.5), (x + 2.5, y - 2), (x + 2, y + 1.5), (x - 2, y + 2)]),
                    ("iron", "copper", "verd", "iron")[k], flat(2, bevel=False), rust=0.0)
        for k in range(6):                                 # flung chunks
            t = (k / 6 + f * 0.11) % 1.0
            x = 4 + t * 26 - lean
            y = 26 - math.sin(t * math.pi) * (20 + (k % 3) * 3)
            ang = (k * 47 + f * 33) % 360
            pts = [(x + math.cos(math.radians(ang + a)) * rr, y + math.sin(math.radians(ang + a)) * rr)
                   for a, rr in ((0, 2.4), (110, 1.8), (200, 2.2), (290, 1.6))]
            ramp = ("iron", "copper", "iron", "iron", "brass", "verd")[k]
            cv.part(Xf(), Poly(pts), ramp, flat(2 if ramp != "brass" else 3, bevel=False), rust=0.0)
        for k in range(4):                                 # aether sparks on the crest
            x, y = int(10 + k * 7 - lean + (f * 3 + k * 5) % 4), int(6 + (k * 3 + f) % 5)
            cv.put(x, y, A[3])
            cv.put(x + 1, y + 1, A[2])
        for x in range(2, 42):                             # the ground cracking under it
            if (x + f) % 7 < 5:
                cv.put(x, 29, I[0])
                if (x + f) % 7 == 2:
                    cv.put(x, 28, A[1])
        frames.append(img(cv, 44, 30))
    return frames


# ================================================================================================
# Tr0mhead: Trash-Tr0m's head in miniature (hand-drawn pixel maps, facing left, 3/4 view)
# ================================================================================================
# Head, 20x15: a rounded verdigris cranium lit from the top-left, the heavy hazard-brass brow jutting forward over the
# eye slot (three aether eyes: friendly), an iron snout with a grille, a row of steel fangs (pairs tapering to tips);
# the near side panel (verdigris, a vent, a brass hinge bolt) shows the 3/4 turn.
TR0M_HEAD = [
    "......mmmmmmmm......",
    "....mmpppoooooonm...",
    "...mpppoooooooonnm..",
    "..mppoooooooooonnnm.",
    ".aaaaaaaaaaaaonnnnm.",
    "afffeeeeeeeeaonnnnm.",
    "adddddddddddaonpnnm.",
    "ae0e0e0e0e0eaonnnnm.",
    ".00DC00DC00DC0nnnnm.",
    ".0443333333330nmmnm.",
    ".0313131313130npnnm.",
    ".0222222222220nednm.",
    ".0111111111110ncanm.",
    ".0vv00vv00vv00mmmmm.",
    ".00v000v000v00......",
]
# Jaw, 16x6: lower fang tips and pairs, a brass lip, the iron plate, hazard stripes; the hinge plate on the near side.
TR0M_JAW = [
    "....v...v....aa.",
    "0000vv00vv000aea",
    "aeeeeeeeeeeeaeda",
    "0333333333330dca",
    "0e0e0e0e0e0e0cba",
    ".000000000000aa.",
]
# Swivel ring under the head, 14x2.
TR0M_RING = [
    "01333333333310",
    "0e0e0e0e0e0e00",
]
FANG_ROW = 14                                              # head row of the upper fang tips; the closed jaw's top row
MAX_JAW_DROP = 3


def throat(cv, x0, y0, w, h, grind):
    """The open mouth: dark, an aether vortex turning around a white-hot core (glow pixels)."""
    cx, cy = x0 + w / 2.0, y0 + h / 2.0
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.6)
            ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
            if d < 0.8 + 0.3 * h:
                cv.put_glow(x, y, WHITE if h >= 3 else A[3])
            elif d < 1.6 + 0.6 * h:
                cv.put_glow(x, y, A[3])
            elif d < 2.6 + 0.9 * h:
                cv.put_glow(x, y, A[2])
            elif int(ang * 3.0 / math.pi + d * 0.45 - grind * 0.5) % 3 == 0:
                cv.put_glow(x, y, A[1])
            else:
                cv.put(x, y, I[0])


def exhaust(cv, x, y):
    """The little exhaust stack on the back of the cranium: a brass rim and an iron pipe (drawn before the head)."""
    for k, col in enumerate((B[0], B[4], B[0])):
        cv.put(x - 1 + k, y, col)
    for yy in range(y + 1, y + 4):
        cv.put(x - 1, yy, I[0])
        cv.put(x, yy, I[3])
        cv.put(x + 1, yy, I[1])


def tr0mhead(cv, x, y, drop=0, eyes=1.0, grind=0, bob=0):
    """Paints the exhaust, the throat (when open), the head and the jaw with the head's top-left at (x, y + bob).
    Returns the mouth point (1x, the throat's centre)."""
    y += bob
    exhaust(cv, x + 17, y - 2)
    if drop > 0:
        throat(cv, x + 1, y + FANG_ROW, 12, drop, grind)
    dim = None if eyes >= 1.0 else ({"D": "C", "C": "B"} if eyes > 0 else {"D": "1", "C": "1"})
    blit(cv, TR0M_HEAD, x, y, swap=dim)
    blit(cv, TR0M_JAW, x, y + FANG_ROW + drop)
    return (x + 7.0, y + FANG_ROW + drop / 2.0)


SENTRY_W, SENTRY_H = 28, 30
HEAD_X, HEAD_Y = 3, 2
SENTRY_POSES = [
    dict(drop=0, bob=0),                       # idle 0
    dict(drop=0, bob=1),                       # idle 1 (it breathes)
    dict(drop=1, grind=0),                     # the jaw drops
    dict(drop=2, grind=1),
    dict(drop=3, grind=0),                     # sucking: the vortex turns
    dict(drop=3, grind=1),
    dict(drop=3, grind=2),
    dict(drop=3, grind=3),
    dict(drop=0, eyes=0.5, steam=1),           # resting: eyes dim, the stack vents
    dict(drop=0, eyes=0.5, steam=2, bob=1),
]


def tripod(cv):
    """Three pipe legs and their feet; the ground line is row 29."""
    for (top, foot, ramp) in (((14.0, 23.5), (14.0, 28.5), "copper"), ((9.0, 23.0), (3.5, 28.5), "iron"), ((19.0, 23.0), (24.5, 28.5), "iron")):
        ang = math.degrees(math.atan2(foot[1] - top[1], foot[0] - top[0]))
        ln = math.hypot(foot[0] - top[0], foot[1] - top[1])
        rod(cv, top, ang, ln, lambda t, r=ramp: (1.5, r, 2, 4))
    for fx in (3.5, 14.0, 24.5):
        boxed(cv, int(fx) - 2, int(fx) + 2, 28, 29, "iron", 3, 2, 2)


def sentry_frame(drop=0, eyes=1.0, grind=0, bob=0, steam=0):
    cv = Canvas()
    tripod(cv)
    blit(cv, TR0M_RING, HEAD_X + 1, 22)
    mouth = tr0mhead(cv, HEAD_X, HEAD_Y, drop, eyes, grind, bob)
    for k in range(steam):                                 # steam puffs rising from the exhaust
        cx, cy = HEAD_X + 17.5 + k * 1.0, HEAD_Y - 1.5 - k * 0.5
        for p in cv.raster(Xf(), Ellipse(cx, cy, 1.3 + k * 0.6, 1.0 + k * 0.4)):
            if p[1] >= 0:
                cv.put(p[0], p[1], S[2] if (p[0] + 2 * p[1]) % 4 else S[1])
    return cv, mouth


def sentry_frames():
    frames, glows, mouth = [], [], None
    for k, pose in enumerate(SENTRY_POSES):
        cv, m = sentry_frame(**pose)
        if k == 4:
            mouth = m
        frames.append(img(cv, SENTRY_W, SENTRY_H))
        glows.append(img(cv, SENTRY_W, SENTRY_H, glow=True))
    return frames, glows, mouth


def staff_section(t):
    if 6.0 <= t < 7.0 or 13.0 <= t < 14.0:
        return (2.4, "brass", 2, 5)
    if t < 1.5:
        return (2.0, "brass", 2, 5)
    return (1.5, "iron", 2, 4)


def tr0mhead_staff():
    """Item (2026-10-27: no staff, only the head): the little Tr0m head with its jaw a crack open and its exhaust stack."""
    cv = Canvas()
    tr0mhead(cv, 0, 2, drop=1, grind=1)
    return img_fit(cv, 20, 24, "Tr0mheadStaff")


# ================================================================================================
# Scrap Launcher impact burst (2026-10-27) and Trash-Tr0m's loose cog
# ================================================================================================
def impact_frames(size, big):
    """A size x size burst (1x), 5 frames: a white-hot core with brass rays, an expanding brass ring with scrap
    flying out of it, the ring breaking into aether sparks, the last fragments, a few embers of brass. Friendly
    colours (D3); opaque pixels only, the code shows each frame for 3 ticks (no fades, D4)."""
    out = []
    c = size / 2.0 - 0.5
    rng = random.Random(11 if big else 7)
    shards = [(rng.uniform(0, math.tau), rng.uniform(0.55, 1.0), rng.choice(("iron", "copper", "iron", "brass"))) for _ in range(9 if big else 5)]
    s = size / 24.0
    for f in range(5):
        cv = Canvas()
        r = (2.2, 5.0, 7.5, 9.5, 10.5)[f] * s
        width = (2.2, 1.7, 1.2, 1.0, 0.8)[f] * (1.2 if big else 1.0)
        if f == 0:
            for p in cv.raster(Xf(), Ellipse(c, c, 2.8 * s, 2.8 * s)):
                cv.put(p[0], p[1], WHITE)
            for k in range(8):
                a = math.radians(k * 45 + 22.5)
                for d in range(int(3 * s), int((7 if k % 2 == 0 else 5) * s)):
                    q = (int(round(c + math.cos(a) * d)), int(round(c + math.sin(a) * d)))
                    cv.put(q[0], q[1], B[5] if d < 5 * s else B[4])
        else:
            for p in cv.raster(Xf(), Ring(c, c, r - width, r + width * 0.6)):
                ang = math.atan2(p[1] + 0.5 - c, p[0] + 0.5 - c)
                if f >= 3 and int((ang + math.pi) / (math.pi / 6)) % 2 == 1:
                    continue                                   # the ring breaks up
                outer = math.hypot(p[0] + 0.5 - c, p[1] + 0.5 - c) > r
                cv.put(p[0], p[1], (B[5] if not outer else B[4]) if f < 3 else (A[3] if not outer else A[2]))
            if f <= 2:
                for p in cv.raster(Xf(), Ellipse(c, c, (2.0 - f * 0.6) * s, (2.0 - f * 0.6) * s)):
                    cv.put(p[0], p[1], WHITE if f == 1 else B[5])
        if f >= 1:                                         # scrap shards flying out past the ring
            for (a, sp, ramp) in shards:
                d = r * (0.7 + 0.5 * sp) + f * 0.8 * s
                x, y = c + math.cos(a) * d, c + math.sin(a) * d
                if 1 <= x < size - 2 and 1 <= y < size - 2 and f <= 3:
                    rr = RAMP[ramp]
                    bx, by = int(x), int(y)
                    cv.put(bx, by, rr[-1])
                    cv.put(bx + 1, by, rr[2])
                    cv.put(bx, by + 1, rr[1])
                    cv.put(bx + 1, by + 1, rr[0])
            if f >= 2:
                for k in range(6 if big else 4):           # aether sparks
                    a = k * math.tau / (6 if big else 4) + f * 0.4
                    d = r + 1.5 * s
                    q = (int(c + math.cos(a) * d), int(c + math.sin(a) * d))
                    if 0 <= q[0] < size and 0 <= q[1] < size:
                        cv.put(q[0], q[1], A[3] if f < 4 else B[4])
        out.append(img(cv, size, size))
    return out


def scrap_impact_sheet():
    """Two columns: the chunk's 24 px burst (left) and the ball's 40 px burst (right, from x 25), stride size + 1."""
    from PIL import Image
    small, big = impact_frames(24, False), impact_frames(40, True)
    sheet = Image.new("RGBA", (24 + 1 + 40, 5 * 41), (0, 0, 0, 0))
    for k in range(5):
        sheet.alpha_composite(small[k], (0, k * 25))
        sheet.alpha_composite(big[k], (25, k * 41))
    return sheet


def boss_cog_frames():
    """12x12, 4 frames: a loose rusted cog (copper rust over iron, six teeth turning 15 degrees a frame: a full tooth
    period in 4 frames), an iron hub with an ember-hot axle hole (hostile colours, D3)."""
    out = []
    for f in range(4):
        cv = Canvas()
        cxy = (6.0, 6.0)
        xf = Xf.pose(f * 15.0, cxy)
        teeth = Union(*[Capsule(cxy, (6.0 + math.cos(math.radians(a)) * 5.0, 6.0 + math.sin(math.radians(a)) * 5.0), 1.1) for a in range(0, 360, 60)])
        cv.part(xf, Ellipse(6.0, 6.0, 3.7, 3.7) | teeth, "copper", dome(4.5, 4.5, 5.5, lo=1, hi=4, gain=1.3), rust=0.0)
        hub = cv.part(Xf(), Ellipse(6.0, 6.0, 1.9, 1.9), "iron", dome(5.0, 5.0, 2.4, lo=2, hi=4), rust=0.0)
        for (x, y, col) in ((5, 5, E[3]), (6, 5, E[2]), (5, 6, E[2]), (6, 6, E[1])):
            cv.put_glow(x, y, col)
        out.append(img(cv, 12, 12))
    return out


# ================================================================================================
# Treasure bag, debuff icon
# ================================================================================================
def treasure_bag():
    cv = Canvas()
    X = Xf()
    sack = cv.part(X, Poly([(4.0, 5.0), (14.0, 5.0), (16.5, 10.0), (16.0, 16.0), (2.0, 16.0), (1.5, 10.0)]), "leather",
                   dome(6.0, 7.0, 11.0, lo=1, hi=2, gain=1.2, bias=0.1), shadow=(1, 1), rust=0.0)
    for (a, b) in (((3.0, 9.0), (6.0, 15.5)), ((15.0, 9.0), (12.0, 15.5))):
        line(cv, X, a, b, lambda n: LE[0], sack)
    cv.part(X, Poly([(6.0, 1.5), (12.0, 1.5), (13.0, 5.0), (5.0, 5.0)]), "leather", flat(2), rust=0.0)
    cv.part(X, box(4.0, 4.0, 14.0, 6.0), "copper", cyl((4, 5), (14, 5), 1.0, lo=2, hi=4, gain=1.4), rust=0.0)   # the tie
    plate = cv.part(X, Poly([(5.0, 8.5), (13.0, 8.0), (13.5, 14.0), (5.5, 14.5)]), "iron", face((-0.3, -0.5, 0.8), lo=1, hi=3, ramp_len=5), rust=0.0)
    stripes(cv, cv.raster(X, Poly([(5.0, 8.5), (13.0, 8.0), (13.0, 10.0), (5.0, 10.5)])) & plate, 2, B[4], I[0], slope=-1)
    for x in range(6, 13):
        cv.put(x, 11, I[0])
    for x in (6, 9, 11):                                   # the boss's own three ember eyes
        cv.put(x, 11, E[3])
    for x in (7, 10):
        cv.put(x, 11, E[2])
    for x in range(6, 13, 2):
        cv.put(x, 13, S[2])
    cv.put(4, 7, WHITE)
    return img(cv, 18, 18)


def nail_section(t):
    if t < 1.6:
        return (2.4, "iron", 2, 4)                         # the head
    if t < 10.0:
        return (1.1, "copper", 2, 4)                       # the rusted shank
    return (max(0.4, 1.1 - (t - 10.0) * 0.35), "copper", 3, 4)


def tetanus_debuff_icon():
    cv = Canvas()
    plate = cv.part(Xf(), Poly([(1.5, 4.0), (12.0, 2.5), (14.5, 13.5), (3.0, 15.0)]), "iron",
                    face((-0.3, -0.5, 0.8), lo=1, hi=3, ramp_len=5), shadow=(1, 1), rust=0.0)
    for (a, b) in (((8.0, 8.0), (4.0, 13.0)), ((8.0, 8.0), (13.0, 5.5)), ((8.0, 8.0), (12.0, 13.0)), ((8.0, 8.0), (3.0, 6.0))):
        line(cv, Xf(), a, b, lambda n: I[0], plate)        # the plate cracks out from the nail
    rod(cv, (13.5, 1.5), 135.0, 13.0, nail_section)
    for (x, y) in ((6, 12), (6, 13), (7, 14)):             # rust running down from the wound
        cv.put(x, y, C[2] if y < 14 else C[1])
    return img(cv, 16, 16)


# ================================================================================================

def export_all():
    export(treasure_bag(), "Items/TrashTr0mBag.png")
    export(tetanus_item(), "Weapons/Tetanus.png")
    export(tetanus_projectile(), "Weapons/TetanusProjectile.png")
    export(vertical(tetanus_glow_frames()), "Weapons/TetanusProjectile_Glow.png")
    export(vertical(tetanus_flash_frames()), "Weapons/TetanusFlash.png")
    export(scrap_launcher(), "Weapons/ScrapLauncher.png")
    export(vertical(launcher_chunk_frames()), "Weapons/ScrapLauncherChunk.png")
    export(vertical(launcher_ball_frames()), "Weapons/ScrapLauncherBall.png")
    export(scrap_impact_sheet(), "Weapons/ScrapImpact.png")
    export(vertical(boss_cog_frames()), "Projectiles/TrashTr0mCog.png")
    export(scrapmancer(), "Weapons/Scrapmancer.png")
    export(vertical(friendly_wave_frames()), "Weapons/ScrapmancerWave.png")
    export(tr0mhead_staff(), "Weapons/Tr0mheadStaff.png")
    frames, glows, mouth = sentry_frames()
    export(vertical(frames), "Weapons/Tr0mheadSentry.png")
    export(vertical(glows), "Weapons/Tr0mheadSentry_Glow.png")
    export(tetanus_debuff_icon(), "Buffs/TetanusDebuff.png")
    # Tr0mheadSentry.PreDraw puts a frame's top at Bottom + 2 - 60 and its left at Centre.X - 28; the hitbox centre is
    # Bottom - 22 (44 px tall), so a 1x frame point (x, y) is (2x - 28, 2y - 36) from the centre (game px).
    mx, my = mouth
    print("Tr0mheadSentry.MouthOffset = (%.0f, %.0f)" % (2 * mx - SENTRY_W, 2 * my - 36))


if __name__ == "__main__":
    export_all()
