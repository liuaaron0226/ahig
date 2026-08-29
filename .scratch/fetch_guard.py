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
| 1 | 同一主機不得高於每秒一次；**每輪總數須記入產物** | 逐主機記錄上次請求時刻並補足間隔；`counters()` 回傳總數與逐主機數 |
| 2 | 同一 URL 每輪🚫 重試不得超過一次；**403／429 一律不重試** | 記錄已試 URL；`4xx` 直接回傳不重試 |
| 3 | 主機明示拒絕自動化即**停止該主機全部後續請求**，並於回報列名 | `403`／`429`／`Retry-After` 出現即列入 `blocked`，其後同主機請求一律不送出 |
| 4 | 🚫 不得偽裝身分（具名 UA 可） | UA 由本檔組出，含 `AHIG` 與聯絡信箱，**呼叫端不得覆寫** |

## 🚨 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 擋得住：速率、同輪重試、對已拒絕主機之後續請求、UA 覆寫。
- 🚨 擋不住：**跨輪之累計行為**——⚠️ 本檔之狀態隨行程結束而消失，
  **🚫 故「同一 URL 不得重試超過一次」之保證僅限單次執行內。**
- ⚠️ 亦擋不住**呼叫端不使用本檔**——**🚨 本檔是工具不是沙箱。**
"""
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

MIN_INTERVAL = 1.0          # n+146(3).1：同一主機每秒至多一次
_last = {}                  # host -> 上次請求之單調時刻
_count = {}                 # host -> 本次執行之請求數
_tried = set()              # 本次執行已請求過之 URL
_blocked = {}               # host -> 拒絕之原因（其後不再請求）


def _ua(email):
    # n+146(3).4：具名，🚫 不偽裝
    return 'AHIG/0.2.1 (+mailto:%s)' % (email or 'unset')


def fetch(url, *, email, range_bytes=None, cap=400_000, timeout=30):
    """回傳 dict：status／body／error／skipped。🚫 不拋例外給呼叫端。"""
    host = urlparse(url).netloc
    if host in _blocked:
        return {'status': 'SKIPPED', 'body': b'', 'skipped': True,
                'error': '該主機已明示拒絕自動化存取：%s' % _blocked[host]}
    if url in _tried:
        return {'status': 'SKIPPED', 'body': b'', 'skipped': True,
                'error': '本次執行已請求過此 URL（n+146(3).2 禁止再試）'}
    _tried.add(url)
    wait = MIN_INTERVAL - (time.monotonic() - _last.get(host, -1e9))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()
    _count[host] = _count.get(host, 0) + 1
    headers = {'User-Agent': _ua(email), 'Accept': '*/*'}
    if range_bytes:
        headers['Range'] = 'bytes=0-%d' % (range_bytes - 1)
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=timeout) as r:
            return {'status': r.status, 'body': r.read(range_bytes or cap),
                    'skipped': False, 'error': ''}
    except urllib.error.HTTPError as e:
        # n+146(3).3：明示拒絕即封鎖該主機；🚫 不重試
        if e.code in (401, 403, 429) or e.headers.get('Retry-After'):
            _blocked[host] = 'HTTP %s' % e.code
        return {'status': e.code, 'body': b'', 'skipped': False,
                'error': 'HTTP %s' % e.code}
    except Exception as e:
        return {'status': 'ERR', 'body': b'', 'skipped': False,
                'error': '%s: %s' % (type(e).__name__, str(e)[:120])}


def counters():
    """n+146（三）1 要求之對外請求計數，供回報產物直接引用。"""
    return {'totalRequests': sum(_count.values()),
            'perHost': dict(sorted(_count.items())),
            'blockedHosts': dict(_blocked),
            'distinctUrls': len(_tried),
            'minIntervalSeconds': MIN_INTERVAL,
            'note': 'Per-execution counters. State does not survive the process, '
                    'so the no-retry guarantee holds within one run only.'}


if __name__ == '__main__':
    print(json.dumps(counters(), ensure_ascii=False, indent=1))
