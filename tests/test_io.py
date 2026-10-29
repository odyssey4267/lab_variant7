import unittest

from matrix_lab.io_utils import parse_matrix

class TestParse(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(parse_matrix(["2 2", "1 2", "3,5 4"]), [[1.0, 2.0], [3.5, 4.0]])

    def test_bad_header(self):
        with self.assertRaises(ValueError):
            parse_matrix(["2", "1 2"])

    def test_wrong_rows(self):
        with self.assertRaises(ValueError):
            parse_matrix(["2 2", "1 2"])

    def test_wrong_cols(self):
        with self.assertRaises(ValueError):
            parse_matrix(["1 2", "1"])

    def test_not_number(self):
        with self.assertRaises(ValueError):
            parse_matrix(["1 2", "1 a"])
