'''
mutation
'''
from typing import Callable

from afl_fuzz.afl.config import (
    ARITH_MAX, 
    HAVOC_STACK_POW2,
    HAVOC_BLK_SM, HAVOC_BLK_MD, HAVOC_BLK_LG, HAVOC_BLK_XL,
    MAX_FILE
)

import random

def swap16(b: int) -> int:
    '''
    reverse 2 bytes

    Arguments:
    ---
    - b: 2-bytes in integer representation

    Returns:
    ---
    - reversed bytes
    '''
    return ((b << 8) & 0xff00) | ((b >> 8) & 0x00ff)

def swap32(b: int) -> int:
    '''
    reverse 4 bytes

    https://stackoverflow.com/a/2182184

    Arguments:
    ---
    - b: 4-bytes in integer representation

    Returns:
    ---
    - reversed bytes
    '''
    return ((b >> 24) & 0xff)\
            | ((b << 8) & 0xff0000)\
            | ((b >> 8) & 0xff00)\
            | ((b << 24) & 0xff000000)

def flip_bit(a: bytearray, idx: int) -> int:
    '''
    flip one bit in byte sequence in place

    Arguments:
    ---
    - a: bytes
    - b: bit index

    Returns:
    ---
    - reference to byte sequence
    '''
    a[idx >> 3] ^= (128 >> (idx & 7))

def could_be_bitflip(x: int) -> bool:
    sh = 0

    if not x: return True

    # shift left until first bit set
    while not (x & 1):
        sh += 1
        x >>= 1

    # 1-, 2-, and 4-bit patterns are ok anywhere
    if x == 1 or x == 3 or x == 15: return True

    # 8-, 16-, and 32-bit patterns are ok only if shift factor
    # is divisible by 8, since that's the stepover for these ops
    if sh & 7: return False
    
    
    if x == 0xff or x == 0xffff or x == 0xffffffff:
        return True
    
    return False

def choose_block_len(limit: int) -> int:
    '''
    randomize mutation block size

    Arguments:
    ---
    - limit: max block size

    Returns:
    ---
    - block size
    '''
    # TODO: choose rlim based on elapsed and queue_cycle
    rlim: int = 1

    rand = random.randint(0, rlim)

    if rand == 0:
        min_val = 1
        max_val = HAVOC_BLK_SM
    elif rand == 1:
        min_val = HAVOC_BLK_SM
        max_val = HAVOC_BLK_MD
    else:
        if random.random() > 0.1:
            min_val = HAVOC_BLK_MD
            max_val = HAVOC_BLK_LG
        else:
            min_val = HAVOC_BLK_LG
            max_val = HAVOC_BLK_XL

    if min_val >= limit:
        min_val = 1

    max_val = min(max_val, limit)

    return min_val + random.randint(0, max_val - min_val)


def generate_bitflips(buffer: bytearray, window: int):
    '''
    generate bit-flips

    Arguments:
    ---
    - buffer
    - window: window size
    '''
    for i in range((len(buffer) << 3) - window + 1):
        for offset in range(window):
            flip_bit(buffer, i + offset)

        yield i, buffer

        for offset in range(window):
            flip_bit(buffer, i + offset)

def generate_byteflips(buffer: bytearray, window: int, should_skip: Callable[[int], bool] = None):
    '''
    generate byte-flips in place

    Arguments:
    ---
    - buffer: bytes
    - window: sliding window size
    '''
    for i in range(len(buffer) - window + 1):
        if should_skip and should_skip(i):
            continue

        for offset in range(window):
            buffer[i + offset] ^= 0xff

        yield i, buffer

        for offset in range(window):
            buffer[i + offset] ^= 0xff

def generate_arith8(buffer: bytearray, should_skip: Callable[[int], bool] = None):
    '''
    generate arith 8/8 mutations in place
    '''
    for i in range(len(buffer)):
        orig = buffer[i]

        if should_skip and should_skip(i):
            continue

        for offset in range(1, ARITH_MAX + 1):
            r = orig ^ ((orig + offset) & 0xff)

            if not could_be_bitflip(r):
                buffer[i] = (orig + offset) & 0xff
                yield buffer

            r = orig ^ ((orig - offset) & 0xff)

            if not could_be_bitflip(r):
                buffer[i] = (orig - offset) & 0xff
                yield buffer
                
        buffer[i] = orig

def generate_arith16(buffer: bytearray, should_skip: Callable[[int], bool] = None):
    '''
    generate arith 16/8 mutations in place
    '''
    for i in range(len(buffer) - 1):
        orig = (buffer[i] << 8) | buffer[i + 1]

        if should_skip and should_skip(i):
            continue

        for offset in range(1, ARITH_MAX + 1):
            r1 = orig ^ ((orig + offset) & 0xffff)
            r2 = orig ^ ((orig - offset) & 0xffff)
            r3 = orig ^ swap16(swap16(orig) + offset)
            r4 = orig ^ swap16(swap16(orig) - offset)

            if (orig & 0xff) + offset > 0xff and not could_be_bitflip(r1):
                new_val = orig + offset
                buffer[i] = (new_val & 0xff00) >> 8
                buffer[i + 1] = new_val & 0x00ff
                yield buffer


            if (orig & 0xff) < offset and not could_be_bitflip(r2):
                new_val = orig - offset
                buffer[i] = (new_val & 0xff00) >> 8
                buffer[i + 1] = new_val & 0x00ff
                yield buffer


            if ((orig >> 8) + offset) > 0xff and not could_be_bitflip(r3):
                new_val = swap16(swap16(orig) + offset)
                buffer[i] = (new_val & 0xff00) >> 8
                buffer[i + 1] = new_val & 0x00ff
                yield buffer


            if (orig >> 8) < offset and not could_be_bitflip(r4):
                new_val = swap16(swap16(orig) - offset)
                buffer[i] = (new_val & 0xff00) >> 8
                buffer[i + 1] = new_val & 0x00ff
                yield buffer

        buffer[i] = (orig & 0xff00) >> 8
        buffer[i + 1] = orig & 0x00ff

def generate_arith32(buffer: bytearray, should_skip: bool = None):
    '''
    generate arith 32/8 mutations in place

    Arguments:
    ---
    - buffer
    - should_skip
    '''
    for i in range(len(buffer) - 3):
        orig = (buffer[i] << 24) | (buffer[i + 1] << 16) | (buffer[i + 2] << 8) | buffer[i + 3]

        if should_skip and should_skip(i):
            continue

        for offset in range(1, ARITH_MAX + 1):
            r1 = orig ^ ((orig + offset) & 0xffffffff)
            r2 = orig ^ ((orig - offset) & 0xffffffff)
            r3 = orig ^ swap32(swap32(orig) + offset)
            r4 = orig ^ swap32(swap32(orig) - offset)

            if (orig & 0xffff) + offset > 0xffff and not could_be_bitflip(r1):
                new_val = orig + offset
                buffer[i] = (new_val & 0xff000000) >> 24
                buffer[i + 1] = (new_val & 0x00ff0000) >> 16
                buffer[i + 2] = (new_val & 0x0000ff00) >> 8
                buffer[i + 3] = new_val & 0x000000ff
                
                yield buffer


            if (orig & 0xffff) < offset and not could_be_bitflip(r2):
                new_val = orig - offset
                buffer[i] = (new_val & 0xff000000) >> 24
                buffer[i + 1] = (new_val & 0x00ff0000) >> 16
                buffer[i + 2] = (new_val & 0x0000ff00) >> 8
                buffer[i + 3] = new_val & 0x000000ff

                yield buffer

            if (swap32(orig) & 0xffff) + offset > 0xffff and not could_be_bitflip(r3):
                new_val = swap32(swap32(orig) + offset)
                buffer[i] = (new_val & 0xff000000) >> 24
                buffer[i + 1] = (new_val & 0x00ff0000) >> 16
                buffer[i + 2] = (new_val & 0x0000ff00) >> 8
                buffer[i + 3] = new_val & 0x000000ff

                yield buffer

            if (swap32(orig) & 0xffff) < offset and not could_be_bitflip(r4):
                new_val = swap32(swap32(orig) - offset)
                buffer[i] = (new_val & 0xff000000) >> 24
                buffer[i + 1] = (new_val & 0x00ff0000) >> 16
                buffer[i + 2] = (new_val & 0x0000ff00) >> 8
                buffer[i + 3] = new_val & 0x000000ff

                yield buffer

def havoc(buffer: bytearray):
    '''
    random mutations

    Arguments:
    ---
    - buffer: byte seq
    '''
    for _ in range(1 << 1 + random.randint(1, HAVOC_STACK_POW2)):
        mut_type = random.randint(0, 14)
        n = len(buffer)


        if mut_type == 0:
            # flip bit somewhere
            flip_bit(buffer, random.randrange(n << 3))
        elif mut_type == 1:
            # TODO: set byte to interesting value
            pass
        elif mut_type == 2:
            # TODO: set byte to interesting value, random endian
            pass
        elif mut_type == 3:
            # TODO: set dword to interesting value, random endian
            pass
        elif mut_type == 4 or mut_type == 5:
            # case 4: subtract from byte
            # case 5: add to byte
            idx = random.randrange(n)
            offset = random.randint(0, ARITH_MAX)
            factor = 1 if mut_type == 4 else -1

            buffer[idx] = (buffer[idx] + factor * offset) & 0xff
        elif mut_type == 6 or mut_type == 7:
            # case 6: subtract from word, random endian
            # case 7: add to word, random endian
            if n < 2: continue

            idx = random.randint(0, n - 2)
            old_val = (buffer[idx] << 8) | buffer[idx + 1]
            offset = random.randint(1, ARITH_MAX)
            factor = 1 if mut_type == 6 else -1

            if random.random() > 0.5:
                new_val = old_val + factor * offset
            else:
                new_val = swap16(swap16(old_val) + factor * offset)

            buffer[idx] = (new_val & 0xff00) >> 8
            buffer[idx + 1] = new_val & 0x00ff

        elif mut_type == 8 or mut_type == 9:
            # case 8: subtract from dword, random endian
            # case 9: add to dword, random endian
            if n < 4: continue

            idx = random.randint(0, n - 4)
            old_val = (buffer[idx] << 24) | (buffer[idx + 1] << 16) | (buffer[idx + 2] << 8) | buffer[idx + 3]
            offset = random.randint(1, ARITH_MAX)
            factor = 1 if mut_type == 8 else -1

            if random.random() > 0.5:
                new_val = old_val + factor * offset
            else:
                new_val = swap32(swap32(old_val) + factor * offset)

            buffer[idx] = (new_val & 0xff000000) >> 24
            buffer[idx + 1] = (new_val & 0x00ff0000) >> 16
            buffer[idx + 2] = (new_val & 0x0000ff00) >> 8
            buffer[idx + 3] = new_val & 0x000000ff 

        elif mut_type == 10:
            # random substitution
            buffer[random.randrange(n)] ^= random.randint(1, 255)

        elif mut_type == 11 or mut_type == 12:
            # case 11, 12: delete bytes
            # Delete bytes. We're making this a bit more likely
            # than insertion (the next option) in hopes of keeping
            # files reasonably small.
            if n < 2: continue

            del_len = choose_block_len(n - 1)
            del_from = random.randrange(n - del_len)

            buffer = buffer[:del_from] + buffer[(del_from + del_len):]

        elif mut_type == 13:
            # case 13: insert
            if len(buffer) + HAVOC_BLK_XL < MAX_FILE:
                # Clone bytes (75%) or insert a block of constant bytes (25%).
                actually_clone = random.randrange(4)
                
                if actually_clone:
                    clone_len = choose_block_len(n)
                    clone_from = random.randint(0, n - clone_len)
                else:
                    clone_len = choose_block_len(HAVOC_BLK_XL)
                    clone_from = 0

                clone_to = random.randrange(n)

                if actually_clone:
                    buffer = buffer[:clone_to] + buffer[clone_from:(clone_from + clone_len)] + buffer[clone_to:]
                else:
                    chunk = bytearray(clone_len)
                    val = random.randint(0x00, 0xff) if random.randint(0, 1) else buffer[random.randrange(len(buffer))]

                    for i in range(clone_len):
                        chunk[i] = val

                    buffer = buffer[:clone_to] + chunk + buffer[clone_to:]

        elif mut_type == 14:
            # case 14: overwrite bytes with random chunk or fixed bytes
            # Overwrite bytes with a randomly selected chunk (75%) or fixed
            # bytes (25%).
            # TODO: not implemented
            if n < 2: continue

            # n - 1: prevent overwrite the entire block I guess
            copy_len = choose_block_len(n - 1)

            copy_from = random.randint(0, n - copy_len)
            copy_to = random.randint(0, n - copy_len)

            if random.random() > 0.75:
                if copy_from > copy_to:
                    # copy left to right
                    generator = range(copy_len)
                elif copy_from < copy_to:
                    # copy right to left
                    generator = range(copy_len - 1, -1, -1)
                else:
                    # no need to copy
                    continue

                for i in generator:
                    buffer[copy_to + i] = buffer[copy_from + i]

            else:
                if random.random() > 0.5:
                    sub_val = random.randint(0, 0xff)
                else:
                    sub_val = buffer[random.randrange(n)]

                for i in range(copy_to, copy_to + copy_len):
                    buffer[i] = sub_val
        # TODO: case 15: overwrite bytes with extras
        # TODO: case 16: insert extra

    return buffer

def locate_diffs(s1: bytearray, s2: bytearray):
    '''
    find diff region
    '''
    f_loc: int = -1
    l_loc: int = -1

    p1 = 0
    p2 = 0

    for pos in range(min(len(s1), len(s2))):
        if s1[p1] != s2[p2]:
            if f_loc == -1: f_loc = pos
            l_loc = pos

        p1 += 1
        p2 += 1

    return f_loc, l_loc

def splice_afl(target: bytearray, source: bytes) -> bytes:
    '''
    splice target **in place**. original implementation in AFL.

    Arguments:
    ---
    - target: target to be mutated
    - source: source gene

    Returns:
    ---
    - target ref
    '''
    f_loc, l_loc = locate_diffs(source, target)

    # Find a suitable splicing location, somewhere between the first and
    # the last differing byte. Bail out if the difference is just a single
    # byte or so.
    if f_loc < 0 or l_loc < 2 or l_loc == f_loc:
        return target

    split_at = random.randint(f_loc, l_loc)

    for i in range(split_at, min(len(source), len(target))):
        target[i] = source[i]

    return target

def splice(target: bytearray, source: bytes) -> bytes:
    '''
    splice target. choose first half from `target`, second half from `source`.
    '''
    t_split = random.randint(1, len(target))
    s_split = random.randint(0, len(source) - 1)

    return target[:t_split] + source[s_split:]