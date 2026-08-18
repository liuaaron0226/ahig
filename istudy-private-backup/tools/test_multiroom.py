# -*- coding: utf-8 -*-
"""測試「兩支影片分走不同機房」能否疊加頻寬。

背景：同機房 2 支平行 = 0.44 MB/s（比單支 0.68 還低），推測伺服器端限速。
但先前兩支都連 ds。若限速是「每機房每帳號」而非「每帳號」，分走 ds 與 cl4
就能疊加。本腳本用兩個分頁各鎖一個機房、同時抓 45 秒，比較合計吞吐。

對照組：單支 ds（基準）。
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "data" / "chrome-profile"
HOME = "https://istudy.way-to-win.com/cloud/video_main.php"
SAMPLE = 45

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

LIST_JS = """
(n) => {
  const out = [];
  for (const f of document.querySelectorAll('form')) {
    const nno = f.querySelector('input[name=media_nno]');
    if (!nno || !nno.value) continue;
    const box = f.closest('tr') || f.parentElement;
    const btn = box?.querySelector('button,input[type=submit]');
    const code = (btn?.textContent || btn?.value || '').trim();
    if (!code || code === '搜尋') continue;
    const extra = {};
    for (const i of f.querySelectorAll('input[type=hidden]')) extra[i.name] = i.value;
    out.push({ nno: nno.value, code, extra });
    if (out.length >= n) break;
  }
  return out;
}
"""

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


def grab_url(page, ep, ce, room_prefix):
    """開播放頁、切到指定機房，回傳該機房的串流網址。"""
    page.goto(f"{HOME}?ce={ce}&pageID=1", wait_until="domcontentloaded")
    page.wait_for_timeout(300)
    with page.expect_response(lambda r: ".m3u8" in r.url, timeout=90000) as ri:
        page.evaluate(OPEN_JS, dict(ep["extra"], media_nno=ep["nno"], ce=ce))
    url = ri.value.url
    page.wait_for_timeout(2500)
    info = page.evaluate(ROOMS_JS)
    if info:
        sel = f"#{info['selId']}" if info["selId"] else f"select[name='{info['selName']}']"
        opt = next((o for o in info["options"] if o["label"].startswith(room_prefix)), None)
        if opt and not opt["selected"]:
            with page.expect_response(lambda r: ".m3u8" in r.url, timeout=45000) as ri2:
                page.select_option(sel, value=opt["value"])
            url = ri2.value.url
    try:
        page.evaluate("() => document.querySelectorAll('video').forEach(v=>{v.pause();v.removeAttribute('src');v.load()})")
    except Exception:
        pass
    return url


def measure(urls: list[str], referer: str, ua: str, label: str) -> float:
    """同時抓所有 url，回傳合計 MB/s。"""
    sizes = {}
    procs = []
    tmpdir = tempfile.mkdtemp()
    for i, u in enumerate(urls):
        out = Path(tmpdir) / f"s{i}.mp4"
        p = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-user_agent", ua, "-headers", f"Referer: {referer}\r\n",
             "-i", u, "-c", "copy", "-bsf:a", "aac_adtstoasc", str(out)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append((p, out))
    time.sleep(SAMPLE)
    total = 0
    for p, out in procs:
        sz = out.stat().st_size if out.exists() else 0
        total += sz
        p.kill(); p.wait()
    rate = total / SAMPLE / 2**20
    print(f"{label}: {rate:.2f} MB/s（{len(urls)} 條連線）")
    return rate


def main() -> int:
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), channel="chrome", headless=False,
            viewport={"width": 1280, "height": 900})
        p1 = ctx.pages[0] if ctx.pages else ctx.new_page()
        p1.on("dialog", lambda d: d.accept())
        p2 = ctx.new_page()
        p2.on("dialog", lambda d: d.accept())
        try:
            p1.goto(f"{HOME}?ce=電子學&pageID=1", wait_until="domcontentloaded")
            p1.wait_for_timeout(1500)
            eps = p1.evaluate(LIST_JS, 2)
            if len(eps) < 2:
                print("找不到兩支課程（未登入？）")
                return 1
            ua = p1.evaluate("() => navigator.userAgent")
            print(f"測試素材：{eps[0]['code']}、{eps[1]['code']}\n")

            # 2026-08-17 重測：原本寫死的 ds+cl4 是當日最慢的兩台（0.56／0.58），
            # 拿最慢的組合驗證疊加會系統性低估。改用不同實體主機的最快兩台：
            # tp1(1.02, tp1.wa…) 與 tp3(0.94, tp2021…)。
            # 注意 tp6 與 tp1 同機、tp4 與 tp3 同機，不能拿來當第二條線。
            ROOM_A, ROOM_B = "機房tp1", "機房tp3"

            u_a = grab_url(p1, eps[0], "電子學", ROOM_A)
            base = measure([u_a], p1.url, ua, f"對照組 單支 {ROOM_A}")

            u_a2 = grab_url(p1, eps[0], "電子學", ROOM_A)
            u_b = grab_url(p2, eps[1], "電子學", ROOM_B)
            h1 = re.sub(r"^https?://", "", u_a2).split(".")[0]
            h2 = re.sub(r"^https?://", "", u_b).split(".")[0]
            print(f"（實際主機：{h1} / {h2}）")
            multi = measure([u_a2, u_b], p1.url, ua, f"實驗組 {ROOM_A} + {ROOM_B}")

            print(f"\n結論：{multi/base:.2f}x")
            print("  > 1.5x → 分機房可疊加，改用雙機房並行")
            print("  ≈ 1.0x 或更低 → 限速在帳號層級，維持單支")
        finally:
            ctx.close()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
