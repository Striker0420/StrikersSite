"""Postcard 3 - Earthrise Over the Greenhouse. A glass dome of green on the grey Moon, and home in the sky."""
import math
import os
import random

from pixelkit import Canvas, Noise, gradient, mix, add, scale

W, H = 320, 180
cv = Canvas(W, H)
nz = Noise(33)
rng = random.Random(33)
SUN = (0.75, -0.25, 0.62)                # light from the right and a little above
sl = math.sqrt(sum(v * v for v in SUN))
SUN = tuple(v / sl for v in SUN)

# the black sky, the Milky Way, and the stars
for y in range(H):
    for x in range(W):
        band = math.exp(-((y - (30 + x * 0.32)) / 22) ** 2) * nz.fbm2(x * 0.04, y * 0.04, 4)
        cv.put(x, y, add((0.005, 0.006, 0.015), (0.20, 0.17, 0.30), 0.55 * band))
for _ in range(520):
    x, y = rng.randrange(W), rng.randrange(125)
    b = rng.random() ** 3
    cv.glow(x, y, rng.choice([(1, 1, 1), (0.8, 0.88, 1), (1, 0.9, 0.8)]), 0.2 + 0.8 * b)

# Earth, rising: oceans, land, cloud, a crescent of night, a thin blue atmosphere
EX, EY, ER = 236, 50, 24
for y in range(EY - ER - 6, EY + ER + 7):
    for x in range(EX - ER - 6, EX + ER + 7):
        u, v = (x - EX) / ER, (y - EY) / ER
        d2 = u * u + v * v
        if d2 <= 1.0:
            z = math.sqrt(1 - d2)
            lam = max(0.0, u * SUN[0] + v * SUN[1] + z * SUN[2])
            lon, lat = math.atan2(u, z) * 2.2, v * 3.0
            land = nz.fbm2(lon * 1.6 + 10, lat * 1.6 + 4, 5)
            c = (0.10, 0.28, 0.66) if land < 0.55 else mix((0.25, 0.48, 0.22), (0.62, 0.52, 0.34), (land - 0.55) * 3)
            if abs(v) > 0.82:
                c = (0.85, 0.90, 0.95)                         # ice at the poles
            cloud = nz.fbm2(lon * 2.4 + 40, lat * 3.2 + 7, 5)
            if cloud > 0.58:
                c = mix(c, (0.95, 0.96, 1.0), min(1.0, (cloud - 0.58) * 4))
            c = scale(c, 0.04 + 1.05 * lam)
            rim = (1 - z) ** 4
            c = add(c, (0.30, 0.55, 1.0), 0.6 * rim * (0.3 + lam))
            cv.put(x, y, c)
        elif d2 <= 1.09:
            k = 1 - (math.sqrt(d2) - 1) / 0.045
            lit = max(0.0, u * SUN[0] + v * SUN[1])
            cv.glow(x, y, (0.30, 0.55, 1.0), 0.45 * k * (0.2 + lit))

# the lunar ground: rolling, cratered, lit from the right
HZ = [int(118 + 6 * nz.fbm1(x * 0.02 + 5) - 3 * math.sin(x * 0.012)) for x in range(W)]
for x in range(W):
    for y in range(HZ[x], H):
        r = nz.fbm2(x * 0.09, y * 0.15, 4)
        depth = (y - HZ[x]) / (H - HZ[x] + 1)
        cv.put(x, y, scale((0.50, 0.49, 0.52), 0.42 + 0.50 * r + 0.18 * depth))
    cv.put(x, HZ[x], (0.78, 0.78, 0.80))
for _ in range(16):
    # a crater lit low from the right: its right inner wall in shadow, its left inner wall lit, a bright rim
    cx, cy = rng.randrange(0, W), rng.randrange(128, H)
    rx = rng.randrange(4, 15)
    ry = rx * 0.32
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            if 0 <= x < W and HZ[x] < y < H:
                u, v = (x - cx) / rx, (y - cy) / ry
                e = u * u + v * v
                if e <= 1.0:
                    c = scale(cv.get(x, y), 0.80)
                    if (u + 0.45) ** 2 + v * v > 1.0:            # the crescent away from the Sun
                        c = scale(c, 0.50)
                    elif (u - 0.55) ** 2 + v * v > 1.0:          # the crescent facing it
                        c = mix(c, (0.85, 0.84, 0.84), 0.35)
                    cv.put(x, y, c)
                elif e <= 1.4 and u > -0.2:
                    cv.put(x, y, mix(cv.get(x, y), (0.92, 0.91, 0.90), 0.45))

# the greenhouse: a glass dome with a garden under pink grow-lights
GX, GR = 104, 36
GY = HZ[GX] + 14
GROW = (1.0, 0.35, 0.80)
for y in range(GY - 46, GY + 26):                                # light from inside, falling on the dust
    for x in range(GX - 70, GX + 70):
        d = math.hypot((x - GX) / 1.6, y - GY)
        if 0 <= x < W and 0 <= y < H and y >= HZ[x]:
            cv.glow(x, y, (0.55, 0.20, 0.45), 0.35 * math.exp(-(d / 28) ** 2))
for y in range(GY - GR, GY + 1):                                 # the garden inside
    for x in range(GX - GR, GX + GR + 1):
        if (x - GX) ** 2 + (y - GY) ** 2 <= (GR - 1) ** 2:
            c = mix((0.10, 0.06, 0.12), (0.30, 0.10, 0.28), (GY - y) / GR)
            cv.put(x, y, c)
for row in range(4):                                             # planters with rows of plants
    ry = GY - 4 - row * 7
    half = int(math.sqrt(max(0, (GR - 3) ** 2 - (GY - ry) ** 2)))
    for x in range(GX - half + 2, GX + half - 1):
        cv.put(x, ry, (0.25, 0.16, 0.12))
        if (x + row * 3) % 4 != 0:
            leaf = mix((0.20, 0.70, 0.30), (0.55, 0.90, 0.40), nz.n2(x * 0.5, row * 3.0))
            leaf = mix(leaf, GROW, 0.18)
            cv.put(x, ry - 1, leaf)
            if nz.n2(x * 0.7 + 20, row * 5.0) > 0.4:
                cv.put(x, ry - 2, leaf)
            if nz.n2(x * 0.9 + 70, row * 7.0) > 0.78:
                cv.put(x, ry - 3, (1.0, 0.45, 0.35))            # a ripe tomato or two
for x in range(GX - 2, GX + 3):                                  # a small tree in the middle
    for y in range(GY - 30, GY - 6):
        if x == GX:
            cv.put(x, y, (0.35, 0.22, 0.14))
cv.disc(GX, GY - 31, 6, (0.30, 0.78, 0.38))
cv.disc(GX - 3, GY - 29, 4, (0.36, 0.85, 0.42))
cv.disc(GX + 4, GY - 28, 4, (0.25, 0.70, 0.34))
for k in range(-2, 3):                                           # the grow-lights, hanging from the frame
    lx = GX + k * 12
    ly = GY - int(math.sqrt(max(0, (GR - 4) ** 2 - (k * 12) ** 2))) + 3
    cv.put(lx, ly, (1.0, 0.75, 0.95))
    cv.halo(lx, ly, 4, GROW, 0.35)
for y in range(GY - GR - 1, GY + 1):                             # the glass: a lattice, a tint, a highlight
    for x in range(GX - GR - 1, GX + GR + 2):
        d = math.hypot(x - GX, y - GY)
        if d <= GR + 0.5:
            ang = math.atan2(GY - y, x - GX)
            on_frame = d > GR - 1 or abs(math.sin(ang * 6)) < 0.08 or int(d) in (int(GR * 0.55), int(GR * 0.82))
            if on_frame:
                cv.put(x, y, (0.72, 0.78, 0.86))
            else:
                cv.blend(x, y, (0.75, 0.90, 1.0), 0.10)
            if GR * 0.62 < d < GR * 0.80 and 1.9 < ang < 2.5:
                cv.blend(x, y, (1.0, 1.0, 1.0), 0.45)            # the window-light glint, upper left
cv.rect(GX - GR - 2, GY, GX + GR + 3, GY + 2, (0.45, 0.45, 0.50))     # the footing ring
cv.rect(GX + GR - 2, GY - 7, GX + GR + 6, GY + 1, (0.40, 0.41, 0.46)) # the airlock
cv.rect(GX + GR + 1, GY - 5, GX + GR + 4, GY, (1.0, 0.72, 0.4))

# the dome's long shadow, thrown to the left by the low Sun: a stretched, softening oval
SCX, SRX, SRY = GX - 34, 62, 4.5
for y in range(int(GY - SRY), int(GY + SRY) + 2):
    for x in range(int(SCX - SRX), GX - GR + 2):
        if 0 <= x < W and 0 <= y < H:
            e = ((x - SCX) / SRX) ** 2 + ((y - GY - 1) / SRY) ** 2
            if e <= 1.0:
                fade = 0.45 + 0.4 * (1 - (x - (SCX - SRX)) / (GX - GR - (SCX - SRX)))
                cv.put(x, y, scale(cv.get(x, y), min(1.0, fade + 0.15 * e)))

# an astronaut, by the airlock, looking up at home
AX = GX + GR + 14
AY = HZ[AX] + 18
SUIT, SHADE = (0.92, 0.92, 0.95), (0.55, 0.56, 0.62)
cv.rect(AX - 3, AY - 9, AX + 3, AY - 2, SUIT)                    # body
cv.rect(AX - 3, AY - 9, AX - 1, AY - 2, SHADE)                   # the side away from the Sun
cv.rect(AX - 3, AY - 2, AX - 1, AY + 2, SUIT)                    # legs
cv.rect(AX + 1, AY - 2, AX + 3, AY + 2, SUIT)
cv.rect(AX - 5, AY - 8, AX - 3, AY - 3, (0.75, 0.75, 0.78))      # backpack
cv.disc(AX, AY - 12, 3.2, SUIT)                                  # helmet
cv.rect(AX, AY - 14, AX + 3, AY - 11, (1.0, 0.78, 0.35))         # visor, catching the light
cv.put(AX + 2, AY - 14, (1.0, 0.95, 0.8))
for k in range(18):                                              # footprints back to the airlock
    fx = AX - 3 - k * 1
    fy = AY + 3 + (k % 2)
    if k % 2 == 0:
        cv.put(fx, fy, scale(cv.get(fx, fy), 0.6))

cv.vignette(0.35)
out = cv.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "03 Earthrise Over the Greenhouse.png"))
print("wrote", out)
