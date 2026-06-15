import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync  # noqa: E402


class TestClassify(unittest.TestCase):
    def test_buckets(self):
        s2p = {"docx": "document-skills", "pptx": "document-skills", "old": "example-skills"}
        upstream = ["docx", "pptx", "brandnew"]
        uh = {"docx": "A", "pptx": "B", "brandnew": "Z"}
        fh = {"docx": "A", "pptx": "B-changed", "old": "Q"}
        cls = sync.classify(upstream, s2p, uh, fh)
        self.assertEqual(cls["unchanged"], ["docx"])
        self.assertEqual(cls["updated"], ["pptx"])
        self.assertEqual(cls["new_unmapped"], ["brandnew"])
        self.assertEqual(cls["removed_upstream"], ["old"])


class TestRenderTable(unittest.TestCase):
    def test_order_and_sort(self):
        out = sync.render_table(
            ["document-skills", "claude-api"],
            {"document-skills": ["pptx", "docx"], "claude-api": ["claude-api"], "z-extra": ["zz"]},
        )
        self.assertIn("| `document-skills` | docx, pptx |", out)
        self.assertIn("| `claude-api` | claude-api |", out)
        # plugin not in order still appears (appended, sorted)
        self.assertIn("| `z-extra` | zz |", out)
        self.assertLess(out.index("document-skills"), out.index("claude-api"))


class TestUpdateReadmeTable(unittest.TestCase):
    def test_replaces_region_only(self):
        text = f"top\n{sync.MARKER_BEGIN}\nOLD\n{sync.MARKER_END}\nbottom\n"
        out = sync.update_readme_table(text, "NEW")
        self.assertIn("top\n", out)
        self.assertIn("bottom\n", out)
        self.assertIn(f"{sync.MARKER_BEGIN}\nNEW\n{sync.MARKER_END}", out)
        self.assertNotIn("OLD", out)

    def test_missing_markers_exits(self):
        with self.assertRaises(SystemExit):
            sync.update_readme_table("no markers here", "NEW")


class TestScanPlugins(unittest.TestCase):
    def _mk(self, base, plugin, skill):
        d = base / "plugins" / plugin / "skills" / skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: x\n---\n")

    def test_mapping(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self._mk(base, "document-skills", "docx")
            self._mk(base, "claude-api", "claude-api")
            p2s, s2p = sync.scan_plugins(base)
            self.assertEqual(s2p, {"docx": "document-skills", "claude-api": "claude-api"})
            self.assertEqual(p2s["document-skills"], ["docx"])

    def test_duplicate_skill_exits(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self._mk(base, "a", "dup")
            self._mk(base, "b", "dup")
            with self.assertRaises(SystemExit):
                sync.scan_plugins(base)


class TestMarketplaceIdentity(unittest.TestCase):
    def _mk(self, base, name, owner):
        import json
        d = base / ".claude-plugin"
        d.mkdir(parents=True)
        (d / "marketplace.json").write_text(json.dumps(
            {"name": name, "owner": owner, "metadata": {"x": 1},
             "plugins": [{"name": "p", "source": "./plugins/p"}]}, indent=2) + "\n")

    def test_intact_no_drift_no_write(self):
        import tempfile, json
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self._mk(base, sync.FORK_MARKETPLACE_NAME, sync.FORK_MARKETPLACE_OWNER)
            before = (base / ".claude-plugin" / "marketplace.json").read_text()
            self.assertEqual(sync.marketplace_identity_drift(base), [])
            self.assertEqual(sync.restore_marketplace_identity(base), [])
            # untouched when already correct
            self.assertEqual((base / ".claude-plugin" / "marketplace.json").read_text(), before)

    def test_drift_detected_and_restored(self):
        import tempfile, json
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self._mk(base, "anthropic-agent-skills",
                     {"name": "Keith Lazuka", "email": "klazuka@anthropic.com"})
            drift = sync.marketplace_identity_drift(base)
            self.assertEqual(len(drift), 2)  # both name and owner drifted
            restored = sync.restore_marketplace_identity(base)
            self.assertEqual(len(restored), 2)
            mp = json.loads((base / ".claude-plugin" / "marketplace.json").read_text())
            self.assertEqual(mp["name"], sync.FORK_MARKETPLACE_NAME)
            self.assertEqual(mp["owner"], sync.FORK_MARKETPLACE_OWNER)
            # other fields preserved, key order intact
            self.assertEqual(mp["metadata"], {"x": 1})
            self.assertEqual(mp["plugins"], [{"name": "p", "source": "./plugins/p"}])
            self.assertEqual(list(mp), ["name", "owner", "metadata", "plugins"])
            # now idempotent
            self.assertEqual(sync.marketplace_identity_drift(base), [])


class TestParseKV(unittest.TestCase):
    def test_ok_and_bad(self):
        self.assertEqual(sync.parse_kv(["skill=plug", "k = v "]), {"skill": "plug", "k": "v"})
        with self.assertRaises(SystemExit):
            sync.parse_kv(["noequals"])


if __name__ == "__main__":
    unittest.main()
