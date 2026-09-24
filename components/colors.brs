' Tile palette shared by Tile (tile art) and GameScene (merge burst rings).
function tileColors(v as integer) as object
    dark = "0x776E65FF"
    light = "0xF9F6F2FF"
    if v = 2 then return ["0xEEE4DAFF", dark]
    if v = 4 then return ["0xEDE0C8FF", dark]
    if v = 8 then return ["0xF2B179FF", light]
    if v = 16 then return ["0xF59563FF", light]
    if v = 32 then return ["0xF67C5FFF", light]
    if v = 64 then return ["0xF65E3BFF", light]
    if v = 128 then return ["0xEDCF72FF", light]
    if v = 256 then return ["0xEDCC61FF", light]
    if v = 512 then return ["0xEDC850FF", light]
    if v = 1024 then return ["0xEDC53FFF", light]
    if v = 2048 then return ["0xEDC22EFF", light]
    return ["0x3C3A32FF", light]
end function
