# AHIG 多 session 協調看板

多個 Claude session 並行處理 AHIG 專案時的共享狀態。**git 是唯一可靠的共享事實**：
每個 session 開工先 `git fetch`，收工必 push。

## 協調者

- Session：**AHIG 協調中心（coordinator）**，ID `session_01GJ7jGHfPUahTcKWwDd9Gcu`
- 對齊方式（擇一）：
  1. 用 session 間訊息工具（SendMessage / claude-code-remote）傳給上述 session；
  2. 更新本檔你那條工作線的狀態列並 push（協調者會拉下來看）。

## 分支規則

- 主幹：`feature/istudy-private-backup-workflow`。**不要直接推主幹**，合回主幹由協調者做。
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

| 工作線 | 分支 | Session | 狀態 |
|---|---|---|---|
| 協調・合併・S2 決策支援 | `claude/fail-open-bug-merge-kmifpb` | AHIG 協調中心（coordinator） | 進行中 |
| （新工作線由協調者或開線 session 在此登記） | | | |
