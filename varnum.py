# Number of LSBs to check, Value to check against, Number of bytes to follow
table = (
        (1, 0, 0),
        (2, 1, 1),
        (3, 3, 2),
        (4, 7, 3),
        (5, 0xf, 4),
        (8, 0x1f, 5),
        (8, 0x3f, 6),
        (8, 0x5f, 7),
        (8, 0x7f, 8),
        (8, 0x9f, 10),
        (8, 0xbf, 12),
        (8, 0xdf, 14),
        (8, 0xff, 16))

"""Write number to f as a varnum."""
def write(f, number):
    for marker_length, marker_value, extra_bytes in table:
        max_number = 1 << (8 - marker_length + extra_bytes * 8)
        if number < max_number:
            break
    else:
        raise ValueError

    varnum = marker_value | (number << marker_length)
    if varnum == 0:
        f.write(b"\0")
    else:
        while varnum != 0:
            f.write(bytes([varnum & 0xff]))
            varnum >>= 8

"""Write a varnum from f."""
def read(f):
    byte = ord(f.read(1))
    for marker_length, marker_value, extra_bytes in table:
        if (byte & ((1<< marker_length)-1)) == marker_value:
            break
    else:
        raise ValueError

    varnum = byte >> marker_length
    varlen = 8 - marker_length
    for _ in range(extra_bytes):
        byte = ord(f.read(1))
        varnum |= byte << varlen
        varlen += 8
    return varnum

if __name__ == '__main__':
    import unittest
    import io

    class TestVarNum(unittest.TestCase):
        cases = (
                (0, bytes([0])),
                (42, bytes([84])),
                (1234, bytes([0x49, 0x13])),
                (8675309, bytes([0xd7, 0xfe, 0x45, 0x08])),
                (0x01020304050607080910111213141516,
                    b'\xff\x16\x15\x14\x13\x12\x11\x10\t\x08\x07\x06\x05\x04\x03\x02\x01')
                )

        def testWrite(self):
            for varnum, binary in self.cases:
                b = io.BytesIO()
                write(b, varnum)
                self.assertEqual(b.getbuffer(), binary)

        def testRead(self):
            for varnum, binary in self.cases:
                b = io.BytesIO(binary)
                self.assertEqual(read(b), varnum)

    unittest.main()
