# ADR-0006：AHIG 的公開／私密邊界與白名單提交

- 狀態：已接受
- 日期：2026-08-13
- 情境：在既有 repo 內建立 AHIG（運動員健康知識圖譜）的公開契約與驗證器

## 問題

AHIG 同時牽涉三類東西：

1. **公開核心** — 契約 schema、SHACL shapes、確定性檢查、統計、虛構 fixtures、
   校準契約、文件。這些應該可以被讀、被 review、被 fork。
2. **個人健康 ABox** — 使用者自己的體重、血檢、訓練紀錄。
3. **論文全文** — 合法取得的 PDF，多數不可再散布。

第 2、3 類若混進第 1 類，整個專案就變成不可分享的。而混入的方式往往不是
「把檔案複製進去」這麼明顯，比較常見的是程式裡寫死一條 `health/log/2026-08.md`
的路徑、或在 fixture 裡放一筆真實數值當範例。

這個 repo 已經有一個現成的教訓：`health/` 底下的私密紀錄**已經被 git tracking**
（見下方遺留問題）。

## 決策

**目錄分離**：`ahig/` 只放公開核心。個人 ABox 與全文位於外部私有資料根。

**環境變數 fail-closed**：私有資料命令從 `AHIG_PRIVATE_ROOT` 取得資料根，
未設定時**拋出而非採用預設值**：

```python
def private_root() -> Path:
    raw = os.environ.get("AHIG_PRIVATE_ROOT")
    if not raw:
        raise RuntimeError("AHIG_PRIVATE_ROOT is required for private-data commands")
    return Path(raw).expanduser().resolve()
```

「未設定時寫到某個合理的預設位置」是最容易讓私密資料流進公開目錄的設計。
拋出比較吵，但吵是對的。

**公開驗證不依賴私有根**：`python -m ahig.cli verify --all` 在完全沒有
`AHIG_PRIVATE_ROOT` 的環境要能跑完。這條讓公開部分可以被別人驗證。

**白名單提交**：`ahig/.gitignore` 採白名單式——放行程式、schema、shape、
公開文件、虛構 fixtures 與 gold-test 結構；全文、真實 metadata、資料庫、
索引、job output、log、秘密與私有資料根一律拒絕。黑名單會漏，白名單只會誤擋。

**自動掃描**：`verify --all` 的第 10 階段掃描 `ahig/` 下所有
`.py`/`.json`/`.md`/`.ttl`，命中私密路徑 token 即失敗。這道掃描的實作有個
細節：token 必須以字串拼接寫出，否則掃描器自己會成為第一個命中——那會讓
它永遠紅燈，實務上等於被關掉。

## 後果

- 公開部分可以獨立被驗證與分享。
- 多一個環境變數要設，私有資料命令在新環境第一次跑一定會失敗一次。這是刻意的。
- 掃描是字串比對，能抓路徑外洩，抓不到「把真實數值抄進 fixture」。後者只能靠
  review 與「fixture 一律虛構」的紀律。

## 遺留問題（未在本階段處理）

`health/` 底下的個人健康紀錄**已經在 git 追蹤中**（`health/log/2026-08.md`、
`health/profile.md` 等）。本 ADR 只界定 AHIG 的邊界，沒有處理這個既有事實。

untrack、刪除或歷史重寫都是不可逆且會改變既有 commit 的操作，需要使用者
明確決定。已另開 `ready-for-human` issue 追蹤：
`.scratch/ahig-v2-1/issues/10-health-data-git-tracked.md`。
