from .exec import fuzz_arg, calibrate
from .config import SKIP_FUZZ_PROB, SKIP_NFAV_NEW_PROB, SKIP_NFAV_OLD_PROB
from afl_fuzz.coverage_collector.result import CoverageResult
from .state import State
import random

def fuzz_one(state: State, path: CoverageResult):
    if state.pending_favored:
        if (path.fuzzed or not path.favored) and random.random() < SKIP_FUZZ_PROB:
            return 1
    elif len(state.queue) > 10:
        if state.queue_cycle > 1 and not path.fuzzed:
            if random.random() < SKIP_NFAV_NEW_PROB:
                return 1
        else:
            if random.random() < SKIP_NFAV_OLD_PROB:
                return 1
            
    if not path.calibrated:
        path = calibrate(state, path.args, state.queue_cycle - 1)

        if path.exception:
            return