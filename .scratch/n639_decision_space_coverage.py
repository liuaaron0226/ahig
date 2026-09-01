# -*- coding: utf-8 -*-
"""**判定空間裡，有多少條規則從來沒被真實資料走過。**（第 639 輪）

## 🚨 第 638 輪跑起來一條沒人跑過的路，並且在那裡找到最糟的後果

⚠️ 那一條是本室**猜**出來的（因為第 637 輪剛好量到上限沒觸發過）。
**🚫 但一條一條猜不是辦法。**

> **✅ 本輪把整張地圖攤開：產品程式裡有哪些判定分支，
> 而 38 份清冊實際走過哪幾條。**

## ✅ 作法

以 AST 從 `ahig/scope/matcher.py` 抽出每一個 `ruleId` 與 `reasonCode` 字面，
再數它們在清冊裡出現幾次。**🚨 出現 0 次的就是從未被真實資料走過的分支。**

## ⚠️ 「沒走過」不等於「壞掉」

🚫 本支不宣稱那些分支有缺陷——⚠️ 它們可能單純是這批文獻沒有觸發的情況。
**✅ 但第 638 輪剛示範過：沒走過的分支裡確實藏著自相矛盾的輸出。**

## 🚫 本支不改任何產品程式、不改任何清冊、不送外部請求
"""
import ast
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

OUT = Path(__file__).resolve().parent / 'n639_decision_space_coverage.json'
MATCHER = REPO / 'ahig/ahig/scope/matcher.py'


def literals_from(source):
    """抽出 ScopeDecision(...) 呼叫裡的 reasonCode 與 ruleId 字面。

    ⚠️ 用 AST 而非搜字串：🚨 註解與說明文字裡也寫著這些代號，
    而那些不是分支。
    """
    tree = ast.parse(source)
    reasons, rules = set(), set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == 'ScopeDecision'):
            continue
        strings = [a.value for a in node.args
                   if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        # ⚠️ ScopeDecision(in_scope, reason_code, matched, rule_id)
        if len(strings) >= 1:
            reasons.add(strings[0])
        if len(strings) >= 2:
            rules.add(strings[-1])
    return reasons, rules


def main():
    source = MATCHER.read_text(encoding='utf-8')
    reason_literals, rule_literals = literals_from(source)

    # ⚠️ 逐項判定另有兩處直接寫欄位（上限那一段不走 ScopeDecision）。
    extra_reason = {'escalated-exceeds-max-studyresults'}
    extra_rule = {'SCOPE-100-exceeds-max'}
    reason_literals |= extra_reason
    rule_literals |= extra_rule

    seen_reason = collections.Counter()
    seen_rule = collections.Counter()
    inventories = 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventories += 1
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            decision = outcome.get('scopeDecision') or {}
            if decision.get('reasonCode'):
                seen_reason[decision['reasonCode']] += 1
            if decision.get('ruleId'):
                seen_rule[decision['ruleId']] += 1

    # ⚠️ 「沒走過」有兩種很不一樣的原因：🚨 這批文獻不觸發，
    # 或者**它排在漏斗後面、根本沒幾項走到那裡**。✅ 故把漏斗算出來。
    # decide() 的順序：數值結果 → 結局／儀器 → 時點 → 分析集 → 效應量
    #                  → 統計模型 → 次群／敏感度 → 劑量帶。
    ORDER = [
        ('SCOPE-000-no-numeric-result', '有沒有數值結果'),
        ('SCOPE-001-outcome', '結局在不在契約裡'),
        ('SCOPE-001b-instrument', '儀器在不在允許清單'),
        ('SCOPE-002-timepoint', '時點落不落在窗內'),
        ('SCOPE-003-analysis-set', '分析集'),
        ('SCOPE-004-effect-measure', '效應量'),
        ('SCOPE-005-model', '統計模型'),
        ('SCOPE-006-subgroup', '次群政策'),
        ('SCOPE-007-sensitivity', '敏感度政策'),
        # 🚨 第一版漏了這一關，於是漏斗停在 117 而在範圍內是 98——
        # ⚠️ 一張自己交代不完的表，讀者會以為中間有東西消失了。
        ('SCOPE-008-dose', '劑量落不落在帶內'),
    ]
    funnel = []
    remaining = sum(seen_reason.values())
    for rule_id, label in ORDER:
        failed = seen_rule[rule_id]
        funnel.append({'gate': label, 'ruleId': rule_id,
                       'reached': remaining, 'rejectedHere': failed,
                       'everFired': failed > 0})
        remaining -= failed
    funnel.append({'gate': '全關通過（在範圍內）', 'ruleId': 'SCOPE-999-in-scope',
                   'reached': remaining, 'rejectedHere': 0,
                   'everFired': seen_rule['SCOPE-999-in-scope'] > 0})

    unexercised_reason = sorted(r for r in reason_literals
                                if seen_reason[r] == 0)
    unexercised_rule = sorted(r for r in rule_literals if seen_rule[r] == 0)
    unknown_reason = sorted(r for r in seen_reason if r not in reason_literals)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('抽得到分支字面（必觸發之正對照）',
          len(reason_literals) >= 6 and len(rule_literals) >= 6,
          '🚨 抽出理由碼 %d 種、規則 %d 種；⚠️ 太少代表 AST 抽取失敗，'
          '那麼「幾條沒走過」就沒有分母'
          % (len(reason_literals), len(rule_literals)))
    probe('清冊裡真的數得到（必觸發之正對照）',
          sum(seen_reason.values()) >= 600 and inventories == 38,
          '🚨 %d 份清冊、%d 個判定；⚠️ 若很少，「沒走過」只是本支沒讀到'
          % (inventories, sum(seen_reason.values())))
    probe('漏斗結算得回在範圍內的項數（必觸發之正對照）',
          funnel[-1]['reached'] == seen_rule['SCOPE-999-in-scope'],
          '🚨 漏斗走完剩 %d、實際在範圍內 %d；⚠️ 對不上代表本支漏了某一關，'
          '**而一張自己交代不完的表，讀者會以為中間有東西消失了**'
          % (funnel[-1]['reached'], seen_rule['SCOPE-999-in-scope']))
    probe('清冊裡沒有產品程式以外的理由碼（必觸發之反向）',
          not unknown_reason,
          '🚨 清冊出現而程式裡抽不到的理由碼：%s；'
          '⚠️ 若有，代表本支的抽取漏了分支，或清冊寫進了非法值'
          % unknown_reason)
    # 🚨 這一道是答案。
    probe('每一條判定分支都被真實資料走過',
          not unexercised_reason and not unexercised_rule,
          '🚨 從未走過的理由碼 %d 種：%s；規則 %d 種：%s'
          % (len(unexercised_reason), unexercised_reason,
             len(unexercised_rule), unexercised_rule))

    doc = {
        'schemaVersion': 1,
        'documentType': 'decision-space-coverage',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': inventories,
        'decisionsCounted': sum(seen_reason.values()),
        'reasonCodesInCode': sorted(reason_literals),
        'ruleIdsInCode': sorted(rule_literals),
        'exercisedReasonCodes': dict(seen_reason.most_common()),
        'exercisedRuleIds': dict(seen_rule.most_common()),
        'funnel': funnel,
        'funnelNote': (
            '⚠️ decide() 是逐關順序判定，🚨 故後面的關卡只看得到前面全過的項目。'
            '**✅ 「從未走過」要配著「有幾項走到那裡」讀**——'
            '例如時點那一關有 %d 項走到、0 項被擋下，'
            '⚠️ 那是「這批文獻的時點都合格」，🚫 不是「沒有東西測過它」。'
            % next((f['reached'] for f in funnel
                    if f['ruleId'] == 'SCOPE-002-timepoint'), 0)),
        'unexercisedReasonCodes': unexercised_reason,
        'unexercisedRuleIds': unexercised_rule,
        'coverage': {
            'reasonCodes': '%d/%d' % (len(reason_literals)
                                      - len(unexercised_reason),
                                      len(reason_literals)),
            'ruleIds': '%d/%d' % (len(rule_literals) - len(unexercised_rule),
                                  len(rule_literals)),
        },
        'notAClaimOfDefect': (
            '🚫 「沒走過」不等於「壞掉」——⚠️ 那些分支可能只是這批文獻沒觸發。'
            '**✅ 但第 638 輪剛示範過：沒走過的分支裡確實藏著自相矛盾的輸出。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n639 判定空間覆蓋率 ===')
    print('   清冊 %d 份｜判定 %d 個' % (inventories, sum(seen_reason.values())))
    print('   理由碼覆蓋 %s｜規則覆蓋 %s'
          % (doc['coverage']['reasonCodes'], doc['coverage']['ruleIds']))
    print('   漏斗（逐關）：')
    for f in funnel:
        print('      %-30s 走到 %3d｜擋下 %3d  %s'
              % (f['gate'], f['reached'], f['rejectedHere'],
                 '✅ 有觸發' if f['everFired'] else '🚨 從未觸發'))
    print('   ✅ 走過的理由碼：')
    for code, count in seen_reason.most_common():
        print('      %-52s %d' % (code, count))
    print('   🚨 從未走過的理由碼：')
    for code in unexercised_reason:
        print('      %s' % code)
    print('   🚨 從未走過的規則：')
    for rule in unexercised_rule:
        print('      %s' % rule)
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
