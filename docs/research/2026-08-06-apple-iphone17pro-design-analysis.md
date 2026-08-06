# Apple iPhone 17 Pro 產品頁 — 完整設計解構

> 來源：https://www.apple.com/tw/iphone-17-pro/（2026-08-06 實測抓取）
> 方法：實際載入頁面，用 JavaScript 讀取 computed styles、DOM 結構、組件屬性，並截圖驗證。
> 所有數值（色碼、字級、圓角、斷點）皆為從頁面直接量測的真實值，非猜測。

截圖：[hero](assets-iphone17pro/a17_hero.png)｜[設計區](assets-iphone17pro/a17_design.png)｜[產品檢視器](assets-iphone17pro/a17_viewer.png)｜[相機微距](assets-iphone17pro/a17_zoom.png)｜[電池數據](assets-iphone17pro/a17_battery.png)｜[淺色商務區](assets-iphone17pro/a17_light.png)

---

## 1. 整體風格定位

**「深色劇場 + 淺色商店」的雙幕結構。** 整頁 54,700px 高、18 個 section，前 9 個（產品敘事）全黑背景，後 7 個（購買誘因、環保、比較）全淺灰 `#f5f5f7`。產品故事像電影院一樣在黑暗中放映，講完才把燈打開讓你購物。

核心風格關鍵字：

- **極簡奢華（Minimal Luxury）**：大量留白（黑）、一次只講一件事、每屏只有一個視覺焦點
- **攝影主導（Photography-first）**：文字永遠在為滿版微距產品照服務，不是反過來
- **單一強調色**：本代主色是「宇宙橙 Cosmic Orange」`rgb(255,121,27)`，只用在 eyebrow 標籤、大數字、hero 漸層字，用量極少所以每次出現都搶眼
- **膠囊形狀語言**：按鈕、導覽、標籤全是全圓角 pill（`border-radius: 980px`）
- **滾動即敘事**：捲動不是翻頁，是播放——影片、淡入、視差全部掛在 scroll 上

---

## 2. 頁面資訊架構（Section 逐一解構）

實測 18 個 section，順序與高度如下（1280px 視窗）：

| # | Section | 高度 | 主題 | 內容 |
|---|---------|------|------|------|
| 1 | `section-welcome` (hero) | 630px | 黑 | 巨型漸層字 + 產品微距 + 購買 CTA + 價格 |
| 2 | `section-highlights` | 4,726px | 深灰 `#1d1d1f` | 7 張自動輪播的媒體卡片畫廊（重點速覽） |
| 3 | `section-design` | 1,243px | 純黑 | 設計敘事：eyebrow + 80px 大標 + 段落 + 產品照 |
| 4 | `section-product-viewer` | 1,375px | 純黑 | 互動產品檢視器：左側熱點 pill 清單、右側手機、顏色切換 |
| 5 | `section-cameras` | **19,773px** | 純黑 | 全頁最大宗：變焦畫廊、鏡頭規格、照片畫廊、新功能、Pro 影片 |
| 6 | `section-performance` | 3,677px | 純黑 | A19 Pro、散熱、電池大數字 |
| 7 | `section-shared-features` | 8,126px | 純黑 | iOS 26 / Apple Intelligence / 實用功能卡片群 |
| 8 | `section-upgrade` | 1,335px | 純黑 | 「值得升級嗎」互動比較（選舊機型看差異） |
| 9 | `section-accessories` | 670px | 純黑 | 配件橫捲畫廊 |
| 10–12 | upgrade-banner / incentive | ~4,600px | 淺灰 | 換購、分期、設定服務等 6 張商務卡片 |
| 13 | `section-contrast` | 2,007px | 淺灰 | 「找出適合你的 iPhone」產品比較 tiles |
| 14 | `section-environment` | 2,869px | 淺灰 | 環保三段落（再生物料/電力/包裝） |
| 15 | `section-values` | 1,076px | 淺灰 | 價值觀三卡（環境/隱私/輔助使用） |
| 16 | `section-index` | 320px | 淺灰 | 「比較最新 iPhone 機型」錨點索引 |
| 17–18 | footnotes + footer | ~960px | 淺灰 | 法務註腳（帶編號上標）+ 全站 footer |

**敘事節奏公式**：`勾引（hero）→ 速覽（highlights）→ 深講（design→cameras→performance，由淺入深）→ 全系列共同點 → 說服升級 → 配件加購 → 購買誘因 → 比較收尾`。每個產品敘事 section 結尾都掛一顆置中的「比較 iPhone ○○ ＋」pill 按鈕開 modal，把「比較」動作分散埋進每一段。

---

## 3. 色彩系統（實測值）

### 深色劇場（敘事區）

| 用途 | 值 | 備註 |
|------|-----|------|
| 背景主色 | `#000000` | 純黑，產品敘事區 |
| 背景次色 | `#1d1d1f` | highlights 區、深灰卡片 |
| 主文字 | `#f5f5f7` | 近白（不是純白，降低刺眼感） |
| 次要文字 | `#86868b` | 中灰——**這是 Apple 最重要的顏色**，見 §9 雙色調文字 |
| 深灰第三階 | `#6e6e73` | 淺色區的次要文字 |
| 連結藍（深色上） | `#2997ff` | 深背景用亮藍 |

### 淺色商店（商務區）

| 用途 | 值 |
|------|-----|
| 背景 | `#f5f5f7` |
| 卡片 | `#ffffff` |
| 主文字 | `#1d1d1f` |
| 連結藍（淺色上） | `#0066cc` |
| CTA 按鈕藍 | `#0071e3` |

### 本代主題強調色

| 用途 | 值 |
|------|-----|
| 宇宙橙（Cosmic Orange） | `rgb(255,121,27)` ≈ `#ff791b` |

只用在：hero 巨型字漸層、section eyebrow（如「設計」「相機」二字）、電池區大數字（31 小時/37 小時/50%）、產品檢視器的顏色圓點。**全頁出現不到 15 次**——強調色的力量來自稀缺。

### 玻璃／半透明層

浮動導覽和覆蓋層用半透明 + backdrop blur：`rgba(0,0,0,0.72)`、`rgba(42,42,45,0.72)`、`rgba(255,255,255,0.8)` 等，配 `backdrop-filter: blur()` 做毛玻璃。

---

## 4. 字體系統（完整實測 Type Scale）

字體堆疊（繁中頁）：

```css
font-family: "SF Pro TC", "SF Pro Text", "SF Pro Icons",
             "PingFang TC", "Helvetica Neue", Helvetica, Arial, sans-serif;
```

一般專案替代方案：英文用 Inter / SF Pro（自行授權），繁中用 PingFang TC（Mac 內建）或 Noto Sans TC。

### 實測 Typography Tokens（桌面 1280px）

| Token | 字級/行高 | 字重 | 用途 |
|-------|----------|------|------|
| `typography-ps-headline-elevated` | **80px/87px** | 600 | 產品敘事超大標（「一體成型機身，鑄就一身強悍實力。」） |
| `typography-section-header-headline` / `ps-headline` / `modal-header-headline` / `index-headline` | **56px/60px** | 600 | 次級大標 |
| `typography-manifesto` | 32px/42px | 600 | 宣言式段落 |
| `typography-banner-card-headline` | 32px/39px | 600 | 橫幅卡標題 |
| `typography-media-card-gallery-headline` / `feature-card-headline` / `product-tile-headline` | 28px/35px | 600 | 卡片標題 |
| `typography-ps-headline-eyebrow` | 24px/31px | 600 | 大標上方的橙色小標 |
| `typography-ps-body` / `fade-gallery-captions` / `callout-above-keyline` | **21px/29px** | **600** | 敘事內文——注意是 semibold 不是 regular |
| `typography-welcome-detail` / `localnav-product-name` | 19px/26px | 600 | 導覽產品名 |
| `typography-utility-modal-block-body` | 19px/27px | 400 | modal 內文 |
| `typography-callout-base` / `label` / `caption-tile` | 17px/23–25px | 600 | 卡片小標、標籤 |
| `typography-tout-reduced` / `feature-card-body` / `section-header-link` | 17px/23–25px | 400 | 一般內文、連結 |
| `typography-body-reduced` | 14px/21px | 500 | 縮小內文 |
| `typography-caption` / `tout-copy` | 12px/16px | 400 | 註腳、圖說 |

### 關鍵觀察

1. **只有兩個字重在做事**：600（semibold）與 400（regular）。整個視覺層級靠「大小」而非「字重數量」拉開。
2. **敘事內文是 21px semibold**，比一般網站的 16px regular 大膽很多——這是 Apple 味的關鍵之一。
3. **行高比約 1.05–1.1（大標）→ 1.38（內文）**：標題行高極緊（80/87 ≈ 1.09），內文才放鬆。
4. **Letter-spacing 微調**：大字 `normal`（中文不加），拉丁與中小字級 +0.1~0.23px。
5. 大標題常配 **兩行斷句 + 全形句號結尾**：「威力強大，開啟新境界。」——標題當標語寫，句號給定調感。

---

## 5. 版面、網格與間距

### 斷點（實測自 `<picture>` source media）

```
small:   ≤ 734px   （手機）
medium:  ≤ 1068px  （平板）
large:   ≤ 1440px  （筆電）
xlarge:  > 1440px  （大桌機）
```

每張圖都出 4 個斷點 × 1x/2x = 8 個版本（`hero__xxx_large_2x.jpg` 命名法）。

### 網格

12 欄網格，常見組合 `large-10 large-centered small-12`：內容在桌面佔 10/12 欄置中（兩側各留 1 欄呼吸），手機滿版。文字敘事區更窄（約 6–8 欄）維持 25–35 字/行。

### 間距 Token（實測 class 名）

```
ps-spacing-large-160   桌面段落間距 160px
ps-spacing-medium-128  平板 128px
ps-spacing-small-96    手機 96px
```

Section 之間垂直間距極大（96–160px 起跳），是「奢華感」的直接來源——敢留白。

### 圓角系統（實測用量統計）

| 半徑 | 出現次數 | 用途 |
|------|---------|------|
| `28px` | 120 | **主力卡片圓角**——媒體卡、白卡、feature card |
| `10px` | 24 | 小元素（縮圖、小卡） |
| `980px` | 全部按鈕 | pill 按鈕（做法：塞一個永遠大於高度的值） |
| `50%` | 15 | 圓形按鈕（＋號、播放/暫停、paddle 箭頭） |
| `32px` | 1 | 特大容器 |

---

## 6. 元件庫逐一解構

Apple 用自研框架，每個組件以 `data-component-list` 宣告。實測全頁組件清單與其設計行為：

### 6.1 LocalNav（浮動膠囊導覽）
全站 globalnav 之下，一條**浮動的黑色圓角長條**（sticky, top:0，`border-radius` 大圓角、半透明+blur）：左「iPhone 17 Pro」產品名（19px/600），右「探索」幽靈 pill ＋「購買」藍色 pill。捲動時常駐，「探索」展開錨點選單（重點特色/設計/相機/效能…），對應 `DeepLink` 組件做平滑捲動。

### 6.2 Welcome（Hero）
- `<h1>` 是 `visuallyhidden`（給 SEO/螢幕閱讀器），視覺上的「iPhone 17 PRO」其實是**橙色漸層巨型美術字**（圖像/影片），PRO 三個字母佔滿寬度、被產品照局部遮擋，做出前後層次
- Hero 影片：`preload="none" muted playsinline`，`data-inline-media-basepath` 指向影格資料夾，載入逾時 3 秒 fallback 到靜態 `<picture>`（先放 1×1 透明 gif 佔位）
- 影片下方置中：藍色「購買」pill + 「NT$39,900 起」價格 + 促銷 tout

### 6.3 MediaCardGallery（highlights 重點輪播）
7 張 28px 圓角大卡自動輪播，配 **timed-dotnav**（會隨播放進度填滿的長條點點導覽）+ 圓形播放/暫停鈕。每卡＝一句 28px 標題疊在滿版圖/影片上。這是「速覽」層——不想細讀的人 30 秒看完全部賣點。

### 6.4 ProductViewer（互動產品檢視器）
左側一欄 pill 熱點按鈕（顏色●／鋁金屬一體成型＋／均溫板＋／超瓷晶盾＋／顯示器＋／相機控制＋／動作按鈕＋），右側大產品渲染。點「顏色」切換三色（宇宙橙/藏藍/銀），點其他項展開該部位特寫與說明。組件：`ProductViewerCore/Gallery/ColorNavGallery/CustomProductScene`。

### 6.5 FadeGallery + tabnav-pill（變焦畫廊）
相機區的 8 倍變焦互動：上方一條 **pill 分段切換器**（微距/0.5x/1x/1.2x/1.5x/2x/4x/8x），下方同一場景在不同焦段的照片交叉淡入淡出（fade），支援自動輪播。`tabnav-platter` 是滑動的底盤 highlight。

### 6.6 SlideGallery / VideoGallery / ScrollGallery
- SlideGallery：橫向滑動卡片（拍照範例、配件），配左右 **paddle 圓形箭頭**（50% 圓、右下角落位）
- ScrollGallery：橫捲式敘事
- VideoGallery：影片卡片組

### 6.7 Stat Tile（大數字統計磚）
電池/效能區的招牌模式，三欄：

```
最長可達        ← 17px 灰
31 小時         ← 56–80px 橙色 semibold
iPhone 17 Pro   ← 17px 白
影片播放時間¹⁰   ← 12px 灰＋上標註腳
```

**「小字前綴 + 巨大橙色數字 + 小字說明」**，數字才是圖像。

### 6.8 Card / Modal（＋號卡片）
19 張 Card + 16 個 Modal。淺色區白卡（28px 圓角）右下角一顆黑底白＋圓鈕，點開全螢幕 modal 讀細節。**頁面本身只放一句話，細節全部塞 modal**——這是頁面乾淨的祕密。

### 6.9 InlineCompare / ContextualCompare（升級比較）
「值得升級嗎？絕對值得。」區：下拉選你的舊機型（iPhone 13–15 Pro Max），下方 stat tiles 即時換成「相對你那台」的提升數字。個人化說服。

### 6.10 Index（收尾比較索引）
頁尾前的「比較最新 iPhone 機型」：三機並排，逐列（設計/相機/晶片/電池/價格）對照，每機直欄含顏色圓點、機名、賣點句、規格清單。

---

## 7. 動效系統（實測技術）

**沒有 GSAP、沒有 Three.js、零 canvas**（實測 `window` 全域無任何動畫框架）。全部是自研滾動系統 + 原生技術：

| 技術 | 實測證據 | 行為 |
|------|---------|------|
| 滾動分組 | `data-anim-scroll-group="Design"` 等 17 組 | 每 section 一個滾動時間軸群組 |
| 交錯淡入 | `StaggeredFadeIn` × 20 | 進入視窗時子元素依序 fade+上移，全頁最常用的動效 |
| 效能提示 | `WillChange` × 25 | 動畫前掛 `will-change`，動完移除 |
| 滾動觸發影片 | `InlineMediaDefault`、`data-inline-media-basepath` | 影片捲到才載入、播完 `unload-at-end` 釋放記憶體 |
| 預載區間 | `data-download-area-keyframe='{"start":"t - 150vh","end":"b"}'` | 元素進入視窗前 150vh 就開始下載素材 |
| 串流 | `hls.js` | 長影片用 HLS 串流非整檔下載 |
| Sticky 疊層 | localnav + 各區 sticky 容器 | 比較 pill、關閉鈕等黏在捲動中 |

**可辨識的動效節奏**：一屏一事、淡入 + 20–40px 上移、交錯 80–120ms、曲線接近 `cubic-bezier(0.28, 0.11, 0.32, 1)`（Apple 慣用 ease）、時長 0.6–1s。沒有彈跳、沒有旋轉、沒有花俏 3D——**只有 opacity 和 transform，快速且克制**。

影片全部 `muted playsinline preload="none"`，自動播放不出聲，且尊重 `prefers-reduced-motion`（提供播放/暫停鈕）。

---

## 8. 媒體與攝影風格

1. **滿版微距攝影**：相機模組、鋁機身切面、拆解件——拍得像精品錶廣告。深黑背景 + 單側柔光 + 金屬質感高光。
2. **產品永遠是去背或黑背景實拍**，不用場景擺拍（生活情境只出現在功能示範截圖裡）。
3. **149 個 `<picture>` / 151 張圖、17 支影片**：每個賣點都有專屬視覺，沒有裝飾性 stock photo。
4. 拆解圖（均溫板、相機內部）用來講工程故事——「給你看內臟」是 Pro 系列的視覺修辭。
5. 淺色商務區改用**藍色線框 icon 插畫**（細線、圓角、單色 `#0066cc` 系），與敘事區的攝影形成質感落差，明示「這裡是商店」。

---

## 9. 文案風格（可直接模仿的公式）

1. **雙色調句內強調**（全頁最重要的文字技巧）：同一句話裡，重點詞 `#f5f5f7` 白、其餘 `#86868b` 灰。例：「<span style="color:#86868b">彷彿</span><b>隨身攜帶 8 個專業級鏡頭</b><span style="color:#86868b">，張張照片都</span><b>預設 2400 萬像素</b>…」讀者掃一眼只看白字就得到重點。
2. **標題公式**：兩短句 + 逗號 + 句號。「威力強大，開啟新境界。」「變焦，前瞻躍進。」
3. **Eyebrow**：橙色 2–4 字分類詞（設計/相機/效能）壓在大標上方。
4. **數字讓位**：能用數字就不用形容詞——「加大 56% 的感光元件」「最長可達 200 公釐」。
5. **註腳紀律**：所有宣稱掛上標數字（¹⁰ ¹¹），頁尾 footnotes 區統一交代——大膽宣稱 + 法務兜底。
6. 每個功能說明開頭都是「**粗體功能名。**」+ 一句話：「均溫板。 密封於內部的去離子水…」——名詞當小標內嵌在段落裡。

---

## 10. 無障礙與效能（容易被忽略但構成質感）

- `<h1>` 用 `visuallyhidden` 保留語意，視覺用美術字
- 影片都有完整 `aria-label` 描述畫面內容
- 畫廊是真 `role="tablist"/tab/tabpanel`，鍵盤可操作
- `<noscript>` 提供完整的 `<picture>` fallback
- 圖片 lazy：先塞 1×1 透明 gif，進入預載區間才換真圖
- 響應式圖片 4 斷點 × 2 解析度，`data-inline-media-breakpoint-substitution-map` 讓影片也按斷點換檔

---

## 11. 復刻指南 — 用現代 Web 技術做出同款頁面

### 11.1 Design Tokens（可直接用的 CSS）

```css
:root {
  /* 色彩 */
  --bg-stage: #000;            /* 敘事區 */
  --bg-stage-alt: #1d1d1f;     /* 深灰卡 */
  --bg-store: #f5f5f7;         /* 商務區 */
  --bg-card: #fff;
  --text-primary-dark: #f5f5f7;
  --text-secondary: #86868b;   /* 雙色調文字的灰 */
  --text-primary-light: #1d1d1f;
  --accent: #ff791b;           /* 換成你的產品主題色 */
  --link-on-dark: #2997ff;
  --link-on-light: #0066cc;
  --cta: #0071e3;

  /* 圓角 */
  --radius-card: 28px;
  --radius-small: 10px;
  --radius-pill: 980px;

  /* 間距 */
  --section-gap: clamp(96px, 12vw, 160px);

  /* 字體 */
  --font-stack: "SF Pro TC","SF Pro Display",-apple-system,
                "PingFang TC","Noto Sans TC",sans-serif;
}

/* Type scale（桌面；手機約乘 0.6）*/
.h-hero    { font-size: 80px; line-height: 1.09; font-weight: 600; }
.h-section { font-size: 56px; line-height: 1.07; font-weight: 600; }
.h-card    { font-size: 28px; line-height: 1.25; font-weight: 600; }
.eyebrow   { font-size: 24px; font-weight: 600; color: var(--accent); }
.body-ps   { font-size: 21px; line-height: 1.38; font-weight: 600;
             color: var(--text-secondary); }
.body-ps b { color: var(--text-primary-dark); font-weight: inherit; }
.caption   { font-size: 12px; line-height: 1.33; color: var(--text-secondary); }

.btn-pill  { border-radius: var(--radius-pill); padding: 11px 21px;
             background: var(--cta); color: #fff; font-size: 17px; }
```

### 11.2 頁面骨架

```
黑色敘事幕（每段都是同一模板）：
  <section class="stage">
    <p class="eyebrow">分類詞</p>
    <h2 class="h-hero">兩句式大標，句號結尾。</h2>
    <p class="body-ps">灰底白重點的<b>雙色調段落</b>。</p>
    <figure>滿版產品圖/滾動影片</figure>
    <button class="btn-pill">比較 ○○ ＋</button>  ← 開 modal
  </section>
  × N 段，段距 var(--section-gap)

淺色商店幕：白卡 grid + 藍線 icon + ＋號 modal + 比較表
```

### 11.3 動效對應表（Apple 自研 → 你可用的等價物）

| Apple 的 | 復刻方案 |
|----------|---------|
| StaggeredFadeIn | `IntersectionObserver` 加 `.in-view`，CSS `opacity/translateY(24px)` transition，子元素 `transition-delay: calc(var(--i) * 100ms)`；或 GSAP ScrollTrigger `batch()` |
| 滾動 scrub 影片/序列 | GSAP ScrollTrigger `scrub: true` + `<video currentTime>` 或 canvas 影格序列；純 CSS 可用 `animation-timeline: scroll()`（Chrome/Edge 已支援） |
| Sticky 敘事段 | `position: sticky` + 一個超高的 wrapper（Apple 的 cameras 區 19,773px 就是這樣） |
| timed dotnav 輪播 | 每點一個 CSS width animation 當進度條，`animationend` 換下一張 |
| pill tabnav 滑動底盤 | 一個絕對定位的 platter div，JS 量目標 tab 的 `offsetLeft/width` 後 transform 過去 |
| ＋號 modal | `<dialog>` 元素 + backdrop blur |
| 毛玻璃 localnav | `position: sticky; background: rgba(0,0,0,.72); backdrop-filter: blur(20px); border-radius: 24px` |
| 影片策略 | `preload="none" muted playsinline loop`，IntersectionObserver 進場才 `play()`、離場 `pause()`；長片用 hls.js |

### 11.4 做出「Apple 味」的十條鐵則

1. **一屏一事**：每個視窗高度內只有一個標題、一段話、一張圖。資訊密度低到奢侈。
2. **黑講故事、白做生意**：敘事深色、交易淺色，用背景切換告訴讀者現在是哪一幕。
3. **強調色配額制**：主題色全頁 <15 處，只給 eyebrow、大數字、hero 字。
4. **內文敢用 21px semibold**，標題行高壓到 1.05–1.1。
5. **雙色調句子**：灰句子裡藏白重點，讓人「掃讀」也能拿到賣點。
6. **數字是主角**：把規格做成 56px+ 的橙色大字磚，不是表格。
7. **細節全進 modal**：頁面只留一句話 + ＋號，長文案別上頁面。
8. **動效只有 opacity/translate**，0.6–1s、交錯 100ms、無彈跳。
9. **攝影棚級素材**：黑背景、微距、金屬高光；沒有好圖之前別排版（圖是版面的地基）。
10. **每個宣稱掛註腳**，結尾集中交代——專業感的一半來自這種紀律。

### 11.5 素材規格清單（照抄 Apple 的產線）

- 圖片：4 斷點（734/1068/1440/+）× 2 解析度，JPG（照片）/PNG（去背）
- 影片：H.264/HEVC MP4，muted、無音軌、3–8 秒 loop；長片 HLS
- 佔位：1×1 透明 gif → lazy 換圖
- 命名：`hero__{hash}_{breakpoint}_{2x}.jpg`
```

---

## 附：實測組件總表（`data-component-list`）

`FocusManager, DeepLink, LocalNav, Welcome, InlineMediaDefault×4, StaggeredFadeIn×20, MediaCardGallery, MediaCardGalleryControl, TextIconControl×4, ProductViewerCore, ProductViewer, ProductViewerSmall, CustomProductScene, ProductViewerGallery, ProductViewerColorNavGallery, ProductViewerMediaDefault×3, FadeGallery×2, SlideGallery×2, DeepLinkGalleryTab, HardwareZoom, InlineMediaRMFallback×2, InlineCompare, WillChange×25, CaptionTileGallery×3, InlineCompareUpgrade, UpgradeLoadAssets, Card×19, VideoGallery×2, Modal×16, ScrollGallery×2, Index, ContextualCompare`

外掛腳本僅：自研 `head.built.js` / `main.built.js`、globalnav/footer、analytics、`hls.js 2.920.4`。無任何第三方動畫/UI 框架。
