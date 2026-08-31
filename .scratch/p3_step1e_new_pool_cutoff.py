# -*- coding: utf-8 -*-
"""**對修正後的池子做同一件事：摘要裡的檢索截止日。**（n+195，P3）

⚠️ 第 600 輪對**舊池子**做過這件事；🚨 而第 601 輪查明舊查詢問錯了構念。
✅ 第 602 輪換了池子（134 筆，其中 102 筆是舊搜尋看不到的）。
**故本支對新池子重做一次**，🚫 不沿用舊池子的數字。

## 🚨 一樣的兩條紀律

1. **🚫 只抄論文自己寫出來的日期**——⚠️ 不從出版年推測（n+195 三之 3）。
2. **⚠️ `core` 一次只要 25 筆**——🚨 100 筆會超過 `fetch_guard` 的上限而截斷。

## ✅ 而本支多做一件事：**與舊池子的截止日分布並排**

⚠️ 若新池子的截止日比舊池子更近，那是「換對池子」的另一個佐證；
🚨 若更遠，那要記下來——**不能只挑對自己有利的數字。**
"""
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_guard import contact_email, counters, fetch, masked  # noqa: E402
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'p3_step1e_new_pool_cutoff.json'
NEW_SET = Path(__file__).resolve().parent / 'p3_step1d_requery.json'
OLD_SCAN = Path(__file__).resolve().parent / 'p3_step1b_cutoff_scan.json'
PRIV_NEW = ROOT / 'p3-stress-eating' / 'step1d-requery.json'
DETAIL = ROOT / 'p3-stress-eating' / 'step1e-new-pool.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
CORE_PAGE = 25

CUTOFF = re.compile(
    r'(?:search(?:ed|es)?|searching|database[s]?\s+were\s+searched|literature '
    r'search)[^.]{0,120}?'
    r'(?:up\s+to|until|through|inception\s+to|to)\s+'
    r'((?:January|February|March|April|May|June|July|August|September|October'
    r'|November|December)\s+\d{4}|\d{1,2}\s+\w+\s+\d{4}|\d{4})',
    re.I)


def core_page(ids, email):
    query = ' OR '.join('EXT_ID:%s' % pmid for pmid in ids if pmid)
    if not query:
        return None, {'error': 'no pmid in batch'}
    params = {'query': query, 'format': 'json', 'pageSize': str(CORE_PAGE),
              'resultType': 'core', 'cursorMark': '*'}
    got = fetch('%s?%s' % (BASE, urllib.parse.urlencode(params)), email=email)
    if got.get('skipped') or got.get('error') or got.get('status') != 200:
        return None, got
    try:
        return json.loads(got['body']), got
    except ValueError as exc:
        return None, {'error': 'json: %s' % exc,
                      'bodyChars': len(got.get('body') or '')}


def main():
    email, _source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 不送請求。', file=sys.stderr)
        return 2

    new_ids = json.loads(NEW_SET.read_text(encoding='utf-8'))['newIds']
    priv = json.loads(PRIV_NEW.read_text(encoding='utf-8'))
    by_id = {item['id']: item for item in priv['items']}
    # ⚠️ Europe PMC 的 id 對 MED 來源即為 pmid。
    pmids = [i for i in new_ids if i.isdigit()]

    stated, abstracts, failures, scanned = {}, {}, {}, 0
    for start in range(0, len(pmids), CORE_PAGE):
        payload, raw = core_page(pmids[start:start + CORE_PAGE], email)
        if payload is None:
            failures['core:%d' % start] = raw
            continue
        for record in payload.get('resultList', {}).get('result', []):
            scanned += 1
            text = record.get('abstractText') or ''
            abstracts[record['id']] = text
            hit = CUTOFF.search(text)
            if hit:
                stated[record['id']] = hit.group(1)

    def years_of(mapping):
        return Counter(re.search(r'(\d{4})', v).group(1)
                       for v in mapping.values() if re.search(r'\d{4}', v))

    new_years = years_of(stated)
    old = json.loads(OLD_SCAN.read_text(encoding='utf-8'))
    old_years = years_of(old['statedCutoffByRecord'])

    def recent_share(counter):
        total = sum(counter.values())
        recent = sum(n for y, n in counter.items() if y >= '2024')
        return (recent, total, round(100 * recent / total) if total else 0)

    new_share, old_share = recent_share(new_years), recent_share(old_years)
    dated = sorted(((re.search(r'(\d{4})', v).group(1), v, k)
                    for k, v in stated.items() if re.search(r'\d{4}', v)),
                   reverse=True)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('新池子的摘要真的讀到了（必觸發）', scanned > 0,
          '🚨 若為零，「新池子裡沒有截止日」只是沒讀到；實得 %d／%d 份'
          % (scanned, len(pmids)))
    probe('截止日樣式在新池子上也打得中（必觸發之反向）', bool(stated),
          '✅ 實得 %d 份；🚨 若為零，代表樣式對這個池子失效，'
          '而「多半不寫」會是假的' % len(stated))
    # ⚠️ 並排比較：🚨 這一道不預設方向，只要求兩邊都算得出來。
    probe('新舊兩個池子的截止日分布都算得出來（必觸發）',
          sum(new_years.values()) > 0 and sum(old_years.values()) > 0,
          '⚠️ 新池 %d／%d 份為 2024 年以後（%d%%）；'
          '舊池 %d／%d 份（%d%%）'
          % (new_share + old_share))
    # 🚨 這一道會紅。
    probe('新池子已篩選並填好截止日', False,
          '🚨 本支只讀摘要。🚫 未篩選、未讀方法段——⚠️ 摘要不是權威來源')

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p3-step1e-private',
         'items': {k: {'title': (by_id.get(k) or {}).get('title'),
                       'pubYear': (by_id.get(k) or {}).get('pubYear'),
                       'statedCutoff': stated.get(k)} for k in new_ids},
         'abstracts': abstracts},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1e-new-pool-cutoff',
        'assignment': 'n+195：P3 第一步（修正後的池子）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contactEmail': masked(email),
        'requests': counters(),
        'poolSize': len(new_ids),
        'abstractsScanned': scanned,
        'statedCutoffFound': len(stated),
        'statedCutoffByRecord': stated,
        'newPoolCutoffYears': dict(sorted(new_years.items(), reverse=True)),
        'oldPoolCutoffYears': dict(sorted(old_years.items(), reverse=True)),
        'recentShare': {'newPool': '%d/%d (%d%%)' % new_share,
                        'oldPool': '%d/%d (%d%%)' % old_share,
                        'definition': '截止日為 2024 年以後者所佔比例'},
        'latestStatedCutoff': ({'value': dated[0][1], 'record': dated[0][2]}
                               if dated else None),
        'latestIsProvisional': (
            '🚨 未篩選。⚠️ 第 601 輪的教訓：上一個「最新截止日」是一份計畫書。'
            '🚫 篩過之前不得當成答案。'),
        'failures': {k: {kk: vv for kk, vv in (v or {}).items()
                         if kk in ('status', 'error', 'skipped', 'bodyChars')}
                     for k, v in failures.items()},
        'titlesKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3：修正後池子的摘要截止日 ===')
    print('   池子 %d 份｜讀到摘要 %d 份｜✅ 自述截止日 %d 份'
          % (len(new_ids), scanned, len(stated)))
    print('   新池截止年：%s' % dict(sorted(new_years.items(), reverse=True)))
    print('   ⚠️ 2024 年以後占比：新池 %d/%d (%d%%)｜舊池 %d/%d (%d%%)'
          % (new_share + old_share))
    print('   最新（暫定）：%s' % (dated[0][1] if dated else '無'))
    print('   請求數 %s' % counters().get('totalRequests'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（題名與摘要留私有根）' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
