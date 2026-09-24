' Entry point: reads the saved game for the scene, then only handles the
' certification plumbing (roInput, cert 5.2; memory monitoring).
'
' The main thread must not touch the scene after CreateScene(): on real devices
' the scene's init() is still running on the render thread, so observeField()
' there fails and field access can deadlock. Saving lives in SaveTask instead.
sub Main(args as dynamic)
    screen = CreateObject("roSGScreen")
    port = CreateObject("roMessagePort")
    screen.setMessagePort(port)

    reg = CreateObject("roRegistrySection", "roku2048")
    saved = ""
    if reg.Exists("state") then saved = reg.Read("state")
    screen.getGlobalNode().addFields({ saved: saved })

    screen.CreateScene("GameScene")
    screen.show()

    ' Deep links / voice "launch" commands: a game has no content to jump to,
    ' so any contentId simply lands on the (resumed) board.
    logDeepLink("launch", args)
    input = CreateObject("roInput")
    input.setMessagePort(port)

    ' Memory monitoring: the app uses a few MB, but log if the OS warns us.
    mem = CreateObject("roAppMemoryMonitor")
    if mem <> invalid
        mem.setMessagePort(port)
        mem.EnableMemoryWarningEvent(true)
        print "[2048] memory: "; mem.GetChannelAvailableMemory(); " KB free, "; mem.GetMemoryLimitPercent(); "% of limit used"
        limits = mem.GetChannelMemoryLimit()
        if limits <> invalid then print "[2048] memory limit: "; FormatJson(limits)
    end if
    info = CreateObject("roDeviceInfo")
    info.setMessagePort(port)
    info.EnableLowGeneralMemoryEvent(true)

    while true
        msg = wait(0, port)
        msgType = type(msg)
        if msgType = "roSGScreenEvent"
            if msg.isScreenClosed() then return
        else if msgType = "roInputEvent"
            if msg.isInput() then logDeepLink("input", msg.getInfo())
        else if msgType = "roAppMemoryNotificationEvent"
            print "[2048] memory warning: "; FormatJson(msg.getInfo())
        else if msgType = "roDeviceInfoEvent"
            print "[2048] device info event: "; FormatJson(msg.getInfo())
        end if
    end while
end sub

sub logDeepLink(source as string, a as dynamic)
    if type(a) = "roAssociativeArray" and a.contentId <> invalid
        print "[2048] "; source; " deep link contentId="; a.contentId; " mediaType="; a.mediaType; " (no content to open; showing the board)"
    end if
end sub
