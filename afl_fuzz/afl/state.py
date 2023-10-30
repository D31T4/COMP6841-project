from threading import Lock
from uuid import uuid4
import os
import random

from afl_fuzz.afl.queue import Queue
from afl_fuzz.coverage_collector.result import CoverageResult, bitmap_size
from afl_fuzz.coverage_collector.context import Context
from afl_fuzz.logger.base import ILogger, devNullLogger


class State:
    '''
    AFL state
    '''

    def __init__(
        self, 
        entry_point: str, 
        ctx_fname: str = None, 
        exception_logger: ILogger = None, 
        op_logger: ILogger = None, 
        n_buckets: int = 1024
    ):
        '''
        Arguments:
        ---
        - entry_point: entry point
        - ctx_fname: context filename. random generate one if `None`
        - exception_logger: exception logger
        - op_logger: operation logger
        - n_buckets: no. of trace buckets
        '''
        self.queue = Queue()
        self.queue_cycle: int = 0

        self.fuzzed_queue: Queue = Queue()

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

        # global coverage bitmap
        self.covered = bytearray(n_buckets)

        self.top_rated: list[CoverageResult] = [None] * self.n_buckets
        self.pending_favored: int = 0
        
        self.score_changed: bool = False

        self.should_splice: bool = False
        self.havoc_diff: int = 10

        self.coverage_updated: bool = False

    def use_ctx(self):
        '''
        write context file
        '''
        self.ctx.write(self.ctx_fname)

    def rm_ctx(self):
        '''
        delete context file
        '''
        os.path.exists(self.ctx_fname) and os.remove(self.ctx_fname)

    def update_coverage(self, cov: CoverageResult):
        '''
        update global coverage

        Arguments:
        ---
        - trace_bits: coverage bitmap

        Returns:
        ---
        - `True` if global coverage map changed. else `False`.
        '''
        changed: int = 0

        for i in range(self.n_buckets):
            covered = self.covered[i]
            new_covered = covered | cov.cov[i]

            if new_covered != covered:
                self.covered[i] = new_covered
                changed = 1 + int(not covered)
                self.coverage_updated = True

        if changed:
            self.op_logger.write(f'new area covered by input: {cov.arg_head()}')

            if cov.exception:
                self.exception_logger.write(f'new exception covered by input: {cov.arg_head()}')

        return changed

    @property
    def avg_total_cal_us(self):
        return self.total_calc_us / self.total_cal_cycles if self.total_cal_cycles > 0 else float('inf')
    
    @property
    def avg_bitmap_size(self):
        return self.total_bitmap_size / self.total_bitmap_entries if self.total_bitmap_entries > 0 else 0
    
    def sample(self):
        '''
        sample with uniform distribution
        '''
        l1 = len(self.queue)
        l2 = len(self.fuzzed_queue)

        if random.random() < l1 / (l1 + l2):
            return self.queue.sample()
        else:
            return self.fuzzed_queue.sample()
        
    @property
    def n_entries(self):
        return len(self.queue) + len(self.fuzzed_queue)
    
    def estimate_coverage(self):
        return bitmap_size(self.covered) / self.n_buckets
