"""Compose the soundtrack on the video's beat grid (110 BPM) and mix quiet Kenney SFX on visual events.
Usage: python3 -I audio.py <sfx-dir> <out.wav>
"""
import subprocess, sys, wave
import numpy as np

SR = 48000
B = 60 / 110; BAR = 4 * B
at = lambda b: b * BAR
DUR = at(28)
sfx_dir, out = sys.argv[1], sys.argv[2]
t = np.arange(int(SR * DUR)) / SR
mix = np.zeros_like(t)

def env(start, length, a=0.5, r=0.9):
    e = np.zeros_like(t); i0, i1 = int(start * SR), min(int((start + length + r) * SR), len(t))
    tt = t[i0:i1] - start
    e[i0:i1] = np.clip(tt / a, 0, 1) * np.where(tt > length, np.clip(1 - (tt - length) / r, 0, 1), 1)
    return e

def tone(f, start, length, amp, a=0.6, r=1.0):
    ph = 2 * np.pi * f * t
    return amp * env(start, length, a, r) * (np.sin(ph) + 0.25 * np.sin(2 * ph + 0.3) + 0.12 * np.sin(3.01 * ph))

hz = lambda n: 440 * 2 ** ((n - 69) / 12)
CHORDS = {"Am": [57, 60, 64], "F": [53, 57, 60], "C": [48, 55, 60, 64], "G": [55, 59, 62]}
prog = ["Am", "F", "C", "G"]
for bar in range(28):
    s = at(bar)
    if bar == 10:                                    # the turn: a single held high note, near silence
        mix += tone(hz(76), s + 0.1, BAR - 0.4, 0.025, a=0.8, r=0.6); continue
    if bar >= 25:                                       # resolve on C, held to the end
        if bar == 25:
            for n in CHORDS["C"] + [72]: mix += tone(hz(n), s, DUR - s - 1.6, 0.045, a=0.9, r=1.5)
        continue
    name = prog[bar % 4]
    for n in CHORDS[name]: mix += tone(hz(n), s, BAR - 0.2, 0.04, a=0.5, r=0.6)
    if not (22 <= bar < 25):                            # soft sub pulse on each downbeat (thins near the end)
        root = hz(CHORDS[name][0] - 12); i0 = int(s * SR); n = int(0.6 * SR)
        mix[i0:i0 + n] += 0.11 * np.sin(2 * np.pi * root * t[:n]) * np.exp(-t[:n] * 6)
    if bar >= 11:                                        # gentle off-beat shimmer after the turn
        for k in (1, 3):
            mix += tone(hz(CHORDS[name][-1] + 12), s + k * B, 0.15, 0.012, a=0.02, r=0.35)

# one-pole low-pass to keep the pad soft
y = np.empty_like(mix); acc = 0.0; alpha = 0.18
for i, v in enumerate(mix): acc += alpha * (v - acc); y[i] = acc
mix = y

def sfx(name, when, gain):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f"{sfx_dir}/{name}", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32) * gain; i0 = int(when * SR); i1 = min(i0 + len(a), len(mix))
    mix[i0:i1] += a[: i1 - i0]

SOFT, CLICK, BONG = "impact/impactSoft_medium_001.ogg", "interface/click_003.ogg", "interface/bong_001.ogg"
sfx(SOFT, 0.0, 0.35)
for i in range(1, 5): sfx(CLICK, at(2) + (i - 1) * 2 * B + B, 0.25)          # rings 152..45
sfx(BONG, at(2) + 4 * 2 * B + B, 0.3)                                         # ring 36 turns blue
for i in range(4): sfx(CLICK, at(7) + i * 1.5 * B, 0.25)                      # care badges
sfx("impact/impactSoft_medium_003.ogg", at(11) + 0.1, 0.3)                    # cohort opens
for i in range(5): sfx(CLICK, at(13) + B + i * B * 0.75, 0.22)                # too-short counts land
sfx(BONG, at(13) + B + 4 * B * 0.75 + 0.3, 0.28)                              # 258
sfx("impact/impactSoft_medium_002.ogg", at(16) + 0.2, 0.3)                    # map rises
sfx(CLICK, at(17) + 0.3, 0.22); sfx(CLICK, at(17) + 1.6, 0.22)                # Nyarugenge / Gicumbi callouts
for i in range(5): sfx(CLICK, at(18) + i * B * 0.6, 0.18)                     # top-5 badges
for i in range(6): sfx(CLICK, at(19.5) + 0.2 + i * B * 0.6, 0.2)              # age columns
sfx(BONG, at(19.5) + 2.2, 0.24)                                               # x2 arrow
sfx(BONG, at(23.6) + B * 0.7, 0.3)                                            # 2029 goal
for i in range(7): sfx(CLICK, at(25) + 0.1 + i * B * 0.55, 0.2)               # summary cards pile up
sfx("impact/impactSoft_medium_000.ogg", at(25) + 2.4, 0.3)                    # title

mix *= np.clip((DUR - t) / 1.5, 0, 1)                                         # fade out
mix = mix / max(1e-9, np.abs(mix).max()) * 0.6
assert len(mix) == int(SR * DUR)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print(f"{out}: {DUR}s @ {SR} Hz")
