-- HELLO!
--  No! I dont know how to make this run in cheat engine
--  You need to go  ctrl+alt+l and copy / paste this in.
--  itll start listening to the temp file as below
--  TELEPORT code taken from the popular  cheat engine tbale for dark souls remastered and
--  slightly retooled to work here.
--  Freeze / pause is just speed hack


-- TODO: How tf do we respawn asylum demon and reset it's health....
-- 


local commandFile = [[C:\temp\ce_commands.txt]]
local statusFile = [[C:\temp\ce_status.txt]]

function writeStatus(status)
    local file = io.open(statusFile, "w")
    if file then
        file:write(status)
        file:close()
    end
end

function teleportToCoords(x, y, z)
    print(string.format("Attempting teleport to: %.10f, %.10f, %.10f", x, y, z))
    
    local posAddrString = "[[[[[[BaseX]+68]+18]+28]+50]+20]+120"
    local posAddr = getAddress(posAddrString)
    
    if not posAddr then
        print("ERROR: Could not resolve position address")
        print("Make sure BaseX is registered in your table")
        return false
    end
    
    print(string.format("Writing to address: 0x%X", posAddr))
    writeFloat(posAddr, x)
    writeFloat(posAddr + 4, y)
    writeFloat(posAddr + 8, z)
    print("Teleport complete!")
    return true
end

function teleportToBytes(bytesX, bytesY, bytesZ)
    print("Attempting teleport using byte arrays")
    
    local posAddrString = "[[[[[[BaseX]+68]+18]+28]+50]+20]+120"
    local posAddr = getAddress(posAddrString)
    
    if not posAddr then
        print("ERROR: Could not resolve position address")
        return false
    end
    
    print(string.format("Writing bytes to address: 0x%X", posAddr))
    writeBytes(posAddr, bytesX)
    writeBytes(posAddr + 4, bytesY)
    writeBytes(posAddr + 8, bytesZ)
    print("Teleport complete!")
    return true
end

function getCurrentPosition()
    local posAddrString = "[[[[[[BaseX]+68]+18]+28]+50]+20]+120"
    local posAddr = getAddress(posAddrString)
    
    if posAddr then
        local x = readFloat(posAddr)
        local y = readFloat(posAddr + 4)
        local z = readFloat(posAddr + 8)
        
        local bytesX = readBytes(posAddr, 4, true)
        local bytesY = readBytes(posAddr + 4, 4, true)
        local bytesZ = readBytes(posAddr + 8, 4, true)
        
        return x, y, z, bytesX, bytesY, bytesZ
    end
    return nil
end

function checkCommands()
    local file = io.open(commandFile, "r")
    if file then
        local cmd = file:read("*all")
        file:close()
        os.remove(commandFile)
        
        cmd = cmd:match("^%s*(.-)%s*$")
        if cmd == "" then return end
        
        print("Received: " .. cmd)
        
        if cmd == "pause" then
            speedhack_setSpeed(0)
            print("Game paused")
            writeStatus("paused")
            
        elseif cmd == "resume" then
            speedhack_setSpeed(1)
            print("Game resumed")
            writeStatus("resumed")
            
        elseif cmd:match("^speed:") then
            local speed = tonumber(cmd:match("speed:(.+)"))
            if speed then
                speedhack_setSpeed(speed)
                print("Speed set to: " .. speed)
                writeStatus("speed:" .. speed)
            else
                writeStatus("error:invalid_speed")
            end
            
        elseif cmd:match("^teleport_bytes:") then
            local args = cmd:match("teleport_bytes:(.+)")
            
            if not args then
                writeStatus("error:invalid_teleport_command")
            else
                local xBytes, yBytes, zBytes = args:match("([^,]+),([^,]+),([^,]+)")
                
                if xBytes and yBytes and zBytes then
                    local function hexToBytes(hexStr)
                        local bytes = {}
                        for byte in hexStr:gmatch("%x%x") do
                            table.insert(bytes, tonumber(byte, 16))
                        end
                        return bytes
                    end
                    
                    local xByteTable = hexToBytes(xBytes)
                    local yByteTable = hexToBytes(yBytes)
                    local zByteTable = hexToBytes(zBytes)
                    
                    if #xByteTable == 4 and #yByteTable == 4 and #zByteTable == 4 then
                        if teleportToBytes(xByteTable, yByteTable, zByteTable) then
                            print("Teleported using byte arrays")
                            writeStatus("teleported")
                        else
                            writeStatus("error:teleport_failed")
                        end
                    else
                        writeStatus("error:invalid_byte_arrays")
                    end
                else
                    writeStatus("error:invalid_coordinates")
                end
            end
            
        elseif cmd:match("^teleport:") then
            local args = cmd:match("teleport:(.+)")
            
            if not args then
                writeStatus("error:invalid_teleport_command")
                print("Error: No arguments provided for teleport")
            else
                local x, y, z = args:match("([^,]+),([^,]+),([^,]+)")
                x, y, z = tonumber(x), tonumber(y), tonumber(z)
                if x and y and z then
                    if teleportToCoords(x, y, z) then
                        print(string.format("Teleported to: %.10f, %.10f, %.10f", x, y, z))
                        writeStatus("teleported")
                    else
                        writeStatus("error:teleport_failed")
                    end
                else
                    writeStatus("error:invalid_coordinates")
                    print("Error: Could not parse coordinates: " .. args)
                end
            end
            
        elseif cmd == "get_position" then
            print("Getting current position...")
            local x, y, z, bytesX, bytesY, bytesZ = getCurrentPosition()
            if x then
                local posStr = string.format("%.10f,%.10f,%.10f", x, y, z)
                
                local function bytesToHex(bytes)
                    local hex = {}
                    for i, byte in ipairs(bytes) do
                        table.insert(hex, string.format("%02X", byte))
                    end
                    return table.concat(hex, " ")
                end
                
                local hexX = bytesToHex(bytesX)
                local hexY = bytesToHex(bytesY)
                local hexZ = bytesToHex(bytesZ)
                
                print("Current position (floats): " .. posStr)
                print(string.format("Current position (bytes): %s,%s,%s", hexX, hexY, hexZ))
                writeStatus("position:" .. posStr .. "|" .. hexX .. "," .. hexY .. "," .. hexZ)
            else
                writeStatus("error:position_read_failed")
            end
            
        elseif cmd == "status" then
            local currentSpeed = speedhack_getSpeed()
            writeStatus("speed:" .. currentSpeed)
            print("Current speed: " .. currentSpeed)
            
        else
            print("Unknown command: " .. cmd)
            writeStatus("error:unknown_command")
        end
    end
end

if commandTimer then
    commandTimer.destroy()
    commandTimer = nil
end

commandTimer = createTimer(nil)
commandTimer.Interval = 50
commandTimer.OnTimer = checkCommands



writeStatus("ready")