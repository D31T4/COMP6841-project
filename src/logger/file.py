from threading import Lock
from .base import ILogger

class FileLogger(ILogger):
    '''
    write log to disc
    '''
    def __init__(self, fname: str):
        self._fname = fname
        self._lock = Lock()

    @property
    def fname(self):
        return self._fname
    
    def write(self, msg: str):
        with self._lock, open(self.fname, 'a') as f:
            f.write(msg)