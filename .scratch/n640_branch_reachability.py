# -*- coding: utf-8 -*-
"""**那些沒被走過的分支，逐條驅動一次。**（第 640 輪）

## 🚨 第 639 輪列出 9 條從未被真實資料走過的規則

⚠️ 而「沒走過」有三種很不一樣的可能：

| | 意思 |
|---|---|
| **✅ 正常** | 這批文獻剛好不觸發，分支本身健全 |
| **🚨 死碼** | 在任何合法契約下都到不了——**那條規則等於不存在** |
| **🚨 錯碼** | 到得了，但回傳的理由碼或規則 id 不是它自己那一條 |

> **⚠️ 第 638 輪已證明：沒走過的分支裡真的藏著壞東西。**
> **✅ 故本輪逐條驅動，🚫 不再用「應該沒問題」帶過。**

## ✅ 作法

拿一筆**真實的在範圍內紀錄**當模板（🚫 不手刻——第 632 輪的教訓），
每次只改一個欄位去驅動一條分支，看產品匹配器實際回哪一條。

## 🚫 本支不改任何產品程式、不改任何清冊、不送外部請求
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts import freeze  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n640_branch_reachability.json'
CONTRACT = REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json'

# ⚠️ 每個案例：要驅動哪一條規則、怎麼改模板。
CASES = [
    {'rule': 'SCOPE-002-timepoint', 'what': '時點推到所有窗之外',
     'mutate': lambda r: r.update({'timepointDays': 999})},
    {'rule': 'SCOPE-002c-multiple-measurements',
     'what': '同一時窗內有多個測量點',
     'mutate': lambda r: r.update({'multipleMeasurementsInWindow': True})},
    {'rule': 'SCOPE-003-analysis-set', 'what': '分析集換成契約沒收的值',
     'mutate': lambda r: r.update({'analysisSet': 'per-protocol'})},
    {'rule': 'SCOPE-005-model', 'what': '統計模型換成契約沒收的值',
     'mutate': lambda r: r.update({'statisticalModel': 'ZZ-不收的模型-ZZ'})},
    {'rule': 'SCOPE-006-subgroup', 'what': '標成次群分析',
     'mutate': lambda r: r.update({'isSubgroup': True,
                                   'subgroupId': 'ZZ-未列的次群-ZZ'})},
    {'rule': 'SCOPE-007-sensitivity', 'what': '標成敏感度分析',
     'mutate': lambda r: r.update({'isSensitivityAnalysis': True})},
]


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    template = None
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path) or template is not None:
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if (outcome.get('scopeDecision') or {}).get('inScope'):
                template = {k: v for k, v in outcome.items()
                            if k != 'scopeDecision'}
                break

    baseline = matcher.decide(copy.deepcopy(template))

    rows = []
    for case in CASES:
        reported = copy.deepcopy(template)
        case['mutate'](reported)
        try:
            decision = matcher.decide(reported)
            got_rule = decision.rule_id
            got_reason = decision.reason_code
            in_scope = decision.in_scope
            error = None
        except Exception as err:  # noqa: BLE001
            got_rule = got_reason = None
            in_scope = None
            error = '%s: %s' % (type(err).__name__, err)
        rows.append({
            'targetRule': case['rule'], 'mutation': case['what'],
            'gotRuleId': got_rule, 'gotReasonCode': got_reason,
            'inScope': in_scope, 'error': error,
            'verdict': ('✅ 亮對了' if got_rule == case['rule']
                        else ('🚨 例外' if error
                              else '🚨 到不了或亮錯條')),
        })

    # 🚨 SCOPE-002b 另外處理：⚠️ 它要「同一時窗內有多個結局窗命中」，
    # 而 freeze.py 的凍結前檢查**擋掉重疊時窗**——
    # ✅ 故本支不去偽造一份非法契約，而是問：**它在合法契約下到得了嗎**。
    windows = contract['inScopeTimepoints']
    overlaps = []
    for i, left in enumerate(windows):
        for right in windows[i + 1:]:
            if (left['unit'] == right['unit']
                    and left['windowStart'] <= right['windowEnd']
                    and right['windowStart'] <= left['windowEnd']):
                overlaps.append((left['timepointId'], right['timepointId']))

    # 🚨 上面只驗到「**這一份**契約沒有重疊時窗」。
    # ⚠️ 而「任何合法契約都不會有」是本室從說明文字推的——**照規矩要跑，不要推。**
    overlapping = copy.deepcopy(contract)
    first = copy.deepcopy(overlapping['inScopeTimepoints'][0])
    first['timepointId'] = 'ZZ-重疊窗-ZZ'
    overlapping['inScopeTimepoints'] = (
        overlapping['inScopeTimepoints'] + [first])
    try:
        freeze.assert_freezable(overlapping)
        preflight_refuses = False
        preflight_message = '（未拋出例外）'
    except freeze.ContractFreezeError as err:
        preflight_refuses = True
        preflight_message = str(err)[:160]

    # ⚠️ 而若有人**繞過**前置檢查、手寫一份 status=frozen 的契約呢。
    # 🚨 那條分支其實到得了——本支把它也跑一次，證明分支本身是健全的。
    forged = copy.deepcopy(overlapping)
    forged['status'] = 'frozen'
    try:
        forged_matcher = ScopeMatcher(forged)
        forged_decision = forged_matcher.decide(copy.deepcopy(template))
        forged_rule = forged_decision.rule_id
    except Exception as err:  # noqa: BLE001
        forged_rule = 'error:%s' % type(err).__name__

    misfired = [r for r in rows if r['verdict'] != '✅ 亮對了']

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('模板本身仍判為在範圍內（必觸發之正對照）',
          baseline.in_scope and baseline.rule_id == 'SCOPE-999-in-scope',
          '🚨 未改動的模板判定 in_scope=%s／rule=%s；⚠️ 若模板本身就過不了，'
          '下面每一條都測不到自己想測的東西'
          % (baseline.in_scope, baseline.rule_id))
    probe('每個案例都真的改動了模板（必觸發之正對照）',
          all(r['gotRuleId'] != 'SCOPE-999-in-scope' for r in rows),
          '🚨 仍判為在範圍內的案例：%s；⚠️ 那代表突變沒生效'
          % [r['targetRule'] for r in rows
             if r['gotRuleId'] == 'SCOPE-999-in-scope'])
    # 🚨 這兩道是答案。
    probe('每一條沒走過的分支都驅動得起來、且亮的是自己那一條',
          not misfired,
          '🚨 未如預期者 %d 條：%s'
          % (len(misfired),
             [(r['targetRule'], r['gotRuleId'], r['verdict'])
              for r in misfired]))
    probe('凍結前置檢查真的擋得住重疊時窗（必觸發之反向）',
          preflight_refuses,
          '🚨 造一份含重疊時窗的契約丟給 assert_freezable：%s；'
          '⚠️ 若它不擋，「死碼」這句就不成立' % preflight_message)
    probe('SCOPE-002b 在通得過前置檢查的契約下到得了',
          bool(overlaps),
          '🚨 現行契約的時窗兩兩重疊者：%s；⚠️ 而前置檢查擋掉重疊——'
          '**🚨 故在任何通得過凍結前置檢查的契約裡，這條分支到不了。**'
          '✅ 但它本身健全：繞過前置檢查、手寫一份 status=frozen 的契約，'
          '同一筆紀錄就判成 %s——⚠️ 即**它不是壞的，是到不了的**'
          % (overlaps or '（無）', forged_rule))

    doc = {
        'schemaVersion': 1,
        'documentType': 'branch-reachability',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'templateFrom': '語料裡第一筆在範圍內的紀錄（🚫 非手刻）',
        'baseline': {'inScope': baseline.in_scope,
                     'ruleId': baseline.rule_id},
        'cases': rows,
        'timepointWindowOverlaps': overlaps,
        'preflightRefusesOverlap': preflight_refuses,
        'preflightMessage': preflight_message,
        'ruleWhenPreflightBypassed': forged_rule,
        'scope002bNote': (
            '🚨 `SCOPE-002b-multiple-timepoint-match` 只有在**時窗重疊**時才到得了，'
            '⚠️ 而 `freeze.py` 的凍結前檢查明文擋掉重疊時窗'
            '（且 ScopeMatcher 只收 status=frozen 的契約）。'
            '**🚨 故在任何通得過凍結前置檢查的契約裡它都到不了。**'
            '⚠️ 說得更精確：擋它的是**前置檢查**，'
            '🚨 若有人手寫一份 status=frozen 的契約繞過去，這條分支就到得了'
            '（本支實跑：那時同一筆紀錄判成 %s）——'
            '**✅ 即它不是壞的，是到不了的。**'
            '✅ 這不是缺陷指控——⚠️ 它是刻意的防禦；'
            '🚨 但「防禦」與「永遠不會執行的程式」長得一樣，'
            '**而後者沒有人會發現它壞了。**' % forged_rule),
        'whatThisCannotAnswer': (
            '🚫 本支只驅動單一欄位的突變——⚠️ 多欄位交互（例如次群＋敏感度同時成立）'
            '未受檢；🚨 亮得對也不表示它在真實文獻上會亮對。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n640 分支可達性 ===')
    print('   模板基線：in_scope=%s／%s'
          % (baseline.in_scope, baseline.rule_id))
    print('   %-38s %-34s %s' % ('要驅動的規則', '實際回傳', ''))
    for row in rows:
        print('   %-38s %-34s %s'
              % (row['targetRule'], row['gotRuleId'] or row['error'],
                 row['verdict']))
        print('      突變：%s｜理由碼 %s' % (row['mutation'],
                                            row['gotReasonCode']))
    print('   時窗重疊：%s' % (overlaps or '（無）'))
    print('   前置檢查擋重疊：%s｜繞過之後同一筆判成 %s'
          % (preflight_refuses, forged_rule))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
