from threading import Lock
from uuid import uuid4
import os

from .queue import Queue
from afl_fuzz.coverage_collector.result import CoverageResult
from afl_fuzz.coverage_collector.context import Context
from afl_fuzz.logger.base import ILogger, devNullLogger


class State:
    def __init__(self, entry_point: str, ctx_fname: str = None, exception_logger: ILogger = None, op_logger: ILogger = None, n_buckets: int = 1024):
        self.queue = Queue()
        self.queue_cycle: int = 0

        self.total_calc_us: int = 0
        self.total_cal_cycles: int = 0
        self.total_bitmap_size: int = 0
        self.total_bitmap_entries: int = 0
        self.lock = Lock()

        self.exception_logger = exception_logger or devNullLogger
        self.op_logger = op_logger or devNullLogger
        
        self.n_buckets: int = n_buckets

        # substring before .py
        self.entry_module: str = entry_point[:entry_point.rindex('.')]

        self.ctx = Context.create(n_buckets, entry_point)
        self.ctx_fname = ctx_fname or f'{uuid4()}.ctx'

        self.covered = bytearray(n_buckets)

        self.top_rated: list[CoverageResult] = [None] * self.n_buckets
        self.pending_favored: int = 0
        self.score_changed: bool = False

    def use_ctx(self):
        self.ctx.write(self.ctx_fname)

    def rm_ctx(self):
        os.path.exists(self.ctx_fname) and os.remove(self.ctx_fname)

    def update_coverage(self, trace_bits: bytes):
        changed: int = 0

        for i in range(self.n_buckets):
            covered = self.covered[i]
            new_covered = covered | trace_bits[i]

            if new_covered != covered:
                self.covered[i] = new_covered
                changed = 1 + int(not covered)

        return changed

    @property
    def avg_total_cal_us(self):
        return self.total_calc_us / self.total_cal_cycles if self.total_cal_cycles > 0 else float('inf')
    
    @property
    def avg_bitmap_size(self):
        return self.total_bitmap_size / self.total_bitmap_entries if self.total_bitmap_entries > 0 else 0
