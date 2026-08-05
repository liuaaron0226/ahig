## Review Workflow

Before starting any non-trivial code change, write a short spec first so review has something to check against. After the change, run a review before asking for final human review.

Recommended flow:

1. Spec: write 3-6 lines covering what the change should do, the boundary cases, and what "done" looks like. Skip this for trivial fixes (typos, one-line changes, config tweaks).
2. Make the change against that spec.
3. Run the narrowest useful local checks.
4. Run `/review` in Claude Code to review the change - check it against the spec from step 1, not just general code quality.
5. If the review finds a real issue, fix it and re-run review.

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature>/` (no git remote). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
