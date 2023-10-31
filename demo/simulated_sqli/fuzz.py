from afl_fuzz import fuzz
from afl_fuzz.logger.print import PrintLogger

if __name__ == '__main__':
    logger = PrintLogger()

    exceptions_found = set()

    def on_exception(args: bytes, exception: dict[str, str]):
        if exception['name'] not in exceptions_found:
            print(f'new exception found: {exception["name"]}')
            exceptions_found.add(exception['name'])

            if exception['name'] == 'SyntaxError':
                print(f'SQLi detected with input: {args.decode("utf-8")}')

    fuzz(
        'sqli.py',
        [bytes([0x00, 0x00, 0x00, 0x00]), 'abc'.encode('utf-8')],
        max_cycles=50,
        op_logger=logger,
        exception_logger=logger,
        n_workers=2,
        on_exception=on_exception
    )
