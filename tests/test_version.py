import unittest

from matrix_lab import version

class TestVersion(unittest.TestCase):
    def test_format(self):
        self.assertRegex(version.get_version(), r"^\d+\.\d+\.\d+$")

    def test_constant_matches_function(self):
        self.assertEqual(version.get_version(), version.__version__)

if __name__ == "__main__":
    unittest.main()
