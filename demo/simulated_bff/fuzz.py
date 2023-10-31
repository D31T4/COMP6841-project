import random
import string

from afl_fuzz import fuzz
from afl_fuzz.logger.print import PrintLogger

from buffer_overflow import buffer_len

if __name__ == '__main__':
    logger = PrintLogger()

    exceptions_found = set()

    def on_exception(args: bytes, exception: dict[str, str]):
        if exception['name'] not in exceptions_found:
            print(f'new exception found: {exception["name"]}')
            exceptions_found.add(exception['name'])

    seed = [
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(0, buffer_len))).encode('utf-8')
        for _ in range(10)
    ]

    seed.append(('a' * 100).encode('utf-8'))

    fuzz(
        'buffer_overflow.py',
        seed,
        op_logger=logger,
        exception_logger=logger,
        n_workers=1,
        on_exception=on_exception
    )
