"""Night Shift - painted for the top of Striker's website, where it sits behind "Welcome To My Website".

Somewhere under the aurora a cabin keeps one window lit: someone inside is taking a world apart to see how it
works. The left half is kept quiet (sky, still water) because that is where the site's words sit; the story is on
the right. 480x270, so it is exactly 4x on a 1920-wide screen. Plain Python 3, no libraries (pixelkit lives with
the postcards). Writes "Night Shift.png" (4x) and "Night Shift - 480x270.png" (1x, what the website scales).
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True                # importing pixelkit must not leave a __pycache__ in the postcards' folder
sys.path.insert(0, os.path.join(HERE, "..", "2026-10-06 Postcards"))
from pixelkit import Canvas, Noise, gradient, mix, add, scale  # noqa: E402

W, H = 480, 270
LAKE = 214                                    # the waterline
cv = Canvas(W, H)
nz = Noise(2026)
rng = random.Random(1006)


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---- the sky, the Milky Way, the stars -----------------------------------------------------------------------
SKY = [(0.00, (0.012, 0.014, 0.055)), (0.45, (0.055, 0.04, 0.14)), (0.78, (0.16, 0.075, 0.24)), (1.00, (0.32, 0.13, 0.33))]
for y in range(LAKE):
    base = gradient(SKY, y / LAKE)
    for x in range(W):
        cv.put(x, y, base)


def band_dist(x, y):                          # distance from the Milky Way's spine, rising to the right
    return (y - (150 - 0.27 * x)) / 1.05


for y in range(LAKE):
    for x in range(W):
        d = band_dist(x, y)
        k = math.exp(-((d / 30) ** 2))
        if k < 0.01:
            continue
        dust = nz.fbm2(x * 0.03, y * 0.05, 5)
        lane = max(0.0, nz.fbm2(x * 0.05 + 50, y * 0.08 + 9, 4) - 0.55) * 2.4   # the dark lanes
        glow = k * max(0.0, dust - 0.32) * 0.5 * (1 - min(1.0, lane))
        cv.glow(x, y, mix((0.55, 0.50, 0.78), (0.75, 0.62, 0.70), dust), glow * 0.55)

TINTS = [(1, 1, 1), (0.75, 0.85, 1.0), (1.0, 0.82, 0.88), (1.0, 0.94, 0.80)]
for i in range(1100):
    x, y = rng.randrange(W), rng.randrange(LAKE - 20)
    in_band = math.exp(-((band_dist(x, y) / 30) ** 2))
    if i > 650 and rng.random() > in_band:     # the later stars crowd into the Milky Way
        continue
    b = rng.random() ** 2.6
    t = rng.choice(TINTS)
    cv.glow(x, y, t, 0.18 + 0.75 * b)
    if b > 0.62:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.glow(x + dx, y + dy, t, 0.22 * b)

# ---- the aurora: curtains hanging from a ribbon, brighter toward the right ---------------------------------------
for x in range(W):                            # a short curtain: green at its hem, violet above, folded
    centre = 72 + 12 * math.sin(0.011 * x + 0.6) + 6 * math.sin(0.037 * x + 2.2) + 2.5 * math.sin(0.13 * x)
    fold = 0.62 + 0.38 * math.sin(0.55 * x + 0.4 * math.sin(0.07 * x))
    rays = 0.8 + 0.2 * math.sin(1.7 * x)
    amp = 0.03 + 0.34 * smooth(70, 430, x)
    for y in range(0, 150):
        d = y - centre
        k = math.exp(-((d / 4.0) ** 2)) if d > 0 else math.exp(d / 15.0)
        k *= fold * rays * amp
        if k > 0.004:
            cv.glow(x, y, mix((0.18, 0.95, 0.62), (0.62, 0.36, 1.0), min(1.0, max(0.0, -d / 26))), k)

# ---- a thin old moon, high on the left -----------------------------------------------------------------------
MX, MY = 62, 30
cv.halo(MX, MY, 7, (0.7, 0.68, 0.9), 0.18)
for y in range(MY - 7, MY + 8):
    for x in range(MX - 7, MX + 8):
        if math.hypot(x - MX, y - MY) <= 5.6 and math.hypot(x - MX + 2.6, y - MY + 1.2) > 5.2:
            cv.put(x, y, (0.90, 0.88, 0.96))

# ---- the ringed ice planet ------------------------------------------------------------------------------------
PX, PY, PR = 382, 74, 38
L = (-0.62, -0.42, 0.66)
n_ = math.sqrt(sum(v * v for v in L))
L = tuple(v / n_ for v in L)
TILT = -0.28
cv.halo(PX, PY, 30, (0.35, 0.55, 0.9), 0.10)


def ring_r(x, y):
    u, v = x - PX, y - PY
    ru = u * math.cos(TILT) - v * math.sin(TILT)
    rv = u * math.sin(TILT) + v * math.cos(TILT)
    return math.sqrt((ru / 74) ** 2 + (rv / 13) ** 2), rv


def ring_paint(x, y, front_only):
    r, rv = ring_r(x, y)
    if 0.6 < r < 1.0:
        front = rv > 0
        if front_only != front:
            return
        gap = 0.55 + 0.45 * math.sin(r * 61)
        a = max(0.0, min(0.85, 0.62 * gap * (1 - abs(r - 0.80) / 0.20)))
        if 0.835 < r < 0.86:
            a *= 0.15                               # the gap in the rings
        cv.blend(x, y, (0.93, 0.90, 0.82), a)


for y in range(PY - 30, PY + 31):             # the far side of the rings goes behind the planet
    for x in range(PX - 80, PX + 81):
        ring_paint(x, y, False)
for y in range(PY - PR - 1, PY + PR + 2):
    for x in range(PX - PR - 1, PX + PR + 2):
        u, v = x - PX, y - PY
        d2 = u * u + v * v
        if d2 > PR * PR:
            continue
        z = math.sqrt(PR * PR - d2)
        nx, ny, nzz = u / PR, v / PR, z / PR
        lam = max(0.0, nx * L[0] + ny * L[1] + nzz * L[2])
        band = 0.5 + 0.5 * math.sin(v * 0.42 + 2.4 * nz.n1(u * 0.06 + v * 0.02 + 30) + 0.5)
        base = mix((0.62, 0.86, 0.92), (0.30, 0.46, 0.74), band)
        base = mix(base, (0.86, 0.94, 0.98), max(0.0, -ny - 0.75) * 2.2)   # a pale polar cap
        rim = (1 - nzz) ** 3
        c = add(scale(base, 0.06 + 0.98 * lam), (0.35, 0.55, 1.0), 0.45 * rim)
        r, rv = ring_r(x, y)                    # the rings' shadow across the planet
        if 0.6 < (math.hypot((x + 6 - PX), (y - 5 - PY) * 2.4) / 64) < 1.0 and v > 2:
            c = scale(c, 0.55)
        cv.put(x, y, c)
for y in range(PY - 30, PY + 31):
    for x in range(PX - 80, PX + 81):
        ring_paint(x, y, True)

# ---- a floating island: blocks of earth, a tree, a waterfall into the haze --------------------------------------
IX, IY = 292, 130
STEPS = [(15, 0), (13, 4), (10, 8), (7, 12), (4, 16)]   # half-width, depth: stepped like stacked blocks
for half, dy in STEPS:
    for y in range(IY + dy, IY + dy + 4):
        for x in range(IX - half, IX + half):
            edge_r = x >= IX + half - 2
            c = (0.30, 0.20, 0.15) if (x // 4 + y // 4) % 2 else (0.26, 0.17, 0.13)
            if (x - IX) % 4 == 0 or (y - IY) % 4 == 0:
                c = scale(c, 0.8)               # the seams between blocks
            if edge_r:
                c = scale(c, 0.6)
            cv.put(x, y, c)
for x in range(IX - 15, IX + 15):             # grass on top, lit from the left
    cv.put(x, IY - 1, (0.36, 0.72, 0.34) if x < IX + 6 else (0.26, 0.52, 0.27))
    cv.put(x, IY, (0.24, 0.50, 0.26))
    if rng.random() < 0.35:
        cv.put(x, IY - 2, (0.30, 0.62, 0.30))
for y in range(IY - 7, IY - 1):               # a small tree
    cv.put(IX - 6, y, (0.22, 0.14, 0.10))
for y in range(IY - 14, IY - 5):
    for x in range(IX - 11, IX - 1):
        if math.hypot((x - (IX - 6)) * 0.9, y - (IY - 10)) < 4.6:
            cv.put(x, y, (0.14, 0.36, 0.20) if x < IX - 6 else (0.10, 0.26, 0.15))
cv.put(IX - 8, IY - 11, (0.30, 0.55, 0.32))
for y in range(IY + 1, IY + 46):              # the waterfall, thinning into mist
    t = (y - IY) / 46
    for x, k in ((IX + 9, 1.0), (IX + 10, 0.8)):
        cv.blend(x + int(1.2 * math.sin(y * 0.4)), y, (0.62, 0.82, 1.0), (1 - t) * 0.75 * k)
cv.halo(IX + 10, IY + 46, 6, (0.55, 0.7, 0.95), 0.12)

# ---- mountains across the lake ---------------------------------------------------------------------------------
def mountains(seed, base, count, hmin, hmax, smin, smax, rough):
    """A ridge made of real peaks: each falls away from its summit at its own slope; the highest wins."""
    r = random.Random(seed)
    peaks = [(r.uniform(-40, W + 40), r.uniform(hmin, hmax), r.uniform(smin, smax)) for _ in range(count)]
    prof = []
    for x in range(W):
        h = max(ph - s * abs(x - px) for px, ph, s in peaks)
        h += rough * (nz.fbm1(x * 0.21 + seed, 3) - 0.5) * 2
        prof.append(int(round(base - max(0.0, h))))
    return prof


far = mountains(11, 204, 11, 12, 44, 0.42, 0.95, 2.6)
near = mountains(29, 213, 26, 5, 17, 0.2, 0.48, 1.4)          # gentle and many: rolling foothills, not cones
for x in range(W):
    lit = far[max(0, x - 1)] > far[min(W - 1, x + 1)]          # this slope faces the moon (on the left)
    height = 204 - far[x]
    for y in range(far[x], LAKE):
        depth = (y - far[x]) / max(1, LAKE - far[x])
        c = mix((0.10, 0.07, 0.19), (0.24, 0.12, 0.30), depth ** 1.5)   # haze gathers at the foot
        if lit and y - far[x] < 6:
            c = mix(c, (0.20, 0.17, 0.34), 0.5 * (1 - (y - far[x]) / 6))
        if height > 24 and y - far[x] < 3 + (height - 24) // 6:   # snow on the high peaks
            c = (0.66, 0.62, 0.82) if lit else (0.36, 0.33, 0.52)
        cv.put(x, y, c)
for x in range(W):
    for y in range(near[x], LAKE):
        cv.put(x, y, (0.065, 0.05, 0.13))
    cv.put(x, near[x], (0.14, 0.11, 0.24))

# ---- the lake: the mountains and sky mirrored, darker, broken into ripples ----------------------------------------
for y in range(LAKE, H):
    depth = (y - LAKE) / (H - LAKE)
    for x in range(W):
        my = max(0, min(LAKE - 1, 2 * LAKE - y - 1 + int(2.5 * math.sin(x * 0.11 + y * 0.9))))
        refl = cv.get(x, my)
        water = mix(scale(refl, 0.62), (0.03, 0.035, 0.09), 0.25 + 0.5 * depth)
        if nz.n2(x * 0.09, y * 0.8) > 0.7:
            water = add(water, (0.45, 0.42, 0.70), 0.06 * (1 - depth))
        cv.put(x, y, water)
for x in range(W):                            # a thin bright line where the far shore meets the water
    cv.blend(x, LAKE, (0.42, 0.30, 0.52), 0.35)
for _ in range(70):                           # stars glinting on the water
    x, y = rng.randrange(W), rng.randrange(LAKE + 2, H - 4)
    cv.glow(x, y, (0.75, 0.75, 1.0), 0.08 + 0.22 * rng.random() ** 2 * (1 - (y - LAKE) / (H - LAKE)))

# ---- the hill on the right, the cabin, its light ----------------------------------------------------------------
def hill(x):
    return int(270 - max(0, x - 318) * 0.47 + 3 * nz.fbm1(x * 0.08 + 40)) if x >= 318 else H


HILL = (0.045, 0.04, 0.09)
for x in range(310, W):
    top = hill(x)
    for y in range(max(0, top), H):
        cv.put(x, y, HILL)
CABX, CABW = 392, 28
base_y = min(hill(x) for x in range(CABX, CABX + CABW)) + 1
for x in range(CABX - 3, CABX + CABW + 3):   # level the ground under the cabin
    for y in range(base_y, H):
        cv.put(x, y, HILL)
WOOD, WOOD_D, ROOF = (0.22, 0.13, 0.10), (0.15, 0.09, 0.07), (0.11, 0.075, 0.10)
for y in range(base_y - 14, base_y):
    for x in range(CABX, CABX + CABW):
        c = WOOD if (y - base_y) % 3 else WOOD_D            # the planks
        if x >= CABX + CABW - 3:
            c = scale(c, 0.65)
        cv.put(x, y, c)
peak_x, peak_y = CABX + CABW // 2, base_y - 25
for y in range(peak_y, base_y - 13):          # a steep roof with a little overhang
    half = int((y - peak_y) * 1.55) + 1
    for x in range(peak_x - half, peak_x + half + 1):
        if CABX - 3 <= x <= CABX + CABW + 2:
            cv.put(x, y, ROOF if x < peak_x + half - 1 else scale(ROOF, 0.7))
for x in range(CABX - 3, CABX + CABW + 3):
    cv.put(x, base_y - 14, (0.20, 0.14, 0.18))
for y in range(peak_y - 2, base_y - 19):      # the chimney
    for x in range(CABX + CABW - 8, CABX + CABW - 5):
        cv.put(x, y, (0.18, 0.12, 0.12))
for i in range(18):                           # smoke, drifting left
    t = i / 18
    sx = CABX + CABW - 7 - t * 30 + 2 * math.sin(i * 1.3)
    sy = peak_y - 4 - t * 26
    cv.halo(sx, sy, 1.2 + 2.2 * t, (0.55, 0.50, 0.62), 0.16 * (1 - t))
# the window: a desk lamp's warm light, and the cyan of a screen with someone in front of it
WX0, WY0, WX1, WY1 = CABX + 5, base_y - 11, CABX + 15, base_y - 4
cv.halo((WX0 + WX1) / 2, (WY0 + WY1) / 2, 14, (1.0, 0.62, 0.30), 0.22)
for y in range(WY0, WY1):
    for x in range(WX0, WX1):
        cv.put(x, y, mix((1.0, 0.78, 0.45), (1.0, 0.58, 0.30), (y - WY0) / (WY1 - WY0)))
for y in range(WY0 + 1, WY0 + 4):
    for x in range(WX0 + 5, WX0 + 9):
        cv.put(x, y, (0.45, 0.95, 1.0))      # the monitor
cv.halo(WX0 + 7, WY0 + 2.5, 3, (0.35, 0.85, 1.0), 0.35)
for (x, y) in ((WX0 + 3, WY0 + 2), (WX0 + 3, WY0 + 3), (WX0 + 2, WY0 + 3), (WX0 + 4, WY0 + 3),
               (WX0 + 2, WY0 + 4), (WX0 + 3, WY0 + 4), (WX0 + 4, WY0 + 4), (WX0 + 2, WY0 + 5),
               (WX0 + 3, WY0 + 5), (WX0 + 4, WY0 + 5), (WX0 + 2, WY0 + 6), (WX0 + 3, WY0 + 6), (WX0 + 4, WY0 + 6)):
    cv.put(x, y, (0.10, 0.06, 0.08))          # the modder, from behind
for x in range(WX0 - 1, WX1 + 1):
    cv.put(x, WY0 - 1, WOOD_D)
    cv.put(x, WY1, WOOD_D)
for y in range(WY0, WY1):
    cv.put(WX0 - 1, y, WOOD_D)
    cv.put(WX1, y, WOOD_D)
    cv.put((WX0 + WX1) // 2 - 3, y, scale(WOOD_D, 1.3) if y == (WY0 + WY1) // 2 else cv.get((WX0 + WX1) // 2 - 3, y))
for y in range(base_y - 10, base_y):          # the door, a crack of light at its edge
    for x in range(CABX + 19, CABX + 24):
        cv.put(x, y, (0.09, 0.055, 0.05))
    cv.put(CABX + 23, y, (0.80, 0.52, 0.28))
for x in range(CABX - 6, CABX + 14):          # light spilling onto the grass below the window
    for y in range(base_y, base_y + 4):
        cv.blend(x, y, (0.60, 0.38, 0.20), 0.35 * (1 - (y - base_y) / 4) * math.exp(-((x - (WX0 + WX1) / 2) / 8) ** 2))
AX = peak_x - 4                                # the antenna and its red light
for y in range(peak_y - 13, peak_y + 2):
    cv.put(AX, y, (0.30, 0.26, 0.34))
for d in range(-3, 4):
    cv.put(AX + d, peak_y - 9 + abs(d) // 2, (0.42, 0.38, 0.48))
cv.put(AX, peak_y - 14, (1.0, 0.25, 0.22))
cv.halo(AX, peak_y - 14, 2.2, (1.0, 0.2, 0.15), 0.55)
for x in range(310, W):                       # grass along the hilltop, catching a little light
    top = hill(x)
    if top < H and not (CABX - 3 <= x < CABX + CABW + 3):
        warm = math.exp(-((x - (WX0 + WX1) / 2) / 26) ** 2)
        cv.put(x, top, mix((0.12, 0.16, 0.20), (0.62, 0.44, 0.26), warm))
        if rng.random() < 0.4:
            cv.put(x, top - 1, mix((0.10, 0.14, 0.18), (0.50, 0.36, 0.22), warm))

# ---- the jetty, and someone on the end of it with a lantern -----------------------------------------------------
JY = LAKE + 12
JX0, JX1 = 282, 336
for x in range(JX0, JX1):
    cv.put(x, JY, (0.30, 0.20, 0.16))
    cv.put(x, JY + 1, (0.13, 0.085, 0.07))
for px in range(JX0 + 3, JX1, 12):            # posts, and their reflections
    for y in range(JY + 2, JY + 7):
        cv.put(px, y, (0.09, 0.06, 0.06))
    for y in range(JY + 7, JY + 11):
        cv.blend(px, y, (0.09, 0.06, 0.06), 0.4)
FX = JX0 + 6                                  # a small figure sitting, legs over the edge, looking up
for (dx, dy) in ((0, -7), (1, -7), (0, -6), (1, -6), (0, -5), (1, -5), (-1, -4), (0, -4), (1, -4), (2, -4),
                 (-1, -3), (0, -3), (1, -3), (2, -3), (-1, -2), (0, -2), (1, -2), (2, -2), (-1, -1), (0, -1), (1, -1)):
    cv.put(FX + dx, JY + dy, (0.03, 0.025, 0.05))
for (dx, dy) in ((-1, 0), (-1, 1), (-1, 2), (0, 2)):
    cv.put(FX + dx, JY + dy, (0.03, 0.025, 0.05))
cv.put(FX + 2, JY - 7, (0.35, 0.40, 0.65))   # moonlight catching the top of a hood
for (dx, dy) in ((2, -4), (2, -3), (2, -2), (1, -1)):
    cv.put(FX + dx, JY + dy, (0.42, 0.24, 0.12))   # the lantern's warmth on their side
LX_, LY_ = FX + 6, JY - 2                     # the lantern
cv.put(LX_, LY_, (1.0, 0.85, 0.50))
cv.put(LX_, LY_ - 1, (0.25, 0.18, 0.14))
cv.halo(LX_, LY_, 6, (1.0, 0.65, 0.30), 0.32)
for y in range(JY + 2, H):                    # its reflection, a broken streak of light in the water
    t = (y - JY) / (H - JY)
    if nz.n2(LX_ * 0.2, y * 0.7) > 0.35:
        for dx in (-1, 0, 1):
            cv.glow(LX_ + dx + int(1.5 * math.sin(y * 0.6)), y, (1.0, 0.62, 0.30), 0.22 * (1 - t) * (1 - abs(dx) * 0.5))

# ---- fireflies, a shooting star ------------------------------------------------------------------------------------
for _ in range(16):
    x = rng.uniform(345, 478)
    y = rng.uniform(hill(int(x)) - 20, hill(int(x)) - 2)
    cv.put(int(x), int(y), (0.85, 1.0, 0.55))
    cv.halo(x, y, 1.4, (0.7, 1.0, 0.4), 0.25)
for k in range(22):
    t = k / 22
    cv.glow(int(150 + 34 * t), int(16 + 11 * t), (1.0, 0.96, 0.88), 0.55 * t)

cv.vignette(0.32)
out4 = cv.save(os.path.join(HERE, "Night Shift.png"), pixel=4)
out1 = cv.save(os.path.join(HERE, "Night Shift - 480x270.png"), pixel=1)
print("wrote", out4)
print("wrote", out1)
