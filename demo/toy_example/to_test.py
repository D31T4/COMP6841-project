from test_util import render_bool

def rng(n):
    for i in range(n): yield i

def get_list():
    return [i for i in rng(10)]

def main(x: bytes):
    x = int.from_bytes(x[:1], 'big')

    if x - 1 == 0:
        print('1')

    x = get_list()

    render_bool(x)

    y = 1 if True else 0
    print(y)

    for i in range(10):
        if i % 2:
            print(
                'Fizz' +
                'z'
            )
        else:
            print('Buzz')

if True:
    print('imported')