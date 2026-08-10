# SmoothUI 研究：作為公司網站建置素材的評估

日期：2026-08-06
來源：https://smoothui.dev/（首頁、/docs/guides、/docs/guides/installation、/docs/templates、/themes、llms.txt、registry JSON 實測）
關聯：上一輪已移植過按鈕 → `button-reference.html`（commit 8024865）

## 一句話結論

SmoothUI 是 MIT 授權的 React 動效元件庫（130 元件＋34 個行銷區塊），它的 34 個 blocks
剛好湊成一整套公司官網（header/hero、features、logo cloud、stats、team、testimonials、
FAQ、CTA、pricing、footer 全有）；但它綁定 React 19＋Tailwind v4＋Motion 技術棧，
與我們現行「單檔 HTML＋GSAP」微網站做法不同，要嘛官網改走 React 專案直接裝，
要嘛延續 button-reference.html 的移植路線——每個元件的完整原始碼都能從
`https://smoothui.dev/r/<name>.json` 直接抓下來，移植成本低。

## 基本盤

- 作者 Eduardo Calvo（educlopez），GitHub 876 stars，MIT 授權、全部免費（含 blocks；首頁的 pricing 卡片只是 block 示範內容，不是真收費）。
- 技術棧：React 19、TypeScript、Tailwind CSS v4（oklch、@theme token）、Motion（前 framer-motion）＋部分 GSAP、shadcn/ui 生態。
- 是 shadcn 官方 registry：`npx shadcn@latest add @smoothui/<name>`，零設定；也有自家互動式 CLI `smoothui-cli`。
- 支援框架：Next.js、Vite、Astro、Remix、TanStack Start（各有官方安裝指南）。
- 裝進來的是原始碼落在 `components/smoothui/` 下，可自由改，無 runtime 套件。
- 深色模式、reduced-motion、無障礙都是預設內建。

## 對公司官網最有價值的：34 個 Blocks（完整清單）

| 區塊 | 數量 | 亮點 |
|------|------|------|
| Header/Hero | 6 | header-4＝rauno.me 風格互動 3D grid hero；header-5＝深色 spotlight hero；header-6＝極簡排版 |
| Features | 3 | features-2＝bento 不對稱網格 |
| Logo Cloud | 4 | logo-cloud-3＝無限跑馬燈（客戶/夥伴 logo 牆） |
| Stats | 2 | 搭配 number-flow 數字滾動 |
| Team | 2 | 網格＋輪播兩款 |
| Testimonials | 3 | 自動輪播、網格、星評三款 |
| FAQ | 4 | 含可搜尋、分類 tab 版本 |
| CTA | 3 | 置中光暈、左右分欄、橫幅三款 |
| Pricing | 3 | |
| Footer | 4 | 從單列極簡到 mega footer |

## 130 個元件中對官網有用的子集

- **文字動效（hero 標題用）**：reveal-text、shine-text、mask-reveal-up、per-character-rise、blur/stagger 系列約 25 款，全部只依賴 `motion`，最容易移植。
- **展示**：infinite-slider、number-flow / price-flow（數字滾動）、reviews-carousel、photo-stack、expandable-cards、glow-hover-card、scrollable-card-stack。
- **互動**：magnetic-button、smooth-button（已移植）、animated-tabs、basic-accordion、animated-file-upload、form（含動畫錯誤訊息）。
- **頁面轉場**：約 15 款 WebGL shader 轉場（Codrops 系列改編），單檔微網站也能參考其 shader 邏輯。
- **AI 類 18 款**（siri-orb、ai-prompt-input、dynamic-island…）：官網用不上，但 golem/VAULT 類專案可回頭挖。

## Theme Studio（/themes）——不用 React 也能用

互動式調 light/dark、字體（sans/serif/mono）、中性色冷暖、radius、accent，
然後「Copy CSS variables」直接輸出 CSS 變數。做品牌 token 起手式很快，
產出物是純 CSS，可直接貼進單檔 HTML 微網站。

## AI 友善度（對我們的工作流很重要）

- `https://smoothui.dev/llms.txt`：130 元件＋34 blocks 的一行式目錄（本檔清單即出自此）。
- `https://smoothui.dev/llms-full.txt`、`llms-components.json`：機器可讀完整目錄。
- `https://smoothui.dev/r/<name>.json`：**含完整 TSX 原始碼、依賴清單、CSS**（已實測 reveal-text：單檔 index.tsx，依賴只有 motion）。
- 公開 API（/api/v1/suggest 等，免 auth）＋ shadcn MCP server 可用。
- 附帶發現：作者另有 ui-craft（agent UI 品質閘門工具），只有 brew cask（macOS），Windows 用不上，略過。

## 限制與注意

- Templates 目前只有一個 Chat 樣板，對官網無用；官網素材以 blocks 為主。
- 綁 Tailwind v4 語法（oklch、@theme），若移植到單檔 HTML 需手動展開 utility class。
- blocks 是英文示範文案，中文字體排版（行高、字重）要自己調。
- 星數 876、單人維護：當「素材庫＋抄法參考」很好，當「長期依賴的框架」風險偏高——但因為程式碼直接落地在自己 repo，此風險實際很低。

## 建議路線

1. **官網若開新 React 專案（Next.js/Vite）**：直接以 SmoothUI blocks 當骨架
   （header-6 或 header-4 ＋ features-2 bento ＋ logo-cloud-3 ＋ stats ＋ testimonials ＋ faq-2 ＋ cta-1 ＋ footer），
   Theme Studio 出品牌 token，一天內可拼出全站雛形。
2. **官網若延續單檔 HTML＋GSAP 路線（現行 BixLink 微網站做法）**：不裝，改移植——
   從 `/r/<name>.json` 抓原始碼，照 button-reference.html 模式轉成無依賴 CSS/JS。
   優先移植對象：文字動效系列（hero 標題）、infinite-slider（logo 牆）、number-flow（數據區）。
3. 兩條路都合法（MIT），選哪條取決於官網要不要上 build 工具鏈——這是下一步唯一要拍板的決策。
