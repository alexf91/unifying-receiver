-- trivial protocol example
-- declare our protocol
unifying_proto = Proto("unifying", "Logitech Unifying Receiver")

chan_f = ProtoField.int8("unifying.chan", "Channel", base.DEC)
addr_f = ProtoField.string("unifying.addr", "Address")
pid_f  = ProtoField.int8("unifying.pid",  "PID", base.DEC)
nack_f = ProtoField.int8("unifying.nack", "NACK", base.DEC)
len_f  = ProtoField.int8("unifying.len",  "Length", base.DEC)
pld_f  = ProtoField.string("unifying.pld",  "Payload")
crc_f  = ProtoField.string("unifying.crc",  "CRC", base.HEX)

unifying_proto.fields = {chan_f, addr_f, pid_f, nack_f, len_f, pld_f, crc_f}

function buffer_to_hex(buffer)
    hexstr = ""
    for i=0, buffer:len()-1 do
        b = buffer(i, 1):uint()
        hexstr = hexstr .. string.format("%02X", b)
    end

    return hexstr
end


-- create a function to dissect it
function unifying_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "UNIFYING"

    local subtree = tree:add(unifying_proto, buffer(), "Unifying Receiver Frame")

    local channel = buffer(0, 1):uint()
    subtree:add(chan_f, channel)

    local address = buffer_to_hex(buffer(1, 5))
    subtree:add(addr_f, address)

    local pid = buffer(6, 1):uint()
    subtree:add(pid_f, pid)

    local noack = buffer(7, 1):uint()
    subtree:add(nack_f, noack)

    local len = buffer:len() - 1 - 5 - 1 - 1 - 2
    subtree:add(len_f, len)
    subtree:add(pld_f, buffer_to_hex(buffer(8, len)))

    local crc = buffer_to_hex(buffer(8+len, 2))
    subtree:add(crc_f, crc)
end
