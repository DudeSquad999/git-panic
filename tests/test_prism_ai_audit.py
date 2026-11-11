import unittest

from scripts.prism_ai_audit import (
    check_markdown_links,
    check_typography,
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

    def test_html_image_source_is_checked(self):
        result = check_markdown_links(
            {"README.md": '<img src="docs/images/flow.svg">\n'}, self.paths
        )
        self.assertEqual(result["html_checked"], 1)
        self.assertEqual(result["broken"], [])

    def test_missing_html_asset_is_reported(self):
        result = check_markdown_links(
            {"README.md": '<img src="missing-banner.png">\n'}, self.paths
        )
        self.assertEqual(len(result["broken"]), 1)
        self.assertEqual(result["broken"][0]["kind"], "HTML src/href")

    def test_duplicate_heading_slugs(self):
        anchors = heading_anchors("# Setup\n\n## Setup!\n\n## A & B\n")
        self.assertIn("setup", anchors)
        self.assertIn("setup-1", anchors)
        self.assertIn("a--b", anchors)

    def test_typography_detects_em_dash_and_emoji(self):
        result = check_typography({"README.md": "No issue\nAn em dash — here\nA smile 😀\n"})
        self.assertEqual([item["kind"] for item in result], ["em dash", "emoji"])

    def test_typography_accepts_clean_markdown(self):
        self.assertEqual(check_typography({"README.md": "Plain text and hyphens - only\n"}), [])


class CredentialScanTests(unittest.TestCase):
    def test_detects_secret_as_aggregate_count_only(self):
        candidate = "ghp_" + ("A" * 36)
        match_count = scan_secret_candidates("TOKEN = " + candidate)
        self.assertEqual(match_count, 1)
        self.assertIsInstance(match_count, int)
        self.assertNotIn(candidate, str(match_count))

    def test_placeholder_is_ignored(self):
        candidate = "ghp_" + ("example" * 6)
        self.assertEqual(scan_secret_candidates(candidate), 0)

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
        match_count = scan_secret_candidates("-----BEGIN PRIVATE KEY-----\n")
        self.assertEqual(match_count, 1)


if __name__ == "__main__":
    unittest.main()
