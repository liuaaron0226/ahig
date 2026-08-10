# 學術依據庫

> **收錄規則**：每一筆引用都必須通過 `scripts/verify_citation.py`（Crossref + OpenAlex 雙庫比對）
> 才能寫入。未查證的引用一律不得出現在這份文件。
>
> 狀態：**核心引用已人工查證完成；完整版正由 7 個並行研究代理擴充中（含台/日/韓/美市場史）。**

---

## 已查證引用（雙資料庫確認）

以下每一筆都經 Crossref 與 OpenAlex 交叉確認作者、年份、期刊、卷期頁。

### 動能與反轉

**Jegadeesh, N., & Titman, S. (1993).** "Returns to Buying Winners and Selling Losers:
Implications for Stock Market Efficiency." *The Journal of Finance*, 48(1), 65–91.
DOI: `10.1111/j.1540-6261.1993.tb04702.x` · 被引用 8,614（Crossref）／11,556（OpenAlex）

> 動能效應的原始論文。買進過去表現佳、賣出表現差的股票，在中期（3–12 個月）
> 產生顯著正報酬。這是金融學最被廣泛複製的異象之一。
>
> ⚠️ **適用邊界**：這是**橫斷面**（相對排序）現象，不是「漲的會繼續漲」的時間序列規律。
> 已知在市場劇烈反轉時出現極大回撤（動能崩潰）。詳細邊界待研究代理補充。

**De Bondt, W. F. M., & Thaler, R. (1985).** "Does the Stock Market Overreact?"
*The Journal of Finance*, 40(3), 793–805. · 被引用 4,063

> 長期反轉：3–5 年的輸家組合在其後期間表現優於贏家組合。與動能效應作用在
> **不同時間尺度**，兩者並不矛盾——這一點常被誤解。

### 因子模型

**Fama, E. F., & French, K. R. (1992).** "The Cross-Section of Expected Stock Returns."
*The Journal of Finance*, 47(2), 427–465. · 被引用 3,519

**Fama, E. F., & French, K. R. (2015).** "A Five-Factor Asset Pricing Model."
*Journal of Financial Economics*, 116(1), 1–22. · 被引用 7,946

> 從三因子（市場、規模、價值）擴充到五因子（加入獲利能力、投資）。

### ★ 因子失效與方法論批評（比正面證據更重要）

**McLean, R. D., & Pontiff, J. (2016).** "Does Academic Research Destroy Stock Return
Predictability?" *The Journal of Finance*, 71(1), 5–32.
DOI: `10.1111/jofi.12365` · 被引用 1,364

> **論文發表後，該因子的報酬會顯著下降。** 這直接說明：
> 你在教科書或論文上讀到的因子，很可能在你開始用的時候已經被套利掉了。
> 這是整個「因子投資」領域最重要的警告。

**Harvey, C. R., Liu, Y., & Zhu, H. (2016).** "…and the Cross-Section of Expected Returns."
*The Review of Financial Studies*, 29(1), 5–68. · 被引用 2,091

> 「因子動物園」批判：學界已發表數百個宣稱有效的因子，但在考慮多重檢定
> （data mining／p-hacking）後，多數在統計上站不住腳。作者主張顯著性門檻
> 應大幅提高（遠高於慣用的 t > 2）。
>
> **實務意涵**：看到「某某指標有效」的宣稱時，預設懷疑。這也是本專案
> `reviews/backlog.md` 存在的理由。

### 散戶行為 ★ 用台灣資料做的關鍵研究

**Barber, B. M., Lee, Y.-T., Liu, Y.-J., & Odean, T. (2009).** "Just How Much Do Individual
Investors Lose by Trading?" *The Review of Financial Studies*, 22(2), 609–632. · 被引用 807

> **用台灣證券交易所的完整交易資料**（全市場、全帳戶）研究散戶績效。
> 這是全球少數能取得完整市場微觀結構資料的研究，資料品質極高，
> 對台灣投資人的參考價值遠高於美國樣本的研究。
>
> 具體損失規模數字待研究代理查證後補上——**我不從記憶寫數字**。

---

## 待補充（研究代理進行中）

以下主題已派出研究代理，每份研究都會經對抗式查證後才併入：

| 主題 | 內容 |
|------|------|
| 橫斷面因子 | 動能崩潰、台股與亞洲市場實證、日本動能異常 |
| 總經擇時 | 殖利率曲線倒掛（含 2022–23 失效案例）、Sahm rule、Welch-Goyal 樣本外批評 |
| 資金流與行為 | 外資流向預測力、羊群效應、**期貨未平倉的資訊含量**（對應 backlog B-01） |
| 台灣市場史 | 1990 崩盤、1997、2000、2008、2020、2022、AI 行情與集中度 |
| 日本市場史 | 1989 泡沫與 35 年修復、安倍經濟學、2024 套利平倉股災、日銀正常化 |
| 韓國市場史 | 1997 IMF、半導體週期與 KOSPI、Korea Discount 與 Value-up |
| 美國市場史 | 1929／1987／2000／2008／2020／2022，以及 2026 當前估值與 2000 對照 |

---

## 查證工具

```bash
python scripts/verify_citation.py "論文標題關鍵字"
python scripts/verify_citation.py --file citations.txt   # 批次
```

**判讀要點**：
- 兩個資料庫都查不到 → 極可能是編造的引用
- 被引用次數極低的「經典論文」→ 危險訊號
- 同一篇出現多個年份（如 SSRN 工作論文 vs 正式期刊版）→ 以正式期刊版為準
- 注意線上出版年與紙本期號年可能差一年（例：Barber et al. RFS 22(2) 線上 2008／期號 2009）

---

*建立 2026-08-10 · 核心引用經 Crossref + OpenAlex 雙庫查證*
