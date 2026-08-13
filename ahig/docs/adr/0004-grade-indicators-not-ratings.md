# ADR-0004：GRADE 由 indicators 經人類判斷再確定性聚合

- 狀態：已接受
- 日期：2026-08-13
- 情境：v2 讓統計量直接成為 GRADE domain rating，且有多處 fail-open

## 問題

GRADE 的五個 domain（risk of bias、inconsistency、indirectness、imprecision、
publication bias）有大量可計算的輸入：I²、τ²、Q、預測區間、OIS、MID、事件數、
Egger 檢定、registry completeness。把它們直接映射成 rating 很誘人，因為
評級是整條流程裡最耗人力的一步。

但 GRADE 明確是**判斷**框架，不是計算框架。I² = 60% 在不同的臨床情境下可以是
not-serious 也可以是 serious，取決於效果方向是否一致、異質性是否可解釋。
把統計量當 rating，等於宣稱這個判斷不存在。

實測還揭露三個 fail-open：

- **Egger 檢定 `Singular matrix` 時仍回 `not-serious`**，且不要求人工確認。
  「算不出來」變成「沒問題」——這是最糟的失效方向。
- **`apply_override` 把 moderate 改成 high**，卻同時標記
  `effectiveForApprovedClaim=false`。一份 certainty 同時是 high 又不生效，
  讀者會看到哪一個取決於他讀哪個欄位。
- **τ² = 0 時預測區間仍被用來重複降級 inconsistency**，同一件事被扣兩次。

## 決策

**三段，職責不重疊：**

```
deterministic indicators  →  human domain judgement  →  deterministic aggregation
（可計算的都算出來）          （五個，缺一不可）         （純規則，無自由度）
```

**indicators 只產生 `suggested_judgement`，不是 rating。** `DomainIndicators`
同時帶 `human_judgement_required`，明說這一步沒有結論。

**`aggregate_certainty` 只收五個生效的 `HumanDomainJudgement`。** 缺任一
domain、任一由模型作出、任一為 indeterminate、任一未確認必要旗標——一律
block，`effectiveCertainty` 為 `None`。不是降級為 very-low，是**沒有結論**。

**風險分級決定誰有資格判斷：**

- `general-clinical` — 可由 `human-self`
- `safety-critical` — 必須 `human-expert`

**Egger 相關全部 fail-closed。** 不適用（k < 10）、singular、運算失敗、
資料不足，一律回 `indeterminate` + `requiresHumanConfirmation=true`。
「算不出來」永遠不得表現為「沒問題」。

**override 完全隔離。** model override 與未核准的 override 只寫入
`advisoryOverrides` 與 `advisoryCertainty`，不觸碰 effective domain judgement
或 effective certainty。全程 `deepcopy`，避免 override 歷史污染前一版。

**MID 狀態設上限。** `provisional` 或 `unavailable` 都不足以支撐 high
certainty；`unavailable` 時 `contextualised=False` 並強制人工說明。
**不擅自創造新的 GRADE 等級**——GRADE 四級（High / Moderate / Low / Very Low）
忠實重用，無可靠 OWL 時只做 faithful SKOS encoding。

**τ² = 0 時不以預測區間重複降級 inconsistency。**

## 後果

- GRADE 評級無法自動化。這是刻意的：能自動化的部分（indicators）已經自動化，
  剩下的是判斷。
- `aggregate_certainty` 與 v2 的 `propose_certainty` 簽章不相容。後者保留為
  相容 wrapper（`ruleId = "GRADE-SUM-001-COMPAT"`），但**只產出
  `advisoryCertainty`，`effectiveCertainty` 恆為 `None`**——v2 的呼叫端傳的是
  裸的等級字串，沒有 agentClass 也沒有理由，無從確認是不是人類作出的。
  它存在是為了讓舊呼叫端明確 blocked 而不是靜默失敗，不是讓人繼續用。
- B.11 校準集所有 `midRef` 為 `null`，所以本階段任何 imprecision 判定都會
  顯性標記未做 contextualised 評級——而不是靜默當作做過。
