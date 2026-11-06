"""The game's thin smoke trails (Core/Visuals/SmokeTrails.cs, 2026-11-05) for the D5 simulations: a shot adds the
segment it flew each tick, every segment lives LifeTicks ticks on its own, drawn as a line of 2x2 squares on the 2 px
grid that drift up and break up as they fade (the same constants, parsed from the C# file)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trashtr0m_loot_sim import consts  # noqa: E402

KT = consts("Core/Visuals/SmokeTrails.cs")
LIFE = KT.get("LifeTicks", 30)
RISE = 0.12
MAX_SEGMENT = 160.0


class Smoke:
    def __init__(self, tint=(195, 200, 205)):
        self.segments = []
        self.tint = tint
        self.n = 0

    def add(self, a, b, tick, tint=None):
        if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > MAX_SEGMENT ** 2 or a == b:
            return
        self.n += 1
        self.segments.append((a, b, tick, tint or self.tint, (self.n * 37) & 255))

    def draw(self, img, tick):
        px = img.load()
        w, h = img.size
        keep = []
        for (a, b, born, tint, seed) in self.segments:
            age = tick - born
            if age >= LIFE:
                continue
            keep.append((a, b, born, tint, seed))
            life = 1.0 - age / LIFE
            alpha = 0.75 * life * life + 0.1 * life
            share = 0.35 + life
            dx, dy = b[0] - a[0], b[1] - a[1]
            steps = max(1, int(max(abs(dx), abs(dy)) / 2))
            rise = age * RISE
            for k in range(steps):
                if ((k * 73 + seed * 19 + age * 3) & 15) / 16.0 > share:
                    continue
                x = int((a[0] + dx * k / steps) // 2) * 2
                y = int((a[1] + dy * k / steps - rise) // 2) * 2
                for (ox, oy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if 0 <= x + ox < w and 0 <= y + oy < h:
                        r, g, bb, aa = px[x + ox, y + oy]
                        px[x + ox, y + oy] = (int(r + (tint[0] - r) * alpha), int(g + (tint[1] - g) * alpha),
                                              int(bb + (tint[2] - bb) * alpha), aa)
        self.segments = keep
