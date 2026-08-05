# claude-video（`/watch`）研究與 CreatorHub 產品參考比較（截至 2026-07-30）

- 評估標的：[bradautomates/claude-video](https://github.com/bradautomates/claude-video)
- 對照標的：[3441293738/creatorhub](https://github.com/3441293738/creatorhub)（見 [2026-07-29 分析](./2026-07-29-creatorhub-analysis.md)）
- 來源原則：只用 README、原始碼、GitHub API、CI workflow、CHANGELOG、Issues、Releases 等第一手來源
- 研究目的：不是評估「該不該用」，而是萃取**可重用的產品模式**，作為未來自建類似 agent-skill 型工具的設計參考

---

## 結論先行（10 點）

1. **claude-video 是一個單一職責的 Agent Skill**：`/watch <url-or-path> [問題]`，把「下載影片→抽幀→字幕/Whisper 轉錄→交給 Claude 多模態分析」做成一條可重跑的 pipeline，不是帳號營運平台。[README](https://github.com/bradautomates/claude-video/blob/main/README.md)
2. **架構極簡但邊界清楚**：7 個 Python 腳本各司其職（download / frames / transcribe / whisper / config / setup / watch 協調），無 Web server、無資料庫、無常駐 process；每次執行都是一次性 CLI 呼叫＋暫存資料夾。[skills/watch/scripts](https://github.com/bradautomates/claude-video/tree/main/skills/watch/scripts)
3. **成熟度遠高於 CreatorHub**：12,595 星、1,243 fork、5 個正式 SemVer release（含建置好的 `.skill` 產物）、有 CI release workflow、MIT 授權、CHANGELOG 逐版列出 Added/Changed/Fixed/Security。但仍是**單一維護者**（`bradautomates` 貢獻 11 commits，其餘全來自社群 PR）、community health 只有 42%、目前有 79 個 open issues、22 筆近期都是 Windows/ffmpeg 相容性與轉錄品質的修補 PR。[repo metadata](https://api.github.com/repos/bradautomates/claude-video) · [releases](https://api.github.com/repos/bradautomates/claude-video/releases) · [contributors](https://api.github.com/repos/bradautomates/claude-video/contributors) · [community profile](https://api.github.com/repos/bradautomates/claude-video/community/profile) · [issues](https://github.com/bradautomates/claude-video/issues)
4. **安全模型天差地遠**：claude-video 沒有網路監聽面，攻擊面只有「本機 subprocess 呼叫 yt-dlp/ffmpeg」＋「上傳抽出的音檔到 Groq/OpenAI」；`.env` 有嘗試設 600 權限（但 config.py 本身讀取時不驗證權限、且 Windows 上該檢查會誤判，已有 PR 在修）。CreatorHub 則是預設 `0.0.0.0` 監聽、無 auth、Cookie/私訊/AI key 明文存 SQLite，兩者風險等級不在同一量級。[config.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/config.py) · [setup.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/setup.py) · [PR #89](https://github.com/bradautomates/claude-video/pull/89)
5. **共同點**：兩者都重度依賴第三方非官方工具鏈的穩定性（claude-video 依賴 `yt-dlp` 對抖音等平台的解析器；CreatorHub 依賴 Playwright DOM/簽名）；都用「本機明文 `.env`/SQLite 存 API key／登入態」；都是單一維護者、無 CI 品質門檻式的完整驗證（claude-video 有 CI 但只跑 release 建置，沒看到 test-on-PR workflow）。
6. **最值得抄的產品模式**：SKILL.md 當「agent 可讀的操作手冊＋決策樹」而不是純文件；`config.py` 的「環境變數覆蓋 `.env` 檔覆蓋內建預設」三層優先序；`watch.py` 的「探測→按需下載→按 detail mode 抽樣→合併時間軸→交還 markdown 報告＋不自動刪暫存」pipeline 骨架；`setup.py --check` 回傳結構化 exit code 讓呼叫端（agent）做決策樹分支，而不是印文字要人看。[SKILL.md](https://github.com/bradautomates/claude-video/blob/main/skills/watch/SKILL.md) · [watch.py 摘要見下文]
7. **不該照抄的設計**：`.env` 明文存 API key 且未強制權限檢查生效；`download.py` 對外部 URL 沒有 SSRF/私網位址防護、無檔案大小上限、無逾時；`config.py` 允許無密鑰即靜默運作（產品面友善但企業場景要能強制）；單體巨型 test/PR 積壓（79 open issues）顯示「先求可用、後補穩定」的維護節奏，若要做成正式產品不能照搬這個節奏。
8. **對 CreatorHub 的互補性**：claude-video 證明「單一垂直能力（看影片）＋乾淨 CLI 邊界＋agent-native 說明書」可以又快又穩地做成 12k star 專案；CreatorHub 的多平台監控/下載模組若要重構，可借用 claude-video 的「provider 抽象＋一次性 subprocess pipeline＋不常駐」模式，取代「所有能力塞進一個常駐 FastAPI monolith」。
9. **給未來自建產品的分階段藍圖**：MVP 先做「單一來源→單一輸出格式的 CLI pipeline＋SKILL.md 手冊」，比照 claude-video v0.1.0；第二階段才加 detail modes／dedup／時間窗這類效能功能；正式產品化才需要 auth、secret 加密、SSRF 防護、CI 測試門檻——這些 claude-video 到現在（v0.2.0，79 open issues）都還沒完全補齊，代表這條路是可接受的漸進節奏，但「安全」這塊建議自建產品比它更早補上，因為一旦做成有網路監聽面（像 CreatorHub）風險等級會跳級。
10. **關鍵限制與待驗證項**：本研究未實際執行 `/watch`、未讀 79 個 issue 全文、未讀 `tests/` 逐檔內容、未做逐行 code review；架構與行為描述以 README／CHANGELOG／原始碼摘要與 WebFetch 對原始碼的忠實摘要為準，未做語意驗證執行。

---

## 1. claude-video 是什麼與實際工作流

claude-video 是 [Bradley Bonanno](https://github.com/bradautomates)（帳號 `bradautomates`）開發的 **Agent Skill**（不是完整應用程式），名稱 `watch`，讓 Claude（以及 Codex、Cursor、GitHub Copilot、Gemini CLI 等 50+ 個 Agent Skills 相容 host）能「看」影片：下載或直接讀取本機影片、抽取關鍵畫格、取得原生字幕或用 Whisper 轉錄，再把畫格路徑＋逐字稿一起交給 Claude 做多模態分析。[repo 描述](https://api.github.com/repos/bradautomates/claude-video) · [README](https://github.com/bradautomates/claude-video/blob/main/README.md)

**支援輸入**：本機 `.mp4/.mov/.mkv/.webm`；以及 `yt-dlp` 能解析的網址（YouTube、Loom、TikTok、X、Instagram、Vimeo 等）。[README](https://github.com/bradautomates/claude-video/blob/main/README.md)

**使用方式**（皆為 agent 對話中直接輸入的指令）：

```text
/watch https://youtu.be/dQw4w9WgXcQ what happens at the 30 second mark?
/watch ~/Movies/screen-recording.mp4 when does the UI break?
/watch https://youtu.be/abc --start 2:15 --end 2:45
```

**實際工作流程（`SKILL.md` 規定 agent 必須依序執行的步驟）**：

1. 從 `SKILL.md` 自身路徑解析出 skill 目錄，確認 `scripts/watch.py` 存在（不假設固定安裝路徑）。
2. Session 首次呼叫先跑 `setup.py --json`；之後改跑安靜版 `setup.py --check`，依 exit code（2＝缺二進位檔、3＝缺設定檔但可無金鑰運作、4＝缺依賴＋可選 Whisper）走不同分支，**不重複詢問**已完成設定的使用者。
3. 首次設定：優先建議設 Groq key、其次 OpenAI，使用者拒絕則走純視覺模式；並詢問一次預設 `WATCH_DETAIL`（transcript/efficient/balanced/token-burner，balanced 為建議值），寫入後標記 `SETUP_COMPLETE=true`，之後不再問。
4. 解析使用者輸入，拆出來源（URL/路徑）與問題，原樣傳給腳本。
5. 依使用者是否指名特定片段，決定要不要帶 `--start/--end/--timestamps`。
6. 執行 `watch.py`：探測字幕（URL 先查 `yt-dlp` 是否有字幕，有則可能整段跳過下載影片本體）→ 依需要下載（全片或僅音訊）→ 讀 `ffprobe` metadata → 依 detail mode 抽幀（keyframe/scene-aware/uniform，外加使用者指定的 timestamp 幀）→ 去重 → 若無字幕且有音訊則呼叫 Whisper → 輸出一份 Markdown 報告（畫格路徑＋時間戳＋逐字稿），暫存資料夾**不自動刪除**。
7. Agent 讀取報告內列出的每一個畫格檔案路徑（用 Read 工具，建議平行讀取），對齊逐字稿時間戳後回答使用者問題或做摘要。
8. 後續追問同一支影片時重用既有輸出，不重跑；確認使用者不會再問時才清掉暫存資料夾。

來源：[SKILL.md](https://github.com/bradautomates/claude-video/blob/main/skills/watch/SKILL.md) · [watch.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/watch.py)

它不是：官方影音下載服務、社群/帳號管理工具、常駐 Web 服務、資料庫驅動的多使用者後台——這點與 CreatorHub 的定位完全不同。

---

## 2. 技術架構與關鍵檔案

### 2.1 檔案樹（完整）

```text
claude-video/
├── .agents/plugins/marketplace.json      (388B)
├── .claude-plugin/
│   ├── marketplace.json                  (608B)
│   └── plugin.json                       (612B)
├── .codex-plugin/plugin.json             (1,663B)
├── .github/workflows/release.yml         (602B)
├── hooks/
│   ├── hooks.json                        (279B)
│   └── scripts/check-setup.sh            (2,009B)
├── skills/watch/
│   ├── SKILL.md                          (21,807B)
│   ├── .skillignore
│   └── scripts/
│       ├── build-skill.sh                (1,391B)
│       ├── config.py                     (2,108B)
│       ├── download.py                   (5,454B)
│       ├── frames.py                     (26,346B)
│       ├── setup.py                      (12,080B)
│       ├── transcribe.py                 (2,897B)
│       ├── watch.py                      (16,482B)
│       └── whisper.py                    (17,046B)
├── tests/  (9 個 pytest 檔：config/dedup/download/fixtures/frames/setup/timestamps/watch/whisper)
├── AGENTS.md / CLAUDE.md / CHANGELOG.md / LICENSE / README.md / dev-sync.sh
```

來源：[recursive tree API](https://api.github.com/repos/bradautomates/claude-video/git/trees/main?recursive=1)

### 2.2 元件與資料流

```text
使用者輸入（URL 或本機檔案 + 問題）
        │
        ▼
watch.py（協調者：argparse → get_config()/frame_cap() → 分支邏輯）
        │
        ├─ is_url() 判斷來源類型
        ├─ URL：download.py.fetch_captions() 先查字幕（yt-dlp --skip-download）
        ├─ download.py.download()：按需全片/純音訊下載（yt-dlp，-N 8、720p 上限、MP4 合併）
        ├─ frames.py：get_metadata()（ffprobe）→ 依 detail mode 抽幀（uniform/scene/keyframe/timestamp）
        │        └─ 去重：16×16 灰階縮圖，逐幀與上一張保留幀比較，平均像素差 > 2.0 才保留
        ├─ transcribe.py：字幕不存在時走 Whisper 分支
        │        └─ whisper.py：純標準庫 HTTPS multipart 呼叫 Groq/OpenAI，>24MB 自動分段
        └─ 產出 Markdown 報告（畫格清單＋時間戳＋逐字稿＋工作目錄路徑）→ stdout
                （暫存檔留在 --out-dir 或 tempfile.mkdtemp(prefix="watch-")，不自動清除）
```

`config.py` 負責讀 `~/.config/watch/.env`（環境變數優先於檔案，檔案優先於內建預設），只管理 `WATCH_DETAIL` 一個核心開關與各 detail mode 的預設 frame cap。`setup.py` 負責跨平台依賴檢查/安裝（macOS 用 Homebrew 自動裝，Linux/Windows 只印指令）、API key 詢問與 `.env` scaffold、以及 600 權限設定與警告。[watch.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/watch.py) · [config.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/config.py) · [setup.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/setup.py) · [download.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/download.py) · [frames.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/frames.py) · [whisper.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/whisper.py)

### 2.3 抽幀與轉錄演算法要點

- **Detail modes**：`transcript`（0 幀，僅逐字稿）／`efficient`（keyframe，上限 50）／`balanced`（scene-aware，上限 100，預設）／`token-burner`（scene-aware，無上限）。
- **Frame budget** 依片長分級（≤30s→約 30 幀，30–60s→40，1–3min→60，3–10min→80，>10min→100，聚焦區間可更密，最高 2 fps）。
- **Scene detection**：取首幀＋ffmpeg scene score > 0.20 的候選幀，候選過多再依全片均勻抽稀，保留頭尾。
- **去重**：16×16 灰階縮圖比對，平均絕對像素差 ≤ 2.0 視為重複並刪除，去重在 frame cap 之前套用。
- **Whisper**：音訊先轉 mono/16kHz/64kbps MP3，＞24MB 自動切塊個別上傳，`verbose_json`＋`temperature=0`，失敗重試（4xx 多數不重試、429 有限重試、5xx/網路錯誤重試至 4 次）。
- **安全強化（v0.1.3 起）**：yt-dlp 呼叫在 URL 前加 `--` 防選項注入；`is_url()` 拒絕以 `-` 開頭的輸入；影音路徑呼叫 ffmpeg/ffprobe 前一律 `Path.resolve()` 轉絕對路徑，避免相對路徑被誤判為 flag。

來源：[frames.py 摘要](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/frames.py) · [whisper.py 摘要](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/whisper.py) · [CHANGELOG v0.1.3](https://github.com/bradautomates/claude-video/blob/main/CHANGELOG.md)

### 2.4 Plugin / Hook 機制

- `.claude-plugin/plugin.json`：`name: watch`、`version: 0.2.0`、`license: MIT`、`author: Bradley Bonanno`，含 keywords（video/youtube/whisper/ffmpeg 等）。[plugin.json](https://github.com/bradautomates/claude-video/blob/main/.claude-plugin/plugin.json)
- `hooks/hooks.json`：註冊一個 `SessionStart` hook，無 matcher（每次 session 開始都跑），執行 `bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check-setup.sh`，timeout 5 秒。[hooks.json](https://github.com/bradautomates/claude-video/blob/main/hooks/hooks.json)
- `check-setup.sh`：檢查 `.env` 權限（非 600/400 則警告）、讀取 key 是否存在、檢查 `ffmpeg`/`yt-dlp` 是否已裝，設定完成且工具齊全時**完全靜默**，否則印一行狀態提示。[check-setup.sh](https://github.com/bradautomates/claude-video/blob/main/hooks/scripts/check-setup.sh)
- 同時提供 `.agents/plugins/marketplace.json`、`.codex-plugin/plugin.json`，讓同一份 skill 可分別以 Claude Code plugin marketplace、通用 Agent Skills（`npx skills add`）、Codex plugin 三種管道安裝，用同一份 `skills/watch/` 作為 single source of truth。[.codex-plugin/plugin.json](https://github.com/bradautomates/claude-video/blob/main/.codex-plugin/plugin.json)

---

## 3. 安裝與使用

### 3.1 三種安裝管道

```text
# Claude Code（plugin marketplace）
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video

# 任何 Agent Skills 相容 host（Codex/Cursor/Copilot/Gemini CLI…）
npx skills add bradautomates/claude-video -g
npx skills add bradautomates/claude-video -a codex -a cursor

# claude.ai（網頁版）
# 下載 GitHub Release 附的 watch.skill，Settings → Capabilities → Skills → 上傳
```

手動開發安裝：`git clone` 後對 `skills/watch` 建 symlink 到 `~/.claude/skills/watch`（或 `~/.codex/skills/watch`）。[README 安裝章節](https://github.com/bradautomates/claude-video/blob/main/README.md)

### 3.2 首次執行需求

`setup.py` 檢查 `ffmpeg`／`ffprobe`／`yt-dlp`：macOS 用 Homebrew 自動裝，Linux 印 `apt`/`dnf`/`pipx` 指令，Windows 印 `winget`/`pip` 指令；Whisper 為可選，Groq 優先、OpenAI 次之，key 只能手動加入，程式不會自動寫入；設定檔固定在 `~/.config/watch/.env`，只在不存在時建立並嘗試設權限 600。[setup.py 摘要](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/setup.py)

### 3.3 建置與發布

```bash
python3 -m pytest -q                     # 跑測試
bash skills/watch/scripts/build-skill.sh # 打包 claude.ai 用的 dist/watch.skill
```

Release 流程：對 `v*` tag push 觸發 GitHub Actions（`.github/workflows/release.yml`），跑 `build-skill.sh` 產出 `dist/watch.skill`，用 `softprops/action-gh-release@v2` 建立非 draft／非 prerelease release 並自動生成 release notes、附加 `.skill` 檔。[release.yml](https://github.com/bradautomates/claude-video/blob/main/.github/workflows/release.yml)

---

## 4. 成熟度、安全／隱私／授權／供應鏈風險

### 4.1 客觀指標

| 指標 | 狀態 |
|---|---|
| 建立日期 | 2026-04-24 |
| 最後 push | 2026-07-01（metadata）／2026-07-29 有更新活動 |
| Stars / Forks | 12,595 / 1,243 |
| Open issues | 79 |
| Contributors | 1 位作者 commit（其餘經 PR 貢獻，見上表約 22 筆近期開放 PR） |
| Releases | 5 個 SemVer release，皆附建置產物 |
| License | MIT，© 2026 Bradley Bonanno |
| Community profile health | 42%（有 README/License，無 Contributing/CoC/Issue Template/PR Template/Security policy） |
| CI | 只有 tag-triggered release workflow，未見 PR/push 觸發的測試 CI workflow |
| 測試 | `tests/` 9 個 pytest 檔，用 ffmpeg 產生的合成影片做離線測試 |

來源：[repo metadata](https://api.github.com/repos/bradautomates/claude-video) · [releases](https://api.github.com/repos/bradautomates/claude-video/releases) · [contributors](https://api.github.com/repos/bradautomates/claude-video/contributors) · [community profile](https://api.github.com/repos/bradautomates/claude-video/community/profile) · [workflows 目錄](https://github.com/bradautomates/claude-video/tree/main/.github/workflows) · [tests 目錄](https://github.com/bradautomates/claude-video/tree/main/tests)

### 4.2 安全與隱私觀察

- **無網路監聽面**：這是與 CreatorHub 最大的結構性差異——claude-video 是一次性 CLI 呼叫，沒有常駐 server、沒有 API、沒有 port。攻擊面收斂到「本機檔案/subprocess」與「對外部 URL／API 的請求」。
- **Secret 儲存**：`~/.config/watch/.env` 明文存 `GROQ_API_KEY`/`OPENAI_API_KEY`；`setup.py` 建檔時嘗試設 600 並在權限過鬆時警告，但 `config.py` 讀取端**不驗證**權限，且 Windows 上的 POSIX 權限檢查邏輯本身有誤判問題，已有社群 PR 在修（[PR #89](https://github.com/bradautomates/claude-video/pull/89) “fix: make .env permission check Windows-aware”）。
- **URL/下載安全**：`download.py` 用 `subprocess.run` 不經 shell，且對 URL 前綴 `--` 防選項注入、拒絕 `-` 開頭輸入——這比 CreatorHub 的處理更嚴謹；但**沒有** host allowlist、私網位址阻擋、逾時、下載大小上限或重導向驗證，理論上仍有 SSRF／資源耗盡風險（例如 `/watch http://169.254.169.254/...` 這類雲端 metadata endpoint，若 yt-dlp 誤判為可處理來源）。[download.py 摘要](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/download.py)
- **資料外送**：只有**抽出的音訊**（非原始影片）會上傳到使用者選定的 Groq/OpenAI；原始碼未說明供應商的資料保留/訓練使用政策。字幕/畫格留在本機。SKILL.md 明文要求 agent「不得上傳影片本體，只能送音訊」、「不得使用帳號 session/cookie/發文權限」。
- **授權**：MIT，可自由修改、散布、商用，這點與 CreatorHub（`license: null`）截然不同，是可安心參考、甚至衍生的素材。
- **供應鏈**：核心相依 `yt-dlp`、`ffmpeg` 為外部二進位（非 pip 套件鎖版），版本漂移風險與 CreatorHub 類似；Whisper 呼叫未用官方 SDK、純標準庫實作，減少了一層第三方套件供應鏈風險，但也代表升級/相容性要自己維護。

來源：[config.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/config.py) · [setup.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/setup.py) · [download.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/download.py) · [SKILL.md 明確 dos/don'ts](https://github.com/bradautomates/claude-video/blob/main/skills/watch/SKILL.md) · [LICENSE](https://github.com/bradautomates/claude-video/blob/main/LICENSE)

### 4.3 成熟度判斷

- **功能廣度**：中（單一垂直能力，做得深不做得廣）。
- **可靠度**：中低——`yt-dlp` 對特定平台的解析器隨時可能失效（issue 追蹤中大量 Windows/ffmpeg 版本相容性 bug），但因為架構單純，修復成本比 CreatorHub 低很多。
- **安全成熟度**：中——沒有網路監聽面把整體風險壓低很多，但 secret 明文與下載端缺乏邊界防護仍是需要注意的點。
- **維運成熟度**：中高——有 SemVer release、CHANGELOG、CI 建置自動化，但**沒有** PR 測試門檻 CI、沒有 CONTRIBUTING/SECURITY 文件、單一維護者。
- **社群成熟度**：高熱度（12.6k star）但治理仍薄（42% community health，79 open issues 待處理）。

---

## 5. 與 CreatorHub 的共同點、差異、互補性

| 面向 | claude-video | CreatorHub |
|---|---|---|
| 定位 | 單一能力 Agent Skill（看影片） | 多平台帳號營運＋監控＋下載＋發布控制台 |
| 執行型態 | 一次性 CLI subprocess，無常駐服務 | 常駐 FastAPI + Uvicorn + Playwright，長駐 process |
| 網路面 | 無監聽，只主動對外呼叫 | 預設監聽 `0.0.0.0:8000`，無 auth |
| Secret 存放 | `.env` 明文，嘗試設 600 | SQLite 明文欄位，無加密/keychain |
| 平台依賴 | `yt-dlp` 解析器 | Playwright DOM + 逆向簽名（如 xhshow） |
| 授權 | MIT，明確 | 無 LICENSE |
| 維護者 | 1 人 commit + 活躍社群 PR | 1 人（全部） |
| Release/CI | 5 個 SemVer release + tag CI | 0 release，無 CI |
| 測試 | 9 個 pytest（合成影片） | 5 個 unittest（純邏輯） |
| 寫操作範圍 | 無（唯讀分析） | 大量寫操作：發布、評論、私訊、關注 |
| 使用同意面 | 使用者主動 `/watch <url>` | 背景監控＋自動化操作可無人值守運行 |

**共同點**：兩者都證明「把非官方工具鏈（yt-dlp/Playwright）包裝成好用面板/技能」市場需求真實存在；都選擇本機/單機執行、明文設定檔的最短路徑；都是單一維護者主導、靠社群回報驅動修 bug；都依賴外部平台的非公開行為，隨時可能因對方改版而失效。

**差異的根源**：claude-video 只做「唯讀讀取＋分析」，天然安全邊界小；CreatorHub 做「多帳號寫操作＋常駐服務」，天然安全邊界大很多。兩者的架構複雜度差異（7 個小檔案 vs. 5 個巨型檔案）某種程度上直接對應到這個範疇差異。

**互補性／可遷移的具體建議**：若要重構 CreatorHub 這類多平台工具，可以借用 claude-video 的「provider adapter 做成獨立可測試的小模組＋主流程做成一次性 pipeline，只有真正需要常駐輪詢的部分（監控排程）才維持背景 process」，把「監控排程」與「使用者互動式操作（登入/發布/看單支影片）」拆成兩個邊界完全不同的子系統，而不是全部塞進一個 FastAPI app 的 lifespan。這正是下一節要展開的模式。

---

## 6. 可重用的產品模式（給未來自建同類產品參考）

### 6.1 Domain model（以 claude-video 為例抽象化）

```text
Source        := URL | LocalPath
Job           := { source: Source, question?: str, range?: TimeRange, detail: DetailMode }
DetailMode    := transcript | efficient | balanced | token-burner
TimeRange     := { start?: Timecode, end?: Timecode, timestamps?: Timecode[] }
Media         := { videoPath?, audioPath?, durationSec, hasAudio, dimensions }
Transcript    := { source: native_caption | whisper, segments: [{start,end,text}] }
Frame         := { path, timestampSec, reason: scene|keyframe|cue|uniform }
Report        := { meta, frames: Frame[], transcript?: Transcript, workDir }
```

這個 domain model 的價值在於：**Job 是無狀態、可重跑的值物件**；`Report` 是純資料輸出，agent（呼叫端）負責解讀，pipeline 本身不做「回答問題」這件語意層的事——語意留給 LLM，工程層只做「取得證據」。這個切分是最值得複製的架構決策：**確定性、可測試的部分（下載/抽幀/轉錄）與非確定性、需要模型判斷的部分（回答問題、摘要）嚴格分離**。

### 6.2 模組邊界

- `download`：只認識「來源→媒體檔案／字幕」，不知道後面要幹嘛。
- `frames`：只認識「媒體檔案＋策略→畫格清單」，不知道來源是 URL 還是本機檔。
- `transcribe`：只認識「音檔／字幕檔→帶時間戳文字」，對 provider 是 Groq 還是 OpenAI 無感（provider 差異封裝在 `whisper.py` 內的函式選擇）。
- `config`：唯一知道「使用者偏好從哪裡讀」的模組，其餘模組只吃已解析好的設定值，不自己讀環境變數。
- `watch`（orchestrator）：唯一知道「完整流程順序」的模組，其餘模組互不知道彼此存在。

這種「每個模組只認識自己輸入輸出型別，不假設呼叫順序」的邊界，讓 9 個 pytest 檔可以逐模組獨立測試（用合成 ffmpeg 影片，不需要真的打 YouTube），是 claude-video 相對 CreatorHub 測試覆蓋率高出很多的直接原因。[tests 目錄](https://github.com/bradautomates/claude-video/tree/main/tests)

### 6.3 Provider 抽象模式

Whisper 的 Groq/OpenAI 雙 provider 沒有做成 class/interface 抽象，而是「兩個幾乎對稱的函式＋一個依優先序選擇 key 的 `load_api_key()`」——刻意不做過度工程化的 plugin 系統，因為目前只有兩個 provider。這呼應「別為只有一個實作的東西做 interface」的簡化原則，**只有當 provider 數量真的變多（PR #91 要求支援自架 OpenAI-compatible endpoint）才需要往更通用的抽象演進**，而不是一開始就設計。[whisper.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/whisper.py) · [PR #91](https://github.com/bradautomates/claude-video/pull/91)

### 6.4 Extension / 分發抽象

claude-video 用「單一 `skills/watch/` 目錄 + 三份平台專屬 manifest（`.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`.agents/plugins/marketplace.json`）」達成一次開發、多平台分發，manifest 之間唯一要手動同步的是 version number（CHANGELOG 明確提醒「Version numbers must remain synchronized across the skill and plugin manifests」）。這是「一個核心＋多個薄殼 adapter 對接不同宿主生態」的典型模式，值得在自建 skill/plugin 型產品時直接複製。[README Architecture 章節](https://github.com/bradautomates/claude-video/blob/main/README.md)

### 6.5 Agent 說明書即產品介面

`SKILL.md`（21.8KB）本身就是「give the agent a decision tree, not just docs」的示範：它不只是敘述功能，而是明確寫「先做什麼、若 X 則做 Y、絕對不要做 Z」，並把 exit code（2/3/4）當作 agent 決策分支的訊號通道。這比傳統 CLI `--help` 更適合 agent 消費，是這類 agent-facing 產品的核心介面設計模式，值得作為未來任何 Claude Skill 產品的預設寫法範本。[SKILL.md](https://github.com/bradautomates/claude-video/blob/main/skills/watch/SKILL.md)

### 6.6 資料流的「按需最小化」原則

- 有字幕就不下載影片本體（transcript-only 模式 4.5 秒完成，不下載）。
- 只轉錄音訊需要時才拉音軌，不需要畫格時不拉影片。
- 聚焦時間窗只抽該窗格內的畫格，不做全片抽樣後再篩選。

這是「先問要多少證據，再決定拉多少資料」的資料流設計，直接對應到 token/頻寬/時間成本控制，是任何要接 LLM 消費媒體資料的產品都該採用的預設路徑。[README Processing workflow](https://github.com/bradautomates/claude-video/blob/main/README.md)

---

## 7. 不該照抄的設計

1. **`.env` 明文＋權限檢查不生效**：`setup.py` 寫檔時嘗試設 600，但 `config.py` 讀取時完全不驗證權限，且該邏輯在 Windows 上會誤判（PR #89 在修）。自建產品若要存 API key，至少要在讀寫兩端都做一致的權限/加密策略，或改用 OS keychain。
2. **下載端無邊界防護**：`download.py` 對外部 URL 沒有私網位址阻擋、逾時、大小上限。這在 claude-video 情境下風險較低（單機互動式使用、無網路監聽面），但若這套 pipeline 被包進任何有網路服務層的產品（例如未來要做 SaaS 版），必須補齊 SSRF 防護與資源上限，不能原樣複製。
3. **無 PR 測試門檻 CI**：唯一的 GitHub Actions workflow 只在 tag push 時跑建置，沒有看到「PR 必須跑測試才能合併」的門檻，79 個 open issue／22 個待審 PR 某種程度上反映了這個缺口。正式產品應該一開始就把測試門檻掛在 PR 上，而不是等社群壓力大了才補。
4. **社群治理文件缺失**：無 CONTRIBUTING、CODE_OF_CONDUCT、ISSUE_TEMPLATE、SECURITY.md（community health 42%）。專案熱度已達 12k star 規模，這类文件的缺席會讓維護者被動於社群量能，值得在自建產品達到中等熱度前就先補上。
5. **「靜默失敗優先」在某些分支可能過度寬容**：例如 Whisper 失敗時「report 繼續、只留下警示」而非中止，這對互動式單人使用是合理的 UX，但若移植到自動化/無人值守情境（例如排程任務），「靜默降級」可能掩蓋長期系統性問題，需要額外加告警機制才能照搬。

---

## 8. MVP → Production 分階段研發藍圖（給「做類似產品」的自己參考）

以 claude-video 的實際版本演進為錨點（[CHANGELOG](https://github.com/bradautomates/claude-video/blob/main/CHANGELOG.md)）：

**階段 0（v0.1.0，MVP）**
- 單一命令、單一資料流：來源→字幕優先→按需下載→固定策略抽幀（無 detail mode 分級）→ Whisper 兜底→ Markdown 報告。
- 一份 `SKILL.md`＋一份 session-start hook 做基本環境檢查。
- 目標：能跑、能被 agent 正確消費輸出，不追求效能與涵蓋率。

**階段 1（v0.1.1–v0.1.3，跨平台補強）**
- 修 Windows/編碼相容性（UTF-8、`python` vs `python3`、emoji 顯示問題）。
- 補安全基本功：subprocess 選項注入防護、路徑絕對化、URL 格式驗證。
- 這階段的教訓：**MVP 一上線就會馬上暴露跨平台 edge case，這些 bug 修復要當作標準路徑規劃，不是意外**。

**階段 2（v0.2.0，效能與精度分級）**
- 引入 detail mode 分級（transcript/efficient/balanced/token-burner）與對應 frame budget。
- 加去重演算法降低 token 浪費。
- 加時間窗聚焦（`--start/--end/--timestamps`）。
- 加離線 pytest 覆蓋（用合成媒體，不依賴真實網路請求，讓測試可在 CI 穩定跑）。
- 這階段的教訓：**先讓核心可用，效能/精度分級是第二階段才做的正確順序**，不要一開始就設計多層 detail mode。

**階段 3（尚未做到，production 化建議項，目前 issue 已浮現但未合併）**
- PR 測試門檻 CI（目前缺）。
- Secret 讀寫兩端一致的權限/加密策略（PR #89 顯示還在補）。
- 下載端邊界防護（SSRF、大小/逾時上限）。
- 多語言字幕可設定（PR #90）、多 provider 可設定 endpoint（PR #91）——即「當真實需求出現多個 provider/多語需求時才做抽象」，而不是預先設計。
- CONTRIBUTING/SECURITY/CoC 文件與 issue/PR template，降低社群治理成本。

**給未來自建產品的建議節奏**：階段 0-2 可以照抄這個節奏（先求可跑，再補跨平台穩定性，最後做效能分級）；但如果目標產品比 claude-video 涉及更高風險（例如接觸使用者帳號、寫操作、或要開放網路服務），**階段 3 的安全項目不能拖到「社群 PR 壓力大了才補」，必須在 MVP 之後、開放給非本人使用之前就完成**——這正是 CreatorHub 目前最大的欠款。

---

## 9. 驗收指標與風險清單（供自建類似產品時直接套用）

### 9.1 驗收指標建議

| 類別 | 指標 | claude-video 現況作為參考基準 |
|---|---|---|
| 功能正確性 | 抽幀/轉錄輸出與人工核對的時間戳誤差 | 未見公開量化數據，需自行建 golden set |
| 效能 | 49 分鐘影片：transcript-only ≈4.5 秒、efficient ≈0.5 秒（含下載後）、balanced/token-burner ≈21 秒 | README 揭露基準，可作對照 |
| Token 成本 | 512×288 每幀 ≈197 image tokens | README 揭露，建議自建產品也公開此類換算表 |
| 測試覆蓋 | 9 個模組化 pytest（合成媒體，離線可跑） | 可作最低配置基準 |
| 發布紀律 | SemVer release + 建置產物 + CI 自動化 | 可直接複製 release.yml 模式 |
| 安全基線 | 至少：無選項注入、路徑絕對化、URL schema 驗證 | claude-video v0.1.3 已達成，可作最低門檻 |
| 治理成熟度 | CONTRIBUTING/SECURITY/issue template 齊全 | claude-video 尚未達成（42% health），自建產品應以超越它為目標 |

### 9.2 風險清單

| 風險 | 說明 | 建議緩解 |
|---|---|---|
| 上游平台/工具鏈斷裂 | `yt-dlp` 解析器、ffmpeg flag（如 `-vsync` 已被移除）隨版本失效 | 鎖版＋自動化相容性測試矩陣（多 ffmpeg/yt-dlp 版本） |
| Secret 明文 | `.env`/設定檔明文存 API key | 讀寫兩端一致做權限檢查，或改用 OS keychain |
| 下載端邊界 | 無 SSRF/大小/逾時防護 | 若產品會被非本人或服務化使用，必須補上 host allowlist、逾時、大小上限 |
| 單一維護者 bus factor | 核心 commit 集中一人 | 及早建立 CONTRIBUTING、code owner、多人 review 習慣 |
| 測試門檻缺失 | 無 PR-gate CI，issue/PR 堆積 | MVP 後立刻掛 CI 測試門檻，不要等社群壓力 |
| 供應鏈（第三方 API） | 音檔上傳到 Groq/OpenAI，無明確資料保留政策揭露 | 產品文件需明確告知使用者資料流向與供應商政策連結 |
| 版本同步 | 多份 plugin manifest 需手動同步版本號 | 建議改自動化腳本檢查/生成，降低人為疏漏 |

---

## 10. 主要來源（全部第一手）

- [Repository](https://github.com/bradautomates/claude-video)
- [Repo metadata API](https://api.github.com/repos/bradautomates/claude-video)
- [README.md](https://github.com/bradautomates/claude-video/blob/main/README.md)
- [Recursive source tree API](https://api.github.com/repos/bradautomates/claude-video/git/trees/main?recursive=1)
- [CHANGELOG.md](https://github.com/bradautomates/claude-video/blob/main/CHANGELOG.md)
- [LICENSE](https://github.com/bradautomates/claude-video/blob/main/LICENSE)
- [SKILL.md](https://github.com/bradautomates/claude-video/blob/main/skills/watch/SKILL.md)
- [scripts/watch.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/watch.py)
- [scripts/download.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/download.py)
- [scripts/frames.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/frames.py)
- [scripts/transcribe.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/transcribe.py)
- [scripts/whisper.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/whisper.py)
- [scripts/config.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/config.py)
- [scripts/setup.py](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/setup.py)
- [scripts/build-skill.sh](https://github.com/bradautomates/claude-video/blob/main/skills/watch/scripts/build-skill.sh)
- [hooks/hooks.json](https://github.com/bradautomates/claude-video/blob/main/hooks/hooks.json)
- [hooks/scripts/check-setup.sh](https://github.com/bradautomates/claude-video/blob/main/hooks/scripts/check-setup.sh)
- [.claude-plugin/plugin.json](https://github.com/bradautomates/claude-video/blob/main/.claude-plugin/plugin.json)
- [.codex-plugin/plugin.json](https://github.com/bradautomates/claude-video/blob/main/.codex-plugin/plugin.json)
- [.github/workflows/release.yml](https://github.com/bradautomates/claude-video/blob/main/.github/workflows/release.yml)
- [tests/](https://github.com/bradautomates/claude-video/tree/main/tests)
- [Contributors API](https://api.github.com/repos/bradautomates/claude-video/contributors)
- [Releases API](https://api.github.com/repos/bradautomates/claude-video/releases)
- [Community profile API](https://api.github.com/repos/bradautomates/claude-video/community/profile)
- [Issues（含 PR）](https://github.com/bradautomates/claude-video/issues)
- 對照：[CreatorHub 分析（2026-07-29）](./2026-07-29-creatorhub-analysis.md)

### 研究限制

- 15 分鐘時間盒內完成，未實際執行 `/watch`、未逐一讀完 79 個 open issue 全文、未讀 `tests/` 逐檔實作細節，也未做逐行原始碼稽核；架構與行為描述基於對原始碼／README／CHANGELOG 的第一手忠實摘要，未做語意執行驗證。
- 未查證 Groq/OpenAI 兩家 Whisper 供應商實際的資料保留與訓練使用政策，僅指出原始碼未揭露此資訊。
- Star/fork/issue 數字為研究當下快照，會持續變動。
