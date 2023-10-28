from collections import deque

from afl_fuzz.coverage_collector.result import CoverageResult

class Queue:
    def __init__(self):
        self._queue: deque[CoverageResult] = deque()

    def __len__(self):
        return len(self._queue)
    
    def __bool__(self):
        return bool(self._queue)
    
    def __iter__(self):
        return self._queue.__iter__()

    def pop(self):
        out: CoverageResult = None

        if self._queue:
            out = self._queue.popleft()

        return out
    
    def push(self, item: CoverageResult):
        self._queue.append(item)
    
