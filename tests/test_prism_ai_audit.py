import unittest

from scripts.prism_ai_audit import (
    check_markdown_links,
    heading_anchors,
    is_scannable_text,
    redact_sensitive_text,
    safe_report_url,
    scan_secret_candidates,
)


class MarkdownLinkTests(unittest.TestCase):
    def setUp(self):
        self.paths = {"README.md", "docs/guide.md", "docs/images/flow.svg", "LICENSE"}

    def test_relative_file_and_anchor_resolve(self):
        docs = {
            "README.md": "# Home\n\n[Guide](docs/guide.md#first-steps)\n",
            "docs/guide.md": "# First steps\n\n[Home](../README.md#home)\n",
        }
        result = check_markdown_links(docs, self.paths)
        self.assertEqual(result["broken"], [])
        self.assertEqual(result["checked"], 2)

    def test_missing_relative_file_is_reported(self):
        result = check_markdown_links(
            {"README.md": "[Missing](docs/nope.md)\n"}, self.paths
        )
        self.assertEqual(len(result["broken"]), 1)
        self.assertIn("missing target", result["broken"][0]["problem"])

    def test_missing_heading_is_reported(self):
        docs = {
            "README.md": "[Bad anchor](docs/guide.md#does-not-exist)\n",
            "docs/guide.md": "# Real heading\n",
        }
        result = check_markdown_links(docs, self.paths)
        self.assertEqual(len(result["broken"]), 1)
        self.assertIn("missing heading", result["broken"][0]["problem"])

    def test_external_urls_are_not_fetched(self):
        result = check_markdown_links(
            {"README.md": "[Website](https://example.com)\n"}, self.paths
        )
        self.assertEqual(result["external"], 1)
        self.assertEqual(result["checked"], 0)
        self.assertEqual(result["broken"], [])

    def test_duplicate_heading_slugs(self):
        anchors = heading_anchors("# Setup\n\n## Setup!\n\n## A & B\n")
        self.assertIn("setup", anchors)
        self.assertIn("setup-1", anchors)
        self.assertIn("a--b", anchors)


class CredentialScanTests(unittest.TestCase):
    def test_detects_without_returning_secret_value(self):
        candidate = "ghp_" + ("A" * 36)
        hits = scan_secret_candidates("src/config.py", "TOKEN = " + candidate)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["detector"], "github-token")
        self.assertNotIn(candidate, str(hits))

    def test_placeholder_is_ignored(self):
        candidate = "ghp_" + ("example" * 6)
        self.assertEqual(scan_secret_candidates("README.md", candidate), [])

    def test_dotenv_files_are_included_in_scan(self):
        self.assertTrue(is_scannable_text(".env", 20))
        self.assertTrue(is_scannable_text(".env.local", 20))

    def test_report_redacts_token_and_private_key_values(self):
        token = "ghp_" + ("B" * 36)
        private_key = "-----BEGIN PRIVATE KEY-----\nPRIVATE-MATERIAL\n-----END PRIVATE KEY-----"
        safe = redact_sensitive_text("token=" + token + " " + private_key)
        self.assertNotIn(token, safe)
        self.assertNotIn("PRIVATE-MATERIAL", safe)
        self.assertIn("[REDACTED]", safe)

    def test_report_url_drops_userinfo_query_and_fragment(self):
        safe = safe_report_url("https://user:password@example.com/path?token=secret#fragment")
        self.assertEqual(safe, "https://example.com/path")

    def test_private_key_marker_is_detected(self):
        hits = scan_secret_candidates("keys.txt", "-----BEGIN PRIVATE KEY-----\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["detector"], "private-key")


if __name__ == "__main__":
    unittest.main()
