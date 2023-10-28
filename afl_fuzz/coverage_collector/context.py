from .pos_enc import get_positional_encoding
from .dep_analyzer import get_deps
import json

class Context:
    '''
    coverage collection context
    '''
    _instance = None

    def __init__(self, n_buckets: int, pe: dict[str, dict[int, int]] = None):
        self._n_buckets = n_buckets
        self._pe = pe or dict()

    @property
    def n_buckets(self) -> int:
        return self._n_buckets

    @staticmethod
    def create(n_nuckets: int, entry: str):
        src = get_deps(entry)
        pe = get_positional_encoding(src)
        return Context(n_nuckets, pe)

    @staticmethod
    def read(f: str):
        with open(f, 'r') as io:
            obj = json.load(io)

            pe = obj['pe']
            for k in pe.keys():
                pe[k] = dict(pe[k])

            n_buckets = int(obj['n_buckets'])

            Context._instance = Context(n_buckets=n_buckets, pe=obj['pe'])

    @staticmethod
    def get():
        return Context._instance

    def write(self, f: str):
        serialized_pe = dict(self._pe)

        for k in self._pe.keys():
            serialized_pe[k] = [*self._pe[k].items()]

        with open(f, 'w') as io:
            json.dump({
                'pe': serialized_pe,
                'n_buckets': self.n_buckets
            }, io)