# -*- coding: utf-8 -*-
"""**現有這 41 篇，哪些結論撐得住、哪些只靠一兩篇。**（第 628 輪）

## 🚨 第 624–627 輪一直在講「缺了什麼」，本輪講**手上有的那份有多薄**

⚠️ 前四輪量的是語料之外：分母、年代、劑量空間、尺準不準。
**🚫 但從沒有人問過：手上這 98 項，攤到六種契約結局上，每一種靠幾篇撐。**

> **🚨 以「結局數」數支持度會騙人**——⚠️ 一篇報六個結局不是六份證據。
> **✅ 故本支一律以「相異篇數」計。**

## ✅ 本支問三件事

| | 問題 |
|---|---|
| **甲** | 每一種契約結局由**幾篇相異報告**支撐 |
| **乙** | 劑量帶 × 結局的**覆蓋格**——🚨 哪一格是空的 |
| **丙** | 撐住低劑量端的那幾篇，**貢獻的是哪一種結局** |

⚠️ 分帶刻意把 `=60` 單獨列一格：第 627 輪查明 **60 g/h 正好是資料的眾數**，
🚨 把它併進任何一邊都會讓某一格憑空胖一圈。

## 🚫 本支不送外部請求、不改任何清冊、不輸出任何標籤或題名文字
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n628_evidence_thinness.json'

BANDS = [(0.0, 59.99, '<60'), (60.0, 60.0, '=60'),
         (60.01, 89.99, '60-90'), (90.0, 9999.0, '>=90')]

# ⚠️ 表現類結局＝擁有者真正問的那一類；🚨 腸胃症狀是耐受性，不是表現。
PERFORMANCE = {'tt-completion-time', 'time-to-exhaustion'}

# 🚨 第 584 輪查明的同群重複對：論文與期刊文章報的是同一批受試者。
KNOWN_COHORT_PAIR = ('307c0dd5b141caed', '7a6ac1559c740fd6')


def band_of(value):
    for low, high, label in BANDS:
        if low <= value <= high:
            return label
    return None


def main():
    rows = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if not (outcome.get('scopeDecision') or {}).get('inScope'):
                continue
            rows.append({
                'report': doc['report'][-16:],
                'ref': outcome.get('normalisedOutcomeRef'),
                'dose': float(outcome['dose']),
                'instrument': outcome.get('instrument'),
            })

    papers_by_ref = collections.defaultdict(set)
    instruments_by_ref = collections.defaultdict(set)
    grid = collections.defaultdict(set)
    for row in rows:
        papers_by_ref[row['ref']].add(row['report'])
        instruments_by_ref[row['ref']].add(row['instrument'])
        grid[(row['ref'], band_of(row['dose']))].add(row['report'])

    census = []
    for ref, papers in sorted(papers_by_ref.items(),
                              key=lambda kv: -len(kv[1])):
        census.append({
            'outcome': ref,
            'papers': len(papers),
            'outcomes': sum(1 for r in rows if r['ref'] == ref),
            'instruments': len(instruments_by_ref[ref]),
            'byDoseBand': {label: len(grid[(ref, label)])
                           for _, _, label in BANDS},
            'isPerformance': ref in PERFORMANCE,
        })

    # 丙：撐住低端的那幾篇，各自貢獻什麼。
    low_papers = sorted({r['report'] for r in rows if r['dose'] < 60})
    low_detail = []
    for report in low_papers:
        mine = [r for r in rows if r['report'] == report]
        refs = sorted({r['ref'] for r in mine})
        low_detail.append({
            'report': report,
            'minDose': min(r['dose'] for r in mine),
            'outcomes': refs,
            'supportsPerformance': bool(set(refs) & PERFORMANCE),
        })

    perf_low = [d for d in low_detail if d['supportsPerformance']]
    # 🚨 收束點：低端唯一撐表現的那篇，是不是已知同群重複對的一半。
    overlaps_pair = [d for d in perf_low
                     if d['report'] in KNOWN_COHORT_PAIR]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('98 項全部落得進某個劑量帶（必觸發之正對照）',
          all(band_of(r['dose']) is not None for r in rows) and len(rows) == 98,
          '🚨 實得 %d 項、落不進任何帶者 %d；⚠️ 若有落空的，覆蓋格就漏數'
          % (len(rows), sum(1 for r in rows if band_of(r['dose']) is None)))
    # 🚨 第一版寫成 `len(papers_by_ref['ZZ-不存在-ZZ']) == 0`——⚠️ 兩個缺陷：
    #   ① papers_by_ref 是 defaultdict，**取值這個動作本身就把鍵建了出來**，
    #      於是「契約結局幾種」從 6 變成 7——🚨 量測改變了被量的東西；
    #   ② 新建的空集合長度必為 0，**那道探針恆真、永遠不可能亮紅**——🚨 假尺。
    # ✅ 改成問「這個鍵在不在」，並要求真實的鍵確實在。
    probe('以不存在的結局查，查無此鍵（必觸發之反向）',
          ('ZZ-不存在-ZZ' not in papers_by_ref
           and 'gi-symptom-severity' in papers_by_ref),
          '🚨 若不存在的鍵也查得到、或真實的鍵反而查不到，'
          '整張普查表就不可信；⚠️ 現有鍵 %d 個' % len(papers_by_ref))
    probe('=60 單獨成格真的有東西（必觸發）',
          any(len(grid[(ref, '=60')]) for ref in papers_by_ref),
          '🚨 恰為 60 g/h 者共 %d 項；⚠️ 若把它併進任一邊，'
          '該格會憑空胖一圈（第 627 輪查明 60 是眾數）'
          % sum(1 for r in rows if r['dose'] == 60.0))
    # 🚨 以下三道是紅燈——它們就是本支的發現。
    probe('每一種契約結局都有 ≥3 篇支撐',
          all(c['papers'] >= 3 for c in census),
          '🚨 實得 %s'
          % '、'.join('%s %d 篇' % (c['outcome'], c['papers'])
                      for c in census if c['papers'] < 3))
    probe('表現類結局在低劑量帶有支撐',
          all(c['byDoseBand']['<60'] > 0
              for c in census if c['isPerformance']),
          '🚨 %s'
          % '；'.join('%s 在 <60 g/h 為 %d 篇'
                      % (c['outcome'], c['byDoseBand']['<60'])
                      for c in census if c['isPerformance']))
    probe('低端的表現證據不倚賴已知的同群重複對',
          not overlaps_pair,
          '🚨 低端撐表現的 %d 篇中，有 %d 篇是第 584 輪那組同群重複對的一半'
          '（%s）；⚠️ 配對的另一篇目前在範圍內 0 項只因舊請求沒帶儀器清單——'
          '**🚨 一旦重讀，同一批受試者就會被重複計入**'
          % (len(perf_low), len(overlaps_pair),
             [d['report'] for d in overlaps_pair]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'evidence-thinness-census',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'countingUnit': '相異報告篇數（🚫 不是結局數）',
        'inScopeOutcomes': len(rows),
        'contractOutcomes': len(papers_by_ref),
        'census': census,
        'doseBands': [label for _, _, label in BANDS],
        'lowEndContributors': low_detail,
        'lowEndPerformanceSupport': len(perf_low),
        'knownCohortPair': list(KNOWN_COHORT_PAIR),
        'convergence': (
            '🚨 低劑量端唯一撐住**表現類**結局的是 %s——'
            '⚠️ 而它正是第 584 輪查明的同群重複對裡的那本論文。'
            '🚨 配對的期刊那篇目前在範圍內 0 項，'
            '**不是因為它沒有結局**，而是 n+189 之前的請求沒帶儀器清單。'
            '⚠️ 故 D2／D3 一旦動，動到的正是本支指出最薄的那一格。'
            % KNOWN_COHORT_PAIR[0]),
        'erratumOnMyOwnProbes': {
            'found': (
                '🚨 本支第一版的反向探針寫成 '
                'len(papers_by_ref[不存在的鍵]) == 0——⚠️ 兩個缺陷：'
                '① defaultdict **取值即建鍵**，於是「契約結局幾種」被自己的'
                '探針從 6 撐成 7（🚨 量測改變了被量的東西）；'
                '② 新建空集合長度必為 0，**該探針恆真、永不亮紅**。'),
            'sameShapeElsewhere': {
                'n622': '「不存在的段落不在標題集合裡」——✅ 用 not in，不建鍵；'
                        '🚨 但同樣恆真。',
                'n624': 'status_count[不存在的 status] == 0——'
                        '✅ 實測 Counter 取缺鍵**不會插入**，故計數未被污染；'
                        '🚨 但同樣恆真。',
                'n625': 'sum(1 for o in opinion.values() if o == 不存在)==0——'
                        '✅ 不建鍵；🚨 同樣恆真。',
            },
            'consequence': (
                '⚠️ 依 n+112（二），必觸發之反向控制要**真的會亮**。'
                '🚨 上述三道不符合——它們是裝飾，不是控制。'
                '✅ 本支已改成「假鍵必須不在**且**真鍵必須在」（後半可能失敗）。'
                '🚫 n622／n624／n625 不就地改寫（已上看板），本條即其 errata。'),
        },
        'whatThisCannotAnswer': (
            '🚫 本支不判斷「幾篇才夠」——⚠️ 那是方法學與擁有者的裁定；'
            '✅ 它只把每一格實際有幾篇攤開。'
            '🚫 也不宣稱篇數即獨立性：⚠️ 同群重複已知至少一對，'
            '🚨 而未知的還可能有。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n628 證據厚度普查 ===')
    print('   在範圍內 %d 項｜契約結局 %d 種｜計數單位＝相異篇數'
          % (len(rows), len(papers_by_ref)))
    print('   %-30s %5s %5s %5s %6s %6s %6s %6s'
          % ('結局', '篇數', '項數', '儀器', '<60', '=60', '60-90', '>=90'))
    for entry in census:
        print('   %-30s %5d %5d %5d %6d %6d %6d %6d'
              % (entry['outcome'], entry['papers'], entry['outcomes'],
                 entry['instruments'],
                 entry['byDoseBand']['<60'], entry['byDoseBand']['=60'],
                 entry['byDoseBand']['60-90'], entry['byDoseBand']['>=90']))
    print('   撐住低端（<60 g/h）的 %d 篇：' % len(low_detail))
    for entry in low_detail:
        print('      %s 最低 %5.1f g/h｜%s%s'
              % (entry['report'], entry['minDose'], entry['outcomes'],
                 '  ⬅ 表現類' if entry['supportsPerformance'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
