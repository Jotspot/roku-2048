"""Compose the six 1920x1080 store screenshots as HTML and render with headless Chrome.

    python3 tools/promo/make_slides.py      -> store/screenshots/*.png

Gameplay images in shots/ are real device captures made by capture.py.
Font: Outfit (SIL Open Font License), bundled in fonts/.
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "store", "screenshots")
ICONS = os.path.join(HERE, "..", "..", "images")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TILE = {2: ("#EEE4DA", "#776E65"), 0: ("#F59563", "#F9F6F2"), 4: ("#F67C5F", "#F9F6F2"), 8: ("#EDC22E", "#F9F6F2")}

CSS = """
@font-face { font-family: Outfit; src: url(../fonts/outfit.woff2) format('woff2'); font-weight: 100 900; }
* { margin: 0; box-sizing: border-box; }
html, body { width: 1920px; height: 1080px; overflow: hidden; }
body {
  font-family: Outfit, sans-serif; color: #5E564E; position: relative;
  background: radial-gradient(ellipse 90% 80% at 30% 35%, #FBF8F1 0%, #F3EDE1 55%, #E9E1D1 100%);
}
.deco { position: absolute; border-radius: 28px; filter: blur(1px); }
.copy { position: absolute; left: 130px; top: 0; bottom: 0; width: 600px;
        display: flex; flex-direction: column; justify-content: center; }
.right .copy { left: auto; right: 120px; }
.kicker { display: inline-flex; align-self: flex-start; align-items: center; gap: 12px;
          background: #8F7A66; color: #F9F6F2; font-weight: 600; font-size: 24px; letter-spacing: .08em;
          text-transform: uppercase; padding: 12px 22px; border-radius: 14px; margin-bottom: 34px;
          box-shadow: 0 6px 0 #74624F; }
.kicker img { width: 30px; height: 30px; }
h1 { font-weight: 800; font-size: 86px; line-height: 1.02; letter-spacing: -.02em; color: #5E564E; }
h1 em { font-style: normal; color: #F2804F; }
p.sub { margin-top: 30px; font-size: 34px; line-height: 1.38; font-weight: 400; color: #85796C; max-width: 560px; }
.badges { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 40px; }
.badge { background: rgba(143,122,102,.12); color: #74624F; font-weight: 600; font-size: 24px;
         padding: 12px 20px; border-radius: 12px; }
.tv { position: absolute; left: 790px; top: 180px; width: 1040px; }
.right .tv { left: 90px; }
.screen { position: relative; border-radius: 22px; background: #1C1A19; padding: 14px;
          box-shadow: 0 50px 90px -30px rgba(70,52,34,.55), 0 18px 36px -12px rgba(70,52,34,.35), inset 0 0 0 2px #2d2a28; }
.screen img { display: block; width: 100%; border-radius: 10px; }
.stand { margin: 0 auto; width: 260px; height: 26px; background: linear-gradient(#2a2725, #151312);
         border-radius: 0 0 16px 16px; }
.shadow { margin: 0 auto; width: 620px; height: 22px; border-radius: 50%;
          background: radial-gradient(rgba(70,52,34,.28), transparent 70%); }
.zoom { position: absolute; width: 380px; height: 380px; border-radius: 30px; overflow: hidden;
        border: 8px solid #FFFDF8; box-shadow: 0 30px 60px -18px rgba(70,52,34,.5); }
.zoom img { position: absolute; }
.boardcard { position: absolute; left: 150px; top: 80px; width: 920px; height: 920px; border-radius: 34px;
             overflow: hidden; transform: rotate(-2.5deg);
             box-shadow: 0 60px 100px -30px rgba(70,52,34,.55), 0 20px 40px -14px rgba(70,52,34,.35); }
.boardcard img { position: absolute; width: 1920px; left: -160px; top: -80px; }
.controls { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 28px; margin-top: 44px; }
.ctl { display: flex; align-items: center; gap: 16px; font-size: 30px; font-weight: 500; color: #74624F; }
.ctl i { width: 72px; height: 50px; border-radius: 12px; background: #8F7A66; display: flex;
         align-items: center; justify-content: center; box-shadow: 0 5px 0 #74624F; }
.ctl i img { width: 32px; height: 32px; }
.logo { display: grid; grid-template-columns: repeat(4, 96px); gap: 12px; margin-bottom: 44px; }
.logo div { height: 96px; border-radius: 14px; display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 60px; box-shadow: inset 0 -7px 0 rgba(0,0,0,.14), 0 12px 22px -10px rgba(90,60,30,.45); }
"""


def deco(items):
    """Faded, oversized brand tiles drifting at the edges."""
    out = []
    for x, y, s, c, o, r in items:
        out.append(f'<div class="deco" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;background:{c};opacity:{o};transform:rotate({r}deg)"></div>')
    return "\n".join(out)


DECO_A = deco([(-80, 760, 300, "#EDC22E", .16, -12), (1650, -90, 260, "#F67C5F", .12, 14), (560, 950, 180, "#F2B179", .14, 8)])
DECO_B = deco([(1700, 800, 320, "#EDC22E", .14, 10), (-110, -70, 280, "#F59563", .12, -10), (1160, 960, 160, "#EDCF72", .16, -6)])


def tv(shot, extra=""):
    return f'''<div class="tv">
  <div class="screen"><img src="../shots/{shot}"></div>
  <div class="stand"></div><div class="shadow"></div>{extra}
</div>'''


def page(body, right=False, decos=DECO_A):
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body class="{'right' if right else ''}">{decos}{body}</body></html>'''


def logo():
    cells = []
    for d, bg in zip("2048", ["#F2B179", "#F59563", "#F67C5F", "#EDC22E"]):
        cells.append(f'<div style="background:{bg};color:#F9F6F2">{d}</div>')
    return '<div class="logo">' + "".join(cells) + "</div>"


def zoom(shot, sx, sy, scale, left, top):
    """Magnified crop of a screenshot: (sx, sy) is the top-left of the source region in 1920x1080 px."""
    w = 1920 * scale
    return (f'<div class="zoom" style="left:{left}px;top:{top}px">'
            f'<img src="../shots/{shot}" style="width:{w}px;left:{-sx*scale}px;top:{-sy*scale}px"></div>')


SLIDES = {
    "01_hero": page(f'''
<div class="copy">
  {logo()}
  <h1>The classic puzzle, <em>made for your TV.</em></h1>
  <p class="sub">Slide the tiles, merge matching numbers and reach 2048, all from the comfort of your couch.</p>
</div>
{tv("hero_0.jpg")}'''),

    "02_merges": page(f'''
<div class="boardcard"><img src="../shots/merge_1.jpg"></div>
<div class="copy">
  <div class="kicker">Feels great</div>
  <h1>Snappy, <em>satisfying</em> merges.</h1>
  <p class="sub">Every slide, squish and pop is tuned to feel instant and fun, with sound effects that rise as your tiles grow.</p>
</div>''', right=True, decos=DECO_B),

    "03_remote": page(f'''
<div class="copy">
  <div class="kicker"><img src="../../../images/ic_dpad_fhd.png">Easy to play</div>
  <h1>Just use your <em>remote.</em></h1>
  <p class="sub">Press the arrow pad to slide every tile. No extra controller, no learning curve.</p>
  <div class="controls">
    <div class="ctl"><i><img src="../../../images/ic_dpad_fhd.png"></i>Slide tiles</div>
    <div class="ctl"><i><img src="../../../images/ic_replay_fhd.png"></i>Undo</div>
    <div class="ctl"><i><img src="../../../images/ic_options_fhd.png"></i>New game</div>
    <div class="ctl"><i><img src="../../../images/ic_playpause_fhd.png"></i>Sound on/off</div>
  </div>
</div>
{tv("remote_0.jpg")}'''),

    "04_undo": page(f'''
<div class="copy">
  <div class="kicker"><img src="../../../images/ic_replay_fhd.png">Second chances</div>
  <h1>Oops? <em>Undo it.</em></h1>
  <p class="sub">Press Replay to take back your last move, even right after a game over.</p>
</div>
{tv("over_0.jpg")}''', right=True, decos=DECO_B),

    "05_win": page(f'''
<div class="copy">
  <div class="kicker">The big goal</div>
  <h1>Reach 2048. <em>Then keep going.</em></h1>
  <p class="sub">Celebrate the win, then push on for 4096 and beyond.</p>
</div>
{tv("win_1.jpg")}'''),

    "06_resume": page(f'''
<div class="copy">
  <div class="kicker">Always saved</div>
  <h1>Pick up right <em>where you left off.</em></h1>
  <p class="sub">Your game and best score are saved after every move, so you can jump back in any time.</p>
  <div class="badges"><span class="badge">Crisp in HD &amp; Full HD</span><span class="badge">No ads</span><span class="badge">No account needed</span></div>
</div>
{tv("best_0.jpg")}''', right=True, decos=DECO_B),
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    for name, html in SLIDES.items():
        src = os.path.join(HERE, "build", name + ".html")
        open(src, "w").write(html)
        png = os.path.join(OUT, name + ".png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=1920,1080", "--virtual-time-budget=3000", f"--screenshot={png}", "file://" + src],
                       capture_output=True)
        print(name, os.path.getsize(png) if os.path.exists(png) else "FAILED")
