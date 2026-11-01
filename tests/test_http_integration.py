import json
import os
import unittest
import urllib.error
import urllib.request

from matrix_lab import http_client, mapping
from matrix_lab.errors import IntegrationError, InvalidDataError
from tests.http_helpers import running_server

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")


def post(url, payload):
    data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url + "/api/v1/process", data=data, method="POST")
    return urllib.request.urlopen(request, timeout=2)


class TestRestIntegration(unittest.TestCase):
    def test_health(self):
        with running_server() as url:
            with urllib.request.urlopen(url + "/api/v1/health", timeout=2) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(body, {"status": "ok", "api_version": mapping.API_VERSION})

    def test_unknown_path_404(self):
        with running_server() as url:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(url + "/nope", timeout=2)
            self.assertEqual(ctx.exception.code, 404)
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                post(url + "/x", {})
            self.assertEqual(ctx.exception.code, 404)

    def test_client_server_roundtrip(self):
        with running_server() as url:
            result = http_client.process_remote([[0, 5, 0], [0, 3, 0]], base_url=url)
        self.assertEqual(result.zero_columns, [True, False, True])
        self.assertEqual(result.descending_rows, [False, False])

    def test_response_matches_direct_call(self):
        from matrix_lab import input_module, processing_module
        matrix = input_module.read_matrix(os.path.join(EXAMPLES, "input2.txt"))
        direct = processing_module.process(matrix)
        with running_server() as url:
            remote = http_client.process_remote(matrix, base_url=url)
        self.assertEqual(remote, direct)

    def test_server_rejects_bad_json(self):
        with running_server() as url:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                post(url, b"{not json")
        self.assertEqual(ctx.exception.code, 400)

    def test_server_rejects_bad_matrix(self):
        with running_server() as url:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                post(url, {"api_version": mapping.API_VERSION,
                           "matrix": {"rows": 1, "cols": 2, "data": [[1]]}})
        self.assertEqual(ctx.exception.code, 400)

    def test_client_reports_http_error(self):
        # сервис вернёт 400 на непрямоугольную матрицу, посланную мимо mapping
        with running_server() as url:
            with self.assertRaises(IntegrationError):
                http_client.process_remote([[1, 2], [3]], base_url=url)

    def test_client_cannot_send_nan(self):
        with self.assertRaises(InvalidDataError):
            http_client.process_remote([[float("nan")]], base_url="http://127.0.0.1:1")

    def test_unreachable_service(self):
        with self.assertRaises(IntegrationError):
            http_client.process_remote([[1]], base_url="http://127.0.0.1:1", timeout=0.5)


if __name__ == "__main__":
    unittest.main()
