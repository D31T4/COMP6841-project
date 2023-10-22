from .pos_enc import get_positional_encoding
from .dep_analyzer import get_deps
import json

class Context:
    _instance = None

    def __init__(self, pe: dict[str, dict[int, int]] = None):
        self._pe = pe or dict()

    @staticmethod
    def create(entry: str):
        src = get_deps(entry)
        pe = get_positional_encoding(src)
        return Context(pe)

    @staticmethod
    def read(f: str):
        with open(f, 'r') as io:
            obj = json.load(io)

            pe = obj['pe']
            for k in pe.keys():
                pe[k] = dict(pe[k])

            Context._instance = Context(pe=obj['pe'])

    @staticmethod
    def get():
        return Context._instance

    def write(self, f: str):
        serialized_pe = dict(self._pe)

        for k in self._pe.keys():
            serialized_pe[k] = [*self._pe[k].items()]

        with open(f, 'w') as io:
            json.dump({
                'pe': serialized_pe
            }, io)