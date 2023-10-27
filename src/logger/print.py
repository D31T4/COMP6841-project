from typing import Callable
from threading import Lock
from .base import ILogger

class PrintLogger(ILogger):
    def __init__(self, write: Callable[[str], None] = print):
        self._write = write
        self._lock = Lock()

    def write(self, msg: str):
        with self._lock:
            self._write(msg)
