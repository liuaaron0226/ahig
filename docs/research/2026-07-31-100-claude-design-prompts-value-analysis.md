# 《100 Claude Design Prompts》實際利用價值分析

- **來源檔案**：`D:\UserData\Downloads\100-Claude-Design-Prompts.pdf`
- **研究日期**：2026-07-31
- **閱讀範圍**：完整 12 頁；不是抽樣。PDF 第 1 頁為封面與使用說明，第 2–11 頁各有 10 個提示詞，共 100 個，第 12 頁為結語與作者宣傳。
- **目標讀者**：沒有設計背景、近期要做網站、海報、產品封面照／產品攝影的人。
- **評估方式**：以「能不能幫初學者做出可執行的設計簡報、可交付的版面規格、可用的圖片生成提示，以及可檢查的成品」為標準，不以提示詞數量本身評分。

## 一、先講結論：有用，但不是「複製貼上就會得到成品」

這份 PDF 最有價值的地方，不是提供 100 個魔法咒語，而是把設計工作拆成幾種常見思考框架：**定位、層級、版式、攝影條件、跨尺寸適配、批評、測試與檢查**。其中產品海報、UI／UX、Landing Page、包裝與創意簡報等章節，確實能幫沒有設計背景的人補上「不知道該要求什麼」的缺口。（PDF p. 4、6–8、11）

但它大多是讓 Claude **產生設計方向、文字規格或下一階段的圖片提示詞**，不是直接生成可上線網站、可印刷海報或忠實產品照片。像「give me an exact image-generation prompt」其實仍是「叫 Claude 幫你再寫一層提示詞」；最終效果仍取決於你使用的圖片工具、參考圖、品牌素材與尺寸限制。（PDF p. 3–6、8、10）

### 綜合評分

| 面向 | 評分 | 判斷 |
|---|---:|---|
| 靈感與方向探索 | 8/10 | 很會迫使模型提出多個方向、比較安全與大膽方案，適合破除空白頁焦慮。（PDF p. 4、11） |
| 設計需求簡報 | 8/10 | 多個提示詞要求層級、受眾、媒介、理由與限制，比單純「做漂亮一點」有效很多。（PDF p. 4、6–8、11） |
| 網站規劃 | 8/10 | UI／UX 與 Landing Page 兩章可直接當網站規劃問題清單，但通常不會直接產出完整、可維護的網站。（PDF p. 7–8） |
| 海報規劃 | 8/10 | 視覺隱喻、標題長度、比例轉版與測試變因都很實用。（PDF p. 4） |
| 產品封面／產品攝影 | 7/10 | 攝影角度、光線、表面與道具限制很好，但缺少產品忠實度、參考圖與生成工具規格。（PDF p. 4、6、10–11） |
| 初學者直接複製使用 | 6/10 | 方括號看似簡單，實際上若沒有品牌、受眾、尺寸、素材與禁區，輸出仍會很泛。（PDF p. 1–11） |
| 作為長期 prompt library | 6/10（原檔）／9/10（整理後） | 原檔重複且缺少工作階段與工具標籤；濃縮成 15–25 張模板卡後很值得留。（PDF p. 2–11） |

**總判斷：值得保留，但應把它視為「設計提問清單與簡報骨架」，不是完整設計教材，也不是任何圖片工具通用的最終生成提示詞。**

---

## 二、文件結構與涵蓋範圍

### 2.1 文件編排

| PDF 頁碼 | 原始章節 | 提示詞編號 | 主要內容 |
|---:|---|---:|---|
| 1 | 封面／使用說明 | — | 主張填入方括號後貼進 Claude，並先要 3 個方向再深化最佳方向。這是全文件唯一明示的使用流程。（PDF p. 1） |
| 2 | Branding | 001–010 | 品牌定位、識別、語調、命名、品牌架構、改版、Moodboard。（PDF p. 2） |
| 3 | Logo Design | 011–020 | 標誌概念、批評、字母標、使用規範、符號學、響應式 Logo、字標。（PDF p. 3） |
| 4 | Product Posters | 021–030 | 產品海報、產品主視覺攝影、系列海報、跨比例改版、A/B 測試。（PDF p. 4） |
| 5 | Social Media | 031–040 | Instagram 系統、九宮格、輪播、迷因、照片處理、廣告、Quote Post。（PDF p. 5） |
| 6 | Packaging | 041–050 | 包裝層級、開箱、標籤、永續、文案、印刷規格、Packshot、電商縮圖。（PDF p. 6） |
| 7 | UI / UX | 051–060 | Onboarding、介面批評、Design System、Empty State、UX Writing、Accessibility。（PDF p. 7） |
| 8 | Landing Pages | 061–070 | 頁面結構、Hero、冷流量、社會證明、比較、A/B Test、速度、FAQ、長銷頁。（PDF p. 8） |
| 9 | Typography | 071–080 | 字體搭配、字級系統、多語字體、可讀性、純字體活動、Typography 禁忌。（PDF p. 9） |
| 10 | Thumbnails | 081–090 | YouTube 封面、CTR 診斷、模板、圖片提示、120px 行動裝置測試。（PDF p. 10） |
| 11 | Creative Direction | 091–100 | 月度創意檢討、Creative Brief、Campaign Platform、攝影方向、趨勢、拍攝清單、創意發散。（PDF p. 11） |
| 12 | 結語 | — | 鼓勵立即挑一個提示詞使用；沒有補充方法、案例或品質檢查標準。（PDF p. 12） |

### 2.2 涵蓋得好的範圍

1. **要求模型解釋設計決策，而非只吐出形容詞。**例如提示詞會要求說明版面層級、焦點、光線、字體理由、轉版時刪掉什麼，以及為何這樣做。（PDF p. 4、6–9）
2. **有多個真實製作限制。**例如 4:5、9:16、16:9、A4、favicon、100px 縮圖、120px 寬、2m／50cm／手持閱讀距離。（PDF p. 3–4、6、10）
3. **不只做圖，也涵蓋系統與驗證。**例如 Design System、品牌規則、包裝系列架構、Accessibility、A/B Test、Creative Review Checklist。（PDF p. 2、6–8、11）
4. **重視「同一核心在不同媒介怎麼變」。**這比單張漂亮圖更接近真正設計工作。（PDF p. 3–6、10–11）

### 2.3 明顯缺口

1. 沒有教初學者如何先準備品牌 Logo、產品參考圖、精確文案、尺寸與印刷／網站技術限制；但這些正是成品品質最重要的輸入。（PDF p. 1–11）
2. 沒有區分「請 Claude 做策略／文案／HTML」與「請圖片生成模型產圖」兩種不同任務。（PDF p. 3–10）
3. 沒有真正的範例輸入與範例輸出，使用者看不到何謂合格答案。（PDF p. 2–11）
4. 沒有教迭代失敗時怎麼修：例如人物不像、產品變形、文字亂碼、留白不足、網站層級不清。（PDF p. 1–12）
5. 沒有版權、商標、字型授權、攝影師風格模仿、真實產品宣稱等提醒。（PDF p. 2–11）

---

## 三、依實際用途重新分類

原文件按設計專業分成 10 章，但初學者更適合按「我要做什麼」分類。以下分類允許交叉使用；同一提示詞可能同時出現在主要用途與通用工作流。

### A. 網站

**核心提示詞：051–070。**UI／UX 章負責產品流程與元件系統，Landing Page 章負責行銷頁結構與轉換。（PDF p. 7–8）

- **網站流程與資訊架構**：051、054、056、059、060。（PDF p. 7）
- **介面品質與系統**：052、053、055、058。（PDF p. 7）
- **Landing Page 架構與 Hero**：061、062、063、070。（PDF p. 8）
- **轉換元素**：057、064、065、066、067、069。（PDF p. 7–8）
- **效能與技術限制**：068。（PDF p. 8）
- **可搭配的跨章提示詞**：033 可規劃 HTML 輪播；050 可處理電商縮圖；071、072、078 可補網站字體與可讀性。（PDF p. 5–6、9）

**實際價值**：很適合先產生 Wireframe、內容層級與 Design System 草案；若要真的做網站，應再追加技術棧、響應式斷點、Accessibility 驗收與元件狀態，不要把文字 Wireframe 當成完成品。（PDF p. 7–8）

### B. 海報

**核心提示詞：021–030。**這是全文件最接近可直接工作的章節，因為同時要求概念、標題、比例、版式、光線與測試。（PDF p. 4）

- **概念與主視覺**：021、022、024、027、028。（PDF p. 4）
- **產品攝影結合海報**：023、029。（PDF p. 4）
- **純字體海報**：026，另可搭配 077、079。（PDF p. 4、9）
- **跨尺寸改版**：025。（PDF p. 4）
- **廣告驗證**：030。（PDF p. 4）
- **社群海報系統**：031–040，尤其 035、038、039。（PDF p. 5）

**實際價值**：適合先找主意與層級，不適合直接把長文交給圖片生成模型。正確做法通常是「生成無字主視覺」後，再在 Figma、Canva、Photoshop 或 HTML/CSS 裡排真實文字。（PDF p. 4–5、9）

### C. 產品封面／產品攝影

這類工作分成「產品主視覺照片」、「包裝／封面」、「平台縮圖」三層。

- **英雄產品照／Lifestyle**：023、029。（PDF p. 4）
- **包裝設計與 Packshot**：041–050，尤其 041、043、047、049、050。（PDF p. 6）
- **影片／內容封面**：081–090，尤其 081、086、088、089。（PDF p. 10）
- **完整品牌攝影系統與 Shot List**：095、099。（PDF p. 11）
- **相關風格控制**：010、037、071、075。（PDF p. 2、5、9）

**實際價值**：023、029、049、095、099 是好骨架，但要再加產品參考圖、不可改變的外觀細節、Logo／標籤忠實度、材質、尺寸、背景去背需求、文字安全區與生成後人工合成方式。（PDF p. 4、6、11）

### D. 品牌／風格探索

- **品牌定位與語言**：001–010。（PDF p. 2）
- **Logo 與符號方向**：011–020。（PDF p. 3）
- **社群視覺系統**：031、034、037、040。（PDF p. 5）
- **包裝系列系統**：043、046、047。（PDF p. 6）
- **Typography**：071–080。（PDF p. 9）
- **Creative Direction**：091–100。（PDF p. 11）
- **特別適合探索風格差異**：022 的三種情緒溫度、079 的三種字體方向、100 的安全／大膽／高風險創意分級。（PDF p. 4、9、11）

**實際價值**：適合產出方向候選，不應讓模型單方面決定品牌。初學者至少要先給「受眾、價格帶、競品、不能像誰、想保留什麼」；否則模型容易回到常見的極簡、奢華、復古、科技感等通用套路。（PDF p. 2–3、9、11）

### E. 通用工作流

這些不是特定媒介，而是可以套到網站、海報、封面與品牌工作的通用方法。

| 工作階段 | 可重用提示詞 | 用法 |
|---|---|---|
| 定位／Brief | 001、008、092、100 | 把商業問題、受眾張力、品牌語言與創意選項講清楚。（PDF p. 2、11） |
| 多方向發散 | 003、010、011、022、027、067、079、081、100 | 先拿 3–7 個方向再選，不要第一稿即定案。（PDF p. 2–4、8–11） |
| 批評／Audit | 002、012、040、052、073、084、091、096 | 找系統破壞、層級問題與最高影響修正。（PDF p. 2–3、5、7、9–11） |
| 跨尺寸適配 | 019、025、050、089 | 決定小尺寸時什麼放大、什麼刪除、什麼保留。（PDF p. 3–4、6、10） |
| 系統化規格 | 004、014、031、047、053、072、074、080、098 | 把一次性設計變成可持續規則。（PDF p. 2–3、5–7、9、11） |
| 生產／技術檢查 | 048、058、068、078、089、098 | 印刷、Accessibility、效能、閱讀與縮圖測試。（PDF p. 6–11） |
| A/B 測試 | 030、067、083 | 一次只改一個變因，讓結果可解釋。（PDF p. 4、8、10） |

---

## 四、可直接複製的高價值提示詞

以下保留 PDF 原文。建議不要原封不動直接送出；先把方括號資料補完整，再加上尺寸、素材與禁區。

### 4.1 網站

#### 1. Landing Page 架構

> **“You are a conversion designer. Wireframe a landing page for [offer]: section order with the job of each section, hero layout, where proof lives, and the single CTA repeated how many times.”**（Prompt 061，PDF p. 8）

**為何有價值**：它要求每一區都要有「工作」，可避免把網站做成只是在堆元件。初學者可再補「受眾、流量來源、裝置比例、轉換目標」。

#### 2. Hero 的文案、視覺與首屏邏輯

> **“Write and art-direct the hero section for [product]: headline (under 10 words), subhead, CTA label, and the hero visual described for an image generator — with the fold logic explained.”**（Prompt 062，PDF p. 8）

**為何有價值**：不只要求一句標題，也要求首屏內什麼先被看見、圖片扮演什麼角色。適合網站首頁或產品頁開場。

#### 3. 介面批評按效益排序

> **“Critique this screen like a design lead: [describe/attach]. Hierarchy, affordance, cognitive load, accessibility — the 3 changes with the highest impact-to-effort ratio first.”**（Prompt 052，PDF p. 7）

**為何有價值**：`highest impact-to-effort ratio first` 是非常值得抽出來重用的句型，能防止模型一次列 20 個問題卻沒有優先順序。

#### 4. 可執行的 Accessibility 檢查

> **“You are an accessibility auditor. Review this design: [describe]. Contrast, touch targets, focus order, motion sensitivity — pass/fail each with the fix, no vague advice.”**（Prompt 058，PDF p. 7）

**為何有價值**：`pass/fail each with the fix, no vague advice` 把輸出從建議提升成驗收清單。若是實際網站，還應要求對照 WCAG 版本與檢查工具。

#### 5. 網頁效能限制

> **“You are a page-speed pragmatist. List the 10 design decisions for [page] that keep it beautiful AND under 2s load: image strategy, font limits, animation budget, third-party rules.”**（Prompt 068，PDF p. 8）

**為何有價值**：提醒初學者視覺設計和載入效能是同一個問題。但「under 2s」不能單靠設計保證，還要補測試裝置、網路條件與 Web Vitals 指標。

### 4.2 海報

#### 6. 海報的完整最小規格

> **“You are an art director. Design a product poster for [product]: one visual metaphor, headline under 6 words, layout grid, lighting direction, and an exact image-generation prompt in 4:5.”**（Prompt 021，PDF p. 4）

**為何有價值**：把概念、文案、格線、光線、比例一次串起來，是海報章的最佳起點。建議再加 Logo 區、法規文字區、印刷尺寸與出血。

#### 7. 跨格式改版

> **“You are a retail designer. Adapt this poster concept for 4 formats: IG feed 4:5, story 9:16, billboard 16:9 landscape, and A4 print — what changes in hierarchy at each size: [describe concept].”**（Prompt 025，PDF p. 4）

**為何有價值**：真正好用的不是四個比例，而是 `what changes in hierarchy at each size`。它迫使模型說明縮放以外的重新編排。

#### 8. 可解釋的 A/B Test

> **“Create the poster testing plan: 3 poster variants for [product] that isolate one variable each (headline, visual metaphor, colour), so ad results tell me WHY the winner won.”**（Prompt 030，PDF p. 4）

**為何有價值**：`isolate one variable each` 可直接套用網站 Hero、社群廣告、封面縮圖，避免測試同時改太多東西。

### 4.3 產品封面／產品攝影

#### 9. Hero Product Shot

> **“Write the full art direction for a hero product shot of [product]: camera angle, focal length feel, background, surface, lighting setup with shadow behaviour, and prop rules (max 2 props).”**（Prompt 023，PDF p. 4）

**為何有價值**：這是全 PDF 最實用的產品攝影骨架之一。`shadow behaviour` 與 `max 2 props` 能大幅減少雜亂與不真實感。

#### 10. Packshot

> **“Write an image-generation prompt for a packshot: [product] packaging on [surface] with [lighting style], studio quality, showing material texture — precise enough to look like a real product photo.”**（Prompt 049，PDF p. 6）

**為何有價值**：能得到基本商品圖，但需要追加「使用已上傳產品作唯一造型參考、不得改 Logo／標籤／比例、背景要求、陰影方向、輸出尺寸」。

#### 11. 小尺寸生存測試

> **“You are a mobile-first designer. Take this thumbnail concept and make it survive at 120px wide: [describe]. What simplifies, what enlarges, what dies.”**（Prompt 089，PDF p. 10）

**為何有價值**：`What simplifies, what enlarges, what dies` 是封面、產品卡、Logo、海報縮圖都能使用的強句型。

#### 12. 完整 Shot List

> **“Direct a full brand campaign shoot in one prompt: for [product], give me the shot list (10 shots), each with composition, lens feel, lighting, and the story beat it covers.”**（Prompt 099，PDF p. 11）

**為何有價值**：比只生成一張 Hero 圖更完整，適合一次規劃首頁、廣告、社群與電商素材。但應再指定每張用途和比例，否則 10 張可能只是風格相近的清單。

### 4.4 品牌與創意工作流

#### 13. Creative Brief

> **“Write a creative brief for [campaign]: business problem, audience insight (a real tension, not a demographic), the single-minded proposition, mandatories, and what great looks like.”**（Prompt 092，PDF p. 11）

**為何有價值**：`a real tension, not a demographic` 與 `single-minded proposition` 是這份 PDF 最值得長期保留的句型之一。它把「25–35 歲女性」這種空泛受眾，改成真正的需求衝突。

#### 14. 創意發散的風險梯度

> **“You are my creative partner. Here is the brief: [paste]. Give me 3 safe ideas, 3 brave ideas, and 1 idea that could get us fired — then argue for the brave option you'd actually ship.”**（Prompt 100，PDF p. 11）

**為何有價值**：安全／大膽／極端的梯度有助於突破第一個平庸答案。實務上應把 `could get us fired` 改成「高風險實驗」，並補品牌、法規與聲譽禁區。

### 4.5 最值得抽出的句型元件

以下元件比完整提示詞更值得存進個人 library：

- **“ranked by how much it costs us trust”**：按對信任的傷害排序，而不是只列問題。（Prompt 002，PDF p. 2）
- **“why it works at favicon size”**：要求概念在極小尺寸仍成立。（Prompt 011，PDF p. 3）
- **“what drops at each size and the exact breakpoint logic”**：要求響應式設計有刪減規則。（Prompt 019，PDF p. 3）
- **“what changes in hierarchy at each size”**：跨比例不是單純縮放。（Prompt 025，PDF p. 4）
- **“isolate one variable each”**：建立可解釋的測試。（Prompt 030，PDF p. 4）
- **“what’s readable at 2m, 50cm, in-hand”**：按觀看距離設計資訊層級。（Prompt 041，PDF p. 6）
- **“the 3 changes with the highest impact-to-effort ratio first”**：先做最有效率的修正。（Prompt 052，PDF p. 7）
- **“pass/fail each with the fix, no vague advice”**：把評論轉成驗收與修正。（Prompt 058，PDF p. 7）
- **“one row we concede (and why that builds trust)”**：比較頁主動承認一項弱勢以提高可信度。（Prompt 066，PDF p. 8）
- **“what simplifies, what enlarges, what dies”**：小尺寸設計的刪減決策。（Prompt 089，PDF p. 10）
- **“audience insight (a real tension, not a demographic)”**：把人口屬性轉成真實心理張力。（Prompt 092，PDF p. 11）
- **“ordered from strategy to craft”**：檢查順序先策略、後工藝，不先糾結細節。（Prompt 098，PDF p. 11）

---

## 五、哪些內容需要打折看待

### 5.1 容易過時或必須即時查證

這份文件在 2026 年製作，沒有整體過時問題；真正容易過時的是要求模型憑記憶回答市場與資源現況的提示詞。

1. **Prompt 006 的 `.com-style handle idea` 不是網域可用性、商標或社群帳號查核。**只能當命名形式靈感，不能當註冊結論。（PDF p. 2）
2. **Prompt 018 的 30 年 Logo 演變與 Prompt 097 的趨勢預測需要即時研究與來源。**若沒有搜尋、日期與案例引用，答案很可能只是模型熟悉的設計史敘事。（PDF p. 3、11）
3. **Prompt 071 的「free options included」會受字型授權、平台與語言支援變化影響。**每次正式使用都要重新核對授權與字重。（PDF p. 9）
4. **Prompt 068 的「under 2s load」仍是合理方向，但不是只靠 10 個設計決策即可保證。**它忽略裝置、網路、伺服器、框架、快取與 Core Web Vitals 測試條件。（PDF p. 8）
5. **Prompt 084 的 CTR 診斷若沒有頻道規模、流量來源、題材與同類基準，百分比本身無法判斷好壞。**（PDF p. 10）

### 5.2 空泛或容易產生漂亮廢話

1. 多數開頭的 **“You are a…”** 角色設定不是問題，但通常不是品質主因；真正有效的是後面的輸出欄位、限制與判斷標準。（PDF p. 2–11）
2. Prompt 022 的「minimal and quiet／bold and loud／surreal and dreamlike」可快速發散，但若沒有品牌、受眾與銷售情境，容易得到三套熟悉風格標籤。（PDF p. 4）
3. Prompt 093 的 Campaign Platform 沒有預算、通路優先順序、地區、執行資源與 KPI，容易產生氣勢很大的概念卻難落地。（PDF p. 11）
4. Prompt 097 的「即將達峰／正在興起」如果不要求證據、時間範圍與地區，就是高風險的趨勢幻覺。（PDF p. 11）
5. Prompt 100 的「could get us fired」有記憶點，但會鼓勵模型把極端當創意。實務上應加品牌安全、法規、文化敏感度與不可觸碰項目。（PDF p. 11）

### 5.3 重複度高

1. **081 與 088 幾乎是同一個 YouTube Thumbnail Brief**：主體、文字、對比與 Image Prompt，保留一個即可。（PDF p. 10）
2. **021、023、029、049** 都在要求產品圖的構圖、光線、場景與圖片提示；差別是海報、Hero、Lifestyle、Packshot，可合併成一張有「拍攝模式」欄位的模板。（PDF p. 4、6）
3. **012、052、073** 是同一種「像資深設計主管一樣批評」框架，只是對象換成 Logo、介面、Typography。（PDF p. 3、7、9）
4. **003、010、095** 都在建立視覺風格系統：Identity、Moodboard、Photography Direction，可用同一套風格欄位重組。（PDF p. 2、11）
5. **031、037、040** 分別做社群系統、照片處理、社群一致性 Audit，適合合併成「定義規則 → 產生模板 → 稽核輸出」的一個工作流。（PDF p. 5）

### 5.4 只適合 Claude Artifacts／HTML，或其實只是規格文件

文件沒有直接提到「Claude Artifacts」，但幾組提示詞本質上是文字規格或 HTML 原型任務，不適合直接交給圖片生成工具。

1. **Prompt 033 明寫「Describe precisely enough to build in HTML」**，最適合 Claude Artifact、HTML/CSS 原型或前端實作；給圖片模型只會得到一張不可互動的版面示意。（PDF p. 5）
2. **Prompts 051–060** 多半輸出流程、Design System、UX Copy、Accessibility 判斷；它們適合 Claude 文字推理或互動原型，不是圖片生成提示。（PDF p. 7）
3. **Prompts 061–070** 主要產出 Landing Page 架構、文案、Proof Strategy、FAQ 與測試計畫；若要可用網站，必須追加 HTML／CSS／React 等實作要求與驗收條件。（PDF p. 8）
4. **Prompt 053 的 Token、Button Hierarchy、Spacing Scale** 是設計系統文件；只有要求輸出程式碼或 Artifact 時才會變成可點的介面。（PDF p. 7）

### 5.5 對圖片生成工具不夠具體

1. **Prompt 013、016 的 Logo 生成**低估了圖片模型對幾何一致性、精確字形、向量可編輯性與小尺寸辨識的限制。應先生成無字符號草圖，再由人用向量工具重畫；不要把生成圖當最終 Logo。（PDF p. 3）
2. **Prompt 021 雖要求「exact image-generation prompt」**，仍未指定產品參考圖、品牌 Logo、文字安全區、產品不可變形項目、負面條件與最終工具。（PDF p. 4）
3. **Prompt 029 的 “shot like a [film/photographer] frame”** 太依賴作者／攝影師名稱。更穩定的做法是描述鏡頭、光線、色調、顆粒、構圖與年代特徵。（PDF p. 4）
4. **Prompt 039、075、079 涉及圖中精確文字或 Typography。**圖片模型常無法穩定產出正確文字、字距與換行；應生成背景／質感，文字由排版工具完成。（PDF p. 5、9）
5. **Prompt 049 的 Packshot** 缺少產品比例、包裝標籤忠實、透明或純色背景、去背、反射控制、顏色校準與解析度。（PDF p. 6）
6. **Prompt 086、088 的 Thumbnail** 未處理人物一致性與標題文字問題。更可靠的流程是生成「無文字、保留文字區」的底圖，再人工加入 2–3 字標題。（PDF p. 10）
7. **Prompt 095、099 的拍攝方向**沒有把每張圖綁定用途和比例，容易得到 5–10 張敘述相似的圖片，而不是完整素材矩陣。（PDF p. 11）

---

## 六、給初學者的最小可行使用法

### 6.1 不要一開始挑 Prompt；先填「需求簡報模板」

以下模板是從 Creative Brief、Landing Page、Product Shot、Format Adaptation 與 Review Checklist 類提示詞整理而來。（主要依據：Prompt 023、025、061、062、092、098；PDF p. 4、8、11）

```text
【專案】
我要做：網站／海報／產品封面／產品攝影／品牌方向

【商業目標】
這個設計要讓人：理解＿＿＿／相信＿＿＿／點擊＿＿＿／購買＿＿＿

【受眾】
誰會看？他現在最在意什麼、懷疑什麼、害怕什麼？
不要只寫年齡與性別，請寫一個真實張力。

【單一核心訊息】
看完後只能記得一件事：＿＿＿

【產品／品牌真相】
最重要且可證明的 1–3 個優勢：＿＿＿
不可誇大或改寫的數據／宣稱：＿＿＿

【視覺方向】
希望感覺：＿＿＿
不要像：＿＿＿
可參考的作品與只想借用的特徵：＿＿＿

【素材】
已有 Logo、產品照片、人物照、文案、品牌色、字型：＿＿＿
哪些素材必須原樣保留：＿＿＿

【版位與尺寸】
平台／媒介：＿＿＿
比例與像素／印刷尺寸：＿＿＿
需要保留的 Logo、標題、CTA、安全區：＿＿＿

【限制】
必須有：＿＿＿
絕對不能有：＿＿＿
圖片生成不得改變：＿＿＿

【交付內容】
我要模型輸出：
1. 3 個明顯不同方向
2. 每個方向的概念、版式、色彩、字體、圖片策略
3. 推薦一個方向並說明原因
4. 最終圖片提示詞／版面規格／文案
5. 自我檢查清單
```

### 6.2 提示詞組裝公式

最小公式：

> **目標與受眾 + 單一訊息 + 交付物 + 視覺方向 + 層級／構圖 + 技術規格 + 必須／禁止 + 變體 + 驗收標準**

可直接套用的完整骨架：

```text
我要為【產品／品牌】製作【網站／海報／封面／產品照】，目標是讓【受眾】
在【觀看情境】理解／相信／採取【行動】。

單一核心訊息是：【一句話】。
必須保留的品牌／產品真實資訊：【Logo、外觀、數據、文案】。

先提出 3 個真正不同的視覺方向。每個方向請提供：
- 一句概念
- 資訊層級與構圖
- 色彩與字體策略
- 圖片／攝影策略
- 為何適合受眾與目標

選出你最推薦的一個方向，再輸出：
- 可直接執行的版面規格
- 【尺寸／比例／平台】的適配規則
- 圖片生成提示詞；另列不可出現或不可改變的項目
- 哪些文字應由排版工具後製，不要交給圖片模型
- 5 項 pass/fail 驗收清單，並把最高影響、最低成本的修正排前面

限制：【必須有】；【絕對不能有】。
不要使用空泛詞如「高級、現代、乾淨」而不解釋它如何反映在版式、光線、色彩與材質。
```

這個公式吸收了 PDF 最強的幾個做法：先多方向、說明層級、限制道具／元素、跨尺寸刪減、按影響排序、Pass/Fail 驗收。（PDF p. 1、4、6–8、10–11）

### 6.3 最小工作流：三輪就夠

1. **第一輪：只做方向。**要求 3 個差異明顯的方向，不生成最終稿；使用 Prompt 022 或 100 的分級思路。（PDF p. 4、11）
2. **第二輪：選一個方向做規格。**要求層級、尺寸、字體、色彩、攝影與素材禁區；可用 023、025、053、061、062。（PDF p. 4、7–8）
3. **第三輪：做成品提示與 QA。**輸出圖片生成提示、人工排版項目、跨尺寸版本、A/B 變因與 Pass/Fail Checklist；可用 030、058、089、098。（PDF p. 4、7、10–11）

如果第一輪的 3 個方向只是換顏色，直接要求：**「三個方向必須在構圖機制、視覺隱喻與攝影／插畫方法上都不同，不得只改色盤。」**這是對 Prompt 022、079、100 的必要補強。（PDF p. 4、9、11）

---

## 七、3 個完整範例

以下不是 PDF 原文，而是把其中高價值結構組裝成初學者可直接使用的版本。

### 範例 1：B2B 產品網站首頁

**組合來源**：061、062、064、068，以及 052、058 的審查方式。（PDF p. 7–8）

```text
我要為一款工業用鈉離子儲能電池設計 B2B Landing Page，主要受眾是工廠能源主管與採購人員。
他們的真實張力是：想降低供應與安全風險，但不願為尚未驗證的新技術承擔停機責任。

商業目標：讓合格訪客預約技術諮詢。
單一核心訊息：這是一個可被工程與採購共同驗證的替代方案，不是概念展示。

現有素材：產品實拍、技術規格表、3 個測試數據、公司 Logo。
所有測得數值必須原樣保留，不得自行改寫、四捨五入或創造比較數據。

請先提出 3 個真正不同的視覺方向，每個方向說明：
1. Hero 構圖與首屏資訊層級
2. 色盤與字體，包含實際字體名稱
3. 產品照片如何處理
4. 如何建立工程可信度而不做成沉悶型錄
5. 為何適合冷流量 B2B 訪客

再選一個最推薦方向，輸出：
- 桌面與手機的完整 section order，並寫出每區唯一工作
- 10 字內 Hero headline、subhead、主 CTA、次 CTA
- Logo／測試數據／客戶證據出現的 scroll depth
- 3 個方案比較區與 6 題 FAQ
- 圖片策略、字型載入限制、動畫預算，目標在一般 4G 手機維持快速首屏
- 1440px、768px、390px 三個斷點的層級變化：what simplifies, what enlarges, what dies
- Accessibility pass/fail 清單：對比、觸控區、焦點順序、Reduced Motion

不要直接用紫色科技漸層、漂浮卡片或沒有證據的「革命性」文案。
最後把建議按最高 impact-to-effort ratio 排序。
```

### 範例 2：活動海報

**組合來源**：021、025、026、030、079。（PDF p. 4、9）

```text
我要設計一張「夜間城市攝影展」主視覺海報，受眾是 20–40 歲、喜歡攝影與城市文化但不熟悉參展者的人。
目標是讓人停下來看、記住展名，並掃 QR Code 購票。

單一核心訊息：城市在熄燈後才顯露另一種秩序。
固定文字：
- 展名：AFTER THE LAST TRAIN
- 日期：2026.09.18–10.04
- 地點：Warehouse 7
- CTA：Tickets / QR

先提出 3 個在「構圖機制、視覺隱喻、影像方法」都不同的方向：
A. minimal and quiet
B. bold and loud
C. surreal and dreamlike
不得只改色盤。

每個方向提供：
- 一個視覺隱喻
- 6 字內副標
- 版面格線與觀看順序
- 字體建議、字重、字距
- 主圖的光線、顆粒、鏡頭感與色調
- 為何能在 2 秒內讓路人理解

選出最推薦方向後，輸出：
1. A2 直式印刷版規格，含 3mm bleed、安全邊界、QR 安全區
2. IG 4:5、Story 9:16、16:9 螢幕版的層級變化
3. 一段只生成「無文字主視覺」的圖片提示詞，畫面預留標題與 QR 區域
4. 明列哪些文字必須在 Figma／Canva 後製，不要由圖片模型生成
5. 3 個 A/B 版本；每版只改 headline、visual metaphor、colour 其中一項
6. 5 項 pass/fail 清單：3 秒辨識、縮圖可讀、日期清楚、QR 不被搶焦、無多餘裝飾
```

### 範例 3：產品封面照／電商 Hero Packshot

**組合來源**：023、029、049、050、089、095、099。（PDF p. 4、6、10–11）

```text
我要為一款霧面深灰色行動電源製作電商首頁 Hero 圖與產品封面照。
受眾是重視旅行輕量化與產品可靠度的商務旅客。
單一核心訊息：安靜、可信賴、隨手帶走的備用電力。

我會上傳產品正面、背面、側面與 Logo 參考圖。產品外形、接口數量、按鍵位置、Logo、標籤、比例與霧面材質必須忠實保留，不得增加不存在的螢幕、接口或燈效。

先提出 3 個攝影方向：
1. 純棚拍 Packshot
2. 低調商務旅行 Lifestyle
3. 有一個視覺隱喻的 Campaign Hero

每個方向提供：
- camera angle 與 focal length feel
- 背景與 surface
- 主光、補光、輪廓光、shadow behaviour
- 色調與反射控制
- props 規則，最多 2 件
- 產品在畫面中的百分比與文字安全區
- 為何適合電商 100px 縮圖

選出最推薦方向後，輸出兩段圖片生成提示：
A. 1:1 電商封面，產品置中、純背景、可去背、材質清楚
B. 16:9 網站 Hero，產品偏左，右側保留 40% 乾淨文字區

兩段提示都必須包含：
- 使用上傳圖片作唯一產品造型參考
- 不得改變產品幾何、接口、Logo、標籤或色彩
- 不生成任何文案、假字或額外品牌
- realistic studio photography，不要 3D 塑膠感、過度光暈、漂浮粒子或不合理反射
- 產品邊緣完整，不裁切主體

最後提供：
- 120px 寬縮圖測試：what simplifies, what enlarges, what dies
- 5 項產品忠實度 pass/fail 清單
- 若圖片模型無法忠實保留 Logo，說明如何用原始產品照與生成背景做人工合成
```

---

## 八、是否值得長期保留？

### 判斷：值得，但只值得「封存原 PDF + 建立精簡版」

原 PDF 適合保留作來源，因為它把常見設計任務完整掃過一輪，而且多次提供非常好的限制句型，例如觀看距離、跨尺寸刪減、單一變因測試、影響成本排序與策略到工藝的檢查順序。（PDF p. 3–11）

但不建議每天在 100 條裡搜尋。它的章節是按設計專業，不是按工作階段；重複提示多，也沒有標示輸入需求、適用工具、輸出格式與失敗處理。（PDF p. 2–11）

### 建議整理成 5 個資料夾、15–25 張核心模板

```text
prompt-library/
  website/
    landing-page-brief
    hero-section
    ui-critique
    accessibility-review
    responsive-reduction
  poster/
    poster-directions
    typography-only-poster
    format-adaptation
    ab-test-plan
  product-visuals/
    hero-product-shot
    lifestyle-shot
    packshot
    ecommerce-thumbnail
    campaign-shot-list
  brand-style/
    brand-positioning
    moodboard
    typography-system
    photography-direction
    creative-directions
  workflow/
    requirements-brief
    critique
    production-checklist
    test-plan
    final-qa
```

### 每張 Prompt Card 應包含的欄位

```yaml
name: hero-product-shot
purpose: 產生產品主視覺攝影方向與最終圖片提示
stage: direction | production | review
inputs_required:
  - product reference images
  - audience
  - message
  - placement and aspect ratio
  - immutable product details
output_required:
  - three directions
  - selected direction
  - camera / lighting / surface / props
  - final image prompt
  - negative constraints
  - QA checklist
tool: Claude + image generator + layout tool
source: PDF prompt 023, p.4; prompt 049, p.6
last_tested: YYYY-MM-DD
notes: 圖中文字與 Logo 建議後製
```

### 建議保留與刪減

- **原文保留**：001、002、008、011、019、021、023、025、030、041、049、052、053、058、061、062、066、068、071、078、089、092、095、098、099、100，共約 26 條。（PDF p. 2–11）
- **合併重複**：012／052／073；021／023／029／049；081／088；003／010／095。（PDF p. 2–4、6–11）
- **改寫後再用**：006、013、016、039、075、086、097、100；原因分別是查核不足、Logo／文字生成限制、趨勢幻覺與創意風險邊界。（PDF p. 2–5、9–11）
- **原 PDF 不刪**：它仍是來源與頁碼索引；日常只用整理後的 Prompt Card。

---

## 九、最終建議

1. **把 PDF 當成「你應該問設計師什麼」的題庫，不要當成「圖片生成咒語大全」。**它最強的是設計 Brief 與批評結構。（PDF p. 2–11）
2. **近期做網站時，優先使用 052、053、058、061、062、068；**這組涵蓋介面批評、Design System、Accessibility、頁面架構、Hero 與效能。（PDF p. 7–8）
3. **近期做海報時，優先使用 021、025、030，再搭配 079；**先定概念與層級，再做跨格式與可解釋測試。（PDF p. 4、9）
4. **近期做產品封面／產品攝影時，優先使用 023、049、089、095、099，並強制補上產品忠實度與後製規則。**（PDF p. 4、6、10–11）
5. **真正值得長期保存的是句型元件與工作流，而不是 100 條原句。**將 100 條濃縮成約 20 張帶有輸入、輸出、工具、限制與 QA 的 Prompt Card，實用價值會遠高於原 PDF。（PDF p. 2–11）
