# -*- coding: utf-8 -*-
"""M1 第 ③ 步：對校準集 60 篇重跑全文取得（信箱已設定後）。

🚨 沿用既有之 `.scratch/w4a1_run.py` 做法，**不另造一套**（n+44）：
同一個 `acquire_from_run_root`、同一個 1.2 秒節流之 `PacedTransport`
——**⚠️ 對公共 OA API 節流是正確的預設，被限流或封鎖是難以回復的傷害（n+48 一）。**
差別只有兩處：**候選清單改為校準集**，以及**信箱從登錄檔讀**（見下）。

## ⚠️ 為什麼要自己讀登錄檔

`AHIG_CONTACT_EMAIL` 已以 PowerShell 設為使用者層級，**但使用者層級環境變數
只對「設定之後啟動的程序」生效**——本 session 之 shell 早於該設定啟動，
故 `os.environ` 讀不到。
**🚨 若不處理，這一趟會在「以為信箱已設」的情況下再次全部被 `missing-contact-email` 擋掉**
——**⚠️ 而那正是本次要修的問題本身，重演一次卻更難察覺（因為我們相信它已設好）。**

**故本檔自 `HKCU\\Environment` 讀取，並在啟動時印出遮蔽後之值供核對。**
⚠️ 印出時遮蔽本地部分，**只驗「有沒有、對不對得上」，不把完整地址寫進終端機紀錄**。

## 用法

    python .scratch/m1_step3_acquire.py [limit]

**⚠️ 未帶 limit 即跑全部 60 筆。首次執行務必帶小的 limit 驗證**
（n+96 二：跑了才發現地址錯，等於白跑一輪且已把錯地址送給外部服務）。
可重入：內容定址 manifest ＋ candidate lock，中斷後重跑安全。
"""
import json
import os
import sys
import time

os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')

from ahig.search.fulltext import (  # noqa: E402
    UrllibBinaryTransport, acquire_from_run_root)

RUN = (os.environ['AHIG_PRIVATE_ROOT'] +
       '/search-runs/b11-exogenous-cho-endurance/b11-full-run')
MIN_INTERVAL = 1.2          # 秒；與 w4a1_run.py 相同，不放寬


def contact_email():
    """取聯絡信箱：先環境變數，再 HKCU\\Environment。"""
    v = os.environ.get('AHIG_CONTACT_EMAIL')
    if v:
        return v, 'os.environ'
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
            v, _ = winreg.QueryValueEx(k, 'AHIG_CONTACT_EMAIL')
            return v, 'HKCU\\Environment'
    except (ImportError, OSError):
        return None, None


def masked(addr):
    """遮蔽本地部分，只留首尾各一字元與網域。"""
    if not addr or '@' not in addr:
        return '<無>'
    local, _, domain = addr.partition('@')
    keep = local[0] + '*' * max(len(local) - 2, 1) + local[-1] if len(local) > 1 else '*'
    return '%s@%s' % (keep, domain)


class PacedTransport:
    """在每次請求前補足最小間隔；其餘行為完全委派給內建 transport。"""

    def __init__(self, inner, min_interval=MIN_INTERVAL):
        self.inner = inner
        self.min_interval = min_interval
        self._last = 0.0
        self.calls = 0

    def get_bytes(self, *, url, headers=None):
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        self.calls += 1
        return self.inner.get_bytes(url=url, headers=headers)


def main():
    cal = json.load(open('.scratch/m1_step2_calibration_set.json',
                         encoding='utf-8'))
    ids = sorted({x for d in cal['draws'].values() for x in d['candidateIds']})
    assert len(ids) == 60, '🚨 校準集不是 60 篇'

    # 🚨 只跑「尚無確定結論」者——可重入不等於該重跑。
    # ⚠️ `no-oa-fulltext` 是查過之後的確定答案，重查它既無新資訊，
    #    也是對公共 OA API 的無謂請求（n+48 一：被限流是難以回復的傷害）。
    SETTLED = {'acquired', 'no-oa-fulltext'}
    inv = json.load(open('.scratch/m1_step3_inventory.json', encoding='utf-8'))
    settled = {r['candidateId'] for r in inv['records']
               if r['status'] in SETTLED}
    todo = [i for i in ids if i not in settled]

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if limit:
        todo = todo[:limit]

    email, src = contact_email()
    print('校準集 %d 篇；已有確定結論 %d（acquired 或 no-oa-fulltext）；本次對象 %d 筆'
          % (len(ids), len(settled), len(todo)))
    print('聯絡信箱 %s（來源 %s）' % (masked(email), src or '—'))
    if not email:
        print('🚨 未取得聯絡信箱——Unpaywall 會再次被 missing-contact-email 擋下。')
        print('   ⚠️ 中止，不做一趟注定重演同一個失敗的請求。')
        return 1
    print('節流 %.1f 秒／請求；可重入' % MIN_INTERVAL, flush=True)
    print()

    transport = PacedTransport(UrllibBinaryTransport())
    started = time.monotonic()
    summary = acquire_from_run_root(
        __import__('pathlib').Path(RUN), todo,
        transport=transport, contact_email=email)
    elapsed = time.monotonic() - started

    # ⚠️ 不預設 summary 的鍵名——第一次執行時我猜了五個鍵，全印 0，
    #    而真實狀態是 `no-oa-fulltext`（不在我猜的清單裡）。
    # 🚨 猜格式再拿它下結論，正是 n+101 立的那條通則所禁者。
    for k in sorted(summary):
        v = summary[k]
        if not isinstance(v, (list, dict)):
            print('   %-30s %s' % (k, v))
    print('   %-28s %d 次 / %.1f 秒' % ('請求', transport.calls, elapsed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
