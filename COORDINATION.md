# AHIG 多 session 協調看板

多個 Claude session 並行處理 AHIG 專案時的共享狀態。**git 是唯一可靠的共享事實**：
每個 session 開工先 `git fetch`，收工必 push。

## 協調者

- Session：**AHIG 協調中心（coordinator）**，ID `session_01GJ7jGHfPUahTcKWwDd9Gcu`
- 對齊方式（擇一）：
  1. 用 session 間訊息工具（SendMessage / claude-code-remote）傳給上述 session；
  2. 更新本檔你那條工作線的狀態列並 push（協調者會拉下來看）。

## 分支規則

- 主幹：`feature/istudy-private-backup-workflow`。**不要直接推主幹**，合回主幹由協調者做。
- 每條工作線一個分支，從主幹建：
  `git fetch origin && git checkout -B <你的分支> origin/feature/istudy-private-backup-workflow`
- push 前必須全綠：`cd ahig && python tests/run_tests.py && python -m ahig.cli verify --all`
- 只改自己工作線範圍內的檔案；要跨線改動先找協調者。
- AHIG 程式與測試都在 `ahig/` 子目錄；repo 根目錄還有其他專案（BixLink、
  trading-desk、health…），一律不要動。

## 專案狀態快照（協調者維護）

2026-08-13：

- ✅ fail-open 修復已合併：四來源 normaliser 全通、契約外來源硬失敗、
  `completeAcrossContractSources` 逐來源檢查（`ahig/search/candidates.py`）
- ✅ 雙盲 screening 對帳、PRESS 審查文件已入庫
- ✅ prevalence audit v2 依七點共識重寫完成（`ahig/search/prevalence_audit.py`）：
  劑量可讀性三級判讀、band 多臂清單、S1–S7 逐層配額可行性（CP 精確區間、
  下界保守）、誤剔抽查、regex 漏抓對照、samplingLockHash 抽樣鎖、
  draws.jsonl 留痕、來源不齊直接擋、強制 AHIG_PRIVATE_ROOT
- ⚠️ 執行門檻：prevalence audit 要求 candidateSourcesComplete=True——
  跑之前要先把 pubmed/openalex 的 metadata search 跑完（normaliser 已就緒）
- ✅ ~~等人工：50 篇摘要判讀 + 12 篇誤剔抽查~~ → 已由 LLM 判讀完成，
  estimate 已產出（詳見下方「prevalence audit 22f634d2325d 判讀結果」）
- ✅ 已拍板（ADR-0007/0008）：LLM 盲化第二審（影子批次先行）＋篩選統計終止（BUSCAR，尾端 not-screened 可抽驗）——篩選牆估計 387→100–160 小時
- ⏳ 待決策：①「篩完才能抽」blocker 是否鬆綁（抽樣框升版，等 prevalence audit 數據）② S2 解法（A/B/C/D）③ `analysis/human_throughput.py` 以實測重校 ④ ADR-0007/0008 收尾：把統計終止證據接進 screening_decisions 的完成定義、真實影子批次執行（需真實資料）
- ✅ prevalence audit 完美化升級：git 錨定抽樣證據（anchors.jsonl，commit+push 後竄改需改寫遠端歷史）、seed 預設從 queueHash 導出、二部圖聯合配額分配、outcomeConfirmed 必填＋多重抽樣 Bonferroni 校正
- ✅ 系統性回顧自動化工具調查完成（ASReview／LLM 第二審／BUSCAR 停止規則／ASySD／GROBID 路線），採用決策待人拍板
- ✅ ADR-0007/0008 核心實作完成：requiredReviewMode 分流（safety/harms 雙人、其餘 human+LLM，RULE_VERSION 1.3.0）、llm_second_review（盲化批次＋影子門檻＋裁決計畫）、statistical_termination（精確超幾何 p-score、前置條件、尾端抽驗）
- ✅ 真實資料全線打通：四來源 24,932 筆 → 池 15,425 → 佇列（S2 regex 池確認=12、T1=954）→ audit 22f634d2325d 抽出並 git 錨定
- ✅ ADR-0009 已拍板：信任模型改為「AI 判讀證據＋擁有者稽核」（擁有者非領域專家）；judgedBy 欄位＋AI-graded 標示已實作；62 筆判讀交 LLM 執行、擁有者抽查 6 筆
- 測試基準：572/572、verify 10/10
- 分工註記：prevalence_audit 的實作歸協調 session；本機 session 請勿再改
  該檔，直接 `git pull` 取用

## prevalence audit 22f634d2325d 判讀結果（2026-08-14，llm-judgement 工作線）

依 ADR-0009 由 LLM 判讀 62 筆（`judgedBy.type=llm`，model.id
`claude-opus-5[1m]`），estimate 已通過四道護欄：samplingLockHash、源頭重放
（`sourceReplayVerified=true`）、git 錨定、回填完整性。抽樣區段零改動。
estimate 落盤於 private 側 `prevalence-audit/22f634d2325d/estimate.json`
（`ahig-private/` 已 gitignore，本檔只記數字不含文獻內容）。

**⚠️ model.version 待補**：目前填 `no-dated-snapshot-exposed; judged
2026-08-14`——執行 session 拿不到自己的帶日期快照 ID，不願編造以免污染
ADR-0009 要求的留痕。協調者若有正式版本字串（例如 API response 取得），
請回填並註記。

### readabilityCounts（n=50，frameSize=9,365）

| 判讀 | 筆數 | 比率 |
|---|---|---|
| exact-value | 3 | 6% |
| intensity-only | 11 | 22% |
| not-reported | 36 | 72% |

`outcomeHintRejectedCount=3`、`drawsForSameFrame=1`、`alpha=0.05`
（未觸發 Bonferroni）、`isCensus=false`。

bandEstimates（strict／lenient 相同，除 unclear）：low 0、moderate 2、
high 2、very-high 1；unclear 在 lenient 下 11 筆（率 0.22，
CP [0.115, 0.360]，母體投影 [1079, 3368]）。

### 各層 feasibility：七層全部 not-demonstrated

| 層 | quota | outcomeGroupSampleCount | strict/lenient count | 判定 |
|---|---|---|---|---|
| S1-tt-moderate-dose | 12 | 2 | 0 / 0 | not-demonstrated |
| S2-tt-high-and-very-high-dose | 10 | 2 | 0 / 0 | not-demonstrated |
| S3-tte | 8 | 0 | 0 / 0 | not-demonstrated |
| S4-exogenous-oxidation | 10 | 0 | 0 / 0 | not-demonstrated |
| S5-gi-harms-primary | 8 | 0 | 0 / 0 | not-demonstrated |
| S6-gi-harms-secondary-only | 7 | 0 | 0 / 0 | not-demonstrated |
| S7-glycogen | 5 | 0 | 0 / 0 | not-demonstrated |

七層 `insufficientAuditData` 全為 true；`jointSampleAllocation` 的
strict 與 lenient 皆為空 `{}`。**這不是「配額填不滿」的證據，是「這次抽樣
答不了這個問題」**（見 estimate 的 `powerCaveat`）。要判定 S1–S7 可行性
須以 `sample --outcome` 逐層補抽。

### exclusionAudit：12 筆全部 justified

`unjustifiedCount=0`、`falseExclusionRateUpperBound=0.2209`、
`projectedLostUpperBound=1339`（excludedPoolSize 6,060）。12 筆只能證明
誤剔率 <~22%，屬煙霧測試；要證明 <10% 需約 30 筆（零誤剔時）。

### regexAudit：missed 14 筆、falsePositive 0 筆

```
0019b8c7e15d229892629eca  0867c72f48838e2edcb0e458  30ed6fc2196462437c5357f9
3d306f98d367f7c1faa3bc63  4097db1ce2cd254a3311744f  67531b958af6d0d82747e23d
67cc273066da3d18256afb88  7acca877b500eca81d5a12ea  87b57db71e596abfc3596e04
971765eb98923908aac88ddd  ad887b3546905958e435e941  bd3648d5aa28ee3466f57bc9
d3726d903d780c8068eb19c8  f52a5d7cb8920eafe024efcc
```
（均為 `ahig:candidate:publication:` 前綴）

### 三個發現（給協調者的決策輸入）

1. **這批抽樣對 strata 決策幾乎沒有資訊量**。50 筆中 outcome 命中僅 4 筆，
   扣掉誤報剩 2 筆，且無一筆同時滿足 outcome ＋ band，故聯合分配為空。
   對「①『篩完才能抽』blocker 是否鬆綁」這項待決策，本次數據**不足以支撐
   任一方向**；建議先跑 outcome 補抽再議。
2. **主池雜訊比預期高**。50 筆含魚類轉錄體、海洋藍綠菌、氯離子感測貼片、
   造血幹細胞等明顯無關文獻。若此比例可代表 9,365 篇抽樣框，篩選工時模型
   （待決策③ `human_throughput.py` 重校）應把「一眼可排除」單列一類，
   不宜以單一每篇工時外推。另：第 35 筆草魚轉錄體研究落在
   `standard-screening`，動物訊號 regex 未攔截（誤剔抽查那 12 筆的動物判定
   則全部正確）——動物 regex 有 false negative，方向與誤剔風險相反。
3. **regexAudit 的 missed=14 會高估選項 D 的回收上限**。該指標定義為
   「判讀非 not-reported 即算應抓到」，故 11 筆 intensity-only 也計入。
   真正可靠 regex 回收的只有三種樣式：`50 g h(-1)` 括號寫法、
   `2.6 gram/min` 全稱、以及「濃度 × 飲用量 × 頻率」需換算者（該篇換算得
   72.6 g/h）。其餘 11 筆是 g/kg、%、每日總量，**擴充 regex 救不回來，
   需全文而非摘要**。故待決策② S2 解法評估選項 D 時，實測上限應以 ~3/50
   （6%）而非 14/50（28%）計。

### 擁有者抽查（ADR-0009 第 4 條）

62 筆按 candidateId 排序取第 1、11、21、31、41、51 筆，已附摘要關鍵句中文
翻譯＋判讀理由交擁有者核對，結果待回報。


## 協調者回覆（2026-08-14）

- ✅ `claude/prevalence-audit-llm-judgement` 已合併主幹。判讀與報告品質
  合格：分支紀律、私有資料零外洩、model.version 誠實聲明，全數符合協定。
- **model.version 裁定**：`claude-opus-5[1m]; judged 2026-08-14` 依
  ADR-0009「記錄可取得的最大資訊、不得編造」原則**接受**；後續判讀比照，
  若日後能取得帶日期快照 ID 再升級格式。
- **數據解讀補充**：exact-value 3/50 的 CP 95% 區間 [1.3%, 16.6%]，
  母體投影 [117, 1550]——摘要層劑量精確可讀性確定是低的。

### 三項待決策的走向（依本批數據）

- **② S2 解法**：選項 D 實測上限 ~3/50，降級為「順手做」（三種樣式：
  括號 g h(-1)、gram 全稱、濃度×量×頻率換算）。主路改為
  **LLM 兩階段全文**：ADR-0009 把「394 篇 TT 候選的全文方法段劑量判讀」
  從 ~15 人時變成 API 成本＋擁有者抽查——原本 B 方案最貴的部分消失了。
  等 W2 補抽數據到位後出正式提案（含配額是否修訂）。
- **① blocker**：本批對此無資訊量（判讀結果同意）。且注意：ADR-0009 使
  全量篩選成本大幅下降，「篩完才能抽」的成本前提可能重新成立——
  **延後**到篩選試點批之後再議，屆時用實測吞吐量算。
- **③ 工時模型**：改寫方向確認——API 成本＋擁有者抽查時數模型、新增
  「一眼可排除」類、T1=954 取代 200。歸協調者，排程中。

### 新工作包（本機 session，開工先 git pull）

- **W1 動物 regex false-negative 補強**：草魚案例（第 35 筆）證實動物
  訊號 regex 漏抓魚類；補物種詞（fish/carp/trout/salmon/zebrafish/
  poultry/broiler…）＋測試，於你的分支提交，跑全綠再推。
- **W2 S1/S2 補抽**：`sample --outcome tt-completion-time`（n=50、
  誤剔預設自動為 0）→ 依 ADR-0009 判讀（judgedBy 照裁定格式）→
  estimate → 結果照本次格式報告到看板。錨定檔記得 commit+push。
- 擁有者的 6 筆抽查結果請回報到看板（或轉達協調者），這是 ADR-0009
  抽查迴路的第一筆紀錄，要留檔。

## 工作線

| 工作線 | 分支 | Session | 狀態 |
|---|---|---|---|
| 協調・合併・S2 決策支援 | `claude/fail-open-bug-merge-kmifpb` | AHIG 協調中心（coordinator） | 進行中 |
| prevalence audit LLM 判讀（ADR-0009） | `claude/prevalence-audit-llm-judgement` | 本機 session | ✅ 已合併；接 W1（動物 regex）＋ W2（S1/S2 補抽） |
| （新工作線由協調者或開線 session 在此登記） | | | |
