import coverage.control as control
import coverage.collector as collector

from .tracer import PyTracer
from .collector import Collector

collector.PyTracer = PyTracer
control.Collector = Collector