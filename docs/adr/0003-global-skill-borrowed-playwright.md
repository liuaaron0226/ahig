# ADR-0003：`/watch-ui` 設為全域 skill，並借用既有 Playwright 安裝

- 狀態：已接受
- 日期：2026-07-31
- 情境：`/watch-ui` skill 設計

## 問題

skill 應安裝在全域（`~/.claude/skills/`）或專案內（`.claude/skills/`）？以及如何取得 Playwright？

## 決策

全域安裝。Playwright npm 套件借用 `C:\Users\User\Desktop\project-golem\node_modules`，不在 skill 目錄重複安裝。

## 理由

1. **驗證需求是跨專案的。** 微網站散落在 `bixlink-sodium-site`、`bixlink-battery-site`、`grad-exam-hub/site` 等多處，且全域 CLAUDE.md 已將「做完 UI 就實際打開驗證」定為通則。工具鎖在單一 repo 與該通則矛盾。

2. **瀏覽器本體已是系統層共用。** Chromium 與 ffmpeg 位於 `C:\Users\User\AppData\Local\ms-playwright\`，非專案私有。重複安裝的只會是 npm 套件層（數百 MB），收益低。

## 後果

- skill 內含一個指向 `project-golem/node_modules` 的硬編碼路徑。這是刻意的簡化，程式碼中以 `ponytail:` 註解標明上限與升級路徑。
- **若 `project-golem` 被移動、刪除或清空 `node_modules`，`/watch-ui` 會失效。** 全域 CLAUDE.md 已將 `project-golem` 列為禁止搬移路徑，此風險可接受。
- 升級路徑：改為搜尋多個候選路徑，或在 skill 目錄自帶最小安裝。

## 已考慮但未採用

**skill 目錄自帶 npm 安裝**：多佔數百 MB、多一份版本要維護，而瀏覽器本體仍是共用的——重複的只有薄薄一層 JS API。
