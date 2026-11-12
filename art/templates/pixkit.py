"""Pixel kit for hand-built item, projectile and prop sprites (D4), 2026-11-11.

A material map at 1x: each pixel holds a ramp (a tuple of colours from art/palettes/cogpunk.gpl, darkest first) and a
shade index into it. Parts are painted with plain shapes or ASCII rows, then `outline()` gives the silhouette its
ramp-coloured outline (D4 rule 3: the darkest shade of the material it bounds, a step lighter where the only open sides
face the light, top and left), and `image()` / `export()` write the sprite (2x nearest-neighbour, D4 rule 1).
Stamps (glints, rivets, sparkles) go on after the outline, so it doesn't eat them.

    from pixkit import Pix, export, sheet
    p = Pix(28, 14)
    p.rect(13, 4, 22, 8, STEEL, 5)
    p.outline()
    export(p.image(), "Content/.../Thing.png")
"""
import os

from PIL import Image

ROOT = os.getcwd()
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Pix:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.m = {}                          # (x, y) -> (ramp, index)
        self.locked = set()                  # pixels the outline pass leaves alone

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def put(self, x, y, ramp, i, lock=False):
        if not self.inside(x, y):
            return
        ramp = tuple(tuple(c) for c in ramp)
        self.m[(x, y)] = (ramp, max(0, min(len(ramp) - 1, int(i))))
        if lock:
            self.locked.add((x, y))
        else:
            self.locked.discard((x, y))

    def get(self, x, y):
        return self.m.get((x, y))

    def clear(self, x, y):
        self.m.pop((x, y), None)
        self.locked.discard((x, y))

    def rect(self, x0, y0, x1, y1, ramp, i, lock=False):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, ramp, i, lock)

    def rows(self, x0, y0, rows, key, lock=False):
        """ASCII rows: each character maps through `key` to (ramp, index); characters not in it (' ', '.') are skipped."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in key and key[ch] is not None:
                    ramp, i = key[ch]
                    self.put(x0 + dx, y0 + dy, ramp, i, lock)

    def shift(self, x, y, d):
        """A pixel a shade lighter (d > 0) or darker (d < 0) in its own ramp."""
        q = self.m.get((x, y))
        if q:
            self.m[(x, y)] = (q[0], max(0, min(len(q[0]) - 1, q[1] + d)))

    def outline(self, lit=True, skip=()):
        """Silhouette pixels (a 4-neighbour empty) take their ramp's darkest shade; with `lit`, one whose open sides all
        face the light (up, left) takes the next one. Ramps in `skip` keep their colours (glass, glows)."""
        changes = {}
        for (x, y), (ramp, i) in self.m.items():
            if (x, y) in self.locked or ramp in skip:
                continue
            open_ = [d for d in SIDES if (x + d[0], y + d[1]) not in self.m]
            if not open_:
                continue
            changes[(x, y)] = (ramp, 1 if lit and all(d in ((-1, 0), (0, -1)) for d in open_) else 0)
        self.m.update(changes)

    def image(self):
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = img.load()
        for (x, y), (ramp, i) in self.m.items():
            px[x, y] = tuple(ramp[i]) + (255,)
        return img

    def colours(self):
        return {ramp[i] for ramp, i in self.m.values()}


def export(img, rel):
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    big = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    big.save(out)
    print("wrote %s (%dx%d)" % (rel, big.width, big.height))


def sheet(frames, pad=1):
    """Equal frames stacked vertically, `pad` px (1x) under each (2 px at 2x, D4 rule 8)."""
    w, h = frames[0].size
    out = Image.new("RGBA", (w, (h + pad) * len(frames)), (0, 0, 0, 0))
    for k, im in enumerate(frames):
        out.alpha_composite(im, (0, k * (h + pad)))
    return out


def preview(images, path, scale=4, bgs=((30, 30, 36), (196, 214, 232)), gap=8):
    """Each image at `scale` over a dark and a light background (D4: readable on both)."""
    w = sum(im.width * scale + gap for im in images) + gap
    h = max(im.height for im in images) * scale + 2 * gap
    out = Image.new("RGBA", (w, h * len(bgs)), (0, 0, 0, 255))
    for row, bg in enumerate(bgs):
        band = Image.new("RGBA", (w, h), bg + (255,))
        out.alpha_composite(band, (0, row * h))
        x = gap
        for im in images:
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            out.alpha_composite(big, (x, row * h + gap))
            x += big.width + gap
    out.save(path)
    print("wrote", path)
