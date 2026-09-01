# -*- coding: utf-8 -*-
"""**上一輪對的是頭條數字，而錯的那個藏在建議文字裡。**（第 637 輪）

## 🚨 本輪找到一個飄掉的數字，它躲過了第 636 輪的對帳

⚠️ 第 636 輪把十個**頭條**數字重算後與憑證比對，全數相符。
**🚨 但登記簿的「建議」欄裡也寫著數字，而那一層沒有任何東西在對。**

> **🚨 D3 的建議寫著「改名會讓期刊那篇拿回 **9** 項」——⚠️ 實際是 **6** 項。**
> ✅ 第 584 輪當初寫的「六項」才是對的；🚨 是第 610 輪的建議文字把它寫成 9。

## ✅ 順帶把兩件事查清楚

| | 問題 | 答案 |
|---|---|---|
| **甲** | 上限（`maxStudyResultsPerStudy`）在本 run 觸發過嗎 | **🚨 從未**：最大 9、上限 12 |
| **乙** | D3 一旦施行會不會第一次觸發它 | **🚫 不會**：4 ＋ 6 ＝ 10 ≤ 12 |

⚠️ 本室原本假設「D3 會踩到 cap，而那正是 D8／D9 分歧之處」。
**🚨 讀了第 593 輪的憑證才知道假設錯兩層**：一是合併後只有 10；
二是**兩條路徑目前本來就一致**（契約的 `onExceedMax` 剛好是 `escalate`）。
✅ 假設死在自己的憑證手上，🚫 不是死在本室的印象裡。

## 🚫 本支不改任何憑證、不送外部請求、不改任何產品程式
"""
import collections
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

S = Path(__file__).resolve().parent
OUT = S / 'n637_prose_numbers.json'

PAIR_THESIS = '307c0dd5b141caed'
PAIR_JOURNAL = '7a6ac1559c740fd6'

# ⚠️ 建議文字裡可機械查證的數字宣稱。
# 🚨 只列本室查得動的；**覆蓋率不是 100%，這一點本支自己說**。
CHECKABLE = [
    {'decision': 'D3',
     'claim': '改名會讓期刊那篇拿回 9 項',
     'claimedValue': 9,
     'what': '%s 目前卡在 instrument-not-in-allowlist 的項數' % PAIR_JOURNAL,
     'source': ('live', 'journalBlocked')},
    {'decision': 'D2', 'claim': '更正表 15 項改名', 'claimedValue': 15,
     'what': 'n585 的 itemsByCategory.rename-safe',
     'source': ('artefact', 'n585_blocked_drafts_errata.json',
                ['itemsByCategory', 'rename-safe'])},
    {'decision': 'D2', 'claim': '更正表 5 項撤回', 'claimedValue': 5,
     'what': 'n585 的 itemsByCategory.withdraw',
     'source': ('artefact', 'n585_blocked_drafts_errata.json',
                ['itemsByCategory', 'withdraw'])},
    {'decision': 'D12', 'claim': '宣稱有數值而找不到的有 4 項',
     'claimedValue': 4,
     'what': 'n597 的 unsupported 筆數',
     'source': ('artefact', 'n597_numeric_result_unsupported.json',
                ['unsupported'], 'len')},
    {'decision': 'D12', 'claim': '那 4 項的症狀在全文裡**各只出現一次**',
     'claimedValue': 1,
     'what': '🚨 n597 自己記的 comfort 出現次數',
     'source': ('artefact', 'n597_numeric_result_unsupported.json',
                ['symptomNumberProximity', 'comfort', 'mentions'])},
]


def main():
    inventories = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventories.append(json.loads(path.read_text(encoding='utf-8')))

    def in_scope_count(report_suffix):
        for doc in inventories:
            if doc['report'].endswith(report_suffix):
                return sum(1 for o in doc.get('reportedOutcomes') or []
                           if (o.get('scopeDecision') or {}).get('inScope'))
        return None

    def reason_count(report_suffix, code):
        for doc in inventories:
            if doc['report'].endswith(report_suffix):
                return sum(1 for o in doc.get('reportedOutcomes') or []
                           if (o.get('scopeDecision') or {}).get('reasonCode')
                           == code)
        return None

    journal_blocked = reason_count(
        PAIR_JOURNAL, 'notExtracted-instrument-not-in-allowlist')
    thesis_in_scope = in_scope_count(PAIR_THESIS)

    def dig(doc, path):
        cur = doc
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                return None
        return cur

    live = {'journalBlocked': journal_blocked}
    for claim in CHECKABLE:
        source = claim['source']
        if source[0] == 'live':
            claim['actualValue'] = live[source[1]]
        else:
            path = S / source[1]
            value = (dig(json.loads(path.read_text(encoding='utf-8')),
                         source[2]) if path.is_file() else None)
            if len(source) > 3 and source[3] == 'len' and value is not None:
                value = len(value)
            claim['actualValue'] = value
        claim['agrees'] = claim['claimedValue'] == claim['actualValue']

    # 甲／乙：上限的實況。
    caps = collections.Counter()
    per_inventory = []
    for doc in inventories:
        summary = doc.get('scopeDecisionSummary') or {}
        count = sum(1 for o in doc.get('reportedOutcomes') or []
                    if (o.get('scopeDecision') or {}).get('inScope'))
        caps[summary.get('maxStudyResultsPerStudy')] += 1
        per_inventory.append({'report': doc['report'][-16:],
                              'inScope': count,
                              'cap': summary.get('maxStudyResultsPerStudy'),
                              'escalated': summary.get('escalated')})
    cap = next(iter(caps), None)
    largest = max((r['inScope'] for r in per_inventory), default=0)
    ever_fired = [r for r in per_inventory
                  if r['cap'] is not None and r['inScope'] > r['cap']]
    merged_if_d3 = (thesis_in_scope or 0) + (journal_blocked or 0)

    # 🚨 建議文字裡總共有多少數字——⚠️ 用來說清楚本支的覆蓋率。
    register = json.loads(
        (S / 'n634_decision_register_v2.json').read_text(encoding='utf-8'))
    numbers_in_prose = 0
    for item in register['items']:
        for field in ('ask', 'recommend'):
            numbers_in_prose += len(re.findall(r'\d+', str(item.get(field) or '')))

    disagreements = [c for c in CHECKABLE if not c['agrees']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('那兩篇都找得到、數得出來（必觸發之正對照）',
          journal_blocked is not None and thesis_in_scope is not None,
          '🚨 期刊那篇卡在儀器清單 %s 項｜論文那篇在範圍內 %s 項；'
          '⚠️ 任一為 None 就代表本支根本沒讀到那兩份清冊'
          % (journal_blocked, thesis_in_scope))
    probe('上限值在 38 份清冊裡一致（必觸發之正對照）',
          len(caps) == 1 and cap is not None,
          '🚨 實得上限值 %s；⚠️ 若不只一種，「上限」這個詞就要先定義'
          % dict(caps))
    # 🚨 這一道是本輪的發現。
    probe('建議文字裡可查證的數字都正確',
          not disagreements,
          '🚨 不符 %d 筆：%s；⚠️ **第 636 輪只對頭條數字，'
          '這一層當時沒有任何東西在看**'
          % (len(disagreements),
             [(c['decision'], c['claimedValue'], c['actualValue'])
              for c in disagreements]))
    probe('上限從未被觸發（本輪的事實，非缺陷）',
          not ever_fired,
          '✅ 觸發過的清冊 %d 份；⚠️ 最大在範圍內項數 %d、上限 %s——'
          '**🚨 即 escalate 那條路在本 run 從未跑過**'
          % (len(ever_fired), largest, cap))

    doc = {
        'schemaVersion': 1,
        'documentType': 'prose-number-reconciliation',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'checkedClaims': CHECKABLE,
        'coverage': {
            'numbersFoundInRegisterProse': numbers_in_prose,
            'claimsCheckedHere': len(CHECKABLE),
            'note': ('🚨 本支只查了 %d 筆，而登記簿的 ask／recommend 裡共有 '
                     '%d 個數字——**⚠️ 覆蓋率遠不到一半**。'
                     '✅ 本支不假裝這一層已經清乾淨。'
                     % (len(CHECKABLE), numbers_in_prose)),
        },
        'capStatus': {
            'cap': cap, 'largestInScopeInAnyInventory': largest,
            'inventoriesOverCap': len(ever_fired),
            'mergedIfD3': merged_if_d3,
            'wouldD3FireTheCap': merged_if_d3 > (cap or 0),
            'note': ('🚨 上限在本 run **從未被觸發**（最大 %d、上限 %s）。'
                     '⚠️ 本室原本假設 D3 一旦施行會第一次踩到它——'
                     '**🚫 錯了**：合併後是 %d ≤ %s。'
                     % (largest, cap, merged_if_d3, cap)),
        },
        'howWrongIsEachError': {
            'D3（9 vs 6）': (
                '🚨 實質有影響：⚠️ 合併後的項數從「4＋9＝13、會超過上限 12」'
                '變成「4＋6＝10、不會超過」。'
                '**✅ 也就是說，錯的那個數字曾經讓本室推出一個錯的後果。**'),
            'D12（各只出現一次）': (
                '⚠️ 這一句是「**各只出現一次且無數字**」。'
                '✅ **「無數字」那半句四個症狀全部成立**'
                '（n597 記的 withNumberNearby 皆為 0）；'
                '🚨 錯的只有「只出現一次」——comfort 是 5 次。'
                '**✅ 故 D12 的實質不受影響，🚨 錯的是修飾語。**'),
        },
        'killedHypothesis': (
            '⚠️ 本室原本還假設「D3 踩到 cap 就會暴露 D8／D9 的分歧」。'
            '🚨 讀第 593 輪的憑證才知道**那也錯了**：'
            '兩條路徑目前本來就一致，因為契約的 `onExceedMax` 剛好是 escalate。'
            '**✅ 假設死在自己的憑證手上，🚫 不是死在本室的印象裡。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n637 建議文字裡的數字 ===')
    for claim in CHECKABLE:
        print('   %s：宣稱 %s｜實際 %s  %s'
              % (claim['decision'], claim['claimedValue'],
                 claim['actualValue'], '✅' if claim['agrees'] else '🚨'))
        print('      查的是：%s' % claim['what'])
    print('   覆蓋率：本支查 %d 筆／登記簿文字裡共 %d 個數字'
          % (len(CHECKABLE), numbers_in_prose))
    print('   上限：%s｜最大在範圍內 %d｜觸發過 %d 份｜D3 合併後 %d'
          % (cap, largest, len(ever_fired), merged_if_d3))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
