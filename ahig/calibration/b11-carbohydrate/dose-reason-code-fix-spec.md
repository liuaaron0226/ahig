# 劑量理由碼之修法規格（交接用）

- 產出：2026-09-03（第 771 輪）　｜　依據：**ADR-0015 決策 2**（不確定必須輸出 `unresolved`）＋ **ADR-0016**（M1 固定測試集）
- 🚫 **本室未修改任何產品碼**——⚠️ 本文只把修法寫到「可以照著改」的程度，✅ 交給流程持有者。
- 對應測試題：`fixed-test-set.md` 第 **5／6／7** 列。

---

## 一、🚨 現在的行為

`ahig/ahig/scope/matcher.py`：

```python
def _match_dose(self, dose, unit):
    if not self.dose_bands:
        return "__no-band-constraint__"
    if dose is None:              # ← ①「沒有記錄劑量」
        return None
    for b in self.dose_bands:
        if b["unit"] == unit and b["min"] <= dose <= b["max"]:
            return b["bandId"]
    return None                   # ← ②「有劑量，但不落在任何帶內」
```

```python
band = self._match_dose(reported.get("dose"), reported.get("doseUnit"))
if band is None:
    return ScopeDecision(False, "notExtracted-dose-outside-bands", m,
                         "SCOPE-008-dose")
```

> **🚨 ① 與 ② 回傳同一個 `None`，於是被貼上同一個碼。**
> ⚠️ 而那個碼講的是一件**具體的事**：「劑量在帶外」。
> **🚫 對 ① 來說那句話是假的——它根本沒有劑量可以在帶外。**

## 二、⚠️ 語料裡實際上是三件事（第 770 輪逐項查證）

| 實際狀況 | 項數 | 篇數 | 目前的碼 | ✅ 應該是 |
|---|---|---|---|---|
| 🚨 **`dose` 欄位不存在** | **12** | 6 | `notExtracted-dose-outside-bands` | ✅ **`unresolved`：未報告劑量** |
| ⚠️ **`dose = 0 g/h`（對照組）** | **4** | 1 | 同上 | ✅ **辨認為對照組**（📮 見第五節） |
| ✅ **`dose = 180 g/h`** | **3** | 1 | 同上 | 🚨 **維持不變**（契約上限 150，真的帶外） |

## 三、✅ 建議的修法（最小改動）

**1. 讓 `_match_dose` 把兩種 `None` 分開：**

```python
DOSE_NOT_REPORTED = "__dose-not-reported__"

def _match_dose(self, dose, unit):
    if not self.dose_bands:
        return "__no-band-constraint__"
    if dose is None:
        return DOSE_NOT_REPORTED     # ← ✅ 不再與「帶外」共用回傳值
    for b in self.dose_bands:
        if b["unit"] == unit and b["min"] <= dose <= b["max"]:
            return b["bandId"]
    return None
```

**2. 讓 `decide()` 分開處置：**

```python
band = self._match_dose(reported.get("dose"), reported.get("doseUnit"))
if band is DOSE_NOT_REPORTED:
    return ScopeDecision(False, "unresolved-dose-not-reported", m,
                         "SCOPE-008a-dose-unresolved")
if band is None:
    return ScopeDecision(False, "notExtracted-dose-outside-bands", m,
                         "SCOPE-008-dose")
```

⚠️ **一個實作上的細節，先講清楚**：`reported.get("dose")` 對「**鍵不存在**」與
「**鍵存在但為 null**」給同一個答案。
✅ **在這一層那沒關係**——🚨 兩者對判定的意義相同：**沒有劑量可用。**
（⚠️ 但在**清冊品質**的層次上那是兩件事，🚫 不要在別處把它們也混起來。）

## 四、✅ 怎麼證明改對了（三向，缺一不可）

| 篇號 | 期望 | 🚨 它擋的作弊法 |
|---|---|---|
| `ad7c0004c386f31c` | ✅ 5 項變成 **`unresolved-dose-not-reported`** | — |
| `8a62d501f88c7d04` | 🚨 3 項**仍是** `notExtracted-dose-outside-bands` | ⚠️ 防止「乾脆不用劑量擋」 |
| `307c0dd5b141caed` | 📮 4 項**不得**再被說成「帶外」 | ⚠️ 防止只換掉 ① 而不管 ② |

**🚨 只驗第一篇會過關的爛改法**：把 `SCOPE-008-dose` 整條拿掉。
**✅ 第二篇會立刻把它打回。**

## 五、📮 一項需要裁定，🚫 本室不自行決定

**對照組（`dose = 0 g/h`）該怎麼記？** ⚠️ 兩種都說得通：

1. ✅ **獨立理由碼**（例如 `notExtracted-control-arm`）——
   🚨 好處：對照組是**設計的一部分**，不是資料缺陷。
2. ⚠️ **視為 `unresolved`**——🚫 缺點：它其實一點也不 unresolved，**我們很清楚它是 0。**

**🚨 本室傾向第 1 種**，⚠️ 但那牽涉 `ADJUDICATION_CAUSES`／理由碼清單的擴充，
**📮 故請協調者裁定後再動。**

## 六、🚫 本室刻意**沒有**寫進規格的東西

⚠️ 還有一種可以想像的混淆：**劑量有值，但單位不在帶的單位裡**（例如 `g/min`）。
🚨 **目前語料裡沒有任何一項是這樣**（19 項的單位全是 `g/h` 或缺）。
**✅ 故本室不建議先寫那段——🚫 沒有實例的分支，是投機性需求。**
