from threading import Lock
import os
from datetime import datetime

from .base import ILogger

class FileLogger(ILogger):
    '''
    write log to disc
    '''
    def __init__(self, fname: str):
        '''
        Arguments:
        ---
        - fname: log file name
        '''
        if os.path.exists(fname):
            raise ValueError(f'file {fname} already exists!')

        self._fname = fname
        self._lock = Lock()

    @property
    def fname(self):
        '''
        log file name
        '''
        return self._fname
    
    def write(self, msg: str):
        with self._lock, open(self.fname, 'a') as f:
            f.write(f'{datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}: {msg}')