# -*- coding: utf-8 -*-
"""**待裁定的登記簿，補上第 624–633 輪改變的那幾件。**（第 634 輪）

## 🚨 十輪過去，好幾件待裁定的**輕重與價碼**都變了，而沒有一處把它們合起來

⚠️ 第 610 輪登記了 D1–D16，第 611 輪加了 D17，第 624 輪加了 D18–D20。
🚨 而第 624–633 輪查出的東西直接改變了其中幾件：

- **D17** 從「要不要修」變成「**要不要付 14 份清冊、43 項的重讀**」；
- **D2／D3** 從整潔問題變成「**它動到的是本 run 最薄的那一格**」；
- **D18／D19** 從補件變成「**低劑量端的錨**」。

## ✅ 本支的規矩：引用的數字**在執行時從憑證讀出來**

🚨 手打的數字會跟證據脫節，⚠️ 而脫節的登記簿比沒有登記簿更糟——
**它看起來有根據。** ✅ 故每一個引用都寫成「憑證檔 ＋ 欄位路徑」，由本支去取值；
**⚠️ 取不到就亮紅。**

## 🚫 本支不新增待裁定項目，🚫 不改任何清冊，🚫 不送外部請求
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

S = Path(__file__).resolve().parent
OUT = S / 'n634_decision_register_v2.json'

# ⚠️ 第 624–633 輪為既有待裁定補上的事實。
# 🚨 值一律寫成「檔名 ＋ 欄位路徑」，由本支執行時取——不手打。
NEW_EVIDENCE = {
    'D2': [('n628_evidence_thinness.json', ['lowEndPerformanceSupport'],
            '低劑量端撐住表現類結局的篇數')],
    'D3': [('n628_evidence_thinness.json', ['lowEndPerformanceSupport'],
            '低劑量端撐住表現類結局的篇數——🚨 那一篇正是這一對的論文那半')],
    'D17': [('n630_binding_integrity.json',
             ['d17Cost', 'inventoriesBoundToGrobidSections'],
             '會失效的清冊份數'),
            ('n630_binding_integrity.json',
             ['d17Cost', 'inScopeOutcomesAffected'],
             '受影響的在範圍內結局數'),
            ('n630_binding_integrity.json',
             ['d17Cost', 'shareOfAllInScope'], '佔全體百分比')],
    'D18': [('n625_corpus_era_bias.json', ['eraBlockers', '≤1999',
                                           '位置已知未取'],
             '2000 年前「位置已知、只差去取」的篇數')],
    'D19': [('n625_corpus_era_bias.json', ['eraBlockers', '≤1999',
                                           'Unpaywall 從未被問'],
             '2000 年前從未被問過 Unpaywall 的篇數'),
            ('n624_corpus_denominator.json', ['singleBlocker', 'count'],
             '全體卡在同一個關卡的份數')],
}

# ⚠️ 第 624 輪新增的三件（第 610 輪之後才有），一併登記。
NEW_ITEMS = [
    {'id': 'D18', 'round': 624, 'status': 'open', 'blocks': '語料完整性',
     'ask': '那 18 篇「判定可得卻未取」要不要補取？',
     'evidence': 'n624_corpus_denominator.json',
     'recommend': '⚠️ 建議補取，且**先做 2000 年前那批**——'
                  '🚨 它們位置已知、零次新查詢。'
                  '🚫 需外部請求，本室不自行開跑。'},
    {'id': 'D19', 'round': 624, 'status': 'open', 'blocks': '語料完整性',
     'ask': '卡在 unpaywall=blocked 的那批要不要用現有信箱重問？',
     'evidence': 'n624_corpus_denominator.json',
     'recommend': '⚠️ 建議重問，優先 2000 年前那批——'
                  '🚨 那是打開該年代的唯一鑰匙。'
                  '🚫 需大量外部請求，須照 n+146（三）／n+150（三）節流。'},
    {'id': 'D20', 'round': 624, 'status': 'open', 'blocks': '無（整潔）',
     'ask': '4 個舊命名的孤兒目錄怎麼處置？',
     'evidence': 'n624_corpus_denominator.json',
     'recommend': '✅ 建議記 errata、**不刪**——🚫 刪檔本室一律不自行動手。'},
]


def by_number(decision_id):
    """⚠️ 依編號排序；🚨 字典序會排成 D1, D10, D12, D2——協調者要讀的東西不該長那樣。"""
    return int(str(decision_id)[1:])


def dig(doc, path):
    cur = doc
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def main():
    previous = json.loads(
        (S / 'n610_pending_decisions.json').read_text(encoding='utf-8'))
    items = {row['id']: dict(row) for row in previous['items']}
    for row in NEW_ITEMS:
        items.setdefault(row['id'], dict(row))

    # ⚠️ 第 611 輪的 D17 不在 n610 裡，補進來。
    items.setdefault('D17', {
        'id': 'D17', 'round': 611, 'status': 'open', 'blocks': '酬載品質',
        'ask': '要不要修 parse_tei 漏掉表格的缺陷？',
        'evidence': 'n612_parse_tei_root_cause.json',
        'recommend': '⚠️ 建議修，🚨 但論文那篇的文獻整理表不得當成它自己的結果。'})

    resolved = []
    missing_evidence = []
    for decision_id, refs in NEW_EVIDENCE.items():
        entry = items.get(decision_id)
        if entry is None:
            missing_evidence.append((decision_id, '（無此待裁定）'))
            continue
        facts = []
        for filename, path, label in refs:
            source = S / filename
            if not source.is_file():
                missing_evidence.append((decision_id, filename))
                continue
            value = dig(json.loads(source.read_text(encoding='utf-8')), path)
            if value is None:
                missing_evidence.append(
                    (decision_id, '%s:%s' % (filename, '/'.join(map(str, path)))))
                continue
            facts.append({'label': label, 'value': value,
                          'from': '%s → %s' % (filename,
                                               '/'.join(map(str, path)))})
        if facts:
            entry['newEvidenceSince610'] = facts
            resolved.append(decision_id)

    open_items = [v for v in items.values() if v.get('status') == 'open']
    blocking_gates = {}
    for entry in open_items:
        blocking_gates.setdefault(entry.get('blocks') or '（未標）', []).append(
            entry['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到第 610 輪的登記（必觸發之正對照）',
          len(previous['items']) == 16 and len(items) >= 20,
          '🚨 前一版 %d 項、本版 %d 項；⚠️ 少於前一版就代表本支弄丟了東西'
          % (len(previous['items']), len(items)))
    probe('每一個新引用都取得到值（必觸發）',
          not missing_evidence,
          '🚨 取不到的引用 %d 筆：%s；'
          '⚠️ **取不到的引用比沒有引用更糟——它看起來有根據**'
          % (len(missing_evidence), missing_evidence[:5]))
    probe('每一項都指得到真的證據檔（必觸發）',
          all((S / (v.get('evidence') or '')).is_file()
              for v in items.values() if v.get('evidence')),
          '🚨 實得指不到者：%s'
          % [v['id'] for v in items.values()
             if v.get('evidence') and not (S / v['evidence']).is_file()])
    probe('每一項都有本室的建議（必觸發）',
          all(v.get('recommend') for v in items.values()),
          '🚨 只提問而不建議，等於把工作原封退回去；實得缺建議：%s'
          % [v['id'] for v in items.values() if not v.get('recommend')])
    # 🚨 這一道是狀態，不是缺陷——⚠️ 但它就是本室交不出關卡的原因。
    probe('沒有待裁定卡著內容關卡',
          not [v for v in open_items
               if str(v.get('blocks') or '').startswith('A')],
          '🚨 卡著內容關卡的待裁定 %d 件：%s'
          % (len([v for v in open_items
                  if str(v.get('blocks') or '').startswith('A')]),
             sorted((v['id'] for v in open_items
                     if str(v.get('blocks') or '').startswith('A')),
                    key=by_number)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'pending-decisions-register-v2',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n610_pending_decisions.json（🚫 不改寫該檔）',
        'addsNothingNew': (
            '🚫 本支不新增待裁定項目——✅ 只承接、補登第 611／624 輪已提的三件，'
            '並替第 624–633 輪查出的事實掛回對應的決定。'),
        'counts': {'total': len(items), 'open': len(open_items),
                   'withNewEvidence': len(resolved)},
        'openByBlocking': {k: sorted(v, key=by_number)
                           for k, v in blocking_gates.items()},
        'decisionsUpdatedThisChain': sorted(resolved, key=by_number),
        'items': sorted(items.values(), key=lambda r: by_number(r['id'])),
        'howToUse': (
            '✅ 每一項都附證據檔與本室建議；'
            '⚠️ 引用的數字是**執行時從憑證取的**，🚫 不是手打的——'
            '故登記簿不會跟證據脫節。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n634 待裁定登記簿 v2 ===')
    print('   合計 %d 件｜未決 %d 件｜本鏈補上新事實者 %d 件'
          % (len(items), len(open_items), len(resolved)))
    print('   卡著什麼：')
    for gate, ids in sorted(blocking_gates.items()):
        print('      %-14s %s' % (gate, ' '.join(sorted(ids, key=by_number))))
    print('   第 624–633 輪掛回去的事實：')
    for decision_id in sorted(resolved, key=by_number):
        for fact in items[decision_id]['newEvidenceSince610']:
            print('      %-4s %s = %s' % (decision_id, fact['label'],
                                          fact['value']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
