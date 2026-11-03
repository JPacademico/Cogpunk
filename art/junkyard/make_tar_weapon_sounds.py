"""Source for the Metal Wrench's clash (2026-10-30, user: "a metal clash sound"). Run from the repo root:

    python -P art/junkyard/make_tar_weapon_sounds.py

Synthesised (no samples), 22050 Hz, 16-bit mono WAV (tModLoader loads .wav sounds):

    Assets/Sounds/Weapons/MetalClash.wav   0.9 s: steel struck on steel. A 6 ms burst of filtered noise for the impact,
                                           then the ring of a struck plate: eight inharmonic partials (circular-plate
                                           mode ratios over 740 Hz), the high ones dying fast, two of them a few hertz
                                           apart so the ring beats, the whole tail decaying exponentially. The game plays
                                           it higher for a parry, lower for the riposte on a boss.

A short fade at the end keeps it click-free; the peak stays at -6 dBFS so it sits under vanilla's own effects.
"""
import math
import os
import random
import struct
import wave

RATE = 22050
OUT = "Assets/Sounds/Weapons/"
F0 = 740.0
# (ratio, amplitude, decay time in s): circular-plate modes, the low ones ringing longest
PARTIALS = ((1.0, 1.0, 0.55), (1.004, 0.55, 0.5), (1.59, 0.7, 0.35), (2.14, 0.55, 0.26), (2.30, 0.45, 0.22),
            (2.65, 0.4, 0.16), (2.92, 0.3, 0.12), (3.16, 0.25, 0.09))


def write(name, samples, peak=0.5):
    top = max(1e-9, max(abs(s) for s in samples))
    path = os.path.join(OUT, name)
    os.makedirs(OUT, exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s / top * peak)) * 32767)) for s in samples))
    print("wrote", path, "(%.2f s)" % (len(samples) / RATE))


def clash(length=0.9):
    rng = random.Random(7)
    n = int(RATE * length)
    out = [0.0] * n
    phases = [rng.uniform(0.0, math.tau) for _ in PARTIALS]
    for i in range(n):
        t = i / RATE
        s = 0.0
        for (ratio, amp, decay), ph in zip(PARTIALS, phases):
            s += amp * math.exp(-t / decay) * math.sin(math.tau * F0 * ratio * t + ph)
        out[i] = s
    # the impact: noise through a one-pole high-pass, 6 ms with a fast decay
    prev, hp = 0.0, 0.0
    for i in range(int(RATE * 0.006)):
        x = rng.uniform(-1.0, 1.0)
        hp = 0.82 * (hp + x - prev)
        prev = x
        out[i] += 1.6 * hp * math.exp(-i / (RATE * 0.0025))
    # a soft attack (no click) and a fade at the end
    for i in range(int(RATE * 0.0015)):
        out[i] *= i / (RATE * 0.0015)
    fade = int(RATE * 0.03)
    for i in range(fade):
        out[-1 - i] *= i / fade
    return out


if __name__ == "__main__":
    write("MetalClash.wav", clash())
