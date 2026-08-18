# -*- coding: utf-8 -*-
"""iStudy 批次備份 — 專用 Chrome 視窗版（使用者 2026-08-16 選定路線 A）。

背景：Chrome 136+ 起，Google 為防 cookie 竊取，在「預設 user-data-dir」上直接
忽略 --remote-debugging-port，所以 CDP 連使用者主 Chrome 這條路走不通（實測
Chrome 151，DevToolsActivePort 不生成）。改用 Playwright 開一個**專用 profile
的 Chrome 視窗**，由使用者自己在該視窗登入 iStudy 一次（帳密永不經過本程式）。

政策（使用者 2026-08-16 拍板，取代 2026-07-23 spec 的保守規則）：
- AES-128 HLS 不視為 DRM：金鑰由平台直接發給已登入 session，ffmpeg 走與播放器
  完全相同的授權路徑。仍絕不碰 EME/Widevine/DASH（偵測到即中止該支）。
- 僅下載使用者本人付費課程，供個人備考離線使用。

注意：iStudy 會統計同時上線 session，於第二個瀏覽器登入可能導致主 Chrome 的
iStudy 被登出，屬正常現象。

用法（首次會停下來等你在跳出的視窗登入）：
  python tools/grab_istudy.py --docs-only     # 只抓講義 PDF（快、先驗證管線）
  python tools/grab_istudy.py --limit 1       # 試抓 1 支影片
  python tools/grab_istudy.py --skip-docs     # 影片全量（可中斷重跑）
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from urllib.parse import unquote, urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "data" / "chrome-profile"
OUT_ROOT = Path(r"F:\istudy-backup")
STATE_FILE = OUT_ROOT / "state.json"
DOCS_STATE = OUT_ROOT / "docs_state.json"
LOG_FILE = OUT_ROOT / "grab.log"
HOME = "https://istudy.way-to-win.com/cloud/video_main.php"
LOGIN_TIMEOUT = 12 * 60 * 60  # 等登入不要放棄：逾時退出只會讓整輪白跑，寧可一直等使用者回來
KEEPALIVE_SECONDS = 110  # 站方閒置登出門檻未知，取兩分鐘內較安全
MAX_ROUNDS = 3           # 斷網／暫時性錯誤留下的 failed，自動再跑幾輪

TARGETS = [
    ("電子學", re.compile(r"^114暑電子(?:\(劉\))?\d"), "電子學/114暑電子"),
    ("電子學", re.compile(r"^115暑電子(?:\(劉\))?\d"), "電子學/115暑電子"),
    ("工數", re.compile(r"^115春微方\(喻\)\d"), "工數/115春微方"),
    ("工數", re.compile(r"^115暑微方\(喻\)\d"), "工數/115暑微方"),
    ("線性代數", re.compile(r"^115春矩陣\(喻\)\d"), "線代/115春矩陣"),
    ("線性代數", re.compile(r"^115暑線代(?:\(喻\))?\d"), "線代/115暑線代"),
    # 多益（2026-08-16 加入）：加分項，排在最後下載。
    # 2026-08-17 收窄：原本用 ^11[45][春暑秋題]?多益 把 114 年與其他季別也掃進來（45 集），
    # 但使用者實際在上的只有 115 春季班揚洋這一班共 13 集（01A、01B、02–11、12-The End）。
    ("多益", re.compile(r"^115春多益\d"), "多益/115春多益"),
]
DOC_CE = ["電子學", "工數", "線性代數", "多益"]
BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

SCAN_JS = """
() => {
  const rows = [];
  for (const f of document.querySelectorAll('form')) {
    const nno = f.querySelector('input[name=media_nno]');
    if (!nno || !nno.value) continue;
    const box = f.closest('tr') || f.parentElement;
    const btn = box?.querySelector('button,input[type=submit]');
    const code = (btn?.textContent || btn?.value || '').trim();
    if (!code || code === '搜尋') continue;
    const cells = [...(box?.querySelectorAll('td') || [])].map(td => td.textContent.trim());
    const extra = {};
    for (const i of f.querySelectorAll('input[type=hidden]')) extra[i.name] = i.value;
    rows.push({ nno: nno.value, code, cells, extra });
  }
  const pags = [...document.querySelectorAll('a')].map(a => a.textContent.trim())
    .filter(t => /^\\[?\\d+\\]?$/.test(t)).map(t => parseInt(t.replace(/\\D/g, '')));
  return { rows, maxPage: pags.length ? Math.max(...pags) : 1 };
}
"""

OPEN_JS = """
(payload) => {
  const f = document.createElement('form');
  f.method = 'POST'; f.action = 'video_content_show_newtab.php'; f.target = '_self';
  for (const [n, v] of Object.entries(payload)) {
    const i = document.createElement('input');
    i.type = 'hidden'; i.name = n; i.value = v; f.appendChild(i);
  }
  document.body.appendChild(f); f.submit();
}
"""

# 講義連結實際長相：note_download.php?<編碼參數>（無副檔名），文字尾端帶 (365KB )
DOCS_JS = """
() => [...document.querySelectorAll('a')]
  .filter(a => {
    const h = a.getAttribute('href') || '';
    const t = (a.textContent || '').replace(/\\s+/g, ' ').trim();
    return /note_download\\.php/i.test(h)
        || /\\.(pdf|zip|rar|doc|docx)(\\?|$)/i.test(h)
        || (h && /\\(\\s*\\d+(\\.\\d+)?\\s*[KMG]?B\\s*\\)/.test(t));
  })
  .map(a => ({ href: a.getAttribute('href'), text: a.textContent.replace(/\\s+/g, ' ').trim() }));
"""

DRM_INIT = """
(() => {
  window.__DRM__ = false;
  const o = navigator.requestMediaKeySystemAccess?.bind(navigator);
  if (o) navigator.requestMediaKeySystemAccess = (...a) => { window.__DRM__ = true; return o(...a); };
})();
"""


def log(msg: str) -> None:
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


LINE_HOST = "access.line.me"
LINE_MAX_CLICKS = 5      # 點不動就別再瞎點，退回人工
# 名稱語意明確，沒有文字也可以放心點：
LINE_SAFE_SELECTORS = ("button[name='allow']", "button.c-button--allow")
# 泛用 selector，必須文字命中 LINE_OK_TEXTS 才點，免得按到別的東西：
LINE_GENERIC_SELECTORS = ("form button[type='submit']", "button[type='submit']", "button")
LINE_OK_TEXTS = ("允許", "同意", "登入", "許可", "Allow", "Log in", "Login", "Confirm")
LINE_NO_TEXTS = ("取消", "拒絕", "不允許", "Cancel", "Deny", "Reject")


def line_pages(page) -> list:
    """LINE 登入可能開在新分頁，所以掃整個 context 而不是只看當前 page。"""
    try:
        pages = list(page.context.pages)
    except Exception:
        pages = [page]
    out = []
    for p in pages:
        try:
            if LINE_HOST in p.url:
                out.append(p)
        except Exception:
            pass
    return out


def try_line_consent(page) -> bool:
    """帳號已綁定並授權過 LINE 時，OAuth 頁只剩一顆確認鈕，替使用者按下去。

    界線：只點按鈕。一旦頁面出現密碼欄（久未登入／風控要求重新驗證），立刻放手
    交回人工——本程式永遠不碰帳密欄位，就算 Chrome profile 裡存了也不代填。
    """
    for p in line_pages(page):
        try:
            if p.locator("input[type='password']").count():
                log("LINE 要求重新輸入密碼 — 不代填，請在【專用 Chrome 視窗】手動登入")
                return False
            for sel in LINE_SAFE_SELECTORS + LINE_GENERIC_SELECTORS:
                loc = p.locator(sel)
                for i in range(min(loc.count(), 5)):
                    btn = loc.nth(i)
                    if not btn.is_visible():
                        continue
                    label = (btn.inner_text() or "").strip()
                    if any(t in label for t in LINE_NO_TEXTS):
                        continue
                    if sel in LINE_GENERIC_SELECTORS and not any(t in label for t in LINE_OK_TEXTS):
                        continue
                    btn.click(timeout=5000)
                    log(f"已自動按下 LINE 確認鈕（{sel}｜{label or '無文字'}）")
                    p.wait_for_timeout(3000)
                    return True
        except Exception as exc:  # noqa: BLE001
            log(f"自動按 LINE 確認鈕失敗，交回人工：{str(exc)[:120]}")
            return False
    return False


def wait_login(page) -> None:
    deadline = time.monotonic() + LOGIN_TIMEOUT
    told = False
    auto_clicks = 0
    while time.monotonic() < deadline:
        try:
            url, body = page.url, page.locator("body").inner_text()
        except Exception:
            raise RuntimeError("專用 Chrome 視窗被關閉了，請重跑並保持視窗開啟")
        if "video_main.php" in url and "index_login.php" not in url and "尚未登入" not in body:
            log("登入完成")
            return
        if not told:
            log("=" * 58)
            log("偵測到已登出。此帳號已綁定 LINE，會先嘗試自動按下 LINE 的確認鈕。")
            log("若自動沒成功、或 LINE 要求重新輸入密碼，請在【專用 Chrome 視窗】手動登入。")
            log("登入後回到課程頁即可，程式會自動繼續。")
            log("=" * 58)
            told = True
        if auto_clicks < LINE_MAX_CLICKS and try_line_consent(page):
            auto_clicks += 1
            page.wait_for_timeout(2000)
            continue
        if line_pages(page):
            # 人（或上面的自動點擊）正停在 LINE 流程上，別把頁面導回 iStudy 打斷它
            page.wait_for_timeout(2000)
            continue
        page.wait_for_timeout(2000)
        if "istudy.way-to-win.com" not in page.url:
            try:
                page.goto(HOME, wait_until="domcontentloaded")
            except Exception:
                pass
    raise TimeoutError("等不到登入")


def keepalive(page) -> None:
    """對同源發輕量請求，避免下載期間被站方以「閒置過久」登出。"""
    try:
        page.evaluate(
            "() => fetch('video_main.php?ce=%E9%9B%BB%E5%AD%90%E5%AD%B8&pageID=1',"
            " {cache: 'no-store'}).then(() => 1).catch(() => 0)")
    except Exception:
        pass


NET_ERR = ("net::", "ERR_NAME_NOT_RESOLVED", "ERR_INTERNET_DISCONNECTED",
           "ERR_CONNECTION", "ERR_NETWORK", "ERR_TIMED_OUT", "ERR_ADDRESS_UNREACHABLE")


def is_net_error(exc: Exception) -> bool:
    s = str(exc)
    return any(k in s for k in NET_ERR)


def wait_for_network(page, timeout_seconds: int = 3600) -> bool:
    """網路中斷時等它回來。不等的話一斷線就會在幾秒內把整個佇列標記成失敗。"""
    log("⚠ 網路異常，暫停下載並等待連線恢復…")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        time.sleep(30)
        try:
            page.goto(HOME, wait_until="domcontentloaded", timeout=30000)
            log("網路已恢復，繼續下載")
            return True
        except Exception:
            continue
    log("✗ 等待網路恢復逾時")
    return False


def logged_in(page) -> bool:
    try:
        body = page.locator("body").inner_text()
        return "index_login.php" not in page.url and "尚未登入" not in body
    except Exception:
        return False


def goto_retry(page, url: str, tries: int = 4) -> bool:
    """列表分頁偶爾會 ERR_ABORTED（站方轉址／連線抖動），重試而不是讓整輪掛掉。"""
    for i in range(tries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            return True
        except Exception as exc:  # noqa: BLE001
            if i == tries - 1:
                log(f"  ✗ 載入失敗（已重試 {tries} 次）：{str(exc)[:90]}")
                return False
            if is_net_error(exc):
                wait_for_network(page)
            else:
                time.sleep(3)
    return False


def scan(page, ce: str) -> list[dict]:
    rows, pg, mx = [], 1, 1
    while pg <= mx and pg < 15:
        if not goto_retry(page, f"{HOME}?ce={ce}&pageID={pg}"):
            pg += 1
            continue
        page.wait_for_timeout(400)
        try:
            data = page.evaluate(SCAN_JS)
        except Exception as exc:  # noqa: BLE001
            log(f"  ✗ 解析第 {pg} 頁失敗：{str(exc)[:80]}")
            pg += 1
            continue
        mx = max(mx, data["maxPage"])
        for r in data["rows"]:
            joined = "".join(r["cells"])
            r["campus"] = "北" if "台北" in joined else ("壢" if "中壢" in joined else "?")
            r["title"] = r["cells"][-1].replace("\n", " ") if r["cells"] else ""
            r["ce"] = ce
            rows.append(r)
        pg += 1
    return rows


GRAD_HUB = Path(r"C:\Users\User\Desktop\claude\grad-exam-hub\data")


def _norm(code: str) -> str:
    """115春微方(喻)01 → 115春微方01；供 sprint/videos 對照表比對用。"""
    return re.sub(r"\([^)]*\)", "", code).strip()


def week_of_code() -> dict[str, int]:
    """讀衝刺計畫＋影片索引，算出每個集數代號屬於第幾週（W1 最優先）。"""
    try:
        sprint = json.loads((GRAD_HUB / "sprint.json").read_text(encoding="utf-8"))
        videos = json.loads((GRAD_HUB / "videos.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        log(f"（讀不到衝刺計畫，改用預設順序：{exc}）")
        return {}
    ch_week = {c["id"]: c.get("week", 99) or 99
               for s in sprint.get("subjects", []) for c in s.get("chapters", [])}
    out: dict[str, int] = {}
    for ch, eps in (videos.get("istudy", {}).get("byChapter") or {}).items():
        w = ch_week.get(ch, 99)
        for e in eps:
            k = _norm(e["code"])
            out[k] = min(out.get(k, 99), w)
    return out


# 115暑電子（使用者正在上的班、頁碼對得上手上的補充講義）01-24 已涵蓋 114暑 01-24 的內容；
# 114暑 25-32（回授/尼奎斯特/米勒補償/CMOS反向器/輸出級/穩壓器）才是 115暑 尚未教到的部分。
DUP_114 = re.compile(r"^114暑電子(?:\(劉\))?(?:0[1-9]|1\d|2[0-4])(?:\D|$)")
SERIES_RANK = {"電子學/115暑電子": 0, "電子學/114暑電子": 1}


def prioritize(eps: list[dict]) -> list[dict]:
    wmap = week_of_code()
    if not wmap:
        return eps

    def week_of(e) -> int:
        w = wmap.get(_norm(e["code"]), 99)
        if w < 99 and DUP_114.match(e["code"]):
            return 90  # 與 115暑 重複：留到最後再補，不佔正課頻寬
        return w

    def key(e):
        return (week_of(e), SERIES_RANK.get(e["series"], 0), e["series"], e["code"])
    ordered = sorted(eps, key=key)
    per: dict[int, int] = {}
    for e in ordered:
        per[week_of(e)] = per.get(week_of(e), 0) + 1
    label = {90: "114暑重複段", 99: "其餘/多益"}
    log("排序（W1 優先）：" + "、".join(
        f"{label.get(w, 'W'+str(w))}×{n}" for w, n in sorted(per.items())))
    return ordered


def discover(page) -> list[dict]:
    picked: dict[str, dict] = {}
    for ce in dict.fromkeys(t[0] for t in TARGETS):
        rows = scan(page, ce)
        seen_prefix: dict[str, int] = {}
        for r in rows:
            if r["campus"] != "北":
                continue
            pre = re.sub(r"\d+.*$", "", r["code"]) or r["code"]
            seen_prefix[pre] = seen_prefix.get(pre, 0) + 1
            for tce, pat, outdir in TARGETS:
                if tce == ce and pat.match(r["code"]):
                    r["series"] = outdir
                    picked.setdefault(outdir + "|" + r["code"], r)
                    break
        # 留下實際代號前綴，規則沒對上時可據此修正（不必重掃）
        log(f"[{ce}] 台北班代號前綴：" + "、".join(
            f"{k}×{v}" for k, v in sorted(seen_prefix.items(), key=lambda x: -x[1])[:12]))
    eps = sorted(picked.values(), key=lambda e: (e["series"], e["code"]))
    per: dict[str, int] = {}
    for e in eps:
        per[e["series"]] = per.get(e["series"], 0) + 1
    log("盤點：" + "、".join(f"{k}×{v}" for k, v in sorted(per.items())))
    save(OUT_ROOT / "manifest.json", {"episodes": eps})
    return eps


def grab_docs(page) -> None:
    import requests

    state = load(DOCS_STATE)
    sess = requests.Session()
    for c in page.context.cookies():
        if "way-to-win" in (c.get("domain") or ""):
            sess.cookies.set(c["name"], c["value"], domain=c["domain"].lstrip("."))
    ua = page.evaluate("() => navigator.userAgent")
    n_new = 0
    for ce in DOC_CE:
        eps = [r for r in scan(page, ce) if r["campus"] == "北"]
        if not eps:
            log(f"{ce}：找不到台北班課程，跳過")
            continue
        first = eps[0]
        page.evaluate(OPEN_JS, dict(first["extra"], media_nno=first["nno"], ce=ce))
        page.wait_for_timeout(4000)
        docs = page.evaluate(DOCS_JS)
        log(f"{ce}：講義 {len(docs)} 份")
        for d in docs:
            key = ce + "|" + d["href"]
            if state.get(key, {}).get("status") == "done":
                continue
            url = urljoin(page.url, d["href"])
            raw = re.sub(r"\(\s*\d+(\.\d+)?\s*[KMG]?B\s*\)", "", d["text"] or "").strip()
            name = BAD.sub("_", raw or "講義")[:110]
            try:
                r = sess.get(url, headers={"Referer": page.url, "User-Agent": ua}, timeout=180)
                r.raise_for_status()
                if len(r.content) < 2000:
                    raise RuntimeError(f"檔案過小 {len(r.content)}B（可能是錯誤頁）")
                # note_download.php 無副檔名：依 Content-Disposition／magic bytes 判斷
                suf = ""
                cd = r.headers.get("content-disposition", "")
                m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', cd)
                if m:
                    suf = Path(unquote(m.group(1).strip())).suffix
                if not suf:
                    head = r.content[:4]
                    suf = {b"%PDF": ".pdf", b"PK\x03\x04": ".zip", b"Rar!": ".rar"}.get(head, "")
                    if not suf and head[:2] == b"\xd0\xcf":
                        suf = ".doc"
                    suf = suf or ".pdf"
                if not name.lower().endswith(suf.lower()):
                    name += suf
                dest = OUT_ROOT / "講義" / ce / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                state[key] = {"status": "done", "path": str(dest), "bytes": len(r.content)}
                n_new += 1
                log(f"  ✓ {name}（{len(r.content)/2**20:.1f} MB）")
            except Exception as exc:  # noqa: BLE001
                state[key] = {"status": "failed", "err": str(exc)[:200]}
                log(f"  ✗ {name}：{str(exc)[:120]}")
            save(DOCS_STATE, state)
        page.goto(HOME, wait_until="domcontentloaded")
    log(f"講義完成，本輪新增 {n_new} 份")


# 2026-08-16 實測（45 秒取樣）：機房速度差 7.5 倍，且站方標籤不可信——
# ds(標「快")=0.68、cl4(超快)=0.64、tp6=0.29、tp3=0.19、tp1=0.17、cl2=0.11、cl3(標「飛快")=0.09
# 2026-08-17 20:29 重測（45 秒取樣）：排名與 08-16 完全翻轉，機房速度會逐日漂移。
# tp1(標「順」)=1.02、tp6=1.01、tp3(超快)=0.94、tp4(超快)=0.86、cl2(飛快)=0.75、
# cl4(超快)=0.58、ds(快)=0.56、cl3(飛快)=0.56 —— 昨天的冠軍 ds 今天墊底，標籤依然不可信。
# tp1/tp6 解析到同一台主機且上限僅 60 人（測時已 38 人），塞住就往後備切。
ROOM_PREF = ["機房tp1", "新機房tp6", "機房tp3", "機房tp4"]

# 2026-08-17 實測：tp1 單支 0.97、tp1+tp3 雙線合計 1.81（1.87x），
# 站方限速是「每機房每帳號」而非「每帳號」，所以並行必須分走不同實體主機。
# 主機對應：tp1/tp6→tp1.wa、tp3/tp4→tp2021、cl2→cl2.re、cl4→cl5178。
# 同機的不能並列，否則會退化成同機房互搶（舊實測 0.44，比單支還低）。
# 2026-08-18 03:08 重測：站方全站變慢（八台皆 0.15~0.34，傍晚是 0.56~1.02），
# 且在線人數反而更少（2~9 人 vs 傍晚 19~38），研判是站方自身排程作業佔頻寬。
# 當下最快：tp4=0.34（tp2021）、cl4=0.31（cl5178），兩台不同主機故可並行。
# 站方恢復後這個排名很可能再度翻轉，請重跑 test_rooms.py 校準。
ROOM_LANES = ["機房tp4", "機房cl4", "機房cl2", "機房ds"]


def lane_pref(k: int) -> list[str]:
    """第 k 條並行線的機房偏好：先鎖自己那台，塞住再退回共用順位。"""
    lane = ROOM_LANES[k % len(ROOM_LANES)]
    return [lane] + [r for r in ROOM_PREF if r != lane]

ROOMS_JS = r"""
() => {
  for (const sel of document.querySelectorAll('select')) {
    const opts = [...sel.options].filter(o => /機房/.test(o.textContent || ''));
    if (!opts.length) continue;
    return { selId: sel.id || '', selName: sel.getAttribute('name') || '',
             options: opts.map(o => ({ value: o.value,
                 label: (o.textContent || '').replace(/\s+/g, ' ').trim(),
                 selected: o.selected })) };
  }
  return null;
}
"""


def switch_room(page, url: str, rooms: list[str] | None = None) -> str:
    """切到指定機房（預設 ROOM_PREF）；失敗就沿用原本的串流網址。"""
    try:
        info = page.evaluate(ROOMS_JS)
        if not info:
            return url
        sel = f"#{info['selId']}" if info["selId"] else f"select[name='{info['selName']}']"
        for pref in (rooms or ROOM_PREF):
            opt = next((o for o in info["options"]
                        if o["label"].startswith(pref) and not o["selected"]), None)
            if opt is None:
                # 已經在偏好機房上就不用切
                if any(o["label"].startswith(pref) and o["selected"] for o in info["options"]):
                    return url
                continue
            with page.expect_response(lambda r: ".m3u8" in r.url, timeout=45000) as ri:
                page.select_option(sel, value=opt["value"])
            return ri.value.url
    except Exception as exc:  # noqa: BLE001
        log(f"  （機房切換略過：{str(exc)[:70]}）")
    return url


def capture_m3u8(page, ep: dict, rooms: list[str] | None = None) -> str:
    page.goto(f"{HOME}?ce={ep['ce']}&pageID=1", wait_until="domcontentloaded")
    page.wait_for_timeout(300)
    with page.expect_response(lambda r: ".m3u8" in r.url, timeout=90000) as ri:
        page.evaluate(OPEN_JS, dict(ep["extra"], media_nno=ep["nno"], ce=ep["ce"]))
    url = ri.value.url
    page.wait_for_timeout(2500)
    url = switch_room(page, url, rooms)
    if page.evaluate("() => !!window.__DRM__"):
        raise RuntimeError("偵測到 EME/DRM，依政策跳過")
    try:
        page.evaluate("() => document.querySelectorAll('video').forEach(v=>{v.pause();v.removeAttribute('src');v.load()})")
    except Exception:
        pass
    return url


def ffmpeg_grab(url: str, referer: str, ua: str, dest: Path) -> None:
    """後備路線：ffmpeg 逐段序列下載（單支約 0.8 MB/s）。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part.mp4")
    # +faststart：把 moov 索引搬到檔頭，播放器不必先讀到檔尾才知道片長
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
           "-user_agent", ua, "-headers", f"Referer: {referer}\r\n",
           "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc",
           "-movflags", "+faststart", str(tmp)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg rc={r.returncode}: {(r.stderr or '')[-300:]}")
    tmp.replace(dest)


def ytdlp_grab(url: str, referer: str, ua: str, dest: Path, frags: int) -> None:
    """主要路線：yt-dlp 原生 HLS 下載器，分段平行（-N）＋原生 AES-128 解密。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["yt-dlp", "--no-warnings", "--no-progress", "--hls-prefer-native",
           "--concurrent-fragments", str(frags), "--retries", "5",
           "--fragment-retries", "10", "--no-playlist",
           "--add-header", f"Referer:{referer}", "--user-agent", ua,
           "--remux-video", "mp4", "-o", str(dest.with_suffix(".%(ext)s")), url]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp rc={r.returncode}: {(r.stderr or '')[-300:]}")
    if not dest.exists():  # remux 後副檔名可能不同，找同名檔補救
        for cand in dest.parent.glob(dest.stem + ".*"):
            if cand.suffix.lower() in (".mp4", ".mkv", ".ts"):
                cand.replace(dest)
                break
    if not dest.exists():
        raise RuntimeError("yt-dlp 完成但找不到輸出檔")


def grab_video(url: str, referer: str, ua: str, dest: Path, frags: int, engine: str) -> None:
    if engine == "ffmpeg":
        ffmpeg_grab(url, referer, ua, dest)
        return
    try:
        ytdlp_grab(url, referer, ua, dest, frags)
    except RuntimeError as exc:
        log(f"  yt-dlp 失敗，改用 ffmpeg：{str(exc)[:120]}")
        ffmpeg_grab(url, referer, ua, dest)


def probe(dest: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(dest)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def run_round(page, todo: list[dict], state: dict, args, ua: str) -> int:
    """跑一輪下載，回傳本輪完成支數。取串流序列化、實際下載走執行緒池。"""
    done_n = 0
    ref = {"url": page.url}  # 給工作執行緒用的 Referer 快照（page 非執行緒安全）

    def fetch_one(e: dict, url: str):
        name = BAD.sub("_", f"{e['code']} {e['title']}").strip()[:115] + ".mp4"
        dest = OUT_ROOT / e["series"] / name
        grab_video(url, ref["url"], ua, dest, args.frags, args.engine)
        sec, size = probe(dest), dest.stat().st_size
        if sec < 60 or size < 5_000_000:
            raise RuntimeError(f"驗證失敗 dur={sec:.0f}s size={size}")
        return e, str(dest), sec, size

    for i in range(0, len(todo), args.jobs):
        batch = todo[i:i + args.jobs]
        if not logged_in(page):  # session 失效就停下來等人工重新登入，不要空轉失敗
            log("偵測到已登出，等待重新登入…")
            page.goto(HOME, wait_until="domcontentloaded")
            if not logged_in(page):
                wait_login(page)
        pairs: list[tuple[dict, str]] = []
        for k, e in enumerate(batch):  # 取串流網址必須序列化（共用同一個瀏覽器分頁）
            for attempt in range(3):
                try:
                    pairs.append((e, capture_m3u8(page, e, lane_pref(k))))
                    log(f"▶ {e['code']}｜{e['title'][:40]}")
                    break
                except Exception as exc:  # noqa: BLE001
                    if is_net_error(exc) and attempt < 2:
                        if wait_for_network(page):
                            if not logged_in(page):
                                wait_login(page)
                            continue
                    state[e["nno"]] = {"status": "failed", "code": e["code"], "err": str(exc)[:300]}
                    log(f"  ✗ 取串流失敗 {e['code']}：{str(exc)[:120]}")
                    save(STATE_FILE, state)
                    break
        ref["url"] = page.url
        if not pairs:
            continue
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(fetch_one, e, u): e for e, u in pairs}
            remaining = set(futs)
            while remaining:
                # 一支要 20 分鐘以上，期間瀏覽器不動會被站方以「閒置過久」登出，
                # 所以每 KEEPALIVE_SECONDS 對同源發一個輕量請求續命。
                finished, remaining = wait(remaining, timeout=KEEPALIVE_SECONDS)
                if remaining:
                    keepalive(page)
                for fut in finished:
                    e = futs[fut]
                    try:
                        e, path, sec, size = fut.result()
                        state[e["nno"]] = {"status": "done", "code": e["code"], "title": e["title"],
                                           "series": e["series"], "path": path,
                                           "sec": round(sec), "bytes": size}
                        done_n += 1
                        log(f"  ✓ {e['code']}・{sec/60:.0f} 分・{size/2**30:.2f} GB")
                    except Exception as exc:  # noqa: BLE001
                        state[e["nno"]] = {"status": "failed", "code": e["code"],
                                           "err": str(exc)[:300]}
                        log(f"  ✗ {e['code']}：{str(exc)[:160]}")
                    save(STATE_FILE, state)
        mb = sum(state.get(e["nno"], {}).get("bytes", 0) for e, _ in pairs
                 if state.get(e["nno"], {}).get("status") == "done") / 2**20
        el = time.time() - t0
        log(f"  ── 批次 {len(pairs)} 支・{el/60:.1f} 分・{mb/1024:.2f} GB・{mb/max(el,1):.2f} MB/s")
    return done_n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=2, help="同時下載幾支")
    ap.add_argument("--frags", type=int, default=8, help="單支影片同時抓幾個 HLS 分段（yt-dlp -N）")
    # 實測：本站 yt-dlp 分段平行反而較慢（2 支合計 0.34 MB/s vs ffmpeg 單支 0.52），
    # 瓶頸在伺服器端而非本地併發，故預設 ffmpeg。
    ap.add_argument("--engine", choices=["ffmpeg", "ytdlp"], default="ffmpeg",
                    help="ffmpeg=序列（本站實測較快）；ytdlp=分段平行（備用）")
    ap.add_argument("--docs-only", action="store_true")
    ap.add_argument("--skip-docs", action="store_true")
    args = ap.parse_args()

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), channel="chrome", headless=False,
            viewport={"width": 1440, "height": 950}, accept_downloads=True)
        ctx.add_init_script(DRM_INIT)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # 站方公告／LINE 綁定提示都要按「確定」流程才會往下走（dismiss 會卡住登入）
        def on_dialog(d):
            # 站方會連跳多個公告；晚到的 accept 可能打在已消失的對話框上，不能讓它炸掉整支腳本
            log(f"[對話框] {d.message[:80].replace(chr(10), ' ')}")
            try:
                d.accept()
            except Exception:
                pass

        page.on("dialog", on_dialog)
        try:
            page.goto(HOME, wait_until="domcontentloaded")
            wait_login(page)
            ua = page.evaluate("() => navigator.userAgent")

            if not args.skip_docs:
                grab_docs(page)
            if args.docs_only:
                return 0

            eps = prioritize(discover(page))
            state = load(STATE_FILE)
            todo = [e for e in eps if state.get(e["nno"], {}).get("status") != "done"]
            if args.limit:
                todo = todo[:args.limit]
            log(f"影片待抓 {len(todo)} 支（已完成 {len(eps)-len(todo)}）・並行 {args.jobs}")

            # 外層重試：斷網／站方抽風留下的 failed 自動再跑，最多 MAX_ROUNDS 輪
            for round_no in range(1, MAX_ROUNDS + 1):
                state = load(STATE_FILE)
                todo = [e for e in eps if state.get(e["nno"], {}).get("status") != "done"]
                if args.limit:
                    todo = todo[:args.limit]
                if not todo:
                    break
                if round_no > 1:
                    log(f"── 第 {round_no} 輪：重試 {len(todo)} 支未完成的")
                    if not logged_in(page):
                        page.goto(HOME, wait_until="domcontentloaded")
                        if not logged_in(page):
                            wait_login(page)
                n = run_round(page, todo, state, args, ua)
                ok = sum(1 for v in state.values() if v.get("status") == "done")
                log(f"── 第 {round_no} 輪結束：本輪 {n} 支；累計 done={ok}")
                if n == 0 and round_no > 1:
                    log("本輪毫無進展，停止重試")
                    break
            state = load(STATE_FILE)
            ok = sum(1 for v in state.values() if v.get("status") == "done")
            fail = sum(1 for v in state.values() if v.get("status") == "failed")
            log(f"全部結束：完成 {ok} 支、未完成 {fail} 支")
        finally:
            ctx.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
