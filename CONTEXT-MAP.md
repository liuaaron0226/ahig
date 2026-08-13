# Context Map

這個 repo 事實上已經是多 context 的：工具與微網站的工作區、市場研究工作台、
運動員健康知識圖譜，三者的詞彙與方法論並不共用。原本只有根目錄一份
`CONTEXT.md`，導致三套用語擠在同一個 glossary 裡互相污染。本檔把它們分開。

探索程式碼前，先讀與主題相關的那一份，不要三份都讀。

| Context | CONTEXT | ADR | 是什麼 |
|---|---|---|---|
| 工作區核心 | [`CONTEXT.md`](CONTEXT.md) | [`docs/adr/`](docs/adr/) | 個人 Claude 工具與微網站。`/watch` 的證據管線用語（Evidence Report、Detail Mode、Frame Budget、Dedup、Scroll Drive）以此為準。 |
| Trading Desk | [`trading-desk/CONTEXT.md`](trading-desk/CONTEXT.md) | — | 市場資料與研究流程。證據分級【數據／實證／待驗】是它的核心機制。 |
| AHIG | [`ahig/CONTEXT.md`](ahig/CONTEXT.md) | [`ahig/docs/adr/`](ahig/docs/adr/) | 運動員健康知識圖譜的公開契約、驗證器與校準契約。 |

系統層級的決策（跨 context 的邊界、私密資料的處理）放在根目錄
[`docs/adr/`](docs/adr/)；只影響單一 context 的決策放該 context 自己的
`docs/adr/`。

## 容易混淆的用語

同一個詞在不同 context 意思不同，跨 context 討論時要標明是哪一個：

- **「證據」**：在工作區核心是 `/watch` 管線輸出的畫格與逐字稿；在 Trading Desk
  是分級標記【數據／實證／待驗】；在 AHIG 是綁定 Manifestation hash 的
  CitationAnchor 與 StudyResult。三者的可稽核性標準完全不同。
- **「驗證」**：在工作區核心多指用 Playwright 實際打開頁面看；在 AHIG 指
  `python -m ahig.cli verify --all` 的十個閘門階段。
- **「coverage」**：在 AHIG 專指確定性裁決處理掉的分歧比例，**不是品質指標**
  （見 `ahig/CONTEXT.md`）。不要與測試覆蓋率混用。

## 私密資料

`health/` 是個人健康紀錄，不屬於任何一個公開 context。`ahig/` 是 AHIG 的
**公開**部分——契約、schema、shapes、虛構 fixtures 與公開文件；個人健康
ABox 與論文全文位於外部私有資料根（由 `AHIG_PRIVATE_ROOT` 指向），
不進 Git。`ahig` 的驗證入口有一個階段專門掃描私密路徑外洩。
