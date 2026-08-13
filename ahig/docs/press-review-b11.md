# AHIG B.11 碳水化合物／肝醣管理檢索策略 PRESS 2015 同行審查

審查日期：2026-08-13

本審查依 PRESS 2015 的六個面向，逐一比對 `search-contract.json`、四份查詢工件、`scope-contract.json` 與 `strata.json`。審查重點包括研究問題轉譯、布林結構、主題標目、自由文字、各平台語法、限制條件，以及契約中的來源配置、去重與召回評估。這是離線的檔案層級審查；依任務限制未呼叫任何外部 API，也未下載或查核全文。因此，平台語法可依實際查詢規則判讀，但 URL 編碼、伺服器實際解析結果與逐子句命中數仍須在下一次受控執行中保存。

整體判定為 **需重大修訂後重跑**。目前沒有發現會令 PubMed 或 Europe PMC 整條查詢失效的括號或欄位錯誤；主要問題是自由文字詞彙與 registry 搜尋範圍不足，以及 `knownItemSeedSet` 為空，尚不能證明達到 0.95 的召回門檻。

契約的去重規則本身合理：DOI／PMID／PMCID／registry ID／OpenAlex ID 的優先順序清楚，禁止只憑標題自動合併，模糊配對交由人工複核，且不把同一研究的多篇報告誤當成書目重複。建議在召回校準時同時報告去重前、去重後的 seed 命中，確認去重沒有誤刪 seed；去重不能補救檢索階段未召回的研究。

## 1. Translation of the research question — REVISE

### 理由

目前 PubMed 與 Europe PMC 都採用三個必要概念群：碳水化合物、運動、攝取／補充。這個骨架可以辨識大量「運動中攝取碳水」研究，也沒有把 comparator、outcome 或 RCT filter 設為必要條件，因此避免因摘要未報告安慰劑、劑量或研究設計而漏檢。OpenAlex 被正確定位為語意／引用圖補充來源；ClinicalTrials.gov 則用運動條件／關鍵字與介入名稱交集尋找試驗。

但目前轉譯不完整：

- `trained`、`highly trained`、`elite` 與 18–45 歲沒有進入查詢。這會降低 precision，但若在 screening 判定，並不直接傷害 recall；不應把訓練狀態或年齡設為新的必要 AND 群，因許多合格摘要不會報告 VO2max、FTP 或年齡範圍。
- comparator 沒有進入查詢是合理的。`placebo`、`water`、`no intervention` 或較低劑量常未出現在標題／摘要，把它們設為必要條件反而會漏檢。
- TT、TTE、外源性氧化、肌肉肝醣與 GI harms 沒有任何 outcome rescue 詞。Outcome 不宜獨立成一個必要 AND 群，但應與 ingestion 詞放在同一個替代群，否則只使用 `fed`、`consumed`、`administered` 或只在 outcome 用語中描述介入的研究可能漏失。
- 「during exercise」沒有明確編碼。把它設為必要片語會漏掉只寫 `exercise trial` 或在方法段才交代時點的論文，因此仍應 downstream screening；但可用補充查詢量測其增益。
- `scope-contract.json` 只接受 RCT parallel／crossover，但不套 RCT filter 是符合 frozen `searchLimits` 的高召回選擇。

### 可執行修正

保留現有兩個核心群，將第三群改成「攝取／給予詞 **OR** outcome rescue 詞」：

```text
(CHO concepts)
AND
(exercise/endurance concepts)
AND
(
  ingestion/administration concepts
  OR oxidation/glycogen/GI/performance rescue concepts
)
```

PubMed 可加入下列片段；不要再另加 comparator 或 trained-athlete 必要群：

```text
OR fed[tiab]
OR consum*[tiab]
OR administ*[tiab]
OR provision[tiab]
OR oxid*[tiab]
OR glycogen*[tiab]
OR gastrointestinal[tiab]
OR gastro-intestinal[tiab]
OR "GI symptom"[tiab]
OR "GI symptoms"[tiab]
OR "time trial"[tiab]
OR "time trials"[tiab]
OR "time to exhaustion"[tiab]
OR TTE[tiab]
```

另跑一條補充時點查詢並與主查詢取聯集，可評估「運動中」片語的增益，但不應取代主查詢：

```text
AND ("during exercise"[tiab] OR "during cycling"[tiab] OR "during running"[tiab] OR "exercise feeding"[tiab])
```

## 2. Boolean and proximity operators — PASS

### 理由

- PubMed 與 Europe PMC 的三個概念群都有完整外括號；群內以 OR、群間以 AND，優先順序正確。
- 查詢沒有使用 NOT，因此不存在以 NOT 誤刪 crossover、動物／人體混合摘要、預印本或非典型研究設計的風險。
- ClinicalTrials.gov 的最外層為 `(ConditionSearch OR Keyword) AND InterventionName`，巢狀邏輯明確。
- 四個平台查詢均未使用 proximity operator；PubMed 原生檢索並沒有可直接平移自 Ovid 的鄰近運算子，因此不使用 proximity 並非錯誤。Europe PMC 雖可做較複雜的 Lucene 查詢，但本題不必以鄰近限制犧牲 recall。
- OpenAlex 的 `search` 值不是布林式；空白分隔的詞由相關性搜尋處理，不能解讀為「所有詞均須出現」。工件已把它定位為 discovery supplement，因此這不是括號錯誤，但其命中數不得當成結構化布林查詢的結果。

### 維持與微調建議

維持現有群組結構與「不使用 NOT」的政策。為使 ClinicalTrials.gov 多字詞意圖更清楚，可寫成：

```text
AREA[ConditionSearch](Exercise OR Endurance OR "Athletic Performance")
```

這是可讀性與解析穩定性的微調，不代表目前外層布林邏輯錯誤。

## 3. Subject headings — PASS

### 理由

PubMed 實際上有使用正確的 MeSH 標目：`"Carbohydrates"[Mesh]`、`"Dietary Carbohydrates"[Mesh]`、`"Exercise"[Mesh]`、`"Sports"[Mesh]`、`"Athletic Performance"[Mesh]`。`[Mesh]` 與 `[mh]` 都是 PubMed 接受的 MeSH 欄位標籤。它們與 `[tiab]` 自由文字以 OR 並列，未形成 MeSH-only filter。

因此，`searchLimits` 所稱「不用 MeSH/publication-type/species filters」應理解為「不以已完成 MeSH 索引、publication type 或 human/species 標籤作為納入必要條件」，而不是完全不用 MeSH 詞。現在的 MeSH＋free-text 並行方法與該理由一致：

- recall 方面，可保留尚未完成 MEDLINE 索引的最新紀錄、publisher supplied 紀錄、預印本與非典型運動科學設計。
- precision 方面，代價是大量一般運動、營養、代謝與非人體研究會進入候選池；Europe PMC 的 10,080 筆正反映此代價。
- free-text 必須承擔更多責任，尤其是縮寫、產品型態、拼寫變異、未索引 outcome 與較新的術語；目前這一側尚未足夠，故第 4 面向判為 REVISE。

Emtree 不適用，因 frozen sources 沒有 Embase。若日後新增 Embase，必須另做 Emtree translation，不能直接沿用 PubMed `[Mesh]`。

### 可選的補強片段

下列 MeSH 可作為 outcome rescue 的補充，但不得取代自由文字，也不得成為新的必要 AND 群：

```text
OR "Glycogen"[Mesh]
OR "Dietary Supplements"[Mesh]
```

## 4. Text word searching — REVISE

### 理由

現有 `carbohydrat*` 可涵蓋 `carbohydrate`／`carbohydrates`，`exercis*`、`cyclist*`、`runner*` 等截斷也合乎平台用途；單複數片語另列在目前寫法下沒有錯。然而仍有會影響 seed recall 的明顯缺口：

- 缺少領域最常見縮寫 `CHO`。
- 缺少 `dextrose`、`glucose polymer`、`carbohydrate-electrolyte`、`sports drink`、`isomaltulose` 等介入描述；`maltodextrin` 也宜改為 `maltodextrin*`。
- `feed*` 不會命中不規則過去式 `fed`；`intake` 未截斷，且缺 `consum*`、`administ*`、`provision`。
- `triathlon` 不涵蓋 `triathlete(s)`；宜改成 `triathl*`。可補 `swim*`、`rowing`、`rower*`，但不宜用過短的 `row*` 或 `ski*`，以免引入大量非運動詞。
- 缺少 `oxid*`，因此沒有同時涵蓋 `oxidation`、`oxidized`／`oxidised`、`oxidizing`／`oxidising`。缺少 `glycogen*`，加入後亦可涵蓋罕見的 `glycogene` 拼法。
- GI harms 是 critical outcome，但沒有 `gastrointestinal`、`gastro-intestinal`、`GI symptom(s)`、`nausea`、`cramp(s)`、`bloating`、`diarrh*`。
- 缺少 `time trial(s)`、`time to exhaustion`、`TTE`。不建議加入單獨的 `TT`，因其歧義過高。

### 可執行修正

PubMed 的 CHO 群可加入：

```text
OR CHO[tiab]
OR dextrose[tiab]
OR (glucose[tiab] AND polymer*[tiab])
OR "carbohydrate-electrolyte"[tiab]
OR "carbohydrate electrolyte"[tiab]
OR "sports drink"[tiab]
OR "sports drinks"[tiab]
OR isomaltulose[tiab]
OR maltodextrin*[tiab]
```

運動群可將 `triathlon[tiab]` 改為並補入：

```text
OR triathl*[tiab]
OR swim*[tiab]
OR rowing[tiab]
OR rower*[tiab]
```

第三群除第 1 節所列 rescue 詞外，再加入 GI 症狀詞：

```text
OR nausea[tiab]
OR cramp*[tiab]
OR bloat*[tiab]
OR diarrh*[tiab]
```

Europe PMC 應作等價翻譯，而不是直接貼上 PubMed 欄位標籤，例如：

```text
OR TITLE_ABS:CHO
OR TITLE_ABS:dextrose
OR (TITLE_ABS:glucose AND TITLE_ABS:polymer*)
OR TITLE_ABS:"carbohydrate-electrolyte"
OR TITLE_ABS:"sports drink"
OR TITLE_ABS:"sports drinks"
OR TITLE_ABS:isomaltulose
OR TITLE_ABS:maltodextrin*
OR TITLE_ABS:fed
OR TITLE_ABS:consum*
OR TITLE_ABS:administ*
OR TITLE_ABS:oxid*
OR TITLE_ABS:glycogen*
OR TITLE_ABS:gastrointestinal
OR TITLE_ABS:"gastro-intestinal"
OR TITLE_ABS:"time trial"
OR TITLE_ABS:"time trials"
OR TITLE_ABS:"time to exhaustion"
```

OpenAlex 不宜把更多詞全部塞入同一個 `search` 字串；應以多條概念清楚的 discovery searches 取聯集，例如：

```text
search="carbohydrate ingestion endurance exercise performance"
search="glucose fructose exogenous oxidation exercise"
search="carbohydrate exercise muscle glycogen"
search="carbohydrate exercise gastrointestinal symptoms"
search="CHO cycling time trial"
```

## 5. Spelling, syntax, line numbers — PASS

### 理由

在所審查的工件中，沒有發現可直接判定會被平台靜默忽略的拼字或語法片段：

- **PubMed：** `[tiab]` 與 `[Mesh]` 均為有效欄位；每一個自由文字詞都有自己的欄位標籤；截斷符放在詞尾；括號平衡。這裡沒有 `[mh]` 才有效、`[Mesh]` 無效的問題。
- **Europe PMC：** `TITLE_ABS:term` 與 `TITLE_ABS:"phrase"` 為正確的欄位作用域；布林運算子大寫、括號平衡，詞尾 `*` 的使用位置合理。
- **OpenAlex：** `search`、`per_page`、`cursor`、`select` 都是 Works API 的參數；`select` 內列的是頂層 work fields。此檔沒有 `filter` 參數，所以沒有 OpenAlex filter expression 可審；風險是把 relevance search 誤當 Boolean AND，而不是欄位被忽略。
- **ClinicalTrials.gov：** API v2 的 `query.term` 可承載 expert-search expression；`AREA[ConditionSearch]`、`AREA[Keyword]`、`AREA[InterventionName]` 的寫法與 `format`、`pageSize`、`countTotal` 參數形式可成立。現有 212 筆結果至少證明整體查詢被接受，但不能單憑總數證明每個子句的 recall。

最危險的靜默問題仍可能發生在「工件到 HTTP request」的傳輸層，例如括號、雙引號或方括號被重複 URL-encode，或 executor 漏送某個 JSON parameter；這無法由查詢文字本身證明。下一次執行必須保存最終 request URL／parameter map、伺服器回應與下列逐子句 canary counts：

```text
ClinicalTrials.gov:
1. AREA[InterventionName](Carbohydrate)
2. AREA[ConditionSearch](Exercise)
3. AREA[Keyword](Athlete)
4. (1 OR expanded intervention terms) AND (2 OR 3)
```

若任一單一子句為 0、報錯，或加入子句後出現不合邏輯的計數變化，應先停止候選池晉升，確認實際送出的 URL 與 parser 行為。所有文字檔也應維持 UTF-8；本次終端初讀曾出現顯示層亂碼，但以明確 UTF-8 重讀後 JSON 內容正常，未見檔案本體損壞。

## 6. Limits and filters — PASS

### 理由

`searchLimits` 明確記錄：不限制語言與日期、不套 study-design filter、納入所有出版狀態（含預印本）、human species 於 downstream screening 判定。這些選擇與 objective 要找未發表、預印本、撤稿及非典型運動科學試驗一致。

- 不設年份下限可保留 1970–1990 年代的經典運動中補充碳水試驗。
- 不設語言限制可降低 language bias。
- 不設 publication type／RCT filter 可保留未正確標記的 crossover trial 與 publisher supplied 紀錄。
- 不設 species filter 會增加動物與基礎代謝研究的 screening 工作量，但避免漏掉尚未索引為 humans 的新紀錄。
- ClinicalTrials.gov 沒有 recruitment-status filter，符合尋找 completed、terminated、withdrawn 與 unknown-status 試驗的目的。
- Europe PMC 沒有 `HAS_FT`／`OPEN_ACCESS` filter；取得全文的便利性沒有被錯當成 eligibility。

上述限制均有正當理由並記錄在案。仍須依 `executionProtocol` 保存各來源實際搜尋日期與完整 request；這是執行證據，不是新增查詢限制。

## 實測落差：Europe PMC 10,080 筆與 ClinicalTrials.gov 212 筆

**212 筆不能只憑數量判定「過低」，但對目前 objective 而言，低到足以觸發 registry recall 診斷；它同時反映來源本來較少與查詢式可修正的漏檢。**

Europe PMC 的 10,080 筆屬可預期結果。其查詢只要求 title/abstract 同時出現廣義碳水、運動與攝取／補充詞，沒有人體、成年、trained、RCT、時間點或 publication status 限制；Europe PMC 又包含 PubMed 重疊、預印本與其他來源。`feed*`、`supplement*`、`drink*` 等詞也會帶入大量非介入或非耐力研究。這是高 recall 策略的 precision 代價，不是自動代表語法失控。

ClinicalTrials.gov 的母體原本就會小很多：運動營養試驗規模小，許多經典研究早於普遍 trial registration，單中心 crossover studies 也常未註冊；同一研究在書目庫可有多篇報告，但 registry 通常只有一個 NCT record。因此，不能期待其數量接近書目庫。

不過，現有 query 另有明確的可修正收窄：

- 運動概念只在 `ConditionSearch` 或 `Keyword` 找。許多健康志願者試驗會把 condition 填成 `Healthy`，而把 cycling、running、endurance 寫在 official title、brief summary、outcomes 或 eligibility。
- 碳水只在 `InterventionName` 找；registry 可能填 `sports drink`、`energy gel`、`glucose polymer`、`CHO beverage`、配方名或商品名。
- 缺 `CHO`、`dextrose`、`carbohydrate-electrolyte`、`sports drink`、`gel`、`isomaltulose`，也沒有 performance／oxidation／glycogen／GI rescue 詞。

建議保留原查詢作為一個窄而精確的 pass，再新增至少一個使用 API v2 專用參數的廣搜尋，最後依 NCT ID 去重：

```json
{
  "query.intr": "(Carbohydrate OR Glucose OR Fructose OR Sucrose OR Maltodextrin OR Dextrose OR CHO OR \"Sports Drink\" OR \"Carbohydrate-Electrolyte\" OR Gel)",
  "query.term": "(Exercise OR Endurance OR Athlete OR Cyclist OR Runner OR Triathlete OR \"Time Trial\" OR \"Time to Exhaustion\" OR Glycogen OR \"Carbohydrate Oxidation\")"
}
```

再做三項 count ablation：只跑 expanded `query.intr`、只跑 expanded `query.term`、兩者 AND。比較命中增量並人工抽查新增紀錄，才能區分「來源本來少」與「欄位過窄」。最終判斷依已驗證 registry known items 的命中率，不依總筆數。下節的論文 seeds 主要測試書目來源；對沒有 NCT ID、尤其早於註冊常規的舊論文，不能把 ClinicalTrials.gov 未命中算成 registry failure。registry 應另建一組已確認 NCT ID 的較新試驗 seeds；本次離線審查不猜測 NCT ID。

## Known-item seed recall

`knownItemSeedSet` 目前為空，故 `seedRecallCurrent` 無分母、無分子，不能宣稱達到 `minAcceptableSeedRecall: 0.95`。以下推薦 13 篇跨年代、表現、TTE、外源性氧化、肌肉肝醣與 GI tolerance 的高把握種子文獻。依任務限制未連線查核；列入者皆為本審查者對題名與 DOI 有高把握的真實論文。正式寫回下一版契約前，仍應以 PubMed／DOI resolver 作一次機器核對；不要把未核對的轉錄錯誤凍結成 gold set。

| # | 種子文獻與識別碼 | 為何合格檢索式應命中 |
|---:|---|---|
| 1 | Coyle EF et al. *Carbohydrate feeding during prolonged strenuous exercise can delay fatigue.* DOI: `10.1152/jappl.1983.55.1.230` | 成年耐力運動、運動中 carbohydrate feeding、延緩 fatigue／TTE；應由 `carbohydrate`＋`feeding`＋`exercise` 命中。 |
| 2 | Coyle EF et al. *Muscle glycogen utilization during prolonged strenuous exercise when fed carbohydrate.* DOI: `10.1152/jappl.1986.61.1.165` | 直接覆蓋運動中外源性碳水與 muscle glycogen；也專門測試目前缺少不規則詞 `fed` 的風險。 |
| 3 | Coggan AR, Coyle EF. *Reversal of fatigue during prolonged exercise by carbohydrate infusion or ingestion.* DOI: `10.1152/jappl.1987.63.6.2388` | 含 carbohydrate ingestion、prolonged exercise 與 fatigue reversal／TTE；具口服 ingestion 分支，合格策略不應因題名同時提到 infusion 而漏掉。 |
| 4 | Below PR et al. *Fluid and carbohydrate ingestion independently improve performance during 1 h of intense exercise.* DOI: `10.1249/00005768-199502000-00009` | 碳水攝取、運動表現與對照設計均直接呈現在題名；是 performance stratum 的明確正控制。 |
| 5 | Tsintzas K et al. *Carbohydrate ingestion and glycogen utilization in different muscle fibre types in man.* DOI: `10.1113/jphysiol.1995.sp021047` | 覆蓋 ingestion、人體運動代謝與肌纖維 glycogen utilization；測試 `glycogen*` outcome rescue。 |
| 6 | Jeukendrup AE et al. *Carbohydrate-electrolyte feedings improve 1 h time trial cycling performance.* DOI: `10.1055/s-2007-972607` | trained cycling、carbohydrate-electrolyte feeding 與 1 h time trial；測試連字詞、`feed*` 與 TT 詞。 |
| 7 | Jentjens RLPG et al. *Oxidation of combined ingestion of glucose and fructose during exercise.* DOI: `10.1152/japplphysiol.00974.2003` | glucose＋fructose、多重可運輸碳水、運動中攝取與 exogenous oxidation 的核心研究。 |
| 8 | Wallis GA et al. *Oxidation of combined ingestion of maltodextrins and fructose during exercise.* DOI: `10.1249/01.MSS.0000155399.23345.82` | 覆蓋 maltodextrin/fructose、combined ingestion 與 oxidation；測試 `maltodextrin*` 複數變體。 |
| 9 | Stellingwerff T et al. *Carbohydrate supplementation during prolonged cycling exercise spares muscle glycogen but does not affect intramyocellular lipid use.* DOI: `10.1007/s00424-007-0236-0` | 直接覆蓋 cycling、during-exercise supplementation 與 muscle glycogen sparing，是 S7 glycogen 的關鍵 seed。 |
| 10 | Currell K, Jeukendrup AE. *Superior endurance performance with ingestion of multiple transportable carbohydrates.* DOI: `10.1249/mss.0b013e31815adf19` | 同時覆蓋 multiple transportable carbohydrates、ingestion 與 endurance performance，應由片語與一般 CHO 詞兩條路徑命中。 |
| 11 | Pfeiffer B et al. *The effect of carbohydrate gels on gastrointestinal tolerance during a 16-km run.* DOI: `10.1123/ijsnem.19.5.485` | 直接覆蓋 carbohydrate gel、耐力跑與 gastrointestinal tolerance，是 critical GI harms stratum 的必要正控制。 |
| 12 | Smith JW et al. *Fuel selection and cycling endurance performance with ingestion of [13C]glucose: evidence for a carbohydrate dose response.* DOI: `10.1152/japplphysiol.91394.2008` | 覆蓋 13C tracer、glucose ingestion、cycling endurance、oxidation／fuel selection 與 dose response。 |
| 13 | Smith JW et al. *Carbohydrate dose and cycling time-trial performance.* DOI: `10.1249/MSS.0b013e31827205d1` | 直接覆蓋 dose comparison、cycling 與 time-trial performance；可測試只在摘要交代攝取動詞時的召回。 |

這 13 篇不可只用 DOI 逐筆反查來「證明」召回；正確方法是先執行完整查詢，再以標準化 DOI／PMID 與結果集交集。應分別報告 PubMed、Europe PMC、OpenAlex 與書目來源聯集的命中；OpenAlex 只能作補充，不得掩蓋核心書目查詢的漏失。以 13 篇為分母時，漏 1 篇即為 12/13 = 0.923，低於 0.95，所以必須 13/13 才能過門檻。另應在獨立專家或已納入系統性回顧中補充並驗證更多 GI harms seeds；本次不為湊數而列入 DOI 不確定的論文。

## 總結：目前是否足以支撐 Approved Claim？

**否。** 目前策略可以執行探索與校準搜尋，但不足以支撐 Approved Claim，理由如下：

1. 研究問題轉譯與自由文字均為 **REVISE**；`CHO`、`fed`、oxidation、glycogen、GI harms 與若干介入／運動詞仍有可預見的漏檢。
2. ClinicalTrials.gov 的 212 筆有來源本身較少的合理成分，但欄位限制過窄尚未經 expanded-query、count ablation 與 registry seeds 排除 under-retrieval。
3. `knownItemSeedSet` 為空，0.95 門檻尚未實測；以本文 13 篇為初始書目 seeds 時須 13/13 命中。
4. frozen contract 的 `pressReview.status` 仍為 `notPRESSReviewed`，且其 note 要求 human-information-specialist peer review。本文可作完整的結構化同行審查報告，但若治理規則按字面要求真人資訊專家簽核，仍須另行取得該簽核；不應只靠產生此檔就改旗標。

解除阻擋的最低步驟是：在不覆寫 frozen v1 的前提下建立修訂版查詢／契約、納入上述詞彙與 registry 補充 pass、保存各平台最終 request 與逐子句計數、以已核對 identifiers 的 seed set 實測來源別及聯集召回、確認去重前後不遺失 seeds，並完成契約要求的同行審查簽核。完成前維持 Approved Claim block。
