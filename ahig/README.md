# AHIG

Athlete Health Intelligence Graph（AHIG）的公開契約、驗證器、虛構 fixtures 與校準契約。

本目錄不保存個人健康紀錄、論文全文、真實研究資料庫、索引、NotebookLM 執行結果
或秘密。私有資料命令只接受由 `AHIG_PRIVATE_ROOT` 指向的外部資料根；公開驗證
不需要該環境變數。

## 驗證

```bash
python -m ahig.cli verify --all
```

十個階段，由便宜到昂貴：執行環境 → JSON Schema → Registry → SHACL canary →
交付物驗證 → 單元與整合測試 → B.11 凍結契約 → 端到端貫穿 → 數字對帳 →
私密資料掃描。前面的階段失敗時，後面的失敗多半是衍生的。

無 pytest 時仍可單獨執行測試（本專案的測試檔是標準 pytest 格式，但不依賴它）：

```bash
python tests/run_tests.py
python tests/run_tests.py tests/test_b11_calibration.py    # 單一檔案
```

## 目錄

| 路徑 | 內容 |
|---|---|
| `ahig/` | 程式：contracts（凍結）、scope（lifecycle 與比對）、stats（裁決、GRADE、確定性檢查）、gates（SHACL、品質閘門、verify --all） |
| `schema/` | JSON Schema 2020-12。條件式規則寫在 schema 裡，不只是註解 |
| `shapes/core/` | SHACL 1.0 Core，結構性阻擋，零 `sh:sparql` |
| `shapes/sparql/` | SHACL-SPARQL，pinned audit profile，**不是唯一安全防線** |
| `shapes/canaries/` | negative／positive 對照。negative 必須 `conforms=false` 且命中指定 shape |
| `registry/` | 量綱與 MID 註冊表。`quantity-kinds.*.json` 會被合併成單一命名空間 |
| `calibration/` | 凍結的校準契約與抽樣框。目前只有 B.11 碳水化合物策略 |
| `analysis/` | 人力與抽樣的情境模型；產物在 `analysis/results/` |
| `tests/` | 單元、整合、canary 與端到端貫穿 |
| `docs/` | 見下 |

## 文件

- **`CONTEXT.md`** — 詞彙表。用語不一致時以它為準。
- **`docs/adr/`** — AHIG 內部的架構決策。每一份記錄的是「為什麼不用那個看起來
  更明顯的做法」，多數源於本機實測推翻了 v2 的設計。
- **`docs/architecture/AHIG-contract-v2.md`** — v2 原件，不覆寫。
- **`docs/architecture/AHIG-contract-v2.1.md`** — 現行契約。
- **`docs/migrations/v2-to-v2.1.md`** — 手上有 v2 資料或實作時的遷移步驟。

系統層級（跨 context）的決策在 repo 根目錄的 `docs/adr/`，見根目錄
`CONTEXT-MAP.md`。

## B.11 公開 metadata 搜尋

SearchContract 已凍結。搜尋輸出只寫入 `AHIG_PRIVATE_ROOT`，不進 repo：

```bash
# 先預覽，不需私有根也不寫檔
python -m ahig.search.runner --dry-run

# 先在目前 shell 設定 AHIG_PRIVATE_ROOT 指向 repo 外的私有資料根，
# 再執行公開、不需帳號的來源
python -m ahig.search.runner \
  --only europe-pmc --only clinicaltrials-gov --run-id b11-initial

# PubMed 另需 AHIG_CONTACT_EMAIL；OpenAlex 另需 OPENALEX_API_KEY
python -m ahig.search.runner --only pubmed --run-id b11-initial
python -m ahig.search.runner --only openalex --run-id b11-initial

# 已完成來源會跳過；--redo 會封存舊嘗試後重跑
python -m ahig.search.runner --only europe-pmc --run-id b11-initial --redo
```

runner 只抓公開 metadata，不下載全文、不呼叫 NotebookLM。每一頁保存原始 HTTP body、
headers、status、final URL（敏感 query 參數遮罩）、checksum 與 request manifest；
API 宣告的 total count 與實際保留筆數不一致時，來源標 `failed` 而非 `completed`。

## 目前的狀態

v2.1 契約核心已完成並可在原生 Windows 完整驗證。B.11 的 Search → Scope → strata
契約鏈與 60 篇分層抽樣框已凍結；SearchContract 仍標記 `notPRESSReviewed`，
known-item seed set 尚未建立，因此允許探索／校準搜尋，但 Approved Claim 被阻擋。

**尚未取得任何文獻全文。** 所有 `midRef` 為 `null`，未登錄文獻型 MID，也尚未
產生任何 Approved Claim。
