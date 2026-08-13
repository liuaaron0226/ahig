# AHIG Domain Context

## 名稱

AHIG = Athlete Health Intelligence Graph（運動員健康智慧圖譜）。

## 核心詞彙

- **SourceCompetencyEntry**：140 個來源能力條目中的不可變原始條目。
- **CanonicalCompetency**：一或多個來源條目映射到的正規化能力節點。
- **OutcomeInventoryDraft**：模型或人工完整登錄報告結果後、尚未做範圍判定的清單。
- **ScopedOutcomeInventory**：由確定性 ScopeMatcher 加上逐項 scope decision 的清單。
- **StudyResult**：單一研究、族群、介入、比較、結果、時間點、分析族與模型下的一個結果。
- **SynthesizedClaim**：經正式證據合成後的主張，不與 StudyResult 混用。
- **CitationAnchor**：綁定 Manifestation hash 與原文 selector 的穩定引用錨點；NotebookLM ID 不是 CitationAnchor。
- **Deterministic Resolution Coverage**：分歧中由確定性規則處理的比例，不代表正確率。
- **Deterministic Resolution Accuracy**：確定性裁決與 gold answer 相符的比例。
- **Effective Certainty**：經合格人類 domain judgment 後，由 GRADE 四級規則聚合出的生效 certainty。
- **Advisory Certainty**：模型或未核准 override 的建議，不得影響 Effective Certainty。

## 邊界

- `ahig/` 只保存公開核心、schema、shapes、虛構 fixtures、gold-test 結構與公開文件。
- 個人健康 ABox 與合法全文位於外部私有資料根，不得提交到 Git，也不得預設上傳第三方服務。
- 原始 140 項能力內容維持不變；正規化只增加映射，不覆寫來源。
