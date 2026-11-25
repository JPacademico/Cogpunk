"""The Fungimancer's 2026-11-25 fight things (user: his attacks 1-8 and the defeat). Called by make_fungimancer_art.export_all;
run alone for a preview:

    python -P art/bosses/fungimancer/fungimancer_fight.py PREVIEW.png

Colours: the palette only; the fight's rainbow is the palette's (crimson, ember, fel, emerald, the glowing mushrooms' cyan,
aether, amethyst). Outputs under Content/Bosses/Fungimancer/:
    Projectiles/RainbowSpore.png      6 frames of 8 x 8: a pale core in a turning ring of the rainbow
    Projectiles/PolymorphBolt.png     4 frames of 12 x 12: a pink bubble with a turning swirl
    Projectiles/MushroomMissile.png   16 headings of 16 x 16 (sculpted; never rotated at runtime, D4 rule 14)
    NPCs/FloatyMushroom.png (+_Glow)  3 frames of 12 x 12: leaning left, upright, leaning right
    NPCs/OrbitMushroom.png (+_Glow)   4 frames of 16 x 16: a pulse, then swelling to hatch
    NPCs/ChannelMushroom.png (+_Glow) 6 growth stages of 42 x 36 (the Rainbow Mushroom's look, grown)
    Polymorph/Polymorphed.png, Polymorph/ShellShocked.png   the debuff icons (16 x 16)
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "templates"))
sys.path.insert(0, HERE)
from rig import RAMP  # noqa: E402
from sculpt import Frame, Ell, Tube, Part, render  # noqa: E402
from make_trashtr0m_art import export  # noqa: E402
import fungimancer_things as things  # noqa: E402

K, EM, AE, SM, IV, AM, GI, FEL, EMR = (RAMP[k] for k in ("crimson", "ember", "aether", "steam", "ivory", "amethyst", "gilt", "fel",
                                                            "emerald"))
CYAN = (67, 221, 248)
SPECTRUM = (K[4], EM[2], EM[3], FEL[6], EMR[4], CYAN, AE[2], AM[4])
CAP = ((5, 32, 51), (10, 47, 71), (6, 67, 88), (8, 100, 114), (11, 135, 137), (12, 176, 161), CYAN)   # the biome's teal
DARK = (8, 4, 6)


def img(px, w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), c in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), tuple(c) + (255,))
    return im


def stack(frames, w, h):
    out = Image.new("RGBA", (w, (h + 1) * len(frames)), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        out.alpha_composite(im, (0, k * (h + 1)))
    return out


def outline(px, edge_colour):
    edge = {}
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px:
                edge[q] = edge_colour
    edge.update(px)
    return edge


def rainbow_spore():
    """User: "5 small rainbow spore projectiles", "a fan burst of 6 quick rainbow spore projectiles"."""
    frames = []
    for k in range(6):
        px = {}
        for y in range(8):
            for x in range(8):
                dx, dy = x + 0.5 - 4.0, y + 0.5 - 4.0
                d = math.hypot(dx, dy)
                if d > 3.3:
                    continue
                if d < 1.5:
                    px[(x, y)] = SM[3] if (x, y) == (3, 3) else SM[2]
                else:
                    a = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                    px[(x, y)] = SPECTRUM[(int(a * 8) + k) % 8]
        frames.append(img(outline(px, AM[1]), 8, 8))
    return stack(frames, 8, 8)


def polymorph_bolt():
    """User: "he quickly burps a pink accelerating homming ... projectile that polymorphs the player hit into a toadstool"."""
    frames = []
    for k in range(4):
        px = {}
        for y in range(12):
            for x in range(12):
                dx, dy = x + 0.5 - 6.0, y + 0.5 - 6.0
                d = math.hypot(dx, dy)
                if d > 4.75:
                    continue
                lit = -(dx + dy) / 6.0
                a = math.atan2(dy, dx) + k * math.pi / 2
                swirl = (math.sin(a * 2 + d * 1.3) > 0.55) and d > 1.2
                i = 4 + (1 if lit > 0.35 else 0) - (1 if lit < -0.35 else 0) - (1 if swirl else 0)
                px[(x, y)] = AM[max(2, min(5, i))]
        px[(4, 3)] = SM[3]
        px[(3, 4)] = AM[5]
        frames.append(img(outline(px, AM[1]), 12, 12))
    return stack(frames, 12, 12)


MISSILE_HEADINGS, MISSILE_CELL = 16, 16


def mushroom_missile():
    """User: "fire a quick mushroom missile that bounces up to 3 times and deals heavy damage": a fat violet cap with pale
    spots flying cap first, its stalk trailing; heading k points k x 22.5 degrees clockwise from right; one to the left is
    modelled mirrored so the cap's top stays up. Cells 16 x 16, 1 px apart, the origin in the middle."""
    out = Image.new("RGBA", (MISSILE_HEADINGS * (MISSILE_CELL + 1), MISSILE_CELL), (0, 0, 0, 0))
    for k in range(MISSILE_HEADINGS):
        angle = k * 2 * math.pi / MISSILE_HEADINGS
        mirror = math.cos(angle) < -1e-6 or (abs(math.cos(angle)) <= 1e-6 and math.sin(angle) < 0)
        s = -1.0 if mirror else 1.0
        f = Frame(0.0, 0.0, angle)
        spots = ((2.2, -1.8 * s, 0.8, 0.7, 2), (1.0, 1.6 * s, 0.7, 0.6, 2), (3.2, 0.6 * s, 0.6, 0.6, 2))
        parts = [Part("stalk", Tube([(-1.0, 0.0), (-5.8, 0.4 * s)], [1.6, 1.1]), IV, 0, f, lo=2, hi=5),
                 Part("cap", Ell(1.6, 0.0, 3.2, 4.6), AM, 1, f, lo=1, hi=5, spots=spots)]
        px, _, _ = render(parts, MISSILE_CELL, MISSILE_CELL, MISSILE_CELL / 2.0, MISSILE_CELL / 2.0)
        out.alpha_composite(img(px, MISSILE_CELL, MISSILE_CELL), (k * (MISSILE_CELL + 1), 0))
    return out


def floaty_mushroom():
    """User: "a small floaty mushroom that comes swaying falling": a glowing mushroom of the biome, a teal cap over a pale stalk
    hanging under it, 3 frames of 12 x 12 (leaning left, upright, leaning right); the cap's light in the glow sheet."""
    frames, glows = [], []
    for lean in (-1, 0, 1):
        px, glow = {}, {}
        cx, top = 6.0 + lean * 0.6, 2.0
        for y in range(12):
            for x in range(12):
                dx, dy = (x + 0.5 - cx) / 4.6, (y + 0.5 - (top + 2.6)) / 3.0
                if dy <= 0.25 and dx * dx + dy * dy <= 1.0:
                    lit = -(dx * 0.7 + dy * 0.7)
                    i = 4 + (1 if lit > 0.45 else 0) + (1 if lit > 0.85 else 0) - (1 if lit < -0.2 else 0)
                    px[(x, y)] = CAP[max(2, min(6, i))]
                    if i >= 5:
                        glow[(x, y)] = CAP[min(6, i)]
        for y in range(5, 10):                            # the stalk, slanting with the lean
            x = int(round(6.0 - lean * 0.35 * (y - 5) - 0.5))
            px[(x, y)] = IV[4] if y < 9 else IV[3]
            px[(x + 1, y)] = IV[3] if y < 9 else IV[2]
        g = (int(cx) - 2, 3)
        px[g] = SM[3]                                     # a glint
        glow[g] = SM[3]
        frames.append(img(outline(px, CAP[0]), 12, 12))
        glows.append(img(glow, 12, 12))
    return stack(frames, 12, 12), stack(glows, 12, 12)


def orbit_mushroom():
    """User: "he summons 6 mushroons that spin arround him and if not detroyed in 6 seconds they burst into 1-2 toadstools":
    classic toadstools (a red cap with white spots on a pale stalk), 4 frames of 16 x 16: two of a slow pulse, two swelling
    (their last second: about to hatch); the spots glow."""
    frames, glows = [], []
    for k in range(4):
        swell = (0.0, 0.0, 0.5, 1.0)[k]
        bump = 1 if k == 1 else 0
        px, glow = {}, {}
        cx, cy = 8.0, 7.6 - bump * 0.5
        rx, ry = 6.2 + swell * 1.2, 4.4 + swell * 0.9 + bump * 0.3
        for y in range(16):
            for x in range(16):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if dy <= 0.3 and dx * dx + dy * dy <= 1.0:
                    lit = -(dx * 0.7 + dy * 0.7)
                    i = 3 + (1 if lit > 0.35 else 0) + (1 if lit > 0.8 else 0) - (1 if lit < -0.25 else 0)
                    px[(x, y)] = K[max(1, min(5, i))]
        for (sx, sy) in ((5, 5), (9, 4), (11, 7), (7, 8), (4, 8)):
            q = (sx, sy - bump)
            if q in px:
                px[q] = IV[5]
                glow[q] = IV[5]
        for y in range(int(cy + ry * 0.3) + 1, 15):
            px[(7, y)] = IV[4]
            px[(8, y)] = IV[3]
            if y == 14:
                px[(6, y)] = IV[3]
                px[(9, y)] = IV[2]
        frames.append(img(outline(px, K[0]), 16, 16))
        glows.append(img(glow, 16, 16))
    return stack(frames, 16, 16), stack(glows, 16, 16)


CHANNEL_STAGES, CHANNEL_W, CHANNEL_H = 6, 42, 36
# the cap's rainbow bands from the crown out, each a lit and a shadowed tone (lit from the top-left), and its outline
BANDS = ((K[4], K[3]), (EM[2], EM[1]), (EM[3], GI[7]), (FEL[6], FEL[4]), (CYAN, CAP[5]), (AE[2], AE[1]), (AM[4], AM[3]))
CAP_EDGE = RAMP["plum"][0]


def channel_mushroom():
    """User: "chanel a growing rainbow mushroom for 5 seconds ... the mushroom can be damaged and destroyed": the Rainbow
    Mushroom's look grown big (its rainbow bands from red at the crown to violet at the rim), modelled properly: a domed cap
    lit from the top-left (each band in a lit and a shadowed tone), pale spots, a dark fringe of gills under the rim, a thick
    ivory stalk with a skirt; 6 growth stages of 42 x 36, the origin at the bottom middle; the cap glows."""
    frames, glows = [], []
    for k in range(CHANNEL_STAGES):
        t = (k + 1) / CHANNEL_STAGES
        cx, base = CHANNEL_W / 2.0, CHANNEL_H - 1.0
        rx, ry = 4.0 + 15.5 * t, 3.2 + 9.5 * t
        stalk_h, stalk_r = 2.5 + 12.0 * t, 1.0 + 2.2 * t
        top = base - stalk_h
        px, glow = {}, {}
        for y in range(CHANNEL_H):                       # the stalk: lit left, shadowed right, a skirt a third down
            for x in range(CHANNEL_W):
                dx = x + 0.5 - cx
                if top - 1 <= y <= base and abs(dx) <= stalk_r + 0.4 * (y - top) / max(1.0, stalk_h):
                    u = dx / (stalk_r + 0.01)
                    px[(x, y)] = IV[5] if u < -0.35 else IV[4] if u < 0.25 else IV[3] if u < 0.7 else IV[2]
        skirt = int(round(top + stalk_h * 0.3))
        if k >= 2:
            for x in range(int(cx - stalk_r - 1), int(cx + stalk_r + 2)):
                px[(x, skirt)] = IV[4] if x < cx else IV[3]
                px[(x, skirt + 1)] = IV[2]
        for y in range(CHANNEL_H):                       # the cap: a dome, banded from the crown, lit from the top-left
            for x in range(CHANNEL_W):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - top) / ry
                if dy > 0.15 or dx * dx + dy * dy > 1.0:
                    continue
                r = math.sqrt(dx * dx + (dy * 1.15) ** 2)
                band = min(len(BANDS) - 1, int(r * len(BANDS)))
                lit = -(dx * 0.7 + dy * 0.75)
                c = BANDS[band][0] if lit > -0.1 else BANDS[band][1]
                px[(x, y)] = c
                glow[(x, y)] = c
        for (sx, sy) in ((-0.45, -0.55), (0.1, -0.78), (0.5, -0.42), (-0.15, -0.3), (0.72, -0.12), (-0.7, -0.15)):
            q = (int(cx + sx * rx), int(top + sy * ry))
            if q in px and k >= 1:
                px[q] = SM[3]                            # pale spots
                glow[q] = SM[3]
        rim = int(round(top + ry * 0.15))
        for x in range(int(cx - rx * 0.92), int(cx + rx * 0.92) + 1):   # the gills' dark fringe under the rim
            q = (x, rim + 1)
            if q not in px or px[q] in (IV[2], IV[3], IV[4], IV[5]):
                px[q] = AM[1] if (x % 2) else AE[0]
        px = outline(px, CAP_EDGE)
        frames.append(img(px, CHANNEL_W, CHANNEL_H))
        glows.append(img(glow, CHANNEL_W, CHANNEL_H))
    return stack(frames, CHANNEL_W, CHANNEL_H), stack(glows, CHANNEL_W, CHANNEL_H)


def polymorph_icon():
    """The Polymorphed debuff: a toad's face peering up (the Toadstool's green, orange eyes), a mushroom on its head."""
    FR = RAMP["frog"]
    px = {}
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - 8.0) / 6.6, (y + 0.5 - 10.0) / 4.8
            if dx * dx + dy * dy <= 1.0:
                lit = -(dx * 0.6 + dy * 0.8)
                px[(x, y)] = FR[max(2, min(6, 4 + (1 if lit > 0.3 else 0) + (1 if lit > 0.75 else 0) - (1 if lit < -0.3 else 0)))]
    for (ex, ey) in ((4, 6), (10, 6)):                    # eye bumps, orange eyes with slit pupils
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 1), (2, 1), (0, -1), (1, -1)):
            px[(ex + dx, ey + dy)] = FR[5]
        px[(ex, ey)] = EM[3]
        px[(ex + 1, ey)] = EM[2]
        px[(ex, ey + 1)] = EM[2]
        px[(ex + 1, ey + 1)] = DARK
    for x in range(4, 12):                                # the wide mouth
        px[(x, 12)] = FR[1]
    for (x, y, c) in ((7, 2, CAP[5]), (8, 2, CAP[5]), (6, 3, CAP[4]), (7, 3, CAP[6]), (8, 3, CAP[5]), (9, 3, CAP[4]), (7, 4, IV[4]),
                      (8, 4, IV[3])):
        px[(x, y)] = c                                    # a mushroom on its head
    return img(outline(px, FR[0]), 16, 16)


def shell_shocked_icon():
    """The Shell-Shocked debuff (the rainbow mushroom's blast: "stunning the players for 1.5 seconds"): a white burst, three
    stars circling it, the ringing in the ears."""
    px = {}
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - 8.0, y + 0.5 - 9.0
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            r = 3.0 + 1.6 * (math.cos(a * 8) > 0.3)
            if d <= r:
                px[(x, y)] = SM[3] if d < 1.6 else SM[2] if d < 2.6 else SM[1]
    for (sx, sy) in ((3, 3), (12, 4), (8, 1)):
        for (dx, dy, c) in ((0, 0, GI[8]), (1, 0, GI[7]), (-1, 0, GI[7]), (0, 1, GI[7]), (0, -1, GI[7])):
            px[(sx + dx, sy + dy)] = c
    return img(outline(px, AE[0]), 16, 16)


def export_fight(out):
    export(rainbow_spore(), out + "Projectiles/RainbowSpore.png")
    export(polymorph_bolt(), out + "Projectiles/PolymorphBolt.png")
    export(mushroom_missile(), out + "Projectiles/MushroomMissile.png")
    for name, (sheet, glow) in (("FloatyMushroom", floaty_mushroom()), ("OrbitMushroom", orbit_mushroom()),
                                ("ChannelMushroom", channel_mushroom())):
        export(sheet, out + "NPCs/%s.png" % name)
        export(glow, out + "NPCs/%s_Glow.png" % name)
    export(polymorph_icon(), out + "Polymorph/Polymorphed.png")
    export(shell_shocked_icon(), out + "Polymorph/ShellShocked.png")


def preview(path, sc=6):
    tiles = [rainbow_spore(), polymorph_bolt(), mushroom_missile(), floaty_mushroom()[0], orbit_mushroom()[0], channel_mushroom()[0],
             polymorph_icon(), shell_shocked_icon()]
    w = sum(t.width * sc + 8 for t in tiles) + 8
    h = max(t.height for t in tiles) * sc + 16
    out = Image.new("RGBA", (w, h), (30, 34, 60, 255))
    x = 8
    for t in tiles:
        out.alpha_composite(t.resize((t.width * sc, t.height * sc), Image.NEAREST), (x, 8))
        x += t.width * sc + 8
    out.save(path)
    print("preview", path)


if __name__ == "__main__":
    preview(sys.argv[1] if len(sys.argv) > 1 else "fight_preview.png", sc=3)
