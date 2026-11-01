import os
import tempfile
import unittest
from unittest import mock

from matrix_lab import input_module
from matrix_lab.errors import InvalidDataError

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


class TestInputModule(unittest.TestCase):
    def test_reads_example_file(self):
        matrix = input_module.read_matrix(os.path.join(EXAMPLES, "input1.txt"))
        self.assertEqual(len(matrix), 3)
        self.assertEqual(matrix[0], [0.0, 5.0, 0.0, 1.0])

    def test_missing_file_is_invalid_data(self):
        with self.assertRaises(InvalidDataError):
            input_module.read_matrix("no_such_file.txt")

    def test_malformed_file_is_invalid_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("2 2\n1 2\n3\n")
            with self.assertRaises(InvalidDataError):
                input_module.read_matrix(path)

    def test_console_input(self):
        answers = ["2 2", "1 2", "3,5 4"]
        with mock.patch("builtins.input", side_effect=answers):
            matrix = input_module.read_matrix()
        self.assertEqual(matrix, [[1.0, 2.0], [3.5, 4.0]])

    def test_console_eof_is_invalid_data(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            with self.assertRaises(InvalidDataError) as ctx:
                input_module.read_matrix()
        self.assertIn("ввод прерван", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
