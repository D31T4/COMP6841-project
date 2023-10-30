from typing import Iterable
from multiprocessing.pool import ThreadPool

from afl_fuzz.coverage_collector.process import collect
from afl_fuzz.coverage_collector.result import CoverageResult

from afl_fuzz.afl.state import State
from afl_fuzz.afl.score import update_bitmap_score
from afl_fuzz.afl.config import EXEC_TIMEOUT, CALIBRATE_SAMPLE_SIZE

def calibrate(state: State, path: CoverageResult) -> CoverageResult:
    '''
    calibrate case
    '''
    # we assume cov is already in queue
    state.op_logger.write('begin calibration')

    total_bitmap_size = 0
    total_calc_us = 0

    for _ in range(CALIBRATE_SAMPLE_SIZE):
        try:
            cov = collect(state.entry_module, state.ctx_fname, path.args, timeout=EXEC_TIMEOUT)
        except:
            state.exception_logger.write(f'failed to run exception')
            return None

        total_bitmap_size += cov.bitmap_size
        total_calc_us += cov.elapsed

    path.bitmap_size = cov.bitmap_size
    path.cov_cksum = cov.cov_cksum
    path.cov = cov.cov
    path.exception = cov.exception

    path.elapsed = total_calc_us // CALIBRATE_SAMPLE_SIZE
    path.calibrated = True

    with state.lock:
        state.total_bitmap_size += total_bitmap_size
        state.total_calc_us += total_calc_us
        state.total_cal_cycles += CALIBRATE_SAMPLE_SIZE
        state.total_bitmap_entries += CALIBRATE_SAMPLE_SIZE

        update_bitmap_score(state, path)

    state.op_logger.write('calibrate completed')

    return path


def dryrun(state: State, paths: Iterable[bytes], n_workers: int):
    '''
    run test cases

    Arguments:
    ---
    - state: afl state
    - paths: inputs
    - n_workers: no. of workers
    '''
    for p in paths:
        state.queue.push(CoverageResult(p))

    state.score_changed = True

    def run(_):
        with state.lock:
            p = state.queue.pop()

        calibrate(state, p)

        with state.lock:
            state.update_coverage(p)
            p.cov = None

            state.fuzzed_queue.push(p)

    if n_workers == 1:
        for i in range(len(state.queue)):
            run(i)
    else:
        tp = ThreadPool(n_workers)
        tp.imap_unordered(run, range(len(state.queue)))
        tp.close()
        tp.join()

    assert bool(state.fuzzed_queue)

    state.op_logger.write('dryrun completed')
    
def save_if_interesting(state: State, cov: CoverageResult):
    '''
    save if interesting

    Arguments:
    ---
    - state: afl state
    - cov: coverage result
    '''
    assert cov.cov

    if not state.update_coverage(cov):
        return False
    
    cov.handicap = state.queue_cycle + 1
    state.queue.push(cov)

    try:
        calibrate(state, cov)
        cov.cov = None
    except Exception as ex:
        state.op_logger.write(f'Failed to calibrate path due to {ex}')

    return True

def fuzz_arg(state: State, arg: bytes, depth: int = 0):
    '''
    fuzz with input

    Arguments:
    ---
    - state: afl state
    - arg: input
    - depth: depth (or generation)
    '''
    try:
        cov: CoverageResult = collect(state.entry_module, state.ctx_fname, arg, timeout=EXEC_TIMEOUT)
    except TimeoutError:
        return None
    
    cov.depth = depth + 1
    save_if_interesting(state, cov)
    return cov
