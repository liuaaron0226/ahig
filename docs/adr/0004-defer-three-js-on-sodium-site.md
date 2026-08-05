# ADR-0004：sodium-site 的 three.js 改為 defer 載入

- 狀態：已接受
- 日期：2026-07-31
- 情境：`bixlink-sodium-site/index.html` 首屏白畫面

## 問題

`/watch-ui` 首次實測時，逐幀檢視發現開場約 1–2 秒全白，使用者要等到約第 6 幀才看得到內容。

量測後確認並非動畫問題（body 與 hero 的 `opacity` 全程都是 `1`），而是資源載入阻塞：

| 資源 | 大小 | 載入方式 |
|---|---:|---|
| `lib/three.min.js` | 594 KB | 同步阻塞 |
| `lib/gsap.min.js` | 71 KB | 同步阻塞 |
| `lib/ScrollTrigger.min.js` | 42 KB | 同步阻塞 |

`three.min.js` 是其他兩者總和的五倍，但全站只服務 `#cell3d` 一個 3D 電池模型。

## 決策

`three.min.js` 加上 `defer`。`init3D` 由立即執行的 IIFE 改為具名函式，並在 three.js 就緒後才呼叫：

```js
if(window.THREE) init3D();
else window.addEventListener('DOMContentLoaded', init3D);
```

GSAP 與 ScrollTrigger 維持同步載入——它們較小，且進場動畫需要在首次繪製前就位，延後會造成內容閃現。

## 理由

`#cell3d` 位於 hero 區，屬首屏可見，因此不適合延後到捲動才載入（會留下空洞）。但它不需要**阻塞文字內容的繪製**：文字先出現、3D 模型稍後補上，是比整頁空白更好的載入體驗。

## 量測結果

| 指標 | 修改前 | 修改後 |
|---|---:|---:|
| 文字首次可見 | 約 1648ms（`readyState` complete） | **513ms** |
| 3D canvas 出現 | 同上 | 1261ms |

`/watch-ui` 逐幀複驗：修改前第 2 幀仍全白；修改後第 2 幀已是完整 hero 區，第 3 幀 3D 模型補上。

## 後果

- `defer` 腳本保證在 `DOMContentLoaded` 前執行完畢，因此上述 fallback 不會漏接。
- 若日後把 `init3D` 相關程式碼移入外部檔案或改為 `type="module"`，需重新確認初始化時機。
- 錄影的第 1 幀仍為白色，那是 Playwright 從 `page.goto` 結束即開始錄製、瀏覽器尚未首次繪製所致，非網站缺陷。
