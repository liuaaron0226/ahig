# 學術依據庫 — 研究代理產出

> **自動產生** — 來源：workflow `trading-desk-evidence-base`，7 個並行研究代理 + 對抗式查證。
> 重新產生：`python scripts/export_research.py <journal> <outdir>`
>
> **查證統計**：共 144 條主張 —
> ✅ 通過 31 · ⚠️ 更正 18 · ❌ 推翻 0 · ❓ 未查證 95
>
> 已查證的 49 條中，
> **37% 需要更正或被推翻**。
> 這個比率本身就是最重要的結論：**未經查證的研究產出不可信任。**

---
## 投資人結構、資金流向與行為偏誤：外資／機構流向的預測力、散戶績效、羊群效應、融資融券與期權未平倉的資訊含量

### ✅ [1] 台灣證交所全市場完整交易資料顯示，散戶整體投資組合每年績效落後 3.8 個百分點，總損失規模相當於台灣 GDP 的 2.2%。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：散戶年化績效懲罰 −3.8 個百分點；總損失 = 台灣 GDP 的 2.2%、個人所得總額的 2.8%；同期機構年化績效加分 +1.5 個百分點（已扣手續費與交易稅、未扣其他成本）；散戶虧損幾乎全部來自「主動（aggressive）掛單」，被動掛單在短期反而獲利；樣本期 1995–1999，涵蓋台灣股市全部交易人身分別
- **適用邊界／何時會害人賠錢**：這是 1995–1999 的資料，距今約 27 年；期間台灣尚無當沖降稅（2017 才實施）、無盤中零股、無現行 ETF 生態、外資佔比也遠低於現在，直接外推到 2026 是危險的。更致命的誤用：把「散戶整體虧損」讀成「反做散戶就會賺」——這是總和統計，不是可交易訊號；散戶同時是市場的流動性提供者（見 Kaniel/Saar/Titman 2008），機械性反向操作在散戶被動掛單佔優的區段會直接賠錢。此外 −3.8pp 是「相對市場」，不是絕對虧損。
- **來源**：Barber, B. M., Lee, Y.-T., Liu, Y.-J., & Odean, T. (2009). Just How Much Do Individual Investors Lose by Trading? Review of Financial Studies, 22(2), 609–632. https://academic.oup.com/rfs/article-abstract/22/2/609/1595677

### ⚠️ [2] 台灣當沖客的獲利能力極度集中：不到 1% 的當沖交易人具有可預測的持續獲利能力，其餘絕大多數扣費後為負。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本期 1992–2006 台灣證交所全體交易人；不到 1% 的當沖人口可預測地獲利；前 500 名當沖客日報酬扣費前 61.3 bp、扣費後 37.9 bp；後段當沖客扣費前 11.5 bp、扣費後 −28.9 bp
- **適用邊界／何時會害人賠錢**：「有 1% 的人賺錢」不等於「你可以事先辨認自己屬於那 1%」——論文的排名是用歷史績效事後分組，倖存者偏誤與樣本內排序問題無法完全排除。2006 年前的台灣手續費與稅制與現在差很多（當沖證交稅 2017 起減半至 1.5‰），扣費後數字不可直接搬用。最危險的誤用是拿「前 500 名日賺 37.9bp」去推論「當沖可行」：那是 15 年資料裡的極端右尾，且該群人只佔約 12% 的當沖量能，容量極小。
- **來源**：Barber, B. M., Lee, Y.-T., Liu, Y.-J., & Odean, T. (2014). The Cross-Section of Speculator Skill: Evidence from Day Trading. Journal of Financial Markets, 18, 1–26. https://doi.org/10.1016/j.finmar.2013.05.006

> ⚠️ **查證更正**：兩處要改。(1) 正負號錯誤：後段當沖客扣費前為 −11.5 bp（負值），不是 +11.5 bp。原文摘要為「−11.5 (−28.9) bps per day」，即扣費前已經是負的，扣費後 −28.9 bp。本條寫成「扣費前 11.5 bp」會讓人誤以為後段當沖客在扣費前還小賺、只是被手續費吃掉——實際上他們扣費前就已經在虧，這使結論比原本寫的更悲觀。(2) 頁碼應為 Journal of Financial Markets 18, 1–24（Semantic Scholar 與 RePEc 一致），非 1–26。其餘正確：樣本 1992–2006、前 500 名 61.3 (37.9) bp、「less than 1% of the day trader population is able to predictably and reliably earn positive abnormal returns net of fees」。boundary 中「該群人只佔約 12% 當沖量能」未見於摘要，須查正文後才可引用。

### ⚠️ [3] 跨境資金流入對新興市場未來股價報酬具有統計顯著的正向預測力，但資金流本身同時被過去報酬強烈驅動（正回饋交易）。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：樣本：44 個國家、1994–1998 的每日國際投資組合資金流；流入對未來股票報酬有正向預測力，在新興市場統計顯著；資金流有高度持續性（遠高於報酬的持續性）；當地股價對外資流入的敏感度為正且量級大
- **適用邊界／何時會害人賠錢**：1994–1998 的資料，正好包含亞洲金融風暴，估計值被單一極端事件主導的風險很高。更嚴重的是內生性：既然資金流被過去報酬驅動（正回饋），「流入預測報酬」有很大一塊可能只是動能因子的換皮，而不是外資有獨立資訊。若把它當成「看到外資買超就跟單」的依據，在動能反轉的區段（例如 2000、2008、2022 的高檔反轉）會連續踩雷。此外原文是週／日頻的跨國panel平均效果，個別市場（含台灣）的係數不保證顯著。
- **來源**：Froot, K. A., O'Connell, P. G. J., & Seasholes, M. S. (2001). The portfolio flows of international investors. Journal of Financial Economics, 59(2), 151–193. https://doi.org/10.1016/S0304-405X(00)00084-2

> ⚠️ **查證更正**：(1) 國家數錯誤：應為 46 個國家，不是 44 個。原文摘要為「46 countries from 1994 through 1998」，State Street Bank 資料、逾 300 萬筆交易。(2) 應補上原文的兩項限定，兩者都往懷疑方向修正本條：其一，預測力「僅」存在於新興市場，對已開發國家報酬明確沒有預測力（forecasting power for future emerging market returns, but not for developed country returns）；其二，原文同時發現「暫時性（transitory）流入之後伴隨負的未來報酬」——這條被本條完全省略，而它正是「看到外資買超就跟單」最直接的反證，重要性不亞於本條的 boundary 論述，應補入 key_numbers。(3) 另原文明確「拒絕」了「報酬與流入的正共變數反映國際投資人資訊劣勢」的假說，這與第 5 條 Choe/Kho/Stulz 的韓國結論方向相反，兩條並列時需標明此張力。書目其餘正確：JFE 59(2), 151–193, 2001。

### ✅ [4] 外資在亞洲六個新興市場（含台灣）的資金流呈現對「全球」與「本地」報酬雙重的正回饋交易，且其價格衝擊遠大於早期文獻估計。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：六個亞洲新興股市的外資「全體」日交易資料；發現外資對全球股市報酬亦做正回饋交易（不只本地報酬）；價格衝擊估計值「遠大於」早期研究——原文未在摘要給出單一彙總的 bp 數值，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：作者本人把「對全球報酬做正回饋」解讀為行為因素而非純粹再平衡——這代表外資買超裡有相當比例是被動跟隨美股／MSCI 再配置，不含台股個別資訊。用它支持「外資懂台股基本面」是誤讀。另外「價格衝擊大」是雙面刃：衝擊大代表你看到外資買超時，價格多半已經反映完，追進去買的是衝擊成本本身。樣本期止於 2000 年代初，台灣外資持股比重當時遠低於現在，衝擊係數今日應已下降。
- **來源**：Richards, A. (2005). Big Fish in Small Ponds: The Trading Behavior and Price Impact of Foreign Investors in Asian Emerging Equity Markets. Journal of Financial and Quantitative Analysis, 40(1), 1–27. https://doi.org/10.1017/S0022109000001721

### ✅ [5] 反面證據：外資在韓國市場相對本地機構是資訊劣勢方——買進時付出的價格較高、賣出時拿到的價格較低。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：中大額交易中，外資法人相對本國法人的日交易量加權劣勢：買進 21 個基點、賣出 16 個基點；成因是價格在外資成交「之前」就對他們不利地移動
- **適用邊界／何時會害人賠錢**：這條直接打臉「跟著外資走」的台股通俗操作法。適用邊界：韓國、2000 年代初、且是「中大額交易」；小額交易與被動指數型資金不適用。但它的殺傷力在於——如果外資在成交前價格就已經跑掉，那你在收盤後才看到外資買賣超公告時，資訊優勢早就歸零甚至為負。任何以「外資買超金額」為進場訊號的策略，都必須先證明自己不是在承接那 21bp 的劣勢。反向邊界：Grinblatt & Keloharju (2000) 在芬蘭得到相反結論（外資績效優於家庭），所以「外資笨」也不能當普世法則。
- **來源**：Choe, H., Kho, B.-C., & Stulz, R. M. (2005). Do Domestic Investors Have an Edge? The Trading Experience of Foreign Investors in Korea. Review of Financial Studies, 18(3), 795–829. https://www.nber.org/papers/w10502

### ✅ [6] 反面證據：印尼交易資料顯示本地投資人的獲利高於外資，且本地券商客戶具有短期資訊優勢。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：本地投資人整體獲利高於外資；全球券商客戶的「長期」獲利較高，但「中期（月內）」與「短期（日內）」獲利較低；獲利最高的是「全球券商的本地客戶」——即本地資訊＋全球專業的組合。原文未給單一彙總 bp 數值，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：印尼市場深度、外資限制與資訊揭露程度與台灣差異極大，跨市場外推的效度低。這條的價值不在於「本地人比較強」，而在於證明「外資 vs 本地誰有優勢」在不同市場答案完全相反（韓國：本地贏；芬蘭：外資贏；印尼：本地贏）。任何把「外資＝聰明錢」寫死進策略的做法，都是在賭一個跨市場並不穩定的實證結論。
- **來源**：Dvořák, T. (2005). Do Domestic Investors Have an Information Advantage? Evidence from Indonesia. Journal of Finance, 60(2), 817–839. https://doi.org/10.1111/j.1540-6261.2005.00747.x

### ✅ [7] 外資與本地投資人的交易風格系統性相反：芬蘭資料顯示外資是動能交易者、本地家庭是逆勢交易者，且外資績效優於家庭。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：外資買過去贏家、賣過去輸家（動能）；本地投資人特別是家庭為逆勢；此行為差異在多種「過去報酬計算區間」下都穩定存在；控制行為差異後外資組合仍優於家庭組合。原文摘要未給單一報酬差距數值，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：芬蘭 1990 年代、諾基亞單一權值股佔比極高的市場，樣本外效度存疑。與 Choe/Kho/Stulz (2005)、Dvořák (2005) 結論方向相反，這三篇並列時只能得到「外資是否較聰明因市場而異」的結論，不能單挑一篇支持自己的立場。實務上最危險的誤用：把「外資做動能」當成「外資買超＝趨勢確立」——動能策略在崩盤月份的尾部風險極大（動能崩潰），跟著外資做動能等於同時繼承了動能因子的左尾。
- **來源**：Grinblatt, M., & Keloharju, M. (2000). The investment behavior and performance of various investor types: a study of Finland's unique data set. Journal of Financial Economics, 55(1), 43–67. https://doi.org/10.1016/S0304-405X(99)00044-6

### ⚠️ [8] 外資在韓國 1997 危機前確實有正回饋交易與羊群行為，但危機期間兩者都減弱或消失，且沒有證據顯示外資交易「造成」市場不穩定。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本期 1997 年（重點在最後三個月的危機期）；危機前外資正回饋交易與羊群顯著；危機期間羊群減弱、正回饋消失；全樣本期無外資交易造成韓股不穩定的證據
- **適用邊界／何時會害人賠錢**：這條專門用來打「外資大賣＝崩盤元凶」的敘事。但它的邊界很硬：只有韓國、只有 1997、只有股票市場，且當時外資持股比重遠低於今日；作者也不宣稱外資在任何危機都無害。反向誤用同樣危險——不能因此推論「外資賣超可以不看」。實務上真正該記住的是：危機期間外資行為模式會「換檔」，用平時估出的流向—報酬關係去外推到危機期，會系統性失效。
- **來源**：Choe, H., Kho, B.-C., & Stulz, R. M. (1999). Do foreign investors destabilize stock markets? The Korean experience in 1997. Journal of Financial Economics, 54(2), 227–264. https://doi.org/10.1016/S0304-405X(99)00037-9

> ⚠️ **查證更正**：實質結論完全正確，僅樣本期需修正：應為 1996 年 11 月至 1997 年 12 月（原文摘要為 examines foreign investor behavior in Korea's stock market from November 1996 through December 1997），非本條所寫的「樣本期 1997 年」。這不是雞蛋裡挑骨頭——多出的危機前十三個月正是「危機前正回饋顯著」這個對照組的來源，寫成只有 1997 年會讓人以為前後對照是同一年內切出來的。其餘逐字相符：「strong evidence of positive feedback trading and herding by foreign investors before the period of Korea's economic crisis」「the evidence of herding becomes weaker during the crisis period and positive feedback trading by foreign investors disappears」「We find no evidence that trades by foreign investors had a destabilizing effect」。另建議補入摘要中一句可直接強化本條用途的證據：「the market adjusted quickly and efficiently to large sales by foreign investors and these sales were not followed by negative abnormal returns amplifying their impact」。書目正確：JFE 54(2), 227–264。

### ✅ [9] 反面證據：機構的跨境資金流中，有一部分只是短期價格壓力而非資訊，價格效果會回吐；必須區分永久性與暫時性衝擊。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：樣本：25 個國家、1994–1998 的週頻資料；機構跨境資金流與基本面（NAV）連動；封閉式基金資金流則是短期價格壓力來源；機構流在 NAV 與價格報酬「對稱／不對稱」變動下分別呈現追漲／反轉行為
- **適用邊界／何時會害人賠錢**：這篇的殺傷力在於：資金流之後的價格上漲，可能只是你自己（和同向的人）把價格推上去，之後會還回來。若把「外資買超後上漲」當成資訊確認而加碼，等於在買進暫時性衝擊的頂點。邊界：樣本仍是 1994–1998、以 State Street 託管資料為主，涵蓋的是特定託管客戶而非全體外資；台灣的 FINI 資料結構不同（含大量指數型與避險部位），不能假設分解結果一樣。
- **來源**：Froot, K. A., & Ramadorai, T. (2008). Institutional Portfolio Flows and International Investments. Review of Financial Studies, 21(2), 937–971. https://academic.oup.com/rfs/article-abstract/21/2/937/1609654

### ✅ [10] 反面證據：機構羊群效應在「平均個股」上其實很小——美國退休基金資料中幾乎測不到實質羊群或正回饋交易，只有小型股例外。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本：美國 769 檔全權委託股票型退休基金、1985–1989；除小型股外，未發現實質的羊群或正回饋交易；退休基金持股變動與該股異常報酬之間亦無強烈橫斷面相關。原文摘要未給單一彙總的 LSV 指標百分比，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：這是「羊群」這個詞被過度使用的解毒劑：學術上的羊群測度（LSV 指標）通常只有個位數百分點，遠不足以支撐「法人一起衝所以趨勢必成」的說法。邊界：1985–1989 的美國退休基金，不含對沖基金、不含被動指數資金、不含 ETF 生態；今日的擁擠交易（crowding）機制與當年不同。反過來說，若有人用這篇宣稱「羊群不存在、不必看法人動向」，那也超出了原文範圍——原文明確保留了小型股的例外。
- **來源**：Lakonishok, J., Shleifer, A., & Vishny, R. W. (1992). The impact of institutional trading on stock prices. Journal of Financial Economics, 32(1), 23–43. https://doi.org/10.1016/0304-405X(92)90023-Q

### ✅ [11] 共同基金羊群買進的股票在後續六個月的表現優於羊群賣出的股票約 4 個百分點，效果在小型股更明顯。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本期 1975–1994 美國共同基金業；平均個股的羊群程度不高（與退休基金研究相當）；羊群買進 vs 羊群賣出的股票在後續六個月報酬差約 4%；成長型基金羊群程度高於收益型基金
- **適用邊界／何時會害人賠錢**：4% 是「買方組合減賣方組合」的多空價差，不是單邊報酬，實務上要放空一半才拿得到，而羊群集中的小型股正是最難放空、借券成本最高的地方——扣掉借券費與衝擊成本後可能所剩無幾。樣本止於 1994，之後被大量套利；McLean & Pontiff (2016) 的通則預期此類已發表訊號發表後衰減約 58%。此外原文的解讀是「羊群加速價格調整」（即基金是對的），若你以為這是可以套利的錯價，方向就理解反了。
- **來源**：Wermers, R. (1999). Mutual Fund Herding and the Impact on Stock Prices. Journal of Finance, 54(2), 581–622. https://doi.org/10.1111/0022-1082.00118

### ✅ [12] 機構羊群的主因是機構彼此從對方的交易中推論資訊（互相跟隨），而非單純的動能／正回饋交易。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：機構會跟隨其他機構「上一期」的交易，也會跟隨自己上一期的交易；雖然機構整體是動能交易者，但羊群中只有很小一部分可由動能交易解釋。原文摘要未給單一彙總的分解百分比，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：「互相推論資訊」在資訊為真時加速價格發現，在資訊為假時就是資訊瀑布（information cascade）——同一個機制可以造成 2000 年網通泡沫，也可以造成 2021 年迷因股。這篇不能拿來當「法人一致看多就跟」的依據，因為它恰恰說明法人的一致性有一部分是自我參照而非獨立判斷。邊界：美國 13F 季頻持股資料，季頻的解析度無法應用在台股日頻的三大法人買賣超上。
- **來源**：Sias, R. W. (2004). Institutional Herding. Review of Financial Studies, 17(1), 165–206. https://academic.oup.com/rfs/article-abstract/17/1/165/1564376

### ✅ [13] 反面證據：機構持股大幅變動之後的一年內，並未觀察到報酬均值回歸——機構買進的股票後續表現優於機構賣出的股票。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：機構持股變動與同期報酬呈強烈正相關；機構羊群與落後報酬正相關（與動能有關）；大幅機構持股變動後的一年內無報酬均值回歸現象。原文摘要未給單一彙總的報酬差距數值，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：這條與「法人推高股價後會回吐」的直覺相反，但別過度解讀：同期正相關無法區分「機構有資訊」與「機構把價格推上去」，作者自己說兩者都有貢獻。年頻資料掩蓋了中間的路徑——一年後不回歸不代表三個月內不會腰斬。樣本為 1977–1996 美國年頻機構持股，換到台股日頻三大法人買賣超上完全沒有對應關係，硬套會得到錯誤的持有期間。
- **來源**：Nofsinger, J. R., & Sias, R. W. (1999). Herding and Feedback Trading by Institutional and Individual Investors. Journal of Finance, 54(6), 2263–2295. https://doi.org/10.1111/0022-1082.00188

### ⚠️ [14] 融資保證金與市場波動的關係在頂級期刊上是「直接矛盾」的未解問題：AER 與 JF 同年得出相反結論，且後續證據顯示是波動 Granger 導致保證金調整、而非相反。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：Hardouvelis：在正常與多頭期間提高保證金要求可顯著降低波動，空頭期間則測不到關係；Hsieh & Miller：找不到聯準會保證金要求抑制波動的可信證據，並指 Hardouvelis 的檢定設計有瑕疵；兩篇一致的部分是「保證金變動傾向跟在波動變動之後」（波動 Granger 導致保證金）
- **適用邊界／何時會害人賠錢**：這條的用途不是「證明什麼」，而是證明「這題沒有共識」。任何用融資餘額／保證金水準推論未來波動的模型，都建立在一個連 AER 與 JF 都打架的關係上。實務致命點：因果方向若真的是「波動 → 保證金」，那你看到的融資變化只是波動的落後指標，用它預測波動等於用昨天的雨預測昨天的雨。樣本皆為 1980 年代前的美國全市場保證金規定，台股的融資成數與斷頭機制屬於個股層級且由券商執行，制度上不可類比。
- **來源**：Hardouvelis, G. A. (1990). Margin Requirements, Volatility, and the Transitory Component of Stock Prices. American Economic Review, 80(4), 736–762（部分索引記為 736–763）；Hsieh, D. A., & Miller, M. H. (1990). Margin Regulation and Stock Market Volatility. Journal of Finance, 45(1), 3–29（Wiley 索引記為 3–30）https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1990.tb05078.x

> ⚠️ **查證更正**：兩篇論文都真實存在且書目大致正確，但本條有一處明確的張冠李戴，外加一處推論過頭。(1) 張冠李戴：「在正常與多頭期間提高保證金要求可顯著降低波動，空頭期間則測不到關係」不是 Hardouvelis (1990, AER) 的結論。該文摘要只說「higher or rising margin requirements are associated with lower stock price volatility, lower excess volatility, and smaller deviations of stock prices from their fundamental values」，全期成立，完全沒有做多空頭分段。多空頭不對稱是另一篇論文的結果：Hardouvelis, G. A., & Theodossiou, P. (2002). The Asymmetric Relation Between Initial Margin Requirements and Stock Market Volatility Across Bull and Bear Markets. Review of Financial Studies, 15(5), 1525–1559. DOI 10.1093/rfs/15.5.1525（經 OpenAlex 標題精確比對確認）。要保留這個論點就必須改引 2002 年 RFS 那篇。(2) 推論過頭：「兩篇一致的部分是波動 Granger 導致保證金」不成立。這是 Hsieh & Miller 單方面的結論（「changes in margin requirements by the Fed have tended to follow, rather than lead, changes in market volatility」），Hardouvelis 主張的正是相反的因果方向，兩人當年公開筆戰，說他們在因果方向上「一致」等於抹掉了這條 claim 自己想強調的矛盾。(3) 書目小校：AER 原文標題為 Transitory Components（複數）。Hsieh & Miller (1990), JF 45(1), 3–29 的內容驗證無誤，並另有一項本條可補的發現：保證金要求與融資餘額之間確實存在預期中的負向關係。

### ⚠️ [15] 反面證據：台灣資料顯示當沖交易確實提高日內波動，但「累積融資餘額」上升反而使市場趨於穩定，支持理性投機假說。

- **證據等級**：實證 · 研究者信心：low
- **關鍵數字**：樣本期間台灣個別投資人約佔成交量 90%（部分期間 92%）；當沖交易提高日內價格波動，且在當日上漲時波動放大更明顯；融資餘額（累積投機部位）上升與波動下降相關；成交量上升與 1997 亞洲金融風暴均顯著提高波動
- **適用邊界／何時會害人賠錢**：直接與台股實務界「融資餘額創高＝散戶過熱＝危險」的信仰衝突，這正是它該被記錄的理由。但別反向濫用：這是 2003 年發表、資料為 1990 年代的台股，當時無現行當沖降稅、無盤中零股、無高比重 ETF；且 Global Finance Journal 屬中階期刊，未經頂刊同儕檢驗，複製性未知。最重要的邊界：「融資餘額水準與波動負相關」是無條件平均關係，完全不排除「融資餘額在崩盤前創高、崩盤時斷頭加速下跌」的條件性事件——用平均關係去管理尾部風險，是這條最容易害人的方式。
- **來源**：Hsin, C.-W., Guo, W.-C., Tseng, S.-S., & Luo, W.-C. (2003). The impact of speculative trading on stock return volatility: the evidence from Taiwan. Global Finance Journal, 14(3), 243–270. https://www.sciencedirect.com/science/article/abs/pii/S1044028303000437

> ⚠️ **查證更正**：書目經 RePEc 與 OpenAlex 雙重確認為真且正確：Hsin, C.-W., Guo, W.-C., Tseng, S.-S., & Luo, W.-C. (2003). The impact of speculative trading on stock return volatility: the evidence from Taiwan. Global Finance Journal, 14(3), 243–270. DOI 10.1016/j.gfj.2003.10.003（本條原引用未附 DOI，建議補上）。但實質內容一項都驗不到：RePEc 明載 No abstract is available for this item，OpenAlex 無摘要，ScienceDirect 回 403。也就是說 key_numbers 裡的每一個數字（散戶佔量 90%／92%、當沖提高日內波動、上漲日放大更明顯、融資餘額上升與波動下降相關、1997 風暴顯著提高波動）目前都沒有任何可公開取得的原始文字支持。依「不可以幻想」的標準，這一條應從「實證證據」降級為「引用存在、內容待查全文」，在取得全文前不得用來推翻台股實務界「融資餘額創高＝危險」的信仰——本清單中唯一一條明確與市場共識對衝的台灣證據，恰好是唯一一條內容驗不到的，這個組合本身就該提高警覺。confidence 標為 low 是正確的，但仍嫌不足。

### ⚠️ [16] 反面證據：涵蓋中國、日本、台灣 6,024 檔股票的研究發現，融資買進（margin trading）對橫斷面未來報酬「沒有」統計顯著的預測力；只有放空才有預測力。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：樣本：中國 A 股、日本、台灣共 6,024 檔股票的融資與融券逐檔資料；放空（short sales）對未來橫斷面報酬呈顯著負向預測；融資買進與未來報酬無顯著關係；融資活動的跨股相關性較高、對公司基本面預測力弱，顯示融資交易人較不具個股層級資訊優勢。卷期頁碼未查得，僅確認 2024 年線上發表
- **適用邊界／何時會害人賠錢**：這是台股「融資餘額」派最該正視的一條：融資變化被證明缺乏個股層級資訊，跨股高度共動意味著它更像一個總體槓桿／情緒變數，不是選股訊號。邊界：這是「橫斷面」結論，不排除融資總量在「時間序列」上對大盤有訊息（本研究未回答）；且中日台三地融資制度差異大（中國有兩融標的限制、台灣有融資成數與斷頭），彙總係數可能掩蓋台灣單獨的效果。此外此文尚屬近期發表，尚未有獨立複製。
- **來源**：Chen, Z., Li, P., Wang, Z., & Zhang, B. (2024). Leveraged trading and stock returns: Evidence from international stock markets. Journal of Empirical Finance. https://www.sciencedirect.com/science/article/abs/pii/S1386418124000259 ；工作論文版 SSRN 3776995

> ⚠️ **查證更正**：期刊掛錯。正確書目為：Chen, Z., Li, P., Wang, Z., & Zhang, B. (2024). Leveraged trading and stock returns: Evidence from international stock markets. Journal of Financial Markets, 69, 100907. DOI 10.1016/j.finmar.2024.100907（經 OpenAlex 與 RePEc 雙重確認），不是 Journal of Empirical Finance。附帶一提，本條自己給的 ScienceDirect 網址 pii=S1386418124000259 其實就是對的——S1386-4181 正是 Journal of Financial Markets 的 ISSN 前綴，而 Journal of Empirical Finance 是 S0927-5398——所以是網址對、刊名錯，屬於可自我檢核卻沒檢核出來的錯誤。實質結論則完全正確，摘要逐字支持：「while short selling has cross-sectional return predictability, margin trading does not」「margin-trading activities demonstrate a stronger correlation across stocks and weakly predict firm fundamentals」「margin traders are less likely to possess a firm-specific information advantage」「margin traders are less sophisticated than short sellers」。惟兩項細節須查正文：摘要僅稱 three international stock markets，未點名中國／日本／台灣；「6,024 檔股票」亦未見於摘要。這兩個數字在查證前不應寫進 claim 主文。

### ⚠️ [17] 槓桿引發的強制拋售會造成真實但可逆的價格衝擊：中國 2015 年股災中，被高槓桿帳戶集中持有的股票出現顯著異常下跌，並在後續約 40 個交易日內回補。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：帳戶層級交易資料，涵蓋券商融資帳戶與場外配資（影子）帳戶；投資人在帳戶槓桿逼近上限時大量賣出持股；被瀕臨追繳帳戶集中持有的股票出現高賣壓與顯著異常下跌，並在其後 40 個交易日內回補；未受監管、高槓桿的影子配資帳戶雖持股市值遠小，對崩盤的貢獻卻大於受規範的券商帳戶
- **適用邊界／何時會害人賠錢**：截至查證時（2026-08）此文在 NBER 頁面仍列為工作論文，未見正式期刊出版資訊，因此未經頂刊同儕審查的完整檢驗——引用時必須標明工作論文身分。邊界：中國 2015 年的場外配資是特定制度產物（4–10 倍槓桿、無統一監管），台灣的融資成數（約 6 成、槓桿約 2.5 倍）與券商斷頭機制完全不同，量級不可直接搬用。最危險的誤用是把「40 個交易日回補」當成抄底時程表：這是事後平均，個股層級的分散度極大，且回補的前提是基本面沒有同步惡化。
- **來源**：Bian, J., He, Z., Shue, K., & Zhou, H. (2018). Leverage-Induced Fire Sales and Stock Market Crashes. NBER Working Paper No. 25040. https://www.nber.org/papers/w25040

> ⚠️ **查證更正**：工作論文身分與核心機制都查證無誤，唯一問題是被放進 claim 主文的「40 個交易日」查不到出處。(1) 已證實部分：NBER WP 25040（2018 年 9 月發布）摘要逐字支持「Stocks that are disproportionately held by accounts close to leverage limits experience high selling pressure and abnormal price declines which subsequently reverse」與「Unregulated shadow-financed margin accounts, facilitated by FinTech lending platforms, contributed more to the crash despite their smaller asset holdings relative to regulated brokerage accounts」。(2) 工作論文身分正確：NBER 頁面未列已出版版本，OpenAlex 亦僅查得 NBER WP 25040 與 SSRN preprint 3345297 兩筆，無同儕審查期刊版本，本條 boundary 的標註屬實。(3) 須修正：摘要只說價格下跌「subsequently reverse（其後反轉）」，並未給出任何時程。「40 個交易日內回補」目前無來源支持，須查正文圖表確認後才可引用；在此之前應自 claim 主文與 key_numbers 移除，或明確標為未驗證。這一點特別重要，因為本條 boundary 自己就警告「最危險的誤用是把 40 個交易日當成抄底時程表」——那個時程表數字本身現在也還沒站穩。

### ✅ [18] 個股選擇權的買方開倉 put-call 比率對次日與次週股價有顯著預測力，且來源被歸因為選擇權交易人持有的非公開資訊，而非市場無效率。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本：1990–2001 全部 CBOE 掛牌選擇權的每日成交量；低 put-call 比率股票次日報酬高於高 put-call 比率股票逾 40 個基點，一週逾 1%；在知情交易人密度較高的股票、與槓桿較大的合約上，預測力更強
- **適用邊界／何時會害人賠錢**：關鍵限制：這需要「買方開倉」的分類資料（open-buy volume），一般投資人拿得到的是總成交量或未平倉總數，用總量算出來的 put-call ratio 沒有同樣的預測力（見 Chang/Hsieh/Lai 2009 在台指選擇權的直接反證）。40bp 的橫斷面價差在扣除選擇權買賣價差與股票交易成本後所剩無幾，且樣本止於 2001；McLean & Pontiff (2016) 的通則預期發表後衰減。最後，這是「個股」選擇權的結論，作者對指數選擇權（S&P500／S&P100／NASDAQ100）並未找到同等的知情交易證據——把它拿去解讀台指選擇權或台指期的總量，是跨越了原文最明確的邊界。
- **來源**：Pan, J., & Poteshman, A. M. (2006). The Information in Option Volume for Future Stock Prices. Review of Financial Studies, 19(3), 871–908. https://academic.oup.com/rfs/article-abstract/19/3/871/1646711

### ✅ [19] 關鍵反面證據（台灣）：台指選擇權的「總量」對加權指數沒有預測力，只有拆解出來的外資法人部位才有——合計數字會把資訊洗掉。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：以台灣 TAIEX 選擇權（TXO）分交易人類別資料檢驗；彙總後的選擇權成交量對現貨指數無預測力；外資法人雖交易量有限，卻具顯著預測力；預測力集中於「近價（near-the-money）」與「中期到期」合約
- **適用邊界／何時會害人賠錢**：這條同時是支持與反對「看法人期權部位」的證據，取決於你看的是哪一欄。實務上最致命的誤用：台灣散戶普遍看的是「三大法人合計」與「未平倉總量」——本文顯示合計數字沒有預測力；期交所本身也提示三大法人資訊是眾多法人互抵後的合計結果。另外「近價、中期合約」的限定條件表示：外資的價外週選部位與這個結論無關。樣本為 2000 年代中期，當時 TXO 尚無週選擇權、無現行造市與 HFT 生態，時效性存疑。
- **來源**：Chang, C.-C., Hsieh, P.-F., & Lai, H.-N. (2009). Do informed option investors predict stock returns? Evidence from the Taiwan stock exchange. Journal of Banking & Finance, 33(4), 757–764. https://ideas.repec.org/a/eee/jbfina/v33y2009i4p757-764.html

### ✅ [20] 台指選擇權中外資法人是最具資訊的交易人，且其預測力在下跌行情中更明顯；四類交易人中僅外資具顯著預測力。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：Hsieh & He (2014)：外資為最具資訊的交易人，預測力在下跌行情更顯著；外資使用價外選擇權取得槓桿、選擇中期到期以平衡 delta 曝險與時間價值耗損、以限價單與中型單量掩飾資訊優勢。Lee & Wang (2016)：四類交易人中僅外資具顯著預測力，拆解後的 call O/S 比率優於整體 O/S 與 put-call 比率。兩文均未提供單一彙總的報酬預測 bp 數值，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：兩篇皆為中階期刊（JIFMIM、PBFJ），未經頂刊檢驗，且結論高度依賴期交所分類的「外資」欄位——該欄位混合了方向性投機、現貨避險、指數套利與 ETF 造市，論文推論其為「投機」是間接推理而非直接觀測到部位動機。時效性問題嚴重：樣本多為 2000 年代至 2010 年代初，此後台指選擇權的週選、造市制度與外資結構已大幅改變。最危險的誤用是把「外資有資訊」推論成「外資部位方向可直接照抄」——資訊優勢是統計上的、扣成本後極薄，且下跌行情才明顯，意味著多頭時跟單的期望值可能為零。
- **來源**：Hsieh, W. G., & He, H.-R. (2014). Informed trading, trading strategies and the information content of trading volume: Evidence from the Taiwan index options market. Journal of International Financial Markets, Institutions and Money, 31(C), 187–215. https://ideas.repec.org/a/eee/intfin/v31y2014icp187-215.html ；Lee, Y.-H., & Wang, D. K. (2016). Information content of investor trading behavior: Evidence from Taiwan index options market. Pacific-Basin Finance Journal, 38, 149–160.

### ✅ [21] 誠實標記缺口：「外資台指期淨未平倉可否直接解讀為方向性看法」——查無頂級期刊的直接證據，現有文獻只能間接支持，且該欄位在制度上必然混雜避險與套利部位。

- **證據等級**：實證 · 研究者信心：low
- **關鍵數字**：Chuang, Lin & Weng (2019)：以台灣期交所全部逐筆成交資料，發現外資法人在交易方向、委託型態、交易對手、委託量與委託積極度上全面優於本土投資人，並認為「資訊優勢」比「下單策略」更能解釋其超額績效——但該文未直接檢驗「淨未平倉部位可否作為方向訊號」。Wang et al. (2025)：需先對機構情緒做「頻率分解」才取得對台指期與大盤報酬的預測力，暗示原始淨部位序列本身的訊噪比不足。針對「外資期貨淨未平倉＝方向性看法」的直接證據：未查得具體數值，亦未查得頂級期刊實證
- **適用邊界／何時會害人賠錢**：這是本清單中最該被打上警告的一條。三點失效情境：(1) 期交所公告的外資期貨部位在定義上就混合了現貨避險空單、指數套利、ETF 造市與方向性投機，無法從公開資料分離，把淨額當方向解讀是把三種不同動機的部位相加後求平均；(2) 期交所本身明示該資訊是「眾多法人機構看法的合計互抵結果」，不代表任一機構的策略；(3) 現有支持性文獻（Chuang 2019、Wang 2025）都是中階期刊、且 Wang et al. 必須經過頻率分解才有預測力，等於承認原始序列不可直接使用。若使用者在盤後看到「外資期貨淨空單創高」就做空，最可能的失效情境是：那批空單是外資同時大買現貨的避險腿，方向解讀完全相反。在取得能分離避險／投機的資料之前，此條應視為未證實的市場民俗。
- **來源**：間接證據：Chuang, Y.-W., Lin, Y.-F., & Weng, P.-S. (2019). Why and how do foreign institutional investors outperform domestic investors in futures trading: Evidence from Taiwan. Journal of Futures Markets, 39(3), 279–301. https://ideas.repec.org/a/wly/jfutmk/v39y2019i3p279-301.html ；Wang, Y.-H., Chang, S.-L., Lee, H.-C., & Lien, D. (2025). Forecasting the Market Returns and Portfolio Enhancement With Frequency-Decomposed Institutional Investor Sentiment: Evidence From the Taiwan Futures Market. Journal of Futures Markets, 45(6), 521–546. https://onlinelibrary.wiley.com/doi/10.1002/fut.22580 ；制度說明：臺灣期貨交易所三大法人交易資訊查詢頁 https://www.taifex.com.tw/cht/3/futContractsDate

### ✅ [22] 反面證據：散戶並非永遠是錯的——NYSE 資料顯示個別投資人密集買進後的次月有正超額報酬、密集賣出後為負，方向與「散戶是笨錢」相反。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：大樣本 NYSE 股票的散戶淨交易與短期報酬動態關係；散戶在前一月下跌後買進、上漲後賣出（逆勢）；散戶密集買進後的一個月有正超額報酬、密集賣出後有負超額報酬；作者解釋為風險趨避的散戶對機構的立即成交需求提供流動性而獲得補償。原文摘要未給單一彙總的百分比數值，本欄未查得具體數值
- **適用邊界／何時會害人賠錢**：這條與 Barber/Lee/Liu/Odean (2009) 的台灣結論並不矛盾但極易被混用：台灣那篇說散戶「主動掛單」虧錢、「被動掛單」短期獲利，本篇量到的正是被動提供流動性的那一塊。誤用風險：把它讀成「散戶買超可以跟」——效果只有一個月、需要橫斷面多空、且報酬本質是流動性補償而非選股能力，在流動性充裕、機構不急著成交的時期會消失。樣本為 2000–2003 的 NYSE，制度（十進位化前後、無現行 HFT）與台股完全不同。
- **來源**：Kaniel, R., Saar, G., & Titman, S. (2008). Individual Investor Trading and Stock Returns. Journal of Finance, 63(1), 273–310. https://doi.org/10.1111/j.1540-6261.2008.01316.x

### ✅ [23] 注意力驅動的散戶羊群會系統性製造事後負報酬：Robinhood 用戶當日買進最多的股票，後續 20 個交易日平均異常報酬為 −4.7%。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：每日 Robinhood 用戶買進最多的股票，其後 20 日平均異常報酬 −4.7%；羊群事件當日該股平均大漲約 14%，其後轉為顯著負報酬、20 日後仍下跌約 5%；羊群事件股票的放空活動明顯增加
- **適用邊界／何時會害人賠錢**：樣本期為 Robinhood 公開持有人數 API 存在的期間（約 2018–2020），涵蓋 2020 疫情散戶潮這個極端事件，估計值可能被單一時期主導；該 API 已停止公開，訊號不可再取得——這是「訊號因資料消失而失效」的教科書案例。誤用風險：看到台股某股當沖比暴增就假設 20 日後 −4.7%，這是把美國零手續費 App 的注意力機制硬套到不同市場結構。另外 −4.7% 是等權重平均，個股分散度極大，做空的尾部風險（軋空）正是這類股票最高的地方。
- **來源**：Barber, B. M., Huang, X., Odean, T., & Schwarz, C. (2022). Attention-Induced Trading and Returns: Evidence from Robinhood Users. Journal of Finance, 77(6), 3141–3190. https://doi.org/10.1111/jofi.13183

### ✅ [24] 元警告：所有已發表的報酬預測訊號在樣本外平均衰減 26%，在論文發表後平均衰減 58%——本證據庫中的每一條可交易訊號都必須先扣掉這個折扣。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：檢驗 97 個已被證明可預測橫斷面股票報酬的變數；樣本外（原文樣本結束後、發表前）組合報酬低 26%；發表後低 58%；作者推估其中 32%（=58%−26%）可歸因於「因發表而被套利」；樣本內報酬越高的訊號，發表後衰減越大
- **適用邊界／何時會害人賠錢**：這條的作用是對本清單其餘所有條目施加系統性折扣，但它自己也有邊界：樣本是美國股票的橫斷面異常，不必然適用於總體層級的資金流訊號、也不必然適用於資訊揭露有制度性延遲的市場（如台股法人買賣超為盤後公告）。反向誤用同樣危險——不能因此宣稱「所有學術訊號都沒用」；26% 與 58% 是衰減幅度，不是歸零。實務上最該記住的是最後一項：樣本內報酬看起來越漂亮的訊號，發表後崩得越兇，因此對本庫中任何「數字特別好看」的條目要加倍懷疑。
- **來源**：McLean, R. D., & Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? Journal of Finance, 71(1), 5–32. https://doi.org/10.1111/jofi.12365

---

## 股票橫斷面報酬的因子證據（動能、反轉、價值、規模、獲利、投資，含樣本外衰退與亞洲市場反面證據）

> ❓ **本主題的對抗式查證未完成。**
> 以下主張尚未經獨立查證，**不可當作結論使用**。
> 已查證主題的錯誤率約 39%，故未查證內容的可靠度應假定同等偏低。

### ❓ [1] 買進過去 6 個月贏家、放空輸家並持有 6 個月的動能策略，在 1965–1989 年美國 NYSE/AMEX 樣本中年化複利超額報酬為 12.01%。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：6-6 策略年化複利超額報酬 12.01%；最強組合為 12 個月形成期/3 個月持有期，落後 1 週執行時 1.49%/月（無落後時 1.31%/月）；6 個月形成期各持有期約 1%/月；樣本期 1965/01–1989/12
- **適用邊界／何時會害人賠錢**：這是等權重十分位、零成本多空、不扣交易成本與放空成本的紙上報酬。實務上輸家股多為小型低價股，放空券源與衝擊成本會吃掉大半。作者自己在同一篇就指出第一年的超額報酬在接下來兩年會消散一部分——把它當長期持有的理由會賠錢。樣本結束於 1989 年，距今 36 年，不能直接外推到 2026 年。
- **來源**：Jegadeesh, N., & Titman, S. (1993). Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency. The Journal of Finance, 48(1), 65-91. DOI 10.1111/j.1540-6261.1993.tb04702.x（已下載 JSTOR 原文 PDF 逐字核對結論段）

### ❓ [2] 同一篇動能原始論文中，動能策略在 1 月的報酬是顯著為負的 -6.86%/月，也就是說一年裡最重要的一個月它是反向的。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：全樣本 1 月 -6.86%（t=-3.52）；最小型股組 S1 為 -7.97%（t=-3.36）；中型 -3.47%（t=-2.14）；最大型 -1.61%（t=-1.28，不顯著）。1 月為正報酬的比例僅 0.24（全樣本），小型股僅 0.16
- **適用邊界／何時會害人賠錢**：任何「全年無休持有動能」的回測都在 1 月被血洗一次，靠其他 11 個月補回來。若資金曲線在 1 月被追繳保證金或被贖回，就永遠等不到補回來的那 11 個月。且此為 1965–1989 美國稅務年結構下的結果，稅制與法人結構已變，不保證 1 月效應仍在。
- **來源**：Jegadeesh, N., & Titman, S. (1993). The Journal of Finance, 48(1), 65-91, Table V（月份別零成本組合平均報酬，原文 PDF 核對）

### ❓ [3] 動能在原始論文的五個五年子區間中，有一個子區間（1975–1979）報酬為負且不顯著，證明它並非每個五年都有效。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：6-6 策略各子區間月報酬：65-69 為 +1.23%（t=1.94）、70-74 為 +1.09%（t=1.23，不顯著）、75-79 為 -0.44%（t=-0.51，負值）、80-84 為 +1.27%（t=2.67）、85-89 為 +1.62%（t=3.42）
- **適用邊界／何時會害人賠錢**：五個子區間裡有兩個 t 值低於 2，一個直接為負。這代表即使在論文自己的樣本內，投資人也可能連續 5–10 年拿不到動能溢酬。以人的職涯與基金的存續期來看，「五年無效」等同於策略死亡——經理人會先被開除，資金會先被贖回。
- **來源**：Jegadeesh, N., & Titman, S. (1993). The Journal of Finance, 48(1), 65-91, Table VI（5 年子區間報酬，原文 PDF 核對）

### ❓ [4] 動能策略在 1930 年代大空頭後的市場反彈中發生過災難級崩潰，1932 年 7 月單月虧 40%、8 月再虧 68%。

- **證據等級**：歷史 · 研究者信心：high
- **關鍵數字**：1932/07 等權指數在前 6 個月下跌 40% 後單月反彈 43%，6-6 動能組合當月 -40%；1932/08 指數再漲 66%，動能組合 -68%。1930 年代另有 4 個月動能虧損超過 40%，全部發生在市場大漲時。該期間零成本組合的 beta 約 -0.5，且在市場下跌後顯著升高
- **適用邊界／何時會害人賠錢**：這不是尾部風險，是結構性的：動能在大跌後會系統性地做空高 beta 瀕臨破產股，市場一反彈就被軋到爆。任何用常態分配、標準差或 VaR 估計動能風險的模型都會嚴重低估。用槓桿做動能在這種月份會直接歸零，不是回撤而是斷頭。
- **來源**：Jegadeesh, N., & Titman, S. (1993). The Journal of Finance, 48(1), 65-91, Section VII 回測 1927–1940 期間（原文 PDF 逐字核對）

### ❓ [5] 動能崩潰是可部分預測的：它發生在市場大跌後、波動率高的「恐慌狀態」，且崩潰來自空方（輸家暴漲），而非多方下跌。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本 1927/01–2013/03。WML 組合月報酬偏態 -4.70（日 -1.18）。最差兩個月為 1932/07-08：市場 +82%、贏家十分位 +32%、輸家十分位 +232%。2009/03-05：市場 +26%、贏家 +8%、輸家 +163%。15 個最差月份中有 14 個發生在落後兩年市場報酬為負時，且全部發生在市場當月上漲時。兩大回撤期為 1932/06–1939/12 與 2009/03–2013/03。動態擇時版本使 alpha 與 Sharpe 約增為兩倍
- **適用邊界／何時會害人賠錢**：「可預測」是統計上的，不是即時可操作的。恐慌狀態的判定要用已實現波動率與落後兩年市場報酬，這些訊號在轉折點附近會頻繁誤報，且動態版本的兩倍 Sharpe 是樣本內最佳化的結果——作者自己是用同一段資料估計均值與變異數。2009 那次崩潰持續到 2013 年，長達四年；相信「崩潰後會反彈」而加碼的人會先陣亡。樣本止於 2013 年。
- **來源**：Daniel, K., & Moskowitz, T. J. (2016). Momentum crashes. Journal of Financial Economics, 122(2), 221-247. DOI 10.1016/j.jfineco.2016.08.006（Elsevier open access 原文 PDF 逐字核對）

### ❓ [6] 短期（一個月）反轉存在：極端十分位組合的月異常報酬差距在 1934–1987 年美國樣本中為 2.49%。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：1934–1987 期間極端十分位異常報酬差 2.49%/月；月報酬一階序列相關顯著為負；12 個月落後期序列相關顯著為正
- **適用邊界／何時會害人賠錢**：2.49%/月是換手率極高的策略，每月全部重組。買賣價差、市場衝擊與價格壓力會吞掉絕大部分——Jegadeesh & Titman (1991) 與 Lo & MacKinlay (1990) 都指出這類短期反轉利潤大半來自買賣價差跳動與流動性不足，而非真的錯價。散戶或中型資金照抄必虧。此數字為 1990 年前的市場結構（無電子交易、價差以 1/8 美元計）下的產物，現代價差已縮小一個量級，效應大概率已大幅衰減。
- **來源**：Jegadeesh, N. (1990). Evidence of Predictable Behavior of Security Returns. The Journal of Finance, 45(3), 881-898. DOI 10.1111/j.1540-6261.1990.tb05110.x

### ❓ [7] 長期（3–5 年）反轉存在：形成期後 36 個月，過去輸家組合的報酬比過去贏家高約 25%。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：形成期後 36 個月，輸家組合（35 檔）平均超越大盤 19.6%，贏家組合落後大盤約 5.0%，價差約 25%；使用 CRSP 月報酬資料；效應在 1 月特別集中
- **適用邊界／何時會害人賠錢**：19.6%/5.0% 的分解我是從次級來源取得，未親自核對原文表格，故信心降級。更關鍵的是：Jegadeesh & Titman (1993) 明白指出此結果可能被系統性風險與規模效應解釋，且輸家只在 1 月贏過贏家，這使「過度反應」的解讀站不住腳。輸家組合充滿瀕臨破產的小型股，倖存者偏誤與下市處理方式會大幅影響結果。3 年的持有期意味著你要忍受極長的錯誤期。
- **來源**：De Bondt, W. F. M., & Thaler, R. H. (1985). Does the Stock Market Overreact? The Journal of Finance, 40(3), 793-805. DOI 10.1111/j.1540-6261.1985.tb05004.x（書目經 RePEc 與 OpenAlex 雙重核對；卷期頁為 40(3), 793-805，非常見誤引的 793-808）

### ❓ [8] 反面證據：長期反轉（contrarian）策略在加拿大市場不成立，1950–1988 年多倫多交易所資料反而呈現顯著的「延續」而非「反轉」。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：樣本 1950–1988 多倫多證交所；發現贏家與輸家在後續 1 年（及 2 年）呈統計顯著的延續行為，反轉行為不顯著；結論對 1 月/非 1 月、規模分組、市場調整累積異常報酬與 Jensen、Sharpe 等多種績效衡量方式皆穩健
- **適用邊界／何時會害人賠錢**：這是對 De Bondt-Thaler 最直接的跨市場否證，且作者刻意用多種方法檢驗以排除方法論解釋。它的存在說明長期反轉極可能是美國樣本的特有現象或資料探勘產物。任何把「買落難股」當普世法則的人，應該先解釋為什麼隔壁一個制度相近、語言相通的成熟市場完全相反。加拿大市場高度集中於資源股，產業結構特殊，這既是它否證的力量也是它的限制。
- **來源**：Kryzanowski, L., & Zhang, H. (1992). The Contrarian Investment Strategy Does Not Work in Canadian Markets. Journal of Financial and Quantitative Analysis, 27(3), 383-395.（RePEc 書目與摘要核對）

### ❓ [9] 規模（SMB）與價值（HML）作為系統性風險因子的原始文獻是 Fama-French 三因子模型。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：提出五個共同風險因子：三個股市因子（市場、規模 SMB、淨值市價比 HML）與兩個債市因子（期限、違約風險）；股票報酬的橫斷面差異主要由 SMB 與 HML 捕捉
- **適用邊界／何時會害人賠錢**：這篇是「描述」而非「解釋」——它從未證明 SMB/HML 是風險補償而不是錯價或資料探勘。Fama-French 自己在 2015 年宣告 HML 在加入獲利與投資因子後變成冗餘（見下條），而 2012 年的國際研究發現規模溢酬在任何地區都不存在（見下條）。把三因子當成不變的世界法則，是把 1963–1991 美國樣本的迴歸結果誤當成物理定律。
- **來源**：Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. Journal of Financial Economics, 33(1), 3-56. DOI 10.1016/0304-405X(93)90023-5（Crossref 書目核對）

### ❓ [10] 反面證據：在 Fama-French 自己的五因子論文中，加入獲利（RMW）與投資（CMA）因子後，價值因子 HML 變成冗餘；且 GRS 檢定明確拒絕該五因子模型。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本 1963/07–2013/12，606 個月；模型解釋期望報酬橫斷面變異的 71%–94%，但 GRS 檢定「輕易拒絕」（easily rejects）該模型；HML 在五因子中對描述平均報酬變得冗餘（作者限定為「至少在 1963–2013 的美國資料」）；五因子迴歸平均 R² 在 5x5 分組為 0.91–0.93；最大失敗是無法解釋「低獲利但高投資」的小型股的低報酬
- **適用邊界／何時會害人賠錢**：作者自己在文中警告這個結果「可能是本樣本特有」（may be specific to this sample）。實務上這代表：如果你的價值策略在 2015 年後績效崩潰，學術上早已預告 HML 沒有獨立的資訊含量。同時 GRS 被拒絕代表模型定價錯誤在統計上確定存在，71%–94% 是「解釋不了 6%–29%」的另一種說法。此為美國資料，且樣本止於 2013 年，未涵蓋 2014–2026 這段成長股極端主導的時期。
- **來源**：Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. Journal of Financial Economics, 116(1), 1-22. DOI 10.1016/j.jfineco.2014.10.010（原文 PDF 逐字核對摘要與第 7、9 節）

### ❓ [11] 獲利能力因子的原始文獻顯示，毛利率對資產（gross profits-to-assets）預測橫斷面報酬的能力與淨值市價比大致相當。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：摘要原文：毛利率對資產「與淨值市價比有大致相同的預測能力」；高獲利公司的平均報酬顯著高於低獲利公司，儘管前者平均具有較低的淨值市價比與較高的市值
- **適用邊界／何時會害人賠錢**：未查得本篇具體的月報酬與 t 值數字（工作論文摘要未載明樣本期間與量化結果，原文 PDF 連結已失效）。關鍵陷阱是「毛利率」這個特定定義——用淨利、ROE、營業利益率替代會得到明顯不同甚至相反的結果，這正是 factor zoo 批評所指的研究者自由度。且此因子被發表後即被大量商品化，樣本外衰退風險見 McLean-Pontiff 條目。
- **來源**：Novy-Marx, R. (2013). The other side of value: The gross profitability premium. Journal of Financial Economics, 108(1), 1-28. DOI 10.1016/j.jfineco.2013.01.003（Crossref 書目核對；摘要經 NBER w15940 逐字核對）

### ❓ [12] 反面證據（最重要）：已發表的橫斷面預測變數，其報酬在樣本外下降 26%，在論文發表後下降 58%。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：研究 97 個已被證明能預測橫斷面股票報酬的變數；組合報酬在樣本外低 26%，在發表後低 58%；兩者之差 32% 被歸因於「因發表而知情的交易」（publication-informed trading）
- **適用邊界／何時會害人賠錢**：26% 是資料探勘效應的上界估計，58% 是你實際會拿到的縮水幅度。這條的殺傷力在於：你在券商或論文上看到的任何因子回測績效，預設就該打四折再評估。更糟的是這 58% 是平均值——有些因子完全消失。此研究本身樣本止於 2013 年前後，而 2013 年後量化投資規模又擴張數倍，衰退幅度只會更大不會更小。注意它衡量的是「下降」不是「歸零」，把它讀成「所有因子都沒用」同樣是錯的。
- **來源**：McLean, R. D., & Pontiff, J. (2016). Does Academic Research Destroy Stock Return Predictability? The Journal of Finance, 71(1), 5-32. DOI 10.1111/jofi.12365

### ❓ [13] 反面證據：因子文獻存在大規模多重檢定問題，作者主張新因子的 t 值門檻應提高到 3.0，並直言「金融經濟學中多數已宣稱的研究發現很可能是假的」。

- **證據等級**：規則 · 研究者信心：high
- **關鍵數字**：編目 316 個不同因子，來自 313 篇已發表著作與 63 篇工作論文；近九年新增 164 個因子，約為前此所有年份 84 個的兩倍，年發現率約 18 個；主張新因子需 t 值 > 3.0（而非慣用的 2.0）；作者明言 316 個「很可能低估了因子母體」
- **適用邊界／何時會害人賠錢**：t>3.0 是針對「新宣稱的因子」的門檻，不是對既有因子的追認標準；用它去回頭殺掉所有 t 在 2–3 之間的舊因子會過度嚴格。反過來，t>3.0 也擋不住「換個定義重跑一百次只報最好那次」這種研究者自由度——多重檢定校正只能處理你看得見的檢定次數，看不見的那些（作者自己承認無法觀測）才是真正的問題。這是方法論規則，不是可交易的訊號。
- **來源**：Harvey, C. R., Liu, Y., & Zhu, H. (2016). ... and the Cross-Section of Expected Returns. The Review of Financial Studies, 29(1), 5-68. DOI 10.1093/rfs/hhv059（NBER w20592 原文 PDF 逐字核對因子數與門檻）

### ❓ [14] 反面證據：對 452 個異常現象的大規模重製顯示，在抑制微型股後有 65% 連 t=1.96 的單一檢定門檻都過不了。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：資料庫含 452 個異常現象；以 NYSE 分界點與市值加權抑制微型股後，65% 無法通過 |t|=1.96；提高到 5% 顯著水準的多重檢定門檻 2.78 後失敗率升至 82%；交易摩擦類異常有 96% 失敗；即使成功重製者，其經濟量級也遠小於原始論文。（NBER 工作論文版為 447 個異常、64% 於 5% 水準不顯著、t=3 門檻下 85% 不顯著）
- **適用邊界／何時會害人賠錢**：這篇的方法論選擇本身有爭議：用 NYSE 分界點與市值加權會系統性壓低小型股異常，而部分異常本來就宣稱存在於小型股。批評者（如 Chen & Zimmermann）認為這高估了失敗率。但反過來說，若一個因子只在市值加權下消失，代表它只能靠微型股賺錢——那對任何有規模的資金而言本來就不可投資。這條該讀成「大部分異常無法承載真實資金」，而非「大部分異常不存在」。
- **來源**：Hou, K., Xue, C., & Zhang, L. (2020). Replicating Anomalies. The Review of Financial Studies, 33(5), 2019-2133. DOI 10.1093/rfs/hhy131（RePEc 摘要逐字核對；NBER w23394 工作論文版本數字略異）

### ❓ [15] 反面證據：動能在日本不存在。在 1990–2011 年四大區域研究中，日本的 WML 報酬接近零，而其他所有區域皆顯著為正。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本 1990/11–2011/03，245 個月，23 個已開發國家，四區域（北美、歐洲、日本、亞太除日本）。日本 WML 在大小型股皆接近零；其他區域 WML 從北美 0.64%/月（t=1.91）到歐洲 0.92%/月（t=3.38）；全球 WML 0.62%/月（t=2.30），小型股 0.82%（t=3.14）、大型股 0.41%（t=1.38）。日本股票風險溢酬本身為負 -0.12%/月
- **適用邊界／何時會害人賠錢**：必須誠實指出兩件事：第一，連北美的動能 t 值只有 1.91，在 5% 水準下並不顯著——這段期間美國動能也很弱。第二，Fama-French 自己做的 Hotelling T² 檢定「在 90% 水準下無法拒絕」各區域期望 WML 相同，他們明言「機率巧合是很有力的競爭解釋」（chance is a serious contender）。所以「日本動能失效」這件事本身的統計證據，比多數人引用時所暗示的要弱得多。20 年樣本對估計月報酬而言太短。
- **來源**：Fama, E. F., & French, K. R. (2012). Size, value, and momentum in international stock returns. Journal of Financial Economics, 105(3), 457-472. DOI 10.1016/j.jfineco.2012.05.011（原文 PDF 逐字核對摘要與第 4.1 節）

### ❓ [16] 反面證據：在 1990–2011 年的國際樣本中，四大區域沒有任何一個存在規模溢酬；北美的價值溢酬也不顯著。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：原文：「在我們的樣本期間，沒有任何一個區域存在規模溢酬」（There is no size premium in any region during our sample period），各區域平均 SMB 報酬皆接近零；HML 則從北美 0.33%/月（t=1.48，不顯著）到亞太 0.62%/月（t=3.04）
- **適用邊界／何時會害人賠錢**：這是 Fama-French 親手為自己 1993 年三因子模型中的 SMB 開的死亡證明（至少在 1990 年後的國際資料上）。任何以「小型股長期贏大型股」為前提的資產配置，都應該被要求說明它憑什麼認為 1990 年後消失的東西會回來。北美價值溢酬 t=1.48 同樣提醒：價值在這 20 年也沒有統計上站得住的溢酬。單一 20 年樣本期不足以宣告因子「已死」，但足以宣告「不能當作可靠的規劃假設」。
- **來源**：Fama, E. F., & French, K. R. (2012). Journal of Financial Economics, 105(3), 457-472, 第 4.1 節（原文 PDF 逐字核對）

### ❓ [17] 跨國動能強度與文化個人主義指數正相關，日本因個人主義排名低而動能不顯著。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：使用 Hofstede (2001) 個人主義指數；在月均至少 500 檔股票的國家中，日本單獨納入時動能不顯著；個人主義與成交量、波動率正相關，且與動能利潤幅度強烈相關；結論對是否納入動能較弱的東亞國家皆穩健
- **適用邊界／何時會害人賠錢**：未查得本篇各國動能報酬的具體數值與 t 值（內部附錄僅含變數定義，未含國別動能表）。更根本的問題是 Fama-French (2012) 對此因果解釋公開表示懷疑，指出論證方向可以反過來——低個人主義也可能因為股價對資訊反應遲緩而「產生」動能。用文化常數解釋跨國差異，無法被證偽也無法用來擇時：日本的個人主義指數不會下季度就改變，但日本的動能報酬會。
- **來源**：Chui, A. C. W., Titman, S., & Wei, K. C. J. (2010). Individualism and Momentum around the World. The Journal of Finance, 65(1), 361-392. DOI 10.1111/j.1540-6261.2009.01532.x

### ❓ [18] 反對「日本動能失效」的反駁：日本動能結果完全落在統計雜訊範圍內，且將價值與動能視為一個系統時，動能在日本是有效的。

- **證據等級**：實證 · 研究者信心：low
- **關鍵數字**：未查得具體數值（摘要為純論述，未載明報酬率與 t 值）。核心主張：因價值與動能強烈負相關，兩者必須作為一個系統研究；日本動能結果與「在各地以相近幅度有效」的假說在統計上完全一致，落在雜訊範圍內
- **適用邊界／何時會害人賠錢**：這是 AQR 創辦人為自家核心策略辯護的文章，發表於 Journal of Portfolio Management（實務型期刊，非頂級學術期刊，同儕審查強度較低），利益衝突明顯，應以此折價看待。它的邏輯也有循環風險：如果任何區域的失效都能用「統計雜訊」與「要看價值動能組合」化解，那這套說法就近乎不可證偽。不過 Fama-French 自己的 Hotelling T² 結果確實支持「無法拒絕各區域相同」，所以這個反駁在統計上並非空話。
- **來源**：Asness, C. (2011). Momentum in Japan: The Exception that Proves the Rule. The Journal of Portfolio Management, 37(4), 67-75. DOI 10.3905/jpm.2011.37.4.067（Crossref 書目與 OpenAlex 摘要核對）

### ❓ [19] 台灣股市長期被記載為動能現象的顯著例外；其成因是贏家/輸家組合換手率過高，而以「持續性」篩選後的動能策略才能產生顯著的中期利潤。

- **證據等級**：實證 · 研究者信心：low
- **關鍵數字**：未查得本篇具體報酬率、t 值與樣本期間（僅取得摘要）。摘要要點：台灣股市「被廣泛記載為動能現象的顯著例外」；贏家與輸家組合存在高換手率，因而削弱動能利潤；買進持續型贏家、放空持續型輸家的策略可產生顯著的中期報酬。相關前作 Chen, Chou & Hsieh (2017), European Financial Management, 24(5), 856-892 指出「超過 40% 的贏家與輸家會立即掉出各自分組」
- **適用邊界／何時會害人賠錢**：這是本清單中證據等級最低的一條：Pacific-Basin Finance Journal 屬區域型期刊而非頂級七大，且我只取得摘要、未核對表格數字，因此不知道「顯著中期利潤」的幅度與是否扣除成本。更該警惕的是方法論：「持續性」篩選本身就是在原始動能失效後加上的第二層條件——這正是 Harvey-Liu-Zhu 所批評的研究者自由度典型形態，樣本外極可能不成立。台股散戶佔比高、當沖比重大、有漲跌幅限制與處置股制度，這些制度特徵會直接扭曲動能與反轉的測量。在台股照抄美式動能策略，先驗上就該預期失敗。
- **來源**：Chen, H.-Y., Hsieh, C.-H., & Lee, C.-F. (2023). Revisiting the momentum effect in Taiwan: The role of persistency. Pacific-Basin Finance Journal, 78, 101943. DOI 10.1016/j.pacfin.2023.101943（Crossref 書目與 OpenAlex 摘要核對）

---

## 總體經濟指標對股市與衰退的預測力：實證證據與失效案例（含反面證據）

> ❓ **本主題的對抗式查證未完成。**
> 以下主張尚未經獨立查證，**不可當作結論使用**。
> 已查證主題的錯誤率約 39%，故未查證內容的可靠度應假定同等偏低。

### ❓ [1] 在 1968–2005 年的樣本裡，10 年期減 3 個月期美債利差以「月平均」為準的倒掛，對美國 NBER 衰退零假訊號，六次衰退前全部倒掛。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：論文原文：「when inversion on a monthly average basis is used as an indicator, there have been no false signals over this period」（1968-01 至 2005-12）。probit 以 1959-01～2005-12 估計，每次衰退前機率均超過 30%，1981-82 衰退前最高達 98%。以日資料看，1968-01-01 至 2005-12-31 間有 100 個交易日利差為負、但當月月均並未轉負（即日內／日資料會給假訊號）。
- **適用邊界／何時會害人賠錢**：這條「零假訊號」的紀錄本身就是後見之明的樣本內宣告，而且它在論文發表 16 年後被打破（見 2022–2024 案例）。作者自己在結論寫「the evidence of the yield curve's predictive power is statistical and ... it is impossible to guarantee future results」。用它做資產配置最危險的地方是：訊號是二元的（倒不倒掛），但市場報酬不是——1968 以來六次衰退前的倒掛到衰退起點之間，股市可以再漲一年以上。以倒掛為由空手，最可能的賠錢方式是踏空這段。
- **來源**：Estrella, Arturo, and Mary R. Trubin (2006), "The Yield Curve as a Leading Indicator: Some Practical Issues," Federal Reserve Bank of New York, Current Issues in Economics and Finance, Vol. 12, No. 5 (July/August). 全文取自 https://msuweb.montclair.edu/~lebelp/EstrellaYieldCurveIndicatorFRBNY200608.pdf

### ❓ [2] 倒掛的「深度」與「持續月數」在各次衰退之間差異極大，不能用來推衰退的時點或嚴重度。

- **證據等級**：數據 · 研究者信心：high
- **關鍵數字**：衰退前 12 個月內 10y-3m 月均利差的最低值：1970 衰退 -0.51（10 個月為負）；1973-75 -1.59（6 個月）；1980 -2.20（12 個月）；1981-82 -3.51（10 個月）；1990-91 -0.08（3 個月）；2001 -0.70（7 個月）。1990-91 那次另註：1989-06 利差為 -0.16，落在衰退開始前 14 個月。
- **適用邊界／何時會害人賠錢**：最淺的一次是 -0.08，最深的一次是 -3.51，相差 44 倍；月數 3 到 12 個月。任何「倒掛超過 X 基點／持續 X 個月才算數」的交易規則都是曲線擬合，樣本只有 6 個觀測值。真正會害人賠錢的用法：看到 -0.08 就說「太淺不算數」——1990-91 那次就是 -0.08。
- **來源**：Estrella & Trubin (2006), FRBNY Current Issues 12(5), Table "Magnitude of Term Spread Signals Twelve Months before Each Recession since 1968".

### ❓ [3] 殖利率曲線斜率在超過一季的預測期間，是單一財務變數中樣本外表現最好的衰退預測指標，而且單獨使用通常比與其他變數合用還好。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：未查得具體數值。MIT Press 頁面與多方引用一致指出「beyond one quarter, the slope of the yield curve emerges as the clear individual choice and typically performs better by itself out of sample than in conjunction with other variables」。坊間廣泛流傳的「領先 6～24 個月」說法，我未能從論文原文直接驗證（MIT Press 與 SSRN 皆封鎖抓取）。
- **適用邊界／何時會害人賠錢**：論文樣本止於 1990 年代中期，之後三十年是「零利率＋QE＋期限溢酬崩塌」的新環境，原始係數不必然可外推。更重要的是：這篇的結論是「相對其他財務變數最好」，不是「絕對準確」——在一個所有指標都不太行的比賽裡拿第一，不代表可以拿來壓身家。引用時把「6-24 個月領先」講得像論文原文，是常見的二手誤傳。
- **來源**：Estrella, Arturo, and Frederic S. Mishkin (1998), "Predicting U.S. Recessions: Financial Variables as Leading Indicators," The Review of Economics and Statistics, Vol. 80, No. 1, pp. 45–61. https://direct.mit.edu/rest/article/80/1/45/57058/

### ❓ [4] 2022–2024 年的殖利率曲線倒掛是一次明確的失效案例：倒掛時間創紀錄、模型機率破 70%，但截至 2026-08-10 NBER 從未認定衰退。

- **證據等級**：歷史 · 研究者信心：medium
- **關鍵數字**：已驗證：NBER 自 2020-04 谷底以來未宣告新的高峰，美國經濟至 2026 年仍在擴張（2026 Q1 實質 GDP 年化 +2.1%，2025 Q4 +0.5%；失業率 2025 年由 4.1% 升至 4.4%）。未直接驗證（僅二手）：2022-07 至 2024-08 的 10y-2y 倒掛約 26 個月、最深約 -108bp；NY Fed 一年期衰退機率 2023-05 達 70.85%，為 1982-04 以來最高。
- **適用邊界／何時會害人賠錢**：這條的殺傷力在於：任何 2022–2023 年根據倒掛減碼美股的人，錯過了之後兩年多的多頭。反過來說，也不能因此宣告「倒掛已死」——樣本數只有一次，且 NBER 認定有 1 年以上落後，理論上仍可能事後補認定（機率低但非零）。二手數字（26 個月、-108bp、70.85%）我未能從 NY Fed／FRED 原始檔驗證，因這些站點封鎖自動抓取，引用時請自行覆核。
- **來源**：NBER Business Cycle Dating Committee, US Business Cycle Expansions and Contractions（https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions ；截至 2026 年無新的景氣循環高峰宣告，最近一次宣告為 2020-02 高峰／2020-04 谷底）。倒掛期間與模型機率細節取自二手報導：eco3min.fr, "Yield Curve Inversion History: Recession Signals & 2s10s Since 1976"；centralbank.watch / MacroMicro 對 NY Fed 模型的報導。

### ❓ [5] 純期限利差的 probit 模型在 1995 與 1998 年都給出接近五五波的衰退機率，但兩次都沒有衰退；加入聯邦資金利率水準後的模型才沒有誤報。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：Model A（僅期限利差）「predicted nearly even odds of a recession in 1995 and 1998, but no recession occurred」。預測期間測 2、4、6 季。LM 參數穩定性檢定在 1964–2005 未發現顯著結構斷裂，但作者自承「tests might fail to detect even quite notable parameter instability」因為衰退觀測值太少。
- **適用邊界／何時會害人賠錢**：這篇正好證明「零假訊號」的說法取決於你怎麼定義訊號：用月均倒掛當二元訊號沒假訊號，用 probit 機率當連續訊號就有兩次接近 50% 的誤報。實務上你交易的是機率，不是二元訊號。另外，Wright 的解方（加入聯邦資金利率水準）在 2020-2021 零利率環境下本身就失去鑑別力。
- **來源**：Wright, Jonathan H. (2006), "The Yield Curve and Predicting Recessions," Board of Governors of the Federal Reserve System, Finance and Economics Discussion Series No. 2006-07, February. https://www.federalreserve.gov/pubs/feds/2006/200607/index.html

### ❓ [6] 舊金山聯準銀行 2022 年 5 月用其偏好的 10y-3m 模型算出未來 12 個月衰退機率僅約 4%，是 2017 年初以來最低——兩個月後該利差就開始倒掛。這是即時（real-time）預測失效的實例。

- **證據等級**：歷史 · 研究者信心：high
- **關鍵數字**：10y-2y 模型：約 17% 一年內衰退機率；10y-3m 模型（作者偏好）：約 4%，「the lowest level since early 2017」。臨界門檻：10y-2y 為 22%、10y-3m 為 32%。文中並稱「prior to all 10 U.S. recessions since 1955, the Treasury yield curve inverted」。2019 年兩個利差都倒掛時，模型機率落在 20–40%。
- **適用邊界／何時會害人賠錢**：這條是雙面刃的完美教材：同一批作者、同一個模型，2022 年 5 月說風險極低（結果兩個月後倒掛），2023 年模型狂噴高機率（結果沒衰退）。兩次都錯，方向相反。啟示是：以「當下利差水準」外推 12 個月的模型，在利率快速變動的環境下幾乎沒有資訊價值，因為它的輸入本身就是 12 個月內會劇烈改變的東西。
- **來源**：Bauer, Michael D., and Thomas M. Mertens (2022), "Current Recession Risk According to the Yield Curve," FRBSF Economic Letter 2022-11, May 9, 2022. https://www.frbsf.org/research-and-insights/publications/economic-letter/2022/05/current-recession-risk-according-to-yield-curve/

### ❓ [7] 過去六次衰退前 10y-3m 利差都收窄，但其中只有五次真正倒掛；且期限溢酬長期下滑意味著相同的衰退機率現在會對應更平（而非更倒）的曲線。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：「the ten-year minus three-month term spread narrowed prior to each of the six most recent recessions」但「the yield curve was inverted according to this measure prior to five of those recessions」。期限溢酬由 1980 年代初約 4% 降至 2018 年接近零。2018 Q1 單變數 probit 給出約 30% 一年期衰退機率，遠低於歷次衰退前的 60%+。加入殖利率曲線其他資訊或 excess bond premium 後，預測機率大幅降低。
- **適用邊界／何時會害人賠錢**：直接和 Estrella-Trubin「六次全倒」矛盾——差別在利差定義（月均 vs 其他）與衰退期間認定慣例。這代表「歷史命中率 100%」這種說法對定義極度敏感，任何人報給你 100% 命中率而不講清楚定義，就是在賣故事。另外：期限溢酬歸零這件事同時也意味著「零門檻倒掛」的訊號閾值已經失準，但沒人知道新閾值該是多少。
- **來源**：Johansson, Peter, and Andrew Meldrum (2018), "Predicting Recession Probabilities Using the Slope of the Yield Curve," FEDS Notes, Board of Governors of the Federal Reserve System, March 1, 2018. https://www.federalreserve.gov/econres/notes/feds-notes/predicting-recession-probabilities-using-the-slope-of-the-yield-curve-20180301.html

### ❓ [8] 股票報酬與「預期」通膨呈負相關——股票不是通膨的好對沖工具，這與教科書直覺相反。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：未查得具體回歸係數（ScienceDirect 與備份 PDF 皆無法取得可讀全文）。已驗證的定性結論：普通股報酬與通膨的預期成分呈負相關，可能與非預期成分也呈負相關；同期美國公債與國庫券是預期通膨的完全對沖，民間住宅不動產則同時對沖預期與非預期通膨。主要分析期間 1953–1971。
- **適用邊界／何時會害人賠錢**：樣本只有 1953–1971（19 年、一個通膨體制），而且是布列敦森林體系下的美國。Boudoukh & Richardson 之後主張在 5 年以上的長期，名目股票報酬確實會隨通膨上升，所以「股票不抗通膨」在短中期成立、長期未必。最會害人賠錢的誤用：把它讀成「通膨升就該賣股」——2022 年這樣做對，1970 年代末到 1982 年這樣做也對，但 2021 年這樣做會踏空一整年。
- **來源**：Fama, Eugene F., and G. William Schwert (1977), "Asset Returns and Inflation," Journal of Financial Economics, Vol. 5, No. 2 (November), pp. 115–146. https://www.sciencedirect.com/science/article/abs/pii/0304405X77900149

### ❓ [9] 「股票是實質資產所以抗通膨」的直覺，在過去一個世紀相當長的時間裡嚴重失效；通膨對股票的影響取決於它來自需求面（好通膨）還是供給面（壞通膨）。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：原文：「For investors in financial claims such as stocks that derive their value from real assets, intuition might instead suggest that inflation poses no tangible threat. Unfortunately, this intuition has badly failed over a significant part of the past century.」1970-80 年代高且持續的通膨伴隨股市估值被壓抑到 1930 年代大蕭條以來未見的水準。股債報酬相關性在 21 世紀初由負轉正（Panel B）。論文以新凱因斯模型區分需求衝擊（好通膨）與供給衝擊（壞通膨）。
- **適用邊界／何時會害人賠錢**：這是回顧型論文（review），提供的是機制與敘事框架，不是可直接交易的參數。「好通膨／壞通膨」的分類在事後很清楚、在事前極難即時判斷——2021 年供給鏈瓶頸 vs 需求過熱的爭論持續了一整年，聯準會自己也判斷錯。用這套框架做即時決策，等於把一個難題換成另一個難題。
- **來源**：Cieslak, Anna, and Carolin Pflueger (2023), "Inflation and Asset Returns," Becker Friedman Institute Working Paper No. 2023-34, March 2023. https://bfi.uchicago.edu/wp-content/uploads/2023/03/BFI_WP_2023-34.pdf

### ❓ [10] 2022 年是「高通膨＋股票實質報酬大幅為負」的當代實例：CPI 年增率 6 月見頂 9.1%、12 月 6.5%，同年 S&P 500 總報酬約 -18%，實質報酬約 -23%。

- **證據等級**：數據 · 研究者信心：medium
- **關鍵數字**：2022 CPI 年增率：1 月 7.5%、6 月 9.1%（峰值）、12 月 6.5%，全年平均 8.0%（2021 年平均 4.7%）。Damodaran 序列的 S&P 500 年度報酬：2022 -18.04%、1973 -14.31%、1974 -25.90%、1977 -6.98%、1981 -4.70%、2008 -36.55%。實質報酬 = (1-0.1804)/(1+0.065)-1 ≈ -23.0%（本人以上述兩個已驗證數字計算，非論文原載）。
- **適用邊界／何時會害人賠錢**：單一年度、單一國家，n=1，不能當通則。而且 2022 年股債同跌的主因很難跟「聯準會史上最快升息」切開——把它全歸因於通膨本身是過度歸因。另外 Damodaran 的年度報酬序列與 S&P 官方總報酬序列有小幅差異（一般引用的 2022 為 -18.11%、1974 為 -26.47%），差異來自資料商與計算慣例；要求精確到小數點時務必註明用哪一個序列。
- **來源**：CPI：U.S. Bureau of Labor Statistics（All items, U.S. city average, all urban consumers, NSA），經 usinflationcalculator.com/inflation/current-inflation-rates/ 彙整。S&P 500 年度總報酬：Aswath Damodaran, "Annual Returns on Stock, T.Bonds and T.Bills: 1928–Current", NYU Stern，https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html （頁面更新日 2026-01-05）。

### ❓ [11] 非預期的聯邦資金利率意外降息 25 個基點，平均伴隨廣泛股價指數當日上漲約 1%。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：以聯邦資金期貨拆解出的「意外」成分回歸 CRSP 市值加權報酬：每 1 個百分點的意外降息對應當日 +4.68% 報酬（係數 -4.68，高度顯著）。R² = 0.17，即事件日股價變異的 17% 與貨幣政策消息有關。樣本：1989 年 6 月首次事件至 2002 年 12 月 FOMC 會議，共 131 個觀測值（2001-09-17 排除）。原始利率變動（未拆解預期／非預期）的係數雖為負但小且不顯著。
- **適用邊界／何時會害人賠錢**：事件研究測的是「當日」反應，不是「未來報酬」。把 -4.68 拿來做降息循環的部位配置是嚴重誤用：降息通常伴隨經濟惡化，2001 與 2007-08 都是邊降息邊崩盤。此外樣本止於 2002 年，之後有 ZIRP、前瞻指引、QE，政策「意外」的度量方式（單看目標利率期貨）在 2009-2015 期間幾乎無效。
- **來源**：Bernanke, Ben S., and Kenneth N. Kuttner (2005), "What Explains the Stock Market's Reaction to Federal Reserve Policy?", The Journal of Finance, Vol. 60, No. 3, pp. 1221–1257. 工作論文版：NBER Working Paper No. 10402, March 2004, https://www.nber.org/papers/w10402

### ❓ [12] 反面證據：Bernanke-Kuttner 的頭條估計極度脆弱——剔除 131 個觀測值中影響力最大的 6 個之後，係數從 -4.68 掉到 -2.55，R² 從 0.17 掉到 0.05。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：剔除的 6 個高影響力觀測值：1991-08-08（作者文中另提 1991-08-21 俄羅斯政變落幕）、1992-07-02、1998-10-15、2001-01-03、2001-03-20、2001-04-18。其中 2001-01-03 與 2001-04-18 的意外 50bp 降息當日分別大漲 5.3% 與 4.0%；2001-03-20 的 50bp 降息因市場期待 75bp 反而下跌逾 2%；1998-10-15 的意外 25bp 降息推升股市逾 4%。剔除後 R² 由 0.17 降至 0.05。
- **適用邊界／何時會害人賠錢**：這是本清單裡最重要的一條方法論警訊：一個被引用上萬次的「每 25bp 約 1%」定律，有將近一半來自 131 個觀測值中的 6 個。也就是說，這條關係在「平常的 FOMC 日」幾乎不存在，只在極端政策意外時才強烈——而極端政策意外恰恰是最難事前預測的。把它當作日常倉位規則會系統性高估貨幣政策對股價的可預測影響。作者自己也點出 1992-07-02 的降息其實是對當日糟糕就業數據的內生反應，內生性問題並未完全解決。
- **來源**：Bernanke & Kuttner (2005), Journal of Finance 60(3): 1221–1257，Table 2 columns (c)(d)；NBER WP 10402 第 9–12 頁。

### ❓ [13] 反面證據：後續研究推翻了 Bernanke-Kuttner 的機制解釋——FOMC 日股價對政策意外的反應，主要來自無風險殖利率曲線的變動，而非股權風險溢酬的變動。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：未查得具體分解比例（摘要僅稱 "explained mostly by changes in the default-free term structure of yields, not by changes in the equity premium"）。方法：使用股利期貨價格建構「純粹由無風險殖利率曲線變動造成」的股價反事實變化，此資料在 2005 年時尚不存在。並指出 FOMC 雙週循環的股市報酬型態也主要來自殖利率曲線循環，而非股權溢酬循環。
- **適用邊界／何時會害人賠錢**：這是 2024 年的工作論文，截至查證時我未確認是否已在頂級期刊發表，尚未經完整同儕審查。股利期貨資料只回溯到約 2000 年代中期，因此新方法能覆蓋的樣本遠短於 Bernanke-Kuttner 原始樣本，兩者不是在同一段歷史上對決。實務意涵：如果反應主要來自折現率而非風險溢酬，那麼「降息利多股市」的邏輯高度依賴長端殖利率是否跟著下降——2022-2023 年短端降息預期升高而長端不降的情境下，這個傳導就會斷掉。
- **來源**：Nagel, Stefan, and Zhengyang Xu (2024), "Movements in Yields, not the Equity Premium: Bernanke-Kuttner Redux," NBER Working Paper No. 32884, August 2024. https://www.nber.org/papers/w32884

### ❓ [14] 反面證據（最重要的一條）：文獻上所有主流的股市報酬預測變數，在真實可用資訊條件下的樣本外檢定中，沒有一個能贏過「就用歷史平均報酬」這個笨方法。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：NBER 工作論文版原文：年頻的 51 個預測回歸中，46 個在 RMSE 準則上輸給「當時為止的歷史平均」。少數贏的例外「none reaches good economic significance, i.e., surpassing even very modest transaction costs. (The average annual outperformance is 12 basis points.)」測試變數包含股利價格比、股利殖利率、盈餘價格比、股利發放率、淨發行比率、淨值市價比、各式利率（短期利率、期限利差、違約利差、通膨率）、cay。資料：S&P 500 月資料 1871–2003（1871-1926 取自 Shiller，1926-2003 取自 CRSP）。
- **適用邊界／何時會害人賠錢**：這條直接否定了本清單中大多數「指標有預測力」主張的實務價值。注意作者的限定：本文只談總體市場擇時，不談橫斷面選股，也不談「若已知參數」的模型。反過來說，這篇也不代表「一切都不可預測」——它證明的是「用滾動樣本估參數的實時投資人賺不到」。最會害人賠錢的誤讀：把某個指標的樣本內 t 值 3.0 當成可交易訊號。
- **來源**：Welch, Ivo, and Amit Goyal (2008), "A Comprehensive Look at the Empirical Performance of Equity Premium Prediction," The Review of Financial Studies, Vol. 21, No. 4, pp. 1455–1508. 工作論文版：NBER Working Paper No. 10483, May 2004, https://www.nber.org/system/files/working_papers/w10483/w10483.pdf

### ❓ [15] 反面證據：Goyal-Welch 批評在 2024 年被更新到 2021 年底，結果更慘——2008 年之後新發表的預測變數，超過三分之一連樣本內顯著性都消失了。

- **證據等級**：實證 · 研究者信心：medium
- **關鍵數字**：重新檢驗 2008 年之後 26 篇論文提出的 29 個新變數，加上原始的 17 個變數，資料截至 2021 年底。結果：超過三分之一的新變數在樣本內已不具統計顯著性；在仍顯著的變數中，約一半的樣本外表現不佳；只有少數變數在樣本內外都還算可以。
- **適用邊界／何時會害人賠錢**：這是典型的發表偏誤（publication bias）／樣本外衰退證據：學術論文發表之後，其宣稱的效應平均會大幅縮水。對操作的意涵很直接——任何你在論文或賣方報告看到的「新指標」，預設它在你開始用的當下已經比論文報告的弱一半以上。我未能取得該文全文（Oxford Academic 封鎖抓取），上述比例來自出版社摘要頁與多方一致引用，未逐項核對。
- **來源**：Goyal, Amit, Ivo Welch, and Athanasse Zafirov (2024), "A Comprehensive 2022 Look at the Empirical Performance of Equity Premium Prediction," The Review of Financial Studies, Vol. 37, No. 11 (November), pp. 3490–3557. https://academic.oup.com/rfs/article/37/11/3490/7749383

### ❓ [16] CAPE（席勒本益比）對未來十年實質報酬確實有可觀的樣本內解釋力（R²≈40%），但對一年期報酬幾乎沒有解釋力（R²<1%）。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：美國年度資料 1872–2000。價格／十年平均實質盈餘比（即 CAPE）預測未來十年實質股價成長 R²=30%；預測未來十年實質總報酬 R²=40%。股利價格比對應數字：十年股價成長 R²=9%、十年總報酬 R²=16%；一年期股價變動 R²「less than 1%」。CAPE 歷史均值 16.0，2000 年 1 月創紀錄 44.9（前高為 1929 年的 28.0）。傳統（未平滑）本益比歷史區間約 8–20、均值 14.5，2000 年 1 月為 29.6。
- **適用邊界／何時會害人賠錢**：三個致命限制。第一，十年期迴歸用的是重疊樣本，1872–2000 只有約 13 個不重疊的十年，統計自由度遠低於 R² 給人的印象（作者自承股利價格比那張圖只有 29 個不重疊區間）。第二，這是樣本內 R²，Welch-Goyal 已證明樣本外會崩。第三，CAPE 自 1990 年代起長期高於歷史均值卻沒有均值回歸，用「CAPE 高就減碼」的人已經連續錯了三十年。這條最會害人的用法：把 40% 的十年 R² 當成擇時依據——它對「未來十二個月該不該持股」的資訊量接近零。
- **來源**：Campbell, John Y., and Robert J. Shiller (2001), "Valuation Ratios and the Long-Run Stock Market Outlook: An Update," NBER Working Paper No. 8221, April 2001. https://www.nber.org/system/files/working_papers/w8221/w8221.pdf （原始版本：Campbell & Shiller, Journal of Portfolio Management, 1998）

### ❓ [17] 反面證據：Campbell 與 Shiller 自己在 2001 年就明白寫下，當估值比率遠超歷史區間時線性迴歸不可信；而他們 1996 年底作證看空之後，實質 S&P 指數又漲了 80%。

- **證據等級**：歷史 · 研究者信心：high
- **關鍵數字**：原文：自 1996-12-03 向聯準會理事會作證起算，到 2001 年初，實質（經通膨調整）S&P 綜合指數上漲 80%；自 1998 年論文發表起算上漲 30%。他們以 2000 年 1 月股利價格比 1.2%（歷史均值 4.65%、歷史最低區間 3.4% 以下）推出的預測：十年期連續複利實質總報酬 -44%；十年實質股價下跌 55%；以「回到均值時」為期間的迴歸則隱含市場將失去四分之三以上的實質價值。對 CAPE 44.9 的外推，作者自評「We do not find this extreme forecast credible; when the independent variable has moved so far from the historically observed range, we cannot trust a linear regression line.」
- **適用邊界／何時會害人賠錢**：這是「邏輯對、時機錯」的教科書案例：他們方向猜對（2000-2010 確實是失落的十年），但（一）在被證明對之前先錯了超過三年、實質指數再漲 80%，任何真金白銀照做的人早已被迫平倉；（二）預測的幅度（-44% 到 -75%）明顯過度外推。啟示：估值是「未來十年期望報酬的估計」，不是「進出場訊號」。今天任何以 CAPE 高為由清空部位的人，應該先問自己能不能忍受連續三年再漲 80%。
- **來源**：Campbell & Shiller (2001), NBER Working Paper No. 8221, pp. 2, 10.

### ❓ [18] 由個別公司債微觀資料建構的 GZ 信用利差，對未來經濟活動的預測力顯著優於傳統的 Baa-Aaa 利差與商業本票-國庫券利差；而且預測力主要來自「超額債券溢酬」而非預期違約。

- **證據等級**：實證 · 研究者信心：high
- **關鍵數字**：樣本：1973:M1–2010:M9，5,982 檔優先無擔保公司債、1,112 家非金融公司、346,126 個債券-月觀測值；平均信用利差 204bp（標準差 281bp），中位數 118bp。3 個月期預測的標準化係數（絕對值愈大愈強）：GZ 利差對民間就業 -0.322 [t=8.50]、失業率 +0.351 [t=19.5]、工業生產 -0.386 [t=5.28]；相對之下 Baa-Aaa 利差分別為 -0.075 [2.05]、+0.198 [10.4]、-0.211 [3.08]，商業本票-國庫券利差為 -0.165、+0.268、-0.332。基準模型（期限利差＋實質聯邦資金利率）中期限利差本身在兩個預測期間對三個指標都顯著。
- **適用邊界／何時會害人賠錢**：報告的是樣本內配適（adjusted R²）與標準化係數，不是樣本外檢定——Welch-Goyal 的批評同樣適用。GZ 利差需要 Compustat/CRSP 配對與逐檔債券定價，一般投資人無法即時複製；FRB 公布的更新版有數週延遲。最關鍵的邊界：2008-09 危機在樣本內，而該次危機本身就是信用市場事件，用它證明「信用利差預測衰退」有循環論證的味道。2011-2019 這段低波動期間該指標幾乎沒發出過有用訊號。
- **來源**：Gilchrist, Simon, and Egon Zakrajšek (2012), "Credit Spreads and Business Cycle Fluctuations," American Economic Review, Vol. 102, No. 4 (June), pp. 1692–1720. 工作論文版：NBER Working Paper No. 17021, May 2011, https://www.nber.org/papers/w17021

### ❓ [19] Sahm rule 的原始設計是財政刺激的自動觸發器，不是衰退「預測」指標——歷史上它是在衰退開始後 0 到 4 個月才觸發的。

- **證據等級**：規則 · 研究者信心：high
- **關鍵數字**：觸發定義（原文）：「Automatic lump-sum stimulus payments would be made to individuals when the three-month average national unemployment rate rises by at least 0.50 percentage points relative to its low in the previous 12 months.」該書 Figure 3 顯示歷次觸發時點相對衰退起點的落後月數，六個標示點為 1974-03、1980-04、1981-11、1990-11、2001-06、2008-04，落後 0 至約 4 個月。作者原文並稱「by this rule the stimulus payments would have been triggered only in recessions」。
- **適用邊界／何時會害人賠錢**：這是被市場最嚴重誤用的指標。它是同時／落後指標，不是領先指標——當它觸發時，衰退（若真發生）通常已經開始好幾個月，股市多半已經跌過一輪。作者本人在原文就寫明失業率「tends to lag the business cycle」且「gives little advance warning of recessions」。任何拿 Sahm rule 當賣出訊號的策略，本質上是在事件發生後才行動。另一個作者自己點出的限制：衰退前的失業率上升幅度完全無法預測衰退的嚴重度（2001 與 2008-09 的前期升幅相近，但後續差了一倍以上）。
- **來源**：Sahm, Claudia (2019), "Direct Stimulus Payments to Individuals," in Recession Ready: Fiscal Policies to Stabilize the American Economy, The Hamilton Project / Brookings Institution, pp. 67–92. https://www.brookings.edu/wp-content/uploads/2019/05/ES_THP_Sahm_web_20190506.pdf

### ❓ [20] 反面證據：Sahm rule 於 2024 年 7 月就業報告觸發（值 0.53、失業率 4.3%），但截至 2026-08-10 沒有衰退；規則命名者本人在觸發當下就公開表示「這次真的可能不一樣」。

- **證據等級**：歷史 · 研究者信心：high
- **關鍵數字**：2024 年 7 月：Sahm rule 讀數 0.53（6 月為 0.43），觸發門檻 0.50；失業率由 6 月 4.1% 升至 7 月 4.3%。Sahm 原話：「I am not concerned that, at this moment, we are in a recession」、「This time really could be different. [The Sahm Rule] may not tell us what it's told us in the past, because of these swings from labor shortages, with people dropping out of the labor force, to now having immigrants coming lately.」、「the volume is probably turned up a little too loud」。事後：美國 2025 年失業率由 4.1% 升至 4.4%，2026 Q1 實質 GDP 年化成長 2.1%，NBER 未認定衰退。
- **適用邊界／何時會害人賠錢**：失效機制很明確：Sahm rule 假設失業率上升來自「解僱」（需求面），但 2023-2024 的上升主要來自勞動供給增加（勞參率回升＋移民流入），分子分母的經濟意義完全不同。這條的普遍教訓最狠：所有以失業率、勞參率為輸入的規則，在移民政策或勞參結構劇烈變動時全部失效，而你通常要事後兩年才確定當時屬於哪一種。順帶注意：規則設計者當下就公開說別亂用，市場仍然照用不誤——這是訊號傳播比訊號本身更容易出錯的例子。
- **來源**：Daniel, Will, Fortune, 2024-08-02, "Recession indicator Claudia Sahm rule trigger unemployment rate jobs report," https://fortune.com/2024/08/02/recession-indicator-claudia-sahm-rule-trigger-unemployment-rate-jobs-report ；衰退未發生之佐證：NBER Business Cycle Dating Committee 至 2026 年未宣告新高峰，https://www.nber.org/research/business-cycle-dating

### ❓ [21] 股利比率（股利價格比、股利殖利率）對股權風險溢酬的預測力，在樣本外檢定下站不住腳，這個結論早於 2008 年那篇綜合檢視就已提出。

- **證據等級**：實證 · 研究者信心：low
- **關鍵數字**：未查得具體樣本外 R² 數值（INFORMS 與 JSTOR 均封鎖抓取）。已驗證的定性結論：採用樣本外檢定時，股利比率的預測力證據受到嚴重質疑。該文是 Welch & Goyal (2008) RFS 綜合檢視的前身，方法論相同：僅使用預測時點之前可得的資料做滾動迴歸，與「當時為止的歷史平均」對比。
- **適用邊界／何時會害人賠錢**：我只驗證到書目與定性結論，未取得原文數字，請勿引用任何具體 R²。這條與 Campbell-Shiller 的 CAPE 結論表面衝突，實際上是兩種檢定的差別：樣本內長期迴歸看起來很強，樣本外實時預測就垮掉。實務上該相信哪一邊？相信你自己能不能在 1996 年、在不知道未來的情況下，靠這個訊號活過接下來的四年。
- **來源**：Goyal, Amit, and Ivo Welch (2003), "Predicting the Equity Premium with Dividend Ratios," Management Science, Vol. 49, No. 5 (May), pp. 639–654. https://pubsonline.informs.org/doi/abs/10.1287/mnsc.49.5.639.15149

---

