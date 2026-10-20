"""Source for the scaffold sprites (icon.png, icon_small.png, Assets/Textures/Placeholder.png).

Draws at 1x with Cogpunk palette colours only, then exports at 2x nearest-neighbour (D4).
Run from the repo root:  python -P art/scaffold/make_scaffold_art.py
Replace with hand-drawn .aseprite sources when real art exists.
"""
import math
from PIL import Image

C = {
    "brass0": (43, 26, 14), "brass1": (90, 58, 23), "brass2": (138, 93, 34), "brass3": (184, 138, 51),
    "brass4": (223, 185, 78), "brass5": (246, 231, 161),
    "iron0": (21, 22, 28), "iron1": (46, 50, 59), "iron2": (79, 85, 98), "iron3": (127, 135, 148),
    "ember1": (163, 48, 26), "ember2": (236, 113, 40), "ember3": (255, 199, 90),
}


def gear_mask(size, teeth, r_body, r_tooth, r_hole, duty=0.45):
    """Pixel-centre test: True where the gear (body + teeth, minus the hole) is solid."""
    c = (size - 1) / 2
    mask = [[False] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            frac = ((math.atan2(dy, dx) + math.pi) / (2 * math.pi) * teeth) % 1.0
            outer = r_tooth if frac < duty else r_body
            mask[y][x] = r_hole < r <= outer
    return mask


def shade_gear(img, mask, ox, oy, r_hole, groove=None):
    """Flat brass face lit from the top-left: lit rim, shadowed rim, ramp-0 outline."""
    size = len(mask)
    c = (size - 1) / 2
    px = img.load()

    def solid(x, y):
        return 0 <= x < size and 0 <= y < size and mask[y][x]

    for y in range(size):
        for x in range(size):
            if not mask[y][x]:
                continue
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            edge = not (solid(x - 1, y) and solid(x + 1, y) and solid(x, y - 1) and solid(x, y + 1))
            if edge:
                colour = C["brass0"]
            else:
                # Light from the top-left: compare the pixel's direction with (-1, -1).
                facing = (-dx - dy) / (max(r, 0.001) * math.sqrt(2))
                near_outer = not (solid(x - 2, y) and solid(x + 2, y) and solid(x, y - 2) and solid(x, y + 2))
                near_hole = r <= r_hole + 2.0
                colour = C["brass3"]
                if near_outer:
                    colour = C["brass5"] if facing > 0.75 else C["brass4"] if facing > 0.2 else C["brass2"] if facing < -0.2 else C["brass3"]
                elif near_hole:
                    # Inside edge of the hole is lit from the opposite side.
                    colour = C["brass2"] if facing > 0.2 else C["brass4"] if facing < -0.2 else C["brass3"]
                elif groove and abs(r - groove) < 0.6:
                    colour = C["brass2"] if facing > 0 else C["brass4"]
            px[ox + x, oy + y] = colour + (255,)


def hole_core(img, size, ox, oy, r_hole):
    c = (size - 1) / 2
    px = img.load()
    for y in range(size):
        for x in range(size):
            r = math.hypot(x - c, y - c)
            if r <= r_hole:
                px[ox + x, oy + y] = (C["ember3"] if r <= r_hole * 0.35 else C["ember2"] if r <= r_hole * 0.7 else C["ember1"]) + (255,)


def make_icon():
    art = Image.new("RGBA", (40, 40), C["iron1"] + (255,))
    px = art.load()
    for i in range(40):
        for p in ((i, 0), (i, 39), (0, i), (39, i)):
            px[p] = C["iron0"] + (255,)
    for i in range(1, 39):  # bevel: lit top/left, dark bottom/right
        px[i, 1] = C["iron2"] + (255,)
        px[1, i] = C["iron2"] + (255,)
    size, r_hole = 38, 5.2
    mask = gear_mask(size, teeth=8, r_body=13.2, r_tooth=17.6, r_hole=r_hole)
    hole_core(art, size, 1, 1, r_hole)
    shade_gear(art, mask, 1, 1, r_hole, groove=9.5)
    return art


def make_small_icon():
    art = Image.new("RGBA", (15, 15), (0, 0, 0, 0))
    size, r_hole = 15, 1.6
    mask = gear_mask(size, teeth=6, r_body=5.2, r_tooth=7.3, r_hole=r_hole, duty=0.5)
    hole_core(art, size, 0, 0, r_hole)
    shade_gear(art, mask, 0, 0, r_hole)
    return art


GLYPH = ["01110", "10001", "00001", "00110", "00100", "00000", "00100"]  # "?"


def make_placeholder():
    art = Image.new("RGBA", (16, 16), (0, 0, 0, 255))
    px = art.load()
    for y in range(16):
        for x in range(16):
            border = x in (0, 15) or y in (0, 15)
            checker = ((x // 4) + (y // 4)) % 2 == 0
            px[x, y] = (C["brass0"] if border else C["iron3"] if checker else C["iron2"]) + (255,)
    for gy, row in enumerate(GLYPH):
        for gx, bit in enumerate(row):
            if bit == "1":
                px[5 + gx, 4 + gy] = C["brass4"] + (255,)
    return art


def export(art, path):
    art.resize((art.width * 2, art.height * 2), Image.NEAREST).save(path)
    print("wrote", path, art.width * 2, "x", art.height * 2)


if __name__ == "__main__":
    export(make_icon(), "icon.png")
    export(make_small_icon(), "icon_small.png")
    export(make_placeholder(), "Assets/Textures/Placeholder.png")
