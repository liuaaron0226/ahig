## Multi-session coordination

AHIG 專案有多個 session 並行。開工前先讀 repo 根目錄的 `COORDINATION.md`：
分支規則、工作線登記、協調者聯絡方式都在那裡。主幹是
`feature/istudy-private-backup-workflow`，不要直接推主幹。

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature>/` (no git remote). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
