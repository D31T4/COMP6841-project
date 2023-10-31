'''
simulated buffer overflow vulnerability
'''

class IamAdmin(Exception):
    pass

class ItsJoever(Exception):
    pass

class SegmentationFault(Exception):
    pass

def secret(*_):
    raise ItsJoever()

def reject(*_):
    print('access denied')

symbol_table: dict[int, any] = {
    0x50: reject,
    0x54: secret
}

buffer_len = 100

callstack = bytearray([
    0x50, # 1-byte func pointer
    0x00  # is_admin: a bool flag indicating user is admin
]) + bytearray(buffer_len) # buffer

func_var = 0
is_admin_ptr = 1
buffer_ptr = len(callstack) - 1

def main(args: bytes):
    # fill buffer
    for i in range(len(args)):
        callstack[buffer_ptr - i] = args[i]

        # index out of range
        if buffer_ptr - i < 0:
            raise SegmentationFault()

    if int.from_bytes(callstack[is_admin_ptr:(is_admin_ptr + 1)], 'little'):
        raise IamAdmin()
    else:
        fp = int.from_bytes(callstack[func_var:(func_var + 1)], 'little')
        symbol_table[fp]()