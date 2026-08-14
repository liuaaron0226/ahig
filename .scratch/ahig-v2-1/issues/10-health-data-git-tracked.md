# 10 health-data-git-tracked

Status: done
Blocked by: —
Resolved: 2026-08-14（擁有者拍板，選項 2）

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

- 2026-08-14：**前一則的前置假設已經不成立。** repo 現在有遠端
  `https://github.com/liuaaron0226/ahig.git`，且 `health/` 已隨 9 條
  `origin/claude/*` 分支推上 GitHub（各 14 筆）。`origin/main` 與
  `origin/master` 乾淨（0 筆）。查證：repo 為 **private**（匿名存取回 404），
  帳號下的 public repo 只有 `chromatic-glass-design` 與 `WebDesign`，
  **未外洩**。

- 2026-08-14 **擁有者裁定：採選項 2（停止追蹤，不改歷史）**。

  否決選項 3（歷史重寫）的決定性理由：**AHIG 的抽樣證據用 git 歷史當防竄改
  錨定**（`anchors.jsonl`，見狀態快照「commit+push 後竄改需改寫遠端歷史」）。
  改寫歷史正是這套機制定義的「竄改」動作，會讓已結案的 audit
  `22f634d2325d` 證據鏈失效。次要理由：`f1ea2fe` 在主幹深度 48、8 條分支
  全部要 force-push、3 個活躍房間的 local clone 全數作廢、GitHub 上的舊物件
  仍需另開 support ticket 才會真正消失。

  接受的代價（明講，不要之後誤以為已清乾淨）：**歷史 commit 裡仍有全部內容**。
  這個 repo 因此**永遠不能直接轉 public**；要開源只能抽子集到新 repo。

  已執行：
  1. `health/` 就地 `git init` 成獨立 repo（25 個檔案，比原本追蹤的 14 個更完整
     ——`減重方案.md`、`行動總表.md`、`身體部位對照.html` 之前根本沒進版控），
     推到自己的 private repo。
  2. 本 repo `git rm -r --cached health/` ＋ `.gitignore` 加 `health/`。
  3. 看板公告請各房 fetch+merge 主幹。

  遺留注意事項：在各房把主幹合併進來之前，切到舊分支會讓 git 用舊版
  `health/*` 覆蓋本機檔案（因為已 ignore，git 會靜默覆寫）。`health/` 自己的
  git repo 是這個情況的救援管道。
