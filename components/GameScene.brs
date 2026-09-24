' 2048 game scene: layout, grid logic, input, and animation orchestration.
'
' Snappiness rule: input is never blocked. The logical grid updates instantly on
' each key press; if the previous move is still animating, its slides are
' snapped to their end state first (Tile.finish) and the new move plays.
'
' Merge choreography: both source tiles slide into the target cell (100 ms,
' ease-out) while squishing to 80%, then the merged tile pops out of them.

sub init()
    m.L = layout()
    m.global.addFields({ layout: m.L })
    L = m.L

    m.top.backgroundURI = ""
    m.top.backgroundColor = "0xFAF8EFFF"

    m.board = m.top.findNode("boardGroup")
    m.tileLayer = m.top.findNode("tileLayer")
    m.plusLbl = m.top.findNode("plusLbl")
    m.plusAnim = m.top.findNode("plusAnim")
    m.scoreBump = m.top.findNode("scoreBump")
    m.bestBump = m.top.findNode("bestBump")
    m.nudgeAnim = m.top.findNode("nudgeAnim")
    m.nudgeInterp = m.top.findNode("nudgeInterp")
    m.flashAnim = m.top.findNode("flashAnim")
    m.delayTimer = m.top.findNode("delayTimer")
    m.initTimer = m.top.findNode("initTimer")
    m.delayTimer.observeField("fire", "onDelayFire")
    m.initTimer.observeField("fire", "onDeferredInit")

    buildBoard()
    buildRings()
    buildPanel()
    m.overlay = m.top.findNode("overlayHost").createChild("Overlay")
    m.overlay.translation = [L.bx, L.by]
    m.overlay.visible = false

    m.lines = buildLines()
    m.dirs = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] }
    m.grid = filled(0)
    m.tiles = filled(invalid)
    m.pool = []
    m.moving = []
    m.dying = []
    m.undo = invalid
    m.score = 0
    m.best = 0
    m.won = false
    m.muted = false
    m.mode = "play"      ' play | win | over | confirm
    m.pendingEnd = ""
    m.sfx = {}

    ' Registry writes run on their own Task thread (see SaveTask). Started
    ' before loadState() so the very first snapshot is captured.
    m.saver = m.top.createChild("SaveTask")
    m.saver.control = "RUN"

    loadState()
    m.top.setFocus(true)
    m.initTimer.control = "start"
    print "[2048] "; L.res; " layout ready"
end sub

' Runs right after the first frame: the board is on screen and interactive, so
' signal launch complete (cert 3.2). Audio decoding and pool warm-up happen after
' that, so they never delay launch.
sub onDeferredInit()
    m.top.signalBeacon("AppLaunchComplete")
    names = ["slide", "spawn", "bump", "undo", "win", "lose"]
    for i = 1 to 11
        names.push("merge_" + i.ToStr())
    end for
    for each n in names
        snd = m.top.createChild("SoundEffect")
        snd.uri = "pkg:/sounds/" + n + ".wav"
        m.sfx[n] = snd
    end for

    live = m.dying.count()
    for each t in m.tiles
        if t <> invalid then live = live + 1
    end for
    while m.pool.count() + live < 24
        m.pool.push(createTile())
    end while
end sub

' ----------------------------------------------------------------- layout --

' All geometry derives from the design height (720 or 1080) and is rounded to
' whole pixels. Tile images are pre-rendered at exactly L.tile px per resolution.
function layout() as object
    H = 1080
    r = m.top.currentDesignResolution
    if r <> invalid and r.height <> invalid and r.height > 0 then H = r.height
    k = H / 1080.0
    res = "fhd"
    if H < 1000 then res = "hd"
    tile = Int(200 * k + 0.5)
    gap = Int(16 * k + 0.5)
    board = tile * 4 + gap * 5
    return {
        W: Int(H * 16 / 9), H: H, k: k, res: res,
        tile: tile, gap: gap, step: tile + gap, board: board,
        bx: Int(180 * k + 0.5), by: Int((H - board) / 2),
        band: Int(7 * k + 0.5),                ' bevel depth baked into tile_*.png
        tileUri: "pkg:/images/tile_" + res + ".png",
        cellUri: "pkg:/images/cell_" + res + ".png",
        ringUri: "pkg:/images/ring_" + res + ".png",
        rrUri: "pkg:/images/rr_" + res + ".9.png",
        icon: Int(44 * k + 0.5),               ' remote-button icons, pre-rendered per res
        spring: springCurve(20, 0.25, 0.7),    ' overlay card pop
        glide: easeOutCubic(10)                ' tile slides
    }
end function

function easeOutCubic(n as integer) as object
    keys = []
    vals = []
    for i = 0 to n
        p = i / n
        keys.push(p)
        vals.push(1 - (1 - p) * (1 - p) * (1 - p))
    end for
    return { keys: keys, vals: vals }
end function

' Damped spring settling within `dur`, sampled into n+1 keyframes for linear
' interpolators. zeta 0.7 matches play2048.co's "bounce: 0.3".
function springCurve(n as integer, dur as float, zeta as float) as object
    w = 4.6 / (zeta * dur)
    wd = w * Sqr(1 - zeta * zeta)
    keys = []
    vals = []
    for i = 0 to n
        t = dur * i / n
        e = Exp(-zeta * w * t)
        keys.push(i / n)
        vals.push(1 - e * (Cos(wd * t) + (zeta * w / wd) * Sin(wd * t)))
    end for
    vals[n] = 1.0
    return { keys: keys, vals: vals }
end function

function s(v as float) as integer
    return Int(v * m.L.k + 0.5)
end function

sub buildBoard()
    L = m.L
    m.board.translation = [L.bx, L.by]
    bg = m.top.findNode("bgGrad")
    bg.width = L.W
    bg.height = L.H

    sh = m.top.findNode("boardShadow")
    sh.translation = [-s(20), -s(12)]
    sh.width = L.board + s(40)
    sh.height = L.board + s(40)

    for each id in ["boardBg", "flash"]
        p = m.top.findNode(id)
        p.uri = L.rrUri
        p.width = L.board
        p.height = L.board
    end for

    cells = m.top.findNode("cells")
    for i = 0 to 15
        p = cells.createChild("Poster")
        p.uri = L.cellUri
        p.width = L.tile
        p.height = L.tile
        p.blendColor = "0xCDC1B4FF"
        p.translation = [L.gap + (i mod 4) * L.step, L.gap + (i \ 4) * L.step]
    end for

    m.nudgeBase = [L.bx, L.by]
    m.nudgeAmp = s(14)
end sub

' Side panel, authored in 1080p units and scaled through s().
sub buildPanel()
    panel = m.top.findNode("panel")
    x = 1160
    brown = "0x776E65FF"

    mkLabel(panel, "2048", x - 10, 90, 600, 220, 190, true, brown, "left")
    mkLabel(panel, "Join the tiles, get to 2048!", x, 495, 580, 50, 34, false, brown, "left")

    m.scoreLbl = buildBox(m.top.findNode("scoreBox"), "SCORE", x, 330)
    m.bestLbl = buildBox(m.top.findNode("bestBox"), "BEST", x + 290, 330)

    m.plusLbl.width = s(270)
    m.plusLbl.height = s(60)
    m.plusLbl.font = "font:MediumBoldSystemFont"
    m.plusLbl.font.size = s(46)
    m.plusLbl.translation = [s(x), s(370)]
    m.top.findNode("plusMove").keyValue = [[s(x), s(370)], [s(x), s(285)]]

    ' Remote-button legend: icon chip + description.
    rows = [
        ["dpad", "Slide tiles"],
        ["replay", "Undo last move"],
        ["options", "New game"],
        ["playpause", "Sound: on"]
    ]
    y = 590
    for each r in rows
        chip = panel.createChild("Poster")
        chip.uri = m.L.rrUri
        chip.blendColor = "0x8F7A66FF"
        chip.translation = [s(x), s(y)]
        chip.width = s(96)
        chip.height = s(64)
        ic = panel.createChild("Poster")
        ic.uri = iconUri(r[0])
        ic.width = m.L.icon
        ic.height = m.L.icon
        ic.blendColor = "0xF9F6F2FF"
        ic.translation = [s(x) + Int((s(96) - m.L.icon) / 2), s(y) + Int((s(64) - m.L.icon) / 2)]
        ' the last row's description doubles as the live sound on/off label
        m.soundLbl = mkLabel(panel, r[1], x + 124, y, 400, 64, 32, false, brown, "left")
        y = y + 85
    end for
end sub

' Merge burst: a small pool of rounded outlines that grow and fade from a
' merged cell. They live in fxLayer, above all tiles, so neighbours never cover
' them. Growth animates the poster's real size (not scale) so every renderer
' draws it the same.
sub buildRings()
    L = m.L
    fx = m.top.findNode("fxLayer")
    m.rings = []
    for i = 0 to 7
        p = fx.createChild("Poster")
        p.id = "ring" + i.ToStr()
        p.uri = L.ringUri
        p.width = L.tile
        p.height = L.tile
        p.opacity = 0.0
        a = fx.createChild("Animation")
        a.duration = 0.38
        a.easeFunction = "outCubic"
        mv = a.createChild("Vector2DFieldInterpolator")
        mv.key = [0.0, 1.0]
        mv.fieldToInterp = p.id + ".translation"
        for each f in ["width", "height"]
            si = a.createChild("FloatFieldInterpolator")
            si.key = [0.0, 1.0]
            si.keyValue = [L.tile * 1.0, L.tile * 1.3]
            si.fieldToInterp = p.id + "." + f
        end for
        fi = a.createChild("FloatFieldInterpolator")
        fi.key = [0.0, 1.0]
        fi.keyValue = [0.75, 0.0]
        fi.fieldToInterp = p.id + ".opacity"
        m.rings.push({ p: p, a: a, mv: mv })
    end for
    m.ringNext = 0
end sub

sub burst(idx as integer, v as integer, delay as float)
    r = m.rings[m.ringNext]
    m.ringNext = (m.ringNext + 1) mod m.rings.count()
    r.a.control = "stop"
    c = cellCenter(idx)
    h0 = m.L.tile / 2.0
    h1 = h0 * 1.3
    r.mv.keyValue = [[c[0] - h0, c[1] - h0], [c[0] - h1, c[1] - h1]]
    r.p.translation = [c[0] - h0, c[1] - h0]
    r.p.width = m.L.tile
    r.p.height = m.L.tile
    r.p.blendColor = tileColors(v)[0]
    r.p.opacity = 0.0
    r.a.delay = delay
    r.a.control = "start"
end sub

' Score box whose origin is its centre, so its bump scales from the middle.
function buildBox(host as object, caption as string, x as integer, y as integer) as object
    w = 270
    h = 130
    host.translation = [s(x + w / 2), s(y + h / 2)]
    inner = host.createChild("Group")
    inner.translation = [-s(w / 2), -s(h / 2)]
    bg = inner.createChild("Poster")
    bg.uri = m.L.rrUri
    bg.blendColor = "0xBBADA0FF"
    bg.width = s(w)
    bg.height = s(h)
    mkLabel(inner, caption, 0, 14, w, 34, 28, true, "0xEEE4DAFF", "center")
    return mkLabel(inner, "0", 0, 48, w, 70, 56, true, "0xFFFFFFFF", "center")
end function

function iconUri(name as string) as string
    return "pkg:/images/ic_" + name + "_" + m.L.res + ".png"
end function

function mkLabel(parent as object, text as string, x as integer, y as integer, w as integer, h as integer, size as integer, bold as boolean, color as string, align as string) as object
    lbl = parent.createChild("Label")
    lbl.text = text
    lbl.translation = [s(x), s(y)]
    lbl.width = s(w)
    lbl.height = s(h)
    lbl.horizAlign = align
    lbl.vertAlign = "center"
    lbl.color = color
    if bold
        lbl.font = "font:MediumBoldSystemFont"
    else
        lbl.font = "font:MediumSystemFont"
    end if
    lbl.font.size = s(size)
    return lbl
end function

' ------------------------------------------------------------------ input --

function onKeyEvent(key as string, press as boolean) as boolean
    if not press then return false

    if key = "back"
        ' Back closes a dismissible modal (cert 4.6: return to the previous
        ' state); otherwise it exits to the Roku home screen. State is saved
        ' after every move, so exiting is always safe.
        if m.mode = "confirm" or m.mode = "win"
            closeOverlay()
            return true
        end if
        return false
    end if

    if key = "play"
        toggleMute()
        return true
    end if

    if m.mode = "play"
        if m.dirs.DoesExist(key)
            doMove(key)
        else if key = "replay"
            undoMove()
        else if key = "options"
            if m.score > 0
                m.mode = "confirm"
                m.overlay.callFunc("present", {
                    title: "New game?", sub: "Your current progress will be lost.", gold: false,
                    hints: [["OK", "Start over"], ["back", "Cancel"]]
                })
                play("spawn", 60)
            else
                newGame(true)
            end if
        end if
        return true
    end if

    if m.mode = "confirm"
        if key = "OK" or key = "options" then newGame(true)
        return true
    end if

    if m.mode = "win"
        if key = "OK"
            closeOverlay()
        else if key = "options"
            newGame(true)
        end if
        return true
    end if

    if m.mode = "over"
        if key = "OK" or key = "options"
            newGame(true)
        else if key = "replay"
            undoMove()
        end if
        return true
    end if

    return true
end function

' ------------------------------------------------------------------- game --

sub doMove(dir as string)
    finishAll()

    newGrid = filled(0)
    newTiles = filled(invalid)
    cmdAt = filled(invalid)
    cmds = []
    merges = []
    moved = false
    gained = 0
    maxMerge = 0

    for each line in m.lines[dir]
        tgt = 0
        canMerge = false
        for i = 0 to 3
            idx = line[i]
            v = m.grid[idx]
            if v > 0
                t = m.tiles[idx]
                if canMerge and newGrid[line[tgt - 1]] = v
                    d = line[tgt - 1]
                    nv = v * 2
                    newGrid[d] = nv
                    newTiles[d] = invalid
                    cmdAt[d].die = true
                    cmds.push({ t: t, from: idx, idx: d, die: true })
                    merges.push({ idx: d, v: nv })
                    gained = gained + nv
                    if nv > maxMerge then maxMerge = nv
                    canMerge = false
                    moved = true
                else
                    d = line[tgt]
                    newGrid[d] = v
                    newTiles[d] = t
                    c = { t: t, from: idx, idx: d, die: false }
                    cmds.push(c)
                    cmdAt[d] = c
                    if d <> idx then moved = true
                    canMerge = true
                    tgt = tgt + 1
                end if
            end if
        end for
    end for

    if not moved
        nudge(dir)
        return
    end if

    m.undo = { g: m.grid, s: m.score }
    for each c in cmds
        if c.die or c.idx <> c.from
            p = cellCenter(c.idx)
            c.t.callFunc("slide", { x: p[0], y: p[1], die: c.die })
            m.moving.push(c.t)
            if c.die then m.dying.push(c.t)
        end if
    end for
    m.grid = newGrid
    m.tiles = newTiles

    for each mg in merges
        t = newTile(mg.v, mg.idx, 0.07, "merge")
        burst(mg.idx, mg.v, 0.07)
        m.tileLayer.appendChild(t)   ' bring to front, above the shrinking sources
    end for
    spawnRandom(0.07)

    play("slide", 40)
    if gained > 0
        addScore(gained)
        k = 0
        v = maxMerge
        while v > 2 and k < 11
            v = v \ 2
            k = k + 1
        end while
        play("merge_" + k.ToStr(), 80)
    end if
    if maxMerge >= 2048
        m.flashAnim.control = "stop"
        m.flashAnim.control = "start"
    end if

    checkEnd()
    save()
end sub

sub checkEnd()
    if not m.won
        for each v in m.grid
            if v >= 2048
                m.won = true
                endAfterDelay("win", 0.35)
                return
            end if
        end for
    end if
    if not canMove() then endAfterDelay("over", 0.5)
end sub

' Lock input into the end state immediately, but let the last move's
' animations finish before the overlay springs in.
sub endAfterDelay(kind as string, sec as float)
    m.mode = kind
    m.pendingEnd = kind
    m.delayTimer.duration = sec
    m.delayTimer.control = "start"
end sub

sub onDelayFire()
    sub_ = "Score " + m.score.ToStr()
    if m.pendingEnd = "win"
        play("win", 85)
        m.overlay.callFunc("present", {
            title: "You win!", sub: sub_, gold: true,
            hints: [["OK", "Keep going"], ["options", "New game"]]
        })
    else if m.pendingEnd = "over"
        play("lose", 80)
        m.overlay.callFunc("present", {
            title: "Game over!", sub: sub_, gold: false,
            hints: [["OK", "Try again"], ["replay", "Undo"]]
        })
    end if
    m.pendingEnd = ""
end sub

sub closeOverlay()
    m.delayTimer.control = "stop"
    m.pendingEnd = ""
    m.overlay.callFunc("dismiss", {})
    m.mode = "play"
end sub

function canMove() as boolean
    for i = 0 to 15
        v = m.grid[i]
        if v = 0 then return true
        if (i mod 4) < 3 and m.grid[i + 1] = v then return true
        if i < 12 and m.grid[i + 4] = v then return true
    end for
    return false
end function

sub newGame(withSound as boolean)
    finishAll()
    closeOverlay()
    for i = 0 to 15
        if m.tiles[i] <> invalid then releaseTile(m.tiles[i])
    end for
    m.grid = filled(0)
    m.tiles = filled(invalid)
    m.undo = invalid
    m.won = false
    m.score = 0
    m.scoreLbl.text = "0"
    spawnRandom(0.0)
    spawnRandom(0.06)
    if withSound then play("spawn", 70)
    save()
end sub

sub undoMove()
    if m.undo = invalid
        play("bump", 50)
        return
    end if
    finishAll()
    if m.mode <> "play" then closeOverlay()

    g = m.undo.g
    for i = 0 to 15
        if m.grid[i] <> g[i]
            if m.tiles[i] <> invalid then releaseTile(m.tiles[i])
            m.tiles[i] = invalid
            m.grid[i] = g[i]
            if g[i] > 0 then newTile(g[i], i, 0.0)
        end if
    end for
    m.score = m.undo.s
    m.undo = invalid
    m.scoreLbl.text = m.score.ToStr()
    bump(m.scoreBump)
    play("undo", 70)
    save()
end sub

sub spawnRandom(delay as float)
    empties = []
    for i = 0 to 15
        if m.grid[i] = 0 then empties.push(i)
    end for
    if empties.count() = 0 then return
    idx = empties[Rnd(empties.count()) - 1]
    v = 2
    if Rnd(10) = 1 then v = 4
    m.grid[idx] = v
    newTile(v, idx, delay)
end sub

' ------------------------------------------------------------------ tiles --

function createTile() as object
    t = m.tileLayer.createChild("Tile")
    t.visible = false
    return t
end function

function newTile(v as integer, idx as integer, delay as float, kind = "appear" as string) as object
    if m.pool.count() > 0
        t = m.pool.pop()
    else
        t = createTile()
    end if
    p = cellCenter(idx)
    t.callFunc("spawn", { x: p[0], y: p[1], v: v, d: delay, kind: kind })
    m.tiles[idx] = t
    return t
end function

sub releaseTile(t as object)
    t.callFunc("hide", {})
    m.pool.push(t)
end sub

sub finishAll()
    for each t in m.moving
        t.callFunc("finish", {})
    end for
    m.moving = []
    for each t in m.dying
        m.pool.push(t)
    end for
    m.dying = []
    if m.nudgeAnim.state <> "stopped"
        m.nudgeAnim.control = "stop"
        m.board.translation = m.nudgeBase
    end if
end sub

sub nudge(dir as string)
    d = m.dirs[dir]
    b = m.nudgeBase
    kv = []
    for each f in [0.0, 1.0, -0.3, 0.08, 0.0]
        kv.push([b[0] + d[0] * m.nudgeAmp * f, b[1] + d[1] * m.nudgeAmp * f])
    end for
    m.nudgeInterp.keyValue = kv
    m.nudgeAnim.control = "stop"
    m.nudgeAnim.control = "start"
    play("bump", 55)
end sub

function cellCenter(i as integer) as object
    L = m.L
    h = L.tile / 2.0
    return [L.gap + (i mod 4) * L.step + h, L.gap + (i \ 4) * L.step + h]
end function

' ------------------------------------------------------------------ score --

sub addScore(gained as integer)
    m.score = m.score + gained
    m.scoreLbl.text = m.score.ToStr()
    bump(m.scoreBump)
    if m.score > m.best
        m.best = m.score
        m.bestLbl.text = m.best.ToStr()
        bump(m.bestBump)
    end if
    m.plusLbl.text = "+" + gained.ToStr()
    m.plusAnim.control = "stop"
    m.plusAnim.control = "start"
end sub

sub bump(anim as object)
    anim.control = "stop"
    anim.control = "start"
end sub

' ------------------------------------------------------------------ sound --

sub play(name as string, vol as integer)
    if m.muted then return
    snd = m.sfx[name]
    if snd = invalid then return
    snd.volume = vol
    snd.control = "stop"
    snd.control = "play"
end sub

sub toggleMute()
    m.muted = not m.muted
    updateSoundLbl()
    play("spawn", 70)
    save()
end sub

sub updateSoundLbl()
    if m.muted
        m.soundLbl.text = "Sound: off"
    else
        m.soundLbl.text = "Sound: on"
    end if
end sub

' ------------------------------------------------------------ persistence --

sub save()
    m.saver.data = FormatJson({ g: m.grid, s: m.score, b: m.best, w: m.won, m: m.muted })
end sub

sub loadState()
    st = invalid
    raw = m.global.saved
    if raw <> invalid and raw <> "" then st = ParseJson(raw)
    resumed = false
    if st <> invalid
        if st.b <> invalid then m.best = st.b
        if st.m <> invalid then m.muted = st.m
        g = st.g
        if g <> invalid and g.count() = 16 and st.s <> invalid
            for i = 0 to 15
                m.grid[i] = g[i]
            end for
            if canMove() and st.s > 0
                m.score = st.s
                if st.w <> invalid then m.won = st.w
                ' Deal the saved board back in with a quick staggered pop.
                n = 0
                for i = 0 to 15
                    if m.grid[i] > 0
                        newTile(m.grid[i], i, n * 0.02)
                        n = n + 1
                    end if
                end for
                resumed = true
            else
                m.grid = filled(0)
            end if
        end if
    end if
    updateSoundLbl()
    m.scoreLbl.text = m.score.ToStr()
    m.bestLbl.text = m.best.ToStr()
    if not resumed then newGame(false)
end sub

' ---------------------------------------------------------------- helpers --

function filled(v as dynamic) as object
    a = []
    for i = 0 to 15
        a.push(v)
    end for
    return a
end function

' Cell indices per line, ordered from the edge tiles slide toward.
function buildLines() as object
    L = { left: [], right: [], up: [], down: [] }
    for k = 0 to 3
        L.left.push([k * 4, k * 4 + 1, k * 4 + 2, k * 4 + 3])
        L.right.push([k * 4 + 3, k * 4 + 2, k * 4 + 1, k * 4])
        L.up.push([k, k + 4, k + 8, k + 12])
        L.down.push([k + 12, k + 8, k + 4, k])
    end for
    return L
end function
