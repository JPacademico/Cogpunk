"""Source for the Fungimancer, the glowing mushroom biome's secret boss, and its things (D4), 2026-11-19. Run from the repo
root:

    python -P art/bosses/fungimancer/make_fungimancer_art.py [--preview FILE]

User, 2026-11-19: "add a new secret boss to the blue mushroom area called "Fungimancer" a magic dumb frog like creature ...
Reference for the design on the example image of the prompt (floaty boss)". The reference (a painting, kept in
reference/fungimancer_user_2026-11-19.png) is redrawn here as pixel art in the Cogpunk palette, its body plan and colours
kept, nothing traced: a fat frog (the cactus ramp) with a pale belly (sage), a wide head with big bulging orange eyes
(ember) on top, slit pupils that look two ways at once (the "dumb" part), a dopey mouth, red frills sweeping back off the
head (crimson) and arms going from green to red hands; it sits on the cap of a floating glowing mushroom (the biome's
blue: denim, violet gills, pale spots that glow), its magic violet (aether).

Three planes (D4 rule 13, drawn with Core/Visuals/DepthLayers): far (the far arm), middle (the seat, the body, the head),
near (the near arm). The art faces left; each frame is a pose of the same parts (no part redrawn, nothing rotated at
runtime). Frames (FungimancerRigData's names):
  Idle 0-3      breathing, a blink on the last
  Cast 4-7      the near hand rises, lights up violet, flings forward, comes back (the spore bolts)
  Croak 8-11    the throat sac swells, holds, croaks (the mushroom bloom), sinks
  Tongue 12-14  the mouth opens wide, stays open (the tongue is drawn by the game), shuts
  Fizzle 15-16  the spell goes wrong: eyes crossed, a dumb open mouth (the dumb moment)
  Intro 17-18   eyes shut, then open (rising out of the spores)
  Death 19-22   it bloats, glowing mushrooms sprout all over it, bloats more (then bursts: gores)

Outputs (Content/Bosses/Fungimancer/):
    Fungimancer.png, _Far.png, _Near.png, _Glow.png    grid sheets (COLUMNS wide), 2 px right of and under each cell
    FungimancerRigData.cs                              cells, frame indices, hitbox, points per frame
    Fungimancer_Head_Boss.png                          the map icon
    Gores/Fungimancer_Gore{Head,Body,Seat}.png
    Projectiles/SporeBolt.png (4 frames), ShroomSpike.png (4 frames), FungimancerTongue.png (the tongue's tip)
    Items/FungimancerBag.png, Items/RainbowMushroom.png, Tiles/RainbowMushroomTile.png (3 styles)
"""
import argparse
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "trashtr0m"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "oldbrasstown"))
from rig import RAMP, Xf, Ellipse, Capsule, Poly, Canvas, dome, texture  # noqa: E402
from westbots import finish, limb  # noqa: E402
from make_trashtr0m_art import export, to_image  # noqa: E402

OUT = "Content/Bosses/Fungimancer/"
COLUMNS = 8
GROUND_CLIP = 2
CA, SA, K, EM, DN, AE, SM, IV = (RAMP[k] for k in ("cactus", "sage", "crimson", "ember", "denim", "aether", "steam", "ivory"))

# --- Reference-based anatomy, drawn at 1x; the carpet's lower edge is the origin. ------------------
SEAT_C, SEAT_R = (0, -8), (51, 11)
BODY_C, BODY_R = (5, -42), (34, 31)
BELLY_C, BELLY_R = (-5, -39), (28, 27)
HEAD_C, HEAD_R = (-7, -89), (30, 17)
EYE_N, EYE_F = (-23, -106, 11), (8, -102, 7)
SHOULDER_N, SHOULDER_F = (-25, -69), (31, -66)
MOUTH = (-31, -84)
SPROUTS = ((-19, -73), (25, -78), (-26, -39), (29, -41), (6, -24), (-4, -110), (19, -60))
GH, AM = RAMP["ghost"], RAMP["amethyst"]


class Pose:
    def __init__(self, near=(-50, -95), far=(31, -52), sac=0., mouth=0., eyes=0., breath=0, bloat=0., shrooms=0,
                 magic=0., curl=0, head=0, finger=0.):
        self.near, self.far = near, far
        self.sac, self.mouth, self.eyes, self.breath = sac, mouth, eyes, breath
        self.bloat, self.shrooms, self.magic = bloat, shrooms, magic
        self.curl, self.head, self.finger = curl, head, finger


def curve(a, b, c, d, count=24):
    return [((1-u)**3*a[0] + 3*(1-u)**2*u*b[0] + 3*(1-u)*u*u*c[0] + u**3*d[0],
             (1-u)**3*a[1] + 3*(1-u)**2*u*b[1] + 3*(1-u)*u*u*c[1] + u**3*d[1])
            for u in (k/count for k in range(count+1))]


def stroke(cv, points, ramp, width, light=3, taper=False):
    """Rasterise a connected ribbon at 1x, with colours fixed to its transverse bands."""
    for k in range(len(points)-1):
        r = width * (1-k/len(points)*.84) if taper else width
        cv.part(Xf(), Capsule(points[k],points[k+1], max(.65,r)), ramp, lambda i: light, rust=0.)
    for k in range(len(points)-1):
        r = width * (1-k/len(points)*.84) if taper else width
        if r > 1.5:
            a,b=points[k],points[k+1]
            cv.part(Xf(), Capsule((a[0]-.6,a[1]-.8),(b[0]-.6,b[1]-.8), max(.5,r*.36)),
                    ramp, lambda i: min(light+1,len(RAMP[ramp])-1), outline=False, rust=0.)


def seat(mid, phase):
    """Teal flying carpet with curled corners, woven borders and violet hanging fringe."""
    wave = round(math.sin(phase*math.tau/12))
    shape = Poly([(-54,-5),(-50,-16),(-42,-18),(39,-17),(50,-10),(54,-4),(37,-6),(23,-3),
                  (4,-5),(-14,-2),(-35,-5)])
    mid.part(Xf(), shape, "ghost", dome(-10,-18,54,lo=1,hi=3,fixed=True,dither=.08),rust=0.)
    stroke(mid,curve((-50,-9),(-22,-2),(17,-7),(49,-7)), "ghost", 2.2, 3)
    for x in range(-41,44,9):
        yy=-9+(x//9%2)
        mid.part(Xf(), Poly([(x,yy-2),(x+3,yy-4),(x+6,yy-1),(x+3,yy+1)]),
                 "ghost",lambda i:2,outline=False,rust=0.)
    for x in range(-44,45,7):
        y=-5+(x//7%2)
        mid.part(Xf(),Poly([(x,y),(x+3,y),(x+2+wave,y+5),(x+wave,y+2)]),
                 "aether",lambda i:2,outline=False,rust=0.)
        mid.put_glow(x+1,y+1,AE[2])
    # The inset jewel anchors the saturated magic against the dark cloth.
    mid.part(Xf(),Ellipse(-37,-10,3.2,3.4),"amethyst",dome(-38,-12,4,lo=1,hi=4,fixed=True),rust=0.)
    mid.put_glow(-38,-12,AM[4])


def spell_curls(far, phase):
    """Two sparsely spaced spirals frame the silhouette without concealing the hands or face."""
    sway = round(2*math.sin(phase*math.tau/12))
    curls=[curve((45,-13),(77,-48),(43,-54),(49,-84)),
           curve((49,-84),(58,-108),(30,-114),(33,-127)),
           curve((33,-127),(41,-142),(66,-126),(47,-124)),
           curve((-48,-22),(-74,-34),(-57,-65),(-63,-78)),
           curve((-63,-78),(-74,-96),(-61,-120),(-47,-119))]
    for n,path in enumerate(curls):
        pp=[(round(x+sway*(n%2)),round(y)) for x,y in path]
        stroke(far,pp,"aether",1.7,2)
    for x,y in ((59,-97),(64,-56),(-60,-45),(28,-130),(-40,-128)):
        far.part(Xf(),Ellipse(x+sway,y,1.4,1.4),"amethyst",lambda i:4,outline=False,rust=0.)


def thigh(mid, at, foot, depth):
    x,y=at
    mid.part(Xf(),Ellipse(x,y,15,13),"cactus",dome(x-5,y-7,18,lo=1,hi=4-depth,fixed=True,dither=.08),rust=0.)
    fx,fy=foot
    limb(mid,(x,y+2),(fx+4,fy-2),5,"cactus",depth,lo=1,hi=4)
    # Broad webbing joins three long toes with round adhesive pads.
    mid.part(Xf(),Poly([(fx+10,fy-6),(fx+7,fy+3),(fx-18,fy+4),(fx-14,fy-2),(fx-7,fy-6)]),
             "crimson",dome(fx-4,fy-5,18,lo=2,hi=5-depth,fixed=True),rust=0.)
    for k in range(3):
        start=(fx+6-k*2,fy-1)
        end=(fx-18+k*6,fy-16+k*8)
        limb(mid,start,end,3.4,"crimson",depth,lo=2,hi=5-depth)
        mid.part(Xf(),Ellipse(end[0],end[1],4.8,3.5),"crimson",
                 dome(end[0]-2,end[1]-2,6,lo=2,hi=5-depth,fixed=True),rust=0.)
        if depth==0:
            mid.put(round(end[0]-2),round(end[1]-2),EM[2])
            mid.put(round(end[0]-1),round(end[1]-2),K[5])


def body(mid, glow, p):
    s=1+.16*p.bloat
    bx,by=BODY_C
    skin=mid.part(Xf(),Ellipse(bx,by,BODY_R[0]*s,BODY_R[1]*s),
                  "cactus",texture(dome(bx-12,by-16,41*s,lo=1,hi=4,gain=1.2,fixed=True,dither=.10),
                                  "pebble",seed=71,density=.25,lo=1,hi=4),rust=0.)
    # Irregular paired mottling remains attached to the torso, using adjacent palette values.
    for x,y in sorted(skin):
        if (x*13+y*7)%67 in (0,1) and mid.get(x,y) in (CA[2],CA[3]):
            mid.put(x,y,CA[3] if mid.get(x,y)==CA[2] else CA[4])
    ex,ey=BELLY_C
    mid.part(Xf(),Ellipse(ex,ey,31*s,27*s+p.breath*.25),
             "ivory",dome(ex-11,ey-14,39*s,lo=2,hi=5,gain=1.15,fixed=True,dither=.16),rust=0.)
    # The lower belly rolls over its seated legs.
    for k in range(3):
        yy=-24+k*3
        for x,y in curve((-25+k*3,yy),(0,yy+5),(19,yy+4),(24-k*4,yy-1),32):
            ix,iy=round(x),round(y)
            if mid.get(ix,iy) in IV[2:]:
                mid.put(ix,iy,IV[2 if k==0 else 3])
                if mid.get(ix,iy-1) in IV[2:]: mid.put(ix,iy-1,IV[4])


def throat(mid,p):
    """The pale drooping throat is asymmetric and folded, broad at the jaw and narrow over the stomach."""
    dy=p.head
    swell=round(p.sac*7)
    verts=(curve((-31-swell,-84+dy),(-18,-91+dy),(7,-88+dy),(14,-78+dy))
           +curve((14,-78+dy),(23+swell,-65),(19+swell,-42),(4,-38))
           +curve((4,-38),(-8,-42),(-26-swell,-48),(-31-swell,-69))
           +curve((-31-swell,-69),(-33-swell,-74),(-33-swell,-79),(-31-swell,-84+dy)))
    mid.part(Xf(),Poly(verts),"ivory",dome(-20,-82,54,lo=2,hi=5,fixed=True,dither=.08),rust=0.)
    folds=[((-27,-79),(-15,-62),(1,-57),(14,-71)),
           ((-25,-75),(-15,-55),(2,-47),(16,-61)),
           ((-22,-64),(-12,-48),(3,-40),(13,-48))]
    for k,(a,b,c,d) in enumerate(folds):
        for x,y in curve(a,b,c,d,30):
            ix,iy=round(x-swell*.3),round(y+dy*.5)
            if mid.get(ix,iy) in IV[2:]:
                mid.put(ix,iy,IV[2 if k==2 else 3])
                if mid.get(ix-1,iy) in IV[2:]: mid.put(ix-1,iy,IV[4])


def head(mid,glow,p):
    dy=p.head
    # Five tapering red frills sweep backward from the crown and cheek.
    frills=[((10,-106),(24,-122),(37,-119),(45,-113)),
            ((15,-99),(37,-111),(40,-106),(50,-103)),
            ((17,-92),(39,-98),(45,-86),(49,-83)),
            ((23,-83),(46,-82),(42,-70),(49,-64)),
            ((8,-111),(12,-128),(27,-128),(32,-124))]
    for a,b,c,d in frills:
        stroke(mid,[(x,y+dy) for x,y in curve(a,b,c,d)],"crimson",3.2,3,True)
    hx,hy=HEAD_C
    hy+=dy
    mid.part(Xf(),Ellipse(hx,hy,HEAD_R[0],HEAD_R[1]),"cactus",
             texture(dome(hx-12,hy-9,36,lo=1,hi=4,gain=1.15,fixed=True,dither=.10),
                     "pebble",seed=29,density=.22,lo=1,hi=4),rust=0.)
    # Wide upper lip with an asymmetrical frown.
    mouth=[(-34,hy+5),(-26,hy+1),(-18,hy),(-7,hy+1),(3,hy+3),(15,hy+7),
           (12,hy+10+p.mouth*4),(-4,hy+6+p.mouth*4),(-23,hy+5+p.mouth*5)]
    mid.part(Xf(),Poly(mouth),"crimson",lambda i:1 if i.ly<hy+4 else 2,rust=0.)
    lip=curve((-35,hy+3),(-23,hy-7),(-6,hy-6),(16,hy+7),30)
    stroke(mid,lip,"cactus",2.7,3)
    # Crooked teeth are thick enough to survive the 2x export and the finishing pass.
    for x,y,w,h in ((-25,hy+2,3,4),(-17,hy+1,2,3),(-3,hy+3,3,3),(10,hy+7,2,3)):
        mid.part(Xf(),Poly([(x,y),(x+w,y+1),(x+w-1,y+h),(x-1,y+h)]),
                 "ivory",lambda i:4 if i.lx>x else 5,outline=False,rust=0.)
    # The near eye is much larger, as in the supplied painting.
    for idx,(ex,ey,rad) in enumerate((EYE_F,EYE_N)):
        ey+=dy
        mid.part(Xf(),Ellipse(ex,ey,rad+2,rad+2),"cactus",
                 dome(ex-4,ey-5,rad+5,lo=1,hi=4,fixed=True),rust=0.)
        if p.eyes>=1.8:
            stroke(mid,curve((ex-rad+1,ey),(ex-4,ey+3),(ex+4,ey+2),(ex+rad-1,ey-1),14),"cactus",1,1)
            continue
        mid.part(Xf(),Ellipse(ex,ey,rad,rad+1),"ember",
                 dome(ex-3,ey-4,rad+2,lo=1,hi=3,gain=1.3,fixed=True),rust=0.)
        # Tiny, mismatched pupils keep the slightly vacant expression.
        px=round(ex+(-rad*.45 if idx==0 else rad*.4)*(1-p.eyes))
        py=round(ey-rad*.42+p.eyes*2)
        mid.part(Xf(),Ellipse(px,py,1.6,3),"crimson",lambda i:0,outline=False,rust=0.)
        mid.part(Xf(),Ellipse(ex-3,ey-5,max(1.6,rad*.27),max(1.5,rad*.24)),
                 "ivory",lambda i:5,outline=False,rust=0.)
    for x,y in ((-10,hy-11),(1,hy-12)):
        mid.part(Xf(),Ellipse(x,y,2.3,1.8),"cactus",lambda i:1,rust=0.)
    for x,y,rx,ry in ((17,hy-2,3,2),(22,hy+2,2,2),(16,hy+8,2,1.5),(-4,hy-12,2,2)):
        mid.part(Xf(),Ellipse(x,y,rx,ry),"cactus",dome(x-1,y-1,4,lo=2,hi=4,fixed=True),rust=0.)
    # Wet skin highlights follow the brow and cheek.
    for x,y in curve((-30,hy+10),(-18,hy+14),(3,hy+11),(11,hy+13),25):
        if mid.get(round(x),round(y)) in CA[1:]:
            mid.put(round(x),round(y),CA[4])


def sprouts(mid,glow,n):
    for x,y in SPROUTS[:round(n)]:
        mid.part(Xf(),Capsule((x,y+3),(x,y-2),1.6),"ivory",lambda i:4,rust=0.)
        mid.part(Xf(),Ellipse(x,y-3,4.6,3)-Poly([(x-6,y-2),(x+6,y-2),(x+6,y+5),(x-6,y+5)]),
                 "denim",lambda i:4 if i.lx<x else 3,rust=0.)
        glow[(x-1,y-5)]=DN[5]
        glow[(x,y-5)]=DN[5]


def arm(cv,glow,shoulder,hand,depth,magic,finger=0.):
    """Bent green forearm with three large red pads; the near arm holds the reference's spell-casting gesture."""
    sx,sy=shoulder
    hx,hy=map(round,hand)
    elbow=(round(sx*.42+hx*.58+(-5 if depth==0 else 7)),round(max(sy,hy)+17))
    limb(cv,(sx,sy),elbow,5.5,"cactus",depth,lo=1,hi=4)
    limb(cv,elbow,(hx,hy+6),4.5,"cactus",depth,lo=1,hi=4)
    if depth==0:
        for x,y in curve((elbow[0]+1,elbow[1]-3),(elbow[0]+2,elbow[1]-12),(hx+2,hy+15),(hx+1,hy+9),18):
            if cv.get(round(x),round(y)) in CA[1:]:
                cv.put(round(x),round(y),CA[3])
    limb(cv,(hx,hy+6),(hx,hy),5,"crimson",depth,lo=2,hi=5)
    directions=((-10,-6),(-2,-17),(10,-9)) if depth==0 else ((-9,6),(1,9),(10,4))
    for k,(dx,dy) in enumerate(directions):
        tip=(round(hx+dx*(1-finger*.25)),round(hy+dy+finger*4))
        bend=(hx+dx*.6,hy+dy*.45)
        limb(cv,(hx,hy),bend,3.2,"crimson",depth,lo=2,hi=5)
        limb(cv,bend,tip,2.8,"crimson",depth,lo=2,hi=5)
        cv.part(Xf(),Ellipse(tip[0],tip[1],4.5,5.4 if k==1 else 3.8),"crimson",
                dome(tip[0]-2,tip[1]-3,6.6,lo=2,hi=5-depth,fixed=True),rust=0.)
        if depth==0:
            cv.put(tip[0]-1,tip[1]-2,K[5])
            cv.put(tip[0],tip[1]-2,EM[2])
    if magic>.1:
        radius=3+round(magic*3)
        x,y=hx,hy-22
        cv.part(Xf(),Ellipse(x,y,radius,radius),"amethyst",dome(x-1,y-2,radius+2,lo=2,hi=4,fixed=True),rust=0.)
        for dx,dy in ((-1,-1),(0,-1),(-1,0),(0,0)):
            glow[(x+dx,y+dy)]=AE[3]


def frame(p):
    far,mid,near=Canvas(),Canvas(),Canvas()
    glow={}
    spell_curls(far,p.curl)
    arm(far,glow,SHOULDER_F,p.far,1,0.)
    finish(far)
    seat(mid,p.curl)
    thigh(mid,(27,-27),(37,-17),1)
    body(mid,glow,p)
    throat(mid,p)
    head(mid,glow,p)
    thigh(mid,(-26,-25),(-22,-15),0)
    sprouts(mid,glow,p.shrooms)
    finish(mid)
    arm(near,glow,SHOULDER_N,p.near,0,p.magic,p.finger)
    finish(near)
    mid.glow.update(glow)
    return far,mid,near


REST_N,REST_F=(-50,-95),(31,-52)


def tween(a,b,u):
    q=u*u*(3-2*u)
    kw={}
    for key,value in vars(a).items():
        other=getattr(b,key)
        if isinstance(value,tuple):
            kw[key]=tuple(round(x+(y-x)*q) for x,y in zip(value,other))
        else:
            v=value+(other-value)*q
            kw[key]=round(v) if key in ("breath","curl","head") else v
    return Pose(**kw)


def sequence(name,keys,count):
    out=[]
    for k in range(count):
        position=k/(count-1)*(len(keys)-1)
        idx=min(len(keys)-2,int(position))
        pose=tween(keys[idx],keys[idx+1],position-idx)
        pose.curl=k%12
        out.append((name+str(k),pose))
    return out


FRAMES=[]
for k in range(16):
    breath=round(math.sin(k*math.tau/16))
    FRAMES.append(("Idle"+str(k),Pose(near=(-50,-95+breath),breath=breath,curl=k%12)))
FRAMES+=sequence("Cast",[Pose(),Pose(near=(-46,-104),magic=1,finger=.5),
                         Pose(near=(-59,-94),magic=1.8,mouth=.5),Pose(near=(-63,-85),magic=.2,mouth=.7),
                         Pose()],16)
FRAMES+=sequence("Croak",[Pose(),Pose(sac=.4,near=(-48,-87),mouth=.2),
                          Pose(sac=1,near=(-44,-80),mouth=.3),Pose(sac=.65,mouth=1,head=-2),
                          Pose()],20)
FRAMES+=sequence("Tongue",[Pose(),Pose(mouth=.7,near=(-47,-90)),Pose(mouth=1.9,near=(-45,-86)),
                           Pose(mouth=1.9,near=(-45,-86)),Pose()],16)
FRAMES+=sequence("Fizzle",[Pose(),Pose(near=(-47,-99),eyes=1,magic=.3),
                           Pose(near=(-43,-82),eyes=1,mouth=1.2,head=2),
                           Pose(near=(-47,-88),eyes=.6,mouth=.3),Pose()],16)
FRAMES+=sequence("Intro",[Pose(eyes=2,near=(-39,-72),head=2),Pose(eyes=2,near=(-46,-86)),
                          Pose(eyes=0),Pose()],16)
FRAMES+=sequence("Death",[Pose(),Pose(bloat=.25,shrooms=1,eyes=.4),
                          Pose(bloat=.55,shrooms=3,eyes=1,mouth=.5),
                          Pose(bloat=1,shrooms=7,eyes=1,mouth=1.4,near=(-57,-100),head=-2)],24)
FRAMES+=sequence("Blink",[Pose(),Pose(eyes=2),Pose()],6)
INDEX={name:k for k,(name,_) in enumerate(FRAMES)}
SEQUENCES=("Idle","Cast","Croak","Tongue","Fizzle","Intro","Death","Blink")


def render_all():
    return [(name,*frame(p),p) for name,p in FRAMES]


def fit_cell(frames):
    pts = [q for (_, far, mid, near, _) in frames for cv in (far, mid, near) for q in list(cv.px) + list(cv.glow)]
    xs = [x for x, y in pts if y < GROUND_CLIP]
    ys = [y for x, y in pts if y < GROUND_CLIP]
    ox = max(-min(xs), max(xs) + 1)
    return 2 * ox, GROUND_CLIP - min(ys), ox, -min(ys)


def grid(canvases, cell, glow=False):
    w, h, ox, oy = cell
    rows = (len(canvases) + COLUMNS - 1) // COLUMNS
    out = Image.new("RGBA", ((w + 1) * COLUMNS, (h + 1) * rows), (0, 0, 0, 0))
    pix = out.load()
    for k, cv in enumerate(canvases):
        src = cv.glow if glow else cv.px
        bx, by = (k % COLUMNS) * (w + 1), (k // COLUMNS) * (h + 1)
        for (x, y), col in src.items():
            if y >= GROUND_CLIP:
                continue
            cx, cy = x + ox, y + oy
            if not (0 <= cx < w and 0 <= cy < h):
                raise SystemExit("pixel (%d, %d) of frame %d is outside its %dx%d cell" % (x, y, k, w, h))
            pix[bx + cx, by + cy] = col + (255,)
    return out


def body_box(mid):
    """The hitbox (1x, from the origin): the seat's cap, the body and the head to the eyes' tops (not the frills' tips)."""
    xs = sorted(x for (x, y) in mid.px if y > HEAD_C[1])
    return xs[2], xs[-3] + 1, int(EYE_N[1] - EYE_N[2] - 1), 0


def write_rig(path, cell, frames):
    w, h, ox, oy = cell
    left, right, top, bottom = body_box(frames[0][2])
    seq = []
    for name in SEQUENCES:
        n = sum(1 for (fn, _) in FRAMES if fn.startswith(name) and fn[len(name):].isdigit())
        seq.append("%s = %d, %sFrames = %d" % (name, INDEX[name + "0"], name, n))

    def arr(name, vals):
        return "\t\tpublic static readonly short[] %s = { %s };" % (name, ", ".join(str(v) for v in vals))
    lines = [
        "// <auto-generated> by art/bosses/fungimancer/make_fungimancer_art.py - do not edit by hand. </auto-generated>",
        "namespace Cogpunk.Content.Bosses.Fungimancer",
        "{",
        "\t/// <summary>The Fungimancer's grid sheets (game px, facing left): far, middle, near and glow, equal cells in",
        "\t/// <see cref=\"Columns\"/> columns with 2 px right of and under each; the origin is under its seat's stalk. Body*: its hitbox",
        "\t/// from the origin. Per frame, from the origin, facing left: NearX/NearY the near hand (its spells leave it); Mouth: the",
        "\t/// mouth's front corner (the tongue leaves it); Throat: under the chin (the croak's ring).</summary>",
        "\tpublic static class FungimancerRigData",
        "\t{",
        "\t\tpublic const int CellWidth = %d, CellHeight = %d, OriginX = %d, OriginY = %d, Frames = %d, Columns = %d;"
        % (w * 2, h * 2, ox * 2, oy * 2, len(FRAMES), COLUMNS),
        "\t\tpublic const int " + ", ".join(seq[:4]) + ";",
        "\t\tpublic const int " + ", ".join(seq[4:]) + ";",
        "\t\tpublic const int BodyLeft = %d, BodyRight = %d, BodyTop = %d, BodyBottom = %d;" % (left * 2, right * 2, top * 2, bottom * 2),
        "\t\tpublic const int MouthX = %d, MouthY = %d, ThroatX = %d, ThroatY = %d;"
        % (round(MOUTH[0] * 2), round(MOUTH[1] * 2), round((HEAD_C[0] - 4) * 2), round((HEAD_C[1] + 9) * 2)),
        arr("NearX", [round(p.near[0] * 2) for (_, _, _, _, p) in frames]),
        arr("NearY", [round((p.near[1] - 1) * 2) for (_, _, _, _, p) in frames]),
        "\t}",
        "}",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("wrote", path)


def head_icon(mid):
    hx, hy = HEAD_C
    px = {(x, y): c for (x, y), c in mid.px.items() if abs(x - hx) <= 13 and hy - 14 <= y <= hy + 8}
    xs, ys = [x for x, _ in px], [y for _, y in px]
    return to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def gores(mid):
    hy = HEAD_C[1]
    parts = {"Fungimancer_GoreHead": {q: c for q, c in mid.px.items() if q[1] <= hy + 6},
             "Fungimancer_GoreBody": {q: c for q, c in mid.px.items() if hy + 6 < q[1] <= -18},
             "Fungimancer_GoreSeat": {q: c for q, c in mid.px.items() if q[1] > -18}}
    out = {}
    for name, px in parts.items():
        xs, ys = [x for x, _ in px], [y for _, y in px]
        out[name] = to_image(px, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    return out


# --- projectiles and things ------------------------------------------------------------------------------------------------
def spore_bolt():
    """A spore of violet light: a round glow (aether) round a bright core, sparkles turning round it, 4 frames, 9 px."""
    out = Image.new("RGBA", (9, 4 * 10 - 1), (0, 0, 0, 0))
    for k in range(4):
        px = {}
        for y in range(9):
            for x in range(9):
                d = math.hypot(x - 4, y - 4)
                if d <= 3.3:
                    px[(x, y)] = AE[3] if d < 1.2 else AE[2] if d < 2.4 else AE[1]
        a = k * math.pi / 2
        for (r, off) in ((4.2, 0.0), (4.2, math.pi)):
            q = (int(round(4 + r * math.cos(a + off))), int(round(4 + r * math.sin(a + off))))
            if 0 <= q[0] < 9 and 0 <= q[1] < 9:
                px[q] = DN[5]
        px[(3, 3)] = SM[3]
        for (x, y), c in px.items():
            out.putpixel((x, y + k * 10), c + (255,))
    return out


def shroom_spike():
    """A glowing mushroom bursting up out of the ground, 4 frames of 14 x 18: a bump, the stalk rising, the cap open, the cap
    with spores (it lingers that way while it hurts)."""
    out = Image.new("RGBA", (14, 4 * 19 - 1), (0, 0, 0, 0))
    for k in range(4):
        cv = Canvas()
        rise = (3.0, 8.0, 12.0, 12.0)[k]
        base = 17.5
        cv.part(Xf(), Capsule((7.0, base), (7.0, base - rise), 2.2, 1.8), "steam", lambda i: 2 if i.lx < 6.8 else 1, rust=0.0)
        if k >= 1:
            cap_w = (3.5, 6.4, 6.6)[k - 1]
            cy = base - rise - 1.0
            cv.part(Xf(), Ellipse(7.0, cy + 1.0, cap_w, 4.4 if k > 1 else 2.6) - Poly([(0.0, cy + 1.2), (14.0, cy + 1.2), (14.0, 20.0), (0.0, 20.0)]),
                    "denim", dome(5.0, cy - 2.5, 7.0, lo=2, hi=5, fixed=True), rust=0.0)
            cv.part(Xf(), Ellipse(7.0, cy + 1.0, cap_w - 0.6, 0.9), "aether", lambda i: 2, rust=0.0, outline=False)
            if k >= 2:
                for (x, y) in ((5, int(cy - 1)), (9, int(cy))):
                    cv.put(x, y, SM[3])
            if k == 3:
                for (x, y) in ((2, int(cy - 4)), (11, int(cy - 3)), (7, int(cy - 5))):
                    cv.put(x, y, AE[3])
        finish(cv)
        for (x, y), c in cv.px.items():
            if 0 <= x < 14 and 0 <= y < 18:
                out.putpixel((x, y + k * 19), c + (255,))
    return out


def tongue_tip():
    cv = Canvas()
    cv.part(Xf(), Ellipse(3.5, 3.5, 3.2, 2.8), "crimson", dome(2.6, 2.4, 3.6, lo=3, hi=5, fixed=True), rust=0.0)
    finish(cv)
    return to_image(cv.px, 0, 0, 7, 7)


def bag():
    """The treasure bag: a blue cloth sack tied with a violet cord, a glowing mushroom stitched on it."""
    cv = Canvas()
    cv.part(Xf(), Ellipse(8.0, 10.0, 6.5, 5.6), "denim", dome(6.0, 8.0, 8.0, lo=2, hi=4, fixed=True), rust=0.0)
    cv.part(Xf(), Poly([(5.0, 3.0), (11.0, 3.0), (9.6, 5.6), (6.4, 5.6)]), "denim", lambda i: 3, rust=0.0)
    for x in range(6, 11):
        cv.put(x, 5, AE[2] if x % 2 else AE[3])
    cv.part(Xf(), Ellipse(8.0, 9.6, 2.6, 1.6), "steam", lambda i: 3 if i.lx < 8.0 else 2, rust=0.0, outline=False)
    cv.put(8, 11, SM[1])
    cv.put(8, 12, SM[1])
    finish(cv)
    return to_image(cv.px, 0, 0, 16, 16)


RAINBOW = (K[4], EM[3], RAMP["gilt"][8], CA[4], DN[5], AE[3])


def rainbow_mushroom(w, cap_rx, cap_ry, stalk_h, cx, base):
    """A glowing mushroom whose cap runs through the rainbow in bands (red at the crown to violet at the rim), a pale stalk."""
    cv = Canvas()
    cv.part(Xf(), Capsule((cx, base), (cx, base - stalk_h), 1.3, 1.1), "steam", lambda i: 2 if i.lx < cx - 0.2 else 1, rust=0.0)
    top = base - stalk_h - 0.6
    shape = Ellipse(cx, top, cap_rx, cap_ry) - Poly([(-5.0, top + 0.8), (w + 5.0, top + 0.8), (w + 5.0, base + 5.0), (-5.0, base + 5.0)])
    cv.part(Xf(), shape, "steam", lambda i: 3, rust=0.0)
    for (x, y), _ in list(cv.px.items()):
        dx, dy = (x + 0.5 - cx) / cap_rx, (y + 0.5 - top) / max(cap_ry, 0.1)
        if dy <= 0.2 and dx * dx + dy * dy <= 1.0:
            r = math.sqrt(dx * dx + dy * dy)
            band = min(len(RAINBOW) - 1, int(r * len(RAINBOW)))
            edge = any((x + ox, y + oy) not in cv.px for ox, oy in ((1, 0), (-1, 0), (0, -1)))
            cv.px[(x, y)] = RAMP["plum"][0] if edge else RAINBOW[band]
    return cv


def tile_sheet():
    """Three rainbow mushrooms (1 x 1 tile each, 8 x 8 at 1x, 9 px apart: 18 at 2x) of different heights."""
    out = Image.new("RGBA", (27, 9), (0, 0, 0, 0))
    for k, (rx, ry, sh) in enumerate(((3.4, 2.6, 2.6), (3.0, 2.4, 3.6), (3.6, 2.8, 2.0))):
        cv = rainbow_mushroom(8, rx, ry, sh, 3.8, 7.6)
        for (x, y), c in cv.px.items():
            if 0 <= x < 8 and 0 <= y < 8:
                out.putpixel((x + k * 9, y), c + (255,))
    return out


def summon_item():
    cv = rainbow_mushroom(14, 6.0, 4.6, 5.0, 7.0, 13.0)
    return to_image(cv.px, 0, 0, 14, 14)


def export_all():
    frames = render_all()
    cell = fit_cell(frames)
    for key, idx, glow in (("", 2, False), ("_Far", 1, False), ("_Near", 3, False), ("_Glow", 2, True)):
        export(grid([fr[idx] for fr in frames], cell, glow), OUT + "Fungimancer%s.png" % key)
    write_rig(OUT + "FungimancerRigData.cs", cell, frames)
    export(head_icon(frames[0][2]), OUT + "Fungimancer_Head_Boss.png")
    for name, im in gores(frames[INDEX["Death23"]][2]).items():
        export(im, OUT + "Gores/" + name + ".png")
    export(spore_bolt(), OUT + "Projectiles/SporeBolt.png")
    export(shroom_spike(), OUT + "Projectiles/ShroomSpike.png")
    export(tongue_tip(), OUT + "Projectiles/FungimancerTongue.png")
    export(bag(), OUT + "Items/FungimancerBag.png")
    export(summon_item(), OUT + "Items/RainbowMushroom.png")
    export(tile_sheet(), OUT + "Tiles/RainbowMushroomTile.png")
    print("cell (1x) %dx%d, origin %d,%d" % cell)
    return frames, cell


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    args = ap.parse_args()
    frames, cell = export_all()
    if args.preview:
        w, h, ox, oy = cell
        sc = 3
        n = len(frames)
        sheet = Image.new("RGBA", (w * 2 * sc * 6 + 70, (h * 2 * sc + 10) * ((n + 5) // 6) + 10), (24, 24, 30, 255))
        for k, (name, far, mid, near, p) in enumerate(frames):
            im = Image.new("RGBA", (w, h), (36, 44, 72, 255))
            for cv, glow in ((far, False), (mid, False), (near, False), (mid, True)):
                for (x, y), c in (cv.glow if glow else cv.px).items():
                    if y < GROUND_CLIP and 0 <= x + ox < w and 0 <= y + oy < h:
                        im.putpixel((x + ox, y + oy), c + (255,))
            big = im.resize((w * 2 * sc, h * 2 * sc), Image.NEAREST)
            sheet.alpha_composite(big, (10 + (k % 6) * (w * 2 * sc + 10), 10 + (k // 6) * (h * 2 * sc + 10)))
        sheet.save(args.preview)
        print("preview", args.preview)


if __name__ == "__main__":
    main()
