import io
import json
import socket
import unittest
import urllib.error
import urllib.request
from unittest import mock

from matrix_lab import http_client, mapping
from matrix_lab.errors import (
    IntegrationError,
    InvalidDataError,
    ModuleTimeoutError,
    ModuleUnavailableError,
    VersionConflictError,
)
from tests.http_helpers import running_server


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TestModuleUnavailable(unittest.TestCase):
    def test_connection_refused(self):
        url = f"http://127.0.0.1:{free_port()}"
        with self.assertRaises(ModuleUnavailableError):
            http_client.process_remote([[1]], base_url=url, timeout=10)

    def test_connection_reset_during_read(self):
        with mock.patch("urllib.request.urlopen", side_effect=ConnectionResetError("reset")):
            with self.assertRaises(ModuleUnavailableError):
                http_client.process_remote([[1]])


class TestTimeout(unittest.TestCase):
    def test_slow_service(self):
        with running_server(delay=0.5) as url:
            with self.assertRaises(ModuleTimeoutError):
                http_client.process_remote([[1]], base_url=url, timeout=0.1)

    def test_timeout_inside_urlerror(self):
        err = urllib.error.URLError(socket.timeout("timed out"))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(ModuleTimeoutError):
                http_client.process_remote([[1]])

    def test_fast_service_within_timeout(self):
        with running_server(delay=0.0) as url:
            result = http_client.process_remote([[1]], base_url=url, timeout=2)
        self.assertEqual(result.zero_columns, [False])


class TestInvalidData(unittest.TestCase):
    def test_server_400_becomes_invalid_data(self):
        bad_dto = {"api_version": mapping.API_VERSION,
                   "matrix": {"rows": 1, "cols": 2, "data": [[1]]}}
        with running_server() as url:
            with mock.patch("matrix_lab.http_client.mapping.matrix_to_dto", return_value=bad_dto):
                with self.assertRaises(InvalidDataError) as ctx:
                    http_client.process_remote([[1, 2]], base_url=url)
        self.assertIn("Строка 1", str(ctx.exception))

    def test_garbage_response(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"<html>not json</html>"

        with mock.patch("urllib.request.urlopen", return_value=Response()):
            with self.assertRaises(InvalidDataError):
                http_client.process_remote([[1]])

    def test_unexpected_http_status(self):
        err = urllib.error.HTTPError("http://x", 500, "boom", {}, io.BytesIO(b""))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(IntegrationError) as ctx:
                http_client.process_remote([[1]])
        self.assertIn("500", str(ctx.exception))


class TestVersionConflict(unittest.TestCase):
    def test_check_version(self):
        mapping.check_version({"api_version": "1.7"})  # та же старшая версия — совместимо
        for dto in ({"api_version": "2.0"}, {}, None, {"api_version": 1}):
            with self.subTest(dto=dto):
                with self.assertRaises(VersionConflictError):
                    mapping.check_version(dto)

    def test_server_answers_409(self):
        payload = mapping.matrix_to_dto([[1]])
        payload["api_version"] = "2.0"
        with running_server() as url:
            request = urllib.request.Request(
                url + "/api/v1/process", data=json.dumps(payload).encode("utf-8"), method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(request, timeout=2)
        self.assertEqual(ctx.exception.code, 409)

    def test_client_raises_version_conflict(self):
        old = mapping.matrix_to_dto([[1]])
        old["api_version"] = "2.0"
        with running_server() as url:
            with mock.patch("matrix_lab.http_client.mapping.matrix_to_dto", return_value=old):
                with self.assertRaises(VersionConflictError):
                    http_client.process_remote([[1]], base_url=url)

    def test_client_checks_response_version(self):
        reply = mapping.result_to_dto(mapping.dto_to_result(
            {"result": {"zeroColumns": [True], "descendingRows": [True], "symmetricRows": [True]}}))
        reply["api_version"] = "9.0"

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(reply).encode("utf-8")

        with mock.patch("urllib.request.urlopen", return_value=Response()):
            with self.assertRaises(VersionConflictError):
                http_client.process_remote([[1]])


class TestExitCodes(unittest.TestCase):
    def test_codes_are_distinct(self):
        codes = [InvalidDataError.exit_code, ModuleUnavailableError.exit_code,
                 ModuleTimeoutError.exit_code, VersionConflictError.exit_code]
        self.assertEqual(sorted(codes), [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
