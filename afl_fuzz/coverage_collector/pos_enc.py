from coverage.parser import PythonParser
from coverage.config import DEFAULT_EXCLUDE
from coverage.misc import join_regex
from typing import Iterable
import random

# max 4-byte unsigned int
MAX_INT = 2 ** 32 - 1

def randint():
    '''
    generate random 4-byte integer
    '''
    return random.randint(0, MAX_INT)

def to_binned(val: int):
    '''
    convert to binned value

    Arguments:
    ---
    - val: value

    Returns:
    ---
    - binned value
    '''
    if val >= 4 and val <= 7:
        return 4
    elif val >= 8 and val <= 15:
        return 5
    elif val >= 16 and val <= 31:
        return 6
    elif val >= 32 and val <= 127:
        return 7
    elif val >= 128:
        return 8
    else:
        return val

class Hitcount:
    '''
    Approximated branch hitcount
    '''
    def __init__(self, n_buckets: int):
        '''
        Arguments:
        ---
        - n_buckets: no. of buckets
        '''
        self._n = n_buckets
        self._buckets = [0] * n_buckets

    def add(self, s: int, t: int):
        '''
        add edge s->t

        Arguments:
        ---
        - s: source
        - t: target
        '''
        hash = (s ^ t) % self._n
        self._buckets[hash] = min(self._buckets[hash] + 1, 128)

    def get_binned(self) -> list[int]:
        '''
        get binned hitcounts

        Returns:
        ---
        - binned hitcounts
        '''
        out: list[int] = self._buckets[:]

        for i in range(self._n):
            out[i] = to_binned(out[i])

        return out
            
def get_positional_encoding(files: Iterable[str]):
    '''
    get positional encodings

    Arguments:
    ---
    - files to be marked

    Returns:
    ---
    - map: filename => (lineno => marker)
    '''
    enc: dict[str, dict[int, int]] = dict()
    exclude_re = join_regex(DEFAULT_EXCLUDE[:])
    
    for f in files:
        p = PythonParser(filename=f, exclude=exclude_re)
        p.parse_source()

        pe = dict()
        enc[f] = pe

        pe[-1] = randint()

        for s, t in p.arcs():
            s = abs(s)
            t = abs(t)

            if s not in pe:
                pe[s] = randint()

            if t not in pe:
                pe[t] = randint()

    return enc
    