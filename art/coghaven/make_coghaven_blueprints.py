r"""Source of Coghaven's palace blueprints (2026-11-06). Run from the repo root:

    python -P art/coghaven/make_coghaven_blueprints.py [--png PATH]

Writes Content/Coghaven/Generation/CoghavenBlueprints.cs (generated: edit this script, not the C#), the ASCII rows that
Content/Coghaven/Generation/CoghavenPass.cs builds, and with --png a colour key render of every building for review.
tools/sim/coghaven_sim.py reads the generated C# back to replay the pass and render the island with the real sprites.

The palace (user, 2026-11-06: "a steampunk jade palace with red, bronze and jade colours, built like a well designed,
detailed dungeon") is composed here from parts: curved Chinese hip roofs of glazed jade tiles with upturned eaves and a
gilt ridge (roof()), red lacquered pillars and beams over jade-brick plinths, bronze fret lattice windows, bronze
gearwork and turning cogs where the steam machinery shows through, Dynasty furniture and lanterns inside. Read left to
right across the island: the garden and its koi pond, the gate (paifang), the forecourt, the Main Hall on its terrace
(the throne, the gallery above, the stair down), the five-storey pagoda (the treasure at its top, a turning cog for a
finial), the tea pavilion and the far garden; under them, inside the island's bronze core, the Jade Vault (since
2026-11-16: one long machine hall, Jadey's arena, in place of the engine deck's corridor, storerooms, shrine and boiler hall).

Legend (each cell a tile; the cell's wall in brackets):
    ' '  leave as it is (the open sky: no tile, no wall)
    F    Palace Flagstone [Flagstone Wall]         f  Palace Flagstone [none]   (2026-11-06: floors are stone, the jade
                                                   is the roofs' alone)
    R    Cinnabar Lacquer [Cinnabar Panel Wall]    r  Cinnabar Lacquer [none]
    G    Bronze Gearwork [Gearwork Wall]           g  Bronze Gearwork [none]
    T    Jade Roof Tiles [none]                    Y  vanilla Gold Brick [none] (the ridges' gilt ornaments)
    /    Jade Roof Tiles sloped, rising to the right (SlopeDownRight)   \  ... rising to the left (SlopeDownLeft)
    (    Palace Flagstone sloped, rising to the right [none]            )  ... rising to the left [none]
    -    Jade Roof Tiles half block [none]
    .    air [Cinnabar Panel Wall]   ,  air [Flagstone Wall]   :  air [Gearwork Wall]   #  air [Bronze Lattice Wall]
    m    air [vanilla White Dynasty Wall] (2026-11-19: the plaster of the rooms, between the red beams)
    =    Dynasty platform [Cinnabar Panel Wall]    +  Dynasty platform [none]    %  Dynasty platform [Gearwork Wall]
    w    water [none]    ~  water [Flagstone Wall]
    X    Vault Gearwork [Vault Gearwork Wall]      x  Vault Gearwork [none]     (2026-11-16: the Jade Vault's shell,
         unbreakable)                              ;  air [Vault Gearwork Wall] $  Dynasty platform [Vault Gearwork Wall]
Furniture (placed after the blocks, at the marked cell, which is the object's anchor; the other cells of the object are
air with the room's wall: '.', ',' or ':'):
    C  a Pagoda Chest, sky loot (bottom left of 2x2;   Q  the pagoda's treasure chest
       since 2026-11-17 the Main Hall gallery's) (bottom left of 2x2): a Locked
                                                          Pagoda Chest since 2026-11-16 (the Pagoda Key opens it)
    &  the Jade Vault (bottom left of 2x2): sealed until Jadey is defeated; touching it wakes her (2026-11-16)
    <  Dynasty Chair facing left (bottom of 1x2)       >  Dynasty Chair facing right
    A  Dynasty Table (bottom middle of 3x2)            B  Dynasty Bookcase (bottom middle of 3x4)
    S  Dynasty Sofa (bottom middle of 3x2)             P  Dynasty Piano (bottom middle of 3x2)
    K  Dynasty Clock (bottom left of 2x5)              N  Throne (bottom middle of 3x4)
    L  Dynasty Lantern (top of 1x2, hangs)             O  Chinese Lantern (top left of 2x2, hangs)
    H  Dynasty Chandelier (top middle of 3x3, hangs)   i  Dynasty Candle (on a table or platform)
    I  Dynasty Lamp (bottom of 1x3)                    V  Dynasty Candelabra (bottom left of 2x2)
    U  Steampunk Boiler (bottom middle of 3x3)         ^  Steampunk Lantern (top of 1x2, hangs)
    Z  Bronze Cog, clockwise (6x6, top left; it stands on the two tiles under its middle)    z  ... turning the other way
"""
import argparse
import os

ROOT = os.getcwd()
OUT_CS = "Content/Coghaven/Generation/CoghavenBlueprints.cs"


class Plan:
    """A grid of legend characters, y down; the bottom row is laid on the island's surface row."""

    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.g = [[" "] * w for _ in range(h)]

    def put(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else " "

    def rect(self, x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, ch)

    def hline(self, x0, x1, y, ch):
        self.rect(x0, y, x1, y, ch)

    def vline(self, x, y0, y1, ch):
        self.rect(x, y0, x, y1, ch)

    def text(self, x0, y0, rows):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != "?":
                    self.put(x0 + dx, y0 + dy, ch)

    def rows(self):
        return ["".join(r) for r in self.g]


def roof(p, cx, ridge_y, ridge_half, eave_half, rows, gilt=True, tips=True, finial=None):
    """A curved hip roof of glazed jade tiles centred on column cx (cx may be x.5 for an even width): `rows` rows from
    the ridge (ridge_y) down to the eave, the half-width growing slowly near the ridge and fast near the eave (a
    concave Chinese roof); every row's ends are slopes, the eave's ends turn up (tips), the ridge carries gilt
    ornaments at its ends (and a finial in the middle when given)."""
    halves = []
    for r in range(rows):
        t = r / max(1, rows - 1)
        halves.append(int(round(ridge_half + (eave_half - ridge_half) * t ** 1.55)))
    for r, half in enumerate(halves):
        y = ridge_y + r
        x0, x1 = int(round(cx - half)), int(round(cx + half - (0 if cx == int(cx) else 1)))
        if cx != int(cx):
            x0, x1 = int(cx - half + 0.5), int(cx + half - 0.5)
        p.hline(x0, x1, y, "T")
        if r == 0:
            if gilt:
                p.put(x0, y, "Y")
                p.put(x1, y, "Y")
            continue
        last = r == rows - 1
        if last and tips:
            p.put(x0, y, "\\")                              # the eave turns up at its tips
            p.put(x1, y, "/")
            p.put(x0 + 1, y, "T")
            p.put(x1 - 1, y, "T")
        else:
            prev = halves[r - 1]
            if half - prev >= 2:
                p.put(x0, y, "-")                           # a long step: a half block, then a slope
                p.put(x0 + 1, y, "/")
                p.put(x1, y, "-")
                p.put(x1 - 1, y, "\\")
            else:
                p.put(x0, y, "/")
                p.put(x1, y, "\\")
    if finial:
        fx = int(cx) if cx == int(cx) else int(cx - 0.5)
        for dy, row in enumerate(finial):
            for dx, ch in enumerate(row):
                if ch != "?":
                    p.put(fx - len(row) // 2 + dx + (0 if cx == int(cx) else 1) * 0, ridge_y - len(finial) + dy, ch)
    return halves


# ================================================================================================
# The gate (paifang): four red pillars on jade plinths, three openings, a gilt plaque, three curved roofs
# ================================================================================================
def gate():
    p = Plan("Gate", 25, 19)
    floor = p.h - 1
    p.hline(0, p.w - 1, floor, "f")                         # its own strip of terrace
    for x in (2, 8, 16, 22):                                # pillars
        top = 6 if x in (8, 16) else 9
        p.vline(x, top, floor - 1, "r")
        p.put(x - 1, floor - 1, "(")                        # jade plinths
        p.put(x, floor - 1, "f")
        p.put(x + 1, floor - 1, ")")
    p.hline(8, 16, 7, "r")                                  # the main lintel, the plaque on it
    p.hline(10, 14, 6, "Y")
    p.put(9, 6, "r")
    p.put(15, 6, "r")
    p.hline(8, 16, 9, "r")
    p.hline(2, 8, 10, "r")                                  # side lintels
    p.hline(16, 22, 10, "r")
    for x in (4, 6, 18, 20):
        p.put(x, 11, "r")                                   # bracket posts under the side lintels
    roof(p, 12, 1, 2, 7, 5)                                 # the central roof
    roof(p, 5, 6, 1, 5, 3)                                  # the side roofs
    roof(p, 19, 6, 1, 5, 3)
    p.put(12, 0, "Y")                                       # a gilt pearl on the central ridge
    for x in (9, 14):
        p.put(x, 10, "O")                                   # two Chinese lanterns hang from the main lintel
    return p


# ================================================================================================
# The Main Hall: a three-step jade terrace, a two-storey hall of red pillars and lattice, a double-eave roof
# ================================================================================================
def main_hall():
    W = 63
    p = Plan("MainHall", W, 36)
    floor = p.h - 1                                         # the island's surface row
    # the terrace: three steps of jade brick; the hall stands on the top one
    for step, (x0, x1) in enumerate(((0, W - 1), (2, W - 3), (4, W - 5))):
        y = floor - step
        p.hline(x0, x1, y, "F" if step == 0 else "f")
        if step:
            p.put(x0, y, "(")
            p.put(x1, y, ")")
    base = floor - 2                                        # the hall's floor row
    hx0, hx1 = 7, W - 8                                     # the hall's end walls
    mid = (hx0 + hx1) // 2
    g_top = base - 10                                       # the ground storey: rows base-1 .. g_top+1 (9 rows)
    # the ground storey: red panel walls with gold lattice windows between the (background) pillars; solid red end
    # walls with a doorway each
    p.rect(hx0, g_top, hx1, base - 1, "m")                  # 2026-11-19: white plaster between red beams (was all red)
    for x in range(hx0 + 1, hx1, 8):
        p.vline(x, g_top + 1, base - 1, ".")
    p.hline(hx0 + 1, hx1 - 1, g_top + 1, ".")
    for x0 in range(hx0 + 2, hx1 - 1, 8):
        x1 = min(x0 + 4, hx1 - 2)
        if x0 <= mid <= x1 + 1:
            continue                                        # the middle bay: the throne's
        p.rect(x0, base - 8, x1, base - 4, "#")
    for x in (hx0, hx1):
        p.vline(x, g_top, base - 5, "R")                    # end walls, a 4-tall doorway under each
    # the lower eave all round the ground storey (overhanging 4), then the upper storey stands in its middle
    low = roof(p, (hx0 + hx1) / 2.0, g_top - 4, (hx1 - hx0) // 2 - 3, (hx1 - hx0) // 2 + 4, 4, gilt=False)
    p.hline(hx0, hx1, g_top, "R")                           # the beam over the ground storey
    ux0, ux1 = hx0 + 7, hx1 - 7
    u_top = g_top - 9                                       # the upper storey: rows g_top-1 .. u_top+1 (8 rows)
    p.rect(ux0, u_top, ux1, g_top - 1, "m")
    for x in range(ux0 + 1, ux1, 6):
        p.vline(x, u_top + 1, g_top - 1, ".")
    p.hline(ux0 + 1, ux1 - 1, u_top + 1, ".")
    for x0 in range(ux0 + 2, ux1 - 1, 6):
        p.rect(x0, u_top + 2, min(x0 + 3, ux1 - 2), u_top + 5, "#")
    for x in (ux0, ux1):
        p.vline(x, u_top, g_top - 1, "R")
    p.hline(ux0, ux1, u_top, "R")
    p.hline(ux1 - 5, ux1 - 2, g_top, "=")                   # the gallery's hatch (Dynasty platforms) in its solid floor
    p.hline(ux1 - 5, ux1 - 2, base - 5, "=")                # a landing half way up under it
    for x in range(hx0 + 1, ux0, 3):
        p.put(x, g_top - 1, "G")                            # bronze brackets under the lower eave, outside the gallery
    for x in range(ux1 + 2, hx1, 3):
        p.put(x, g_top - 1, "G")
    # the upper roof: a curved hip roof with gilt ridge ends and a gilt and bronze finial
    high = roof(p, (hx0 + hx1) / 2.0, u_top - 7, 8, (ux1 - ux0) // 2 + 6, 7, finial=["?Y?", "YGY"])
    # 2026-11-19: Chinese lanterns hanging under the eaves' tips (the reference's), each roof's last row the hook
    for (eave_y, half) in ((g_top - 1, low[-1]), (u_top - 1, high[-1])):
        left, right = int(round((hx0 + hx1) / 2.0 - half)), int(round((hx0 + hx1) / 2.0 + half))
        p.put(left + 1, eave_y + 1, "O")
        p.put(right - 2, eave_y + 1, "O")
    # the throne on its dais between two great turning cogs; lanterns, chests and candelabras in the end bays
    p.hline(mid - 3, mid + 3, base - 1, "F")
    p.put(mid - 4, base - 1, "(")
    p.put(mid + 4, base - 1, ")")
    p.put(mid, base - 2, "N")
    p.put(mid - 11, base - 6, "Z")                          # 6x6 cogs standing on the floor, either side of the dais
    p.put(mid + 6, base - 6, "z")
    for x in (hx0 + 3, hx1 - 3, mid - 7, mid + 7):
        p.put(x, g_top + 1, "L")
    p.put(mid, g_top + 1, "H")                              # a chandelier over the throne
    p.put(hx0 + 5, base - 1, "V")
    p.put(hx1 - 6, base - 1, "V")
    # the stair down to the engine deck: a hatch of platforms in the floor of the left bay, the shaft under it
    sx = hx0 + 9
    for y in range(base, floor + 1):
        for x in range(sx, sx + 3):
            p.put(x, y, "," if y > base else "=")
    # the gallery: bookcases at the ends, a table with a candle, two chairs, a chandelier, steam lanterns
    p.put(ux0 + 3, g_top - 1, "B")
    p.put(ux1 - 3, g_top - 1, "B")
    p.put(mid, g_top - 1, "A")
    p.put(mid - 2, g_top - 1, ">")
    p.put(mid + 2, g_top - 1, "<")
    p.put(ux0 + 7, g_top - 1, "C")                          # 2026-11-17: the gallery's chest (sky loot, a plain Pagoda Chest)
    p.put(mid, g_top - 3, "i")
    p.put(mid, u_top + 1, "H")
    p.put(ux0 + 6, u_top + 1, "^")
    p.put(ux1 - 6, u_top + 1, "^")
    return p, sx


# ================================================================================================
# The pagoda: five storeys, each narrower, each with its own little eave; the treasure at the top; a cog finial
# ================================================================================================
def pagoda(storeys=5):
    """2026-11-19 (user: "rework cogpalace design i will provide a base example of a quality terraria japanese building stile
    using in-game blocks", reference/pagoda_user_2026-11-19.png): the reference's tiered pagoda in Coghaven's colours. Each
    storey a white plaster room (vanilla White Dynasty Wall: 'm') framed by red beams in the background (posts every fifth
    column and a beam under the ceiling, the Cinnabar Panel Wall: nothing blocks the way), red lacquer corner posts, lattice
    windows; over it a jade eave sweeping EAVE_OUT columns past the walls in ROOF_ROWS rows, its tips turned up, a red
    bracket beam under it and a Chinese lantern hanging under each tip; the top storey under a tall pointed roof, a gilt
    spire and the turning cog. The 2026-11-06 pagoda (small eaves, flagstone rooms) is in previous/."""
    widths = [21, 19, 17, 15, 13][:storeys]
    heights = [8, 7, 7, 6, 6][:storeys]
    roof_rows, eave_out, top_rows = 4, 5, 7
    W = 21 + 2 * eave_out + 2                               # the ground storey's eave and a column either side: 33
    H = 3 + sum(h + roof_rows for h in heights) + (top_rows - roof_rows) + 11 + 1
    p = Plan("Pagoda%d" % storeys, W, H)
    floor = H - 1
    cx = W // 2
    # a jade plinth with steps
    p.hline(1, W - 2, floor, "F")
    p.put(1, floor, "(")
    p.put(W - 2, floor, ")")
    p.hline(4, W - 5, floor - 1, "f")
    p.put(4, floor - 1, "(")
    p.put(W - 5, floor - 1, ")")
    y = floor - 2                                           # the ground storey's floor row
    p.hline(4, W - 5, y, "F")
    rooms = []
    for s_, (w, h) in enumerate(zip(widths, heights)):
        x0, x1 = cx - w // 2, cx + w // 2
        top = y - h
        last = s_ == storeys - 1
        p.rect(x0, top, x1, y - 1, "m")
        for x in range(x0 + 5, x1 - 1, 5):
            p.vline(x, top + 1, y - 1, ".")                  # the red posts (background)
        p.hline(x0 + 1, x1 - 1, top + 1, ".")                # the beam under the ceiling
        p.vline(x0, top, y - 1, "R")
        p.vline(x1, top, y - 1, "R")
        p.hline(x0, x1, top, "R")
        if s_ == 0:
            p.vline(x0, y - 4, y - 1, "m")                   # a doorway in each side of the ground storey
            p.vline(x1, y - 4, y - 1, "m")
        p.rect(x0 + 2, top + 3, x0 + 3, top + 5, "#")        # lattice windows on both sides
        p.rect(x1 - 3, top + 3, x1 - 2, top + 5, "#")
        rooms.append((x0, x1, top, y))
        rows = top_rows if last else roof_rows
        half = w // 2 + eave_out
        roof(p, cx, top - rows + 1, 1 if last else w // 2 - 1, half, rows, gilt=last)
        # the red bracket beam under the eave, outside the walls, and a lantern under each tip
        for x in list(range(cx - half + 3, x0)) + list(range(x1 + 1, cx + half - 2)):
            p.put(x, top + 1, "r")
        p.put(cx - half + 1, top + 1, "O")
        p.put(cx + half - 2, top + 1, "O")
        up = top - rows + 1
        if not last:
            p.hline(cx - widths[s_ + 1] // 2, cx + widths[s_ + 1] // 2, up, "F")
            # the stair: a landing half way up the room and a hole through the slab, platforms at the floor above,
            # on alternate sides so the climb zig-zags
            sx = x0 + 2 if s_ % 2 == 0 else x1 - 4
            for yy in range(up, top + 1):
                for xx in range(sx, sx + 3):
                    p.put(xx, yy, "m")
            p.hline(sx, sx + 2, up, "=")
            p.hline(sx, sx + 2, y - 4, "=")
        y = up
    # the spire: a gilt mast on the pointed roof's ridge, the turning cog standing on it
    p.rect(cx - 1, y - 4, cx, y - 1, "Y")
    p.put(cx - 3, y - 10, "Z")
    # furniture: a lantern in every room, a clock and a table on the ground floor, bookcases, the treasure at the top
    for s_, (x0, x1, top, bot) in enumerate(rooms):
        p.put(x0 + (x1 - x0) // 2, top + 2, "L")
        if s_ == 0:
            p.put(x1 - 5, bot - 1, "K")
            p.put(x0 + 7, bot - 1, "A")
            p.put(x0 + 7, bot - 3, "i")
        elif s_ == storeys - 1:
            p.put(x0 + (x1 - x0) // 2 - 1, bot - 1, "Q")
            p.put(x0 + 2, bot - 1, "V")
        else:
            p.put(x0 + (x1 - x0) // 2, bot - 1, "B")
    return p


# ================================================================================================
# The tea pavilion: four red pillars, an open floor, a curved roof, tea on the table
# ================================================================================================
def pavilion():
    p = Plan("Pavilion", 19, 15)
    floor = p.h - 1
    p.hline(0, p.w - 1, floor, "F")
    p.hline(1, p.w - 2, floor - 1, "F")
    p.put(0, floor, "(")
    p.put(p.w - 1, floor, ")")
    p.put(1, floor - 1, "(")
    p.put(p.w - 2, floor - 1, ")")
    base = floor - 1
    for x in (3, 15):
        p.vline(x, base - 7, base - 1, "r")
    p.hline(3, 15, base - 7, "r")
    p.hline(4, 14, base - 8, "r")
    for x in (5, 9, 13):
        p.put(x, base - 8, "G")
    roof(p, 9, base - 13, 2, 9, 5, finial=["Y"])
    p.put(9, base - 1, "A")
    p.put(7, base - 1, ">")
    p.put(11, base - 1, "<")
    p.put(9, base - 3, "i")
    p.put(6, base - 6, "O")
    p.put(11, base - 6, "O")
    # a railing of platforms between the pillars (low, so the pavilion stays open)
    return p


# ================================================================================================
# The Jade Vault: inside the island's bronze core, under the Main Hall; reached by the hall's stair shaft
# ================================================================================================
VAULT_X0, VAULT_X1 = 11, 60             # the shell's columns (deck x; the deck's x 0 = the Main Hall's x 0)
VAULT_TOP, VAULT_FLOOR = 1, 18          # the shell's ceiling and floor rows (deck rows from the island's surface row)


def vault(shaft_x):
    """The Jade Vault (user, 2026-11-16: "the underground section of coghaven (under the main mansion) should be a single
    bigger room (like the machinery room but a bit longer) and the chest should be located on the middle of this room ...
    the arena room should be unbreakable"): the old boiler hall's machinery (two great cogs on the floor, boilers, steam
    lanterns) in one hall 48 tiles long (the boiler hall was 26) and 16 high, its shell of unbreakable Vault Gearwork, the
    vault chest in its middle. The hall's stair shaft drops through platforms in its ceiling; a ladder of platforms under
    the shaft and ledges on the far side lead back up. Rows 0.. from the island's surface row; shaft_x = the hall stair's
    column in deck coordinates."""
    W, H = 96, VAULT_FLOOR + 1
    p = Plan("Vault", W, H)
    for x in range(shaft_x, shaft_x + 3):                   # the shaft's last row (the surface row), air
        p.put(x, 0, ",")
    p.put(shaft_x - 1, 0, "G")
    p.put(shaft_x + 3, 0, "G")
    p.rect(VAULT_X0, VAULT_TOP, VAULT_X1, VAULT_FLOOR, "X")   # the shell, then the hall carved out of it
    p.rect(VAULT_X0 + 1, VAULT_TOP + 1, VAULT_X1 - 1, VAULT_FLOOR - 1, ";")
    for x in range(shaft_x, shaft_x + 3):
        p.put(x, VAULT_TOP, "$")                            # the way in: platforms in the ceiling under the shaft
    for y in (VAULT_TOP + 4, VAULT_TOP + 8, VAULT_TOP + 12):
        p.hline(shaft_x - 1, shaft_x + 3, y, "$")           # the ladder back up
    for y in (VAULT_TOP + 6, VAULT_TOP + 10):
        p.hline(VAULT_X1 - 8, VAULT_X1 - 4, y, "$")         # ledges on the far side
    floor_in = VAULT_FLOOR - 1                              # the row things stand on
    mid = (VAULT_X0 + 1 + VAULT_X1 - 1) // 2                # the hall's middle column (35)
    p.put(mid, floor_in, "&")                               # the vault chest, its left half on the middle column
    p.put(mid - 12, floor_in - 5, "Z")                      # the great cogs either side of it, standing on the floor
    p.put(mid + 8, floor_in - 5, "z")
    p.put(VAULT_X0 + 3, floor_in, "U")                      # boilers at both ends
    p.put(VAULT_X1 - 3, floor_in, "U")
    p.put(mid - 4, floor_in, "V")                           # candelabras beside the chest
    p.put(mid + 3, floor_in, "V")
    for x in (mid - 15, mid - 6, mid + 7, mid + 16):
        p.put(x, VAULT_TOP + 1, "^")                        # steam lanterns hanging from the ceiling
    return p


# ================================================================================================
# The site: where everything goes on the island (x from the island's left edge)
# ================================================================================================
ISLAND_WIDTH = 220
LAYOUT = {
    "Gate": 30,
    "MainHall": 74,
    "Pagoda": 143,                # 2026-11-19: 33 wide (was 27 at 146): its eaves sweep out further
    "Pavilion": 180,
}
TERRACE = (26, 200)               # jade brick under the buildings and the forecourt
POND = (11, 24)                   # the koi pond in the west garden (on the island's flat top: x 8-212); 14 wide since
                                  # 2026-11-12 (6 deep in CoghavenPass): 84 water tiles, vanilla fishes only in 75+
LAMPS = (25, 58, 66, 140, 176, 202)                          # Dynasty lamps along the terrace and the gardens
TREES = (8, 206, 211)            # sakura in the gardens, where the top is flat (vanilla's grower needs grass either side)
TURBINES = (38, 72, 108, 144, 178)
COG_SOCKETS = ((14, 0, 3), (28, 1, 2), (58, 0, 2), (90, 1, 2), (126, 0, 2), (152, 1, 2), (184, 0, 2), (198, 1, 3))
#                (x, style, rows above the island's bottom): eight cogs turning in the cloud of its flanks and keel


def all_plans():
    hall, shaft = main_hall()
    deck = vault(shaft)
    pagodas = [pagoda(n) for n in (5, 4, 3, 2)]
    return [gate(), hall, *pagodas, pavilion(), deck], shaft


def check(plan):
    """The plan's rows with blank rows at the top dropped (the bottom row stays on the surface: only the top is
    trimmed, so heights measure what is really built)."""
    rows = plan.rows()
    assert all(len(r) == plan.w for r in rows), plan.name
    while len(rows) > 1 and not rows[0].strip():
        rows = rows[1:]
    return rows


def write_cs(plans, shaft):
    L = ["// <auto-generated> by art/coghaven/make_coghaven_blueprints.py - do not edit by hand. </auto-generated>",
         "namespace Cogpunk.Content.Coghaven.Generation",
         "{",
         "\t/// <summary>Coghaven's buildings as ASCII rows (top to bottom, equal widths; the last row is laid on the island's",
         "\t/// surface row, the engine deck's first row on it too). The legend is in art/coghaven/make_coghaven_blueprints.py",
         "\t/// and <see cref=\"CoghavenPass\"/>; where each goes: the X constants below (from the island's left edge).</summary>",
         "\tinternal static class CoghavenBlueprints",
         "\t{",
         "\t\tpublic const int IslandWidth = %d;" % ISLAND_WIDTH,
         "\t\tpublic const int GateX = %d, MainHallX = %d, PagodaX = %d, PavilionX = %d;" % (
             LAYOUT["Gate"], LAYOUT["MainHall"], LAYOUT["Pagoda"], LAYOUT["Pavilion"]),
         "\t\tpublic const int TerraceLeft = %d, TerraceRight = %d, PondLeft = %d, PondRight = %d;" % (TERRACE + POND),
         "\t\t/// <summary>The vault's x 0 is the Main Hall's; the hall's stair shaft starts at this column of both.</summary>",
         "\t\tpublic const int ShaftX = %d;" % shaft,
         "\t\t/// <summary>The Jade Vault's unbreakable shell (vault coordinates: x from the Main Hall's x 0, rows from the island's",
         "\t\t/// surface row), inclusive; the arena is the inside of it.</summary>",
         "\t\tpublic const int VaultLeft = %d, VaultRight = %d, VaultTop = %d, VaultFloor = %d;" % (VAULT_X0, VAULT_X1, VAULT_TOP, VAULT_FLOOR),
         "\t\tpublic static readonly int[] TurbineX = { %s };" % ", ".join(str(x) for x in TURBINES),
         "\t\tpublic static readonly int[] LampX = { %s };" % ", ".join(str(x) for x in LAMPS),
         "\t\tpublic static readonly int[] TreeX = { %s };" % ", ".join(str(x) for x in TREES),
         "\t\tpublic static readonly int[] CogSocketX = { %s };" % ", ".join(str(x) for x, _, _ in COG_SOCKETS),
         "\t\tpublic static readonly int[] CogSocketStyle = { %s };" % ", ".join(str(s) for _, s, _ in COG_SOCKETS),
         "\t\tpublic static readonly int[] CogSocketLift = { %s };" % ", ".join(str(l) for _, _, l in COG_SOCKETS),
         ""]
    for plan in plans:
        rows = check(plan)
        L.append("\t\tpublic static readonly string[] %s = {" % plan.name)
        for r in rows:
            L.append("\t\t\t\"%s\"," % r.replace("\\", "\\\\"))
        L.append("\t\t};")
        L.append("")
    L.append("\t\t/// <summary>The pagodas from the tallest down: the pass builds the tallest that fits under the sky's ceiling.</summary>")
    L.append("\t\tpublic static readonly string[][] Pagodas = { Pagoda5, Pagoda4, Pagoda3, Pagoda2 };")
    L.append("\t}")
    L.append("}")
    path = os.path.join(ROOT, OUT_CS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("wrote %s" % OUT_CS)


KEY = {"F": (196, 180, 150), "f": (196, 180, 150), "R": (168, 44, 42), "r": (168, 44, 42), "G": (138, 93, 34), "g": (138, 93, 34),
       "T": (30, 114, 88), "Y": (223, 185, 78), "/": (30, 114, 88), "\\": (30, 114, 88), "(": (196, 180, 150), ")": (196, 180, 150),
       "-": (30, 114, 88), ".": (84, 20, 28), ",": (104, 84, 64), ":": (90, 58, 23), "#": (184, 138, 51), "=": (146, 86, 42),
       "+": (146, 86, 42), "%": (146, 86, 42), "w": (44, 92, 176), "~": (44, 92, 176), "X": (61, 66, 78), "x": (61, 66, 78),
       ";": (46, 50, 59), "$": (146, 86, 42), "m": (226, 222, 206)}


def png(plans, path):
    from PIL import Image, ImageDraw
    S = 6
    width = sum(p.w for p in plans) * S + 20 * len(plans)
    height = max(p.h for p in plans) * S + 20
    img = Image.new("RGB", (width, height), (150, 190, 230))
    d = ImageDraw.Draw(img)
    ox = 10
    for p in plans:
        oy = height - 10 - p.h * S
        for y, row in enumerate(p.rows()):
            for x, ch in enumerate(row):
                if ch == " ":
                    continue
                X, Y = ox + x * S, oy + y * S
                col = KEY.get(ch, (255, 255, 255))
                if ch in "/(":
                    d.polygon([(X, Y + S), (X + S, Y), (X + S, Y + S)], fill=col)
                elif ch in "\\)":
                    d.polygon([(X, Y), (X + S, Y + S), (X, Y + S)], fill=col)
                elif ch == "-":
                    d.rectangle([X, Y + S // 2, X + S - 1, Y + S - 1], fill=col)
                elif ch in "=+%$":
                    d.rectangle([X, Y, X + S - 1, Y + 1], fill=col)
                elif ch in KEY:
                    d.rectangle([X, Y, X + S - 1, Y + S - 1], fill=col)
                else:
                    d.rectangle([X, Y, X + S - 1, Y + S - 1], fill=(255, 255, 255))
                    d.text((X, Y - 2), ch, fill=(0, 0, 0))
        ox += p.w * S + 20
    img.save(path)
    print("wrote %s" % path)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--png")
    args = a.parse_args()
    plans, shaft = all_plans()
    write_cs(plans, shaft)
    if args.png:
        png(plans, args.png)


if __name__ == "__main__":
    main()
