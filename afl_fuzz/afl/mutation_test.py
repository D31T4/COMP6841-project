'''
unit test for mutation.py
'''

import unittest

from mutation import (
    flip_bit, 
    swap16, swap32,
    splice,
    generate_arith8,
    generate_arith16,
    generate_arith32,
    generate_bitflips,
    generate_byteflips
)

class flip_bit_test(unittest.TestCase):
    def test(self):
        byt = bytearray([0xff, 0xff, 0xff, 0x10])
        flip_bit(byt, 27)
        self.assertEqual(bytes(byt), bytes([0xff, 0xff, 0xff, 0x00]))

        byt = bytearray([0xff, 0xff, 0xff, 0x00])
        flip_bit(byt, 27)
        self.assertEqual(bytes(byt), bytes([0xff, 0xff, 0xff, 0x10]))

class swap16_test(unittest.TestCase):
    def test(self):
        self.assertEqual(0xff00, swap16(0x00ff))
        self.assertEqual(0x00ff, swap16(0xff00))
        self.assertEqual(0x0100, swap16(0x0001))

class swap32_test(unittest.TestCase):
    def test(self):
        self.assertEqual(0xff000000, swap32(0x000000ff))
        self.assertEqual(0x000000ff, swap32(0xff000000))
        self.assertEqual(0x00010000, swap32(0x00000100))

class splice_test(unittest.TestCase):
    def test(self):
        splice(bytearray([0x00, 0x00]), bytes([0xff, 0xff]))

class generate_arith8_test(unittest.TestCase):
    def test(self):
        for _ in generate_arith8(bytearray([0x00])):
            continue

class generate_arith16_test(unittest.TestCase):
    def test(self):
        for _ in generate_arith16(bytearray([0x00, 0x00])):
            continue

class generate_arith32_test(unittest.TestCase):
    def test(self):
        for _ in generate_arith32(bytearray([0x00, 0x00, 0x00, 0x00])):
            continue

class generate_bitflips_test(unittest.TestCase):
    def test(self):
        for offset in [1, 2, 4]:
            for _ in generate_bitflips(bytearray([0x00, 0x00, 0x00, 0x00]), offset):
                continue

class generate_byteflips_test(unittest.TestCase):
    def test(self):
        x = bytearray([0x00, 0x00, 0x00, 0x00])

        for offset in [1, 2, 4]:
            for _ in generate_byteflips(x, offset):
                continue

if __name__ == '__main__':
    unittest.main()