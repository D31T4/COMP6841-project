# COMP6841-project

A toy Python fuzzer made for COMP6841 Extended Security Engineering and Cyber Security.

Implements a simplified version of the [American Fuzzy Lop](https://en.wikipedia.org/wiki/American_fuzzy_lop_(fuzzer)) (AFL) algorithm.

In short, poke the test program and see what happens by generating random inputs and observe coverage.

# Features

- ✅ Coverage based fuzzing
- ✅ Local search and evolutionary randomization
- ⬜️ Real concurrency
- ⬜️ Adaptive computation
- ⬜️ Fuzz report

# Usage

1. Download the project
2. Run `pip install -e .` at the project root to install the project as an editable package in pip.
3. Run any `fuzz.py` in the demo folder. Or use it to fuzz your own (see instructions in [afl_fuzz/afl/README.md](afl_fuzz/afl/README.md)).

# Technical Details

See:
- [afl_fuzz/coverage_collector/README.md](afl_fuzz/coverage_collector/README.md)
- [afl_fuzz/afl/README.md](afl_fuzz/afl/README.md).

# Disclaimer

Some code in [afl_fuzz/afl](afl_fuzz/afl) are stolen from the [AFL repository](https://github.com/google/AFL).

This is a toy project, not meant for production use. Performance is not our first priority and there are lots of bugs in the project. Use at your own risk.
