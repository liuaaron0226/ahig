# Maybe Finance 自架評估（截至 2026-07-28）

- 評估標的：[maybe-finance/maybe](https://github.com/maybe-finance/maybe)
- 評估日期：2026-07-28
- 使用者環境：Windows 11、Docker Desktop／WSL2；既有 `signal-desk` 用於 KOL 投資訊號追蹤與語音早報，刻意不與 `project-golem` 耦合
- 來源限制：只採用 Maybe 官方 GitHub repository、GitHub API、官方 Wiki／文件、官方 container package，以及必要原始碼；沒有採用第三方評測、教學或社群整理文

## 結論先行

**建議：先做一次隔離的本機 demo，不建議現在把 Maybe 安裝成正式、長期依賴的個人財務主系統。**

原因不是產品沒有功能，而是它已進入「功能完整但停止維護」的狀態：repository 已 archived，最後程式推送與最終 release 都停在 2025-07-24；官方明說 v0.6.0 是 working, “as-is” final release，之後不主動維護、也不接受貢獻。[Repo metadata](https://api.github.com/repos/maybe-finance/maybe) · [v0.6.0 final release](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0) · [latest commits](https://api.github.com/repos/maybe-finance/maybe/commits?per_page=10)

對此使用者最關鍵的限制是：

1. **台灣銀行與券商沒有實用的自動同步路徑。** Maybe 的 Plaid 程式碼只開放 US/CA 與一組歐洲國家，沒有 TW；台灣資料主要只能靠 CSV 或手動維護。[Plaid country codes](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/plaid.rb#L201-L210) · [CSV import types](https://github.com/maybe-finance/maybe/blob/main/app/models/import.rb#L1-L15)
2. **投資與加密資產可記錄，但全球行情完整性不可靠。** 官方最終說明承認全球證券、匯率與市場資料是未完全解決的核心難題；找不到行情時會建立不抓價格的 offline ticker。Crypto 則主要是手動建立一個有名稱、幣別與餘額的資產帳戶，沒有看到交易所、錢包或鏈上同步 provider。[v0.6.0 reflections](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0) · [offline security resolver](https://github.com/maybe-finance/maybe/blob/main/app/models/security/resolver.rb#L8-L43) · [Crypto model](https://github.com/maybe-finance/maybe/blob/main/app/models/crypto.rb) · [account form](https://github.com/maybe-finance/maybe/blob/main/app/views/accounts/_form.html.erb#L7-L18)
3. **自架不是單一無狀態容器。** 官方 Compose 實際啟動 `web`、`worker`、PostgreSQL、Redis 四個 service，並使用三個 named volume；使用者要自己負責秘密、備份、升級、TLS、Docker Desktop／WSL2 資源與故障排查。[compose.example.yml](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml)
4. **財務軟體停止安全更新的風險高於一般個人工具。** Repository 沒有 `SECURITY.md`，GitHub metadata 顯示 issues 與 discussions 都已停用；即使目前能正常跑，也沒有可信的後續漏洞修補與相依套件維護管道。[Repo metadata](https://api.github.com/repos/maybe-finance/maybe) · [community profile](https://api.github.com/repos/maybe-finance/maybe/community/profile)
5. **它與 `signal-desk` 主要互補，不是替代品。** Maybe 是資產負債表、交易、預算、淨值與持倉帳本；`signal-desk` 是外部 KOL 訊號評估與語音早報。兩者只在「投資脈絡」有交集，資料模型與主要工作流不同。

若 demo 後發現核心需求其實是「台灣銀行／券商自動同步、可靠行情、低維運」，結論應直接升級為 **不要安裝**；Maybe 不會因正式部署就補上這些能力。

---

## 1. 產品定位與核心功能

Maybe 的定位是自架、開源的個人財務管理系統，而不是交易下單平台、投資訊號平台或純記帳 App。官方最終 release 列出的 self-hosted 功能包括：[v0.6.0 feature list](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0)

- 淨值趨勢與個人資產負債表 dashboard
- 交易搜尋、篩選、批次修改與明細
- 各帳戶餘額趨勢、reconciliation 與餘額變動分解
- 月度預算、分類平均支出與收入摘要
- 多幣別
- 帳戶、交易、投資 trades 的 CSV 匯入
- Categories、Tags、Merchants
- 自動分類、商家辨識等 rules
- household 成員邀請
- 2FA
- 有金鑰管理的 API
- 可選的 AI 財務聊天

它處理的帳戶類型涵蓋存款、投資、Crypto、房產、車輛、其他資產、信用卡、貸款與其他負債。[Accountable types](https://github.com/maybe-finance/maybe/blob/main/app/models/concerns/accountable.rb#L1-L10)

產品設計上有幾個值得肯定的地方：

- Transfer 是一等資料型別，不必硬塞進支出分類；信用卡付款等可避免預算重複計算。
- 可標記 one-time expense，避免污染平均支出與預算。
- 帳戶可直接 reconcile 到新餘額，而不必製造難以分類的 adjustment transaction。
- 投資可記錄 buy/sell、利息、存入與提領，並能用 provider ticker 或手動 offline ticker。[trade form](https://github.com/maybe-finance/maybe/blob/main/app/models/trade/create_form.rb)

這些能力讓它比單純 spreadsheet 更像一個完整的「個人財務 ledger + analytics engine」。但官方自己也把最終版本稱為接近完整、仍存在一致性與資料 provider 問題的核心 engine，而不是持續支援的成品服務。[v0.6.0 final release](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0)

## 2. 2026-07-28 的維護狀態與成熟度

### 2.1 客觀狀態

| 指標 | 2026-07-28 狀態 | 第一手來源 |
|---|---|---|
| Repository | **Archived / read-only** | [GitHub API](https://api.github.com/repos/maybe-finance/maybe) |
| Active maintenance | 官方 README 明示已停止 | [README](https://github.com/maybe-finance/maybe/blob/main/README.md) |
| 最後 push | 2025-07-24 22:20:44 UTC | [GitHub API](https://api.github.com/repos/maybe-finance/maybe) |
| 最後 commit | `77b5469`，加入 attribution note | [commit](https://github.com/maybe-finance/maybe/commit/77b5469832758d1cbee1a940f3012a1ae1c74cd3) |
| 最後 release | v0.6.0，2025-07-24 | [release](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0) |
| Issues | `has_issues: false`、0 open issues | [GitHub API](https://api.github.com/repos/maybe-finance/maybe) |
| Discussions | `has_discussions: false` | [GitHub API](https://api.github.com/repos/maybe-finance/maybe) |
| Security policy | 無 `SECURITY.md` | [community profile](https://api.github.com/repos/maybe-finance/maybe/community/profile) |
| Docker image | 官方 GHCR package 仍可拉取，含 `0.6.0`、`stable`、`latest` | [container package](https://github.com/maybe-finance/maybe/pkgs/container/maybe) |

GitHub 的 `updated_at` 可能因 star、metadata 或其他 repository 活動在 2026 年仍變動，**不能把它解讀成程式仍維護**；判斷維護狀態應看 `archived`、`pushed_at`、release 與官方告別說明。[Repo metadata](https://api.github.com/repos/maybe-finance/maybe)

### 2.2 成熟度判斷

**功能成熟度：中等偏高。** v0.1.0 到 v0.6.0 曾有十個左右公開 release，最終版已包含預算、投資、多幣別、Plaid、2FA、API、AI 與匯入匯出，不是概念驗證。[Releases](https://github.com/maybe-finance/maybe/releases)

**產品可靠度：中等。** 官方表示最終版「comes close」但仍未完全解決 cache 與資料一致性；任何歷史交易變動都會影響淨值、預算、帳戶趨勢與其他衍生結果。[v0.6.0 data consistency section](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0)

**長期維運成熟度：低。** 它尚未到 1.0，停止維護後也沒有正式安全回報與修補管道。官方 Compose、hosting guide 與 app image 還在，但文件中的 Discussion／issue 回報連結已失去實際用途，因 repository 已 archived 且 discussions/issues 停用。[Docker guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md) · [Repo metadata](https://api.github.com/repos/maybe-finance/maybe)

因此，Maybe 適合「理解限制後的本機唯讀／輔助帳本試驗」，不適合作為需要未來多年安全更新、零資料遺失與穩定 provider 的唯一財務真實來源。

## 3. 自架安裝與維運成本：Windows 11 + Docker Desktop／WSL2

### 3.1 官方部署形態

官方推薦 Docker Compose。標準 Compose 包含：[compose.example.yml](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml)

- `web`：Maybe Rails web app
- `worker`：Sidekiq background worker
- `db`：PostgreSQL 16
- `redis`：`redis:latest`
- `app-storage`、`postgres-data`、`redis-data` 三個 named volume
- host port `3000` 對 web port `3000`

最終 release 宣稱「single Docker container」，但官方 Compose 實際是四個 service，其中 web 與 worker 使用同一 Maybe image。維運評估應以 Compose 實際內容為準，而不是把它視為單一容器。[v0.6.0](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0) · [compose.example.yml](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml)

### 3.2 Windows 11 實務

Maybe 官方 Windows 開發指南建議先安裝 WSL Ubuntu，再於 Linux 環境安裝 Ruby、PostgreSQL 等；它是開發指南，不是 Docker Desktop production guide。[Windows Dev Setup Guide](https://github.com/maybe-finance/maybe/wiki/Windows-Dev-Setup-Guide)

對此使用者，最小摩擦路徑是：

- Docker Desktop 使用 WSL2 backend。
- 在 WSL2 的 Ubuntu shell 內建立部署目錄並執行官方 `docker compose` 指令。
- Compose 檔與 `.env` 放在 WSL2 Linux filesystem，而不是跨 Windows/WSL 的高摩擦同步目錄。
- 只在 `localhost:3000` 使用，不直接開放公網。

後兩點是根據官方 shell-oriented Docker guide 與 Compose 結構做的環境建議；Maybe 官方沒有提供 Docker Desktop 專用步驟、最低 RAM/CPU、WSL2 資源上限或 Windows 自動啟動指引。因此無法只靠官方來源負責任地給出精確 RAM／磁碟數字。[Docker guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md) · [Windows guide](https://github.com/maybe-finance/maybe/wiki/Windows-Dev-Setup-Guide)

### 3.3 初始安裝成本

官方流程本身不長：下載 `compose.example.yml`、設定 `.env`、`docker compose up`、在 `localhost:3000` 建立第一個帳號。[Docker guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md)

但預設檔為了「開箱即跑」保留了不宜正式使用的 fallback：

- database user/password 預設為 `maybe_user` / `maybe_password`
- `SECRET_KEY_BASE` 有固定 fallback 值
- `RAILS_FORCE_SSL`、`RAILS_ASSUME_SSL` 都是 `false`
- Redis 無認證
- Maybe image 使用 mutable `latest`
- Redis 也使用 mutable `latest`

來源：[compose.example.yml](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml#L30-L45)

本機隔離 demo 可接受這個形態，但只要要放真實財務資料，就至少要更換 secrets、固定 Maybe 版本、限制網路範圍，並建立備份。

### 3.4 日常維運成本

使用者需自行負責：

- Docker Desktop／WSL2 啟動與資源占用
- 四個 service 的 logs、健康狀態與磁碟成長
- PostgreSQL、Active Storage 與 secrets 備份
- container image pinning
- TLS／reverse proxy（若不只 localhost）
- SMTP（若需要密碼重設或 email report）
- Synth／Plaid／OpenAI 等外部 API 帳號、金鑰、費用與失效處理

官方更新流程是 `docker compose pull` 後重建 web/worker，且明說不會自動更新。[Docker update guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md#L138-L175) 但專案既已停止維護，`latest` 與 `stable` 現在實質停在最後一批 image；未來不應期待 Maybe 本身收到 security fixes。

此外，官方文件更新指令一處重啟 `web worker`，另一處卻重啟不存在於 sample Compose 的 `app` service，顯示最終文件仍有不一致。[Docker guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md#L151-L175) 正式操作前應先以 `docker compose config --services` 核對實際 service 名稱。

## 4. 資料匯入、銀行同步與地區限制

### 4.1 CSV 匯入能力

Maybe 支援四種匯入型別：[Import model](https://github.com/maybe-finance/maybe/blob/main/app/models/import.rb#L1-L15)

1. `TransactionImport`
2. `TradeImport`
3. `AccountImport`
4. `MintImport`

匯入器支援逗號或分號分隔、多種歐美／亞洲數字格式、流入正負號慣例、欄位 mapping、dry run 與 revert；一般匯入上限是 10,000 rows，帳戶匯入上限 50 rows。[Import model](https://github.com/maybe-finance/maybe/blob/main/app/models/import.rb) · [AccountImport](https://github.com/maybe-finance/maybe/blob/main/app/models/account_import.rb#L35-L63)

交易 CSV 可包含日期、金額、名稱、幣別、分類、tags、帳戶與 notes。[TransactionImport template](https://github.com/maybe-finance/maybe/blob/main/app/models/transaction_import.rb#L35-L68) 投資 trade CSV 可包含 ticker、exchange operating MIC、幣別、數量、價格與帳戶。[TradeImport template](https://github.com/maybe-finance/maybe/blob/main/app/models/trade_import.rb#L45-L75)

**台灣銀行 CSV 的判斷：可用，但屬人工 ETL。** 只要網銀／信用卡可匯出 CSV，或先把 XLSX/CSV 整理成 Maybe 欄位，就能匯入；但每家銀行欄位、正負號、編碼、日期格式與跨帳戶 transfer 都要自行驗證。Maybe 沒有台灣銀行專用 parser。

### 4.2 銀行同步與 Plaid

Maybe 的自動銀行同步只實作 Plaid，支援 products 為 transactions、investments、liabilities，最多請求 730 天歷史資料。[Plaid provider](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/plaid.rb#L1-L6)

地區在程式碼中是硬編碼：

- US region：`US`, `CA`
- EU region：`ES`, `NL`, `FR`, `IE`, `DE`, `IT`, `PL`, `DK`, `NO`, `SE`, `EE`, `LT`, `LV`, `PT`, `BE`
- **沒有 Taiwan / `TW`**

來源：[Plaid country codes](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/plaid.rb#L201-L210)

Self-host 若要啟用 Plaid，還需自行提供 `PLAID_CLIENT_ID` / `PLAID_SECRET`（EU 另有一組），而且 production flow 會產生 webhook URL，表示部署端必須能讓 Plaid 安全連入。[Plaid initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/plaid.rb) · [PlaidItemsController](https://github.com/maybe-finance/maybe/blob/main/app/controllers/plaid_items_controller.rb#L1-L23) 官方 `.env.example` 並沒有把 Plaid 列為標準 self-host 選項。[.env.example](https://github.com/maybe-finance/maybe/blob/main/.env.example)

**結論：台灣帳戶不要把 Plaid 當可行方案。** 即使自行申請 Plaid production access，Maybe 程式本身也沒有 TW country code 路徑。

### 4.3 台灣券商與全球投資資料

對台灣券商，實用途徑是 trade CSV 或手動輸入：

- ticker、exchange MIC、qty、price 可匯入。
- 若 Synth 能找到該 security，Maybe 可抓價格。
- 若找不到，resolver 會建立 `offline: true` 的 security，之後不抓 provider price。[TradeImport](https://github.com/maybe-finance/maybe/blob/main/app/models/trade_import.rb) · [Security resolver](https://github.com/maybe-finance/maybe/blob/main/app/models/security/resolver.rb#L8-L43)
- 手動 ticker 的持倉價值依輸入的 trade price 推進，不等於可靠的每日市價。[Trade create form](https://github.com/maybe-finance/maybe/blob/main/app/models/trade/create_form.rb#L20-L29)

Maybe 唯一登錄的 securities / exchange-rates provider 是 Synth。[Provider registry](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/registry.rb#L92-L102) 官方 `.env.example` 也把 Synth API key 標為 optional，用於 exchange rates 與 stock prices。[.env.example](https://github.com/maybe-finance/maybe/blob/main/.env.example#L17-L23)

原始碼的 security relevance ranking 把 `TW` 列入國家清單，但 exchange MIC 排序明確註明非常 US-centric；這只能證明資料模型容得下台灣市場，不能證明 Synth 對台股的價格覆蓋完整。[Security resolver](https://github.com/maybe-finance/maybe/blob/main/app/models/security/resolver.rb#L124-L154) 官方最終說明也承認沒有單一 provider 能供應所有全球證券價格，manual ticker 只是退路。[v0.6.0 multi-currency/investments section](https://github.com/maybe-finance/maybe/releases/tag/v0.6.0)

**台灣券商實用性：中低。** 適合把成交紀錄與大致持倉集中顯示，不適合期待免維護、每日精準的台股／基金／選擇權資產淨值。

### 4.4 加密資產

Maybe 有 `Crypto` account type，但 model 本身只定義資產分類、圖示與顯示名稱；新增帳戶沿用一般 account form，未連結時主要填名稱與 balance。[Crypto model](https://github.com/maybe-finance/maybe/blob/main/app/models/crypto.rb) · [Crypto form](https://github.com/maybe-finance/maybe/blob/main/app/views/cryptos/_form.html.erb) · [Account form](https://github.com/maybe-finance/maybe/blob/main/app/views/accounts/_form.html.erb)

官方 provider registry 沒有 Coinbase、Binance、Kraken、wallet 或 blockchain provider；只有 Synth、Plaid、OpenAI、GitHub 與 Stripe 路徑。[Provider registry](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/registry.rb)

**加密資產實用性：低。** 可把交易所／冷錢包當作一個手動估值帳戶，但不是 crypto portfolio tracker，沒有錢包位址、鏈上交易、staking、token lot 或交易所 API 同步。

### 4.5 資料匯出

Maybe 可產生 ZIP，包含：

- `accounts.csv`
- `transactions.csv`
- `trades.csv`
- `categories.csv`
- `all.ndjson`

NDJSON 另含 tags、merchants、valuations、budgets 等。[Family::DataExporter](https://github.com/maybe-finance/maybe/blob/main/app/models/family/data_exporter.rb)

這降低資料鎖定，但它是**業務資料匯出**，不是完整 disaster-recovery backup：沒有涵蓋 PostgreSQL 內所有 authentication/session/provider metadata，也不等同 Active Storage volume 與資料庫一致性快照。

## 5. 資料隱私、安全邊界與第三方 API

### 5.1 資料主要落點

標準自架把主要資料放在本機 Docker volumes：PostgreSQL、Redis、Active Storage 各一個。[compose.example.yml](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml#L47-L108)

Rails 使用 `has_secure_password`，並支援 TOTP MFA 與一次性 backup codes。[User model](https://github.com/maybe-finance/maybe/blob/main/app/models/user.rb#L1-L3) · [MFA implementation](https://github.com/maybe-finance/maybe/blob/main/app/models/user.rb#L123-L151)

Plaid access token 與 app API key 使用 Rails Active Record encryption；self-host 未提供獨立 encryption keys 時，會由 `SECRET_KEY_BASE` deterministically 派生。[PlaidItem](https://github.com/maybe-finance/maybe/blob/main/app/models/plaid_item.rb#L1-L9) · [ApiKey](https://github.com/maybe-finance/maybe/blob/main/app/models/api_key.rb#L1-L6) · [active_record_encryption initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/active_record_encryption.rb)

因此 `SECRET_KEY_BASE` 不只是 web session secret，也是 encrypted provider credentials 可否復原的關鍵；備份資料庫卻遺失原 secret，可能造成加密欄位無法解密。

### 5.2 第三方資料流

| 第三方 | 何時使用 | 可能送出的資料／邊界 | 第一手來源 |
|---|---|---|---|
| Synth | 設定 `SYNTH_API_KEY` 後抓匯率、ticker、價格 | ticker、MIC、country code、日期、匯率 pair；API header 包含 app name/type | [Synth provider](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/synth.rb) |
| Plaid | 設定 Plaid credentials 並連結機構 | access token、帳戶、交易、投資、負債與 institution metadata；webhook 回傳 Maybe | [Plaid provider](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/plaid.rb) · [PlaidItem storage](https://github.com/maybe-finance/maybe/blob/main/app/models/plaid_item.rb#L73-L93) |
| OpenAI | 設定 `OPENAI_ACCESS_TOKEN` 並使用 AI | 財務聊天 prompt、tool input、交易分類／merchant detection context | [OpenAI provider](https://github.com/maybe-finance/maybe/blob/main/app/models/provider/openai.rb) · [compose warning](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml#L44-L45) |
| Sentry | 只有設定 `SENTRY_DSN` | errors、breadcrumbs 與 25% tracing/profiling samples | [Sentry initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/sentry.rb) |
| Intercom | 只有同時設定兩個 Intercom env vars | 使用者、family id、role、account count、AI enabled 等 custom data | [Intercom initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/intercom.rb) |
| 外部 CDN／logo host | 部分頁面由 browser 直接載入 | Plaid Link JS、Synth institution/ticker logo、flag assets；會暴露一般 web request metadata，ticker/logo path 也可能揭露正在顯示的標的 | [shared head](https://github.com/maybe-finance/maybe/blob/main/app/views/layouts/shared/_head.html.erb) · [holding logo view](https://github.com/maybe-finance/maybe/blob/main/app/views/holdings/_holding.html.erb) · [account logo view](https://github.com/maybe-finance/maybe/blob/main/app/views/accounts/_logo.html.erb) |

沒有設定 Sentry／Intercom env vars 時，原始碼不會初始化這兩套服務；標準 Compose 也沒有設定它們。因此沒有看到預設啟用的 Sentry／Intercom telemetry。[Sentry initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/sentry.rb) · [Intercom initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/intercom.rb) · [compose](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml)

但「自架」不等於「完全 air-gapped」：Plaid JS 在 shared head 中以外部 CDN script 載入，部分 logo 也直接向 Synth 網域請求。若要求嚴格不出網，需要自行修改程式或在網路層封鎖，這會進入無上游支援的 fork 維護範圍。

### 5.3 安全缺口與邊界

- 標準 Compose 的 SSL flags 是 false；它適合 localhost，不能直接當安全的公網部署。[compose](https://github.com/maybe-finance/maybe/blob/main/compose.example.yml#L35-L45)
- 正式 production config 原本預設 force/assume SSL，但 Compose 明確覆寫成 false。[production config](https://github.com/maybe-finance/maybe/blob/main/config/environments/production.rb#L44-L49)
- Content Security Policy initializer 全部註解，沒有啟用 CSP。[CSP initializer](https://github.com/maybe-finance/maybe/blob/main/config/initializers/content_security_policy.rb)
- Repository 沒有 public security policy，且 archived 後沒有持續 dependency/security patching。[community profile](https://api.github.com/repos/maybe-finance/maybe/community/profile) · [README](https://github.com/maybe-finance/maybe/blob/main/README.md)
- 官方 Docker guide 甚至允許本機使用者跳過 secrets 強化；這只適合無真實資料的測試。[Docker guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md#L52-L95)

### 5.4 備份與還原風險

官方 Docker guide 有資料庫 volume reset 指令，並明確警告會刪除資料，但**沒有提供正式 backup／restore runbook**。[Docker troubleshooting](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md#L177-L194)

若正式使用，至少要保存：

1. PostgreSQL 邏輯備份或一致性快照
2. `app-storage` volume
3. `.env`／`SECRET_KEY_BASE`／Active Record encryption keys
4. Compose 檔與實際 image tag/digest
5. 定期的 Maybe data export，作為可讀、可轉移的第二層保險

只備份 `postgres-data` volume 而不保留 secret，或只下載 app export 而不備份 DB/attachments，都不是完整復原方案。

### 5.5 升級風險

Container entrypoint 在 web server 啟動時會執行 `rails db:prepare`，亦即會建立或 migrate database。[docker-entrypoint](https://github.com/maybe-finance/maybe/blob/main/bin/docker-entrypoint)

在有新版本的專案中，這代表拉新 image 後啟動就可能自動跑 migration；但 Maybe 已停止 release，主要風險轉為：

- 誤用 mutable `latest`／`redis:latest`
- 未備份就重建或執行 destructive troubleshooting
- 自行 fork 後 schema 與原 image 分歧
- Windows／Docker Desktop 更新造成容器或 volume 行為改變，卻沒有上游協助

正式試用應固定 `ghcr.io/maybe-finance/maybe:0.6.0`，而不是期待 `latest` 代表持續維護。

## 6. 授權與商標限制

Maybe 使用 GNU Affero General Public License v3.0。[LICENSE](https://github.com/maybe-finance/maybe/blob/main/LICENSE)

實務影響：

- 個人私下執行原版通常不要求公開自己的資料或設定。
- 若修改程式並讓其他使用者透過網路互動，AGPLv3 §13 要求向這些使用者清楚提供該修改版的 Corresponding Source。
- 散布修改版時需保留授權、變更說明，整體 covered work 繼續以 AGPLv3 授權。
- 軟體按現狀提供，沒有適售性、特定目的適用性或無錯誤保證。

商標限制是另一層：官方 README 要求 fork 保留 AGPLv3、說明源自 Maybe Finance 且不受其背書，並明確禁止 fork 繼續使用「Maybe」名稱或 logo。[README fork/branding section](https://github.com/maybe-finance/maybe/blob/main/README.md#forking-and-attribution) · [attribution commit](https://github.com/maybe-finance/maybe/commit/77b5469832758d1cbee1a940f3012a1ae1c74cd3)

因此：

- **純自架、不改品牌、不對外發布 fork：**授權負擔低。
- **修改後只給自己用：**通常仍可行。
- **提供給家人、團隊或公眾透過網路使用修改版：**要安排 source offer 與 AGPL compliance。
- **公開 fork／衍生產品：**必須改名、換 logo、加 attribution 與 no-affiliation 聲明。

此段是工程評估，不是法律意見。

## 7. 與現有 `signal-desk`：互補還是重疊

| 面向 | Maybe | `signal-desk` | 判斷 |
|---|---|---|---|
| 核心問題 | 我的資產、負債、交易、預算、淨值是多少 | 哪些 KOL 訊號可信、今天有哪些投資訊號值得聽 | **互補** |
| 主要輸入 | 銀行／券商資料、CSV、手動帳戶與 trades | KOL 內容、訊號紀錄、績效驗證 | **不同** |
| 主要輸出 | 財務 dashboard、預算、持倉、交易分析 | KOL 準確度、投資訊號、語音早報 | **不同** |
| 市場資料 | Synth 價格／匯率，或 offline manual ticker | 為訊號判讀服務的市場脈絡 | **小幅重疊** |
| AI／語音 | OpenAI 財務 chat，沒有以語音早報為核心 | 語音早報是核心 | **不構成替代** |
| 長期定位 | 個人財務 ledger / system of record 候選 | 訊號 intelligence assistant | **互補** |

Maybe 不會取代 `signal-desk`，也不應併入 `project-golem`。若 demo 後保留，建議維持三者零耦合：

- Maybe 僅作獨立個人財務帳本。
- `signal-desk` 繼續做 KOL 訊號與語音早報。
- 不要讓 `signal-desk` 直接依賴 Maybe database schema；若未來真的需要持倉-aware 訊號，只透過 Maybe 的 read-only API key 或人工 export 建立窄介面。[Maybe API key model](https://github.com/maybe-finance/maybe/blob/main/app/models/api_key.rb)

目前不值得為這個假設整合增加耦合：台灣帳戶資料本來就主要是手動匯入，而 Maybe 上游又已停止維護。

## 8. 明確建議與最小試用路徑

### 8.1 建議等級

**現在的建議：先用本機 demo。**

不是「現在正式安裝」，因為：

- 沒有台灣銀行自動同步。
- 台灣券商／全球行情只能部分自動，缺資料時退回 manual ticker。
- Crypto 幾乎是手動資產餘額。
- 上游停止維護、安全支援與 issues/discussions 都關閉。
- 正式使用需要自行建立備份、復原與安全邊界。

也不是直接「不要安裝」，因為它的 transaction、budget、net-worth、multi-currency、trade import、export 與 household 功能已相當完整；如果使用者接受手動 CSV，它可能仍比 spreadsheet 好用。

### 8.2 最小、低風險試用路徑

1. **隔離環境**：在 WSL2 建立單獨目錄，使用 Docker Desktop WSL2 backend；不要放進 `project-golem` 或 `signal-desk` repo。
2. **固定版本**：下載官方 `compose.example.yml`，把兩個 Maybe image 都固定為 `ghcr.io/maybe-finance/maybe:0.6.0`。[container tags](https://github.com/maybe-finance/maybe/pkgs/container/maybe)
3. **只限本機**：只從 `localhost:3000` 開啟，不做 port forwarding、不設公開 domain。
4. **設定強 secret**：即使是 demo，也建立自己的 `SECRET_KEY_BASE` 與 `POSTGRES_PASSWORD`，不要沿用 sample fallback。[Docker guide](https://github.com/maybe-finance/maybe/blob/main/docs/hosting/docker.md#L52-L95)
5. **關閉第三方資料流**：第一輪不要設定 Plaid、Synth、OpenAI、Sentry、Intercom、SMTP、S3/R2。
6. **只用假資料**：建立一個測試 household；從 UI 下載／依照內建 template 製作 10–30 筆匿名交易、一個台灣券商 trade、一個 manual ticker、一個 Crypto balance。不要先匯入真實全量財務資料。[Transaction template](https://github.com/maybe-finance/maybe/blob/main/app/models/transaction_import.rb#L57-L68) · [Trade template](https://github.com/maybe-finance/maybe/blob/main/app/models/trade_import.rb#L65-L75)
7. **驗證五件事**：
   - 中文商家名稱、TWD 與日期格式是否正常
   - 銀行 CSV mapping 是否可重複套用
   - transfer、信用卡付款與預算是否符合預期
   - 台股 manual ticker 的估值誤差是否可接受
   - data export 是否足以離開系統
8. **重啟測試**：停止並重新啟動 Compose，確認 volumes 持久化；再做一次 app export。
9. **決策門檻**：只有在「每月人工匯入可接受、台股價格不完整可接受、願意自行做 DB/volume/secret 備份」三項都為 yes 時，才進入真資料試用。

### 8.3 何時改判「不要安裝」

任一條成立就應停止：

- 主要目的是台灣銀行／券商自動同步。
- 希望加密資產自動同步交易所或錢包。
- 不想維護 PostgreSQL/Redis/Docker backups。
- 需要公網、多使用者、長期安全更新與正式 support。
- 只是想強化 KOL 訊號追蹤或語音早報；這應繼續投資 `signal-desk`，Maybe 不解這個問題。

### 8.4 何時可考慮正式保留

只有在以下情境值得：

- 使用者真正需要獨立的 net-worth／budget ledger。
- 台灣資料可以穩定轉成 CSV。
- Maybe 僅在本機／可信 LAN 使用。
- 能接受它是 frozen software，並自行承擔備份、安全與日後 fork 維護。
- 它與 `signal-desk` 維持資料與部署隔離。

---

## 最終判定

> **先用 demo；目前不要正式安裝成財務主系統。**

Maybe v0.6.0 是一個功能豐富、設計完整的個人財務引擎，但在 2026-07-28 已是 archived、無 active maintenance 的 frozen application。對台灣使用者，最有價值的是 CSV ledger、預算、淨值與手動投資追蹤；最弱的是銀行同步、台灣券商行情與 crypto automation。它和 `signal-desk` 是互補而非重疊，但沒有足夠理由現在新增正式基礎設施與長期維運責任。

最合理的做法是用固定 `0.6.0` image、匿名資料、localhost-only 做一次可隨時丟棄的 Docker demo；通過 CSV、估值、export 與維運接受度測試後，再決定是否保留。