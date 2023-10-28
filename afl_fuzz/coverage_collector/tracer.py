'''
lossy tracer
'''

from coverage.pytracer import PyTracer as _PyTracer
from coverage.types import TLineNo, TTraceFn
import sys
from types import FrameType
from typing import Any, Optional

from .context import Context

THIS_FILE = __file__.rstrip("co")

class PyTracer(_PyTracer):
    def __init__(self):
        super().__init__()
        self.cur_file_pe = None

    def _trace(
        self,
        frame: FrameType,
        event: str,
        arg: Any,                               # pylint: disable=unused-argument
        lineno: Optional[TLineNo] = None,       # pylint: disable=unused-argument
    ) -> Optional[TTraceFn]:
        """The trace function passed to sys.settrace."""
        
        if THIS_FILE in frame.f_code.co_filename:
            return None
        
        if (self.stopped and sys.gettrace() == self._cached_bound_method_trace):
            sys.settrace(None)
            return None

        
        flineno: TLineNo = frame.f_lineno
        filename = frame.f_code.co_filename

        pe: int = -1

        # cache file marker
        if filename != self.cur_file_name:
            if file_pe := Context.get()._pe.get(filename, None):
                pe = file_pe.get(flineno, -1)
        else:
            file_pe = self.cur_file_pe
            pe = self.cur_file_pe.get(flineno, -1)
        
        if pe != -1:
            self._activity = True
            
            if event == 'call':
                self.data_stack.append((self.last_line, self.cur_file_name, self.cur_file_pe))

                if self.last_line != 0:
                    self.data.add(self.last_line, pe)

                self.last_line = 0
                self.cur_file_name = filename
                self.cur_file_pe = file_pe

            elif event == 'line':
                # Note: 
                # cannot distinguish multiline statements
                # e.g.
                # ```
                # print(
                #   'x' + 
                #   'y'
                # )
                # ```
                #
                # inline statements
                # e.g.
                # ```
                # if x: print(x)
                # ```
                if self.last_line != 0:
                    self.data.add(self.last_line, pe)

                self.last_line = pe >> 1

            elif event == 'return':
                if self.last_line != 0:
                    self.data.add(self.last_line, self.data_stack[-1][0])

                self.last_line, self.cur_file_name, self.cur_file_pe = self.data_stack.pop()

        return self._cached_bound_method_trace
