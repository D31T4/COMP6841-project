'''
lossy coverage collector
'''

from coverage.collector import Collector as _Collector

from afl_fuzz.coverage_collector.pos_enc import Hitcount
from afl_fuzz.coverage_collector.context import Context

class Collector(_Collector):
    def reset(self):
        super().reset()
        
        self.data = Hitcount(n_buckets=Context.get().n_buckets)