import unittest

from matrix_lab import logic

class TestValidate(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(logic.validate_matrix([[1, 2, 3], [4, 5, 6]]), (2, 3))

    def test_empty(self):
        with self.assertRaises(ValueError):
            logic.validate_matrix([])
        with self.assertRaises(ValueError):
            logic.validate_matrix([[]])

    def test_ragged(self):
        with self.assertRaises(ValueError):
            logic.validate_matrix([[1, 2], [3]])
