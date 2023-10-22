import subprocess
import sys
import json
import uuid
import os

def _compile_code(src: str, out: str, kwargs: str, ctx: str) -> str:
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
try:
    from coverage import Coverage;
    import traceback;
    import json;
    import override;

    from coverage_collector.context import Context

    Context.read("{ctx}")

    c = Coverage(branch=True, data_file=None, data_suffix=True, timid=True);
    c.start();
    
    from {src} import main;
    main(**{kwargs})

    c.stop();
    #c.json_report(outfile="{out}")

    with open("{out}", 'w') as f:
        json.dump({{
            "cov": c._collector.data.get_binned(),
            "exception": False
        }}, f);

except Exception as ex:
    with open("{out}", 'w') as f:
        json.dump({{
            "name": ex.__class__.__name__,
            "message": str(ex),
            "stacktrace": traceback.format_exc(),
            "exception": True
        }}, f);
'''

def collect(src: str, ctx: str, kwargs: dict[any, any] = None, out: str = None):
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
    out = out or f'.temp.{uuid.uuid4()}'
    kwargs = json.dumps(kwargs or dict())

    try:
        p = subprocess.Popen([sys.executable, '-c', _compile_code(src, out, kwargs, ctx)])
        p.wait()
        
        if p.returncode != 0:
            raise Exception('failed to collect coverage due to an exception')

        with open(out, 'r') as f:
            result = json.load(f)

        return result
    finally:
        #os.path.exists(out) and os.remove(out)
        pass