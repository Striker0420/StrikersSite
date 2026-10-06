"""Postcard 4 - The Last Train Across the Glass Desert. Sunset, a viaduct, and a desert where the sand is glass."""
import math
import os
import random

from pixelkit import Canvas, Noise, gradient, mix, add, scale

W, H = 320, 180
cv = Canvas(W, H)
nz = Noise(44)
rng = random.Random(44)

SKY = [(0.0, (0.10, 0.08, 0.28)), (0.40, (0.45, 0.20, 0.42)), (0.75, (0.95, 0.45, 0.35)), (1.0, (1.0, 0.72, 0.38))]
SX, SY, SR = 212, 98, 24

# the sky, with a few long clouds lit from below
for y in range(H):
    base = gradient(SKY, min(1.0, y / 112))
    for x in range(W):
        cl = nz.fbm2(x * 0.010, y * 0.11, 4)
        band = max(0.0, cl - 0.55) * 3.0 * (y / 112)
        cv.put(x, y, mix(base, (1.0, 0.62, 0.55), min(0.7, band)))
for _ in range(30):
    cv.glow(rng.randrange(W), rng.randrange(30), (1.0, 0.95, 0.9), 0.2 + 0.4 * rng.random() ** 2)
cv.halo(SX, SY, 30, (1.0, 0.45, 0.25), 0.55)
for y in range(SY - SR, SY + SR + 1):                           # the sun, banded where the haze crosses it
    for x in range(SX - SR, SX + SR + 1):
        if (x - SX) ** 2 + (y - SY) ** 2 <= SR * SR:
            t = (y - (SY - SR)) / (2 * SR)
            c = gradient([(0, (1.0, 0.95, 0.70)), (1, (1.0, 0.55, 0.30))], t)
            if t > 0.55 and int(y - SY) % 4 == 0:
                c = mix(c, (0.95, 0.45, 0.40), 0.6)
            cv.put(x, y, c)

# far dunes, hazy
far = [int(116 + 6 * math.sin(x * 0.035 + 1.0) + 4 * nz.fbm1(x * 0.02 + 3)) for x in range(W)]
for x in range(W):
    for y in range(far[x], H):
        cv.put(x, y, mix((0.80, 0.42, 0.36), (0.55, 0.26, 0.30), min(1.0, (y - far[x]) / 25)))

# the viaduct: a deck on stone arches, in silhouette against the sun
DECK = 104
STONE = (0.20, 0.09, 0.15)
SPAN = 26
for x in range(W):
    for y in range(DECK, DECK + 5):
        cv.put(x, y, STONE)
    k = (x + 7) % SPAN
    pier = k < 5
    for y in range(DECK + 5, H):
        if pier:
            cv.put(x, y, STONE)
        else:
            u = (k - 5 - (SPAN - 5) / 2) / ((SPAN - 5) / 2)          # -1..1 across the opening
            arch_top = DECK + 5 + (1 - math.sqrt(max(0.0, 1 - u * u))) * 9
            if y < arch_top:
                cv.put(x, y, STONE)
    if x % 2 == 0:
        cv.put(x, DECK - 1, scale(STONE, 1.4))                       # the parapet

# the train, heading west, its smoke trailing back into the sunset
TX = 38
LOCO = (0.10, 0.05, 0.09)
cv.rect(TX, DECK - 11, TX + 22, DECK - 1, LOCO)                      # the engine
cv.rect(TX + 15, DECK - 16, TX + 22, DECK - 11, LOCO)                # the cab
cv.rect(TX + 4, DECK - 15, TX + 7, DECK - 11, LOCO)                  # the funnel
cv.rect(TX + 3, DECK - 16, TX + 8, DECK - 15, LOCO)
cv.rect(TX - 3, DECK - 4, TX, DECK - 1, LOCO)                        # the cow-catcher
cv.put(TX + 1, DECK - 8, (1.0, 0.92, 0.6))                           # the headlamp
for i in range(1, 30):
    cv.glow(TX - i, DECK - 8 + int(i * 0.08), (1.0, 0.85, 0.5), 0.35 * (1 - i / 30))
cv.rect(TX + 17, DECK - 14, TX + 20, DECK - 12, (1.0, 0.70, 0.35))   # the cab window
for car in range(6):
    cx0 = TX + 25 + car * 24
    cv.rect(cx0, DECK - 12, cx0 + 21, DECK - 1, LOCO)
    cv.rect(cx0 - 1, DECK - 13, cx0 + 22, DECK - 12, scale(LOCO, 0.8))
    for wx in range(cx0 + 2, cx0 + 20, 4):                            # lit windows, some with a passenger
        cv.rect(wx, DECK - 9, wx + 2, DECK - 6, (1.0, 0.78, 0.42))
        if rng.random() < 0.35:
            cv.put(wx + rng.randrange(2), DECK - 7, (0.30, 0.15, 0.12))
    cv.halo(cx0 + 10, DECK - 7, 6, (1.0, 0.6, 0.3), 0.08)
for k in range(60):                                                   # smoke, drifting back along the train
    px = TX + 6 + k * 2.6
    py = DECK - 18 - 7 * (1 - math.exp(-k / 12)) - 2 * math.sin(k * 0.4)
    r = 2 + k * 0.10
    cv.disc(px, py, r, mix((0.35, 0.22, 0.30), (0.95, 0.65, 0.55), min(1.0, k / 45)), 0.22 * (1 - k / 60))

# the near dunes: backlit crests, deep shadow slopes, and glass in the sand
near = [int(140 + 10 * math.sin(x * 0.028 + 2.2) + 7 * nz.fbm1(x * 0.03 + 9)) for x in range(W)]
for x in range(W):
    # ⛔ a per-column lit/unlit switch made vertical stripes; light is now a soft band under every crest,
    # a little stronger where the slope faces the sun (a smooth function of a wide slope estimate)
    slope = (near[min(x + 4, W - 1)] - near[max(x - 4, 0)]) / 8.0
    facing = max(0.0, min(1.0, 0.5 + slope * 0.9))
    for y in range(near[x], H):
        depth = (y - near[x]) / 40
        c = mix((0.58, 0.30, 0.26), (0.30, 0.14, 0.20), min(1.0, depth * 1.5))
        glow = math.exp(-((y - near[x]) / 5.0) ** 2) * (0.10 + 0.22 * facing)
        cv.put(x, y, add(c, (0.55, 0.28, 0.12), glow))
    cv.put(x, near[x], mix((0.85, 0.50, 0.38), (1.0, 0.72, 0.46), facing))     # the crest catching the sun
for _ in range(140):                                                  # glints: the sand is glass
    x = rng.randrange(W)
    y = rng.randrange(near[x] + 1, H)
    cv.glow(x, y, (1.0, 0.92, 0.75), 0.6 * rng.random() ** 1.5)


def shard(x0, base, h, lean):
    """A blade of glass standing out of the dune, lit on the side toward the sun."""
    for k in range(h):
        x = int(round(x0 + lean * k))
        w = max(1, int(5 * (1 - k / h)) + 1)
        for dx in range(w):
            if dx == w - 1:
                c, a = (0.92, 1.0, 1.0), 0.95                   # the edge facing the sun
            elif dx >= w // 2:
                c, a = (0.60, 0.85, 0.95), 0.80
            else:
                c, a = (0.22, 0.40, 0.58), 0.85
            cv.blend(x + dx, base - k, c, a)
    tip_x, tip_y = int(round(x0 + lean * (h - 1))), base - h + 1
    cv.halo(tip_x, tip_y, 2.5, (1.0, 0.95, 0.85), 0.55)
    cv.glow(tip_x, tip_y, (1.0, 1.0, 1.0), 0.9)


for x0, h, lean in ((24, 22, 0.12), (31, 13, -0.15), (276, 26, -0.10), (288, 15, 0.20), (300, 10, 0.05),
                    (150, 9, 0.18)):
    shard(x0, near[x0] + 6, h, lean)

cv.vignette(0.45)
out = cv.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "04 The Last Train Across the Glass Desert.png"))
print("wrote", out)
