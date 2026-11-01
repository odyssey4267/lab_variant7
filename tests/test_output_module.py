import unittest

from matrix_lab import output_module
from matrix_lab.models import Report


class TestOutputModule(unittest.TestCase):
    def make_report(self, **kw):
        base = dict(matrix=[[0.0, 1.0], [0.0, 2.0]], zero_columns=[True, False],
                    descending_rows=[False, False], symmetric_rows=[False, False])
        base.update(kw)
        return Report(**base)

    def test_render_contains_matrix_and_vectors(self):
        text = output_module.render(self.make_report())
        self.assertIn("Матрица:", text)
        self.assertIn("0  1", text)
        self.assertIn("[True, False]  -> столбцы: 1", text)

    def test_render_none_found(self):
        text = output_module.render(self.make_report(zero_columns=[False, False]))
        self.assertIn("[False, False]  -> столбцы: нет", text)

    def test_render_several_numbers(self):
        text = output_module.render(self.make_report(symmetric_rows=[True, True]))
        self.assertIn("-> строки: 1, 2", text)


if __name__ == "__main__":
    unittest.main()
