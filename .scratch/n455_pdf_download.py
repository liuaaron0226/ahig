# -*- coding: utf-8 -*-
"""把本環境取得到的 12 個 PDF 真正下載到私有根——與工具選型無關之部分。

## 授權依據

擁有者第 454 輪指示：**「同意安裝解析器，把那 12 個 PDF 轉成文字」**。
**⚠️ 本檔只做前半段之前置：把 PDF 位元組取下來。**
**🚫 不安裝任何東西、不解析、不決定用哪個工具**
——⚠️ 因為解析工具之選型受兩個硬限制影響（見第 455 輪回報），**須先讓擁有者知情。**

**✅ 下載本身早已獲授權**（n+117／n+119：「PDF 路之取得層，不涉安裝」），
且**任何工具選型都需要這些位元組**，故先做不會白做。

## 落點與隔離

- 存入 **`$AHIG_PRIVATE_ROOT/fulltext/pdf-cache/`**，
  **🚨 私有根，永不進版控**（文獻內容）。
- **檔名只用 candidateId 之末段雜湊**，**🚫 不用標題、不記完整網址**
  （第 452 輪：落地頁路徑內嵌逐字標題，而 n+48 五道抓不到該型）。
- **⚠️ 不寫入 `fulltext/<既有目錄>`**——🚨 那是取得管線自有之佈局，
  本檔為前置快取，混入會讓管線之 manifest 與實際檔案不一致。

## 校驗

每檔存後即驗：`%PDF-` 開頭、大小、`file_hash`。
**⚠️ 未通過者不留檔**，🚨 並如實記為失敗，**🚫 不以「已下載」計數。**
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.search.fulltext import _artifact_dir  # noqa: E402
from ahig.contracts.freeze import content_hash, file_hash  # noqa: E402

S = '.scratch/'
GAP = 1.5
EMAIL = os.environ.get('AHIG_CONTACT_EMAIL', '')
if not EMAIL:
    sys.exit('🚨 AHIG_CONTACT_EMAIL 未設定——🚫 中止（第 454 輪之教訓：先確認再跑）。')
UA = 'Mozilla/5.0 (compatible; AHIG/0.2.1 fulltext-acquisition; +mailto:%s)' % EMAIL
DEST = os.path.join(os.environ['AHIG_PRIVATE_ROOT'], 'fulltext', 'pdf-cache')
os.makedirs(DEST, exist_ok=True)


def fetch(url, cap=60_000_000):
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': UA,
                                                     'Accept': '*/*'}),
                timeout=120) as r:
            return r.status, r.read(cap), ''
    except urllib.error.HTTPError as e:
        return e.code, b'', 'HTTP %s' % e.code
    except Exception as e:
        return 'ERR', b'', '%s: %s' % (type(e).__name__, str(e)[:110])


def landing(cid):
    m = json.load(io.open(_artifact_dir(cid) / 'manifest.json', encoding='utf-8'))
    return m.get('availableUrl')


# ── 目標一：第 453 輪判為 pdf-ok 之 10 筆 ─────────────────────────
probe = json.load(io.open(S + 'n453_pdf_reachability.json', encoding='utf-8'))
direct = [(r['candidateId'], landing(r['candidateId']), r['host'])
          for r in probe['records'] if r['verdict'] == 'pdf-ok']

# ── 目標二：figshare 之 2 筆（經 API 取檔案下載網址）──────────────
FIG = [20870530, 12046290, 32548500, 20891005]
fig = []
for i, aid in enumerate(FIG):
    if i:
        time.sleep(GAP)
    code, body, err = fetch('https://api.figshare.com/v2/articles/%d' % aid,
                            cap=400_000)
    if code != 200:
        continue
    for f in (json.loads(body.decode('utf-8')).get('files') or []):
        if (f.get('name') or '').lower().endswith('.pdf') and f.get('download_url'):
            fig.append(('figshare:%d' % aid, f['download_url'], 'figshare.com'))

targets = direct + fig
print('=== 下載 %d 個 PDF（直接 %d ＋ figshare %d）==='
      % (len(targets), len(direct), len(fig)))
print('   落點 %s' % DEST)
print('   🚨 私有根，永不進版控；檔名只用 id 末段，不用標題。')
print()
print('%-22s %-30s %8s %10s %s' % ('id', 'host', 'HTTP', '大小KB', '判定'))
print('-' * 86)
rows, ok = [], 0
for i, (cid, url, host) in enumerate(targets):
    if i:
        time.sleep(GAP)
    code, body, err = fetch(url)
    is_pdf = body[:5] == b'%PDF-'
    tail = cid.split(':')[-1][:16]
    saved = ''
    if is_pdf and len(body) > 1024:
        p = os.path.join(DEST, '%s.pdf' % tail)
        with open(p, 'wb') as fh:
            fh.write(body)
        saved = file_hash(body)
        ok += 1
    rows.append({'candidateId': cid, 'host': host, 'http': code,
                 'bytes': len(body), 'isPdf': is_pdf,
                 'saved': bool(saved), 'fileHash': saved, 'error': err})
    print('%-22s %-30s %8s %10d %s'
          % (tail, host[:30], code, len(body) // 1024,
             '✅ 已存' if saved else ('🚨 非 PDF' if code == 200 else '🚨 %s' % (err or code))))

print('-' * 86)
print('   ✅ 實際存檔：%d／%d' % (ok, len(targets)))
tot = sum(r['bytes'] for r in rows if r['saved'])
print('   合計 %.1f MB' % (tot / 1048576.0))

doc = {
    'schemaVersion': 1,
    'documentType': 'pdf-download-cache',
    'ruling': 'owner instruction round 454; fetch layer already authorised by '
              'n+117(1). Downloads only -- no installation, no parsing, no tool '
              'choice.',
    'population': 'the 10 direct pdf-ok records of round 453 plus figshare PDFs',
    'countingUnit': 'file',
    'criterion': 'saved only if the body begins with %PDF- and exceeds 1KB',
    'destination': 'AHIG_PRIVATE_ROOT/fulltext/pdf-cache (private root, never '
                   'version controlled)',
    'namingNote': 'files are named by an id fragment, never by title, and no '
                  'URL is recorded -- landing paths embed verbatim titles',
    'saved': ok,
    'attempted': len(targets),
    'totalBytes': tot,
    'records': rows,
    'coverageStatement': 'These are bytes on disk. Whether each is complete '
                         'full text, and whether a parser can section it, is '
                         'not established here.',
    'contentNote': 'Hosts, sizes and hashes only. No document content and no '
                   'URLs are stored in this artefact.',
}
doc['downloadHash'] = content_hash({'saved': ok, 'attempted': len(targets)})
io.open(S + 'n455_pdf_download.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤（僅雜湊與計數）→ %sn455_pdf_download.json' % S)
