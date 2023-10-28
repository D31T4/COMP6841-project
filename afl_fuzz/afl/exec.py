from typing import Iterable
from multiprocessing.pool import ThreadPool

from afl_fuzz.coverage_collector.process import collect
from afl_fuzz.coverage_collector.result import CoverageResult

from .state import State
from .score import update_bitmap_score, calculate_score
from .config import EXEC_TIMEOUT, CALIBRATE_SAMPLE_SIZE

def calibrate(state: State, args: bytes, handicap: int) -> CoverageResult:
    total_bitmap_size = 0
    total_calc_us = 0

    for _ in range(CALIBRATE_SAMPLE_SIZE):
        cov = collect(state.entry_module, state.ctx_fname, args, timeout=EXEC_TIMEOUT)

        # abort if exception
        if cov.exception:
            state.exception_logger.write(f'Exception found: {cov.exception}')
            return None

        total_bitmap_size += cov.bitmap_size
        total_calc_us += cov.elapsed

    with state.lock:
        state.total_bitmap_size += total_bitmap_size
        state.total_calc_us += total_calc_us
        state.total_cal_cycles += CALIBRATE_SAMPLE_SIZE
        state.total_bitmap_entries += CALIBRATE_SAMPLE_SIZE

        state.queue.push(args)

        update_bitmap_score(state, cov)

    cov.elapsed = total_calc_us // CALIBRATE_SAMPLE_SIZE
    cov.cov = None
    cov.handicap = handicap
    cov.calibrated = True

    return cov


def dryrun(state: State, paths: Iterable[bytes], n_workers: int = 1):
    '''
    run test cases
    '''
    pool = ThreadPool(n_workers)

    def run(path: bytes):
        try:
            calibrate(state, path, handicap=0)
        except Exception as ex:
            state.exception_logger.write(f'failed to run exception')

    pool.map(run, paths)
    pool.close()
    pool.join()

    assert bool(state.queue)
    
def save_if_interesting(state: State, cov: CoverageResult):
    assert cov.cov

    if not state.update_coverage(cov.cov):
        return False
    
    if not cov.exception:
        try:
            cov = calibrate(state, cov.args, state.queue_cycle - 1)
            state.queue.push(cov)
        except Exception as ex:
            state.op_logger.write(f'Failed to calibrate path due to {ex}')

    return True

def fuzz_arg(state: State, arg: bytes):
    try:
        cov = collect(arg, state.ctx_fname, timeout=EXEC_TIMEOUT)
    except:
        return
    
    save_if_interesting(state, cov)
