# ADR-0001：SHACL Core、SPARQL audit 與確定性 gate 的責任邊界

- 狀態：已接受
- 日期：2026-08-13
- 情境：v2 把所有阻擋規則都寫成 SHACL-SPARQL，本機實測時全部靜默失效

## 問題

v2 的設計是「所有約束都是 SHACL」，聽起來乾淨。實測時 pySHACL 對 17 條
SPARQL 約束回報 `Unknown namespace prefix : ahig`——這些約束依賴 rdflib
的 namespace 回退，換一個處理器就全部失效。

更根本的是三個規範層面的性質：

1. **`sh:conforms` 是全有全無的**。只要驗證報告裡有任何一筆結果，`conforms`
   就是 false，不分 severity。把「缺必填欄位」和「建議補上 rationale」放在
   同一份 shapes graph，結果是後者會擋住前者的放行。
2. **Core-only 處理器可以合法忽略 `sh:sparql`**。這是 SHACL 1.0 Recommendation
   允許的。把安全防線建在一個處理器可以合法跳過的機制上，等於沒有防線。
3. **SHACL 不擅長跨節點與時間運算**。「監控是否逾期」需要
   `lastSuccessfulCheckAt + maxAgeHours + graceHours` 與當下時間比較；
   用 SPARQL 硬寫得出來，但可讀性與可測性都遠差於幾行 Python。

## 決策

**三層，責任不重疊：**

| 層 | 負責 | 不負責 |
|---|---|---|
| SHACL Core（`shapes/core/`）| 結構性阻擋：必填、基數、資料型別、列舉 | 跨節點、日期、聚合 |
| SHACL-SPARQL（`shapes/sparql/`）| pinned audit profile，複雜關係的稽核 | **不作為唯一安全防線** |
| 確定性 Python gate | 跨節點、日期、聚合、精確統計 | 結構性形狀 |

**Core profile 零 `sh:sparql`。** 這是可測的：有一條測試掃描 core 檔案，
出現 `sh:sparql` 即失敗。

**shapes 拆成 approval-core 與 advisory-quality。** severity 不會繼承，
所以「阻擋」與「建議」必須是不同的 shapes graph，不能靠 severity 區分。

**所有 SPARQL 約束自帶 `sh:declare` / `sh:namespace`。** 不依賴任何處理器的
namespace 回退。有一條測試 `test_sparql_profile_survives_prefix_binding_loss`
刻意剝掉 graph 的前綴綁定後重跑，釘住這條性質。

**所有 property shape 具名（`ahigsh:PS-*`）並自帶 severity。** 匿名 property
shape 在驗證報告裡無法回指，negative canary 就無法斷言「命中了哪一條」。

**每條 critical constraint 有 positive 與 negative canary。** negative canary
必須得到 `conforms=false` **且**報告命中指定的 `sh:sourceShape`。只斷言
「有擋下來」不夠——擋錯地方也會 conforms=false。

**驗證前做 target-count preflight。** 應命中卻為 0 個 target 時回報
`TARGET_COVERAGE_FAILURE`。「shape 寫了但 targetClass 打錯字」的表現形式
就是安靜地通過。

## 後果

- 多了一層要維護（21 個 negative + 6 個 positive canary）。
- SHACL 不再是唯一真相來源，讀者需要知道去哪找對應規則。本文件就是那張地圖。
- 換 SHACL 處理器時，Core profile 應該還能用；SPARQL profile 不保證。這是
  刻意把不確定性集中到 audit 層。
