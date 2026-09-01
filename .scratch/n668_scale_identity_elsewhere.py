# -*- coding: utf-8 -*-
"""**那 60 項的量表身分，是不是記在別的欄位。**（第 668 輪）

## 🚨 第 667 輪的結果留下一個很實際的問題

在範圍內的 98 項有 **60 項沒有儀器紀錄**（GI 症狀那兩個結局，47／47 與 13／13）。

> **⚠️ 若量表身分其實記在別的欄位，要補的是「對映」；
> 🚨 若哪裡都沒有，要補的是「回去把 60 項重讀一遍」。**
> **✅ 這兩件事的成本差一個數量級。**

## ✅ schema 裡的候選欄位

`reportedOutcome` 有 `localLabel`（自由文字）、**`unitAsReported`**、
`outcomeRoleAsStated`、`sourceLocation`。
🚨 GI 嚴重度的量表身分（幾分制、VAS 幾公釐）**本來就會落在單位上**。

## ✅ 本支怎麼判「這一欄可能承載量表身分」

**填答率 ≥ 50% 且相異值 ≥ 5**——
⚠️ 只填答率高不夠（`analysisSet` 人人都填但只有三種值，🚫 分不出量表）；
⚠️ 只相異值高也不夠（十項裡只填兩項，補不動）。

## 🚫 本支只輸出「填答率」與「相異值數」，**🚫 一個欄位值都不印**

🚨 那些是文獻衍生文字；✅ 而計數就足以回答本題。
**⚠️ 且本支證不出那些相異值裡面就是量表名稱——那要讀，而讀是 n+187 的視窗。**
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

OUT = Path(__file__).resolve().parent / 'n668_scale_identity_elsewhere.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

CANDIDATES = ['localLabel', 'unitAsReported', 'outcomeRoleAsStated',
              'sourceLocation', 'effectMeasure', 'analysisSet',
              'reportedTimepoints', 'instrument']
FILL_FLOOR = 0.5
DISTINCT_FLOOR = 5


def inventories():
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        yield json.loads(path.read_text(encoding='utf-8'))


def profile(items):
    """每個候選欄位的填答率與相異值數。🚫 不輸出任何值本身。"""
    out = {}
    for field in CANDIDATES:
        filled, values = 0, set()
        for item in items:
            value = item.get(field)
            if value is None or value == [] or value == {}:
                continue
            filled += 1
            values.add(json.dumps(value, ensure_ascii=False, sort_keys=True))
        out[field] = {
            'filled': filled,
            'of': len(items),
            'fillRate': round(filled / len(items), 3) if items else 0.0,
            'distinct': len(values),
        }
    return out


def carriers(prof):
    return sorted(f for f, s in prof.items()
                  if f != 'instrument'
                  and s['fillRate'] >= FILL_FLOOR
                  and s['distinct'] >= DISTINCT_FLOOR)


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    without, with_instrument = [], []
    papers = collections.Counter()
    for inventory in inventories():
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            if reported.get('instrument') is None:
                without.append(reported)
                papers[inventory['report'][-16:]] += 1
            else:
                with_instrument.append(reported)

    prof_without = profile(without)
    prof_with = profile(with_instrument)
    found = carriers(prof_without)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('抓到的正是第 667 輪那 60 項（必觸發之正對照）',
          len(without) == 60 and len(with_instrument) == 38,
          '🚨 無儀器 %d 項／有儀器 %d 項；⚠️ 對不上就與上一輪不一致'
          % (len(without), len(with_instrument)))
    probe('那 60 項的 instrument 欄必須是 0 填答（必觸發之反向・恆等）',
          prof_without['instrument']['filled'] == 0
          and prof_with['instrument']['filled'] == len(with_instrument),
          '🚨 無儀器組的 instrument 填答 %d；有儀器組 %d／%d；'
          '⚠️ 若無儀器組不是 0，代表本支分組分錯了'
          % (prof_without['instrument']['filled'],
             prof_with['instrument']['filled'], len(with_instrument)))
    probe('判準真的會篩掉低相異度的欄位（必觸發之反向）',
          'analysisSet' not in found,
          '🚨 analysisSet 填答 %.0f%%／相異 %d，判為「不可能承載量表身分」；'
          '⚠️ 若它也入選，代表判準只是在挑「填得多的欄位」'
          % (100 * prof_without['analysisSet']['fillRate'],
             prof_without['analysisSet']['distinct']))
    # 🚨 這一道是答案。
    probe('量表身分 🚫 沒有記在任何其他欄位',
          not found,
          '🚨 可能承載量表身分的欄位（填答率 ≥ %.0f%% 且相異值 ≥ %d）：%s；'
          '⚠️ 若有，補的是**對映**；🚫 若沒有，補的是**回去重讀 60 項**'
          % (100 * FILL_FLOOR, DISTINCT_FLOOR, found or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'scale-identity-elsewhere',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeWithoutInstrument': len(without),
        'inScopeWithInstrument': len(with_instrument),
        'papersAffected': dict(papers.most_common()),
        'profileWithoutInstrument': prof_without,
        'profileWithInstrument': prof_with,
        'criterion': {'fillRate': FILL_FLOOR, 'distinct': DISTINCT_FLOOR},
        'possibleCarriers': found,
        'criterionFalsePositive': (
            '🚨 本支的判準是**純結構的**（填答率＋相異值），'
            '⚠️ 分不出「描述欄位」與「定位欄位」——'
            '`sourceLocation` 會入選，但它是頁碼／章節／表號，'
            '**🚫 它說得出去哪裡找，說不出量的是什麼**。'
            '✅ 真正的候選只有 `localLabel` 一個。'),
        'locatorCoverage': (
            '✅ 而 `sourceLocation` 100%% 填答這件事本身有用：'
            '**要補那 60 項的儀器，🚫 不必重讀 %d 篇全文，'
            '✅ 只要跳到那 %d 個定位點。**'
            % (len(papers), prof_without['sourceLocation']['distinct'])),
        'whyThisMatters': (
            '⚠️ 第 667 輪指出 60／98 沒有儀器紀錄。'
            '🚨 若量表身分其實在別欄，要補的是**對映**；'
            '🚫 若哪裡都沒有，要補的是**回去把 60 項重讀一遍**——'
            '✅ 成本差一個數量級，而裁定需要知道是哪一種。'),
        'methodLimit': (
            '🚨 本支只算**填答率與相異值數**，🚫 一個欄位值都沒有輸出，'
            '⚠️ 也**證不出那些相異值裡面就是量表名稱**——'
            '✅ 高相異度的自由文字欄位「可能」承載它，'
            '🚫 但要確認得讀，而讀是 n+187 的視窗。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n668 量表身分是否記在別的欄位 ===')
    print('   在範圍內無儀器 %d 項（來自 %d 篇）｜有儀器 %d 項'
          % (len(without), len(papers), len(with_instrument)))
    print('   欄位｜無儀器那 60 項：填答／相異｜有儀器那 38 項：填答／相異')
    for field in CANDIDATES:
        a, b = prof_without[field], prof_with[field]
        print('      %-22s %3d/%-3d 相異 %-4d ｜ %3d/%-3d 相異 %d'
              % (field, a['filled'], a['of'], a['distinct'],
                 b['filled'], b['of'], b['distinct']))
    print('   判準：填答率 ≥ %.0f%% 且相異值 ≥ %d'
          % (100 * FILL_FLOOR, DISTINCT_FLOOR))
    print('   → 可能承載量表身分者：%s' % (found or '無'))
    print('   受影響的篇：%s' % dict(papers.most_common()))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
