"""n+47：W4a-1 全文取得，以 308 筆有效 advance 為清單，背景執行。

要點（對應 n+47 建議之四項）：
1. 只寫 AHIG_PRIVATE_ROOT（由 fulltext._require_private 強制），repo 零文獻內容。
2. 可重入——內容定址 manifest ＋ candidate lock，中斷後重跑安全。
3. AHIG_CONTACT_EMAIL 不由本執行室代設；未設則 Unpaywall 自動略過。
4. 不做任何抽樣或方法學決定，只取 PDF。

額外：內建 UrllibBinaryTransport 只有失敗重試退避，「請求之間」沒有間隔。
308 筆 × 最多 3 個來源接近千次請求，對 Europe PMC／OpenAlex 不禮貌，
故以 transport 擴充點包一層節流，不修改 ahig/ 原始碼。
"""
import json, os, sys, time

os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')

from ahig.search.fulltext import UrllibBinaryTransport, acquire_from_run_root

RUN = os.environ['AHIG_PRIVATE_ROOT'] + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
MIN_INTERVAL = 1.2  # 秒；對公共 OA API 的請求間隔下限


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
    ids = json.load(open('.scratch/adv_ids.json', encoding='utf-8'))
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if limit:
        ids = ids[:limit]
    contact = os.environ.get('AHIG_CONTACT_EMAIL') or None
    print('candidates %d  unpaywall %s' % (
        len(ids), 'enabled' if contact else 'SKIPPED (AHIG_CONTACT_EMAIL unset)'),
        flush=True)

    transport = PacedTransport(UrllibBinaryTransport())
    started = time.monotonic()
    summary = acquire_from_run_root(
        __import__('pathlib').Path(RUN), ids,
        transport=transport, contact_email=contact)

    elapsed = time.monotonic() - started
    out = {k: summary[k] for k in (
        'candidateCount', 'acquiredCount', 'availablePdfCount',
        'unavailableCount', 'incompleteCount', 'batchManifest')}
    out['httpCalls'] = transport.calls
    out['elapsedSec'] = round(elapsed, 1)
    print(json.dumps(out, ensure_ascii=False), flush=True)

    # 逐筆狀態另存，供心跳統計；只寫 .scratch 的 ID 與狀態，不含文獻內容。
    by_status = {}
    for r in summary['results']:
        by_status.setdefault(r['status'], []).append(r['candidateId'])
    json.dump({k: sorted(v) for k, v in by_status.items()},
              open('.scratch/w4a1_status.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('status counts', {k: len(v) for k, v in sorted(by_status.items())},
          flush=True)


if __name__ == '__main__':
    main()
