'''
inject overrides
'''

import coverage.control as control
import coverage.collector as collector

from afl_fuzz.coverage_collector.tracer import PyTracer
from afl_fuzz.coverage_collector.collector import Collector

collector.PyTracer = PyTracer
control.Collector = Collector