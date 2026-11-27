"""D5 visual proof generator for the 0.3.0 early-game progression update (2026-11-27).

Produces:
  1. docs/media/2026-11-27_early-progression-items.png     (2x/4x sprite inspection sheet over dark & light backgrounds)
  2. docs/media/2026-11-27_early-progression-showcase.gif  (4-panel animated simulation using real sprites & C# constants)

Note: Offline Pillow simulation replaying C# constants and compositing actual exported PNG sheets (omits Terraria dynamic
tile lighting and netcode).
"""
import math
import os
import random
from PIL import Image, ImageDraw

ROOT = os.getcwd()


def load(rel):
    return Image.open(os.path.join(ROOT, rel)).convert("RGBA")


def scale_nn(im, factor):
    return im.resize((im.width * factor, im.height * factor), Image.NEAREST)


def make_static_sheet():
    items = [
        ("Sparkler", load("Content/Mechanist/Weapons/Sparkler.png")),
        ("Flintsword", load("Content/Scrap/Weapons/Flintsword.png")),
        ("Hand-made Gun", load("Content/Scrap/Weapons/HandMadeGun.png")),
        ("Spare Helmet", load("Content/Scrap/Armor/SpareHelmet.png")),
        ("Spare Vest", load("Content/Scrap/Armor/SpareVest.png")),
        ("Spare Boots", load("Content/Scrap/Armor/SpareBoots.png")),
        ("Ore GPS", load("Content/Research/Items/OreGps.png")),
        ("Driller Extractor", load("Content/Research/Items/DrillerExtractor.png")),
    ]
    # Also composite worn Spare Armor (frame 0 idle)
    head_sh = load("Content/Scrap/Armor/SpareHelmet_Head.png")
    body_sh = load("Content/Scrap/Armor/SpareVest_Body.png")
    legs_sh = load("Content/Scrap/Armor/SpareBoots_Legs.png")
    worn = Image.new("RGBA", (40, 56), (0, 0, 0, 0))
    worn.alpha_composite(body_sh.crop((80, 112, 120, 168)), (0, 0))
    worn.alpha_composite(legs_sh.crop((0, 0, 40, 56)), (0, 0))
    worn.alpha_composite(body_sh.crop((0, 0, 40, 56)), (0, 0))
    worn.alpha_composite(head_sh.crop((0, 0, 40, 56)), (0, 0))
    worn.alpha_composite(body_sh.crop((80, 0, 120, 56)), (0, 0))
    worn.alpha_composite(body_sh.crop((0, 56, 40, 112)), (0, 0))
    items.append(("Spare Set (Worn)", worn))

    cols = len(items)
    cell_w, cell_h = 124, 124
    w = 20 + cols * (cell_w + 8)
    h = 24 + 2 * (cell_h + 12) + 20
    sheet = Image.new("RGBA", (w, h), (18, 18, 24, 255))
    draw = ImageDraw.Draw(sheet)

    for row, bg in enumerate(((28, 28, 38, 255), (192, 212, 230, 255))):
        for col, (label, sp) in enumerate(items):
            x0 = 14 + col * (cell_w + 8)
            y0 = 16 + row * (cell_h + 24)
            box = Image.new("RGBA", (cell_w, cell_h), bg)
            zoomed = scale_nn(sp, 2)
            bx = (cell_w - zoomed.width) // 2
            by = (cell_h - zoomed.height) // 2
            box.alpha_composite(zoomed, (bx, by))
            sheet.alpha_composite(box, (x0, y0))
            if row == 1:
                draw.text((x0 + 6, y0 + cell_h + 4), label, fill=(223, 185, 78, 255))

    out_path = os.path.join(ROOT, "docs/media/2026-11-27_early-progression-items.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    print("Saved static sheet:", out_path)


def draw_spark(canvas, x, y, bright=True):
    d = ImageDraw.Draw(canvas)
    ix, iy = int(x) & ~1, int(y) & ~1
    c1 = (255, 199, 90, 255) if bright else (236, 113, 40, 255)
    c2 = (163, 48, 26, 255)
    d.rectangle([ix - 2, iy - 2, ix + 1, iy + 1], fill=c1)
    d.rectangle([ix - 4, iy, ix - 3, iy + 1], fill=c2)


def make_showcase_gif():
    sparkler = load("Content/Mechanist/Weapons/Sparkler.png")
    flintsword = load("Content/Scrap/Weapons/Flintsword.png")
    trail_sh = load("Content/Scrap/Weapons/FlintswordTrail.png")
    hmgun = load("Content/Scrap/Weapons/HandMadeGun.png")
    bullet_sh = load("Content/Scrap/Weapons/HandMadeBullet.png")
    ore_gps = load("Content/Research/Items/OreGps.png")
    drill_item = load("Content/Research/Items/DrillerExtractor.png")
    drill_sh = load("Content/Research/Items/DrillerExtractorProjectile.png")
    drill_gl = load("Content/Research/Items/DrillerExtractorProjectile_Glow.png")
    arrow_sh = load("Content/Junkyard/Map/MysteriousMapArrow.png")
    arrow_gl = load("Content/Junkyard/Map/MysteriousMapArrow_Glow.png")
    cog_icon = load("Content/Scrap/Items/RustedCog.png")
    scrap_tile = load("Content/Scrap/Items/RustedScrap.png")

    head_frames = [load(f"Content/Scrap/Armor/SpareHelmet_Head{'' if i == 0 else f'_{i}'}.png") for i in range(4)]
    body_frames = [load(f"Content/Scrap/Armor/SpareVest_Body{'' if i == 0 else f'_{i}'}.png") for i in range(4)]
    legs_frames = [load(f"Content/Scrap/Armor/SpareBoots_Legs{'' if i == 0 else f'_{i}'}.png") for i in range(4)]

    def composite_player(cog_idx):
        p = Image.new("RGBA", (40, 56), (0, 0, 0, 0))
        b, h, l = body_frames[cog_idx], head_frames[cog_idx], legs_frames[cog_idx]
        p.alpha_composite(b.crop((80, 112, 120, 168)), (0, 0))
        p.alpha_composite(l.crop((0, 0, 40, 56)), (0, 0))
        p.alpha_composite(b.crop((0, 0, 40, 56)), (0, 0))
        p.alpha_composite(h.crop((0, 0, 40, 56)), (0, 0))
        p.alpha_composite(b.crop((80, 0, 120, 56)), (0, 0))
        p.alpha_composite(b.crop((0, 56, 40, 112)), (0, 0))
        return p

    players = [composite_player(i) for i in range(4)]

    pw, ph = 300, 170
    W, H = pw * 2 + 12, ph * 2 + 12
    n_frames = 48  # 48 frames at 60 ms (~3 ticks/frame) = 2.88 s seamless loop

    frames_out = []
    for f in range(n_frames):
        tick = f * 3
        cog_f = (tick // 8) % 4
        canvas = Image.new("RGBA", (W, H), (14, 15, 20, 255))
        draw = ImageDraw.Draw(canvas)

        # ---------------- Panel 1 (Top-Left): Sparkler 4-spark burst + Spare Armor hurt burst ----------------
        p1 = Image.new("RGBA", (pw, ph), (26, 24, 34, 255))
        d1 = ImageDraw.Draw(p1)
        d1.rectangle([0, 134, pw, ph], fill=(46, 50, 59, 255))
        d1.rectangle([0, 134, pw, 136], fill=(127, 135, 148, 255))
        hurt_flash = 24 <= f <= 27
        pl = players[cog_f]
        p1.alpha_composite(pl, (44, 78))
        p1.alpha_composite(sparkler, (66, 98))
        if hurt_flash:
            d1.rectangle([44, 78, 84, 134], outline=(236, 113, 40, 255), width=2)
        # Sparkler 4-shot burst (fires at f=0 and f=16)
        shot_t = (f % 16) * 3
        if shot_t < 36:
            for k in range(4):
                ang = math.radians(-12 + k * 8)
                sx = 104 + math.cos(ang) * shot_t * 4.2
                sy = 106 + math.sin(ang) * shot_t * 4.2 + 0.04 * (shot_t ** 2)
                if sx < pw - 6:
                    draw_spark(p1, sx, sy, bright=(k % 2 == 0))
        # Spare Armor 5-spark burst when hurt at f=24..40
        if f >= 24:
            ht = (f - 24) * 3
            if ht < 42:
                for k in range(5):
                    ang = -math.pi * 0.82 + (k / 4.0) * (math.pi * 0.64)
                    sx = 64 + math.cos(ang) * ht * 3.4
                    sy = 96 + math.sin(ang) * ht * 3.4 + 0.06 * (ht ** 2)
                    if 4 < sx < pw - 4 and 4 < sy < 132:
                        draw_spark(p1, sx, sy, bright=True)
        d1.text((8, 6), "Sparkler (4x spark) + Spare Set", fill=(223, 185, 78, 255))
        canvas.alpha_composite(p1, (4, 4))

        # ---------------- Panel 2 (Top-Right): Flintsword directional slash + Hand-made Gun bounce/whiff ----------------
        p2 = Image.new("RGBA", (pw, ph), (26, 24, 34, 255))
        d2 = ImageDraw.Draw(p2)
        d2.rectangle([0, 134, pw, ph], fill=(46, 50, 59, 255))
        d2.rectangle([268, 36, 286, 134], fill=(79, 85, 98, 255))  # wall to bounce off
        p2.alpha_composite(pl, (28, 78))
        # Flintsword phantom crescent + spark on dummy in first half, Hand-made Gun in second half
        d2.rectangle([118, 90, 142, 134], fill=(138, 93, 34, 255), outline=(43, 26, 14, 255))
        if f < 24:
            u = (f % 12) / 11.0
            tf = min(7, int(u * 8))
            cres = trail_sh.crop((0, tf * 90, 96, tf * 90 + 88))
            p2.alpha_composite(cres, (48, 36))
            p2.alpha_composite(flintsword, (54, 56 + int(u * 26)))
            if 5 <= (f % 12) <= 11:
                st = ((f % 12) - 5) * 3
                draw_spark(p2, 132 + st * 3.5, 102 - st * 1.4 + 0.08 * (st ** 2), True)
            d2.text((8, 6), "Flintsword: trail + hit spark", fill=(223, 185, 78, 255))
        else:
            p2.alpha_composite(hmgun, (54, 96))
            gt = f - 24
            if gt < 14:
                # Precise bullet bounces off wall at x=268
                dist = gt * 18
                if dist <= 178:
                    bx, by, hd = 90 + dist, 102, 0
                else:
                    over = dist - 178
                    bx, by, hd = 268 - over, 102 - int(over * 0.45), 9
                bcell = bullet_sh.crop((0, hd * 14, 12, hd * 14 + 12))
                p2.alpha_composite(bcell, (int(bx) - 6, int(by) - 6))
            else:
                # 10% whiff spark!
                wt = (gt - 14) * 3
                draw_spark(p2, 92 + wt * 2.8, 102 - wt * 0.4 + 0.06 * (wt ** 2), False)
                d2.text((86, 78), "whiff!", fill=(236, 122, 88, 255))
            d2.text((8, 6), "Hand-made Gun: bounce + 10% whiff", fill=(223, 185, 78, 255))
        canvas.alpha_composite(p2, (pw + 8, 4))

        # ---------------- Panel 3 (Bottom-Left): Research UI - The Basics Pedestal + Driller Chain ----------------
        p3 = Image.new("RGBA", (pw, ph), (18, 16, 30, 255))
        d3 = ImageDraw.Draw(p3)
        pulse = 0.65 + 0.35 * math.sin(f / n_frames * 2 * math.pi * 2)
        # The Basics at (190, 44)
        bx0, by0 = 186, 34
        halo_c = (int(184 + 54 * pulse), int(138 + 72 * pulse), int(51 + 59 * pulse), 255)
        d3.rectangle([bx0 - 6, by0 - 6, bx0 + 50, by0 + 50], fill=(21, 22, 28, 255), outline=halo_c, width=2)
        d3.rectangle([bx0, by0, bx0 + 44, by0 + 44], fill=(30, 28, 44, 255), outline=(140, 201, 176, 255), width=2)
        # Corner brackets
        for cx, cy in ((bx0 - 8, by0 - 8), (bx0 + 46, by0 - 8), (bx0 - 8, by0 + 46), (bx0 + 46, by0 + 46)):
            d3.rectangle([cx, cy, cx + 6, cy + 6], outline=(238, 210, 110, 255), width=2)
        bounce = int(math.sin(f / n_frames * 2 * math.pi * 2) * 3) & ~1
        ay = by0 + 54 + bounce
        d3.polygon([(bx0 + 22, ay), (bx0 + 14, ay + 8), (bx0 + 30, ay + 8)], fill=(140, 228, 88, 255))
        d3.rectangle([bx0 - 26, ay + 10, bx0 + 70, ay + 28], fill=(21, 22, 28, 255), outline=(140, 228, 88, 255), width=2)
        d3.text((bx0 - 18, ay + 14), "START HERE", fill=(140, 228, 88, 255))

        # Connected 3-node Driller chain: X-Ray -> Driller+ -> Pre-HM Drill?!
        chain = [(118, 118, ore_gps), (64, 118, cog_icon), (10, 118, drill_item)]
        for i in range(len(chain) - 1):
            d3.line([(chain[i][0], 138), (chain[i + 1][0] + 40, 138)], fill=(223, 185, 78, 255), width=2)
        for nx, ny, icon in chain:
            d3.rectangle([nx, ny, nx + 40, ny + 40], fill=(30, 28, 44, 255), outline=(223, 185, 78, 255), width=2)
            ix = nx + (40 - icon.width) // 2
            iy = ny + (40 - icon.height) // 2
            p3.alpha_composite(icon, (ix, iy))
        d3.text((8, 6), "The Basics highlight + Driller chain", fill=(223, 185, 78, 255))
        canvas.alpha_composite(p3, (4, ph + 8))

        # ---------------- Panel 4 (Bottom-Right): Ore GPS arrow (-> 6+ ore vein) + Driller Extractor ----------------
        p4 = Image.new("RGBA", (pw, ph), (24, 22, 30, 255))
        d4 = ImageDraw.Draw(p4)
        d4.rectangle([0, 134, pw, ph], fill=(46, 50, 59, 255))
        # 6-block Gold Ore clump on top-right cavern ceiling (x 236..284, y 28..60)
        vein = [(244, 32), (260, 32), (276, 32), (244, 48), (260, 48), (276, 48)]
        for vx, vy in vein:
            d4.rectangle([vx, vy, vx + 14, vy + 14], fill=(223, 185, 78, 255), outline=(90, 58, 23, 255), width=2)
        d4.text((234, 66), "6+ clump", fill=(140, 228, 88, 255))

        p4.alpha_composite(pl, (46, 78))
        # Mysterious Map / Ore GPS arrow at heading 15 (~top-right)
        hd_arrow = 15
        ar = arrow_sh.crop((0, hd_arrow * 42, 40, hd_arrow * 42 + 40))
        ag = arrow_gl.crop((0, hd_arrow * 42, 40, hd_arrow * 42 + 40))
        p4.alpha_composite(ar, (84, 52))
        if f % 4 < 2:
            p4.alpha_composite(ag, (84, 52))

        # Spinning Driller Extractor mining Rusted Scrap blocks & popping cogs/coins!
        spin = f % 3
        dcell = drill_sh.crop((0, spin * 54, 52, spin * 54 + 52))
        dgcell = drill_gl.crop((0, spin * 54, 52, spin * 54 + 52))
        p4.alpha_composite(dcell, (68, 82))
        p4.alpha_composite(dgcell, (68, 82))
        # Rusted Scrap pocket in front of drill
        for sy in (86, 102, 118):
            for sx in (122, 138):
                if not (sx == 122 and sy == 102 and (f % 16) > 8):
                    p4.alpha_composite(scrap_tile, (sx, sy))
        # Extracted cog & gold coin popping out when block breaks!
        et = (f % 16)
        if et >= 6:
            dt = et - 6
            p4.alpha_composite(cog_icon, (int(124 + dt * 2.5), int(94 - dt * 2.8 + 0.35 * (dt ** 2))))
            d4.rectangle([136 + dt * 2, int(88 - dt * 3 + 0.35 * (dt ** 2)),
                          142 + dt * 2, int(94 - dt * 3 + 0.35 * (dt ** 2))], fill=(246, 231, 161, 255))
        d4.text((8, 6), "Ore GPS arrow + Driller Extractor", fill=(223, 185, 78, 255))
        canvas.alpha_composite(p4, (pw + 8, ph + 8))

        frames_out.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=128))

    gif_path = os.path.join(ROOT, "docs/media/2026-11-27_early-progression-showcase.gif")
    frames_out[0].save(
        gif_path,
        save_all=True,
        append_images=frames_out[1:],
        duration=60,
        loop=0,
        optimize=False,
    )
    print("Saved showcase GIF:", gif_path, f"({os.path.getsize(gif_path) // 1024} KB)")


if __name__ == "__main__":
    random.seed(300)
    make_static_sheet()
    make_showcase_gif()
