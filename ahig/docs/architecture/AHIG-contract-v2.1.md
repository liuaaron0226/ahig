# AHIG 契約 v2.1

**日期：** 2026-08-13
**狀態：** 公開契約核心可在原生 Windows 完整驗證；B.11 校準契約已凍結，尚未取得任何文獻。
**前一版：** `AHIG-contract-v2.md`（原件保留，不覆寫）

---

## 這份文件是什麼

v2 是一份**設計提案**：它把 v1 憑直覺宣告的數字改成實算，方向是對的。但它的參考實作從未在本機真正執行過——SHACL 形狀沒被 pySHACL 載入過、測試在 Windows 原生編碼下根本跑不起來、schema 與程式的介面從未對接過。

v2.1 不是 v2 的下一輪設計，是**把 v2 拿去實際執行後的修正**。這份文件的重點因此不在「架構長什麼樣」，而在**哪些設計在實測下失效、失效模式是什麼、現在用什麼結構擋住它**。設計意圖已經寫在 v2 裡了，重複一遍沒有價值；踩過的雷才是。

每一節的形式都是：v2 怎麼寫的 → 本機實測發生了什麼 → v2.1 改成什麼 → 現在由誰擋住。

### v2 在本機重現的失效清單

這九項全部可重現，全部是「看起來會動、實際上不會動」或「會動但擋不住該擋的東西」：

| # | 失效 | 性質 |
|---|---|---|
| 1 | pySHACL 載入 SPARQL 約束時 `Unknown namespace prefix: ahig` | 形狀根本無法執行 |
| 2 | Windows CP950 下 `read_text()` 未指定 encoding，測試無法啟動 | 驗證器本身跑不起來 |
| 3 | ADJ-005 讓標了 exact anchor 的**錯值**勝過正確值 | fail-open，會寫入錯誤資料 |
| 4 | ADJ-004 讓 crude RR 0.50 擊敗 adjusted RR 0.80 | fail-open，估計量張冠李戴 |
| 5 | `apply_override` 把 moderate 改成 high，卻同時標 `effectiveForApprovedClaim=false` | 自相矛盾，等級已被改掉 |
| 6 | Egger 檢定 singular matrix 仍回 `not-serious` 且不要求人工 | fail-open，「算不出來」變成「沒問題」 |
| 7 | n=299 被自家的 `3/n` shape 否決 | 閘門否決了唯一能達標的樣本數 |
| 8 | schema 合法的 OutcomeInventory 餵不進 ScopeMatcher | 介面漂移，兩邊各自綠燈 |
| 9 | 空 inventory 加 `status:"compared"` 可通過驗證 | 完整性宣稱無法稽核 |

第 3、4、6 項是最危險的一類：它們不會讓任何測試變紅，只會讓錯誤的東西安靜地通過。

---

## 一、三層模型分工

分工本身沿用 v2，但責任邊界在 v2.1 被結構化執行，而不只是政策宣示。

| 層 | 角色 | 硬性限制 |
|---|---|---|
| NotebookLM | 長上下文比較、檢索線索 | **輸出不是證據。** `notebookId`、`notebookSourceId`、`notebookChunkId`、`notebookCitationNumber` 任一出現在 CitationAnchor 即 Violation |
| Claude ＋ TERRA MAX | 獨立盲抽取 | 兩者皆為 `model`；模型不得作出納入決定、範圍判定、family 合併或 GRADE domain 評級 |
| 本機 Ollama | `untrusted-preprocessing` | 不參與任何正式判斷，輸出不得作為閘門依據 |

**NotebookLM 的座標為什麼不能當 anchor**：它的 `source_id` 與 `citation_number` 是會話內的內部座標，重新詢問可能改變，且 v1 實測 30 筆 reference 的 `cited_text` 全為空。一個會變的識別碼無法支撐可稽核的引用。CitationAnchor 必須綁定 Manifestation hash 與原文 selector。

**兩個模型的「獨立」是名義上的**：Claude 與 TERRA MAX 都是 LLM，共享大量失效模式。兩者一致**不代表**正確——這正是 v2.1 把 accuracy 與 coverage 分離、並要求量測 `commonWrongAgreement` 的原因（見第七節）。盲審 agreement 看不見共同錯誤，只有 gold set 看得見。

---

## 二、責任邊界：Core / SPARQL / Python

這是 v2.1 最重要的結構決定，直接來自失效 #1。

v2 把 17 個零容忍條件全部押在 `sh:sparql` 上。本機以 pySHACL 載入時直接爆 `Unknown namespace prefix: ahig`——因為 SPARQL 約束依賴 Turtle 檔頭的 `@prefix`，而 SHACL-SPARQL 要求約束**自帶** `sh:declare`／`sh:namespace`。更根本的問題是：`sh:sparql` 是 SHACL 的 SPARQL 擴充，各家驗證器支援程度不一，而 SHACL 1.0 Recommendation 明文允許 Core-only 處理器忽略它。**把零容忍條件單獨押在上面，等於接受「換一個驗證器就全面 fail-open」。**

v2.1 拆成三層，各自負責它擅長的：

| 層 | 檔案 | 內容 | 實測規模 |
|---|---|---|---|
| **SHACL Core** | `shapes/core/ahig-core.shacl.ttl` | 結構阻擋：必填、列舉、基數、條件式必填 | 35 NodeShape、66 PropertyShape、**0 個 `sh:sparql`** |
| **SHACL-SPARQL** | `shapes/sparql/ahig-v2.1.shacl.ttl` | Core 表達不了的跨節點算術與集合條件 | 10 NodeShape、19 個約束 |
| **確定性 Python gate** | `ahig/gates/`、`ahig/stats/` | 日期算術、統計重算、聚合、跨檔案交叉比對 | 13 項統計檢查、15 條裁決規則 |

**Core 是唯一必要的防線；SPARQL 是 pinned audit。** 任何合格的 SHACL 驗證器都能完整執行 Core，所以結構性阻擋全部落在那裡。SPARQL profile 提供更深的稽核，但它的失效不能造成安全洞。

### 三個 SHACL 陷阱

寫形狀時踩到的，記下來免得再踩：

1. **`sh:conforms` 只要有任何結果就是 false。** 所以「品質建議」不能和「核准阻擋」放在同一份 shapes graph——否則一個 Info 級的建議會讓整份文件無法核准。拆成 `approval-core-shapes` 與 `advisory-quality-shapes`。
2. **severity 不繼承。** NodeShape 上宣告的 severity 不會傳給它的 property shape。v2.1 讓每個 property shape 都具名（`ahigsh:PS-*`）並自帶 severity——匿名 property shape 在驗證報告裡無法回指，形狀改壞了也看不出來。
3. **`sh:closed` 只計同一 shape 的 `sh:property`。** 跨 shape 的欄位不算在內，所以 `sh:closed` 擋不住你以為它擋得住的東西。

### canary：形狀自己也需要被驗證

形狀能載入 ≠ 形狀擋得住東西。v2.1 建立 27 個 canary（21 negative、6 positive），全部以 pySHACL **0.40.1**（版本釘死）實際執行：

- **negative canary** 必須得到 `conforms=false`，**而且**必須命中檔頭 `# @expect-core:` / `# @expect-sparql:` 宣告的特定 `sh:sourceShape`。只檢查 `conforms=false` 是不夠的：形狀改壞之後，違規可能改由某個無關的必填欄位順手擋掉，`conforms=false` 依舊成立，測試卻已失去意義。
- **positive canary** 必須通過。沒有正向 canary 的話，「把所有東西都擋掉」會是滿分解——fail-closed 會退化成不可用。
- **target coverage preflight**：SHACL 最安靜的失效模式是「沒有任何形狀 target 到這個節點」，驗證器回報 `conforms=true` 因為它根本沒檢查。驗證前先確認資料圖裡每個 `rdf:type` 都至少被一個形狀 target 到。
- `test_sparql_profile_survives_prefix_binding_loss` 把圖經 N-Triples 往返、清掉所有前綴綁定後再驗一次——證明 SPARQL 形狀不是靠 Turtle 的 `@prefix` 僥倖過關。這條測試直接釘住失效 #1 不再發生。

### v2 修掉的四個 fail-open

canary 建立過程中發現，這些條件在 v2 的寫法下擋不住實際的違規圖：

- Outcome switching 只認一個方向，`StudyResult → derivedFromOutcomeInventory` 的正式方向漏掉。
- safety-critical approved claim 只擋「明寫 self-adjudicated」，**沒有裁決者**的情況直接放行。
- GRADE 只要求「五筆 rating」，不要求五個**不同的** domain——同一個 domain 寫五次可以過。
- Monitoring SLA 缺欄位時不 fail-closed。v2.1 改為由 `lastSuccessfulCheckAt + maxAgeHours + graceHours` 計算，必要欄位缺失即擋。

---

## 三、OutcomeInventory 的 draft / scoped lifecycle

失效 #8：v2 的 schema 合法文件餵不進 ScopeMatcher，因為 schema 定義的欄位軸與 matcher 實際讀取的鍵從未對接。兩邊各自對著自己的 fixture 綠燈。

失效 #9：空的 `reportedOutcomes` 配上 `registryComparison.status = "compared"` 可以通過驗證——一份宣稱「已與登錄比對」但沒有任何條目的清單，無法支撐任何 `notExtracted` 標記，也無法區分「未抽取」與「不存在」。

### 兩階段生命週期

```
OutcomeInventoryDraft          模型或人工完整登錄論文報告了什麼
    ↓  ScopeMatcher（確定性）
ScopedOutcomeInventory         每項補上 scopeDecision.ruleId 與 matchedScopeElements
```

**draft 攜帶任何 `scopeDecision` 一律視為污染，不得升級。** 理由很直接：範圍判定若能由模型填寫，範圍契約就形同虛設——模型可以宣稱任何東西 out-of-scope 而無人可查。`assert_scopable()` 在升級前檢查，`draft` 帶 `scopeDecision`、`scopedAt` 或 `scopeDecisionSummary` 即拒絕，不做靜默修補。

每一筆 `scopeDecision.decidedBy` 固定為 `{"agentClass": "deterministic", "matcherVersion": "scope-matcher/2.0.0"}`。matcher 版本必須隨規則語意變更升版，否則已 scoped 的清單無法分辨自己是由哪一版規則判定的。

### 介面漂移的防線

`schema/outcome-inventory.schema.json` 是 v2.1 條件式規則最密集的一份（9 組 `if/then`）。但 schema 只管形狀，擋不住漂移，所以另外兩道：

1. **AST 掃描**：測試解析 `matcher.py`，比對它實際讀取的軸鍵、發出的 `reasonCode` 與 `ruleId` 是否與 schema 宣告完全一致。schema 與實作各自演化時必然亮紅燈。目前 13 個 `reasonCode`、15 個 `ruleId`，兩邊對齊。
2. **round-trip**：ScopeMatcher 的輸出必須**直接**通過 scoped schema，不容許測試端補欄位。這條主張寫在 `test_scoped_output_validates_without_touch_up`——`verify.py` 也不再自帶平行 fixture，改為呼叫真的 matcher，否則會出現「驗證器綠燈但沒人餵得出這種文件」的假象。

### 完整性必須可稽核

`completenessAttestation` 改為必填，且分開記錄正文、表圖、補充材料與 **harms/safety 掃描**。schema 擋得住「宣稱找到 harm 卻沒有任何 safety 條目」，但擋不住**數量不符**——JSON Schema 無法把 `contains` 的命中數與另一個欄位的整數相比。`audit_harms_scan()` 補上這個對帳。

`registryComparison.status = "compared"` 時強制四個欄位齊備；`outcomeSwitchingFlags` 非空時強制 `dualExtracted = true`。

---

## 四、確定性裁決：15 條規則

`ahig/stats/adjudication.py`。v2 有 7 條規則，v2.1 有 15 條——多出來的多半不是新功能，是把 v2 一條規則裡混在一起的幾種情況拆開，因為它們的**安全處置不同**。

```
ADJ-000-identical                        ADJ-004b-both-fail-recomputation
ADJ-001-text-normalisation               ADJ-004c-crude-2x2-inadmissible
ADJ-002-enum-synonym                     ADJ-005-anchor-strength
ADJ-003-unit-conversion                  ADJ-006-null-vs-anchored
ADJ-003b-comparability-blocked           ADJ-006b-null-unanchored
ADJ-003c-undeclared-composite-conversion ADJ-006c-null-state-contradiction
ADJ-004-numeric-recomputation            ADJ-007-schema-violation
                                         ADJ-999-no-deterministic-basis
```

### anchor 只能定位，不能替數值背書

失效 #3：v2 的 ADJ-005 讓「有 exact anchor 的一方」直接勝出。實測中，一個標了 exact anchor 的錯值 24 打敗了正確的 42。

問題在於推論本身無效：**逐字 anchor 證明「原文某處有這串字」，不證明「這個數字是這個 estimand 在這個時間點、這個 arm、這個 analysis set 的值」。** 一篇論文裡「42」可能出現在十幾個地方。

v2.1 的處置：

- **數值欄位一律不得由 anchor 強度單獨裁決。** 無重算依據就升級 `human-expert`。
- 非數值欄位的 anchor 也必須帶 `verifiedBinding`：`sourceHash`（sha256 格式驗證）＋ `field` ＋ `outcome` ＋ `timepoint` ＋ `arm` ＋ `analysisSet` 六鍵齊備並比對通過，才算定位證據。缺一即不足以證明「這段文字就是這個欄位」。

### crude 2×2 不得打敗校正估計

失效 #4：v2 的 ADJ-004 用事件數重算效果量來判勝負，實測讓 crude RR 0.50 擊敗了 adjusted RR 0.80。

由 2×2 表重算出的是**未校正**效果量。報告值若來自校正模型，兩者本來就不該相等——差異是校正的效果，不是錯誤。v2.1 加上 `_crude_2x2_admissible()`：estimand、`analysisSet` 或 `statisticalModel` 與 2×2 不一致時，回傳 `ADJ-004c-crude-2x2-inadmissible` 升級，而不是誤判。

`ADJ-004b` 處理另一種情況：兩方都有數學矛盾——那可能是原文本身有誤，一律 `human-expert`。

### null 有兩種，不可互相抵銷

v2 只有一個「缺值」狀態。但「原文未報告這個量」是**對原文內容的實質主張**（可被 gold 驗證），「我在原文中定位不到」是**抽取者的能力聲明**。兩者混為一談會讓前者的錯誤被後者的模糊性吸收掉。

v2.1 三分：

| 狀態 | 意義 | 處置 |
|---|---|---|
| `NOT_REPORTED` | 原文未報告 | 對方若提交了值 → `ADJ-006c` 升級（實質矛盾） |
| `CANNOT_LOCATE` | 定位不到 | 對方的值若能被獨立重算佐證 → 可採用 |
| `NULL_STATE_UNDECLARED` | 未宣告 | 一律升級——不得由未宣告狀態走寬鬆路徑 |

### 規則順序：遮蔽修正

v2 把 anchor 規則排在 null 與 schema 規則之前，**使後兩者永遠不可達**。v2.1 的順序是 null → 文字/列舉/單位 → 重算 → schema → anchor。schema 是硬事實，anchor 只是定位證據，硬事實必須先判。

測試 `_rule_fixtures()` 為 15 條規則各準備可達 fixture 並斷言 rule ID——任何一條變成不可達都會亮紅燈。

### 單位換算讀註冊表，不做字串比對

`ADJ-003` 依 QuantityKindRegistry 的 `comparabilityClass`、`crossStudyComparability.level` 與 `blockingConditions` 判斷可否換算，並回傳註冊表的 canonical unit（使結果與 A/B 順序無關）。`not-comparable` 或命中任一 blocking condition → `ADJ-003b` 升級。複合／導出單位（含 `/()·*^` 者）→ `ADJ-003c` 升級，因為複合換算牽涉多個量綱的基準對齊，不得由單位字串推導。

**禁止數值多數決**由結構測試釘住：原始碼掃描驗證模組不含 `majority`、`vote(`、`most_common`、`Counter(`。

### 量綱註冊表是單一命名空間

領域註冊表會持續增加（目前 2 份共 22 項：`sport-science` 13 項 ＋ `b11-carbohydrate` 9 項），但裁決層必須只有一個查表入口——分檔是編輯上的方便，不是語意上的隔離。合併時若出現重複 `quantityKindId` 直接拋 `QuantityKindCollision`：靜默讓後載入者覆蓋前者，會使 `blockingConditions` 取決於**檔名排序**，那是最難察覺的一種閘門失效。

---

## 五、GRADE：indicators → 人類判斷 → 確定性聚合

v2 把「可計算」誤當成「可判定」：I² ≥ 75% 直接輸出 very-serious、總事件數 < 300 直接降級、Egger p < 0.10 直接判 serious。那不是 GRADE——GRADE 的 domain 評級需要臨床脈絡，統計量只是輸入之一。

更嚴重的是 fail-open（失效 #6）：k < 10、Egger 失敗、資料不足時 v2 回落 `not-serious`。**「算不出來」被靜默翻譯成「沒問題」。** 實測中 Egger 遇到 singular matrix 仍回 `not-serious` 且不要求人工確認。

### 三層分離

```
確定性指標 (DomainIndicators)     ← 永遠不是 final rating
    ↓
人類 domain judgement             ← 五個 domain 各一筆，必須留痕
    ↓
確定性聚合 (aggregate_certainty)  ← 純規則，無自由度
```

`DomainIndicators` 帶 `suggested_judgement`（建議，不是評級）、`flags` 與 `requires_acknowledgement`。**`aggregate_certainty()` 只接受五個具生效 `HumanDomainJudgement` 的 domain**，任一缺漏、任一由模型作出、任一為 `indeterminate`、任一未確認必要旗標——一律 block，不產出 `effectiveCertainty`。

裸的等級字串不構成人類判斷：舊介面 `propose_certainty()` 保留為相容 wrapper，但它**永遠 blocked**，只產出 `advisoryCertainty`。輸入不含 agentClass 與理由時，無從判斷這些等級是不是人類作出的，那個資訊量下唯一安全的行為就是不放行。

### 風險層決定誰有資格判斷

| riskTier | 可作出生效判斷者 |
|---|---|
| `general-clinical` | `human-self`、`human-expert` |
| `safety-critical` | **只有** `human-expert` |

### advisory override 的隔離

失效 #5：v2 的 `apply_override` 把 moderate 改成 high，同時標 `effectiveForApprovedClaim=false`——但等級**已經被改掉了**，標記只是自我安慰。

v2.1 的 `apply_override` 全程 `deepcopy`，並嚴格分流：

- 合格的人類 override → 寫入 `overrides`、改 `perDomain`、重算、`certaintyDerivation` 改為 `deterministic-rule-with-logged-override`。
- 模型 override、風險層不足的人類 override、proposal 已被阻擋 → **只**寫入 `advisoryOverrides`。計算「假如採納會變成什麼」並存為 `advisoryCertainty`，但不動 effective domain、不動 `effectiveCertainty`、不動 `certaintyDerivation`。

### fail-closed 清單

| 情況 | 處置 |
|---|---|
| k < 10 | `indeterminate` ＋ `k<10-egger-not-applicable`，強制人工確認 |
| Egger 奇異／失敗／非有限值 | `indeterminate` ＋ `egger-failed`。`eggers_test()` 設計上不吞例外，一律拋 `ValueError` 由呼叫端轉 indeterminate |
| k < 3 | I² 不穩定，強制人工確認 |
| MID `unavailable` | `contextualised = False`，certainty 上限 moderate，且**不得聲稱已做 contextualised 評級** |
| MID `provisional` | 標記後 certainty 上限 moderate |

MID 上限只封頂不硬鎖 low——降級只能來自實際的 domain judgement，不能由 MID 狀態代勞。

保留 v2 由測試發現的正確修正：**τ² = 0 時預測區間不計入 inconsistency**。τ²=0 時預測區間變寬純粹來自小 k 的 t 乘數，那是 imprecision 的問題；在 inconsistency 降級會把同一個不確定性算兩次。

---

## 六、品質閘門

失效 #7：v2 用 SHACL 寫了一條 `nonCriticalErrorCeiling < 3.0/sampleSize` 的 rule-of-three 檢查。實測中，**n=299 被這條 shape 否決**——而 299 正是 v2 自己算出來、唯一能支撐 1% 上界的樣本數。rule-of-three 是近似式，比精確解寬鬆，用它去重算精確計算的結果必然誤拒。

v2.1 的分工：**Clopper–Pearson 精確計算由 Python 負責；SHACL 只驗證方法、輸入、計算 provenance 與 pass/fail 結果，不再重算。**

實算值（`scipy.stats.beta.ppf`，零錯誤、單側 95%）：

| n | 可證明的錯誤率上界 |
|---:|---:|
| 30 | 9.5034% |
| 60 | 4.8703% |
| **299** | **0.9969%** |

要證明 ≤ 1%，零錯誤下需要 **n = 299**。這個數字由 `minimum_sample_size(0.01)` 實算，並由 `verify --all` 的數字對帳階段每次重新驗證。

### 三個指標必須分離

v2 最容易被誤讀的地方，是把 coverage 當品質。v2.1 拆成三個各自獨立的指標：

| 指標 | 意義 | 政策值 | 性質 |
|---|---|---:|---|
| `deterministicResolutionCoverage` | 分歧中由確定性規則處理的比例 | 0.875 | **期程指標，不是品質** |
| `deterministicResolutionAccuracy` | 確定性裁決與 gold answer 相符的比例 | ≥ 0.99 | 品質 |
| `majorErrorCount` | 重大錯誤數 | 0 | 品質 |

**87.3%（實算 0.8733）是「基準情境、每週 10 小時、3 年期程」下推算出的所需 coverage，政策採 0.875。** 這是情境模型的輸出，不是實測——它回答的是「要在三年內做完，確定性層得處理掉多少比例的分歧」，完全不涉及處理得對不對。coverage 高而 accuracy 低，代表系統又快又錯。

`analysis/results/adjudication_sensitivity.json` 的欄位名已改為 `required_deterministic_resolution_coverage`，並帶 `quality_metrics_not_implied: ["accuracy", "major-error-rate"]`。`verify --all` 會掃描舊欄位名 `required_deterministic_auto_resolution_rate`，出現即失敗——這個名字會被讀成品質。

### `insufficient-evidence` 為什麼要存在

`evaluate_batch_quality()` 有三種結果：`pass`、`fail`、`insufficient-evidence`。第三種在以下情況回傳：

- 缺 gold（`accuracy`、`majorErrorCount`、`commonWrongAgreementCount` 任一為 `None`）
- AC1 缺 `modelAssumptions`

沒有第三種結果的話，缺 gold 只能二選一：判 pass（把「沒量」說成「合格」）或判 fail（把「沒量」說成「不合格」）。兩者都是謊。

`commonWrongAgreementCount` 是專為第一節那個問題設的：兩位 LLM 盲審者一致但同時錯，agreement 指標完全看不見，只有 gold 抓得到。上限 0。

AC1 的報告一律標明「在指定 prevalence、獨立等誤差模型與搜尋網格下的估計」；`None` 的意思是**在所測網格內未達門檻**，不是「永遠達不到」。

---

## 七、契約凍結

v2 沒有凍結機制，只有一個 `scopeContractHash` 欄位。v2.1 的 `ahig/contracts/freeze.py` 補上兩件事。

### 雜湊必須排除自身

`document_hash(doc, hash_field)` 算的是**排除雜湊欄位之後**的正規化雜湊（JCS 風格：鍵排序、無多餘空白、UTF-8）。

理由是自我驗證的必要條件：若把 `hash_field` 一起算進去，寫回雜湊就會改變被雜湊的內容，於是**沒有任何一份已凍結的文件能通過自我驗證**。陣列順序有意義（`[1,2]` 與 `[2,1]` 雜湊不同）——靜默把它們視為同一份契約會遮蔽真實差異。

流程刻意分兩個檔案：`scope-contract.draft.json` 是可編輯來源，`scope-contract.json` 是產物。手改產物會讓雜湊失效並被測試抓到；要改就改草稿後重跑 `freeze_contract.py`。

### 凍結前置檢查：契約作者的錯誤要在凍結前擋

三類問題會讓確定性層陷入無解，而它們在凍結前就能確定性檢出：

| 檢查 | 為什麼是契約錯誤 |
|---|---|
| **時窗重疊** | 兩個 in-scope 時窗重疊時，任何落在交集的測量點都會被 `SCOPE-002b` 升級人工。跨單位比較（7 day 與 1 week 是同一個時間點）、閉區間邊界相接也算重疊；session 與時間單位分開比較，因為 matcher 對兩者走不同分支 |
| **劑量分帶重疊** | `_match_dose` 的結果會取決於清單順序 |
| **重複 ID** | `matchedScopeElements` 無法回指唯一定義 |

放行的代價很具體：跑完 60 篇論文後才發現一半的結果卡在人工佇列，而原因從第一天就寫在契約裡。

### SCOPE-002b 與 SCOPE-002c 的責任歸屬不同

兩者看起來相似，處置完全相反：

- **`SCOPE-002b`（單一測量點落入兩個時窗）是契約作者的錯誤**，凍結前確定性檢出 → 要求為 0，由 `freeze_preflight` 強制。
- **`SCOPE-002c`（同一時窗內該研究有多個測量點）是文獻本身的性質**，凍結前無從得知比率 → **只量測，不設門檻**。先設一個「通過率」等於先射箭再畫靶。

---

## 八、驗證入口

```bash
python -m ahig.cli verify --all
```

十個階段，順序由便宜到昂貴、由基礎到整合——前面失敗時後面的失敗多半是衍生的。**目前十階段全數通過。**

| # | 階段 | 擋什麼 | 實測 |
|---:|---|---|---|
| 1 | 執行環境 | stdio 非 UTF-8；未設 `AHIG_PRIVATE_ROOT` 時 `private_root()` 沒 fail-closed | 通過 |
| 2 | JSON Schema | schema 本身不符 2020-12 meta-schema | 10 份 |
| 3 | Registry 與量綱命名空間 | 註冊項不符 schema；`quantityKindId` 跨檔碰撞 | 2 份、22 項 |
| 4 | SHACL canary | negative canary 變成 conforms=true（fail-open）；命中錯誤的 sourceShape；positive canary 被誤擋；target coverage 缺口 | 21 negative ＋ 6 positive，共 48 次驗證 |
| 5 | 交付物驗證 | `verify.py` 的 schema 正反例、Turtle 煙霧測試、統計數字交叉驗證 | 42/42 |
| 6 | 單元與整合測試 | 全部行為契約 | 380/380 |
| 7 | B.11 凍結契約 | 非 frozen；雜湊自我驗證失敗（＝被手改）；前置檢查有殘留；matcher 不接受；GI harms 不是 critical | 6 outcome（2 critical） |
| 8 | 端到端貫穿 | 層與層的接縫漂移 | 27 段 |
| 9 | 數字對帳 | 抽樣框宣稱的上界與實算不符；配額加總不符；n=60 宣稱支撐 1% 上界；strata 釘住的契約雜湊過期；分析產物用回會被誤讀的舊欄位名 | 通過 |
| 10 | 私密資料掃描 | 公開專案出現私密健康資料路徑 | 通過 |

### 端到端貫穿測的是接縫

每一層都有自己的單元測試，但**介面漂移在單元測試裡看不見**——每一層都對著自己的 fixture 綠燈（這正是失效 #8 的成因）。`test_end_to_end.py` 走完整條路：

```
frozen contract → OutcomeInventoryDraft → ScopeMatcher → ScopedOutcomeInventory
  → StudyResult → 確定性檢查 → 雙盲審分歧 → 裁決 → 品質閘門
  → GRADE indicators → 人類判斷 → 聚合
```

貫穿用的是 B.11 的**真實凍結契約**，不是另一份 fixture——契約若改壞，貫穿會亮紅燈。資料全部虛構，且涵蓋連續型（計時賽時間）與二分型（GI harms 事件數，走 2×2 重算分支）兩條路徑。

### 這個入口本身會不會變紅

不會變紅的驗證入口是裝飾品。以下故障各自注入並實測確認會被抓到：

| 注入的故障 | 被哪些階段抓到 |
|---|---|
| 手改凍結契約（`inScopeAnalysisSets` 加一項） | 6、7、8 |
| 量綱 ID 跨檔碰撞 | 3、6 |
| Core 形狀的 `sh:minCount 1` 改成 0 | 4、6 |
| 抽樣框宣稱上界改成 0.009 | 6、9 |
| 公開檔案出現私密資料路徑 | 10 |

**階段 1、2、5 尚未經故障注入**。它們的失敗模式（stdio 編碼、schema 本身不合 meta-schema、`verify.py` 非零退出）比較直接，但「比較直接」不等於已驗證——補上注入測試是待辦事項。

第 10 階段的 token 以字串拼接寫出，否則掃描器自己會成為第一個命中——那會讓這道檢查永遠紅燈，實務上等於被關掉。這不是假設：第一次執行時它確實抓到了自己。

---

## 九、B.11 校準契約

第一個凍結的校準契約：`ahig:scope:b11-exogenous-cho-endurance`（受過訓練的成年耐力運動員、運動中攝取外源性碳水）。6 個 in-scope outcome、3 個時窗、7 個抽樣層、總計 60 篇。

**GI harms 是 critical outcome，不是附帶觀察。** 如果它只留在廉價的 OutcomeInventory，就不會進 SoF 表、不會被 GRADE 評級、不會影響任何建議——那等於在方法論層面預先決定了結論的方向。抽樣框有兩個專屬層（GI 為主要結果 8 篇、GI 僅次要回報 7 篇）確保它不是靠其他層的附帶回報湊數。

RED-S、低能量可用性、快速減重屬 safety-critical 分支，需要各自的範圍契約與 `human-expert` 裁決資格，明確排除在外。排除不等於刪除：落在排除條件內的研究仍會被登錄並標記 `notExtracted-*`，不靜默丟棄。

### 這個校準集能證明什麼

**能**：暴露範圍契約的缺陷、量測實際工時、量測雙審分歧率與 coverage/accuracy、檢驗量綱 `blockingConditions` 擋不擋得住不當合併。

**不能**：證明品質閘門達標。零錯誤下 60 篇的可證明上界是 **4.8703%**，離 1% 差得遠。`strata.json` 顯性寫著 `sufficientForOnePercentCeiling: false`——這個欄位存在的唯一理由，是讓「60 篇校準完成」不會在後續文件裡被讀成「品質閘門已通過」。

**所有 6 個 outcome 的 `midRef` 皆為 `null`**，GRADE 會走 `midUnavailable` 路徑並強制人工說明。捏造一個門檻會讓 imprecision 評級看起來像做過 contextualised 判定。

### 兩個危險的相等

本領域最容易產生**量級錯誤而非細微偏差**的地方，量綱註冊表刻意為它們設計：

**肝醣的乾重 vs 濕重**——兩者 UCUM code 完全相同（`mmol/kg`），乾重值約為濕重值的四倍餘，而文獻常只在方法段一句話交代基準。若自動換算，`400 mmol/kg dw` 與 `90 mmol/kg ww` 會被判為「兩位審查者不一致」然後選出一個勝出值——正確答案是兩者都對，只是基準不同。濕重登錄為 `not-comparable`，兩者都帶 `basis-differs-dry-vs-wet` blocking condition。本專案不接受以文獻通用係數代替該研究實測含水量的自動換算。

**TT vs TTE**——兩者都是「秒」，但計時賽越短越好、力竭時間越長越好，構念不同且 TTE 變異係數顯著較高。單位相同、方向相反——最容易在合成階段同號相加。登錄為不同 `comparabilityClass`，任何情況下不得併入同一效果量。

---

## 十、仍未收斂與刻意延後

誠實列出。

### 仍未收斂

1. **13 項確定性檢查，不是 16 項。** v2 的流水線圖寫「16 類檢查」，實際實作 13 項（`STAT-001`–`007`、`011`–`016`）。**ID 008–010 刻意留空**：為了湊數字而新增未經方法學定案的檢查，只會製造看起來嚴謹的噪音。日後有依據與需求時再補。文件服從實作，不是反過來。

2. **coverage 87.3% 從未在真實資料上量測。** 這個數字不是「規則有多好」的估計，而是**反解出來的需求**：基準情境、每週 10 小時、三年完成，人工佇列消化得完所需的最低 coverage 是 0.8733（政策取 0.875）。15 條規則實際能達到多少完全未知。B.11 校準集是第一次能量測的機會；若實測遠低於此，要改的是期程假設，不是品質門檻。

3. **所有工時數字是情境模型，不是實測。** 特別是 `model_disagreement_rate`——它直接決定 82% 的工時項。第一批跑完必須以實測重新校準。

4. **MID 註冊表實質是空的。** 種子檔 2 個 placeholder，全部 `provisional`。B.11 的 6 個 outcome 全部 `midRef: null`。

5. **indirectness / transportability 仍是純人工。** GRADE 五個 domain 中唯一沒有確定性支撐的。要確定性化需要族群特徵的結構化表示與距離度量。

6. **`SCOPE-002c` 的實際發生率未知。** 若運動科學研究普遍在同一時窗有多個測量點，這個 escalate 會產生比預期更多的人工。B.11 應優先統計此比率。

7. **不可變模型與個人資料刪除權的張力未處理。** InferenceRecord 永久保存 ＋ 個案資料快照識別碼。要刪除某段健康資料需要 crypto-shredding 或 tombstone 語意，否則會留下懸空引用。單人自用可能不在乎法遵，但**懸空引用會破壞可稽核性本身**。

8. **SHACL 1.2 不可用於 production。** SHACL 1.0（2017-07-20 Recommendation）是唯一正式依據。1.2 Core / SPARQL / Rules 目前都還是 Working Draft，不得作為阻擋依據。

### 刻意延後

- 文獻搜尋、取得與權利處理（含付費牆的**合法免費版本**搜尋——不規避存取控制）
- NotebookLM notebook 建立與 hint recall/precision 實測
- 各 outcome 的文獻型 MID 登錄
- 不可變 InferenceRecord 與個人資料刪除的 crypto-shredding
- Jena、Fuseki、Qdrant、Tantivy 與私人 ABox migration
- 由 B.11 校準集產生任何 Approved Claim

---

## 附錄：v2 → v2.1 對照速查

| 面向 | v2 | v2.1 |
|---|---|---|
| SHACL | 17 個 SPARQL 約束，pySHACL 載不進去 | Core（35 NodeShape、0 `sh:sparql`）＋ SPARQL audit（19 約束），27 個 canary 實測 |
| 裁決規則 | 7 條 | 15 條；anchor 不裁決數值、crude 2×2 不打敗校正、null 三分、規則順序修正 |
| GRADE | 統計量直接變 domain rating，多處 fail-open | indicators → 人類判斷 → 確定性聚合；advisory override 完全隔離 |
| 品質閘門 | 單一門檻，SHACL 用 `3/n` 重算並誤拒 n=299 | Python 精確計算，SHACL 只驗方法與結果；coverage/accuracy/major-error 三分 |
| OutcomeInventory | 單一狀態，schema 與 matcher 未對接 | draft/scoped 兩階段；AST 漂移偵測 ＋ round-trip |
| 契約凍結 | 只有一個 hash 欄位 | 正規化雜湊排除自身 ＋ 三類凍結前置檢查 |
| 編碼 | CP950 下測試跑不起來 | 全面 UTF-8 ＋ `configure_stdio()` |
| 驗證 | 「36 項交叉驗證」，SHACL 未實際載入 | `verify --all` 十階段，全部實際執行；其中 3、4、6、7、8、9、10 經故障注入確認會變紅 |
