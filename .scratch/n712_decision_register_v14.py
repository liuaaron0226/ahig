# -*- coding: utf-8 -*-
"""**決策登記簿 v14——`D23` 的份量被低估了。**（第 712 輪）

## 🚨 為什麼不等批次

`D23`（回補空白欄位）現在的建議只寫「4 項是強漏填訊號」——
**⚠️ 那讀起來像是一件小事。**

> **🚨 而第 711 輪算出：補回那些空白劑量，
> `tt-completion-time` 最多可以從「**0 組**同篇內劑量對比」變成 **3 組**。**
> ⚠️ 而那個結局是**耐力表現最直接的一個**，
> 🚨 目前**零篇**提供同篇內對比（第 710 輪）。

**✅ 一則把效益寫小了的登記，會讓它被排到後面。**

## 🚫 本版不新增決策、不改任何清冊與契約、不送外部請求
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n712_decision_register_v14.json'
V13 = HERE / 'n707_decision_register_v13.json'

CITATIONS = []


def cite(filename, *keys):
    path = HERE / filename
    entry = {'from': filename, 'path': ' → '.join(str(k) for k in keys)}
    try:
        node = json.loads(path.read_text(encoding='utf-8'))
        for key in keys:
            node = node[key]
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        node = None
    entry['value'] = node
    CITATIONS.append(entry)
    return node


def main():
    v13 = json.loads(V13.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v13['items']}

    focus_gain = cite('n711_blank_dose_contrast_potential.json',
                      'focusGroupsThatCouldGain')
    by_outcome = cite('n710_within_study_dose_contrast.json', 'byOutcome')
    total_multi = cite('n710_within_study_dose_contrast.json',
                       'papersWithAnyWithinStudyContrast')

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince707', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    attach('D23',
           '🚨 補回空白劑量後，`tt-completion-time` 可能獲得的同篇內對比組數'
           '（目前是 0）',
           len(focus_gain or []),
           'n711_blank_dose_contrast_potential.json')
    attach('D23', '⚠️ 全語料目前提供同篇內劑量對比的論文數',
           total_multi, 'n710_within_study_dose_contrast.json')
    attach('D25', '⚠️ 各結局的同篇內多劑量對比（劑量-反應的上限之一）',
           {k: v.get('papersMultiDose') for k, v in (by_outcome or {}).items()},
           'n710_within_study_dose_contrast.json')

    items['D23']['sizeNote'] = (
        '🚨 **本項的效益比原本寫的大。**'
        '⚠️ 原建議只提「4 項是強漏填訊號」，'
        '🚨 但第 711 輪算出：補回空白劑量後，'
        '**`tt-completion-time` 最多可從 0 組同篇內劑量對比變成 %d 組**——'
        '⚠️ 而那是耐力表現最直接的結局，目前**零篇**提供同篇內對比。'
        '**🚫 那是「可能」，不是「會」：補進來的值若與現有的相同，仍然沒有對比。**'
        % len(focus_gain or []))

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        if item['status'] == 'open':
            by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v13 的全部登記（必觸發之正對照）',
          len(items) == 27, '🚨 承接 %d 項' % len(items))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))

    def evidence_resolves(item):
        parts = str(item['evidence']).replace('；', ';').split(';')
        return all((HERE / part.split('→')[0].strip()).exists()
                   for part in parts if part.strip())

    dangling = [item['id'] for item in merged if not evidence_resolves(item)]
    probe('每一項的每一個證據檔都存在（必觸發）',
          not dangling,
          '🚨 檢查 %d 項；有指不到檔的：%s' % (len(merged), dangling or '無'))
    probe('`D23` 的份量說明有把「可能」講清楚（必觸發之反向）',
          '不是「會」' in items['D23']['sizeNote'],
          '🚨 份量說明：%s；⚠️ 沒把「可能」講清楚，就會被讀成承諾'
          % items['D23']['sizeNote'][:100])
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s' % (len(blockers), blockers))

    doc = {
        'schemaVersion': 14,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n707_decision_register_v13.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '🚨 `D23` 的效益被本室自己寫小了——'
            '⚠️ 原建議只提「4 項是強漏填訊號」，'
            '🚨 而第 711 輪算出它可能讓最要緊的結局'
            '從 0 組同篇內對比變成 %d 組。'
            '**✅ 一則把效益寫小的登記，會讓它被排到後面。**'
            % len(focus_gain or [])),
        'counts': {'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open')},
        'decisionsUpdatedThisRound': updated,
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n712 決策登記簿 v14 ===')
    print('   合計 %d 項（open %d）｜本版更新：%s'
          % (len(merged), doc['counts']['open'], updated))
    print('   D23 的份量說明：%s' % items['D23']['sizeNote'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
