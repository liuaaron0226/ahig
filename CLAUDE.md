## 交付給擁有者的格式：一律 HTML

**🚫 不要給擁有者 `.md` 檔。** 他看不了原始 markdown——⚠️ 交出去的東西他打不開，
等於沒交。決策卡、報告、任何要他讀的東西，**一律 HTML**：
發布成 Artifact 給他連結，或給一個可直接開的 `.html`。

⚠️ 本條已被違反過兩次（決策卡 001、002 都是先給了 `.md`）。

✅ **內部文件不受此限**：看板、ADR、契約、`scope-extensions-required.md`
等只給機器與 session 讀的東西，維持 markdown。

## 擁有者提出新問題時

**看 `docs/new-question-recipe.md`——那是唯一的一份做法。**
🚫 不要為新領域另寫一份 protocol（⚠️ 先前三個領域各寫一份，三份都過期了）。

⚠️ **現況**（ADR-0017）：三題已答完並收工。**🚫 「讀原始論文」那條路目前不可用**
——它已知會宣稱文件裡不存在的數值。**✅ 新問題預設停在「盤點既有回顧」**，
🚨 三次實測都停在那裡就足夠。

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

⚠️ **但 `CONTEXT.md` 不是 AHIG 的**：它是這個工作區其他專案（Claude 工具與微網站）
的詞彙表（Evidence Report、Detail Mode、`/watch`）。🚫 不要照它的用語做 AHIG 的事。
**✅ AHIG 的決策紀錄是 `docs/adr/0006`–`0016`**（`0001`–`0005` 亦屬別的專案）。

⚠️ **讀 ADR 之前先看它的 front-matter**：被後續 ADR 取代的條文都標了
「⚠️ 部分已被取代」與取代它的編號。🚨 `0010` 的 M1 定義、`0011` 的領域順序與
P1 題目、`0012` 的 P1 問題框架與順序，**都已經不是現行的**。
