sub init()
    m.top.functionName = "saveLoop"
end sub

sub saveLoop()
    reg = CreateObject("roRegistrySection", "roku2048")
    port = CreateObject("roMessagePort")
    m.top.observeField("data", port)
    ' A snapshot may have been set before this thread started listening.
    last = writeState(reg, m.top.data, "")
    while true
        msg = wait(0, port)
        if type(msg) = "roSGNodeEvent" then last = writeState(reg, msg.getData(), last)
    end while
end sub

function writeState(reg as object, json as string, last as string) as string
    if json = "" or json = last then return last
    reg.Write("state", json)
    reg.Flush()
    return json
end function
