'''
mutation
'''

from typing import Generator
import random

def swap32(b: int) -> int:
    '''
    https://stackoverflow.com/a/2182184
    '''
    return ((b >> 24) & 0xff)\
            | ((b << 8) & 0xff0000)\
            | ((b >> 8) & 0xff00)\
            | ((b << 24) & 0xff000000)

def get_mutations(path: bytearray) -> Generator[bytearray]:
    x = path[0]

def splice(path1: bytearray, path2: bytearray) -> bytearray:
    pass