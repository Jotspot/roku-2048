sub init()
    L = m.global.layout
    m.L = L
    B = L.board

    m.dim = m.top.findNode("dim")
    m.dim.uri = L.rrUri
    m.dim.width = B
    m.dim.height = B

    m.card = m.top.findNode("card")
    m.card.translation = [B / 2.0, B / 2.0]
    m.top.findNode("cardBody").translation = [-B / 2.0, -B / 2.0]

    m.title = m.top.findNode("title")
    place(m.title, 0, sc(L, 250), B, sc(L, 150), sc(L, 104))
    m.sub = m.top.findNode("sub")
    place(m.sub, 0, sc(L, 410), B, sc(L, 60), sc(L, 40))

    m.chipW = sc(L, 340)
    m.chipY = sc(L, 540)
    m.chips = []
    for i = 1 to 2
        p = "chip" + i.ToStr()
        bg = m.top.findNode(p + "Bg")
        bg.uri = L.rrUri
        bg.width = m.chipW
        bg.height = sc(L, 104)
        ' Top row: remote-button icon (or "OK" text), bottom row: the action.
        k = m.top.findNode(p + "Key")
        place(k, 0, sc(L, 8), m.chipW, L.icon, sc(L, 28))
        ic = m.top.findNode(p + "Icon")
        ic.width = L.icon
        ic.height = L.icon
        ic.translation = [Int((m.chipW - L.icon) / 2), sc(L, 8)]
        a = m.top.findNode(p + "Act")
        place(a, 0, sc(L, 52), m.chipW, sc(L, 44), sc(L, 38))
        m.chips.push({ g: m.top.findNode(p), k: k, ic: ic, a: a })
    end for

    ' Card pops in on a spring: 0.9 -> 1 with a hint of overshoot.
    keys = L.spring.keys
    sv = []
    fade = []
    for each v in L.spring.vals
        s = 0.9 + 0.1 * v
        sv.push([s, s])
        f = v * 2.5
        if f > 1 then f = 1.0
        fade.push(f)
    end for
    m.top.findNode("cardScale").key = keys
    m.top.findNode("cardScale").keyValue = sv
    m.top.findNode("cardFade").key = keys
    m.top.findNode("cardFade").keyValue = fade
    m.dimIn = m.top.findNode("dimIn")
    m.dimIn.key = [0.0, 0.5, 1.0]

    m.inAnim = m.top.findNode("inAnim")
    m.outAnim = m.top.findNode("outAnim")
    m.dimOut = m.top.findNode("dimOut")
    m.cardOut = m.top.findNode("cardOut")
    m.outAnim.observeField("state", "onOutState")
    m.closing = false
end sub

function sc(L as object, v as float) as integer
    return Int(v * L.k + 0.5)
end function

sub place(lbl as object, x as integer, y as integer, w as integer, h as integer, size as integer)
    lbl.translation = [x, y]
    lbl.width = w
    lbl.height = h
    lbl.font = "font:MediumBoldSystemFont"
    lbl.font.size = size
end sub

' {title, sub, gold, hints: [[key, action], ...]}; key is "OK" or an icon name
function present(a as object) as dynamic
    m.closing = false
    m.outAnim.control = "stop"
    m.inAnim.control = "stop"

    dimTo = 0.88
    if a.gold
        m.dim.blendColor = "0xEDC22EFF"
        m.title.color = "0xF9F6F2FF"
        m.sub.color = "0xF9F6F2FF"
        dimTo = 0.86
    else
        m.dim.blendColor = "0xEEE4DAFF"
        m.title.color = "0x776E65FF"
        m.sub.color = "0x776E65FF"
    end if
    m.dimIn.keyValue = [0.0, dimTo, dimTo]
    m.title.text = a.title
    m.sub.text = a.sub

    hints = a.hints
    B = m.L.board
    gap = sc(m.L, 30)
    if hints.count() = 1
        xs = [Int((B - m.chipW) / 2)]
    else
        x0 = Int((B - (m.chipW * 2 + gap)) / 2)
        xs = [x0, x0 + m.chipW + gap]
    end if
    for i = 0 to 1
        c = m.chips[i]
        if i < hints.count()
            c.g.visible = true
            c.g.translation = [xs[i], m.chipY]
            key = hints[i][0]
            if key = "OK"
                c.k.text = key
                c.k.visible = true
                c.ic.visible = false
            else
                c.ic.uri = "pkg:/images/ic_" + key + "_" + m.L.res + ".png"
                c.ic.visible = true
                c.k.visible = false
            end if
            c.a.text = hints[i][1]
        else
            c.g.visible = false
        end if
    end for

    m.dim.opacity = 0.0
    m.card.opacity = 0.0
    m.card.scale = [0.9, 0.9]
    m.top.visible = true
    m.inAnim.control = "start"
    return true
end function

function dismiss(a as dynamic) as dynamic
    if not m.top.visible or m.closing then return false
    m.closing = true
    m.inAnim.control = "stop"
    m.dimOut.keyValue = [m.dim.opacity, 0.0]
    m.cardOut.keyValue = [m.card.opacity, 0.0]
    m.outAnim.control = "start"
    return true
end function

sub onOutState()
    if m.closing and m.outAnim.state = "stopped"
        m.closing = false
        m.top.visible = false
    end if
end sub
