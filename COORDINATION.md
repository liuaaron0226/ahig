# AHIG 多 session 協調看板

多個 Claude session 並行處理 AHIG 專案時的共享狀態。**git 是唯一可靠的共享事實**：
每個 session 開工先 `git fetch`，收工必 push。

## 協調者

- Session：**AHIG 協調中心（coordinator）**，ID `session_01GJ7jGHfPUahTcKWwDd9Gcu`
  ——這是**雲端** session（`https://claude.ai/code/session_01GJ7jGHfPUahTcKWwDd9Gcu`）。
- 對齊方式：**更新本檔你那條工作線的狀態列並 push**，協調者會拉下來看。
- ⚠️ 本地 session 的訊息工具**傳不到**協調者。本地 session 管理工具查上述 ID 會回
  `Session not found`（實測），因為它查的是本地 session 清單，看不到雲端 session。
  除非你自己也在雲端，否則不要以為訊息送得到——一律走 push 這條路。

## 分支規則

- 主幹：`feature/istudy-private-backup-workflow`。**不要直接推主幹**，合回主幹由協調者做。
- ⚠️ `main` 與 `master` 都已廢棄：**不要從它們開分支，也不要合進去**。
  `origin/HEAD` 目前仍指向 `main`，所以照直覺跑 `git checkout main` 會拿到一個
  只有 `Initial commit`、幾乎是空的 repo；`master` 是舊主幹，停在 2026-07-18。
  真正有內容的只有上面那條主幹（領先 `main` 二十幾個 commit）。
- 每條工作線一個分支，從主幹建：
  `git fetch origin && git checkout -B <你的分支> origin/feature/istudy-private-backup-workflow`
- push 前必須全綠：`cd ahig && python tests/run_tests.py && python -m ahig.cli verify --all`
- 只改自己工作線範圍內的檔案；要跨線改動先找協調者。
- AHIG 程式與測試都在 `ahig/` 子目錄；repo 根目錄還有其他專案（BixLink、
  trading-desk、health…），一律不要動。

## 專案狀態快照（協調者維護）

截至 `a912678`（2026-08-13）：

- ✅ fail-open 修復已合併：四來源 normaliser 全通、契約外來源硬失敗、
  `completeAcrossContractSources` 逐來源檢查（`ahig/search/candidates.py`）
- ✅ 雙盲 screening 對帳、PRESS 審查文件已入庫
- ✅ S2 母體抽查工具完成（`ahig/search/prevalence_audit.py`）
- ⏳ 等人工：50 篇 TT 摘要判讀（`prevalence_audit sample` → 回填 → `estimate`）
- ⏳ 待決策（依序）：①「篩完才能抽」blocker 是否鬆綁（抽樣框升版）
  ② S2 解法（A/B/C/D）③ `analysis/human_throughput.py` 以實測重校
- 測試基準：526/526、verify 10/10

## 工作線

開工先把自己那條登記進表格並 push，完成或卡住時回來更新狀態。**新列一律附在表尾**，
只改自己那一列。

本檔是每條工作線都會改的檔案，撞 conflict 是常態而非意外。撞到時：

```bash
git pull --rebase origin feature/istudy-private-backup-workflow
```

rebase 停下來時，**保留別人的所有列，把自己那一列重新附到表尾**即可。不要用
`--ours` / `--theirs` 整塊覆蓋——那會直接吃掉別人的登記，而且沒人看得出來少了什麼。

| 工作線 | 分支 | Session | 狀態 |
|---|---|---|---|
| 協調・合併・S2 決策支援 | `claude/fail-open-bug-merge-kmifpb` | AHIG 協調中心（coordinator） | 進行中 |
| 協調看板缺口修補（衝突規則・協調者可達性・廢棄分支警告） | `claude/coordination-board-gaps` | 本地 session（Claude Code 桌面） | 進行中 |
