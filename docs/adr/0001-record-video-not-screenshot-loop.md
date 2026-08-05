# ADR-0001：動畫證據用錄影抽幀，不用連續截圖

- 狀態：已接受
- 日期：2026-07-31
- 情境：`/watch-ui` skill 設計

## 問題

要讓 Claude「看見」網頁動畫過程，必須把動態畫面轉成一疊靜態畫格。Playwright 有兩條路：

- **A. 錄影 → 抽幀**：`recordVideo` 產出 `.webm`，再抽幀。
- **B. 連續截圖**：動畫進行中迴圈呼叫 `page.screenshot()`。

## 決策

採 A。

## 理由

1. **抽幀邏輯完全重用。** `/watch`（bradautomates/claude-video，MIT）已安裝於本機，其 `watch.py` 接受本機檔案路徑，並提供 `--fps`、`--no-dedup`、`--start/--end`、`--out-dir`。錄出影片後直接轉交，不必自行實作抽幀、去重與報告格式。

2. **截圖速度追不上動畫。** `page.screenshot()` 單張約 50–200ms 且阻塞主執行緒。一個 300ms 轉場僅能取得 2–3 張，且截圖本身會拖慢頁面、使動畫時序失真。錄影由瀏覽器層處理，不干擾頁面執行。

3. **時序保真。** 錄影保留真實播放時序；截圖迴圈得到的是「被觀測行為擾動後」的動畫。

## 後果

- 必須帶 `--no-dedup` 呼叫 `watch.py`。預設去重會刪掉相鄰的動畫中間態，正是本工具唯一在意的資訊。這是本決策最容易踩的坑。
- 錄影檔需等 `context.close()` 才落地，無法邊錄邊看。
- 錄的是整個 viewport，無法只錄單一元素（見 CONTEXT.md「Viewport Recording」）。
- 依賴 Playwright 自帶的 ffmpeg（`AppData\Local\ms-playwright\ffmpeg-*`），已確認存在。

## 已考慮但未採用

**兩種都實作、依情境切換**：過早抽象。先讓 A 穩定運作，真正遇到「需精準捕捉單一瞬間」的需求再加 B。
