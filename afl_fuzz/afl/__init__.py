'''
main fuzzing logic
'''
from typing import Iterable, Callable
import time
from multiprocessing.pool import ThreadPool

from afl_fuzz.logger.base import ILogger

from afl_fuzz.afl.state import State
from afl_fuzz.afl.config import TRACE_BUCKETS
from afl_fuzz.afl.exec import dryrun
from afl_fuzz.afl.fuzz_one import fuzz_one
from afl_fuzz.afl.score import cull_queue

def fuzz(
    entry: str, 
    seed: Iterable[bytes], 
    exception_logger: ILogger = None, 
    op_logger: ILogger = None, 
    max_elpased: int = float('inf'), 
    max_cycles: int = float('inf'), 
    n_workers: int = 1,
    on_exception: Callable[[bytes, dict[str, str]], None] = None
):
    '''
    main fuzz loop

    Arguments:
    ---
    - entry: entry point
    - seed: input seed
    - exception_logger: exception logger
    - op_logger: operation logger
    - max_elapsed: elapsed time
    - max_cycles: max fuzz cycles
    - n_workers: no. of worker threads
    '''
    afl = State(
        entry, 
        n_buckets=TRACE_BUCKETS, 
        exception_logger=exception_logger, 
        op_logger=op_logger, 
        on_exception=on_exception
    )
    
    afl.use_ctx()

    pool: ThreadPool = None

    try:
        dryrun(afl, seed, n_workers=n_workers)

        start = time.time()

        def map(_):
            with afl.lock:
                entry = afl.queue.pop()

            fuzz_one(afl, entry)

            with afl.lock:
                afl.fuzzed_queue.push(entry)

        afl.coverage_updated = True
        afl.should_splice = False

        while (time.time() - start < max_elpased) and afl.queue_cycle < max_cycles:
            # fuzz loop
            cull_queue(afl)

            afl.op_logger.write(f'begin fuzz cycle = {afl.queue_cycle}')

            if n_workers == 1:
                for i in range(len(afl.queue)):
                    map(i)
            else:
                pool = ThreadPool(n_workers)
                pool.imap_unordered(map, range(len(afl.queue)))
                pool.close()
                pool.join()
                pool = None


            afl.should_splice = not afl.coverage_updated
            afl.coverage_updated = False

            # show stats
            afl.op_logger.write(f'completed fuzz cycle = {afl.queue_cycle}')
            afl.queue_cycle += 1

            print('=====')
            print(f'elapsed: {time.time() - start}')
            print(f'estimated coverage: {afl.estimate_coverage()}')
            print('=====')

    finally:
        afl.rm_ctx()
        pool and pool.close()