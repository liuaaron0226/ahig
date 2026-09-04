# 缺值處置的通用修法規格（交接用）

- 產出：2026-09-04（第 782 輪）　｜　依據：**ADR-0015 決策 2**（🚨 不確定必須輸出 `unresolved`，🚫 不得變相排除）
- **🚨 本文取代 `dose-reason-code-fix-spec.md`**——⚠️ 那一份只修了劑量一軸，
  **✅ 而同樣的毛病在六個軸上都有。**
- 🚫 **本室未修改任何產品碼**。

---

## 一、🚨 原則

> **⚠️ 「欄位沒有值」是一個關於**紀錄**的事實，
> **🚫 不是一個關於**這篇論文**的判斷。**
>
> **✅ 故：缺值一律輸出 `unresolved-<欄位>-not-reported`，
> 🚫 不得使用任何描述「值不合格」的理由碼。**

## 二、📮 現況：**缺值被轉成判斷，而且兩個方向都有**

| 欄位 | 🚨 缺值率（790 項） | 現在缺值時會發生什麼 | ⚠️ 方向 |
|---|---|---|---|
| `normalisedOutcomeRef` | **83%** | `notExtracted-outcome-**not-in-scope**` | 🚨 當成不合格 |
| `instrument` | **87%** | `notExtracted-instrument-**not-in-allowlist**` | 🚨 當成不合格 |
| `timepointDays`／`Sessions` | **80%** | `notExtracted-timepoint-**outside-window**` | 🚨 當成不合格 |
| `analysisSet` | **80%** | `notExtracted-analysis-set-**not-in-scope**` | 🚨 當成不合格 |
| `effectMeasure` | **78%** | `notExtracted-effect-measure-**not-in-scope**` | 🚨 當成不合格 |
| `dose` | **84%** | `notExtracted-dose-**outside-bands**` | 🚨 當成不合格 |
| `statisticalModel` | **99%** | 🚨 **靜靜套用預設 `"unadjusted"`**，⚠️ 而它在契約內 → **放行 786 項** | ⚠️ 當成合格 |
| `hasNumericResult` | **0%** | ⚠️ 預設 `True`（🚨 若缺值就會放行） | ⚠️ 當成合格（**目前潛伏，未觸發**） |

> **🚨 一個軸靠「缺值＝不合格」擋掉 647 項；
> 另一個軸靠「缺值＝預設合格」放行 786 項。**
> **✅ 兩者是同一個問題的兩面：把「沒有值」變成了實質判斷。**

## 三、✅ 修法

**1. 每一個「值不在允許集合」的分支，先分出「欄位缺值」：**

```python
def _absent(reported, field):
    return field not in reported or reported[field] is None

# 例：分析集
if _absent(reported, "analysisSet"):
    return ScopeDecision(False, "unresolved-analysis-set-not-reported", m,
                         "SCOPE-003a-analysis-set-unresolved")
if reported["analysisSet"] not in self.analysis_sets:
    return ScopeDecision(False, "notExtracted-analysis-set-not-in-scope", m,
                         "SCOPE-003-analysis-set")
```

⚠️ 同樣的形狀套用於 `normalisedOutcomeRef`、`instrument`、`timepoint`、
`effectMeasure`、`dose`。

**2. 兩個「預設合格」的地方改成顯式：**

- `statisticalModel`：🚫 不要 `.get(..., "unadjusted")`。
  ✅ 缺值就是 `unresolved-statistical-model-not-reported`——
  **⚠️ 或由契約明寫「缺值視為 unadjusted」**，🚨 但那要寫在契約裡，**🚫 不是藏在預設參數裡**。
- `hasNumericResult`：⚠️ 目前 0% 缺值，🚫 故**不急**；
  ✅ 但 `.get(..., True)` 是**放寬方向的預設**，**🚨 一旦有讀者漏填就會靜靜放行。**

## 四、⚠️ 這個修法**不會**改變任何一項的收錄與否

**🚨 重要，先講清楚**：上述改動只換**理由碼**，
✅ `inScope` 的真假**完全不變**。

> ⚠️ 但它會讓 **82% 的排除理由**從「這個結局不在範圍內」
> 變成「**這一項沒有記錄結局對應**」。
> **✅ 那才是事實。**

## 五、✅ 怎麼證明改對了

| 檢驗 | 期望 |
|---|---|
| `ad7c0004c386f31c` 的 5 項（`dose` 鍵不存在） | ✅ `unresolved-dose-not-reported` |
| `8a62d501f88c7d04` 的 3 項（`dose=180`） | 🚨 **仍是** `notExtracted-dose-outside-bands` |
| 全語料 `inScopeCount` | 🚨 **仍是 98**——⚠️ 若變了，代表改動不只換碼 |
| `notExtracted-outcome-not-in-scope` 的項數 | ✅ 由 **647 降為 0**（⚠️ 因為 647 項全部是缺值） |

## 六、🚫 本規格刻意沒有處理的事

- 🚫 **不動 `decide()` 的順序。** ⚠️ 順序決定了多數項目在結局那一關就停下，
  **🚨 但改順序會改變哪一個理由碼被報出來——那是裁定問題，🚫 不是修法。**
- 🚫 **不新增理由碼以外的東西**（⚠️ 例如組別、時點單位）——✅ 那些在別的規格裡。
