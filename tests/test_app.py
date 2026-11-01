import unittest

from matrix_lab import app, stubs
from matrix_lab.errors import IntegrationError, InvalidDataError


class TestAppWithStubs(unittest.TestCase):
    def test_pipeline_with_stubs(self):
        out = []
        code = app.run(stubs.read_input_stub, stubs.process_stub, stubs.render_stub,
                       write=out.append)
        self.assertEqual(code, 0)
        self.assertEqual(out, ["[заглушка] вывод для матрицы 2x2"])

    def test_module_error_is_reported_and_returns_code(self):
        def failing():
            raise InvalidDataError("плохие данные")

        errors = []
        code = app.run(failing, stubs.process_stub, stubs.render_stub,
                       write=lambda text: None, write_err=errors.append)
        self.assertEqual(code, 1)
        self.assertIn("плохие данные", errors[0])
        self.assertIn("InvalidDataError", errors[0])

    def test_error_code_comes_from_exception(self):
        class Custom(IntegrationError):
            exit_code = 7

        def failing():
            raise Custom("сбой")

        code = app.run(failing, stubs.process_stub, stubs.render_stub,
                       write=lambda text: None, write_err=lambda text: None)
        self.assertEqual(code, 7)

    def test_default_error_writer_uses_stderr(self):
        import contextlib
        import io

        def failing():
            raise InvalidDataError("x")

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = app.run(failing, stubs.process_stub, stubs.render_stub, write=lambda t: None)
        self.assertEqual(code, 1)
        self.assertIn("x", err.getvalue())

    def test_stubs_return_expected_shape(self):
        matrix = stubs.read_input_stub()
        result = stubs.process_stub(matrix)
        self.assertEqual(len(result.zero_columns), 2)
        self.assertEqual(len(result.descending_rows), 2)


if __name__ == "__main__":
    unittest.main()
