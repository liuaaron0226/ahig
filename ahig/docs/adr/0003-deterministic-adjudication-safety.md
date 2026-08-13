# ADR-0003：確定性裁決只做「可驗真」的消解

- 狀態：已接受
- 日期：2026-08-13
- 情境：v2 的自動裁決在本機實測中自信地選出錯誤答案

## 問題

雙盲審會產生分歧。人工逐項裁決是主要的成本來源，所以「自動消解率」看起來
是個值得優化的指標。v2 把它訂在 85%。

實測揭露兩個獨立的問題。

**第一，指標被混用。** v2 的 `autoResolutionRate` 計算的是「分歧中有多少被
規則處理掉」，但文件把它當品質指標讀。這兩件事完全不同：一條「總是選 A」
的規則能達到 100% coverage 與 50% accuracy。

**第二，兩條規則會產生自信的錯誤：**

- **ADJ-005**（anchor 強度）讓標記了 exact anchor 的錯值 `24` 勝過正確的 `42`。
  anchor 只證明「這個位置存在」，不證明「這個數字是對的」。抽取者標錯位置時，
  anchor 強度反而變成錯誤答案的加分項。
- **ADJ-004**（2×2 重算）讓 crude RR `0.50` 擊敗 adjusted RR `0.80`。重算
  crude 2×2 只能驗證 crude estimand；用它去否決一個 adjusted 估計，是拿
  不同的東西比較。

## 決策

**三個指標分離，各自有名字：**

| 指標 | 意義 | 政策值 |
|---|---|---|
| `deterministicResolutionCoverage` | 分歧中被規則處理掉的比例 | 0.875（**期程指標**） |
| `deterministicResolutionAccuracy` | 對照 gold answer 的正確率 | ≥ 0.99 |
| `majorErrorCount` | 重大錯誤數 | 0 |

coverage 是期程指標——它決定人工佇列有多長，不決定結果對不對。0.875 來自
「三年、每週 10 小時」情境下的人力推算（0.8733 進位），是情境模型不是實測。

**沒有 gold 就不得出現任何 accuracy 數字。** `adjudicate_record` 在
`gold=None` 時，`metrics.goldEvaluation` 是 `None`，不是 0 也不是省略。

**數值欄位不得只因 anchor 較強而勝出。** anchor 只能定位，不能取勝。要作為
證據，anchor 必須先通過 source hash 與 field/outcome/timepoint/arm/analysis-set
的六鍵綁定驗證（`verifiedBinding`）。

**crude 2×2 只能裁決同一個 unadjusted estimand。** 新增
`ADJ-004c-crude-2x2-inadmissible`：目標是 adjusted 估計時，重算不可採。

**null 狀態三分。** `NOT_REPORTED`（論文沒報）、`CANNOT_LOCATE`（找不到，
但可能有）、`NULL_STATE_UNDECLARED`（抽取者沒說是哪一種）。前兩者意義完全
不同，混為一談會讓「找不到」被當成「不存在」。

**數值無確定性依據一律升級 `human-expert`。** 沒有可驗真的依據時，正確的
行為是承認算不出來，不是挑一個。

**單位換算讀 QuantityKind registry。** 遵守 comparability class、
instrument/method 與 blocking conditions；不作 naive 字串等值。複合單位
（`mg/(kg.d)`）不由字串推導——換算需要多個量綱對齊。

**輸出與 A/B 順序無關。** ADJ-003 回傳 registry 的 canonical unit，
不是「先出現的那個」。

**每條規則有可達 fixture，測試斷言 rule ID。** 15 條 ADJ 規則各有一個
能走到它的案例；`test_every_fixture_reaches_its_declared_rule` 確保沒有
死規則，也確保規則順序改動時會被發現。

## 後果

- 人工佇列會比 v2 的宣稱長。這是誠實的代價。
- 「85% 自動消解率」不再是單一目標數字，換成三個各有意義的指標。
- 校準集（60 篇）能量測 coverage 與 accuracy，但**不足以證明** 1% 錯誤率上界
  ——零錯誤下 60 篇的 95% 精確上界是 4.87%，1% 需要 299 篇。
