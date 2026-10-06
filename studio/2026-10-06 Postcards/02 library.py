"""Postcard 2 - The Library That Opens When It Snows. A stone library in a pine wood, its windows full of books."""
import math
import os
import random

from pixelkit import Canvas, Noise, gradient, mix, add, scale

W, H = 320, 180
cv = Canvas(W, H)
nz = Noise(22)
rng = random.Random(22)

WARM = (1.0, 0.76, 0.42)
SNOW = (0.80, 0.85, 0.96)

# sky and moon
SKY = [(0.0, (0.03, 0.04, 0.12)), (0.6, (0.09, 0.12, 0.26)), (1.0, (0.20, 0.24, 0.40))]
for y in range(H):
    c = gradient(SKY, y / 120)
    for x in range(W):
        cv.put(x, y, c)
for _ in range(70):
    cv.glow(rng.randrange(W), rng.randrange(80), (0.9, 0.95, 1.0), 0.15 + 0.4 * rng.random() ** 2)
MX, MY = 262, 30
cv.halo(MX, MY, 14, (0.55, 0.65, 0.95), 0.45)
cv.disc(MX, MY, 8, (0.92, 0.94, 1.0))
for dx, dy, r in ((-2.5, -2, 2.2), (3, 1.5, 1.8), (-0.5, 3.5, 1.4)):   # a few soft maria
    cv.disc(MX + dx, MY + dy, r, (0.80, 0.83, 0.93), 0.7)

# far hills under snow
far = [int(108 + 10 * nz.fbm1(x * 0.015 + 2)) for x in range(W)]
for x in range(W):
    for y in range(far[x], H):
        cv.put(x, y, mix((0.42, 0.48, 0.66), (0.25, 0.30, 0.48), min(1.0, (y - far[x]) / 30)))


def pine(cx, base, h, body, snow, tiers=4):
    """A pine: stacked tiers, each wearing a cap of snow on its upper part and a ragged snowy hem."""
    for y in range(base - 3, base):
        cv.put(cx, y, scale(body, 0.6))
    top = base - h
    tier_h = h / tiers
    for t in range(tiers):
        y0 = top + t * tier_h * 0.8
        y1 = y0 + tier_h * 1.25
        rows = range(int(y0), int(min(y1, base - 2)))
        for y in rows:
            f = (y - y0) / (y1 - y0)
            half = f * (h * 0.32 + t * 1.5)
            for x in range(int(cx - half), int(cx + half) + 1):
                capped = f < 0.38 and nz.n2(x * 0.7, y * 0.7) > 0.25
                mottle = nz.n2(x * 0.9 + 50, y * 0.9) > 0.72
                cv.put(x, y, snow if (capped or mottle) else body)
        hem = int(min(y1, base - 2)) - 1                          # snow caught on the tier's lower edge
        half = (hem - y0) / (y1 - y0) * (h * 0.32 + t * 1.5)
        for x in range(int(cx - half), int(cx + half) + 1):
            if nz.n1(x * 0.8 + t * 9) > 0.45:
                cv.put(x, hem, snow)


for i in range(26):                                             # the back row of pines
    x = rng.randrange(-5, W + 5)
    if 70 < x < 175:
        continue
    pine(x, far[min(max(x, 0), W - 1)] + 6, rng.randrange(18, 30), (0.10, 0.15, 0.24), (0.55, 0.62, 0.80), 3)

# the ground: snow in soft drifts
ground = [int(132 + 4 * nz.fbm1(x * 0.03 + 9)) for x in range(W)]
for x in range(W):
    for y in range(ground[x], H):
        d = nz.fbm2(x * 0.05, y * 0.12, 3)
        cv.put(x, y, mix(SNOW, (0.55, 0.62, 0.82), 0.35 + 0.4 * d + 0.25 * (y - ground[x]) / 50))

# the library
LX0, LX1 = 82, 168
WALL_TOP, WALL_BOT = 98, min(ground[LX0:LX1]) + 2
for y in range(WALL_TOP, WALL_BOT):
    for x in range(LX0, LX1):
        brick = ((x + (4 if (y // 4) % 2 else 0)) % 8 == 0) or y % 4 == 0
        c = (0.30, 0.31, 0.40) if not brick else (0.22, 0.23, 0.31)
        cv.put(x, y, c)
for y in range(WALL_TOP - 30, WALL_TOP + 1):                    # the roof, heavy with snow
    half = (y - (WALL_TOP - 30)) * 1.55
    for x in range(int((LX0 + LX1) / 2 - half) - 2, int((LX0 + LX1) / 2 + half) + 3):
        cv.put(x, y, (0.18, 0.13, 0.17))
    for x in range(int((LX0 + LX1) / 2 - half) - 2, int((LX0 + LX1) / 2 + half) + 3):
        if y - (WALL_TOP - 30) < 26 and (y % 3 != 0 or abs(x - (LX0 + LX1) / 2) < half - 4):
            cv.put(x, y, mix(SNOW, (0.62, 0.68, 0.86), 0.25 + 0.3 * nz.n2(x * 0.2, y * 0.2)))
CHX = 148                                                        # chimney and its smoke
cv.rect(CHX, WALL_TOP - 30, CHX + 7, WALL_TOP - 14, (0.26, 0.20, 0.22))
cv.rect(CHX - 1, WALL_TOP - 32, CHX + 8, WALL_TOP - 29, SNOW)
for k in range(40):
    sx = CHX + 3 + 6 * math.sin(k * 0.25) + k * 0.6
    sy = WALL_TOP - 34 - k * 1.1
    cv.disc(sx, sy, 1.5 + k * 0.08, (0.60, 0.62, 0.72), 0.10 * (1 - k / 40))

BOOK = [(0.75, 0.25, 0.22), (0.25, 0.45, 0.70), (0.85, 0.70, 0.30), (0.30, 0.55, 0.35), (0.55, 0.30, 0.55),
        (0.80, 0.50, 0.30)]


def window(x0, y0, w, h):
    """An arched window, lit from inside, with shelves of book spines."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if y - y0 < w // 2:                                  # the arch
                dx, dy = x - (x0 + (w - 1) / 2), (y0 + w // 2) - y
                if dx * dx + dy * dy > (w / 2) ** 2:
                    continue
            row = (y - y0 - 2) % 6
            if row == 5 and y > y0 + 3:
                c = (0.45, 0.28, 0.16)                           # a shelf
            elif y > y0 + 3:
                c = mix(WARM, rng.choice(BOOK), 0.55) if rng.random() < 0.85 else WARM
            else:
                c = WARM
            cv.put(x, y, c)
    cv.halo(x0 + w / 2, y0 + h / 2, 6, WARM, 0.18)
    for x in range(x0 - 1, x0 + w + 1):                          # snow on the sill
        cv.put(x, y0 + h, SNOW)


for wx in (88, 106, 142, 158):
    window(wx, WALL_TOP + 6, 9, 15)
DX = 123                                                         # the door, ajar, warm light spilling out
cv.rect(DX, WALL_BOT - 22, DX + 11, WALL_BOT, (0.30, 0.18, 0.10))
cv.rect(DX + 2, WALL_BOT - 20, DX + 6, WALL_BOT, WARM)
cv.halo(DX + 4, WALL_BOT - 6, 9, WARM, 0.25)
for y in range(WALL_BOT, WALL_BOT + 14):                         # the spill of light across the snow
    for x in range(DX - 6, DX + 18):
        k = max(0.0, 1 - (y - WALL_BOT) / 14) * max(0.0, 1 - abs(x - DX - 4) / (6 + (y - WALL_BOT) * 0.8))
        cv.glow(x, y, (0.55, 0.35, 0.12), 0.45 * k)
cv.put(DX - 3, WALL_BOT - 15, (0.15, 0.10, 0.08))                # the lantern by the door
cv.rect(DX - 4, WALL_BOT - 14, DX - 1, WALL_BOT - 10, (1.0, 0.85, 0.5))
cv.halo(DX - 2.5, WALL_BOT - 12, 5, (1.0, 0.75, 0.4), 0.5)

# the OPEN sign, in a small pixel font (N needs four columns: three makes it read as M)
FONT = {"O": ["###", "#.#", "#.#", "#.#", "###"], "P": ["###", "#.#", "###", "#..", "#.."],
        "E": ["###", "#..", "##.", "#..", "###"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"]}
SX, SY = DX - 5, WALL_TOP - 1
cv.rect(SX - 2, SY - 2, SX + 20, SY + 7, (0.12, 0.08, 0.10))
cx = SX
for ch in "OPEN":
    for r, line in enumerate(FONT[ch]):
        for c, p in enumerate(line):
            if p == "#":
                cv.put(cx + c, SY + r, (1.0, 0.55, 0.45))
    cx += len(FONT[ch][0]) + 1
cv.halo(SX + 9, SY + 2, 6, (1.0, 0.4, 0.35), 0.25)

# the front row of pines, framing the scene
for x, h in ((12, 62), (40, 48), (196, 52), (226, 66), (262, 50), (300, 70)):
    pine(x, ground[min(x, W - 1)] + 4, h, (0.06, 0.09, 0.16), (0.70, 0.76, 0.92), 4)

# footprints to the door
for k in range(14):
    fy = H - 4 - k * 3
    fx = int(DX + 4 + (k - 13) * -2.2 + (2 if k % 2 else -2))
    if fy > WALL_BOT + 2:
        cv.put(fx, fy, (0.45, 0.52, 0.72))
        cv.put(fx + 1, fy, (0.45, 0.52, 0.72))

# falling snow: small and faint far away, larger and brighter close
for _ in range(420):
    x, y = rng.randrange(W), rng.randrange(H)
    near = rng.random()
    if near > 0.85:
        cv.blend(x, y, (1.0, 1.0, 1.0), 0.85)
        cv.blend(x + 1, y, (1.0, 1.0, 1.0), 0.6)
        cv.blend(x, y + 1, (1.0, 1.0, 1.0), 0.6)
    else:
        cv.blend(x, y, (0.92, 0.95, 1.0), 0.25 + 0.5 * near)

cv.vignette(0.5)
out = cv.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "02 The Library That Opens When It Snows.png"))
print("wrote", out)
