'''
unit test for queue.py
'''

import unittest

from afl_fuzz.afl.queue import Queue

class queue_test(unittest.TestCase):
    '''
    unit test for Queue
    '''

    def test_push(self):
        q = Queue(range(10))

        for i0, i1 in enumerate(q):
            self.assertEqual(i0, i1)

    def test_pop(self):
        q = Queue(range(10))

        for i in range(len(q)):
            self.assertEqual(i, q.pop())

        self.assertIsNone(q.pop())

    def test_sample(self):
        q = Queue(range(10))

        for _ in range(10):
            self.assertIsNotNone(q.sample())

if __name__ == '__main__':
    unittest.main()