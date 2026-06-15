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

## Fork-specific marketplace.json divergence

`.claude-plugin/marketplace.json` has two fields that intentionally diverge from
upstream and must survive every sync:

- `name`: `spx-ant-agent-skills` — upstream uses `anthropic-agent-skills`, a
  **reserved** name only `github.com/anthropics/*` repos may register. A fork
  must use a non-reserved name or `plugin marketplace add` is rejected.
- `owner`: `Steven R. <contact@spxrogers.com>` — the fork maintainer, not the
  upstream Anthropic owner block.

Because upstream is the source of truth for *content* only, the script guards
these explicitly (constants `FORK_MARKETPLACE_NAME` / `FORK_MARKETPLACE_OWNER`):
`--plan` warns if either has drifted from the fork value; `--apply` re-asserts
both (preserving key order and the `plugins` list) so a wholesale upstream
`marketplace.json` can never silently clobber the fork's identity. If you ever
change the marketplace name or owner, update those two constants to match.

## Safety properties

- Writes only: `plugins/*/skills/`, `state.json`, the README table region,
  `marketplace.json` (re-asserting the fork `name`/`owner` and, only when you
  choose a new plugin, one appended plugin entry), and — for a new plugin — a new
  `plugins/<name>/` + `plugin.json`.
- Never edits existing plugin entries, existing `plugin.json`, README prose,
  `spec/`, `template/`, or this skill itself.
- Never commits, pushes, or force-anything.
- Aborts if upstream has no top-level `skills/` tree (layout changed) instead of
  doing damage. Idempotent: no upstream changes ⇒ "Already up to date."

## Files

- `sync.py` — the implementation.
- `test_sync.py` — unit tests (`python3 test_sync.py -v`).
- `state.json` — `{ upstream_remote, upstream_url, upstream_branch, last_synced_sha }`.
