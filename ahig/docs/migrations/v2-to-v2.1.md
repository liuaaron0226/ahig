# AHIG v2 → v2.1 遷移指南

## 1. 誰需要讀這份文件

手上有以下任一項的人：

- 依 v2 `outcome-inventory.schema.json` 產出的 OutcomeInventory 實例
- 依 v2 `mid-registry.schema.json` 登錄的 MID 項目
- 直接引用 `shapes/ahig-patch-v2.shacl.ttl` 的驗證流程
- 呼叫 v2 `reference-impl/` 五個模組的程式
- 依 v2 `analysis/results/*.json` 欄位名做報表的下游

**若你只有 v2 的文件而沒有資料或程式**，可以跳過第 3 節，只讀第 4 節（被推翻的宣稱）。

### 前提

- Python 3.11、`jsonschema`、`numpy`、`scipy`、`rdflib`、`pyshacl 0.40.1`（版本被釘住，見 3.4）
- v2 原件保存在 `docs/architecture/AHIG-contract-v2.md`，**未被覆寫**。遷移過程隨時可回頭對照。
- 遷移是單向的。v2.1 的 OutcomeInventory 實例無法通過 v2 schema 驗證（多了 `lifecycle` 等未宣告欄位，v2 為 `additionalProperties: false`）。

---

## 2. Breaking changes 一覽

| # | 項目 | v2 | v2.1 | 不遷移的後果 |
|---|---|---|---|---|
| B1 | `outcome-inventory.schema.json` | `1.0.0` | `2.0.0` | 既有實例一律驗證失敗（缺 `lifecycle`、`completenessAttestation`） |
| B2 | inventory lifecycle | 無此概念，`scopeDecision` 為每項必填 | `draft`／`scoped` 兩態，draft 禁止攜帶 `scopeDecision` | 模型可自行填寫範圍判定，範圍契約形同虛設 |
| B3 | `scopeDecision` | 只需 `inScope` + `reasonCode` | 另需 `ruleId`、`matchedScopeElements` 五軸、`decidedBy.agentClass = "deterministic"` | 排除決定無法回溯到具名規則，稽核時無從判斷是規則還是人為 |
| B4 | `completenessAttestation` | 選填、無結構要求 | **必填**，且必含 `harmsScan` | harms 漏抽無法被偵測；「沒有 harm」與「沒去找 harm」不可區分 |
| B5 | `registryComparison.status = "compared"` | 只需 `status` | 另需 `registryId`、`registryRetrievedAt`、`registryPrimaryOutcomes`、`outcomeSwitchingFlags` 四欄 | 空 inventory 標 `compared` 即可通過驗證（v2 實測缺陷） |
| B6 | outcome switching flag 非空 | 僅文字描述「不得由模型單獨判定」 | schema 強制 `createdBy.dualExtracted = true` | 描述沒有執行力，單模型判定可通過 |
| B7 | `mid-registry.schema.json` | `value` 為必填 | 新增 `status: "unavailable"`；該狀態下 `value` **禁止**出現，改填 `unavailableReason` | 為了填滿必填欄位而捏造 MID magnitude，使 imprecision 評級看似 contextualised |
| B8 | SHACL | 單檔 `shapes/ahig-patch-v2.shacl.ttl` | 拆為 `shapes/core/ahig-core.shacl.ttl`（Core-only）與 `shapes/sparql/ahig-v2.1.shacl.ttl`（audit profile） | 引用舊路徑的流程直接找不到檔案 |
| B9 | 量綱註冊表 | 單檔 `quantity-kinds.sport-science.json` | `registry/quantity-kinds.*.json` 多檔合併為單一命名空間；ID 碰撞拋 `QuantityKindCollision` | 領域註冊表新增後裁決層看不到，`blockingConditions` 靜默失效 |
| B10 | `grade.propose_certainty()` | 產出 `certainty`，可直接使用 | 降級為相容 wrapper，只回 `advisoryCertainty`，`effectiveCertainty` 恆為 `None` | 呼叫端拿到 `None` 而非等級字串；未檢查即使用會 `KeyError` 或誤判為未評級 |
| B11 | GRADE 聚合 | `propose_certainty(design, domains, upgrades)`，`domains` 為 `{domain: str}` | `aggregate_certainty(design, judgements, risk_tier, upgrades)`，`judgements` 為 `{domain: HumanDomainJudgement}` | 簽章不相容，位置參數對不上（多了 `risk_tier`） |
| B12 | 分析產物欄位 | `required_auto_resolution[].required_deterministic_auto_resolution_rate` | `required_coverage[].required_deterministic_resolution_coverage` | 下游讀不到欄位；且舊名把 coverage 讀成品質指標 |
| B13 | 模組路徑 | `reference-impl/{scope_match,deterministic_stats,grade_domains,study_family,adjudication}.py` 平面模組 | `ahig/{scope/matcher,stats/deterministic,stats/grade,stats/family,stats/adjudication}.py` package | `ImportError` |
| B14 | 檔案 IO 編碼 | 未指定 encoding | 全面 `encoding="utf-8"`；stdio 由 `configure_stdio()` 強制 | 原生 Windows（CP950）下 `UnicodeDecodeError`（見第 4 節） |

### 非 breaking 但需注意

| 項目 | 變更 |
|---|---|
| `extraction-scope-contract.schema.json` | `$id` 未變，但新增 `allOf`：`status = "frozen"` 時 `frozenAt` 與 `scopeContractHash` 必填。v2 的 frozen 契約若缺這兩欄會驗證失敗 |
| `search-contract-version.schema.json` | 新增 2 條 `allOf`：`recall-expanding` 強制 backfill 三欄常數值 + `recallEvaluation`；`recall-neutral` 強制 seed recall 前後值 |
| `monitoring.schema.json` | 新增頂層 `oneOf`，四個 `$defs` 擇一。v2 可餵入不屬於任何一型的雜湊物件，v2.1 會拒絕 |
| `quantity-kind-registry.schema.json` | `$id` 未變，但 `representation` 與 `crossStudyComparability` 各新增條件式（`ucum` → `ucumCode` 必填；`comparable-after-declared-conversion` → `conversionRule` 必填；`not-comparable` → `blockingConditions` 至少一項） |
| 新增 schema | `batch-quality-gate`、`time-log`、`gold-scope-metrics`（v2 無對應，無需遷移） |

---

## 3. 逐項遷移步驟

### 3.1 OutcomeInventory 實例（B1–B6）

**這是遷移工作量最大的一項。** 每一份 v2 的 OutcomeInventory 都要處理。

**步驟 1：判定 lifecycle。**

- 實例中的 `reportedOutcomes[]` 有 `scopeDecision` → 標 `lifecycle: "scoped"`
- 沒有 → 標 `lifecycle: "draft"`

**步驟 2a：若判定為 `draft`。**

移除任何殘留的 `scopeDecision`、`scopedAt`、`scopeDecisionSummary`。draft 攜帶這些欄位一律驗證失敗——這是刻意的，模型不得預寫確定性結論。

**步驟 2b：若判定為 `scoped`。**

不要手工補欄位。**丟掉舊的 `scopeDecision`，退回 draft，重跑 ScopeMatcher**：

```python
from ahig.scope import matcher as sm

scoped = sm.ScopeMatcher(frozen_contract).scope_inventory(draft)
```

理由：v2.1 的 `scopeDecision` 需要 `ruleId` 與五軸 `matchedScopeElements`，這兩者只有 matcher 算得出來。手工回填等於重新做一次判定，而且沒有規則版本可回溯。matcher 會一併補上 `scopedAt` 與 `scopeDecisionSummary`，輸出直接通過 schema，不需要任何測試端修補。

若原本的 `scopeDecision` 與重跑結果不一致，那是有價值的資訊——記下來，那代表 v2 當時的判定有問題。

**步驟 3：補 `completenessAttestation`（必填）。**

```json
{
  "sectionsScanned": ["Methods", "Results", "Tables", "Supplement"],
  "supplementaryScanned": true,
  "harmsScan": {
    "performed": true,
    "sectionsScanned": ["Results", "Adverse events"],
    "harmOutcomesFound": 0,
    "harmsReportingStatement": "explicit-none-reported"
  },
  "attestedBy": {"agentClass": "model", "at": "<ISO 8601>"}
}
```

`harmsScan.performed` 不得填 `false`——那不是一個合法的完成狀態，是「這份 inventory 還沒做完」。若當初真的沒掃 harms，就必須回頭掃，不能靠改欄位繞過。

另注意：`harmOutcomesFound ≥ 1` 時，`reportedOutcomes` 內必須真的有一項 `outcomeRoleAsStated: "safety"`，否則驗證失敗。宣稱與清單必須對得起來。

**步驟 4：補 `registryComparison` 四欄（若 `status = "compared"`）。**

`registryId`、`registryRetrievedAt`、`registryPrimaryOutcomes`、`outcomeSwitchingFlags` 全部必填。`outcomeSwitchingFlags` 為空陣列是合法的（代表比對過、沒發現 switching）；**欄位缺席不合法**（代表沒比對，卻標了 `compared`）。

若拿不到 registry 資訊，把 `status` 改成誠實的值：`no-registration-found`、`registry-record-inaccessible` 或 `pending`。

**步驟 5：switching flag 非空時設 `createdBy.dualExtracted = true`。**

若當初是單模型抽取，這份 inventory 必須重新雙審，不能只改旗標。

**驗證：**

```python
from jsonschema import Draft202012Validator
import json, pathlib

schema = json.loads(pathlib.Path("schema/outcome-inventory.schema.json").read_text(encoding="utf-8"))
errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
```

### 3.2 MID registry（B7）

檢查每一筆 v2 項目：`value.magnitude` 是不是為了滿足必填而編出來的？

- **是** → 改為 `status: "unavailable"`，刪除整個 `value` 物件，加上 `unavailableReason`（說明為何本領域無共識 MID）。`derivationMethod` 與 `revalidateBy` 在 unavailable 下不再必填。
- **否，且有文獻依據** → 保持 `status: "active"`，但需補 `provenance.citationAnchor`（v2.1 對 active 的新要求）與 `revalidateBy`。
- **否，但只是專案內部暫定** → `status: "provisional"`，需 `value`、`derivationMethod`、`revalidateBy`。provisional MID 不足以支撐 high certainty，GRADE 會自動加上限。

下游影響：`status = "unavailable"` 的 MID 會讓 `rate_imprecision()` 回傳 `contextualised = False`，並強制人工說明。這是預期行為，不是錯誤。

### 3.3 抽取範圍契約（frozen 者）

v2 的 frozen 契約若缺 `frozenAt` 或 `scopeContractHash`，v2.1 直接拒絕。不要手填雜湊——用凍結流程重算：

```python
from ahig.contracts import freeze

freeze.assert_freezable(contract)              # 先跑確定性前置檢查
frozen = freeze.freeze_document(contract, "scopeContractHash", frozen_at="<ISO 8601>")
assert freeze.verify_frozen(frozen, "scopeContractHash")
```

`freeze_preflight()` 會擋下三類 v2 沒檢查的契約層錯誤：時窗重疊（會讓所有落在交集的測量點被 `SCOPE-002b` 升級人工）、劑量分帶重疊（讓 `_match_dose` 的結果取決於清單順序）、軸內重複 ID。

**若前置檢查報錯，那是 v2 契約本身的缺陷**，必須先改契約，不能略過。

`document_hash()` 排除雜湊欄位自身後才計算——這是 v2 沒有明確定義的細節。若你的 v2 流程把 `scopeContractHash` 一起算進去，重算後的值會不同，這是正確的修正。

### 3.4 SHACL shapes（B8）

**路徑對照：**

| v2 | v2.1 |
|---|---|
| `shapes/ahig-patch-v2.shacl.ttl`（500 行，單檔） | `shapes/core/ahig-core.shacl.ttl`（763 行，零 `sh:sparql`）<br>`shapes/sparql/ahig-v2.1.shacl.ttl`（469 行，audit profile） |

**遷移動作：**

1. 把驗證流程改為載入 `core` profile 作為**阻擋依據**。Core 只用 SHACL 1.0 Core 詞彙，任何合規處理器都必須執行——Core-only 處理器可合法忽略 `sh:sparql`，所以把 SPARQL 約束當唯一防線等於沒有防線。
2. `sparql` profile 作為 audit，pySHACL 版本釘在 `0.40.1`（`ahig/gates/shacl.py:PINNED_PYSHACL_VERSION`）。版本不符時 canary runner 直接失敗，不會靜默降級。
3. 若你有自訂 shapes：所有 property shape 必須具名（`ahigsh:PS-*`）並自帶 `sh:severity`（severity 不繼承）；所有 SPARQL 約束必須自帶 `sh:declare` / `sh:namespace`，不得依賴 rdflib 的 namespace 回退（見 4.2）。

**跨節點、日期與聚合規則已從 SHACL 移出**，改由確定性 Python gate 負責（`ahig/gates/`）。若你依賴 v2 SHACL 做這類檢查，要改呼叫對應的 gate 函式。

### 3.5 量綱註冊表（B9）

v2.1 的 `ahig/stats/adjudication.py:_registry()` 掃描 `registry/quantity-kinds.*.json` 並合併。

**遷移動作：**

- 新增領域註冊表時直接放進 `registry/`，命名為 `quantity-kinds.<domain>.json`。不需要改程式。
- **ID 全域唯一。** 兩份檔案定義同一個 `quantityKindId` 會拋 `QuantityKindCollision`，不是後者覆蓋前者。這是刻意的：靜默覆蓋會讓 `blockingConditions` 取決於檔名排序，是最難察覺的閘門失效。
- v2 的 `quantity-kinds.sport-science.json` 有三筆 `crossStudyComparability.level = "comparable-after-declared-conversion"` 但 `conversionRule` 為 `null`（`vo2max-relative`、`power-to-mass`、`blood-lactate`）。v2.1 的條件式會拒絕——已在 v2.1 補上 `conversionRule`。你自己的註冊表要做同樣的檢查。
- v2.1 另新增 `ahig:qk:supplement-dose-absolute`，供 `ADJ-003` 產生與 A/B 順序無關的 canonical 單位。

### 3.6 程式呼叫端（B10、B11、B13）

**模組路徑：**

```python
# v2
from scope_match import ScopeMatcher
from deterministic_stats import run_all
from grade_domains import propose_certainty
from study_family import ...
from adjudication import adjudicate_record

# v2.1
from ahig.scope.matcher import ScopeMatcher
from ahig.stats.deterministic import run_all
from ahig.stats.grade import aggregate_certainty
from ahig.stats.family import ...
from ahig.stats.adjudication import adjudicate_record
```

**GRADE 聚合改寫：**

```python
# v2：直接由等級字串算出 certainty
result = propose_certainty("RCT", {
    "risk-of-bias": "not-serious",
    "inconsistency": "serious",
    ...
})
certainty = result["certainty"]

# v2.1：必須提供帶 agentClass 與理由的人類判斷
from ahig.stats.grade import HumanDomainJudgement, GRADE_DOMAINS, aggregate_certainty

judgements = {
    d: HumanDomainJudgement(
        domain=d,
        rating="not-serious",
        agent_class="human-self",        # safety-critical 需 "human-expert"
        rationale="……",
        acknowledged_flags=[],           # 須涵蓋 indicators 的 requires_acknowledgement
    )
    for d in GRADE_DOMAINS
}
result = aggregate_certainty("RCT", judgements, risk_tier="general-clinical")
certainty = result["effectiveCertainty"]   # 條件不足時為 None，必須檢查
```

`propose_certainty()` 仍可呼叫，但只回 `advisoryCertainty`，`effectiveCertainty` 恆為 `None`（`ruleId = "GRADE-SUM-001-COMPAT"`）。它存在的目的是讓舊呼叫端不會靜默失敗，而不是讓你繼續用。

**override 行為變更：** `apply_override()` 在 v2 會同時改 `perDomain` 與標記 `effectiveForApprovedClaim`，導致「等級被改成 high 卻標記為不生效」的自相矛盾狀態。v2.1 分流：模型 override 與風險層不足的人類 override 只寫入 `advisoryOverrides`，完全不動 effective 值；合格的人類 override 才進 `overrides` 並重算。且全程 `deepcopy`，原物件與其歷史不受污染。

**裁決規則新增：** `ADJ-003b`（可比性阻擋）、`ADJ-003c`（未宣告的複合單位換算）、`ADJ-004c`（crude 2×2 不可採）、`ADJ-006c`（null 狀態矛盾）。若你有針對 ADJ rule ID 的分支或報表，要加上這四條。

**確定性檢查未變：** `STAT-001` 到 `STAT-016`，實際實作 13 條（008–010 為保留空號，v2 與 v2.1 皆同）。v2 README 寫「16 類統計一致性檢查」，實際是 13 條 + 3 個空號——v2.1 文件改為忠實宣稱 13 條。

### 3.7 分析產物（B12）

重跑四支分析腳本：

```bash
python analysis/sampling_power.py            # 約 90 秒
python analysis/gate_inversion.py
python analysis/human_throughput.py
python analysis/adjudication_sensitivity.py
```

**`adjudication_sensitivity.json` 的欄位更名（語意修正，非美化）：**

| v2 | v2.1 |
|---|---|
| `required_auto_resolution`（頂層鍵） | `required_coverage` |
| `weekly_capacity_by_auto_rate_base_3y` | `weekly_capacity_by_coverage_base_3y` |
| `required_deterministic_auto_resolution_rate` | `required_deterministic_resolution_coverage` |
| （無） | `metric: "deterministic-resolution-coverage"` |
| （無） | `quality_metrics_not_implied: ["accuracy", "major-error-rate"]` |
| （無） | `policy_target_3y_10h_week: 0.875` |

**為什麼改名。** 「自動消解率」讀起來像品質指標，實際上它只是「分歧中有多少比例由規則處理掉」——規則可以 100% 消解且 100% 錯誤。coverage 是**期程指標**（決定需要多少人工時數），accuracy 與 major-error 才是品質指標，且必須對 gold answer 計算。v2 的 87.3% 被當成品質門檻引用，那是誤讀。v2.1 政策採 87.5% coverage（期程目標），另設 accuracy ≥ 99%、major error = 0（品質目標）。

**`sampling_power.json` 新增兩個欄位：** 每個 AC1 情境多了 `search_grid_max` 與 `not_reached_within_grid`。v2 在搜尋網格內找不到滿足門檻的 n 時回傳 `None`，讀起來像「永遠達不到」；實際只代表「在所測網格內未達」。新欄位讓這個區別可見。

---

## 4. 被推翻的 v2 宣稱

### 4.1 「101 項單元測試全通過」

**本機原生 Windows 實測是 100/101。**

失敗的是 `test_scope_and_family.py:554`，`Path.read_text()` 未指定 encoding，在 CP950 預設編碼下拋 `UnicodeDecodeError`。加上 `python -X utf8` 後確實是 101/101。

這不是造假，是**環境依賴未被宣告**。v2 的開發沙箱預設 UTF-8，該依賴從未浮現。差別在於：v2 說的是「測試全通過」，實際成立的命題是「在 UTF-8 預設的環境下測試全通過」。

v2.1 的處理：所有 `read_text` / `write_text` / `open` 明確指定 `encoding="utf-8"`，stdio 由 `ahig/bootstrap.py:configure_stdio()` 強制，並列為 `verify --all` 的第 1 階段。

同理，「36 項交付物驗證全通過」在 UTF-8 模式下可重現。v2.1 的 `verify.py` 現為 42 項（新增 ScopeMatcher 輸出直通驗證等）。

### 4.2 已本機重現的閘門缺陷

以下八項在本機重現後才寫進 v2.1 的紅測試。遷移時應確認你的環境不再出現：

| # | v2 行為 | 本機重現 | v2.1 修正 |
|---|---|---|---|
| 1 | SHACL-SPARQL 約束缺自足前綴 | pySHACL 拋 `Unknown namespace prefix: ahig` | 所有 SPARQL 約束自帶 `sh:declare` / `sh:namespace`；`test_sparql_profile_survives_prefix_binding_loss` 釘住這個性質 |
| 2 | `ADJ-005` 只看 anchor 強度 | 標了 exact anchor 的錯值 **24** 勝過正確的 **42** | anchor 必須先通過 source hash 與 field/outcome/timepoint/arm/analysisSet 六鍵綁定；且只作為證據定位，不得單獨決定數值勝負 |
| 3 | `ADJ-004` crude 2×2 重算無條件適用 | crude RR **0.50** 擊敗 adjusted RR **0.80** | 新增 `_crude_2x2_admissible()` 與 `ADJ-004c`：crude 重算只能裁決同一 unadjusted estimand |
| 4 | `apply_override` | moderate 被改成 high，同時標記 `effectiveForApprovedClaim = false` | 分流為 `overrides` / `advisoryOverrides`，不合格的 override 完全不動 effective 值 |
| 5 | Egger 檢定失敗 | `Singular matrix` 例外後仍回 `not-serious`，且不要求人工確認（fail-open） | 全面 fail-closed：不適用、singular、運算失敗、資料不足皆回 `indeterminate` + `requiresHumanConfirmation = true` |
| 6 | `3/n` rule-of-three SHACL shape | **n=299 被自家 shape 否決**——近似式比精確式嚴格，會擋掉正確的樣本數 | SHACL 不再重算，改由 Python gate 做 Clopper–Pearson 精確計算（n=30 → 9.5034%，n=299 → 0.9969%）；SHACL 只驗證方法、輸入與 pass/fail 結果 |
| 7 | schema 與 matcher 介面漂移 | schema 合法的 inventory 餵不進 ScopeMatcher；matcher 產出的形狀被 `additionalProperties: false` 拒絕 | schema 與 matcher 共用同一組軸定義；整合測試以 AST 掃描 matcher 實際讀取的鍵，任何漂移即紅燈 |
| 8 | 空 inventory + `status: "compared"` | 通過驗證 | `reportedOutcomes` 加 `minItems: 1`；`compared` 強制四欄 |

**共同性質**：這八項在 v2 的單元測試裡全部是綠的。原因是每一層都對著自己的 fixture 驗證，接縫沒有人測。v2.1 因此新增 `tests/test_end_to_end.py`（貫穿測試）與 SHACL canary 語料（21 negative + 6 positive），negative canary 必須得到 `conforms = false` **且**命中特定的 `sh:sourceShape`——只檢查「有沒有擋下來」不夠，還要確認是被正確的規則擋下來的。

### 4.3 v2 已自述、v2.1 仍成立的限制

v2 README 末節列的「尚未收斂」大部分仍然成立，遷移不會解決它們：

- MID 註冊表實質為空（v2.1 讓「空」變成可表達的 `unavailable` 狀態，但沒有填入內容）
- 所有時間參數仍是規劃估計，未經實測
- 85% 自動消解率未在真實資料上驗證。v2.1 改稱 coverage 並訂在 **87.5%**——注意這是**比 v2 更高**的數字，不是放寬：它來自「基準情境、每週 10 小時、三年」推算出的 0.8733 進位，是人力可行性的下限而非品質門檻。語意修正了，數字仍未實測。
- indirectness 仍純人工
- 不可變模型與資料刪除權的張力未處理

v2 說「SHACL 未經 pySHACL 實際載入」——**這一項 v2.1 已解決**，見 4.2 第 1 項。

---

## 5. 遷移後如何驗證

```bash
python -m ahig.cli verify --all
```

十個階段，任一失敗回傳非零退出碼：

| # | 階段 | 檢查什麼 |
|---|---|---|
| 1 | 執行環境 | stdio 為 UTF-8；未設 `AHIG_PRIVATE_ROOT` 時私密資料命令 fail-closed |
| 2 | JSON Schema | 所有 schema 通過 2020-12 meta-validation |
| 3 | Registry 與量綱命名空間 | 每筆 registry entry 通過 schema；多檔合併後無 ID 碰撞 |
| 4 | SHACL canary | 每個 negative canary 得到 `conforms = false` 且命中預期的 `sh:sourceShape`；positive canary 不被誤擋 |
| 5 | 交付物驗證 | `verify.py` 全數通過 |
| 6 | 單元與整合測試 | `tests/run_tests.py` 全數通過 |
| 7 | B.11 凍結契約 | 雜湊自我驗證、前置檢查為 0、matcher 接受、GI harms 為 critical |
| 8 | 端到端貫穿 | frozen contract → draft → scope → StudyResult → 檢查 → 裁決 → 閘門 → GRADE |
| 9 | 數字對帳 | 文件宣稱的數字與現場實算一致（Clopper–Pearson 上界、配額加總、契約雜湊交叉引用） |
| 10 | 私密資料掃描 | 公開專案內無私密健康資料路徑 |

無 pytest 時仍可單獨執行：

```bash
python tests/run_tests.py
python tests/run_tests.py tests/test_end_to_end.py    # 只跑貫穿
```

**遷移過程的建議順序**：先讓階段 1–3 綠（環境與 schema），再處理 4（shapes），最後才是 6、8（程式與貫穿）。前面紅的時候，後面的紅多半是衍生的。

---

## 6. 不需要遷移的部分

以下 v2 設計被 v2.1 **完整保留**，沒有任何欄位或語意變更：

- **抽取範圍契約的核心結構**（A 項）。`researchQuestion` / `inScopeOutcomes` / `inScopeTimepoints` / `inScopeAnalysisSets` / `inScopeEffectMeasures` / `extractionPolicy` 六軸不變。這是 v2 最有價值的貢獻——把 604,800 個 StudyResult 降到 25,200 個、58.1 人年降到 2.7 人年的結構修正。v2.1 只是把它從「schema 描述」變成「可執行的閘門」。
- **`onOutOfScope = "record-in-outcome-inventory-only"` 常數**。超出範圍者只登錄不建 StudyResult、絕不靜默丟棄——這條原則不變。
- **監控 schema 的四個 `$defs`**（D 項）。`MonitoringPolicy` / `MonitoringRun` / `SourceStatusRecord` / `StaleMonitoringEvent` 內容不變，v2.1 只在頂層加 `oneOf` 讓它們互斥。
- **`study-family.schema.json`**。完全未修改（檔案時間戳仍是 v2 原始的）。
- **GRADE 四級忠實重用**。High / Moderate / Low / Very Low 四級、五個 domain、降級與升級規則，全部照 GRADE 原文，v2.1 沒有發明新等級。變的只是「誰有資格作出 domain judgement」與「模型的建議放在哪個欄位」。
- **`SCOPE-000` 到 `SCOPE-999` 規則 ID 與語意**。matcher 的判定邏輯未變，v2.1 只是把輸出補上 `ruleId` 與 `decidedBy`。
- **13 條確定性統計檢查**（`STAT-001`–`STAT-016`，008–010 為空號）。演算法未變。
- **量綱註冊表的「UCUM 不敷使用」結論**（G 項）。`local-ratio` / `local-ordinal` / `local-index` / `dimensionless-count` 四種非 UCUM 表示法保留，`comparabilityClass` 與 `crossStudyComparability` 的四級可比性也保留。v2.1 只是讓其中的條件式變成可執行。
- **`analysis/` 四支腳本的演算法**。Gwet AC1 線性化變異數、Clopper–Pearson、人力模型、閘門反解——計算方法完全未變，只改了輸出欄位名與新增說明欄位。三個推翻 v1 的實算結果（n=30 只能證明 9.5%、AC1 在 n=30 只有 48.7% 通過率、10 h/週實際上限 1.14 個領域）全部維持有效。
