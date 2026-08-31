# -*- coding: utf-8 -*-
"""**P3 第一步：盤點既有回顧**——搜尋那一段。（n+195 交辦）

## 🚨 三條硬規矩（n+195 三）

1. **🚫 逐字英文題名不得進本 repo**——⚠️ 題名與摘要一律只寫私有根，
   ✅ 本 repo 只收計數與識別碼。
2. **⚠️ 對外請求走 `.scratch/fetch_guard.py`**：每主機每秒一次、計次、
   🚫 403／429 後不重試、**🚨 無聯絡信箱即不送請求**。
3. **🚨 最重要的一欄是「搜尋截止日」**——⚠️ 本支**不猜**：
   🚫 這一步只取得候選清單，✅ 截止日要逐份讀方法段才填得出來。

## ⚠️ 本支做到哪裡

✅ 只做**搜尋**：問「有哪些系統性回顧／統合分析談這兩件事」。
🚫 不讀全文、不填截止日、不下判斷——⚠️ 那些是後續的步驟。

## 🚨 兩個問題分開問，🚫 不合併

protocol 一（刻意問兩件事）：
- **甲**：減少壓力／情緒驅動的進食
- **乙**：提高熱量赤字的維持率

⚠️ 兩者未必同一——🚨 減少壓力性進食不保證赤字維持得住。
**✅ 故兩組查詢分開跑、分開記。**
"""
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_guard import contact_email, counters, fetch, masked  # noqa: E402
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'p3_step1_survey.json'
DETAIL = ROOT / 'p3-stress-eating' / 'step1-candidates.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'

REVIEW = ('(PUB_TYPE:"systematic review" OR PUB_TYPE:"meta-analysis" '
          'OR TITLE:"systematic review" OR TITLE:"meta-analysis")')
QUERIES = {
    # 🚨 甲：壓力／情緒驅動的進食本身。
    'stress-eating': (
        '(TITLE_ABS:"emotional eating" OR TITLE_ABS:"stress eating" '
        'OR TITLE_ABS:"stress-induced eating" '
        'OR TITLE_ABS:"disinhibited eating") AND ' + REVIEW),
    # ⚠️ 乙：赤字維持得住與否——🚫 這不是同一個問題。
    'deficit-adherence': (
        '(TITLE_ABS:"dietary adherence" OR TITLE_ABS:"diet adherence" '
        'OR TITLE_ABS:"weight loss maintenance" '
        'OR TITLE_ABS:"adherence to energy restriction") AND ' + REVIEW),
}


def search(query, email):
    # 🚨 第一版用 resultType=core，⚠️ 回應被閘門的 40 萬字元上限截斷（JSON 截半）。
    # ✅ 改要 lite：⚠️ 它不含摘要，故小得多。
    # **🚫 修法是「少要一點」，不是「把上限調高」**——那道上限是保護，不是障礙。
    params = {'query': query, 'format': 'json', 'pageSize': '100',
              'resultType': 'lite'}
    url = '%s?%s' % (BASE, urllib.parse.urlencode(params))
    result = fetch(url, email=email)
    if result.get('skipped') or result.get('error') or result.get('status') != 200:
        return None, result
    try:
        return json.loads(result['body']), result
    except ValueError as exc:
        return None, {'error': 'json: %s' % exc}


def main():
    email, source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 依 n+150（三）不送任何請求。', file=sys.stderr)
        print('   ⚠️ 請設定 AHIG_CONTACT_EMAIL 後再跑。', file=sys.stderr)
        return 2
    print('   聯絡信箱 %s（來源 %s）' % (masked(email), source))

    found, failures = {}, {}
    for name, query in QUERIES.items():
        payload, raw = search(query, email)
        if payload is None:
            failures[name] = {k: v for k, v in (raw or {}).items()
                              if k in ('status', 'error', 'skipped')}
            continue
        result = payload.get('resultList', {}).get('result', [])
        # 🚫 題名與摘要只進私有根。✅ 本 repo 只留識別碼。
        found[name] = {
            'hitCount': payload.get('hitCount'),
            'returned': len(result),
            'records': [{'id': r.get('id'), 'source': r.get('source'),
                         'pmid': r.get('pmid'), 'doi': r.get('doi'),
                         'pubYear': r.get('pubYear'),
                         'isOpenAccess': r.get('isOpenAccess'),
                         'pubType': r.get('pubType')}
                        for r in result],
            'private': [{'id': r.get('id'), 'title': r.get('title'),
                         'journal': r.get('journalTitle'),
                         'pubYear': r.get('pubYear')}
                        for r in result],
        }
        time.sleep(0)   # ⚠️ 間隔由 fetch_guard 負責，🚫 此處不自行加碼。

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩組查詢都拿到結果（必觸發）',
          len(found) == len(QUERIES),
          '🚨 少一組就代表盤點不完整，⚠️ 而不完整的盤點看起來跟完整的一樣；'
          '實得 %d／%d，失敗 %s' % (len(found), len(QUERIES), failures or '無'))
    probe('兩個問題確實問到不同的東西（必觸發之反向）',
          len({r['id'] for v in found.values() for r in v['records']}) >
          max((len(v['records']) for v in found.values()), default=0),
          '🚨 若兩組回傳的是同一批文獻，protocol 所稱「兩件事」就沒有分開；'
          '⚠️ 實得聯集 %d 筆、單組最大 %d 筆'
          % (len({r['id'] for v in found.values() for r in v['records']}),
             max((len(v['records']) for v in found.values()), default=0)))
    probe('本支沒有把逐字題名寫進 repo',
          True,
          '✅ 題名與摘要只寫私有根 %s；🚫 本 repo 只收識別碼與計數'
          % DETAIL.name)
    # 🚨 這一道**故意會紅**：⚠️ 搜尋不是盤點。
    probe('每一份候選回顧都已填入搜尋截止日', False,
          '🚨 本支只做搜尋，🚫 一份都還沒讀；⚠️ 截止日要逐份讀方法段才填得出來，'
          '**🚫 不得用「大概是那幾年」補上去**（n+195 三之 3）')

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p3-step1-candidates-private',
         'queries': QUERIES,
         'sets': {k: {'hitCount': v['hitCount'], 'items': v['private']}
                  for k, v in found.items()}},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1-survey',
        'assignment': 'n+195：依 review-of-reviews.md 執行 P3 第一步',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contactEmail': masked(email),
        'requests': counters(),
        'queries': QUERIES,
        'sets': {k: {'hitCount': v['hitCount'], 'returned': v['returned'],
                     'records': v['records']} for k, v in found.items()},
        'failures': failures,
        'whatIsNotDoneYet': (
            '🚨 本支只做搜尋。🚫 尚未讀任何一份回顧，故**搜尋截止日一欄全部是空的**'
            '——⚠️ 而那是 protocol 說的最重要的一欄。'
            '🚫 不得用「大概是那幾年」補（n+195 三之 3）。'),
        'titlesKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3 第一步：搜尋 ===')
    for name, value in found.items():
        print('   %-18s 命中 %s 筆｜取回 %d 筆'
              % (name, value['hitCount'], value['returned']))
    if failures:
        print('   🚨 失敗：%s' % failures)
    print('   請求計數：%s' % counters())
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（題名與摘要留私有根：%s）' % (OUT.name, DETAIL.name))
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
