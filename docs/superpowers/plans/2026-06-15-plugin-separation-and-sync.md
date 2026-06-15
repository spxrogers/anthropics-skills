# Plugin Separation + Upstream Sync — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Note: this plan and the spec are committed as **commit 0** of the PR (a "superpowers docs" commit), ahead of the three functional commits.

**Goal:** Restructure the fork into isolated per-plugin directories so installing one plugin installs only its own skills, and add a local `sync-from-anthropic-repo` skill that pulls upstream skill updates into that layout.

**Architecture:** Each plugin lives in `plugins/<name>/` with its own `plugin.json`; marketplace `source` points at the subdir (auto-discovery). A Python helper (`sync.py`, stdlib only) treats upstream `anthropics/skills` as the content source of truth and maps its flat `skills/<x>/` onto `plugins/<p>/skills/<x>/`, regenerating the README table and never committing.

**Tech Stack:** git, Python 3 (stdlib: argparse/json/subprocess/shutil/tempfile/pathlib/unittest), `claude plugin validate`, `gh`.

---

## File Structure

**Commit 1 (restructure):**
- Create: `plugins/document-skills/.claude-plugin/plugin.json`, `plugins/example-skills/.claude-plugin/plugin.json`, `plugins/claude-api/.claude-plugin/plugin.json`
- Move (git mv): `skills/<x>/` → `plugins/<plugin>/skills/<x>/` for all 17 skills
- Modify: `.claude-plugin/marketplace.json` (sources → subdirs; drop `strict`+`skills`)
- Delete: empty top-level `skills/`

**Commit 2 (sync skill):**
- Create: `.claude/skills/sync-from-anthropic-repo/SKILL.md`
- Create: `.claude/skills/sync-from-anthropic-repo/sync.py`
- Create: `.claude/skills/sync-from-anthropic-repo/state.json`
- Create: `.claude/skills/sync-from-anthropic-repo/test_sync.py`

**Commit 3 (README):**
- Modify: `README.md` (add "About This Fork" + marker-wrapped table; fix moved-path links)

---

## Task 1: Branch + commit 0 (superpowers docs)

- [ ] **Step 1: Create the branch**

```bash
cd /Users/steven/projects/anthropics-skills
git checkout -b fix/plugin-separation-and-sync
```

- [ ] **Step 2: Commit the spec + plan as commit 0**

```bash
git add docs/superpowers/specs docs/superpowers/plans
git commit -m "$(cat <<'EOF'
Add superpowers design spec and implementation plan

Brainstorming spec and subagent-driven implementation plan for the plugin
separation + upstream sync work that follows in this branch.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 (Commit 1): Move skills into per-plugin directories

**Files:** moves under `skills/` → `plugins/*/skills/`

- [ ] **Step 1: Make plugin skill directories**

```bash
mkdir -p plugins/document-skills/skills plugins/example-skills/skills plugins/claude-api/skills
```

- [ ] **Step 2: git mv the four document skills**

```bash
git mv skills/docx skills/pdf skills/pptx skills/xlsx plugins/document-skills/skills/
```

- [ ] **Step 3: git mv the twelve example skills**

```bash
git mv skills/algorithmic-art skills/brand-guidelines skills/canvas-design \
       skills/doc-coauthoring skills/frontend-design skills/internal-comms \
       skills/mcp-builder skills/skill-creator skills/slack-gif-creator \
       skills/theme-factory skills/web-artifacts-builder skills/webapp-testing \
       plugins/example-skills/skills/
```

- [ ] **Step 4: git mv the claude-api skill, remove empty skills/**

```bash
git mv skills/claude-api plugins/claude-api/skills/
rmdir skills 2>/dev/null || true
```

- [ ] **Step 5: Verify the partition (4 / 12 / 1, none left behind)**

```bash
echo "doc:" $(ls plugins/document-skills/skills | wc -l) \
"ex:" $(ls plugins/example-skills/skills | wc -l) \
"api:" $(ls plugins/claude-api/skills | wc -l)
test ! -d skills && echo "top-level skills/ removed OK"
```
Expected: `doc: 4 ex: 12 api: 1` and `top-level skills/ removed OK`.

---

## Task 3 (Commit 1): Write per-plugin plugin.json files

**Files:** Create three `.claude-plugin/plugin.json`

- [ ] **Step 1: Create directories**

```bash
mkdir -p plugins/document-skills/.claude-plugin plugins/example-skills/.claude-plugin plugins/claude-api/.claude-plugin
```

- [ ] **Step 2: Write `plugins/document-skills/.claude-plugin/plugin.json`**

```json
{
  "name": "document-skills",
  "description": "Collection of document processing suite including Excel, Word, PowerPoint, and PDF capabilities",
  "author": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  }
}
```

- [ ] **Step 3: Write `plugins/example-skills/.claude-plugin/plugin.json`**

```json
{
  "name": "example-skills",
  "description": "Collection of example skills demonstrating various capabilities including skill creation, MCP building, visual design, algorithmic art, internal communications, web testing, artifact building, Slack GIFs, and theme styling",
  "author": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  }
}
```

- [ ] **Step 4: Write `plugins/claude-api/.claude-plugin/plugin.json`**

```json
{
  "name": "claude-api",
  "description": "Claude API and SDK documentation skill for building LLM-powered applications",
  "author": {
    "name": "Anthropic",
    "email": "support@anthropic.com"
  }
}
```

---

## Task 4 (Commit 1): Rewrite marketplace.json

**Files:** Modify `.claude-plugin/marketplace.json`

- [ ] **Step 1: Replace the whole file with subdir sources (no `strict`, no `skills`)**

```json
{
  "name": "anthropic-agent-skills",
  "owner": {
    "name": "Keith Lazuka",
    "email": "klazuka@anthropic.com"
  },
  "metadata": {
    "description": "Anthropic example skills",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "document-skills",
      "description": "Collection of document processing suite including Excel, Word, PowerPoint, and PDF capabilities",
      "source": "./plugins/document-skills"
    },
    {
      "name": "example-skills",
      "description": "Collection of example skills demonstrating various capabilities including skill creation, MCP building, visual design, algorithmic art, internal communications, web testing, artifact building, Slack GIFs, and theme styling",
      "source": "./plugins/example-skills"
    },
    {
      "name": "claude-api",
      "description": "Claude API and SDK documentation skill for building LLM-powered applications",
      "source": "./plugins/claude-api"
    }
  ]
}
```

> `owner` left as upstream values (changing ownership wasn't requested). `name` stays `anthropic-agent-skills` (reserved name, but fine for a local fork).

---

## Task 5 (Commit 1): Verify and commit the restructure

- [ ] **Step 1: Validate the marketplace + each plugin**

```bash
claude plugin validate .
claude plugin validate ./plugins/document-skills
claude plugin validate ./plugins/example-skills
claude plugin validate ./plugins/claude-api
```
Expected: validation passes (no errors). Warnings about missing optional fields are acceptable.

- [ ] **Step 2: Assert isolation structurally**

```bash
python3 - <<'PY'
import json, pathlib
root = pathlib.Path(".")
mp = json.loads((root/".claude-plugin/marketplace.json").read_text())
exp = {
  "document-skills": {"docx","pdf","pptx","xlsx"},
  "example-skills": {"algorithmic-art","brand-guidelines","canvas-design","doc-coauthoring",
                     "frontend-design","internal-comms","mcp-builder","skill-creator",
                     "slack-gif-creator","theme-factory","web-artifacts-builder","webapp-testing"},
  "claude-api": {"claude-api"},
}
for p in mp["plugins"]:
    assert p["source"] == f"./plugins/{p['name']}", p
    got = {d.name for d in (root/"plugins"/p['name']/"skills").iterdir() if d.is_dir()}
    assert got == exp[p['name']], (p['name'], got ^ exp[p['name']])
    assert (root/"plugins"/p['name']/".claude-plugin/plugin.json").is_file()
assert not (root/"skills").exists(), "top-level skills/ still present"
print("OK: 3 plugins isolated, 17 skills partitioned, no top-level skills/")
PY
```
Expected: `OK: 3 plugins isolated, 17 skills partitioned, no top-level skills/`

- [ ] **Step 3: Commit (restructure only — no README)**

```bash
git add .claude-plugin/marketplace.json plugins
git commit -m "$(cat <<'EOF'
Restructure marketplace into isolated per-plugin directories

Each plugin now lives in plugins/<name>/ with its own plugin.json and
skills/ folder, and its marketplace source points at that subdirectory
instead of "./". Installing a plugin now copies only that plugin's skills
rather than the entire repo, fixing the duplicate-skill bloat (anthropics/skills#189).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 (Commit 2): Write `sync.py`

**Files:** Create `.claude/skills/sync-from-anthropic-repo/sync.py`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p .claude/skills/sync-from-anthropic-repo
```

- [ ] **Step 2: Write `sync.py`**

```python
#!/usr/bin/env python3
"""Sync skills from upstream anthropics/skills into this fork's per-plugin layout.

Upstream is the source of truth for skill *content*. This fork keeps each plugin's
skills under plugins/<plugin>/skills/<skill>/. This script maps upstream's flat
skills/<skill>/ onto that layout, never reintroducing the source:"./" duplication.

Usage:
  sync.py --plan
  sync.py --apply [--assign SKILL=PLUGIN ...] [--new-plugin PLUGIN=DESCRIPTION ...] [--delete SKILL ...]

It never commits or pushes. After --apply, review `git diff --cached` and commit.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile
from pathlib import Path

MARKER_BEGIN = "<!-- BEGIN PLUGIN-SKILLS-TABLE (auto-generated by sync-from-anthropic-repo) -->"
MARKER_END = "<!-- END PLUGIN-SKILLS-TABLE -->"

SKILL_DIR = Path(__file__).resolve().parent
STATE_PATH = SKILL_DIR / "state.json"


# ---------- repo / state ----------

def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p, *p.parents]:
        if (cand / ".claude-plugin" / "marketplace.json").is_file():
            return cand
    sys.exit("error: could not find repo root (.claude-plugin/marketplace.json)")


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


# ---------- git helpers ----------

def git(root: Path, *args: str, check: bool = True) -> str:
    res = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True)
    if check and res.returncode != 0:
        sys.exit(f"error: git {' '.join(args)} failed:\n{res.stderr}")
    return (res.stdout or "").strip()


def ensure_upstream(root: Path, remote: str, url: str) -> None:
    if remote not in git(root, "remote").splitlines():
        git(root, "remote", "add", remote, url)


def tree_sha(root: Path, ref: str, path: str) -> str | None:
    res = subprocess.run(["git", "-C", str(root), "rev-parse", f"{ref}:{path}"],
                         text=True, capture_output=True)
    return res.stdout.strip() if res.returncode == 0 else None


# ---------- layout scan ----------

def marketplace_path(root: Path) -> Path:
    return root / ".claude-plugin" / "marketplace.json"


def load_marketplace(root: Path) -> dict:
    return json.loads(marketplace_path(root).read_text())


def plugin_order(root: Path) -> list[str]:
    return [p["name"] for p in load_marketplace(root).get("plugins", [])]


def scan_plugins(root: Path):
    """Return (plugin -> sorted skills, skill -> plugin). Exit on a duplicate skill."""
    plugins_dir = root / "plugins"
    plugin_to_skills: dict[str, list[str]] = {}
    skill_to_plugin: dict[str, str] = {}
    if not plugins_dir.is_dir():
        return plugin_to_skills, skill_to_plugin
    for plugin in sorted(d.name for d in plugins_dir.iterdir() if d.is_dir()):
        skills_dir = plugins_dir / plugin / "skills"
        if not skills_dir.is_dir():
            continue
        names = []
        for sd in sorted(d.name for d in skills_dir.iterdir() if d.is_dir()):
            if not (skills_dir / sd / "SKILL.md").is_file():
                continue
            if sd in skill_to_plugin:
                sys.exit(f"error: skill '{sd}' appears in two plugins: "
                         f"{skill_to_plugin[sd]} and {plugin}")
            skill_to_plugin[sd] = plugin
            names.append(sd)
        plugin_to_skills[plugin] = names
    return plugin_to_skills, skill_to_plugin


def list_upstream_skills(root: Path, ref: str) -> list[str]:
    out = git(root, "ls-tree", "-d", "--name-only", f"{ref}:skills")
    return sorted(line.strip() for line in out.splitlines() if line.strip())


# ---------- pure logic (unit-tested) ----------

def classify(upstream: list[str], skill_to_plugin: dict[str, str],
             upstream_hash: dict, fork_hash: dict) -> dict:
    updated, new_unmapped, unchanged = [], [], []
    for name in upstream:
        if name in skill_to_plugin:
            if upstream_hash.get(name) != fork_hash.get(name):
                updated.append(name)
            else:
                unchanged.append(name)
        else:
            new_unmapped.append(name)
    removed = sorted(set(skill_to_plugin) - set(upstream))
    return {"updated": sorted(updated), "new_unmapped": sorted(new_unmapped),
            "removed_upstream": removed, "unchanged": sorted(unchanged)}


def render_table(order: list[str], plugin_to_skills: dict[str, list[str]]) -> str:
    lines = ["| Plugin | Skills |", "| --- | --- |"]
    seen = set()
    for plugin in order:
        if plugin in plugin_to_skills:
            seen.add(plugin)
            lines.append(f"| `{plugin}` | {', '.join(sorted(plugin_to_skills[plugin]))} |")
    for plugin in sorted(plugin_to_skills):
        if plugin not in seen:
            lines.append(f"| `{plugin}` | {', '.join(sorted(plugin_to_skills[plugin]))} |")
    return "\n".join(lines)


def update_readme_table(text: str, table: str) -> str:
    if MARKER_BEGIN not in text or MARKER_END not in text:
        sys.exit("error: README table markers not found; cannot update table.")
    pre, rest = text.split(MARKER_BEGIN, 1)
    _, post = rest.split(MARKER_END, 1)
    return f"{pre}{MARKER_BEGIN}\n{table}\n{MARKER_END}{post}"


def parse_kv(items: list[str]) -> dict:
    out = {}
    for it in items:
        if "=" not in it:
            sys.exit(f"error: expected KEY=VALUE, got '{it}'")
        k, v = it.split("=", 1)
        out[k.strip()] = v.strip()
    return out


# ---------- apply helpers ----------

def extract_upstream_skill(root: Path, ref: str, skill: str, dest: Path) -> None:
    """Replace dest with upstream skills/<skill> content (handles intra-skill deletions)."""
    with tempfile.TemporaryDirectory() as td:
        archive = subprocess.run(["git", "-C", str(root), "archive", ref, f"skills/{skill}"],
                                 capture_output=True)
        if archive.returncode != 0:
            sys.exit(f"error: git archive failed for {skill}:\n{archive.stderr.decode()}")
        tar = subprocess.run(["tar", "-x", "-C", td], input=archive.stdout)
        if tar.returncode != 0:
            sys.exit(f"error: tar extract failed for {skill}")
        src = Path(td) / "skills" / skill
        if not src.is_dir():
            sys.exit(f"error: extracted content missing for {skill}")
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))


def upstream_skill_description(root: Path, ref: str, skill: str) -> str:
    res = subprocess.run(["git", "-C", str(root), "show", f"{ref}:skills/{skill}/SKILL.md"],
                         text=True, capture_output=True)
    text = res.stdout if res.returncode == 0 else ""
    if text.startswith("---"):
        fm = text.split("---", 2)[1]
        for line in fm.splitlines():
            if line.strip().startswith("description:"):
                return line.split("description:", 1)[1].strip().strip('"').strip("'")
    return f"Skills plugin: {skill}"


def scaffold_plugin(root: Path, plugin: str, description: str) -> None:
    pdir = root / "plugins" / plugin
    (pdir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (pdir / "skills").mkdir(parents=True, exist_ok=True)
    manifest = {"name": plugin, "description": description,
                "author": {"name": "Anthropic", "email": "support@anthropic.com"}}
    (pdir / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    mp = load_marketplace(root)
    if not any(p["name"] == plugin for p in mp["plugins"]):
        mp["plugins"].append({"name": plugin, "description": description,
                              "source": f"./plugins/{plugin}"})
        marketplace_path(root).write_text(json.dumps(mp, indent=2) + "\n")


# ---------- orchestration ----------

def compute(root: Path, state: dict, fork_ref: str = "HEAD"):
    remote = state.get("upstream_remote", "anthropic-upstream")
    url = state.get("upstream_url", "https://github.com/anthropics/skills.git")
    branch = state.get("upstream_branch", "main")
    ensure_upstream(root, remote, url)
    git(root, "fetch", remote, branch)
    upstream_ref = f"{remote}/{branch}"
    if tree_sha(root, upstream_ref, "skills") is None:
        sys.exit("error: upstream has no top-level skills/ tree; layout may have changed. "
                 "Aborting without changes.")
    upstream = list_upstream_skills(root, upstream_ref)
    if not upstream:
        sys.exit("error: found 0 skills upstream; aborting without changes.")
    plugin_to_skills, skill_to_plugin = scan_plugins(root)
    upstream_hash = {n: tree_sha(root, upstream_ref, f"skills/{n}") for n in upstream}
    fork_hash = {n: tree_sha(root, fork_ref, f"plugins/{skill_to_plugin[n]}/skills/{n}")
                 for n in skill_to_plugin}
    cls = classify(upstream, skill_to_plugin, upstream_hash, fork_hash)
    return remote, branch, upstream_ref, cls, plugin_to_skills, skill_to_plugin


def warn_if_dirty(root: Path) -> None:
    if git(root, "status", "--porcelain"):
        print("warning: working tree is not clean; run on a clean tree for a reviewable diff.\n",
              file=sys.stderr)


def cmd_plan(root: Path, state: dict) -> None:
    warn_if_dirty(root)
    remote, branch, upstream_ref, cls, _p2s, _s2p = compute(root, state)
    last = state.get("last_synced_sha", "")
    head = git(root, "rev-parse", upstream_ref)
    print(f"Upstream {remote}/{branch} HEAD: {head}")
    print(f"Last synced:            {last or '(none)'}")
    if last and last != head:
        print("\nUpstream commits touching skills/ since last sync:")
        print(git(root, "log", "--oneline", f"{last}..{head}", "--", "skills", check=False) or "  (none)")
    for key, title in [("updated", "Updated (will sync)"),
                       ("new_unmapped", "New, unmapped (will ask)"),
                       ("removed_upstream", "Removed upstream (will ask)"),
                       ("unchanged", "Unchanged")]:
        print(f"\n{title}: {len(cls[key])}")
        for n in cls[key]:
            print(f"  - {n}")
    if not (cls["updated"] or cls["new_unmapped"] or cls["removed_upstream"]):
        print("\nAlready up to date.")


def cmd_apply(root: Path, state: dict, assigns: dict, new_plugins: dict, deletes: list[str]) -> None:
    warn_if_dirty(root)
    remote, branch, upstream_ref, cls, _p2s, skill_to_plugin = compute(root, state)
    head = git(root, "rev-parse", upstream_ref)
    for skill in assigns:
        if skill not in cls["new_unmapped"]:
            sys.exit(f"error: --assign {skill}: not a new-unmapped skill (see --plan)")
    for skill in deletes:
        if skill not in skill_to_plugin:
            sys.exit(f"error: --delete {skill}: not present in the fork")
    changed = []

    for skill in cls["updated"]:
        plugin = skill_to_plugin[skill]
        extract_upstream_skill(root, upstream_ref, skill, root / "plugins" / plugin / "skills" / skill)
        changed.append(f"~{skill}")

    for skill, plugin in assigns.items():
        pdir = root / "plugins" / plugin
        if not (pdir / ".claude-plugin" / "plugin.json").is_file():
            desc = new_plugins.get(plugin) or upstream_skill_description(root, upstream_ref, skill)
            scaffold_plugin(root, plugin, desc)
        extract_upstream_skill(root, upstream_ref, skill, pdir / "skills" / skill)
        changed.append(f"+{skill}->{plugin}")

    for skill in deletes:
        shutil.rmtree(root / "plugins" / skill_to_plugin[skill] / "skills" / skill)
        changed.append(f"-{skill}")

    p2s, _ = scan_plugins(root)
    readme = root / "README.md"
    readme.write_text(update_readme_table(readme.read_text(), render_table(plugin_order(root), p2s)))

    state["last_synced_sha"] = head
    save_state(state)

    git(root, "add", "-A", "plugins", "README.md", ".claude-plugin/marketplace.json",
        str(STATE_PATH.relative_to(root)))
    print("Changed:", ", ".join(changed) or "(none)")
    print("\nStaged:")
    print(git(root, "diff", "--cached", "--stat"))
    print("\nReview `git diff --cached`, then commit. This script does not commit or push.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--assign", action="append", default=[], metavar="SKILL=PLUGIN")
    ap.add_argument("--new-plugin", action="append", default=[], metavar="PLUGIN=DESCRIPTION")
    ap.add_argument("--delete", action="append", default=[], metavar="SKILL")
    args = ap.parse_args()

    root = find_repo_root(SKILL_DIR)
    state = load_state()
    if args.plan:
        cmd_plan(root, state)
    else:
        cmd_apply(root, state, parse_kv(args.assign), parse_kv(args.new_plugin), args.delete)


if __name__ == "__main__":
    main()
```

---

## Task 7 (Commit 2): Write `state.json`

**Files:** Create `.claude/skills/sync-from-anthropic-repo/state.json`

- [ ] **Step 1: Write the baseline state (fork HEAD == upstream HEAD today)**

```json
{
  "upstream_remote": "anthropic-upstream",
  "upstream_url": "https://github.com/anthropics/skills.git",
  "upstream_branch": "main",
  "last_synced_sha": "57546260929473d4e0d1c1bb75297be2fdfa1949"
}
```

---

## Task 8 (Commit 2): Write `test_sync.py` and run it

**Files:** Create `.claude/skills/sync-from-anthropic-repo/test_sync.py`

- [ ] **Step 1: Write the tests**

```python
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


class TestParseKV(unittest.TestCase):
    def test_ok_and_bad(self):
        self.assertEqual(sync.parse_kv(["skill=plug", "k = v "]), {"skill": "plug", "k": "v"})
        with self.assertRaises(SystemExit):
            sync.parse_kv(["noequals"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests**

```bash
python3 .claude/skills/sync-from-anthropic-repo/test_sync.py -v
```
Expected: all tests pass (OK).

---

## Task 9 (Commit 2): Write `SKILL.md`

**Files:** Create `.claude/skills/sync-from-anthropic-repo/SKILL.md`

- [ ] **Step 1: Write the skill**

````markdown
---
name: sync-from-anthropic-repo
description: Use when syncing this fork with upstream anthropics/skills — pulls the latest skill updates from upstream and re-applies them into this fork's per-plugin layout (plugins/<plugin>/skills/<skill>/) while preserving plugin separation. Triggers on "sync from upstream", "pull latest skills", "update fork from anthropics/skills".
---

# Sync From anthropic/skills

Keep this fork's skill **content** current with upstream `anthropics/skills` while
preserving the per-plugin separation (each plugin's skills live under
`plugins/<plugin>/skills/`, never a single shared `skills/` with `source: "./"`).

Upstream is the source of truth for content. This skill maps upstream's flat
`skills/<skill>/` onto the fork's per-plugin layout. It is **not** a `git merge`.

## When to use

Run when you want to pull the latest skill changes from upstream into this fork.

## How it works

`sync.py` (Python 3, stdlib only) derives the `skill → plugin` mapping from the
directory layout itself (`plugins/*/skills/*`), compares upstream vs. the fork by
git tree SHA (content-identical ⇒ skipped), and classifies every skill as
updated / new-unmapped / removed-upstream / unchanged.

## Procedure

1. **Start clean.** Ensure the working tree is clean (`git status`). The script
   warns otherwise; a clean tree gives a reviewable staged diff.

2. **Plan (read-only).**

   ```bash
   python3 .claude/skills/sync-from-anthropic-repo/sync.py --plan
   ```

   This adds/fetches the `anthropic-upstream` remote and prints the four buckets
   plus the upstream commit range since the last sync. It writes nothing.

3. **Decide, with the user, for each non-trivial bucket:**
   - **Updated** — synced automatically.
   - **New, unmapped** — ASK the user which plugin each belongs to:
     `document-skills` / `example-skills` / `claude-api` / **new plugin (type a name)** / **skip**.
     Never auto-assign. Choosing a new plugin name scaffolds it inline.
   - **Removed upstream** — ASK whether to delete from the fork or keep. Never auto-delete.

4. **Apply.** Pass the decisions as flags:

   ```bash
   python3 .claude/skills/sync-from-anthropic-repo/sync.py --apply \
     --assign <skill>=<existing-or-new-plugin> \
     --new-plugin <new-plugin>="<description>" \
     --delete <skill>
   ```

   `--assign` only accepts skills the plan listed as new-unmapped. If the target
   plugin doesn't exist yet, it is scaffolded: `plugins/<name>/.claude-plugin/plugin.json`
   + a `plugins/<name>/skills/` dir + one appended `marketplace.json` entry
   (`"source": "./plugins/<name>"`). The plugin description comes from
   `--new-plugin` if given, otherwise from the skill's own `SKILL.md`.

   `--apply` then regenerates the README Plugin↔Skills table (between its
   `PLUGIN-SKILLS-TABLE` markers), bumps `state.json`, and `git add`s the changes.

5. **Review and commit yourself.** The script never commits or pushes. Inspect
   `git diff --cached` and commit when satisfied. Suggested message:
   `Sync skills from upstream anthropics/skills (<old>..<new>)`.

## Safety properties

- Writes only: `plugins/*/skills/`, `state.json`, the README table region, and —
  only when you choose a new plugin — a new `plugins/<name>/` + `plugin.json` +
  one appended `marketplace.json` entry.
- Never edits existing plugin entries, existing `plugin.json`, README prose,
  `spec/`, `template/`, or this skill itself.
- Never commits, pushes, or force-anything.
- Aborts if upstream has no top-level `skills/` tree (layout changed) instead of
  doing damage. Idempotent: no upstream changes ⇒ "Already up to date."

## Files

- `sync.py` — the implementation.
- `test_sync.py` — unit tests (`python3 test_sync.py -v`).
- `state.json` — `{ upstream_remote, upstream_url, upstream_branch, last_synced_sha }`.
````

---

## Task 10 (Commit 2): Verify and commit the sync skill

- [ ] **Step 1: Re-run unit tests**

```bash
python3 .claude/skills/sync-from-anthropic-repo/test_sync.py -v
```
Expected: OK (all pass).

- [ ] **Step 2: Smoke-test `--plan` against real upstream**

```bash
python3 .claude/skills/sync-from-anthropic-repo/sync.py --plan
```
Expected: fetches `anthropic-upstream`, prints buckets; since fork HEAD == upstream HEAD, updated/new/removed are all 0 and it prints "Already up to date." (If upstream has advanced, it lists real changes — that's fine; do NOT apply during this verification.)

- [ ] **Step 3: Confirm the remote was added but nothing was modified**

```bash
git remote -v | grep anthropic-upstream
git status --porcelain   # expect: empty (plan writes nothing)
```

- [ ] **Step 4: Commit the sync skill**

```bash
git add .claude/skills/sync-from-anthropic-repo
git commit -m "$(cat <<'EOF'
Add sync-from-anthropic-repo skill

Local maintenance skill that pulls skill content from upstream anthropics/skills
and re-applies it into this fork's per-plugin layout, preserving separation.
Classifies skills by git tree SHA, asks before assigning new/removed skills,
regenerates the README table, and stages (never commits) for review.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11 (Commit 3): Update README

**Files:** Modify `README.md`

- [ ] **Step 1: Insert the "About This Fork" section between the badge line and `# Skills`**

Find:
```
[![skills.sh](https://skills.sh/b/anthropics/skills)](https://skills.sh/anthropics/skills)

# Skills
```
Replace with:
```
[![skills.sh](https://skills.sh/b/anthropics/skills)](https://skills.sh/anthropics/skills)

# About This Fork

This is a fork of [anthropics/skills](https://github.com/anthropics/skills) that fixes a plugin-isolation bug in the upstream marketplace.

**The problem:** upstream's `.claude-plugin/marketplace.json` sets every plugin's `source` to `"./"`, so installing *any* one plugin copies the entire repo — all 17 skills — into that plugin's cache. Installing `document-skills` and `example-skills` together loads every skill two or three times, wasting ~50k tokens of context on duplicates ([anthropics/skills#189](https://github.com/anthropics/skills/issues/189)).

**The fix:** each plugin lives in its own `plugins/<name>/` directory with its own `plugin.json`, and its marketplace `source` points at that subdirectory — so installing a plugin copies only that plugin's skills:

<!-- BEGIN PLUGIN-SKILLS-TABLE (auto-generated by sync-from-anthropic-repo) -->
| Plugin | Skills |
| --- | --- |
| `document-skills` | docx, pdf, pptx, xlsx |
| `example-skills` | algorithmic-art, brand-guidelines, canvas-design, doc-coauthoring, frontend-design, internal-comms, mcp-builder, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing |
| `claude-api` | claude-api |
<!-- END PLUGIN-SKILLS-TABLE -->

To stay current with upstream, this fork includes a local maintenance skill, `.claude/skills/sync-from-anthropic-repo`, which pulls the latest skill updates from `anthropics/skills` and re-applies them into the per-plugin layout without reintroducing the duplication.

# Skills
```

- [ ] **Step 2: Fix the moved-path links in the "About This Repository" paragraph**

Find:
```
[`skills/docx`](./skills/docx), [`skills/pdf`](./skills/pdf), [`skills/pptx`](./skills/pptx), and [`skills/xlsx`](./skills/xlsx) subfolders
```
Replace with:
```
[`document-skills/skills/docx`](./plugins/document-skills/skills/docx), [`document-skills/skills/pdf`](./plugins/document-skills/skills/pdf), [`document-skills/skills/pptx`](./plugins/document-skills/skills/pptx), and [`document-skills/skills/xlsx`](./plugins/document-skills/skills/xlsx) subfolders
```

- [ ] **Step 3: Fix the "Skill Sets" bullet that points at `./skills`**

Find:
```
- [./skills](./skills): Skill examples for Creative & Design, Development & Technical, Enterprise & Communication, and Document Skills
```
Replace with:
```
- [./plugins](./plugins): The three installable plugins (`document-skills`, `example-skills`, `claude-api`), each containing its own skills
```

- [ ] **Step 4: Verify README links and table consistency**

```bash
python3 - <<'PY'
import re, pathlib
t = pathlib.Path("README.md").read_text()
assert "# About This Fork" in t
assert "BEGIN PLUGIN-SKILLS-TABLE" in t and "END PLUGIN-SKILLS-TABLE" in t
assert "](./skills/" not in t, "stale ./skills/ link remains"
assert "[./skills]" not in t, "stale ./skills Skill Sets link remains"
for p in ["document-skills","example-skills","claude-api"]:
    assert f"`{p}`" in t
print("README OK")
PY
```
Expected: `README OK`

- [ ] **Step 5: Confirm the table matches the live layout (dry-run of the generator)**

```bash
python3 - <<'PY'
import sys, pathlib
sys.path.insert(0, ".claude/skills/sync-from-anthropic-repo")
import sync
root = pathlib.Path(".")
p2s, _ = sync.scan_plugins(root)
table = sync.render_table(sync.plugin_order(root), p2s)
readme = pathlib.Path("README.md").read_text()
block = readme.split(sync.MARKER_BEGIN,1)[1].split(sync.MARKER_END,1)[0].strip()
assert block == table, f"README table out of sync:\n--- README ---\n{block}\n--- generated ---\n{table}"
print("table matches layout")
PY
```
Expected: `table matches layout`

- [ ] **Step 6: Commit the README**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
README: explain the fork and document the per-plugin layout

Add an "About This Fork" section describing the duplicate-skill bug and the fix,
with an auto-generated Plugin/Skills table (maintained by sync-from-anthropic-repo),
and update links to the relocated skill paths.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Final verification and PR

- [ ] **Step 1: Confirm 4 commits, clean tree, validation**

```bash
git log --oneline -4
git status --porcelain   # expect empty (everything is committed)
claude plugin validate .
```
Expected: 4 commits atop main (commit 0 docs, restructure, sync skill, README); validation passes.

- [ ] **Step 2: Push the branch**

```bash
git push -u origin fix/plugin-separation-and-sync
```

- [ ] **Step 3: Open the PR against the fork's main**

```bash
gh pr create --repo spxrogers/anthropics-skills --base main \
  --head fix/plugin-separation-and-sync \
  --title "Isolate plugins into per-plugin directories + add upstream sync skill" \
  --body "$(cat <<'EOF'
## Why

Upstream's `.claude-plugin/marketplace.json` gives every plugin `"source": "./"`, so
installing any one plugin copies the whole repo (all 17 skills) into its cache —
duplicate skills and ~50k wasted context tokens (anthropics/skills#189). Confirmed
locally: the installed `document-skills` cache contained all 17 skills.

## What changed

1. **Restructure** — each plugin now lives in `plugins/<name>/` with its own
   `plugin.json`; marketplace `source` points at the subdir (auto-discovery). Installing
   a plugin copies only its own skills.
   - `document-skills` → docx, pdf, pptx, xlsx
   - `example-skills` → algorithmic-art, brand-guidelines, canvas-design, doc-coauthoring, frontend-design, internal-comms, mcp-builder, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing
   - `claude-api` → claude-api
2. **Sync skill** — `.claude/skills/sync-from-anthropic-repo/` pulls upstream skill
   updates into the per-plugin layout (content-diff by git tree SHA, asks before
   assigning new/removed skills, regenerates the README table, stages for review,
   never commits).
3. **README** — adds an "About This Fork" section + an auto-generated Plugin/Skills
   table, and fixes relocated skill links.

## Test plan

- [x] `claude plugin validate .` and each `plugins/<name>` validates
- [x] Structural assertion: each plugin's `skills/` holds exactly its declared skills; no top-level `skills/`
- [x] `python3 .claude/skills/sync-from-anthropic-repo/test_sync.py -v` passes
- [x] `sync.py --plan` runs read-only and reports "Already up to date" (fork == upstream HEAD)
- [ ] Manual: `/plugin marketplace add ./` then install `document-skills` and confirm `/context` shows only its 4 skills (not driven headlessly)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review

**Spec coverage:** Section A → Tasks 2–5; Section B → Tasks 6–10 (sync.py, state.json, tests, SKILL.md); README table sync → `update_readme_table`/`render_table` in Task 6 + Task 11 markers; Section C → Task 11; new-plugin inline scaffold → `scaffold_plugin` + `--assign`/`--new-plugin` in Tasks 6 & 9; commit/PR plan → Tasks 1, 5, 10, 11, 12; verification → Tasks 5, 8, 10, 11, 12.

**Placeholder scan:** none — all files and commands are complete.

**Type/name consistency:** `MARKER_BEGIN`/`MARKER_END` constants used in `sync.py`, `test_sync.py`, and the README match exactly. `scan_plugins` return shape (`plugin_to_skills`, `skill_to_plugin`) consistent across `compute`/`cmd_apply`/tests. CLI flags `--plan/--apply/--assign/--new-plugin/--delete` match between `main`, `SKILL.md`, and Task 11/12 usage. `state.json` keys match `compute()` defaults.
