# -*- coding: utf-8 -*-
"""對外抓取之閘門——把 n+146（三）四條限制做成機制，而不是靠記得遵守。

## 🚨 為什麼要有這支

擁有者將本室改為自動模式後，**手動模式原本兼任的「第三雙眼睛」消失了**（n+146 二）。
協調者據此立下四條限制，並指出：**自動模式下若本室開始硬闖，最長 25 分鐘才會被看見。**

**⚠️ 那四條若只寫在看板上，就是「規則寫下了也不會執行自己」**
（本 run 之第 15 型缺陷）。**🚨 故本檔把它們變成程式擋不過去的東西。**

## 四條限制（照抄 n+146 三，逐條對應到程式）

| # | 限制 | 本檔如何強制 |
|---|---|---|
| 1 | 同一主機不得高於每秒一次；**每輪總數須記入產物** | **逐跳**記錄該主機上次請求時刻並補足間隔；`counters()` 回傳總數與逐主機數 |
| 2 | 同一 URL 每輪🚫 重試不得超過一次；**403／429 一律不重試** | 記錄已試 URL；`4xx` 直接回傳不重試 |
| 3 | 主機明示拒絕自動化即**停止該主機全部後續請求**，並於回報列名 | `401`／`403`／`429`／`Retry-After` 出現即封鎖**最終回應之主機**；其後對該主機之請求（**含經由轉址抵達者**）一律不送出 |
| 4 | 🚫 不得偽裝身分（具名 UA 可） | UA 由本檔組出，含 `AHIG` 與聯絡信箱，**呼叫端不得覆寫**；**🚨 信箱缺失即不送出** |

## 🚨 n+150 補的兩個洞（⚠️ 兩個都是原本那四條自己的漏洞）

### 洞一：**封鎖以請求主機為鍵，而 `doi.org` 會轉址**

`urlopen` 預設自行跟隨轉址。於是：

> **🚨 對 `doi.org` 之請求若落到某出版社而回 403，被封鎖的是 `doi.org`，不是那家出版社。**
> **⚠️ 反過來，已被封鎖的出版社仍可經由 `doi.org` 再被請求到。**

**✅ 本檔改為自行逐跳跟隨轉址**（`_NoRedirect` 關掉自動跟隨）。因此：

- **封鎖鍵是最終回應之主機**，🚫 不是轉址器。
- **每一跳都先查封鎖表再送**——⚠️ 故已封鎖之出版社**無法**經由轉址器再被碰到。
- **每一跳都各自節流與計數**——**🚨 自動跟隨時，中間跳是繞過節流的**：
  兩個不同 DOI 若指向同一出版社，原本會在一秒內連打該出版社兩次。

### 洞二：**信箱缺失時 UA 會寫 `mailto:unset` 而請求照送**

**⚠️ 禮貌抓取之慣例是聯絡位址須真的可達**；`unset` 不是偽裝，但也不是可達的聯絡方式。
**🚨 而這不是假想**：本 run 已發生過一次「信箱已設為使用者層級卻未進入該次執行之環境」。

**✅ 依 n+150（三）改為 fail-closed：信箱為空即回 `SKIPPED`，🚫 不送出。**

## 🚨 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 擋得住：速率（逐跳）、同輪重試、對已拒絕主機之後續請求（**含轉址抵達**）、
  UA 覆寫、信箱缺失。
- 🚨 擋不住：**跨輪之累計行為**——⚠️ 本檔之狀態隨行程結束而消失，
  **🚫 故「同一 URL 不得重試超過一次」之保證僅限單次執行內。**
- 🚨 擋不住**同一主機之不同 URL**：⚠️ 限制 2 之鍵是 URL，
  **故換一個路徑就是一次新請求**（節流仍在，封鎖仍在）。
- ⚠️ 亦擋不住**呼叫端不使用本檔**——**🚨 本檔是工具不是沙箱。**
"""
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

MIN_INTERVAL = 1.0          # n+146(3).1：同一主機每秒至多一次
MAX_HOPS = 5                # 🚫 轉址鏈上限；超過即放棄，不無限跟隨
REDIRECTS = (301, 302, 303, 307, 308)
REFUSALS = (401, 403, 429)  # n+146(3).3：明示拒絕

_last = {}                  # host -> 上次請求之單調時刻
_count = {}                 # host -> 本次執行實際送出之請求數（逐跳）
_final = {}                 # host -> 本次執行作為「最終回應者」之次數
_tried = set()              # 本次執行已請求過之 URL（呼叫端所給者）
_blocked = {}               # host -> 拒絕之原因（其後不再請求）
_hops = 0                   # 轉址跳數合計


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """🚫 關掉自動跟隨——⚠️ 自動跟隨會讓中間跳繞過節流與封鎖檢查。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _send(url, headers, timeout, cap):
    """單一跳。🚫 不跟隨轉址、🚫 不重試、🚫 不拋例外。

    ⚠️ 這是唯一的網路接觸點，故也是自測時唯一要換掉的東西。
    """
    try:
        with _opener.open(urllib.request.Request(url, headers=headers),
                          timeout=timeout) as r:
            return {'status': r.status, 'headers': dict(r.headers),
                    'body': r.read(cap), 'url': r.url, 'error': ''}
    except urllib.error.HTTPError as e:
        # ⚠️ fp 為 None 時 addinfourl 沒設 .url，故必須有退路。
        return {'status': e.code, 'headers': dict(e.headers or {}), 'body': b'',
                'url': getattr(e, 'url', None) or url, 'error': 'HTTP %s' % e.code}
    except Exception as e:
        return {'status': 'ERR', 'headers': {}, 'body': b'', 'url': url,
                'error': '%s: %s' % (type(e).__name__, str(e)[:120])}


def contact_email():
    r"""取聯絡信箱：先環境變數，再 `HKCU\Environment`。

    🚨 這支放在閘門裡而不是各呼叫端，是因為 n+150（三）把「信箱缺失即不送出」
    立成了閘門的契約——**⚠️ 那麼「信箱從哪裡來」就是閘門的事。**

    **⚠️ 而且這不是假想**：`m1_step3_acquire.py` 開頭已載明本 run 發生過
    「信箱已以 PowerShell 設為使用者層級，但沒有進入該次執行之環境」。
    **🚨 只看 `os.environ` 會把一個設好的信箱讀成沒設，於是 fail-closed
    擋掉一次本來合規的抓取。**

    回傳 `(信箱或 None, 來源)`；**🚫 讀取登錄檔是唯讀查詢，不寫入。**
    """
    v = os.environ.get('AHIG_CONTACT_EMAIL')
    if v:
        return v, 'os.environ'
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
            v, _ = winreg.QueryValueEx(k, 'AHIG_CONTACT_EMAIL')
            return (v or None), r'HKCU\Environment'
    except (ImportError, OSError):
        return None, None


def masked(addr):
    """遮蔽本地部分——⚠️ 回報與產物一律用這個，🚫 不落盤完整信箱。"""
    if not addr or '@' not in addr:
        return '<無>'
    local, _, domain = addr.partition('@')
    keep = (local[0] + '*' * max(len(local) - 2, 1) + local[-1]
            if len(local) > 1 else '*')
    return '%s@%s' % (keep, domain)


def _ua(email):
    # n+146(3).4：具名，🚫 不偽裝。🚨 信箱缺失不會走到這裡（fetch 已 fail-closed）。
    return 'AHIG/0.2.1 (+mailto:%s)' % email


def fetch(url, *, email, range_bytes=None, cap=400_000, timeout=30, send=None):
    """回傳 dict：status／body／error／skipped／finalUrl／hops。

    🚫 不拋例外給呼叫端。`send` 只為自測而存在——⚠️ 正式呼叫不要傳。
    """
    global _hops
    send = send or _send
    # n+150（三）：🚨 信箱缺失即不送出（fail-closed）。
    if not email:
        return {'status': 'SKIPPED', 'body': b'', 'skipped': True,
                'finalUrl': None, 'hops': 0,
                'error': '聯絡信箱未設定，依 n+150 三不送出'}
    if url in _tried:
        return {'status': 'SKIPPED', 'body': b'', 'skipped': True,
                'finalUrl': None, 'hops': 0,
                'error': '本次執行已請求過此 URL（n+146(3).2 禁止再試）'}
    _tried.add(url)

    headers = {'User-Agent': _ua(email), 'Accept': '*/*'}
    if range_bytes:
        headers['Range'] = 'bytes=0-%d' % (range_bytes - 1)
    read_cap = range_bytes or cap

    current, hops = url, 0
    while True:
        host = urlparse(current).netloc
        # 🚨 每一跳都查——⚠️ 這就是「已封鎖之主機不得經由轉址器再被碰到」。
        if host in _blocked:
            return {'status': 'SKIPPED', 'body': b'', 'skipped': True,
                    'finalUrl': current, 'hops': hops,
                    'error': '該主機已明示拒絕自動化存取：%s（%s）'
                             % (_blocked[host], host)}
        wait = MIN_INTERVAL - (time.monotonic() - _last.get(host, -1e9))
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.monotonic()
        _count[host] = _count.get(host, 0) + 1

        res = send(current, headers, timeout, read_cap)
        status = res.get('status')
        final_url = res.get('url') or current
        final_host = urlparse(final_url).netloc or host

        if status in REDIRECTS:
            loc = (res.get('headers') or {}).get('Location') \
                or (res.get('headers') or {}).get('location')
            if not loc:
                return {'status': status, 'body': b'', 'skipped': False,
                        'finalUrl': final_url, 'hops': hops,
                        'error': 'HTTP %s 但無 Location' % status}
            hops += 1
            _hops += 1
            if hops > MAX_HOPS:
                return {'status': status, 'body': b'', 'skipped': False,
                        'finalUrl': final_url, 'hops': hops,
                        'error': '轉址逾 %d 跳，🚫 不再跟隨' % MAX_HOPS}
            current = urljoin(current, loc)
            continue

        _final[final_host] = _final.get(final_host, 0) + 1
        # n+146(3).3：🚨 封鎖鍵是最終回應之主機，🚫 不是轉址器（n+150 二）。
        if status in REFUSALS or (res.get('headers') or {}).get('Retry-After'):
            _blocked[final_host] = 'HTTP %s' % status
        return {'status': status, 'body': res.get('body') or b'',
                'skipped': False, 'finalUrl': final_url, 'hops': hops,
                'error': res.get('error') or ''}


def counters():
    """n+146（三）1 之計數；⚠️ 依 n+150（四）1 併記請求主機與最終主機兩者。"""
    return {'totalRequests': sum(_count.values()),
            'perRequestedHost': dict(sorted(_count.items())),
            'perFinalHost': dict(sorted(_final.items())),
            'redirectHops': _hops,
            'blockedHosts': dict(_blocked),
            'distinctUrls': len(_tried),
            'minIntervalSeconds': MIN_INTERVAL,
            'note': 'Per-execution counters. totalRequests counts every hop '
                    'actually sent, including redirect hops, because each hop is '
                    'a real outbound request. Requested and final hosts are kept '
                    'apart: a redirector such as doi.org appears in the first and '
                    'the publisher it lands on in the second, and blocking keys '
                    'on the second. State does not survive the process, so the '
                    'no-retry guarantee holds within one run only.'}


def _selftest():
    """🚨 控制探針：正反兩向，🚫 不發任何真實請求。"""
    global _last, _count, _final, _tried, _blocked, _hops
    ok = True

    def reset():
        global _last, _count, _final, _tried, _blocked, _hops
        _last, _count, _final, _tried, _blocked, _hops = {}, {}, {}, set(), {}, 0

    def say(name, cond, detail=''):
        nonlocal ok
        ok = ok and cond
        print('   %s %-46s %s' % ('✅' if cond else '🚨', name, detail))

    # 甲：信箱缺失即不送出（n+150 三）
    reset()
    sent = []
    fake_ok = lambda u, h, t, c: (sent.append(u), {  # noqa: E731
        'status': 200, 'headers': {}, 'body': b'ok', 'url': u, 'error': ''})[1]
    r = fetch('https://example.org/a', email='', send=fake_ok)
    say('甲：信箱為空 → SKIPPED 且未送出',
        r['skipped'] and not sent, r['error'])

    # 乙：正向對照——有信箱就會送出（🚨 否則甲之綠燈毫無意義）
    reset()
    sent = []
    r = fetch('https://example.org/a', email='a@b.c', send=fake_ok)
    say('乙：有信箱 → 送出且回 200', r['status'] == 200 and sent == ['https://example.org/a'])

    # 丙：同一 URL 同輪不得再試
    r2 = fetch('https://example.org/a', email='a@b.c', send=fake_ok)
    say('丙：同輪重複 URL → SKIPPED', r2['skipped'], r2['error'][:40])

    # 丁：轉址後 403 → 封鎖的是**出版社**，🚫 不是轉址器（n+150 二）
    reset()
    hops = []

    def fake_redirect(u, h, t, c):
        hops.append(u)
        if 'doi.org' in u:
            return {'status': 302, 'headers': {'Location': 'https://pub.example/x'},
                    'body': b'', 'url': u, 'error': ''}
        return {'status': 403, 'headers': {}, 'body': b'', 'url': u,
                'error': 'HTTP 403'}

    r = fetch('https://doi.org/10.1/x', email='a@b.c', send=fake_redirect)
    say('丁：轉址→403，封鎖鍵為最終主機',
        _blocked == {'pub.example': 'HTTP 403'}, str(_blocked))
    say('丁之二：轉址器🚫 未被封鎖', 'doi.org' not in _blocked)
    say('丁之三：兩跳都算進總數', counters()['totalRequests'] == 2,
        str(counters()['perRequestedHost']))

    # 戊：已封鎖之出版社🚫 不得再經由轉址器被碰到（⚠️ 這就是那個洞）
    hops.clear()
    r = fetch('https://doi.org/10.1/y', email='a@b.c', send=fake_redirect)
    say('戊：經轉址器再訪已封鎖主機 → 停在第二跳',
        r['skipped'] and hops == ['https://doi.org/10.1/y'], str(hops))

    # 己：反向對照——未封鎖之主機仍走得到（🚨 否則戊之綠燈可能來自「什麼都擋」）
    reset()
    r = fetch('https://other.example/z', email='a@b.c', send=fake_ok)
    say('己：未封鎖主機仍正常送出', r['status'] == 200 and not _blocked)

    # 庚：轉址無限迴圈 → 於 MAX_HOPS 停住
    reset()
    loop = lambda u, h, t, c: {'status': 302,  # noqa: E731
                            'headers': {'Location': 'https://loop.example/n'},
                            'body': b'', 'url': u, 'error': ''}
    r = fetch('https://loop.example/0', email='a@b.c', send=loop)
    say('庚：轉址迴圈於 %d 跳停住' % MAX_HOPS,
        r['hops'] == MAX_HOPS + 1 and '不再跟隨' in r['error'], r['error'][:40])

    reset()
    print('   %s 自測%s——🚫 全程未發任何真實請求。'
          % ('✅' if ok else '🚨', '全綠' if ok else '未過'))
    return ok


if __name__ == '__main__':
    import sys
    print('=== fetch_guard 自測（n+146 三／n+150 四）===')
    good = _selftest()
    print()
    print(json.dumps(counters(), ensure_ascii=False, indent=1))
    sys.exit(0 if good else 1)
