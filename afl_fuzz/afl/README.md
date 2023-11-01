# AFL

Main fuzzing logic.

## Fuzzing from an optimization perspective

In fuzzing, our objective is to maximize the coverage of the test program. And it is desirable to minimize runtime, number of test cases, size of test cases to reduce time (runtime, I/O) and resources (memory, disc).

We vary the input (a sequence of bytes) to optimize the objective. We now have a integer programing problem which sadly is not polynomial time.

## How AFL works

### AFL formulation of the optimization problem

AFL optimizes coverage and minimizes a score function $f(x)=\text{size}\cdot\text{runtime}$. It keeps the cases with the minimum score in each bucket in the next cycle.

AFL minimizes the number of test cases kept using a greedy approximation.

AFL also reduces the average size of test cases by 1) setting a higher probability of deletion in mutation; and 2) trim the test cases such that size is reduced but the coverage remains same.

### Solving the optimization problem

AFL uses a combination of local search and evolutionary algorithm to optimize our objective.

Local search:

- deterministic perturbation of the input by arithmatic additions/subtractions, bit-flipping, substitutions.

AFL defers local search probabalistically since this is an expensive process which requires calling the test program very frequently.

Evolutionary algorithm:

- random mutations (arithmatic additions/subtractions, bit-flipping, insertion, deletion, substitution)
- splicing: randomized combination of 2 input byte sequence

This above process is repeated iteratively.

### When to stop?

Stop when no new branches is discovered for a while.

## Our Implementation

We implemented most of the algorithmic features of AFL. Except the adaptive computation part: which AFL will adjust some parameters based on score and runtime, allowing certain test cases to be ran more frequently.

Our implementation is not concurrent. We used `ThreadPool` in our implementation and it subjects to the global interpreter lock.

## Usage

```{python}
from afl_fuzz.afl import fuzz

fuzz(
    entry, 
    seed, 
    exception_logger, 
    op_logger, 
    max_elapsed, 
    max_cycles, 
    n_workers,
    on_exception
)
```

- `entry`: entry point filename: must be in same folder as your fuzzing code
- `seed`: initial test cases
- `exception_logger`: logger
- `op_logger`: operation logger for debug
- `max_elapsed`: max elapsed time. prevents next cycle if current elapsed > max_elapsed
- `max_cycles`: max fuzz cycles
- `n_workers`: no. of workers.
- `on_exception`: called when a new case is discovered with exception