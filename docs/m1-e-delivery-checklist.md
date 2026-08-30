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

共 **140** 個佔位符。凍結 **55**、漂移 **85**；其中 **18** 個之權威來源**協調者無法自行核對**（見下文第二節）。

| 節 | 佔位符 | 類別 | 來源型態 | 定位 |
|---|---|---|---|---|
| 甲 | `COLLISION_N` | 漂移 | 產物 | `docs/w4b-design-inputs.md`（**受追蹤**）之 `C-*` 相異編號＝**40**（⚠️ 檔內排列非遞增，🚫 不得以「順序遞增」查完備） |
| 甲 | `ORPHAN_N` | 凍結 | 看板 | 看板 23514–23515；⚠️ 私有根之 `critical-harms-sweep-orphans` 工作單協調者不可及 |
| 乙 | `ADVANCE_EXPECTED` | 凍結 | 看板 | 同上：advance 側兩段合計期望 16.9 筆 |
| 乙 | `ADVANCE_OBSERVED` | 凍結 | 看板 | 同上：實測 1 筆 |
| 乙 | `FISHER_P` | 凍結 | 看板 | 同上：Fisher p=0.0011 |
| 乙 | `NARR_COMPARATOR_ADV` | 漂移 | 不可及 | 同上之 advance 筆數；⚠️ 這一格存在的理由就是「總數會被讀成排除數」 |
| 乙 | `NARR_COMPARATOR_N` | 漂移 | 不可及 | `.scratch/n60_tags.py` 現跑（讀私有根 `judgements.json`）；🚨 須併報排除／納入 |
| 乙 | `NARR_CRITERIA_HASH` | 漂移 | 產物 | `.scratch/n60_tags.py`（**受追蹤**）之 content_hash（CRLF→LF 正規化後 SHA-256）；⚠️ 交付時重算，值變則三個筆數須重跑 |
| 乙 | `NARR_INSTRUMENT_N` | 漂移 | 不可及 | 同上，`allowedInstruments`／「儀器效度」敘述式 |
| 乙 | `NARR_RETRACT_TEXT_N` | 漂移 | 不可及 | 同上，理由文字之撤稿字樣；🚫 不得與 `RETRACT_FIELD_N` 混用或相加 |
| 乙 | `PLANNING_RATE_F` | 凍結 | 看板 | 同上，女性 67–72% |
| 乙 | `PLANNING_RATE_M` | 凍結 | 看板 | 同上，男性 91–93% |
| 乙 | `PLANNING_RATE_OVERALL` | 凍結 | 看板 | 看板 49702：菁英層級補給規劃率（⚠️ **規劃率，非佔比**） |
| 乙 | `POP_WORDING_UNCLEAR_N` | 漂移 | 不可及 | 私有根名冊中「僅卡族群措辭」之 unclear 筆數；🚫 不得沿用看板逐輪累計（那是當輪快照） |
| 乙 | `RETRACT_FIELD_N` | 漂移 | 不可及 | **八份工作單之 `publicationTypes` 聯集去重**（n+152 一裁定之母體；🚨 原僅寫「worksheet.json」而私有根有八份、互相重疊）；⚠️ 依 n+86（十）交付時重查 |
| 乙 | `RETRACT_IN_EVIDENCE` | 漂移 | 不可及 | 上述聯集中**進入證據體**者；🚨 這一個才影響結論，🚫 不得與「篩選遇到幾筆」互換（n+152 一） |
| 乙 | `SEX_SAMPLE_COMPOSITION` | 漂移 | 不可及 | 證據體之性別組成，私有根名冊；🚨 與規劃率是兩個量 |
| 乙 | `SIGNAL_DENSITY_RATIO` | 凍結 | 看板 | 同上：標題碳水訊號密度相差 26.57 倍 |
| 乙 | `THRESHOLD3_GAP` | 凍結 | 看板 | 同上：差 0.02 倍而未放寬 |
| 乙 | `THRESHOLD3_STRATA` | 凍結 | 看板 | 看板 47448–47460：三分層之門檻 3 實測 **1.52** |
| 乙 | `THRESHOLD3_SUBGROUP` | 凍結 | 看板 | 同上：「補得到」子群體之門檻 3 實測 **1.76**（🚨 與 1.52 是兩個檢定） |
| 乙 | `THRESHOLD3_VALUE` | 凍結 | 看板 | 同上：事前門檻 1.5 |
| 乙 | `TITLE_ONLY_EXPECTED_GAP` | 漂移 | 不可及 | 🚨 **須重算**：底數 77→133→175 而衍生數一直寫「約 10」；舊率 14.7% 取自特定段落，不得直接套用（n+121） |
| 乙 | `TITLE_ONLY_N` | 漂移 | 不可及 | 私有根 `title-only-judged-roster.json` → `entryCount`＝**175**（執行室量測）；🚨 不得以判讀理由文字代算 |
| 乙 | `UNTRACEABLE_N` | 凍結 | 看板 | 看板 61541／61653：33 段設計輸入無 `candidateId` 可對應 |
| 乙 | `WORDING_SPLIT_GROUPS` | 漂移 | 看板 | 看板 7692（臨界功率兩篇）、7983（三篇同試驗）；🚨 **敘述式辨識，非掛牌統計**——不得寫成已窮舉 |
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
| 丙 | `PAGES_BETWEEN` | 凍結 | 推導 | **已定案＝20**（299 − 279）；依據見第四節（四） |
| 丙 | `P_ALLQUEUE` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `evaluateTerminationStandardBasis.pScore`（⚠️ 僅用於呈示禁句） |
| 丙 | `SEQ_LEN` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `standardLaneSequence.screenedCount` |
| 丙 | `SPOT_N` | 凍結 | 原始碼 | 同檔 `DEFAULT_TAIL_SPOT_CHECK_N` = 200 |
| 丙 | `TARGET_RECALL` | 凍結 | 原始碼 | 同檔 `DEFAULT_TARGET_RECALL` = 0.95 |
| 丙 | `TRIGGER_CAUSE_ID` | 凍結 | 產物 | `.scratch/n78_termination_evidence.json` → `triggerCause.candidateId` |
| 丙 | `W7_ADVERSARIAL` | 凍結 | 產物 | `ahig/analysis/results/synergy_replay.json`（**受追蹤**）→ `aggregate['adversarial@look100'].violationRate`＝0.3652 |
| 丙 | `W7_RANDOM` | 凍結 | 產物 | `ahig/analysis/results/synergy_replay.json`（**受追蹤**）→ `aggregate['random@look100'].violationRate`＝0.0115 |
| 丙 | `W7_TRIPWIRE_CATCH` | 凍結 | 產物 | `ahig/analysis/results/synergy_replay.json`（**受追蹤**）→ `aggregate['adversarial@look100'].meanTailCatchOnViolation`＝0.8893 |
| 丙 | `W7_WALKS` | 凍結 | 產物 | `ahig/analysis/results/synergy_replay.json`（**受追蹤**）→ `aggregate[*].walks`＝2270（六組皆同） |
| 丁 | `DEBT_B4` | 漂移 | 看板 | 影子歧異之尚欠項 11（未解決者，n+106 裁定；單位＝抽查項目） |
| 丁 | `DEBT_CUMULATIVE` | 漂移 | 看板 | n+108：**22**（相加 23、重疊 1，已去重） |
| 丁 | `DEBT_OUTSTANDING` | 漂移 | 看板 | n+108：**16**（W2 之 5 ∪ 影子 11）——⚠️ 單位＝**抽查項目**，非文獻 |
| 丁 | `DEBT_SETTLED` | 漂移 | 看板 | n+108：**6** |
| 丁 | `OBLIGATION_DISTINCT` | 漂移 | 推導 | 條目數 − 重述數；🚨 「N／N 涵蓋」之 N 是條目數，不得讀成相異義務數 |
| 丁 | `OBLIGATION_RESTATED` | 漂移 | 產物 | 同上：標為「重述／同上」之條數 |
| 丁 | `OBLIGATION_ROWS` | 漂移 | 產物 | `.scratch/n116_obligation_crosscheck.py` 之 `len(ANCHORS)`（條目數） |
| 丁 | `SHADOW_CONCORDANT` | 凍結 | 不可及 | 私有根 `machine-reconciliation.json` → `counts.concordantCount`＝**288**（執行室量測） |
| 丁 | `SHADOW_QUEUED` | 凍結 | 不可及 | 同上 → `counts.ownerAuditCount`＝**12**（執行室量測） |
| 庚 | `HARMS_ATTRIBUTABLE` | 漂移 | 產物 | `.scratch/n482_harms_adjacent_roster.json`（**受追蹤**，我已自跑覆核）→ `included` 之相異 `idPrefix`＝**3** |
| 庚 | `HARMS_COMBINED` | 凍結 | 產物 | 同上：8＋7＝**15**；✅ 與 `m1_step2_assignment.json` 之 `S5+S6-gi-merged` 配額交叉核對相符 |
| 庚 | `HARMS_COUNTER_LAST` | 凍結 | 看板 | 看板 21985 行「增至 10 筆」——**計數器之最終讀數**，其後停止維護；🚨 這是讀數，🚫 不是名單 |
| 庚 | `HARMS_RESERVE_MENTIONS` | 漂移 | 產物 | 同上 → `reserve` 之長度＝**21**；**⚠️ 單位＝提及**，🚨 實測三個 id 同時落在兩欄，🚫 三欄不得相加 |
| 庚 | `HARMS_S5_ACTUAL` | 漂移 | 不可及 | 🚨 **全文取得後才存在**；不得為填滿配額而放寬判準 |
| 庚 | `HARMS_S5_QUOTA` | 凍結 | 產物 | `ahig/calibration/b11-carbohydrate/strata.json`（**受追蹤**，我已自算覆核）→ `strata[S5-gi-harms-primary].quota`＝**8** |
| 庚 | `HARMS_S6_QUOTA` | 凍結 | 產物 | `ahig/calibration/b11-carbohydrate/strata.json`（**受追蹤**，我已自算覆核）→ `strata[S6-gi-harms-secondary-only].quota`＝**7** |
| 庚 | `HARMS_UNATTRIBUTABLE` | 漂移 | 推導 | 讀數 − 可指認者（**10 − 3 = 7**）；⚠️ 成因為五次計數器移動中兩次無 id、兩次 +2 而僅 1 個 id |
| 庚 | `S56_ACQ` | 漂移 | 產物 | 同上依層別：`S5+S6-gi-merged` 之 acquired＝**3** |
| 庚 | `S56_NONPUB` | 漂移 | 產物 | 同上：其中非刊出版＝**2**；🚨 即本契約最在意之結局，其在手全文有三分之二是作者稿 |
| 庚 | `SHORTFALL_HARMS` | 漂移 | 看板 | 同上（S5+S6） |
| 辛 | `ACQ_ALL` | 漂移 | 不可及 | 私有根 fulltext 目錄之全部 acquired manifest＝**41**（執行室量測）；⚠️ 含本工作線以外之舊工作線 |
| 辛 | `ACQ_CALIB` | 漂移 | 產物 | `.scratch/m1_step3_inventory.json` → `counts.acquired`＝**14**（我已自檔覆核） |
| 辛 | `ACQ_IN_OBTAINABLE` | 漂移 | 產物 | 🚨 n+155 取代已作廢之 `ACQUIRED_N`：**45 筆可得之中 JATS 已在手者**＝`totals.obtainable` − `n450` 之記錄數（45−33）＝**12**；⚠️ 與 `ACQ_ALL`／`ACQ_SCOPED`／`ACQ_CALIB` 皆非同一母體 |
| 辛 | `ACQ_SCOPED` | 漂移 | 不可及 | 校準 60 ＋ n+103 補集之 acquired＝**27**；🚨 n+138 曾誤標為「全體 manifest」 |
| 辛 | `ALT_HAS` | 漂移 | 產物 | `.scratch/n477_alt_oa_locations.json`：有替代位址者＝**8**（我已自算） |
| 辛 | `ALT_LANDING_ONLY` | 漂移 | 產物 | 同上：可達但僅取回書目頁＝**4**；⚠️ 是否另有可取全文未追 |
| 辛 | `ALT_NONE` | 漂移 | 產物 | 同上：查無替代位址＝**3**（🚫 非窮盡，不等於不存在） |
| 辛 | `ALT_PDF` | 漂移 | 產物 | 同上：可取得 PDF＝**4**，四筆短碼皆已見於驗收產物 ✅ |
| 辛 | `ALT_REACHABLE` | 漂移 | 產物 | 同上：其中可達＝**8**（全數） |
| 辛 | `BLOCKED_N` | 凍結 | 產物 | 同上：`survey == blocked-or-error` ＝ **11**（403 十筆＋逾時一筆） |
| 辛 | `CALIBRATION_TARGET` | 凍結 | 產物 | `ahig/calibration/b11-carbohydrate/strata.json`（**受追蹤**，我已自算覆核）→ `totalSampleSize`＝**60**；✅ 七層配額總和亦為 60 |
| 辛 | `CALIB_NONPUB` | 漂移 | 推導 | 5＋1＝**6**（校準集 14 筆中）；⚠️ 🚫 不得與 41 筆之 10 互換，兩者母體不同 |
| 辛 | `CALIB_VER_ACC` | 漂移 | 產物 | 同上：`acceptedVersion`＝**5**；🚨 每一個取自此類之數值須逐筆標記 |
| 辛 | `CALIB_VER_PUB` | 漂移 | 產物 | `.scratch/n489_calibration_versions.json`（**受追蹤**，我已自檔交叉核對）→ 校準集 acquired 中之 `publishedVersion`＝**8** |
| 辛 | `CALIB_VER_SUB` | 漂移 | 產物 | 同上：`submittedVersion`＝**1**；🚫 不得作為數值來源 |
| 辛 | `EXTRACTABLE_N` | 漂移 | 產物 | `.scratch/n492_stratum_table.json` → `totals.withBackfill`＝**27**（12 JATS ＋ 15 TEI）；🚨 n+155 更正：原註「與 `ACQ_SCOPED` 數值相同而**母體不同**」**是錯的**——⚠️ 兩者同母體，其相等是因為 `n498` 之節次一致性 41／41 全過，**🚫 無一筆被排除**；⚠️ 若日後有一筆不一致，兩數即分開 |
| 辛 | `LANDING_FIGSHARE` | 漂移 | 產物 | 同上（figshare，有 API） |
| 辛 | `LANDING_FULLTEXT_MARKER` | 凍結 | 產物 | 同上：其中有 HTML 全文標記者＝**1** |
| 辛 | `LANDING_PMC_SCAN` | 漂移 | 產物 | 同上（PMC 掃描件） |
| 辛 | `LANDING_PUBLISHER` | 漂移 | 產物 | 同上（出版社；⚠️ 經 doi.org 轉址解出後由 9 增為 13） |
| 辛 | `LANDING_REACHED` | 凍結 | 產物 | `.scratch/n450_landing_survey.json`：HTTP 200 且有內容者＝**16**（我已自算） |
| 辛 | `LANDING_REPO` | 漂移 | 產物 | `.scratch/n439_route_cost.json` → `landingKindsAggregate`（機構典藏庫）；🚨 母體＝**尚未到手之 33 筆**，🚫 不得與 `SRC_REPO` 互換 |
| 辛 | `LANDING_ROUTE_N` | 漂移 | 產物 | 同上 `available-landing-page` |
| 辛 | `LANDING_WORDS_MAX` | 凍結 | 產物 | 同上：最大 **22,761**（⚠️ 母體＝已量到之 16 筆；🚨 而此值在 33 筆母體下**也是 22,761**——**⚠️ 三格中唯一巧合相同的一格，🚫 不得據此認為三格母體相同**） |
| 辛 | `LANDING_WORDS_MED` | 凍結 | 產物 | 同上：中位 **3071.5**；🚨 **n+162 更正**：原寫 3,807，而那是 16 個排序值裡的**第 9 個**——⚠️ 偶數長度之中位數應取第 8、9 兩值之平均。🚫 該錯躲過本檢查兩輪，因定位欄未用 `＝` 而舊規則只認 `＝` |
| 辛 | `LANDING_WORDS_MIN` | 凍結 | 產物 | 同上：去標籤字數最小 **160**（⚠️ 母體＝已量到之 16 筆，🚫 非 33 筆） |
| 辛 | `LANDING_WORTH_PARSER` | 凍結 | 產物 | 同上：達門檻者＝**0**（⚠️ 就已量到的 16 筆而言，非 33 筆）；🚨 **n+162 更正**：門檻值**有存**（`criterion` 欄之 8000 字），故本格可現算＝「有全文標記且字數 ≥ 8000」；⚠️ 實測 5 筆過字數而**無標記**、1 筆有標記而僅 1805 字，交集為 0——**🚨 這是一個真的量測，🚫 不是缺判準**；⚠️ 而 `n450` 自載「門檻只用來排序，不用來決定」仍須同引 |
| 辛 | `LEGACY_DIRS` | 漂移 | 產物 | `.scratch/n496_corpus_verify.json` → `legacySchemeDirectories` 之長度＝**4**（我已自檔覆核）；🚨 不刪，僅排除並列名 |
| 辛 | `LIC_FILLED` | 漂移 | 不可及 | 私有根 acquired manifest 中具 `licenceProvenance` 欄者（執行室依 n+138（三）填入並附來源與查取日期）；⚠️ 母體為 acquired 全體，🚫 **不是首批 8 筆**（n+167 更正）；🚨 另有 24 筆之授權係自 JATS `<license>` 自動擷取、無來源欄，🚫 不得與本格相加 |
| 辛 | `OBTAINABLE_N` | 漂移 | 產物 | `.scratch/m1_step3_backfill.json` → `totals.obtainable`＝**45**（🚨 單一欄位；n+155 更正：原寫「inventory ＋ backfill」而未載合併規則，⚠️ 實則不需合併）；⚠️ **上界非保證** |
| 辛 | `PDF_IN_HAND` | 漂移 | 產物 | `.scratch/n456_pdf_textlayer.json`：**11** 檔（我已自算） |
| 辛 | `PDF_ROUTE_N` | 漂移 | 產物 | 同上 `available-pdf` |
| 辛 | `PDF_SCANNED` | 漂移 | 產物 | 同上：純掃描 **0** |
| 辛 | `PDF_TEXTLAYER` | 漂移 | 產物 | 同上：文字層 **9** |
| 辛 | `PDF_UNCERTAIN` | 漂移 | 產物 | 同上：不確定 **2** |
| 辛 | `PMC_MISS_404` | 凍結 | 產物 | 同上（已知 PMCID 但 `fullTextXML` 404） |
| 辛 | `PMC_MISS_NO_ID` | 凍結 | 產物 | `.scratch/n439_route_cost.json` → `europePmcMissCauses`（無 PMCID） |
| 辛 | `S3_ACQ_BACKFILL` | 漂移 | 產物 | 同上 → `acquiredWithBackfill`＝**1**；⚠️ 與上一格母體不同 |
| 辛 | `S3_ACQ_CALIB` | 漂移 | 產物 | `.scratch/n492_stratum_table.json`（**受追蹤**，我已自檔覆核）→ `S3-tte` 之 `acquiredCalibration60`＝**0**；🚨 全空，且曾被合計數藏住 |
| 辛 | `S3_QUOTA` | 凍結 | 產物 | `ahig/calibration/b11-carbohydrate/strata.json` → `S3-tte` 配額＝**8**（我已自檔覆核） |
| 辛 | `S7_POOL_N` | 凍結 | 看板 | 看板 63655 一帶之清點（S7 全池） |
| 辛 | `SECTIONS_OK` | 漂移 | 產物 | `.scratch/n498_sections_integrity.json` → `counts.consistent`＝**41**（我已自檔覆核） |
| 辛 | `SHORTFALL_HARMS` | 漂移 | 看板 | 同上（S5+S6） |
| 辛 | `SHORTFALL_N` | 漂移 | 看板 | 校準集設計數 − 可得數，交付時現算 |
| 辛 | `SHORTFALL_S7` | 漂移 | 看板 | 看板 63655 三之缺口分布 |
| 辛 | `SRC_NOLIC_PUB` | 漂移 | 推導 | 同上，`kind=publisher` 者；⚠️ 未記載授權之 5 份全落在典藏庫與出版社，**🚨 PMC 那批一份不缺** |
| 辛 | `SRC_NOLIC_REPO` | 漂移 | 推導 | 同上 `records` 中 `kind=repository` 且 `hasLicence=false` 者；🚨 逐筆現數，🚫 不取 `unlicensedHosts`（那一欄的鍵是主機不是類別） |
| 辛 | `SRC_PMC` | 漂移 | 產物 | `.scratch/n512_source_host_provenance.json` → `byKind.pmc`＝**26**；⚠️ 母體＝**已在手之 41 份**，🚫 不是尚未到手的 33 筆 |
| 辛 | `SRC_PUBLISHER` | 漂移 | 產物 | 同上 → `byKind.publisher`；🚨 同上不得與 `LANDING_PUBLISHER` 互換 |
| 辛 | `SRC_REPO` | 漂移 | 產物 | 同上 → `byKind.repository`；🚨 **不得與 `LANDING_REPO` 互換**——後者是尚未到手者之網站別 |
| 辛 | `SRC_UNKNOWN` | 漂移 | 產物 | 同上 → `byKind.unknown`；⚠️ `doi.org` 歸此類——**它是轉址器不是來源**，🚫 不假裝知道其指向 |
| 辛 | `UNPROBED_ALT` | 漂移 | 產物 | `.scratch/n494_alt_oa_round2.json` → 有其他位址者＝**3**（其餘 9 筆無） |
| 辛 | `UNPROBED_N` | 漂移 | 產物 | `.scratch/n493_unprobed_available.json` → `count`＝**12**（我已自檔覆核）；⚠️ 母體＝校準 60＋補集中從未試過者 |
| 辛 | `UNPROBED_PDF` | 漂移 | 產物 | 同上 → `obtainable`＝**0**；🚨 🚫 不得由此推論「替代位址法無效」——該法之前提對本批不成立 |
| 辛 | `UNTITLED_LEADING` | 漂移 | 產物 | 同上 → `totals.filesWhoseLeadingSectionIsUntitled`＝**5**；🚨 首節無標題者，摘要／前言最常在此 |
| 辛 | `UNTITLED_SECTIONS` | 漂移 | 產物 | 同上 → `totals.untitledSections`＝**20**；⚠️ 判準為空字串**或**字面 `Untitled` |
| 辛 | `VER_ACCEPTED` | 漂移 | 產物 | 同上 |
| 辛 | `VER_PUBLISHED` | 漂移 | 產物 | `n486`＋`n487`＋`n488` 合計；⚠️ 三批母體互斥 |
| 辛 | `VER_SUBMITTED` | 漂移 | 產物 | 同上；🚫 依 n+138 不得作為數值萃取來源 |
| 辛 | `VER_UNKNOWN` | 漂移 | 產物 | 同上＋`n488_pmcid_to_doi.json`；⚠️ 補查後**由 26 降為 1**，🚨 該 26 是量測缺口且集中於單一取得路徑，🚫 不得反過來當成「多半是作者稿」之證據（n+141） |
| 壬 | `DEBT_CUMULATIVE` | 漂移 | 看板 | n+108：**22**（相加 23、重疊 1，已去重） |
| 壬 | `DEBT_OUTSTANDING` | 漂移 | 看板 | n+108：**16**（W2 之 5 ∪ 影子 11）——⚠️ 單位＝**抽查項目**，非文獻 |
| 壬 | `DEBT_SETTLED` | 漂移 | 看板 | n+108：**6** |
| 壬 | `HARMS_ATTRIBUTABLE` | 漂移 | 產物 | `.scratch/n482_harms_adjacent_roster.json`（**受追蹤**，我已自跑覆核）→ `included` 之相異 `idPrefix`＝**3** |
| 壬 | `HARMS_COMBINED` | 凍結 | 產物 | 同上：8＋7＝**15**；✅ 與 `m1_step2_assignment.json` 之 `S5+S6-gi-merged` 配額交叉核對相符 |
| 壬 | `HARMS_COUNTER_LAST` | 凍結 | 看板 | 看板 21985 行「增至 10 筆」——**計數器之最終讀數**，其後停止維護；🚨 這是讀數，🚫 不是名單 |
| 壬 | `S3_QUOTA` | 凍結 | 產物 | `ahig/calibration/b11-carbohydrate/strata.json` → `S3-tte` 配額＝**8**（我已自檔覆核） |
| 壬 | `S56_ACQ` | 漂移 | 產物 | 同上依層別：`S5+S6-gi-merged` 之 acquired＝**3** |
| 壬 | `S56_NONPUB` | 漂移 | 產物 | 同上：其中非刊出版＝**2**；🚨 即本契約最在意之結局，其在手全文有三分之二是作者稿 |
| 壬 | `TAG_ROSTER_COUNT` | 漂移 | 不可及 | `.scratch/n60_tags.py` 現跑之掛牌名單份數（讀私有根）；⚠️ 份數本身會隨新掛牌而變 |
| 壬 | `TAG_ROSTER_TOTAL` | 漂移 | 不可及 | 同上，去重後合計筆數（同一筆可掛多牌）；🚨 須併報各牌之排除／納入（檢查表第十條） |

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

**「不可及」之項數以第一節表為準**（🚫 此處刻意不複寫數字——
**複寫的數字會過期，而過期的描述正是本檔一路在修的東西**）。分三批：

| 批 | 佔位符 | 狀態 |
|---|---|---|
| **已取得值與 `file_hash`** | `TITLE_ONLY_N`、`SHADOW_CONCORDANT`、`SHADOW_QUEUED` | 可寫入，須標「執行室量測、協調者未獨立覆核」 |
| **🚨 尚未索取** | `SEX_SAMPLE_COMPOSITION` | 私有根名冊 |
| **🚨 尚不存在／須重算** | `HARMS_S5_ACTUAL`、`TITLE_ONLY_EXPECTED_GAP` | 見下 |

**⚠️ 第三批之兩格特別容易被誤填**：
- **`HARMS_S5_ACTUAL` 現在還沒有值**——全文取得後才會有，
  且 🚫 不得為填滿配額而放寬主要性判準。
- **`TITLE_ONLY_EXPECTED_GAP` 有一個看板上現成的數字（「約 10」），而它已失效**——
  底數由 77 長到 `{{TITLE_ONLY_N}}` 而該數未動。**🚨 現成而過期的數字，比沒有數字更危險。**

### 🚨 第三次同型：庚節配額也在版控裡；**而追下去查出一件更要緊的事**

執行室第 451 輪指出 `strata.json` **受版控追蹤**，故 `HARMS_S5_QUOTA`／`HARMS_S6_QUOTA`／
`HARMS_COMBINED`／`CALIBRATION_TARGET` 皆非不可及。**我已自算覆核**：
S5 ＝ **8**、S6 ＝ **7**、合計 **15**、`totalSampleSize` ＝ **60**，
**且七層配額總和恰為 60 ✅**。

**⚠️ 這是我第三次把版控裡的東西標成不可及**（前兩次：W7 四格、`COLLISION_N`）。

### 🚨🚨 而覆核時，它附的 `file_hash` 對不上——追出來的原因會影響整份報告

執行室報 `file_hash(strata.json)` ＝ `sha256:373ffe26…`；
**我以其同一支函式、同一個路徑現算，得 `sha256:05045684…`。**

**⚠️ 我沒有臆測，逐一試算七種可能**，結果：

```
原樣（LF）        05045684…
LF → CRLF        373ffe26…   ✅ 與執行室所報完全相同
去尾端換行        08bc0128…
加尾端換行        0775107f…
UTF-8 BOM 版本    皆不符
```

**🚨 成因確定：執行室之 Windows 檢出為 CRLF，本室為 LF。同一份內容、不同位元組。**

> **⚠️ 故 `file_hash`（原始位元組雜湊）用在文字檔上，跨平台不可攜——
> 兩室對同一份受版控文字檔，永遠會算出不同的值。**

**🚨 交付後果**：報告若引用任何文字檔之原始位元組雜湊，
**在另一個平台上的稽核者必然對不上，而他看到的會像是檔案被動過。**

**故立為規則（n+122）**：
1. **文字／JSON 產物一律以 `content_hash`（正規化）為準**——它不吃行尾。
2. **若必須用原始位元組雜湊**（例如非 JSON 附件），
   **須同時載明「以 LF 行尾計算」**，否則該雜湊不構成可驗證的憑證。
3. **⚠️ 已知受影響者**：`worksheetFileSha256`（私有根之文字檔，我不可及）
   ——**🚨 交付前須確認其行尾約定，否則它與 `screeningQueueHash` 一樣是外部錨，
   且比外部錨更糟：它看起來可重算，實際不可攜。**

**✅ 反面確認**：本 run 證據鏈之九個自證雜湊皆為 `content_hash`（對已剖析之 JSON 計算），
**不受此影響**——這也是為何前一輪那 26 處比對能全數相符。

### 🚨 更正：本檔初版把 **8** 項列為不可及，其中 **5** 項其實在版控裡

執行室第 440 輪指出，**我自己就打得開**其中五項。**我已逐項自算覆核**：

| 佔位符 | 我實算所得 | 出處（受追蹤） |
|---|---|---|
| `W7_WALKS` | **2270**（六組皆同） | `ahig/analysis/results/synergy_replay.json` → `aggregate[*].walks` |
| `W7_RANDOM` | **0.0115** | 同上 → `['random@look100'].violationRate` |
| `W7_ADVERSARIAL` | **0.3652** | 同上 → `['adversarial@look100'].violationRate` |
| `W7_TRIPWIRE_CATCH` | **0.8893** | 同上 → `['adversarial@look100'].meanTailCatchOnViolation` |
| `COLLISION_N` | **40**（相異 `C-*` 編號） | `docs/w4b-design-inputs.md` |

**⚠️ 成因（要寫出來，因為它會再犯）**：我以**我以為它該有的檔名**去搜——
搜 `w7` 搜不到 `synergy_replay.json`，搜 `碰撞|collision` 搜不到 `w4b-design-inputs.md`
（而後者其實出現在我另一次 `git ls-files` 的輸出裡，**我看到了卻沒接上**）。
**🚨 搜不到就宣告不存在，正是檢查表第一條所禁的形狀**——
**「我沒看到」寫成「沒有」**，而本檔正是收攏這些規則的那一份。

**⚠️ 立為規則**：**凡標「不可及」，須先跑 `git ls-files` 全表確認，不得以檔名猜測代替。**

**⚠️ 併記一項執行室之提醒**：`C-1…C-40` **無重號無跳號，但檔內排列非遞增**，
**🚫 故不得以「順序遞增」查完備**（執行室自陳第一次即如此得到假陰性）。

### ⚠️ 另須分清：「凍結」是交付規則，不是「有雜湊背書」

上表之凍結值中，**真正落在某個雜湊原像內的是少數**（見下節之實測）。
**⚠️ 而「可自版控核對」與「有雜湊」又是第三件事**——
`W7_*` 與 `COLLISION_N` 我可自行打開重算，但那兩個檔並非證據鏈之雜湊產物。
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

## 四、交付前必須先解決的事項（🚨 二項未決、✅ 二項已結）

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
**✅ 更正值 5,115 之產生指令已於第 440 輪備妥**（`.scratch/n440_not_screened.py`）：
七個判讀目錄逐一計數、取聯集去重得 **10,310**，`15,425 − 10,310 = 5,115`。
**⚠️ 其輸入在私有根，協調者不可及**，故該數交付時仍標「執行室量測、協調者未獨立覆核」。

**🚨 並更正本檔前述之成因措辭**：我寫「六個判讀來源只計入四個」，
**而執行室逐目錄列出的是七個目錄名。**
**⚠️ 我不替它決定哪兩個算一個**——交付時以逐目錄之數為準，**不以「六」或「七」這個形容詞為準**。

**⚠️ 另一項須併記**：`5,357` **不是手打錯**。生產程式依其輸入算出
`15,425 − 7,431 − 2,637 = 5,357`；**錯的是餵進去的 `screenedCount`（未計入影子兩批），不是算式。**
**🚨 這個區別會改變讀者對流程的判斷**——算式錯代表程式有 bug，
輸入漏代表**組裝輸入時漏了來源**，後者正是檢查表第四條所講的那件事。

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

### （四）✅ `PAGES_BETWEEN` 已定案為 **20**——而它不再是主要論據

我原列兩種讀法（299→20 或 p294→15）並要求執行室裁決。
**執行室指出這不是二選一，檔內可自證**，**我已重算覆核**：

```
triggerCause.after      windowSize 201｜relevantFound 718
standardLaneSequence    windowSize 201｜relevantFound 718   ← 逐欄相同
pScore                  0.012405（after，記至 6 位）
                        0.012404888703091584（標準線，全精度）
                        ⚠️ round(全精度, 6) == 0.012405 → 兩者同值，只是記載精度不同
```

**🚨 故 `standardLaneSequence` 就是觸發當下之狀態**，其 `contiguousPagesJudged` = 299，
**299 − 279 = 20**。**p294 是被改判那筆紀錄坐落的頁**（其後 86 筆排除，故為序列最後一個命中），
**是「成因所在位置」，不是「觸發發生位置」。**

**⚠️ 一項對執行室措辭之更正**：它寫兩者「**完全相同**」。
`windowSize` 與 `relevantFound` 確實完全相同，**但 `pScore` 是四捨五入後的副本**——
**🚨 稽核者若用 `==` 比對浮點數會得到 False，而據此以為此論據不成立。**
**故交付時須寫「相同至記載精度」，不得寫「完全相同」。**

**🚨 且丙節應改用更硬的論據**（執行室之建議，我採納）：
兩次觸發之**成因型態不同**——第一次是判讀推進到 p279 而觸發；
第二次是一筆 `unclear → exclude` 之改判**把窗口由 115 併為 201**
（`triggerCause.kind = "reclassification"`）。
**⚠️ 「不是同一件事重測」用成因型態說，比用相隔 20 頁說更強，且不依賴頁數口徑之爭。**

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
- [ ] **抽查債以三欄呈現**（n+108 之三欄，值見丁節之佔位符），**並註明單位為抽查項目**。
      **🚫 此處刻意不重寫那三個數**——⚠️ 一份禁止沿用舊值的清單，自己不該內建一組舊值。
- [ ] **敘述式估計不得以單一數字呈現**（清冊 49308）。
- [ ] **第二節「不可及」三項**（`{{TITLE_ONLY_N}}`／`{{SHADOW_CONCORDANT}}`／`{{SHADOW_QUEUED}}`），已標示「執行室量測、協調者未獨立覆核」。
- [ ] **凡標「不可及」前，先跑 `git ls-files` 全表確認**，🚫 不得以檔名猜測代替（本檔曾誤標 5 項）。
- [ ] **第四節（一）（三）兩項未決**已處置（雜湊涵蓋範圍與兩次原像欄位清單皆已寫明）。
- [ ] **第四節（二）之勘誤已併呈**，且以**逐目錄之數**呈現，不寫「六個來源」這種形容詞。
- [ ] **丙節「兩次不是重測」改以成因型態論述**，頁距 20 僅作佐證。
- [ ] **全文逐條過 `docs/m1-wording-checklist.md`（十二條）。**
- [ ] **每一個層別筆數註明其取自哪一份產物**；⚠️ 散文摘要與產物不符時**一律以產物為準**
      （🚨 已連兩輪在同一層發生：`S5+S6` 之筆數，回報散文與 `n489`／`n490` 兩份產物皆不符）。
- [ ] **交付時不得引用未落盤之 IP 位址**，除非另附產生該值之指令（n+122）。
- [ ] **義務清冊逐條標註狀態**（`docs/m1-obligations.md`，⚠️ 該檔只保證不漏，不保證已辦）。
      **🚫 此處刻意不寫條數**——⚠️ 它每次重跑都變（曾寫死「42 條」而實際已達七十餘條）；
      條目數與相異義務數見丁節之 `{{OBLIGATION_ROWS}}`／`{{OBLIGATION_DISTINCT}}`。
