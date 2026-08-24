# n+48 內容制衛生檢查：樣式清單、涵蓋範圍與命中檔

依協調者裁定 n+80（三）之要求產出。**數字皆為現算**（n+61），
**清單只列路徑與處數，不含任何標題文字**（n+80 明令）。

## 一、現行檢查的實際定義

```
git ls-files .scratch/ | xargs grep -l '^TITLE:\|^ABS:\|"abstractText"\|^   T: '
```

| 樣式 | 針對的形態 |
|---|---|
| `^TITLE:` | 逐頁轉存檔之題名行 |
| `^ABS:` | 逐頁轉存檔之摘要行 |
| `"abstractText"` | API 原始回應之摘要欄位 |
| `^   T: ` | 某一種縮排題名行 |

**範圍是 `.scratch/`，不是整個 repo。** 現算結果：

| 範圍 | 命中檔 | 處數 |
|---|---|---|
| `.scratch/`（＝實際檢查範圍） | 0 | 0 |
| 全體追蹤檔 | 4 | 7 |

🚨 **範圍限縮是刻意且正確的**——把它擴大到全 repo 只會產生誤報。
全 repo 多出來的命中已逐處查看，**全部不是文獻內容**：

| 路徑 | 處數 | 實際是什麼 |
|---|---|---|
| `COORDINATION.md` | 4 | 檢查指令本身被引用（樣式字面，非資料） |
| `ahig/ahig/search/candidates.py` | 1 | Europe PMC API 之欄位名 `abstractText`（程式碼，非資料） |
| `ahig/tests/test_candidate_pool.py` | 1 | Europe PMC API 之欄位名 `abstractText`（程式碼，非資料） |
| `ahig/tests/test_prevalence_audit.py` | 1 | Europe PMC API 之欄位名 `abstractText`（程式碼，非資料） |

⚠️ 附帶查到一處不一致：本看板**第 94 行**引用的檢查指令是舊版，
少了 `^   T: ` 這一項。⚠️ 看板頂部規約與 n+48 正文不同步，
照頂部抄指令的人會跑到一個比現行更鬆的檢查。

## 二、n+80 所報 53 檔 118 處，對應哪一種掃法

n+80 未載明其樣式，故以三種候選掃法各自實算對照：

| 掃法 | 樣式 | 範圍 | 命中檔 | 處數 |
|---|---|---|---|---|
| A | 〈 後緊接英文 | `.scratch/` | 41 | 80 |
| A | 〈 後緊接英文 | 全 repo | 44 | 350 |
| B | 〈…〉內含 3 個以上連續英文字母 | `.scratch/` | 54 | 124 |
| B | 〈…〉內含 3 個以上連續英文字母 | 全 repo | 56 | 481 |
| C | 〈…〉任意內容 | `.scratch/` | 60 | 148 |
| C | 〈…〉任意內容 | 全 repo | 64 | 598 |

**最接近 n+80（53 檔／118 處）者為掃法 B、範圍 `.scratch/`：54 檔／124 處。**

⚠️ 仍有小幅差距。可能來自 n+80 掃描時點之後的改動（第 402–403 輪
已新增檔案並合併主幹），也可能來自樣式細節。**本執行室不宣稱已重現
n+80 的掃法**——協調者未公布其樣式，逼近不等於重現。若要對齊，
請協調者提供其實際使用的樣式。

## 三、命中檔完整清單（掃法 B、範圍 `.scratch/`）

共 **54 檔、124 處**。⚠️ 只列路徑與處數。

| # | 路徑 | 處數 |
|---|---|---|
| 1 | `.scratch/ch76_b4.json` | 32 |
| 2 | `.scratch/mk_p243.py` | 5 |
| 3 | `.scratch/mk_p249.py` | 4 |
| 4 | `.scratch/mk_p252.py` | 4 |
| 5 | `.scratch/mk_p260.py` | 4 |
| 6 | `.scratch/ch_p5.json` | 3 |
| 7 | `.scratch/mk_p258.py` | 3 |
| 8 | `.scratch/mk_p259.py` | 3 |
| 9 | `.scratch/mk_p263.py` | 3 |
| 10 | `.scratch/mk_p291.py` | 3 |
| 11 | `.scratch/ch76_b2.json` | 2 |
| 12 | `.scratch/ch_orph.json` | 2 |
| 13 | `.scratch/mk_p224.py` | 2 |
| 14 | `.scratch/mk_p225.py` | 2 |
| 15 | `.scratch/mk_p226.py` | 2 |
| 16 | `.scratch/mk_p228.py` | 2 |
| 17 | `.scratch/mk_p246.py` | 2 |
| 18 | `.scratch/mk_p253.py` | 2 |
| 19 | `.scratch/mk_p254.py` | 2 |
| 20 | `.scratch/mk_p268.py` | 2 |
| 21 | `.scratch/mk_p272.py` | 2 |
| 22 | `.scratch/mk_p280.py` | 2 |
| 23 | `.scratch/mk_p283.py` | 2 |
| 24 | `.scratch/n78_tail_dec_025.py` | 2 |
| 25 | `.scratch/n78_tail_dec_050.py` | 2 |
| 26 | `.scratch/n78_tail_dec_125.py` | 2 |
| 27 | `.scratch/ch76_b3.json` | 1 |
| 28 | `.scratch/ch_p2.json` | 1 |
| 29 | `.scratch/ch_p4.json` | 1 |
| 30 | `.scratch/mk_p222.py` | 1 |
| 31 | `.scratch/mk_p223.py` | 1 |
| 32 | `.scratch/mk_p227.py` | 1 |
| 33 | `.scratch/mk_p230.py` | 1 |
| 34 | `.scratch/mk_p235.py` | 1 |
| 35 | `.scratch/mk_p236.py` | 1 |
| 36 | `.scratch/mk_p242.py` | 1 |
| 37 | `.scratch/mk_p244.py` | 1 |
| 38 | `.scratch/mk_p245.py` | 1 |
| 39 | `.scratch/mk_p255.py` | 1 |
| 40 | `.scratch/mk_p256.py` | 1 |
| 41 | `.scratch/mk_p262.py` | 1 |
| 42 | `.scratch/mk_p271.py` | 1 |
| 43 | `.scratch/mk_p273.py` | 1 |
| 44 | `.scratch/mk_p274.py` | 1 |
| 45 | `.scratch/mk_p285.py` | 1 |
| 46 | `.scratch/mk_p287.py` | 1 |
| 47 | `.scratch/mk_p293.py` | 1 |
| 48 | `.scratch/mk_p294.py` | 1 |
| 49 | `.scratch/mk_p296.py` | 1 |
| 50 | `.scratch/n68_tail_dec_025.json` | 1 |
| 51 | `.scratch/n68_tail_j025.py` | 1 |
| 52 | `.scratch/n70_std_tail.json` | 1 |
| 53 | `.scratch/n78_tail_dec_075.py` | 1 |
| 54 | `.scratch/n78_tail_dec_175.py` | 1 |

## 四、涵蓋範圍聲明

**✅ 現行檢查抓得到**：文獻內容以「行首關鍵字」或「JSON 欄位名」形式
出現者——即逐頁轉存檔（`TITLE:`／`ABS:`）與 API 原始回應
（`"abstractText"`）。這兩種是**大量傾印**的形態，也正是歷史上兩次事故
（第 329 輪 39 檔、n+48 當輪）的形態。⚠️ 換句話說，這組樣式是照著
**已經發生過的事故**長出來的，它防的是重演，不是未知。

**❌ 現行檢查抓不到**（以下皆為本檔實測，非推測）：

1. **〈…〉內之逐字題名**——判讀理由裡引述原標題的寫法，即 n+80 發現者。
   命中數見第三節。
2. **不加任何標記、直接寫在中文判讀理由裡的英文題名或摘要片語**。
   🚨 本檔**不宣稱**已量到這一類——沒有可靠樣式能把它與執行室自己寫的
   英文說明（協調紀錄、docstring、commit 訊息引文）區分開。
   ⚠️ 故第三節的數字是**下界，不是總量**。

**🚨 這個聲明本身的效力邊界**：以上「抓不到」清單列的是**我測過的**。
凡未列者不代表安全，只代表沒測過。**綠燈不等於被檢查過**（n+80 三）。

**⚠️ 本檔不改動 n+48 的樣式。** 加嚴樣式會改變「PASS」這個字的意義，
而過去約三十輪心跳的 PASS 都是拿舊樣式跑出來的——換樣式而不換名稱，
會讓歷史紀錄變成不可比較，且會讓人以為那三十輪也被新樣式檢查過。
是否改採新樣式、舊 PASS 如何重新表述，屬裁定層級，已列看板待協調者。
