---
name: multi-session-architecture
description: Split a project into coordinated Claude Code chatrooms — a coordinator room plus per-workstream executor rooms — with a git-mailbox coordination board, one-branch-per-room discipline, ADR decision records, and an owner audit loop. Use when multiple Claude sessions or agents work the same repo in parallel, when a session's context keeps getting polluted by unrelated sub-tasks, or when the user asks to organize/split project work across chatrooms.
---

# 多 session 專案架構（房間制＋git 信箱）

把一個專案拆成多個各司其職的 Claude Code 聊天室（房間），用 git 當唯一
可靠的共享通道。本 skill 來自 AHIG 專案的實戰記錄（見文末實例）。

## 為什麼需要

- Session 之間**不共享記憶**：每個聊天室只知道自己對話裡的事。
- 單一聊天室混做所有事，context 會被雜事污染，追進度要翻整段對話。
- 兩個 agent 改同一批檔案會撞車（本方法的起點就是一次真實撞車）。

## 核心概念

1. **房間（room）**：一個聊天室＝一個職責。分兩類：
   - **協調中心**（唯一）：進度總表、決策裁定、合併主幹、看板維護。
     不做長流水線執行。
   - **執行室**（多個）：各領一條工作線（如「本機資料管線」「工具偵察」
     「文件/ADR」）。有問題在自己房間解決，跨房事務走信箱。
2. **看板（`COORDINATION.md`）**＝git 信箱＋唯一權威進度：
   - 頂部「狀態快照」由協調者維護——任何房間回答「現在進度如何」都以它
     為準，不憑各自的對話記憶。
   - 跨房訊息：寫進看板 → commit → push；對方開工先 pull。
   - 從 `CLAUDE.md` 指一行過去，讓新房間自動被導到看板。
3. **一房一分支**：主幹只由協調者合併；執行室在自己的分支工作，
   測試全綠才推。
4. **章程（charter）**：每個房間開設時寫明「職責」與「禁區」，登記在
   看板的房間表。沒有章程的房間不開——房間不是越多越好，每多一房就多
   一份協調成本。
5. **決策走 ADR**（`docs/adr/NNNN-*.md`）：拍板的事留檔，房間輪替或
   context 清空後決策不失傳。
6. **擁有者（人）**：只在兩種時刻出現——拍板 ADR、做抽查。其餘時間
   房間之間自轉。

## 建立步驟

1. 在 repo 根建 `COORDINATION.md`：狀態快照區＋房間章程表＋工作線表
   （見下方模板）；`CLAUDE.md` 加一行「開工前先讀 COORDINATION.md」。
2. 把現任聊天室改名為協調中心（雲端 session 可用 set_session_title），
   在看板登記。
3. 每條活躍工作線開一個房間：開場訊息講清楚章程、分支、
   「開工先 git pull、有結果寫看板並 push」。
4. 協調者定期把各房推上來的分支合併主幹（`--ff-only` 優先；看板同檔
   撞車時手工融合兩邊事實，不要挑一邊丟一邊）。

## 看板模板

```markdown
# <專案名> 多 session 協調看板

git 是唯一可靠的共享事實：開工先 `git fetch`，收工必 push。

## 房間架構章程
| 房間 | 載體 | 職責 | 禁區 |
|---|---|---|---|
| 🏛 協調中心 | <session> | 總表/裁定/合併/看板 | 不執行流水線 |
| … | | | |

## 分支規則
- 主幹：`<trunk>`。不要直接推主幹，合併由協調者做。
- 每房一分支；push 前測試全綠。

## 專案狀態快照（協調者維護）
- ✅/⏳/⚠️ 條列，含測試基準

## <跨房訊息區：報告、裁定、工作包>

## 工作線
| 工作線 | 分支 | Session | 狀態 |
```

## 紀律規則（實戰淬煉）

- **勤推勤拉**：session 容器是暫時的，沒推上去的工作等於不存在。
- **工作包制**：協調者派工用編號工作包（W1、W2…）寫進看板，含完成
  定義；執行室領走後在自己分支交付。
- **撞車處理**：看板同檔衝突是常態（兩房同時報告），融合雙方事實後
  由協調者裁定合併——衝突不是事故，是通道在工作。
- **誠實傳染**：報告裡的統計但書、拿不到的資訊寧缺勿造——房間之間
  互相校正過度解讀，是這個架構對準確度的真實貢獻。
- 執行力來自房間並行與 context 專注；**準確度來自護欄**（測試、審查、
  ADR、抽查迴路），房間只是讓護欄好執行的容器。

## 實例：AHIG 專案（2026-08）

- 房間：協調中心（cloud）＋B.11 執行室（本機，持有 private root）＋
  工具偵察室（cloud）＋擁有者。
- 信箱實績：執行室推 LLM 判讀報告（自帶 n=6 上界但書）→ 協調者合併、
  裁定 model.version、派 W1/W2 → 全程擁有者只說了一個「推」字。
- 決策留檔：ADR-0007（LLM 第二審）、0008（統計終止）、0009（AI 判讀
  信任模型）——三份都是跨房協作的產物。
- 教訓入章程：兩房同時改看板的 race（融合解決）、無章程房間的
  檔案撞車（撞出本方法）。
