"""D5 preview of an armor set worn by a stand-in player, replaying vanilla's frame mapping (reusable for any armor).

    python -P tools/sim/armor_preview.py --head <X_Head.png> --body <X_Body.png> --legs <X_Legs.png> \
        --out docs/media/<date>_<area>-<set>.gif [--png docs/media/<...>.png] [--anim-frames 4 --anim-ticks 6] \
        [--back <X_Back.png>] [--skin] [--female]

Equip-texture animation frames are picked up as <sheet>_1.png .. <sheet>_<n-1>.png (see Core/Visuals/AnimatedEquip).

Replayed from decompiled tModLoader v2026.08.3.0:
* PlayerDrawSet.CreateCompositeData: which body-sheet cell is the torso, the shoulders and the front/back arm for each of
  the 20 player animation frames, and whether the front shoulder draws over the front arm.
* PlayerDrawLayers.DrawPlayer_17_TorsoComposite / _28_ArmOverItemComposite / _12_SkinComposite_BackArmShirt: every
  composite body part (torso, shoulders, both arms) is offset by Main.OffsetsPlayerHeadgear[frame].Y - 2, i.e. lifted
  2 px in walk frames 7-9 and 14-16. The head and leg sheets carry that bob in their own frames and are drawn unshifted.
  (PlayerDrawSet.cs's `Position -= OffsetsPlayerHeadgear` is inside HeadOnlySetup, the map-icon path, not the body.)
* Draw order: back arm, legs, torso, back shoulder, head, then front arm / front shoulder.
* Shoulders are hidden in the jump frame (ArmorIDs.Body.Sets.showsShouldersWhileJumping is false for modded bodies).
* --female: the torso and both shoulders come from rows 2-3 of the body sheet (CreateCompositeData: pt.Y += 2 when not
  Male); the arms are the same for both.
* --back (2026-10-30): a back equip such as a body's cape (ArmorIDs.Body.Sets.IncludedCapeBack), a 20-frame 40x56 strip
  drawn behind everything (the BackAcc layer comes before Skin) with the body frame, centred like the body
  (DrawPlayer_10_BackAcc: (width/2, height - 28 - 4 + 8) = the torso's centre); it carries the walk bob in its frames.
* --skin (2026-10-30): a stand-in skin body (copper tones) cut from the template's full-coverage masks (torso, the arm
  cells of the frame, the legs), drawn where vanilla draws the wearer's skin under armor that leaves it bare
  (HidesTopSkin / HidesBottomSkin false, HidesHands false).

Leaves out: lighting, dyes, rotated item-use arms (cols 7-8), hair, the real skin sprite (a plain stand-in face is
drawn under the helmet), and walk-speed-dependent frame timing (fixed 3 ticks per walk frame).
"""
import argparse
import json
import os
from PIL import Image, ImageDraw

FW, FH = 40, 56                                    # one player frame in the 2x textures
HEADGEAR_OFFSET = [2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 2, 2, 2]   # Main.OffsetsPlayerHeadgear (Y)

# CreateCompositeData: body frame -> (front arm cell, front shoulder drawn over the front arm)
FRONT_ARM = {0: ((2, 0), True), 1: ((3, 0), False), 2: ((4, 0), False), 3: ((5, 0), True), 4: ((6, 0), True),
             5: ((2, 1), False), 6: ((3, 1), True)}
for _f in (7, 8, 9, 10):
    FRONT_ARM[_f] = ((4, 1), True)
for _f in (11, 12, 13, 18, 19):
    FRONT_ARM[_f] = ((3, 1), True)
for _f in (14, 17):
    FRONT_ARM[_f] = ((5, 1), True)
for _f in (15, 16):
    FRONT_ARM[_f] = ((6, 1), True)


def load_frames(path, n):
    base, ext = os.path.splitext(path)
    out = [Image.open(path).convert("RGBA")]
    for i in range(1, n):
        alt = f"{base}_{i}{ext}"
        out.append(Image.open(alt).convert("RGBA") if os.path.exists(alt) else out[0])
    return out


def cell(sheet, col, row):
    return sheet.crop((col * FW, row * FH, col * FW + FW, row * FH + FH))


def strip_frame(sheet, f):
    return sheet.crop((0, f * FH, FW, f * FH + FH))


def stand_in_head(bob):
    """Plain face under the helmet (preview only): skin block with an eye, at the vanilla head position."""
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 2 * bob
    d.rectangle([14, 10 + y, 29, 25 + y], fill=(196, 104, 58, 255))      # art x 7..14, y 5..12
    d.rectangle([24, 18 + y, 27, 19 + y], fill=(238, 241, 243, 255))
    d.rectangle([26, 18 + y, 27, 19 + y], fill=(21, 22, 28, 255))
    return img


_LAYOUT = None
SKIN = ((147, 68, 31, 255), (196, 104, 58, 255), (233, 160, 107, 255))   # stand-in skin: outline, body, lit


def _layout():
    global _LAYOUT
    if _LAYOUT is None:
        _LAYOUT = json.load(open(os.path.join(os.getcwd(), "art/templates/armor_layout.json"), encoding="utf-8"))
    return _LAYOUT


def skin_from_mask(mask):
    """A 1x template mask as a 2x stand-in skin layer: outlined, lit on its top-left pixels."""
    img = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    inside = {(x, y) for y, row in enumerate(mask) for x, ch in enumerate(row) if ch == "#"}
    d = ImageDraw.Draw(img)
    for (x, y) in inside:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lit = (x - 1, y) not in inside or (x, y - 1) not in inside
        col = SKIN[2] if (lit and not edge) else (SKIN[0] if edge else SKIN[1])
        d.rectangle([x * 2, y * 2, x * 2 + 1, y * 2 + 1], fill=col)
    return img


def skin_cell(col, row):
    mask = _layout()["body_cells"].get("%d,%d" % (col, row))
    return skin_from_mask(mask) if mask else Image.new("RGBA", (FW, FH), (0, 0, 0, 0))


def compose(head, body, legs, frame, bob, back=None, skin=False, female=False):
    img = Image.new("RGBA", (FW, FH + 4), (0, 0, 0, 0))
    base = 2                                       # canvas margin so a lifted part never leaves the image
    lift = HEADGEAR_OFFSET[frame] - 2              # composite parts: 0, or -2 px in frames 7-9 / 14-16
    (fa_col, fa_row), shoulder_over = FRONT_ARM[frame]
    g = 2 if female else 0                         # female torso and shoulders: rows 2-3
    torso = (1, g) if frame == 5 else (0, g)
    layers = []
    if back is not None:
        layers.append((strip_frame(back, frame), 0))            # the cape, behind everything
    if skin:
        layers.append((skin_cell(fa_col, fa_row + 2), lift))    # the back arm's skin
    layers.append((cell(body, fa_col, fa_row + 2), lift))       # back arm
    if skin:
        layers.append((skin_from_mask(_layout()["legs"][frame]), 0))
    layers.append((strip_frame(legs, frame), 0))
    if skin:
        layers.append((skin_cell(*torso), lift))
    layers.append((cell(body, *torso), lift))
    if frame != 5:
        layers.append((cell(body, 1, 1 + g), lift))             # back shoulder
    layers += [(stand_in_head(bob[frame]), 0), (strip_frame(head, frame), 0)]
    front_arm = [(cell(body, fa_col, fa_row), lift)]
    if skin:
        front_arm.insert(0, (skin_cell(fa_col, fa_row), lift))
    front_shoulder = [(cell(body, 0, 1 + g), lift)] if frame != 5 else []
    layers += (front_arm + front_shoulder) if shoulder_over else (front_shoulder + front_arm)
    for layer, dy in layers:
        img.alpha_composite(layer, (0, base + dy))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--legs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--png")
    ap.add_argument("--anim-frames", type=int, default=1)
    ap.add_argument("--anim-ticks", type=int, default=6)
    ap.add_argument("--zoom", type=int, default=3)
    ap.add_argument("--head-bob", default="0,0,0,0,0,0,0,-1,-1,-1,0,0,0,0,-1,-1,-1,0,0,0")
    ap.add_argument("--back")
    ap.add_argument("--skin", action="store_true")
    ap.add_argument("--female", action="store_true")
    a = ap.parse_args()
    bob = [int(v) for v in a.head_bob.split(",")]

    heads = load_frames(a.head, a.anim_frames)
    bodies = load_frames(a.body, a.anim_frames)
    legs = load_frames(a.legs, a.anim_frames)
    back = Image.open(a.back).convert("RGBA") if a.back else None
    extra = dict(back=back, skin=a.skin, female=a.female)

    # Timeline in game ticks: idle, a walk cycle (3 ticks/frame) twice, a jump, an item swing (6 ticks/frame).
    timeline = [0] * 60 + [f for _ in range(2) for f in range(6, 20) for _t in range(3)] + [5] * 30
    timeline += [f for f in (1, 2, 3, 4) for _t in range(6)] + [0] * 24
    backgrounds = [((30, 30, 36), "cavern"), ((150, 180, 210), "sky")]
    pad = 8
    W = (FW + pad * 2) * len(backgrounds)
    H = FH + pad * 2 + 12
    gif = []
    for tick, frame in enumerate(timeline):
        if tick % 3:
            continue
        anim = (tick // a.anim_ticks) % a.anim_frames
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        d = ImageDraw.Draw(canvas)
        for i, (bg, _name) in enumerate(backgrounds):
            x0 = i * (FW + pad * 2)
            d.rectangle([x0, 0, x0 + FW + pad * 2 - 1, H - 1], fill=bg)
            d.rectangle([x0, pad + FH + 2, x0 + FW + pad * 2 - 1, H - 1], fill=(91, 54, 38))
            canvas.alpha_composite(compose(heads[anim], bodies[anim], legs[anim], frame, bob, **extra), (x0 + pad, pad))
        d.text((2, H - 11), f"frame {frame:2d}  cog {anim}", fill=(238, 241, 243))
        gif.append(canvas.convert("RGB").resize((W * a.zoom, H * a.zoom), Image.NEAREST))
    gif[0].save(a.out, save_all=True, append_images=gif[1:], duration=50, loop=0)
    print(f"{a.out}: {len(gif)} frames, {len(timeline) / 60:.1f} s")

    if a.png:   # static sheet: idle with every cog frame, plus walk/jump/use poses (cog frame 0)
        poses = [(0, n) for n in range(a.anim_frames)] + [(f, 0) for f in (6, 8, 10, 13, 15, 5, 2, 4)]
        sheet = Image.new("RGBA", ((FW + 4) * len(poses), (FH + 8) * 2), (0, 0, 0, 255))
        for i, (frame, anim) in enumerate(poses):
            for j, (bg, _name) in enumerate(backgrounds):
                tile = Image.new("RGBA", (FW + 4, FH + 8), bg + (255,))
                tile.alpha_composite(compose(heads[anim], bodies[anim], legs[anim], frame, bob, **extra), (2, 2))
                sheet.alpha_composite(tile, (i * (FW + 4), j * (FH + 8)))
        sheet.resize((sheet.width * a.zoom, sheet.height * a.zoom), Image.NEAREST).save(a.png)
        print(f"{a.png}: {len(poses)} poses")


if __name__ == "__main__":
    main()
