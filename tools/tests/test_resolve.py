"""Unit tests for the autoupdate resolver's pure selection logic. Fixtures
are real tag lists captured with `git ls-remote --tags` from the repos that
produced past reds (see docs/autoupdate.md); synthetic cases cover shapes
we have not hit yet. No network: resolve.py's I/O layer is not under test.
Run via tools/test.sh (inside the gate) or directly:

    python3 -m unittest discover -s tools/tests -t . -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "scripts"))

import resolve  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(name):
    return (FIXTURES / f"{name}.txt").read_text().split()


class NormalizeTag(unittest.TestCase):
    def test_plain_with_and_without_v(self):
        self.assertEqual(resolve.normalize_tag("v1.2.3"), ("1.2.3", True))
        self.assertEqual(resolve.normalize_tag("1.2.3"), ("1.2.3", True))
        self.assertEqual(resolve.normalize_tag("2.2.5"), ("2.2.5", True))

    def test_component_tags_are_fallback_only(self):
        self.assertEqual(resolve.normalize_tag("vscode-v1.0.0"), ("1.0.0", False))
        self.assertEqual(resolve.normalize_tag("rust-v0.163.0"), ("0.163.0", False))
        self.assertEqual(resolve.normalize_tag("vfox-v2026.11.9"),
                         ("2026.11.9", False))

    def test_junk_and_degenerate_tags_rejected(self):
        # ghostty's "vt-1.0.0" has no "-v<digit>" boundary and no digit
        # start: not a version tag in either pass
        for t in ("vt-1.0.0", "_pr-attachments", "worktree-release",
                  "v.1.5.5", "<2.7.0", "latest", ""):
            self.assertIsNone(resolve.normalize_tag(t), t)


class SelectTag(unittest.TestCase):
    def test_strict_beats_component(self):
        # anomalyco/opencode: plain v2.x must beat vscode-v* component tags
        self.assertEqual(resolve.select_tag(fixture("anomalyco-opencode")),
                         "2.3.2")

    def test_component_fallback_when_no_plain_tags(self):
        self.assertEqual(resolve.select_tag(
            ["rust-v0.163.0", "rust-v0.162.0"]), "0.163.0")

    def test_component_date_scheme_tracks_its_own_tags(self):
        # jdx/mise ships vfox-* component tags mirroring its date scheme:
        # plain v2026.11.9 exists, so the strict pass wins
        self.assertEqual(resolve.select_tag(fixture("mise")), "2026.11.9")

    def test_ghostty_vt_component_tags_ignored(self):
        self.assertEqual(resolve.select_tag(fixture("ghostty")), "1.4.0")

    def test_legacy_prefixed_cluster_loses_to_plain(self):
        # faugus-launcher: old "v1.1-24" tags must not beat plain "2.5.7"
        self.assertEqual(resolve.select_tag(fixture("faugus-launcher")),
                         "2.5.7")

    def test_degenerate_leading_dot_tags_ignored(self):
        self.assertEqual(resolve.select_tag(fixture("kora")), "2.0.6")
        self.assertEqual(resolve.select_tag(fixture("hydra")), "4.4.1")

    def test_junk_top_tag_ignored(self):
        self.assertEqual(resolve.select_tag(fixture("oh-my-openagent")),
                         "5.1.77")

    def test_date_tags_order_numerically(self):
        # vinceliuice themes tag with dates; "2026-08-10" is the max
        self.assertEqual(resolve.select_tag(fixture("colloid-icon-theme")),
                         "2026-08-10")

    def test_prerelease_never_outranks_its_release(self):
        self.assertEqual(resolve.select_tag(
            ["v1.6.0", "v1.6.0-rc1", "v1.5.9"]), "1.6.0")
        self.assertEqual(resolve.select_tag(
            ["v0.45.0-rc.2", "v0.44.1"]), "0.45.0-rc.2")

    def test_numeric_segments_compare_as_integers(self):
        self.assertEqual(resolve.select_tag(
            ["v0.9.9", "v0.10.0", "v0.100.0"]), "0.100.0")

    def test_no_version_tags_at_all(self):
        self.assertIsNone(resolve.select_tag(["main", "nightly", "next"]))


class StripReleaseTag(unittest.TestCase):
    def test_leading_v(self):
        self.assertEqual(resolve.strip_release_tag("v1.19.6"), "1.19.6")

    def test_component_prefix_from_release(self):
        # openai/codex class: releases/latest tag_name "rust-v0.163.0"
        self.assertEqual(resolve.strip_release_tag("rust-v0.163.0"),
                         "0.163.0")

    def test_plain_tag_without_v(self):
        self.assertEqual(resolve.strip_release_tag("2.2.5"), "2.2.5")


class JsonField(unittest.TestCase):
    def test_compact_and_pretty(self):
        self.assertEqual(resolve.json_field('{"tag_name":"v1.0"}', "tag_name"),
                         "v1.0")
        self.assertEqual(
            resolve.json_field('{\n  "tag_name": "v1.0"\n}', "tag_name"), "v1.0")

    def test_first_element_of_a_list(self):
        # gitlab /tags and codeberg /tags return arrays
        self.assertEqual(
            resolve.json_field('[{"name":"v2"},{"name":"v1"}]', "name"), "v2")

    def test_garbage_body_is_none(self):
        # a 200 response can still be an HTML error page
        self.assertIsNone(resolve.json_field("<html>forbidden</html>", "name"))
        self.assertIsNone(resolve.json_field(None, "name"))


class VerKey(unittest.TestCase):
    def test_dates_and_dashed_versions(self):
        self.assertGreater(resolve.ver_key("2026-08-10"),
                           resolve.ver_key("2025-12-31"))
        self.assertGreater(resolve.ver_key("1.1-24"), resolve.ver_key("1.1-9"))

    def test_long_component_scheme(self):
        self.assertGreater(resolve.ver_key("1.0.30.1"), resolve.ver_key("1.0.30"))


if __name__ == "__main__":
    unittest.main()
