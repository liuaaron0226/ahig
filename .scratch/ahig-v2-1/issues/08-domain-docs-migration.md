# 08 domain-docs-migration

Status: done
Blocked by: 02, 03, 04, 05, 06, 07

## 目標

建立 context、ADR、migration 與敏感資料追蹤 issue。

## 產出

Repo 根目錄：

- `CONTEXT-MAP.md` — 三個 context（工作區核心／Trading Desk／AHIG）分流，
  並列出跨 context 會誤讀的詞（證據、驗證、coverage）
- `docs/adr/0006-ahig-public-private-split.md` — 系統層級的公開／私密邊界

AHIG 內部：

- `ahig/docs/adr/0001` SHACL Core／SPARQL／確定性 gate 的責任邊界
- `ahig/docs/adr/0002` OutcomeInventory 的 draft/scoped lifecycle
- `ahig/docs/adr/0003` 確定性裁決只做可驗真的消解
- `ahig/docs/adr/0004` GRADE indicators → 人類判斷 → 確定性聚合
- `ahig/docs/adr/0005` 精確品質閘門與契約凍結前置檢查
- `ahig/docs/architecture/AHIG-contract-v2.1.md`
- `ahig/docs/migrations/v2-to-v2.1.md`
- `ahig/README.md` 改寫

追蹤：

- `.scratch/ahig-v2-1/issues/10-health-data-git-tracked.md`（ready-for-human）

## Comments

- 每份 ADR 記錄的是「為什麼不採用那個看起來更明顯的做法」，且都指向本機
  實測推翻 v2 的具體證據，而非設計意圖的重述。
- `health/` 私密檔已被 git tracking 屬既有事實，本票只記錄不處理——
  untrack／刪除／歷史重寫皆不可逆，需使用者決定。
