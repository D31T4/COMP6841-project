from typing import Iterable
from multiprocessing.pool import ThreadPool

from afl_fuzz.coverage_collector.process import collect
from afl_fuzz.coverage_collector.result import CoverageResult

from afl_fuzz.afl.state import State
from afl_fuzz.afl.score import update_bitmap_score

from afl_fuzz.afl.config import (
    EXEC_TIMEOUT, 
    CALIBRATE_SAMPLE_SIZE,
    TRIM_MIN_BYTES,
    TRIM_END_STEPS,
    TRIM_START_STEPS
)

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

            if cov.exception:
                state.on_exception(cov.args, cov.exception)

        except Exception as ex:
            state.exception_logger.write(f'failed to run due to an exception: {ex}')
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

        if cov.exception:
            state.on_exception(cov.args, cov.exception)
        
    except TimeoutError:
        return None
    
    cov.depth = depth + 1
    save_if_interesting(state, cov)
    return cov

def next_p2(val: int):
    ret: int = 1

    while val > ret:
        ret <<= 1

    return ret

def trim_case(state: State, path: CoverageResult):
    if len(path.args) < 5: return False
    
    # Select initial chunk len, starting with large steps
    len_p2 = next_p2(len(path.args))

    remove_len = max(len_p2 // TRIM_START_STEPS, TRIM_MIN_BYTES)

    # Continue until the number of steps gets too high or the stepover
    # gets too small.
    while remove_len >= max(len_p2 // TRIM_END_STEPS, TRIM_MIN_BYTES):
        remove_pos = remove_len

        trimmed: bool = False

        while remove_pos < len(path.args):
            trim_avail = min(remove_len, len(path.args) - remove_pos)

            out_buf = path.args[:remove_pos] + path.args[(path + trim_avail):]

            result: CoverageResult = collect(state.entry_module, state.ctx_fname, out_buf)
            if not result: return False

            # If the deletion had no impact on the trace, make it permanent. This
            # isn't perfect for variable-path inputs, but we're just making a
            # best-effort pass, so it's not a big deal if we end up with false
            # negatives every now and then.
            if result.cov_cksum == path.cov_cksum:
                path.cov = result.cov
                path.bitmap_size = result.bitmap_size
                path.elapsed = result.elapsed
                path.args = result.args
                path.exception = result.exception

                len_p2 = next_p2(len(path.args))

                trimmed = True
            else:
                remove_pos += remove_len

        remove_len >>= 1

        if trimmed: 
            update_bitmap_score(state, path)

        return trimmed