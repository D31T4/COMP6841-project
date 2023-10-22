from coverage.pytracer import PyTracer as _PyTracer, RESUME, RETURN_VALUE, YIELD_FROM_OFFSET, YIELD_FROM, YIELD_VALUE
from coverage.types import TLineNo, TTraceFn
import sys
from types import FrameType
from typing import Any, Optional
from collections import defaultdict

from .context import Context

THIS_FILE = __file__.rstrip("co")

class PyTracer(_PyTracer):
    def __init__(self):
        super().__init__()
        self.cur_file_pe = None

    def _get_marker(self, file: str, line: int):
        if file != self.cur_file_name:
            self.cur_file_pe = Context.get()._pe.get(file, None)

        return self.cur_file_pe.get(line, -1) if self.cur_file_pe else -1

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

        if filename != self.cur_file_name:
            if file_pe := Context.get()._pe.get(filename, None):
                pe = file_pe.get(flineno, -1)
        else:
            file_pe = self.cur_file_pe
            pe = self.cur_file_pe.get(flineno, -1)
        
        if pe != -1:
            print(event, frame)
            print(f'pe: {pe}')
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
        """
        if event == "call":
            # Should we start a new context?
            if self.should_start_context and self.context is None:
                context_maybe = self.should_start_context(frame)
                if context_maybe is not None:
                    self.context = context_maybe
                    started_context = True
                    assert self.switch_context is not None
                    self.switch_context(self.context)
                else:
                    started_context = False
            else:
                started_context = False
            self.started_context = started_context

            # Entering a new frame.  Decide if we should trace in this file.
            self._activity = True
            self.data_stack.append(
                (
                    self.cur_file_data,
                    self.cur_file_name,
                    self.last_line,
                    started_context,
                )
            )

            # Improve tracing performance: when calling a function, both caller
            # and callee are often within the same file. if that's the case, we
            # don't have to re-check whether to trace the corresponding
            # function (which is a little bit expensive since it involves
            # dictionary lookups). This optimization is only correct if we
            # didn't start a context.
            filename = frame.f_code.co_filename
            if filename != self.cur_file_name or started_context:
                self.cur_file_name = filename
                disp = self.should_trace_cache.get(filename)
                if disp is None:
                    disp = self.should_trace(filename, frame)
                    self.should_trace_cache[filename] = disp

                self.cur_file_data = None
                if disp.trace:
                    tracename = disp.source_filename
                    assert tracename is not None
                    if tracename not in self.data:
                        self.data[tracename] = defaultdict(lambda: 0)    # type: ignore[assignment]
                    self.cur_file_data = self.data[tracename]
                else:
                    frame.f_trace_lines = False
            elif not self.cur_file_data:
                frame.f_trace_lines = False

            # The call event is really a "start frame" event, and happens for
            # function calls and re-entering generators.  The f_lasti field is
            # -1 for calls, and a real offset for generators.  Use <0 as the
            # line number for calls, and the real line number for generators.
            if RESUME is not None:
                # The current opcode is guaranteed to be RESUME. The argument
                # determines what kind of resume it is.
                oparg = frame.f_code.co_code[frame.f_lasti + 1]
                real_call = (oparg == 0)
            else:
                real_call = (getattr(frame, "f_lasti", -1) < 0)
            if real_call:
                self.last_line = -frame.f_code.co_firstlineno
            else:
                self.last_line = frame.f_lineno

        elif event == "line":
            # Record an executed line.
            if self.cur_file_data is not None:
                flineno: TLineNo = frame.f_lineno

                if self.trace_arcs:
                    self.cur_file_data[(self.last_line, flineno)] += 1
                else:
                    self.cur_file_data[flineno] += 1
                self.last_line = flineno

        elif event == "return":
            if self.trace_arcs and self.cur_file_data:
                # Record an arc leaving the function, but beware that a
                # "return" event might just mean yielding from a generator.
                code = frame.f_code.co_code
                lasti = frame.f_lasti
                if RESUME is not None:
                    if len(code) == lasti + 2:
                        # A return from the end of a code object is a real return.
                        real_return = True
                    else:
                        # it's a real return.
                        real_return = (code[lasti + 2] != RESUME)
                else:
                    if code[lasti] == RETURN_VALUE:
                        real_return = True
                    elif code[lasti] == YIELD_VALUE:
                        real_return = False
                    elif len(code) <= lasti + YIELD_FROM_OFFSET:
                        real_return = True
                    elif code[lasti + YIELD_FROM_OFFSET] == YIELD_FROM:
                        real_return = False
                    else:
                        real_return = True
                if real_return:
                    first = frame.f_code.co_firstlineno
                    self.cur_file_data[(self.last_line, -first)]  += 1
            
            # Leaving this function, pop the filename stack.
            self.cur_file_data, self.cur_file_name, self.last_line, self.started_context = (
                self.data_stack.pop()
            )
            # Leaving a context?
            if self.started_context:
                assert self.switch_context is not None
                self.context = None
                self.switch_context(None)
        """
                
        return self._cached_bound_method_trace
