# -*- coding: utf-8 -*-
"""**把連鎖掃描修好：只算「各自獨有憑證都指到」的共用論文。**（第 705 輪）

## 🚨 第 704 輪揭穿的混淆

第 703 輪說 `D18`／`D19`「共用 18 篇」。
**⚠️ 但第 704 輪實測：兩者的論文集合零重疊。**
🚨 那 18 篇之所以「共用」，只是因為**兩個決定引用了同一份憑證**（n624），
而那份憑證**同時列了兩個不相干的集合**。

> **🚨 共同引用一份多用途的憑證，會製造假連結。**

## ✅ 修法：要求**獨立佐證**

一篇論文要算成 A 與 B 的共用，必須：

- 出現在 **只有 A 引用**的憑證裡，**而且**
- 出現在 **只有 B 引用**的憑證裡

⚠️ 只出現在兩邊**共同引用**的那一份裡 → 🚫 不算。

## ✅ 而本支有兩個已知答案可以驗

| 對 | 應該 |
|---|---|
| `D3`／`D24`（第 701 輪實算為真） | **必須留下** |
| `D18`／`D19`（第 704 輪實算為假） | **必須掉光** |

> **🚨 一個修好的判準要同時通過這兩題，🚫 只過一題不算。**

## 🚫 本支不新增或修改任何決定、不送外部請求
"""
import collections
import itertools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n705_independent_corroboration.json'
REGISTER = HERE / 'n702_decision_register_v12.json'

REPORT = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
DID = re.compile(r'\bD[1-9][0-9]?\b')
MUST_SURVIVE = ('D24', 'D3')
MUST_DROP = ('D18', 'D19')
CORPUS_WIDE = 20


def text_of(item):
    return ' '.join(str(item.get(k) or '') for k in
                    ('ask', 'recommend', 'notADuplicateOf', 'sizeNote',
                     'interlock', 'executionPrerequisite'))


def evidence_files(item):
    out = []
    for part in str(item.get('evidence') or '').replace('；', ';').split(';'):
        name = part.split('→')[0].strip()
        if name and (HERE / name).is_file():
            out.append(name)
    return out


def main():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    items = {item['id']: item for item in register['items']}

    cited_by = collections.defaultdict(set)
    per_decision_files = {}
    for did, item in items.items():
        files = evidence_files(item)
        per_decision_files[did] = files
        for name in files:
            cited_by[name].add(did)

    reports_in = {}
    for name in cited_by:
        path = HERE / name
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and \
                doc.get('documentType') == 'pending-decision-register':
            reports_in[name] = set()
            continue
        reports_in[name] = set(REPORT.findall(
            path.read_text(encoding='utf-8')))

    def reports_from_exclusive(did, other):
        """只有 `did` 引用、`other` 沒引用的憑證裡出現的報告。"""
        out = set()
        for name in per_decision_files.get(did, ()):
            if other in cited_by.get(name, set()):
                continue
            out |= reports_in.get(name, set())
        return out

    all_reports = {d: set().union(*(reports_in.get(n, set())
                                    for n in per_decision_files[d]))
                   if per_decision_files[d] else set()
                   for d in items}
    specific = sorted(d for d in items
                      if 0 < len(all_reports[d]) < CORPUS_WIDE)

    rows = []
    for a, b in itertools.combinations(specific, 2):
        naive = all_reports[a] & all_reports[b]
        if not naive:
            continue
        corroborated = (reports_from_exclusive(a, b)
                        & reports_from_exclusive(b, a))
        cross = (b in set(DID.findall(text_of(items[a])))
                 or a in set(DID.findall(text_of(items[b]))))
        rows.append({
            'pair': [a, b],
            'naiveShared': len(naive),
            'independentlyCorroborated': len(corroborated),
            'sample': sorted(corroborated)[:3],
            'crossReferenced': cross,
            'coCitedFiles': sorted(set(per_decision_files[a])
                                   & set(per_decision_files[b])),
        })
    rows.sort(key=lambda r: (-r['independentlyCorroborated'],
                             -r['naiveShared'], r['pair']))

    survivors = [r for r in rows if r['independentlyCorroborated']]
    unrecorded = [r for r in survivors if not r['crossReferenced']]

    def find(pair):
        return next((r for r in rows if sorted(r['pair']) == sorted(pair)),
                    None)

    keep = find(MUST_SURVIVE)
    drop = find(MUST_DROP)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('已知為真的那一對必須留下（必觸發之正對照）',
          keep is not None and keep['independentlyCorroborated'] > 0,
          '🚨 `%s`／`%s`：素樸共用 %s、獨立佐證 %s；'
          '⚠️ 掉光的話這個判準太嚴，把真的連鎖也殺掉了'
          % (MUST_SURVIVE[0], MUST_SURVIVE[1],
             keep['naiveShared'] if keep else '—',
             keep['independentlyCorroborated'] if keep else '—'))
    probe('已知為假的那一對必須掉光（必觸發之反向）',
          drop is None or drop['independentlyCorroborated'] == 0,
          '🚨 `%s`／`%s`：素樸共用 %s、獨立佐證 %s、共同引用的憑證 %s；'
          '⚠️ 沒掉光的話這個判準沒有修好那個混淆'
          % (MUST_DROP[0], MUST_DROP[1],
             drop['naiveShared'] if drop else '未成對',
             drop['independentlyCorroborated'] if drop else '—',
             drop['coCitedFiles'] if drop else '—'))
    probe('判準真的比素樸版嚴（必觸發之反向）',
          len(survivors) < len(rows),
          '🚨 素樸候選 %d 對 → 有獨立佐證的 %d 對；'
          '⚠️ 若一樣多，代表這個判準什麼都沒篩掉'
          % (len(rows), len(survivors)))
    # 🚨 這一道是答案。
    probe('沒有「有獨立佐證卻兩邊都沒提對方」的決定對',
          not unrecorded,
          '🚨 候選 %d 對：%s；'
          '⚠️ 這一批才值得像第 701／704 輪那樣逐對算'
          % (len(unrecorded),
             [(r['pair'], r['independentlyCorroborated'])
              for r in unrecorded[:10]]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'independent-corroboration-interlocks',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'fixes': ('n703 的素樸「共用論文」訊號——'
                  '🚨 第 704 輪證明它會被**共同引用一份多用途憑證**污染。'),
        'rule': ('✅ 一篇論文要算成 A 與 B 的共用，必須**同時**出現在'
                 '「只有 A 引用」與「只有 B 引用」的憑證裡；'
                 '🚫 只出現在兩邊共同引用的那一份裡不算。'),
        'naiveCandidatePairs': len(rows),
        'corroboratedPairs': len(survivors),
        'unrecordedCandidates': unrecorded,
        'rows': rows,
        'validation': {'mustSurvive': keep, 'mustDrop': drop},
        'whyTwoKnownAnswers': (
            '🚨 一個修好的判準要**同時**通過兩題：'
            '把真的連鎖（`D3`／`D24`，第 701 輪實算）留下，'
            '把假的（`D18`／`D19`，第 704 輪實算）殺掉。'
            '**⚠️ 只過一題的判準，可能只是變嚴或變鬆。**'),
        'methodLimit': (
            '⚠️ 「獨立佐證」仍只是**必要條件**，🚫 不是連鎖的證明——'
            '🚨 兩個決定可能只是碰巧都提到同一篇論文。'
            '✅ 真正的連鎖仍要像第 701 輪那樣**算後果**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n705 只算獨立佐證的連鎖 ===')
    print('   素樸候選 %d 對 → 有獨立佐證 %d 對 → 其中兩邊都沒提對方 %d 對'
          % (len(rows), len(survivors), len(unrecorded)))
    print('   驗證：')
    print('      必須留下 %s：素樸 %s／獨立佐證 %s'
          % ('／'.join(MUST_SURVIVE),
             keep['naiveShared'] if keep else '—',
             keep['independentlyCorroborated'] if keep else '—'))
    print('      必須掉光 %s：素樸 %s／獨立佐證 %s'
          % ('／'.join(MUST_DROP),
             drop['naiveShared'] if drop else '未成對',
             drop['independentlyCorroborated'] if drop else '—'))
    print('   有獨立佐證的對：')
    for row in survivors[:12]:
        print('      %-9s 素樸 %2d → 獨立 %2d｜互相提到：%s'
              % ('／'.join(row['pair']), row['naiveShared'],
                 row['independentlyCorroborated'],
                 '✅' if row['crossReferenced'] else '🚨 沒有'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
