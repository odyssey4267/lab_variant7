import contextlib
import io
import os
import unittest

import main as main_module
from tests.http_helpers import running_server

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


class TestFullPipelineHttp(unittest.TestCase):
    def test_http_transport_gives_same_output_as_direct(self):
        path = os.path.join(EXAMPLES, "input2.txt")

        def run(argv):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main_module.main(argv)
            return code, out.getvalue()

        direct_code, direct_out = run([path])
        with running_server() as url:
            http_code, http_out = run([path, "--transport", "http", "--url", url])
        self.assertEqual((direct_code, http_code), (0, 0))
        self.assertEqual(direct_out, http_out)


if __name__ == "__main__":
    unittest.main()
