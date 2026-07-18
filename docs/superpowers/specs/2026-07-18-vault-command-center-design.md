# V.A.U.L.T. 指揮中心設計（project-golem 語音層 + 統一儀表板）

日期：2026-07-18
狀態：使用者已核准設計，進入實作
參考：denghao.substack.com「5 步驟建構 Fable 5 AI 個人作業系統」

## 目標

在 project-golem 上補齊文章五步驟中缺少的兩塊：語音層（聽 + 說）與
V.A.U.L.T. 風格統一指揮中心頁面。golem 現有程式碼只加不改。

## 已確認的決策（使用者選定）

- 擴充 project-golem，不從零建新專案
- TTS 用 Edge-TTS 雲端（台灣腔 HsiaoChenNeural），STT 全本地（faster-whisper）
- 語音入口：儀表板麥克風按鈕（按住說話），不做全域熱鍵、不做喚醒詞
- 本地模型：deepseek-r1:8b（已裝入 Ollama，模型庫已遷至 D:\ollama\models）
- Grok：無本地可跑版本，排除

## 架構

### 1. voice-service（新增 Python FastAPI sidecar）

位置：`project-golem/apps/voice-service/`

- `POST /stt`：接收音訊 blob → faster-whisper（small 模型、中文、GPU int8）→ 回傳文字
- `POST /tts`：接收文字 → edge-tts（zh-TW-HsiaoChenNeural）→ 回傳 mp3 串流
- `GET /health`：前端用來顯示語音服務在線/離線徽章
- 獨立 requirements.txt 與啟動腳本；不改動 golem 的 Node 啟動流程

### 2. VAULT 頁面（新增 dashboard route）

位置：`web-dashboard/src/app/dashboard/vault/page.tsx`

深色未來感指揮中心，四區塊（照文章 V.A.U.L.T. 概念）：

- 中央語音區：按住說話按鈕、錄音波形、TTS 播放動畫、對話文字紀錄
- Metrics：Ollama 模型清單、golem 服務健康度、記憶條目數
- Skills：golem 現有 skills 資料，顯示啟用中技能
- Schedule：golem 現有 calendar 模組資料

### 3. 語音資料流

按住錄音（MediaRecorder）→ voice-service /stt → 文字送 golem 現有 chat
流程（不另建大腦）→ 回覆文字 → voice-service /tts → 前端播放。

### 4. 本地模型整合

golem 已有 OllamaClient.js 與模型路由；把 deepseek-r1:8b 加入模型設定，
VAULT 頁提供「本地大腦 / 雲端大腦」切換。

## 錯誤處理

- 麥克風權限被拒：顯示提示，退回打字輸入
- voice-service 未啟動：離線徽章，語音按鈕 disabled，聊天仍可打字
- Edge-TTS 連不上（斷網）：只顯示回覆文字，不發聲，不報錯干擾

## 驗證（done 的定義）

- voice-service 三個 endpoint 的 smoke test 通過（中文語句實測 STT/TTS）
- deepseek-r1:8b 實際推理測試通過
- VAULT 頁在瀏覽器實測：按住說話 → 得到語音回答，四區塊有真實資料
- golem 原有功能不受影響（現有程式碼零修改）
