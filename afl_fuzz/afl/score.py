from afl_fuzz.afl.state import State
from afl_fuzz.afl.config import HAVOC_MAX_MULT, PREFER_QUEUE_CAPACITY
from afl_fuzz.afl.queue import Queue
from afl_fuzz.coverage_collector.result import CoverageResult

import random


def calculate_score(state: State, cov: CoverageResult):
    '''
    calculate score for adjusting fuzzing time

    Arguments:
    ---
    - state: afl state
    - cov: coverage

    Returns:
    ---
    - score
    '''
    avg_exec_us = state.avg_total_cal_us
    avg_bitmap_size = state.avg_bitmap_size

    perf_score: int = 100

    if cov.elapsed * 0.1 > avg_exec_us:
        perf_score = 10
    elif cov.elapsed * 0.25 > avg_exec_us:
        perf_score = 25
    elif cov.elapsed * 0.5 > avg_exec_us:
        perf_score = 50
    elif cov.elapsed * 0.75 > avg_exec_us:
        perf_score = 75
    elif cov.elapsed * 4 < avg_exec_us:
        perf_score = 300
    elif cov.elapsed * 3 < avg_exec_us:
        perf_score = 200
    elif cov.elapsed * 2 < avg_exec_us:
        perf_score = 150


    if cov.bitmap_size * 0.3 > avg_bitmap_size:
        perf_score *= 3
    elif cov.bitmap_size * 0.5 > avg_bitmap_size:
        perf_score *= 2
    elif cov.bitmap_size * 0.75 > avg_bitmap_size:
        perf_score *= 1.5
    elif cov.bitmap_size * 3 < avg_bitmap_size:
        perf_score *= 0.25
    elif cov.bitmap_size * 2 < avg_bitmap_size:
        perf_score *= 0.5
    elif cov.bitmap_size * 1.5 < avg_bitmap_size:
        perf_score *= 0.75

    # Adjust score based on handicap. Handicap is proportional to how late
    # in the game we learned about this path. Latecomers are allowed to run
    # for a bit longer until they catch up with the rest.
    if cov.handicap >= 4:
        perf_score *= 4
        cov.handicap -= 4
    elif cov.handicap:
        perf_score *= 2
        cov.handicap -= 1

    # Final adjustment based on input depth, under the assumption that fuzzing
    # deeper test cases is more likely to reveal stuff that can't be
    # discovered with traditional fuzzers.
    if cov.depth >= 4 and cov.depth <= 7:
        perf_score *= 2
    elif cov.depth >= 8 and cov.depth <= 13:
        perf_score *= 3
    elif cov.depth >= 14 and cov.depth <= 25:
        perf_score *= 4
    elif cov.depth > 25:
        perf_score *= 5

    perf_score = min(perf_score, HAVOC_MAX_MULT * 100)

    return perf_score

def update_bitmap_score(state: State, cov: CoverageResult):
    '''
    update bitmap score

    Arguments:
    ---
    - state: afl state
    - cov: coverage result
    '''
    factor = cov.elapsed * len(cov.args)

    for i in range(state.n_buckets):
        if not cov.cov[i]: continue

        tr = state.top_rated[i]

        if tr and factor > tr.elapsed * len(tr.args):
            continue

        state.top_rated[i] = cov
        cov.cov_ref += 1
        state.score_changed = True
        
        if tr:
            tr.cov_ref -= 1
        
            if tr.cov_ref <= 0:
                tr.cov = None

    state.op_logger.write('update_bitmap_score completed')


def cull_queue(state: State):
    '''
    cull queue.

    Arguments:
    ---
    - state: afl state
    '''
    with state.lock:
        # join queue
        state.queue._queue.extend(state.fuzzed_queue)
        state.fuzzed_queue.clear()

        if not state.score_changed: return

        state.score_changed = False
        state.pending_favored = 0

        covered = [False] * state.n_buckets

        for el in state.queue:
            el.favored = False

        for i in range(state.n_buckets):
            if not state.top_rated[i] or covered[i]:
                continue
                
            for j in range(state.n_buckets):
                covered[i] |= bool(state.top_rated[j])

            if not state.top_rated[i].favored:
                state.pending_favored += 1

            state.top_rated[i].favored = True

        # drop unfavored items from queue probalistically
        if len(state.queue) > PREFER_QUEUE_CAPACITY and PREFER_QUEUE_CAPACITY > state.pending_favored:
            # expected no. of items after drop = PREFER_QUEUE_CAPACITY
            keep_prob = (PREFER_QUEUE_CAPACITY - state.pending_favored) / len(state.queue)

            new_queue = Queue()

            for el in state.queue:
                if el.favored or random.random() < keep_prob:
                    new_queue.push(el)

            state.queue = new_queue

        state.n_entries = len(state.queue)

    state.op_logger.write('cull_queue completed')