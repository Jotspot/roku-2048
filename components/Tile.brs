sub init()
    L = m.global.layout
    m.size = L.tile
    m.k = L.k
    half = L.tile / 2.0

    m.mover = m.top.findNode("mover")
    m.popper = m.top.findNode("popper")
    m.bg = m.top.findNode("bg")
    m.lbl = m.top.findNode("lbl")
    m.bg.uri = L.tileUri
    m.bg.width = L.tile
    m.bg.height = L.tile
    m.bg.translation = [-half, -half]
    m.lbl.width = L.tile
    m.lbl.height = L.tile
    ' centre the number on the tile face, above the bevel band
    m.lbl.translation = [-half, -half - L.band / 2.0]

    ' glow.9.png feathers 20px beyond the tile edge at every resolution
    m.glow = m.top.findNode("glow")
    m.glow.width = L.tile + 40
    m.glow.height = L.tile + 40
    m.glow.translation = [-half - 20, -half - 20 + L.band / 2.0]

    m.moveAnim = m.top.findNode("moveAnim")
    m.moveInterp = m.top.findNode("moveInterp")
    m.shrinkAnim = m.top.findNode("shrinkAnim")
    m.popAnim = m.top.findNode("popAnim")
    m.moveAnim.observeField("state", "onMoveState")

    ' Slides: 100 ms ease-out (keyValues built per slide from this curve).
    ' Merge sources shrink to 80% over the same 100 ms.
    m.curve = L.glide.vals
    m.moveInterp.key = L.glide.keys
    shrink = []
    for each v in m.curve
        s = 1.0 - 0.2 * v
        shrink.push([s, s])
    end for
    shrinkInterp = m.top.findNode("shrinkInterp")
    shrinkInterp.key = L.glide.keys
    shrinkInterp.keyValue = shrink

    ' Two entrance styles sharing popAnim (150 ms, linear over keyframes):
    '  merge  - picks up from the sources' squished 80%, overshoots, settles
    '  appear - new tiles fade in while easing up from 60%
    appearKeys = []
    appearScale = []
    appearFade = []
    for i = 0 to 10
        p = i / 10.0
        e = 1 - (1 - p) * (1 - p) * (1 - p)
        appearKeys.push(p)
        a = 0.6 + 0.4 * e
        appearScale.push([a, a])
        appearFade.push(p * p * (3 - 2 * p))
    end for
    m.styles = {
        merge: {
            sk: [0.0, 0.4, 0.75, 1.0], sv: [[0.8, 0.8], [1.12, 1.12], [0.98, 0.98], [1.0, 1.0]],
            fk: [0.0, 0.25, 1.0], fv: [0.0, 1.0, 1.0]
        },
        appear: { sk: appearKeys, sv: appearScale, fk: appearKeys, fv: appearFade }
    }
    m.popInterp = m.top.findNode("popInterp")
    m.popFade = m.top.findNode("popFade")
    m.style = ""

    m.fontSize = 0
    m.dying = false
    m.target = [0, 0]
end sub

' {x, y, v, d, kind}: enter at centre x,y with value v after d seconds.
' kind is "merge" (pop) or "appear" (soft fade-in).
function spawn(a as object) as dynamic
    stopAll()
    m.dying = false
    m.target = [a.x, a.y]
    m.mover.translation = m.target
    setValue(a.v)
    if a.kind <> m.style
        m.style = a.kind
        st = m.styles[a.kind]
        m.popInterp.key = st.sk
        m.popInterp.keyValue = st.sv
        m.popFade.key = st.fk
        m.popFade.keyValue = st.fv
    end if
    m.popper.scale = m.styles[a.kind].sv[0]
    m.popper.opacity = 0.0
    m.top.visible = true
    m.popAnim.delay = a.d
    m.popAnim.control = "start"
    return true
end function

' {x, y, die}: slide to centre x,y. Merge sources (die) also shrink to 80%
' while travelling, then vanish under the merged tile.
function slide(a as object) as dynamic
    from = m.mover.translation
    m.target = [a.x, a.y]
    dx = a.x - from[0]
    dy = a.y - from[1]
    kv = []
    for each v in m.curve
        kv.push([from[0] + dx * v, from[1] + dy * v])
    end for
    m.moveInterp.keyValue = kv
    m.dying = a.die
    m.moveAnim.control = "start"
    if a.die
        m.popAnim.control = "stop"
        m.popper.opacity = 1.0
        m.shrinkAnim.control = "start"
    end if
    return true
end function

' Snap the slide to its end state (input arrived mid-animation). A spawn pop
' only touches scale, so it's left running and overlaps the next move.
function finish(a as dynamic) as dynamic
    if m.moveAnim.state <> "stopped" then m.moveAnim.control = "stop"
    settle()
    return true
end function

function hide(a as dynamic) as dynamic
    stopAll()
    m.dying = false
    m.top.visible = false
    return true
end function

sub onMoveState()
    ' Guard against a stale "stopped" arriving after a new slide already started.
    if m.moveAnim.state = "stopped" then settle()
end sub

sub settle()
    m.mover.translation = m.target
    if m.dying
        m.dying = false
        m.shrinkAnim.control = "stop"
        m.top.visible = false
    end if
end sub

sub stopAll()
    m.moveAnim.control = "stop"
    m.shrinkAnim.control = "stop"
    m.popAnim.control = "stop"
    m.popper.scale = [1.0, 1.0]
    m.popper.opacity = 1.0
end sub

sub setValue(v as integer)
    c = tileColors(v)
    m.bg.blendColor = c[0]
    m.lbl.color = c[1]
    if v >= 128
        lvl = 0
        g = v
        while g > 128 and lvl < 4
            g = g \ 2
            lvl = lvl + 1
        end while
        m.glow.blendColor = c[0]
        m.glow.opacity = 0.35 + 0.12 * lvl
        m.glow.visible = true
    else
        m.glow.visible = false
    end if
    txt = v.ToStr()
    m.lbl.text = txt
    n = Len(txt)
    base = 100
    if n = 3
        base = 84
    else if n = 4
        base = 66
    else if n >= 5
        base = 52
    end if
    size = Int(base * m.k + 0.5)
    if size <> m.fontSize
        m.fontSize = size
        m.lbl.font = "font:MediumBoldSystemFont"
        m.lbl.font.size = size
    end if
end sub
