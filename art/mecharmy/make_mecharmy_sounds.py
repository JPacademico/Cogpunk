"""Source for the Mech Army's sound effects, 2026-10-27. Run from the repo root:

    python -P art/mecharmy/make_mecharmy_sounds.py

Synthesised (no samples), 22050 Hz, 16-bit mono WAV (tModLoader loads .wav sounds):

    Assets/Sounds/MechArmy/AlarmSiren.wav   0.96 s, the Annoy-o-tron's alarm: a two-tone European "hi-lo" emergency siren
                                            (960 / 770 Hz) in a buzzy band-limited square wave with a fast warble, the
                                            kind of noise that is hard to ignore. The NPC plays it once a second.
    Assets/Sounds/MechArmy/BoombotBeep.wav  0.07 s, the Boombot's proximity beep: a 1.8 kHz square chirp with a fast
                                            decay. The NPC beeps faster as it closes in.

Short fades at every edge keep them click-free; peaks stay at -6 dBFS so they sit under vanilla's own effects.
"""
import math
import os
import struct
import wave

RATE = 22050
OUT = "Assets/Sounds/MechArmy/"


def square(phase, harmonics):
    """A band-limited square wave (odd harmonics only, below Nyquist): buzzy but not aliased."""
    return sum(math.sin(phase * k) / k for k in range(1, harmonics * 2, 2)) * (4.0 / math.pi)


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


def fade(samples, ms=6):
    n = int(RATE * ms / 1000)
    for i in range(min(n, len(samples) // 2)):
        k = i / n
        samples[i] *= k
        samples[-1 - i] *= k
    return samples


def siren():
    out = []
    phase = 0.0
    seg = int(RATE * 0.48)
    for tone in (960.0, 770.0):
        part = []
        for i in range(seg):
            t = i / RATE
            f = tone * (1.0 + 0.012 * math.sin(2 * math.pi * 11.0 * t))     # the warble
            phase += 2 * math.pi * f / RATE
            harmonics = max(1, int((RATE / 2) / (2 * f)))
            part.append(square(phase, min(harmonics, 6)) * (0.85 + 0.15 * math.sin(2 * math.pi * 22.0 * t)))
        out += fade(part, 4)
    return out


def beep():
    out = []
    n = int(RATE * 0.07)
    phase = 0.0
    for i in range(n):
        t = i / n
        phase += 2 * math.pi * 1800.0 / RATE
        out.append(square(phase, 3) * math.exp(-3.0 * t))
    return fade(out, 3)


if __name__ == "__main__":
    write("AlarmSiren.wav", siren(), peak=0.5)
    write("BoombotBeep.wav", beep(), peak=0.45)
