"""Native 1x Jade Fox art, hand-authored to the supplied small fox reference.
The face, long ruff, slender paws and sweeping tail use explicit pixel clusters.
All exports are 2x nearest-neighbour. The tail has an independent 16-frame cycle.
"""
import argparse
import math
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oldbrasstown"))
sys.path.insert(0, os.path.join(HERE, "..", "bosses", "trashtr0m"))
from westbots import RAMP, Xf, Ellipse, Canvas, dome, finish
from make_trashtr0m_art import export

OUT = "Content/Coghaven/Pets/"
GH, G, E, S = (RAMP[k] for k in ("ghost", "gilt", "emerald", "sage"))
CHARS = "ABCDEFGabcdef0123456789"
COLOUR = dict(zip(CHARS, E + S + G))
FOX = (
    "............................A.......",
    "...........................AA.......",
    "..........................AEa......A",
    "......AAAA...............AAEea....AA",
    "........AEA...............Abee...ADa",
    ".....AAAGFA...............AbfeaafECa",
    "...AAGGGGFA...............AbedcaEDCa",
    "..AGGFFFFGA..............aebddcfeEca",
    ".AGGFFFFFFGA............aebdffffEfa.",
    ".AGFFFFFFFDDA...........aebdffffEfa.",
    "..AGfffffffDGA..........aefaaaffffa.",
    "..AGffeefEDDDFA.........affGACffffa.",
    "...aeeeedEEDDEEA........afedffcfeaa.",
    "...aedddDEEEDEEA...aaaaaedeeefeda...",
    "...aeddDEEEEDDEEA.aeefdddddeeedda...",
    "....addDEEEEDDEEAaeffffffdeeeddda...",
    "....acbCEEEEDDEBBceefffdddeefddda...",
    ".....aGFFEEDDECCfefffdddeeffeedca...",
    ".....AFEEEBBEEDBdceeedddeeaffddca...",
    "......aFEEEcbEbfefddddddeeeeddcca...",
    ".......AAEEbdccadddddBbbee7dBBEa....",
    ".........Aaaeca.adaaBbAAadecbbAA....",
    "............aA..ed..aA...aefca......",
    "................ea..aC...aefca......",
    "...............aefa.aDa...aefea.....",
    "................aa...aa...aaaaa.....",
)
FOX = tuple(row.ljust(36,'.') for row in FOX)
CELL_W, CELL_H, SX, SY, OX = 40, 32, 2, 6, 26
FRAMES, TAIL_FRAMES = 21, 16
BODY_OFFSETS = (0,0,1,1, 0,1,0,-1,0,1, 0,-1,-1,0, 1,2,2,2,2,1,0)
PARTS = {k:{} for k in ("tail","body","head","HN","HF","FN","FF")}
for y,row in enumerate(FOX):
    for x,c in enumerate(row):
        if c==".": continue
        if y>=22: part="HN" if x<20 else "HF" if x<25 else "FN" if x<30 else "FF"
        elif x<16: part="tail"
        elif x>=25 and y<14: part="head"
        else: part="body"
        PARTS[part][x,y]=c

def leg_pose(part,shift,lift):
    if not part: return {}
    top=min(y for x,y in part)
    bottom=max(y for x,y in part)
    return {(x+round(shift*(y-top)/max(1,bottom-top)),y-lift):c for (x,y),c in part.items()}

def body_pixels(frame):
    bob=BODY_OFFSETS[frame]
    tucked=10<=frame<14
    lying=15<=frame<=18
    sleep=frame in (16,17)
    out={}
    for k in ("HF","FF","HN","FN"):
        shift=lift=0
        if 4<=frame<10:
            phase=(frame-4)/6*math.tau + (math.pi if k in ("HF","FN") else 0)
            shift=round(1.5*math.sin(phase))
            lift=int(math.cos(phase)>.2)
        if tucked: shift=-1 if k.startswith("F") else 1; lift=2
        part=leg_pose(PARTS[k],shift,lift)
        if lying:
            bottom=max(y for x,y in part)
            part={(x+1,y):c for (x,y),c in part.items() if y==bottom and k.startswith("F")}
        out.update(part)
    for k in ("body","head"):
        out.update({(x,y+bob):c for (x,y),c in PARTS[k].items()})
    if sleep:
        for x in (27,28,29):
            out[x,11+bob]="a"
            out[x,10+bob]="e"
            out[x,12+bob]="f"
    return out

def tail_pixels(frame):
    # A fixed root at the rump and a delayed distal curve keep the attachment stable.
    phase=frame/TAIL_FRAMES*math.tau
    out={}
    for (x,y),c in PARTS["tail"].items():
        weight=max(0,min(1,(16-x)/16))
        dy=round(2.2*math.sin(phase-weight*.7)*weight)
        dx=round(.75*math.sin(phase+.7)*weight*weight)
        out[x+dx,y+dy]=c
    return out

def pixel_image(pixels,glow=False):
    im=Image.new("RGBA",(CELL_W,CELL_H))
    for (x,y),c in pixels.items():
        xx,yy=x+SX,y+SY
        if not (0<=xx<CELL_W and 0<=yy<CELL_H):
            raise ValueError((x,y,c))
        if not glow or (x,y) in ((27,11),(28,11)) and c in "GFC":
            im.putpixel((xx,yy),COLOUR[c]+(255,))
    return im

def sheet(tail=False,glow=False):
    count=TAIL_FRAMES if tail else FRAMES
    out=Image.new("RGBA",(CELL_W,(CELL_H+1)*count))
    for frame in range(count):
        pixels=tail_pixels(frame) if tail else body_pixels(frame)
        out.alpha_composite(pixel_image(pixels,glow),(0,frame*(CELL_H+1)))
    return out

def fox_frame(frame,tail_frame):
    image=Image.new("RGBA",(CELL_W,CELL_H))
    tail=pixel_image(tail_pixels(tail_frame))
    image.alpha_composite(tail,(0,BODY_OFFSETS[frame]))
    image.alpha_composite(pixel_image(body_pixels(frame)))
    return image

def token():
    """The Jade Token: a round jade coin, a gilt rim lit top-left, a fox's head in relief on its face."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(7.0, 7.0, 6.6, 6.6), "gilt", dome(5.0, 5.0, 7.0, lo=3, hi=8, gain=1.3, fixed=True), rust=0.0)
    cv.part(Xf(), Ellipse(7.0, 7.0, 5.0, 5.0), "ghost", dome(5.6, 5.4, 6.0, lo=1, hi=4, gain=1.2, fixed=True), rust=0.0, outline=False)
    head = ((5, 4, GH[5]), (8, 4, GH[5]), (5, 5, GH[4]), (6, 5, GH[4]), (7, 5, GH[4]), (8, 5, GH[4]), (5, 6, GH[4]), (6, 6, GH[0]),
            (7, 6, GH[4]), (8, 6, GH[0]), (6, 7, GH[4]), (7, 7, GH[4]), (6, 8, GH[3]), (7, 8, GH[2]), (4, 3, GH[4]), (9, 3, GH[3]))
    finish(cv)
    for (x, y, c) in head:                                      # the relief, stamped after the finish (small details)
        cv.put(x, y, c)
    return cv


def boxed(cv, w, h, dx=0, dy=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    xs, ys = [x for x, _ in cv.px], [y for _, y in cv.px]
    ox = (w - (max(xs) - min(xs) + 1)) // 2 - min(xs) + dx
    oy = (h - (max(ys) - min(ys) + 1)) // 2 - min(ys) + dy
    for (x, y), c in cv.px.items():
        if 0 <= x + ox < w and 0 <= y + oy < h:
            im.putpixel((x + ox, y + oy), tuple(c) + (255,))
    return im


def buff_icon():
    face=pixel_image(body_pixels(0)).crop((25,5,39,22))
    out=Image.new("RGBA",(16,16))
    out.alpha_composite(face,(1,0))
    return out

def outputs():
    return {OUT+"JadeFoxPet.png":sheet(),
            OUT+"JadeFoxPet_Glow.png":sheet(glow=True),
            OUT+"JadeFoxPet_Tail.png":sheet(tail=True),
            OUT+"JadeToken.png":boxed(token(),14,14),
            OUT+"JadeFoxBuff.png":buff_icon()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview")
    args=parser.parse_args()
    for name,im in outputs().items(): export(im,name)
    if args.preview:
        out=Image.new("RGB",(640,448),(34,36,43))
        for i in range(21):
            im=fox_frame(i,(i*2)%16).resize((120,96),Image.Resampling.NEAREST)
            out.paste(im,((i%5)*128,(i//5)*88),im)
        out.save(args.preview)

if __name__=="__main__": main()
