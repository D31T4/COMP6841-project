from hashlib import md5
from typing import Union

def bitmap_size(bm: bytes) -> int:
    '''
    count no. of bits
    '''
    return 0 + sum(bool(b) for b in bm)

def to_bitmap(cov: list[int]) -> bytes:
    '''
    covert coverage output to bitmap
    '''
    bm = bytearray(len(cov))

    for i, c in enumerate(cov):
        bm[i] = (1 << (c - 1)) if c else 0

    return bm

def hash(bm: bytes) -> bytes:
    '''
    hash for computing checksum of trace bits
    '''
    # just take first 4-bytes of md5 lol
    return md5(bm).digest()[:4]

class CoverageResult:
    '''
    coverage result
    '''
    def __init__(self, args: bytes, cov: list[int] = None, elapsed: int = -1, exception: dict[str, str] = None):
        '''
        create result instance.

        Arguments:
        ---
        - args: input
        - cov: coverage
        - elapsed: run time
        - execption: exception if any
        '''
        if cov:
            cov = to_bitmap(cov)
            self.cov_cksum = hash(cov)
            self.bitmap_size = bitmap_size(cov)

        self.args = args

        self.elapsed: int = elapsed
        self.exception = exception

        self.cov: Union[bytes, None] = cov
        self.cov_ref: int = 0
        
        self.handicap: int = 0
        self.depth: int = 0
        self.calibrated: bool = False
        self.fuzzed: bool = False
        self.favored: bool = False
        self.trimmed: bool = False

    def arg_head(self) -> str:
        return self.args[:4].hex()