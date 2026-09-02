# -*- coding: utf-8 -*-
"""**`D18` 那 18 篇是哪個年代的——會不會補上低劑量端。**（第 714 輪）

## ✅ 把劑量-反應那條線收尾

第 713 輪：**整個語料的 `low` 帶（10–29.9 g/h）只有 1 篇。**
第 626 輪：**缺掉的 2000 年前那批，劑量顯著較低**（中位數差 21 g/h，p＝0.0054）。
第 624 輪的 `D18`：**18 篇「判定可得卻未取」**，建議補取、且先做 2000 年前那批。

> **🚨 於是問題很具體：那 18 篇裡，有幾篇是 2000 年前的？**
> ⚠️ 若一篇都沒有，**🚫 補了也補不到低劑量端**——那 `D18` 的效益要換個說法。

## ✅ 本支只讀候選池的 `publicationYear`

🚫 不讀判詞、🚫 不推估劑量——⚠️ 年代與劑量的關係是**第 626 輪**證的，
**🚨 本支只提供年代這一半，🚫 不重做那個統計。**

## 🚫 本支不送請求、不改任何清冊與契約、不輸出題名
"""
import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n714_d18_era_profile.json'
N624 = HERE / 'n624_corpus_denominator.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'


def main():
    never_taken = json.loads(N624.read_text(encoding='utf-8'))[
        'obtainableNeverTaken']

    pool = {r['candidateId']: r for r in json.loads(
        (RUN / 'candidate-pool/candidates.json').read_text(encoding='utf-8'))}
    by_suffix = {cid[-16:]: rec for cid, rec in pool.items()}

    rows, unmatched = [], []
    for short in never_taken:
        rec = by_suffix.get(short)
        if rec is None:
            unmatched.append(short)
            continue
        raw = rec.get('publicationYear')
        rows.append({'candidate': short,
                     'year': int(raw) if raw else None})

    years = sorted(r['year'] for r in rows if r['year'])
    pre2000 = [r for r in rows if r['year'] and r['year'] < 2000]
    no_year = [r['candidate'] for r in rows if not r['year']]
    decades = collections.Counter(
        '%ds' % (r['year'] // 10 * 10) for r in rows if r['year'])

    # ✅ 對照：已取得那 41 篇的年代（第 625 輪報過 2005–2026、中位 2020）
    acquired_years = []
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue
        path = entry / 'manifest.json'
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc.get('status') != 'acquired':
            continue
        rec = pool.get(str(doc.get('candidateId')))
        raw = (rec or {}).get('publicationYear')
        if raw:
            acquired_years.append(int(raw))
    acquired_years.sort()

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('那 18 篇都對得到候選池（必觸發之正對照）',
          not unmatched and len(rows) == len(never_taken),
          '🚨 名單 %d 篇、對到 %d 篇、對不到的：%s；'
          '⚠️ 對不到的話年代分佈就是殘的'
          % (len(never_taken), len(rows), unmatched or '無'))
    probe('候選池真的有年份（必觸發之反向）',
          len(years) > 0 and len(acquired_years) > 0,
          '🚨 那 18 篇有年份的 %d 篇；已取得那批有年份的 %d 篇；'
          '⚠️ 任一為 0 就代表本支讀錯了欄位'
          % (len(years), len(acquired_years)))
    probe('捏造的代號對不到候選池（必觸發之反向）',
          'ffffffffffffffff' not in by_suffix,
          '🚨 捏造代號查無；⚠️ 若查得到，代表比對是在亂配')
    # 🚨 這一道是答案。
    probe('那 18 篇裡有 2000 年前的（補得到低劑量端）',
          bool(pre2000),
          '🚨 2000 年前的 %d 篇；年份範圍 %s；中位數 %s；'
          '⚠️ 若一篇都沒有，**補了也補不到低劑量端**'
          % (len(pre2000),
             [years[0], years[-1]] if years else '（無）',
             statistics.median(years) if years else '（無）'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd18-era-profile',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLoopWith': ('n713（`low` 帶只有 1 篇）＋'
                           'n626（缺掉的年代劑量顯著較低）'),
        'candidates': len(rows),
        'unmatched': unmatched,
        'yearRange': [years[0], years[-1]] if years else None,
        'medianYear': statistics.median(years) if years else None,
        'pre2000': [r['candidate'] for r in pre2000],
        'withoutYear': no_year,
        'byDecade': dict(sorted(decades.items())),
        'acquiredCorpusYearRange': ([acquired_years[0], acquired_years[-1]]
                                    if acquired_years else None),
        'acquiredCorpusMedianYear': (statistics.median(acquired_years)
                                     if acquired_years else None),
        'whyThisMatters': (
            '🚨 第 713 輪：`low` 帶（10–29.9 g/h）**只有 1 篇**。'
            '⚠️ 第 626 輪：缺掉的 2000 年前那批**劑量顯著較低**。'
            '**✅ 故「補取那 18 篇會不會補上低劑量端」，'
            '取決於它們是不是那個年代的。**'),
        'whatThisCannotAnswer': (
            '🚫 本支**不推估那 18 篇的劑量**——⚠️ 年代與劑量的關係是'
            '第 626 輪證的，🚨 而那是**群體層次的統計**，'
            '**⚠️ 🚫 不保證任何一篇個別落在低劑量帶。**'
            '✅ 又：本支只讀候選池的年份，🚫 不送任何請求。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n714 D18 那 18 篇的年代 ===')
    print('   對到候選池 %d／%d 篇｜沒有年份 %d 篇'
          % (len(rows), len(never_taken), len(no_year)))
    print('   年份範圍 %s｜中位數 %s'
          % (doc['yearRange'], doc['medianYear']))
    print('   逐十年：%s' % doc['byDecade'])
    print('   🚨 2000 年前：%d 篇 %s' % (len(pre2000), doc['pre2000']))
    print('   對照・已取得那批：範圍 %s｜中位數 %s'
          % (doc['acquiredCorpusYearRange'],
             doc['acquiredCorpusMedianYear']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
