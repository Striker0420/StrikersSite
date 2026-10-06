"""Atuscurt Nocturne - a small piece of chiptune, composed and synthesized in plain Python (no libraries).
Writes "Atuscurt Nocturne.wav" and "Atuscurt Nocturne - score.png" (the piece drawn as a night sky) next to itself."""
import math
import os
import random
import struct
import wave
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 22050
BPM = 76
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = random.Random(64)

# ---- the score ------------------------------------------------------------------------------------------------
CHORDS = {                       # bass root, four arpeggio tones (MIDI)
    "Am": (45, (57, 60, 64, 69)),
    "F": (41, (53, 57, 60, 65)),
    "C": (48, (55, 60, 64, 67)),
    "G": (43, (55, 59, 62, 67)),
    "Dm": (50, (53, 57, 62, 65)),
    "E": (40, (52, 56, 59, 64)),
}
PROGRESSION = (["Am", "F", "C", "G"]                                   # intro
               + ["Am", "F", "C", "G", "Am", "F", "Dm", "E"]           # A
               + ["F", "C", "G", "Am", "F", "C", "Dm", "E"]            # B
               + ["Am", "F", "Am", "Am"])                               # outro
MELODY = {                       # bar index -> [(midi or None for a rest, beats)]
    4: [(69, 1.5), (72, 0.5), (76, 2)],
    5: [(77, 1), (76, 0.5), (74, 0.5), (72, 2)],
    6: [(76, 1.5), (79, 0.5), (84, 1), (83, 1)],
    7: [(74, 1.5), (71, 0.5), (67, 2)],
    8: [(69, 1.5), (72, 0.5), (76, 1), (81, 1)],
    9: [(79, 1), (77, 0.5), (76, 0.5), (72, 2)],
    10: [(74, 1), (77, 1), (76, 1), (74, 1)],
    11: [(76, 1.5), (68, 0.5), (71, 2)],
    12: [(81, 2), (79, 1), (77, 1)],
    13: [(76, 2), (72, 1), (76, 1)],
    14: [(74, 1.5), (76, 0.5), (74, 1), (71, 1)],
    15: [(72, 2), (69, 2)],
    16: [(77, 1), (81, 1), (84, 2)],
    17: [(83, 1), (79, 1), (76, 2)],
    18: [(77, 1), (76, 1), (74, 1), (72, 1)],
    19: [(71, 2), (68, 1), (64, 1)],
    20: [(69, 4)],
    21: [(None, 4)],
    22: [(76, 4)],
}
for bar, notes in MELODY.items():
    assert abs(sum(b for _, b in notes) - 4.0) < 1e-9, "bar %d does not add up to four beats" % bar
ARP_ORDER = [0, 1, 2, 3, 2, 1, 0, 1]
TWINKLE_NOTES = [91, 93, 96, 98, 100]          # G6 A6 C7 D7 E7: the A minor pentatonic, up in the stars

TOTAL = len(PROGRESSION) * BAR + 4.0
N = int(TOTAL * SR)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def triangle(ph):
    return 4.0 * abs(ph - math.floor(ph + 0.5)) - 1.0


def pulse(ph, duty):
    return 1.0 if (ph - math.floor(ph)) < duty else -1.0


def lowpass(buf, a):
    y = 0.0
    for i, x in enumerate(buf):
        y += a * (x - y)
        buf[i] = y


bass, arp, lead, pad, sparkle = ([0.0] * N for _ in range(5))
events = []                                     # (start s, midi, length s, voice) - for the score picture


def note(buf, start, length, freq, shape, amp, attack, release, decay=None, vibrato=0.0, tail=0.0):
    i0, i1 = int(start * SR), min(N, int((start + length + tail) * SR))
    ph = 0.0
    for i in range(i0, i1):
        t = (i - i0) / SR
        f = freq * (1.0 + vibrato * math.sin(2 * math.pi * 5.2 * t) * min(1.0, max(0.0, (t - 0.15) / 0.3)))
        ph += f / SR
        env = min(1.0, t / attack) if attack > 0 else 1.0
        if decay:
            env *= math.exp(-t * decay)
        if t > length:
            env *= max(0.0, 1.0 - (t - length) / release)
        buf[i] += amp * env * shape(ph)


for b, name in enumerate(PROGRESSION):
    t0 = b * BAR
    root, tones = CHORDS[name]
    fade = 1.0 if b < len(PROGRESSION) - 1 else 0.6
    for half in (0, 2):                                            # bass: two half notes a bar
        note(bass, t0 + half * BEAT, 2 * BEAT * 0.92, hz(root), triangle, 0.22 * fade, 0.01, 0.06, decay=0.35)
        events.append((t0 + half * BEAT, root, 2 * BEAT, "bass"))
    for k, idx in enumerate(ARP_ORDER):                            # arpeggio: eighth notes, plucked
        m = tones[idx]
        note(arp, t0 + k * BEAT / 2, 0.55, hz(m), lambda p: pulse(p, 0.25), 0.075 * fade, 0.004, 0.08, decay=5.5)
        events.append((t0 + k * BEAT / 2, m, BEAT / 2, "arp"))
    for m in (root + 12, root + 19):                               # pad: a soft root and fifth under each bar
        note(pad, t0, BAR, hz(m), lambda p: math.sin(2 * math.pi * p), 0.035 * fade, 0.45, 0.6)
    if b in MELODY:                                                # the melody
        at = t0
        for m, beats in MELODY[b]:
            if m is not None:
                note(lead, at, beats * BEAT * 0.94, hz(m), lambda p: pulse(p, 0.5), 0.11, 0.025, 0.12,
                     vibrato=0.004)
                events.append((at, m, beats * BEAT, "lead"))
            at += beats * BEAT
    if 2 <= b < len(PROGRESSION) - 1:                              # a star or two chiming on an off-beat
        for _ in range(rng.choice((0, 1, 1, 2))):
            at = t0 + (rng.randrange(8) + 0.5) * BEAT / 2
            m = rng.choice(TWINKLE_NOTES)
            note(sparkle, at, 0.02, hz(m), lambda p: math.sin(2 * math.pi * p), 0.045, 0.002, 0.5, decay=7.0,
                 tail=0.6)
            events.append((at, m, 0.3, "star"))

lowpass(arp, 0.28)
lowpass(lead, 0.20)
mix = [bass[i] + arp[i] + lead[i] + pad[i] + sparkle[i] for i in range(N)]

# echo: half a beat, fed back softly
d = int(BEAT / 2 * SR)
for i in range(d, N):
    mix[i] += 0.27 * mix[i - d]

# fades, soft clip, normalise to -1 dBFS
fi, fo = int(1.5 * SR), int(4.5 * SR)
for i in range(N):
    g = min(1.0, i / fi) * min(1.0, (N - i) / fo)
    mix[i] = math.tanh(mix[i] * g * 1.1)
peak = max(abs(v) for v in mix)
k = (10 ** (-1 / 20)) / peak
mix = [v * k for v in mix]

wav = os.path.join(HERE, "Atuscurt Nocturne.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in mix))

# a few honest numbers, since the composer cannot listen
rms = [math.sqrt(sum(v * v for v in mix[j:j + SR * 10]) / max(1, len(mix[j:j + SR * 10]))) for j in range(0, N, SR * 10)]
print("%.1f s, peak %.3f, RMS per 10 s: %s" % (N / SR, max(abs(v) for v in mix), " ".join("%.3f" % r for r in rms)))

# ---- the score, drawn as a night sky: time runs left to right, pitch bottom to top ------------------------------
W, H = 960, 300
img = [[(0.02 + 0.05 * y / H, 0.02 + 0.03 * y / H, 0.09 + 0.12 * y / H) for _ in range(W)] for y in range(H)]
COL = {"bass": (0.30, 0.22, 0.55), "arp": (0.25, 0.75, 0.70), "lead": (0.95, 0.97, 1.0), "star": (1.0, 0.85, 0.55)}
lo, hi = 38, 102
for start, m, length, voice in events:
    x0, x1 = int(start / TOTAL * W), max(int((start + length) / TOTAL * W), int(start / TOTAL * W) + 1)
    y = int(H - 10 - (m - lo) / (hi - lo) * (H - 20))
    th = 3 if voice == "lead" else 1
    for x in range(x0, min(x1, W)):
        for yy in range(y - th // 2, y + th // 2 + 1):
            if 0 <= yy < H:
                img[yy][x] = COL[voice]
    if voice == "star":
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
            if 0 <= x0 + dx < W and 0 <= y + dy < H:
                img[y + dy][x0 + dx] = COL["star"]
rows = b"".join(b"\x00" + bytes(int(max(0, min(1, c)) * 255) for px in row for c in px) for row in img)


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))
with open(os.path.join(HERE, "Atuscurt Nocturne - score.png"), "wb") as fh:
    fh.write(png)
print("wrote the WAV and the score")
