# AHIG 契約補丁 v2

**修補範圍：** 前一輪審查提出的 A–G 七項缺口
**狀態：** 架構契約 + 可執行參考實作。尚未修改原始 140 條目、未建立 Notebook、未上傳論文。
**日期：** 2026-08-13

---

## 本補丁的方法論立場

v1 契約的多數數字是宣告出來的，不是算出來的。本補丁把三個關鍵參數改成**實算結果**，並附上可重跑的程式：

| 參數 | v1 的來源 | v2 的來源 |
|---|---|---|
| 品質閘門的抽樣數與門檻 | 直覺 | Clopper-Pearson 封閉解 + Gwet AC1 蒙地卡羅模擬 |
| 每批領域數 | 直覺（8–12） | 佇列穩定條件推導 |
| 確定性層的效能要求 | 未定義 | 由期程與人力預算反解 |

實算結果推翻了 v1 的兩個數字，並使第三個從「定性期待」變成「可驗收的設計目標」。

所有分析可重跑：

```
analysis/sampling_power.py          # 抽樣統計
analysis/gate_inversion.py          # 閘門反解
analysis/human_throughput.py        # 人力吞吐量
analysis/adjudication_sensitivity.py # 自動消解率反解
verify.py                           # 36 項交叉驗證
reference-impl/tests/run_tests.py   # 101 項單元測試
```

---

# A. 抽取範圍契約（P0，新增；優先於 v1 的 P2-8）

## A.1 問題重述

v1 的 StudyResult 原子 tuple 有 11 個維度，且明列八種必須拆分的情況。這使 StudyResult 的產生量由「論文報告了什麼」決定。

一篇典型運動科學 RCT：5 個 outcome × 5 個時間點 × 2 個 analysis set × 2 個模型 = 100 個候選組合。

**實測（`test_scope_reduces_studyresult_count_dramatically`）：** 同一組 100 個候選，套用範圍契約後只剩 **4 個**（4%）。

全庫影響：

| | StudyResult 總數 | 人工工時（基準情境） |
|---|---:|---:|
| 無範圍契約 | 604,800 | 104,593 h（58.1 人年） |
| 有範圍契約 | 25,200 | 4,901 h（2.7 人年） |
| 降幅 | 95.8% | 95.3% |

這不是最佳化，是可行性的分界線。**因此 A 項提升為 P0。**

## A.2 定案：StudyResult 由範圍契約授權，不由論文內容決定

新增兩個節點類型：

```
ExtractionScopeContract   凍結的研究問題，決定哪些軸值組合值得抽取
OutcomeInventory          該論文報告的全部 outcome 的廉價完整清單
```

**分工是本設計的核心：**

| | OutcomeInventory | StudyResult |
|---|---|---|
| 涵蓋範圍 | 論文報告的**全部** outcome | 只有範圍內的組合 |
| 成本 | 廉價：粗座標即可，不需 anchor 驗證 | 昂貴：完整 anchor + 確定性檢查 + 雙審 |
| 產生者 | 單模型即可 | 雙盲審 + 確定性層 + 裁決 |
| 職責 | outcome-switching 偵測、backfill 依據、區分「未抽取」與「不存在」 | 支撐 Claim |

硬性規則：

- `extractionPolicy.onOutOfScope` 的唯一合法值是 `record-in-outcome-inventory-only`。**不得靜默丟棄。**
- `outcomeInventoryPolicy.required` 的唯一合法值是 `true`。缺少 OutcomeInventory 時，任何 `notExtracted-outOfScope` 標記都不可信。
- 每個 StudyResult 必須記錄 `scopeContractHash` 與 `scopeRuleId`（SHACL `ahigsh:StudyResultShape`）。
- `maxStudyResultsPerStudy` 預設 12。超過即 **escalate**，代表範圍契約定義過寬，須人工複審——**不得自動擴張，也不得截斷。**

## A.3 十三個 notExtracted 理由碼

不允許自由文字。完整列舉見 `schema/outcome-inventory.schema.json`：

```
in-scope
notExtracted-outcome-not-in-scope
notExtracted-timepoint-outside-window
notExtracted-analysis-set-not-in-scope
notExtracted-effect-measure-not-in-scope
notExtracted-subgroup-excluded-by-policy
notExtracted-sensitivity-analysis-excluded-by-policy
notExtracted-model-not-in-scope
notExtracted-instrument-not-in-allowlist
notExtracted-dose-outside-bands
notExtracted-no-numeric-result
escalated-multiple-matches-in-window
escalated-exceeds-max-studyresults
```

注意最後兩個是 `escalated-` 而非 `notExtracted-`。**同一時窗內有多個測量點時，預設行為是 escalate，不是靜默選一個。** 這是 v1 未定義而必然發生的情況。

## A.4 Backfill：範圍擴張不必重讀論文

`scope_match.backfill_candidates(inventory, old_matcher, new_matcher)` 從既有 OutcomeInventory 直接找出新進範圍的組合。

觸發條件（`backfillPolicy.triggers`）：

- `scope-contract-version-bump`
- `search-contract-version-bump`
- `new-canonical-competency-mapped`
- `user-ad-hoc-question-outside-scope`
- `mid-registry-update`

最後一項處理了 v1 未涵蓋的情境：使用者臨時問了一個 140 條目沒覆蓋的問題。答案不是繞過流水線建立第二套未治理的知識，而是**觸發範圍契約版本升級 + backfill**。

## A.5 交付物

```
schema/extraction-scope-contract.schema.json
schema/outcome-inventory.schema.json
reference-impl/scope_match.py
```

---

# B. 人工裁決者：分級、編列、與佇列穩定

## B.1 問題重述

v1 至少五處要求人工：gold set 建立、高風險主張 100% 裁決、fuzzy anchor 100% 確認、相似度 0.75–0.90 的 manual-required、數值分歧的第三順位裁決。但沒有人力預算，也沒有處理「使用者自己就是裁決者」的獨立性問題。

## B.2 實算：校準集

自動化啟用**之前**必須完成的一次性工時：

| 情境 | 閱讀 50 篇 | 300 個 gold 欄位 | 盲測比對 | **合計** |
|---|---:|---:|---:|---:|
| 樂觀 | 20.8 h | 10.0 h | 14.0 h | **44.8 h** |
| 基準 | 37.5 h | 20.0 h | 28.0 h | **85.5 h** |
| 保守 | 75.0 h | 40.0 h | 52.5 h | **167.5 h** |

到第一條 Approved Claim 的前置時間（基準情境、有範圍契約）：

| 週產能 | 校準 | 首個領域 | 合計 |
|---:|---:|---:|---:|
| 5 h/週 | 17.1 週 | 7.0 週 | **24.1 週** |
| 10 h/週 | 8.6 週 | 3.5 週 | **12.1 週** |
| 20 h/週 | 4.3 週 | 1.8 週 | **6.0 週** |

**定案：這個數字必須先被接受，才能啟動第一批。** 沒有校準集就沒有自動晉升權限，這條不放寬。

## B.3 實算：v1 的「8–12 領域/批」不成立

佇列穩定條件：每批產生的人工需求 ≤ 該批期間的人工產能（批期 4 週）。

| 情境 | 週產能 | 無範圍契約 | 有範圍契約 |
|---|---:|---:|---:|
| 基準 | 5 h/週 | 0.03 | 0.57 |
| 基準 | **10 h/週** | 0.05 | **1.14** |
| 基準 | 20 h/週 | 0.11 | 2.29 |
| 樂觀 | 20 h/週 | 0.41 | 8.25 |

**定案：**

> 批次大小不再是固定的 8–12，而是由 `floor(週產能 × 批期 ÷ 每領域人工工時)` 動態決定，且每批結束後以實測工時重算。基準情境、10 h/週下，實際上限是 **1 個領域/批**。要支撐 8 領域/批需要 **70 h/週**。

v1 的 8–12 只在「樂觀情境 + 20 h/週以上」才成立。把它寫死會讓佇列在第一批就開始無界成長。

## B.4 定案：人工裁決者分兩級

| 級別 | 定義 | 可支撐 |
|---|---|---|
| `self-adjudicated` | 使用者本人裁決 | 一般主張 |
| `expert-adjudicated` | 具證據評讀資格的外部人員 | 高風險主張的**唯一**可接受者 |

SHACL `ahigsh:HighRiskAdjudicationShape` 執行：`riskTier=safety-critical` 且 `status=approved` 但 `adjudicationLevel=self-adjudicated` → Violation。

沿用 v1 的正確處置：沒有合格 expert 時，高風險主張可以被完整收錄與標記，但**不得晉升為 Approved**。本補丁只是把它變成 SHACL 可執行的條件，並讓「誰裁決的」在主張上可見。

同一形狀另外禁止：數值分歧由第三模型或多數決裁決。

## B.5 交付物

```
analysis/human_throughput.py
analysis/results/human_throughput.json
shapes/ahig-patch-v2.shacl.ttl  (ahigsh:HighRiskAdjudicationShape)
```

---

# C. 品質閘門：修正三個互相矛盾的數字

## C.1 問題重述

v1 同時要求：

1. non-critical 抽樣「至少 10%，且不少於 30 筆」
2. non-critical error rate ≤ 1%
3. Gwet AC1 的 95% CI 下限 ≥ 0.80

這三個數字不能同時成立。

## C.2 實算一：n=30 無法驗證 1% 門檻

0 個錯誤下，Clopper-Pearson 單側 95% 上界的封閉解為 `1 − 0.05^(1/n)`：

| n | 0 錯誤下可證明的上界 |
|---:|---:|
| 30 | **9.50%** |
| 50 | 5.82% |
| 100 | 2.95% |
| 200 | 1.49% |
| **299** | **0.99%** |
| 500 | 0.60% |

**n=30 只能證明 ≤9.5%，與宣稱的 1% 差 9.5 倍。** 要證明 ≤1% 需 **n ≥ 299**（`ln(0.05)/ln(0.99) = 298.07`，二分搜尋與封閉解一致，見 `verify.py` 第 5 節）。

## C.3 實算二：AC1 的 CI 下限 ≥ 0.80 需要多大樣本

蒙地卡羅模擬，Gwet (2008) 線性化變異數 + t(df=n−1) 臨界值。判準：`P(CI 下限 ≥ 0.80) ≥ 0.80`。

| 欄位型態 | 每位評分者誤差率 | 真值 AC1 | 所需最小 n |
|---|---:|---:|---:|
| 二分類平衡 | 2% | 0.925 | **125** |
| 二分類平衡 | 5% | 0.811 | **永遠達不到** |
| 二分類平衡 | 10% | ~0.62 | 永遠達不到 |
| 二分類偏斜 90/10 | 5% | 0.884 | 300 |
| 四分類 RoB2 型 | 5% | 0.872 | 250 |
| 四分類 RoB2 型 | 10% | ~0.75 | 永遠達不到 |
| 四分類 unclear 主導 | 8% | 0.834 | **2000** |

線性化變異數已用 bootstrap 交叉驗證，三個情境的 CI 下限差異均 < 0.003。

## C.4 實算三：n=30 的實際通過率

| 欄位型態 | n | P(通過閘門) | 平均 AC1 | 平均 CI 下限 |
|---|---:|---:|---:|---:|
| 二分類平衡, 誤差 2% | 30 | **48.7%** | 0.925 | 0.813 |
| 二分類平衡, 誤差 2% | 100 | 79.5% | 0.921 | 0.847 |
| 二分類平衡, 誤差 5% | 30 | 11.7% | 0.811 | 0.604 |
| 四分類 RoB2, 誤差 5% | 30 | 20.5% | 0.872 | 0.733 |

**一個真值 AC1 = 0.925 的優秀欄位，在 n=30 時有一半機率被判為不合格。** 閘門把「證據不足」誤判成「品質不足」。

## C.5 實算四：閘門反解成可解釋的要求

`AC1 CI 下限 ≥ 0.80` 其實同時施加兩個獨立限制。把真值限制反解成每位評分者的最大誤差率：

| 欄位型態 | AC1≥0.80 需誤差率 ≤ | AC1≥0.85 需 ≤ | AC1≥0.90 需 ≤ |
|---|---:|---:|---:|
| 二分類，平衡 | **5.3%** | 3.9% | 2.6% |
| 二分類，偏斜 90/10 | 7.9% | 6.0% | 4.0% |
| 三分類，平衡 | 7.0% | 5.2% | 3.4% |
| 四分類，RoB2 型 | 8.0% | 5.9% | 3.9% |
| 四分類，unclear 主導 | 9.5% | 7.0% | 4.6% |

**在平衡二分欄位上，`AC1 ≥ 0.80` 等價於要求每位評分者的誤差率 ≤ 5.3%。** 這是個嚴格但明確的要求，值得保留——但必須用可驗證的方式表述。

## C.6 定案：把真值限制與精度限制拆開

**取代 v1 的單一門檻：**

```
【真值門檻】   AC1 點估計 ≥ 0.85
【精度門檻】   AC1 的 95% CI 下限 ≥ 0.65
【樣本門檻】   依欄位型態查表，見下
【錯誤率門檻】 error rate 的 95% 上界 ≤ 5%（n≥60），
              目標值 1% 僅在 n≥299 時才可宣稱
```

最小樣本數查表（達成上述精度門檻）：

| 欄位型態 | 最小 n |
|---|---:|
| 二分類，接近平衡（少數類 ≥ 30%） | 60 |
| 二分類，中度偏斜（少數類 10–30%） | 100 |
| 二分類，高度偏斜（少數類 < 10%） | 150 |
| 三至四分類 | 120 |
| 五分類以上 | 200 |
| 稀有類別主導（單一類別 > 70%） | 改以 gold-set accuracy 判定，不用 agreement |

**允許跨批次累積樣本。** 每批獨立計算是 v1 的隱含假設，也是使門檻不可能達成的原因之一。

**未達門檻時的處置不變：** 該欄位轉為全人工，不丟棄整批；連續兩批不通過則停止下一批並重新校準。

## C.7 定案：AC1 為主指標的實測依據

在 unclear 主導的偏斜欄位上：

| 指標 | 數值 |
|---|---:|
| Gwet AC1 | 0.830 |
| Cohen's κ | 0.622 |
| 差距 | **+0.209** |

κ 的 prevalence paradox 在此類欄位上會系統性低估一致性約 0.2。v1 選擇 AC1 為主指標是對的，本補丁補上實測佐證。κ 仍需併同報告（SHACL `ahigsh:QualityGateShape` 要求同時報告 positive agreement、negative agreement、完整交叉表與 κ，共四項）。

## C.8 零容忍項不變

以下維持 0 容忍，與樣本數無關（它們不是抽樣估計，是逐案檢查）：

- 虛構或錯誤歸屬的引用
- Approved Claim 引用缺少穩定 anchor
- 多重命中卻自動選第一筆
- 缺少 source manifestation hash
- 已撤稿來源仍被當作 active support
- effect / CI / p / event count 有未解決數學矛盾
- outcome switching 卻被標為 prespecified primary
- 權利或隱私 egress gate 違規
- 模型、prompt、schema 或搜尋契約無法追溯
- 高風險主張沒有規定的裁決者

## C.9 交付物

```
analysis/sampling_power.py
analysis/gate_inversion.py
analysis/results/sampling_power.json
analysis/results/gate_inversion.json
shapes/ahig-patch-v2.shacl.ttl  (ahigsh:QualityGateShape)
```

SHACL 執行 rule-of-three 一致性：`nonCriticalErrorCeiling < 3.0/sampleSize` → Violation。這道形狀本身就防止 v1 的矛盾再次出現。

---

# D. 監控失效的 fail-safe

## D.1 問題重述

v1 的 rights gate 有 fail-closed（metadata 不完整就拒絕），但時間維度沒有。回掃排程若靜默失敗——API 改版、rate limit、金鑰過期、排程沒跑——`sourceStatusCheckedAt` 只是停在舊時間，Approved Claim 仍然 active，系統看起來一切正常。

## D.2 定案一：拆開「嘗試」與「成功」

v1 的 `sourceStatusCheckedAt` 語意不清。拆成：

```
checkedAt                  最近一次嘗試
checkOutcome               confirmed-current | confirmed-changed | check-failed
lastSuccessfulCheckAt      只有 checkOutcome != check-failed 時才更新
```

**SLA 以 `lastSuccessfulCheckAt` 計算，不是 `checkedAt`。**

## D.3 定案二：SLA 逾期自動降級

```
now − lastSuccessfulCheckAt > (maxAgeHours + graceHours)
  → 自動轉為 stale-monitoring
  → safety-critical 必須 blocksHealthReasoning = true
```

| 風險級別 | 來源狀態 SLA | 證據重驗週期 | SLA 逾期處置 |
|---|---:|---:|---|
| safety-critical | 36 h | 1 個月 | stale-monitoring，停用於健康推理 |
| general-clinical | 10 天 | 12 個月 | flagged |
| stable-basic-science | 10 天 | 24 個月 | flagged |
| wada-dependent | 36 h | 新清單發布即暫停 | suspended |

**`stale-monitoring` 與 `suspended` 的關鍵差異：** 前者可由一次成功回掃**自動清除**，後者必須重新審查。v1 的狀態機沒有可自動恢復的狀態，若直接用 suspended 會讓一次網路故障產生大量不必要的人工重審。

## D.4 定案三：改用 change feed，不要逐筆輪詢

v1 的「高風險每日檢查來源狀態」若以逐 DOI 輪詢實作，高風險子集約 3,500 篇 = 每天 3,500 次 API 呼叫，必然撞上 rate limit。

**這是設計錯誤，不是規模問題。** 正確作法是拉變更流再與本地 DOI 集合求交集：

| feedType | strategy | 每日 API 呼叫量 |
|---|---|---:|
| `crossref-retraction-watch-dump` | change-feed-diff | 1（下載後本地 diff） |
| `crossref-updates-filter` | change-feed-diff | 少量分頁 |
| `pubmed-publication-type-query` | change-feed-diff | 少量（依日期範圍查全域撤稿再取交集） |
| `europepmc-annotations` | change-feed-diff | 少量 |
| `per-doi-poll` | per-item-poll | **需填 `perItemPollJustification`** |

schema 強制：`strategy = per-item-poll` 時必須填寫理由。這讓「逐筆輪詢」成為需要辯護的例外，而不是預設。

每次 `MonitoringRun` 記錄 `snapshotHash` 與 `snapshotRecordCount`，使回掃本身可稽核、可重現。

## D.5 定案四：連續失敗計數

`MonitoringRun.consecutiveFailureCount` 讓 SLA breach 可以在**下一次成功之前**就觸發，而不是等到成功後才發現落後。

## D.6 交付物

```
schema/monitoring.schema.json
shapes/ahig-patch-v2.shacl.ttl  (ahigsh:ClaimVersionMonitoringShape)
```

---

# E. GRADE 確定性化

## E.1 問題重述

v1 已把 RoB 2 與 AMSTAR 2 拆成 signalling question + 規則映射，但 GRADE 仍讓模型直接給 certainty——而它才是最終決定主張強度的東西。

## E.2 定案：五個 domain 中三個改為確定性計算

| Domain | 來源 | 確定性程度 |
|---|---|---|
| risk of bias | RoB 2 / ROBINS-I 規則映射（v1 已定） | 完全確定性 |
| **inconsistency** | **DerSimonian–Laird：I²、τ²、Cochran Q、預測區間** | **本補丁新增** |
| indirectness | 人工判斷 + transportability 評估 | 保留人工 |
| **imprecision** | **OIS + MID 閾值 + 總事件數** | **本補丁新增** |
| **publication bias** | **Egger 檢定（k≥10）+ registry 完整性** | **本補丁新增** |

`propose_certainty()` 由起始等級與降級量計算 proposed certainty。SHACL 要求 `certaintyDerivation ∈ {deterministic-rule, deterministic-rule-with-logged-override}`——**模型不得直接輸出 overall certainty。**

## E.3 三個實作上的正確性決定

**其一：k < 10 時不執行 Egger 檢定。** 漏斗圖不對稱檢定在小 k 下功效不足且易誤判。此時回傳 `k<10-egger-not-applicable` 並強制 `requires_human_confirmation`。SHACL 另有形狀禁止 k<10 時以 Egger 支撐 publication bias 評級。

**其二：τ² = 0 時預測區間不計入 inconsistency。** 這是實作過程中被單元測試抓到的設計錯誤。τ²=0 時預測區間變寬純粹來自小 k 的 t 乘數，那是 imprecision 的問題；在 inconsistency 降級會把同一個不確定性重複計算兩次。修正後標記 `prediction-interval-not-used-tau2-zero`。

**其三：k < 3 時 I² 不穩定，強制人工確認。**

## E.4 定案：MID 必須顯性化並版本化

運動科學多數 outcome 沒有共識 MID。若不把 MID 顯性化，certainty 就不可重現——同一批證據換個人算會得到不同結果。

`MIDRegistryEntry` 必要欄位包含 `population`（MID 是族群依賴的：同一 outcome 在未訓練者與菁英運動員的 MID 不同，必須分別登錄）、`derivationMethod`、`provenance.citationAnchor`、`revalidateBy`。

三種 MID 狀態的處置：

| midStatus | imprecision 判定 | 標記 |
|---|---|---|
| `registered` | 完整 contextualised 判定 | 無 |
| `provisional` | 可判定 | `midProvisional`，不得評為 high certainty |
| `unavailable` | 只以 OIS 與跨虛無值判定 | `midUnavailable`，強制人工確認，**不得聲稱已做 contextualised 評級** |

SHACL 禁止使用未登錄或非 active 的 MID。

種子註冊表（`registry/mid-registry.seed.json`）的所有項目都標記為 `provisional`，並在檔頭寫明**這些不是文獻共識 MID**。正式使用前必須為每個 inScopeOutcome 查找並登錄有依據的 MID，或明確登錄 `midStatus=unavailable`。

## E.5 定案：override 必須留痕，模型 override 不生效

```python
apply_override(proposal, domain, new_level, agent_class, rationale)
```

`agentClass=model` 的 override 自動帶 `effectiveForApprovedClaim=false`。SHACL 執行：模型 override 未經人工確認即用於 Approved Claim → Violation。

## E.6 交付物

```
reference-impl/grade_domains.py
schema/mid-registry.schema.json
registry/mid-registry.seed.json
shapes/ahig-patch-v2.shacl.ttl  (ahigsh:SynthesizedClaimGradeShape)
```

---

# F. NotebookLM 的觸發條件與退場條件

## F.1 問題重述

v1 把 NotebookLM 降為 RetrievalHint 是對的。但降完之後要面對：能合法上傳的只剩 OA 子集（VoR 預設拒絕、AAM 未過 embargo 拒絕、ILL 拒絕、Unknown 拒絕），而 OA 子集本機已經有 hash、解析、索引與穩定 anchor 了。

流水線裡它排在 CitationAnchor 建立**之後**，意味著它只作用於已取得全文的子集，對「發現尚未取得的文獻」毫無貢獻——這與「檢索線索層」的定位有張力。

## F.2 定案：寫入使用觸發條件

只在同時滿足以下條件時使用：

1. 單一研究問題涉及 **> 20 篇**已合法取得全文的研究
2. 該批全文全部通過 rights gate 的 `NotebookLM 上傳` 欄位
3. 任務性質為**跨文獻比較**（族群差異、介入異質性、結論矛盾定位），而非單篇抽取
4. 本機檢索已先執行，NotebookLM 的輸出用於**補充**而非取代

不滿足時直接走本機檢索 + Claude 長上下文，不付出 egress 風險與 ID 映射成本。

## F.3 定案：寫入退場條件（可量測）

在校準集上定義 **hint recall**：

> NotebookLM 的線索所指向的來源，命中 gold-standard CitationAnchor 所在來源的比例。

退場規則：

```
若 本機檢索的 hint recall ≥ NotebookLM 的 hint recall − 0.05
   且 本機檢索的 hint precision ≥ NotebookLM 的
→ 停用 NotebookLM 層，流水線改為 本機檢索 → Claude/TERRA 盲審
```

每完成 3 個批次重新量測一次。**沒有退場條件的元件會被無限期維護下去，即使邊際貢獻歸零。**

## F.4 定案：座標隔離以 SHACL 執行

`ahigsh:NotebookIsolationShape`：CitationAnchor 若出現 `notebookId`、`notebookSourceId`、`notebookChunkId`、`notebookCitationNumber` 任一 → Violation。

這把 v1 的政策宣示變成可執行的結構約束。v1 的實測發現（30 筆 reference 的 cited_text 全空、chunk_id 重複詢問會變）是這條規則的直接依據。

---

# G. SearchContract 版本化、StudyFamily 判定、量綱註冊

## G.1 SearchContract 版本演進

**問題：** v1 的流水線是「凍結 SearchContract → 搜尋」，但第一批必然學到更好的檢索式。不處理的話，前 12 個領域用 v1、後 128 個用 v3，完成度報表看起來一模一樣。

**定案：以 `changeClass` 決定 backfill 義務**

| changeClass | 意義 | backfill 義務 |
|---|---|---|
| `editorial` | 純文字修改 | 無 |
| `recall-neutral` | 檢索式改寫但 recall 不變 | 無，但須以 seed set 佐證 |
| `recall-expanding` | 新版可能找到舊版找不到的 | **必須**，範圍為所有低版本領域 |
| `recall-restricting` | 收窄 | 須記錄被排除者，不必重搜 |

`recall-expanding` 的預設 deadlinePolicy 是 `before-any-approved-claim-in-domain`：舊版本搜尋的領域可以繼續處理，但**不得晉升 Claim**。SHACL `ahigsh:SearchContractBackfillShape` 執行此條。

**changeClass 的宣告必須有證據。** `recallEvaluation` 要求以 known-item seed set 客觀量測 recall 變化（`minAcceptableSeedRecall` 預設 0.95），不接受僅憑判斷宣告 `recall-neutral`。

`blocksNewBatches` 讓版本債不會累積：未完成 backfill 前不得啟動新批次。

## G.2 StudyFamily 判定演算法

**問題：** v1 有 StudyFamily 計數欄位，沒有判定演算法。交給 LLM 判定即違反「模型不做納入決定」；全交人工又撞上吞吐量瓶頸。

**定案：三層 + 延後解析**

| tier | 訊號 | 處置 |
|---|---|---|
| tier1 | 相同 DOI / 相同 registry ID / 相同 acronym + 共同首末作者 | **自動合併** |
| tier2 | 相同 n + 相同招募時窗 + 相同地點；或 相同 n + 共同首末作者 + 相同族群描述 | suspected，**不自動合併** |
| tier3 | 作者重疊 ≥2 + 相同族群描述 + 發表年差 ≤4 | suspected，優先度較低 |
| none | 以上皆非 | 無關聯 |

**關鍵設計：tier2/tier3 的解析延後到該研究實際要支撐 Claim 時才發生。**

```
suspected + 成員屬於 claim-supporting 集合 → suspected-unresolved（進人工佇列）
suspected + 成員皆不支撐 Claim           → deferred-not-claim-supporting（零成本）
```

絕大多數文獻停在 T1/T2，永遠不需要人工解析。這把人工成本從「全庫 O(n²)」降到「僅 Claim 支撐集」。

**未解析時的安全處置：** 若 suspected 配對的兩端同時計入同一 SynthesizedClaim，該 Claim 帶 `possibleDuplicateEvidence` 標記，且 **certainty 上限為 moderate**（SHACL `ahigsh:DuplicateEvidenceCeilingShape`）。

**模型不得判定 family。** 合併會改變證據權重，屬於納入決定。SHACL 禁止 `resolvedBy.agentClass = model`。模型可提出候選，但只寫入 advisory 命名空間。

## G.3 量綱註冊表：UCUM 不夠用

**問題：** v1 寫「所有劑量與臨床單位使用 UCUM」。實測 12 個運動科學常見量：

| | 數量 |
|---|---:|
| UCUM 可完整表達 | **5** |
| 需本地定義 | **7** |

無法以 UCUM 表達者：`%1RM`、Borg RPE 6–20、Borg CR10、sRPE 訓練負荷（a.u.）、TRIMP、ACWR、整數加總量表分數。

**定案：quantity kind 註冊表，四級可比性**

| level | 意義 | 例 |
|---|---|---|
| `directly-comparable` | 可直接合併 | mg/(kg·d) |
| `comparable-after-declared-conversion` | 須宣告換算並檢查阻斷條件 | VO2max、W/kg、血乳酸、CMJ 高度 |
| `comparable-only-as-SMD` | 絕對值無共同尺度，只能標準化後比較 | sRPE 負荷（a.u.）、心理量表總分 |
| `not-comparable` | **禁止合併** | Borg 6–20 vs CR10、TRIMP 各變體、ACWR |

每項另有 `blockingConditions`：即使 level 允許，滿足任一條件時仍禁止合併。例如 CMJ 高度的 `flight-time-vs-impulse-momentum`——飛行時間法與衝量法所得高度有系統性差異，不得跨方法合併。

**GRIM/GRIMMER 的適用範圍由此註冊表決定。** 12 項中只有 **2 項**（Borg 6–20、整數加總量表）標記 `isDiscreteIntegerScale=true`。參考實作強制傳入此旗標，為 false 時回傳 `NOT_APPLICABLE` 而非 FAIL——**「不適用」與「不一致」是完全不同的結論**，v1 對此的警告在此被結構化執行。

## G.4 交付物

```
schema/search-contract-version.schema.json
schema/study-family.schema.json
schema/quantity-kind-registry.schema.json
registry/quantity-kinds.sport-science.json
reference-impl/study_family.py
```

---

# H. 衍生定案：確定性自動消解率（新增）

## H.1 為何需要這一節

吞吐量模型顯示，欄位裁決佔人工工時 **82%**（基準情境：4,032 h / 4,901 h）。這使「確定性統計攔截層」從定性要求變成有數字的設計目標。

## H.2 實算：必要的自動消解率

| 情境 | 週產能 | 目標期程 | 需自動消解率 |
|---|---:|---:|---:|
| 基準 | 10 h/週 | 2 年 | 98.7% |
| 基準 | **10 h/週** | **3 年** | **87.3%** |
| 基準 | 10 h/週 | 5 年 | 64.5% |
| 基準 | 20 h/週 | 3 年 | 53.1% |
| 樂觀 | 10 h/週 | 3 年 | 0%（不需自動化亦可） |
| 保守 | 20 h/週 | 5 年 | 85.5% |

反向：基準情境、3 年期程下，自動消解率與所需週產能的關係：

| 自動消解率 | 總人工 | 所需週產能 |
|---:|---:|---:|
| 0% | 4,901 h | 35.5 h/週 |
| 50% | 2,885 h | 20.9 h/週 |
| 70% | 2,079 h | 15.1 h/週 |
| 80% | 1,675 h | 12.1 h/週 |
| **85%** | **1,474 h** | **10.7 h/週** |
| 90% | 1,272 h | 9.2 h/週 |
| 95% | 1,071 h | 7.8 h/週 |

## H.3 定案

> **確定性層的驗收目標：對兩模型盲審產生的欄位分歧，自動消解率 ≥ 85%（在校準集上量測）。** 低於此值時，專案期程必須相應延長，或週產能必須相應提高——不得以放寬品質門檻換取進度。

## H.4 七條自動消解規則

`reference-impl/adjudication.py` 實作，全部有客觀依據：

| ruleId | 依據 |
|---|---|
| `ADJ-001-text-normalisation` | NFKC + 空白摺疊 + 連字號正規化後相同 |
| `ADJ-002-enum-synonym` | 映射到同一 canonical 列舉值 |
| `ADJ-003-unit-conversion` | 已**宣告**的換算表換算後同值 |
| `ADJ-004-numeric-recomputation` | 一方通過確定性統計檢查、另一方失敗 |
| `ADJ-005-anchor-strength` | 一方有唯一命中的逐字 anchor、另一方沒有 |
| `ADJ-006-null-vs-anchored` | 一方缺值、另一方有已驗證 anchor |
| `ADJ-007-schema-violation` | 一方的值不在 schema 允許列舉內 |

**無客觀依據時一律 `ADJ-999-no-deterministic-basis` 升級：**

- 數值型分歧 → `human-expert`（**不得**送第三模型）
- 非數值型分歧 → `third-model`
- 兩方皆有數學矛盾 → `human-expert`（`ADJ-004b`，可能是原文本身有誤）

**單元測試 `test_majority_vote_never_used_for_numeric` 以原始碼掃描驗證模組中不含任何投票邏輯**（`majority`、`vote(`、`most_common`、`Counter(`）。這是把「明確禁止多數決」變成可自動驗證的條件。

## H.5 未宣告的換算不自動消解

`same_after_conversion()` 只接受 `DECLARED_CONVERSIONS` 表內的單位對。測試 `test_undeclared_unit_pair_does_not_auto_resolve` 驗證 `5 AU` vs `5000 TRIMP` 會 escalate 而非自動換算——這正是 G.3 量綱註冊表要防的錯誤。

---

# 修正後的完整流水線

```
140 個原始能力條目（不可變 SourceCompetencyEntry）
    ↓
映射 CanonicalCompetency（多對一，原始條目不消失）
    ↓
凍結 SearchContract（含 changeClass + seed recall 佐證）
    ↓
凍結 ExtractionScopeContract          ← A 新增
    ↓
多資料庫搜尋 ＋ PRISMA-S 稽核軌
    ↓
Work / Expression / Manifestation 去重
    ↓
StudyFamily tier1 自動合併；tier2/3 進 deferred 佇列   ← G 新增
    ↓
Rights Gate ＋ Privacy Gate（fail-closed）
    ↓
本機全文 hash、解析、索引、穩定 CitationAnchor
    ↓
OutcomeInventory（完整、廉價、單模型）  ← A 新增
    ↓
ScopeMatcher 確定性判定                 ← A 新增
    ├─ out-of-scope → 只留 OutcomeInventory，零成本
    └─ in-scope     → 進入昂貴流程
        ↓
    NotebookLM 長上下文比較（僅在觸發條件成立時）  ← F 新增門檻
        ↓
    RetrievalHint（不得成為 CitationAnchor）
        ↓
    Claude 與 TERRA 獨立盲抽取
        ↓
    確定性統計攔截層（16 類檢查）
        ↓
    確定性自動消解（目標 ≥85%）          ← H 新增
        ├─ 已消解 → 續行
        └─ 升級   → 第三模型 / 人類專家 / UNRESOLVED
        ↓
    StudyResult（帶 scopeContractHash + scopeRuleId）
        ↓
    證據合成
        ↓
    GRADE：inconsistency / imprecision / publication bias 確定性計算  ← E 新增
        ↓
    SHACL 驗證（13 個 NodeShape、17 個 SPARQL 約束）
        ↓
    Immutable ClaimVersion
        ↓
    Active Approved-Claim View
        ↓
    change-feed 回掃 ＋ SLA fail-safe    ← D 新增
        ↓
    受影響 InferenceRecord 回溯
```

---

# 驗證狀態

```
單元測試        101 / 101 通過
交付物驗證       36 /  36 通過
JSON Schema      7 個檔案通過 2020-12 meta-schema 驗證
SHACL           13 個 NodeShape、17 個 SPARQL 約束，語法煙霧測試通過
數值交叉驗證     封閉解 vs 二分搜尋、解析變異數 vs bootstrap，皆一致
```

**本輪由測試發現並修正的實作錯誤一則：** GRADE inconsistency 在 τ²=0 時仍以預測區間降級，重複計算了 imprecision（見 E.3）。

**未在本沙箱驗證者：** SHACL 形狀未經 rdflib/pySHACL 實際載入（沙箱無法取得該套件）。語法煙霧測試涵蓋前綴宣告、括號平衡、`sh:sparql`/`sh:select` 配對，但**不等同於完整 SHACL 語意驗證**。在本機以 pySHACL 載入是啟用前的必要步驟。

---

# 修正後仍未收斂的部分

誠實列出，不假裝已完備：

1. **MID 註冊表是空的。** 種子檔只有 2 個 placeholder，全部標記 provisional。在為每個 inScopeOutcome 登錄有文獻依據的 MID 之前，GRADE imprecision 只能以 OIS 判定並帶 `midUnavailable`。這是下一個必須做的實質工作，且無法由架構設計代替。

2. **時間參數全部是規劃估計。** B 與 H 的所有工時數字來自明列假設，非實測。第一批跑完必須以實測重新校準 `human_throughput.py` 的參數——特別是 `model_disagreement_rate`，它直接決定 82% 的工時項。

3. **確定性自動消解率 85% 尚未在真實資料上量測。** 七條規則的覆蓋率是設計推估。校準集是第一次能驗證它的機會；若實測遠低於 85%，期程假設必須修改，而不是放寬品質門檻。

4. **indirectness / transportability 仍是純人工。** GRADE 五個 domain 中唯一沒有確定性支撐的（risk of bias 有 RoB 2 規則映射）。要確定性化需要族群特徵的結構化表示與距離度量，本補丁未處理。

5. **`escalated-multiple-matches-in-window` 的實際發生率未知。** 若運動科學研究普遍在同一時窗有多個測量點，這個 escalate 會產生比預期更多的人工。第一批應優先統計此比率。

6. **不可變模型與個人資料刪除權的張力未處理。** InferenceRecord 永久保存 + 個案資料快照識別碼。若使用者要刪除某段健康資料，需要 crypto-shredding（快照以金鑰加密，刪金鑰即失效）或 tombstone 語意，否則會留下懸空引用並破壞稽核性。單人自用可能不在乎法遵，但**懸空引用會破壞可稽核性本身**。這值得列為下一輪的 P1。
