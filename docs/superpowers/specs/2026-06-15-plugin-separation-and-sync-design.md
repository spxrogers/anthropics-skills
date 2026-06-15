# Plugin Separation + Upstream Sync — Design

**Date:** 2026-06-15
**Repo:** `spxrogers/anthropics-skills` (fork of `anthropics/skills`)
**Status:** Approved design, pending spec review

> Note: this spec and its companion plan are committed as **commit 0** of the PR
> (a "superpowers docs" commit), ahead of the three functional commits, so the
> design rationale travels with the change.

## Problem

This fork is a Claude Code plugin marketplace. Upstream `.claude-plugin/marketplace.json`
gives all three plugins (`document-skills`, `example-skills`, `claude-api`) a
`"source": "./"`. Claude Code copies a plugin's entire `source` directory into its
cache, so `"./"` copies the whole repo — all 17 skills — into **every** plugin's
cache. Installing more than one plugin loads each skill two or three times,
wasting ~50k tokens of context on duplicates.

Confirmed empirically: the installed `document-skills` cache at
`~/.claude/plugins/cache/anthropic-agent-skills/document-skills/<v>/skills/`
contains all 17 skills, not the 4 it declares. Matches upstream issue
[anthropics/skills#189](https://github.com/anthropics/skills/issues/189) and
PR [#551](https://github.com/anthropics/skills/pull/551).

The declared `skills` arrays + `strict: false` do not prevent this: the
conventional top-level `skills/` directory is copied wholesale and auto-discovered.

## Decisions (locked)

1. **Layout:** canonical `plugins/<name>/` with a per-plugin `plugin.json`,
   skills auto-discovered, `strict` default (true) — matches `claude-plugins-official`.
2. **PR target:** `spxrogers/anthropics-skills:main` (the fork).
3. **Re-point local marketplace:** No. The PR is the deliverable; user re-points later.
4. **New unmapped skill during sync:** flag and ask — never auto-assign. Options:
   `document-skills / example-skills / claude-api / new plugin (type name) / skip`.
   Picking *new plugin* inline-scaffolds it. Changes always left staged for review;
   never auto-committed.
5. **README table** is kept current by the sync skill (auto-generated region).

## Section A — Repository restructure (commit 1)

Target layout (clean 1:1 partition of all 17 skills; `git mv` to preserve history):

```
.claude-plugin/marketplace.json     # source → ./plugins/<name>; drop strict + skills arrays
plugins/
  document-skills/.claude-plugin/plugin.json
  document-skills/skills/   docx, pdf, pptx, xlsx                          (4)
  example-skills/.claude-plugin/plugin.json
  example-skills/skills/    algorithmic-art, brand-guidelines, canvas-design,
                            doc-coauthoring, frontend-design, internal-comms,
                            mcp-builder, skill-creator, slack-gif-creator,
                            theme-factory, web-artifacts-builder, webapp-testing (12)
  claude-api/.claude-plugin/plugin.json
  claude-api/skills/        claude-api                                      (1)
spec/        # unchanged (Agent Skills spec, not a plugin)
template/    # unchanged (skill template)
README.md THIRD_PARTY_NOTICES.md .gitignore   # unchanged in commit 1
```

Each marketplace entry:
```json
{ "name": "document-skills",
  "description": "...",
  "source": "./plugins/document-skills" }
```
`strict: false` and the `skills` arrays are removed. marketplace.json is normalized
to 2-space indent (`json.dump`) so the sync script can edit it programmatically later.

Each `plugin.json` (minimal; matches `agent-sdk-dev`):
```json
{ "name": "document-skills",
  "description": "...",
  "author": { "name": "Anthropic", "email": "support@anthropic.com" } }
```
No `version` → SHA-based versioning preserved (every commit = update).

**Marketplace name** stays `anthropic-agent-skills`. It is a reserved name (claude.ai
sync would reject a third-party marketplace using it), but it works for a personal
fork installed locally and keeps the existing install path intact. Noted, not changed.

## Section B — Sync skill `.claude/skills/sync-from-anthropic-repo/` (commit 2)

**Model:** upstream is source of truth for skill *content*; the fork applies a
deterministic *separation transform*. Sync is not `git merge` — it maps upstream's
flat `skills/<x>/` into the fork's `plugins/<p>/skills/<x>/`.

**Files**
- `SKILL.md` — procedure + safety rules + the question wording.
- `sync.py` — Python 3 stdlib only (no installs). Deterministic fetch/diff/copy.
- `state.json` — `{ "upstream_remote": "anthropic-upstream",
  "upstream_url": "https://github.com/anthropics/skills.git",
  "upstream_branch": "main",
  "last_synced_sha": "57546260929473d4e0d1c1bb75297be2fdfa1949" }`.

**Mapping = the layout.** `sync.py` derives `skill → plugin` by scanning
`plugins/*/skills/*`. No separate config. A skill found under two plugins is an error.

**Flow**
1. Preconditions: warn if working tree dirty; verify fork (marketplace.json sources are
   `./plugins/...`). Abort if upstream `skills/` has 0 entries (layout changed upstream).
2. `sync.py --plan` (read-only): ensure remote `anthropic-upstream`, `git fetch`,
   classify each upstream skill by **content** vs the fork:
   - **updated** (mapped skill changed), **new-unmapped**, **removed-upstream**, **unchanged**.
   Print plan + upstream commit range `git log last_synced..HEAD -- skills/`.
3. Review with user. Updated→sync automatically. New-unmapped→ask
   (`document-skills / example-skills / claude-api / new plugin (type name) / skip`).
   Removed-upstream→ask delete-or-keep. Never auto-decide.
4. `sync.py --apply --assign <skill>=<plugin> ... --delete <skill> ...`:
   - Replace mapped skill dirs from upstream via `git archive <ref> skills/<x> | tar`
     (handles intra-skill file deletions).
   - Place assigned skills. If `<plugin>` does not exist, scaffold it:
     `plugins/<plugin>/.claude-plugin/plugin.json` (name + Anthropic author;
     description from the skill's `SKILL.md` frontmatter or asked) and append one
     marketplace.json entry `"source": "./plugins/<plugin>"`.
   - Apply chosen deletions.
   - Regenerate the README Plugin↔Skills table between its markers from the actual
     `plugins/*/skills/*` layout (plugins in marketplace.json order, skills alphabetical).
   - Bump `state.json.last_synced_sha` to upstream HEAD.
   - `git add` the changes. **No commit. No push.**
5. Print summary + suggested commit message. User reviews `git diff --cached` and commits.

**Safety (explicit).** Writes only: `plugins/*/skills/`, `state.json`, the README
table region (between markers), and — only when the user chooses *new plugin* — a new
`plugins/<name>/` + `plugin.json` + one appended marketplace.json entry. Never edits
existing plugin entries / existing plugin.json / README prose / spec/ / template/ /
itself. Never commits, pushes, or forces. Idempotent: no upstream changes → "up to date."

## Section C — README (commit 3)

Add an **About This Fork** section right after the badge, before `# Skills`:
explains the `source: "./"` bug, links #189, and presents the Plugin↔Skills table
wrapped in auto-generation markers:

```
<!-- BEGIN PLUGIN-SKILLS-TABLE (auto-generated by sync-from-anthropic-repo) -->
| Plugin | Skills |
| --- | --- |
| `document-skills` | docx, pdf, pptx, xlsx |
| `example-skills` | algorithmic-art, brand-guidelines, canvas-design, doc-coauthoring, frontend-design, internal-comms, mcp-builder, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing |
| `claude-api` | claude-api |
<!-- END PLUGIN-SKILLS-TABLE -->
```
Also fix the moved-path links (`./skills/docx` → `./plugins/document-skills/skills/docx`,
`./skills` references). All README edits live in commit 3.

## Commit / PR plan

- Branch `fix/plugin-separation-and-sync` off `main`.
- Commit 0: superpowers docs (this spec + the implementation plan).
- Commit 1: restructure (git mv + 3 plugin.json + marketplace.json). No README.
- Commit 2: `.claude/skills/sync-from-anthropic-repo/` (SKILL.md, sync.py, state.json).
- Commit 3: README (path fixes + About This Fork + marker-wrapped table).
- PR against `spxrogers/anthropics-skills:main`.

## Verification (before claiming done / opening PR)

- `claude plugin validate .` passes (CLI present: v2.1.177).
- Structural assertions: each `plugins/<name>/skills/` contains exactly its declared
  skills and nothing else; no top-level `skills/` remains; all 17 skills accounted for.
- `sync.py --plan` against current upstream prints "up to date" (fork HEAD == upstream HEAD).
- README table markers present and table matches the layout.
- Honest reporting: the interactive `/plugin marketplace add` install test can't be
  driven headlessly; will state that explicitly rather than claim it was run.

## Out of scope

- Re-pointing the local marketplace (decision #3).
- A separate PR to upstream anthropics/skills (decision #2; can be done later).
- Syncing commands/agents — this repo ships skills only.
