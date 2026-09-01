# -*- coding: utf-8 -*-
"""**被擋的每一項，卡的是一道門還是好幾道門。**（第 665 輪）

## 🚨 第 664 輪的分佈是「首擋分佈」，不是「唯一擋它的門」

`ScopeMatcher.decide` 是**依序短路**的——回傳的理由碼是**第一道**擋下它的門。
🚨 第 663 輪就親眼看到：換完儀器名字，有 2 項立刻改卡在劑量上。

> **⚠️ 故「儀器擋 9 項」🚫 不等於「修好儀器就多 9 項」。**

## ✅ 甲、本支怎麼量「卡幾道門」

對每一個**已對上契約結局卻被擋**的項目，做**單欄捐贈**：
拿同一個契約結局底下**真的在範圍內**的某一項當捐贈者，
**一次只換一個欄位**，再用**產品的 `decide()`** 重判。

- ✅ 換了某一欄就進來了 → **只卡那一道門**（真的可回收）
- 🚨 每一欄單獨換都進不來 → **卡兩道以上**

⚠️ 沒有任何在範圍內項目的結局，就沒有捐贈者——🚫 那些只能記為無法測。

## ✅ 乙、順手驗一件結構上的事：**空設定的意思，各門不同**

| 契約欄位 | 留空時 | 產品位置 |
|---|---|---|
| `allowedInstruments` | 🚨 **門全開**（`if allowed and ...`） | `_match_outcome` |
| `doseBands` | 🚨 **門全開**（`if not self.dose_bands: return ...`） | `_match_dose` |
| `inScopeEffectMeasures` | 🚨 **門全關**（`em not in set()` 恆真） | `decide` |
| `inScopeAnalysisSets` | 🚨 **門全關**（同上） | `decide` |

> **⚠️ 同一份契約裡把某一格留空，有的門會全開、有的門會全關。**
> **✅ 本支不靠讀程式碼下這個結論——實際各清空一次，用產品重判。**

## 🚫 本支全部在記憶體副本上做，磁碟上的契約與清冊一字未改
"""
import collections
import copy
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

OUT = Path(__file__).resolve().parent / 'n665_blocked_gate_depth.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# 一次捐一組（劑量的值與單位必須同進同出，否則帶比對必然失敗）
DONATIONS = {
    '儀器': ['instrument'],
    '效應量測': ['effectMeasure'],
    '分析集': ['analysisSet'],
    '劑量': ['dose', 'doseUnit'],
    '時間點': ['timepointDays', 'timepointSessions'],
    '有無數值': ['hasNumericResult'],
    '統計模型': ['statisticalModel'],
}
ALL_FIELDS = sorted({f for fields in DONATIONS.values() for f in fields})


def donate(item, donor, fields):
    """把 donor 的這幾欄搬到 item 的副本上。

    🚨 捐贈者**沒有**的鍵要**刪掉**，🚫 不可設成 None——
    ⚠️ 產品讀的是 `reported.get("statisticalModel", "unadjusted")`，
    **鍵存在但值為 None 時拿不到預設值**，會被模型那道門誤擋。
    ✅ 這一條是本支的全捐正對照亮紅之後才抓到的。
    """
    probe = dict(item)
    for field in fields:
        if field in donor:
            probe[field] = donor[field]
        else:
            probe.pop(field, None)
    return probe


def inventories():
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        yield json.loads(path.read_text(encoding='utf-8'))


def empty_config_semantics(contract, sample):
    """各清空一個設定欄位，看門是全開還是全關。⚠️ 用產品重判，🚫 不讀程式碼下結論。"""
    knobs = {}

    def variant(mutate):
        c = copy.deepcopy(contract)
        mutate(c)
        return ScopeMatcher(c).decide(sample).in_scope

    def clear_instruments(c):
        for o in c['inScopeOutcomes']:
            o['allowedInstruments'] = []

    def clear_bands(c):
        c['researchQuestion']['interventionOrExposure']['doseBands'] = []

    def clear_effect(c):
        c['inScopeEffectMeasures'] = []

    def clear_sets(c):
        c['inScopeAnalysisSets'] = []

    for label, mutate in (('allowedInstruments', clear_instruments),
                          ('doseBands', clear_bands),
                          ('inScopeEffectMeasures', clear_effect),
                          ('inScopeAnalysisSets', clear_sets)):
        knobs[label] = '門全開' if variant(mutate) else '門全關'
    return knobs


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    donors, blocked = {}, []
    sample_in_scope = None
    for inventory in inventories():
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            ref = reported.get('normalisedOutcomeRef')
            if not ref:
                continue
            if decision['inScope']:
                donors.setdefault(ref, reported)
                if sample_in_scope is None:
                    sample_in_scope = reported
            else:
                blocked.append({'report': inventory['report'][-16:],
                                'ref': ref,
                                'firstBlock': decision['reasonCode'],
                                'item': reported})

    rows, no_donor = [], []
    single_fix = collections.Counter()
    depth = collections.Counter()
    identity_ok = True
    full_ok = 0
    for entry in blocked:
        donor = donors.get(entry['ref'])
        if donor is None:
            no_donor.append(entry)
            continue

        # ⚠️ 恆等檢查：什麼都不換必須仍被擋，否則本支的判定跟主判定不一致。
        if matcher.decide(entry['item']).in_scope:
            identity_ok = False

        fixes = []
        for label, fields in DONATIONS.items():
            if matcher.decide(donate(entry['item'], donor, fields)).in_scope:
                fixes.append(label)

        # ✅ 正對照：全部欄位都捐過去，必須進得來。
        whole_ok = matcher.decide(
            donate(entry['item'], donor, ALL_FIELDS)).in_scope
        full_ok += 1 if whole_ok else 0

        if fixes:
            single_fix[fixes[0] if len(fixes) == 1 else '多種單欄皆可'] += 1
            depth['只卡一道門'] += 1
        else:
            depth['卡兩道以上'] += 1
        rows.append({'report': entry['report'], 'ref': entry['ref'],
                     'firstBlock': entry['firstBlock'],
                     'singleFieldFixes': fixes,
                     'allFieldsDonatedPasses': whole_ok})

    knobs = empty_config_semantics(contract, sample_in_scope) \
        if sample_in_scope else {}

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的有被擋的項目可以測（必觸發之正對照）',
          len(rows) > 0,
          '🚨 可測 %d 項｜無捐贈者而測不了 %d 項；⚠️ 若可測是 0，本支沒有內容'
          % (len(rows), len(no_donor)))
    probe('什麼都不換時，被擋的仍被擋（必觸發之反向・恆等）',
          identity_ok,
          '🚨 恆等重判與主判定一致：%s；⚠️ 若不一致，本支換的東西以外還動到了別的'
          % identity_ok)
    probe('把整組欄位都捐過去之後，每一項都進得來（必觸發之正對照）',
          full_ok == len(rows),
          '🚨 全捐後通過 %d／%d；⚠️ 若不是全部，代表還有本支沒捐到的欄位在擋，'
          '「卡兩道以上」的歸因就不完整' % (full_ok, len(rows)))
    probe('留空的設定，四道門的意思一致',
          len(set(knobs.values())) <= 1,
          '🚨 實測：%s；⚠️ 不一致代表「把一格留空」在同一份契約裡意思相反' % knobs)
    # 🚨 這一道是答案。
    probe('被擋的項目都只卡一道門',
          depth.get('卡兩道以上', 0) == 0,
          '🚨 只卡一道 %d 項｜卡兩道以上 %d 項；⚠️ 後者不是「修一欄就回收得到」的'
          % (depth.get('只卡一道門', 0), depth.get('卡兩道以上', 0)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'blocked-item-gate-depth',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'blockedMappedItems': len(blocked),
        'testable': len(rows),
        'noDonorOutcome': [{'report': e['report'], 'ref': e['ref'],
                            'firstBlock': e['firstBlock']} for e in no_donor],
        'gateDepth': dict(depth),
        'singleFieldFixDistribution': dict(single_fix.most_common()),
        'emptyConfigSemantics': knobs,
        'rows': rows,
        'whyThisCorrectsN664': (
            '🚨 第 664 輪報的是**首擋分佈**——`decide` 依序短路，'
            '⚠️ 故「儀器擋 9 項」🚫 不等於「修好儀器就多 9 項」。'
            '✅ 本支改用單欄捐贈量「卡幾道門」，'
            '**只卡一道的才是修一欄就回收得到的**。'),
        'methodLimit': (
            '⚠️ 捐贈者是**同結局的另一項**，🚫 不是這一篇的真實值——'
            '🚨 故本支證的是「這一欄的值若換成一個合格的值，門會不會開」，'
            '🚫 不是「這一項應該填什麼」。'
            '⚠️ 沒有任何在範圍內項目的結局沒有捐贈者，那些完全測不到。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n665 被擋項目卡幾道門 ===')
    print('   已對上結局卻被擋 %d 項｜可測 %d 項｜無捐贈者 %d 項'
          % (len(blocked), len(rows), len(no_donor)))
    print('   卡的深度：%s' % dict(depth))
    print('   單欄即可修者的分佈：%s' % dict(single_fix.most_common()))
    print('   留空設定的語意（實測）：')
    for knob, meaning in knobs.items():
        print('      %-26s %s' % (knob, meaning))
    print('   明細（首擋 → 單欄可修者）：')
    for row in rows:
        print('      %s｜%-30s %-44s → %s'
              % (row['report'], row['ref'], row['firstBlock'],
                 row['singleFieldFixes'] or '🚨 單欄修不動'))
    if no_donor:
        print('   🚨 無捐贈者（該結局沒有任何項在範圍內，測不了）：')
        for entry in no_donor:
            print('      %s｜%-30s %s'
                  % (entry['report'], entry['ref'], entry['firstBlock']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
