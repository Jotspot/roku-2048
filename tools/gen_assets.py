#!/usr/bin/env python3
"""Generate every image and sound used by the channel. Standard library only.

    python3 tools/gen_assets.py

Images are rendered at the exact pixel sizes each UI resolution uses (HD 720p /
FHD 1080p) so nothing is resampled on screen. Sounds are 44.1 kHz, built from
clean sines and filtered noise with smooth envelopes (no saturation).
"""
import math
import os
import random
import struct
import wave
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
SND = os.path.join(ROOT, "sounds")

# Must match layout() in components/GameScene.brs: round(200 * H / 1080)
TILE_PX = {"fhd": 200, "hd": 133}
PANEL_RADIUS = {"fhd": 12, "hd": 8}


# ---------------------------------------------------------------- PNG ----

def write_png(path, w, h, px, alpha=True):
    """px: flat list of (r, g, b, a) tuples, row-major. alpha=False writes opaque RGB."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(px[y * w + x] if alpha else px[y * w + x][:3])

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6 if alpha else 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


def rr_dist(x, y, w, h, r):
    """Signed distance from (x, y) to a rounded rect [0,w]x[0,h] with radius r."""
    qx = abs(x - w / 2) - (w / 2 - r)
    qy = abs(y - h / 2) - (h / 2 - r)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - r


def coverage(x, y, w, h, r, ss=4):
    hit = 0
    for sy in range(ss):
        for sx in range(ss):
            if rr_dist(x + (sx + .5) / ss, y + (sy + .5) / ss, w, h, r) <= 0:
                hit += 1
    return hit / (ss * ss)


def make_tile(path, size, r, band, inset=False):
    """Exact-size white rounded square, tinted at runtime with blendColor.
    raised: a darker crescent along the bottom edge (key-cap depth).
    inset:  a soft shadow along the top edge (sunken cell)."""
    px = []
    for y in range(size):
        for x in range(size):
            a = coverage(x, y, size, size, r)
            if inset:
                face = coverage(x, y - band, size, size, r, 2)
                shade = 0.9 + 0.1 * face
            else:
                face = coverage(x, y + band, size, size, r, 2)
                shade = 0.8 + 0.2 * face
            g = int(round(255 * shade))
            px.append((g, g, g, int(round(a * 255))))
    write_png(path, size, size, px)


def make_ring(path, size, r, w):
    """Rounded-square outline used for the merge burst."""
    px = []
    for y in range(size):
        for x in range(size):
            outer = coverage(x, y, size, size, r)
            inner = coverage(x - w, y - w, size - 2 * w, size - 2 * w, max(1, r - w))
            px.append((255, 255, 255, int(round(max(0.0, outer - inner) * 255))))
    write_png(path, size, size, px)


def make_bg(path, w=64, h=36):
    """Tiny warm radial gradient, stretched full-screen at runtime."""
    c0, c1 = (0xFC, 0xFA, 0xF4), (0xEF, 0xE9, 0xDC)
    px = []
    for y in range(h):
        for x in range(w):
            dx, dy = (x + .5) / w * 2 - 1, (y + .5) / h * 2 - 1.1
            d = min(1.0, math.hypot(dx, dy * 0.9) / 1.35)
            k = d ** 1.8
            px.append(tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3)) + (255,))
    write_png(path, w, h, px)


def nine_patch(path, inner, alpha_at, stretch):
    """.9.png: 1px border, top/left black marks over the stretch range."""
    w = inner + 2
    px = [(0, 0, 0, 0)] * (w * w)
    for y in range(inner):
        for x in range(inner):
            px[(y + 1) * w + (x + 1)] = (255, 255, 255, int(round(alpha_at(x, y) * 255)))
    lo, hi = stretch
    for i in range(lo, hi):
        px[i + 1] = (0, 0, 0, 255)
        px[(i + 1) * w] = (0, 0, 0, 255)
    write_png(path, w, w, px)


def make_rr(path, r):
    inner = 2 * r + 4
    nine_patch(path, inner, lambda x, y: coverage(x, y, inner, inner, r), (r, inner - r))


def make_glow():
    # Soft shadow: solid inside a 12px-radius rounded rect inset by F, feathering out over F px.
    F, r = 20, 12
    inner = 2 * (F + r) + 2

    def a(x, y):
        d = rr_dist(x + .5 - F, y + .5 - F, inner - 2 * F, inner - 2 * F, r)
        if d <= 0:
            return 1.0
        t = max(0.0, 1 - d / F)
        return t * t * (3 - 2 * t) * 0.9

    nine_patch(os.path.join(IMG, "glow.9.png"), inner, a, (F + r, inner - F - r))


# --- vector digits for the channel icon ---

def _arc(cx, cy, rx, ry, a0, a1, n=28):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GLYPHS = {
    "0": [_arc(.5, .5, .40, .44, 0, 360, 40)],
    "2": [_arc(.5, .30, .38, .24, 175, 395) + [(.10, .94), (.92, .94)]],
    "4": [[(.70, .94), (.70, .06), (.06, .66), (.96, .66)]],
    "8": [_arc(.5, .27, .31, .21, 0, 360, 32), _arc(.5, .71, .38, .23, 0, 360, 32)],
}


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def make_icon(path, w, h, text_h):
    bg = (0xED, 0xC2, 0x2E)
    fg = (0xF9, 0xF6, 0xF2)
    cov = [0.0] * (w * h)
    gw = text_h * 0.60
    adv = gw * 1.18
    thick = text_h * 0.15
    x0 = (w - (adv * 3 + gw)) / 2
    y0 = (h - text_h) / 2
    for gi, ch in enumerate("2048"):
        ox = x0 + gi * adv
        segs = []
        for poly in GLYPHS[ch]:
            pts = [(ox + x * gw, y0 + y * text_h) for x, y in poly]
            segs += list(zip(pts, pts[1:]))
        pad = thick
        for y in range(int(y0 - pad), int(y0 + text_h + pad) + 1):
            for x in range(int(ox - pad), int(ox + gw + pad) + 1):
                if not (0 <= x < w and 0 <= y < h):
                    continue
                d = min(seg_dist(x + .5, y + .5, a[0], a[1], b[0], b[1]) for a, b in segs)
                i = y * w + x
                cov[i] = max(cov[i], max(0.0, min(1.0, thick / 2 - d + 0.5)))
    px = [tuple(int(round(bg[k] + (fg[k] - bg[k]) * c)) for k in range(3)) + (255,) for c in cov]
    write_png(path, w, h, px)


# --- remote-button icons: white on transparent, tinted at runtime ---

ICON_PX = {"fhd": 44, "hd": 29}   # must match layout().icon in GameScene.brs


def _capsule(ax, ay, bx, by, r):
    return lambda x, y: seg_dist(x, y, ax, ay, bx, by) <= r


def _poly(pts):
    def inside(x, y):
        c = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c
    return inside


def _circle(cx, cy, r):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _replay():
    cx, cy, R, w = 0.5, 0.54, 0.31, 0.06
    a0, a1 = math.radians(165), math.radians(-78)   # counter-clockwise on screen
    n = 40
    pts = [(cx + R * math.cos(a0 + (a1 - a0) * i / n), cy + R * math.sin(a0 + (a1 - a0) * i / n))
           for i in range(n + 1)]
    shapes = [_capsule(*pts[i], *pts[i + 1], w) for i in range(n)]
    ex, ey = pts[-1]
    dx, dy = math.sin(a1), -math.cos(a1)            # tangent, direction of travel
    nx, ny = -dy, dx
    shapes.append(_poly([(ex + dx * 0.2, ey + dy * 0.2),
                         (ex + nx * 0.16 - dx * 0.02, ey + ny * 0.16 - dy * 0.02),
                         (ex - nx * 0.16 - dx * 0.02, ey - ny * 0.16 - dy * 0.02)]))
    return shapes


def _dpad():
    """The purple D-pad on a Roku remote: a rounded plus/cross with a round
    hole in the middle where the OK button sits. Shapes tagged "cut" are subtracted."""
    arm, r = .36, .1

    def rrect(x0, y0, x1, y1):
        return lambda x, y: rr_dist(x - x0, y - y0, x1 - x0, y1 - y0, r) <= 0
    lo, hi = .5 - arm / 2, .5 + arm / 2
    return [
        rrect(.03, lo, .97, hi),
        rrect(lo, .03, hi, .97),
        ("cut", _circle(.5, .5, .165)),
    ]


ICONS = {
    "dpad": _dpad(),
    "replay": _replay(),
    "options": [_capsule(.5 + .36 * math.cos(a), .5 + .36 * math.sin(a),
                         .5 - .36 * math.cos(a), .5 - .36 * math.sin(a), .075)
                for a in (math.radians(90), math.radians(30), math.radians(150))],
    "playpause": [
        _poly([(.06, .2), (.06, .8), (.46, .5)]),
        _poly([(.58, .2), (.7, .2), (.7, .8), (.58, .8)]),
        _poly([(.82, .2), (.94, .2), (.94, .8), (.82, .8)]),
    ],
    "back": [
        _capsule(.2, .5, .84, .5, .065),
        _capsule(.2, .5, .44, .26, .065),
        _capsule(.2, .5, .44, .74, .065),
    ],
}


def make_icon_glyph(path, shapes, size, ss=5):
    adds = [f for f in shapes if not isinstance(f, tuple)]
    cuts = [f[1] for f in shapes if isinstance(f, tuple)]
    px = []
    for y in range(size):
        for x in range(size):
            hit = 0
            for sy in range(ss):
                for sx in range(ss):
                    u, v = (x + (sx + .5) / ss) / size, (y + (sy + .5) / ss) / size
                    if any(f(u, v) for f in adds) and not any(f(u, v) for f in cuts):
                        hit += 1
            px.append((255, 255, 255, int(round(255 * hit / (ss * ss)))))
    write_png(path, size, size, px)



# --- channel poster + splash artwork: the four-tile "2048" logo ---

LOGO_COLORS = [(0xF2, 0xB1, 0x79), (0xF5, 0x95, 0x63), (0xF6, 0x7C, 0x5F), (0xED, 0xC2, 0x2E)]
BG = (0xFA, 0xF8, 0xEF)


def draw_logo(w, h, tile, gap, bg=BG, grid=False):
    cov = [list(bg) for _ in range(w * h)]
    r = max(2, round(tile * 0.09))
    band = max(2, round(tile * 0.05))
    cols, rows = (2, 2) if grid else (4, 1)
    x0 = (w - (tile * cols + gap * (cols - 1))) // 2
    y_top = (h - (tile * rows + gap * (rows - 1))) // 2
    feather = tile * 0.18
    sh_off = tile * 0.06

    def blend(i, col, a):
        c = cov[i]
        for k in range(3):
            c[k] = c[k] * (1 - a) + col[k] * a

    for n, ch in enumerate("2048"):
        tx = x0 + (n % cols) * (tile + gap)
        y0 = y_top + (n // cols) * (tile + gap)
        # soft shadow
        for y in range(int(y0 - feather), int(y0 + tile + feather + sh_off) + 1):
            for x in range(int(tx - feather), int(tx + tile + feather) + 1):
                if 0 <= x < w and 0 <= y < h:
                    d = rr_dist(x + .5 - tx, y + .5 - y0 - sh_off, tile, tile, r)
                    if d < feather:
                        s = 1 - max(0.0, d) / feather
                        blend(y * w + x, (0x77, 0x6E, 0x65), 0.16 * s * s)
        # bevelled tile
        col = LOGO_COLORS[n]
        for y in range(y0, y0 + tile):
            for x in range(tx, tx + tile):
                if not (0 <= x < w and 0 <= y < h):
                    continue
                a = coverage(x - tx, y - y0, tile, tile, r, 3)
                if a <= 0:
                    continue
                face = coverage(x - tx, y - y0 + band, tile, tile, r, 2)
                sh = 0.8 + 0.2 * face
                blend(y * w + x, tuple(c * sh for c in col), a)
        # digit
        gh = tile * 0.52
        gw = gh * 0.6
        th = gh * 0.17
        gx = tx + (tile - gw) / 2
        gy = y0 + (tile - band - gh) / 2
        segs = []
        for poly in GLYPHS[ch]:
            pts = [(gx + px_ * gw, gy + py * gh) for px_, py in poly]
            segs += list(zip(pts, pts[1:]))
        for y in range(int(gy - th), int(gy + gh + th) + 1):
            for x in range(int(gx - th), int(gx + gw + th) + 1):
                if 0 <= x < w and 0 <= y < h:
                    d = min(seg_dist(x + .5, y + .5, a_[0], a_[1], b_[0], b_[1]) for a_, b_ in segs)
                    a = max(0.0, min(1.0, th / 2 - d + 0.5))
                    if a > 0:
                        blend(y * w + x, (0xF9, 0xF6, 0xF2), a)
    return [tuple(int(round(v)) for v in c) + (255,) for c in cov]


def legal(v):
    """Map full-range 0-255 into broadcast-safe 16-235 (cert 6.4 artwork)."""
    return int(round(16 + v * 219 / 255))


def make_art(path, w, h, tile, gap, grid=False):
    px = draw_logo(w, h, tile, gap, grid=grid)
    write_png(path, w, h, [(legal(r), legal(g), legal(b), a) for r, g, b, a in px], alpha=False)


# ---------------------------------------------------------------- WAV ----

SR = 44100


def write_wav(name, s, peak):
    """Normalize to `peak`, 2 ms fade-in / 12 ms fade-out, 16-bit mono."""
    m = max(1e-9, max(abs(v) for v in s))
    g = peak / m
    n = len(s)
    fi, fo = int(SR * 0.002), int(SR * 0.012)
    out = bytearray()
    for i, v in enumerate(s):
        if i < fi:
            v *= 0.5 - 0.5 * math.cos(math.pi * i / fi)
        if i > n - fo:
            v *= 0.5 - 0.5 * math.cos(math.pi * (n - i) / fo)
        out += struct.pack("<h", int(round(max(-1.0, min(1.0, v * g)) * 32767)))
    with wave.open(os.path.join(SND, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(bytes(out))


def smooth_attack(t, a):
    return 1.0 if t >= a else 0.5 - 0.5 * math.cos(math.pi * t / a)


def voice(freq_fn, dur, partials, attack=0.004):
    """Sum of sine partials: [(ratio, amp, decay_tau)], sharing one phase clock."""
    out, ph = [], 0.0
    for i in range(int(SR * dur)):
        t = i / SR
        ph += 2 * math.pi * freq_fn(t) / SR
        v = 0.0
        for ratio, amp, tau in partials:
            v += amp * math.exp(-t / tau) * math.sin(ratio * ph)
        out.append(v * smooth_attack(t, attack))
    return out


class Biquad:
    def __init__(self):
        self.x1 = self.x2 = self.y1 = self.y2 = 0.0

    def run(self, x, kind, fc, q=0.707):
        w0 = 2 * math.pi * fc / SR
        al = math.sin(w0) / (2 * q)
        c = math.cos(w0)
        if kind == "lp":
            b0, b1, b2 = (1 - c) / 2, 1 - c, (1 - c) / 2
        else:
            b0, b1, b2 = (1 + c) / 2, -(1 + c), (1 + c) / 2
        a0, a1, a2 = 1 + al, -2 * c, 1 - al
        y = (b0 * x + b1 * self.x1 + b2 * self.x2 - a1 * self.y1 - a2 * self.y2) / a0
        self.x2, self.x1, self.y2, self.y1 = self.x1, x, self.y1, y
        return y


def whoosh(dur, f_from, f_to, seed, hp=180):
    """Soft band-limited noise swept between two cutoffs, sin^2 window."""
    rnd = random.Random(seed)
    lp1, lp2, h = Biquad(), Biquad(), Biquad()
    out = []
    for i in range(int(SR * dur)):
        p = i / (SR * dur)
        fc = f_from * (f_to / f_from) ** p
        v = lp2.run(lp1.run(rnd.uniform(-1, 1), "lp", fc), "lp", fc)
        v = h.run(v, "hp", hp)
        w = math.sin(math.pi * min(1.0, p * 1.6)) ** 2 if p < 0.3125 else math.cos(math.pi / 2 * (p - 0.3125) / 0.6875) ** 2
        out.append(v * w)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] if i < len(t) else 0.0 for t in tracks) for i in range(n)]


def delayed(track, sec):
    return [0.0] * int(SR * sec) + track


def scaled(track, k):
    return [v * k for v in track]


def marimba(f, dur, bright=1.0):
    """Warm mallet: fundamental + soft octave + quickly-fading 4x 'wood' partial."""
    return voice(lambda t: f, dur, [(1, 1.0, dur * 0.35), (2, 0.16, dur * 0.18), (3.98, 0.10 * bright, 0.018)], 0.003)


def gen_sounds():
    write_wav("slide", whoosh(0.11, 2600, 700, seed=3), 0.5)

    # merge_1..11 (tiles 4 .. 4096): rounded "bloop" climbing a major pentatonic
    steps = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24]
    for k, st in enumerate(steps, start=1):
        f0 = 330 * 2 ** (st / 12)
        body = voice(lambda t, f0=f0: f0 * (0.9 + 0.1 * (1 - math.exp(-t / 0.02))), 0.32,
                     [(1, 1.0, 0.085), (2, 0.14, 0.04), (3, 0.04, 0.02)], 0.004)
        sub = voice(lambda t, f0=f0: f0 / 2, 0.1, [(1, 0.35, 0.03)], 0.004)
        write_wav("merge_%d" % k, mix(body, sub), 0.62)

    write_wav("spawn", voice(lambda t: 1760, 0.06, [(1, 1.0, 0.012), (2, 0.1, 0.006)], 0.001), 0.3)

    thud = voice(lambda t: 72 + 60 * math.exp(-t / 0.025), 0.16, [(1, 1.0, 0.05), (2, 0.2, 0.025)], 0.003)
    write_wav("bump", thud, 0.7)

    chirp = voice(lambda t: 420 * 2 ** (t / 0.14), 0.14, [(1, 1.0, 0.06), (2, 0.1, 0.03)], 0.01)
    write_wav("undo", mix(scaled(chirp, 0.6), scaled(whoosh(0.14, 600, 2400, seed=9), 1.2)), 0.5)

    notes = [523.25, 659.25, 783.99, 1046.5, 1318.5]
    write_wav("win", mix(*[delayed(marimba(f, 0.9), 0.085 * i) for i, f in enumerate(notes)]), 0.7)

    write_wav("lose", mix(marimba(392.0, 0.6, 0.5), delayed(marimba(311.13, 0.8, 0.5), 0.2)), 0.6)


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(SND, exist_ok=True)
    for res, size in TILE_PX.items():
        k = size / 200.0
        make_tile(os.path.join(IMG, "tile_%s.png" % res), size, round(size * 0.07), round(7 * k))
        make_tile(os.path.join(IMG, "cell_%s.png" % res), size, round(size * 0.07), round(6 * k), inset=True)
        make_ring(os.path.join(IMG, "ring_%s.png" % res), size, round(size * 0.07), max(2, round(6 * k)))
        make_rr(os.path.join(IMG, "rr_%s.9.png" % res), PANEL_RADIUS[res])
    make_glow()
    make_bg(os.path.join(IMG, "bg.png"))
    for res, size in ICON_PX.items():
        for name, shapes in ICONS.items():
            make_icon_glyph(os.path.join(IMG, "ic_%s_%s.png" % (name, res)), shapes, size)
    # Channel posters (Roku spec: FHD 540x405, HD 290x218) and splash screens
    make_art(os.path.join(IMG, "poster_fhd.png"), 540, 405, 168, 14, grid=True)
    make_art(os.path.join(IMG, "poster_hd.png"), 290, 218, 90, 8, grid=True)
    make_art(os.path.join(IMG, "splash_fhd.png"), 1920, 1080, 200, 20)
    make_art(os.path.join(IMG, "splash_hd.png"), 1280, 720, 133, 13)
    gen_sounds()
    print("assets written")
