"""Stage game states on the real Roku and grab 1920x1080 device screenshots.

    ROKU_IP=... ROKU_PASS=... python3 tools/promo/capture.py [hero merge remote over win best]

Each shot installs a scratch build that loads a scripted board and never writes
the registry (the user's real save is untouched). Run `make install` afterwards to put the real build back.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
IP = os.environ["ROKU_IP"]
USER, PW = "rokudev", os.environ["ROKU_PASS"]


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def build(name, state, slow=1.0, show_end=False, auto=None):
    d = os.path.join(HERE, "build", "app_" + name)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(PROJ, d, ignore=shutil.ignore_patterns("out", "tools", "*.md", ".DS_Store"))
    # scripted board, and no registry writes
    p = os.path.join(d, "source/main.brs")
    t = open(p).read()
    lit = json.dumps(state).replace('"', '""')
    t = t.replace('    if reg.Exists("state") then saved = reg.Read("state")', '    saved = "%s"' % lit)
    t = t.replace('    scene.observeField("save", port)\n', "")
    open(p, "w").write(t)
    if show_end:
        p = os.path.join(d, "components/GameScene.brs")
        t = open(p).read()
        t = t.replace("            if canMove() and st.s > 0", "            if st.s > 0")
        t = t.replace("    if not resumed then newGame(false)", "    if not resumed then newGame(false)\n    if resumed then checkEnd()")
        open(p, "w").write(t)
    if auto:
        # ECP keypresses are blocked on this Roku ("limited" mode), so the
        # staged build performs its own move after `delay` seconds.
        direction, delay = auto
        p = os.path.join(d, "components/GameScene.brs")
        t = open(p).read()
        t = t.replace('    m.top.signalBeacon("AppLaunchComplete")\n', '    m.top.signalBeacon("AppLaunchComplete")\n'
                      '    m.autoTimer = m.top.createChild("Timer")\n    m.autoTimer.duration = %s\n'
                      '    m.autoTimer.observeField("fire", "onAutoMove")\n    m.autoTimer.control = "start"\n' % delay)
        t += '\nsub onAutoMove()\n    doMove("%s")\nend sub\n' % direction
        open(p, "w").write(t)
    if slow != 1.0:
        for f, pats in {
            "components/Tile.xml": [r'(duration=")([\d.]+)(")'],
            "components/GameScene.brs": [r'(newTile\(mg\.v, mg\.idx, )([\d.]+)', r'(burst\(mg\.idx, mg\.v, )([\d.]+)',
                                         r'(spawnRandom\()([\d.]+)(\)\n\n    play)', r'(a\.duration = )([\d.]+)'],
        }.items():
            p = os.path.join(d, f)
            t = open(p).read()
            for pat in pats:
                t = re.sub(pat, lambda m: m.group(1) + str(round(float(m.group(2)) * slow, 3)) + (m.group(3) if m.lastindex >= 3 else ""), t)
            open(p, "w").write(t)
    z = os.path.join(HERE, "build", name + ".zip")
    if os.path.exists(z):
        os.remove(z)
    sh('cd "%s" && zip -9 -q -r "%s" manifest source components images sounds' % (d, z))
    return z


def install(z):
    out = sh('curl -sS -m 60 --digest -u %s:%s -F mysubmit=Install -F archive=@"%s" http://%s/plugin_install' % (USER, PW, z, IP))
    assert "Install Success" in out or "Identical" in out, out[-500:]


def key(k):
    sh("curl -s -d '' http://%s:8060/keypress/%s" % (IP, k))


def shot(path):
    sh('curl -sS -m 30 --digest -u %s:%s -F mysubmit=Screenshot -F passwd= -F archive= http://%s/plugin_inspect -o /dev/null' % (USER, PW, IP))
    sh('curl -sS --digest -u %s:%s "http://%s/pkgs/dev.jpg" -o "%s"' % (USER, PW, IP, path))
    print("saved", path)


def run(name, state, keys=(), waits=(1.5,), slow=1.0, show_end=False, settle=7.0, auto=None):
    z = build(name, state, slow, show_end, auto)
    install(z)
    time.sleep(settle)
    for k in keys:
        key(k)
    t0 = time.time()
    for i, w in enumerate(waits):
        time.sleep(max(0, w - (time.time() - t0)))
        shot(os.path.join(HERE, "shots", "%s_%d.jpg" % (name, i)))


if __name__ == "__main__":
    which = sys.argv[1:]
    BEST = 24860
    S = {
        "hero": dict(state={"g": [2, 8, 32, 0, 4, 16, 128, 8, 16, 256, 512, 2, 2048, 1024, 64, 4], "s": 24860, "b": BEST, "w": True, "m": False}),
        "merge": dict(state={"g": [4, 4, 8, 8, 16, 16, 2, 2, 32, 32, 0, 0, 64, 64, 128, 128], "s": 1240, "b": BEST, "w": False, "m": False},
                      auto=("left", 4.0), settle=3.5, waits=[1.3, 1.55, 1.8, 2.05, 2.3, 2.55], slow=10.0),
        "remote": dict(state={"g": [0, 2, 0, 0, 2, 4, 8, 0, 4, 16, 32, 2, 8, 64, 128, 4], "s": 1536, "b": BEST, "w": False, "m": False}),
        "over": dict(state={"g": [2, 4, 8, 16, 4, 8, 16, 32, 8, 16, 32, 64, 16, 32, 64, 128], "s": 3120, "b": BEST, "w": False, "m": False},
                     show_end=True, waits=[2.0]),
        "win": dict(state={"g": [1024, 1024, 4, 2, 256, 128, 16, 8, 64, 32, 8, 2, 4, 2, 0, 0], "s": 19876, "b": BEST, "w": False, "m": False},
                    auto=("left", 3.0), settle=3.0, waits=[2.5, 4.0]),
        "best": dict(state={"g": [2, 0, 8, 2, 16, 32, 4, 8, 128, 64, 16, 4, 256, 512, 1024, 2048], "s": 20528, "b": 20528, "w": True, "m": False}),
    }
    for n in which or S:
        run(n, **S[n])
