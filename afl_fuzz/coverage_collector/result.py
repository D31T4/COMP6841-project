from hashlib import md5
from typing import Union

def bitmap_size(bm: bytes) -> int:
    '''
    count no. of bits
    '''
    return 0 + sum(bool(b) for b in bm)

def to_bitmap(cov: list[int]) -> bytes:
    bm = bytearray(len(cov))

    for i, c in enumerate(cov):
        bm[i] = (1 << (c - 1)) if c else 0

    return bm

class CoverageResult:
    '''
    coverage result
    '''
    def __init__(self, args: bytes, cov: list[int], elapsed: int, exception: dict[str, str] = None):
        '''
        create result instance. score is not calculated here.
        '''
        cov = to_bitmap(cov)

        self.args = args
        self.cov_cksum = md5(cov).digest()
        self.bitmap_size = bitmap_size(cov)
        self.elapsed: int = elapsed
        self.exception = exception

        self.cov: Union[bytes, None] = cov
        self.cov_ref: int = 0
        
        self.handicap: int = 0
        self.depth: int = 0
        self.calibrated: bool = False
        self.fuzzed: bool = False
        self.favored: bool = False