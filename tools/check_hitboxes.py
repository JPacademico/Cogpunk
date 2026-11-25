"""Hitboxes against their art (user, 2026-11-25: "verify hitboxes and make sure they match the sprites"; memory: art-matched
hitboxes). For every NPC class that sets `NPC.width` / `NPC.height` from numbers the tool can resolve, and whose sheet it can
read, the opaque bounds of its frames next to the hitbox placed where the game places it:

* grid sheets (`GridWalkerNPC` and the bosses: a RigData with CellWidth, CellHeight, OriginX, OriginY, Frames and maybe
  Columns): the cell's origin is the hitbox's bottom centre (`DepthLayers.DrawCell`); the far, middle and near planes
  (<Name>_Far.png, <Name>.png, <Name>_Near.png) are merged;
* vertical frame sheets (`Main.npcFrameCount`): vanilla's placement, the frame centred on the hitbox and its bottom 4 px
  under the hitbox's (decompiled `Main.DrawNPCDirect`), shown as "vanilla" (an NPC with its own PreDraw may differ).

A line is flagged when the hitbox, against the median frame's bounds (so walk cycles and squash-and-stretch average out),
is wider or taller than the art by more than TOO_BIG (hits
landing on air), smaller than TOO_SMALL of it (hits passing through the body: fine for wings and tails, so it is a "check"
and doesn't fail), or when less than COVER of the hitbox lies on the art's bounds.

    python -P tools/check_hitboxes.py [--png OUT] [--only NAME]

Projectiles turn, so one fails only when its hitbox is bigger than its sprite's longest side.

`--png` writes every checked NPC's first frame at 2x with its hitbox outlined (red) and the median frame's bounds (cyan).
Exit 1 when an NPC fails.
"""
import argparse
import glob
import os
import re
import sys

from PIL import Image, ImageDraw

ROOT = os.getcwd()
TOO_BIG = 1.12          # hitbox / art, either axis
TOO_SMALL = 0.5
COVER = 0.85            # share of the hitbox inside the art's bounds

CONST_RE = re.compile(r"const\s+(?:int|float)\s+([^;]+);")
PROP_RE = re.compile(r"(?:protected|public)\s+override\s+int\s+(\w+)\s*=>\s*([^;]+);")
ANCHOR_RE = re.compile(r"override\s+Vector2\s+DrawAnchor\s*=>\s*([^;]+);")
VEC_RE = re.compile(r"new\s+Vector2\(([^,]+),([^)]+)\)")


def consts_in(text):
    out = {}
    for m in CONST_RE.finditer(text):
        for part in m.group(1).split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def evaluate(expr, names, depth=0):
    """A C# constant expression of ints, names and + - * /, or None."""
    if expr is None or depth > 8:
        return None
    e = expr.strip().rstrip("f")
    e = re.sub(r"\b\w+RigData\.", "", e)
    e = re.sub(r"\bR\.", "", e)
    e = e.replace("Math.Max", "max").replace("Math.Min", "min").replace("(int)", "")

    def sub(m):
        name = m.group(0)
        if name in ("max", "min"):
            return name
        if name in names:
            v = evaluate(names[name], names, depth + 1)
            return "None" if v is None else repr(v)
        return "None"

    e = re.sub(r"[A-Za-z_]\w*", sub, e)
    if "None" in e or not re.fullmatch(r"[0-9.+\-*/() ,maxin]*", e):
        return None
    try:
        v = eval(e, {"__builtins__": {}}, {"max": max, "min": min})
    except Exception:
        return None
    return v


def class_blocks(text):
    """(name, base, body) for each class in a file."""
    heads = list(re.finditer(r"class\s+(\w+)\s*:\s*([\w.<>]+)", text))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        yield m.group(1), m.group(2), text[m.start():end]


def rig_files(path, body):
    names = set(re.findall(r"\b(\w+RigData)\b", body))
    alias = re.search(r"using\s+R\s*=\s*([\w.]+);", open(path, encoding="utf-8").read())
    if alias:
        names.add(alias.group(1).split(".")[-1])
    found = []
    for n in names:
        found += glob.glob(os.path.join(ROOT, "Content", "**", n + ".cs"), recursive=True)
    return found


def median(values):
    s = sorted(values)
    return s[len(s) // 2]


def frame_boxes(layout, images, frames, cw, ch, cols, pad):
    """The cell rectangle of every frame."""
    out = []
    for k in range(frames):
        if layout == "grid":
            col, row = k % cols, k // cols
            out.append((col * (cw + pad), row * (ch + pad), col * (cw + pad) + cw, row * (ch + pad) + ch))
        else:
            out.append((0, k * ch, cw, k * ch + ch))
    return out


def opaque_bounds(images, box):
    """The union of the opaque pixels' bounds inside `box` over the images, relative to the box, or None."""
    x0, y0, x1, y1 = box
    best = None
    for im in images:
        if x1 > im.width or y1 > im.height:
            continue
        bb = im.crop(box).getchannel("A").getbbox()
        if bb is None:
            continue
        best = bb if best is None else (min(best[0], bb[0]), min(best[1], bb[1]), max(best[2], bb[2]), max(best[3], bb[3]))
    return best


def check(path, name, base, body, filetext):
    names = consts_in(filetext)
    for rf in rig_files(path, body):
        names.update({k: v for k, v in consts_in(open(rf, encoding="utf-8").read()).items() if k not in names})
    props = dict(PROP_RE.findall(body))
    wm = re.search(r"NPC\.width\s*=(?!=)\s*(?:NPC\.height\s*=(?!=)\s*)?([^;]+);", body)
    hm = re.search(r"NPC\.height\s*=(?!=)\s*([^;]+);", body)
    if not wm:
        return None
    w = evaluate(wm.group(1), names)
    h = evaluate(hm.group(1), names) if hm else w
    if "NPC.width = NPC.height" in body:
        h = w
    if w is None or h is None:
        return {"name": name, "skip": "hitbox from runtime values (%s x %s)" % (wm.group(1).strip(), hm.group(1).strip() if hm else "")}
    folder = os.path.dirname(path)
    tex = re.search(r'override\s+string\s+Texture\s*=>\s*"Cogpunk/([^"]+)"', body)
    stem = os.path.join(ROOT, tex.group(1)) if tex else os.path.join(folder, name)
    planes = [p for p in (stem + "_Far.png", stem + ".png", stem + "_Near.png") if os.path.exists(p)]
    if not planes:
        return {"name": name, "skip": "no sheet found"}
    images = [Image.open(p).convert("RGBA") for p in planes]

    def prop(key, default=None):
        if key in props:
            return evaluate(props[key], names)
        return evaluate(key, names) if key in names else default

    cw, ch, ox, oy = prop("CellWidth"), prop("CellHeight"), prop("OriginX"), prop("OriginY")
    am = ANCHOR_RE.search(body)
    anchor = am.group(1).strip() if am else "NPC.Bottom"
    # the sheets face left: a facing ternary takes its left-facing branch, a per-frame one its usual (last) branch
    anchor = re.sub(r"NPC\.spriteDirection\s*==\s*1\s*\?\s*([^:]+?)\s*:\s*([^,)]+)", lambda m: m.group(2), anchor)
    if "?" in anchor:
        anchor = anchor.rsplit(":", 1)[1].strip()
    if None not in (cw, ch, ox, oy):
        cols = prop("Columns", 1) or 1
        pad = prop("CellPadding", 2)
        frames = prop("FrameCount", None) or prop("Frames", 1) or 1
        layout = "grid"
        origin = (ox, oy)
        boxes = frame_boxes("grid", images, int(frames), cw, ch, int(cols), pad)
    else:
        fc = re.search(r"npcFrameCount\[Type\]\s*=\s*([^;]+);", body)
        n = evaluate(fc.group(1), names) if fc else None
        if rig_files(path, body) and (n is None or n == 1):
            return {"name": name, "skip": "drawn from a rig without a cell grid: check by hand"}
        if not n:
            return {"name": name, "skip": "frame count not readable"}
        fw, fh = images[0].width, images[0].height // int(n)
        layout = "vanilla"
        origin = (fw / 2, fh - 4)
        boxes = frame_boxes("vanilla", images, int(n), fw, fh, 1, 0)
    # where the hitbox sits against the origin: the bottom centre (the default), or a DrawAnchor of NPC.Center/NPC.Bottom
    # plus a constant vector
    ax = ay = 0.0
    vm = VEC_RE.search(anchor)
    if vm:
        ax, ay = evaluate(vm.group(1), names), evaluate(vm.group(2), names)
        if ax is None or ay is None:
            return {"name": name, "skip": "DrawAnchor not readable: " + anchor}
    if anchor.startswith("NPC.Center"):
        hit = (origin[0] - ax - w / 2, origin[1] - ay - h / 2, origin[0] - ax + w / 2, origin[1] - ay + h / 2)
    elif anchor.startswith("NPC.Bottom"):
        hit = (origin[0] - ax - w / 2, origin[1] - ay - h, origin[0] - ax + w / 2, origin[1] - ay)
    else:
        return {"name": name, "skip": "DrawAnchor not readable: " + anchor}
    bounds = [b for b in (opaque_bounds(images, bx) for bx in boxes) if b is not None]
    if not bounds:
        return {"name": name, "skip": "empty frames"}
    box = boxes[0]
    bb = tuple(sum(b[i] for b in bounds) / len(bounds) for i in range(4))   # the mean frame (walk cycles, squash and stretch)
    hx0, hy0, hx1, hy1 = hit
    aw, ah = bb[2] - bb[0], bb[3] - bb[1]
    ix = max(0.0, min(hx1, bb[2]) - max(hx0, bb[0]))
    iy = max(0.0, min(hy1, bb[3]) - max(hy0, bb[1]))
    cover = ix * iy / max(1.0, w * h)
    rw, rh = w / aw, h / ah
    verdict = "ok"
    notes = []
    if rw > TOO_BIG or rh > TOO_BIG:
        verdict = "FAIL"
        notes.append("hitbox bigger than the art")
    if cover < COVER:
        verdict = "FAIL"
        notes.append("%.0f%% of the hitbox on the art" % (cover * 100))
    if os.environ.get("HB_DEBUG"):
        print(name, "bb", tuple(round(v, 1) for v in bb), "hit", hit, "origin", origin, "anchor", anchor)
    if verdict == "ok" and (rw < TOO_SMALL or rh < TOO_SMALL):
        verdict = "check"
        notes.append("hitbox under half the art (wings, tails, weapons?)")
    if anchor != "NPC.Bottom":
        notes.append("anchor " + anchor)
    return {"name": name, "w": w, "h": h, "aw": aw, "ah": ah, "rw": rw, "rh": rh, "cover": cover, "verdict": verdict,
            "notes": notes, "layout": layout, "images": images, "box": box, "bb": bb, "hit": (hx0, hy0, hx1, hy1),
            "path": os.path.relpath(path, ROOT)}


def check_projectile(path, name, body, filetext):
    """A projectile's hitbox against its sprite: projectiles turn, so only a hitbox bigger than the sprite's longest side
    (bigger than the sprite in every rotation) fails."""
    names = consts_in(filetext)
    for rf in rig_files(path, body):
        names.update({k: v for k, v in consts_in(open(rf, encoding="utf-8").read()).items() if k not in names})
    wm = re.search(r"Projectile\.width\s*=\s*(?:Projectile\.height\s*=\s*)?([^;]+);", body)
    hm = re.search(r"Projectile\.height\s*=\s*([^;]+);", body)
    if not wm or "Projectile.hide = true" in body or re.search(r"CanDamage\(\)\s*=>\s*false", body):
        return None                                        # invisible, or harmless (its hitbox never touches anything)
    w = evaluate(wm.group(1), names)
    h = evaluate(hm.group(1), names) if hm else w
    if "Projectile.width = Projectile.height" in body:
        h = w
    if w is None or h is None:
        return {"name": name, "skip": "hitbox from runtime values"}
    tex = re.search(r'override\s+string\s+Texture\s*=>\s*"Cogpunk/([^"]+)"', body)
    png = (os.path.join(ROOT, tex.group(1)) if tex else os.path.join(os.path.dirname(path), name)) + ".png"
    if not os.path.exists(png):
        return {"name": name, "skip": "no sprite (drawn by code or another texture)"}
    im = Image.open(png).convert("RGBA")
    fm = re.search(r"projFrames\[Type\]\s*=\s*([^;]+);", body)
    n = int(evaluate(fm.group(1), names) or 1) if fm else 1
    fh = im.height // max(1, n)
    bounds = [b for b in (im.crop((0, k * fh, im.width, k * fh + fh)).getchannel("A").getbbox() for k in range(n)) if b]
    if not bounds:
        return {"name": name, "skip": "empty sprite"}
    aw = sum(b[2] - b[0] for b in bounds) / len(bounds)
    ah = sum(b[3] - b[1] for b in bounds) / len(bounds)
    longest = max(aw, ah)
    verdict = "FAIL" if (w > longest * TOO_BIG + 2 or h > longest * TOO_BIG + 2) else "ok"
    if verdict == "FAIL" and re.search(r"override\s+bool\?\s+Colliding", body):
        return {"name": name, "skip": "its own Colliding shape: check by hand"}
    return {"name": name, "w": w, "h": h, "aw": aw, "ah": ah, "verdict": verdict, "path": os.path.relpath(path, ROOT)}


def montage(rows, out):
    tiles = []
    for r in rows:
        if "skip" in r:
            continue
        x0, y0, x1, y1 = r["box"]
        cell = Image.new("RGBA", (x1 - x0, y1 - y0), (40, 40, 48, 255))
        for im in r["images"]:
            cell.alpha_composite(im.crop(r["box"]))
        big = cell.resize((cell.width * 2, cell.height * 2), Image.NEAREST)
        d = ImageDraw.Draw(big)
        bb = r["bb"]
        d.rectangle([bb[0] * 2, bb[1] * 2, bb[2] * 2 - 1, bb[3] * 2 - 1], outline=(80, 220, 240, 255))
        hx0, hy0, hx1, hy1 = r["hit"]
        d.rectangle([hx0 * 2, hy0 * 2, hx1 * 2 - 1, hy1 * 2 - 1], outline=(240, 60, 60, 255), width=2)
        label = Image.new("RGBA", (max(big.width, 180), big.height + 16), (20, 20, 24, 255))
        label.alpha_composite(big, (0, 16))
        ImageDraw.Draw(label).text((2, 2), "%s %s" % (r["name"], r["verdict"]), fill=(230, 230, 230))
        tiles.append(label)
    if not tiles:
        return
    width = 1600
    x = y = rowh = 0
    placed = []
    for t in tiles:
        if x + t.width > width:
            x, y, rowh = 0, y + rowh + 8, 0
        placed.append((t, x, y))
        x += t.width + 8
        rowh = max(rowh, t.height)
    sheet = Image.new("RGBA", (width, y + rowh), (10, 10, 12, 255))
    for t, px, py in placed:
        sheet.alpha_composite(t, (px, py))
    sheet.save(out)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png")
    ap.add_argument("--only")
    a = ap.parse_args()
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "Content", "**", "*.cs"), recursive=True)):
        text = open(path, encoding="utf-8").read()
        if "NPC.width" not in text:
            continue
        for name, base, body in class_blocks(text):
            if "NPC.width" not in body or (a.only and a.only != name):
                continue
            r = check(path, name, base, body, text)
            if r:
                rows.append(r)
    projectiles = []
    for path in sorted(glob.glob(os.path.join(ROOT, "Content", "**", "*.cs"), recursive=True)):
        text = open(path, encoding="utf-8").read()
        if "Projectile.width" not in text:
            continue
        for name, base, body in class_blocks(text):
            if "Projectile.width" not in body or (a.only and a.only != name):
                continue
            r = check_projectile(path, name, body, text)
            if r:
                projectiles.append(r)
    fails = 0
    for r in rows:
        if "skip" in r:
            print("%-22s skipped: %s" % (r["name"], r["skip"]))
            continue
        fails += r["verdict"] == "FAIL"
        print("%-22s %-5s %-7s hitbox %3dx%-3d art %3dx%-3d  w %.2f  h %.2f  on art %3.0f%%  %s" % (
            r["name"], r["verdict"], r["layout"], r["w"], r["h"], r["aw"], r["ah"], r["rw"], r["rh"], r["cover"] * 100,
            "; ".join(r["notes"])))
    pfails = 0
    for r in projectiles:
        if "skip" in r or r["verdict"] == "ok":
            continue
        pfails += 1
        print("%-22s FAIL  projectile hitbox %3dx%-3d sprite %3.0fx%-3.0f (bigger than the sprite turned any way)" % (
            r["name"], r["w"], r["h"], r["aw"], r["ah"]))
    if a.png:
        montage(rows, a.png)
    print("NPCs: %d checked, %d failed; projectiles: %d checked, %d failed, %d skipped" % (
        sum("skip" not in r for r in rows), fails, sum("skip" not in r for r in projectiles), pfails,
        sum("skip" in r for r in projectiles)))
    fails += pfails
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
