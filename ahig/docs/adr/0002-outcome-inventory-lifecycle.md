# ADR-0002：OutcomeInventory 的 draft / scoped 兩階段生命週期

- 狀態：已接受
- 日期：2026-08-13
- 情境：v2 讓模型在登錄論文結果的同時填寫 `scopeDecision`

## 問題

OutcomeInventory 的用途是「這篇論文報告了哪些結果」——包含那些**不會被抽取**
的結果。它是 outcome switching 偵測與日後 backfill 的唯一依據，所以必須完整。

v2 的 schema 允許模型在同一份文件裡同時填寫「論文報告了什麼」與
「這一項在不在抽取範圍內」。問題是後者是確定性判定：給定凍結的範圍契約，
一個結果在不在範圍內沒有判斷空間。讓模型填寫，範圍契約就形同虛設——模型可以
宣稱任何東西 out-of-scope，而且沒有人查得出來，因為那份 `scopeDecision`
看起來完全合法。

實測時還發現另一個更基本的問題：**schema 合法的 inventory 餵不進 ScopeMatcher**
（缺 matcher 需要的軸），而 **matcher 產出的形狀被 `additionalProperties: false`
拒絕**。兩邊各自對著自己的 fixture 綠燈，接縫從未被測過。

## 決策

**兩個 lifecycle 狀態，由 schema 條件式強制：**

- **`draft`** — 完整登錄論文報告了什麼，含 matcher 需要的全部軸（outcome、
  instrument、timepoint、analysis set、effect measure、model、dose、subgroup、
  sensitivity）。**禁止**出現 `scopeDecision`、`scopedAt`、`scopeDecisionSummary`。
- **`scoped`** — 由確定性 ScopeMatcher 產生。每一項補上
  `scopeDecision.ruleId`、五軸 `matchedScopeElements`，且
  `decidedBy.agentClass` 是 `const: "deterministic"`。

`decidedBy.agentClass` 用 `const` 而不是 `enum`——這一格不存在「也可以是別的值」
的情況。

**out-of-scope 者被標記，不被刪除。** `onOutOfScope` 是
`const: "record-in-outcome-inventory-only"`。一份少了三項的清單與一份完整
但標記了三項的清單，在 schema 層面都合法；只有後者能支撐 switching 偵測。

**接縫由整合測試釘住，不由 fixture。** `test_scoped_output_validates_without_touch_up`
的主張是：matcher 的輸出**不需要測試端補任何欄位**就能通過 scoped schema。
另有一條 AST 掃描比對 matcher 實際讀取的軸鍵與 schema 宣告的欄位，
兩邊各自演化時必然亮紅燈。

**完整性可稽核。** `completenessAttestation` 必填，分開記錄正文、表圖、
補充材料與 harms 掃描；`registryComparison.status = "compared"` 時強制四欄
（registry ID、取得時間、比較內容、switching flags）；switching flag 非空時
強制 `dualExtracted: const true`。

這些條件式揭露過一個真實矛盾：v2 允許「空 inventory + `status: "compared"`」
通過驗證——宣稱比對過註冊資料，但清單裡什麼都沒有。

## 後果

- 多一次狀態轉換，模型的輸出不能直接當最終產物。
- 抽取端要填的軸變多了。這是把成本從「日後查不出來」前移到「現在多填幾格」。
- ScopeMatcher 成為必經路徑，不能繞過。這正是重點。
