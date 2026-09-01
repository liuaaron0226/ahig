# -*- coding: utf-8 -*-
"""**決策登記簿 v5——把第 679 輪那個落差登記掉。**（第 680 輪）

## ✅ 承接 v4（25 項），🚫 不改寫它

第 679 輪查出：`shapes/core` 守備 8 類、`shapes/sparql` 守備 7 類，
🚨 而 `OutcomeInventory` 與 **`QuantitativeStudyResult`** **只有 core 守備**——
⚠️ 後者正是「量化 StudyResult 必須有點估計／不確定性區間」那條規則的所在。

⚠️ 而聲稱要守住這件事的那條測試，**主體從沒比較過兩個集合**
（突變證明：把 sparql 換成與 core 完全不相交，斷言照樣通過）。

> **📮 這一件本室不判——動到的是產品的測試與形狀，是裁定。**
> **🚨 但它必須被登記，🚫 不能只留在看板上。**

## ✅ 本支立刻登記，🚫 不留到下一輪

⚠️ 第 673／674 輪剛示範過：沒被登記的發現，只靠「有人提過那一輪」撐著。

## 🚫 本支不改任何清冊與契約、不送外部請求
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
OUT = HERE / 'n680_decision_register_v5.json'
V4 = HERE / 'n675_decision_register_v4.json'

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
    v4 = json.loads(V4.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v4['items']}

    core_only = cite('n679_profile_coverage_gap.json', 'coreOnly')
    sparql_only = cite('n679_profile_coverage_gap.json', 'sparqlOnly')
    orphan_rules = cite('n679_profile_coverage_gap.json',
                        'rulesLivingOnlyInCore')
    compares = cite('n679_profile_coverage_gap.json', 'theTest',
                    'bodyComparesTheTwoSets')

    new_items = [{
        'id': 'D26', 'round': 679, 'status': 'open',
        'blocks': '驗收可信度',
        'ask': '兩個 SHACL profile 的守備範圍要不要一致？'
               '以及那條聲稱在守它的測試，是名不副實還是註解寫錯？',
        'evidence': 'n679_profile_coverage_gap.json；'
                    'n678_shacl_v21_anchor_spec.json',
        'recommend': (
            '⚠️ 建議先決定**哪一邊是對的**，🚫 本室不判。'
            '🚨 實測：只有 core 守備 %s；sparql 獨有 %s。'
            '⚠️ 而只存在於 core 的具名規則有 %d 條，'
            '**其中兩條正是「量化 StudyResult 必須有點估計／不確定性區間」**——'
            '🚨 故只跑 SPARQL（稽核）profile 驗收，'
            '**一個沒有信賴區間的量化結果會通過**。'
            '⚠️ 而那條測試的主體是否比較過兩個集合：%s'
            '（突變證明：換成完全不相交的集合，斷言照樣通過）。'
            % (core_only, sparql_only, len(orphan_rules or []), compares)),
        'notADuplicateOf': (
            '🚨 D25 問的是**要不要抽數值**；'
            '⚠️ 本項問的是**抽出來之後，驗收時會不會被漏掉**——'
            '✅ 兩者相依但不是同一件事：'
            '**就算 D25 裁了要抽，這個落差仍會讓沒有區間的結果通過稽核。**'),
    }]

    merged = list(items.values()) + new_items
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v4 的全部登記（必觸發之正對照）',
          len(items) == 25,
          '🚨 承接 %d 項｜新增 %d 項｜合計 %d 項；⚠️ 少接一項就是把待裁定弄丟了'
          % (len(items), len(new_items), len(merged)))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s；⚠️ 取不到就代表登記簿與憑證脫節'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))

    def evidence_resolves(item):
        parts = str(item['evidence']).replace('；', ';').split(';')
        return any((HERE / part.split('→')[0].strip()).exists()
                   for part in parts if part.strip())

    dangling = [item['id'] for item in merged if not evidence_resolves(item)]
    probe('每一項都指得到真的證據檔（必觸發）',
          not dangling,
          '🚨 檢查 %d 項；指不到檔的：%s；⚠️ 指到不存在的檔就是空頭支票'
          % (len(merged), dangling or '無'))
    probe('新增項聲明了它與最近既有項的關係（必觸發之反向）',
          all(item.get('notADuplicateOf') for item in new_items),
          '🚨 新增 %d 項，未聲明者：%s；⚠️ 不聲明就可能只是把既有的重登一次'
          % (len(new_items),
             [i['id'] for i in new_items if not i.get('notADuplicateOf')]
             or '無'))
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s；⚠️ 這些不決定，A 系列過不了'
          % (len(blockers), blockers))

    doc = {
        'schemaVersion': 5,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n675_decision_register_v4.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 把第 679 輪那個 profile 守備落差**當輪登記**為 D26，'
            '🚫 不留到下一輪——⚠️ 第 673／674 輪剛示範過'
            '「沒被登記的發現只靠有人提過那一輪撐著」。'),
        'counts': {'carriedOver': len(items), 'added': len(new_items),
                   'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open')},
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'howToUse': (
            '✅ 每一項都附證據檔與本室建議；'
            '⚠️ 引用的數字是**執行時從憑證取的**，🚫 不是手打的。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n680 決策登記簿 v5 ===')
    print('   承接 %d｜新增 %d｜合計 %d（open %d）'
          % (len(items), len(new_items), len(merged), doc['counts']['open']))
    for item in new_items:
        print('   %s 阻擋 %s' % (item['id'], item['blocks']))
        print('      問：%s' % item['ask'])
        print('      建議：%s' % item['recommend'])
        print('      不是重複：%s' % item['notADuplicateOf'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
