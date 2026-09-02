# -*- coding: utf-8 -*-
"""**還有沒有別的決定對是連在一起、而兩邊都沒寫的。**（第 703 輪）

## 🚨 上一輪那個連鎖是**碰巧**發現的

第 701 輪查出 `D3` 與 `D24` 連在一起（修一邊會讓同一組人被算兩次）。
**⚠️ 而本室是排順序時順手撞到的，🚫 不是查出來的。**

> **🚨 碰巧發現一個，就該問：還有幾個沒被碰到？**

## ✅ 怎麼精確地找

兩個決定若**碰的是同一批論文**，就有連鎖的可能。
✅ 而「同一批論文」是可以逐字比對的——**報告代號**。

1. 每個決定 → 它的證據憑證裡出現的報告代號集合
2. 兩兩比，看共用幾篇
3. **🚨 共用論文、但兩邊的條目都沒提到對方的代號** → **候選未記錄連鎖**

⚠️ 登記簿本身（`pending-decision-register`）不算證據——
🚨 它提到全部的報告，會把每一對都變成「共用」。

## ✅ 而本支有一個現成的正對照

**`D3`／`D24` 必須出現，而且必須被判為「已記錄」**（第 702 輪剛寫進兩邊）。
⚠️ 若它沒出現，代表本支的比對根本沒接上。

## 🚫 本支不新增或修改任何決定、不送外部請求
"""
import collections
import itertools
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n703_unrecorded_interlocks.json'
REGISTER = HERE / 'n702_decision_register_v12.json'

REPORT = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
DID = re.compile(r'\bD[1-9][0-9]?\b')
CONTROL_PAIR = ('D24', 'D3')


def text_of(item):
    return ' '.join(str(item.get(k) or '') for k in
                    ('ask', 'recommend', 'notADuplicateOf', 'sizeNote',
                     'interlock', 'executionPrerequisite'))


def main():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    items = {item['id']: item for item in register['items']}

    reports = {}
    skipped = collections.Counter()
    for did, item in items.items():
        found = set()
        for part in str(item.get('evidence') or '').replace(
                '；', ';').split(';'):
            name = part.split('→')[0].strip()
            path = HERE / name
            if not name or not path.is_file():
                continue
            try:
                doc = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue
            # 🚨 登記簿不算證據——⚠️ 它提到全部報告，會讓每一對都「共用」。
            if isinstance(doc, dict) and \
                    doc.get('documentType') == 'pending-decision-register':
                skipped[did] += 1
                continue
            found |= set(REPORT.findall(path.read_text(encoding='utf-8')))
        reports[did] = found

    # 🚨 有些決定的證據**涵蓋全語料**（例如 D1／D17）——
    # ⚠️ 它們跟誰都「共用論文」，那個訊號沒有鑑別力。
    # ✅ 故只在**指名特定論文**的決定之間找連鎖，並把全語料型的另外列出。
    CORPUS_WIDE = 20
    corpus_wide = sorted(d for d, v in reports.items()
                         if len(v) >= CORPUS_WIDE)
    specific = sorted(d for d, v in reports.items()
                      if 0 < len(v) < CORPUS_WIDE)

    pairs = []
    for a, b in itertools.combinations(specific, 2):
        shared = reports[a] & reports[b]
        if not shared:
            continue
        a_mentions_b = b in set(DID.findall(text_of(items[a])))
        b_mentions_a = a in set(DID.findall(text_of(items[b])))
        pairs.append({
            'pair': [a, b], 'sharedReports': len(shared),
            'sharedSample': sorted(shared)[:4],
            'crossReferenced': a_mentions_b or b_mentions_a,
            'bothWaysReferenced': a_mentions_b and b_mentions_a,
            'bothOpen': (items[a].get('status') == 'open'
                         and items[b].get('status') == 'open'),
        })
    pairs.sort(key=lambda p: (-p['sharedReports'], p['pair']))

    unrecorded = [p for p in pairs
                  if p['bothOpen'] and not p['crossReferenced']]
    control = next((p for p in pairs
                    if sorted(p['pair']) == sorted(CONTROL_PAIR)), None)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每個決定都抽得到報告代號（必觸發之正對照）',
          sum(1 for v in reports.values() if v) >= 10,
          '🚨 %d／%d 個決定的證據裡有報告代號；'
          '⚠️ 太少的話這個比對沒有分母'
          % (sum(1 for v in reports.values() if v), len(reports)))
    probe('`D3`／`D24` 這一對必須出現，且已被判為「已記錄」（必觸發之正對照）',
          control is not None and control['bothWaysReferenced'],
          '🚨 對照對：%s；⚠️ 沒出現代表比對沒接上，'
          '只有單向代表第 702 輪的雙邊寫入沒生效' % control)
    # 🚨 第一版把這道寫成「略過次數必須 > 0」——⚠️ 但實測是 0，
    # 也就是**沒有任何決定拿登記簿當證據**。
    # 🚨 一道永遠不會觸發的檢查，正是本室反覆在別處抓的那種。
    # ✅ 改成斷言真實狀態：登記簿不在任何決定的證據清單裡。
    probe('登記簿不在任何決定的證據清單裡（實際狀態）',
          sum(skipped.values()) == 0,
          '🚨 被當成證據的登記簿引用 %d 次；'
          '⚠️ 若不是 0，每一對都會因為它而「共用」全部論文'
          % sum(skipped.values()))
    probe('全語料型的決定已被排除在配對之外（必觸發之正對照）',
          bool(corpus_wide) and bool(specific),
          '🚨 全語料型（證據涵蓋 ≥ %d 篇）%d 個：%s；'
          '指名特定論文的 %d 個；'
          '⚠️ 若沒有排除，D1／D17 這種會跟誰都「共用 41 篇」'
          % (CORPUS_WIDE, len(corpus_wide), corpus_wide, len(specific)))
    # 🚨 這一道是答案。
    probe('沒有「共用論文卻兩邊都沒提對方」的決定對',
          not unrecorded,
          '🚨 候選未記錄連鎖 %d 對：%s；'
          '⚠️ 這是**候選**，🚫 不是「一定有連鎖」——'
          '**共用論文只代表它們碰同一批東西**'
          % (len(unrecorded),
             [(p['pair'], p['sharedReports']) for p in unrecorded[:12]]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'unrecorded-interlocks',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'why': ('🚨 第 701 輪那個連鎖是**碰巧**撞到的——'
                '⚠️ 碰巧發現一個，就該問還有幾個沒被碰到。'),
        'reportsPerDecision': {k: len(v) for k, v in sorted(reports.items())},
        'corpusWideDecisions': corpus_wide,
        'specificDecisions': specific,
        'corpusWideThreshold': CORPUS_WIDE,
        'registerCitationsSkipped': dict(skipped),
        'pairs': pairs,
        'unrecordedCandidates': unrecorded,
        'controlPair': control,
        'whatSharedReportsMeans': (
            '⚠️ 「共用論文」只代表兩個決定**碰同一批東西**，'
            '🚫 不代表裁一邊會影響另一邊。'
            '**✅ 本支產出的是候選清單**——'
            '🚨 `D3`／`D24` 那種真正的連鎖，仍要像第 701 輪那樣**逐對算**。'),
        'methodLimit': (
            '🚨 只找得到**在證據憑證裡留下報告代號**的連鎖；'
            '⚠️ 若兩個決定連在一起卻不共用論文'
            '（例如都動到同一段產品程式），**本支看不到**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n703 未記錄的決定連鎖 ===')
    print('   有報告代號的決定 %d 個｜共用論文的對 %d 組｜候選未記錄 %d 組'
          % (sum(1 for v in reports.values() if v), len(pairs),
             len(unrecorded)))
    print('   共用最多的前 12 對：')
    for row in pairs[:12]:
        print('      %-9s 共用 %2d 篇｜互相提到：%s%s'
              % ('／'.join(row['pair']), row['sharedReports'],
                 '✅' if row['crossReferenced'] else '🚨 沒有',
                 '（雙向）' if row['bothWaysReferenced'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
