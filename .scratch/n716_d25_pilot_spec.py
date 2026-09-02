# -*- coding: utf-8 -*-
"""**`D25` 若要試點，從哪個結局開始、成本多少。**（第 716 輪）

## ✅ 這是第 715 輪那張表的下一步

計分表指出：**`exogenous-cho-oxidation-peak` 條件最完整**——
3 個劑量帶、3 篇同篇內對比、**18／18 都有工具紀錄、0 缺漏**。

> **🚨 那它就是 `D25` 落地時最合理的試點：
> ⚠️ 一個小到做得完、又足以產出真正劑量-反應的切片。**

## ✅ 本支把試點的成本算精確

- 幾項、幾篇、收成幾個「同篇同定位點」的工作組（第 688 輪的分組法）
- 其中幾組落在**拿得到表格**的那一層（第 690 輪的三層）
- 劑量帶的分佈（能不能真的畫出三個點）

## ⚠️ 而本支**不主張**應該做試點

🚫 `D25` 還沒裁——✅ 本支只回答「若要做，最小的一塊長什麼樣、要多少工」。

## 🚫 本支不改任何清冊與契約、不送外部請求、不輸出出處文字
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

OUT = Path(__file__).resolve().parent / 'n716_d25_pilot_spec.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
PILOT = 'exogenous-cho-oxidation-peak'


def payload_types():
    out = {}
    for path in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        candidate = str(doc.get('candidateId') or '')
        if candidate and doc.get('sourceType'):
            out.setdefault(candidate[-16:], doc['sourceType'])
    return out


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    bands = contract['researchQuestion']['interventionOrExposure']['doseBands']
    types = payload_types()

    def band_of(dose):
        for band in bands:
            if band['min'] <= dose <= band['max']:
                return band['bandId']
        return None

    groups = collections.defaultdict(list)
    papers = set()
    band_papers = collections.defaultdict(set)
    tier = collections.Counter()
    items = 0
    other_outcomes = 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        report = inventory['report'][-16:]
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            if reported['normalisedOutcomeRef'] != PILOT:
                other_outcomes += 1
                continue
            items += 1
            papers.add(report)
            dose = reported.get('dose')
            if dose is not None:
                band = band_of(float(dose))
                if band:
                    band_papers[band].add(report)
            loc = reported.get('sourceLocation') or {}
            has_table = isinstance(loc, dict) and \
                loc.get('tableOrFigure') is not None
            source = types.get(report, '（未知）')
            if has_table and source == 'europe-pmc-jats':
                label = '第 1 層：JATS ＋ 表格（表格拿得到）'
            elif has_table and source == 'grobid-tei':
                label = '第 3 層：GROBID ＋ 表格（🚨 卡在 D17）'
            else:
                label = '第 2 層：只有段落（要自己找）'
            tier[label] += 1
            groups['%s｜%s' % (report, json.dumps(loc, sort_keys=True))]\
                .append(label)

    tier1_groups = sum(1 for v in groups.values()
                       if any('第 1 層' in x for x in v))
    tier3_groups = sum(1 for v in groups.values()
                       if any('第 3 層' in x for x in v))
    sizes = sorted((len(v) for v in groups.values()), reverse=True)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('試點結局的項數與前幾輪一致（必觸發之正對照）',
          items == 18,
          '🚨 `%s` 在範圍內 %d 項、%d 篇；⚠️ 不是 18 就與第 713／715 輪不一致'
          % (PILOT, items, len(papers)))
    probe('別的結局沒有被混進來（必觸發之反向）',
          other_outcomes > 0 and items + other_outcomes == 98,
          '🚨 試點 %d 項 ＋ 其餘 %d 項 ＝ %d；'
          '⚠️ 不等於 98 就代表本支濾錯了'
          % (items, other_outcomes, items + other_outcomes))
    probe('劑量帶覆蓋與第 713 輪一致（必觸發之正對照）',
          len([b for b in band_papers if band_papers[b]]) == 3,
          '🚨 有論文的帶：%s；⚠️ 不是 3 個就與第 713 輪不一致'
          % {b: len(v) for b, v in sorted(band_papers.items())})
    # 🚨 這一道是答案。
    probe('試點可以完全在第 1 層（表格拿得到）之內做完',
          tier.get('第 2 層：只有段落（要自己找）', 0) == 0
          and tier.get('第 3 層：GROBID ＋ 表格（🚨 卡在 D17）', 0) == 0,
          '🚨 分層：%s；⚠️ 有第 2／3 層就代表試點也要處理'
          '「段落裡自己找」與「表格拿不到」這兩種情形' % dict(tier))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd25-pilot-spec',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'pilotOutcome': PILOT,
        'whyThisOne': (
            '✅ 第 715 輪的計分表：**條件最完整**——'
            '3 個劑量帶、3 篇同篇內對比、18／18 都有工具紀錄、0 缺漏。'),
        'items': items,
        'papers': len(papers),
        'workGroups': len(groups),
        'groupSizeMax': sizes[0] if sizes else 0,
        'groupSizeMedian': sizes[len(sizes) // 2] if sizes else 0,
        'papersByBand': {b: len(v) for b, v in sorted(band_papers.items())},
        'itemsByTier': dict(tier.most_common()),
        'tier1Groups': tier1_groups,
        'tier3GroupsBlockedByD17': tier3_groups,
        'notAnAdvocacy': (
            '🚫 本支**不主張**應該做試點——⚠️ `D25` 還沒裁。'
            '✅ 它只回答「若要做，最小的一塊長什麼樣、要多少工」。'),
        'whatThisCannotAnswer': (
            '🚫 本支**不看數值**（第 659 輪已證那 98 項沒有效應量）；'
            '⚠️ 也不保證那些定位點過去就有數字'
            '（第 689 輪：定位點是排序訊號，🚫 不是判定）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n716 D25 試點規格（%s）===' % PILOT)
    print('   在範圍內 %d 項｜%d 篇｜工作組 %d 個（最大 %d、中位 %d）'
          % (items, len(papers), len(groups),
             sizes[0] if sizes else 0,
             sizes[len(sizes) // 2] if sizes else 0))
    print('   劑量帶（篇）：%s' % doc['papersByBand'])
    print('   分層（項）：')
    for label, count in tier.most_common():
        print('      %-40s %d' % (label, count))
    print('   帶表格指標的工作組 %d 個｜其中卡在 D17 的 %d 個'
          % (tier1_groups + tier3_groups, tier3_groups))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
