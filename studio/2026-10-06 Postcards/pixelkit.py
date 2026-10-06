"""pixelkit - the few things every postcard needs: a canvas of float colours, noise, and a PNG writer.
Plain Python 3, no libraries. Colours are (r, g, b) floats in 0..1."""
import math
import random
import struct
import zlib


def mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def add(c, d, k=1.0):
    return (c[0] + d[0] * k, c[1] + d[1] * k, c[2] + d[2] * k)


def scale(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


def gradient(stops, t):
    """stops: [(t, colour), ...] ascending in t."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0.0)
    return stops[-1][1]


class Noise:
    """Seeded value noise, 1-D and 2-D, with fractal sums."""

    def __init__(self, seed):
        r = random.Random(seed)
        self.p = [r.random() for _ in range(4096)]

    def _h(self, i, j=0):
        return self.p[(i * 1619 + j * 31337 + 1013) % 4096]

    def n1(self, x):
        i = math.floor(x)
        f = x - i
        f = f * f * (3 - 2 * f)
        return self._h(i) + (self._h(i + 1) - self._h(i)) * f

    def n2(self, x, y):
        i, j = math.floor(x), math.floor(y)
        fx, fy = x - i, y - j
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a, b = self._h(i, j), self._h(i + 1, j)
        c, d = self._h(i, j + 1), self._h(i + 1, j + 1)
        return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy

    def fbm1(self, x, octaves=4):
        s = amp = norm = 0.0
        amp, fr = 1.0, 1.0
        for _ in range(octaves):
            s += amp * self.n1(x * fr)
            norm += amp
            amp *= 0.5
            fr *= 2.03
        return s / norm

    def fbm2(self, x, y, octaves=4):
        s = norm = 0.0
        amp, fr = 1.0, 1.0
        for _ in range(octaves):
            s += amp * self.n2(x * fr, y * fr)
            norm += amp
            amp *= 0.5
            fr *= 2.03
        return s / norm


class Canvas:
    def __init__(self, w=320, h=180, fill=(0.0, 0.0, 0.0)):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def get(self, x, y):
        return self.px[y][x]

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def blend(self, x, y, c, a):
        if 0 <= x < self.w and 0 <= y < self.h and a > 0:
            self.px[y][x] = mix(self.px[y][x], c, min(1.0, a))

    def glow(self, x, y, c, k):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = add(self.px[y][x], c, k)

    def disc(self, cx, cy, r, c, a=1.0):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    self.blend(x, y, c, a)

    def halo(self, cx, cy, radius, c, k):
        """An additive soft glow."""
        for y in range(max(0, int(cy - 3 * radius)), min(self.h, int(cy + 3 * radius) + 1)):
            for x in range(max(0, int(cx - 3 * radius)), min(self.w, int(cx + 3 * radius) + 1)):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                self.glow(x, y, c, k * math.exp(-d2 / (2 * radius * radius)))

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[y][x] = c

    def line(self, x0, y0, x1, y1, c, a=1.0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.blend(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), c, a)

    def vignette(self, strength=0.5):
        for y in range(self.h):
            for x in range(self.w):
                u, v = (x / self.w - 0.5) * 1.6, (y / self.h - 0.5) * 1.6
                self.px[y][x] = scale(self.px[y][x], 1.0 - strength * (u * u + v * v))

    def save(self, path, pixel=4, gamma=1.1):
        def b8(v):
            v = 0.0 if v < 0 else 1.0 if v > 1 else v
            return int(round((v ** (1 / gamma)) * 255))
        rows = []
        for y in range(self.h):
            line = bytearray()
            for x in range(self.w):
                r, g, b = self.px[y][x]
                line += bytes((b8(r), b8(g), b8(b))) * pixel
            row = b"\x00" + bytes(line)
            rows.extend([row] * pixel)

        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w * pixel, self.h * pixel, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))
        with open(path, "wb") as fh:
            fh.write(png)
        return path
