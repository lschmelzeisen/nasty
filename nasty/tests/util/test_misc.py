import unittest

from nasty.util.misc import chunked


class TestChunked(unittest.TestCase):
    def test_length_divisable(self):
        self.assertEqual([[0, 1, 2], [3, 4, 5]],
                         list(chunked(3, range(6))))

    def test_length_divisable_pad(self):
        self.assertEqual([[0, 1, 2], [3, 4, 5]],
                         list(chunked(3, range(6), pad=True)))

    def test_length_unidivisable(self):
        self.assertEqual([[0, 1, 2], [3, 4, 5], [6]],
                         list(chunked(3, range(7))))

    def test_length_unidivisable_pad(self):
        self.assertEqual([[0, 1, 2], [3, 4, 5], [6, None, None]],
                         list(chunked(3, range(7), pad=True)))

    def test_length_unidivisable_pad_value(self):
        self.assertEqual([[0, 1, 2], [3, 4, 5], [6, 'x', 'x']],
                         list(chunked(3, range(7), pad=True, pad_value='x')))
