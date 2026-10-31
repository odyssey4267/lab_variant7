import contextlib
import io
import os
import unittest
from unittest import mock

import main as main_module

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


class TestMain(unittest.TestCase):
    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main_module.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_example_file(self):
        code, out, _ = self.run_main([os.path.join(EXAMPLES, "input1.txt")])
        self.assertEqual(code, 0)
        self.assertIn("[True, False, True, False]", out)

    def test_missing_file(self):
        code, _, err = self.run_main(["no_such_file.txt"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка", err)

    def test_eof_on_console(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            code, _, err = self.run_main([])
        self.assertEqual(code, 1)
        self.assertIn("ввод прерван", err)


if __name__ == "__main__":
    unittest.main()
