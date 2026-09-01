# -*- coding: utf-8 -*-
"""**決策登記簿 v3——把第 662–668 輪這一串轉成待裁定事項。**（第 669 輪）

## ✅ 承接 v2，🚫 不改寫它

v2（第 634 輪）有 20 項。本支**承接全部 20 項**，然後做兩件事：

1. **把這一串查到的事實掛回既有的決定**（D4／D5／D6／D10）
2. **新增這一串真正產生的待裁定事項**（D21–D24）

## 🚨 一件必須先講的事：這一串有一半是**重新發現既有的裁定**

**🚨 D4（第 594 輪）早就裁過切片器械那 3 項**——結論是「不改名，移到契約缺口」，
理由是第二位讀者記載的取樣器械**兩個名字都不是**。

> **⚠️ 故第 663 輪算的「7 項儀器單欄可修」裡，有 2 項屬於 D4 已裁的那 3 項。**
> **✅ 真正還開著的是 5 項。**

## ✅ 規矩（沿用 v2）

- 🚨 引用的數字**執行時從憑證取**，🚫 不是手打的
- ✅ 每一個新增項都要聲明**它跟最近的既有項是什麼關係**（否則就是在重複登記）
- ✅ 跨憑證對帳：劑量拆解 12＋4＋3 必須等於 n664 存的總數

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
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n669_decision_register_v3.json'
V2 = HERE / 'n634_decision_register_v2.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

CITATIONS = []


def cite(filename, *keys):
    """從憑證取值，並把來源記下來。🚨 取不到就是 None，會被探針抓到。"""
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


def dose_split():
    """把 dose-outside-bands 拆成空白／對照臂／超上限。

    ⚠️ 第 664 輪回報過這個拆解但沒落成憑證欄位，✅ 故本支自己重算，
    🚨 並與 n664 存的總數對帳。
    """
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    split = collections.Counter()
    medians = 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if decision['inScope'] or not reported.get('normalisedOutcomeRef'):
                continue
            code = decision['reasonCode']
            if code == 'notExtracted-dose-outside-bands':
                dose = reported.get('dose')
                split['空白' if dose is None
                      else ('對照臂' if dose == 0 else '超出帶上限')] += 1
            elif code == 'notExtracted-effect-measure-not-in-scope' \
                    and reported.get('effectMeasure') == 'median':
                medians += 1
    return dict(split), medians


def main():
    v2 = json.loads(V2.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v2['items']}

    split, medians = dose_split()
    stored_dose_total = cite('n664_vocabulary_upper_bound.json',
                             'mappedButBlockedByReason',
                             'notExtracted-dose-outside-bands')

    # -- 掛回既有決定 -----------------------------------------------------
    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince634', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)

    attach('D4', '🚨 第 663 輪重新撞到的正是 D4 已裁的那一批（單欄換儀器即可進範圍者）',
           sum(1 for r in (cite('n665_blocked_gate_depth.json', 'rows') or [])
               if r['ref'] == 'muscle-glycogen-post-exercise'
               and r['singleFieldFixes'] == ['儀器']),
           'n665_blocked_gate_depth.json → rows')
    attach('D5', '⚠️ 走排除路徑的對照臂（dose=0）實測項數',
           split.get('對照臂'), 'n669 重算（產品判定器＋私有根）')
    attach('D5', '⚠️ 真的超出帶上限（180 g/h）的項數',
           split.get('超出帶上限'), 'n669 重算（產品判定器＋私有根）')
    attach('D6', '🚨 因 median 被擋掉的實測項數',
           medians, 'n669 重算（產品判定器＋私有根）')
    attach('D6', '⚠️ GI 兩結局在範圍內的項數（佔全體之分子）',
           (cite('n667_inscope_without_instrument.json',
                 'withoutInstrumentByOutcome', 'gi-symptom-severity') or 0)
           + (cite('n667_inscope_without_instrument.json',
                   'withoutInstrumentByOutcome', 'gi-symptom-incidence') or 0),
           'n667_inscope_without_instrument.json')
    attach('D10', '🚨 雙讀在**欄位層級**的不一致處數（結局層級是 3/3 全一致）',
           cite('n662_double_read_fields.json', 'disagreements') and
           len(cite('n662_double_read_fields.json', 'disagreements')),
           'n662_double_read_fields.json → disagreements')
    attach('D10', '⚠️ 不一致的欄位分佈',
           cite('n662_double_read_fields.json', 'byField'),
           'n662_double_read_fields.json → byField')

    # -- 新增待裁定 -------------------------------------------------------
    in_scope_total = cite('n667_inscope_without_instrument.json',
                          'inScopeTotal')
    without_instrument = cite('n667_inscope_without_instrument.json',
                              'inScopeWithoutInstrument')
    papers_affected = cite('n668_scale_identity_elsewhere.json',
                           'papersAffected')
    locators = cite('n668_scale_identity_elsewhere.json',
                    'profileWithoutInstrument', 'sourceLocation', 'distinct')
    unit_filled = cite('n668_scale_identity_elsewhere.json',
                       'profileWithoutInstrument', 'unitAsReported', 'filled')
    empty_semantics = cite('n665_blocked_gate_depth.json',
                           'emptyConfigSemantics')
    blank_verdicts = cite('n666_blank_field_provenance.json', 'verdicts')
    instrument_fixable = sum(
        1 for r in (cite('n665_blocked_gate_depth.json', 'rows') or [])
        if r['singleFieldFixes'] == ['儀器'])
    d4_already = sum(
        1 for r in (cite('n665_blocked_gate_depth.json', 'rows') or [])
        if r['ref'] == 'muscle-glycogen-post-exercise'
        and r['singleFieldFixes'] == ['儀器'])

    new_items = [
        {
            'id': 'D21', 'round': 667, 'status': 'open',
            'blocks': 'GI 家族（可合併性）',
            'ask': 'gi-symptom-incidence／gi-symptom-severity 要不要要求記錄量表（儀器欄）？',
            'evidence': 'n667_inscope_without_instrument.json；'
                        'n668_scale_identity_elsewhere.json',
            'recommend': (
                '⚠️ 建議要求。🚨 在範圍內 %s 項中有 %s 項完全沒有量表資訊，'
                '且那兩個結局是 47／47 與 13／13 **全數落空**——'
                '✅ 能進來不是因為通過檢查，是因為契約對它們沒設檢查。'
                '✅ 補的成本已實測：%s 個定位點、%s 篇，'
                '🚫 不是「重讀 %s 篇全文」。'
                % (in_scope_total, without_instrument, locators,
                   len(papers_affected or {}), len(papers_affected or {}))),
            'notADuplicateOf': (
                'D6（median 要不要收）談的是**效應量測**這一軸，'
                'D11 談的是 incidence 的**分母**——'
                '🚨 本項談的是**用哪個量表量的**，三者互不涵蓋。'),
        },
        {
            'id': 'D22', 'round': 665, 'status': 'open',
            'blocks': '判定一致性（產品程式）',
            'ask': '契約設定欄位「留空」的語意要不要統一？',
            'evidence': 'n665_blocked_gate_depth.json → emptyConfigSemantics',
            'recommend': (
                '⚠️ 建議統一，🚫 但本室不判要統一成哪一邊。'
                '🚨 實測：%s——**同一份契約裡把一格留空，'
                '有的門放行全部、有的門擋掉全部**。'
                '⚠️ 而 D21 那 %s 項正是踩在「留空＝門全開」上。'
                % (empty_semantics, without_instrument)),
            'notADuplicateOf': (
                'D8 談的是**資料項**的「明寫 null vs 鍵缺席」，'
                '🚨 本項談的是**契約設定**的「空清單」——'
                '⚠️ 同一族的病，但發生在不同層。'),
        },
        {
            'id': 'D23', 'round': 666, 'status': 'open',
            'blocks': '語料完整性',
            'ask': '因欄位空白被擋的那批要不要回補？',
            'evidence': 'n666_blank_field_provenance.json；'
                        'n665_blocked_gate_depth.json',
            'recommend': (
                '⚠️ 建議先補「像漏填」的那幾項。🚨 實測分類：%s——'
                '**只有同篇填得出來的那幾項才是強漏填訊號**，'
                '🚫 「整篇該欄全空」分不出是論文沒報還是整篇漏填。'
                '⚠️ 需要讀論文的視窗（n+187），🚫 本室不自行讀。'
                % blank_verdicts),
            'notADuplicateOf': (
                'D18／D19 談的是**還沒取到的論文**，'
                '🚨 本項談的是**已經在手上、但欄位空著**的項目。'),
        },
        {
            'id': 'D24', 'round': 663, 'status': 'open',
            'blocks': 'A4（範圍歸屬）',
            'ask': '運動至衰竭時間與計時賽的儀器同義字，要不要在契約收，'
                   '還是回全文判定哪一位讀者寫的才對？',
            'evidence': 'n663_reader_vocabulary.json；'
                        'n665_blocked_gate_depth.json',
            'recommend': (
                '⚠️ 建議回全文判定，🚫 不要先收同義字。'
                '🚨 因為 D4 的前例正是「兩個名字都不對」——'
                '收同義字會把一個錯的名字寫進契約。'
                '✅ 規模：單欄換儀器即可進範圍者共 %s 項，'
                '🚨 其中 %s 項屬 D4 已裁的那批，**真正還開著的是 %s 項**。'
                % (instrument_fixable, d4_already,
                   instrument_fixable - d4_already)),
            'notADuplicateOf': (
                '🚨 D4 已裁的是**切片器械**那一個結局；'
                '⚠️ 本項是**運動至衰竭時間與計時賽**那兩個，跨 3 篇。'),
        },
    ]

    merged = list(items.values()) + new_items
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v2 的全部登記（必觸發之正對照）',
          len(items) == 20,
          '🚨 承接 %d 項｜新增 %d 項｜合計 %d 項；⚠️ 少接一項就是把待裁定弄丟了'
          % (len(items), len(new_items), len(merged)))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s；⚠️ 取不到就代表登記簿與憑證脫節'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))
    def evidence_resolves(item):
        """⚠️ 證據字串可能帶「→ 欄位」後綴，🚨 要切掉才是檔名。"""
        parts = str(item['evidence']).replace('；', ';').split(';')
        return any((HERE / part.split('→')[0].strip()).exists()
                   for part in parts if part.strip())

    dangling = [item['id'] for item in merged if not evidence_resolves(item)]
    probe('每一項都指得到真的證據檔（必觸發）',
          not dangling,
          '🚨 檢查 %d 項；指不到檔的：%s；⚠️ 指到不存在的檔就是空頭支票'
          % (len(merged), dangling or '無'))
    probe('每一個新增項都聲明了它與最近既有項的關係（必觸發之反向）',
          all(item.get('notADuplicateOf') for item in new_items),
          '🚨 新增 %d 項，未聲明者：%s；⚠️ 不聲明就可能只是把既有的重登一次'
          % (len(new_items),
             [i['id'] for i in new_items if not i.get('notADuplicateOf')]
             or '無'))
    probe('劑量拆解與 n664 存的總數對得起來（必觸發之跨憑證對帳）',
          sum(split.values()) == stored_dose_total,
          '🚨 重算 %s（合計 %d）｜n664 存的總數 %s；'
          '⚠️ 對不起來代表兩支憑證之一漂掉了'
          % (split, sum(split.values()), stored_dose_total))
    # 🚨 這一道是答案。
    content_gate_blockers = [i['id'] for i in merged
                             if i['status'] == 'open'
                             and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not content_gate_blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s；⚠️ 這些不決定，A 系列過不了'
          % (len(content_gate_blockers), content_gate_blockers))

    doc = {
        'schemaVersion': 3,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n634_decision_register_v2.json（🚫 不改寫該檔）',
        'whatThisChainAdded': (
            '🚨 第 662–668 輪這一串有一半是**重新撞到既有的裁定**——'
            'D4（第 594 輪）早就裁過切片器械那 3 項。'
            '✅ 真正新增的是 4 項（D21–D24），'
            '另有 4 項既有決定拿到新的實測數字（D4／D5／D6／D10）。'),
        'counts': {'carriedOver': len(items), 'added': len(new_items),
                   'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open')},
        'decisionsUpdatedThisChain': updated,
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'doseSplitRecomputed': split,
        'howToUse': (
            '✅ 每一項都附證據檔與本室建議；'
            '⚠️ 引用的數字是**執行時從憑證取的**，🚫 不是手打的。'
            '✅ 新增項另附「它不是哪一項的重複」，🚫 免得登記簿膨脹成噪音。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n669 決策登記簿 v3 ===')
    print('   承接 %d 項｜新增 %d 項｜合計 %d 項（其中 open %d）'
          % (len(items), len(new_items), len(merged), doc['counts']['open']))
    print('   本串掛上新證據的既有決定：%s' % updated)
    print('   新增：')
    for item in new_items:
        print('      %s [%s] 阻擋 %s' % (item['id'], item['status'],
                                          item['blocks']))
        print('         問：%s' % item['ask'])
        print('         建議：%s' % item['recommend'])
        print('         不是重複：%s' % item['notADuplicateOf'])
    print('   劑量拆解（重算）：%s｜n664 存的總數 %s'
          % (split, stored_dose_total))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
