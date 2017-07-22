#######################################################################
#  The one wire CRC algorithm is derived from the OneWire.cpp Library
#  The latest version of this library may be found at:
#  http://www.pjrc.com/teensy/td_libs_OneWire.html
#######################################################################
def crc8(line):
    crc=0
    for i in range(len(line)):
        inbyte=line[i]
        for j in range(8):
            mix = (crc ^ inbyte) & 0x01
            crc >>= 1
            if (mix):
                crc ^= 0x8C
            inbyte >>= 1
    return crc
#######################################################################
