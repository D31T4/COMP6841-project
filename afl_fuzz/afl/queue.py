from collections import deque
from typing import Iterable
import random

from afl_fuzz.coverage_collector.result import CoverageResult

class Queue:
    '''
    double linked list. a deque wrapper.
    '''

    def __init__(self, items: Iterable[CoverageResult] = None):
        self._queue: deque[CoverageResult] = deque()

        for el in items or []:
            self.push(el)

    def __len__(self):
        return len(self._queue)
    
    def __bool__(self):
        return bool(self._queue)
    
    def __iter__(self):
        return self._queue.__iter__()

    def pop(self):
        '''
        pop item from queue
        '''
        out: CoverageResult = None

        if self._queue:
            out = self._queue.popleft()

        return out
    
    def push(self, item: CoverageResult):
        '''
        push item into queue
        '''
        self._queue.append(item)

    def clear(self):
        self._queue.clear()

    def sample(self):
        '''
        sample queue entries with uniform distribution
        '''
        if not self: return None
        
        pos = random.randrange(len(self))
        idx = 0

        for el in self:
            if idx == pos:
                return el

            idx += 1
    
