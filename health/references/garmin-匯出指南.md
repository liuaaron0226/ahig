# Garmin Vivoactive 5 資料匯出指南

> 目的：把手錶的睡眠與運動資料交給本機 Claude 分析。
> 查證日期：2026-08-08。Garmin 的網頁 UI 常改版，路徑若對不上以實際畫面為準。

---

## 安全紅線（先講清楚）

**Claude 不會、也不能代你登入 Garmin Connect 輸入帳號密碼。** 這條沒有例外，即使你主動提供密碼也一樣。

所以底下所有方案都是同一個形狀：**你自己操作拿到檔案 → 放進資料夾 → Claude 讀檔分析**。
需要密碼的開源工具（方案 5）也是**你自己在本機終端機跑**，密碼只留在你的電腦上，不經過 Claude。

---

## 首選推薦

**主力：方案 3（帳號完整資料匯出）。**
點四五下就送出申請，24–48 小時後信箱收到一包 ZIP，裡面有全部歷史的睡眠分期、Body Battery、壓力、HRV、SpO2（JSON）＋所有運動 FIT 檔。零安裝、零密碼外流、資料最完整。

**過渡：先跑方案 1（App 截圖）。**
匯出在等的這一兩天，先截 5–6 張關鍵畫面給 Claude，當天就能開始聊。

**之後要每天自動更新再考慮方案 5（GarminDB）**，在那之前不用裝任何東西。

---

## 方案對照

| # | 方案 | 費工程度 | 產出格式 | 睡眠分期 | 歷史範圍 | 需密碼 |
|---|------|---------|---------|---------|---------|--------|
| 1 | App 截圖 | ★☆☆☆☆ | PNG | 有（圖） | 看你截幾張 | 否 |
| 2 | 網頁單筆活動匯出 | ★★☆☆☆ | FIT / TCX / GPX | 無（只有運動） | 一次一筆 | 否 |
| 3 | **帳號完整匯出** | ★★☆☆☆ | JSON + FIT（ZIP） | **有（數值）** | **全部** | 否 |
| 4 | 手錶 USB 直接拉檔 | ★★★☆☆ | FIT | 有（需解析） | 僅近期 | 否 |
| 5 | 開源工具 | ★★★★☆ | SQLite / JSON | 有（數值） | 全部＋可自動更新 | **是（你自己輸入）** |
| 6 | Health API | 不可行 | — | — | — | — |

---

## 方案 1：Garmin Connect App 截圖（最省事）

門檻最低，五分鐘搞定，適合「今天就想聊」。

### 最有分析價值的 6 張

1. **睡眠 → 某一晚的詳細頁**：睡眠分數（0–100）＋ 深／淺／REM／清醒 分期長條圖
2. **同一頁往下捲**：過夜血氧（Pulse Ox）曲線 ＋ 呼吸速率／呼吸變化（breathing variations）
   → 這張對評估睡眠呼吸中止風險最關鍵，**前提是你已開啟 During Sleep 模式**（見文末）
3. **HRV 狀態頁**：夜間 HRV 平均值 ＋ 個人基線區間（平衡／低／不平衡）
4. **Body Battery 24 小時曲線**：起床值、最高值、睡前最低值
5. **睡眠週檢視 / 月檢視**：看入睡與起床時間的規律度，比單晚有用得多
6. **運動**：活動列表（近一週）＋ 任一筆重點活動的摘要頁（配速、心率區間分布）

### 限制

- Claude 只能「看圖估讀」，讀不到精確數值，也無法做統計計算
- **截圖務必讓日期入鏡**，否則多張圖無法對齊時間軸
- 深色模式下細線圖表對比低，淺色模式截圖辨識度較好

---

## 方案 2：Connect 網頁單筆匯出

### 運動（可行）

1. 瀏覽器開 `connect.garmin.com`（**手機 App 完全不提供任何格式的檔案匯出**）
2. 左側 **Activities** → 點開某一筆活動
3. 右上角**齒輪圖示**（部分版面是三個點）→ 選擇：
   - `Export Original` → 原始 **FIT**（資訊最完整，Claude 可解析）
   - `Export as TCX` → 含心率的 XML
   - `Export as GPX` → 只有軌跡，健康分析用處小

**單筆活動沒有 CSV 選項**（CSV 只出現在活動「列表」的批次匯出）。

### 睡眠（不確定，需你自己確認）

論壇上有使用者提到：Connect 網頁 **Sleep** 頁面的單日檢視右上角有齒輪圖示，可匯出該夜睡眠分期的 FIT（下載為 ZIP）。

⚠️ **但這說法出自 2016 年的討論串，且同串有使用者回報在 Chrome 上找不到該選項。我無法確認 2026 年的網頁版還有沒有這個入口。** 你打開看一眼，有就用，沒有就走方案 3。

即使有，也是**一天一次、無法批次**，不值得為了整月資料這樣點。

---

## 方案 3：帳號完整資料匯出（GDPR 匯出）★ 首選

### 步驟

1. 瀏覽器登入 `connect.garmin.com`
2. 右上角你的頭像／名字 → **Account Settings**（帳號設定）
   - 部分地區會導向 Garmin **Account Center**（`account.garmin.com`）
3. 找到 **Data Management**（資料管理）／**Account management** 區塊
4. **Export Your Data** → **Request Data Export**（或「Request Data」）
5. 等 email 通知，點連結下載 ZIP

> 各家教學對第 3 步的區塊名稱說法不一（Data Management / Account management），因地區與改版而異。認「Export Your Data」這個字串就對了。

### 等多久

- 一般 **24–48 小時**
- 資料量大的帳號可能到 **30 天**
- 送出後**在完成前無法再申請一次**
- 沒收到記得翻**垃圾郵件匣**

### 拿到什麼

**格式只有 FIT 和 JSON，沒有 CSV。**

ZIP 解開後大致長這樣（資料夾名稱的大小寫、底線／連字號在不同帳號間略有差異，以你實際解壓的為準）：

```
DI_CONNECT/
├── DI-Connect-Wellness/          ← 睡眠、壓力、Body Battery、HRV、SpO2
│   └── 2024-09-22_2024-12-31_<id>_sleepData.json
├── DI-Connect-Fitness/
│   └── ..._summarizedActivities.json    ← 活動名稱對照表
└── UploadedFiles_0-_Part1.zip    ← 巢狀 ZIP，裡面才是運動 FIT 檔
    UploadedFiles_0-_Part2.zip
    ...
```

重點：
- **睡眠資料在 `DI-Connect-Wellness/` 底下的 `*_sleepData.json`**，是**每晚計算後的摘要**（含分期），不是逐秒原始感測波形
- 運動 FIT 檔藏在**巢狀 ZIP** 裡，要再解一層
- FIT 檔名是時間戳，看不出是什麼運動，要靠 `summarizedActivities.json` 對照

### 已知缺漏

Garmin 不會把這些放進匯出包：
- 訓練狀態歷史（Base / Build / Peak 標籤）
- 生理基線趨勢（VO2 max 的歷史演進）
- 已儲存的路線（courses）

### 給 Claude 的建議

解壓後把 `DI-Connect-Wellness/` 整個資料夾丟到 `Desktop\claude\health\data\garmin\`，Claude 直接讀 JSON 做統計。運動 FIT 檔量大，建議只挑要分析的那幾筆。

---

## 方案 4：手錶 USB 直接拉檔（完全離線）

不碰 Garmin 伺服器、不用登入任何東西，最保護隱私。

### 步驟

1. 用充電線把 Vivoactive 5 接到電腦
2. **Vivoactive 5 是 MTP 裝置**（不是傳統 USB 隨身碟模式）
   - **Windows 11 原生支援 MTP**，直接開檔案總管就看得到手錶
   - macOS 的 Finder 認不到，要裝 OpenMTP 之類的工具
3. 進手錶內部儲存的 `GARMIN` 資料夾，把 FIT 檔複製到本機硬碟
   - ⚠️ **我沒查證到 Vivoactive 5 的確切子資料夾清單**。Garmin 各機種常見的有 `Activity/`（運動）、`Monitor/`（全天監測，睡眠在這裡）、`TempFIT/`。插上去自己看，不要照抄。
4. **一定要先複製到本機硬碟再處理** — 腳本無法直接對 MTP 路徑操作

### 產出

FIT 檔。GarminDB 作者確認這些檔案裡有「sleep level by time、oxygen levels（若手錶支援）、breathing rates、heart rate」，也就是**不經過 Garmin 伺服器也能重建睡眠分期與血氧**。

### 限制

- **手錶本機只保留近期資料**（通常兩週上下，Garmin 未公開確切天數），同步後會被覆寫 — 拿不到長期歷史
- FIT 是二進位格式，要用 `fit-tool`、`fitdecode`（Python）或 GarminDB 解析才能讀
- GarminDB 作者自己說換機後就沒再測過 copy 模式，這條路的維護狀態不明

---

## 方案 5：開源工具（需要密碼 — 你自己跑，不經由 Claude）

> **⚠️ 這兩個工具都需要你的 Garmin Connect 帳號密碼。**
> **請你自己在本機終端機執行，密碼絕對不要貼進和 Claude 的對話。**
> Claude 只負責讀它們產出的資料庫／JSON 檔。

### 5-1. `python-garminconnect`（cyberjunky）

非官方 API wrapper，走 Garmin 手機 App 用的同一套 SSO 流程。

```bash
pip install garminconnect
```

- Token 存在 `~/.garminconnect/garmin_tokens.json`，會自動更新，**不必每次重打密碼**
- 支援 MFA（會跳出來要你輸入一次性驗證碼）
- 相關方法：`get_sleep_data()`、`get_hrv_data()`、`get_body_battery()`、`get_spo2_data()`

**風險**：這是逆向工程來的非官方介面，**Garmin 一改後端就會壞**。社群歷史上多次出現登入全面失效（例如 2026-03 有 401 Unauthorized 的 issue）。版本以 PyPI 上的最新為準，遇到登入失敗先升級套件再說。

### 5-2. GarminDB（tcgoetz）

包裝層更高，直接把 Garmin Connect 資料倒進 **SQLite** — 對 Claude 來說是最好分析的格式。

```bash
pip install garmindb
garmindb_cli.py --all --download --import --analyze          # 首次全抓
garmindb_cli.py --all --download --import --analyze --latest # 之後增量更新
```

- 支援睡眠、體重、靜止心率、每日監測資料
- 也能吃方案 4 從手錶拉下來的 FIT 檔（離線模式）
- **⚠️ 安全提醒**：帳密要寫進設定檔（`GarminConnectConfig.json`）且是**明文**。建議在 Garmin 帳號開啟 MFA，並認知這個檔案等同你的密碼。

**這是想做「每日自動更新健康儀表板」時的正解**，但只做一次性分析的話，方案 3 更省事也更安全。

### 5-3. Gadgetbridge（不建議）

Android 開源 App，可把 Vivoactive 5 的資料（含睡眠分期）存進本機 SQLite 匯出。

**但代價很高**：Gadgetbridge 是要**取代** Garmin Connect App 的，你得把手錶從官方 App 解除配對。這會讓你失去 Sleep Coach、HRV Status、Body Battery 等 Garmin 雲端算出來的指標 — 而那些正是你想分析的東西。**除非你本來就想脫離 Garmin 生態系，否則別走這條。**

---

## 方案 6：Garmin Health API / Developer Program（❌ 不可行）

**個人用不了，直接放棄。**

Garmin Connect Developer Program 官方 FAQ 明講：

- **不開放個人使用**，只給企業（公司、大學、醫院、研究機構等法人）
- 申請要填公司背景、用途、資料處理方式
- 審核約 2 個工作天

另有第三方來源稱該計畫目前「暫停收件」，但 Garmin 官方 FAQ 頁面顯示仍正常受理 — **說法不一，不過「個人不可申請」這點兩邊一致**。

---

## Vivoactive 5 的血氧（Pulse Ox）確認

### ✅ 支援，但**預設是關閉的**（為了省電）

Vivoactive 5 有三種追蹤模式（官方手冊確認）：

| 模式 | 行為 |
|------|------|
| **All Day** | 白天不活動期間也持續量測 |
| **During Sleep** | **睡眠期間每分鐘量測一次** ← 睡眠分析要開這個 |
| On Demand | 關閉自動量測，只能手動單次測 |

### 怎麼開

**手錶上**：長按 B 鍵 → `Settings > Watch Sensors > Pulse Ox > Tracking Mode` → 選 **During Sleep**（或 All Day）

**手機 App 上**：Device Settings → Vivoactive 5 → Pulse Ox → 打開 Sleep 或 All-Day

⚠️ **開啟後會明顯耗電**，這是官方註明的代價。

⚠️ **重要**：如果你以前沒開過，**過去的資料就是沒有血氧**，不管用哪種方案匯出都拿不到。今天就去開，累積至少 7–14 晚再來分析才有意義。

### 睡眠期間還會記錄什麼

官方手冊：「Sleep statistics include total hours of sleep, sleep stages, sleep movement, and sleep score.」
另外 —「You must turn on pulse oximeter sleep tracking to detect breathing variations.」
即**過夜呼吸變化（breathing variations）也綁在 Pulse Ox 睡眠追蹤上**，一起開才有。

Vivoactive 5 同時支援 **HRV Status**、**Body Battery**、**Sleep Score（0–100）** 與 **Sleep Coach**。

---

## ⚠️ 醫療免責聲明（請務必看）

**Garmin Pulse Ox 不是醫療器材，不能用來診斷任何疾病，包括睡眠呼吸中止症（OSA）。**

官方手冊自己就註明：

> 「The accuracy of the pulse oximeter reading can vary based on your blood flow, the watch placement on your wrist, and your stillness.」

腕式光學血氧的先天限制：
- 夜間手腕壓迫、姿勢變換、體溫下降造成末梢血流減少 → 大量假性低讀
- 深色刺青、手錶戴太鬆／太緊都會嚴重影響讀數
- **Garmin 的「睡眠分期」是靠心率＋動作推估的，不是腦波（PSG）**，與臨床標準有明顯落差

**這份資料能做什麼**：看趨勢、找規律、當作「要不要去看醫生」的參考訊號（例如連續多晚出現規律的血氧下降＋高呼吸變化＋白天嗜睡）。

**這份資料不能做什麼**：判定你有沒有睡眠呼吸中止症。**只有醫院的睡眠多項生理檢查（PSG）或合格的居家睡眠檢測（HSAT）才能診斷。**

Claude 的分析同理 — 那是資料歸納，不是醫療意見。有疑慮請掛胸腔內科／耳鼻喉科／睡眠中心。

---

## 建議工作流（總結）

```
今天  → 1. 手錶開 Pulse Ox「During Sleep」（否則之後永遠沒血氧資料）
        2. 網頁送出 Export Your Data 申請
        3. App 截 6 張關鍵畫面 → 丟給 Claude 先聊

1–2 天後 → 收信下載 ZIP
          → 解壓 DI_CONNECT/DI-Connect-Wellness/ 到
             Desktop\claude\health\data\garmin\
          → Claude 讀 sleepData.json 做完整統計分析

之後   → 想做每日自動更新，再考慮自己裝 GarminDB
```

---

## 誠實標註：本文的不確定項

1. **Connect 網頁睡眠頁的齒輪匯出** — 依據是 2016 年論壇貼文，2026 年是否還存在**未經確認**，同串有人找不到
2. **匯出 ZIP 的資料夾名稱** — 不同來源寫法不一致（`DI-Connect-Wellness` vs `DI_Connect_Wellness`），且各帳號略有差異，以實際解壓為準
3. **Vivoactive 5 手錶內部確切資料夾路徑** — 查不到官方文件，只確認它是 MTP 裝置。方案 4 的資料夾名稱是 Garmin 通用慣例，**不保證你機上一模一樣**
4. **手錶本機保留天數** — 查不到官方數字，「約兩週」是社群經驗值
5. **Garmin Developer Program 是否暫停收件** — 兩來源說法衝突（不影響結論，個人本來就不能申請）
6. **`python-garminconnect` 當前可用性** — 非官方 API，隨時可能因 Garmin 改版失效，查證當下無法確認最新狀態

---

## 參考來源

- [vívoactive 5 手冊 — Changing the Pulse Oximeter Tracking Mode](https://www8.garmin.com/manuals/webhelp/GUID-5D183A14-BB43-4A9B-B441-5F824214CE40/EN-US/GUID-C5EB0E62-7C00-4AC6-96AE-CF9079CD5D90.html)
- [vívoactive 5 手冊 — Sleep Tracking](https://www8.garmin.com/manuals/webhelp/GUID-5D183A14-BB43-4A9B-B441-5F824214CE40/EN-US/GUID-70D41BFB-2BB2-4933-BF95-47FF63140112.html)
- [vívoactive 5 手冊 — Getting Pulse Oximeter Readings](https://www8.garmin.com/manuals/webhelp/GUID-5D183A14-BB43-4A9B-B441-5F824214CE40/EN-US/GUID-987F8345-58B3-489E-98ED-E6999ACBB630.html)
- [Garmin Connect Developer Program FAQ](https://developer.garmin.com/gc-developer-program/program-faq/)
- [How to Export Garmin Data in 2026 (Gneta)](https://www.gneta.app/blog/export-garmin-data-guide)
- [How to Export Garmin Data: GPX, TCX, FIT & CSV (FitMesh)](https://www.fitmesh.fit/en/blog/export-garmin-data)
- [Garmin Forums — Sleep data export from Garmin Connect](https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/119054/sleep-data-export-from-garmin-connect)
- [Garmin Forums — vivoactive internal storage (MTP)](https://forums.garmin.com/sports-fitness/healthandwellness/f/vivoactive-5-series/399541/vivoactive-internal-storage)
- [cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect)
- [tcgoetz/GarminDB](https://github.com/tcgoetz/GarminDB)
- [GarminDB Discussion #156 — offline local-only analysis](https://github.com/tcgoetz/GarminDB/discussions/156)
- [Gadgetbridge — Garmin watches](https://gadgetbridge.org/gadgets/wearables/garmin-watches/)
- [Exporting Files from Garmin Connect (Strava Help)](https://support.strava.com/en-us/articles/15402167-exporting-files-from-garmin-connect)
- [Garmin Pulse Ox explained (Wareable)](https://www.wareable.com/garmin/garmin-pulse-ox-blood-oxygen-spo2-explained)
