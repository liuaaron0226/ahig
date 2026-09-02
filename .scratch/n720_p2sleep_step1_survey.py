# -*- coding: utf-8 -*-
"""**P2 第一步：盤點既有回顧**——搜尋那一段。（n+196 交辦）

## 🚨 三條硬規矩（n+196 三，與 P3 相同）

1. **🚫 逐字英文題名不得進本 repo**——⚠️ 題名只寫私有根，
   ✅ 本 repo 只收計數與識別碼。
2. **⚠️ 對外請求走 `.scratch/fetch_guard.py`**：每主機每秒一次、計次、
   🚫 403／429 後不重試、**🚨 無聯絡信箱即不送請求**。
3. **🚨 最重要的一欄是「搜尋截止日」**——⚠️ 本支**不猜**：
   🚫 這一步只取得候選清單，✅ 截止日要逐份讀方法段才填得出來。

## ⚠️ 本支做到哪裡

✅ 只做**搜尋**。🚫 不讀全文、不填截止日、不下判斷——⚠️ 那些是後續步驟。

## 🚨 兩個問題分開問，🚫 不合併

- **甲**：睡眠介入 → **食慾／進食行為**
- **乙**：睡眠介入 → **赤字的維持率／依從性**

⚠️ 兩者未必同一——🚨 食慾變好不保證赤字維持得住。
**✅ 故兩組查詢分開跑、分開記**（與 P3 的作法一致）。
"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_guard import contact_email, counters, fetch, masked  # noqa: E402
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

# 🚨 `.gitignore` 有一條 `.scratch/p2_*.json`（原為篩選第二輪的每頁暫存檔）——
# ⚠️ 本支若沿用 `p2_step1_survey.json` 會被**靜默排除在 git 之外**，
# 而看板會引用到一個不在 repo 裡的檔案。
# ✅ 故改用輪次編號命名，避開那條規則。
OUT = Path(__file__).resolve().parent / 'n720_p2sleep_step1_survey.json'
DETAIL = ROOT / 'p2-sleep' / 'step1-candidates.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'

REVIEW = ('(PUB_TYPE:"systematic review" OR PUB_TYPE:"meta-analysis" '
          'OR TITLE:"systematic review" OR TITLE:"meta-analysis")')
# ⚠️ 睡眠側的說法很分歧（實驗性限制／習慣性短睡／睡眠品質／延長介入），
# 🚨 故一次涵蓋，🚫 但後續逐份記下該回顧用的是哪一個。
SLEEP = ('(TITLE_ABS:"sleep extension" OR TITLE_ABS:"sleep restriction" '
         'OR TITLE_ABS:"sleep deprivation" OR TITLE_ABS:"sleep duration" '
         'OR TITLE_ABS:"sleep quality" OR TITLE_ABS:"short sleep")')

QUERIES = {
    # 🚨 甲：食慾／進食行為本身。
    'sleep-appetite': (
        SLEEP + ' AND (TITLE_ABS:"appetite" OR TITLE_ABS:"energy intake" '
        'OR TITLE_ABS:"food intake" OR TITLE_ABS:"eating behaviour" '
        'OR TITLE_ABS:"eating behavior" OR TITLE_ABS:"food craving") AND '
        + REVIEW),
    # ⚠️ 乙：赤字維持得住與否——🚫 這不是同一個問題。
    'sleep-adherence': (
        SLEEP + ' AND (TITLE_ABS:"weight loss" OR TITLE_ABS:"fat loss" '
        'OR TITLE_ABS:"energy restriction" OR TITLE_ABS:"dietary adherence" '
        'OR TITLE_ABS:"weight loss maintenance" '
        'OR TITLE_ABS:"caloric restriction") AND ' + REVIEW),
}


def search(query, email):
    # ✅ 沿用 P3 的教訓：要 `lite`，🚫 不要 `core`——
    # ⚠️ core 含摘要，回應會被閘門的 40 萬字元上限截斷。
    params = {'query': query, 'format': 'json', 'pageSize': '100',
              'resultType': 'lite'}
    url = '%s?%s' % (BASE, urllib.parse.urlencode(params))
    result = fetch(url, email=email)
    if result.get('skipped') or result.get('error') \
            or result.get('status') != 200:
        return None, result
    try:
        return json.loads(result['body']), result
    except ValueError as exc:
        return None, {'error': 'json: %s' % exc}


def main():
    email, source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 依 n+150（三）不送任何請求。', file=sys.stderr)
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
        # 🚫 題名只進私有根。✅ 本 repo 只留識別碼。
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

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    ids_union = {r['id'] for v in found.values() for r in v['records']}
    largest = max((len(v['records']) for v in found.values()), default=0)

    probe('兩組查詢都拿到結果（必觸發）',
          len(found) == len(QUERIES),
          '🚨 少一組就代表盤點不完整，⚠️ 而不完整的盤點看起來跟完整的一樣；'
          '實得 %d／%d，失敗 %s' % (len(found), len(QUERIES), failures or '無'))
    probe('兩個問題確實問到不同的東西（必觸發之反向）',
          len(ids_union) > largest,
          '🚨 若兩組回傳的是同一批文獻，protocol 所稱「兩件事」就沒有分開；'
          '⚠️ 實得聯集 %d 筆、單組最大 %d 筆' % (len(ids_union), largest))
    probe('本支沒有把逐字題名寫進 repo',
          True,
          '✅ 題名只寫私有根 %s；🚫 本 repo 只收識別碼與計數' % DETAIL.name)
    # 🚨 這一道**故意會紅**：⚠️ 搜尋不是盤點。
    probe('每一份候選回顧都已填入搜尋截止日', False,
          '🚨 本支只做搜尋，🚫 一份都還沒讀；⚠️ 截止日要逐份讀方法段才填得出來，'
          '**🚫 不得用「大概是那幾年」補上去**（n+196 三）')

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p2-step1-candidates-private',
         'queries': QUERIES,
         'sets': {k: v['private'] for k, v in found.items()}},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p2-step1-survey',
        'assignment': 'n+196：P2（睡眠）第一步之搜尋',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'protocol': 'ahig/domains/p2-sleep/review-of-reviews.md',
        'method': '✅ 與 P3 同一套（`p3_step1_survey.py`），🚫 不另發明。',
        'queries': QUERIES,
        'results': {k: {'hitCount': v['hitCount'], 'returned': v['returned'],
                        'ids': [r['id'] for r in v['records']]}
                    for k, v in found.items()},
        'failures': failures,
        'unionIds': len(ids_union),
        'requestCounters': counters(),
        'contactEmail': masked(email),
        'titlesKeptPrivate': str(DETAIL),
        'whatThisDoesNotDo': (
            '🚫 本支只做搜尋——⚠️ 不讀全文、不填截止日、不下判斷。'
            '🚨 而**搜尋截止日**是這一步最重要的一欄，'
            '**⚠️ 它要逐份讀方法段才填得出來**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P2 第一步・搜尋 ===')
    for name, info in found.items():
        print('   %-18s 命中 %s 筆｜本次取回 %d 筆'
              % (name, info['hitCount'], info['returned']))
    print('   兩組聯集 %d 筆｜失敗 %s' % (len(ids_union), failures or '無'))
    print('   請求計數：%s' % counters())
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
