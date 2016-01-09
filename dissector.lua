-- trivial protocol example
-- declare our protocol
unifying_proto = Proto("unifying", "Logitech Unifying Receiver")

-- create a function to dissect it
function unifying_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "UNIFYING"
    local subtree = tree:add(trivial_proto,buffer(),"Unifying Protocol Data")
    subtree:add(buffer(0, 1),"Channel: " .. buffer(0, 1):uint())
    subtree:add(buffer(1, 5),"Address: " .. buffer(1, 5))
    subtree:add(buffer(6, 1),"Length: " .. buffer(6, 1):uint())
    subtree:add(buffer(7, 1),"PID: " .. buffer(7, 1):uint())
    subtree:add(buffer(8, 1),"NOACK: " .. buffer(8, 1):uint())
    length = buffer(6, 1):uint()
    subtree:add(buffer(41-length, length),"Payload: " .. buffer(41-length, length))
    subtree:add(buffer(41, 2),"CRC: " .. buffer(41, 2))
end

-- load the udp.port table
udp_table = DissectorTable.get("udp.port")
-- register our protocol to handle udp port 48222
udp_table:add(48222, unifying_proto)
