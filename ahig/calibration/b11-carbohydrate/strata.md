# B.11 碳水化合物策略與肝醣管理 — 校準集抽樣框

**狀態**：契約與抽樣框已凍結（2026-08-13）。**尚未取得任何文獻。**

機器可讀版本是 `strata.json`；本檔說明每個決定背後的理由。兩者不一致時以
`strata.json` 為準（測試只讀 JSON）。

---

## 研究問題

受過訓練的成年耐力運動員（18–45 歲），在**單次**耐力運動中攝取外源性碳水化合物，
相較安慰劑、無介入或較低劑量的對照，對以下結果的影響：

| Outcome | GRADE 角色 | 量綱 | 方向 |
|---|---|---|---|
| 計時賽完成時間 | critical | `time-trial-completion-time` | 越短越好 |
| 腸胃道症狀發生率 | **critical** | `gi-symptom-incidence` | 越少越好 |
| 力竭時間 | important | `time-to-exhaustion` | 越長越好 |
| 外源性碳水氧化速率（峰值） | important | `exogenous-cho-oxidation-rate` | 越高越好 |
| 腸胃道症狀嚴重度 | important | `gi-symptom-severity-0-10` | 越低越好 |
| 運動後肌肉肝醣（乾重） | supporting | `muscle-glycogen-dry-weight` | 越高越好 |

### 為什麼 GI harms 是 critical 而不是「順便記一下」

如果 GI 不適只留在廉價的 OutcomeInventory，它就不會進 Summary of Findings 表、
不會被 GRADE 評級，也不會影響任何建議。但對實際要在比賽中吞下 90 g/h 的人來說，
「表現提升 2%」與「三成的人會拉肚子」是同一個決策的兩面。把 harms 排除在
critical 之外，等於在方法論層面預先決定了結論的方向。

因此 `gi-symptom-incidence` 是 in-scope critical outcome，且抽樣框有兩個
專屬層（S5、S6）確保它不是靠其他層的附帶回報湊數。

---

## 刻意排除的分支

| 排除項 | 理由 |
|---|---|
| RED-S / 相對能量不足 | safety-critical。錯誤建議的後果是骨質流失、內分泌抑制與停經，需要 human-expert 裁決資格與獨立的範圍契約。 |
| 低能量可用性（LEA）操弄 | 同上。且 LEA 是自變項時，碳水攝取的效果無法與能量赤字的效果分離。 |
| 快速減重／製造體重（含脫水） | safety-critical，且脫水狀態下的表現與 GI 結果不可與常態補水情境合併。 |
| 糖尿病、IBD、乳糜瀉 | 族群的 GI 反應與碳水代謝機制不同，屬臨床範疇。 |
| 18 歲以下、45 歲以上 | 另設範圍契約。 |
| 多日／慢性介入 | 本契約限定單次運動（`durationRange` 為 1 session）。肝醣裝載屬 B.18。 |

排除不等於刪除：落在排除條件內的研究若在檢索中出現，仍會被登錄在
OutcomeInventory 並標記 `notExtracted-*` 理由碼，而不是靜默丟棄
（`onOutOfScope = record-in-outcome-inventory-only`）。

---

## 分層配額（合計 60）

| 層 | 類型 | 內容 | 配額 | 這一層在壓測什麼 |
|---|---|---|---|---|
| S1 | performance | 計時賽 × 中劑量 30–59.9 g/h | 12 | 常見情境的抽取品質基準 |
| S2 | performance | 計時賽 × 高／極高劑量 ≥60 g/h | 10 | 劑量分帶邊界（SCOPE-008）、多臂研究的 `maxStudyResultsPerStudy` |
| S3 | performance | 力竭時間 | 8 | 抽取端會不會把 TT 與 TTE 併成同一個 outcome |
| S4 | mechanism | 外源性碳水氧化（示蹤法） | 10 | 測量方法異質性；`blockingConditions` 擋不擋得住不當合併 |
| S5 | harms | GI 為主要／共同主要結果 | 8 | GI harms 的正面抽取 |
| S6 | harms | GI 僅作次要或安全性結果 | 7 | `completenessAttestation.harmsScan` 抓不抓得到埋在正文一句話或補充材料裡的 harms |
| S7 | mechanism | 肌肉肝醣（生檢法） | 5 | 乾重／濕重基準混用 |

配額的形狀刻意不等比於文獻母體的形狀。S6 與 S7 在真實文獻中佔比很低，
但它們是最可能暴露契約缺陷的地方——校準集的目的是找出問題，不是估計母體。

---

## 兩個危險的相等

這是本領域最容易產生**量級錯誤而非細微偏差**的地方，量綱註冊表刻意為它們設計：

**1. 肝醣的乾重 vs 濕重**

兩者的 UCUM code 完全相同（`mmol/kg`），但乾重值約為濕重值的四倍餘。
文獻中經常只在方法段落一句話交代基準。若自動換算，一個 `400 mmol/kg dw`
與 `90 mmol/kg ww` 的比較會被判定為「兩位審查者不一致」，然後由裁決規則
選出一個「勝出值」——而正確答案是兩者都對，只是基準不同。

因此濕重基準登錄為 `not-comparable`，且兩者都帶
`basis-differs-dry-vs-wet` 與 `tissue-water-content-not-measured` 兩個
blocking condition。本專案不接受以文獻通用係數（約 4.3）代替該研究實測
含水量的自動換算。

**2. TT vs TTE**

兩者都是「秒」。但計時賽是「完成固定距離要多久」（越短越好），力竭時間是
「固定強度能撐多久」（越長越好），且 TTE 的變異係數顯著較高。單位相同、
方向相反、構念不同——這是最容易在合成階段同號相加的組合。兩者登錄為不同的
`comparabilityClass`，任何情況下都不得併入同一效果量。

---

## 本校準集能證明什麼、不能證明什麼

**能**：暴露範圍契約的缺陷、量測實際工時、量測雙審分歧率與確定性裁決的
coverage/accuracy、檢驗量綱 blockingConditions 是否真的擋得住不當合併。

**不能**：證明品質閘門達標。

零錯誤下，60 篇的 95% Clopper–Pearson 精確上界是 **4.87%**。要把錯誤率上界
壓到 1% 以下，零錯誤需要 **299 篇**。因此 `strata.json` 顯性寫著
`sufficientForOnePercentCeiling: false`——這個欄位存在的唯一理由，是讓
「60 篇校準完成」不會在後續文件裡被讀成「品質閘門已通過」。

### Scope gold 目標

| 指標 | 目標 | 性質 |
|---|---|---|
| scope recall | ≥ 0.95 | 校準目標 |
| false exclusion rate | ≤ 0.05 | 校準目標 |
| critical harms false exclusion | **0** | 硬性 |
| SCOPE-002b（時窗重疊） | **凍結前必須為 0** | 由 `freeze_preflight` 確定性強制 |
| SCOPE-002c（同窗多測量點） | 只量測，不設門檻 | 見下 |

SCOPE-002b 與 SCOPE-002c 看起來相似，但責任歸屬完全不同。**002b 是契約作者的
錯誤**：兩個 in-scope 時窗重疊，任何落在交集的測量點都會被升級人工——這在凍結
前就能確定性檢出，所以 `freeze_contract.py` 直接擋下，不讓它進入資料階段。
**002c 是文獻本身的性質**：同一時窗內該研究測了好幾次。凍結前無從得知這種情況
有多常見，先設一個「通過率」等於先射箭再畫靶。因此本階段只量測其分佈，之後再
依實際分佈決定契約要不要從 `escalate` 改成
`take-nearest-to-window-midpoint`。

---

## 凍結與修改

契約來源是 `scope-contract.draft.json`；`scope-contract.json` 是產物。

```bash
python calibration/b11-carbohydrate/freeze_contract.py --dry-run   # 只檢查
python calibration/b11-carbohydrate/freeze_contract.py             # 寫出
```

凍結會做三件事：跑確定性前置檢查（時窗重疊、劑量帶重疊、重複 ID）、補
`frozenAt` 與 `status`、算出排除雜湊欄位自身的正規化雜湊。**不要手改
`scope-contract.json`**——手改會讓雜湊失效，`test_contract_is_frozen_and_hash_self_verifies`
會抓到。要改就改草稿後重跑。

契約改動屬實質變更時，`version` 必須升版，且已用舊版抽取的結果需依
`backfillPolicy` 處理。

---

## 明確延後的事項

- 文獻搜尋、取得與權利處理（含任何付費牆的合法免費版本搜尋）
- NotebookLM notebook 建立與引用線索的 recall/precision 實測
- 各 outcome 的文獻型 MID 登錄——本階段**所有 `midRef` 皆為 `null`**，
  GRADE 會走 `midUnavailable` 路徑並強制人工說明，而不是捏造一個門檻讓
  imprecision 評級看起來像做過 contextualised 判定
- 由本校準集產生任何 Approved Claim
