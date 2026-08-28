# M1 · 己類交付檢查清單（跨章節）

**⚠️ 本檔不是章節，是交付當日照著跑的清單。**
四份骨架各有一份佔位符來源表，**分開看不出三件事**：
哪些來源協調者根本開不到、哪些數字彼此單位不同、哪一個雜湊掛錯了區塊。
**本檔把四份合為一份，並補上「來源型態」與「定位」兩欄。**

**本檔之對應義務（清冊己類三條）**：
看板 48414（交付前應重查）、48897（**不得沿用任何一輪之數字**）、
49308（**敘述式估計不得以單一數字呈現**）。

**⚠️ 表格由 `.scratch/n115_delivery_checklist.py` 產生，不得手改**；
散文部分為協調者撰寫（同 `docs/m1-wording-checklist.md` 之體例）。
**🚨 該腳本設有斷言**：骨架若新增一個沒有定位的佔位符，**腳本會擋下來**，
不會讓它無聲地走到交付。

---

## 一、佔位符總表

<!-- BEGIN GENERATED n115 -->

共 **33** 個佔位符。凍結 **25**、漂移 **8**；其中 **8** 個之權威來源**協調者無法自行核對**（見下文第二節）。

| 節 | 佔位符 | 類別 | 來源型態 | 定位 |
|---|---|---|---|---|
| 甲 | `COLLISION_N` | 漂移 | 不可及 | 🚨 碰撞清單檔未入版控 |
| 甲 | `ORPHAN_N` | 凍結 | 看板 | 看板 23514–23515；⚠️ 私有根之 `critical-harms-sweep-orphans` 工作單協調者不可及 |
| 乙 | `SEX_REPRESENTATION` | 凍結 | 看板 | 看板 49702 之量測（無產物、無雜湊） |
| 乙 | `TITLE_ONLY_N` | 漂移 | 不可及 | 名冊檔在私有根；🚨 不得以判讀理由文字代算 |
| 丙 | `ALPHA` | 凍結 | 原始碼 | `statistical_termination.py` `DEFAULT_ALPHA` = 0.05 |
| 丙 | `NOT_SCREENED_STD` | 漂移 | 產物 | `.scratch/n78_termination_evidence.json` → `tailSpotCheckPopulation.count`（**閉合式之第三項**） |
| 丙 | `N_TOTAL_STD` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `standardLaneSequence.nTotal` |
| 丙 | `OCC1_HITS` | 凍結 | 產物 | `.scratch/n68_tail_result.json`（⚠️ 命中 2 筆，即絆網攔下者） |
| 丙 | `OCC1_P` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `previousOccurrence.pScore` |
| 丙 | `OCC1_PAGE` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `previousOccurrence.atPage` |
| 丙 | `OCC1_POP` | 凍結 | 產物 | `.scratch/n68_termination_evidence.json` 之尾端抽驗母體 |
| 丙 | `OCC1_W` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `previousOccurrence.windowSize` |
| 丙 | `OCC2_HITS` | 凍結 | 產物 | `.scratch/n78_tail_result.json` → `result.relevantOrUnclearFound` **之長度**（非欄位值） |
| 丙 | `OCC2_P` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `standardLaneSequence.pScore` |
| 丙 | `OCC2_POP` | 漂移 | 產物 | `.scratch/n78_termination_evidence.json` → `tailSpotCheckPopulation.count` |
| 丙 | `OCC2_W` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `standardLaneSequence.windowSize` |
| 丙 | `OUT_OF_SEQ` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `standardLaneSequence.outOfSequenceCount` |
| 丙 | `PAGES_BETWEEN` | 凍結 | 推導 | 🚨 **兩種讀法，尚未裁定**——見下文第四節（四） |
| 丙 | `P_ALLQUEUE` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `evaluateTerminationStandardBasis.pScore`（⚠️ 僅用於呈示禁句） |
| 丙 | `SEQ_LEN` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `standardLaneSequence.screenedCount` |
| 丙 | `SPOT_N` | 凍結 | 原始碼 | 同檔 `DEFAULT_TAIL_SPOT_CHECK_N` = 200 |
| 丙 | `TARGET_RECALL` | 凍結 | 原始碼 | 同檔 `DEFAULT_TARGET_RECALL` = 0.95 |
| 丙 | `TRIGGER_CAUSE_ID` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `triggerCause.candidateId` |
| 丙 | `W7_ADVERSARIAL` | 凍結 | 不可及 | 🚨 同上 |
| 丙 | `W7_RANDOM` | 凍結 | 不可及 | 🚨 同上 |
| 丙 | `W7_TRIPWIRE_CATCH` | 凍結 | 不可及 | 🚨 同上 |
| 丙 | `W7_WALKS` | 凍結 | 不可及 | 🚨 W7 重放報告未入版控，協調者無法核對 |
| 丁 | `DEBT_B4` | 漂移 | 看板 | 影子歧異之尚欠項 11（未解決者，n+106 裁定；單位＝抽查項目） |
| 丁 | `DEBT_CUMULATIVE` | 漂移 | 看板 | n+108：**22**（相加 23、重疊 1，已去重） |
| 丁 | `DEBT_OUTSTANDING` | 漂移 | 看板 | n+108：**16**（W2 之 5 ∪ 影子 11）——⚠️ 單位＝**抽查項目**，非文獻 |
| 丁 | `DEBT_SETTLED` | 漂移 | 看板 | n+108：**6** |
| 丁 | `SHADOW_CONCORDANT` | 凍結 | 不可及 | `machine-reconciliation.json` 未入版控 |
| 丁 | `SHADOW_QUEUED` | 凍結 | 不可及 | 同上 |

<!-- END GENERATED n115 -->

---

## 二、🚨 有一批佔位符，其權威來源**協調者核不到**

上表「不可及」者，其權威來源在私有根或未入版控。
**⚠️ 這不是缺陷，是設計**（`ahig-private/` 依規定不得入庫），
**🚨 但它有一個交付後果必須現在講清楚**：

> **這些數字，協調者只能轉述執行室的量測，不能獨立覆核。**

**⚠️ 而「轉述他方敘述並當成自己的數據」是本 run 已記錄之缺陷型之一。**
**故交付時，此類數字一律以下列形式呈現，不得寫成協調者自己驗過**：

| 呈現要素 | 說明 |
|---|---|
| 產生指令 | 執行室須附**可重跑之指令或腳本路徑** |
| 產物雜湊 | 該量測所依據之檔案雜湊，**並註明雜湊涵蓋什麼範圍** |
| 覆核狀態 | 明寫「**執行室量測、協調者未獨立覆核**」 |

**🚨 交付前須向執行室索取者**（依上表「不可及」欄，共 8 項）：
W7 重放報告之四項數字、碰撞清單筆數、`[title-only-judged]` 名冊筆數、
影子對帳之 `machine-reconciliation.json` 兩項。

### ⚠️ 另須分清：「凍結」是交付規則，不是「有雜湊背書」

上表 25 個凍結值中，**真正落在某個雜湊原像內的是少數**（見下節之實測）。
**🚨 兩者不可混為一談**：
「凍結」的意思是**交付時原樣引用、不重算**；
「有雜湊」的意思是**稽核者可比對一個字串**。
**⚠️ 看板型與不可及型之凍結值，兩者都不具備第二項。**

---

## 三、✅ 證據鏈之雜湊：**全部定位完成、逐一比對相符**（本輪實測）

`.scratch/n115_hash_scopes.py` 對六步證據鏈之十個產物、
逐一試算每個 `*Hash` 欄之涵蓋範圍：

```
依欄位計：自證 10 ｜ 引用且與上游比對相符 16 ｜ 未定位 0
依雜湊值計：相異值 11 ｜ 至少一檔可自證 10 ｜ 無一檔可自證 1
```

- **自證**＝該雜湊由本檔內容算出，**且本輪已重算重現**；
- **引用**＝該值由上游步驟算出、抄入以串接鏈路，
  **且實測與上游同值**（故鏈路確實接得起來，不是各寫各的）。

**⚠️ 兩種計法都要報，因為依欄位計會蓋掉一件事**：
一個值可能在每個檔案裡都只是被抄來抄去，**沒有任何一檔算得出它**。
本組唯一這樣的是 **`screeningQueueHash`**（四處出現、皆相同 ✅），
**其原像為工作單檔，在私有根**——屬設計使然，但報告須寫明它是**外部錨**，
🚫 不得列為「可自版控重現」。

### 🚨 自證的 10 個，涵蓋範圍共有**五種**

| # | 涵蓋範圍 | 例 |
|---|---|---|
| 1 | 整份文件（扣除該雜湊欄） | `n68_tail_sample.json` → `sampleHash` |
| 2 | 子物件（原樣） | `n78_tail_result.json` → `resultHash`（`result`） |
| 3 | 清單本身 | `n85_tail_population.json` → `populationHash`（`candidateIds`） |
| 4 | ADR-0008 之**固定欄位原像** | 兩次觸發之 `terminationEvidenceHash`（⚠️ 且兩次欄位數不同，見（三）） |
| 5 | **本檔內容 ＋ 上游雜湊** | `informationConditionHash` ＝ `{rows, sampleHash}` |

**🚨 第 5 種猜不到**：它把本檔的 `rows` 與**上游的** `sampleHash` 綁在一起。
**⚠️ 本輪試了 50 個候選範圍全部落空，最後是讀 `.scratch/n78_step4_information.py`
第 96–97 行才知道的。** 這正是 n+100 那條規則的實例：
**先讀產生腳本，再寫驗證器；猜範圍會得到假的失敗。**

**故丙節第四節「須註明該雜湊涵蓋什麼範圍」不是體例要求，是必要條件**——
只寫欄位名，稽核者要在五種裡面猜。

---

## 四、🚨 交付前必須先解決的四件事（本輪查出）

### （一）凍結證據之**唯一一個雜湊**，掛在「不是決策」的那個區塊上

`.scratch/n78_termination_evidence.json` 內只有一處 `terminationEvidenceHash`，
**它在 `evaluateTerminationStandardBasis`**——即**全 queue 分母之比較用區塊**
（`poolSize` 15,425，`allowedToStop` **False**）。

**⚠️ 而真正作成終止決策的區塊是 `standardLaneSequence`**
（`poolSize` 9,091、`pScore` 0.012405），**它沒有自己的證據雜湊。**

**🚨 這一點必須在報告中主動寫出，不得等稽核者發現。** 正確的陳述是：

> **權威區塊之可重現性，來自 `worksheetFileSha256` 與判讀輸入可重跑，
> 而不是來自一個現成可比對的證據雜湊。**

**⚠️ 這比「有雜湊」弱，但仍是可稽核的**——差別在於稽核者必須重跑，
不能只比對一個字串。**🚫 不得寫成「終止證據已雜湊固定」。**

**🚨 且兩次觸發在這一點上不對稱，方向還是不利的那一邊**：

| | 第一次（已作廢） | 第二次（**現行有效**） |
|---|---|---|
| 整份文件自證雜湊 | **有**（`n68_termination_evidence.json` 頂層） | **無** |
| 尾端抽驗結果自證雜湊 | **無**（`n68_tail_result.json` 無 `resultHash`） | **有**（`resultHash`） |

**⚠️ 即：站得住的那一次，其證據檔沒有整份文件雜湊。**
**🚨 這不是說它不可信**——其內容仍可自工作單與判讀輸入重跑；
**但報告不得含糊帶過，須明說覆蓋到哪、沒覆蓋到哪。**

### （二）帶雜湊的那個區塊，其中一個欄位**已知被更正過**

該區塊之 `notScreenedCount` 為 **5,357**。
**而 `docs/m1-wording-checklist.md` 第四條記載：全 queue 未篩數「曾報 5,357，實為 5,115」**，
成因為六個判讀來源只計入四個。**兩者是同一個量**（同母體、同欄位）。

**🚨 而 `notScreenedCount` 在雜湊的原像裡**
（`statistical_termination.py` 第 227 行，該欄名列於 `content_hash` 之輸入）。
**⚠️ 即：今日以更正後之來源重算該區塊，雜湊必然不同。**

**✅ 已查明未受影響者（讀原始碼確認，非推測）**：
- `pScore` 由 `p_score(labels, len(queue), target_recall)` 算出（第 184 行），
  **不吃 `notScreenedCount`**；
- `allowedToStop` 之三個條件（前置條件、待納回、p < α，第 191 行）**亦不吃它**。

**🚨 故受影響的是「雜湊與該筆報數」，不是終止判斷本身。**
**⚠️ 但這句話只有在報告裡寫出來才有用**——否則稽核者重算得到不同雜湊，
**看到的是一份對不上的證據。**

**處置（依 n+82 之既定原則）**：**🚫 不得就地改該檔**——凍結產物一律不就地編輯。
以**勘誤**形式併呈：原值、更正值、成因、以及「終止判斷不受影響」之上述兩條依據。
**⚠️ 更正值 5,115 之產生指令協調者尚未取得，須向執行室索取後才可寫入報告**
（本檔第二節之規則同樣適用於它）。

### （三）🚨 兩次觸發之雜湊原像**欄位數不同**，而版本號**相同**

本輪以 ADR-0008 之原像欄位清單逐一重算，兩次皆重現，**但用的不是同一份清單**：

| 觸發 | 產物 | 原像 | 重算 |
|---|---|---|---|
| 第一次 | `n68_termination_evidence.json` → `terminationResult` | **11 欄**（無 `outOfSequenceCount`） | ✅ 重現 |
| 第二次 | `n78_termination_evidence.json` → `evaluateTerminationStandardBasis` | **12 欄**（含 `outOfSequenceCount`） | ✅ 重現 |

**⚠️ 成因可理解**：第三態（`outOfSequenceCount`）是 n+72 才立的，
**即第一次觸發時它還不存在**——原像少一欄是歷史，不是錯誤。

**🚨 真正的問題在版本號**：第一次那份自記 `schemaVersion` **1.1.0**，
**而現行程式碼同樣自記 1.1.0，卻用 12 欄原像。**
**⚠️ 即：版本號沒有隨著雜湊原像改變而改變。**

**交付後果（這才是要寫進報告的那句）**：

> **稽核者若依 `schemaVersion` 選定重算方式，第一次觸發之雜湊必然對不上，
> 而那不是證據被動過，是原像換過而版本號沒換。**

**故報告須對兩次觸發分別載明其原像欄位清單**，🚫 不得只寫「皆附證據雜湊」。
**⚠️ 並須註明第二次那份未存 `alpha` 與 `targetRecall`**
（重算時須自版控之預設值補入 0.05／0.95，**補的是版控內的值，不是猜的**）。

### （四）`PAGES_BETWEEN` 有兩種讀法，尚未裁定

第一次觸發於 `previousOccurrence.atPage` = **279**。第二次無對應欄位，可讀為：

| 讀法 | 值 | 疑慮 |
|---|---|---|
| `standardLaneSequence.contiguousPagesJudged` 299 | 20 | 那是「已判頁數」，未必等於觸發頁 |
| `triggerCause.reason` 所述之 p294 | 15 | 那是**被改判紀錄所在頁**，不是觸發頁 |

**🚨 兩種讀法都不明顯正確，故不得任選一個寫進去。**
**⚠️ 這個數字在丙節被用來支撐「兩次不是同一件事重測」**，
**故它不是可有可無的修辭**——寫錯會削弱一個實質論點。
**交付前須由執行室以其判讀序列回答「第二次觸發於第幾頁」。**

---

## 五、✅ 一項現算通過的閉合式，可直接引用

丙節第二節之分母裁定依賴池子閉合。**本輪現算成立**：

```
screenedCount 7,431 ＋ outOfSequence 200 ＋ tailSpotCheckPopulation 1,460 ＝ 9,091 ＝ nTotal ✅
judgementsEntryCount 7,631 ＝ 7,431 ＋ 200 ✅
```

**⚠️ 第二式是第一式的獨立佐證**：判讀筆數與「已篩＋第三態」兩路相符，
**表示 1,460 不是用減法湊出來的**，而是兩邊各自數出來後對得上。

---

## 六、報數之三項附註：母體、計數單位、判準

**⚠️ 本 run 已有五次「數字都對、量的不是同一件事」**（看板 64478–64484）。
**故交付時每一個數字都須附三項**，缺一即可能被讀錯：

| 附註 | 反例 |
|---|---|
| **母體** | 45 可得 vs 12 在手；勘誤 7／8／4；影子 11 vs 12 |
| **計數單位** | **抽查債 22／16／6 是「抽查項目」，而帳本各批之 50、12、11 是「文獻」** |
| **判準** | 「僅題名可判 2 筆」是資料形態，「無從判定方向 4 筆」是判讀結果 |

**🚨 計數單位那一列是本檔要求丁節修正的直接理由**：
丁節帳本表原以「筆」列各批，而更正後之總數以「項目」計，
**兩者並列會讓 62 與 22 看起來矛盾，其實是兩種東西。**

---

## 七、交付當日必做（逐項打勾，不得憑印象）

- [ ] **所有「漂移」佔位符現算**，不沿用任何一輪之值（清冊 48897）。
- [ ] **撤稿狀態重查，且逐筆確認主題涵蓋**——曾有一次由 4 改為 5，
      **新增那筆恰是唯一與運動營養直接相關者**（丁節第三節）。
- [ ] **`[title-only-judged]` 以名冊檔計**，🚫 不得以判讀理由文字統計。
- [ ] **抽查債以三欄呈現**：累計 22／已清 6／尚欠 16（n+108），**並註明單位為抽查項目**。
- [ ] **敘述式估計不得以單一數字呈現**（清冊 49308）。
- [ ] **第二節「不可及」八項**，皆已取得產生指令與雜湊，且已標示未經協調者覆核。
- [ ] **第四節四件事**皆已處置（勘誤已併呈、雜湊範圍與原像欄位已寫明、觸發頁已裁定）。
- [ ] **全文逐條過 `docs/m1-wording-checklist.md`（十一條）。**
- [ ] **42 條義務清冊逐條標註狀態**（`docs/m1-obligations.md`，⚠️ 該檔只保證不漏，不保證已辦）。
