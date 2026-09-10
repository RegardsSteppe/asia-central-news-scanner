import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from text_utils import (
    clean_text,
    clean_title,
    normalize_url,
    parse_date,
    article_date_timestamp,
)


class CleanTextTests(unittest.TestCase):
    def test_none_returns_empty_string(self):
        self.assertEqual(clean_text(None), "")

    def test_collapses_whitespace(self):
        self.assertEqual(clean_text("  hello   world  "), "hello world")

    def test_unescapes_html_entities(self):
        self.assertEqual(clean_text("Tom &amp; Jerry"), "Tom & Jerry")

    def test_strips_zero_width_characters(self):
        self.assertEqual(clean_text("hello\u200bworld"), "helloworld")

    def test_repairs_mojibake(self):
        # "café" mis-decoded as latin1/cp1252 then re-encoded UTF-8.
        mojibake = "café".encode("utf-8").decode("latin1")
        self.assertEqual(clean_text(mojibake), "café")

    def test_non_string_input_is_stringified(self):
        self.assertEqual(clean_text(123), "123")


class CleanTitleTests(unittest.TestCase):
    def test_collapses_and_strips(self):
        self.assertEqual(clean_title("  Some   Title\n"), "Some Title")

    def test_empty_input(self):
        self.assertEqual(clean_title(""), "")


class NormalizeUrlTests(unittest.TestCase):
    def test_removes_fragment(self):
        self.assertEqual(
            normalize_url("https://example.com/a?x=1#section"),
            "https://example.com/a?x=1",
        )

    def test_missing_scheme_returns_empty(self):
        self.assertEqual(normalize_url("/relative/path"), "")

    def test_resolves_relative_with_base(self):
        self.assertEqual(
            normalize_url("/a/b", base_url="https://example.com"),
            "https://example.com/a/b",
        )

    def test_empty_input(self):
        self.assertEqual(normalize_url(""), "")

    def test_none_input(self):
        self.assertEqual(normalize_url(None), "")

    def test_strips_tracking_params(self):
        self.assertEqual(
            normalize_url(
                "https://example.com/a?utm_source=x&utm_medium=y&fbclid=z"
            ),
            "https://example.com/a",
        )

    def test_keeps_non_tracking_query_params(self):
        self.assertEqual(
            normalize_url("https://example.com/a?id=123&utm_source=x"),
            "https://example.com/a?id=123",
        )


class ParseDateTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(parse_date(None))

    def test_iso_with_z_suffix(self):
        dt = parse_date("2024-03-15T10:00:00Z")
        self.assertEqual(dt, datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc))

    def test_rfc2822(self):
        dt = parse_date("Fri, 15 Mar 2024 10:00:00 GMT")
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 15)

    def test_invalid_string_returns_none(self):
        self.assertIsNone(parse_date("not a date"))

    def test_struct_time_input(self):
        import time

        struct = time.strptime("2024-03-15", "%Y-%m-%d")
        dt = parse_date(struct)
        self.assertEqual(dt.year, 2024)

    def test_naive_datetime_gets_utc(self):
        dt = parse_date(datetime(2024, 1, 1))
        self.assertEqual(dt.tzinfo, timezone.utc)


class ArticleDateTimestampTests(unittest.TestCase):
    def test_missing_date_returns_zero(self):
        self.assertEqual(article_date_timestamp({}), 0)

    def test_datetime_value(self):
        article = {"date": datetime(2024, 1, 1, tzinfo=timezone.utc)}
        self.assertGreater(article_date_timestamp(article), 0)


if __name__ == "__main__":
    unittest.main()
