"""Unit tests for vendor-sources.py's pure helpers. No network: the fetch
and cargo layers are not under test. Run via tools/test.sh (inside the
gate) or directly:

    python3 -m unittest discover -s tools/tests -t . -v
"""

import importlib.util
import sys
import tempfile
import unittest
import tomllib
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "vendor_sources", Path(__file__).resolve().parents[1] / "vendor-sources.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)


class CrateMemberDir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def test_virtual_workspace_root_resolves_to_member(self):
        # craft-libs shape: root is a virtual manifest, crate in a subdir
        self.write("Cargo.toml", "[workspace]\nmembers = [\"crates/*\"]\n")
        self.write("crates/craft-audio/Cargo.toml",
                   "[package]\nname = \"craft-audio\"\nversion = \"0.1.0\"\n")
        self.write("crates/craft-mime/Cargo.toml",
                   "[package]\nname = \"craft-mime\"\nversion = \"0.1.0\"\n")
        self.assertEqual(vs.crate_member_dir(self.root, "craft-audio"),
                         self.root / "crates" / "craft-audio")

    def test_root_package_manifest_falls_back_to_root(self):
        self.write("Cargo.toml", "[package]\nname = \"single\"\nversion = \"1.0\"\n")
        self.assertEqual(vs.crate_member_dir(self.root, "single"), self.root)

    def test_no_match_falls_back_to_root(self):
        # caller (pin_duplicate_git_crate) dies loudly on this when the
        # root is a virtual manifest
        self.write("Cargo.toml", "[workspace]\n")
        self.assertEqual(vs.crate_member_dir(self.root, "gone"), self.root)

    def test_name_in_array_or_deps_does_not_match(self):
        # workspace members lists / dependency tables mention crate names
        # without a package manifest: only `^name = "..."` counts
        self.write("Cargo.toml",
                   "[workspace]\nmembers = [\"crates/*\"]\n"
                   "[dependencies]\nother = \"1\"\n")
        self.write("crates/other/Cargo.toml",
                   "[package]\nname = \"other\"\n"
                   "[dependencies]\ncraft-audio = { path = \"../craft-audio\" }\n")
        self.assertEqual(vs.crate_member_dir(self.root, "craft-audio"),
                         self.root)


class FlattenWorkspaceMembers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def test_inlines_inheritance_and_rewrites_path_deps(self):
        # craft-libs shape: virtual root, member inherits package fields,
        # registry deps and root-relative path deps
        self.write("Cargo.toml",
                   "[workspace]\nmembers = [\"crates/*\"]\n\n"
                   "[workspace.package]\nversion = \"0.1.0\"\nedition = \"2021\"\n\n"
                   "[workspace.dependencies]\nserde = \"1\"\n"
                   "sib = { path = \"crates/sib\" }\n")
        self.write("crates/sib/Cargo.toml",
                   "[package]\nname = \"sib\"\nversion.workspace = true\n"
                   "edition.workspace = true\n")
        cm = self.write("crates/foo/Cargo.toml",
                        "[package]\nname = \"foo\"\nversion.workspace = true\n"
                        "edition.workspace = true\n\n"
                        "[lints]\nworkspace = true\n\n"
                        "[dependencies]\nserde = { workspace = true }\n"
                        "sib = { workspace = true }\n")
        vs.flatten_workspace_members(self.root)
        m = tomllib.loads(cm.read_text())
        self.assertEqual(m["package"]["version"], "0.1.0")
        self.assertEqual(m["package"]["edition"], "2021")
        self.assertEqual(m["dependencies"]["serde"], {"version": "1"})
        # root-relative crates/sib -> member-relative ../sib
        self.assertEqual(m["dependencies"]["sib"]["path"], "../sib")
        self.assertNotIn("workspace", m["dependencies"]["serde"])
        # sibling flattened too (it is reached via the path closure)
        sib = tomllib.loads((self.root / "crates/sib/Cargo.toml").read_text())
        self.assertEqual(sib["package"]["version"], "0.1.0")

    def test_clean_manifests_untouched(self):
        self.write("Cargo.toml",
                   "[workspace]\nmembers = [\"crates/*\"]\n\n"
                   "[workspace.package]\nversion = \"0.1.0\"\n")
        cm = self.write("crates/plain/Cargo.toml",
                        "[package]\nname = \"plain\"\nversion = \"2.0\"\n")
        before = cm.read_text()
        vs.flatten_workspace_members(self.root)
        self.assertEqual(cm.read_text(), before)

    def test_roundtrip_supports_arrays_of_tables_and_nested_targets(self):
        # _toml_dumps must survive [[bin]] sections and target-scoped deps
        self.write("Cargo.toml",
                   "[workspace]\nmembers = [\"crates/*\"]\n\n"
                   "[workspace.package]\nversion = \"0.1.0\"\n\n"
                   "[workspace.dependencies]\nserde = \"1\"\n")
        cm = self.write("crates/app/Cargo.toml",
                        "[package]\nname = \"app\"\nversion.workspace = true\n\n"
                        "[[bin]]\nname = \"appbin\"\npath = \"src/main.rs\"\n\n"
                        "[target.'cfg(windows)'.dependencies]\n"
                        "serde = { workspace = true }\n")
        vs.flatten_workspace_members(self.root)
        m = tomllib.loads(cm.read_text())
        self.assertEqual(m["bin"][0]["name"], "appbin")
        self.assertEqual(m["target"]["cfg(windows)"]["dependencies"]["serde"],
                         {"version": "1"})


if __name__ == "__main__":
    unittest.main()
