import contextlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from org_blogger.cli import resolve_org_file
from org_blogger.config import resolve_config_dir
from org_blogger.org_export import parse_labels


class ResolveOrgFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.drafts = self.root / "drafts"
        self.drafts.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_accepts_direct_path(self):
        post = self.root / "post.org"
        post.write_text("* Heading", encoding="utf-8")

        self.assertEqual(resolve_org_file(str(post), self.drafts), post.resolve())

    def test_accepts_filename_inside_drafts(self):
        post = self.drafts / "post.org"
        post.write_text("* Heading", encoding="utf-8")

        self.assertEqual(resolve_org_file("post.org", self.drafts), post.resolve())

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            resolve_org_file("missing.org", self.drafts)


class ParseLabelsTests(unittest.TestCase):
    def test_comma_separated(self):
        self.assertEqual(parse_labels("emacs, org, blogger"), ["emacs", "org", "blogger"])

    def test_whitespace_separated(self):
        self.assertEqual(parse_labels("emacs org blogger"), ["emacs", "org", "blogger"])

    def test_mixed_separators_and_duplicates_whitespace(self):
        self.assertEqual(parse_labels(" emacs,org  blogger "), ["emacs", "org", "blogger"])

    def test_empty(self):
        self.assertEqual(parse_labels(None), [])
        self.assertEqual(parse_labels("   "), [])


class ResolveConfigDirTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop("ORG_BLOGGER_CONFIG_DIR", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_explicit_directory_wins(self):
        self.assertEqual(
            resolve_config_dir(self.root / "custom"),
            self.root / "custom",
        )

    def test_environment_variable(self):
        os.environ["ORG_BLOGGER_CONFIG_DIR"] = str(self.root / "from-env")
        self.assertEqual(resolve_config_dir(), self.root / "from-env")

    def test_local_config_directory_is_preferred(self):
        (self.root / "config").mkdir()
        with contextlib.chdir(self.root):
            self.assertEqual(resolve_config_dir(), self.root / "config")


if __name__ == "__main__":
    unittest.main()
