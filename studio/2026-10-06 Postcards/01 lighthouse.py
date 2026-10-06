"""Postcard 1 - The Lighthouse at the Edge of the Map. Dusk over a calm sea; the lamp has just been lit."""
import math
import os
import random

from pixelkit import Canvas, Noise, gradient, mix, add, scale

W, H = 320, 180
HORIZON = 112
cv = Canvas(W, H)
nz = Noise(11)
rng = random.Random(11)

SKY = [(0.00, (0.10, 0.10, 0.28)), (0.45, (0.42, 0.24, 0.48)), (0.80, (0.95, 0.52, 0.42)), (1.00, (1.0, 0.80, 0.52))]
SUN_X, SUN_Y = 92, HORIZON - 4

# sky, with long thin clouds lit from below
for y in range(HORIZON):
    base = gradient(SKY, y / HORIZON)
    for x in range(W):
        c = base
        cl = nz.fbm2(x * 0.012, y * 0.09, 4)
        band = max(0.0, cl - 0.52) * 3.2 * (0.3 + 0.7 * (y / HORIZON))
        lit = gradient([(0, (0.55, 0.32, 0.55)), (1, (1.0, 0.68, 0.55))], min(1.0, y / HORIZON + 0.2))
        c = mix(c, lit, min(0.85, band))
        cv.put(x, y, c)
# a few early stars where the sky is darkest
for _ in range(45):
    x, y = rng.randrange(W), rng.randrange(int(HORIZON * 0.38))
    cv.glow(x, y, (1.0, 0.95, 0.9), 0.25 + 0.5 * rng.random() ** 2)
# the low sun, half into the sea
cv.halo(SUN_X, SUN_Y, 18, (1.0, 0.50, 0.25), 0.60)
cv.halo(SUN_X, SUN_Y, 7, (1.0, 0.85, 0.60), 0.70)
cv.disc(SUN_X, SUN_Y, 9, (1.0, 0.97, 0.86))

# the sea: the sky mirrored, darker, broken into horizontal ripples; a road of light under the sun
for y in range(HORIZON, H):
    depth = (y - HORIZON) / (H - HORIZON)
    for x in range(W):
        my = max(0, min(HORIZON - 1, 2 * HORIZON - y - 1 + int(4 * math.sin(x * 0.13 + y * 0.7))))
        refl = cv.get(x, my)
        water = mix(scale(refl, 0.55), (0.06, 0.09, 0.20), 0.35 + 0.45 * depth)
        rip = nz.n2(x * 0.08, y * 0.9)
        if rip > 0.62:
            water = mix(water, (1.0, 0.75, 0.55), 0.35 * (1 - depth))
        road = math.exp(-((x - SUN_X) / (7 + 30 * depth)) ** 2) * (0.8 if rip > 0.45 else 0.15)
        water = add(water, (1.0, 0.72, 0.42), road * (1 - 0.6 * depth))
        cv.put(x, y, water)

# the headland and the lighthouse, on the right
cliff = [int(HORIZON - 14 + 20 * max(0.0, (x - 200) / 120) ** 0.7 * -1 + 6 * nz.fbm1(x * 0.06)) for x in range(W)]
FOOT = 176                                                       # where the slope meets the sea


def waterline(x):
    """The headland runs toward us on the right, so its foot meets nearer (lower) water there."""
    return min(H, int(HORIZON + 7 + (x - FOOT) * 0.42))


ROCK = (0.05, 0.045, 0.08)
FOAM = (0.95, 0.88, 0.85)
for x in range(FOOT, W):
    if x < 214:                                                  # the seaward face: a rough slope, not a wall
        t = (x - FOOT) / (214 - FOOT)
        top = int(HORIZON + 6 + (cliff[214] - HORIZON - 6) * t ** 0.8 + 3 * nz.n1(x * 0.4))
    else:
        top = cliff[x]
    yw = waterline(x)
    for y in range(top, yw):
        shade = 0.05 + 0.04 * nz.n2(x * 0.3, y * 0.3)
        cv.put(x, y, (shade, shade * 0.9, shade * 1.4))
    cv.put(x, top, (0.35, 0.20, 0.28))                       # the rim, warmed by the last of the sun
    if x < 214:
        cv.put(x, top + 1, (0.20, 0.12, 0.20))
    reach = max(2, (yw - top) // 3)                              # the cliff's dark reflection in the water
    for y in range(yw, min(H, yw + reach)):
        cv.blend(x, y, ROCK, 0.6 * (1 - (y - yw) / reach))
    if yw < H and nz.n1(x * 0.35) > 0.35:                        # foam where the sea meets the rock
        cv.blend(x, yw, FOAM, 0.55)
        cv.blend(x, yw + 1, FOAM, 0.2)
for i in range(7):                                               # a few rocks standing in the shallows
    fx = FOOT - 10 + rng.randrange(0, 22)
    fy = waterline(max(fx, FOOT)) - 1
    r = rng.choice((1, 1.5, 2))
    cv.disc(fx, fy, r, ROCK)
    cv.blend(fx - 1, int(fy + r + 1), FOAM, 0.4)
    cv.blend(fx + 1, int(fy + r + 1), FOAM, 0.4)
LX = 268
base_y = cliff[LX]
for y in range(base_y - 46, base_y):                            # the tower: tapering, with a red band
    half = 4 + int((y - (base_y - 46)) * 0.06)
    for x in range(LX - half, LX + half + 1):
        stripe = ((y - (base_y - 46)) // 9) % 2 == 1
        c = (0.60, 0.16, 0.18) if stripe else (0.86, 0.83, 0.80)
        if x > LX + half - 2:
            c = scale(c, 0.55)                                   # the side away from the sun
        cv.put(x, y, c)
lamp_y = base_y - 50
cv.rect(LX - 5, lamp_y - 1, LX + 6, lamp_y + 5, (0.12, 0.12, 0.16))    # the lantern room
cv.rect(LX - 3, lamp_y, LX + 4, lamp_y + 4, (1.0, 0.95, 0.72))
cv.rect(LX - 6, lamp_y - 3, LX + 7, lamp_y - 1, (0.20, 0.12, 0.14))    # the roof
cv.put(LX, lamp_y - 4, (0.20, 0.12, 0.14))
# the beam, sweeping out over the sea on the left, angled a little down toward the water
for i in range(1, 250):
    t = i / 250
    bx = LX - 6 - i * 1.0
    by = lamp_y + 2 + i * 0.11
    spread = 1.5 + t * 14
    for k in range(-int(spread) - 1, int(spread) + 2):
        a = (1 - t) ** 1.3 * 0.40 * math.exp(-(k / spread) ** 2 * 2.2)
        cv.glow(int(bx), int(by + k), (1.0, 0.93, 0.70), a)
cv.halo(LX, lamp_y + 2, 5, (1.0, 0.9, 0.6), 1.0)
# a small boat, heading home along the road of light
BX, BY = 120, HORIZON + 30
for x in range(BX - 7, BX + 8):
    cv.put(x, BY, (0.04, 0.03, 0.06))
for x in range(BX - 5, BX + 6):
    cv.put(x, BY + 1, (0.04, 0.03, 0.06))
for y in range(BY - 9, BY):
    cv.put(BX, y, (0.04, 0.03, 0.06))
for y in range(BY - 8, BY - 1):
    for x in range(BX + 1, BX + 1 + (y - (BY - 8)) // 2 + 1):
        cv.put(x, y, (0.95, 0.88, 0.80) if x < BX + 5 else (0.80, 0.72, 0.66))
cv.put(BX - 2, BY - 1, (1.0, 0.85, 0.5))                          # a lantern on board
cv.halo(BX - 2, BY - 1, 2.0, (1.0, 0.8, 0.45), 0.5)
# gulls
for gx, gy in ((150, 40), (162, 34), (171, 44)):
    for d in (-2, -1, 1, 2):
        cv.put(gx + d, gy - (1 if abs(d) == 1 else 0), (0.10, 0.07, 0.14))
    cv.put(gx, gy, (0.10, 0.07, 0.14))

cv.vignette(0.45)
out = cv.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "01 The Lighthouse at the Edge of the Map.png"))
print("wrote", out)
