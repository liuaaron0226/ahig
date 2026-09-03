## 交付給擁有者的格式：一律 HTML

**🚫 不要給擁有者 `.md` 檔。** 他看不了原始 markdown——⚠️ 交出去的東西他打不開，
等於沒交。決策卡、報告、任何要他讀的東西，**一律 HTML**：
發布成 Artifact 給他連結，或給一個可直接開的 `.html`。

⚠️ 本條已被違反過兩次（決策卡 001、002 都是先給了 `.md`）。

✅ **內部文件不受此限**：看板、ADR、契約、`scope-extensions-required.md`
等只給機器與 session 讀的東西，維持 markdown。

## Multi-session coordination

AHIG 專案有多個 session 並行。開工前先讀 `COORDINATION.md`：
分支規則、工作線登記、協調者聯絡方式都在那裡。主幹是
`feature/istudy-private-backup-workflow`，不要直接推主幹。

⚠️ **看板有兩份**：根目錄那份是第 598 輪以前的歷史（🚫 不再追加）；
**現行看板是 `ahig/COORDINATION.md`**。

## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature>/` (no git remote). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
