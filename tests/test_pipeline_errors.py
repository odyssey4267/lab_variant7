import contextlib
import io
import os
import socket
import unittest

import main as main_module
from tests.http_helpers import running_server

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
INPUT = os.path.join(EXAMPLES, "input1.txt")


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main_module.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestExitCodesFromCli(unittest.TestCase):
    def test_service_down_gives_code_2(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        code, _, err = run_main([INPUT, "--transport", "http",
                                 "--url", f"http://127.0.0.1:{port}", "--timeout", "5"])
        self.assertEqual(code, 2)
        self.assertIn("ModuleUnavailableError", err)

    def test_slow_service_gives_code_3(self):
        with running_server(delay=0.5) as url:
            code, _, err = run_main([INPUT, "--transport", "http", "--url", url,
                                     "--timeout", "0.1"])
        self.assertEqual(code, 3)
        self.assertIn("ModuleTimeoutError", err)


if __name__ == "__main__":
    unittest.main()
