# -*- coding: utf-8 -*-
"""**決策登記簿 v11——補上 `D25` 漏掉的三支規格憑證。**（第 700 輪）

## 🚨 第 699 輪排順序時撞出來的漏洞

排序要看「這個決定有沒有前置條件擋著」，而本室加了第二條偵測管道：
**去讀它的證據憑證**。

> **🚨 結果 `D25` 的證據清單裡根本沒有 n676／n677／n678——
> ⚠️ 而那三支正是 D25 的**規格**（要抽哪些欄位、一份合法的 StudyResult 還要帶什麼）。**

⚠️ 本室在看板上寫過它們，🚫 但從來沒掛進登記簿。
**✅ 而登記簿才是裁定時會被讀的東西。**

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
OUT = HERE / 'n700_decision_register_v11.json'
V10 = HERE / 'n698_decision_register_v10.json'

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
    v10 = json.loads(V10.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v10['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince698', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    attach('D25', '✅ 消費端實際要求的欄位數／清冊已有幾個',
           [len(cite('n676_numeric_field_requirements.json',
                     'requiredTopLevelFields') or []),
            len(cite('n676_numeric_field_requirements.json',
                     'alreadyPresent') or [])],
           'n676_numeric_field_requirements.json')
    attach('D25', '🚨 一份合法 StudyResult 還要帶的東西（SHACL 要、程式沒碰）',
           len(cite('n677_shacl_studyresult_spec.json',
                    'shaclOnlyNotSeenByRunAll') or []),
           'n677_shacl_studyresult_spec.json')
    attach('D25', '🚨 每個數字都要配一段**唯一命中**的逐字引文（v2.1 對 anchor 的約束）',
           len(cite('n678_shacl_v21_anchor_spec.json',
                    'v21ConstraintsOnStudyResultAndAnchor') or []),
           'n678_shacl_v21_anchor_spec.json')

    items['D25']['executionPrerequisite'] = (
        '🚨 **裁了之後要動工，需要讀論文的視窗（n+187）**——'
        '⚠️ 抽數值與取逐字引文都必須讀原文。'
        '✅ 第 688 輪的工作清單就是為那個視窗備的（98 項／50 組）。'
        '🚫 本室不在這個視窗讀論文。')

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v10 的全部登記（必觸發之正對照）',
          len(items) == 27,
          '🚨 承接 %d 項' % len(items))
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
    # 🚨 這一道是本版的重點。
    d25_ev = str(items['D25']['evidence'])
    need = ['n676_numeric_field_requirements.json',
            'n677_shacl_studyresult_spec.json',
            'n678_shacl_v21_anchor_spec.json']
    probe('`D25` 的證據裡已經有它的規格三支',
          all(n in d25_ev for n in need),
          '🚨 缺的：%s；⚠️ 少了規格，裁定的人看不到「要抽什麼、還要帶什麼」'
          % ([n for n in need if n not in d25_ev] or '無'))
    probe('`D25` 已載明動工的前置條件（必觸發之反向）',
          'n+187' in items['D25'].get('executionPrerequisite', ''),
          '🚨 前置條件說明：%s'
          % items['D25'].get('executionPrerequisite', '🚨 缺')[:80])

    doc = {
        'schemaVersion': 11,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n698_decision_register_v10.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '🚨 第 699 輪排順序時撞出漏洞：`D25` 的證據清單裡'
            '**沒有它自己的規格**（n676／n677／n678）——'
            '⚠️ 本室在看板上寫過，🚫 但沒掛進登記簿，'
            '**而登記簿才是裁定時會被讀的東西。**'
            '✅ 一併補上動工的前置條件（`n+187`）。'),
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

    print('=== n700 決策登記簿 v11 ===')
    print('   合計 %d 項（open %d）｜本版更新：%s'
          % (len(merged), doc['counts']['open'], updated))
    for row in items['D25']['newEvidenceSince698']:
        print('      %s ＝ %s' % (row['label'], row['value']))
    print('   D25 前置條件：%s' % items['D25']['executionPrerequisite'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
