from .state import State
from .config import HAVOC_MAX_MULT, PREFER_QUEUE_CAPACITY
from .queue import Queue
from afl_fuzz.coverage_collector.result import CoverageResult

import random


def calculate_score(state: State, cov: CoverageResult):
    '''
    
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
        
        tr.cov_ref -= 1
        
        if tr.cov_ref <= 0:
            tr.cov = None


def cull_queue(state: State):
    '''
    
    '''
    if not state.score_changed: return

    covered = [False] * state.n_buckets

    favored: int = 0

    with state.lock:
        state.score_changed = False
        state.pending_favored = 0

        for el in state.queue:
            el.favored = False

        for i in range(state.n_buckets):
            if not state.top_rated[i] or covered[i]:
                continue
                
            for j in range(state.n_buckets):
                covered[i] |= bool(state.top_rated[j])

            state.top_rated[i].favored = True
            favored += 1
            
            if not state.top_rated[i].fuzzed:
                state.pending_favored += 1

        # drop unfavored items from queue probalistically
        if len(state.queue) > PREFER_QUEUE_CAPACITY and PREFER_QUEUE_CAPACITY > favored:
            # expected no. of items after drop = PREFER_QUEUE_CAPACITY
            keep_prob = (PREFER_QUEUE_CAPACITY - favored) / len(state.queue)

            new_queue = Queue()

            for el in state.queue:
                if el.favored or random.random() < keep_prob:
                    new_queue.push(el)

            state.queue = new_queue