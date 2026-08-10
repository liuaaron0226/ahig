# Trading Desk

市場資料與研究工作台。三件事：**每日資料整理**、**個股三層分析**、**歷史借鏡與策略自省**。

## 快速開始

```bash
# 每日市場資料（台股指數、籌碼、期貨、美債、VIX、全球指數、ADR 溢價率）
TSMC_CLOSE=2370 TWD_RATE=32.288 bash scripts/fetch_daily.sh 20260807

# 個股硬數據（估值、月營收、量價、法人籌碼）
bash scripts/fetch_stock.sh 2330 20260807

# 盤中即時（大盤、櫃買、權值股）
python scripts/fetch_intraday.py

# 全球指數 + 台積電 ADR 溢價率
python scripts/fetch_global.py 2370 32.288

# 查證論文引用是否真實存在（Crossref + OpenAlex，不耗搜尋額度）
python scripts/verify_citation.py "論文標題"
```

## 引用查證 ★

LLM 編造書目是最危險的失效模式——**錯誤的引用看起來和正確的一模一樣**。
`verify_citation.py` 同時查 Crossref 與 OpenAlex 兩個免費書目資料庫，
把「查證」變成機械動作而非信任問題。

```
$ python scripts/verify_citation.py "Returns to Buying Winners and Selling Losers"

  [Crossref] 被引用 8,614 次
    Jegadeesh Narasimhan; Titman Sheridan
    The Journal of Finance 1993;48(1):65-91
    DOI 10.1111/j.1540-6261.1993.tb04702.x
```

**規則：evidence-base.md 裡的每一筆引用，都必須通過這支腳本才能寫入。**

## 對抗式查證的實證結果 ★

2026-08-10 跑了 7 個研究代理產出 144 條主張，並派出獨立代理逐條反駁。
在完成查證的 **49 條中，18 條（37%）需要更正**——沒有一條是憑空捏造的引用，
但錯誤形式包括：正負號寫反、樣本期少一年、期刊掛錯、國家數錯、
把 40% 寫成 69%、排名宣稱與自己引用的來源矛盾。

> **這個 37% 就是為什麼「研究產出必須經過獨立查證」不是流程潔癖。**
> 這些錯誤單看每一條都很合理，只有實際去比對原文才會發現。

仍有 **95 條未完成查證**（工作流被中止），已在檔案中標為 ❓，**不可當結論使用**。

```bash
# 重新產生證據庫（含查證狀態徽章）
python scripts/export_research.py <journal.jsonl> docs/
```

## 文件地圖

| 檔案 | 內容 |
|------|------|
| [CONTEXT.md](CONTEXT.md) | **先讀這個**。定位、證據分級制度、詞彙表、更新機制 |
| [docs/daily-dashboard.md](docs/daily-dashboard.md) | 專業操盤手每日必看資料清單（按時間軸，含實測 API） |
| [docs/analysis-framework.md](docs/analysis-framework.md) | 個股短／中／長三層分析框架 |
| [docs/evidence-base.md](docs/evidence-base.md) | 學術依據庫（核心引用，經 Crossref/OpenAlex 雙庫查證） |
| [docs/evidence-base-research.md](docs/evidence-base-research.md) | 研究代理產出：因子、總經擇時、資金流行為（64 條） |
| [docs/history-casebook.md](docs/history-casebook.md) | 台／日／韓／美歷史事件案例庫（80 條） |
| [briefings/](briefings/) | 每日市場簡報 |
| [reviews/backlog.md](reviews/backlog.md) | **待驗證清單** — 未驗證的說法不可當結論 |

## 核心原則

1. **證據分級**：每個判斷都標 `【數據】【規則】【實證】【歷史】【推論】【待驗】`。
   沒標記的斷言 = bug。
2. **不做投資建議**：不給目標價、不說買賣、不預測明日漲跌。這是研究材料。
3. **資料抓取自動化，判讀不自動化**：自動產生的「訊號」會讓人停止思考。
4. **誠實優於完整**：查不到就寫查不到，不確定就標 low confidence。
5. **定期自我推翻**：每季檢討框架是否還成立，見 CONTEXT.md 更新機制。

## 已知限制

- 只涵蓋上市（TWSE）資料，上櫃（TPEx）需另接端點。
- 月營收 API 有數週延遲，即時資料需查 [MOPS](https://mops.twse.com.tw/)。
- 美股資料靠網路搜尋，無穩定免費 API。
- `reviews/backlog.md` 目前有 10 項未驗證說法，其中 B-01、B-02、B-08 會直接影響判讀。
