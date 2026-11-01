import contextlib
import io
import os
import unittest
from unittest import mock

import main as main_module

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main_module.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestFullPipelineDirect(unittest.TestCase):
    """Все три модуля интегрированы: ввод -> обработка -> вывод (прямые вызовы)."""

    def test_example_1(self):
        code, out, _ = run_main([os.path.join(EXAMPLES, "input1.txt")])
        self.assertEqual(code, 0)
        self.assertIn("[True, False, True, False]  -> столбцы: 1, 3", out)

    def test_example_2(self):
        code, out, _ = run_main([os.path.join(EXAMPLES, "input2.txt")])
        self.assertEqual(code, 0)
        self.assertIn("[True, False, True, False]  -> строки: 1, 3", out)
        self.assertIn("[False, True, True, True]  -> строки: 2, 3, 4", out)

    def test_missing_file(self):
        code, _, err = run_main(["no_such_file.txt"])
        self.assertEqual(code, 1)
        self.assertIn("InvalidDataError", err)

    def test_eof_on_console(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            code, _, err = run_main([])
        self.assertEqual(code, 1)
        self.assertIn("ввод прерван", err)


if __name__ == "__main__":
    unittest.main()
