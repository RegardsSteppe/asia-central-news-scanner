import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

import http_utils
from http_utils import fetch_url, _is_retryable_error


class IsRetryableErrorTests(unittest.TestCase):
    def test_timeout_is_retryable(self):
        exc = requests.exceptions.Timeout("timed out")
        self.assertTrue(_is_retryable_error(exc))

    def test_connection_error_is_retryable(self):
        exc = requests.exceptions.ConnectionError("boom")
        self.assertTrue(_is_retryable_error(exc))

    def test_503_response_is_retryable(self):
        response = MagicMock(status_code=503)
        exc = requests.exceptions.HTTPError("server error", response=response)
        self.assertTrue(_is_retryable_error(exc))

    def test_404_response_is_not_retryable(self):
        response = MagicMock(status_code=404)
        exc = requests.exceptions.HTTPError("not found", response=response)
        self.assertFalse(_is_retryable_error(exc))


class FetchUrlTests(unittest.TestCase):
    def setUp(self):
        http_utils._MEMORY_CACHE.clear()
        http_utils._CACHE_META = {}
        self._tmpdir = tempfile.TemporaryDirectory()
        http_utils._CACHE_FILE = Path(self._tmpdir.name) / "http_cache.json"

    def tearDown(self):
        self._tmpdir.cleanup()

    @patch("http_utils.time.sleep", return_value=None)
    @patch("http_utils.requests.get")
    def test_retries_then_succeeds(self, mock_get, mock_sleep):
        timeout_exc = requests.exceptions.Timeout("timed out")

        success_response = MagicMock()
        success_response.raise_for_status.return_value = None
        success_response.encoding = "utf-8"
        success_response.text = "content"

        mock_get.side_effect = [timeout_exc, success_response]

        result = fetch_url(
            "https://example.com/feed",
            headers={},
            request_timeout=5,
            cache_ttl=60,
        )

        self.assertEqual(result, "content")
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("http_utils.time.sleep", return_value=None)
    @patch("http_utils.requests.get")
    def test_gives_up_after_max_attempts(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.exceptions.ConnectionError("down")

        with self.assertRaises(RuntimeError):
            fetch_url(
                "https://example.com/feed",
                headers={},
                request_timeout=5,
                cache_ttl=60,
            )

        self.assertEqual(mock_get.call_count, http_utils.MAX_ATTEMPTS)

    @patch("http_utils.requests.get")
    def test_ssl_error_is_not_retried(self, mock_get):
        mock_get.side_effect = requests.exceptions.SSLError("bad cert")

        with self.assertRaises(RuntimeError):
            fetch_url(
                "https://example.com/feed",
                headers={},
                request_timeout=5,
                cache_ttl=60,
            )

        self.assertEqual(mock_get.call_count, 1)

    @patch("http_utils.requests.get")
    def test_uses_cache_without_extra_request(self, mock_get):
        success_response = MagicMock()
        success_response.raise_for_status.return_value = None
        success_response.encoding = "utf-8"
        success_response.text = "cached content"
        mock_get.return_value = success_response

        url = "https://example.com/cached"

        first = fetch_url(url, headers={}, request_timeout=5, cache_ttl=60)
        second = fetch_url(url, headers={}, request_timeout=5, cache_ttl=60)

        self.assertEqual(first, second)
        self.assertEqual(mock_get.call_count, 1)

    @patch("http_utils.requests.get")
    def test_uses_conditional_request_headers_from_persisted_cache(self, mock_get):
        first_response = MagicMock()
        first_response.status_code = 200
        first_response.raise_for_status.return_value = None
        first_response.encoding = "utf-8"
        first_response.text = "fresh content"
        first_response.headers = {
            "ETag": '"abc123"',
            "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT",
        }

        not_modified_response = MagicMock()
        not_modified_response.status_code = 304
        not_modified_response.raise_for_status.return_value = None
        not_modified_response.encoding = "utf-8"
        not_modified_response.text = ""
        not_modified_response.headers = {}

        mock_get.side_effect = [first_response, not_modified_response]

        url = "https://example.com/feed"
        result_1 = fetch_url(url, headers={}, request_timeout=5, cache_ttl=60)
        http_utils._MEMORY_CACHE.clear()
        result_2 = fetch_url(url, headers={}, request_timeout=5, cache_ttl=0)

        self.assertEqual(result_1, "fresh content")
        self.assertEqual(result_2, "fresh content")
        self.assertEqual(mock_get.call_count, 2)
        second_call_headers = mock_get.call_args_list[1].kwargs["headers"]
        self.assertEqual(second_call_headers["If-None-Match"], '"abc123"')
        self.assertEqual(
            second_call_headers["If-Modified-Since"],
            "Mon, 01 Jan 2024 00:00:00 GMT",
        )


if __name__ == "__main__":
    unittest.main()
