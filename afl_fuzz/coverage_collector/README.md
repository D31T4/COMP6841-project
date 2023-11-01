# Coverage collector

Collects branch coverage for `afl`.

## Background

AFL collects branch coverage of the control graph. Below shows an example of a control flow graph.

```{python}
# A
if x:
  # B
else:
  # C
# D
```

The control flow graph is: `A->B`, `A->C`, `B->D`, `C->D`. And branch coverage is the multiset of traversed edges in the control flow graph, one example is `{ A->B: 1, B->D: 1 }`.

AFL approximates the branch coverage using a lossy data structure (similar to a [counting bloom filter](https://en.wikipedia.org/wiki/Counting_Bloom_filter) but we only have one hash function). It places randomized markers (randomized once before fuzzing) on the control flow nodes, and collect branch coverage using the below hash function:

```
hash <- (current_position xor previous_position) mod n
coverage[hash] += 1
previous_position <- current_position >> 1
```

`n` is the no. of buckets in the hash table (coverage). We compute a bitshift such that the hash is not commutative (i.e. `hash(A->B) != hash(B->A)`), and to distinguish tight loops and recursions (i.e. `hash(A->A) != hash(B->B)`).

Finally, the counts in the hash table are binned into 8 buckets (so that we can fit in 1-byte):

- 0: 0,
- 1: 1,
- 2: 2,
- 3: 3,
- 4: 4-7,
- 5: 8-15,
- 6: 16-31,
- 7: 32-127,
- 8: 128+

## Implementation

We used the package coverage.py in our implementation. We will first use the python parser in coverage.py to identify nodes in the control flow graph, then we assign random integers to it. The markers are stored in hash tables which maps filename and line number to the marker.

We override the tracer of [coverage.py](https://coverage.readthedocs.io/en/7.3.2/index.html) to track branch execution and perform lossy counting.

To collect branch coverage, we first save the markers into a json file. Then spawn a child process to execute and trace the python file. Finally store the result in a json file and we can access the result by reading the file with our main process. The reason for using child process is to allow parallel and isolated execution.

### Limitations

Our implementations uses hash tables to store the markers. During the tracing process, we need to compute the hash of filenames (string) to retrieve the markers from our hash table and this will be an overhead. In addition, all child processes need to keep its own copy of the hash table in memory leading to memory overhead. Typical fuzzers implements this by injecting instrumentation (including the marker) during compile time and thus no retrieval overhead. And [Atheris](https://github.com/google/atheris) implement this by injecting to Python byte code.

Our implementations relies on the sys.settrace API in Python. Due to the limitation of trace, we cannot track in-line statements (e.g. `if x: do_stuff()` and `x = True if y else False`), multi-line statements e.g.
```{python}
print(
  'x' +
  'y'
)
```
and collection (list/dict/set) comprehension (e.g. `[x for x in range(n)]`).

## Usage

Place your entry point in the same folder as your Python code. Name of your entry point must be a valid Python module.

```{python}
from afl_fuzz.coverage_collector.context import Context
from afl_fuzz.coverage_collector.process import collect

ctx_fname = <path to context file>

# create and write context
ctx = Context.create(n_buckets, <path to your entry point>)
ctx.write(ctx_fname)

# collect coverage
result = collect(<module name of your entry point>, ctx_fname, args)
```

By default, coverage will be collected in all dependencies. Use the `omit` option in `get_deps` to control which file need to be traced.

## Known Issues

- `get_deps` may not parse Python files successfully due to encoding issue.
