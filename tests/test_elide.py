"""Tests for the elide CLI (stdlib unittest, path-independent)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ELIDE = str(Path(__file__).resolve().parent.parent / "elide")


def run(args, stdin_data=None):
    return subprocess.run(
        [sys.executable, ELIDE] + args,
        input=stdin_data,
        capture_output=True,
        text=True,
    )


def display_width(s):
    import unicodedata
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        if unicodedata.category(ch) in ("Mn", "Me"):
            continue
        if ord(ch) < 32 or ord(ch) == 127:
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


class TestElide(unittest.TestCase):
    def test_default_width_40(self):
        r = run([], stdin_data="a" * 50 + "\n")
        self.assertEqual(r.returncode, 0)
        line = r.stdout.rstrip("\n")
        self.assertEqual(line, "a" * 39 + "…")
        self.assertEqual(display_width(line), 40)

    def test_short_line_untouched_default(self):
        r = run([], stdin_data="hello\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "hello\n")

    def test_custom_width(self):
        r = run(["--width", "3"], stdin_data="hello\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "he…\n")

    def test_default_ellipsis(self):
        r = run(["--width", "3"], stdin_data="hello\n")
        self.assertTrue(r.stdout.endswith("…\n"))

    def test_custom_ellipsis(self):
        r = run(["--width", "5", "--ellipsis", "..."], stdin_data="hello world\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "he...\n")

    def test_empty_ellipsis(self):
        r = run(["--width", "3", "--ellipsis", ""], stdin_data="hello\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "hel\n")

    def test_words_boundary_vs_hard_cut(self):
        hard = run(["--width", "10"], stdin_data="hello world\n")
        words = run(["--width", "10", "--words"], stdin_data="hello world\n")
        self.assertEqual(hard.stdout, "hello wor…\n")
        self.assertEqual(words.stdout, "hello…\n")
        self.assertNotEqual(hard.stdout, words.stdout)

    def test_words_fallback_no_boundary(self):
        r = run(["--width", "5", "--words"], stdin_data="abcdefghij\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "abcd…\n")

    def test_pad_short_line(self):
        r = run(["--width", "5", "--pad"], stdin_data="hi\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "hi   \n")
        self.assertEqual(display_width(r.stdout.rstrip("\n")), 5)

    def test_pad_combined_with_truncation(self):
        r = run(["--width", "5", "--pad"], stdin_data="hello world\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "hell…\n")
        self.assertEqual(display_width(r.stdout.rstrip("\n")), 5)

    def test_stdin_input(self):
        r = run(["--width", "3"], stdin_data="hello\n")
        self.assertEqual((r.returncode, r.stdout), (0, "he…\n"))

    def test_file_input(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as f:
            f.write("hello\n")
            path = f.name
        try:
            r = run(["--width", "3", path])
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "he…\n")
        finally:
            os.unlink(path)

    def test_multiple_files_in_order(self):
        paths = []
        try:
            for content in ("AAA\n", "BBB\n"):
                f = tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False)
                f.write(content)
                f.close()
                paths.append(f.name)
            r = run(paths)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "AAA\nBBB\n")
        finally:
            for p in paths:
                os.unlink(p)

    def test_missing_file_nonzero_stderr(self):
        r = run(["/nonexistent-elide-fixture"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("No such file", r.stderr)

    def test_invalid_width_zero_exits_2(self):
        r = run(["--width", "0"], stdin_data="hi\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--width", r.stderr)

    def test_invalid_width_negative_exits_2(self):
        r = run(["--width", "-1"], stdin_data="hi\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--width", r.stderr)

    def test_invalid_width_nonnumeric_exits_2(self):
        r = run(["--width", "abc"], stdin_data="hi\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--width", r.stderr)

    def test_ellipsis_wider_than_width_exits_2(self):
        r = run(["--width", "2", "--ellipsis", "..."], stdin_data="hello\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("ellipsis", r.stderr.lower())


if __name__ == "__main__":
    unittest.main()
