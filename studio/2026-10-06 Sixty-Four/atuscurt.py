"""A night on Atuscurt: pixel art painted by code, no libraries. 320 x 180, scaled 4x to 1280 x 720."""
import math
import os
import random
import struct
import zlib

W, H, SCALE = 320, 180, 4
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "A night on Atuscurt.png")
rng = random.Random(64)        # sixty-four blocks

img = [[(0.0, 0.0, 0.0)] * W for _ in range(H)]


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def add(c, d, k=1.0):
    return tuple(x + y * k for x, y in zip(c, d))


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img[y][x] = c


def blend(x, y, c, a):
    if 0 <= x < W and 0 <= y < H:
        img[y][x] = mix(img[y][x], c, a)


# ---- value noise ---------------------------------------------------------------------------------------------
_lat = [rng.random() for _ in range(1024)]


def vnoise(x):
    i = math.floor(x)
    f = x - i
    a, b = _lat[i % 1024], _lat[(i + 1) % 1024]
    f = f * f * (3 - 2 * f)
    return a + (b - a) * f


def fbm(x, octaves=4):
    s, amp, fr, norm = 0.0, 1.0, 1.0, 0.0
    for _ in range(octaves):
        s += amp * vnoise(x * fr)
        norm += amp
        amp *= 0.5
        fr *= 2.03
    return s / norm


# ---- the sky ---------------------------------------------------------------------------------------------------
TOP, MID, HORIZON = (0.015, 0.02, 0.10), (0.09, 0.05, 0.21), (0.32, 0.12, 0.36)
for y in range(H):
    t = y / (H * 0.74)
    c = mix(TOP, MID, min(t / 0.55, 1.0)) if t < 0.55 else mix(MID, HORIZON, min((t - 0.55) / 0.45, 1.0))
    for x in range(W):
        img[y][x] = c

# stars: many faint, a few bright with a cross of light
stars = []
for _ in range(330):
    x, y = rng.randrange(W), rng.randrange(int(H * 0.72))
    b = rng.random() ** 2.2
    tint = rng.choice([(1.0, 1.0, 1.0), (0.75, 0.85, 1.0), (1.0, 0.8, 0.9), (1.0, 0.95, 0.8)])
    stars.append((x, y, b, tint))
for x, y, b, tint in stars:
    put(x, y, add(img[y][x], tint, 0.25 + 0.75 * b))
    if b > 0.62:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            blend(x + dx, y + dy, tint, 0.35 * b)

# aurora: a curtain that hangs from a wavering line and fades upward
for x in range(W):
    centre = 50 + 9 * math.sin(0.031 * x + 0.4) + 4 * math.sin(0.11 * x + 2.1)
    streak = 0.55 + 0.45 * math.sin(0.9 * x + 0.3 * math.sin(0.2 * x))
    col = mix((0.15, 0.95, 0.65), (0.55, 0.35, 1.0), 0.5 + 0.5 * math.sin(0.012 * x + 1.3))
    for y in range(0, 110):
        d = y - centre
        k = math.exp(-(d / 4.5) ** 2) if d > 0 else math.exp(d / 22.0)
        k *= streak * 0.32
        if k > 0.004:
            img[y][x] = add(img[y][x], col, k)

# the ringed planet, low in the east, lit from the upper left
PX, PY, PR = 252, 42, 19
LIGHT = (-0.6, -0.55, 0.58)
ln = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / ln for v in LIGHT)


def ring_hit(x, y):
    """Distance through the ring's ellipse, tilted - None when off the ring."""
    u, v = x - PX, y - PY
    ang = -0.22
    ru = u * math.cos(ang) - v * math.sin(ang)
    rv = u * math.sin(ang) + v * math.cos(ang)
    r = math.sqrt((ru / 36.0) ** 2 + (rv / 7.5) ** 2)
    if 0.66 < r < 1.0:
        return r, rv
    return None


for y in range(PY - 30, PY + 30):
    for x in range(PX - 44, PX + 44):
        u, v = x - PX, y - PY
        d2 = u * u + v * v
        hit = ring_hit(x, y)
        on_planet = d2 <= PR * PR
        if on_planet:
            z = math.sqrt(max(PR * PR - d2, 0.0))
            n = (u / PR, v / PR, z / PR)
            lam = max(0.0, n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2])
            band = 0.5 + 0.5 * math.sin(v * 0.62 + 2.2 * vnoise(u * 0.3 + 40) + 0.8)
            base = mix((0.95, 0.60, 0.42), (0.80, 0.36, 0.52), band)
            c = tuple(ch * (0.08 + 0.95 * lam) for ch in base)
            rim = max(0.0, 1.0 - z / PR) ** 3
            c = add(c, (0.55, 0.35, 0.75), 0.35 * rim)
            img[y][x] = c
        if hit:
            r, rv = hit
            in_front = rv > 0           # the near half crosses in front of the planet
            if on_planet and not in_front:
                continue
            gap = 0.55 + 0.45 * math.sin(r * 58.0)
            a = 0.55 * gap * (1.0 - abs(r - 0.83) / 0.17)
            shade = 0.45 if (on_planet and in_front) else 1.0
            blend(x, y, tuple(ch * shade for ch in (0.95, 0.88, 0.76)), max(0.0, min(a, 0.8)))

# ---- the land ----------------------------------------------------------------------------------------------------
far = [int(118 + 11 * fbm(x * 0.018 + 3.0) + 4 * math.sin(x * 0.05)) for x in range(W)]
near = [int(143 + 15 * fbm(x * 0.024 + 7.0) + 6 * math.sin(x * 0.03 + 1.0)) for x in range(W)]

FAR_COL, NEAR_COL = (0.11, 0.065, 0.21), (0.055, 0.045, 0.13)
for x in range(W):
    for y in range(far[x], H):
        depth = (y - far[x]) / 30.0
        haze = max(0.0, 1.0 - depth) * 0.22
        img[y][x] = mix(FAR_COL, HORIZON, haze)
    put(x, far[x], (0.33, 0.20, 0.48))                 # the ridge line, so the face has ground to stand on

# the creeper face: 8 x 8 cells of 3 pixels, standing on the far hill
FACE = ["........", "........", ".##..##.", ".##..##.", "...##...", "..####..", "..####..", "..#..#.."]
CELL, CX = 4, 148
HALF = 4 * CELL
base_y = min(far[CX - HALF:CX + HALF]) + 2
FX0, FY0 = CX - HALF, base_y - 8 * CELL
GLOW = (0.45, 0.65, 0.95)
gcx, gcy = CX, base_y - HALF
for y in range(max(0, gcy - 60), min(H, gcy + 60)):
    for x in range(max(0, gcx - 80), min(W, gcx + 80)):
        d = math.hypot((x - gcx) * 0.8, y - gcy)
        k = math.exp(-(d / 22.0) ** 2) * 0.55 + math.exp(-(d / 7.0) ** 2) * 0.25
        img[y][x] = add(img[y][x], GLOW, k)
def dark(r, c):
    return 0 <= r < 8 and 0 <= c < 8 and FACE[r][c] == "#"


for r, line in enumerate(FACE):
    for c, ch in enumerate(line):
        for dy in range(CELL):
            for dx in range(CELL):
                x, y = FX0 + c * CELL + dx, FY0 + r * CELL + dy
                if ch != "#":
                    put(x, y, (0.93, 0.97, 1.0))
                    continue
                # frame only the OUTSIDE of each dark shape: lit on the top/left, shaded on the bottom/right
                lit = (dx == 0 and not dark(r, c - 1)) or (dy == 0 and not dark(r - 1, c))
                shade = (dx == CELL - 1 and not dark(r, c + 1)) or (dy == CELL - 1 and not dark(r + 1, c))
                put(x, y, (0.30, 0.55, 0.98) if lit else (0.10, 0.20, 0.45) if shade else (0.03, 0.04, 0.09))

# the near hill, with a rim of the creeper's light
for x in range(W):
    for y in range(near[x], H):
        img[y][x] = NEAR_COL
    prox = math.exp(-((x - CX) / 70.0) ** 2)
    put(x, near[x], add(NEAR_COL, (0.30, 0.50, 0.85), 0.25 + 0.55 * prox))

# alien flora: curling stalks, some with glowing spores
for i in range(16):
    x0 = 8 + i * 19 + rng.randrange(-6, 7)
    if abs(x0 - 100) < 10:
        continue                                   # leave room for the traveller
    h = rng.randrange(9, 23)
    lean = rng.uniform(-0.25, 0.25)
    gx, gy = x0, near[x0]
    for k in range(h):
        gx2 = x0 + lean * k + 1.2 * math.sin(k * 0.35 + i)
        put(int(round(gx2)), gy - k, (0.03, 0.025, 0.07))
    tx, ty = int(round(x0 + lean * h)), gy - h
    for a in range(0, 300, 30):                    # the curl at the top
        rr = 2.6 * (1 - a / 360.0)
        put(int(round(tx + rr * math.cos(math.radians(a)))), int(round(ty + rr * math.sin(math.radians(a)))),
            (0.04, 0.03, 0.09))
    if rng.random() < 0.6:
        spore = rng.choice([(0.3, 1.0, 0.8), (1.0, 0.45, 0.85), (0.6, 0.8, 1.0)])
        for _ in range(rng.randrange(1, 4)):
            sx, sy = tx + rng.randrange(-4, 5), ty + rng.randrange(-5, 2)
            put(sx, sy, spore)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                blend(sx + dx, sy + dy, spore, 0.25)

# the traveller: a blocky silhouette looking up at the face, lit from the right by it
SX = 100
sy = near[SX]
FIG = ["..###..", "..###..", "..###..", ".#####.", ".#####.", ".#####.", "..#.#..", "..#.#..", "..#.#.."]
for r, line in enumerate(FIG):
    for c, ch in enumerate(line):
        if ch == "#":
            x, y = SX - 3 + c, sy - len(FIG) + r
            lit = c + 1 < len(line) and line[c + 1] != "#"
            put(x, y, (0.30, 0.48, 0.80) if lit else (0.01, 0.01, 0.03))

# vignette
for y in range(H):
    for x in range(W):
        u, v = (x / W - 0.5) * 1.6, (y / H - 0.5) * 1.6
        k = 1.0 - 0.55 * (u * u + v * v)
        img[y][x] = tuple(ch * k for ch in img[y][x])

# ---- write the PNG, scaled up with hard pixels ---------------------------------------------------------------------
def to8(v):
    v = max(0.0, min(1.0, v))
    return int(round((v ** (1 / 1.1)) * 255))


rows = []
for y in range(H):
    line = bytearray()
    for x in range(W):
        r, g, b = (to8(ch) for ch in img[y][x])
        line += bytes((r, g, b)) * SCALE
    for _ in range(SCALE):
        rows.append(b"\x00" + bytes(line))
raw = b"".join(rows)


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W * SCALE, H * SCALE, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
with open(OUT, "wb") as fh:
    fh.write(png)
print("wrote", OUT, len(png), "bytes")
