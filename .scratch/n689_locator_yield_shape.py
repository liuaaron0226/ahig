# -*- coding: utf-8 -*-
"""**那些定位點，指得到表／圖嗎。**（第 689 輪）

## ✅ 補上第 688 輪自己寫下的限制

n688：「🚨 『有定位點』🚫 不等於『那個位置真的有數字』。」

## ✅ 而前人已經把兩個相鄰的問題查掉了

- **n590**：790 項的來源段落**全部真的存在**；在範圍內的 98 項**沒有一項**取自導論／討論段。
- **n609**：在範圍內的 98 項**沒有一項**引用標題像方法段的段落（13 項全在範圍外）。

> **🚨 故剩下的正是這一題：定位點**帶不帶表／圖指標**。**
> ⚠️ 那是**結構**訊號，🚫 不是對段落名做關鍵字判斷——
> 本室已經三次做出沒有鑑別力的關鍵字規則，這一支刻意不走那條路。

## ✅ 為什麼這個訊號有意義

🚨 效應量、信賴區間、樣本數**通常落在表裡**；
⚠️ 只指到段落的項目，讀的人得在段落裡自己找。
**✅ 這不判定有沒有數字，🚫 只把工作組排出「先做哪一批」的順序。**

## 🚫 本支不輸出任何段落名或表號文字、不改任何清冊、不送外部請求
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
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n689_locator_yield_shape.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')


def shape_of(reported):
    """定位點的**形狀**（🚫 不看內容文字）。"""
    loc = reported.get('sourceLocation')
    if not isinstance(loc, dict):
        return '無定位'
    has_table = loc.get('tableOrFigure') is not None
    has_page = loc.get('pageIndex') is not None
    has_section = loc.get('section') is not None
    if has_table:
        return '表／圖' + ('＋頁' if has_page else '')
    if has_page:
        return '頁碼＋段落' if has_section else '只有頁碼'
    return '只有段落' if has_section else '無定位'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    in_scope = collections.Counter()
    out_scope = collections.Counter()
    by_outcome = collections.defaultdict(collections.Counter)
    groups = collections.defaultdict(list)
    total_in, total_out = 0, 0

    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            shape = shape_of(reported)
            if decision['inScope']:
                total_in += 1
                in_scope[shape] += 1
                by_outcome[reported['normalisedOutcomeRef']][shape] += 1
                loc = reported.get('sourceLocation') or {}
                key = '%s｜%s' % (inventory['report'][-16:],
                                 json.dumps(loc, sort_keys=True))
                groups[key].append(shape)
            else:
                total_out += 1
                out_scope[shape] += 1

    with_table = sum(v for k, v in in_scope.items() if k.startswith('表／圖'))
    group_with_table = sum(
        1 for shapes in groups.values()
        if any(s.startswith('表／圖') for s in shapes))
    items_in_table_groups = sum(
        len(shapes) for shapes in groups.values()
        if any(s.startswith('表／圖') for s in shapes))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('掃到的正是那 98 項（必觸發之正對照）',
          total_in == 98,
          '🚨 在範圍內 %d 項、範圍外 %d 項；⚠️ 對不上就與前幾輪不一致'
          % (total_in, total_out))
    # 🚨 必觸發之反向：同一支分類器套到範圍外那批，分佈必須不同，
    # ⚠️ 否則它可能是在回傳一個常數。
    probe('同一支分類器在範圍外那批上給出不同分佈（必觸發之反向）',
          dict(in_scope) != dict(out_scope) and len(out_scope) > 0,
          '🚨 在範圍內 %s；範圍外 %s；'
          '⚠️ 兩者一模一樣的話，這支分類器可能只是在回傳常數'
          % (dict(in_scope.most_common()), dict(out_scope.most_common())))
    probe('分類窮盡，沒有落到「無定位」的（必觸發之正對照）',
          in_scope.get('無定位', 0) == 0,
          '🚨 在範圍內「無定位」%d 項；⚠️ 與第 688 輪的 0 項須一致'
          % in_scope.get('無定位', 0))
    # 🚨 這一道是答案。
    probe('在範圍內的項目，定位點都指得到表／圖',
          with_table == total_in,
          '🚨 指到表／圖的 %d／%d 項（%.0f%%）；'
          '⚠️ 其餘只指到頁或段落——**讀的人得自己在那一段裡找數字**'
          % (with_table, total_in,
             100.0 * with_table / total_in if total_in else 0))

    doc = {
        'schemaVersion': 1,
        'documentType': 'locator-yield-shape',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n688（有定位點不等於那裡有數字）',
        'buildsOn': ('n590（在範圍內 0 項取自導論／討論段）；'
                     'n609（在範圍內 0 項引用方法段標題）'),
        'inScopeTotal': total_in,
        'inScopeByShape': dict(in_scope.most_common()),
        'outOfScopeByShape': dict(out_scope.most_common()),
        'byOutcome': {k: dict(v.most_common())
                      for k, v in sorted(by_outcome.items())},
        'workGroups': len(groups),
        'workGroupsWithTablePointer': group_with_table,
        'itemsInTablePointingGroups': items_in_table_groups,
        'tablePointerRate': {
            'inScope': round(100.0 * with_table / total_in, 1)
            if total_in else 0,
            'outOfScope': round(
                100.0 * sum(v for k, v in out_scope.items()
                            if k.startswith('表／圖')) / total_out, 1)
            if total_out else 0,
            'note': ('🚨 在範圍內的項目**比較不常**指到表——'
                     '⚠️ 而這只是描述：範圍外那 692 項裡有 647 項'
                     '**根本沒對上任何契約結局**，🚫 兩群不可比因果。'),
        },
        'outcomesWithNoTablePointerAtAll': sorted(
            ref for ref, shapes in by_outcome.items()
            if not any(s.startswith('表／圖') for s in shapes)),
        'howToUseThis': (
            '✅ 先做**帶表／圖指標**的工作組——'
            '🚨 效應量、區間、樣本數通常落在表裡。'
            '⚠️ 只指到段落的那些留到後面，'
            '**因為讀的人得在段落裡自己找**。'),
        'whatThisIsNot': (
            '🚫 本支**不判定那裡有沒有數字**——⚠️ 它只看定位點的**形狀**。'
            '🚨 一個指到表的項目也可能該表沒有它要的那一格；'
            '⚠️ 一個只指到段落的項目也可能段落裡就寫著數字。'
            '**✅ 這是排序訊號，🚫 不是判定。**'),
        'contentDiscipline': (
            '✅ 只輸出形狀分類與計數，🚫 未輸出任何段落名或表號文字'
            '（n+195 一）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n689 定位點的形狀 ===')
    print('   在範圍內 %d 項：%s' % (total_in, dict(in_scope.most_common())))
    print('   範圍外 %d 項：%s' % (total_out, dict(out_scope.most_common())))
    print('   工作組 %d 個｜其中含表／圖指標 %d 個（涵蓋 %d 項）'
          % (len(groups), group_with_table, items_in_table_groups))
    print('   各結局的定位點形狀：')
    for ref in sorted(by_outcome):
        print('      %-32s %s' % (ref, dict(by_outcome[ref].most_common())))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
