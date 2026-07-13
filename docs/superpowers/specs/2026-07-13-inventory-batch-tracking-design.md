# 庫存與批次追蹤（Module 2）— 架構設計 Spec

日期：2026-07-13
狀態：待使用者確認
前置模組：物料主檔與編碼引擎（已完成，`C:\Users\User\Desktop\bixlink-wms`）

## 1. 背景與目標

延續總體設計文件（`2026-07-13-bixlink-wms-design.md`）module 2「庫存與批次追蹤」。本模組建立 Partner、Site、Location、Batch、InventoryTransaction、BatchAllocation 的 schema 與服務層，**用小規模測試資料以 TDD 驗證，不接入 7,661 筆真實歷史資料**（那是下一個模組：歷史資料遷移，依賴本模組先把 schema 定案並驗證過）。

## 2. 範圍

包含：schema、服務層函式（createPartner/createSite/createLocation/createBatch/createTransaction）、對應 API route、庫存結存查詢函式。

明確排除：FIFO/FEFO 配撥引擎、批次到期日提醒、跨系統對帳、歷史資料匯入（下一模組）。

## 3. 資料模型

### Partner（往來對象主檔）
`id, name(正式名稱, unique), aliases(String[] JSON), type(String[] JSON: 供應商/客戶/代工廠可複選), country, defaultCurrency, isSite(Boolean), isActive(Boolean @default(true))`

### Site（據點）
`id, name(unique), partnerId(nullable FK→Partner), isActive(Boolean @default(true))`

### Location（儲位）
`id, siteId(FK→Site), code(nullable — 正規儲位代碼如 H-15), legacyText(nullable — 承接舊資料裡的雜亂寫法), isActive(Boolean @default(true))`
`@@unique([siteId, code])`（code 非 null 時，同據點內不可重複）

### Batch（批次/Lot）
`id, itemId(FK→Item), batchNo(nullable — 批號/Date code), sourcePartnerId(nullable FK→Partner), receivedDate(nullable), sourceAttribute(enum: PURCHASED/FREE_SAMPLE/CUSTOMER_SUPPLIED), certRefs(nullable — JSON 陣列存文件參照，UN38.3/MSDS 等)`

### InventoryTransaction（庫存異動 — 不可變）
`id, date, type(enum: IN/OUT/ADJUST_INCREASE/ADJUST_DECREASE/TRANSFER), itemId(FK→Item), batchId(nullable FK→Batch), quantity(Int, 一律為正數，方向由 type 決定), siteId(FK→Site), locationId(nullable FK→Location), projectId(nullable — 本模組先不建 Project 表，暫存 String), issuedTo(nullable String — 專案代號或人名), orderNo(nullable), remark(nullable), partnerId(nullable FK→Partner), transferGroupId(nullable — 見下方 TRANSFER 設計), createdAt`

**TRANSFER 設計**：不在單一列存來源/目的兩個 Site，而是拆成兩筆配對交易（來源站 OUT + 目的站 IN），共用同一個 `transferGroupId` 方便介面把兩筆顯示在一起。這樣結存計算永遠只需要「對單一 siteId 加總」，不用為 TRANSFER 另外寫查詢邏輯。

### BatchAllocation（批次分配 — 追溯用途）
`id, batchId(FK→Batch, 來源批次), finishedItemId(FK→Item, 分配到的成品料號), quantity, transactionId(nullable FK→InventoryTransaction, 對應的出庫異動)`

這是 Batch 與 Item 之間的多對多中介表：一批原料可以分給多個成品料號（fan-out），一個成品料號的生產也可能耗用多個批次（fan-in），quantity 是這條邊的權重。用途是料件追溯——例如查「這批電芯用在了哪些成品」或「這個成品用了哪些電芯批次」。取代 Excel `2026` 分頁的 T~AK 寬欄位設計。

### Item（既有表，本模組要補回一個遺漏欄位）
原始總體設計文件在 Item 實體定義了「啟用狀態」欄位，但 module 1 實作時漏掉了。本模組的 migration 要把它補上：
`isActive Boolean @default(true)`（module 1 沒做的技術債，在此一併還清，不是本模組的新需求）

## 4. 業務規則

### 4.1 單位（UOM）
**所有 Quantity 一律以 `Item.unit` 定義的最小單位記錄，不做單位換算。** 一卷 3000pcs 的物料，入庫時 quantity 必須填 3000，不能填 1。本階段不支援「卷/盤/kg」等多單位換算，這是刻意的 YAGNI：換算係數表是另一個功能，等真的有需求再做。

### 4.2 負庫存防呆
**初期採嚴格阻擋（Option A）**：`createTransaction` 建立 OUT 交易時，會先計算目前結存：
- 若交易指定了 `batchId`：計算「該 batch 在該 site 的結存」（該 batch 所有 IN/OUT/ADJUST 加總）
- 若未指定 `batchId`：計算「該 item 在該 site 的結存」（不分批次，全部加總）

若 `quantity` 超過可用結存，API 回傳 400 錯誤並拒絕建立交易。這會強制「先入帳、再領料」的紀律，避免帳實脫鉤。`ADJUST_DECREASE`（例如盤點發現實際數量比帳上少）不受此上限檢查——它本來就是用來讓帳面對齊實體現況，不該因為「帳上數字不夠扣」而被擋下來。

結存計算公式：`SUM(IN) + SUM(ADJUST_INCREASE) − SUM(OUT) − SUM(ADJUST_DECREASE)`（TRANSFER 已拆成配對的 OUT/IN，套用同一公式即可，不用另外處理）。

### 4.3 交易不可變性（Immutability）
**InventoryTransaction 沒有 UPDATE 或 DELETE API。** 打錯一筆出庫單的更正方式，是建立一筆反向的 ADJUST 交易沖銷，而不是修改或刪除原始記錄。這是稽核軌跡（Audit Trail）的基本要求——查帳時要能重播每一筆異動，歷史記錄不能憑空消失或被覆寫。

### 4.4 軟刪除
Partner、Site、Location、Item 都用 `isActive` 布林欄位表示啟用狀態，**沒有實體刪除（Hard Delete）API**。這些主檔一旦被 InventoryTransaction 引用過，刪除會讓歷史交易的外鍵找不到對應資料。「刪除」在應用層一律等於把 `isActive` 設為 `false`（新交易的下拉選單不再顯示它，但既有關聯資料完整保留）。

## 5. API 介面

服務層函式：`createPartner`、`createSite`、`createLocation`、`createBatch`、`createTransaction`（內建負庫存檢查）、`getStockBalance(itemId, siteId, batchId?)`（計算結存，供 4.2 的檢查與查詢共用同一邏輯，避免兩處各寫一份加總規則）。

對應 API route：`/api/partners`、`/api/sites`、`/api/locations`、`/api/batches`、`/api/transactions`（POST 建立 / GET 列表，比照 module 1 `/api/items` 的規格；無 PATCH/DELETE，呼應 4.3、4.4）。

## 6. 測試策略

延續 module 1 做法：TDD、真實 SQLite test.db（不 mock）、小規模手打測試資料驗證每條規則（負庫存拒絕、ADJUST 不受限、TRANSFER 配對交易、結存計算正確、軟刪除後舊交易仍可查詢關聯資料）。不接觸真實 Excel 資料——那是下一模組的工作，會直接匯入到這裡驗證過的 schema。

## 7. 下一步

本模組完成並驗證後，下一個模組是「歷史資料遷移」：把 7,661 筆真實交易、Cell 批次記錄等匯入本模組定義的 Batch/InventoryTransaction/BatchAllocation，含 MigrationQuarantine 隔離區機制（見總體設計文件第 7 節）。
