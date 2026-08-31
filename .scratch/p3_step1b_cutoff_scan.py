# -*- coding: utf-8 -*-
"""**P3 第一步（續）：取齊候選，並從摘要撈「搜尋截止日」。**（n+195）

## ✅ 本輪做兩件事

1. **取齊**：⚠️ 乙組 228 筆只取回 100，本支用 `cursorMark` 分頁補齊。
2. **第一遍截止日**：✅ 從**摘要**找「搜尋到哪一天」的陳述。

## 🚨 而這一遍**不是**盤點的答案

⚠️ 摘要**經常不寫**搜尋截止日——🚨 權威來源是方法段。
**✅ 故本支的產出是「哪幾份摘要裡就寫了」＋「其餘要去讀方法段」，
🚫 不是一份填好的截止日清單。**

> **🚨 而 n+195 三之 3 說得很清楚：沒有截止日的回顧記為「無法接續」，
> 🚫 不得用「大概是那幾年」補上去。**
> ⚠️ 故本支只抄**論文自己寫出來的日期**，🚫 一個字都不推測。

## ⚠️ 分頁要小

第 599 輪學到：`resultType=core` 一次 100 筆會超過 `fetch_guard` 的 40 萬字元上限，
**🚨 JSON 會在字串中間斷掉。** ✅ 故本支 core 一次只要 25 筆。
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

OUT = Path(__file__).resolve().parent / 'p3_step1b_cutoff_scan.json'
PRIOR = Path(__file__).resolve().parent / 'p3_step1_survey.json'
DETAIL = ROOT / 'p3-stress-eating' / 'step1b-cutoff.json'
BASE = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
CORE_PAGE = 25      # 🚨 core 記錄大，⚠️ 一次 100 筆會被上限截斷
LITE_PAGE = 100

# ✅ 只抓論文**自己寫出來**的檢索截止陳述。🚫 不從出版年推測。
CUTOFF = re.compile(
    r'(?:search(?:ed|es)?|searching|database[s]?\s+were\s+searched|literature '
    r'search)[^.]{0,120}?'
    r'(?:up\s+to|until|through|inception\s+to|to)\s+'
    r'((?:January|February|March|April|May|June|July|August|September|October'
    r'|November|December)\s+\d{4}|\d{1,2}\s+\w+\s+\d{4}|\d{4})',
    re.I)


def page(query, email, cursor='*', size=LITE_PAGE, kind='lite'):
    params = {'query': query, 'format': 'json', 'pageSize': str(size),
              'resultType': kind, 'cursorMark': cursor}
    url = '%s?%s' % (BASE, urllib.parse.urlencode(params))
    got = fetch(url, email=email)
    if got.get('skipped') or got.get('error') or got.get('status') != 200:
        return None, got
    try:
        return json.loads(got['body']), got
    except ValueError as exc:
        return None, {'error': 'json: %s' % exc, 'bodyChars': len(got.get('body') or '')}


def main():
    email, source = contact_email()
    if not email:
        print('🚨 無聯絡信箱——🚫 依 n+150（三）不送任何請求。', file=sys.stderr)
        return 2

    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    queries = prior['queries']

    # ── 一、取齊 ────────────────────────────────────────────────
    ids, failures = {}, {}
    for name, query in queries.items():
        cursor, seen, guard = '*', {}, 0
        while guard < 6:                     # ⚠️ 上限六頁，🚫 不無限翻
            guard += 1
            payload, raw = page(query, email, cursor)
            if payload is None:
                failures[name] = raw
                break
            for record in payload.get('resultList', {}).get('result', []):
                seen[record['id']] = record
            nxt = payload.get('nextCursorMark')
            if not nxt or nxt == cursor or len(seen) >= int(payload.get('hitCount', 0)):
                break
            cursor = nxt
        ids[name] = seen

    union = {}
    for name, records in ids.items():
        for key, record in records.items():
            union.setdefault(key, record)

    # ── 二、摘要裡的截止日 ──────────────────────────────────────
    stated, scanned, abstracts = {}, 0, {}
    order = sorted(union, key=lambda k: union[k].get('pubYear') or '0',
                   reverse=True)
    for start in range(0, len(order), CORE_PAGE):
        batch = order[start:start + CORE_PAGE]
        query = ' OR '.join('EXT_ID:%s' % union[k].get('pmid')
                            for k in batch if union[k].get('pmid'))
        if not query:
            continue
        payload, raw = page(query, email, '*', CORE_PAGE, 'core')
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

    years = Counter(v.get('pubYear') for v in union.values())
    # ✅ protocol 四之 2 要的那一句：**最新的檢索截止日是哪一天。**
    # 🚨 但這 318 份**尚未篩選**，⚠️ 故本數字是暫定的：
    # 那份「最新」的回顧未必切題，🚫 不得當成結論。
    dated = sorted(((re.search(r'(\d{4})', v).group(1), v, k)
                    for k, v in stated.items() if re.search(r'\d{4}', v)),
                   reverse=True)
    cutoff_years = Counter(y for y, _v, _k in dated)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('候選已取齊（必觸發）',
          all(len(ids[n]) >= min(int(prior['sets'][n]['hitCount']), 500)
              for n in ids),
          '🚨 沒取齊的盤點與取齊的長得一樣；實得 %s，命中 %s'
          % ({n: len(v) for n, v in ids.items()},
             {n: prior['sets'][n]['hitCount'] for n in ids}))
    probe('摘要真的拿到了（必觸發）', scanned > 0,
          '🚨 若為零，「摘要裡沒寫截止日」只是沒讀到；實得 %d 份摘要' % scanned)
    # 🚨 必觸發之反向：⚠️ 樣式要真的在某些摘要裡打得中，否則零命中無意義。
    probe('截止日樣式確實打得中（必觸發之反向）', bool(stated),
          '✅ 實得 %d 份摘要自己寫了檢索截止；🚨 若為零，'
          '代表樣式壞了，而「摘要多半不寫」會是假的' % len(stated))
    # 🚨 這一道會紅：⚠️ 摘要不是權威來源。
    probe('每一份候選都有搜尋截止日',
          len(stated) == len(union),
          '🚨 實得 %d／%d 份；⚠️ 其餘要逐份讀**方法段**——'
          '🚫 摘要多半不寫，而 n+195 三之 3 禁止用出版年推測'
          % (len(stated), len(union)))

    DETAIL.parent.mkdir(parents=True, exist_ok=True)
    DETAIL.write_text(json.dumps(
        {'documentType': 'p3-step1b-private',
         'candidates': {k: {'title': v.get('title'),
                            'pubYear': v.get('pubYear'),
                            'journal': v.get('journalTitle'),
                            'statedCutoff': stated.get(k)}
                        for k, v in union.items()},
         'abstracts': abstracts},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    doc = {
        'schemaVersion': 1,
        'documentType': 'p3-step1b-cutoff-scan',
        'assignment': 'n+195：P3 第一步（續）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contactEmail': masked(email),
        'requests': counters(),
        'retrieved': {n: len(v) for n, v in ids.items()},
        'hitCounts': {n: prior['sets'][n]['hitCount'] for n in ids},
        'unionCandidates': len(union),
        'abstractsScanned': scanned,
        'statedCutoffFound': len(stated),
        'statedCutoffByRecord': stated,
        'pubYearDistribution': dict(sorted(years.items(), reverse=True)),
        'statedCutoffYearDistribution': dict(sorted(cutoff_years.items(),
                                                    reverse=True)),
        'latestStatedCutoff': ({'value': dated[0][1], 'record': dated[0][2]}
                               if dated else None),
        'latestIsProvisional': (
            '🚨 這 318 份**尚未篩選**：⚠️ 那份「最新」的回顧未必切題、未必高品質。'
            '✅ 故「最新截止日」是暫定值，🚫 不得當成 protocol 四之 2 的答案。'),
        'failures': {k: {kk: vv for kk, vv in (v or {}).items()
                         if kk in ('status', 'error', 'skipped', 'bodyChars')}
                     for k, v in failures.items()},
        'whatThisIsNot': (
            '🚨 這不是填好的截止日清單。⚠️ 摘要經常不寫檢索截止，'
            '權威來源是方法段。'
            '✅ 本支只抄論文自己寫出來的日期，🚫 一個字都不推測'
            '——n+195 三之 3 禁止用「大概是那幾年」補。'),
        'titlesKeptPrivate': str(DETAIL),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== P3 第一步（續）：取齊＋摘要截止日 ===')
    print('   取回：%s（命中 %s）'
          % ({n: len(v) for n, v in ids.items()},
             {n: prior['sets'][n]['hitCount'] for n in ids}))
    print('   聯集候選 %d 份｜讀到摘要 %d 份｜✅ 摘要自述截止日 %d 份'
          % (len(union), scanned, len(stated)))
    print('   出版年分布（前 8）：%s'
          % dict(list(sorted(years.items(), reverse=True))[:8]))
    print('   截止日年份分布：%s' % dict(sorted(cutoff_years.items(), reverse=True)))
    print('   ✅ 最新自述截止日：%s（暫定，🚨 尚未篩選）'
          % (dated[0][1] if dated else '無'))
    print('   請求數 %s' % counters().get('totalRequests'))
    if failures:
        print('   🚨 失敗 %d 處' % len(failures))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s（題名與摘要留私有根）' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
