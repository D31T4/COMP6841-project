from afl_fuzz.afl.exec import fuzz_arg, calibrate
from afl_fuzz.afl.score import calculate_score

from afl_fuzz.afl.mutation import (
    generate_bitflips, 
    generate_byteflips, 
    generate_arith8, 
    generate_arith16, 
    generate_arith32,
    havoc,
    splice
)

from afl_fuzz.afl.config import (
    SKIP_FUZZ_PROB, 
    SKIP_NFAV_NEW_PROB, 
    SKIP_NFAV_OLD_PROB, 
    SPLICE_CYCLES, 
    HAVOC_CYCLES_INIT, 
    HAVOC_CYCLES, 
    SPLICE_HAVOC, 
    HAVOC_MIN,
    SKIP_DETERMINISTIC
)

from afl_fuzz.coverage_collector.result import CoverageResult
from afl_fuzz.afl.state import State

import random

def fuzz_one(state: State, path: CoverageResult):
    '''
    fuzz one

    Arguments:
    ---
    - state: afl state
    - path: coverage result
    '''
    def done():
        path.fuzzed = True

        if path.favored:
            state.pending_favored -= 1

        state.op_logger.write('fuzz_one completed')

        return True
    
    def skip():
        state.op_logger.write('fuzz_one skipped')
        return False
    
    if state.pending_favored:
        # If we have any favored, non-fuzzed new arrivals in the queue,
        # possibly skip to them at the expense of already-fuzzed or non-favored
        # cases.
        if (path.fuzzed or not path.favored) and random.random() < SKIP_FUZZ_PROB:
            return skip()
    elif not path.favored and state.n_entries > 10:
        # Otherwise, still possibly skip non-favored cases, albeit less often.
        # The odds of skipping stuff are higher for already-fuzzed inputs and
        # lower for never-fuzzed entries.
        if state.queue_cycle > 1 and not path.fuzzed:
            if random.random() < SKIP_NFAV_NEW_PROB:
                return skip()
        else:
            if random.random() < SKIP_NFAV_OLD_PROB:
                return skip()
    
    if not path.calibrated:
        cal_result = bool(calibrate(state, path))
        path.cov = None

        if not cal_result:
            return skip()
        

    # TODO: trimming

    perf_score = calculate_score(state, path)
    orig_perf = perf_score

    out_buf = bytearray(path.args)

    path_queued: int = 0
    doing_det = not path.fuzzed

    state.op_logger.write('fuzz_one: begin fuzz')
    
    if not path.fuzzed and not SKIP_DETERMINISTIC:
        state.op_logger.write('fuzz_one: begin deterministic fuzz')

        #region bitflip
        #region bitflip 1/1
        for _ in generate_bitflips(out_buf, 1):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1

            # TODO: sensitivity analysis of token
        #endregion
        
        #region bitflip 2/2
        for _ in generate_bitflips(out_buf, 2):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1            
        #endregion

        #region bitflip 4/1
        for _ in generate_bitflips(out_buf, 4):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1
        #endregion
       
        #region bitflip 8/8
        for i, _ in generate_byteflips(out_buf, 1):
            res = fuzz_arg(state, bytes(out_buf), path.depth)

            if not res:
                return done()
            else:
                path_queued += 1
            
            # TODO: eff map
        #endregion

        #region bitflip 16/8
        for _ in generate_byteflips(out_buf, 2):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1
        #endregion

        #region bitflip 32/8
        for _ in generate_byteflips(out_buf, 4):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1

        #endregion
        #endregion

        #region arith
        #region arith 8/8
        for _ in generate_arith8(out_buf):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1

        #endregion

        #region arith 16/8
        for _ in generate_arith16(out_buf):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1
        #endregion

        #region arith 32/8
        for _ in generate_arith32(out_buf):
            if not fuzz_arg(state, bytes(out_buf), path.depth):
                return done()
            else:
                path_queued += 1
        #endregion
        #endregion

        # TODO: intereting values
        # TODO: extras

        state.op_logger.write('completed determinisic fuzz')

    # random stage
    splice_cycle: int = 0

    state.op_logger.write('begin stochastic fuzz')

    while splice_cycle <= SPLICE_CYCLES:
        #region havoc
        if not splice_cycle:
            stage_max = HAVOC_CYCLES_INIT if doing_det else HAVOC_CYCLES
            stage_max = stage_max * perf_score // state.havoc_diff // 100
        else:
            stage_max = SPLICE_HAVOC * perf_score // state.havoc_diff // 100

        stage_max = max(stage_max, HAVOC_MIN)

        for _ in range(stage_max):
            havoc(out_buf)

        if not fuzz_arg(state, bytes(out_buf), path.depth):
            return done()
        else:
            path_queued += 1


        # TODO: increase perf_score if find stuff
        if not state.should_splice: break
        #endregion

        #region splice
        # reset buffer
        with state.lock:
            source = state.sample()
        if not source: break

        out_buf = bytearray(path.args)
        out_buf = splice(out_buf, source)

        splice_cycle += 1
        #endregion

    state.op_logger.write('completed stochastic fuzz')

    return done()