from coverage.collector import Collector as _Collector

from .pos_enc import Hitcount

class Collector(_Collector):
    def reset(self):
        super().reset()

        # 64kB
        self.data = Hitcount(n_buckets=1024*64)