from afl_fuzz import fuzz
from afl_fuzz.logger.print import PrintLogger

if __name__ == '__main__':
    logger = PrintLogger()

    fuzz(
        'to_test.py',
        [bytes([0x00])],
        max_cycles=2,
        op_logger=logger,
        exception_logger=logger
    )
