'''
config settings
'''

# no. of buckets used in sketch
TRACE_BUCKETS: int = 1024

# Default timeout for fuzzed code (milliseconds).
EXEC_TIMEOUT: int = 500

# Number of calibration cycles per every new test case
CALIBRATE_SAMPLE_SIZE: int = 3

PREFER_QUEUE_CAPACITY: int = 2000

# Probabilities of skipping non-favored entries in the queue
SKIP_FUZZ_PROB: float = 0.99
SKIP_NFAV_OLD_PROB: float = 0.95
SKIP_NFAV_NEW_PROB: float = 0.75

# Minimum input file length at which the effector logic kicks in:
EFF_MIN_LEN: int = 128

# Maximum effector density past which everything is just fuzzed
# unconditionally:
EFF_MAX_PERC: float = 0.9

# Maximum offset for integer addition / subtraction stages:
ARITH_MAX: int = 35

# Splicing cycle count:
SPLICE_CYCLES: int = 15

# Nominal per-splice havoc cycle length:
SPLICE_HAVOC: int = 32

# Baseline number of random tweaks during a single 'havoc' stage:
HAVOC_CYCLES_INIT: int = 1024
HAVOC_CYCLES: int = 256

HAVOC_MIN: int = 16

# Maximum multiplier for the above (should be a power of two, beware
# of 32-bit int overflows):
HAVOC_MAX_MULT: int = 16

# Maximum stacking for havoc-stage tweaks. The actual value is calculated
# like this: 
#
# n = random between 1 and HAVOC_STACK_POW2
# stacking = 2^n
# 
# In other words, the default (n = 7) produces 2, 4, 8, 16, 32, 64, or
# 128 stacked tweaks:
HAVOC_STACK_POW2: int = 7

# Caps on block sizes for cloning and deletion operations. Each of these
# ranges has a 33% probability of getting picked, except for the first
# two cycles where smaller blocks are favored:
HAVOC_BLK_SM: int = 32
HAVOC_BLK_MD: int = 128
HAVOC_BLK_LG: int = 1500
HAVOC_BLK_XL: int = 32768

SKIP_DETERMINISTIC: bool = False

# Limits for the test case trimmer. The absolute minimum chunk size; and
# the starting and ending divisors for chopping up the input file:
TRIM_MIN_BYTES: int = 4
TRIM_START_STEPS: int = 16
TRIM_END_STEPS: int = 1024

# Maximum size of input file, in bytes
MAX_FILE: int = 1 * 1024 * 1024