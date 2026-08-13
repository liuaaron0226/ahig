# 10 health-data-git-tracked

Status: ready-for-human
Blocked by: —

## 事實

`health/` 底下的個人健康紀錄目前**在 git 追蹤中**。至少包含：

- `health/profile.md` — 初診基線（身高體重、目標、飲食限制、作息）
- `health/log/2026-08.md` — 每日睡眠／飲食／心情流水
- `health/減重方案.md`、`health/行動總表.md`、`health/身體部位對照.html`（未追蹤但在同一目錄）

這不是 AHIG 造成的，是既有狀態。ADR-0006 只界定了 `ahig/` 的公開／私密邊界，
沒有處理這批已進版控的檔案。

## 為什麼需要人來決定

三個可能的處置各有不可逆的代價：

1. **維持現狀** — 若這個 repo 永遠不推到任何遠端，風險僅限於本機與備份。
   代價是「哪天想開源某個子目錄」時會發現整段歷史都帶著健康資料。
2. **`git rm --cached` + `.gitignore`** — 從此不再追蹤，但**歷史 commit 裡仍有全部內容**。
   看起來乾淨、實際沒清掉，是最容易誤以為已解決的選項。
3. **歷史重寫**（`filter-repo` / `filter-branch`）— 真的清掉，但會改寫所有 commit
   hash。若有任何 clone、備份或分支基於現有歷史，全部失效。

還有一個前置問題：**這個 repo 有沒有遠端？** 有的話，資料是否已經推上去，
會直接改變 1 與 2 的風險評估。

## 需要的決定

- 這個 repo 現在或未來會不會有遠端（GitHub 等）？
- 若要處理，接受哪一種代價：不動、停止追蹤但留歷史、或重寫歷史？

## 明確不做

在收到明確指示前，**不執行** `git rm`、不刪除、不重寫歷史、不改 `.gitignore`。
這類操作不可逆，且 `health/` 是使用者每天在用的活資料。

## Comments

- 2026-08-13：已唯讀查證目前 repo 沒有任何 `remote.*` 設定，三個本機 branch 也都沒有 upstream。`health/profile.md` 與 `health/log/2026-08.md` 自 commit `f1ea2fe` 起被追蹤。這只能證明**現況未連遠端**，不能證明過去從未設定或推送；議題維持 `ready-for-human`。
