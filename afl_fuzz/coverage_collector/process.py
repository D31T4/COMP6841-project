import subprocess
import sys
import json
import uuid
import os
from afl_fuzz.coverage_collector.result import CoverageResult

def _compile_code(src: str, out: str, args: str, ctx: str) -> str:
    '''
    compile template

    Arguments:
    ---
    - src: entry point module
    - out: temp file
    - kwargs: kwargs in json

    Returns:
    ---
    - code
    '''

    return f'''
from coverage import Coverage
import traceback
import json
import time
import afl_fuzz.override

from afl_fuzz.coverage_collector.context import Context

Context.read("{ctx}")

c = Coverage(branch=True, data_file=None, data_suffix=True, timid=True)
elapsed = time.time()
stopped = False

output = dict()

try:
    c.start()
    
    from {src} import main;
    main({args})

    c.stop()
    elapsed = time.time() - elapsed
    stopped = True

    output["exception"] = None

except Exception as ex:
    if not stopped:
        c.stop()
        elapsed = time.time() - elapsed
        stopped = False

    output["exception"] = {{
        "name": ex.__class__.__name__,
        "message": str(ex),
        "stacktrace": traceback.format_exc()
    }}

output["cov"] = c._collector.data.get_binned()
output["elapsed"] = elapsed

with open("{out}", 'w') as f:
    json.dump(output, f)
'''

def collect(src: str, ctx: str, args: bytes, out: str = None, timeout: int = None) -> CoverageResult:
    '''
    collect coverage data in a spawned process

    Arguments:
    ---
    - src: entry point module
    - kwargs: kwargs passed to <src>.main()
    - out: temp file name. use uuid to generate temp file name if set to `None`.

    Returns:
    ---
    - coverage data
    '''
    out = out or f'{uuid.uuid4()}.cov'

    p = subprocess.Popen(
        [sys.executable, '-c', _compile_code(src, out, args, ctx)], 
        stdout=subprocess.DEVNULL,
        #stderr=subprocess.DEVNULL
    )

    try:
        p.wait(timeout=timeout)

        with open(out, 'r') as f:
            result = json.load(f)

        return CoverageResult(
            args=args,
            cov=result['cov'],
            elapsed=result['elapsed'],
            exception=result['exception']
        )
    finally:
        # kill children
        p.terminate()

        os.path.exists(out) and os.remove(out)