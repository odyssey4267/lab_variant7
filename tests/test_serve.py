import contextlib
import io
import unittest
from unittest import mock

import serve


class FakeServer:
    closed = False

    def serve_forever(self):
        raise KeyboardInterrupt

    def server_close(self):
        self.closed = True


class TestServe(unittest.TestCase):
    def test_main_starts_and_stops(self):
        fake = FakeServer()
        out = io.StringIO()
        with mock.patch("serve.make_server", return_value=fake) as factory:
            with contextlib.redirect_stdout(out):
                code = serve.main(["--port", "9999"])
        self.assertEqual(code, 0)
        self.assertTrue(fake.closed)
        factory.assert_called_once_with("127.0.0.1", 9999)
        self.assertIn("Сервис запущен", out.getvalue())


if __name__ == "__main__":
    unittest.main()
