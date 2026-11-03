"""Source for the Coghawk, a Cogpunk enemy of the desert (D4), 2026-11-03. Run from the repo root:

    python -P art/desert/make_coghawk_art.py [--preview FILE]

Design (user, 2026-11-03: "a new enemy for the desert called Coghawk that attacks with a quick swoop, a bit stronger than
the vulture"): a hawk of riveted brass and iron built round a cog. A barrel of a torso with a brass cog turning in its
chest, a brass head with an iron hooked beak and one ember eye (hostile), a fan of three iron tail plates, iron talons,
and wings of riveted iron plates on a brass spar. Three-quarter view facing left (D4 rule 13), lit from the top-left.

Three planes (DepthLayers.DrawWalker grid sheets, like the Mech Army's machines): far (the far wing, a ramp step darker),
middle (head, torso, tail, talons), near (the near wing); the glow sheet holds the eye. Stable pixels (D4 rule 17): the
body only moves by whole pixels in the flap loop and is lit in its own space (fixed); the wings turn about their
shoulder and are lit in 45-degree steps (snap); the cog spins by half a tooth a frame (two states, D4 rule 17).

Frames: Flap x4 (wings up, level, down, level), Glide (spread, level), Screech x2 (the swoop's telegraph: wings flared
high, head back, beak open; a shudder between the two), Dive (pitched down, wings swept back), Skim (level at the
bottom of the swoop, talons thrown forward, wings half back), Climb (pitched up, wings beating down).

Outputs:
    Content/Desert/NPCs/Coghawk.png, Coghawk_Far.png, Coghawk_Near.png, Coghawk_Glow.png   grid sheets
    Content/Desert/NPCs/CoghawkRigData.cs                                                 cells, origin, frames
    Content/Desert/Gores/Coghawk_GoreHead.png, Coghawk_GoreWing.png, Coghawk_GoreCog.png
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "mecharmy"))
from rig import RAMP, WHITE, Xf, Poly, Ellipse, Capsule, Ring, Union, box, Canvas, flat, dome, cyl, face, rivet, line  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402
from make_mecharmy_art import fit_cell, grid_layer  # noqa: E402

ROOT = os.getcwd()
OUT = "Content/Desert/"
I, B, C, E, S = (RAMP[k] for k in ("iron", "brass", "copper", "ember", "steam"))

BODY_C = (1.0, -8.0)                                      # the torso's centre (rig space, origin = hitbox bottom centre)
SHOULDER = (0.0, -11.0)                                   # where the wings join (in the body's own space: relative to BODY_C)
WING_LEN = 15.0


def P(xf, p):
    x, y = xf.fwd(p)
    return int(math.floor(x)), int(math.floor(y))


def despeckle(cv):
    changes = {}
    for (x, y), col in cv.px.items():
        if (x, y) in cv.glow:
            continue
        nb = [cv.px.get((x + 1, y)), cv.px.get((x - 1, y)), cv.px.get((x, y + 1)), cv.px.get((x, y - 1))]
        if None in nb or col in nb:
            continue
        changes[(x, y)] = max(set(nb), key=nb.count)
    cv.px.update(changes)


class Pose:
    def __init__(self, pitch=0.0, bob=0, wing=0.0, sweep=0.0, head=0.0, beak=0.0, talons=0.0, cog=0):
        self.pitch = pitch          # degrees, + = nose up (the art faces left: a clockwise turn on screen lifts the head)
        self.bob = bob              # whole px, + = down
        self.wing = wing            # degrees the wing is raised (90 = straight up, 0 = level back, -40 = down)
        self.sweep = sweep          # 0 spread .. 1 swept back along the body (a dive)
        self.head = head            # degrees the head is thrown back (the screech)
        self.beak = beak            # 0 shut .. 1 open
        self.talons = talons        # 0 tucked .. 1 thrown forward (the strike)
        self.cog = cog              # the chest cog's turn step (0-3)


# ================================================================================================
# Wing: a broad membrane of riveted iron plates under a brass spar, a scalloped trailing edge of primaries
# ================================================================================================
def wing_shape(L):
    """The wing in its own space: the spar along +x from the shoulder (x back, y down = the trailing side)."""
    return Poly([(0.0, -1.8), (L * 0.45, -2.8), (L, -1.4), (L - 0.4, 0.4), (L - 1.8, 1.0), (L - 2.4, 2.6), (L - 4.0, 2.8),
                 (L - 4.6, 4.4), (L - 6.4, 4.4), (L - 7.0, 5.8), (L - 9.0, 5.6), (L - 9.6, 6.6), (L - 11.6, 6.0), (1.6, 5.4),
                 (0.0, 3.6)])


def wing(cv, root, pose, depth):
    """Raised `pose.wing` degrees about the shoulder (up = anticlockwise on screen: the art faces left and the wing
    points back), folded towards the tail by `pose.sweep`. The plates face the viewer (3/4 view), lit in 45-degree steps
    as the wing turns (D4 rule 17); feather seams run from the spar to the scallops."""
    L = WING_LEN * (1.0 - 0.3 * pose.sweep)
    ang = -pose.wing + 16.0 * pose.sweep
    xf = Xf.pose(ang, (0.0, 0.0), root)
    shape = wing_shape(L)
    inner = cv.part(xf, shape, "iron", face((0.0, -0.35, 0.94), lo=2, hi=4, gain=1.1, bias=0.25, snap=45), depth=depth, rust=0.0)
    for k, (a, b) in enumerate((((L * 0.30, -1.6), (L * 0.22, 5.0)), ((L * 0.50, -2.2), (L * 0.42, 5.6)),
                                ((L * 0.68, -2.0), (L - 7.6, 5.4)), ((L * 0.84, -1.6), (L - 4.8, 3.8)))):
        line(cv, xf, a, b, lambda n: I[max(1, 2 - depth)], inner)       # the seams between the plates
    spar = cv.part(xf, Capsule((0.0, -0.6), (L - 0.6, -1.4), 1.5, 0.8), "brass",
                   cyl((0.0, -0.6), (L - 0.6, -1.4), 1.5, lo=2, hi=5, gain=1.3, snap=45), depth=depth, rust=0.0)
    for t in (0.25, 0.6):
        q = P(xf, (L * t, 0.9))
        if q in inner:
            cv.put(q[0], q[1], I[max(1, 4 - depth)])                     # rivets under the spar
    return inner | spar


# ================================================================================================
# Body: torso with the chest cog, head, beak, eye, tail plates, talons
# ================================================================================================
def chest_cog(cv, xf, c, r, step, depth):
    """A brass cog: eight teeth turned by whole steps of a 4-step cycle, a dark hub, lit in its own space."""
    teeth = Union(*[Poly([(c[0] + math.cos(a - 0.24) * r, c[1] + math.sin(a - 0.24) * r),
                          (c[0] + math.cos(a - 0.17) * (r + 1.2), c[1] + math.sin(a - 0.17) * (r + 1.2)),
                          (c[0] + math.cos(a + 0.17) * (r + 1.2), c[1] + math.sin(a + 0.17) * (r + 1.2)),
                          (c[0] + math.cos(a + 0.24) * r, c[1] + math.sin(a + 0.24) * r)])
                    for a in (math.radians(k * 45.0 + step * 11.25) for k in range(8))])
    gear = Union(Ellipse(c[0], c[1], r, r), teeth)
    inner = cv.part(xf, gear, "brass", dome(c[0] - 1.0, c[1] - 1.2, r * 1.6, lo=3, hi=5, gain=1.3, bias=0.15, fixed=True), depth=depth, rust=0.0)
    hub = P(xf, c)
    cv.put(hub[0], hub[1], B[1])
    cv.put(hub[0] + 1, hub[1], B[2])
    return inner


def body(mid, glow, pose):
    bx = Xf.pose(pose.pitch, BODY_C, (0.0, float(pose.bob)))    # pitch about the torso's centre (+ clockwise = nose up); whole-pixel bob
    cx, cy = BODY_C
    # tail: three iron plates fanned behind (right)
    for k, (a, l) in enumerate(((-16.0, 8.0), (0.0, 9.5), (16.0, 7.5))):
        txf = bx.then(Xf.pose(a, (cx + 5.0, cy - 0.6)))
        mid.part(txf, Poly([(cx + 4.4, cy - 1.8), (cx + 4.4 + l, cy - 1.6), (cx + 5.4 + l, cy - 0.4), (cx + 4.6 + l, cy + 1.0),
                            (cx + 4.4, cy + 0.8)]),
                 "iron", face((0.0, -0.45, 0.9), lo=2, hi=4, bias=0.2 - 0.12 * k, fixed=True), rust=0.0)
    # talons (thrown forward on the strike): a brass shank, three iron hooks
    for side, dx in ((1, 1.8), (0, -1.0)):
        hip = bx.fwd((cx + dx, cy + 3.4))
        reach = pose.talons
        foot = (hip[0] - 1.0 - 5.0 * reach, hip[1] + 3.6 - 1.6 * reach)
        mid.part(Xf(), Capsule(hip, foot, 0.9, 0.8), "brass", flat(3 if side else 4), rust=0.0)
        for k in range(3):
            a = math.radians(115.0 + k * 32.0 - 45.0 * reach)
            tip = (foot[0] + math.cos(a) * 2.2, foot[1] + math.sin(a) * 1.8)
            line(mid, Xf(), foot, tip, lambda n: I[3] if n == 0 else I[2])
            mid.put(int(round(tip[0])), int(round(tip[1])), I[0])
    # the torso: a barrel of riveted iron lit on its back, a brass breastplate round the cog, a seam along its back
    torso = mid.part(bx, Ellipse(cx, cy, 7.0, 4.6), "iron", dome(cx - 2.2, cy - 2.8, 8.0, lo=2, hi=4, gain=1.35, bias=0.3, fixed=True),
                     shadow=(1, 1), rust=0.0)
    plate = mid.part(bx, Ellipse(cx - 3.4, cy + 1.6, 3.6, 2.8), "copper", dome(cx - 4.4, cy + 0.4, 4.4, lo=1, hi=3, gain=1.2, bias=0.1, fixed=True),
                     rust=0.0)                               # a copper breast plate under the cog
    chest_cog(mid, bx, (cx - 3.6, cy + 1.4), 2.3, pose.cog, 0)
    for t in range(0, 6):                                    # the seam along its back
        q = P(bx, (cx + t, cy - 3.2))
        if q in torso and q not in plate:
            mid.put(q[0], q[1], I[1])
            if (q[0], q[1] + 1) in torso:
                mid.put(q[0], q[1] + 1, I[4] if t % 2 == 0 else I[3])
    for p in ((cx + 2.4, cy - 1.8), (cx + 4.8, cy - 0.6)):
        rivet(mid, bx, p, "iron", torso)
    # the head: thrown back by pose.head about the neck
    neck = (cx - 5.4, cy - 2.6)
    hx = bx.then(Xf.pose(pose.head, neck))
    hc = (cx - 7.4, cy - 4.6)
    head = mid.part(hx, Ellipse(hc[0], hc[1], 3.8, 3.2), "brass", dome(hc[0] - 1.4, hc[1] - 1.4, 4.6, lo=2, hi=5, gain=1.35, bias=0.1, fixed=True),
                    shadow=(1, 1), rust=0.0)
    # the hooked beak: an iron upper mandible curling down to a point, a lower one that drops open
    gape = 22.0 * pose.beak
    lo_xf = hx.then(Xf.pose(-gape, (hc[0] - 2.6, hc[1] + 1.0)))
    mid.part(lo_xf, Poly([(hc[0] - 2.4, hc[1] + 0.8), (hc[0] - 5.6, hc[1] + 1.4), (hc[0] - 5.2, hc[1] + 2.4), (hc[0] - 2.4, hc[1] + 2.2)]),
             "iron", flat(2), rust=0.0)
    mid.part(hx, Poly([(hc[0] - 2.6, hc[1] - 1.6), (hc[0] - 6.0, hc[1] - 0.8), (hc[0] - 7.6, hc[1] + 0.6), (hc[0] - 7.2, hc[1] + 2.4),
                       (hc[0] - 6.2, hc[1] + 1.2), (hc[0] - 2.6, hc[1] + 1.0)]),
             "iron", face((-0.35, -0.6, 0.72), lo=2, hi=4, gain=1.2, fixed=True), rust=0.0)
    # the eye: an ember lens in a dark socket under an angry brow (glow sheet)
    e = P(hx, (hc[0] - 1.2, hc[1] - 0.8))
    mid.put(e[0] - 1, e[1], I[0])
    for (dx, dy, col) in ((0, 0, E[3]), (1, 0, E[2]), (0, 1, E[2]), (1, 1, E[1])):
        mid.put_glow(e[0] + dx, e[1] + dy, col)
        glow.put_glow(e[0] + dx, e[1] + dy, col)
    for k in range(5):
        q = P(hx, (hc[0] - 2.6 + k, hc[1] - 2.4 + (0.8 if k < 2 else 0.0)))
        if q in head:
            mid.put(q[0], q[1], B[0])
    for k, (dx, l) in enumerate(((1.6, 3.6), (0.4, 2.8))):   # a crest of two iron plates swept back off the crown
        cxf = hx.then(Xf.pose(-18.0 - 14.0 * k, (hc[0] + dx, hc[1] - 2.4)))
        mid.part(cxf, Poly([(hc[0] + dx, hc[1] - 3.2), (hc[0] + dx + l, hc[1] - 2.8), (hc[0] + dx + l + 0.8, hc[1] - 2.0),
                            (hc[0] + dx, hc[1] - 1.8)]), "iron", flat(3 - k), rust=0.0)
    q = P(hx, (hc[0] + 1.0, hc[1] - 2.0))
    if q in head:
        mid.put(q[0], q[1], WHITE)                           # a glint on the brass crown
    return bx


def frame(pose):
    far, mid, near, glow = Canvas(), Canvas(), Canvas(), Canvas()
    bx = body(mid, glow, pose)
    root = bx.fwd((BODY_C[0] + SHOULDER[0], BODY_C[1] + SHOULDER[1] + 7.0))
    wing(far, (root[0] + 1.5, root[1] - 0.5), pose, 1)
    wing(near, root, pose, 0)
    for cv in (far, mid, near):
        despeckle(cv)
    return far, mid, near, glow


FLAP = [Pose(wing=72.0, bob=0, cog=0), Pose(wing=18.0, bob=0, cog=2), Pose(wing=-34.0, bob=1, cog=0), Pose(wing=12.0, bob=1, cog=2)]   # the cog spins in half-tooth steps
FRAMES = ([("Flap%d" % k, p) for k, p in enumerate(FLAP)] + [
    ("Glide", Pose(wing=6.0)),
    ("Screech0", Pose(wing=96.0, head=-22.0, beak=1.0, talons=0.3, pitch=6.0)),
    ("Screech1", Pose(wing=88.0, head=-18.0, beak=0.8, talons=0.3, pitch=6.0, bob=-1)),
    ("Dive", Pose(pitch=-32.0, wing=24.0, sweep=1.0, talons=0.2)),
    ("Skim", Pose(pitch=0.0, wing=10.0, sweep=0.6, talons=1.0, beak=0.6)),
    ("Climb", Pose(pitch=26.0, wing=-30.0, sweep=0.2, talons=0.4)),
])
INDEX = {n: k for k, (n, _) in enumerate(FRAMES)}


# ================================================================================================
def crop(px):
    xs = [x for (x, _) in px]
    ys = [y for (_, y) in px]
    x0, y0 = min(xs), min(ys)
    return to_image(px, x0, y0, max(xs) - x0 + 1, max(ys) - y0 + 1)


def gores():
    far, mid, near, glow = frame(dict(FRAMES)["Glide"])
    head_x = BODY_C[0] - 5.6
    out = {"Coghawk_GoreHead": crop({q: c for q, c in mid.px.items() if q[0] <= head_x}),
           "Coghawk_GoreWing": crop(near.px),
           "Coghawk_GoreCog": None}
    cv = Canvas()
    chest_cog(cv, Xf(), (4.0, 4.0), 2.6, 0, 0)
    out["Coghawk_GoreCog"] = crop(cv.px)
    return out


def write_rig(path, cell):
    w, h, ox, oy = cell
    L = ["// <auto-generated> by art/desert/make_coghawk_art.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Desert.NPCs",
         "{",
         "\t/// <summary>The Coghawk's grid sheets (game px, left-facing): far, middle, near planes and the glow, equal cells with",
         "\t/// 2 px under each; the origin is the hitbox's bottom centre.</summary>",
         "\tpublic static class CoghawkRigData",
         "\t{",
         "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d;" % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES)),
         "\t\tpublic const int Flap = %d, FlapFrames = %d, Glide = %d, Screech = %d, ScreechFrames = 2, Dive = %d, Skim = %d, Climb = %d;"
         % (INDEX["Flap0"], len(FLAP), INDEX["Glide"], INDEX["Screech0"], INDEX["Dive"], INDEX["Skim"], INDEX["Climb"]),
         "\t}",
         "}"]
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", path)


def export_all():
    frames = [frame(p) for _, p in FRAMES]
    cell = fit_cell([fr[:3] for fr in frames])
    for suffix, idx in (("_Far", 0), ("", 1), ("_Near", 2)):
        export(grid_layer([fr[idx] for fr in frames], cell), OUT + "NPCs/Coghawk%s.png" % suffix)
    export(grid_layer([fr[3] for fr in frames], cell, glow=True), OUT + "NPCs/Coghawk_Glow.png")
    write_rig(OUT + "NPCs/CoghawkRigData.cs", cell)
    for name, im in gores().items():
        export(im, OUT + "Gores/" + name + ".png")


def preview(path):
    cw, ch = 60, 44
    out = Image.new("RGBA", (cw * 5, ch * 2), (36, 40, 48, 255))
    light = Image.new("RGBA", (cw * 5, ch * 2), (200, 170, 120, 255))
    for k, (n, p) in enumerate(FRAMES):
        far, mid, near, _ = frame(p)
        tile = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        for cv in (far, mid, near):
            tile.alpha_composite(to_image(cv.px, -cw // 2, -ch + 6, cw, ch))
        out.alpha_composite(tile, ((k % 5) * cw, (k // 5) * ch))
        light.alpha_composite(tile, ((k % 5) * cw, (k // 5) * ch))
    both = Image.new("RGBA", (cw * 5, ch * 4))
    both.alpha_composite(out, (0, 0))
    both.alpha_composite(light, (0, ch * 2))
    both = both.resize((both.width * 4, both.height * 4), Image.NEAREST)
    both.save(path)
    print("preview", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    else:
        export_all()
