# Agent notes for sil-lift

Read and follow [CONTRIBUTING.md](CONTRIBUTING.md) in full — its byte-exact
corpus rules and fidelity contract are essential to avoid silently breaking this
repo.

Not covered there:

- No remote actions without asking the user first — no push, repo or project
  creation, issue or PR creations, PyPI publishing, or posting anywhere.
- No destructive actions ever — no force push, branch deletion, or changing repo
  settings.
- Commit messages describe the commit's diff and stand on their own. Do not
  reference conversation, tasks, audits, review rounds, or other outside context
  ("as requested", "fixes audit finding", "per feedback") — a reader with only
  the diff should understand the message fully.
- Root-level prose docs (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, this
  file) are hard-wrapped, so a bare Markdown list marker (`+`, `-`, `*`) can be
  pushed to the start of a re-wrapped line and render as a stray bullet. Where
  that can bite — e.g. `sort \+ save` in the changelog — the marker is
  backslash-escaped on purpose; keep the `\`. `docs/en/` is not hard-wrapped
  (one line per paragraph), so it uses no such escaping.
