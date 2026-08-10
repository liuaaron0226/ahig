# 好棒Bump《我花了18個月從交易機構洗出1000萬》影片分析

**分析日期**：2026-08-10
**標的影片**：<https://www.youtube.com/watch?v=rR8EJQfibAk>（好棒Bump，2026-08-09 上傳，19:37，分析當下約 22 萬觀看）
**方法**：Whisper 逐字稿（720 段）＋ 28 幀關鍵畫面 OCR ＋ 平台官網一手抓取 ＋ 監理公告 ＋ 同儕審查文獻檢索（19 個檢索／查核 agent，含引用真實性反駁式查核）

> **文獻使用原則**：本文所有理論命題僅引用通過「書目存在性 ＋ 核心發現正確性」雙重查核的期刊論文。新聞、論壇、部落格僅作為找資料的方向線索，不承載任何理論主張。未通過查核者列於 §7。

---

## 1. 一手證據盤點（我實際看到的東西）

### 1.1 平台身分已確認

影片 07:07 的違規通知信畫面中出現條款連結 `https://www.mycryptofund.com/#/faq/1`。因此影片所稱「MCF」＝ **MyCryptoFund（mycryptofund.com）**，一家加密貨幣 prop firm（自營交易考核機構），營運主體查得為 YSF Tech Limited（英屬維京群島），準據法香港、爭議走 HKIAC 仲裁。

**須與另一家同簡稱公司 My Crypto Funding（mycryptofunding.org）嚴格區分**——網路上多數「MCF 拒付」投訴指向後者，本次查證期間後者 DNS 已無法解析。

### 1.2 平台官網現況（2026-08-10 直接抓取）

| 項目 | 內容 |
|---|---|
| 現行方案 | 1,000,000 USDT（報名費 4,980）／5,000,000 USDT（報名費 24,900）。$200K／$1,080 該檔已從價目表移除，但 FAQ 內文與 meta 描述仍寫 $200,000，站內新舊文案並存互相矛盾 |
| 第一階段 | 累積獲利目標 **60%**、最短 **6 個月**、首次交易起 12 個月內完成 |
| 風控 | 單筆虧損 ≤1%（觸發即失格）、單筆計入獲利上限 3%、每 30 天至少 +1%、日虧 5%、總回撤 10% |
| 明文禁止 | **No Copy Trading or Hedging**、**No VPN / Region Bypass** |
| 帳戶限制 | 「each user may hold only one main Funded Account and one Challenge Account at any time. Operating multiple accounts or attempting to circumvent program restrictions is strictly prohibited.」 |
| 出金 | 每月 1–5 日（UTC）申請、月底前須全部平倉、**當月淨利須達 10%**、每個 KYC 用戶僅能綁定一個 TRC20 地址且不得共用 |
| 分潤 | 80% |
| 站方自報統計 | Active Challengers 8,793／Challengers to Date 11,466／Funded Traders 1,172／**Paid Out to Date $2,829,281** |
| Official Partners | Unbrella Fund、Cybotrade、Balaena Quant、TheTradveller——**四家皆非交易所** |

### 1.3 監理狀態

中華民國虛擬通貨商業同業公會轉載金管會證期局 **2024-10-14** 公告，將境外虛擬資產平台「Mycryptfund（MCF）」列為未依公司法登記、未完成洗錢防制法令遵循聲明之業者，籲請民眾拒絕往來、避免匯款。

> ⚠️ 精確性保留：公告拼法為 `Mycryptfund`（少一個 o），所載網址 `Mycryptfund.com` 本次無法解析。身分綁定為高度可能但非鐵證。時序上，該公告在 Bump 首支 MCF 影片（2024-09-22）後約三週。

### 1.4 影片內畫面的關鍵佐證

- **00:55 的「數據」是 AI 對話截圖**，不是原始研究。所幸其核心數字可回溯：FPFX Technologies 提供給 Finance Magnates 的 10 家公司／10 萬名交易者／30 萬帳號資料，通過率 14%、其中 45% 曾出金 → 全體 7% 曾出金。影片畫面上的「5–14% 通過、約 7% 出金」與此吻合。
- **02:10** MCF 官網舊價目表：5,000/10,000/25,000/50,000/100,000/200,000 USDT 對應 55/105/230/345/540/1080 USDT，並註明「挑戰完成後全額退費」。
- **02:52** 他的試算表（見 §3）。
- **03:33–06:10** 九筆 Bybit ETHUSDT 平倉紀錄，日期落在 2025-01-09 至 2025-02-03，入場／出場價位與該期間 ETH 實際走勢（約 3,330 跌至 2,714）相符。
- **07:07** 違規信全文可讀，含考試 ID、逐筆訂單、違規獲利金額 4,992.79 USDT。
- **09:47** 2025 年 4 月 25 日規則調整信，「每個階段至少三個完整持倉生命週期、每週期回報率不得低於初始資本 1%」文字與他的口述一致。
- **16:02–16:12** 牆上約 200 餘張 MCF「OVERALL REWARDS」出金證明，可讀金額 $8,118.3／$8,439／$8,552／$8,836／$16,047.6／$24,045.6。
- **17:00** 2026-03-01 生效的新規公告，與官網現行 FAQ 逐字一致。

---

## 2. 真實性判定（分層）

### 2.1 可獨立證實為真

| 主張 | 證據 |
|---|---|
| MCF 這家機構存在、規則與影片描述一致 | 官網一手抓取；2026-03 新規逐字可對 |
| prop firm 帳戶是模擬帳戶，客戶的單不進市場 | FTMO 服務條款自陳「All accounts we provide to our clients are demo accounts with fictitious funds」、FAQ「clients therefore never actually perform any trades on live markets」；加拿大 OSC 對 My Forex Funds 認定「virtually no real trading taking place」 |
| 通過率 5–14% 的量級 | FPFX 30 萬帳號資料 14%；Topstep 法定揭露 2025 年 Combine 完成率 16.8%；ATFunded 自報約 6% |
| 產業收入以報名費為主 | 比利時 FSMA（2024-03-07）稱其為「shadow investment game」；義大利 CONSOB（2024-07-08）稱其為線上交易電玩，並指測驗難度被設計成促使重考 |
| 他的試算表算術完全自洽 | 見 §3，逐格重算全部吻合 |
| 影片描述的手法是平台明文禁止的違約行為 | 官網首頁「No Copy Trading or Hedging」、一人一帳戶條款；MCF T&C 第 5.2 條列舉跨帳戶反向部位、代他人交易分潤、規避地域限制為 Prohibited Conduct。動區動趨 2024-09-24 也記載當時規則已禁止對沖 |

### 2.2 方向對但數字誇大

**「最終出金持續獲利的人不到 1%」**——所有可查實測都高於 1%：FPFX 為 7% 曾出金；體質最差的 The Funded Trader 執行長自承通過 5–10%、其中 20% 出金（全體約 1–2%）；Topstep 揭露 33.3% 的 funded 參與者收到過出金。

真正低於 1% 的是另一個指標：Topstep 揭露 2025 年僅 **0.71%** 的 Express Funded 參與者被升級到真實資金帳戶。方向正確，但引用的數字對不上任何可查來源。

另外，「持續獲利」（多次出金、長期淨正報酬）目前**沒有任何公開資料集在衡量**，所有統計最多只到「是否曾經拿到過一次出金」。

### 2.3 查無證據

| 主張 | 狀態 |
|---|---|
| 「世界前三大的交易所在後面服事」 | MCF 官網歷年文案只說「利用某家主要中心化交易所的流動性」，從未具名；59,533 字 T&C 中 exchange 與 liquidity 出現 0 次；現行四家 Official Partners 皆非交易所。**查無公開證據** |
| 所有金額主張 | 三種情況淨賺 1／9／18 萬台幣、一週賠 180 萬、單帳號虧 14,800 美元、500 萬三個月變 1,100 多萬、月化 40%、524 天——**全部僅有單方陳述，無任何第三方紀錄可交叉驗證** |
| 2025/4 與 2025/7 兩次規則變更的確切生效日 | 規則文字確實存在於 MCF 舊規則頁，但站台為 SPA、Wayback 無乾淨歷史快照，日期無法確認。只有 2026/3 那次有官方公告字串與生效日 |

### 2.4 畫面證據與口述的落差（需注意）

**這一項是我在逐幀 OCR 時才看到的，值得單獨列出。**

- **07:07 的違規信**實際寫的是：扣除違規獲利 4,992.79 USDT、資金水位回到 100,007.21 USDT、**「為此我們將再提供您一次第二階段的補考機會」**，並要求他重新申請一個 100,000 USDT／3 倍槓桿的模擬帳戶。口述則是「他不承認我是有證照的」「他要沒收我證照」「7,800 美金打水漂」。兩者嚴重程度不同。
- **12:12 的拒絕出金信**（畫面部分被裁切）可讀出「本次 4 月〔的出金申請〕予以拒絕」，但後段接著寫「僅針對此次申請，未來若〔以與 KYC〕資訊一致的錢包地址進行〔出金，不受〕影響，系統會正常處理」。口述則是「超級多帳號全部被拒絕」「拿水漂」。

他確實展示了多封信，我看到的只是其中兩封的可讀部分，因此這不構成「造假」的指控。但**畫面上可讀的文字，比口白所描述的溫和**，這是閱聽時該自己按暫停確認的地方。

### 2.5 一個量級上的內部張力

MCF 官網自報「Paid Out to Date $2,829,281」。影片牆上約 200 餘張出金證明，畫面可讀者介於 $8,118 至 $24,045，取保守平均 $10,000 估算即 **約 200 萬美元，佔該平台史上總出金的七成以上**。

三種可能：(a) 官網計數器只涵蓋現行 v2.0.0 方案、未含 2024–2025；(b) 影片誇大；(c) 「1000 萬」大部分其實來自 Bybit 側而非 MCF 出金——若是 (c)，標題的「從交易機構洗出」就不精確。§3 的推導顯示 (c) 極可能為真。

---

## 3. 數學核心：這不是套利，是一個買權加上交易對手違約風險

### 3.1 他的試算表（02:52 逐格重算）

| 階段 | MCF 名目 | 價格變動 | MCF 損益 | Bybit 名目 | Bybit 損益 | 對沖比 |
|---|---:|---:|---:|---:|---:|---:|
| 第一關（考試） | 595,000 | +3.50% | +20,379 | 67,295 | −2,398 | **11.3%** |
| | | −1.55% | −9,877 | | +1,000 | |
| 第二關（考試） | 595,000 | +1.82% | +10,383 | 228,802 | −4,311 | **38.5%** |
| | | −1.55% | −9,877 | | +3,400 | |
| 第三關（證照） | 198,000 | +5.30% | +10,346 | 162,584 | −8,721 | **82.1%** |
| | | −4.80% | −9,722 | | +7,700 | |
| 第四關（證照） | 198,000 | +5.30% | +10,346 | 147,804 | −7,928 | 74.6% |
| | | −4.80% | −9,722 | | +7,000 | |

逐格驗算全部吻合（例：595,000 × 3.50% = 20,825 − 446 手續費 = 20,379；162,584 × 4.80% = 7,804 − 104 = 7,700）。**這份表格是真的算過的，不是拍腦袋。**

### 3.2 關鍵發現：這不是 1:1 對沖

考試階段的對沖比只有 11.3% 與 38.5%。**如果目的是「鎖住」，比例應該接近 1；如果目的是「用假錢買一個真錢的選擇權」，比例就該長成這樣。**

- 考試階段 MCF 的損益是**模擬資金**，虧掉不是真的損失，只是失去帳戶。所以正確的對沖比不是 1，而是「讓 MCF 爆倉時 Bybit 的獲利剛好覆蓋報名費」——67,295 × 1.55% ≈ 1,043，扣手續費後 1,000，對上 1,080 報名費，誤差 80 美元。**這個 11.3% 是反推出來的，不是隨便抓的。**
- 證照階段 MCF 損益要真的分 80% 給他，所以正確對沖比是 0.8——實測 82.1%。**這是一個在真實貨幣意義上接近 delta 中性的部位。**

### 3.3 證照階段的期望值分解

令 MCF 名目 198,000、分潤 φ=0.8、Bybit 名目 162,584（實質曝險 158,400 vs 162,584，比值 1.026）。

**若 MCF 履約**：
- 價格上漲 5.30%：MCF 名目 +10,346，他實得 80% = +8,277；Bybit −8,721。**淨 −444。**
- 價格下跌 4.80%：MCF −9,722（模擬資金，帳戶死亡，無真實損失）；Bybit +7,700。**淨 +7,700。**

EV = p·(−444) + (1−p)·(+7,700)，對任何 p<1 皆為正。**這是一個真實存在的數學優勢，來自「下檔被截斷在假錢、上檔用真錢兌現」的不對稱性。**

**若 MCF 不履約**（援引 No Hedging 條款拒付）：
- 上漲情境變成 −8,721 而非 −444。
- EV = p·(−8,721) + (1−p)·(+7,700)，**當 p > 46.9% 時轉為負值。**

**整個策略的期望值符號，完全取決於一個沒有任何公開統計的變數：平台履約的機率。而他的試算表把這一項設為 1。**

### 3.4 三種情況的現金流（計算機畫面逐格驗證）

| | 現金流 | 淨額 (USD) | ×32 (NTD) |
|---|---|---:|---:|
| 情況一 | −1,080 +999.36 +479.38 | **+398.74** | 12,760 |
| 情況二 | −1,080 −2,443.99 +3,398.34 +2,946.88 | **+2,821.23** | 90,279 |
| 情況三 | −1,080 −2,369.80 −4,351.89 +7,403.59 +6,253.40 | **+5,855.30** | 187,370 |

**三種情況裡，MCF 付給他的錢都是 0 元。**

九筆交易全部是 Bybit 的平倉損益；MCF 那一側每一次都是以爆倉收場（−9,965／−9,369／−9,830／−9,653／−9,845／−9,642），或是通過關卡但不產生現金。**他示範的「怎麼樣都是賺」，賺的全部是 Bybit 的真實部位損益；MCF 帳戶的角色是提供一個免費的反向選擇權，讓那個方向性部位可以被合理化。**

這在經濟意義上是正確的——優勢確實由 MCF 的模擬資金創造——但在描述上，「從交易機構洗出 1000 萬」與畫面證據不完全相符：錢是從加密永續合約市場出來的，MCF 提供的是**免費的下檔保護**。

### 3.5 真正的分母不是報名費

證照階段 Bybit 名目 162,584、20 倍全倉 → 起始保證金約 8,129，但該部位必須吸收最大 −8,721 的虧損。**也就是說單一帳戶的真實資金占用約 1.5–2 萬美元，而不是 1,080 美元的報名費。**

以情況三為例：獲利 5,855 美元，交易日期跨 2025-01-19 至 2025-02-03（15 天）。若分母取 ~17,000 美元的必要權益，報酬率約 34%／15 天。這個數字比他宣稱的「月化 40%」還高——正說明他展示的是**選擇過的路徑，不是分布**。

「投入 500 萬台幣（約 15.6 萬美元）」對應 50 個帳戶，平均每帳戶約 3,100 美元，遠低於單帳戶的必要權益。合理解讀是帳戶並非同時滿倉、且夥伴自帶資金；但這也意味著「月化 40%」這個數字的分母定義從未被說明。

---

## 4. 學術理論框架

以下九條命題全部掛在通過查核的期刊論文上。完整書目見 §8。

### 命題 1｜母體基準率：若獲利來自「交易技能」，統計上不可能

- 台灣證交所全市場資料：散戶總合每年因交易損失 3.8 個百分點，相當於台灣 GDP 的 2.2%（Barber, Lee, Liu & Odean, 2009, *RFS*）
- 當沖母體中**不到 1%** 的人能事前辨識、且扣費後仍有正異常報酬；前 500 名事後每日扣費後 +37.9 bps，墊底組 −28.9 bps（Barber et al., 2014, *JFM*）
- 每日 97% 的當沖者可預期虧損；15 年間總合扣費後績效逐年為負；虧損者續留機率 95.3%、獲利者 96.4%，幾無差別（Barber et al., 2020, *RAPS*）
- 台灣期貨當沖 3,470 人：扣費前即虧損 26,700 元、扣費後 61,500 元（Kuo & Lin, 2013, *JBF*）
- 巴西股指期貨持續 300 天以上者 97% 賠錢，僅 0.4% 賺得比銀行櫃員多（Chague, De-Losso & Giovannetti, 工作論文）
- 忽略退出者會把「交易可學習」高估 2–4 倍（Seru, Shumway & Stoffman, 2010, *RFS*）

→ 影片的「只有 1% 會穩定獲利」在**量級上有紮實實證支持**（雖然操作型定義與他的說法不同）。同一組文獻也說明：他的獲利不可能來自交易技能，只能來自規則結構。

### 命題 2｜報酬結構：這是一個買權，不是一個帳戶

支付函數為 $\Pi = \phi\cdot\max(V_T-K,0)\cdot\mathbb{1}\{\tau_B>T\} - c$，即**帶敲出障礙的買權，報名費就是權利金**。

- 有限責任下的權益即為買權；權益持有人偏好更高的資產波動度，即使降低整體價值（Jensen & Meckling, 1976, *JFE*）
- 交易員報酬因有限責任而為利潤的凸函數；最適政策下選擇權最終「不是深價內就是深價外」（Carpenter, 2000, *JF*）
- 績效費誘發的冒險在經理人自有資金達約 30% 以上時大幅降低（Kouwenberg & Ziemba, 2007, *JBF*）——本案自有資金比例 1,080/200,000 ≈ **0.54%**

**但必須誠實引入反例**：凸性既非必要也非充分條件，不存在使所有期望效用最大化者一律更冒險的誘因表（Ross, 2004, *JF*）。本案能推出「極大化槓桿」，是因為他**能在 Bybit 對沖掉這個買權，因而在有效意義上風險中立**（Grinblatt & Titman, 1989, *Management Science*）。這條路徑必須明講，否則整個論證會被 Ross (2004) 一擊擊倒。

### 命題 3｜「通過考核」不構成交易能力的證據

- 限期達標機率極大化的最適策略等價於複製一個歐式 digital option；在單資產常數參數的特例下，**最適策略與資產的漂移率無關**——通關策略根本不使用 alpha 資訊（Browne, 1999, *Advances in Applied Probability*）
- 報酬型績效指標可被系統性操縱，即使存在可觀交易成本（Goetzmann, Ingersoll, Spiegel & Welch, 2007, *RFS*）
- **不可能定理**：若罰則重到足以嚇退風險中立的模仿者，也會嚇退任意高技術水準的經理人；不存在僅憑報酬歷史即可分離技術的績效薪酬機制。數值例：一支「年復一年每月成長 1%」的基金可由賣出價外選擇權的模仿者複製，期望可存續並持續吸金約 13 年（Foster & Young, 2010, *QJE*）

→ 平台把罰則移到**事後裁量**（違規即沒收、拒絕出金），是這個不可能定理下的實務閃避。它同時解釋了兩件事：MCF 兩度扣款不是「無故毀約」，而是均衡行為；但也意味著**參與者事前無法確知自己會不會被判違規**——這才是這類商品對散戶最危險的地方。

### 命題 4｜這不是套利，是帶交易對手違約風險的相對價值交易

- 現實套利由資本有限的代理人執行，價差最大時往往正是資本被抽走、必須被迫平倉之時（Shleifer & Vishny, 1997, *JF*）
- **關鍵技術對應**：套利者必須在每個市場分別提供抵押品，兩邊部位不能互相沖抵；因此「經濟上完全對沖」≠「資金流上對沖」（Gromb & Vayanos, 2002, *JFE*）——Bybit 側要真金白銀補繳或被強平時，MCF 側的對應獲利完全不能提出來救援
- 即使給予「MCF 百分之百履約」這個最寬厚的假設，雙重抵押約束下的最適部位仍應**遠小於**抵押允許上限；且套利組合在收斂前通常先虧損，其初期績效「可能與一檔績效不佳的普通投資組合無從區分」（Liu & Longstaff, 2004, *RFS*）
- **最有力的反面校準**：CDS 市場中交易對手風險「小到近乎消失」，摘要明確歸因於市場結構要求對手為互換負債提供擔保品（Arora, Gandhi & Longstaff, 2012, *JFE*）。MCF **不具備其中任何一項機制**——無擔保、無資金隔離、無中央清算、無破產隔離、無申訴管道。因此正確的先驗不是「可忽略的尾部項」，而是**第一階風險項**
- 缺乏部位透明度的雙邊市場會產生交易對手風險外部性，總槓桿超過柏拉圖效率水準（Acharya & Bisin, 2014, *JET*）
- 加密中介違約的量級參照：40 家早期比特幣交易所中 18 家（45%）關閉（Moore & Christin, 2013, FC/LNCS 7859）

### 命題 5｜對沖側不是免費的

- 永續合約價格等於「在由資金費率錨定強度決定的隨機時點抽樣之現貨價格」的風險中性期望值（Ackerer, Hugonnier & Jermann, 2026, *Mathematical Finance*）
- **Bybit 直式永續**的 1 日歷史清算機率：5X 多方 0.55%／空方 0.42%；**20X 為 22.72%／25.33%**；50X 為 62.48%／71.36%。保證金約束下最適隱含槓桿低於 5X（Alexander, Deng & Zou, 2023, *EJOR*）
- 被清算者「權益歸零」；即使不使用槓桿，多頭也會在價格歸零前被清算（Soska et al., 2021, *WWW '21*）
- 排除較弱的反駁：現貨 BTC/USD 平均買賣價差僅 0.0298%（Aleti & Mizrach, 2021, *JFM*）——**手續費確實是小數字，所以論證重心必須放在持有成本與清算風險上，而不是手續費**

→ 他的試算表用 **20 倍全倉**。文獻給出的同一交易所、同一槓桿的日清算機率超過 22%。**模擬盤那側不會爆倉，真錢這側會在同一根 K 棒被清光**——這是整個結構最脆弱的接縫。

### 命題 6｜規則博弈的租金必然被關閉

「只要是人設計的規則就一定有洞可鑽」是契約理論的定理，不是聰明話：

- 多任務問題下，委託人的最適工具往往不是調整誘因斜率，而是**直接限制代理人的其他活動**——MCF 的 "No Copy Trading or Hedging"、"No VPN"、一人一帳戶逐條都是此意義下的 activity restriction（Holmström & Milgrom, 1991, *JLEO*）
- 指標的好壞不取決於雜訊而取決於與目標的對齊程度；即使指標零雜訊仍無法提供 first-best 誘因（Baker, 1992, *JPE*）
- Campbell's Law：量化指標被用於決策的程度越高，越容易受腐化壓力扭曲（Campbell, 1979, *Evaluation and Program Planning*）
- 非線性門檻本身生產 gaming（Oyer, 1998, *QJE*；Brown, Harlow & Starks, 1996, *JF*；Chevalier & Ellison, 1997, *JPE*）
- **但同一組文獻也預測委託人會反覆適應**：規範者與被規範者交替適應，被規範者效率較高，規則約束力持續衰減，但每一輪衰減引發下一輪重寫（Kane, 1977, *JMCB*；Kane, 1981, *JF*）

→ **影片自身的 524 天時間線，就是這個循環走完一輪的教科書級實例。**「找到漏洞」與「可持續獲利」是兩件事。

### 命題 7｜容量限制是硬的，且此處的稀缺要素是「身分」

- 知情交易者的最適交易量由「私有資訊經訂單流洩漏的速度」決定，而非由可用資金決定；分散下單只改變洩漏的時間分布、不消除累積洩漏（Kyle, 1985, *Econometrica*）
- 資金流入直到淨 alpha 歸零；績效不持續不是「無技能」的證據，而是「技能租金被規模擴張耗盡」（Berk & Green, 2004, *JPE*；Pástor, Stambaugh & Taylor, 2015, *JFE*）
- 公開化的代價：97 個報酬預測變數，樣本外報酬低 26%、發表後低 58%（McLean & Pontiff, 2016, *JF*）
- 加密市場自身的收斂：套利機會確曾存在，但自 2018 年 4 月起大幅縮小，此後「幾乎不可能」實際攫取（Crépellière, Pelster & Zeisberger, 2023, *JFM*）

**規模化所需的稀缺要素是身分，其成本被外部化給第三人**：

- 進入犯罪的關鍵不是個人傾向，而是「通往獲利犯罪機會的社會連結」，因此存在大量原本無犯罪生涯的晚啟動者（Kleemans & de Poot, 2008, *European Journal of Criminology*）
- 新手由既有參與者引介、透過社會學習取得技術與規範（Hutchings, 2014, *Crime, Law and Social Change*）
- 共犯三分類：professional facilitators／recruited facilitators／money mules（Bekkers, Leukfeldt & Kleemans, 2024, *Trends in Organized Crime*）
- 逾 3,000 名 16–25 歲荷蘭人中約 10% 曾被人頭招募者接觸，且**普遍低估後果**，部分人視「借帳戶」為可接受（Bekkers, van Houten, Spithoven & Leukfeldt, 2023, *Deviant Behavior*）
- 中和技術（Sykes & Matza, 1957, *American Sociological Review*；Kaptein & van Helvoort, 2019, *Deviant Behavior*）

→ 影片中「我又沒讓平台虧錢」「虧的是市場上亂交易的那些人」在文獻中有專名：**denial of injury**。這類話術的出現時序是**行為前**，功能是解除自我約束，不是事後辯解。

> **外部效度斷層須標明**：全部 money mule 文獻研究的是「提供銀行帳戶收轉贓款」的**資金人頭**（荷蘭、澳洲、美國樣本）。本案 50 位友人提供的是**身分證／護照供境外平台 KYC**，屬 Wang (2025) 分類中的 identity operators，法律與風險結構不同，量化結果不可直接移植。台灣本地的盛行率、招募管道分布均為空白。

### 命題 8｜破產機制：不是「重複下注必破產」，而是超額下注 × 吸收壁 × 完全相關複製

**必須嚴格避免的誇大**：複合報酬均值—變異數有效（含 Kelly）的投資組合**永不冒破產風險**（Hakansson & Miller, 1975, *Management Science*）。「重複下注必然破產」在標準框架下是錯的。

真正的破產來源有三，本案三項全中：

- **(a) 超額下注**：下注恰為兩倍 Kelly 時成長率降至僅剩無風險利率，超過兩倍則長期成長率轉負。即使每次都有 14% 優勢的 700 次下注，全 Kelly 也可能把 1,000 美元打到 18 美元（MacLean, Thorp & Ziemba, 2010, *Quantitative Finance*）
- **(b) 硬性吸收壁**：回撤約束下，部位必須隨接近門檻而縮小（Grossman & Zhou, 1993, *Mathematical Finance*）
- **(c) 成長—安全權衡未被設定**：可用部分 Kelly 在成長端與安全端之間連續取捨（MacLean, Ziemba & Blazenko, 1992, *Management Science*）。從單帳戶擴張至 50 帳戶是把權衡曲線推到極端成長端而完全未設安全端約束

**50 個帳戶同策略、同方向、同時段，總部位變異數是單帳戶的 50² 倍而非 50 倍——這在數學上是槓桿，不是分散。**

報酬形狀：即使機會在基本面上無風險，套利活動仍以正機率產生虧損，且總損失偶爾極大，使報酬呈**負偏態**（Kondor, 2009, *JF*）。這是賭「第三方會不會履約」的二元事件，報酬形狀是**賣出未避險的賣權**（Mitchell & Pulvino, 2001, *JF*）——成功賺小、失敗賠大。而在成熟監理市場中，承擔這種二元履約風險的合理補償是控制交易成本後**約每年 4%**。

→ **「18 個月洗出 1000 萬」與「一週賠 180 萬」不是先成功後失敗，而是同一個報酬分布的兩端。**以未實現崩潰前的樣本推算年化報酬，是選擇性抽樣（Samuelson, 1971, *PNAS*；Brown, Goetzmann, Ibbotson & Ross, 1992, *RFS*）。

### 命題 9｜n=1 敘事的資訊量趨近零，傳染力卻極高

- 社會傳遞偏誤：訊號在人際傳遞中被系統性單向扭曲並遞迴放大（Hirshleifer, 2020, *JF*）
- **凸性放大**：轉換他人採用同一策略的機率是實現報酬的凸函數，因此即使投資人對變異數與偏態毫無偏好，**高變異、高正偏態的主動策略仍無條件佔優並廣泛流行**（Han, Hirshleifer & Walden, 2022, *JFQA*）
- **因果證據**：同儕前 6 個月的**正**報酬使進場機率提高約 12%，而同儕**負**報酬的邊際效果為零；且同儕報酬高的班級學生日後交易利潤顯著較低（Escobar & Pedraza, 2023, *JFE*，13,730 名學生）
- 存活者截斷本身即製造技能假象：波動度與報酬的內生關聯足以「製造出可預測性的表象」（Brown et al., 1992, *RFS*）
- 財經網紅的均衡：56% 具負技能（月異常報酬 −2.3%），且**負技能者追蹤者更多、對散戶交易影響更大**（Kakhbod, Kazempour, Livdan & Schuerhoff, 2023, SFI 工作論文）
- 接收端的認知基礎：小樣本被視為在所有本質特徵上代表母體，連受過統計訓練的專家亦然（Tversky & Kahneman, 1971, *Psychological Bulletin*）；技能線索（試算表、槓桿比、操作細節）本身即在結果不由己的情境中製造不當自信（Langer, 1975, *JPSP*）
- 加密特有的外推：同一批散戶在股票與黃金上逆勢、在加密貨幣上卻動能操作，且此差異無法以個人特徵或彩券偏好解釋（Kogan, Makarov, Niessner & Schoar, 2024, *JFE*）

### 命題 10｜結尾的「你得先相信」：帕斯卡賭注的濫用

影片 18:00–18:30 的論證是標準帕斯卡賭注結構（相信神＝無限快樂 vs 不信＝有限成本），再類比到「相信金融市場一定有漏洞」。

**該論證的標準反駁**：

- 一旦允許無限效用進入決策矩陣，任何帶非零機率通往無限報酬的行動期望值皆為無限大，決策論失去排序功能（Duff, 1986, *Analysis*）
- **混合策略使論證形式無效**：以任意微小機率 p>0 隨機下注同樣得到無限期望效用，故「全押」與「幾乎不投入」並列；連與結論相反的行為也可產生無限期望（Hájek, 2003, *Philosophical Review*）
- 某些報酬結構的期望值是條件收斂級數，重排可得任意值——**取期望值這個動作本身不合法**（Nover & Hájek, 2004, *Mind*）
- 賭注的說服力寄生於矩陣的填法，而填法本身是未經論證的實質假設（Mougin & Sober, 1994, *Noûs*）
- **最精確的結構同構**：任何嚴格奉行期望效用最大化、且對效用不設上界的行為者，都可被宣稱「極小機率、極大報酬」的對手系統性掠奪——文獻稱之為 **Pascal's Mugging**（Bostrom, 2009, *Analysis*）
- 「你應該去相信」在概念上不可執行：信念不受直接意志控制（Williams, 1970；Alston, 1988, *Philosophical Perspectives*）。因此實際被執行的必然不是「相信」，而是**行動**——繳費、開戶、借證件、招募親友

**移植到金融時更弱**：宗教版成立所需的兩個前提是「真無限報酬」與「有限微小成本」。金融版兩者都不成立——報酬有界（他自己說 524 天就結束了），成本也不有界（法律責任、對 50 位人頭與學員的連帶責任、實際發生的 180 萬損失）。他的試算表只算了兩格比例（0.113、0.82），**從未為法律責任與拒付風險編列任何效用值**。

> 精確性保留：帕斯卡賭注在哲學上並非「已被推翻」。SEP 詳列 Schlesinger、Lycan & Schlesinger、Bartha 等辯護方案，明確是進行中的爭論。可以說的是「存在一整套標準反駁，且其中多數在金融移植版本上更強」，不可說「學界公認站不住腳」。

---

## 5. 可以從中學到什麼

### 5.1 真的值得學的（方法論層次）

1. **把制度讀成支付函數，再求極值。** 他做的事情的本質是：把一份規則翻譯成 $\Pi(\cdot)$，然後找 argmax。這是 Holmström & Milgrom (1991)、Baker (1992) 的正式版本，也是任何契約設計者的基本功。「只要是人設計的規則就一定有洞」在契約理論裡是定理，不是雞湯。

2. **辨識有限責任／凸性結構。** 任何「下檔被截斷、上檔開放」的合約都值得停下來算一算（Jensen & Meckling, 1976；Carpenter, 2000）。但記得 Ross (2004)：凸性本身既非必要也非充分，**關鍵是你能不能把那個買權對沖掉，讓自己在有效意義上風險中立**。這一步他做對了，而且對沖比 0.113／0.82 是反推出來的，不是抓的。

3. **把「無風險」拆成具名的風險逐項標價。** 這是我認為這支影片最大的反面教材，也是最值得內化的一課：他拆了市場風險，但把**交易對手風險設為 0**。Arora, Gandhi & Longstaff (2012) 告訴我們，CDS 的交易對手風險之所以小到可忽略，是因為**有擔保品制度**；沒有擔保、沒有資金隔離、沒有中央清算、沒有申訴管道的對手，該給的先驗是第一階風險項。

4. **記住兩腳不能 netting。** Gromb & Vayanos (2002) 的核心結果：分屬不同主體的兩個部位，即使經濟上完全對沖，資金流上也不對沖。他自述的 14,800 美元單帳號實虧，就是這個結構的必然產物。

5. **估「租金還剩多久」，而不是假設永遠。** Kane 的 regulatory dialectic（1977, 1981）預測：被規範者適應得比規範者快，但規則會被反覆重寫。**524 天就是一個完整循環。**做規則套利時該問的不是「這個洞存不存在」，而是「這個洞的半衰期是多久，我的部位規模會不會自己把它關掉」。

6. **算術要自洽。** 他的試算表逐格重算全部吻合。這件事的價值不在於證明他誠實，而在於：**先把每個分支的現金流列完再下手**，是一個可以直接抄的工作習慣。

### 5.2 明確不該學的

1. **把交易對手風險設為 1（履約機率）。** 這使整套論述從 arbitrage 降級為 relative-value trade with credit exposure。而且這裡的對手方比併購套利的情況更糟：**平台可以主動製造理賠事由**（援引 No Hedging 條款），而併購破局機率至少可由歷史頻率估計。

2. **把規模化的成本外部化給朋友。** 50 支手機、50 份證件、十幾位自家社群學員。文獻對此有完整描述：透過既有社會連結招募（Kleemans & de Poot, 2008；Hutchings, 2014），被招募者普遍低估後果（Bekkers et al., 2023），且提供身分開戶在司法實務上自成一類（Wang, 2025）。在台灣，洗錢防制法已於 113/7/31 全文修正，人頭帳戶相關規定為**第 21 條（收集帳戶）與第 22 條（交付提供帳戶）**，兩條均明文涵蓋「向提供虛擬資產服務之事業申請之帳號」。（註：台灣查無同型判例，這是條文涵攝的推論，不是既有實務見解。）

3. **把 50 個完全相關的帳戶當成分散。** 總變異數 ∝ N²。這是槓桿。

4. **用 n=1 的存活敘事教方法。** Han, Hirshleifer & Walden (2022) 的凸性放大結果解釋了為什麼這類內容會流行；Escobar & Pedraza (2023) 給出因果證據：同儕的正報酬使進場機率提高 12%，負報酬的邊際效果為零——**成功故事單向傳播，失敗故事不傳播**，這是結構性的，不是誰的道德問題。

5. **用「月化報酬率」包裝一個容量受限的一次性機會。** 月化 40% 一年是 56.7 倍。這個指標是為長期複利設計的；用在 524 天就歸零、分母定義不明的機會上，量化表述本身即具誤導性。要公允地說：**這不是市場 alpha，是以規則為分母的費用套利，小規模短期做出高月化在數學上可行**，不該一概斥為造假——問題出在表述而非可能性。

6. **帕斯卡賭注式的動員。** 見命題 10。「你得先相信」在概念上不可執行；實際被執行的是繳費、開戶、借證件、招募親友。

### 5.3 對台灣觀眾的一句話風險警語

> 這支影片示範的手法，在平台自己的服務條款裡本來就是明文禁止的違約行為（官網首頁「No Copy Trading or Hedging」、一人一挑戰帳戶；T&C 第 5.2 條禁止跨帳戶反向部位與代他人交易分潤），他自述的兩次重大損失正是違反這些條款的標準後果；影片裡所有獲利數字都只有他單方說法、沒有任何第三方紀錄可查；而在台灣，蒐集他人證件開立帳號可能涉及洗錢防制法第 21、22 條。**請不要模仿。**

**不能加的字**（會變成不實指控）：「詐騙」「吸金」「違法」——查無判決、查無定罪。特別注意：CFTC 起訴 My Forex Funds 那案，2025 年 5 月被紐澤西聯邦法院以 Rule 11 制裁，告訴 with prejudice 駁回並判 CFTC 賠付被告逾 300 萬美元律師費（首席調查員就一筆 CAD 31.55M 稅款作出不實具結）；**詐欺指控從未進入實體審理**。任何拿該案當「prop firm 是詐騙」鐵證的說法都是錯的。

---

## 6. 沒查到的東西（誠實標示）

| 缺口 | 說明 |
|---|---|
| 影片的公開反應 | 發布未滿 24 小時，Google News 無報導，PTT／Dcard／Threads 搜不到討論串。**資料不足，不宜推測風向** |
| 利益衝突鏈 | 2024-09-22 那支影片（118 萬觀看）說明欄只有 Discord 連結，**無 MCF 推薦碼**；2026-08-09 這支說明欄只有前一支影片＋IG＋FB，無任何導流連結。但他持有 Bybit affiliate 連結（affiliate_id=57199、ref_code=BUMPIG）已獲一手確認——**50 個帳戶、20 萬美元名目、反覆開平倉產生的手續費返佣，可能是獨立於「套利獲利」的第二條金流。金額未知，需他自行揭露** |
| 參與者的說法 | 十幾位參與學員、50 位提供證件的朋友，**沒有任何一個第三方參與者的說法**。這是最可能改變結論方向的一塊 |
| prop firm 產業的任何量化基礎事實 | 三個獨立主題檢索均為**零篇同儕審查論文**。通過率、拒付率、報名費佔營收比重全部出自業者部落格與產業媒體，**不可作為論文的實證支撐** |
| 模擬成交 vs 真實成交的績效差距 | 全部當沖文獻用的都是真實成交紀錄；沒有任何文獻估計「無滑價、無拒單的模擬成交會高估報酬多少」 |
| 「模擬帳戶請求權」的定價理論 | 「有限責任買權 × 交易對手拒付選擇權」的複合結構**查無對應模型** |
| 策略性違約（strategic breach via ToS） | 現有違約文獻處理的都是「無力償付」；本案是「有能力償付但援引條款拒付，且解釋權在債務人手中」。**查無把 efficient breach 與金融交易對手風險連起來的期刊論文** |
| 多帳戶／Sybil 規模化的偵測函數 | N 個帳戶產生 N(N−1)/2 對可比對訊號，偵測機率是否超線性上升，**無可引用估計**。Kyle (1985) 只提供結構同構，不提供參數 |
| 全倉 vs 逐倉的清算機率差異 | Alexander 等人的 20X 數字是逐倉邏輯；本案明載 20 倍全倉，此取捨的淨效果**查無量化研究** |
| 對手方可片面違約時的最適下注 | 整個 capital growth 文獻的核心假設之一是**賠付可執行**。當賠付機率本身是下注規模的遞減函數時最適比例應如何調整，**查無期刊論文**——這可能是一個真實的理論缺口 |
| 台灣本地 money mule 實證 | 全部量化基準來自荷蘭與澳洲樣本；台灣的盛行率與風險知覺水準為空白 |
| 帕斯卡賭注移植到金融勸誘的類比效度 | 整個文獻在宗教語境內，**查無任何論文處理其向投資／交易教學的移植** |

---

## 7. 未通過引用查核、不得使用的文獻（節錄）

書目均真實存在，但摘要的核心發現有實質錯誤，已排除於命題與參考文獻表外：

- **Baker & Faulkner (2004, *Social Networks*)**：方向完全相反。原文為「與負責人有既存連結者損失機率 39%，無連結且未盡職調查者 79%」——社會連結是**保護因子**，不可用於「信任取代盡職調查導致損失」的論證
- **Bennett (1990, *Analysis*)**：在文獻中的定位是**為信念自主論辯護、挑戰 Williams**，與「先相信不可執行」的論證方向相反
- **Sobel (1996, *Synthese*)**：SEP 對該文的引用方向與描述相反——Sobel 是少數主張該格效用為**有限**者
- **Hautsch, Scheuch & Voigt (2024, *Review of Finance*)**：「121 個基點套利邊界」「解釋 91% 跨市場價差」兩個數字在刊出版、arXiv 版與全文中皆查無，屬高風險數字幻覺
- **Novy-Marx & Velikov (2016, *RFS*)**：容量方向寫反，原文為「新資本壓低獲利的程度與換手率成**反比**」
- **Piquero, Tibbetts & Blankenship (2005, *Deviant Behavior*)**：達顯著的中和技術為「政府誇大危險」與「利潤最優先」，非 denial of injury
- **Manheim & Garrabrant (2018)**：內容查核通過，但為 arXiv 預印本、非同儕審查。Goodhart 四型分類在經濟／管理期刊中無等價正式化版本，須改以 Campbell (1979) ＋ Baker (1992) 替代

---

## 8. 參考文獻（APA 7；僅列通過查核者）

### 散戶交易績效與技能分布
Barber, B. M., Huang, X., Odean, T., & Schwarz, C. (2022). Attention-induced trading and returns: Evidence from Robinhood users. *The Journal of Finance, 77*(6), 3141–3190. https://doi.org/10.1111/jofi.13183

Barber, B. M., Lee, Y.-T., Liu, Y.-J., & Odean, T. (2009). Just how much do individual investors lose by trading? *The Review of Financial Studies, 22*(2), 609–632. https://doi.org/10.1093/rfs/hhn046

Barber, B. M., Lee, Y.-T., Liu, Y.-J., & Odean, T. (2014). The cross-section of speculator skill: Evidence from day trading. *Journal of Financial Markets, 18*, 1–24. https://doi.org/10.1016/j.finmar.2013.05.006

Barber, B. M., Lee, Y.-T., Liu, Y.-J., Odean, T., & Zhang, K. (2020). Learning, fast or slow. *The Review of Asset Pricing Studies, 10*(1), 61–93. https://doi.org/10.1093/rapstu/raz006

Barber, B. M., & Odean, T. (2000). Trading is hazardous to your wealth. *The Journal of Finance, 55*(2), 773–806. https://doi.org/10.1111/0022-1082.00226

Chague, F., De-Losso, R., & Giovannetti, B. (2019/2020). *Day trading for a living?* [Working paper]. SSRN. https://doi.org/10.2139/ssrn.3423101

Kuo, W.-Y., & Lin, T.-C. (2013). Overconfident individual day traders: Evidence from the Taiwan futures market. *Journal of Banking & Finance, 37*(9), 3548–3561. https://doi.org/10.1016/j.jbankfin.2013.04.036

Seru, A., Shumway, T., & Stoffman, N. (2010). Learning by trading. *The Review of Financial Studies, 23*(2), 705–739. https://doi.org/10.1093/rfs/hhp060

### 有限責任、凸性報酬與誘因設計
Brown, K. C., Harlow, W. V., & Starks, L. T. (1996). Of tournaments and temptations. *The Journal of Finance, 51*(1), 85–110. https://doi.org/10.1111/j.1540-6261.1996.tb05203.x

Browne, S. (1999). Reaching goals by a deadline. *Advances in Applied Probability, 31*(2), 551–577. https://doi.org/10.1239/aap/1029955147

Carpenter, J. N. (2000). Does option compensation increase managerial risk appetite? *The Journal of Finance, 55*(5), 2311–2331. https://doi.org/10.1111/0022-1082.00288

Chevalier, J. A., & Ellison, G. D. (1997). Risk taking by mutual funds as a response to incentives. *Journal of Political Economy, 105*(6), 1167–1200. https://doi.org/10.1086/516389

Foster, D. P., & Young, H. P. (2010). Gaming performance fees by portfolio managers. *The Quarterly Journal of Economics, 125*(4), 1435–1458. https://doi.org/10.1162/qjec.2010.125.4.1435

Goetzmann, W. N., Ingersoll, J. E., Spiegel, M., & Welch, I. (2007). Portfolio performance manipulation and manipulation-proof performance measures. *The Review of Financial Studies, 20*(5), 1503–1546. https://doi.org/10.1093/rfs/hhm025

Grinblatt, M., & Titman, S. (1989). Adverse risk incentives and the design of performance-based contracts. *Management Science, 35*(7), 807–822. https://doi.org/10.1287/mnsc.35.7.807

Hellmann, T. F., Murdock, K. C., & Stiglitz, J. E. (2000). Liberalization, moral hazard in banking, and prudential regulation. *American Economic Review, 90*(1), 147–165. https://doi.org/10.1257/aer.90.1.147

Jensen, M. C., & Meckling, W. H. (1976). Theory of the firm. *Journal of Financial Economics, 3*(4), 305–360. https://doi.org/10.1016/0304-405X(76)90026-X

Kouwenberg, R., & Ziemba, W. T. (2007). Incentives and risk taking in hedge funds. *Journal of Banking & Finance, 31*(11), 3291–3310. https://doi.org/10.1016/j.jbankfin.2007.04.003

Panageas, S., & Westerfield, M. M. (2009). High-water marks: High risk appetites? *The Journal of Finance, 64*(1), 1–36. https://doi.org/10.1111/j.1540-6261.2008.01427.x

Ross, S. A. (2004). Compensation, incentives, and the duality of risk aversion and riskiness. *The Journal of Finance, 59*(1), 207–225. https://doi.org/10.1111/j.1540-6261.2004.00631.x

### 套利的極限與交易對手風險
Acharya, V. V., & Bisin, A. (2014). Counterparty risk externality. *Journal of Economic Theory, 149*, 153–182. https://doi.org/10.1016/j.jet.2013.07.001

Arora, N., Gandhi, P., & Longstaff, F. A. (2012). Counterparty credit risk and the credit default swap market. *Journal of Financial Economics, 103*(2), 280–293. https://doi.org/10.1016/j.jfineco.2011.10.001

Baba, N., & Packer, F. (2009). Interpreting deviations from covered interest parity during the financial market turmoil of 2007–08. *Journal of Banking & Finance, 33*(11), 1953–1962. https://doi.org/10.1016/j.jbankfin.2009.05.007

Du, W., Tepper, A., & Verdelhan, A. (2018). Deviations from covered interest rate parity. *The Journal of Finance, 73*(3), 915–957. https://doi.org/10.1111/jofi.12620

Duffie, D. (2010). Presidential address: Asset price dynamics with slow-moving capital. *The Journal of Finance, 65*(4), 1237–1267. https://doi.org/10.1111/j.1540-6261.2010.01569.x

Gromb, D., & Vayanos, D. (2002). Equilibrium and welfare in markets with financially constrained arbitrageurs. *Journal of Financial Economics, 66*(2–3), 361–407. https://doi.org/10.1016/S0304-405X(02)00228-3

Kondor, P. (2009). Risk in dynamic arbitrage. *The Journal of Finance, 64*(2), 631–655. https://doi.org/10.1111/j.1540-6261.2009.01445.x

Liu, J., & Longstaff, F. A. (2004). Losing money on arbitrage. *The Review of Financial Studies, 17*(3), 611–641. https://doi.org/10.1093/rfs/hhg029

Mitchell, M., & Pulvino, T. (2001). Characteristics of risk and return in risk arbitrage. *The Journal of Finance, 56*(6), 2135–2175. https://doi.org/10.1111/0022-1082.00401

Rime, D., Schrimpf, A., & Syrstad, O. (2022). Covered interest parity arbitrage. *The Review of Financial Studies, 35*(11), 5185–5227. https://doi.org/10.1093/rfs/hhac026

Shleifer, A., & Vishny, R. W. (1997). The limits of arbitrage. *The Journal of Finance, 52*(1), 35–55. https://doi.org/10.1111/j.1540-6261.1997.tb03807.x

### 加密市場結構、永續合約與清算
Ackerer, D., Hugonnier, J., & Jermann, U. J. (2026). Perpetual futures pricing. *Mathematical Finance, 36*(3), 481–499. https://doi.org/10.1111/mafi.70018

Alexander, C., Choi, J., Park, H., & Sohn, S. (2020). BitMEX bitcoin derivatives. *Journal of Futures Markets, 40*(1), 23–43. https://doi.org/10.1002/fut.22050

Alexander, C., Deng, J., & Zou, B. (2023). Hedging with automatic liquidation and leverage selection on bitcoin futures. *European Journal of Operational Research, 306*(1), 478–493. https://doi.org/10.1016/j.ejor.2022.07.037

Aleti, S., & Mizrach, B. (2021). Bitcoin spot and futures market microstructure. *Journal of Futures Markets, 41*(2), 194–225. https://doi.org/10.1002/fut.22163

Brauneis, A., Mestel, R., Riordan, R., & Theissen, E. (2021). How to measure the liquidity of cryptocurrency markets? *Journal of Banking & Finance, 124*, 106041. https://doi.org/10.1016/j.jbankfin.2020.106041

Cheng, Z., Deng, J., Wang, T., & Yu, M. (2021). Liquidation, leverage and optimal margin in bitcoin futures markets. *Applied Economics, 53*(47), 5415–5428. https://doi.org/10.1080/00036846.2021.1922597

Cong, L. W., Li, X., Tang, K., & Yang, Y. (2023). Crypto wash trading. *Management Science, 69*(11), 6427–6454. https://doi.org/10.1287/mnsc.2021.02709

Crépellière, T., Pelster, M., & Zeisberger, S. (2023). Arbitrage in the market for cryptocurrencies. *Journal of Financial Markets, 64*, 100817. https://doi.org/10.1016/j.finmar.2023.100817

Kogan, S., Makarov, I., Niessner, M., & Schoar, A. (2024). Are cryptos different? Evidence from retail trading. *Journal of Financial Economics, 159*, 103897. https://doi.org/10.1016/j.jfineco.2024.103897

Makarov, I., & Schoar, A. (2020). Trading and arbitrage in cryptocurrency markets. *Journal of Financial Economics, 135*(2), 293–319. https://doi.org/10.1016/j.jfineco.2019.07.001

Moore, T., & Christin, N. (2013). Beware the middleman. In *Financial cryptography and data security* (LNCS 7859, pp. 25–33). Springer. https://doi.org/10.1007/978-3-642-39884-1_3

Soska, K., Dong, J.-D., Khodaverdian, A., Zetlin-Jones, A., Routledge, B., & Christin, N. (2021). Towards understanding cryptocurrency derivatives. In *Proceedings of the Web Conference 2021* (pp. 45–57). ACM. https://doi.org/10.1145/3442381.3450059

### 指標博弈、規則適應與容量
Agarwal, V., Gay, G. D., & Ling, L. (2014). Window dressing in mutual funds. *The Review of Financial Studies, 27*(11), 3133–3170. https://doi.org/10.1093/rfs/hhu045

Baker, G. P. (1992). Incentive contracts and performance measurement. *Journal of Political Economy, 100*(3), 598–614. https://doi.org/10.1086/261831

Berk, J. B., & Green, R. C. (2004). Mutual fund flows and performance in rational markets. *Journal of Political Economy, 112*(6), 1269–1295. https://doi.org/10.1086/424739

Berk, J. B., & van Binsbergen, J. H. (2015). Measuring skill in the mutual fund industry. *Journal of Financial Economics, 118*(1), 1–20. https://doi.org/10.1016/j.jfineco.2015.05.002

Bevan, G., & Hood, C. (2006). What's measured is what matters. *Public Administration, 84*(3), 517–538. https://doi.org/10.1111/j.1467-9299.2006.00600.x

Campbell, D. T. (1979). Assessing the impact of planned social change. *Evaluation and Program Planning, 2*(1), 67–90. https://doi.org/10.1016/0149-7189(79)90048-X

Chen, J., Hong, H., Huang, M., & Kubik, J. D. (2004). Does fund size erode mutual fund performance? *American Economic Review, 94*(5), 1276–1302. https://doi.org/10.1257/0002828043052277

Courty, P., & Marschke, G. (2004). An empirical investigation of gaming responses to explicit performance incentives. *Journal of Labor Economics, 22*(1), 23–56. https://doi.org/10.1086/380402

Ederer, F., Holden, R., & Meyer, M. (2018). Gaming and strategic opacity in incentive provision. *The RAND Journal of Economics, 49*(4), 819–854. https://doi.org/10.1111/1756-2171.12253

Holmström, B., & Milgrom, P. (1991). Multitask principal–agent analyses. *The Journal of Law, Economics, & Organization, 7*(Special Issue), 24–52. https://doi.org/10.1093/jleo/7.special_issue.24

Jacob, B. A., & Levitt, S. D. (2003). Rotten apples. *The Quarterly Journal of Economics, 118*(3), 843–877. https://doi.org/10.1162/00335530360698441

Kane, E. J. (1977). Good intentions and unintended evil. *Journal of Money, Credit and Banking, 9*(1), 55–69. https://doi.org/10.2307/1991999

Kane, E. J. (1981). Accelerating inflation, technological innovation, and the decreasing effectiveness of banking regulation. *The Journal of Finance, 36*(2), 355–367. https://doi.org/10.1111/j.1540-6261.1981.tb00449.x

Kyle, A. S. (1985). Continuous auctions and insider trading. *Econometrica, 53*(6), 1315–1335. https://doi.org/10.2307/1913210

McLean, R. D., & Pontiff, J. (2016). Does academic research destroy stock return predictability? *The Journal of Finance, 71*(1), 5–32. https://doi.org/10.1111/jofi.12365

Naik, N. Y., Ramadorai, T., & Strömqvist, M. (2007). Capacity constraints and hedge fund strategy returns. *European Financial Management, 13*(2), 239–256. https://doi.org/10.1111/j.1468-036X.2006.00353.x

Oyer, P. (1998). Fiscal year ends and nonlinear incentive contracts. *The Quarterly Journal of Economics, 113*(1), 149–185. https://doi.org/10.1162/003355398555559

Pástor, Ľ., Stambaugh, R. F., & Taylor, L. A. (2015). Scale and skill in active management. *Journal of Financial Economics, 116*(1), 23–45. https://doi.org/10.1016/j.jfineco.2014.11.008

### 下注規模、成長—安全權衡與回撤
Grossman, S. J., & Zhou, Z. (1993). Optimal investment strategies for controlling drawdowns. *Mathematical Finance, 3*(3), 241–276. https://doi.org/10.1111/j.1467-9965.1993.tb00044.x

Hakansson, N. H., & Miller, B. L. (1975). Compound-return mean-variance efficient portfolios never risk ruin. *Management Science, 22*(4), 391–400. https://doi.org/10.1287/mnsc.22.4.391

Kelly, J. L., Jr. (1956). A new interpretation of information rate. *Bell System Technical Journal, 35*(4), 917–926. https://doi.org/10.1002/j.1538-7305.1956.tb03809.x

MacLean, L. C., Thorp, E. O., & Ziemba, W. T. (2010). Long-term capital growth. *Quantitative Finance, 10*(7), 681–687. https://doi.org/10.1080/14697688.2010.506108

MacLean, L. C., Ziemba, W. T., & Blazenko, G. (1992). Growth versus security in dynamic investment analysis. *Management Science, 38*(11), 1562–1585. https://doi.org/10.1287/mnsc.38.11.1562

Magdon-Ismail, M., Atiya, A. F., Pratap, A., & Abu-Mostafa, Y. S. (2004). On the maximum drawdown of a Brownian motion. *Journal of Applied Probability, 41*(1), 147–161. https://doi.org/10.1239/jap/1077134674

Samuelson, P. A. (1971). The "fallacy" of maximizing the geometric mean in long sequences of investing or gambling. *PNAS, 68*(10), 2493–2496. https://doi.org/10.1073/pnas.68.10.2493

### 社會傳遞、存活者偏差與行為偏誤
Brown, S. J., Goetzmann, W. N., Ibbotson, R. G., & Ross, S. A. (1992). Survivorship bias in performance studies. *The Review of Financial Studies, 5*(4), 553–580. https://doi.org/10.1093/rfs/5.4.553

Camerer, C. F., & Lovallo, D. (1999). Overconfidence and excess entry. *American Economic Review, 89*(1), 306–318. https://doi.org/10.1257/aer.89.1.306

Escobar, L., & Pedraza, A. (2023). Active trading and (poor) performance: The social transmission channel. *Journal of Financial Economics, 150*(1), 139–165. https://doi.org/10.1016/j.jfineco.2023.103706

Han, B., Hirshleifer, D., & Walden, J. (2022). Social transmission bias and investor behavior. *Journal of Financial and Quantitative Analysis, 57*(1), 390–412. https://doi.org/10.1017/S0022109021000077

Heimer, R. Z. (2016). Peer pressure: Social interaction and the disposition effect. *The Review of Financial Studies, 29*(11), 3177–3209. https://doi.org/10.1093/rfs/hhw063

Hirshleifer, D. (2020). Presidential address: Social transmission bias in economics and finance. *The Journal of Finance, 75*(4), 1779–1831. https://doi.org/10.1111/jofi.12906

Hong, H., Kubik, J. D., & Stein, J. C. (2004). Social interaction and stock-market participation. *The Journal of Finance, 59*(1), 137–163. https://doi.org/10.1111/j.1540-6261.2004.00629.x

Kahneman, D., & Lovallo, D. (1993). Timid choices and bold forecasts. *Management Science, 39*(1), 17–31. https://doi.org/10.1287/mnsc.39.1.17

Kakhbod, A., Kazempour, S. M., Livdan, D., & Schuerhoff, N. (2023). *Finfluencers* (SFI Research Paper No. 23-30) [Working paper]. SSRN. https://doi.org/10.2139/ssrn.4428232

Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology, 32*(2), 311–328. https://doi.org/10.1037/0022-3514.32.2.311

Pedersen, L. H. (2022). Game on: Social networks and markets. *Journal of Financial Economics, 146*(3), 1097–1119. https://doi.org/10.1016/j.jfineco.2022.05.002

Shiller, R. J. (2017). Narrative economics. *American Economic Review, 107*(4), 967–1004. https://doi.org/10.1257/aer.107.4.967

Tversky, A., & Kahneman, D. (1971). Belief in the law of small numbers. *Psychological Bulletin, 76*(2), 105–110. https://doi.org/10.1037/h0031322

### 決策論與帕斯卡賭注
Alston, W. P. (1988). The deontological conception of epistemic justification. *Philosophical Perspectives, 2*, 257–299. https://doi.org/10.2307/2214077

Bartha, P. (2007). Taking stock of infinite value. *Synthese, 154*(1), 5–52. https://doi.org/10.1007/s11229-005-8006-z

Beckstead, N., & Thomas, T. (2024). A paradox for tiny probabilities and enormous values. *Noûs, 58*(2), 431–455. https://doi.org/10.1111/nous.12462

Bostrom, N. (2009). Pascal's mugging. *Analysis, 69*(3), 443–445. https://doi.org/10.1093/analys/anp062

Duff, A. (1986). Pascal's wager and infinite utilities. *Analysis, 46*(2), 107–109. https://doi.org/10.1093/analys/46.1.107

Hájek, A. (2000). Objecting vaguely to Pascal's wager. *Philosophical Studies, 98*(1), 1–14. https://doi.org/10.1023/A:1018329005240

Hájek, A. (2003). Waging war on Pascal's wager. *The Philosophical Review, 112*(1), 27–56. https://doi.org/10.1215/00318108-112-1-27

Mougin, G., & Sober, E. (1994). Betting against Pascal's wager. *Noûs, 28*(3), 382–395. https://doi.org/10.2307/2216065

Nover, H., & Hájek, A. (2004). Vexing expectations. *Mind, 113*(450), 237–249. https://doi.org/10.1093/mind/113.450.237

Saka, P. (2001). Pascal's wager and the many gods objection. *Religious Studies, 37*(3), 321–341. https://doi.org/10.1017/S0034412501005686

Williams, B. (1970). Deciding to believe. In H. E. Kiefer & M. K. Munitz (Eds.), *Language, belief, and metaphysics* (pp. 95–111). SUNY Press.

### 人頭帳戶、共犯招募與中和技術
Bekkers, L., Leukfeldt, E. R., & Kleemans, E. R. (2024). Recruiting co-offenders for financial cybercrime. *Trends in Organized Crime*. https://doi.org/10.1007/s12117-024-09556-y

Bekkers, L., Spithoven, R., van Houten, Y., & Leukfeldt, E. R. (2025). The involvement mechanisms of cybercrime. *European Journal of Criminology, 22*(4), 487–507. https://doi.org/10.1177/14773708251323349

Bekkers, L., van Houten, Y., Spithoven, R., & Leukfeldt, E. R. (2023). Money mules and cybercrime involvement mechanisms. *Deviant Behavior, 44*(9), 1368–1385. https://doi.org/10.1080/01639625.2023.2196365

Hutchings, A. (2014). Crime from the keyboard. *Crime, Law and Social Change, 62*(1), 1–20. https://doi.org/10.1007/s10611-014-9520-z

Kaptein, M., & van Helvoort, M. (2019). A model of neutralization techniques. *Deviant Behavior, 40*(10), 1260–1285. https://doi.org/10.1080/01639625.2018.1491696

Kleemans, E. R., & de Poot, C. J. (2008). Criminal careers in organized crime and social opportunity structure. *European Journal of Criminology, 5*(1), 69–98. https://doi.org/10.1177/1477370807084225

Sykes, G. M., & Matza, D. (1957). Techniques of neutralization. *American Sociological Review, 22*(6), 664–670. https://doi.org/10.2307/2089195
