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

class TestColumnAllZero(unittest.TestCase):
    def test_mixed(self):
        m = [[0, 1, 0], [0, 0, 0], [0, 2, 0]]
        self.assertEqual(logic.column_all_zero(m), [True, False, True])

    def test_no_zero_columns(self):
        self.assertEqual(logic.column_all_zero([[1, 2], [3, 4]]), [False, False])

    def test_all_zero(self):
        self.assertEqual(logic.column_all_zero([[0, 0], [0, 0]]), [True, True])

    def test_negative_zero_and_tiny(self):
        self.assertEqual(logic.column_all_zero([[-0.0, 1e-12], [0.0, 0.0]]), [True, True])

    def test_single_row(self):
        self.assertEqual(logic.column_all_zero([[0, 5, 0]]), [True, False, True])
        